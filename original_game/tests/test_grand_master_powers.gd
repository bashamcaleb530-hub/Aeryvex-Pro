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
    verify(p.complete_ritual_step("void_seals_united"), "Five Void seals assembled")
    verify(p.complete_ritual_step("celestial_arch_corrupted"), "Celestial Arch corrupted")
    verify(not p.steal_rainbow_soul(6), "Two of three steps cannot steal soul")
    verify(p.complete_ritual_step("rainbow_ascension_open"), "Rainbow Ascension opened")
    verify(not p.steal_rainbow_soul(12), "Only Drakthar can perform theft")
    verify(p.steal_rainbow_soul(6), "Drakthar steals soul after all steps")
    verify(p.outcome()["orion_form"] == "soul_captive", "Orion soul becomes captive")
    verify(not p.steal_rainbow_soul(6), "Soul theft is single-use")
    var q = power_script.new()
    verify(not q.perform_succession(12), "Unchosen successor rejected")
    verify(q.designate_successor(12), "Maeryn selected as new supreme")
    verify(q.perform_succession(12), "Power transfers peacefully")
    verify(q.outcome()["orion_form"] == "rainbow_spirit", "Orion becomes Rainbow Lightning Spirit")
    verify(q.outcome()["supreme_power_holder"] == 12, "Successor receives supreme power")
    verify(not q.perform_succession(12), "Succession cannot happen twice")
    print("GRAND MASTER POWERS: ", "PASS" if fails == 0 else "%d FAILED" % fails)
    quit(0 if fails == 0 else 1)
