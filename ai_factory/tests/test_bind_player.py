"""Offline binding gates. No real Godot or Meshy credits required."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_factory.bind_player import bind


class BindPlayerTests(unittest.TestCase):
    def test_rejects_unapproved_asset_without_engine_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            bible = {"template": "rpg_3d", "assets": [{
                "character": "Hero", "sha256": "b" * 64,
                "license_review": "PENDING", "visual_review": "PENDING",
                "approved": True, "license": "CC0", "author": "Tester",
                "source": "Test", "reference_sha256": "a" * 64}],
                "approved_appearance_references": {"Hero": "a" * 64}}
            with patch("ai_factory.bind_player._managed_guard"), patch(
                    "ai_factory.bind_player.core.load", return_value=bible), patch(
                    "ai_factory.bind_player.check_candidate") as check:
                with self.assertRaisesRegex(ValueError, "approval"):
                    bind(tmp, "Hero", "b" * 64)
                check.assert_not_called()

    def test_wrong_character_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            bible = {"template": "rpg_3d", "assets": [],
                "approved_appearance_references": {}}
            with patch("ai_factory.bind_player._managed_guard"), patch(
                    "ai_factory.bind_player.core.load", return_value=bible):
                with self.assertRaisesRegex(ValueError, "Select one"):
                    bind(tmp, "Unlisted", "f" * 64)

    def test_non_rpg_is_not_modified(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("ai_factory.bind_player._managed_guard"), patch(
                    "ai_factory.bind_player.core.load", return_value={"template": "collect_survive_2d"}):
                with self.assertRaisesRegex(ValueError, "3D RPG"):
                    bind(tmp, "Hero", "a" * 64)


if __name__ == "__main__":
    unittest.main()
