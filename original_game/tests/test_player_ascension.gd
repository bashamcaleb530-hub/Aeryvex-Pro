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
    check(game.rank_name() == "Teenage Applicant", "Player begins as a teenage civilian")
    check(not game.mark_warrior_trial("defend_aether_settlement"), "No military promotions before admission")
    check(not game.admission.begin_green_training(), "Entry trials cannot be skipped")
    for trial in game.admission.ENTRY_TRIALS:
        check(game.admission.complete_challenge(trial), "Complete difficult entrance trial: " + trial)
    check(game.admission.begin_green_training(), "Begin training under green Adept")
    check(not game.admission.face_purple_master(), "Cannot skip green-ranked training")
    for trial in game.admission.GREEN_TRAINING:
        check(game.admission.complete_challenge(trial), "Complete green training: " + trial)
    check(game.admission.face_purple_master(), "Earn examination by purple Master")
    check(not game.admission.master_recommendation(), "Purple examiner demands all tests")
    for trial in game.admission.PURPLE_EXAM:
        check(game.admission.complete_challenge(trial), "Complete purple Master examination: " + trial)
    check(game.admission.master_recommendation(), "Purple Master recommends candidate")
    check(not game.admission.decide_admission(), "Council approval cannot be bypassed")
    for seat in game.admission.COUNCIL_SEATS:
        check(game.admission.council_vote(seat, true), "Approval from " + seat)
    check(game.admission.decide_admission(), "Grand Masters and Orion approve military enrollment")
    check(game.rank_name() == "Warrior" and game.lightning_color() == "blue", "Admitted as blue-lightning warrior")
    check(not game.become_master(), "Master requires warrior achievements")
    for trial in ["defend_aether_settlement", "survive_first_war_gate", "complete_warrior_oath"]:
        check(game.mark_warrior_trial(trial), "Earn warrior trial " + trial)
    check(game.become_temple_guard(), "Ascend to yellow-lightning Temple Guard")
    check(game.lightning_color() == "yellow", "Temple Guard has yellow lightning")
    check(not game.become_adept(), "Adept promotion requires temple duties")
    for trial in ["defend_temple", "protect_yellow_flame"]:
        check(game.mark_temple_trial(trial), "Earn temple trial " + trial)
    check(game.become_adept(), "Ascend to green-lightning Adept")
    check(game.lightning_color() == "green", "Adept has green lightning")
    check(not game.become_master(), "Master requires adept achievements")
    for trial in ["awaken_green_lightning", "restore_war_gate"]:
        check(game.mark_adept_trial(trial), "Earn adept trial " + trial)
    check(game.become_master(), "Ascend to purple-lightning Master")
    check(game.lightning_color() == "purple", "Master has purple lightning")
    check(not game.become_grand_master(), "Grand Master requires further achievements")
    for trial in ["master_multicolor_discipline", "protect_celestial_arch", "win_master_duel"]:
        check(game.mark_master_trial(trial), "Earn master trial " + trial)
    check(game.become_grand_master(), "Ascend to multicolor-lightning Grand Master")
    check(game.lightning_color() == "multicolor", "Grand Master has multicolor lightning")
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
    check(game.lightning_color() == "rainbow", "Player wields exclusive supreme rainbow lightning")
    check(game.summary()["orion_form"] == "rainbow_spirit", "Orion endures as Rainbow Lightning Spirit")
    check(not game.receive_orions_final_gift(), "Supreme transfer cannot repeat")
    print("PLAYER ASCENSION TEST: ", "PASS" if failures == 0 else "%d FAILED" % failures)
    quit(0 if failures == 0 else 1)
