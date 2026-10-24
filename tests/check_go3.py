"""Static Go 3 regression checks. This is NOT an engine test."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
main = (root/'scripts/Main.gd').read_text()
rules = (root/'scripts/CombatRules.gd').read_text()
checks={
  'Godot 3 rules module present': 'extends Reference' in rules and 'const CombatRules = preload(' in main,
  'attack timing windup-active-recovery': all(s in main for s in ['"windup"','"active"','"recovery"','func _advance_strike(who, delta):']),
  'delayed hit resolution': 'strike["phase"] = "active"' in main and '_resolve_swing(who, data)' in main,
  'one hit per strike': 'if not strike["connected"]:' in main and 'strike["connected"] = true' in main,
  'facing & distance checked': 'func in_arc(' in rules and 'facing.normalized().dot(toward.normalized())' in rules,
  'stamina gates attacks': 'func can_start(' in rules and 'energy >= cost' in rules,
  'block & guard damage': '"guard_left"' in rules and '"block"' in rules,
  'parry staggers opponent': '"parry"' in rules and '"attacker_stagger"' in rules,
  'guard break lockout': '"guard_break"' in rules and '"defender_stagger"' in rules,
  'dodge immunity': '"dodge"' in rules and 'invulnerable' in rules,
  'player attack input linked': '_attack(0, "light")' in main and '_attack(0, "heavy")' in main,
  'enemy strike shares same rules': '_attack(1, choice_attack)' in main and 'EnemyBrain.attack_for_opening(' in main,
  'force has distinct cooldown': 'var cooldown = [0.0,0.0]  # Force cooldown' in main,
  'combo buffering': 'attack_buffer = kind' in main and 'var followup = attack_buffer' in main,
  'weapon pose animation': 'func _animate_saber(who):' in main,
  'AI block and parry': 'ai_block_time' in main and 'parry_window[1]' in main,
  'engine combat test included': (root/'tests/runtime_combat.gd').is_file(),
  'previous static tests preserved': all((root/f'tests/{x}').exists() for x in ('check_project.py','check_go2.py')),
}
for name, good in checks.items():
    print(('PASS' if good else 'FAIL')+': '+name)
if not all(checks.values()):
    raise SystemExit(1)
print(f'Static Go 3 checks: {sum(checks.values())}/{len(checks)} passed')
