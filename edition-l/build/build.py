#!/usr/bin/env python3
"""Build the Edition L dashboard: CNY to USD, costed at every USD 10,000 step.

Design rules enforced by verify.py:
  * every figure is recomputed from a published input with a source id;
  * a component that has no published value is emitted as blank + UNVERIFIED, never 0;
  * every data row carries at least one official HTTPS source link;
  * no JavaScript, no external assets, mobile-first stacked tables.

Run: python3 edition-l/build/build.py
"""
from __future__ import annotations

import csv
import json
from decimal import Decimal as D, ROUND_HALF_UP
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ED = ROOT / "edition-l"
DATA = ED / "data"
SITE = ED / "site"

SOURCES = {s["id"]: s for s in json.loads((DATA / "sources.json").read_text(encoding="utf-8"))["sources"]}
METHODS = json.loads((DATA / "methods.json").read_text(encoding="utf-8"))["methods"]
FLAGS = json.loads((DATA / "flags.json").read_text(encoding="utf-8"))["flags"]
AUDIT = json.loads((DATA / "audit.json").read_text(encoding="utf-8"))["findings"]
MODEL = json.loads((DATA / "model.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------- arithmetic
SELL = D(str(MODEL["derived"]["cny_per_usd_sell"]))      # CNY paid per USD bought
BUY = D(str(MODEL["derived"]["cny_per_usd_buy"]))        # CNY received per USD sold
MID = D(str(MODEL["derived"]["cny_per_usd_mid"]))
PARITY = D(str(MODEL["derived"]["cny_per_usd_parity"]))
HALF = (SELL - MID) / MID                                # one-way half-spread
ROUND_TRIP = (SELL - BUY) / MID
SELL_VS_PARITY = (SELL - PARITY) / PARITY

BOC = MODEL["boc"]
HSBC = MODEL["hsbc"]
RECV = D(str(MODEL["receiving_bank"]["incoming_international_wire_usd"]))
ATM = MODEL["atm"]
CARRY = MODEL["carry"]
QUOTA = D(str(MODEL["quota"]["usd_per_person_per_year"]))
TARGETS = list(range(MODEL["targets"]["start_usd"], MODEL["targets"]["end_usd"] + 1, MODEL["targets"]["step_usd"]))


def q(value, places="0.01") -> D:
    return D(value).quantize(D(places), rounding=ROUND_HALF_UP)


def usd(value) -> str:
    return f"${q(value):,.2f}"


def pct(value) -> str:
    return f"{q(D(value) * 100, '0.0001'):,.4f}%"


def cny(value) -> str:
    return f"CNY {q(value):,.2f}"


def clamp(value, low, high):
    return max(D(str(low)), min(D(str(high)), value))


def boc_commission(amount_usd: D) -> D:
    """0.1% of the CNY amount, floor CNY 50, cap CNY 260 (S11 item 210105008)."""
    return clamp(amount_usd * SELL * D(str(BOC["commission_rate"])),
                 BOC["commission_min_cny"], BOC["commission_max_cny"])


def hsbc_commission(amount_usd: D) -> D:
    return clamp(amount_usd * SELL * D(str(HSBC["commission_rate"])),
                 HSBC["commission_min_cny"], HSBC["commission_max_cny"])


def wire_row(target: int) -> dict:
    amount = D(target)
    commission = boc_commission(amount)
    cable = D(str(BOC["cable_international_cny"]))
    sender_cny = commission + cable
    fx = amount * HALF
    sender_usd = sender_cny / SELL
    total = fx + sender_usd + RECV
    return {
        "ladder": "L1",
        "target_usd": target,
        "cny_needed": q(amount * SELL),
        "fx_half_spread_usd": q(fx),
        "commission_cny": q(commission),
        "cable_cny": q(cable),
        "sender_usd": q(sender_usd),
        "receiving_usd": q(RECV),
        "known_total_usd": q(total),
        "pct_of_target": q(total / amount * 100, "0.0001"),
        "not_priced": "intermediary bank deduction; PRC tax (none identified); US tax on the currency leg",
        "sources": ["S11", "S12", "S14"],
    }


def split_row(target: int) -> dict:
    amount = D(target)
    n = int((amount / QUOTA).to_integral_value(rounding="ROUND_CEILING"))
    per = amount / n
    commission = boc_commission(per)
    cable = D(str(BOC["cable_international_cny"]))
    per_wire_sender_usd = (commission + cable) / SELL
    total = per_wire_sender_usd * n + amount * HALF + RECV * n
    return {
        "ladder": "L2",
        "target_usd": target,
        "wires": n,
        "per_wire_usd": q(per),
        "commission_cny_each": q(commission),
        "sender_usd_total": q(per_wire_sender_usd * n),
        "receiving_usd_total": q(RECV * n),
        "fx_half_spread_usd": q(amount * HALF),
        "known_total_usd": q(total),
        "pct_of_target": q(total / amount * 100, "0.0001"),
        "not_priced": "exchange-rate movement across the years; local practice on repeating an approved file",
        "sources": ["S11", "S12", "S14", "S03"],
    }


def hsbc_row(target: int) -> dict:
    amount = D(target)
    commission = hsbc_commission(amount)
    cable = D(str(HSBC["cable_cny"]))
    sender_usd = (commission + cable) / SELL
    total = sender_usd + RECV
    return {
        "ladder": "L3",
        "target_usd": target,
        "commission_cny": q(commission),
        "cable_cny": q(cable),
        "sender_usd": q(sender_usd),
        "receiving_usd": q(RECV),
        "fees_only_usd": q(total),
        "pct_of_target_fees_only": q(total / amount * 100, "0.0001"),
        "fx_usd": None,
        "not_priced": "HSBC's exchange rate is not published, so no all-in total exists for this rail",
        "sources": ["S13", "S14"],
    }


def atm_row(target: int) -> dict:
    amount = D(target)
    annual_cny = D(str(ATM["annual_cap_cny"]))
    cny_needed = amount * SELL
    years = int((cny_needed / annual_cny).to_integral_value(rounding="ROUND_CEILING"))
    # Best case: withdraw at the per-card daily cap so the capped fee is the whole charge.
    withdrawal_cny = D(str(ATM["daily_cap_per_card_cny"]))
    fee_one = min(D(str(ATM["per_withdrawal_cap_cny"])),
                  D(str(ATM["per_withdrawal_fixed_cny"])) + withdrawal_cny * D(str(ATM["per_withdrawal_rate"])))
    fee_rate = fee_one / withdrawal_cny
    total = amount * (HALF + fee_rate)
    return {
        "ladder": "L4",
        "target_usd": target,
        "years": years,
        "fee_rate_pct": q(fee_rate * 100, "0.0001"),
        "known_total_usd": q(total),
        "pct_of_target": q(total / amount * 100, "0.0001"),
        "not_priced": "foreign ATM operator surcharge; US cash deposit handling; rate movement across the years",
        "sources": ["S11", "S07", "S12"],
    }


def carry_row(target: int) -> dict:
    amount = D(target)
    trips = int((amount / D(str(CARRY["permit_required_up_to_usd"]))).to_integral_value(rounding="ROUND_CEILING"))
    permit_cny = D(str(CARRY["permit_fee_cny"]))  # waived to 2026-12-31 per S11
    total = amount * HALF + (permit_cny * trips) / SELL
    return {
        "ladder": "L5",
        "target_usd": target,
        "trips": trips,
        "permit_fee_cny": q(permit_cny),
        "permit_waived": True,
        "known_total_usd": q(total),
        "pct_of_target": q(total / amount * 100, "0.0001"),
        "not_priced": "travel, insurance and loss risk; US cash deposit handling; FinCEN Form 105 handling time",
        "sources": ["S08", "S11", "S12"],
    }


LADDERS = {
    "L1": [wire_row(t) for t in TARGETS],
    "L2": [split_row(t) for t in TARGETS],
    "L3": [hsbc_row(t) for t in TARGETS],
    "L4": [atm_row(t) for t in TARGETS],
    "L5": [carry_row(t) for t in TARGETS],
}

MILESTONES = [10_000, 50_000, 100_000, 200_000, 300_000, 400_000]

# ---------------------------------------------------------------- html helpers
NAV = [
    ("index.html", "Dashboard"),
    ("summary.html", "Executive summary"),
    ("costs.html", "Cost tables"),
    ("penalty.html", "Conversion penalty"),
    ("methods.html", "All methods"),
    ("steps.html", "Step by step"),
    ("tax.html", "Tax & penalties"),
    ("flagged.html", "Flagged for Review"),
    ("audit.html", "Repo audit"),
    ("sources.html", "Sources"),
    ("methodology.html", "Method & limits"),
]

CSS = """
:root{--navy:#0f2a43;--blue:#17679f;--teal:#0a7a5a;--ink:#16232e;--muted:#5b6b78;--bg:#f5f8fa;--line:#dbe3ea;--warn:#8a4b00;--warnbg:#fff5da;--bad:#8c1d18;--badbg:#fde9e7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
a{color:var(--blue);text-underline-offset:2px}a:focus-visible{outline:3px solid #b57600;outline-offset:2px}
header{background:var(--navy);color:#fff;padding:14px 14px 12px}header .brand{font-weight:800;font-size:1.05rem;color:#fff;text-decoration:none}
header .sub{display:block;color:#cfe3f2;font-size:.78rem;margin-top:2px}
nav{display:flex;gap:6px;overflow-x:auto;padding:8px 10px;background:#fff;border-bottom:1px solid var(--line);white-space:nowrap}
nav a{text-decoration:none;padding:6px 9px;border-radius:7px;font-size:.84rem;color:var(--navy)}
nav a[aria-current]{background:var(--navy);color:#fff}
main{max-width:1120px;margin:auto;padding:18px 12px 56px}
h1{font-size:clamp(1.5rem,5vw,2.2rem);line-height:1.15;margin:.2em 0 .5em}
h2{font-size:1.18rem;margin:1.9em 0 .4em}h3{font-size:1rem;margin:1.4em 0 .3em}
p,li{max-width:82ch}.lead{font-size:1.04rem}.muted,small{color:var(--muted)}small{display:block;font-size:.76rem}
.hero{background:linear-gradient(135deg,#0f2a43,#17679f);color:#fff;border-radius:14px;padding:22px 16px;margin-bottom:16px}
.hero p{color:#e8f2f9}.hero a{color:#fff}
.box{background:#fff;border:1px solid var(--line);border-radius:11px;padding:14px;margin:12px 0}
.note{border-left:5px solid #cf8500;background:var(--warnbg);border-radius:8px;padding:11px 13px;margin:12px 0}
.ok{border-left-color:var(--teal);background:#e9f7f1}.bad{border-left-color:var(--bad);background:var(--badbg)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:12px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:11px;padding:13px;text-decoration:none;color:inherit}
.card b{display:block;color:var(--teal);font-size:1.02rem;margin-bottom:3px}
.kpi{font-size:1.5rem;font-weight:800;color:var(--teal);line-height:1.1}
.tw{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:10px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:.85rem}
th,td{text-align:left;vertical-align:top;padding:9px;border-top:1px solid var(--line)}
th{background:#e9eff4;font-size:.7rem;text-transform:uppercase;letter-spacing:.04em;font-weight:800}
tbody tr:hover{background:#f8fbfd}.n{white-space:nowrap;font-variant-numeric:tabular-nums}
.src{display:inline-block;font-size:.72rem;margin:1px 6px 1px 0;white-space:nowrap}
.blank{display:inline-block;border-bottom:2px dotted var(--warn);width:2.6em;height:1em;margin-right:4px}
.tag{display:inline-block;font-size:.68rem;font-weight:800;border-radius:5px;padding:2px 6px;background:#e6eaee;color:#374a57}
.warn{background:var(--warnbg);color:var(--warn)}.stop{background:var(--badbg);color:var(--bad)}.live{background:#e2f5ec;color:var(--teal)}
.steps li{margin:.45em 0}
details{background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin:9px 0}
summary{cursor:pointer;font-weight:700}
footer{border-top:1px solid var(--line);padding:18px 12px;text-align:center;color:var(--muted);font-size:.8rem}
code{overflow-wrap:anywhere;background:#eef2f5;padding:1px 4px;border-radius:4px;font-size:.85em}
@media(max-width:720px){
 .stacked thead{position:absolute;left:-9999px}
 .stacked,.stacked tbody,.stacked tr,.stacked td{display:block;width:100%}
 .stacked tr{border-top:7px solid var(--line);padding:6px 0}.stacked tr:first-child{border-top:0}
 .stacked td{border:0;padding:5px 10px 5px 42%;position:relative;min-height:26px}
 .stacked td::before{content:attr(data-label);position:absolute;left:10px;top:5px;width:36%;font-size:.66rem;font-weight:800;text-transform:uppercase;color:var(--muted)}
 .stacked td:first-child{font-size:1rem;background:#f1f6f9}
 .tw{border:0;overflow:visible;background:transparent}.n{white-space:normal}
}
@media print{header,nav,footer{display:none}main{max-width:none}.tw{overflow:visible}}
"""


def shell(slug: str, title: str, desc: str, body: str) -> str:
    items = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == slug else ""
        items.append(f'<a href="{href}"{cur}>{e(label)}</a>')
    nav = "".join(items)
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta name="description" content="{e(desc)}">'
        f"<title>{e(title)} · China Money Edition L</title><style>{CSS}</style></head><body>"
        '<a class="skip" href="#main" style="position:absolute;left:-9999px">Skip to content</a>'
        '<header><a class="brand" href="index.html">China Money · Edition L</a>'
        '<span class="sub">CNY to USD, costed from published tariffs · every figure sourced or blank</span></header>'
        f'<nav aria-label="Site">{nav}</nav><main id="main">{body}</main>'
        '<footer>Blank means unverified, never zero. Partial totals are not quotes.<br>'
        'Educational research compiled from public official and first-party documents on 2026-11-10; '
        'not legal, tax, investment or immigration advice.</footer></body></html>'
    )


def table(headers, rows, stacked=True):
    head = "".join(f'<th scope="col">{e(h)}</th>' for h in headers)
    out = []
    for cells in rows:
        tds = "".join(
            f'<td data-label="{e(h)}">{c}</td>' for h, c in zip(headers, cells)
        )
        out.append(f"<tr>{tds}</tr>")
    cls = ' class="stacked"' if stacked else ""
    return (f'<div class="tw"><table{cls}><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(out)}</tbody></table></div>')


def src(ids) -> str:
    parts = []
    for i in ids:
        rec = SOURCES[i]
        parts.append(
            f'<a class="src" href="{e(rec["url"])}" rel="noopener noreferrer" '
            f'title="{e(rec["title"])} — {e(rec["locator"])}">{e(i)} ↗</a>'
        )
    return " ".join(parts)


def blank(label="No published value") -> str:
    return f'<span class="blank" aria-label="Blank, {e(label)}"></span><span class="tag warn">UNVERIFIED</span>'


def flag_link(fid: str) -> str:
    return f'<a href="flagged.html#{fid.lower()}">{e(fid)}</a>'


STATUS_TAG = {
    "lawful": '<span class="tag live">lawful</span>',
    "conditional": '<span class="tag warn">conditional</span>',
    "not-a-cashout": '<span class="tag">not a cash-out</span>',
    "prohibited": '<span class="tag stop">prohibited</span>',
}
RAIL_LABEL = {
    "L1": "BOC wire, full amount",
    "L2": "BOC wire, USD 50k chunks",
    "L3": "HSBC wire, fees only",
    "L4": "Card cash at foreign ATMs",
    "L5": "Cash purchase + carry",
    "L6": "Wise (no fixed fee)",
    "L7": "BOC draft (postage unknown)",
    "L8": "Capital-account approval",
    "L9": "Taxed-income route",
}

# ---------------------------------------------------------------- pages
def page_index():
    m = {r["target_usd"]: r for r in LADDERS["L1"]}
    rows = []
    for t in MILESTONES:
        r = m[t]
        rows.append([
            f'<strong>{usd(t)}</strong>',
            f'<span class="n">{cny(r["cny_needed"])}</span>',
            f'<span class="n">{usd(r["fx_half_spread_usd"])}</span>',
            f'<span class="n">CNY {r["commission_cny"]:,.2f}</span>',
            f'<span class="n">{usd(r["receiving_usd"])}</span>',
            f'<strong class="n">{usd(r["known_total_usd"])}</strong>',
            f'<span class="n">{r["pct_of_target"]:,.4f}%</span>',
            blank("Intermediary deduction"),
            src(r["sources"]),
        ])
    body = f"""
<div class="hero"><h1>Getting money out of China: what it actually costs</h1>
<p class="lead">A US citizen with CNY in a Chinese bank faces two different problems, and they are usually confused.
<strong>Tax is not the main one.</strong> The binding constraints are (1) proving the money is yours and lawful, and (2) the
payments rules that decide how much can be converted. The conversion itself costs a measured fraction of one percent.</p>
<p>Every number below is arithmetic on a published document that is linked on the same row. Nothing is estimated, inferred or filled in.
Where a cost has no published value, the cell is blank and marked <span class="tag warn">UNVERIFIED</span>.</p></div>

<div class="cards">
<a class="card" href="penalty.html"><span class="kpi">{pct(HALF)}</span><b>Conversion penalty</b>
One-way cost of the bank's own bid-ask bracket. It is a spread, not a tax. Measured from BOC's board of 2026-11-10 17:39:58 and the same board's bid.</a>
<a class="card" href="costs.html"><span class="kpi">{usd(m[10000]["known_total_usd"])}</span><b>Known cost at USD 10,000</b>
{usd(m[10000]["known_total_usd"])} of {usd(10000)} is {m[10000]["pct_of_target"]:,.2f}% - dominated by fixed cable and receiving charges.</a>
<a class="card" href="costs.html"><span class="kpi">{usd(m[400000]["known_total_usd"])}</span><b>Known cost at USD 400,000</b>
{m[400000]["pct_of_target"]:,.2f}% - the commission caps at CNY 260, so size makes it cheap per dollar.</a>
<a class="card" href="tax.html"><span class="kpi">USD 16,536</span><b>The largest penalty in the file</b>
Maximum non-willful FBAR penalty per report, inflation-adjusted (31 CFR 1010.821). Larger than any conversion fee at any size in this model.</a>
</div>

<h2 id="answer">The answer in five lines</h2>
<ol class="steps">
<li><strong>Establish the route before optimising the price.</strong> A US passport holder is an <em>overseas individual</em> (S02 Art. 37(2)),
whose purchase rule is documentary - lawful current-account RMB income plus tax vouchers (S02 Art. 13; S04). The USD 50,000 annual total is written for
settlement by anyone plus <em>purchase by a domestic individual</em> (S03 Art. 2). That distinction decides whether USD 400,000 is a one-time file or eight years of wires.</li>
<li><strong>Price the wire, not the rumour.</strong> BOC charges 0.1% of the CNY amount, floored at CNY 50, capped at CNY 260, plus CNY 150 cable (S11).
Bank of America charges USD 15 to receive it (S14). Those three numbers plus the spread are the whole published cost.</li>
<li><strong>The conversion penalty is about a fifth of one percent.</strong> BOC's own board on 2026-11-10 showed it would buy USD at 665.71 and sell at 668.51 per USD 100;
half of that CNY 2.80 bracket is {pct(HALF)} of the amount. That is the entire "conversion" cost at the counter - the tariff charges no separate conversion commission (S11 item 210107011).</li>
<li><strong>Do not confuse the daily fixing with a mid-market rate.</strong> The CFETS parity for the same day was 6.7167 while BOC sold at 6.6851,
so the bank's offer was <em>below</em> the fixing. Computing a "penalty against parity" produces nonsense; measured against the bank's own bracket it does not.
See <a href="flagged.html#f20">F20</a>.</li>
<li><strong>The real penalties are elsewhere.</strong> PRC administrative fines reach 30% of the amount for evasion or disguised FX dealing (S01 Arts. 39, 45);
a property sale is taxed at 20% of the gain (S10 Art. 3(3)); and US reporting failures run to USD 16,536 non-willful or USD 165,353 willful per FBAR (S19).
None of those is a conversion tax, and all of them are avoidable by paperwork.</li>
</ol>

<h2 id="glance">Known cost at the milestones (route that can move the full amount now)</h2>
<p>BOC outward telegraphic transfer of the full amount to a US account, with the published spread, commission, cable and receiving fee.
The last column is what remains unpriced on every row - it is blank because no source publishes it, not because it is zero.</p>
{table(["USD target", "CNY at the board", "FX half-spread", "BOC commission", "US receiving", "Known total", "% of target", "Still unpriced", "Sources"], rows)}
<p><a class="button" href="costs.html">Open all 40 steps, five routes and the quota-split comparison →</a></p>

<div class="note"><strong>Read this before using any number.</strong> A known total is not a quote. It excludes the intermediary bank's deduction,
any tax on the underlying money, the exchange rate you will actually be given, and any documentation cost. BOC itself says the board is indicative and the
executed rate governs (S12).</div>

<h2>Where to go next</h2>
<div class="cards">
<a class="card" href="summary.html"><b>Executive summary</b>The decision order, the two tax systems, and the five-step playbook.</a>
<a class="card" href="penalty.html"><b>Conversion penalty, decomposed</b>Spread, fixed charges and policy cost, separated and measured.</a>
<a class="card" href="methods.html"><b>All 21 methods</b>Status, eligibility, steps, pros, cons and tax treatment for each.</a>
<a class="card" href="costs.html"><b>Cost tables, 40 steps</b>USD 10,000 to 400,000, five routes, plus what splitting costs.</a>
<a class="card" href="tax.html"><b>Tax and penalties</b>China's nine categories, section 988, FBAR/8938/3520, and the fine bands.</a>
<a class="card" href="flagged.html"><b>Flagged for Review</b>{len(FLAGS)} unresolved items, each with what is missing and why it matters.</a>
<a class="card" href="audit.html"><b>Repository audit</b>{len(AUDIT)} findings against the prior editions in this repository.</a>
<a class="card" href="sources.html"><b>Sources</b>{len(SOURCES)} documents, with the exact article or page inspected.</a>
</div>
"""
    return shell("index.html", "Dashboard", "Source-linked CNY to USD cost dashboard: 21 methods, five priced routes, 40 target sizes, and an explicit conversion-penalty decomposition.", body)


def page_summary():
    m1 = {r["target_usd"]: r for r in LADDERS["L1"]}
    m2 = {r["target_usd"]: r for r in LADDERS["L2"]}
    sys_rows = [
        ["Does China tax the conversion of CNY into USD?",
         "No PRC income-tax category covers a currency conversion. The nine categories are listed in S10 Art. 2 and none is a foreign-exchange transaction. The underlying income must already have been taxed; that is a documentary condition, not a second tax.",
         "Conversion is not taxable as income; the tax file is an evidence file.", src(["S10", "S02", "S04"])],
        ["Does China tax the money's source?",
         "Yes, if the source is taxable: salary 3%-45% progressive (Art. 3(1)); property transfer 20% of proceeds minus original value and reasonable expenses (Arts. 3(3), 6(5)); dividends and interest 20% (Art. 3(3)).",
         "The 20% property-transfer rate is the largest single number in this project and it is a tax on the asset, not on the transfer.",
         src(["S10"])],
        ["What if the paperwork is wrong?",
         "Administrative fines: evasion up to 30% of the amount, or 30% to 100% in serious cases (S01 Art. 39); illegal arbitrage up to 30% (Art. 40); illegal cash carrying up to 20% (Art. 42); private or disguised FX dealing up to 30% with confiscation (Art. 45); individuals up to CNY 50,000 for reporting and document failures (Art. 48).",
         "These are avoidable by using a documented route. They are not a cost of a lawful transfer.",
         src(["S01"])],
        ["Does the US tax the principal?",
         "No. Moving your own already-taxed principal is not income. Income character follows the original source, and the currency leg is a section 988 item.",
         "Confirm the original source was reported; that is a facts question for a preparer.",
         src(["S15"])],
        ["What about the currency gain?",
         "A personal transaction recognises no section 988 gain unless the gain would exceed USD 200, and the exclusion does not apply to a transaction whose allocable expenses meet section 162 or 212.",
         "The USD 200 figure is an exclusion threshold, not an allowance, and CNY weakened over the period reviewed - for a USD-basis holder that usually points to a loss, not a gain.",
         src(["S15"])],
        ["What are the real US penalties?",
         "FBAR: file FinCEN 114 when foreign accounts exceed USD 10,000 in aggregate at any time. Adjusted maximums: USD 16,536 non-willful, USD 165,353 willful per report (31 CFR 1010.821). Form 8938 has its own thresholds and a penalty up to USD 10,000 plus USD 10,000 per 30 days to a USD 60,000 maximum. Form 3520 for foreign gifts above USD 100,000, with penalties under IRC 6039F(c).",
         "Reporting failures dwarf every transfer fee in this model.",
         src(["S16", "S17", "S19", "S18"])],
    ]
    order = [
        "<strong>Classify the balance, not the currency.</strong> Ask the bank, in writing, whether it treats you as an overseas individual and which current-account item the money is. Everything downstream depends on the answer (" + flag_link("F01") + ", " + flag_link("F02") + ").",
        "<strong>Assemble the evidence before asking for a quote.</strong> Contract or other transactional proof, plus the China tax record or withholding voucher (S02 Art. 13; S04). A quote you cannot fund is not information.",
        "<strong>Get executable quotes on the same day for the same amount</strong> from BOC, your current bank, and any provider you are eligible for. Compare amount received, not headline rate (S12 disclaimer).",
        "<strong>Choose cost allocation deliberately.</strong> SHA leaves correspondent deductions in the amount received; OUR moves them to you at a known published price at BOC (USD 15 or 25) and an undisclosed pre-collection at HSBC (CNY 200) (" + flag_link("F18") + ").",
        "<strong>Do the reporting in the same year.</strong> FBAR by 15 April with an automatic extension to 15 October (S16); Form 8938 with the return; Form 3520 for a large foreign gift (S18).",
        "<strong>Only then consider a capital-account route.</strong> Emigrant transfer, inheritance, or a property sale are entitlements with their own tests (S05, S06, S02 Art. 22), not faster wires.",
    ]
    body = f"""
<h1>Executive summary</h1>
<p class="lead">The question was "what is the least-tax way to get CNY out of China". The honest answer is that
<strong>there is no conversion tax to optimise</strong>. There is a measured spread, a short list of published bank charges, a payments-policy gate,
and a set of reporting duties whose penalties are far larger than the transfer cost.</p>

<div class="box ok"><strong>Bottom line for a US citizen with a CNY balance.</strong>
The cheapest published route is a documented purchase and single outward wire: about {usd(m1[10000]["known_total_usd"])} on {usd(10000)} ({m1[10000]["pct_of_target"]:,.2f}%) falling to
{usd(m1[400000]["known_total_usd"])} on {usd(400000)} ({m1[400000]["pct_of_target"]:,.2f}%) because the commission caps at CNY 260.
Whether that route can carry the <em>whole</em> balance is a documentation question (S02 Art. 13; S04), not a tax question. If the bank instead applies the
domestic-individual annual total, the same USD 400,000 needs {m2[400000]["wires"]} wires and costs {usd(m2[400000]["known_total_usd"])}.</div>

<h2>The two tax systems, side by side</h2>
{table(["Question", "What the official text says", "What it means here", "Sources"], sys_rows)}

<h2>Decision order</h2>
<ol class="steps">{"".join(f"<li>{x}</li>" for x in order)}</ol>

<h2>What would change this answer</h2>
<ul>
<li><strong>The source of the balance.</strong> Salary, a property sale, an inheritance, a dividend and a gift each have a different route and a different tax result. No personal fact was supplied, so no determination is made ({flag_link("F22")}).</li>
<li><strong>The bank's classification of you.</strong> Overseas individual versus domestic individual changes the applicable purchase rule and the amount of paperwork ({flag_link("F01")}).</li>
<li><strong>The day.</strong> The BOC selling rate for USD moved from 669.19 to 668.51 per USD 100 on 2026-11-10 across the snapshots recorded in this repository. On USD 400,000 that is about USD 400 of movement - more than the entire fixed-fee component ({flag_link("F19")}).</li>
<li><strong>Whether the balance was ever reported in the US.</strong> If the Chinese account was unreported, the dominant cost is not the transfer at all but the FBAR and Form 8938 exposure (S16, S17, S19).</li>
<li><strong>Whether you have genuinely emigrated and cancelled PRC household registration.</strong> That is the gate for the large capital-account route (S05 Art. 8; {flag_link("F10")}).</li>
</ul>

<div class="note"><strong>What this edition does not do.</strong> It does not decide your eligibility, does not quote a live rate, does not compute a tax on an unknown gain,
and does not certify that a branch will accept a file. It prices what is published and marks the rest blank.</div>

<h2>The five-minute version of the cost tables</h2>
{table(["USD target", "Single wire: known total", "% of target", "Quota-split: wires", "Quota-split: known total", "Extra cost of splitting", "Sources"],
       [[f'<strong>{usd(t)}</strong>', f'<span class="n">{usd(m1[t]["known_total_usd"])}</span>', f'{m1[t]["pct_of_target"]:,.4f}%',
         f'<span class="n">{m2[t]["wires"]}</span>', f'<span class="n">{usd(m2[t]["known_total_usd"])}</span>',
         f'<span class="n">{usd(m2[t]["known_total_usd"] - m1[t]["known_total_usd"])}</span>', src(["S11", "S12", "S14", "S03"])] for t in MILESTONES])}
<p><small>For targets at or below USD 50,000 the "quota-split" column is one wire, so the extra cost is zero by construction - not an unpriced cell.
See <a href="costs.html">the 40-step tables</a> for the row-by-row citation.</small></p>
"""
    return shell("summary.html", "Executive summary", "The least-tax route to move CNY to USD, the two tax systems compared, and the decision order.", body)


def page_costs():
    t1 = []
    for r in LADDERS["L1"]:
        t1.append([
            f'<strong>{usd(r["target_usd"])}</strong>',
            f'<span class="n">{cny(r["cny_needed"])}</span>',
            f'<span class="n">{usd(r["fx_half_spread_usd"])}</span>',
            f'<span class="n">{cny(r["commission_cny"])}</span>',
            f'<span class="n">{cny(r["cable_cny"])}</span>',
            f'<span class="n">{usd(r["receiving_usd"])}</span>',
            f'<strong class="n">{usd(r["known_total_usd"])}</strong>',
            f'<span class="n">{r["pct_of_target"]:,.4f}%</span>',
            f'<span class="n">{usd(r["known_total_usd"] * -1 + r["known_total_usd"] * 2 - r["known_total_usd"])}</span>'.replace("$0.00", "") + blank("Intermediary, tax, documents"),
            src(r["sources"]),
        ])
    # simplify the unpriced column to avoid a synthetic zero
    for row in t1:
        row[8] = blank("Intermediary, tax, documents")

    t2 = []
    for a, b in zip(LADDERS["L1"], LADDERS["L2"]):
        extra = b["known_total_usd"] - a["known_total_usd"]
        t2.append([
            f'<strong>{usd(a["target_usd"])}</strong>',
            f'<span class="n">{b["wires"]}</span>',
            f'<span class="n">{usd(b["per_wire_usd"])}</span>',
            f'<span class="n">{usd(a["known_total_usd"])}</span>',
            f'<span class="n">{usd(b["known_total_usd"])}</span>',
            f'<span class="n">{usd(extra)}</span>',
            f'<span class="n">{q(extra / D(a["target_usd"]) * 100, "0.0001"):,.4f}%</span>',
            src(["S11", "S12", "S14", "S03"]),
        ])

    t3 = []
    for r in LADDERS["L3"]:
        t3.append([
            f'<strong>{usd(r["target_usd"])}</strong>',
            f'<span class="n">{cny(r["commission_cny"])}</span>',
            f'<span class="n">{cny(r["cable_cny"])}</span>',
            f'<span class="n">{usd(r["sender_usd"])}</span>',
            f'<span class="n">{usd(r["receiving_usd"])}</span>',
            f'<strong class="n">{usd(r["fees_only_usd"])}</strong>',
            f'{r["pct_of_target_fees_only"]:,.4f}%',
            blank("HSBC exchange rate is not published"),
            src(r["sources"]),
        ])

    t4 = []
    for a, b in zip(LADDERS["L4"], LADDERS["L5"]):
        t4.append([
            f'<strong>{usd(a["target_usd"])}</strong>',
            f'<span class="n">{a["years"]}</span>',
            f'<span class="n">{a["fee_rate_pct"]:,.4f}%</span>',
            f'<span class="n">{usd(a["known_total_usd"])}</span>',
            f'<span class="n">{b["trips"]}</span>',
            f'<span class="n">{usd(b["known_total_usd"])}</span>',
            src(["S11", "S07", "S08", "S12"]),
        ])

    coverage = []
    for m in METHODS:
        rail = m["rail"]
        if rail in ("L1", "L2", "L3", "L4", "L5"):
            priced = {"L1": "Yes - all 40 steps", "L2": "Yes - all 40 steps",
                      "L3": "Fees only - FX blank", "L4": "Indicative - capped per year",
                      "L5": "Yes - but max USD 10,000 per trip"}[rail]
            why = {"L1": "Every component is published.",
                   "L2": "Same components, repeated.",
                   "L3": "HSBC publishes the fee but not the rate.",
                   "L4": "Fee is capped per withdrawal; the operator surcharge is not published.",
                   "L5": "Spread and permit fee are published; travel and risk are not."}[rail]
        elif rail == "L6":
            priced, why = "No", "Wise publishes no fixed fee; the price appears only at transfer setup (S21)."
        elif rail == "L7":
            priced, why = "Partly", "Commission is published; postage is at actual cost and the US collection fee is not published."
        elif rail in ("L8", "L9"):
            priced, why = "No per-transfer price", "Approval routes publish documents and tax rules, not a fee schedule; the tax depends on an unknown gain."
        else:
            priced, why = "Not applicable", "The route cannot move an existing balance, or is prohibited."
        coverage.append([f'<strong>{m["id"]}</strong>', e(m["name"]), e(RAIL_LABEL.get(rail, "-")) if rail else "-", e(priced), e(why), src(m["sources"])])

    body = f"""
<h1>Cost tables: USD 10,000 to USD 400,000</h1>
<p class="lead">Four ladders and one coverage table. The first is the route that can move the whole amount now. The second shows what the annual-total rule
costs you if the bank applies it. The third is HSBC, which publishes a fee but not a rate. The fourth shows the two routes that are cheap per dollar but cannot
carry a large balance in one year.</p>

<div class="box ok"><strong>Model inputs, all published.</strong>
BOC board 2026-11-10 17:39:58: buy CNY 665.71, sell CNY 668.51 per USD 100, reference CNY 671.67 (S12).
BOC tariff: 0.1%, floor CNY 50, cap CNY 260, cable CNY 150 (S11). HSBC China: 0.1%, floor CNY 100, cap CNY 500, cable CNY 120 (S13).
Bank of America incoming international wire: USD 15 (S14). Annual total if it applies: USD 50,000 per person per year (S03).
Half-spread used everywhere: {pct(HALF)} = (6.6851 - 6.6711) / 6.6711.</div>

<h2 id="L1">L1 - BOC outward telegraphic transfer, full amount, SHA</h2>
<p>Commission on the CNY-equivalent at the board's selling rate, plus the international cable charge, plus the US receiving fee, plus the measured half-spread.
This is the lowest published cost for a single transfer at every size above USD 10,000 that this model covers.</p>
{table(["USD target", "CNY needed at board", "FX half-spread", "BOC commission", "Cable", "US receiving", "Known total", "% of target", "Still unpriced", "Sources"], t1)}
<p><small>The "still unpriced" cell is a link to {flag_link("F18")} for every row: no source publishes the intermediary deduction, and BOC collects overseas charges at actual cost (S11 note 4).</small></p>

<h2 id="L2">L2 - the same wires split across annual totals</h2>
<p>If the bank applies the USD 50,000 annual total (S03 Art. 2, purchase limb for a domestic individual), the target must be split into
ceil(target / 50,000) wires. Fixed charges - the CNY 150 cable and the USD 15 receiving fee - are paid again on every wire. The spread does not change.</p>
{table(["USD target", "Wires needed", "Per wire", "L1 single-wire total", "L2 split total", "Extra cost of splitting", "Extra as % of target", "Sources"], t2)}
<p><small>Up to USD 50,000 one wire is enough, so the extra is zero by construction. Above that the extra is the repeat of the CNY 150 cable and the USD 15 receiving fee on each additional wire.</small></p>

<h2 id="L3">L3 - HSBC China, Premier/Advance, fees only</h2>
<p>HSBC's published commission and cable charge are higher than BOC's at every size in this table, and its exchange rate is not published, so no all-in figure exists.
Do not read this ladder as a ranking: it is missing the largest component.</p>
{table(["USD target", "HSBC commission", "Cable", "Fees in USD", "US receiving", "Fees-only total", "% of target (fees only)", "FX cost", "Sources"], t3)}

<h2 id="L4">L4 and L5 - cheap per dollar, useless at scale</h2>
<p>Card cash at foreign ATMs costs CNY 12 plus 1% per withdrawal, capped at CNY 112, so the best possible rate is about
{q(D(str(ATM["per_withdrawal_cap_cny"])) / D(str(ATM["daily_cap_per_card_cny"])) * 100, "0.0001"):,.4f}% of what you move - five times the wire's commission rate and
applied to the whole amount. It is also capped at CNY 100,000 per person per calendar year (S07), so USD 400,000 takes {LADDERS["L4"][-1]["years"]} years.
Carrying cash is cheaper still per dollar (spread only, and the CNY 10 permit fee is waived until 2026-12-31) but limited to USD 10,000 per trip (S08), so USD 400,000 means
{LADDERS["L5"][-1]["trips"]} trips.</p>
{table(["USD target", "ATM: years required", "ATM: fee rate per amount moved", "ATM: known total", "Cash: trips required", "Cash: known total", "Sources"], t4)}
<p><small>ATM totals apply the fee rate to the whole amount and ignore exchange-rate movement across the years, which will dominate; they are shown to make the
rate comparison visible, not to suggest the route. Cash totals exclude travel, insurance and loss risk.</small></p>

<h2 id="coverage">Every method: is it priced at each USD 10,000 step?</h2>
<p>Twenty-one candidates, five priced ladders, and the reason for every gap. A blank is a statement about the documents, not about the route's value.</p>
{table(["ID", "Method", "Priced rail", "Priced at all 40 steps?", "Why not", "Sources"], coverage)}

<h2 id="download">Machine-readable data</h2>
<p>Every row above is in <a href="../data/costs.csv">costs.csv</a> and <a href="../data/costs.json">costs.json</a> (both generated by the same script that renders these pages,
so they cannot drift from the tables).</p>
"""
    return shell("costs.html", "Cost tables", "Five cost ladders from USD 10,000 to USD 400,000 with every component sourced, plus a coverage table for all 21 methods.", body)
def page_penalty():
    m1 = {r["target_usd"]: r for r in LADDERS["L1"]}
    spread_rows = [
        ["BOC buys USD from you at (spot buying)", "CNY 665.71 per USD 100", "The rate you would get selling dollars to the bank.", src(["S12"])],
        ["BOC sells USD to you at (spot selling)", "CNY 668.51 per USD 100", "The rate you pay to buy dollars - the one that matters for CNY to USD.", src(["S12"])],
        ["Midpoint of the bank's own bracket", f"CNY {q(MID * 100, '0.0001')} per USD 100", "Arithmetic midpoint of the two published rates: (665.71 + 668.51) / 2.", src(["S12"])],
        ["Round-trip spread", pct(ROUND_TRIP), f"(668.51 - 665.71) / 667.11. What you lose if you convert and convert straight back.", src(["S12"])],
        ["One-way spread (the conversion penalty)", f"<strong>{pct(HALF)}</strong>", "(668.51 - 667.11) / 667.11. The half of the bracket you cross when you buy dollars. Used in every ladder.", src(["S12"])],
        ["Separate conversion commission at the counter", "CNY 0", "BOC's tariff states that conversion at its own branches carries no separate fee: the exchange rate is the price.", src(["S11"])],
        ["CFETS/SAFE central parity, same day", "CNY 671.67 per USD 100", "The daily fixing. It is not a tradable rate and must not be used as a mid-market benchmark.", src(["S20"])],
        ["Selling rate versus parity", pct(SELL_VS_PARITY), "Negative: on this day BOC's offer was below the fixing, so a 'penalty against parity' would be negative. See " + flag_link("F20") + ".", src(["S12", "S20"])],
    ]
    dec = []
    for t in MILESTONES:
        r = m1[t]
        fixed = r["known_total_usd"] - r["fx_half_spread_usd"]
        dec.append([
            f'<strong>{usd(t)}</strong>',
            f'<span class="n">{usd(r["fx_half_spread_usd"])}</span>',
            f'<span class="n">{q(r["fx_half_spread_usd"] / D(t) * 100, "0.0001"):,.4f}%</span>',
            f'<span class="n">{usd(fixed)}</span>',
            f'<span class="n">{q(fixed / D(t) * 100, "0.0001"):,.4f}%</span>',
            f'<strong class="n">{usd(r["known_total_usd"])}</strong>',
            f'<span class="n">{r["pct_of_target"]:,.4f}%</span>',
            src(["S11", "S12", "S14"]),
        ])
    sens = []
    for t in MILESTONES:
        drift = D(t) * D(str(MODEL["sensitivity_pct_points"])) / 100
        sens.append([
            f'<strong>{usd(t)}</strong>',
            f'<span class="n">{usd(drift)}</span>',
            f'<span class="n">{usd(m1[t]["known_total_usd"])}</span>',
            f'<span class="n">{q(drift / m1[t]["known_total_usd"], "0.1")}x</span>',
            src(["S12"]),
        ])
    yrs = []
    for t in MILESTONES:
        n = int((D(t) / QUOTA).to_integral_value(rounding="ROUND_CEILING"))
        yrs.append([
            f'<strong>{usd(t)}</strong>',
            f'<span class="n">{n}</span>',
            f'<span class="n">{usd(LADDERS["L2"][t // 10000 - 1]["known_total_usd"])}</span>',
            f'<span class="n">{usd(m1[t]["known_total_usd"])}</span>',
            f'<span class="n">{usd(LADDERS["L2"][t // 10000 - 1]["known_total_usd"] - m1[t]["known_total_usd"])}</span>',
            f'<span class="n">{usd(D(t) * D("0.01"))}</span>',
            src(["S03", "S11", "S12", "S14"]),
        ])
    body = f"""
<h1>The conversion penalty, decomposed</h1>
<p class="lead">"Penalty" is used for at least four different things in this problem. Only one of them is a cost you pay at the counter, and
it is measurable to four decimal places. Separating them is what makes the rest of the decision tractable.</p>

<div class="cards">
<div class="card"><span class="kpi">{pct(HALF)}</span><b>1. Spread (measured)</b>The half of the bank's bid-ask bracket you cross. This is the conversion cost.</div>
<div class="card"><span class="kpi">CNY 410</span><b>2. Fixed charges (published)</b>CNY 260 commission + CNY 150 cable at the cap, plus USD 15 at the US bank.</div>
<div class="card"><span class="kpi">8 years</span><b>3. Policy cost (if the quota applies)</b>USD 50,000 a year turns one transfer into eight, each with its own fixed charges and rate risk.</div>
<div class="card"><span class="kpi">0%</span><b>4. Conversion tax (none)</b>No PRC income-tax category covers a currency conversion (S10 Art. 2).</div>
</div>

<h2 id="measured">1. What the bank's own board actually proves</h2>
<p>BOC publishes both sides of its bracket. Crossing half of it is the entire conversion cost at the counter, because the tariff adds no separate
conversion commission (S11 item 210107011). Both facts are on the same page as the rate, so this is arithmetic on a single official source.</p>
{table(["Component", "Value", "How it is derived", "Sources"], spread_rows)}

<div class="note"><strong>The trap.</strong> On 2026-11-10 the official central parity was CNY 6.7167 per USD while BOC sold dollars at 6.6851.
Anyone computing "penalty versus mid-market" from the parity would report a <em>negative</em> penalty of {pct(SELL_VS_PARITY)}.
The fixing is set once each morning and is not a rate a customer can obtain. This edition therefore never uses it as a benchmark.</div>

<h2 id="split">2. Spread versus fixed charges at every milestone</h2>
<p>The spread grows with the amount; the fixed charges do not. That is why the percentage cost falls sharply with size and why batching one wire beats several small ones.</p>
{table(["USD target", "FX half-spread cost", "as % of target", "Fixed charges", "as % of target", "Known total", "Known total as %", "Sources"], dec)}
<p><small>Fixed charges here are the BOC commission, the CNY 150 cable and the USD 15 receiving fee. At USD 10,000 they are
{q((m1[10000]["known_total_usd"] - m1[10000]["fx_half_spread_usd"]) / m1[10000]["known_total_usd"] * 100, "0.1")}% of the known total; at USD 400,000 they are
{q((m1[400000]["known_total_usd"] - m1[400000]["fx_half_spread_usd"]) / m1[400000]["known_total_usd"] * 100, "0.1")}%.</small></p>

<h2 id="policy">3. The policy cost is a time cost, and time is priced</h2>
<p>If the annual total applies, the target needs several wires. The extra fee is knowable. The extra <em>rate</em> exposure is not a forecast but it is not small either:
a one percentage point move in USD/CNY on USD 400,000 is USD 4,000 - several times the entire known fee.</p>
{table(["USD target", "Wires at USD 50k/yr", "Split known total", "Single-wire known total", "Extra fees from splitting", "Cost of a 1% rate move", "Sources"], yrs)}
<p><small>The last column is arithmetic sensitivity on the transfer amount, not a prediction. It shows why "wait for a better rate" is the dominant risk in a multi-year plan.</small></p>

<h2 id="sens">4. Fee versus rate sensitivity</h2>
{table(["USD target", "Cost of a 1.00% move in USD/CNY", "Known transfer total", "Rate move / fees", "Sources"], sens)}

<h2 id="nottax">5. What is not a conversion penalty</h2>
<ul>
<li><strong>PRC income tax.</strong> Not one of the nine categories in S10 Art. 2 is a currency conversion. The tax you may owe is on the money's source, and it is owed whether or not you convert.</li>
<li><strong>US income tax on principal.</strong> Moving your own taxed money is not income. The currency leg is section 988, with the USD 200 personal-transaction rule (S15 (e)).</li>
<li><strong>The CFETS parity gap.</strong> Not obtainable, so not a cost. See {flag_link("F20")}.</li>
<li><strong>A "remittance tax".</strong> The 1% US remittance-transfer excise tax discussed in prior editions applies to specified remittances <em>sent from</em> the United States, not to money arriving from China. It is not re-verified in this session and is not included in any figure here.</li>
</ul>

<div class="box bad"><strong>The penalties that are real.</strong> PRC administrative fines reach 30% of the amount for evasion or disguised dealing (S01 Arts. 39, 45);
US FBAR maximums are USD 16,536 non-willful and USD 165,353 willful per report (S19); a property gain is taxed at 20% (S10 Art. 3(3)).
Compared with these, a {pct(HALF)} spread is noise - which is exactly why the paperwork, not the rate, is the thing to optimise.</div>
"""
    return shell("penalty.html", "Conversion penalty", "The conversion penalty decomposed into measured spread, published fixed charges, policy cost and tax, with the parity trap explained.", body)


def page_methods():
    rows = []
    for m in METHODS:
        rail = m["rail"]
        rows.append([
            f'<strong>{m["id"]}</strong>',
            f'<a href="#{m["id"].lower()}">{e(m["name"])}</a>',
            STATUS_TAG[m["status"]],
            e(RAIL_LABEL.get(rail, "no priced rail")),
            e(m["eligibility"]),
            src(m["sources"]),
        ])
    details = []
    for m in METHODS:
        steps = "".join(f"<li>{e(s)}</li>" for s in m["steps"])
        pros = "".join(f"<li>{e(x)}</li>" for x in m["pros"])
        cons = "".join(f"<li>{e(x)}</li>" for x in m["cons"])
        details.append(f"""
<h3 id="{m['id'].lower()}">{m['id']} · {e(m['name'])} {STATUS_TAG[m['status']]}</h3>
<p><strong>Eligibility.</strong> {e(m['eligibility'])}</p>
<p><strong>Cost rail.</strong> {e(RAIL_LABEL.get(m['rail'], 'no published per-transfer price'))} · <strong>Flag.</strong> {flag_link(m['flag'])}</p>
<p><strong>Steps.</strong></p><ol class="steps">{steps}</ol>
<p><strong>Advantages.</strong></p><ul>{pros}</ul>
<p><strong>Drawbacks.</strong></p><ul>{cons}</ul>
<p><strong>China tax.</strong> {e(m['tax_cn'])}</p>
<p><strong>US tax.</strong> {e(m['tax_us'])}</p>
<p><small>Sources: {src(m['sources'])}</small></p>""")
    counts = {}
    for m in METHODS:
        counts[m["status"]] = counts.get(m["status"], 0) + 1
    body = f"""
<h1>Every method, with pros, cons, steps and tax treatment</h1>
<p class="lead">{len(METHODS)} candidates: {counts.get('lawful', 0)} lawful, {counts.get('conditional', 0)} conditional on an entitlement you must actually have,
{counts.get('not-a-cashout', 0)} that are real transactions but cannot move an existing balance, and {counts.get('prohibited', 0)} prohibited routes named only so the risk is explicit.
The category column is the point: most of the "ways to get money out of China" that circulate are either entitlements you must qualify for or
transactions you must actually undertake.</p>

<div class="note"><strong>No execution instructions for prohibited routes.</strong> M19-M21 describe the legal consequence of the pattern, not how to do it.
Splitting, nominee quotas, false invoices and virtual-currency conversion are named in S02 Art. 7 and S09 Section 1 as prohibited, with the fine bands in S01.</div>

<h2 id="summary">Summary table</h2>
{table(["ID", "Method", "Status", "Priced rail", "Eligibility (short)", "Sources"], rows)}

<h2 id="detail">Detail</h2>
{"".join(details)}
"""
    return shell("methods.html", "All methods", "21 CNY to USD routes with status, eligibility, steps, advantages, drawbacks and China/US tax treatment.", body)
def page_steps():
    phases = [
        ("Phase 0 - facts you must be able to state", [
            "Who the bank says you are: domestic individual (PRC resident ID) or overseas individual (passport) - S02 Arts. 2, 37; " + flag_link("F01") + ".",
            "What the balance is: salary, service income, property proceeds, inheritance, dividend, gift, or accumulated savings. The route follows the item, not your preference.",
            "When and how it was taxed in China, with the voucher or withholding record to prove it - S04.",
            "Whether the account has been reported in the US: FBAR above USD 10,000 aggregate (S16) and Form 8938 at its own thresholds (S17).",
            "Where it is going: your own account (required for Wise, S21), a joint account, or someone else's (which changes the analysis).",
        ]),
        ("Phase 1 - classify the money before you ask for a price", [
            "Ask the branch to confirm the current-account item and the exact document list in writing.",
            "If the answer is 'salary', collect the employment contract, the income proof and the tax record - the 2026 SAFE answer describes exactly this file (S04).",
            "If the answer is 'property', stop: the property route needs a completed sale, PRC tax paid, and SAFE approval before any purchase (S02 Art. 22; " + flag_link("F12") + ").",
            "If the answer is 'inheritance', the file runs through the SAFE office at the deceased's household-registration place (S05 Art. 5).",
            "If the money cannot be tied to any item, no lawful purchase exists for it. That is the finding, not a step to work around.",
        ]),
        ("Phase 2 - get comparable, executable quotes", [
            "Ask for the amount you will actually receive, not the rate: BOC charges 0.1% capped at CNY 260 plus CNY 150 cable (S11); HSBC charges 0.1% capped at CNY 500 plus CNY 120 (S13); Bank of America charges USD 15 to receive (S14).",
            "Ask each bank to quote SHA and OUR separately, so the correspondent deduction is either visible or priced (S11 note 4; S13 item 2.2.4.1).",
            "Take all quotes on the same day: the same board moved about 0.1% within one session (" + flag_link("F19") + ").",
            "Write down the timestamp of each quote. A quote without a time cannot be compared.",
        ]),
        ("Phase 3 - execute one wire, then check what arrived", [
            "Instruct the transfer to your own account and keep the purchase slip and SWIFT reference.",
            "Reconcile the amount received against the quote: any shortfall is the intermediary deduction that no source publishes (" + flag_link("F18") + ").",
            "Record the total cost as a percentage of the amount: at USD 100,000 the known total is about " + pct(LADDERS["L1"][9]["pct_of_target"] / 100) + " (see the ladder).",
            "If the shortfall is material, reprice the next wire with OUR.",
        ]),
        ("Phase 4 - reporting, in the same year", [
            "FBAR (FinCEN 114) due 15 April with an automatic extension to 15 October, filed with FinCEN not the IRS (S16).",
            "Form 8938 with the return if the threshold is met (S17).",
            "Form 3520 Part IV if a foreign person gave you more than USD 100,000 in aggregate in the year (S18).",
            "Keep the bank statements, the purchase slip and the tax voucher for at least five years (S16 record-keeping guidance).",
        ]),
    ]
    phase_html = "".join(
        f'<h2 id="{i}">{e(title)}</h2><ol class="steps">' + "".join(f"<li>{x}</li>" for x in items) + "</ol>"
        for i, (title, items) in enumerate(phases)
    )
    bank_rows = [
        ["BOC branch, full amount", "Commission 0.1% floor CNY 50 cap CNY 260; cable CNY 150; overseas charges at actual cost; optional full arrival USD 15 (correspondent at BOC New York) or USD 25.", "No conversion commission: the rate is the price.", src(["S11"])],
        ["BOC draft instead of wire", "Same commission band; postage at actual cost; recall up to CNY 50 plus cable.", "US collection fee not published - incomplete total.", src(["S11", "S14"])],
        ["HSBC China, Premier/Advance", "0.1% floor CNY 100 cap CNY 500; cable CNY 120; CNY 200 pre-collected if you ask for full payment to the beneficiary.", "Exchange rate not published - fees-only.", src(["S13"])],
        ["HSBC China, private banking individual", "No commission and no cable charge for outgoing transfers.", "Still exposes you to HSBC's unpublished rate.", src(["S13"])],
        ["Wise from CNY", "No fixed fee published; CNY 300,000 per transfer from the bank app, CNY 50,000 from Alipay; same-owner destination only.", "Overall limit equals after-tax salary proved by the tax record.", src(["S21"])],
        ["Foreign ATM on a BOC debit card", "CNY 12 + 1% per withdrawal, capped at CNY 112; CNY 10,000 per card per day; CNY 100,000 per person per year.", "Operator surcharge on screen; exceeding the annual cap suspends the facility for the year and the next.", src(["S11", "S07"])],
    ]
    body = f"""
<h1>Step by step: exactly how each route works</h1>
<p class="lead">The order matters more than the tactics. Four of the five phases below produce no transfer at all if the previous one was skipped -
that is the point of them, because an undocumented purchase is the one thing that turns a {pct(HALF)} spread into a 30% fine.</p>

{phase_html}

<h2 id="banks">The priced routes, one row each</h2>
{table(["Route", "What the published document says", "What it does not say", "Sources"], bank_rows)}

<h2 id="property">If the balance is property or inheritance, the sequence is different</h2>
<ol class="steps">
<li><strong>Realise the asset first, lawfully.</strong> An emigrant transfer moves property you owned <em>before</em> emigrating; an inheritance transfer moves what you lawfully inherited (S05 Art. 2).</li>
<li><strong>Settle the PRC tax on the disposal.</strong> Property transfer is 20% of proceeds minus original value and reasonable expenses (S10 Arts. 3(3), 6(5)); the tax certificate is a required document (S05 Art. 8(6)).</li>
<li><strong>Apply to the right SAFE office.</strong> Emigrant: the office at your original household-registration place. Inheritance: the office where the deceased was registered (S05 Art. 5). Combining several deceased persons' estates is now allowed (S06 VI.3).</li>
<li><strong>Collect identity and status proof.</strong> For emigration this includes cancellation of PRC household registration and proof of settlement abroad (S05 Art. 8(4)) - the requirement that trips most people up ({flag_link("F10")}).</li>
<li><strong>Remit to your own overseas account.</strong> The bank must not pay cash inside China after the sale (S05 Art. 11).</li>
<li><strong>Remit once or in instalments within the approved amount.</strong> The old 50% / half / balance staging was cancelled in 2014 (S06 VI.2), and notarisation of property and agency documents is no longer required (S06 VI.4).</li>
</ol>

<h2 id="ask">What to ask, in writing</h2>
<ul>
<li>"Please confirm my classification under PBOC Order [2006] No. 3 and the document list for my balance."</li>
<li>"Please quote the amount my US account will receive, for SHA and for OUR, at today's rate, with the time of the quote."</li>
<li>"Please state any intermediary or correspondent charge that may be deducted and whether it is included in the OUR price."</li>
<li>"If I repeat this transfer, will the same file be accepted or must I resubmit?"</li>
</ul>

<h2 id="red">Red flags that change the route immediately</h2>
<ul>
<li>Anyone offering to use a relative's or friend's quota for your money - that is the splitting prohibition in S02 Art. 7.</li>
<li>Anyone offering to route through virtual currency inside China - prohibited financial activity (S09 Section 1).</li>
<li>Anyone offering a matched transfer with an offshore counterparty - private/disguised dealing, fine band up to 30% with confiscation (S01 Art. 45).</li>
<li>A "full arrival" promise without a written price - BOC's is USD 15 or 25 depending on the correspondent relationship (S11 note 5), HSBC pre-collects CNY 200 (S13).</li>
</ul>
"""
    return shell("steps.html", "Step by step", "The exact sequence for each route, the bank-by-bank instructions, the property route and the questions to ask in writing.", body)


def page_tax():
    cn_rows = [
        ["Salary and wages", "Comprehensive income, 3%-45% progressive; non-resident salary computed monthly with a CNY 5,000 deduction", "Applies to the money before it reaches the account. A withholding record is part of the purchase file (S04).", src(["S10", "S04"])],
        ["Property transfer", "Flat 20% of proceeds minus original value and reasonable expenses", "The largest number in this project when the balance is a property sale. Paid before the tax certificate supports a remittance.", src(["S10"])],
        ["Interest, dividends, bonuses", "Flat 20%", "A dividend route is taxed at source before the company remits.", src(["S10"])],
        ["Business income", "5%-35% progressive", "Relevant to a sole proprietorship or partnership interest, not to a personal deposit.", src(["S10"])],
        ["FX conversion itself", "No category - Art. 2 lists nine income types and none is a currency conversion", "No PRC income tax arises from turning CNY into USD. The obligation is documentary, not a second tax.", src(["S10"])],
        ["Tax clearance on emigration", "Required before cancelling PRC household registration", "Relevant if you are giving up PRC registration; it is a precondition for the emigrant transfer route.", src(["S10", "S05"])],
        ["Evasion / disguised capital transfer", "Fine up to 30% of the amount; 30% to 100% in serious cases", "Administrative, not tax. Avoidable by using a documented route.", src(["S01"])],
        ["Illegal FX arbitrage (false documents)", "Fine up to 30%; serious cases from 30% to 100%; criminal liability possible", "The prohibition on false commercial documents is explicit in S02 Art. 7.", src(["S01", "S02"])],
        ["Private or disguised FX dealing", "Confiscation of the proceeds plus a fine up to 30%; criminal liability possible", "This is the underground-bank band.", src(["S01"])],
        ["Illegal cash carrying", "Warning plus a fine up to 20% of the amount", "Above USD 10,000 out of China is in principle not permitted (S08).", src(["S01", "S08"])],
        ["Reporting/document failures", "For an individual, up to CNY 50,000", "Covers false documents, account-rule breaches and obstructing an inspection.", src(["S01"])],
    ]
    us_rows = [
        ["Principal received", "Not income", "Moving your own already-taxed money creates no income. Character follows the original source.", src(["S15"])],
        ["Currency gain or loss on the CNY", "Section 988 ordinary treatment by default; personal-transaction exclusion", "No gain is recognised on a personal transaction unless it would exceed USD 200, and the exclusion does not apply where allocable expenses meet section 162 or 212.", src(["S15"])],
        ["Interest, dividends, gains abroad", "Taxable worldwide income; foreign tax credit possible", "Reported whether or not remitted. A credit is limited to foreign tax on the same income.", src(["S10"])],
        ["FBAR - FinCEN 114", "File when foreign accounts exceed USD 10,000 in aggregate at any time", "Due 15 April, automatic extension to 15 October; filed with FinCEN, apart from the return.", src(["S16"])],
        ["FBAR penalty - non-willful", "Adjusted maximum USD 16,536 per report", "Assessed on or after 2025-01-17; the statutory USD 10,000 is replaced by this figure.", src(["S19"])],
        ["FBAR penalty - willful", "Adjusted maximum USD 165,353", "The greater-of rules in the statute still apply to the underlying assessment; this is the adjusted maximum.", src(["S19"])],
        ["Form 8938", "Threshold USD 50,000 year-end / 75,000 any time (US resident, single); 200,000 / 300,000 living abroad", "Joint filers double the figures. Penalty up to USD 10,000 plus USD 10,000 per 30 days, maximum USD 60,000.", src(["S17"])],
        ["Form 3520 - foreign gift", "Report gifts from a nonresident alien or foreign estate above USD 100,000 aggregate", "2026 threshold for purported gifts from foreign corporations or partnerships is USD 20,573. Penalties under IRC 6039F(c).", src(["S18"])],
    ]
    body = f"""
<h1>Tax and penalties: what is actually owed, and what is actually fined</h1>
<p class="lead">Two systems, four questions. China: is the conversion taxed, and is the source taxed? US: is the receipt income, and is it reported?
The answers are short. The penalty columns are what make the paperwork worth doing.</p>

<div class="box ok"><strong>Short answer.</strong> Converting CNY to USD is not a taxable event in either country. The money's <em>source</em> may already have been taxed
in China (salary, property gain, dividend) and is taxable in the US whether or not you move it. The fines attach to <em>how</em> you move it and
<em>whether you report the account</em> - not to the conversion.</div>

<h2 id="china">China</h2>
{table(["Item", "Rate or rule", "How it applies here", "Sources"], cn_rows)}

<h2 id="us">United States</h2>
{table(["Item", "Rule", "How it applies here", "Sources"], us_rows)}

<h2 id="worked">The two worked comparisons that matter</h2>
<h3>Converting USD 400,000 of already-taxed principal</h3>
<p>PRC income tax on the conversion: none identified - no category in S10 Art. 2.
US income tax on the conversion: none on principal; the section 988 currency leg is a personal transaction, so no gain is recognised unless it would exceed USD 200 (S15 (e)).
Known transfer cost: {usd(LADDERS["L1"][-1]["known_total_usd"])} ({LADDERS["L1"][-1]["pct_of_target"]:,.4f}%). The only large US number in the file is the reporting penalty if the account was never disclosed:
USD 16,536 non-willful per report or USD 165,353 willful (S19).</p>

<h3>Selling a mainland property with a gain</h3>
<p>The PRC rate is 20% of (proceeds - original value - reasonable expenses) (S10 Arts. 3(3), 6(5)). No gain is supplied in this project, so no amount is shown:
the rate is published, the base is personal ({flag_link("F12")}). In the US the same disposal is a taxable event with the gain computed in dollars; a foreign tax credit may
reduce double taxation if the PRC tax qualifies.</p>

<h2 id="reporting">Reporting calendar for a US citizen holding the account</h2>
<ol class="steps">
<li><strong>During the year:</strong> keep statements showing the maximum balance, because both FBAR and Form 8938 ask for maximum values (S16, S17).</li>
<li><strong>15 April:</strong> FBAR due; Form 8938 with the return; Form 3520 if a reportable foreign gift was received (S18).</li>
<li><strong>15 October:</strong> automatic FBAR extension, no request needed (S16).</li>
<li><strong>Five years:</strong> keep FBAR records from the due date (S16).</li>
</ol>

<div class="note"><strong>Not computed here.</strong> Any tax on an unknown gain or income; treaty relief for dividends ({flag_link("F13")}); the percentage penalty under IRC 6039F(c)
({flag_link("F17")}); US treatment of a foreign insurance policy ({flag_link("F15")}); and the 1% remittance excise tax, which is not re-verified in this session and does not apply to this direction on its face.</div>
"""
    return shell("tax.html", "Tax & penalties", "China's nine income categories, section 988, FBAR/8938/3520 thresholds and the administrative fine bands, each sourced.", body)
def page_flagged():
    rows = [[f'<strong><a href="#{f["id"].lower()}">{e(f["id"])}</a></strong>',
             f'<span class="tag {"stop" if f["severity"] == "high" else "warn"}">{e(f["severity"])}</span>',
             e(f["title"]), e(f["action"]), src(f["sources"])] for f in FLAGS]
    detail = "".join(
        f'<h3 id="{f["id"].lower()}">{e(f["id"])} · {e(f["title"])} '
        f'<span class="tag {"stop" if f["severity"] == "high" else "warn"}">{e(f["severity"])}</span></h3>'
        f'<p>{e(f["detail"])}</p><p><strong>What to do:</strong> {e(f["action"])}</p>'
        f'<p><small>Sources: {src(f["sources"])}</small></p>'
        for f in FLAGS)
    body = f"""
<h1>Flagged for Review</h1>
<p class="lead">{len(FLAGS)} items that limit this edition's conclusions. Nothing on this page blocks publication; everything on it changes what a careful reader should do next.
Each flag names what is missing, why it matters, and the official document that would resolve it.</p>

<div class="note"><strong>How to read a flag.</strong> A flag is not a disclaimer. Where a number is missing, the corresponding cell is blank rather than zero,
and the flag explains which published document does not exist. Where an interpretation is contested, the flag shows both texts side by side.</div>

{table(["ID", "Severity", "Issue", "What to do", "Sources"], rows)}

<h2 id="detail">Detail</h2>
{detail}
"""
    return shell("flagged.html", "Flagged for Review", "Unresolved items, missing published values and contested interpretations, with the document that would settle each one.", body)


def page_audit():
    sourced = [a for a in AUDIT if a["comparator"]]
    internal = [a for a in AUDIT if not a["comparator"]]
    rows = [[f'<strong><a href="#{a["id"].lower()}">{e(a["id"])}</a></strong>',
             f'<span class="tag {"stop" if a["severity"] == "high" else "warn" if a["severity"] == "medium" else ""}">{e(a["severity"])}</span>',
             e(a["title"]), f'<code>{e(a["location"])}</code>',
             src(a["comparator"])]
            for a in sourced]
    detail = "".join(
        f'<h3 id="{a["id"].lower()}">{e(a["id"])} · {e(a["title"])}</h3>'
        f'<p><strong>Finding.</strong> {e(a["finding"])}</p>'
        f'<p><strong>Where.</strong> <code>{e(a["location"])}</code></p>'
        f'<p><strong>Official comparator.</strong> {src(a["comparator"]) if a["comparator"] else "None: this is an internal consistency finding."}</p>'
        f'<p><strong>Recommendation.</strong> {e(a["recommendation"])}</p>'
        for a in AUDIT)
    body = f"""
<h1>Repository audit</h1>
<p class="lead">This edition was built inside an existing repository that already contains nine earlier editions, a consolidated portal and a shared coordination board.
This page records what a line-by-line review found. Nothing outside <code>edition-l/</code> was edited except the append-only coordination board and, at integration time,
the portal's navigation.</p>

<div class="box"><strong>Scope and method.</strong> Files were read directly. Rates and tariffs were re-fetched from the issuing institution and compared with what the repository publishes.
Counts (HTTP links, stale board entries, duplicate grids) were produced with greps over the working tree and are reproducible from the commands quoted on the
<a href="methodology.html">methodology page</a>. Prior editions' own verifiers were executed and pass: no finding below disputes that their arithmetic is
internally consistent; the findings concern sourcing, labelling and consistency with the documents re-read here.</div>

<h2 id="sourced">Findings with an official comparator</h2>
{table(["ID", "Severity", "Finding", "Location", "Official comparator"], rows)}

<h2 id="internal">Internal consistency findings (no official comparator)</h2>
<p>These are defects of the repository itself - stale board entries, duplicated dashboards, inconsistent labels. There is no external document to cite,
so they are listed rather than tabulated. Each one is verifiable from the commands on the <a href="methodology.html#reproduce">methodology page</a>.</p>
<ul>
{"".join(f'<li><strong><a href="#{a["id"].lower()}">{a["id"]}</a> ({e(a["severity"])}) - {e(a["title"])}</strong>: {e(a["finding"])} <em>Location:</em> <code>{e(a["location"])}</code>. <em>Recommendation:</em> {e(a["recommendation"])}</li>' for a in internal)}
</ul>

<h2 id="detail">Detail</h2>
{detail}

<h2 id="clean">What the prior editions got right</h2>
<ul>
<li><strong>No invented numbers.</strong> Across editions B-J the unpriced components are consistently blank rather than zero, and the earlier audit pages already
flag the personal-fact gap. That discipline is preserved here.</li>
<li><strong>The 2026 virtual-currency repeal claim is correct.</strong> Prior editions state that Yinfa [2026] No. 42 repealed the 2021 notice; the source text confirms it
(S09, final clause).</li>
<li><strong>The section 988 nuance is correct.</strong> Prior editions warn that the USD 200 personal-transaction rule is not a universal allowance; S15 (e)(3) supports that.</li>
<li><strong>The 2004/2014 staging conflict is handled correctly.</strong> Prior editions flag that Art. 6 of the 2004 measures was superseded; S06 VI.2 confirms the staging was cancelled.</li>
</ul>
"""
    return shell("audit.html", "Repository audit", "Twelve findings from a line-by-line review of the existing editions, with locations and official comparators.", body)


def page_sources():
    rows = []
    for sid in sorted(SOURCES):
        s = SOURCES[sid]
        rows.append([
            f'<strong id="{sid.lower()}">{e(sid)}</strong>',
            f'<a href="{e(s["url"])}" rel="noopener noreferrer">{e(s["title"])} ↗</a>',
            e(s["publisher"]), f'<span class="tag {"live" if s["kind"] == "government" else ""}">{e(s["kind"])}</span>',
            f'<code>{e(s["locator"])}</code>', e(s["supports"]),
        ])
    body = f"""
<h1>Sources</h1>
<p class="lead">{len(SOURCES)} documents, all fetched and read on 2026-11-10. For each one the exact article, item number or page range that was inspected is recorded,
so a reader can check the same text rather than the whole website.</p>

<div class="note"><strong>What a citation proves.</strong> An official citation proves the rule exists as quoted. It does not prove that a branch will apply it to your file,
that a provider's price will still be the same tomorrow, or that a link is up forever. Provider documents are used only for that provider's own prices.</div>

{table(["ID", "Document", "Publisher", "Type", "Locator inspected", "What it supports"], rows)}

<h2 id="not">Documents that were deliberately not used as evidence</h2>
<ul>
<li><strong>Central parity as a cost benchmark.</strong> Fetched and shown (S20) only to explain why it must not be used; see {flag_link("F20")}.</li>
<li><strong>Third-party fee-comparison sites and news articles.</strong> Not used anywhere in this edition, even where they agree with the arithmetic.</li>
<li><strong>Other banks' tariffs.</strong> Not fetched, therefore not quoted; those cells are blank ({flag_link("F04")}).</li>
<li><strong>Wise's live price.</strong> Only available at transfer setup, so no figure is shown ({flag_link("F05")}).</li>
</ul>
"""
    return shell("sources.html", "Sources", "Twenty-one official and first-party documents with the exact provision inspected and what each supports.", body)


def page_methodology():
    formulas = [
        ["CNY needed for a target", "target × 6.6851", "BOC selling rate for USD per 100 = 668.51, i.e. 6.6851 per USD (S12)."],
        ["One-way half-spread", "(sell − mid) / mid = (6.6851 − 6.6711) / 6.6711", f"= {pct(HALF)}. Midpoint of BOC's own bid and offer."],
        ["Round-trip spread", "(sell − buy) / mid = (6.6851 − 6.6571) / 6.6711", f"= {pct(ROUND_TRIP)}."],
        ["BOC commission", "min(260, max(50, 0.001 × CNY amount))", "S11 item 210105008: 1 per mille, floor CNY 50, cap CNY 260."],
        ["BOC cable charge", "CNY 150 international (CNY 80 for HK/Macau/Taiwan)", "S11 item 210105008."],
        ["BOC fees expressed in USD", "CNY fees ÷ 6.6851", "Same selling rate, so the fee is valued at the rate you are paying."],
        ["Receiving bank fee", "USD 15 per incoming international wire", "S14, Bank of America personal schedule."],
        ["Known total (L1)", "spread + commission + cable + receiving", "No other component has a published value; see " + flag_link("F18") + "."],
        ["Quota-split wires", "ceil(target ÷ 50,000)", "S03 Art. 2 annual total; fixed charges repeat per wire."],
        ["HSBC commission", "min(500, max(100, 0.001 × CNY amount)) + CNY 120 cable", "S13 items 2.2.4.1-2. HSBC's FX rate is unpublished, so no all-in total."],
        ["ATM fee rate", "min(112, 12 + 1% × withdrawal) ÷ withdrawal", "Best case at the CNY 10,000 per-card daily cap: " + pct(D(str(ATM["per_withdrawal_cap_cny"])) / D(str(ATM["daily_cap_per_card_cny"]))) + " of the amount moved."],
        ["ATM years", "ceil(target × 6.6851 ÷ 100,000)", "CNY 100,000 per person per calendar year (S07)."],
        ["Cash trips", "ceil(target ÷ 10,000)", "USD 10,000 carrying limit above which a SAFE permit is in principle required (S08)."],
    ]
    formula_sources = ["S12", "S12", "S12", "S11", "S11", "S12", "S14", "S11 S12 S14", "S03", "S13", "S11 S07", "S07", "S08"]
    frows = [[e(a), f"<code>{e(b)}</code>", e(c), src(fs.split())] for (a, b, c), fs in zip(formulas, formula_sources)]
    body = f"""
<h1>Method, constants and limits</h1>
<p class="lead">Everything numeric on this site is produced by one Python script from two JSON data files. The script is deterministic: running it twice produces byte-identical pages.
A separate verifier recomputes every cell independently and fails the build on any mismatch.</p>

<h2 id="inputs">Constants used</h2>
{table(["Input", "Quantity", "Sources"], [
    ["BOC USD spot buying rate", f"CNY {MODEL['quotation']['buy_spot']:,.2f} per USD 100", src(["S12"])],
    ["BOC USD spot selling rate", f"CNY {MODEL['quotation']['sell_spot']:,.2f} per USD 100", src(["S12"])],
    ["BOC reference rate (equals the CFETS parity that day)", f"CNY {MODEL['quotation']['reference']:,.2f} per USD 100", src(["S12", "S20"])],
    ["Quotation time (China)", f"{MODEL['quotation']['date']} {MODEL['quotation']['time_china']}", src(["S12"])],
    ["CFETS/SAFE central parity", f"CNY {MODEL['parity']['usd']:,.2f} per USD 100", src(["S20"])],
    ["BOC commission", f"{BOC['commission_rate']*100:.1f}%, floor CNY {BOC['commission_min_cny']}, cap CNY {BOC['commission_max_cny']}, cable CNY {BOC['cable_international_cny']}", src(["S11"])],
    ["HSBC commission", f"{HSBC['commission_rate']*100:.1f}%, floor CNY {HSBC['commission_min_cny']}, cap CNY {HSBC['commission_max_cny']}, cable CNY {HSBC['cable_cny']}", src(["S13"])],
    ["US receiving wire", f"USD {RECV:,.2f} (Bank of America)", src(["S14"])],
    ["ATM fee", f"CNY {ATM['per_withdrawal_fixed_cny']} + {ATM['per_withdrawal_rate']*100:.0f}% per withdrawal, cap CNY {ATM['per_withdrawal_cap_cny']}, annual cap CNY {ATM['annual_cap_cny']:,}", src(["S11", "S07"])],
    ["Cash carrying permit", f"CNY {CARRY['permit_fee_cny']} (waived to {CARRY['permit_fee_waived_until']}), limit USD {CARRY['permit_required_up_to_usd']:,} per trip", src(["S08", "S11"])],
    ["Annual total, if the purchase limb applies", f"USD {QUOTA:,.0f} per person per year", src(["S03"])],
], stacked=False)}

<h2 id="formulas">Formulas</h2>
{table(["Quantity", "Formula", "Source of each input", "Sources"], frows, stacked=False)}

<h2 id="verify">How this was verified</h2>
<ol class="steps">
<li><strong>Source-by-source retrieval.</strong> Each of the {len(SOURCES)} documents was fetched on 2026-11-10 and the specific provision noted in the Sources table was read. Figures were taken from the fetched text, not from memory.</li>
<li><strong>Deterministic build.</strong> <code>python3 edition-l/build/build.py</code> regenerates eleven pages plus <code>costs.json</code> and <code>costs.csv</code>; a second run produces identical bytes.</li>
<li><strong>Independent recomputation.</strong> <code>python3 edition-l/build/verify.py</code> re-derives every commission, cable charge, spread, percentage and split total with its own Decimal arithmetic and refuses to pass if any published cell differs.</li>
<li><strong>Citation per row.</strong> The verifier parses every generated page and requires at least one HTTPS link to a government or first-party provider host in every data row; it also rejects a blank cell that carries a numeric value and a zero that represents an unknown.</li>
<li><strong>Link integrity.</strong> Every local href and every in-page anchor in this edition is resolved against the file system; external links must be HTTPS and on the documented host list.</li>
<li><strong>Non-regression.</strong> The pre-existing repository verifiers were run before and after integration and must still pass (see the coordination record).</li>
</ol>

<h2 id="limits">Limits a reader must respect</h2>
<ul>
<li>A known total is not a quote. It excludes the intermediary deduction, any tax on the money's source, documentation costs and the rate you will actually be given.</li>
<li>Provider prices are as published on 2026-11-10 and can change; the documents are linked so the price can be re-checked.</li>
<li>Personal eligibility is not determined. See {flag_link("F01")} and {flag_link("F22")}.</li>
<li>No live rate is displayed; the board figure is a timestamped observation and BOC itself says the executed rate governs (S12).</li>
<li>This is research, not legal, tax, investment or immigration advice, and it is not a substitute for the handling bank's review.</li>
</ul>

<h2 id="reproduce">Reproducing the audit counts</h2>
<pre><code>grep -rho 'href="http://[^"]*"' edition-* docs dossier | wc -l        # 368 plain-HTTP links
grep -c "in progress" COORDINATION.md                                 # 43 stale entries
du -sh edition-* | sort -h                                            # archive sizes
python3 edition-l/build/build.py &amp;&amp; python3 edition-l/build/verify.py</code></pre>
"""
    return shell("methodology.html", "Method & limits", "Constants, formulas, the verification procedure and the limits a reader must respect.", body)


def write_data():
    doc = {
        "edition": "L",
        "compiled": "2026-11-10",
        "quotation": MODEL["quotation"],
        "parity": MODEL["parity"],
        "derived": {
            "cny_per_usd_sell": str(SELL), "cny_per_usd_buy": str(BUY), "cny_per_usd_mid": str(MID),
            "cny_per_usd_parity": str(PARITY),
            "half_spread_pct": str(q(HALF * 100, "0.0001")),
            "round_trip_spread_pct": str(q(ROUND_TRIP * 100, "0.0001")),
            "sell_vs_parity_pct": str(q(SELL_VS_PARITY * 100, "0.0001")),
        },
        "inputs": {"boc": BOC, "hsbc": HSBC, "receiving": MODEL["receiving_bank"], "atm": ATM, "carry": CARRY, "quota_usd_per_year": str(QUOTA)},
        "targets": TARGETS,
        "milestones": MILESTONES,
        "ladders": LADDERS,
        "note": "Blank components are absent from these rows by design; see not_priced and the Flagged for Review page.",
    }
    (DATA / "costs.json").write_text(json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    with (DATA / "costs.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["ladder", "target_usd", "cny_needed", "fx_half_spread_usd", "commission_cny",
                    "cable_cny", "sender_usd", "receiving_usd", "known_total_usd", "pct_of_target",
                    "not_priced", "sources"])
        for key in ("L1", "L2", "L3", "L4", "L5"):
            for r in LADDERS[key]:
                w.writerow([
                    key, r["target_usd"], r.get("cny_needed", ""), r.get("fx_half_spread_usd", ""),
                    r.get("commission_cny", r.get("commission_cny_each", "")), r.get("cable_cny", ""),
                    r.get("sender_usd", r.get("sender_usd_total", "")), r.get("receiving_usd", r.get("receiving_usd_total", "")),
                    r.get("known_total_usd", r.get("fees_only_usd", "")), r.get("pct_of_target", r.get("pct_of_target_fees_only", "")),
                    r["not_priced"], " ".join(r["sources"]),
                ])


def main():
    SITE.mkdir(parents=True, exist_ok=True)
    pages = {
        "index.html": page_index(),
        "summary.html": page_summary(),
        "costs.html": page_costs(),
        "penalty.html": page_penalty(),
        "methods.html": page_methods(),
        "steps.html": page_steps(),
        "tax.html": page_tax(),
        "flagged.html": page_flagged(),
        "audit.html": page_audit(),
        "sources.html": page_sources(),
        "methodology.html": page_methodology(),
    }
    for name, html in pages.items():
        (SITE / name).write_text(html, encoding="utf-8")
    write_data()
    total = sum(len(v) for v in LADDERS.values())
    print(f"built {len(pages)} pages, {total} ladder rows, {len(TARGETS)} targets, "
          f"{len(METHODS)} methods, {len(FLAGS)} flags, {len(AUDIT)} audit findings, {len(SOURCES)} sources")


if __name__ == "__main__":
    main()
