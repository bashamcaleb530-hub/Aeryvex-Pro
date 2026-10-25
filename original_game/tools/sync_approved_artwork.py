#!/usr/bin/env python3
"""Keep original, visually locked ruler references with the GitHub checkout.

Usage:
  python original_game/tools/sync_approved_artwork.py restore
  python original_game/tools/sync_approved_artwork.py publish

Restore copies approved images from tracked repo originals into character_factory,
validating the canonical SHA256. Publish stages the verified originals in the
repository and attempts git push through Kaggle's existing Git credentials.
No artwork is generated or altered.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[2]
SOURCE = PROJECT / "original_game" / "assets" / "approved_refs"
DEST = PROJECT / "character_factory" / "approved_refs"
LOCK = PROJECT / "original_game" / "character_visual_lock.json"
BRANCH = "aeryvex-original-game"

def verify(directory):
    manifest = directory / "reference_manifest.json"
    if not manifest.is_file():
        raise RuntimeError("Approved manifest is missing: " + str(manifest))
    obj = json.loads(manifest.read_text())
    rulers = obj["rulers"]
    locked = json.loads(LOCK.read_text())["rulers"]
    assert len(rulers) == len(locked) == 10, "Expected exactly ten approved ruler references"
    by_id = {r["id"]: r for r in rulers}
    for ruler in locked:
        item = by_id.get(ruler["id"])
        if not item or any(item[k] != ruler[k] for k in ("name", "galaxy", "species", "faction")):
            raise RuntimeError("Approved reference does not match visual lock: " + ruler["name"])
        if not (directory / item["reference"]).is_file():
            raise RuntimeError("Missing original reference crop: " + item["reference"])
    lineup = directory / obj["canonical_image"]
    if not lineup.is_file():
        raise RuntimeError("Approved lineup is missing")
    digest = hashlib.sha256(lineup.read_bytes()).hexdigest()
    if digest != obj["sha256"]:
        raise RuntimeError("Approved lineup changed or wrong file (checksum mismatch)")
    return obj, digest

def copy_assets(src, dst, obj):
    dst.mkdir(parents=True, exist_ok=True)
    for name in ["reference_manifest.json", obj["canonical_image"]] + [r["reference"] for r in obj["rulers"]]:
        origin, target = src / name, dst / name
        if origin.resolve() != target.resolve():
            shutil.copy2(origin, target)

def restore():
    if not SOURCE.is_dir():
        raise RuntimeError(
            "GitHub does not yet contain the artwork. Its original images must be published ONCE; "
            "metadata alone cannot recreate approved pictures. See publish mode."
        )
    manifest, sha = verify(SOURCE)
    copy_assets(SOURCE, DEST, manifest)
    print("SUCCESS: restored all 10 approved reference crops and exact approved lineup from GitHub.")
    print("SHA256:", sha)
    print("Kaggle files:", DEST)

def publish():
    manifest, sha = verify(DEST)
    copy_assets(DEST, SOURCE, manifest)
    files = ["original_game/assets/approved_refs/"]
    subprocess.run(["git", "add", "--"] + files, cwd=PROJECT, check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=PROJECT)
    if diff.returncode != 0:
        subprocess.run(["git", "commit", "-m", "Store verified approved 10-ruler original artwork for Kaggle restore"], cwd=PROJECT, check=True)
    print("Validated exact image SHA256:", sha)
    push = subprocess.run(["git", "push", "origin", BRANCH], cwd=PROJECT)
    if push.returncode != 0:
        raise RuntimeError("Original artwork is staged locally, but GitHub push did not succeed. Kaggle needs repository write authentication. The artwork has NOT been backed up remotely.")
    print("SUCCESS: exact approved images backed up to private GitHub; Kaggle can restore them after a reset.")

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("publish", "restore"):
        sys.exit("Usage: python original_game/tools/sync_approved_artwork.py [publish|restore]")
    try:
        (publish if sys.argv[1] == "publish" else restore)()
    except Exception as e:
        sys.exit("ERROR: " + str(e))
