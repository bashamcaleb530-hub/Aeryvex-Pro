extends CharacterBody3D
var health := 100.0
var alive := true
var control_enabled := true
var intent := Vector3.ZERO
var running := false
var jump_requested := false
var speed := 5.0
var cooldown := 0.0
var energy := 100.0
var yaw := 0.0
var pitch := -0.2
var pivot: Node3D
var arm: SpringArm3D
var abilities: Array = []
var world: Node3D
var attack_power := 35
var material: StandardMaterial3D
var flash_time := 0.0
var character_animator: AnimationPlayer
var character_clips: Dictionary = {}
var current_character_clip := ""
var attack_animation_time := 0.0
# Reviewed-character animation state machine. Gameplay never depends on it.
const ANIMATION_STATES := ["idle", "walk", "run", "jump", "fall", "land", "attack", "hurt", "death"]
const LOOPING_STATES := ["idle", "walk", "run", "fall"]
const ANIMATION_FALLBACKS := {"run": "walk", "fall": "jump", "land": "idle"}
const ANIMATION_BLEND := {"idle": 0.2, "walk": 0.2, "run": 0.15, "jump": 0.1, "fall": 0.15, "land": 0.08, "attack": 0.06, "hurt": 0.05, "death": 0.12}
var animation_state := ""
var animation_transitions: Array = []
var hurt_animation_time := 0.0
var landing_time := 0.0
var cinematic_time := 0.0
var cinematic_state := ""
var was_on_floor := true
var restart_animation := false
var character_visual: Node3D
var visual_yaw_offset := 0.0
var visual_fit := {}
func _ready() -> void:
	var collision := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = 0.4
	shape.height = 1.8
	collision.shape = shape
	collision.position.y = 0.9
	add_child(collision)
	var mesh := MeshInstance3D.new()
	mesh.mesh = CapsuleMesh.new()
	mesh.position.y = 0.9
	material = StandardMaterial3D.new()
	material.albedo_color = Color("8bd5f2")
	mesh.material_override = material
	mesh.tree_exiting.connect(func(): mesh.mesh = null)
	add_child(mesh)
	# Reversible replacement of the visual only: physics, combat and camera stay.
	if ResourceLoader.exists("res://player_visual.glb"):
		var packed := load("res://player_visual.glb") as PackedScene
		if packed != null:
			var visual := packed.instantiate() as Node3D
			if visual != null:
				visual.name = "ReviewedPlayerVisual"
				add_child(visual)
				mesh.visible = false
				character_visual = visual
				# Mesh-only visual binding does not retarget animation skeletons.
				setup_character_animations(visual)
	pivot = Node3D.new()
	pivot.position.y = 1.5
	add_child(pivot)
	arm = SpringArm3D.new()
	arm.spring_length = 5
	arm.add_excluded_object(get_rid())
	pivot.add_child(arm)
	var camera := Camera3D.new()
	camera.current = true
	arm.add_child(camera)
func setup_character_animations(visual: Node3D) -> void:
	var manifest := FileAccess.get_file_as_string("res://player_visual.json")
	var parsed = JSON.parse_string(manifest)
	if typeof(parsed) != TYPE_DICTIONARY:
		return
	visual_yaw_offset = deg_to_rad(float(parsed.get("yaw_offset_degrees", 0.0)))
	fit_character_visual(visual, float(parsed.get("target_height", 1.8)))
	var requested = parsed.get("animation_mapping", {})
	if typeof(requested) != TYPE_DICTIONARY:
		return
	character_animator = find_animation_player(visual)
	if character_animator == null:
		return
	for state in requested:
		if not (state in ANIMATION_STATES or str(state).begins_with("cinematic_")):
			continue
		var clip = requested[state]
		if typeof(clip) != TYPE_STRING or clip.is_empty():
			continue
		if character_animator.has_animation(clip):
			character_clips[state] = clip
			var animation := character_animator.get_animation(clip)
			animation.loop_mode = Animation.LOOP_LINEAR if state in LOOPING_STATES else Animation.LOOP_NONE
		else:
			push_warning("Reviewed animation clip missing in Godot: " + clip)
	update_character_animation("idle")

