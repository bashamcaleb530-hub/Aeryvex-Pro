"""Character Studio workflow: reference lock -> candidate -> inspection -> approval -> binding.

Offline tests stub Meshy HTTP (no paid requests). The engine test runs the full
pipeline in real Godot and is skipped when no Godot 4 binary is available.
"""
import base64
import io
import json
import os
import shutil
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

from ai_factory import character_studio as cs, core
from asset_fixtures import write_humanoid_fixture

ENGINE = os.environ.get('GODOT_BIN') or shutil.which('godot4') or shutil.which('godot')


def png(color=b'\x20\x60\xff'):
    raw = b''.join(b'\0' + color * 4 for _ in range(4))
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 4, 4, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


class Response(io.BytesIO):
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()


def project(root, name='Hero3D'):
    path = core.project_path(root, name)
    core.new(path, name, 'A 3D RPG with 2 missions, a town, 1 enemy and heal')
    return path


def passing_inspection(path, character, sha, mapping):
    """Record an inspection report as if Godot had passed (offline gate tests only)."""
    run = cs.inspection_dir(path, character, sha) / 'run-001'
    run.mkdir(parents=True)
    (run / 'report.json').write_text(json.dumps({'engine_import': 'PASSED', 'status': 'INSPECTED_PENDING_HUMAN_REVIEW',
                                                 'mapping_verification': {s: {'clip': c, 'status': 'ENGINE_VERIFIED'} for s, c in mapping.items()},
                                                 'renders': [], 'render_status': 'BLOCKED_NO_DISPLAY'}))


class ReferenceLockTests(unittest.TestCase):
    def test_lock_requires_confirmation_and_real_image(self):
        with tempfile.TemporaryDirectory() as d:
            p = project(d)
            with self.assertRaisesRegex(ValueError, 'Confirm'):
                cs.lock_reference(p, 'Orion', png(), '.png', False)
            with self.assertRaisesRegex(ValueError, 'does not match'):
                cs.lock_reference(p, 'Orion', b'not an image', '.png', True)
            with self.assertRaisesRegex(ValueError, 'PNG, JPG or WEBP'):
                cs.lock_reference(p, 'Orion', png(), '.gif', True)
            self.assertEqual(core.load(p)['revision'], 1)

    def test_lock_is_exact_permanent_and_survives_design_revisions(self):
        with tempfile.TemporaryDirectory() as d:
            p = project(d)
            data = png()
            locked = cs.lock_reference(p, 'Orion Valen', data, '.png', True, 'approved lineup crop')
            self.assertEqual(locked['status'], 'LOCKED')
            self.assertEqual(cs.reference_file(p, 'Orion Valen').read_bytes(), data)
            self.assertEqual(cs.lock_reference(p, 'Orion Valen', data, '.png', True)['status'], 'ALREADY_LOCKED')
            with self.assertRaisesRegex(ValueError, 'never replaced'):
                cs.lock_reference(p, 'Orion Valen', png(b'\xff\x00\x00'), '.png', True)
            core.add(p, 'Add lightning and a new area')
            self.assertEqual(core.load(p)['approved_appearance_references']['Orion Valen'], locked['sha256'])
            # A changed reference file is refused rather than silently substituted.
            cs.reference_file(p, 'Orion Valen').write_bytes(png(b'\x00\xff\x00'))
            with self.assertRaisesRegex(ValueError, 'missing or changed'):
                cs.reference_file(p, 'Orion Valen')


