#!/usr/bin/env python3
"""Build Edition I: datasets, cost ladder, dashboard and all subpages.

Pure Python 3 standard library. Deterministic: rerunning produces byte-identical
files. No network access is needed at build time; all inputs are transcribed in
model.py from pages retrieved and checked during the session.
"""
from __future__ import annotations

import csv
import html
import json
import math
import os
import sys
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import model as M  # noqa: E402
import audit  # noqa: E402

SITE = os.path.join(ROOT, "site")
DATA = os.path.join(ROOT, "data")
SITE_DATA = os.path.join(SITE, "data")

P = M.PARAMS
SELL = P["boc_sell"] / 100.0            # CNY per 1 USD (posted 现汇卖出价)
BUY = P["boc_buy"] / 100.0             # CNY per 1 USD (posted 现汇买入价)
MID = (SELL + BUY) / 2.0
HALF_SPREAD_CNY = SELL - MID             # CNY per USD, one-way proxy
ROUND_SPREAD_PCT = (P["boc_sell"] - P["boc_buy"]) / P["boc_sell"]
HALF_SPREAD_PCT = HALF_SPREAD_CNY / SELL

SOURCE_BY_ID = {s["id"]: s for s in M.SOURCES}


def money(v, digits=2):
    return f"{v:,.{digits}f}"


def esc(v):
    return html.escape(str(v), quote=True)


def src_links(ids, limit=None):
    ids = [i for i in ids if i in SOURCE_BY_ID]
    if limit:
        ids = ids[:limit]
    out = []
    for sid in ids:
        s = SOURCE_BY_ID[sid]
        out.append(
            f'<a class="src-chip" href="{esc(s["url"])}" target="_blank" '
            f'rel="noopener noreferrer" title="{esc(s["title"])}">{esc(sid)}</a>'
        )
    return " ".join(out)


def td(value, cls="", suffix="", blank_note=True):
    if value is None:
        note = '<span class="unverified">blank · unverified</span>' if blank_note else ""
        return f'<td class="blank {cls}"><span aria-label="blank, unverified">—</span>{note}</td>'
    return f'<td class="{cls}">{esc(value)}{esc(suffix)}</td>'


# ---------------------------------------------------------------------------
# Cost engine
# ---------------------------------------------------------------------------
def boc_tt_fee(cny_principal):
    return min(max(cny_principal * P["boc_fee_rate"], P["boc_fee_min"]), P["boc_fee_max"])


def hsbc_tt_fee(cny_principal):
    return min(max(cny_principal * P["hsbc_fee_rate"], P["hsbc_fee_min"]), P["hsbc_fee_max"])


def quote_for(cny_principal):
    """Only an exactly observed provider quote is used; no interpolation."""
    for q in M.QUOTES:
        if abs(q["amount_cny"] - cny_principal) < 0.5:
            return q
    return None


def compute_row(method, amount):
    """Return all cost components for one USD amount. None = unverified/blank."""
    cm = M.COST_MODELS[method["model"]]
    src = list(method["sources"])
    if cm.get("prohibited"):
        # No lawful execution price exists. Keep all 40 rows, keep every value
        # blank, and keep the row source-linked to the prohibiting authority.
        return OrderedDict(
            method_id=method["id"], amount_usd=amount,
            cny_principal=None, tranches=None, half_spread_cny=None,
            half_spread_usd=None, boc_tt_fee_cny=None, boc_cable_cny=None,
            hsbc_tt_fee_cny=None, hsbc_cable_cny=None, wise_fee_cny=None,
            atm_fee_cny=None, atm_withdrawals=None, chase_incoming_usd=None,
            documented_subtotal_cny=None, documented_subtotal_usd=None,
            china_tax_cny=None, us_tax_usd=None, intermediary_fee_usd=None,
            all_in_total_usd=None, sources=src,
        )
    cny = round(amount * SELL, 2)
    tranches = 1
    if cm.get("tranche_quota"):
        tranches = int(math.ceil(amount / P["annual_convenience_usd"]))

    spread_cny = round(amount * HALF_SPREAD_CNY, 2) if cm.get("spread") else None
    spread_usd = round(amount * HALF_SPREAD_PCT, 2) if cm.get("spread") else None

    boc_fee = round(boc_tt_fee(cny) * tranches, 2) if cm.get("wire_boc") else None
    cable = round(P["boc_cable"] * tranches, 2) if cm.get("wire_boc") else None
    hsbc_fee = round(hsbc_tt_fee(cny), 2) if cm.get("wire_hsbc") else None
    hsbc_cable = P["hsbc_cable"] if cm.get("wire_hsbc") else None

    q = quote_for(cny) if cm.get("wise") else None
    wise_fee = q["fee_cny"] if q else None

    atm_fee = None
    atm_withdrawals = None
    if cm.get("atm"):
        # CNY 10,000 per card per day; each withdrawal at the daily cap costs
        # min(12 + 1% * 10,000, 112) = 112 CNY under the current tariff.
        atm_withdrawals = int(math.ceil(cny / P["atm_daily_cny"]))
        per = min(P["atm_base_cny"] + P["atm_pct"] * P["atm_daily_cny"], P["atm_cap_cny"])
        atm_fee = round(per * atm_withdrawals, 2)

    chase = P["chase_incoming"] if cm.get("chase") else None

    # Documented subtotal = sum of components that are published or derived
    # from published numbers. It is deliberately NOT an all-in total.
    parts_cny = [v for v in (spread_cny, boc_fee, cable, hsbc_fee, hsbc_cable, atm_fee, wise_fee) if v is not None]
    subtotal_cny = round(sum(parts_cny), 2) if parts_cny else None
    subtotal_usd = None
    if subtotal_cny is not None:
        subtotal_usd = round(subtotal_cny / SELL + (chase or 0.0), 2)

    return OrderedDict(
        method_id=method["id"],
        amount_usd=amount,
        cny_principal=cny,
        tranches=tranches,
        half_spread_cny=spread_cny,
        half_spread_usd=spread_usd,
        boc_tt_fee_cny=boc_fee,
        boc_cable_cny=cable,
        hsbc_tt_fee_cny=hsbc_fee,
        hsbc_cable_cny=hsbc_cable,
        wise_fee_cny=wise_fee,
        atm_fee_cny=atm_fee,
        atm_withdrawals=atm_withdrawals,
        chase_incoming_usd=chase,
        documented_subtotal_cny=subtotal_cny,
        documented_subtotal_usd=subtotal_usd,
        china_tax_cny=None,          # unknown source of funds / gain
        us_tax_usd=None,             # unknown basis / gain
        intermediary_fee_usd=None,   # passed through at actual cost
        all_in_total_usd=None,       # never claimed
        sources=src,
    )


LADDER = OrderedDict(
    (m["id"], [compute_row(m, a) for a in M.AMOUNTS])
    for m in M.METHODS
)


def exposure_rows():
    rows = []
    for a in M.AMOUNTS:
        low = round(a * P["cn_escape_low"], 2)
        high = round(a * P["cn_escape_high"], 2)
        half = round(a * P["us_willful_fbar_rate"], 2)
        floor = P["us_willful_fbar_floor"]
        rows.append(OrderedDict(
            amount_usd=a,
            cn_30pct=low,
            cn_100pct=high,
            fbar_50pct=half,
            fbar_floor=floor,
            fbar_greater_of=max(half, floor),
            fbar_nonwillful_max=P["us_nonwillful_fbar_max"],
            sources=["CN-REG-532", "US-5321", "US-1010-821"],
        ))
    return rows


EXPOSURE = exposure_rows()


# ---------------------------------------------------------------------------
# HTML shell
# ---------------------------------------------------------------------------
NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("costs.html", "Cost ladder · 40 steps"),
    ("methods.html", "All methods"),
    ("penalty.html", "Penalty breakdown"),
    ("tax-china.html", "China tax"),
    ("tax-us.html", "US tax & reporting"),
    ("sources.html", "Official sources"),
    ("repo-review.html", "Repo review"),
    ("flagged.html", "Flagged for review"),
    ("methodology.html", "Method & limits"),
    ("requirements.html", "Requirements"),
]
CATEGORY_NAV = [(f"category-{c['id']}.html", c["name"]) for c in M.CATEGORIES]

CSS = """:root{--ink:#12212e;--muted:#5d6d7b;--line:#dde5ec;--bg:#f4f7fa;--card:#fff;--accent:#0b6d62;--accent2:#0a4f8a;--warn:#9a5b00;--danger:#a32424;--chip:#eaf2f7}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
a{color:var(--accent2);text-decoration:none}
a:hover{text-decoration:underline}
.skip{position:absolute;left:-9999px;top:0;background:#fff;padding:8px 14px;z-index:99}
.skip:focus{left:8px;top:8px}
.layout{display:grid;grid-template-columns:242px minmax(0,1fr);min-height:100vh}
.side{background:#0d2733;color:#dce8ee;padding:22px 16px;position:sticky;top:0;height:100vh;overflow-y:auto}
.side .brand{font-weight:700;font-size:17px;color:#fff;letter-spacing:.2px;display:block;margin-bottom:4px}
.side .sub{font-size:12px;color:#9fb6c1;margin-bottom:18px}
.side h4{margin:18px 0 7px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:#8fabb8}
.side a{display:block;color:#dce8ee;padding:6px 9px;border-radius:6px;font-size:13.5px}
.side a:hover,.side a.active{background:#17485a;color:#fff;text-decoration:none}
.main{padding:0 0 60px;min-width:0}
.topbar{background:#fff;border-bottom:1px solid var(--line);padding:12px 24px;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.topbar .crumb{font-size:12.5px;color:var(--muted)}
.topbar .stamp{margin-left:auto;font-size:12px;color:var(--muted)}
.wrap{max-width:1120px;margin:0 auto;padding:26px 22px}
h1{font-size:29px;line-height:1.2;margin:0 0 10px;letter-spacing:-.02em}
h2{font-size:20px;margin:30px 0 10px}
h3{font-size:16px;margin:20px 0 8px}
p{margin:9px 0 14px;max-width:92ch}
.lead{font-size:17px;color:#21394a}
.hero{background:linear-gradient(135deg,#0d2733,#0b6d62);color:#fff;border-radius:14px;padding:28px 26px;margin-bottom:22px}
.hero h1{color:#fff}
.hero p{color:#d8ece8}
.hero .answer{font-size:19px;font-weight:650;margin:12px 0 0;max-width:90ch}
.badges{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 0}
.badge{background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.3);color:#fff;border-radius:999px;padding:4px 11px;font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:16px}
.card h3{margin:0 0 6px}
.card p{font-size:13.5px;color:var(--muted);margin:0 0 8px}
.card .big{font-size:24px;font-weight:700;color:var(--accent);display:block;margin:4px 0}
.stat{font-size:12px;color:var(--muted)}
.table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:10px;background:#fff;margin:12px 0 20px}
table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:640px}
caption{text-align:left;padding:11px 13px;font-weight:650;background:#f8fbfd;border-bottom:1px solid var(--line);font-size:13.5px}
th,td{padding:8px 10px;border-bottom:1px solid #edf2f6;text-align:left;vertical-align:top;white-space:nowrap}
th{background:#f8fbfd;color:#31495a;font-size:12px;text-transform:uppercase;letter-spacing:.03em;position:relative}
tbody tr:hover{background:#fbfdff}
td:first-child,th:first-child{position:sticky;left:0;background:#fff;z-index:1;font-weight:600}
th:first-child{background:#f8fbfd;z-index:2}
td.num{font-variant-numeric:tabular-nums}
td.blank{color:#8a97a1;background:#fcfdfe}
td.blank span.unverified{display:block;font-size:10.5px;color:var(--warn);white-space:normal}
td.src-cell{white-space:normal;min-width:150px}
.src-chip{display:inline-block;background:var(--chip);border:1px solid #d5e5ef;border-radius:5px;padding:1px 5px;margin:1px 3px 1px 0;font-size:10.5px;color:#0a4f8a;white-space:nowrap}
.note{background:#fff8ea;border-left:4px solid #e0a32e;padding:11px 14px;border-radius:0 8px 8px 0;margin:14px 0;font-size:13.5px}
.ok{background:#eef8f4;border-left:4px solid var(--accent)}
.bad{background:#fdf0f0;border-left:4px solid var(--danger)}
.tag{display:inline-block;border-radius:999px;padding:1px 8px;font-size:11px;font-weight:650;background:#e8f2ef;color:#0b6d62}
.tag.warn{background:#fff1d9;color:#8a5200}
.tag.bad{background:#fdeaea;color:#a32424}
ol.steps{padding-left:20px;max-width:95ch}
ol.steps li{margin:0 0 9px}
ul.tight{margin:4px 0 12px;padding-left:19px}
.foot{border-top:1px solid var(--line);margin-top:34px;padding-top:14px;color:var(--muted);font-size:12.5px}
.pill{font-size:11px;color:var(--muted)}
@media(max-width:900px){
 .layout{display:block}
 .side{position:static;height:auto;padding:14px}
 .side h4{margin-top:12px}
 .side a{display:inline-block;margin:2px 3px;padding:5px 9px;border:1px solid #2a5263}
 .side a.active{background:#17485a}
 .wrap{padding:18px 12px}
 h1{font-size:23px}
 .hero{padding:20px 16px}
 .hero .answer{font-size:16px}
 table{font-size:12.5px}
 th,td{padding:7px 8px}
 .topbar{padding:10px 12px}
 .topbar .stamp{margin-left:0;width:100%}
}
"""


