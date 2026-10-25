extends RefCounted
class_name GrandMasterPowers

# Story-canon power rules. No ordinary attack can kill Orion.
# The soul theft ritual is deliberately gated by story events.
const POWERS := {
    0: {"name": "Orion Valen", "signature": "Spectrum Dominion", "ultimate": "Eternal Rainbow Judgment", "element": "rainbow", "damage": 95},
    12: {"name": "Maeryn Sol", "signature": "Infinite Gate Cascade", "ultimate": "Celestial Rift Collapse", "element": "rainbow", "damage": 80},
    13: {"name": "Thalen Orris", "signature": "Sevenfold Warstorm", "ultimate": "Grand Legion Tempest", "element": "rainbow", "damage": 85},
    14: {"name": "Ilyra Venn", "signature": "Prismatic Phantom", "ultimate": "A Thousand Hidden Bolts", "element": "rainbow", "damage": 78},
    15: {"name": "Selene Avaris", "signature": "Lifeweave Radiance", "ultimate": "Genesis Restoration Storm", "element": "rainbow", "damage": 72},
    6: {"name": "Drakthar Vex", "signature": "Crimson Dominion", "ultimate": "Crimson Cataclysm", "element": "red", "damage": 98},
    16: {"name": "Malveris Thorne", "signature": "Bloodfire Siege", "ultimate": "Worldbreaker Barrage", "element": "red", "damage": 86},
    17: {"name": "Nyssara Veil", "signature": "Scarlet Shadowfall", "ultimate": "Nightmare Eclipse", "element": "red", "damage": 80},
    18: {"name": "Korr Uldane", "signature": "Fourfold Ravager", "ultimate": "Crimson Warquake", "element": "red", "damage": 88},
    19: {"name": "Vaelith Sorn", "signature": "Blood Sigil Convergence", "ultimate": "Abyssal Rite", "element": "red", "damage": 83}
}
# Every trial is a campaign-scale achievement. Completing nine is insufficient.
const RITUAL_STEPS := [
    "unite_five_void_seals",
    "conquer_five_void_thrones",
    "extinguish_the_eternal_beacon",
    "survive_the_starless_abyss",
    "break_the_seven_prismatic_wards",
    "corrupt_the_first_celestial_arch",
    "defeat_the_four_grand_master_guardians",
    "bind_the_crimson_eclipse",
    "recover_the_lost_name_of_the_first_storm",
    "breach_rainbow_ascension"
]
var orion_form := "living" # living, rainbow_spirit, soul_captive
var successor_id := -1
var supreme_power_holder := 0
var ritual_flags := {}
var soul_theft_used := false

func describe(character_id: int) -> Dictionary:
    return POWERS.get(character_id, {}).duplicate(true)

func can_damage(target_id: int) -> bool:
    return target_id != 0 or orion_form == "soul_captive"

func resolve_attack(attacker_id: int, target_id: int, use_ultimate: bool = false) -> Dictionary:
    if not POWERS.has(attacker_id):
        return {"success": false, "reason": "Unknown grand master"}
    var move: Dictionary = POWERS[attacker_id]
    var label_name: String = move["ultimate"] if use_ultimate else move["signature"]
    if target_id == 0:
        return {"success": true, "ability": label_name, "damage": 0, "invulnerable": true,
            "reason": "Orion is invulnerable to ordinary attacks and ultimates"}
    return {"success": true, "ability": label_name,
        "damage": int(move["damage"]) * (2 if use_ultimate else 1),
        "invulnerable": false, "element": move["element"]}

func designate_successor(candidate_id: int) -> bool:
    if not POWERS.has(candidate_id) or candidate_id == 0 or candidate_id == 6:
        return false
    if candidate_id not in [12, 13, 14, 15]:
        return false
    successor_id = candidate_id
    return true

func perform_succession(candidate_id: int) -> bool:
    if orion_form != "living" or candidate_id != successor_id or candidate_id < 0:
        return false
    supreme_power_holder = candidate_id
    orion_form = "rainbow_spirit"
    return true

func complete_ritual_step(step: String) -> bool:
    if step not in RITUAL_STEPS:
        return false
    ritual_flags[step] = true
    return true

func can_steal_rainbow_soul(caster_id: int) -> bool:
    if caster_id != 6 or soul_theft_used:
        return false
    if orion_form not in ["living", "rainbow_spirit"]:
        return false
    for step in RITUAL_STEPS:
        if not ritual_flags.get(step, false):
            return false
    return true

func steal_rainbow_soul(caster_id: int) -> bool:
    if not can_steal_rainbow_soul(caster_id):
        return false
    soul_theft_used = true
    orion_form = "soul_captive"
    supreme_power_holder = 6
    return true

func outcome() -> Dictionary:
    return {"orion_form": orion_form, "successor_id": successor_id,
        "supreme_power_holder": supreme_power_holder, "ritual_ready": can_steal_rainbow_soul(6)}
