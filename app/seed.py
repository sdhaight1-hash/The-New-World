"""Import existing The New World references AND distinct, linked canon entries.

Idempotent, deterministic stable IDs, no overwrites of edited records.
The original Markdown stays intact; chronology remains explicitly provisional.
Usage: python app/seed.py [--db PATH]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

from curate import cleanup_legacy
from uuid import uuid5, NAMESPACE_URL

from server import Store, DB_DEFAULT

ROOT = Path(__file__).resolve().parent.parent
WORLD_ID = str(uuid5(NAMESPACE_URL, "the-new-world/initial-workspace"))
KIND = {"regions": "place", "bible": "subject"}
# Only documents about the world are source material for encyclopedia entries.
# UX, software design, research TODOs and system architecture stay in GitHub.
WORLD_SOURCE_PATHS = {
    "bible/01-chronology.md",
    "bible/02-great-plague.md",
    "bible/03-cascade.md",
    "bible/04-technology.md",
    "bible/05-successor-societies.md",
    "bible/20-brief-age-of-ai.md",
    "bible/21-real-world-2019-2026.md",
    "history/00-world-2018-2026.md",
    "history/01-western-hemisphere-2018-2026.md",
    "history/02-united-states-2018-2026.md",
    "history/03-western-united-states-2018-2026.md",
    "history/04-california-2018-2026.md",
    "history/05-oregon-2018-2026.md",
    "history/06-wyoming-2018-2026.md",
    "history/07-southern-california-local-2018-2026.md",
    "history/08-clatsop-local-2018-2026.md",
    "history/09-wyoming-local-2018-2026.md",
    "history/10-big-bear-valley-2018-2026.md",
    "history/11-victor-valley-2018-2026.md",
    "regions/southern-california.md",
    "regions/clatsop-county.md",
    "regions/wyoming.md",
}

EVENTS = {"02-great-plague.md", "03-cascade.md"}
INDEX = ROOT / "discovery" / "index.json"
CANON = ROOT / "canon" / "entries.json"

# These are APPROXIMATE Cascade-relative time ranges, not fixed Gregorian dates.
SOURCE_EVENT_DETAILS = {
    "bible/02-great-plague.md": {
        "summary": "Globally devastating epidemic before the Cascade; uneven regional mortality and migration.",
        "start_year": -5, "end_year": -2, "theme_id": "chronicle", "status": "established",
    },
    "bible/03-cascade.md": {
        "summary": "Exceptional solar disturbances begin around provisional Year 0; prolonged infrastructure crisis follows.",
        "start_year": 0, "end_year": 0, "theme_id": "chronicle", "status": "established",
    },
}
# Regional source pages describe areas, not named characters or future factions.
REGION_SOURCE_ALIASES = {
    "regions/southern-california.md": ["Southern California regional study"],
    "regions/clatsop-county.md": ["Northern Oregon coast study"],
    "regions/wyoming.md": ["Wyoming regional study"],
}


def source_id(relative: str) -> str:
    return str(uuid5(NAMESPACE_URL, "the-new-world/article/" + relative))


def canon_id(key: str) -> str:
    return str(uuid5(NAMESPACE_URL, "the-new-world/canon/" + key))


def base_text(entry: dict) -> str:
    """No fabricated canon or implicit publication in seed prose."""
    return (
        entry["body"].strip() + "\n\n"
        "## Record provenance\n\n"
        f"Source reference: `{entry['source']}`. "
        f"Canon status: **{entry.get('status', 'working')}**. "
        "Documented geography is distinct from hypothetical future history. "
        "Dates, borders, people and population estimates not established in the source remain open."
    )


def load_canon() -> dict:
    data = json.loads(CANON.read_text(encoding="utf-8"))
    if data.get("format") != "world-bible-canon-seed-v1":
        raise ValueError("Unsupported canon manifest")
    entries, relations = data.get("entries"), data.get("relations")
    if not isinstance(entries, list) or not isinstance(relations, list):
        raise ValueError("Invalid canon manifest")
    keys = [item["key"] for item in entries]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate canon keys")
    known = set(keys)
    for item in entries:
        if item["source"] not in WORLD_SOURCE_PATHS:
            raise ValueError(f"Non-world source rejected: {item['source']}")
        if not (ROOT / item["source"]).is_file():
            raise ValueError(f"Missing source for {item['key']}: {item['source']}")
        if item.get("reuse_source") and item["reuse_source"] != item["source"]:
            raise ValueError("Reused source must match source reference")
    for relation in relations:
        if relation["source"] not in known or relation["target"] not in known:
            raise ValueError("Relationship references an undefined canon entry")
        if relation["source"] == relation["target"]:
            raise ValueError("Reflexive relationship")
    return data


def linked_body(entry: dict, manifest: dict, ids: dict) -> str:
    """Reconstruct the exact auto-generated body used by previous imports."""
    adjacent = set()
    for relation in manifest["relations"]:
        if relation["source"] == entry["key"]:
            adjacent.add(relation["target"])
        if relation["target"] == entry["key"]:
            adjacent.add(relation["source"])
    titles = {item["key"]: item["title"] for item in manifest["entries"]}
    links = [
        f"[[{ids[key]}|{titles[key]}]]" for key in sorted(adjacent)
    ]
    links.append(f"[[{source_id(entry['source'])}|Original source document]]")
    return (
        base_text(entry)
        + "\n\n## Related records and original source\n\n"
        + "\n".join("- " + link for link in links)
    )


def update_generated_legacy_source_link(store: Store, manifest: dict, ids: dict) -> int:
    """Remove erroneous link to the product's editorial ledger if unmodified.

    Never rewrite a published article or a human-edited body.
    """
    article = next(e for e in manifest["entries"] if e["key"] == "reference-present")
    old = {**article, "source": "bible/00-foundations.md"}
    eid = ids[article["key"]]
    existing = store.check_entity(WORLD_ID, eid)
    if (
        existing["body"] == linked_body(old, manifest, ids)
        and not store.is_published(WORLD_ID, eid)
    ):
        store.update_entry(WORLD_ID, eid, {"body": linked_body(article, manifest, ids)})
        return 1
    return 0


def seed(path=DB_DEFAULT):
    """Create missing records, preserving all existing edits and publication choices."""
    manifest = load_canon()  # Fail before any DB changes if the manifest is invalid.
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
            for item in registry.get("entries", []):
                alias_by_path[item["path"]] = item.get("aliases", [])

        added_docs = added_canon = skipped = related = 0
        # Preserve the original source Markdown VERBATIM as research/reference pages.
        for relative in sorted(WORLD_SOURCE_PATHS):
                file = ROOT / relative
                eid = source_id(relative)
                if store.one("SELECT 1 FROM entities WHERE id=?", (eid,)):
                    skipped += 1
                    continue
                body = file.read_text(encoding="utf-8")
                title = next((line.removeprefix("# ").strip()
                              for line in body.splitlines() if line.startswith("# ")), file.stem)
                typ = "event" if file.name in EVENTS else ("place" if relative.startswith("regions/") else "subject")
                aliases = REGION_SOURCE_ALIASES.get(relative, alias_by_path.get(relative, []))
                properties = {
                    "title": title, "type": typ, "body": body,
                    "status": "working", "aliases": aliases,
                    **({"status": "established", "theme_id": "chronicle"} if relative.startswith("history/") else {}),
                    **SOURCE_EVENT_DETAILS.get(relative, {}),
                }
                store.create_entry(WORLD_ID, properties, specified_id=eid)
                added_docs += 1

        ids = {e["key"]:source_id(e["reuse_source"]) if e.get("reuse_source") else canon_id(e["key"])
               for e in manifest["entries"]}
        # Source event pages are authoritative: do not create second 'The Great Plague' or Cascade article.
        for entry in manifest["entries"]:
            if entry.get("reuse_source"):
                continue
            eid = ids[entry["key"]]
            if store.one("SELECT 1 FROM entities WHERE id=? AND world_id=?", (eid, WORLD_ID)):
                skipped += 1
                continue
            properties = {
                k: entry[k] for k in (
                    "type", "title", "summary", "status", "aliases",
                    "start_year", "end_year", "theme_id"
                ) if k in entry
            }
            properties["body"] = base_text(entry)
            store.create_entry(WORLD_ID, properties, specified_id=eid)
            added_canon += 1

        # Add generated links only to untouched, newly seeded page templates.
        for entry in manifest["entries"]:
            if entry.get("reuse_source"):
                continue
            eid = ids[entry["key"]]
            existing = store.check_entity(WORLD_ID, eid)
            if existing["body"] == base_text(entry):
                store.update_entry(WORLD_ID, eid, {
                    "body": linked_body(entry, manifest, ids)
                })

        repaired_links = update_generated_legacy_source_link(store, manifest, ids)

        # Publish the initial, source-backed reading shelf once. Existing worlds with
        # editorial publications are left alone, as are subsequent manual unpublishes.
        # This is local reader visibility, not a deployment or remote upload.
        with store.lock, store.db:
            store.db.execute("""CREATE TABLE IF NOT EXISTS seed_migrations (
                name TEXT PRIMARY KEY
            )""")
            migration = "starter_reader_publications_v1"
            first_run = not store.db.execute(
                "SELECT 1 FROM seed_migrations WHERE name=?", (migration,)
            ).fetchone()
            published_starters = 0
            if first_run:
                already_published = store.db.execute("""SELECT 1 FROM publications p
                    JOIN entities e ON e.id=p.entity_id
                    WHERE e.world_id=? LIMIT 1""", (WORLD_ID,)).fetchone()
                if not already_published:
                    for relative in sorted(WORLD_SOURCE_PATHS):
                        # The curated source documents carry their own provenance.
                        # Generated/working canon entries still require review.
                        eid = source_id(relative)
                        if store.db.execute(
                            "SELECT 1 FROM entities WHERE id=? AND world_id=?", (eid, WORLD_ID)
                        ).fetchone():
                            store.db.execute(
                                "INSERT OR IGNORE INTO publications(entity_id,published_at) VALUES (?,?)",
                                (eid, datetime.now(timezone.utc).isoformat())
                            )
                            published_starters += 1
                store.db.execute("INSERT INTO seed_migrations(name) VALUES (?)", (migration,))

        # Deterministic relationship identity. Existing user-edited relationships are untouched.
        for relation in manifest["relations"]:
            src,dst=ids[relation["source"]],ids[relation["target"]]
            pred=relation["predicate"]
            if store.one("""SELECT 1 FROM relations
                WHERE world_id=? AND source_id=? AND target_id=? AND predicate=?""",
                (WORLD_ID,src,dst,pred)):
                continue
            store.create_relation(WORLD_ID, {
                "source_id":src, "target_id":dst,"predicate":pred,
                "status":relation.get("status","working"),
                "notes":"Source-grounded relationship from canon/entries.json; review original cited records."
            })
            related += 1

        removed, protected, archive = cleanup_legacy(
            store, ROOT, Path(path), WORLD_ID, source_id,
            WORLD_SOURCE_PATHS, alias_by_path
        )
        print(
            f"Seed complete: {added_docs} world source documents, {added_canon} distinct canon records, "
            f"{related} relationships added; {skipped} existing records preserved; "
            f"{removed} non-world documents removed; {repaired_links} old source links repaired; "
            f"{published_starters} starter reader articles published. "
            f"World ID: {WORLD_ID}"
        )
        if archive:
            print(f"Pre-cleanup full backup: {archive}")
        if protected:
            print("Protected edited, published or referenced non-world entries; manual review needed: "
                  + ", ".join(protected))
    finally:
        store.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB_DEFAULT))
    args = parser.parse_args()
    seed(args.db)