def page(title, active, body, crumb=""):
    nav = []
    for href, label in NAV:
        cls = ' class="active"' if href == active else ""
        nav.append(f'<a{cls} href="{href}">{esc(label)}</a>')
    cats = "".join(f'<a href="{esc(h)}">{esc(l)}</a>' for h, l in CATEGORY_NAV)
    stamp = f"Edition I · verified {M.RETRIEVED} · session {M.SESSION}"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — China money · Edition I</title>
<meta name="description" content="Independently verified CNY to USD route, cost and tax dossier for a US citizen.">
<link rel="stylesheet" href="assets/style.css"></head>
<body><a class="skip" href="#main">Skip to content</a>
<div class="layout"><aside class="side">
<a class="brand" href="index.html">China money</a>
<div class="sub">Edition I · verified dashboard</div>
<h4>Analysis</h4>{''.join(nav)}
<h4>Categories</h4>{cats}
<div class="sub" style="margin-top:18px">Sources: official government, regulator, statute and provider-primary pages. Blank cells are unverified.</div>
</aside><div class="main">
<div class="topbar"><span class="crumb"><a href="index.html">Home</a> / {esc(crumb or title)}</span><span class="stamp">{esc(stamp)}</span></div>
<main class="wrap" id="main">
{body}
<div class="foot">Edition I · <a href="sources.html">Official sources</a> · <a href="flagged.html">Flagged for review</a> · <a href="methodology.html">Method and limits</a>. Research dossier, not legal, tax or investment advice. Retrieved {M.RETRIEVED} UTC. No executable quote, personal tax result or all-in total is claimed.</div>
</main></div></div></body></html>
"""


def table(caption, headers, rows, note=""):
    """rows: list of list[str] already HTML-rendered cells."""
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(r if isinstance(r, str) and r.startswith("<td") else td(r) for r in row) + "</tr>" for row in rows)
    n = f'<div class="note">{note}</div>' if note else ""
    return (f'<div class="table-wrap"><table><caption>{esc(caption)}</caption>'
            f'<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>{n}')


def cost_headers(method):
    cm = M.COST_MODELS[method["model"]]
    h = ["USD target", "CNY principal", "Half-spread proxy"]
    if cm.get("wire_boc"):
        h += ["BOC TT fee (CNY)", "Cable (CNY)"]
    if cm.get("tranche_quota"):
        h += ["Tranches"]
    if cm.get("wire_hsbc"):
        h += ["HSBC TT fee (CNY)", "HSBC cable (CNY)"]
    if cm.get("wise"):
        h += ["Wise observed fee (CNY)"]
    if cm.get("atm"):
        h += ["ATM fee (CNY)", "Withdrawals"]
    if cm.get("chase"):
        h += ["Chase incoming (USD)"]
    h += ["Documented subtotal (USD)", "China tax (CNY)", "US tax (USD)",
          "Intermediary fee (USD)", "All-in total (USD)", "Official sources"]
    return h


def cost_cells(method, r):
    cm = M.COST_MODELS[method["model"]]

    def cn(v, suffix=""):
        return td(f"{money(v)}{suffix}" if v is not None else None, "num")

    def n(v):
        return td(str(v) if v is not None else None, "num")

    c = [f'<td class="num">{money(r["amount_usd"],0)}</td>',
         cn(r["cny_principal"]),
         cn(r["half_spread_cny"], " CNY")]
    if cm.get("wire_boc"):
        c += [cn(r["boc_tt_fee_cny"]), cn(r["boc_cable_cny"])]
    if cm.get("tranche_quota"):
        c += [n(r["tranches"])]
    if cm.get("wire_hsbc"):
        c += [cn(r["hsbc_tt_fee_cny"]), cn(r["hsbc_cable_cny"])]
    if cm.get("wise"):
        c += [cn(r["wise_fee_cny"])]
    if cm.get("atm"):
        c += [cn(r["atm_fee_cny"]), n(r["atm_withdrawals"])]
    if cm.get("chase"):
        c += [cn(r["chase_incoming_usd"])]
    c += [cn(r["documented_subtotal_usd"]),
          td(None), td(None), td(None), td(None),
          f'<td class="src-cell">{src_links(r["sources"])}</td>']
    return c


def cost_table(method, amounts, caption):
    idx = {a: i for i, a in enumerate(M.AMOUNTS)}
    rows = [cost_cells(method, LADDER[method["id"]][idx[a]]) for a in amounts]
    note = ("<strong>How to read this table.</strong> CNY principal = USD target × 6.6919 (BOC posted "
            "现汇卖出价). Half-spread proxy = (6.6919 − 6.67785) × USD target, derived from the posted "
            "bid/ask board; it is conditional arithmetic, not a quoted fee. The documented subtotal sums "
            "only published/derived components. China tax, US tax, intermediary charges and the all-in "
            "total are deliberately blank and flagged on the <a href='flagged.html'>Flagged for review</a> page. "
            "Chase USD 15 is a provider-specific illustration, not a universal fee.")
    return table(caption, cost_headers(method), rows, note)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def write(name, title, active, body, crumb=""):
    with open(os.path.join(SITE, name), "w", encoding="utf-8") as f:
        f.write(page(title, active, body, crumb))


def headline_verdict():
    rows = [
        ["Conversion itself", "No conversion tax identified in the PRC IIT Law's nine taxable categories; a US personal FX gain up to USD 200 is not recognised under §988(e).",
         src_links(["CN-IIT-LAW", "US-988"])],
        ["What the 'considerable tax' usually is", "Tax on the underlying income (salary, 20% on asset transfers or FIE dividends), or the bank demanding tax vouchers before it will sell FX — not a tax on exchanging your own principal.",
         src_links(["CN-FAQ-SALARY-2026", "CN-IIT-LAW", "CN-DIV-2026"])],
        ["Best documented route for a US citizen", "境外个人 purchase against lawful China-source RMB income (Art. 59): passport + source documents incl. tax vouchers; no annual cap appears in the rule text; then wire to your own US account.",
         src_links(["CN-GUIDE-2020", "CN-FAQ-SALARY-2026"])],
        ["If the money is pre-emigration property", "移民转移 capital-account approval; the 2014 reform cancelled the three-year staged release and the >CNY 500,000 head-office filing.",
         src_links(["CN-PROP-2004", "CN-CAP-2014"])],
        ["Real conversion cost", "BOC counter tariff 0.1% (min CNY 50, max CNY 260) + CNY 150 cable; posted board bid/ask spread 0.4199% round trip, one-way half-spread proxy 0.2100%.",
         src_links(["BOC-TARIFF-PDF", "BOC-FX-BOARD"])],
        ["Largest number in the picture", "Willful FBAR penalty: greater of USD 165,353 (adjusted) or 50% of the account balance, per violation — resolve US reporting before moving money.",
         src_links(["US-5321", "US-1010-821", "US-FBAR"])],
        ["Do not use", "Quota splitting, underground banks, fake invoices, crypto bridges, undeclared cash: PRC fine bands up to 30% / 30%–100% and US seizure exposure.",
         src_links(["CN-REG-532", "CN-GUIDE-2020", "CN-CRYPTO-2021", "US-CBP-CASH"])],
    ]
    rows = [[td(a), f"<td>{b}</td>", f'<td class="src-cell">{c}</td>'] for a, b, c in rows]
    return table("The answer, most important information first", ["Question", "Verified answer", "Official sources"], rows)


def index_page():
    key = [10000, 50000, 100000, 200000, 400000]
    m3 = next(m for m in M.METHODS if m["id"] == "M03")
    preview = cost_table(m3, key, "Cost ladder preview · primary recommended route (M03), five key amounts")
    cards = []
    for c in M.CATEGORIES:
        n = sum(1 for m in M.METHODS if m["category"] == c["id"])
        cards.append(f'<div class="card"><h3>{esc(c["icon"])} · {esc(c["name"])}</h3><p>{esc(c["blurb"])}</p>'
                     f'<span class="stat">{n} routes</span><p><a href="category-{esc(c["id"])}.html">Open category →</a></p></div>')
    stats = [
        ("23", "routes mapped", "M"), ("40", "USD amount steps", "10k–400k"),
        (f"{len(M.SOURCES)}", "official sources", "all retrieved"),
        (f"{len(M.FLAGS)}", "flagged items", "non-blocking"),
    ]
    stat_html = "".join(f'<div class="card"><span class="big">{esc(a)}</span><strong>{esc(b)}</strong><div class="stat">{esc(c)}</div></div>' for a, b, c in stats)
    body = f"""
<div class="hero"><h1>CNY → USD, without the tax myth</h1>
<p class="answer">Converting your own money is not a taxable event in either jurisdiction; the barrier is China's
capital-account inconvertibility and the documentation the bank requires. For a US citizen with documented Chinese
earnings, the least-penalty route is the 境外个人 current-account purchase against lawful China-source RMB income,
then one direct wire.</p>
<div class="badges"><span class="badge">Verified {M.RETRIEVED} UTC</span><span class="badge">Every row source-linked</span><span class="badge">Blank = unverified</span><span class="badge">No all-in total claimed</span></div></div>
<h2>The answer, first</h2>
{headline_verdict()}
<div class="note ok"><strong>Scope.</strong> All legal and tax propositions come from government, regulator or statute
pages. A bank's or provider's own tariff supports only that institution's price. The posted BOC board is explicitly
'for reference only' and is not an executable quote. Unknown personal facts are blank, never inferred.</div>
<h2>Dashboard at a glance</h2><div class="grid">{stat_html}</div>
<h2>Cost ladder preview</h2>
<p>The full 40-step ladder for this route is on the <a href="costs.html">Cost ladder</a> page; every method also has
its own 40-row grid. <a href="data/cost-ladder.csv">Download all rows as CSV</a>.</p>
{preview}
<h2>Browse by category</h2><div class="grid">{''.join(cards)}</div>
<h2>What to do first</h2>
{table('Sequenced checks', ['Step', 'Why', 'Official sources'], [
 [td('1'), '<td>Ask the bank in writing for the account subject category and the ID on file.</td>', f'<td class="src-cell">{src_links(["CN-MEAS-2006","CN-NATIONALITY"])}</td>'],
 [td('2'), '<td>Resolve the US FBAR / Form 8938 / Schedule B position before a large inbound wire.</td>', f'<td class="src-cell">{src_links(["US-FBAR","US-8938-FBAR","US-STREAMLINED"])}</td>'],
 [td('3'), '<td>Identify the source of funds tranche by tranche and obtain tax vouchers.</td>', f'<td class="src-cell">{src_links(["CN-FAQ-SALARY-2026","CN-PROP-2004"])}</td>'],
 [td('4'), '<td>Choose the route that matches the source, convert once and wire directly.</td>', f'<td class="src-cell">{src_links(["CN-GUIDE-2020","BOC-TARIFF-PDF"])}</td>'],
 [td('5'), '<td>Report the arrival year; the Chinese account stays reportable until it is closed.</td>', f'<td class="src-cell">{src_links(["US-FBAR","US-WORLDWIDE"])}</td>'],
])}
"""
    write("index.html", "Overview", "index.html", body, "Overview")


def executive_summary_page():
    body = f"""
