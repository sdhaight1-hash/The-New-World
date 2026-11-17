# The New World — Conworld Atlas & World Bible

**A realistic, globally scoped, post-industrial alternate future Earth.** The primary reference era is approximately fifty years after the Cascade. This is an open-ended **worldbuilding project**, not a novel outline; no protagonists, book sequence, or fixed geographical limits are assumed.

## Run World Bible Studio

The New World now includes a **working, local-first worldbuilding application** that can host multiple independent worlds. The repository's historical Bible is the initial dataset; the engine itself uses generic person, place, organization, family, event, subject, and media records.

**Windows quick launch:** double-click `Launch-World-Bible.cmd` after cloning the repository and installing Python 3.11+. Image uploads need Pillow (see below). The launcher safely imports missing original Markdown pages and opens the browser.

From the project directory with Python 3.11+:

1. Install the image dependency: \`python -m pip install -r app/requirements.txt\`
2. Import the existing Bible without overwriting later edits: \`python app/seed.py\`
3. Launch the application: \`python app/server.py\`
4. Open **http://127.0.0.1:8765/app/**

**[Studio setup and features](app/README.md)** · **[Automated tests](https://github.com/sdhaight1-hash/The-New-World/actions/workflows/test-studio.yml)**

The application supports independent worlds, encyclopedia editing, identity-preserving hyperlinks and backlinks, reference suggestions, typed/dated relationships, family connections, a chronological event list, a 2D map of documented locations, reusable images with captions, and entry-specific themes and section arrangements. Data lives locally in \`.worldbible/\`, which must be backed up. The Export button saves world metadata and text records as JSON; **media binaries require separate backup**.

**Current maturity: functional foundation, not feature-complete.** Advanced GIS drawing, complex page builder drag-and-drop, high-volume indexing, full evidence/version systems, interactive multigenerational chart layouts and finished visual regression testing remain open. Previous stand-alone HTML tools are prototypes and should not be expanded as separate databases.

---

## Begin here

- [Canon, assumptions, and open questions](bible/00-foundations.md)
- [Master historical chronology](bible/01-chronology.md)
- [The Great Plague and demographic inversion](bible/02-great-plague.md)
- [The Cascade and the Long Storms](bible/03-cascade.md)
- [Technology and material culture](bible/04-technology.md)
- [Political and social development](bible/05-successor-societies.md)
- [Connected world encyclopedia architecture](bible/08-world-bible-architecture.md)
- [Relationship mapping and link discovery](bible/09-linking-and-discovery.md)
- [RFC 001: Unified Historical Knowledge Core](bible/10-rfc-historical-knowledge-core.md)
- [RFC 002: Location and Faction Systems](bible/11-rfc-location-faction-systems.md)
- [RFC 003: Historical Timeline and Chronology Engine](bible/12-rfc-timeline-engine.md)
- [RFC 004: Media Library and Image Handling](bible/13-rfc-media-image-handling.md)
- [Unified architecture & migration plan](bible/15-unified-architecture.md)
- [Visual design, themes & entry builder](bible/16-ux-and-entry-designer.md)
- [2D Historical Atlas](bible/17-rfc-2d-historical-atlas.md)
- [Versioned design presets and layout](design/README.md)
- [RFC 005: Earlier 3D atlas proposal (superseded)](bible/14-rfc-gods-eye-atlas.md)
- [Open the link discovery explorer](tools/discovery/index.html)
- [Genealogy, family history, and kinship](bible/07-genealogy-dynasties.md)
- [Genealogy data model and roadmap](genealogy/README.md)
- [Open genealogy workbench](tools/genealogy/index.html)
- [Southern California: Big Bear and Victor Valley](regions/southern-california.md)
- [Northern Oregon: Clatsop County](regions/clatsop-county.md)
- [Wyoming: ranchlands and reservation region](regions/wyoming.md)
- [Questions and research priorities](bible/06-research-register.md)

## Timekeeping

**Year 0** is the onset of the Cascade, currently *tentatively* placed around **2034–2035**. The plague is tentatively tied to international travel surrounding the **2030 men's World Cup**, with epidemic waves and partial recovery preceding the Cascade. **Year 50 (~2084–2085) is the main reference era**, not a fixed narrative date.

## Editorial principles

1. **Real Earth remains real Earth.** Geography, ecology, physics, and historical infrastructure are grounded in reality; extrapolation is explicit.
2. **Two unrelated catastrophes.** Pandemic deaths and migration reshape populations; repeated severe solar events and cascading institutional failures damage recovery. No magic, no suppression of gunpowder or gasoline.
3. **Never confuse hypothesis with canon.** Pages label what is established, provisional, and unresolved. Every region can change as evidence improves.
4. **Global scope, local depth.** Big Bear–Victor Valley, Clatsop County and the Wyoming ranch/reservation country are *starting focus areas*, not the boundaries of the world.
5. **Causal history.** Track populations, land, water, food, skills, logistics, institutions, generational change, trade and political legitimacy before asserting dynasties or wars.
6. **No instant medieval reset.** Firearms and engines still work if maintained; ammunition, fuel, equipment and industrial inputs become unequally available. Diverse successor institutions, including feudal-like systems, emerge over time.

## Contribution convention

Each entry should note: **status**, **geographic/temporal scope**, **causes and dependencies**, **links to related entries**, **uncertainties**, and **sources to verify**. Distinguish real baseline claims from projected world history. Avoid invented precise statistics until a demographic or infrastructure model supports them.
