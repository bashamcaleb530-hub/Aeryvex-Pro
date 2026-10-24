extends Spatial
const CombatRules = preload("res://scripts/CombatRules.gd")
const FighterVisual = preload("res://scripts/FighterVisual.gd")
const EnemyBrain = preload("res://scripts/EnemyBrain.gd")
const DuelRules = preload("res://scripts/DuelRules.gd")
const FrontsRules = preload("res://scripts/FrontsRules.gd")
const SquadRules = preload("res://scripts/SquadRules.gd")
const ArenaArchitecture = preload("res://scripts/ArenaArchitecture.gd")
# Playable Godot 3.x 3D arena prototype. No external assets required.
const ROSTER = ["Anakin", "Dooku", "Obi-Wan", "Windu", "Qui-Gon", "Yoda", "Vader", "Palpatine", "Grievous"]
const COLORS = [Color(0.2,0.55,1), Color(1,0.2,0.16), Color(0.2,0.55,1), Color(0.55,0.35,1), Color(0.2,0.75,0.4), Color(0.2,0.85,0.5), Color(1,0.12,0.1), Color(1,0.2,0.12), Color(0.28,0.85,0.8)]
var player
var enemy
var cam
var info
var hp_label
var menu_label
var mode = "Duel"
var selected = 0
var enemy_index = 1
var hp = [100.0,100.0]
var stamina = [100.0,100.0]
var cooldown = [0.0,0.0]  # Force cooldown (separate from melee attacks).
var strikes = []
var stagger = [0.0,0.0]
var guard_break = [0.0,0.0]
var parry_window = [0.0,0.0]
var ai_block = false
var ai_block_time = 0.0
var ai_difficulty = 1  # 0 Rookie, 1 Veteran, 2 Master
var ai_reaction_time = 0.0
var ai_saw_windup = false
var ai_reacted = false
var ai_dodge_cooldown = 0.0
var ai_strafe_side = 1.0
var ai_strafe_clock = 0.0
var attack_buffer = ""
var invuln = [0.0,0.0]
var block = false
var paused = false
var match_done = false
var round_pending = false
var duel_round = 1
var duel_score = [0, 0]
var duel_winner = -1
var wave = 1
var ai_clock = 0.0
# Go 2: camera-relative movement, analog controller input and mouse orbit.
var yaw = 0.0
var camera_pitch = deg2rad(28.0)
var camera_distance = 7.6
var mouse_orbit = false
var move_velocity = Vector3.ZERO
var enemy_move_speed = 0.0
const WALK_SPEED = 5.0
const GUARD_SPEED = 2.45
const SPRINT_SPEED = 7.2
const STICK_DEADZONE = 0.22
const ARENA_EDGE = 13.0
var elapsed = 0.0
var hits = 0
var wins = 0
var training = false
var combat_log = ""
var fronts_posts = []
var fronts_tickets = [120.0, 120.0]
var fronts_clock = 0.0
var fronts_ai_goal = -1
var fronts_soldiers = []
var fronts_cover = []
var fronts_hit_flashes = []
var shot_tracers = []
const SOLDIERS_PER_TEAM = 3
const SOLDIER_RESPAWN = 5.0
const SAVE_PATH = "user://aeryvex_progress.json"

func _ready():
    randomize()
    _load_progress()
    _make_input()
    _make_world()
    _make_hud()
    _create_fronts_posts()
    _create_fronts_cover()
    _spawn()
    _create_tracer_pool()

func _load_progress():
    var file = File.new()
    if not file.file_exists(SAVE_PATH):
        return
    if file.open(SAVE_PATH, File.READ) != OK:
        return
    var result = JSON.parse(file.get_as_text())
    file.close()
    if result.error != OK or typeof(result.result) != TYPE_DICTIONARY:
        return
    var data = result.result
    wins = max(0, int(data.get("wins", 0)))
    selected = int(clamp(int(data.get("hero", 0)), 0, ROSTER.size()-1))
    ai_difficulty = EnemyBrain.skill(int(data.get("ai_level", 1)))
    enemy_index = (selected+1)%ROSTER.size()

func _save_progress():
    var file = File.new()
    if file.open(SAVE_PATH, File.WRITE) == OK:
        file.store_string(to_json({"version": 2, "wins": wins, "hero": selected, "ai_level": ai_difficulty}))
        file.close()

func _bind_key(action, code):
    if not InputMap.has_action(action):
        InputMap.add_action(action, STICK_DEADZONE)
    var e = InputEventKey.new()
    e.scancode = code
    InputMap.action_add_event(action, e)

func _bind_pad_button(action, button_index):
    if not InputMap.has_action(action):
        InputMap.add_action(action, STICK_DEADZONE)
    var e = InputEventJoypadButton.new()
    e.button_index = button_index
    InputMap.action_add_event(action, e)

func _bind_pad_axis(action, axis_index, axis_direction):
    if not InputMap.has_action(action):
        InputMap.add_action(action, STICK_DEADZONE)
    var e = InputEventJoypadMotion.new()
    e.axis = axis_index
    e.axis_value = axis_direction
    InputMap.action_add_event(action, e)

func _make_input():
    # InputMap handles both keyboard and analog sticks. Never add raw stick
    # values separately or keyboard + gamepad input will double movement speed.
    var keys = {
        "move_forward":KEY_W, "move_back":KEY_S,
        "move_left":KEY_A, "move_right":KEY_D,
        "light_attack":KEY_J, "heavy_attack":KEY_K,
        "force_push":KEY_F, "dodge":KEY_SPACE,
        "block_attack":KEY_L, "sprint":KEY_SHIFT,
        "switch_hero":KEY_H, "mode_change":KEY_M,
        "restart_match":KEY_R, "pause_game":KEY_P,
        "camera_left":KEY_Q, "camera_right":KEY_E,
        "recenter_camera":KEY_C, "difficulty_change":KEY_T,
        "next_round":KEY_N
    }
    for action in keys:
        _bind_key(action, keys[action])
    # Godot 3 joypad constants: A=0, B=1, Y=3, LB=4, RB=5,
    # Start=7, right-stick press=9. Exact mappings can vary by device.
    var buttons = {
        "light_attack":0, "dodge":1, "force_push":3,
        "block_attack":4, "heavy_attack":5,
        "pause_game":7, "recenter_camera":9
    }
    for action in buttons:
        _bind_pad_button(action, buttons[action])
    _bind_pad_axis("move_left", 0, -1.0)
    _bind_pad_axis("move_right", 0, 1.0)
    _bind_pad_axis("move_forward", 1, -1.0)
    _bind_pad_axis("move_back", 1, 1.0)
    _bind_pad_axis("camera_left", 2, -1.0)
    _bind_pad_axis("camera_right", 2, 1.0)
    _bind_pad_axis("camera_up", 3, -1.0)
    _bind_pad_axis("camera_down", 3, 1.0)
    _bind_pad_axis("sprint", 6, 1.0)

