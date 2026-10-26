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


# Synthetic humanoid rig: seven joints, rigid box skinning and Meshy/Mixamo-style
# clip names. Test geometry only; it is never a character, approved or shipped.
HUMANOID_JOINTS = [  # name, parent index, local translation
    ('Hips', None, (0, 0.95, 0)), ('Spine', 0, (0, 0.25, 0)), ('Head', 1, (0, 0.35, 0)),
    ('LeftArm', 1, (0.25, 0.2, 0)), ('RightArm', 1, (-0.25, 0.2, 0)),
    ('LeftLeg', 0, (0.12, -0.05, 0)), ('RightLeg', 0, (-0.12, -0.05, 0))]
HUMANOID_BOXES = [  # joint, center, size, material
    (0, (0, 0.95, 0), (0.35, 0.2, 0.2), 0), (1, (0, 1.25, 0), (0.4, 0.45, 0.22), 0),
    (2, (0, 1.65, 0), (0.22, 0.24, 0.22), 1), (2, (0, 1.65, 0.13), (0.06, 0.06, 0.05), 2),
    (3, (0.3, 1.12, 0), (0.1, 0.55, 0.1), 1), (4, (-0.3, 1.12, 0), (0.1, 0.55, 0.1), 1),
    (5, (0.12, 0.45, 0), (0.14, 0.9, 0.14), 0), (6, (-0.12, 0.45, 0), (0.14, 0.9, 0.14), 0)]
HUMANOID_CLIPS = {  # clip name -> (length, {joint: [(time, axis, degrees)]}, hips translation keys)
    'Idle': (2.0, {1: [(0, 'x', 0), (1, 'x', 4), (2, 'x', 0)], 3: [(0, 'z', 4), (1, 'z', 8), (2, 'z', 4)],
                   4: [(0, 'z', -4), (1, 'z', -8), (2, 'z', -4)]}, None),
    'Walking': (1.0, {5: [(0, 'x', 25), (0.5, 'x', -25), (1, 'x', 25)], 6: [(0, 'x', -25), (0.5, 'x', 25), (1, 'x', -25)],
                      3: [(0, 'x', -20), (0.5, 'x', 20), (1, 'x', -20)], 4: [(0, 'x', 20), (0.5, 'x', -20), (1, 'x', 20)]}, None),
    'Running': (0.6, {5: [(0, 'x', 45), (0.3, 'x', -45), (0.6, 'x', 45)], 6: [(0, 'x', -45), (0.3, 'x', 45), (0.6, 'x', -45)],
                      3: [(0, 'x', -40), (0.3, 'x', 40), (0.6, 'x', -40)], 4: [(0, 'x', 40), (0.3, 'x', -40), (0.6, 'x', 40)],
                      1: [(0, 'x', 12), (0.6, 'x', 12)]}, None),
    'Jump': (0.6, {5: [(0, 'x', 0), (0.3, 'x', 35), (0.6, 'x', 10)], 6: [(0, 'x', 0), (0.3, 'x', 35), (0.6, 'x', 10)],
                   3: [(0, 'z', 0), (0.3, 'z', 120), (0.6, 'z', 60)], 4: [(0, 'z', 0), (0.3, 'z', -120), (0.6, 'z', -60)]}, None),
    'Attack': (0.45, {4: [(0, 'x', 0), (0.2, 'x', -110), (0.45, 'x', 0)], 1: [(0, 'y', 0), (0.2, 'y', -25), (0.45, 'y', 0)]}, None),
    'Hit_Reaction': (0.4, {1: [(0, 'x', 0), (0.15, 'x', -22), (0.4, 'x', 0)], 2: [(0, 'x', 0), (0.15, 'x', -15), (0.4, 'x', 0)]}, None),
    'Death': (1.2, {0: [(0, 'x', 0), (1.2, 'x', -88)]}, [(0, (0, 0.95, 0)), (1.2, (0, 0.18, 0))]),
    'Bow': (1.5, {1: [(0, 'x', 0), (0.75, 'x', 45), (1.5, 'x', 0)]}, None),
}


def _quat(axis, degrees):
    import math
    half = math.radians(degrees) / 2
    s = math.sin(half)
    return [s if axis == 'x' else 0, s if axis == 'y' else 0, s if axis == 'z' else 0, math.cos(half)]


