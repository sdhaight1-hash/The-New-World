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

const state={worlds:[],world:null,entries:[],entry:null,panel:"home",mode:"read",relations:[],media:[],allMedia:[],incoming:[],outgoing:[],layout:[],dirty:false,designDirty:false,networkFilter:"all",globalMedia:[],mediaUses:[],published:false,boards:[],board:null,boardZoom:1};
state.v2={types:[],categories:[],tags:[],memberships:{},metadata:null};
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
function safeExit(){return (!state.dirty&&!state.designDirty)||confirm("Discard unsaved article or design edits?");}
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
 state.v2.types=await api("/api/v2/types");
 await refresh();workspaceChrome();
}
const ENTRY_MODES={
 read:{name:"Reading mode",description:"Explore the article and its verified connections. Navigation and backlinks stay close at hand.",icon:"▤",hint:"ARTICLE VIEW"},
 write:{name:"Writing mode",description:"Focus on the content, names and historical facts. Use Discover References to connect existing entries.",icon:"✎",hint:"CONTENT EDITOR"},
 design:{name:"Design mode",description:"Reorder visible sections, apply a visual theme, and choose an entry accent without changing the facts.",icon:"▧",hint:"PRESENTATION EDITOR"},
 explore:{name:"Connection mode",description:"Manage typed relationships, family links and media placements for this record.",icon:"⌘",hint:"RELATIONSHIP EDITOR"}
};
const SPACE_META={
 home:{name:"World Overview",label:"OVERVIEW",description:"Your worldbuilding workspace, records, and progress.",icon:"⌂",accent:"#8ebfb5"},
 article:{name:"Encyclopedia",label:"KNOWLEDGE LIBRARY",description:"Read, author, design, and link world records.",icon:"▤",accent:"#89bdac"},
 atlas:{name:"Historical Atlas",label:"GEOGRAPHICAL WORKSPACE",description:"Explore mapped places, resources, and routes in 2D.",icon:"◇",accent:"#9ebf8b"},
 timeline:{name:"Chronology",label:"HISTORICAL WORKSPACE",description:"Study events and relationships across time.",icon:"◷",accent:"#d3b081"},
 network:{name:"Connections",label:"RELATIONSHIP WORKSPACE",description:"Trace the network joining people, places, and organizations.",icon:"⌘",accent:"#b49dce"},
 media:{name:"Media Library",label:"VISUAL ARCHIVE",description:"Images, source artwork, portraits and their usage.",icon:"▧",accent:"#92bcd5"},
 boards:{name:"Moodboards",label:"VISUAL DEVELOPMENT",description:"Compose visual references using shared world assets.",icon:"▦",accent:"#d8b58b"}
};
const displayType=t=>({person:"People",place:"Locations",event:"Events",organization:"Factions & organizations",family:"Families & households",object:"Objects & resources",source:"Sources & research",subject:"Topics & articles"})[t]||t.replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase());
const groupOrder=["place","organization","person","family","event","object","source","subject"];
function categoryCounts(){
 const counts=new Map();
 for(const e of state.entries)counts.set(e.type,(counts.get(e.type)||0)+1);
 return [...counts].sort((a,b)=>{
  const ia=groupOrder.indexOf(a[0]),ib=groupOrder.indexOf(b[0]);
  return (ia===-1?999:ia)-(ib===-1?999:ib)||a[0].localeCompare(b[0]);
 });
}
function workspaceChrome(){
 const p=state.panel,meta=SPACE_META[p]||SPACE_META.home;
 document.body.dataset.space=p;
 document.body.dataset.mode=state.mode;
 document.body.style.setProperty("--space-accent",meta.accent);
 const banner=$("entryModeBanner");
 banner.hidden=p!=="article"||!state.entry;
 if(!banner.hidden){
  const modeMeta=ENTRY_MODES[state.mode]||ENTRY_MODES.read;
  $("entryModeIcon").textContent=modeMeta.icon;
  $("entryModeTitle").textContent=modeMeta.name;
  $("entryModeDescription").textContent=modeMeta.description;
  $("entryModeContext").textContent=modeMeta.hint;
 }
 $("spaceHeading").textContent=meta.name;
 $("spaceEyebrow").textContent=state.world?.name.toUpperCase()+" / "+meta.label;
 $("spaceSubtitle").textContent=meta.description;
 $("spaceEmblem").textContent=meta.icon;
 $("workspaceScope").textContent=p==="article"&&state.entry?displayType(state.entry.type)+" · "+state.entry.status:"WORLD · "+(state.world?.name||"");
 $("entryToolbar").hidden=p!=="article"||!state.entry;
 renderPublication();
 $("modeNav").hidden=p!=="article"||!state.entry;
 $("welcome").hidden=p!=="article"||!!state.entry;
 document.querySelectorAll("[data-panel]").forEach(b=>{
  const active=b.dataset.panel===p;
  b.classList.toggle("active",active);
  if(active)b.setAttribute("aria-current","page");
  else b.removeAttribute("aria-current");
 });
 $("libraryHeading").textContent=p==="home"?"World index":p==="boards"?"World record palette":p==="media"?"Record navigator":p==="network"?"Connected records":p==="timeline"?"Chronology index":p==="atlas"?"Geographical index":"Entity Explorer";
 $("navHelp").textContent=p==="boards"?"Find references to arrange on a moodboard.":p==="media"?"Select the records these assets appear in.":p==="atlas"?"Find places and linked settlements.":p==="timeline"?"Find historical events and participants.":p==="network"?"Browse the people, places and organizations in this network.":"Browse by type or search the full encyclopedia.";
 const count=state.entries.length;
 $("navStats").textContent=count+" "+(count===1?"entry":"entries")+" · "+categoryCounts().length+" types";
}
async function refresh(){
 state.entries=await api(q("/api/entities",{world_id:wid()}));
 const [categories,tags,memberships]=await Promise.all([
  api(q("/api/v2/categories",{world_id:wid()})),
  api(q("/api/v2/tags",{world_id:wid()})),
  api(q("/api/v2/memberships",{world_id:wid()}))
 ]);
 Object.assign(state.v2,{categories,tags,memberships});
 populateV2Filters();
 const filter=$("typeFilter"),before=filter.value;
 filter.replaceChildren(new Option("All entries",""));
 for(const [type] of categoryCounts())filter.add(new Option(displayType(type),type));
 filter.value=[...filter.options].some(o=>o.value===before)?before:"";
 renderList();
 renderHome();
 if(state.panel==="timeline")timeline();
 if(state.panel==="atlas")atlas(false);
 if(state.panel==="network")network();
 if(state.panel==="media")mediaWorkspace();
 if(state.panel==="boards")boardsWorkspace();
 if(state.entry){state.entry=byId(state.entry.id)||null;if(state.panel==="article")render();}
 workspaceChrome();
}
function v2CategoryLabel(category){
 const segments=[category.name],visited=new Set([category.id]);
 let parent=category.parent_id;
 while(parent&&!visited.has(parent)){
  visited.add(parent);
  const found=state.v2.categories.find(x=>x.id===parent);if(!found)break;
  segments.unshift(found.name);parent=found.parent_id;
 }
 return segments.join(" / ");
}
function populateV2Filters(){
 const category=$("v2CategoryFilter"),tag=$("v2TagFilter");
 const priorCategory=category.value,priorTag=tag.value;
 category.replaceChildren(new Option("All collections",""),
  ...state.v2.categories.map(c=>new Option(v2CategoryLabel(c),c.id)));
 tag.replaceChildren(new Option("All tags",""),
  ...state.v2.tags.map(t=>new Option(t.name,t.id)));
 category.value=[...category.options].some(o=>o.value===priorCategory)?priorCategory:"";
 tag.value=[...tag.options].some(o=>o.value===priorTag)?priorTag:"";
}
function categoryControls(){
 const root=$("categoryChips");root.replaceChildren();
 const counts=categoryCounts(),selected=$("typeFilter").value;
 const all=button("All · "+state.entries.length,()=>{ $("typeFilter").value="";renderList();},"category-chip"+(!selected?" active":""));
 root.append(all);
 for(const [type,count] of counts){
  const chip=button(displayType(type)+" · "+count,()=>{
   $("typeFilter").value=type;renderList();
  },"category-chip"+(selected===type?" active":""));
  root.append(chip);
 }
}
function renderList(){
 if(!state.world)return;
 const search=$("search").value.toLowerCase().trim(),type=$("typeFilter").value;
 const categoryId=$("v2CategoryFilter").value,tagId=$("v2TagFilter").value;
 const entries=state.entries.filter(e=>(!type||e.type===type)
  &&(!categoryId||(state.v2.memberships[e.id]?.categories||[]).includes(categoryId))
  &&(!tagId||(state.v2.memberships[e.id]?.tags||[]).includes(tagId))&&
  (!search||[e.title,e.summary,e.body,...e.aliases].some(t=>String(t).toLowerCase().includes(search))));
 const root=$("entryList");root.replaceChildren();
 $("entryCount").textContent=String(entries.length);
 categoryControls();
 if(!entries.length){root.append(el("p","No matching entries. Try another search or category.","muted"));return;}
 const ordered=[...entries].sort((a,b)=>{
  const ai=groupOrder.indexOf(a.type),bi=groupOrder.indexOf(b.type);
  return (ai===-1?999:ai)-(bi===-1?999:bi)||a.type.localeCompare(b.type)||a.title.localeCompare(b.title);
 });
 let lastType="";
 for(const e of ordered){
  if(e.type!==lastType){lastType=e.type;const h=el("div",displayType(e.type),"entry-group");root.append(h);}
  const b=button(e.title,()=>open(e.id),"entry-item"+(state.entry?.id===e.id?" current":""));
  b.append(el("small",e.status+(e.summary?" · "+e.summary.slice(0,58):"")));
  if(e.id===state.entry?.id)b.setAttribute("aria-current","true");
  root.append(b);
 }
}
function renderHome(){
 const w=state.world;if(!w)return;
 $("homeWorldTitle").textContent=w.name;
 $("homeWorldDescription").textContent=w.description||"An independent worldbuilding project. Build places, people, events and relationships in one knowledge space.";
 const counts=categoryCounts(),total=state.entries.length,events=counts.find(x=>x[0]==="event")?.[1]||0,places=counts.find(x=>x[0]==="place")?.[1]||0;
 const established=state.entries.filter(e=>e.status==="established").length;
 const metrics=[["All records",total,"Open the encyclopedia","article"],["Locations",places,"Browse your geographical records","article"],["Historical events",events,"View your chronology","timeline"],["Established",established,"Records marked established","article"]];
 const grid=$("homeMetrics");grid.replaceChildren();
 for(const [name,value,detail,target] of metrics){
  const tile=button("",()=>{if(name==="Locations"){$("typeFilter").value="place";renderList();}panel(target);},"metric-card");
  tile.append(el("span",name,"metric-label"),el("strong",String(value),"metric-value"),el("span",detail,"metric-detail"));
  grid.append(tile);
 }
 const recent=$("recentEntries");recent.replaceChildren();
 const items=[...state.entries].sort((a,b)=>b.updated_at.localeCompare(a.updated_at)).slice(0,8);
 if(!items.length)recent.append(el("p","Create your first entry to begin building your world.","empty-state"));
 for(const e of items){
  const row=button("",()=>open(e.id),"home-record");
  row.append(el("span",e.title,"home-record-title"),el("small",displayType(e.type)+" · "+e.status));
  recent.append(row);
 }
 const cats=$("homeCategories");cats.replaceChildren();
 for(const [type,count] of counts){
  const row=button("",()=>{$("typeFilter").value=type;renderList();panel("article");},"home-category");
  row.append(el("span",displayType(type)),el("strong",String(count)));
  cats.append(row);
 }
 if(!counts.length)cats.append(el("p","Your categories will appear as entries are added.","empty-state"));
 const statuses=$("homeStatuses");statuses.replaceChildren();
 for(const name of ["established","working","disputed","superseded"]){
  const n=state.entries.filter(e=>e.status===name).length;
  const row=el("div",undefined,"status-row");
  row.append(el("span",name,"status-label status-"+name),el("strong",String(n)));
  statuses.append(row);
 }
}

