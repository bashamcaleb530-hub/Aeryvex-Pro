#!/usr/bin/env python3
"""Batch-create experimental TripoSR meshes from the ten locked ruler reference crops.
These are 3D candidates, NOT approved faithful models, rigs, or animations.
Run from Kaggle after install_approved_rulers.py has validated the package.
"""
from pathlib import Path
import argparse
import json
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[2]
ROOT = PROJECT / "character_factory"
REFS = ROOT / "approved_refs"
LOCK = PROJECT / "original_game" / "character_visual_lock.json"
TRIPOSR = Path("/kaggle/working/appearance_models/TripoSR/run.py")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", default="", help="Optional ruler name to process")
    p.add_argument("--python", default=sys.executable, help="Interpreter with TripoSR installed")
    p.add_argument("--tripo", type=Path, default=TRIPOSR)
    p.add_argument("--resume", action="store_true")
    args = p.parse_args()
    manifest_path = REFS / "reference_manifest.json"
    validation = ROOT / "approved_reference_validation.json"
    if not manifest_path.exists() or not validation.exists() or not LOCK.exists():
        sys.exit("Approved references not installed. Run install_approved_rulers.py first.")
    manifest = json.loads(manifest_path.read_text())
    lock = json.loads(LOCK.read_text())
    by_id = {r["id"]: r for r in manifest["rulers"]}
    if not args.tripo.is_file():
        sys.exit(f"TripoSR script not found: {args.tripo}. Install TripoSR in Kaggle, then rerun.")
    candidates = ROOT / "mesh_candidates"
    candidates.mkdir(parents=True, exist_ok=True)
    results = []
    for ruler in lock["rulers"]:
        ref = by_id[ruler["id"]]
        if args.name and args.name.lower() not in (ruler["name"].lower(), ruler["name"].lower().replace(" ", "_")):
            continue
        source = REFS / ref["reference"]
        if not source.is_file():
            sys.exit(f"Missing approved crop: {source}")
        output = candidates / ruler["name"].lower().replace(" ", "_")
        output.mkdir(exist_ok=True)
        status_file = output / "run_status.json"
        if args.resume and status_file.exists() and json.loads(status_file.read_text()).get("returncode") == 0:
            print("SKIP:", ruler["name"])
            continue
        cmd = [args.python, str(args.tripo), str(source), "--output-dir", str(output)]
        print("GENERATING CANDIDATE:", ruler["name"], flush=True)
        run = subprocess.run(cmd, text=True, capture_output=True, check=False)
        status = {"name": ruler["name"], "source": str(source),
                  "returncode": run.returncode,
                  "mesh_files": [str(q) for q in output.rglob("*") if q.suffix.lower() in (".obj", ".glb", ".ply")],
                  "stderr_tail": run.stderr[-2400:],
                  "status": "candidate_unverified" if run.returncode == 0 else "failed"}
        status_file.write_text(json.dumps(status, indent=2))
        print(json.dumps(status, indent=2), flush=True)
        results.append(status)
    if not results:
        sys.exit("No rulers matched or all were skipped.")
    print("Batch completed. Candidate meshes require geometry inspection, rigging and actual Godot validation.")
    if any(item["returncode"] != 0 for item in results):
        sys.exit(1)

if __name__ == "__main__":
    main()
