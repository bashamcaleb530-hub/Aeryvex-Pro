"""Local application: browser presentation, durable jobs, explicit review, artifact access."""
import base64, hmac, json, mimetypes, os, secrets, shutil, subprocess, tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from . import core
from .jobs import JobManager, ACTIVE
UI=Path(__file__).parent/'ui'

def create_server(workspace,port=8765):
    root=Path(workspace).resolve();manager=JobManager(root)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def respond(self,value,status=200,kind='application/json',filename=None):
            data=(json.dumps(value).encode() if kind=='application/json' else value)
            self.send_response(status);self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store')
            if filename:self.send_header('Content-Disposition','attachment; filename="'+filename+'"')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; object-src 'none'; base-uri 'none'")
            self.end_headers();self.wfile.write(data)
        def trusted(self):
            host=self.headers.get('Host','')
            return host in [f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}']
        def project(self,name):return core.project_path(root,name)
        def query(self):
            parsed=urlsplit(self.path)
            return parsed.path,{k:v[-1] for k,v in parse_qs(parsed.query).items()}
        def do_GET(self):
            if not self.trusted():return self.respond({'error':'Local host required'},403)
            try:
                route,q=self.query()
                if route=='/':return self.respond((UI/'index.html').read_bytes().replace(b'FACTORY_TOKEN',self.server.token.encode()),kind='text/html; charset=utf-8')
                if route in ['/app.css','/app.js']:
                    return self.respond((UI/route[1:]).read_bytes(),kind='text/css' if route.endswith('css') else 'application/javascript')
                if route=='/api/state':
                    from .genres import registry
                    projects=[]
                    for folder in sorted(root.iterdir()):
                        if folder.is_symlink() or not folder.is_dir() or not ((folder/'bible.json').is_file() or (folder/'checkpoints/0001.json').is_file()):continue
                        try:projects.append(core.status(folder))
                        except (ValueError,OSError,KeyError):continue
                    return self.respond({'projects':projects,'jobs':manager.list(),'genres':list(registry().values()),'workspace':str(root),'engine':os.environ.get('GODOT_BIN') or shutil.which('godot4') or shutil.which('godot'),'limits':['Template-based local design; arbitrary mechanics remain pending','All primitive visuals are prototypes; no photorealistic character assets included','No arbitrary AAA or 24-hour completion guarantee']})
                if route=='/api/project':
                    from .asset_review import inventory
                    p=self.project(q.get('name',''));bible=core.load(p)
                    native=json.loads((p/'native.json').read_text()) if (p/'native.json').exists() else None
                    if native and native.get('evidence')!=core.evidence_key(p):native=dict(native,status='PENDING_OR_STALE')
                    return self.respond({'bible':bible,'status':core.status(p),'checkpoints':[int(f.stem) for f in sorted((p/'checkpoints').glob('*.json'))],'assets':inventory(p)['assets'],'native':native,'qa':json.loads((p/'qa.json').read_text()) if (p/'qa.json').exists() else None,'source_download':(p/'dist'/(bible['name']+'.zip')).exists() and core.status(p)['qa']=='RUNTIME_CHECKED'})
                if route=='/api/job':return self.respond({'job':manager.get(q.get('id','')),'log':manager.log(q.get('id',''))})
                if route=='/download':
                    p=self.project(q.get('project',''))
                    if core.status(p)['qa']!='RUNTIME_CHECKED':raise ValueError('Artifact QA missing or stale; rebuild first')
                    if q.get('kind')=='source':
                        artifact=p/'dist'/(core.load(p)['name']+'.zip')
                        manifest=json.loads((p/'dist/manifest.json').read_text())
                        if manifest['sha256']!=core.digest(artifact) or manifest['revision']!=core.load(p)['revision'] or manifest['files']!=core.managed_files(p):raise ValueError('Source artifact checksum or revision failed; test and package again')
                    elif q.get('kind')=='native':
                        report=json.loads((p/'native.json').read_text())
                        if report['status']!='NATIVE_CHECKED' or report['evidence']!=core.evidence_key(p):raise ValueError('Native artifact is not current')
                        artifact=Path(report['archive'])
                        if core.digest(artifact)!=report['archive_sha256']:raise ValueError('Native artifact checksum failed')
                    else:raise ValueError('Unknown artifact')
                    artifact=artifact.resolve()
                    if p/'dist' not in artifact.parents:raise ValueError('Invalid artifact location')
                    return self.respond(artifact.read_bytes(),kind='application/zip',filename=artifact.name)
                return self.respond({'error':'Not found'},404)
            except (ValueError,OSError,KeyError,json.JSONDecodeError) as e:self.respond({'error':str(e)},400)
        def do_POST(self):
            if not self.trusted() or not hmac.compare_digest(self.headers.get('X-Factory-Token',''),self.server.token):return self.respond({'error':'Local session token required'},403)
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=24*1024*1024:raise ValueError('Request must be 1 byte to 24 MB')
                data=json.loads(self.rfile.read(size));route,_=self.query()
                if not isinstance(data,dict):raise ValueError('JSON object required')
                if route=='/api/jobs':
                    allowed={'name','prompt','action','native','budget_seconds','revision','provider'}
                    if set(data)-allowed:raise ValueError('Unknown job fields')
                    return self.respond(manager.submit(**data),202)
                if route=='/api/cancel':return self.respond(manager.cancel(data['id']))
                if route=='/api/resume':return self.respond(manager.resume(data['id']),202)
                if route=='/api/play':
                    p=self.project(data['name'])
                    if any(j['name']==data['name'] and j['status'] in ACTIVE for j in manager.list()):raise ValueError('Wait for the active job')
                    if core.status(p)['qa']!='RUNTIME_CHECKED':raise ValueError('Run current QA before launching')
                    engine=os.environ.get('GODOT_BIN') or shutil.which('godot4') or shutil.which('godot')
                    if not engine:raise ValueError('Godot unavailable')
                    if not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):raise ValueError('Launch requires your laptop desktop session; download the native build to play')
                    log=p/'.play.log'
                    with log.open('ab') as handle:subprocess.Popen([engine,'--path',str(p/'godot')],stdout=handle,stderr=subprocess.STDOUT,start_new_session=True)
                    return self.respond({'status':'LAUNCHED','log':str(log)})
                if route in ['/api/asset-inspect','/api/asset-stage']:
                    from . import asset_review
                    metadata=data.get('metadata',{});blob=base64.b64decode(data['data'],validate=True)
                    if len(blob)>16*1024*1024:raise ValueError('Local browser intake limit is 16 MB; CLI accepts larger files')
                    p=self.project(data['name']);core.load(p)
                    if any(j['name']==data['name'] and j['status'] in ACTIVE for j in manager.list()):raise ValueError('Wait for the active job')
                    with tempfile.NamedTemporaryFile(suffix='.glb') as handle:
                        handle.write(blob);handle.flush()
                        result=asset_review.inspect(handle.name,metadata) if route=='/api/asset-inspect' else asset_review.stage(p,handle.name,metadata,character=data.get('character'))
                    return self.respond(result)
                if route=='/api/meshy-submit':
                    from .meshy_bridge import submit
                    if not os.environ.get('MESHY_API_KEY'):raise ValueError('Set MESHY_API_KEY in the factory process environment first')
                    encoded=data.get('image')
                    if not isinstance(encoded,str) or len(encoded)>12*1024*1024:raise ValueError('Image payload missing or too large')
                    blob=base64.b64decode(encoded,validate=True)
                    if not 0<len(blob)<=8*1024*1024:raise ValueError('Reference image exceeds 8 MiB browser limit')
                    ext=data.get('extension')
                    if ext not in ['.png','.jpg','.jpeg','.webp']:raise ValueError('Unsupported reference image type')
                    with tempfile.TemporaryDirectory(prefix='aeryvex-meshy-') as temp:
                        image=Path(temp)/('reference'+ext)
                        image.write_bytes(blob)
                        return self.respond(submit(image),202)
                if route=='/api/meshy-status':
                    from .meshy_bridge import status
                    return self.respond(status(data.get('task_id')))
                if route=='/api/meshy-download':
                    from .meshy_bridge import download
                    import re
                    task_id=data.get('task_id')
                    if not isinstance(task_id,str) or not re.fullmatch('[A-Za-z0-9-]{1,100}',task_id):raise ValueError('Invalid task ID')
                    candidate_dir=root/'.factory-candidates'
                    candidate_dir.mkdir(parents=True,exist_ok=True)
                    destination=candidate_dir/(task_id+'.glb')
                    result=download(task_id,destination)
                    return self.respond(result)
                if route=='/api/meshy-verify':
                    from .godot_candidate_check import check_candidate
                    import re
                    task_id=data.get('task_id')
                    if not isinstance(task_id,str) or not re.fullmatch('[A-Za-z0-9-]{1,100}',task_id):raise ValueError('Invalid task ID')
                    destination=root/'.factory-candidates'/(task_id+'.glb')
                    if destination.is_symlink() or not destination.is_file():raise ValueError('Download candidate first')
                    return self.respond(check_candidate(destination))
                if route=='/api/asset-review':
                    from .asset_review import review
                    p=self.project(data['name'])
                    if any(j['name']==data['name'] and j['status'] in ACTIVE for j in manager.list()):raise ValueError('Wait for the active job')
                    return self.respond(review(p,data['sha256'],license_approved=data.get('license_approved'),visual_approved=data.get('visual_approved'),prototype_approved=data.get('prototype_approved')))
                return self.respond({'error':'Not found'},404)
            except (ValueError,TypeError,OSError,KeyError,json.JSONDecodeError) as e:self.respond({'error':str(e)},400)
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler);server.token=secrets.token_urlsafe(32);server.manager=manager
    return server

def serve(workspace,port=8765):
    server=create_server(workspace,port)
    print(f'Aeryvex AI Game Factory: http://127.0.0.1:{server.server_port}',flush=True)
    print('Local application. Projects are stored in '+str(Path(workspace).resolve()),flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
