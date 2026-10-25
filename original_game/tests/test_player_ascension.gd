extends SceneTree
var failures := 0
func _initialize() -> void:
    call_deferred("_run")
func check(condition: bool, label: String) -> void:
    if condition:
        print("PASS: ", label)
    else:
        failures += 1
        push_error("FAIL: " + label)
func _run() -> void:
    var game = load("res://PlayerAscension.gd").new()
    check(game.rank_name() == "Warrior" and game.lightning_color() == "blue", "Start as blue-lightning warrior")
    check(not game.become_master(), "Master requires warrior achievements")
    for trial in ["defend_aether_settlement", "survive_first_war_gate", "complete_warrior_oath"]:
        check(game.mark_warrior_trial(trial), "Earn warrior trial " + trial)
    check(game.become_master(), "Ascend to purple-lightning Master")
    check(game.lightning_color() == "purple", "Master has purple lightning")
    check(not game.become_grand_master(), "Grand Master requires further achievements")
    for trial in ["master_rainbow_discipline", "protect_celestial_arch", "win_master_duel"]:
        check(game.mark_master_trial(trial), "Earn master trial " + trial)
    check(game.become_grand_master(), "Ascend to rainbow-lightning Grand Master")
    check(game.lightning_color() == "rainbow", "Grand Master has rainbow lightning")
    check(not game.receive_orions_final_gift(), "Cannot skip to Supreme")
    check(not game.save_orion(), "Cannot rescue before soul drain")
    for i in range(9):
        game.powers.complete_ritual_step(game.powers.RITUAL_STEPS[i])
    check(not game.witness_drakthar_drain(), "Nine trials cannot initiate drain")
    game.powers.complete_ritual_step(game.powers.RITUAL_STEPS[9])
    check(game.witness_drakthar_drain(), "All ten enable Drakthar's soul-draining confrontation")
    check(not game.kill_drakthar(), "Rescue must precede final battle")
    check(game.save_orion(), "Player rescues Orion")
    check(not game.receive_orions_final_gift(), "Player must defeat Dark Lord first")
    check(game.kill_drakthar(), "Player defeats Supreme Dark Lord")
    check(game.receive_orions_final_gift(), "Dying Orion transfers supreme power")
    check(game.rank_name() == "Supreme Grand Master", "Player becomes Supreme Grand Master")
    check(game.lightning_color() == "supreme_rainbow", "Player wields supreme rainbow lightning")
    check(game.summary()["orion_form"] == "rainbow_spirit", "Orion endures as Rainbow Lightning Spirit")
    check(not game.receive_orions_final_gift(), "Supreme transfer cannot repeat")
    print("PLAYER ASCENSION TEST: ", "PASS" if failures == 0 else "%d FAILED" % failures)
    quit(0 if failures == 0 else 1)
