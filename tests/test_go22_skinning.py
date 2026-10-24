from pathlib import Path
r = Path(__file__).resolve().parents[1]
source = (r/'scripts/SkinnedLimbs.gd').read_text()
visual = (r/'scripts/FighterVisual.gd').read_text()
rig = (r/'scripts/HumanoidRig.gd').read_text()
checks = {
    'bone indices': 'Mesh.ARRAY_BONES' in source,
    'bone weights': 'Mesh.ARRAY_WEIGHTS' in source,
    'skeleton binding': 'skeleton = NodePath("..")' in source,
    'arm and leg geometry': 'upper_arm' in source and 'upper_leg' in source,
    'blended joints': '0.48' in source and '0.52' in source,
    'mesh is created': 'SkinnedLimbs.new()' in visual,
    'old geometry hidden after creation': 'if skinned_limbs.create_for_skeleton' in visual,
    'rig retains pose bridge': 'update_from_pivots' in rig,
}
for name, ok in checks.items():
    assert ok, name
print(f'Go 22 structural checks: {len(checks)}/{len(checks)} passed')
