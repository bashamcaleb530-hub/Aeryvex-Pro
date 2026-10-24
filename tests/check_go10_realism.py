from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'scripts/FighterVisual.gd').read_text()
checks={
 'rounded tapered upper arms':'_taper(shoulder, "UpperArm"' in s,
 'tapered forearms':'_taper(elbow, "Forearm"' in s,
 'tapered thighs':'_taper(hip, "Thigh"' in s,
 'tapered shins':'_taper(knee, "Shin"' in s,
 'tapered torso':'_taper(torso, "Chest"' in s,
 'left foot pivot':'left_foot = left_knee.get_node("Foot")' in s,
 'right foot pivot':'right_foot = right_knee.get_node("Foot")' in s,
 'foot motion driven by legs':'left_foot.rotation_degrees.x' in s and 'right_foot.rotation_degrees.x' in s,
 'independent breathing clock':'breathing_clock += delta * 1.7' in s,
}
for name,ok in checks.items():print(('PASS' if ok else 'FAIL'),name)
if not all(checks.values()):raise SystemExit(1)
