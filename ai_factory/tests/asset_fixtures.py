"""Generated synthetic test geometry only; never approved or packaged game artwork."""
import copy
import json
from pathlib import Path
import struct

STATES = ('idle','move','attack_light','attack_heavy','combo_1','combo_2','combo_3','guard','parry','dodge','hit','special','victory','defeat')

def synthetic_glb():
    # One skinned triangle, one joint, one two-key translation clip.
    blob = struct.pack('<9f', 0,0,0, 1,0,0, 0,1,0)
    views = [{'buffer':0,'byteOffset':0,'byteLength':36}]
    accessors = [{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3'}]
    for data, component, count, shape in [
        (bytes(24),5123,3,'VEC4'), (struct.pack('<12f',*([1,0,0,0]*3)),5126,3,'VEC4'),
        (struct.pack('<2f',0,1),5126,2,'SCALAR'), (struct.pack('<6f',0,0,0,0,1,0),5126,2,'VEC3')]:
        views.append({'buffer':0,'byteOffset':len(blob),'byteLength':len(data)})
        accessors.append({'bufferView':len(views)-1,'componentType':component,'count':count,'type':shape})
        blob += data
    doc = {'asset':{'version':'2.0'},'buffers':[{'byteLength':len(blob)}], 'bufferViews':views,'accessors':accessors,
           'nodes':[{'name':'Rig','children':[1,2]},{'name':'Bone'},{'name':'Body','mesh':0,'skin':0}],
           'scenes':[{'nodes':[0]}],'scene':0,'skins':[{'joints':[1],'skeleton':1}],
           'meshes':[{'primitives':[{'attributes':{'POSITION':0,'JOINTS_0':1,'WEIGHTS_0':2}}]}],
           'animations':[{'name':'idle','samplers':[{'input':3,'output':4}], 'channels':[{'sampler':0,'target':{'node':1,'path':'translation'}}]}]}
    return doc, blob


def write_glb(path, doc=None, blob=None):
    if doc is None: doc, blob = synthetic_glb()
    j = json.dumps(doc).encode(); j += b' ' * (-len(j)%4)
    blob += b'\0' * (-len(blob)%4)
    path.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(j)+len(blob)) + struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(blob),0x004e4942)+blob)


def write_rigged_fixture(path):
    """Write a native-engine fixture outside shipping asset directories; return its path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc, blob = synthetic_glb()
    doc['accessors'][0].update({'min':[0,0,0],'max':[1,1,0]})
    clip = doc['animations'][0]
    doc['animations'] = [dict(copy.deepcopy(clip),name=state) for state in STATES]
    write_glb(path,doc,blob)
    return path.resolve()
