"""Inspect a candidate GLB in an isolated Godot project, never in a real game.

Usage: python3 -m ai_factory.godot_candidate_check --glb candidate.glb
An actual Godot 4 binary is required. No visual/rights approval is implied.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from .assets import inspect_glb
from .tools.preview_character import create_preview


def check_candidate(glb, godot_bin=None, timeout=120):
    glb = Path(glb).expanduser().resolve(strict=True)
    facts = inspect_glb(glb)
    binary = godot_bin or os.environ.get("GODOT_BIN") or shutil.which("godot") or shutil.which("godot4")
    if not binary:
        return {"status": "BLOCKED_GODOT_UNAVAILABLE", "glb": str(glb),
                "facts": facts, "engine_import": "NOT_RUN", "visual_approved": False}
    with tempfile.TemporaryDirectory(prefix="aeryvex-candidate-") as temp:
        project = Path(temp) / "preview"
        create_preview(glb, project)
        # --editor imports referenced resources. Use separate user data/cache paths
        # to keep preview artifacts out of existing games.
        env = dict(os.environ)
        env["XDG_DATA_HOME"] = str(Path(temp) / "data")
        env["XDG_CACHE_HOME"] = str(Path(temp) / "cache")
        env["XDG_CONFIG_HOME"] = str(Path(temp) / "config")
        try:
            proc = subprocess.run([str(binary), "--headless", "--path", str(project),
                                   "--editor", "--quit"], capture_output=True,
                                  text=True, encoding="utf-8", errors="replace",
                                  timeout=timeout, env=env, check=False)
        except FileNotFoundError:
            return {"status": "BLOCKED_GODOT_UNAVAILABLE", "glb": str(glb),
                    "facts": facts, "engine_import": "NOT_RUN", "visual_approved": False}
        except subprocess.TimeoutExpired:
            return {"status": "FAILED_TIMEOUT", "glb": str(glb),
                    "facts": facts, "engine_import": "FAILED", "visual_approved": False}
        output = (proc.stdout + "\n" + proc.stderr)[-16000:]
        # Godot can exit 0 while logging an importer or GDScript error.
        has_errors = any(marker in output.lower() for marker in (
            "error:", "parse error", "failed to load", "failed to import", "script error"))
        imported = (project / ".godot" / "imported").is_dir() and any(
            (project / ".godot" / "imported").iterdir())
        ok = proc.returncode == 0 and not has_errors and imported
        return {"status": "ENGINE_IMPORTED_PENDING_REVIEW" if ok else "FAILED_IMPORT",
                "glb": str(glb), "facts": facts,
                "engine_import": "PASSED" if ok else "FAILED",
                "exit_code": proc.returncode, "log_tail": output,
                "visual_approved": False, "rig_approved": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glb", required=True)
    parser.add_argument("--godot-bin")
    args = parser.parse_args(argv)
    result = check_candidate(args.glb, args.godot_bin)
    print(json.dumps(result, indent=2))
    return 0 if result["engine_import"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
