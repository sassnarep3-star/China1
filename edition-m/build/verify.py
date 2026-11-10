#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent verifier for Edition M. Does not import build.py: recomputes every published
figure with exact fractions, re-parses the generated HTML, and checks the source discipline.
Exit code 1 on any failure."""
import csv, json, os, re, sys, subprocess
from fractions import Fraction as Fr
from html.parser import HTMLParser
from urllib.parse import urlparse
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); ROOT = os.path.dirname(OUT)
sys.path.insert(0, HERE)
import content as C
fails = []; checks = 0
def ok(cond, msg):
    global checks
    checks += 1
    if not cond: fails.append(msg)

# hosts accepted as official: government bodies, or the institution's own published tariff/help page
OFFICIAL = {"www.gov.cn", "www.safe.gov.cn", "m.safe.gov.cn", "www.pbc.gov.cn", "www.boc.cn", "pic.bankofchina.com", "www.hsbc.com.cn",
            "www1.ccb.com", "wise.com", "guangdong.chinatax.gov.cn", "fgk.chinatax.gov.cn", "hainan.chinatax.gov.cn", "www.hunan.gov.cn",
            "guangzhou.customs.gov.cn", "www.irs.gov", "www.govinfo.gov", "www.cbp.gov", "www.chase.com"}
REPO_HOST = "github.com"

# ---- 1. source registry
for k, v in C.S.items():
    h = urlparse(v["u"]).netloc
    ok(h in OFFICIAL, "source %s host not on official list: %s" % (k, h))
    ok(v["how"] in ("full", "excerpt"), "source %s has no verification method" % k)
    ok(len(v["v"]) > 20 and v["t"] and v["pub"], "source %s incomplete" % k)
for k, (t, d, s) in C.F.items():
    for i in s: ok(i in C.S, "flag %s cites unknown source %s" % (k, i))
for mm in C.M:
    for i in mm["src"]: ok(i in C.S, "method %s cites unknown source %s" % (mm["id"], i))
    if not mm["src"]: ok(mm["status"] == "unverified" and mm.get("flag") in C.F, "method %s has no source but is not flagged unverified" % mm["id"])
    if mm["kind"] == "prohibited": ok(not any(st[0] == mm["id"] for st in C.STEPS), "prohibited method %s has steps" % mm["id"])
for mid, title, st in C.STEPS:
    ok(any(x["id"] == mid and x["status"] != "prohibited" for x in C.M), "steps for unknown/prohibited method " + mid)
    for t, s in st:
        ok(s and all(i in C.S for i in s), "step without valid source in " + mid)
for group in (C.CN_TAX, C.US_TAX, C.US_PEN):
    for row in group: ok(row[3] and all(i in C.S for i in row[3]), "tax row without source: " + row[0])

# ---- 2. arithmetic, recomputed with exact fractions
m = {k: Fr(v) for k, v in C.MODEL.items() if k != "board_time"}
ASK, BID = m["ask"], m["bid"]; MID = (ASK + BID) / 2
ok(ASK == Fr("6.6851") and BID == Fr("6.6571"), "rate inputs changed without verifier update")
def r2(x):  # round half up to cents
    return "%.2f" % (int(x * 100 + Fr(1, 2)) / 100.0)
def ceil(x): return -((-x.numerator) // x.denominator)
def clamp(x, lo, hi): return max(lo, min(hi, x))
rows = list(csv.DictReader(open(os.path.join(OUT, "data", "costs.csv"), encoding="utf-8")))
ok(len(rows) == 40, "costs.csv must have 40 rows")
exp_all = {}
for i, row in enumerate(rows):
    U = Fr(10000 * (i + 1)); ok(Fr(row["usd"]) == U, "row %d amount" % i)
    P = U * ASK; spread = U * (ASK - MID) / MID
    boc = clamp(m["boc_rate"] * P, m["boc_min"], m["boc_max"]) + m["boc_cable"]
    hs = clamp(m["hsbc_rate"] * P, m["hsbc_min"], m["hsbc_max"]) + m["hsbc_cable"]
    cc = clamp(m["ccb_rate"] * P, m["ccb_min"], m["ccb_max"]) + m["ccb_cable"]
    at_mid = U * MID; n_full = at_mid // m["atm_day_cny"]; rem = at_mid - n_full * m["atm_day_cny"]
    atm = n_full * min(m["atm_max"], m["atm_fix"] + m["atm_pct"] * m["atm_day_cny"]) + (min(m["atm_max"], m["atm_fix"] + m["atm_pct"] * rem) if rem else 0)
    t20 = U * m["tax_flat"]
    exp = {"cny_principal": r2(P), "spread": r2(spread), "boc_fee_cny": r2(boc), "boc_fee_usd": r2(boc / MID),
           "boc_std": r2(spread + boc / MID + m["chase_in"]), "boc_full": r2(spread + boc / MID + m["chase_in"] + m["boc_full_usd"]),
           "boc_cny_needed": r2(P + boc), "hsbc_fee_cny": r2(hs), "hsbc_fee_usd": r2(hs / MID), "ccb_fee_cny": r2(cc), "ccb_fee_usd": r2(cc / MID),
           "wise_n": str(ceil(at_mid / m["wise_cap_cny"])), "atm_years": str(ceil(at_mid / m["atm_year_cny"])), "atm_n": str(int(n_full) + (1 if rem else 0)),
           "atm_fee_cny": r2(atm), "atm_fee_usd": r2(atm / MID), "cash_trips5": str(ceil(U / m["cash_nopermit"])), "cash_trips10": str(ceil(U / m["cash_permit"])),
           "tax20": r2(t20), "tax_lo": r2(U * m["tax_lo"]), "tax_hi": r2(U * m["tax_hi"]), "late_year": r2(t20 * m["late_day"] * 365),
           "pen_lo": r2(t20 * m["pen_lo"]), "pen_hi": r2(t20 * m["pen_hi"]), "fine30": r2(U * m["fx_fine"]), "fine100": r2(U), "cash20": r2(U * m["cash_fine"]),
           "fbar_w": r2(max(m["fbar_w_base"], U * m["fbar_w_pct"]))}
    exp_all[int(U)] = exp
    for k, v in exp.items(): ok(row[k] == v, "costs.csv row $%d %s: file %s, recomputed %s" % (U, k, row[k], v))
    # identities
    ok(abs(Fr(row["boc_std"]) - (Fr(row["spread"]) + Fr(row["boc_fee_usd"]) + 15)) <= Fr(2, 100), "sum identity row $%d" % U)
j = json.load(open(os.path.join(OUT, "data", "costs.json"), encoding="utf-8"))
ok(j["rows"] == [{k: (int(v) if k in ("wise_n", "atm_years", "atm_n", "cash_trips5", "cash_trips10") else v) for k, v in r.items()} for r in rows], "costs.json differs from costs.csv")

# ---- 3. audit claim R05: recompute the legacy EXECUTIVE_SUMMARY fee table at its own rate (6.6903)
legacy = {10000: ("216.90", "220.00"), 20000: ("283.81", "253.81"), 30000: ("350.71", "320.71"), 40000: ("410.00", "387.61"), 400000: ("410.00", "620.00")}
for U, (b, h) in legacy.items():
    P = Fr(U) * Fr("6.6903")
    ok(r2(clamp(P / 1000, 50, 260) + 150) == b and r2(clamp(P / 1000, 100, 500) + 120) == h, "R05 legacy fee recomputation mismatch at $%d" % U)
es = os.path.join(ROOT, "EXECUTIVE_SUMMARY.md")
if os.path.exists(es):
    t = open(es, encoding="utf-8").read()
    if "669.03" in t:  # only assert while the reviewed text is still in place
        for U, (b, h) in legacy.items(): ok(b in t and h in t, "R05: figure %s/%s not found in EXECUTIVE_SUMMARY.md" % (b, h))

# ---- 3b. audit claim R15: Edition L's ladder L1 differs from ours only by the fee-conversion convention
el = os.path.join(ROOT, "edition-l", "data", "costs.csv")
if os.path.exists(el):
    L = {int(r["target_usd"]): r for r in csv.DictReader(open(el, encoding="utf-8")) if r["ladder"] == "L1"}
    if L.get(10000, {}).get("known_total_usd") == "68.42":  # only while the reviewed data is in place
        for U in (10000, 400000):
            ours = exp_all[U]; theirs = L[U]
            ok(theirs["fx_half_spread_usd"] == ours["spread"], "R15: margin differs from Edition L at $%d" % U)
            ok(abs(Fr(theirs["sender_usd"]) - Fr(ours["boc_fee_cny"]) / ASK) <= Fr(1, 100), "R15: Edition L fee is not our CNY fee at the selling rate at $%d" % U)
            ok(Fr(ours["boc_std"]) - Fr(theirs["known_total_usd"]) <= Fr(15, 100), "R15: totals differ by more than 15 cents at $%d" % U)
        ok(L[400000]["known_total_usd"] == "915.77", "R15: Edition L $400,000 total is not 915.77")

# ---- 4. generated HTML: every table row has a source link; blanks are flagged; links resolve
class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.rows = []; s.cur = None; s.cell = None; s.ids = set(); s.links = []; s.in_tbody = False; s.h1 = 0; s.viewport = False; s.title = ""; s._t = False
    def handle_starttag(s, tag, a):
        a = dict(a)
        if "id" in a: s.ids.add(a["id"])
        if tag == "tbody": s.in_tbody = True
        if tag == "tr" and s.in_tbody: s.cur = {"cells": [], "links": [], "cls": a.get("class", ""), "id": a.get("id")}
        if tag == "td" and s.cur is not None: s.cell = {"text": "", "label": a.get("data-label"), "unv": False, "flag": False}
        if tag == "a" and "href" in a:
            s.links.append(a["href"])
            if s.cur is not None: s.cur["links"].append((a["href"], a.get("class", "")))
            if s.cell is not None and a.get("class") == "f": s.cell["flag"] = True
        if tag == "span" and a.get("class") == "unv" and s.cell is not None: s.cell["unv"] = True
        if tag == "h1": s.h1 += 1
        if tag == "meta" and a.get("name") == "viewport": s.viewport = True
        if tag == "title": s._t = True
        if tag == "link" and a.get("rel") == "stylesheet": s.links.append(a["href"])
        if tag in ("script", "img", "iframe"): s.links.append("EXTERNAL-ASSET:" + tag)
    def handle_endtag(s, tag):
        if tag == "tbody": s.in_tbody = False
        if tag == "td" and s.cell is not None: s.cur["cells"].append(s.cell); s.cell = None
        if tag == "tr" and s.cur is not None: s.rows.append(s.cur); s.cur = None
        if tag == "title": s._t = False
    def handle_data(s, d):
        if s.cell is not None: s.cell["text"] += d
        if s._t: s.title += d
pages = sorted(f for f in os.listdir(OUT) if f.endswith(".html"))
ok(pages == sorted(["index.html", "methods.html", "costs.html", "steps.html", "taxes.html", "flagged.html", "sources.html", "review.html"]), "unexpected page set: %s" % pages)
parsed = {}; total_rows = 0; total_blank = 0
urls = {v["u"] for v in C.S.values()}
for f in pages:
    p = P(); p.feed(open(os.path.join(OUT, f), encoding="utf-8").read()); parsed[f] = p
    ok(p.h1 == 1 and p.viewport and p.title.strip(), "%s: needs one h1, viewport meta, title" % f)
    ok(not any(l.startswith("EXTERNAL-ASSET") for l in p.links), "%s: scripts/images/iframes are not allowed" % f)
    for r in p.rows:
        total_rows += 1
        ext = [h for h, c in r["links"] if h.startswith("http")]
        offic = [h for h in ext if h in urls]
        repo = [h for h in ext if urlparse(h).netloc == REPO_HOST]
        if "nosrc" in r["cls"]:
            ok(any(c["unv"] for c in r["cells"]), "%s: row marked nosrc lacks the 'unverified' marker" % f)
        elif f == "review.html":
            ok(offic or repo, "%s: review row without evidence link: %s" % (f, r["cells"][0]["text"]))
        else:
            ok(offic, "%s: table row without official source link: %s" % (f, r["cells"][0]["text"][:50]))
        for h in ext:
            ok(h in urls or urlparse(h).netloc == REPO_HOST, "%s: external link not in source registry: %s" % (f, h))
        for c in r["cells"]:
            ok(c["label"], "%s: cell without data-label (mobile layout)" % f)
            if c["unv"]:
                total_blank += 1
                ok(c["flag"] or "nosrc" in r["cls"], "%s: unverified cell without a flag link" % f)
                ok(not re.search(r"[$¥]\s?\d", c["text"]), "%s: unverified cell carries a number: %s" % (f, c["text"]))
            else:
                ok(c["text"].strip() != "", "%s: empty cell without 'unverified' marker in row %s" % (f, r["cells"][0]["text"][:40]))
for f, p in parsed.items():
    for l in p.links:
        if l.startswith(("http", "mailto:", "EXTERNAL")): continue
        path, _, frag = l.partition("#")
        tgt = os.path.normpath(os.path.join(OUT, path)) if path else os.path.join(OUT, f)
        ok(os.path.exists(tgt), "%s: broken local link %s" % (f, l))
        if frag and os.path.exists(tgt) and tgt.endswith(".html") and os.path.dirname(tgt) == OUT:
            ok(frag in parsed[os.path.basename(tgt)].ids, "%s: missing anchor %s" % (f, l))

# ---- 5. published figures on the pages equal the recomputed ones (spot rows on the landing page and every cost row)
def money(x): return "$" + format(float(x), ",.2f")
idx = open(os.path.join(OUT, "index.html"), encoding="utf-8").read()
for U in (10000, 50000, 100000, 200000, 300000, 400000): ok(money(exp_all[U]["boc_std"]) in idx, "index.html missing recomputed total for $%d" % U)
cost_rows = [r for r in parsed["costs.html"].rows if r["cells"] and r["cells"][1]["label"] == "Total estimated cost" and len(r["cells"]) == 10]
ok(len(cost_rows) == 40, "costs.html BOC standard table must have 40 rows")
for i, r in enumerate(cost_rows):
    e_ = exp_all[10000 * (i + 1)]
    ok(r["cells"][1]["text"] == money(e_["boc_std"]) and r["cells"][3]["text"] == money(e_["spread"]) and r["cells"][4]["text"] == money(e_["boc_fee_usd"]), "costs.html row %d differs from recomputation" % i)
    ok(r["cells"][7]["unv"], "costs.html: intermediary cell must stay blank/flagged")
n40 = sum(1 for r in parsed["costs.html"].rows if r["cells"][0]["text"].startswith("$"))
ok(n40 == 8 * 40, "costs.html: expected 8 tables x 40 amount rows, found %d" % n40)

# ---- 6. no prohibited-route instructions; determinism
steps_html = open(os.path.join(OUT, "steps.html"), encoding="utf-8").read().lower()
for w in ("underground", "crypto", "stablecoin", "borrowed quota"): ok(w not in steps_html, "steps.html mentions prohibited route: " + w)
snap = {f: open(os.path.join(OUT, f), "rb").read() for f in pages}
subprocess.run([sys.executable, os.path.join(HERE, "build.py")], check=True, stdout=subprocess.DEVNULL)
ok(all(open(os.path.join(OUT, f), "rb").read() == b for f, b in snap.items()), "build is not deterministic or outputs are stale")

print("Edition M verify: %d checks, %d table rows, %d blank+flagged cells, %d sources (%d read in full), %d flags" % (
    checks, total_rows, total_blank, len(C.S), sum(v["how"] == "full" for v in C.S.values()), len(C.F)))
if fails:
    print("FAILED (%d):" % len(fails)); [print(" -", x) for x in fails[:60]]; sys.exit(1)
print("PASS")
