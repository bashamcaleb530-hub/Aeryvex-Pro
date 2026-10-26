# Aeryvex AI Game Factory

A local application that turns supported natural-language ideas into playable Godot 4 projects, tests them in the real engine, and exports source and Linux builds. It extends the existing factory; existing Aeryvex projects and approved character references are preserved.

## Launch on Debian 13

Python 3.10+ runs the application with **no pip packages, paid service, or GPU**. Godot 4.2+ is needed for game QA. Native Linux exports also need official Linux export templates matching the engine version exactly.

From this repository:

```sh
python3 -m ai_factory ui
```

Open **http://127.0.0.1:8765**. Default project storage is `factory_projects/`. A new game must have a new name; select an existing project to revise it. The UI shows requirements, configuration, history, actual job stages/logs, source/native downloads and a desktop game launcher. Preview/edit the downloaded source in Godot. The decorative header is not a generated-game preview.

Optional local installation, without sudo or modifying existing projects:

```sh
sh ai_factory/tools/setup_debian.sh
"${XDG_DATA_HOME:-$HOME/.local/share}/aeryvex-game-factory/bin/aeryvex-factory"
```

Setup refuses to overwrite an existing installation. For upgrades use a new `--prefix` and launch the source against your existing `--workspace`; back up the workspace first. `--check` only reports dependencies. On the same desktop, **Launch game** starts the checked game. A headless server cannot display it on another computer; download the Linux build instead.

If Godot is not on PATH, set these in the terminal before launching (replace paths/version with your own matching installation):

```sh
export GODOT_BIN="$HOME/Applications/Godot_v4.2.2-stable_linux.x86_64"
export FACTORY_EXPORT_TEMPLATES="$HOME/.local/share/godot/export_templates/4.2.2.stable"
python3 -m ai_factory ui
```

The template directory must contain `version.txt` (`4.2.2.stable` in this example), `linux_release.x86_64` and `linux_debug.x86_64`. Obtain these from the matching official Godot release/export-template download. The factory never silently installs an engine or templates. Absent templates block the native stage while a successfully checked Godot source ZIP remains available. Unzip the Linux archive and run `./game.x86_64` (use `chmod +x game.x86_64` if your extraction tool discarded permissions). Its `game.pck` must stay beside it.

## Build something playable

Use **3D RPG campaign** as a starting prompt, for example:

> A 3D RPG with 3 missions, a town, 2 enemies and a healing ability

Then revise the selected project:

> Add an enemy, add a new area and lightning, and make missions longer

This produces actual additional enemies, connected walkable terrain, a tested lightning damage ability and additional physical shard objectives. Prompts and unsupported clauses remain in the Game Bible. `make it photorealistic` and `give me three playable characters` do not silently manufacture finished assets or new controllers; unchanged supported configuration is explicitly recorded as `NO_SUPPORTED_CHANGE`.

The campaign measures active playtime and has mission dialogue, enemy combat, shard recovery, return objectives, checkpoint retry, XP, blade upgrades, potion/relic inventory, saves and an ending. The 2D genre has movement, pursuers, collection, health, victory/defeat and restart. All capsule/primitive art is prototype artwork.

### Campaign controls

| Action | Keyboard/mouse | Gamepad mapping |
|---|---|---|
| Move / run | WASD / Shift | Left stick / L3 |
| Camera | Mouse after click; Esc releases | Right stick |
| Jump / melee | Space / F or left click | A / X |
| Abilities | 1, 2, 3 | RB, LB, B |
| Speak / collect | E | Y |
| Potion / blade upgrade | H / U | D-pad up / right |
| Save / load | F5 / F9 | Keyboard |
| Retry checkpoint | R | Start |
| Large text / reduced motion | T / M | Keyboard |
| New campaign after ending | N | Keyboard |

