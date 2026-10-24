# Go 11 — face proportions and layered hair

Updated `scripts/FighterVisual.gd` from the Go 10 source:
- Added low-poly nose bridge, chin, brow ridge and temples with differentiated shapes.
- Added variant jaw stubble to two fighters.
- Added tapered hair locks and fringe on non-helmet, non-hooded fighters.
- All geometry is generated in Godot and uses original procedural meshes.

Verification: all Python source-check scripts, including new `tests/check_go11_realism.py`, pass. The Godot engine is not installed in this environment; runtime rendering, gameplay and FPS testing remain unverified. This is a procedural art pass, not the final photorealistic/fully skinned character-model milestone.

Realism scorecard (estimated qualitative indicator, not a measured percentage): Go 10 baseline 12/100; Go 11 14/100. The two-point gain reflects implementation and structural checks only; visual quality needs engine review.
