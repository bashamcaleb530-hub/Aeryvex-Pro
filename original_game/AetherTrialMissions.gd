extends RefCounted
class_name AetherTrialMissions

# Deterministic mission logic, independent of rendering and input devices.
# Each trial requires a different active gameplay objective.
const MISSIONS := [
    {"name":"The Storm Labyrinth","type":"dodge","goal":30,"description":"Enter the lightning maze / Cross the shifting storm field / Survive the final lightning surge","phases":["Enter the lightning maze","Cross the shifting storm field","Survive the final lightning surge"]},
    {"name":"Trial of the Unbroken","type":"combat","goal":36,"description":"Learn defensive footwork / Win the sparring circuit / Face the arena champion","phases":["Learn defensive footwork","Win the sparring circuit","Face the arena champion"]},
    {"name":"Weapons of the Aether","type":"weapons","goal":42,"description":"Prove weapon fundamentals / Overcome ranged sentries / Disarm the final examiner","phases":["Prove weapon fundamentals","Overcome ranged sentries","Disarm the final examiner"]},
    {"name":"The Last Defender","type":"defense","goal":75,"description":"Secure the convoy / Hold against the assault / Protect the last evacuation","phases":["Secure the convoy","Hold against the assault","Protect the last evacuation"]},
    {"name":"The Aether Gate","type":"dodge","goal":42,"description":"Reach the outer gate / Survive the storm corridor / Seal the corrupted gateway","phases":["Reach the outer gate","Survive the storm corridor","Seal the corrupted gateway"]},
    {"name":"Green Master's Discipline","type":"combat","goal":48,"description":"Study the Adept's technique / Survive relentless sparring / Earn the green mentor's respect","phases":["Study the Adept's technique","Survive relentless sparring","Earn the green mentor's respect"]},
    {"name":"Lightning Conduit Trial","type":"weapons","goal":54,"description":"Control dual and single conduits / Complete the precision course / Survive the weapon gauntlet","phases":["Control dual and single conduits","Complete the precision course","Survive the weapon gauntlet"]},
    {"name":"Purple Master's Gauntlet","type":"defense","goal":90,"description":"Hold the eastern barricade / Defend the wounded candidates / Endure the Master's final assault","phases":["Hold the eastern barricade","Defend the wounded candidates","Endure the Master's final assault"]},
    {"name":"Judgment of Restraint","type":"combat","goal":60,"description":"Win without reckless attacks / Face escalating challenges / Show restraint under pressure","phases":["Win without reckless attacks","Face escalating challenges","Show restraint under pressure"]},
    {"name":"The Final Qualification","type":"weapons","goal":72,"description":"Demonstrate your weapon control / Survive the examination wave / Earn the Master's recommendation","phases":["Demonstrate your weapon control","Survive the examination wave","Earn the Master's recommendation"]}
]
var mission_index := 0
var progress := 0
var hero_health := 100
var mission_elapsed := 0.0
var enemy_health := 100
var failed := false
var total_failures := 0
var attack_cooldown := 0.0
var checkpoint_progress := 0
var checkpoint_act := 0

func current() -> Dictionary:
    return MISSIONS[mini(mission_index,MISSIONS.size()-1)]

func phase_index() -> int:
    var goal := int(current()["goal"])
    if progress >= goal:
        return 2
    return mini(2, int(float(progress) * 3.0 / float(goal)))

func phase_name() -> String:
    return current()["phases"][phase_index()]

func act_start(index: int) -> int:
    var goal := int(current()["goal"])
    return int(ceil(float(goal * clampi(index, 0, 2)) / 3.0))

func _record_checkpoint() -> void:
    # Act 2 and Act 3 are persistent retry checkpoints.
    var act := phase_index()
    if act > checkpoint_act and not failed:
        checkpoint_act = act
        checkpoint_progress = act_start(act)

func checkpoint_name() -> String:
    return current()["phases"][checkpoint_act]

func is_complete() -> bool:
    return progress >= int(current()["goal"]) and not failed

func reset_attempt() -> void:
    progress = 0
    checkpoint_progress = 0
    checkpoint_act = 0
    hero_health = 100
    enemy_health = 100
    failed = false
    mission_elapsed = 0.0
    attack_cooldown = 0.0

func restart_after_failure() -> bool:
    if not failed:
        return false
    # Preserve the last successfully reached act on retry.
    var saved_progress := checkpoint_progress
    var saved_act := checkpoint_act
    reset_attempt()
    progress = saved_progress
    checkpoint_progress = saved_progress
    checkpoint_act = saved_act
    enemy_health = maxi(0,100 - progress * 100 / int(current()["goal"]))
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
    _record_checkpoint()
    enemy_health = maxi(0,100 - progress * 100 / int(current()["goal"]))
    attack_cooldown = 0.22
    return true

func dodge_pulse(moved_out_of_danger: bool) -> bool:
    if failed or is_complete() or current()["type"] != "dodge":
        return false
    if moved_out_of_danger:
        progress += 1
        _record_checkpoint()
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
            _record_checkpoint()
        else:
            take_damage(int(ceil(delta*8.0)))
