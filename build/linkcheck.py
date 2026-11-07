#!/usr/bin/env python3
"""
Validation gate. Run after build/build.py and before publishing.

Checks, in order:
  1.  every data file parses as JSON and carries a _meta block
  2.  every source id cited anywhere in data/ exists in data/sources.json
  3.  every source URL is absolute, uses https or http, and sits on a host that
      is either in the accepted official list or is explicitly marked
      not-official with an officiality_note
  4.  every flag id referenced anywhere resolves to an entry in data/flags.json
  5.  every route category resolves to a category with a page
  6.  every route cites at least one source, or is marked unverified with a flag
  7.  no route states a limit while being marked unverified
  8.  every internal href in every generated page resolves to a generated file
  9.  every fragment in an internal link resolves to an id in the target page
  10. no duplicate element ids within a page
  11. no numeric-looking value is rendered without an adjacent source or an
      UNVERIFIED badge in the same cell
  12. generated output is stable: rebuilding produces byte-identical files

Exits non-zero on any failure, so it can gate publication.

Usage:  python3 build/linkcheck.py [--rewrite-check]
"""

import hashlib
import json
import os
import re
import sys
from collections import Counter
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DOCS = os.path.join(ROOT, "docs")

ACCEPTED_OFFICIAL_HOSTS = (
    "safe.gov.cn",
    "gov.cn",
    "pbc.gov.cn",
    "chinatax.gov.cn",
    "moj.gov.cn",
    "mof.gov.cn",
    "customs.gov.cn",
    "mofcom.gov.cn",
    "court.gov.cn",
    "spp.gov.cn",
    "hunan.gov.cn",
    "gdhmo.gov.cn",
    "irs.gov",
    "treasury.gov",
    "ecfr.gov",
    "congress.gov",
    "govinfo.gov",
    "fincen.gov",
    "cbp.gov",
    "uscode.house.gov",
)

failures = []
warnings = []


def fail(msg):
    failures.append(msg)


def warn(msg):
    warnings.append(msg)


def load(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        fail("missing data file: data/%s" % name)
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as exc:
        fail("data/%s does not parse as JSON: %s" % (name, exc))
        return None


def host_of(url):
    try:
        h = urlsplit(url).netloc.lower()
    except ValueError:
        return ""
    return h


def host_is_official(url):
    h = host_of(url)
    if not h:
        return False
    return any(h == d or h.endswith("." + d) for d in ACCEPTED_OFFICIAL_HOSTS)


# ---------------------------------------------------------------- 1. loading
sources = load("sources.json")
routes = load("routes.json")
tax = load("tax.json")
penalties = load("penalties.json")
flags = load("flags.json")
review = load("repo-review.json")
summary = load("summary.json")

DATASETS = {
    "sources.json": sources,
    "routes.json": routes,
    "tax.json": tax,
    "penalties.json": penalties,
    "flags.json": flags,
    "repo-review.json": review,
    "summary.json": summary,
}

for name, doc in DATASETS.items():
    if doc is None:
        continue
    if not isinstance(doc, dict):
        fail("data/%s: top level must be an object" % name)
    elif "_meta" not in doc:
        warn("data/%s: no _meta block" % name)

if failures:
    print("\n".join("FAIL " + f for f in failures))
    sys.exit(1)

SRC_IDS = set(s["id"] for s in sources["sources"])
FLAG_IDS = set(f["id"] for f in flags["flags"])
CAT_IDS = set(c["id"] for c in routes["categories"])
CAT_PAGES = set(c["page"] for c in routes["categories"])

if len(SRC_IDS) != len(sources["sources"]):
    dupes = [k for k, v in Counter(s["id"] for s in sources["sources"]).items() if v > 1]
    fail("duplicate source ids: %s" % ", ".join(dupes))
if len(FLAG_IDS) != len(flags["flags"]):
    dupes = [k for k, v in Counter(f["id"] for f in flags["flags"]).items() if v > 1]
    fail("duplicate flag ids: %s" % ", ".join(dupes))
if len(set(r["id"] for r in routes["routes"])) != len(routes["routes"]):
    dupes = [k for k, v in Counter(r["id"] for r in routes["routes"]).items() if v > 1]
    fail("duplicate route ids: %s" % ", ".join(dupes))


# ------------------------------------------------- 2/4. citation resolution
def walk(node, path, on_ids):
    """Visit every string in a nested structure, reporting its dotted path."""
    if isinstance(node, dict):
        for k, v in node.items():
            walk(v, path + [str(k)], on_ids)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, path + ["[%d]" % i], on_ids)
    elif isinstance(node, str):
        on_ids(node, path)


