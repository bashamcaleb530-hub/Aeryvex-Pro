from pathlib import Path
s=(Path(__file__).resolve().parents[1]/'scripts/Main.gd').read_text()
checks={
    'hero swings hit soldiers':'_hurt_soldier(unit, data["damage"])' in s,
    'force affects enemy infantry':'_hurt_soldier(unit, 24.0)' in s,
    'one death ticket update':'func _hurt_soldier(unit, damage):' in s and 'if unit["hp"] <= 0.0 or match_done:' in s,
    'soldiers can target heroes':'hero_index = 1 - unit["team"]' in s,
    'soldier shots damage heroes':'_damage(hero_index, 5.0, -1, 4.0)' in s,
    'no conflict markers':'<<<<<<<' not in s,
}
for k,v in checks.items():print(('PASS' if v else 'FAIL'), k)
assert all(checks.values())
print(f'{len(checks)}/{len(checks)} Go 9 checks passed')
