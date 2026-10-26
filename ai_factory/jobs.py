"""Durable bounded pipeline supervisor. No shell commands or generated executable code."""
import argparse, fcntl, json, os, re, signal, subprocess, sys, threading, time, uuid
from pathlib import Path
from . import core
ACTIVE={'QUEUED','RUNNING'}
TERMINAL={'COMPLETED','BLOCKED','FAILED','CANCELLED','INTERRUPTED','BUDGET_EXCEEDED'}
REPO=Path(__file__).resolve().parents[1]

def alive(job,filename):
    try:
        return str(filename).encode() in Path('/proc',str(job['pid']),'cmdline').read_bytes().split(b'\0')
    except (OSError,KeyError):return False

class JobManager:
    def __init__(self,workspace):
        self.root=Path(workspace).resolve();self.store=self.root/'.factory-jobs'
        self.store.mkdir(parents=True,exist_ok=True);self.lock=threading.RLock();self.processes={}
    def location(self,jid):
        if not isinstance(jid,str) or not re.fullmatch('[0-9a-f]{32}',jid):raise ValueError('Invalid job ID')
        path=self.store/jid/'job.json'
        if path.is_symlink() or path.parent.is_symlink():raise ValueError('Symlink job forbidden')
        return path
    def get(self,jid):
        path=self.location(jid);job=json.loads(path.read_text())
        if (path.parent/'cancel.requested').exists():
            job.update(status='CANCELLED',error='Cancelled by user; completed stages retained')
            return job
        process=self.processes.get(jid)
        if process and process.poll() is not None:self.processes.pop(jid,None)
        orphaned_queue=job['status']=='QUEUED' and time.time()-job.get('queued_at',job['created'])>5 and not (process and process.poll() is None)
        if (job['status']=='RUNNING' and not alive(job,path)) or orphaned_queue:
            job.update(status='INTERRUPTED',error='Worker stopped; resume to continue from the last recorded stage')
            core.write_json(path,job)
        return job
    def list(self):
        return sorted([self.get(p.parent.name) for p in self.store.glob('*/job.json')],key=lambda j:j['created'],reverse=True)
    def log(self,jid):
        self.location(jid)
        path=self.store/jid/'pipeline.log'
        if not path.exists():return ''
        with path.open('rb') as stream:
            stream.seek(max(0,path.stat().st_size-70000));output=stream.read().decode('utf-8','replace')
        job=self.get(jid)
        current=self.store/jid/(job['stage']+'.log')
        if job['status']=='RUNNING' and current.is_file():
            with current.open('rb') as stream:
                stream.seek(max(0,current.stat().st_size-30000));output+='\n'+stream.read().decode('utf-8','replace')
        return output
    def submit(self,name,prompt='',action='new',budget_seconds=7200,native=True,revision=None,autostart=True,provider='template'):
        if action not in ['new','revise','rebuild','rollback']:raise ValueError('Unknown action')
        if type(budget_seconds) is not int or not 1<=budget_seconds<=86400:raise ValueError('Budget must be 1..86400 seconds')
        if type(native) is not bool:raise ValueError('Native option must be boolean')
        if provider not in ['template','ollama']:raise ValueError('Unknown provider')
        project=core.project_path(self.root,name)
        if action in ['new','revise']:prompt=core.validate_prompt(prompt)
        if action=='new' and project.exists():raise ValueError('Project exists; revise it instead')
        if action!='new' and not (project/'bible.json').is_file():raise ValueError('Project does not exist')
        if action=='rollback' and (type(revision) is not int or not (project/'checkpoints'/f'{revision:04d}.json').is_file()):raise ValueError('Checkpoint does not exist')
        with self.lock:
            if any(j['name']==name and j['status'] in ACTIVE for j in self.list()):raise ValueError('Project has an active job')
            jid=uuid.uuid4().hex
            initial_revision=0 if action=='new' else core.load(project)['revision']
            job={'id':jid,'name':name,'action':action,'provider':provider,'prompt':prompt,'restore_revision':revision,'initial_revision':initial_revision,'initial_bible_sha256':None if action=='new' else core.digest(project/'bible.json'),'workspace':str(self.root),'native':native,'budget_seconds':budget_seconds,'elapsed_seconds':0,'created':time.time(),'status':'QUEUED','completed':[],'stage':'queued','error':'','repairs':[],'scope':'Small playable template slice; unsupported requirements stay pending. Budget is a limit, not a completion guarantee.'}
            core.write_json(self.location(jid),job)
            if autostart:self._start(job)
            return job
    def _start(self,job):
        filename=self.location(job['id'])
        with (filename.parent/'pipeline.log').open('ab') as log:
            child=subprocess.Popen([sys.executable,'-m','ai_factory.jobs','--run',str(filename)],cwd=REPO,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        self.processes[job['id']]=child
        threading.Thread(target=child.wait,daemon=True).start()
    def cancel(self,jid):
        with self.lock:
            job=self.get(jid)
            if job['status'] not in ACTIVE:return job
            # Write cancellation before killing; worker never overwrites this state.
            (self.location(jid).parent/'cancel.requested').touch()
            job.update(status='CANCELLED',error='Cancelled by user; completed stages retained')
            core.write_json(self.location(jid),job)
            if alive(job,self.location(jid)):
                try:os.killpg(job['pid'],signal.SIGTERM)
                except ProcessLookupError:pass
            process=self.processes.get(jid)
            if process:
                try:process.wait(timeout=5)
                except subprocess.TimeoutExpired:pass
            return job
    def resume(self,jid,autostart=True):
        with self.lock:
            job=self.get(jid)
            if job['status'] in ACTIVE:raise ValueError('Job already active')
            if job['status']=='COMPLETED':raise ValueError('Completed job; start a revision or rebuild')
            if alive(job,self.location(jid)):raise ValueError('Worker is still stopping; resume in a moment')
            if any(j['id']!=jid and j['name']==job['name'] and j['status'] in ACTIVE for j in self.list()):raise ValueError('Project has an active job')
            project=core.project_path(self.root,job['name'])
            if not (project/'bible.json').exists() and (project/'checkpoints/0001.json').exists():core.load(project)
            if (project/'bible.json').exists():
                bible=core.load(project)
                if 'design' not in job['completed'] and job['action'] in ['new','revise','rollback']:
                    # Crash after a committed revision but before recording stage completion.
                    matches=(bible['history'][-1].get('restored_from')==job['restore_revision']) if job['action']=='rollback' else bible['history'][-1]['prompt']==job['prompt']
                    if bible['revision']==job['initial_revision']+1 and matches:
                        job['completed'].append('design')
                        job['design_evidence']=core.digest(project/'bible.json')
                    elif job['action']=='new' or core.digest(project/'bible.json')!=job['initial_bible_sha256']:
                        raise ValueError('Project changed outside this job; start a new rebuild or revision')
                elif job.get('design_evidence') and core.digest(project/'bible.json')!=job['design_evidence']:
                    raise ValueError('Project changed outside this job; start a new rebuild or revision')
            (self.location(jid).parent/'cancel.requested').unlink(missing_ok=True)
            job.update(status='QUEUED',error='',queued_at=time.time())
            # Completed design/build are durable. QA/native are rechecked after any interruption.
            job['completed']=[s for s in job['completed'] if s not in ['qa','native']]
            job['elapsed_seconds']=0
            core.write_json(self.location(jid),job)
            if autostart:self._start(job)
            return job

def run(filename):
    filename=Path(filename).resolve();job=json.loads(filename.read_text())
    if job['status']!='QUEUED':return
    root=Path(job['workspace']);project=core.project_path(root,job['name'])
    lockfile=root/'.factory-jobs'/(job['name']+'.lock')
    with lockfile.open('a') as guard:
        try:fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            job.update(status='FAILED',error='Another worker is modifying this project');core.write_json(filename,job);return
        started=time.monotonic();prior=job['elapsed_seconds']
        child=None
        def terminate(_signal=None,_frame=None):
            if child is not None and child.poll() is None:
                try:os.killpg(child.pid,signal.SIGTERM)
                except ProcessLookupError:pass
                child.wait(timeout=5)
            if _signal is not None:raise SystemExit(0)
        signal.signal(signal.SIGTERM,terminate)
        job.update(status='RUNNING',pid=os.getpid(),started=time.time())
        def update(**values):
            latest=json.loads(filename.read_text())
            if latest['status']=='CANCELLED' or (filename.parent/'cancel.requested').exists():return False
            job.update(values,elapsed_seconds=round(prior+time.monotonic()-started,2));core.write_json(filename,job);return True
        update()
        base=[sys.executable,'-m','ai_factory','--workspace',str(root)]
        action=job['action'];name=job['name']
        commands=[]
        if action in ['new','revise']:
            commands.append(('design',base+(['new','--name',name] if action=='new' else ['add','--project',name])+['--prompt',job['prompt'],'--provider',job.get('provider','template')]))
        elif action=='rollback':commands.append(('design',base+['rollback','--project',name,'--revision',str(job['restore_revision'])]))
        commands.extend([('build',base+['build','--project',name]),('qa',base+['test','--project',name])])
        if job['native']:commands.append(('native',base+['export','--project',name]))
        try:
            for stage,command in commands:
                if stage in job['completed']:continue
                if not update(stage=stage):return
                print('\n=== '+stage+' ===',flush=True)
                output=filename.parent/(stage+'.log')
                with output.open('w') as handle:
                    child=subprocess.Popen(command,cwd=REPO,stdout=handle,stderr=subprocess.STDOUT,start_new_session=True)
                    while child.poll() is None:
                        if json.loads(filename.read_text())['status']=='CANCELLED':
                            terminate();return
                        if prior+time.monotonic()-started>job['budget_seconds']:
                            terminate()
                            update(status='BUDGET_EXCEEDED',error='Compute/time budget reached; resume with a fresh budget to continue');return
                        time.sleep(.1)
                text=output.read_text();print(text,flush=True)
                try:result=json.loads(text)
                except json.JSONDecodeError:result={'status':'FAILED','error':text[-3000:]}
                if child.returncode or result.get('status') in ['FAILED','BLOCKED']:
                    error=str(result.get('reason') or result.get('error') or 'Stage failed; inspect logs')
                    # One safe repair: rerun Godot import+QA in fresh cache after import failure.
                    # Never rewrite generated or approved source to conceal failures.
                    if stage=='qa' and not job['repairs'] and (project/'qa.json').exists():
                        qa=json.loads((project/'qa.json').read_text())
                        failed=next((c for c in qa.get('checks',[]) if not c['passed']),{})
                        if failed.get('name')=='import':
                            import shutil
                            cache=project/'godot/.godot'
                            if cache.exists():shutil.rmtree(cache)
                            job['repairs'].append({'action':'Reimport generated cache','reason':failed['log'][-1000:]})
                            # Recurse is avoided: immediate bounded retry uses same budget.
                            retry=subprocess.run(command,cwd=REPO,capture_output=True,text=True,timeout=max(1,job['budget_seconds']-(time.monotonic()-started)))
                            print('SAFE IMPORT RETRY\n'+retry.stdout+retry.stderr,flush=True)
                            if retry.returncode==0:
                                job['completed'].append(stage);update();continue
                    runner_missing=False
                    if stage=='qa' and (project/'qa.json').exists():
                        qa=json.loads((project/'qa.json').read_text())
                        runner_missing=any(c.get('name')=='runner' and 'No such file' in c.get('log','') for c in qa.get('checks',[]))
                    blocked=('BLOCKED' in error or runner_missing or 'Godot' in error and not (project/'qa.json').exists() or result.get('status')=='BLOCKED')
                    update(status='BLOCKED' if blocked else 'FAILED',error=error);return
                job['completed'].append(stage)
                if stage=='design':job['design_evidence']=core.digest(project/'bible.json')
                if not update():return
            update(status='COMPLETED',stage='complete',finished=time.time(),error='')
        except Exception as error:
            update(status='FAILED',error=str(error))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True)
    run(parser.parse_args().run)
