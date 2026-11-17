# The New World — Conworld Atlas & World Bible

**A realistic, globally scoped, post-industrial alternate future Earth.** The primary reference era is approximately fifty years after the Cascade. This is an open-ended **worldbuilding project**, not a novel outline; no protagonists, book sequence, or fixed geographical limits are assumed.

## Explore the world and build its encyclopedia

The project now has two deliberately separate experiences sharing one knowledge base: a **reader-facing illustrated encyclopedia** and a **creator-focused Studio**.

- **Reader:** `http://127.0.0.1:8765/read/` — editorial presentation, maps, history, article discovery and published-only content.
- **Studio:** `http://127.0.0.1:8765/app/` — worldbuilding, editorial drafting, relationships, images, design and publication controls.

Run `python app/launch.py` to start locally. The repository also includes a published-only **static website exporter**: `python app/publish_site.py public-site` after selecting which entries to publish.

**[Reader experience research](bible/18-reader-first-ux.md)** · **[Visual worldbuilding and moodboards](bible/19-visual-worldbuilding-and-moodboards.md)** · **[Reader publishing and site-export guide](app/README.md#reader-first-world-encyclopedia)**

---

## Run World Bible Studio

The New World now includes a **working, local-first worldbuilding application** that can host multiple independent worlds. The repository's historical Bible is the initial dataset; the engine itself uses generic person, place, organization, family, event, subject, and media records.

**Windows quick launch:** double-click `Launch-World-Bible.cmd` after cloning the repository and installing Python 3.11+. Image uploads need Pillow (see below). The launcher safely imports missing original Markdown pages and opens the browser.

From the project directory with Python 3.11+:

1. Install the image dependency: `python -m pip install -r app/requirements.txt`
2. Import the existing Bible without overwriting later edits: `python app/seed.py`
3. Launch the application: `python app/launch.py` (or use `app/server.py` for server-only mode)
4. Open **http://127.0.0.1:8765/app/**

**[Studio setup and features](app/README.md)** · **[Navigation and UI/UX Guide](app/NAVIGATION.md)** · **[Automated tests](https://github.com/sdhaight1-hash/The-New-World/actions/workflows/test-studio.yml)**

The application supports independent worlds, encyclopedia editing, identity-preserving hyperlinks and backlinks, reference suggestions, typed/dated relationships, family connections, a chronological event list, a 2D map of documented locations, reusable images with captions, and entry-specific themes and section arrangements. Data lives locally in `.worldbible/`, which must be backed up. The Export button saves world metadata and text records as JSON; **media binaries require separate backup**.

**Current maturity: functional foundation, not feature-complete.** Advanced GIS drawing, complex page builder drag-and-drop, high-volume indexing, full evidence/version systems, interactive multigenerational chart layouts and finished visual regression testing remain open. Previous stand-alone HTML tools are prototypes and should not be expanded as separate databases.

---

## Existing worldbuilding canon — imported into Studio

The first structured canon population is now in [`canon/entries.json`](canon/entries.json), with a [source and provenance guide](canon/README.md). It covers **107 world-content records** in a fresh database (10 historical/geographical source articles plus 97 structured records), including **112 typed relationships** connecting regions, settlements, catastrophe phases, technology and institutional themes.

The normal launcher imports this content automatically, **without replacing existing Studio edits or publishing drafts**. Earlier imports mistakenly included software-design documents; the launcher now removes their untouched copies only after making a complete backup. Edited or published copies are protected and flagged for review. It reuses the original Great Plague and Cascade documents as the authoritative event records rather than duplicating them.

This is an inventory of what the prior source documents actually establish—not a generated set of fictional rulers, invented dynasties, falsely precise historical dates or guesswork about the Wyoming reservation. Names and outcomes not yet decided are explicitly treated as open.

---

## The world itself — source material

These documents establish the setting and are the only Markdown sources imported as world content. The [structured canon inventory](canon/entries.json) adds individual places, events, and linked subjects from them.

- [**The Pre-Divergence World (2019–November 2026)** — public health, politics, economics, warfare, climate and technology](bible/21-real-world-2019-2026.md)
- [The Brief Age of AI (2022–2030), documented history and alternate-history divergence](bible/20-brief-age-of-ai.md)
- [Master historical chronology](bible/01-chronology.md)
- [The Great Plague and demographic inversion](bible/02-great-plague.md)
- [The Cascade and the Long Storms](bible/03-cascade.md)
- [Technology and material culture](bible/04-technology.md)
- [Political and social development](bible/05-successor-societies.md)
- [Southern California: Big Bear and Victor Valley](regions/southern-california.md)
- [Northern Oregon: Clatsop County](regions/clatsop-county.md)
- [Wyoming: ranchlands and reservation region](regions/wyoming.md)

## Editorial notes and research — not encyclopedia entries

These guide decisions about what becomes canon, but are **not places, events, people, or other entries in the world**.

- [Foundations and canon ledger](bible/00-foundations.md)
- [Research register and unresolved questions](bible/06-research-register.md)
- [Genealogy and kinship system planning](bible/07-genealogy-dynasties.md)

## Studio software documentation — not world lore

These are engineering and interface design references for building the program. They stay in GitHub and **must never be imported into the world's encyclopedia**.

- [World Bible information architecture](bible/08-world-bible-architecture.md)
- [Relationship mapping and discovery design](bible/09-linking-and-discovery.md)
- [Historical knowledge core RFC](bible/10-rfc-historical-knowledge-core.md)
- [Locations and factions RFC](bible/11-rfc-location-faction-systems.md)
- [Timeline engine RFC](bible/12-rfc-timeline-engine.md)
- [Media handling RFC](bible/13-rfc-media-image-handling.md)
- [Superseded 3D atlas proposal](bible/14-rfc-gods-eye-atlas.md)
- [Unified technical architecture](bible/15-unified-architecture.md)
- [Studio interface and page design](bible/16-ux-and-entry-designer.md)
- [2D atlas design](bible/17-rfc-2d-historical-atlas.md)
- [Reader-first experience design](bible/18-reader-first-ux.md)
- [Visual worldbuilding and moodboards](bible/19-visual-worldbuilding-and-moodboards.md)
- [Theme and layout implementation](design/README.md)
- [Legacy discovery prototype](tools/discovery/index.html)
- [Legacy genealogy prototype](tools/genealogy/index.html)

## Timekeeping

**The world chronology begins in 2019. Documented history is followed through November 17, 2026, encompassing COVID-19, economic disruption, political transitions, wars, energy and trade, climate and AI. ChatGPT’s November 2022 launch is a pivotal event within this baseline, not its beginning. A convincing December 2026 AGI announcement marks the alternate-history divergence, followed by fictional large-scale automation and labor displacement in 2027–2029.**

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
