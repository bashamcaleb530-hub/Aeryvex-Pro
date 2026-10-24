# Go 16 — Contact-aware procedural gait

Changed `scripts/FighterVisual.gd`: added phase-smoothed alternating stance weights, swing-foot local lift, knee flexion, and contact-weighted toe pitch. These are visual proxy improvements, **not** inverse kinematics, physically accurate planting, or a true Skeleton/SkinnedMesh rig. Combat collision remains unchanged.

Testing: Python structural regression suite and archive integrity; Godot executable unavailable here. Engine rendering, foot sliding, gameplay, and FPS are not verified.

Realism implementation estimate: **24%** (from 22%), subjective and not a visual-quality measurement.