<h1>Executive summary</h1>
<p class="lead">Question: a US citizen holds CNY in a mainland Chinese bank account and reports being unable to
convert it to USD "without paying a considerable amount of taxes".</p>
{headline_verdict()}
<h2>1. Reframe the problem</h2>
<p>The PRC Individual Income Tax Law lists nine taxable income categories; converting one's own principal is not
one of them. US §988(e) excludes a personal FX gain up to USD 200. So the cost being described is almost always
one of three different things: (a) tax on the income that created the balance, (b) a bank requirement to produce
tax vouchers before selling FX, or (c) the bid/ask spread and wire tariff. Those are not a conversion tax.</p>
{table('The three things commonly called a "conversion tax"', ['Item', 'What it actually is', 'Official sources'], [
 [td('PRC IIT on the source'), '<td>Tax on salary, 20% flat on asset transfers / interest / dividends / dividends from FIEs (from 2026-09-01); savings-deposit interest temporarily exempt since 2008-10-09.</td>', f'<td class="src-cell">{src_links(["CN-IIT-LAW","CN-INTEREST-2008","CN-DIV-2026"])}</td>'],
 [td('Tax vouchers at the bank'), '<td>Art. 59 requires source-of-funds materials including tax vouchers for an overseas individual to buy FX against China-source income. A documentation condition, not a new levy.</td>', f'<td class="src-cell">{src_links(["CN-GUIDE-2020","CN-FAQ-SALARY-2026"])}</td>'],
 [td('Spread + wire tariff'), '<td>BOC posted board spread and its published 0.1% counter tariff + CNY 150 cable. A price, not a tax.</td>', f'<td class="src-cell">{src_links(["BOC-FX-BOARD","BOC-TARIFF-PDF"])}</td>'],
])}
<h2>2. The legal fork that decides everything</h2>
<p>个人外汇管理办法 Art. 3: current-account individual FX is administered on the convertibility principle;
capital-account individual FX is administered "according to the process of convertibility". Parking savings abroad is
a capital-account act. The USD 50,000 figure is an annual <em>purchase convenience quota</em> for 境内个人, while
USD 50,000/<em>day</em> is the remittance threshold for FX already held. Those two are routinely conflated.</p>
{table('Classification and limits', ['Position', 'Rule', 'Official sources'], [
 [td('境内个人'), '<td>Annual USD 50,000 convenience purchase quota; ID only inside it; above-quota current-account purchase with purpose documents; USD 50,000/day remittance threshold from an FX account.</td>', f'<td class="src-cell">{src_links(["CN-GUIDE-2020","CN-FAQ-QUOTA-2026","CN-FAQ-REMIT-2026"])}</td>'],
 [td('境外个人'), '<td>Art. 59 purchase against lawful China-source RMB income with ID + source documents incl. tax vouchers; no annual cap in the rule text. Art. 65 outward remittance of account FX with ID alone.</td>', f'<td class="src-cell">{src_links(["CN-GUIDE-2020","CN-FAQ-SALARY-2026"])}</td>'],
 [td('US citizen with an uncancelled PRC ID'), '<td>Nationality Law Art. 9: acquiring a foreign nationality while settled abroad automatically loses Chinese nationality, but a live ID can still cause the bank to classify the account as 境内个人.</td>', f'<td class="src-cell">{src_links(["CN-NATIONALITY","CN-MEAS-2006"])}</td>'],
])}
<h2>3. Ranked recommendation</h2>
{table('Route ranking for the stated facts', ['Rank', 'Route', 'When it wins', 'Official sources'], [
 [td('1'), '<td>M03 — 境外个人 Art. 59 purchase + direct wire</td>', '<td>Balance is documented, already-taxed China-source income; no approval, no annual cap in the rule text.</td>', f'<td class="src-cell">{src_links(["CN-GUIDE-2020","CN-FAQ-SALARY-2026"])}</td>'],
 [td('2'), '<td>M07 — 移民转移</td>', '<td>Balance is pre-emigration property and you can produce hukou cancellation + settlement certificate + tax clearance.</td>', f'<td class="src-cell">{src_links(["CN-PROP-2004","CN-CAP-2014"])}</td>'],
 [td('3'), '<td>M09 — documented property-sale proceeds</td>', '<td>Balance came from selling mainland property; 20% IIT on the gain is unavoidable.</td>', f'<td class="src-cell">{src_links(["CN-PROPERTY-FAQ","CN-IIT-LAW"])}</td>'],
 [td('4'), '<td>M11 — Wise (licensed partner)</td>', '<td>Non-mainland-Chinese with 3 years of China tax records; up to CNY 300,000 per bank-app transfer; transparent quoted fee.</td>', f'<td class="src-cell">{src_links(["WISE-GUIDE","WISE-Q-66919"])}</td>'],
 [td('5'), '<td>M13 / M16 — spend from the card or hold</td>', '<td>When no lump-sum USD balance is actually needed; avoids spread and wire entirely.</td>', f'<td class="src-cell">{src_links(["CN-ATM-2017","US-FBAR"])}</td>'],
])}
<h2>4. Penalty ladder, in order of size</h2>
{table('Ceilings, not predictions', ['Exposure', 'Ceiling', 'Official sources'], [
 [td('Willful FBAR failure'), '<td>Greater of USD 165,353 (inflation-adjusted) or 50% of the account balance at the time of the violation.</td>', f'<td class="src-cell">{src_links(["US-5321","US-1010-821"])}</td>'],
 [td('Non-willful FBAR / Form 8938'), '<td>Adjusted FBAR maximum USD 16,536; Form 8938 up to USD 10,000 plus USD 10,000 per 30 days after notice, max USD 60,000.</td>', f'<td class="src-cell">{src_links(["US-1010-821","US-8938-FBAR"])}</td>'],
 [td('PRC 逃汇 / illegal FX trading'), '<td>Fine ≤30% of the amount; 30%–100% if serious; confiscation and criminal referral where the threshold is met.</td>', f'<td class="src-cell">{src_links(["CN-REG-532"])}</td>'],
 [td('Quota splitting'), '<td>关注名单 for the listing year plus two following years; all purchases then need full documents.</td>', f'<td class="src-cell">{src_links(["CN-GUIDE-2020"])}</td>'],
 [td('Undeclared US cash'), '<td>Entire amount exposed to seizure; additional civil penalty up to the amount of the monetary instrument.</td>', f'<td class="src-cell">{src_links(["US-CBP-CASH","US-5321"])}</td>'],
])}
<h2>5. The US reporting stack</h2>
{table('Four parallel obligations', ['Filing', 'Trigger', 'Official sources'], [
 [td('FinCEN Form 114 (FBAR)'), '<td>Aggregate foreign accounts > USD 10,000 at any time in the calendar year; due April 15, automatic extension to October 15.</td>', f'<td class="src-cell">{src_links(["US-FBAR"])}</td>'],
 [td('Form 8938'), '<td>US-resident unmarried > USD 50,000 last day / > USD 75,000 during year; MFJ > USD 100,000 / > USD 150,000; higher thresholds abroad.</td>', f'<td class="src-cell">{src_links(["US-8938-FBAR"])}</td>'],
 [td('Worldwide income / Schedule B'), '<td>US citizens taxed on worldwide income; all amounts reported in USD at the prevailing rate.</td>', f'<td class="src-cell">{src_links(["US-WORLDWIDE","US-FXCURRENCY"])}</td>'],
 [td('Form 3520 Part IV'), '<td>Foreign gift/bequest from a nonresident alien or foreign estate > USD 100,000 in the year; reporting, generally not income.</td>', f'<td class="src-cell">{src_links(["US-3520-GIFTS","US-3520-INSTR"])}</td>'],
 [td('Foreign tax credit'), '<td>Form 1116 may credit qualifying PRC income tax on the same income; no credit for excluded income.</td>', f'<td class="src-cell">{src_links(["US-FTC"])}</td>'],
])}
<h2>6. What is not known</h2>
<p>Balance, source of funds, bank classification, ID/hukou status, prior US filings, exact financial product,
receiving bank, live FX quote and actual intermediary charges were not supplied. Those values are blank on every
table and published on the <a href="flagged.html">Flagged for review</a> page. Twenty flagged items are
non-blocking; they are the exact inputs a PRC lawyer and a US CPA would need.</p>
<div class="note"><strong>Not advice.</strong> This is a research dossier. Applying it requires a PRC-qualified
lawyer for the China side and a US CPA or tax attorney for the US side. Capital-account approval is discretionary.
See <a href="methodology.html">method and limits</a>.</div>
"""
    write("executive-summary.html", "Executive summary", "executive-summary.html", body, "Executive summary")


def costs_page():
    m3 = next(m for m in M.METHODS if m["id"] == "M03")
    full = cost_table(m3, M.AMOUNTS, "Full ladder · USD 10,000 to USD 400,000 in USD 10,000 steps · M03")
    # Comparison table at key amounts across representative methods
    reps = ["M01", "M02", "M03", "M04", "M07", "M11", "M12", "M14", "M18"]
    rows = []
    for a in (10000, 50000, 100000, 200000, 400000):
        i = M.AMOUNTS.index(a)
        cells = [f'<td class="num">{money(a,0)}</td>']
        for mid in reps:
            r = LADDER[mid][i]
            v = money(r["documented_subtotal_usd"]) if r["documented_subtotal_usd"] is not None else None
            cells.append(td(v, "num", blank_note=False))
        cells.append(f'<td class="src-cell">{src_links(["BOC-TARIFF-PDF","BOC-FX-BOARD","HSBC-TARIFF","WISE-Q-66919","CHASE-FEES"])}</td>')
        rows.append(cells)
    headers = ["USD target"] + [f"{mid}" for mid in reps] + ["Official sources"]
    comp = table("Method comparison · documented subtotal in USD (blank = no verified component)", headers, rows,
                 "Each column is the sum of published/derived bank-side components only, not an all-in total. "
                 "Blank means no official component was confirmed for that amount and method. Open a method page "
                 "for the full 40-row grid and the exact step list.")
    body = f"""
<h1>Cost ladder · every USD 10,000 step</h1>
<p class="lead">Most important information first: the five key amounts, then the complete 40-row ladder for the
primary recommended route, then a cross-method comparison. <a href="data/cost-ladder.csv">Download the full
CSV (all methods × 40 amounts)</a>.</p>
<div class="note"><strong>Model inputs.</strong> BOC posted board 2026-11-09 09:15:45: USD 现汇买入 666.38,
现汇卖出 669.19 (CNY per 100 USD). One USD therefore costs 6.6919 CNY at the posted sell price; the derived
one-way half-spread proxy is 0.2100% (full board round trip 0.4199%). BOC counter tariff 0.1%, min CNY 50,
max CNY 260, plus CNY 150 international cable. These are published prices, not a live quote.</div>
<h2>Five key amounts</h2>
{cost_table(m3, [10000,50000,100000,200000,400000], "Headline · primary route M03")}
<h2>Full 40-step ladder</h2>
{full}
<h2>Compare methods</h2>
{comp}
<h2>Why the all-in total is blank</h2>
{table('Unverified components', ['Component', 'Status', 'Official sources'], [
 [td('China tax on the source of funds'), '<td>Blank — depends on the source, basis and gain, none of which were supplied. The 20% statutory rate is shown as conditional arithmetic only.</td>', f'<td class="src-cell">{src_links(["CN-IIT-LAW","CN-DIV-2026"])}</td>'],
 [td('US tax on FX gain'), '<td>Blank — acquisition rate/date unknown; §988(e) USD 200 personal-transaction de minimis noted.</td>', f'<td class="src-cell">{src_links(["US-988","US-FXCURRENCY"])}</td>'],
 [td('Intermediary / correspondent fee'), '<td>Blank — BOC states overseas bank charges are passed through at actual cost, with no fixed published number.</td>', f'<td class="src-cell">{src_links(["BOC-TARIFF-PDF"])}</td>'],
 [td('Electronic-channel discount'), '<td>Blank — BOC publishes channel discounts separately; the counter tariff is the baseline.</td>', f'<td class="src-cell">{src_links(["BOC-TARIFF-PDF","BOC-TARIFF"])}</td>'],
 [td('Live FX quote'), '<td>Blank — the BOC board says 仅供参考 and the actual rate is the rate offered at the transaction channel.</td>', f'<td class="src-cell">{src_links(["BOC-FX-BOARD"])}</td>'],
])}
"""
    write("costs.html", "Cost ladder", "costs.html", body, "Cost ladder")


def methods_page():
    rows = []
    for m in M.METHODS:
        status = m["status"]
        cls = "bad" if "prohibited" in status else ("warn" if "conditional" in status or "approval" in status else "")
        rows.append([
            f'<td><a href="method-{esc(m["id"])}.html">{esc(m["id"])}</a></td>',
            f'<td>{esc(m["name"])}</td>',
            f'<td><span class="tag {cls}">{esc(status)}</span></td>',
            f'<td>{esc(next(c["name"] for c in M.CATEGORIES if c["id"]==m["category"]))}</td>',
            td(money(LADDER[m["id"]][9]["documented_subtotal_usd"]) if m["id"] in LADDER and LADDER[m["id"]][9]["documented_subtotal_usd"] is not None else None, "num", blank_note=False),
            f'<td class="src-cell">{src_links(m["sources"])}</td>',
        ])
    body = f"""
