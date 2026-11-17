# Relationship Mapping and Link Discovery

**Status:** architectural priority adopted. Based on research into Realm Works, with a worldbuilding/editorial rather than RPG-player-reveal emphasis.

## What Realm Works contributes

Lone Wolf Development's Realm Works provides automatic content linking, rename-aware links, aliases, full-text search, backlinks, topic containment, link/relationship webs, and collision resolution where names refer to different records. We want those *capabilities*, not a replica of its implementation.

References:
- [Official Realm Works features](https://www.wolflair.com/realmworks/)
- [Developer notes on full linking/backlinks/search](https://www.wolflair.com/realmworks/designers-diary/003-making-the-most-of-official-content/)
- [Name collisions and identity-independent links](https://www.kickstarter.com/projects/610004753/realm-works-streamlined-rpg-campaign-tools/faqs)
- [Relationship webs and annotation](https://forums.wolflair.com/threads/requesting-help-with-relationships-families.48693/)
- [Automatic detection and rename handling](https://forums.wolflair.com/threads/realm-works-beta-release-64-bit-and-more.61660/)

## Underlying model

Entries have stable IDs, type, canonical name, aliases, source path, statuses, broad temporal relevance and substantial prose. **Identity is independent of name**: renaming an entity must not sever established links.

Two different kinds of connections:

1. **Content reference** (A mentions B): an accepted link with optional source span/context and status; backlinks derived from those references.
2. **Semantic relationship** (A located-in B, founded-by C, employed-by D, migrated-to E, partnered-with F): named, directed or symmetric, with optional effective dates, evidence, confidence and editorial status.

Content mention **does not** imply a semantic relation. `Big Bear` mentioned near `Los Angeles` does not establish governmental ownership, migration or alliance.

Do not duplicate a relation as a second independent source of truth merely to show a reverse edge; derive reverse labels (“contains” from “located-in”). Give accepted relation edges stable IDs.

## Discovery workflow

1. The editor indexes all established entry names/aliases (and drafts when explicitly enabled).
2. After a writer edits text, analyze text only in ordinary prose spans—**not** code, embedded links, metadata or existing confirmed links.
3. Detect whole names/phrases using case-aware normalization, longest match first. Prefer multiword names; common words and short aliases need manual review.
4. Display suggestions as reviewable proposed links, grouped by target with context and reason.
5. **Collisions:** when a name matches multiple people/places, present their type and geographic/temporal context. Do not auto-select.
6. **Acceptance** records the stable target ID. **Ignore** should be preserved per occurrence, so suggestions do not repeatedly nag.
7. Save original prose with explicit links and maintain backlinks automatically. Renames change labels, not target identities.
8. Propose missing entry candidates only on explicit review; do not invent people or records.

## Views

- Entry: outbound references, inbound backlinks, explicit semantic relationships with inverse directions, history and sources.
- Explorer: local relationship map centered on the current entry, expandable one edge at a time, filtered by relationship type/status/time.
- Discovery: possible links, ambiguous matches, orphaned entries, dangling references, duplicate names, unlinked mentions, and timeline conflicts.
- Global: search by title/alias, body text, type, tags, place, date and relationship.
- Chronological: visualize only edges and states valid at the selected year, keeping unrelated periods from appearing contemporaneous.

## Operational and quality constraints

- No auto-confirmation of suggested entities, links or facts.
- Existing Markdown remains readable and is not rewritten wholesale.
- Relative links and canonical IDs coexist; export preserves IDs.
- Full-length text and freeform prose remain central, not hundreds of little field limits.
- Relationship predicates should be extensible but curated, with clear directionality and examples.
- Imports must reject dangling targets or flag them for repair; deletion reports affected links and relationships.
- Human review is required for repeated/ambiguous names, titles, nicknames and common terms.
- Graph visualization must remain optional: lists and text links are often better on large graphs.
- Large corpus indexing should be incremental/debounced; don't rescan the entire archive on each keystroke.
- Security: sanitize imported prose and never execute arbitrary HTML, JS or Markdown scripts.

## Implementation checkpoints

### A. Minimal real workflow
- Search/index initial world-bible pages and aliases.
- Offer name-match suggestions with disambiguation and inspectable context.
- Accept suggested links into stable-ID references, keep a manually editable semantic relation set.
- Show reverse links and a local graph/list.

### B. Production-grade foundation
- Shared structured entity registry across all world-bible content, including genealogy.
- Rich-text or Markdown editing with source-span-aware suggestions, stable link IDs, rejected matches.
- Bidirectional reference index, typed relationship editing, conflict auditing, renames, deletion safety.

### C. Deep historical discovery
- Dated edges, versions, as-of chronology, approximate dates, confidence/provenance.
- Search across place, family, title, organization and event histories.
- Automatically surfaced **candidates** for unknown individuals, organizations and connections, never silent insertion.

## Distinction from genealogy

Genealogy is **one view over the universal relationship network**. Parentage, households and unions are specialized edges; trade, migration, jurisdiction, employment, participation, land tenure and institutional history belong to the same overall entry/link ecosystem.
