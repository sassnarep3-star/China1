#!/usr/bin/env python3
"""Verify the China Money guide. Standard library only; exits non-zero on any failure.

 1. build.py is deterministic (rebuild leaves every generated file byte-identical)
 2. every table row on every guide page links to an official source host
 3. every blank cell points to an entry on the Flagged for Review page
 4. the cost ladder is recomputed independently (Fraction arithmetic) and compared
 5. data cross-checks: quoted figures in sources.json match prices.json
 6. every HTML file in the repository is crawled for broken internal links
 7. page hygiene: viewport, data-label on every cell, no scripts, no external assets
"""
import csv
import hashlib
import json
import re
import subprocess
import sys
from fractions import Fraction as F
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "guide"
DATA = GUIDE / "data"
PAGES = [ROOT / "index.html"] + [GUIDE / f"{n}.html" for n in
         ("summary", "methods", "costs", "steps", "taxes", "flagged", "sources", "repo-review", "archive")]
GENERATED = PAGES + [DATA / "cost-ladder.csv", ROOT / "EXECUTIVE_SUMMARY.md"]
problems = []


def check(cond, msg):
    if not cond:
        problems.append(msg)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


# 1 ------------------------------------------------------------------ deterministic build
for p in GENERATED:
    check(p.is_file(), f"missing generated file {p.relative_to(ROOT)}")
if problems:
    print("\n".join(problems)); sys.exit(1)
before = {p: digest(p) for p in GENERATED}
subprocess.run([sys.executable, str(GUIDE / "build" / "build.py")], check=True, capture_output=True)
for p in GENERATED:
    check(digest(p) == before[p], f"{p.relative_to(ROOT)} is stale: run guide/build/build.py and commit")

sources = {s["id"]: s for s in load("sources.json")["sources"]}
flags_doc = load("flagged.json")["items"]
flags = {f["id"]: f for f in flags_doc}
methods = load("methods.json")["methods"]
prices = load("prices.json")
taxes = load("taxes.json")
review = load("review.json")
scan = load("scan.json")

OFFICIAL = {urlsplit(s["url"]).netloc for s in sources.values()}
MANUAL = {urlsplit(m["url"]).netloc for f in flags_doc for m in f.get("manual", [])}
for s in sources.values():
    check(s["url"].startswith("https://"), f"source {s['id']} is not https")
    check(s["level"] in ("full", "excerpt"), f"source {s['id']} has unknown level")
    check(len(s["quote"]) > 20, f"source {s['id']} has no quoted text")

# reference integrity
def refs_ok(where, src, fl=()):
    for sid in src:
        check(sid in sources, f"{where}: unknown source {sid}")
    for fid in fl:
        check(fid in flags, f"{where}: unknown flag {fid}")

used = set()
for m in methods:
    refs_ok(m["id"], m["src"], m["flags"]); used.update(m["src"])
    check(m["src"], f"{m['id']} has no source")
    for st in m["steps"]:
        check(st["src"], f"{m['id']} step without source: {st['t'][:40]}")
        refs_ok(m["id"], st["src"]); used.update(st["src"])
    if m["cat"] == "prohibited":
        check(not m["steps"], f"{m['id']} is prohibited but has steps")
    else:
        check(m["steps"], f"{m['id']} has no steps")
        for field in ("cost", "limit"):
            if not m[field]:
                check(m["flags"], f"{m['id']} has blank {field} but no flag")
for group, items in taxes.items():
    for it in items:
        check(it["figure"] or it["flags"], f"taxes/{group}: blank figure without a flag: {it['item']}")
        check(it["src"], f"taxes/{group}: row without source: {it['item']}")
        refs_ok(f"taxes/{group}", it["src"], it["flags"]); used.update(it["src"])
for f in flags_doc:
    check(f["src"], f"{f['id']} has no source link"); refs_ok(f["id"], f["src"]); used.update(f["src"])
for r in review["rules"] + review["manual"]:
    check(r["src"], "review row without source"); refs_ok("review", r["src"]); used.update(r["src"])
