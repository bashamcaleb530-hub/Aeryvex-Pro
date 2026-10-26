"""Capture real gameplay screenshots of a built game, for review without a desktop.

Runs the exact built Godot project (under xvfb-run when there is no display)
with isolated user-data paths, drives a short scripted sequence and saves PNG
frames to <project>/previews/. The game source is never modified.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile

from . import core
from .character_inspect import _errors, display_command, engine_binary

PREVIEW_GD = r'''extends SceneTree
var frames_taken := []
func _initialize() -> void: call_deferred("run")
func wait(count: int) -> void:
	for i in range(count): await physics_frame
func shot(out: String, label: String) -> void:
	await RenderingServer.frame_post_draw
	var file := "frame_%02d.png" % frames_taken.size()
	root.get_texture().get_image().save_png(out.path_join(file))
	frames_taken.append({"file": file, "label": label})
func run() -> void:
	var out: String = OS.get_cmdline_user_args()[0]
	create_timer(90.0).timeout.connect(func(): quit(2))
	var world = load("res://main.tscn").instantiate()
	root.add_child(world)
	current_scene = world
	await wait(5)
	if world.get("campaign") != null: world.campaign.start_new_game()
	var p = world.get("player")
	if p is Node and "intent" in p:
		p.control_enabled = false
		for enemy in world.enemies: enemy.set_physics_process(false)
		p.yaw = 0.6
		p.pitch = -0.25
		await wait(30)
		await shot(out, "spawn")
		p.intent = Vector3(0.4, 0, -1).normalized()
		await wait(24)
		await shot(out, "walk")
		p.running = true
		await wait(20)
		await shot(out, "run")
		p.running = false
		p.intent = Vector3.ZERO
		p.jump_requested = true
		await wait(8)
		await shot(out, "jump")
		await wait(50)
		p.cooldown = 0
		p.attack()
		await wait(10)
		await shot(out, "attack")
		p.yaw = 2.4
		await wait(10)
		await shot(out, "camera orbit")
	else:
		for label in ["start", "play", "later"]:
			await wait(45)
			await shot(out, label)
	print("AERYVEX_PREVIEW_JSON:" + JSON.stringify(frames_taken))
	quit(0)
'''


def capture(path, godot_bin=None, timeout=180):
    path = Path(path)
    built = json.loads((path / 'build.json').read_text()) if (path / 'build.json').is_file() else None
    if not built or built['revision'] != core.load(path)['revision'] or built['files'] != core.managed_files(path):
        raise ValueError('Build the current revision before previewing')
    engine = engine_binary(godot_bin)
    if not engine:
        return {'status': 'BLOCKED_GODOT_UNAVAILABLE', 'frames': []}
    prefix = display_command()
    if prefix is None:
        return {'status': 'BLOCKED_NO_DISPLAY', 'frames': [],
                'detail': 'Install xvfb (xvfb-run) or run on a desktop session to render previews'}
    folder = path / 'previews'
    if folder.is_symlink():
        raise ValueError('Symlink preview directory forbidden')
    folder.mkdir(exist_ok=True)
    out = folder / ('r%04d-%02d' % (built['revision'], len(list(folder.glob('r%04d-*' % built['revision']))) + 1))
    out.mkdir()
    with tempfile.TemporaryDirectory(prefix='aeryvex-preview-') as temp:
        script = Path(temp) / 'preview.gd'
        script.write_text(PREVIEW_GD)
        env = dict(os.environ, XDG_DATA_HOME=str(Path(temp) / 'data'),
                   XDG_CACHE_HOME=str(Path(temp) / 'cache'), XDG_CONFIG_HOME=str(Path(temp) / 'config'))
        game = (path / 'godot').resolve()
        if not (game / '.godot').is_dir():
            subprocess.run([engine, '--headless', '--editor', '--path', str(game), '--import'],
                           capture_output=True, text=True, timeout=timeout, env=env)
        try:
            ran = subprocess.run(prefix + [engine, '--audio-driver', 'Dummy', '--path', str(game),
                                           '--resolution', '960x600', '--script', str(script), '--', str(out.resolve())],
                                 capture_output=True, text=True, errors='replace', timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return {'status': 'FAILED_TIMEOUT', 'frames': [], 'folder': out.relative_to(path).as_posix()}
    log = ran.stdout + ran.stderr
    frames = []
    for line in log.splitlines():
        if line.startswith('AERYVEX_PREVIEW_JSON:'):
            frames = json.loads(line[len('AERYVEX_PREVIEW_JSON:'):])
    frames = [f for f in frames if (out / f['file']).is_file()]
    errors = _errors(log)
    report = {'status': 'CAPTURED' if frames and ran.returncode == 0 and not errors else 'FAILED',
              'revision': built['revision'], 'folder': out.relative_to(path).as_posix(), 'frames': frames,
              'engine_errors': errors[:40], 'log_tail': log[-6000:],
              'note': 'Scripted capture of the built game; not a substitute for hands-on playtesting.'}
    core.write_json(out / 'preview.json', report)
    return report


def latest(path):
    folder = Path(path) / 'previews'
    runs = sorted(p for p in folder.glob('r*-*') if (p / 'preview.json').is_file()) if folder.is_dir() else []
    return json.loads((runs[-1] / 'preview.json').read_text()) if runs else None
