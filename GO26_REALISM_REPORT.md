# Go 26 — Skeletal skinning runtime verification harness

Added `tests/runtime_skinning.gd`, a Godot 3 headless regression test that constructs the humanoid rig plus limb, torso and joint-transition skinned meshes. It checks bone indices, normalized weights, triangle index bounds, and shoulder bone rotation. Registered it in `tools/run_godot_tests.sh` alongside the previous four runtime tests. Added `tests/test_go26_skinning.py` for structural validation of the harness.

## Verification
- Go 26 structural harness checks: passed.
- Existing Python structural checks: passed.
- Godot engine runtime checks: **not executed here** (Godot 3 executable unavailable). The new test may uncover errors that require further correction.
- Visual realism: **not verified**. No new production character meshes or textures were added in this go.

## Realism tracker
Estimated implementation progress remains **38%** from Go 25. This was a verification milestone rather than independently verified improvement in appearance. It is not a measured visual quality score.

## Execute real skinning tests
From the unzipped project root, run `bash tools/run_godot_tests.sh` with Godot 3.5 or 3.6 installed; override with `GODOT_BIN=/path/to/godot` if needed. Capture the printed engine errors to guide corrections.
