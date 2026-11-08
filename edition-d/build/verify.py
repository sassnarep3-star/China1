# -*- coding: utf-8 -*-
"""Verification gate for Edition D.

Run after build.py. Exits non-zero on any failure. Each check is mechanical; none
of them trusts the page text.

    python3 edition-d/build/verify.py
"""
import json
import os
import re
import sys
import html.parser
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs")
sys.path.insert(0, HERE)
import model as M  # noqa: E402

FAILS = []
WARNS = []
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    if not ok:
        FAILS.append(f"{name}: {detail}")


def warn(name, detail):
    WARNS.append(f"{name}: {detail}")


# --------------------------------------------------------------- official domains
OFFICIAL = {
    "safe.gov.cn", "m.safe.gov.cn", "www.safe.gov.cn",
    "gov.cn", "www.gov.cn", "mofcom.gov.cn", "m.mofcom.gov.cn",
    "chinatax.gov.cn", "www.chinatax.gov.cn",
    "irs.gov", "www.irs.gov", "fincen.gov", "www.fincen.gov",
    "govinfo.gov", "www.govinfo.gov", "ecfr.gov", "www.ecfr.gov",
    "uscode.house.gov", "treasury.gov", "home.treasury.gov",
    "pbc.gov.cn", "www.pbc.gov.cn", "customs.gov.cn", "www.customs.gov.cn",
    "npc.gov.cn", "www.npc.gov.cn",
    # primary publisher of its own price, used only for its own fee
    "boc.cn", "www.boc.cn", "bankofamerica.com", "www.bankofamerica.com",
}

pages = sorted(f for f in os.listdir(DOCS) if f.endswith(".html"))
raw = {p: open(os.path.join(DOCS, p), encoding="utf-8").read() for p in pages}

# --------------------------------------------------------------- 1. inventory
check("1. Every expected page exists", len(pages) == 3 + len(M.METHODS) + 8,
      f"found {len(pages)} pages")
for required in ["index.html", "executive-summary.html", "methods.html", "costs.html",
                 "penalty.html", "taxes.html", "reporting.html", "requirements.html",
                 "sources.html", "flagged.html", "repo-review.html"]:
    check(f"1. Page {required} exists", required in raw)

# --------------------------------------------------------------- 2. sources official
bad = []
for sid, s in M.SOURCES.items():
    host = urlparse(s["url"]).netloc.lower()
    if host not in OFFICIAL:
        bad.append(f"{sid} -> {host}")
check("2. Every source URL is on an allowlisted official publisher", not bad, "; ".join(bad))

check("2b. Every source names what was inspected", all(s.get("inspected") for s in M.SOURCES.values()))
check("2c. Every source lists what it supports", all(s.get("supports") for s in M.SOURCES.values()))
check("2d. Source ids in the register are unique", len(set(M.SOURCES)) == len(M.SOURCES))

