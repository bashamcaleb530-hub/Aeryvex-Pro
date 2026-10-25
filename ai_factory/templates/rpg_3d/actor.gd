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
	mesh.tree_exiting.connect(func(): mesh.mesh = null)
	add_child(mesh)
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
	if event is InputEventMouseButton and event.pressed:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		if event.button_index == MOUSE_BUTTON_LEFT: attack()
func _physics_process(delta: float) -> void:
	cooldown = maxf(0, cooldown - delta)
	energy = minf(100, energy + delta * 8)
	if not alive: return
	if control_enabled:
		var axis := Vector2(float(Input.is_physical_key_pressed(KEY_D)) - float(Input.is_physical_key_pressed(KEY_A)), float(Input.is_physical_key_pressed(KEY_S)) - float(Input.is_physical_key_pressed(KEY_W)))
		intent = Vector3(axis.x, 0, axis.y).rotated(Vector3.UP, yaw).limit_length()
		running = Input.is_physical_key_pressed(KEY_SHIFT)
	pivot.rotation = Vector3(pitch, yaw, 0)
	velocity.x = intent.x * speed * (1.7 if running else 1.0)
	velocity.z = intent.z * speed * (1.7 if running else 1.0)
	velocity.y -= 22 * delta
	if jump_requested and is_on_floor(): velocity.y = 8
	jump_requested = false
	move_and_slide()
func damage(amount: float) -> void:
	if not alive: return
	health = maxf(0, health - amount)
	alive = health > 0
func clear_sight(target: Node3D) -> bool:
	var query := PhysicsRayQueryParameters3D.create(global_position + Vector3.UP, target.global_position + Vector3.UP)
	query.exclude = [get_rid()]
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	return hit.is_empty() or hit.collider == target
func attack() -> int:
	if not alive or cooldown > 0: return 0
	cooldown = 0.5
	var hit_count := 0
	var forward := Vector3.FORWARD.rotated(Vector3.UP, yaw)
	for enemy in world.enemies:
		var offset: Vector3 = enemy.global_position - global_position
		if enemy.alive and offset.length() < 2.8 and forward.dot(offset.normalized()) > 0.3 and clear_sight(enemy):
			enemy.damage(35)
			hit_count += 1
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
	return true