<h1>All methods</h1>
<p class="lead">23 routes in six categories. Every row links to an official source and to a method page with
pros, cons, a numbered step list and its own 40-row cost grid. The USD column is the documented subtotal at
USD 100,000 — not an all-in total.</p>
{table('Complete route inventory', ['ID', 'Method', 'Status', 'Category', 'Documented subtotal at $100,000 (USD)', 'Official sources'], rows)}
<div class="note bad"><strong>Prohibited channels have no execution steps.</strong> They are listed only to make the
statutory exposure visible. <a href="category-prohibited.html">See the prohibited category</a>.</div>
"""
    write("methods.html", "All methods", "methods.html", body, "All methods")


def method_page(m):
    cat = next(c for c in M.CATEGORIES if c["id"] == m["category"])
    if m["model"] == "prohibited":
        cost = ("<div class='note bad'>No lawful cost estimate and no execution steps are published for a "
                "prohibited channel. The 40-row grid below is kept for completeness with every numeric value "
                "blank and flagged unverified; only the statutory exposure on the "
                "<a href='penalty.html'>Penalty breakdown</a> page is shown.</div>")
        grid = cost_table(m, M.AMOUNTS, f"40-step grid · {m['id']} · all values blank / unverified")
    else:
        cost = cost_table(m, [10000, 50000, 100000, 200000, 400000], f"Headline costs · {m['id']}")
        grid = cost_table(m, M.AMOUNTS, f"Full 40-step cost grid · {m['id']}")
    pros = "".join(f"<li>{esc(x)}</li>" for x in m["pros"]) or "<li>None lawfully available.</li>"
    cons = "".join(f"<li>{esc(x)}</li>" for x in m["cons"]) or "<li>Not lawfully available.</li>"
    pc = table("Pros and cons", ["Aspect", "Detail", "Official sources"], [
        ['<td>Pros</td>', f'<td><ul class="tight">{pros}</ul></td>', f'<td class="src-cell">{src_links(m["sources"])}</td>'],
        ['<td>Cons</td>', f'<td><ul class="tight">{cons}</ul></td>', f'<td class="src-cell">{src_links(m["sources"])}</td>'],
    ])
    if m["steps"]:
        srows = []
        for i, s in enumerate(m["steps"], 1):
            srows.append([f'<td>{i}</td>', f'<td>{esc(s["text"])}</td>',
                          f'<td class="src-cell">{src_links(s["sources"])}</td>'])
        steps = table("Exactly how it works · numbered steps", ["#", "Step", "Official sources"], srows)
    else:
        steps = "<div class='note bad'>No execution steps are published for a prohibited channel.</div>"
    body = f"""
<h1>{esc(m["id"])} · {esc(m["name"])}</h1>
<p class="lead">{esc(m["summary"])}</p>
<p><span class="tag {'bad' if 'prohibited' in m['status'] else 'warn' if 'conditional' in m['status'] or 'approval' in m['status'] else ''}">{esc(m["status"])}</span>
&nbsp; Category: <a href="category-{esc(cat["id"])}.html">{esc(cat["name"])}</a></p>
<h2>Eligibility</h2><p>{esc(m["eligibility"])}</p>
<h2>Pros and cons</h2>{pc}
<h2>Step by step</h2>{steps}
<h2>Cost estimate</h2>{cost}{grid}
<h2>Source-linked cautions</h2>
{table('What is not verified for this route', ['Item', 'Status', 'Official sources'], [
 [td('China tax on source'), '<td>Blank — no source-of-funds or gain figures supplied.</td>', f'<td class="src-cell">{src_links(["CN-IIT-LAW","CN-FAQ-SALARY-2026"])}</td>'],
 [td('US tax / reporting'), '<td>Blank — no acquisition basis or filing history supplied; FBAR/8938 obligations continue.</td>', f'<td class="src-cell">{src_links(["US-988","US-FBAR"])}</td>'],
 [td('Intermediary charges'), '<td>Blank — passed through at actual cost.</td>', f'<td class="src-cell">{src_links(["BOC-TARIFF-PDF"])}</td>'],
])}
<p><a href="methods.html">← All methods</a> · <a href="costs.html">Cost ladder</a> · <a href="flagged.html">Flagged for review</a></p>
"""
    write(f"method-{m['id']}.html", f"{m['id']} {m['name']}", "methods.html", body, f"Methods / {m['id']}")


def category_page(c):
    ms = [m for m in M.METHODS if m["category"] == c["id"]]
    rows = []
    for m in ms:
        v = None
        if m["id"] in LADDER:
            r = LADDER[m["id"]][9]
            v = money(r["documented_subtotal_usd"]) if r["documented_subtotal_usd"] is not None else None
        rows.append([
            f'<td><a href="method-{esc(m["id"])}.html">{esc(m["id"])}</a></td>',
            f'<td>{esc(m["name"])}</td>',
            f'<td><span class="tag {"bad" if "prohibited" in m["status"] else ""}">{esc(m["status"])}</span></td>',
            td(v, "num", blank_note=False),
            f'<td class="src-cell">{src_links(m["sources"])}</td>',
        ])
    rows2 = []
    for m in ms:
        rows2.append([
            f'<td>{esc(m["id"])}</td>',
            f'<td>{esc(m["summary"])}</td>',
            f'<td class="src-cell">{src_links(m["sources"])}</td>',
        ])
    body = f"""
<h1>{esc(c["icon"])} · {esc(c["name"])}</h1>
<p class="lead">{esc(c["blurb"])}</p>
{table('Routes in this category', ['ID', 'Route', 'Status', 'Documented subtotal at $100,000 (USD)', 'Official sources'], rows)}
<h2>What each route does</h2>
{table('Summaries', ['ID', 'Summary', 'Official sources'], rows2)}
<p><a href="methods.html">← All methods</a> · <a href="costs.html">Cost ladder</a></p>
"""
    write(f"category-{c['id']}.html", c["name"], f"category-{c['id']}.html", body, f"Category / {c['name']}")


def penalty_page():
    layers = [
        ("FX spread (one-way proxy)", "0.2100% of the amount, derived from the posted 666.38 / 669.19 board", "Derived, conditional", ["BOC-FX-BOARD"]),
        ("FX spread (full round-trip board indicator)", f"{ROUND_SPREAD_PCT*100:.4f}% = (669.19−666.38)/669.19", "Derived, conditional", ["BOC-FX-BOARD"]),
        ("BOC counter TT fee", "0.1% of remittance, min CNY 50, max CNY 260", "Published tariff", ["BOC-TARIFF-PDF"]),
        ("BOC international cable charge", "CNY 150 per international telegram", "Published tariff", ["BOC-TARIFF-PDF"]),
        ("BOC full-amount-credit surcharge", "USD 15 (BOC NY account) or USD 25 (other) — conditional", "Published tariff, conditional", ["BOC-TARIFF-PDF"]),
        ("Chase incoming international wire", "USD 15 per transfer for personal accounts — provider-specific", "Published tariff, conditional", ["CHASE-FEES"]),
        ("Overseas/intermediary bank charges", "Passed through at actual cost; no fixed number published", "Blank · unverified", ["BOC-TARIFF-PDF"]),
        ("PRC tax on the source of funds", "20% flat on asset transfers, interest, dividends; savings interest temporarily exempt", "Blank · source unknown", ["CN-IIT-LAW", "CN-INTEREST-2008", "CN-DIV-2026"]),
        ("US tax on FX gain", "Personal gain up to USD 200 not recognised; basis and gain unknown", "Blank · unverified", ["US-988", "US-FXCURRENCY"]),
        ("US 1% remittance excise tax", "Does not apply: only US-origin remittances funded with physical instruments", "Not applicable", ["US-REMIT-TAX", "US-OBBBA"]),
        ("PRC 逃汇 / illegal FX trading fine", "≤30% of amount; 30%–100% if serious", "Statutory ceiling", ["CN-REG-532"]),
        ("Willful FBAR penalty", "Greater of USD 165,353 (adjusted) or 50% of the account balance", "Statutory ceiling", ["US-5321", "US-1010-821"]),
        ("Undeclared cash", "Entire amount exposed to seizure; declaring is free", "Statutory exposure", ["US-CBP-CASH", "US-5321"]),
    ]
    lrows = [[td(a), f"<td>{esc(b)}</td>", f"<td>{esc(c)}</td>", f'<td class="src-cell">{src_links(d)}</td>'] for a, b, c, d in layers]
    erows = []
    for r in EXPOSURE:
        erows.append([
            f'<td class="num">{money(r["amount_usd"],0)}</td>',
            f'<td class="num">{money(r["cn_30pct"])}</td>',
            f'<td class="num">{money(r["cn_100pct"])}</td>',
            f'<td class="num">{money(r["fbar_50pct"])}</td>',
            f'<td class="num">{money(r["fbar_floor"])}</td>',
            f'<td class="num">{money(r["fbar_greater_of"])}</td>',
            f'<td class="num">{money(r["fbar_nonwillful_max"])}</td>',
            f'<td class="src-cell">{src_links(r["sources"])}</td>',
        ])
    body = f"""
<h1>Conversion penalty · decomposed</h1>
<p class="lead">The "penalty" is not one number. It is a small price layer, a possible real tax on the underlying
income, and — if a shortcut is used — a very large statutory exposure. The table separates all three.</p>
{table('Every layer of the penalty', ['Layer', 'Verified value / rule', 'Status', 'Official sources'], lrows)}
<h2>Why the tax story is usually wrong</h2>
<p>The PRC IIT Law taxes nine categories of <em>income</em>. Exchanging your own principal is not on the list.
What the bank is asking for under Art. 59 is a tax <em>voucher</em> proving the income was taxed. On the US side,
§988(e) excludes a personal FX gain below USD 200, and the 1% remittance tax created in 2025 applies only to
remittances sent <em>from</em> the US using physical instruments — a China→US wire is outside it.</p>
<h2>Statutory exposure by amount</h2>
<p>These are ceilings computed by arithmetic from statutory percentages, <strong>not predicted penalties</strong>.
The Chinese bands apply to the amount illegally moved; the willful FBAR band applies to the balance in the
account. That asymmetry is why US reporting is resolved first.</p>
{table('Exposure ceilings at every USD 10,000 step', ['USD amount', 'PRC ≤30% fine (USD)', 'PRC 30–100% serious band max (USD)', 'FBAR 50% of balance (USD)', 'Adjusted floor (USD)', 'Greater of (USD)', 'Non-willful adjusted max (USD)', 'Official sources'], erows,
 'PRC columns are derived from State Council Order 532 Arts. 39/45; FBAR columns from 31 USC 5321(a)(5) and 31 CFR 1010.821. These are maxima, not predictions; no enforcement outcome is asserted.')}
