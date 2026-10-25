extends SceneTree
var errors: Array[String] = []
func check(ok: bool, message: String) -> void:
	if not ok: errors.append(message)
func _initialize() -> void:
	call_deferred("run")
func run() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	scene.set_process(false)
	check(scene.coins.size() == int(scene.settings.coins), "coin count")
	check(scene.enemies.size() == int(scene.settings.enemies), "enemy count")
	var before: Vector2 = scene.player
	scene.step(0.1, Vector2.RIGHT)
	check(is_equal_approx(scene.player.x - before.x, float(scene.settings.speed) * 0.1), "movement speed")
	scene.step(100, Vector2.RIGHT)
	check(scene.player.x <= 786, "bounds")
	scene.reset_game()
	scene.enemies.clear()
	while not scene.coins.is_empty():
		scene.player = scene.coins[0]
		scene.step(0, Vector2.ZERO)
	check(scene.finished and scene.victory and scene.score == int(scene.settings.coins), "collection victory")
	scene.reset_game()
	scene.coins.clear()
	scene.coins.append(Vector2(30, 80))
	scene.enemies.clear()
	scene.enemies.append(scene.player)
	scene.health = 1
	scene.step(0, Vector2.ZERO)
	check(scene.finished and not scene.victory, "contact defeat")
	scene.reset_game()
	check(not scene.finished and scene.health == 3 and scene.score == 0, "restart")
	scene.queue_free()
	await process_frame
	if errors.is_empty():
		print("FACTORY_SCENARIO_PASS")
		quit(0)
	else:
		printerr(errors)
		quit(1)