func _input_vector():
    var x = Input.get_action_strength("move_right") - Input.get_action_strength("move_left")
    var y = Input.get_action_strength("move_back") - Input.get_action_strength("move_forward")
    var input_axis = Vector2(x, y)
    if input_axis.length() < STICK_DEADZONE:
        return Vector2.ZERO
    return input_axis.normalized() * min(1.0, input_axis.length())

func _world_move(axis):
    # At yaw=0, pushing forward moves toward world -Z. Rotate that motion
    # with the camera, without changing the character's opponent lock-on.
    var v = Vector3(axis.x * cos(yaw) + axis.y * sin(yaw), 0,
                    -axis.x * sin(yaw) + axis.y * cos(yaw))
    return v.normalized() * min(1.0, axis.length()) if v.length() > 0 else Vector3.ZERO

func _clamp_arena(pos):
    return Vector3(clamp(pos.x, -ARENA_EDGE, ARENA_EDGE), 0, clamp(pos.z, -ARENA_EDGE, ARENA_EDGE))

func _step_player(delta, axis, wants_sprint):
    if not is_instance_valid(player):
        return
    var direction = _world_move(axis)
    var can_sprint = wants_sprint and not block and stamina[0] >= 12.0 and direction.length() > 0.01
    var speed = GUARD_SPEED if block else (SPRINT_SPEED if can_sprint else WALK_SPEED)
    if can_sprint:
        stamina[0] = max(0, stamina[0] - 10.0 * delta)
    var target = direction * speed
    var response = 13.0 if direction.length() > 0.01 else 20.0
    move_velocity = move_velocity.linear_interpolate(target, min(1.0, delta * response))
    player.translation = _clamp_arena(player.translation + move_velocity * delta)
    if player.translation.x <= -ARENA_EDGE or player.translation.x >= ARENA_EDGE:
        move_velocity.x = 0
    if player.translation.z <= -ARENA_EDGE or player.translation.z >= ARENA_EDGE:
        move_velocity.z = 0

func _camera_target():
    return player.translation + Vector3(0, 1.3, 0)

func _camera_goal():
    var cosine = cos(camera_pitch)
    return _camera_target() + Vector3(sin(yaw) * cosine, sin(camera_pitch), cos(yaw) * cosine) * camera_distance

func _orbit_camera(delta):
    yaw += (Input.get_action_strength("camera_right") - Input.get_action_strength("camera_left")) * delta * 2.25
    camera_pitch = clamp(camera_pitch +
        (Input.get_action_strength("camera_up") - Input.get_action_strength("camera_down")) * delta * 1.35,
        deg2rad(10.0), deg2rad(65.0))
    cam.translation = cam.translation.linear_interpolate(_camera_goal(), min(1.0, delta * 7.0))
    cam.look_at(_camera_target(), Vector3.UP)

func _mat(c,metal=0.0):
    var m=SpatialMaterial.new()
    m.albedo_color=c
    m.metallic=metal
    m.roughness=0.45
    return m

func _cube(parent,pos,size,color):
    var mesh=CubeMesh.new()
    mesh.size=size
    var node=MeshInstance.new()
    node.mesh=mesh
    node.material_override=_mat(color)
    node.translation=pos
    parent.add_child(node)
    return node

func _sphere(parent,pos,r,color):
    var mesh=SphereMesh.new()
    mesh.radius=r
    mesh.height=r*2
    var node=MeshInstance.new()
    node.mesh=mesh
    node.material_override=_mat(color)
    node.translation=pos
    parent.add_child(node)
    return node

func _make_world():
    VisualServer.set_default_clear_color(Color(0.025,0.035,0.07))
    _cube(self,Vector3(0,-0.27,0),Vector3(30,0.5,30),Color(0.34,0.36,0.42))
    for i in range(-7,8):
        _cube(self,Vector3(i*2,0.006,0),Vector3(0.035,0.01,30),Color(0.47,0.48,0.54))
        _cube(self,Vector3(0,0.006,i*2),Vector3(30,0.01,0.035),Color(0.47,0.48,0.54))
    # Architectural columns are now generated by ArenaArchitecture.
    _setup_cinematic_lighting()
    var architecture = ArenaArchitecture.new()
    architecture.name = "TempleArchitecture"
    add_child(architecture)
    cam=Camera.new()
    cam.current=true
    cam.fov=70
    add_child(cam)

# Go 30: Character readability / cinematic stage lighting, kept GLES2 friendly.
# One shadow-casting key, one shadowless cool fill, and restrained warm rims.
func _setup_cinematic_lighting():
    var key = DirectionalLight.new()
    key.name = "WarmKeySun"
    key.rotation_degrees = Vector3(-58, 27, 0)
    key.light_color = Color(1.0, 0.90, 0.78)
    key.light_energy = 0.90
    key.shadow_enabled = true
    add_child(key)
    var fill = DirectionalLight.new()
    fill.name = "CoolFill"
    fill.rotation_degrees = Vector3(-30, -127, 0)
    fill.light_color = Color(0.48, 0.66, 1.0)
    fill.light_energy = 0.28
    fill.shadow_enabled = false
    add_child(fill)
    for side in [-1.0, 1.0]:
        var rim = OmniLight.new()
        rim.name = "WarmRimLeft" if side < 0.0 else "WarmRimRight"
        rim.translation = Vector3(side * 7.0, 4.6, -4.0)
        rim.light_color = Color(1.0, 0.54, 0.31)
        rim.light_energy = 0.48
        rim.omni_range = 11.0
        rim.shadow_enabled = false
        add_child(rim)
    var ambient = WorldEnvironment.new()
    ambient.name = "ArenaEnvironment"
    var env = Environment.new()
    env.background_mode = Environment.BG_COLOR
    env.background_color = Color(0.025, 0.032, 0.060)
    env.ambient_light_color = Color(0.39, 0.46, 0.59)
    env.ambient_light_energy = 0.50
    ambient.environment = env
    add_child(ambient)

