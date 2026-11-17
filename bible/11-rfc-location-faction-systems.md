# RFC 002 — Location Builder and Organization/Faction System

**Status:** research-backed implementation specification, not a claim of completed interactive tools.  
**Depends on:** [RFC 001 historical knowledge core](10-rfc-historical-knowledge-core.md) and its stable IDs, dated relationships, sources and shared editor.  
**Scope:** globally reusable, beginning with Southern California, Clatsop County and Wyoming.

## Guiding principle

**Place ≠ settlement ≠ political territory ≠ organization ≠ asset.** These may overlap or change independently. A valley is a landform, a town is a human settlement, a regional state is an organization with jurisdiction, a disputed territorial claim is a dated assertion, and a water system or mill is an asset. All should be linked, not collapsed into one article.

### Competitive references

- World Anvil distinguishes geographic location, settlement and organization templates, including diplomatic webs and interactive maps: https://www.worldanvil.com/learn/article-guides/article-templates and https://www.worldanvil.com/
- Kanka supports parent locations, organizations, mapped pins, relations and linked timelines: https://docs.kanka.io/en/latest/entries/locations.html and https://kanka.io/features
- Historical claims require qualifiers and references: https://www.wikidata.org/wiki/Help:Statements/en
- Geospatial interchange: https://datatracker.ietf.org/doc/html/rfc7946 (GeoJSON)
- SQLite RTree (later if warranted): https://www.sqlite.org/rtree.html
- OGC Simple Feature geometry semantics (later if warranted): https://www.ogc.org/standard/sfa/

Do not copy proprietary interfaces or build a parallel database.

## 1. Location Builder

### Categories are descriptive, not separate tables per category

- Physical features: continent, region, coast, watershed, lake, aquifer, river, mountain range, valley, forest, pass.
- Human settlement: city, town, village, neighborhood, hamlet, seasonal camp, abandoned district.
- Built sites: farm, ranch, estate, warehouse, mill, bridge, pier, church, fortification, well, reservoir, workshop, road or rail segment.
- Administrative/geographic designations: county or census area, reserve, conservation area; dated legal boundaries are separate geometry/claim versions.
- Political territories: **not simply places**; represent the controlling organization and the dated jurisdiction/claim relationship to a spatial feature.

Use one canonical entity record with subtype + optional attributes, not thirty narrowly coupled forms.

### Essential place record

Stable ID, title, aliases, feature/settlement subtype, canonical article, optional parent geographical area, coordinate/geometry, geographical precision, source and status. Settlement-specific contextual data: foundation/abandonment periods, physical constraints, water, food production, transport access, demographics and hazards. Everything remains optional until researched.

**Geometry:** point, line or polygon via GeoJSON Feature references. Do not invent coordinates. All geometries need datum (WGS84 default for GeoJSON), source, precision, applicable time interval, and whether they are **actual geographic**, **approximate**, **hypothesized** or **politically claimed**. Spatial extents should not silently imply jurisdiction.

**Nested locations:** a containment relationship is a time-scoped, directed typed edge. Permit multiple overlapping broader areas (e.g., a place in both a watershed and a county). Prevent cycles within a strictly hierarchical subtype (settlement administrative containment) without forbidding valid overlapping natural regions.

**Historical condition:** a place can be `inhabited`, `partially abandoned`, `ruined`, `reoccupied`, `seasonal` at different periods; store dated observation/assertion entries rather than overwriting its identity or forcing a single always-current status.

### Required location views

- Article with geography, local history, water/food resources, roads, people, factions, buildings, sources.
- Spatial view with selectable base layer and pins/lines/polygons.
- Historic slider `Year -5 … Year 50` filtering known/possible relationships and geometry versions.
- Parent/child geographic browser and “nearby/connected to” links.
- Economic/network view: roads, trails, ferries, rail, trade, water distribution and changing operational status.
- Demographic chart with **separate** migration, birth, plague mortality, later mortality and uncertainty.
- Discovery tray recommending linked entries and missing places; never generating factual entries without review.

### Location validation

Geometric integrity (rings/coordinates if supplied), date precision, parent containment graph cycle detection, dangling route endpoints, impossible claimed populations relative to explicitly modeled resources (warning not automatic rejection), overlapping ownership/jurisdiction ambiguities, conflicting geometry or alias matches.

## 2. Organization and Faction Builder

**Faction** is a convenient *view/category* of organization and coalition records, not a separate universal class with duplicated membership and leadership systems.

Types may include: government, town council, tribal government, ranch collective, family association, lineage house, guild, trade company, church, charitable group, school, militia, military body, caravan company, band, informal coalition.

### Essential organization record

Stable ID, full name and aliases, subtype, charter/founding and dissolution dates (uncertain allowed), article, status, declared purpose, structure and decision process, active geographic focus, institutions, archival sources and symbols. Member counts and resources are **dated estimates**, not fixed static facts.

**Leadership, membership and roles:** link individuals/other organizations via dated `member_of`, `leads`, `affiliated_with`, `branch_of`, `chartered_by`, `employed_by` or custom curated predicates. Model offices and appointments independently so the same person can serve several groups and leadership can change without rewriting the organization.