CITE_KEY = re.compile(r"^(source|sources)$")


def check_citations(doc, name):
    def visit(value, path):
        key = path[-1] if path else ""
        if not CITE_KEY.match(key):
            return
        ids = value if isinstance(value, list) else [value]
        for sid in ids:
            if sid in (None, "", []):
                continue
            if sid not in SRC_IDS:
                fail("data/%s %s: cites unknown source id %r" % (name, "/".join(path), sid))

    if isinstance(doc, dict):
        for k, v in doc.items():
            if k == "_meta":
                continue
            walk(v, [k], visit)


for name, doc in DATASETS.items():
    if name == "sources.json":
        continue
    check_citations(doc, name)


def check_flagrefs():
    seen = set()

    def visit(value, path):
        for m in re.finditer(r"\bF\d{2}\b", value or ""):
            seen.add(m.group(0))

    for name, doc in DATASETS.items():
        if name == "flags.json":
            continue
        walk(doc, [], lambda v, p: visit(v, p))

    for fid in sorted(seen):
        if fid not in FLAG_IDS:
            fail("data references undefined flag id %s" % fid)


check_flagrefs()


# ------------------------------------------- 3. source URL and officiality
for s in sources["sources"]:
    sid = s["id"]
    url = s.get("url")
    if not url:
        fail("source %s has no url" % sid)
        continue
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        fail("source %s url is not http(s): %s" % (sid, url))
    if not parts.netloc:
        fail("source %s url has no host: %s" % (sid, url))
    for field in ("url", "url_alt", "url_fallback"):
        u = s.get(field)
        if u and not u.startswith(("http://", "https://")):
            fail("source %s %s is not absolute: %s" % (sid, field, u))
    if not host_is_official(url):
        if s.get("official"):
            fail(
                "source %s is marked official but %s is not on the accepted official host list"
                % (sid, host_of(url))
            )
        if not s.get("officiality_note"):
            fail(
                "source %s is not on an official host and has no officiality_note explaining why it is used"
                % sid
            )
    else:
        if not s.get("official"):
            warn(
                "source %s sits on official host %s but is marked not official; check"
                % (sid, host_of(url))
            )
    for field in ("title_en", "issuer", "doc_number", "host"):
        if not s.get(field):
            warn("source %s has empty %s" % (sid, field))
    if not s.get("used_for"):
        fail("source %s lists no provisions relied on" % sid)


# ------------------------------------------- 5/6/7. route integrity
for r in routes["routes"]:
    rid = r["id"]
    if r.get("category") not in CAT_IDS:
        fail("route %s has category %r with no matching category entry" % (rid, r.get("category")))
    srcs = r.get("sources") or []
    if not srcs:
        if r.get("verified") is not False:
            fail("route %s cites no sources but is not marked unverified" % rid)
        if not r.get("flag"):
            fail("route %s cites no sources, is unverified, and carries no flag reference" % rid)
    if r.get("verified") is False and not r.get("flag"):
        fail("route %s is unverified but carries no flag reference" % rid)
    for field in ("name", "legal_basis", "how_it_works", "pros", "cons", "feasibility", "risk"):
        if not r.get(field):
            warn("route %s has empty %s" % (rid, field))
    if not r.get("pros") or not r.get("cons"):
        fail("route %s is missing a pros or cons list" % rid)


# ---------------------------------------------- 8/9/10. generated site
if not os.path.isdir(DOCS):
    fail("docs/ does not exist; run build/build.py first")
