"""Data-only genre registry backed by existing validated deterministic compilers."""
import json
from pathlib import Path
import re

DIRECTORY = Path(__file__).with_name('genres')
BACKENDS = {'collect_survive_2d': 2, 'rpg_3d': 3}
MATCHES = {r'\b3d\b', 'third.person'}
FIELDS = {'schema_version', 'id', 'backend', 'label', 'dimensions', 'match', 'default', 'limitations'}


def validate_manifest(manifest):
    if not isinstance(manifest, dict) or set(manifest) != FIELDS:
        raise ValueError('Genre manifest requires only supported data fields')
    if manifest['schema_version'] != 1 or type(manifest['schema_version']) is not int:
        raise ValueError('Unsupported genre manifest version')
    backend = manifest['backend']
    if not isinstance(backend, str) or backend not in BACKENDS or manifest['id'] != backend:
        raise ValueError('Unsupported builtin genre backend')
    if type(manifest['dimensions']) is not int or manifest['dimensions'] != BACKENDS[backend]:
        raise ValueError('Invalid genre dimensions')
    if not isinstance(manifest['label'], str) or not manifest['label'].strip() or len(manifest['label']) > 128:
        raise ValueError('Invalid genre label')
    patterns = manifest['match']
    if not isinstance(patterns, list) or any(not isinstance(x, str) or x not in MATCHES for x in patterns) or len(set(patterns)) != len(patterns):
        raise ValueError('Genre matches must use supported builtin selection expressions')
    if type(manifest['default']) is not bool or manifest['default'] != (backend == 'collect_survive_2d'):
        raise ValueError('Invalid default genre')
    if (backend == 'collect_survive_2d' and patterns) or (backend == 'rpg_3d' and set(patterns) != MATCHES):
        raise ValueError('Genre must preserve builtin prompt selection')
    if not isinstance(manifest['limitations'], list) or not manifest['limitations'] or any(not isinstance(x, str) or not x.strip() or len(x) > 4096 for x in manifest['limitations']):
        raise ValueError('Genre limitations must be nonempty text')
    return json.loads(json.dumps(manifest))


def registry(directory=None):
    result = {}
    for path in sorted(Path(directory or DIRECTORY).glob('*.json')):
        manifest = validate_manifest(json.loads(path.read_text()))
        if manifest['id'] in result:
            raise ValueError('Duplicate genre manifest')
        result[manifest['id']] = manifest
    if set(result) != set(BACKENDS):
        raise ValueError('Both builtin genre manifests are required')
    return result


def get(template):
    entries = registry()
    if template not in entries:
        raise ValueError('Unsupported template: ' + str(template))
    return entries[template]


def select(prompt):
    if not isinstance(prompt, str):
        raise ValueError('Prompt must be text')
    entries = registry()
    for manifest in entries.values():
        if any(re.search(pattern, prompt, re.I) for pattern in manifest['match']):
            return manifest
    return next(manifest for manifest in entries.values() if manifest['default'])
