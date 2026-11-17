# RFC 004 — Media Library, Image Handling and Visual Annotation

**Status:** research-backed specification; NOT an implemented image manager.
**Depends on:** [Historical Knowledge Core](10-rfc-historical-knowledge-core.md), [Location/Faction Systems](11-rfc-location-faction-systems.md), [Timeline Engine](12-rfc-timeline-engine.md).
**Core principle:** assets are first-class records reused across all encyclopedia views, not copied into separate map, genealogy, article or faction image stores.

## Research basis

- World Anvil's Image Manager supports embedded images, folders and galleries, though its guide notes map/Chronicle image management is independent: https://www.worldanvil.com/learn/images/images
- IIIF Image API 3.0 defines region/size/rotation requests and IIIF Presentation API 3.0 includes manifests, ordered image canvases and annotations: https://iiif.io/api/
- W3C Web Annotation Data Model offers resource-targeted annotations: https://www.w3.org/TR/annotation-model/
- libvips supports efficient thumbnailing and shrink-on-load: https://www.libvips.org/ and https://github.com/libvips/libvips/blob/master/doc/developer-checklist.md
- OWASP file-upload guidance recommends allowlists, signature/decode validation, size limits, safe filenames and restricted processing: https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
- Git LFS can store large binary images without bloating standard Git history: https://git-lfs.com/

## Architecture decision

Distinguish **asset identity**, **immutable original binary**, **processed derivative**, **placement/use**, and **annotation**.

- An **asset** is the stable record for a work (portrait, map, diagram, photo, heraldry, scan, drawing).
- A **binary blob** is byte content, addressed by cryptographic digest (SHA-256). Multiple assets can reference the same original if deliberately deduplicated, but must not merge distinct editorial identities merely because their bytes are the same.
- A **version** records a replacement or revision of the same asset while preserving the asset's stable ID and all references. Materially different historical depictions should be separate assets linked by `derived_from`/`depicts_same_subject`, not silently replace one another.
- A **derivative** (thumbnail, preview, resized WebP/AVIF/JPEG) is recomputable cache content and not a second canonical original.
- A **placement** links an asset to an entity/article/gallery/map with role, caption, crop, layout, sort order and optional relevant time.
- An **annotation** targets a region of an asset and links it to an entity, event, note or claim; it may carry source, time and editorial confidence.

**One unified media index** under the knowledge core. Genealogy trees, settlement maps, faction banners and articles reference the same asset IDs.

## Image record and metadata

Proposed `media_asset`:
- Stable `asset_id`, title, aliases, description, accessible alt text;
- classification (`portrait`, `landscape`, `map`, `document_scan`, `artifact`, `heraldry`, `diagram`, `photograph`, `illustration`, `other`), tags and gallery membership;
- creation/origin date and **depicted historical time** as separate fields (support uncertain/circa dates and relative Cascade years);
- author/photographer/creator, source URL/citation, license, ownership/usage status, import notes;
- provenance/authenticity category: `real-world photograph`, `reference`, `fictional reconstruction`, `AI-generated`, `modified/manipulated`, `in-universe artifact`; categories are provenance descriptors, not moral judgments;
- original filename as display metadata only; safe stored blob path/digest, dimensions, orientation, MIME type, file length, checksum;
- canonical editorial state (`established`, `working`, `disputed`, `superseded`), license/permission review status, optional sensitivity/privacy flags;
- links to depicted entities (people, places, objects, organizations, events) and explicitly contextual but **not depicted** entities.

Historical distinctions: a photograph captured in 2030 and reproduced in a Year 50 chronicle has distinct `captured_at`, `depicts_at`, `published_at`, `found_at` dates. A 2080 illustration depicting 2030 Los Angeles must not be labelled an authentic 2030 photo.

## Storage and delivery

- **First stage:** local project-managed `media/originals/` for validated source files and `media/derivatives/` as disposable cache; SQLite for metadata, asset relationships and indexes. Store relative repository-friendly asset links and portable export manifests.
- **Repository:** textual metadata, README and export manifests in Git; large originals through Git LFS **if enabled/configured**, or content-addressed external storage with verified backup. Never silently commit huge binaries to regular Git. Choose based on actual size and workflow.
- **Later hosting:** local/offline first; optional object storage, sync and multi-device serving behind an abstraction only when needed.
- Never derive a download path from user-supplied filenames; use generated IDs/hashes and controlled directories.
- Generate responsive sizes, thumbnails and previews with EXIF orientation correction, constrained memory/time/pixel budgets and color-profile handling. Keep originals intact; avoid claiming a thumbnail can reconstruct an original.
- Preserve user-uploaded image originals with their ownership metadata; default public export **strips location/device metadata** from derivatives unless user explicitly opts in. Original restricted metadata remains stored privately when appropriate.
- Explicit backups, digest verification and orphan/unused-asset auditing.

## Editing and presentation

**Media Manager**: browse, grid/list, full-text filter, type/date/place/tags/status/license filters; bulk tag, organize, replace/version, inspect metadata, remove references, detect duplicates and see usage/backlinks.

**Article editor**: drag-drop/paste/select from library, inline/full-width/float/alignment, crop focal point, caption, alt text, replacement without link breakage, keyboard navigation, full-screen lightbox/zoom. Never require uploading duplicates just to reuse an image.

