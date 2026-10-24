from pathlib import Path
p=Path(__file__).resolve().parents[1] / 'scripts' / 'FighterVisual.gd'
s=p.read_text()
checks = ['func _anatomy_and_garments(', 'UpperChestContour', 'WaistContour', 'LayeredTunicPanel', 'TunicBinding', 'BreastplateInset', 'func _joint_costume_detail(', 'DeltoidContour', 'WristCuff', 'UpperThighLayer', 'KneeGuard', 'BootToeCap', '_anatomy_and_garments(torso', '_joint_costume_detail(left_arm', '_joint_costume_detail(right_arm']
for item in checks:
    assert item in s, item
assert s.count('func _anatomy_and_garments(') == 1
assert s.count('func _joint_costume_detail(') == 1
print(f'GO12: {len(checks)+2}/{len(checks)+2} source assertions passed')
