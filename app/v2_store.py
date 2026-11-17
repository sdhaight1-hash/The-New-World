"""Additive v2 knowledge services. Preserves v1 entities, IDs, and prose."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from uuid import uuid4
from knowledge_v2 import type_catalog, validate_properties, suggestions, normalize, insert_approved

V2_SQL = """
CREATE TABLE IF NOT EXISTS entry_details(
 entity_id TEXT PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE,
 world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
 subtype TEXT, properties TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS categories(
 id TEXT PRIMARY KEY, world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
 name TEXT NOT NULL, slug TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
 parent_id TEXT REFERENCES categories(id) ON DELETE RESTRICT, sort_order INTEGER NOT NULL DEFAULT 0,
 UNIQUE(world_id,slug)
);
CREATE TABLE IF NOT EXISTS entity_categories(
 entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
 category_id TEXT NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
 PRIMARY KEY(entity_id,category_id)
);
CREATE INDEX IF NOT EXISTS ix_entity_categories_category ON entity_categories(category_id);
CREATE TABLE IF NOT EXISTS tags(
 id TEXT PRIMARY KEY, world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
 name TEXT NOT NULL, normalized_name TEXT NOT NULL,
 UNIQUE(world_id,normalized_name)
);
CREATE TABLE IF NOT EXISTS entity_tags(
 entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
 tag_id TEXT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
 PRIMARY KEY(entity_id,tag_id)
);
CREATE INDEX IF NOT EXISTS ix_entity_tags_tag ON entity_tags(tag_id);
CREATE TABLE IF NOT EXISTS mention_decisions(
 id TEXT PRIMARY KEY, world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
 source_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
 target_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
 term TEXT NOT NULL, fingerprint TEXT NOT NULL,
 decision TEXT NOT NULL CHECK(decision='ignored'),
 UNIQUE(source_id,target_id,term,fingerprint)
);
"""

def initialize(store, previous_version):
    if previous_version == 1:
        from backup import make_backup
        target = store.path.parent / "backups" / "before-knowledge-v2.zip"
        if not target.exists():
            make_backup(store.path, target)
    with store.lock:
        store.db.executescript(V2_SQL)
        store.db.execute("PRAGMA user_version=2")
        store.db.commit()

def error(message, status=400):
    # Reuse the application's standard HTTP error with correct status.
    import sys
    module = sys.modules.get("server")
    if module is None or not hasattr(module,"Error"):
        module = sys.modules["__main__"]
    return module.Error(message,status)

def types():
    return type_catalog()

def categories(store,wid,public=False):
    store.check_world(wid)
    if public:
        return store.rows("""SELECT DISTINCT c.* FROM categories c
            JOIN entity_categories ec ON ec.category_id=c.id
            JOIN entities e ON e.id=ec.entity_id AND e.world_id=c.world_id
            JOIN publications p ON p.entity_id=e.id
            WHERE c.world_id=? ORDER BY c.sort_order,c.name""",(wid,))
    return store.rows("SELECT * FROM categories WHERE world_id=? ORDER BY sort_order,name",(wid,))

def tags(store,wid,public=False):
    store.check_world(wid)
    if public:
        return store.rows("""SELECT DISTINCT t.* FROM tags t
            JOIN entity_tags et ON et.tag_id=t.id
            JOIN entities e ON e.id=et.entity_id AND e.world_id=t.world_id
            JOIN publications p ON p.entity_id=e.id
            WHERE t.world_id=? ORDER BY t.name""",(wid,))
    return store.rows("SELECT * FROM tags WHERE world_id=? ORDER BY name",(wid,))

def create_category(store,wid,data):
    store.check_world(wid)
    if not isinstance(data,dict) or not isinstance(data.get("name"),str) or not 0<len(data["name"].strip())<=120:
        raise error("Invalid category name")
    name=data["name"].strip()
    slug=re.sub(r"[^\w-]+","-",normalize(name)).strip("-")
    if not slug: raise error("Invalid category name")
    parent=data.get("parent_id")
    if parent and not store.one("SELECT 1 FROM categories WHERE world_id=? AND id=?",(wid,parent)):
        raise error("Invalid category parent")
    cid=str(uuid4())
    try:
        with store.lock,store.db:
            store.db.execute("INSERT INTO categories VALUES(?,?,?,?,?,?,?)",
               (cid,wid,name,slug,str(data.get("description",""))[:2000],parent,0))
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc): raise error("Category already exists",409) from exc
        raise
    return dict(store.one("SELECT * FROM categories WHERE id=?",(cid,)))

def create_tag(store,wid,data):
    store.check_world(wid)
    if not isinstance(data,dict) or not isinstance(data.get("name"),str) or not 0<len(data["name"].strip())<=80:
        raise error("Invalid tag")
    name=data["name"].strip()
    with store.lock,store.db:
        store.db.execute("INSERT OR IGNORE INTO tags VALUES(?,?,?,?)",
             (str(uuid4()),wid,name,normalize(name)))
    return store.rows("SELECT * FROM tags WHERE world_id=? AND normalized_name=?",(wid,normalize(name)))[0]

def classifications(store,wid,eid):
    store.check_entity(wid,eid)
    cats=store.rows("""SELECT ec.category_id FROM entity_categories ec
        JOIN categories c ON c.id=ec.category_id
        WHERE ec.entity_id=? AND c.world_id=?""",(eid,wid))
    tag_rows=store.rows("""SELECT et.tag_id FROM entity_tags et
        JOIN tags t ON t.id=et.tag_id
        WHERE et.entity_id=? AND t.world_id=?""",(eid,wid))
    detail=store.one("SELECT subtype,properties FROM entry_details WHERE entity_id=? AND world_id=?",(eid,wid))
    return {"categories":[r["category_id"] for r in cats],
            "tags":[r["tag_id"] for r in tag_rows],
            "subtype":detail["subtype"] if detail else None,
            "properties":json.loads(detail["properties"]) if detail else {}}

def update_metadata(store,wid,eid,data):
    entry=store.check_entity(wid,eid)
    if not isinstance(data,dict) or set(data)!={"categories","tags","subtype","properties"}:
        raise error("Expected categories, tags, subtype, properties")
    cats,ts=data["categories"],data["tags"]
    if not isinstance(cats,list) or not isinstance(ts,list) or len(cats)>100 or len(ts)>100 or len(cats)!=len(set(cats)) or len(ts)!=len(set(ts)):
        raise error("Invalid classifications")
    try:
        validate_properties(entry["type"],data["subtype"],data["properties"],
           lambda target: bool(store.one("SELECT 1 FROM entities WHERE world_id=? AND id=?",(wid,target))))
    except ValueError as exc:
        raise error(str(exc)) from exc
    with store.lock,store.db:
        for table,values in (("categories",cats),("tags",ts)):
            valid={r["id"] for r in store.db.execute("SELECT id FROM "+table+" WHERE world_id=?",(wid,))}
            if not set(values)<=valid: raise error("Missing or cross-world classification")
        store.db.execute("""INSERT INTO entry_details VALUES(?,?,?,?)
            ON CONFLICT(entity_id) DO UPDATE SET subtype=excluded.subtype,properties=excluded.properties""",
            (eid,wid,data["subtype"],json.dumps(data["properties"],ensure_ascii=False)))
        store.db.execute("DELETE FROM entity_categories WHERE entity_id=?",(eid,))
        store.db.execute("DELETE FROM entity_tags WHERE entity_id=?",(eid,))
        store.db.executemany("INSERT INTO entity_categories VALUES(?,?)",[(eid,x) for x in cats])
        store.db.executemany("INSERT INTO entity_tags VALUES(?,?)",[(eid,x) for x in ts])
    return classifications(store,wid,eid)

def revision(entry):
    return hashlib.sha256(entry["body"].encode("utf-8")).hexdigest()

def mentions(store,wid,eid):
    entry=store.check_entity(wid,eid)
    ignored={(r["target_id"],r["term"],r["fingerprint"]) for r in store.rows(
       "SELECT target_id,term,fingerprint FROM mention_decisions WHERE world_id=? AND source_id=?",(wid,eid))}
    return {"revision":revision(entry),
            "suggestions":suggestions(entry["body"],eid,store.entries(wid),ignored)}

def decide(store,wid,eid,data,approve):
    if not isinstance(data,dict): raise error("Invalid reference decision")
    with store.lock:
        entry=store.check_entity(wid,eid)
        if data.get("revision")!=revision(entry): raise error("Article changed; refresh references",409)
        target=data.get("target_id")
        store.check_entity(wid,target)
        proposal=mentions(store,wid,eid)
        match=next((m for m in proposal["suggestions"]
            if m["start"]==data.get("start") and m["end"]==data.get("end")
            and m["fingerprint"]==data.get("fingerprint")
            and target in [c["id"] for c in m["candidates"]]),None)
        if match is None: raise error("Reference changed; rescan",409)
        if approve:
            with store.db:
                return store.update_entry(wid,eid,{"body":insert_approved(entry["body"],match,target)})
        with store.db:
            store.db.execute("INSERT OR IGNORE INTO mention_decisions VALUES(?,?,?,?,?,?,?)",
                (str(uuid4()),wid,eid,target,normalize(match["text"]),match["fingerprint"],"ignored"))
        return {"ignored":True}

def search(store,wid,needle="",typ=None,category=None,tag=None,public=False,offset=0,limit=40):
    store.check_world(wid)
    if not 0<=offset<=100000 or not 1<=limit<=100: raise error("Invalid pagination")
    if not isinstance(needle,str) or len(needle)>200: raise error("Search too long")
    sql="SELECT e.* FROM entities e"
    params=[]
    if public: sql+=" JOIN publications p ON p.entity_id=e.id"
    if category:
        sql+=" JOIN entity_categories ec ON ec.entity_id=e.id AND ec.category_id=?"
        params.append(category)
    if tag:
        sql+=" JOIN entity_tags et ON et.entity_id=e.id AND et.tag_id=?"
        params.append(tag)
    sql+=" WHERE e.world_id=?";params.append(wid)
    if typ: sql+=" AND e.type=?";params.append(typ)
    if needle:
        sql+=" AND (e.title LIKE ? OR e.aliases LIKE ? OR e.summary LIKE ? OR e.body LIKE ?)"
        params.extend(["%"+needle+"%"]*4)
    sql+=" ORDER BY e.title COLLATE NOCASE LIMIT ? OFFSET ?"
    params.extend([limit,offset])
    import sys
    module = sys.modules.get("server")
    if module is None or not hasattr(module,"canonical"):
        module = sys.modules["__main__"]
    return [module.canonical(r) for r in store.rows(sql,params)]

def enrich_public(store,wid,entries):
    # Batch enrich only published entries. No draft references are exposed.
    items=[]
    for entry in entries:
        copy=dict(entry)
        classes=classifications(store,wid,entry["id"])
        copy["subtype"]=classes["subtype"]
        copy["properties"]=classes["properties"]
        copy["category_ids"]=classes["categories"]
        copy["tag_ids"]=classes["tags"]
        items.append(copy)
    return items

def export_tables(store,wid):
    return {
      "categories":categories(store,wid),"tags":tags(store,wid),
      "entry_details":store.rows("SELECT * FROM entry_details WHERE world_id=?",(wid,)),
      "entity_categories":store.rows("""SELECT ec.* FROM entity_categories ec
            JOIN entities e ON e.id=ec.entity_id WHERE e.world_id=?""",(wid,)),
      "entity_tags":store.rows("""SELECT et.* FROM entity_tags et
            JOIN entities e ON e.id=et.entity_id WHERE e.world_id=?""",(wid,))
    }

def import_tables(store,wid,payload,old_new):
    source_cats=payload.get("categories",[])
    source_tags=payload.get("tags",[])
    cat_map={x["id"]:str(uuid4()) for x in source_cats}
    tag_map={x["id"]:str(uuid4()) for x in source_tags}
    if len(cat_map)!=len(source_cats) or len(tag_map)!=len(source_tags):
        raise error("Duplicate category/tag identifiers")
    with store.lock,store.db:
        for c in source_cats:
            store.db.execute("INSERT INTO categories VALUES(?,?,?,?,?,?,?)",
                (cat_map[c["id"]],wid,c["name"],c["slug"],c.get("description",""),
                 cat_map.get(c.get("parent_id")),c.get("sort_order",0)))
        for t in source_tags:
            store.db.execute("INSERT INTO tags VALUES(?,?,?,?)",
                (tag_map[t["id"]],wid,t["name"],normalize(t["name"])))
        from knowledge_v2 import TYPE_FIELDS
        for detail in payload.get("entry_details",[]):
            if detail["entity_id"] not in old_new: raise error("Invalid metadata entry")
            record=store.check_entity(wid,old_new[detail["entity_id"]])
            props=json.loads(detail["properties"])
            for key,kind in TYPE_FIELDS.get(record["type"],{}).items():
                if kind=="entry" and props.get(key):
                    if props[key] not in old_new: raise error("Invalid metadata reference")
                    props[key]=old_new[props[key]]
            validate_properties(record["type"],detail.get("subtype"),props,
                 lambda key:bool(store.one("SELECT 1 FROM entities WHERE world_id=? AND id=?",(wid,key))))
            store.db.execute("INSERT INTO entry_details VALUES(?,?,?,?)",
                 (record["id"],wid,detail.get("subtype"),json.dumps(props,ensure_ascii=False)))
        for ec in payload.get("entity_categories",[]):
            if ec["entity_id"] not in old_new or ec["category_id"] not in cat_map: raise error("Invalid category assignment")
            store.db.execute("INSERT INTO entity_categories VALUES(?,?)",
                 (old_new[ec["entity_id"]],cat_map[ec["category_id"]]))
        for et in payload.get("entity_tags",[]):
            if et["entity_id"] not in old_new or et["tag_id"] not in tag_map: raise error("Invalid tag assignment")
            store.db.execute("INSERT INTO entity_tags VALUES(?,?)",
                 (old_new[et["entity_id"]],tag_map[et["tag_id"]]))
