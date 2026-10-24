# Go 8 continuation: battlefield cover & tactics

This update extends the same Go 8 Godot 3.x project.

## Added
- Six low, opposing-team barricade positions around the three command posts (visible in Fronts only).
- Injured infantry (<30/60 HP) retreats to the nearest team-side barricade.
- Units can continue shooting while defending cover; their movement objective and firing target are separate.
- Infantry taking shots near friendly cover receives 6 rather than 12 damage; this is a distance-based approximation, **not** ballistic occlusion.
- Respawn restores movement state, and cover is hidden outside Fronts mode.

## Verification
All static source-check scripts run in this environment. There is no Godot runtime installed here, so no engine execution, frame-rate or visual verification is claimed. The scripts check code patterns, not whether combat is fun or free of bugs.

## Important remaining work
Engine smoke testing, hero/infantry shared combat, proper line-of-sight, cover animations, performance testing on the target laptop, finished models and art.
