'use strict';
// Character Studio + gameplay preview. Shares api/safe/notice/text/selected with app.js.
const studio={data:null,character:null,project:null,mappings:{},signature:''};
const GOOD=['LOCKED','READY','PASSED','APPROVED','VERIFIED','BOUND','CAPTURED'];
const BAD=['REJECTED','FAILED','MISSING_FILE','PARTIAL','REBUILD_REQUIRED'];
const STEP_LABELS={reference:'Approved reference',model:'3D model',inspection:'Godot inspection',approval:'Your approval',animation:'Animation check',binding:'Player binding',game_qa:'Game QA'};
function el(tag,attrs={},...children){const n=document.createElement(tag);for(const[k,v]of Object.entries(attrs)){if(k==='class')n.className=v;else if(k.startsWith('on'))n.addEventListener(k.slice(2),v);else if(v!==false&&v!=null)n.setAttribute(k,v===true?'':v);}for(const c of children.flat())if(c!=null)n.append(c instanceof Node?c:document.createTextNode(String(c)));return n;}
function fileUrl(path){return '/api/character-file?project='+encodeURIComponent(studio.project)+'&path='+encodeURIComponent(path);}
async function fileData(file,limit){if(!file)throw new Error('Choose a file first.');if(file.size>limit)throw new Error('File is larger than '+Math.round(limit/1048576)+' MB.');const bytes=new Uint8Array(await file.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));return btoa(binary);}
function describe(value){if(typeof value==='string')return value;const parts=[];for(const k of ['status','engine_import','render_status','rig','revision','character','sha256']){if(value[k]!=null)parts.push(k.replace('_',' ')+': '+(k==='sha256'?String(value[k]).slice(0,12)+'…':value[k]));}return parts.join(' · ')||'Done';}
function showResult(value){$('studio-status').hidden=false;$('studio-status-text').textContent=describe(value);$('studio-result').textContent=typeof value==='string'?value:JSON.stringify(value,null,2);}
async function act(button,route,payload,message){
 const label=button?button.textContent:'';if(button){button.disabled=true;button.textContent=message||'Working…';}
 showResult((message||'Working…')+' (real operation in progress)');
 try{const result=await api(route,Object.assign({name:studio.project},payload));showResult(result);lastSignature='';await studioRefresh();await refresh();return result;}
 catch(e){showResult('Error: '+e.message);throw e;}
 finally{if(button){button.disabled=false;button.textContent=label;}}
}
function statusPill(value){const cls=GOOD.includes(value)?'pill good':BAD.includes(value)?'pill bad':'pill';return el('span',{class:cls},value||'—');}
function gallery(report,referencePath){
 if(!report)return null;
 const wrap=el('div',{class:'inspection'});
 wrap.append(el('p',{class:'fine'},`Godot ${report.godot_version||''} · import ${report.engine_import} · ${report.rig||''} · ${report.bones??'?'} bones · height ${report.height!=null?report.height.toFixed(2)+' units':'?'} · renders ${report.render_status}`));
 const views=(report.renders||[]).filter(r=>r.kind==='view'),poses=(report.renders||[]).filter(r=>r.kind==='pose');
 const run=report.run||'';
 if(views.length){const compare=el('div',{class:'gallery compare'});if(referencePath)compare.append(el('figure',{},el('img',{src:fileUrl(referencePath),alt:'Approved reference'}),el('figcaption',{},'Approved reference')));for(const r of views)compare.append(el('figure',{},el('img',{src:fileUrl(run+'/'+r.file),alt:r.label+' render'}),el('figcaption',{},r.label.replace('_',' '))));wrap.append(compare);}
 if(poses.length){const g=el('div',{class:'gallery poses'});for(const r of poses)g.append(el('figure',{},el('img',{src:fileUrl(run+'/'+r.file),alt:(r.state||r.clip)+' pose'}),el('figcaption',{},(r.state?r.state+' · ':'')+r.clip)));wrap.append(g);}
 if(report.render_status!=='RENDERED')wrap.append(el('p',{class:'fine'},'No renders: '+report.render_status+'. Install xvfb (xvfb-run) or run the factory in a desktop session to see the model before approving.'));
 if((report.clips||[]).length){const verified=report.mapping_verification||{};const t=el('table',{class:'clips'},el('tr',{},el('th',{},'Clip'),el('th',{},'Length'),el('th',{},'Moves skeleton'),el('th',{},'Mapped to')));for(const c of report.clips){const states=Object.entries(verified).filter(([,v])=>v.clip===c.name).map(([s,v])=>s+(v.status==='ENGINE_VERIFIED'?' ✓':' ✗'));t.append(el('tr',{},el('td',{},c.name),el('td',{},c.length.toFixed(2)+'s'),el('td',{},c.moves_skeleton?'yes':'NO'),el('td',{},states.join(', '))));}wrap.append(t);}
 if((report.engine_errors||[]).length)wrap.append(el('pre',{},report.engine_errors.join('\n')));
 return wrap;
}
function mappingEditor(key,clips,initial){
 const states=studio.data.states.concat(Object.keys(initial||{}).filter(s=>s.startsWith('cinematic_')));
 studio.mappings[key]=studio.mappings[key]||Object.assign({},initial||{});
 const box=el('div',{class:'mapping'});
 for(const state of states){const select=el('select',{'aria-label':'Clip for '+state,onchange:e=>{if(e.target.value)studio.mappings[key][state]=e.target.value;else delete studio.mappings[key][state];}},el('option',{value:''},'— none —'),...clips.map(c=>el('option',{value:c,selected:studio.mappings[key][state]===c},c)));const required=studio.data.required_states.includes(state);box.append(el('label',{},state.toUpperCase()+(required?' *':''),select));}
 return box;
}
function candidateCard(c,character){
 const card=el('div',{class:'card'});
 card.append(el('div',{class:'card-head'},el('b',{},`${c.provider} · ${c.kind}`),statusPill(c.status)),el('p',{class:'fine'},`${c.id}${c.progress!=null&&!c.file?' · '+c.progress+'%':''}${c.animations?' · '+c.animations.length+' clip(s)':''}${c.source_label?' · '+c.source_label:''}`));
 const actions=el('div',{class:'job-actions wrap'});
 const send=(button,payload,msg)=>act(button,'/api/character-meshy',Object.assign({character,candidate_id:c.id},payload),msg);
 if(c.provider==='meshy'&&!c.file){const b1=el('button',{onclick:safe(e=>send(e.target,{action:'refresh'},'Checking Meshy…'))},'Check status');const b2=el('button',{disabled:c.status!=='SUCCEEDED',onclick:safe(e=>send(e.target,{action:'fetch'},'Downloading…'))},'Download GLB');actions.append(b1,b2);}
 if(c.provider==='meshy'&&c.kind==='image_to_3d'&&['SUCCEEDED','DOWNLOADED','STAGED'].includes(c.status))actions.append(el('button',{onclick:safe(e=>{if(!$('meshy-authorize').checked)throw new Error('Tick the Meshy credit authorization first.');return send(e.target,{action:'rig',authorize_paid:true},'Submitting rig…');})},'Auto-rig + basic animations (Meshy)'));
 if(c.file){actions.append(el('button',{class:'primary',onclick:safe(e=>act(e.target,'/api/character-inspect',{character,candidate_id:c.id,mapping:studio.mappings[c.id]||null},'Running Godot inspection…'))},c.report?'Re-inspect in Godot':'Inspect in Godot'));}
 card.append(actions);
 if(c.report){
  card.append(gallery(c.report,studio.data._reference));
  if(c.status!=='STAGED'){
   card.append(el('h4',{},'Animation mapping (suggested from clip names, edit before staging)'),mappingEditor(c.id,c.animations||[],c.suggested_mapping||{}));
   const lic=el('input',{placeholder:'CC0, CC-BY-4.0, Meshy output terms, your license…','aria-label':'License'}),author=el('input',{placeholder:'Author / owner','aria-label':'Author'}),ok=el('input',{type:'checkbox'});
   card.append(el('div',{class:'stage-form'},el('label',{},'LICENSE',lic),el('label',{},'AUTHOR',author),el('label',{class:'checkbox'},ok,' I approve this exact file for intake (appearance approval is a separate step)'),
    el('button',{class:'primary',onclick:safe(e=>{if(c.report.engine_import!=='PASSED')throw new Error('Inspection must pass first.');return act(e.target,'/api/character-stage',{character,candidate_id:c.id,license:lic.value,author:author.value,mapping:studio.mappings[c.id]||{},intake_approved:ok.checked},'Staging…');})},'Stage for approval')));
  }
 }
 if(c.file){const f=el('input',{type:'file',accept:'.glb','aria-label':'Animation GLB'}),rn=el('input',{placeholder:'Optional: SourceClip=NewName, …','aria-label':'Rename clips'}),src=el('input',{placeholder:'Where the animation came from','aria-label':'Animation source'});
  card.append(el('details',{},el('summary',{},'Add animation clips from a same-rig GLB (jump, hurt, death…)'),el('div',{class:'stage-form'},f,rn,src,el('button',{onclick:safe(async e=>{const rename={};for(const part of rn.value.split(',').map(x=>x.trim()).filter(Boolean)){const[a,b]=part.split('=').map(x=>x.trim());if(!a||!b)throw new Error('Use SourceClip=NewName');rename[a]=b;}return act(e.target,'/api/character-merge',{character,candidate_id:c.id,data:await fileData(f.files[0],16*1048576),rename,source_label:src.value},'Merging clips…');})},'Merge into new candidate'))));}
 return card;
}
function assetCard(a,character){
 const card=el('div',{class:'card'+(a.bound?' bound':'')});
 card.append(el('div',{class:'card-head'},el('b',{},a.sha256.slice(0,16)+'…'),a.bound?el('span',{class:'pill good'},'PLAYER VISUAL'):null),
  el('p',{class:'fine'},'License: ',statusPill(a.license_review),' Appearance: ',statusPill(a.visual_review),' Engine: ',statusPill(a.engine_import)),
  el('p',{class:'fine'},`${a.license} · ${a.author} · ${a.source}`));
 if(a.rejection_reason)card.append(el('p',{class:'fine bad-text'},'Rejected: '+a.rejection_reason));
 card.append(gallery(a.inspection,studio.data._reference));
 const licenseOk=el('input',{type:'checkbox',checked:a.license_review==='APPROVED'}),reason=el('input',{placeholder:'Why it does not match (recorded)','aria-label':'Rejection reason'});
 card.append(el('div',{class:'decision'},el('label',{class:'checkbox'},licenseOk,' The license allows use in this game'),
  el('button',{class:'primary',onclick:safe(e=>act(e.target,'/api/character-decide',{sha256:a.sha256,approve:true,license_approved:licenseOk.checked},'Recording approval…'))},'Approve final appearance'),
  reason,el('button',{class:'danger',onclick:safe(e=>act(e.target,'/api/character-decide',{sha256:a.sha256,approve:false,reason:reason.value},'Recording rejection…'))},'Reject')));
 card.append(el('h4',{},'Animation mapping'),mappingEditor('asset-'+a.sha256,a.animations||[],a.animation_mapping||{}),el('button',{onclick:safe(e=>act(e.target,'/api/character-mapping',{sha256:a.sha256,mapping:studio.mappings['asset-'+a.sha256]},'Saving mapping…'))},'Save mapping (new revision)'));
 const height=el('input',{type:'number',min:'0.5',max:'4',step:'0.05',value:'1.8','aria-label':'Height in metres'}),yaw=el('select',{'aria-label':'Model facing'},...[0,90,180,270].map(v=>el('option',{value:v},v+'°')));
 const approved=a.visual_review==='APPROVED'&&a.license_review==='APPROVED';
 card.append(el('div',{class:'bind'},el('label',{},'IN-GAME HEIGHT (M)',height),el('label',{},'FACING CORRECTION',yaw),
  el('button',{class:'primary',disabled:!approved,title:approved?'':'Approve license and appearance first',onclick:safe(e=>act(e.target,'/api/character-bind',{sha256:a.sha256,target_height:Number(height.value),yaw_offset_degrees:Number(yaw.value)},'Verifying import & binding…'))},'Use as player character'),
  a.bound?el('button',{onclick:safe(e=>act(e.target,'/api/character-unbind',{},'Unbinding…'))},'Restore prototype capsule'):null));
 if(a.bound)card.append(el('p',{class:'fine'},'Bound. Press “Rebuild & test” above: Godot QA then plays every mapped state (walk, run, jump, attack, hurt, death…) in the real game.'));
 return card;
}
function renderStudio(){
 const d=studio.data;$('character-studio').hidden=false;
 const names=d.characters.map(c=>c.name);if(!names.includes(studio.character))studio.character=names[0]||null;
 $('studio-characters').replaceChildren(...names.map(n=>el('button',{role:'tab','aria-selected':n===studio.character?'true':'false',class:n===studio.character?'selected':'',onclick:()=>{studio.character=n;studio.mappings={};renderStudio();}},n)));
 $('studio-new').open=!names.length;
 const c=d.characters.find(x=>x.name===studio.character);$('studio-body').hidden=!c;if(!c)return;
 d._reference=c.reference?c.reference.file:null;
 $('studio-steps').replaceChildren(...Object.entries(c.steps).map(([k,v],i)=>el('li',{class:GOOD.includes(v.status)?'done':BAD.includes(v.status)?'warn':''},el('b',{},String(i+1).padStart(2,'0')),el('span',{},STEP_LABELS[k],el('small',{},v.status+(v.detail?' · '+v.detail:''))))));
 if(c.reference){$('studio-reference').src=fileUrl(c.reference.file);$('studio-reference-meta').textContent=`SHA-256 ${c.reference.sha256.slice(0,16)}… · locked ${c.reference.locked_at}${c.reference.note?' · '+c.reference.note:''}`;}
 $('meshy-note').textContent=d.meshy_configured?'Configured. Sends the exact locked reference bytes to Meshy; output stays an unapproved candidate.':'MESHY_API_KEY is not set in the factory process, so Meshy is unavailable. Upload a GLB instead, or restart the factory with the key in its environment.';
 $('studio-meshy-generate').disabled=!d.meshy_configured;
 $('studio-candidates').replaceChildren(...(c.candidates.length?c.candidates.slice().reverse().map(x=>candidateCard(x,c.name)):[el('p',{class:'muted'},'No candidates yet. Generate with Meshy or upload a GLB.')]));
 $('studio-assets').replaceChildren(...(c.assets.length?c.assets.slice().reverse().map(x=>assetCard(x,c.name)):[el('p',{class:'muted'},'Nothing staged. Inspect a candidate in Godot, review it, then stage it.')]));
 renderPreview(d.preview);
}
function renderPreview(report){
 const frames=$('preview-frames');frames.replaceChildren();
 if(!report){$('preview-status').textContent='No gameplay preview captured for this project yet.';return;}
 $('preview-status').textContent=`${report.status} · revision ${report.revision} · ${report.note||''}`;
 for(const f of report.frames||[])frames.append(el('figure',{},el('img',{src:fileUrl(report.folder+'/'+f.file),alt:'Gameplay '+f.label}),el('figcaption',{},f.label)));
}
async function studioRefresh(){
 if(!selected){$('character-studio').hidden=true;studio.project=null;return;}
 if(studio.project!==selected){studio.project=selected;studio.character=null;studio.mappings={};}
 try{const data=await api('/api/characters?name='+encodeURIComponent(selected));const signature=JSON.stringify(data);
 // Re-render only on real change so typed input (reasons, licenses) is never wiped.
 if(signature!==studio.signature||$('character-studio').hidden){studio.signature=signature;studio.data=data;renderStudio();}}
 catch(e){$('character-studio').hidden=true;}
}
$('lock-form').onsubmit=safe(async()=>{const file=$('lock-image').files[0];if(!$('lock-confirm').checked)throw new Error('Confirm that this exact image is the approved appearance.');const ext='.'+file.name.split('.').pop().toLowerCase();const name=$('lock-name').value.trim();await act(null,'/api/character-lock',{character:name,image:await fileData(file,20*1048576),extension:ext,confirmed:true,note:$('lock-note').value},'Locking reference…');studio.character=name;$('lock-form').reset();renderStudio();});
$('upload-form').onsubmit=safe(async()=>{await act(null,'/api/character-upload',{character:studio.character,data:await fileData($('upload-file').files[0],16*1048576),source_label:$('upload-source').value},'Adding candidate…');$('upload-form').reset();});
$('studio-meshy-generate').onclick=safe(e=>{if(!$('meshy-authorize').checked)throw new Error('Tick the Meshy credit authorization first.');return act(e.target,'/api/character-meshy',{character:studio.character,action:'generate',authorize_paid:true},'Submitting to Meshy…');});
$('capture-preview').onclick=safe(async e=>{e.target.disabled=true;$('preview-status').textContent='Running the built game in Godot and capturing frames…';try{const r=await api('/api/preview',{name:selected});renderPreview(r);if(r.status!=='CAPTURED')notice('Preview: '+r.status+(r.detail?' · '+r.detail:''));}finally{e.target.disabled=false;}});
window.studioRefresh=studioRefresh;
