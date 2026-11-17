# World Bible Studio — reusable local-first application

The studio is **a generic multi-world editor**. “The New World” is included as an optional initial world, not encoded in the entity model, chronology, or themes.

## Start

Requires Python 3.11 or newer. Pillow is needed for safe image uploads; all other server capabilities use the standard library.

From the repository root:

1. Install image dependency: \`python -m pip install -r app/requirements.txt\`
2. Import existing Bible pages once: \`python app/seed.py\`
3. Run the local application: \`python app/server.py\`
4. Open **http://127.0.0.1:8765/app/** in your browser.

The server listens on **127.0.0.1 only**. It is not authenticated or designed for public Internet hosting. Back up the **.worldbible** folder, including its media directory and SQLite database; the export button currently produces structured JSON **without image binaries**.

If you want a separate world, choose **+ World** in the header. Entries, links, relationships and images never cross world boundaries.

## Available now

- Multiple independent worlds and search/filterable entries (person, place, event, organization, family, object, source, subject).
- Rich long-form Markdown editing, status, aliases, optional year and coordinates.
- Stable-ID article links (\`[[uuid|visible name]]\`), automatic backlinks, reviewable name-match suggestions.
- Typed relationships (kinship, membership, geography, trade, claims, governance and other categories) with parent-cycle protection.
- Individual kinship summary (parents/children/partners) derived from shared relations.
- Event chronology filtered by time and connected entities; year values are currently **world-relative**, not full uncertain Gregorian/relative conversion.
- Zoomable/pannable **2D map** with coordinates, OpenStreetMap reference tiles, labels and year filter. Online tiles require internet; historical shapes and advanced GeoJSON editing are not yet available.
- Image library upload (PNG/JPEG/WebP with validation and previews), reusable article placements, hero and gallery.
- Per-entry theme selection and accent, optional reorder/visibility of live content sections, responsive reading view.
- World JSON metadata export, safe restrictive entry deletion, local SQLite transactions.

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
