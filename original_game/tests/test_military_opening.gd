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
    check(not game.call("request_council_review"), "Council cannot be skipped")
    check(not game.call("try_trial"), "Trial cannot be cleared from a distance")
    for i in range(10):
        var station: Node3D = game.get("stations")[i]
        game.get("hero").position = station.position
        check(game.call("try_trial"), "Trial %d requires reaching the location" % (i + 1))
    check(game.get("completed_count") == 10, "All ten opening challenges counted")
    check(game.get("score") == 1000, "Earned merit recorded")
    check(game.get("admission").stage == "council_review", "Purple recommendation reaches Council")
    check(game.call("request_council_review"), "Council formally approves admission")
    check(game.get("admission").admitted(), "Candidate becomes military warrior")
    check(not game.call("request_council_review"), "Cannot replay approval for rewards")
    print("MILITARY OPENING: ", "PASS" if failures == 0 else "%d FAILED" % failures)
    quit(0 if failures == 0 else 1)
