extends SceneTree
# Visual asset audit: gameplay passing is never proof of approved character likeness.
func _initialize() -> void:
    call_deferred("_audit")

func _audit() -> void:
    var expected := ["kai.png","ryker.png","lyra.png","approved_character_selection.png","approved_main_menu.png"]
    var missing: Array = []
    for asset in expected:
        var path := "res://approved_heroes/" + asset
        var exists := ResourceLoader.exists(path)
        print(("FOUND" if exists else "MISSING") + ": " + path)
        if not exists:
            missing.append(asset)
    for character in ["kai","ryker","lyra"]:
        var model_path := "res://approved_heroes/" + character + ".glb"
        print(("3D MODEL FOUND: " if ResourceLoader.exists(model_path) else "3D MODEL MISSING: ") + model_path)
    if missing.is_empty():
        print("PORTRAIT AUDIT: PASS — approved reference images installed; finished 3D likeness not established.")
    else:
        push_error("PORTRAIT AUDIT FAILED: Install the approved art bundle before visual review.")
    print("NOTE: Passing portrait checks never certifies animated/rigged 3D character fidelity.")
    quit(0 if missing.is_empty() else 1)
