"""Focused tests for the non-destructive standalone Godot GLB preview."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / "tools" / "preview_character.py"
spec = importlib.util.spec_from_file_location("preview_character", TOOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PreviewCharacterTests(unittest.TestCase):
    def test_creates_separate_project_without_changing_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "sorn.glb"
            # Minimal syntactically structured GLB fixture; not a finished mesh.
            payload = b'{"asset":{"version":"2.0"}}'
            payload += b" " * ((-len(payload)) % 4)
            raw = struct.pack("<4sII", b"glTF", 2, 20 + len(payload))
            raw += struct.pack("<II", len(payload), 0x4E4F534A) + payload
            source.write_bytes(raw)
            destination = root / "SornPreview"
            mod.create_preview(source, destination)
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual((destination / "character.glb").read_bytes(), raw)
            self.assertIn('move_and_slide()', (destination / "main.gd").read_text())
            self.assertTrue((destination / "project.godot").is_file())
            with self.assertRaises(FileExistsError):
                mod.create_preview(source, destination)

    def test_rejects_invalid_binary_and_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "fake.glb"
            source.write_bytes(b"not a glb")
            destination = root / "Preview"
            with self.assertRaises(ValueError):
                mod.create_preview(source, destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
