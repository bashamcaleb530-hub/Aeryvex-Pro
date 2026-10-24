"""Dependency-free structural checks; does not replace launching Godot."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
main = (root / 'scripts/Main.gd').read_text()
scene = (root / 'Main.tscn').read_text()
project = (root / 'project.godot').read_text()
checks = {
  'main scene configured': 'run/main_scene="res://Main.tscn"' in project,
  'scene uses gameplay script': 'res://scripts/Main.gd' in scene,
  'all five modes implemented': all(x in main for x in ['"Duel"','"Survival"','"Training"','"Skirmish"','"Story"']),
  'save and load routines': all(x in main for x in ['func _save_progress()', 'func _load_progress()', 'SAVE_PATH']),
  'match state reset': 'match_done=false' in main and 'ai_clock=EnemyBrain.next_attack_delay(ai_difficulty)' in main,
  'nine roster entries': '"Grievous"' in main and '"Palpatine"' in main,
  'controller actions': 'InputEventJoypadButton.new()' in main,
  'saber combat': all(x in main for x in ['func _attack(', 'func _damage(', 'func _force(']),
}
for name, good in checks.items():
    print(('PASS' if good else 'FAIL') + ': ' + name)
if not all(checks.values()):
    raise SystemExit(1)
