#!/usr/bin/env python3
"""Add a small Godot 4 combat contact-effects system to the converted Kaggle worktree."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
main=root/"scripts"/"Main.gd"
fx=root/"scripts"/"CombatVFX.gd"
code='''extends Node3D
# Godot 4 presentation-only melee sparks. Safe in headless runtime tests.
# A short-lived procedural impact flash is positioned at the strike contact.
const LIFETIME := 0.20

func impact(world_position: Vector3, blocked: bool = false) -> void:
    var node := MeshInstance3D.new()
    var sphere := SphereMesh.new()
    sphere.radius = 0.12 if blocked else 0.19
    sphere.height = sphere.radius * 2.0
    node.mesh = sphere
    var mat := StandardMaterial3D.new()
    mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    mat.albedo_color = Color(0.2, 0.7, 1.0, 0.9) if blocked else Color(1.0, 0.73, 0.27, 0.95)
    mat.emission_enabled = true
    mat.emission = mat.albedo_color
    mat.emission_energy_multiplier = 3.0
    node.material_override = mat
    add_child(node)
    node.global_position = world_position + Vector3.UP * 1.0
    var tween := create_tween()
    tween.set_parallel(true)
    tween.tween_property(node, "scale", Vector3.ONE * 3.0, LIFETIME)
    tween.tween_property(mat, "albedo_color:a", 0.0, LIFETIME)
    tween.chain().tween_callback(node.queue_free)
'''
if fx.exists() and fx.read_text()!=code:
    raise SystemExit("Existing CombatVFX.gd differs; not overwriting.")
fx.write_text(code)
s=main.read_text()
if "AERYVEX_G4_COMBAT_VFX" in s:
    print("ALREADY INTEGRATED")
else:
    hook="func _damage(target, amount, attacker = -1, guard_damage_amount = -1.0):"
    if hook not in s: raise SystemExit("Could not locate _damage hook")
    s=s.replace(hook,'''# AERYVEX_G4_COMBAT_VFX
var combat_vfx = null

func _ensure_combat_vfx():
    if combat_vfx == null:
        combat_vfx = load("res://scripts/CombatVFX.gd").new()
        combat_vfx.name = "CombatVFX"
        add_child(combat_vfx)

'''+hook,1)
    needle='    if hp[target] <= 0.0:'
    if needle not in s: raise SystemExit("Missing health check insertion point")
    # Avoid calling resource rendering APIs during automated headless tests.
    addition='''    # Visual contact feedback only; damage remains controlled by CombatRules.
    if not DisplayServer.get_name() == "headless" and attacker >= 0 and result["outcome"] != "dodge":
        _ensure_combat_vfx()
        var victim = player if target == 0 else enemy
        if is_instance_valid(victim):
            combat_vfx.impact(victim.global_position, result["outcome"] != "hit")
'''
    s=s.replace(needle,addition+needle,1)
    main.write_text(s)
    print("INTEGRATED Godot 4 strike/parry visual feedback")
print("VFX script:",fx)
