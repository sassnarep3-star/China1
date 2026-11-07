#!/usr/bin/env python3
"""Export flat, source-linked CSV evidence tables from research/*.json."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
DATA = ROOT / "data"
DOMAINS = ("china", "us", "routes", "analysis")


def walk(obj: Any, section: str = "") -> Iterable[tuple[str, dict]]:
    if isinstance(obj, dict):
        if "source_ids" in obj:
            yield section, obj
        for key, value in obj.items():
            child = f"{section}.{key}" if section else key
            yield from walk(value, child)
    elif isinstance(obj, list):
        for value in obj:
            yield from walk(value, section)


def first(row: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def main() -> None:
    DATA.mkdir(exist_ok=True)
    sources: dict[str, dict] = {}
    rows: list[dict] = []
    for domain in DOMAINS:
        payload = json.loads((RESEARCH / f"{domain}.json").read_text(encoding="utf-8"))
        for source in payload.get("sources", []):
            sources[source["id"]] = source
        for section, row in walk(payload):
            refs = row["source_ids"]
            rows.append({
                "domain": domain,
                "section": section,
                "id": row.get("id", ""),
                "label": first(row, ("topic", "field", "name", "step", "component", "scenario", "myth", "term", "requirement")),
                "summary": first(row, ("finding", "requirement", "action", "definition", "analysis", "correction", "recommendation", "mechanism", "formula", "needed_for", "basis", "condition")),
                "value": "" if row.get("value") is None else row.get("value"),
                "unit": row.get("unit") or "",
                "status": row.get("status") or row.get("severity") or "",
                "flag": row.get("flag") or row.get("resolution") or "",
                "source_ids": " | ".join(refs),
                "source_urls": " | ".join(sources[ref]["url"] for ref in refs),
            })
    with (DATA / "evidence.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    source_rows = [{
        "id": sid,
        "domain": next(d for d in DOMAINS if any(s["id"] == sid for s in json.loads((RESEARCH / f"{d}.json").read_text(encoding="utf-8")).get("sources", []))),
        "title": source["title"],
        "publisher": source["publisher"],
        "url": source["url"],
        "published": source.get("published") or "",
        "locator": source.get("locator") or "",
        "supports": source.get("supports") or "",
        "access": source.get("access") or "",
        "verified_on": source.get("verified_on") or "",
    } for sid, source in sources.items()]
    with (DATA / "sources.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(source_rows[0]))
        writer.writeheader()
        writer.writerows(source_rows)
    print(f"Exported {len(rows)} evidence rows and {len(source_rows)} sources -> {DATA.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
