"""Embedded GLB intake. Container checks do not certify engine or visual quality."""
import hashlib
import json
from pathlib import Path
import re
import struct

MAX_GLB_BYTES = 128 * 1024 * 1024
PROVENANCE = ('license', 'author', 'source', 'reference_sha256')
APPROVALS = ('approved', 'license_approved', 'visual_approved', 'prototype_approved')
UNKNOWN_LICENSES = {'unknown', 'pending', 'unlicensed', 'none', 'n/a', 'tbd', 'unspecified'}


def metadata_record(metadata, locked_reference=None, require_approval=False):
    if not isinstance(metadata, dict):
        raise ValueError('Asset metadata must be an object')
    for field in APPROVALS:
        if field in metadata and type(metadata[field]) is not bool:
            raise ValueError('Approval must be an explicit boolean: ' + field)
    if require_approval and metadata.get('approved') is not True:
        raise ValueError('Explicit asset intake approval required')
    result = {}
    for field in PROVENANCE:
        value = metadata.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > 4096:
            raise ValueError('Missing or invalid ' + field)
        result[field] = value.strip()
    if not re.fullmatch(r'[a-fA-F0-9]{64}', result['reference_sha256']):
        raise ValueError('reference_sha256 must identify an approved reference with a SHA-256 hash')
    result['reference_sha256'] = result['reference_sha256'].lower()
    if locked_reference is not None and result['reference_sha256'] != locked_reference:
        raise ValueError('Approved appearance reference mismatch')
    result.update({field: metadata.get(field, False) for field in APPROVALS})
    if result['license_approved'] and result['license'].casefold() in UNKNOWN_LICENSES:
        raise ValueError('Unknown license cannot be approved')
    mapping = metadata.get('animation_mapping', {})
    if not isinstance(mapping, dict) or any(not isinstance(k, str) or not isinstance(v, str) or
                                             not k or not v or len(k) > 128 or len(v) > 256
                                             for k, v in mapping.items()):
        raise ValueError('Invalid animation_mapping')
    result['animation_mapping'] = dict(mapping)
    return result


def _integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('Invalid GLB ' + name)
    return value


def _no_uris(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.casefold() == 'uri':
                raise ValueError('External or data URI forbidden: export a fully embedded GLB')
            if key == 'extensions' and child:
                raise ValueError('GLB extensions require a supported dedicated importer')
            _no_uris(child)
    elif isinstance(value, list):
        for child in value:
            _no_uris(child)


def _container(data):
    if len(data) < 20 or data[:4] != b'glTF' or struct.unpack_from('<I', data, 4)[0] != 2 or struct.unpack_from('<I', data, 8)[0] != len(data):
        raise ValueError('Invalid GLB container header')
    offset, chunks = 12, []
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError('Truncated GLB chunk header')
        length, kind = struct.unpack_from('<II', data, offset)
        offset += 8
        if not length or length % 4 or offset + length > len(data):
            raise ValueError('Invalid GLB chunk length')
        chunks.append((kind, data[offset:offset + length]))
        offset += length
    if not chunks or chunks[0][0] != 0x4E4F534A or len(chunks) > 2 or (len(chunks) == 2 and chunks[1][0] != 0x004E4942):
        raise ValueError('GLB requires a JSON chunk and optional embedded BIN chunk')
    try:
        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError('Duplicate GLB JSON key')
                result[key] = value
            return result
        doc = json.loads(chunks[0][1].decode('utf-8'), object_pairs_hook=unique_object,
                         parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Invalid JSON number')))
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError('Invalid GLB JSON: ' + str(error)) from error
    if not isinstance(doc, dict) or not isinstance(doc.get('asset'), dict) or doc['asset'].get('version') != '2.0':
        raise ValueError('GLB asset.version must be 2.0')
    try:
        _no_uris(doc)
    except RecursionError as error:
        raise ValueError('GLB JSON nesting too deep') from error
    # Extensions can introduce other external-resource mechanisms. Unsupported
    # extensions require a dedicated importer before they are accepted here.
    if doc.get('extensionsUsed') or doc.get('extensionsRequired'):
        raise ValueError('GLB extensions require a supported dedicated importer')
    binary = chunks[1][1] if len(chunks) == 2 else b''
    buffers = doc.get('buffers', [])
    if not isinstance(buffers, list) or len(buffers) > 1:
        raise ValueError('GLB must use at most one embedded buffer')
    size = 0
    if buffers:
        if not isinstance(buffers[0], dict):
            raise ValueError('Invalid GLB buffer')
        size = _integer(buffers[0].get('byteLength'), 'buffer byteLength', 1)
        if not binary or not size <= len(binary) <= size + 3:
            raise ValueError('Embedded GLB buffer length mismatch')
    elif binary:
        raise ValueError('GLB BIN chunk has no buffer declaration')
    views = doc.get('bufferViews', [])
    if not isinstance(views, list):
        raise ValueError('Invalid GLB bufferViews')
    for view in views:
        if not isinstance(view, dict) or view.get('buffer') != 0 or not buffers:
            raise ValueError('Invalid GLB bufferView buffer')
        start = _integer(view.get('byteOffset', 0), 'bufferView offset')
        length = _integer(view.get('byteLength'), 'bufferView length', 1)
        if start + length > size:
            raise ValueError('GLB bufferView exceeds embedded buffer')
    if not isinstance(doc.get('images', []), list):
        raise ValueError('Invalid GLB images')
    for image in doc.get('images', []):
        if not isinstance(image, dict) or type(image.get('bufferView')) is not int or not 0 <= image['bufferView'] < len(views):
            raise ValueError('GLB images must use embedded bufferViews')
    for field in ('nodes', 'meshes', 'skins', 'animations'):
        if not isinstance(doc.get(field, []), list) or any(not isinstance(x, dict) for x in doc.get(field, [])):
            raise ValueError('Invalid GLB ' + field)
    if any('name' in clip and (not isinstance(clip['name'], str) or not clip['name']) for clip in doc.get('animations', [])):
        raise ValueError('Invalid GLB animation name')
    return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
            'nodes': len(doc.get('nodes', [])), 'meshes': len(doc.get('meshes', [])),
            'skins': len(doc.get('skins', [])),
            'animations': [x.get('name', str(i)) for i, x in enumerate(doc.get('animations', []))],
            'container_validation': 'PASSED', 'engine_import': 'PENDING'}


def _read_glb(source):
    source = Path(source)
    if source.suffix.lower() != '.glb':
        raise ValueError('Export Blender/other tools to embedded GLB first')
    if not source.is_file() or source.stat().st_size > MAX_GLB_BYTES:
        raise ValueError('GLB must be a file of at most 128 MiB')
    with source.open('rb') as stream:
        data = stream.read(MAX_GLB_BYTES + 1)
    if len(data) > MAX_GLB_BYTES:
        raise ValueError('GLB exceeds 128 MiB')
    return data


def inspect_glb(source):
    """Return container facts. Rig correctness still requires real Godot import."""
    return _container(_read_glb(source))


def stage_glb(source, destination, metadata, locked_reference=None):
    """Copy immutable bytes only after intake approval, never infer art approval."""
    record = metadata_record(metadata, locked_reference, require_approval=True)
    data = _read_glb(source)
    facts = _container(data)
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('Never overwrite an existing approved asset')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(data)
    return dict(record, **facts, file=destination.name,
                status='STAGED_REQUIRES_ENGINE_RIG_AND_VISUAL_REVIEW')
