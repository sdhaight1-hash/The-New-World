"""Regression tests for existing-canon population.

The repository is an input to the local-first Studio, NOT an instruction to
overwrite a user's live SQLite files or automatically publish working drafts.
"""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from seed import ROOT, WORLD_ID, canon_id, source_id, load_canon, seed
from server import Store


class CanonSeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"worlds.sqlite3"

    def tearDown(self):
        self.tmp.cleanup()

    def test_manifest_has_only_audited_reference_categories(self):
        manifest=load_canon()
        self.assertGreaterEqual(len(manifest["entries"]),60)
        self.assertGreaterEqual(len(manifest["relations"]),50)
        self.assertEqual({e["type"] for e in manifest["entries"]},{"place","event","subject"})
        self.assertFalse(any(e["type"]=="person" for e in manifest["entries"]))
        for item in manifest["entries"]:
            self.assertTrue((ROOT/item["source"]).is_file())
            self.assertTrue(item["body"].strip())
            self.assertNotIn("lat",item,"No unverified precision for places")
            self.assertNotIn("lon",item,"No unverified precision for places")

    def test_all_existing_sources_structured_records_and_relationships_import(self):
        manifest=load_canon()
        seed(self.path)
        with Store(self.path) as store:
            docs=sum(1 for folder in ("bible","regions") for _ in (ROOT/folder).glob("*.md"))
            distinct=sum(not x.get("reuse_source") for x in manifest["entries"])
            self.assertEqual(len(store.entries(WORLD_ID)),docs+distinct)
            self.assertEqual(len(store.relation_list(WORLD_ID)),len(manifest["relations"]))
            self.assertEqual(store.public_entries(WORLD_ID),[])
            self.assertEqual(len(store.entries(WORLD_ID,typ="person")),0)
            for path in ("bible/00-foundations.md","bible/02-great-plague.md","regions/clatsop-county.md"):
                original=(ROOT/path).read_text(encoding="utf-8")
                self.assertEqual(store.check_entity(WORLD_ID,source_id(path))["body"],original)
            self.assertEqual(store.check_entity(WORLD_ID,canon_id("victor-valley"))["title"],"Victor Valley")
            self.assertEqual(store.check_entity(WORLD_ID,canon_id("diamond-ranch"))["lat"],None)
            self.assertIn("identity unresolved",store.check_entity(WORLD_ID,canon_id("wyoming-reservation"))["title"])
            self.assertEqual(store.check_entity(WORLD_ID,source_id("bible/03-cascade.md"))["start_year"],0)
            backlinks=store.backlinks(WORLD_ID,canon_id("victor-valley"))
            self.assertGreaterEqual(len(backlinks),4)
            self.assertEqual(len(store.boards(WORLD_ID)),0)

    def test_repeat_seed_never_duplicates_or_overwrites_personal_edits(self):
        seed(self.path)
        with Store(self.path) as store:
            eid=canon_id("seaside")
            plague=source_id("bible/02-great-plague.md")
            store.update_entry(WORLD_ID,eid,{
                "body":"This is the creator's manually revised Seaside entry.",
                "summary":"Confirmed custom summary."
            })
            store.update_entry(WORLD_ID,plague,{"body":"A creator-amended historical source page."})
            store.publication(WORLD_ID,eid,True)
            count=len(store.entries(WORLD_ID))
            relations=len(store.relation_list(WORLD_ID))
        seed(self.path)
        with Store(self.path) as store:
            self.assertEqual(len(store.entries(WORLD_ID)),count)
            self.assertEqual(len(store.relation_list(WORLD_ID)),relations)
            self.assertEqual(store.check_entity(WORLD_ID,eid)["body"],
                             "This is the creator's manually revised Seaside entry.")
            self.assertEqual(store.check_entity(WORLD_ID,eid)["summary"],"Confirmed custom summary.")
            self.assertEqual(store.check_entity(WORLD_ID,plague)["body"],
                             "A creator-amended historical source page.")
            self.assertTrue(store.is_published(WORLD_ID,eid))


if __name__=="__main__":
    unittest.main()
