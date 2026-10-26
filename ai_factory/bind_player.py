"""Explicitly bind a staged, visually approved GLB to a generated RPG player.

This action runs a real isolated Godot import and commits a new Bible revision.
Run a normal factory build/test afterward. No existing game is patched in place.
"""
import argparse
import json
from pathlib import Path
from . import assets, core
from .asset_review import _managed_guard, _asset_file, _save
from .godot_candidate_check import check_candidate


def bind(project, character, sha256, godot_bin=None):
    project = Path(project).resolve()
    _managed_guard(project)
    bible = core.load(project)
    if bible["template"] != "rpg_3d":
        raise ValueError("Only 3D RPG players currently support a visual binding")
    matches = [row for row in bible.get("assets", []) if
               row.get("character") == character and row.get("sha256") == sha256]
    if len(matches) != 1:
        raise ValueError("Select one staged asset with the exact character and SHA-256")
    row = matches[0]
    locked = bible.get("approved_appearance_references", {}).get(character)
    if locked is None:
        raise ValueError("Missing approved appearance reference")
    assets.metadata_record(row, locked_reference=locked, require_approval=True)
    if row.get("license_review") != "APPROVED" or row.get("visual_review") != "APPROVED":
        raise ValueError("License and visual approval must be explicit before binding")
    source = _asset_file(project, row)
    facts = assets.inspect_glb(source)
    if facts["meshes"] == 0:
        raise ValueError("GLB contains no character mesh")
    report = check_candidate(source, godot_bin=godot_bin)
    if report["engine_import"] != "PASSED":
        raise ValueError("Real Godot import required: " + report["status"])
    row["engine_import"] = "RUNTIME_CHECKED"
    bible["player_visual_binding"] = {"character": character, "sha256": sha256}
    _save(project, bible, "Bind reviewed player visual (requires rebuild and QA)", sha256)
    return {"revision": bible["revision"], "character": character, "sha256": sha256,
            "status": "SELECTED_REBUILD_REQUIRED", "engine_import": "RUNTIME_CHECKED",
            "animation_binding": "PENDING_REVIEW"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-path", required=True)
    parser.add_argument("--character", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--godot-bin")
    args = parser.parse_args(argv)
    print(json.dumps(bind(args.project_path, args.character, args.sha256, args.godot_bin), indent=2))


if __name__ == "__main__":
    main()
