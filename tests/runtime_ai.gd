extends SceneTree
# Go 5 deterministic gameplay tests; requires Godot 3.5/3.6 runtime.
const Brain = preload("res://scripts/EnemyBrain.gd")
var failures=[]
func _init():
    call_deferred("_run")
func check(condition, label):
    if condition:
        print("PASS: ", label)
    else:
        failures.append(label)
        printerr("FAIL: ", label)
func _run():
    check(Brain.NAMES.size() == 3, "three AI difficulty presets")
    check(Brain.reaction_delay(2) < Brain.reaction_delay(1) and Brain.reaction_delay(1) < Brain.reaction_delay(0), "higher skill reacts sooner")
    check(Brain.next_attack_delay(0) > Brain.next_attack_delay(2), "rookie attacks less often")
    check(Brain.defense_for_threat(2, 15.0, true, 0.0) == "dodge", "low guard causes a dodge")
    check(Brain.defense_for_threat(2, 15.0, false, 0.0) == "none", "can't dodge without budget")
    check(Brain.defense_for_threat(2, 80.0, true, 0.0) == "parry", "master has timed parry option")
    check(Brain.defense_for_threat(0, 80.0, true, 0.45) == "guard", "rookie often guards")
    check(Brain.attack_for_opening(2, 3.0, 100, "idle", false, 0) == "", "AI won't swing out of range")
    check(Brain.attack_for_opening(2, 2.3, 100, "windup", false, 0) == "", "AI won't stack attacks")
    check(Brain.attack_for_opening(2, 2.3, 11, "idle", false, 0) == "", "AI respects stamina")
    check(Brain.attack_for_opening(2, 2.3, 100, "idle", true, 0) == "", "AI won't strike while guarding")
    check(Brain.attack_for_opening(2, 2.3, 100, "idle", false, 0.10) == "heavy", "master uses heavy attacks")
    check(Brain.attack_for_opening(0, 2.3, 20, "idle", false, 0.10) == "light", "low guard avoids heavy attack")
    check(Brain.desired_distance(10.0, true) > Brain.desired_distance(90.0, false), "guard-depleted defender retreats")
    var chase=Brain.steering(Vector3(0,0,5), Vector3.ZERO, 2.2, 1.0)
    check(chase.z < 0.0, "AI chases distant target")
    var retreat=Brain.steering(Vector3(0,0,0.4), Vector3.ZERO, 2.2, 1.0)
    check(retreat.z > 0.0, "AI backs out of too-close range")
    check(abs(Brain.steering(Vector3.ZERO,Vector3.ZERO,2.2,1.0).length()) <= 1.01, "overlap steering stays finite")
    var arena=load("res://Main.tscn").instance()
    get_root().add_child(arena)
    check(InputMap.has_action("difficulty_change"), "difficulty control bound")
    check(arena.ai_difficulty >= 0 and arena.ai_difficulty <= 2, "saved difficulty always valid")
    arena._spawn()
    check(arena.ai_reaction_time == 0.0 and not arena.ai_saw_windup and not arena.ai_reacted, "AI reaction state resets between matches")
    arena.player.translation=Vector3(0,0,0)
    arena.enemy.translation=Vector3(0,0,-2)
    arena.ai_dodge_cooldown=0.0
    arena.stamina[1]=100.0
    check(arena._enemy_dodge(), "AI evasive action executes")
    check(arena.invuln[1] > 0.0 and arena.stamina[1] < 100.0, "dodge grants limited invulnerability and spends guard")
    check(not arena._enemy_dodge(), "dodge cooldown prevents spam")
    arena._spawn()
    arena.ai_difficulty=2
    arena.ai_clock=0.0
    arena.player.translation=Vector3(0,0,0)
    arena.enemy.translation=Vector3(0,0,-2.1)
    var pos_before=arena.enemy.translation
    arena._run_enemy(0.1)
    check(arena.enemy.translation.distance_to(pos_before)>0.001,"opponent strafes instead of standing still")
    check(arena.enemy_move_speed>0.0,"enemy movement animates legs")
    arena.queue_free()
    print("AI ENGINE TEST COMPLETE, failures: ", failures.size())
    quit(0 if failures.empty() else 1)
