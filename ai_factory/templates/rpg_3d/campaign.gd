extends Node
# Small, deterministic prototype campaign. No approved character art is implied.
var world
var mission_index := 0
var stage := "briefing"
var play_seconds := 0.0
var xp := 0
var upgrades := 0
var inventory := {"potions": 3, "relics": 0}
var relics_found := 0
var guide_position := Vector3(-4, 0.1, 3)
var checkpoint: Dictionary = {}
var save_path := "user://campaign-v1.json"
var notice := ""
var notice_time := 0.0
var guide: Node3D
var relic: Node3D
var loading := false
var save_needs_preservation := false
var known_save_hash := ""
var preserved_save_path := ""
const TITLES = ["The Silent Watch", "Ashes of the Beacon", "The Last Light", "Echoes Beyond", "Dawn's Promise"]
const BRIEFINGS = ["Mira: Our beacon has gone dark. Clear the raiders, retrieve its light, and bring it home.", "Mira: The outer watch has fallen. Recover its scattered embers so we can rebuild.", "Mira: This is our final stand. Recover the heart of the beacon and restore our valley.", "Mira: A distant echo calls. Secure the pass and recover the lost light.", "Mira: One last patrol will keep the roads safe. Bring every ember home."]
func _ready() -> void:
	guide = world.make_marker(guide_position, Color("76e5f1"), "WARDEN MIRA · E / Y")
	relic = world.make_marker(relic_position(), Color("ffdb73"), "BEACON SHARD · E / Y")
	if not load_game():
		start_new_game()
		if not preserved_save_path.is_empty(): feedback("Previous save preserved at " + preserved_save_path.get_file())
func _process(delta: float) -> void:
	notice_time = maxf(0, notice_time - delta)
	if relic != null:
		relic.visible = stage == "relic"
		relic.position = relic_position()
		if not world.reduced_motion: relic.rotation.y += delta
	if not world.player.alive: return
	if stage != "victory": play_seconds += delta
	if stage == "combat":
		var living := false
		for enemy in world.enemies:
			if enemy.alive: living = true
		if not living:
			stage = "relic"
			feedback("Path cleared. Follow the golden shard marker.")
			save_game()
func mission_count() -> int: return int(world.settings.get("missions", 3))
func relic_target() -> int: return int(world.settings.get("mission_length", 1))
func relic_position() -> Vector3:
	var area := mini(mission_index, int(world.settings.areas) - 1)
	return Vector3(7 + area * 20, 0.1, 5 - relics_found * 6)
func mission_title() -> String:
	return TITLES[mini(mission_index, TITLES.size() - 1)]
func feedback(message: String) -> void:
	notice = message
	notice_time = 5
func objective_text() -> String:
	if not world.player.alive: return "DEFEAT · R / Start: retry mission checkpoint"
	if stage == "victory": return "VICTORY · Beacon Valley restored\nAll %d missions complete · N: new campaign" % mission_count()
	var prefix := "MISSION %d / %d · %s\n" % [mission_index + 1, mission_count(), mission_title()]
	if stage == "briefing": return prefix + "Speak to Warden Mira at the blue marker · E / Y"
	if stage == "combat":
		var living := 0
		for enemy in world.enemies:
			if enemy.alive: living += 1
		return prefix + "Defeat the raiders · %d remaining" % living
	if stage == "relic": return prefix + "Recover beacon shards at the gold marker · %d / %d · E / Y" % [relics_found, relic_target()]
	return prefix + "Return to Mira with the beacon light · E / Y"
func dialogue_text() -> String:
	if stage == "victory": return "Mira: Because you stood with us, the valley sees a new dawn.\nThe beacon is restored. Your completed campaign is saved."
	if stage == "briefing" and world.player.position.distance_to(guide_position) < 3:
		return BRIEFINGS[mini(mission_index, BRIEFINGS.size() - 1)] + "\nE / Y: accept mission"
	if stage == "return" and world.player.position.distance_to(guide_position) < 3:
		return "Mira: You brought it back. The valley has hope again.\nE / Y: complete mission · +100 XP"
	return ""
