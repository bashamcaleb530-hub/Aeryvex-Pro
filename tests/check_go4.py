"""Go 4 source validation only. Runtime behavior needs Godot 3.6."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
main=(root/'scripts/Main.gd').read_text()
visual=(root/'scripts/FighterVisual.gd').read_text()
checks={
    'visual module exists and is integrated': 'const FighterVisual = preload(' in main and 'FighterVisual.new()' in main,
    'all fighter identities supported': 'const HEIGHTS = [' in visual and 'const CLOTH = [' in visual,
    'separate animated shoulder pivots': 'left_arm = limbs[0]' in visual and 'right_arm = limbs[0]' in visual,
    'two knee/elbow chains': all(t in visual for t in ['side_label = "Left" if side < 0 else "Right"', 'side_label + "Arm"', 'side_label + "Leg"', '"Knee"', '"Elbow"']),
    'saber attached to wrist': 'saber = _pivot(wrist, "Saber"' in visual,
    'pose updates each tick': '_update_fighter_poses(delta)' in main and 'fighter.animate_pose(' in main,
    'locomotion animation': 'running_clock += delta' in visual and 'stride = sin(running_clock)' in visual,
    'attack phases drive animation': all(t in visual for t in ['attack_phase == "windup"','attack_phase == "active"','attack_phase == "recovery"']),
    'defense and recoil states drive animation': 'guard_raise =' in visual and 'stagger_tilt =' in visual,
    'defeat state present': 'if defeated:' in visual,
    'different visual palettes and silhouette': all(t in visual for t in ['const ROBES','const ARMOUR','HEIGHTS[fighter_index]']),
    'combat rules unchanged': (root/'scripts/CombatRules.gd').is_file() and '_resolve_swing(who, data)' in main,
    'engine animation tests supplied': (root/'tests/runtime_animation.gd').is_file(),
    'no old rigid fighter builder': 'func _fighter(idx):' in main and '_cube(root,Vector3(0,1.24' not in main,
}
for name, ok in checks.items(): print(('PASS' if ok else 'FAIL')+': '+name)
if not all(checks.values()): raise SystemExit(1)
print(f'Static Go 4 checks: {sum(checks.values())}/{len(checks)} passed')
