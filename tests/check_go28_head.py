from pathlib import Path
s=(Path(__file__).resolve().parents[1]/'scripts/FighterVisual.gd').read_text()
checks={
 'sculpted mesh function': 'func _sculpted_head(parent, skin, index):',
 'real triangle mesh': 'mesh_tool.begin(Mesh.PRIMITIVE_TRIANGLES)',
 'per-vertex normals': 'mesh_tool.generate_normals()',
 'jaw shape variation': 'jaw_scale =',
 'cheek shape variation': 'cheek_scale =',
 'visible head uses mesh': '_sculpted_head(head, skin, fighter_index)',
 'helmet fallback': 'if fighter_index == 6 or fighter_index == 8:',
 'normal material': 'mesh_instance.material_override = _material(skin, 0.0, false, "Face")',
}
for name,text in checks.items():
 assert text in s,name
print(f'{len(checks)} / {len(checks)} Go 28 head checks passed')
