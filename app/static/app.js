"use strict";
const $=id=>document.getElementById(id),blocks=["body","facts","relationships","backlinks","timeline","map","gallery","sources"];
const themes={
 archive:{dark:["#18232D","#23333D","#F0F3F2","#9AD4D0"],light:["#F7F5EF","#FFFFFF","#213035","#116A6C"]},
 atlas:{dark:["#142520","#233A32","#EFF5F0","#ACDDB0"],light:["#F1F5ED","#FFFFFF","#21352C","#226B43"]},
 chronicle:{dark:["#282019","#392C24","#F7F1E9","#F5C584"],light:["#FBF5EA","#FFFDFC","#372A21","#8A451A"]},
 kinship:{dark:["#251E2B","#362B3D","#F7EFF6","#E9B5CD"],light:["#FCF5FB","#FFFFFF","#36283A","#8E376B"]},
 civic:{dark:["#1C2633","#2B3847","#EEF3FA","#A9CCF1"],light:["#F3F6FB","#FFFFFF","#203347","#245C91"]}
};
function luminance(hex){const v=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)/255).map(x=>x<=0.04045?x/12.92:((x+0.055)/1.055)**2.4);return 0.2126*v[0]+0.7152*v[1]+0.0722*v[2];}
function contrast(a,b){const [hi,lo]=[luminance(a),luminance(b)].sort((x,y)=>y-x);return (hi+0.05)/(lo+0.05);}

