# Issue 2 implementation plan and execution record

Goal: extend the existing factory into a local, runnable application producing tested small games. Issue #2 is the binding specification. Existing original_game, references, website_builder, canon and factory_projects are preserved byte-for-byte.

Architecture: Python standard-library localhost UI calls a persistent job runner. Jobs invoke existing validated design/build/QA APIs and real Godot; native packaging is a separate evidence-bound stage. The 3D template gains a complete small campaign. Immutable Bible checkpoints support audit and rollback. Approved assets keep provenance and explicit prototype states.

Decisions: reuse Python/Godot and browser UI to avoid heavy desktop runtime on an 8 GB laptop; no hosted services or GPU requirement. Native exports use matching user-provided official templates, never fabricate completion. The bounded generator retains unsupported requirements. Scope/budget labels are estimates, not 24h guarantees.

## Work and validation
- [x] Campaign: three objectives, dialogue, checkpoints/retry, progression/upgrades, save/load, ending; bounded mission revisions; actual engine behavior scenarios and Python regression tests.
- [x] Native export: engine/template checks, export, relocated executable smoke test, checksum manifest and archive; missing dependencies explicitly blocked; unit and real Godot validation.
- [x] Asset workflow: provenance/approval/import validation, reviewable staging, no reference replacement; approved character integration only on explicit request; actual GLB tests.
- [x] Application: black/blue accessible localhost UI; project/revision/requirements/build logs, jobs, cancellation/resume/budget, safe artifact access. CLI remains available. Browser end-to-end test.
- [x] Reliability: rollback as a new revision, safe managed edits, genre manifests, actionable repair bounded to safe stale imports. Tests for failure, stale QA, restart persistence, cancellation and conflicts.
- [x] Delivery: regenerate independent demos outside existing projects, verify both 2D/3D initial/revision, Linux/ZIP artifacts, preservation hashes, clean source package, capability matrix and PR.

Review focus: interrupted jobs cannot claim passed; a changed source invalidates QA/export; traversal/CSRF cannot execute arbitrary actions; revisions preserve unrelated prompts and locked references; absent assets/export templates remain explicit blocked capabilities.

Baseline: 15 unittest tests passed on 2026-10-26. Started from e7a74cb30d8188decb8ace19becb6370d163b938 on codex/issue-2-game-factory. Plan location restricted to ai_factory per issue. User explicitly requested implementation; no extra design approval gate.

## Review and fixes
Independent review identified queued orphan jobs, cancellation lost updates, source ZIP checksum validation, rollback replay, interrupted checkpoint promotion, and build/Bible mismatch. Each received a failing regression then a passing fix. A monotonic cancel marker is authoritative even after a late worker write. Completed checkpoint journal entries promote only when their parent Bible hash matches. QA binds both the built Bible digest and source snapshot.

Known boundary: protected original_game already contains menu parse and dummy-renderer errors in the starting commit; copied regression tests record these without changing protected source. Factory passing tests are reported separately.

Final validation: 77/77 factory tests; five Chromium-driven real Godot/native builds passed. Full stdout/native manifests and snapshots are retained under verification/issue2/runs. Asset intake is usable; automatic production-character binding, arbitrary genre code generation and finished artwork remain explicitly unfinished in ISSUE_2_DELIVERY.md.
