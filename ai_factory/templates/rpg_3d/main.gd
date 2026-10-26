extends Node3D
const Actor = preload("res://actor.gd")
const Enemy = preload("res://enemy.gd")
const Campaign = preload("res://campaign.gd")
var settings: Dictionary
var player: CharacterBody3D
var enemies: Array[CharacterBody3D] = []
var navigation_ready := false
var region: NavigationRegion3D
var label: Label
var objective: Label
var dialogue: Label
var toast: Label
var health_bar: ProgressBar
var energy_bar: ProgressBar
var campaign
var town_nodes: Array[Node3D] = []
var reduced_motion := false
var large_text := false
func block(pos: Vector3, size: Vector3, color: Color) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.position = pos
	var collision := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	collision.shape = shape
	body.add_child(collision)
	var mesh := MeshInstance3D.new()
	var box := BoxMesh.new()
	box.size = size
	mesh.mesh = box
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = 0.85
	mesh.material_override = material
	mesh.tree_exiting.connect(func(): mesh.mesh = null)
	body.add_child(mesh)
	add_child(body)
	return body
func _ready() -> void:
	settings = JSON.parse_string(FileAccess.get_file_as_string("res://game.json"))
	var environment := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("7898b3")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color.WHITE
	env.ambient_light_energy = 0.6
	environment.environment = env
	add_child(environment)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-55,-25,0)
	sun.shadow_enabled = true
	add_child(sun)
	for i in range(int(settings.areas)):
		block(Vector3(i * 20, -0.5, 0), Vector3(20,1,20), Color("53794d") if i % 2 == 0 else Color("b59c6d"))
		block(Vector3(i * 20 + 4, 1.5, 0), Vector3(2,3,6), Color("66778a"))
	block(Vector3(-10,1,0), Vector3(1,2,20), Color.GRAY)
	block(Vector3(int(settings.areas)*20-10,1,0), Vector3(1,2,20), Color.GRAY)
	for z in [-10,10]: block(Vector3((int(settings.areas)-1)*10,1,z), Vector3(int(settings.areas)*20,2,1), Color.GRAY)
	build_navigation()
	player = Actor.new()
	player.world = self
	player.speed = float(settings.speed)
	player.abilities = settings.abilities
	player.position = Vector3(0, 0.3, 0)
	add_child(player)
	if not settings.get("campaign", false): spawn_enemies(int(settings.enemies))
	build_hud()
	if settings.get("town", false): build_town()
	if settings.get("campaign", false):
		campaign = Campaign.new()
		campaign.world = self
		add_child(campaign)
	call_deferred("enable_navigation")
func build_navigation() -> void:
	region = NavigationRegion3D.new()
	var nav := NavigationMesh.new()
	var vertices := PackedVector3Array()
	var polygons: Array[PackedInt32Array] = []
	for x in range(-9,int(settings.areas)*20-10):
		for z in range(-9,9):
			# Exclude structure footprints plus actor clearance; all areas connect.
			var local_x := posmod(x + 10,20) - 10
			if local_x >= 2 and local_x <= 5 and z >= -4 and z <= 3: continue
			var start := vertices.size()
			vertices.append_array(PackedVector3Array([Vector3(x,0, z),Vector3(x,0,z+1),Vector3(x+1,0,z+1),Vector3(x+1,0,z)]))
			polygons.append(PackedInt32Array([start,start+1,start+2,start+3]))
	nav.vertices = vertices
	for polygon in polygons: nav.add_polygon(polygon)
	region.navigation_mesh = nav
	add_child(region)
func enable_navigation() -> void:
	NavigationServer3D.map_force_update(get_world_3d().navigation_map)
	navigation_ready = true
func spawn_enemies(count: int, states: Array = []) -> void:
	for enemy in enemies:
		enemy.collision_layer = 0
		enemy.collision_mask = 0
		enemy.set_physics_process(false)
		remove_child(enemy)
		enemy.queue_free()
	enemies.clear()
	for i in range(count):
		var enemy := Enemy.new()
		enemy.world = self
		enemy.target = player
		enemy.position = Vector3(8 + (i % int(settings.areas)) * 20,0.3,-5 + (i % 5)*2)
		if i < states.size():
			var pos: Array = states[i].position
			enemy.position = Vector3(float(pos[0]),float(pos[1]),float(pos[2]))
		add_child(enemy)
		enemies.append(enemy)
func make_marker(pos: Vector3, color: Color, title: String) -> Node3D:
	var marker := Node3D.new()
	marker.position = pos
	var mesh := MeshInstance3D.new()
	var shape := PrismMesh.new()
	shape.size = Vector3(0.7,1.2,0.7)
	mesh.mesh = shape
	mesh.position.y = 2.7
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.emission_enabled = true
	material.emission = color
	mesh.material_override = material
	mesh.tree_exiting.connect(func(): mesh.mesh = null)
	marker.add_child(mesh)
	var text := Label3D.new()
	text.text = title
	text.position.y = 3.7
	text.font_size = 30
	text.outline_size = 8
	text.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	marker.add_child(text)
	add_child(marker)
	return marker
