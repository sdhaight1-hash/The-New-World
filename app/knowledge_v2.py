"""Shared v2 entry schema and deterministic reference discovery.

No external dependencies. These functions do not modify prose or infer canon.
"""
from __future__ import annotations
import hashlib
import json
import re

TYPE_FIELDS = {
    "place": {"kind": "choice", "parent_place": "entry", "terrain": "text"},
    "person": {"birth": "text", "death": "text", "occupation": "text"},
    "organization": {"kind": "text", "founded": "text", "headquarters": "entry"},
    "family": {"origin": "text", "home": "entry"},
    "event": {"kind": "text", "date_note": "text", "location": "entry"},
    "subject": {"domain": "text", "period": "text"},
    "object": {"material": "text", "origin": "entry", "creator": "entry"},
    "source": {"creator": "text", "date": "text", "url": "text", "reliability": "choice"},
}
TYPE_LABELS = {
    "place": "Places", "person": "People", "organization": "Organizations",
    "family": "Families", "event": "Events", "subject": "Subjects",
    "object": "Objects", "source": "Sources"
}
FIELD_OPTIONS = {
    ("place", "kind"): ["region", "settlement", "landmark", "site", "territory", "other"],
    ("source", "reliability"): ["unassessed", "primary", "secondary", "disputed"],
}
SUBTYPES = {
    "place": ["region", "settlement", "landmark", "site", "territory"],
    "person": ["historical", "fictional"],
    "organization": ["government", "faction", "company", "institution"],
    "family": ["household", "lineage", "dynasty"],
    "event": ["conflict", "crisis", "discovery", "political"],
    "subject": ["culture", "technology", "ecology", "concept"],
    "object": ["artifact", "resource", "vehicle", "equipment"],
    "source": ["document", "testimony", "research", "dataset"],
}
LINK = re.compile(r"\[\[([a-zA-Z0-9:-]{3,100})(?:\|[^\]\n]{1,180})?\]\]")
MARKDOWN_LINK = re.compile(r"!?\[[^\]\n]*\]\([^\)\n]*\)")
URL = re.compile(r"https?://[^\s<>]+")
INLINE_CODE = re.compile(r"`+[^`\n]*`+")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s", re.M)


def normalize(text):
    return " ".join(text.casefold().split())


def validate_properties(typ, subtype, props, valid_target=None):
    if not isinstance(props, dict):
        raise ValueError("Properties must be an object")
    if subtype is not None and (not isinstance(subtype, str) or not re.fullmatch(r"[a-z][a-z0-9_]{1,60}", subtype)):
        raise ValueError("Invalid subtype")
    if subtype and typ in SUBTYPES and subtype not in SUBTYPES[typ]:
        raise ValueError("Unknown subtype for this entry type")
    spec = TYPE_FIELDS.get(typ)
    if spec is None and props:
        raise ValueError("Custom types do not yet define structured fields")
    for key, value in props.items():
        kind = (spec or {}).get(key)
        if not kind:
            raise ValueError("Unknown property: " + str(key))
        if value is None or value == "":
            continue
        if not isinstance(value, str) or len(value) > 2000:
            raise ValueError("Invalid value for " + key)
        if kind == "choice" and (typ, key) in FIELD_OPTIONS and value not in FIELD_OPTIONS[(typ, key)]:
            raise ValueError("Invalid choice for " + key)
        if kind == "entry" and valid_target is not None and not valid_target(value):
            raise ValueError("Missing or cross-world entry reference: " + key)
        if typ == "source" and key == "url" and not re.match(r"^https?://[^\s]+$", value):
            raise ValueError("Source URL must be http(s)")
    return props


def type_catalog():
    return [{"key": key, "label": TYPE_LABELS[key], "subtypes": SUBTYPES[key],
             "fields": [{"key": field, "kind": kind, "options": FIELD_OPTIONS.get((key, field), [])}
                        for field, kind in fields.items()]}
            for key, fields in TYPE_FIELDS.items()]


def mask_ineligible(body):
    """Preserve offsets while ignoring Markdown syntax and unsafe link locations."""
    spans = []
    fence = None
    offset = 0
    for line in body.splitlines(keepends=True):
        stripped = line.lstrip()
        marker = re.match(r"^(`{3,}|~{3,})", stripped)
        if marker:
            char, count = marker.group(1)[0], len(marker.group(1))
            if fence is None:
                fence = (char, count)
            elif fence[0] == char and count >= fence[1]:
                fence = None
            spans.append((offset, offset + len(line)))
        elif fence or re.match(r"^\s{0,3}#{1,6}\s", line):
            spans.append((offset, offset + len(line)))
        offset += len(line)
    for regex in (LINK, MARKDOWN_LINK, URL, INLINE_CODE):
        spans.extend((m.start(), m.end()) for m in regex.finditer(body))
    chars = list(body)
    for start, end in spans:
        for i in range(start, end):
            chars[i] = " "
    return "".join(chars)


def suggestions(body, source_id, entries, ignored=(), limit=150):
    """Return candidate spans. Ambiguous aliases never select a target by guess."""
    eligible = mask_ineligible(body)
    names = {}
    for entry in entries:
        if entry["id"] == source_id:
            continue
        for term in [entry["title"], *entry.get("aliases", [])]:
            norm = normalize(term)
            if len(norm) < 4:
                continue
            names.setdefault(norm, {})[entry["id"]] = entry
    ignored = set(ignored)
    matches = []
    for term, candidates in names.items():
        for match in re.finditer(re.escape(term), eligible.casefold()):
            start, end = match.span()
            if (start > 0 and (eligible[start-1].isalnum() or eligible[start-1] == "_")) or (
                end < len(eligible) and (eligible[end].isalnum() or eligible[end] == "_")):
                continue
            paragraph = body[max(0, body.rfind("\n\n", 0, start)+2):body.find("\n\n", end) if body.find("\n\n", end) >= 0 else len(body)]
            fingerprint = hashlib.sha256(normalize(paragraph).encode("utf-8")).hexdigest()[:24]
            options = sorted(candidates.values(), key=lambda e: (e["title"].casefold(), e["id"]))
            visible = body[start:end]
            available = [e for e in options if (e["id"], normalize(visible), fingerprint) not in ignored]
            if available:
                matches.append({"start": start, "end": end, "text": visible,
                                "fingerprint": fingerprint,
                                "candidates": [{"id": e["id"], "title": e["title"],
                                                "type": e["type"], "summary": e.get("summary", "")[:160]}
                                               for e in available]})
    matches.sort(key=lambda x: (x["start"], -(x["end"]-x["start"]), x["text"]))
    chosen = []
    last_end = -1
    for match in matches:
        if match["start"] < last_end:
            continue
        chosen.append(match)
        last_end = match["end"]
        if len(chosen) >= limit:
            break
    return chosen


def insert_approved(body, match, target_id):
    if target_id not in {c["id"] for c in match["candidates"]}:
        raise ValueError("Target not among discovered candidates")
    start, end = match["start"], match["end"]
    if body[start:end] != match["text"]:
        raise ValueError("Stale mention")
    return body[:start] + "[[" + target_id + "|" + body[start:end] + "]]" + body[end:]
