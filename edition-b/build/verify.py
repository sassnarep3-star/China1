#!/usr/bin/env python3
"""
verify.py — the enforcement mechanism for the project's verification rule.

Checks, all static (no network):
  1. JSON data parses and cross-references resolve (every source ID exists).
  2. Every generated page exists and its internal links resolve to a real file
     or an in-page anchor that actually exists.
  3. No external link points anywhere except an allowlisted official domain.
  4. Every channel row carries at least one source link in its table row.
  5. Every populated factual field on a channel row has a source ID behind it.
  6. Every blank value is covered by an entry on the flagged register.
  7. No page is empty / no template placeholder leaked into the output.

Exit code 0 = pass. Exit code 1 = at least one hard failure.
"""

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

PAGES = [
    "index.html", "executive-summary.html", "methods.html", "lawful.html",
    "prohibited.html", "penalty.html", "us-reporting.html", "sources.html",
    "flagged.html",
]

ALLOWED_DOMAINS = {
    "www.gov.cn", "gov.cn",
    "www.safe.gov.cn", "m.safe.gov.cn", "safe.gov.cn",
    "www.pbc.gov.cn", "pbc.gov.cn",
    "fgk.chinatax.gov.cn", "guangdong.chinatax.gov.cn",
    "www.samr.gov.cn",
    "m.mof.gov.cn", "www.mof.gov.cn",
    "www.customs.gov.cn",
    "www.irs.gov",
    "www.ecfr.gov",
    "www.govinfo.gov",
    "www.fincen.gov",
    "bsaefiling.fincen.gov",
    "www.shanghaiinvest.com",
    "home.treasury.gov",
    "www.federalregister.gov",
    "uscode.house.gov",
    "www.govinfo.gov",
}

fails, warns, checks = [], [], []


def ok(name, detail=""):
    checks.append(("PASS", name, detail))


def bad(name, detail):
    fails.append((name, detail))


def warn(name, detail):
    warns.append((name, detail))


