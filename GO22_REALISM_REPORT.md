# Go 22 — first actual weighted character mesh

Built on Go 21. Added `scripts/SkinnedLimbs.gd`, a Godot 3.x MeshInstance that builds indexed triangle geometry for arm sleeves and trouser legs. Each vertex has four bone-index slots and four weights, with gradients around elbows and knees. It is parented under the 13-bone `HumanoidSkeleton` and has a relative skeleton path. When mesh creation reports success, the overlapping primitive upper-arm, forearm, thigh and shin geometry is hidden; original pivot and costume hierarchy remains for compatibility and fallback.

**Limitations:** This is a simple four-limb deformation prototype, not a production human skin, UV texture set, fully rigged body, IK, or realistic character. Skeletal deformation in Godot 3 has not been visually verified. There may be binding/transform issues that require in-engine fixes. No gameplay modes were added.

## Tests
- `python tests/test_go22_skinning.py`: 8/8 structural checks pass.
- Existing `tests/test_*.py` and `tests/check_*.py`: passed.
- Godot engine executable: unavailable in this execution environment; no engine startup or frame-rate measurements.
- ZIP integrity: checked at packaging.

Realism tracker: **32% estimated implementation** (previously 30%). This is not a visual quality measurement.
