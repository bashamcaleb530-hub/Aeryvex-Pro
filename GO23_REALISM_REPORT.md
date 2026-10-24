# Go 23 — Weighted Torso Garment

Implemented `scripts/SkinnedTorso.gd`: a generated six-ring costume shell with sixteen radial segments, normals, UVs and four-slot bone weights per vertex. The garment interpolates between hips and spine bone influences. `FighterVisual.gd` attaches the mesh under `HumanoidSkeleton`, and hides coarse Chest/Waist geometry only when the skinned replacement is constructed successfully. Existing combat and modes are unchanged.

## Verification
All Python source-check scripts pass, including eight new Go 23 assertions. This tests source structure, NOT whether the rig deforms properly. No Godot executable is installed in this environment. In-engine rendering, clipping and frame rates are **not tested**. The rig does not yet weight shoulder/neck bones; this is a two-bone torso foundation, not complete realistic character skinning. The relative bone rest transforms also require validation before a believable deformation can be claimed.

Estimated implementation progress: 34% (previous 32%; +2 provisional for torso weighted geometry). Independently verified visual realism: not measured. Next step: run Godot headless import, inspect character mesh in motion and fix bind/rest mismatches before increasing quality claims.
