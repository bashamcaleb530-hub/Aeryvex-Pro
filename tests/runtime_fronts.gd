extends SceneTree
const FrontsRules = preload("res://scripts/FrontsRules.gd")
func _init():
    var ok = true
    ok = _check("neutral", FrontsRules.owner(0) == -1) and ok
    ok = _check("player capture", abs(FrontsRules.capture(0, 1, 0, 1) - 28) < 0.01) and ok
    ok = _check("contested", FrontsRules.capture(25, 1, 1, 3) == 25) and ok
    ok = _check("clamp", FrontsRules.capture(95, 1, 0, 10) == 100) and ok
    ok = _check("ownership", FrontsRules.owner(-100) == 1 and FrontsRules.owner(100) == 0) and ok
    var tickets = FrontsRules.drain([120.0,120.0], 2, 1, 20)
    ok = _check("majority drains enemy", tickets[0] == 120 and tickets[1] == 100) and ok
    ok = _check("win", FrontsRules.winner([45.0,0.0]) == 0) and ok
    quit(0 if ok else 1)
func _check(label, good):
    print(("PASS " if good else "FAIL ") + label)
    return good
