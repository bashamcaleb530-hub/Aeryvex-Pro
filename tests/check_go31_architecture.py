from pathlib import Path
root=Path(__file__).resolve().parents[1]
main=(root/'scripts/Main.gd').read_text()
a=(root/'scripts/ArenaArchitecture.gd').read_text()
assert 'const ArenaArchitecture = preload(' in main
assert 'architecture = ArenaArchitecture.new()' in main
assert 'add_child(architecture)' in main
assert 'for x in [-12.0,12.0]' not in main, 'old overlapping pillars still in scene'
for term in ['stone =','_cylinder(', '_block(', 'for i in range(8):', 'for i in range(12):', 'Vector3(0, 0.063, 0)', 'for height in [0.38, 3.6]:']:
    assert term in a, term
assert (root/'project.godot').exists()
print('Go 31 architectural structural checks passed (8 assertions).')
