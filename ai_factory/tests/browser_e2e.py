"""Real Chromium UI + Godot end-to-end. Requires playwright and Chromium for development only."""
import json, os, re, shutil, tempfile, threading, time, zipfile
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright, expect
from ai_factory.app import create_server
from ai_factory import core

def run():
    evidence=Path(__file__).resolve().parents[1]/'verification/issue2';evidence.mkdir(parents=True,exist_ok=True)
    output=Path(os.environ.get('FACTORY_E2E_OUTPUT','/tmp/factory-e2e-artifacts'));output.mkdir(parents=True,exist_ok=True)
    temporary=tempfile.TemporaryDirectory(prefix='factory-browser-');root=Path(temporary.name)
    server=create_server(root,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    url='http://127.0.0.1:'+str(server.server_port);results=[];errors=[]
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_BIN','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':1100},accept_downloads=True)
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(url);expect(page.locator('h1')).to_have_text('Build your next world.')
            page.screenshot(path=str(evidence/'application-empty.png'),full_page=True)
            def start(button):
                with page.expect_response(lambda r:'/api/jobs' in r.url and r.request.method=='POST') as response:
                    page.locator(button).click()
                assert response.value.status==202,response.value.text()
                return response.value.json()['id']
            def completed(name,jid):
                status=page.locator('#job-status[data-job-id="'+jid+'"]')
                expect(status).to_have_text(re.compile(r'^(COMPLETED|FAILED|BLOCKED|BUDGET_EXCEEDED|INTERRUPTED)$'),timeout=180000)
                expect(status).to_have_text('COMPLETED')
                p=root/name;b=core.load(p);qa=json.loads((p/'qa.json').read_text());native=json.loads((p/'native.json').read_text())
                assert qa['status']=='RUNTIME_CHECKED',qa
                assert native['status']=='NATIVE_CHECKED',native
                assert qa['evidence']==core.evidence_key(p)
                snapshot=evidence/'runs'/(name+'-r'+str(b['revision']));snapshot.mkdir(parents=True,exist_ok=True)
                core.write_json(snapshot/'qa.json',qa)
                saved_native=json.loads(json.dumps(native))
                for check in saved_native['checks']:
                    log=Path(check['log']);shutil.copyfile(log,snapshot/(check['name']+'.log'))
                    check['log']=check['name']+'.log'
                core.write_json(snapshot/'native.json',saved_native)
                core.write_json(snapshot/'bible.json',b)
                results.append({'name':name,'revision':b['revision'],'config':b['config'],'qa':qa['status'],'qa_checks':[{'name':c['name'],'passed':c['passed'],'log':c['log']} for c in qa['checks']],'native':native['status'],'native_checks':[c['name'] for c in native['checks']],'archive_sha256':native['archive_sha256'],'elapsed_seconds':server.manager.get(jid)['elapsed_seconds']})
                print('VERIFIED',name,'revision',b['revision'],flush=True)
                return p,b,native
            page.locator('#game-name').fill('BeaconValley')
            page.locator('#prompt').fill('A 3D RPG with 3 missions, a town, 2 enemies and a healing ability')
            p,b,n=completed('BeaconValley',start('#generate'))
            checkpoint=(p/'checkpoints/0001.json').read_bytes()
            expect(page.locator('#source-download')).to_be_visible()
            page.locator('#prompt').fill('Add an enemy, add a new area and lightning, and make missions longer')
            p,b,n=completed('BeaconValley',start('#generate'))
            assert b['revision']==2 and b['config']['areas']==2 and b['config']['enemies']==3
            assert 'lightning' in b['config']['abilities'] and b['config']['mission_length']==2
            assert (p/'checkpoints/0001.json').read_bytes()==checkpoint
            page.reload();expect(page.locator('#projects button')).to_have_text('BeaconValley')
            page.locator('#projects button').click();expect(page.locator('#project-title')).to_have_text('BeaconValley · revision 2')
            page.screenshot(path=str(evidence/'application-campaign.png'),full_page=True)
            for control,filename in [('#source-download','Aeryvex_Campaign_Godot.zip'),('#native-download','Aeryvex_Campaign_Linux.zip')]:
                with page.expect_download() as info:page.locator(control).click()
                info.value.save_as(str(output/filename))
                with zipfile.ZipFile(output/filename) as archive:assert archive.testzip() is None
            core.write_json(output/'campaign-qa.json',json.loads((p/'qa.json').read_text()))
            core.write_json(output/'campaign-native.json',n)
            # Rollback is another immutable revision, not deletion of the requirements.
            page.locator('#checkpoint').select_option('1')
            p,b,n=completed('BeaconValley',start('#rollback'))
            assert b['revision']==3 and b['config']['areas']==1 and len(b['requirements'])==3
            assert (p/'checkpoints/0001.json').read_bytes()==checkpoint
            # Distinct 2D flow, generated and revised through the same actual UI.
            page.locator('#new-project').click();page.locator('#game-name').fill('CoinRunner')
            page.locator('#prompt').fill('A blue 2D game collecting 8 coins while avoiding 2 enemies')
            p,b,n=completed('CoinRunner',start('#generate'))
            assert b['template']=='collect_survive_2d'
            page.locator('#prompt').fill('Make the player faster and red with 12 coins')
            p,b,n=completed('CoinRunner',start('#generate'))
            assert b['config']['coins']==12 and b['config']['color']=='red' and b['config']['speed']==260
            with page.expect_download() as info:page.locator('#native-download').click()
            info.value.save_as(str(output/'Aeryvex_CoinRunner_Linux.zip'))
            page.set_viewport_size({'width':390,'height':844})
            assert page.locator('body').evaluate('(el)=>el.scrollWidth<=innerWidth'),'Mobile builder overflow'
            page.screenshot(path=str(evidence/'application-mobile.png'),full_page=True)
            assert not errors,errors
            browser.close()
        core.write_json(evidence/'browser-e2e.json',{'status':'PASS','engine':os.environ.get('GODOT_BIN'),'host':'Debian 13','runs':results,'browser_errors':errors,'visual_review':'UI screenshots inspected separately; game art remains prototype','human_playtime':'NOT_MEASURED','output':str(output)})
        print('BROWSER_E2E_PASS',flush=True)
    finally:
        for job in server.manager.list():
            if job['status'] in ['RUNNING','QUEUED']:server.manager.cancel(job['id'])
        server.shutdown();server.server_close();thread.join();temporary.cleanup()

if __name__=='__main__':run()
