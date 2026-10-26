"""No-network isolated candidate-check unit tests."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from ai_factory.godot_candidate_check import check_candidate


def minimal_glb():
    data = json.dumps({"asset": {"version": "2.0"}}).encode()
    data += b" " * (-len(data) % 4)
    return struct.pack("<4sII", b"glTF", 2, len(data) + 20) + struct.pack("<II", len(data), 0x4E4F534A) + data


class CandidateCheckTests(unittest.TestCase):
    def test_missing_godot_returns_blocked_without_modifying_asset(self):
        with tempfile.TemporaryDirectory() as temp:
            asset = Path(temp) / "model.glb"
            content = minimal_glb()
            asset.write_bytes(content)
            with patch("ai_factory.godot_candidate_check.shutil.which", return_value=None), patch.dict(
                    "os.environ", {"GODOT_BIN": ""}):
                result = check_candidate(asset)
            self.assertEqual(result["status"], "BLOCKED_GODOT_UNAVAILABLE")
            self.assertEqual(result["engine_import"], "NOT_RUN")
            self.assertFalse(result["visual_approved"])
            self.assertEqual(asset.read_bytes(), content)

    def test_invalid_glb_fails_before_engine_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            asset = Path(temp) / "fake.glb"
            asset.write_bytes(b"not a glb")
            with self.assertRaises(ValueError):
                check_candidate(asset, godot_bin="/nonexistent")


if __name__ == "__main__":
    unittest.main()
