"""Export a published-only, standalone reader site.

Usage:
 python app/publish_site.py ./published-site
 python app/publish_site.py ./published-site --world-id <world-uuid>
 python -m http.server 8000 --directory ./published-site

The resulting files need ONLY static hosting; there is no authoring API or draft database.
OSM basemap tiles still use a third-party online provider.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

from server import Store, DB_DEFAULT, LINK_PATTERN

ROOT=Path(__file__).resolve().parent
MEDIA_EXTENSION={"image/jpeg":".jpg","image/png":".png","image/webp":".webp"}


def build_site(store: Store, world_id: str, destination: Path) -> dict:
    destination=Path(destination).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Destination must be empty; refusing to overwrite an existing website")
    world=store.one_world(world_id)
    records=store.public_entries(world_id)
    if not records:
        raise ValueError("No published entries. Publish at least one article in the Studio first.")
    ids={e["id"] for e in records}

    # Fail closed when a public article contains explicit ID links to a draft.
    for e in records:
        targets={m.group(1) for m in LINK_PATTERN.finditer(e["body"])}
        if not targets.issubset(ids):
            raise ValueError("Published article has links to unpublished entries: "+e["title"])

    relationships=store.public_relations(world_id)
    media_by_entity={}
    links={}
    assets={}
    for e in records:
        eid=e["id"]
        media_by_entity[eid]=store.public_media(world_id,eid)
        links[eid]={
            "incoming":store.public_links(world_id,eid,incoming=True),
            "outgoing":store.public_links(world_id,eid,incoming=False),
        }
        for attached in media_by_entity[eid]:
            media_id=attached["media_id"]
            if media_id in assets:
                continue
            info=store.one("SELECT mime,sha256 FROM media WHERE id=? AND world_id=?",(media_id,world_id))
            if not info or info["mime"] not in MEDIA_EXTENSION:
                raise ValueError("Unsupported or missing published media: "+media_id)
            original,mime=store.media_file(world_id,media_id,preview=False)
            preview,_=store.media_file(world_id,media_id,preview=True)
            if hashlib.sha256(original.read_bytes()).hexdigest()!=info["sha256"]:
                raise ValueError("Published original image checksum mismatch: "+media_id)
            assets[media_id]={"extension":MEDIA_EXTENSION[mime],
                              "original":original,"preview":preview}

    payload={
        "format":"world-bible-static-publication-v1",
        "world":world,
        "entities":records,
        "relations":relationships,
        "media_by_entity":media_by_entity,
        "links":links,
        "assets":{id:{"extension":item["extension"]} for id,item in assets.items()},
    }

    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent,prefix=".publication-") as tmp:
        staging=Path(tmp)
        source=(ROOT/"reader"/"index.html").read_text(encoding="utf-8")
        source=source.replace('<meta charset="utf-8">','<meta charset="utf-8"><meta name="worldbible-static" content="true">')
        for old,new in (('/read/reader.css','reader.css'),('/read/reader.js','reader.js')):
            if old not in source:
                raise ValueError("Reader template path missing: "+old)
            source=source.replace(old,new)
        (staging/"index.html").write_text(source,encoding="utf-8")
        for filename in ("reader.js","reader.css"):
            shutil.copyfile(ROOT/"reader"/filename, staging/filename)
        (staging/"site-data.json").write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
        image_dir=staging/"media"
        image_dir.mkdir()
        for id,item in assets.items():
            shutil.copyfile(item["original"],image_dir/(id+item["extension"]))
            shutil.copyfile(item["preview"],image_dir/(id+"-preview.webp"))
        if destination.exists():
            destination.rmdir()
        os.replace(staging,destination)
    return {"world":world["name"],"published_entries":len(records),
            "relationships":len(relationships),"media_assets":len(assets),
            "path":str(destination)}


def main():
    cli=argparse.ArgumentParser(description="Create a public-safe, reader-only static website")
    cli.add_argument("output",help="Empty directory for static published website")
    cli.add_argument("--db",default=str(DB_DEFAULT))
    cli.add_argument("--world-id",help="World UUID; required when multiple worlds have published entries")
    args=cli.parse_args()
    store=Store(args.db)
    try:
        choices=store.public_worlds()
        if args.world_id:
            chosen=next((w for w in choices if w["id"]==args.world_id),None)
            if chosen is None:
                raise ValueError("No published entries exist for the chosen world")
        elif len(choices)==1:
            chosen=choices[0]
        elif not choices:
            raise ValueError("No worlds have published entries yet")
        else:
            raise ValueError("Multiple worlds have published entries; supply --world-id")
        print(json.dumps(build_site(store,chosen["id"],Path(args.output)),indent=2))
    finally:
        store.close()


if __name__=="__main__":
    main()