func ending_text() -> String:
	return "VICTORY · The beacon is restored.\nMira: Because you stood with us, the valley sees a new dawn.\nAll %d missions complete · N: begin a new campaign" % mission_count()
func interact() -> bool:
	if not world.player.alive: return false
	if stage in ["briefing", "return"]:
		if world.player.position.distance_to(guide_position) > 3:
			feedback("Move closer to Warden Mira's blue marker.")
			return false
		if stage == "briefing":
			stage = "combat"
			world.spawn_enemies(maxi(1, int(world.settings.enemies)) + mission_index + relic_target() - 1)
			feedback("Mission accepted. Clear the raiders; healing and potions can help.")
		else:
			xp += 100
			inventory.relics += 1
			mission_index += 1
			stage = "victory" if mission_index >= mission_count() else "briefing"
			relics_found = 0
			world.player.health = 100
			world.player.energy = 100
			feedback("Mission complete · +100 XP · checkpoint saved")
			checkpoint = snapshot()
		save_game()
		return true
	if stage == "relic":
		if world.player.position.distance_to(relic_position()) > 3:
			feedback("Move closer to the golden shard.")
			return false
		relics_found += 1
		if relics_found >= relic_target(): stage = "return"
		feedback("Beacon shard recovered · %d / %d" % [relics_found, relic_target()])
		save_game()
		return true
	return false
func on_enemy_defeated() -> void:
	if loading or stage != "combat": return
	xp += 25
	feedback("Raider defeated · +25 XP")
	save_game()
func purchase_upgrade() -> bool:
	var cost := 100 * (upgrades + 1)
	if not world.player.alive or upgrades >= 5 or xp < cost:
		feedback("Upgrade needs %d XP · current %d" % [cost, xp])
		return false
	xp -= cost
	upgrades += 1
	world.player.attack_power = 35 + upgrades * 10
	feedback("Blade upgraded · melee damage %d" % world.player.attack_power)
	# Keep purchases in the checkpoint without retaining rewards from a failed mission.
	if not checkpoint.is_empty() and int(checkpoint.xp) >= cost:
		checkpoint.xp -= cost
		checkpoint.upgrades = upgrades
	save_game()
	return true
func use_potion() -> bool:
	if not world.player.alive or inventory.potions <= 0 or world.player.health >= 100:
		feedback("No potion needed or inventory empty.")
		return false
	inventory.potions -= 1
	world.player.health = minf(100, world.player.health + 50)
	feedback("Potion used · +50 health")
	save_game()
	return true
func start_new_game() -> void:
	mission_index = 0
	play_seconds = 0
	stage = "briefing"
	xp = 0
	upgrades = 0
	inventory = {"potions": 3, "relics": 0}
	relics_found = 0
	world.player.health = 100
	world.player.energy = 100
	world.player.alive = true
	world.player.attack_power = 35
	world.player.position = Vector3.ZERO + Vector3.UP * 0.1
	world.player.velocity = Vector3.ZERO
	world.spawn_enemies(int(world.settings.enemies))
	for enemy in world.enemies: enemy.set_physics_process(false)
	checkpoint = snapshot()
	feedback("Welcome to Beacon Valley. Speak to Mira to begin.")
	save_game()
func retry_checkpoint() -> void:
	if checkpoint.is_empty(): return
	apply_snapshot(checkpoint.duplicate(true))
	feedback("Mission checkpoint restored. Rewards from the failed attempt reset.")
	save_game()
func snapshot() -> Dictionary:
	var foes: Array = []
	for enemy in world.enemies:
		foes.append({"health": enemy.health, "position": [enemy.position.x, enemy.position.y, enemy.position.z]})
	var p = world.player
	return {"play_seconds": play_seconds, "mission_index": mission_index, "stage": stage, "xp": xp, "upgrades": upgrades, "inventory": inventory.duplicate(), "relics_found": relics_found, "health": p.health, "energy": p.energy, "position": [p.position.x, p.position.y, p.position.z], "enemies": foes}