func _fighter(idx):
    # Jointed procedural visual: combat and movement still use the root Spatial.
    var root = FighterVisual.new()
    root.name = "Fighter_%d" % idx
    add_child(root)
    root.configure(idx, COLORS[idx])
    return root

func _spawn(keep_duel_score = false):
    if not keep_duel_score:
        duel_round = 1
        duel_score = [0, 0]
        duel_winner = -1
    round_pending = false
    _clear_fronts_soldiers()
    if mode == "Fronts":
        _reset_fronts()
    if is_instance_valid(player): player.queue_free()
    if is_instance_valid(enemy): enemy.queue_free()
    player=_fighter(selected)
    enemy=_fighter(enemy_index)
    player.translation=Vector3(0,0,3.7)
    enemy.translation=Vector3(0,0,-3.7)
    hp=[100.0,100.0]
    stamina=[100.0,100.0]
    cooldown=[0.0,0.0]
    invuln=[0.0,0.0]
    stagger=[0.0,0.0]
    guard_break=[0.0,0.0]
    parry_window=[0.0,0.0]
    strikes=[_new_strike(),_new_strike()]
    ai_block=false
    ai_block_time=0.0
    ai_reaction_time=0.0
    ai_saw_windup=false
    ai_reacted=false
    ai_dodge_cooldown=0.0
    ai_strafe_side = -1.0 if randf() < 0.5 else 1.0
    ai_strafe_clock = 1.75
    attack_buffer=""
    match_done=false
    ai_clock=EnemyBrain.next_attack_delay(ai_difficulty)
    block=false
    move_velocity=Vector3.ZERO
    enemy_move_speed=0.0
    combat_log="Fight!"
    if is_instance_valid(cam):
        cam.translation=_camera_goal()
        cam.look_at(_camera_target(), Vector3.UP)
    _set_fronts_visible(mode == "Fronts")
    _set_fronts_cover_visible(mode == "Fronts")
    if mode == "Fronts":
        _create_fronts_soldiers()
    _hud_update()

func _label(parent,xy,content,sz):
    var l=Label.new()
    l.rect_position=xy
    l.text=content
    l.add_color_override("font_color",Color(0.9,0.95,1))
    parent.add_child(l)
    return l

func _make_hud():
    var layer=CanvasLayer.new()
    add_child(layer)
    var panel=Control.new()
    layer.add_child(panel)
    hp_label=_label(panel,Vector2(20,20),"",16)
    info=_label(panel,Vector2(20,50),"",14)
    menu_label=_label(panel,Vector2(20,95),"WASD/left stick move | Shift/LT sprint | J/A light | K/RB heavy | L/LB block/parry\nSpace/B dodge | F/Y Force | Q/E/right stick orbit | RMB drag | Wheel zoom | C recenter\nH hero | M mode | T AI skill | R restart | N next round | P/Start pause",13)

func _hud_update():
    if hp_label==null:return
    hp_label.text="%s  HP %d  Guard %d      VS      %s  HP %d  Guard %d" % [ROSTER[selected],int(hp[0]),int(stamina[0]),ROSTER[enemy_index],int(hp[1]),int(stamina[1])]
    var phase = strikes[0]["phase"] if strikes.size() >= 1 else "idle"
    var threat = " | ENEMY WINDUP!" if strikes.size() >= 2 and strikes[1]["phase"] == "windup" else ""
    var duel_text = " | Duel round %d, score %d-%d" % [duel_round, duel_score[0], duel_score[1]] if mode == "Duel" else ""
    var fronts_text = " | Tickets %d:%d | Posts %s | Squads %d:%d | Capture %s" % [int(fronts_tickets[0]), int(fronts_tickets[1]), _fronts_status(), _living_soldiers(0), _living_soldiers(1), _fronts_capture_detail()] if mode == "Fronts" else ""
    info.text="Mode: %s%s%s | AI: %s | Wave %d | Wins %d | Hits %d | Attack: %s%s | %s" % [mode,duel_text,fronts_text,EnemyBrain.NAMES[ai_difficulty],wave,wins,hits,phase,threat,combat_log]

func _input(event):
    if event is InputEventMouseButton:
        if event.button_index == BUTTON_RIGHT:
            mouse_orbit = event.pressed
        elif event.pressed and event.button_index == BUTTON_WHEEL_UP:
            camera_distance = max(4.0, camera_distance - 0.6)
        elif event.pressed and event.button_index == BUTTON_WHEEL_DOWN:
            camera_distance = min(11.0, camera_distance + 0.6)
    elif event is InputEventMouseMotion and mouse_orbit:
        yaw -= event.relative.x * 0.007
        camera_pitch = clamp(camera_pitch + event.relative.y * 0.006, deg2rad(10.0), deg2rad(65.0))

    if event.is_action_pressed("pause_game") and not event.is_echo():
        paused = not paused
        combat_log = "Paused" if paused else "Resumed"
        _hud_update()
        return
    if paused:
        return
    if event.is_action_pressed("recenter_camera") and not event.is_echo():
        yaw = 0.0
        camera_pitch = deg2rad(28.0)
    if event.is_action_pressed("switch_hero") and not event.is_echo():
        selected = (selected + 1) % ROSTER.size()
        enemy_index = (selected + 1) % ROSTER.size()
        _save_progress()
        _spawn()
    if event.is_action_pressed("mode_change") and not event.is_echo():
        var modes = ["Duel", "Survival", "Training", "Skirmish", "Story", "Fronts"]
        mode = modes[(modes.find(mode) + 1) % modes.size()]
        wave = 1
        _spawn()
    if event.is_action_pressed("difficulty_change") and not event.is_echo():
        ai_difficulty = (ai_difficulty + 1) % EnemyBrain.NAMES.size()
        _save_progress()
        _spawn()
        combat_log = "AI: %s" % EnemyBrain.NAMES[ai_difficulty]
        _hud_update()
    if event.is_action_pressed("restart_match") and not event.is_echo():
        wave = 1
        _spawn()
    if event.is_action_pressed("next_round") and not event.is_echo() and round_pending:
        duel_round += 1
        _spawn(true)
        combat_log = "Duel round %d - Fight!" % duel_round
        _hud_update()
        return
    if match_done or round_pending:
        return
    if event.is_action_pressed("light_attack") and not event.is_echo():
        _attack(0, "light")
    if event.is_action_pressed("heavy_attack") and not event.is_echo():
        _attack(0, "heavy")
    if event.is_action_pressed("force_push") and not event.is_echo():
        _force()
    if event.is_action_pressed("dodge") and not event.is_echo() and stamina[0] >= 20.0 and stagger[0] <= 0.0 and guard_break[0] <= 0.0:
        stamina[0] -= 20.0
        invuln[0] = 0.42
        var dodge_dir = _world_move(_input_vector())
        if dodge_dir.length() < 0.01:
            dodge_dir = player.translation - enemy.translation
            dodge_dir.y = 0
            dodge_dir = dodge_dir.normalized() if dodge_dir.length() > 0.01 else Vector3(0, 0, 1)
        player.translation = _clamp_arena(player.translation + dodge_dir * 1.8)
        move_velocity = Vector3.ZERO
        combat_log = "Dodge"
        _hud_update()

