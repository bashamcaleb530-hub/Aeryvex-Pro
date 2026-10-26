import argparse,json,sys
from pathlib import Path
from . import core

def main(argv=None):
    parser=argparse.ArgumentParser(prog='factory',description='Aeryvex AI Game Factory')
    parser.add_argument('--workspace',default='factory_projects',help='Dedicated project store, never original_game')
    commands=parser.add_subparsers(dest='command',required=True)
    for command in ['new','add','plan','build','test','status','ship']:
        p=commands.add_parser(command)
        p.add_argument('--name' if command in ['new','ship'] else '--project',required=True)
        if command in ['new','add','ship']:
            p.add_argument('--prompt',required=True)
            p.add_argument('--provider',choices=['template','ollama'],default='template')
    args=parser.parse_args(argv)
    try:
        root=Path(args.workspace).resolve()
        # Never allow existing protected content to become a generation workspace.
        repository=Path(__file__).resolve().parents[1]
        for protected in ['original_game','scripts','tests','tools','ai_factory','.git']:
            p=repository/protected
            if root==p or p in root.parents:raise ValueError('Protected workspace: '+str(root))
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
        else:result=getattr(core,args.command)(path)
        print(json.dumps(result,indent=2));return 0
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as error:
        print(json.dumps({'status':'FAILED','error':str(error)}),file=sys.stderr);return 1
