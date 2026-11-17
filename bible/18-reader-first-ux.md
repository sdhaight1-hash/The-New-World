# RFC 008 — Reader-first World Encyclopedia and Authoring Studio

**Status (November 2026):** independent reader website, publication-gated local API, and a reader-only static site exporter are implemented. The Studio retains full authoring workflows. The static exporter builds deployable files but does not itself publish them to a hosting provider. No public internet hosting or Studio authentication is claimed.

## Why this change is essential

A worldbuilding platform has **two distinct jobs**:

1. Let creators construct and revise complex interlocking histories, cultures, geography, relationships, imagery and sources efficiently and safely.
2. Let visitors understand, discover and enjoy those worlds **without learning how the creators' tools are organized**.

These are not two modes on the same crowded control panel. They are different products over a common content model.

**Architecture:** Canonical world records → editorial publishing gate → reader-specific projection → editorial encyclopedia site. Studio tools may use all records; reader endpoints must only project explicitly published records and relationships among published endpoints. Published status and canonical-confidence status are independent dimensions; a well-sourced established fact can be an unpublished draft, and an explicitly labeled disputed proposition can be made public.

## Research and direct design implications

### 1. Progressive disclosure, not a diminished feature set

Nielsen Norman Group's research on [progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/) explains why novice and expert paths can coexist without hiding expert capabilities permanently. In our product this means the reader **never** needs to see the six-item authoring rail, category codes, edit panels, status mutations, database settings or technical identifiers. The Studio is an explicit alternate workspace for authors, not a primary navigation path for visitors.