func _new_strike():
    return {"phase": "idle", "kind": "light", "time": 0.0, "connected": false}

func _attack(who, kind):
    if match_done or paused or not CombatRules.ATTACKS.has(kind):
        return false
    var data = CombatRules.ATTACKS[kind]
    var phase = strikes[who]["phase"]
    if who == 0 and phase == "recovery" and strikes[who]["time"] <= 0.18:
        attack_buffer = kind  # One queued combo strike, no spam queue.
        combat_log = "Next strike queued"
        return true
    if not CombatRules.can_start(phase, stamina[who], data["cost"], stagger[who], guard_break[who]):
        return false
    if (who == 0 and block) or (who == 1 and ai_block):
        return false
    stamina[who] -= data["cost"]
    strikes[who] = {"phase": "windup", "kind": kind, "time": data["windup"], "connected": false}
    if who == 0:
        combat_log = "Heavy windup" if kind == "heavy" else "Light windup"
    else:
        combat_log = "Enemy %s incoming!" % kind
    _hud_update()
    return true

func _advance_strike(who, delta):
    var strike = strikes[who]
    if strike["phase"] == "idle":
        return
    if stagger[who] > 0.0 or guard_break[who] > 0.0 or match_done:
        strikes[who] = _new_strike()
        return
    strike["time"] -= delta
    var transitions = 0
    while strike["time"] <= 0.0 and strike["phase"] != "idle" and transitions < 4:
        transitions += 1
        var overrun = -strike["time"]
        var data = CombatRules.ATTACKS[strike["kind"]]
        if strike["phase"] == "windup":
            strike["phase"] = "active"
            strike["time"] = data["active"] - overrun
            if not strike["connected"]:
                strike["connected"] = true
                _resolve_swing(who, data)
                if match_done or strikes[who] != strike:
                    return  # Match ended or wave reset during contact resolution.
        elif strike["phase"] == "active":
            strike["phase"] = "recovery"
            strike["time"] = data["recovery"] - overrun
        else:
            strike["phase"] = "idle"
            strike["time"] = 0.0
            if who == 0 and attack_buffer != "" and not match_done:
                var followup = attack_buffer
                attack_buffer = ""
                _attack(0, followup)
    _animate_saber(who)

func _animate_saber(who):
    # Retained as a combat animation hook. FighterVisual now owns the wrist,
    # saber and full-body motion, updated each frame by _update_fighter_poses.
    var fighter = player if who == 0 else enemy
    if not is_instance_valid(fighter):
        return
    _set_visual_pose(who, 0.0)

func _set_visual_pose(who, delta):
    var fighter = player if who == 0 else enemy
    if not is_instance_valid(fighter):
        return
    var strike = strikes[who]
    var phase = strike["phase"]
    var progress = 0.0
    if phase != "idle":
        var duration = CombatRules.ATTACKS[strike["kind"]][phase]
        progress = clamp(1.0 - strike["time"] / duration,0.0,1.0)
    var vel = move_velocity.length() if who == 0 else enemy_move_speed
    var guarding = block if who == 0 else ai_block
    var defeated = hp[who] <= 0.0
    fighter.animate_pose(delta, vel, phase, strike["kind"], progress, guarding,
        invuln[who] > 0.0, stagger[who] > 0.0 or guard_break[who] > 0.0, defeated)

func _update_fighter_poses(delta):
    for who in range(2):
        _set_visual_pose(who, delta)

func _resolve_swing(who, data):
    var src = player if who == 0 else enemy
    var dst = enemy if who == 0 else player
    if not is_instance_valid(src) or not is_instance_valid(dst):
        return
    var hero_hit = CombatRules.in_arc(src.global_transform, dst.global_transform.origin, data["reach"], data["arc"])
    if hero_hit:
        _damage(1-who, data["damage"], who, data["guard_damage"])
    # Fronts melee sweeps can also connect with nearby enemy infantry.
    var troop_hits = 0
    if mode == "Fronts":
        for unit in fronts_soldiers:
            if unit["team"] == who or unit["hp"] <= 0.0:
                continue
            if CombatRules.in_arc(src.global_transform, unit["node"].global_transform.origin, data["reach"], data["arc"]):
                _hurt_soldier(unit, data["damage"])
                troop_hits += 1
    if not hero_hit and troop_hits == 0:
        combat_log = "Your swing missed" if who == 0 else "Enemy swing missed"
    elif troop_hits > 0:
        combat_log = "%d infantry struck" % troop_hits

func _is_facing(defender, attacker):
    var src = player if defender == 0 else enemy
    var dst = player if attacker == 0 else enemy
    return CombatRules.in_arc(src.global_transform, dst.global_transform.origin, 99.0, 0.15)

