# Go 32 — Integrated battlefield visibility and presentation

Expanded the current 3D Godot project in place. Added reusable short-lived tracer meshes (16 pooled nodes), barricade-aware infantry firing obstruction, and layered infantry helmet/visor/armor/boots. This directly upgrades team battles and makes cover influence whether shots connect. No new game mode and no loss of earlier work.

**Limitations:** barricade obstruction is a 2D proximity approximation, not mesh-raycast collision. Infantry remain low-poly. Only barricades are accounted for, not other architecture; full bullet physics, audiovisual impact effects, and character animation polishing remain. Godot engine runtime was not available here, so drawing/orientation and gameplay require validation in Godot 3.5/3.6. Python static tests and archive validation are not equivalent to engine execution.

**Progress:** Go 32/40, historical provisional realism implementation score 46%. No percentage increase claimed without visual verification.
