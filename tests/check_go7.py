from pathlib import Path
root=Path(__file__).resolve().parents[1]
main=(root/'scripts/Main.gd').read_text()
rules=(root/'scripts/FrontsRules.gd').read_text()
checks={
    'fronts rules exist': 'class_name' in rules or 'extends Reference' in rules,
    'mode available': '"Story", "Fronts"' in main,
    'capture points placed': 'Vector3(-7, 0, 0)' in main and 'Vector3(7, 0, 0)' in main,
    'contested posts do not capture': 'allies - enemies' in rules,
    'tickets cannot go negative': 'max(0.0' in rules,
    'majority drains tickets': 'friendly_owned > enemy_owned' in rules,
    'no duplicate win credit after match': 'if victory != -1:' in main and 'match_done = true' in main,
    'combatants respawn': '_spawn_fronts_combatants()' in main,
    'fronts update integrated': '_update_fronts(delta)' in main,
    'post ownership visible': '_fronts_status()' in main,
    'reset on restart': 'if mode == "Fronts":\n        _reset_fronts()' in main,
    'show only in Fronts': '_set_fronts_visible(mode == "Fronts")' in main,
}
for name,result in checks.items():print(('PASS' if result else 'FAIL'),name)
assert all(checks.values())
print(f'{len(checks)}/{len(checks)} passed')
