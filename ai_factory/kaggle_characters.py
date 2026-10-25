"""GPU concept candidate generator for Aether World.
Produces DRAFT images only; never changes approved references or claims visual accuracy.
Run in Kaggle after ai_factory/kaggle_bootstrap.py:
    %pip -q install diffusers transformers accelerate safetensors
    !python ai_factory/kaggle_characters.py --all --model stabilityai/sdxl-turbo
For a quick trial: --limit 3. Enable Kaggle GPU and internet.
"""
import argparse, json, hashlib, pathlib, re, sys, csv, os

ROOT=pathlib.Path(__file__).resolve().parents[1]
GAME=ROOT/"original_game"
OUT=pathlib.Path("/kaggle/working/aether_character_candidates")

HEROES=[
  dict(id="hero_kai",name="Kai",faction="aether",role="Teenage agile martial artist",visual="shorter athletic male fighter, dark angular armor with cool teal-blue highlights, two independently held ornate lightning swords, athletic agile stance"),
  dict(id="hero_ryker",name="Ryker",faction="aether",role="Teenage weapons and warfare specialist",visual="broad powerful male weapons tactician, imposing layered battle armor with metallic gold accents, large weapon conduit, sturdy warrior stance"),
  dict(id="hero_lyra",name="Lyra",faction="aether",role="Teenage agile martial artist",visual="athletic female martial artist, flowing dark hair, fitted angular purple accented armor, balanced precise fighting stance")
]
EXTRAS={
 "Orion Valen":"supreme imposing elder ruler, intricate black, white and gold regal battle armor and crown, supreme ornate staff that transforms into two superior rainbow lightning swords",
 "Thalen Orris":"human-sized athletic indigo-skinned alien war general, unique face distinct from Orion, two multicolor lightning swords, less imposing than Orion",
 "Maeryn Sol":"female grand master portal sage, multicolor conduit weapon",
 "Ilyra Venn":"female grand master stealth and intelligence specialist, multicolor twin conduit weapons",
 "Selene Avaris":"female grand master healer, multicolor restoration staff",
 "Drakthar Vex":"terrifying crimson-black armored ex-aether void sovereign, red lightning staff",
 "Korr Uldane":"powerful four-armed alien void lord, red branching lightning",
 "Nyssara Veil":"female void grand lady of shadow, red lightning weapons",
 "Vaelith Sorn":"female void grand lady of broken choir, red lightning",
 "Malveris Thorne":"void grand lord of iron host, red lightning armor"
}
def slug(x):
 return re.sub(r"[^a-z0-9]+","_",str(x).lower()).strip("_")
def list_characters():
    roster=json.loads((GAME/"aeryvex_game_design.json").read_text())["roster"]
    records=HEROES.copy()
    for item in roster:
        name=item["name"]
        extra=EXTRAS.get(name,"")
        if name=="Orion Valen": color="rainbow only for Orion"
        elif item["faction"]=="aether" and item["rank"]=="grand_master": color="multicolor lightning, not supreme rainbow"
        else: color=item["color"]+" lightning"
        records.append(dict(id="roster_"+str(item["id"]),name=name,faction=item["faction"],role=item["role"],visual=(extra or item["role"]+", "+item["ability"]+" ability")+", "+color))
    return records
def generate(args):
    people=list_characters()
    if args.limit:
        people=people[:args.limit]
    OUT.mkdir(parents=True,exist_ok=True)
    gpu_ok=False
    try:
        import torch
        gpu_ok=torch.cuda.is_available()
    except ImportError:
        pass
    print("CHARACTERS:",len(people),"GPU:",gpu_ok)
    if not gpu_ok and not args.manifest_only:
        raise RuntimeError("Enable GPU accelerator in Kaggle settings and install torch/diffusers.")
    records=[]
    generator=None
    if not args.manifest_only:
        import torch
        from diffusers import AutoPipelineForText2Image
        print("Loading model:",args.model)
        pipe=AutoPipelineForText2Image.from_pretrained(args.model,torch_dtype=torch.float16,variant="fp16" if args.fp16_variant else None)
        pipe=pipe.to("cuda")
        pipe.set_progress_bar_config(disable=True)
    for i,item in enumerate(people):
        # Character text is design guidance. Exact likeness needs ORIGINAL approved images.
        prompt=("Original high-end science fantasy game character concept, single full body character standing on neutral dark studio background, clear face, armor, hands and weapons, no lettering, no logos, no collage. "
                +item["name"]+": "+item["role"]+". "+item["visual"]+". "
                +"Lightning stays inside the being until called upon, branching organic electricity rather than rigid lightsaber blades. detailed cinematic character design, realistic materials, head to toe.")
        key=slug(item["id"]+"_"+item["name"])
        image_path=OUT/(key+".png")
        reference_path=GAME/"approved_heroes"/(slug(item["name"])+".png")
        # Approved rulers have a distinct unbacked original montage reference; do not claim similarity.
        reference=reference_path.exists()
        record=dict(id=item["id"],name=item["name"],prompt=prompt,reference_present=reference,output=str(image_path),status="draft_not_approved")
        if not args.manifest_only:
            seed=args.seed+i
            kwargs=dict(prompt=prompt,guidance_scale=0.0,num_inference_steps=4,generator=torch.Generator("cuda").manual_seed(seed))
            try:
                result=pipe(**kwargs).images[0]
            except Exception as e:
                record["status"]="generation_failed"
                record["error"]=str(e)
                records.append(record)
                continue
            result.save(image_path)
            print("GENERATED",i+1,"/",len(people),item["name"])
        records.append(record)
        (OUT/"manifest.json").write_text(json.dumps(records,indent=2))
    # Contact sheets are a review tool, not proof of approved appearance.
    if not args.manifest_only:
        from PIL import Image,ImageDraw
        available=[r for r in records if pathlib.Path(r["output"]).exists()]
        thumb=256
        width=thumb*4
        rows=(len(available)+3)//4
        sheet=Image.new("RGB",(width,max(1,rows)*(thumb+38)),(19,22,32))
        draw=ImageDraw.Draw(sheet)
        for i,r in enumerate(available):
            img=Image.open(r["output"]).convert("RGB")
            img.thumbnail((thumb,thumb))
            x=(i%4)*thumb
            y=(i//4)*(thumb+38)
            sheet.paste(img,(x+(thumb-img.width)//2,y))
            draw.text((x+8,y+thumb+7),r["name"][:32],fill="white")
        sheet.save(OUT/"review_contact_sheet.jpg",quality=92)
        print("REVIEW SHEET:",OUT/"review_contact_sheet.jpg")
    print("MANIFEST:",OUT/"manifest.json")
    print("WARNING: Generated images are candidates, NOT user-approved characters; do not overwrite existing visual locks.")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--all",action="store_true")
    p.add_argument("--limit",type=int,default=0)
    p.add_argument("--model",default="stabilityai/sdxl-turbo")
    p.add_argument("--seed",type=int,default=4100)
    p.add_argument("--manifest-only",action="store_true")
    p.add_argument("--fp16-variant",action="store_true")
    generate(p.parse_args())