def humanoid_glb(clips=None):
    """Return (doc, blob) for the synthetic humanoid with the named clips."""
    clips = list(HUMANOID_CLIPS) if clips is None else list(clips)
    blob = bytearray()
    views, accessors = [], []

    def add(data, component, count, shape, minimum=None, maximum=None, target=None):
        while len(blob) % 4:
            blob.append(0)
        view = {'buffer': 0, 'byteOffset': len(blob), 'byteLength': len(data)}
        if target:
            view['target'] = target
        views.append(view)
        blob.extend(data)
        accessor = {'bufferView': len(views) - 1, 'componentType': component, 'count': count, 'type': shape}
        if minimum is not None:
            accessor.update(min=minimum, max=maximum)
        accessors.append(accessor)
        return len(accessors) - 1

    globals_ = []
    for name, parent, local in HUMANOID_JOINTS:
        base = (0, 0, 0) if parent is None else globals_[parent]
        globals_.append(tuple(b + l for b, l in zip(base, local)))
    faces = [((1, 0, 0), (0, 1, 2, 3)), ((-1, 0, 0), (4, 5, 6, 7)), ((0, 1, 0), (8, 9, 10, 11)),
             ((0, -1, 0), (12, 13, 14, 15)), ((0, 0, 1), (16, 17, 18, 19)), ((0, 0, -1), (20, 21, 22, 23))]
    primitives = []
    for material in range(3):
        positions, normals, joints, weights, indices = [], [], [], [], []
        for joint, center, size, box_material in HUMANOID_BOXES:
            if box_material != material:
                continue
            for normal, _ in faces:
                axis = [i for i in range(3) if normal[i]][0]
                others = [i for i in range(3) if i != axis]
                start = len(positions)
                for a, b in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
                    point = [0.0, 0.0, 0.0]
                    point[axis] = center[axis] + normal[axis] * size[axis] / 2
                    point[others[0]] = center[others[0]] + a * size[others[0]] / 2
                    point[others[1]] = center[others[1]] + b * size[others[1]] / 2
                    positions.append(point)
                    normals.append(normal)
                    joints.append((joint, 0, 0, 0))
                    weights.append((1.0, 0.0, 0.0, 0.0))
                quad = [start, start + 1, start + 2, start, start + 2, start + 3]
                # Counter-clockwise winding seen from the face normal.
                cross_sign = (1 if (others[0] + 1) % 3 == others[1] else -1) * normal[axis]
                indices.extend(quad if cross_sign > 0 else [quad[0], quad[2], quad[1], quad[3], quad[5], quad[4]])
        flat = [c for p in positions for c in p]
        pos = add(struct.pack('<%df' % len(flat), *flat), 5126, len(positions), 'VEC3',
                  [min(p[i] for p in positions) for i in range(3)], [max(p[i] for p in positions) for i in range(3)], 34962)
        nrm = add(struct.pack('<%df' % (3 * len(normals)), *[c for n in normals for c in n]), 5126, len(normals), 'VEC3', target=34962)
        jnt = add(struct.pack('<%dH' % (4 * len(joints)), *[c for j in joints for c in j]), 5123, len(joints), 'VEC4', target=34962)
        wgt = add(struct.pack('<%df' % (4 * len(weights)), *[c for w in weights for c in w]), 5126, len(weights), 'VEC4', target=34962)
        idx = add(struct.pack('<%dH' % len(indices), *indices), 5123, len(indices), 'SCALAR', target=34963)
        primitives.append({'attributes': {'POSITION': pos, 'NORMAL': nrm, 'JOINTS_0': jnt, 'WEIGHTS_0': wgt},
                           'indices': idx, 'material': material})
    ibm = []
    for g in globals_:
        ibm.extend([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -g[0], -g[1], -g[2], 1])
    ibm_accessor = add(struct.pack('<%df' % len(ibm), *ibm), 5126, len(globals_), 'MAT4')
    nodes = [{'name': 'Armature', 'children': [1, len(HUMANOID_JOINTS) + 1]}]
    for index, (name, parent, local) in enumerate(HUMANOID_JOINTS):
        children = [i + 1 for i, row in enumerate(HUMANOID_JOINTS) if row[1] == index]
        node = {'name': name, 'translation': list(local)}
        if children:
            node['children'] = children
        nodes.append(node)
    nodes.append({'name': 'SyntheticBody', 'mesh': 0, 'skin': 0})
    animations = []
    for clip in clips:
        length, tracks, hips = HUMANOID_CLIPS[clip]
        samplers, channels = [], []
        for joint, keys in tracks.items():
            times = [k[0] for k in keys]
            values = [c for k in keys for c in _quat(k[1], k[2])]
            t = add(struct.pack('<%df' % len(times), *times), 5126, len(times), 'SCALAR', [min(times)], [max(times)])
            v = add(struct.pack('<%df' % len(values), *values), 5126, len(keys), 'VEC4')
            samplers.append({'input': t, 'output': v})
            channels.append({'sampler': len(samplers) - 1, 'target': {'node': joint + 1, 'path': 'rotation'}})
        if hips:
            times = [k[0] for k in hips]
            values = [c for k in hips for c in k[1]]
            t = add(struct.pack('<%df' % len(times), *times), 5126, len(times), 'SCALAR', [min(times)], [max(times)])
            v = add(struct.pack('<%df' % len(values), *values), 5126, len(hips), 'VEC3')
            samplers.append({'input': t, 'output': v})
            channels.append({'sampler': len(samplers) - 1, 'target': {'node': 1, 'path': 'translation'}})
        animations.append({'name': clip, 'samplers': samplers, 'channels': channels})
    doc = {'asset': {'version': '2.0', 'generator': 'aeryvex synthetic test fixture'},
           'buffers': [{'byteLength': len(blob)}], 'bufferViews': views, 'accessors': accessors,
           'materials': [{'name': 'Suit', 'pbrMetallicRoughness': {'baseColorFactor': [0.16, 0.42, 0.95, 1], 'metallicFactor': 0, 'roughnessFactor': 0.7}},
                         {'name': 'Skin', 'pbrMetallicRoughness': {'baseColorFactor': [0.85, 0.72, 0.6, 1], 'metallicFactor': 0, 'roughnessFactor': 0.8}},
                         {'name': 'Visor', 'pbrMetallicRoughness': {'baseColorFactor': [0.44, 0.85, 1, 1], 'metallicFactor': 0, 'roughnessFactor': 0.3}}],
           'nodes': nodes, 'scenes': [{'nodes': [0]}], 'scene': 0,
           'skins': [{'joints': list(range(1, len(HUMANOID_JOINTS) + 1)), 'skeleton': 1, 'inverseBindMatrices': ibm_accessor}],
           'meshes': [{'name': 'SyntheticBody', 'primitives': primitives}]}
    if animations:
        doc['animations'] = animations
    return doc, bytes(blob)


def write_humanoid_fixture(path, clips=None):
    """Write the synthetic humanoid GLB and return its resolved path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc, blob = humanoid_glb(clips)
    write_glb(path, doc, blob)
    return path.resolve()
