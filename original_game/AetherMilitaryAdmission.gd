extends RefCounted
class_name AetherMilitaryAdmission

# Opening chapter: teenage civilian applicant, not yet a military warrior.
const ENTRY_TRIALS := [
    "survive_the_storm_labyrinth",
    "save_fellow_candidates",
    "seal_unstable_celestial_arch",
    "hold_the_last_defense"
]
const GREEN_TRAINING := [
    "control_blue_current",
    "master_guard_stances",
    "survive_adept_sparring"
]
const PURPLE_EXAM := [
    "resist_purple_lightning",
    "win_without_harming_civilians",
    "demonstrate_discipline"
]
const COUNCIL_SEATS := ["maeryn_sol", "thalen_orris", "ilyra_venn", "selene_avaris", "orion_valen"]

var stage := "teenage_applicant"
var completed := {}
var purple_master_recommended := false
var council_votes := {}
var application_denied := false

func complete_challenge(key: String) -> bool:
    var permitted: Array = []
    if stage == "teenage_applicant":
        permitted = ENTRY_TRIALS
    elif stage == "green_adept_training":
        permitted = GREEN_TRAINING
    elif stage == "purple_master_exam":
        permitted = PURPLE_EXAM
    if key not in permitted or application_denied:
        return false
    completed[key] = true
    return true

func _finished(tasks: Array) -> bool:
    for key in tasks:
        if not completed.get(key, false):
            return false
    return true

func begin_green_training() -> bool:
    if stage != "teenage_applicant" or not _finished(ENTRY_TRIALS):
        return false
    stage = "green_adept_training"
    return true

func face_purple_master() -> bool:
    if stage != "green_adept_training" or not _finished(GREEN_TRAINING):
        return false
    stage = "purple_master_exam"
    return true

func master_recommendation() -> bool:
    if stage != "purple_master_exam" or not _finished(PURPLE_EXAM):
        return false
    purple_master_recommended = true
    stage = "council_review"
    return true

func council_vote(seat: String, approve: bool) -> bool:
    if stage != "council_review" or not purple_master_recommended or seat not in COUNCIL_SEATS:
        return false
    council_votes[seat] = approve
    return true

func decide_admission() -> bool:
    if stage != "council_review" or council_votes.size() != COUNCIL_SEATS.size():
        return false
    # Four Grand Masters must all agree; Orion alone gives the final supreme consent.
    for seat in COUNCIL_SEATS:
        if council_votes.get(seat, false) != true:
            application_denied = true
            stage = "council_rejected"
            return false
    stage = "military_warrior"
    return true

func admitted() -> bool:
    return stage == "military_warrior"