"""
    write("penalty.html", "Penalty breakdown", "penalty.html", body, "Penalty breakdown")


def tax_china_page():
    rows = [
        ("Conversion of own CNY principal into FX", "Not among the nine taxable categories in IIT Law Art. 2", "No numeric rate to apply", ["CN-IIT-LAW"]),
        ("Salary / remuneration earned in China", "Comprehensive income, 3%–45% progressive (IIT Law Art. 3)", "Blank — actual taxable income unknown", ["CN-IIT-LAW", "CN-FAQ-SALARY-2026"]),
        ("Interest, dividends, asset transfer, leasing, incidental income", "20% flat (IIT Law Art. 3(3))", "Blank — gain/amount unknown", ["CN-IIT-LAW"]),
        ("Savings-deposit interest accruing from 2008-10-09", "Temporarily exempt from PRC IIT (Caishui [2008] No.132)", "0 stated as an exemption, not an estimate", ["CN-INTEREST-2008"]),
        ("FIE dividends to a foreign individual from 2026-09-01", "20% IIT; 1994 exemption repealed; withholding by the FIE", "Blank — dividend amount unknown", ["CN-DIV-2026"]),
        ("Property sale by an overseas individual", "Tax voucher required before FX purchase; Tax Filing Form above USD 50,000", "Blank — gain unknown", ["CN-PROPERTY-FAQ", "CN-TAXFILING-2013"]),
        ("Single service-trade external payment > USD 50,000", "Tax filing required (a reporting step, not a tax)", "No fee published", ["CN-TAXFILING-2013", "CN-TAXFILING-2021"]),
        ("Private study / travel / visiting relatives FX", "Exempt from that tax filing (2013 No.40 Art. 3(13))", "No fee published", ["CN-TAXFILING-2013"]),
        ("Emigration / inheritance transfer", "Tax certificate or clearance document required with the SAFE application", "Blank — tax due depends on the asset", ["CN-PROP-2004", "CN-CAP-2014"]),
        ("1% US remittance excise tax", "Not a PRC tax; does not apply to China-origin wires", "Not applicable", ["US-REMIT-TAX"]),
    ]
    trows = [[td(a), f"<td>{esc(b)}</td>", f"<td>{esc(c)}</td>", f'<td class="src-cell">{src_links(d)}</td>'] for a, b, c, d in rows]
    body = f"""
<h1>China-side tax positions</h1>
<p class="lead">Every row is source-linked. Where a number depends on personal facts that were not supplied, the
value is blank and flagged rather than estimated.</p>
{table('PRC tax and filing positions', ['Position', 'Verified rule', 'Numeric value in this edition', 'Official sources'], trows)}
<div class="note"><strong>The key distinction.</strong> A tax on the income that created the CNY, and a tax-voucher
requirement to buy FX, are not a tax on the conversion. The official 2026 SAFE Q&A restates Art. 59 in exactly those
terms: 购汇资金来源材料（含税务凭证）.</div>
"""
    write("tax-china.html", "China tax", "tax-china.html", body, "China tax")


def tax_us_page():
    rows = [
        ("Worldwide income", "US citizens are taxed on worldwide income; amounts reported in USD at the prevailing rate", "Blank — income unknown", ["US-WORLDWIDE", "US-FXCURRENCY"]),
        ("FX gain on personal disposition of CNY", "§988(e): no gain recognised for a personal transaction unless it exceeds USD 200", "Blank — basis/gain unknown", ["US-988"]),
        ("FBAR (FinCEN 114)", "Required if aggregate foreign accounts exceed USD 10,000 at any time in the year", "USD 10,000 threshold", ["US-FBAR"]),
        ("Form 8938", "US-resident unmarried > USD 50,000 last day / > USD 75,000 any time; MFJ > USD 100,000 / > USD 150,000", "Thresholds stated", ["US-8938-FBAR"]),
        ("Form 3520 Part IV", "Foreign gift/bequest from nonresident alien or foreign estate > USD 100,000 in the year", "USD 100,000 threshold", ["US-3520-GIFTS", "US-WORLDWIDE"]),
        ("Foreign tax credit", "Form 1116 may credit qualifying PRC income tax on the same income", "Blank — foreign tax paid unknown", ["US-FTC"]),
        ("Willful FBAR penalty", "Greater of USD 100,000 or 50% of the account balance; adjusted floor USD 165,353", "Ceilings, not predictions", ["US-5321", "US-1010-821"]),
        ("Non-willful FBAR penalty", "Statutory USD 10,000, adjusted to USD 16,536", "Adjusted maximum", ["US-1010-821"]),
        ("Form 8938 penalty", "Up to USD 10,000, plus USD 10,000 per 30 days after notice, max USD 60,000", "Ceilings", ["US-8938-FBAR"]),
        ("Streamlined procedures", "Available to individuals certifying non-willful conduct", "No numeric value asserted", ["US-STREAMLINED"]),
        ("Currency reporting on entry", "FinCEN 105 at USD 10,000 or more; there is no limit and no tax on declaring", "USD 10,000 threshold", ["US-CBP-CASH"]),
        ("1% remittance excise tax (IRC §4475)", "Applies to US-origin remittances paid with cash / money order / cashier's check / physical instrument", "Not applicable to China→US wires", ["US-REMIT-TAX", "US-OBBBA"]),
    ]
    trows = [[td(a), f"<td>{esc(b)}</td>", f"<td>{esc(c)}</td>", f'<td class="src-cell">{src_links(d)}</td>'] for a, b, c, d in rows]
    body = f"""
<h1>US tax & reporting</h1>
<p class="lead">For a US citizen the largest exposure is not a conversion tax: it is non-reporting. The Chinese
account is a foreign financial account for every year it exists, including the year it is emptied.</p>
{table('US tax and reporting positions', ['Position', 'Verified rule', 'Numeric value in this edition', 'Official sources'], trows)}
<div class="note bad"><strong>Order of operations.</strong> Fix the FBAR / 8938 / Schedule B history before moving a
large balance. The willful-FBAR ceiling is a percentage of the whole balance, while the PRC fine bands are a
percentage of what was moved.</div>
"""
    write("tax-us.html", "US tax & reporting", "tax-us.html", body, "US tax & reporting")


def sources_page():
    rows = []
    for s in M.SOURCES:
        rows.append([
            f'<td>{esc(s["id"])}</td>',
            f'<td><a href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">{esc(s["title"])}</a></td>',
            f'<td>{esc(s["issuer"])}</td>',
            f'<td>{esc(s["kind"])}</td>',
            f'<td>{esc(s["quote"])}</td>',
            f'<td>{esc(s["note"])}</td>',
            f'<td>{esc(M.RETRIEVED)}</td>',
            f'<td class="src-cell"><a class="src-chip" href="{esc(s["url"])}" target="_blank" rel="noopener noreferrer">open official page</a></td>',
        ])
    body = f"""
<h1>Official sources</h1>
<p class="lead">{len(M.SOURCES)} pages, all retrieved and read on {M.RETRIEVED} UTC. Government, regulator and statute
pages support legal/tax propositions; a provider's own tariff or quote supports only that provider's price. The
quote column is a verbatim excerpt for line-by-line checking.</p>
{table('Source registry', ['ID', 'Title / link', 'Issuer', 'Kind', 'Verbatim excerpt', 'Verification note', 'Retrieved', 'Link'], rows)}
"""
    write("sources.html", "Official sources", "sources.html", body, "Official sources")


def flagged_page():
    rows = []
    for f in M.FLAGS:
        rows.append([
            f'<td>{esc(f["id"])}</td>',
            f'<td><span class="tag {"bad" if f["severity"]=="high" else "warn"}">{esc(f["severity"])}</span></td>',
            f'<td>{esc(f["kind"])}</td>',
            f'<td>{esc(f["issue"])}</td>',
            f'<td>{esc(f["missing"]) if f["missing"] != "—" else "—"}</td>',
            f'<td>{esc(f["action"])}</td>',
            f'<td class="src-cell">{src_links(f["sources"])}</td>',
        ])
    body = f"""
<h1>⚑ Flagged for review</h1>
<p class="lead">Clearly labelled, non-blocking. Every item links to the official source used to identify it. Blank
cells in the cost tables correspond to the gaps below; irregularities show where inherited material was corrected.</p>
<div class="note"><strong>No value has been inferred.</strong> Where a number could not be confirmed from an
official page, the cell is literally blank and the item is listed here. These items do not block the site or the
merge; they are the inputs a PRC lawyer and a US CPA would confirm.</div>
{table('Flagged items · gaps and irregularities', ['ID', 'Severity', 'Type', 'Issue', 'What is missing', 'Action for review', 'Official sources'], rows)}
"""
    write("flagged.html", "Flagged for review", "flagged.html", body, "Flagged for review")


def repo_review_page():
    rows = [[f'<td>{esc(r["id"])}</td>', f'<td>{esc(r["finding"])}</td>',
             f'<td>{esc(r["disposition"])}</td>',
             f'<td class="src-cell">{src_links(r["sources"])}</td>'] for r in M.REPO_REVIEW]
    body = f"""
