"""Go 2 *static* safety checks. These are not gameplay/runtime tests."""
from pathlib import Path
import re
root = Path(__file__).resolve().parents[1]
main = (root/'scripts/Main.gd').read_text()
checks = {
    'camera-relative movement': 'func _world_move(axis):' in main and 'sin(yaw)' in main and 'cos(yaw)' in main,
    'analog axis bindings': all(f'_bind_pad_axis("{a}"' in main for a in ['move_left','move_right','move_forward','move_back','camera_left','camera_right','camera_up','camera_down']),
    'controller input via actions': 'Input.get_action_strength("move_right")' in main and 'Input.get_joy_axis(' not in main,
    'stick deadzone': 'STICK_DEADZONE = 0.22' in main,
    'input magnitude bounded': 'min(1.0, input_axis.length())' in main,
    'camera orbit tracking': 'func _orbit_camera(delta):' in main and 'cam.look_at(_camera_target()' in main,
    'mouse camera orbit': 'InputEventMouseMotion and mouse_orbit' in main,
    'wheel zoom bounds': 'max(4.0, camera_distance - 0.6)' in main and 'min(11.0, camera_distance + 0.6)' in main,
    'pitch limits': all(s in main for s in ['deg2rad(10.0)', 'deg2rad(65.0)']),
    'camera recenter': '"recenter_camera":KEY_C' in main,
    'sprint consumes guard': 'stamina[0] = max(0, stamina[0] - 10.0 * delta)' in main,
    'sprint guard restrictions': 'not block and stamina[0] >= 12.0' in main,
    'movement smoothing': 'move_velocity.linear_interpolate(target' in main,
    'arena bounds': 'func _clamp_arena(pos):' in main and 'ARENA_EDGE = 13.0' in main,
    'directional dodge': 'dodge_dir = _world_move(_input_vector())' in main,
    'pause updates HUD': 'combat_log = "Paused" if paused else "Resumed"\n        _hud_update()' in main,
    'restart clears motion': 'move_velocity=Vector3.ZERO' in main,
    'Godot smoke test supplied': (root/'tests/runtime_smoke.gd').exists(),
    'script has no merge conflicts': not re.search(r'^(?:<<<<<<<|=======|>>>>>>>)', main, re.M),
    'original modes retained': all(f'"{mode}"' in main for mode in ['Duel','Survival','Training','Skirmish','Story']),
}
for label, valid in checks.items():
    print(('PASS' if valid else 'FAIL') + ': ' + label)
if not all(checks.values()):
    raise SystemExit(1)
print(f'Static checks: {sum(checks.values())}/{len(checks)} passed')
