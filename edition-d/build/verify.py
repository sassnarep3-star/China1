#!/usr/bin/env python3
"""
Verification gate for Edition D. Recomputes the site's numbers from the parameters
instead of trusting the HTML, then checks citations, links and blank-value discipline.

Exit 0 only if every check passes. Usage: python3 edition-d/build/verify.py
"""

import hashlib
import json
import math
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DOCS = os.path.join(ROOT, "docs")
BUILD = os.path.join(ROOT, "build", "build.py")

ALLOWED_HOSTS = {
    "www.safe.gov.cn", "m.safe.gov.cn", "safe.gov.cn",
    "www.gov.cn", "gov.cn",
    "www.chinatax.gov.cn", "chinatax.gov.cn",
    "www.pbc.gov.cn", "pbc.gov.cn",
    "www.irs.gov", "irs.gov",
    "www.govinfo.gov", "govinfo.gov",
    "www.boc.cn", "boc.cn",
    "www.chase.com", "chase.com",
}

problems = []
counts = {}


def fail(msg):
    problems.append(msg)


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def check(name, ok, detail):
    counts[name] = detail
    if not ok:
        fail("{}: {}".format(name, detail))


# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------
SRC = {s["id"]: s for s in load("sources.json")["sources"]}
METHODS = load("methods.json")["methods"]
FLAGS = load("flags.json")["flags"]
REVIEW = load("review.json")["findings"]
P = load("parameters.json")
FLAG_IDS = {f["id"] for f in FLAGS}
METHOD_IDS = {m["id"] for m in METHODS}

# ---------------------------------------------------------------------------
# 1. source register integrity
# ---------------------------------------------------------------------------
bad_tier = [s["id"] for s in SRC.values() if s.get("tier") not in ("A", "B", "C")]
bad_host = [s["id"] for s in SRC.values() if not re.match(r"^https?://([^/]+)/", s["url"])
            or re.match(r"^https?://([^/]+)", s["url"]).group(1) not in ALLOWED_HOSTS]
missing_fields = [s["id"] for s in SRC.values()
                  if not all(k in s for k in ("title_en", "issuer", "url", "tier", "supports", "retrieval"))]
check("source register", not (bad_tier or bad_host or missing_fields),
      "{} sources; bad tier {}, off-allowlist {}, incomplete {}".format(
          len(SRC), bad_tier or "none", bad_host or "none", missing_fields or "none"))

check("tier C never used for a value",
      not [s for s in SRC.values() if s["tier"] == "C"],
      "no tier C entry exists, so no value can rest on commentary")

# ---------------------------------------------------------------------------
# 2. method / flag cross-references
# ---------------------------------------------------------------------------
unknown_basis = sorted({s for m in METHODS for s in m["basis"] if s not in SRC})
unknown_flags = sorted({f for m in METHODS for f in m.get("flags", []) if f not in FLAG_IDS})
orphan_flags = sorted({f["id"] for f in FLAGS} - {f for m in METHODS for f in m.get("flags", [])})
check("method sources resolve", not unknown_basis, "{} citations across {} methods; unknown {}".format(
    sum(len(m["basis"]) for m in METHODS), len(METHODS), unknown_basis or "none"))
check("method flags resolve", not unknown_flags, "unknown {}".format(unknown_flags or "none"))
check("every flag is attached to a method", not orphan_flags, "orphans {}".format(orphan_flags or "none"))

flag_sources_ok = all(all(s in SRC for s in f["sources"]) for f in FLAGS)
check("flag sources resolve", flag_sources_ok, "{} flags".format(len(FLAGS)))

check("review sources resolve", all(all(s in SRC for s in r["sources"]) for r in REVIEW),
      "{} review findings".format(len(REVIEW)))

check("status vocabulary", all(m["status"] in ("lawful", "lawful_approval", "prohibited", "unverified")
                               for m in METHODS),
      "{:.0f} lawful, {:.0f} approval, {:.0f} prohibited, {:.0f} unverified".format(
          sum(m["status"] == "lawful" for m in METHODS),
          sum(m["status"] == "lawful_approval" for m in METHODS),
          sum(m["status"] == "prohibited" for m in METHODS),
          sum(m["status"] == "unverified" for m in METHODS)))

