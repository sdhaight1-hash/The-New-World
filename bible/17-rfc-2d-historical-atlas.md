# RFC 007 — 2D Historical Atlas (supersedes 3D-first RFC 005)

**Status:** accepted mapping direction; implementation pending.
**References:** [Unified architecture](15-unified-architecture.md), [Locations/Factions](11-rfc-location-faction-systems.md), [Timeline](12-rfc-timeline-engine.md), [UI/Entry Designer](16-ux-and-entry-designer.md).

## Core decision

Build a **2D-first, layer-driven historical map editor and explorer**. Retain God's Eye View's discoverable spatial layers, fly-to, bookmarks, annotation tools, search and time-aware views, **not** its 3D globe, live sensors, 3D assets or AI. Geographic records and historical facts reside in the common knowledge core. The map reads and edits them via transactions.

MapLibre GL JS is the favored renderer, with 2D camera defaults and bounded pitch (normal pitch 0°). Standard GeoJSON points/lines/polygons for authored data; optional hillshade/elevation visualization as a layer, not a separate 3D engine. Keep base map provider configuration and attribution explicit. Avoid assuming an online tile server or token is permanently available.

## Views and scales

World > continent > region > valley/watershed > town > site. Smooth zoom/search/fly-to; cluster/aggregate at low zoom, preserve labels and shapes at high zoom; user-defined groups and saved views.

Support:
- Geographic reference: terrain shaded relief, water bodies, physical areas.
- Settlements and population snapshots (never extrapolate absent data without labeling).
- Infrastructure: historic roads, rail, bridges, ports, wells, aqueducts, power.
- Factions: **actual jurisdiction**, **territorial claim**, **land title**, **military occupation**, **resource/water right** as distinct styles/layers.
- Trade/migration networks: roads/routes, optional direction and dated flows; don't represent social kinship edges as literal roads.
- Events: plague waves, quarantines, battles, migrations, founding/abandonment events; uncertainty and source.
- Knowledge quality: approximate coordinates/areas, disputed borders, unsourced records.
- Imagery: scans, sketches and historical maps as annotated image overlays **only when georeferenced properly**; never fake accuracy.

## Interactions

Click place shape/pin → entry preview → full article; click faction overlay → claims and evidence with temporal status; click route → operation history, linked communities, relevant events. Search by title/alias/disambiguation; bookmarks record entity ID, layer set, bbox, year and basemap.

**Editor tools:** add/move point; draw/edit line and polygon; set precision, source, role, validity interval and linked entity; history/undo/redo; import/export GeoJSON; flag overlaps and unresolved boundary discrepancies. Geometry without exact coordinates can remain text-only, not displayed with invented position.

Time slider is **shared** with the historical timeline and relationship explorer. If Year +20 is selected, all active/possible claims and settlement state follow the same temporal query semantics.

## UI and visual language

Map controls from the application shell tokens (dark/light/high contrast). Basemap styling and political legend are configured separately from entry page themes so a decorative page palette doesn't make two factions indistinguishable or change historical meaning.

- 2D canvas center; layer tree/search left; context inspector right; collapsible time control below.
- Legend explicitly distinguishes verified / approximate / disputed and jurisdiction / claims / ownership / rights.
- Optional color palettes for *user visualization*, with patterns, line styles and textual labels in addition to color; user's high contrast preference wins.
- Multiple projections optional only when actually needed; GeoJSON import/export WGS84 expected.
- Scale bar, north indicator, attribution and uncertainty display; accessible non-map list of all visible entities.

## Milestones

1. A 2D map of sourced existing places, selection links to encyclopedia entries, base provider with proper attribution.
2. Save/map spatial geometry in shared database, verify link rename and GeoJSON round-trip.
3. Time-aware faction claims and route changes, with missing/uncertain data visible.
4. Draw/edit geometry and import overlays; historical side-by-side compare, saved map views.
5. Performance, offline degraded mode, migration map narratives and accessible alternatives.

**Acceptance:** a Year +20 map and Year +50 map disagree only when **stored dated facts justify** differences. Changing a town's name, time of a boundary claim or a route operation date updates maps, article backlinks and timelines consistently.

## Supersession

[RFC 005](14-rfc-gods-eye-atlas.md) is retained as a historical inspiration document; its Cesium/3D implementation recommendation is **not** current direction. No 3D map is required.
