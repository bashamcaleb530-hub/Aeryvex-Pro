extends SceneTree

# Run: godot --headless --path original_game --script res://tests/test_character_arena.gd
var failures := 0

func _initialize() -> void:
    call_deferred("_run")

func _assert_true(condition: bool, message: String) -> void:
    if condition:
        print("PASS: ", message)
    else:
        failures += 1
        push_error("FAIL: " + message)

func _run() -> void:
    var scene = load("res://CharacterArena.tscn")
    _assert_true(scene != null, "Character Arena scene loads")
    if scene == null:
        quit(1)
        return
    var arena: Node = scene.instantiate()
    root.add_child(arena)
    await process_frame
    _assert_true(arena.get("roster").size() >= 20, "Character roster has 20 entries")
    _assert_true(arena.get("current") == 0, "First ruler selected")
    _assert_true(arena.get("target_health") == 100.0, "Target begins at 100 HP")
    arena.set("attack_timer", 0.0)
    arena.call("_attack_target")
    _assert_true(arena.get("target_health") == 75.0, "Attack reduces target HP by 25")
    for i in range(3):
        arena.set("attack_timer", 0.0)
        arena.call("_attack_target")
    _assert_true(arena.get("target_health") == 0.0, "Four hits defeat target")
    _assert_true(arena.get("target_hits") == 4, "Hit counter tracks strikes")
    _assert_true(not arena.get("training_target").visible, "Target hides on defeat")
    arena.call("_select", 1)
    _assert_true(arena.get("current") == 1, "Ruler switching advances selection")
    _assert_true(arena.get("target_health") == 100.0, "Ruler switching resets target")
    for i in range(10):
        arena.call("_select", i)
        _assert_true(arena.get("current") == i, "Ruler index %d selectable" % i)
    _assert_true(arena.get("target_health") == 100.0, "Target remains initialized")
    print("COMBAT TEST RESULT: ", "PASS" if failures == 0 else "%d FAILED" % failures)
    quit(0 if failures == 0 else 1)
