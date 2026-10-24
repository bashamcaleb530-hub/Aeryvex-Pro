from pathlib import Path
s=(Path(__file__).resolve().parents[1]/"scripts"/"Main.gd").read_text()
assert s.count("func _setup_cinematic_lighting():")==1
assert s.count("_setup_cinematic_lighting()") == 2
for expected in ("WarmKeySun", "CoolFill", "WarmRimLeft", "WarmRimRight", "ArenaEnvironment", "key.shadow_enabled = true", "fill.shadow_enabled = false", "rim.shadow_enabled = false", "rim.omni_range = 11.0"):
    assert expected in s, expected
assert s.count("var ambient = WorldEnvironment.new()") == 1
print("GO30_LIGHTING_PASS")
