#!/usr/bin/env python3
"""Install and validate user-approved ruler references in a Kaggle checkout.
Does NOT redraw, hallucinate, retouch or turn these references into fake 3D.
Run: python original_game/tools/install_approved_rulers.py
"""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import zipfile

PROJECT = Path(__file__).resolve().parents[2]
ROOT = PROJECT / "character_factory"
DEST = ROOT / "approved_refs"
ZIP_NAME = "Aeryvex_Approved_Ten_Rulers_Kaggle.zip"
LOCK = PROJECT / "original_game" / "character_visual_lock.json"
REQUIRED = {"orion_valen","maeryn_sol","thalen_orris","ilyra_venn","selene_avaris",
            "drakthar_vex","malveris_thorne","nyssara_veil","korr_uldane","vaelith_sorn"}


def find_zip():
    locations = [Path("/kaggle/working") / ZIP_NAME, PROJECT / ZIP_NAME]
    input_dir = Path("/kaggle/input")
    if input_dir.exists():
        locations += list(input_dir.rglob(ZIP_NAME))
    return next((p for p in locations if p.is_file()), None)


def main():
    assert LOCK.exists(), "GitHub character_visual_lock.json missing; pull the original-game branch."
    lock = json.loads(LOCK.read_text())
    assert len(lock["rulers"]) == 10
    package = find_zip()
    if package is None:
        print("MISSING PACKAGE: Upload the exact approved ZIP to Kaggle inputs or /kaggle/working.")
        print("No replacement images have been created.")
        return 2
    DEST.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(package) as z:
        for member in z.infolist():
            if member.is_dir() or not member.filename.startswith("approved_refs/"):
                continue
            filename = Path(member.filename).name
            if filename not in {"reference_manifest.json", "ten_rulers_approved_lineup.png"} and not filename.endswith("_panel_reference.png"):
                continue
            output = DEST / filename
            with z.open(member) as src, output.open("wb") as dst:
                shutil.copyfileobj(src, dst)
    manifest_file = DEST / "reference_manifest.json"
    assert manifest_file.is_file(), "Approved manifest not found in ZIP"
    manifest = json.loads(manifest_file.read_text())
    full = DEST / manifest["canonical_image"]
    assert full.is_file(), "Approved lineup image missing"
    digest = hashlib.sha256(full.read_bytes()).hexdigest()
    assert digest == manifest["sha256"], "Artwork hash mismatch: DO NOT accept altered lineup"
    by_id = {r["id"]: r for r in manifest["rulers"]}
    assert len(by_id) == 10
    assert {r["name"].lower().replace(" ", "_") for r in manifest["rulers"]} == REQUIRED
    for ruler in lock["rulers"]:
        ref = by_id[ruler["id"]]
        for key in ("name", "species", "galaxy", "faction"):
            assert ref[key] == ruler[key], f"Visual lock mismatch {ruler['name']}: {key}"
        image = DEST / ref["reference"]
        assert image.is_file() and image.stat().st_size > 5000, f"Missing ruler crop {image}"
    tracker_file = ROOT / "character_tracker.json"
    if tracker_file.exists():
        tracker = json.loads(tracker_file.read_text())
        for char in tracker:
            ref = by_id.get(char.get("id"))
            if not ref:
                continue
            char.setdefault("status", {})["concept_approved"] = True
            char["approved_reference"] = str(DEST / ref["reference"])
            char["canonical_lineup"] = str(full)
            char["visual_lock"] = True
            char["species"] = ref["species"]
            char["galaxy"] = ref["galaxy"]
            # Mesh, rig, animation and integration stay unverified until tested.
        tracker_file.write_text(json.dumps(tracker, indent=2) + "\n")
    summary = {
        "status": "approved_references_installed_and_verified",
        "ruler_count": len(by_id),
        "canonical_sha256": digest,
        "lineup": str(full),
        "individual_references": {v["name"]: str(DEST / v["reference"]) for v in manifest["rulers"]},
        "3d_models_verified": 0,
        "note": "Cropped lineup art is not a full-body multiview reconstruction input."
    }
    (ROOT / "approved_reference_validation.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("SUCCESS: all ten approved ruler references verified; exact canonical lineup SHA-256:", digest)
    print("3D reconstruction NOT yet completed or approved.")
    print("Validation report:", ROOT / "approved_reference_validation.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
