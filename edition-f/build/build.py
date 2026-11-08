#!/usr/bin/env python3
"""Edition F static dashboard generator (pure standard library).

Reads edition-f/data/*.json and writes edition-f/site/*.html plus CSV/JSON
exports. Unknown amounts are rendered as blank cells with an unverified badge.
"""
from __future__ import annotations

import csv
import html
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SITE = ROOT / "site"
D = Decimal
CENT = D("0.01")
PCT = D("0.0001")

PAGES = [
    ("index.html", "Overview"),
    ("costs.html", "Cost ladder"),
    ("methods.html", "Methods"),
    ("mechanics.html", "Step by step"),
    ("penalty.html", "Conversion penalty"),
    ("tax.html", "Tax"),
    ("reporting.html", "US reporting"),
    ("audit.html", "Repo audit"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
    ("methodology.html", "Methodology"),
]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def esc(x):
    return html.escape(str(x), quote=True)


def money(x, places=2):
    if x is None or x == "":
        return ""
    q = D(x).quantize(D("1").scaleb(-places), rounding=ROUND_HALF_UP)
    return f"{q:,.{places}f}"


def pct(x):
    if x is None or x == "":
        return ""
    return money(x, 4) + "%"


def blank():
    return '<span class="blank-value" aria-hidden="true"></span><span class="badge unverified">unverified</span>'


def cell(value, cls=""):
    if value is None or value == "":
        return f'<td class="{cls} blank-cell">{blank()}</td>'
    return f'<td class="{cls}">{value}</td>'


class Book:
    def __init__(self):
        self.sources = {s["id"]: s for s in load("sources.json")}
        self.methods = load("methods.json")
        self.inputs = load("cost_inputs.json")
        self.penalty = load("penalty_layers.json")
        self.tax = load("tax_reporting.json")
        self.flags = {f["id"]: f for f in load("flags.json")}
        self.audit = load("repo_audit.json")

    def src(self, ids):
        out = []
        for i in ids:
            s = self.sources[i]
            kind = s["kind"]
            cls = "src official" if kind == "official" else "src provider"
            label = esc(i)
            title = esc(f'{kind}: {s["issuer"]} — {s["title"]}')
            out.append(f'<a class="{cls}" href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer" title="{title}">{label}</a>')
        return " ".join(out)

    def artifact(self, url, label="repository artifact"):
        if not url:
            return ""
        return f'<a class="src artifact" href="{esc(url)}" target="_blank" rel="noopener noreferrer" title="Primary repository artifact">{esc(label)}</a>'

    def flag_links(self, ids):
        return " ".join(f'<a class="badge flag" href="flagged.html#{esc(i)}">{esc(i)}</a>' for i in ids)


def table(book, table_id, caption, headers, rows, note=""):
    head = "".join(f"<th scope=\"col\">{esc(h)}</th>" for h in headers)
    body = "\n".join(rows)
    n = f'<p class="table-note">{note}</p>' if note else ""
    return (
        f'<div class="table-wrap" id="{esc(table_id)}" tabindex="0" role="region" aria-label="{esc(caption)}">'
        f'<table><caption>{esc(caption)}</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>{n}'
    )


def row(cells, attrs=""):
    return f'<tr {attrs}>' + "".join(cells) + "</tr>"


def compute_ladder(book):
    fx = book.inputs["fx"]
    bid = D(fx["bid_per_100_usd"]) / 100
    ask = D(fx["ask_per_100_usd"]) / 100
    mid = (bid + ask) / 2
    boc = book.inputs["boc_wire"]
    hsbc = book.inputs["hsbc_wire"]["premier_advance"]
    sky = book.inputs["skyremit"]
    sky_final = D(sky["final_usd_per_cny"])
    sky_real = D(sky["realtime_usd_per_cny"])
    sky_fee = D(sky["fee_cny"])
    sky_cap = D(sky["max_cny"])
    rows = []
    for usd in range(10000, 400001, 10000):
        u = D(usd)
        cny = u * ask
        boc_comm = min(max(cny * D(boc["commission_rate"]), D(boc["commission_min_cny"])), D(boc["commission_max_cny"]))
        boc_fee_cny = boc_comm + D(boc["cable_international_cny"])
        boc_fee_usd = boc_fee_cny / ask
        boc_spread = u * (ask - mid) / ask
        boc_cost = boc_spread + boc_fee_usd
        hsbc_comm = min(max(cny * D(hsbc["commission_rate"]), D(hsbc["commission_min_cny"])), D(hsbc["commission_max_cny"]))
        hsbc_fee_cny = hsbc_comm + D(hsbc["cable_cny"])
        sky_principal = u / sky_final
        n = int((sky_principal / sky_cap).to_integral_value(rounding=ROUND_HALF_UP))
        if D(n) * sky_cap < sky_principal:
            n += 1
        # ceiling without float math
        n = int(sky_principal // sky_cap) + (1 if sky_principal % sky_cap else 0)
        sky_fee_cny = sky_fee * n
        sky_fx_loss = sky_principal * (sky_real - sky_final)
        sky_fee_usd = sky_fee_cny * sky_final
        sky_cost = sky_fx_loss + sky_fee_usd
        rows.append({
            "target_usd": str(usd),
            "cny_principal_boc_ask": money(cny),
            "boc_commission_cny": money(boc_comm),
            "boc_cable_cny": money(boc["cable_international_cny"]),
            "boc_local_fee_cny": money(boc_fee_cny),
            "boc_local_fee_usd": money(boc_fee_usd),
            "boc_spread_proxy_usd": money(boc_spread),
            "boc_known_cost_usd": money(boc_cost),
            "boc_known_cost_pct": pct(boc_cost / u * 100),
            "hsbc_premier_advance_local_fee_cny": money(hsbc_fee_cny),
            "hsbc_private_personal_local_fee_cny": "0.00",
            "hsbc_total_cost_usd": "",
            "skyremit_principal_cny": money(sky_principal),
            "skyremit_transfers": str(n),
            "skyremit_fee_cny": money(sky_fee_cny),
            "skyremit_fx_loss_usd": money(sky_fx_loss),
            "skyremit_fee_usd": money(sky_fee_usd),
            "skyremit_scenario_cost_usd": money(sky_cost),
            "skyremit_scenario_cost_pct": pct(sky_cost / u * 100),
            "wise_total_cost_usd": "",
            "personal_tax_usd": "",
            "correspondent_receiving_fee_usd": "",
            "quota_only_fit": "yes" if usd <= 50000 else "no",
            "source_ids": ["CN01", "BK01", "BK02", "BK04", "BK10"],
        })
    return rows


def page(book, slug, title, subtitle, body):
    nav = "".join(
        f'<a href="{esc(href)}" class="{"active" if href == slug else ""}">{esc(label)}</a>'
        for href, label in PAGES
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · Edition F · CNY→USD</title>
<meta name="description" content="Independently verified CNY to USD transfer research, cost ladder, mechanics, tax/reporting and repository audit.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="index.html">CNY→USD <span>Edition F</span></a>
    <button class="nav-toggle" aria-expanded="false" aria-controls="nav" onclick="document.getElementById('nav').classList.toggle('open');this.setAttribute('aria-expanded',this.getAttribute('aria-expanded')==='false')">Menu</button>
    <nav id="nav" class="nav">{nav}</nav>
  </div>
</header>
<main id="main" class="wrap">
<section class="hero">
  <p class="eyebrow">Independent verification edition · report date 2026-11-08 UTC</p>
  <h1>{esc(title)}</h1>
  <p class="lede">{esc(subtitle)}</p>
</section>
{body}
</main>
<footer class="site-footer"><div class="wrap">
<p>Research with linked sources and shown arithmetic. Not legal, tax or investment advice, and not a bank quote. Provider tariffs support only that provider’s prices/product terms; legal propositions cite government/regulator sources. Unknown values are blank and flagged.</p>
<p><a href="sources.html">Sources</a> · <a href="flagged.html">Flagged for review</a> · <a href="methodology.html">Methodology</a> · <a href="cost-ladder.csv">CSV</a> · <a href="cost-ladder.json">JSON</a></p>
</div></footer>
</body>
</html>
"""


def status_badge(status):
    return f'<span class="badge status-{esc(status)}">{esc(status.replace("_", " "))}</span>'


def build_index(book, ladder):
    stats = [
        ("40", "USD targets", "$10,000 → $400,000 by $10,000"),
        (str(len(book.methods)), "methods inventoried", "lawful, conditional, closed-loop and prohibited"),
        (str(len(book.sources)), "sources registered", f'{sum(s["kind"] == "official" for s in book.sources.values())} official · {sum(s["kind"] == "provider-primary" for s in book.sources.values())} provider-primary'),
        ("0", "invented personal tax amounts", "unknown fees/tax stay blank"),
    ]
    stat_html = '<div class="stats">' + "".join(f'<div class="stat"><strong>{esc(v)}</strong><span>{esc(l)}</span><small>{esc(d)}</small></div>' for v, l, d in stats) + "</div>"
    start_rows = [
        row([cell("<strong>1. Separate tax from transfer cost</strong>"), cell("No transfer tax on the exchange itself was identified in the reviewed IIT Law; US tax can still arise on currency gain and worldwide income. Reporting penalties are separate."), cell(book.src(["CN20", "US01", "US05"]))]),
        row([cell("<strong>2. Identify the source of funds</strong>"), cell("Salary/current income → Art.59 documented route; property sale → 2025 property-sale guide; emigration/inheritance → 2004 transfer; corporate profits/liquidation → corporate route. Ordinary savings without a lawful source file is the hard case."), cell(book.src(["CN01", "CN14", "CN08", "CN07"]))]),
        row([cell("<strong>3. Resolve identity classification</strong>"), cell("Passport-based overseas-individual treatment conflicts with the one-year-residence domestic definition. Get the bank’s written classification before assuming the USD 50,000 quota does not apply."), cell(book.src(["CN03", "CN07", "CN01"]) + " " + book.flag_links(["F01"]))]),
        row([cell("<strong>4. Quote the actual corridor</strong>"), cell("BOC/HSBC local tariffs are known; correspondent/receiving fees and personal tax are blank. SkyRemit is a single-capture scenario; Wise has one live quote, not a 40-point curve."), cell(book.src(["BK01", "BK04", "BK10", "BK08"]) + " " + book.flag_links(["F09", "F06", "F05"]))]),
        row([cell("<strong>5. File US reports even if no tax is due</strong>"), cell("FBAR, Form 8938, Form 3520 and FinCEN 105 are reporting triggers, not conversion taxes. Current adjusted FBAR dollars are left blank."), cell(book.src(["US05", "US07", "US09", "US06"]) + " " + book.flag_links(["F03"]))]),
    ]
    quick_amounts = {10000, 50000, 100000, 200000, 400000}
    quick_rows = []
    for r in ladder:
        if int(r["target_usd"]) in quick_amounts:
            quick_rows.append(row([
                cell("$" + money(r["target_usd"], 0)),
                cell("$" + r["boc_known_cost_usd"] + " <small>(" + r["boc_known_cost_pct"] + ")</small>"),
                cell("$" + r["skyremit_scenario_cost_usd"] + " <small>(" + r["skyremit_scenario_cost_pct"] + ")</small>"),
                cell("¥" + r["hsbc_premier_advance_local_fee_cny"] + " <small>local only; FX blank</small>"),
                cell(""),
                cell(book.src(r["source_ids"])),
            ], f'data-usd="{r["target_usd"]}"'))
    fork_rows = [
        row([cell("PRC ID / domestic individual"), cell("USD 50,000/year convenience purchase quota; above quota needs documents or another route. Existing FX outbound has a separate USD 50,000/day threshold."), cell(book.src(["CN01", "CN03"]))]),
        row([cell("Passport / overseas individual"), cell("Art.59 documented lawful current-account RMB income has no stated annual cap; permanent-residence-card holders use quota. Branch acceptance and F01 conflict remain."), cell(book.src(["CN01", "CN05", "CN03"]))]),
        row([cell("Property / inheritance / emigration"), cell("Separate approval/document routes; not a general savings quota. Property-sale outbound capped at net sale proceeds with tax-certificate match."), cell(book.src(["CN08", "CN09", "CN10", "CN14"]))]),
        row([cell("Corporate profits / liquidation"), cell("FIE dividend/liquidation routes exist for genuine corporate proceeds; personal savings cannot be relabelled as corporate income."), cell(book.src(["CN07", "CN12", "CN20"]))]),
    ]
    cat_rows = [
        row([cell('<a href="costs.html">Cost ladder</a>'), cell("40 amounts; BOC known cost, SkyRemit scenario, HSBC local fee, blank tax/unknown fees; CSV/JSON."), cell(book.src(["BK01", "BK02", "BK04", "BK10"]))]),
        row([cell('<a href="methods.html">Methods</a> + <a href="mechanics.html">mechanics</a>'), cell("31 methods with pros/cons, limits and step-by-step where lawful; prohibited routes are not instructed."), cell(book.src(["CN01", "CN07", "CN18"]))]),
        row([cell('<a href="penalty.html">Conversion penalty</a>'), cell("12 layers: FX margin, wire fees, account costs, underlying tax, US FX gain, reporting penalties, unlawful fines."), cell(book.src(["BK02", "CN20", "US01", "US10"]))]),
        row([cell('<a href="tax.html">Tax</a> + <a href="reporting.html">US reporting</a>'), cell("China IIT, treaty, US worldwide income/FEIE/FTC/§988, FBAR/8938/3520/105."), cell(book.src(["CN20", "US08", "US01", "US05"]))]),
        row([cell('<a href="audit.html">Repo audit</a> + <a href="flagged.html">flags</a>'), cell("15 repository findings and 22 review flags; earlier editions preserved, not overwritten."), cell(book.artifact("https://github.com/sassnarep3-star/China1/blob/4d844a5/COORDINATION.md") + " " + book.src(["CN02"]))]),
    ]
    body = f"""
<div class="callout warn"><strong>Read this first.</strong> The BOC board used for arithmetic displays 2026-11-09 while the report date is 2026-11-08 UTC; it is reference-only. SkyRemit/Wise values are single dynamic captures. No personal tax amount, correspondent fee or receiving-bank fee is invented. {book.flag_links(['F04','F05','F06','F09','F10'])}</div>
{stat_html}
<h2>Most important actions</h2>
{table(book, 'start-here', 'What to do first', ['Priority', 'Why it matters', 'Sources'], start_rows)}
<h2>Cost snapshot — known charges only, not all-in quotes</h2>
<p>BOC “known cost” = one-way BOC board spread proxy + BOC local TT/cable fee converted at the same ask. SkyRemit “scenario” = observed rate-pair markup + CNY 79 per CNY 300,000 transfer. HSBC column is local Premier/Advance wire fee only; HSBC FX spread and total are blank. Personal tax is blank for every amount.</p>
{table(book, 'quick-costs', 'Quick cost snapshot', ['Target USD', 'BOC known cost', 'SkyRemit scenario', 'HSBC local fee', 'Personal tax', 'Sources'], quick_rows, 'Full 40-row ladder and formulas: <a href="costs.html">cost ladder</a>.')}
<h2>The decision fork</h2>
{table(book, 'decision-fork', 'Which rule applies depends on facts, not on the cheapest app', ['Fact pattern', 'Rule / constraint', 'Sources'], fork_rows)}
<h2>Browse by category</h2>
{table(book, 'categories', 'Dashboard sections', ['Section', 'Contents', 'Sources'], cat_rows)}
<div class="callout"><strong>Bottom line.</strong> For documented China salary, the Art.59 bank route is the strongest text-based path and can exceed USD 50,000; for small amounts SkyRemit’s captured scenario can be cheaper than BOC’s capped wire fee, while BOC’s capped fee can win at larger amounts. None of that is a personal tax opinion or an executable quote. Resolve classification, source documents and US reporting first.</div>
"""
    return page(book, "index.html", "Move CNY to USD without confusing fees, tax and penalties", "A source-verified dashboard for a US citizen: 40 amount scenarios, issuer-tariff arithmetic, exact lawful mechanics, tax/reporting analysis, and an audit of the repository’s earlier overclaims.", body)


def build_costs(book, ladder):
    primary = []
    detail = []
    for r in ladder:
        src = book.src(r["source_ids"])
        primary.append(row([
            cell("<strong>$" + money(r["target_usd"], 0) + "</strong>"),
            cell("$" + r["boc_known_cost_usd"] + "<br><small>" + r["boc_known_cost_pct"] + " of target</small>"),
            cell("$" + r["skyremit_scenario_cost_usd"] + "<br><small>" + r["skyremit_scenario_cost_pct"] + " of target</small>"),
            cell("¥" + r["hsbc_premier_advance_local_fee_cny"] + "<br><small>local only</small>"),
            cell(""),
            cell(src),
        ], f'data-usd="{r["target_usd"]}"'))
        detail.append(row([
            cell("$" + money(r["target_usd"], 0)),
            cell("¥" + r["cny_principal_boc_ask"]),
            cell("¥" + r["boc_local_fee_cny"]),
            cell("$" + r["boc_spread_proxy_usd"]),
            cell(r["skyremit_transfers"]),
            cell("¥" + r["skyremit_fee_cny"]),
            cell("Yes" if r["quota_only_fit"] == "yes" else "No — documents/approval/Art.59"),
            cell(src),
        ], f'data-usd="{r["target_usd"]}"'))
    coverage = []
    for m in book.methods:
        known = m["cost"]
        coverage.append(row([
            cell(f'<a href="mechanics.html#{m["id"]}">{esc(m["id"])} · {esc(m["name"])}</a>'),
            cell(esc(known)),
            cell(""),
            cell(status_badge(m["status"])),
            cell(book.src(m["sources"]) + " " + book.flag_links(m["flags"])),
        ]))
    quotes = [
        row([cell("Wise bank-funded 200,000 CNY"), cell("¥1,224.40 fee; 1 CNY = 0.1498 USD; volume discount ¥31.93; Wise-balance ¥1,208.11"), cell("Single dynamic capture; no 40-point curve"), cell(book.src(["BK08"]) + " " + book.flag_links(["F06"]))]),
        row([cell("SkyRemit calculator"), cell("¥79 fixed fee; real-time 0.149900 vs final 0.149496 USD/CNY; displayed 0.27% markup; cap ¥300,000/transfer"), cell("Scenario only; widget send/receive inconsistency flagged"), cell(book.src(["BK10"]) + " " + book.flag_links(["F05"]))]),
        row([cell("BOC optional full-amount arrival"), cell("+USD 15 where payee bank accounts with BOC New York; otherwise +USD 25 for qualifying US domestic banks"), cell("Optional; not in base known cost; overseas/receiving charges may remain"), cell(book.src(["BK01"]) + " " + book.flag_links(["F09"]))]),
        row([cell("HSBC full-delivery pre-charge"), cell("¥200 pre-charge with later top-up; SHA/BEN/OUR options"), cell("Not a verified all-in correspondent cost"), cell(book.src(["BK04"]) + " " + book.flag_links(["F09"]))]),
        row([cell("ICBC / Western Union / correspondent / receiving / personal tax"), cell(""), cell("Left blank and flagged"), cell(book.src(["BK06", "BK11", "BK01", "BK04", "CN20", "US01"]) + " " + book.flag_links(["F07", "F08", "F09", "F10"]))]),
    ]
    body = f"""
<div class="callout warn"><strong>Scenario, not permission or quote.</strong> Amounts above USD 50,000 are not automatically available under the domestic convenience quota. The ladder shows arithmetic if a lawful documented route exists. BOC board date mismatch: {book.flag_links(['F04'])}. Unknown all-in fees and personal tax remain blank: {book.flag_links(['F09','F10','F11'])}.</div>
<h2>Formulas</h2>
<ul class="formula-list">
<li>BOC CNY principal = target USD × 6.6929 (ask 669.29 per 100 USD).</li>
<li>BOC local fee = clamp(0.001 × CNY principal, ¥50, ¥260) + ¥150 cable; USD equivalent = fee ÷ 6.6929.</li>
<li>BOC one-way spread proxy = target USD × (ask − midpoint) ÷ ask, where midpoint = (6.6929 + 6.6648)/2. Round-trip proxy = (ask − bid)/ask = 0.4198479%.</li>
<li>HSBC Premier/Advance local fee = clamp(0.001 × CNY principal, ¥100, ¥500) + ¥120 cable. HSBC FX spread/total blank.</li>
<li>SkyRemit principal = target USD ÷ 0.149496; transfers = ceil(principal ÷ 300,000); fee = ¥79 × transfers; FX loss = principal × (0.149900 − 0.149496); fee USD = fee CNY × 0.149496.</li>
</ul>
<p><a class="button" href="cost-ladder.csv">Download CSV</a> <a class="button secondary" href="cost-ladder.json">Download JSON</a></p>
<h2>Primary ladder — most important columns first</h2>
{table(book, 'ladder-primary', 'USD 10,000–400,000 in USD 10,000 increments', ['Target USD', 'BOC known cost', 'SkyRemit scenario cost', 'HSBC local fee', 'Personal tax', 'Sources'], primary, 'BOC known cost excludes correspondent/receiving fees and optional full-arrival. SkyRemit is illustrative. HSBC total is blank because its FX spread was not captured.')}
<h2>Detailed inputs</h2>
{table(book, 'ladder-detail', 'Reproducible inputs behind the primary ladder', ['Target USD', 'CNY principal at BOC ask', 'BOC local fee', 'BOC spread proxy', 'SkyRemit transfers', 'SkyRemit fee', 'Quota-only fit?', 'Sources'], detail)}
<h2>Provider one-point quotes and optional charges</h2>
{table(book, 'provider-quotes', 'Captured provider inputs (not extrapolated)', ['Input', 'Captured value', 'Limit', 'Sources'], quotes)}
<h2>Method cost coverage — every method has a row; unknown totals stay blank</h2>
{table(book, 'method-cost-coverage', 'Cost coverage by method', ['Method', 'Known cost input / status', 'Personal all-in total', 'Status', 'Sources'], coverage)}
"""
    return page(book, "costs.html", "Cost ladder: $10,000 to $400,000", "Forty exact USD targets. Tariff-derived local charges and a labelled BOC spread proxy are computed; provider scenarios are single-capture; unknown fees and personal tax are blank.", body)


def build_methods(book):
    cats = {}
    for m in book.methods:
        cats.setdefault(m["category"], []).append(m)
    body = '<div class="callout">Statuses: <strong>conditional</strong> = lawful only if facts/documents match; <strong>not repatriation</strong> = closed-loop/spending; <strong>unverified</strong> = no verified outbound route/price; <strong>prohibited</strong> = no operational steps.</div>'
    for ci, (cat, ms) in enumerate(cats.items()):
        rows = []
        for m in ms:
            pros = "<ul>" + "".join(f"<li>{esc(p)}</li>" for p in m["pros"]) + "</ul>"
            cons = "<ul>" + "".join(f"<li>{esc(c)}</li>" for c in m["cons"]) + "</ul>"
            rows.append(row([
                cell(f'<a href="mechanics.html#{m["id"]}"><strong>{esc(m["id"])}</strong> {esc(m["name"])}</a><br>{status_badge(m["status"])}'),
                cell(f'<strong>Fit:</strong> {esc(m["fit"])}<br><strong>Limit:</strong> {esc(m["limit"])}'),
                cell(pros),
                cell(cons),
                cell(esc(m["cost"])),
                cell(book.src(m["sources"]) + " " + book.flag_links(m["flags"])),
            ]))
        anchor = f"cat-{ci}"
        body += f'<h2 id="{anchor}">{esc(cat)}</h2>' + table(book, f"methods-{ci}", cat, ["Method", "Fit and limit", "Pros", "Cons", "Cost input", "Sources"], rows)
    return page(book, "methods.html", "Method inventory with pros and cons", "31 paths grouped by category. Lawful mechanics are on the step-by-step page; prohibited paths are documented only as prohibited.", body)


def build_mechanics(book):
    body = '<div class="callout warn">Prohibited and unverified wrappers receive no operational instructions. “Exact” mechanics below are the published documentary sequence, not a guarantee that a branch will approve a particular account.</div>'
    for m in book.methods:
        body += f'<section class="method" id="{m["id"]}"><h2>{esc(m["id"])} · {esc(m["name"])} {status_badge(m["status"])}</h2>'
        body += f'<p><strong>Fit:</strong> {esc(m["fit"])}</p><p><strong>Limit:</strong> {esc(m["limit"])}</p><p><strong>Cost:</strong> {esc(m["cost"])}</p>'
        if m["steps"]:
            rows = []
            for n, s in enumerate(m["steps"], 1):
                rows.append(row([cell(str(n)), cell(esc(s["action"])), cell(esc(s["evidence"])), cell(book.src(s["sources"]))]))
            body += table(book, f"steps-{m['id']}", f"Steps for {m['id']}", ["Step", "Action", "Published basis", "Sources"], rows)
        else:
            reason = m.get("no_steps_reason") or "No verified operational sequence."
            body += table(book, f"steps-{m['id']}", f"Steps for {m['id']}", ["Step", "Action", "Published basis", "Sources"], [row([cell("—"), cell(esc(reason)), cell("No operational guidance for prohibited/unverified route."), cell(book.src(m["sources"]))])])
        body += f'<p class="flags">Flags: {book.flag_links(m["flags"]) or "none"}</p></section>'
    return page(book, "mechanics.html", "Step-by-step mechanics", "Published documentary sequences for lawful/conditional routes. Prohibited routes are named and penalised, not instructed.", body)


def build_penalty(book):
    rows = []
    for p in book.penalty:
        rows.append(row([cell(f'<strong>{esc(p["id"])}</strong> {esc(p["layer"])}'), cell(esc(p["value"]) if p["value"] else ""), cell(esc(p["how"])), cell(status_badge(p["status"])), cell(book.src(p["sources"]) + " " + book.flag_links(p["flags"]))]))
    body = f"""
<div class="callout"><strong>The phrase “conversion penalty” mixes at least four different things.</strong> A commercial FX margin, a transfer fee, tax on the income that created the money, and penalties for unlawful conduct or non-reporting. Only the first two are prices of a lawful transfer; the others are not avoided by choosing a cheaper app.</div>
{table(book, 'penalty-layers', 'Twelve layers, separated', ['Layer', 'Value / range', 'How it works', 'Status', 'Sources'], rows)}
<h2>What this means for least tax penalty</h2>
<ul>
<li>Do not create a taxable event just to move money: a sham service/dividend or fabricated sale can add real tax and penalties.</li>
<li>Use the route that matches the true source: documented salary (Art.59), property sale, inheritance/emigration, or genuine corporate proceeds.</li>
<li>Keep basis records: US personal FX gain above USD 200 can be recognised; “principal” is not a blanket exemption from currency-gain tax.</li>
<li>File FBAR/8938/3520/105 where triggered; reporting penalties can exceed the FX margin by orders of magnitude.</li>
</ul>
"""
    return page(book, "penalty.html", "The conversion penalty, broken down", "A deep separation of FX margin, issuer fees, access costs, underlying income tax, US currency-gain tax, reporting penalties and unlawful-route fines.", body)


def build_tax(book):
    groups = {}
    for t in book.tax:
        groups.setdefault(t["jurisdiction"], []).append(t)
    body = '<div class="callout warn">No personal tax amount is computed. The user’s residency, source of funds, basis, filing status and prior reports are unknown. Statutory rates are not a personal liability estimate.</div>'
    for j, ts in groups.items():
        rows = []
        for t in ts:
            rows.append(row([cell(f'<strong>{esc(t["id"])}</strong> {esc(t["topic"])}'), cell(esc(t["rule"])), cell(esc(t["value"]) if t["value"] else ""), cell(status_badge(t["status"])), cell(book.src(t["sources"]) + " " + book.flag_links(t["flags"]))]))
        body += f'<h2>{esc(j)}</h2>' + table(book, f"tax-{j.lower().replace(' ', '-')}", f"{j} tax and treaty rows", ["Topic", "Rule", "Value", "Status", "Sources"], rows)
    return page(book, "tax.html", "Tax analysis: China, treaty and United States", "Income tax attaches to the income event; currency exchange can still produce US FX gain; treaty relief does not erase US citizenship taxation.", body)


def build_reporting(book):
    ids = {"T15", "T16", "T17", "T18", "T19"}
    rows = []
    for t in book.tax:
        if t["id"] in ids:
            rows.append(row([cell(f'<strong>{esc(t["id"])}</strong> {esc(t["topic"])}'), cell(esc(t["rule"])), cell(esc(t["value"]) if t["value"] else ""), cell(book.src(t["sources"]) + " " + book.flag_links(t["flags"]))]))
    body = f"""
<div class="callout"><strong>Reporting is not tax.</strong> A transfer can be tax-free and still reportable; a reportable account can produce no taxable income. The largest quantified exposure in this problem is usually non-reporting, not the FX spread.</div>
{table(book, 'reporting-forms', 'US reporting triggers and penalty framework', ['Form / rule', 'Trigger and mechanics', 'Value', 'Sources'], rows)}
<h2>Practical filing sequence</h2>
<ol>
<li>Inventory every foreign financial account and maximum aggregate value during the year; test FBAR &gt; USD 10,000.</li>
<li>Test Form 8938 against residence/filing-status thresholds; attach to the return if required.</li>
<li>If a foreign individual/estate gift or bequest exceeds USD 100,000 aggregate, test Form 3520.</li>
<li>If carrying &gt; USD 10,000 cash/monetary instruments across the US border, file FinCEN 105; family aggregate applies.</li>
<li>For prior-year gaps, obtain professional advice before amended filings or streamlined procedures; do not assume penalty relief.</li>
</ol>
"""
    return page(book, "reporting.html", "US reporting: FBAR, 8938, 3520 and cash declarations", "The reporting obligations that survive even when the transfer itself produces no income tax.", body)


def build_audit(book):
    rows = []
    for a in book.audit:
        rows.append(row([
            cell(f'<strong>{esc(a["id"])}</strong><br>{status_badge(a["severity"])}'),
            cell(f'<strong>{esc(a["title"])}</strong><br>{esc(a["detail"])}'),
            cell(book.artifact(a["artifact"], "artifact")),
            cell(book.src(a["sources"])),
            cell(esc(a["action"])),
        ]))
    body = f"""
<div class="callout warn">This audit reviews repository evidence at merged main <code>4d844a5</code> and open PRs #12/#14. It does not edit earlier editions. Repository artifacts are primary evidence for repo findings; official comparator sources are linked beside them.</div>
{table(book, 'repo-audit', 'Repository irregularities and overclaims', ['ID / severity', 'Finding', 'Artifact', 'Official comparator', 'Action'], rows)}
<h2>What passed mechanically</h2>
<p>At claim time the inherited root, docs, dossier, edition-b and edition-c build/verify suites passed. That proves internal consistency and link resolution inside those editions, not external retrievability or factual correctness. Edition F adds a separate verifier and does not modify the shared workflow.</p>
"""
    return page(book, "audit.html", "Repository audit", "Line-of-evidence review of earlier editions and concurrent Edition D work, with official comparators and non-destructive actions.", body)


def build_flagged(book):
    rows = []
    for f in book.flags.values():
        links = book.src(f["sources"])
        if f.get("artifact"):
            links += " " + book.artifact(f["artifact"], "artifact")
        rows.append(row([
            cell(f'<strong id="{esc(f["id"])}">{esc(f["id"])}</strong><br>{status_badge(f["severity"])}'),
            cell(f'<strong>{esc(f["title"])}</strong><br>{esc(f["detail"])}'),
            cell(esc(f["blank_fields"]) if f["blank_fields"] else "—"),
            cell(esc(f["resolution"])),
            cell(links),
        ]))
    blank_rows = []
    for field in book.inputs["blank_fields"]:
        related = [f for f in book.flags.values() if field in f["blank_fields"].split("; ")]
        src_ids = []
        for f in related:
            src_ids.extend(f["sources"])
        src_ids = list(dict.fromkeys(src_ids)) or ["CN20", "US01"]
        blank_rows.append(row([cell(f"<code>{esc(field)}</code>"), cell(""), cell(", ".join(esc(f["id"]) for f in related) or "see flags"), cell(book.src(src_ids))]))
    body = f"""
<div class="callout warn"><strong>Nothing here is silently estimated.</strong> Blank cells are intentional. High-severity flags can change the lawful route or tax result; medium/low flags are price/document gaps. External link liveness is not continuously verified by CI.</div>
{table(book, 'flags', 'Flagged for review', ['ID / severity', 'Issue', 'Blank fields', 'Resolution', 'Sources'], rows)}
<h2>Blank fields kept blank in the cost model</h2>
{table(book, 'blank-fields', 'Unverified values are absent, not zero', ['Field', 'Value', 'Related flags', 'Sources'], blank_rows)}
"""
    return page(book, "flagged.html", "Flagged for review", "Unverified values, source conflicts, dynamic quotes and repository irregularities that remain open.", body)


def build_sources(book):
    rows = []
    for s in book.sources.values():
        supports = "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in s.get("supports", [])) + "</ul>" if s.get("supports") else ""
        rows.append(row([
            cell(f'<strong id="{esc(s["id"])}">{esc(s["id"])}</strong><br><span class="badge {"official" if s["kind"] == "official" else "provider"}">{esc(s["kind"])}</span>'),
            cell(f'<strong>{esc(s["title"])}</strong><br>{esc(s["issuer"])}'),
            cell(esc(s["accessed"])),
            cell(esc(s["evidence"]) + supports),
            cell(esc(s["limitations"])),
            cell(f'<a class="src" href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">open source</a>'),
        ]))
    body = f"""
<div class="callout"><strong>Source kinds.</strong> <em>official</em> = government/regulator/statute publisher supporting legal/tax propositions. <em>provider-primary</em> = a bank/remittance provider’s own tariff/product page supporting only that provider’s price/terms. Repository audit rows additionally link primary GitHub artifacts.</div>
{table(book, 'source-register', f'Source register ({len(book.sources)} entries)', ['ID / kind', 'Source', 'Accessed', 'Evidence read', 'Limitations', 'Link'], rows)}
"""
    return page(book, "sources.html", "Source register", "Every load-bearing source opened during research, with the specific evidence relied on and its limits.", body)


def build_methodology(book):
    checks = [
        ("Source discipline", "Legal/tax rows cite official sources; provider prices cite issuer tariffs labelled provider-primary. Unknown values are blank and flagged."),
        ("Arithmetic", "Decimal math; 40 targets from 10,000 to 400,000 by 10,000; formulas printed on the cost page; CSV/JSON exports included."),
        ("No invention", "No personal tax, correspondent fee, receiving-bank fee, HSBC FX spread, ICBC/WU fee or Wise 40-point curve is inferred."),
        ("Prohibited routes", "Named with statutory basis and penalty exposure; no operational steps."),
        ("Verification", "build.py regenerates site; verify.py checks citations, internal links/anchors, table-row source links, ladder arithmetic, blanks, prohibited-step absence and reproducibility inputs."),
        ("Limits", "External HTTP liveness is not continuously checked; official pages can move. Branch practice and personal facts decide execution. Not advice."),
    ]
    rows = [row([cell(f"<strong>{esc(k)}</strong>"), cell(esc(v)), cell(book.src(["CN01", "BK01", "US01"]))]) for k, v in checks]
    body = f"""
<h2>Build and verify</h2>
<pre><code>python3 edition-f/build/build.py
python3 edition-f/build/verify.py</code></pre>
<p>Pure Python 3 standard library. No npm, no CDN, no server-side code. The site works without JavaScript except the optional mobile menu toggle; all tables and links are plain HTML.</p>
{table(book, 'methodology-checks', 'Verification standard', ['Rule', 'Implementation', 'Sources'], rows)}
<h2>Known limitations</h2>
<ul>
<li>BOC board is reference-only and displays a date later than the report date; re-quote before execution.</li>
<li>SkyRemit widget was internally inconsistent; only the rate pair and fixed fee are used in a labelled scenario.</li>
<li>Wise pricing changed during research and only one amount was captured; no curve is extrapolated.</li>
<li>Capital Guide 2024 PDF retrieval did not return every corporate checklist section; corporate steps are framework-level and flagged.</li>
<li>Personal tax, eligibility and prior filing history are unknown; no personal liability amount is computed.</li>
</ul>
"""
    return page(book, "methodology.html", "Methodology and limits", "How the edition is built, what the checker proves, and what it deliberately does not prove.", body)


def write_exports(ladder):
    fields = list(ladder[0].keys())
    with (SITE / "cost-ladder.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in ladder:
            rr = dict(r)
            rr["source_ids"] = ";".join(r["source_ids"])
            w.writerow(rr)
    (SITE / "cost-ladder.json").write_text(json.dumps(ladder, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "assets").mkdir(exist_ok=True)
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    book = Book()
    ladder = compute_ladder(book)
    assert len(ladder) == 40
    writers = {
        "index.html": build_index,
        "costs.html": build_costs,
        "methods.html": build_methods,
        "mechanics.html": build_mechanics,
        "penalty.html": build_penalty,
        "tax.html": build_tax,
        "reporting.html": build_reporting,
        "audit.html": build_audit,
        "flagged.html": build_flagged,
        "sources.html": build_sources,
        "methodology.html": build_methodology,
    }
    for slug, fn in writers.items():
        if slug in {"index.html", "costs.html"}:
            content = fn(book, ladder)
        else:
            content = fn(book)
        (SITE / slug).write_text(content, encoding="utf-8")
    write_exports(ladder)
    css = (ROOT / "build" / "style.css").read_text(encoding="utf-8")
    (SITE / "assets" / "style.css").write_text(css, encoding="utf-8")
    print(f"edition-f: wrote {len(writers)} pages, {len(ladder)} ladder rows, {len(book.sources)} sources")


if __name__ == "__main__":
    main()
