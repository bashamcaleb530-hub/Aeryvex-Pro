# Approved hero visual references — Aether World

These five images are user-approved and must be preserved without edits:
- `approved_heroes/kai.png` — Kai, agile small-framed male martial artist with teal-blue lightning and black layered armor
- `approved_heroes/ryker.png` — Ryker, heavy armored weapons/warfare specialist with gold-blue conduit energy
- `approved_heroes/lyra.png` — Lyra, agile female martial artist with long dark hair, dark-violet armor and purple lightning
- `approved_heroes/approved_character_selection.png` — approved three-character selection art
- `approved_heroes/approved_main_menu.png` — approved AETHER WORLD: THRONES OF THE TEN GALAXIES main menu

Install the downloadable artwork ZIP into `original_game/approved_heroes/`, preserving names and bytes. Godot imports PNGs as textures after an editor import.

**Visual fidelity:** The existing in-world teenage candidate uses a BOX placeholder and does not visually match any approved portrait. Do not claim final appearance has been implemented until three distinct, user-reviewed, rigged 3D GLB character assets are created and integrated. Existing menu rendering loads exact approved portraits if installed; never generate lookalikes to replace them.

Headless asset audit: `godot --headless --path original_game --editor --quit` then `godot --headless --path original_game --script res://tests/audit_approved_hero_visuals.gd`.

Keep the Aether rank progression separate from the menu artwork palette: the teenage applicant is not prematurely promoted by choosing Lyra's purple visual theme.
