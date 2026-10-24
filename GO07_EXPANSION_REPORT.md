# Go 7 continuation — Fronts command-post improvements

Implemented in the existing Go 7 source, without moving the milestone counter to Go 8.

- Enemy fighter changes navigation priority to uncaptured command posts while not in close combat; retains close-range combat AI.
- Enemy target is cached until its post is captured, then reacquired.
- Fighter respawns prefer an owned command post far from the opposing fighter, otherwise fall back to the base spawn.
- Combat HUD shows capture progress at nearby posts.
- Added six new source regression checks (`tests/check_go7_expanded.py`).

## Verification
All eight `tests/check*.py` structural/source scripts run successfully. Existing `tests/runtime_fronts.gd` is included for actual Godot execution, but a Godot executable is not installed in this container, so engine testing is **not verified**.

## Remaining Go 7 limitations
Still a two-combatant objective prototype, not a squad battle. Godot 3.5/3.6 runtime tests and visual inspection are required before treating it as fully playable.
