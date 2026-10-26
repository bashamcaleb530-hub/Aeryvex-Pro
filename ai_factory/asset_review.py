"""Reviewable project asset inventory; staging does not replace game characters."""
import copy
from pathlib import Path
import re

from . import assets, core


def _managed_guard(path):
    managed = path / 'managed.json'
    if managed.exists():
        import json
        expected = json.loads(managed.read_text())
        actual = core.managed_files(path)
        if actual != expected:
            raise ValueError('Managed source edited; resolve before asset revision')
    elif (path / 'godot').exists():
        raise ValueError('Unmanaged game directory; resolve before asset revision')


def inspect(source, metadata):
    """Read-only intake summary, suitable for showing before the approval action."""
    facts = assets.inspect_glb(source)
    record = assets.metadata_record(metadata)
    if any(clip not in facts['animations'] for clip in record['animation_mapping'].values()):
        raise ValueError('Asset animation mapping names a missing clip')
    return dict(record, **facts, license_review='APPROVED' if record['license_approved'] else 'PENDING',
                visual_review='APPROVED' if record['visual_approved'] else 'PENDING',
                prototype_review='APPROVED' if record['prototype_approved'] else 'PENDING',
                production_art='BLOCKED')


def _asset_file(path, row):
    sha = row.get('sha256', '')
    if not isinstance(sha, str) or not re.fullmatch('[a-f0-9]{64}', sha):
        raise ValueError('Asset integrity failed: invalid hash')
    relative = 'assets/' + sha + '.glb'
    if row.get('file') != relative:
        raise ValueError('Asset integrity failed: unsafe file')
    source = path / relative
    if source.is_symlink() or not source.resolve().is_relative_to(path.resolve()) or not source.is_file() or core.digest(source) != sha:
        raise ValueError('Asset integrity failed: missing or changed GLB')
    return source


def inventory(path):
    """Expose review states and provenance without treating intake as approval."""
    path = Path(path)
    bible = core.load(path)
    rows = copy.deepcopy(bible.get('assets', []))
    for row in rows:
        try:
            _asset_file(path, row)
            row['integrity'] = 'VERIFIED'
        except (ValueError, OSError):
            row['integrity'] = 'FAILED'
        for field in ('license_review', 'visual_review', 'prototype_review', 'engine_import'):
            row.setdefault(field, 'PENDING')
    return {'revision': bible['revision'], 'assets': rows, 'production_art': 'BLOCKED',
            'limitations': ['Container inspection does not certify rigs, animation, appearance or engine import.',
                            'Staged assets are not automatically substituted for approved references or characters.']}


def _save(path, bible, action, sha):
    bible['revision'] += 1
    bible['history'].append({'revision': bible['revision'], 'prompt': action,
                             'provider': 'explicit_asset_review', 'asset_sha256': sha,
                             'config': copy.deepcopy(bible['config'])})
    core.save_revision(path, bible)
    return bible


def stage(path, source, metadata, character=None):
    """Create a Bible revision with a staged GLB and explicit independent states."""
    path = Path(path)
    _managed_guard(path)
    bible = core.load(path)
    locked = None
    if character is not None:
        if not isinstance(character, str) or not character.strip() or len(character) > 128:
            raise ValueError('Invalid character name')
        locked = bible.get('approved_appearance_references', {}).get(character)
        if locked is None:
            raise ValueError('Character requires an existing approved appearance reference')
    preview = inspect(source, metadata)
    assets.metadata_record(metadata, locked, require_approval=True)
    sha = preview['sha256']
    if any(row.get('sha256') == sha for row in bible.get('assets', [])):
        raise ValueError('Asset already staged; use explicit review')
    destination = path / 'assets' / (sha + '.glb')
    if (path / 'assets').is_symlink():
        raise ValueError('Symlink asset directory forbidden')
    record = assets.stage_glb(source, destination, metadata, locked)
    # The source may have changed between preview and intake. Never create a
    # filename/hash mismatch or approve the wrong bytes.
    if record['sha256'] != sha:
        destination.unlink()
        raise ValueError('Asset changed during intake; inspect again')
    record.update(file=destination.relative_to(path).as_posix(), character=character,
                  license_review=preview['license_review'], visual_review=preview['visual_review'],
                  prototype_review=preview['prototype_review'])
    bible.setdefault('assets', []).append(record)
    try:
        return _save(path, bible, 'Stage asset for review', sha)
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def review(path, sha256, *, license_approved=None, visual_approved=None, prototype_approved=None):
    """Record human decisions as a revision, without claiming an engine import."""
    choices = {'license': license_approved, 'visual': visual_approved, 'prototype': prototype_approved}
    if all(value is None for value in choices.values()):
        raise ValueError('No explicit review decision supplied')
    if any(value is not None and type(value) is not bool for value in choices.values()):
        raise ValueError('Review approvals must be booleans')
    path = Path(path)
    _managed_guard(path)
    bible = core.load(path)
    rows = [row for row in bible.get('assets', []) if row.get('sha256') == sha256]
    if len(rows) != 1:
        raise ValueError('Unknown or duplicate asset hash')
    row = rows[0]
    _asset_file(path, row)
    character = row.get('character')
    locked = bible.get('approved_appearance_references', {}).get(character) if character else None
    if character and locked is None:
        raise ValueError('Character requires an existing approved appearance reference')
    assets.metadata_record(row, locked, require_approval=True)
    if license_approved is True and row['license'].casefold() in assets.UNKNOWN_LICENSES:
        raise ValueError('Unknown license cannot be approved')
    for field, value in choices.items():
        if value is not None:
            row[field + '_review'] = 'APPROVED' if value else 'PENDING'
            row[field + '_approved'] = value
    return _save(path, bible, 'Review staged asset', sha256)
