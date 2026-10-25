# 3D generation milestone — 2026-10-25

This extends commit e5f0d4691c4288c4f70bfbf3002ce51ab471361f. Existing 2D template and Aeryvex Pro game/canon files are retained.

## Generate and revise

```bash
export GODOT_BIN=/path/to/Godot4
./factory new --name MyRPG --prompt 'A 3D RPG with 1 enemy and healing in ruins'
./factory build --project MyRPG
./factory test --project MyRPG
./factory add --project MyRPG --prompt 'Add an enemy, add lightning ability and a new area'
./factory build --project MyRPG
./factory test --project MyRPG
./factory status --project MyRPG
"$GODOT_BIN" --path factory_projects/MyRPG/godot
```

A prompt containing `3D` or `third-person` selects the new `rpg_3d` template at creation. Existing projects retain their template and requirements. Named numeric counts set totals; `add an enemy`, `add 2 enemies`, and `new area` increment existing values. Areas1..5, enemies0..12, speed2..12, and heal/shockwave/lightning are bounded data. `faster` increments walking speed. Unknown requests remain in the Bible as partially supported requirements, not falsely implemented features. 3D Ollama proposals are explicitly unavailable pending their schema; the existing 2D Ollama adapter is preserved.

## Implemented and runtime checked

Walkable modular ground terrain, differently colored adjacent areas, collision boundaries, solid ruin structures, ambient/directional lighting. Terrain is flat tiled ground, not a heightfield or authored realistic landscape. Runtime NavigationMesh excludes structure footprints with clearance. NavigationAgents follow paths around a real wall, use range detection, chase, and attack on cooldown with line-of-sight checks. Enemies have health/death and lose collision on defeat.

Third-person CharacterBody controller: WASD walk, Shift run, Space jump, gravity/floor/wall collision, mouse orbit/pitch and SpringArm camera obstruction handling. Click captures the mouse; Escape releases it. F/left-click does range/cone/line-of-sight melee with cooldown. 1/2/3 activate the configured ability order: heal restores health; lightning damages visible targets within14m; shockwave damages visible targets within5m. Energy cost40, passive recharge8/sec. Lightning currently implements damage mechanics, not branching electrical visual effects. It must not be described as final lightning art. R restarts the scene; victory/death are shown in the HUD.

The generated demo's revision retains heal and adds one enemy (1→2), lightning and an adjacent area (1→2). It preserves its original prompt, history, unchanged config and two immutable checkpoint JSONs. Generated files with user edits remain protected by the original managed-source guard.

Actual engine: official Godot4.2.2 on Linux, not a claimed Kaggle4.7.2 session. Both versions passed import, startup and behavior checks. Scenario covers walking/running, jumping/landing, structure collision, actual obstacle routing/chasing, enemy attack, melee/cooldown, heal/energy rejection, enemy death, camera orbit/obstruction, unapproved asset rejection, player death and restart; revised version additionally checks lightning damage and physical walking across the new area seam. Exact counts/logs/hashes are in verification/3d/initial.json and revised.json. Existing 2D game also passes Godot regression checks in 2d-regression.json. All Python tests (including previous9) pass: see python-tests.log.

## External asset interfaces

`ai_factory.assets.stage_glb` stages an external GLB only after explicit approval, provenance/license/reference metadata, container checks, optional exact locked-reference match and no-overwrite checks. This is staging, not production certification. Blender and other tools must export an embedded GLB first; automated .blend conversion is not implemented.

Generated `character_import.gd` uses Godot's actual GLTFDocument scene importer, requires skeleton/AnimationPlayer and mapped idle/walk/run/jump/attack/hit/defeat clips, and exposes blended clip playback. A synthetic weighted triangle GLB is imported and an attack animation advances in an actual isolated Godot test (asset-import.log). Synthetic test art is not shipped as an approved character. One native importer ownership warning is retained; the primitive-mesh teardown error discovered during development was fixed. No engine errors remain in that test.

This is an explicit presentation adapter interface, not automatic rig retargeting or automatic replacement of the gameplay capsule. Skin quality, materials/textures, dimensions, origins, clip fidelity, appearance match and binding still require review and integration. No approved reference image, ruler, concept or original_game file is changed. Existing placeholder capsules are prominently labeled prototype visuals. No invented model is presented as approved or realistic.

## Visual inspection and unfinished systems

Headless behavior is RUNTIME_CHECKED. Actual rendered quality, mouse/controller ergonomics, animation fidelity, target hardware FPS and Kaggle GPU behavior remain VISUAL_REVIEW_REQUIRED / NOT_TESTED. This milestone makes no screenshot or final-art acceptance claim. Native executable export remains unimplemented; QA produces an integrity-manifested Godot project ZIP requiring Godot.

Remaining work: terrain heightfields, production art and animation binding/retargeting, cinematic sequencing, physically animated melee hit frames, branching lightning VFX, custom ability synthesis, advanced enemy tactics, quests/story/inventory/progression generation, 3D LLM-provider schema and arbitrary genre generation. This is a playable reusable 3D combat/world prototype foundation, not a complete narrative RPG or a finished professional asset factory.

Persistent source, demo and checkpoints are committed to GitHub. The existing durability policy still applies: push future Kaggle project changes or use durable mounted storage before session loss. No automatic deployment or source replacement occurs.
