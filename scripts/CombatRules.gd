extends Reference
# Godot 3.x. Deterministic combat values kept separate from scene/rendering.
# A hit is generated once, when a strike enters its active phase.

const ATTACKS = {
    "light": {"damage": 18.0, "cost": 12.0, "reach": 2.55, "arc": 0.45,
        "windup": 0.25, "active": 0.12, "recovery": 0.26, "guard_damage": 22.0},
    "heavy": {"damage": 32.0, "cost": 25.0, "reach": 2.85, "arc": 0.3,
        "windup": 0.48, "active": 0.16, "recovery": 0.48, "guard_damage": 46.0}
}

static func can_start(phase, energy, cost, stagger_remaining, guard_break_remaining):
    return phase == "idle" and energy >= cost and stagger_remaining <= 0.0 and guard_break_remaining <= 0.0

static func in_arc(attacker_transform, target_position, reach, required_dot):
    var toward = target_position - attacker_transform.origin
    toward.y = 0.0
    if toward.length_squared() > reach * reach:
        return false
    if toward.length_squared() < 0.0001:
        return true
    var facing = -attacker_transform.basis.z
    facing.y = 0.0
    return facing.normalized().dot(toward.normalized()) >= required_dot

# Predict the combat outcome without touching any scene nodes.
# Front-facing is validated by the caller: blocking doesn't stop rear hits.
static func guard_result(damage, guard_damage, guard, blocking, parry, invulnerable):
    var result = {"outcome": "hit", "hp_loss": damage, "guard_left": guard,
        "attacker_stagger": 0.0, "defender_stagger": 0.0}
    if invulnerable:
        result["outcome"] = "dodge"
        result["hp_loss"] = 0.0
    elif blocking and parry and guard > 0.0:
        result["outcome"] = "parry"
        result["hp_loss"] = 0.0
        result["attacker_stagger"] = 0.6
    elif blocking and guard > 0.0:
        result["guard_left"] = max(0.0, guard - guard_damage)
        if result["guard_left"] <= 0.0:
            result["outcome"] = "guard_break"
            result["hp_loss"] = damage * 0.35
            result["defender_stagger"] = 1.1
        else:
            result["outcome"] = "block"
            result["hp_loss"] = damage * 0.08
    return result
