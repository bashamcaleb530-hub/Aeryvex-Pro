# Go 28 — Sculpted head geometry

## Implementation
Replaced spherical underlying face shapes on unhelmeted fighters with a continuous triangle-surface head shell with jaw taper, a cheekbone contour, an eye-socket recess, and character-specific silhouette variations. Helmeted characters keep their original head proxies. Facial overlays (eyes, brows, nose, hair) and previous gameplay remain unchanged.

## Verification
- 29 pre-existing Python check scripts passed.
- 8 new source regression assertions passed.
- Godot runtime/visual checks: **not run** (Godot binary unavailable in this environment).
- This is original low-poly procedural geometry, **not** a photorealistic face or commercially polished character model.

## Progress
- Go: 28 / 40
- Provisional realism implementation baseline: **42%**, unchanged until a visual or engine test establishes improvement in practice.
- Visual realism score: not measured.

## Next blocker
Run and screenshot the characters in Godot 3.x. If overlays float above or intersect the new head profile, reposition face details to the sculpted surface. Complete facial topology and skinned neck deformation after inspection.
