from pathlib import Path
s=(Path(__file__).resolve().parents[1]/"scripts/FighterVisual.gd").read_text()
checks=["var gait_weight = 0.0", "gait_weight = lerp", "var step_bob =", "var plant =", "var anti_plant =", "left_foot.translation.y", "right_foot.translation.y", "head.rotation_degrees.z =", "11.0 * gait_weight", "max(delta, 0.0)"]
for item in checks:
    assert item in s, item
print(f"Go 14 animation checks: {len(checks)}/{len(checks)} passed")
