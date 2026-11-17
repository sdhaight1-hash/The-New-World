# The New World — structured canon inventory

This directory contains the **source-grounded population manifest** for the local World Bible Studio.

- [`entries.json`](entries.json) — 62 identified historical concepts, including two reused authoritative catastrophe articles, and 58 reviewed relations. When combined with the 8 in-world historical and regional source articles, a fresh Studio seed creates **68 genuine world-content records**.
- [`../app/seed.py`](../app/seed.py) — deterministic, repeatable importer. Source article content is preserved verbatim, and editing an existing database record never causes a later seed to overwrite it.
- [`../app/tests/test_seed.py`](../app/tests/test_seed.py) — tests record totals, related entries and backlinks, source fidelity, world isolation by IDs, stable reimports, preservation of edited content and publication state.

## Quality and scope audit

The original importer accidentally treated 15 editorial/software-design documents as world entries. The [content audit](CONTENT_AUDIT.md) documents every excluded file and flags remaining historical placeholders for review. A fresh seeded encyclopedia contains **68 world-content records**, not the previous 83. Existing local databases receive a backup-first cleanup that preserves edited or published content.

## What counts as canon here?

**Established:** creator-approved broad premises or real-world geographical baseline; it does *not* mean that all future details, dates, populations or institutions are settled.

**Working:** plausible but unapproved future developments, explanatory scenarios, approximated chronology or incomplete local histories.

**Unresolved:** documented as research questions rather than filled in with invented characters, rulers, maps or numbers. Wyoming's "Diamond Ranch" and the unspecified reservation are deliberately not geolocated.

The chronology uses **Cascade-relative Years**, not a fixed Gregorian mapping. Year 0 is the first Cascade, tentatively around 2034–2035; events such as the Great Plague have deliberately approximate ranges. No in-world historian, dynasty or royal capital has been invented simply to make the database look full.

Software architecture, UI/UX specifications, system plans, research task lists, and editorial ledgers remain in the repository for developers but are **excluded from the world's encyclopedia**. The seeder imports only explicitly whitelisted history and geography source articles, never all Markdown under `bible/`. Where a genuine world entity is described inside a broad source, its structured entry links back to the original source and to related entities by stable identifiers.

## Importing

From the project root, run:

```bash
python app/seed.py
python app/launch.py
```

Or use the Windows `Launch-World-Bible.cmd` shortcut; the launcher seeds any missing content automatically.

The importer uses a fixed world UUID reserved for **The New World**. It will not populate any other independent worlds. It creates missing records and links only, without replacing existing article text, titles, design choices or publication settings.

The *reader* intentionally receives **no automatic publications**: article canon status and public editorial approval are separate. Review entries in the Studio, then use **Publish** for the material you want visitors to see.

## Updating and extending the inventory

Use `entries.json` to record new confirmed material **only after verifying the source**. Every record needs a stable `key`, a title, source path, category, summary, body and editorial status. A manifest relation references stable keys, not titles. Avoid duplicate keys and invented coordinates.

If you edit a record through the local Studio, the SQLite copy becomes authoritative for that record. The manifest remains an initial-source record and **does not sync edits back to GitHub**. Back up the live database and image library; Git is not a substitute.

An important scope distinction: only material belonging to **the post-Plague, post-Cascade world** belongs in this manifest. Other stories, personal time-return scenarios, or unrelated worldbuilding projects must remain separate until explicitly merged into this canon.

## Next content passes

The current import faithfully represents what has already been documented but does not silently invent missing institutions. Further population should follow researched regional baselines: first the geography, water and agricultural constraints, then supported settlement history, migration, political institutions, named people and their family networks, with cited evidence and uncertainty.
