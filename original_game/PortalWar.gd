extends Node2D
# Original Aeryvex Pro playable combat slice. Godot 4.
const HERO = Color(0.28, 0.73, 1.0)
const ENEMY = Color(0.95, 0.20, 0.29)
const GOLD = Color(1.0, 0.78, 0.25)
const SCREEN = Vector2(1280, 720)
var player = Vector2(175, 365)
var hp = 100.0
var foes = []
var portal = Vector2(1050, 360)
var stage = 0 # 0=portal 1=battle 2=decision 3=duel 4=ending
var choice = ""
var boss_hp = 180.0
var boss = Vector2(920, 365)
var attack_cd = 0.0
var hit_flash = 0.0
var message = "Approach the Celestial Arch. Press E to enter."
var time_passed = 0.0
var rainbow = false
var enemy_spawned = false

func _ready() -> void:
	set_process(true)
	set_process_unhandled_key_input(true)

func _reset() -> void:
	player = Vector2(175, 365)
	hp = 100
	foes.clear()
	stage = 0
	choice = ""
	boss_hp = 180
	boss = Vector2(920, 365)
	attack_cd = 0
	message = "Approach the Celestial Arch. Press E to enter."
	enemy_spawned = false

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	if event.keycode == KEY_R:
		_reset()
	elif stage == 0 and event.keycode == KEY_E and player.distance_to(portal) < 115:
		stage = 1
		player = Vector2(165, 365)
		_spawn_wave()
		message = "THE SIEGE OF KHAROS: Defeat the invading soldiers. SPACE fires blue lightning."
	elif stage == 2 and event.keycode in [KEY_1, KEY_2]:
		choice = "friend" if event.keycode == KEY_1 else "royalty"
		stage = 3
		player = Vector2(190, 370)
		boss_hp = 180
		hp = min(100, hp + 45)
		message = "The commander appears! Win the lightning duel. Your decision is permanent."

func _spawn_wave() -> void:
	foes = []
	for i in range(6):
		foes.append({"pos": Vector2(650 + (i % 3) * 145, 170 + int(i / 3) * 350), "health": 45.0})
	enemy_spawned = true

func _process(delta: float) -> void:
	time_passed += delta
	attack_cd = max(0.0, attack_cd - delta)
	hit_flash = max(0.0, hit_flash - delta)
	if hp <= 0:
		message = "Defeated. Press R to restart the mission."
		queue_redraw()
		return
	if stage in [0, 1, 3]:
		var direction = Vector2.ZERO
		if Input.is_key_pressed(KEY_A) or Input.is_key_pressed(KEY_LEFT):
			direction.x -= 1
		if Input.is_key_pressed(KEY_D) or Input.is_key_pressed(KEY_RIGHT):
			direction.x += 1
		if Input.is_key_pressed(KEY_W) or Input.is_key_pressed(KEY_UP):
			direction.y -= 1
		if Input.is_key_pressed(KEY_S) or Input.is_key_pressed(KEY_DOWN):
			direction.y += 1
		var velocity = 385 if Input.is_key_pressed(KEY_SHIFT) else 225
		player += direction.normalized() * velocity * delta
		player = player.clamp(Vector2(32, 115), Vector2(1248, 655))
		if Input.is_key_pressed(KEY_SPACE) and attack_cd == 0:
			_attack()
	if stage == 1:
		for f in foes:
			var p: Vector2 = f["pos"]
			var toward = (player - p).normalized()
			f["pos"] = p + toward * 58.0 * delta
			if p.distance_to(player) < 48:
				hp -= 11.0 * delta
		if foes.is_empty() and enemy_spawned:
			stage = 2
			message = "YOUR CHOICE: 1 Save your friend OR 2 Protect the royal family."
	elif stage == 3:
		boss += (player - boss).normalized() * 70.0 * delta
		if boss.distance_to(player) < 82:
			hp -= 15.0 * delta
		if boss_hp <= 0:
			stage = 4
			message = "VICTORY: Kharos secured. Your choice now changes its future."
	queue_redraw()

