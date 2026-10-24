"""Go 5 source-integrity checks, not a substitute for running Godot."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
main=(root/'scripts/Main.gd').read_text()
brain=(root/'scripts/EnemyBrain.gd').read_text()
visual=(root/'scripts/FighterVisual.gd').read_text()
checks={
 'brain module is loaded': 'const EnemyBrain = preload("res://scripts/EnemyBrain.gd")' in main,
 'three named difficulty presets': 'const NAMES = ["Rookie", "Veteran", "Master"]' in brain,
 'AI reaction time configured': 'const REACTION' in brain and 'EnemyBrain.reaction_delay(ai_difficulty)' in main,
 'AI attack interval varies with skill': 'EnemyBrain.next_attack_delay(ai_difficulty)' in main,
 'AI aggression decision': 'EnemyBrain.attack_for_opening(' in main,
 'AI stamina gates offense': 'guard < 12.0' in brain,
 'defensive opportunity decisions': 'EnemyBrain.defense_for_threat(' in main,
 'parry and block reactions': 'choice == "parry"' in main and 'choice == "guard"' in main,
 'AI dodge spends stamina': 'stamina[1] -= 20.0' in main,
 'AI dodge has cooldown': 'ai_dodge_cooldown = 2.2' in main,
 'AI dodge invulnerability': 'invuln[1] = 0.33' in main,
 'AI steer by spacing': 'EnemyBrain.steering(' in main and 'desired_distance(' in brain,
 'AI orbit changes sides': 'ai_strafe_side = -ai_strafe_side' in main,
 'AI reduces speed when guarding': 'movement_speed *= 0.48' in main,
 'AI reads attack windup': 'strikes[0]["phase"] == "windup"' in main,
 'player attack telegraph': 'ENEMY WINDUP!' in main,
 'difficulty can be changed': '"difficulty_change":KEY_T' in main,
 'difficulty persists in save': '"ai_level": ai_difficulty' in main and 'data.get("ai_level", 1)' in main,
 'AI reset during new match': 'ai_reacted=false' in main and 'ai_reaction_time=0.0' in main,
 'hit transition avoids stale state': 'if match_done or strikes[who] != strike:' in main,
 'frame independent animation blends': '1.0 - exp(-delta * 12.0)' in visual,
 'guard arms use both shoulders': 'left_arm.rotation_degrees.z' in visual and 'right_arm.rotation_degrees.z' in visual,
 'engine tests added': (root/'tests/runtime_ai.gd').exists(),
 'no accidental game modes removed': all(m in main for m in ['"Duel"','"Survival"','"Training"','"Skirmish"','"Story"']),
 'no merge conflict artifacts': not re.search(r'^(?:<<<<<<<|=======|>>>>>>>)',main,re.M),
}
for label,good in checks.items():
 print(('PASS' if good else 'FAIL')+': '+label)
if not all(checks.values()): raise SystemExit(1)
print(f'Go 5 static checks: {sum(checks.values())}/{len(checks)} passed')
