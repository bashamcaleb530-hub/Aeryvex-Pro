"""Persistent project state, deterministic compilation and evidence-bound QA."""
import copy, datetime, hashlib, json, os, re, shutil, subprocess, tempfile, zipfile
from pathlib import Path
from .providers import DEFAULT, provider, validate
from . import genre3d, genres
TEMPLATES = Path(__file__).parent/'templates'

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',dir=path.parent,delete=False,suffix='.tmp') as handle:
        handle.write(json.dumps(value,indent=2)+'\n');temporary=Path(handle.name)
    temporary.replace(path)
def project_path(root,name):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}',name): raise ValueError('Unsafe project name')
    root=Path(root).resolve();path=root/name
    if path.is_symlink(): raise ValueError('Symlink project forbidden')
    return path

def load(path):
    """Recover a fully written journal checkpoint after an interrupted pointer update."""
    path=Path(path);pointer=path/'bible.json'
    bible=json.loads(pointer.read_text()) if pointer.exists() else None
    while True:
        revision=bible['revision']+1 if bible else 1
        checkpoint=path/'checkpoints'/f'{revision:04d}.json'
        if not checkpoint.exists():break
        candidate=json.loads(checkpoint.read_text())
        parent=digest(pointer) if bible else None
        if '_previous_bible_sha256' not in candidate or candidate['_previous_bible_sha256']!=parent:break
        if candidate.get('revision')!=revision or not all(k in candidate for k in ['name','config','template','history','requirements','approved_appearance_references','assets']):raise ValueError('Invalid pending checkpoint; preserve it for recovery')
        write_json(pointer,candidate);bible=candidate
    if bible is None:raise ValueError('Project has no recoverable Game Bible')
    return bible
def save_revision(path, bible):
    checkpoint=path/'checkpoints'/f"{bible['revision']:04d}.json"
    if checkpoint.exists(): raise ValueError('Checkpoint already exists')
    bible['_previous_bible_sha256']=digest(path/'bible.json') if (path/'bible.json').exists() else None
    write_json(checkpoint,bible)
    write_json(path/'bible.json',bible)

def validate_prompt(prompt):
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>8000:
        raise ValueError('Prompt must contain 1..8000 characters')
    return prompt.strip()

def rollback(path,revision):
    """Restore design as a new audited revision, never delete later user work."""
    if type(revision) is not int or revision<1:raise ValueError('Invalid checkpoint revision')
    bible=load(path)
    checkpoint=path/'checkpoints'/f'{revision:04d}.json'
    if not checkpoint.is_file():raise ValueError('Checkpoint does not exist')
    old=json.loads(checkpoint.read_text());before=copy.deepcopy(bible['config'])
    bible['config']=old['config'];bible['template']=old['template'];bible['revision']+=1
    prompt=f'Restore design from revision {revision}; retain audit, assets and approved references'
    bible['requirements'].append({'prompt':prompt,'resolution':'CONFIG_RESTORED','confirmed':True})
    bible['history'].append({'revision':bible['revision'],'prompt':prompt,'provider':'checkpoint','config':bible['config'],'restored_from':revision,'changes':{k:{'before':before.get(k),'after':v} for k,v in bible['config'].items() if before.get(k)!=v}})
    save_revision(path,bible);return bible

def new(path,name,prompt,model='template'):
    prompt=validate_prompt(prompt)
    if path.exists(): raise ValueError('Project already exists; use add')
    selected=genres.select(prompt)
    mode3d=selected['dimensions']==3
    config=genre3d.propose(prompt,genre3d.DEFAULT,model) if mode3d else provider(model).propose(prompt,DEFAULT)
    bible={'schema_version':1,'name':name,'revision':1,'template':selected['backend'],
           'config':config,'requirements':[{'prompt':prompt,'resolution':'PARTIAL_TEMPLATE_SUPPORT','confirmed':True}],
           'history':[{'revision':1,'prompt':prompt,'provider':model,'config':config}],
           'approved_appearance_references':{},'assets':[],
           'limitations':['Bounded 2D collection/survival and 3D RPG templates are implemented; arbitrary genres and realistic art remain unavailable. All prompt text preserved; unrepresented clauses are pending.']}
    path.mkdir(parents=True);save_revision(path,bible)
    return bible

