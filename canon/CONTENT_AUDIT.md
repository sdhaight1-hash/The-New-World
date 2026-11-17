# Canon-content audit — encyclopedia versus project documentation

**Scope:** `The New World` local Studio's default seed and earlier imports.
**Decision:** Import only world-setting material into the Encyclopedia. Keep software architecture, interface designs, editorial research planning and development roadmaps in GitHub, *not as lore records*.

## Confirmed ingestion defect

The previous importer loaded every `.md` file inside `bible/` as a world entity. This created incorrect encyclopedia entries for product-development RFCs, the research register, the canon ledger and genealogy-tool planning. A title or location within a software document does not turn the document itself into an in-world fact.

The new source whitelist contains exactly **eight world-content Markdown documents**: `bible/01-chronology.md` through `bible/05-successor-societies.md`, plus the three `regions/*.md` histories.

The following **15** former sources are no longer imported as encyclopedia records:

| Editorial / development source | Why excluded |
|---|---|
| `bible/00-foundations.md` | Editorial canon rules and decisions, not a historical article |
| `bible/06-research-register.md` | Pending research tasks and questions |
| `bible/07-genealogy-dynasties.md` | Genealogy software/data-model plan, not actual families |
| `bible/08-world-bible-architecture.md` | Information architecture |
| `bible/09-linking-and-discovery.md` | Link-discovery system design |
| `bible/10-rfc-historical-knowledge-core.md` | Database architecture |
| `bible/11-rfc-location-faction-systems.md` | Software location/faction functionality |
| `bible/12-rfc-timeline-engine.md` | Timeline editor architecture |
| `bible/13-rfc-media-image-handling.md` | Software media-management specification |
| `bible/14-rfc-gods-eye-atlas.md` | Superseded rendering design |
| `bible/15-unified-architecture.md` | Studio architecture |
| `bible/16-ux-and-entry-designer.md` | Studio UX and page-builder specification |
| `bible/17-rfc-2d-historical-atlas.md` | Atlas editor engineering |
| `bible/18-reader-first-ux.md` | Reader UX engineering |
| `bible/19-visual-worldbuilding-and-moodboards.md` | Moodboard design/research |

These files remain in the repository to support development. Their presence in Git does **not** authorize their presence in the story-world's Encyclopedia.

## Confirmed new baseline

A fresh seed now creates:

- **8** world-content source records, with the original history preserved.
- **60** individual structured world entries (including named real-world places, historical developments, and relevant themes); two named catastrophes reuse existing source records rather than duplicating them.
- **58** links between these structured entries, with working hypotheses marked as such.
- **68 total encyclopedia entries** rather than the previous 83.

This change does **not** automatically publish any articles.

## Existing local databases

The launcher detects previously seeded non-world documents by deterministic source IDs. It deletes only those still **exactly identical** to their original auto-imported form and without incoming links, typed relationships, media placements, moodboard placements or publication state.

Before the first such cleanup, it writes a complete database-and-media ZIP in `.worldbible/backups/`. Cleanup is transactional. Edited, linked or published non-world documents are **preserved for manual review**, not silently destroyed; the launcher prints their paths.

The one previously generated cross-link from the approximately-Year-50 overview to the editorial canon ledger is rewritten to the actual chronology **only when its body is an unchanged, unpublished seed template**. Human-edited or published text is left alone.

## Further editorial quality review

Cleaning software documentation is not the same as declaring every remaining entry finished historical canon. Several records still represent **research hypotheses or structural placeholders** and warrant later editorial reclassification:

- **Proposed 2030 World Cup amplification** and **Proposed Cajon quarantine** are possible historical explanations, not proven events.
- **Atlas reference present (~Year 50)** marks the author's viewpoint, not a literal single-day historical occurrence; it should ultimately be presented as a chronological reference period rather than an ordinary event.
- **Diamond Ranch (identity unresolved)**, **Wyoming reservation (identity unresolved)** and **Wyoming ranchlands and reservation study** are research locators, not confidently identified mapped sites or political entities.
- The **emergency, adaptation, consolidation and generational eras** are broad working period classifications, not singular historical events.
- Some entries have **established general direction** but no verified later demographic, territorial or political facts. They must not be fleshed out with invented exact figures.

These in-setting but provisional records remain draft/unpublished. They are not product design documentation and may be useful to develop world lore, but should receive explicit review before being published as a visitor-facing encyclopedia.

## Prevention checks

- A strict source whitelist is used instead of a broad `bible/*.md` scan.
- The structured canon manifest rejects any `source` path outside that whitelist.
- Regression tests check that architecture RFCs and the editorial ledger do not enter a fresh world.
- Migration tests verify pristine-document deletion, automatic full backup, preservation of human edits/publications, and repair of a legacy automatically generated source link.
- The Studio reader uses explicit publication status; initial seeding does not publish drafts.

**Principle:** The **world** contains in-universe history, geography, peoples, cultures, institutions, events and material life. The **project** contains development plans, research to-do items, software architecture and editorial decisions. The two may inform each other, but do not share encyclopedia entries.
