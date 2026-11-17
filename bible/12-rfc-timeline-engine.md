# RFC 003 — Historical Timeline and Chronology Engine

**Status:** architecture and staged implementation specification. Not an implemented timeline editor.  
**Depends on:** [Historical Knowledge Core](10-rfc-historical-knowledge-core.md), [Locations and Factions](11-rfc-location-faction-systems.md), [Relationship Discovery](09-linking-and-discovery.md).

## Product principle

**Time is foundational metadata for *all* historical entities and relationships, not a separate timeline database.** A historical event exists once and appears on an unlimited number of derived timelines (worldwide, regional, local, organization, person, household, settlement, migration route). Editing its date, participants or locations updates all relevant views through the same entity IDs.

Views must support scale from exact dates to decades and generations, with uncertainty, conflicting accounts, and hypothetical events explicitly marked. An entry's article should remain full-length, searchable and linked to the broader world.

## Research-derived design references

- World Anvil timelines: multiple parallel event lanes, eras, filters, linkable events and reuse across timelines: https://www.worldanvil.com/learn/timelines/timelines
- World Anvil Chronicles: interactive events coupled with changing geographic maps: https://www.worldanvil.com/learn/chronicles/chronicles
- Aeon Timeline: flexible relative/exact dating and event dependency constraints: https://www.aeontimeline.com/guides/add-and-customize-dates and https://help.aeontimeline.com/article/61-dependencies
- W3C OWL-Time: instants, intervals and temporal topological relationships including before, after, overlaps, during: https://www.w3.org/TR/owl-time/
- SQLite: indexed time queries and recursive dependency search using the same relational store: https://www.sqlite.org/lang_with.html

Adapt proven concepts, not proprietary interfaces.

## 1. Temporal objects and identities

- **Event**: entity with stable ID, title, unlimited prose, participants, source(s), category, status, place(s), causal/related event references and time interval. A brief meeting may be a point event; the Great Plague is an extended process with component outbreaks.
- **Period/Era**: independently named interval (e.g., Plague recovery, early Cascade adaptation) with thematic meaning; may overlap and have nested subperiods. Overlap is not an error.
- **Timeline**: saved **query/view definition** with title, description, filters, display scale, time span, lanes and optional curated order. It does **not** own or duplicate events.
- **Historical state**: dated attribute or relationship such as residence, office term, local population, road operation, faction jurisdiction, settlement condition; displayed as intervals, not manufactured standalone events unless there is an actual transition/event.

## 2. Time representation

Separate:
1. **Historical valid time**: when the in-world event or fact took place.
2. **Editorial time**: when the world-bible author created/revised the claim.
3. **Knowledge/canon status**: established, working, disputed, rejected, alternate interpretation; explicitly sourced.

Record calendar basis (`gregorian`, `cascade_relative`), original written expression, precision (`day|month|year|decade|circa|unknown`), uncertain bounds, and whether a start/end is open. Model *bounded possibilities* rather than fake exact timestamps. For example, `between 2034 and 2035` may be stored as start_min=2034 and start_max=2035; don't silently convert it to January 1, 2034.

For v1 keep year-scale temporal constraints simple; add exact YYYY-MM-DD and month granularity when narrative records require it. When there are partial dates, preserve the user expression so round-trip export does not lose meaning.

**Cascade Year 0 is a configurable anchor**, tentatively 2034–2035. Do not hard-code 2035 into every event date. Until anchor is approved, `Year +12` remains relative and conversions to Gregorian date are **a range**, not a false single year. Do not auto-derive 2085 as fixed canon.

Intervals use half-open internal boundaries when precision is exact; human-facing display respects inclusive historical language. Model `before`, `after`, `during`, `starts`, `finishes`, `overlaps`, `meets` and `possibly_overlaps` with uncertainty-aware checks. When data are partial, return `certain / possible / impossible`, not a simplistic boolean.

## 3. Constraints, causality and dependencies

Provide explicit directed event relations:
- `preceded_by` (ordering claim, not necessarily causality)
- `caused_by` / `contributed_to` (historical interpretation with evidence and status)
- `part_of` (subevent/phase)
- `responded_to`, `enabled`, `coincided_with`
- `temporal_dependency` for authoring constraints (minimum/maximum lag, anchor endpoint, optional offset).

**Do not conflate correlation, sequence and causation.** A statement that the World Cup *accelerated* the plague is a working in-world hypothesis, not a demonstrated historical fact. Similarly, pandemic losses precede the Cascade but did not physically cause solar storms.

Dependent dates may move together in a **preview**, but confirmed historical events must never silently change because their precursor's date was edited. Show conflicts and proposed shifts for explicit approval. Detect dependency cycles.

## 4. Parallel and nested timeline views

Start with views saved by filters, not duplicated data:

- **Global Master History**: major world events.
- **Southern California**: pandemic waves, Cajon travel restrictions, migration, regional settlements, political changes.
- **Clatsop County**: coastal pandemic history, local institutions, river trade.
- **Wyoming ranch/reservation region**: locally verified history once exact geography is known.
- **People and families**: births, deaths, marriages, migrations, jobs, life events and household periods.
- **Organizations/factions**: foundation, leadership changes, territories, conflicts and treaties.
- **Places**: settlement phases, population snapshots, construction and abandonment, route openings.

