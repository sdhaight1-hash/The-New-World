# World Bible Studio — Navigation and Editing Guide

## First principle

**World > Workspace > Entry > Task**. Never confuse these layers:

1. **World** (top bar): the independent collection of people, places, organizations, history, sources and media you are working on. Worlds never share the same records.
2. **Workspace** (dedicated left rail): the question or activity you are pursuing across the world.
3. **Entry** (contextual library): the exact person, place, event, family, organization or topic you have selected.
4. **Task** (within Encyclopedia): whether you are reading, writing, arranging appearance or making connections.

Every workspace has a distinctive icon, heading, subtitle, accent and active rail state; the article’s optional theme never alters global navigation. World and selected year are always visible.

## The seven main workspaces

| Workspace | Purpose | Typical actions |
|---|---|---|
| **Overview** | Health and inventory of a world | See counts, recent entries, category breakdown, editorial status, quick jumps |
| **Encyclopedia** | Authoritative long-form entry records | Browse categories, read article, edit prose, design appearance, link to other entries |
| **Atlas** | Geographic view of established coordinates | Browse mapped places and Year X, pan/zoom modern reference map, jump to entries |
| **Chronology** | Historical events | Filter events by an entry and time window, open the canonical event article |
| **Connections** | World-scale relationship inventory | Browse relationship types, most-connected records, and individual typed connections |
| **Media Library** | Reusable image inventory | Search images, review placement counts, navigate to associated entries |
| **Moodboards** | Visual research and art direction | Build boards with drag-and-drop notes, referenced images, linked entries and color palettes; upload and resize |

The right **Record Context** panel is visible only when reading an entry. Writing, Design and Explore expand the central canvas to avoid repeating controls. Other workspaces use their own dedicated panels.

## Start a new record

Click **+ New** in the Entity Explorer or **Create entry** on Overview. Choose a record type and decide whether to use an **editable starter outline**. Different types suggest different sections and use appropriate initial article themes (for example, Atlas for places and Civic for organizations). These are writing aids only—no fictional facts, coordinates or organizations are generated for you.

## Four entry tasks

- **Read**: article as a reader encounters it, with contextual references, status, maps and relevant media.
- **Write**: title, metadata, aliases and long-form Markdown; use **Discover references** for human-reviewed stable-ID links.
- **Design**: appearance themes, optional custom accent, visible section ordering; drag to reorder or use keyboard-reachable arrow buttons. Live presentation preview shows the resulting article sections. Changing layout does not change factual records.
- **Explore**: add or inspect dated typed relationships, genealogy links, image placements, backlinks and direct relationship diagram.

## Usability contract

- The active workspace is communicated by title, subtitle, distinct accent, **and text**; color is not the sole cue.
- A selected entry remains clear in the library and breadcrumb; switching workspaces does not alter its identity or factual contents.
- Switching worlds resets search/media filters so the new world never silently inherits the previous world's empty result set.
- **Ctrl+K / Cmd+K** focuses library search.
- **Alt+1–7** navigates Overview, Encyclopedia, Atlas, Chronology, Connections, Media Library. Browser/OS shortcuts can sometimes take precedence.
- Dark, light and high-contrast global appearance choices do not overwrite per-entry themes.
- Unconfirmed historical knowledge is clearly editorially marked. A modern OSM basemap is a geographic reference, not a Year X historical photograph.
- Data-only JSON export is not a complete media backup. Use [the complete archive utility](README.md#reliable-complete-backups).

## Technical architecture

The front end remains a single local web application using the shared SQLite API. Workspace views do **not** own separate data stores, so a dated faction relationship appears in the relevant entry and Connections workspace, and a single image may be used by multiple entries. The Media Library receives a world-scoped usage index. The entry Design layout is presentation metadata, not a second copy of the article.

The initial page designer uses an ordered set of live blocks, not unrestricted arbitrary HTML/CSS. This is deliberate for portability, historical consistency, accessibility and import/export safety. A richer nested visual canvas is a future milestone.

## Quality gates

GitHub Actions tests backend integrity (multi-world isolation, image reuse, stable backlinks, ancestry cycle checks, full backups), compiles Python, validates JavaScript syntax, verifies idempotent Markdown import, and runs a headless Chromium browser smoke test across workspaces and entry modes.

**Current limitations**: no completed polygon editing, fully semantic historical assertions, large-scale full-text indexing, freeform multi-column designer or extensive browser visual regression suite. This document describes the *working navigation model*, not an assertion of complete feature parity with World Anvil or Realm Works.

## Reader experience is a separate product

Visitors enter the editorial encyclopedia at `/read/`, without a creator navigation rail or authoring controls. The Studio remains at `/app/`. Publishing a record is a deliberate action separate from marking its canon status; the reader displays published records and linked published relationships only.

A standalone reader-only website can be generated using `python app/publish_site.py public-site` after publishing at least one entry. It contains only approved public records and their referenced images; no Studio API or draft database. See the [reader-first research](../bible/18-reader-first-ux.md) and [static publishing guide](README.md#reader-first-world-encyclopedia).

## Visual composition workflow

In the Studio, open **Moodboards** from the world rail. Create a board with a descriptive name, optionally associate it with an existing canon entry, then compose with **Note**, **Image**, **Upload image**, **Linked entry**, and **Color**. Search for existing assets in the visual picker rather than duplicating them. Rearrange cards by dragging their headers; resize with the corner handle or set exact width and height through **Edit**. Colors, captions, and locations are board-specific; canonical article prose and reusable image originals are unaffected.

For a board specific to a place, faction or character, open its entry → **Explore** → **Visual research boards**, where associated boards can be opened or created.

Boards are working material and are not automatically reader-visible. Full database-and-media backup preserves them. See [the visual development research](../bible/19-visual-worldbuilding-and-moodboards.md).
