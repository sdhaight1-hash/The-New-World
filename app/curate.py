"""Remove previous software/editorial documents accidentally seeded as world lore.

Never removes a manually changed or published record. Back up the complete
database and media library before any deletion. Reusable for other world
projects by supplying the canonical source whitelist and world ID.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from backup import make_backup


def legacy_paths(root: Path, whitelisted: set[str]) -> list[str]:
    return sorted(
        file.relative_to(root).as_posix()
        for file in (root / "bible").glob("*.md")
        if file.relative_to(root).as_posix() not in whitelisted
    )


def cleanup_legacy(
    store, root: Path, db_path: Path, world_id: str, source_id,
    whitelisted: set[str], alias_by_path: dict
) -> tuple[int, list[str], str | None]:
    """Delete only unmodified documents from the old wildcard Markdown import.

    Protect author changes, publications, relationships, links and media uses.
    Return (removed_count, protected_paths, snapshot_archive).
    """
    candidates = []
    protected = []
    for relative in legacy_paths(root, whitelisted):
        eid = source_id(relative)
        if not store.one(
            "SELECT 1 FROM entities WHERE id=? AND world_id=?", (eid, world_id)
        ):
            continue

        entity = store.check_entity(world_id, eid)
        file = root / relative
        original = file.read_text(encoding="utf-8")
        title = next(
            (line[2:].strip() for line in original.splitlines() if line.startswith("# ")),
            file.stem
        )
        unchanged = (
            entity["title"] == title
            and entity["type"] == "subject"
            and entity["body"] == original
            and entity["aliases"] == alias_by_path.get(relative, [])
            and entity["summary"] == ""
            and entity["status"] == "working"
            and entity["start_year"] is None
            and entity["end_year"] is None
            and entity["lat"] is None
            and entity["lon"] is None
            and entity["theme_id"] == "archive"
            and entity["accent"] is None
            and entity["layout"] == []
        )
        in_use = any((
            store.one(
                "SELECT 1 FROM content_links WHERE target_id=? AND source_id<>?",
                (eid, eid)
            ),
            store.one(
                "SELECT 1 FROM relations WHERE source_id=? OR target_id=?", (eid, eid)
            ),
            store.one("SELECT 1 FROM publications WHERE entity_id=?", (eid,)),
            store.one("SELECT 1 FROM media_uses WHERE entity_id=?", (eid,)),
            store.one("SELECT 1 FROM moodboards WHERE entity_id=?", (eid,)),
            store.one("SELECT 1 FROM moodboard_items WHERE entity_id=?", (eid,)),
        ))
        if unchanged and not in_use:
            candidates.append(eid)
        else:
            protected.append(relative)

    if not candidates:
        return 0, protected, None

    db_path = Path(db_path)
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    archive = backup_dir / (
        "before-lore-cleanup-"
        + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
        + ".zip"
    )
    make_backup(db_path, archive)

    # Entire deletion is transactional. If there is an unexpected reference
    # or any other SQLite error, it rolls back with no partially removed pages.
    with store.lock, store.db:
        for eid in candidates:
            if store.db.execute(
                "SELECT 1 FROM content_links WHERE target_id=? AND source_id<>?",
                (eid, eid)
            ).fetchone():
                raise RuntimeError("New reference to legacy document; cleanup aborted")
            store.db.execute("DELETE FROM content_links WHERE source_id=?", (eid,))
            store.db.execute(
                "DELETE FROM entities WHERE id=? AND world_id=?", (eid, world_id)
            )
    return len(candidates), protected, str(archive)
