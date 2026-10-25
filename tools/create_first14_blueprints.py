#!/usr/bin/env python3
"""Create explicit character appearance blueprints and Kaggle review board.
Does not overwrite reference PNGs or generated GLBs.
"""
import json, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
root=Path("/kaggle/working/Aeryvex-Pro-Godot4")
roster=json.loads((root/"roster/characters.json").read_text())
specs=[
("Revenge of the Sith","Human","shoulder-length wavy dark brown hair; stern youthful face; scar over right eye","dark charcoal and brown layered Jedi tunic, leather tabards, broad utility belt","dark brown, charcoal, muted leather","right-eye scar; dark Jedi layers; shoulder-length hair"),
("Revenge of the Sith","Human","elderly patrician face; swept-back silver hair; neatly trimmed white beard","tailored dark brown tunic, high collar, deep brown cape with ornamental clasp","brown, silver, burgundy","high collar; cape chain; silver swept hair"),
("Revenge of the Sith","Human","short sandy-auburn hair; closely trimmed auburn beard","cream Jedi tunic, brown outer robe, leather belt and tall boots","sand, cream, chestnut","distinctive beard; pale layered tunic"),
("Revenge of the Sith","Human","bald head; mature angular facial structure; dark brown skin","earth-toned Jedi tunic, broad brown cloak, leather belt","cream, brown, purple accent","bald head; unarmored robes"),
("The Phantom Menace","Human","tall male; shoulder-length brown hair; full beard","off-white Jedi tunic and long brown Jedi cloak","ivory, olive-brown","long hair; beard; tall proportion"),
("Revenge of the Sith","Unknown small green alien","very small elderly green alien; deeply wrinkled face; very wide pointed ears; wispy pale hair","loose textured cream robe with tan underlayer","sage green, aged ivory","short stature; outsized ears; wrinkled expressive face"),
("Revenge of the Sith","Cyborg human","glossy domed black helmet; angular respirator; triangular mouth grille; dark eye lenses","layered glossy black helmet and armor, quilted undersuit, chest-control box, floor-length black cape","black, gunmetal, silver","helmet profile; respirator; control chest panel; cape"),
("Return of the Jedi","Human","aged pale deeply creased face; hood concealing brow; intense eyes","voluminous near-black hooded robes, draped long sleeves","black, charcoal, gray","shadowed hood; elderly face"),
("Revenge of the Sith","Kaleesh cyborg","elongated ivory skull-mask with deep-set yellow eyes; skeletal mechanical limbs","ivory segmented skeletal chest plating over dark mechanical torso, thin metallic limbs","bone white, tarnished metal, black","angular ivory faceplate; tall skeletal cyborg"),
("The Clone Wars","Togruta","young orange skin; white facial markings; shorter blue-and-white striped montrals and lekku","dark red and gray sleeveless fitted battle clothing","orange, white, blue, burgundy","young head-tail lengths; white facial markings"),
("Star Wars Rebels","Togruta","adult orange skin; white face markings; tall montrals and much longer striped blue-white lekku","gray and navy armored woven tunic with layered shoulder pieces","orange, white, blue, slate","adult longer head-tails; gray costume"),
("Revenge of the Sith","Kel Dor","orange-brown alien face; protective dark lenses and metallic breathing apparatus","cream and brown Jedi robes with dark gloves","ochre, brown, silver","distinctive breathing mask and goggles"),
("The Clone Wars","Nautolan","green amphibious skin; large dark eyes; thick flexible tentacle-like head appendages","tan Jedi tunic and brown belt","green, tan, brown","many head tentacles; smooth amphibian face"),
("Revenge of the Sith","Togruta","red-orange skin; symmetrical white facial pattern; tall horn-like montrals and long striped lekku","earth-colored Jedi tunic and layered draped robes","red-orange, white, navy, cream","high striped montrals and lekku; red-and-white face")
]
assert len(specs)==14
records=[]
for i,(era,species,face,outfit,palette,must) in enumerate(specs):
 c=roster[i];slug=re.sub(r"[^a-z0-9]+","_",c["name"].lower()).strip("_")
 folder=root/"art/character_models"/f"{i:02d}_{slug}"
 records.append({"id":i,"name":c["name"],"reference_era":era,"species":species,
 "face_and_anatomy":face,"costume":outfit,"palette":palette,"recognition_requirements":must,
 "reference_source":"https://www.starwars.com/databank/",
 "approved_reference_images":[],"appearance_status":"needs_visual_review",
 "reference_png":str(folder/"front.png"),"mesh_glb":str(folder/"character.glb")})
out=root/"roster/appearance_blueprints_first14.json";out.parent.mkdir(exist_ok=True,parents=True)
out.write_text(json.dumps(records,indent=2))
# Present existing reference images without pretending they prove mesh accuracy.
w,h=350,430
canvas=Image.new("RGB",(w*4,h*4),"#e5e7eb");d=ImageDraw.Draw(canvas)
for n,c in enumerate(records):
 x=(n%4)*w;y=(n//4)*h
 p=Path(c["reference_png"])
 if p.exists():
  img=ImageOps.contain(Image.open(p).convert("RGB"),(w-20,300))
  canvas.paste(img,(x+(w-img.width)//2,y+6))
 else:
  d.text((x+12,y+50),"NO IMAGE",fill="red")
 d.text((x+9,y+313),c["name"][:35],fill="black")
 d.text((x+9,y+334),c["reference_era"][:45],fill="black")
 for k,line in enumerate([c["species"],c["recognition_requirements"][:47]]):
  d.text((x+9,y+355+k*18),line,fill="#343434")
preview=root/"roster/appearance_blueprints_first14.jpg";canvas.save(preview,quality=92)
print("BLUEPRINT JSON:",out)
print("REFERENCE REVIEW SHEET:",preview)
print("Reference images available:",sum(Path(c["reference_png"]).exists() for c in records))
print("3D meshes available:",sum(Path(c["mesh_glb"]).exists() for c in records))
print("APPROVED EXACT LIKENESSES: 0 (not yet visually verified)")
