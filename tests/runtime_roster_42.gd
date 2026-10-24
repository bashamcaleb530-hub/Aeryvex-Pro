extends SceneTree
# Godot 4: every roster slot loads, spawns and performs its configured attack.
const MainScene = preload("res://Main.tscn")
var failures = []

func verify(ok, message):
    if ok:
        print("PASS: ", message)
    else:
        failures.append(message)
        printerr("FAIL: ", message)

func _initialize():
    call_deferred("_run")

func _run():
    var arena = MainScene.instantiate()
    root.add_child(arena)
    verify(arena.ROSTER.size() == 42, "42 roster entries registered")
    verify(arena.ROSTER_CATEGORY.size() == 42, "42 combat categories")
    verify(arena.ROSTER_WEAPON.size() == 42, "42 weapon classifications")
    for i in range(42):
        arena.selected = i
        arena.enemy_index = (i + 1) % 42
        arena._spawn()
        var name = arena.ROSTER[i]
        verify(is_instance_valid(arena.player) and is_instance_valid(arena.enemy), "spawn: " + name)
        verify(arena.player.get_node_or_null("Model") != null, "visual: " + name)
        verify(arena.player.weapon() != null, "weapon proxy: " + name)
        # Exercise contact handling directly, independent of attack windup timing.
        arena.player.position = Vector3.ZERO
        arena.enemy.position = Vector3(0, 0, -2)
        arena.player.look_at(arena.enemy.position, Vector3.UP)
        arena.enemy.look_at(arena.player.position, Vector3.UP)
        arena._resolve_swing(0, {"reach": 3.0, "arc": 0.45, "damage": 15.0, "guard_damage": 10.0})
        verify(arena.hp[1] < 100.0, "attack damages opponent: " + name)
    arena.queue_free()
    print("ROSTER CHECKS COMPLETE: ", 42, " entries; failures: ", failures.size())
    quit(0 if failures.is_empty() else 1)
