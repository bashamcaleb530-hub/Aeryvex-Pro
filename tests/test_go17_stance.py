from pathlib import Path
s = (Path(__file__).resolve().parents[1] / "scripts" / "FighterVisual.gd").read_text()
required = ["left_stance_offset", "right_stance_offset", "left_foot.translation.z", "right_foot.translation.z", "contact_blend", "if defeated or dodging:", "clamp(speed / 5.0"]
for name in required:
    assert name in s, name
assert s.index("left_foot.translation.z") < s.index("# Contact-aware toe pitch")
print("Go 17 stance checks: %s passed" % (len(required) + 1))
