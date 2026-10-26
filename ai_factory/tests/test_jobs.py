import json, tempfile, time, unittest
from pathlib import Path
from ai_factory import core

class JobTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
    def manager(self):
        from ai_factory.jobs import JobManager
        return JobManager(self.root)
    def test_budget_rejected_before_creating_project(self):
        self.assertTrue((Path(core.__file__).parent/'jobs.py').exists(),'persistent jobs missing')
        m=self.manager()
        for n in [0,86401,True]:
            with self.assertRaises(ValueError):m.submit('Demo','5 coins',budget_seconds=n)
        self.assertFalse((self.root/'Demo').exists())
    def test_cancelled_job_never_claims_completion_and_can_resume(self):
        self.assertTrue((Path(core.__file__).parent/'jobs.py').exists(),'persistent jobs missing')
        m=self.manager();job=m.submit('Demo','5 coins',autostart=False)
        m.cancel(job['id']);self.assertEqual(m.get(job['id'])['status'],'CANCELLED')
        m2=self.manager();self.assertEqual(m2.get(job['id'])['prompt'],'5 coins')
        resumed=m2.resume(job['id'],autostart=False)
        self.assertEqual(resumed['status'],'QUEUED')
        self.assertEqual(resumed['id'],job['id'])
    def test_existing_project_cannot_be_recreated(self):
        self.assertTrue((Path(core.__file__).parent/'jobs.py').exists(),'persistent jobs missing')
        core.new(self.root/'Demo','Demo','coins');m=self.manager()
        with self.assertRaises(ValueError):m.submit('Demo','replace')
        job=m.submit('Demo','3 enemies',action='revise',autostart=False)
        with self.assertRaises(ValueError):m.submit('Demo','4 enemies',action='revise',autostart=False)
        self.assertEqual(job['action'],'revise')
    def test_restart_marks_missing_worker_interrupted(self):
        self.assertTrue((Path(core.__file__).parent/'jobs.py').exists(),'persistent jobs missing')
        m=self.manager();j=m.submit('Demo','coins',autostart=False)
        p=self.root/'.factory-jobs'/j['id']/'job.json'
        j.update(status='RUNNING',pid=999999999);core.write_json(p,j)
        self.assertEqual(self.manager().get(j['id'])['status'],'INTERRUPTED')
    def test_worker_runs_real_generation_build_and_reports_missing_engine(self):
        self.assertTrue((Path(core.__file__).parent/'jobs.py').exists(),'persistent jobs missing')
        import os
        from unittest.mock import patch
        with patch.dict(os.environ,{'GODOT_BIN':'/missing/godot'}):
            m=self.manager();j=m.submit('Demo','5 coins',native=False)
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            j=m.get(j['id'])
            if j['status'] not in ['RUNNING','QUEUED']:break
            time.sleep(.05)
        self.assertEqual(j['status'],'BLOCKED',j)
        self.assertTrue((self.root/'Demo/godot/project.godot').exists())
        self.assertIn('build',j['completed'])
        self.assertNotIn('qa',j['completed'])
        self.assertIn('Godot',j['error'])
        self.assertIn('design',m.log(j['id']))
    def test_resume_reconciles_committed_design_without_repeating_prompt(self):
        m=self.manager();j=m.submit('Demo','5 coins',autostart=False)
        core.new(self.root/'Demo','Demo','5 coins')
        p=m.location(j['id']);j.update(status='INTERRUPTED',stage='design');core.write_json(p,j)
        resumed=m.resume(j['id'],autostart=False)
        self.assertIn('design',resumed['completed'])
    def test_resume_rejects_conflicting_later_revision(self):
        core.new(self.root/'Demo','Demo','5 coins')
        m=self.manager();j=m.submit('Demo','3 enemies',action='revise',autostart=False)
        core.add(self.root/'Demo','7 coins')
        j.update(status='INTERRUPTED');core.write_json(m.location(j['id']),j)
        with self.assertRaises(ValueError):m.resume(j['id'],autostart=False)
    def test_old_orphaned_queue_can_resume(self):
        m=self.manager();j=m.submit('Demo','coins',autostart=False)
        j['created']=time.time()-60;core.write_json(m.location(j['id']),j)
        self.assertEqual(self.manager().get(j['id'])['status'],'INTERRUPTED')
        self.assertEqual(self.manager().resume(j['id'],autostart=False)['status'],'QUEUED')
    def test_cancel_is_monotonic_even_if_worker_writes_late_completion(self):
        m=self.manager();j=m.submit('Demo','coins',autostart=False)
        m.cancel(j['id'])
        j.update(status='COMPLETED');core.write_json(m.location(j['id']),j)
        self.assertEqual(m.get(j['id'])['status'],'CANCELLED')
    def test_resume_does_not_replay_committed_rollback(self):
        core.new(self.root/'Demo','Demo','5 coins');core.add(self.root/'Demo','3 enemies')
        m=self.manager();j=m.submit('Demo',action='rollback',revision=1,autostart=False)
        core.rollback(self.root/'Demo',1)
        j.update(status='INTERRUPTED',stage='design');core.write_json(m.location(j['id']),j)
        self.assertIn('design',m.resume(j['id'],autostart=False)['completed'])
