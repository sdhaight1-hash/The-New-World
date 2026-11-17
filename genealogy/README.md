# Genealogy, Families and Kinship

Genealogy is a **general-purpose relationship, historical and information-organizing system** inside the world bible. It exists for **all people and communities**, including ordinary households, migration histories, biological and adoptive kinship, professions, community ties, and—when relevant—political dynasties. The family tree is a view of shared person records, not a separate collection of duplicate biographies. See the [connected encyclopedia architecture](../bible/08-world-bible-architecture.md).

## Start

Open [the browser-based genealogy workbench](../tools/genealogy/index.html) locally in a modern browser. The workbench lets you create/edit people, connect biological/adoptive/step parents, record partners, inspect a person's parent/child links, check relationships and export/import a JSON copy. Data is saved to **your browser's local storage**, **not** automatically to GitHub. Export regularly and commit the JSON to this repo as a deliberate editorial action. The app never silently overwrites the Bible.

The initial [dataset](data.json) is intentionally empty; **no people or noble houses have been invented**.

## Architecture

The current prototype keeps a versioned JSON graph with stable IDs. **Long term, these records should join a shared encyclopedia data model rather than remain a separate genealogy database:**
- `people`: name and name-history, vital dates (with precision), notes, reference to places, narrative status.
- `parentage`: parent → child directed relationship, tagged biological/adoptive/step/claimed/unknown, with evidence/status.
- `unions`: partnerships/marriages that are independent from parentage and may have starts/ends.
- `houses`: **political/social identities**, not a substitute for biological ancestry.
- `house_memberships`: who belongs to a house, and when, with affiliation role.
- `events`: births, deaths, marriages, migrations, adoptions, investitures, wars, treaties, succession etc.
- `claims`: dated assertions or disputed interpretations, with citations or world-canon status.
- `institutions`, `offices`, `tenures`: positions and succession histories separate from ancestry.
- `places`, `sources`: link to canonical world-bible atlas entries, not duplicated prose.

**The prototype implements people, parentage and unions today.** Other collections are specified for future stages but not yet fully editable in the UI.

## Data integrity

- Relationship links use stable IDs and never depend on a person's display name.
- No parentage cycles: someone cannot become their own ancestor.
- Birth/death uncertainty is recorded as text until structured dates are implemented.
- Biological ancestry, adoption, guardianship, marriage, house membership, legal legitimacy and title succession are **not interchangeable**.
- Ambiguous or disputed ancestry must remain an explicit claim rather than silently accepted fact.
- No royal or feudal structure is forced on all regions.
- Deletion should never silently erase associated evidence; robust delete/merge workflows remain a later milestone.

## Roadmap

1. **Delivered:** browser workbench, create/edit people, typed parentage, partner links, relationship overview, JSON import/export, basic integrity validation.
2. Typed event chronology, places linked into atlas, per-fact source/evidence assertions, full uncertainty handling and conflict flagging.
3. Ancestor/descendant/pedigree graphical views, search and filters, cousinship/common ancestor computation, household/union charts.
4. Ordinary household history and community migrations integrated into Person/Place/Event articles; optional political houses, alliances, estates, tenures, succession and competing claims.
5. Consistency audit (age gaps, overlapping tenures, impossible date sequences), historical “as of Year N” views, GEDCOM 7 import/export and bulk editing.
6. World-bible integration: biographies, genealogy indexes, location links, dynasty timelines and auto-generated pages from structured data.

## Research references

- [GEDCOM 7 standard](https://gedcom.io/specifications/FamilySearchGEDCOMv7.html)
- [Gramps Web object model](https://www.grampsweb.org/user-guide/data-model/)

For canonical norms and interpretation see [Dynasties, Kinship and Succession](../bible/07-genealogy-dynasties.md).