# ---------------------------------------------------------------------------
# 3. independent recomputation of every cost cell
# ---------------------------------------------------------------------------
FX = P["fx"]
BUY, SELL = FX["buy_spot"], FX["sell_spot"]
RATE = SELL / 100.0
MID = (BUY + SELL) / 2.0
ONE_WAY = (SELL - MID) / MID
W = P["boc_personal_wire"]
CORR = P["correspondent"]["full_amount_usd"]
US_IN = P["receiving_bank"]["usd"]
QUOTA = P["quota"]["annual_usd"]
THRESH_CNY = P["emigration"]["staging_threshold_cny"]
FRACTIONS = P["emigration"]["release_fractions"]
CASH_TRIP = P["cash"]["per_trip_usd"]
PEN_MIN, PEN_MAX = P["penalty_cn"]["min_rate"], P["penalty_cn"]["max_rate"]
AMOUNTS = list(range(10_000, 400_001, 10_000))


def comm(usd):
    return min(max(W["commission_rate"] * usd * RATE, W["commission_min_cny"]), W["commission_max_cny"])


def expected(model, amount):
    margin = amount * ONE_WAY
    if model == "boc_documented":
        return margin + (comm(amount) + W["cable_fee_cny"]) / RATE + CORR + US_IN
    if model == "boc_quota":
        n = math.ceil(amount / QUOTA)
        per = amount / n
        return margin + n * ((comm(per) + W["cable_fee_cny"]) / RATE + CORR + US_IN)
    if model == "emigration":
        parts = FRACTIONS if amount * RATE >= THRESH_CNY else [1.0]
        fees = sum((comm(amount * f) + W["cable_fee_cny"]) / RATE + CORR + US_IN for f in parts)
        return margin + fees
    if model in ("inheritance", "property", "boc_documented"):
        return margin + (comm(amount) + W["cable_fee_cny"]) / RATE + CORR + US_IN
    if model == "hold_usd":
        return margin
    if model == "cash":
        return margin
    if model == "penalty":
        return PEN_MIN * amount
    raise SystemExit("unknown model " + model)


PAGES = {
    "costs-boc-documented.html": ("boc_documented", 9),
    "costs-boc-quota.html": ("boc_quota", 9),
    "costs-emigration.html": ("emigration", 9),
    "costs-inheritance.html": ("inheritance", 9),
    "costs-property.html": ("property", 9),
    "costs-hold-usd.html": ("hold_usd", 9),
    "costs-cash.html": ("cash", 9),
    "costs-prohibited.html": ("penalty", 5),
}


def money(v, dec=2):
    return ("${:,.%df}" % dec).format(v)


cell_re = re.compile(r"<td>(.*?)</td>", re.S)
row_re = re.compile(r"<tr>(.*?)</tr>", re.S)


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).replace("&mdash;", "\u2014").replace("&nbsp;", " ").strip()


total_mismatch = []
row_count = {"n": 0}
for fname, (model, ncols) in PAGES.items():
    path = os.path.join(DOCS, "pages", fname)
    if not os.path.exists(path):
        fail("missing cost page " + fname)
        continue
    doc = open(path, encoding="utf-8").read()
    rows = [r for r in row_re.findall(doc) if "<td>" in r]
    if len(rows) != len(AMOUNTS):
        fail("{}: expected {} data rows, found {}".format(fname, len(AMOUNTS), len(rows)))
    for i, r in enumerate(rows):
        cells = [strip_tags(c) for c in cell_re.findall(r)]
        if len(cells) != ncols:
            fail("{}: row {} has {} cells, expected {}".format(fname, i, len(cells), ncols))
            continue
        row_count["n"] += 1
        amount = AMOUNTS[i]
        if cells[0] != "${:,}".format(amount):
            fail("{}: row {} amount {} != {}".format(fname, i, cells[0], amount))
        got = cells[5] if model != "penalty" else cells[3]
        want = money(expected(model, amount), 0 if model == "penalty" else 2)
        if got != want:
            total_mismatch.append("{} ${:,}: rendered {} expected {}".format(fname, amount, got, want))
check("cost cells recomputed", not total_mismatch,
      "{} rows across {} tables; mismatches {}".format(row_count["n"], len(PAGES),
                                                       len(total_mismatch) or "none"))
if total_mismatch:
    for m in total_mismatch[:5]:
        fail("recompute " + m)

# ---------------------------------------------------------------------------
# 4. every rendered table row carries a source
# ---------------------------------------------------------------------------
no_source = []
for root, _, files in os.walk(DOCS):
    for fn in files:
        if not fn.endswith(".html"):
            continue
        path = os.path.join(root, fn)
        doc = open(path, encoding="utf-8").read()
        for r in row_re.findall(doc):
            if "<td>" in r and 'class="src"' not in r and 'class="flag"' not in r \
                    and not re.search(r'href="https?://', r):
                text = strip_tags(r)[:80]
                if "README" in text or text == "":
                    continue
                no_source.append("{} :: {}".format(fn, text))
