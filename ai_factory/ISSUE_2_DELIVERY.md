# Issue #2 delivery — tested scoped game-building release

Verified 2026-10-26 on Debian GNU/Linux 13.6, Python 3.12.14, official Godot 4.2.2, matching official Linux export templates, and Chromium 154. This extends the existing factory. It does not establish a 24-hour arbitrary commercial/AAA game SLA.

Launch: `python3 -m ai_factory ui`, then http://127.0.0.1:8765. Install a separate local launcher with `sh ai_factory/tools/setup_debian.sh`. See [README.md](README.md) for dependency paths, controls, source editing and recovery.

## Capability matrix

| Capability | Actual release state | Evidence or boundary |
|---|---|---|
| Black/electric-blue local application | IMPLEMENTED / BROWSER TESTED | Generate, revise, projects, requirements, logs, budgets, rollback, downloads; desktop/mobile screenshots |
| Free CPU-only basic pipeline | IMPLEMENTED / ENGINE TESTED | Python stdlib + existing local Godot; no paid credits, cloud host or GPU required |
| Prompt → design → build → QA → Linux/source ZIP | IMPLEMENTED / END-TO-END TESTED | Five complete browser-driven builds, exact source/design evidence, relocated native executables |
| 3D representative RPG | IMPLEMENTED / ENGINE TESTED / VISUAL REVIEW REQUIRED | Three default missions; dialogue, combat, physical shards, return objectives, checkpoints, XP, blade upgrades, potions, ending |
| Character movement / combat / enemies | IMPLEMENTED / ENGINE TESTED | Walking/running/jumping/collision, orbit camera, obstacle navigation/chase, enemy and player attacks/health/cooldowns, three abilities |
| Save/load and revisions | IMPLEMENTED / ENGINE TESTED | Fresh-process persistence, compatible revision migration, incompatible/corrupt-save archival, checkpoint retry |
| Playtime measurement | IMPLEMENTED / ENGINE TESTED | In-game active elapsed timer persisted with saves; human completion time NOT MEASURED |
| 2D collection/survival | IMPLEMENTED / ENGINE TESTED | Separate playable flow with coins, pursuers, damage, win/lose/restart; revised speed/color/coin count |
| Persistent design / plans / audit / rollback | IMPLEMENTED / TESTED | Every prompt retained; dependency task graph; immutable checkpoints; restore as a new revision; crash recovery |
| Resumable jobs / cancellation / time budgets | IMPLEMENTED / TESTED | Durable stage records; safe committed-design reconciliation; monotonic cancel marker; stale/conflicting changes rejected; max24h limit |
| Self-repair | LIMITED IMPLEMENTATION | One recorded retry of generated import cache; no arbitrary autonomous program repair or source overwrite |
| Optional Ollama/Qwen provider | IMPLEMENTED / HTTP-STUB TESTED / LIVE MODEL UNVERIFIED | Actual local HTTP contract tests, strict bounded full-config JSON, no executable response code; no model bundled |
| GLB asset intake and provenance | IMPLEMENTED / TESTED | Immutable hashes, license/author/source/reference gates, container/URI/range validation, separate review flags |
| Rig/animation adapter | EXISTING ADAPTER / ENGINE TESTED WITH SYNTHETIC FIXTURE | Skeleton/clip checks and actual animation advancement; not a finished realistic character |
| Approved model binding / retargeting | UNFINISHED | Intake does not automatically replace the capsule or approved references; manual integration still needed |
| Genre manifests | IMPLEMENTED / TWO BUILTIN BACKENDS TESTED | Data-only registry; adding other genres needs a new compiler and behavior tests |
| Gamepad controls | IMPLEMENTED / SIMULATED INPUT TESTED | Physical controller verification pending |
| Presentation/accessibility | IMPLEMENTED / VISUAL REVIEW REQUIRED | Lit modular ground/structures/town, health bars, dialogue/toasts, large text, reduced motion; all primitive art explicitly prototype |
| Realistic production assets/materials/animation | UNFINISHED | No approved realistic characters supplied, invented or substituted |
| Cinematics, authored sound, production VFX, heightfield terrain | UNFINISHED | No completion claim from configuration labels or proxy geometry |
| GPU/Kaggle art production | OPTIONAL EXISTING TOOLING / NOT EXERCISED IN THIS RELEASE | No paid infrastructure provisioned; durable storage remains the user's responsibility |
| Arbitrary genres / unrestricted AI code generation | UNFINISHED | Unsupported requests retained and reported; supported revisions change bounded validated data |
| 2015 MacBook Pro graphics/performance | HARDWARE REVIEW REQUIRED | GL Compatibility chosen; headless Debian tests are not a physical Intel GPU/FPS certification |

