extends CharacterBody3D
var world: Node3D
var target: CharacterBody3D
var health := 100.0
var alive := true
var detection := 18.0
var cooldown := 0.0
var agent: NavigationAgent3D
var detected := false
var repath := 0.0
func _ready() -> void:
	var col := CollisionShape3D.new()
	var shape := CapsuleShape3D.new()
	shape.radius = 0.4
	shape.height = 1.8
	col.shape = shape
	col.position.y = 0.9
	add_child(col)
	var mesh := MeshInstance3D.new()
	mesh.mesh = CapsuleMesh.new()
	mesh.position.y = 0.9
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color.CRIMSON
	mesh.material_override = mat
	mesh.tree_exiting.connect(func(): mesh.mesh = null)
	add_child(mesh)
	agent = NavigationAgent3D.new()
	agent.path_desired_distance = 0.4
	agent.target_desired_distance = 1.4
	add_child(agent)
func damage(amount: float) -> void:
	if not alive: return
	health = maxf(0, health - amount)
	alive = health > 0
	if not alive:
		collision_layer = 0
		collision_mask = 0
		hide()
func _physics_process(delta: float) -> void:
	if not alive or not target.alive or not world.navigation_ready: return
	cooldown = maxf(0, cooldown - delta)
	var distance := global_position.distance_to(target.global_position)
	detected = distance < detection
	velocity.x = 0
	velocity.z = 0
	if detected:
		repath -= delta
		if repath <= 0:
			agent.target_position = target.global_position
			repath = 0.7
		if distance > 1.8:
			var direction := (agent.get_next_path_position() - global_position)
			direction.y = 0
			direction = direction.normalized()
			velocity.x = direction.x * 2.8
			velocity.z = direction.z * 2.8
		elif distance <= 1.8 and cooldown <= 0 and target.clear_sight(self):
			target.damage(12)
			cooldown = 1
	velocity.y -= 22 * delta
	move_and_slide()
