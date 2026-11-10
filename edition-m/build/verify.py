#!/usr/bin/env python3
"""Independent checks for Edition M.  Run after build.py:  python3 edition-m/build/verify.py

1. Recomputes every cost row and every currency-gain cell from data/inputs.json with its own
   arithmetic (fractions, not the generator's code) and compares with data/ladders.json and
   with the figures printed in the HTML.
2. Ties each numeric input to the sentence quoted from its official source.
3. Walks every generated page: every table body row must carry a link to an official host,
   no cell may be empty, every blank must point at an existing flag or state its reason,
   every internal link and anchor must resolve, and no template token may be left.
Exit code 0 only if every check passes.
"""
from __future__ import annotations

import json
import math
import re
import sys
from fractions import Fraction as F
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ED = Path(__file__).resolve().parents[1]
DATA = ED / "data"
PAGES = ["index.html", "costs.html", "methods.html", "steps.html", "tax.html", "flagged.html", "audit.html",
         "sources.html", "summary.html"]
OFFICIAL = (
    ".gov.cn", ".gov", "boc.cn", "bankofchina.com", "icbc.com.cn", "hsbc.com.cn", "ccb.com", "cmbchina.com",
    "wise.com", "chase.com", "bankofamerica.com", "schwab.com",
)
checks = 0
errors: list[str] = []


def ok(cond: bool, msg: str) -> None:
    global checks
    checks += 1
    if not cond:
        errors.append(msg)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def fr(x) -> F:
    return F(str(x))


def half_up(x: F, places: int = 2) -> F:
    q = 10 ** places
    return F(math.floor(x * q + F(1, 2)), q)


def near(a, b, tol=F(1, 200)) -> bool:
    return abs(fr(a) - fr(b)) <= tol


inp = load("inputs.json")
src = {s["id"]: s for s in load("sources.json")["sources"]}
methods = load("methods.json")
tax = load("tax.json")
flags = {f["id"]: f for f in load("flags.json")["flags"]}
audit = load("audit.json")
lad = load("ladders.json")

# ---------------------------------------------------------------- 1. arithmetic
bid, ask = fr(inp["fx"]["boc_spot_bid_per100"]), fr(inp["fx"]["boc_spot_ask_per100"])
cash_ask = fr(inp["fx"]["boc_cash_ask_per100"])
mid = (bid + ask) / 2 / 100
askr = ask / 100
margin = (askr - mid) / mid
cash_margin = (cash_ask / 100 - mid) / mid
amounts = list(range(inp["amounts_usd"]["start"], inp["amounts_usd"]["stop"] + 1, inp["amounts_usd"]["step"]))
ok(amounts == [10000 * i for i in range(1, 41)], "amount ladder is not 40 steps of USD 10,000")
ok(near(lad["mid_cny_per_usd"], mid, F(1, 10 ** 9)), "midpoint mismatch")
b, h, w, c = inp["boc"], inp["hsbc_cn"], inp["wise"], inp["safe_caps"]
recv = fr(inp["us_receiving"]["chase_incoming_wire_usd"])


def clampf(x, lo, hi):
    return max(fr(lo), min(fr(hi), x))


def boc_wire(usd: F):
    comm = half_up(clampf(fr(b["commission_rate"]) * usd * askr, b["commission_min_cny"], b["commission_max_cny"]))
    fees_cny = comm + fr(b["cable_international_cny"])
    return usd * margin + fees_cny / mid + fr(b["full_amount_usd"]) + recv, fees_cny


