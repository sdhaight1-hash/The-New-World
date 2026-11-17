# World Bible — Information Architecture

**Status:** adopted product direction; implementation staged. This repository is a conworld encyclopedia, not a dynastic succession simulator, a novel outline, or a tabletop campaign manager.

## Design influences

- **World Anvil:** interconnected encyclopedia articles, context-specific templates, categories, maps, historical timelines/chronicles, genealogy and diplomacy views.
- **Kanka:** linked records across people, places, organizations, events and families; tagged relationships and modular features.
- **Gramps / genealogy standards:** people and relationships as records with stable identities, dates and sources.

Copy the **organizing principles**, not proprietary code, branding, or a sprawling set of unnecessary forms.

## Organizing principle: a connected encyclopedia

A **person** has one canonical biography, not separate duplicate copies in genealogies, timelines, household lists and political histories. A **place** has one canonical entry with historical states; an **event** has one canonical entry linked to participating people, settlements, organizations and sources. Family-tree diagrams are one derived **view** over those underlying records, just as maps and timelines are other views.

The top-level structure should provide:
1. **Atlas:** places, geography, settlement hierarchies, routes and maps.
2. **People:** biographies, relationships, households, education, work, journeys and kinship.
3. **Families and communities:** genealogies, household histories, lineages, ordinary and elite families; optional political houses when relevant.
4. **Organizations and institutions:** civic bodies, trade guilds, businesses, churches, local associations, courts, military and government organizations.
5. **History:** events, periods, chronicles and date-based regional timelines.
6. **Economy and material culture:** farms, estates, water systems, industry, technology, trade and infrastructure.
7. **Society and culture:** languages, customs, belief, law, social classes and historical memory.
8. **Sources and research:** records, citations, uncertainties, conflicting testimony and established canon.
These are navigation lenses, **not rigid boxes**. An entry may appear in several indexes without duplicating the underlying record.

## Minimum common record

Each structured entry should have:
- `id` (stable machine ID), `type`, `title`, optional aliases;
- prose description with **no arbitrary short text limit**;
- canon status (`established`, `working`, `disputed`, `superseded`);
- dates/intervals (including uncertain date precision where known);
- relation IDs linking other entries, with relation type and optional dates;
- geographic references / coordinates where applicable;
- citations and provenance;
- optional images and captions;
- created/updated editorial metadata.

**Keep prose editable as prose.** Structured fields must enhance free writing, not replace it or force premature specificity.

## Genealogy as a universal organizational tool

Family trees are used for:
- normal households across generations, including births, deaths, adoption, step-relationships, remarriage;
- identifying related people across settlement histories and migrations;
- tracking occupations, inheritance of craft knowledge, family farms, business continuity;
- tracing social networks and where families moved after the Plague and Cascade;
- showing the historical development of communities;
- **optionally**, tracking political houses and succession.

Political rights, offices, property tenure and inheritance are distinct from ancestry. A person may have multiple households over a lifetime. Conflicting testimony and disputed parentage must be representable.

No family's prominence is assumed. The default workflow should be **create person → connect relation → link place/event → see biography and tree**, not “create ruling dynasty.”

## Connected views

- Person page: biography, family and non-family relationships, locations lived, life events, associated organizations and sources.
- Place page: settlement history, people born/lived/died there, organizations, migrations, related events, historical demographics and maps.
- Event page: date/location, causes, participants, consequences and source disagreement.
- Family page: multigenerational tree, household timeline, distribution across places, occupations and migration; dynastic mode only when appropriate.
- Organization page: membership over time, leaders, predecessor/successor bodies, places served and relationships.
- Chronology: global/continental/regional/local timelines built from the same event records.
- Maps: spatial views of place records, settlement change and historical routes, with an explicit selected year.

## Search and recommendations

Search across names, aliases, descriptions, dates, tags, and linked records. Suggest existing entities when writing prose, but **do not auto-create factual entries or silently add relationships**. Offer candidate links for review; provide backlinks and orphan-entry reports. Disambiguate similarly named people and places by date and location.

## File and application architecture

- **Now:** GitHub Markdown pages remain the durable, readable world-bible source. Genealogy has a small JSON archive and browser workbench.
- **Next:** shared structured records and entity IDs with export/import; use cross-references from Markdown to those IDs. Preserve all existing pages and historical content.
- **Later:** a unified application with navigation, editing, relationships, timeline/map/family views, change history and validation. Do not bolt unrelated isolated editors onto the repository indefinitely.
- **Non-goal:** pretending the current genealogy workbench already implements this entire design. It is a limited first prototype.

## First meaningful integration milestone

1. Define one compact schema for Person, Place, Event, Organization, Family/Household and Relation, including stable IDs, status and time.
2. Import or index existing Markdown entries without overwriting them.
3. Render an entry page with backlinks and referenced people/places/events.
4. Extend the genealogy view to draw from the same Person/Relation records (no duplicated person profiles).
5. Add consistency checks for missing references and contradictory time intervals.

## Reference sources

- [World Anvil — features](https://www.worldanvil.com/)
- [World Anvil — worldbuilding workflow](https://www.worldanvil.com/learn/workflows/writer-workflow)
- [Kanka — entity and relation overview](https://docs.kanka.io/en/latest/overview.html)
- [Kanka — worldbuilding features](https://kanka.io/features)
- [Genealogy system](../genealogy/README.md)