class CandidateTests(unittest.TestCase):
    def test_upload_requires_locked_reference(self):
        with tempfile.TemporaryDirectory() as d:
            p = project(d)
            glb = write_humanoid_fixture(Path(d) / 'h.glb')
            with self.assertRaisesRegex(ValueError, 'Lock an approved reference'):
                cs.add_upload(p, 'Orion', glb.read_bytes(), 'artist delivery')

    def test_meshy_requires_paid_authorization_and_sends_exact_reference(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {'MESHY_API_KEY': 'fake'}):
            p = project(d)
            data = png()
            cs.lock_reference(p, 'Orion', data, '.png', True)
            calls = []
            def fake_open(request, timeout):
                calls.append(request)
                body = json.loads(request.data)
                self.assertEqual(base64.b64decode(body['image_url'].split(',', 1)[1]), data)
                return Response(b'{"result":"task-abc"}')
            with self.assertRaisesRegex(ValueError, 'paid credits'):
                cs.meshy_generate(p, 'Orion', authorize_paid=False, opener=fake_open)
            self.assertEqual(calls, [])
            row = cs.meshy_generate(p, 'Orion', authorize_paid=True, opener=fake_open)
            self.assertEqual((row['id'], row['status'], row['reference_sha256']), ('meshy-task-abc', 'SUBMITTED', core.digest(cs.reference_file(p, 'Orion'))))
            self.assertFalse(row['visual_approved'])

    def test_meshy_rigging_download_merges_basic_animations(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {'MESHY_API_KEY': 'fake'}):
            d = Path(d)
            p = project(d)
            cs.lock_reference(p, 'Orion', png(), '.png', True)
            rig = write_humanoid_fixture(d / 'rig.glb', clips=[]).read_bytes()
            walking = write_humanoid_fixture(d / 'walk.glb', clips=['Walking']).read_bytes()
            running = write_humanoid_fixture(d / 'run.glb', clips=['Running']).read_bytes()
            files = {'https://assets.meshy.ai/r/rig.glb': rig, 'https://assets.meshy.ai/r/walk.glb': walking,
                     'https://assets.meshy.ai/r/run.glb': running}
            def fake_open(request, timeout):
                url = request.full_url
                if url in files:
                    return Response(files[url])
                if url.endswith('/image-to-3d'):
                    return Response(b'{"result":"img-1"}')
                if url.endswith('/image-to-3d/img-1'):
                    return Response(b'{"status":"SUCCEEDED","progress":100,"model_urls":{"glb":"https://assets.meshy.ai/r/rig.glb"}}')
                if url.endswith('/rigging'):
                    self.assertEqual(json.loads(request.data)['input_task_id'], 'img-1')
                    return Response(b'{"result":"rig-1"}')
                if url.endswith('/rigging/rig-1'):
                    return Response(json.dumps({'status': 'SUCCEEDED', 'progress': 100, 'result': {
                        'rigged_character_glb_url': 'https://assets.meshy.ai/r/rig.glb',
                        'basic_animations': {'walking_glb_url': 'https://assets.meshy.ai/r/walk.glb',
                                             'walking_armature_glb_url': 'https://assets.meshy.ai/r/missing.glb',
                                             'running_glb_url': 'https://assets.meshy.ai/r/run.glb'}}}).encode())
                raise AssertionError('unexpected request ' + url)
            image = cs.meshy_generate(p, 'Orion', True, opener=fake_open)
            with self.assertRaisesRegex(ValueError, 'succeeded'):
                cs.meshy_rig(p, 'Orion', image['id'], True, opener=fake_open)
            self.assertEqual(cs.meshy_refresh(p, 'Orion', image['id'], opener=fake_open)['status'], 'SUCCEEDED')
            rigging = cs.meshy_rig(p, 'Orion', image['id'], True, opener=fake_open)
            fetched = cs.meshy_fetch(p, 'Orion', rigging['id'], opener=fake_open)
            self.assertEqual(sorted(fetched['animations']), ['Running', 'Walking'])
            self.assertTrue(cs.candidate_file(p, fetched).is_file())
            self.assertEqual(cs.suggest_mapping(fetched['animations']), {'run': 'Running', 'walk': 'Walking'})


class DecisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.p = project(self.root)
        cs.lock_reference(self.p, 'Orion', png(), '.png', True)
        glb = write_humanoid_fixture(self.root / 'h.glb')
        self.candidate = cs.add_upload(self.p, 'Orion', glb.read_bytes(), 'synthetic test rig')
        self.mapping = {'idle': 'Idle', 'walk': 'Walking', 'death': 'Death'}

    def tearDown(self):
        self.temp.cleanup()

    def test_mapping_validation_and_suggestions(self):
        clips = ['Idle', 'Walking', 'Running', 'Jump', 'Attack', 'Hit_Reaction', 'Death', 'Bow']
        self.assertEqual(cs.suggest_mapping(clips), {'idle': 'Idle', 'walk': 'Walking', 'run': 'Running', 'jump': 'Jump',
                                                     'attack': 'Attack', 'hurt': 'Hit_Reaction', 'death': 'Death', 'cinematic_bow': 'Bow'})
        with self.assertRaisesRegex(ValueError, 'Unknown animation state'):
            cs.validate_mapping({'teleport': 'Idle'}, clips)
        with self.assertRaisesRegex(ValueError, 'not in this GLB'):
            cs.validate_mapping({'idle': 'Missing'}, clips)

    def test_stage_requires_inspection_and_records_provenance(self):
        with self.assertRaisesRegex(ValueError, 'passing Godot inspection'):
            cs.stage_candidate(self.p, 'Orion', self.candidate['id'], 'CC0', 'Tester', self.mapping, True)
        passing_inspection(self.p, 'Orion', self.candidate['glb_sha256'], self.mapping)
        with self.assertRaisesRegex(ValueError, 'intake approval'):
            cs.stage_candidate(self.p, 'Orion', self.candidate['id'], 'CC0', 'Tester', self.mapping, False)
        staged = cs.stage_candidate(self.p, 'Orion', self.candidate['id'], 'CC0', 'Tester', self.mapping, True)
        row = core.load(self.p)['assets'][0]
        self.assertEqual((row['character'], row['visual_review'], row['animation_mapping']), ('Orion', 'PENDING', self.mapping))
        self.assertIn('approved reference', row['source'])
        self.assertEqual(staged['sha256'], self.candidate['glb_sha256'])

    def test_reject_records_reason_and_unbinds(self):
        passing_inspection(self.p, 'Orion', self.candidate['glb_sha256'], self.mapping)
        sha = cs.stage_candidate(self.p, 'Orion', self.candidate['id'], 'CC0', 'Tester', self.mapping, True)['sha256']
        cs.decide(self.p, sha, True, license_approved=True)
        bible = core.load(self.p)
        bible['assets'][0]['engine_import'] = 'RUNTIME_CHECKED'
        bible['player_visual_binding'] = {'character': 'Orion', 'sha256': sha}
        bible['revision'] += 1
        core.save_revision(self.p, bible)
        cs.decide(self.p, sha, False, reason='Face does not match the lineup')
        bible = core.load(self.p)
        self.assertEqual(bible['assets'][0]['visual_review'], 'REJECTED')
        self.assertNotIn('player_visual_binding', bible)
        with self.assertRaisesRegex(ValueError, 'approval'):
            cs.bind(self.p, sha)
        steps = cs.overview(self.p)['characters'][0]['steps']
        self.assertEqual((steps['approval']['status'], steps['binding']['status']), ('REJECTED', 'NOT_BOUND'))

    def test_approval_requires_engine_inspection(self):
        passing_inspection(self.p, 'Orion', self.candidate['glb_sha256'], self.mapping)
        sha = cs.stage_candidate(self.p, 'Orion', self.candidate['id'], 'CC0', 'Tester', self.mapping, True)['sha256']
        shutil.rmtree(cs.inspection_dir(self.p, 'Orion', sha))
        with self.assertRaisesRegex(ValueError, 'Inspect this exact GLB'):
            cs.decide(self.p, sha, True, license_approved=True)


@unittest.skipUnless(ENGINE, 'Godot unavailable: character runtime validation pending')
class EngineCharacterPipelineTests(unittest.TestCase):
    def test_reference_to_playable_animated_character(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            p = project(d)
            cs.lock_reference(p, 'Orion', png(), '.png', True)
            candidate = cs.add_upload(p, 'Orion', write_humanoid_fixture(d / 'h.glb').read_bytes(), 'synthetic test rig')
            report = cs.inspect_candidate(p, 'Orion', candidate['id'])
            self.assertEqual((report['engine_import'], report['rig']), ('PASSED', 'SKINNED_SKELETON'))
            self.assertTrue(all(v['status'] == 'ENGINE_VERIFIED' for v in report['mapping_verification'].values()))
            if report['render_status'] == 'RENDERED':
                self.assertTrue(any(r['kind'] == 'pose' for r in report['renders']))
            sha = cs.stage_candidate(p, 'Orion', candidate['id'], 'CC0', 'Tester', report['mapping'], True)['sha256']
            cs.decide(p, sha, True, license_approved=True)
            cs.bind(p, sha)
            core.build(p)
            qa = core.test(p)
            character = [c for c in qa['checks'] if c['name'] == 'character']
            self.assertEqual(qa['status'], 'RUNTIME_CHECKED')
            self.assertTrue(character and character[0]['passed'])
            for state in ('walk', 'run', 'jump', 'attack', 'hurt', 'death'):
                self.assertIn('"' + state + '"', character[0]['log'])
            self.assertEqual(cs.overview(p)['characters'][0]['steps']['game_qa']['status'], 'PASSED')


if __name__ == '__main__':
    unittest.main()