**Galleries**: reusable editorial collections with ordering and descriptions; one asset belongs to multiple collections. Albums attached to person, family, settlement, faction, event, period or research theme.

**Hotspots**: optional rectangle/polygon/point annotations using image-relative coordinates (0..1) and shape metadata; annotations survive resizing. Each hotspot can target an entity ID or an evidence-bearing note. Click/keyboard focus to open entity and show why it is associated. If an original is replaced with different dimensions/composition, mark affected annotations **review required**, not automatically trusted.

**Historical maps**: map assets separate from georeferenced GIS layers; a map scan may be annotated without any claim to geographic precision. For true map overlays, add control points/georeferencing and transparent layers *later*. Never treat a hand-drawn political map's pixels as a surveyed boundary.

**Genealogy**: optional portraits in person nodes; marriage/group photos shared across family entries; image identities do not determine person identities. Photo recognition is optional future candidate discovery, never automatic genealogy canon.

**Factions**: heraldry, banners, seals, uniform references, historic emblem variants linked to organization and time range, avoiding overwriting old symbols.

## Discovery and automatic association

Textual search indexes titles, tags, captions, aliases, descriptions, provenance and connected entity names. Show “used in articles” and “depicts these entities” separately.

Future optional OCR and visual analysis can propose candidate entities, dates, subject tags and duplicates, **with human confirmation**, provenance and crop-based supporting context. Do not infer a person's identity from their appearance alone. AI-generated imagery must remain clearly provenance-tagged and should not be silently presented as documentary historical evidence.

## Safety and reliability requirements

1. Allowlist common raster image formats (JPEG, PNG, WebP, optionally AVIF/HEIF via safe decoders). SVG, PDF, TIFF and exotic formats require separate safe conversion paths—not arbitrary browser-executed HTML/SVG.
2. Inspect actual bytes and decode successfully; file extension and client MIME are not enough. Limit bytes, decoded megapixels, frames and decompression ratios. Sandbox processors where practical.
3. Store originals outside public executable content locations; serve generated previews with safe content types and permissions. Prevent path traversal and code execution.
4. Preserve copyrights/license/credit; do not imply scraped Internet images are free to republish.
5. Escape captions/metadata, sanitize any rendered Markdown, enforce permission checks for restricted assets.
6. Deleting an asset must show all usage locations and annotations; never silently erase article images or orphan references.
7. Thumbnail generation failure must not corrupt the original or media index.
8. For collaboration, make provenance and review status visible; for private/offline use avoid unnecessary cloud uploads.

## Minimal schema extensions

`media_asset(asset_id, title, description, alt_text, kind, source_id, creator, license, provenance_kind, status, created_at, updated_at)`

`media_version(version_id, asset_id, sha256, storage_uri, mime_type, bytes, width, height, orientation, version_order, created_at)`

`media_placement(placement_id, asset_id, host_entity_id, role, caption, alt_override, crop_json, sort_order, valid_from, valid_to)`

`media_annotation(annotation_id, asset_id, version_id, selector_json, target_entity_id, note, source_id, status, valid_from, valid_to)`

`media_gallery(gallery_id, title, description)` + gallery-to-media ordered links.

Where possible media can also be an entity in the universal index; avoid duplicate media identities across a generic entity table and the media-specific table. Persist asset IDs and relationship IDs with foreign keys and transactionally maintained backlinks.

## Staged delivery and acceptance tests

### Phase 1: real ingestion + reuse
- Upload safe PNG/JPEG/WebP; detect type, record dimensions and SHA-256; preserve original; produce thumbnail/preview.
- Create one media record and embed the same asset in a person, place and event without new originals.
- Rename media asset or article; all placements remain intact.
- Export/import full media manifest, verify checksums, paths, captions and entity IDs.
- A malformed or decompression-bomb file fails gracefully with no ghost record.
- Media deletion refuses or previews referenced uses.

### Phase 2: galleries, captions and backlinks
- Reorder albums, bulk tag, filter, replace versions, show backlinks and rights/source metadata.
- Display article media responsively, with consistent zoom and keyboard support.
- Replace an asset while preserving placement references, mark hotspots/crops for review.

### Phase 3: annotations and temporal images
- Draw rectangle/point/polygon hotspot, link to place/person/event and navigate to entry.
- Show an organization’s crest for Year 20 and a later version for Year 50.
- Keep map illustration distinct from geospatial truth; accurate overlays require explicit georeferencing.

### Phase 4: deeper discovery
- Optional OCR, visual similarity candidates, IIIF-like region access where actual need warrants.
- Disk usage management, archive backups and performance validation for 10k+ images.

## Critical implementation order

Do not build a disconnected gallery prototype with its own storage system. Implement image ingestion only once the shared knowledge core can store media IDs, metadata, references and deletions correctly. The first vertical slice must be **one image → multiple linked entries → backlinks → lossless archive/export**.

Related: [unified world bible](08-world-bible-architecture.md), [link discovery](09-linking-and-discovery.md), [timeline RFC](12-rfc-timeline-engine.md), [genealogy](../genealogy/README.md).
