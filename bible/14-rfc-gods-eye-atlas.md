# RFC 005 — God's-Eye Historical Atlas

**Status:** design proposal; no globe implementation yet.
**Reference:** https://github.com/bilawalsidhu/gods-eye-view (MIT-licensed *code*; third-party assets/data and external services have their own licenses).
**Dependencies:** [knowledge core](10-rfc-historical-knowledge-core.md), [location/faction architecture](11-rfc-location-faction-systems.md), [timeline](12-rfc-timeline-engine.md), [media](13-rfc-media-image-handling.md).

## Purpose

Create a navigable geographical *view of the world bible* analogous to the immersive globe, layered controls, search/fly-to, annotations, bookmarks, and camera navigation in God's Eye View. This is **not** a real-time OSINT platform, AI agent interface, surveillance tool, or simulation of operating military intelligence infrastructure.

The key use case: **globe → continent → watershed/region → town → farm/site**, exploring linked encyclopedia entities and historical information at each scale, with a single shared timeline selector. Clicking a map record opens its normal world-bible entry; editing an entry updates the map.

## Confirmed upstream techniques worth evaluating

The upstream repository's README identifies:
- Cesium-based 3D globe with different terrain/imagery providers and optional photorealistic 3D tiles.
- Point/area navigation, search and fly-to, bookmarkable/shared camera and layer state.
- Interactive layer toggles and a context/detail panel for selected records.
- Director mode annotations, drawn shapes/routes and saved camera scenes.
- Rewind controls for some live environmental visualizations, adapted here to **authored historical dates**.
- Contextual camera movement and different spatial scales.

Retain the conceptual patterns; **do not import** flight tracking, ship identification, public cameras, RF, live feed infrastructure, social/voice/AI interactions, or sensor/targeting UI as design dependencies. Avoid a bloated surveillance dashboard aesthetic for an encyclopedia.

## Spatial model and source of truth

The globe is a renderer and spatial editor for existing records; it is **not** an independent store of places, borders or facts.

For each spatialized entity:
- `entity_id` stable reference to location, route, organization, asset, event or settlement.
- `geometry_id` representing a sourced WGS84 point, polyline or polygon; optional vertical/elevation information where grounded.
- Historical validity date/interval and editorial status (`established/working/disputed`).
- `geometry_role`: physical location, occupied/controlled area, claimed jurisdiction, route, economic reach, migration path, schematic/approximate boundary. Never conflate them.
- `precision/source`: verified measured coordinate, approximate author geometry, modern geographic reference, or in-world interpretation; display distinction in legend.
- Styles/layer assignments are display preferences; not statements of fact.

Preserve the actual geography of Earth, including mountain relief, coastlines, rivers, valleys and modern infrastructure references. Annotate what persists or fails after the Plague and Cascade rather than altering the physical Earth without explanation.

## Required atlas experience

### Navigation
- Globe orbit/pan/tilt with north-up reset, smoothly zoom to regional 2D/3D maps, keyboard/search navigation.
- Search world-bible names and aliases with existing disambiguation mechanism; coordinates only when known.
- Fly-to entity from its encyclopedia article and open article from its map shape.
- Bookmarks/camera scenes linked to entities, years and active layers; URL/share/export state if useful.

### Layers
- Physical: terrain, satellite imagery, modern basemap, rivers, watersheds, water sources.
- Historical settlement: active, abandoned/reoccupied, hypothesized; population ranges and recorded resources.
- Political: governing jurisdiction vs disputed claims vs privately owned/leased land vs military access; each separate layer.
- Transport: historic roads, trails, rail, navigable rivers, ferries and trade routes; operational period.
- Events/migration: dated events, migration corridors, outbreaks, storms and response territories; spatial precision clearly shown.
- Knowledge: unverified facts, incomplete places, unresolved research questions, author notes.

Layer provider terms, required keys, quotas and offline availability must be clearly disclosed. External satellite/terrain imagery is **reference data**, not automatically bundled or distributable with the app.

### Historical time
Single date/year range shared with timelines, genealogies, factions, demographic history and encyclopedia. Historical queries derive which locations, labels, route statuses and jurisdictions are applicable; uncertain dates should render as possible/estimated, not definitive.

A selected Year 20 should not simply recolor today's map: underlying roads, settlement conditions and faction status are dated records. Modern satellite photos may be useful terrain background, but must be marked **modern reference imagery**, not claimed to depict Year 20.