def add(path,prompt,model='template'):
    prompt=validate_prompt(prompt)
    bible=load(path);config=genre3d.propose(prompt,bible['config'],model) if bible['template']=='rpg_3d' else provider(model).propose(prompt,bible['config'])
    before=copy.deepcopy(bible);bible['revision']+=1;bible['config']=config
    changes={k:{'before':before['config'].get(k),'after':v} for k,v in config.items() if before['config'].get(k)!=v}
    bible['requirements'].append({'prompt':prompt,'resolution':'PARTIAL_TEMPLATE_SUPPORT' if changes else 'NO_SUPPORTED_CHANGE','confirmed':True})
    bible['history'].append({'revision':bible['revision'],'prompt':prompt,'provider':model,'config':config,'changes':changes})
    if before['approved_appearance_references']!=bible['approved_appearance_references']:raise ValueError('Locked appearance changed')
    save_revision(path,bible);return bible

def plan(path):
    bible=load(path)
    tasks=[{'id':'design','depends_on':[],'criterion':'Validated config and every prompt retained','status':'IMPLEMENTED'},
           {'id':'gameplay','depends_on':['design'],'criterion':'Move, collect, survive, win/lose and restart in real Godot','status':'IMPLEMENTED'},
           {'id':'qa','depends_on':['gameplay'],'criterion':'Godot import/startup/scenario exit0, no errors and explicit marker','status':'PENDING'},
           {'id':'package','depends_on':['qa'],'criterion':'Integrity-checked Godot project ZIP','status':'PENDING'},
           {'id':'production_art','depends_on':['design'],'criterion':'Licensed, approved, rigged assets and visual review','status':'BLOCKED'},
           {'id':'unrepresented_requirements','depends_on':['design'],'criterion':'Resolve every prompt clause outside supported config','status':'PENDING'}]
    if bible['template']=='rpg_3d':
        tasks[1]['criterion']='Third-person physics, obstacle navigation, enemy contact combat, abilities and restart in real Godot'
    if status(path)['qa']=='RUNTIME_CHECKED':
        for task in tasks:
            if task['id']=='qa': task['status']='RUNTIME_CHECKED'
            if task['id']=='package': task['status']='IMPLEMENTED'
    value={'revision':bible['revision'],'tasks':tasks};write_json(path/'plan.json',value);return value

def managed_files(path):
    for p in (path/'godot').rglob('*'):
        if p.is_symlink():raise ValueError('Symlink in generated project forbidden: '+str(p))
    return {p.relative_to(path/'godot').as_posix():digest(p) for p in (path/'godot').rglob('*') if p.is_file() and '.godot' not in p.parts and not p.name.endswith(('.uid','.import'))}

