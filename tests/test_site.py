"""Offline acceptance checks for the China-money evidence site.

Run after building: python -m unittest discover -s tests -v
No network access is required; external links are checked structurally, not fetched.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
OUT = ROOT / "site" / "public"
DATA = ROOT / "data"
DOMAINS = ("china", "us", "routes", "analysis")
VERIFIED_ON = "2026-11-07"
REQUIRED_PAGES = {
    "index.html", "china.html", "us.html", "routes.html", "requirements.html",
    "costs.html", "analysis.html", "flagged.html", "sources.html", "executive-summary.html",
}


def iter_rows(obj: Any) -> Iterable[dict]:
    if isinstance(obj, dict):
        if "source_ids" in obj:
            yield obj
        for value in obj.values():
            yield from iter_rows(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from iter_rows(value)


def load_research() -> tuple[dict[str, dict], dict[str, dict], list[dict]]:
    data = {}
    sources = {}
    rows = []
    for domain in DOMAINS:
        payload = json.loads((RESEARCH / f"{domain}.json").read_text(encoding="utf-8"))
        data[domain] = payload
        for source in payload.get("sources", []):
            sources[source["id"]] = {**source, "domain": domain}
        rows.extend(iter_rows(payload))
    return data, sources, rows


class RowAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_tbody = False
        self.in_row = False
        self.row_external = False
        self.rows: list[bool] = []
        self.links: list[str] = []
        self.remote_assets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "tbody":
            self.in_tbody = True
        elif tag == "tr" and self.in_tbody:
            self.in_row = True
            self.row_external = False
        elif tag == "a" and a.get("href"):
            href = a["href"]
            self.links.append(href)
            if self.in_row and href.startswith(("http://", "https://")):
                self.row_external = True
        elif tag in {"link", "script", "img"}:
            url = a.get("href") or a.get("src")
            if url and url.startswith(("http://", "https://")):
                self.remote_assets.append(url)

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.in_row:
            self.rows.append(self.row_external)
            self.in_row = False
        elif tag == "tbody":
            self.in_tbody = False


def hash_tree(path: Path) -> dict[str, str]:
    return {
        str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(path.rglob("*")) if p.is_file()
    }


class ResearchIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data, cls.sources, cls.rows = load_research()

    def test_unique_sources_and_official_urls(self) -> None:
        self.assertEqual(len(self.sources), 58)
        for sid, source in self.sources.items():
            self.assertTrue(source["url"].startswith(("http://", "https://")), sid)
            self.assertEqual(source.get("verified_on"), VERIFIED_ON, sid)
            self.assertTrue(source.get("publisher"), sid)
            self.assertTrue(source.get("locator"), sid)

    def test_every_row_has_resolving_sources(self) -> None:
        self.assertEqual(len(self.rows), 165)
        for row in self.rows:
            self.assertTrue(row.get("id"), row)
            self.assertTrue(row["source_ids"], row["id"])
            for ref in row["source_ids"]:
                self.assertIn(ref, self.sources, f"{row['id']} -> {ref}")

    def test_unverified_values_remain_blank(self) -> None:
        for domain in ("china", "us"):
            for row in self.data[domain]["user_unknowns"]:
                self.assertIsNone(row["value"], row["id"])
        for route in self.data["routes"]["routes"]:
            self.assertTrue(all(value is None for value in route["costs"].values()), route["id"])
            self.assertTrue(route["flag"], route["id"])
        for component in self.data["analysis"]["cost_model"]["components"]:
            self.assertIsNone(component["value"], component["id"])
            self.assertTrue(component["flag"], component["id"])

    def test_route_inventory_coverage(self) -> None:
        routes = self.data["routes"]["routes"]
        self.assertEqual(len(routes), 29)
        self.assertEqual({r["id"] for r in routes}, {f"R{i:02d}" for i in range(1, 30)})
        for route in routes:
            if route["status"] in {"unverified_candidate", "not_repatriation", "prohibited_high_risk"}:
                self.assertTrue(route["flag"], route["id"])


class GeneratedSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data, cls.sources, cls.rows = load_research()
        cls.html = {p.name: p.read_text(encoding="utf-8") for p in OUT.glob("*.html")}
        cls.all_html = "\n".join(cls.html.values())

    def test_required_pages_and_assets(self) -> None:
        self.assertTrue(REQUIRED_PAGES.issubset(self.html.keys()))
        self.assertTrue((OUT / "assets" / "styles.css").is_file())
        self.assertTrue((OUT / "assets" / "app.js").is_file())
        self.assertTrue((OUT / ".nojekyll").is_file())

    def test_every_data_row_links_an_external_source(self) -> None:
        total = 0
        for name, markup in self.html.items():
            audit = RowAudit()
            audit.feed(markup)
            if audit.rows:
                self.assertTrue(all(audit.rows), f"{name}: data row without external source link")
            else:
                self.assertNotIn("<table", markup, f"{name}: table present but no tbody rows parsed")
            self.assertFalse(audit.remote_assets, f"{name}: remote asset {audit.remote_assets}")
            total += len(audit.rows)
        self.assertGreaterEqual(total, 165)

    def test_internal_links_resolve(self) -> None:
        for name, markup in self.html.items():
            audit = RowAudit()
            audit.feed(markup)
            for href in audit.links:
                if href.startswith(("http://", "https://", "#", "mailto:", "tel:")):
                    continue
                target = href.split("#", 1)[0]
                self.assertTrue((OUT / target).exists(), f"{name}: broken internal link {href}")

    def test_all_research_rows_and_flags_are_published(self) -> None:
        for row in self.rows:
            self.assertIn(row["id"], self.all_html, f"missing rendered row {row['id']}")
        flagged = self.html["flagged.html"]
        for domain in DOMAINS:
            for row in self.data[domain].get("flags", []):
                self.assertIn(row["id"], flagged, f"missing flag {row['id']}")
        for row in self.rows:
            if row.get("flag"):
                self.assertIn(row["id"], flagged, f"missing row-level flag {row['id']}")

    def test_source_register_contains_every_source(self) -> None:
        register = self.html["sources.html"]
        for sid, source in self.sources.items():
            self.assertIn(sid, register)
            self.assertIn(source["url"], register)

    def test_route_cost_cells_are_visibly_blank(self) -> None:
        costs = self.html["costs.html"]
        match = re.search(r'<table id="route-costs-table".*?</table>', costs, re.S)
        self.assertIsNotNone(match)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", match.group(0), re.S)
        data_rows = [row for row in rows if "<td" in row]
        self.assertEqual(len(data_rows), 29)
        for row in data_rows:
            self.assertEqual(row.count('class="blank-cell"'), 5, row)
            visible = re.sub(r"<span class=\"sr-only\">.*?</span>", "", row, flags=re.S)
            cells = re.findall(r"<td[^>]*>(.*?)</td>", visible, re.S)
            for cell in cells[2:7]:
                self.assertFalse(re.search(r"\d", cell), f"numeric value in blank cost cell: {cell}")

    def test_no_placeholders_or_local_backend_calls(self) -> None:
        for name, markup in self.html.items():
            self.assertNotRegex(markup, r"TODO|FIXME|localhost|127\.0\.0\.1", name)


class CsvExport(unittest.TestCase):
    def test_evidence_csv(self) -> None:
        with (DATA / "evidence.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 165)
        for row in rows:
            self.assertTrue(row["id"])
            self.assertTrue(row["source_ids"])
            self.assertTrue(row["source_urls"].startswith(("http://", "https://")))

    def test_sources_csv(self) -> None:
        with (DATA / "sources.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 58)
        self.assertEqual(len({row["id"] for row in rows}), 58)


class DeterministicBuild(unittest.TestCase):
    def test_rebuild_is_identical(self) -> None:
        before_site = hash_tree(OUT)
        before_data = hash_tree(DATA)
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build_site.py")], check=True, cwd=ROOT)
        subprocess.run([sys.executable, str(ROOT / "scripts" / "export_data.py")], check=True, cwd=ROOT)
        self.assertEqual(before_site, hash_tree(OUT))
        self.assertEqual(before_data, hash_tree(DATA))


if __name__ == "__main__":
    unittest.main()