for k in ("boc", "hsbc", "atm", "receiving", "wise", "cash", "penalty"):
    refs_ok(f"prices/{k}", prices[k]["src"]); used.update(prices[k]["src"])
for sid, s in sources.items():
    if s["level"] == "excerpt":
        check(any(sid in f["src"] for f in flags_doc), f"excerpt-only source {sid} is not flagged")
check(len(methods) >= 15, "fewer than 15 methods")

# 5 ------------------------------------------------------------------ figures match quoted text
q = sources["CN-FXBOARD"]["quote"]
check(prices["boc_buy_per_100"] in q and prices["boc_sell_per_100"] in q, "board figures not in CN-FXBOARD quote")
q = sources["CN-BOCTARIFF"]["quote"]
for needle in ("1‰", "最低收取50元", "最高收取260元", "国际发电150元", "25美元", "12元+取现金额的1%", "最高112元"):
    check(needle in q, f"BOC tariff quote lacks {needle}")
q = sources["PR-HSBC"]["quote"]
for needle in ("0.1%", "最低人民币100元", "最高人民币500元", "人民币120元", "人民币200元"):
    check(needle in q, f"HSBC quote lacks {needle}")
q = sources["PR-WISEFEE"]["quote"].replace(",", "")
for qt in prices["wise"]["quotes"]:
    for v in (qt["send_cny"], qt["fee_cny"], qt["received_usd"]):
        check(v in q, f"Wise quote figure {v} not in PR-WISEFEE quote")
check("$15 per transfer" in sources["US-CHASE"]["quote"], "Chase quote lacks $15")
check("16,536" in sources["US-FBARPEN"]["quote"] and "165,353" in sources["US-FBARPEN"]["quote"], "FBAR penalty quote")
check("30%以下" in sources["CN-FXREG"]["quote"] and "20%以下" in sources["CN-FXREG"]["quote"], "FX Regulation quote")
check("10万元人民币" in sources["CN-CARD"]["quote"] and "1万元人民币" in sources["CN-CARD"]["quote"], "card rule quote")
check("$200" in sources["US-988"]["quote"], "988 quote")

# 4 ------------------------------------------------------------------ independent recomputation
buy, sell = F(prices["boc_buy_per_100"]) / 100, F(prices["boc_sell_per_100"]) / 100
mid = (buy + sell) / 2
targets = list(range(10_000, 400_001, 10_000))
rows = list(csv.DictReader((DATA / "cost-ladder.csv").open(encoding="utf-8")))
by = {(r["method_id"], int(r["amount_usd"])): r for r in rows}
check(len(rows) == len(methods) * 40, f"cost ladder has {len(rows)} rows, expected {len(methods) * 40}")
for m in methods:
    check([int(r["amount_usd"]) for r in rows if r["method_id"] == m["id"]] == targets, f"{m['id']} ladder is not 40 exact $10,000 steps")


def boc_total(n):
    held = n * mid
    comm = max(F(50), min(F(260), held / 1000))
    return n * (1 - mid / sell) + (comm + 150) / sell + 25 + 15


