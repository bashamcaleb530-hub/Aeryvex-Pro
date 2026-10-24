#!/usr/bin/env python3
"""Aeryvex 42 roster combat pass (converted Godot 4 project).
Requires tools/integrate_full_42_roster.py already applied.
Introduces distance-limited ranged attacks for hunter entries, AI range and
makes hunter weapon proxy distinct. Existing force-character melee is unchanged.
"""
from pathlib import Path
p=Path(__file__).resolve().parents[1]/"scripts"/"Main.gd"
s=p.read_text()
if "AERYVEX_42_COMBAT_V1" in s:
 print("ALREADY APPLIED");raise SystemExit(0)
if "const ROSTER_CATEGORY" not in s:
 raise SystemExit("42-character roster not found; run roster integration first")
at="func _resolve_swing(who, data):"
if at not in s: raise SystemExit("Missing combat entry point")
logic='''# AERYVEX_42_COMBAT_V1
func _is_hunter(who):
    var index = selected if who == 0 else enemy_index
    return ROSTER_CATEGORY[index] == "hunter"

func _hunter_attack(who, data):
    var src = player if who == 0 else enemy
    var dst = enemy if who == 0 else player
    if not is_instance_valid(src) or not is_instance_valid(dst):
        return
    var fighter_id = selected if who == 0 else enemy_index
    var rifle = ROSTER_WEAPON[fighter_id] == "rifle"
    var max_range = 15.0 if rifle else 12.0
    var dist = src.global_position.distance_to(dst.global_position)
    var hit = dist <= max_range and CombatRules.in_arc(src.global_transform, dst.global_position, max_range, -0.25)
    if hit:
        _damage(1 - who, 12.0 if rifle else 9.0, who, -1.0)
        combat_log = "Rifle hit" if rifle else "Blaster hit"
    else:
        combat_log = "Ranged shot missed"
    # Simple ranged infantry targeting in Galactic Fronts.
    if mode == "Fronts":
        for unit in fronts_soldiers:
            if unit["team"] == who or unit["hp"] <= 0.0:
                continue
            if CombatRules.in_arc(src.global_transform, unit["node"].global_position, max_range, -0.25):
                _hurt_soldier(unit, 12.0 if rifle else 9.0)
                break

'''
s=s.replace(at,logic+at,1)
at='''    var src = player if who == 0 else enemy
    var dst = enemy if who == 0 else player
    if not is_instance_valid(src) or not is_instance_valid(dst):
        return
    var hero_hit ='''
replace='''    if _is_hunter(who):
        _hunter_attack(who, data)
        return
    var src = player if who == 0 else enemy
    var dst = enemy if who == 0 else player
    if not is_instance_valid(src) or not is_instance_valid(dst):
        return
    var hero_hit ='''
if at not in s:raise SystemExit("Combat target not found")
s=s.replace(at,replace,1)
old='''    var desired = EnemyBrain.desired_distance(stamina[1], winding)'''
new='''    var desired = (8.0 if ROSTER_WEAPON[enemy_index] == "rifle" else 6.0) if _is_hunter(1) else EnemyBrain.desired_distance(stamina[1], winding)'''
if old not in s:raise SystemExit("AI distance hook not found")
s=s.replace(old,new,1)
old='''        if choice_attack != "":
            _attack(1, choice_attack)'''
new='''        if _is_hunter(1) and enemy.translation.distance_to(player.translation) <= 14.5 and not ai_block:
            _attack(1, "light")
        elif choice_attack != "":
            _attack(1, choice_attack)'''
if old not in s:raise SystemExit("AI attack hook not found")
s=s.replace(old,new,1)
p.write_text(s)
print("INTEGRATED: 12 hunter entries use ranged damage and AI spacing; force users retain melee")
print("NOTICE: this is first-pass hitscan combat, not complete hunter gadgets/animations.")
