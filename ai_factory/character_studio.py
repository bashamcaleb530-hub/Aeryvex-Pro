"""Character Studio: approved reference -> 3D candidate -> engine inspection ->
human approval -> animation mapping -> Godot player binding.

Every decision that changes the game design is a new Bible revision. Provider
jobs, candidate files and inspection reports live beside the project under
characters/ and candidates/; they never approve anything by themselves.
"""
import copy
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

from . import assets, core
from .asset_review import _asset_file, _managed_guard, _save

CHARACTER = re.compile(r'^[A-Za-z][A-Za-z0-9 _-]{0,63}$')
CANDIDATE_ID = re.compile(r'^[a-z0-9-]{1,120}$')
IMAGE_TYPES = {'.png': b'\x89PNG\r\n\x1a\n', '.jpg': b'\xff\xd8\xff', '.jpeg': b'\xff\xd8\xff', '.webp': b'RIFF'}
MAX_REFERENCE = 20 * 1024 * 1024
GAMEPLAY_STATES = ('idle', 'walk', 'run', 'jump', 'fall', 'land', 'attack', 'hurt', 'death')
CINEMATIC_STATE = re.compile(r'^cinematic_[a-z0-9_]{1,40}$')
REQUIRED_FOR_PLAYABLE = ('idle', 'walk')
STATE_KEYWORDS = [  # ordered: first match wins for each clip
    ('death', ('death', 'dying', 'die', 'dead', 'defeat', 'knockout', 'ko')),
    ('hurt', ('hit', 'hurt', 'damage', 'react', 'injur', 'stagger', 'flinch')),
    ('attack', ('attack', 'punch', 'slash', 'strike', 'swing', 'kick', 'combo', 'melee', 'stab')),
    ('jump', ('jump',)), ('fall', ('fall', 'airborne', 'in_air')), ('land', ('land',)),
    ('run', ('run', 'sprint', 'jog')), ('walk', ('walk', 'move', 'locomotion')),
    ('idle', ('idle', 'stand', 'breath', 'rest')),
    ('cinematic_victory', ('victory', 'cheer', 'celebrat', 'win')), ('cinematic_bow', ('bow', 'salute', 'greet')),
]


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def character_name(name):
    if not isinstance(name, str) or not CHARACTER.fullmatch(name.strip()):
        raise ValueError('Character name must be 1-64 letters, digits, spaces, _ or -')
    return name.strip()


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', character_name(name).lower()).strip('-')


def character_dir(project, name):
    path = Path(project) / 'characters' / slug(name)
    for parent in [Path(project) / 'characters', path]:
        if parent.is_symlink():
            raise ValueError('Symlink character directory forbidden')
    return path


def validate_mapping(mapping, clips=None):
    if not isinstance(mapping, dict):
        raise ValueError('Animation mapping must be an object')
    result = {}
    for state, clip in mapping.items():
        if state not in GAMEPLAY_STATES and not (isinstance(state, str) and CINEMATIC_STATE.fullmatch(state)):
            raise ValueError('Unknown animation state: ' + str(state))
        if clip in (None, ''):
            continue
        if not isinstance(clip, str) or len(clip) > 256:
            raise ValueError('Invalid clip for ' + state)
        if clips is not None and clip not in clips:
            raise ValueError('Clip %r is not in this GLB' % clip)
        result[state] = clip
    return result


def suggest_mapping(clips):
    """Keyword suggestion only; the human confirms or edits it before staging."""
    mapping = {}
    for clip in clips:
        lowered = clip.lower()
        for state, words in STATE_KEYWORDS:
            if any(word in lowered for word in words):
                mapping.setdefault(state, clip)
                break
    return mapping


# ----------------------------------------------------------------- references