Actual input events are tested; physical controller hardware is not certified. New campaigns default to three missions. Supported bounds: 1–5 missions, 1–3 shards per mission, 1–5 connected areas, 0–12 initial enemies, heal/shockwave/lightning. Campaign combat spawns at least one enemy and scales bounded encounters by mission. Zero initial enemies therefore does not mean a combat-free campaign. Towns are collidable prototype buildings, not authored realistic environments.

## Persistent work, revisions and budgets

`bible.json`, immutable `checkpoints/`, source integrity manifests, assets and history live in the chosen workspace. Interrupted checkpoint writes are recovered from the journal without deleting checkpoints. Restoring a checkpoint creates a **new revision**, preserving later requirements, locked references and staged assets. Managed source edits are preserved and block regeneration; reconcile/back up them explicitly rather than forcing replacement.

Build jobs persist under `<workspace>/.factory-jobs/`. You may close the browser while a local worker runs. Cancel terminates its subprocesses and leaves completed stages. Resume reconciles committed designs without replaying the prompt, reruns QA/native checks, and rejects conflicting later edits. An orphan worker/queued job becomes interrupted. One active job per project is allowed. A bounded import-cache retry is the current self-repair capability; it does not rewrite arbitrary broken gameplay code.

Budgets are elapsed-time limits (up to 86,400 seconds), not arbitrary-game 24-hour guarantees. This release targets small playable template slices. A larger vision is retained for future implementation. CPU-only testing and bounded scene generation work; final art production and human playtime are separate work.

Campaign saves live in Godot's user-data directory for the game name. F5 and mission actions save atomically. Compatible revisions migrate completed missions/XP/inventory and renew active objectives; added missions extend a completed campaign. Before incompatible or corrupt data is replaced, a byte-preserving backup is made. Never delete those backups if recovery is needed. QA uses isolated XDG directories and does not touch ordinary player saves.

For Kaggle/session recovery, copy the **entire workspace** (including Bible/checkpoints/assets), configuration and source to durable storage/Git. A downloadable Godot project ZIP contains the playable game, not the entire factory revision journal. Ephemeral `/kaggle/working` alone is insufficient storage.

## CLI

```sh
./factory new --name MyGame --prompt 'A 3D RPG with a town'
./factory add --project MyGame --prompt 'Add lightning and a new area'
./factory plan --project MyGame
./factory build --project MyGame
./factory test --project MyGame
./factory export --project MyGame
./factory status --project MyGame
./factory rollback --project MyGame --revision 1
./factory ship --name CoinGame --prompt 'A blue 2D game with 8 coins and 2 enemies'
./factory jobs
```

Use global `--workspace /durable/project/store` **before** the subcommand. `ship` retains its original new/build/test/source-ZIP behavior; the app includes the native stage by default. `export` returns a structured `BLOCKED`, `FAILED` or `NATIVE_CHECKED` report. Read that status, not just process exit code. Job inspection/resume/cancel is also available with `jobs --id ID --resume` or `--cancel`.

## Optional local Ollama

Choose Ollama in the UI or pass `--provider ollama` to `new`/`add`. Run your own authorized local server/model first. Set `FACTORY_OLLAMA_URL` (default `http://127.0.0.1:11434`) and `FACTORY_MODEL` (default `qwen3.5:4b`). No credentials are hardcoded. The adapter accepts bounded validated JSON data only, preserves existing fields, rejects executable/unknown fields, malformed/duplicate/nonfinite JSON and oversized responses. It has real HTTP-stub coverage for 2D/3D; no live Qwen model was available for this release's verification. It is not unrestricted autonomous code generation.

## Asset intake and genre packs

The UI inspects embedded GLB containers and stages explicitly approved intake with license/author/source/reference hash. Staging records independent license, visual, prototype and engine-import states. It does not replace approved artwork or characters. For larger files or review decisions:

```sh
./factory asset-stage --project MyGame --file model.glb --metadata provenance.json
./factory assets --project MyGame
./factory asset-review --project MyGame --sha256 ASSET_HASH --approve-license --approve-prototype
```

