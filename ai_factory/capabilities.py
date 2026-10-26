"""Honest status of each Game Factory component, shown in the app and the delivery report.

IMPLEMENTED: performs real operations with engine-verified tests.
PARTIAL: real but bounded; the detail says what is missing.
NOT_IMPLEMENTED: no working operation yet; nothing in the UI pretends otherwise.
"""
COMPONENTS = [
    ('AI Game Director', 'PARTIAL',
     'Natural-language prompts become a validated, versioned Game Bible (template parser or optional local Ollama). '
     'Only the two bounded genres are buildable; other clauses are kept as pending requirements.'),
    ('Character Studio', 'IMPLEMENTED',
     'Locked approved reference, Meshy or uploaded GLB candidates, real Godot inspection with renders, '
     'human approve/reject, player binding. Live Meshy calls not yet verified against an account.'),
    ('Character Animation', 'PARTIAL',
     'Plays reviewed embedded clips for idle, walk, run, jump, fall, land, attack, hurt, death and cinematic_* '
     'with crossfades, verified in-engine. No motion generation or cross-skeleton retargeting.'),
    ('World Builder', 'PARTIAL',
     '1-5 connected areas, collidable town buildings, navigation mesh and lighting from templates. '
     'No terrain sculpting, authored environments or NPC placement tools.'),
    ('Gameplay Builder', 'PARTIAL',
     '3D RPG campaign: missions, dialogue, melee and abilities, inventory, XP upgrades, checkpoints and saves; '
     '2D collect/survive. Wrestling or fighting-game mechanics and branching choices are not implemented.'),
    ('Story Director', 'NOT_IMPLEMENTED',
     'Fixed mission briefings only; no branching campaigns, decisions or consequences yet.'),
    ('Cinematic Director', 'NOT_IMPLEMENTED',
     'A cinematic_* character clip can play at mission completion; no cutscene cameras, transitions or sound.'),
    ('Audio Studio', 'NOT_IMPLEMENTED', 'No music, sound effects or voice integration yet.'),
    ('Testing and Repair', 'IMPLEMENTED',
     'Real Godot import/startup/gameplay/campaign/character scenarios bound to source hashes, gameplay preview '
     'capture, durable jobs with cancel/resume and one safe import-cache retry. No automatic code repair.'),
    ('Build and Export', 'IMPLEMENTED',
     'Integrity-checked Godot project ZIP and Linux x86_64 export re-tested from a relocated executable; '
     'requires matching official export templates. Other platforms not implemented.'),
]


def registry():
    return [{'name': name, 'status': status, 'detail': detail} for name, status, detail in COMPONENTS]
