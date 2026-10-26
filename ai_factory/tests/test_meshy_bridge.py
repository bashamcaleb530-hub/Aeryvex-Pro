"""Offline Meshy connector tests; no paid API requests."""
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from ai_factory import meshy_bridge


class Response(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


class MeshyBridgeTests(unittest.TestCase):
    def test_missing_api_key(self):
        with patch.dict(os.environ, {"MESHY_API_KEY": ""}):
            with self.assertRaisesRegex(ValueError, "MESHY_API_KEY"):
                meshy_bridge.status("task-123")

    def test_invalid_task_id(self):
        with self.assertRaisesRegex(ValueError, "Invalid"):
            meshy_bridge.status("../secret")

    def test_submit_is_unapproved(self):
        with TemporaryDirectory() as temp, patch.dict(os.environ, {"MESHY_API_KEY": "fake"}):
            image = Path(temp) / "hero.png"
            image.write_bytes(b"fake-example")
            def fake_open(request, timeout):
                body = json.loads(request.data)
                self.assertTrue(body["image_url"].startswith("data:image/png;base64,"))
                self.assertEqual(body["target_formats"], ["glb"])
                return Response(b'{"result":"task-123"}')
            result = meshy_bridge.submit(image, opener=fake_open)
            self.assertEqual(result["task_id"], "task-123")
            self.assertFalse(result["visual_approved"])

    def test_download_rejects_untrusted_host(self):
        with TemporaryDirectory() as temp, patch.dict(os.environ, {"MESHY_API_KEY": "fake"}):
            def fake_open(request, timeout):
                return Response(json.dumps({"status": "SUCCEEDED",
                    "model_urls": {"glb": "https://localhost/private.glb"}}).encode())
            with self.assertRaisesRegex(ValueError, "Untrusted"):
                meshy_bridge.download("task-123", Path(temp) / "candidate.glb", opener=fake_open)
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_download_rejects_not_ready(self):
        with TemporaryDirectory() as temp, patch.dict(os.environ, {"MESHY_API_KEY": "fake"}):
            def fake_open(request, timeout):
                return Response(b'{"status":"IN_PROGRESS"}')
            with self.assertRaisesRegex(ValueError, "not succeeded"):
                meshy_bridge.download("task-123", Path(temp) / "candidate.glb", opener=fake_open)


if __name__ == "__main__":
    unittest.main()
