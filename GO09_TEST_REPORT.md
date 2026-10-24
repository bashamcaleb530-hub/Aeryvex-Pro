# Go 9 — Hero and infantry interaction

Implemented in `scripts/Main.gd`:
- Hero melee attack arcs can damage opposing infantry.
- Force push can damage nearby opposing infantry when the opposing hero is within Force range.
- Infantry fire can damage the opposing hero, using existing guard/dodge/hit logic.
- Centralized infantry damage and death handling ensures each death costs one ticket and initiates one respawn.
- Existing Fronts infantry combat uses the same shared damage routine.

Checks: all Python source/structural tests passed, including Go 9's six dedicated checks, after updating two Go 8 expectations to match the new shared death handler.

Limitations: no Godot 3 binary was available in this session; engine parsing, scene launch and actual playtesting remain unverified. Infantry still uses proximity shots (not raycasts or projectile collision). This is not final large-scale battle gameplay.
