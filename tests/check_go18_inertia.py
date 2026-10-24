"""Static regression checks for Go 18: animation-only locomotion inertia."""
from pathlib import Path
s = (Path(__file__).resolve().parents[1] / 'scripts' / 'FighterVisual.gd').read_text()
checks = {
    'accelerating and braking tracked': 'previous_motion_amount = amount' in s,
    'frame-length guard': 'max(delta, 0.016)' in s,
    'lean bounded': 'clamp(acceleration * 1.7, -8.0, 8.0)' in s,
    'cadence smoothed': 'stride_cadence = lerp(stride_cadence, cadence_target, cadence_alpha)' in s,
    'cadence drives gait': 'running_clock += delta * stride_cadence * gait_weight' in s,
    'lean avoided while attacking and downed': 'if not (attack or defeated)' in s,
    'torso drives visual change': 'locomotion_lean, blend' in s,
}
for label, good in checks.items():
    assert good, label
print(f'Go 18: {len(checks)}/{len(checks)} static checks passed')
