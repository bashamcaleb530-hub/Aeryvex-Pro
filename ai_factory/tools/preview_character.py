"""Create an isolated, playable Godot 4 preview of an existing GLB mesh.

This is intentionally a mesh/locomotion preview, NOT rigging or animation.
Never writes into an existing game, project or output directory.
Usage:
    python3 -m ai_factory.tools.preview_character --glb model.glb --output /tmp/SornPreview
    godot --path /tmp/SornPreview --editor
"""
import argparse
from pathlib import Path
import shutil
import struct

MAIN_GD = r'''extends Node3D

const SPEED := 5.0
const JUMP_VELOCITY := 4.5
var actor: CharacterBody3D
var camera: Camera3D
var pivot_yaw := 0.0
var pivot_pitch := -0.2
var look_active := false

func _ready() -> void:
    var floor_body := StaticBody3D.new()
    floor_body.name = "Ground"
    add_child(floor_body)
    var floor_mesh := MeshInstance3D.new()
    var plane := PlaneMesh.new()
    plane.size = Vector2(50, 50)
    floor_mesh.mesh = plane
    var mat := StandardMaterial3D.new()
    mat.albedo_color = Color(0.08, 0.13, 0.20)
    floor_mesh.material_override = mat
    floor_body.add_child(floor_mesh)
    var ground_collision := CollisionShape3D.new()
    var ground_box := BoxShape3D.new()
    ground_box.size = Vector3(50, 0.2, 50)
    ground_collision.shape = ground_box
    ground_collision.position.y = -0.1
    floor_body.add_child(ground_collision)

    actor = CharacterBody3D.new()
    actor.name = "ControllableCharacter"
    actor.position = Vector3(0, 1.1, 0)
    add_child(actor)
    var col := CollisionShape3D.new()
    var capsule := CapsuleShape3D.new()
    capsule.radius = 0.4
    capsule.height = 2.0
    col.shape = capsule
    actor.add_child(col)

    var packed := load("res://character.glb") as PackedScene
    if packed == null:
        push_error("GLB import failed. Open the generated project in the Godot editor to import.")
        return
    var visual := packed.instantiate() as Node3D
    if visual == null:
        push_error("GLB has no Node3D root")
        return
    visual.name = "ImportedGLB_Prototype"
    actor.add_child(visual)
    # Model-specific scale, pivot, orientation and rig still need review.

    var sun := DirectionalLight3D.new()
    sun.rotation_degrees = Vector3(-55, -35, 0)
    sun.light_energy = 1.5
    add_child(sun)
    var world := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color(0.035, 0.05, 0.085)
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color(0.5, 0.63, 0.9)
    env.ambient_light_energy = 0.8
    world.environment = env
    add_child(world)

    camera = Camera3D.new()
    camera.current = true
    camera.fov = 70
    add_child(camera)
    _update_camera()

func _unhandled_input(event: InputEvent) -> void:
    if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_RIGHT:
        look_active = event.pressed
        Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if look_active else Input.MOUSE_MODE_VISIBLE
    elif event is InputEventMouseMotion and look_active:
        pivot_yaw -= event.relative.x * 0.005
        pivot_pitch = clamp(pivot_pitch - event.relative.y * 0.005, -0.75, 0.65)
    elif event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
        look_active = false
        Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func _physics_process(delta: float) -> void:
    if actor == null:
        return
    var x := float(Input.is_key_pressed(KEY_D)) - float(Input.is_key_pressed(KEY_A))
    var z := float(Input.is_key_pressed(KEY_S)) - float(Input.is_key_pressed(KEY_W))
    var input_dir := Vector2(x, z).normalized()
    var move_dir := Basis(Vector3.UP, pivot_yaw) * Vector3(input_dir.x, 0, input_dir.y)
    actor.velocity.x = move_dir.x * SPEED
    actor.velocity.z = move_dir.z * SPEED
    if not actor.is_on_floor():
        actor.velocity.y -= 9.8 * delta
    elif Input.is_key_pressed(KEY_SPACE):
        actor.velocity.y = JUMP_VELOCITY
    else:
        actor.velocity.y = 0.0
    actor.move_and_slide()
    if input_dir.length() > 0.01:
        actor.rotation.y = atan2(move_dir.x, move_dir.z) + PI
    _update_camera()

func _update_camera() -> void:
    if camera == null or actor == null:
        return
    var target := actor.global_position + Vector3.UP * 0.9
    var offset := Basis(Vector3.UP, pivot_yaw) * Vector3(0, 1.5 + sin(pivot_pitch) * 3.0, 5.5 * cos(pivot_pitch))
    camera.global_position = target + offset
    camera.look_at(target, Vector3.UP)
'''

PROJECT = '''config_version=5

[application]
config/name="Aeryvex Character Gameplay Prototype"
run/main_scene="res://Main.tscn"

[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
'''

SCENE = '''[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://main.gd" id="1"]

[node name="AeryvexCharacterPrototype" type="Node3D"]
script = ExtResource("1")
'''


def create_preview(glb, output):
    glb = Path(glb).expanduser().resolve(strict=True)
    output = Path(output).expanduser().absolute()
    if not glb.is_file() or glb.suffix.lower() != ".glb":
        raise ValueError("Input must be an existing .glb file")
    # Read the binary GLB signature and total declared file length.
    with glb.open("rb") as f:
        header = f.read(12)
    if len(header) != 12 or header[:4] != b"glTF":
        raise ValueError("Input is not a valid GLB header")
    magic, version, length = struct.unpack("<4sII", header)
    if version != 2 or length != glb.stat().st_size:
        raise ValueError("Invalid GLB version or byte length")
    if output.exists():
        raise FileExistsError("Output already exists; choose a NEW empty project path")
    if output.resolve() == glb.parent or output.resolve() in glb.parents:
        raise ValueError("Output must not be a source parent")
    output.mkdir(parents=True, exist_ok=False)
    try:
        shutil.copyfile(glb, output / "character.glb")
        (output / "project.godot").write_text(PROJECT)
        (output / "Main.tscn").write_text(SCENE)
        (output / "main.gd").write_text(MAIN_GD)
        (output / "README.txt").write_text(
            "Aeryvex 3D character mesh preview (NOT rigged or approved).\n"
            "Open this folder in Godot 4.2+ and press F6/F5 to play.\n"
            "WASD: move; Space: jump; hold right mouse: orbit; Esc: release.\n"
            "This is an isolated prototype. Review orientation, scale, appearance, "
            "collisions and animation before importing into your actual game.\n"
        )
    except Exception:
        shutil.rmtree(output)
        raise
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glb", required=True, help="Existing GLB file")
    parser.add_argument("--output", required=True, help="NEW preview project directory")
    args = parser.parse_args()
    print("Created isolated Godot preview:", create_preview(args.glb, args.output))


if __name__ == "__main__":
    main()
