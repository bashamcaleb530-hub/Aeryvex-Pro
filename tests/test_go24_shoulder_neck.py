from pathlib import Path
s = (Path(__file__).resolve().parents[1] / 'scripts' / 'SkinnedTorso.gd').read_text()
for expected in ['find_bone("upper_arm.L")', 'find_bone("upper_arm.R")', 'find_bone("head")', 'shoulder_weight', 'neck_weight', 'torso_weight', 'bone_ids.append(head)', 'weights.append(shoulder_weight)', 'weights.append(neck_weight)']:
    assert expected in s, expected
assert '1.0 - shoulder_weight - neck_weight' in s
print('Go 24 shoulder/neck structural assertions passed')
