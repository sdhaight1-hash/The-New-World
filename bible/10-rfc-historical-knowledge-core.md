# RFC 001 — Historical Knowledge Core

**Status:** foundational SQLite/HTTP core implemented in [World Bible Studio](../app/README.md); advanced provenance, uncertainty, rich linking, FTS5 and full schema migrations remain planned.  
**Scope:** foundational data, relationships, auto-linking, historical semantics, search, genealogy, maps, timelines and auditing.  
**Constraint:** minimal maintainable solution; preserve existing Markdown and genealogy exports.

## Decision summary

**Use one SQLite database as the application's transactional authority for structured records, with full-length Markdown article bodies and deterministic Git-friendly exports.** The repository remains the durable archival and review surface; editing moves through transactions in one application rather than through unrelated browser localStorage stores or manually synchronized manifests.

**Do not introduce Neo4j, RDF triplestores, distributed event sourcing, a vector database, AI-generated canon, or a separate genealogy database in v1.** SQLite supports foreign keys, indexed directed edges, recursive queries, transactions and FTS5; this covers realistic first milestones.

Do not instantly move the existing Markdown content. First migrate **via import preserving stable paths and untouched body content**, validate and export without losing data. Until an existing article is migrated it remains an external read-only source, not a competing writable record. After migration, the app owns canonical editing and exports Markdown + structured JSON into the repo. **One writable authority per record** at every stage.

## Audit of current repository (as of initial RFC)

- `bible/*.md` and `regions/*.md`: human-written encyclopedia; no durable entity IDs embedded in entries, except a separate hand-curated discovery index.
- `discovery/index.json`: manual entry titles, aliases and editorial `related` IDs. Not generated from source and not a relationship truth store.
- `tools/discovery/index.html`: embeds its own duplicate hardcoded index; scanning pasted prose navigates candidates but cannot approve/persist links into articles, nor share graph data with genealogy.
- `genealogy/data.json`: versioned but empty structured archive; `tools/genealogy/index.html`: localStorage-based separate editor with manual export. The stored records are not shared live with the encyclopedia.
- No transactional cross-entry rename, merge, deletion, date-aware queries, provenance or canonical relationship system.

**Conclusion:** stop expanding independent HTML prototypes. Build the core and unify them behind an application with a single data service.

## Foundational domain model

### 1. Entity

Stable UUID or ULID as opaque `entity.id`. Types begin with `person, place, event, organization, family, object, subject, source`. Do not encode the name, type, year, or path in an identifier. `title`, `status`, `summary`, `body_md`, `created_at`, `updated_at`; additional type-specific attributes in validated structured extension fields when genuinely needed.

Aliases have `entity_id`, `alias`, `locale`, optional contextual qualifier and active date range. Never treat alias equality as identity.

A **place** may evolve, change names, have geographic shape and parent-region relationships without becoming a new ID unless there truly is a new institution/settlement. A **government** controlling a location is an organization, not the location itself.

### 2. Content reference

`content_link(id, source_entity_id, target_entity_id, anchor_id, link_label, status)` represents a **confirmed explicit mention/link**. Backlinks are reverse queries, **not separately manually stored relationships**.

In text editing, store target IDs inside safe, parser-recognized link nodes (or a Markdown-compatible reference syntax with an export fallback). Link labels can remain custom, while renamed titles change target lookup rather than silently altering authored quotations.

Text scanning emits **candidates**, not confirmed links. Persisted ignored matches need `source_anchor` or context fingerprint, not fragile numeric character offsets.

### 3. Typed relations

`relationship(id, subject_id, predicate_id, object_id, valid_from, valid_to, status, source_id, notes)`.

Examples: `located_in`, `resided_in`, `parent_of`, `adoptive_parent_of`, `partner_of`, `member_of`, `employed_by`, `founded`, `traded_with`, `participated_in`, `controlled`, `succeeded`, `traveled_to`.

A small `predicate` registry specifies directed/symmetric/inverse labels, allowed entity-type pairs and whether a relationship is inherently temporal. A text mention is **not evidence** for a typed relationship. Do not assume that adjacent names imply relations.

For events involving many participants and roles, model an Event entity and role-labeled edges (e.g. participant, witness, organizer), avoiding a new database table per event kind.

