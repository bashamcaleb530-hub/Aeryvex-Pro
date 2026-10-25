extends Node3D
const Actor = preload("res://actor.gd")
const Enemy = preload("res://enemy.gd")
var settings: Dictionary
var player: CharacterBody3D
var enemies: Array[CharacterBody3D] = []
var navigation_ready := false
var region: NavigationRegion3D
var label: Label
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
	add_child(player)
	player.position = Vector3(0, 0.3, 0)
	for i in range(int(settings.enemies)):
		var enemy := Enemy.new()
		enemy.world = self
		enemy.target = player
		add_child(enemy)
		enemy.position = Vector3(8 + (i % int(settings.areas)) * 20,0.3,-4 + (i % 4)*2)
		enemies.append(enemy)
	var canvas := CanvasLayer.new()
	add_child(canvas)
	label = Label.new()
	label.position = Vector2(12,12)
	canvas.add_child(label)
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
func _process(_delta: float) -> void:
	var living := 0
	for enemy in enemies:
		if enemy.alive: living += 1
	label.text = "3D RPG prototype · WASD walk · Shift run · Space jump\nMouse orbit · F/click melee · 1/2/3 abilities · Esc release mouse · R restart\nHP %d Energy %d Enemies %d Areas %d · Abilities %s\nPrimitive test visuals: approved characters NOT supplied" % [player.health,player.energy,living,settings.areas,str(settings.abilities)]
	if not player.alive: label.text += "\nDEFEAT · R restart"
	elif living == 0: label.text += "\nVICTORY · explore or R restart"
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_R:
		get_tree().reload_current_scene()
