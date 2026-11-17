# RFC 006 — UI/UX, Theme System and Visual Entry Designer

**Status:** partial implementation: responsive studio shell, light/dark theme presets, accent choice, ordered/visible live article blocks and media placement are implemented. Full drag/drop graphical layout designer, reusable custom theme editing and visual regression testing remain planned.
**Primary architecture:** [Unified platform ADR](15-unified-architecture.md).

## Design goals

Readable, serious historical encyclopedia with room for evocative presentation: **editorial atlas meets archival research desk**. Distinctive identities should come from each location, period, family, organization or user-selected aesthetic, not a generic fantasy game skin. The shell remains predictable and sober even on richly customized pages.

### Default aesthetic: “Archive / Cartographic”

- **Default dark UI**: deep ink/slate shell; parchment/sand accents and subdued teal for actionable links. No gratuitous glowing gold borders or heavy textures.
- **Light UI**: warm white/ivory pages, charcoal ink, calm blue-teal controls.
- **High contrast**: near-black/white semantic tokens; explicit outlines and keyboard focus.
- **Typography**: contemporary system sans for controls; optional highly readable serif for article headings/body. Reader selects body font, width, scale and spacing.
- **Motion**: minimal, respectful of `prefers-reduced-motion`.
- **Imagery**: evocative *optional* hero/banner, maps and galleries; no photo required to create an entry.

### Initial color tokens (proposals, not immutable canon)

| Semantic token | Dark default | Light default |
|---|---|---|
| `app.background` | `#111820` | `#F4F3EF` |
| `app.surface` | `#1B2731` | `#FFFFFF` |
| `app.raised` | `#263541` | `#E8ECEA` |
| `app.text` | `#EDF2F1` | `#19282C` |
| `app.muted` | `#B6C5C9` | `#465B62` |
| `app.border` | `#455660` | `#B7C6C8` |
| `app.accent` | `#77B7AE` | `#126D70` |
| `app.focus` | `#FFD48A` | `#005A9A` |

Custom palettes must pass accessibility checks; never rely on accent color alone for distinguishing active/working/disputed/superseded status. Status uses readable labels and icons.

### Entry appearance presets (opt-in)

- **Atlas**: topo-inspired green/teal; locations, geography, ecology and infrastructure.
- **Chronicle**: warm bronze and ink; historical narrative/events/timelines.
- **Archive**: neutral cool gray/blue; sources/research and uncertain evidence.
- **Kinship**: muted aubergine/copper; family trees, households, biographies.
- **Civic**: muted blue/terracotta; factions, institutions, legal records.
- **Custom**: author sets a limited palette, headers and accents.

These are helpful *defaults*, not fixed categories. A faction can use Atlas, a town can use Kinship, and each entry may choose its own theme. Never infer a faction's real historical flag/colors automatically from a page theme.

## Theme scopes and resolution

- App shell uses global reader dark/light/high-contrast theme.
- World-level brand/preset controls default article canvas.
- Entry-type preset is available but never forced.
- Per-entry `theme_id` can select any approved preset/custom authored theme.
- Optional block-level overrides: `tone`, `alignment`, `spacing`, `accent`, `background`, `image fitting`.
- Reader accessibility preferences take precedence over authored color requests where contrast or legibility would be impaired.

Store **semantic design tokens**, not arbitrary CSS strings. Whitelist colors, sizes, spacing scales, font families, radii and opacity; reject CSS expressions and uploaded font executables. User may create/save/edit/duplicate custom theme presets, use live preview, reset overrides and apply a theme to selected entries. Themes are exportable structured JSON with version and IDs.

Two independent choices: `appearance_mode = dark | light | system | high-contrast`, and `entry_theme_id`. Same thematic identity must work in dark and light modes.

### Accessibility policy

Target WCAG 2.2 AA: ordinary text at least 4.5:1, large text at least 3:1; nontext controls/graphical UI at least 3:1 where applicable. Provide automated token contrast checks at save time. If author selects an unsafe pair, propose nearest accessible contrast adjustment and show before/after, or refuse until fixed. Focus styles and minimum pointer targets remain consistent. Prefer text labels + patterns in faction overlays, not color alone.

## Entry Designer: a true no-code layout composer

The editor offers **Read | Write | Design | Explore** modes. Design mode changes presentation *without rewriting canonical facts*.

**Layout block palette (initial):**
- Header/hero (title, subtitle, banner image, emblem/portrait)
- Rich article prose section (unlimited text, headings, citations, accepted entity links)
- Two-column or full-width section; section tabs only where readable with print/keyboard fallback
- Image, gallery, annotated image and caption
- Related entry list, fact panel, relationships/backlinks
- Timeline excerpt, interactive/printable family tree
- 2D map/map viewport; faction territory layer or place point list
- Quote, source note, document facsimile, divider, collapsible notes, comparison panel
- Optional metadata tables (only for actual structured facts).

