# Go 18 — locomotion inertia & stride cadence

## Implementation
- Replaced fixed gait cadence with smoothed speed-responsive cadence.
- Added damped body inertia on starts/stops and a subtle forward lean at speed.
- Suppressed locomotion lean during strikes and defeated poses.
- No combat timing, collision, or game-mode changes.

## Verification
- Existing Python static test suites pass.
- Go 18's 7 additional static assertions pass.
- Godot was not installed in this execution environment: engine parsing, visual quality, controller playtesting, and FPS are **not verified**.
- This remains a procedural pivot-rig prototype, not skeletal IK or a realistic character mesh.

## Next high-value realism work
- Introduce actual skinned mesh + Skeleton assets; render visually in Godot.
- Measure foot sliding and pose transitions with captured video, rather than relying only on code checks.