L = lad["ladders"]
for i, a in enumerate(amounts):
    A = F(a)
    # bank wire, all-in
    tot, fees = boc_wire(A)
    r = L["boc"][i]
    ok(r["usd"] == a and near(r["total"], half_up(tot)) and near(r["fees_cny"], fees) and near(r["pct"], half_up(tot / A * 100))
       and near(r["arrives"], half_up(A - tot)) and near(r["fx"], half_up(A * margin)), f"boc row {a}")
    # quota: one wire per USD 50,000
    n = math.ceil(A / 50000)
    left, tq = A, F(0)
    for _ in range(n):
        part = min(left, F(50000))
        tq += boc_wire(part)[0]
        left -= part
    r = L["quota"][i]
    ok(r["years"] == n and r["transfers"] == n and near(r["total"], half_up(tq)), f"quota row {a}")
    # HSBC known part
    comm = half_up(clampf(fr(h["commission_rate"]) * A * askr, h["commission_min_cny"], h["commission_max_cny"]))
    known = (comm + fr(h["cable_cny"])) / mid + recv
    r = L["hsbc"][i]
    ok(near(r["known"], half_up(known)) and r["total"] is None and r["fx"] is None, f"hsbc row {a}")
    # Wise: sums of quotes, every transfer under the cap
    quotes = {q["send_cny"]: fr(q["fee_cny"]) for q in w["quotes_cny"]}
    sizes = sorted(quotes)
    ok(sizes == [int(half_up(F(10000) * mid * k, 0)) for k in (1, 2, 3, 4)], "Wise quote sizes do not match the row unit") if i == 0 else None
    ok(sizes[-1] <= w["per_transfer_cap_cny"], "Wise transfer above cap") if i == 0 else None
    k = a // 10000
    q4, rem = divmod(k, 4)
    fee_cny = q4 * quotes[sizes[-1]] + (quotes[sizes[rem - 1]] if rem else 0)
    r = L["wise"][i]
    ok(near(r["fee_cny"], fee_cny) and near(r["total"], half_up(fee_cny / mid)) and r["transfers"] == q4 + (1 if rem else 0)
       and near(r["pct"], half_up(fee_cny / mid / A * 100)), f"wise row {a}")
    # cross-border RMB known part
    cny = A * mid
    comm = half_up(clampf(fr(b["commission_rate"]) * cny, b["commission_min_cny"], b["commission_max_cny"]))
    r = L["rmb"][i]
    ok(near(r["known"], half_up((comm + fr(b["cable_international_cny"])) / mid)) and r["total"] is None, f"rmb row {a}")
    # USD cash
    r = L["cash_usd"][i]
    ok(r["trips"] == math.ceil(A / fr(c["cash_carry_bank_permit_max_usd"])) and near(r["known"], half_up(A * cash_margin))
       and r["total"] is None, f"cash_usd row {a}")
    # RMB cash
    r = L["cash_rmb"][i]
    ok(r["trips"] == math.ceil(cny / fr(c["rmb_cash_per_trip_cny"])) and r["total"] is None and r["known"] is None, f"cash_rmb row {a}")
    # ATM
    day = fr(c["card_cash_abroad_per_card_per_day_cny"])
    nfull = math.floor(cny / day)
    remc = cny - nfull * day
    per = lambda x: min(fr(b["atm_abroad_fixed_cny"]) + fr(b["atm_abroad_rate"]) * x, fr(b["atm_abroad_max_cny"]))
    fee = nfull * per(day) + (per(remc) if remc > 0 else 0)
    r = L["atm"][i]
    ok(r["withdrawals"] == nfull + (1 if remc > 0 else 0) and r["years"] == math.ceil(cny / fr(c["card_cash_abroad_per_year_cny"]))
       and near(r["known"], half_up(fee / mid)) and r["total"] is None, f"atm row {a}")
    # card: nothing confirmed
    r = L["card"][i]
    ok(r["total"] is None and r["known"] is None, f"card row {a}")
    # currency gain
    g = lad["currency_gain_usd"][i]
    for y, rate in inp["irs_yearly_average_cny_per_usd"].items():
        if y == "src":
            continue
        ok(near(g[y], half_up(cny / askr - cny / fr(rate))), f"gain {a} {y}")

# ---------------------------------------------------------------- 2. inputs tied to quoted sentences
def quoted(sid: str, *needles: str) -> None:
    text = src[sid]["quote"] + " " + src[sid].get("note", "")
    for n in needles:
        ok(n in text, f"{sid}: quoted text does not contain {n!r}")


