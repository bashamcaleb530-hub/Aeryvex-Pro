extends SceneTree
## Real-engine QA for a bound reviewed character: visual, fit and animation states.
var failures: Array[String] = []
var checks := 0
var report := {}
func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok: failures.append(message)
func frames(count: int) -> void:
	for i in range(count): await physics_frame
func playing(p, state: String) -> bool:
	var resolved: String = p.resolve_animation_state(state)
	return p.animation_state == state and not resolved.is_empty() and p.character_animator.assigned_animation == p.character_clips[resolved]
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var manifest = JSON.parse_string(FileAccess.get_file_as_string("res://player_visual.json"))
	check(typeof(manifest) == TYPE_DICTIONARY, "player visual manifest")
	var world = load("res://main.tscn").instantiate()
	root.add_child(world)
	current_scene = world
	if world.campaign != null:
		await frames(3)
		world.campaign.start_new_game()
	var p = world.player
	p.control_enabled = false
	for enemy in world.enemies: enemy.set_physics_process(false)
	await frames(10)
	var visual = p.get_node_or_null("ReviewedPlayerVisual")
	check(visual != null and p.character_visual == visual, "reviewed visual loaded in player")
	check(p.collision_layer != 0 and p.is_on_floor(), "gameplay collision retained with visual")
	if not p.visual_fit.is_empty():
		check(absf(p.visual_fit.height - float(manifest.get("target_height", 1.8))) < 0.01, "visual fitted to gameplay height")
	report["fit"] = p.visual_fit
	var mapping: Dictionary = manifest.get("animation_mapping", {}) if typeof(manifest) == TYPE_DICTIONARY else {}
	var mapped := []
	for state in mapping:
		if state in p.ANIMATION_STATES or str(state).begins_with("cinematic_"): mapped.append(state)
	report["mapped_states"] = mapped
	if mapped.is_empty():
		report["animation"] = "NO_REVIEWED_CLIPS_MAPPED"
	else:
		check(p.character_animator != null, "embedded AnimationPlayer found")
		for state in mapped:
			check(p.character_clips.has(state), "mapped clip resolves in engine: " + str(state))
		if p.resolve_animation_state("idle") != "":
			check(playing(p, "idle"), "idle at rest")
		if p.resolve_animation_state("walk") != "":
			p.intent = Vector3.RIGHT
			await frames(12)
			check(playing(p, "walk"), "walk while moving")
			var before: float = p.character_animator.current_animation_position
			await frames(6)
			check(p.character_animator.current_animation_position != before, "walk clip advances")
			check(absf(angle_difference(visual.rotation.y, atan2(1.0, 0.0) + p.visual_yaw_offset)) < 0.35, "visual faces movement")
			p.running = true
			await frames(6)
			check(playing(p, "run"), "run (or walk fallback) while running")
			p.running = false
			p.intent = Vector3.ZERO
			await frames(6)
			check(p.animation_state == "idle" or p.resolve_animation_state("idle") == "", "return to idle after moving")
		if p.resolve_animation_state("jump") != "":
			p.jump_requested = true
			await frames(4)
			check(playing(p, "jump"), "jump while rising")
			var airborne := false
			for i in range(90):
				await physics_frame
				if p.animation_state in ["fall", "jump"]: airborne = true
				if p.is_on_floor() and i > 10: break
			check(airborne and p.is_on_floor(), "airborne then lands")
			await frames(40)
			check(p.animation_state == "idle", "idle after landing")
		if p.resolve_animation_state("attack") != "":
			p.cooldown = 0
			p.attack()
			await frames(2)
			check(playing(p, "attack"), "attack plays on melee")
			await frames(int(p.clip_length("attack", 0.45, 1.2) * 60) + 15)
			check(p.animation_state != "attack", "attack returns to locomotion")
		if p.resolve_animation_state("hurt") != "":
			p.damage(10)
			await frames(2)
			check(playing(p, "hurt") and p.alive, "hurt reaction on damage")
			await frames(int(p.clip_length("hurt", 0.35, 0.8) * 60) + 15)
			check(p.animation_state != "hurt", "hurt reaction ends")
		for state in mapped:
			if str(state).begins_with("cinematic_"):
				check(p.play_cinematic(state), "cinematic starts: " + str(state))
				await frames(3)
				check(playing(p, state), "cinematic plays: " + str(state))
				p.cinematic_time = 0.0
				await frames(20)
		if p.resolve_animation_state("death") != "":
			p.damage(999)
			await frames(2)
			check(not p.alive and playing(p, "death"), "death plays on defeat")
			await frames(int(p.clip_length("death", 1.0, 5.0) * 60) + 20)
			check(p.animation_state == "death" and p.character_animator.assigned_animation == p.character_clips["death"], "death pose holds")
			p.health = 100
			p.alive = true
			await frames(30)
			check(p.animation_state != "death", "revive leaves death state")
		report["transitions"] = p.animation_transitions
	world.queue_free()
	await process_frame
	print("CHARACTER_REPORT: " + JSON.stringify(report))
	print("CHARACTER_CHECKS: ", checks)
	if failures.is_empty():
		print("FACTORY_CHARACTER_PASS")
		quit(0)
	else:
		printerr(failures)
		quit(1)