func _damage(target, amount, attacker = -1, guard_damage_amount = -1.0):
    if match_done:
        return
    var defense = block if target == 0 else ai_block
    defense = defense and guard_break[target] <= 0.0 and stagger[target] <= 0.0
    if attacker >= 0 and defense:
        defense = _is_facing(target, attacker)
    if guard_damage_amount < 0.0:
        defense = false  # Force powers bypass saber guard.
    var result = CombatRules.guard_result(amount, guard_damage_amount, stamina[target], defense,
        parry_window[target] > 0.0, invuln[target] > 0.0)
    stamina[target] = result["guard_left"]
    hp[target] = max(0.0, hp[target] - result["hp_loss"])
    if result["defender_stagger"] > 0.0:
        guard_break[target] = result["defender_stagger"]
        strikes[target] = _new_strike()
    if attacker >= 0 and result["attacker_stagger"] > 0.0:
        stagger[attacker] = result["attacker_stagger"]
        strikes[attacker] = _new_strike()
    if result["outcome"] == "parry":
        parry_window[target] = 0.0
        combat_log = "PARRY! Opponent staggered" if target == 0 else "Enemy parried!"
    elif result["outcome"] == "block":
        combat_log = "Guarded strike"
    elif result["outcome"] == "guard_break":
        combat_log = "GUARD BROKEN!"
    elif result["outcome"] == "dodge":
        combat_log = "Dodged!"
    else:
        hits += 1
        combat_log = "Hit: %d" % int(result["hp_loss"])
    if hp[target] <= 0.0:
        # Duel uses a best-of-three match; score only the final match victory.
        # Other modes preserve their existing death/wave transitions.
        if mode == "Duel":
            var round_winner = 1 - target
            duel_score[round_winner] += 1
            round_pending = true
            strikes = [_new_strike(), _new_strike()]
            block = false
            ai_block = false
            if DuelRules.has_winner(duel_score):
                duel_winner = round_winner
                match_done = true
                round_pending = false
                if duel_winner == 0:
                    wins += 1
                    _save_progress()
                combat_log = "MATCH VICTORY! Press R for new duel." if duel_winner == 0 else "MATCH DEFEAT. Press R to retry."
            else:
                combat_log = "Round won! Press N for next round." if round_winner == 0 else "Round lost. Press N for next round."
        elif mode == "Fronts":
            if target == 0:
                fronts_tickets[0] = max(0.0, fronts_tickets[0] - 8.0)
            else:
                fronts_tickets[1] = max(0.0, fronts_tickets[1] - 8.0)
            _spawn_fronts_combatants()
            _fronts_resolve()
        elif target == 1:
            wins += 1
            _save_progress()
            combat_log = "Victory! Press R to replay."
            if mode == "Survival":
                wave += 1
                enemy_index = (enemy_index+1) % ROSTER.size()
                _spawn()
                combat_log = "Survival wave %d" % wave
            elif mode == "Training":
                _spawn()
                combat_log = "Training opponent reset"
            else:
                match_done = true
        else:
            match_done = true
            combat_log = "Defeat. Press R to replay."
    _hud_update()

func _force():
    if cooldown[0] > 0 or stamina[0] < 35 or strikes[0]["phase"] != "idle" or stagger[0] > 0.0 or guard_break[0] > 0.0:
        return
    cooldown[0]=1.2
    stamina[0]-=35
    if player.translation.distance_to(enemy.translation)<5.0:
        _damage(1,24)
        if mode == "Fronts":
            for unit in fronts_soldiers:
                if unit["team"] == 1 and unit["hp"] > 0.0 and player.translation.distance_to(unit["node"].translation) <= 5.0:
                    _hurt_soldier(unit, 24.0)
        if not match_done:
            var away=(enemy.translation-player.translation).normalized()
            enemy.translation=_clamp_arena(enemy.translation+away*2.2)
        combat_log="Force push!"
    else:combat_log="Force out of range"

func _process(delta):
    if paused:
        return
    elapsed += delta
    _step_tracers(delta)
    if not match_done and not round_pending:
        var was_blocking = block
        block = Input.is_action_pressed("block_attack") and guard_break[0] <= 0.0 and stagger[0] <= 0.0
        if block and not was_blocking:
            parry_window[0] = 0.24
        for i in range(2):
            cooldown[i] = max(0.0, cooldown[i] - delta)
            invuln[i] = max(0.0, invuln[i] - delta)
            stagger[i] = max(0.0, stagger[i] - delta)
            guard_break[i] = max(0.0, guard_break[i] - delta)
            parry_window[i] = max(0.0, parry_window[i] - delta)
            if (i == 0 and not block) or (i == 1 and not ai_block):
                stamina[i] = min(100.0, stamina[i] + delta * 14.0)
        if guard_break[0] > 0.0:
            block = false
        if stagger[0] <= 0.0 and guard_break[0] <= 0.0:
            _step_player(delta, _input_vector(), Input.is_action_pressed("sprint"))
        else:
            move_velocity = Vector3.ZERO
        _run_enemy(delta)
        if mode == "Fronts":
            _step_fronts_soldiers(delta)
            _update_fronts(delta)
        player.look_at(Vector3(enemy.translation.x, player.translation.y, enemy.translation.z), Vector3.UP)
        enemy.look_at(Vector3(player.translation.x, enemy.translation.y, player.translation.z), Vector3.UP)
        _advance_strike(0, delta)
        if not match_done:
            _advance_strike(1, delta)
    else:
        move_velocity = Vector3.ZERO
    _update_fighter_poses(delta)
    _orbit_camera(delta)
    if int(elapsed * 5) % 2 == 0:
        _hud_update()

func _enemy_dodge():
    if stamina[1] < 20.0 or ai_dodge_cooldown > 0.0:
        return false
    stamina[1] -= 20.0
    invuln[1] = 0.33
    ai_dodge_cooldown = 2.2
    ai_block_time = 0.0
    ai_block = false
    var away = enemy.translation - player.translation
    away.y = 0.0
    if away.length() < 0.01:
        away = Vector3(0, 0, 1)
    var side = Vector3(-away.z, 0, away.x).normalized() * ai_strafe_side
    enemy.translation = _clamp_arena(enemy.translation + (away.normalized() + side * 0.6).normalized() * 1.6)
    combat_log = "Enemy evaded!"
    return true

