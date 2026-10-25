extends Node3D
# Aeryvex Pro character arena: procedural 3D stand-ins for visual and lightning tests.
# Replace stand-ins with approved, rigged .glb characters when available.
const DESIGN_PATH = "res://aeryvex_game_design.json"
const RULERS = [0, 12, 13, 14, 15, 6, 16, 17, 18, 19]
const RAINBOW = [Color("#ff3865"), Color("#ff962d"), Color("#ffe65f"), Color("#47ff8b"), Color("#2fd7ff"), Color("#735bff"), Color("#d649ff")]
const VOID_RED = [Color("#ff142d"), Color("#ff4545"), Color("#bd071e")]
var roster: Array = []
var current := 0
var character_root: Node3D
var fx_root: Node3D
var camera: Camera3D
var label: Label
var time_s := 0.0
var attack_timer := 0.0
var model_loader: Node3D
var model_active := false
var status_note := ""

func _ready() -> void:
    var file := FileAccess.open(DESIGN_PATH, FileAccess.READ)
    if file == null:
        push_error("Missing character roster: " + DESIGN_PATH)
        return
    var json = JSON.parse_string(file.get_as_text())
    if typeof(json) != TYPE_DICTIONARY or not json.has("roster"):
        push_error("Invalid Aeryvex character roster JSON")
        return
    roster = json["roster"]
    _build_world()
    _select(0)

func _build_world() -> void:
    var world := WorldEnvironment.new()
    var env := Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color("#0a1022")
    env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    env.ambient_light_color = Color("#9aa9ee")
    env.ambient_light_energy = 0.65
    world.environment = env
    add_child(world)
    var light := DirectionalLight3D.new()
    light.rotation_degrees = Vector3(-48, -20, 0)
    light.light_energy = 2.1
    add_child(light)
    camera = Camera3D.new()
    camera.position = Vector3(0, 2.7, 7.6)
    camera.look_at_from_position(camera.position, Vector3(0, 1.5, 0))
    camera.current = true
    add_child(camera)
    _box(self, Vector3(15, 0.18, 15), Vector3(0, -0.17, 0), Color("#27344e"))
    for i in range(-6, 7):
        _box(self, Vector3(0.025, 0.015, 13), Vector3(float(i), -0.07, 0), Color("#365b8c"))
        _box(self, Vector3(13, 0.015, 0.025), Vector3(0, -0.07, float(i)), Color("#365b8c"))
    character_root = Node3D.new()
    add_child(character_root)
    fx_root = Node3D.new()
    add_child(fx_root)
    var loader_script = load("res://ApprovedCharacterLoader.gd")
    model_loader = Node3D.new()
    model_loader.set_script(loader_script)
    # Disable its default ready load; arena selects characters explicitly.
    model_loader.set("character_id", -1)
    character_root.add_child(model_loader)
    var layer := CanvasLayer.new()
    add_child(layer)
    label = Label.new()
    label.position = Vector2(30, 25)
    label.add_theme_font_size_override("font_size", 23)
    label.add_theme_color_override("font_color", Color("#e4efff"))
    layer.add_child(label)

func _box(parent: Node3D, size: Vector3, pos: Vector3, color: Color) -> MeshInstance3D:
    var item := MeshInstance3D.new()
    var mesh := BoxMesh.new()
    mesh.size = size
    item.mesh = mesh
    item.position = pos
    var mat := StandardMaterial3D.new()
    mat.albedo_color = color
    mat.metallic = 0.65
    mat.roughness = 0.36
    item.material_override = mat
    parent.add_child(item)
    return item

func _sphere(parent: Node3D, scale_v: Vector3, pos: Vector3, color: Color) -> MeshInstance3D:
    var item := MeshInstance3D.new()
    var mesh := SphereMesh.new()
    mesh.radius = 0.5
    mesh.height = 1.0
    item.mesh = mesh
    item.scale = scale_v
    item.position = pos
    var mat := StandardMaterial3D.new()
    mat.albedo_color = color
    mat.metallic = 0.38
    item.material_override = mat
    parent.add_child(item)
    return item

func _character(id: int) -> Dictionary:
    for entry in roster:
        if int(entry.get("id", -1)) == id:
            return entry
    return {}

func _clear(node: Node) -> void:
    for child in node.get_children():
        node.remove_child(child)
        child.queue_free()