def lock_reference(project, character, data, extension, confirmed, note=''):
    """Store the exact approved image and lock its SHA-256 as the character's appearance."""
    project = Path(project)
    name = character_name(character)
    if confirmed is not True:
        raise ValueError('Confirm that this exact image is the approved appearance reference')
    extension = (extension or '').lower()
    if extension not in IMAGE_TYPES:
        raise ValueError('Reference must be PNG, JPG or WEBP')
    if not isinstance(data, (bytes, bytearray)) or not 0 < len(data) <= MAX_REFERENCE:
        raise ValueError('Reference image must be 1 byte to 20 MiB')
    if not bytes(data).startswith(IMAGE_TYPES[extension]) or (extension == '.webp' and data[8:12] != b'WEBP'):
        raise ValueError('File content does not match its image type')
    if not isinstance(note, str) or len(note) > 2000:
        raise ValueError('Note must be at most 2000 characters')
    _managed_guard(project)
    bible = core.load(project)
    sha = hashlib.sha256(data).hexdigest()
    locked = bible.get('approved_appearance_references', {}).get(name)
    if locked == sha:
        return {'status': 'ALREADY_LOCKED', 'character': name, 'sha256': sha, 'revision': bible['revision']}
    if locked is not None:
        raise ValueError('%s already has a locked approved reference; appearance locks are never replaced' % name)
    folder = project / 'references'
    if folder.is_symlink():
        raise ValueError('Symlink reference directory forbidden')
    folder.mkdir(exist_ok=True)
    target = folder / (sha + extension)
    if not target.exists():
        with target.open('xb') as stream:
            stream.write(data)
    bible.setdefault('approved_appearance_references', {})[name] = sha
    bible.setdefault('character_references', {})[name] = {
        'sha256': sha, 'file': target.relative_to(project).as_posix(), 'bytes': len(data),
        'extension': extension, 'note': note.strip(), 'locked_at': now(), 'approved_by': 'human'}
    _save(project, bible, 'Lock approved appearance reference for ' + name, sha)
    return {'status': 'LOCKED', 'character': name, 'sha256': sha, 'revision': bible['revision']}


def reference_file(project, character):
    project = Path(project)
    name = character_name(character)
    bible = core.load(project)
    locked = bible.get('approved_appearance_references', {}).get(name)
    info = bible.get('character_references', {}).get(name)
    if not locked or not info:
        raise ValueError('Lock an approved reference image for %s first' % name)
    path = project / info['file']
    if path.is_symlink() or not path.is_file() or core.digest(path) != locked:
        raise ValueError('Approved reference file is missing or changed; it will not be substituted')
    return path


# ----------------------------------------------------------------- candidates

def _registry_path(project, character):
    return character_dir(project, character) / 'candidates.json'


def list_candidates(project, character):
    path = _registry_path(project, character)
    return json.loads(path.read_text()) if path.is_file() else []


def _write_candidates(project, character, rows):
    core.write_json(_registry_path(project, character), rows)


def _candidate(project, character, candidate_id):
    if not isinstance(candidate_id, str) or not CANDIDATE_ID.fullmatch(candidate_id):
        raise ValueError('Invalid candidate ID')
    rows = list_candidates(project, character)
    for row in rows:
        if row['id'] == candidate_id:
            return rows, row
    raise ValueError('Unknown candidate')


def candidate_file(project, row):
    if not row.get('file'):
        raise ValueError('Candidate has no downloaded GLB yet')
    path = Path(project) / row['file']
    if path.is_symlink() or not path.is_file() or core.digest(path) != row['glb_sha256']:
        raise ValueError('Candidate GLB missing or changed')
    return path


def _publish_candidate(project, source):
    """Move a validated GLB into candidates/<sha>.glb (content addressed, never overwritten)."""
    facts = assets.inspect_glb(source)
    folder = Path(project) / 'candidates'
    if folder.is_symlink():
        raise ValueError('Symlink candidate directory forbidden')
    folder.mkdir(exist_ok=True)
    target = folder / (facts['sha256'] + '.glb')
    if not target.exists():
        shutil.copyfile(source, target)
    if core.digest(target) != facts['sha256']:
        raise ValueError('Candidate changed while publishing')
    return target, facts


def _record(project, character, row):
    rows = list_candidates(project, character)
    if any(r['id'] == row['id'] for r in rows):
        raise ValueError('Candidate already recorded')
    rows.append(row)
    _write_candidates(project, character, rows)
    return row


