# World Bible Studio — reusable local-first application

The studio is **a generic multi-world editor**. “The New World” is included as an optional initial world, not encoded in the entity model, chronology, or themes.

## Start

Requires Python 3.11 or newer. Pillow is needed for safe image uploads; all other server capabilities use the standard library.

From the repository root:

**Quick start:** `python app/launch.py`. On Windows, you can double-click `Launch-World-Bible.cmd` in the repository root. The launcher imports only missing Markdown articles, then opens the local site.

For individual steps:

1. Install image dependency: \`python -m pip install -r app/requirements.txt\`
2. Import existing Bible pages once: \`python app/seed.py\`
3. Run the local application: \`python app/server.py\`
4. Open **http://127.0.0.1:8765/app/** in your browser.

The server listens on **127.0.0.1 only**. It is not authenticated or designed for public Internet hosting. Back up the **.worldbible** folder, including its media directory and SQLite database; the export button currently produces structured JSON **without image binaries**.

If you want a separate world, choose **+ World** in the header. Entries, links, relationships and images never cross world boundaries.

## Available now

- Multiple independent worlds with editable names/description, search/filterable entries, and custom entity categories (person/place/event/organization/family/source and other user-defined types).
- Rich long-form Markdown editing, status, aliases, optional year and coordinates.
- Stable-ID article links (\`[[uuid|visible name]]\`), automatic backlinks, reviewable name-match suggestions.
- Typed and custom-named dated relationships (kinship, membership, geography, trade, claims, governance) with parent-cycle protection and a small relationship graph.
- Individual kinship summary (parents/children/partners) derived from shared relations.
- Event chronology filtered by time and connected entities; year values are currently **world-relative**, not full uncertain Gregorian/relative conversion.
- Zoomable/pannable **2D map** with coordinates, OpenStreetMap reference tiles, labels and year filter. Online tiles require internet; historical shapes and advanced GeoJSON editing are not yet available.
- Image library upload (PNG/JPEG/WebP with validation and previews), reusable article placements, editable alt text, credits, captions, hero and gallery.
- Per-entry theme selection and accent, optional reorder/visibility of live content sections, responsive reading view.
- World JSON metadata export, safe restrictive entry deletion, local SQLite transactions.

## Reliable complete backups

**Use a full backup before substantial worldbuilding or upgrading the application.** This includes a consistent database snapshot plus originals and previews from the media library.

Create a complete archive (the studio can be running):

- \`python app/backup.py create my-world-bible-backup.zip\`

Restore the archive (**stop the studio server first**, then use a clean data folder):

- \`python app/backup.py restore my-world-bible-backup.zip\`

If the target \`.worldbible/\` already contains data, restore will refuse to overwrite it. Use \`--force\` only after confirming the server is stopped; the old data directory is moved to a timestamped \`.previous-...\` folder rather than silently deleted. The archive is checked for directory traversal, per-file SHA-256 integrity and SQLite integrity.

The UI **Export** button produces a separate JSON-only interchange format. It does **not** include image binaries, and imports of such image-referencing exports are deliberately rejected to avoid creating broken media links. UI **Import** creates a new isolated world from a data-only archive and remaps entity IDs and links.

**GitHub is not updated automatically when you edit through Studio.** The SQLite database is the live authority. Back up and export deliberately; Git publishing and round-trip Markdown synchronization are a later integration milestone.

## Limitations and architecture honesty

This is a functional **foundation/MVP**, not yet the complete platform in the RFCs. Advanced page layouts, drag/drop composition, custom theme creation UI, polygon GIS editing, map date precision, source-assertion workflows, graph visualization, GEDCOM import, full database + media restore, robust multi-user conflict resolution, and automatic provenance auditing remain future work. The current prototype preserves Markdown and original media; it does not represent itself as a finished Ancestry/World Anvil equivalent.

**Never run this local server bound to 0.0.0.0 or exposed via a public tunnel without a separate security review.** The write header is a CSRF safeguard, not user authentication.

## Development

- \`python -m unittest discover -s app/tests -v\`
- The repository GitHub Actions workflow runs these tests.
- Data: \`.worldbible/worlds.sqlite3\`, \`.worldbible/media/\` (gitignored).
- All application entities have stable opaque IDs; worlds isolate their data.
- Article hyperlinks are validated; a missing link target causes save to be rejected instead of silently corrupting backlinks.
- Deleting referenced entries is blocked until relations and backlinks are deliberately resolved.

See [Unified Architecture](../bible/15-unified-architecture.md) and [Design System](../design/README.md).
