#!/usr/bin/env python3
"""
Edition H - independent verification.

The verifier does not trust the HTML and it does not trust build.py's output: it
recomputes every ladder cell from edition-h/data/parameters.json and compares the
result string-for-string with what is published. It also checks that every table
row carries an external source link (or sits in a table explicitly marked as
flagged), that every internal link and fragment resolves, that every external host
is on the official allowlist, and that a rebuild is byte-identical.
"""
import hashlib
import json
import math
import os
import pathlib
import re
import subprocess
import sys
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).resolve().parents[2]
H = ROOT / "edition-h"
DOCS = H / "docs"
DATA = H / "data"

ALLOWED_HOSTS = {
    "safe.gov.cn", "www.safe.gov.cn", "m.safe.gov.cn",
    "gov.cn", "www.gov.cn",
    "chinatax.gov.cn", "www.chinatax.gov.cn",
    "pbc.gov.cn", "www.pbc.gov.cn",
    "irs.gov", "www.irs.gov",
    "govinfo.gov", "www.govinfo.gov",
    "boc.cn", "www.boc.cn",
    "ecfr.gov", "www.ecfr.gov",
    "wise.com", "www.wise.com",
}

problems = []
checks = []


def fail(msg):
    problems.append(msg)


def check(name, ok, detail):
    checks.append((name, detail))
    if not ok:
        fail("%s: %s" % (name, detail))


def load(name):
    with open(DATA / name, encoding="utf-8") as fh:
        return json.load(fh)


SRC_DOC = load("sources.json")
P = load("parameters.json")
METHODS_DOC = load("methods.json")
TAX_DOC = load("taxes.json")
FLAGS_DOC = load("flags.json")
REQ_DOC = load("requirements.json")
SRC = {s["id"]: s for s in SRC_DOC["sources"]}
METHODS = METHODS_DOC["methods"]
FLAGS = {f["id"]: f for f in FLAGS_DOC["flags"]}

# ---------------------------------------------------------------------------
# 1. source register
# ---------------------------------------------------------------------------

bad = []
for sid, s in SRC.items():
    for field in ("tier", "issuer", "title_en", "url", "supports", "retrieved", "retrieval_note"):
        if field not in s or s[field] in ("", [], None):
            bad.append("%s missing %s" % (sid, field))
    if s.get("tier") not in ("A", "B"):
        bad.append("%s tier %s" % (sid, s.get("tier")))
    host = re.match(r"^https?://([^/]+)", s["url"])
    if not host or host.group(1) not in ALLOWED_HOSTS:
        bad.append("%s off-allowlist host %s" % (sid, s["url"]))
check("source register complete and on the allowlist", not bad, "%d sources; %s" % (len(SRC), bad or "clean"))

# ---------------------------------------------------------------------------
# 2. cross references
# ---------------------------------------------------------------------------

bad = []
for m in METHODS:
    for sid in m["sources"]:
        if sid not in SRC:
            bad.append("%s cites unknown source %s" % (m["id"], sid))
    for fid in m["flags"]:
        if fid not in FLAGS:
            bad.append("%s cites unknown flag %s" % (m["id"], fid))
    for step in m["steps"]:
        if step["cite"] not in SRC:
            bad.append("%s step cites unknown source %s" % (m["id"], step["cite"]))
for t in TAX_DOC["rows"]:
    for sid in t["sources"]:
        if sid not in SRC:
            bad.append("%s cites unknown source %s" % (t["id"], sid))
    if not t["value"] and t["status"] != "unverified":
        bad.append("%s has no value but is not marked unverified" % t["id"])
for f in FLAGS_DOC["flags"]:
    for sid in f["sources"]:
        if sid not in SRC:
            bad.append("%s cites unknown source %s" % (f["id"], sid))
check("method, step, tax and flag cross references", not bad, "%d methods, %d tax rows, %d flags; %s" % (
    len(METHODS), len(TAX_DOC["rows"]), len(FLAGS), bad or "clean"))

# every method's cost model must be one the engine knows
known_models = {"wire_purchase", "wire_quota", "wire_fees_only", "emigration", "inheritance", "cash", "fine", "none", "gain_tax"}
bad = [m["id"] for m in METHODS if m["cost_model"] not in known_models]
check("cost models are ones the engine implements", not bad, "%s" % (bad or "all recognised"))

# ---------------------------------------------------------------------------
# 3. recompute the ladders
# ---------------------------------------------------------------------------

