# World Bible Studio — reusable local-first application

The studio is **a generic multi-world editor**. “The New World” is included as an optional initial world, not encoded in the entity model, chronology, or themes.

## Start

Requires Python 3.11 or newer. Pillow is needed for safe image uploads; all other server capabilities use the standard library.

From the repository root:

**Quick start:** `python app/launch.py`. On Windows, you can double-click `Launch-World-Bible.cmd` in the repository root. The launcher imports only missing Markdown articles, then opens the local site.

For individual steps:

1. Install image dependency: `python -m pip install -r app/requirements.txt`
2. Import existing Bible pages once: `python app/seed.py`
3. Run the local application: `python app/server.py`
4. Open **http://127.0.0.1:8765/app/** in your browser.

The server listens on **127.0.0.1 only**. It is not authenticated or designed for public Internet hosting. Back up the **.worldbible** folder, including its media directory and SQLite database; the export button currently produces structured JSON **without image binaries**.

If you want a separate world, choose **+ World** in the header. Entries, links, relationships and images never cross world boundaries.

## Navigate the Studio

The interface is organized into **seven clearly distinguished workspaces**: Overview, Encyclopedia, Atlas, Chronology, Connections, Media Library, and Moodboards. The selected world is always shown in the top bar; the entry explorer groups entries by type and highlights the current record.

Inside the Encyclopedia, each entry has **Read**, **Write**, **Design**, and **Explore** modes, with contextual instructions and a wider focused canvas for editing. Design mode includes sortable sections, a live page preview, theme presets, and optional accent overrides.

Use **Ctrl+K** to jump to library search or **Alt+1–7** for workspace navigation. See the [Navigation and Editing Guide](NAVIGATION.md) for the mental model, capabilities, and limitations.

## Visual development and moodboards

The Studio's **Moodboards** workspace is a dedicated, world-isolated space for visual research, accessible from its main navigation rail (Alt+7), the Overview dashboard, or an encyclopedia entry's **Explore → Visual research boards** section.

A moodboard can be associated with a specific place, person, society, family, event or other world entry. It holds reusable media, linked records, freeform notes and color swatches. Use the visual picker or upload an image directly; drag and resize cards to develop a look and feel. Click **Edit** on a card to change its caption, palette or exact dimensions. Image credits remain attached to source media.

**Key distinction:** adding an entry to a board does not create a new canon relationship, and adding an image does not create a new image copy. Moodboards are private design workspaces, **not published visitor pages**. Publishing curated exhibition boards is a separate planned feature.

Existing full-archive backups include all moodboards and media. JSON-only data interchange lists board metadata, but its current importer refuses boards rather than losing their source references; use the full backup utility for portable board restoration.

[**VVD × Canva × Notion research and moodboard architecture**](../bible/19-visual-worldbuilding-and-moodboards.md)

## Explore geographic historical depth

The [historical atlas](../history/README.md) uses **ten source chapters**, linked by nine `narrows_to` relations: world → Western Hemisphere → United States → Western United States → California, Oregon, Wyoming → Southern California, Clatsop County and the unresolved Wyoming ranch study. These records appear in the Studio Encyclopedia and Connections, and can be explicitly published to the reader. Published articles expose **wider context** and **go deeper** links. No artificial details have been assigned to the unidentified Wyoming ranch or reservation.

## Populate The New World from established source entries

The repository includes [the structured initial canon inventory](../canon/entries.json) and a [provenance and coverage guide](../canon/README.md). Running `python app/launch.py` or the Windows launcher automatically loads missing material into the dedicated **The New World** world.

A fresh import currently yields **125 world-content records** (20 source articles and 105 distinct structured entries) and **159 typed relationships**. The original plague and Cascade articles are authoritative and are not duplicated. The starting timeline now includes **January 1, 2018–November 17, 2026 documented world history**, across public health, economy, international trade, politics, war, climate and AI, followed by the fictional December 2026 AGI announcement and the 2027–2029 automation and labor crisis. Structured records are searchable and linked through the Encyclopedia, Chronology and Connections workspaces; geographic entries intentionally do not invent coordinates where no source establishes them.

Importing preserves all prior local edits, publication settings and manually authored pages. A one-time migration safely removes untouched *non-world* software-document entries after writing a complete backup. It reports edited or published copies for manual review. No content is published to the reader automatically. You can inspect records individually and publish approved entries through the Studio.

## Available now

