"""Bounded 3D RPG proposal adapter; unsupported text is retained in the Bible."""
import re
import shutil

BASE = {'enemies': 1, 'areas': 1, 'speed': 5, 'abilities': ['heal']}
DEFAULT = dict(BASE, campaign=True, missions=3, mission_length=1, town=False)
OPTIONAL = {'campaign', 'missions', 'mission_length', 'town'}


def is_3d(prompt):
    return bool(re.search(r'\b3d\b|third.person', prompt, re.I))


def validate(config):
    # Previously persisted arena Bibles deliberately remain valid and unchanged.
    if not isinstance(config, dict) or not set(BASE) <= set(config) or set(config) - set(BASE) - OPTIONAL:
        raise ValueError('Invalid 3D fields')
    for key, lo, hi in [('enemies', 0, 12), ('areas', 1, 5), ('speed', 2, 12), ('missions', 1, 5), ('mission_length', 1, 3)]:
        if key in config and (type(config[key]) is not int or not lo <= config[key] <= hi):
            raise ValueError('Invalid 3D ' + key)
    for key in ['campaign', 'town']:
        if key in config and type(config[key]) is not bool:
            raise ValueError('Invalid 3D ' + key)
    abilities = config['abilities']
    if not isinstance(abilities, list) or not abilities or any(not isinstance(x, str) or x not in ['heal', 'shockwave', 'lightning'] for x in abilities) or len(abilities) != len(set(abilities)):
        raise ValueError('Invalid abilities')
    return dict(config, abilities=list(abilities))


def propose(prompt, current, model):
    if model == 'ollama':
        from .providers import OllamaProvider
        return OllamaProvider().propose_config(prompt,current,validate,
            'Godot 3D RPG: enemies integer0..12, areas integer1..5, speed integer2..12, abilities unique nonempty array of heal/shockwave/lightning. Optional existing fields: campaign boolean, missions integer1..5, mission_length integer1..3 shards, town boolean. Preserve every existing field. Unsupported requirements must not create extra fields; never invent finished assets or features.')
    if model != 'template':
        raise ValueError('Unavailable 3D provider: '+str(model))
    c = validate(current)
    if re.search(r'\bcampaign\b|\bmissions?\b', prompt, re.I):
        for key in OPTIONAL:
            c.setdefault(key, DEFAULT[key])
        c['campaign'] = True
    for key, noun in [('enemies', r'enem(?:y|ies)'), ('areas', 'areas?'), ('missions', 'missions?')]:
        add = re.search(r'add\s+(an?|\d+)\s+(?:new\s+)?' + noun, prompt, re.I)
        total = re.search(r'(\d+)\s+' + noun, prompt, re.I)
        if add:
            c[key] = c.get(key, DEFAULT[key]) + (int(add[1]) if add[1].isdigit() else 1)
        elif total:
            c[key] = int(total[1])
        elif key == 'areas' and re.search(r'new area', prompt, re.I):
            c[key] += 1
    for ability in ['heal', 'lightning', 'shockwave']:
        if re.search(ability, prompt, re.I) and ability not in c['abilities']:
            c['abilities'].append(ability)
    if re.search(r'faster', prompt, re.I):
        c['speed'] += 1
    if re.search(r'(?:longer|lengthen|extend).{0,25}missions?|missions?.{0,25}(?:longer|lengthen|extend)', prompt, re.I):
        c['mission_length'] = c.get('mission_length', 1) + 1
        c['campaign'] = True
    if re.search(r'\b(?:add|with|a|the)\s+(?:a\s+)?town\b', prompt, re.I):
        c['town'] = True
        c['campaign'] = True
    return validate(c)


def compile(game, templates):
    for path in (templates / 'rpg_3d').glob('*.gd'):
        shutil.copyfile(path, game / path.name)
