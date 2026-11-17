"""The New World reusable local-first worldbuilding HTTP server (Python 3.11+).

Run: python app/server.py
No cloud accounts or live-service dependencies. Pillow is required for image ingestion.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import mimetypes
import os
from pathlib import Path
import re
import sqlite3
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit, unquote
from uuid import uuid4
import v2_store

ROOT = Path(__file__).resolve().parent
DB_DEFAULT = ROOT.parent / ".worldbible" / "worlds.sqlite3"
MAX_JSON = 25_000_000
MAX_IMAGE = 12_000_000
ALLOWED_TYPES = {"person", "place", "event", "organization", "family", "object", "source", "subject"}
STATUSES = {"working", "established", "disputed", "superseded"}
THEMES = {"archive", "atlas", "chronicle", "kinship", "civic", "custom"}
LINK_PATTERN = re.compile(r"\[\[([a-zA-Z0-9:-]{3,100})(?:\|[^\]\n]{1,180})?\]\]")
TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,60}$")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
VALID_BLOCKS = {"body", "facts", "relationships", "backlinks", "timeline", "map", "gallery", "sources"}
DEFAULT_BLOCKS = ["body", "facts", "relationships", "backlinks", "timeline", "map", "gallery", "sources"]
PREDICATES = {
    "related_to", "located_in", "part_of", "member_of", "founded_by", "participated_in",
    "biological_parent_of", "adoptive_parent_of", "step_parent_of", "partner_of",
    "married_to", "resided_in", "traded_with", "allied_with", "claimed_by", "governed_by",
    "owned_by", "traveled_to", "succeeded_by", "employed_by", "connected_to", "custom",
}
SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS worlds(
 id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
 epoch_year INTEGER, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS entities(
 id TEXT PRIMARY KEY, world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
 type TEXT NOT NULL, title TEXT NOT NULL, aliases TEXT NOT NULL DEFAULT '[]',
 summary TEXT NOT NULL DEFAULT '', body TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'working',
 start_year INTEGER, end_year INTEGER, lat REAL, lon REAL,
 theme_id TEXT NOT NULL DEFAULT 'archive', accent TEXT, layout TEXT NOT NULL DEFAULT '[]',
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 UNIQUE(world_id,id)
);
CREATE INDEX IF NOT EXISTS ix_entities_world_type ON entities(world_id,type,title);
CREATE TABLE IF NOT EXISTS relations(
 id TEXT PRIMARY KEY, world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
 source_id TEXT NOT NULL REFERENCES entities(id) ON DELETE RESTRICT,
 target_id TEXT NOT NULL REFERENCES entities(id) ON DELETE RESTRICT,
 predicate TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'working',
 start_year INTEGER, end_year INTEGER, notes TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_rel_source ON relations(world_id,source_id);
CREATE INDEX IF NOT EXISTS ix_rel_target ON relations(world_id,target_id);
CREATE TABLE IF NOT EXISTS content_links(
 source_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
 target_id TEXT NOT NULL REFERENCES entities(id) ON DELETE RESTRICT,
 PRIMARY KEY(source_id,target_id)
);
CREATE INDEX IF NOT EXISTS ix_link_target ON content_links(target_id);
CREATE TABLE IF NOT EXISTS media(
 id TEXT PRIMARY KEY, world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
 title TEXT NOT NULL, filename TEXT NOT NULL, mime TEXT NOT NULL,
 sha256 TEXT NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL,
 credit TEXT NOT NULL DEFAULT '', alt TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS media_uses(
 id TEXT PRIMARY KEY, world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
 entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
 media_id TEXT NOT NULL REFERENCES media(id) ON DELETE RESTRICT,
 role TEXT NOT NULL DEFAULT 'gallery', caption TEXT NOT NULL DEFAULT '',
 UNIQUE(entity_id,media_id,role)
);
CREATE INDEX IF NOT EXISTS ix_media_uses_entity ON media_uses(entity_id);
CREATE TABLE IF NOT EXISTS moodboards(
 id TEXT PRIMARY KEY, world_id TEXT NOT NULL REFERENCES worlds(id) ON DELETE CASCADE,
 title TEXT NOT NULL, description TEXT NOT NULL DEFAULT '',
 entity_id TEXT REFERENCES entities(id) ON DELETE SET NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_moodboards_world ON moodboards(world_id,title);
CREATE TABLE IF NOT EXISTS moodboard_items(
 id TEXT PRIMARY KEY, board_id TEXT NOT NULL REFERENCES moodboards(id) ON DELETE CASCADE,
 kind TEXT NOT NULL, content TEXT NOT NULL DEFAULT '',
 media_id TEXT REFERENCES media(id) ON DELETE RESTRICT,
 entity_id TEXT REFERENCES entities(id) ON DELETE SET NULL,
 color TEXT, x INTEGER NOT NULL, y INTEGER NOT NULL,
 w INTEGER NOT NULL, h INTEGER NOT NULL, z INTEGER NOT NULL,
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_moodboard_items_board ON moodboard_items(board_id,z);
CREATE TABLE IF NOT EXISTS publications(
 entity_id TEXT PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE,
 published_at TEXT NOT NULL
);

"""
ENTITY_COLUMNS = ("id", "world_id", "type", "title", "aliases", "summary", "body", "status",
                  "start_year", "end_year", "lat", "lon", "theme_id", "accent", "layout",
                  "created_at", "updated_at")
