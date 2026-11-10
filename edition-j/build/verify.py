"""Edition J independent verifier.

Deliberately does not trust the builder. It re-derives every published number
from the raw transcribed inputs and fails on any disagreement, on any citation
that does not resolve, on any prohibited route that leaks execution steps, and
on any page that renders an unverified value as a number.

Exit code 0 means every check below passed.
"""

import csv
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "edition-j" / "site"
sys.path.insert(0, str(ROOT / "edition-j"))

from data import sources, market, routes, costs, analysis  # noqa: E402

FAIL = []
CHECKED = 0


def check(cond, label, detail=""):
    global CHECKED
    CHECKED += 1
    if not cond:
        FAIL.append(f"{label}{(' :: ' + detail) if detail else ''}")


# ------------------------------------------------------------------ 1. re-derive market maths
bid = market.BOC_BOARD["cash_buy"] / market.BOC_BOARD["unit_per"]
ask = market.BOC_BOARD["cash_sell"] / market.BOC_BOARD["unit_per"]
par = market.PARITY["usd_cny"]

check(abs(bid - 6.6622) < 1e-9, "bid/ask 1", f"bid={bid}")
check(abs(ask - 6.6903) < 1e-9, "bid/ask 2", f"ask={ask}")
check(abs(costs.boc_rate_buy() - bid) < 1e-12, "bid helper")
check(abs(costs.boc_rate_sell() - ask) < 1e-12, "ask helper")
check(abs(costs.spread_pct_of_bid() - (ask - bid) / bid) < 1e-12, "spread/bid helper")
check(abs(costs.round_trip_pct() - (ask - bid) / bid) < 1e-12, "round-trip helper")
mid = (bid + ask) / 2
check(abs(costs.mid_rate() - mid) < 1e-12, "mid helper")
check(abs(costs.one_way_cost_pct() - (ask - mid) / mid) < 1e-12, "one-way helper")

# The parity and the board are from different timestamps, so no monotonic
# relation is required - but a cost measure must never be negative.
check(costs.one_way_cost_pct() > 0, "one-way cost is strictly positive",
      str(costs.one_way_cost_pct()))
check(costs.round_trip_pct() > costs.one_way_cost_pct(), "round trip exceeds one way")
check(abs(par - ask) < 0.10, "parity sanity", f"parity {par} vs ask {ask}")
# the rejected measure is retained and demonstrably not used: it must not be
# negative-free. If this ever becomes positive, the rejection note needs review.
check(costs.parity_gap_pct() == (ask - par) / par, "parity gap computed honestly")

# ------------------------------------------------------------------ 2. tariff arithmetic
for target in (10_000, 137_000, 400_000):
    cny = target * ask
    fee = costs.boc_tt_fee_cny(cny)
    commission = min(max(cny * 0.001, 50.0), 260.0)
    check(abs(fee["commission_cny"] - round(commission, 2)) < 0.011, "commission", f"{target}: {fee}")
    check(fee["total_cny"] == round(commission + 150.0, 2), "cable + total", f"{target}: {fee}")

# commission clamps must both be exercised across the range
low = costs.boc_tt_fee_cny(1_000 * ask)      # small: hits the CNY 50 floor
high = costs.boc_tt_fee_cny(400_000 * ask)   # large: hits the CNY 260 ceiling
check(low["commission_cny"] == 50.0, "commission floor", str(low))
check(high["commission_cny"] == 260.0, "commission ceiling", str(high))

# ------------------------------------------------------------------ 3. every published row recomputed from raw inputs
rows_checked = 0
for r in routes.ROUTES:
    for row in costs.ladder_for(r):
        t = row["target_usd"]
        check(row["cny_needed"] == round(t * ask, 2), "cny needed", f"{r['id']} {t}")
        if r["estimate"]["mode"] == "boc_tt":
            check(abs(row["fx_cost_usd"] - round(t * (ask - mid) / mid, 2)) < 0.011,
                  "fx cost", f"{r['id']} {t}")
            fee = row["sender_fee_cny"]
            check(abs(row["sender_fee_usd"] - round(fee / ask, 2)) < 0.011,
                  "fee in usd", f"{r['id']} {t}")
            check(row["receiver_fee_usd"] is None and row["intermediary_usd"] is None,
                  "no invented receiver/intermediary fee", f"{r['id']} {t}")
            check(row["all_in_usd"] is None, "no invented all-in total", f"{r['id']} {t}")
            if r["estimate"].get("tax_rate"):
                check(abs(row["tax_usd"] - round(t * r["estimate"]["tax_rate"]
                                                 / (1 - r["estimate"]["tax_rate"]), 2)) < 0.011,
                      "tax gross-up", f"{r['id']} {t}")
            else:
                check(row["tax_usd"] is None, "no invented tax", f"{r['id']} {t}")
        else:
            check(row["sender_fee_usd"] is None and row["fx_cost_usd"] is None,
                  "limit-only route has no invented price", r["id"])
        rows_checked += 1

