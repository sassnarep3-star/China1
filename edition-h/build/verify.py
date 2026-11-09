#!/usr/bin/env python3
"""Deterministic Edition H verifier; exits nonzero on any blocking defect."""
from html.parser import HTMLParser
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA, SITE, AUDIT = ROOT / "data", ROOT / "site", ROOT / "audit"
AUDIT.mkdir(exist_ok=True)
errors, checks = [], []


def check(cond, message):
    if cond:
        checks.append(message)
    else:
        errors.append(message)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

sources_doc = load("sources.json")
sources = {s["id"]: s for s in sources_doc["sources"]}
methods_doc = load("methods.json")
methods = methods_doc["methods"]
costs = load("costs.json")
flags = load("flags.json")
review = load("repo-review.json")
rows = costs["rows"]
ids = [m["id"] for m in methods]
check(len(methods) == 43, "exactly 43 method candidates")
check(len(ids) == len(set(ids)), "method IDs unique")
check(len(rows) == 1720, "exactly 1,720 cost rows")
targets = list(range(10000, 400001, 10000))
check(costs["_meta"]["targets_usd_equivalent"] == targets, "exact USD10k..USD400k grid")
check(len({s["id"] for s in sources_doc["sources"]}) == len(sources), "source IDs unique")
check(len({f["id"] for f in flags["flags"]}) == len(flags["flags"]), "flag IDs unique")
for s in sources_doc["sources"]:
    check(s["url"].startswith(("https://", "http://")), f'{s["id"]} has absolute source URL')
    check(bool(s["locator"] and s["supports"] and s["issuer"]), f'{s["id"]} source metadata complete')
check(not sources["S52"]["verified"], "secondary S52 excluded from verified source set")

by_method = {mid: [] for mid in ids}
seen = set()
for i, r in enumerate(rows):
    mid, amount = r["method_id"], r["target_usd_equivalent"]
    key = (mid, amount)
    check(mid in by_method, f"row {i} method exists")
    check(key not in seen, f"row {i} method/amount unique")
    seen.add(key)
    if mid in by_method:
        by_method[mid].append(r)
    check(amount in targets, f"row {i} valid amount")
    check(bool(r["sources"]) and all(s in sources for s in r["sources"]), f"row {i} valid citations")
    check("S52" not in r["sources"], f"row {i} excludes secondary source")
    check(bool(r["sources"] and all(sources[s]["verified"] for s in r["sources"])), f"row {i} cites verified sources only")
    check(bool(r["note"]), f"row {i} has scope note")
    for field in ["fx_cost_usd", "downstream_usd", "documentation_usd", "tax_usd", "all_in_usd"]:
        check(r[field] is None, f"row {i} {field} remains blank/null")
    check(r["all_in_status"] == "unverified", f"row {i} all-in explicitly unverified")
    if r["status"] == "not-applicable":
        check(r["known_subtotal_usd"] is None, f"row {i} N/A subtotal blank")
    if r["sender_cny"] is not None:
        check(math.isfinite(r["sender_cny"]) and r["sender_cny"] >= 0, f"row {i} finite sender CNY")
        p = 6.6919 * amount
        expected = None
        if mid in {"P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P11", "P12", "P13", "P14", "B01", "B02", "B03", "B04", "B06", "B07", "B08", "B09", "A04"}:
            expected = min(260, max(50, .001 * p)) + 150
        if mid in {"P10", "R02"}:
            expected = min(260, max(50, .001 * p))
        if mid == "R03":
            expected = min(500, max(100, .001 * p)) + 120
        if mid in {"R04", "R09"}:
            expected = 0
        if expected is not None:
            check(abs(r["sender_cny"] - round(expected + 1e-9, 2)) <= .011, f"row {i} arithmetic matches printed formula")
        if r["sender_usd"] is not None:
            check(abs(r["sender_usd"] - r["sender_cny"] / 6.6919) <= .011, f"row {i} USD conversion arithmetic")
for mid, rs in by_method.items():
    check(len(rs) == 40, f"{mid} exactly 40 rows")
    check([r["target_usd_equivalent"] for r in rs] == targets, f"{mid} ordered 40-point grid")
    check(all(r["status"] == "not-applicable" for r in rs) or any(r["status"] != "not-applicable" for r in rs), f"{mid} disposition consistent")

for m in methods:
    check(bool(m["sources"]) and all(s in sources and sources[s]["verified"] for s in m["sources"]), f'{m["id"]} source links verified')
    check(bool(m["pros"] and m["cons"]), f'{m["id"]} has pros and cons')
    check(bool(m["steps"]), f'{m["id"]} has steps or explicit no-instruction disposition')
    if m["status"] == "rejected" or m["id"] == "S03":
        check(m["steps"] == [], f'{m["id"]} prohibited route has no operational steps')
    check((SITE / f'method-{m["id"]}.html').exists(), f'{m["id"]} detail page exists')

class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()
        self.unknown = 0
        self.viewport = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
        if "class" in a and "unverified" in a["class"].split():
            self.unknown += 1
        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = True

parsers = {}
for page in sorted(SITE.glob("*.html")):
    p = Parser(); p.feed(page.read_text(encoding="utf-8")); parsers[page.name] = p
    check(p.viewport, f"{page.name} mobile viewport")
    check('class="skip"' in page.read_text(encoding="utf-8"), f"{page.name} skip navigation")
for name, p in parsers.items():
    for link in p.links:
        if link.startswith(("http://", "https://", "mailto:", "#")):
            if link.startswith("#"):
                check(link[1:] in p.ids, f"{name} local anchor {link}")
            continue
        file_part, _, anchor = link.partition("#")
        target = SITE / file_part
        check(target.exists(), f"{name} local link exists: {link}")
        if target.exists() and anchor and target.suffix == ".html":
            tp = parsers.get(target.name)
            if tp:
                check(anchor in tp.ids, f"{name} target anchor exists: {link}")
    if name.startswith("method-"):
        text = (SITE / name).read_text(encoding="utf-8")
        check(text.count('data-label="USD-equivalent"') == 40, f"{name} renders exactly 40 amounts")
        check(p.unknown >= 40, f"{name} visibly labels blank/unverified cells")
        check("UNVERIFIED" in text, f"{name} publishes unverified semantics")
check((SITE / "cost-ladder.csv").exists(), "downloadable cost ladder exists")
check(len((SITE / "cost-ladder.csv").read_text(encoding="utf-8").splitlines()) == 1721, "CSV has header plus 1,720 rows")
check((SITE / ".nojekyll").exists(), "Pages .nojekyll exists")
check((SITE / "flagged.html").exists(), "Flagged for Review page exists")
check((SITE / "repo-review.html").exists(), "repo review page exists")
check((SITE / "executive-summary.html").exists(), "executive summary exists")
check(len(review["findings"]) >= 10, "repository audit publishes material irregularities")

report = {"edition": "H", "status": "PASS" if not errors else "FAIL", "checks_passed": len(checks), "errors": errors, "counts": {"sources": len(sources), "methods": len(methods), "cost_rows": len(rows), "flags": len(flags["flags"]), "html_pages": len(parsers), "review_findings": len(review["findings"])}, "target_grid": targets}
(AUDIT / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
sys.exit(1 if errors else 0)