Metadata requires `approved: true`, `license`, `author`, `source`, and a 64-character `reference_sha256`. A character-specific stage also requires `--character NAME` with an existing matching locked reference. Optional `animation_mapping` refers to actual embedded clip names. External URIs/unsupported extensions and invalid buffer ranges are rejected. Intake approval is not a license/fidelity certification. Existing Godot GLB adapter tests validate a synthetic rig and animation; automatic production model binding/retargeting remains unfinished.

Data-only JSON manifests in `ai_factory/genres/` enumerate the two existing backend contracts. This is a safe registry, not an arbitrary code-loading plugin marketplace; new backend implementation is still required for other genres.


## Codex + Meshy + Godot production bridge (opt-in)

Codex can edit this repository, run the factory tests, and submit reviewable commits. Godot 4 is the runtime and exporter. Meshy is used **only** to create *candidate* 3D assets from your own local approved-reference images. The Meshy bridge is a Python standard-library command-line module; it is not yet wired into the factory UI, character binding, animation retargeting or gameplay scenes.

Create a Meshy API key through the [Meshy developer portal](https://docs.meshy.ai/en/api/quick-start). Meshy API usage can require paid credits. Do not paste or commit the key; store it in the local shell environment. Uploading an image sends its bytes to Meshy, so submit only images you are authorized to process.

```sh
export MESHY_API_KEY='your-key-locally-only'
python3 -m ai_factory.meshy_bridge submit --image /path/to/approved-reference.png
# Save the returned task_id, then check until SUCCEEDED:
python3 -m ai_factory.meshy_bridge status TASK_ID
python3 -m ai_factory.meshy_bridge download TASK_ID --output /path/to/new-candidate.glb
# Human-review candidate geometry, likeness, topology, textures, rig and license.
# Prepare provenance.json with your actual license, author, source,
# approved reference SHA-256, and explicit intake approval.
./factory asset-stage --project MyGame --file /path/to/new-candidate.glb --metadata provenance.json
./factory assets --project MyGame
```

Asset staging requires an existing game project and your **explicit** intake approval. A character-specific stage requires a matching locked appearance-reference SHA-256, supplied with `--character NAME`; this does not certify that Meshy matched the reference. Separate license, visual and engine checks must follow. A returned GLB is never auto-installed in a game or labeled approved. Use `GODOT_BIN=/path/to/godot python3 -m unittest discover -s ai_factory/tests -v` to run the complete suite, or `python3 -m unittest ai_factory.tests.test_meshy_bridge -v` for isolated bridge checks. Live paid Meshy requests were not run in this change.

After downloading a Meshy candidate, run the **isolated Godot engine-import check** before staging it:

```sh
python3 -m ai_factory.godot_candidate_check --glb /path/to/new-candidate.glb
# If Godot is not on PATH:
python3 -m ai_factory.godot_candidate_check --glb /path/to/new-candidate.glb --godot-bin /path/to/godot
```

This creates and deletes a temporary preview project, invokes Godot 4 in headless editor mode and reports whether the engine imported the candidate. It does **not** validate animation retargeting, gameplay character binding, licensing or faithful appearance. Results remain pending human review. Isolated tests: `python3 -m unittest ai_factory.tests.test_godot_candidate_check -v`.

## Reviewed character pack export

After staging a GLB and explicitly approving both license and visual review, export a **standalone** Godot character project without modifying the existing generated game:

```sh
python3 -m ai_factory.character_pack_cli \\
  --project-path factory_projects/MyGame \\
  --character Hero \\
  --output /tmp/HeroReview
godot --path /tmp/HeroReview --editor
python3 -m unittest ai_factory.tests.test_character_pack -v
```

The pack includes `character.glb`, an isolated runnable preview and `character_manifest.json` containing the locked appearance-reference hash, provenance, actual GLB animation names and requested mappings. The export requires exactly one approved asset for that character. It refuses missing references, unapproved license/appearance and missing mapped clips. Exporting is not animation retargeting or insertion into the game; its manifest expressly marks gameplay binding as not implemented. Real Godot engine import and human visual review of the exported preview are still necessary.

## Opt-in player visual binding (3D RPG)

The factory now supports explicitly selecting **one** reviewed GLB as the playable player's visual, while retaining its existing Godot movement/camera/combat controller. This is not animation retargeting or a guarantee of correct proportions; manually inspect the result.

1. Lock the character's appearance reference and stage its GLB with `--character NAME`.
2. Approve **both** license and visual review through the asset review workflow.
3. Run the selector below with the staged asset SHA-256; it runs a real isolated Godot import check and creates a **new** Bible revision only on success.
4. Build and test the game again; the new visual is loaded from `player_visual.glb` with an explicit manifest.

```sh
python3 -m ai_factory.bind_player --project-path factory_projects/MyGame \\
  --character Hero --sha256 STAGED_ASSET_SHA256 --godot-bin /path/to/godot
./factory build --project MyGame
./factory test --project MyGame
```

This path requires explicit prior reference-locking and approval; it will refuse missing evidence and cannot be enabled by a creative prompt alone. The game will retain its primitive collision capsule and controls even when a GLB visual is bound. Character skeleton retargeting, appearance quality, asset scale, and gameplay animation remain separate review tasks. Offline binding-gate tests: `python3 -m unittest ai_factory.tests.test_bind_player -v`.

## Embedded character animation playback (experimental)

For an explicitly approved and bound player GLB, the RPG actor now reads the recorded `animation_mapping` from `player_visual.json`, finds an embedded `AnimationPlayer`, and plays configured `idle`, `walk`, `run` and `attack` clips when those exact animation names exist. Missing clips are warned about and skipped; the existing player controller and fallback capsule remain. This **plays existing compatible animations only**, not automatic skeleton retargeting, rigging or production-quality choreography.

For live validation, rebuild and test an RPG containing a reviewed, skinned and animated GLB on a machine with Godot 4.2+: `./factory build --project MyGame && ./factory test --project MyGame`. Visually review scale, pose and transitions; current source contract tests do not prove runtime correctness.

## Validation and honest release scope

```sh
GODOT_BIN=/path/to/godot python3 -m unittest discover -s ai_factory/tests -v
# Developer browser E2E only: requires Playwright + Chromium and matching templates.
FACTORY_EXPORT_TEMPLATES=/matching/templates python3 -m ai_factory.tests.browser_e2e
```

See [ISSUE_2_DELIVERY.md](ISSUE_2_DELIVERY.md) for the capability matrix, evidence, known protected-project baseline failures, and review limits. `RUNTIME_CHECKED` means tested in the actual engine for the exact design/source hashes. `NATIVE_CHECKED` additionally requires a relocated executable/PCK and packaged scenarios to pass. Neither certifies final artwork, controller hardware, laptop performance or commercial game completeness.

### Unified Character Studio intake

The main interface includes reference submission, task status, candidate download,
Godot import verification, and **Use downloaded candidate**. Select an existing
project, enter provenance/license/reference hash, optionally name a character
with an existing matching appearance lock, and explicitly approve intake before
staging. Review license, visual appearance, and prototype use separately from
the project asset list; each decision creates a revision. Downloaded candidates
remain unapproved until those human decisions. Production character binding and
retargeting remain unfinished. Browser coverage uses synthetic geometry and no
paid Meshy calls:

    python3 -B -m ai_factory.tests.studio_browser_e2e

Linux export now includes a temporary export-only main-scene dispatcher because
Godot release templates do not support the editor's --script option. Packaged
scenario and campaign restart checks execute through explicit user arguments.
The generated source project and approved game files are not rewritten.