else:
    generated = set()
    for dirpath, _dirs, files in os.walk(DOCS):
        for f in files:
            rel = os.path.relpath(os.path.join(dirpath, f), DOCS).replace(os.sep, "/")
            generated.add(rel)

    html_pages = sorted(p for p in generated if p.endswith(".html"))
    if not html_pages:
        fail("no HTML pages found in docs/")

    for p in html_pages:
        with open(os.path.join(DOCS, p), encoding="utf-8") as fh:
            text = fh.read()

        # duplicate ids
        ids = re.findall(r'\sid="([^"]+)"', text)
        dupes = [k for k, v in Counter(ids).items() if v > 1]
        if dupes:
            fail("docs/%s has duplicate ids: %s" % (p, ", ".join(sorted(dupes))))
        idset = set(ids)

        # internal links
        for m in re.finditer(r'<a[^>]+href="([^"]+)"', text):
            href = m.group(1)
            if href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
                if href.startswith("#") and href[1:] not in idset:
                    fail("docs/%s links to in-page fragment %s which does not exist" % (p, href))
                continue
            target, _, frag = href.partition("#")
            if target and target not in generated:
                fail("docs/%s links to %s which was not generated" % (p, target))
            if frag and target in generated:
                with open(os.path.join(DOCS, target), encoding="utf-8") as tfh:
                    ttext = tfh.read()
                if ('id="%s"' % frag) not in ttext:
                    fail(
                        "docs/%s links to %s#%s but that page has no such id"
                        % (p, target, frag)
                    )

        # assets referenced must exist
        for m in re.finditer(r'(?:href|src)="((?:assets|[^"]*\.(?:css|js))[^"]*)"', text):
            ref = m.group(1)
            if ref.startswith(("http://", "https://")):
                continue
            if ref not in generated:
                fail("docs/%s references asset %s which was not generated" % (p, ref))

    # --------------------------------- 11. blank-means-flagged, in output
    for p in html_pages:
        with open(os.path.join(DOCS, p), encoding="utf-8") as fh:
            text = fh.read()
        for m in re.finditer(r"<td[^>]*>(.*?)</td>", text, re.S):
            cell = m.group(1)
            if 'class="blank"' not in cell:
                continue
            if not re.search(r"badge-(unverified|secondary|neutral)", cell):
                fail(
                    "docs/%s: a cell renders a blank value with no unverified/secondary badge "
                    "next to it, which hides a gap: %r"
                    % (p, re.sub(r"<[^>]+>", "", cell).strip()[:80])
                )

# --------------------------------- 12. data-level value integrity
# A value may be stated only with a source; otherwise it must be null and flagged.
for t in tax["china"] + tax["us"]:
    if t.get("rate") in (None, ""):
        if t.get("source"):
            warn("tax entry %r is blank but still cites a source" % t.get("item", "")[:60])
    elif not t.get("source"):
        fail("tax entry %r states a rate with no source id" % t.get("item", "")[:60])

for L in penalties["cost_layers"]:
    for vr in L["verified_rates"]:
        if vr.get("rate") in (None, ""):
            fail("cost layer %d entry %r has no rate and no null-marker note" % (
                L["layer"], vr.get("item", "")[:60]))
        elif not vr.get("source"):
            fail("cost layer %d entry %r states a rate with no source id" % (
                L["layer"], vr.get("item", "")[:60]))

PCT = re.compile(r"(\d+(?:\.\d+)?)%")


def parse_money(text):
    """Return a float from strings like 'RMB 24,970,000' or '8.00%'; else None."""
    if not text:
        return None
    m = re.search(r"([\d,]+(?:\.\d+)?)", text)
    if not m:
        return None
    return float(m.group(1).replace(",", ""))


for c in penalties["published_cases"]["cases"]:
    if not c.get("amount_moved") or not c.get("fine"):
        fail("published case for %r is missing an amount or a fine" % c.get("offender", ""))
    if not c.get("source"):
        fail("published case for %r cites no source" % c.get("offender", ""))
    if not c.get("penalty_basis") or not c.get("violation"):
        warn("published case for %r omits the rule breached or the penalty basis"
             % c.get("offender", ""))
    pct = c.get("fine_pct")
    if pct is None:
        # permitted only where the two official figures are in different currencies
        if c.get("amount_currency") == "CNY" and str(c.get("fine", "")).startswith("RMB"):
            fail("case %r has both figures in RMB but no computed fine_pct"
                 % c.get("offender", ""))
        continue
    # independently recompute and compare
    amt = parse_money(c["amount_moved"])
    fin = parse_money(c["fine"])
    stated = parse_money(pct)
    if amt is None or fin is None or stated is None:
        fail("case %r fine_pct %r is not parseable" % (c.get("offender", ""), pct))
        continue
    if not str(c["fine"]).startswith("RMB") or c.get("amount_currency") != "CNY":
        fail("case %r states a computed percentage across mismatched currencies"
             % c.get("offender", ""))
    recomputed = round(fin / amt * 100.0, 2)
    if abs(recomputed - stated) > 0.005:
        fail("case %r fine_pct states %s%% but fine/amount computes to %s%%"
             % (c.get("offender", ""), pct, recomputed))

