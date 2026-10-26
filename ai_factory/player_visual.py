"""Validated opt-in player visual binding for generated Godot 3D projects.

Applied during normal core.build, not by patching an existing deployed game.
A visual binding is deliberately separate from animation retargeting.
"""
import json
from pathlib import Path
import shutil

from . import assets
from .asset_review import _asset_file

def install_approved_visual(project, game, bible):
    binding = bible.get("player_visual_binding")
    if binding is None:
        return False
    if bible.get("template") != "rpg_3d" or not isinstance(binding, dict):
        raise ValueError("Player visual binding requires a 3D RPG")
    name, sha = binding.get("character"), binding.get("sha256")
    if not isinstance(name, str) or not isinstance(sha, str):
        raise ValueError("Invalid player visual binding")
    height, yaw = binding.get("target_height", 1.8), binding.get("yaw_offset_degrees", 0)
    if type(height) not in (int, float) or not 0.5 <= height <= 4 or yaw not in (0, 90, 180, 270):
        raise ValueError("Invalid player visual fit")
    locked = bible.get("approved_appearance_references", {}).get(name)
    rows = [a for a in bible.get("assets", []) if a.get("character") == name and a.get("sha256") == sha]
    if not locked or len(rows) != 1:
        raise ValueError("Bound character or approved reference missing")
    row = rows[0]
    assets.metadata_record(row, locked_reference=locked, require_approval=True)
    if row.get("license_review") != "APPROVED" or row.get("visual_review") != "APPROVED":
        raise ValueError("Binding requires explicit license and visual approvals")
    if row.get("engine_import") != "RUNTIME_CHECKED":
        raise ValueError("Binding requires recorded real Godot import verification")
    source = _asset_file(Path(project), row)
    facts = assets.inspect_glb(source)
    if not facts["meshes"]:
        raise ValueError("Character GLB contains no mesh")
    if any(clip not in facts["animations"] for clip in row.get("animation_mapping", {}).values()):
        raise ValueError("Missing referenced animation clip")
    dest = Path(game) / "player_visual.glb"
    shutil.copyfile(source, dest)
    (Path(game) / "player_visual.json").write_text(json.dumps({
        "character": name, "sha256": sha, "reference_sha256": locked,
        "animation_mapping": row.get("animation_mapping", {}),
        "target_height": binding.get("target_height", 1.8),
        "yaw_offset_degrees": binding.get("yaw_offset_degrees", 0),
        "animation_binding": "PENDING_REVIEW"
    }, indent=2) + "\n")
    return True
