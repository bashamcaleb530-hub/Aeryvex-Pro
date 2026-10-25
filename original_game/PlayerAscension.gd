extends RefCounted
class_name PlayerAscension

# Narrative rank order is irreversible. The player is a unique hero (ID 20).
const WARRIOR := 0
const MASTER := 1
const GRAND_MASTER := 2
const SUPREME_GRAND_MASTER := 3
const RANK_NAMES := ["Warrior", "Master", "Grand Master", "Supreme Grand Master"]
const LIGHTNING := ["blue", "purple", "rainbow", "supreme_rainbow"]
var rank := WARRIOR
var earned_trials := {}
var story_events := {}
var powers: GrandMasterPowers

func _init() -> void:
    powers = GrandMasterPowers.new()

func rank_name() -> String:
    return RANK_NAMES[rank]

func lightning_color() -> String:
    return LIGHTNING[rank]

func mark_warrior_trial(trial: String) -> bool:
    if trial not in ["defend_aether_settlement", "survive_first_war_gate", "complete_warrior_oath"]:
        return false
    earned_trials[trial] = true
    return true

func become_master() -> bool:
    if rank != WARRIOR:
        return false
    for item in ["defend_aether_settlement", "survive_first_war_gate", "complete_warrior_oath"]:
        if not earned_trials.get(item, false):
            return false
    rank = MASTER
    return true

func mark_master_trial(trial: String) -> bool:
    if rank != MASTER or trial not in ["master_rainbow_discipline", "protect_celestial_arch", "win_master_duel"]:
        return false
    earned_trials[trial] = true
    return true

func become_grand_master() -> bool:
    if rank != MASTER:
        return false
    for item in ["master_rainbow_discipline", "protect_celestial_arch", "win_master_duel"]:
        if not earned_trials.get(item, false):
            return false
    rank = GRAND_MASTER
    return true

func witness_drakthar_drain() -> bool:
    if rank != GRAND_MASTER:
        return false
    for trial in powers.RITUAL_STEPS:
        if not powers.ritual_flags.get(trial, false):
            return false
    if not powers.begin_soul_drain(6):
        return false
    story_events["orion_drain_witnessed"] = true
    return true

func save_orion() -> bool:
    if rank != GRAND_MASTER or not story_events.get("orion_drain_witnessed", false):
        return false
    if not powers.rescue_orion():
        return false
    story_events["orion_saved"] = true
    return true

func kill_drakthar() -> bool:
    if rank != GRAND_MASTER or not story_events.get("orion_saved", false):
        return false
    if not powers.defeat_drakthar():
        return false
    story_events["drakthar_killed"] = true
    return true

func receive_orions_final_gift() -> bool:
    if rank != GRAND_MASTER or not story_events.get("drakthar_killed", false):
        return false
    if not powers.designate_successor(20):
        return false
    if not powers.perform_succession(20):
        return false
    rank = SUPREME_GRAND_MASTER
    story_events["orion_becomes_rainbow_spirit"] = true
    return true

func summary() -> Dictionary:
    return {"rank": rank_name(), "lightning": lightning_color(), "supreme_holder": powers.supreme_power_holder,
        "orion_form": powers.orion_form, "events": story_events.duplicate(true)}