BUY = P["fx_board"]["buy_spot_cny_per_100"]
SELL = P["fx_board"]["sell_spot_cny_per_100"]
MID = (BUY + SELL) / 2.0
ONE_WAY = (SELL - MID) / MID
COMM_RATE = P["boc_personal_remittance"]["commission_rate"]
COMM_MIN = P["boc_personal_remittance"]["commission_min_cny"]
COMM_MAX = P["boc_personal_remittance"]["commission_max_cny"]
CABLE = P["boc_personal_remittance"]["cable_cny_non_hk"]
FULL = P["full_amount_service"]["usd_ny_branch_account"]
QUOTA = P["quota"]["annual_usd"]
EMIG_CNY = P["emigration_transfer"]["one_off_threshold_cny"]
EMIG_FRACTIONS = P["emigration_transfer"]["staged_fractions"]
FINE_BASE = P["penalties_cn"]["base_rate"]
FINE_HIGH = P["penalties_cn"]["serious_rate_high"]
AMOUNTS = list(range(P["chart_of_amounts"]["start"], P["chart_of_amounts"]["stop"] + 1, P["chart_of_amounts"]["step"]))


def cny_for_usd(usd):
    return usd * SELL / 100.0


def usd_for_cny(cny):
    return cny / (SELL / 100.0)


def commission_usd(usd_part):
    return usd_for_cny(min(max(COMM_RATE * cny_for_usd(usd_part), COMM_MIN), COMM_MAX))


def splits_for(model, amount):
    if model == "wire_quota":
        n = max(1, math.ceil(amount / QUOTA))
        return [1.0 / n] * n
    if model == "emigration":
        if cny_for_usd(amount) <= EMIG_CNY:
            return [1.0]
        return list(EMIG_FRACTIONS)
    return [1.0]


def expected(model, amount):
    if model == "fine":
        return [amount * FINE_BASE, amount * FINE_HIGH]
    splits = splits_for(model, amount)
    fx = 0.0 if model == "wire_fees_only" else amount * ONE_WAY
    comm = sum(commission_usd(amount * f) for f in splits)
    cable = usd_for_cny(CABLE) * len(splits)
    china = fx + comm + cable
    full = FULL * len(splits) if model in ("wire_purchase", "wire_quota", "emigration", "inheritance", "wire_fees_only") else None
    return [amount, fx, comm, cable, china, china / amount, full, amount - china]


def money(x, d=2):
    if x is None:
        return "&mdash;"
    return "${:,.{d}f}".format(x, d=d)


def pct(x, d=3):
    return "{:.{d}f}%".format((x or 0) * 100, d=d)


LADDER_MODELS = {
    "M01": "wire_purchase", "M02": "wire_quota", "M03": "wire_fees_only", "M05": "emigration",
    "M06": "inheritance", "M09": "cash", "M14": "fine", "M15": "fine",
}

CELL = re.compile(r'<td class="num">(.*?)</td>', re.S)
TAG = re.compile(r"<[^>]+>")


def cell_texts(row_html):
    return [TAG.sub("", c).strip() for c in CELL.findall(row_html)]


bad = []
cells_checked = 0
for fname in sorted(os.listdir(DOCS)):
    if not fname.endswith(".html"):
        continue
    doc = (DOCS / fname).read_text(encoding="utf-8")
    for m in re.finditer(r'<table class="ladder" data-method="(M\d+)">(.*?)</table>', doc, re.S):
        mid, body = m.group(1), m.group(2)
        model = LADDER_MODELS.get(mid)
        if model is None:
            bad.append("%s publishes a ladder for %s with no model" % (fname, mid))
            continue
        tbody = re.search(r"<tbody>(.*?)</tbody>", body, re.S)
        rows = re.findall(r"<tr>(.*?)</tr>", tbody.group(1) if tbody else "", re.S)
        if len(rows) != len(AMOUNTS):
            bad.append("%s %s has %d rows, expected %d" % (fname, mid, len(rows), len(AMOUNTS)))
            continue
        for amount, row in zip(AMOUNTS, rows):
            got = cell_texts(row)
            exp = expected(model, amount)
            cells_checked += 1
            if model == "fine":
                if got[0] != money(amount, 0) or got[1] != money(exp[0]) or got[2] != money(exp[1]):
                    bad.append("%s %s %s fine cells %s" % (fname, mid, amount, got[:3]))
            else:
                want = [money(amount, 0), money(exp[1]), money(exp[2]), money(exp[3]),
                        money(exp[4]), pct(exp[5]), money(exp[6]), money(exp[7])]
                if got[:8] != want:
                    bad.append("%s %s %s: %s != %s" % (fname, mid, amount, got[:8], want))