### Editing
- Create/edit points and line/polygon geometries by drawing on globe/map, with explicit role, status, time, label and linked entry.
- Preview/edit/save transaction; no anonymous map pin that cannot be tied back to entity data.
- Import/export GeoJSON (source and provenance retained).
- Measurements for grounded distances/elevation profiles where appropriate, not invented logistics/travel times.
- Undo/redo and geometry validation. Support overlapping territories and multiple geometries for different periods.

### Knowledge navigation
- Pin/shape click: entry summary, alias, backlinks, event/history count, related factions/persons, source/uncertainty badge.
- Relationship graph/map hybrid: spatial lines only for spatial relations such as routes and migrations. **Don't draw family/ownership/diplomatic edges as physical transport routes**; separate annotated graph links.
- Saved thematic scene: selected year + focal geography + overlay layers + highlighted entities + camera, with provenance.

## UI layout suggestion

Map/globe as central focus; left slim library/search and layer browser; right article/details and relation explorer; bottom retractable historical timeline. The editor can swap to full article view without losing selected entity, camera, year or active filters. Preserve desktop performance on modest hardware and accessible 2D fallback.

## Technology recommendation

**Evaluate CesiumJS** as first 3D engine candidate: strong terrain/imagery, camera controls, geometry and geospatial standards. An alternative is MapLibre GL JS with globe projection for lighter vector/2D-centric rendering. Do not commit to both at once or mix two overlapping earth renderers without a demonstrated need.

A practical implementation target:
- World-bible backend: SQLite + article/media storage and temporal/relationship queries from RFC 001.
- Map service: query spatial entities by bbox/zoom/year/layer. GeoJSON first; vector tiles and indexing after data scale justifies it.
- UI: map engine consumes those same records and links back to the editor.
- Asset pipeline: a single media library; separate geographic raster basemap data, which may be externally licensed.

**Potential licensing risk:** upstream repository's MIT source license does *not* imply bundled third-party terrain, images, datasets, photogrammetry or provider feeds are redistributable. Audit assets/provider terms before copying. Initial MVP should run with legal keyless/open providers where feasible; optionally user-configured access to premium terrain/3D tiles. Support offline raster/vector tiles in later phases only with valid rights and sufficient storage.

## Milestones and test gates

### M0 — spatial truth, not a globe demo
- Register a few existing Southern California places as entity IDs, with verified geocoordinates where available.
- Provide bounded geometry, dates, source and state in same entity database; preserve encyclopedia prose.
- Clicking place record yields its entity info/backlinks.

### M1 — thin navigable globe
- Render 3D globe plus terrain/basemap with one working provider and visible attribution.
- Fly-to known world-bible locations, inspect an entry, toggle physical vs settlement overlays.
- Search and switch between mapped places; retain app context on returning to article.
- User can rotate, pan, zoom and reset; fallback when terrain provider is offline/slow.

### M2 — historical layers
- Add timeline scrub and two dated layers (e.g. a route’s operational status and one explicitly *test* faction’s claim) with status/provenance in legend.
- Year-change updates same underlying entities as a timeline/organization detail view.
- Don't represent speculative or missing data as settled political boundaries.

### M3 — geographic editor
- Draw/save point, route and area shapes into the canonical store; undo and audit validation.
- Every shape linked to stable entity ID, dates and source; editing an entity label survives linked map annotations.
- Export/import GeoJSON round-trip without geometry loss.

### M4 — historical analysis and cinematic tours
- Compare two dates side by side; migration routes and settlement change; saved camera bookmarks/tours.
- Optional high-detail models/3D tiles if provider licensing, performance and user needs permit.
- Performance tests for thousands of points, dense overlapping polygons, low-end GPU and intermittent internet.

## Explicitly defer

3D reconstruction of the entire post-Cascade built environment, live aircraft/satellite/ship feeds, voice AI, omniscient factual inference, real-time population movement, physics simulation, and huge high-detail tile caches. Their cost and complexity would swamp the world-bible mission.

## Acceptance example

From the Southern California article click “View on globe” → fly to **Big Bear Valley** (verified actual coordinate) → display local physical relief and known settlements → select Year +20 → view only documented Year +20 jurisdictions/trade routes (with uncertain boundaries visually distinct) → click a governing organization → inspect its article and dated evidence → return to globe with camera/year/layers preserved.

All historical geometry and authority are authored or imported with sources; the globe doesn't guess which faction controls Big Bear at Year +20.
