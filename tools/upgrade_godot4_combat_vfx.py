#!/usr/bin/env python3
"""Upgrade Godot 4 impact VFX with spark streaks and differentiated parry bursts."""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"scripts"/"CombatVFX.gd"
source='''extends Node3D
# Aeryvex original procedural combat VFX. Presentation-only.
const LIFETIME := 0.23

func _spark(origin: Vector3, direction: Vector3, blocked: bool, index: int) -> void:
    var streak := MeshInstance3D.new()
    var cylinder := CylinderMesh.new()
    cylinder.top_radius = 0.013
    cylinder.bottom_radius = 0.026
    cylinder.height = 0.24 + 0.045 * float(index % 4)
    streak.mesh = cylinder

    var material := StandardMaterial3D.new()
    material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    material.albedo_color = Color(0.20, 0.75, 1.0, 0.96) if blocked else Color(1.0, 0.65, 0.18, 0.96)
    material.emission_enabled = true
    material.emission = material.albedo_color
    material.emission_energy_multiplier = 4.0
    streak.material_override = material

    add_child(streak)
    streak.global_position = origin
    streak.look_at(origin + direction, Vector3.UP)
    streak.rotate_object_local(Vector3.RIGHT, PI / 2.0)

    var tween := create_tween()
    tween.set_parallel(true)
    tween.tween_property(streak, "global_position", origin + direction * 0.68, LIFETIME)
    tween.tween_property(material, "albedo_color:a", 0.0, LIFETIME)
    tween.chain().tween_callback(streak.queue_free)

func impact(world_position: Vector3, blocked: bool = false) -> void:
    var origin := world_position + Vector3.UP * 1.0
    var flash := MeshInstance3D.new()
    var sphere := SphereMesh.new()
    sphere.radius = 0.13 if blocked else 0.20
    sphere.height = sphere.radius * 2.0
    flash.mesh = sphere

    var material := StandardMaterial3D.new()
    material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    material.albedo_color = Color(0.16, 0.67, 1.0, 0.92) if blocked else Color(1.0, 0.78, 0.32, 0.95)
    material.emission_enabled = true
    material.emission = material.albedo_color
    material.emission_energy_multiplier = 3.5
    flash.material_override = material
    add_child(flash)
    flash.global_position = origin

    var tween := create_tween()
    tween.set_parallel(true)
    tween.tween_property(flash, "scale", Vector3.ONE * (2.0 if blocked else 2.8), LIFETIME)
    tween.tween_property(material, "albedo_color:a", 0.0, LIFETIME)
    tween.chain().tween_callback(flash.queue_free)

    var count := 14 if blocked else 9
    for i in range(count):
        var angle := TAU * float(i) / float(count)
        var direction := Vector3(cos(angle), 0.3 + 0.08 * float(i % 3), sin(angle)).normalized()
        _spark(origin, direction, blocked, i)
'''
if p.exists() and "func impact(" in p.read_text():
    p.write_text(source)
    print("UPGRADED: Godot 4 procedural hit and parry spark effects")
else:
    raise SystemExit("Existing CombatVFX.gd not found; run previous VFX integration first")
