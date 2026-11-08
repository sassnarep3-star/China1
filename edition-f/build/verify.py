#!/usr/bin/env python3
"""Edition F verification gate.

Checks citations, internal links/anchors, source links on every table row,
40-row ladder arithmetic, blank discipline, prohibited-route step absence,
and deterministic rebuild. It does NOT prove external HTTP liveness.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SITE = ROOT / "site"
D = Decimal
FAIL = []
CHECKS = 0


def check(name, ok, detail=""):
    global CHECKS
    CHECKS += 1
    if not ok:
        FAIL.append(f"{name}: {detail}")
    print(f"{'PASS' if ok else 'FAIL'} {name}" + (f" — {detail}" if detail else ""))


def load(n):
    return json.loads((DATA / n).read_text(encoding="utf-8"))


OFFICIAL_DOMAINS = ("safe.gov.cn", "gov.cn", "pbc.gov.cn", "chinatax.gov.cn", "irs.gov", "govinfo.gov", "cbp.gov", "hkma.gov.hk")
PROVIDER_DOMAINS = ("boc.cn", "bankofchina.com", "hsbc.com.cn", "icbc.com.cn", "wise.com", "skyremit.cn", "westernunion.com")
REPO_PREFIX = "https://github.com/sassnarep3-star/China1"


def host_ok(url, kind):
    h = urlparse(url).hostname or ""
    if kind == "official":
        return any(h == d or h.endswith("." + d) for d in OFFICIAL_DOMAINS)
    if kind == "provider-primary":
        return any(h == d or h.endswith("." + d) for d in PROVIDER_DOMAINS)
    return False


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.hrefs = []
        self.in_tbody = False
        self.in_row = False
        self.row_ext = False
        self.rows = []
        self.current_table = None
        self.table_rows = {}
        self.text = []
        self.has_script = False
        self.viewport = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = True
        if tag == "script":
            self.has_script = True
        if tag == "div" and "id" in a:
            self.current_table = a["id"]
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.in_row = True
            self.row_ext = False
        if tag == "a" and "href" in a:
            href = a["href"]
            self.hrefs.append(href)
            if self.in_row and href.startswith(("http://", "https://")):
                self.row_ext = True

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.in_row:
            self.rows.append(self.row_ext)
            if self.current_table:
                self.table_rows[self.current_table] = self.table_rows.get(self.current_table, 0) + 1
            self.in_row = False
        if tag == "div":
            self.current_table = None

    def handle_data(self, data):
        self.text.append(data)


def money(x, places=2):
    q = D(x).quantize(D("1").scaleb(-places), rounding=ROUND_HALF_UP)
    return f"{q:,.{places}f}"


def pct(x):
    return money(x, 4) + "%"


def recompute(inputs):
    fx = inputs["fx"]
    bid = D(fx["bid_per_100_usd"]) / 100
    ask = D(fx["ask_per_100_usd"]) / 100
    mid = (bid + ask) / 2
    boc = inputs["boc_wire"]
    hsbc = inputs["hsbc_wire"]["premier_advance"]
    sky = inputs["skyremit"]
    sf = D(sky["final_usd_per_cny"])
    sr = D(sky["realtime_usd_per_cny"])
    fee = D(sky["fee_cny"])
    cap = D(sky["max_cny"])
    out = []
    for usd in range(10000, 400001, 10000):
        u = D(usd)
        cny = u * ask
        bc = min(max(cny * D(boc["commission_rate"]), D(boc["commission_min_cny"])), D(boc["commission_max_cny"]))
        bfee = bc + D(boc["cable_international_cny"])
        bspread = u * (ask - mid) / ask
        bcost = bspread + bfee / ask
        hc = min(max(cny * D(hsbc["commission_rate"]), D(hsbc["commission_min_cny"])), D(hsbc["commission_max_cny"]))
        hfee = hc + D(hsbc["cable_cny"])
        sp = u / sf
        n = int(sp // cap) + (1 if sp % cap else 0)
        sfee = fee * n
        sloss = sp * (sr - sf)
        scost = sloss + sfee * sf
        out.append({
            "target_usd": str(usd),
            "cny_principal_boc_ask": money(cny),
            "boc_commission_cny": money(bc),
            "boc_cable_cny": money(boc["cable_international_cny"]),
            "boc_local_fee_cny": money(bfee),
            "boc_local_fee_usd": money(bfee / ask),
            "boc_spread_proxy_usd": money(bspread),
            "boc_known_cost_usd": money(bcost),
            "boc_known_cost_pct": pct(bcost / u * 100),
            "hsbc_premier_advance_local_fee_cny": money(hfee),
            "hsbc_private_personal_local_fee_cny": "0.00",
            "hsbc_total_cost_usd": "",
            "skyremit_principal_cny": money(sp),
            "skyremit_transfers": str(n),
            "skyremit_fee_cny": money(sfee),
            "skyremit_fx_loss_usd": money(sloss),
            "skyremit_fee_usd": money(sfee * sf),
            "skyremit_scenario_cost_usd": money(scost),
            "skyremit_scenario_cost_pct": pct(scost / u * 100),
            "wise_total_cost_usd": "",
            "personal_tax_usd": "",
            "correspondent_receiving_fee_usd": "",
            "quota_only_fit": "yes" if usd <= 50000 else "no",
            "source_ids": ["CN01", "BK01", "BK02", "BK04", "BK10"],
        })
    return out


def hashes():
    return {str(p.relative_to(SITE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(SITE.rglob("*")) if p.is_file()}


def main():
    sources_list = load("sources.json")
    sources = {s["id"]: s for s in sources_list}
    methods = load("methods.json")
    inputs = load("cost_inputs.json")
    penalty = load("penalty_layers.json")
    tax = load("tax_reporting.json")
    flags_list = load("flags.json")
    flags = {f["id"]: f for f in flags_list}
    audit = load("repo_audit.json")

    check("source ids unique", len(sources) == len(sources_list))
    check("source kinds valid", all(s["kind"] in {"official", "provider-primary"} for s in sources_list))
    check("source URLs on issuer domains", all(host_ok(s["url"], s["kind"]) for s in sources_list), "; ".join(s["id"] for s in sources_list if not host_ok(s["url"], s["kind"])))
    check("source evidence present", all(s.get("evidence") and s.get("accessed") for s in sources_list))

    refs = []
    def collect(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in {"sources", "source_ids"} and isinstance(v, list):
                    refs.extend(v)
                else:
                    collect(v)
        elif isinstance(obj, list):
            for x in obj:
                collect(x)
    for obj in (methods, penalty, tax, flags_list, audit):
        collect(obj)
    check("all cited source ids resolve", all(r in sources for r in refs), "; ".join(sorted(set(r for r in refs if r not in sources))))
    check("method flags resolve", all(f in flags for m in methods for f in m["flags"]))
    check("penalty/tax flags resolve", all(f in flags for row in penalty + tax for f in row["flags"]))
    check("prohibited methods have no steps", all(not m["steps"] and m.get("no_steps_reason") for m in methods if m["status"] == "prohibited"))
    check("audit artifacts are repo-primary", all(a["artifact"].startswith(REPO_PREFIX) for a in audit))
    check("flag artifacts are repo-primary", all(f.get("artifact", REPO_PREFIX).startswith(REPO_PREFIX) for f in flags_list))

    blank_fields = inputs["blank_fields"]
    flagged_blanks = set()
    for f in flags_list:
        flagged_blanks.update(x for x in f["blank_fields"].split("; ") if x)
    check("every model blank field is flagged", all(b in flagged_blanks for b in blank_fields), "; ".join(b for b in blank_fields if b not in flagged_blanks))

    ladder = json.loads((SITE / "cost-ladder.json").read_text(encoding="utf-8"))
    expected = recompute(inputs)
    check("ladder has 40 exact targets", [r["target_usd"] for r in ladder] == [str(u) for u in range(10000, 400001, 10000)])
    check("ladder recomputes from inputs", ladder == expected, "mismatch" if ladder != expected else "")
    check("unknown ladder totals remain blank", all(r["wise_total_cost_usd"] == "" and r["personal_tax_usd"] == "" and r["correspondent_receiving_fee_usd"] == "" and r["hsbc_total_cost_usd"] == "" for r in ladder))
    with (SITE / "cost-ladder.csv").open(newline="", encoding="utf-8") as fh:
        csv_rows = list(csv.DictReader(fh))
    check("CSV has 40 rows and blank unknowns", len(csv_rows) == 40 and all(r["personal_tax_usd"] == "" and r["wise_total_cost_usd"] == "" for r in csv_rows))

    pages = {}
    for p in sorted(SITE.glob("*.html")):
        parser = Page()
        parser.feed(p.read_text(encoding="utf-8"))
        pages[p.name] = parser
    check("all nav pages generated", all((SITE / href).exists() for href, _ in [
        ("index.html", ""), ("costs.html", ""), ("methods.html", ""), ("mechanics.html", ""), ("penalty.html", ""), ("tax.html", ""), ("reporting.html", ""), ("audit.html", ""), ("flagged.html", ""), ("sources.html", ""), ("methodology.html", "")]))
    check("viewport meta on every page", all(p.viewport for p in pages.values()))
    check("no external script dependency", all(not p.has_script for p in pages.values()))
    text_all = "\n".join("".join(p.text) for p in pages.values())
    check("no template placeholders", not any(x in text_all for x in ("TODO", "TBD", "Lorem", "{{", "}}")))

    internal_bad = []
    external_bad = []
    allowed_external = OFFICIAL_DOMAINS + PROVIDER_DOMAINS
    for name, p in pages.items():
        for href in p.hrefs:
            if href.startswith(("http://", "https://")):
                h = urlparse(href).hostname or ""
                ok = any(h == d or h.endswith("." + d) for d in allowed_external) or href.startswith(REPO_PREFIX)
                if not ok:
                    external_bad.append(f"{name}:{href}")
                continue
            if href.startswith("#"):
                if href[1:] not in p.ids:
                    internal_bad.append(f"{name}:{href}")
                continue
            path, _, frag = href.partition("#")
            target = (SITE / path).resolve()
            if not target.exists():
                internal_bad.append(f"{name}:{href}")
            elif frag and target.suffix == ".html":
                tp = pages.get(target.name)
                if tp is None:
                    internal_bad.append(f"{name}:{href} (unparsed target)")
                elif frag not in tp.ids:
                    internal_bad.append(f"{name}:{href} (missing anchor)")
    check("internal links and anchors resolve", not internal_bad, "; ".join(internal_bad[:10]))
    check("external links on source/repo allowlist", not external_bad, "; ".join(external_bad[:10]))

    unsourced = [(name, i) for name, p in pages.items() for i, ok in enumerate(p.rows) if not ok]
    check("every HTML table row has an external source/artifact link", not unsourced, str(unsourced[:10]))
    expected_counts = {"ladder-primary": 40, "ladder-detail": 40, "method-cost-coverage": len(methods), "source-register": len(sources), "flags": len(flags), "repo-audit": len(audit), "penalty-layers": len(penalty)}
    count_bad = {k: (pages["costs.html"].table_rows.get(k) if k.startswith("ladder") or k == "method-cost-coverage" else pages["sources.html"].table_rows.get(k) if k == "source-register" else pages["flagged.html"].table_rows.get(k) if k == "flags" else pages["audit.html"].table_rows.get(k) if k == "repo-audit" else pages["penalty.html"].table_rows.get(k)) for k in expected_counts}
    check("key table row counts match data", all(count_bad[k] == v for k, v in expected_counts.items()), str(count_bad))
    costs_html = (SITE / "costs.html").read_text(encoding="utf-8")
    check("HTML ladder exposes every target and BOC cost", all(("$" + money(r["target_usd"], 0)) in costs_html and ("$" + r["boc_known_cost_usd"]) in costs_html for r in ladder))
    check("blank cells carry unverified badge", all("blank-value" in (SITE / n).read_text(encoding="utf-8") and "unverified" in (SITE / n).read_text(encoding="utf-8") for n in ("costs.html", "flagged.html")))
    css = (SITE / "assets" / "style.css").read_text(encoding="utf-8")
    check("mobile table overflow present", "overflow-x:auto" in css)

    before = hashes()
    subprocess.run([sys.executable, str(ROOT / "build" / "build.py")], check=True, capture_output=True)
    after = hashes()
    check("rebuild is byte-identical", before == after, "changed: " + ", ".join(k for k in before if before[k] != after.get(k)) if before != after else "")

    print(f"\nRESULT: {'PASS' if not FAIL else 'FAIL'} — {CHECKS} checks, {len(FAIL)} failures")
    if FAIL:
        for f in FAIL:
            print(" -", f)
        sys.exit(1)


if __name__ == "__main__":
    main()
