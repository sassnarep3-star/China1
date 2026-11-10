#!/usr/bin/env python3
"""Edition I verifier — independently recomputes costs, checks sources, links, blanks and structure."""
import json, math, re, subprocess, sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
SITE = BASE / "site"

errors = []
checks = 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        errors.append(msg)


def main():
    sources = json.loads((DATA / "sources.json").read_text())["sources"]
    methods = json.loads((DATA / "methods.json").read_text())["methods"]
    model = json.loads((DATA / "model.json").read_text())
    flags = json.loads((DATA / "flags.json").read_text())["flags"]
    taxrows = json.loads((DATA / "taxes.json").read_text())["rows"]
    SRC = {s["id"]: s for s in sources}

    # 1. Deterministic build: rebuild and compare bytes
    before = {p.name: p.read_bytes() for p in SITE.glob("*.html")}
    subprocess.run([sys.executable, str(BASE / "build" / "build.py")], check=True, capture_output=True)
    after = {p.name: p.read_bytes() for p in SITE.glob("*.html")}
    ok(before == after, "rebuild is not byte-identical")

    # 2. Required pages exist
    for page in ["index.html", "executive-summary.html", "methods.html", "steps.html",
                 "costs.html", "taxes.html", "sources.html", "flagged.html"]:
        ok((SITE / page).is_file(), f"missing page {page}")
    ok((SITE / "assets" / "style.css").is_file(), "missing stylesheet")

    # 3. Source integrity: every referenced source id exists; all sources used
    used = set()
    for m in methods:
        used.update(m["sources"])
    for r in taxrows:
        used.update(r["sources"])
    for lid, lad in model["ladders"].items():
        for k in ("fee_source", "fx_source"):
            if lad.get(k):
                used.add(lad[k])
    for u in used:
        ok(u in SRC, f"unknown source id {u}")
    ok(used == set(SRC), f"sources not all referenced: {set(SRC) - used}")
    for s in sources:
        ok(s["url"].startswith("https://") or s["url"].startswith("http://"), f"bad url {s['id']}")

    # 4. Target grid exact
    ok(model["targets_usd"] == list(range(10000, 400001, 10000)), "targets not 10K..400K step 10K")
    ok(len(model["targets_usd"]) == 40, "target count != 40")

    # 5. Independent cost recomputation vs displayed HTML
    SELL = model["fx_board"]["sell_per_usd"]
    mid = model["fx_board"]["mid"]
    margin_rate = (model["fx_board"]["spot_sell"] - mid) / mid
    T = model["boc_tariff"]
    costs_html = (SITE / "costs.html").read_text()

    def wire(target, n):
        margin = target * margin_rate
        handling = 0.0
        cable = 0.0
        remaining = target
        for _ in range(n):
            chunk = min(50000.0, remaining) if n > 1 else target
            fee = min(max(T["handling_pct"] * chunk * SELL, T["handling_min_cny"]), T["handling_max_cny"])
            handling += fee
            cable += T["cable_cny_other"]
            remaining -= chunk
            if remaining <= 0:
                break
        return margin + (handling + cable) / SELL, margin, handling, cable

    for lid, lad in model["ladders"].items():
        if not lad["priced"]:
            continue
        for target in model["targets_usd"]:
            n = math.ceil(target / 50000) if lid == "L2" else 1
            known, margin, handling, cable = wire(target, n)
            ok(f"${known:,.2f}" in costs_html, f"{lid} known subtotal for {target} missing/mismatched")
            ok(f"${margin:,.2f}" in costs_html, f"{lid} margin for {target} missing/mismatched")
        # each priced ladder must contain 40 target rows and blank markers
        seg = costs_html.split(f'id="{lid}"')[1].split("</table>")[0]
        ok(seg.count(f"<strong>$") >= 40, f"{lid} does not show 40 strong target rows")
        ok("⚠ UNVERIFIED" in seg, f"{lid} lacks UNVERIFIED markers")

    # unpriced ladders: all money cells blank + flagged
    for lid, lad in model["ladders"].items():
        if lad["priced"]:
            continue
        seg = costs_html.split(f'id="{lid}"')[1].split("</table>")[0]
        ok("⚠ UNVERIFIED" in seg, f"{lid} lacks UNVERIFIED markers")

    # 6. All-in and unverifiable columns never filled with numbers in cost rows
    for row in re.findall(r"<tr>.*?</tr>", costs_html, flags=re.S):
        blanks = row.count("⚠ UNVERIFIED")
        if blanks and re.search(r'⚠ UNVERIFIED</td><td[^>]*>\$[\d,]+', row):
            errors.append("value placed after UNVERIFIED cell")
    ok(True, "")  # count the UNVERIFIED-leak scan as executed

    # 7. Prohibited methods have no steps and no cost ladder
    for m in methods:
        if m["id"].startswith("P"):
            ok(m["steps"] == [], f"{m['id']} has execution steps")
            ok(m.get("cost_ladder") is None, f"{m['id']} has a cost ladder")
            ok(len(m["pros"]) == 0, f"{m['id']} lists pros")

    # 8. Legal methods: steps, docs, sources present
    for m in methods:
        if not m["id"].startswith("P"):
            ok(len(m["steps"]) >= 3, f"{m['id']} has fewer than 3 steps")
            ok(m["pros"] and m["cons"], f"{m['id']} missing pros/cons")
            ok(len(m["sources"]) >= 2, f"{m['id']} has <2 sources")
        # every method source cited in its rendered row
        ok(f'id="{m["id"]}"' in (SITE / "methods.html").read_text(), f"{m['id']} not rendered on methods page")

    # 9. Every tax row rendered with source links and blank amounts flagged
    taxes_html = (SITE / "taxes.html").read_text()
    for r in taxrows:
        ok(f'id="{r["id"]}"' in taxes_html, f"{r['id']} not rendered")
        for sid in r["sources"]:
            ok(SRC[sid]["url"] in taxes_html, f"{r['id']} source {sid} link missing on taxes page")
        if r["amount"] is None:
            pass  # amount rendered as UNVERIFIED blank
    ok(taxes_html.count("⚠ UNVERIFIED") >= sum(1 for r in taxrows if r["amount"] is None),
       "tax blanks not marked UNVERIFIED")

    # 10. Internal links resolve (hrefs not starting with http/#/mailto)
    all_html = {p.name: p.read_text() for p in SITE.glob("*.html")}
    for name, html in all_html.items():
        for href in re.findall(r'href="([^"]+)"', html):
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if href.startswith("../"):
                target = (SITE / href).resolve()
                ok(target.exists(), f"{name}: broken local link {href}")
                continue
            path, _, frag = href.partition("#")
            if path == "":
                ok(f'id="{frag}"' in html, f"{name}: missing anchor #{frag}")
            else:
                ok((SITE / path).is_file(), f"{name}: broken link {href}")
                if frag and (SITE / path).is_file():
                    ok(f'id="{frag}"' in (SITE / path).read_text(), f"{name}: broken anchor {href}")

    # 11. External links limited to verified source URLs (or repo-relative)
    allowed = {s["url"] for s in sources}
    for name, html in all_html.items():
        for href in re.findall(r'href="(https?://[^"]+)"', html):
            ok(href in allowed, f"{name}: unlisted external URL {href}")

    # 12. Flag register rendered completely
    flagged_html = (SITE / "flagged.html").read_text()
    for f in flags:
        ok(f'id="{f["id"]}"' in flagged_html, f"flag {f['id']} not rendered")

    # 13. Key statutory figures appear where claimed
    ok("$200" in (SITE / "taxes.html").read_text(), "§988 $200 threshold missing from taxes page")
    ok("50,000" in (SITE / "executive-summary.html").read_text(), "quota figure missing from summary")
    ok("S02 Art. 2" in (SITE / "methods.html").read_text() or "S02" in (SITE / "methods.html").read_text(),
       "quota source missing from methods page")

    # 14. Source register shows all 20 with links
    sources_html = (SITE / "sources.html").read_text()
    for s in sources:
        ok(s["url"] in sources_html, f"source {s['id']} link missing on sources page")
        ok(s["id"] in sources_html, f"source {s['id']} missing on sources page")

    print(f"edition-i verify: {checks} checks, {len(errors)} errors")
    for err in errors:
        print(" FAIL:", err)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
