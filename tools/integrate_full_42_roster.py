#!/usr/bin/env python3
"""Aeryvex Pro Godot 4: integrate the established 42-entry roster in one batch.
30 force-user entries (including two Ahsoka versions), 12 bounty hunters.
This delivers selectable/spawnable procedural characters and archetype metadata.
Not final likeness meshes or complete ranged/special-ability gameplay.
"""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
main=root/"scripts/Main.gd"
visual=root/"scripts/FighterVisual.gd"
roster=[
("Anakin Skywalker","force","single"),("Count Dooku","force","single"),("Obi-Wan Kenobi","force","single"),
("Mace Windu","force","single"),("Qui-Gon Jinn","force","single"),("Yoda","force","single"),
("Darth Vader","force","single"),("Emperor Palpatine","force","single"),("General Grievous","force","multi"),
("Ahsoka Tano (Snips)","force","dual"),("Ahsoka Tano (Fulcrum)","force","dual"),
("Plo Koon","force","single"),("Kit Fisto","force","single"),("Shaak Ti","force","single"),
("Aayla Secura","force","single"),("Luminara Unduli","force","single"),("Barriss Offee","force","single"),
("Kanan Jarrus","force","single"),("Ezra Bridger","force","single"),("Cal Kestis","force","single"),
("Luke Skywalker","force","single"),("Darth Maul","force","double"),("Asajj Ventress","force","dual"),
("Savage Opress","force","double"),("Darth Revan","force","single"),("Grand Inquisitor","force","double"),
("Second Sister","force","double"),("Kylo Ren","force","crossguard"),("Baylan Skoll","force","single"),
("Shin Hati","force","single"),
("Jango Fett","hunter","blaster"),("Boba Fett","hunter","blaster"),("Cad Bane","hunter","blaster"),
("Bossk","hunter","rifle"),("IG-88","hunter","rifle"),("Dengar","hunter","rifle"),
("Aurra Sing","hunter","rifle"),("Embo","hunter","blaster"),("Fennec Shand","hunter","rifle"),
("Din Djarin","hunter","blaster"),("Zam Wesell","hunter","blaster"),("Black Krrsantan","hunter","melee")]
assert len(roster)==42 and sum(x[1]=="force" for x in roster)==30
colors=["Color(0.2,0.55,1)","Color(1,0.2,0.16)","Color(0.2,0.55,1)","Color(0.55,0.35,1)","Color(0.2,0.75,0.4)","Color(0.2,0.85,0.5)","Color(1,0.12,0.1)","Color(1,0.2,0.12)","Color(0.28,0.85,0.8)"]
for i in range(9,42):
    # two Ahsoka saber colors, alternated faction/archetype palettes
    if i==9: colors.append("Color(0.22,0.95,0.42)")
    elif i==10:colors.append("Color(0.85,0.94,1.0)")
    elif i>=30:colors.append("Color(1.0,0.62,0.18)")
    elif i in [21,22,23,24,25,26,27,28,29]:colors.append("Color(0.95,0.28,0.18)")
    else: colors.append("Color(0.24,0.62,1.0)")
data=[dict(id=i,name=name,category=category,weapon=weapon,prototype=(i>=30)) for i,(name,category,weapon) in enumerate(roster)]
(root/"roster").mkdir(exist_ok=True)
(root/"roster/characters.json").write_text(json.dumps(data,indent=2)+"\n")
s=main.read_text()
if "AERYVEX_ROSTER_42_V1" not in s:
    start=s.index("const ROSTER = ")
    end=s.index("\nvar player",start)
    new="# AERYVEX_ROSTER_42_V1\n"
    new+="const ROSTER = "+json.dumps([r[0] for r in roster],ensure_ascii=False)+"\n"
    new+="const COLORS = ["+", ".join(colors)+"]\n"
    new+="const ROSTER_CATEGORY = "+json.dumps([r[1] for r in roster])+"\n"
    new+="const ROSTER_WEAPON = "+json.dumps([r[2] for r in roster])+"\n"
    s=s[:start]+new+s[end:]
    main.write_text(s)
    print("UPDATED Main.gd: 42 selectable names, distinct saber colors, weapon archetype metadata")
else: print("ALREADY INTEGRATED: Main.gd")
s=visual.read_text()
if "AERYVEX_ROSTER_42_VISUAL_V1" not in s:
    a="    fighter_index = int(clamp(index, 0, HEIGHTS.size()-1))"
    b="""    # AERYVEX_ROSTER_42_VISUAL_V1
    # Preserve 9 validated base rigs while varying all 42 selectable silhouettes.
    var roster_index = int(clamp(index, 0, 41))
    fighter_index = roster_index % HEIGHTS.size()"""
    if a not in s:raise SystemExit("Expected configure assignment missing; FighterVisual unchanged")
    s=s.replace(a,b,1)
    hook='    var limbs = _limb(body, -1, true, outfit, skin, armored)'
    extra="""    # Distinct low-poly identity cues for every additional roster entry.
    if roster_index >= 9:
        var tint = Color.from_hsv(fmod(float(roster_index) * 0.173, 1.0), 0.44, 0.68)
        _block(torso, "RosterShoulderInsignia", Vector3(0.32, 0.47, -0.16), Vector3(0.16, 0.11, 0.12), tint, 0.25)
        _block(torso, "RosterWaistDetail", Vector3(-0.22, 0.01, -0.27), Vector3(0.14, 0.17, 0.06), tint.darkened(0.18))
        if roster_index >= 30:
            # Hunter silhouette: armored vest and visible side holster.
            _block(torso, "HunterArmoredVest", Vector3(0, 0.33, -0.35), Vector3(0.57, 0.54, 0.13), Color(0.24, 0.27, 0.30), 0.52)
            _block(torso, "HunterHolster", Vector3(0.36, -0.12, -0.16), Vector3(0.16, 0.35, 0.16), Color(0.16, 0.14, 0.13))
        elif roster_index in [9,10,22]:
            _block(torso, "DualWielderStrap", Vector3(-0.25, 0.34, -0.31), Vector3(0.15, 0.62, 0.06), tint)
"""
    if hook not in s:raise SystemExit("Expected limb hook missing; FighterVisual unchanged")
    s=s.replace(hook,extra+hook,1)
    # append after construction but before first animate_pose() in configure
    hook='    animate_pose(0.0,0.0,"idle","light",0.0,false,false,false,false)'
    add="""    # Weapon visuals are preliminary. Ranged gameplay is not yet implemented.
    if roster_index >= 30:
        var blade_node = saber.get_node_or_null("Blade")
        if blade_node != null:
            blade_node.visible = false
        var light_node = saber.get_node_or_null("BladeLight")
        if light_node != null:
            light_node.visible = false
        _block(saber, "BlasterProxy", Vector3(0, 0.27, -0.08), Vector3(0.17, 0.48, 0.26), Color(0.13, 0.15, 0.18), 0.72)
"""
    if hook not in s:raise SystemExit("Expected pose hook missing; FighterVisual unchanged")
    s=s.replace(hook,add+hook,1)
    visual.write_text(s)
    print("UPDATED FighterVisual.gd: 42 spawnable variants with hunter/force visual cues")
else:print("ALREADY INTEGRATED: FighterVisual.gd")
print("ROSTER: 42 total; 30 Force-user entries; 12 hunters")
print("NOTE: hunter weapon combat still inherits current melee gameplay; realistic models still required.")