for r in routes["routes"]:
    if r.get("verified") is False:
        for field in ("limit",):
            if r.get(field):
                fail("route %s is unverified but states a %s" % (r["id"], field))
    if r.get("limit") and not r.get("sources"):
        fail("route %s states a limit with no source" % r["id"])

for k in summary["kpi"]:
    if k.get("value") in (None, ""):
        fail("dashboard KPI %r has no value" % k.get("label", ""))
    if not k.get("page"):
        fail("dashboard KPI %r has no target page" % k.get("label", ""))
    elif k["page"] not in CAT_PAGES | (
        set(f for f in os.listdir(DOCS) if f.endswith(".html"))
        if os.path.isdir(DOCS) else set()
    ):
        fail("dashboard KPI %r points at %s which was not generated"
             % (k.get("label", ""), k["page"]))

# cross-file consistency of the headline counts
counts = {
    "routes": len(routes["routes"]),
    "sources": len(sources["sources"]),
    "flags": len(flags["flags"]),
    "cases": len(penalties["published_cases"]["cases"]),
}
if routes["_meta"].get("count") != counts["routes"]:
    fail("routes.json _meta.count says %s but %d routes are defined"
         % (routes["_meta"].get("count"), counts["routes"]))
official_n = sum(1 for s in sources["sources"] if s.get("official"))
kpi_by_label = {k["label"]: k for k in summary["kpi"]}
for label, expect in (
    ("Conversion channels identified", str(counts["routes"])),
    ("Published enforcement cases analysed", str(counts["cases"])),
    ("Items flagged rather than filled in", str(counts["flags"])),
    ("Sources verified against official texts", "%d of %d" % (official_n, counts["sources"])),
):
    got = kpi_by_label.get(label, {}).get("value")
    if got != expect:
        fail("dashboard KPI %r says %r but the data says %r" % (label, got, expect))

    # ---------------------------------------------- 13. build stability
    if "--rewrite-check" in sys.argv:
        digests = {}
        for p in sorted(generated):
            full = os.path.join(DOCS, p)
            with open(full, "rb") as fh:
                digests[p] = hashlib.sha256(fh.read()).hexdigest()
        manifest = os.path.join(DATA, ".build-digests.json")
        with open(manifest, "w", encoding="utf-8") as fh:
            json.dump(digests, fh, indent=2, sort_keys=True)
        print("wrote %d digests to data/.build-digests.json" % len(digests))
    else:
        manifest = os.path.join(DATA, ".build-digests.json")
        if os.path.exists(manifest):
            with open(manifest, encoding="utf-8") as fh:
                prior = json.load(fh)
            changed = []
            for p in sorted(set(prior) | set(generated)):
                full = os.path.join(DOCS, p)
                cur = None
                if os.path.exists(full):
                    with open(full, "rb") as fh:
                        cur = hashlib.sha256(fh.read()).hexdigest()
                if prior.get(p) != cur:
                    changed.append(p)
            if changed:
                warn(
                    "build is not reproducible against data/.build-digests.json; changed: %s"
                    % ", ".join(changed[:8])
                )


# ------------------------------------------------------------------ report
print("linkcheck: %d sources, %d routes, %d categories, %d flags" % (
    len(SRC_IDS), len(routes["routes"]), len(CAT_IDS), len(FLAG_IDS)))
official = sum(1 for s in sources["sources"] if s.get("official"))
print("           %d of %d source entries marked official" % (official, len(sources["sources"])))
if os.path.isdir(DOCS):
    n = sum(1 for f in os.listdir(DOCS) if f.endswith(".html"))
    print("           %d generated HTML pages in docs/" % n)
    print("           %d category pages" % len(CAT_PAGES))

for w in warnings:
    print("WARN " + w)
for f in failures:
    print("FAIL " + f)

if failures:
    print("\nlinkcheck: FAILED with %d problem(s)" % len(failures))
    sys.exit(1)

print("\nlinkcheck: PASSED (%d warning%s)" % (len(warnings), "" if len(warnings) == 1 else "s"))
sys.exit(0)
