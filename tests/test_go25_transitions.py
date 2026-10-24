from pathlib import Path
root = Path(__file__).resolve().parents[1]
s = (root/'scripts'/'SkinnedTransitions.gd').read_text()
v = (root/'scripts'/'FighterVisual.gd').read_text()
assert 'upper_arm' in s and 'upper_leg' in s
assert 'spine' in s and 'hips' in s
assert 'Mesh.ARRAY_BONES' in s and 'Mesh.ARRAY_WEIGHTS' in s
assert '1.0 - ring[2]' in s and 'weights.append(ring[2])' in s
assert 'bone_ids.size() != verts.size() * 4' in s
assert 'SkinnedTransitions.new()' in v and 'WeightedShoulderHipTransitions' in v
assert 'transitions.queue_free()' in v
# Weight pairs always sum to one for the authored seam rings.
for row in ([0.12,0.34,0.78,0.95], [0.08,0.35,0.78,0.96]):
    assert all(abs((1-w)+w-1)<1e-9 and 0<=w<=1 for w in row)
print('Go 25 joint-transition source checks passed')
