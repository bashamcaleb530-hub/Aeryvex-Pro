'use strict';
const $=id=>document.getElementById(id),token=document.querySelector('meta[name="factory-token"]').content;
let selected=null,jobId=null,lastSignature='',busy=false,polling=false;
async function api(path,data){const r=await fetch(path,{headers:{'Content-Type':'application/json','X-Factory-Token':token},...(data?{method:'POST',body:JSON.stringify(data)}:{})});const body=await r.json();if(!r.ok)throw new Error(body.error||'Request failed');return body;}
function notice(message){$('notice').hidden=false;$('notice').textContent=message;}
function safe(action){return async event=>{if(event)event.preventDefault();try{await action(event);}catch(e){notice(e.message);}};}
function text(tag,value){const n=document.createElement(tag);n.textContent=value;return n;}
function reset(){selected=null;jobId=null;lastSignature='';$('game-name').disabled=false;$('game-name').value='';$('prompt').value='';$('generate').textContent='Generate playable game →';$('examples').hidden=false;$('project-detail').hidden=true;$('deliverables').hidden=true;$('history').replaceChildren();renderJob(null);refresh();$('game-name').focus();}
$('new-project').onclick=reset;
for(const chip of document.querySelectorAll('[data-prompt]'))chip.onclick=()=>{$('prompt').value=chip.dataset.prompt;$('prompt').focus();};
$('generate-form').onsubmit=safe(async()=>{if(busy)throw new Error('Wait for the current build or cancel it.');const name=$('game-name').value.trim();const j=await api('/api/jobs',{name,provider:$('provider').value,prompt:$('prompt').value,action:selected?'revise':'new',native:$('native').checked,budget_seconds:Number($('budget').value)});selected=name;jobId=j.id;renderJob(j);lastSignature='';$('prompt').value='';notice('Build started. You can close this page; the local worker records its progress.');await refresh();});
function renderJob(job){$('job-status').dataset.jobId=job?job.id:'';busy=!!job&&['RUNNING','QUEUED'].includes(job.status);$('job-status').textContent=job?job.status:'READY';$('job-description').textContent=job?`${job.name} · ${job.stage}${job.error?' · '+job.error:''}`:'Your pipeline will appear here. Real results, recorded at every step.';$('elapsed').textContent=job?`${Math.round(job.elapsed_seconds)}s / ${job.budget_seconds}s budget`:'';$('cancel').hidden=!busy;$('resume').hidden=!job||!['FAILED','BLOCKED','INTERRUPTED','CANCELLED','BUDGET_EXCEEDED'].includes(job.status);$('generate').disabled=busy;$('rebuild').disabled=busy;$('rollback').disabled=busy;for(const li of document.querySelectorAll('#stages li')){li.classList.toggle('done',!!job&&job.completed.includes(li.dataset.stage));li.classList.toggle('running',!!job&&job.status==='RUNNING'&&job.stage===li.dataset.stage);}}
async function selectProject(name,jobs=[]){selected=name;lastSignature='';jobId=(jobs.find(j=>j.name===name)||{}).id||null;$('game-name').value=name;$('game-name').disabled=true;$('generate').textContent='Revise & rebuild →';$('examples').hidden=true;$('prompt').value='';$('prompt').placeholder='Add a new area and lightning, lengthen missions, or add a town…';await refresh();}
async function detail(){const d=await api('/api/project?name='+encodeURIComponent(selected)),b=d.bible;$('project-detail').hidden=false;$('project-title').textContent=b.name+' · revision '+b.revision;$('game-name').value=b.name;$('game-name').disabled=true;$('generate').textContent='Revise & rebuild →';$('examples').hidden=true;$('config').textContent=JSON.stringify(b.config,null,2);$('requirements').replaceChildren();for(const r of b.requirements){const li=text('li',r.prompt);li.append(text('small',r.resolution+' · unsupported clauses remain pending'));$('requirements').append(li);}$('history').replaceChildren();for(const h of b.history.slice(-4)){const p=text('p',h.prompt);p.append(text('small','Revision '+h.revision+(h.changes?' · '+(Object.keys(h.changes).join(', ')||'No supported configuration change'):'')));$('history').append(p);}$('checkpoint').replaceChildren(...d.checkpoints.map(n=>{const o=text('option','Revision '+n);o.value=n;return o;}));$('assets').replaceChildren();if(!d.assets.length)$('assets').append(text('li','No approved production assets supplied. Current visuals: primitive prototypes.'));for(const a of d.assets)$('assets').append(text('li',`${a.sha256.slice(0,12)} · license ${a.license_review} · visual ${a.visual_review} · engine ${a.engine_import}`));$('deliverables').hidden=d.status.qa!=='RUNTIME_CHECKED';$('source-download').hidden=!d.source_download;$('source-download').href='/download?kind=source&project='+encodeURIComponent(selected);$('native-download').hidden=!d.native||d.native.status!=='NATIVE_CHECKED';$('native-download').href='/download?kind=native&project='+encodeURIComponent(selected);$('preview-note').textContent='Automated QA: '+d.status.qa+' · Visual review: pending · Native: '+(d.native?d.native.status:'not built')+'. Open the downloaded project in Godot to preview and edit the full game.';}
async function refresh(){if(polling)return;polling=true;try{const s=await api('/api/state');$('engine-status').textContent=s.engine?'Available':'Not found · set GODOT_BIN';$('storage').textContent=s.workspace;$('projects').replaceChildren();for(const p of s.projects){const button=text('button',p.name);button.classList.toggle('selected',selected===p.name);button.onclick=safe(()=>selectProject(p.name,s.jobs));$('projects').append(button);}if(selected){if(!jobId)jobId=(s.jobs.find(j=>j.name===selected)||{}).id||null;const p=s.projects.find(p=>p.name===selected);const j=s.jobs.find(j=>j.id===jobId);const sig=JSON.stringify([selected,p&&p.revision,p&&p.qa,j&&j.status]);if(p&&sig!==lastSignature){await detail();lastSignature=sig;}}if(jobId){const j=await api('/api/job?id='+jobId);renderJob(j.job);$('build-log').textContent=j.log||'Worker queued…';}else renderJob(null);}catch(e){notice(e.message);}finally{polling=false;}}
$('cancel').onclick=safe(async()=>{await api('/api/cancel',{id:jobId});await refresh();});
$('resume').onclick=safe(async()=>{await api('/api/resume',{id:jobId});await refresh();});
$('rebuild').onclick=safe(async()=>{const j=await api('/api/jobs',{name:selected,action:'rebuild',native:$('native').checked,budget_seconds:Number($('budget').value)});jobId=j.id;renderJob(j);lastSignature='';await refresh();});
$('rollback').onclick=safe(async()=>{const j=await api('/api/jobs',{name:selected,action:'rollback',revision:Number($('checkpoint').value),native:$('native').checked,budget_seconds:Number($('budget').value)});jobId=j.id;renderJob(j);lastSignature='';notice('Restoring design as a new revision. History, assets and approved references are retained.');await refresh();});
$('play').onclick=safe(async()=>{const r=await api('/api/play',{name:selected});notice('Game launched on your desktop. '+r.log);});
async function assetData(){const file=$('asset-file').files[0];if(!file)throw new Error('Choose an embedded GLB.');if(file.size>16*1024*1024)throw new Error('Use the CLI for GLB files larger than 16 MB.');const bytes=new Uint8Array(await file.arrayBuffer());let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));return{name:selected,data:btoa(binary),metadata:{approved:$('asset-approved').checked,license:$('asset-license').value,author:$('asset-author').value,source:$('asset-source').value,reference_sha256:$('asset-reference').value}};}
$('asset-form').onsubmit=safe(async()=>{$('asset-result').textContent=JSON.stringify(await api('/api/asset-inspect',await assetData()),null,2);});
$('stage-asset').onclick=safe(async()=>{if(!$('asset-approved').checked)throw new Error('Approve the file for intake before staging it.');$('asset-result').textContent=JSON.stringify(await api('/api/asset-stage',await assetData()),null,2);lastSignature='';await refresh();});
async function meshyAction(route,payload){
 const output=$('meshy-result');
 output.textContent='Requesting '+route+'…';
 try { const result=await api('/api/meshy-'+route,payload);
   if(result.task_id)$('meshy-task').value=result.task_id;
   output.textContent=JSON.stringify(result,null,2);
 } catch(error){ output.textContent='Error: '+error.message; }
}
$('meshy-submit').onclick=safe(async()=>{
 const file=$('meshy-image').files[0];
 if(!file)throw new Error('Choose your reference image first.');
 const extension='.'+file.name.split('.').pop().toLowerCase();
 if(!['.png','.jpg','.jpeg','.webp'].includes(extension)||file.size>8*1024*1024)throw new Error('Choose PNG/JPG/WEBP no larger than 8 MiB.');
 const bytes=new Uint8Array(await file.arrayBuffer());let binary='';
 for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));
 await meshyAction('submit',{image:btoa(binary),extension});
});
for(const action of ['status','download','verify'])$('meshy-'+action).onclick=safe(async()=>{
 const task_id=$('meshy-task').value.trim();
 if(!/^[A-Za-z0-9-]{1,100}$/.test(task_id))throw new Error('Enter a valid Meshy task ID.');
 await meshyAction(action,{task_id});
});
refresh();setInterval(refresh,1200);
