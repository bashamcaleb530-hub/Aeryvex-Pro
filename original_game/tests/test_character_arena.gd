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
    # Exercise actual keyboard event handling, not only internal combat functions.
    arena.set("attack_timer", 0.0)
    var space := InputEventKey.new()
    space.keycode = KEY_SPACE
    space.pressed = true
    arena.call("_input", space)
    _assert_true(arena.get("target_health") == 75.0, "SPACE performs lightning strike")
    arena.call("_input", space)
    _assert_true(arena.get("target_health") == 75.0, "Attack cooldown prevents repeated SPACE damage")
    var reset_key := InputEventKey.new()
    reset_key.keycode = KEY_T
    reset_key.pressed = true
    arena.call("_input", reset_key)
    _assert_true(arena.get("target_health") == 100.0, "T restores target health")
    _assert_true(arena.get("target_hits") == 0, "T resets hit count")
    var next_key := InputEventKey.new()
    next_key.keycode = KEY_RIGHT
    next_key.pressed = true
    arena.call("_input", next_key)
    _assert_true(arena.get("current") == 0, "RIGHT wraps from last ruler to first")
    var prev_key := InputEventKey.new()
    prev_key.keycode = KEY_LEFT
    prev_key.pressed = true
    arena.call("_input", prev_key)
    _assert_true(arena.get("current") == 9, "LEFT wraps from first ruler to last")
    # Active duel simulation: enemy hits player, shield reduces the damage.
    var duel_key := InputEventKey.new()
    duel_key.keycode = KEY_E
    duel_key.pressed = true
    arena.call("_input", duel_key)
    _assert_true(arena.get("duel_mode"), "E enables active enemy")
    var hp_before: float = arena.get("player_health")
    arena.call("_update_enemy", 1.5)
    _assert_true(arena.get("player_health") == hp_before - 15.0, "Enemy attack damages player")
    var shield_key := InputEventKey.new()
    shield_key.keycode = KEY_SHIFT
    shield_key.pressed = true
    arena.call("_input", shield_key)
    _assert_true(arena.get("shield_active"), "SHIFT activates shield")
    arena.call("_update_enemy", 1.5)
    _assert_true(arena.get("player_health") == hp_before - 20.0, "Shield reduces enemy damage")
    arena.call("_input", reset_key)
    _assert_true(arena.get("player_health") == 100.0, "T restores player HP")
    arena.call("_input", duel_key)
    _assert_true(not arena.get("duel_mode"), "E returns to training mode")
    # Approved canon: Orion's single staff transforms into two sword conduits.
    arena.call("_select", 0)
    var weapon: Node = arena.get("weapon_conduit")
    _assert_true(weapon.call("get_mode") == "supreme_staff", "Orion begins with supreme staff")
    var transform_key := InputEventKey.new()
    transform_key.keycode = KEY_F
    transform_key.pressed = true
    arena.call("_input", transform_key)
    _assert_true(weapon.call("get_mode") == "dual_swords", "F transforms Orion staff into dual swords")
    arena.call("_input", transform_key)
    _assert_true(weapon.call("get_mode") == "supreme_staff", "F reforms Orion dual swords into staff")
    arena.call("_select", 2)
    _assert_true(weapon.call("get_mode") == "dual_swords", "Thalen carries dual swords")
    arena.call("_input", transform_key)
    _assert_true(weapon.call("get_mode") == "dual_swords", "Thalen retains his dual swords")
    _assert_true(weapon.get_node("ConduitHandles").get_child_count() == 2, "Thalen has two separate handles")
    print("COMBAT TEST RESULT: ", "PASS" if failures == 0 else "%d FAILED" % failures)
    quit(0 if failures == 0 else 1)