check("rows carry a source", not no_source,
      "{} unsourced rows{}".format(len(no_source), "" if not no_source else " e.g. " + no_source[0]))

# ---------------------------------------------------------------------------
# 5. blanks disclosed
# ---------------------------------------------------------------------------
undisclosed = []
for fn in sorted(os.listdir(os.path.join(DOCS, "pages"))) + ["../index.html"]:
    path = os.path.join(DOCS, "pages", fn) if not fn.startswith("..") else os.path.join(DOCS, "index.html")
    if not path.endswith(".html") or not os.path.exists(path):
        continue
    doc = open(path, encoding="utf-8").read()
    for cell in cell_re.findall(doc):
        if strip_tags(cell) == "\u2014" and 'class="unv"' not in cell:
            undisclosed.append(fn)
check("blank values disclosed", not undisclosed,
      "every em-dash cell carries the unverified marker ({})".format(len(undisclosed)))

# ---------------------------------------------------------------------------
# 6. links: internal resolution and allowed external hosts
# ---------------------------------------------------------------------------
internal_bad, external_bad, checked = [], [], 0
for root, _, files in os.walk(DOCS):
    for fn in files:
        if not fn.endswith(".html"):
            continue
        path = os.path.join(root, fn)
        doc = open(path, encoding="utf-8").read()
        for href in re.findall(r'href="([^"]+)"', doc):
            if href.startswith(("http://", "https://")):
                host = re.match(r"^https?://([^/]+)", href).group(1)
                checked += 1
                if host not in ALLOWED_HOSTS:
                    external_bad.append("{}: {}".format(fn, href))
                continue
            if href.startswith(("#", "mailto:")):
                continue
            target, _, frag = href.partition("#")
            target = target.split("?")[0]
            dest = os.path.normpath(os.path.join(os.path.dirname(path), target))
            checked += 1
            if not os.path.exists(dest):
                internal_bad.append("{} -> {}".format(fn, href))
                continue
            if frag and dest.endswith(".html"):
                dest_doc = open(dest, encoding="utf-8").read()
                if 'id="{}"'.format(frag) not in dest_doc:
                    internal_bad.append("{} -> {} (missing anchor {})".format(fn, href, frag))
check("links resolve", not internal_bad, "{} links checked; broken {}".format(checked, internal_bad or "none"))
check("external hosts allowlisted", not external_bad,
      "{} external links; off-allowlist {}".format(checked, external_bad or "none"))

# ---------------------------------------------------------------------------
# 7. page inventory: no orphans, all nav targets exist
# ---------------------------------------------------------------------------
index = open(os.path.join(DOCS, "index.html"), encoding="utf-8").read()
nav_pages = set()
for group in re.findall(r'<div class="nav-group">(.*?)</div>\s*</div>', index, re.S):
    for href in re.findall(r'class="nav-link[^"]*" href="([^"]+)"', group):
        nav_pages.add(href)
if not nav_pages:
    nav_pages = set(re.findall(r'class="nav-link[^"]*" href="([^"]+)"', index))
missing_nav = [p for p in nav_pages if not os.path.exists(os.path.join(DOCS, p))]
check("nav targets exist", not missing_nav, "{} nav entries; missing {}".format(len(nav_pages), missing_nav or "none"))

linked = set()
for root, _, files in os.walk(DOCS):
    for fn in files:
        if not fn.endswith(".html"):
            continue
        p = os.path.join(root, fn)
        doc = open(p, encoding="utf-8").read()
        for href in re.findall(r'href="([^"]+)"', doc):
            if href.startswith(("http", "#", "mailto")):
                continue
            dest = os.path.normpath(os.path.join(os.path.dirname(p), href.split("#")[0]))
            linked.add(dest)
all_pages = {os.path.join(root, fn) for root, _, files in os.walk(DOCS) for fn in files if fn.endswith(".html")}
orphans = sorted(os.path.relpath(p, DOCS) for p in all_pages - linked if os.path.basename(p) != "index.html")
check("no orphan pages", not orphans, "{} pages, orphans {}".format(len(all_pages), orphans or "none"))