- Multiple independent worlds with editable names/description, search/filterable entries, and custom entity categories (person/place/event/organization/family/source and other user-defined types).
- Rich long-form Markdown editing, status, aliases, optional year and coordinates.
- Stable-ID article links (`[[uuid|visible name]]`), automatic backlinks, reviewable name-match suggestions.
- Typed and custom-named dated relationships (kinship, membership, geography, trade, claims, governance) with parent-cycle protection and a small relationship graph.
- Individual kinship summary (parents/children/partners) derived from shared relations.
- Event chronology filtered by time and connected entities; year values are currently **world-relative**, not full uncertain Gregorian/relative conversion.
- Zoomable/pannable **2D map** with coordinates, OpenStreetMap reference tiles, labels and year filter. Online tiles require internet; historical shapes and advanced GeoJSON editing are not yet available.
- Image library upload (PNG/JPEG/WebP with validation and previews), reusable article placements, editable alt text, credits, captions, hero and gallery.
- Per-entry theme selection and accent, optional reorder/visibility of live content sections, responsive reading view.
- World JSON metadata export, safe restrictive entry deletion, local SQLite transactions.

## Reader-first World Encyclopedia

**Visitors start at the reader, not the editor.** The local application's landing URL is now **http://127.0.0.1:8765/read/**. The authoring Studio remains at **http://127.0.0.1:8765/app/**.

The reader has an editorial world homepage, subject browsing, published-only encyclopedia articles with headings and related reading, media galleries, a 2D atlas, historical chronology, search, and reading preferences. It has **no authoring navigation or editing controls**.

**Publishing is explicit:** selecting an entry in the Studio exposes **Publish/Unpublish**, independent of its editorial canon status. The reader sees only published entries and links between published entries. A published article updates immediately when edited. Drafts remain in the Studio; review prose and image rights before publishing.

### Publish a reader-only static website

After publishing articles, from the repository root:

1. \`python app/publish_site.py public-site\`
2. \`python -m http.server 8000 --directory public-site\`
3. Open **http://127.0.0.1:8000/** to preview the standalone website.

You can host the resulting static directory on an appropriate static host. It includes **only published articles and the media those published articles use**; it does not include the SQLite database, Studio UI, draft articles, or authoring API. The exporter refuses to overwrite an existing non-empty directory and refuses links to unpublished entities until resolved. Multiple worlds with published content require \`--world-id <UUID>\`.

This step **builds** a public-safe static directory; it does **not** upload or deploy your site automatically. Offline maps still require network tiles from OpenStreetMap, and hash-based article URLs are not yet search-engine-optimized. For now, do **not expose the local application server to the public Internet**: it has no authentication and its general authoring endpoints are not a privacy boundary.

See [reader-first UX research and architecture](../bible/18-reader-first-ux.md).

## Reliable complete backups

**Use a full backup before substantial worldbuilding or upgrading the application.** This includes a consistent database snapshot plus originals and previews from the media library.

Create a complete archive (the studio can be running):

- `python app/backup.py create my-world-bible-backup.zip`

Restore the archive (**stop the studio server first**, then use a clean data folder):

- `python app/backup.py restore my-world-bible-backup.zip`

If the target `.worldbible/` already contains data, restore will refuse to overwrite it. Use `--force` only after confirming the server is stopped; the old data directory is moved to a timestamped `.previous-...` folder rather than silently deleted. The archive is checked for directory traversal, per-file SHA-256 integrity and SQLite integrity.

The UI **Export** button produces a separate JSON-only interchange format. It does **not** include image binaries, and imports of such image-referencing exports are deliberately rejected to avoid creating broken media links. UI **Import** creates a new isolated world from a data-only archive and remaps entity IDs and links.

**GitHub is not updated automatically when you edit through Studio.** The SQLite database is the live authority. Back up and export deliberately; Git publishing and round-trip Markdown synchronization are a later integration milestone.

## Limitations and architecture honesty

This is a functional **foundation/MVP**, not yet the complete platform in the RFCs. Advanced page layouts, drag/drop composition, custom theme creation UI, polygon GIS editing, map date precision, source-assertion workflows, graph visualization, GEDCOM import, full database + media restore, robust multi-user conflict resolution, and automatic provenance auditing remain future work. The current prototype preserves Markdown and original media; it does not represent itself as a finished Ancestry/World Anvil equivalent.

**Never run this local server bound to 0.0.0.0 or exposed via a public tunnel without a separate security review.** The write header is a CSRF safeguard, not user authentication.

## Development

- `python -m unittest discover -s app/tests -v`
- The repository GitHub Actions workflow runs these tests.
- Data: `.worldbible/worlds.sqlite3`, `.worldbible/media/` (gitignored).
- All application entities have stable opaque IDs; worlds isolate their data.
- Article hyperlinks are validated; a missing link target causes save to be rejected instead of silently corrupting backlinks.
- Deleting referenced entries is blocked until relations and backlinks are deliberately resolved.

See [Unified Architecture](../bible/15-unified-architecture.md) and [Design System](../design/README.md).