async function context(){
 if(!state.entry)return;const id=state.entry.id,p={world_id:wid(),entity_id:id};
 const [r,m,all,i,o,pub,metadata]=await Promise.all([api(q("/api/relations",p)),api(q("/api/media",p)),api(q("/api/media",{world_id:wid()})),api(q("/api/backlinks",p)),api(q("/api/outgoing",p)),api(q("/api/publication",{world_id:wid(),id})),api(q("/api/v2/metadata",{world_id:wid(),id}))]);
 if(state.entry?.id===id){Object.assign(state,{relations:r,media:m,allMedia:all,incoming:i,outgoing:o,published:pub.published});renderPublication();state.v2.metadata=metadata;}
}
function renderPublication(){
 const visible=state.panel==="article"&&!!state.entry;
 $("publishStatus").hidden=!visible;
 $("publishToggle").hidden=!visible;
 const published=state.published;
 $("publishStatus").textContent=published?"Published for readers":"Draft · not published";
 $("publishStatus").className="publish-status "+(published?"is-published":"is-draft");
 $("publishToggle").textContent=published?"Unpublish":"Publish";
 $("viewPublished").hidden=!visible||!published;
 if(visible&&published)$("viewPublished").href="/read/?world="+encodeURIComponent(wid())+"#/article/"+encodeURIComponent(state.entry.id);
}
async function togglePublication(){
 const e=state.entry;if(!e)return;
 if(state.dirty||state.designDirty)return notice("Save this entry and its design before changing publication.",true);
 const next=!state.published;
 if(!confirm(next?"Publish “"+e.title+"” to the reader-facing encyclopedia? Subsequent edits to this article will be visible immediately.":"Unpublish “"+e.title+"” from the reader-facing encyclopedia?"))return;
 try{
  const result=await api(q("/api/publication",{world_id:wid(),id:e.id}),"POST",{published:next});
  state.published=result.published;renderPublication();
  notice(next?"Article published for readers.":"Article returned to draft.");
 }catch(error){notice(error.message,true);}
}
async function open(id){
 if(!safeExit())return;
 const target=byId(id);if(!target)return;
 state.entry=target;state.v2.metadata=null;dirty(false);state.designDirty=false;state.mode="read";
 state.panel="article";
 await context();
 panel("article");render();
}
function panel(p){
 if(!Object.hasOwn(SPACE_META,p))return;
 if(!safeExit())return;
 if(p!==state.panel){if(state.dirty)dirty(false);state.designDirty=false;}
 state.panel=p;
 for(const name of ["home","article","timeline","atlas","network","media","boards"])$(name+"Panel").hidden=p!==name;
 $("welcome").hidden=p!=="article"||!!state.entry;
 workspaceChrome();
 if(p==="home")renderHome();
 if(p==="timeline")timeline();
 if(p==="atlas")atlas(true);
 if(p==="network")network();
 if(p==="media")mediaWorkspace();
 if(p==="boards")boardsWorkspace();
 if(p==="article")render();
}

