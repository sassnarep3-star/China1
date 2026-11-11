#!/usr/bin/env python3
"""Independently check the published guide's local links, citations and ladder.

This is an offline structural/arithmetic audit, NOT a claim that a linked
regulation supports the words next to it. External sources require separate
manual re-reading. Unknown costs must remain blank and flagged.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "guide"
DATA = GUIDE / "data"
EXPECTED_AMOUNTS = list(range(10_000, 400_001, 10_000))
errors: list[str] = []
warnings: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


class Document(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.duplicates: list[str] = []
        self.links: list[str] = []
        self.tbody_depth = 0
        self.row: list[str] | None = None
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        for key in ("id",):
            if a.get(key):
                value = a[key]
                if value in self.ids:
                    self.duplicates.append(value)
                self.ids.add(value)
        if tag == "a" and a.get("name"):
            self.ids.add(a["name"])
        if tag == "tbody":
            self.tbody_depth += 1
        if tag == "tr" and self.tbody_depth:
            self.row = []
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.row is not None:
                self.row.append(a["href"])
        if tag in ("img", "script", "link", "iframe"):
            value = a.get("src") if tag != "link" else a.get("href")
            if value:
                self.links.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        if tag == "tbody":
            self.tbody_depth = max(self.tbody_depth - 1, 0)


def local_destination(page: Path, href: str) -> tuple[Path, str] | None:
    u = urlsplit(href)
    if u.scheme or u.netloc:
        # Canonical deployment URLs still refer to this repository, not an external source.
        if u.scheme != "https" or u.netloc != "sassnarep3-star.github.io":
            return None
        if not u.path.startswith("/China1/"):
            return None
        path = ROOT / unquote(u.path[len("/China1/"):])
    elif u.path.startswith("/"):
        # Pages is a project site, so root-relative references without /China1/ break.
        if not u.path.startswith("/China1/"):
            errors.append(f"{page.relative_to(ROOT)}: project-root link missing /China1/: {href}")
            return None
        path = ROOT / unquote(u.path[len("/China1/"):])
    elif u.path:
        path = page.parent / unquote(u.path)
    else:
        path = page
    path = path.resolve()
    if not path.is_relative_to(ROOT):
        errors.append(f"{page.relative_to(ROOT)}: local link escapes repository: {href}")
        return None
    if path.is_dir():
        path = path / "index.html"
    return path, unquote(u.fragment)


def page_checks() -> tuple[int, int, int]:
    source_doc = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
    review_doc = json.loads((ROOT / "quality-713a97b7/findings.json").read_text(encoding="utf-8"))
    source_urls = {s["url"] for s in source_doc["sources"] + review_doc["sources"]}
    pages = [ROOT / "index.html", *sorted(GUIDE.glob("*.html")), ROOT / "quality-713a97b7/index.html"]
    parsed: dict[Path, Document] = {}

    def parse(path: Path) -> Document:
        if path not in parsed:
            parser = Document()
            parser.feed(path.read_text(encoding="utf-8", errors="replace"))
            parsed[path] = parser
        return parsed[path]

    local_count = rows_count = 0
    for page in pages:
        doc = parse(page)
        rel = page.relative_to(ROOT)
        if doc.duplicates:
            warnings.append(f"{rel}: duplicate ids: {', '.join(doc.duplicates[:5])}")
        for index, hrefs in enumerate(doc.rows, 1):
            rows_count += 1
            # Stronger than a host-only check: the link must be in the source register.
            check(any(href in source_urls for href in hrefs), f"{rel}: body row {index} has no registered primary/provider source")
        for href in doc.links:
            target = local_destination(page, href)
            if target is None:
                continue
            local_count += 1
            dest, fragment = target
            if not dest.is_file():
                errors.append(f"{rel}: missing local target: {href}")
            elif fragment and dest.suffix.lower() in (".html", ".htm"):
                check(fragment in parse(dest).ids, f"{rel}: missing fragment: {href}")
    return len(pages), rows_count, local_count


def cost_checks() -> tuple[int, int, int]:
    methods = json.loads((DATA / "methods.json").read_text(encoding="utf-8"))["methods"]
    sources = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))["sources"]
    flags = {f["id"] for f in json.loads((DATA / "flagged.json").read_text(encoding="utf-8"))["items"]}
    source_urls = {s["url"] for s in sources}
    prices = json.loads((DATA / "prices.json").read_text(encoding="utf-8"))
    with (DATA / "cost-ladder.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    method_ids = {m["id"] for m in methods}
    check(len(method_ids) == len(methods), "duplicate method IDs")
    check(len(rows) == len(methods) * len(EXPECTED_AMOUNTS), "cost CSV does not contain 40 rows per method")
    by_method: dict[str, list[dict[str, str]]] = {mid: [] for mid in method_ids}
    for row in rows:
        mid = row["method_id"]
        if mid not in by_method:
            errors.append(f"unrecognised method in cost table: {mid}")
            continue
        by_method[mid].append(row)
        urls = row["source_urls"].split()
        check(bool(urls) and all(url in source_urls for url in urls), f"{mid} ${row['amount_usd']}: unregistered source")
        check(row["status"] in {"value", "partial", "blank", "na", "penalty"}, f"{mid} ${row['amount_usd']}: unknown status")
        if row["status"] in {"blank", "partial", "na"}:
            check(not row["total_cost_usd"], f"{mid} ${row['amount_usd']}: unknown/not-applicable cost is not blank")
        if row["status"] in {"blank", "partial"}:
            ids = row["flags"].split()
            check(bool(ids) and all(fid in flags for fid in ids), f"{mid} ${row['amount_usd']}: incomplete cost lacks registered flag")
        if row["total_cost_usd"]:
            try:
                check(Decimal(row["total_cost_usd"]) >= 0, f"{mid} ${row['amount_usd']}: negative cost")
            except Exception:
                errors.append(f"{mid} ${row['amount_usd']}: invalid cost")
    for mid, group in by_method.items():
        try:
            amounts = [int(row["amount_usd"]) for row in group]
        except ValueError:
            errors.append(f"{mid}: invalid target")
            continue
        check(sorted(amounts) == EXPECTED_AMOUNTS, f"{mid}: missing/duplicate $10k increments")

    # Recompute the current documented BOC *scenario*, not a personal quote.
    # If its pricing model changes, flag this comparison for review rather than
    # assert that an unknown alternative formula is necessarily wrong.
    compared = 0
    try:
        d = Decimal
        buy = d(prices["boc_buy_per_100"]) / 100
        sell = d(prices["boc_sell_per_100"]) / 100
        mid = (buy + sell) / 2
        b = prices["boc"]
        incoming = d(prices["receiving"]["chase_incoming_wire_usd"])
        for row in by_method.get("M01", []):
            if row["status"] != "value":
                continue
            n = d(row["amount_usd"])
            held = n * mid
            fee = max(d(b["commission_min_cny"]), min(d(b["commission_max_cny"]), held * d(b["commission_rate"])))
            modeled = n * (1 - mid / sell) + (fee + d(b["cable_cny"])) / sell + d(b["full_amount_usd"]) + incoming
            expected = modeled.quantize(d("0.01"), rounding=ROUND_HALF_UP)
            actual = d(row["total_cost_usd"])
            if abs(actual - expected) > d("0.01"):
                warnings.append(f"M01 ${int(n)}: CSV {actual} differs from prior illustrative model {expected}; review assumptions")
            compared += 1
    except (KeyError, ValueError, ArithmeticError) as exc:
        warnings.append(f"BOC model could not be compared: {exc}")
    # Penalty exposure is not a quoted transfer fee; do not silently count it as cost.
    penalty = sum(row["status"] == "penalty" for row in rows)
    if penalty:
        warnings.append(f"{penalty} CSV rows labelled penalty contain legal exposure, not a transfer price")
    return len(methods), len(rows), compared


def main() -> int:
    pages, table_rows, links = page_checks()
    methods, rows, compared = cost_checks()
    for warning in warnings[:30]:
        print("REVIEW:", warning)
    if len(warnings) > 30:
        print(f"REVIEW: {len(warnings) - 30} further model differences omitted")
    if errors:
        for err in errors[:60]:
            print("FAIL:", err, file=sys.stderr)
        print(f"FAIL: {len(errors)} structural errors", file=sys.stderr)
        return 1
    print(f"PASS: {pages} canonical pages; {table_rows} body rows with registered sources; {links} local links/fragments; "
          f"{methods} methods × 40 amounts = {rows} CSV rows; {compared} BOC example rows compared. "
          f"{len(warnings)} review notes. No external source content was fetched by this check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
