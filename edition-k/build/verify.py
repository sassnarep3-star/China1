#!/usr/bin/env python3
"""Independent verifier for Edition K.

It does not import build.py. It re-derives every priced cell from the raw
parameters in data/model.json with its own arithmetic, then parses the generated
HTML and compares cell by cell. It also enforces the brief's hard rules:

  * exactly the 40 targets, USD 10,000 .. 400,000 in 10,000 steps
  * every table body row carries at least one first-party source link
  * every external link is a registered source
  * every local link and anchor resolves
  * no unrendered template text, no 'None', no 'nan'
  * prohibited routes publish no steps
  * a missing number is visibly marked, never silently zero
"""
from __future__ import annotations

import hashlib
import html as htmlmod
import json
import re
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"

errors: list[str] = []
checks = 0


def check(cond: bool, msg: str) -> None:
    global checks
    checks += 1
    if not cond:
        errors.append(msg)


def D(x) -> Decimal:
    return Decimal(str(x))


def m(x: Decimal) -> str:
    return f"${x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"


def y(x: Decimal) -> str:
    return f"\u00a5{x.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"


# --------------------------------------------------------------- expected values

model = json.loads((DATA / "model.json").read_text())
sources = json.loads((DATA / "sources.json").read_text())
methods = json.loads((DATA / "methods.json").read_text())
flags = json.loads((DATA / "flags.json").read_text())

sell = D(model["rates"]["boc_sell_cny_per_usd"]["value"])
buy = D(model["rates"]["boc_buy_cny_per_usd"]["value"])
board_mid = (buy + sell) / 2
half_spread = ((sell - buy) / 2) / board_mid

boc = next(r for r in model["rails"] if r["id"] == "boc")
hsbc = next(r for r in model["rails"] if r["id"] == "hsbc")

check(abs(half_spread - D(boc["fx_spread_pct"])) < Decimal("0.0000000001"),
      f"half-spread recomputes to {half_spread}, model says {boc['fx_spread_pct']}")
# the model's declared spread is used for the cells; it is checked above against
# an independent recomputation from the two published quotes.
SPREAD = D(boc["fx_spread_pct"])

targets = list(range(model["targets"]["start_usd"], model["targets"]["stop_usd"] + 1,
                     model["targets"]["step_usd"]))
check(len(targets) == 40, f"expected 40 targets, got {len(targets)}")
check(targets[0] == 10000 and targets[-1] == 400000, "target endpoints wrong")
check(all(b - a == 10000 for a, b in zip(targets, targets[1:])), "target step is not 10000")


def expect_boc(t: int) -> list[str]:
    cny = D(t) * sell
    fx = D(t) * SPREAD
    comm_cny = min(max(cny * D(boc["commission_pct"]), D(boc["commission_min_cny"])),
                   D(boc["commission_max_cny"]))
    comm_usd = comm_cny / sell
    cable = D(boc["cable_cny"]) / sell
    recv = D(boc["receiving_usd"])
    total = fx + comm_usd + cable + recv
    return [
        f"${t:,}", m(total), f"{(total / D(t) * 100).quantize(Decimal('0.001'))}%",
        m(D(t) - total), m(fx), y(comm_cny), m(cable), m(recv), y(cny),
    ]


def expect_hsbc_charges(t: int) -> str:
    cny = D(t) * sell
    comm = min(max(cny * D(hsbc["commission_pct"]), D(hsbc["commission_min_cny"])),
               D(hsbc["commission_max_cny"]))
    return m((comm + D(hsbc["cable_cny"])) / sell)


# --------------------------------------------------------------- html helpers

TAG = re.compile(r"<[^>]+>")
ROW = re.compile(r"<tr>(.*?)</tr>", re.S)
CELL = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.S)
TBODY = re.compile(r"<tbody>(.*?)</tbody>", re.S)


def text_of(fragment: str) -> str:
    return re.sub(r"\s+", " ", htmlmod.unescape(TAG.sub("", fragment))).strip()


def pages() -> dict[str, str]:
    out = {}
    for f in sorted(SITE.glob("*.html")):
        out[f.name] = f.read_text(encoding="utf-8")
    return out


PAGES = pages()
check(len(PAGES) == 8, f"expected 8 pages, got {len(PAGES)}")


