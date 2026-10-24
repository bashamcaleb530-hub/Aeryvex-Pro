from pathlib import Path
s=(Path(__file__).resolve().parents[1]/"scripts/Main.gd").read_text()
checks={
 "objective targeting": 'navigation_target = _fronts_enemy_objective()' in s,
 "objective switching": 'FrontsRules.owner(fronts_posts[fronts_ai_goal]["progress"]) != 1' in s,
 "post-aware respawn": 'player.translation = _fronts_respawn_point(0)' in s and 'enemy.translation = _fronts_respawn_point(1)' in s,
 "safe fallback": 'var fallback = Vector3(0, 0, 9.0) if team == 0 else Vector3(0, 0, -9.0)' in s,
 "post capture HUD": '_fronts_capture_detail()' in s,
 "AI resets per battle": 'fronts_ai_goal = -1' in s,
}
for name,ok in checks.items(): print(("PASS" if ok else "FAIL"), name)
assert all(checks.values())
