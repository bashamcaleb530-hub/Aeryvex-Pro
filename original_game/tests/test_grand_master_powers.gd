extends SceneTree

var fails := 0

func _initialize() -> void:
    call_deferred("_run")

func verify(ok: bool, label: String) -> void:
    if ok:
        print("PASS: ", label)
    else:
        fails += 1
        push_error("FAIL: " + label)

func _run() -> void:
    var power_script = load("res://GrandMasterPowers.gd")
    verify(power_script != null, "Power script loads")
    if power_script == null:
        quit(1)
        return
    var p = power_script.new()
    verify(p.POWERS.size() == 10, "Ten unique ruler powers")
    for id in p.POWERS:
        verify(p.resolve_attack(id, 13, true).get("damage", 0) > 100, "Grand master %d has powerful ultimate" % id)
        verify(p.resolve_attack(id, 0, true).get("damage", -1) == 0, "Orion withstands master %d ultimate" % id)
    verify(not p.steal_rainbow_soul(6), "Soul theft blocked without ritual")
    verify(not p.complete_ritual_step("shortcut"), "Unknown ritual shortcut blocked")
    verify(p.RITUAL_STEPS.size() == 10, "Exactly ten near-impossible ritual trials")
    for i in range(9):
        verify(p.complete_ritual_step(p.RITUAL_STEPS[i]), "Trial %d completed" % (i + 1))
    verify(not p.steal_rainbow_soul(6), "Nine trials are not enough")
    verify(p.complete_ritual_step(p.RITUAL_STEPS[9]), "Final tenth trial completed")
    verify(not p.steal_rainbow_soul(12), "Only Drakthar can perform theft")
    verify(p.begin_soul_drain(6), "Drakthar begins draining Orion after ten trials")
    verify(p.steal_rainbow_soul(6), "Uninterrupted drain can capture Orion soul")
    verify(p.outcome()["orion_form"] == "soul_captive", "Orion soul becomes captive")
    verify(not p.steal_rainbow_soul(6), "Soul theft is single-use")
    var q = power_script.new()
    verify(not q.perform_succession(20), "Unchosen player cannot inherit supreme power")
    verify(not q.designate_successor(12), "Existing Grand Master cannot replace player")
    verify(q.designate_successor(20), "Player is designated successor")
    verify(not q.perform_succession(20), "Gift denied before Orion is rescued and Drakthar defeated")
    for trial in q.RITUAL_STEPS:
        q.complete_ritual_step(trial)
    verify(q.begin_soul_drain(6), "Drakthar begins dangerous soul drain")
    verify(q.rescue_orion(), "Player rescues dying Orion")
    verify(not q.steal_rainbow_soul(6), "Drakthar cannot steal soul after rescue")
    verify(not q.perform_succession(20), "Rescue alone cannot trigger succession")
    verify(q.defeat_drakthar(), "Player defeats Drakthar")
    verify(q.perform_succession(20), "Orion gifts supreme power to player")
    verify(q.outcome()["orion_form"] == "rainbow_spirit", "Orion becomes Rainbow Lightning Spirit")
    verify(q.outcome()["supreme_power_holder"] == 20, "Player becomes supreme ruler")
    verify(not q.perform_succession(20), "Succession happens only once")
    print("GRAND MASTER POWERS: ", "PASS" if fails == 0 else "%d FAILED" % fails)
    quit(0 if fails == 0 else 1)
