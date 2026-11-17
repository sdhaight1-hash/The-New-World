"""Import this repository's existing Markdown into the reusable world-bible core.

Usage: python app/seed.py [--db PATH]
Idempotent: existing records are never overwritten. No test people or factions are invented.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from server import Store, DB_DEFAULT

ROOT = Path(__file__).resolve().parent.parent
WORLD_ID = str(uuid5(NAMESPACE_URL, "the-new-world/initial-workspace"))
KIND = {"regions": "place", "bible": "subject"}
EVENTS = {"02-great-plague.md", "03-cascade.md"}
INDEX = ROOT / "discovery" / "index.json"


def seed(path=DB_DEFAULT):
    store = Store(path)
    try:
        if not store.one("SELECT id FROM worlds WHERE id=?", (WORLD_ID,)):
            with store.lock, store.db:
                store.db.execute("INSERT INTO worlds VALUES (?,?,?,?,?)",
                    (WORLD_ID, "The New World",
                     "Realistic post-Plague, post-Cascade alternate-history Earth; historical year zero is provisional.",
                     None, "2026-11-16T00:00:00+00:00"))
        alias_by_path = {}
        if INDEX.exists():
            registry = json.loads(INDEX.read_text(encoding="utf-8"))
            for e in registry.get("entries", []):
                alias_by_path[e["path"]] = e.get("aliases", [])
        added = skipped = 0
        for folder in ("bible", "regions"):
            for path in sorted((ROOT / folder).glob("*.md")):
                relative = path.relative_to(ROOT).as_posix()
                eid = str(uuid5(NAMESPACE_URL, "the-new-world/article/" + relative))
                if store.one("SELECT 1 FROM entities WHERE id=?", (eid,)):
                    skipped += 1
                    continue
                body = path.read_text(encoding="utf-8")
                title = next((line.removeprefix("# ").strip() for line in body.splitlines() if line.startswith("# ")), path.stem)
                typ = "event" if path.name in EVENTS else KIND[folder]
                # All Markdown is preserved verbatim. Current articles aren't silently rewritten as facts.
                store.create_entry(WORLD_ID, {
                    "title": title,
                    "type": typ,
                    "body": body,
                    "status": "working",
                    "aliases": alias_by_path.get(relative, []),
                }, specified_id=eid)
                added += 1
        print(f"Seed complete: {added} entries imported, {skipped} already present. World ID: {WORLD_ID}")
    finally:
        store.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=str(DB_DEFAULT))
    args = p.parse_args()
    seed(args.db)