func build_town() -> void:
	# Explicit primitive village: collidable houses and visible prototype residents.
	for z in [-6, 6]:
		town_nodes.append(block(Vector3(-6,1.25,z), Vector3(3,2.5,3), Color("51647e")))
		town_nodes.append(block(Vector3(-6,2.8,z), Vector3(3.6,0.6,3.6), Color("b77f59")))
	town_nodes.append(make_marker(Vector3(-7,0,0), Color("8bc8a1"), "BEACON VALLEY · prototype town"))
func panel(pos: Vector2, size: Vector2) -> Panel:
	var node := Panel.new()
	node.position = pos
	node.size = size
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.025,0.045,0.09,0.93)
	style.border_color = Color("387fbe")
	style.set_border_width_all(1)
	style.set_corner_radius_all(8)
	node.add_theme_stylebox_override("panel", style)
	return node
func hud_label(parent: Node, pos: Vector2, size: Vector2, font_size: int = 16) -> Label:
	var text := Label.new()
	text.position = pos
	text.size = size
	text.add_theme_font_size_override("font_size", font_size)
	text.add_theme_color_override("font_color", Color("e9f3ff"))
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	parent.add_child(text)
	return text
func meter(parent: Node, pos: Vector2, color: Color) -> ProgressBar:
	var bar := ProgressBar.new()
	bar.position = pos
	bar.size = Vector2(340,12)
	bar.show_percentage = false
	var fill := StyleBoxFlat.new()
	fill.bg_color = color
	fill.set_corner_radius_all(4)
	bar.add_theme_stylebox_override("fill", fill)
	parent.add_child(bar)
	return bar
func build_hud() -> void:
	var canvas := CanvasLayer.new()
	add_child(canvas)
	var top := panel(Vector2(12,12), Vector2(776,118))
	canvas.add_child(top)
	objective = hud_label(top, Vector2(14,10), Vector2(748,54), 18)
	label = hud_label(top, Vector2(14,66), Vector2(748,24))
	health_bar = meter(top, Vector2(14,98), Color("6ddebd"))
	energy_bar = meter(top, Vector2(408,98), Color("73b8ff"))
	var bottom := panel(Vector2(12,440), Vector2(776,148))
	canvas.add_child(bottom)
	dialogue = hud_label(bottom, Vector2(14,10), Vector2(748,76))
	var controls := hud_label(bottom, Vector2(14,86), Vector2(748,62), 13)
	controls.text = "WASD / L stick move · Shift / L3 run · Space / A jump · F / X melee · Mouse / R stick camera\n1/2/3 or RB/LB/B abilities · E / Y interact · H / D-pad up potion · U / D-pad right upgrade\nF5 save · F9 load · R / Start retry · Esc mouse · T large text · M reduced motion · PROTOTYPE ART"
	toast = hud_label(canvas, Vector2(30,388), Vector2(740,44), 18)
	toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
func _process(_delta: float) -> void:
	var living := 0
	for enemy in enemies:
		if enemy.alive: living += 1
	health_bar.value = player.health
	energy_bar.value = player.energy
	if campaign != null:
		objective.text = campaign.objective_text() + " · %ds" % int(campaign.play_seconds)
		label.text = "HP %d / 100 · ENERGY %d · XP %d · BLADE +%d · POTIONS %d · RELICS %d" % [player.health,player.energy,campaign.xp,campaign.upgrades,campaign.inventory.potions,campaign.inventory.relics]
		dialogue.text = campaign.dialogue_text()
		if dialogue.text.is_empty(): dialogue.text = "Beacon Valley · primitive prototype characters and scenery · %s" % str(settings.abilities)
		toast.text = campaign.notice if campaign.notice_time > 0 else ""
	else:
		objective.text = "3D RPG prototype · Clear the arena · %d enemies remaining" % living
		label.text = "HP %d    Energy %d    Areas %d · %s" % [player.health,player.energy,settings.areas,str(settings.abilities)]
		dialogue.text = "Primitive test visuals: approved characters NOT supplied"
		if not player.alive: objective.text = "DEFEAT · R / Start restart"
		elif living == 0: objective.text = "VICTORY · Explore or R / Start restart"
func _unhandled_input(event: InputEvent) -> void:
	var key := 0
	if event is InputEventKey and event.pressed and not event.echo: key = event.keycode
	var button := -1
	if event is InputEventJoypadButton and event.pressed: button = event.button_index
	if key == KEY_T:
		large_text = not large_text
		for text in [objective,label,dialogue,toast]: text.add_theme_font_size_override("font_size", 20 if large_text else 16)
	if key == KEY_M:
		reduced_motion = not reduced_motion
		if campaign != null: campaign.feedback("Reduced motion " + ("on" if reduced_motion else "off"))
	if campaign != null:
		if key == KEY_E or button == JOY_BUTTON_Y: campaign.interact()
		if key == KEY_H or button == JOY_BUTTON_DPAD_UP: campaign.use_potion()
		if key == KEY_U or button == JOY_BUTTON_DPAD_RIGHT: campaign.purchase_upgrade()
		if key == KEY_F5:
			if campaign.save_game(): campaign.feedback("Campaign saved.")
		if key == KEY_F9:
			if not campaign.load_game(): campaign.feedback("No compatible valid save found.")
		if key == KEY_N and campaign.stage == "victory": campaign.start_new_game()
		if key == KEY_R or button == JOY_BUTTON_START: campaign.retry_checkpoint()
	elif key == KEY_R or button == JOY_BUTTON_START:
		get_tree().reload_current_scene()
