"""GLB animation merge: clips from same-rig files combine into one valid GLB."""
import tempfile
import unittest
from pathlib import Path

from ai_factory.assets import inspect_glb
from ai_factory.glb_tools import merge_animations, read_glb
from asset_fixtures import humanoid_glb, write_glb, write_humanoid_fixture


class GlbMergeTests(unittest.TestCase):
    def test_merges_single_clip_files_onto_static_rig(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            base = write_humanoid_fixture(d / 'rig.glb', clips=[])
            walk = write_humanoid_fixture(d / 'walk.glb', clips=['Walking'])
            death = write_humanoid_fixture(d / 'death.glb', clips=['Death'])
            self.assertEqual(inspect_glb(base)['animations'], [])
            result = merge_animations(base, [(walk, {}), (death, {'Death': 'Dying'})], d / 'merged.glb')
            facts = inspect_glb(d / 'merged.glb')
            self.assertEqual(facts['animations'], ['Walking', 'Dying'])
            self.assertEqual(result['sha256'], facts['sha256'])
            doc, _ = read_glb(d / 'merged.glb')
            # Channels re-targeted to the base rig's own joint nodes.
            names = [doc['nodes'][c['target']['node']]['name'] for c in doc['animations'][1]['channels']]
            self.assertIn('Hips', names)

    def test_refuses_unmatched_rig_duplicate_names_and_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            base = write_humanoid_fixture(d / 'rig.glb', clips=['Idle'])
            other_doc, blob = humanoid_glb(['Death'])
            other_doc['nodes'][1]['name'] = 'pelvis'
            write_glb(d / 'other.glb', other_doc, blob)
            with self.assertRaisesRegex(ValueError, 'absent or ambiguous'):
                merge_animations(base, [(d / 'other.glb', {})], d / 'out1.glb')
            same = write_humanoid_fixture(d / 'idle.glb', clips=['Idle'])
            with self.assertRaisesRegex(ValueError, 'already exists'):
                merge_animations(base, [(same, {})], d / 'out2.glb')
            with self.assertRaisesRegex(ValueError, 'no clip named'):
                merge_animations(base, [(same, {'Nope': 'x'})], d / 'out3.glb')
            with self.assertRaisesRegex(ValueError, 'new .glb'):
                merge_animations(base, [(same, {'Idle': 'Idle2'})], base)
            self.assertFalse((d / 'out1.glb').exists())


if __name__ == '__main__':
    unittest.main()
