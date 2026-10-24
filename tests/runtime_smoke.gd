extends SceneTree
# Run with Godot 3.5/3.6 headless/editor binary:
# godot --no-window --path . -s res://tests/runtime_smoke.gd
# (On some Linux packages the binary is named godot3.)

var failures = []

func _check(condition, description):
    if condition:
        print("PASS: ", description)
    else:
        failures.append(description)
        printerr("FAIL: ", description)

func _init():
    call_deferred("_run_tests")

func _run_tests():
    var scene = load("res://Main.tscn").instance()
    get_root().add_child(scene)
    _check(is_instance_valid(scene.player), "fighter spawned")
    _check(is_instance_valid(scene.enemy), "opponent spawned")
    _check(InputMap.has_action("sprint"), "sprint registered")
    _check(InputMap.has_action("camera_up"), "camera tilt registered")
    _check(InputMap.has_action("recenter_camera"), "camera reset registered")

    scene.yaw = 0.0
    var forward = scene._world_move(Vector2(0, -1))
    _check(abs(forward.z + 1.0) < 0.001, "forward movement aims at -Z")
    scene.yaw = PI / 2.0
    var turned = scene._world_move(Vector2(0, -1))
    _check(abs(turned.x + 1.0) < 0.001, "movement rotates with camera")
    scene.yaw = 0.0
    var start = scene.player.translation
    scene._step_player(0.1, Vector2(0, -1), false)
    _check(scene.player.translation.z < start.z, "forward input moves the fighter")

    scene.block = false
    scene.stamina[0] = 100.0
    scene._step_player(0.1, Vector2(0, -1), true)
    _check(scene.stamina[0] < 100.0, "sprinting consumes guard")
    var guard_after_sprint = scene.stamina[0]
    scene.block = true
    scene._step_player(0.1, Vector2(0, -1), true)
    _check(abs(scene.stamina[0] - guard_after_sprint) < 0.001, "blocking prevents sprint")

    var bounded = scene._clamp_arena(Vector3(99, 10, -99))
    _check(abs(bounded.x - 13.0) < 0.001 and abs(bounded.z + 13.0) < 0.001 and abs(bounded.y) < 0.001, "arena boundaries enforced")
    scene.camera_pitch = -10.0
    scene._orbit_camera(0.0)
    _check(scene.camera_pitch >= deg2rad(10.0), "camera pitch lower bound enforced")
    scene.camera_pitch = 10.0
    scene._orbit_camera(0.0)
    _check(scene.camera_pitch <= deg2rad(65.0), "camera pitch upper bound enforced")

    scene._spawn()
    _check(scene.move_velocity.length() < 0.001, "restart clears movement momentum")
    _check(scene.hp[0] == 100.0 and scene.hp[1] == 100.0, "restart resets health")
    scene.queue_free()
    print("SMOKE CHECKS COMPLETE; failures: ", failures.size())
    quit(0 if failures.empty() else 1)
