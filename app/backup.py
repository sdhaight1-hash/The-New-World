"""Create and restore portable, verified backups of a complete World Bible Studio.

Includes a consistent SQLite snapshot AND all media binaries.
Stop the local server before RESTORING. Backup uses SQLite's online backup API.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / ".worldbible" / "worlds.sqlite3"
MAX_ARCHIVE_FILES = 100_000
MAX_UNPACKED_BYTES = 5_000_000_000


def digest(data: bytes):
    return hashlib.sha256(data).hexdigest()


def make_backup(db_path: Path, output: Path) -> dict:
    db_path = Path(db_path)
    output = Path(output)
    if not db_path.is_file():
        raise ValueError("Database not found. Start and seed the studio first.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        snapshot = Path(d) / "database.sqlite3"
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as source:
            with sqlite3.connect(snapshot) as target:
                source.backup(target)
                check = target.execute("PRAGMA integrity_check").fetchone()[0]
                if check != "ok":
                    raise ValueError("Database integrity check failed: " + check)
        files = {"database.sqlite3": snapshot.read_bytes()}
        media = db_path.parent / "media"
        if media.exists():
            for path in sorted(media.rglob("*")):
                if path.is_symlink():
                    raise ValueError("Refusing symbolic link in media library")
                if path.is_file():
                    rel = "media/" + path.relative_to(media).as_posix()
                    if len(files) >= MAX_ARCHIVE_FILES:
                        raise ValueError("Too many media files")
                    files[rel] = path.read_bytes()
        manifest = {
            "format": "world-bible-complete-backup-v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "files": {name: {"size":len(data), "sha256":digest(data)} for name,data in files.items()},
        }
        tmp_zip = output.with_suffix(output.suffix + ".tmp")
        try:
            with zipfile.ZipFile(tmp_zip, "w", compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=5) as archive:
                for name, data in files.items():
                    archive.writestr(name, data)
                archive.writestr("manifest.json", json.dumps(manifest, indent=2))
            os.replace(tmp_zip, output)
        finally:
            tmp_zip.unlink(missing_ok=True)
    return {"files":len(files), "bytes":sum(len(v) for v in files.values()),
            "archive":str(output.resolve())}


def restore_backup(archive_path: Path, db_path: Path, force=False) -> dict:
    archive_path, db_path = Path(archive_path), Path(db_path)
    target_dir = db_path.parent
    if db_path.name != "worlds.sqlite3":
        raise ValueError("Restore target database filename must be worlds.sqlite3")
    if target_dir.exists() and any(target_dir.iterdir()) and not force:
        raise ValueError("Target data directory is not empty; use --force after stopping the server")
    with zipfile.ZipFile(archive_path, "r") as archive:
        names = archive.namelist()
        if len(names) > MAX_ARCHIVE_FILES + 2 or len(set(names)) != len(names):
            raise ValueError("Too many or duplicated archive members")
        if "manifest.json" not in names or "database.sqlite3" not in names:
            raise ValueError("Missing archive manifest or database")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("format") != "world-bible-complete-backup-v1":
            raise ValueError("Unsupported backup format")
        expected = manifest.get("files", {})
        if not isinstance(expected, dict) or set(expected) != set(names)-{"manifest.json"}:
            raise ValueError("Backup manifest and archive contents disagree")
        total = 0
        for info in archive.infolist():
            member = PurePosixPath(info.filename)
            if info.filename == "manifest.json":
                continue
            if (member.is_absolute() or ".." in member.parts or
                not (info.filename=="database.sqlite3" or
                     len(member.parts)>=2 and member.parts[0]=="media")):
                raise ValueError("Unsafe path in backup")
            if info.is_dir():
                raise ValueError("Unexpected directory entry")
            total += info.file_size
            if total > MAX_UNPACKED_BYTES:
                raise ValueError("Backup exceeds unpacked size limit")
            record = expected.get(info.filename)
            if (not isinstance(record, dict) or
                record.get("size") != info.file_size):
                raise ValueError("Incorrect file size in manifest")
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=target_dir.parent, prefix=".wb-restore-") as staging_name:
            staging = Path(staging_name)
            for name in expected:
                data = archive.read(name)
                if digest(data) != expected[name]["sha256"]:
                    raise ValueError("SHA-256 verification failed: " + name)
                destination = staging / name
                if name == "database.sqlite3":
                    destination = staging / "worlds.sqlite3"
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
            with sqlite3.connect(staging/"worlds.sqlite3") as test:
                if test.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("Restored SQLite database is corrupt")
            prior = None
            if target_dir.exists() and any(target_dir.iterdir()):
                prior = target_dir.with_name(target_dir.name+".previous-"+datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"))
                if prior.exists():
                    raise ValueError("Previous backup directory collision")
                os.replace(target_dir, prior)
            elif target_dir.exists():
                target_dir.rmdir()
            try:
                os.replace(staging, target_dir)
            except Exception:
                if prior is not None:
                    os.replace(prior, target_dir)
                raise
    return {"restored_to": str(target_dir.resolve()), "files":len(expected)}


def main():
    cli = argparse.ArgumentParser(description="World Bible complete archive backup/restore")
    cli.add_argument("operation", choices=["create", "restore"])
    cli.add_argument("archive", help="Path to .zip backup archive")
    cli.add_argument("--db", default=str(DEFAULT_DB), help="Target/source SQLite file path")
    cli.add_argument("--force", action="store_true", help="Move existing data directory to a dated .previous backup before restore")
    args = cli.parse_args()
    if args.operation == "create":
        result = make_backup(Path(args.db), Path(args.archive))
    else:
        result = restore_backup(Path(args.archive), Path(args.db), force=args.force)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