func apply_snapshot(data: Dictionary) -> void:
	loading = true
	play_seconds = float(data.get("play_seconds",0))
	mission_index = int(data.mission_index)
	stage = data.stage
	xp = int(data.xp)
	upgrades = int(data.upgrades)
	inventory = data.inventory.duplicate()
	relics_found = int(data.relics_found)
	var p = world.player
	p.health = float(data.health)
	p.energy = float(data.energy)
	p.alive = p.health > 0
	p.attack_power = 35 + upgrades * 10
	p.position = vector(data.position)
	p.velocity = Vector3.ZERO
	p.cooldown = 0
	world.spawn_enemies(data.enemies.size(), data.enemies)
	for i in range(data.enemies.size()):
		var enemy = world.enemies[i]
		enemy.position = vector(data.enemies[i].position)
		enemy.health = float(data.enemies[i].health)
		if enemy.health <= 0: enemy.damage(1)
		enemy.set_physics_process(stage == "combat" and enemy.alive)
	loading = false
func vector(value: Array) -> Vector3: return Vector3(float(value[0]), float(value[1]), float(value[2]))
func bounded(value, low: float, high: float) -> bool:
	return (typeof(value) == TYPE_INT or typeof(value) == TYPE_FLOAT) and is_finite(float(value)) and float(value) >= low and float(value) <= high
func valid_vector(value) -> bool:
	return value is Array and value.size() == 3 and bounded(value[0], -2000, 2000) and bounded(value[1], -2000, 2000) and bounded(value[2], -2000, 2000)
func valid_snapshot(data, saved_count: int = -1, saved_length: int = -1) -> bool:
	var count := mission_count() if saved_count < 0 else saved_count
	var length := relic_target() if saved_length < 0 else saved_length
	if not data is Dictionary: return false
	if data.has("play_seconds") and not bounded(data.play_seconds,0,315360000): return false
	for key in ["mission_index", "stage", "xp", "upgrades", "inventory", "relics_found", "health", "energy", "position", "enemies"]:
		if not data.has(key): return false
	if not bounded(data.mission_index, 0, count) or float(data.mission_index) != floor(float(data.mission_index)): return false
	if not data.stage in ["briefing", "combat", "relic", "return", "victory"]: return false
	if (data.stage == "victory") != (int(data.mission_index) == count): return false
	if not bounded(data.xp, 0, 100000) or not bounded(data.upgrades, 0, 5) or not bounded(data.relics_found, 0, length): return false
	if not data.inventory is Dictionary or not bounded(data.inventory.get("potions"), 0, 3) or not bounded(data.inventory.get("relics"), 0, count): return false
	if not bounded(data.health, 0, 100) or not bounded(data.energy, 0, 100) or not valid_vector(data.position): return false
	if not data.enemies is Array or data.enemies.size() > 20: return false
	for enemy in data.enemies:
		if not enemy is Dictionary or not bounded(enemy.get("health"), 0, 100) or not valid_vector(enemy.get("position")): return false
	return true
func valid_config(data) -> bool:
	if not data is Dictionary: return false
	for key in ["enemies", "areas", "speed", "abilities"]:
		if not data.has(key): return false
	for key in data:
		if not key in ["enemies", "areas", "speed", "abilities", "campaign", "missions", "mission_length", "town"]: return false
	for spec in [["enemies",0,12],["areas",1,5],["speed",2,12],["missions",1,5],["mission_length",1,3]]:
		var value = data.get(spec[0], 3 if spec[0] == "missions" else 1)
		if not bounded(value, spec[1], spec[2]) or float(value) != floor(float(value)): return false
	if data.get("campaign") != true or typeof(data.get("campaign")) != TYPE_BOOL: return false
	if data.has("town") and typeof(data.town) != TYPE_BOOL: return false
	if not data.abilities is Array or data.abilities.is_empty() or data.abilities.size() > 3: return false
	var seen: Array = []
	for ability in data.abilities:
		if not ability in ["heal", "shockwave", "lightning"] or ability in seen: return false
		seen.append(ability)
	return true