**Template hierarchy:** base article template → type starter template → saved reusable custom template → entry-specific layout instance. No hard-coded “faction must have heraldry” or “settlement must have census.” All dynamic widgets source canonical IDs.

### Editing workflow

1. Open article in Write mode and add unlimited prose with rich links.
2. Switch to Design and select a base template or start blank.
3. Drag or keyboard-reorder sections; choose columns/grid spans and visibility.
4. Attach a hero/photo/map by **media asset ID**; adjust caption, crop focal point, size, alt text.
5. Insert dynamic widget (e.g., timeline for this settlement) that **queries shared event records**.
6. Change entry theme with live light/dark preview; tune semantic colors, typography and margins.
7. Preview desktop/mobile/print and check accessibility/overflow before publishing.
8. Save layout as reusable template if desired; revert or compare prior versions.

One view can have multiple saved presentation variants (e.g. “reading”, “academic”, “atlas sheet”) only when useful. Avoid per-reader duplicative facts. **Never save a snapshot of dynamic family/organization facts into page layout data.**

## Persistent layout schema (concept)

`entry_presentation(id, entity_id, template_id, theme_id, layout_json, revision, updated_at)`.

`layout_json` is a versioned **ordered tree of whitelisted blocks**, every node with `block_id`, `type`, approved props and children when allowed. Example in `design/layout-example.json`.

Referenced entity IDs and media IDs are validated on write and preview. Unknown block types, dangling IDs, illegal nesting and recursive template references are errors. A missing optional media rendition shows a safe placeholder; canonical entity is never deleted to repair a layout problem.

### Layout constraints

- Responsive CSS grid with 1-column mobile fallback; meaningful heading/reading order independent of visual columns.
- Limit nested grid depth and avoid unbounded custom positioning. Allow width spanning, crop/align, decorative background, spacing and section ordering; **not unrestricted absolute-position page canvas** as core, since it breaks accessibility/print.
- Rich visual controls, but safe defaults. Provide optional advanced per-template JSON editing only if schema-validated; **do not execute author HTML, CSS or JS**.
- Print/PDF and Markdown export preserve core article and images/captions/metadata in readable sequence. Visual flourishes may degrade gracefully, but no facts disappear.
- Templates can reference the same record in different places without duplicating underlying data.

## Main navigation and layout

Desktop: ~240px collapsible left navigation; fluid center editor/article column (comfortable reading measure, optional wide mode); ~300px collapsible right inspector; optional bottom 2D atlas/time rail. User controls panel widths and remembers workspace preferences.

Mobile/tablet: single article column and drawers for search/inspector/design; commands remain accessible without hover. Avoid hiding essential facts behind canvas interactions.

Global search with entity type/year/status filters, command palette, breadcrumbs, backlinks, recent entries, unresolved-link tray and undo/redo. No redundant duplicate nav trees across feature modules.

## UI states and quality

- Empty entry: explanatory placeholder and optional suggested blocks, no invented records.
- Unsaved changes: clear persistent indicator; transactional autosave + explicit revision history.
- Missing image/linked record: safe meaningful placeholder with repair action.
- Disputed evidence: visible label and provenance in article and derived visuals.
- Loading: preserve navigation and selected year; do not blank full editor when one image/map widget fails.
- Design mode selection outlines must be keyboard reachable and not corrupt article text.
- Editor should support long articles (tens of thousands of words) without truncation; performance tests for thousands of links.

## Implementation choices to test

Tiptap/ProseMirror schema-based nodes and custom node views offer an editable document with controlled rendering. Decide whether `layout_json` composes prose nodes or surrounds canonical Markdown sections only after a **lossless round-trip proof**. Do not build two competing editable bodies.

MapLibre style expressions and layer filters can render temporal/political styling without changing geographic data; entry theme **must not silently recolor historical source maps or misrepresent political boundaries**.

## Acceptance gates

- Create two entries with same canonical links but different themes and section order; links/backlinks remain identical.
- Change one theme globally, preserve per-entry overrides and high-contrast reader mode.
- Pick an unsafe text/background color pair: tool flags or fixes it; contrast audit passes.
- Move image and family graph blocks via drag *and* keyboard; save/reopen retaining layout.
- Rename a referenced entity; in-page graph, summary and inline links remain valid.
- Remove media: preview affected entries and fix with explicit choice; don't drop captions silently.
- Export/import retains theme IDs, layout order, Markdown prose, media references and alt text.
- Print/mobile reading order is coherent regardless of desktop two-column layout.
- No injected scripts from theme names, captions, imported HTML or layout JSON.

## Sources

- [Tiptap schema](https://tiptap.dev/docs/editor/core-concepts/schema)
- [Tiptap custom node views](https://tiptap.dev/docs/editor/extensions/custom-extensions/node-views)
- [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [MapLibre style expressions](https://maplibre.org/maplibre-style-spec/expressions/)
