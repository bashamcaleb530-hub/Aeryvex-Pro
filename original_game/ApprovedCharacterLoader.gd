extends Node3D
## Drops in approved ruler GLBs when they exist; otherwise exposes a missing-asset
## status instead of inventing faces or silently substituting characters.
## Attach to a Node3D or instantiate under the character display scene.
@export var character_id: int = 0
@export var characters_root: String = "res://assets/approved_characters"
@export var height_scale: float = 1.0

const RULERS = {
    0: "orion_valen",
    12: "maeryn_sol",
    13: "thalen_orris",
    14: "ilyra_venn",
    15: "selene_avaris",
    6: "drakthar_vex",
    16: "malveris_thorne",
    17: "nyssara_veil",
    18: "korr_uldane",
    19: "vaelith_sorn"
}
signal character_loaded(character_id: int, model: Node3D)
signal character_missing(character_id: int, expected_path: String)
var active_model: Node3D

func _ready() -> void:
    load_character(character_id)

func load_character(id: int) -> bool:
    character_id = id
    if is_instance_valid(active_model):
        active_model.queue_free()
        active_model = null
    if not RULERS.has(id):
        push_warning("Unknown approved ruler ID: " + str(id))
        return false
    var path: String = characters_root.path_join(RULERS[id] + ".glb")
    if not ResourceLoader.exists(path):
        character_missing.emit(id, path)
        print("Approved ruler mesh pending: ", path)
        return false
    var resource: Resource = load(path)
    if not resource is PackedScene:
        push_warning("Model is not a Godot-imported GLB scene: " + path)
        return false
    active_model = (resource as PackedScene).instantiate() as Node3D
    if active_model == null:
        push_warning("GLB did not instantiate as a Node3D: " + path)
        return false
    active_model.scale = Vector3.ONE * height_scale
    add_child(active_model)
    character_loaded.emit(id, active_model)
    return true
