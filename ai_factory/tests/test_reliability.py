import json, tempfile, unittest
from pathlib import Path
from ai_factory import core

class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'Demo'
        core.new(self.path,'Demo','5 coins')
    def test_rollback_is_a_new_revision_preserving_audit_and_locks(self):
        core.add(self.path,'3 enemies')
        before=(self.path/'checkpoints/0001.json').read_bytes()
        bible=core.load(self.path);bible['approved_appearance_references']={'Orion':'locked'}
        core.write_json(self.path/'bible.json',bible)
        self.assertTrue(hasattr(core,'rollback'),'rollback API missing')
        restored=core.rollback(self.path,1)
        self.assertEqual(restored['revision'],3)
        self.assertEqual(restored['config']['enemies'],0)
        self.assertEqual(restored['approved_appearance_references'],{'Orion':'locked'})
        self.assertEqual(len(restored['requirements']),3)
        self.assertEqual((self.path/'checkpoints/0001.json').read_bytes(),before)
        self.assertEqual(restored['history'][-1]['restored_from'],1)
    def test_no_op_revision_explains_actual_change(self):
        b=core.add(self.path,'make a fully photorealistic open world MMO')
        self.assertEqual(b['requirements'][-1]['resolution'],'NO_SUPPORTED_CHANGE')
        self.assertEqual(b['history'][-1]['changes'],{})
    def test_empty_prompt_is_rejected(self):
        with self.assertRaises(ValueError):core.add(self.path,'   ')
        self.assertEqual(core.load(self.path)['revision'],1)
    def test_generated_symlink_is_rejected_without_reading_target(self):
        core.build(self.path)
        (self.path/'godot/link.gd').symlink_to('/etc/hostname')
        with self.assertRaises(ValueError):core.managed_files(self.path)
    def test_qa_cannot_certify_source_changed_during_execution(self):
        import subprocess
        from unittest.mock import patch
        core.build(self.path)
        count=0
        def run(cmd,**kwargs):
            nonlocal count
            count+=1
            if count==4:
                (self.path/'godot/main.gd').write_text('# changed during QA')
            return subprocess.CompletedProcess(cmd,0,'4.2.2.stable\n' if count==1 else ('FACTORY_SCENARIO_PASS\n' if count==4 else ''),'')
        with patch.dict('os.environ',{'GODOT_BIN':'fake'}),patch('ai_factory.core.subprocess.run',side_effect=run):
            with self.assertRaises(ValueError):core.test(self.path)
        self.assertNotEqual(core.status(self.path)['qa'],'RUNTIME_CHECKED')
    def test_checkpoint_before_bible_crash_is_recoverable_without_deletion(self):
        from unittest.mock import patch
        original=core.write_json
        def fail_bible(path,value):
            if Path(path).name=='bible.json':raise OSError('simulated interruption')
            return original(path,value)
        with patch('ai_factory.core.write_json',side_effect=fail_bible):
            with self.assertRaises(OSError):core.add(self.path,'3 enemies')
        recovered=core.load(self.path)
        self.assertEqual(recovered['revision'],2)
        self.assertEqual(recovered['config']['enemies'],3)
        self.assertEqual(core.add(self.path,'7 coins')['revision'],3)
        self.assertTrue((self.path/'checkpoints/0002.json').exists())
    def test_initial_checkpoint_crash_remains_discoverable(self):
        from unittest.mock import patch
        other=Path(self.tmp.name)/'New';original=core.write_json
        def fail_bible(path,value):
            if Path(path).name=='bible.json':raise OSError('simulated interruption')
            return original(path,value)
        with patch('ai_factory.core.write_json',side_effect=fail_bible):
            with self.assertRaises(OSError):core.new(other,'New','coins')
        self.assertEqual(core.load(other)['revision'],1)
    def test_same_revision_bible_edit_requires_rebuild(self):
        core.build(self.path);b=core.load(self.path);b['config']['coins']=17;core.write_json(self.path/'bible.json',b)
        with self.assertRaisesRegex(ValueError,'build first'):core.test(self.path)
