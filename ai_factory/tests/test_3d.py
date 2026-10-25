import tempfile, unittest
from pathlib import Path
from ai_factory import core
class Generation3DTests(unittest.TestCase):
    def test_new_and_add_3d(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'RPG';b=core.new(p,'RPG','a 3D RPG with 1 enemy and a healing ability')
            self.assertEqual(b['template'],'rpg_3d')
            b=core.add(p,'add an enemy, add lightning ability and a new area')
            self.assertEqual(b['config']['enemies'],2);self.assertEqual(b['config']['areas'],2)
            self.assertIn('lightning',b['config']['abilities']);self.assertIn('heal',b['config']['abilities'])
            core.build(p);self.assertTrue((p/'godot/actor.gd').exists())
            self.assertEqual(len(b['requirements']),2)
    def test_2d_still_default(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'Old';self.assertEqual(core.new(p,'Old','5 coins')['template'],'collect_survive_2d')
    def test_asset_reference_protection(self):
        from ai_factory.assets import stage_glb
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'fake.glb';source.write_bytes(b'fake')
            with self.assertRaises(ValueError):stage_glb(source,Path(d)/'out.glb',{'approved':False})
            meta={'approved':True,'license':'CC0','author':'test','source':'test','reference_sha256':'wrong'}
            with self.assertRaises(ValueError):stage_glb(source,Path(d)/'out.glb',meta,locked_reference='locked')
    def test_actual_glb_import_and_animation(self):
        import os, shutil, subprocess
        from ai_factory.core import TEMPLATES
        from asset_fixtures import write_rigged_fixture
        engine=os.environ.get('GODOT_BIN') or shutil.which('godot4') or shutil.which('godot')
        if not engine:self.skipTest('Godot unavailable: GLB runtime validation pending')
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'assets').mkdir()
            (root/'project.godot').write_text('config_version=5\n[application]\nconfig/name="Import test"\n')
            shutil.copyfile(TEMPLATES/'rpg_3d/character_import.gd',root/'character_import.gd')
            write_rigged_fixture(root/'assets/fixture.glb')
            (root/'test.gd').write_text('''extends SceneTree
func _initialize(): call_deferred("run")
func run():
	var adapter = load("res://character_import.gd").new()
	root.add_child(adapter)
	var approved = {"approved":true,"license":"CC0 synthetic test only","author":"test","source":"generated triangle","reference_sha256":"test fixture only"}
	var mapping = {"idle":"idle","walk":"move","run":"move","jump":"dodge","attack":"attack_light","hit":"hit","defeat":"defeat"}
	if not adapter.configure("res://assets/fixture.glb",approved,mapping):
		printerr(adapter.status)
		quit(1)
		return
	if not adapter.play_clip("attack_light"):
		quit(1)
		return
	adapter.animation_player.advance(0.2)
	if adapter.animation_player.current_animation_position <= 0:
		quit(1)
		return
	adapter.queue_free()
	await process_frame
	print("ASSET_IMPORT_PASS")
	quit(0)
''')
            env=dict(os.environ,XDG_DATA_HOME=str(root/'data'),XDG_CONFIG_HOME=str(root/'config'),XDG_CACHE_HOME=str(root/'cache'))
            result=subprocess.run([engine,'--headless','--path',str(root),'--script','res://test.gd'],env=env,capture_output=True,text=True,timeout=40)
            output=result.stdout+result.stderr
            evidence=Path(__file__).resolve().parents[1]/"verification/3d/asset-import.log"
            evidence.parent.mkdir(parents=True,exist_ok=True)
            evidence.write_text("Godot command: "+engine+" --headless --path <isolated temporary project> --script res://test.gd\n"+output)
            self.assertEqual(result.returncode,0,output);self.assertNotIn('ERROR:',output);self.assertIn('ASSET_IMPORT_PASS',output)