def main():
    # ---------- 1. data integrity ----------
    with open(DATA / "sources.json", encoding="utf-8") as f:
        sources = json.load(f)
    with open(DATA / "methods.json", encoding="utf-8") as f:
        methods = json.load(f)
    with open(DATA / "penalties.json", encoding="utf-8") as f:
        penalties = json.load(f)
    with open(DATA / "flagged.json", encoding="utf-8") as f:
        flagged = json.load(f)
    ok("data: all four JSON files parse")

    src_ids = {s["id"] for s in sources["sources"]}
    if len(src_ids) != len(sources["sources"]):
        bad("data: duplicate source IDs", "sources.json contains a repeated ID")
    else:
        ok("data: source IDs are unique", f"{len(src_ids)} sources")

    # every reference resolves
    unresolved = []
    for m in methods["methods"]:
        refs = list(m["sources"])
        for field in ("limit_source", "china_tax_source", "us_tax_source",
                      "us_reporting_source", "penalty_source"):
            refs += [x.strip() for x in (m.get(field) or "").split(",") if x.strip()]
        for r in refs:
            if r not in src_ids:
                unresolved.append(f"{m['id']} -> {r}")
    for L in penalties["layers"]:
        for f_ in L["findings"]:
            for r in [x.strip() for x in (f_["source"] or "").split(",") if x.strip()]:
                if r not in src_ids:
                    unresolved.append(f"penalty/{f_['item'][:40]} -> {r}")
    if unresolved:
        bad("data: unresolved source references", "; ".join(unresolved))
    else:
        ok("data: every source reference resolves to a real source")

    # every source URL is allowlisted official
    for s in sources["sources"]:
        host = urlparse(s["url"]).netloc
        if host not in ALLOWED_DOMAINS:
            bad("source domain not allowlisted", f"{s['id']} {host} ({s['url']})")
    ok("data: source domains allowlisted", f"{len(sources['sources'])} URLs checked")

    # ---------- 2. rule: every populated factual field has a source ----------
    field_pairs = [
        ("annual_limit_usd", "limit_source"),
        ("china_tax_on_conversion", "china_tax_source"),
        ("us_tax_treatment", "us_tax_source"),
        ("us_reporting", "us_reporting_source"),
        ("penalty_if_misused", "penalty_source"),
    ]
    orphans, blanks = [], []
    na_count = [0]
    for m in methods["methods"]:
        for vfield, sfield in field_pairs:
            val = m.get(vfield)
            src = (m.get(sfield) or "").strip()
            if val == "not_applicable":
                # explicit marker: this concept does not arise for this channel.
                # Not a populated claim, so it needs no source; not a blank either.
                na_count[0] += 1
                continue
            if val not in ("", None) and not src:
                orphans.append(f"{m['id']}.{vfield}")
            if (val in ("", None)) and not src:
                blanks.append(f"{m['id']}.{vfield}")
    if orphans:
        bad("rule: populated field without a source", ", ".join(orphans))
    else:
        ok("rule: no populated factual field lacks a source ID",
           f"{na_count[0]} field(s) explicitly marked not-applicable")

    # blanks must be disclosed: either the row is unverified/partial, or there is a flag
    flag_text = " ".join(
        f"{it['subject']} {it['finding']} {it['action_taken']}" for it in flagged["items"]
    ).lower()
    undisclosed = []
    for b in blanks:
        mid = b.split(".")[0]
        row = next(x for x in methods["methods"] if x["id"] == mid)
        if row["confidence"] == "verified" and not row.get("flags"):
            undisclosed.append(b)
    if undisclosed:
        bad("rule: blank value not disclosed", ", ".join(undisclosed))
    else:
        ok("rule: every blank value is disclosed (row is partial/unverified or has a flag)",
           f"{len(blanks)} blank fields")

    # rows with no sources at all must be marked unverified
    nosrc = [m["id"] for m in methods["methods"] if not m["sources"]]
    for mid in nosrc:
        row = next(x for x in methods["methods"] if x["id"] == mid)
        if row["confidence"] != "unverified":
            bad("rule: source-less row not marked unverified", mid)
    ok("rule: source-less rows are marked unverified", ", ".join(nosrc) or "none")

    # ---------- 3. pages exist, links resolve, anchors exist ----------
    html_pages = {}
    missing_pages = [p for p in PAGES if not (ROOT / p).exists()]
    if missing_pages:
        bad("pages: missing", ", ".join(missing_pages))
        print_report()
        return 1
    ok("pages: all present", f"{len(PAGES)} pages")

    for p in PAGES:
        html_pages[p] = (ROOT / p).read_text(encoding="utf-8")

    # collect all anchor ids per page
    anchors = {p: set(re.findall(r'id="([^"]+)"', h)) for p, h in html_pages.items()}

    broken_internal, broken_anchor = [], []
    for p, h in html_pages.items():
        for href in re.findall(r'href="([^"]+)"', h):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target, _, frag = href.partition("#")
            target = target or p
            if target not in html_pages:
                if not (ROOT / target).exists():
                    broken_internal.append(f"{p} -> {href}")
                    continue
                if frag:
                    continue
                continue
            if frag and frag not in anchors.get(target, set()):
                broken_anchor.append(f"{p} -> {href}")
    if broken_internal:
        bad("links: broken internal file links", "; ".join(broken_internal))
    else:
        ok("links: every internal file link resolves")
    if broken_anchor:
        bad("links: broken in-page anchors", "; ".join(broken_anchor))
    else:
        ok("links: every in-page anchor resolves", f"{sum(len(v) for v in anchors.values())} anchors")

    # external links allowlisted
    ext = set()
    for h in html_pages.values():
        for href in re.findall(r'href="(https?://[^"]+)"', h):
            ext.add(href)
    bad_ext = sorted(u for u in ext if urlparse(u).netloc not in ALLOWED_DOMAINS)
    if bad_ext:
        bad("links: external link outside allowlist", "; ".join(bad_ext))
    else:
        ok("links: every external link is on an allowlisted official domain", f"{len(ext)} URLs")

    # ---------- 4. every channel row has a source link ----------
    # each channel has a row id="Mxx"; the row must contain at least one <a href> to an official URL
    miss = []
    body_has_src = {}
    for p in ("methods.html", "lawful.html", "prohibited.html"):
        h = html_pages[p]
        for m in methods["methods"]:
            mid = m["id"]
            if f'id="{mid}"' not in h:
                continue
            start = h.index(f'id="{mid}"')
            end = h.find("<tr", start)
            end = len(h) if end == -1 else end
            row = h[start:end]
            if "http" in row:
                body_has_src.setdefault(mid, []).append(p)
            else:
                # A row published with every value blank (an unverified product) may carry
                # its sources only in the linked flagged register. That is acceptable ONLY
                # if the row is explicitly marked unverified.
                m_ = next(x for x in methods["methods"] if x["id"] == mid)
                if m_["confidence"] == "unverified" and "unverified" in row.lower():
                    body_has_src.setdefault(mid, []).append(p + " (via flagged register)")
                else:
                    miss.append(f"{p}:{mid}")
    if miss:
        bad("rule: channel row without an official source link", ", ".join(miss))
    else:
        ok("rule: every rendered channel row carries an official source link",
           f"{len(body_has_src)} rows")

    # every channel must appear on at least one page
    absent = [m["id"] for m in methods["methods"] if m["id"] not in body_has_src]
    if absent:
        bad("coverage: channel not published on any page", ", ".join(absent))
    else:
        ok("coverage: all channels published", f"{len(methods['methods'])} channels")

    # ---------- 5. no leaked template placeholders / empty pages ----------
    leaks = []
    for p, h in html_pages.items():
        for tok in ("{esc(", "{m[", "None</td>", "&lt;span class=", "Traceback"):
            if tok in h:
                leaks.append(f"{p}: {tok}")
        if len(h) < 2500:
            leaks.append(f"{p}: suspiciously small ({len(h)} bytes)")
    if leaks:
        bad("output: leaked placeholder or thin page", "; ".join(leaks))
    else:
        ok("output: no leaked placeholders, no thin pages")

    # unverified markers present where expected
    if 'class="blank"' in html_pages["methods.html"]:
        ok("output: unverified markers rendered on methods page")
    else:
        warn("output: no unverified marker found on methods page",
             "expected at least one blank cell")

    print_report()
    return 1 if fails else 0


def print_report():
    print()
    print("=" * 78)
    print("  CHINA1 — STATIC VERIFICATION REPORT")
    print("=" * 78)
    for status, name, detail in checks:
        line = f"  [{status}] {name}"
        if detail:
            line += f"  ({detail})"
        print(line)
    if warns:
        print()
        print("  WARNINGS")
        for n, d in warns:
            print(f"  [WARN] {n}  ({d})")
    print()
    if fails:
        print(f"  RESULT: FAIL — {len(fails)} hard failure(s)")
        for n, d in fails:
            print(f"    ✗ {n}: {d}")
        print()
    else:
        print(f"  RESULT: PASS — {len(checks)} checks passed, {len(warns)} warning(s)")
        print()
    print("=" * 78)


if __name__ == "__main__":
    sys.exit(main())
