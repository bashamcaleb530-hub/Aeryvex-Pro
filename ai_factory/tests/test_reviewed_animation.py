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
                         'update_character_animation(choose_animation_state())',
                         'update_character_animation("death")'):
            self.assertIn(required, source)

    def test_state_machine_covers_jump_damage_death_and_transitions(self):
        source = ACTOR.read_text()
        self.assertIn('const ANIMATION_STATES := ["idle", "walk", "run", "jump", "fall", "land", "attack", "hurt", "death"]', source)
        for required in ('hurt_animation_time = clip_length("hurt"', 'candidates.append("death")',
                         'candidates.append("jump" if velocity.y > 0.0 else "fall")',
                         'character_animator.play(clip, ANIMATION_BLEND.get(state, 0.15))',
                         'Animation.LOOP_LINEAR if state in LOOPING_STATES else Animation.LOOP_NONE',
                         'func play_cinematic(state: String) -> bool:'):
            self.assertIn(required, source)

    def test_no_arbitrary_user_animation_path_execution(self):
        source = ACTOR.read_text()
        # Only whitelisted state names (or cinematic_*) select clips; clips must exist.
        self.assertIn('if not (state in ANIMATION_STATES or str(state).begins_with("cinematic_")):', source)
        self.assertIn('find_animation_player(visual)', source)
        self.assertNotIn('load(clip', source)

if __name__ == "__main__":
    unittest.main()
