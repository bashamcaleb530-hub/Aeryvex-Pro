# Go 20 — animation bind-pose correction

Go 19 was not issued as a separate package; this is explicitly Go 20 following Go 18.

## Changes
- Preserve both foot pivots' original rest transforms after they are constructed.
- Apply swing-foot vertical lift relative to each rest position.
- Apply stance-depth compensation relative to the original boot depth, rather than overwriting it.
- Added `tests/test_go20_bind_pose.py` to check correct application and guard against regression.

## Limitations
This corrects a real procedural rig transform bug, but the fighters remain proxy meshes without skeletal skinning or inverse kinematics. Full in-engine rendering and playtesting has not yet been completed; there is no evidence to claim a verified increase in visual realism.
