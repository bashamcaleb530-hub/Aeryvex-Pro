extends SceneTree
# Godot 3.6 test: godot3 --no-window --path . -s res://tests/runtime_combat.gd
# No runtime result should be claimed until this script is actually executed.
const Rules = preload("res://scripts/CombatRules.gd")
var failed = []

func _check(ok, label):
    if ok:
        print("PASS: ", label)
    else:
        failed.append(label)
        printerr("FAIL: ", label)

func _init():
    call_deferred("_run")

func _arrange(scene):
    scene._spawn()
    scene.player.translation = Vector3(0,0,0)
    scene.enemy.translation = Vector3(0,0,-2)
    scene.player.look_at(scene.enemy.translation, Vector3.UP)
    scene.enemy.look_at(scene.player.translation, Vector3.UP)

func _run():
    var arena = load("res://Main.tscn").instance()
    get_root().add_child(arena)
    var rules = Rules.new()
    _check(Rules.can_start("idle", 100, 25, 0, 0), "full energy allows a new heavy")
    _check(not Rules.can_start("windup", 100, 12, 0, 0), "no overlapping swings")
    _check(not Rules.can_start("idle", 10, 12, 0, 0), "insufficient energy refuses swing")
    _check(not Rules.can_start("idle", 100, 12, 0.2, 0), "stagger prevents swing")
    _check(not Rules.can_start("idle", 100, 12, 0, 0.2), "guard break prevents swing")
    _check(Rules.in_arc(Transform.IDENTITY, Vector3(0, 0, -2), 3, 0.45), "swing cone includes targets ahead")
    _check(not Rules.in_arc(Transform.IDENTITY, Vector3(0, 0, 2), 3, 0.45), "swing cone rejects targets behind")
    _check(not Rules.in_arc(Transform.IDENTITY, Vector3(0, 0, -4), 3, 0.45), "swing cone rejects targets beyond reach")
    var guarded = Rules.guard_result(30, 20, 90, true, false, false)
    _check(guarded["outcome"] == "block" and abs(guarded["hp_loss"]-2.4)<0.001 and guarded["guard_left"]==70, "ordinary block drains guard with chip damage")
    var parried = Rules.guard_result(30, 20, 90, true, true, false)
    _check(parried["outcome"] == "parry" and parried["hp_loss"] == 0 and parried["attacker_stagger"] > 0, "timed parry counters attacker")
    var broken = Rules.guard_result(32, 46, 10, true, false, false)
    _check(broken["outcome"] == "guard_break" and broken["guard_left"] == 0 and broken["defender_stagger"] > 0, "low guard causes guard break")
    var dodged = Rules.guard_result(32, 46, 10, true, false, true)
    _check(dodged["outcome"] == "dodge" and dodged["hp_loss"] == 0, "dodge immunity takes priority")

    _arrange(arena)
    _check(arena._attack(0, "light"), "light attack begins")
    _check(arena.hp[1] == 100, "no premature damage during windup")
    arena._advance_strike(0, 0.26)
    _check(arena.hp[1] == 82, "light hit lands on active frame")
    arena._advance_strike(0, 0.04)
    _check(arena.hp[1] == 82, "active frames cannot deal duplicate hits")
    _check(not arena._attack(0, "heavy"), "recovery rejects early attack")

    _arrange(arena)
    arena.ai_block = true
    arena.parry_window[1] = 0.24
    arena._attack(0, "light")
    arena._advance_strike(0, 0.26)
    _check(arena.hp[1] == 100 and arena.stagger[0] > 0, "parry cancels damage and staggers attacker")
    _check(not arena._attack(0, "light"), "parried attacker cannot instantly strike")

    _arrange(arena)
    arena.ai_block = true
    arena.stamina[1] = 10
    arena._attack(0, "heavy")
    arena._advance_strike(0, 0.49)
    _check(arena.guard_break[1] > 0 and arena.stamina[1] == 0, "heavy breaks depleted guard")

    _arrange(arena)
    arena.invuln[1] = 0.5
    arena._attack(0, "light")
    arena._advance_strike(0, 0.26)
    _check(arena.hp[1] == 100, "invulnerable defender avoids strike")

    _arrange(arena)
    arena.enemy.translation = Vector3(0,0,2)
    arena._attack(0, "light")
    arena._advance_strike(0, 0.26)
    _check(arena.hp[1] == 100, "back-facing attack does not hit")
    arena.queue_free()
    print("COMBAT TESTS COMPLETE; failures: ", failed.size())
    quit(0 if failed.empty() else 1)
