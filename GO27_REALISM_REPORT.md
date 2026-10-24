# Go 27 — Bridge shading and deformation continuity

## Implemented
- Shoulder and hip transition mesh normals now account for the bridge centerline direction. Previously all ring normals were horizontal even across diagonal shoulders, creating misleading specular/diffuse shading.
- Added a regression test for the code path and the perpendicular-normal math.
- Preserved all combat and game modes; no new features outside realism.

## Verification and limits
- Python source tests pass (see execution results). The test checks the normal math, not a screenshot or GPU rendering.
- Godot 3 executable was not found here. Deformation, mesh visibility, and frame rate remain unverified in Godot.
- Prior realism estimate was 38% implementation. This targeted lighting correction is insufficient to claim a measured 2-point gain; keep the estimate at 38% until in-engine validation.
