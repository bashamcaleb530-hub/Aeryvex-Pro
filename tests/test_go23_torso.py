from pathlib import Path
root = Path(__file__).resolve().parents[1]
s = (root / 'scripts/SkinnedTorso.gd').read_text()
v = (root / 'scripts/FighterVisual.gd').read_text()
checks = {
    'weight arrays': 'Mesh.ARRAY_BONES' in s and 'Mesh.ARRAY_WEIGHTS' in s,
    'hip and spine support': 'find_bone("hips")' in s and 'find_bone("spine")' in s,
    'six shaped rings': s.count('[1.') >= 5 and '[0.94' in s,
    'skeleton linked': 'skeleton = NodePath("..")' in s,
    'weight normalization': '1.0 - section[3]' in s and 'section[3] * torso_weight' in s and '1.0 - shoulder_weight - neck_weight' in s,
    'triangle surface': 'Mesh.PRIMITIVE_TRIANGLES' in s,
    'mesh wired': 'SkinnedTorso.new()' in v and 'WeightedTorsoGarment' in v,
    'fallback guarded': 'if skinned_torso.create_for_skeleton' in v,
}
for name, result in checks.items():
    assert result, name
print(f'Go 23 checks: {sum(checks.values())}/{len(checks)} passed')
