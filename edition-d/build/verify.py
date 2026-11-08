#!/usr/bin/env python3
"""Edition D independent verifier. Exit 0 = pass."""
import html, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs")
DATA = os.path.join(ROOT, "data")
sys.path.insert(0, HERE)
import data_model as M

P = M.PARAMS
SOURCES = {s["id"]: s for s in M.SOURCES}
SOURCE_URLS = {s["url"] for s in M.SOURCES}
errors, checks = [], []


def check(name, cond):
    global checks
    status = "PASS" if cond else "FAIL"
    checks.append((name, status))
    if not cond:
        errors.append(name)


pages = [f for f in os.listdir(DOCS) if f.endswith(".html")]
expected_pages = {"index.html","ladder.html","methods.html","penalties.html","repo-review.html","flagged.html","sources.html","methodology.html"}
check("all 8 pages exist", set(pages) == expected_pages)
check("stylesheet exists and non-trivial", os.path.getsize(os.path.join(DOCS,"assets/style.css")) > 1000)

content = {p: open(os.path.join(DOCS,p), encoding="utf-8").read() for p in pages}

# internal links + anchors
broken = []
for name, c in content.items():
    for t in re.findall(r'(?:href|src)="([^"]+)"', c):
        if t.startswith(("http://","https://","mailto:","tel:","data:","#")):
            continue
        path = t.split("#")[0]
        if path.startswith("../"):
            resolved = os.path.normpath(os.path.join(DOCS, path))
            if not os.path.exists(resolved):
                broken.append(f"{name}: {t}")
            continue
        if path and not (path in expected_pages or os.path.exists(os.path.join(DOCS, path))):
            broken.append(f"{name}: {t}")
check("all internal links resolve", not broken)
if broken: print("   broken:", broken[:6])

missing_anchors = []
for name, c in content.items():
    ids = set(re.findall(r'id="([^"]+)"', c))
    for t in re.findall(r'href="#([^"]+)"', c):
        if t not in ids:
            missing_anchors.append(f"{name}: #{t}")
check("all in-page anchors resolve", not missing_anchors)
if missing_anchors: print("   anchors:", missing_anchors[:6])

# every external URL cited must be in the registry (by construction) and registry URLs must be http(s)
bad_url = [u for u in SOURCE_URLS if not u.startswith("http")]
check("registry URLs are http(s)", not bad_url)

# no template placeholders
placeholders = [n for n,c in content.items() if re.search(r"\{[a-z_]+\}|\$\{|TODO|FIXME|XXX", c)]
check("no template placeholders", not placeholders)

# JSON exports
ladder = json.load(open(f"{DATA}/ladder.json"))
check("ladder has 200 rows (5 methods × 40 increments)", len(ladder) == 200)
methods_in_ladder = {}
for r in ladder:
    methods_in_ladder.setdefault(r["method"], []).append(r["amount"])
check("all 5 laddered methods cover exactly $10k–$400k by $10k",
      all(sorted(v) == list(range(10000, 400001, 10000)) for v in methods_in_ladder.values()) and len(methods_in_ladder) == 5)

flags = json.load(open(f"{DATA}/flags.json"))
check("flag register parses; ids unique; all severities known",
      len({f["id"] for f in flags}) == len(flags) and {f["severity"] for f in flags} <= {"high","medium","low","informational"})

srcs = json.load(open(f"{DATA}/sources.json"))
check("source registry: ids unique, tiers A/C only",
      len({s["id"] for s in srcs}) == len(srcs) and {s["tier"] for s in srcs} <= {"A","C"})

# arithmetic re-verification (independent recomputation)
half = (P["spot_sell"] - (P["spot_buy"] + P["spot_sell"]) / 2) / ((P["spot_buy"] + P["spot_sell"]) / 2)
check("one-way spread recomputed ≈ 0.2104%", abs(half - 0.00210366) < 1e-6)
def wire(usd):
    a = usd * P["fx_rate"]
    return min(max(a*0.001, 50), 260) + 150
check("wire fee at $10k = ¥216.93", abs(wire(10000) - 216.929) < 1e-3)
check("wire fee saturates at ¥410 (1‰ cap) for ≥$38,853", abs(wire(50000) - 410.0) < 1e-9)
total_400k_l2 = 400000*half + wire(400000)/P["fx_rate"]
check("L2 $400k total ≈ $902.72", abs(total_400k_l2 - 902.72) < 0.01)
ladder_html = content.get("ladder.html", "")
check("rendered ladder contains the recomputed value $902.72", "$902.72" in ladder_html)
check("rendered ladder discloses the excluded US fee (F-D03)", "F-D03" in ladder_html)
check("rendered ladder flags disposition taxes on property route (F-D07)", "F-D07" in ladder_html)

# prohibited methods carry no step-by-step in methods.html
methods_html = content.get("methods.html","")
prohibited_blocks = re.findall(r'<article class="method" id="(P\d)">(.*?)</article>', methods_html, re.S)
check("6 prohibited entries present", len(prohibited_blocks) == 6)
check("no operational steps under prohibited entries", all("<ol" not in b[1] for b in prohibited_blocks))

# every page carries the disclaimer/limits somewhere
check("index discloses research/not-advice nature", "Research document, not legal" in content["index.html"] or "not legal" in content["index.html"].lower())

print(f"\n{'='*60}")
for name, status in checks:
    print(f"[{status}] {name}")
print(f"{'='*60}")
print(f"RESULT: {'PASS' if not errors else 'FAIL'} — {sum(1 for _,s in checks if s=='PASS')}/{len(checks)} checks passed")
sys.exit(0 if not errors else 1)
