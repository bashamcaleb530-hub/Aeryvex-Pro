from pathlib import Path
p = Path(__file__).resolve().parents[1] / 'scripts' / 'FighterVisual.gd'
s = p.read_text()
requirements = {
    'guard blending': 'guard_weight = lerp(',
    'one-shot hit response': 'if staggered and not last_hit_state:',
    'hit fade': 'hit_weight = max(0.0, hit_weight -',
    'smoothed windup': 'var ease_in = progress * progress',
    'smoothed contact': 'var contact = progress * progress',
    'smoothed recovery': 'var settle = 1.0 - progress * progress',
    'torso recoil': 'twist_target += 7.0 * hit_weight',
    'arm recoil': 'shoulder_swing-18.0*hit_weight',
    'preserved weapon motion': 'saber.rotation_degrees.z = lerp(',
}
for label, fragment in requirements.items():
    assert fragment in s, label
print(f'Go 15 static checks: {len(requirements)} passed')
