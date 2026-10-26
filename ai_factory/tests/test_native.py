"""Native export safety tests; fixture executables exercise the real subprocess path."""
import hashlib
import json
import os
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from ai_factory import core


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / 'Demo'
        core.new(self.path, 'Demo', 'collect coins')
        core.build(self.path)
        core.write_json(self.path / 'qa.json', {'status': 'RUNTIME_CHECKED', 'evidence': core.evidence_key(self.path)})
        self.templates = self.root / 'templates' / '4.2.2.stable'
        self.templates.mkdir(parents=True)
        (self.templates / 'version.txt').write_text('4.2.2.stable\n')
        for name in ['linux_debug.x86_64', 'linux_release.x86_64']:
            (self.templates / name).write_bytes(b'\x7fELFfixture')
        self.engine = self.root / 'godot'
        self.engine.write_text('''#!/usr/bin/env python3
import os, pathlib, sys
args=sys.argv[1:]
if '--version' in args:
    print(os.environ.get('FAKE_VERSION','4.2.2.stable.official.fixture'))
    sys.exit(0)
if os.environ.get('FAKE_ERROR'):
    print('SCRIPT ERROR: broken export',file=sys.stderr)
    sys.exit(0)
if '--export-release' in args:
    destination=pathlib.Path(args[-1])
    destination.write_text(''' + repr('''#!/usr/bin/env python3
import os, pathlib, sys
if pathlib.Path('project.godot').exists():
    sys.exit('relocation must have no project.godot')
if not pathlib.Path(__file__).with_suffix('.pck').exists():
    sys.exit('missing pack')
if '--script' in sys.argv:
    if os.environ.get('FAKE_NO_MARKER'):
        sys.exit(0)
    if 'res://campaign_scenario.gd' in sys.argv:
        save=pathlib.Path(os.environ['XDG_DATA_HOME'])/'campaign-save-fixture'
        if '--verify-restart' in sys.argv:
            if not save.is_file():
                sys.exit('campaign save missing after process restart')
            if not os.environ.get('FAKE_NO_RESTART_MARKER'):
                print('FACTORY_CAMPAIGN_RESTART_PASS')
        else:
            save.write_text('campaign complete')
            if not os.environ.get('FAKE_NO_CAMPAIGN_MARKER'):
                print('FACTORY_CAMPAIGN_PASS')
    else:
        print('FACTORY_SCENARIO_PASS')
''') + ''')
    destination.chmod(0o755)
    destination.with_suffix('.pck').write_bytes(b'fixture package')
''')
        self.engine.chmod(0o755)
        self.env = patch.dict(os.environ, {'GODOT_BIN': str(self.engine), 'FACTORY_EXPORT_TEMPLATES': str(self.templates), 'XDG_DATA_HOME': str(self.root / 'data')})
        self.env.start()
        self.addCleanup(self.env.stop)

    def export(self):
        from ai_factory.native import export_linux
        return export_linux(self.path)

    def test_missing_templates_is_actionable_and_preserves_sources(self):
        before = core.evidence_key(self.path)
        with patch.dict(os.environ, {'FACTORY_EXPORT_TEMPLATES': str(self.root / 'absent')}):
            report = self.export()
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('4.2.2.stable', report['reason'])
        self.assertIn('linux_release.x86_64', report['reason'])
        self.assertIn('FACTORY_EXPORT_TEMPLATES', report['reason'])
        self.assertEqual(core.evidence_key(self.path), before)
        self.assertFalse((self.path / 'godot/export_presets.cfg').exists())

    def test_stale_qa_blocks_export(self):
        (self.path / 'godot/main.gd').write_text('# edited')
        report = self.export()
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('RUNTIME_CHECKED', report['reason'])
        self.assertFalse((self.path / 'dist/linux').exists())

    def test_engine_error_on_zero_exit_is_failure(self):
        with patch.dict(os.environ, {'FAKE_ERROR': '1'}):
            report = self.export()
        self.assertEqual(report['status'], 'FAILED')
        self.assertTrue(any(not c['passed'] and 'SCRIPT ERROR:' in Path(c['log']).read_text() for c in report['checks']))
        self.assertFalse((self.path / 'dist/linux').exists())

    def test_old_engine_and_mismatched_templates_are_blocked(self):
        with patch.dict(os.environ, {'FAKE_VERSION': '4.1.4.stable.official.fixture'}):
            self.assertEqual(self.export()['status'], 'BLOCKED')
        (self.templates / 'version.txt').write_text('4.3.stable')
        report = self.export()
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('version.txt', report['reason'])

    def test_success_is_relocated_and_archive_keeps_executable_and_checksums(self):
        before = core.evidence_key(self.path)
        report = self.export()
        self.assertEqual(report['status'], 'NATIVE_CHECKED', report)
        self.assertEqual(core.evidence_key(self.path), before)
        self.assertEqual(core.status(self.path)['qa'], 'RUNTIME_CHECKED')
        self.assertEqual(report['evidence'], before)
        self.assertEqual([c['name'] for c in report['checks']], ['version', 'import', 'export', 'relocated_startup', 'relocated_scenario'])
        self.assertTrue(all(c['passed'] for c in report['checks']))
        artifact = Path(report['executable'])
        self.assertTrue(artifact.stat().st_mode & stat.S_IXUSR)
        manifest = json.loads(Path(report['manifest']).read_text())
        for name, value in manifest['files'].items():
            self.assertEqual(hashlib.sha256((artifact.parent / name).read_bytes()).hexdigest(), value)
        self.assertEqual(hashlib.sha256(Path(report['archive']).read_bytes()).hexdigest(), report['archive_sha256'])
        with zipfile.ZipFile(report['archive']) as archive:
            self.assertTrue((archive.getinfo(artifact.name).external_attr >> 16) & stat.S_IXUSR)
            self.assertIn('manifest.json', archive.namelist())
        for check in report['checks']:
            self.assertFalse(Path(check['log']).is_relative_to(self.path / 'godot'))
        self.assertFalse((self.path / 'godot/export_presets.cfg').exists())

    def test_missing_scenario_marker_fails_export(self):
        with patch.dict(os.environ, {'FAKE_NO_MARKER': '1'}):
            report = self.export()
        self.assertEqual(report['status'], 'FAILED')
        self.assertEqual(report['checks'][-1]['name'], 'relocated_scenario')

    def campaign_project(self):
        self.path = self.root / 'Campaign'
        core.new(self.path, 'Campaign', 'a 3D RPG with 2 enemies and three missions')
        core.build(self.path)
        self.assertTrue(core.load(self.path)['config']['campaign'])
        core.write_json(self.path / 'qa.json', {'status': 'RUNTIME_CHECKED', 'evidence': core.evidence_key(self.path)})

    def test_campaign_is_checked_in_package_and_save_survives_new_process(self):
        self.campaign_project()
        before = core.evidence_key(self.path)
        report = self.export()
        self.assertEqual(report['status'], 'NATIVE_CHECKED', report)
        self.assertEqual([c['name'] for c in report['checks']][-2:],
                         ['relocated_campaign_scenario', 'relocated_campaign_restart'])
        campaign, restart = report['checks'][-2:]
        self.assertEqual(campaign['cwd'], restart['cwd'])
        self.assertIn('res://campaign_scenario.gd', campaign['command'])
        self.assertEqual(restart['command'][-2:], ['--', '--verify-restart'])
        self.assertIn('FACTORY_CAMPAIGN_PASS', Path(campaign['log']).read_text().splitlines())
        self.assertIn('FACTORY_CAMPAIGN_RESTART_PASS', Path(restart['log']).read_text().splitlines())
        self.assertEqual(core.evidence_key(self.path), before)

    def test_missing_campaign_or_restart_marker_never_certifies_native(self):
        self.campaign_project()
        for variable, stage in [('FAKE_NO_CAMPAIGN_MARKER', 'relocated_campaign_scenario'),
                                ('FAKE_NO_RESTART_MARKER', 'relocated_campaign_restart')]:
            with self.subTest(stage=stage), patch.dict(os.environ, {variable: '1'}):
                report = self.export()
            self.assertEqual(report['status'], 'FAILED', report)
            self.assertEqual(report['checks'][-1]['name'], stage)
            self.assertFalse((self.path / 'dist/linux').exists())

    def test_discovers_xdg_versioned_templates(self):
        import shutil
        destination = self.root / 'data/godot/export_templates/4.2.2.stable'
        shutil.copytree(self.templates, destination)
        with patch.dict(os.environ, {'FACTORY_EXPORT_TEMPLATES': ''}):
            report = self.export()
        self.assertEqual(report['status'], 'NATIVE_CHECKED', report)
        self.assertEqual(report['templates'], str(destination))

    def test_symlink_source_is_rejected_without_following_it(self):
        (self.path / 'godot/escape.txt').symlink_to(self.root / 'outside')
        report = self.export()
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertIn('symlink', report['reason'].lower())


if __name__ == '__main__':
    unittest.main()