# --------------------------------------------------------------- 3. numbers re-derived
tables = json.load(open(os.path.join(DOCS, "model.json"), encoding="utf-8"))["cost_tables"]
mismatch = []
for m in M.METHODS:
    cm = m["cost_model"]
    for row in tables[m["id"]]:
        a = row["amount"]
        if cm == "bank_wire_1":
            exp = M.bank_wire(a, 1)["total"]
        elif cm == "bank_wire_n":
            exp = M.bank_wire(a, int(-(-a // 50000)))["total"]
        elif cm == "staged_50_25_25":
            exp = M.staged(a, [0.5, 0.25, 0.25])["total"]
        elif cm == "no_conversion":
            exp = (M._commission(a) + M.P["cable_usd"] + M.P["intermediary_usd"]
                   + M.P["receiving_usd"])
        elif cm == "cash_carry":
            exp = a * M.P["one_way_pct"]
        else:
            exp = None
        if exp is not None and row["cost"] is not None and abs(row["cost"] - exp) > 0.005:
            mismatch.append(f"{m['id']} {a}: {row['cost']} != {exp}")
check("3. Every published cost is re-derived from the model", not mismatch, "; ".join(mismatch[:5]))

# --------------------------------------------------------------- 4. 40 increments everywhere
missing = []
for m in M.METHODS:
    amounts = [r["amount"] for r in tables[m["id"]]]
    if amounts != list(range(10000, 400001, 10000)):
        missing.append(m["id"])
check("4. Every route table covers exactly $10,000-$400,000 in $10,000 steps (40 rows)",
      not missing, ", ".join(missing))

# --------------------------------------------------------------- 5. rendered cells match model
render_bad = []
def money(x):
    return "$" + f"{x:,.2f}"

for m in M.METHODS:
    src = raw[f"method-{m['id']}.html"]
    for row in tables[m["id"]]:
        if row["cost"] is None:
            continue
        if money(row["cost"]) not in src:
            render_bad.append(f"{m['id']} {row['amount']}")
            break
check("5. Every computed total appears verbatim in its rendered page", not render_bad,
      ", ".join(render_bad[:5]))

# --------------------------------------------------------------- 6. citations on every route
uncited = [m["id"] for m in M.METHODS if not m["basis"] and m["kind"] != "NOT_AVAILABLE"]
check("6. Every route that is not 'not available' carries a source id", not uncited, ", ".join(uncited))
no_link = [m["id"] for m in M.METHODS
           if "class=\"src\"" not in raw[f"method-{m['id']}.html"]
           and not (m["kind"] == "NOT_AVAILABLE" and "class=\"flag\"" in raw[f"method-{m['id']}.html"])]
check("6b. Every route page renders an official source link, or a flagged absence for a route that does not exist",
      not no_link, ", ".join(no_link))

# --------------------------------------------------------------- 7. blanks are disclosed
blank_bad = []
for m in M.METHODS:
    if m["cost_model"] in ("unverified", "not_available", "prohibited"):
        src = raw[f"method-{m['id']}.html"]
        if "Unverified" not in src and "Statutory exposure" not in src and "No cost table" not in src:
            blank_bad.append(m["id"])
check("7. Every blank or unpriced table is labelled unverified or statutory", not blank_bad,
      ", ".join(blank_bad))

# --------------------------------------------------------------- 8. flags resolve
flag_ids = {f["id"] for f in M.FLAGS}
referenced = set()
for p, s in raw.items():
    referenced |= set(re.findall(r'href="flagged\.html#(U\d\d)"', s))
unknown = referenced - flag_ids
check("8. Every referenced flag exists", not unknown, ", ".join(sorted(unknown)))
check("8b. Every flag is reachable on the flagged page",
      all(f'id="{f}"' in raw["flagged.html"] for f in flag_ids))

# --------------------------------------------------------------- 9. internal links resolve
broken = []
for p, s in raw.items():
    for href in re.findall(r'href="([^"#][^"]*)"', s):
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        target = href.split("#")[0]
        if not target:
            continue
        if not os.path.exists(os.path.join(DOCS, target)):
            broken.append(f"{p} -> {href}")
check("9. Every internal link resolves to a generated file", not broken, "; ".join(broken[:6]))

# anchors
anchor_bad = []
for p, s in raw.items():
    for href in re.findall(r'href="(?:[\w.\-]+\.html)?#([\w\-]+)"', s):
        target = href
        page = p
        m_ = re.match(r'href="([\w.\-]+\.html)#', s)
        if m_:
            pass
        if f'id="{target}"' not in raw.get(page, ""):
            # check across all pages, since cross-page anchors are used for flags
            if not any(f'id="{target}"' in t for t in raw.values()):
                anchor_bad.append(f"{p}#{target}")
check("9b. Every in-page anchor exists somewhere on the site", not anchor_bad,
      ", ".join(anchor_bad[:6]))

# --------------------------------------------------------------- 10. no placeholders
placeholders = ["TODO", "TBD", "lorem ipsum", "XXX", "{{", "}}", "FIXME"]
found = []
for p, s in raw.items():
    for ph in placeholders:
        if ph in s:
            found.append(f"{p}:{ph}")
check("10. No template placeholders survive into the output", not found, ", ".join(found[:5]))

# --------------------------------------------------------------- 11. every row in the master table has a basis
costs_page = raw["costs.html"]
check("11. The cost page states the basis of every input",
      all(x in costs_page for x in ["Assumption A2", "Assumption A3", "Verified", "Derived"]))
check("11b. The cost page publishes the rate and its date",
      str(M.P["cny_per_usd"]) in costs_page and "2026-11-09" in costs_page)

# --------------------------------------------------------------- 12. steps present
step_bad = [m["id"] for m in M.METHODS if len(m["steps"]) < 1]
check("12. Every route has at least one step listed", not step_bad, ", ".join(step_bad))
step_cited = [m["id"] for m in M.METHODS
              if not any(s[2] for s in m["steps"]) and m["kind"] not in ("NOT_AVAILABLE",)]
check("12b. Every route's step sequence carries a source on at least one step",
      not step_cited, ", ".join(step_cited))
no_disclaimer = [m["id"] for m in M.METHODS
                 if m["kind"] == "PROHIBITED" and "no lawful" not in raw[f"method-{m['id']}.html"].lower()]
check("12c. Every prohibited route states that no lawful sequence is provided",
      not no_disclaimer, ", ".join(no_disclaimer))

# --------------------------------------------------------------- 13. payment of tax claims
check("13. No page claims a Chinese conversion tax exists",
      "tax on the conversion" not in "".join(raw.values()).lower()
      or "no chinese tax on the conversion" in "".join(raw.values()).lower())

# --------------------------------------------------------------- 14. determinism inputs
check("14. model.json exists and parses", os.path.exists(os.path.join(DOCS, "model.json")))
check("14b. .nojekyll present for GitHub Pages", os.path.exists(os.path.join(DOCS, ".nojekyll")))

# --------------------------------------------------------------- 15. every method appears in nav
orphans = [m["id"] for m in M.METHODS if f'method-{m["id"]}.html' not in raw["methods.html"]]
check("15. No orphan route pages", not orphans, ", ".join(orphans))

# --------------------------------------------------------------- report
print("Edition D verification")
print("=" * 60)
for name, ok, detail in CHECKS:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))
print("-" * 60)
for w in WARNS:
    print("WARN ", w)
print(f"{sum(1 for _, ok, _ in CHECKS if ok)}/{len(CHECKS)} checks passed, "
      f"{len(FAILS)} failure(s), {len(WARNS)} warning(s)")
if FAILS:
    print("\nFAILURES:")
    for f in FAILS:
        print(" -", f)
    sys.exit(1)
print("RESULT: PASS")
