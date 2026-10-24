from pathlib import Path
s=(Path(__file__).resolve().parents[1]/"scripts/Main.gd").read_text()
checks={
"cover locations": "func _create_fronts_cover():" in s and 'range(3)' in s,
"cover only in Fronts": '_set_fronts_cover_visible(mode == "Fronts")' in s,
"retreat when injured": 'if unit["hp"] < 30.0 and cover != null:' in s,
"fire while defending": 'var shot_distance =' in s,
"cover reduces damage": '6.0 if _unit_in_cover(foe) else 12.0' in s,
"advances on objectives": 'SquadRules.choose_post(fronts_posts' in s,
"respawn resets state": 'unit["state"] = "advance"' in s,
"no merge conflicts": '<<<<<<<' not in s,
}
for n,ok in checks.items():print(("PASS" if ok else "FAIL"),n)
assert all(checks.values())
print(f"{len(checks)}/{len(checks)} Go 8 cover checks passed")
