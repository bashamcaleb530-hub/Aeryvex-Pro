"""Go 6 structural regression checks. These cannot replace engine execution."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
main=(root/'scripts/Main.gd').read_text()
rules=(root/'scripts/DuelRules.gd').read_text()
checks={
 'duel rules module exists': 'ROUNDS_TO_WIN = 2' in rules,
 'duel score tracked': 'duel_score = [0, 0]' in main,
 'round remains paused after knockout': 'round_pending = true' in main and 'not round_pending' in main,
 'next round uses same match score': '_spawn(true)' in main,
 'next-round input binding': '"next_round":KEY_N' in main,
 'two-round win match': 'DuelRules.has_winner(duel_score)' in main,
 'wins counted at match completion': 'if duel_winner == 0:' in main,
 'HUD shows round and score': 'Duel round %d, score %d-%d' in main,
 'existing modes retained': all('"'+x+'"' in main for x in ['Duel','Training','Survival','Skirmish','Story']),
 'runtime rules test present': (root/'tests/runtime_duel.gd').exists(),
}
for name,passed in checks.items(): print(('PASS' if passed else 'FAIL')+': '+name)
assert all(checks.values())
print('Go 6 structural checks: %d/%d passed' % (sum(checks.values()),len(checks)))
