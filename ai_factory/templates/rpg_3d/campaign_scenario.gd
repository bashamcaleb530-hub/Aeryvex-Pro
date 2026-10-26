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
	await frames(4)
	var c = world.campaign
	check(c != null, "enabled campaign controller exists")
	if c == null:
		finish()
		return
	var p = world.player
	p.control_enabled = false
	if "--verify-restart" in OS.get_cmdline_user_args():
		check(c.stage == "victory", "completed ending persisted across real process restart")
		check(c.mission_index == int(world.settings.missions), "all mission progress persisted")
		check(c.upgrades == 1 and c.inventory.potions == 2, "inventory and purchased upgrade persisted")
		check(c.xp > 0 and p.attack_power == 45, "XP and equipment stat persisted")
		check(c.ending_text().contains("restored"), "ending survives reload")
		finish(true)
		return
	if "--verify-migration" in OS.get_cmdline_user_args():
		check(c.stage == "briefing" and c.mission_index == 3, "added mission extends completed campaign")
		check(c.upgrades == 1 and c.inventory.potions == 2 and c.inventory.relics == 3, "revision preserves equipment and inventory")
		check(c.xp > 0 and p.attack_power == 45, "revision preserves XP and upgrade stat")
		check(c.checkpoint.mission_index == 3, "migrated checkpoint preserves completed missions")
		finish()
		return
	if "--verify-archive" in OS.get_cmdline_user_args():
		check(c.stage == "briefing" and c.mission_index == 0, "incompatible or malformed save starts fresh only after preservation")
		finish()
		return
	c.start_new_game()
	await frames(4)
	check(c.get("play_seconds") != null and float(c.get("play_seconds")) > 0, "active playtime is measured")
	check(c.stage == "briefing" and c.mission_index == 0, "new campaign starts with dialogue")
	check(c.objective_text().contains("Mira"), "readable first objective")
	p.position = Vector3(8,0.1,6)
	check(not c.interact(), "dialogue requires proximity")
	p.position = c.guide_position
	check(c.interact() and c.stage == "combat", "accept mission through NPC dialogue")
	for enemy in world.enemies: enemy.set_physics_process(false)
	p.damage(999)
	check(not p.alive, "combat defeat")
	c.retry_checkpoint()
	check(p.alive and p.health == 100 and c.stage == "briefing", "checkpoint restores mission and health")
	check(c.xp == 0, "retry cannot farm rewards")
	var accessibility := InputEventKey.new()
	accessibility.pressed = true
	accessibility.keycode = KEY_T
	world._unhandled_input(accessibility)
	check(world.large_text, "large text accessibility toggle")
	accessibility.keycode = KEY_M
	world._unhandled_input(accessibility)
	check(world.reduced_motion, "reduced motion accessibility toggle")
	var pad := InputEventJoypadButton.new()
	pad.pressed = true
	pad.button_index = JOY_BUTTON_Y
	p.position = c.guide_position
	world._unhandled_input(pad)
	check(c.stage == "combat", "gamepad interaction accepts mission")
	for enemy in world.enemies: enemy.set_physics_process(false)
	await frames(3)
	var foe = world.enemies[0]
	p.position = Vector3(0,0.1,0)
	foe.position = p.position + Vector3(0,0,-1.7)
	p.yaw = 0
	p.cooldown = 0
	await frames(2)
	pad.button_index = JOY_BUTTON_X
	p.control_enabled = true
	p._unhandled_input(pad)
	p.control_enabled = false
	check(foe.health == 65, "gamepad melee causes actual damage")
	c.retry_checkpoint()
	for mission in range(int(world.settings.missions)):
		p.position = c.guide_position
		check(c.interact() and c.stage == "combat", "mission dialogue %d" % mission)
		for enemy in world.enemies:
			enemy.set_physics_process(false)
		check(not c.interact(), "objective gate before combat")
		for enemy in world.enemies: enemy.damage(999)
		await frames(2)
		check(c.stage == "relic", "actual enemy defeat unlocks relic objective")
		for relic in range(c.relic_target()):
			p.position = c.relic_position()
			check(c.interact(), "recover physical relic with interaction")
		check(c.stage == "return", "relic target gates return")
		p.position = c.guide_position
		check(c.interact(), "return mission to NPC")
		check(c.mission_index == mission + 1, "mission completion advances progression")
	check(c.stage == "victory" and c.ending_text().contains("restored"), "complete campaign ending")
	check(c.inventory.relics == int(world.settings.missions), "quest inventory rewards")
	check(c.purchase_upgrade() and c.upgrades == 1 and p.attack_power == 45, "XP purchases upgrade with actual combat stat")
	p.health = 20
	check(c.use_potion() and p.health == 70 and c.inventory.potions == 2, "consumable inventory heals and decrements")
	check(c.save_game(), "save returns success")
	var before_xp: int = c.xp
	c.xp = 0
	p.health = 3
	check(c.load_game() and c.xp == before_xp and p.health == 70, "manual save/load restores state")
	check(c.stage == "victory", "load preserves completed ending")
	# A truncated or edited save must not erase current progress or crash startup.
	var valid_save := FileAccess.get_file_as_string(c.save_path)
	var file := FileAccess.open(c.save_path, FileAccess.WRITE)
	file.store_string('{"version":1,"mission_index":999}')
	file.close()
	check(not c.load_game() and c.stage == "victory", "malformed save rejected without mutation")
	file = FileAccess.open(c.save_path, FileAccess.WRITE)
	file.store_string(valid_save)
	file.close()
	if world.settings.get("town", false): check(world.town_nodes.size() > 0, "town prompt creates physical buildings and residents")
	finish()
func finish(restarted: bool = false) -> void:
	if current_scene != null: current_scene.queue_free()
	await process_frame
	print("CAMPAIGN_CHECKS: ", checks)
	if failures.is_empty():
		print("FACTORY_CAMPAIGN_RESTART_PASS" if restarted else "FACTORY_CAMPAIGN_PASS")
		quit(0)
	else:
		printerr(failures)
		quit(1)
