"""Opt-in Meshy Image-to-3D bridge. Output remains unapproved until asset review.

Usage: python3 -m ai_factory.meshy_bridge submit --image reference.png
       python3 -m ai_factory.meshy_bridge status TASK_ID
       python3 -m ai_factory.meshy_bridge download TASK_ID --output candidate.glb
Set MESHY_API_KEY in your environment. Never commit the key.
"""
import argparse
import base64
import json
import os
from pathlib import Path
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.meshy.ai/openapi/v1/image-to-3d"
MAX_IMAGE = 20 * 1024 * 1024
MAX_MODEL = 128 * 1024 * 1024
MIMES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
TASK_ID = re.compile(r"^[A-Za-z0-9-]{1,100}$")


def _request(url, *, payload=None, opener=None):
    key = os.environ.get("MESHY_API_KEY")
    if not key:
        raise ValueError("Set MESHY_API_KEY before using Meshy")
    raw = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=raw, headers={
        "Authorization": "Bearer " + key,
        "Accept": "application/json",
        **({"Content-Type": "application/json"} if raw is not None else {}),
    }, method="POST" if raw is not None else "GET")
    open_fn = opener or urllib.request.urlopen
    try:
        with open_fn(req, timeout=60) as response:
            result = json.loads(response.read(2 * 1024 * 1024 + 1))
    except urllib.error.HTTPError as error:
        raise ValueError("Meshy API request failed with HTTP " + str(error.code)) from None
    if not isinstance(result, dict):
        raise ValueError("Unexpected Meshy response")
    return result


def submit(image, *, opener=None):
    image = Path(image)
    if image.suffix.lower() not in MIMES or not image.is_file():
        raise ValueError("Input must be a PNG, JPG or WEBP image file")
    size = image.stat().st_size
    if not 0 < size <= MAX_IMAGE:
        raise ValueError("Meshy image must be between 1 byte and 20 MiB")
    data = base64.b64encode(image.read_bytes()).decode("ascii")
    payload = {
        "image_url": "data:" + MIMES[image.suffix.lower()] + ";base64," + data,
        "ai_model": "meshy-7.1",
        "target_formats": ["glb"],
        "pose_mode": "a-pose",
    }
    result = _request(API, payload=payload, opener=opener)
    task_id = result.get("result")
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
        raise ValueError("Meshy did not return a valid task ID")
    return {"task_id": task_id, "status": "SUBMITTED", "visual_approved": False}


def status(task_id, *, opener=None):
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
        raise ValueError("Invalid Meshy task ID")
    result = _request(API + "/" + task_id, opener=opener)
    return {"task_id": task_id, "status": result.get("status", "UNKNOWN"),
            "progress": result.get("progress"), "has_glb": bool(
                isinstance(result.get("model_urls"), dict) and result["model_urls"].get("glb")),
            "visual_approved": False}


