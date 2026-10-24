extends Reference
# Go 5: deterministic tactical decisions for the computer opponent.
# Randomness is supplied by the caller so Godot tests can use fixed rolls.
# Three difficulty levels adjust reaction speed, offensive pressure, and defense.

const NAMES = ["Rookie", "Veteran", "Master"]
const REACTION = [0.47, 0.30, 0.15]
const ATTACK_INTERVAL = [1.65, 1.14, 0.86]
const AGGRESSION = [0.55, 0.78, 0.95]
const PARRY_CHANCE = [0.07, 0.20, 0.34]
const GUARD_CHANCE = [0.52, 0.77, 0.90]
const HEAVY_CHANCE = [0.12, 0.28, 0.37]

static func skill(value):
    return int(clamp(value, 0, NAMES.size() - 1))

static func reaction_delay(value):
    return REACTION[skill(value)]

static func next_attack_delay(value):
    return ATTACK_INTERVAL[skill(value)]

static func defense_for_threat(value, guard, can_dodge, roll):
    # Don't make a physically impossible parry when guard is depleted.
    if guard < 20.0:
        return "dodge" if can_dodge else "none"
    var level = skill(value)
    if roll < PARRY_CHANCE[level]:
        return "parry"
    if roll < GUARD_CHANCE[level]:
        return "guard"
    return "none"

static func attack_for_opening(value, distance, guard, phase, defending, roll):
    if phase != "idle" or defending or distance > 2.75 or guard < 12.0:
        return ""
    var level = skill(value)
    if roll > AGGRESSION[level]:
        return ""
    if guard >= 25.0 and roll < HEAVY_CHANCE[level]:
        return "heavy"
    return "light"

static func desired_distance(guard, target_windup):
    if target_windup and guard < 28.0:
        return 2.95
    return 2.2

static func steering(from_position, target_position, desired_range, orbit_side):
    # Horizontal steering, never vertical movement; no divide-by-zero at overlap.
    var away = from_position - target_position
    away.y = 0.0
    var distance = away.length()
    if distance < 0.01:
        away = Vector3(0, 0, 1)
    else:
        away /= distance
    var tangent = Vector3(-away.z, 0, away.x) * orbit_side
    if distance > desired_range + 0.35:
        return (-away * 0.91 + tangent * 0.25).normalized()
    if distance < desired_range - 0.55:
        return (away * 0.9 + tangent * 0.28).normalized()
    return tangent * 0.55
