# Entry Presentation Design System

**Status:** a reusable, validated foundation. The visual editor, page renderer and shared data core have **not yet been implemented**.

## Files

- [Theme presets](themes.json): named semantic page-canvas themes with dark and light variants.
- [Example layout](layout-example.json): one ordered layout block tree describing a reference article; **no facts or people invented**.
- [Validator](validate.py): checks theme ID uniqueness, hex colors, WCAG-style text contrast, block types, IDs, nesting and allowed configuration properties.
- [Full specification](../bible/16-ux-and-entry-designer.md): modes, drag/drop and keyboard editing, images, responsive layout, templates, entry overrides, rich links and accessibility.
- [Unified architecture](../bible/15-unified-architecture.md).

## Design contract

The configuration is **presentation-only**. It must not be used as an independent store for biographies, populations, governments, event dates or any historical claim. Dynamic blocks resolve an entity's live linked records by stable ID.

The application shell stays consistent. Only the entry canvas and approved blocks inherit entry-specific themes. The reader's accessibility preferences override unsafe author choices.

Run the validator from the repository root with `python design/validate.py`. CI checks designs when files change. The validator catches structural errors; **it is not a sanitizer** and it does not replace real runtime validation, safe Markdown rendering, content-security policy or accessibility UI tests.

## Starter theme families

**Archive**: neutral research records; **Atlas**: landscapes/settlements; **Chronicle**: historical narratives; **Kinship**: biographies/families; **Civic**: organizations/law. Any entry may use any theme, with custom theme creation planned in the eventual Design mode.

## Editing workflow (future application)

Read → Write → Design → Preview → Publish. A drag/drop **and** keyboard-reorderable page editor lets authors organize text, images, maps, galleries, family trees, relationships, illustrations, callouts and timelines; select backgrounds/spacing/fonts/colors; preview light/dark/mobile/print; save reusable templates and page-specific overrides.

**Priority:** implement the shared entity/data service first, then a real renderer/editor that reads these versioned files. Do not create another isolated localStorage writer with a competing knowledge database.