def _new_row(character, reference, provider, kind, **extra):
    return dict({'character': character, 'reference_sha256': reference, 'provider': provider, 'kind': kind,
                 'created': now(), 'updated': now(), 'status': 'SUBMITTED', 'file': None, 'glb_sha256': None,
                 'inspection': None, 'staged_sha256': None, 'visual_approved': False}, **extra)


def _locked(project, character):
    reference_file(project, character)
    return core.load(project)['approved_appearance_references'][character_name(character)]


def add_upload(project, character, data, source_label):
    """Register a GLB the user made elsewhere (Blender, Mixamo export, artist delivery)."""
    project = Path(project)
    name = character_name(character)
    locked = _locked(project, name)
    if not isinstance(source_label, str) or not source_label.strip() or len(source_label) > 500:
        raise ValueError('Describe where this GLB came from')
    with tempfile.TemporaryDirectory() as temp:
        source = Path(temp) / 'upload.glb'
        source.write_bytes(data)
        target, facts = _publish_candidate(project, source)
    row = _new_row(name, locked, 'upload', 'upload', id='upload-' + facts['sha256'][:16], status='DOWNLOADED',
                   file=target.relative_to(project).as_posix(), glb_sha256=facts['sha256'],
                   source_label=source_label.strip(), animations=facts['animations'])
    existing = [r for r in list_candidates(project, name) if r['id'] == row['id']]
    return existing[0] if existing else _record(project, name, row)


def meshy_generate(project, character, authorize_paid, opener=None):
    """Submit the exact locked reference bytes to Meshy Image-to-3D (may spend credits)."""
    from . import meshy_bridge
    if authorize_paid is not True:
        raise ValueError('Meshy requests may spend paid credits; explicit authorization is required')
    project = Path(project)
    name = character_name(character)
    locked = _locked(project, name)
    result = meshy_bridge.submit(reference_file(project, name), opener=opener)
    row = _new_row(name, locked, 'meshy', 'image_to_3d', id='meshy-' + result['task_id'].lower(),
                   task_id=result['task_id'])
    return _record(project, name, row)


def meshy_rig(project, character, candidate_id, authorize_paid, height_meters=1.7, opener=None):
    """Ask Meshy to auto-rig a succeeded Image-to-3D candidate (may spend credits)."""
    from . import meshy_bridge
    if authorize_paid is not True:
        raise ValueError('Meshy requests may spend paid credits; explicit authorization is required')
    project = Path(project)
    name = character_name(character)
    _, parent = _candidate(project, name, candidate_id)
    if parent['provider'] != 'meshy' or parent['kind'] != 'image_to_3d' or parent['status'] not in ('SUCCEEDED', 'DOWNLOADED'):
        raise ValueError('Rig a succeeded Meshy Image-to-3D candidate')
    result = meshy_bridge.submit_rigging(parent['task_id'], height_meters=height_meters, opener=opener)
    row = _new_row(name, parent['reference_sha256'], 'meshy', 'rigging', id='meshy-' + result['task_id'].lower(),
                   task_id=result['task_id'], parent=parent['id'])
    return _record(project, name, row)


def meshy_refresh(project, character, candidate_id, opener=None):
    from . import meshy_bridge
    project = Path(project)
    name = character_name(character)
    rows, row = _candidate(project, name, candidate_id)
    if row['provider'] != 'meshy':
        raise ValueError('Only Meshy candidates have remote status')
    if row['file']:
        return row
    info = meshy_bridge.task_status(row['kind'], row['task_id'], opener=opener)
    row.update(status=info['status'], progress=info.get('progress'), updated=now())
    _write_candidates(project, name, rows)
    return row


