from pathlib import Path
s = (Path(__file__).resolve().parents[1] / "scripts" / "FighterVisual.gd").read_text()
checks = ["left_plant_weight", "right_plant_weight", "left_foot.translation.y", "right_foot.translation.y", "left_pitch", "right_pitch", "stance_blend", "attack_phase", "hit_weight"]
for fragment in checks:
    assert fragment in s, fragment
print("Go 16 motion source checks: %d passed" % len(checks))
