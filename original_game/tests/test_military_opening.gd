extends SceneTree
var failures := 0
func _initialize() -> void:
    call_deferred("_run")
func check(ok: bool, label: String) -> void:
    if ok:
        print("PASS: ", label)
    else:
        failures += 1
        push_error("FAIL: " + label)
func _run() -> void:
    var scene = load("res://MilitaryOpening.tscn")
    check(scene != null, "Military opening loads")
    if scene == null:
        quit(1)
        return
    var game: Node3D = scene.instantiate()
    root.add_child(game)
    await process_frame
    check(game.get("admission").stage == "teenage_applicant", "Starts as teenage applicant")
    check(game.get("completed_count") == 0, "No trials completed for free")
    check(game.get("hero").has_node("ApprovedHeroAppearance"), "Hero uses approved-reference/model importer")
    check(game.get("hero").get_children().size() >= 1, "Hero has selectable visual representation")
    check(not game.call("request_council_review"), "Council cannot be skipped")
    check(not game.call("try_trial"), "Trial cannot be cleared from a distance")
    # Failure and retry keep all prior cleared missions.
    var missions: RefCounted = game.get("missions")
    check(missions.MISSIONS.size() == 10, "Ten distinct mission stages defined")
    check(game.get("hazard") != null, "Visible lightning hazard created")
    check(game.get("opponent") != null, "Visible sparring opponent created")
    check(game.get("hazard").visible, "Storm mission displays hazard")
    check(not game.get("opponent").visible, "Storm mission hides sparring opponent")
    check(not game.call("_attempt_strike", false), "Cannot score combat hits in storm mission")
    for i in range(10):
        var station: Node3D = game.get("stations")[i]
        game.get("hero").position = station.position
        check(not game.call("try_trial"), "Mission %d cannot skip gameplay objective" % (i + 1))
        if i == 1:
            check(game.get("opponent").visible, "Martial arts mission displays opponent")
            game.get("hero").position = Vector3(-6, 0, -6)
            check(not game.call("_attempt_strike", false), "Martial hits require melee proximity")
            game.get("hero").position = station.position
        if i == 2:
            check(game.get("opponent").visible, "Weapons mission displays opponent")
        var m: Dictionary = missions.current()
        var kind: String = m["type"]
        check(m["phases"].size() == 3, "Mission %d has three distinct acts" % (i+1))
        check(int(m["goal"]) >= 30, "Mission %d requires extended gameplay" % (i+1))
        if i == 0:
            missions.take_damage(100)
            check(missions.failed, "Lethal storm hit fails the mission")
            check(missions.restart_after_failure(), "Retry restores the current mission")
            check(not missions.failed and missions.hero_health == 100, "Health restored after retry")
        for hit in range(int(m["goal"])):
            if kind == "dodge":
                check(missions.dodge_pulse(true), "Dodge objective step %d" % (hit+1))
            elif kind == "defense":
                missions.tick(1.0, true)
            else:
                check(missions.strike(kind == "weapons"), "Combat objective step %d" % (hit+1))
                missions.tick(0.3,true)
        check(missions.phase_index() == 2, "Mission final act reached")
        check(missions.is_complete(), "Mission %d objective complete" % (i+1))
        check(game.call("try_trial"), "Mission %d completed at gateway" % (i+1))
        check(game.get("completed_count") == i+1, "Mission count increments")
    # Checkpoints allow a lengthy trial to resume at the last reached act.
    var trials = load("res://AetherTrialMissions.gd").new()
    check(trials.checkpoint_progress == 0, "First act has no checkpoint")
    for hit in range(14):
        trials.dodge_pulse(true)
    check(trials.phase_index() == 1, "Act two is unlocked by actual progress")
    check(trials.checkpoint_progress == trials.act_start(1), "Act two checkpoint saved")
    trials.take_damage(100)
    check(trials.restart_after_failure(), "Can retry after failing the second act")
    check(trials.progress == trials.act_start(1), "Retry resumes at act two checkpoint")
    check(trials.hero_health == 100, "Retry restores health")
    trials.reset_attempt()
    check(trials.checkpoint_progress == 0, "Fresh mission resets all checkpoints")
    var defense_trials = load("res://AetherTrialMissions.gd").new()
    defense_trials.mission_index = 3
    defense_trials.tick(30.0, true)
    check(defense_trials.phase_index() == 1, "Defense mission reaches second act")
    defense_trials.take_damage(100)
    check(defense_trials.restart_after_failure(), "Defense mission retry succeeds")
    check(defense_trials.progress == defense_trials.act_start(1), "Defense progress retains checkpoint")
    defense_trials.tick(1.0, true)
    check(defense_trials.progress > defense_trials.act_start(1), "Defense timer advances beyond checkpoint")
    check(game.get("completed_count") == 10, "All ten opening challenges counted")
    check(game.get("score") == 1000, "Earned merit recorded")
    check(game.get("admission").stage == "council_review", "Purple recommendation reaches Council")
    check(game.call("request_council_review"), "Council formally approves admission")
    check(game.get("admission").admitted(), "Candidate becomes military warrior")
    check(not game.call("request_council_review"), "Cannot replay approval for rewards")
    print("MILITARY OPENING: ", "PASS" if failures == 0 else "%d FAILED" % failures)
    quit(0 if failures == 0 else 1)
