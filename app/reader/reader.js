"use strict";
// Reader uses published-only API endpoints. It never requests the Studio's full entity store.
const $=id=>document.getElementById(id);
const state={worlds:[],world:null,entries:[],relations:[],current:null,media:[],related:[],incoming:[],outgoing:[],font:17,appearance:"dark",staticBundle:null,map:{lon:0,lat:25,zoom:2,drag:null}};
const CATEGORY={
 place:{label:"Places & geography",short:"Places",symbol:"◇",description:"Settlements, landscapes and regions"},
 organization:{label:"Factions & societies",short:"Societies",symbol:"⚑",description:"Institutions, governments and communities"},
 person:{label:"People & lives",short:"People",symbol:"♙",description:"People and their connections"},
 family:{label:"Families & kinship",short:"Families",symbol:"⌘",description:"Families, households and ancestry"},
 event:{label:"History & events",short:"History",symbol:"◷",description:"Events and historical turning points"},
 subject:{label:"Culture & knowledge",short:"Subjects",symbol:"✦",description:"Ideas, traditions and general subjects"},
 source:{label:"Documents & sources",short:"Sources",symbol:"▤",description:"Sources, archives and material evidence"},
 object:{label:"Artifacts & material life",short:"Artifacts",symbol:"▥",description:"Objects, technology and resources"}
};
const category=e=>CATEGORY[e.type]||{label:humanize(e.type),short:humanize(e.type),symbol:"◇",description:"Related encyclopedia subjects"};
const humanize=x=>String(x||"").replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase());
const escapeHTML=x=>String(x??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const node=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n};
const link=(title,href,cls)=>{const a=node("a",title,cls);a.href=href;return a};
const url=(path,args={})=>path+"?"+new URLSearchParams(args);
const currentId=()=>state.world?.id;
const byId=id=>state.entries.find(e=>e.id===id);
const mediaUrl=(id,preview=true)=>{
 if(state.staticBundle){
  const asset=state.staticBundle.assets[id];
  if(!asset)return "";
  return "media/"+encodeURIComponent(id)+(preview?"-preview.webp":asset.extension);
 }
 return "/media/"+encodeURIComponent(currentId())+"/"+encodeURIComponent(id)+(preview?"-preview":"");
};
const readableDate=e=>e.start_year==null&&e.end_year==null?"Date not recorded":e.start_year===e.end_year?"Year "+e.start_year:"Year "+(e.start_year??"unknown")+" – "+(e.end_year??"ongoing");
const activeAt=(e,year)=>(e.start_year===null||e.start_year<=year)&&(e.end_year===null||e.end_year>=year);
async function get(path){
 if(state.staticBundle)return staticRequest(path);
 const response=await fetch(path);
 const obj=await response.json();
 if(!response.ok)throw Error(obj.error||"Reader request failed");
 return obj;
}
function staticRequest(path){
 const req=new URL(path,location.origin),q=req.searchParams,b=state.staticBundle;
 if(req.pathname==="/api/public/worlds")return Promise.resolve([b.world]);
 if(q.get("world_id")!==b.world.id)throw Error("Unknown published world");
 if(req.pathname==="/api/public/entities"){
  const type=q.get("type"),search=(q.get("search")||"").toLowerCase();
  return Promise.resolve(b.entities.filter(e=>(!type||e.type===type)&&
    (!search||[e.title,e.summary,e.body,...e.aliases].some(v=>String(v).toLowerCase().includes(search)))));
 }
 if(req.pathname==="/api/public/media")return Promise.resolve(b.media_by_entity[q.get("entity_id")]||[]);
 if(req.pathname==="/api/public/relations"){
  const id=q.get("entity_id");
  return Promise.resolve(b.relations.filter(r=>!id||r.source_id===id||r.target_id===id));
 }
 if(req.pathname==="/api/public/backlinks"||req.pathname==="/api/public/outgoing"){
  const id=q.get("entity_id");
  return Promise.resolve((b.links[id]?.[req.pathname.endsWith("backlinks")?"incoming":"outgoing"])||[]);
 }
 throw Error("Unknown reader publication resource");
}
function showRoute(name){for(const id of ["Home","Browse","Article","Atlas","History","Empty"])$("reader"+id).hidden=id.toLowerCase()!==name;document.querySelectorAll("[data-route]").forEach(a=>{const on=(name==="article"&&a.dataset.route==="browse")||a.dataset.route===name;a.classList.toggle("active",on);if(on)a.setAttribute("aria-current","page");else a.removeAttribute("aria-current");});}
function setTitle(value){document.title=value+" · "+(state.world?.name||"World Bible");}
function syncWorld(){
 const name=state.world?.name||"World Bible";
 $("brandWorld").textContent=name;$("footerBrand").textContent=name;
 $("coverTitle").textContent=name;
 $("coverSummary").textContent=state.world?.description||"Explore the lives, geography, communities and history of a richly connected world.";
 $("coverCount").textContent=state.entries.length+" published articles";
}
function renderCard(e){
 const a=link("", "#/article/"+encodeURIComponent(e.id),"article-card");
 const cover=node("div",undefined,"article-cover");
 if(e.hero_media_id){
  const image=node("img");image.src=mediaUrl(e.hero_media_id);image.alt="";image.loading="lazy";cover.append(image);
 }else cover.append(node("span",category(e).symbol));
 const info=node("div",undefined,"article-info");
 info.append(node("span",category(e).short,"article-type"),node("h3",e.title,"article-title"),
  node("p",e.summary||"Explore this entry and its connections to the wider world.","article-desc"),
  node("span","Read article →","article-open"));
 a.append(cover,info);return a;
}
function renderHome(){
 syncWorld();
 const counts=new Map();
 for(const e of state.entries)counts.set(e.type,(counts.get(e.type)||0)+1);
 const ordered=[...counts].sort((a,b)=>b[1]-a[1]);
 const grid=$("categoryCards");grid.replaceChildren();
 for(const [type,count] of ordered){
  const cfg=category({type});
  const card=link("","#/browse/"+encodeURIComponent(type),"category-card");
  card.append(node("span",cfg.symbol,"category-symbol"),node("strong",cfg.label,"category-title"),
   node("small",cfg.description+" · "+count+" "+(count===1?"article":"articles")));
  grid.append(card);
 }
 if(!ordered.length)grid.append(node("p","Published categories will appear here.","empty-published"));
 const frontHero=state.entries.find(e=>e.hero_media_id);
 $("readerHome").style.setProperty("--cover-art",frontHero?'url("'+mediaUrl(frontHero.hero_media_id)+'")':"none");
  const featured=$("featuredCards");featured.replaceChildren();
 const priority={"place":0,"person":1,"organization":2,"event":3};
 const shortlist=[...state.entries].sort((a,b)=>(priority[a.type]??9)-(priority[b.type]??9)||a.title.localeCompare(b.title)).slice(0,6);
 for(const e of shortlist)featured.append(renderCard(e));
 if(!shortlist.length)featured.append(node("p","Articles are being prepared for publication. Explore the atlas and chronology as they become available.","empty-published"));
}
function renderBrowse(type=""){
 showRoute("browse");setTitle(type?category({type}).label:"Encyclopedia");
 const input=$("browseSearch"),select=$("browseType");
 const previously=select.value;
 select.replaceChildren(new Option("All categories",""));
 for(const t of [...new Set(state.entries.map(e=>e.type))].sort())select.add(new Option(category({type:t}).label,t));
 select.value=type||previously;
 const fn=()=>{
  const needle=input.value.toLowerCase().trim(),t=select.value;
  const list=state.entries.filter(e=>(!t||e.type===t)&&
   (!needle||[e.title,e.summary,...e.aliases,e.body].some(x=>String(x||"").toLowerCase().includes(needle))));
  $("browseCount").textContent=list.length+" "+(list.length===1?"article":"articles");
  const root=$("browseCards");root.replaceChildren();
  for(const e of list)root.append(renderCard(e));
  if(!list.length)root.append(node("p","No published articles match that search.","empty-published"));
 };
 input.oninput=fn;select.onchange=fn;fn();
}
function markup(src){
 let code=false,inList=false;const out=[];
 const inline=text=>escapeHTML(text).replace(/\[\[([a-zA-Z0-9:-]{3,100})(?:\|([^\]\n]{1,180}))?\]\]/g,(_,id,custom)=>{
  const target=byId(id);
  if(!target)return custom?escapeHTML(custom):"";
  return '<a href="#/article/'+encodeURIComponent(id)+'">'+escapeHTML(custom||target.title)+"</a>";
 }).replace(/\*\*([^*\n]+)\*\*/g,"<strong>$1</strong>")
 .replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g,"<em>$1</em>");
 for(const line of String(src||"").split(/\r?\n/)){
  if(line.startsWith("&#96;&#96;&#96;")||line.startsWith("\x60\x60\x60")){
   if(inList){out.push("</ul>");inList=false;}
   out.push(code?"</code></pre>":"<pre><code>");code=!code;continue;
  }
  if(code){out.push(escapeHTML(line)+"\n");continue;}
  if(/^[-*]\s+/.test(line)){if(!inList){out.push("<ul>");inList=true;}out.push("<li>"+inline(line.slice(2))+"</li>");continue;}
  if(inList){out.push("</ul>");inList=false;}
  const h=line.match(/^(#{1,4})\s+(.+)$/);
  if(h){const n=Math.min(5,h[1].length+1),id="part-"+out.length;out.push("<h"+n+' id="'+id+'">'+inline(h[2])+"</h"+n+">");continue;}
  if(line.startsWith("> ")){out.push("<blockquote>"+inline(line.slice(2))+"</blockquote>");continue;}
  if(/^---+$/.test(line)){out.push("<hr>");continue;}
  if(!line.trim())continue;
  out.push("<p>"+inline(line)+"</p>");
 }
 if(inList)out.push("</ul>");
 if(code)out.push("</code></pre>");
 return out.join("\n");
}
function makeMedia(m){
 const figure=node("figure"),img=node("img");
 img.loading="lazy";img.src=mediaUrl(m.media_id);
 img.alt=m.alt||m.title;
 figure.append(img,node("figcaption",m.caption||m.credit||m.title));return figure;
}
function setArticleTheme(root,e){
 const light=state.appearance==="light";
 const tones={
  atlas:["#b7cfad","#356747"],chronicle:["#d9c099","#855626"],
  kinship:["#deb6d3","#8c436d"],civic:["#b5cae9","#32628b"],
  archive:["#b8d4d0","#276468"],custom:["#b8d4d0","#276468"]
 };
 const color=e.accent||((tones[e.theme_id]||tones.archive)[light?1:0]);
 if(!/^#[0-9a-f]{6}$/i.test(color))return;
 // Maintain readable links when authors select a low contrast custom accent.
 const lum=x=>[1,3,5].map(i=>parseInt(x.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
 const background=light?"#f4f2ea":"#101b20",a=lum(background),b=lum(color),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
 root.style.setProperty("--article-accent",ratio>=4.5?color:(light?"#356747":"#b7cfad"));
 root.dataset.theme=e.theme_id;
}
async function renderArticle(id){
 const entry=byId(id);
 if(!entry)return missing("Article unavailable","This article is not currently published.");
 const world=currentId();
 const [media,relations,incoming,outgoing]=await Promise.all([
  get(url("/api/public/media",{world_id:world,entity_id:id})),
  get(url("/api/public/relations",{world_id:world,entity_id:id})),
  get(url("/api/public/backlinks",{world_id:world,entity_id:id})),
  get(url("/api/public/outgoing",{world_id:world,entity_id:id}))
 ]);
 if(world!==currentId()||location.hash!=="#/article/"+id)return;
 Object.assign(state,{current:entry,media,relations,incoming,outgoing});
 setTitle(entry.title);showRoute("article");
 const root=$("articleContent");root.replaceChildren();
 const wrap=node("div",undefined,"article-page-wrap");
 setArticleTheme(wrap,entry);
 const crumbs=node("nav",undefined,"crumbs");crumbs.setAttribute("aria-label","Breadcrumb");
 crumbs.append(link("World","#/"),link("Encyclopedia","#/browse"),link(category(entry).short,"#/browse/"+entry.type),node("span",entry.title));
 wrap.append(crumbs);
 const heroHeading=node("header",undefined,"article-heading");
 heroHeading.append(node("p",category(entry).label.toUpperCase(),"eyebrow"),node("h1",entry.title));
 if(entry.summary)heroHeading.append(node("p",entry.summary));
 wrap.append(heroHeading);
 const hero=media.find(m=>m.role==="hero"||m.role==="portrait");
 if(hero){const fig=makeMedia(hero);fig.className="article-hero";fig.querySelector("img").loading="eager";wrap.append(fig);}
 const cols=node("div",undefined,"article-columns");
 const main=node("div",undefined,"article-main");
 const aside=node("aside",undefined,"article-aside");
 const layout=entry.layout?.length?entry.layout:["body","facts","relationships","backlinks","timeline","map","gallery","sources"];
 const body=node("article",undefined,"reader-prose");
 body.innerHTML=markup(entry.body||"This entry has no extended article text yet.");
 if(layout.includes("body")){
  const headings=body.querySelectorAll("h2,h3,h4,h5");
  if(headings.length){
   const toc=node("section",undefined,"aside-panel"),list=node("nav",undefined,"toc");
   list.setAttribute("aria-label","On this page");toc.append(node("h2","In this article"));
   for(const heading of headings){
    const jump=node("button",heading.textContent,"toc-jump");
    jump.onclick=()=>heading.scrollIntoView({
     behavior:window.matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",
     block:"start"
    });
    list.append(jump);
   }
   toc.append(list);aside.append(toc);
  }
 }
 const connections=[...new Map([...relations.map(r=>{
  const other=byId(r.source_id===id?r.target_id:r.source_id);
  return other?[other.id,{entry:other,relation:humanize(r.predicate)}]:null;
 }).filter(Boolean),...outgoing.map(e=>[e.id,{entry:byId(e.id),relation:"Read more"}])]).values()]
 .filter(x=>x.entry&&x.entry.id!==id);
 const gallery=media.filter(m=>m.id!==hero?.id);
 const contentSection=(title)=>{const section=node("section",undefined,"reader-data-section");section.append(node("h2",title));return section;};
 for(const name of layout){
  if(name==="body"){
   main.append(body);
  }else if(name==="facts"){
   const section=contentSection("At a glance"),facts=node("dl",undefined,"reader-facts");
   const add=(term,value)=>{facts.append(node("dt",term),node("dd",value));};
   add("Subject",category(entry).label);
   if(entry.start_year!==null||entry.end_year!==null)add("Period",readableDate(entry));
   if(entry.aliases?.length)add("Also known as",entry.aliases.join(", "));
   if(entry.lat!==null&&entry.lon!==null)add("Location",entry.lat+", "+entry.lon);
   section.append(facts);main.append(section);
  }else if(name==="relationships"&&connections.length){
   const section=contentSection("People, places & connections"),list=node("div",undefined,"relation-list");
   for(const rel of connections.slice(0,16)){
    const a=link("","#/article/"+rel.entry.id,"relation-item");
    a.append(node("small",rel.relation),node("strong",rel.entry.title));list.append(a);
   }
   section.append(list);main.append(section);
  }else if(name==="backlinks"&&incoming.length){
   const section=contentSection("Referenced elsewhere");
   const list=node("div",undefined,"relation-list");
   for(const e of incoming.slice(0,12)){
    const item=link("","#/article/"+e.id,"relation-item");
    item.append(node("small","Referenced by"),node("strong",e.title));list.append(item);
   }
   section.append(list);main.append(section);
  }else if(name==="timeline"){
   const events=connections.filter(c=>c.entry.type==="event");
   if(events.length){
    const section=contentSection("Historical connections");
    for(const ev of events.slice(0,12)){
     const row=node("p",undefined,"reader-history-link");
     row.append(node("time",readableDate(ev.entry)+" · "),link(ev.entry.title,"#/article/"+ev.entry.id));section.append(row);
    }
    main.append(section);
   }
  }else if(name==="map"&&entry.lat!==null&&entry.lon!==null){
   const section=contentSection("In the atlas");
   section.append(node("p","Recorded coordinates: "+entry.lat+", "+entry.lon));
   section.append(link("Find this place on the map →","#/atlas/"+encodeURIComponent(entry.id),"reader-map-link"));
   main.append(section);
  }else if(name==="gallery"&&gallery.length){
   const section=contentSection("Images & documents"),strip=node("div",undefined,"gallery-strip");
   for(const m of gallery){
    const fig=makeMedia(m),img=fig.querySelector("img");
    const original=state.staticBundle?mediaUrl(m.media_id,false):"/media/"+encodeURIComponent(currentId())+"/"+encodeURIComponent(m.media_id);
    const a=link("",original);a.target="_blank";a.rel="noopener noreferrer";a.title="Open original image: "+m.title;
    img.remove();a.append(img);fig.prepend(a);strip.append(fig);
   }
   section.append(strip);main.append(section);
  }else if(name==="sources"){
   const sources=[...connections,...outgoing.map(e=>({entry:byId(e.id)}))]
    .filter(c=>c.entry?.type==="source");
   const unique=[...new Map(sources.map(c=>[c.entry.id,c.entry])).values()];
   if(unique.length){
    const section=contentSection("Documents & sources");
    for(const e of unique)section.append(link(e.title,"#/article/"+e.id,"reader-source-link"));
    main.append(section);
   }
  }
 }
 if(connections.length){
  const related=node("section",undefined,"aside-panel");
  related.append(node("h2","Continue exploring"));
  for(const rel of connections.slice(0,8))related.append(link(rel.entry.title,"#/article/"+rel.entry.id));
  aside.append(related);
 }
 cols.append(main,aside);wrap.append(cols);
 root.append(wrap);
 window.scrollTo(0,0);
}
function missing(title,description){$("emptyTitle").textContent=title;$("emptyDescription").textContent=description;showRoute("empty");setTitle(title);}
function renderHistory(){
 showRoute("history");setTitle("History");
 const fn=()=>{
  const year=Number($("historyYear").value)||50,all=$("historyAll").checked;
  const events=state.entries.filter(e=>e.type==="event"&&(all||e.start_year===null||e.start_year<=year))
    .sort((a,b)=>(a.start_year??999999)-(b.start_year??999999));
  const root=$("chronicleEntries");root.replaceChildren();
  for(const e of events){const row=node("article",undefined,"chronicle-event");
   row.append(node("time",readableDate(e)));const h=node("h2");h.append(link(e.title,"#/article/"+e.id));
   row.append(h,node("p",e.summary||"Read this event in the encyclopedia."));root.append(row);}
  if(!events.length)root.append(node("p","No historical events have been published for this period.","empty-published"));
 };$("historyYear").onchange=fn;$("historyAll").onchange=fn;fn();
}
const TILE=256;
function project(lon,lat,z){const n=256*2**z,r=Math.max(-85,Math.min(85,lat))*Math.PI/180;return{x:(lon+180)/360*n,y:(1-Math.log(Math.tan(r)+1/Math.cos(r))/Math.PI)/2*n};}
function unproject(x,y,z){const n=256*2**z,a=Math.PI-2*Math.PI*y/n;return{lon:x/n*360-180,lat:180/Math.PI*Math.atan(Math.sinh(a))};}
function paintMap(){
 if($("readerAtlas").hidden)return;
 const root=$("readerMap"),w=root.clientWidth,h=root.clientHeight,year=Number($("mapYear").value)||50;
 if(!w||!h)return;
 const c=project(state.map.lon,state.map.lat,state.map.zoom),left=c.x-w/2,top=c.y-h/2,n=2**state.map.zoom;
 const tiles=$("readerTiles"),pins=$("readerPins");tiles.replaceChildren();pins.replaceChildren();
 for(let x=Math.floor(left/TILE);x<=Math.floor((left+w)/TILE);x++)for(let y=Math.floor(top/TILE);y<=Math.floor((top+h)/TILE);y++){
  if(y<0||y>=n)continue;const img=node("img");
  img.src="https://tile.openstreetmap.org/"+state.map.zoom+"/"+((x%n+n)%n)+"/"+y+".png";img.alt="";img.draggable=false;img.loading="lazy";
  img.style.left=(x*TILE-left)+"px";img.style.top=(y*TILE-top)+"px";tiles.append(img);
 }
 const mapped=state.entries.filter(e=>e.lat!==null&&e.lon!==null&&activeAt(e,year));
 const places=$("mappedPlaces");places.replaceChildren();
 for(const e of mapped){places.append(link(e.title,"#/article/"+e.id));const p=project(e.lon,e.lat,state.map.zoom),x=p.x-left,y=p.y-top;
  if(x<0||y<0||x>w||y>h)continue;
  const pin=node("button","●","map-pin");pin.style.left=x+"px";pin.style.top=y+"px";pin.title=e.title;pin.setAttribute("aria-label","Read "+e.title);
  pin.append(node("span",e.title));pin.onclick=()=>location.hash="#/article/"+e.id;pins.append(pin);}
 if(!mapped.length)places.append(node("p","No published places with coordinates are recorded yet."));
}
function mapHandlers(){
 const map=$("readerMap");
 map.addEventListener("pointerdown",e=>{if(e.target.closest("button"))return;const p=project(state.map.lon,state.map.lat,state.map.zoom);state.map.drag={x:e.clientX,y:e.clientY,p,dx:0,dy:0};map.setPointerCapture(e.pointerId);});
 map.addEventListener("pointermove",e=>{if(!state.map.drag)return;state.map.drag.dx=e.clientX-state.map.drag.x;state.map.drag.dy=e.clientY-state.map.drag.y;
  for(const id of ["readerTiles","readerPins"])$(id).style.transform="translate("+state.map.drag.dx+"px,"+state.map.drag.dy+"px)";});
 for(const event of ["pointerup","pointercancel"])map.addEventListener(event,()=>{
  const d=state.map.drag;if(!d)return;state.map.drag=null;
  const p=unproject(d.p.x-d.dx,d.p.y-d.dy,state.map.zoom);
  state.map.lon=Math.max(-180,Math.min(180,p.lon));state.map.lat=Math.max(-85,Math.min(85,p.lat));
  for(const id of ["readerTiles","readerPins"])$(id).style.transform="";
  paintMap();
 });
 map.addEventListener("wheel",e=>{e.preventDefault();state.map.zoom=Math.max(1,Math.min(15,state.map.zoom+(e.deltaY<0?1:-1)));paintMap();},{passive:false});
 $("mapPlus").onclick=()=>{state.map.zoom=Math.min(15,state.map.zoom+1);paintMap();};
 $("mapMinus").onclick=()=>{state.map.zoom=Math.max(1,state.map.zoom-1);paintMap();};
 $("mapHome").onclick=()=>{state.map.lon=0;state.map.lat=25;state.map.zoom=2;paintMap();};
 $("mapYear").onchange=paintMap;
 window.addEventListener("resize",()=>{if(!$("readerAtlas").hidden)paintMap();});
}
function setupTools(){
 $("searchToggle").onclick=()=>{$("readingPanel").hidden=true;$("searchPanel").hidden=!$("searchPanel").hidden;if(!$("searchPanel").hidden)$("siteSearch").focus();};
 $("closeSearch").onclick=()=>$("searchPanel").hidden=true;
 const quick=()=>{
  const q=$("siteSearch").value.toLowerCase().trim(),root=$("quickResults");root.replaceChildren();
  if(!q)return;
  const matches=state.entries.filter(e=>[e.title,e.summary,...e.aliases].some(v=>String(v||"").toLowerCase().includes(q))).slice(0,12);
  for(const e of matches){const b=node("button",undefined,"quick-result");b.append(node("strong",e.title),node("small",category(e).short+" · "+(e.summary||"").slice(0,115)));
   b.onclick=()=>{$("searchPanel").hidden=true;location.hash="#/article/"+e.id;};root.append(b);}
  if(!matches.length)root.append(node("p","No published matches."));
 };
 $("siteSearch").oninput=quick;
 $("textSettings").onclick=()=>{$("searchPanel").hidden=true;$("readingPanel").hidden=!$("readingPanel").hidden;};
 $("fontSmaller").onclick=()=>{state.font=Math.max(14,state.font-1);document.documentElement.style.setProperty("--read-size",state.font+"px");localStorage.setItem("reader-font",state.font);};
 $("fontLarger").onclick=()=>{state.font=Math.min(23,state.font+1);document.documentElement.style.setProperty("--read-size",state.font+"px");localStorage.setItem("reader-font",state.font);};
 $("readingAppearance").onchange=()=>{state.appearance=$("readingAppearance").value;document.body.dataset.appearance=state.appearance;localStorage.setItem("reader-mode",state.appearance);};
 document.addEventListener("keydown",e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==="k"){e.preventDefault();$("searchPanel").hidden=false;$("siteSearch").focus();}if(e.key==="Escape"){$("searchPanel").hidden=true;$("readingPanel").hidden=true;}});
 state.font=Math.max(14,Math.min(23,Number(localStorage.getItem("reader-font"))||17));
 document.documentElement.style.setProperty("--read-size",state.font+"px");
 state.appearance=localStorage.getItem("reader-mode")==="light"?"light":"dark";
 $("readingAppearance").value=state.appearance;document.body.dataset.appearance=state.appearance;
 mapHandlers();
}
async function changeWorld(id){
 const found=state.worlds.find(w=>w.id===id);if(!found)return;
 state.world=found;localStorage.setItem("reader-world",id);
 state.entries=await get(url("/api/public/entities",{world_id:id}));
 syncWorld();renderHome();await navigate();
}
async function navigate(){
 const hash=decodeURIComponent(location.hash||"#/");
 const parts=hash.replace(/^#\/?/,"").split("/");const route=parts[0]||"home";
 $("searchPanel").hidden=true;$("readingPanel").hidden=true;
 if(route==="home"){showRoute("home");renderHome();setTitle("Discover");}
 else if(route==="browse")renderBrowse(parts[1]||"");
 else if(route==="article"){try{await renderArticle(parts[1]);}catch(e){missing("Article unavailable","This article could not be loaded.");}}
 else if(route==="atlas"){
  const selected=byId(parts[1]);
  if(selected&&selected.lat!==null&&selected.lon!==null){
   state.map.lon=selected.lon;state.map.lat=selected.lat;state.map.zoom=8;
  }
  showRoute("atlas");setTitle("Atlas");paintMap();
 }
 else if(route==="history")renderHistory();
 else missing("Page not found","Choose a destination from the navigation above.");
 window.scrollTo(0,0);
}
async function init(){
 setupTools();
 try{
  if(document.querySelector('meta[name="worldbible-static"]')){
   const response=await fetch("site-data.json");
   if(!response.ok)throw Error("Published site data missing");
   state.staticBundle=await response.json();
  }
  state.worlds=await get("/api/public/worlds");
  const fromUrl=new URLSearchParams(location.search).get("world");
  const saved=localStorage.getItem("reader-world");
  state.world=state.worlds.find(w=>w.id===fromUrl)||state.worlds.find(w=>w.id===saved)||state.worlds[0]||null;
  const picker=$("readerWorld");picker.replaceChildren(...state.worlds.map(w=>new Option(w.name,w.id)));
  picker.hidden=state.worlds.length<2;
  picker.onchange=async()=>{history.replaceState(null,"",location.pathname+"?world="+encodeURIComponent(picker.value)+"#/");await changeWorld(picker.value);};
  if(state.world){picker.value=state.world.id;state.entries=await get(url("/api/public/entities",{world_id:currentId()}));}
  syncWorld();window.addEventListener("hashchange",navigate);await navigate();
 }catch(e){console.error("Reader initialization failed",e);missing("Unable to load the encyclopedia","Please verify the local server is running.");}
}
init();
