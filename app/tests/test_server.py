import io
import json
import sqlite3
from unittest.mock import patch
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import backup
from server import Store, Handler, Error
from backup import make_backup, restore_backup
from publish_site import build_site


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "test.sqlite3")
        self.a = self.store.create_world({"name": "World A", "epoch_year": 2035})["id"]
        self.b = self.store.create_world({"name": "World B"})["id"]

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def add(self, world, title, typ="person", **kwargs):
        return self.store.create_entry(world, {"title": title, "type": typ, **kwargs})

    def test_world_isolation_and_search(self):
        a = self.add(self.a, "Northwind", "place", summary="A distant settlement")
        b = self.add(self.b, "Northwind", "place")
        self.assertNotEqual(a["id"], b["id"])
        self.assertEqual(len(self.store.entries(self.a, "distant")), 1)
        self.assertEqual(len(self.store.entries(self.b, "distant")), 0)
        with self.assertRaises(Error):
            self.store.check_entity(self.a, b["id"])
        with self.assertRaises(Error):
            self.store.create_relation(self.a, {"source_id": a["id"], "target_id": b["id"]})

    def test_stable_links_backlinks_rename_and_delete(self):
        source = self.add(self.a, "Archive")
        target = self.add(self.a, "Oldname")
        text = "See [[" + target["id"] + "|Oldname]] for details."
        self.store.update_entry(self.a, source["id"], {"body": text})
        self.assertEqual(self.store.backlinks(self.a, target["id"])[0]["id"], source["id"])
        self.store.update_entry(self.a, target["id"], {"title": "Newname"})
        self.assertEqual(self.store.outgoing(self.a, source["id"])[0]["title"], "Newname")
        with self.assertRaises(Error) as cm:
            self.store.delete_entry(self.a, target["id"])
        self.assertEqual(cm.exception.status, 409)
        self.store.update_entry(self.a, source["id"], {"body": "No external link."})
        self.store.delete_entry(self.a, target["id"])
        self.assertEqual(self.store.backlinks(self.a, source["id"]), [])

    def test_unknown_and_cross_world_links_rejected_without_changing_existing_body(self):
        source = self.add(self.a, "Archive", body="Original")
        other = self.add(self.b, "Other")
        for target in ("not-real-id", other["id"]):
            with self.assertRaises(Error):
                self.store.update_entry(self.a, source["id"], {"body": "[[" + target + "|Other]]"})
        self.assertEqual(self.store.check_entity(self.a, source["id"])["body"], "Original")

    def test_parentage_cycle(self):
        p = self.add(self.a, "Parent")
        c = self.add(self.a, "Child")
        self.store.create_relation(self.a, {"source_id": p["id"], "target_id": c["id"], "predicate": "biological_parent_of"})
        with self.assertRaises(Error):
            self.store.create_relation(self.a, {"source_id": c["id"], "target_id": p["id"], "predicate": "adoptive_parent_of"})
        self.assertEqual(len(self.store.relation_list(self.a)), 1)

    def test_years_coordinates_and_design_validated(self):
        a = self.add(self.a, "Valley", "place", start_year=1, end_year=50, lat=34.25, lon=-116.9,
                     theme_id="atlas", layout=["body", "map"])
        self.assertEqual(a["layout"], ["body", "map"])
        for payload in ({"lat": 999}, {"start_year": 51, "end_year": 2},
                        {"accent": "expression(alert(1))"}, {"layout": ["body", "body"]},
                        {"theme_id": "not-a-preset"}, {"body": 55}):
            with self.assertRaises(Error):
                self.store.update_entry(self.a, a["id"], payload)
        self.assertEqual(self.store.check_entity(self.a, a["id"])["title"], "Valley")

    def test_media_reuse(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow absent")
        f = io.BytesIO()
        Image.new("RGB", (10, 12), (100, 140, 170)).save(f, "PNG")
        media = self.store.upload_image(self.a, f.getvalue(), "test.png")
        x = self.add(self.a, "Person")
        y = self.add(self.a, "Location", "place")
        self.store.add_media_use(self.a, {"entity_id":x["id"], "media_id":media["id"], "role":"portrait"})
        self.store.add_media_use(self.a, {"entity_id":y["id"], "media_id":media["id"], "role":"gallery"})
        self.assertEqual(len(self.store.media_list(self.a, x["id"])), 1)
        self.assertEqual(len(self.store.media_list(self.a, y["id"])), 1)
        self.assertTrue(self.store.media_file(self.a, media["id"], True)[0].is_file())
        with self.assertRaises(Error):
            self.store.add_media_use(self.b, {"entity_id":self.add(self.b, "B")["id"],
                                               "media_id":media["id"]})

    def test_archive_roundtrip_isolated_and_stable(self):
        author = self.add(self.a, "Author")
        town = self.add(self.a, "Harbor", "place")
        self.store.update_entry(self.a, author["id"], {"body":"Lived at [[" + town["id"] + "|Harbor]]."})
        self.store.create_relation(self.a, {"source_id":author["id"],
                     "target_id":town["id"],"predicate":"resided_in"})
        export = self.store.export(self.a)
        result = self.store.import_data(export)
        new_world = result["world"]["id"]
        self.assertNotEqual(new_world, self.a)
        imported = self.store.entries(new_world)
        self.assertEqual(len(imported), 2)
        i_author = next(e for e in imported if e["title"] == "Author")
        i_town = next(e for e in imported if e["title"] == "Harbor")
        self.assertNotEqual(i_town["id"], town["id"])
        self.assertIn("[[" + i_town["id"] + "|Harbor]]", i_author["body"])
        self.assertEqual(self.store.backlinks(new_world, i_town["id"])[0]["id"], i_author["id"])
        self.assertEqual(len(self.store.relation_list(new_world)), 1)
        self.assertEqual(self.store.check_entity(self.a, town["id"])["title"], "Harbor")

    def test_no_truncated_world_export(self):
        with self.store.lock, self.store.db:
            for idx in range(505):
                self.store.db.execute(
                    "INSERT INTO entities VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (f"test-{idx}",self.a,"subject",f"Topic {idx}","[]","","","working",
                     None,None,None,None,"archive",None,"[]","now","now"))
        self.assertEqual(len(self.store.entries(self.a)), 505)
        self.assertEqual(len(self.store.export(self.a)["entities"]), 505)

    def test_import_rejects_media_manifest_without_binaries(self):
        e = self.add(self.a, "A")
        archive = self.store.export(self.a)
        archive["media_metadata"] = [{"id":"image-without-binary"}]
        with self.assertRaises(Error) as ctx:
            self.store.import_data(archive)
        self.assertEqual(ctx.exception.status, 409)

    def test_world_settings_persist_and_isolate(self):
        self.store.update_world(self.a, {"name":"Changed World","description":"New description","epoch_year":2040})
        a = self.store.one_world(self.a)
        self.assertEqual(a["epoch_year"], 2040)
        self.assertEqual(a["name"], "Changed World")
        self.assertEqual(self.store.one_world(self.b)["epoch_year"], None)
        with self.assertRaises(Error):
            self.store.update_world(self.a, {"epoch_year":"tomorrow"})

    def test_media_metadata_caption_updates_and_invalid_bytes(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow absent")
        with self.assertRaises(Error):
            self.store.upload_image(self.a, b"not an image", "bad.png")
        raw = io.BytesIO()
        Image.new("RGB", (8, 8), (18, 24, 32)).save(raw, "PNG")
        media = self.store.upload_image(self.a, raw.getvalue(), "photo.png")
        person = self.add(self.a, "Portrait subject")
        usage = self.store.add_media_use(self.a, {"entity_id": person["id"], "media_id": media["id"]})
        edited = self.store.update_media(self.a, media["id"], {
            "title":"Portrait", "alt":"Person in a portrait", "credit":"Creator"})
        self.assertEqual(edited["alt"], "Person in a portrait")
        caption = self.store.update_media_use(self.a, usage["id"], {"caption":"Archival reproduction"})
        self.assertEqual(caption["caption"], "Archival reproduction")
        with self.assertRaises(Error):
            self.store.update_media(self.b, media["id"], {"title":"Stolen"})

    def test_bad_ancestry_archive_rejected_atomically(self):
        parent = self.add(self.a, "A")
        child = self.add(self.a, "B")
        exported = self.store.export(self.a)
        exported["relations"] = [
            {"source_id":parent["id"],"target_id":child["id"],"predicate":"biological_parent_of","status":"working"},
            {"source_id":child["id"],"target_id":parent["id"],"predicate":"adoptive_parent_of","status":"working"}]
        count = len(self.store.worlds())
        with self.assertRaises(Error):
            self.store.import_data(exported)
        self.assertEqual(len(self.store.worlds()), count)

    def test_custom_worldbuilding_categories_and_relations(self):
        a = self.add(self.a, "Mars Ecology", "biosphere")
        b = self.add(self.a, "Main Planet", "planet")
        r = self.store.create_relation(self.a, {
            "source_id":a["id"],"target_id":b["id"],"predicate":"evolves_on"})
        self.assertEqual(r["predicate"], "evolves_on")
        self.assertEqual(len(self.store.entries(self.a, typ="biosphere")), 1)
        with self.assertRaises(Error):
            self.add(self.a, "Invalid", "bad type; DROP TABLE entities;")
        with self.assertRaises(Error):
            self.store.create_relation(self.a, {
                "source_id":a["id"],"target_id":b["id"],"predicate":"evil predicate;"})

    def test_backup_closes_all_sqlite_connections_before_temp_cleanup(self):
        # SQLite's context manager doesn't close connections, even after exit.
        # Windows cannot delete a snapshot database while SQLite holds it open.
        opened=[]
        native_connect=sqlite3.connect

        class TrackedConnection(sqlite3.Connection):
            def close(self):
                self.was_closed=True
                super().close()

        def track_connect(*args,**kwargs):
            connection=native_connect(*args, factory=TrackedConnection, **kwargs)
            connection.was_closed=False
            opened.append(connection)
            return connection

        archive=Path(self.tmp.name)/"tracked-backup.zip"
        with patch.object(backup.sqlite3,"connect",side_effect=track_connect):
            result=make_backup(self.store.path,archive)
        self.assertTrue(archive.is_file())
        self.assertGreaterEqual(result["files"],1)
        self.assertEqual(len(opened),2)
        self.assertTrue(all(connection.was_closed for connection in opened))

        restored_path=Path(self.tmp.name)/"tracked-restored"/"worlds.sqlite3"
        opened.clear()
        with patch.object(backup.sqlite3,"connect",side_effect=track_connect):
            restore_backup(archive,restored_path)
        self.assertTrue(restored_path.is_file())
        self.assertEqual(len(opened),1)
        self.assertTrue(opened[0].was_closed)

    def test_complete_media_backup_and_restore(self):
        from PIL import Image
        self.add(self.a, "Archived settlement", "place")
        image = io.BytesIO()
        Image.new("RGB", (6, 8), (12, 48, 75)).save(image, "PNG")
        m = self.store.upload_image(self.a, image.getvalue(), "settlement.png")
        board=self.store.create_board(self.a,{"title":"Preserved reference collage"})
        bid=board["board"]["id"]
        self.store.add_board_item(self.a,bid,{"kind":"image","media_id":m["id"],"x":300,"y":140,"w":360,"h":260})
        archive = Path(self.tmp.name) / "complete.zip"
        details = make_backup(self.store.path, archive)
        self.assertGreaterEqual(details["files"], 3)
        restore_db = Path(self.tmp.name) / "restored" / "worlds.sqlite3"
        outcome = restore_backup(archive, restore_db)
        self.assertEqual(outcome["files"], details["files"])
        restored = Store(restore_db)
        try:
            self.assertEqual(len(restored.entries(self.a)), 1)
            self.assertEqual(restored.media_file(self.a, m["id"])[0].read_bytes(), image.getvalue())
            self.assertTrue(restored.media_file(self.a, m["id"],True)[0].is_file())
            board_items=restored.board(self.a,bid)["items"]
            self.assertEqual(len(board_items),1)
            self.assertEqual(board_items[0]["media_id"],m["id"])
            self.assertEqual((board_items[0]["x"],board_items[0]["y"],board_items[0]["w"],board_items[0]["h"]), (300,140,360,260))
        finally:
            restored.close()
        with self.assertRaises(ValueError):
            restore_backup(archive,restore_db)

    def test_restore_rejects_invalid_paths(self):
        import zipfile
        archive = Path(self.tmp.name) / "evil.zip"
        with zipfile.ZipFile(archive,"w") as z:
            z.writestr("database.sqlite3", b"fake")
            z.writestr("media/../../escape.txt", b"bad")
            z.writestr("manifest.json", json.dumps({"format":"world-bible-complete-backup-v1",
                "files":{"database.sqlite3":{"size":4,"sha256":"x"},
                         "media/../../escape.txt":{"size":3,"sha256":"x"}}}))
        with self.assertRaises(ValueError):
            restore_backup(archive,Path(self.tmp.name)/"evil-target"/"worlds.sqlite3")

    def test_world_media_usage_index_is_isolated(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not installed")
        image = io.BytesIO()
        Image.new("RGB", (5, 6), (24, 42, 66)).save(image, "PNG")
        media = self.store.upload_image(self.a, image.getvalue(), "coast.png")
        subject = self.add(self.a, "A maritime place", "place")
        self.store.add_media_use(self.a, {
            "entity_id": subject["id"],
            "media_id": media["id"],
            "role": "gallery",
            "caption": "Coastal reference"})
        uses = self.store.media_uses(self.a)
        self.assertEqual(len(uses), 1)
        self.assertEqual(uses[0]["entity_title"], "A maritime place")
        self.assertEqual(uses[0]["caption"], "Coastal reference")
        self.assertEqual(self.store.media_uses(self.b), [])

    def test_publishing_is_independent_of_canon_and_world(self):
        public = self.add(self.a, "Published settlement", "place", status="working", summary="A known port.")
        draft = self.add(self.a, "Research notes", "source", status="established", summary="Private working archive")
        outside = self.add(self.b, "Other world", "place")
        self.assertEqual(self.store.public_worlds(), [])
        self.assertEqual(self.store.public_entries(self.a), [])
        self.store.publication(self.a, public["id"], True)
        self.assertTrue(self.store.is_published(self.a, public["id"]))
        self.assertEqual([e["title"] for e in self.store.public_entries(self.a)], ["Published settlement"])
        self.assertEqual(self.store.public_entries(self.a, search="Private"), [])
        self.assertEqual(len(self.store.public_worlds()), 1)
        self.assertEqual(self.store.public_relations(self.a), [])
        with self.assertRaises(Error):
            self.store.public_entity(self.a, draft["id"])
        with self.assertRaises(Error):
            self.store.public_entity(self.a, outside["id"])
        with self.assertRaises(Error):
            self.store.publication(self.a, outside["id"], True)
        self.store.publication(self.a, public["id"], False)
        self.assertEqual(self.store.public_entries(self.a), [])

    def test_public_backlinks_and_relations_exclude_drafts(self):
        subject = self.add(self.a, "Coastal town", "place")
        reader = self.add(self.a, "River history", "event")
        hidden = self.add(self.a, "Unpublished family", "family")
        self.store.update_entry(self.a, reader["id"], {
            "body":"See [[" + subject["id"] + "|Coastal town]]."})
        self.store.update_entry(self.a, hidden["id"], {
            "body":"An unpublished reference to [[" + subject["id"] + "|Coastal town]]."})
        self.store.create_relation(self.a, {"source_id":reader["id"],"target_id":subject["id"],"predicate":"located_in"})
        self.store.create_relation(self.a, {"source_id":hidden["id"],"target_id":subject["id"],"predicate":"part_of"})
        for e in (subject, reader):
            self.store.publication(self.a, e["id"], True)
        self.assertEqual(len(self.store.public_relations(self.a, subject["id"])), 1)
        self.assertEqual([x["title"] for x in self.store.public_links(self.a,subject["id"],incoming=True)],
                         ["River history"])
        with self.assertRaises(Error) as ctx:
            self.store.public_links(self.a,hidden["id"])
        self.assertEqual(ctx.exception.status,404)

    def test_publications_preserved_after_archive_import(self):
        source = self.add(self.a, "Published port", "place")
        self.store.publication(self.a, source["id"], True)
        exported = self.store.export(self.a)
        self.assertEqual(len(exported["publications"]), 1)
        target = self.store.import_data(exported)["world"]["id"]
        imported = self.store.public_entries(target)
        self.assertEqual(len(imported), 1)
        self.assertEqual(imported[0]["title"],"Published port")
        self.assertNotEqual(imported[0]["id"], source["id"])
        self.assertEqual(self.store.public_entries(self.b), [])

    def test_static_publication_contains_no_draft_records_or_private_notes(self):
        from PIL import Image
        import zipfile
        published = self.add(self.a, "Published valley", "place", summary="A river valley")
        draft = self.add(self.a, "Secret faction", "organization", summary="Not released")
        media_bytes=io.BytesIO()
        Image.new("RGB",(9,7),(55,86,74)).save(media_bytes,"PNG")
        asset=self.store.upload_image(self.a,media_bytes.getvalue(),"valley.png")
        self.store.add_media_use(self.a,{"entity_id":published["id"],"media_id":asset["id"],"role":"hero"})
        self.store.create_relation(self.a,{"source_id":published["id"],"target_id":draft["id"],
            "predicate":"related_to","notes":"Confidential historical research"})
        self.store.publication(self.a,published["id"],True)
        folder=Path(self.tmp.name)/"public-website"
        result=build_site(self.store,self.a,folder)
        self.assertEqual(result["published_entries"],1)
        self.assertEqual(result["media_assets"],1)
        self.assertTrue((folder/"index.html").is_file())
        self.assertIn('name="worldbible-static"',(folder/"index.html").read_text())
        self.assertTrue((folder/"reader.js").is_file())
        content=(folder/"site-data.json").read_text()
        self.assertIn("Published valley",content)
        self.assertNotIn("Secret faction",content)
        self.assertNotIn("Confidential historical research",content)
        bundle=json.loads(content)
        self.assertEqual(bundle["relations"],[])
        self.assertEqual(len(bundle["entities"]),1)
        self.assertEqual(bundle["entities"][0]["hero_media_id"],asset["id"])
        self.assertTrue((folder/"media"/(asset["id"]+"-preview.webp")).is_file())
        with self.assertRaises(ValueError):
            build_site(self.store,self.a,folder)

    def test_public_site_refuses_links_to_unpublished_entries(self):
        a=self.add(self.a,"A","place")
        b=self.add(self.a,"Private B","person")
        self.store.update_entry(self.a,a["id"],{"body":"See [[" + b["id"] + "|B]]."})
        self.store.publication(self.a,a["id"],True)
        with self.assertRaises(ValueError):
            build_site(self.store,self.a,Path(self.tmp.name)/"blocked-site")
        self.assertFalse((Path(self.tmp.name)/"blocked-site").exists())

    def test_moodboards_link_shared_images_and_canon_entries(self):
        from PIL import Image
        raw=io.BytesIO()
        Image.new("RGB",(10,10),(20,50,80)).save(raw,"PNG")
        media=self.store.upload_image(self.a,raw.getvalue(),"coast.png")
        place=self.add(self.a,"Shoreline","place")
        board=self.store.create_board(self.a,{"title":"Coastal architecture","description":"Visual references","entity_id":place["id"]})
        bid=board["board"]["id"]
        board=self.store.add_board_item(self.a,bid,{"kind":"note","content":"Weathered cedar",
            "x":145,"y":80,"w":280,"h":190,"z":1})
        note=board["items"][0]
        self.store.add_board_item(self.a,bid,{"kind":"image","media_id":media["id"],"x":400,"y":60})
        self.store.add_board_item(self.a,bid,{"kind":"entry","entity_id":place["id"],"x":600,"y":120})
        self.store.add_board_item(self.a,bid,{"kind":"swatch","color":"#a6c5af","content":"Moss"})
        current=self.store.board(self.a,bid)
        self.assertEqual(len(current["items"]),4)
        self.assertEqual(next(i for i in current["items"] if i["kind"]=="image")["media_id"],media["id"])
        self.assertEqual(next(i for i in current["items"] if i["kind"]=="entry")["entity_title"],"Shoreline")
        changed=self.store.update_board_item(self.a,bid,note["id"],{"x":300,"content":"Wet cedar"})
        self.assertEqual(next(i for i in changed["items"] if i["id"]==note["id"])["x"],300)
        self.assertEqual(next(i for i in changed["items"] if i["id"]==note["id"])["content"],"Wet cedar")
        self.assertEqual(self.store.boards(self.a)[0]["item_count"],4)
        self.assertEqual(self.store.boards(self.b),[])
        with self.assertRaises(Error):
            self.store.board(self.b,bid)
        with self.assertRaises(Error):
            self.store.add_board_item(self.b,bid,{"kind":"note","content":"Cross-world"})
        with self.assertRaises(Error):
            self.store.add_board_item(self.a,bid,{"kind":"image","media_id":"not-found"})
        with self.assertRaises(Error):
            self.store.update_board_item(self.a,bid,note["id"],{"x":1000000})
        with self.assertRaises(Error):
            self.store.add_board_item(self.a,bid,{"kind":"swatch","color":"background:url(javascript:evil)"})
        export=self.store.export(self.a)
        self.assertEqual(len(export["moodboards"]),1)
        self.assertEqual(len(export["moodboard_items"]),4)
        with self.assertRaises(Error):
            self.store.import_data(export)
        self.assertEqual(self.store.check_entity(self.a,place["id"])["title"],"Shoreline")
        self.assertEqual(self.store.media_file(self.a,media["id"])[0].read_bytes(),raw.getvalue())
        self.store.delete_board(self.a,bid)
        self.assertEqual(self.store.boards(self.a),[])
        self.assertEqual(self.store.check_entity(self.a,place["id"])["title"],"Shoreline")
        self.assertTrue(self.store.media_file(self.a,media["id"])[0].exists())

    def test_moodboard_belongs_to_one_world_and_deletions_are_scoped(self):
        a=self.add(self.a,"Gallery owner")
        b=self.add(self.b,"Other world")
        board=self.store.create_board(self.a,{"title":"A","entity_id":a["id"]})
        bid=board["board"]["id"]
        self.assertEqual(self.store.board(self.a,bid)["board"]["entity_id"],a["id"])
        with self.assertRaises(Error):
            self.store.update_board(self.a,bid,{"entity_id":b["id"]})
        self.store.add_board_item(self.a,bid,{"kind":"entry","entity_id":a["id"]})
        self.store.delete_entry(self.a,a["id"])
        items=self.store.board(self.a,bid)
        self.assertIsNone(items["board"]["entity_id"])
        self.assertIsNone(items["items"][0]["entity_id"])

    def test_export_content(self):
        a = self.add(self.a, "River", "place")
        data = self.store.export(self.a)
        self.assertEqual(data["format"], "world-bible-export-v1")
        self.assertEqual(data["entities"][0]["id"], a["id"])
        self.assertEqual(len(self.store.export(self.b)["entities"]), 0)


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "api.sqlite3")
        self.http = ThreadingHTTPServer(("127.0.0.1",0), Handler)
        self.http.store = self.store
        self.url = "http://127.0.0.1:" + str(self.http.server_port)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(2)
        self.store.close()
        self.tmp.cleanup()

    def request(self, path, method="GET", body=None, headers=None):
        opts = {"X-World-Bible":"1"}
        if headers:
            opts.update(headers)
        blob = json.dumps(body).encode() if body is not None else None
        if blob is not None:
            opts["Content-Type"]="application/json"
        try:
            with urlopen(Request(self.url+path, data=blob, method=method, headers=opts),timeout=5) as resp:
                return resp.status, resp.read(), resp.headers
        except HTTPError as e:
            return e.code, e.read(), e.headers

    def test_http_creation_linking_and_static(self):
        code, page, headers = self.request("/app/")
        self.assertEqual(code,200)
        self.assertIn(b"World Bible Studio", page)
        self.assertIn("Content-Security-Policy", headers)
        code, raw, _ = self.request("/api/worlds","POST",{"name":"Another World"})
        self.assertEqual(code,201)
        wid=json.loads(raw)["id"]
        code, raw, _ = self.request("/api/entities?world_id="+wid,"POST",{"title":"Village","type":"place"})
        self.assertEqual(code,201)
        entity=json.loads(raw)
        self.assertEqual(self.request("/api/entity?world_id="+wid+"&id="+entity["id"])[0],200)
        self.assertEqual(self.request("/api/export?world_id="+wid)[0],200)

    def test_reader_pages_and_published_api(self):
        status, page, headers = self.request("/")
        # urllib automatically follows the root redirect to the reader page.
        self.assertEqual(status,200)
        self.assertIn(b"Explore the World",page)
        status, page, headers = self.request("/read/")
        self.assertEqual(status,200)
        self.assertIn(b"Explore the World",page)
        self.assertIn("Content-Security-Policy",headers)
        status, data, _ = self.request("/api/worlds","POST",{"name":"New Public World"})
        world = json.loads(data)["id"]
        status, data, _ = self.request("/api/entities?world_id="+world,"POST",
            {"title":"A city","type":"place","summary":"Port on the coast"})
        eid = json.loads(data)["id"]
        status, data, _ = self.request("/api/public/entities?world_id="+world)
        self.assertEqual(json.loads(data),[])
        status, _, _ = self.request("/api/public/entity?world_id="+world+"&id="+eid)
        self.assertEqual(status,404)
        status, data, _ = self.request("/api/publication?world_id="+world+"&id="+eid,"POST",{"published":True})
        self.assertEqual(status,200)
        status, data, _ = self.request("/api/public/entities?world_id="+world)
        self.assertEqual(len(json.loads(data)),1)
        status, data, _ = self.request("/api/public/media?world_id="+world+"&entity_id="+eid)
        self.assertEqual(json.loads(data),[])

    def test_missing_header_and_cross_origin_refused(self):
        code, _, _ = self.request("/api/worlds","POST",{"name":"X"},headers={"Origin":"http://attacker.invalid"})
        self.assertEqual(code,403)
        req=Request(self.url+"/api/worlds",data=b'{"name":"X"}',method="POST",headers={"Content-Type":"application/json"})
        with self.assertRaises(HTTPError) as cm:
            urlopen(req,timeout=5)
        self.assertEqual(cm.exception.code,403)


if __name__ == "__main__":
    unittest.main()
