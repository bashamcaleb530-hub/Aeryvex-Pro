extends SceneTree
var fails := 0
func _initialize() -> void:
    call_deferred("_run")
func check(value: bool, description: String) -> void:
    if value:
        print("PASS: ", description)
    else:
        fails += 1
        push_error("FAIL: " + description)
func _run() -> void:
    var menu_scene = load("res://AetherWorldMenu.tscn")
    check(menu_scene != null, "Aether World main menu scene exists")
    if menu_scene == null:
        quit(1)
        return
    var menu: Control = menu_scene.instantiate()
    root.add_child(menu)
    await process_frame
    check(menu.HEROES.size() == 3, "Three selectable characters are present")
    check(menu.get("hero_buttons").size() == 3, "Three functional selection buttons exist")
    menu.call("choose_hero", 0)
    check(menu.get("selected") == 0, "Kai can be selected")
    menu.call("choose_hero", 1)
    check(menu.get("selected") == 1, "Ryker can be selected")
    menu.call("choose_hero", 2)
    check(menu.get("selected") == 2, "Lyra can be selected")
    menu.call("choose_hero", 99)
    check(menu.get("selected") == 2, "Invalid selection is ignored")
    check(FileAccess.file_exists(menu.SAVE_PATH), "Character selection is persisted")
    var opening_scene = load("res://MilitaryOpening.tscn")
    check(opening_scene != null, "New Game military opening exists")
    if opening_scene != null:
        var opening: Node = opening_scene.instantiate()
        check(opening.get_script() != null and opening.get_script().can_instantiate(), "Military opening script actually compiles")
        opening.free()
    check(load("res://CharacterArena.tscn") != null, "Character arena exists")
    print("MENU RESULT: ", "PASS" if fails == 0 else "%d FAILED" % fails)
    quit(0 if fails == 0 else 1)