Timeline lanes may show geography, event type, political organization, community, family, or user-selected topics. One event can occupy multiple lanes but remains one entity. Support overlapping events with layout collision avoidance and zoom-responsive grouping, not arbitrarily limited fixed lane counts.

Provide **as-of year** and **range selection** throughout map, relationship, genealogy and articles. Historic state should use the same query semantics everywhere.

## 5. Interface requirements

- Horizontal scalable chronology with era bands, nested intervals, hover summary, click-to-article and zoom (decades/years/months/days as data supports).
- Readable vertical list / table alternative and keyboard navigation for accessibility and very dense histories.
- Focus/compare multiple filtered timelines in parallel lanes, with adjustable chronology scale.
- Event creation from a person, place, organization or article with that entity prelinked as context.
- An event editor with title, rich prose, category, time (including uncertainty), place, participants, relations, references and editorial status.
- Cross-highlighting with location map: selecting a time range updates visible settlements/territories; selecting an event centers applicable locations **when coordinates actually exist**.
- Click a person or organization to see their lifetime/active-period band and relevant events.
- Filter by category, status, geography, house/family, faction, character, source and certainty.
- Source/history panel showing alternate interpretations without presenting them as canon.
- Export as Markdown narrative chronology and structured JSON/CSV; optional SVG/PNG visualization later.

## 6. Proposed SQL extensions to RFC 001

`temporal_expression(id, calendar_basis, original_text, precision, start_min, start_max, end_min, end_max, start_open, end_open, status)` linked to entities and relationship assertion records as required.

`timeline_view(id, title, query_json, lane_config_json, sort_order)`: only filters/presentation; events remain canonical.

`event_dependency(id, antecedent_event_id, consequent_event_id, dependency_kind, offset_min, offset_max, editorial_status, evidence_id)` with FK, DAG validation for strict ordering, and preview-on-change semantics.

Do **not** introduce all of these tables before implementation tests justify them. Start by extending the existing event-time representation and storing the saved view configuration; add dependency calculations when the authoring UI is ready.

## 7. Linking and discovery as part of chronology

Typing “the Cajon Quarantine” should propose an existing event entity when it exists. Mentioning “2031” should **not** create an event automatically. Time-aware discovery should flag likely existing events sharing dates, region, participants and title variants, but must not merge them without review.

Cross-entry discoveries:
- Someone's biography mentions a migration that is not linked to their residence history.
- A faction's founding date follows a treaty where it is supposedly an active party.
- A person appears in a dated event after their established death.
- A bridge is described as destroyed before an event that relied on it.
- A ruling council appears in a territory map years before its recorded foundation.
- A claim of unique ownership conflicts with a second, overlapping established claim.

Provide severity and explanation; allow real-world exceptions or disputed claims. **Warnings are not automatic retcons.**

## 8. Historical timelines for The New World

Do **not** lock the tentative calendar while building the tool:
- 2030 men's World Cup is an actual scheduled anchor in real-world background; pandemic amplification is alternate-history speculation.
- Great Plague: tentative outbreak 2030 and worst waves 2030–2032.
- Partial recovery: roughly 2032–2033.
- Cascade: tentative 2034–2035, Year 0.
- Year 50 reference era: relative +50, approximately 2084–2085 only if the anchor holds.

Keep rural/metro epidemic outcomes as broad history until individual local dates and death rates are actually established. The date engine must support adjusting uncertainty without breaking links or renumbering entities.

## 9. Concrete acceptance tests

**Temporal correctness**
- Store `Year -3` and `Year +12` as relative; changing anchor from 2034 to 2035 adjusts derived Gregorian display but not original meaning.
- Store an uncertain date of 2034–2035; never display an invented exact day.
- Query interval overlap and containment with `certain/possible/impossible` results.
- Established marriage, office tenure, settlement control and migration show consistent state for two different year selections.
- Prevent invalid strict dependency cycles while allowing events to overlap when history requires it.

**Shared data correctness**
- Create a migration event for an individual; it appears in the person's biography, origin/destination settlement timelines and the global view when the filters apply.
- Edit title/date once; all relevant views reflect the change without duplicated events.
- An event with several participants retains one stable ID and source record.
- Time-filtered map and faction graph agree about control or claims in Year 20 versus Year 40.
- Conflicting historical dates from two sources can be shown side-by-side without becoming two canonical events by default.

**Editor and data integrity**
- Export/import round trip preserves date expressions, aliases, IDs, sources and article Markdown.
- Delete/merge previews show affected links and dependent timelines.
- Dense timelines are virtualized or aggregated without changing event data.

## 10. Staged delivery

1. **Temporal core**: define a simple rigorous date/interval representation and query semantics, with tests; integrate with entity/relationship storage.
2. **Timeline MVP**: event editor, one global and several saved filtered regional timelines; links, search, list view, era bands.
3. **Historical graph**: participants, organizations, events, settlement and family filters, temporal relations, uncertain date representation.
4. **Maps and synchronization**: Year X filter shared across map, timeline, relationship/faction and genealogy views.
5. **Deep chronology**: dependency preview, contradiction detection, overlapping parallel lanes, historical comparisons and performance hardening.

**Priority rule:** no stand-alone timeline editor with a duplicate event file. The temporal core must be part of the same application as the location/faction system and general world-bible articles.
