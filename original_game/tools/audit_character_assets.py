#!/usr/bin/env python3
"""Audit approved-ruler assets and import existing GLBs into the Godot arena.

No new images, models or faces are generated. This only imports GLBs that
already exist, and reports missing requirements instead of claiming completion.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[2]
FACTORY = PROJECT / "character_factory"
GAME = PROJECT / "original_game"
LOCK = GAME / "character_visual_lock.json"
REFS = FACTORY / "approved_refs"
TARGET = GAME / "assets" / "approved_characters"
REPORT = FACTORY / "godot_character_asset_report.json"

def run():
    p = argparse.ArgumentParser()
    p.add_argument("--godot", default="/kaggle/working/aeryvex_tools/Godot_v4.7.2-stable_linux.x86_64")
    p.add_argument("--import-verified", action="store_true", help="Copy existing *manually approved* GLBs from character_factory/verified_glb")
    a = p.parse_args()
    rulers = json.loads(LOCK.read_text())["rulers"]
    assert len(rulers) == 10
    TARGET.mkdir(parents=True, exist_ok=True)
    approved_models = FACTORY / "verified_glb"
    manifest_file = REFS / "reference_manifest.json"
    manifest = json.loads(manifest_file.read_text()) if manifest_file.is_file() else None
    artwork_valid = False
    if manifest:
        artwork = REFS / manifest["canonical_image"]
        artwork_valid = artwork.is_file() and hashlib.sha256(artwork.read_bytes()).hexdigest() == manifest["sha256"]
    entries = []
    for r in rulers:
        stem = r["name"].lower().replace(" ", "_")
        destination = TARGET / (stem + ".glb")
        approved_source = approved_models / (stem + ".glb")
        approved_marker = approved_models / (stem + ".approved.json")
        has_approval = False
        if approved_marker.is_file() and approved_source.is_file():
            note = json.loads(approved_marker.read_text())
            expected = note.get("sha256")
            has_approval = (
                note.get("character_id") == r["id"]
                and note.get("approved") is True
                and isinstance(expected, str)
                and hashlib.sha256(approved_source.read_bytes()).hexdigest() == expected
            )
        if a.import_verified and artwork_valid and has_approval:
            shutil.copy2(approved_source, destination)
            print("IMPORTED APPROVED GLB:", r["name"])
        entries.append({
            "id": r["id"], "name": r["name"], "species": r["species"],
            "reference_available": bool(manifest and (REFS / next(
                (x["reference"] for x in manifest["rulers"] if x["id"] == r["id"]), ""
            )).is_file()),
            "approval_marker_valid": has_approval,
            "godot_glb_present": destination.is_file(),
            "godot_path": "res://assets/approved_characters/" + stem + ".glb"
        })
    godot = Path(a.godot)
    result = {"artwork_checksum_valid": artwork_valid, "characters": entries,
              "godot_available": godot.is_file(), "godot_import_exit_code": None,
              "godot_errors": [], "note": "A GLB being present is not proof of correct visual likeness, valid skeleton or animation."}
    if godot.is_file():
        proc = subprocess.run([str(godot), "--headless", "--path", str(GAME), "--editor", "--quit"],
                              capture_output=True, text=True, timeout=180)
        result["godot_import_exit_code"] = proc.returncode
        output = proc.stdout + "\n" + proc.stderr
        result["godot_errors"] = [line.strip() for line in output.splitlines()
                                  if "ERROR:" in line or "SCRIPT ERROR" in line]
    FACTORY.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print("Approved reference hash valid:", artwork_valid)
    print("Godot model GLBs present:", sum(x["godot_glb_present"] for x in entries), "/ 10")
    print("Approved GLB markers:", sum(x["approval_marker_valid"] for x in entries), "/ 10")
    print("Godot editor import exit code:", result["godot_import_exit_code"])
    print("Godot reported errors:", len(result["godot_errors"]))
    print("Report:", REPORT)
    return 0 if result["godot_import_exit_code"] in (None, 0) and not result["godot_errors"] else 1

if __name__ == "__main__":
    sys.exit(run())
