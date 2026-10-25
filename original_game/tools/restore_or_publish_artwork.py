#!/usr/bin/env python3
"""Kaggle entrypoint for approved visual references.
Use the *exact original* Aeryvex_Approved_Ten_Rulers_Kaggle.zip once.
After image files are in GitHub, subsequent resets restore without any ZIP.
"""
from pathlib import Path
import subprocess
import sys
import zipfile

PROJECT = Path(__file__).resolve().parents[2]
ROOT = PROJECT / "character_factory"
TRACKED = PROJECT / "original_game" / "assets" / "approved_refs"
ZIP_NAME = "Aeryvex_Approved_Ten_Rulers_Kaggle.zip"

def run(relative, *args):
    return subprocess.run([sys.executable, str(PROJECT / relative), *args],cwd=PROJECT).returncode

def main():
    if (TRACKED / "reference_manifest.json").exists():
        print("Approved original images are tracked in GitHub. Restoring...", flush=True)
        return run("original_game/tools/install_approved_rulers.py")

    print("First-time publication required: checking Kaggle inputs.",flush=True)
    possible = [PROJECT / ZIP_NAME, Path("/kaggle/working") / ZIP_NAME]
    if Path("/kaggle/input").is_dir():
        possible.extend(Path("/kaggle/input").rglob(ZIP_NAME))
    archive = next((x for x in possible if x.is_file()),None)
    if archive is None:
        print("MISSING ORIGINAL IMAGE BYTES: GitHub contains only metadata, not the approved pictures.")
        print("Upload the exact approved ZIP as Kaggle Input once; do not re-generate any ruler.")
        return 2
    print("Found original ZIP:",archive)
    code = run("original_game/tools/install_approved_rulers.py")
    if code != 0: return code
    print("Artwork verified. Attempting one-time backup into private GitHub...",flush=True)
    code = run("original_game/tools/sync_approved_artwork.py","publish")
    if code != 0:
        print("Back up has NOT reached GitHub. Kaggle git push needs write access.")
        print("Artwork remains in Kaggle for this session; do not assume persistence.")
        return code
    print("GITHUB ASSET BACKUP VERIFIED BY SUCCESSFUL PUSH. Next restart needs git clone only.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