Do not place a disabled "Edit" control on every page. An author can enter \`/app/\` directly; a visitor receives a full coherent experience at \`/read/\`.

### 2. Meaningful information scent

[NN/g's information scent guidance](https://www.nngroup.com/articles/information-scent/) emphasizes that meaningful link names, contextual descriptions and early confirmation are essential to navigation. Our entry cards therefore require a **title, content type and useful description**, with an image when present. A pretty abstract thumbnail without text is not navigation. Public article link labels should derive from published names, not system IDs.

Operational rule: recommended/featured content must be chosen by transparent rules initially; do not silently invent editorial importance. Give authors deliberate curation controls in a later pass. In the meantime, stable category sort and bounded highlights are preferable to random front-page content.

### 3. Curated exploration plus lookup

The [Digital Public Library of America](https://dp.la/) offers *Browse by Topic*, primary-source sets and exhibitions in addition to search, supporting visitors without a specific search term. Our landing page provides subject portals, featured articles, atlas and history invitations. Search and catalogue browsing remain available at every point. Future authored journeys/exhibitions should be first-class records linked to entries, with explicit ordering, summary, media and editorial review.

### 4. Strong article reading architecture

NN/g's [How Users Read on the Web](https://www.nngroup.com/articles/how-users-read-on-the-web/) and [Concise, Scannable, and Objective](https://www.nngroup.com/articles/concise-scannable-and-objective-how-to-write-for-the-web/) support clear headings, summaries, linked concepts and short sections. **Do not delete long historical writing to mimic a marketing website.** Preserve the original scholarly depth; add a concise summary, scannable headings, on-page navigation, factual panels and related reading around it.

### 5. Orientation and predictable navigation

The [GOV.UK breadcrumbs pattern](https://design-system.service.gov.uk/components/breadcrumbs/) establishes hierarchical context without conflating it with an action wizard. We use World → Encyclopedia → Subject → Article breadcrumbs. [WCAG 2.2](https://www.w3.org/TR/WCAG22/) and [WAI predictable navigation](https://www.w3.org/WAI/WCAG22/Understanding/predictable) support consistent navigation, explicit keyboard focus, readable contrast, and layout order. In-page TOC links must not collide with client-side URL routing. Article links must survive renaming through stable IDs. Focus and reading preferences must persist without changing content.

### 6. Presentation as a first-class requirement

[World Anvil](https://www.worldanvil.com/faq) demonstrates the importance of both tools and world presentation: maps, articles, family trees and timelines work together, and public presentation is a separate concern. Their [public/private versus published/draft distinction](https://www.worldanvil.com/learn/beginner-tutorials/get-started-articles) is a useful model: visibility and editorial readiness cannot be inferred from a single "established" status.

Do not equate page theming with completeness. Meaningful presentation requires images with attribution, typographic hierarchy, suitable whitespace, compelling covers, captions, related subjects, clear navigational landmarks, and high-quality actual prose.

## Product information architecture

**Reader-facing site:** Discover → Encyclopedia (category + search) → Article (full prose + images + TOC + related items) → Atlas / History → Article. A reader can enter at any deep link, navigate to context and continue. No creator workflow must be learned.

**Studio:** Overview → Encyclopedia/Write/Design/Explore, Atlas, Chronology, Connections, Media Library. All authoring remains accessible, with typed records and data integrity checks. The reader never has to use these features.

**Shared infrastructure:** one database; a separate publication table independent of canon status; published-only projections; a generic site identity per world; media reused by ID; presentation data stored per entity; all worlds remain logically separate.

## Editorial lifecycle

Draft → editorial review → explicitly publish → publicly readable → explicitly unpublish, or continue editing live.

- Draft does not mean "false", and published does not mean "certain".
- Publishing an article exposes its current body, summary, images, aliases and other display metadata. Editing a published article changes the reader immediately.
- Publishing an entry does **not** automatically publish related entries. Connections shown to readers are limited to other published endpoints.
- Unpublished linked records must not appear in reader search, catalogue, graph, chronology or backlinks. If a published body explicitly names a draft, **the author must review that prose before publishing**; names mentioned in plain text cannot be generically redacted without changing the article's meaning.
- Publishing a world over a network is **not** the same as running the current local server on a public port. The Studio API is unauthenticated and the shared server is not an internet security boundary. Public deployment should use a static export of published content or a separately authenticated service; never expose \`/app/\`, \`/api/entities\` or raw draft media as publicly hosted endpoints.
- Image credits, permissions and editorial rights must be reviewed before publication; rich rights management remains a future feature.

## Reader presentation design principles

- **Editorial not dashboard:** immersive but grounded site identity, meaningful hero, categorization, visual entry covers, chapter-like prose, atlas and chronology invitations.
- **Entry themes are local:** the article can use an Atlas/Civic/Chronicle/Kinship/Archive accent while navigation and typography remain legible and consistent.
- **One concept, one page:** dynamic related sections reference canonical IDs, not copy-pasted facts.
- **No empty shell:** if a world has no published articles, show a graceful publication-pending experience rather than exposing the Studio.
- **Media is optional:** a readable typographic cover replaces missing images; never introduce unsourced stock imagery as a historical depiction.
- **Deep links and back navigation:** opening \`#/article/<stable ID>\` works independently, and article-internal TOC navigation must not trigger a route change.
- **Readers choose comfort:** light/dark, adjustable article type size, mobile first, high-contrast audit.
- **Source credibility:** article facts and editorial status must be distinguished from decoration; a historical map layer must explain uncertainty and chronology, not silently depict modern geometry as authoritative old boundaries.

## Usability acceptance

Test with two tasks **without a tutorial**:
- Visitor: arrive at the reader home → find a settlement → read its background → navigate to a person or event → find its geographic context → return; **zero creator terms exposed**.
- Creator: draft a place → add a linked faction → attach image → preview how readers will see it → publish just the place → check that faction draft is hidden → publish faction → observe the new link; **no duplicated records**.

Also test keyboard search, responsive navigation, deep URL entry, browser back, dark/light preferences, missing media, empty publication set, 1,000+ article catalogue, no accidental draft leaks in reader endpoints, and visual screenshot comparisons.

## Next advanced milestones

- Authored editorial journeys/exhibitions, curated covers, and featured article ordering.
- Dedicated public thematic maps and historic polygon/route layers, without leaking modern boundary assumptions.
- Full historical source apparatus, citations and versioned assertions, with readable public editorial notes.
- Static publication export and verification **implemented**; automated hosting, search-engine-friendly article URLs and deployment workflows remain to be built.
- Reader site design controls beyond current article accents and ordered sections.
- Usability tests with real first-time readers, not only scripted interaction; quantitative success criteria should use observed task completion and navigation mistakes.

## Relevant references

- NN/g: [Progressive disclosure](https://www.nngroup.com/articles/progressive-disclosure/), [Information scent](https://www.nngroup.com/articles/information-scent/), [Information architecture](https://www.nngroup.com/articles/ia-study-guide/), [Reading on the web](https://www.nngroup.com/articles/how-users-read-on-the-web/)
- [DPLA homepage and exhibitions](https://dp.la/)
- [GOV.UK breadcrumbs](https://design-system.service.gov.uk/components/breadcrumbs/)
- [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [World Anvil features](https://www.worldanvil.com/faq) and [draft/published distinction](https://www.worldanvil.com/learn/beginner-tutorials/get-started-articles)