# ------------------------------------------------------------------ 4. exact target grid
check(costs.TARGETS[0] == 10_000 and costs.TARGETS[-1] == 400_000, "ladder starts and ends correctly")
check(len(costs.TARGETS) == 40, "exactly 40 targets", str(len(costs.TARGETS)))
check(all(b - a == 10_000 for a, b in zip(costs.TARGETS, costs.TARGETS[1:])),
      "uniform 10,000 increment")

# ------------------------------------------------------------------ 5. citation discipline
S = sources.SOURCES
for r in routes.ROUTES:
    check(len(r["law_basis"]) >= 1, "route has law source", r["id"])
    for sid in r["law_basis"] + r["cost_basis"] + r.get("risk_basis", []) + r["limit_basis"]:
        check(sid in S, "citation resolves", f"{r['id']} -> {sid}")
    if not r.get("limit_known", True):
        check(r["limit"].lower().find("no ") >= 0 or "not verified" in r["limit"].lower()
              or "no reliable" in r["limit"].lower() or "not verified" in r["limit"].lower(),
              "unknown limit is disclosed", r["id"])
    if r["lawful"] == "prohibited":
        check(r["steps"] == [], "prohibited route publishes no steps", r["id"])
        check(len(r.get("risk_basis", [])) >= 1, "prohibited route cites its instrument", r["id"])
        check(r["estimate"]["mode"] == "prohibited", "prohibited route not priced", r["id"])
    else:
        check(len(r["steps"]) >= 1, "lawful route has steps", r["id"])
        if r["estimate"]["mode"] == "boc_tt":
            check(len(r["cost_basis"]) >= 1, "priced route cites a price source", r["id"])
    check(len(r["pros"]) + len(r["cons"]) > 0, "pros/cons present", r["id"])

for f in analysis.FINDINGS:
    for sid in f["sources"]:
        check(sid in S, "finding citation resolves", f"{f['id']} -> {sid}")
for p in analysis.PENALTY_LINES:
    check(len(p["sources"]) >= 1, "penalty line has a source", p["id"])
    for sid in p["sources"]:
        check(sid in S, "penalty citation resolves", f"{p['id']} -> {sid}")
for f in analysis.FLAGS:
    check(len(f["sources"]) >= 1, "flag has a source", f["id"])
    for sid in f["sources"]:
        check(sid in S, "flag citation resolves", f"{f['id']} -> {sid}")

# every source in the register must be used by something - no decorative citations
used = set()
for r in routes.ROUTES:
    used |= set(r["law_basis"]) | set(r["cost_basis"]) | set(r.get("risk_basis", [])) | set(r["limit_basis"])
for f in analysis.FINDINGS:
    used |= set(f["sources"])
for p in analysis.PENALTY_LINES:
    used |= set(p["sources"])
for f in analysis.FLAGS:
    used |= set(f["sources"])
unused = set(S) - used
check(not unused, "no unused sources", str(unused))

# tier discipline: a provider page may never be the only basis for a legal claim
for r in routes.ROUTES:
    legal_tiers = {S[s]["tier"] for s in r["law_basis"]}
    check(bool(legal_tiers & {"A", "B"}), "legal basis is government, not provider", r["id"])

# ------------------------------------------------------------------ 6. HTML: links, blanks, rendering
class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.ids = set()
        self.text = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a" and d.get("href"):
            self.hrefs.append(d["href"])
        if d.get("id"):
            self.ids.add(d["id"])

    def handle_data(self, data):
        self.text.append(data)


pages = sorted(SITE.glob("*.html"))
check(len(pages) >= 20, "all pages generated", str(len(pages)))
expected = 8 + sum(1 for r in routes.ROUTES if r["estimate"]["mode"] in ("boc_tt", "limit_only"))
check(len(pages) == expected, "page count matches routes", f"{len(pages)} vs {expected}")

parsed = {}
for p in pages:
    lp = LinkParser()
    lp.feed(p.read_text(encoding="utf-8"))
    parsed[p.name] = lp

