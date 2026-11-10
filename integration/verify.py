"""Verify the consolidated dashboard and crawl the combined static repository.

Checks prove deterministic arithmetic, citation presence, blank semantics and
internal-link integrity. They do not prove legal correctness, personal
eligibility, executable prices or future external-link availability.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import runpy
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "integration"
GENERATED = [
    ROOT / "index.html", OUT / "costs.html", OUT / "methods.html",
    OUT / "tax.html", OUT / "review.html", OUT / "evidence.html",
    OUT / "methodology.html", OUT / "costs.json", OUT / "costs.csv",
    OUT / "evidence.json",
]
PAGES = [p for p in GENERATED if p.suffix == ".html"]
TARGETS = list(range(10_000, 400_001, 10_000))
RATE = Decimal("6.6903")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.rows = []
        self.row = None
        self.viewport = False
        self.mobile_labels = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = True
        if tag == "td" and "data-label" in a:
            self.mobile_labels += 1
        if tag == "tr":
            self.row = []
        if tag in {"a", "link", "script", "img"}:
            attr = "href" if tag in {"a", "link"} else "src"
            if attr in a:
                self.links.append(a[attr])
                if tag == "a" and self.row is not None:
                    self.row.append(a[attr])

    def handle_endtag(self, tag):
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message):
    raise AssertionError(message)


before = [digest(p) for p in GENERATED]
runpy.run_path(str(OUT / "build.py"))["build"]()
after = [digest(p) for p in GENERATED]
assert before == after, "non-deterministic consolidated build"

cost_doc = json.loads((OUT / "costs.json").read_text(encoding="utf-8"))
rows = cost_doc["rows"]
assert len(rows) == 40
assert [r["target_usd"] for r in rows] == TARGETS
assert cost_doc["boc_observation"]["cny_per_usd_ask"] == float(RATE)
assert cost_doc["boc_observation"]["usd100_ask_cny"] == 669.03
for i, row in enumerate(rows):
    amount = Decimal(row["target_usd"])
    principal = RATE * amount
    boc = min(Decimal(260), max(Decimal(50), principal * Decimal("0.001"))) + 150
    hsbc = min(Decimal(500), max(Decimal(100), principal * Decimal("0.001"))) + 120
    q = lambda x: x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    assert row["cny_scenario"] == float(q(principal)), i
    assert row["boc_sender_cny"] == float(q(boc)), i
    assert row["hsbc_sender_cny"] == float(q(hsbc)), i
    assert row["boc_sender_usd_comparison"] == float(q(boc / RATE)), i
    assert row["hsbc_sender_usd_comparison"] == float(q(hsbc / RATE)), i
    assert row["sources"] == ["S14", "S16", "S18"]
    for field in ("fx_cost_usd", "downstream_usd", "documentation_usd", "tax_usd", "all_in_usd"):
        assert row[field] is None, (i, field)

# Endpoint values are explicit regression tests against the published formulas.
assert rows[0]["boc_sender_cny"] == 216.90
assert rows[0]["hsbc_sender_cny"] == 220.00
assert rows[-1]["boc_sender_cny"] == 410.00
assert rows[-1]["hsbc_sender_cny"] == 620.00

# External hosts seen in consolidated rows. Every one is a government source or
# the first-party provider for the product/tariff being described.
allowed = {
    "www.gov.cn", "www.safe.gov.cn", "m.safe.gov.cn", "www.pbc.gov.cn",
    "guangdong.chinatax.gov.cn", "shanghai.chinatax.gov.cn", "www.chinatax.gov.cn", "tianjin.chinatax.gov.cn",
    "www.irs.gov", "www.govinfo.gov", "www.supremecourt.gov", "www.cbp.gov",
    "pic.bankofchina.com", "www.bankofchina.com", "www.boc.cn", "www.hsbc.com.cn", "wise.com",
    "www.westernunion.com", "www.moneygram.com", "www.paypal.com",
    "www.icbcasia.com", "www.gdhmo.gov.cn",
}

parsers = {}
row_count = 0
for path in PAGES:
    text = path.read_text(encoding="utf-8")
    parser = Page()
    parser.feed(text)
    parsers[path] = parser
    assert parser.viewport, f"missing viewport: {path}"
    assert "<table" not in text or parser.mobile_labels > 0, f"missing mobile data labels: {path}"
    assert "<script" not in text
    for row in parser.rows:
        if not row:
            continue  # header
        row_count += 1
        assert any(urlsplit(h).scheme == "https" and urlsplit(h).netloc in allowed for h in row), (path, row)
    for href in parser.links:
        u = urlsplit(href)
        if u.scheme:
            assert u.scheme == "https" and u.netloc in allowed, (path, href)
        elif href.startswith(("#", "mailto:", "tel:")):
            if href.startswith("#"):
                assert href[1:] in parser.ids, (path, href)
        else:
            dest = (path.parent / unquote(u.path)).resolve()
            assert dest.is_relative_to(ROOT) and dest.exists(), (path, href)
            if u.fragment and dest.suffix == ".html":
                target_text = dest.read_text(encoding="utf-8")
                assert f'id="{u.fragment}"' in target_text, (path, href)

cost_html = (OUT / "costs.html").read_text(encoding="utf-8")
assert cost_html.count('data-label="USD target"') == 40
assert cost_html.count('aria-label="Blank, FX, downstream, documents and tax unknown"') == 40
methods_html = (OUT / "methods.html").read_text(encoding="utf-8")
assert methods_html.count('data-label="Candidate"') == 43
for mid in [f"P{i:02d}" for i in range(1, 10)] + [f"R{i:02d}" for i in range(1, 14)] + [f"B{i:02d}" for i in range(1, 9)] + [f"A{i:02d}" for i in range(1, 6)] + [f"X{i:02d}" for i in range(1, 9)]:
    assert f"method-{mid}.html" in methods_html, mid
root = (ROOT / "index.html").read_text(encoding="utf-8")
for required in ("edition-h/site/index.html", "edition-g/docs/index.html", "edition-f/site/index.html", "edition-e/site/index.html", "edition-d/docs/index.html", "edition-c/docs/index.html", "edition-b/index.html", "dossier/index.html", "docs/index.html", "overview.html", "pages/estimates.html", "COORDINATION.md"):
    assert required in root, required
assert "under 1% at every size" not in root
assert "CNY 200–410</td>" not in root

# Whole-repository local file crawl: no archived page is silently broken by integration.
html_files = sorted(ROOT.rglob("*.html"))
local_references = 0
for path in html_files:
    parser = Page()
    parser.feed(path.read_text(encoding="utf-8"))
    for href in parser.links:
        u = urlsplit(href)
        if u.scheme or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
            continue
        if not u.path:
            continue
        dest = (path.parent / unquote(u.path)).resolve()
        if dest.is_dir():
            dest = dest / "index.html"
        assert dest.is_relative_to(ROOT) and dest.exists(), (path.relative_to(ROOT), href)
        local_references += 1

# Root executive summary and requirements must not reintroduce superseded claims.
summary = (ROOT / "EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
requirements = (ROOT / "REQUIREMENTS.md").read_text(encoding="utf-8")
assert "staged: 50%" not in summary
assert "real conversion cost is about 0.42%" not in summary
assert "per year**. | 31 U.S.C." not in summary
assert "Final integration" in requirements

print(f"PASS: {len(PAGES)} consolidated pages; {row_count} sourced table rows; 40 exact targets; 160 independently recomputed fee values; 43 method links; {len(html_files)} HTML files / {local_references} local file references; deterministic rebuild. Personal eligibility, external uptime and all-in totals are not certified.")
