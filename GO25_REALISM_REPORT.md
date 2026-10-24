# Go 25 — Shoulder and hip transition skinning

Implemented `scripts/SkinnedTransitions.gd`, which generates four deforming fabric transition regions between the torso and upper arms/legs. Each vertex has four Godot 3 bone slots, with two continuously blended influences totaling one. `FighterVisual.gd` instantiates the geometry under the existing `HumanoidSkeleton` and removes it if construction fails.

## Verification
All existing Python source test scripts and `tests/test_go25_transitions.py` passed. No Godot binary is installed in this execution environment; animation deformation, topology/winding, visual appearance, and frame-rate were **not** runtime tested. This is a low-poly costume transition, not production-ready anatomy or a photorealistic rig.

## Realism indicator
Estimated *implementation* progress: **38%** (Go 24: 36%). This is a subjective milestone tracker and not a visually verified realism score. Do not equate with playable quality or 100% readiness.

## Next priority
Run in-engine deformation tests on shoulder raises, lunges, and crouches; replace procedural rig proxies with integrated realistic skinned character assets.