func _attack() -> void:
	attack_cd = 0.35
	hit_flash = 0.17
	var reach = 145.0
	if stage == 1:
		for i in range(foes.size() - 1, -1, -1):
			if player.distance_to(foes[i]["pos"]) < reach:
				foes[i]["health"] -= 26.0
				if foes[i]["health"] <= 0:
					foes.remove_at(i)
	elif stage == 3 and player.distance_to(boss) < reach:
		boss_hp -= 23.0

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, SCREEN), Color("#0b1228"))
	for i in range(11):
		draw_line(Vector2(i * 128, 110), Vector2(i * 128, 680), Color("#273452"), 1)
	for i in range(5):
		draw_line(Vector2(0, 135 + i * 128), Vector2(1280, 135 + i * 128), Color("#273452"), 1)
	draw_rect(Rect2(0, 0, 1280, 92), Color("#111b38"))
	_title(Vector2(30, 35), "AERYVEX PRO  /  THRONES OF THE TEN GALAXIES", 28, GOLD)
	_title(Vector2(30, 65), "PORTAL WAR - PLAYABLE PROTOTYPE", 17, Color("#d9e6ff"))
	_title(Vector2(30, 705), "WASD/ARROWS move    SPACE lightning    SHIFT sprint    E enter portal    R restart", 17, Color("#c0d1f4"))
	if stage == 0:
		for r in [90, 73, 54]:
			draw_arc(portal, r, 0, TAU, 90, Color("#57d5ff"), 5.0)
		draw_circle(portal, 46, Color(0.12, 0.48, 0.82, 0.36))
		_title(Vector2(907, 235), "CELESTIAL ARCH", 20, GOLD)
	elif stage == 1:
		for f in foes:
			var p: Vector2 = f["pos"]
			draw_circle(p, 22, ENEMY)
			draw_arc(p, 27, 0, TAU, 36, Color("#ffc2c9"), 2.0)
	elif stage == 2:
		draw_rect(Rect2(150, 165, 980, 390), Color("#1b2549"))
		_title(Vector2(200, 248), "THE CITY WALLS ARE FALLING.", 34, GOLD)
		_title(Vector2(200, 315), "Your closest friend is trapped. The royal family is under attack.", 23, Color.WHITE)
		_title(Vector2(200, 387), "1  SAVE YOUR FRIEND - royal influence falls.", 24, HERO)
		_title(Vector2(200, 439), "2  PROTECT THE ROYAL FAMILY - your friend is lost.", 24, GOLD)
	elif stage == 3:
		draw_circle(boss, 40, ENEMY)
		draw_arc(boss, 47, 0, TAU, 48, Color("#ff7d93"), 4)
		_title(boss + Vector2(-95, -78), "DOMINION COMMANDER", 18, ENEMY)
		draw_rect(Rect2(boss.x - 70, boss.y - 65, 140 * max(0, boss_hp) / 180.0, 7), ENEMY)
	elif stage == 4:
		_title(Vector2(230, 300), "KHAROS IS UNDER AETHER PROTECTION", 35, GOLD)
		if choice == "friend":
			_title(Vector2(265, 375), "Your friend survives. The Crown Houses distrust you.", 24, HERO)
		else:
			_title(Vector2(245, 375), "Royal alliance secured. Your friend is remembered.", 24, HERO)
		_title(Vector2(410, 452), "Press R to replay and choose differently.", 20, Color.WHITE)
	if stage in [0, 1, 3]:
		draw_circle(player, 27, HERO)
		draw_circle(player, 14, Color("#b9f7ff"))
		if hit_flash > 0.0:
			for j in range(5):
				var endp = player + Vector2.from_angle(time_passed * 12 + j * TAU / 5) * (90 + 18 * sin(time_passed * 45))
				draw_line(player, endp, Color("#2faafa"), 5.0)
				draw_line(endp, endp + Vector2(12, -15), Color.WHITE, 2.0)
	draw_rect(Rect2(29, 97, 300, 9), Color("#302c39"))
	draw_rect(Rect2(29, 97, 300 * clamp(hp / 100.0, 0.0, 1.0), 9), Color("#66eebb"))
	_title(Vector2(29, 137), "HEALTH  %d" % int(max(0, hp)), 18, Color.WHITE)
	_title(Vector2(30, 172), message, 18, Color("#dce9ff"))

func _title(pos: Vector2, str_text: String, size: int, color: Color) -> void:
	draw_string(ThemeDB.fallback_font, pos, str_text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)
