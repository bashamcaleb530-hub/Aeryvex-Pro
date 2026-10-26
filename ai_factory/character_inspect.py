"""Inspect a character GLB in a real, isolated Godot 4 project.

Reports what the engine actually sees: meshes, skins, skeleton bones, embedded
animation clips and whether each clip really moves the skeleton. When an X
display (or xvfb-run) is available it also renders turnaround and per-clip pose
images for human visual review. Nothing here approves an asset.

Usage: python3 -m ai_factory.character_inspect --glb model.glb --output DIR
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .assets import inspect_glb

MARKER = 'AERYVEX_INSPECTION_JSON:'
VIEWS = [('front', 0), ('three_quarter', 45), ('side', 90), ('back', 180)]
MAX_POSE_RENDERS = 12

INSPECT_GD = r'''extends SceneTree
var report := {}
func _initialize() -> void: call_deferred("run")
func finish(code: int) -> void:
	print("AERYVEX_INSPECTION_JSON:" + JSON.stringify(report))
	quit(code)
func bone_snapshot(skeletons: Array) -> Array:
	var poses := []
	for skeleton in skeletons:
		for bone in range(skeleton.get_bone_count()):
			poses.append(skeleton.get_bone_pose(bone))
	return poses
func pose_delta(a: Array, b: Array) -> float:
	var delta := 0.0
	for i in range(mini(a.size(), b.size())):
		var x: Transform3D = a[i]
		var y: Transform3D = b[i]
		delta = maxf(delta, x.origin.distance_to(y.origin))
		delta = maxf(delta, x.basis.get_rotation_quaternion().angle_to(y.basis.get_rotation_quaternion()))
	return delta
func shoot(camera: Camera3D, center: Vector3, distance: float, degrees: float, path: String) -> void:
	var angle := deg_to_rad(degrees)
	camera.position = center + Vector3(sin(angle) * distance, distance * 0.18, cos(angle) * distance)
	camera.look_at(center, Vector3.UP)
	for i in 3: await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(path)
func run() -> void:
	var args := OS.get_cmdline_user_args()
	var out_dir: String = args[0] if args.size() > 0 else ""
	var render := args.size() > 1 and args[1] == "render"
	var mapping := {}
	if args.size() > 2:
		var parsed = JSON.parse_string(args[2])
		if typeof(parsed) == TYPE_DICTIONARY: mapping = parsed
	var packed = load("res://character.glb")
	if not packed is PackedScene:
		report["error"] = "Godot could not load the imported GLB scene"
		finish(1)
		return
	var stage := Node3D.new()
	root.add_child(stage)
	var character: Node3D = packed.instantiate()
	stage.add_child(character)
	await process_frame
	var meshes := character.find_children("*", "MeshInstance3D", true, false)
	var skeletons := character.find_children("*", "Skeleton3D", true, false)
	var players := character.find_children("*", "AnimationPlayer", true, false)
	var bounds := AABB()
	var first := true
	var skinned := 0
	for mesh in meshes:
		if mesh.mesh == null: continue
		if mesh.skin != null or not mesh.skeleton.is_empty(): skinned += 1
		var box: AABB = mesh.global_transform * mesh.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
	report["mesh_instances"] = meshes.size()
	report["skinned_meshes"] = skinned
	report["bounds"] = {"position": [bounds.position.x, bounds.position.y, bounds.position.z], "size": [bounds.size.x, bounds.size.y, bounds.size.z]}
	var bone_names := []
	var bone_count := 0
	for skeleton in skeletons:
		bone_count += skeleton.get_bone_count()
		for bone in range(skeleton.get_bone_count()):
			if bone_names.size() < 120: bone_names.append(skeleton.get_bone_name(bone))
	report["skeletons"] = skeletons.size()
	report["bones"] = bone_count
	report["bone_names"] = bone_names
	report["animation_players"] = players.size()
	var clips := []
	var player: AnimationPlayer = players[0] if not players.is_empty() else null
	if player != null:
		for clip_name in player.get_animation_list():
			var animation := player.get_animation(clip_name)
			player.play(clip_name)
			player.seek(0.0, true)
			var start := bone_snapshot(skeletons)
			var motion := 0.0
			for fraction in [0.25, 0.5, 0.75]:
				player.seek(animation.length * fraction, true)
				motion = maxf(motion, pose_delta(start, bone_snapshot(skeletons)))
			clips.append({"name": str(clip_name), "length": animation.length, "tracks": animation.get_track_count(), "loop_mode": animation.loop_mode, "max_bone_motion": motion, "moves_skeleton": motion > 0.001})
			player.stop()
		for skeleton in skeletons: skeleton.reset_bone_poses()
	report["clips"] = clips
	report["renders"] = []
	if render and not out_dir.is_empty() and not first:
		var environment := WorldEnvironment.new()
		var env := Environment.new()
		env.background_mode = Environment.BG_COLOR
		env.background_color = Color("0b1220")
		env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		env.ambient_light_color = Color.WHITE
		env.ambient_light_energy = 0.55
		env.reflected_light_source = Environment.REFLECTION_SOURCE_BG
		environment.environment = env
		stage.add_child(environment)
		var key := DirectionalLight3D.new()
		key.rotation_degrees = Vector3(-40, 30, 0)
		stage.add_child(key)
		var fill := DirectionalLight3D.new()
		fill.rotation_degrees = Vector3(-20, -150, 0)
		fill.light_energy = 0.45
		stage.add_child(fill)
		var floor_mesh := MeshInstance3D.new()
		var plane := PlaneMesh.new()
		plane.size = Vector2(1, 1) * maxf(bounds.size.x, bounds.size.z) * 4.0 + Vector2(2, 2)
		floor_mesh.mesh = plane
		var floor_material := StandardMaterial3D.new()
		floor_material.albedo_color = Color("16233a")
		floor_mesh.material_override = floor_material
		floor_mesh.position.y = bounds.position.y
		stage.add_child(floor_mesh)
		var camera := Camera3D.new()
		camera.fov = 40
		stage.add_child(camera)
		camera.current = true
		var center := bounds.get_center()
		var distance := maxf(bounds.size.y, maxf(bounds.size.x, bounds.size.z)) * 1.75 + 0.4
		for view in [["front", 0.0], ["three_quarter", 45.0], ["side", 90.0], ["back", 180.0]]:
			var file: String = "view_" + view[0] + ".png"
			await shoot(camera, center, distance, view[1], out_dir.path_join(file))
			report["renders"].append({"file": file, "kind": "view", "label": view[0]})
		if player != null:
			var wanted := []
			for state in mapping:
				var clip_name = mapping[state]
				if typeof(clip_name) == TYPE_STRING and player.has_animation(clip_name): wanted.append([str(state), clip_name])
			if wanted.is_empty():
				for clip_name in player.get_animation_list(): wanted.append(["", str(clip_name)])
			var index := 0
			for entry in wanted.slice(0, MAX_POSES):
				var animation := player.get_animation(entry[1])
				player.play(entry[1])
				player.seek(animation.length * 0.5, true)
				player.pause()
				var file := "pose_%02d.png" % index
				await shoot(camera, center, distance, 35.0, out_dir.path_join(file))
				report["renders"].append({"file": file, "kind": "pose", "state": entry[0], "clip": entry[1], "time": animation.length * 0.5})
				index += 1
	finish(0)
'''.replace('MAX_POSES', str(MAX_POSE_RENDERS))

PROJECT = '''config_version=5
[application]
config/name="Aeryvex character inspection"
[display]
window/size/viewport_width=640
window/size/viewport_height=800
[rendering]
renderer/rendering_method="gl_compatibility"
'''


def engine_binary(godot_bin=None):
    return godot_bin or os.environ.get('GODOT_BIN') or shutil.which('godot4') or shutil.which('godot')


def display_command():
    """Return the prefix that gives Godot a real framebuffer, or None."""
    if os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'):
        return []
    runner = shutil.which('xvfb-run')
    return [runner, '-a', '-s', '-screen 0 1280x1024x24'] if runner else None


def _errors(output):
    return [line for line in output.splitlines()
            if re.match(r'\s*(SCRIPT ERROR:|ERROR:|Parse Error:)', line)]


def verify_mapping(report, mapping):
    """Per gameplay state: the mapped clip must exist and visibly move the skeleton."""
    clips = {clip['name']: clip for clip in report.get('clips', [])}
    result = {}
    for state, clip in sorted((mapping or {}).items()):
        if clip not in clips:
            result[state] = {'clip': clip, 'status': 'MISSING_CLIP'}
        elif not clips[clip]['moves_skeleton']:
            result[state] = {'clip': clip, 'status': 'CLIP_DOES_NOT_MOVE_SKELETON'}
        else:
            result[state] = {'clip': clip, 'status': 'ENGINE_VERIFIED', 'length': clips[clip]['length']}
    return result


def inspect_character(glb, output, mapping=None, godot_bin=None, render=True, timeout=240):
    """Run the inspection and write report.json plus any renders into a NEW output directory."""
    glb = Path(glb).expanduser().resolve(strict=True)
    facts = inspect_glb(glb)
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Inspection output must be a new or empty directory')
    output.mkdir(parents=True, exist_ok=True)
    mapping = dict(mapping or {})
    base = {'format': 'aeryvex-character-inspection-v1', 'glb_sha256': facts['sha256'], 'container': facts,
            'mapping': mapping, 'created': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
            'visual_review': 'PENDING_HUMAN_REVIEW', 'visual_approved': False}
    binary = engine_binary(godot_bin)
    if not binary:
        report = dict(base, status='BLOCKED_GODOT_UNAVAILABLE', engine_import='NOT_RUN', render_status='NOT_RUN')
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        return report
    prefix = display_command() if render else None
    with tempfile.TemporaryDirectory(prefix='aeryvex-inspect-') as temp:
        project = Path(temp) / 'project'
        project.mkdir()
        shutil.copyfile(glb, project / 'character.glb')
        (project / 'project.godot').write_text(PROJECT)
        (project / 'inspect.gd').write_text(INSPECT_GD)
        env = dict(os.environ, XDG_DATA_HOME=str(Path(temp) / 'data'),
                   XDG_CACHE_HOME=str(Path(temp) / 'cache'), XDG_CONFIG_HOME=str(Path(temp) / 'config'))
        logs = []
        try:
            version = subprocess.run([binary, '--version'], capture_output=True, text=True, timeout=30, env=env)
            imported = subprocess.run([binary, '--headless', '--editor', '--path', str(project), '--import'],
                                      capture_output=True, text=True, errors='replace', timeout=timeout, env=env)
            logs.append(imported.stdout + imported.stderr)
            command = [binary, '--audio-driver', 'Dummy', '--path', str(project), '--script', 'res://inspect.gd',
                       '--', str(output.resolve()), 'render' if prefix is not None else 'data', json.dumps(mapping)]
            command = prefix + command if prefix is not None else [binary, '--headless'] + command[1:]
            ran = subprocess.run(command, capture_output=True, text=True, errors='replace', timeout=timeout, env=env)
            logs.append(ran.stdout + ran.stderr)
        except subprocess.TimeoutExpired:
            report = dict(base, status='FAILED_TIMEOUT', engine_import='FAILED', render_status='NOT_RUN')
            (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
            return report
        log = '\n'.join(logs)
        engine = None
        for line in (ran.stdout + ran.stderr).splitlines():
            if line.startswith(MARKER):
                engine = json.loads(line[len(MARKER):])
        errors = _errors(log)
        ok = imported.returncode == 0 and ran.returncode == 0 and engine is not None and not engine.get('error') and not errors
        engine = engine or {}
        rigged = engine.get('bones', 0) > 0 and engine.get('skinned_meshes', 0) > 0
        renders = [r for r in engine.get('renders', []) if (output / r['file']).is_file()]
        report = dict(base, godot_version=version.stdout.strip(), engine=engine,
                      status='INSPECTED_PENDING_HUMAN_REVIEW' if ok else 'FAILED_ENGINE_INSPECTION',
                      engine_import='PASSED' if ok else 'FAILED',
                      rig='SKINNED_SKELETON' if rigged else 'STATIC_OR_UNSKINNED',
                      bones=engine.get('bones'), height=(engine.get('bounds') or {}).get('size', [None, None])[1],
                      clips=engine.get('clips', []), mapping_verification=verify_mapping(engine, mapping),
                      renders=renders,
                      render_status='RENDERED' if renders else ('BLOCKED_NO_DISPLAY' if prefix is None else 'FAILED'),
                      engine_errors=errors[:40], log_tail=log[-12000:])
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--glb', required=True)
    parser.add_argument('--output', required=True, help='New directory for report.json and renders')
    parser.add_argument('--mapping', help='JSON object: gameplay state -> clip name')
    parser.add_argument('--no-render', action='store_true')
    parser.add_argument('--godot-bin')
    args = parser.parse_args(argv)
    report = inspect_character(args.glb, args.output, json.loads(args.mapping) if args.mapping else None,
                               args.godot_bin, render=not args.no_render)
    summary = {k: v for k, v in report.items() if k not in ('log_tail', 'engine')}
    print(json.dumps(summary, indent=2))
    return 0 if report['engine_import'] == 'PASSED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
