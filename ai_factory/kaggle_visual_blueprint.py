"""Build a reference-safe character blueprint for Kaggle from Aether canon."""
import json, pathlib, hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
GAME=ROOT/"original_game"
OUT=pathlib.Path("/kaggle/working/aether_character_blueprint")
OUT.mkdir(parents=True,exist_ok=True)
design=json.loads((GAME/"aeryvex_game_design.json").read_text())
lock=json.loads((GAME/"character_visual_lock.json").read_text())
heroes=[
 ("Kai","agile teenage male martial fighter, black layered armor, teal-blue lightning, TWO independently held swords"),
 ("Ryker","heavily armored teenage male weapons and warfare specialist, gold-blue conduit energy"),
 ("Lyra","agile teenage female fighter, long dark hair, fitted dark-violet armor, purple lightning")
]
special={
 "Orion Valen":"Supreme leader; approved ornate armor and crown; rainbow lightning staff that transforms into two swords",
 "Thalen Orris":"Human-scale athletic indigo-skinned Ormathi; distinct from Orion; TWO multicolor swords",
 "Drakthar Vex":"Supreme Void leader; approved likeness, red branching lightning",
}
approved_rulers={r["name"]:r for r in lock["rulers"]}
characters=[]
for i,(name,look) in enumerate(heroes):
    path=GAME/"approved_heroes"/(name.lower()+".png")
    characters.append(dict(key="hero_"+name.lower(),name=name,role="playable hero",visual_blueprint=look,
      reference_path=str(path),reference_available=path.is_file(),visual_approval="REFERENCE_REQUIRED",
      generation_mode="reference_guided_only",model_verified=False))
for item in design["roster"]:
    name=item["name"]
    ruler=approved_rulers.get(name)
    if ruler:
        ref=GAME/"approved_heroes"/"ten_rulers_approved_lineup.png"
        role=f'{item["role"]}; {ruler["species"]} of {ruler["galaxy"]}'
        look=special.get(name,"Approved ten-ruler lineup is visual authority; do not invent facial features, armor, or proportions")
    else:
        ref=GAME/"approved_heroes"/(name.lower().replace(" ","_")+".png")
        role=item["role"]
        look=f'{item["faction"]} faction, {item["rank"]} rank, {item["color"]} electrical effects; canon abilities: {item["ability"]}'
    characters.append(dict(key=f'roster_{item["id"]}',name=name,role=role,visual_blueprint=look,
       reference_path=str(ref),reference_available=ref.is_file(),visual_approval="REFERENCE_REQUIRED",
       generation_mode="reference_guided_only" if ruler else "draft_concept_allowed_not_approved",model_verified=False))
manifest=dict(title="Aether World — visual canon production blueprint",schema_version=1,
 instructions=[
 "Approved references outrank text descriptions. Never automatically change approved faces, physiques, armor, weapons or lineage.",
 "DO NOT describe text-to-image candidates as user-approved or in-game-ready.",
 "When image reference is absent, mark BLOCKED_REFERENCE and do not pretend visual similarity was checked.",
 "Create annotated comparison sheets only after both original approved reference and candidate are available.",
 "Produce a turnaround after user approves visual candidate; then create GLB, validate skeleton animations and Godot import.",
 "Keep source images/GLBs and rendered screenshots; preserve copyright/provenance and no destructive overwrite.",
 "Branching electrical conduits, not solid metal swords or standard lightsabers; preserve faction/rank colors.",
 "Additional soldiers, mentors, NPCs and other unnamed characters are a separate discovered roster, not included in 23 named entities."
 ],characters=characters,
 ruler_visual_lock_sha256=lock["approved_lineup_sha256"])
for c in characters:
 c["status"]="READY_FOR_REFERENCE_COMPARISON" if c["reference_available"] else "BLOCKED_REFERENCE"
(OUT/"blueprint.json").write_text(json.dumps(manifest,indent=2))
print("Blueprint characters:",len(characters))
print("Missing exact reference for:",sum(not c["reference_available"] for c in characters))
print("Blueprint:",OUT/"blueprint.json")
print("Do not claim approved appearance until approved references and user visual review are available.")
