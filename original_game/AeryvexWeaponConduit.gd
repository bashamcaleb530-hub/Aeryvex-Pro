extends Node3D
class_name AeryvexWeaponConduit

# Prototype geometry only. The approved weapon art/meshes must replace these handles.
# Electricity stays visibly branching and never becomes a rigid luminous blade.
const MODES := {
    0: ["supreme_staff", "dual_swords"],
    12: ["staff"],
    13: ["dual_swords"],
    14: ["dual_swords"],
    15: ["staff"],
    6: ["void_staff"],
    16: ["greatsword"],
    17: ["dual_swords"],
    18: ["dual_swords"],
    19: ["staff"]
}
const RAINBOW := [Color("#fd3552"),Color("#ffbd37"),Color("#eefa4c"),Color("#42fb9d"),Color("#22baff"),Color("#7a54ff"),Color("#d048fa")]
const MULTICOLOR := [Color("#9c35ed"),Color("#12e6a7"),Color("#f5b544"),Color("#258dff")]
const CRIMSON := [Color("#ff1835"),Color("#a80726"),Color("#f34e49")]

var character_id := 0
var mode_index := 0
var weapon_mode := "supreme_staff"
var weapon_root: Node3D
var energy_root: Node3D
var phase := 0.0

func _ready() -> void:
    weapon_root = Node3D.new()
    weapon_root.name = "ConduitHandles"
    add_child(weapon_root)
    energy_root = Node3D.new()
    energy_root.name = "BranchingElectricalArcs"
    add_child(energy_root)
    equip(character_id)

func available_modes(id: int) -> Array:
    return MODES.get(id, ["staff"]).duplicate()

func equip(id: int) -> void:
    character_id = id
    mode_index = 0
    _redraw()

func transform() -> bool:
    var choices: Array = available_modes(character_id)
    if choices.size() < 2:
        return false
    mode_index = (mode_index + 1) % choices.size()
    _redraw()
    return true

func get_mode() -> String:
    return weapon_mode

func _clear(root_node: Node) -> void:
    for child in root_node.get_children():
        root_node.remove_child(child)
        child.queue_free()

func _redraw() -> void:
    if weapon_root == null:
        return
    _clear(weapon_root)
    var choices: Array = available_modes(character_id)
    weapon_mode = choices[mode_index]
    var dark_metal := Color("#29394e") if character_id != 6 else Color("#291b25")
    if weapon_mode in ["dual_swords"]:
        _handle(Vector3(-0.68,1.08,0), 0.43, dark_metal)
        _handle(Vector3(0.68,1.08,0), 0.43, dark_metal)
    elif weapon_mode in ["supreme_staff","void_staff","staff"]:
        _handle(Vector3(-0.98,1.62,0), 2.4, dark_metal)
    elif weapon_mode == "greatsword":
        _handle(Vector3(-0.68,1.23,0), 0.7, dark_metal)
    _draw_arcs()

func _handle(pos: Vector3, length: float, color: Color) -> void:
    var mesh_instance := MeshInstance3D.new()
    var mesh := CylinderMesh.new()
    mesh.height = length
    mesh.top_radius = 0.07
    mesh.bottom_radius = 0.095
    mesh_instance.mesh = mesh
    mesh_instance.position = pos
    var material := StandardMaterial3D.new()
    material.albedo_color = color
    material.metallic = 0.95
    material.roughness = 0.22
    mesh_instance.material_override = material
    weapon_root.add_child(mesh_instance)

func _process(delta: float) -> void:
    phase += delta
    _draw_arcs()

func _draw_arcs() -> void:
    if energy_root == null:
        return
    _clear(energy_root)
    var colors: Array = RAINBOW if character_id == 0 else (MULTICOLOR if character_id in [12,13,14,15] else CRIMSON)
    var origins: Array = []
    if weapon_mode == "dual_swords":
        origins = [Vector3(-0.68,1.3,0), Vector3(0.68,1.3,0)]
    elif weapon_mode in ["supreme_staff","void_staff","staff"]:
        origins = [Vector3(-0.98,2.85,0)]
    else:
        origins = [Vector3(-0.68,1.6,0)]
    for n in range(origins.size()):
        var start: Vector3 = origins[n]
        var end: Vector3 = start + Vector3(-0.22 if n == 0 else 0.22,1.38,0)
        for strand in range(3):
            var last: Vector3 = start
            for step in range(1,8):
                var t := float(step)/7.0
                var point := start.lerp(end,t)
                if step < 7:
                    point += Vector3(sin(phase*19.0+step*7.0+strand*3.0)*0.17, cos(phase*13.0+step*5.0+strand)*0.08, sin(phase*17.0+strand*8.0+step)*0.11)
                _segment(last,point,colors[(n*3+strand+step)%colors.size()])
                last = point

func _segment(a: Vector3,b: Vector3,color: Color) -> void:
    var length := a.distance_to(b)
    if length < 0.01:
        return
    var mesh_instance := MeshInstance3D.new()
    var mesh := CylinderMesh.new()
    mesh.height = length
    mesh.top_radius = 0.011
    mesh.bottom_radius = 0.011
    mesh_instance.mesh = mesh
    mesh_instance.position = (a+b)*0.5
    mesh_instance.quaternion = Quaternion(Vector3.UP,(b-a).normalized())
    var material := StandardMaterial3D.new()
    material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    material.albedo_color = color
    material.emission_enabled = true
    material.emission = color
    material.emission_energy_multiplier = 3.0
    mesh_instance.material_override = material
    energy_root.add_child(mesh_instance)
