extends Reference
# Deterministic, engine-independent command-post and ticket logic.
const CAPTURE_SPEED = 28.0
const TICKET_DRAIN = 1.0
const START_TICKETS = 120.0

static func capture(progress, allies, enemies, delta):
    # -100 enemy held; +100 player held. Contested posts remain stationary.
    var influence = clamp(allies - enemies, -1, 1)
    return clamp(progress + influence * CAPTURE_SPEED * max(0.0, delta), -100.0, 100.0)

static func owner(progress):
    if progress >= 99.99:
        return 0
    if progress <= -99.99:
        return 1
    return -1

static func drain(tickets, friendly_owned, enemy_owned, delta):
    var result = tickets.duplicate()
    if friendly_owned > enemy_owned:
        result[1] = max(0.0, result[1] - (friendly_owned - enemy_owned) * TICKET_DRAIN * max(0.0, delta))
    elif enemy_owned > friendly_owned:
        result[0] = max(0.0, result[0] - (enemy_owned - friendly_owned) * TICKET_DRAIN * max(0.0, delta))
    return result

static func winner(tickets):
    if tickets[0] <= 0.0 and tickets[1] <= 0.0:
        return -2  # draw
    if tickets[1] <= 0.0:
        return 0
    if tickets[0] <= 0.0:
        return 1
    return -1
