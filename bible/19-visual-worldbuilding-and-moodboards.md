# RFC 019 — Spatial Inspiration & Connected Worldbuilding Workspaces

**Status (November 2026):** first working moodboard workspace integrated into the local World Bible Studio. Advanced template layouts, connectors, automated palette extraction, per-card media annotations, collaborative sessions, and publishable exhibition boards remain future work.

## The product lesson

The New World should have two first-class forms of creativity:

1. **Structured history:** people, places, events, organizations, families, temporal claims, sourced lore, and maps belong to authoritative linked records.
2. **Visual exploration:** references, sketches, images, materials, palettes, notes, and ideas need a flexible space before they are stable enough to become established facts.

The second form should *inform* the first without automatically converting provisional reference material into canon. Conversely, readers should receive curated finished encyclopedia pages, not an accidental public feed of creators' research boards.

This is a generic feature of the Studio engine, not a hardcoded The New World board.

## Research: what to adapt, not merely copy

### VVD: connected spaces and document types

- [VVD's toolkit](https://app.vvd.world/) groups authoring, mapmaking, canvases, relationship graphs and custom wikis in one world. Its [legacy presentation](https://legacy.vvd.world/) explicitly calls out the visual canvas, custom types, rich-text editor and world atmosphere.
- Its [document model](https://docs.vvd.world/docs/concepts) treats cards, maps, timelines, and other tools as documents belonging to a world.
- We should retain the core principle of **one world, multiple interactive views**, but avoid copying one competitor's styling or forcing every tool into a generic, opaque document blob. Our existing SQLite models already represent historical relationships and media with stronger typed integrity.
- The reader remains a different product using publication-filtered projections; authoring affordances do not leak into a visitor encyclopedia.

### Canva: direct manipulation and a compact tool palette

- [Canva's Whiteboards guidance](https://www.canva.com/help/expand-to-whiteboard/) combines shapes, sticky notes, text, images and free positioning into a visual workspace.
- [Canva's concept-map help](https://www.canva.com/help/visualize-ideas-concept-maps-whiteboards/) emphasizes nodes, connectors, an expanding canvas, and user-controllable placements.
- [Its Tools Tab](https://www.canva.com/help/tools-tab/) favors immediate access to a small set of high-frequency tools rather than deeply nested menus.

**Adaptation:** a dedicated board workspace, top toolbar with Note / Image / Upload / Linked Entry / Color, searchable visual asset picker, drag positioning, resize handles, zoom controls, contextual card editing, and visible creation state. Start with a bounded scrollable 2D workspace; avoid premature generic infinite-canvas engines, compositing layers and rendering frameworks. The user wants understandable control over their visual development, not a graphics editor clone.

### Notion: multiple views over the same records

- [Notion database views](https://www.notion.com/help/views-filters-and-sorts) allow tables, boards, lists, gallery and timeline over the **same underlying pages**, avoiding separate copies.
- [Notion's gallery advice](https://www.notion.com/help/galleries) explicitly mentions moodboards; preview and card order are adjustable independently of the content.
- [Notion's relation properties](https://www.notion.com/help/relations-and-rollups) link records bidirectionally rather than duplicating their contents.

**Adaptation:** a visual card points to its actual \`entity_id\` or \`media_id\`, while its layout, local caption and visual color are specific to that board. A linked entity card opens the source encyclopedia entry. Renaming a world entity changes the referenced title in every board. Deleting a board must **never delete** the underlying image or person/location/faction. Deleting an entity clears that placement's reference instead of silently moving it to another world.

## What is implemented

- World-scoped \`moodboards\` with title, description, optional linked canonical entity, creation/update timestamps.
- World-scoped board cards: \`note\`, \`image\`, \`entry\`, \`swatch\`. Each stores \`x,y,w,h,z\`, optional board-local text, optional palette color and foreign keys for source assets.
- Studio's seventh main workspace: **Moodboards**, with board library, composition canvas and clear authoring-only labelling.
- Board creation form with optional associated encyclopedia entry.
- Searchable visual picker for images and encyclopedia entries, with no arbitrary 40- or 150-item cap.
- Drag-to-move, resize handle, zoom slider, optional foreground ordering, board-local card editor.
- Direct image upload through the existing media ingestion pipeline, reusing originals and previews.
- SQL foreign-key checks, world isolation, integrity tests, safe deletion and full SQLite/media backup support.
- JSON export includes board metadata; the data-only importer currently rejects archives containing moodboards rather than silently losing them. Use the complete archival backup for them.

**Not yet implemented:** live multiuser editing, automatic color extraction, 2D image cropping/masking, freehand pen strokes, image-rights assertions, board version history, reusable board templates, automatic background image and galleries in public articles, thematic presentation of *published boards*, and smooth infinite-canvas pan/reflow.

## Design constraints and non-goals

- Moodboards are **private working material** in the Studio by default. They are *not* automatically published because their content might contain drafts, third-party references or contradictory visual research. A separate reviewed "Editorial Exhibition" publishing layer should eventually support curated public visual stories.
- Moodboards do not assert claims. A board may juxtapose conflicting cultural references or tentative geology without becoming established lore.
- Existing entry and media IDs remain stable. Board-local captions are not the primary canonical image title or article summary.
- A board may be associated with one canonical entry without changing the entry's actual relationships. Additional entry cards are cross-references, not \`related_to\` facts until the author deliberately creates a relationship.
- The design must remain navigable through text and keyboard controls. Drag-only interactions need non-pointer alternatives; cards expose Edit, layer actions, and numerical dimensions.
- No unsourced stock images are inserted into The New World by the software. Reference provenance must remain visible and preserved.
- No hidden use of external AI generation, remote uploads, or third-party asset scraping.

## Next design milestones

1. **Canvas refinement:** better pan/zoom hit testing, copy/paste, select/move several cards, snap/grid, keyboard nudging and alignment guides, undo/redo, reliable move/resize conflict handling.
2. **Board structure:** editable columns/frames, themed regions, card grouping, saved views and reusable moodboard templates for city design, architecture, faction visual identity, clothing, climate and historical eras.
3. **Research clarity:** image citations, URLs, license/permissions, creator credits and "inspiration vs canon illustration" status, plus source review before publishing.
4. **Entry integrations:** an entry's private moodboards listed in its author inspector; related boards surfaced from the Media Library. Never make private board content automatically reader-visible.
5. **Reader presentation:** curated public exhibitions, visual essays and chaptered journeys, with explicit review/approval and independent publication status.
6. **Interchange:** lossless data-only JSON migration of no-image boards; versioned board schema, optional export to PNG/PDF, with a full backup for originals.
7. **Usability research:** scenario testing with novice readers and heavy creators, task completion, first-click accuracy and recoverability after errors—not just subjective beauty.

## Verification scenarios

- Create a board in World A linked to a location. Add a note, a color, a shared image and a faction record. Move/resize. Reload. All elements should persist.
- Rename the faction. The board displays its new canonical name.
- Remove an image card; the original asset and other uses still exist.
- Create World B. None of World A's boards, source references or images become available.
- Delete a board. The linked place, faction, and shared image survive.
- Create a complete archival backup and restore. Both board layout and image binaries survive.
- A visitor accessing the reader cannot accidentally discover or query private draft moodboards.
- No image canvas is required to use the conventional encyclopedia or chronology; powerful visual tools complement, rather than replace, structured worldbuilding.

## Official references

- VVD: [Toolkit](https://app.vvd.world/), [Document and era concepts](https://docs.vvd.world/docs/concepts), [Canvas description](https://legacy.vvd.world/)
- Canva: [Whiteboards](https://www.canva.com/help/expand-to-whiteboard/), [Concept maps](https://www.canva.com/help/visualize-ideas-concept-maps-whiteboards/), [Tools Tab](https://www.canva.com/help/tools-tab/)
- Notion: [Gallery view](https://www.notion.com/help/galleries), [Database views](https://www.notion.com/help/views-filters-and-sorts), [Relations and rollups](https://www.notion.com/help/relations-and-rollups/)
