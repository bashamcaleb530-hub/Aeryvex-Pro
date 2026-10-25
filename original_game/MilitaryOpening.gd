extends Node3D
const TrialMissionScript = preload("res://AetherTrialMissions.gd")

# First playable vertical slice: approach training stations and complete each gate.
# Temporary scene geometry; no approved character appearance is replaced.
const TASK_POSITIONS := [
    Vector3(-5, 0, -4), Vector3(0, 0, -5), Vector3(5, 0, -4), Vector3(5, 0, 2),
    Vector3(0, 0, 4), Vector3(-5, 0, 3), Vector3(-4, 0, -1),
    Vector3(2, 0, -2), Vector3(4, 0, 4), Vector3(-2, 0, 4)
]
var missions: RefCounted
var pulse_clock := 0.0
var last_pulse_position := Vector3.ZERO
var admission: AetherMilitaryAdmission
var opponent: Node3D
var hazard: Node3D
var hero: Node3D
var stations: Array = []
var task_index := 0
var completed_count := 0
var score := 0
var hud: Label
var message := "You are a teenage applicant. Earn your place in the Aether military."
var council_approved := false
var movement_speed := 4.8
var selected_hero := "KAI"
var hero_tint := Color("#32aaff")

func _ready() -> void:
    admission = AetherMilitaryAdmission.new()
    missions = TrialMissionScript.new()
    _load_selected_hero()
    _setup_world()
    _refresh_encounter()
    _update_hud()

func _load_selected_hero() -> void:
    if not FileAccess.file_exists("user://aether_world_profile.json"):
        return
    var data = JSON.parse_string(FileAccess.get_file_as_string("user://aether_world_profile.json"))
    if typeof(data) != TYPE_DICTIONARY:
        return
    var idx := clampi(int(data.get("selected", 0)), 0, 2)
    selected_hero = ["KAI", "RYKER", "LYRA"][idx]
    movement_speed = [6.2, 4.1, 5.8][idx]
    hero_tint = [Color("#32aaff"), Color("#f2bf61"), Color("#ad72ff")][idx]

func _box(parent: Node3D, size: Vector3, position: Vector3, tint: Color) -> MeshInstance3D:
    var node := MeshInstance3D.new()
    var mesh := BoxMesh.new()
    mesh.size = size
    node.mesh = mesh
    node.position = position
    var material := StandardMaterial3D.new()
    material.albedo_color = tint
    material.metallic = 0.32
    node.material_override = material
    parent.add_child(node)
    return node

func _setup_world() -> void:
    var world := WorldEnvironment.new()
    var environment := Environment.new()
    environment.background_mode = Environment.BG_COLOR
    environment.background_color = Color("#071427")
    environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
    environment.ambient_light_color = Color("#9ab5ff")
    world.environment = environment
    add_child(world)
    var sun := DirectionalLight3D.new()
    sun.rotation_degrees = Vector3(-54, -25, 0)
    add_child(sun)
    _box(self, Vector3(18, 0.3, 16), Vector3(0, -0.2, 0), Color("#26364f"))
    for x in [-8, 8]:
        _box(self, Vector3(0.4, 2.0, 16), Vector3(x, 0.8, 0), Color("#405b8a"))
    hero = Node3D.new()
    hero.name = "TeenageCandidate"
    add_child(hero)
    _box(hero, Vector3(0.62, 1.2, 0.45), Vector3(0, 1.12, 0), hero_tint)
    _box(hero, Vector3(0.48, 0.48, 0.48), Vector3(0, 1.92, 0), Color("#8fa5bb"))
    opponent = Node3D.new()
    opponent.name = "TrainingOpponent"
    opponent.position = Vector3(1.5, 0, 0)
    add_child(opponent)
    _box(opponent, Vector3(0.74, 1.35, 0.5), Vector3(0, 1.0, 0), Color("#a24363"))
    _box(opponent, Vector3(0.5, 0.5, 0.5), Vector3(0, 1.91, 0), Color("#bd8ca7"))
    hazard = Node3D.new()
    hazard.name = "StormHazard"
    add_child(hazard)
    _box(hazard, Vector3(2.2, 0.08, 2.2), Vector3(0, 0.06, 0), Color("#26a8ea"))
    var camera := Camera3D.new()
    camera.position = Vector3(0, 12.2, 13)
    camera.look_at_from_position(camera.position, Vector3(0, 0, 0))
    camera.current = true
    add_child(camera)
    var colors := [Color("#1376c9"), Color("#9a3ee4"), Color("#e6bd3e")]
    for i in range(TASK_POSITIONS.size()):
        var tint: Color = colors[0] if i < 4 else (colors[1] if i >= 7 else colors[2])
        var station := Node3D.new()
        station.name = "TrialStation_%02d" % (i + 1)
        station.position = TASK_POSITIONS[i]
        add_child(station)
        _box(station, Vector3(1.15, 0.27, 1.15), Vector3(0, 0.07, 0), tint)
        _box(station, Vector3(0.18, 1.2, 0.18), Vector3(0, 0.72, 0), tint)
        stations.append(station)
    var overlay := CanvasLayer.new()
    add_child(overlay)
    hud = Label.new()
    hud.position = Vector2(22, 20)
    hud.add_theme_font_size_override("font_size", 21)
    hud.add_theme_color_override("font_color", Color("#ffffff"))
    overlay.add_child(hud)

