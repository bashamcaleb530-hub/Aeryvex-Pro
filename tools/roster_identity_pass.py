#!/usr/bin/env python3
"""Nine-roster character identity art pass for converted Godot 4 project.
Additional costume geometry, silhouettes, helmets and accessories; not photoreal assets.
Idempotent. Requires the existing procedural FighterVisual.gd.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
path=root/"scripts/FighterVisual.gd"
s=path.read_text()
marker="# AERYVEX_ROSTER_IDENTITY_PASS_V1"
if marker in s:
 print("ALREADY INSTALLED: nine-character art pass")
 raise SystemExit(0)
needle="    var limbs = _limb(body, -1, true, outfit, skin, armored)"
if needle not in s:
 raise SystemExit("Expected character build hook missing. No changes made.")
s=s.replace(needle,"    _roster_identity_details(outfit, skin)\n"+needle,1)
extra='''

# AERYVEX_ROSTER_IDENTITY_PASS_V1
# Nine distinct stylized character silhouettes. Geometry remains procedural,
# not a film-accurate scan or a licensed production character model.
func _roster_identity_details(outfit, skin):
    var leather = Color(0.24, 0.15, 0.10)
    var silver = Color(0.58, 0.62, 0.70)
    var gold = Color(0.72, 0.55, 0.25)
    var near_black = Color(0.055, 0.063, 0.075)
    if fighter_index == 0:
        # Young blue-blade warrior: asymmetric shoulder layer, belt gear.
        _block(torso, "LayeredRightShoulder", Vector3(0.39, 0.46, -0.03), Vector3(0.32, 0.12, 0.40), leather)
        _block(torso, "CrossBodySash", Vector3(0.05, 0.30, -0.255), Vector3(0.17, 0.62, 0.035), outfit.lightened(0.22))
        _block(torso, "UtilityPouch", Vector3(-0.28, 0.02, -0.22), Vector3(0.16, 0.18, 0.12), leather)
    elif fighter_index == 1:
        # Tall aristocratic duelist: high collar, shoulder cape, bright fastener.
        _block(torso, "TallNeckCollar", Vector3(0, 0.70, 0), Vector3(0.56, 0.25, 0.40), Color(0.21, 0.15, 0.15))
        _block(torso, "FormalCapeUpper", Vector3(0, 0.51, 0.25), Vector3(0.88, 0.24, 0.17), Color(0.32, 0.16, 0.15))
        _ball(torso, "CapeClasp", Vector3(0, 0.53, -0.26), 0.065, gold, 0.65)
    elif fighter_index == 2:
        # Veteran robe-wearing knight: layered tabard and utility strap.
        _block(torso, "CreamTabard", Vector3(0, 0.24, -0.27), Vector3(0.36, 0.92, 0.055), Color(0.72, 0.63, 0.48))
        _block(torso, "LeatherStrap", Vector3(0.19, 0.35, -0.295), Vector3(0.10, 0.72, 0.035), leather)
        _block(torso, "ShoulderSeam", Vector3(-0.38, 0.55, 0), Vector3(0.22, 0.09, 0.42), outfit.darkened(0.24))
    elif fighter_index == 3:
        # Violet-blade master: darker shoulder panels and metallic belt accent.
        for side in [-1.0, 1.0]:
            _block(torso, "MasterShoulderPanel", Vector3(side * 0.40, 0.50, 0), Vector3(0.28, 0.11, 0.40), Color(0.17, 0.14, 0.22))
        _block(torso, "MasterBeltPlate", Vector3(0, 0.02, -0.29), Vector3(0.23, 0.13, 0.06), silver, 0.55)
    elif fighter_index == 4:
        # Traveling guardian: poncho-style chest layer and longer sash.
        _block(torso, "TravelMantle", Vector3(0, 0.49, 0), Vector3(0.88, 0.13, 0.50), Color(0.37, 0.24, 0.14))
        _block(torso, "LongCentralTabard", Vector3(0, -0.22, -0.26), Vector3(0.35, 0.84, 0.08), outfit.lightened(0.28))
    elif fighter_index == 5:
        # Very short green warrior: broad ears and warm robe/hood back silhouette.
        for side in [-1.0, 1.0]:
            _block(head, "EarTip", Vector3(side * 0.47, 0.025, 0), Vector3(0.27, 0.08, 0.11), skin)
        _block(torso, "BroadRobeShoulders", Vector3(0, 0.45, 0), Vector3(0.85, 0.18, 0.55), Color(0.71, 0.67, 0.48))
    elif fighter_index == 6:
        # Dark armored warrior: brow crest and chest control unit.
        _block(head, "HelmetCrown", Vector3(0, 0.35, 0.08), Vector3(0.59, 0.21, 0.59), near_black, 0.70)
        _block(head, "Breather", Vector3(0, -0.14, -0.34), Vector3(0.26, 0.19, 0.12), silver, 0.63)
        _block(torso, "ChestControlPanel", Vector3(0, 0.30, -0.35), Vector3(0.35, 0.27, 0.09), near_black, 0.45)
        for side in [-1.0, 1.0]:
            _block(torso, "ChestIndicator", Vector3(side * 0.09, 0.33, -0.42), Vector3(0.045, 0.055, 0.014), Color(0.14, 0.67, 0.85) if side < 0 else Color(0.91, 0.18, 0.15))
    elif fighter_index == 7:
        # Hooded dark sorcerer: hood rim, inner cowl, layered sleeves.
        _block(head, "InnerHoodShadow", Vector3(0, 0.015, -0.20), Vector3(0.49, 0.33, 0.09), near_black)
        _block(head, "HoodBrow", Vector3(0, 0.20, -0.24), Vector3(0.61, 0.13, 0.18), outfit.darkened(0.16))
        _block(torso, "DarkCowl", Vector3(0, 0.56, 0.04), Vector3(0.88, 0.18, 0.52), near_black)
    elif fighter_index == 8:
        # Tall plated cyborg: rear backplate, visor ridge, armored throat.
        _block(head, "FacePlate", Vector3(0, -0.09, -0.29), Vector3(0.41, 0.25, 0.10), silver, 0.80)
        _block(head, "VisorRidge", Vector3(0, 0.14, -0.31), Vector3(0.48, 0.10, 0.14), near_black, 0.65)
        _block(torso, "CyborgBackplate", Vector3(0, 0.38, 0.29), Vector3(0.65, 0.73, 0.14), silver, 0.85)
        _block(torso, "ArmoredGorget", Vector3(0, 0.66, 0.0), Vector3(0.58, 0.17, 0.43), silver, 0.75)
'''
path.write_text(s+extra)
print("UPDATED all nine fighter variants with unique costume and silhouette details")
print("Characters remain procedural placeholders; detailed production 3D models still required")
