#!/usr/bin/env python3
"""Independent verifier for Edition I.

It does not trust build.py's output: it recomputes every cost row from the
published board and tariff, re-parses the rendered HTML, and fails on any
mismatch, missing source, undisclosed blank, broken link or hand-typed claim.

Usage: python3 edition-i/build/verify.py
Exit code 0 = pass.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ED = Path(__file__).resolve().parents[1]
ROOT = ED.parent
DATA = ED / "data"
SITE = ED / "site"

ERRORS: list[str] = []
CHECKS = 0


def check(cond: bool, msg: str):
    global CHECKS
    CHECKS += 1
    if not cond:
        ERRORS.append(msg)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


sources_doc = load("sources.json")
sources = {s["id"]: s for s in sources_doc["sources"]}
routes_doc = load("routes.json")
routes = routes_doc["routes"]
penalty = load("penalty.json")
taxes = load("taxes.json")
flags = load("flags.json")["flags"]

AMOUNTS = list(range(10_000, 400_001, 10_000))
FX = 6.6903
FX_BUY = 6.6622
MID = (FX + FX_BUY) / 2
CABLE = 150.0
CMIN, CMAX = 50.0, 260.0
MODELS = {"boc_fx_wire", "boc_wire_only", "boc_cash", "none_published", "prohibited", "hold",
          "card", "atm", "provider"}

# ---------------------------------------------------------------- source checks
check(len(sources) >= 25, f"expected at least 25 sources, found {len(sources)}")
check(len(sources) == len(sources_doc["sources"]), "duplicate source IDs")
for sid, s in sources.items():
    for f in ("publisher", "title", "url", "type", "retrieved", "scope"):
        check(bool(s.get(f)), f"{sid}: missing {f}")
    check(s["url"].startswith("http"), f"{sid}: url is not absolute")
    check(s["type"] in ("government", "provider"), f"{sid}: bad type")
    check(bool(s.get("quote")), f"{sid}: no verbatim quote recorded")
    check(bool(re.match(r"^\d{4}-\d{2}-\d{2}$", s["retrieved"])), f"{sid}: bad retrieval date")

# ---------------------------------------------------------------- route checks
check(len(routes) == routes_doc["_meta"]["route_count"], "route count does not match declared meta")
check(len(routes) >= 28, f"only {len(routes)} routes")
check(len({r['id'] for r in routes}) == len(routes), "duplicate route IDs")
CATS = {"personal", "capital", "rail", "card", "hold", "prohibited"}
STATUSES = {"candidate", "conditional", "limited", "prohibited", "unverified"}
for r in routes:
    check(r["category"] in CATS, f"{r['id']}: bad category {r['category']}")
    check(r["status"] in STATUSES, f"{r['id']}: bad status")
    check(len(r["sources"]) >= 1, f"{r['id']}: no source")
    for sid in r["sources"]:
        check(sid in sources, f"{r['id']}: unknown source {sid}")
    check(bool(r["one_line"]), f"{r['id']}: no summary")
    check(bool(r["who"]), f"{r['id']}: no eligibility statement")
    check(r["cost_model"] in MODELS, f"{r['id']}: unknown cost model {r['cost_model']}")
    if r["status"] == "prohibited":
        check(r["steps"] == [], f"{r['id']}: prohibited route must not contain steps")
        check(not r["pros"], f"{r['id']}: prohibited route must not list pros")
    elif r["status"] in ("candidate", "conditional", "limited"):
        check(len(r["steps"]) >= 2, f"{r['id']}: fewer than two steps")
    if r.get("cap_step_usd") is not None:
        check(isinstance(r["cap_step_usd"], (int, float)) and r["cap_step_usd"] > 0,
              f"{r['id']}: bad cap")

# ------------------------------------------------------------ FX data coherence
fx = penalty["_meta"]["fx"]
check(abs(fx["mid_cny_per_usd"] - (fx["usd_spot_buy_cny_per_100"] / 100 + fx["usd_spot_sell_cny_per_100"] / 100) / 2) < 1e-6,
      "penalty fx midpoint does not equal the board buy/sell midpoint")
check(abs(fx["one_way_margin_pct"] - (fx["sell_cny_per_usd"] - fx["mid_cny_per_usd"]) / fx["mid_cny_per_usd"] * 100) < 1e-4,
      "penalty one-way margin is inconsistent with the board")
check(abs(fx["sell_cny_per_usd"] - fx["usd_spot_sell_cny_per_100"] / 100) < 1e-9,
      "penalty sell rate does not match the board")
check(abs(fx["central_parity_cny_per_usd"] - 6.7188) < 1e-9, "central parity not 6.7188")


def compute(route, target):
    m = route["cost_model"]
    if m in ("none_published", "prohibited", "card", "atm", "provider"):
        return None
    if m == "hold":
        return (0.0, 0.0, 0.0, 0.0)
    fx_m = target * (FX - MID) / MID
    if m == "boc_wire_only":
        comm = max(CMIN, min(CMAX, 0.001 * target * FX)) / FX
        cable = CABLE / FX
    elif m == "boc_cash":
        comm, cable = 0.0, 0.0
    else:
        comm = max(CMIN, min(CMAX, 0.001 * target * FX)) / FX
        cable = CABLE / FX
    return (fx_m, comm, cable, fx_m + comm + cable)


# ------------------------------------------------------- rendered page checking
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.refs = [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "a" and "href" in a:
            self.refs.append(a["href"])


ROW_RX = re.compile(
    r'<td class="num" data-label="Target">\$([\d,]+)</td>'
    r'<td class="num( blank)?" data-label="FX margin">([^<]+)</td>'
    r'<td class="num( blank)?" data-label="Commission">([^<]+)</td>'
    r'<td class="num( blank)?" data-label="Cable">([^<]+)</td>'
    r'<td class="num blank" data-label="Receiver">([^<]+)</td>'
    r'<td class="num( blank)?" data-label="Sender total">(?:<strong>)?([^<]+)')

pages = sorted(p for p in SITE.glob("*.html"))
check(len(pages) >= 12, f"expected at least 12 pages, found {len(pages)}")
all_ids = {}
all_refs = {}
for p in pages:
    html = p.read_text(encoding="utf-8")
    check(html.startswith("<!doctype html>"), f"{p.name}: missing doctype")
    check('name="viewport"' in html, f"{p.name}: missing viewport meta")
    check("<title>" in html, f"{p.name}: missing title")
    check('<main id="main">' in html, f"{p.name}: missing main landmark")
    check("aria-current=\"page\"" in html or p.name == "index.html", f"{p.name}: no current nav item")
    check("<footer>" in html, f"{p.name}: missing footer")
    check("guaranteed return" not in html.lower() and "guaranteed approval" not in html.lower(),
          f"{p.name}: forbidden guarantee claim")
    check("tax-free" not in html.lower(), f"{p.name}: forbidden claim 'tax-free'")
    check("$0 tax" not in html.lower(), f"{p.name}: forbidden claim '$0 tax'")
    parser = Links()
    parser.feed(html)
    all_ids[p.name] = parser.ids
    all_refs[p.name] = parser.refs

# internal links inside the generated site
missing = []
bad_anchor = []
for name, refs in all_refs.items():
    for link in refs:
        u = urlparse(link)
        if u.scheme in ("http", "https", "mailto", "tel"):
            continue
        if not link.strip():
            continue
        target = SITE / unquote(u.path) if u.path else SITE / name
        if not target.exists():
            missing.append(f"{name} -> {link}")
        elif u.fragment and u.fragment not in all_ids.get(target.name, []):
            bad_anchor.append(f"{name} -> {link}")
check(not missing, "broken internal links: " + "; ".join(missing[:6]))
check(not bad_anchor, "unresolved fragments: " + "; ".join(bad_anchor[:6]))

# every route page exists and carries 40 rows
for r in routes:
    page = SITE / f"method-{r['id']}.html"
    check(page.exists(), f"missing page for {r['id']}")
    if not page.exists():
        continue
    html = page.read_text(encoding="utf-8")
    check(r["name"] in html or r["name"].replace("&", "&amp;") in html, f"{r['id']}: name not rendered")
    targets = [int(x.replace(",", "")) for x in re.findall(r'data-label="Target">\$([\d,]+)<', html)]
    check(targets == AMOUNTS, f"{r['id']}: target ladder is not exactly 10k..400k by 10k")
    for sid in r["sources"]:
        check(sources[sid]["url"] in html, f"{r['id']}: source {sid} link missing")
    check(html.count('<td class="num blank" data-label="Receiver">UNVERIFIED') == 40,
          f"{r['id']}: receiver column is not blank in all 40 rows")
    rows = ROW_RX.findall(html)
    check(len(rows) == 40, f"{r['id']}: expected 40 parsed cost rows, found {len(rows)}")
    if len(rows) == 40:
        for row, amount in zip(rows, AMOUNTS):
            target = int(row[0].replace(",", ""))
            check(target == amount, f"{r['id']}: row order mismatch at {amount}")
            exp = compute(r, amount)
            if exp is None:
                check(row[2] == "UNVERIFIED" and row[9] == "UNVERIFIED",
                      f"{r['id']} at {amount}: unpublished model must be blank, got {row[2]}/{row[9]}")
                check(row[1] == " blank", f"{r['id']} at {amount}: blank cell missing its class")
            else:
                got_fx = float(row[2].replace("$", "").replace(",", ""))
                got_comm = float(row[4].replace("$", "").replace(",", ""))
                got_cable = float(row[6].replace("$", "").replace(",", ""))
                got_total = float(row[9].replace("$", "").replace(",", ""))
                check(abs(got_fx - exp[0]) < 0.011, f"{r['id']} at {amount}: fx {got_fx} != {exp[0]:.4f}")
                check(abs(got_comm - exp[1]) < 0.011, f"{r['id']} at {amount}: comm {got_comm} != {exp[1]:.4f}")
                check(abs(got_cable - exp[2]) < 0.011, f"{r['id']} at {amount}: cable {got_cable} != {exp[2]:.4f}")
                check(abs(got_total - exp[3]) < 0.011, f"{r['id']} at {amount}: total {got_total} != {exp[3]:.4f}")
                check(row[7].strip() == "UNVERIFIED",
                      f"{r['id']} at {amount}: receiver fee must stay blank")
    if r["status"] == "prohibited":
        check("<ol class=\"steps\">" not in html, f"{r['id']}: prohibited route rendered steps")
        check("No execution steps are provided" in html, f"{r['id']}: missing no-steps notice")

# costs page checks
costs_html = (SITE / "costs.html").read_text(encoding="utf-8")
check(costs_html.count('data-label="Target"') == 40, "costs.html: ladder is not 40 rows")
check(costs_html.count('data-label="China tax"') == 40, "costs.html: tax column missing or unlabelled")
for a in AMOUNTS:
    check(f"${a:,}" in costs_html, f"costs.html: missing target ${a:,}")
matrix_rows = costs_html.count('data-label="Route"')
check(matrix_rows == len(routes), f"costs.html: route matrix has {matrix_rows} rows, expected {len(routes)}")
for r in routes:
    check(f'method-{r["id"]}.html' in costs_html, f"costs.html: no link to {r['id']}")

# routes page lists everything
routes_html = (SITE / "routes.html").read_text(encoding="utf-8")
for r in routes:
    check(f'method-{r["id"]}.html' in routes_html, f"routes.html: missing {r['id']}")

# sources page renders every URL and quote
src_html = (SITE / "sources.html").read_text(encoding="utf-8")
for sid, s in sources.items():
    check(s["url"] in src_html, f"sources.html: missing URL for {sid}")
    check(sid in src_html, f"sources.html: missing row for {sid}")

# flags page renders every flag and every source link
rev_html = (SITE / "review.html").read_text(encoding="utf-8")
for f in flags:
    check(f["id"] in rev_html, f"review.html: missing flag {f['id']}")
    for sid in f["sources"]:
        check(sources[sid]["url"] in rev_html, f"review.html: missing link {sid} for {f['id']}")
check(len(flags) >= 15, f"expected at least 15 flags, found {len(flags)}")

# tax page: unverified rows stay blank-labelled
tax_html = (SITE / "taxes.html").read_text(encoding="utf-8")
for t in taxes["rows"]:
    check(t["topic"] in tax_html or t["topic"].replace("&", "&amp;") in tax_html,
          f"taxes.html: missing {t['id']}")
    if t["status"] == "unverified":
        check("UNVERIFIED" in tax_html, "taxes.html: no unverified marker")

# ---------------------------------------------------------------- CSV checks
with (SITE / "cost-ladder.csv").open(encoding="utf-8") as fh:
    rows = list(csv.reader(fh))
check(rows[0][0] == "route_id" and len(rows[0]) == 9, "CSV header wrong")
data_rows = rows[1:]
check(len(data_rows) == len(routes) * 40, f"CSV has {len(data_rows)} rows, expected {len(routes)*40}")
per_route = {}
for row in data_rows:
    per_route[row[0]] = per_route.get(row[0], 0) + 1
for r in routes:
    check(per_route.get(r["id"]) == 40, f"CSV: {r['id']} has {per_route.get(r['id'])} rows")

# ------------------------------------------------ every source is actually used
used = set()
for r in routes:
    used.update(r["sources"])
for f in flags:
    used.update(f["sources"])
for ln in penalty["lines"]:
    used.update(ln["sources"])
for sc in penalty["scenarios"]:
    used.update(sc["sources"])
for t in taxes["rows"]:
    used.update(t["sources"])
for sid in sources:
    check(sid in used, f"source {sid} is registered but never cited")

# --------------------------------------------------------- determinism check
before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in SITE.iterdir() if p.is_file()}
subprocess.run([sys.executable, str(ED / "build" / "build.py")], check=True,
               stdout=subprocess.DEVNULL)
after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in SITE.iterdir() if p.is_file()}
check(before == after, "rebuild is not byte-identical")

result = {
    "edition": "I",
    "status": "PASS" if not ERRORS else "FAIL",
    "checks_passed": CHECKS,
    "errors": ERRORS[:25],
    "error_count": len(ERRORS),
    "counts": {
        "sources": len(sources),
        "routes": len(routes),
        "cost_rows": len(data_rows),
        "html_pages": len(pages),
        "flags": len(flags),
        "penalty_lines": len(penalty["lines"]),
        "scenarios": len(penalty["scenarios"]),
        "tax_rows": len(taxes["rows"]),
        "internal_links": sum(len(v) for v in all_refs.values()),
    },
    "target_grid": AMOUNTS[:3] + ["..."] + AMOUNTS[-1:],
}
print(json.dumps(result, indent=1))
sys.exit(0 if not ERRORS else 1)