func _select(index: int) -> void:
    if roster.is_empty():
        return
    current = posmod(index, RULERS.size())
    # Keep the loader resident across selections, clearing only test geometry.
    for child in character_root.get_children():
        if child != model_loader:
            character_root.remove_child(child)
            child.queue_free()
    _clear(fx_root)
    model_active = model_loader.call("load_character", RULERS[current])
    status_note = "APPROVED GLB LOADED" if model_active else "TEST BODY - APPROVED GLB NOT YET INSTALLED"
    var entry := _character(RULERS[current])
    var is_aether: bool = entry.get("faction", "") == "aether"
    var skin := Color("#384987") if is_aether else Color("#51313a")
    var armor := Color("#e5c37a") if is_aether else Color("#711d32")
    var dark := Color("#1c305e") if is_aether else Color("#17111f")
    var is_thalen: bool = entry.get("name", "") == "Thalen Orris"
    if is_thalen:
        skin = Color("#414bb0")
        armor = Color("#77879e")
        dark = Color("#26283c")
    # Procedural temporary stand-in, only visible if no approved model exists.
    # Same overall human-scale skeleton for Thalen. Korr alone has 4 arms.
    _box(character_root, Vector3(0.68, 0.85, 0.38), Vector3(0, 1.62, 0), dark)
    _box(character_root, Vector3(0.82, 0.22, 0.5), Vector3(0, 2.02, 0), armor)
    _sphere(character_root, Vector3(0.54, 0.66, 0.52), Vector3(0, 2.37, 0), skin)
    _box(character_root, Vector3(0.28, 0.86, 0.3), Vector3(-0.22, 0.57, 0), dark)
    _box(character_root, Vector3(0.28, 0.86, 0.3), Vector3(0.22, 0.57, 0), dark)
    for sign_x in [-1.0, 1.0]:
        _box(character_root, Vector3(0.22, 0.79, 0.25), Vector3(sign_x * 0.53, 1.51, 0), armor)
        _sphere(character_root, Vector3(0.28, 0.28, 0.28), Vector3(sign_x * 0.53, 1.02, 0), skin)
    if entry.get("name", "") == "Korr Uldane":
        for sign_x in [-1.0, 1.0]:
            _box(character_root, Vector3(0.2, 0.6, 0.25), Vector3(sign_x * 0.75, 1.0, -0.1), armor)
    # Orion has a crown; Thalen does not. Distinct placeholder proportions.
    if entry.get("name", "") == "Orion Valen":
        _box(character_root, Vector3(0.57, 0.17, 0.55), Vector3(0, 2.76, 0), Color("#e7be57"))
    elif entry.get("name", "") == "Drakthar Vex":
        _box(character_root, Vector3(0.62, 0.29, 0.57), Vector3(0, 2.7, 0), Color("#440913"))
    elif is_thalen:
        _box(character_root, Vector3(0.55, 0.08, 0.55), Vector3(0, 2.7, 0), Color("#242e56"))
    _box(character_root, Vector3(0.07, 2.7, 0.07), Vector3(-0.96, 1.32, 0), armor)
    _sphere(character_root, Vector3(0.29, 0.32, 0.29), Vector3(-0.96, 2.72, 0), Color("#8fd2ff") if is_aether else Color("#ff3451"))
    label.text = "AERYVEX PRO — CHARACTER ARENA\n%s  |  %s\n%s LIGHTNING  |  SPACE: burst   LEFT/RIGHT: switch   ESC: quit\nProcedural test body: final 3D model not yet imported" % [entry.get("name", "Unknown"), entry.get("role", ""), "RAINBOW" if is_aether else "RED"]
    if model_active:
        for child in character_root.get_children():
            if child != model_loader:
                child.visible = false
    attack_timer = 0.7

func _input(event: InputEvent) -> void:
    if event is InputEventKey and event.pressed and not event.echo:
        if event.keycode == KEY_RIGHT:
            _select(current + 1)
        elif event.keycode == KEY_LEFT:
            _select(current - 1)
        elif event.keycode == KEY_SPACE:
            attack_timer = 0.7
        elif event.keycode == KEY_ESCAPE:
            get_tree().quit()

func _process(delta: float) -> void:
    if roster.is_empty():
        return
    time_s += delta
    attack_timer = maxf(0.0, attack_timer - delta)
    if character_root:
        character_root.rotation.y = sin(time_s * 0.45) * 0.23
    _draw_lightning()

func _draw_lightning() -> void:
    _clear(fx_root)
    var entry := _character(RULERS[current])
    var aether: bool = entry.get("faction", "") == "aether"
    var colors: Array = RAINBOW if aether else VOID_RED
    var burst := attack_timer > 0.0
    var count := 8 if burst else 3
    for j in range(count):
        var start := Vector3(-0.96, 2.65, 0) if j % 2 == 0 else Vector3(0.55, 1.15, 0)
        var endpoint := Vector3(
            (-1.0 if j % 2 == 0 else 1.0) * (1.2 + 0.2 * float(j % 3)),
            0.3 + float((j * 3) % 7) * 0.42,
            0.05 + 0.2 * sin(time_s * 8.0 + float(j))
        )
        var color: Color = colors[j % colors.size()]
        var last := start
        for k in range(1, 9):
            var fraction := float(k) / 8.0
            var pos := start.lerp(endpoint, fraction)
            if k < 8:
                pos += Vector3(
                    sin(time_s * 19.0 + float(j * 7 + k * 13)) * 0.13,
                    cos(time_s * 14.0 + float(j * 11 + k * 3)) * 0.1,
                    sin(time_s * 17.0 + float(j + k * 5)) * 0.1
                )
            _arc_segment(last, pos, color)
            if burst and k == 5:
                _arc_segment(pos, pos + Vector3(0.3, 0.25, -0.18), color)
            last = pos

func _arc_segment(a: Vector3, b: Vector3, color: Color) -> void:
    var length := a.distance_to(b)
    if length < 0.01:
        return
    var line := MeshInstance3D.new()
    var mesh := CylinderMesh.new()
    mesh.top_radius = 0.015
    mesh.bottom_radius = 0.015
    mesh.height = length
    line.mesh = mesh
    line.position = (a + b) * 0.5
    line.quaternion = Quaternion(Vector3.UP, (b - a).normalized())
    var mat := StandardMaterial3D.new()
    mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    mat.albedo_color = color
    mat.emission_enabled = true
    mat.emission = color
    mat.emission_energy_multiplier = 3.0
    line.material_override = mat
    fx_root.add_child(line)