func _run_enemy(delta):
    enemy_move_speed = 0.0
    ai_clock -= delta
    ai_dodge_cooldown = max(0.0, ai_dodge_cooldown - delta)
    ai_block_time = max(0.0, ai_block_time - delta)
    ai_block = ai_block_time > 0.0
    if stagger[1] > 0.0 or guard_break[1] > 0.0:
        ai_block = false
        ai_block_time = 0.0
        return

    var old_enemy_position = enemy.translation
    var dist = enemy.translation.distance_to(player.translation)
    var winding = strikes[0]["phase"] == "windup" and dist < 3.3
    var free_to_defend = strikes[1]["phase"] == "idle"
    if winding and not ai_saw_windup:
        ai_saw_windup = true
        ai_reacted = false
        ai_reaction_time = EnemyBrain.reaction_delay(ai_difficulty)
    elif not winding:
        ai_saw_windup = false
        ai_reacted = false
    if winding and not ai_reacted and free_to_defend:
        ai_reaction_time = max(0.0, ai_reaction_time - delta)
        if ai_reaction_time <= 0.0:
            ai_reacted = true
            var choice = EnemyBrain.defense_for_threat(ai_difficulty, stamina[1],
                ai_dodge_cooldown <= 0.0 and stamina[1] >= 20.0, randf())
            if choice == "dodge":
                _enemy_dodge()
            elif choice == "guard" or choice == "parry":
                ai_block_time = max(0.40, strikes[0]["time"] + 0.19)
                ai_block = true
                if choice == "parry":
                    parry_window[1] = 0.16
                    combat_log = "Enemy parry stance!"
                else:
                    combat_log = "Enemy guarding"

    ai_strafe_clock -= delta
    if ai_strafe_clock <= 0.0:
        ai_strafe_side = -ai_strafe_side
        ai_strafe_clock = rand_range(1.2, 2.2)
    var desired = EnemyBrain.desired_distance(stamina[1], winding)
    var navigation_target = player.translation
    if mode == "Fronts" and dist > 3.4:
        navigation_target = _fronts_enemy_objective()
        desired = 0.75
    var step = EnemyBrain.steering(enemy.translation, navigation_target, desired, ai_strafe_side)
    var movement_speed = 2.0 + min(1.0, float(wave - 1) * 0.07)
    if ai_block:
        movement_speed *= 0.48
    if strikes[1]["phase"] != "idle":
        movement_speed *= 0.38
    enemy.translation = _clamp_arena(enemy.translation + step * delta * movement_speed)
    if delta > 0.0:
        enemy_move_speed = enemy.translation.distance_to(old_enemy_position) / delta

    if ai_clock <= 0.0:
        ai_clock = EnemyBrain.next_attack_delay(ai_difficulty) * rand_range(0.88, 1.14)
        var choice_attack = EnemyBrain.attack_for_opening(ai_difficulty,
            enemy.translation.distance_to(player.translation), stamina[1],
            strikes[1]["phase"], ai_block or winding, randf())
        if choice_attack != "":
            _attack(1, choice_attack)


# Go 7: command-post control. Neutral posts require sustained uncontested presence.
# Team tickets also drain from holding the majority of posts. This is a
# playable two-combatant objective prototype, NOT full squad battles yet.
func _create_fronts_posts():
    var locations = [Vector3(-7, 0, 0), Vector3(0, 0, 0), Vector3(7, 0, 0)]
    for i in range(locations.size()):
        var post = Spatial.new()
        post.name = "CommandPost_%d" % i
        add_child(post)
        post.translation = locations[i]
        var base = _cube(post, Vector3(0, 0.12, 0), Vector3(1.65, 0.24, 1.65), Color(0.20, 0.23, 0.30))
        var flag = _cube(post, Vector3(0, 1.2, 0), Vector3(0.2, 2.0, 0.2), Color(0.4, 0.4, 0.5))
        fronts_posts.append({"node": post, "flag": flag, "progress": 0.0})
    _set_fronts_visible(false)

# Three low barricades on each side of the battlefield. They are visual
# anchors for the infantry AI, not collision bodies (heroes can still pass).
func _create_fronts_cover():
    for side in range(2):
        for slot in range(3):
            var z = 5.1 if side == 0 else -5.1
            var center = Vector3(-7.0 + 7.0 * float(slot), 0, z)
            var root = Spatial.new()
            root.name = "FrontsCover_%d_%d" % [side, slot]
            add_child(root)
            root.translation = center
            _cube(root, Vector3(0, 0.62, 0), Vector3(2.0, 1.25, 0.65), Color(0.25, 0.29, 0.33))
            _cube(root, Vector3(0, 1.23, 0), Vector3(2.14, 0.13, 0.75), Color(0.43, 0.46, 0.49))
            fronts_cover.append({"node": root, "team": side, "position": center})
    _set_fronts_cover_visible(false)

func _set_fronts_cover_visible(value):
    for cover in fronts_cover:
        cover["node"].visible = value

func _nearest_cover(unit):
    var nearest = null
    var best = INF
    for cover in fronts_cover:
        if cover["team"] != unit["team"]:
            continue
        var distance = unit["node"].translation.distance_to(cover["position"])
        if distance < best:
            best = distance
            nearest = cover
    return nearest

func _unit_in_cover(unit):
    var cover = _nearest_cover(unit)
    if cover == null:
        return false
    return unit["node"].translation.distance_to(cover["position"]) <= 1.8

func _set_fronts_visible(value):
    for post in fronts_posts:
        post["node"].visible = value

func _reset_fronts():
    fronts_tickets = [FrontsRules.START_TICKETS, FrontsRules.START_TICKETS]
    fronts_clock = 0.0
    fronts_ai_goal = -1
    for post in fronts_posts:
        post["progress"] = 0.0
        post["flag"].material_override = _mat(Color(0.45, 0.48, 0.52))
    _set_fronts_visible(true)

func _fronts_capture_detail():
    var nearest = -1
    var nearest_distance = 3.0
    for i in range(fronts_posts.size()):
        var distance = player.translation.distance_to(fronts_posts[i]["node"].translation)
        if distance < nearest_distance:
            nearest = i
            nearest_distance = distance
    if nearest < 0:
        return "enter post zone"
    return "%d: %d%%" % [nearest + 1, int(abs(fronts_posts[nearest]["progress"]))]

func _fronts_enemy_objective():
    # Reacquire an uncaptured post when a goal changes ownership.
    # Closest-first selection prevents the AI endlessly pursuing the player
    # while ignoring the ticket objectives.
    if fronts_ai_goal >= 0 and fronts_ai_goal < fronts_posts.size():
        if FrontsRules.owner(fronts_posts[fronts_ai_goal]["progress"]) != 1:
            return fronts_posts[fronts_ai_goal]["node"].translation
    var best = -1
    var distance = INF
    for i in range(fronts_posts.size()):
        if FrontsRules.owner(fronts_posts[i]["progress"]) == 1:
            continue
        var candidate = enemy.translation.distance_to(fronts_posts[i]["node"].translation)
        if candidate < distance:
            best = i
            distance = candidate
    fronts_ai_goal = best
    return fronts_posts[best]["node"].translation if best >= 0 else player.translation