quoted("S30", f'{inp["fx"]["boc_spot_bid_per100"]:.2f}', f'{inp["fx"]["boc_spot_ask_per100"]:.2f}', f'{inp["fx"]["boc_reference_per100"]:.2f}', "17:39:58")
quoted("S32", "1‰", "50元", "260元", "150元", "80元", "25美元", "15 美元", "10元/份", "2026-12-31")
quoted("S33", "1‰", "50元", "260元", "150元")
quoted("S34", "12 元", "1%", "112 元")
quoted("S35", "0.1%", "100元", "500元", "120元", "CNY 200")
quoted("S40", "$15 per transfer")
quoted("S41", "$15.00")
quoted("S42", "No fee")
quoted("S39", "434.84", "0.149924", "845.90", "1,741.62")
quoted("S38", "1,570.09", "1,224.98", "mid-market")
quoted("S37", "300,000 CNY")
quoted("S15", "10万元", "1万元")
quoted("S19", "20000元")
quoted("S16", "5万美元")
quoted("S53", "7.129", "7.189", "7.075", "6.730", "6.452")
quoted("S58", "16,536", "165,353")
quoted("S01", "购汇资金来源材料（含税务凭证）")
quoted("S07", "20 个工作日", "5 个工作日", "否")
quoted("S52", "$200")
quoted("S50", "$10,000")
quoted("S51", "$100,000")
ok(inp["us_penalties"]["fbar_nonwillful_usd"] == 16536 and inp["us_penalties"]["fbar_willful_floor_usd"] == 165353, "FBAR inputs")
for q in w["quotes_cny"]:
    ok(f'{q["fee_cny"]:,.2f}' in (src["S39"]["quote"] + src["S39"]["note"] + src["S38"]["quote"] + src["S38"]["note"]),
       f'Wise quote {q["send_cny"]} not in quoted source text')

# every source: official host, required fields
for s in src.values():
    host = urlparse(s["url"]).netloc.lower()
    ok(any(host == o.lstrip(".") or host.endswith(o) for o in OFFICIAL), f'{s["id"]}: host {host} is not on the official list')
    ok(all(s.get(k) for k in ("issuer", "title", "url", "how", "quote", "group")), f'{s["id"]}: missing field')
    ok(s["how"] in ("full", "sections", "excerpt"), f'{s["id"]}: bad how')