recomputed = 0
wise = {F(x["send_cny"]): F(x["received_usd"]) for x in prices["wise"]["quotes"]}
for m in methods:
    for n in targets:
        r = by[(m["id"], n)]
        model = m["ladder"]
        exp_status, exp_total = None, None
        if model == "boc" or (model == "pr_quota" and n <= 50_000):
            exp_status, exp_total = "value", boc_total(n)
        elif model == "pr_quota":
            exp_status = "na"
        elif model in ("hsbc", "rmb"):
            exp_status = "partial"
        elif model == "wise":
            if n * mid in wise:
                exp_status, exp_total = "value", n - wise[n * mid]
            else:
                exp_status = "blank"
        elif model == "cash":
            exp_status, exp_total = ("value", n * (1 - mid / sell)) if n <= 10_000 else ("na", None)
        elif model == "atm":
            exp_status = "partial" if n * mid <= 100_000 else "na"
        elif model == "penalty":
            exp_status, exp_total = "penalty", F(n) * F(3, 10)
        elif model == "crypto":
            exp_status = "na"
        elif model == "blank":
            exp_status = "blank"
        check(r["status"] == exp_status, f"{m['id']} ${n}: status {r['status']} != {exp_status}")
        if exp_total is None:
            check(r["total_cost_usd"] == "" and r["share_of_amount"] == "", f"{m['id']} ${n}: total should be blank")
        else:
            check(abs(F(r["total_cost_usd"]) - exp_total) <= F(1, 100), f"{m['id']} ${n}: total {r['total_cost_usd']} != {float(exp_total):.4f}")
            recomputed += 1
        if r["status"] in ("blank", "partial"):
            check(r["flags"], f"{m['id']} ${n}: blank total without a flag")
            for fid in r["flags"].split():
                check(fid in flags, f"{m['id']} ${n}: unknown flag {fid}")
        check(r["source_urls"].startswith("https://"), f"{m['id']} ${n}: no source url")
# HSBC and ATM verified components inside the detail text
h10 = by[("M02", 10_000)]["made_up_of"]
check("CNY 420.00" in h10, "HSBC $10,000 fee component should be CNY 420.00 (100 + 120 + 200)")
h400 = by[("M02", 400_000)]["made_up_of"]
check("CNY 820.00" in h400, "HSBC $400,000 fee component should be CNY 820.00 (500 + 120 + 200)")
a10 = by[("M13", 10_000)]["made_up_of"]
check("CNY 751.11" in a10, "ATM $10,000 fee should be CNY 751.11 (6 × 112 + 12 + 1% × 6,711)")

# 2, 3, 7 ------------------------------------------------------------ page checks
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.rows, self.tags = [], set(), [], []
        self.in_tbody = self.in_tr = False
        self.cur = None
        self.viewport = False
        self.td_without_label = 0
        self.assets = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = True
        if tag in ("script", "iframe", "object", "embed"):
            self.assets.append(tag)
        if tag in ("img", "link") and (a.get("src") or a.get("href")):
            self.assets.append(f"{tag}:{a.get('src') or a.get('href')}")
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.cur = {"hrefs": [], "blank": False, "flag": False}
        if tag == "td" and self.cur is not None and not a.get("data-label"):
            self.td_without_label += 1
        if tag == "span" and "blank" in (a.get("class") or "").split() and self.cur is not None:
            self.cur["blank"] = True
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.cur is not None:
                self.cur["hrefs"].append(a["href"])
                if "flagged.html#F" in a["href"]:
                    self.cur["flag"] = True

    def handle_endtag(self, tag):
        if tag == "tr" and self.cur is not None:
            self.rows.append(self.cur); self.cur = None
        if tag == "tbody":
            self.in_tbody = False


parsed, total_rows, blank_cells = {}, 0, 0
for p in PAGES:
    pg = Page(); text = p.read_text(encoding="utf-8"); pg.feed(text); parsed[p] = pg
    rel = p.relative_to(ROOT)
    check(pg.viewport, f"{rel}: no viewport meta")
    check(not pg.assets, f"{rel}: scripts or external assets present: {pg.assets[:3]}")
    check(pg.td_without_label == 0, f"{rel}: {pg.td_without_label} cells without data-label")
    check(text.count("<h1") == 1, f"{rel}: must have exactly one h1")
    for r in pg.rows:
        total_rows += 1
        hosts = {urlsplit(h).netloc for h in r["hrefs"] if h.startswith("https://")}
        check(hosts & OFFICIAL, f"{rel}: table row without an official source link")
        check(hosts <= (OFFICIAL | MANUAL), f"{rel}: table row links a non-official host {hosts - OFFICIAL - MANUAL}")
        if r["blank"]:
            blank_cells += 1
            check(r["flag"] or p.name == "flagged.html", f"{rel}: blank cell without a Flagged link")
    for h in pg.links:
        check(not h.startswith("http://"), f"{rel}: insecure link {h}")

