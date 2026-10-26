"""Offline Character Studio browser flow using synthetic candidate geometry."""
import json
import tempfile
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from ai_factory import core
from ai_factory.app import create_server
from ai_factory.tests.asset_fixtures import write_rigged_fixture

def run():
    with tempfile.TemporaryDirectory() as tmp:
        root=Path(tmp);p=root/'StudioGame';core.new(p,'StudioGame','3D RPG')
        b=core.load(p);b['approved_appearance_references']={'Orion':'a'*64};core.write_json(p/'bible.json',b)
        write_rigged_fixture(root/'.factory-candidates/test-task.glb')
        server=create_server(root,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
                page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto('http://127.0.0.1:'+str(server.server_port))
                page.locator('#projects button').click()
                page.locator('#meshy-task').fill('test-task')
                page.locator('#meshy-use').click()
                page.locator('#asset-author').fill('Synthetic test')
                page.locator('#asset-source').fill('Local fixture')
                page.locator('#asset-license').fill('CC0')
                page.locator('#asset-reference').fill('a'*64)
                page.locator('#asset-character').fill('Orion')
                page.locator('#asset-approved').check()
                page.locator('#stage-candidate').click()
                expect(page.locator('#assets')).to_contain_text('visual PENDING')
                page.get_by_role('button',name='Approve visual').click()
                expect(page.locator('#assets')).to_contain_text('visual APPROVED')
                page.reload();page.locator('#projects button').click()
                expect(page.locator('#assets')).to_contain_text('visual APPROVED')
                assert core.load(p)['approved_appearance_references']=={'Orion':'a'*64}
                assert not errors,errors
                page.set_viewport_size({'width':390,'height':844})
                assert page.locator('body').evaluate('(el)=>el.scrollWidth<=innerWidth'),page.locator('body').evaluate("()=>Array.from(document.querySelectorAll('*')).filter(e=>e.getBoundingClientRect().right>innerWidth).map(e=>({tag:e.tagName,id:e.id,right:e.getBoundingClientRect().right}))")
                browser.close()
                print('STUDIO_BROWSER_PASS: staged candidate, explicit review, reload, phone layout')
        finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':run()