def build(path):
    bible=load(path);mode3d=bible['template']=='rpg_3d'
    genres.get(bible['template'])
    (genre3d.validate if mode3d else validate)(bible['config']);game=path/'godot'
    previous=path/'managed.json'
    if previous.exists():
        expected=json.loads(previous.read_text())
        for file,hash_value in expected.items():
            p=game/file
            if not p.is_file() or digest(p)!=hash_value: raise ValueError('Managed source edited; preserved, resolve before rebuilding: '+file)
    elif game.exists():raise ValueError('Unmanaged game directory; refusing overwrite')
    game.mkdir(exist_ok=True)
    if mode3d:genre3d.compile(game,TEMPLATES)
    else:
        for name in ['main.gd','scenario.gd']:shutil.copyfile(TEMPLATES/name,game/name)
    (game/'main.tscn').write_text('[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://main.gd" id="1"]\n[node name="GeneratedGame" type="Node2D"]\nscript = ExtResource("1")\n')
    (game/'project.godot').write_text('config_version=5\n[application]\nconfig/name='+json.dumps(bible['name'])+'\nrun/main_scene="res://main.tscn"\nconfig/features=PackedStringArray("4.2", "GL Compatibility")\n[display]\nwindow/size/viewport_width=800\nwindow/size/viewport_height=600\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
    if mode3d:
        scene=game/'main.tscn';scene.write_text(scene.read_text().replace('type="Node2D"','type="Node3D"'))
    if mode3d:\n        from .player_visual import install_approved_visual\n        install_approved_visual(path, game, bible)\n    write_json(game/'game.json',bible['config'])
    write_json(path/'managed.json',managed_files(path));plan(path)
    write_json(path/'build.json',{'revision':bible['revision'],'bible_sha256':digest(path/'bible.json'),'status':'IMPLEMENTED','files':managed_files(path)})
    return {'revision':bible['revision'],'status':'IMPLEMENTED','project':str(game),'next':'factory test'}

def evidence_key(path):
    return {'revision':load(path)['revision'],'files':managed_files(path),'bible_sha256':digest(path/'bible.json')}

def test(path):
    built=json.loads((path/'build.json').read_text())
    if built['revision']!=load(path)['revision'] or built['files']!=managed_files(path) or built.get('bible_sha256')!=digest(path/'bible.json'):raise ValueError('Source/design changed or revision not built; build first')
    engine=os.environ.get('GODOT_BIN') or shutil.which('godot4') or shutil.which('godot')
    if not engine:raise ValueError('BLOCKED: Godot4.2+ unavailable; set GODOT_BIN')
    tested_evidence=evidence_key(path)
    game=(path/'godot').resolve();checks=[]
    env=os.environ.copy()
    # QA writes no ordinary player saves. Paths stay inside project and are excluded from archives.
    for key,suffix in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]:
        target=path/'.qa'/suffix;target.mkdir(parents=True,exist_ok=True);env[key]=str(target.resolve())
    commands=[('version',[engine,'--version']),('import',[engine,'--headless','--editor','--path',str(game),'--import']),
              ('startup',[engine,'--headless','--path',str(game),'--quit-after','8']),
              ('scenario',[engine,'--headless','--fixed-fps','60','--path',str(game),'--script','res://scenario.gd'])]
    if load(path)['config'].get('campaign'):
        commands.extend([
            ('campaign',[engine,'--headless','--fixed-fps','60','--path',str(game),'--script','res://campaign_scenario.gd']),
            ('campaign_restart',[engine,'--headless','--fixed-fps','60','--path',str(game),'--script','res://campaign_scenario.gd','--','--verify-restart'])])
    try:
        for label,cmd in commands:
            result=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=90)
            output=result.stdout+result.stderr
            passed=result.returncode==0 and not re.search(r'(?im)^\s*(SCRIPT ERROR:|ERROR:|Parse Error:)',output)
            if label=='version':passed=passed and bool(re.match(r'^4\.(?:[2-9]|[1-9][0-9])\.',output.strip()))
            if label=='scenario':passed=passed and 'FACTORY_SCENARIO_PASS' in output.splitlines()
            if label=='campaign':passed=passed and 'FACTORY_CAMPAIGN_PASS' in output.splitlines()
            if label=='campaign_restart':passed=passed and 'FACTORY_CAMPAIGN_RESTART_PASS' in output.splitlines()
            checks.append({'name':label,'command':cmd,'exit_code':result.returncode,'passed':passed,'log':output})
            if not passed:break
    except (OSError,subprocess.TimeoutExpired) as error:checks.append({'name':'runner','passed':False,'log':str(error)})
    if tested_evidence!=evidence_key(path):checks.append({'name':'source_integrity','passed':False,'log':'Source changed while QA was running'})
    report={'status':'RUNTIME_CHECKED' if len(checks)==len(commands) and all(c['passed'] for c in checks) else 'FAILED','evidence':tested_evidence,'checks':checks,'visual_review':'PENDING','hardware_review':'PENDING'}
    write_json(path/'qa.json',report)
    if report['status']=='FAILED':raise ValueError('Godot QA failed: '+str(path/'qa.json'))
    dist=path/'dist';dist.mkdir(exist_ok=True)
    archive=dist/(load(path)['name']+'.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(game.rglob('*')):
            if p.is_file() and '.godot' not in p.parts and not p.name.endswith(('.uid','.import')):z.write(p,p.relative_to(game))
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    write_json(dist/'manifest.json',{'format':'GODOT_PROJECT_ZIP_NOT_NATIVE_EXECUTABLE','sha256':digest(archive),'files':managed_files(path),'revision':load(path)['revision'],'native_export':'NOT_IMPLEMENTED'})
    return report

def status(path):
    bible=load(path);report=json.loads((path/'qa.json').read_text()) if (path/'qa.json').exists() else None
    current=report and report['evidence']==evidence_key(path)
    approved=sum(a.get('license_review')=='APPROVED' and a.get('visual_review')=='APPROVED' and a.get('engine_import')=='RUNTIME_CHECKED' for a in bible['assets'])
    return {'name':bible['name'],'revision':bible['revision'],'config':bible['config'],'qa':report['status'] if current else 'PENDING_OR_STALE','approved_assets':approved,'staged_assets':len(bible['assets']),'production_art':'BLOCKED','provider_default':'template','requirements':bible['requirements'],'limitations':bible['limitations']}
