"""Bounded 3D RPG proposal adapter; unsupported text is retained in the Bible."""
import re, shutil
from .providers import validate as validate_2d
DEFAULT={'enemies':1,'areas':1,'speed':5,'abilities':['heal']}
def is_3d(prompt):return bool(re.search(r'\b3d\b|third.person',prompt,re.I))
def validate(config):
    if set(config)!=set(DEFAULT):raise ValueError('Invalid 3D fields')
    for k,lo,hi in [('enemies',0,12),('areas',1,5),('speed',2,12)]:
        if type(config[k]) is not int or not lo<=config[k]<=hi:raise ValueError('Invalid 3D '+k)
    a=config['abilities']
    if not isinstance(a,list) or len(a)!=len(set(a)) or not a or any(x not in ['heal','shockwave','lightning'] for x in a):raise ValueError('Invalid abilities')
    return dict(config,abilities=list(a))
def propose(prompt,current,model):
    if model!='template':raise ValueError('3D model-provider schema not implemented; use template')
    c=dict(current,abilities=list(current['abilities']))
    for key,noun in [('enemies',r'enem(?:y|ies)'),('areas','areas?')]:
        add=re.search(r'add\s+(an?|\d+)\s+(?:new\s+)?'+noun,prompt,re.I)
        total=re.search(r'(\d+)\s+'+noun,prompt,re.I)
        if add:c[key]+=int(add[1]) if add[1].isdigit() else 1
        elif total:c[key]=int(total[1])
        elif key=='areas' and re.search(r'new area',prompt,re.I):c[key]+=1
    for ability,pattern in [('heal',r'heal'),('lightning',r'lightning'),('shockwave',r'shockwave')]:
        if re.search(pattern,prompt,re.I) and ability not in c['abilities']:c['abilities'].append(ability)
    if re.search(r'faster',prompt,re.I):c['speed']+=1
    return validate(c)
def compile(game,templates):
    for p in (templates/'rpg_3d').glob('*.gd'):shutil.copyfile(p,game/p.name)
