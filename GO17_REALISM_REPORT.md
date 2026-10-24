# Go 17 — Stance compensation and gait polish

Added independently damped, bounded foot-pivot offsets during stance; the opposite foot returns to neutral during swing. Offsets return toward zero during dodges, defeat, and idle. This is **visual-only**; movement, collisions and hit registration are unchanged.

## Verification
All 20 Python structural suites passed (the Go 14 source assertion was refreshed to reference the newer Go 16 foot-lift code instead of the superseded knee formula). Archive integrity verified. Godot execution and visual footage review **not performed** because no Godot executable is installed in this environment. This is a procedural approximation, not world-space foot locking or skeletal IK.

## Realism tracker
Prior estimate: 24% implementation. Current provisional estimate: 26% implementation (subjective). Visual realism remains unverified; this is not a measured quality score.
