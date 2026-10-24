extends Reference
# Rules kept independent from the scene so they can be unit tested.
const ROUNDS_TO_WIN = 2

static func has_winner(score):
    return score[0] >= ROUNDS_TO_WIN or score[1] >= ROUNDS_TO_WIN

static func winner(score):
    if score[0] >= ROUNDS_TO_WIN:
        return 0
    if score[1] >= ROUNDS_TO_WIN:
        return 1
    return -1
