# Architecture Decision Record 001 — Unified World Bible Platform

**Decision:** Accepted design direction, implementation pending.  
**Supersedes conflicting architectural guidance** in RFCs 001–005; the RFCs remain research/history, not independent mandates.  
**Scope:** global alternate-history encyclopedia, with historical atlas, genealogy, organizations, timelines, media and discovery.

## Product boundaries

This is an **editorial research and worldbuilding system**, not a game engine, story generator, 3D surveillance globe or simulation platform. Ordinary settlements, people, households, institutions and histories are as important as noble lineages. Everything is optional except stable identity and readable prose.

### The central invariant

**One world, one identity registry, one writable authority per record.** Every map, timeline, pedigree, organization diagram, relationship graph, article and gallery is a view over shared entities and facts.

- **Entity**: person, place, settlement, event, family/household, organization, material asset, topic, source.
- **Relationship/assertion**: directed typed fact, effective time, editorial status, provenance; links are not automatically proof.
- **Content reference**: authored mention linked to a stable target ID; backlinks derived, never manually synchronized.
- **Media**: canonical image/asset with immutable versions, placements, annotations and attribution.
- **Presentation**: page composition, appearance tokens, custom components and per-entry overrides stored separately from canon.
- **Saved view**: filters, map camera, selected time, layer state, relation scope and chosen layout; not duplicated history.

**No duplicate authoritative person record in genealogy, location record on a map, or event inside a timeline.**

## Architectural layers

1. **Storage**: SQLite with WAL, FK constraints, transactional writes, migrations, FTS5; media originals stored as managed file blobs; human-readable Markdown and data exported to Git.
2. **Domain service**: typed entities, aliases, claims, evidence, dates, relations, referenced content and media; mutation validation, cross-domain queries and history-aware state. This is the **only write API**.
3. **Indexing and discovery**: full-text + exact alias matching, backlink and graph traversal, ambiguity review, contradiction warnings. Derived indexes are rebuildable from canonical records.
4. **Presentation engine**: renderer of safe, validated entry-layout documents; responsive templates, styles and media *reference canonical IDs*. Never embed historical data as independent page-builder JSON facts.
5. **Feature views**: editor, entity explorer, genealogy, faction map, 2D historical atlas, parallel timeline, galleries, sources/continuity audit. They all consume the same APIs.
6. **Export/backup**: deterministic Markdown + JSON/GeoJSON + managed asset manifest; Git is archival version history, SQLite is live transactional authority. Imported edits require conflict checks.

### Technology choices

- **Application direction:** local-first web UI served by a small local backend. Favor TypeScript for UI and schema, SQLite for persistence, without committing to a large desktop shell. Framework selection remains implementation work; avoid premature Rust+JS dual-core or microservices.
- **Authoring:** Tiptap/ProseMirror-style structured rich text with Markdown import/export, strict node schema and stable inline reference IDs. Non-supported imported structures must be reported, **not silently lost**.
- **2D atlas:** MapLibre GL JS (not Cesium-first); GeoJSON for initial routes/points/polygons, vector tiles if actual scale warrants. Support conventional 2D views with hillshade if useful. RFC 005's 3D-first globe is **superseded**.
- **Graph views:** a constrained local neighborhood drawing; collapse/filter huge graphs. Graph visualization is optional; link lists are authoritative and accessible.
- **Styling:** CSS custom properties driven by validated design tokens and theme inheritance, not arbitrary CSS injection.
- **Images:** managed original blobs, generated previews, placements and optional linked hotspots, with source/license metadata.
- **Tests:** unit validation, SQLite integration tests, import/export golden files, UI workflows, accessibility and visual regression.

## Canon, uncertainty and provenance

Treat editorial state (`established / working / disputed / superseded`) independently from in-universe point of view and dated validity. An in-universe chronicle may be wrong. The Great Plague may be anchored to 2030 tentatively without forcing every dependent date to a fixed Gregorian year.

Time filtering must distinguish **known-valid, possibly-valid, and known-not-valid** assertions, and must not silently promote missing facts to certainty.

## Entry and page structure

A page has four independent pieces:

- **Identity**: stable entity ID/type/aliases, with links and bibliography.
- **Substance**: unlimited prose, structured facts, events, related entities and media.
- **Composition**: an ordered tree of supported layout blocks referencing those sources.
- **Appearance**: a resolved theme preset + limited typed overrides; personal accessibility preferences can supersede presentational cosmetics.

