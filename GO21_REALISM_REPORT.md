# Go 21 — Skeletal rig foundation

## Implemented
- Added `scripts/HumanoidRig.gd`, an actual Godot 3 `Skeleton` with 13 named bones, parent relations, and bone rest transforms.
- Added a pose bridge from the existing procedural fighter pivots into Skeleton bone poses, preserving the combat/movement logic.
- Added `tests/check_go21_skeleton.py` for hierarchy and integration structural validation.

## Verification
- 23/23 Python test suites passed, including 7 new assertions.
- Godot 3 engine runtime is **not installed in this execution environment**. Runtime, visual rendering, animation deformation and frame rate remain unverified.
- No skinned mesh with vertex weights is included: this is a skeletal pipeline foundation, **not** completion of realistic skinning or final character models.

## Realism tracker
Previous provisional implementation estimate: 28%. Updated Go 21 implementation estimate: **30%** (heuristic, not a measured visual-quality score). Visual verification remains pending.

## Next
Bind weighted humanoid meshes to this skeleton and visually validate movement in Godot 3.6, then handle retargeting/inverse kinematics and detailed assets. Do not treat skeletal structure alone as a finished realistic character.
