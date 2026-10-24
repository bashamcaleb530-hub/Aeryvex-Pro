from pathlib import Path
p=Path(__file__).resolve().parents[1]/'scripts'/'FighterVisual.gd'
s=p.read_text()
checks={
    'new facial proportions function': 'func _face_shape(' in s,
    'nose bridge': '"NasalBridge"' in s,
    'chin shaping': '"Chin"' in s,
    'brow ridge': '"BrowRidge"' in s,
    'temple shapes': '"Temple"' in s,
    'layered hair function': 'func _hair_layers(' in s,
    'tapered hair locks': '"HairLock"' in s,
    'hair fringe': '"HairFringe"' in s,
    'face connected to character build': '_face_shape(head, skin, fighter_index)' in s,
    'hair connected to character build': '_hair_layers(head, fighter_index)' in s,
}
for label,ok in checks.items(): print(('PASS' if ok else 'FAIL'),label)
if not all(checks.values()): raise SystemExit(1)
