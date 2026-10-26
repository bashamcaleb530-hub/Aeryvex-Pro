# One-command playable prototype creation

From repository root with Godot 4.2+ installed and `GODOT_BIN` configured:

```bash
./factory ship --name MyFirstRPG --prompt "Build a third-person 3D RPG with 3 enemies, healing, lightning and ruined arenas"
```

This performs **new → build → headless Godot QA → ZIP** automatically. The resulting
`factory_projects/MyFirstRPG/dist/MyFirstRPG.zip` is a **Godot project**, not a
native executable; Godot is required to play it. The tool reports
`BUILT_QA_BLOCKED` if Godot is missing or tests fail, and never claims a tested
ZIP in that case. Review the project in Godot to judge graphics and ergonomics.
For an existing project, use `./factory add --project MyFirstRPG --prompt "add an enemy"`
and then `./factory build --project MyFirstRPG && ./factory test --project MyFirstRPG`.

**Scope:** the one-command workflow speeds up the existing bounded 2D/3D
templates; it does NOT yet generate complete arbitrary games, realistic art,
full campaigns, rigged characters, or promise a full professional game in 24h.
It leaves unsupported instructions visible in the project bible for later work.

# Current extension: 3D generation

See [MILESTONE_2.md](MILESTONE_2.md) for the working 3D template, controls, revision syntax, real engine checks and remaining visual/asset work. The original 2D workflow below is retained.

# Aeryvex AI Game Factory

A working bounded Godot4 generator with persistent revisions. This is the first end-to-end template, not an arbitrary-game or realistic-3D generator. Existing `original_game/` is preserved verbatim and is never a generation target.

From repository root, Python3.10+:

```bash
export PATH="$PWD:$PATH"
export GODOT_BIN=/path/to/Godot4
factory new --prompt "A top down collection game with 5 coins" --name MyGame
factory plan --project MyGame
factory build --project MyGame
factory test --project MyGame
factory add --project MyGame --prompt "add 3 enemies and make the player faster and blue"
factory build --project MyGame
factory test --project MyGame
factory status --project MyGame
"$GODOT_BIN" --path factory_projects/MyGame/godot
python3 -m unittest discover -s ai_factory/tests -v
```

Arrow keys/WASD move, collect all coins to win, avoid chasing enemies, R restarts. Enemies have contact damage and invulnerability cooldown. Generated circles are explicitly prototype drawing, not finished artwork. Tests exercise movement, bounds, actual contact damage, win/loss and restart in Godot.

Template prompts understand numeric coin/enemy counts, speed number, faster/slower, and named green/blue/red/purple/yellow player colors. Revisions preserve previous config fields, project identity, prompt history, locks and immutable JSON checkpoints. Every raw prompt is retained as PARTIAL_TEMPLATE_SUPPORT: extra cities, dual swords, 3DRPGs, story and realistic art are NOT silently claimed implemented. In this initial parser “3 enemies” sets the total count; it is not an incremental enemy-count arithmetic command.

`factory new/add --provider ollama` uses an actual Ollama /api/chat structured proposal with strict bounds. Set FACTORY_MODEL and optional FACTORY_OLLAMA_URL; default is local127.0.0.1:11434. No server/model is bundled and no credits are required. This adapter is implemented but was not live-model tested here. It proposes configuration only, not arbitrary code. The default template provider is deterministic and requires neither GPU nor LLM. Arbitrary hosted-provider auth and broader model tool use remain future work; never put secrets in a bible or source.

Build preserves user-modified generated source by refusing to overwrite it. Resolve edits deliberately or keep a separate copy before regenerating. Tests fail on changed/unbuilt revisions, Godot errors even at exit0, missing result marker, absent engine, unsupported engine version or timeout. `qa.json` binds evidence to every file and exact bible hash; status invalidates stale results. Build itself reports IMPLEMENTED only; successful engine QA reports RUNTIME_CHECKED, with visual/hardware review still PENDING.

Successful QA creates `dist/<name>.zip` and an integrity manifest. This is a Godot project ZIP, not a native OS executable. Native export/template management is not implemented yet. No binary or external art generator is fabricated. Asset production, retargeting, Blender/rigging tool adapters, cinematic generation, arbitrary genres, GPU production and autonomous repair agents are still unfinished.

## Session loss and rollback

Bibles, plans, checkpoints, source and verification are plain files. `--workspace /durable/mounted/path` selects durable storage. Kaggle /kaggle/working is ephemeral: commit and push your project files after every confirmed revision before ending a session:

```bash
git add factory_projects/MyGame
git commit -m "Checkpoint MyGame requirements and generated game"
git push origin aeryvex-original-game
```

Do not commit `.qa`, `.godot`, secrets or `dist`. This release includes the verified example's two checkpoints in GitHub. Resume after reset by checking out the branch, setting GODOT_BIN, and running status/build/test on that existing project. Restore an earlier bible/checkpoint using Git on a separate branch; no destructive automatic rollback is performed. Simultaneous writers to the same project and automatic remote sync are not implemented.

## Protected Aeryvex Pro

`preservation.json` records the inspected source commit and original_game object IDs. Existing rulers, references, Orion staff-to-dual-swords, Thalen dual swords, lightning hierarchy, Void trials and Supreme Grand Master progression are user canon. This factory does not reinterpret or modify them. Reference metadata says approved source image binaries are not yet backed up; that remains an external blocker. Source/canon preservation is not a claim that all those game features are already playable.