<h1>Repository review</h1>
<p class="lead">The repository contains several independently built editions. This review reads their claims
against the retrieved primary sources and logs irregularities rather than silently editing another session's files.
No inherited file was modified by Edition I.</p>
{table('Line-by-line findings on inherited editions', ['ID', 'Finding', 'Disposition in Edition I', 'Official sources'], rows)}
<div class="note ok"><strong>Scope discipline.</strong> Edition I writes only <code>edition-i/**</code>, an additive
section of <code>COORDINATION.md</code>, a short additive README note and its own workflow. Open PRs #12 and #14
belong to earlier sessions and were not merged, closed or overwritten.</div>
"""
    write("repo-review.html", "Repo review", "repo-review.html", body, "Repo review")


REQ_SOURCES = {
    "R1": ["CN-GUIDE-2020"], "R2": ["CN-GUIDE-2020", "US-988"],
    "R3": ["CN-FAQ-SALARY-2026"], "R4": ["CN-MEAS-2006"], "R5": ["CN-REG-532"],
    "R6": ["BOC-FX-BOARD", "BOC-TARIFF-PDF"], "R7": ["BOC-FX-BOARD", "BOC-TARIFF-PDF"],
    "R8": ["BOC-TARIFF-PDF", "HSBC-TARIFF"], "R9": ["CN-GUIDE-2020"],
    "R10": ["BOC-FX-BOARD"], "R11": ["US-FBAR"], "R12": ["CN-GUIDE-2020", "US-5321"],
    "R13": ["CN-CAP-2014"], "R14": ["US-988", "BOC-FX-BOARD"],
    "R15": ["CN-MEAS-2006"], "R16": ["CN-REG-532"], "R17": ["CN-GUIDE-2020"],
    "R18": ["BOC-TARIFF-PDF", "US-1010-821"], "R19": ["CN-CAP-2014"],
    "R20": ["US-REMIT-TAX"], "R21": ["US-FBAR", "US-988"],
}


def requirements_page():
    rows = [[f'<td>{esc(r["id"])}</td>', f'<td>{esc(r["text"])}</td>',
             f'<td>{esc(r["status"])}</td>', f'<td>{esc(r["where"])}</td>',
             f'<td class="src-cell">{src_links(REQ_SOURCES[r["id"]])}</td>'] for r in M.REQUIREMENTS]
    body = f"""
<h1>Requirements traceability</h1>
<p class="lead">Every requirement from the brief restated as a testable item, with the artifact that satisfies it.
Status is updated in <code>COORDINATION.md</code> when the PR is merged and Pages deployment is confirmed.</p>
{table('Full requirements list', ['#', 'Requirement', 'Status', 'Where satisfied', 'Official sources'], rows)}
"""
    write("requirements.html", "Requirements", "requirements.html", body, "Requirements")


def methodology_page():
    qrows = []
    for q in M.QUOTES:
        qrows.append([
            f'<td class="num">{money(q["amount_cny"],0)} CNY</td>',
            f'<td class="num">{money(q["fee_cny"])} CNY</td>',
            f'<td class="num">{money(q["balance_fee_cny"])} CNY</td>',
            td(money(q["discount_cny"]) + " CNY" if q["discount_cny"] is not None else None, "num"),
            f'<td class="src-cell">{src_links([q["src"]])}</td>',
        ])
    body = f"""
<h1>Method and limits</h1>
<h2>1. How the numbers were produced</h2>
{table('Published inputs and derived arithmetic', ['Input', 'Value', 'Source', 'Derived result'], [
 [td('BOC posted USD 现汇买入 / 现汇卖出'), '<td>666.38 / 669.19 CNY per 100 USD</td>', f'<td class="src-cell">{src_links(["BOC-FX-BOARD"])}</td>', f'<td>6.6638 / 6.6919 CNY per USD; midpoint 6.67785</td>'],
 [td('Full board round-trip spread'), '<td>(669.19 − 666.38) / 669.19</td>', f'<td class="src-cell">{src_links(["BOC-FX-BOARD"])}</td>', f'<td>{ROUND_SPREAD_PCT*100:.4f}%</td>'],
 [td('One-way half-spread proxy'), '<td>(6.6919 − 6.67785) / 6.6919</td>', f'<td class="src-cell">{src_links(["BOC-FX-BOARD"])}</td>', f'<td>{HALF_SPREAD_PCT*100:.4f}% — conditional arithmetic, not a quoted fee</td>'],
 [td('BOC TT fee'), '<td>0.1%, min CNY 50, max CNY 260</td>', f'<td class="src-cell">{src_links(["BOC-TARIFF-PDF"])}</td>', '<td>Applied to CNY principal; multiplied by quota-derived tranche count where relevant</td>'],
 [td('BOC international cable'), '<td>CNY 150 per telegram</td>', f'<td class="src-cell">{src_links(["BOC-TARIFF-PDF"])}</td>', '<td>Added once per wire / tranche</td>'],
 [td('Chase incoming international wire'), '<td>USD 15 per transfer</td>', f'<td class="src-cell">{src_links(["CHASE-FEES"])}</td>', '<td>Illustrative, provider-specific; conditional</td>'],
 [td('Annual convenience quota'), '<td>USD 50,000 per person per year</td>', f'<td class="src-cell">{src_links(["CN-GUIDE-2020"])}</td>', '<td>Tranche count = ceil(USD amount / 50,000)</td>'],
 [td('ATM limits'), '<td>CNY 100,000/year per person; CNY 10,000/day per card</td>', f'<td class="src-cell">{src_links(["CN-ATM-2017"])}</td>', '<td>Withdrawals = ceil(CNY principal / 10,000); fee = withdrawals × min(12 + 1%×10,000, 112) = 112 CNY</td>'],
 [td('Statutory exposure'), '<td>30% / 100% PRC bands; 50% FBAR; USD 165,353 adjusted floor</td>', f'<td class="src-cell">{src_links(["CN-REG-532","US-5321","US-1010-821"])}</td>', '<td>Ceilings by arithmetic, never predictions</td>'],
])}
<h2>2. Observed provider quotes (no interpolation)</h2>
{table('Wise public quotes retrieved', ['CNY sent', 'Bank-transfer fee', 'Wise-balance fee', 'Displayed volume discount', 'Official source'], qrows,
 'Only these four amounts were observed. Above CNY 300,000 the provider page returned a waiting-list notice, so all other Wise cost cells are blank and flagged. No fee formula was inferred.')}
<h2>3. Verification standard</h2>
<ul class="tight">
<li>Government, regulator or statute pages support legal and tax propositions.</li>
<li>A provider's own tariff or quote supports only that provider's price or product terms.</li>
<li>Every displayed table row carries at least one link to a retrieved official page.</li>
<li>Any value not confirmed from an official page is <code>None</code> in the data, renders as a blank cell, and appears on Flagged for Review.</li>
<li>Derived arithmetic is allowed only when both inputs and the formula are shown and sourced; it is labelled conditional.</li>
<li>Internal checkers prove consistency, arithmetic, citations and link resolution — not external retrievability or the correctness of a personal eligibility determination.</li>
</ul>
<h2>4. Known limits</h2>
<ul class="tight">
<li>The BOC board is explicitly for reference only; the actual rate is offered at the transaction channel.</li>
<li>No personal balance, source of funds, tax residency, US filing history, receiving bank or executable quote was supplied.</li>
<li>Capital-account approval is discretionary; no processing time or local document checklist was published in the retrieved instruments.</li>
<li>Criminal exposure beyond the statutory referral language is outside scope.</li>
<li>This is a research dossier, not legal, tax or investment advice.</li>
</ul>
"""
    write("methodology.html", "Method & limits", "methodology.html", body, "Method & limits")


# ---------------------------------------------------------------------------
# Markdown deliverables, research notes and landing redirect
# ---------------------------------------------------------------------------
VERIFICATION_RESULTS = [
    ("Deterministic rebuild", "pending local run"),
    ("Arithmetic recomputation of 920 ladder rows and 40 exposure rows", "pending local run"),
    ("Official-source registry / allowlist / citation-row gate", "pending local run"),
    ("Blank-not-zero, flagged-item and prohibited-route gates", "pending local run"),
    ("Internal links, fragments and orphan-page graph", "pending local run"),
    ("Local HTTP 200 for every HTML, CSS, CSV and JSON page", "pending local run"),
    ("Inherited checkers", "pending local run"),
    ("GitHub Actions check run", "pending PR"),
    ("GitHub Pages deployment", "pending merge"),
]


def md_sources(ids):
    return ", ".join(f"[{i}]({SOURCE_BY_ID[i]['url']})" for i in ids if i in SOURCE_BY_ID)


def md_esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def write_docs():
    key_rows = [
        ("Conversion of own principal", "No conversion tax identified in the PRC IIT Law's nine categories; US §988(e) excludes a personal FX gain up to USD 200.", ["CN-IIT-LAW", "US-988"]),
        ("Primary route", "境外个人 Art. 59 purchase against documented lawful China-source RMB income, then a direct wire to your own US account.", ["CN-GUIDE-2020", "CN-FAQ-SALARY-2026"]),
        ("If the balance is property", "移民转移 approval under the 2004 measures; the 2014 reform cancelled the staged release and >CNY 500,000 head-office filing.", ["CN-PROP-2004", "CN-CAP-2014"]),
        ("Documented conversion cost", "BOC TT 0.1% (min CNY 50, max CNY 260) + CNY 150 cable; posted board round-trip spread 0.4199%, one-way half-spread proxy 0.2100%.", ["BOC-TARIFF-PDF", "BOC-FX-BOARD"]),
        ("Largest exposure", "Willful FBAR penalty: greater of USD 165,353 adjusted floor or 50% of the account balance, per violation.", ["US-5321", "US-1010-821"]),
        ("US 1% remittance tax", "Does not apply to China→US bank wires; it applies only to US-origin remittances funded with physical instruments.", ["US-REMIT-TAX", "US-OBBBA"]),
        ("Do not use", "Quota splitting, underground banks, fake invoices, crypto bridges and undeclared cash carry PRC fine bands and US seizure exposure.", ["CN-REG-532", "CN-CRYPTO-2021", "US-CBP-CASH"]),
    ]
    lines = [
        "# Executive summary — China money, Edition I\n",
        f"Session `{M.SESSION}` · verified {M.RETRIEVED} UTC · live dashboard: {M.PUBLIC_SITE_URL}\n",
        "**Question.** A US citizen holds CNY in a mainland-China bank account and reports being unable to convert / transfer it to USD without considerable taxes.\n",
        "## The answer, most important first\n",
        "| Question | Verified answer | Official sources |\n|---|---|---|\n",
    ]
    for a, b, ids in key_rows:
        lines.append(f"| {md_esc(a)} | {md_esc(b)} | {md_sources(ids)} |\n")
    U = lambda sid: SOURCE_BY_ID[sid]["url"]
    lines += [
        "\n## 1. The tax premise is wrong\n",
        f"The PRC Individual Income Tax Law taxes nine categories of **income**; exchanging one's own principal is not one of them ([CN-IIT-LAW]({U('CN-IIT-LAW')})). US §988(e) does not recognise a personal-transaction FX gain unless it exceeds USD 200 ([US-988]({U('US-988')})). What is commonly described as a conversion tax is actually tax on the underlying income, a **tax-voucher requirement** at the bank, or the FX spread plus wire tariff.\n",
        f"- PRC tax on the source remains real: 20% flat on asset transfers, interest, dividends and incidental income ([CN-IIT-LAW]({U('CN-IIT-LAW')})); savings-deposit interest temporarily exempt since 2008-10-09 ([CN-INTEREST-2008]({U('CN-INTEREST-2008')})); foreign-individual FIE dividends taxed 20% from 2026-09-01 ([CN-DIV-2026]({U('CN-DIV-2026')})).\n",
        f"- Art. 59 requires source-of-funds materials **including tax vouchers** for an overseas individual buying FX against lawful China-source RMB income ([CN-GUIDE-2020]({U('CN-GUIDE-2020')}); [CN-FAQ-SALARY-2026]({U('CN-FAQ-SALARY-2026')})).\n",
        f"- The BOC posted board is for reference only and the bank's actual channel rate governs ([BOC-FX-BOARD]({U('BOC-FX-BOARD')})). The published counter tariff is a price, not a tax ([BOC-TARIFF-PDF]({U('BOC-TARIFF-PDF')})).\n",
        "\n## 2. Classification decides the route\n",
        f"PBOC Decree [2006] No.3 distinguishes 境内个人 / 境外个人 and applies convertibility to current-account items but a staged convertibility process to capital-account items ([CN-MEAS-2006]({U('CN-MEAS-2006')})). USD 50,000/year is an annual **purchase convenience quota** for 境内个人, not an absolute ceiling: documented non-quota current-account purchase is allowed under Art. 56 ([CN-GUIDE-2020]({U('CN-GUIDE-2020')}); [CN-FAQ-QUOTA-2026]({U('CN-FAQ-QUOTA-2026')})). USD 50,000/**day** is a separate remittance-document threshold for FX already in the account ([CN-FAQ-REMIT-2026]({U('CN-FAQ-REMIT-2026')})). A US passport holder with a live PRC ID can still be misclassified by the bank; Nationality Law Art. 9 is relevant ([CN-NATIONALITY]({U('CN-NATIONALITY')})).\n",
        "\n## 3. Ranked recommendation\n",
        "| Rank | Route | Condition | Official sources |\n|---|---|---|---|\n",
        f"| 1 | Art. 59 purchase + direct wire (M03) | Documented, already-taxed China-source income; no annual cap in the rule text | {md_sources(['CN-GUIDE-2020','CN-FAQ-SALARY-2026'])} |\n",
        f"| 2 | 移民转移 (M07) | Pre-emigration property, hukou cancellation, settlement certificate, tax clearance | {md_sources(['CN-PROP-2004','CN-CAP-2014'])} |\n",
        f"| 3 | Documented property-sale proceeds (M09) | Property sale; 20% IIT on the gain is unavoidable | {md_sources(['CN-PROPERTY-FAQ','CN-IIT-LAW'])} |\n",
        f"| 4 | Wise licensed partner (M11) | Non-mainland-Chinese with three years of China tax records; CNY 300,000 single-transfer cap | {md_sources(['WISE-GUIDE','WISE-Q-66919'])} |\n",
        f"| 5 | Card spend / hold (M13, M16) | No lump-sum USD balance actually needed | {md_sources(['CN-ATM-2017','US-FBAR'])} |\n",
        "\n## 4. Penalty ladder and US reporting\n",
        f"- PRC 逃汇 / illegal FX trading: fine ≤30%, serious 30%–100% of the amount ([CN-REG-532]({U('CN-REG-532')})).\n",
        f"- Willful FBAR: greater of USD 165,353 adjusted floor or 50% of the **account balance** at the violation ([US-5321]({U('US-5321')}); [US-1010-821]({U('US-1010-821')})).\n",
        f"- Non-willful FBAR adjusted maximum USD 16,536; Form 8938 failure up to USD 10,000 plus USD 10,000/30 days after notice, max USD 60,000 ([US-1010-821]({U('US-1010-821')}); [US-8938-FBAR]({U('US-8938-FBAR')})).\n",
        f"- FBAR threshold: aggregate foreign accounts > USD 10,000 at any time in the year; due April 15, automatic extension to October 15 ([US-FBAR]({U('US-FBAR')})). Form 8938 thresholds are higher ([US-8938-FBAR]({U('US-8938-FBAR')})).\n",
        f"- US citizens report worldwide income in USD; Form 3520 Part IV applies to a >USD 100,000 foreign gift/bequest from a nonresident alien or foreign estate ([US-WORLDWIDE]({U('US-WORLDWIDE')}); [US-3520-GIFTS]({U('US-3520-GIFTS')})).\n",
        "\n## 5. What remains blank\n",
        "Balance, source of funds, account classification, ID/hukou status, prior US filings, exact product, receiving bank, live quote and intermediary charges were not supplied. Numeric cells depending on them are blank and published on the [Flagged for Review](site/flagged.html) page. The statutory ceilings on the [Penalty breakdown](site/penalty.html) page are arithmetic maxima, never predicted assessments.\n",
        "\n## 6. Limits\n",
        "This is a source-linked research dossier, not legal, tax or investment advice. Applying it requires a PRC-qualified lawyer and a US CPA or tax attorney. Capital-account approval is discretionary. No executable quote, no personal tax result and no all-in total is claimed. See [Method and limits](site/methodology.html).\n",
    ]
    with open(os.path.join(ROOT, "EXECUTIVE_SUMMARY.md"), "w", encoding="utf-8") as f:
        f.write("".join(lines))

    req = [
        "# Full requirements traceability — Edition I\n",
        f"Session `{M.SESSION}` · verified {M.RETRIEVED} UTC. Every row links to an official source; R20 is completed only after the PR merge and live Pages deployment are confirmed.\n",
        "| # | Requirement | Status | Where satisfied | Official sources |\n|---|---|---|---|---|\n",
    ]
    for r in M.REQUIREMENTS:
        req.append(f"| {r['id']} | {md_esc(r['text'])} | {md_esc(r['status'])} | {md_esc(r['where'])} | {md_sources(REQ_SOURCES[r['id']])} |\n")
    req += [
        "\n## Source standard\n",
        "Government, regulator and statute pages support legal and tax propositions. A provider's own tariff/quote supports only that provider's price or product terms. Derived arithmetic is allowed only when the inputs and formula are shown and sourced, and is labelled conditional. Unknown values are blank and flagged, never inferred.\n",
        "\n## Verification\n",
        "Run `python3 edition-i/build/build.py` then `python3 edition-i/build/verify.py`. The verifier recomputes all cost cells, checks official-source links on every generated table row, resolves internal links and anchors, proves byte-identical rebuilds, and performs local HTTP 200 checks. The full research log is in [`research/`](research/README.md).\n",
    ]
    with open(os.path.join(ROOT, "REQUIREMENTS.md"), "w", encoding="utf-8") as f:
        f.write("".join(req))

    readme = f"""# Edition I — verified China-money dashboard

- **Live dashboard:** {M.PUBLIC_SITE_URL}
- **Short redirect:** https://sassnarep3-star.github.io/China1/edition-i/
- **Session:** `{M.SESSION}`; sources retrieved {M.RETRIEVED} UTC.
- **Scope:** 23 routes, 6 categories, 40 USD amount steps per route (920 rows), {len(M.SOURCES)} official/provider-primary sources, {len(M.FLAGS)} flagged items, {len(M.REPO_REVIEW)} repo-review findings, {len(M.REQUIREMENTS)} requirements.

Pages: [overview](site/index.html), [executive summary](site/executive-summary.html), [cost ladder](site/costs.html),
[all methods](site/methods.html), [penalty breakdown](site/penalty.html), [China tax](site/tax-china.html),
[US tax & reporting](site/tax-us.html), [official sources](site/sources.html), [repo review](site/repo-review.html),
[Flagged for Review](site/flagged.html), [method & limits](site/methodology.html), [requirements](site/requirements.html).

Build and verify:

```sh
python3 edition-i/build/build.py
python3 edition-i/build/verify.py
```

No user input was required. Values not confirmed from an official page are blank and flagged. This is research, not
legal, tax or investment advice.
"""
    with open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)


def write_research():
    research = os.path.join(ROOT, "research")
    os.makedirs(research, exist_ok=True)

    # Retrieval log with exact URL, verbatim excerpt, source kind, and chunk note.
    out = [
        "# Primary-source retrieval log — Edition I\n",
        f"Session `{M.SESSION}` · retrieved {M.RETRIEVED} UTC.\n",
        "Every URL below is the exact URL retrieved during the research pass. `quote` is a short verbatim excerpt for line-by-line checking; raw full-page content was not saved separately. Provider pages support only provider-specific prices or product terms, never a legal entitlement.\n",
        "\n## Chunk-coverage caveat\n",
        M.DEFAULT_CHUNK_NOTE + "\n",
        "\n## Registry\n",
        "| ID | Issuer / kind | Exact official URL | Verbatim excerpt | Verification note | Chunk note |\n|---|---|---|---|---|---|\n",
    ]
    for s in M.SOURCES:
        chunk = M.CHUNK_LOG.get(s["id"], M.DEFAULT_CHUNK_NOTE)
        out.append(f"| {s['id']} | {md_esc(s['issuer'])} / {md_esc(s['kind'])} | [{md_esc(s['url'])}]({s['url']}) | {md_esc(s['quote'])} | {md_esc(s['note'])} | {md_esc(chunk)} |\n")
    out.append("\nNo third-party search result is cited as legal authority; web search was used only to locate the primary pages above.\n")
    with open(os.path.join(research, "retrieval-log.md"), "w", encoding="utf-8") as f:
        f.write("".join(out))

    notes = f"""# Primary-source legal and tax notes — Edition I

Session `{M.SESSION}` · {M.RETRIEVED} UTC. Each bullet below is a proposition transcribed from the linked official page. Where a personal fact was not supplied, no numeric result is asserted.

## A. The conversion is not the taxable event

- PRC IIT Law Art. 2 lists nine taxable income categories; exchanging one's own principal is not among them ([CN-IIT-LAW]({SOURCE_BY_ID['CN-IIT-LAW']['url']})).
- 26 USC §988(e) excludes a personal transaction from FX-gain recognition unless the gain exceeds USD 200 ([US-988]({SOURCE_BY_ID['US-988']['url']})).
- The IRS requires all amounts to be reported in USD at the prevailing rate ([US-FXCURRENCY]({SOURCE_BY_ID['US-FXCURRENCY']['url']})).
- Therefore the "considerable tax" is normally tax on the source income, a documentation condition, or a bank price. It is not a tax on converting principal.

## B. China-side legal structure

- PBOC Decree [2006] No.3 Art. 3: current-account individual FX follows convertibility; capital-account individual FX follows the convertibility process ([CN-MEAS-2006]({SOURCE_BY_ID['CN-MEAS-2006']['url']})).
- State Council Order 532 Art. 5 permits current-account FX payment/transfer with a real, lawful basis; Arts. 39/40/45 set ≤30% and 30%–100% fine bands for 逃汇, 骗购外汇 and illegal private FX trading ([CN-REG-532]({SOURCE_BY_ID['CN-REG-532']['url']})).
- SAFE Huifa [2020] No.14 Art. 54 sets a USD 50,000 annual convenience quota for 境内个人; Art. 56 allows documented non-quota current-account purchase; Art. 59 covers 境外个人 lawful China-source RMB income with tax vouchers; Art. 64 sets a USD 50,000/day remittance threshold; Art. 65 covers 境外个人 outward remittance of account FX with ID ([CN-GUIDE-2020]({SOURCE_BY_ID['CN-GUIDE-2020']['url']})).
- 2026 SAFE Tianjin Q&As confirm quota election, daily remittance threshold and Art. 59 tax-voucher requirement ([CN-FAQ-QUOTA-2026]({SOURCE_BY_ID['CN-FAQ-QUOTA-2026']['url']}); [CN-FAQ-REMIT-2026]({SOURCE_BY_ID['CN-FAQ-REMIT-2026']['url']}); [CN-FAQ-SALARY-2026]({SOURCE_BY_ID['CN-FAQ-SALARY-2026']['url']})).
- PBOC Announcement [2004] No.16 defines 移民转移 / 继承转移 and requires hukou cancellation, settlement proof, property title and tax certificate ([CN-PROP-2004]({SOURCE_BY_ID['CN-PROP-2004']['url']})). SAFE Huifa [2014] No.2 §VI(2) cancels the staged release and the >CNY 500,000 head-office filing ([CN-CAP-2014]({SOURCE_BY_ID['CN-CAP-2014']['url']})); the English translation is reference only ([CN-CAP-2014-EN]({SOURCE_BY_ID['CN-CAP-2014-EN']['url']})).
- Nationality Law Art. 9 as restated by NIA: acquiring a foreign nationality while settled abroad automatically loses Chinese nationality ([CN-NATIONALITY]({SOURCE_BY_ID['CN-NATIONALITY']['url']})).
- Overseas ATM withdrawals are capped at CNY 100,000/person/year and CNY 10,000/card/day; ordinary card consumption and the purchase quota are unaffected ([CN-ATM-2017]({SOURCE_BY_ID['CN-ATM-2017']['url']})).
- Outbound cash is limited to CNY 20,000 or USD 5,000 equivalent; larger amounts need a permit; the GACC service guide requires the red-channel declaration ([CN-CASH-CUSTOMS]({SOURCE_BY_ID['CN-CASH-CUSTOMS']['url']}); [CN-CUSTOMS-GUIDE]({SOURCE_BY_ID['CN-CUSTOMS-GUIDE']['url']})).
- PBOC Yinfa [2021] No.237 prohibits fiat/virtual-currency exchange and offshore exchange services to mainland residents ([CN-CRYPTO-2021]({SOURCE_BY_ID['CN-CRYPTO-2021']['url']})).

## C. China tax

- IIT Law Art. 3 sets a 20% flat rate for interest, dividends, asset transfers, leasing and incidental income ([CN-IIT-LAW]({SOURCE_BY_ID['CN-IIT-LAW']['url']})).
- Savings-deposit interest is temporarily exempt from PRC IIT from 2008-10-09 ([CN-INTEREST-2008]({SOURCE_BY_ID['CN-INTEREST-2008']['url']})).
- MOF/STA 2026 No.27 imposes 20% IIT on foreign-individual FIE dividends from 2026-09-01 and repeals the 1994 exemption ([CN-DIV-2026]({SOURCE_BY_ID['CN-DIV-2026']['url']})).
- STA/SAFE 2013 No.40 requires tax filing for a single external service-trade payment >USD 50,000, but exempts private 境内个人 study/travel/family visits; 2021 No.19 repealed specified articles and allows one-time electronic filing for repeated payments on one contract ([CN-TAXFILING-2013]({SOURCE_BY_ID['CN-TAXFILING-2013']['url']}); [CN-TAXFILING-2021]({SOURCE_BY_ID['CN-TAXFILING-2021']['url']})).
- The Shanghai government FAQ (source: BOC) gives the house-sale tax-voucher sequence and a Tax Filing Form above USD 50,000 ([CN-PROPERTY-FAQ]({SOURCE_BY_ID['CN-PROPERTY-FAQ']['url']})).

## D. Bank / provider prices

- BOC posted USD board on {M.PARAMS['boc_board_date']}: 现汇买入 666.38, 现汇卖出 669.19, 中行折算价 671.88 CNY per 100 USD; explicitly for reference only ([BOC-FX-BOARD]({SOURCE_BY_ID['BOC-FX-BOARD']['url']})).
- Current BOC personal tariff effective 2025-11-11, item 210105008: cross-border TT 0.1% (min CNY 50, max CNY 260) + CNY 150 international cable; overseas charges passed through at actual cost; full-amount credit USD 15/25; ATM 12 CNY + 1% capped 112 CNY ([BOC-TARIFF-PDF]({SOURCE_BY_ID['BOC-TARIFF-PDF']['url']}); [BOC-TARIFF]({SOURCE_BY_ID['BOC-TARIFF']['url']})).
- BOC notice effective 2026-11-11 changes Mastercard/Visa overseas ATM pricing to 2.5% (min USD 3, max USD 40); it is future-dated relative to {M.RETRIEVED} and is **not** applied as the current tariff ([BOC-ATM-2026]({SOURCE_BY_ID['BOC-ATM-2026']['url']})).
- HSBC China tariff effective 2026-10-31: Private Banking TT/cable free; Premier/Advance 0.1% (min CNY 100, max CNY 500) + CNY 120 cable; Pay Exact CNY 200. The PDF embeds an older 2024 table, flagged F16 ([HSBC-TARIFF]({SOURCE_BY_ID['HSBC-TARIFF']['url']})).
- Wise's own guide limits CNY sending to qualifying non-mainland-Chinese current/former workers with China tax records from the last three years, own-name source and own-name recipient, and a CNY 300,000 bank-app single-transfer cap ([WISE-GUIDE]({SOURCE_BY_ID['WISE-GUIDE']['url']})).
- Four exact public quotes were observed, at CNY 66,919 / 133,858 / 200,787 / 267,716 ([WISE-Q-66919]({SOURCE_BY_ID['WISE-Q-66919']['url']}); [WISE-Q-133858]({SOURCE_BY_ID['WISE-Q-133858']['url']}); [WISE-Q-200787]({SOURCE_BY_ID['WISE-Q-200787']['url']}); [WISE-Q-267716]({SOURCE_BY_ID['WISE-Q-267716']['url']})). No fee formula above CNY 300,000 is inferred.
- Chase's personal fee schedule charges USD 15 for an incoming international wire, provider-specific and conditional ([CHASE-FEES]({SOURCE_BY_ID['CHASE-FEES']['url']})).

## E. US tax and reporting

- US citizens report worldwide taxable income ([US-WORLDWIDE]({SOURCE_BY_ID['US-WORLDWIDE']['url']})); all amounts in USD at the prevailing rate ([US-FXCURRENCY]({SOURCE_BY_ID['US-FXCURRENCY']['url']})).
- FBAR is required when aggregate foreign accounts exceed USD 10,000 at any time in the calendar year; due April 15, automatic October 15; file with FinCEN, not with the return ([US-FBAR]({SOURCE_BY_ID['US-FBAR']['url']})).
- Form 8938 thresholds and failure penalty: unmarried US resident >USD 50,000 last day / >USD 75,000 any time; MFJ >USD 100,000 / >USD 150,000; failure up to USD 10,000 plus USD 10,000 per 30 days after notice, max USD 60,000 ([US-8938-FBAR]({SOURCE_BY_ID['US-8938-FBAR']['url']})).
- 31 USC §5321: non-willful FBAR statutory USD 10,000 with reasonable-cause exception; willful greater of USD 100,000 or 50% of the account balance at violation ([US-5321]({SOURCE_BY_ID['US-5321']['url']})).
- 31 CFR §1010.821 inflation-adjusted table for penalties assessed on/after 2025-01-17: non-willful USD 16,536, willful floor USD 165,353 ([US-1010-821]({SOURCE_BY_ID['US-1010-821']['url']})).
- Form 3520 Part IV applies to >USD 100,000 gifts/bequests from a nonresident alien or foreign estate; 2026 foreign-company/partnership threshold USD 20,573 ([US-3520-GIFTS]({SOURCE_BY_ID['US-3520-GIFTS']['url']}); [US-WORLDWIDE]({SOURCE_BY_ID['US-WORLDWIDE']['url']})).
- Streamlined filing compliance procedures require a non-willful certification ([US-STREAMLINED]({SOURCE_BY_ID['US-STREAMLINED']['url']})); Form 1116 may credit qualifying foreign income tax on the same income ([US-FTC]({SOURCE_BY_ID['US-FTC']['url']})).
- IR-2026-48 and the Working Families Tax Cuts page confirm the 1% excise tax from 2026-01-01 applies only to US-origin remittances funded with cash, money orders, cashier's checks or similar physical instruments; China-origin bank wires are outside it ([US-REMIT-TAX]({SOURCE_BY_ID['US-REMIT-TAX']['url']}); [US-OBBBA]({SOURCE_BY_ID['US-OBBBA']['url']})).
- CBP states there is no US limit on currency, but USD 10,000 or more requires FinCEN 105; nondeclaration risks seizure, Global Entry revocation and criminal prosecution ([US-CBP-CASH]({SOURCE_BY_ID['US-CBP-CASH']['url']})).

## F. Deliberately not asserted

No personal balance, source-of-funds breakdown, bank classification, acquisition basis, prior filing history, receiving-bank charge, live executable quote or local SAFE processing time was supplied. Those values are blank in the data and published on [Flagged for Review](../site/flagged.html).
"""
    with open(os.path.join(research, "primary-source-notes.md"), "w", encoding="utf-8") as f:
        f.write(notes)

    dead = [
        "# Known dead ends and official replacements — Edition I\n",
        f"Session `{M.SESSION}` · {M.RETRIEVED} UTC. These URLs were probed during research and are recorded so the inherited irregularities can be manually reviewed. Each row links to the exact replacement official source(s).\n",
        "| Probed URL | Result | Replacement / note | Official sources |\n|---|---|---|---|\n",
    ]
    for d in M.DEAD_ENDS:
        dead.append(f"| [{md_esc(d['url'])}]({d['url']}) | {md_esc(d['status'])} | {md_esc(d['note'])} | {md_sources(d['replacement'])} |\n")
    dead.append("\nNo third-party search result is cited as legal authority. The failed URLs are not used as evidence in Edition I tables.\n")
    with open(os.path.join(research, "known-dead-ends.md"), "w", encoding="utf-8") as f:
        f.write("".join(dead))

    ver = ["# Verification log — Edition I\n",
           f"Session `{M.SESSION}` · {M.RETRIEVED} UTC.\n",
           "The deterministic verifier is [`build/verify.py`](../build/verify.py). It recomputes the cost ladder from [`build/model.py`](../build/model.py) rather than trusting HTML, checks the official-source registry and allowlist, checks that every generated table row has a source link, checks blank-not-zero and flagged-item discipline, resolves internal links and anchors, proves byte-identical rebuilds, and performs local HTTP 200 checks.\n",
           "\n| Check | Status at build time | Evidence |\n|---|---|---|\n"]
    for name, status in VERIFICATION_RESULTS:
        ver.append(f"| {md_esc(name)} | {md_esc(status)} | [build/verify.py](../build/verify.py), [site/sources.html](../site/sources.html) |\n")
    ver.append("\nExternal links are the exact official URLs in [`research/retrieval-log.md`](retrieval-log.md); they were retrieved during research and are presented for manual review. Internal checkers prove deterministic generation and link resolution, not continuous external retrievability or factual correctness of a personal eligibility determination.\n")
    with open(os.path.join(research, "verification.md"), "w", encoding="utf-8") as f:
        f.write("".join(ver))

    index_notes = f"""# Edition I research notes

- [Primary-source retrieval log](retrieval-log.md) — {len(M.SOURCES)} exact official/provider URLs, verbatim excerpts and chunk coverage.
- [Primary-source legal and tax notes](primary-source-notes.md) — the China-side and US-side propositions used in the analysis.
- [Line-by-line repository audit](repo-audit.md) — deterministic snapshot of the inherited repository at `{M.REPO_BASE_COMMIT[:12]}`.
- [Known dead ends](known-dead-ends.md) — failed URLs and their official replacements.
- [Verification log](verification.md) — checks implemented and their status.

Raw full-page content is not saved; every cited URL and short verbatim excerpt is in the retrieval log and [`data/sources.json`](../data/sources.json). No value is inferred where an official source did not confirm it.
"""
    with open(os.path.join(research, "README.md"), "w", encoding="utf-8") as f:
        f.write(index_notes)


def write_redirect():
    """A clean edition-root landing page that links into the generated site."""
    cards = [
        ("Executive summary", "The answer first", "site/executive-summary.html"),
        ("Cost ladder", "40 USD steps", "site/costs.html"),
        ("All methods", "23 routes", "site/methods.html"),
        ("Penalty breakdown", "Every layer", "site/penalty.html"),
        ("Official sources", f"{len(M.SOURCES)} pages", "site/sources.html"),
        ("Flagged for review", f"{len(M.FLAGS)} items", "site/flagged.html"),
    ]
    card_html = "".join(
        f'<a class="card" href="{href}"><strong>{esc(title)}</strong><span>{esc(sub)}</span></a>'
        for title, sub, href in cards
    )
    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="0;url=site/index.html">
<title>China money · Edition I</title>
<link rel="stylesheet" href="site/assets/style.css">
<style>body{{background:#0d2733;color:#fff;display:grid;place-items:center;min-height:100vh;padding:20px}}
.panel{{max-width:760px;width:100%;background:#123747;border:1px solid #2b5d70;border-radius:16px;padding:28px}}
h1{{margin:0 0 6px}}p{{color:#cfe2e9}}.grid{{grid-template-columns:repeat(auto-fit,minmax(210px,1fr));margin-top:18px}}
.card{{display:block;background:#fff;color:#12212e;border-radius:10px;padding:14px;text-decoration:none}}
.card span{{display:block;color:#5d6d7b;font-size:13px;margin-top:3px}}</style></head>
<body><main class="panel"><h1>China money · Edition I</h1>
<p>Verified CNY → USD dossier. Opening the dashboard automatically… if it does not, use the link below.</p>
<p><a href="site/index.html" style="color:#7fe0cf;font-weight:700">Open the full dashboard →</a></p>
<div class="grid">{card_html}</div>
<p style="margin-top:18px;font-size:12px;color:#9fb6c1">Retrieved {M.RETRIEVED} UTC · session {M.SESSION} · blank cells are unverified · every table row is source-linked.</p>
</main></body></html>
"""
    with open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8") as f:
        f.write(doc)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def main():
    os.makedirs(SITE, exist_ok=True)
    os.makedirs(DATA, exist_ok=True)
    os.makedirs(SITE_DATA, exist_ok=True)
    os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)
    with open(os.path.join(SITE, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(CSS)
    with open(os.path.join(SITE, ".nojekyll"), "w", encoding="utf-8") as f:
        f.write("")

    def dump(path, obj):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=2, sort_keys=False)
            fh.write("\n")

    dump(os.path.join(DATA, "sources.json"), M.SOURCES)
    dump(os.path.join(DATA, "params.json"), P)
    dump(os.path.join(DATA, "quotes.json"), M.QUOTES)
    dump(os.path.join(DATA, "methods.json"), M.METHODS)
    dump(os.path.join(DATA, "flags.json"), M.FLAGS)
    dump(os.path.join(DATA, "repo_review.json"), M.REPO_REVIEW)
    dump(os.path.join(DATA, "requirements.json"), M.REQUIREMENTS)
    dump(os.path.join(DATA, "categories.json"), M.CATEGORIES)
    dump(os.path.join(DATA, "cost_ladder.json"), LADDER)
    dump(os.path.join(DATA, "exposure.json"), EXPOSURE)
    dump(os.path.join(DATA, "derived.json"), dict(
        sell_cny_per_usd=SELL, buy_cny_per_usd=BUY, midpoint_cny_per_usd=MID,
        half_spread_cny_per_usd=HALF_SPREAD_CNY, half_spread_pct=HALF_SPREAD_PCT,
        round_trip_spread_pct=ROUND_SPREAD_PCT,
    ))

    # CSV: one row per method per amount, blank cells for unverified values
    cols = list(LADDER["M01"][0].keys())
    csv_path = os.path.join(SITE_DATA, "cost-ladder.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for mid, rows in LADDER.items():
            for r in rows:
                d = dict(r)
                d["sources"] = " ".join(d["sources"])
                w.writerow({k: ("" if d.get(k) is None else d.get(k)) for k in cols})
    dump(os.path.join(SITE_DATA, "cost-ladder.json"), LADDER)

    index_page()
    executive_summary_page()
    costs_page()
    methods_page()
    penalty_page()
    tax_china_page()
    tax_us_page()
    sources_page()
    flagged_page()
    repo_review_page()
    requirements_page()
    methodology_page()
    for m in M.METHODS:
        method_page(m)
    for c in M.CATEGORIES:
        category_page(c)

    audit_data = audit.scan()
    audit.write(audit_data, DATA, os.path.join(ROOT, "research"))
    write_docs()
    write_research()
    write_redirect()

    print(f"Built {1 + len(M.METHODS) + len(M.CATEGORIES) + 11} site HTML pages plus edition-root landing, "
          f"{len(LADDER)} method grids × {len(M.AMOUNTS)} amounts "
          f"({sum(len(v) for v in LADDER.values())} ladder rows), "
          f"{len(EXPOSURE)} exposure rows, {len(M.SOURCES)} sources, "
          f"{audit_data['lines_scanned']:,} inherited lines audited.")


if __name__ == "__main__":
    main()
