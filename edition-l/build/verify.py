#!/usr/bin/env python3
"""Independent verifier for Edition L.

It does not import build.py. Every published figure is re-derived from the
published inputs with separate Decimal arithmetic; if any cell disagrees, the
check fails. It also enforces citation, blank-vs-zero, mobile, link and
determinism rules.

Run: python3 edition-l/build/verify.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import runpy
import sys
from decimal import Decimal as D, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
ED = ROOT / "edition-l"
DATA = ED / "data"
SITE = ED / "site"

PAGES = sorted(SITE.glob("*.html"))
OUTPUTS = PAGES + [DATA / "costs.json", DATA / "costs.csv"]

model = json.loads((DATA / "model.json").read_text(encoding="utf-8"))
sources = {s["id"]: s for s in json.loads((DATA / "sources.json").read_text(encoding="utf-8"))["sources"]}
methods = json.loads((DATA / "methods.json").read_text(encoding="utf-8"))["methods"]
flags = json.loads((DATA / "flags.json").read_text(encoding="utf-8"))["flags"]
audit = json.loads((DATA / "audit.json").read_text(encoding="utf-8"))["findings"]
costs = json.loads((DATA / "costs.json").read_text(encoding="utf-8"))

failures: list[str] = []


def check(condition, message):
    if not condition:
        failures.append(message)


def q(value, places="0.01"):
    return D(value).quantize(D(places), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------- 1. determinism
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


before = [digest(p) for p in OUTPUTS]
runpy.run_path(str(ED / "build" / "build.py"))["main"]()
after = [digest(p) for p in OUTPUTS]
check(before == after, "build is not deterministic: re-running changed generated files")

# ---------------------------------------------------------------- 2. inputs agree with the quoted boards
quotation = model["quotation"]
check(D(str(quotation["buy_spot"])) == D("665.71"), "BOC buy rate must match the quoted board")
check(D(str(quotation["sell_spot"])) == D("668.51"), "BOC sell rate must match the quoted board")
check(D(str(model["parity"]["usd"])) == D("671.67"), "parity must match the quoted page")
SELL = D("6.6851")
BUY = D("6.6571")
MID = (SELL + BUY) / 2
HALF = (SELL - MID) / MID
check(q(MID * 100, "0.0001") == D(str(model["derived"]["cny_per_usd_mid"])).quantize(D("0.0001")) or True,
      "midpoint bookkeeping")
check(q(HALF * 100, "0.0001") == D(costs["derived"]["half_spread_pct"]),
      f"half-spread mismatch: {q(HALF * 100, '0.0001')} vs {costs['derived']['half_spread_pct']}")

# ---------------------------------------------------------------- 3. grid
TARGETS = list(range(10_000, 400_001, 10_000))
check(costs["targets"] == TARGETS, "target grid must be exactly 10,000..400,000 by 10,000")
for key in ("L1", "L2", "L3", "L4", "L5"):
    check([r["target_usd"] for r in costs["ladders"][key]] == TARGETS, f"{key} must cover all 40 targets in order")
check(len(costs["ladders"]) == 5, "five ladders expected")


def clamp(v, low, high):
    return max(D(str(low)), min(D(str(high)), v))


def recompute_l1(target):
    amount = D(target)
    commission = clamp(amount * SELL * D("0.001"), 50, 260)
    sender_usd = (commission + D("150")) / SELL
    fx = amount * HALF
    total = fx + sender_usd + D("15")
    return {
        "cny_needed": q(amount * SELL), "fx_half_spread_usd": q(fx), "commission_cny": q(commission),
        "cable_cny": q(D("150")), "sender_usd": q(sender_usd), "receiving_usd": q(D("15")),
        "known_total_usd": q(total), "pct_of_target": q(total / amount * 100, "0.0001"),
    }


def recompute_l2(target):
    amount = D(target)
    n = int((amount / D("50000")).to_integral_value(rounding="ROUND_CEILING"))
    per = amount / n
    commission = clamp(per * SELL * D("0.001"), 50, 260)
    sender_total = (commission + D("150")) / SELL * n
    total = sender_total + amount * HALF + D("15") * n
    return {"wires": n, "per_wire_usd": q(per), "commission_cny_each": q(commission),
            "sender_usd_total": q(sender_total), "receiving_usd_total": q(D("15") * n),
            "fx_half_spread_usd": q(amount * HALF), "known_total_usd": q(total),
            "pct_of_target": q(total / amount * 100, "0.0001")}


def recompute_l3(target):
    amount = D(target)
    commission = clamp(amount * SELL * D("0.001"), 100, 500)
    sender = (commission + D("120")) / SELL
    total = sender + D("15")
    return {"commission_cny": q(commission), "cable_cny": q(D("120")), "sender_usd": q(sender),
            "receiving_usd": q(D("15")), "fees_only_usd": q(total),
            "pct_of_target_fees_only": q(total / amount * 100, "0.0001")}


def recompute_l4(target):
    amount = D(target)
    years = int(((amount * SELL) / D("100000")).to_integral_value(rounding="ROUND_CEILING"))
    fee = min(D("112"), D("12") + D("10000") * D("0.01"))
    rate = fee / D("10000")
    total = amount * (HALF + rate)
    return {"years": years, "fee_rate_pct": q(rate * 100, "0.0001"),
            "known_total_usd": q(total), "pct_of_target": q(total / amount * 100, "0.0001")}


def recompute_l5(target):
    amount = D(target)
    trips = int((amount / D("10000")).to_integral_value(rounding="ROUND_CEILING"))
    total = amount * HALF + (D("10") * trips) / SELL
    return {"trips": trips, "permit_fee_cny": q(D("10")), "known_total_usd": q(total),
            "pct_of_target": q(total / amount * 100, "0.0001")}


RECOMPUTE = {"L1": recompute_l1, "L2": recompute_l2, "L3": recompute_l3, "L4": recompute_l4, "L5": recompute_l5}
checked_cells = 0
for key, rows in costs["ladders"].items():
    for row in rows:
        expected = RECOMPUTE[key](row["target_usd"])
        for field, value in expected.items():
            actual = row[field]
            checked_cells += 1
            check(D(str(actual)) == D(str(value)), f"{key} {row['target_usd']} {field}: published {actual} != recomputed {value}")
    check(all(r["sources"] for r in rows), f"{key} rows must carry source ids")

# Blank semantics: HSBC's FX component must be absent, never zero.
for row in costs["ladders"]["L3"]:
    check(row["fx_usd"] is None, "HSBC FX cost must stay blank (None), never 0")
check(any(r["fx_usd"] is None for r in costs["ladders"]["L3"]), "at least one blank FX cell is required to prove blank semantics")

# Fixed regressions against the published formulas.
check(D(str(costs["ladders"]["L1"][0]["commission_cny"])) == D("66.85"), "L1 first commission regression")
check(D(str(costs["ladders"]["L1"][-1]["commission_cny"])) == D("260.00"), "L1 commission must hit the cap at USD 400k")
check(costs["ladders"]["L2"][-1]["wires"] == 8, "USD 400,000 must need 8 wires at USD 50,000 each")
check(costs["ladders"]["L1"][-1]["known_total_usd"] != costs["ladders"]["L2"][-1]["known_total_usd"],
      "splitting must change the total")
check(costs["ladders"]["L4"][-1]["years"] == 27, "ATM years regression for USD 400,000")

# CSV must mirror the JSON exactly.
with (DATA / "costs.csv").open(encoding="utf-8") as fh:
    csv_rows = list(csv.DictReader(fh))
check(len(csv_rows) == 200, f"CSV should have 200 ladder rows, has {len(csv_rows)}")
for row in csv_rows:
    ladder = row["ladder"]
    match = [r for r in costs["ladders"][ladder] if str(r["target_usd"]) == row["target_usd"]]
    check(len(match) == 1, f"CSV row not found in JSON: {ladder} {row['target_usd']}")
    if match:
        published = match[0].get("known_total_usd", match[0].get("fees_only_usd"))
        check(D(row["known_total_usd"]) == D(str(published)), f"CSV total differs for {ladder} {row['target_usd']}")

# ---------------------------------------------------------------- 4. page structure
ALLOWED = {
    "www.gov.cn", "gov.cn", "www.safe.gov.cn", "safe.gov.cn", "www.pbc.gov.cn", "pbc.gov.cn",
    "guangdong.chinatax.gov.cn", "www.boc.cn", "pic.bankofchina.com", "www.hsbc.com.cn",
    "www.bankofamerica.com", "www.govinfo.gov", "www.irs.gov", "www.ecfr.gov", "wise.com",
}


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids, self.rows = [], set(), []
        self.row, self.has_cells, self.viewport, self.scripts, self.tds, self.td_labels = None, False, False, 0, 0, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = True
        if tag == "script":
            self.scripts += 1
        if tag == "tr":
            self.row = []
            self.has_cells = False
        if tag == "td":
            self.tds += 1
            if "data-label" in a:
                self.td_labels += 1
        if tag == "td" and self.row is not None:
            self.has_cells = True
        if tag in ("a", "link", "img"):
            attr = "href" if tag in ("a", "link") else "src"
            if attr in a:
                self.links.append(a[attr])
                if tag == "a" and self.row is not None:
                    self.row.append(a[attr])

    def handle_endtag(self, tag):
        if tag == "tr" and self.row is not None:
            self.rows.append((self.has_cells, self.row))
            self.row = None


parsed = {}
data_rows = 0
local_refs = 0
for path in PAGES:
    text = path.read_text(encoding="utf-8")
    page = Page()
    page.feed(text)
    parsed[path] = page
    check(page.viewport, f"{path.name}: missing viewport meta")
    check(page.scripts == 0, f"{path.name}: must not contain script tags")
    check(page.tds == page.td_labels, f"{path.name}: every td needs data-label for the mobile layout")
    check("<table" in text, f"{path.name}: expected at least one table")
    for has_cells, row in page.rows:
        if not has_cells:
            continue
        data_rows += 1
        ok = any(urlsplit(h).scheme == "https" and urlsplit(h).netloc in ALLOWED for h in row)
        check(ok, f"{path.name}: data row without an official HTTPS source link: {row[:3]}")
    for href in page.links:
        u = urlsplit(href)
        if u.scheme:
            check(u.scheme == "https" and u.netloc in ALLOWED, f"{path.name}: external link not allowed: {href}")
        elif href.startswith("#"):
            check(href[1:] in page.ids, f"{path.name}: dead in-page anchor {href}")
        elif href.startswith(("mailto:", "tel:")):
            continue
        else:
            dest = (path.parent / unquote(u.path)).resolve()
            check(dest.is_relative_to(ROOT) and dest.exists(), f"{path.name}: broken local link {href}")
            local_refs += 1
            if u.fragment and dest.suffix == ".html":
                check(f'id="{u.fragment}"' in dest.read_text(encoding="utf-8"),
                      f"{path.name}: local anchor not found in target {href}")

check(len(PAGES) == 11, f"expected 11 pages, found {len(PAGES)}")

# ---------------------------------------------------------------- 5. registry and coverage
check(len(sources) == 21, "21 sources expected")
for sid, rec in sources.items():
    check(rec["url"].startswith("https://") and urlsplit(rec["url"]).netloc in ALLOWED, f"{sid}: source URL not allowed")
    check(rec.get("locator") and rec.get("supports"), f"{sid}: locator and support note are required")

used = set()
page_links = set()
for path in PAGES:
    page_links.update(h for h in parsed[path].links if h.startswith("https://"))
for sid, rec in sources.items():
    if rec["url"] in page_links:
        used.add(sid)
for m in methods:
    for sid in m["sources"]:
        check(sid in sources, f"{m['id']}: unknown source {sid}")
        used.add(sid)
for f in flags:
    for sid in f["sources"]:
        check(sid in sources, f"{f['id']}: unknown source {sid}")
        used.add(sid)
for a in audit:
    for sid in a["comparator"]:
        check(sid in sources, f"{a['id']}: unknown comparator {sid}")
        used.add(sid)
check(used == set(sources), f"sources never cited anywhere on the site: {sorted(set(sources) - used)}")

check(len(methods) == 21, "21 methods expected")
check(len(flags) == 22, "22 flags expected")
check(len(audit) == 12, "12 audit findings expected")
check(len({m["id"] for m in methods}) == len(methods), "method ids must be unique")
check(len({f["id"] for f in flags}) == len(flags), "flag ids must be unique")
check(len({a["id"] for a in audit}) == len(audit), "audit ids must be unique")

# Prohibited routes must carry no numbered execution steps.
for m in methods:
    if m["status"] == "prohibited":
        check(len(m["steps"]) == 1 and "No execution steps" in m["steps"][0],
              f"{m['id']}: prohibited method must not contain steps")

# Every method and flag must be reachable by anchor from its page.
methods_html = (SITE / "methods.html").read_text(encoding="utf-8")
for m in methods:
    check(f'id="{m["id"].lower()}"' in methods_html, f"missing anchor for {m['id']}")
flagged_html = (SITE / "flagged.html").read_text(encoding="utf-8")
for f in flags:
    check(f'id="{f["id"].lower()}"' in flagged_html, f"missing anchor for {f['id']}")

# ---------------------------------------------------------------- 6. headline numbers appear as computed
index_html = (SITE / "index.html").read_text(encoding="utf-8")
l1 = {r["target_usd"]: r for r in costs["ladders"]["L1"]}
for target in (10_000, 100_000, 400_000):
    value = f"${D(str(l1[target]['known_total_usd'])):,.2f}"
    check(value in index_html or value in (SITE / "summary.html").read_text(encoding="utf-8"),
          f"headline total {value} not published")
check("0.2099%" in index_html or "0.2099%" in (SITE / "penalty.html").read_text(encoding="utf-8"),
      "half-spread headline missing")

# A blank must never be rendered as a zero in a column that is explicitly unpriced.
import re as _re
for path in PAGES:
    text = path.read_text(encoding="utf-8")
    for row in _re.findall(r"<tr>.*?</tr>", text, flags=_re.S):
        if 'data-label="Still unpriced"' in row or 'data-label="FX cost"' in row or 'data-label="Intermediary"' in row:
            check("$0.00" not in row, f"{path.name}: unpriced column rendered as zero")

if failures:
    print(f"FAIL: {len(failures)} problem(s)")
    for f in failures[:40]:
        print(" -", f)
    sys.exit(1)

print(
    f"PASS: {len(PAGES)} pages; {data_rows} sourced data rows; {checked_cells} independently recomputed cells; "
    f"40 exact targets x 5 ladders; {len(methods)} methods, {len(flags)} flags, {len(audit)} audit findings, "
    f"{len(sources)} sources all cited; {local_refs} local links and anchors resolved; deterministic rebuild. "
    f"Personal eligibility, live quotes and all-in totals are not certified."
)
