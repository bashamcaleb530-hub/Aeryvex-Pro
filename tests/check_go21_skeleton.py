from pathlib import Path
p=Path(__file__).resolve().parents[1]
s=(p/'scripts/HumanoidRig.gd').read_text()
f=(p/'scripts/FighterVisual.gd').read_text()
assert 'extends Skeleton' in s
assert s.count('["') >= 13
assert 'set_bone_rest' in s and 'set_bone_parent' in s
assert 'set_bone_pose' in s
assert 'skeletal_rig.update_from_pivots' in f
assert 'HumanoidRig.new()' in f
assert 'left_foot_rest' in f and 'right_foot_rest' in f
print('Go 21 skeleton bridge: 7/7 structural assertions passed')
