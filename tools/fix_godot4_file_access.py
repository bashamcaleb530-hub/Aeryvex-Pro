#!/usr/bin/env python3
"""Post-conversion Godot 4 repairs for Aeryvex Pro. Run inside converted worktree."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
path = root / "scripts/Main.gd"
s = path.read_text()
start = s.index("func _load_progress():")
end = s.index("func _bind_key(", start)
new = '''func _load_progress():
    if not FileAccess.file_exists(SAVE_PATH):
        return
    var file = FileAccess.open(SAVE_PATH, FileAccess.READ)
    if file == null:
        return
    var data = JSON.parse_string(file.get_as_text())
    if typeof(data) != TYPE_DICTIONARY:
        return
    wins = max(0, int(data.get("wins", 0)))
    selected = int(clamp(int(data.get("hero", 0)), 0, ROSTER.size() - 1))
    ai_difficulty = EnemyBrain.skill(int(data.get("ai_level", 1)))
    enemy_index = (selected + 1) % ROSTER.size()

func _save_progress():
    var file = FileAccess.open(SAVE_PATH, FileAccess.WRITE)
    if file != null:
        file.store_string(JSON.stringify({"version": 2, "wins": wins, "hero": selected, "ai_level": ai_difficulty}))

'''
if "var file = File.new()" in s[start:end]:
    path.write_text(s[:start]+new+s[end:])
    print("PATCHED: Godot 4 FileAccess and JSON APIs")
elif "FileAccess.file_exists(SAVE_PATH)" in s[start:end]:
    print("ALREADY PATCHED: Godot 4 save/load")
else:
    raise SystemExit("Unexpected save/load source — not modified")
