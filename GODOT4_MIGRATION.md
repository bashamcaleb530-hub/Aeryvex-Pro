# Aeryvex Pro — Godot 4 migration

Migration target: **Godot 4.7.2 stable**.

This branch preserves the Godot 3 project as its starting point. The Godot 4 converter has not yet been run or validated on this branch.

## Kaggle migration
Use a separate worktree. Copy the locally generated `art/textures/` assets and locally modified `scripts/FighterVisual.gd` and `scripts/ArenaArchitecture.gd` from the Kaggle Godot 3 working tree first. Never run the 3-to-4 converter on the sole copy of the working Godot 3 project.

Godot editor's CLI command is `--convert-3to4`; see https://docs.godotengine.org/en/latest/tutorials/editor/command_line_tutorial.html

Expect the migration to require manual fixes to Godot 3 GDScript and scene APIs; conversion is not proof of playability. Run Godot 4 editor import/parse and gameplay checks separately.
