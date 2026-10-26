"""Combine animation clips from same-rig GLB files into one new embedded GLB.

Rigging services and animation libraries usually deliver one clip per file.
The game needs a single GLB whose AnimationPlayer holds every reviewed clip.
Channels are matched to the base rig by node name; any unmatched node is an
error, never silently dropped. The base mesh, skin and materials are untouched.
"""
import json
from pathlib import Path
import struct

from .assets import _container, _read_glb


def read_glb(path):
    data = _read_glb(path)
    _container(data)
    offset, doc, blob = 12, None, b''
    while offset < len(data):
        length, kind = struct.unpack_from('<II', data, offset)
        chunk = data[offset + 8:offset + 8 + length]
        if kind == 0x4E4F534A:
            doc = json.loads(chunk.decode('utf-8'))
        else:
            blob = chunk
        offset += 8 + length
    size = doc.get('buffers', [{}])[0].get('byteLength', 0) if doc.get('buffers') else 0
    return doc, bytearray(blob[:size])


def glb_bytes(doc, blob):
    doc = json.loads(json.dumps(doc))
    blob = bytes(blob)
    if blob:
        doc.setdefault('buffers', [{}])[0]['byteLength'] = len(blob)
    text = json.dumps(doc, separators=(',', ':')).encode('utf-8')
    text += b' ' * (-len(text) % 4)
    padded = blob + b'\0' * (-len(blob) % 4)
    total = 12 + 8 + len(text) + (8 + len(padded) if padded else 0)
    out = struct.pack('<4sII', b'glTF', 2, total) + struct.pack('<II', len(text), 0x4E4F534A) + text
    if padded:
        out += struct.pack('<II', len(padded), 0x004E4942) + padded
    return out


def _node_names(doc):
    names = {}
    for index, node in enumerate(doc.get('nodes', [])):
        name = node.get('name')
        if isinstance(name, str) and name:
            names.setdefault(name, []).append(index)
    return names


def merge_animations(base, donors, output):
    """donors: list of (path, {source clip: new name}); an empty dict takes every clip.

    Returns {'output', 'animations', 'added'}. Output must be a new .glb path.
    """
    output = Path(output)
    if output.suffix.lower() != '.glb' or output.exists() or output.is_symlink():
        raise ValueError('Merged output must be a new .glb file')
    doc, blob = read_glb(base)
    if not doc.get('buffers'):
        doc['buffers'] = [{'byteLength': 0}]
    doc.setdefault('bufferViews', [])
    doc.setdefault('accessors', [])
    doc.setdefault('animations', [])
    base_names = _node_names(doc)
    taken = {clip.get('name') for clip in doc['animations']}
    added = []
    for donor_path, rename in donors:
        rename = dict(rename or {})
        donor, donor_blob = read_glb(donor_path)
        donor_nodes = donor.get('nodes', [])
        copied = {}

        def copy_accessor(index):
            if index in copied:
                return copied[index]
            accessor = dict(donor['accessors'][index])
            if 'sparse' in accessor or 'bufferView' not in accessor:
                raise ValueError('Sparse or view-less animation accessors are not supported')
            view = dict(donor['bufferViews'][accessor['bufferView']])
            start = view.get('byteOffset', 0)
            data = bytes(donor_blob[start:start + view['byteLength']])
            if len(data) != view['byteLength']:
                raise ValueError('Donor animation data exceeds its buffer')
            while len(blob) % 4:
                blob.append(0)
            view.update(buffer=0, byteOffset=len(blob))
            view.pop('target', None)
            blob.extend(data)
            doc['bufferViews'].append(view)
            accessor['bufferView'] = len(doc['bufferViews']) - 1
            doc['accessors'].append(accessor)
            copied[index] = len(doc['accessors']) - 1
            return copied[index]

        clips = donor.get('animations', [])
        wanted = rename or {clip.get('name', str(i)): clip.get('name', str(i)) for i, clip in enumerate(clips)}
        found = {clip.get('name', str(i)) for i, clip in enumerate(clips)}
        missing = sorted(set(wanted) - found)
        if missing:
            raise ValueError('Donor has no clip named: ' + ', '.join(missing))
        for i, clip in enumerate(clips):
            source = clip.get('name', str(i))
            if source not in wanted:
                continue
            name = wanted[source]
            if not isinstance(name, str) or not name or len(name) > 128:
                raise ValueError('Invalid new clip name')
            if name in taken:
                raise ValueError('Clip name already exists in merged GLB: ' + name)
            samplers = [{'input': copy_accessor(s['input']), 'output': copy_accessor(s['output']),
                         **({'interpolation': s['interpolation']} if 'interpolation' in s else {})}
                        for s in clip.get('samplers', [])]
            channels = []
            for channel in clip.get('channels', []):
                target = dict(channel.get('target', {}))
                node = donor_nodes[target['node']] if type(target.get('node')) is int and target['node'] < len(donor_nodes) else {}
                matches = base_names.get(node.get('name'), [])
                if len(matches) != 1:
                    raise ValueError('Donor clip %s targets node %r that is absent or ambiguous in the base rig'
                                     % (source, node.get('name')))
                target['node'] = matches[0]
                channels.append({'sampler': channel['sampler'], 'target': target})
            doc['animations'].append({'name': name, 'samplers': samplers, 'channels': channels})
            taken.add(name)
            added.append({'source_file': Path(donor_path).name, 'source_clip': source, 'clip': name})
    if not added:
        raise ValueError('No animation clips were merged')
    data = glb_bytes(doc, blob)
    facts = _container(data)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('xb') as stream:
        stream.write(data)
    return {'output': str(output), 'sha256': facts['sha256'], 'animations': facts['animations'], 'added': added}
