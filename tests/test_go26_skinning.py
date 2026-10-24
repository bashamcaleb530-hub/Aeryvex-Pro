from pathlib import Path
root = Path(__file__).resolve().parents[1]
test = (root/'tests'/'runtime_skinning.gd').read_text()
runner = (root/'tools'/'run_godot_tests.sh').read_text()
assert 'runtime_skinning' in runner
assert 'Mesh.ARRAY_WEIGHTS' in test
assert 'Mesh.ARRAY_BONES' in test
assert 'triangles.size() % 3' in test
assert 'abs(total - 1.0)' in test
assert 'set_bone_pose' in test
assert 'GO26_RUNTIME_SKINNING_PASS' in test
print('Go 26 structural skinning checks passed')
