# Go 24 — Shoulder and neck weight blending

Extended the skinned torso garment to use four influences: hips, spine, the nearby upper-arm bone, and head. The upper chest ring blends progressively toward shoulder rotations and the central neckline gains head influence. Bone weights remain normalized for every vertex. Existing fallback geometry and all other gameplay are preserved.

This is a procedural garment deformation improvement, **not** production-quality anatomy or a facial rig. Needs Godot 3 runtime and visual validation. Realism implementation tracker: provisional 36% (previous 34%); verified rendering quality remains unknown.