func preserve_existing_save() -> bool:
	if not FileAccess.file_exists(save_path):
		save_needs_preservation = false
		return true
	var backup := save_path + ".preserved-%d-%d" % [int(Time.get_unix_time_from_system()), Time.get_ticks_usec()]
	var suffix := 0
	while FileAccess.file_exists(backup):
		suffix += 1
		backup = save_path + ".preserved-%d-%d-%d" % [int(Time.get_unix_time_from_system()), Time.get_ticks_usec(), suffix]
	var result := DirAccess.rename_absolute(ProjectSettings.globalize_path(save_path), ProjectSettings.globalize_path(backup))
	if result != OK:
		feedback("Save blocked: original save could not be archived. It has been preserved unchanged.")
		return false
	preserved_save_path = backup
	save_needs_preservation = false
	known_save_hash = ""
	return true
func save_game() -> bool:
	# Preserve unknown external edits, malformed data and incompatible revisions before writing.
	if FileAccess.file_exists(save_path) and FileAccess.get_sha256(save_path) != known_save_hash:
		save_needs_preservation = true
	if save_needs_preservation and not preserve_existing_save(): return false
	var data := {"version": 1, "config": world.settings, "state": snapshot(), "checkpoint": checkpoint}
	var text := JSON.stringify(data)
	var file := FileAccess.open(save_path + ".tmp", FileAccess.WRITE)
	if file == null:
		feedback("Save failed: user data directory is unavailable.")
		return false
	file.store_string(text)
	file.close()
	var result := DirAccess.rename_absolute(ProjectSettings.globalize_path(save_path + ".tmp"), ProjectSettings.globalize_path(save_path))
	if result != OK: feedback("Save failed: could not replace save file.")
	else: known_save_hash = text.sha256_text()
	return result == OK
func load_game() -> bool:
	if not FileAccess.file_exists(save_path): return false
	save_needs_preservation = true
	var file := FileAccess.open(save_path, FileAccess.READ)
	if file == null or file.get_length() > 262144: return false
	var text := file.get_as_text()
	file.close()
	var parser := JSON.new()
	if parser.parse(text) != OK: return false
	var data = parser.data
	if not data is Dictionary or data.get("version") != 1 or not valid_config(data.get("config")): return false
	var old_count := int(data.config.get("missions", 3))
	var old_length := int(data.config.get("mission_length", 1))
	if not valid_snapshot(data.get("state"), old_count, old_length) or not valid_snapshot(data.get("checkpoint"), old_count, old_length): return false
	if data.config != world.settings:
		# Supported additions retain completed missions and earned progression. Reset the
		# active objective safely because terrain, enemy waves and shard targets may change.
		if old_count > mission_count(): return false
		var state: Dictionary = data.state.duplicate(true)
		state.stage = "victory" if int(state.mission_index) == mission_count() else "briefing"
		state.relics_found = 0
		state.health = 100
		state.energy = 100
		state.position = [0, 0.1, 0]
		state.enemies = []
		for i in range(int(world.settings.enemies)):
			state.enemies.append({"health": 100, "position": [8 + (i % int(world.settings.areas)) * 20, 0.3, -5 + (i % 5) * 2]})
		checkpoint = state.duplicate(true)
		apply_snapshot(state)
		# The prior configuration remains recoverable, including any partial objectives.
		if not save_game(): return true
		feedback("Save migrated: completed missions, XP and inventory kept. Current mission checkpoint renewed.")
		return true
	save_needs_preservation = false
	known_save_hash = text.sha256_text()
	checkpoint = data.checkpoint.duplicate(true)
	apply_snapshot(data.state)
	feedback("Saved campaign loaded.")
	return true