function mode(m){
 if((state.mode==="write"||state.mode==="design")&&m!==state.mode&&!safeExit())return;
 state.designDirty=false;
 state.mode=m;render();
}
function render(){
 const e=state.entry;
 if(!e){
  $("welcome").hidden=state.panel!=="article";
  $("entryToolbar").hidden=true;
  $("modeNav").hidden=true;
  $("breadcrumb").textContent="Select an entry";
  workspaceChrome();
  return;
 }
 $("breadcrumb").textContent=displayType(e.type)+" / "+e.title;
 workspaceChrome();
 for(const m of ["read","write","design","explore"])$(m+"Panel").hidden=state.mode!==m;
 document.querySelectorAll("[data-mode]").forEach(b=>{
  const selected=b.dataset.mode===state.mode;
  b.classList.toggle("active",selected);
  b.setAttribute("aria-pressed",String(selected));
 });
 if(state.mode==="read")read();
 if(state.mode==="write")write();
 if(state.mode==="design")design();
 if(state.mode==="explore")explore();
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
  if(block==="facts"){s.append(el("h2","Details"));const grid=el("div",undefined,"facts");
  const md=state.v2.metadata||{properties:{},categories:[],tags:[]};
  const named=(ids,items)=>ids.map(id=>items.find(x=>x.id===id)?.name).filter(Boolean).join(", ");
  const props=Object.entries(md.properties||{}).filter(([,value])=>value!==null&&value!=="").map(([key,value])=>[key.replaceAll("_"," "),byId(value)?.title||value]);
  for(const [k,v] of [["Type",e.type],["Subtype",md.subtype||""],["Status",e.status],["Period",when(e)],["Collections",named(md.categories,state.v2.categories)],["Tags",named(md.tags,state.v2.tags)],["Aliases",e.aliases.join(", ")||"None"],["Coordinates",e.lat===null?"Not recorded":e.lat+", "+e.lon],...props])if(v)grid.append(el("p",k+": "+v));s.append(grid);}
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
 const typeSelect=$("eType");
 if(![...typeSelect.options].some(x=>x.value===e.type))typeSelect.add(new Option("Custom: "+e.type,e.type));
 typeSelect.value=e.type;$("editCustomTypeField").hidden=true;$("editCustomType").value="";
 $("suggestions").hidden=true;dirty(false);renderV2Editor();
}
async function save(){
 const e=state.entry;
 const data={title:$("eTitle").value.trim(),type:$("eType").value==="custom"?$("editCustomType").value.trim():$("eType").value,status:$("eStatus").value,
  aliases:$("eAliases").value.split(",").map(x=>x.trim()).filter(Boolean),summary:$("eSummary").value,body:$("eBody").value,
  start_year:num($("eStart").value),end_year:num($("eEnd").value),lat:num($("eLat").value),lon:num($("eLon").value)};
 try{state.entry=await api(q("/api/entity",{world_id:wid(),id:e.id}),"PATCH",data);dirty(false);await refresh();await context();render();notice("Saved.");}catch(err){notice(err.message,true);}
}
const STARTER_ARTICLES={
 place:{theme:"atlas",hint:"Geographical regions, settlements, sites and environmental history.",sections:["Geography and setting","Settlement and land use","Water, resources and infrastructure","Historical development","People and institutions","Sources and open questions"]},
 organization:{theme:"civic",hint:"Governments, factions, guilds, companies, associations and informal groups.",sections:["Founding and purpose","Organization and leadership","Members and branches","Territory, resources and relationships","Historical development","Sources and open questions"]},
 person:{theme:"kinship",hint:"Biographies, life histories, residences, kinship and participation in events.",sections:["Life and background","Family and relationships","Residences and work","Historical events and activities","Legacy and sources"]},
 family:{theme:"kinship",hint:"Households, ancestry, kinship groups and their history over time.",sections:["Origins and identity","Members and kinship","Residences and migration","Activities and social ties","Historical development","Sources"]},
 event:{theme:"chronicle",hint:"Historically situated events with participants, locations and consequences.",sections:["Overview","Background and causes","Participants and locations","Sequence of events","Consequences and later interpretation","Sources and uncertainties"]},
 source:{theme:"archive",hint:"Historical references, documents, testimony, provenance and disputed evidence.",sections:["Description","Origin and provenance","Contents and testimony","Reliability and limitations","Related records"]},
 object:{theme:"archive",hint:"Objects, materials, technologies, resources and artifacts.",sections:["Description and characteristics","Origins and manufacture","Uses and owners","Historical context","Sources"]},
 subject:{theme:"archive",hint:"Culture, customs, ecological topics, general history or other subjects.",sections:["Overview","Background","Regional variation","Historical development","Related records and sources"]}
};
function updateCreateHint(){
 const type=$("createType").value;
 $("customTypeField").hidden=type!=="custom";
 const entry=STARTER_ARTICLES[type];
 $("createTypeHint").textContent=entry?.hint||"Define a custom category for this world. You can write your own structure and relationships.";
}
function createEntry(){
 if(!safeExit())return;$("createTitle").value="";$("createType").value="place";$("customType").value="";$("createOutline").checked=true;updateCreateHint();$("createDialog").showModal();$("createTitle").focus();
}
async function submitCreate(){
 const title=$("createTitle").value.trim(),type=$("createType").value==="custom"?$("customType").value.trim():$("createType").value;
 if(!title)return;
 try{
  const starter=STARTER_ARTICLES[type];
  const body=$("createOutline").checked&&starter?starter.sections.map(section=>"## "+section+"\n\n").join("\n"):"";
  const e=await api(q("/api/entities",{world_id:wid()}),"POST",{title,type,body,theme_id:starter?.theme||"archive"});
  $("createDialog").close();await refresh();await open(e.id);mode("write");
 }catch(err){notice(err.message,true);}
}

