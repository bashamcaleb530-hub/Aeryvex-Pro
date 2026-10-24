from pathlib import Path
s = (Path(__file__).resolve().parents[1] / 'scripts' / 'FighterVisual.gd').read_text()
checks = {
    'eyes and pupils': '"Pupil"' in s and '"Iris"' in s and '"EyeWhite"' in s,
    'face geometry': all(x in s for x in ['"Jaw"','"Nose"','"Brow"','"Cheek"','"Mouth"']),
    'costume detail': all(x in s for x in ['"Collar"','"Seam"','"ShoulderPlate"','"BeltPouch"']),
    'detail called on fighter': '_costume_details(torso, outfit, armored)' in s,
    'face detail called only on bare heads': '_face_details(head, skin, fighter_index)' in s,
    'retains poses': 'func animate_pose(' in s,
    'GLES2 compatible procedural meshes': 'CylinderMesh.new()' in s,
}
for name, ok in checks.items():
    print(('PASS' if ok else 'FAIL') + ': ' + name)
assert all(checks.values())
