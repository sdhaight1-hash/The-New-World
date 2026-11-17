#!/usr/bin/env python3
"""Validate The New World theme and page-layout files without third-party packages."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
ID = re.compile(r"^[a-z][a-z0-9-]{1,79}$")
THEME_COLORS = {"canvas", "surface", "text", "muted", "accent", "border"}
BLOCK_TYPES = {
    "hero", "columns", "stack", "article_body", "fact_panel", "backlinks",
    "related_entries", "sources", "image", "gallery", "annotated_image",
    "timeline", "family_tree", "map", "relationship_graph", "quote",
    "divider", "rich_text", "callout",
}
CONTAINERS = {"columns", "stack"}
LEAF_PROPS = {
    "hero": {"variant", "show_title", "show_subtitle", "media_asset_id"},
    "article_body": {"show_toc"},
    "fact_panel": {"include_status"},
    "backlinks": {"limit"},
    "related_entries": {"limit"},
    "sources": {"show_provenance"},
    "image": {"asset_id", "caption", "alt_text", "fit", "alignment"},
    "gallery": {"gallery_id", "limit"},
    "annotated_image": {"asset_id"},
    "timeline": {"scope", "limit"},
    "family_tree": {"scope", "depth"},
    "map": {"scope", "layer_ids", "height"},
    "relationship_graph": {"scope", "depth"},
    "quote": {"source_id", "text"},
    "divider": set(),
    "rich_text": {"text"},
    "callout": {"tone", "text"},
    "columns": {"ratios"},
    "stack": set(),
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def contrast(a: str, b: str) -> float:
    def luminance(hex_color: str) -> float:
        rgb = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        rgb = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
        return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def check_themes(obj: dict) -> set[str]:
    require(obj.get("schema_version") == 1, "theme schema version must be 1")
    require(isinstance(obj.get("themes"), list), "themes must be a list")
    seen = set()
    for t in obj["themes"]:
        tid = t.get("id")
        require(isinstance(tid, str) and ID.fullmatch(tid), "invalid theme ID")
        require(tid not in seen, f"duplicate theme {tid}")
        seen.add(tid)
        require(isinstance(t.get("name"), str) and t["name"].strip(), f"missing name: {tid}")
        for mode in ("dark", "light"):
            palette = t.get(mode)
            require(isinstance(palette, dict), f"{tid}.{mode}: missing palette")
            require(set(palette) == THEME_COLORS, f"{tid}.{mode}: unexpected/missing token")
            for key, color in palette.items():
                require(isinstance(color, str) and HEX.fullmatch(color), f"{tid}.{mode}.{key}: use #RRGGBB")
            for fg, bg in (("text", "canvas"), ("muted", "canvas"), ("accent", "canvas"), ("text", "surface")):
                require(contrast(palette[fg], palette[bg]) >= 4.5, f"{tid}.{mode}: {fg}/{bg} under 4.5:1")
    return seen


def check_layout(obj: dict, theme_ids: set[str]) -> None:
    require(obj.get("schema_version") == 1, "layout schema version must be 1")
    require(isinstance(obj.get("id"), str) and ID.fullmatch(obj["id"]), "invalid layout ID")
    require(obj.get("theme_id") in theme_ids, "unknown layout theme")
    seen = set()
    def walk(block: dict, depth: int = 0) -> None:
        require(isinstance(block, dict), "block must be object")
        require(depth <= 6, "layout nesting exceeds six")
        bid = block.get("id")
        typ = block.get("type")
        require(isinstance(bid, str) and ID.fullmatch(bid) and bid not in seen, f"invalid/duplicate block ID: {bid}")
        seen.add(bid)
        require(typ in BLOCK_TYPES, f"unknown block type: {typ}")
        require(set(block) <= {"id", "type", "props", "children"}, f"unknown block field: {bid}")
        props = block.get("props", {})
        require(isinstance(props, dict) and set(props) <= LEAF_PROPS[typ], f"unrecognized props: {bid}")
        for k, v in props.items():
            require(not isinstance(v, str) or not re.search(r"<script|javascript:|expression\s*\(", v, re.I), f"unsafe text: {bid}.{k}")
        children = block.get("children", [])
        require(isinstance(children, list), f"children must be array: {bid}")
        require(typ in CONTAINERS or not children, f"leaf block cannot have children: {bid}")
        require(typ not in CONTAINERS or children, f"container needs child blocks: {bid}")
        if typ == "columns":
            ratios = props.get("ratios")
            require(isinstance(ratios, list) and len(ratios) == len(children) and 1 <= len(ratios) <= 3, "column ratios mismatch")
            require(all(type(r) in (int, float) and 0 < r <= 12 for r in ratios), "invalid column ratios")
        for child in children:
            walk(child, depth + 1)
    blocks = obj.get("blocks")
    require(isinstance(blocks, list) and blocks, "layout must contain blocks")
    for b in blocks:
        walk(b)


def main() -> int:
    try:
        themes = json.loads((ROOT / "themes.json").read_text(encoding="utf-8"))
        layout = json.loads((ROOT / "layout-example.json").read_text(encoding="utf-8"))
        ids = check_themes(themes)
        check_layout(layout, ids)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: {len(ids)} themes and sample layout structurally valid; minimum contrast checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
