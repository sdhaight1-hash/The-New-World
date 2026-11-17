"""Regression tests for existing-canon population.

The repository is an input to the local-first Studio, NOT an instruction to
overwrite a user's live SQLite files or automatically publish working drafts.
"""
from contextlib import closing
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from seed import ROOT, WORLD_ID, WORLD_SOURCE_PATHS, canon_id, source_id, load_canon, linked_body, seed
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
        with closing(Store(self.path)) as store:
            docs=len(WORLD_SOURCE_PATHS)
            distinct=sum(not x.get("reuse_source") for x in manifest["entries"])
            self.assertEqual(len(store.entries(WORLD_ID)),docs+distinct)
            self.assertEqual(len(store.relation_list(WORLD_ID)),len(manifest["relations"]))
            self.assertNotIn(source_id("bible/10-rfc-historical-knowledge-core.md"),
                             {e["id"] for e in store.entries(WORLD_ID)})
            self.assertNotIn(source_id("bible/00-foundations.md"),
                             {e["id"] for e in store.entries(WORLD_ID)})
            self.assertEqual(store.public_entries(WORLD_ID),[])
            self.assertEqual(len(store.entries(WORLD_ID,typ="person")),0)
            for path in ("bible/01-chronology.md","bible/02-great-plague.md","regions/clatsop-county.md"):
                original=(ROOT/path).read_text(encoding="utf-8")
                self.assertEqual(store.check_entity(WORLD_ID,source_id(path))["body"],original)
            self.assertEqual(store.check_entity(WORLD_ID,canon_id("victor-valley"))["title"],"Victor Valley")
            self.assertEqual(store.check_entity(WORLD_ID,canon_id("diamond-ranch"))["lat"],None)
            self.assertIn("identity unresolved",store.check_entity(WORLD_ID,canon_id("wyoming-reservation"))["title"])
            self.assertEqual(store.check_entity(WORLD_ID,source_id("bible/03-cascade.md"))["start_year"],0)
            backlinks=store.backlinks(WORLD_ID,canon_id("victor-valley"))
            self.assertGreaterEqual(len(backlinks),4)
            self.assertEqual(len(store.boards(WORLD_ID)),0)

    def test_legacy_software_documents_pruned_only_if_untouched(self):
        seed(self.path)
        dev_path="bible/15-unified-architecture.md"
        edited_path="bible/16-ux-and-entry-designer.md"
        public_path="bible/17-rfc-2d-historical-atlas.md"

        def legacy(store,path):
            original=(ROOT/path).read_text(encoding="utf-8")
            title=next(line[2:].strip() for line in original.splitlines() if line.startswith("# "))
            return store.create_entry(WORLD_ID,{
                "type":"subject","title":title,"body":original,"status":"working"
            },specified_id=source_id(path))

        with closing(Store(self.path)) as store:
            legacy(store,dev_path)
            edited=legacy(store,edited_path)
            published=legacy(store,public_path)
            store.update_entry(WORLD_ID,edited["id"],{"body":"My custom project notes"})
            store.publication(WORLD_ID,published["id"],True)

        seed(self.path)
        with closing(Store(self.path)) as store:
            self.assertFalse(store.one("SELECT id FROM entities WHERE id=?",(source_id(dev_path),)))
            self.assertEqual(store.check_entity(WORLD_ID,source_id(edited_path))["body"],
                             "My custom project notes")
            self.assertTrue(store.is_published(WORLD_ID,source_id(public_path)))
            backups=list((self.path.parent/"backups").glob("before-lore-cleanup-*.zip"))
            self.assertEqual(len(backups),1)
            self.assertGreater(backups[0].stat().st_size,100)
        seed(self.path)
        self.assertEqual(len(list((self.path.parent/"backups").glob("*.zip"))),1)

    def test_generated_ledger_reference_is_migrated(self):
        manifest=load_canon()
        seed(self.path)
        entry=next(item for item in manifest["entries"] if item["key"]=="reference-present")
        ids={item["key"]:source_id(item["reuse_source"]) if item.get("reuse_source") else canon_id(item["key"])
             for item in manifest["entries"]}
        old={**entry,"source":"bible/00-foundations.md"}
        with closing(Store(self.path)) as store:
            legacy_text=(ROOT/"bible/00-foundations.md").read_text(encoding="utf-8")
            store.create_entry(WORLD_ID,{
                "type":"subject","title":"Foundations and canon ledger","body":legacy_text,
                "aliases":["Foundational Canon"],"status":"working"
            },specified_id=source_id("bible/00-foundations.md"))
            store.update_entry(WORLD_ID,ids["reference-present"],
                               {"body":linked_body(old,manifest,ids)})
            self.assertEqual(len(store.backlinks(WORLD_ID,source_id("bible/00-foundations.md"))),1)
        seed(self.path)
        with closing(Store(self.path)) as store:
            self.assertNotIn("bible/00-foundations.md",
                             store.check_entity(WORLD_ID,ids["reference-present"])["body"])
            self.assertFalse(store.one("SELECT id FROM entities WHERE id=?",
                                       (source_id("bible/00-foundations.md"),)))
            self.assertTrue(store.backlinks(WORLD_ID,source_id("bible/01-chronology.md")))

    def test_opening_ai_era_and_documented_vs_alternate_history(self):
        manifest=load_canon()
        opening={e["key"]:e for e in manifest["entries"]}
        self.assertIn("bible/20-brief-age-of-ai.md",WORLD_SOURCE_PATHS)
        self.assertEqual(opening["chatgpt-public-launch"]["status"],"established")
        self.assertIn("November 30, 2022",opening["chatgpt-public-launch"]["title"])
        self.assertIn("GPT-3.5",opening["chatgpt-public-launch"]["body"])
        self.assertIn("alternate",opening["agi-announcement-2026"]["body"].lower())
        self.assertIn("have not been established",opening["social-fracture-2029"]["body"])
        seed(self.path)
        with closing(Store(self.path)) as store:
            years=[e for e in store.entries(WORLD_ID) if e["type"]=="event"]
            self.assertEqual(min(e["start_year"] for e in years if e["start_year"] is not None),-15)
            self.assertEqual(store.check_entity(WORLD_ID,canon_id("chatgpt-public-launch"))["start_year"],-12)
            self.assertEqual(store.check_entity(WORLD_ID,canon_id("agi-announcement-2026"))["start_year"],-8)
            self.assertEqual(store.check_entity(WORLD_ID,canon_id("automation-boom-2028"))["start_year"],-6)
            self.assertEqual(store.public_entries(WORLD_ID),[])
            self.assertGreaterEqual(len(store.relation_list(WORLD_ID)),75)
            self.assertIn("November 30, 2022",store.check_entity(
                WORLD_ID,source_id("bible/20-brief-age-of-ai.md"))["body"])

    def test_2019_to_2026_documented_multidomain_history(self):
        manifest=load_canon()
        items={item["key"]:item for item in manifest["entries"]}
        self.assertIn("bible/21-real-world-2019-2026.md",WORLD_SOURCE_PATHS)
        fields={
            "2019":("global-baseline-2019","covid-emergence-2019","hong-kong-2019"),
            "2020":("covid-pandemic-2020","pandemic-recession-2020","us-election-2020"),
            "2021":("afghanistan-2021","supply-inflation-2021"),
            "2022":("ukraine-invasion-2022","chatgpt-public-launch"),
            "2023":("sudan-war-2023","israel-gaza-2023","nato-enlargement-2023"),
            "2024":("eu-ai-act-2024","us-election-2024","climate-2024"),
            "2025":("us-presidency-2025","ai-investment-2025","military-spending-2025"),
            "2026":("trade-uncertainty-2026","iran-conflict-2026","us-midterms-2026","agi-announcement-2026"),
        }
        for year,keys in fields.items():
            for key in keys:
                self.assertIn(key,items,(year,key))
                self.assertIn(items[key]["source"],WORLD_SOURCE_PATHS)
        self.assertEqual(items["global-baseline-2019"]["start_year"],-15)
        self.assertEqual(items["covid-emergence-2019"]["start_year"],-15)
        self.assertEqual(items["trade-uncertainty-2026"]["end_year"],-8)
        self.assertEqual(items["agi-announcement-2026"]["start_year"],-8)
        self.assertEqual(len(manifest["relations"]),143)
        self.assertEqual(len(manifest["entries"]),109)
        self.assertTrue(all(e["status"]=="established" for e in manifest["entries"]
                            if e["source"]=="bible/21-real-world-2019-2026.md"))
        self.assertNotIn("great plague",items["covid-pandemic-2020"]["title"].lower())
        seed(self.path)
        with closing(Store(self.path)) as store:
            self.assertEqual(len(store.entries(WORLD_ID)),117)
            self.assertEqual(len(store.relation_list(WORLD_ID)),143)
            self.assertEqual(store.public_entries(WORLD_ID),[])
            original=(ROOT/"bible/21-real-world-2019-2026.md").read_text(encoding="utf-8")
            self.assertEqual(store.check_entity(WORLD_ID,source_id("bible/21-real-world-2019-2026.md"))["body"],original)
            self.assertGreaterEqual(len(store.backlinks(WORLD_ID,canon_id("covid-pandemic-2020"))),2)
        seed(self.path)
        with closing(Store(self.path)) as store:
            self.assertEqual(len(store.entries(WORLD_ID)),117)
            self.assertEqual(len(store.relation_list(WORLD_ID)),143)

    def test_zooming_historical_layers_reuse_original_articles_and_preserve_edits(self):
        manifest=load_canon()
        hierarchy={row["key"]:row for row in manifest["entries"] if row["key"].startswith("history-")}
        self.assertEqual(len(hierarchy),10)
        for row in hierarchy.values():
            self.assertEqual(row["reuse_source"],row["source"])
            self.assertIn(row["source"],WORLD_SOURCE_PATHS)
            self.assertTrue((ROOT/row["source"]).is_file())
        required=[
            ("history-world","history-hemisphere"),
            ("history-hemisphere","history-us"),
            ("history-us","history-west"),
            ("history-west","history-california"),
            ("history-west","history-oregon"),
            ("history-west","history-wyoming"),
            ("history-california","history-so-cal-local"),
            ("history-oregon","history-clatsop-local"),
            ("history-wyoming","history-wyoming-local"),
        ]
        actual={(r["source"],r["target"]) for r in manifest["relations"] if r["predicate"]=="narrows_to"}
        self.assertTrue(set(required)<=actual)
        seed(self.path)
        with closing(Store(self.path)) as store:
            for row in hierarchy.values():
                record=store.check_entity(WORLD_ID,source_id(row["source"]))
                self.assertEqual(record["body"],(ROOT/row["source"]).read_text(encoding="utf-8"))
                self.assertEqual(record["type"],"subject")
                self.assertEqual(record["status"],"established")
            west=source_id(hierarchy["history-west"]["source"])
            self.assertEqual(len([r for r in store.relation_list(WORLD_ID,west)
                 if r["predicate"]=="narrows_to" and r["source_id"]==west]),3)
            self.assertEqual(store.public_entries(WORLD_ID),[])
            california=source_id(hierarchy["history-california"]["source"])
            store.update_entry(WORLD_ID,california,{"body":"My revised California history"})
        seed(self.path)
        with closing(Store(self.path)) as store:
            self.assertEqual(store.check_entity(WORLD_ID,california)["body"],"My revised California history")
            self.assertEqual(len(store.entries(WORLD_ID)),117)
            self.assertEqual(len(store.relation_list(WORLD_ID)),143)

    def test_repeat_seed_never_duplicates_or_overwrites_personal_edits(self):
        seed(self.path)
        with closing(Store(self.path)) as store:
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
        with closing(Store(self.path)) as store:
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
