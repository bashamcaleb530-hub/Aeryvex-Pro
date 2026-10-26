import json, tempfile, threading, unittest, urllib.request, urllib.error
from pathlib import Path
from ai_factory import core
class AppTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((Path(core.__file__).parent/'app.py').exists(),'local application missing')
        from ai_factory.app import create_server
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.server=create_server(Path(self.tmp.name),0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.close);self.url='http://127.0.0.1:'+str(self.server.server_port)
    def close(self):
        self.server.shutdown();self.server.server_close();self.thread.join()
    def request(self,path,data=None,token=True,host=None):
        headers={'Content-Type':'application/json'}
        if token:headers['X-Factory-Token']=self.server.token
        if host:headers['Host']=host
        req=urllib.request.Request(self.url+path,headers=headers,data=json.dumps(data).encode() if data is not None else None)
        return urllib.request.urlopen(req)
    def test_ui_and_state_are_real_routes(self):
        with self.request('/') as r:self.assertIn(b'Aeryvex',r.read())
        with self.request('/api/state') as r:
            data=json.load(r);self.assertEqual(data['projects'],[]);self.assertEqual(data['jobs'],[])
    def test_csrf_and_host_rejection(self):
        for args in [('/api/jobs',{},False,None),('/api/state',None,True,'evil.example')]:
            with self.assertRaises(urllib.error.HTTPError) as caught:self.request(*args)
            self.assertEqual(caught.exception.code,403)
    def test_artifact_traversal_blocked(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:self.request('/download?project=../../etc&kind=source')
        self.assertEqual(caught.exception.code,400)
    def test_revision_job_preserves_existing_project(self):
        p=Path(self.tmp.name)/'Demo';core.new(p,'Demo','5 coins');before=(p/'bible.json').read_bytes()
        with self.assertRaises(urllib.error.HTTPError):self.request('/api/jobs',{'name':'Demo','prompt':'overwrite'})
        self.assertEqual((p/'bible.json').read_bytes(),before)
        with self.request('/api/project?name=Demo') as r:
            value=json.load(r);self.assertEqual(value['bible']['revision'],1)
            self.assertIsInstance(value['assets'],list,'UI needs a renderable asset list')
    def test_source_download_rejects_corrupt_archive(self):
        p=Path(self.tmp.name)/'Demo';core.new(p,'Demo','coins');core.build(p)
        core.write_json(p/'qa.json',{'status':'RUNTIME_CHECKED','evidence':core.evidence_key(p)})
        (p/'dist').mkdir();artifact=p/'dist/Demo.zip';artifact.write_bytes(b'original archive')
        core.write_json(p/'dist/manifest.json',{'sha256':core.digest(artifact),'files':core.managed_files(p),'revision':1})
        artifact.write_bytes(b'corrupted archive')
        with self.assertRaises(urllib.error.HTTPError) as caught:self.request('/download?project=Demo&kind=source')
        self.assertEqual(caught.exception.code,400)
    def test_character_studio_routes_lock_reference_and_serve_only_project_images(self):
        import base64
        from test_character_studio import png
        p=Path(self.tmp.name)/'Hero';core.new(p,'Hero','A 3D RPG with a town')
        image=png()
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.request('/api/character-lock',{'name':'Hero','character':'Orion','image':base64.b64encode(image).decode(),'extension':'.png','confirmed':False})
        self.assertEqual(caught.exception.code,400)
        with self.request('/api/character-lock',{'name':'Hero','character':'Orion','image':base64.b64encode(image).decode(),'extension':'.png','confirmed':True}) as r:
            locked=json.load(r);self.assertEqual(locked['status'],'LOCKED')
        with self.request('/api/characters?name=Hero') as r:
            data=json.load(r);character=data['characters'][0]
            self.assertEqual((character['name'],character['steps']['reference']['status']),('Orion','LOCKED'))
            self.assertIn(data['display'],['AVAILABLE','UNAVAILABLE'])
        with self.request('/api/character-file?project=Hero&path='+character['reference']['file']) as r:
            self.assertEqual((r.headers['Content-Type'],r.read()),('image/png',image))
        for path in ['bible.json','../../etc/passwd','references/../bible.json']:
            with self.assertRaises(urllib.error.HTTPError) as caught:self.request('/api/character-file?project=Hero&path='+path)
            self.assertEqual(caught.exception.code,400)
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.request('/api/character-meshy',{'name':'Hero','character':'Orion','action':'generate','authorize_paid':False})
        self.assertEqual(caught.exception.code,400)
