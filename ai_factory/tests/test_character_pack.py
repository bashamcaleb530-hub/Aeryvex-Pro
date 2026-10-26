"""Character-pack approval gates (offline)."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from ai_factory.character_pack import export_character


def glb():
    body = b'{"asset":{"version":"2.0"}}'
    body += b" " * (-len(body) % 4)
    return struct.pack("<4sII", b"glTF", 2, len(body) + 20) + struct.pack("<II", len(body), 0x4e4f534a) + body


class CharacterPackTests(unittest.TestCase):
    def test_requires_locked_reference_before_export(self):
        with tempfile.TemporaryDirectory() as root:
            with patch("ai_factory.character_pack.core.load", return_value={
                "approved_appearance_references": {}, "assets": []}):
                with self.assertRaisesRegex(ValueError, "locked"):
                    export_character(root, "Hero", Path(root) / "pack")

    def test_requires_two_review_approvals(self):
        with tempfile.TemporaryDirectory() as root:
            data=glb()
            import hashlib
            sha=hashlib.sha256(data).hexdigest()
            asset=Path(root)/"assets"/(sha+".glb")
            asset.parent.mkdir()
            asset.write_bytes(data)
            row={"character":"Hero","sha256":sha,"file":"assets/"+sha+".glb",
                 "reference_sha256":"a"*64,"approved":True,"license":"CC0",
                 "author":"Test","source":"Test asset", "license_review":"APPROVED",
                 "visual_review":"PENDING","animation_mapping":{}}
            bible={"approved_appearance_references":{"Hero":"a"*64},"assets":[row]}
            with patch("ai_factory.character_pack.core.load",return_value=bible):
                with self.assertRaisesRegex(ValueError, "visual review"):
                    export_character(root,"Hero",Path(root)/"pack")
                self.assertFalse((Path(root)/"pack").exists())

    def test_success_exports_manifest_and_does_not_modify_asset(self):
        with tempfile.TemporaryDirectory() as root:
            import hashlib
            data=glb()
            sha=hashlib.sha256(data).hexdigest()
            asset=Path(root)/"assets"/(sha+".glb")
            asset.parent.mkdir()
            asset.write_bytes(data)
            row={"character":"Hero","sha256":sha,"file":"assets/"+sha+".glb",
                 "reference_sha256":"a"*64,"approved":True,"license":"CC0",
                 "author":"Test","source":"Test asset", "license_review":"APPROVED",
                 "visual_review":"APPROVED","animation_mapping":{}}
            bible={"approved_appearance_references":{"Hero":"a"*64},"assets":[row]}
            out=Path(root)/"pack"
            with patch("ai_factory.character_pack.core.load",return_value=bible):
                result=export_character(root,"Hero",out)
            self.assertEqual(result["source_sha256"],sha)
            self.assertEqual(json.loads((out/"character_manifest.json").read_text())["character"],"Hero")
            self.assertEqual((out/"character.glb").read_bytes(),data)
            self.assertEqual(asset.read_bytes(),data)
            self.assertEqual(result["gameplay_binding"],"NOT_IMPLEMENTED")


if __name__ == "__main__":
    unittest.main()
