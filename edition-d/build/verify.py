#!/usr/bin/env python3
"""Edition D validation gate. Exits non-zero on any failure."""
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
TARGETS = list(range(10000, 400001, 10000))

OFFICIAL_HOSTS = (
    "gov.cn", "safe.gov.cn", "pbc.gov.cn", "chinatax.gov.cn", "customs.gov.cn",
    "irs.gov", "govinfo.gov", "ecfr.gov", "supremecourt.gov", "cbp.gov",
    "fincen.gov", "treasury.gov", "congress.gov", "uscode.house.gov",
    "gdhmo.gov.cn", "bankofchina.com", "boc.cn", "hsbc.com.cn", "wise.com",
    "westernunion.com", "moneygram.com", "paypal.com", "icbcasia.com",
)

failures = []


def fail(msg):
    failures.append(msg)


def load(name):
    p = DATA / name
    if not p.exists():
        fail(f"missing data file {name}")
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as exc:
        fail(f"{name} invalid JSON: {exc}")
        return None
    if not isinstance(d, dict) or "_meta" not in d:
        fail(f"{name} missing _meta")
    return d


sources_doc = load("sources.json")
methods_doc = load("methods.json")
flags_doc = load("flags.json")
taxes_doc = load("taxes.json")
penalty_doc = load("penalty.json")
summary_doc = load("summary.json")
costs_doc = load("costs.json")
review_doc = load("repo-review.json")
if failures:
    print("\n".join("FAIL " + f for f in failures)); sys.exit(1)

SOURCES = {s["id"]: s for s in sources_doc["sources"]}
FLAGS = {f["id"]: f for f in flags_doc["flags"]}
METHODS = methods_doc["methods"]
CATS = {c["id"] for c in methods_doc["categories"]}

if len(SOURCES) != len(sources_doc["sources"]):
    fail("duplicate source ids")
if len(FLAGS) != len(flags_doc["flags"]):
    fail("duplicate flag ids")
if len({m["id"] for m in METHODS}) != len(METHODS):
    fail("duplicate method ids")

# source hosts / verified discipline
for sid, s in SOURCES.items():
    u = urlsplit(s["url"])
    if u.scheme not in ("http", "https") or not u.netloc:
        fail(f"{sid}: bad URL")
    host = u.netloc.lower()
    if not any(host == d or host.endswith("." + d) for d in OFFICIAL_HOSTS):
        if s["type"] != "secondary":
            fail(f"{sid}: host {host} not in accepted list and not marked secondary")
    # 'verified' means directly checked; secondary sources may be checked but
    # must never be used as row citations (enforced below).


def walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


# citation resolution across all data
for name in ("methods.json", "flags.json", "taxes.json", "penalty.json", "summary.json", "costs.json"):
    d = json.loads((DATA / name).read_text(encoding="utf-8"))
    for path, val in walk(d):
        if path.endswith(".sources") or path.endswith(".sources[]") or re.search(r"\.sources\[\d+\]$", path):
            if val not in SOURCES:
                fail(f"{name}{path}: unknown source {val}")
        if re.search(r"\.flags\[\d+\]$", path) or path.endswith(".flags"):
            if val not in FLAGS:
                fail(f"{name}{path}: unknown flag {val}")

for m in METHODS:
    if m["category"] not in CATS:
        fail(f"{m['id']}: bad category")
    if not m["sources"]:
        fail(f"{m['id']}: no sources")
    for sid in m["sources"]:
        if SOURCES[sid]["type"] == "secondary":
            fail(f"{m['id']}: secondary source {sid} used as a citation")
    if m["status"] in ("prohibited",) and m["steps"]:
        fail(f"{m['id']}: prohibited candidate must not have execution steps")

# cost grid completeness and blank discipline
rows = costs_doc["rows"]
by_method = Counter(r["method_id"] for r in rows)
for m in METHODS:
    if by_method[m["id"]] != 40:
        fail(f"{m['id']}: expected 40 cost rows, got {by_method[m['id']]}")
seen = set()
for r in rows:
    key = (r["method_id"], r["target_usd"])
    if key in seen:
        fail(f"duplicate cost row {key}")
    seen.add(key)
    if r["target_usd"] not in TARGETS:
        fail(f"bad target {r['target_usd']}")
    for field in ("cny_principal", "fx_cost_usd", "downstream_usd", "documentation_usd", "tax_usd", "all_in_usd"):
        if r[field] is not None:
            fail(f"{key}: {field} must be blank/unverified, got {r[field]}")
    if r["all_in_status"] != "unverified":
        fail(f"{key}: all_in_status must be unverified")
    if not r["sources"]:
        fail(f"{key}: no sources")
    fee = r["sender_fee"]
    if fee is not None:
        if fee["min"] > fee["max"]:
            fail(f"{key}: fee min>max")
        if fee["currency"] not in ("CNY", "USD"):
            fail(f"{key}: bad fee currency")
for m in METHODS:
    ts = sorted(r["target_usd"] for r in rows if r["method_id"] == m["id"])
    if ts != TARGETS:
        fail(f"{m['id']}: target grid mismatch")

# observed Wise quotes must match registered sources
for q in costs_doc["_meta"]["observed_wise_quotes"]:
    if q["source"] not in SOURCES:
        fail("observed quote missing source")

# generated pages: links, fragments, duplicate ids, row source links
pages = {p.name: p.read_text(encoding="utf-8") for p in DOCS.glob("*.html")}
if not pages:
    fail("no generated pages")
ids_by_page = {}
for name, text in pages.items():
    ids = re.findall(r'id="([^"]+)"', text)
    dupes = [k for k, v in Counter(ids).items() if v > 1]
    if dupes:
        fail(f"{name}: duplicate ids {dupes}")
    ids_by_page[name] = set(ids)
for name, text in pages.items():
    for href in re.findall(r'href="([^"]+)"', text):
        if href.startswith(("http://", "https://", "mailto:", "#")):
            if href.startswith("#") and href[1:] not in ids_by_page[name]:
                fail(f"{name}: missing fragment {href}")
            continue
        target = unquote(href.split("#")[0])
        frag = href.split("#")[1] if "#" in href else None
        if target not in pages:
            fail(f"{name}: broken link {href}")
        elif frag and frag not in ids_by_page[target]:
            fail(f"{name}: broken fragment {href}")
# every method page cost table row carries a source link
for m in METHODS:
    text = pages.get(f"method-{m['id']}.html", "")
    body_rows = re.findall(r"<tr><td>\$[\d,]+</td>.*?</tr>", text, flags=re.S)
    if len(body_rows) != 40:
        fail(f"method-{m['id']}.html: expected 40 rendered cost rows, got {len(body_rows)}")
    for row in body_rows:
        if 'class="srcs"' not in row or "UNVERIFIED" not in row:
            fail(f"method-{m['id']}.html: cost row missing source link or unverified badge")
            break

# reproducibility: rebuild and compare digests
def digests():
    out = {}
    for p in sorted(DOCS.glob("*.html")) + [DATA / "costs.json"]:
        out[str(p.relative_to(ROOT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out

before = digests()
subprocess.run([sys.executable, str(ROOT / "build" / "build.py")], check=True, capture_output=True)
after = digests()
if before != after:
    fail("build is not reproducible")

if failures:
    print("\n".join("FAIL " + f for f in failures))
    sys.exit(1)
print(f"PASS: {len(METHODS)} candidates, {len(rows)} cost rows, {len(SOURCES)} sources, {len(FLAGS)} flags, {len(pages)} pages; links/fragments/blanks/reproducibility verified.")