func _fronts_status():
    var parts = []
    for post in fronts_posts:
        var ownership = FrontsRules.owner(post["progress"])
        parts.append("A" if ownership == 0 else ("E" if ownership == 1 else "-"))
    return "/".join(parts)

func _fronts_respawn_point(team):
    # Prefer the safest owned command post; fall back to opposite base edges.
    var fallback = Vector3(0, 0, 9.0) if team == 0 else Vector3(0, 0, -9.0)
    var best = fallback
    var best_distance = -1.0
    var opponent = enemy.translation if team == 0 else player.translation
    for post in fronts_posts:
        if FrontsRules.owner(post["progress"]) != team:
            continue
        var loc = post["node"].translation
        var value = loc.distance_to(opponent)
        if value > best_distance:
            best_distance = value
            best = _clamp_arena(loc + Vector3(0, 0, 2.5 if team == 0 else -2.5))
    return best

func _spawn_fronts_combatants():
    # Respawn combatants without resetting flags or tickets.
    strikes = [_new_strike(), _new_strike()]
    hp = [100.0, 100.0]
    stamina = [100.0, 100.0]
    stagger = [0.0, 0.0]
    guard_break = [0.0, 0.0]
    invuln = [0.0, 0.0]
    player.translation = _fronts_respawn_point(0)
    enemy.translation = _fronts_respawn_point(1)
    fronts_ai_goal = -1
    ai_block = false
    block = false
    combat_log = "Respawn - capture command posts!"

func _fronts_resolve():
    var victory = FrontsRules.winner(fronts_tickets)
    if victory != -1:
        match_done = true
        if victory == 0:
            wins += 1
            _save_progress()
        combat_log = "FRONTS VICTORY! Press R to restart" if victory == 0 else ("FRONTS DEFEAT. Press R to retry" if victory == 1 else "DRAW. Press R to retry")

func _update_fronts(delta):
    var friendly = 0
    var hostile = 0
    for post in fronts_posts:
        var center = post["node"].translation
        var allies = 1 if player.translation.distance_to(center) <= 3.0 and hp[0] > 0 else 0
        var enemies = 1 if enemy.translation.distance_to(center) <= 3.0 and hp[1] > 0 else 0
        for unit in fronts_soldiers:
            if unit["hp"] > 0.0 and unit["node"].translation.distance_to(center) <= 3.0:
                if unit["team"] == 0:
                    allies += 1
                else:
                    enemies += 1
        post["progress"] = FrontsRules.capture(post["progress"], allies, enemies, delta)
        var ownership = FrontsRules.owner(post["progress"])
        friendly += 1 if ownership == 0 else 0
        hostile += 1 if ownership == 1 else 0
        var tint = Color(0.2, 0.65, 1.0) if ownership == 0 else (Color(1, 0.25, 0.2) if ownership == 1 else Color(0.6, 0.6, 0.62))
        post["flag"].material_override = _mat(tint)
    fronts_tickets = FrontsRules.drain(fronts_tickets, friendly, hostile, delta)
    _fronts_resolve()


# Go 8: lightweight AI infantry proxies. Their squad combat and tickets are
# independent of the two existing hero combatants and work on the same posts.
func _clear_fronts_soldiers():
    for soldier in fronts_soldiers:
        if is_instance_valid(soldier["node"]):
            soldier["node"].queue_free()
    fronts_soldiers.clear()

func _create_fronts_soldiers():
    for team in range(2):
        for slot in range(SOLDIERS_PER_TEAM):
            var root = Spatial.new()
            root.name = "Ally_%d" % slot if team == 0 else "EnemySoldier_%d" % slot
            add_child(root)
            var tint = Color(0.16, 0.50, 0.85) if team == 0 else Color(0.80, 0.24, 0.20)
            _cube(root, Vector3(0, 1.05, 0), Vector3(0.44, 0.95, 0.30), tint)
            _sphere(root, Vector3(0, 1.73, 0), 0.24, Color(0.72, 0.75, 0.78))
            _cube(root, Vector3(-0.13, 0.4, 0), Vector3(0.13, 0.75, 0.18), tint.darkened(0.15))
            _cube(root, Vector3(0.13, 0.4, 0), Vector3(0.13, 0.75, 0.18), tint.darkened(0.15))
            _cube(root, Vector3(0.34, 1.0, -0.35), Vector3(0.11, 0.11, 0.7), Color(0.16, 0.18, 0.22))
            # Layered uniform, helmet visor, torso plate, weapon and boots.
            _cube(root, Vector3(0, 1.14, -0.165), Vector3(0.49, 0.40, 0.07), tint.lightened(0.18))
            _cube(root, Vector3(0, 1.82, -0.20), Vector3(0.41, 0.13, 0.11), Color(0.05, 0.11, 0.16))
            _cube(root, Vector3(-0.30, 1.20, 0), Vector3(0.17, 0.52, 0.22), tint.darkened(0.22))
            _cube(root, Vector3(0.30, 1.20, 0), Vector3(0.17, 0.52, 0.22), tint.darkened(0.22))
            _cube(root, Vector3(-0.13, 0.10, -0.085), Vector3(0.24, 0.23, 0.38), Color(0.13, 0.15, 0.18))
            _cube(root, Vector3(0.13, 0.10, -0.085), Vector3(0.24, 0.23, 0.38), Color(0.13, 0.15, 0.18))
            root.translation = _soldier_spawn(team, slot)
            fronts_soldiers.append({"node":root, "team":team, "slot":slot,
                "hp":60.0, "cooldown":0.3 + randf(), "respawn":0.0,
                "goal":slot % fronts_posts.size(), "state":"advance", "flash":0.0})

# Reusable tracer meshes: no per-shot scene allocation during squad firefights.
func _create_tracer_pool():
    var material = SpatialMaterial.new()
    material.flags_unshaded = true
    material.albedo_color = Color(0.98, 0.74, 0.22)
    material.emission_enabled = true
    material.emission = Color(1.0, 0.36, 0.05)
    var mesh = CylinderMesh.new()
    mesh.top_radius = 0.025
    mesh.bottom_radius = 0.025
    mesh.height = 1.0
    for _i in range(16):
        var tracer = MeshInstance.new()
        tracer.mesh = mesh
        tracer.material_override = material
        tracer.visible = false
        add_child(tracer)
        shot_tracers.append({"node": tracer, "time": 0.0})

