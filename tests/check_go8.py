from pathlib import Path
base=Path(__file__).resolve().parents[1]
s=(base/'scripts/Main.gd').read_text()
r=(base/'scripts/SquadRules.gd').read_text()
checks={
 'soldier unit limit': 'SOLDIERS_PER_TEAM = 3' in s,
 'creation in Fronts': 'if mode == "Fronts":\n        _create_fronts_soldiers()' in s,
 'cleanup on mode switching': '_clear_fronts_soldiers()' in s,
 'squad AI update in tick': '_step_fronts_soldiers(delta)' in s,
 'unit-versus-unit combat': '_hurt_soldier(foe, damage)' in s and 'var damage =' in s,
 'unit respawn countdown': 'unit["respawn"] = SOLDIER_RESPAWN' in s,
 'squad ticket penalty': 'fronts_tickets[unit["team"]]' in s,
 'units contribute to capture': 'if unit["team"] == 0:' in s and 'allies += 1' in s,
 'squads displayed in HUD': 'Squads %d:%d' in s,
 'changing post objectives': 'static func choose_post' in r and 'posts[i]["progress"]' in r,
 'no placeholder artifacts': '<<<<<<<' not in s,
}
for name,good in checks.items():
 print(('PASS' if good else 'FAIL'),name)
assert all(checks.values())
print(f'{len(checks)}/{len(checks)} Go 8 source checks passed')