# every source id used in the data exists
def ids_in(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("src", "check") and isinstance(v, list):
                yield from v
            else:
                yield from ids_in(v)
    elif isinstance(o, list):
        for v in o:
            yield from ids_in(v)


for name, blob in (("methods", methods), ("tax", tax), ("flags", list(flags.values())), ("audit", audit)):
    for i in ids_in(blob):
        ok(i in src, f"{name}: unknown source {i}")
for m in methods["methods"]:
    ok(len(m["steps"]) >= 2 and m["pros"] and m["cons"] and m["ladder"] in L, f'{m["id"]}: incomplete method')
    for part in m["steps"] + m["pros"] + m["cons"]:
        ok(bool(part["src"]), f'{m["id"]}: item without source')
ok(len(methods["methods"]) == 13 and len(methods["prohibited"]) == 6, "method counts")
ok(all("step" not in json.dumps(p).lower() for p in methods["prohibited"]), "prohibited entries must not contain steps")

# ---------------------------------------------------------------- 3. the generated pages
class Walker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.hrefs = set(), []
        self.in_tbody = self.in_tr = self.in_cell = False
        self.row_links, self.cell_text, self.rows, self.cells = [], [], [], []
        self.stack, self.tables, self.table_rows = [], 0, []
        self.blank_pending = None
        self.blank_problems = 0
        self.after_blank = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag not in ("meta", "link", "br", "img", "hr", "input"):
            self.stack.append(tag)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
            if self.in_tr:
                self.row_links.append((a.get("class", ""), a["href"]))
            if self.blank_pending is not None and a.get("class") == "fl":
                self.after_blank.append(a["href"])
                self.blank_pending = None
        if tag == "span" and a.get("class") == "why" and self.blank_pending is not None:
            self.blank_pending = None
        if tag == "span" and a.get("class") == "blank":
            if self.blank_pending is not None:
                self.blank_problems += 1
            self.blank_pending = True
        if tag == "table":
            self.tables += 1
            self.table_rows.append(0)
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.in_tr, self.row_links, self.cells = True, [], []
            self.table_rows[-1] += 1
        if tag in ("td", "th") and self.in_tr:
            self.in_cell, self.cell_text = True, []

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            errors.append(f"unbalanced tag {tag}")
        if tag in ("td", "th") and self.in_cell:
            self.in_cell = False
            self.cells.append("".join(self.cell_text).strip())
        if tag == "tr" and self.in_tr:
            self.in_tr = False
            self.rows.append((self.cells, self.row_links))
            if self.blank_pending is not None:
                self.blank_problems += 1
                self.blank_pending = None
        if tag == "tbody":
            self.in_tbody = False

    def handle_data(self, data):
        if self.in_cell:
            self.cell_text.append(data)


walk = {}
for p in PAGES:
    f = ED / p
    ok(f.exists(), f"missing page {p}")
    text = f.read_text(encoding="utf-8")
    ok("{{" not in text and "}}" not in text, f"{p}: template token left")
    ok('<meta name="viewport" content="width=device-width, initial-scale=1">' in text, f"{p}: no viewport meta")
    ok('<html lang="en">' in text and "<h1>" in text, f"{p}: lang or h1 missing")
    ok(not re.search(r">\s*(None|null|nan)\s*<", text), f"{p}: literal None/null printed in a cell")
    wk = Walker()
    wk.feed(text)
    walk[p] = wk
    ok(not wk.stack, f"{p}: unclosed tags {wk.stack[:5]}")
    ok(wk.blank_problems == 0, f"{p}: {wk.blank_problems} blank cells without a flag link or reason")
    for cells, row_links in wk.rows:
        official = [h for cls, h in row_links if cls == "s" and any(urlparse(h).netloc.lower().endswith(o) or urlparse(h).netloc.lower() == o.lstrip(".") for o in OFFICIAL)]
        ok(bool(official), f"{p}: table row without an official source link: {cells[:2]}")
        ok(all(cells[1:]) and len(cells) >= 2, f"{p}: empty cell in row {cells[:2]}")
    for hflag in wk.after_blank:
        ok(hflag.startswith("flagged.html#") and hflag.split("#")[1] in flags, f"{p}: blank points at unknown flag {hflag}")

for p, wk in walk.items():
    for h in wk.hrefs:
        if h.startswith(("http://", "https://", "mailto:")):
            continue
        path, _, frag = h.partition("#")
        target = (ED / path).resolve() if path else ED / p
        ok(target.exists(), f"{p}: broken link {h}")
        if frag and target.suffix == ".html" and target.parent == ED:
            ok(frag in walk[target.name].ids, f"{p}: missing anchor {h}")
    # every external link in a source pill must be a known source URL
    known = {s["url"] for s in src.values()}
    for h in wk.hrefs:
        if h.startswith(("http://", "https://")) and "github.com/sassnarep3-star" not in h:
            ok(h in known, f"{p}: external link not in sources.json: {h}")

# ladder tables: nine tables of 40 rows on the costs page, gain table of 40 rows on the tax page
costs = walk["costs.html"]
ok(sum(1 for n in costs.table_rows if n == 40) == 9, f"costs.html: expected nine 40-row tables, got {costs.table_rows}")
ok(40 in walk["tax.html"].table_rows, "tax.html: no 40-row currency-gain table")
ctext = (ED / "costs.html").read_text(encoding="utf-8")
for i, a in enumerate(amounts):
    tot, _ = boc_wire(F(a))
    ok(f"${float(half_up(tot)):,.2f}" in ctext, f"costs.html does not print the recomputed bank-wire total for {a}")
    ok(f"${L['wise'][i]['total']:,.2f}" in ctext, f"costs.html does not print the Wise total for {a}")
ok("Flagged for Review" in (ED / "flagged.html").read_text(encoding="utf-8"), "flagged page title")
ok(len(walk["flagged.html"].rows) == len(flags), "flagged.html: one row per flag")
ok(len(walk["sources.html"].rows) == len(src), "sources.html: one row per source")
ok(all(fid in walk["flagged.html"].ids for fid in flags), "flag anchors")
ok(all(m["id"] in walk["steps.html"].ids and m["id"] in walk["methods.html"].ids for m in methods["methods"]), "method anchors")
ok((ED / "assets" / "style.css").exists() and (DATA / "ladders.csv").exists(), "assets and exports present")
md = (ED / "EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
ok(f"${L['boc'][9]['total']:,.2f}" in md and f"${L['boc'][39]['total']:,.2f}" in md, "EXECUTIVE_SUMMARY.md figures")

rows_total = sum(len(wk.rows) for wk in walk.values())
if errors:
    print(f"FAILED: {len(errors)} of {checks} checks")
    for e in errors[:60]:
        print(" -", e)
    sys.exit(1)
print(f"edition-m verified: {checks} checks passed; {len(PAGES)} pages; {rows_total} table rows, each with an official source link; "
      f"{sum(len(v) for v in L.values())} cost rows recomputed; {len(src)} sources; {len(flags)} flags")