## Verification performed

`GODOT_BIN=/path/to/Godot4.2.2 python3 -m unittest discover -s ai_factory/tests -v`: **77 tests passed**, including real Godot campaign runs, actual GLB rig/animation import, real HTTP provider tests, recovery, corruption, stale evidence and path/CSRF checks. See [unit-tests.log](verification/issue2/unit-tests.log).

`python3 -m ai_factory.tests.browser_e2e` with matching templates: **BROWSER_E2E_PASS**, no browser JavaScript errors, mobile390px without horizontal overflow. Real browser actions generated and downloaded builds; reloading preserved the project; restoring revision1 created revision3 without deleting history. See [browser-e2e.json](verification/issue2/browser-e2e.json) and [run evidence](verification/issue2/runs/).

| Build | Source QA | Native checks | Observed pipeline elapsed |
|---|---|---|---|
| 3D initial3 missions/town/2 enemies | Six stages pass | Seven checks pass | 23.65s |
| 3D revision: new enemy/area/lightning/longer missions | Six stages pass | Seven checks pass | 23.67s |
| 3D rollback as revision3 | Six stages pass | Seven checks pass | 24.98s |
| 2D initial8 coins/2 enemies | Four stages pass | Five checks pass | 21.68s |
| 2D revision12 coins/red/faster | Four stages pass | Five checks pass | 23.91s |

These are measured headless build/QA/export times on this executor, not human playtime or a laptop benchmark. Native checks run from an unrelated temporary directory containing only executable/PCK. Campaign native checks complete all missions and then start a separate executable process to verify the saved ending/progression. Exact logs and SHA-256 evidence are retained per run. ZIP CRCs, manifest hashes, executable permissions and current source/design identity are checked.

Local installation was tested in a path containing spaces, its installed launcher served the real UI, and repeat setup refused overwrite. See [installation.json](verification/issue2/installation.json). Project sources are not installed into or generated over existing original-game folders.

Independent review found and prompted fixes for source download checksum validation, queued orphans, cancel/completion races, exactly-once rollback recovery, interrupted checkpoint promotion and same-revision Bible edits. Every finding has a failing-then-passing regression. A release-only Godot Label3D teardown error was reproduced and fixed by detaching its render base before destruction; engine error gates were retained.

## Protected-project baseline findings

Only factory files are changed by this release. Existing projects, canon, approved references and unrelated website work remain preserved. Newer concurrent development-branch changes are included as the PR base, not overwritten.

A copied `original_game/` regression revealed existing errors in the starting source: `AetherWorldMenu.gd` cannot infer `portrait_path` at line133 and its menu test times out; character-arena and military-opening tests emit dummy-renderer mesh errors despite exit0. Powers and ascension tests are clean. These were recorded separately in [original-regression.json](verification/issue2/original-regression.json) with logs; they are not counted as passing factory tests or silently suppressed. The protected original source was not modified. The repository-root Godot3 legacy project is not the generated Godot4 factory target.

## Remaining review

Inspect generated games visually, try the physical controller/Intel GPU, review any supplied asset licenses and character fidelity, and test a live local model before relying on those capabilities. The release provides a working small-game pipeline and a reviewable foundation for broader production; it does not claim finished photorealistic art or fully autonomous development of arbitrary games.