async function remove(){
 if(!confirm("Delete this entry? Referenced entries cannot be deleted without resolving their links."))return;
 try{await api(q("/api/entity",{world_id:wid(),id:state.entry.id}),"DELETE");state.entry=null;await refresh();render();notice("Deleted.");}catch(err){notice(err.message,true);}
}
function renderV2Editor(){
 const entry=state.entry,md=state.v2.metadata||{subtype:null,properties:{},categories:[],tags:[]};
 if(!entry)return;
 const def=state.v2.types.find(t=>t.key===entry.type);
 const sub=$("v2Subtype");sub.replaceChildren(new Option("No subtype",""),
  ...(def?.subtypes||[]).map(t=>new Option(t.replaceAll("_"," "),t)));
 sub.value=md.subtype||"";
 const cat=$("v2Categories"),tags=$("v2Tags");
 cat.replaceChildren(...state.v2.categories.map(c=>new Option(c.name,c.id)));
 tags.replaceChildren(...state.v2.tags.map(t=>new Option(t.name,t.id)));
 for(const opt of cat.options)opt.selected=md.categories.includes(opt.value);
 for(const opt of tags.options)opt.selected=md.tags.includes(opt.value);
 const root=$("v2PropertyFields");root.replaceChildren();
 for(const field of def?.fields||[]){
  const label=el("label",field.key.replaceAll("_"," ").replace(/\\b\\w/g,c=>c.toUpperCase()));
  let control;
  if(field.kind==="choice"){
   control=el("select");control.add(new Option("Not recorded",""));
   for(const value of field.options||[])control.add(new Option(value,value));
  }else if(field.kind==="entry"){
   control=el("select");control.add(new Option("Not recorded",""));
   for(const e of state.entries.filter(x=>x.id!==entry.id))control.add(new Option(e.title+" · "+e.type,e.id));
  }else{control=el("input");control.maxLength=2000;control.placeholder="Not recorded";}
  control.dataset.property=field.key;control.value=md.properties[field.key]||"";
  label.append(control);root.append(label);
 }
 $("v2MetaStatus").textContent=def?"Type-aware properties":"Custom type · no property schema";
}
async function saveV2Metadata(){
 if(!state.entry)return;
 const subtype=$("v2Subtype").value||null;
 const props={};
 for(const element of $("v2PropertyFields").querySelectorAll("[data-property]"))
  if(element.value.trim())props[element.dataset.property]=element.value.trim();
 const values=sel=>[...$(sel).selectedOptions].map(o=>o.value);
 try{
  const payload={subtype,properties:props,categories:values("v2Categories"),tags:values("v2Tags")};
  state.v2.metadata=await api(q("/api/v2/metadata",{world_id:wid(),id:state.entry.id}),"POST",payload);
  await refresh();renderV2Editor();$("v2MetaStatus").textContent="Saved";
  notice("Entry properties and classifications saved.");
 }catch(err){$("v2MetaStatus").textContent=err.message;notice(err.message,true);}
}
async function createV2Classification(kind){
 const field=$(kind==="category"?"v2NewCategory":"v2NewTag");
 const name=field.value.trim();if(!name)return;
 try{
  await api(q(kind==="category"?"/api/v2/categories":"/api/v2/tags",{world_id:wid()}),"POST",
   kind==="category"?{name,parent_id:$("v2CategoryFilter").value||null}:{name});
  field.value="";await refresh();
  if(state.entry)renderV2Editor();
  notice((kind==="category"?"Collection":"Tag")+" created.");
 }catch(err){notice(err.message,true);}
}
async function discover(){
 const e=state.entry;if(!e)return;
 if(state.dirty||$("eBody").value!==e.body)return notice("Save article changes before discovering references.",true);
 try{
  const response=await api(q("/api/v2/mentions",{world_id:wid(),id:e.id}));
  const root=$("suggestions");root.hidden=false;root.replaceChildren(el("h3","Unlinked references · author review"));
  const list=response.suggestions;
  if(!list.length){root.append(el("p","No unlinked names found in the saved article.","muted"));return;}
  for(const candidate of list){
   const row=el("div",undefined,"suggestion-row");
   const snippet=e.body.slice(Math.max(0,candidate.start-45),Math.min(e.body.length,candidate.end+55)).replace(/\\s+/g," ");
   row.append(el("span",snippet,"v2-mention-excerpt"));
   for(const target of candidate.candidates){
    const payload={revision:response.revision,start:candidate.start,end:candidate.end,
      fingerprint:candidate.fingerprint,target_id:target.id};
    row.append(button("Link → "+target.title+" ("+target.type+")",async()=>{
     try{
      state.entry=await api(q("/api/v2/mentions/approve",{world_id:wid(),id:e.id}),"POST",payload);
      await refresh();await context();render();await discover();
      notice("Approved permanent link.");
     }catch(err){notice(err.message,true);}
    },"pill"));
    row.append(button("Ignore "+target.title,async()=>{
     try{
      await api(q("/api/v2/mentions/ignore",{world_id:wid(),id:e.id}),"POST",payload);
      await discover();
     }catch(err){notice(err.message,true);}
    },"pill"));
   }
   root.append(row);
  }
 }catch(err){notice(err.message,true);}
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
async function showEntryBoards(){
 const entry=state.entry;if(!entry)return;
 const root=$("entryBoards");root.replaceChildren(el("p","Loading associated boards…","muted"));
 try{
  const world=wid(),all=await api(q("/api/boards",{world_id:world}));
  if(wid()!==world||state.entry?.id!==entry.id)return;
  root.replaceChildren();
  const boards=all.filter(board=>board.entity_id===entry.id);
  for(const board of boards){
   const card=button("",async()=>{panel("boards");await loadBoard(board.id);},"entry-board-link");
   card.append(el("strong",board.title),el("small",board.item_count+" visual references"));
   root.append(card);
  }
  if(!boards.length)root.append(el("p","No visual research boards attached yet.","muted"));
 }catch(error){root.replaceChildren(el("p",error.message,"error"));}
}
function explore(){
 showEntryBoards();
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
 const g=$("mediaCards");g.replaceChildren();for(const m of state.media){const f=el("figure",undefined,"media-item"),img=el("img");img.src="/media/"+wid()+"/"+m.media_id+"-preview";img.alt=m.alt||m.title;f.append(img,el("figcaption",m.title+" · "+m.role),button("Edit image",async()=>{
  const title=prompt("Image title",m.title);if(title===null)return;
  const alt=prompt("Descriptive alternative text",m.alt||"");if(alt===null)return;
  const credit=prompt("Credit / source attribution",m.credit||"");if(credit===null)return;
  const caption=prompt("Caption on this article",m.caption||"");if(caption===null)return;
  try{
    await api(q("/api/media",{world_id:wid(),id:m.media_id}),"PATCH",{title,alt,credit});
    await api(q("/api/media-use",{world_id:wid(),id:m.use_id}),"PATCH",{caption});
    await context();render();notice("Image details saved.");
  }catch(err){notice(err.message,true);}
 }),button("Unlink",async()=>{
  try{await api(q("/api/media-use",{world_id:wid(),id:m.use_id}),"DELETE");await context();render();}catch(err){notice(err.message,true);}
 }));g.append(f);}
}
async function addRelation(){
 const target_id=$("relTarget").value;if(!target_id)return;
 try{await api(q("/api/relations",{world_id:wid()}),"POST",{source_id:state.entry.id,target_id,predicate:$("relType").value==="custom"?$("relCustom").value.trim():$("relType").value,start_year:num($("relStart").value),end_year:num($("relEnd").value),status:$("relStatus").value,notes:$("relNotes").value});await context();render();notice("Relationship added.");}catch(err){notice(err.message,true);}
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
const BLOCK_LABELS={
 body:"Article body",facts:"Record details",relationships:"Relationships",
 backlinks:"References",timeline:"Associated history",map:"Geography",gallery:"Image gallery",sources:"Sources & status"
};
function design(){
 const e=state.entry;
 state.layout=[...(e.layout.length?e.layout:blocks)];
 $("dTheme").value=e.theme_id;
 $("dOverrideAccent").checked=!!e.accent;
 $("dAccent").disabled=!e.accent;
 $("dAccent").value=e.accent||"#77B7AE";
 layoutControls();
}
function layoutControls(){
 const root=$("layoutBlocks");root.replaceChildren();
 const displayOrder=[...state.layout,...blocks.filter(name=>!state.layout.includes(name))];
 for(const name of displayOrder){
  const row=el("div",undefined,"layout-row design-block");
  row.dataset.block=name;
  const included=state.layout.includes(name);
  const check=el("input");check.type="checkbox";check.checked=included;
  check.setAttribute("aria-label","Show "+BLOCK_LABELS[name]);
  check.onchange=()=>{
   state.layout=check.checked?[...state.layout,name]:state.layout.filter(x=>x!==name);
   state.designDirty=true;layoutControls();
  };
  const handle=el("span","⠿","drag-handle");handle.title="Drag to change section order";
  row.append(handle,check,el("span",BLOCK_LABELS[name],"layout-name"));
  const i=state.layout.indexOf(name);
  if(i>=0){
   row.draggable=true;row.title="Drag to rearrange this section";
   row.addEventListener("dragstart",e=>{
    e.dataTransfer.setData("text/plain",name);e.dataTransfer.effectAllowed="move";row.classList.add("dragging");
   });
   row.addEventListener("dragend",()=>row.classList.remove("dragging"));
   row.addEventListener("dragover",e=>{e.preventDefault();e.dataTransfer.dropEffect="move";row.classList.add("drag-over");});
   row.addEventListener("dragleave",()=>row.classList.remove("drag-over"));
   row.addEventListener("drop",e=>{
    e.preventDefault();row.classList.remove("drag-over");
    const source=e.dataTransfer.getData("text/plain");
    if(!state.layout.includes(source)||source===name)return;
    const next=state.layout.filter(x=>x!==source);
    next.splice(next.indexOf(name),0,source);
    state.layout=next;state.designDirty=true;layoutControls();
   });
   row.append(
    button("↑",()=>{if(i>0){[state.layout[i-1],state.layout[i]]=[state.layout[i],state.layout[i-1]];state.designDirty=true;}layoutControls();}),
    button("↓",()=>{if(i<state.layout.length-1){[state.layout[i+1],state.layout[i]]=[state.layout[i],state.layout[i+1]];state.designDirty=true;}layoutControls();})
   );
  }else{
   row.classList.add("design-block-hidden");
   row.append(el("small","Hidden"));
  }
  root.append(row);
 }
 previewDesign();
}
function previewDesign(){
 const root=$("designPreview");root.replaceChildren();
 const e={...state.entry,theme_id:$("dTheme").value,accent:$("dOverrideAccent").checked?$("dAccent").value:null};
 setTheme(root,e);
 const header=el("header",undefined,"preview-header");
 header.append(el("span",displayType(e.type)+" · "+e.status,"preview-kicker"),el("h3",e.title));
 header.append(el("p",e.summary||"No summary yet.","preview-summary"));
 root.append(header);
 if(!state.layout.length)root.append(el("p","Choose at least one section to display.","preview-empty"));
 for(const name of state.layout){
  const area=el("section",undefined,"preview-section");
  area.append(el("h4",BLOCK_LABELS[name]));
  let value;
  if(name==="body")value=e.body?e.body.replace(/^#+\s*/gm,"").replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g,"$2").slice(0,460):"An article body will appear here.";
  if(name==="facts")value=displayType(e.type)+" · "+e.status+" · "+when(e);
  if(name==="relationships")value=state.relations.length+" recorded connection(s)";
  if(name==="backlinks")value=state.incoming.length+" incoming references, "+state.outgoing.length+" outgoing";
  if(name==="timeline")value="Events related to this entry are drawn from the shared chronology.";
  if(name==="map")value=e.lat!==null&&e.lon!==null?"Mapped at "+e.lat+", "+e.lon:"No verified location coordinates";
  if(name==="gallery")value=state.media.length+" attached image(s)";
  if(name==="sources")value="Editorial status: "+e.status+" · source and research records";
  area.append(el("p",value,"preview-copy"));root.append(area);
 }
}
async function saveDesign(){
 if(!state.layout.length)return notice("Select at least one visible section before saving.",true);
 try{
  state.entry=await api(q("/api/entity",{world_id:wid(),id:state.entry.id}),"PATCH",{
   theme_id:$("dTheme").value,
   accent:$("dOverrideAccent").checked?$("dAccent").value:null,
   layout:state.layout
  });
  state.designDirty=false;
  await refresh();await context();render();notice("Page design saved.");
 }catch(err){notice(err.message,true);}
}
async function network(){
 if(!state.world)return;
 const world=wid();
 try{
  const rels=await api(q("/api/relations",{world_id:world}));
  if(world!==wid()||state.panel!=="network")return;
  $("networkSummary").textContent=rels.length+" "+(rels.length===1?"relationship":"relationships");
  const byType=new Map(),byEntity=new Map();
  for(const r of rels){
   byType.set(r.predicate,(byType.get(r.predicate)||0)+1);
   for(const id of [r.source_id,r.target_id])byEntity.set(id,(byEntity.get(id)||0)+1);
  }
  const types=$("networkPredicates");types.replaceChildren();
  const all=button("All connections · "+rels.length,()=>{state.networkFilter="all";network();},"network-filter"+(state.networkFilter==="all"?" active":""));types.append(all);
  for(const [type,count] of [...byType].sort((a,b)=>b[1]-a[1])){
   const b=button(type.replaceAll("_"," ")+" · "+count,()=>{state.networkFilter=type;network();},"network-filter"+(state.networkFilter===type?" active":""));types.append(b);
  }
  const records=$("networkEntries");records.replaceChildren();
  for(const [id,count] of [...byEntity].sort((a,b)=>b[1]-a[1]).slice(0,14)){
   const e=byId(id);if(!e)continue;
   const row=button("",()=>open(e.id),"network-record");row.append(el("span",e.title),el("small",count+" connections"));records.append(row);
  }
  if(!byEntity.size)records.append(el("p","Link two entries to begin building the relationship graph.","empty-state"));
  const list=$("networkRelations");list.replaceChildren();
  const selected=rels.filter(x=>state.networkFilter==="all"||x.predicate===state.networkFilter);
  for(const r of selected.slice(0,250)){
   const a=byId(r.source_id),b=byId(r.target_id);if(!a||!b)continue;
   const row=el("div",undefined,"network-row");
   row.append(linkTo(a),el("span",r.predicate.replaceAll("_"," ")+" → ","network-predicate"),linkTo(b));
   const detail=el("span",r.status+(r.start_year!==null||r.end_year!==null?" · "+when(r):""),"network-period");row.append(detail);
   list.append(row);
  }
  if(selected.length>250)list.append(el("p","Showing the first 250 records. Refine by relationship type.","muted"));
  if(!selected.length)list.append(el("p","No relationships in this category.","empty-state"));
 }catch(e){notice("Connections unavailable: "+e.message,true);}
}
async function boardsWorkspace(){
 if(!state.world)return;
 const world=wid();
 try{
  const boards=await api(q("/api/boards",{world_id:world}));
  if(wid()!==world)return;
  state.boards=boards;
  renderBoardList();
  const selected=boards.find(b=>b.id===state.board?.board?.id);
  if(selected)await loadBoard(selected.id);
  else{state.board=null;$("boardEditor").hidden=true;$("boardEmpty").hidden=false;}
 }catch(error){notice("Moodboards unavailable: "+error.message,true);}
}
function renderBoardList(){
 const list=$("boardList");list.replaceChildren();
 $("boardCount").textContent=String(state.boards.length);
 for(const board of state.boards){
  const b=button("",()=>loadBoard(board.id),"board-entry"+(state.board?.board?.id===board.id?" active":""));
  const thumb=el("span",undefined,"board-entry-preview");
  if(board.preview_media_id){
   const img=el("img");img.src="/media/"+wid()+"/"+board.preview_media_id+"-preview";
   img.alt="";img.loading="lazy";thumb.append(img);
  }else{
   thumb.style.backgroundColor=board.preview_color||"var(--raised)";
   thumb.append(el("span",board.preview_color?"COLOR STUDY":"VISUAL STUDY"));
  }
  b.append(thumb,el("strong",board.title),el("small",board.item_count+" items"+(board.entity_title?" · "+board.entity_title:"")));
  list.append(b);
 }
}
async function loadBoard(id){
 const world=wid();
 try{
  const data=await api(q("/api/board",{world_id:world,id}));
  if(world!==wid())return;
  state.board=data;
  $("boardEditor").hidden=false;$("boardEmpty").hidden=true;
  $("boardTitle").textContent=data.board.title;
  $("boardDescription").textContent=data.board.description||"Compose visual references, notes and canon links.";
  renderBoardList();renderBoardItems();
 }catch(error){notice(error.message,true);}
}
function newBoard(){
 if(!state.world)return;
 const select=$("boardNewEntry");select.replaceChildren(new Option("General world board — not linked to an entry",""));
 for(const entry of state.entries)select.add(new Option(entry.title+" · "+displayType(entry.type),entry.id));
 if(state.entry)select.value=state.entry.id;
 $("boardNewTitle").value="";
 $("boardNewDescription").value="";
 $("boardCreateDialog").showModal();
 $("boardNewTitle").focus();
}
async function submitBoard(event){
 event.preventDefault();
 const title=$("boardNewTitle").value.trim();
 if(!title)return;
 const description=$("boardNewDescription").value;
 const entity_id=$("boardNewEntry").value||null;
 try{
  const created=await api(q("/api/boards",{world_id:wid()}),"POST",{title,description,entity_id});
  $("boardCreateDialog").close();
  await boardsWorkspace();await loadBoard(created.board.id);
  notice("Moodboard created.");
 }catch(error){notice("Unable to create board: "+error.message,true);}
}
async function boardDetails(){
 if(!state.board)return;
 const current=state.board.board;
 const title=prompt("Moodboard title",current.title);if(title===null)return;
 const description=prompt("Moodboard description",current.description);if(description===null)return;
 try{
  const data=await api(q("/api/board",{world_id:wid(),id:current.id}),"PATCH",{title,description});
  state.board=data;await boardsWorkspace();notice("Board details saved.");
 }catch(error){notice(error.message,true);}
}
async function deleteBoard(){
 if(!state.board)return;
 if(!confirm("Delete the moodboard “"+state.board.board.title+"” and its placements? Linked source images and encyclopedia entries will be kept."))return;
 try{await api(q("/api/board",{world_id:wid(),id:state.board.board.id}),"DELETE");
 state.board=null;await boardsWorkspace();notice("Moodboard deleted; source assets preserved.");
 }catch(error){notice(error.message,true);}
}
async function placeBoardCard(kind,reference=null){
 if(!state.board)return;
 const count=state.board.items.length;
 const item={kind,content:reference?.content??"",media_id:reference?.media_id??null,
             entity_id:reference?.entity_id??null,color:reference?.color??null,
             x:35+(count%4)*255,y:35+Math.floor(count/4)*225,w:230,h:185,z:count+1};
 try{
  state.board=await api(q("/api/board-item",{world_id:wid(),board_id:state.board.board.id}),"POST",item);
  renderBoardItems();notice("Reference placed on the moodboard.");
 }catch(error){notice("Unable to add card: "+error.message,true);}
}
async function boardAdd(kind){
 if(!state.board)return;
 if(kind==="image"||kind==="entry"){await openBoardPicker(kind);return;}
 if(kind==="note"){
  const content=prompt("Visual note, research question or creative direction","");
  if(content!==null)await placeBoardCard("note",{content});
 }else if(kind==="swatch"){
  const color=prompt("Color hex value","#9cb6a0");
  if(color===null)return;
  const content=prompt("Meaning or purpose of this color","")??"";
  await placeBoardCard("swatch",{color,content});
 }
}
let boardPickerKind="image",boardPickerAssets=[];
async function openBoardPicker(kind){
 boardPickerKind=kind;
 $("boardPickerHeading").textContent=kind==="image"?"Choose an image":"Link a world entry";
 $("boardPickerSearch").value="";
 try{
  boardPickerAssets=kind==="image"?await api(q("/api/media",{world_id:wid()})):state.entries;
  $("boardPickerDialog").showModal();
  renderBoardPicker();
  $("boardPickerSearch").focus();
 }catch(error){notice("Unable to load references: "+error.message,true);}
}
function renderBoardPicker(){
 const root=$("boardPickerResults");root.replaceChildren();
 const search=$("boardPickerSearch").value.toLowerCase().trim();
 const selected=boardPickerAssets.filter(item=>[item.title,item.summary,item.credit,item.alt,item.type]
  .some(value=>String(value||"").toLowerCase().includes(search)));
 for(const item of selected){
  const card=button("",
   async()=>{
    $("boardPickerDialog").close();
    if(boardPickerKind==="image")await placeBoardCard("image",{media_id:item.id,content:item.title});
    else await placeBoardCard("entry",{entity_id:item.id});
   },"mood-picker-tile");
  if(boardPickerKind==="image"){
   const image=el("img");image.src="/media/"+wid()+"/"+item.id+"-preview";
   image.alt=item.alt||item.title;image.loading="lazy";card.append(image);
  }else{
   card.append(el("span",displayType(item.type),"mood-picker-category"));
  }
  card.append(el("strong",item.title));
  if(boardPickerKind==="entry"&&item.summary)card.append(el("small",item.summary.slice(0,90)));
  root.append(card);
 }
 if(!selected.length)root.append(el("p",boardPickerKind==="image"?
  "No images found. Use Upload image to add a new asset.":"No records match the search.","muted"));
}
async function uploadBoardImage(){
 const file=$("boardImageFile").files?.[0];
 if(!file)return;
 try{
  if(file.size>12000000||file.size===0)throw Error("Image must be between 1 byte and 12 MB.");
  if(!["image/jpeg","image/png","image/webp"].includes(file.type))throw Error("Use PNG, JPEG or WebP.");
  const response=await fetch(q("/api/upload",{world_id:wid()}),{
   method:"POST",headers:{"X-World-Bible":"1","X-File-Name":encodeURIComponent(file.name),
   "Content-Type":"application/octet-stream"},body:file
  });
  const result=await response.json();
  if(!response.ok)throw Error(result.error||"Upload failed");
  await placeBoardCard("image",{media_id:result.id,content:result.title||file.name});
 }catch(error){notice("Upload failed: "+error.message,true);}
 finally{$("boardImageFile").value="";}
}
function renderBoardItems(){
 const canvas=$("boardCanvas");canvas.replaceChildren();
 if(!state.board)return;
 const items=state.board.items;
 canvas.style.width="1400px";canvas.style.height="980px";
 canvas.style.transformOrigin="top left";
 canvas.style.transform="scale("+state.boardZoom+")";
 $("boardZoomValue").textContent=Math.round(state.boardZoom*100)+"%";
 const viewport=$("boardViewport");viewport.style.setProperty("--board-scale",state.boardZoom);
 for(const item of items){
  const card=el("article",undefined,"mood-card mood-"+item.kind);
  card.style.left=item.x+"px";card.style.top=item.y+"px";
  card.style.width=item.w+"px";card.style.height=item.h+"px";card.style.zIndex=item.z;
  const header=el("div",undefined,"mood-card-header"),kindName=el("strong",item.kind,"mood-kind");
  header.append(el("span","⠿","mood-grip"),kindName);
  const edit=button("Edit",()=>editBoardCard(item.id),"mood-card-action");
  const front=button("↑",()=>updateBoardCard(item.id,{z:Math.min(100000,Math.max(0,...state.board.items.map(x=>x.z))+1)}),"mood-card-action");
  const remove=button("×",()=>removeBoardCard(item.id),"mood-card-action");
  remove.setAttribute("aria-label","Remove moodboard card");
  header.append(edit,front,remove);card.append(header);
  const body=el("div",undefined,"mood-card-body");
  if(item.kind==="image"&&item.media_id){
   const img=el("img");img.src="/media/"+wid()+"/"+item.media_id+"-preview";img.alt=item.media_title||item.content;
   img.loading="lazy";body.append(img);
   if(item.content)body.append(el("span",item.content,"mood-caption"));
   if(item.media_credit)body.append(el("small","Credit: "+item.media_credit,"mood-credit"));
  }else if(item.kind==="entry"){
   const e=byId(item.entity_id);
   body.append(el("span",e?displayType(e.type):"Entry","mood-entry-type"));
   body.append(el("strong",e?.title||"Entry no longer exists"));
   if(e)body.append(button("Open entry",()=>open(e.id),"mood-open"));
  }else if(item.kind==="swatch"){
   const sample=el("div",undefined,"mood-swatch");sample.style.backgroundColor=item.color||"#aaa";body.append(sample);
   body.append(el("span",(item.color||"")+" "+item.content,"mood-caption"));
  }else body.append(el("p",item.content||"A visual research note"));
  card.append(body);
  const resize=el("button","↘","mood-resize");
  resize.title="Resize card";
  resize.setAttribute("aria-label","Drag to resize card");
  resize.onpointerdown=e=>{
   e.preventDefault();e.stopPropagation();
   const startX=e.clientX,startY=e.clientY,w=item.w,h=item.h;
   resize.setPointerCapture(e.pointerId);
   const move=event=>{
    const width=Math.max(120,Math.min(1200,Math.round(w+(event.clientX-startX)/state.boardZoom)));
    const height=Math.max(95,Math.min(1200,Math.round(h+(event.clientY-startY)/state.boardZoom)));
    card.style.width=width+"px";card.style.height=height+"px";
   };
   const end=async event=>{
    resize.removeEventListener("pointermove",move);
    resize.removeEventListener("pointerup",end);
    resize.removeEventListener("pointercancel",end);
    if(event.type==="pointercancel"){
     card.style.width=w+"px";card.style.height=h+"px";return;
    }
    const width=Math.max(120,Math.min(1200,Math.round(w+(event.clientX-startX)/state.boardZoom)));
    const height=Math.max(95,Math.min(1200,Math.round(h+(event.clientY-startY)/state.boardZoom)));
    if(width!==w||height!==h)await updateBoardCard(item.id,{w:width,h:height});
   };
   resize.addEventListener("pointermove",move);
   resize.addEventListener("pointerup",end);
   resize.addEventListener("pointercancel",end);
  };
  card.append(resize);
  header.addEventListener("pointerdown",e=>{
   if(e.target.closest("button"))return;
   e.preventDefault();
   const x=e.clientX,y=e.clientY,startX=item.x,startY=item.y;
   header.setPointerCapture(e.pointerId);card.classList.add("moving");
   const move=event=>{
    const dx=(event.clientX-x)/state.boardZoom,dy=(event.clientY-y)/state.boardZoom;
    card.style.left=Math.round(startX+dx)+"px";card.style.top=Math.round(startY+dy)+"px";
   };
   const finish=async event=>{
    header.removeEventListener("pointermove",move);
    header.removeEventListener("pointerup",finish);
    header.removeEventListener("pointercancel",finish);
    card.classList.remove("moving");
    const dx=(event.clientX-x)/state.boardZoom,dy=(event.clientY-y)/state.boardZoom;
    const next={x:Math.max(-20000,Math.min(20000,Math.round(startX+dx))),
                y:Math.max(-20000,Math.min(20000,Math.round(startY+dy)))};
    if(event.type!=="pointercancel"&&(next.x!==item.x||next.y!==item.y))await updateBoardCard(item.id,next);
    else{card.style.left=item.x+"px";card.style.top=item.y+"px";}
   };
   header.addEventListener("pointermove",move);
   header.addEventListener("pointerup",finish);
   header.addEventListener("pointercancel",finish);
  });
  canvas.append(card);
 }
 if(!items.length)canvas.append(el("p","Add your first image, note, linked entry or color to begin composing.","mood-start"));
}
async function updateBoardCard(id,data){
 if(!state.board)return;
 try{
  const boardId=state.board.board.id;
  state.board=await api(q("/api/board-item",{world_id:wid(),board_id:boardId,id}),"PATCH",data);
  renderBoardItems();
 }catch(error){notice("Card not saved: "+error.message,true);await loadBoard(state.board.board.id);}
}
let editingBoardCard=null;
function editBoardCard(id){
 const item=state.board?.items.find(x=>x.id===id);if(!item)return;
 editingBoardCard=item.id;
 $("boardCardHeading").textContent="Edit "+item.kind+" card";
 $("boardCardText").value=item.content||"";
 $("boardCardColorField").hidden=item.kind!=="swatch";
 $("boardCardColor").value=item.color||"#9cb6a0";
 $("boardCardWidth").value=item.w;
 $("boardCardHeight").value=item.h;
 $("boardCardDialog").showModal();
 $("boardCardText").focus();
}
async function saveBoardCard(event){
 event.preventDefault();
 if(!editingBoardCard)return;
 const item=state.board?.items.find(x=>x.id===editingBoardCard);
 if(!item)return $("boardCardDialog").close();
 const data={
  content:$("boardCardText").value,
  w:Number($("boardCardWidth").value),
  h:Number($("boardCardHeight").value)
 };
 if(item.kind==="swatch")data.color=$("boardCardColor").value;
 await updateBoardCard(item.id,data);
 $("boardCardDialog").close();
 editingBoardCard=null;
}
async function removeBoardCard(id){
 if(!state.board||!confirm("Remove this placement from the board? Source records and media remain unchanged."))return;
 try{
  state.board=await api(q("/api/board-item",{world_id:wid(),board_id:state.board.board.id,id}),"DELETE");
  renderBoardItems();
 }catch(error){notice(error.message,true);}
}
async function mediaWorkspace(){
 if(!state.world)return;
 const world=wid();
 try{
  const [all,uses]=await Promise.all([api(q("/api/media",{world_id:world})),api(q("/api/media-uses",{world_id:world}))]);
  if(world!==wid()||state.panel!=="media")return;
  state.globalMedia=all;state.mediaUses=uses;
  renderMediaGrid();
 }catch(e){notice("Media library unavailable: "+e.message,true);}
}
function renderMediaGrid(){
 const search=$("mediaSearch").value.toLowerCase().trim(),filter=$("mediaFilter").value;
 const root=$("globalMediaGrid");root.replaceChildren();
 const media=state.globalMedia.filter(m=>{
  const uses=state.mediaUses.filter(u=>u.media_id===m.id);
  return (filter==="all"||(filter==="used"?uses.length>0:uses.length===0))&&
   (!search||[m.title,m.filename,m.credit,m.alt].some(t=>String(t||"").toLowerCase().includes(search)));
 });
 $("mediaSummary").textContent=state.globalMedia.length+" "+(state.globalMedia.length===1?"image":"images");
 for(const m of media){
  const card=el("article",undefined,"global-media-card"),img=el("img");
  img.src="/media/"+wid()+"/"+m.id+"-preview";img.alt=m.alt||m.title;img.loading="lazy";
  const info=el("div",undefined,"global-media-info");info.append(el("h3",m.title),el("p",m.credit||"No credit recorded","muted"));
  const refs=state.mediaUses.filter(u=>u.media_id===m.id);
  info.append(el("small",refs.length+" "+(refs.length===1?"placement":"placements")));
  for(const u of refs.slice(0,7)){
   const e=byId(u.entity_id);if(e)info.append(linkTo(e));
  }
  card.append(img,info);root.append(card);
 }
 if(!media.length)root.append(el("p","No images match these filters. Open an entry → Explore to upload or attach images.","empty-state"));
}
function timeline(){timelineLoad().catch(err=>notice("Timeline failed: "+err.message,true));}
async function timelineLoad(){
 if(!state.world)return;
 const scope=$("timelineScope"),old=scope.value;
 optionList(scope,state.entries,"Entire world");
 if(byId(old))scope.value=old;
 const selected=scope.value,world=wid();
 const related=selected?await api(q("/api/relations",{world_id:world,entity_id:selected})):[];
 if(world!==wid()||scope.value!==selected)return;
 const root=$("timelineList");root.replaceChildren();
 const year=num($("timelineYear").value)??50;
 const list=state.entries.filter(e=>
   e.type==="event"&&($("timelineAll").checked||active(e,year))&&
   (!selected||e.id===selected||related.some(r=>
     [r.source_id,r.target_id].includes(e.id)&&[r.source_id,r.target_id].includes(selected))))
   .sort((a,b)=>(a.start_year??999999)-(b.start_year??999999));
 for(const e of list){
   const row=el("div",undefined,"timeline-event");
   row.append(el("time",when(e)),linkTo(e),el("p",e.summary||"No summary","muted"));
   root.append(row);
 }
 if(!list.length)root.append(el("p","No matching historical events.","muted"));
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
 const frame=$("map");
 frame.addEventListener("pointerdown",e=>{
  if(e.target.closest("button"))return;
  map.drag={x:e.clientX,y:e.clientY,p:project(map.lon,map.lat,map.zoom),dx:0,dy:0};
  frame.setPointerCapture(e.pointerId);
 });
 frame.addEventListener("pointermove",e=>{
  if(!map.drag)return;
  map.drag.dx=e.clientX-map.drag.x;map.drag.dy=e.clientY-map.drag.y;
  for(const layer of ["tiles","pins"])$(layer).style.transform="translate("+map.drag.dx+"px,"+map.drag.dy+"px)";
 });
 function endDrag(){
  if(!map.drag)return;
  const d=map.drag;map.drag=null;
  const pt=inverse(d.p.x-d.dx,d.p.y-d.dy,map.zoom);
  map.lon=Math.max(-180,Math.min(180,pt.lon));map.lat=Math.max(-85,Math.min(85,pt.lat));
  for(const layer of ["tiles","pins"])$(layer).style.transform="";
  atlas(true);
 }
 for(const event of ["pointerup","pointercancel"])frame.addEventListener(event,endDrag);
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
 state.entry=null;state.published=false;state.relations=[];state.media=[];state.incoming=[];state.outgoing=[];
 state.globalMedia=[];state.mediaUses=[];state.networkFilter="all";state.boards=[];state.board=null;
 state.v2.metadata=null;
 $("search").value="";$("typeFilter").value="";$("v2CategoryFilter").value="";$("v2TagFilter").value="";$("mediaSearch").value="";$("mediaFilter").value="all";
 localStorage.setItem("wb-world",id);$("worldDescription").textContent=state.world.description||"";
 await refresh();panel("home");render();
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
  renderHome();workspaceChrome();
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
 $("publishToggle").onclick=togglePublication;
 $("v2SaveMetadata").onclick=saveV2Metadata;
 $("v2AddCategory").onclick=()=>createV2Classification("category");
 $("v2AddTag").onclick=()=>createV2Classification("tag");
 $("v2MetadataEditor").addEventListener("input",event=>event.stopPropagation());
 $("v2CategoryFilter").onchange=renderList;
 $("v2TagFilter").onchange=renderList;
 $("newBoard").onclick=newBoard;
 $("boardEmptyCreate").onclick=newBoard;
 $("boardRename").onclick=boardDetails;
 $("boardDelete").onclick=deleteBoard;
 $("boardAddNote").onclick=()=>boardAdd("note");
 $("boardAddImage").onclick=()=>boardAdd("image");
 $("boardUpload").onclick=()=>$("boardImageFile").click();
 $("boardImageFile").onchange=uploadBoardImage;
 $("boardPickerSearch").oninput=renderBoardPicker;
 $("boardPickerClose").onclick=()=>$("boardPickerDialog").close();
 $("boardCardForm").onsubmit=saveBoardCard;
 $("boardCardCancel").onclick=()=>$("boardCardDialog").close();
 $("createEntryBoard").onclick=()=>{panel("boards");newBoard();};
 $("boardCreateForm").onsubmit=submitBoard;
 $("boardCreateCancel").onclick=()=>$("boardCreateDialog").close();
 $("boardAddEntry").onclick=()=>boardAdd("entry");
 $("boardAddSwatch").onclick=()=>boardAdd("swatch");
 $("boardZoom").oninput=()=>{state.boardZoom=Number($("boardZoom").value)/100;renderBoardItems();};
 $("homeNew").onclick=createEntry;
 $("homeBrowse").onclick=()=>panel("article");
 $("homeToAtlas").onclick=()=>panel("atlas");
 $("homeToTime").onclick=()=>panel("timeline");
 $("homeToNetwork").onclick=()=>panel("network");
 $("homeToMedia").onclick=()=>panel("media");
 $("homeToBoards").onclick=()=>panel("boards");
 $("mediaSearch").oninput=renderMediaGrid;
 $("mediaFilter").onchange=renderMediaGrid;
  $("world").onchange=e=>switchWorld(e.target.value);$("worldSettings").onclick=editWorld;$("cancelCreate").onclick=()=>$("createDialog").close();$("createForm").onsubmit=e=>{e.preventDefault();submitCreate();};$("importWorld").onclick=()=>$("importFile").click();$("importFile").onchange=importWorld;$("addWorld").onclick=createWorld;$("newEntry").onclick=createEntry;$("welcomeNew").onclick=createEntry;$("export").onclick=exportWorld;
 $("welcomeTimeline").onclick=()=>panel("timeline");$("welcomeAtlas").onclick=()=>panel("atlas");
 document.addEventListener("keydown",e=>{
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){
   e.preventDefault();$("search").focus();$("search").select();return;
  }
  if(e.altKey&&!e.ctrlKey&&!e.metaKey&&/^[1-7]$/.test(e.key)){
   e.preventDefault();const names=["home","article","atlas","timeline","network","media","boards"];
   panel(names[Number(e.key)-1]);
  }
 });
  $("search").oninput=renderList;$("typeFilter").onchange=renderList;$("globalYear").onchange=()=>setHistoricalYear($("globalYear").value);
 document.querySelectorAll("[data-panel]").forEach(b=>b.onclick=()=>panel(b.dataset.panel));
 document.querySelectorAll("[data-mode]").forEach(b=>b.onclick=()=>mode(b.dataset.mode));
 $("appearance").value=localStorage.getItem("wb-mode")||"dark";document.body.dataset.appearance=$("appearance").value;
 $("appearance").onchange=()=>{document.body.dataset.appearance=$("appearance").value;localStorage.setItem("wb-mode",$("appearance").value);if(state.mode==="read"&&state.entry)read();if(state.mode==="design"&&state.entry)previewDesign();};
 $("createType").onchange=updateCreateHint;
 $("eType").onchange=()=>{$("editCustomTypeField").hidden=$("eType").value!=="custom";};
 $("eType").addEventListener("change",()=>{if(state.v2.metadata)renderV2Editor();});
 $("relType").onchange=()=>{$("relCustom").hidden=$("relType").value!=="custom";};
 $("editForm").onsubmit=e=>{e.preventDefault();save();};$("editForm").oninput=()=>dirty(true);
 $("deleteEntry").onclick=remove;$("findLinks").onclick=discover;$("addRelation").onclick=addRelation;
 $("uploadImage").onclick=uploadImage;$("attachImage").onclick=attachImage;
 $("dTheme").onchange=()=>{state.designDirty=true;previewDesign();};
 $("dOverrideAccent").onchange=()=>{$("dAccent").disabled=!$("dOverrideAccent").checked;state.designDirty=true;previewDesign();};
 $("dAccent").oninput=()=>{state.designDirty=true;previewDesign();};
 $("saveDesign").onclick=saveDesign;
 $("resetDesign").onclick=()=>{state.layout=[...blocks];state.designDirty=true;layoutControls();};
 $("timelineScope").onchange=timeline;$("timelineAll").onchange=timeline;
 setupMap();window.addEventListener("beforeunload",e=>{if(state.dirty||state.designDirty){e.preventDefault();e.returnValue="";}});
}
async function init(){wire();try{await worlds();panel("home");notice("World Bible Studio ready.");}catch(err){notice("Server error: "+err.message,true);}}
init();