def rows_of(html: str) -> list[dict]:
    """Each row: {'raw': original html, 'cells': visible text per cell}."""
    out = []
    for body in TBODY.findall(html):
        for r in ROW.findall(body):
            cells = [text_of(c) for c in CELL.findall(r)]
            if cells:
                out.append({"raw": r, "cells": cells})
    return out


# --------------------------------------------------------------- ladder checks

costs = PAGES["costs.html"]
cost_rows = [r for r in rows_of(costs)
             if r["cells"] and r["cells"][0].startswith("$")]
# table 1 rows: 10 cells (9 values + sources); table 2 rows: 7 cells
t1 = [r for r in cost_rows if len(r["cells"]) == 10]
t2_rows = [r for r in cost_rows if len(r["cells"]) == 7]
check(len(t1) == 40, f"BOC ladder should have 40 rows, found {len(t1)}")
for i, row in enumerate(t1[:40]):
    exp = expect_boc(targets[i])
    got = row["cells"][:9]
    check(got == exp, f"BOC row {i+1} ({row['cells'][0]}) mismatch:\n  got {got}\n  exp {exp}")
    check("http" in row["raw"].split("</td>")[-2] if "</td>" in row["raw"] else False,
          f"BOC row {row['cells'][0]} has no source link")

# comparison ladder: 7 cells
t2 = t2_rows
check(len(t2) == 40, f"comparison ladder should have 40 rows, found {len(t2)}")
for i, row in enumerate(t2[:40]):
    t = targets[i]
    c = row["cells"]
    check(c[0] == f"${t:,}", f"comparison row {i} amount {c[0]}")
    check(c[1] == expect_boc(t)[1], f"comparison BOC total row {t}: {c[1]} vs {expect_boc(t)[1]}")
    check(c[2] == expect_hsbc_charges(t), f"comparison HSBC row {t}: {c[2]} vs {expect_hsbc_charges(t)}")
    check(c[3] == "UNVERIFIED", f"Wise cell at {t} must be UNVERIFIED, got {c[3]}")
    check(c[4] == m(D(t) * D(model["penalties"]["standard_max_pct"])), f"penalty 30% row {t}")
    check(c[5] == m(D(t) * D(model["penalties"]["serious_max_pct"])), f"penalty 100% row {t}")
    check("http" in row["raw"], f"comparison row {t} has no source link")

# monotonic sanity: cost percentage must fall as amount rises, cost must rise
totals = [D(expect_boc(t)[1].replace("$", "").replace(",", "")) for t in targets]
check(all(b > a for a, b in zip(totals, totals[1:])), "all-in cost is not strictly increasing")
pcts = [D(expect_boc(t)[2].replace("%", "")) for t in targets]
check(all(b <= a for a, b in zip(pcts, pcts[1:])), "cost percentage should not increase with size")
check(pcts[0] > pcts[-1], "cost percentage does not fall between $10k and $400k")

# penalty ladders
tax = PAGES["taxes.html"]
pen = [r for r in rows_of(tax)
       if len(r["cells"]) == 5 and r["cells"][0].startswith("$") and r["cells"][1].startswith("$")]
pen = [r for r in pen if r["cells"][0] in {f"${t:,}" for t in targets}]
check(len(pen) == 40, f"tax penalty ladder should have 40 rows, found {len(pen)}")
for r in pen[:40]:
    c = r["cells"]
    t = int(c[0].replace("$", "").replace(",", ""))
    check(c[1] == m(D(t) * D("0.30")), f"penalty 30% wrong at {t}")
    check(c[2] == m(D(t) * D("1.00")), f"penalty 100% wrong at {t}")
    check(c[3] == m(D(t) * D("0.20")), f"cash penalty 20% wrong at {t}")
    check("http" in r["raw"], f"penalty row {t} has no source link")

# index figures agree with the ladder
idx = PAGES["index.html"]
for t in (10000, 100000, 400000):
    exp = expect_boc(t)
    check(exp[1] in idx, f"index missing all-in {exp[1]} for ${t:,}")
    check(exp[2] in idx, f"index missing percentage {exp[2]} for ${t:,}")

# --------------------------------------------------------------- hard rules

allowed_hosts = {urlparse(s["url"]).netloc for s in sources["sources"]}
source_urls = {s["url"] for s in sources["sources"]}
LOCAL = re.compile(r'href="([^"]+)"')
ID = re.compile(r'id="([^"]+)"')

ids_by_page = {name: set(ID.findall(h)) for name, h in PAGES.items()}