This enables each article to look like a historical document, local gazetteer, family album, scholarly report, settlement dossier or faction chronicle **without changing its data model**.

Layouts can be copied as templates. A template's graph/timeline/map/related-people sections resolve live against the entity; copying the template does not duplicate records.

## Canonical editor navigation (same everywhere)

Global app chrome: search, library navigation, recent history, selected historical date, active workspace/world.

Entry workspace: article canvas center; relationships/backlinks, references, contextual facts, media and discoveries in a right inspector; left explorer collapsible; editable page layout and theme from an explicit **Design** mode. Keep **Read**, **Write**, **Design**, and **Explore** modes distinct while preserving selection/camera/time context.

A user's selected dark/light/high-contrast preference is global. An entry-specific theme colors its canvas, highlights, header, cards and decorative elements, not every toolbar and app control.

## Visual identity and theme precedence

1. Accessible/contrast/motion preferences set the **constraints** for all colors and effects.
2. Stable application shell theme remains consistent.
3. World preset applies to entry canvas.
4. Entity-type preset provides an optional visual starting point.
5. User-selected entry theme override changes canvas appearance.
6. Per-block style overrides are allowed only for approved properties/values.

**No auto-color change just because the page mentions a faction or region.** Explicit `theme_ref` and per-entry choice control the appearance; use deterministic fallback. Theme precedence is documented more fully in [Visual Design & Page Builder](16-ux-and-entry-designer.md).

## Migration and hardening

The current repository contains Markdown articles, a manual discovery index, a separate localStorage genealogy workbench, and static HTML reference explorer. Those are valuable *content and prototypes*, but **not** the final application architecture.

**Phase 0 — inventory, no loss**
- Enumerate article paths, image references, index aliases, existing data IDs and genealogy exports.
- Generate stable IDs with immutable import mapping; preserve Markdown bytes and current references.
- Write round-trip tests, collision reports and a manifest.

**Phase 1 — coherent minimal core**
- SQLite schema/migrations, entity/content/alias/typed relation/reference/source storage with integration tests.
- One shared search, backlinks, rename and safe-delete mechanism.
- One unified editor capable of editing an existing article and two linked entities.

**Phase 2 — layouts, appearance, images**
- Validated layout renderer with safe, editable block model and theme presets.
- Design-mode rearrangement, media placement, preview, undo/redo, per-entry theme.
- Export with both portable prose fallback and structured composition metadata.

**Phase 3 — historical views**
- 2D atlas, chronology, genealogy and organization views querying one historical service.
- Year selector and uncertain dates preserved; no duplicated timeline and graph events.

**Phase 4 — discovery, research and scale**
- Candidate linking, ambiguity review, provenance, visual graph discovery and contradiction audits.
- Performance and accessibility testing; backup/restore, corruption and merge tests.

**Stop rule:** No separate new localStorage mini-apps; each feature must participate in the shared core, or remain an explicitly non-canonical preview.

## Release gates

1. **Integrity:** zero dangling references after rename/import; invalid FK rejected; cycle/temporal anomalies reported.
2. **Round trip:** original article prose and existing media preserved, plus stable IDs/claims/layouts after export-import.
3. **Editor:** add a person and place, link them, author an event, attach image, style page; every view resolves same target.
4. **Design safety:** arbitrary pasted HTML/CSS/scripts never execute, unknown block/theme properties fail validation, no invented facts in decorative content.
5. **Accessibility:** WCAG 2.2 AA contrast for core content/UI, keyboard equivalent for rearranging blocks, reduced-motion and high-contrast modes; readable fallback for maps/graphs.
6. **Historical:** Year +20 and Year +50 views show correct time-qualified claims with uncertainty surfaced.
7. **Recovery:** autosave is transactional; backup restored; export from clean clone reproduces expected corpus.

## Status of older documents

- [RFC 001 Knowledge Core](10-rfc-historical-knowledge-core.md): retained; normalized here.
- [RFC 002 Locations/Factions](11-rfc-location-faction-systems.md): retained.
- [RFC 003 Timeline](12-rfc-timeline-engine.md): retained.
- [RFC 004 Media](13-rfc-media-image-handling.md): retained.
- [RFC 005 3D God's-Eye Atlas](14-rfc-gods-eye-atlas.md): **superseded for primary spatial UI** by 2D-first decision; its layered exploration/bookmark concepts remain useful.
- [Visual design, theming, and entry builder](16-ux-and-entry-designer.md): implements the new presentation contract.
- [2D Historical Atlas](17-rfc-2d-historical-atlas.md): authoritative map direction.