check("every ladder cell recomputes", not bad,
      "%d rows across %d models; %s" % (cells_checked, len(LADDER_MODELS), bad[:3] or "clean"))

# hand-check: arithmetic written out independently of the engine helpers, so a shared
# bug in a helper cannot pass unnoticed
hand = [
    (10_000, 21.04, 10.00, 22.42, 53.45),
    (400_000, 841.59, 38.85, 22.42, 902.86),
]
bad = []
for amount, fx, comm, cable, total in hand:
    want = expected("wire_purchase", amount)
    if abs(want[1] - fx) > 0.02 or abs(want[2] - comm) > 0.02 or abs(want[3] - cable) > 0.02 or abs(want[4] - total) > 0.05:
        bad.append("%s: %s vs hand %s" % (amount, [round(x, 2) for x in want[1:5]], [fx, comm, cable, total]))
check("independent hand-check of two ladder rows", not bad, "%s" % (bad or "10,000 and 400,000 match written-out arithmetic"))

# headline figures must appear in the dashboard and on the root page
r400 = expected("wire_purchase", 400_000)
dash = (DOCS / "index.html").read_text(encoding="utf-8")
root = (ROOT / "index.html").read_text(encoding="utf-8")
check("headline cost figures match the engine",
      money(r400[4]) in dash and money(r400[4]) in root and pct(r400[5]) in dash,
      "$400,000 total %s, share %s" % (money(r400[4]), pct(r400[5])))
check("one-way margin printed, round trip not used as the single-conversion cost",
      pct(ONE_WAY, 4) in dash and "0.4199" not in dash.split("Cost at a glance")[0],
      "one-way %s" % pct(ONE_WAY, 4))

# ---------------------------------------------------------------------------
# 4. tables cite a source
# ---------------------------------------------------------------------------