func _refresh_encounter() -> void:
    if opponent == null or hazard == null:
        return
    var kind: String = missions.current()["type"]
    opponent.visible = kind in ["combat", "weapons"]
    hazard.visible = kind == "dodge"
    if opponent.visible:
        opponent.position = hero.position + Vector3(1.7, 0, -0.4)
    if hazard.visible:
        hazard.position = hero.position

func _attempt_strike(weapon: bool) -> bool:
    if opponent == null or not opponent.visible:
        return false
    if hero.position.distance_to(opponent.position) > 2.3:
        message = "Get close to your opponent before striking."
        _update_hud()
        return false
    var landed: bool = missions.strike(weapon)
    if landed:
        opponent.position.x = clampf(opponent.position.x + 0.24, -6.5, 6.5)
        message = "Conduit hit!" if weapon else "Martial arts hit!"
        _update_hud()
    return landed

func _task_keys() -> Array:
    return admission.ENTRY_TRIALS + admission.GREEN_TRAINING + admission.PURPLE_EXAM

func current_trial() -> String:
    var keys := _task_keys()
    return keys[task_index] if task_index < keys.size() else "council_review"

func _update_hud() -> void:
    if hud == null:
        return
    var objective := current_trial().replace("_", " ").capitalize()
    var mission: Dictionary = missions.current()
    var hint := "WASD move | J martial | K weapon | H defend | R retry | F finish at marker."
    if admission.stage == "council_review":
        hint = "Press C to present the purple Master's recommendation to the Council."
    if council_approved:
        hint = "ENROLLED: Blue Lightning Warrior. The larger campaign continues from here."
    hud.text = "AETHER WORLD — TEN MILITARY MISSIONS\n%s | %s\nStage: %s | Cleared: %d/10 | Merit: %d\nMission %d: %s\n%s | %d/%d | Health: %d | Failures: %d\n%s" % [
        message, selected_hero, admission.stage.replace("_", " ").capitalize(), completed_count, score,
        mini(task_index+1,10), mission["name"], mission["description"], missions.progress,
        int(mission["goal"]), missions.hero_health, missions.total_failures, hint
    ]

func _process(delta: float) -> void:
    if hero == null or council_approved:
        return
    var direction := Vector3.ZERO
    if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
        direction.x -= 1
    if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
        direction.x += 1
    if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
        direction.z -= 1
    if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
        direction.z += 1
    hero.position += direction.normalized() * movement_speed * delta
    hero.position.x = clampf(hero.position.x, -7.2, 7.2)
    hero.position.z = clampf(hero.position.z, -6.2, 6.2)
    if missions.failed:
        return
    missions.tick(delta,Input.is_key_pressed(KEY_H))
    if opponent != null and opponent.visible and not missions.is_complete():
        opponent.position.x += sin(Time.get_ticks_msec() * 0.002) * delta * 0.6
    if hazard != null and hazard.visible:
        hazard.position = last_pulse_position
    if missions.current()["type"] == "dodge" and not missions.is_complete():
        pulse_clock += delta
        if pulse_clock >= 1.0:
            pulse_clock -= 1.0
            missions.dodge_pulse(hero.position.distance_to(last_pulse_position) >= 1.0)
            last_pulse_position = hero.position
    if missions.failed:
        message = "FAILED: Health depleted. Press R to retry this mission."
    _update_hud()

func try_trial() -> bool:
    if task_index >= stations.size():
        return false
    if hero.position.distance_to(stations[task_index].position) > 1.8:
        message = "Approach the marked trial before attempting it."
        _update_hud()
        return false
    if not missions.is_complete():
        message = "Complete the mission objective before using this gateway."
        _update_hud()
        return false
    var key := current_trial()
    if not admission.complete_challenge(key):
        return false
    stations[task_index].visible = false
    task_index += 1
    completed_count += 1
    if task_index < 10:
        missions.advance()
        _refresh_encounter()
        pulse_clock = 0.0
        last_pulse_position = hero.position
    score += 100
    message = "Completed: %s." % key.replace("_", " ").capitalize()
    if task_index == 4:
        if admission.begin_green_training():
            message = "Entrance survived. A green Adept now trains you."
    elif task_index == 7:
        if admission.face_purple_master():
            message = "Green training passed. Face the purple Master."
    elif task_index == 10:
        if admission.master_recommendation():
            message = "Purple Master recommends you to Orion's Council."
    _update_hud()
    return true

func request_council_review() -> bool:
    if admission.stage != "council_review" or council_approved:
        return false
    # This is a prototype scripted approval, not yet a dialogue/decision scene.
    for seat in admission.COUNCIL_SEATS:
        admission.council_vote(seat, true)
    council_approved = admission.decide_admission()
    if council_approved:
        message = "The four Grand Masters and Orion approve your military enlistment!"
    _update_hud()
    return council_approved

func _input(event: InputEvent) -> void:
    if not (event is InputEventKey) or not event.pressed or event.echo:
        return
    if event.keycode == KEY_F:
        try_trial()
    elif event.keycode == KEY_J:
        _attempt_strike(false)
    elif event.keycode == KEY_K:
        _attempt_strike(true)
    elif event.keycode == KEY_R:
        if missions.restart_after_failure():
            pulse_clock = 0.0
            last_pulse_position = hero.position
            _refresh_encounter()
            message = "Retrying mission; earlier victories remain."
            _update_hud()
    elif event.keycode == KEY_C:
        request_council_review()
    elif event.keycode == KEY_ESCAPE:
        get_tree().quit()