for name, html in PAGES.items():
    for href in LOCAL.findall(html):
        if href.startswith(("http://", "https://")):
            check(href in source_urls, f"{name}: external link not in source register: {href}")
            check(urlparse(href).netloc in allowed_hosts, f"{name}: host not allowed: {href}")
        elif href.startswith("#"):
            check(href[1:] in ids_by_page[name], f"{name}: missing local anchor {href}")
        else:
            target, _, frag = href.partition("#")
            if not target:
                continue
            check(target in PAGES or (SITE / target).is_file(),
                  f"{name}: broken local link {target}")
            if frag:
                check(frag in ids_by_page.get(target, set()), f"{name}: broken anchor {href}")

    # every table body row must cite a first-party source
    for body in TBODY.findall(html):
        for r in ROW.findall(body):
            cells = CELL.findall(r)
            if not cells:
                continue
            txt = text_of(r)
            check("http" in r or "No official source exists" in txt,
                  f"{name}: table row without a source link: {txt[:70]}")

    for bad in ("&lt;span", "{{", "}}", "UNVERIFIED_LINK", "Decimal(", "&lt;td"):
        check(bad not in html, f"{name}: suspicious token {bad!r} in output")
    check(re.search(r">\s*None\s*<", html) is None, f"{name}: a cell rendered as None")
    check(re.search(r"\bnan\b", html) is None, f"{name}: a cell rendered as nan")

# prohibited routes publish no steps
for meth in methods["methods"]:
    if meth["status"] == "prohibited":
        check(meth["steps"] == [], f"{meth['id']}: prohibited route has steps")
        check(f'id="{meth["id"]}"' not in PAGES["steps.html"],
              f"{meth['id']}: prohibited route appears on the steps page")

# every lawful route with steps has an anchor on the steps page
for meth in methods["methods"]:
    if meth["steps"]:
        check(f'id="{meth["id"]}"' in PAGES["steps.html"], f"{meth['id']}: missing steps anchor")
    else:
        check(f'id="{meth["id"]}"' not in PAGES["steps.html"], f"{meth['id']}: step anchor for a route with no steps")

# every method cites at least one registered source
for meth in methods["methods"]:
    check(bool(meth["sources"]), f"{meth['id']}: no sources")
    for sid in meth["sources"]:
        check(sid in {s["id"] for s in sources["sources"]}, f"{meth['id']}: unknown source {sid}")

# every flag id appears on the flagged page
for f in flags["flags"]:
    check(f["id"] in PAGES["flagged.html"], f"{f['id']}: not published on the flagged page")

# every source id appears in the register page
for s in sources["sources"]:
    check(s["url"] in PAGES["sources.html"], f"{s['id']}: url missing from register")
    check(s["quote"][:40] in PAGES["sources.html"], f"{s['id']}: quote missing from register")

# blank semantics: the unpriced rails must be marked, not zeroed
check("UNVERIFIED" in PAGES["costs.html"], "costs page has no UNVERIFIED marker")
check(costs.count("UNVERIFIED") >= 40, "every Wise cell should be marked UNVERIFIED")

# --------------------------------------------------------------- determinism


def digest() -> str:
    h = hashlib.sha256()
    for f in sorted(SITE.rglob("*")):
        if f.is_file():
            h.update(f.relative_to(SITE).as_posix().encode())
            h.update(f.read_bytes())
    return h.hexdigest()


before = digest()
res = subprocess.run([sys.executable, str(ROOT / "build" / "build.py")],
                     capture_output=True, text=True)
check(res.returncode == 0, f"rebuild failed: {res.stderr[-400:]}")
after = digest()
check(before == after, "build is not deterministic: output changed on rebuild")

# --------------------------------------------------------------- report

print(f"Edition K verification: {checks} checks")
if errors:
    print(f"FAIL — {len(errors)} error(s)")
    for e in errors[:40]:
        print("  -", e)
    sys.exit(1)
print("PASS — 0 errors")
print(f"  targets: {len(targets)} ({targets[0]:,} to {targets[-1]:,})")
print(f"  BOC all-in: {expect_boc(10000)[1]} at $10,000 -> {expect_boc(400000)[1]} at $400,000")
print(f"  half-spread: {(half_spread*100).quantize(Decimal('0.00001'))}%")
print(f"  sources: {len(sources['sources'])}  methods: {len(methods['methods'])}  flags: {len(flags['flags'])}")
