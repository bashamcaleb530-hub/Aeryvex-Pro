"""Real Chromium + Godot end-to-end of the Character Studio workflow (development only).

Requires Python playwright, Chromium (CHROMIUM_BIN) and Godot 4 (GODOT_BIN); xvfb-run for renders.
Run: python3 -m ai_factory.tests.browser_character_e2e
Uses only the synthetic test rig; screenshots go to ai_factory/verification/character/.
"""
import json, os, re, sys, tempfile, threading
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asset_fixtures import write_humanoid_fixture
from ai_factory.app import create_server
from ai_factory import core


def run():
    evidence = Path(__file__).resolve().parents[1] / 'verification/character'
    evidence.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(prefix='factory-character-')
    root = Path(temporary.name) / 'workspace'
    files = Path(temporary.name) / 'files'
    rig = write_humanoid_fixture(files / 'rig.glb')
    rejected_rig = write_humanoid_fixture(files / 'idle_only.glb', clips=['Idle', 'Walking'])
    server = create_server(root, 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = 'http://127.0.0.1:' + str(server.server_port)
    errors = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_BIN', '/usr/bin/chromium'), args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('console', lambda m: m.type == 'error' and errors.append(m.text))
            page.goto(url)
            page.fill('#game-name', 'RigDemo')
            page.fill('#prompt', 'A 3D RPG with 2 missions, a town, 1 enemy and heal')
            page.uncheck('#native')
            page.click('#generate')
            expect(page.locator('#job-status')).to_have_text('COMPLETED', timeout=240000)
            expect(page.locator('#character-studio')).to_be_visible()
            # 1. Lock the approved reference (a render of the synthetic rig stands in for artwork).
            reference = files / 'reference.png'
            reference.write_bytes(bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de0000000c4944415408d763f8ffff3f0005fe02fea7d69f3a0000000049454e44ae426082'))
            page.fill('#lock-name', 'Test Rig')
            page.set_input_files('#lock-image', str(reference))
            page.check('#lock-confirm')
            page.click('#lock-form button[type=submit]')
            expect(page.locator('#studio-steps')).to_contain_text('LOCKED')

            def upload(path, label):
                page.set_input_files('#upload-file', str(path))
                page.fill('#upload-source', label)
                page.click('#upload-form button[type=submit]')

            def inspect_and_stage(card):
                card.locator('button:has-text("Inspect in Godot")').click()
                expect(card.locator('table.clips')).to_be_visible(timeout=180000)
                card.locator('input[aria-label=License]').fill('CC0 synthetic test fixture')
                card.locator('input[aria-label=Author]').fill('Aeryvex test suite')
                card.locator('.stage-form input[type=checkbox]').check()
                card.locator('button:has-text("Stage for approval")').click()
            # 2. A candidate missing most clips is inspected, staged and rejected with a reason.
            upload(rejected_rig, 'Incomplete rig delivery')
            inspect_and_stage(page.locator('#studio-candidates .card').first)
            asset = page.locator('#studio-assets .card').first
            expect(asset).to_be_visible()
            asset.locator('input[aria-label="Rejection reason"]').fill('Missing jump, attack, hurt and death clips')
            asset.locator('button:has-text("Reject")').click()
            expect(page.locator('#studio-assets')).to_contain_text('Rejected: Missing jump')
            # 3. The complete rig is inspected (renders beside reference), staged, approved and bound.
            upload(rig, 'Synthetic humanoid test rig')
            card = page.locator('#studio-candidates .card', has_text='Synthetic humanoid').first
            inspect_and_stage(card)
            page.locator('#character-studio').screenshot(path=str(evidence / 'studio-inspected.png'))
            asset = page.locator('#studio-assets .card', has_text='PENDING').first
            asset.locator('.decision input[type=checkbox]').check()
            asset.locator('button:has-text("Approve final appearance")').click()
            bind = page.locator('#studio-assets .card button:has-text("Use as player character"):not([disabled])').first
            bind.click()
            expect(page.locator('#studio-assets')).to_contain_text('PLAYER VISUAL', timeout=180000)
            page.click('#rebuild')
            status = page.locator('#job-status')
            expect(status).to_have_text(re.compile('RUNNING|QUEUED'), timeout=20000)
            expect(status).to_have_text(re.compile('^(COMPLETED|FAILED|BLOCKED)$'), timeout=300000)
            expect(status).to_have_text('COMPLETED')
            expect(page.locator('#studio-steps')).to_contain_text('Game QA', timeout=10000)
            expect(page.locator('#studio-steps li').last).to_contain_text('PASSED', timeout=15000)
            page.click('#capture-preview')
            expect(page.locator('#preview-frames img').first).to_be_visible(timeout=180000)
            page.wait_for_timeout(1000)
            page.screenshot(path=str(evidence / 'factory-character-complete.png'), full_page=True)
            page.locator('#deliverables').screenshot(path=str(evidence / 'gameplay-preview.png'))
            page.set_viewport_size({'width': 390, 'height': 900})
            page.wait_for_timeout(400)
            overflow = page.evaluate('document.documentElement.scrollWidth - window.innerWidth')
            page.locator('#character-studio').screenshot(path=str(evidence / 'studio-mobile.png'))
            browser.close()
        project = root / 'RigDemo'
        qa = json.loads((project / 'qa.json').read_text())
        bible = core.load(project)
        character = next(c for c in qa['checks'] if c['name'] == 'character')
        result = {'qa': qa['status'], 'checks': [(c['name'], c['passed']) for c in qa['checks']],
                  'character_report': next(l for l in character['log'].splitlines() if l.startswith('CHARACTER_REPORT')),
                  'assets': [(a['sha256'][:12], a['visual_review'], a.get('rejection_reason')) for a in bible['assets']],
                  'binding': bible.get('player_visual_binding'), 'mobile_overflow_px': overflow, 'browser_errors': errors}
        assert qa['status'] == 'RUNTIME_CHECKED' and character['passed'], result
        assert [a[1] for a in result['assets']] == ['REJECTED', 'APPROVED'], result
        assert overflow <= 0 and not errors, result
        core.write_json(evidence / 'browser-character-e2e.json', result)
        print(json.dumps(result, indent=2))
        print('CHARACTER_BROWSER_E2E_PASS')
    finally:
        server.shutdown()
        temporary.cleanup()


if __name__ == '__main__':
    run()