### 4. Assertions and evidence

Wikibase-style *claims about the world*, separate from editorial certainty:
`assertion(id, subject_id, predicate_id, object_entity_id OR literal_value, valid_from/to, status, confidence, source_id, explanation)`.

`source` can refer to external real-world historical evidence, in-universe chronicles, author decisions, or editorial research notes. Preserve source type; **an in-universe unreliable narrator is not authoritative canon**.

Allow simultaneously recorded inconsistent claims for disputed history without silently choosing one. Use `status=established|working|disputed|rejected`; provenance and dates are first-class. Implement facts as relationships or assertions **once**: avoid duplicate authoritative edges in two tables. In first implementation, use the **relationship table as entity-to-entity assertion** with a claim status and supporting evidence; add separate scalar assertion support only for quantitative/other literal facts.

### 5. Temporal meaning

Model **when an event occurred** separately from **when the author recorded it**. `valid_from` and `valid_to` represent history; `created_at`/`updated_at` represent editing time.

Partial/uncertain dates are not guessed into fake exact calendar dates. Begin with `year_start_min, year_start_max, year_end_min, year_end_max` or a modest `time_expression` structure; allow `unknown`, `circa`, and open-ended intervals. The Year 0 offset should be configurable so shifting the Cascade date does not require retconning all relative chronology.

A later query `as_of(year)` includes facts known to be applicable, flags possible/uncertain matches, and excludes things known to have ended. Never imply exactness from approximations.

### 6. Generic structural relationships vs special views

- **Genealogy**: ancestor, descendant and household views built from person-to-person kinship and union records, with distinction between biological, adoptive, legal and claimed links.
- **Maps**: places and geographic geometries plus time-bounded location, administrative and travel edges.
- **Timelines**: dated event records and participants.
- **Political atlas**: organizations, territorial claims, tenures, treaties and offices.
- **Trade network**: settlements, routes and commodity relations.
No separate person/household graph with a competing store of truth.

## Storage proposal

### Minimum normalized tables

`entity`, `alias`, `predicate`, `relationship`, `content_link`, `event_time`, `source_reference`, `editorial_change`.

Indices:
- entity type, status, ID;
- normalized alias/name with type/location filter;
- relationship subject, object, predicate and validity;
- link source and target;
- event dates and place;
- FTS5 indexed title, aliases and prose, updated transactionally (trigger or explicit index rebuild strategy);
- optional RTree/spatial index **only after** actual map data exists.

Enforce `PRAGMA foreign_keys=ON` on each connection; use transactions for all writes. Restrict destructive deletes when referenced, offering explicit **merge/redirect** workflows. Backups, schema migrations, validation and restore tests precede large imports.

No separate graph database: recursive CTE traversal suffices for modest local networks. Do not render every edge at once; filter/cap traversal depth and nodes.

### Git integration

- Existing `bible/` and `regions/` Markdown remain legible.
- Export canonical article bodies with stable `id` and type metadata, plus machine-readable structured records and source maps. Generate the discovery index; never manually duplicate it in JS.
- Import changes with content hashes / last-committed revision to detect conflicts. Reject non-lossless roundtrips and force manual review of collisions.
- Git commits serve editorial snapshots, not a substitute for atomic database writes.
- Backups and export/import must work offline.

## Reliable automatic linking

**Pipeline**: tokenize/index names and aliases → identify possible spans in prose → rank candidates → disambiguate → user accepts/dismisses → persist an ID-based content link.

Ranking signals, in order: exact multiword alias > explicit manual link > page/type context > location/era compatibility > popularity; ambiguous short names must be confirmed. Favor a simple trie/Aho–Corasick matcher or precompiled name dictionary for large text, not N×M rescans per keystroke. Run on editor pause/changed paragraphs; ignore code blocks, markup, existing links, quotations and dismissed occurrences.

Show a “Possible references” tray with source sentence, candidate type, place/time and reason. Distinguish:
- exact known reference;
- ambiguous entity;
- possible missing entity;
- inferred possible semantic relationship (**never** auto-confirm).
All suggestions should be reversible with provenance. False positives are an explicit performance metric.

For rich text, Tiptap/ProseMirror can represent stable-ID inline references as editor nodes/marks; preserve valid markdown serialization and round-trip tests.

