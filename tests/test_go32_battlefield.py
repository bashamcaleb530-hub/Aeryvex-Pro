from pathlib import Path
s=(Path(__file__).resolve().parents[1]/'scripts'/'Main.gd').read_text()
checks = [
    'func _create_tracer_pool():', 'func _show_tracer(a, b):',
    'func _step_tracers(delta):', 'func _fire_line_clear(a, b):',
    'if not _fire_line_clear(origin, aim + Vector3(0, 1.0, 0)):',
    '_show_tracer(origin, aim + Vector3(0, 1.0, 0))',
    'var shot_tracers = []',
    'Layered uniform, helmet visor, torso plate, weapon and boots',
]
for check in checks:
    assert check in s, check
assert s.index('if not _fire_line_clear') < s.index('_show_tracer(origin')
assert 'Basis(Vector3.UP, axis)' not in s
print(f'Go 32 battlefield static checks passed: {len(checks)+2}')
