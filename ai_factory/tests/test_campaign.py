"""Behavioral coverage for campaign generation and real Godot save/restart."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from ai_factory import core, genre3d


class CampaignTests(unittest.TestCase):
    def test_new_rpg_defaults_to_three_mission_campaign(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'Campaign'
            b = core.new(p, 'Campaign', 'a 3D RPG campaign')
            self.assertTrue(b['config']['campaign'])
            self.assertEqual(b['config']['missions'], 3)
            core.build(p)
            self.assertTrue((p / 'godot/campaign.gd').is_file())
            self.assertTrue((p / 'godot/campaign_scenario.gd').is_file())

    def test_bounded_revisions_preserve_unrepresented_character_requirements(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'Campaign'
            core.new(p, 'Campaign', 'a 3D RPG')
            b = core.add(p, 'add a mission, make missions longer and add a town with photorealistic Orion')
            self.assertEqual(b['config']['missions'], 4)
            self.assertEqual(b['config']['mission_length'], 2)
            self.assertTrue(b['config']['town'])
            self.assertIn('photorealistic Orion', b['requirements'][-1]['prompt'])
            self.assertEqual(b['requirements'][-1]['resolution'], 'PARTIAL_TEMPLATE_SUPPORT')
            with self.assertRaises(ValueError):
                core.add(p, '9 missions')
            self.assertEqual(core.load(p)['revision'], 2)

    def test_legacy_config_still_builds_an_arena(self):
        legacy = {'enemies': 1, 'areas': 1, 'speed': 5, 'abilities': ['heal']}
        self.assertEqual(genre3d.validate(legacy), legacy)
        revised = genre3d.propose('add an enemy', legacy, 'template')
        self.assertNotIn('campaign', revised)
        self.assertEqual(revised['enemies'], 2)
        for changes in [{'missions': 0}, {'missions': 6}, {'campaign': 1}, {'town': 'yes'}, {'mission_length': 4}, {'unknown': 1}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                genre3d.validate(dict(legacy, **changes))

    def test_real_campaign_and_save_survive_engine_restart(self):
        engine = os.environ.get('GODOT_BIN') or shutil.which('godot4') or shutil.which('godot')
        if not engine:
            self.skipTest('Godot unavailable: campaign runtime validation pending')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'Campaign'
            core.new(p, 'Campaign', 'a 3D RPG with 3 missions, a town and lightning')
            core.build(p)
            env = dict(os.environ, XDG_DATA_HOME=str(Path(d) / 'data'), XDG_CONFIG_HOME=str(Path(d) / 'config'), XDG_CACHE_HOME=str(Path(d) / 'cache'))
            for revision in range(2):
                if revision:
                    core.add(p, 'add a mission, make missions longer and add a new area')
                    core.build(p)
                for extra, marker in [([], 'FACTORY_CAMPAIGN_PASS'), (['--', '--verify-restart'], 'FACTORY_CAMPAIGN_RESTART_PASS')]:
                    result = subprocess.run([engine, '--headless', '--fixed-fps', '60', '--path', str(p / 'godot'), '--script', 'res://campaign_scenario.gd', *extra], capture_output=True, text=True, env=env, timeout=60)
                    output = result.stdout + result.stderr
                    self.assertEqual(result.returncode, 0, output)
                    self.assertIsNone(re.search(r'(?im)^\s*(SCRIPT ERROR:|ERROR:|Parse Error:)', output), output)
                    self.assertIn(marker, output.splitlines())

    def test_real_save_migration_and_incompatible_or_corrupt_archival(self):
        engine = os.environ.get('GODOT_BIN') or shutil.which('godot4') or shutil.which('godot')
        if not engine:
            self.skipTest('Godot unavailable: save migration runtime validation pending')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'Migration'
            core.new(p, 'Migration', 'a 3D RPG campaign with a town')
            core.build(p)
            env = dict(os.environ, XDG_DATA_HOME=str(Path(d) / 'data'), XDG_CONFIG_HOME=str(Path(d) / 'config'), XDG_CACHE_HOME=str(Path(d) / 'cache'))
            def run(flag=None):
                cmd = [engine, '--headless', '--fixed-fps', '60', '--path', str(p / 'godot'), '--script', 'res://campaign_scenario.gd']
                if flag:
                    cmd += ['--', flag]
                result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=60)
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, output)
                self.assertIsNone(re.search(r'(?im)^\s*(SCRIPT ERROR:|ERROR:|Parse Error:)', output), output)
                self.assertIn('FACTORY_CAMPAIGN_PASS', output.splitlines())
            run()
            core.add(p, 'add a mission, add a new area, make missions longer and add lightning')
            core.build(p)
            run('--verify-migration')
            save = next((Path(d) / 'data').rglob('campaign-v1.json'))
            migrated = save.read_bytes()
            core.add(p, '1 mission')
            core.build(p)
            run('--verify-archive')
            self.assertTrue(any(f.read_bytes() == migrated for f in save.parent.glob('campaign-v1.json.preserved-*')))
            corrupt = b'{broken user save must survive'
            save.write_bytes(corrupt)
            run('--verify-archive')
            self.assertTrue(any(f.read_bytes() == corrupt for f in save.parent.glob('campaign-v1.json.preserved-*')))
            self.assertEqual(json.loads(save.read_text())['state']['mission_index'], 0)
