"""Export a reviewed character as a portable, non-destructive Godot preview pack.

The pack is NOT inserted into generated gameplay or a substitute for rig validation.
"""
import json
from pathlib import Path
import shutil

from . import assets, core
from .asset_review import _asset_file
from .tools.preview_character import create_preview


def export_character(project, character, output):
    project = Path(project).resolve()
    bible = core.load(project)
    if not isinstance(character, str) or not character.strip():
        raise ValueError("Character is required")
    locked = bible.get("approved_appearance_references", {}).get(character)
    if not locked:
        raise ValueError("Character has no locked approved appearance reference")
    matches = [row for row in bible.get("assets", []) if row.get("character") == character]
    if len(matches) != 1:
        raise ValueError("Select exactly one staged character asset; duplicates are ambiguous")
    row = matches[0]
    source = _asset_file(project, row)
    assets.metadata_record(row, locked_reference=locked, require_approval=True)
    if row.get("license_review") != "APPROVED" or row.get("visual_review") != "APPROVED":
        raise ValueError("License and visual review must both be approved")
    facts = assets.inspect_glb(source)
    mapping = row.get("animation_mapping", {})
    if mapping and (not facts["skins"] or any(clip not in facts["animations"] for clip in mapping.values())):
        raise ValueError("Animation mapping requires a GLB skin and actual clips")
    output = Path(output).expanduser().absolute()
    created = create_preview(source, output)
    try:
        manifest = {
            "format": "aeryvex-reviewed-character-v1",
            "character": character,
            "source_sha256": facts["sha256"],
            "reference_sha256": locked,
            "license": row["license"],
            "author": row["author"],
            "source": row["source"],
            "animations": facts["animations"],
            "skins": facts["skins"],
            "animation_mapping": mapping,
            "license_review": "APPROVED",
            "visual_review": "APPROVED",
            "engine_import": "NOT_VERIFIED_FOR_THIS_EXPORT",
            "gameplay_binding": "NOT_IMPLEMENTED",
        }
        (created / "character_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        return manifest
    except Exception:
        shutil.rmtree(created)
        raise
