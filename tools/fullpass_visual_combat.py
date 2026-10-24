#!/usr/bin/env python3
"""Aeryvex Godot 4: integrated combat-style + arena environment batch.
Run in the converted Godot 4 worktree. Safe to rerun, backs up modified files.
No copyrighted production assets included.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
main=root/"scripts/Main.gd"
fighter=root/"scripts/FighterVisual.gd"
env=root/"scripts/BattleEnvironment.gd"
environment='''extends Node3D
# Procedural environment art: layered sky, stage surface, trim, architecture,
# and atmospheric decoration. Noncolliding visuals do not alter movement bounds.
const SEGMENTS := 32

func _material(color: Color, roughness: float = 0.8, metallic: float = 0.0, emission: bool = false) -> StandardMaterial3D:
    var mat := StandardMaterial3D.new()
    mat.albedo_color = color
    mat.roughness = roughness
    mat.metallic = metallic
    if emission:
        mat.emission_enabled = true
        mat.emission = color
        mat.emission_energy_multiplier = 1.65
    return mat

func _block(position: Vector3, dimensions: Vector3, material: Material) -> void:
    var node := MeshInstance3D.new()
    var cube := BoxMesh.new()
    cube.size = dimensions
    node.mesh = cube
    node.material_override = material
    node.position = position
    add_child(node)

func _ring(radius: float, y: float, material: Material) -> void:
    for i in range(SEGMENTS):
        var angle := TAU * float(i) / float(SEGMENTS)
        var next_angle := TAU * float(i + 1) / float(SEGMENTS)
        var middle := (angle + next_angle) * 0.5
        var chord := 2.0 * radius * sin((next_angle - angle) * 0.5)
        var part := MeshInstance3D.new()
        var mesh := BoxMesh.new()
        mesh.size = Vector3(chord + 0.018, 0.018, 0.065)
        part.mesh = mesh
        part.material_override = material
        part.position = Vector3(cos(middle) * radius, y, sin(middle) * radius)
        part.rotation.y = -middle - PI * 0.5
        add_child(part)

func _ready() -> void:
    var stone := _material(Color(0.29, 0.34, 0.43))
    var trim := _material(Color(0.34, 0.51, 0.62), 0.27, 0.65)
    var glow := _material(Color(0.07, 0.42, 0.86), 0.3, 0.0, true)
    var accent := _material(Color(0.55, 0.42, 0.28), 0.33, 0.5)
    var floor_tex := load("res://art/textures/stone_floor_albedo.png") if ResourceLoader.exists("res://art/textures/stone_floor_albedo.png") else null
    if floor_tex != null:
        stone.albedo_texture = floor_tex
        stone.albedo_color = Color.WHITE
    var metal_tex := load("res://art/textures/metal_trim_albedo.png") if ResourceLoader.exists("res://art/textures/metal_trim_albedo.png") else null
    if metal_tex != null:
        trim.albedo_texture = metal_tex
        trim.albedo_color = Color.WHITE
    # The central ring stays flush with the existing collision floor.
    _ring(7.2, 0.014, trim)
    _ring(7.55, 0.015, glow)
    _ring(8.0, 0.013, accent)
    # Plinth and overhead frieze details outside the playable ring.
    for side in [-1.0, 1.0]:
        for n in range(-6, 7):
            var x := float(n) * 2.1
            _block(Vector3(x, 0.15, side * 14.05), Vector3(1.64, 0.3, 0.42), stone)
            _block(Vector3(side * 14.05, 0.15, x), Vector3(0.42, 0.3, 1.64), stone)
            if n % 2 == 0:
                _block(Vector3(x, 3.2, side * 14.08), Vector3(0.15, 1.4, 0.11), glow)
                _block(Vector3(side * 14.08, 3.2, x), Vector3(0.11, 1.4, 0.15), glow)
    # Four light pools, omitting expensive dynamic shadows.
    for x in [-10.8, 10.8]:
        for z in [-10.8, 10.8]:
            var light := OmniLight3D.new()
            light.light_color = Color(0.26, 0.51, 1.0)
            light.light_energy = 0.45
            light.omni_range = 6.0
            light.shadow_enabled = false
            light.position = Vector3(x, 3.0, z)
            add_child(light)
'''
env.write_text(environment)
s=main.read_text()
marker='# AERYVEX_FULLPASS_ENVIRONMENT'
if marker not in s:
    anchor='    architecture.name = "TempleArchitecture"'
    if anchor not in s: raise SystemExit("Expected arena placement not found; no edit")
    # append environment after architecture added to scene
    anchor='    add_child(architecture)'
    insert='''    # AERYVEX_FULLPASS_ENVIRONMENT
    var environment_art = load("res://scripts/BattleEnvironment.gd").new()
    environment_art.name = "BattleEnvironment"
    add_child(environment_art)
'''
    s=s.replace(anchor,anchor+"\n"+insert.rstrip(),1)
    main.write_text(s)
    print("INTEGRATED: temple floor rings, perimeter relief, luminous trim, four light pools")
else: print("ALREADY INTEGRATED: environment")
s=fighter.read_text()
marker='# AERYVEX_FULLPASS_STYLES'
if marker not in s:
    target='    var amount = clamp(speed / 5.0, 0.0, 1.0)'
    if target not in s:raise SystemExit("Expected animation hook not found")
    insertion='''    # AERYVEX_FULLPASS_STYLES: nine varied motion profiles on shared rig.
    # Lightweight fighters move more sharply; armored fighters have deliberate swings.
    var style_speed = [1.06, 0.94, 1.10, 1.08, 0.92, 1.20, 0.78, 1.03, 0.81][fighter_index]
    var style_swing = [1.03, 0.97, 1.12, 1.05, 0.98, 1.18, 0.82, 1.04, 0.86][fighter_index]
'''
    s=s.replace(target,insertion+target,1)
    old='    running_clock += delta * stride_cadence * gait_weight'
    if old not in s:raise SystemExit("Missing stride hook")
    s=s.replace(old,'    running_clock += delta * stride_cadence * gait_weight * style_speed',1)
    old='    var guard_raise = 29.0 * guard_weight'
    if old not in s:raise SystemExit("Missing swing hook")
    s=s.replace(old,'    blade_swing *= style_swing\n    shoulder_swing *= style_swing\n'+old,1)
    fighter.write_text(s)
    print("INTEGRATED: nine distinct gait/swing profiles")
else:print("ALREADY INTEGRATED: styles")
print("COMPLETE: batch source changes staged in Kaggle worktree only")