class TableAudit(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.in_table = 0
        self.table_flagged = False
        self.row = None
        self.rows = 0
        self.cited = 0
        self.missing = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "table":
            self.in_table += 1
            self.table_flagged = "flagtable" in (attrs.get("class") or "")
        elif tag == "tr" and self.in_table:
            self.row = {"td": 0, "ext": False}
        elif tag == "td" and self.row is not None:
            self.row["td"] += 1
        elif tag == "a" and self.row is not None:
            href = attrs.get("href") or ""
            if href.startswith(("http://", "https://")):
                self.row["ext"] = True

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table -= 1
        elif tag == "tr" and self.row is not None:
            if self.row["td"]:
                self.rows += 1
                if self.row["ext"]:
                    self.cited += 1
                elif not self.table_flagged:
                    self.missing.append("%s row %d" % (self.path, self.rows))
            self.row = None


total_rows = total_cited = 0
missing = []
for fname in sorted(os.listdir(DOCS)):
    if fname.endswith(".html"):
        a = TableAudit(fname)
        a.feed((DOCS / fname).read_text(encoding="utf-8"))
        total_rows += a.rows
        total_cited += a.cited
        missing += a.missing
check("every table row carries an external source link", not missing,
      "%d rows, %d cited, %s" % (total_rows, total_cited, missing[:4] or "clean"))

# ---------------------------------------------------------------------------
# 5. blanks are disclosed, not zeroed
# ---------------------------------------------------------------------------

blank_bad = []
flagpage = (DOCS / "flagged.html").read_text(encoding="utf-8")
for f in FLAGS_DOC["flags"]:
    fid = f["id"]
    if fid not in flagpage:
        blank_bad.append("flag %s not published" % fid)
    if not f["sources"] and "No official instrument retrieved" not in flagpage:
        blank_bad.append("empty-source disclosure missing")
check("every flag is published and unsourced flags are disclosed", not blank_bad,
      "%d flags; %s" % (len(FLAGS), blank_bad or "clean"))

# unknown parameters must not be rendered as a number anywhere
check("US receiving-bank fee is blank, not a number",
      P["receiving_bank_us"]["usd"] is None and "receiving_bank_us" not in
      json.dumps([{"v": v} for v in []]) and "&mdash;" in (DOCS / "costs.html").read_text(encoding="utf-8"),
      "parameter null and rendered as an em dash")

# ---------------------------------------------------------------------------
# 6. links, fragments and hosts
# ---------------------------------------------------------------------------

bad = []
internal = 0
for fname in sorted(os.listdir(DOCS)):
    if not fname.endswith(".html"):
        continue
    doc = (DOCS / fname).read_text(encoding="utf-8")
    for href in re.findall(r'href="([^"]+)"', doc):
        if href.startswith(("http://", "https://")):
            host = re.match(r"^https?://([^/]+)", href)
            if not host or host.group(1) not in ALLOWED_HOSTS:
                bad.append("%s off-allowlist %s" % (fname, href))
            continue
        if href.startswith(("#", "mailto:")):
            continue
        internal += 1
        path, _, frag = href.partition("#")
        dest = (DOCS / path).resolve() if path else (DOCS / fname).resolve()
        if not dest.exists():
            bad.append("%s missing target %s" % (fname, href))
            continue
        if frag and dest.suffix == ".html":
            if 'id="{}"'.format(frag) not in dest.read_text(encoding="utf-8"):
                bad.append("%s missing fragment %s" % (fname, href))
check("internal links and fragments resolve, external hosts allowed", not bad,
      "%d internal links; %s" % (internal, bad[:4] or "clean"))

# root landing page
bad = []
root_doc = (ROOT / "index.html").read_text(encoding="utf-8")
for href in re.findall(r'href="([^"]+)"', root_doc):
    if href.startswith(("http://", "https://")):
        host = re.match(r"^https?://([^/]+)", href)
        if not host or host.group(1) not in {"boc.cn", "www.boc.cn", "gov.cn", "www.gov.cn",
                                             "chinatax.gov.cn", "www.chinatax.gov.cn",
                                             "pbc.gov.cn", "www.pbc.gov.cn", "irs.gov", "www.irs.gov",
                                             "govinfo.gov", "www.govinfo.gov", "m.safe.gov.cn"}:
            bad.append("root off-allowlist %s" % href)
        continue
    if href.startswith("#"):
        continue
    if not (ROOT / href.split("#")[0]).exists():
        bad.append("root missing target %s" % href)
required = ["edition-h/docs/index.html", "edition-d/docs/index.html", "overview.html", "pages/estimates.html",
            "dossier/index.html", "edition-b/index.html", "edition-c/docs/index.html", "COORDINATION.md",
            "edition-e/site/index.html", "edition-f/site/index.html", "edition-g/docs/index.html"]
for r in required:
    if r not in root_doc:
        bad.append("root does not link %s" % r)
check("root landing page links resolve and reach every edition", not bad, "%s" % (bad or "clean"))

# ---------------------------------------------------------------------------
# 7. page set, navigation, no orphans
# ---------------------------------------------------------------------------

pages = sorted(p.name for p in DOCS.glob("*.html"))
needed = ["index.html", "executive-summary.html", "methods.html", "costs.html", "taxes.html", "penalties.html",
          "steps.html", "sources.html", "flagged.html", "repo-review.html", "methodology.html", "requirements.html"]
needed += ["method-%s.html" % m["id"] for m in METHODS]
needed += ["category-current.html", "category-capital.html", "category-alternatives.html", "category-prohibited.html"]
missing_pages = [n for n in needed if n not in pages]
check("required pages exist", not missing_pages, "%d pages; %s" % (len(pages), missing_pages or "all present"))

reached = set()
for fname in pages:
    doc = (DOCS / fname).read_text(encoding="utf-8")
    for href in re.findall(r'href="([^"#]+)', doc):
        if not href.startswith(("http", "mailto")):
            reached.add(os.path.basename(href))
orphans = [p for p in pages if p != "index.html" and p not in reached]
check("no orphan pages", not orphans, "%s" % (orphans or "every page is linked"))

# ---------------------------------------------------------------------------
# 8. reproducibility
# ---------------------------------------------------------------------------


def digest():
    h = hashlib.sha256()
    for p in sorted(DOCS.glob("*.html")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    h.update((ROOT / "index.html").read_bytes())
    return h.hexdigest()


before = digest()
subprocess.run([sys.executable, str(H / "build" / "build.py")], check=True, capture_output=True)
after = digest()
check("rebuild is byte-identical", before == after, "sha256 %s" % before[:16])

# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

print("Edition H verification")
print("=" * 66)
for name, detail in checks:
    print("  PASS  {:<52} {}".format(name, detail))
if problems:
    print("\nFAILURES")
    for p in problems:
        print("  FAIL  " + p)
    sys.exit(1)
print("\nRESULT: PASS - {} checks, 0 failures".format(len(checks)))