**Branches/coalitions:** a guild chapter in Astoria is a distinct organization only if it has meaningful autonomous identity/history; otherwise a dated branch relationship or named unit suffices. Mergers, splits, renames and succession require explicit event and predecessor/successor relationships.

**Faction relationships:** `allied_with`, `competes_with`, `trades_with`, `claims_against`, `subordinate_to`, `at_war_with`, `recognized_by`, `treaty_party`. Each is statused, time-scoped and source-backed, with role/terms where needed. A relationship may be reciprocal or asymmetric; inverse labels must be defined.

**Political territory:** state governing organization A `exercises_jurisdiction_in` place B from year N to year M. Organization C may `claims_territory` B simultaneously, without automatically controlling it. Land title, tenancy, water rights, military occupation, taxation and legal jurisdiction are **separate relationships**.

**No forced feudalism:** no default lord/king/ruler requirement. Councils, families, associations, unions, religious organizations and trading groups receive equal organizational tooling.

### Required organization views

- Organization article with historical constitution/structure, members, leaders, symbols, sites, activities and timeline.
- Interactive membership hierarchy, including dated branch structures.
- Diplomacy graph: alliances, trade, disputes, treaty links and hostility, filtered by date.
- Territory map: controlled versus claimed, with **different legend semantics**; disputed overlaps visible.
- Resource / institution links: ownership, access rights, roads, water systems, mills and productive assets.
- History: foundations, schisms, reorganizations, succession, treaties, wars and dissolution.
- Influence analysis as **research-backed relationships**, not a fabricated numerical “power score.”

## 3. Model cross-domain sample (non-canon illustration)

An entity for **Big Bear Valley** (physical region) and an entity for **Big Bear Lake** (settlement) coexist. An **Emergency Council** (organization) is `formed_at` the settlement in Year 0, then `administers` specific places through Year 7. A **Mountain Confederation** (organization) later `recognized_by` some communities and `claims_territory` an adjacent pass but does not necessarily govern it. A **Cajon Route** (transport corridor) connects settlements and has time-varying passability. An **annual market** (event) is held at a site and includes multiple participating guilds. These names are *examples*, not historical canon or newly established factions.

The corresponding person and genealogy pages link to the same council, town, event and market. No one re-enters the information manually.

## 4. Shared editor and templates

The author should always be free to write unlimited long-form prose. A narrow panel provides **optional** relevant fields (e.g. coordinates for place, leadership for organization) and proposed references based on the existing registry. When typing “Cajon Pass,” offer an exact entity link. When writing “administered by,” propose a **reviewable typed relation** if context supports it; never create it silently.

Support images with captions/credits and source references as assets linked to any entity. All entries have searchable tags, aliases and backlinks.

## 5. Implementation in the common core

Extend RFC 001's entity types with `place`, `organization`, `asset`, `route`, `region` **as subtypes**, not necessarily distinct tables:
- `place_geometry(id, place_id, geometry_geojson, source_id, precision, valid_from, valid_to, status)`.
- `observation(id, subject_id, property_key, value, unit, min/max range, year_range, evidence, status)` for population, livestock, resources. Introduce only when actual quantitative data requires it.
- `relationship` already covers containment, jurisdiction, branch hierarchy, membership, marriage, alliances and route endpoints. Create predicate rules rather than special-casing every edge in UI.
- `event` remains entity with dates and participant relationships; place-specific or faction events reference the same event ID.

Keep verified geographic reference data separate from invented post-Cascade assertions, with explicit provenance.

## 6. Acceptance checkpoints

### First working vertical slice
- Create/edit Big Bear Lake settlement record and Cajon Pass route/location records from existing pages, no lost prose.
- Link both to a non-canon *test* organization as `located_in` or `operates_in` with dated relationships.
- Use year selector: past and present membership and jurisdiction views differ correctly.
- Rename organization and place; accepted hyperlinks and backlinks survive.
- Search “Big Bear,” find entity candidates with disambiguation; no auto-assignment of governments or population.
- No geographic coordinates or authority claims are invented to make a map look complete.

### Hardening
- Merge/split/rename history doesn't orphan links.
- A faction may claim a region while another administers it; both facts remain distinguishable.
- One organization can have overlapping membership and independent elected offices without duplication.
- Invalid parent containment cycles, dangling references and impossible dates produce actionable errors.
- Export → reimport → validate yields identical IDs, dates and prose.

### Later features
- GeoJSON import/export and saved map layers.
- Historical territory boundary editing and comparison snapshots.
- Fine-grained political subdivisions, transport networks, resource flow and agricultural carrying-capacity analyses.
- Graph filters and discovered relationship candidates backed by citations.

## 7. Priorities

1. Establish shared entity/relationship core (RFC 001).
2. **Locations and organizations before special-purpose genealogy expansions**: create/edit entities, relations and backlinks in the same UI.
3. Implement geospatial references, basic map view and a date-filtered faction relationship graph.
4. Add advanced territorial polygon editing, conflict analysis and economic simulation only when basic data flow is reliable.

See [World Bible architecture](08-world-bible-architecture.md), [link discovery](09-linking-and-discovery.md), and [RFC 001](10-rfc-historical-knowledge-core.md).
