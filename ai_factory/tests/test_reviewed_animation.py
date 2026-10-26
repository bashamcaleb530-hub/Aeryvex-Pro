"""Source contract tests for opt-in reviewed-clip playback.

These do not replace a real Godot import/gameplay test.
"""
from pathlib import Path
import unittest

ACTOR = Path(__file__).resolve().parents[1] / "templates" / "rpg_3d" / "actor.gd"


class ReviewedAnimationTests(unittest.TestCase):
    def test_controller_retains_physics_and_combat(self):
        source = ACTOR.read_text()
        for required in ("move_and_slide()", "func attack()", "func special(",
                         "func damage(", "SpringArm3D.new()"):
            self.assertIn(required, source)

    def test_animation_playback_is_opt_in_and_reversible(self):
        source = ACTOR.read_text()
        for required in ('ResourceLoader.exists("res://player_visual.glb")',
                         'res://player_visual.json', 'character_animator.has_animation(clip)',
                         'update_character_animation("idle")',
                         'update_character_animation("attack")',
                         'update_character_animation("run" if running else "walk")'):
            self.assertIn(required, source)

    def test_no_arbitrary_user_animation_path_execution(self):
        source = ACTOR.read_text()
        self.assertIn('for state in ["idle", "walk", "run", "attack"]:', source)
        self.assertIn('find_animation_player(visual)', source)


if __name__ == "__main__":
    unittest.main()