const state={worlds:[],world:null,entries:[],entry:null,panel:"article",mode:"read",relations:[],media:[],allMedia:[],incoming:[],outgoing:[],layout:[],dirty:false};
const escapeHTML=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const el=(tag,text,cls)=>{const x=document.createElement(tag);if(text!==undefined)x.textContent=text;if(cls)x.className=cls;return x;};
const byId=id=>state.entries.find(e=>e.id===id);
const q=(path,args={})=>path+"?"+new URLSearchParams(args);
const wid=()=>state.world.id;
const num=v=>String(v).trim()===""?null:Number(v);
const when=e=>e.start_year===null&&e.end_year===null?"Undated":(e.start_year===e.end_year?"Year "+e.start_year:"Year "+(e.start_year??"?")+"–"+(e.end_year??"?"));
const active=(e,year)=>(e.start_year===null||e.start_year<=year)&&(e.end_year===null||e.end_year>=year);
const optionList=(node,items,defaultText="Choose…")=>node.replaceChildren(new Option(defaultText,""),...items.map(e=>new Option(e.title+" · "+e.type,e.id)));
function button(text,fn,cls=""){const b=el("button",text,cls);b.onclick=fn;return b;}
function linkTo(e){return button(e.title,()=>open(e.id),"pill");}
function notice(text,error=false){$("notice").textContent=text;$("notice").className=error?"error":"message";clearTimeout(notice.timer);notice.timer=setTimeout(()=>$("notice").textContent="",6000);}
async function api(path,method="GET",body){
 const init={method,headers:{}};if(method!=="GET"){init.headers["X-World-Bible"]="1";if(body!==undefined){init.headers["Content-Type"]="application/json";init.body=JSON.stringify(body);}}
 const res=await fetch(path,init),val=await res.json();if(!res.ok)throw Error(val.error||"Request failed");return val;
}
function safeExit(){return !state.dirty||confirm("Discard unsaved article edits?");}
function dirty(v){state.dirty=v;$("dirtyIndicator").textContent=v?"Unsaved changes":"Saved";}
function setTheme(root,entry){
 const mode=$("appearance").value;
 const preset=themes[entry.theme_id==="custom"?"archive":entry.theme_id]||themes.archive;
 const colors=mode==="high-contrast"?["#000000","#111111","#FFFFFF","#FFFF00"]:preset[mode==="light"?"light":"dark"];
 const accent=entry.accent&&mode!=="high-contrast"&&contrast(entry.accent,colors[0])>=4.5
   &&contrast(entry.accent,colors[1])>=4.5?entry.accent:colors[3];
 for(const [key,index] of [["--entry-bg",0],["--entry-surface",1],["--entry-text",2],["--entry-accent",3]])
   root.style.setProperty(key,index===3?accent:colors[index]);
}
function prose(text){
 // Untrusted author HTML is escaped before generating the controlled subset of tags.
 function inline(s){return escapeHTML(s).replace(/\[\[([a-zA-Z0-9:-]{3,100})(?:\|([^\]\n]{1,180}))?\]\]/g,(_,id,name)=>{
  const e=byId(id);return e?'<a href="#entry='+encodeURIComponent(id)+'" data-target="'+escapeHTML(id)+'">'+escapeHTML(name||e.title)+'</a>':'<span class="broken-link">'+escapeHTML(name||id)+'</span>';
 }).replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>");}
 const lines=text.split(/\r?\n/),out=[];let code=false;
 for(const l of lines){
  if(l.startsWith("\x60\x60\x60")){out.push(code?"</code></pre>":"<pre><code>");code=!code;continue;}
  if(code){out.push(escapeHTML(l)+"\n");continue;}
  const h=l.match(/^(#{1,4})\s+(.+)$/);
  if(h){let tag="h"+(h[1].length+1);out.push("<"+tag+">"+inline(h[2])+"</"+tag+">");}
  else if(!l.trim())out.push("<div class='paragraph-break'></div>");
  else if(/^[-*] /.test(l))out.push("<p>• "+inline(l.slice(2))+"</p>");
  else if(l.startsWith("> "))out.push("<blockquote>"+inline(l.slice(2))+"</blockquote>");
  else out.push("<p>"+inline(l)+"</p>");
 }
 if(code)out.push("</code></pre>");
 return out.join("\n");
}
function bindLinks(root){root.querySelectorAll("[data-target]").forEach(a=>a.onclick=e=>{e.preventDefault();open(a.dataset.target);});}
async function worlds(){
 state.worlds=await api("/api/worlds");
 if(!state.worlds.length)state.worlds.push(await api("/api/worlds","POST",{name:"The New World"}));
 state.world=state.worlds.find(x=>x.id===localStorage.getItem("wb-world"))||state.worlds[0];
 $("world").replaceChildren(...state.worlds.map(w=>new Option(w.name,w.id)));
 $("world").value=wid();localStorage.setItem("wb-world",wid());
 $("worldDescription").textContent=state.world.description||"Separate worldbuilding workspace.";
 await refresh();
}
async function refresh(){
 state.entries=await api(q("/api/entities",{world_id:wid()}));
 renderList();timeline();atlas(false);
 if(state.entry){state.entry=byId(state.entry.id)||null;render();}
}
function renderList(){
 const search=$("search").value.toLowerCase().trim(),type=$("typeFilter").value;
 const entries=state.entries.filter(e=>(!type||e.type===type)&&(!search||[e.title,e.summary,e.body,...e.aliases].some(t=>String(t).toLowerCase().includes(search))));
 const root=$("entryList");root.replaceChildren();
 for(const e of entries){const b=button(e.title,()=>open(e.id),"entry-item"+(state.entry?.id===e.id?" current":""));b.append(el("small",e.type+" · "+e.status));root.append(b);}
 if(!entries.length)root.append(el("p","No matching entries","muted"));
}
async function context(){
 if(!state.entry)return;const id=state.entry.id,p={world_id:wid(),entity_id:id};
 const [r,m,all,i,o]=await Promise.all([api(q("/api/relations",p)),api(q("/api/media",p)),api(q("/api/media",{world_id:wid()})),api(q("/api/backlinks",p)),api(q("/api/outgoing",p))]);
 if(state.entry?.id===id)Object.assign(state,{relations:r,media:m,allMedia:all,incoming:i,outgoing:o});
}
async function open(id){
 if(!safeExit())return;state.entry=byId(id);if(!state.entry)return;
 dirty(false);state.mode="read";await context();panel("article");render();
}
function panel(p){
 if(!safeExit())return;
 state.panel=p;
 for(const name of ["article","timeline","atlas"])$(name+"Panel").hidden=p!==name;
 $("welcome").hidden=p!=="article"||!!state.entry;
 $("modeNav").hidden=p!=="article"||!state.entry;
 document.querySelectorAll("[data-panel]").forEach(b=>b.classList.toggle("active",b.dataset.panel===p));
 if(p==="timeline")timeline();if(p==="atlas")atlas(true);if(p==="article")render();
}
function mode(m){
 if(state.mode==="write"&&m!=="write"&&!safeExit())return;
 state.mode=m;render();
}
function render(){
 const e=state.entry;
 if(!e){$("welcome").hidden=state.panel!=="article";$("modeNav").hidden=true;$("breadcrumb").textContent="Select an entry";return;}
 $("welcome").hidden=true;$("breadcrumb").textContent=e.type+" / "+e.title;
 for(const m of ["read","write","design","explore"])$(m+"Panel").hidden=state.mode!==m;
 document.querySelectorAll("[data-mode]").forEach(b=>b.classList.toggle("active",b.dataset.mode===state.mode));
 if(state.mode==="read")read();if(state.mode==="write")write();
 if(state.mode==="design")design();if(state.mode==="explore")explore();
 inspector();renderList();
}
function read(){
 const e=state.entry,root=$("readPanel");root.replaceChildren();setTheme(root,e);
 const head=el("header",undefined,"entry-hero"),hero=state.media.find(x=>x.role==="hero");
 if(hero){const img=el("img");img.src="/media/"+wid()+"/"+hero.media_id+"-preview";img.alt=hero.alt||hero.title;img.className="hero-img";head.append(img);}
 head.append(el("span",e.type+" · "+e.status,"entry-kicker"),el("h1",e.title),el("p",e.summary||"No summary yet.","entry-subtitle"));root.append(head);
 for(const block of (e.layout.length?e.layout:blocks)){
  const s=el("section",undefined,"entry-section");
  if(block==="body"){const a=el("article",undefined,"prose");a.innerHTML=prose(e.body||"This article has not been written yet.");bindLinks(a);s.append(a);}
  if(block==="facts"){s.append(el("h2","Details"));const grid=el("div",undefined,"facts");for(const [k,v] of [["Type",e.type],["Status",e.status],["Period",when(e)],["Aliases",e.aliases.join(", ")||"None"],["Coordinates",e.lat===null?"Not recorded":e.lat+", "+e.lon]])grid.append(el("p",k+": "+v));s.append(grid);}
  if(block==="relationships"){s.append(el("h2","Relationships"));for(const r of state.relations.filter(relationActive)){const other=byId(r.source_id===e.id?r.target_id:r.source_id);if(other){s.append(el("span",r.predicate.replaceAll("_"," ")+(r.source_id===e.id?" → ":" ← ")));s.append(linkTo(other));}}}
  if(block==="backlinks"){s.append(el("h2","Cross-references"));for(const r of state.incoming){s.append(el("span","Linked from: "));const other=byId(r.id);if(other)s.append(linkTo(other));}for(const r of state.outgoing){const other=byId(r.id);if(other)s.append(linkTo(other));}}
  if(block==="timeline"){s.append(el("h2","Linked historical events"));for(const ev of state.entries.filter(x=>x.type==="event"&&(x.id===e.id||state.relations.some(r=>[r.source_id,r.target_id].includes(e.id)&&[r.source_id,r.target_id].includes(x.id))))){s.append(el("span",when(ev)+" "));s.append(linkTo(ev));}}
  if(block==="map"){s.append(el("h2","Geography"));s.append(el("p",e.lat===null?"No documented coordinates":e.lat+", "+e.lon));if(e.lat!==null)s.append(button("View on atlas",()=>{panel("atlas");center(e.lon,e.lat,7);}));}
  if(block==="gallery"){s.append(el("h2","Media"));const g=el("div",undefined,"gallery");for(const m of state.media){const f=el("figure"),img=el("img");img.src="/media/"+wid()+"/"+m.media_id+"-preview";img.alt=m.alt||m.title;img.loading="lazy";f.append(img,el("figcaption",m.caption||m.title));g.append(f);}s.append(g);}
  if(block==="sources"){s.append(el("h2","Sources & editorial status"),el("p","Canon status: "+e.status+". Link Source entries and cite evidence in article prose.","muted"));}
  root.append(s);
 }
}
function write(){
 const e=state.entry;
 for(const [id,v] of Object.entries({eTitle:e.title,eType:e.type,eStatus:e.status,eAliases:e.aliases.join(", "),eStart:e.start_year,eEnd:e.end_year,eLat:e.lat,eLon:e.lon,eSummary:e.summary,eBody:e.body}))$(id).value=v??"";
 $("suggestions").hidden=true;dirty(false);
}
async function save(){
 const e=state.entry;
 const data={title:$("eTitle").value.trim(),type:$("eType").value,status:$("eStatus").value,
  aliases:$("eAliases").value.split(",").map(x=>x.trim()).filter(Boolean),summary:$("eSummary").value,body:$("eBody").value,
  start_year:num($("eStart").value),end_year:num($("eEnd").value),lat:num($("eLat").value),lon:num($("eLon").value)};
 try{state.entry=await api(q("/api/entity",{world_id:wid(),id:e.id}),"PATCH",data);dirty(false);await refresh();await context();render();notice("Saved.");}catch(err){notice(err.message,true);}
}
function createEntry(){
 if(!safeExit())return;$("createTitle").value="";$("createType").value="place";$("createDialog").showModal();$("createTitle").focus();
}
async function submitCreate(){
 const title=$("createTitle").value.trim(),type=$("createType").value;
 if(!title)return;
 try{
  const e=await api(q("/api/entities",{world_id:wid()}),"POST",{title,type});
  $("createDialog").close();await refresh();await open(e.id);mode("write");
 }catch(err){notice(err.message,true);}
}

async function remove(){
 if(!confirm("Delete this entry? Referenced entries cannot be deleted without resolving their links."))return;
 try{await api(q("/api/entity",{world_id:wid(),id:state.entry.id}),"DELETE");state.entry=null;await refresh();render();notice("Deleted.");}catch(err){notice(err.message,true);}
}
function discover(){
 const body=$("eBody").value,found=[];
 for(const e of state.entries.filter(e=>e.id!==state.entry.id))for(const alias of new Set([e.title,...e.aliases])){
  if(alias.length<4)continue;const low=body.toLowerCase(),needle=alias.toLowerCase();let start=0;
  while((start=low.indexOf(needle,start))!==-1){
   const prev=body[start-1]||"",next=body[start+needle.length]||"";
   if(!/[\p{L}\p{N}_]/u.test(prev)&&!/[\p{L}\p{N}_]/u.test(next)&&!body.slice(Math.max(0,start-50),start+needle.length+20).includes("[["))found.push({start,alias,e});
   start+=needle.length;
  }
 }
 const root=$("suggestions");root.hidden=false;root.replaceChildren(el("h3","Potential references · review before linking"));
 for(const x of found.slice(0,40)){const row=el("div",undefined,"suggestion-row");row.append(el("span",'"'+x.alias+'" → '));
 row.append(button(x.e.title+" ("+x.e.type+")",()=>{
  const text=$("eBody").value;if(text.slice(x.start,x.start+x.alias.length).toLowerCase()!==x.alias.toLowerCase())return notice("Text changed; scan again.",true);
  $("eBody").value=text.slice(0,x.start)+"[["+x.e.id+"|"+text.slice(x.start,x.start+x.alias.length)+"]]"+text.slice(x.start+x.alias.length);
  dirty(true);discover();
 },"pill"));root.append(row);}
 if(!found.length)root.append(el("p","No additional unlinked names found.","muted"));
}
function inspector(){
 const root=$("context");root.replaceChildren();const e=state.entry;if(!e)return;
 root.append(el("h3",e.title),el("p",e.type+" · "+e.status,"muted"),el("h3","Backlinks"));
 for(const x of state.incoming){const target=byId(x.id);if(target)root.append(linkTo(target));}
 root.append(el("h3","References"));for(const x of state.outgoing){const target=byId(x.id);if(target)root.append(linkTo(target));}
 root.append(el("h3","Related"));for(const r of state.relations.filter(relationActive)){const target=byId(r.source_id===e.id?r.target_id:r.source_id);if(target)root.append(linkTo(target));}
}
const historicalYear=()=>num($("globalYear").value)??50;
const relationActive=r=>(r.start_year===null||r.start_year<=historicalYear())&&(r.end_year===null||r.end_year>=historicalYear());
function graph(){
 const root=$("relationshipGraph");root.replaceChildren();const e=state.entry;if(!e)return;
 const relationships=state.relations.filter(relationActive).slice(0,18);
 if(!relationships.length){root.append(el("p","No dated relationships active in the selected year.","muted"));return;}
 const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");
 svg.setAttribute("viewBox","0 0 660 330");svg.setAttribute("role","img");
 svg.setAttribute("aria-label","Relationship map for "+e.title);
 const ns="http://www.w3.org/2000/svg";
 const shape=(name,attrs)=>{const x=document.createElementNS(ns,name);for(const [k,v] of Object.entries(attrs))x.setAttribute(k,v);svg.append(x);return x;};
 const center=[330,165],count=relationships.length;
 const positions=relationships.map((r,i)=>{const t=2*Math.PI*i/count-Math.PI/2;return [330+240*Math.cos(t),165+119*Math.sin(t)];});
 relationships.forEach((r,i)=>{const pos=positions[i];shape("line",{x1:center[0],y1:center[1],x2:pos[0],y2:pos[1],stroke:"currentColor","stroke-opacity":".34","stroke-width":"2"});
 const other=byId(r.source_id===e.id?r.target_id:r.source_id);if(!other)return;
 const circle=shape("circle",{cx:pos[0],cy:pos[1],r:21,fill:"#3c6174",stroke:"#b7dce1","stroke-width":"2"});
 const title=document.createElementNS(ns,"title");title.textContent=other.title+" · "+r.predicate;circle.append(title);
 circle.style.cursor="pointer";circle.addEventListener("click",()=>open(other.id));
 const text=shape("text",{x:pos[0],y:pos[1]+36,"text-anchor":"middle",fill:"currentColor","font-size":"11"});text.textContent=other.title.length>23?other.title.slice(0,20)+"…":other.title;
 });
 shape("circle",{cx:center[0],cy:center[1],r:31,fill:"#a57b48",stroke:"#ecd19a","stroke-width":"3"});
 const title=shape("text",{x:330,y:212,"text-anchor":"middle",fill:"currentColor","font-size":"12","font-weight":"bold"});title.textContent=e.title.length>32?e.title.slice(0,29)+"…":e.title;
 root.append(svg);
 if(state.relations.filter(relationActive).length>18)root.append(el("p","Showing the first 18 connections. Use the complete relationship list above for the rest.","muted"));
}
function setHistoricalYear(raw){
 const year=num(raw);if(year===null||!Number.isInteger(year))return;
 for(const id of ["globalYear","timelineYear","atlasYear"])$(id).value=year;
 if(state.entry){if(state.mode==="read")read();if(state.mode==="explore")graph();inspector();}
 if(state.panel==="timeline")timeline();
 if(state.panel==="atlas")atlas(true);
}
function explore(){
 const e=state.entry;optionList($("relTarget"),state.entries.filter(x=>x.id!==e.id));
 const rows=$("relationCards");rows.replaceChildren();graph();
 for(const r of state.relations){const other=byId(r.source_id===e.id?r.target_id:r.source_id);if(!other)continue;
  const row=el("div",undefined,"record-card");row.append(el("span",r.predicate+" · "+r.status+" · "+when(r)+" · "+(r.notes||"")+" "),linkTo(other),button("Remove",async()=>{
   if(!confirm("Remove relationship?"))return;try{await api(q("/api/relation",{world_id:wid(),id:r.id}),"DELETE");await context();render();}catch(err){notice(err.message,true);}
  }));rows.append(row);}
 const family=$("familyView");family.replaceChildren();
 if(e.type==="person")for(const [kind,rels] of [["Parents",state.relations.filter(r=>r.target_id===e.id&&r.predicate.endsWith("parent_of"))],["Children",state.relations.filter(r=>r.source_id===e.id&&r.predicate.endsWith("parent_of"))],["Partners",state.relations.filter(r=>[r.source_id,r.target_id].includes(e.id)&&["partner_of","married_to"].includes(r.predicate))]]){
  const row=el("div",kind+": ","family-row");for(const r of rels){const other=byId(r.source_id===e.id?r.target_id:r.source_id);if(other)row.append(linkTo(other));}family.append(row);
 }else family.append(el("p","Select a person to view family connections.","muted"));
 const refs=$("referenceView");refs.replaceChildren();for(const r of state.incoming)refs.append(el("p","Linked from "+r.title));for(const r of state.outgoing)refs.append(el("p","Links to "+r.title));
 const s=$("mediaSelect");optionList(s,state.allMedia.map(m=>({id:m.id,title:m.title,type:m.mime})));
 const g=$("mediaCards");g.replaceChildren();for(const m of state.media){const f=el("figure",undefined,"media-item"),img=el("img");img.src="/media/"+wid()+"/"+m.media_id+"-preview";img.alt=m.alt||m.title;f.append(img,el("figcaption",m.title+" · "+m.role),button("Unlink",async()=>{
  try{await api(q("/api/media-use",{world_id:wid(),id:m.use_id}),"DELETE");await context();render();}catch(err){notice(err.message,true);}
 }));g.append(f);}
}
async function addRelation(){
 const target_id=$("relTarget").value;if(!target_id)return;
 try{await api(q("/api/relations",{world_id:wid()}),"POST",{source_id:state.entry.id,target_id,predicate:$("relType").value,start_year:num($("relStart").value),end_year:num($("relEnd").value),status:$("relStatus").value,notes:$("relNotes").value});await context();render();notice("Relationship added.");}catch(err){notice(err.message,true);}
}
async function uploadImage(){
 const f=$("imageFile").files[0];if(!f)return;
 if(f.size>12000000)return notice("Image exceeds 12 MB.",true);
 try{const res=await fetch(q("/api/upload",{world_id:wid()}),{method:"POST",headers:{"X-World-Bible":"1","X-File-Name":encodeURIComponent(f.name),"Content-Type":"application/octet-stream"},body:f});
 const media=await res.json();if(!res.ok)throw Error(media.error);state.allMedia=await api(q("/api/media",{world_id:wid()}));
 optionList($("mediaSelect"),state.allMedia.map(m=>({id:m.id,title:m.title,type:m.mime})));$("mediaSelect").value=media.id;notice("Uploaded. Choose placement role to attach image.");
 }catch(err){notice(err.message,true);}
}
async function attachImage(){
 const media_id=$("mediaSelect").value;if(!media_id)return;
 try{await api(q("/api/media-use",{world_id:wid()}),"POST",{entity_id:state.entry.id,media_id,role:$("mediaRole").value});await context();render();notice("Image attached.");}catch(err){notice(err.message,true);}
}
function design(){
 const e=state.entry;state.layout=[...(e.layout.length?e.layout:blocks)];
 $("dTheme").value=e.theme_id;$("dAccent").value=e.accent||"#77B7AE";layoutControls();
}
function layoutControls(){
 const root=$("layoutBlocks");root.replaceChildren();
 for(const name of blocks){const row=el("div",undefined,"layout-row"),check=el("input");check.type="checkbox";check.checked=state.layout.includes(name);
  check.onchange=()=>{state.layout=check.checked?[...state.layout,name]:state.layout.filter(x=>x!==name);layoutControls();};
  row.append(check,el("span",name,"layout-name"));const i=state.layout.indexOf(name);
  if(i>=0){row.append(button("↑",()=>{if(i>0)[state.layout[i-1],state.layout[i]]=[state.layout[i],state.layout[i-1]];layoutControls();}),button("↓",()=>{if(i<state.layout.length-1)[state.layout[i+1],state.layout[i]]=[state.layout[i],state.layout[i+1]];layoutControls();}));}root.append(row);
 }
 previewDesign();
}
function previewDesign(){
 const root=$("designPreview");root.replaceChildren();setTheme(root,{...state.entry,theme_id:$("dTheme").value,accent:$("dAccent").value});
 root.append(el("h3",state.entry.title),el("p","Visible sections: "+(state.layout.join(" → ")||"none")));
}
async function saveDesign(){
 try{state.entry=await api(q("/api/entity",{world_id:wid(),id:state.entry.id}),"PATCH",{theme_id:$("dTheme").value,accent:$("dAccent").value,layout:state.layout});
 await refresh();await context();render();notice("Design saved.");}catch(err){notice(err.message,true);}
}
function timeline(){
 if(!state.world)return;const s=$("timelineScope"),selected=s.value;optionList(s,state.entries,"Entire world");if(byId(selected))s.value=selected;
 const root=$("timelineList");root.replaceChildren(),year=num($("timelineYear").value)??50;
 const events=state.entries.filter(e=>e.type==="event"&&($("timelineAll").checked||active(e,year))&&(!s.value||e.id===s.value||state.relations.some(r=>[r.source_id,r.target_id].includes(e.id)&&[r.source_id,r.target_id].includes(s.value)))).sort((a,b)=>(a.start_year??999999)-(b.start_year??999999));
 for(const e of events){const row=el("div",undefined,"timeline-event");row.append(el("time",when(e)),linkTo(e),el("p",e.summary||"No summary","muted"));root.append(row);}
 if(!events.length)root.append(el("p","No matching historical events.","muted"));
}
const map={lon:0,lat:25,zoom:2,drag:null},TILE=256;
function project(lon,lat,z){const scale=TILE*2**z,r=Math.max(-85,Math.min(85,lat))*Math.PI/180;return{x:(lon+180)/360*scale,y:(1-Math.log(Math.tan(r)+1/Math.cos(r))/Math.PI)/2*scale};}
function inverse(x,y,z){const scale=TILE*2**z,n=Math.PI-2*Math.PI*y/scale;return{lon:x/scale*360-180,lat:180/Math.PI*Math.atan(Math.sinh(n))};}
function center(lon,lat,zoom){Object.assign(map,{lon,lat,zoom});atlas(true);}
function atlas(paint=true){
 if(!state.world)return;
 const year=num($("atlasYear").value)??50,places=state.entries.filter(e=>e.lat!==null&&e.lon!==null&&active(e,year));
 const out=$("atlasResults");out.replaceChildren(el("h3",places.length+" mapped entries"));for(const e of places)out.append(linkTo(e));
 if(!paint||$("atlasPanel").hidden)return;
 const frame=$("map"),w=frame.clientWidth,h=frame.clientHeight;if(!w||!h)return;
 const center=project(map.lon,map.lat,map.zoom),left=center.x-w/2,top=center.y-h/2,N=2**map.zoom;
 const tiles=$("tiles"),pins=$("pins");tiles.replaceChildren();pins.replaceChildren();
 for(let x=Math.floor(left/TILE);x<=Math.floor((left+w)/TILE);x++)for(let y=Math.floor(top/TILE);y<=Math.floor((top+h)/TILE);y++){
  if(y<0||y>=N)continue;const img=el("img");img.src="https://tile.openstreetmap.org/"+map.zoom+"/"+((x%N+N)%N)+"/"+y+".png";
  img.alt="";img.draggable=false;img.loading="lazy";img.style.left=(x*TILE-left)+"px";img.style.top=(y*TILE-top)+"px";tiles.append(img);
 }
 for(const e of places){const pt=project(e.lon,e.lat,map.zoom),x=pt.x-left,y=pt.y-top;if(x<0||x>w||y<0||y>h)continue;
  const marker=button("●",()=>open(e.id),"map-pin");marker.title=e.title;marker.style.left=x+"px";marker.style.top=y+"px";if($("mapLabels").checked)marker.append(el("span",e.title));pins.append(marker);
 }
 $("mapReadout").textContent="Zoom "+map.zoom+" · Year "+year+" · "+places.length+" mapped";
}
function setupMap(){
 const frame=$("map");frame.addEventListener("pointerdown",e=>{if(e.target.closest("button"))return;map.drag={x:e.clientX,y:e.clientY,p:project(map.lon,map.lat,map.zoom)};frame.setPointerCapture(e.pointerId);});
 frame.addEventListener("pointermove",e=>{if(!map.drag)return;const d=map.drag,pt=inverse(d.p.x-(e.clientX-d.x),d.p.y-(e.clientY-d.y),map.zoom);map.lon=Math.max(-180,Math.min(180,pt.lon));map.lat=Math.max(-85,Math.min(85,pt.lat));atlas(true);});
 for(const event of ["pointerup","pointercancel"])frame.addEventListener(event,()=>map.drag=null);
 frame.addEventListener("wheel",e=>{e.preventDefault();map.zoom=Math.max(1,Math.min(15,map.zoom+(e.deltaY<0?1:-1)));atlas(true);},{passive:false});
 $("mapZoomIn").onclick=()=>{map.zoom=Math.min(15,map.zoom+1);atlas(true);};
 $("mapZoomOut").onclick=()=>{map.zoom=Math.max(1,map.zoom-1);atlas(true);};
 $("mapReset").onclick=()=>center(0,25,2);$("mapLabels").onchange=()=>atlas(true);
 $("atlasYear").onchange=()=>setHistoricalYear($("atlasYear").value);
 $("timelineYear").onchange=()=>setHistoricalYear($("timelineYear").value);
 window.addEventListener("resize",()=>{if(state.panel==="atlas")atlas(true);});
}
async function switchWorld(id){
 if(!safeExit()){$("world").value=wid();return;}state.world=state.worlds.find(w=>w.id===id);
 state.entry=null;state.relations=[];state.media=[];state.incoming=[];state.outgoing=[];
 localStorage.setItem("wb-world",id);$("worldDescription").textContent=state.world.description||"";
 await refresh();panel("article");render();
}
async function createWorld(){
 if(!safeExit())return;const name=prompt("New world name");if(!name)return;
 try{const w=await api("/api/worlds","POST",{name});state.worlds.push(w);$("world").add(new Option(w.name,w.id));await switchWorld(w.id);notice("New independent world created.");}catch(err){notice(err.message,true);}
}
async function editWorld(){
 if(!safeExit())return;
 const name=prompt("World name",state.world.name);if(name===null)return;
 const description=prompt("World description",state.world.description||"");if(description===null)return;
 const epochText=prompt("Calendar anchor year (optional; leave blank for unconfirmed)",state.world.epoch_year??"");
 if(epochText===null)return;
 const epoch_year=epochText.trim()===""?null:Number(epochText);
 if(epoch_year!==null&&!Number.isInteger(epoch_year))return notice("Invalid epoch year.",true);
 try{
  const updated=await api(q("/api/world",{world_id:wid()}),"PATCH",{name,description,epoch_year});
  state.world=updated;
  state.worlds=state.worlds.map(w=>w.id===updated.id?updated:w);
  $("world").selectedOptions[0].textContent=updated.name;
  $("worldDescription").textContent=updated.description||"";
  notice("World settings saved.");
 }catch(err){notice(err.message,true);}
}
async function exportWorld(){
 try{const data=await api(q("/api/export",{world_id:wid()})),blob=new Blob([JSON.stringify(data,null,2)],{type:"application/json"}),url=URL.createObjectURL(blob),a=el("a");a.href=url;a.download="world-bible-export.json";a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);notice("Data exported; back up image originals separately.");}catch(err){notice(err.message,true);}
}
async function importWorld(){
 const file=$("importFile").files[0];if(!file)return;
 try{
  if(file.size>25000000)throw Error("Archive exceeds 25 MB.");
  const contents=JSON.parse(await file.text());
  if(contents.media_metadata?.length||contents.media_uses?.length)throw Error("This export includes image references. Restore the .worldbible folder to preserve originals.");
  if(!confirm("Import into a NEW isolated world? Existing worlds will not be overwritten."))return;
  const outcome=await api("/api/import","POST",contents);
  state.worlds.push(outcome.world);$("world").add(new Option(outcome.world.name,outcome.world.id));
  await switchWorld(outcome.world.id);notice("Imported "+outcome.entries+" entries and "+outcome.relations+" relationships.");
 }catch(err){notice("Import failed: "+err.message,true);}
 finally{$("importFile").value="";}
}
function wire(){
 $("world").onchange=e=>switchWorld(e.target.value);$("worldSettings").onclick=editWorld;$("cancelCreate").onclick=()=>$("createDialog").close();$("createForm").onsubmit=e=>{e.preventDefault();submitCreate();};$("importWorld").onclick=()=>$("importFile").click();$("importFile").onchange=importWorld;$("addWorld").onclick=createWorld;$("newEntry").onclick=createEntry;$("welcomeNew").onclick=createEntry;$("export").onclick=exportWorld;
 $("welcomeTimeline").onclick=()=>panel("timeline");$("welcomeAtlas").onclick=()=>panel("atlas");
 $("search").oninput=renderList;$("typeFilter").onchange=renderList;$("globalYear").onchange=()=>setHistoricalYear($("globalYear").value);
 document.querySelectorAll("[data-panel]").forEach(b=>b.onclick=()=>panel(b.dataset.panel));
 document.querySelectorAll("[data-mode]").forEach(b=>b.onclick=()=>mode(b.dataset.mode));
 $("appearance").value=localStorage.getItem("wb-mode")||"dark";document.body.dataset.appearance=$("appearance").value;
 $("appearance").onchange=()=>{document.body.dataset.appearance=$("appearance").value;localStorage.setItem("wb-mode",$("appearance").value);render();};
 $("editForm").onsubmit=e=>{e.preventDefault();save();};$("editForm").oninput=()=>dirty(true);
 $("deleteEntry").onclick=remove;$("findLinks").onclick=discover;$("addRelation").onclick=addRelation;
 $("uploadImage").onclick=uploadImage;$("attachImage").onclick=attachImage;
 $("dTheme").onchange=previewDesign;$("dAccent").oninput=previewDesign;$("saveDesign").onclick=saveDesign;
 $("resetDesign").onclick=()=>{state.layout=[...blocks];layoutControls();};
 $("timelineScope").onchange=timeline;$("timelineAll").onchange=timeline;
 setupMap();window.addEventListener("beforeunload",e=>{if(state.dirty){e.preventDefault();e.returnValue="";}});
}
async function init(){wire();try{await worlds();render();notice("World Bible Studio ready.");}catch(err){notice("Server error: "+err.message,true);}}
init();
