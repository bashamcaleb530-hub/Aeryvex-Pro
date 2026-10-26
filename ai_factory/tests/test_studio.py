"""Candidate intake must preserve references and require explicit human review."""
import json
import unittest
import urllib.error
from pathlib import Path
import test_app
from asset_fixtures import write_rigged_fixture
from ai_factory import core

class StudioTests(unittest.TestCase):
    request=test_app.AppTests.request
    close=test_app.AppTests.close
    def setUp(self):
        test_app.AppTests.setUp(self)
        self.project_path=Path(self.tmp.name)/'Demo'
        core.new(self.project_path,'Demo','3D RPG')
        bible=core.load(self.project_path)
        bible['approved_appearance_references']={'Orion':'a'*64}
        core.write_json(self.project_path/'bible.json',bible)
        self.candidate=write_rigged_fixture(Path(self.tmp.name)/'.factory-candidates/task-1.glb')
        self.payload={'name':'Demo','task_id':'task-1','character':'Orion','metadata':{
            'approved':True,'author':'Synthetic test','source':'Test fixture','license':'CC0',
            'reference_sha256':'a'*64,'animation_mapping':{'idle':'idle'}}}

    def test_stage_downloaded_candidate_keeps_visual_review_pending(self):
        with self.request('/api/meshy-stage',self.payload) as response:
            result=json.load(response)
        self.assertEqual(result['revision'],2)
        row=result['assets'][0]
        self.assertEqual(row['character'],'Orion')
        self.assertEqual(row['visual_review'],'PENDING')
        self.assertEqual(row['animation_mapping'],{'idle':'idle'})
        self.assertEqual(result['approved_appearance_references'],{'Orion':'a'*64})
        self.assertEqual((self.project_path/row['file']).read_bytes(),self.candidate.read_bytes())
        with self.request('/candidate?task_id=task-1') as response:
            self.assertEqual(response.read(),self.candidate.read_bytes())
        with self.request('/api/asset-review',{'name':'Demo','sha256':row['sha256'],'visual_approved':True}) as response:
            self.assertEqual(json.load(response)['assets'][0]['visual_review'],'APPROVED')

    def test_intake_refuses_reference_mismatch_without_revision(self):
        self.payload['metadata']['reference_sha256']='b'*64
        with self.assertRaises(urllib.error.HTTPError) as error:self.request('/api/meshy-stage',self.payload)
        self.assertEqual(error.exception.code,400)
        self.assertEqual(core.load(self.project_path)['revision'],1)

    def test_candidate_paths_and_symlinks_are_rejected(self):
        self.candidate.unlink();self.candidate.symlink_to('/etc/hosts')
        for task in ['task-1','../../etc/hosts']:
            with self.assertRaises(urllib.error.HTTPError) as error:self.request('/candidate?task_id='+task)
            self.assertEqual(error.exception.code,400)
