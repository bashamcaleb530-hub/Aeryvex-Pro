import json, tempfile, unittest
from pathlib import Path
from ai_factory import core
from ai_factory.providers import TemplateProvider,validate
from ai_factory.cli import main

class FactoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'Demo'
    def test_revision_preserves_requirements_and_locks(self):
        a=core.new(self.path,'Demo','collect 5 coins in a magic city')
        a['approved_appearance_references']={'Orion':'approved hash'};core.write_json(self.path/'bible.json',a)
        b=core.add(self.path,'add 3 enemies and make player faster and blue')
        self.assertEqual(b['config'],{'coins':5,'enemies':3,'speed':260,'color':'blue'})
        self.assertEqual(len(b['requirements']),2);self.assertEqual(b['approved_appearance_references'],a['approved_appearance_references'])
        self.assertTrue((self.path/'checkpoints/0001.json').exists())
    def test_managed_user_edit_is_preserved(self):
        core.new(self.path,'Demo','collect coins');core.build(self.path)
        p=self.path/'godot/main.gd';p.write_text('user source')
        with self.assertRaises(ValueError):core.build(self.path)
        self.assertEqual(p.read_text(),'user source')
    def test_stale_evidence(self):
        core.new(self.path,'Demo','5 coins');core.build(self.path)
        core.write_json(self.path/'qa.json',{'status':'RUNTIME_CHECKED','evidence':core.evidence_key(self.path)})
        self.assertEqual(core.status(self.path)['qa'],'RUNTIME_CHECKED')
        core.add(self.path,'3 enemies');self.assertEqual(core.status(self.path)['qa'],'PENDING_OR_STALE')
        with self.assertRaises(ValueError):core.test(self.path)
    def test_invalid_proposal_does_not_change_state(self):
        core.new(self.path,'Demo','coins');before=(self.path/'bible.json').read_bytes()
        with self.assertRaises(ValueError):core.add(self.path,'999 enemies')
        self.assertEqual(before,(self.path/'bible.json').read_bytes())
    def test_validation_and_paths(self):
        for n in ['../original_game','/tmp/game','a/b','x;rm']:
            with self.assertRaises(ValueError):core.project_path(Path(self.tmp.name),n)
        with self.assertRaises(ValueError):validate({'coins':True,'enemies':0,'speed':220,'color':'blue'})
    def test_new_never_replaces(self):
        core.new(self.path,'Demo','coins')
        with self.assertRaises(ValueError):core.new(self.path,'Demo','replace')
    def test_plan_is_dependency_ordered(self):
        core.new(self.path,'Demo','coins');done=set()
        for task in core.plan(self.path)['tasks']:
            self.assertTrue(set(task['depends_on'])<=done);done.add(task['id'])
    def test_checkpoint_resumes_after_copy(self):
        import shutil
        core.new(self.path,'Demo','7 coins');copy=Path(self.tmp.name)/'Restored';shutil.copytree(self.path,copy)
        core.add(copy,'2 enemies');core.build(copy)
        self.assertEqual(core.load(copy)['config']['coins'],7)
    def test_zero_exit_engine_error_and_missing_marker_fail(self):
        import subprocess
        from unittest.mock import patch
        core.new(self.path,'Demo','coins');core.build(self.path)
        for outputs in [['4.2.2.stable\n','ERROR: broken script'],['4.2.2.stable\n','','','']]:
            results=[subprocess.CompletedProcess([],0,out,'') for out in outputs]
            with patch.dict('os.environ',{'GODOT_BIN':'fake-godot'}),patch('ai_factory.core.subprocess.run',side_effect=results):
                with self.assertRaises(ValueError):core.test(self.path)
            self.assertEqual(json.loads((self.path/'qa.json').read_text())['status'],'FAILED')