## Discovery beyond name matching

1. Full-text lexical search + aliases, filters and backlinks (first milestone).
2. Graph views: two-hop relationships, linked people in a settlement, all entities affected by an event.
3. Integrity: orphaned pages; dangling links; duplicate-looking names; parentage cycles; impossible or uncertain chronologies; contradictory exclusive tenure.
4. History: as-of-year relationship views, migration history, settlement population snapshots, causality chains where explicitly authored.
5. Later, **optional AI/embedding-assisted candidate discovery** based on the same canonical records, always with quoted supporting context and review. Do not let semantic similarity become historical truth.

## UX contract (one integrated system)

Left: Search, categories, recent entries, collection navigation.
Center: generous freeform article editor with contextual fields only where appropriate.
Right: suggested links, backlinks, relationships, sources and contradictions.
Focused view switcher: article / timeline / family / map / relationships; no independent unsynchronized mini-apps.
People and place entries are the same editorial experience with different useful contextual views.

## Implementation order and acceptance tests

### Phase 0 — Preserve and inventory (blocking)
- Import every existing `bible/` and `regions/` article into an entity inventory **without changing its prose or existing links**.
- Reconcile `discovery/index.json` and current genealogy exports; preserve stable existing IDs as legacy aliases/mapping.
- Record input checksums; test deterministic lossless export.

**Gate:** all existing content survives a round-trip byte-for-byte, or deliberately approved normalization; no duplicated entry identities.

### Phase 1 — One shared relationship core (blocking)
- Implement SQLite migrations and stable IDs, types, aliases, typed relationships, content references, provenance.
- Query inbound/outbound references, ancestor paths and as-of relations.
- Safe deletion/merge semantics and automated tests.

**Gate:** rename preserves references; repeated import is idempotent; invalid foreign links are rejected; duplicate creation doesn't proliferate; no genealogy cycles.

### Phase 2 — The real authoring loop
- Integrated editor with link suggestions, disambiguation and accept/dismiss; reliable Markdown roundtrip.
- Backlink browser and a filtered neighborhood relationship view.
- Persistent edits with audit history, Git-friendly exports.

**Gate:** add text “Big Bear”, accept one target, rename target, save/reopen, retrieve working link and backlink; ambiguous “Astoria” never auto-links to an unrelated person.

### Phase 3 — Historical discovery and genealogy
- Person/household graph and event timeline from same records.
- Date uncertainty, evidence and contradictory claims.
- Geography with time-aware boundaries/locations.

**Gate:** a person moves between settlements, joins an institution, marries, then dies; all regional, family and chronological views agree for Year 20 vs Year 50.

### Phase 4 — Scale and polish
- Incremental indexing; performance profiling at 10k/100k entities, relationship fanouts and long chapters.
- Import/export recovery, backup integrity, deletion audit, conflict handling, search quality metrics.
- Optional GEDCOM 7 and other interchange after lossless internal editing is proven.

## Explicit non-goals for v1

- A general-purpose fully RDF/OWL-compliant triplestore.
- Sophisticated AI entity resolution, LLM-inferred canonical facts.
- Distributed real-time collaboration.
- Hand-maintained discovery lists or duplicate editors.
- Complicated dynastic or inheritance simulators before basic cross-linking works.
- Premature microservices, plugin frameworks or graph databases.

## Research references

- [SQLite FTS5](https://www.sqlite.org/fts5.html)
- [SQLite foreign keys](https://www.sqlite.org/foreignkeys.html)
- [SQLite recursive CTEs](https://www.sqlite.org/lang_with.html)
- [Wikibase claim/reference/qualifier data model](https://www.mediawiki.org/wiki/Wikibase/DataModel)
- [W3C PROV-O provenance ontology](https://www.w3.org/TR/prov-o/)
- [W3C OWL-Time](https://www.w3.org/TR/owl-time/)
- [Tiptap mention nodes](https://tiptap.dev/docs/editor/extensions/nodes/mention)
- [Tiptap suggestions](https://tiptap.dev/docs/editor/api/utilities/suggestion)
- [GEDCOM 7](https://gedcom.io/specs/)

See [current architecture](08-world-bible-architecture.md) and [linking requirements](09-linking-and-discovery.md).