REL_COLUMNS = ("id", "world_id", "source_id", "target_id", "predicate", "status",
               "start_year", "end_year", "notes", "created_at")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Error(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status
        super().__init__(message)


def require(condition, message, status=400):
    if not condition:
        raise Error(message, status)


def canonical(row):
    d = dict(row)
    for key in ("aliases", "layout"):
        if key in d:
            d[key] = json.loads(d[key])
            if isinstance(d[key], str):
                # Accept records written by early prototype with double-serialized defaults.
                d[key] = json.loads(d[key])
    return d


def validate_entity(data, partial=False):
    fields = {"type", "title", "aliases", "summary", "body", "status", "start_year",
              "end_year", "lat", "lon", "theme_id", "accent", "layout"}
    require(isinstance(data, dict) and set(data) <= fields, "Invalid entity properties")
    if not partial:
        require("title" in data and "type" in data, "Title and type required")
    if "type" in data:
        require(isinstance(data["type"], str) and TYPE_PATTERN.fullmatch(data["type"]), "Invalid entity type")
    if "title" in data:
        require(isinstance(data["title"], str) and 0 < len(data["title"].strip()) <= 250, "Invalid title")
    for k in ("summary", "body"):
        if k in data:
            require(isinstance(data[k], str) and len(data[k]) <= 2_000_000, "Invalid " + k)
    if "status" in data:
        require(data["status"] in STATUSES, "Invalid canon status")
    if "aliases" in data:
        a = data["aliases"]
        require(isinstance(a, list) and len(a) <= 100 and all(isinstance(v, str) and 0 < len(v) <= 250 for v in a), "Invalid aliases")
        data["aliases"] = list(dict.fromkeys(v.strip() for v in a if v.strip()))
    if "theme_id" in data:
        require(data["theme_id"] in THEMES, "Unknown theme")
    if "accent" in data:
        require(data["accent"] is None or isinstance(data["accent"], str) and HEX.fullmatch(data["accent"]), "Accent must be hex color")
    if "layout" in data:
        require(isinstance(data["layout"], list) and len(data["layout"]) <= len(VALID_BLOCKS), "Invalid layout")
        require(all(isinstance(v, str) and v in VALID_BLOCKS for v in data["layout"]), "Invalid layout block")
        require(len(set(data["layout"])) == len(data["layout"]), "Duplicate layout block")
    for k in ("start_year", "end_year"):
        if k in data:
            require(data[k] is None or type(data[k]) is int and -100000 <= data[k] <= 100000, "Invalid year")
    if "start_year" in data and "end_year" in data and data["start_year"] is not None and data["end_year"] is not None:
        require(data["start_year"] <= data["end_year"], "End precedes start")
    for k, bounds in (("lat", (-90, 90)), ("lon", (-180, 180))):
        if k in data:
            v = data[k]
            require(v is None or type(v) in (float, int) and bounds[0] <= v <= bounds[1], "Invalid coordinate")
    return data


class Store:
    def __init__(self, path=DB_DEFAULT, media_dir=None):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.media_dir = Path(media_dir) if media_dir else self.path.parent / "media"
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        require(version <= 2, "Database schema is newer than this application", 409)
        self.db.executescript(SCHEMA)
        self.db.commit()
        v2_store.initialize(self, version)

    def close(self):
        self.db.close()

    def one(self, sql, args=()):
        with self.lock:
            return self.db.execute(sql, args).fetchone()

    def rows(self, sql, args=()):
        with self.lock:
            return [dict(r) for r in self.db.execute(sql, args).fetchall()]

    def check_world(self, wid):
        require(self.one("SELECT 1 FROM worlds WHERE id=?", (wid,)), "World not found", 404)

    def check_entity(self, wid, eid):
        r = self.one("SELECT * FROM entities WHERE id=? AND world_id=?", (eid, wid))
        require(r, "Entry not found in this world", 404)
        return canonical(r)

    def boards(self, wid):
        self.check_world(wid)
        return self.rows("""SELECT b.*,e.title AS entity_title,
           (SELECT COUNT(*) FROM moodboard_items i WHERE i.board_id=b.id) AS item_count,
           (SELECT i.media_id FROM moodboard_items i
              WHERE i.board_id=b.id AND i.kind='image' ORDER BY i.z DESC LIMIT 1) AS preview_media_id,
           (SELECT i.color FROM moodboard_items i
              WHERE i.board_id=b.id AND i.kind='swatch' ORDER BY i.z DESC LIMIT 1) AS preview_color
           FROM moodboards b LEFT JOIN entities e ON e.id=b.entity_id
           WHERE b.world_id=? ORDER BY b.updated_at DESC,b.title""", (wid,))

    def board(self, wid, bid):
        self.check_world(wid)
        row=self.one("SELECT * FROM moodboards WHERE id=? AND world_id=?", (bid,wid))
        require(row,"Moodboard not found in this world",404)
        return {"board":dict(row),"items":self.rows("""SELECT i.*,e.title AS entity_title,
                 m.title AS media_title,m.credit AS media_credit,m.alt AS media_alt FROM moodboard_items i
                 LEFT JOIN entities e ON e.id=i.entity_id
                 LEFT JOIN media m ON m.id=i.media_id
                 WHERE i.board_id=? ORDER BY i.z,i.created_at""",(bid,))}

    def create_board(self, wid, data):
        self.check_world(wid)
        require(isinstance(data,dict) and set(data)<={"title","description","entity_id"},"Invalid board fields")
        title=data.get("title","")
        desc=data.get("description","")
        eid=data.get("entity_id")
        require(isinstance(title,str) and 0<len(title.strip())<=180,"Invalid moodboard title")
        require(isinstance(desc,str) and len(desc)<=4000,"Invalid moodboard description")
        if eid is not None:self.check_entity(wid,eid)
        bid=str(uuid4());stamp=now()
        with self.lock,self.db:
            self.db.execute("INSERT INTO moodboards VALUES(?,?,?,?,?,?,?)",
                            (bid,wid,title.strip(),desc,eid,stamp,stamp))
        return self.board(wid,bid)

    def update_board(self,wid,bid,data):
        self.board(wid,bid)
        require(isinstance(data,dict) and set(data)<={"title","description","entity_id"},"Invalid board fields")
        if "title" in data:require(isinstance(data["title"],str) and 0<len(data["title"].strip())<=180,"Invalid board title")
        if "description" in data:require(isinstance(data["description"],str) and len(data["description"])<=4000,"Invalid description")
        if "entity_id" in data and data["entity_id"] is not None:self.check_entity(wid,data["entity_id"])
        if "title" in data:data["title"]=data["title"].strip()
        data["updated_at"]=now()
        with self.lock,self.db:
            self.db.execute("UPDATE moodboards SET "+",".join(k+"=?" for k in data)+" WHERE id=? AND world_id=?",
                            (*data.values(),bid,wid))
        return self.board(wid,bid)

    def delete_board(self,wid,bid):
        self.board(wid,bid)
        with self.lock,self.db:
            self.db.execute("DELETE FROM moodboards WHERE id=? AND world_id=?",(bid,wid))
        return {"deleted":bid}

    def add_board_item(self,wid,bid,data):
        self.board(wid,bid)
        require(isinstance(data,dict) and set(data)<={"kind","content","media_id","entity_id","color","x","y","w","h","z"},"Invalid board card")
        kind=data.get("kind")
        require(kind in ("note","image","entry","swatch"),"Invalid board card kind")
        content=data.get("content","")
        require(isinstance(content,str) and len(content)<=5000,"Invalid board card text")
        mid=data.get("media_id");eid=data.get("entity_id");color=data.get("color")
        if mid is not None:require(self.one("SELECT 1 FROM media WHERE world_id=? AND id=?",(wid,mid)),"Image not found in this world",404)
        if eid is not None:self.check_entity(wid,eid)
        require((kind=="image" and mid is not None and eid is None) or
                (kind=="entry" and eid is not None and mid is None) or
                (kind in ("note","swatch") and mid is None and eid is None),"Invalid card reference")
        if kind=="swatch":require(isinstance(color,str) and HEX.fullmatch(color),"Invalid swatch color")
        else:require(color is None or isinstance(color,str) and HEX.fullmatch(color),"Invalid card color")
        values={key:data.get(key,default) for key,default in (("x",60),("y",60),("w",240),("h",190),("z",0))}
        self._validate_board_geometry(values)
        iid=str(uuid4())
        with self.lock,self.db:
            self.db.execute("""INSERT INTO moodboard_items
              (id,board_id,kind,content,media_id,entity_id,color,x,y,w,h,z,created_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
              (iid,bid,kind,content,mid,eid,color,*(values[k] for k in ("x","y","w","h","z")),now()))
            self.db.execute("UPDATE moodboards SET updated_at=? WHERE id=?",(now(),bid))
        return self.board(wid,bid)

    def _validate_board_geometry(self,values):
        for k in ("x","y","w","h","z"):
            require(type(values[k]) is int,"Board positions must be integers")
        require(-20000<=values["x"]<=20000 and -20000<=values["y"]<=20000,"Board position out of bounds")
        require(120<=values["w"]<=1200 and 95<=values["h"]<=1200,"Board size out of bounds")
        require(0<=values["z"]<=100000,"Board layer out of bounds")

    def update_board_item(self,wid,bid,iid,data):
        self.board(wid,bid)
        require(self.one("SELECT 1 FROM moodboard_items WHERE id=? AND board_id=?",(iid,bid)),
                "Board card not found",404)
        require(isinstance(data,dict) and set(data)<={"content","color","x","y","w","h","z"},
                "Invalid card update")
        if "content" in data:require(isinstance(data["content"],str) and len(data["content"])<=5000,"Invalid card text")
        if "color" in data:require(data["color"] is None or isinstance(data["color"],str) and HEX.fullmatch(data["color"]),"Invalid card color")
        values=dict(self.one("SELECT x,y,w,h,z FROM moodboard_items WHERE id=?",(iid,)))
        values.update({k:v for k,v in data.items() if k in values})
        self._validate_board_geometry(values)
        if data:
            with self.lock,self.db:
                self.db.execute("UPDATE moodboard_items SET "+",".join(k+"=?" for k in data)+" WHERE id=? AND board_id=?",
                                (*data.values(),iid,bid))
                self.db.execute("UPDATE moodboards SET updated_at=? WHERE id=?",(now(),bid))
        return self.board(wid,bid)

    def delete_board_item(self,wid,bid,iid):
        self.board(wid,bid)
        with self.lock,self.db:
            cur=self.db.execute("DELETE FROM moodboard_items WHERE id=? AND board_id=?",(iid,bid))
            require(cur.rowcount==1,"Board card not found",404)
            self.db.execute("UPDATE moodboards SET updated_at=? WHERE id=?",(now(),bid))
        return self.board(wid,bid)

    def publication(self, wid, eid, publish):
        """Publishing is separate from canon status; unpublished records remain editable."""
        self.check_entity(wid, eid)
        require(type(publish) is bool, "Published must be boolean")
        with self.lock, self.db:
            if publish:
                self.db.execute("""INSERT INTO publications(entity_id,published_at) VALUES(?,?)
                    ON CONFLICT(entity_id) DO NOTHING""", (eid, now()))
            else:
                self.db.execute("DELETE FROM publications WHERE entity_id=?", (eid,))
        return {"entity_id":eid,"published":publish}

    def is_published(self, wid, eid):
        self.check_world(wid)
        return bool(self.one("""SELECT 1 FROM publications p
            JOIN entities e ON e.id=p.entity_id
            WHERE e.world_id=? AND e.id=?""",(wid,eid)))

    def public_worlds(self):
        return self.rows("""SELECT w.* FROM worlds w
            WHERE EXISTS(SELECT 1 FROM entities e JOIN publications p ON p.entity_id=e.id
                         WHERE e.world_id=w.id)
            ORDER BY w.name""")

    def public_entries(self, wid, search="", typ=None):
        self.check_world(wid)
        require(isinstance(search,str) and len(search)<=200, "Invalid search")
        if typ:
            require(isinstance(typ,str) and TYPE_PATTERN.fullmatch(typ), "Invalid type")
        sql = """SELECT e.*,
                   (SELECT u.media_id FROM media_uses u
                    WHERE u.entity_id=e.id AND u.role IN ('hero','portrait')
                    ORDER BY CASE u.role WHEN 'hero' THEN 0 ELSE 1 END LIMIT 1)
                   AS hero_media_id
                 FROM entities e JOIN publications p ON p.entity_id=e.id
                 WHERE e.world_id=?"""
        args=[wid]
        if typ:
            sql+=" AND e.type=?"
            args.append(typ)
        if search:
            sql+=" AND (e.title LIKE ? OR e.summary LIKE ? OR e.aliases LIKE ? OR e.body LIKE ?)"
            args.extend(["%"+search+"%"]*4)
        sql+=" ORDER BY e.title COLLATE NOCASE"
        with self.lock:
            return [canonical(row) for row in self.db.execute(sql,args)]

    def public_entity(self, wid, eid):
        require(self.is_published(wid,eid), "Published article not found", 404)
        return self.check_entity(wid,eid)

    def public_relations(self, wid, eid=None):
        self.check_world(wid)
        if eid:
            require(self.is_published(wid,eid), "Published article not found", 404)
        sql = """SELECT r.id,r.world_id,r.source_id,r.target_id,r.predicate,
                        r.status,r.start_year,r.end_year FROM relations r
                 JOIN entities a ON a.id=r.source_id
                 JOIN publications pa ON pa.entity_id=a.id
                 JOIN entities b ON b.id=r.target_id
                 JOIN publications pb ON pb.entity_id=b.id
                 WHERE r.world_id=? AND a.world_id=? AND b.world_id=?"""
        args=[wid,wid,wid]
        if eid:
            sql+=" AND (r.source_id=? OR r.target_id=?)"
            args.extend([eid,eid])
        return self.rows(sql+" ORDER BY r.created_at",args)

    def public_links(self, wid, eid, incoming=False):
        require(self.is_published(wid,eid), "Published article not found", 404)
        target_col="l.source_id" if incoming else "l.target_id"
        where_col="l.target_id" if incoming else "l.source_id"
        return self.rows(f"""SELECT e.id,e.title,e.type FROM content_links l
           JOIN entities e ON e.id={target_col}
           JOIN publications p ON p.entity_id=e.id
           WHERE {where_col}=? AND e.world_id=? ORDER BY e.title""", (eid,wid))

    def public_media(self, wid, eid):
        require(self.is_published(wid,eid), "Published article not found", 404)
        records=self.media_list(wid,eid)
        safe_keys={"id","media_id","use_id","role","caption","title","alt","credit","width","height"}
        return [{k:v for k,v in r.items() if k in safe_keys} for r in records]

    def worlds(self):
        return self.rows("SELECT * FROM worlds ORDER BY created_at,name")

    def create_world(self, data):
        require(isinstance(data, dict) and set(data) <= {"name", "description", "epoch_year"}, "Invalid world payload")
        name = data.get("name")
        require(isinstance(name, str) and 0 < len(name.strip()) <= 150, "Invalid world name")
        desc = data.get("description", "")
        epoch = data.get("epoch_year")
        require(isinstance(desc, str) and len(desc) <= 3000, "Invalid description")
        require(epoch is None or type(epoch) is int and -100000 <= epoch <= 100000, "Invalid epoch")
        wid = str(uuid4())
        with self.lock, self.db:
            self.db.execute("INSERT INTO worlds VALUES(?,?,?,?,?)", (wid, name.strip(), desc, epoch, now()))
        return self.one_world(wid)

    def one_world(self, wid):
        self.check_world(wid)
        return dict(self.one("SELECT * FROM worlds WHERE id=?", (wid,)))

    def update_world(self, wid, data):
        current = self.one_world(wid)
        require(isinstance(data, dict) and set(data) <= {"name", "description", "epoch_year"},
                "Invalid world settings")
        if "name" in data:
            require(isinstance(data["name"], str) and 0 < len(data["name"].strip()) <= 150,
                    "Invalid world name")
            data["name"] = data["name"].strip()
        if "description" in data:
            require(isinstance(data["description"], str) and len(data["description"]) <= 3000,
                    "Invalid world description")
        if "epoch_year" in data:
            require(data["epoch_year"] is None or type(data["epoch_year"]) is int
                    and -100000 <= data["epoch_year"] <= 100000, "Invalid epoch")
        if data:
            with self.lock, self.db:
                self.db.execute("UPDATE worlds SET " + ",".join(k+"=?" for k in data)
                                +" WHERE id=?", (*data.values(),wid))
        return self.one_world(wid)

    def entries(self, wid, search="", typ=None):
        self.check_world(wid)
        sql = "SELECT * FROM entities WHERE world_id=?"
        args = [wid]
        if typ:
            require(TYPE_PATTERN.fullmatch(typ), "Unknown type")
            sql += " AND type=?"
            args.append(typ)
        if search:
            require(len(search) <= 200, "Search too long")
            sql += " AND (title LIKE ? OR aliases LIKE ? OR body LIKE ? OR summary LIKE ?)"
            args += ["%" + search + "%"] * 4
        sql += " ORDER BY title COLLATE NOCASE"
        with self.lock:
            return [canonical(r) for r in self.db.execute(sql, args)]

    def create_entry(self, wid, data, specified_id=None):
        self.check_world(wid)
        data = validate_entity(dict(data))
        eid = specified_id or str(uuid4())
        stamp = now()
        base = dict(id=eid, world_id=wid, type=data["type"], title=data["title"].strip(),
                    aliases=[], summary="", body="", status="working",
                    start_year=None, end_year=None, lat=None, lon=None,
                    theme_id="archive", accent=None, layout=[],
                    created_at=stamp, updated_at=stamp)
        base.update(data)
        for field in ("aliases", "layout"):
            base[field] = json.dumps(base[field], ensure_ascii=False)
        with self.lock, self.db:
            self.db.execute("INSERT INTO entities(" + ",".join(ENTITY_COLUMNS) + ") VALUES(" + ",".join("?" for _ in ENTITY_COLUMNS) + ")",
                            [base[k] for k in ENTITY_COLUMNS])
            self._sync_links(wid, eid, data.get("body", ""))
        return self.check_entity(wid, eid)

    def _sync_links(self, wid, eid, body):
        targets = set(LINK_PATTERN.findall(body))
        if targets:
            placeholders = ",".join("?" for _ in targets)
            valid = {r["id"] for r in self.db.execute(
                "SELECT id FROM entities WHERE world_id=? AND id IN (" + placeholders + ")", (wid, *targets))}
            require(targets == valid, "Article contains links to missing or other-world entries")
        self.db.execute("DELETE FROM content_links WHERE source_id=?", (eid,))
        for target in targets:
            self.db.execute("INSERT INTO content_links(source_id,target_id) VALUES(?,?)", (eid, target))

    def update_entry(self, wid, eid, data):
        current = self.check_entity(wid, eid)
        data = validate_entity(dict(data), partial=True)
        if not data:
            return current
        merged = {**current, **data}
        validate_entity({k: merged[k] for k in ("type", "title", "aliases", "summary", "body", "status", "start_year", "end_year", "lat", "lon", "theme_id", "accent", "layout")})
        data["updated_at"] = now()
        for k in ("aliases", "layout"):
            if k in data:
                data[k] = json.dumps(data[k], ensure_ascii=False)
        with self.lock, self.db:
            self.db.execute("UPDATE entities SET " + ",".join(k + "=?" for k in data) +
                            " WHERE id=? AND world_id=?", (*data.values(), eid, wid))
            if "body" in data:
                self._sync_links(wid, eid, data["body"])
        return self.check_entity(wid, eid)

    def delete_entry(self, wid, eid):
        self.check_entity(wid, eid)
        inbound = self.rows("SELECT source_id FROM content_links WHERE target_id=? AND source_id<>?", (eid, eid))
        rel = self.rows("SELECT id FROM relations WHERE source_id=? OR target_id=?", (eid, eid))
        require(not inbound and not rel, "Entry has incoming references or relationships. Remove or redirect them first.", 409)
        with self.lock, self.db:
            self.db.execute("DELETE FROM content_links WHERE source_id=? AND target_id=?", (eid, eid))
            self.db.execute("DELETE FROM entities WHERE id=? AND world_id=?", (eid, wid))

    def relation_list(self, wid, eid=None):
        self.check_world(wid)
        if eid:
            self.check_entity(wid, eid)
            return self.rows("SELECT * FROM relations WHERE world_id=? AND (source_id=? OR target_id=?) ORDER BY created_at", (wid, eid, eid))
        return self.rows("SELECT * FROM relations WHERE world_id=? ORDER BY created_at", (wid,))

    def create_relation(self, wid, data):
        self.check_world(wid)
        require(isinstance(data, dict) and set(data) <= {"source_id","target_id","predicate","status","start_year","end_year","notes"}, "Invalid relation")
        src, dst = data.get("source_id"), data.get("target_id")
        require(isinstance(src, str) and isinstance(dst, str) and src != dst, "Invalid source/target")
        self.check_entity(wid, src)
        self.check_entity(wid, dst)
        pred = data.get("predicate", "related_to")
        require(isinstance(pred, str) and TYPE_PATTERN.fullmatch(pred), "Invalid relationship type")
        require(data.get("status", "working") in STATUSES, "Invalid relationship status")
        notes = data.get("notes", "")
        require(isinstance(notes, str) and len(notes) <= 5000, "Invalid relationship notes")
        start, end = data.get("start_year"), data.get("end_year")
        for y in (start, end):
            require(y is None or type(y) is int and -100000 <= y <= 100000, "Invalid year")
        require(start is None or end is None or start <= end, "End precedes start")
        if pred.endswith("parent_of"):
            require(not self._is_ancestor(wid, dst, src), "Parentage cycle detected")
        rid = str(uuid4())
        with self.lock, self.db:
            self.db.execute("INSERT INTO relations VALUES(?,?,?,?,?,?,?,?,?,?)",
                            (rid, wid, src, dst, pred, data.get("status", "working"), start, end, notes, now()))
        return dict(self.one("SELECT * FROM relations WHERE id=?", (rid,)))

    def _is_ancestor(self, wid, start, target):
        # Existing directed paths from the prospective child to the proposed parent.
        visited = set()
        pending = [start]
        while pending:
            person = pending.pop()
            if person == target:
                return True
            if person in visited:
                continue
            visited.add(person)
            pending.extend(r["target_id"] for r in self.rows(
                "SELECT target_id FROM relations WHERE world_id=? AND source_id=? AND predicate IN (?,?,?)",
                (wid, person, "biological_parent_of", "adoptive_parent_of", "step_parent_of")))
        return False

    def delete_relation(self, wid, rid):
        self.check_world(wid)
        r = self.one("SELECT * FROM relations WHERE id=? AND world_id=?", (rid, wid))
        require(r, "Relationship not found", 404)
        with self.lock, self.db:
            self.db.execute("DELETE FROM relations WHERE id=? AND world_id=?", (rid, wid))

    def backlinks(self, wid, eid):
        self.check_entity(wid, eid)
        return self.rows("""SELECT e.id,e.title,e.type FROM content_links l
          JOIN entities e ON e.id=l.source_id WHERE l.target_id=? AND e.world_id=? ORDER BY e.title""", (eid, wid))

    def outgoing(self, wid, eid):
        self.check_entity(wid, eid)
        return self.rows("""SELECT e.id,e.title,e.type FROM content_links l
          JOIN entities e ON e.id=l.target_id WHERE l.source_id=? AND e.world_id=? ORDER BY e.title""", (eid, wid))

    def media_uses(self, wid):
        self.check_world(wid)
        return self.rows("""SELECT u.id,u.entity_id,u.media_id,u.role,u.caption,e.title AS entity_title
            FROM media_uses u JOIN entities e ON e.id=u.entity_id
            WHERE u.world_id=? AND e.world_id=? ORDER BY e.title,u.role""", (wid,wid))

    def media_list(self, wid, eid=None):
        self.check_world(wid)
        if eid:
            self.check_entity(wid, eid)
            return self.rows("""SELECT m.*,u.id as use_id,u.media_id,u.role,u.caption FROM media m JOIN media_uses u ON m.id=u.media_id
               WHERE u.world_id=? AND u.entity_id=? ORDER BY m.created_at""", (wid, eid))
        return self.rows("SELECT * FROM media WHERE world_id=? ORDER BY created_at DESC", (wid,))

    def upload_image(self, wid, raw, filename):
        self.check_world(wid)
        require(0 < len(raw) <= MAX_IMAGE, "Image size out of bounds")
        try:
            from PIL import Image, ImageOps, UnidentifiedImageError
        except ImportError as e:
            raise Error("Image uploads need Pillow: pip install -r app/requirements.txt", 503) from e
        Image.MAX_IMAGE_PIXELS = 25_000_000
        try:
            with Image.open(io.BytesIO(raw)) as img:
                require(img.format in ("PNG", "JPEG", "WEBP"), "Only PNG, JPEG and WebP supported")
                require(img.width * img.height <= 25_000_000, "Too many image pixels")
                fmt = img.format
                img.verify()
            with Image.open(io.BytesIO(raw)) as img:
                thumb = ImageOps.exif_transpose(img)
                thumb.thumbnail((640, 640))
                if thumb.mode not in ("RGB", "RGBA"):
                    thumb = thumb.convert("RGB")
                out = io.BytesIO()
                thumb.save(out, format="WEBP", quality=80)
                tw, th = img.size
        except (OSError, ValueError, UnidentifiedImageError) as exc:
            raise Error("Invalid or unsafe image") from exc
        aid = str(uuid4())
        safe_name = Path(filename).name[:180] or "image"
        mime = {"PNG":"image/png","JPEG":"image/jpeg","WEBP":"image/webp"}[fmt]
        suffix = {"PNG":".png","JPEG":".jpg","WEBP":".webp"}[fmt]
        folder = self.media_dir / wid
        folder.mkdir(parents=True, exist_ok=True)
        original, preview = folder / (aid + suffix), folder / (aid + "-preview.webp")
        try:
            original.write_bytes(raw)
            preview.write_bytes(out.getvalue())
            with self.lock, self.db:
                self.db.execute("INSERT INTO media VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                                (aid,wid,safe_name,safe_name,mime,hashlib.sha256(raw).hexdigest(),
                                 tw,th,"","",now()))
        except Exception:
            original.unlink(missing_ok=True)
            preview.unlink(missing_ok=True)
            raise
        return dict(self.one("SELECT * FROM media WHERE id=?", (aid,)))

    def media_file(self, wid, aid, preview=False):
        m = self.one("SELECT * FROM media WHERE world_id=? AND id=?", (wid, aid))
        require(m, "Image not found", 404)
        suffix = {"image/png":".png","image/jpeg":".jpg","image/webp":".webp"}[m["mime"]]
        path = self.media_dir / wid / (aid + ("-preview.webp" if preview else suffix))
        require(path.is_file(), "Image blob missing", 404)
        return path, ("image/webp" if preview else m["mime"])

    def update_media(self, wid, aid, data):
        current = self.one("SELECT * FROM media WHERE world_id=? AND id=?", (wid, aid))
        require(current, "Image not found", 404)
        require(isinstance(data, dict) and set(data) <= {"title", "alt", "credit"}, "Invalid media details")
        for key, value in data.items():
            require(isinstance(value, str) and len(value) <= (250 if key=="title" else 2000), "Invalid media field: "+key)
            if key == "title":
                require(value.strip(), "Image title required")
        if data:
            with self.lock, self.db:
                self.db.execute("UPDATE media SET " + ",".join(k+"=?" for k in data)+" WHERE id=? AND world_id=?",
                                (*data.values(),aid,wid))
        return dict(self.one("SELECT * FROM media WHERE id=?", (aid,)))

    def update_media_use(self, wid, uid, data):
        use = self.one("SELECT * FROM media_uses WHERE id=? AND world_id=?", (uid, wid))
        require(use, "Image placement not found", 404)
        require(isinstance(data, dict) and set(data) <= {"caption"}, "Invalid placement details")
        if "caption" in data:
            require(isinstance(data["caption"],str) and len(data["caption"])<=2000, "Invalid caption")
            with self.lock,self.db:
                self.db.execute("UPDATE media_uses SET caption=? WHERE id=? AND world_id=?",
                                (data["caption"],uid,wid))
        return dict(self.one("SELECT * FROM media_uses WHERE id=?", (uid,)))

    def add_media_use(self, wid, data):
        require(isinstance(data, dict) and set(data) <= {"entity_id","media_id","role","caption"}, "Invalid media use")
        entity = data.get("entity_id")
        self.check_entity(wid, entity)
        media = data.get("media_id")
        require(self.one("SELECT 1 FROM media WHERE world_id=? AND id=?", (wid, media)), "Media not found", 404)
        role = data.get("role", "gallery")
        require(role in {"gallery", "hero", "portrait", "map", "document"}, "Unknown media role")
        caption = data.get("caption", "")
        require(isinstance(caption, str) and len(caption) <= 2000, "Invalid caption")
        uid = str(uuid4())
        with self.lock, self.db:
            try:
                self.db.execute("INSERT INTO media_uses VALUES(?,?,?,?,?,?)", (uid,wid,entity,media,role,caption))
            except sqlite3.IntegrityError as exc:
                raise Error("Image already linked with this role", 409) from exc
        return {"id":uid, "entity_id":entity, "media_id":media, "role":role, "caption":caption}

    def remove_media_use(self, wid, uid):
        require(self.one("SELECT 1 FROM media_uses WHERE id=? AND world_id=?", (uid,wid)), "Image placement not found", 404)
        with self.lock, self.db:
            self.db.execute("DELETE FROM media_uses WHERE id=? AND world_id=?", (uid,wid))

    def import_data(self, payload):
        """Restore a data-only export into a NEW isolated world, atomically.

        Image metadata without original blobs cannot be faithfully restored.
        """
        require(isinstance(payload, dict) and payload.get("format") in ("world-bible-export-v1","world-bible-export-v2"),
                "Unsupported export format")
        source_world = payload.get("world")
        entities = payload.get("entities")
        relations = payload.get("relations")
        require(isinstance(source_world, dict) and isinstance(entities, list) and isinstance(relations, list),
                "Malformed export")
        require(not payload.get("moodboards") and not payload.get("moodboard_items"),
                "Moodboard archives require a full database/media backup",409)
        require(not payload.get("media_metadata") and not payload.get("media_uses"),
                "Export references images. Restore the original .worldbible directory instead.", 409)
        require(len(entities) <= 20000 and len(relations) <= 100000, "Import exceeds limit")
        name = source_world.get("name")
        require(isinstance(name, str) and 0 < len(name.strip()) <= 150, "Invalid imported world name")
        ids = [e.get("id") for e in entities if isinstance(e, dict)]
        require(len(ids) == len(entities) and all(isinstance(x, str) and x for x in ids)
                and len(set(ids)) == len(ids), "Invalid or duplicate entity IDs")
        # Validate parentage as a directed acyclic graph before any writes.
        adjacency = {id_: [] for id_ in ids}
        indegree = {id_: 0 for id_ in ids}
        for rel in relations:
            require(isinstance(rel, dict), "Invalid relationship")
            src, dst = rel.get("source_id"), rel.get("target_id")
            require(src in adjacency and dst in adjacency and src != dst, "Invalid relationship endpoints")
            if rel.get("predicate") in ("biological_parent_of", "adoptive_parent_of", "step_parent_of"):
                adjacency[src].append(dst)
                indegree[dst] += 1
        queue = [id_ for id_, degree in indegree.items() if degree == 0]
        visited = 0
        while queue:
            node = queue.pop()
            visited += 1
            for child in adjacency[node]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)
        require(visited == len(ids), "Imported parentage contains an ancestry cycle")
        old_new = {id_: str(uuid4()) for id_ in ids}
        pub_records = payload.get("publications", [])
        require(isinstance(pub_records,list) and all(isinstance(p,dict) and p.get("entity_id") in old_new
          for p in pub_records),"Invalid publication records")
        require(len(set(p["entity_id"] for p in pub_records))==len(pub_records),"Duplicate publications")
        world_id = str(uuid4())
        epoch = source_world.get("epoch_year")
        require(epoch is None or type(epoch) is int and -100000 <= epoch <= 100000, "Invalid imported epoch")
        with self.lock, self.db:
            self.db.execute("INSERT INTO worlds VALUES(?,?,?,?,?)",
                            (world_id, name + " (Imported)", str(source_world.get("description", ""))[:3000],
                             epoch, now()))
            for e in entities:
                payload_entity = {k:e[k] for k in ("type", "title", "aliases", "summary",
                  "body", "status", "start_year", "end_year", "lat", "lon", "theme_id", "accent", "layout") if k in e}
                require(set(payload_entity) == {"type", "title", "aliases", "summary", "body", "status",
                   "start_year", "end_year", "lat", "lon", "theme_id", "accent", "layout"},
                   "Missing fields in exported entity")
                payload_entity = validate_entity(payload_entity)
                old_id = e["id"]
                def relink(match):
                    target = match.group(1)
                    require(target in old_new, "Export contains an unknown cross-world link")
                    display = match.group(0).split("|", 1)
                    return "[[" + old_new[target] + ("|" + display[1] if len(display) == 2 else "]]")
                payload_entity["body"] = LINK_PATTERN.sub(relink, payload_entity["body"])
                row = dict(id=old_new[old_id], world_id=world_id, **payload_entity,
                           created_at=now(), updated_at=now())
                for key in ("aliases", "layout"):
                    row[key] = json.dumps(row[key], ensure_ascii=False)
                self.db.execute("INSERT INTO entities(" + ",".join(ENTITY_COLUMNS) + ") VALUES("
                                + ",".join("?" for _ in ENTITY_COLUMNS) + ")",
                                [row[k] for k in ENTITY_COLUMNS])
            for e in entities:
                self._sync_links(world_id, old_new[e["id"]], LINK_PATTERN.sub(
                    lambda m: "[[" + old_new[m.group(1)] + ("|" + m.group(0).split("|",1)[1] if "|" in m.group(0) else "]]"),
                    e["body"]))
            for pub in pub_records:
                self.db.execute("INSERT INTO publications(entity_id,published_at) VALUES (?,?)",
                    (old_new[pub["entity_id"]],now()))
            for rel in relations:
                require(isinstance(rel, dict) and rel.get("source_id") in old_new
                        and rel.get("target_id") in old_new, "Invalid imported relationship target")
                require(isinstance(rel.get("predicate"), str) and TYPE_PATTERN.fullmatch(rel["predicate"])
                        and rel.get("status") in STATUSES,
                        "Invalid imported relationship type/status")
                start, end = rel.get("start_year"), rel.get("end_year")
                require(start is None or type(start) is int, "Invalid relation start")
                require(end is None or type(end) is int, "Invalid relation end")
                require(start is None or end is None or start <= end, "Invalid relation period")
                note = rel.get("notes","")
                require(isinstance(note,str) and len(note)<=5000, "Invalid relation notes")
                self.db.execute("INSERT INTO relations VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (str(uuid4()), world_id, old_new[rel["source_id"]], old_new[rel["target_id"]],
                     rel["predicate"], rel["status"], start, end, note, now()))
        if payload.get("format")=="world-bible-export-v2":
            v2_store.import_tables(self,world_id,payload,old_new)
        return {"world": self.one_world(world_id), "entries": len(entities), "relations": len(relations)}

    def export(self, wid):
        with self.lock:
            world = self.one_world(wid)
            entries = [canonical(r) for r in self.db.execute(
                "SELECT * FROM entities WHERE world_id=? ORDER BY id", (wid,))]
            relations = self.relation_list(wid)
            media = self.media_list(wid)
            uses = self.rows("SELECT * FROM media_uses WHERE world_id=?", (wid,))
            boards = self.rows("SELECT * FROM moodboards WHERE world_id=? ORDER BY id",(wid,))
            board_items = self.rows("""SELECT i.* FROM moodboard_items i JOIN moodboards b ON b.id=i.board_id
                        WHERE b.world_id=? ORDER BY i.id""",(wid,))
            published = self.rows("""SELECT p.entity_id,p.published_at FROM publications p
                    JOIN entities e ON e.id=p.entity_id WHERE e.world_id=?""",(wid,))
        return {"format":"world-bible-export-v2","world":world,"entities":entries,
                **v2_store.export_tables(self,wid),
                "relations":relations,"media_metadata":media,"media_uses":uses,
                "moodboards":boards,"moodboard_items":board_items,
                "publications":published,
                "notice":"Image binaries are not included. Back up the .worldbible/media folder separately."}


class Handler(BaseHTTPRequestHandler):
    server_version = "WorldBible/0.1"

    def log_message(self, fmt, *args):
        print("%s %s" % (self.address_string(), fmt % args))

    def reply(self, result, status=200):
        data = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def fail(self, exc):
        try:
            self.reply({"error":exc.message if isinstance(exc,Error) else "Internal server error"},
                       exc.status if isinstance(exc,Error) else 500)
        except (BrokenPipeError, ConnectionResetError):
            pass
        if not isinstance(exc, Error):
            print("Unhandled API exception:", repr(exc))

    def json_body(self):
        length = self.headers.get("Content-Length", "0")
        require(length.isdigit() and int(length) <= MAX_JSON, "JSON body too large")
        try:
            return json.loads(self.rfile.read(int(length)))
        except (ValueError, UnicodeError) as exc:
            raise Error("Invalid JSON body") from exc

    def check_write(self):
        require(self.headers.get("X-World-Bible") == "1", "Missing local write header", 403)
        origin = self.headers.get("Origin")
        if origin:
            from urllib.parse import urlparse
            u = urlparse(origin)
            require(u.scheme in ("http", "https") and u.netloc == self.headers.get("Host"), "Cross-origin write rejected", 403)

    def get_arg(self, q, name):
        v = q.get(name, [None])[0]
        require(v is not None, "Missing parameter: " + name)
        return v

    def do_GET(self):
        try:
            p = urlsplit(self.path)
            route = p.path
            q = parse_qs(p.query)
            s = self.server.store
            if route == "/":
                self.send_response(302)
                self.send_header("Location", "/read/")
                self.end_headers()
                return
            if route.startswith("/read/"):
                rel = route[6:] or "index.html"
                require(rel in ("index.html", "reader.js", "reader.css"), "Asset not found", 404)
                f = ROOT / "reader" / rel
                require(f.is_file(), "Asset not found", 404)
                blob=f.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", mimetypes.guess_type(f.name)[0] or "application/octet-stream")
                self.send_header("Content-Length", str(len(blob)))
                self.send_header("Cache-Control","no-store")
                self.send_header("X-Content-Type-Options","nosniff")
                self.send_header("Content-Security-Policy",
                  "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                  "img-src 'self' https://tile.openstreetmap.org data:; connect-src 'self'; "
                  "object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
                self.end_headers()
                self.wfile.write(blob)
                return
            if route == "/api/v2/types":
                return self.reply(v2_store.types())
            if route == "/api/v2/categories":
                return self.reply(v2_store.categories(s,self.get_arg(q,"world_id")))
            if route == "/api/v2/tags":
                return self.reply(v2_store.tags(s,self.get_arg(q,"world_id")))
            if route == "/api/v2/public/categories":
                return self.reply(v2_store.categories(s,self.get_arg(q,"world_id"),True))
            if route == "/api/v2/public/tags":
                return self.reply(v2_store.tags(s,self.get_arg(q,"world_id"),True))
            if route == "/api/v2/metadata":
                return self.reply(v2_store.classifications(s,self.get_arg(q,"world_id"),self.get_arg(q,"id")))
            if route == "/api/v2/memberships":
                return self.reply(v2_store.memberships(s,self.get_arg(q,"world_id")))
            if route == "/api/v2/public/memberships":
                return self.reply(v2_store.memberships(s,self.get_arg(q,"world_id"),True))
            if route == "/api/v2/public/metadata":
                return self.reply(v2_store.public_metadata(s,self.get_arg(q,"world_id"),self.get_arg(q,"id")))
            if route == "/api/v2/mentions":
                return self.reply(v2_store.mentions(s,self.get_arg(q,"world_id"),self.get_arg(q,"id")))
            if route in ("/api/v2/search","/api/v2/public/search"):
                return self.reply(v2_store.search(s,self.get_arg(q,"world_id"),
                    q.get("search",[""])[0],q.get("type",[None])[0],
                    q.get("category",[None])[0],q.get("tag",[None])[0],
                    route=="/api/v2/public/search",int(q.get("offset",[0])[0])))
            if route == "/api/boards":
                return self.reply(s.boards(self.get_arg(q,"world_id")))
            if route == "/api/board":
                return self.reply(s.board(self.get_arg(q,"world_id"),self.get_arg(q,"id")))
            if route == "/api/public/worlds":
                return self.reply(s.public_worlds())
            if route == "/api/public/entities":
                return self.reply(s.public_entries(self.get_arg(q,"world_id"),
                     q.get("search",[""])[0], q.get("type",[None])[0]))
            if route == "/api/public/entity":
                return self.reply(s.public_entity(self.get_arg(q,"world_id"),self.get_arg(q,"id")))
            if route == "/api/public/relations":
                return self.reply(s.public_relations(self.get_arg(q,"world_id"),
                    q.get("entity_id",[None])[0]))
            if route == "/api/public/backlinks":
                return self.reply(s.public_links(self.get_arg(q,"world_id"),
                    self.get_arg(q,"entity_id"),incoming=True))
            if route == "/api/public/outgoing":
                return self.reply(s.public_links(self.get_arg(q,"world_id"),
                    self.get_arg(q,"entity_id"),incoming=False))
            if route == "/api/public/media":
                return self.reply(s.public_media(self.get_arg(q,"world_id"),
                    self.get_arg(q,"entity_id")))
            if route.startswith("/app/"):
                rel = route[5:] or "index.html"
                require(rel in ("index.html", "app.js", "style.css", "workspaces.css"), "Asset not found", 404)
                f = ROOT / "static" / rel
                require(f.is_file(), "Asset not found", 404)
                data = f.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", mimetypes.guess_type(f.name)[0] or "application/octet-stream")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data: https://tile.openstreetmap.org; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'")
                self.end_headers()
                self.wfile.write(data)
                return
            if route == "/api/publication":
                world=self.get_arg(q,"world_id")
                eid=self.get_arg(q,"id")
                s.check_entity(world,eid)
                return self.reply({"entity_id":eid,"published":s.is_published(world,eid)})
            if route == "/api/worlds":
                return self.reply(s.worlds())
            if route == "/api/entities":
                return self.reply(s.entries(self.get_arg(q,"world_id"), q.get("search",[""])[0], q.get("type",[None])[0]))
            if route == "/api/entity":
                return self.reply(s.check_entity(self.get_arg(q,"world_id"), self.get_arg(q,"id")))
            if route == "/api/relations":
                return self.reply(s.relation_list(self.get_arg(q,"world_id"), q.get("entity_id",[None])[0]))
            if route == "/api/backlinks":
                return self.reply(s.backlinks(self.get_arg(q,"world_id"), self.get_arg(q,"entity_id")))
            if route == "/api/outgoing":
                return self.reply(s.outgoing(self.get_arg(q,"world_id"), self.get_arg(q,"entity_id")))
            if route == "/api/media":
                return self.reply(s.media_list(self.get_arg(q,"world_id"), q.get("entity_id",[None])[0]))
            if route == "/api/media-uses":
                return self.reply(s.media_uses(self.get_arg(q,"world_id")))
            if route == "/api/export":
                return self.reply(s.export(self.get_arg(q,"world_id")))
            if route.startswith("/media/"):
                parts = route.split("/")
                require(len(parts) == 4 and parts[3] and parts[2], "Invalid image URL", 404)
                file, mime = s.media_file(parts[2], parts[3].removesuffix("-preview"), parts[3].endswith("-preview"))
                blob = file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(blob)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Cache-Control", "private, max-age=3600")
                self.end_headers()
                self.wfile.write(blob)
                return
            raise Error("Route not found",404)
        except Exception as exc:
            self.fail(exc)

    def do_POST(self):
        self.mutate("POST")

    def do_PATCH(self):
        self.mutate("PATCH")

    def do_DELETE(self):
        self.mutate("DELETE")

    def mutate(self, verb):
        try:
            self.check_write()
            p=urlsplit(self.path)
            route=p.path
            q=parse_qs(p.query)
            s=self.server.store
            wid=self.get_arg(q,"world_id") if route not in ("/api/worlds","/api/import") else None
            if route=="/api/upload" and verb=="POST":
                count=self.headers.get("Content-Length","0")
                require(count.isdigit() and 0<int(count)<=MAX_IMAGE,"Image body too large")
                raw=self.rfile.read(int(count))
                filename=unquote(self.headers.get("X-File-Name","image"))[:180]
                return self.reply(s.upload_image(wid,raw,filename),201)
            data=self.json_body() if verb in ("POST","PATCH") else {}
            if route=="/api/v2/categories" and verb=="POST":
                return self.reply(v2_store.create_category(s,wid,data),201)
            if route=="/api/v2/tags" and verb=="POST":
                return self.reply(v2_store.create_tag(s,wid,data),201)
            if route=="/api/v2/metadata" and verb=="POST":
                return self.reply(v2_store.update_metadata(s,wid,self.get_arg(q,"id"),data))
            if route=="/api/v2/mentions/approve" and verb=="POST":
                return self.reply(v2_store.decide(s,wid,self.get_arg(q,"id"),data,True))
            if route=="/api/v2/mentions/ignore" and verb=="POST":
                return self.reply(v2_store.decide(s,wid,self.get_arg(q,"id"),data,False))
            if route=="/api/import" and verb=="POST":
                return self.reply(s.import_data(data),201)
            if route=="/api/worlds" and verb=="POST":
                return self.reply(s.create_world(data),201)
            if route=="/api/world" and verb=="PATCH":
                return self.reply(s.update_world(wid,data))
            if route=="/api/boards" and verb=="POST":
                return self.reply(s.create_board(wid,data),201)
            if route=="/api/board":
                bid=self.get_arg(q,"id")
                if verb=="PATCH":return self.reply(s.update_board(wid,bid,data))
                if verb=="DELETE":return self.reply(s.delete_board(wid,bid))
            if route=="/api/board-item":
                bid=self.get_arg(q,"board_id")
                if verb=="POST":return self.reply(s.add_board_item(wid,bid,data),201)
                if verb=="PATCH":return self.reply(s.update_board_item(wid,bid,self.get_arg(q,"id"),data))
                if verb=="DELETE":return self.reply(s.delete_board_item(wid,bid,self.get_arg(q,"id")))
            if route=="/api/publication" and verb=="POST":
                require(isinstance(data,dict) and set(data)=={"published"},"Invalid publication payload")
                return self.reply(s.publication(wid,self.get_arg(q,"id"),data["published"]))
            if route=="/api/entities" and verb=="POST":
                return self.reply(s.create_entry(wid,data),201)
            if route=="/api/entity":
                eid=self.get_arg(q,"id")
                if verb=="PATCH":
                    return self.reply(s.update_entry(wid,eid,data))
                if verb=="DELETE":
                    s.delete_entry(wid,eid)
                    return self.reply({"deleted":eid})
            if route=="/api/relations" and verb=="POST":
                return self.reply(s.create_relation(wid,data),201)
            if route=="/api/relation" and verb=="DELETE":
                s.delete_relation(wid,self.get_arg(q,"id"))
                return self.reply({"ok":True})
            if route=="/api/media" and verb=="PATCH":
                return self.reply(s.update_media(wid,self.get_arg(q,"id"),data))
            if route=="/api/media-use" and verb=="PATCH":
                return self.reply(s.update_media_use(wid,self.get_arg(q,"id"),data))
            if route=="/api/media-use" and verb=="POST":
                return self.reply(s.add_media_use(wid,data),201)
            if route=="/api/media-use" and verb=="DELETE":
                s.remove_media_use(wid,self.get_arg(q,"id"))
                return self.reply({"ok":True})
            raise Error("Route or method not found",404)
        except Exception as exc:
            self.fail(exc)


def serve(path=DB_DEFAULT, port=8765):
    store=Store(path)
    httpd=ThreadingHTTPServer(("127.0.0.1",port),Handler)
    httpd.store=store
    print(f"World Bible running at http://127.0.0.1:{port}/app/ (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
        store.close()


if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--db",default=str(DB_DEFAULT))
    cli.add_argument("--port",type=int,default=8765)
    args=cli.parse_args()
    serve(args.db,args.port)
