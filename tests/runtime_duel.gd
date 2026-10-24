extends SceneTree
const Rules = preload("res://scripts/DuelRules.gd")
func _init():
    assert(not Rules.has_winner([0, 0]))
    assert(not Rules.has_winner([1, 1]))
    assert(not Rules.has_winner([1, 0]))
    assert(Rules.has_winner([2, 0]))
    assert(Rules.has_winner([1, 2]))
    assert(Rules.winner([0, 0]) == -1)
    assert(Rules.winner([2, 1]) == 0)
    assert(Rules.winner([1, 2]) == 1)
    print("GO6_DUEL_RULES_PASS")
    quit()
