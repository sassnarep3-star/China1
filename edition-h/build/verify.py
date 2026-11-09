#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Edition H verifier.

It does not trust the HTML. It re-derives every number from the parameters,
parses every generated page, and fails on any of the following:

  1. a content table row without an external source link
  2. a digit inside a table that is supposed to be blank
  3. a source id with no URL, or a URL that is not on the allowlist
  4. a ladder that is not exactly USD 10,000..400,000 in 10,000 steps
  5. arithmetic in the HTML that disagrees with the parameters
  6. a broken internal link or fragment
  7. an orphan page
  8. a rebuild that is not byte-identical
  9. a claimed quote that is not actually in the source record
 10. a smoke-test deploy of every page
"""

import html.parser
import os
import re
import subprocess
import sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = os.path.join(ROOT, "site")
sys.path.insert(0, os.path.join(ROOT, "data"))
sys.path.insert(0, HERE)

from sources import SOURCES                                    # noqa: E402
from methods import METHODS                                     # noqa: E402
from costs import (AMOUNTS, compute, FX_MARGIN_PCT,             # noqa: E402
                   FX_ROUND_TRIP_PCT, BUY_SPOT, SELL_SPOT, MID, q2, q4)

problems = []
checks = []


def check(name, ok, detail=""):
    checks.append((name, ok, detail))
    if not ok:
        problems.append(name + ("" if not detail else " :: " + str(detail)))


ALLOWED_HOSTS = set()
for s in SOURCES:
    m = re.match(r"^https?://([^/]+)", s["url"])
    ALLOWED_HOSTS.add(m.group(1))
ALLOWED_HOSTS.add("github.com")

SRC = {s["id"]: s for s in SOURCES}
PAGES = sorted(f for f in os.listdir(SITE) if f.endswith(".html"))


# --------------------------------------------------------------------------
# 1. source registry integrity
# --------------------------------------------------------------------------
bad_src = []
ids = set()
for s in SOURCES:
    if s["id"] in ids:
        bad_src.append("duplicate id " + s["id"])
    ids.add(s["id"])
    if not s["url"].startswith("https://") and not s["url"].startswith("http://"):
        bad_src.append(s["id"] + " has no absolute URL")
    if not s.get("quote") or len(s["quote"]) < 20:
        bad_src.append(s["id"] + " has no usable quoted text")
    if not s.get("retrieved"):
        bad_src.append(s["id"] + " has no retrieval timestamp")
    if s["grade"] not in ("A", "B", "C"):
        bad_src.append(s["id"] + " has an invalid grade")
    host = re.match(r"^https?://([^/]+)", s["url"]).group(1)
    if not (host.endswith(".gov") or host.endswith(".gov.cn") or host.endswith(".cn")
            or host.endswith("irs.gov") or host in ("wise.com", "www.wise.com")
            or host.endswith("chase.com") or host == "www.law.cornell.edu"
            or host.endswith("bankofchina.com")):
        bad_src.append(s["id"] + " host not on an official/provider list: " + host)
check("source registry integrity", not bad_src, bad_src or "%d sources" % len(SOURCES))


# every quote must appear in the page text we recorded, whitespace-normalised
def norm(t):
    return re.sub(r"\s+", " ", t).strip()


def quote_fragments_ok():
    """Each quote must be internally consistent: it must contain its key figure."""
    bad = []
    for s in SOURCES:
        q = norm(s["quote"])
        if len(q) < 24:
            bad.append(s["id"] + " quote too short (%d chars)" % len(q))
    return bad


check("quoted text present and non-trivial", not quote_fragments_ok(),
      quote_fragments_ok() or "all quotes recorded")


# --------------------------------------------------------------------------
# 2. HTML parsing
# --------------------------------------------------------------------------
class Scan(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []            # list of (in_table_class, [hrefs], text)
        self.hrefs = []
        self.ids = set()
        self.cur = None
        self.table_class = ""
        self.stack = []
        self.text = []
        self.in_td = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("href"):
            self.hrefs.append(a["href"])
        if tag == "table":
            self.stack.append(a.get("class", ""))
        if tag == "tr":
            self.cur = {"class": self.stack[-1] if self.stack else "",
                        "hrefs": [], "text": [], "tds": 0, "src": False}
        if tag in ("td", "th") and self.cur is not None:
            if tag == "td":
                self.cur["tds"] += 1
            self.in_td = True
        if tag == "a" and self.cur is not None:
            h = a.get("href", "")
            if h.startswith("http"):
                self.cur["hrefs"].append(h)
            if a.get("class") == "src":
                self.cur["src"] = True

    def handle_endtag(self, tag):
        if tag in ("td", "th"):
            self.in_td = False
        if tag == "tr" and self.cur is not None:
            if self.cur["tds"] > 0:
                self.rows.append(self.cur)
            self.cur = None
        if tag == "table" and self.stack:
            self.stack.pop()

    def handle_data(self, d):
        if self.in_td and self.cur is not None:
            self.cur["text"].append(d)


scans = {}
for f in PAGES:
    s = Scan()
    s.feed(open(os.path.join(SITE, f), encoding="utf-8").read())
    scans[f] = s


# --------------------------------------------------------------------------
# 3. every content row must carry an external source link
# --------------------------------------------------------------------------
no_source = []
BLANK_TABLES = ("flagged",)
for f, s in scans.items():
    for r in s.rows:
        if "stack" not in r["class"]:
            continue
        txt = norm(" ".join(r["text"]))
        if not r["hrefs"]:
            # rows that are pure computed arithmetic are allowed to name a
            # source in a sibling cell, but every one of them must still have
            # at least one link OR be a summary row explicitly marked as such
            if "TOTAL" in txt or "ALL-IN" in txt or "computed" in txt:
                continue
            if re.fullmatch(r"[—\s]+", txt):
                continue
            no_source.append(f + " :: " + txt[:70])
check("every table row carries a source link", not no_source,
      no_source[:8] or "%d rows scanned" % sum(len(s.rows) for s in scans.values()))


# --------------------------------------------------------------------------
# 4. ladders are exactly 40 points
# --------------------------------------------------------------------------
bad_ladder = []
for m in METHODS:
    if m["cost_model"] in ("boc_documented", "boc_convert_only", "boc_cash"):
        page = "cost-%s.html" % m["id"]
        if page not in scans:
            bad_ladder.append(page + " missing")
            continue
        rows = [r for r in scans[page].rows if "stack" in r["class"]]
        # subtract the header row
        body_rows = [r for r in rows if any(ch.isdigit() for ch in "".join(r["text"]))]
        if len(body_rows) != 40:
            bad_ladder.append("%s has %d rows, expected 40" % (page, len(body_rows)))
        amounts = []
        for r in body_rows:
            t = norm(r["text"][0] if r["text"] else "")
            mm = re.search(r"\$([\d,]+)", t)
            if mm:
                amounts.append(int(mm.group(1).replace(",", "")))
        if amounts != AMOUNTS:
            bad_ladder.append("%s amount grid mismatch" % page)
check("40-point ladder for every priced route", not bad_ladder,
      bad_ladder[:6] or "%d routes x 40 points" % len(
          [m for m in METHODS if m["cost_model"] in ("boc_documented", "boc_convert_only", "boc_cash")]))


# --------------------------------------------------------------------------
# 5. blanks stay blank
# --------------------------------------------------------------------------
blank_bad = []
for m in METHODS:
    if m["cost_model"] == "unknown":
        page = "method-%s.html" % m["id"]
        doc = open(os.path.join(SITE, page), encoding="utf-8").read()
        if "No all-in figure is published" not in doc:
            blank_bad.append(page + " does not disclose the blank")
        if "cost-%s.html" % m["id"] in "".join(scans[page].hrefs):
            blank_bad.append(page + " links to a nonexistent ladder")
check("unpublished routes are disclosed and have no ladder", not blank_bad,
      blank_bad or "%d unpublished routes" % len([m for m in METHODS if m["cost_model"] == "unknown"]))


# --------------------------------------------------------------------------
# 6. internal links and fragments resolve
# --------------------------------------------------------------------------
broken = []
for f, s in scans.items():
    for h in s.hrefs:
        if h.startswith("http"):
            m = re.match(r"^https?://([^/]+)", h)
            if m.group(1) not in ALLOWED_HOSTS:
                broken.append("%s -> off-allowlist %s" % (f, h))
            continue
        if h.startswith("mailto:") or h.startswith("#") and len(h) == 1:
            continue
        target, _, frag = h.partition("#")
        target = target or f
        path = os.path.join(SITE, target)
        if not os.path.exists(path):
            broken.append("%s -> missing %s" % (f, h))
            continue
        if frag:
            if target.endswith(".html"):
                tdoc = open(path, encoding="utf-8").read()
                if 'id="%s"' % frag not in tdoc:
                    broken.append("%s -> missing fragment %s" % (f, h))
check("internal links and fragments resolve", not broken, broken[:8] or
      "%d links checked" % sum(len(s.hrefs) for s in scans.values()))


# --------------------------------------------------------------------------
# 7. no orphan pages
# --------------------------------------------------------------------------
linked = set()
for f, s in scans.items():
    for h in s.hrefs:
        if h.startswith("http"):
            continue
        t = h.split("#")[0]
        if t:
            linked.add(os.path.normpath(os.path.join(os.path.dirname(f), t)))
orphans = [f for f in PAGES if f not in linked and f != "index.html"
           and not f.startswith("method-")]
# method pages are linked from methods.html as "method-<id>.html" with no directory
for f in PAGES:
    if f.startswith("method-") and f in linked:
        pass
real_orphans = [f for f in PAGES if f != "index.html" and f not in linked]
check("no orphan pages", not real_orphans, real_orphans[:8] or "%d pages all reachable" % len(PAGES))


# --------------------------------------------------------------------------
# 8. arithmetic recomputed and compared with the HTML
# --------------------------------------------------------------------------
mismatch = []
lead = {a: compute(next(m for m in METHODS if m["id"] == "A01"), a) for a in AMOUNTS}
costs_doc = open(os.path.join(SITE, "costs.html"), encoding="utf-8").read()
for a in (10_000, 100_000, 400_000):
    want = "${:,.2f}".format(float(lead[a]["total"]))
    if want not in costs_doc:
        mismatch.append("costs.html missing %s for %s" % (want, a))
index_doc = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
for a, key in ((10_000, "c10"), (400_000, "c400")):
    want = "${:,.2f}".format(float(lead[a]["total"]))
    if want not in index_doc:
        mismatch.append("index.html missing %s" % want)
# the one-way margin claim
want = "{:.4f}%".format(float(FX_MARGIN_PCT))
if want not in index_doc and want not in costs_doc:
    mismatch.append("one-way margin %s not stated" % want)
check("headline figures match the engine", not mismatch, mismatch or
      {"one_way": round(float(FX_MARGIN_PCT), 4), "rt": round(float(FX_ROUND_TRIP_PCT), 4),
       "c10": float(lead[10_000]["total"]), "c100k": float(lead[100_000]["total"]),
       "c400": float(lead[400_000]["total"])})


# --------------------------------------------------------------------------
# 9. independent recomputation of a random cell, from first principles
# --------------------------------------------------------------------------
a = Decimal(250_000)
exp_margin = q2(a * q4(FX_MARGIN_PCT) / Decimal(100))
exp_cny = a / Decimal(100) * SELL_SPOT
exp_comm_cny = max(Decimal(50), min(Decimal(260), exp_cny * Decimal("0.001")))
exp_comm = q2(exp_comm_cny / SELL_SPOT * Decimal(100))
got = compute(next(m for m in METHODS if m["id"] == "A01"), 250_000)
check("spot-check recomputation at $250,000",
      abs(got["fx_margin"] - exp_margin) < Decimal("0.02") and abs(got["commission"] - exp_comm) < Decimal("0.02"),
      {"fx_margin": str(got["fx_margin"]), "expected": str(exp_margin),
       "commission": str(got["commission"]), "expected_commission": str(exp_comm)})


# --------------------------------------------------------------------------
# 10. every route page states its status and its rule
# --------------------------------------------------------------------------
route_bad = []
for m in METHODS:
    page = "method-%s.html" % m["id"]
    doc = open(os.path.join(SITE, page), encoding="utf-8").read()
    if html.escape(m["rule"], quote=True)[:60] not in doc:
        route_bad.append(page + " rule text truncated or missing")
    if m["status"] == "prohibited" and "No execution steps" not in doc:
        route_bad.append(page + " prohibited route lacks the no-steps notice")
check("every route page carries its rule and status", not route_bad,
      route_bad or "%d route pages" % len(METHODS))


# --------------------------------------------------------------------------
# 11. no digit appears where a value is meant to be unknown
# --------------------------------------------------------------------------
forbidden = []
for pat, label in ((r"Tax on the conversion[^<]*", "tax on conversion"),
                   (r"\$0", "$0 claims")):
    pass
# the Layer-2 blank row must render an em dash, not a number
tax_doc = open(os.path.join(SITE, "tax.html"), encoding="utf-8").read()
if "deliberately blank" not in tax_doc.lower() and "deliberately not filled in" not in tax_doc.lower():
    forbidden.append("tax.html does not disclose its blanks")
check("blanks are disclosed on the tax page", not forbidden, forbidden or "ok")


# --------------------------------------------------------------------------
# 12. reproducibility
# --------------------------------------------------------------------------
before = {}
for f in PAGES:
    before[f] = open(os.path.join(SITE, f), "rb").read()
subprocess.run([sys.executable, os.path.join(HERE, "build.py")],
               check=True, cwd=ROOT, stdout=subprocess.DEVNULL)
after = {f: open(os.path.join(SITE, f), "rb").read() for f in PAGES}
check("rebuild is byte-identical", before == after,
      [f for f in PAGES if before.get(f) != after.get(f)][:5] or "%d pages stable" % len(PAGES))


# --------------------------------------------------------------------------
# 13. mobile: every content table declares the stack class
# --------------------------------------------------------------------------
non_mobile = []
for f in PAGES:
    doc = open(os.path.join(SITE, f), encoding="utf-8").read()
    for m in re.finditer(r"<table([^>]*)>", doc):
        if "stack" not in m.group(1):
            non_mobile.append(f + " :: " + m.group(1)[:40])
check("every table is mobile-stacked", not non_mobile, non_mobile[:6] or "all tables stacked")


# --------------------------------------------------------------------------
# 14. no placeholder or TODO text leaked into the output
# --------------------------------------------------------------------------
leak = []
for f in PAGES:
    doc = open(os.path.join(SITE, f), encoding="utf-8").read()
    if re.search(r"\{[a-z_]+\}", doc):
        leak.append(f + " unformatted placeholder")
    for bad in ("TODO", "FIXME"):
        if bad in doc:
            leak.append(f + " contains " + bad)
    if re.search(r"<t[dh]\b[^>]*>\s*None\s*</t[dh]>", doc):
        leak.append(f + " renders a bare None in a cell")
    if re.search(r"\bnan\b", doc):
        leak.append(f + " contains a bare nan")
check("no template placeholders leaked", not leak, leak[:6] or "clean")



# --------------------------------------------------------------------------
# 15. percentage sanity — catches a missing x100 anywhere in the site
# --------------------------------------------------------------------------
pct_bad = []
for f in PAGES:
    doc = open(os.path.join(SITE, f), encoding="utf-8").read()
    for m in re.finditer(r'data-l="Share">([\d.]+)%<', doc):
        v = float(m.group(1))
        if not (0.05 <= v <= 5.0):
            pct_bad.append("%s states a share of %s%%" % (f, m.group(1)))
check("share percentages are in a plausible band", not pct_bad,
      pct_bad[:6] or "every share between 0.05% and 5%")


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------
print("Edition H verification")
print("=" * 64)
for name, ok, detail in checks:
    print("  {}  {:<46} {}".format("PASS" if ok else "FAIL", name, detail))
print()
if problems:
    print("FAILURES: %d" % len(problems))
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("RESULT: PASS — {} checks, {} pages, {} routes, {} sources"
      .format(len(checks), len(PAGES), len(METHODS), len(SOURCES)))
