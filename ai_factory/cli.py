import argparse,json,sys
from pathlib import Path
from . import core

def main(argv=None):
    parser=argparse.ArgumentParser(prog='factory',description='Aeryvex AI Game Factory')
    parser.add_argument('--workspace',default='factory_projects',help='Dedicated project store, never original_game')
    commands=parser.add_subparsers(dest='command',required=True)
    for command in ['new','add','plan','build','test','status','ship','export','rollback','assets','asset-stage','asset-review']:
        p=commands.add_parser(command)
        p.add_argument('--name' if command in ['new','ship'] else '--project',required=True)
        if command in ['new','add','ship']:
            p.add_argument('--prompt',required=True)
            p.add_argument('--provider',choices=['template','ollama'],default='template')
        if command=='rollback':p.add_argument('--revision',type=int,required=True)
        if command=='asset-stage':
            p.add_argument('--file',required=True);p.add_argument('--metadata',required=True);p.add_argument('--character')
        if command=='asset-review':
            p.add_argument('--sha256',required=True)
            for flag in ['license','visual','prototype']:p.add_argument('--approve-'+flag,action='store_true')
    p=commands.add_parser('character',help='Character Studio: reference lock, candidates, inspection, approval, binding')
    p.add_argument('action',choices=['status','lock','upload','meshy-generate','meshy-refresh','meshy-fetch','meshy-rig','inspect','stage','approve','reject','mapping','bind','unbind','preview'])
    p.add_argument('--project',required=True);p.add_argument('--character');p.add_argument('--candidate');p.add_argument('--sha256')
    p.add_argument('--image');p.add_argument('--file');p.add_argument('--source');p.add_argument('--note',default='')
    p.add_argument('--license');p.add_argument('--author');p.add_argument('--mapping',help='JSON object: state -> clip')
    p.add_argument('--reason',default='');p.add_argument('--height',type=float,default=1.8);p.add_argument('--yaw',type=int,default=0)
    p.add_argument('--confirm',action='store_true',help='The --image is the exact approved appearance')
    p.add_argument('--approve-intake',action='store_true');p.add_argument('--approve-license',action='store_true')
    p.add_argument('--authorize-paid',action='store_true',help='Allow Meshy requests that may spend credits')
    p=commands.add_parser('ui');p.add_argument('--port',type=int,default=8765)
    p=commands.add_parser('jobs');p.add_argument('--id');p.add_argument('--resume',action='store_true');p.add_argument('--cancel',action='store_true')
    args=parser.parse_args(argv)
    try:
        root=Path(args.workspace).resolve()
        # Never allow existing protected content to become a generation workspace.
        repository=Path(__file__).resolve().parents[1]
        for protected in ['original_game','scripts','tests','tools','ai_factory','.git','website_builder']:
            p=repository/protected
            if root==p or p in root.parents:raise ValueError('Protected workspace: '+str(root))
        if args.command=='ui':
            from .app import serve
            serve(root,args.port);return 0
        if args.command=='jobs':
            from .jobs import JobManager
            manager=JobManager(root)
            if args.resume or args.cancel:
                if not args.id:raise ValueError('--id required')
                result=manager.resume(args.id) if args.resume else manager.cancel(args.id)
            else:result=manager.get(args.id) if args.id else manager.list()
            print(json.dumps(result,indent=2));return 0
        if args.command=='character':
            print(json.dumps(character_command(core.project_path(root,args.project),args),indent=2));return 0
        name=args.name if args.command in ['new','ship'] else args.project
        path=core.project_path(root,name)
        if args.command=='ship':
            # One-command flow. Never conceal QA/art gaps or delete partial projects.
            created=core.new(path,name,args.prompt,args.provider)
            built=core.build(path)
            try:
                qa=core.test(path)
                result={'status':'RUNTIME_CHECKED','project':str(path),'godot_project':str(path/'godot'), 'zip':str(path/'dist'/(name+'.zip')),'qa':qa['status'],'visual_review':'PENDING','production_art':'BLOCKED','requirements':created['requirements']}
            except (ValueError,OSError,KeyError,json.JSONDecodeError) as error:
                result={'status':'BUILT_QA_BLOCKED','project':str(path),'godot_project':str(path/'godot'),'build':built['status'],'reason':str(error),'visual_review':'PENDING','production_art':'BLOCKED','next':'Install Godot 4.2+ or inspect QA error, then run factory test --project '+name}
        elif args.command=='new':result=core.new(path,name,args.prompt,args.provider)
        elif args.command=='add':result=core.add(path,args.prompt,args.provider)
        elif args.command=='rollback':result=core.rollback(path,args.revision)
        elif args.command=='export':
            from .native import export_linux
            result=export_linux(path)
        elif args.command=='assets':
            from .asset_review import inventory
            result=inventory(path)
        elif args.command=='asset-stage':
            from .asset_review import stage
            result=stage(path,args.file,json.loads(Path(args.metadata).read_text()),character=args.character)
        elif args.command=='asset-review':
            from .asset_review import review
            result=review(path,args.sha256,license_approved=True if args.approve_license else None,visual_approved=True if args.approve_visual else None,prototype_approved=True if args.approve_prototype else None)
        else:result=getattr(core,args.command)(path)
        print(json.dumps(result,indent=2));return 0
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as error:
        print(json.dumps({'status':'FAILED','error':str(error)}),file=sys.stderr);return 1


def character_command(path,args):
    from . import character_studio as cs
    a=args.action;mapping=json.loads(args.mapping) if args.mapping else None
    if a=='status':return cs.overview(path)
    if a=='lock':image=Path(args.image);return cs.lock_reference(path,args.character,image.read_bytes(),image.suffix,args.confirm,args.note)
    if a=='upload':return cs.add_upload(path,args.character,Path(args.file).read_bytes(),args.source)
    if a=='meshy-generate':return cs.meshy_generate(path,args.character,args.authorize_paid)
    if a=='meshy-refresh':return cs.meshy_refresh(path,args.character,args.candidate)
    if a=='meshy-fetch':return cs.meshy_fetch(path,args.character,args.candidate)
    if a=='meshy-rig':return cs.meshy_rig(path,args.character,args.candidate,args.authorize_paid)
    if a=='inspect':return cs.inspect_candidate(path,args.character,args.candidate,mapping)
    if a=='stage':return cs.stage_candidate(path,args.character,args.candidate,args.license,args.author,mapping,args.approve_intake)
    if a in ['approve','reject']:return {'revision':cs.decide(path,args.sha256,a=='approve',args.approve_license,args.reason)['revision']}
    if a=='mapping':return {'revision':cs.set_mapping(path,args.sha256,mapping)['revision']}
    if a=='bind':return cs.bind(path,args.sha256,args.height,args.yaw)
    if a=='unbind':return {'revision':cs.unbind(path)['revision']}
    from .preview import capture
    return {k:v for k,v in capture(path).items() if k!='log_tail'}