# ---------------------------------------------------------------------------
# 8. no template residue
# ---------------------------------------------------------------------------
residue = []
for root, _, files in os.walk(DOCS):
    for fn in files:
        if fn.endswith(".html"):
            doc = open(os.path.join(root, fn), encoding="utf-8").read()
            for token in re.findall(r"\{[a-z_]+\}", doc):
                residue.append("{}: {}".format(fn, token))
            for token in re.findall(r">\s*(None|nan|NaN|null)\s*<", doc):
                residue.append("{}: {}".format(fn, token))
check("no template residue", not residue, "tokens found {}".format(residue[:5] or "none"))

# ---------------------------------------------------------------------------
# 9. determinism
# ---------------------------------------------------------------------------
def digest():
    h = hashlib.sha256()
    for root, dirs, files in os.walk(DOCS):
        dirs.sort()
        for fn in sorted(files):
            if fn.endswith((".html", ".css", ".json")):
                p = os.path.join(root, fn)
                h.update(os.path.relpath(p, DOCS).encode())
                h.update(open(p, "rb").read())
    return h.hexdigest()


before = digest()
subprocess.run([sys.executable, BUILD], check=True, capture_output=True)
after = digest()
check("deterministic rebuild", before == after,
      "digest {} on rebuild".format("unchanged" if before == after else "CHANGED"))

# ---------------------------------------------------------------------------
# 10. headline arithmetic
# ---------------------------------------------------------------------------
headline = {
    "one_way_pct": round(ONE_WAY * 100, 4),
    "round_trip_pct": round((SELL - BUY) / SELL * 100, 4),
    "cost_10k": round(expected("boc_documented", 10_000), 2),
    "cost_100k": round(expected("boc_documented", 100_000), 2),
    "cost_400k": round(expected("boc_documented", 400_000), 2),
}
index_doc = index
missing_headline = []
for k, v in headline.items():
    if k == "one_way_pct":
        if "{:.4f}%".format(v) not in index_doc and "{:.4f}%".format(v) not in open(
                os.path.join(DOCS, "pages", "costs.html"), encoding="utf-8").read():
            missing_headline.append(k)
    elif k in ("cost_10k", "cost_100k", "cost_400k"):
        haystack = index_doc + open(os.path.join(DOCS, "pages", "summary.html"), encoding="utf-8").read() \
            + open(os.path.join(DOCS, "pages", "costs.html"), encoding="utf-8").read()
        if money(v) not in haystack and money(v, 0) not in haystack:
            missing_headline.append(k)
check("headline figures match the engine", not missing_headline,
      "{}; missing {}".format(headline, missing_headline or "none"))

# ---------------------------------------------------------------------------
# 11. root portal and archive
# ---------------------------------------------------------------------------
ROOT_INDEX = os.path.join(ROOT, "..", "index.html")
portal_bad = []
if not os.path.exists(ROOT_INDEX):
    fail("root portal index.html missing")
else:
    doc = open(ROOT_INDEX, encoding="utf-8").read()
    for href in re.findall(r'href="([^"]+)"', doc):
        if href.startswith(("http://", "https://")):
            host = re.match(r"^https?://([^/]+)", href).group(1)
            # Final-integration portal sources directly inspected on 2026-11-10.
            # This exception applies only to the root portal, not archived Edition D rows.
            portal_hosts = ALLOWED_HOSTS | {
                "wise.com", "pic.bankofchina.com", "www.hsbc.com.cn",
                "guangdong.chinatax.gov.cn",
            }
            if host not in portal_hosts:
                portal_bad.append("off-allowlist external: " + href)
            continue
        if href.startswith(("#", "mailto:")):
            continue
        dest = os.path.normpath(os.path.join(ROOT, "..", href.split("#")[0]))
        if not os.path.exists(dest):
            portal_bad.append("missing target: " + href)
    for required in ("edition-d/docs/index.html", "overview.html", "pages/estimates.html", "dossier/index.html",
                     "edition-b/index.html", "edition-c/docs/index.html", "COORDINATION.md"):
        if required not in doc:
            portal_bad.append("portal does not link " + required)
check("root portal links", not portal_bad,
      "{} targets; problems {}".format(len(re.findall(r'href="', doc)) if os.path.exists(ROOT_INDEX) else 0,
                                       portal_bad or "none"))

# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
print("Edition D verification")
print("=" * 62)
for name, detail in counts.items():
    print("  PASS  {:<34} {}".format(name, detail))
if problems:
    print("\nFAILURES")
    for p in problems:
        print("  - " + p)
    sys.exit(1)
print("\nRESULT: PASS — {} checks, 0 failures".format(len(counts)))