# Scale the reviewed model to the gameplay capsule and stand it on the floor.
func fit_character_visual(visual: Node3D, target_height: float) -> void:
	var bounds := AABB()
	var first := true
	for node in visual.find_children("*", "MeshInstance3D", true, false):
		if node.mesh == null: continue
		var box: AABB = visual.global_transform.affine_inverse() * node.global_transform * node.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
	if first or bounds.size.y < 0.01 or target_height <= 0.0:
		return
	var factor := target_height / bounds.size.y
	visual.scale = Vector3.ONE * factor
	var center := bounds.get_center()
	visual.position = Vector3(-center.x * factor, -bounds.position.y * factor, -center.z * factor)
	visual_fit = {"source_height": bounds.size.y, "scale": factor, "height": target_height}

func find_animation_player(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:
		return node as AnimationPlayer
	for child in node.get_children():
		var found := find_animation_player(child)
		if found != null:
			return found
	return null

func clip_length(state: String, fallback: float, limit: float) -> float:
	if character_animator == null or not character_clips.has(state):
		return fallback
	return clampf(character_animator.get_animation(character_clips[state]).length, 0.1, limit)

func resolve_animation_state(state: String) -> String:
	var candidate := state
	while not candidate.is_empty():
		if character_clips.has(candidate):
			return candidate
		candidate = ANIMATION_FALLBACKS.get(candidate, "")
	return ""

func choose_animation_state() -> String:
	# Highest-priority active state that has a reviewed clip (directly or by fallback).
	var candidates := []
	if not alive: candidates.append("death")
	if cinematic_time > 0.0: candidates.append(cinematic_state)
	if hurt_animation_time > 0.0: candidates.append("hurt")
	if attack_animation_time > 0.0: candidates.append("attack")
	if not is_on_floor(): candidates.append("jump" if velocity.y > 0.0 else "fall")
	if landing_time > 0.0: candidates.append("land")
	candidates.append(("run" if running else "walk") if intent.length() > 0.15 else "idle")
	for state in candidates:
		if not resolve_animation_state(state).is_empty():
			return state
	return "idle"

func update_character_animation(state: String) -> void:
	if character_animator == null:
		return
	var resolved := resolve_animation_state(state)
	if resolved.is_empty():
		return
	var clip: String = character_clips[resolved]
	if state == animation_state and clip == current_character_clip and not restart_animation:
		return
	if clip == current_character_clip and restart_animation:
		character_animator.stop(true)
	character_animator.play(clip, ANIMATION_BLEND.get(state, 0.15))
	restart_animation = false
	current_character_clip = clip
	animation_state = state
	if animation_transitions.size() >= 96: animation_transitions.pop_front()
	animation_transitions.append(state)

func play_cinematic(state: String) -> bool:
	if not state.begins_with("cinematic_") or not character_clips.has(state) or not alive:
		return false
	cinematic_state = state
	cinematic_time = clip_length(state, 1.0, 8.0)
	restart_animation = true
	return true

func face_character_visual(delta: float) -> void:
	if character_visual == null: return
	var direction := intent
	if attack_animation_time > 0.0: direction = Vector3.FORWARD.rotated(Vector3.UP, yaw)
	if direction.length() > 0.15:
		var target := atan2(direction.x, direction.z) + visual_yaw_offset
		character_visual.rotation.y = lerp_angle(character_visual.rotation.y, target, minf(1.0, delta * 12.0))

func _unhandled_input(event: InputEvent) -> void:
	if not control_enabled: return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		yaw -= event.relative.x * 0.003
		pitch = clampf(pitch - event.relative.y * 0.003, -0.9, 0.4)
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ESCAPE: Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		if event.keycode == KEY_SPACE: jump_requested = true
		if event.keycode == KEY_F: attack()
		if event.keycode in [KEY_1, KEY_2, KEY_3]: special(int(event.keycode) - int(KEY_1))
	if event is InputEventJoypadButton and event.pressed:
		if event.button_index == JOY_BUTTON_A: jump_requested = true
		if event.button_index == JOY_BUTTON_X: attack()
		if event.button_index == JOY_BUTTON_RIGHT_SHOULDER: special(0)
		if event.button_index == JOY_BUTTON_LEFT_SHOULDER: special(1)
		if event.button_index == JOY_BUTTON_B: special(2)
	if event is InputEventMouseButton and event.pressed:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		if event.button_index == MOUSE_BUTTON_LEFT: attack()
func _physics_process(delta: float) -> void:
	cooldown = maxf(0, cooldown - delta)
	energy = minf(100, energy + delta * 8)
	flash_time = maxf(0, flash_time - delta)
	attack_animation_time = maxf(0, attack_animation_time - delta)
	hurt_animation_time = maxf(0, hurt_animation_time - delta)
	landing_time = maxf(0, landing_time - delta)
	cinematic_time = maxf(0, cinematic_time - delta)
	material.albedo_color = Color("f6a2a2") if flash_time > 0 and not world.reduced_motion else Color("8bd5f2")
	if not alive:
		attack_animation_time = 0.0
		hurt_animation_time = 0.0
		cinematic_time = 0.0
		update_character_animation("death")
		return
	if control_enabled:
		var axis := Vector2(float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A)), float(Input.is_physical_key_pressed(KEY_S)) - float(Input.is_physical_key_pressed(KEY_W)))
		for device in Input.get_connected_joypads():
			var stick := Vector2(Input.get_joy_axis(device, JOY_AXIS_LEFT_X), Input.get_joy_axis(device, JOY_AXIS_LEFT_Y))
			if stick.length() > 0.2: axis += stick
			var orbit := Vector2(Input.get_joy_axis(device, JOY_AXIS_RIGHT_X), Input.get_joy_axis(device, JOY_AXIS_RIGHT_Y))
			if orbit.length() > 0.2:
				yaw -= orbit.x * delta * 2.2
				pitch = clampf(pitch - orbit.y * delta * 1.6, -0.9, 0.4)
		intent = Vector3(axis.x, 0, axis.y).rotated(Vector3.UP, yaw).limit_length()
		running = Input.is_physical_key_pressed(KEY_SHIFT)
		for device in Input.get_connected_joypads():
			if Input.is_joy_button_pressed(device, JOY_BUTTON_LEFT_STICK): running = true
	pivot.rotation = Vector3(pitch, yaw, 0)
	velocity.x = intent.x * speed * (1.7 if running else 1.0)
	velocity.z = intent.z * speed * (1.7 if running else 1.0)
	velocity.y -= 22 * delta
	if jump_requested and is_on_floor(): velocity.y = 8
	jump_requested = false
	move_and_slide()
	var grounded := is_on_floor()
	if grounded and not was_on_floor: landing_time = clip_length("land", 0.0, 0.5)
	was_on_floor = grounded
	if intent.length() > 0.15 and cinematic_time > 0.0: cinematic_time = 0.0
	face_character_visual(delta)
	update_character_animation(choose_animation_state())