def meshy_fetch(project, character, candidate_id, opener=None):
    """Download a succeeded Meshy task. Rigging results merge their basic animations."""
    from . import meshy_bridge
    from .glb_tools import merge_animations
    project = Path(project)
    name = character_name(character)
    rows, row = _candidate(project, name, candidate_id)
    if row['provider'] != 'meshy':
        raise ValueError('Only Meshy candidates are downloaded from Meshy')
    if row['file']:
        return row
    with tempfile.TemporaryDirectory() as temp:
        downloaded = meshy_bridge.download_task_glbs(row['kind'], row['task_id'], Path(temp) / 'files', opener=opener)
        files = downloaded['files']
        if row['kind'] == 'rigging':
            base_key = next((k for k in files if 'rigged_character' in k), None)
            if base_key is None:
                raise ValueError('Meshy rigging result has no rigged character GLB')
            donors = [(info['file'], {}) for key, info in files.items() if key != base_key and info['facts']['animations']]
            if donors:
                merged = merge_animations(files[base_key]['file'], donors, Path(temp) / 'merged.glb')
                source = merged['output']
            else:
                source = files[base_key]['file']
        else:
            source = files.get('glb', next(iter(files.values())))['file']
        target, facts = _publish_candidate(project, source)
    row.update(status='DOWNLOADED', file=target.relative_to(project).as_posix(), glb_sha256=facts['sha256'],
               animations=facts['animations'], updated=now())
    _write_candidates(project, name, rows)
    return row


def merge_candidate_animations(project, character, candidate_id, donor_data, rename, source_label):
    """Add clips from a same-rig GLB (e.g. a separately downloaded death clip) as a NEW candidate."""
    from .glb_tools import merge_animations
    project = Path(project)
    name = character_name(character)
    _, base = _candidate(project, name, candidate_id)
    base_file = candidate_file(project, base)
    if not isinstance(rename, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in rename.items()):
        raise ValueError('Rename must map source clip names to new clip names')
    if not isinstance(source_label, str) or not source_label.strip() or len(source_label) > 500:
        raise ValueError('Describe where the animation file came from')
    with tempfile.TemporaryDirectory() as temp:
        donor = Path(temp) / 'donor.glb'
        donor.write_bytes(donor_data)
        merged = merge_animations(base_file, [(donor, rename)], Path(temp) / 'merged.glb')
        target, facts = _publish_candidate(project, merged['output'])
    row = _new_row(name, base['reference_sha256'], base['provider'], 'merge', id='merge-' + facts['sha256'][:16],
                   status='DOWNLOADED', file=target.relative_to(project).as_posix(), glb_sha256=facts['sha256'],
                   parent=base['id'], animations=facts['animations'], added_clips=merged['added'],
                   source_label=source_label.strip())
    existing = [r for r in list_candidates(project, name) if r['id'] == row['id']]
    return existing[0] if existing else _record(project, name, row)


# ----------------------------------------------------------------- inspection

def inspection_dir(project, character, sha):
    return character_dir(project, character) / 'inspections' / sha


def latest_inspection(project, character, sha):
    folder = inspection_dir(project, character, sha)
    runs = sorted(p for p in folder.glob('run-*') if (p / 'report.json').is_file()) if folder.is_dir() else []
    if not runs:
        return None
    report = json.loads((runs[-1] / 'report.json').read_text())
    report['run'] = runs[-1].relative_to(Path(project)).as_posix()
    return report


def inspect_candidate(project, character, candidate_id, mapping=None, godot_bin=None, render=True):
    from .character_inspect import inspect_character
    project = Path(project)
    name = character_name(character)
    rows, row = _candidate(project, name, candidate_id)
    source = candidate_file(project, row)
    facts = assets.inspect_glb(source)
    mapping = validate_mapping(mapping, facts['animations']) if mapping is not None else suggest_mapping(facts['animations'])
    folder = inspection_dir(project, name, row['glb_sha256'])
    folder.mkdir(parents=True, exist_ok=True)
    run = folder / ('run-%03d' % (len(list(folder.glob('run-*'))) + 1))
    report = inspect_character(source, run, mapping, godot_bin=godot_bin, render=render)
    row.update(inspection=run.relative_to(project).as_posix(), inspection_status=report['status'],
               suggested_mapping=mapping, updated=now())
    _write_candidates(project, name, rows)
    return dict(summarize(report), run=row['inspection'])


def summarize(report):
    return {k: v for k, v in report.items() if k not in ('log_tail', 'engine')}


# ----------------------------------------------------------------- decisions