func _show_tracer(a, b):
    var travel = b - a
    if travel.length() < 0.01:
        return
    for effect in shot_tracers:
        if effect["time"] > 0.0:
            continue
        var tracer = effect["node"]
        tracer.translation = (a + b) * 0.5
        tracer.scale = Vector3(1, travel.length(), 1)
        # Orient the cylinder's local Y axis toward the target.
        tracer.transform.basis = Basis(Quat(Vector3.UP, travel.normalized())).scaled(Vector3(1, travel.length(), 1))
        tracer.visible = true
        effect["time"] = 0.16
        return

func _step_tracers(delta):
    for effect in shot_tracers:
        if effect["time"] > 0.0:
            effect["time"] -= delta
            if effect["time"] <= 0.0:
                effect["node"].visible = false

# Horizontal obstruction test against visible command-post barricades.
# Cover must be between shooter and target: nearby cover no longer grants
# unconditional damage reduction from bullets arriving behind it.
func _fire_line_clear(a, b):
    var line = Vector2(b.x - a.x, b.z - a.z)
    var denom = line.length_squared()
    if denom < 0.01:
        return true
    for barricade in fronts_cover:
        var center = barricade["position"]
        var v = Vector2(center.x - a.x, center.z - a.z)
        var t = clamp(v.dot(line) / denom, 0.0, 1.0)
        if t <= 0.08 or t >= 0.92:
            continue
        var closest = Vector2(a.x, a.z) + line * t
        if closest.distance_to(Vector2(center.x, center.z)) < 0.70:
            return false
    return true

# Centralized infantry damage prevents duplicate ticket loss on repeated hits.
func _hurt_soldier(unit, damage):
    if unit["hp"] <= 0.0 or match_done:
        return
    unit["hp"] = max(0.0, unit["hp"] - damage)
    unit["flash"] = 0.18
    if unit["hp"] <= 0.0:
        unit["node"].visible = false
        unit["respawn"] = SOLDIER_RESPAWN
        fronts_tickets[unit["team"]] = max(0.0, fronts_tickets[unit["team"]] - 1.0)

func _soldier_spawn(team, slot):
    var x = -4.0 + float(slot) * 4.0
    return Vector3(x, 0, 10.0 if team == 0 else -10.0)

func _living_soldiers(team):
    var count = 0
    for soldier in fronts_soldiers:
        if soldier["team"] == team and soldier["hp"] > 0.0:
            count += 1
    return count

func _soldier_target(soldier):
    var origin = soldier["node"].translation
    var best = null
    var best_distance = 5.0
    for other in fronts_soldiers:
        if other["team"] == soldier["team"] or other["hp"] <= 0.0:
            continue
        var distance = origin.distance_to(other["node"].translation)
        if distance < best_distance:
            best_distance = distance
            best = other
    return best

func _step_fronts_soldiers(delta):
    for unit in fronts_soldiers:
        if unit["hp"] <= 0.0:
            unit["respawn"] -= delta
            if unit["respawn"] <= 0.0:
                unit["hp"] = 60.0
                unit["node"].translation = _soldier_spawn(unit["team"], unit["slot"])
                unit["node"].visible = true
                unit["cooldown"] = 0.8
                unit["state"] = "advance"
            continue
        unit["cooldown"] = max(0.0, unit["cooldown"] - delta)
        unit["flash"] = max(0.0, unit["flash"] - delta)
        var foe = _soldier_target(unit)
        var destination = Vector3.ZERO
        # Injured soldiers fall back behind friendly barricades. Healthy units
        # advance to posts unless an opponent is already nearby.
        var cover = _nearest_cover(unit)
        if unit["hp"] < 30.0 and cover != null:
            unit["state"] = "cover"
            destination = cover["position"]
        elif foe != null:
            unit["state"] = "engage"
            destination = foe["node"].translation
        else:
            unit["state"] = "advance"
            var goal = SquadRules.choose_post(fronts_posts, unit["team"], unit["node"].translation)
            if goal >= 0:
                unit["goal"] = goal
            destination = fronts_posts[unit["goal"]]["node"].translation
        var gap = unit["node"].translation.distance_to(destination)
        if gap > (2.0 if unit["state"] == "engage" else 1.35):
            var direction = destination - unit["node"].translation
            direction.y = 0.0
            if direction.length() > 0.01:
                unit["node"].translation = _clamp_arena(unit["node"].translation + direction.normalized() * min(gap, 2.35 * delta))
        if gap > 0.05:
            unit["node"].look_at(Vector3(destination.x, unit["node"].translation.y, destination.z), Vector3.UP)
        # The firing target is independent of the movement destination: a
        # soldier behind cover can defend without running into the opponent.
        var shot_distance = unit["node"].translation.distance_to(foe["node"].translation) if foe != null else INF
        var hero_index = 1 - unit["team"]
        var opposing_hero = player if hero_index == 0 else enemy
        var hero_distance = unit["node"].translation.distance_to(opposing_hero.translation) if hp[hero_index] > 0.0 else INF
        if unit["cooldown"] <= 0.0 and min(hero_distance, shot_distance) <= 4.2:
            var origin = unit["node"].translation + Vector3(0, 1.2, 0)
            var aim = opposing_hero.translation if hero_distance < shot_distance else foe["node"].translation
            if not _fire_line_clear(origin, aim + Vector3(0, 1.0, 0)):
                unit["cooldown"] = 0.28
                continue
            _show_tracer(origin, aim + Vector3(0, 1.0, 0))
            if hero_distance < shot_distance:
                # Infantry fire uses a lighter hit than a hero's sword and
                # respects dodges, guard and the existing match death logic.
                _damage(hero_index, 5.0, -1, 4.0)
                combat_log = "Infantry under fire!" if hero_index == 0 else "Enemy hero under fire"
            elif foe != null:
                var damage = 6.0 if _unit_in_cover(foe) else 12.0
                _hurt_soldier(foe, damage)
            unit["cooldown"] = 1.2 + randf() * 0.4
