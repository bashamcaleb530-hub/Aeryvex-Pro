extends SceneTree
var failures: Array[String] = []
var checks := 0
func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok: failures.append(message)
func frames(count: int) -> void:
	for i in range(count): await physics_frame
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var world = load("res://main.tscn").instantiate()
	root.add_child(world)
	current_scene = world
	# QA uses an isolated user directory and resets prior campaign evidence deterministically.
	if world.campaign != null:
		await frames(3)
		world.campaign.start_new_game()
	var p = world.player
	p.control_enabled = false
	for enemy in world.enemies: enemy.set_physics_process(false)
	await frames(20)
	check(p.is_on_floor(), "floor collision and gravity")
	check(world.enemies.size() == int(world.settings.enemies), "prompt enemy count")
	var origin: Vector3 = p.position
	p.intent = Vector3.FORWARD
	await frames(20)
	var walked: float = p.position.distance_to(origin)
	p.running = true
	await frames(20)
	check(p.position.distance_to(origin) - walked > walked * 1.3, "run faster than walk")
	p.intent = Vector3.ZERO
	p.running = false
	p.jump_requested = true
	await frames(8)
	check(p.position.y > 0.4, "jump rises")
	await frames(50)
	check(p.is_on_floor(), "jump lands")
	p.position = Vector3(0,0.1,0)
	p.intent = Vector3.RIGHT
	await frames(90)
	check(p.position.x < 2.7, "solid structure collision")
	p.intent = Vector3.ZERO
	p.position = Vector3(0,0.1,0)
	await frames(5)
	var path := NavigationServer3D.map_get_path(world.get_world_3d().navigation_map, Vector3(8,0,0), Vector3.ZERO, true)
	check(path.size() >= 3, "navigation routes around structure")
	if not world.enemies.is_empty():
		var enemy = world.enemies[0]
		enemy.position = Vector3(8,0.1,0)
		enemy.set_physics_process(true)
		await frames(600)
		check(enemy.detected and enemy.position.distance_to(p.position) < 3, "detection and navigation chase")
		await frames(100)
		check(p.health < 100, "enemy attacks damage player")
		enemy.set_physics_process(false)
		p.health = 100
		p.alive = true
		enemy.position = p.position + Vector3(0,0,-1.7)
		p.yaw = 0
		p.cooldown = 0
		await frames(2)
		check(p.attack() == 1 and enemy.health < 100, "melee contact damages enemy")
		check(p.attack() == 0, "melee cooldown")
		p.health = 40
		p.cooldown = 0
		var slot: int = p.abilities.find("heal")
		check(slot >= 0 and p.special(slot) and p.health > 40, "configured heal works")
		p.cooldown = 0
		p.energy = 0
		check(not p.special(slot), "energy gate")
		if "lightning" in p.abilities:
			p.cooldown = 0
			p.energy = 100
			var before: float = enemy.health
			check(p.special(p.abilities.find("lightning")) and enemy.health < before, "new lightning damages enemy")
		var original_abilities: Array = p.abilities
		p.abilities = original_abilities.duplicate()
		p.abilities.append("shockwave")
		p.cooldown = 0
		p.energy = 100
		enemy.health = 100
		check(p.special(p.abilities.find("shockwave")) and enemy.health == 75, "configurable shockwave damage")
		p.abilities = original_abilities
		enemy.damage(999)
		check(not enemy.alive and enemy.collision_layer == 0, "enemy defeat disables collision")
	if int(world.settings.areas) > 1:
		p.position = Vector3(20,1,0)
		await frames(35)
		check(p.is_on_floor(), "new area walkable floor")
		p.position = Vector3(8,0.1,6)
		p.intent = Vector3.RIGHT
		await frames(60)
		check(p.position.x > 10 and p.is_on_floor(), "walk across connected area seam")
		p.intent = Vector3.ZERO
	check(p.arm.spring_length == 5 and p.pivot != null, "third person camera and collision arm")
	p.position = Vector3(0,0.1,0)
	p.yaw = 0.6
	await frames(3)
	check(is_equal_approx(p.pivot.rotation.y,0.6), "camera orbit yaw")
	p.yaw = 0
	var wall = world.block(Vector3(0,1.5,2),Vector3(2,3,0.5),Color.GRAY)
	await frames(5)
	check(p.arm.get_hit_length() < 4, "camera avoids obstruction")
	wall.queue_free()
	var adapter = load("res://character_import.gd").new()
	world.add_child(adapter)
	check(not adapter.configure("res://assets/missing.glb",{},{}) and adapter.status == "APPROVAL_REQUIRED", "unapproved asset rejected")
	p.damage(999)
	check(not p.alive and p.attack() == 0, "player defeat prevents attack")
	var restart := InputEventKey.new()
	restart.keycode = KEY_R
	restart.pressed = true
	world._unhandled_input(restart)
	await frames(5)
	world = current_scene
	check(world != null and world.player.health == 100, "restart restores fresh scene")
	world.queue_free()
	await process_frame
	print("RPG_CHECKS: ", checks)
	if failures.is_empty():
		print("FACTORY_SCENARIO_PASS")
		quit(0)
	else:
		printerr(failures)
		quit(1)