def stage_candidate(project, character, candidate_id, license, author, mapping, intake_approved):
    """Stage an inspected candidate as a project asset with full provenance."""
    from .asset_review import stage
    project = Path(project)
    name = character_name(character)
    rows, row = _candidate(project, name, candidate_id)
    source = candidate_file(project, row)
    report = latest_inspection(project, name, row['glb_sha256'])
    if not report or report.get('engine_import') != 'PASSED':
        raise ValueError('Run a passing Godot inspection before staging')
    facts = assets.inspect_glb(source)
    mapping = validate_mapping(mapping or {}, facts['animations'])
    origin = {'meshy': 'Meshy %s task %s' % (row['kind'], row.get('task_id', row.get('parent', ''))),
              'upload': 'Uploaded GLB: ' + row.get('source_label', '')}.get(row['provider'], row['provider'])
    if row['kind'] == 'merge':
        origin += '; clips merged from ' + row.get('source_label', '')
    metadata = {'approved': intake_approved is True, 'license': license, 'author': author,
                'source': origin + '; generated from approved reference ' + row['reference_sha256'],
                'reference_sha256': row['reference_sha256'], 'animation_mapping': mapping}
    bible = stage(project, source, metadata, character=name)
    row.update(status='STAGED', staged_sha256=facts['sha256'], updated=now())
    _write_candidates(project, name, rows)
    return {'revision': bible['revision'], 'sha256': facts['sha256'], 'status': 'STAGED_PENDING_REVIEW'}


def _asset_row(bible, sha):
    rows = [row for row in bible.get('assets', []) if row.get('sha256') == sha]
    if len(rows) != 1:
        raise ValueError('Unknown or duplicate asset hash')
    return rows[0]


def decide(project, sha256, approve, license_approved=False, reason=''):
    """Human approval or rejection of a staged character's final appearance."""
    from .asset_review import review
    project = Path(project)
    if type(approve) is not bool:
        raise ValueError('Decision must be approve true/false')
    if not isinstance(reason, str) or len(reason) > 2000:
        raise ValueError('Reason must be at most 2000 characters')
    bible = core.load(project)
    row = _asset_row(bible, sha256)
    character = row.get('character')
    if not character:
        raise ValueError('Only character assets go through appearance approval')
    if approve:
        report = latest_inspection(project, character, sha256)
        if not report or report.get('engine_import') != 'PASSED':
            raise ValueError('Inspect this exact GLB in Godot before approving its appearance')
        return review(project, sha256, license_approved=True if license_approved is True else None, visual_approved=True)
    _managed_guard(project)
    _asset_file(project, row)
    row.update(visual_review='REJECTED', visual_approved=False, rejection_reason=reason.strip(), rejected_at=now())
    binding = bible.get('player_visual_binding')
    if isinstance(binding, dict) and binding.get('sha256') == sha256:
        bible.pop('player_visual_binding')
    return _save(project, bible, 'Reject character appearance for %s%s' % (character, ': ' + reason.strip() if reason.strip() else ''), sha256)


def set_mapping(project, sha256, mapping):
    project = Path(project)
    _managed_guard(project)
    bible = core.load(project)
    row = _asset_row(bible, sha256)
    facts = assets.inspect_glb(_asset_file(project, row))
    row['animation_mapping'] = validate_mapping(mapping, facts['animations'])
    return _save(project, bible, 'Set reviewed animation mapping for ' + str(row.get('character')), sha256)


def bind(project, sha256, target_height=1.8, yaw_offset_degrees=0, godot_bin=None):
    from .bind_player import bind as bind_player
    project = Path(project)
    row = _asset_row(core.load(project), sha256)
    report = latest_inspection(project, row.get('character'), sha256) if row.get('character') else None
    if not report or report.get('engine_import') != 'PASSED':
        raise ValueError('Inspect this exact GLB in Godot before binding it')
    return bind_player(project, row['character'], sha256, godot_bin=godot_bin,
                       target_height=target_height, yaw_offset_degrees=yaw_offset_degrees)