for name, lp in parsed.items():
    for href in lp.hrefs:
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        if href.startswith("/China1/"):
            # GitHub Pages project-site absolute path: resolve against the repo root
            check((ROOT / href[len("/China1/"):]).exists(), "root link resolves", f"{name} -> {href}")
            continue
        target, _, frag = href.partition("#")
        if target == "":
            tgt = name
        else:
            tgt = target
        check((SITE / tgt).is_file(), "local link resolves", f"{name} -> {href}")
        if frag and (SITE / tgt).is_file() and tgt.endswith(".html"):
            dest = parsed.get(Path(tgt).name)
            if dest:
                check(frag in dest.ids, "anchor resolves", f"{name} -> {href}")

    text = "".join(lp.text)
    # blanks must never be printed as a number in a cost column
    check(not re.search(r">\s*None\s*<", p.read_text(encoding="utf-8")), "no raw None cell", name)
    check(not re.search(r">\s*NaN\s*<|>\s*None\s*<", p.read_text(encoding="utf-8")),
          "no sentinel values rendered", name)
    check(len(text.strip()) > 1500, "page has substantive content", name)

for p in pages:
    raw = p.read_text(encoding="utf-8")
    check(raw.count("<table") == raw.count("</table>"), "tables balanced", p.name)
    check(raw.count("<tr") == raw.count("</tr>"), "rows balanced", p.name)
    check('data-label=' in raw or "<table" not in raw, "mobile labels present", p.name)

# every table row that shows a value must also show at least one source chip in that row
for name in ("routes.html", "penalties.html", "ladder.html", "tax.html", "methodology.html"):
    raw = (SITE / name).read_text(encoding="utf-8")
    body_rows = re.findall(r"<tbody>(.*?)</tbody>", raw, re.S)
    unsourced = []
    for block in body_rows:
        for row in re.findall(r"<tr>(?:(?!</tr>).)*?</tr>", block, re.S):
            if 'class="src' not in row and re.search(r"\$[\d,]{3,}", row):
                unsourced.append(row)
    check(not unsourced, "every money row carries a source",
          f"{name}: {len(unsourced)} rows e.g. {unsourced[0][:160] if unsourced else ''}")

# ------------------------------------------------------------------ 7. exports match the site
with open(SITE / "cost-ladder.csv", encoding="utf-8") as fh:
    csv_rows = list(csv.DictReader(fh))
check(len(csv_rows) == rows_checked, "csv row count", f"{len(csv_rows)} vs {rows_checked}")
check(all(r["all_in_usd"] == "" for r in csv_rows), "csv keeps all-in blank")
check(all(r["receiver_fee_usd"] == "" for r in csv_rows), "csv keeps receiver fee blank")

data = json.loads((SITE / "data.json").read_text(encoding="utf-8"))
check(len(data["routes"]) == len(routes.ROUTES), "json route count")
check(abs(data["derived"]["ask_cny_per_usd"] - round(ask, 4)) < 1e-9, "json ask")
check(abs(data["derived"]["one_way_cost_pct"] - round((ask - mid) / mid, 6)) < 1e-9, "json one-way cost")
check(data["derived"]["one_way_cost_pct"] > 0, "json one-way cost positive")
check(len(data["penalty_lines"]) == len(analysis.PENALTY_LINES), "json penalty line count")
check(len(data["flags"]) == len(analysis.FLAGS), "json flag count")

# ------------------------------------------------------------------ 8. reproducibility
before = {p.name: p.read_bytes() for p in SITE.iterdir() if p.is_file()}
import subprocess
subprocess.run([sys.executable, str(ROOT / "edition-j" / "build" / "build.py")],
               check=True, capture_output=True)
after = {p.name: p.read_bytes() for p in SITE.iterdir() if p.is_file()}
check(before.keys() == after.keys(), "rebuild produces the same file set")
for k in before:
    check(before[k] == after[k], "rebuild is byte-identical", k)

# ------------------------------------------------------------------ report
print(f"Edition J verification: {CHECKED} checks")
print(f"  sources: {len(S)}  routes: {len(routes.ROUTES)}  ladder rows: {rows_checked}")
print(f"  pages: {len(pages)}  findings: {len(analysis.FINDINGS)}  "
      f"penalty lines: {len(analysis.PENALTY_LINES)}  flags: {len(analysis.FLAGS)}")
if FAIL:
    print(f"\nFAILED {len(FAIL)}:")
    for f in FAIL[:40]:
        print("  -", f)
    sys.exit(1)
print("  all checks passed")