func damage(amount: float) -> void:
	if not alive: return
	flash_time = 0.15
	health = maxf(0, health - amount)
	alive = health > 0
	if alive:
		hurt_animation_time = clip_length("hurt", 0.35, 0.8)
		restart_animation = animation_state == "hurt"
	else:
		update_character_animation("death")
func clear_sight(target: Node3D) -> bool:
	var query := PhysicsRayQueryParameters3D.create(global_position + Vector3.UP, target.global_position + Vector3.UP)
	query.exclude = [get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	return hit.is_empty() or hit.collider == target
func attack() -> int:
	if not alive or cooldown > 0: return 0
	cooldown = 0.5
	attack_animation_time = clip_length("attack", 0.45, 1.2)
	restart_animation = animation_state == "attack"
	var hit_count := 0
	var forward := Vector3.FORWARD.rotated(Vector3.UP, yaw)
	for enemy in world.enemies:
		var offset: Vector3 = enemy.global_position - global_position
		if enemy.alive and offset.length() < 2.8 and forward.dot(offset.normalized()) > 0.3 and clear_sight(enemy):
			enemy.damage(attack_power)
			hit_count += 1
	if world.campaign != null: world.campaign.feedback("Melee hit · %d damage" % attack_power if hit_count > 0 else "Melee · move close and face the raider")
	return hit_count
func special(slot: int) -> bool:
	if not alive or cooldown > 0 or energy < 40 or slot < 0 or slot >= abilities.size(): return false
	var ability: String = abilities[slot]
	energy -= 40
	cooldown = 1
	if ability == "heal": health = minf(100, health + 35)
	else:
		for enemy in world.enemies:
			var distance: float = global_position.distance_to(enemy.global_position)
			if enemy.alive and distance < (14 if ability == "lightning" else 5) and clear_sight(enemy):
				enemy.damage(45 if ability == "lightning" else 25)
	if world.campaign != null: world.campaign.feedback(ability.capitalize() + " cast · 40 energy")
	return true