fl = parsed[GUIDE / "flagged.html"]
for fid in flags:
    check(fid in fl.ids, f"flagged.html lacks anchor {fid}")
check(len(fl.rows) >= len(flags), "flagged.html has fewer rows than flagged items")
src_pg = parsed[GUIDE / "sources.html"]
for sid in sources:
    check(sid in src_pg.ids, f"sources.html lacks {sid}")
    check(sid in used, f"source {sid} is never used")
home = (ROOT / "index.html").read_text(encoding="utf-8")
for p in PAGES[1:]:
    check(f'href="guide/{p.name}"' in home, f"landing page does not link guide/{p.name}")
costs = parsed[GUIDE / "costs.html"]
for m in methods:
    check(f"L-{m['id']}" in costs.ids, f"costs.html lacks ladder for {m['id']}")
    check(m["id"] in parsed[GUIDE / "methods.html"].ids, f"methods.html lacks {m['id']}")
    if m["cat"] != "prohibited":
        check(m["id"] in parsed[GUIDE / "steps.html"].ids, f"steps.html lacks {m['id']}")
check(len(costs.rows) == 40 + 9 + len(methods) * 40, f"costs.html has {len(costs.rows)} rows")

# review snapshot sanity
check(scan["total_lines"] > 100_000 and scan["total_files"] > 300, "scan snapshot looks incomplete")
for r in review["rules"]:
    check(r["id"] in scan["rules"], f"scan snapshot lacks rule {r['id']}")
    re.compile(r["pattern"])

# 6 ------------------------------------------------------------------ whole-repository link crawl
class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("name"):
            self.ids.add(a["name"])
        for k in ("href", "src"):
            if a.get(k) and tag in ("a", "link", "img", "script"):
                self.links.append(a[k])


html_files = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)
cache, local_refs = {}, 0
for p in html_files:
    lk = Links(); lk.feed(p.read_text(encoding="utf-8", errors="replace")); cache[p] = lk
for p, lk in cache.items():
    for h in lk.links:
        u = urlsplit(h)
        if u.scheme or h.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "//")) or not u.path:
            if h.startswith("#") and len(h) > 1 and p in PAGES:
                check(unquote(h[1:]) in lk.ids, f"{p.relative_to(ROOT)}: missing fragment {h}")
            continue
        dest = (p.parent / unquote(u.path)).resolve()
        if dest.is_dir():
            dest = dest / "index.html"
        local_refs += 1
        if not (dest.is_relative_to(ROOT) and dest.exists()):
            problems.append(f"{p.relative_to(ROOT)}: broken link {h}")
            continue
        if u.fragment and p in PAGES and dest in cache:
            check(unquote(u.fragment) in cache[dest].ids, f"{p.relative_to(ROOT)}: missing fragment {h}")

# root documents
req = (ROOT / "REQUIREMENTS.md").read_text(encoding="utf-8")
check("Final integration" in req, "REQUIREMENTS.md must keep the 'Final integration' heading")
check((ROOT / "legacy-portal.html").is_file(), "legacy-portal.html missing")
for x in load("archive.json")["entries"]:
    check((ROOT / x["href"]).is_file(), f"archive entry points to a missing file: {x['href']}")

if problems:
    print(f"FAIL: {len(problems)} problem(s)")
    for x in problems[:60]:
        print(" -", x)
    sys.exit(1)
print(f"PASS: {len(PAGES)} pages; {total_rows} table rows, each with an official source link; "
      f"{blank_cells} rows with blank cells, each linked to Flagged for Review; "
      f"{len(methods)} methods × 40 amounts = {len(rows)} ladder rows, {recomputed} totals recomputed independently; "
      f"{len(sources)} sources, {len(flags)} flagged items; "
      f"{len(html_files)} HTML files / {local_refs} internal links crawled, none broken; deterministic rebuild.")
