"""V2 schema, classification, reviewed links and reader isolation regression tests."""
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from server import Store,Error
import v2_store
from knowledge_v2 import mask_ineligible, suggestions

class KnowledgeV2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"test.sqlite3"
        self.store=Store(self.path)
        self.w=self.store.create_world({"name":"Research world"})["id"]
        self.other=self.store.create_world({"name":"Other world"})["id"]

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def add(self,title,typ="subject",world=None,**kwargs):
        return self.store.create_entry(world or self.w,{"type":typ,"title":title,**kwargs})

    def test_schema_v2_and_original_entries_unchanged(self):
        self.assertEqual(self.store.one("PRAGMA user_version")[0],2)
        entry=self.add("Original manuscript",body="Unmodified source content")
        self.store.close()
        self.store=Store(self.path)
        self.assertEqual(self.store.check_entity(self.w,entry["id"])["body"],"Unmodified source content")
        self.assertEqual(v2_store.classifications(self.store,self.w,entry["id"])["properties"],{})

    def test_types_and_properties_validate_references_and_choices(self):
        entry=self.add("Valley","place")
        parent=self.add("California","place")
        metadata={"subtype":"region","properties":{"kind":"region","parent_place":parent["id"],"terrain":"desert"},
                  "categories":[],"tags":[]}
        result=v2_store.update_metadata(self.store,self.w,entry["id"],metadata)
        self.assertEqual(result["properties"]["parent_place"],parent["id"])
        self.assertEqual(result["subtype"],"region")
        with self.assertRaises(Error):
            v2_store.update_metadata(self.store,self.w,entry["id"],{**metadata,"subtype":"novel"})
        outside=self.add("Outside","place",world=self.other)
        with self.assertRaises(Error):
            v2_store.update_metadata(self.store,self.w,entry["id"],{**metadata,"properties":{"parent_place":outside["id"]}})
        self.assertEqual(v2_store.classifications(self.store,self.w,entry["id"])["properties"]["terrain"],"desert")

    def test_structured_references_block_unsafe_deletion_and_type_change(self):
        parent=self.add("Parent region","place")
        child=self.add("Child region","place")
        v2_store.update_metadata(self.store,self.w,child["id"],
             {"subtype":"region","properties":{"parent_place":parent["id"]},"categories":[],"tags":[]})
        with self.assertRaises(Error):
            self.store.delete_entry(self.w,parent["id"])
        with self.assertRaises(Error):
            self.store.update_entry(self.w,child["id"],{"type":"person"})
        self.assertEqual(self.store.check_entity(self.w,child["id"])["type"],"place")

    def test_category_tag_membership_and_public_visibility(self):
        public=self.add("Public","place")
        private=self.add("Private","place")
        category=v2_store.create_category(self.store,self.w,{"name":"High Desert"})
        tag=v2_store.create_tag(self.store,self.w,{"name":"Infrastructure"})
        data={"subtype":None,"properties":{},"categories":[category["id"]],"tags":[tag["id"]]}
        for record in (public,private):
            v2_store.update_metadata(self.store,self.w,record["id"],data)
        self.store.publication(self.w,public["id"],True)
        self.assertEqual(len(v2_store.categories(self.store,self.w,True)),1)
        self.assertEqual(len(v2_store.tags(self.store,self.w,True)),1)
        self.assertEqual(set(v2_store.memberships(self.store,self.w,True)),{public["id"]})
        self.assertEqual(len(v2_store.search(self.store,self.w,category=category["id"],public=True)),1)
        self.assertEqual(len(v2_store.search(self.store,self.w,tag=tag["id"],public=False)),2)
        outside=v2_store.create_category(self.store,self.other,{"name":"Other"})
        with self.assertRaises(Error):
            v2_store.update_metadata(self.store,self.w,public["id"],{**data,"categories":[outside["id"]]})

    def test_reference_match_and_author_approval(self):
        target=self.add("Victor Valley","place",aliases=["the Victor Valley"])
        source=self.add("Field notes",body="Victor Valley survived. `Victor Valley` was a code label.\n\n[Victor Valley](https://example.org)")
        findings=v2_store.mentions(self.store,self.w,source["id"])
        self.assertEqual(len(findings["suggestions"]),1)
        match=findings["suggestions"][0]
        self.assertEqual(match["text"],"Victor Valley")
        body=v2_store.decide(self.store,self.w,source["id"],
            {"revision":findings["revision"],"start":match["start"],"end":match["end"],
             "fingerprint":match["fingerprint"],"target_id":target["id"]},True)["body"]
        self.assertIn("[["+target["id"]+"|Victor Valley]]",body)
        self.assertEqual(len(self.store.outgoing(self.w,source["id"])),1)
        self.assertFalse(v2_store.mentions(self.store,self.w,source["id"])["suggestions"])

    def test_ambiguous_mentions_ignore_and_stale_revision(self):
        first=self.add("The Cascade","event",aliases=["Blackout"])
        second=self.add("Regional blackout","event",aliases=["Blackout"])
        source=self.add("Notes",body="Blackout affected the region.")
        found=v2_store.mentions(self.store,self.w,source["id"])
        self.assertEqual(len(found["suggestions"]),1)
        self.assertEqual(len(found["suggestions"][0]["candidates"]),2)
        candidate=found["suggestions"][0]
        payload={"revision":found["revision"],"start":candidate["start"],"end":candidate["end"],
                 "fingerprint":candidate["fingerprint"],"target_id":first["id"]}
        v2_store.decide(self.store,self.w,source["id"],payload,False)
        remaining=v2_store.mentions(self.store,self.w,source["id"])["suggestions"]
        self.assertEqual(len(remaining[0]["candidates"]),1)
        self.assertEqual(remaining[0]["candidates"][0]["id"],second["id"])
        self.store.update_entry(self.w,source["id"],{"body":"Revised Blackout records."})
        with self.assertRaises(Error) as caught:
            v2_store.decide(self.store,self.w,source["id"],payload,True)
        self.assertEqual(caught.exception.status,409)

    def test_public_metadata_hides_unpublished_entry_reference(self):
        public=self.add("Published place","place")
        private=self.add("Unpublished place","place")
        self.store.publication(self.w,public["id"],True)
        v2_store.update_metadata(self.store,self.w,public["id"],
             {"subtype":"region","properties":{"parent_place":private["id"]},"categories":[],"tags":[]})
        self.assertEqual(v2_store.public_metadata(self.store,self.w,public["id"])["properties"],{})
        with self.assertRaises(Error):
            v2_store.public_metadata(self.store,self.w,private["id"])

    def test_export_import_v2_roundtrip(self):
        source=self.add("Location","place")
        category=v2_store.create_category(self.store,self.w,{"name":"Location index"})
        tag=v2_store.create_tag(self.store,self.w,{"name":"Geography"})
        v2_store.update_metadata(self.store,self.w,source["id"],
             {"subtype":"region","properties":{"kind":"region"},"categories":[category["id"]],"tags":[tag["id"]]})
        archive=self.store.export(self.w)
        self.assertEqual(archive["format"],"world-bible-export-v2")
        target=self.store.import_data(archive)["world"]["id"]
        imported=self.store.entries(target)
        self.assertEqual(len(imported),1)
        restored=v2_store.classifications(self.store,target,imported[0]["id"])
        self.assertEqual(restored["subtype"],"region")
        self.assertEqual(restored["properties"]["kind"],"region")
        self.assertEqual(len(restored["categories"]),1)
        self.assertEqual(len(restored["tags"]),1)
        self.assertNotEqual(restored["categories"][0],category["id"])

    def test_studio_search_filters(self):
        place=self.add("Water plant","place")
        self.add("Other plant","place",world=self.other)
        self.assertEqual([e["id"] for e in v2_store.search(self.store,self.w,"plant",typ="place")],[place["id"]])

if __name__=="__main__":
    unittest.main()
