extends Node2D
var settings: Dictionary
var player := Vector2(400, 300)
var coins: Array[Vector2] = []
var enemies: Array[Vector2] = []
var health := 3
var score := 0
var finished := false
var victory := false
var invulnerable := 0.0
var label: Label

func _ready() -> void:
	settings = JSON.parse_string(FileAccess.get_file_as_string("res://game.json"))
	label = Label.new()
	label.position = Vector2(18, 12)
	add_child(label)
	reset_game()

func reset_game() -> void:
	player = Vector2(400, 300)
	coins.clear()
	enemies.clear()
	health = 3
	score = 0
	finished = false
	victory = false
	invulnerable = 0.0
	for i in range(int(settings.coins)):
		coins.append(Vector2(55 + (i * 137) % 690, 85 + (i * 83) % 440))
	for i in range(int(settings.enemies)):
		enemies.append(Vector2(55 + (i * 173) % 690, 500))
	update_hud()
	queue_redraw()

func step(delta: float, direction: Vector2) -> void:
	if finished: return
	invulnerable = maxf(0, invulnerable - delta)
	player += direction.limit_length() * float(settings.speed) * delta
	player = player.clamp(Vector2(14, 65), Vector2(786, 586))
	for i in range(coins.size() - 1, -1, -1):
		if player.distance_to(coins[i]) < 23:
			coins.remove_at(i)
			score += 1
	for i in range(enemies.size()):
		enemies[i] = enemies[i].move_toward(player, 65 * delta)
		if invulnerable <= 0 and enemies[i].distance_to(player) < 25:
			health -= 1
			invulnerable = 1.0
	if health <= 0:
		finished = true
		victory = false
	elif coins.is_empty():
		finished = true
		victory = true
	update_hud()
	queue_redraw()

func _process(delta: float) -> void:
	var direction := Input.get_vector("ui_left", "ui_right", "ui_up", "ui_down")
	if Input.is_physical_key_pressed(KEY_A): direction.x -= 1
	if Input.is_physical_key_pressed(KEY_D): direction.x += 1
	if Input.is_physical_key_pressed(KEY_W): direction.y -= 1
	if Input.is_physical_key_pressed(KEY_S): direction.y += 1
	step(minf(delta, 0.1), direction)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_R:
		reset_game()

func update_hud() -> void:
	label.text = "Collect %d coins | Score %d | Health %d | WASD/arrows · R restart\n%s\nPrototype visuals · no approved production assets" % [settings.coins, score, health, ("VICTORY" if victory else "DEFEAT") if finished else "Avoid the red pursuers"]

func _draw() -> void:
	draw_rect(Rect2(0, 0, 800, 600), Color("172433"))
	for coin in coins: draw_circle(coin, 9, Color.GOLD)
	for enemy in enemies: draw_circle(enemy, 13, Color.CRIMSON)
	draw_circle(player, 13, Color(str(settings.color)))