def _fetch_glb(url, destination, opener=None):
    """Download one Meshy-hosted GLB to a NEW path; validate before publishing."""
    if not isinstance(url, str):
        raise ValueError("Meshy returned no GLB download URL")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "assets.meshy.ai" or parsed.username or parsed.password:
        raise ValueError("Untrusted GLB download host")
    destination = Path(destination)
    if destination.suffix.lower() != ".glb" or destination.exists() or destination.is_symlink():
        raise ValueError("Use a new .glb output file; never overwrite existing assets")
    destination.parent.mkdir(parents=True, exist_ok=True)
    open_fn = opener or urllib.request.urlopen
    # Disable redirect-following for the asset download. A signed URL must not
    # redirect to a local/private host or leak its signature to another host.
    if opener is None:
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                raise ValueError("GLB download redirected; refusing untrusted host")
        open_fn = urllib.request.build_opener(NoRedirect()).open
    fd, temporary = tempfile.mkstemp(prefix=".meshy-", suffix=".glb", dir=destination.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            with open_fn(urllib.request.Request(url, headers={"Accept": "model/gltf-binary"}), timeout=120) as response:
                remaining = MAX_MODEL + 1
                while remaining:
                    chunk = response.read(min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    stream.write(chunk)
                    remaining -= len(chunk)
                if remaining == 0:
                    raise ValueError("GLB exceeds factory 128 MiB limit")
        from .assets import inspect_glb
        facts = inspect_glb(temporary)
        os.link(temporary, destination)  # atomic no-overwrite publication
        return facts
    finally:
        Path(temporary).unlink(missing_ok=True)


def download(task_id, output, *, opener=None):
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
        raise ValueError("Invalid Meshy task ID")
    result = _request(API + "/" + task_id, opener=opener)
    if result.get("status") != "SUCCEEDED":
        raise ValueError("Meshy task has not succeeded")
    facts = _fetch_glb((result.get("model_urls") or {}).get("glb"), output, opener)
    return {"task_id": task_id, "output": str(output), "facts": facts,
            "status": "DOWNLOADED_PENDING_REVIEW", "visual_approved": False}


# Auto-rigging and animation library. These follow Meshy's published
# openapi/v1 rigging and animations endpoints. They have offline HTTP-stub
# coverage only; no live paid request has been made from this repository.
RIGGING_API = "https://api.meshy.ai/openapi/v1/rigging"
ANIMATION_API = "https://api.meshy.ai/openapi/v1/animations"


def submit_rigging(input_task_id, *, height_meters=1.7, opener=None):
    if not isinstance(input_task_id, str) or not TASK_ID.fullmatch(input_task_id):
        raise ValueError("Invalid Meshy task ID")
    if type(height_meters) not in (int, float) or not 0.3 <= height_meters <= 5:
        raise ValueError("Character height must be 0.3..5 metres")
    result = _request(RIGGING_API, payload={"input_task_id": input_task_id, "height_meters": height_meters}, opener=opener)
    task_id = result.get("result")
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
        raise ValueError("Meshy did not return a valid rigging task ID")
    return {"task_id": task_id, "status": "SUBMITTED", "kind": "rigging", "visual_approved": False}


def submit_animation(rig_task_id, action_id, *, opener=None):
    if not isinstance(rig_task_id, str) or not TASK_ID.fullmatch(rig_task_id):
        raise ValueError("Invalid Meshy rigging task ID")
    if type(action_id) is not int or not 0 <= action_id <= 100000:
        raise ValueError("Animation action_id must be an integer from Meshy's animation library")
    result = _request(ANIMATION_API, payload={"rig_task_id": rig_task_id, "action_id": action_id}, opener=opener)
    task_id = result.get("result")
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
        raise ValueError("Meshy did not return a valid animation task ID")
    return {"task_id": task_id, "status": "SUBMITTED", "kind": "animation", "visual_approved": False}


def _glb_urls(value, prefix=""):
    """Every *_glb_url string in a nested Meshy result, keyed by dotted path."""
    found = {}
    if isinstance(value, dict):
        for key, child in value.items():
            path = prefix + key
            if isinstance(child, str) and key.endswith("glb_url"):
                found[path] = child
            elif isinstance(child, dict):
                found.update(_glb_urls(child, path + "."))
    return found


def task_status(kind, task_id, *, opener=None):
    if kind not in ("image_to_3d", "rigging", "animation"):
        raise ValueError("Unknown Meshy task kind")
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
        raise ValueError("Invalid Meshy task ID")
    url = {"image_to_3d": API, "rigging": RIGGING_API, "animation": ANIMATION_API}[kind] + "/" + task_id
    result = _request(url, opener=opener)
    urls = _glb_urls(result.get("model_urls") or {}) if kind == "image_to_3d" else _glb_urls(result.get("result") or {})
    if kind == "image_to_3d" and isinstance((result.get("model_urls") or {}).get("glb"), str):
        urls["glb"] = result["model_urls"]["glb"]
    return {"task_id": task_id, "kind": kind, "status": result.get("status", "UNKNOWN"),
            "progress": result.get("progress"), "glb_urls": urls, "visual_approved": False}


def download_task_glbs(kind, task_id, output_dir, *, opener=None):
    """Download every GLB of a succeeded task (rig + basic animations) into NEW files."""
    info = task_status(kind, task_id, opener=opener)
    if info["status"] != "SUCCEEDED":
        raise ValueError("Meshy task has not succeeded")
    # Armature-only files carry no skinned mesh; the full-character variants suffice.
    urls = {k: v for k, v in info["glb_urls"].items() if "armature" not in k}
    if not urls:
        raise ValueError("Meshy returned no GLB download URL")
    output_dir = Path(output_dir)
    files = {}
    for key, url in sorted(urls.items()):
        name = re.sub(r"[^A-Za-z0-9_]+", "_", key).strip("_") + ".glb"
        files[key] = {"file": str(output_dir / name), "facts": _fetch_glb(url, output_dir / name, opener)}
    return {"task_id": task_id, "kind": kind, "files": files, "status": "DOWNLOADED_PENDING_REVIEW",
            "visual_approved": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Meshy candidate generation (never grants visual approval)")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("submit")
    p.add_argument("--image", required=True)
    p = sub.add_parser("status")
    p.add_argument("task_id")
    p = sub.add_parser("download")
    p.add_argument("task_id")
    p.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    if args.command == "submit":
        result = submit(args.image)
    elif args.command == "status":
        result = status(args.task_id)
    else:
        result = download(args.task_id, args.output)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
