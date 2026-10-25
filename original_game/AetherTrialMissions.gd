extends RefCounted
class_name AetherTrialMissions

# Deterministic mission logic, independent of rendering and input devices.
# Each trial requires a different active gameplay objective.
const MISSIONS := [
    {"name":"The Storm Labyrinth","type":"dodge","goal":5,"description":"Avoid five storm pulses while navigating the arena."},
    {"name":"Trial of the Unbroken","type":"combat","goal":4,"description":"Land four strikes in close combat."},
    {"name":"Weapons of the Aether","type":"weapons","goal":5,"description":"Land five weapon strikes on training opponents."},
    {"name":"The Last Defender","type":"defense","goal":8,"description":"Protect the convoy for eight seconds."},
    {"name":"The Aether Gate","type":"dodge","goal":7,"description":"Survive seven more violent storm pulses."},
    {"name":"Green Master's Discipline","type":"combat","goal":6,"description":"Defeat six sparring exchanges."},
    {"name":"Lightning Conduit Trial","type":"weapons","goal":7,"description":"Master seven precise conduit strikes."},
    {"name":"Purple Master's Gauntlet","type":"defense","goal":12,"description":"Hold the defensive line for twelve seconds."},
    {"name":"Judgment of Restraint","type":"combat","goal":8,"description":"Win eight exchanges against an examiner."},
    {"name":"The Final Qualification","type":"weapons","goal":10,"description":"Complete ten accurate final-exam strikes."}
]
var mission_index := 0
var progress := 0
var hero_health := 100
var mission_elapsed := 0.0
var enemy_health := 100
var failed := false
var total_failures := 0
var attack_cooldown := 0.0

func current() -> Dictionary:
    return MISSIONS[mini(mission_index,MISSIONS.size()-1)]

func is_complete() -> bool:
    return progress >= int(current()["goal"]) and not failed

func reset_attempt() -> void:
    progress = 0
    hero_health = 100
    enemy_health = 100
    failed = false
    mission_elapsed = 0.0
    attack_cooldown = 0.0

func restart_after_failure() -> bool:
    if not failed:
        return false
    reset_attempt()
    return true

func advance() -> bool:
    if not is_complete() or mission_index >= MISSIONS.size()-1:
        return false
    mission_index += 1
    reset_attempt()
    return true

func mark_finished_campaign() -> bool:
    return mission_index == MISSIONS.size()-1 and is_complete()

func strike(weapon: bool) -> bool:
    if failed or is_complete() or attack_cooldown > 0.0:
        return false
    var kind: String = current()["type"]
    if (kind == "weapons") != weapon or kind not in ["combat","weapons"]:
        return false
    progress += 1
    enemy_health = maxi(0,100 - progress * 100 / int(current()["goal"]))
    attack_cooldown = 0.22
    return true

func dodge_pulse(moved_out_of_danger: bool) -> bool:
    if failed or is_complete() or current()["type"] != "dodge":
        return false
    if moved_out_of_danger:
        progress += 1
    else:
        take_damage(18)
    return moved_out_of_danger

func take_damage(amount: int) -> void:
    if failed:
        return
    hero_health = maxi(0,hero_health - amount)
    if hero_health == 0:
        failed = true
        total_failures += 1

func tick(delta: float, defending: bool) -> void:
    if failed or is_complete() or delta <= 0.0:
        return
    attack_cooldown = maxf(0.0,attack_cooldown-delta)
    if current()["type"] == "defense":
        mission_elapsed += delta
        if defending:
            progress = mini(int(current()["goal"]),int(mission_elapsed))
        else:
            take_damage(int(ceil(delta*8.0)))
