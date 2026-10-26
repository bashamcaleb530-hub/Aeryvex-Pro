"""Asset intake never grants art approval or bypasses immutable revisions."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from ai_factory import assets, core
from asset_fixtures import synthetic_glb, write_glb


class AssetReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'fixture.glb'
        write_glb(self.source)
        self.metadata = dict(approved=True, license='CC0-1.0', author='Synthetic test',
                             source='generated test triangle', reference_sha256='a' * 64)

    def project(self):
        path = self.root / 'Demo'
        core.new(path, 'Demo', '3D RPG')
        return path

    def test_container_inspection_reports_facts_without_engine_or_art_approval(self):
        result = assets.inspect_glb(self.source)
        self.assertEqual(result['skins'], 1)
        self.assertEqual(result['animations'], ['idle'])
        self.assertEqual(result['sha256'], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertEqual(result['engine_import'], 'PENDING')

    def test_malformed_chunks_and_external_uris_rejected_before_copy(self):
        original = self.source.read_bytes()
        bad = bytearray(original)
        struct.pack_into('<I', bad, 12, len(original) + 4)
        self.source.write_bytes(bad)
        with self.assertRaises(ValueError):
            assets.stage_glb(self.source, self.root / 'out.glb', self.metadata)
        self.assertFalse((self.root / 'out.glb').exists())
        for uri in ('../../secret', 'file:///etc/passwd', 'https://example.test/x', 'data:application/octet-stream;base64,AA=='):
            with self.subTest(uri=uri):
                doc, blob = synthetic_glb()
                doc['buffers'][0]['uri'] = uri
                write_glb(self.source, doc, blob)
                with self.assertRaisesRegex(ValueError, 'URI|uri'):
                    assets.inspect_glb(self.source)
        doc, blob = synthetic_glb()
        doc['extras'] = {'nested': {'uri': 'https://example.test/evil'}}
        write_glb(self.source, doc, blob)
        with self.assertRaisesRegex(ValueError, 'URI|uri'):
            assets.inspect_glb(self.source)

    def test_buffer_ranges_validated(self):
        doc, blob = synthetic_glb()
        doc['bufferViews'][0]['byteLength'] = len(blob) + 1
        write_glb(self.source, doc, blob)
        with self.assertRaises(ValueError):
            assets.inspect_glb(self.source)

    def test_malformed_image_and_undeclared_extensions_are_rejected(self):
        for extra in ({'images': 7}, {'extensions': {'EXT_untrusted': {'url': 'file:///etc/passwd'}}}):
            with self.subTest(extra=extra):
                doc, blob = synthetic_glb()
                doc.update(extra)
                write_glb(self.source, doc, blob)
                with self.assertRaises(ValueError):
                    assets.inspect_glb(self.source)

    def test_mapping_cannot_claim_clips_absent_from_container(self):
        from ai_factory import asset_review
        with self.assertRaisesRegex(ValueError, 'animation'):
            asset_review.stage(self.project(), self.source,
                               dict(self.metadata, animation_mapping={'attack': 'missing'}))

    def test_staging_creates_revision_with_pending_approvals_and_no_runtime_copy(self):
        from ai_factory import asset_review
        path = self.project()
        before = (path / 'checkpoints/0001.json').read_bytes()
        result = asset_review.stage(path, self.source, self.metadata)
        self.assertEqual(result['revision'], 2)
        row = result['assets'][0]
        self.assertEqual(row['license_review'], 'PENDING')
        self.assertEqual(row['visual_review'], 'PENDING')
        self.assertEqual(row['prototype_review'], 'PENDING')
        self.assertEqual(row['engine_import'], 'PENDING')
        self.assertTrue((path / row['file']).is_file())
        self.assertFalse((path / 'godot').exists())
        self.assertEqual((path / 'checkpoints/0001.json').read_bytes(), before)
        inventory = asset_review.inventory(path)
        self.assertEqual(inventory['assets'][0]['integrity'], 'VERIFIED')
        self.assertEqual(inventory['production_art'], 'BLOCKED')

    def test_locked_character_reference_never_replaced(self):
        from ai_factory import asset_review
        path = self.project()
        bible = core.load(path)
        bible['approved_appearance_references'] = {'Orion': 'b' * 64}
        core.write_json(path / 'bible.json', bible)
        with self.assertRaisesRegex(ValueError, 'reference'):
            asset_review.stage(path, self.source, self.metadata, character='Orion')
        self.assertEqual(core.load(path)['revision'], 1)
        self.assertFalse((path / 'assets').exists())

    def test_approval_is_explicit_and_unknown_license_cannot_be_approved(self):
        from ai_factory import asset_review
        path = self.project()
        with self.assertRaises(ValueError):
            asset_review.stage(path, self.source, dict(self.metadata, approved=False))
        bible = asset_review.stage(path, self.source, dict(self.metadata, license='unknown'))
        row = bible['assets'][0]
        with self.assertRaisesRegex(ValueError, 'license'):
            asset_review.review(path, row['sha256'], license_approved=True)
        self.assertEqual(core.load(path)['revision'], 2)

    def test_review_changes_only_requested_state_and_detects_asset_tampering(self):
        from ai_factory import asset_review
        path = self.project()
        row = asset_review.stage(path, self.source, self.metadata)['assets'][0]
        bible = asset_review.review(path, row['sha256'], prototype_approved=True)
        self.assertEqual(bible['revision'], 3)
        self.assertEqual(bible['assets'][0]['prototype_review'], 'APPROVED')
        self.assertEqual(bible['assets'][0]['visual_review'], 'PENDING')
        self.assertEqual(bible['assets'][0]['engine_import'], 'PENDING')
        (path / row['file']).write_bytes(b'tampered')
        self.assertEqual(asset_review.inventory(path)['assets'][0]['integrity'], 'FAILED')
        with self.assertRaisesRegex(ValueError, 'integrity'):
            asset_review.review(path, row['sha256'], visual_approved=True)
        self.assertEqual(core.load(path)['revision'], 3)

    def test_character_review_refuses_missing_reference_lock(self):
        from ai_factory import asset_review
        path = self.project()
        bible = core.load(path)
        bible['approved_appearance_references'] = {'Orion': 'a' * 64}
        core.write_json(path / 'bible.json', bible)
        row = asset_review.stage(path, self.source, self.metadata, character='Orion')['assets'][0]
        bible = core.load(path)
        bible['approved_appearance_references'] = {}
        core.write_json(path / 'bible.json', bible)
        with self.assertRaisesRegex(ValueError, 'reference'):
            asset_review.review(path, row['sha256'], visual_approved=True)

    def test_managed_edits_prevent_asset_revision(self):
        from ai_factory import asset_review
        path = self.project()
        core.build(path)
        (path / 'godot/main.gd').write_text('user edit')
        with self.assertRaisesRegex(ValueError, 'Managed|managed'):
            asset_review.stage(path, self.source, self.metadata)
        self.assertEqual(core.load(path)['revision'], 1)

    def test_duplicate_intake_does_not_overwrite_existing_asset_or_revision(self):
        from ai_factory import asset_review
        path = self.project()
        asset_review.stage(path, self.source, self.metadata)
        with self.assertRaisesRegex(ValueError, 'already|duplicate'):
            asset_review.stage(path, self.source, self.metadata)
        self.assertEqual(core.load(path)['revision'], 2)


class GenreRegistryTests(unittest.TestCase):
    def test_registry_selects_existing_generators_and_preserves_default(self):
        from ai_factory import genres
        self.assertEqual(genres.select('5 coins')['id'], 'collect_survive_2d')
        self.assertEqual(genres.select('a third person RPG')['id'], 'rpg_3d')
        self.assertEqual(genres.get('rpg_3d')['backend'], 'rpg_3d')
        self.assertEqual(len(genres.registry()), 2)

    def test_untrusted_manifest_cannot_name_code_or_paths(self):
        from ai_factory import genres
        good = genres.get('rpg_3d')
        for change in ({'backend': 'os.system'}, {'template_directory': '../../original_game'},
                       {'match': ['(']}, {'id': '../../evil'}, {'arbitrary_code': 'print(1)'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                genres.validate_manifest(dict(copy.deepcopy(good), **change))


if __name__ == '__main__':
    unittest.main()