def unbind(project):
    project = Path(project)
    _managed_guard(project)
    bible = core.load(project)
    if 'player_visual_binding' not in bible:
        raise ValueError('No player visual is bound')
    sha = bible.pop('player_visual_binding')['sha256']
    return _save(project, bible, 'Unbind player visual; prototype capsule restored on rebuild', sha)


# ----------------------------------------------------------------- overview

def _step(status, detail=''):
    return {'status': status, 'detail': detail}


def overview(project):
    """Every character's true pipeline state, derived from files and the Bible."""
    project = Path(project)
    bible = core.load(project)
    status = core.status(project)
    qa = json.loads((project / 'qa.json').read_text()) if (project / 'qa.json').is_file() else None
    character_check = next((c for c in (qa or {}).get('checks', []) if c.get('name') == 'character'), None)
    binding = bible.get('player_visual_binding')
    names = sorted(set(bible.get('approved_appearance_references', {})) |
                   {a['character'] for a in bible.get('assets', []) if a.get('character')})
    characters = []
    for name in names:
        try:
            reference = bible.get('character_references', {}).get(name)
            reference_ok = bool(reference) and bool(reference_file(project, name))
        except ValueError:
            reference_ok = False
        candidates = list_candidates(project, name) if CHARACTER.fullmatch(name) else []
        staged = []
        for row in bible.get('assets', []):
            if row.get('character') != name:
                continue
            report = latest_inspection(project, name, row['sha256'])
            view = {k: row.get(k) for k in ('sha256', 'license', 'author', 'source', 'license_review',
                                            'visual_review', 'engine_import', 'animation_mapping', 'rejection_reason')}
            view.update(animations=assets.inspect_glb(project / row['file'])['animations'] if (project / row['file']).is_file() else [],
                        inspection=summarize(report) if report else None,
                        bound=isinstance(binding, dict) and binding.get('sha256') == row['sha256'])
            staged.append(view)
        approved = [a for a in staged if a['visual_review'] == 'APPROVED' and a['license_review'] == 'APPROVED']
        bound = next((a for a in staged if a['bound']), None)
        mapping = (bound or (approved[-1] if approved else {})).get('animation_mapping') or {}
        verification = ((bound or (approved[-1] if approved else {})).get('inspection') or {}).get('mapping_verification', {})
        missing = [s for s in REQUIRED_FOR_PLAYABLE if s not in mapping]
        steps = {
            'reference': _step('LOCKED' if reference_ok else ('MISSING_FILE' if name in bible.get('approved_appearance_references', {}) else 'MISSING')),
            'model': _step('READY' if any(c.get('file') for c in candidates) or staged else ('PENDING' if candidates else 'NOT_STARTED'),
                           '%d candidate(s)' % len(candidates)),
            'inspection': _step('PASSED' if any((a['inspection'] or {}).get('engine_import') == 'PASSED' for a in staged) or
                                any(c.get('inspection_status') == 'INSPECTED_PENDING_HUMAN_REVIEW' for c in candidates) else 'NOT_RUN'),
            'approval': _step('APPROVED' if approved else ('REJECTED' if staged and all(a['visual_review'] == 'REJECTED' for a in staged)
                                                           else ('PENDING' if staged else 'NOT_STAGED'))),
            'animation': _step('VERIFIED' if mapping and not missing and all(v.get('status') == 'ENGINE_VERIFIED' for v in verification.values())
                               and set(mapping) <= set(verification) else ('PARTIAL' if mapping else 'NONE_MAPPED'),
                               ('missing: ' + ', '.join(missing)) if missing else ''),
            'binding': _step('BOUND' if bound else 'NOT_BOUND'),
            'game_qa': _step(('PASSED' if character_check.get('passed') and status['qa'] == 'RUNTIME_CHECKED' else 'FAILED')
                             if bound and character_check else ('REBUILD_REQUIRED' if bound else 'NOT_APPLICABLE')),
        }
        characters.append({'name': name, 'reference': reference, 'candidates': candidates, 'assets': staged, 'steps': steps})
    return {'revision': bible['revision'], 'binding': copy.deepcopy(binding), 'characters': characters,
            'states': list(GAMEPLAY_STATES), 'required_states': list(REQUIRED_FOR_PLAYABLE)}
