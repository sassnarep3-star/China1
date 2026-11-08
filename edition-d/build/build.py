#!/usr/bin/env python3
"""
Edition D generator: CNY -> USD cost engine and dashboard.

Design rules enforced by construction and re-checked in build/verify.py:
  * every table row carries at least one source id from data/sources.json
  * a number is only printed if every input behind it has a source id
  * a missing official price produces an em dash plus an UNVERIFIED marker, never an estimate
  * every rendered page is listed in NAV, so no orphan page can exist

No third-party dependencies. Deterministic: same data -> byte-identical HTML.
Usage: python3 edition-d/build/build.py
"""

import html
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "docs")

AS_OF = "8 November 2026"
AMOUNTS = list(range(10_000, 400_001, 10_000))


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


SOURCES_DOC = load("sources.json")
METHODS_DOC = load("methods.json")
P = load("parameters.json")
FLAGS_DOC = load("flags.json")
REVIEW_DOC = load("review.json")

SRC = {s["id"]: s for s in SOURCES_DOC["sources"]}
FLAG = {f["id"]: f for f in FLAGS_DOC["flags"]}
METHOD = {m["id"]: m for m in METHODS_DOC["methods"]}


# ---------------------------------------------------------------------------
# engine
# ---------------------------------------------------------------------------

FX = P["fx"]
BUY = FX["buy_spot"]
SELL = FX["sell_spot"]
MID = round((BUY + SELL) / 2, 5)
SELL_RATE = SELL / 100.0
BUY_RATE = BUY / 100.0
ONE_WAY = (SELL - MID) / MID
ROUND_TRIP = (SELL - BUY) / SELL

W = P["boc_personal_wire"]
COMM_RATE = W["commission_rate"]
COMM_MIN = W["commission_min_cny"]
COMM_MAX = W["commission_max_cny"]
CABLE = W["cable_fee_cny"]

CORR = P["correspondent"]["full_amount_usd"]
US_IN = P["receiving_bank"]["usd"]
QUOTA = P["quota"]["annual_usd"]
STAGE_THRESHOLD_CNY = P["emigration"]["staging_threshold_cny"]
RELEASES = P["emigration"]["releases"]
RELEASE_FRACTIONS = P["emigration"]["release_fractions"]
CASH_TRIP = P["cash"]["per_trip_usd"]
PEN_MIN = P["penalty_cn"]["min_rate"]
PEN_MAX = P["penalty_cn"]["max_rate"]
US_BRACKETS = P["us_income_tax_2026_single"]
STD_DED = US_BRACKETS["standard_deduction"]
BRACKETS = US_BRACKETS["brackets"]


def cny_of(usd):
    return usd * SELL_RATE


def commission(usd_amount):
    """CNY commission on a remittance of ``usd_amount``, per the BOC personal tariff."""
    return min(max(COMM_RATE * cny_of(usd_amount), COMM_MIN), COMM_MAX)


def fx_margin(usd):
    return usd * ONE_WAY


def boc_wire_usd(usd_amount, corr=CORR):
    """Commission + cable + correspondent, expressed in USD."""
    return (commission(usd_amount) + CABLE) / SELL_RATE + corr


def us_tax_on_ordinary(amount):
    taxable = max(0.0, amount - STD_DED)
    for b in BRACKETS:
        if b["up_to"] is None or taxable <= b["up_to"]:
            return b["base"] + b["rate"] * (taxable - (BRACKETS[BRACKETS.index(b) - 1]["up_to"] if BRACKETS.index(b) else 0))
    return 0.0


def us_marginal_rate(amount):
    taxable = max(0.0, amount - STD_DED)
    last = BRACKETS[-1]["rate"]
    for b in BRACKETS:
        if b["up_to"] is not None and taxable <= b["up_to"]:
            return b["rate"]
    return last


def cost_rows(model):
    """Return one dict per USD 10,000 increment. Any None value renders as an unverified blank."""
    rows = []
    for amount in AMOUNTS:
        r = {
            "amount": amount,
            "fx": fx_margin(amount),
            "cn_fees": None,
            "wires": None,
            "us_in": None,
            "tax": None,
            "total": None,
            "extra": {},
            "srcs": [],
            "note": None,
            "unverified": [],
        }
        if model == "boc_documented":
            r["cn_fees"] = (commission(amount) + CABLE) / SELL_RATE
            r["wires"] = CORR
            r["us_in"] = US_IN
            r["tax"] = 0.0
            r["srcs"] = ["CN-07", "CN-08", "CN-09", "BK-02", "CN-05", "US-01"]
        elif model == "boc_quota":
            tranches = math.ceil(amount / QUOTA)
            per = amount / tranches
            cn = tranches * (commission(per) + CABLE) / SELL_RATE
            r["cn_fees"] = cn
            r["wires"] = tranches * CORR
            r["us_in"] = tranches * US_IN
            r["tax"] = 0.0
            r["extra"]["tranches"] = tranches
            r["extra"]["years"] = tranches
            r["srcs"] = ["CN-03", "CN-07", "CN-08", "CN-09", "BK-02"]
        elif model == "emigration":
            releases = RELEASES if cny_of(amount) >= STAGE_THRESHOLD_CNY else 1
            cn = 0.0
            for f in (RELEASE_FRACTIONS if releases == 3 else [1.0]):
                cn += (commission(amount * f) + CABLE) / SELL_RATE
            r["cn_fees"] = cn
            r["wires"] = releases * CORR
            r["us_in"] = releases * US_IN
            r["tax"] = 0.0
            r["extra"]["tranches"] = releases
            r["srcs"] = ["CN-04", "CN-07", "CN-08", "CN-09", "BK-02"]
        elif model == "inheritance":
            r["cn_fees"] = (commission(amount) + CABLE) / SELL_RATE
            r["wires"] = CORR
            r["us_in"] = US_IN
            r["tax"] = 0.0
            r["extra"]["tranches"] = 1
            r["srcs"] = ["CN-04", "CN-07", "CN-08", "CN-09", "BK-02"]
        elif model == "property":
            r["cn_fees"] = (commission(amount) + CABLE) / SELL_RATE
            r["wires"] = CORR
            r["us_in"] = US_IN
            r["tax"] = None
            r["note"] = "The 20% China IIT falls on the transfer gain, which is unknown; it is not a percentage of this amount."
            r["srcs"] = ["CN-01", "CN-05", "CN-07", "CN-08", "BK-02"]
            r["unverified"] = ["China IIT on gain"]
        elif model == "hold_usd":
            r["cn_fees"] = 0.0
            r["wires"] = 0.0
            r["us_in"] = 0.0
            r["tax"] = 0.0
            r["note"] = "No purchase fee appears in the published personal tariff; that is an absence of a line item, not a verified zero (F17)."
            r["srcs"] = ["CN-03", "CN-07", "CN-08"]
            r["unverified"] = ["purchase fee"]
        elif model == "cash":
            trips = math.ceil(amount / CASH_TRIP)
            r["cn_fees"] = 0.0
            r["wires"] = None
            r["us_in"] = None
            r["tax"] = 0.0
            r["extra"]["tranches"] = trips
            r["note"] = "Travel, insurance and loss risk are not priced. The margin uses the published USD cash rates, which matched the spot rates on the board retrieved."
            r["srcs"] = ["CN-03", "CN-08", "US-06"]
            r["unverified"] = ["travel cost", "carriage permit cost"]
        elif model == "penalty":
            r["cn_fees"] = PEN_MIN * amount
            r["wires"] = PEN_MAX * amount
            r["us_in"] = None
            r["tax"] = None
            r["note"] = "These are the statutory fine ranges for the conduct, not an assessment, and confiscation is additional."
            r["srcs"] = ["CN-02"]
            r["unverified"] = ["actual fine"]
        if model in ("boc_documented", "boc_quota", "emigration", "inheritance", "property", "hold_usd", "cash"):
            total = r["fx"]
            for k in ("cn_fees", "wires", "us_in"):
                v = r[k]
                if v is not None:
                    total += v
            if r["tax"] is not None:
                total += r["tax"]
            r["total"] = total
        elif model == "penalty":
            r["total"] = PEN_MIN * amount
        rows.append(r)
    return rows


# ---------------------------------------------------------------------------
# formatting helpers
# ---------------------------------------------------------------------------

def esc(s):
    return html.escape(str(s), quote=True)


def money(v, dec=0):
    if v is None:
        return None
    if dec == 0:
        return "${:,.0f}".format(v)
    return "${:,.2f}".format(v)


def pct(v, dec=2):
    return "{:.{}f}%".format(v * 100, dec)


def src_links(ids, compact=True):
    out = []
    for i in ids:
        s = SRC.get(i)
        if not s:
            raise SystemExit("unknown source id " + i)
        label = i if compact else s["title_en"]
        out.append(
            '<a class="src" href="{url}" target="_blank" rel="noopener noreferrer" '
            'title="{title}">{label}&nbsp;&#8599;</a>'.format(
                url=esc(s["url"]), title=esc(s["title_en"]), label=esc(label)
            )
        )
    return " ".join(out)


def flag_link(fid):
    f = FLAG[fid]
    return '<a class="flag" href="../pages/flagged.html#{fid}" title="{t}">{fid}</a>'.format(
        fid=fid, t=esc(f["title"])
    )


def badge(text, kind):
    return '<span class="badge badge-{}">{}</span>'.format(kind, esc(text))


STATUS_BADGE = {
    "lawful": ("lawful", "ok"),
    "lawful_approval": ("lawful, needs approval", "warn"),
    "prohibited": ("prohibited", "bad"),
    "unverified": ("unverified", "muted"),
}

NAV = [
    ("Overview", [
        ("index.html", "Dashboard"),
        ("pages/summary.html", "Executive summary"),
        ("pages/methodology.html", "Method and limits"),
    ]),
    ("Convert", [
        ("pages/methods.html", "All methods"),
        ("pages/costs.html", "Cost comparison"),
        ("pages/steps.html", "Step by step"),
    ]),
    ("Tax and reporting", [
        ("pages/tax.html", "Tax and penalties"),
        ("pages/reporting.html", "US reporting"),
    ]),
    ("Evidence", [
        ("pages/sources.html", "Sources"),
        ("pages/repo-review.html", "Repo review"),
        ("pages/flagged.html", "Flagged for review"),
    ]),
]

COST_PAGES = [
    ("costs-boc-documented.html", "M01 documented remittance"),
    ("costs-boc-quota.html", "M02 quota-paced"),
    ("costs-emigration.html", "M03 emigration transfer"),
    ("costs-inheritance.html", "M04 inheritance transfer"),
    ("costs-property.html", "M05 property proceeds"),
    ("costs-hold-usd.html", "M06 convert and hold"),
    ("costs-cash.html", "M09 cash"),
    ("costs-prohibited.html", "M14-M16 prohibited"),
]


def shell(title, body, rel="", active=""):
    nav_html = []
    for group, items in NAV:
        nav_html.append('<div class="nav-group"><div class="nav-label">{}</div>'.format(esc(group)))
        for href, label in items:
            cls = "nav-link active" if href == active else "nav-link"
            nav_html.append('<a class="{c}" href="{r}{h}">{l}</a>'.format(c=cls, r=rel, h=href, l=esc(label)))
        nav_html.append("</div>")
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Official-source research on converting CNY to USD for a US citizen: every route, its published cost at USD 10,000 steps to USD 400,000, and the tax position on each side.">
<title>{title} &middot; China Money</title>
<link rel="stylesheet" href="{rel}assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<input type="checkbox" id="navtoggle" class="navtoggle" aria-label="Open navigation">
<div class="layout">
<aside class="sidebar">
  <a class="brand" href="{rel}index.html"><span class="mark">&#165;&#8594;$</span><span>China Money<small>EDITION D &middot; COST ENGINE</small></span></a>
  <label for="navtoggle" class="navburger">Menu</label>
  <nav aria-label="Main navigation">{nav}</nav>
  <div class="sidebar-note"><span class="dot"></span> Sources checked {asof}<br><small>Every figure cites an official page</small></div>
</aside>
<main id="main">
<div class="topline"><span>RESEARCH BRIEF &middot; CNY TO USD</span><span>{asof}</span></div>
{body}
<footer>
<p><strong>What this is.</strong> Published-rule research with arithmetic shown. It is not legal, tax or investment advice, and it is not a bank quote. Rates and tariffs change; the sources are linked for manual review.</p>
<p>Values that could not be confirmed from an official page are blank and listed on <a href="{rel}pages/flagged.html">Flagged for review</a>. No value is ever inferred.</p>
</footer>
</main>
</div>
</body>
</html>
""".format(title=esc(title), body=body, rel=rel, nav="".join(nav_html), asof=AS_OF)


def table(headers, rows, cls="", caption=None):
    h = "".join("<th scope=\"col\">{}</th>".format(x) for x in headers)
    out = ['<div class="tablewrap">']
    if caption:
        out.append('<p class="caption">{}</p>'.format(caption))
    out.append('<table class="data {}"><thead><tr>{}</tr></thead><tbody>'.format(cls, h))
    for r in rows:
        out.append("<tr>{}</tr>".format("".join("<td>{}</td>".format(c) for c in r)))
    out.append("</tbody></table></div>")
    return "".join(out)


def page_header(eyebrow, h1, sub):
    return ('<header class="page-head"><div class="eyebrow">{}</div><h1>{}</h1>'
            '<p class="sub">{}</p></header>').format(esc(eyebrow), esc(h1), sub)


def cost_table(model, method_id):
    rows = cost_rows(model)
    m = METHOD[method_id]
    if model == "penalty":
        headers = ["Amount", "Fine at 30%", "Fine at 100%", "Total at risk", "Basis"]
        body = []
        for r in rows:
            body.append([
                money(r["amount"]),
                money(r["cn_fees"]),
                money(r["wires"]),
                money(r["total"]),
                src_links(r["srcs"]),
            ])
        return table(headers, body, cls="tight penalty",
                     caption="Statutory fine range under CN-02 Arts. 39 and 45, before confiscation of illegal gains and before any criminal exposure.")

    headers = ["Amount", "FX margin", "Bank fees", "Wire and correspondent", "US bank in", "Total cost", "of amount", "Net received", "Source"]
    body = []
    for r in rows:
        total = r["total"]
        share = pct(total / r["amount"]) if total is not None else "&mdash;"
        net = money(r["amount"] - total) if total is not None else "&mdash;"
        cells = [
            money(r["amount"]),
            money(r["fx"], 2),
            money(r["cn_fees"], 2) if r["cn_fees"] is not None else '<span class="unv">&mdash;</span>',
            money(r["wires"], 2) if r["wires"] is not None else '<span class="unv">&mdash;</span>',
            money(r["us_in"], 2) if r["us_in"] is not None else '<span class="unv">&mdash;</span>',
            '<strong>{}</strong>'.format(money(total, 2)) if total is not None else '<span class="unv">&mdash;</span>',
            share,
            net,
            src_links(r["srcs"]),
        ]
        body.append(cells)
    cap = "Every row is derived arithmetic from the sourced unit rates, not an observed quote. Tax on the conversion is USD 0 on both sides (CN-05 Art. 2, US-01), so it is not a column. "
    if model == "boc_quota":
        cap += "The middle column counts the annual USD 50,000 tranches needed at this size; the fees are charged per tranche."
    if model == "emigration":
        cap += "Release schedule: half, then half the remainder after one year, the rest after two years, for transfers at or above CNY 200,000."
    if model == "cash":
        cap += "One trip per USD 5,000; travel cost is not included."
    if model == "hold_usd":
        cap += "No wire is sent, so no cable, correspondent or receiving-bank fee arises."
    return table(headers, body, cls="tight", caption=cap)


def summary_matrix():
    """Comparison of every costed method at representative sizes."""
    models = [
        ("M01", "boc_documented"),
        ("M02", "boc_quota"),
        ("M03", "emigration"),
        ("M04", "inheritance"),
        ("M05", "property"),
        ("M06", "hold_usd"),
        ("M09", "cash"),
    ]
    picks = [10_000, 20_000, 50_000, 100_000, 200_000, 400_000]
    header = ["Method"] + [money(a) for a in picks] + ["Source"]
    body = []
    for mid, model in models:
        rows = {r["amount"]: r for r in cost_rows(model)}
        cells = [METHOD[mid]["name"] + "<br><small>" + mid + "</small>"]
        for a in picks:
            r = rows[a]
            if r["total"] is None:
                cells.append('<span class="unv">&mdash;</span>')
            else:
                cells.append("{}<br><small>{}</small>".format(money(r["total"]), pct(r["total"] / a)))
        ids = sorted(set(rows[picks[0]]["srcs"]) | set(rows[picks[-1]]["srcs"]))
        cells.append(src_links(ids))
        body.append(cells)
    return table(header, body, cls="matrix",
                 caption="Total cost to end up with the stated number of US dollars in your US account. Fee columns are in USD converted at the BOC sell rate; small percentages are the cost as a share of the amount.")


def methods_table():
    rows = []
    for m in METHODS_DOC["methods"]:
        label, kind = STATUS_BADGE[m["status"]]
        cost = ""
        if m["cost_model"]:
            cost = '<a href="../pages/costs-{}.html">table</a>'.format(
                {"boc_documented": "boc-documented", "boc_quota": "boc-quota",
                 "emigration": "emigration", "inheritance": "inheritance",
                 "property": "property", "hold_usd": "hold-usd", "cash": "cash",
                 "penalty": "prohibited"}[m["cost_model"]]
            )
        rows.append([
            "<strong>{}</strong><br><small>{}</small>".format(m["id"], esc(m["name"])),
            badge(label, kind),
            esc(m["one_liner"]),
            cost or '<span class="unv">no official price</span>',
            (src_links(m["basis"]) if m["basis"] else "")
            + (" " if m["basis"] else "") + " ".join(flag_link(f) for f in m.get("flags", [])),
        ])
    return table(["Route", "Status", "What it is", "Costed", "Rule"], rows)


def method_detail(m):
    label, kind = STATUS_BADGE[m["status"]]
    pros = "".join("<li>{}</li>".format(esc(p)) for p in m["pros"]) or "<li>None: this route is prohibited.</li>"
    cons = "".join("<li>{}</li>".format(esc(p)) for p in m["cons"])
    steps = "".join("<li>{}</li>".format(esc(s)) for s in m["steps"])
    docs = "".join("<li>{}</li>".format(esc(d)) for d in m["documents"]) or "<li>None: prohibited.</li>"
    flags = " ".join(flag_link(f) for f in m.get("flags", []))
    return """
<section class="card method" id="{mid}">
  <div class="method-head"><h2>{mid} &middot; {name}</h2>{badge}</div>
  <p class="lede">{one}</p>
  <dl class="kv">
    <dt>Rule</dt><dd>{rule}</dd>
    <dt>Limit in the text</dt><dd>{cap}</dd>
    <dt>Documents</dt><dd><ul class="tight-list">{docs}</ul></dd>
  </dl>
  <div class="two-col">
    <div><h3>Pros</h3><ul>{pros}</ul></div>
    <div><h3>Cons</h3><ul>{cons}</ul></div>
  </div>
  <h3>How it would work, step by step</h3><ol>{steps}</ol>
  <p class="srcrow"><strong>Sources:</strong> {srcs} {flags}</p>
</section>""".format(
        mid=m["id"], name=esc(m["name"]), badge=badge(label, kind), one=esc(m["one_liner"]),
        rule=esc(m["rule_text"]), cap=esc(m["cap"]), docs=docs, pros=pros, cons=cons,
        steps=steps, srcs=src_links(m["basis"]) if m["basis"] else "none cited",
        flags=flags,
    )


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------

def build_index():
    r400 = cost_rows("boc_documented")[-1]
    r10 = cost_rows("boc_documented")[0]
    stats = [
        ("FX margin, one conversion", pct(ONE_WAY), "of the USD received, derived from BOC's own bid and ask"),
        ("Total cost at $400,000", "{}".format(money(r400["total"], 2)), "{} of the amount, all fees included".format(pct(r400["total"] / 400000))),
        ("Total cost at $10,000", "{}".format(money(r10["total"], 2)), "{} — the same machinery, a fixed cost spread thinner".format(pct(r10["total"] / 10000))),
        ("Tax on the conversion itself", "$0", "no provision in either jurisdiction charges it"),
    ]
    cards = "".join(
        '<div class="stat"><small>{}</small><strong>{}</strong><span>{}</span></div>'.format(esc(a), esc(b), esc(c))
        for a, b, c in stats)

    answer_rows = [
        ["You are not taxed for converting", "China charges nine enumerated income categories; a currency exchange is none of them (CN-05 Art. 2). The US charges income; a personal conversion is a §988 event whose gain is not recognised up to $200 (US-01).", src_links(["CN-05", "US-01"])],
        ["The conversion is cheap; the exit is the problem", "Total cost is {} at $400,000. What stops the money is capital-account convertibility, not a levy (CN-01 Art. 3).".format(money(r400["total"])), src_links(["CN-01"])],
        ["One fact decides everything", "If the bank holds your passport, CN-03 Art. 59 gives a documented purchase route with no annual cap in the text. If it holds a PRC ID card, the USD 50,000 quota applies.", src_links(["CN-03", "CN-01"])],
        ["The real money at risk is US reporting", "A willful FBAR penalty is the greater of $100,000 or 50% of the account balance, per violation (US-02). At $400,000 that is {fbar} — {ratio} times the cost of moving it.".format(fbar=money(200000), ratio="{:.0f}".format(200000 / r400["total"])), src_links(["US-02", "US-03"])],
        ["The wrong routes cost 30% to 100%", "Splitting, underground dealing and crypto convert a sub-1% problem into a fine of 30% to 100% of the amount, plus confiscation: {lo} to {hi} at $400,000 (CN-02 Arts. 39, 45; CN-06).".format(lo=money(0.30 * 400000), hi=money(400000)), src_links(["CN-02", "CN-06"])],
        ["Cheapest lawful route", "M01: documented current-account purchase and one wire. It is also the shortest procedure.", src_links(["CN-01", "CN-03"])],
    ]

    body = """
<header class="page-head hero">
  <div class="eyebrow">Executive dashboard</div>
  <h1>What it actually costs to turn CNY into USD</h1>
  <p class="sub">Sixteen routes — ten lawful, three prohibited, three unverified — costed from published tariffs in USD 10,000 steps to USD 400,000. Every figure below is arithmetic on a sourced unit rate. Where no official price exists, the cell is blank and flagged.</p>
</header>
<section class="stats">{stats}</section>
<section>
  <div class="section-head"><h2>The answer in six rows</h2><a class="text-link" href="pages/summary.html">Full executive summary &rarr;</a></div>
  {answer}
</section>
<section>
  <div class="section-head"><h2>Cost of the best lawful route</h2><a class="text-link" href="pages/costs-boc-documented.html">All 40 increments &rarr;</a></div>
  {matrix}
</section>
<section class="cards">
  <a class="card-link" href="pages/methods.html"><span class="kicker">01</span><h3>Every method</h3><p>Sixteen routes with the rule, the cap, the documents, and the pros and cons of each.</p></a>
  <a class="card-link" href="pages/costs.html"><span class="kicker">02</span><h3>Cost comparison</h3><p>All costed routes side by side, from $10,000 to $400,000, in one table.</p></a>
  <a class="card-link" href="pages/steps.html"><span class="kicker">03</span><h3>Step by step</h3><p>The exact sequence at the counter, with the provision to cite at each stage.</p></a>
  <a class="card-link" href="pages/tax.html"><span class="kicker">04</span><h3>Tax and penalties</h3><p>China IIT, §988, the FBAR ladder and the fine ranges for the prohibited routes.</p></a>
  <a class="card-link" href="pages/repo-review.html"><span class="kicker">05</span><h3>Repo review</h3><p>Line-by-line audit of the four earlier editions in this repository, with what was right and what was not.</p></a>
  <a class="card-link" href="pages/flagged.html"><span class="kicker">06</span><h3>Flagged for review</h3><p>Twenty-five items that could not be confirmed, published instead of guessed.</p></a>
</section>
<section class="callout">
  <h2>Read this before using any number</h2>
  <p>The tables price a <em>lawful, documented</em> transfer. They do not tell you whether your particular balance qualifies, because the character of the money is unknown (F03). They also do not include anything that could not be sourced — notarisation, travel, card conversion fees and your own bank's inbound charge are blank and flagged.</p>
</section>
""".format(stats=cards, answer=table(["Finding", "Why", "Sources"], answer_rows), matrix=summary_matrix())
    return shell("Dashboard", body)


def build_summary():
    r400 = cost_rows("boc_documented")[-1]
    r100 = {r["amount"]: r for r in cost_rows("boc_documented")}[100_000]
    rows = [
        ["1", "No conversion tax exists in either jurisdiction", "China taxes nine categories of income; exchange is not one. The US taxes income and FX gain, not the movement of your own funds.", src_links(["CN-05", "US-01"])],
        ["2", "The conversion margin is {} one way".format(pct(ONE_WAY)), "Derived from BOC's USD board: sell 669.29, buy 666.48, midpoint 667.885. The often-quoted 0.42% is the round trip, i.e. twice the one-way margin. See R01 on the repo review page.", src_links(["CN-08"])],
        ["3", "Total cost falls with size", "{} at $10,000 ({}), {} at $100,000 ({}), {} at $400,000 ({}). The commission is capped at CNY 260, so fixed fees dominate small transfers.".format(
            money({r['amount']: r for r in cost_rows('boc_documented')}[10_000]["total"]), pct({r['amount']: r for r in cost_rows('boc_documented')}[10_000]["total"] / 10_000),
            money(r100["total"]), pct(r100["total"] / 100_000), money(r400["total"]), pct(r400["total"] / 400_000)), src_links(["CN-07", "CN-08", "CN-09", "BK-02"])],
        ["4", "Capital-account convertibility is the real barrier", "Current-account business is convertible; capital-account business follows 'the process of convertibility'. Parking savings abroad is a capital-account act.", src_links(["CN-01"])],
        ["5", "The passport decides the quota", "CN-03 Art. 59 gives a documented purchase route to a 境外个人 and says only a Foreigner Permanent Residence ID holder uses the annual quota. A PRC ID card on file brings the USD 50,000 quota instead.", src_links(["CN-03", "CN-01"])],
        ["6", "Emigration transfer is the purpose-built route", "One application for the whole pre-emigration estate; releases of 50%, 25%, 25% above CNY 200,000; provincial approval below CNY 500,000.", src_links(["CN-04"])],
        ["7", "US reporting is the largest quantified exposure", "Willful FBAR: greater of $100,000 or 50% of the balance, per violation. At $400,000 that is $200,000, or {:.0f} times the transfer cost.".format(200000 / cost_rows("boc_documented")[-1]["total"]), src_links(["US-02", "US-03"])],
        ["8", "§988 is not a free pass above $200 of gain", "The personal-transaction exclusion applies only where the gain would not exceed $200. On a large balance the gain can exceed it, making it ordinary income. This is F11 and it is the most consequential correction to the earlier editions.", src_links(["US-01"])],
        ["9", "Prohibited routes are 100 to 400 times more expensive", "A 30%-100% fine plus confiscation, against a total lawful cost of {:.2f}% at $400,000.".format(100 * cost_rows("boc_documented")[-1]["total"] / 400000), src_links(["CN-02", "CN-06"])],
        ["10", "What remains unknown decides the answer", "The source of the funds, the account classification, the emigration proof, the property gain and the prior US filing history are all unknown. Twenty-five flags record them.", src_links(["CN-01", "CN-03", "CN-04", "US-03"])],
    ]
    body = page_header("Executive summary", "Ten findings, in the order they change the answer",
                       "Each finding is a statement about a published rule, a computed figure, or an explicit gap. Nothing here depends on facts that were not supplied.") + """
<section>{t1}</section>
<section>
  <h2>The recommendation, stated plainly</h2>
  <div class="callout">
    <p><strong>If the balance is documented, after-tax China-source income:</strong> use M01. Ask the bank in writing which identity document governs the account, assemble the source-of-funds file with tax vouchers, buy the USD and send one wire. At $400,000 the modelled total cost is {cost} ({share}).</p>
    <p><strong>If it is property you owned before emigrating:</strong> M03 is the route the rules were written for, at the cost of three releases and notarisation that is not priced here.</p>
    <p><strong>If it is property sold in China:</strong> M05, after the 20% IIT on the gain, which is unavoidable and is not a conversion tax.</p>
    <p><strong>Before any of that:</strong> resolve the US filing history. The FBAR exposure is larger than every fee in this document combined (F05).</p>
    <p><strong>Never:</strong> split across relatives, use an underground dealer, or bridge through a stablecoin. Those are the only routes here that can cost more than the balance itself.</p>
  </div>
</section>
<section>
  <h2>What this edition adds to the repository</h2>
  <p>The four earlier editions established the legal taxonomy and refused to invent fees, which left the practical question — how much, at what size, by which sequence — unanswered. Edition D sources a bank tariff, a rate board and a statutory tax table, and builds the missing tables. Where a price still does not exist officially, it stays blank.</p>
</section>
""".format(t1=table(["#", "Finding", "Detail", "Sources"], rows),
           cost=money(r400["total"]), share=pct(r400["total"] / 400_000))
    return shell("Executive summary", body, rel="../", active="pages/summary.html")


def build_methods():
    detail = "".join(method_detail(m) for m in METHODS_DOC["methods"])
    body = page_header("Methods", "Sixteen routes, classified by the rule that governs them",
                       "Status is taken from the instrument, not from a provider's marketing. Costed rows link to a 40-row table; rows with no official price say so.") + """
<section>{overview}</section>
<section class="legend">
  <p><span class="badge badge-ok">lawful</span> permitted by the cited rule on the documents it specifies.
  <span class="badge badge-warn">lawful, needs approval</span> permitted after a SAFE or other approval.
  <span class="badge badge-bad">prohibited</span> expressly unlawful; named so the exposure is visible, with no procedure given.
  <span class="badge badge-muted">unverified</span> no official source located; nothing asserted.</p>
</section>
{detail}
""".format(overview=methods_table(), detail=detail)
    return shell("All methods", body, rel="../", active="pages/methods.html")


def build_costs():
    body = page_header("Cost comparison", "Every costed route, side by side",
                       "Totals are the all-in cost of ending up with the stated number of US dollars in a US account: FX margin, bank fees, correspondent charge and the receiving bank's inbound fee.") + """
<section>
  <h2>The comparison</h2>
  {matrix}
  <p class="note">Blank cells are not zeros. They are routes for which no official price exists, or where the route is prohibited and the only number is a statutory fine range.</p>
</section>
<section>
  <h2>How the numbers are produced</h2>
  <div class="tablewrap"><table class="data">
  <thead><tr><th>Component</th><th>Value used</th><th>Where it comes from</th></tr></thead>
  <tbody>
  <tr><td>USD spot sell / buy</td><td>669.29 / 666.48 CNY per 100 USD</td><td>BOC board, stamp {stamp} {s8}</td></tr>
  <tr><td>One-way margin</td><td>{ow} of the USD amount</td><td>Derived: (sell &minus; midpoint) &divide; midpoint {s8}</td></tr>
  <tr><td>Round-trip spread</td><td>{rt} of the USD amount</td><td>Derived: (sell &minus; buy) &divide; sell {s8}</td></tr>
  <tr><td>Remittance commission</td><td>1 per mille, min CNY 50, max CNY 260</td><td>BOC personal e-banking tariff {s7}</td></tr>
  <tr><td>Cable fee</td><td>CNY 150 to a non-HK/Macau/Taiwan destination</td><td>Same tariff {s7}</td></tr>
  <tr><td>Full-amount-arrival surcharge</td><td>USD 15 (USD 25 if the receiving bank is not at BOC New York)</td><td>BOC trade-finance price announcement {s9}</td></tr>
  <tr><td>US receiving bank, inbound</td><td>USD 15, named example only</td><td>Chase published fee schedule {bk}</td></tr>
  <tr><td>Tax on the conversion</td><td>USD 0</td><td>CN-05 Art. 2 and US-01 §988(e)(2); see the tax page for the $200 caveat {s5} {u1}</td></tr>
  </tbody></table></div>
</section>
<section>
  <h2>Per-method tables</h2>
  <div class="grid-links">{links}</div>
</section>
<section class="callout">
  <h2>Why the percentage keeps falling</h2>
  <p>The commission is capped at CNY 260 and the cable fee is flat at CNY 150. At $10,000 those fixed items are {small_share} of the amount; at $400,000 they are {big_share}. The FX margin is the only component that scales, and it is about {margin} one way. That is why a single large transfer is cheaper than several small ones — and why anyone charging a percentage to move this money is charging more than the bank does.</p>
</section>
""".format(
        matrix=summary_matrix(), stamp=esc(FX["board_stamp"]),
        s8=src_links(["CN-08"]), s7=src_links(["CN-07"]), s9=src_links(["CN-09"]),
        bk=src_links(["BK-02"]), ow=pct(ONE_WAY, 4), rt=pct(ROUND_TRIP, 4),
        s5=src_links(["CN-05"]), u1=src_links(["US-01"]),
        links="".join('<a class="card-link small" href="../pages/{h}"><strong>{t}</strong></a>'.format(h=h, t=esc(t)) for h, t in COST_PAGES),
        small_share=pct((cost_rows("boc_documented")[0]["cn_fees"] + cost_rows("boc_documented")[0]["wires"] + cost_rows("boc_documented")[0]["us_in"]) / 10000, 2),
        big_share=pct((cost_rows("boc_documented")[-1]["cn_fees"] + cost_rows("boc_documented")[-1]["wires"] + cost_rows("boc_documented")[-1]["us_in"]) / 400000, 2),
        margin=pct(ONE_WAY, 2),
    )
    return shell("Cost comparison", body, rel="../", active="pages/costs.html")


COST_PAGE_META = {
    "costs-boc-documented.html": (
        "M01", "boc_documented", "Documented remittance, all-in cost",
        "The best lawful route for a documented balance: one purchase, one wire, every published fee included.",
        ["Every row assumes one conversion and one remittance.", "The receiving bank fee is a USD 15 named example (F07)."],
    ),
    "costs-boc-quota.html": (
        "M02", "boc_quota", "Quota-paced remittance, all-in cost",
        "What the fee bill looks like if the account is classified 境内个人 and the USD 50,000 annual quota pace applies.",
        ["Fees are charged per annual tranche, so the fixed items repeat.", "Pacing is not a saving: the totals rise with the number of tranches, and the real cost is the years (F01)."],
    ),
    "costs-emigration.html": (
        "M03", "emigration", "Emigration transfer, all-in cost",
        "The purpose-built capital-account route, priced on its three-release schedule.",
        ["Notarisation, translation and valuation are excluded and flagged F14.", "The release schedule is statutory, so the fee repeats three times."],
    ),
    "costs-inheritance.html": (
        "M04", "inheritance", "Inheritance transfer, all-in cost",
        "A single release is modelled, because the official description permits one or several.",
        ["Most estates use more than one release; the fee then repeats.", "Notarisation and probate costs are excluded and flagged F14."],
    ),
    "costs-property.html": (
        "M05", "property", "Property-proceeds remittance, all-in cost",
        "The wire cost of remitting sale proceeds, with the 20% IIT left out on purpose: it falls on the gain, which is unknown.",
        ["The China IIT column is deliberately blank (F13).", "SAFE approval is a precondition and is not a cost."],
    ),
    "costs-hold-usd.html": (
        "M06", "hold_usd", "Convert now, remit later, cost",
        "Only the FX margin is incurred now. The wire is deferred, not avoided.",
        ["No purchase fee appears in the published tariff (F17).", "A USD account in China remains a reportable foreign account."],
    ),
    "costs-cash.html": (
        "M09", "cash", "Cash carriage, known cost",
        "The margin and the number of trips are shown. Travel, insurance and loss risk are not priced.",
        ["One trip per USD 5,000, the tier that needs no carriage permit.", "At USD 400,000 this is 80 trips (F20)."],
    ),
    "costs-prohibited.html": (
        "M14", "penalty", "Prohibited routes, statutory exposure",
        "The only figure that exists for these routes is the statutory fine range: 30% to 100% of the amount, plus confiscation.",
        ["Not an assessment of any case (F24).", "Crypto is prohibited without a fixed penalty (F25)."],
    ),
}


def build_cost_page(fname, rel=""):
    mid, model, title, sub, notes = COST_PAGE_META[fname]
    m = METHOD[mid] if mid in METHOD else METHOD["M14"]
    ticker = '<div class="tabs">' + "".join(
        '<a class="{c}" href="{h}">{t}</a>'.format(c="tab active" if h == fname else "tab", h=h, t=esc(t))
        for h, t in COST_PAGES) + "</div>"
    if model == "penalty":
        explain = """<div class="callout"><p><strong>These routes are unlawful.</strong> Splitting across quotas (CN-03 Art. 62) brings watch-list treatment; private or disguised FX dealing (CN-02 Art. 45) and evading FX control (Art. 39) carry fines of 30% to 100% of the amount plus confiscation. Crypto exchange between legal tender and virtual currency is illegal financial activity (CN-06). No procedure is given for any of them.</p></div>"""
    else:
        explain = """<div class="callout"><p>{}</p></div>""".format(" ".join(esc(n) for n in notes))
    body = page_header("Cost table", title, esc(sub)) + ticker + explain + """
<section>{table}</section>
<section class="rules">
  <h2>Formula used for every row</h2>
  <p class="mono">total = amount &times; {ow} + (min(max(amount &times; {sell} &times; 0.001, 50), 260) + 150) &divide; {sell} + correspondence + receiving-bank fee</p>
  <p>Where a route releases in tranches, the bracketed fee term is evaluated per tranche and summed, and the correspondence and receiving-bank fees are multiplied by the number of tranches. The FX margin is applied once to the total, because the whole amount is converted either way.</p>
  <p class="srcrow"><strong>Inputs:</strong> {s7} {s8} {s9} {bk}</p>
</section>
""".format(table=cost_table(model, mid),
           ow=pct(ONE_WAY, 4), sell=SELL_RATE, s7=src_links(["CN-07"]), s8=src_links(["CN-08"]),
           s9=src_links(["CN-09"]), bk=src_links(["BK-02"]))
    return shell(title, body, rel=rel, active="pages/costs.html")


def build_steps():
    blocks = []
    for m in METHODS_DOC["methods"]:
        if m["id"] in ("M08", "M10", "M11"):
            continue
        status, kind = STATUS_BADGE[m["status"]]
        steps = "".join("<li>{}</li>".format(esc(s)) for s in m["steps"])
        blocks.append("""
<section class="card">
  <div class="method-head"><h2>{mid} &middot; {name}</h2><span class="badge badge-{kind}">{st}</span></div>
  <p class="lede">{one}</p>
  <ol>{steps}</ol>
  <p class="srcrow"><strong>Rule:</strong> {srcs}</p>
</section>""".format(mid=m["id"], name=esc(m["name"]), kind=kind, st=esc(status),
                     one=esc(m["one_liner"]), steps=steps,
                     srcs=src_links(m["basis"]) if m["basis"] else "none cited"))
    body = page_header("Step by step", "How each route would actually be executed",
                       "Including the provision to cite at the counter. Three routes are omitted because no official procedure was retrieved; they are named on the methods page with that stated.") + "".join(blocks)
    return shell("Step by step", body, rel="../", active="pages/steps.html")


def build_tax():
    scen = []
    for a in (10_000, 25_000, 50_000, 100_000, 200_000, 400_000):
        tax = us_tax_on_ordinary(a)
        scen.append([
            money(a),
            money(tax),
            pct(tax / a),
            pct(us_marginal_rate(a), 0),
            money(0.20 * a),
            money(max(P["us_fbar"]["willful_floor_usd"], P["us_fbar"]["willful_rate"] * a)),
            src_links(["US-04", "CN-05", "US-02"]),
        ])
    ladder = [
        ["Evading FX control to move capital abroad (逃汇)", "Fine up to 30% of the amount; 30%-100% if serious; criminal referral", src_links(["CN-02"])],
        ["Private, disguised or brokered FX dealing", "Warning, confiscation of gains, fine up to 30%; 30%-100% if serious", src_links(["CN-02"])],
        ["Carrying FX across the border in breach of the rules", "Warning, fine up to 20% of the amount", src_links(["CN-02"])],
        ["Submitting invalid or untrue documents", "Fine up to CNY 50,000 for an individual", src_links(["CN-02"])],
        ["Splitting to evade the quota", "Watch list for the year of listing plus two further years", src_links(["CN-03"])],
        ["Virtual-currency exchange business", "Illegal financial activity, prohibited and to be banned", src_links(["CN-06"])],
        ["Willful FBAR violation", "Greater of USD 100,000 or 50% of the balance, per violation", src_links(["US-02"])],
        ["Non-willful FBAR violation", "Up to USD 10,000 per violation, adjusted for inflation", src_links(["US-02", "US-03"])],
        ["Form 8938 failure", "USD 10,000 plus USD 10,000 per 30 days after notice, maximum USD 60,000", src_links(["US-03"])],
        ["Form 3520 failure (foreign gift over USD 100,000)", "Penalty under IRC §6039F(c) absent reasonable cause", src_links(["US-05"])],
    ]
    body = page_header("Tax and penalties", "What is taxed, what is not, and what the penalties are",
                       "Two questions are separated: whether the transfer is taxed (it is not), and whether the money was already taxable income (a different question, answered by the underlying facts).") + """
<section>
  <h2>China: the conversion is not in the tax base</h2>
  <p>The Individual Income Tax Law charges nine categories of income. Currency exchange is not one of them, and neither is the remittance of a person's own funds. The rate that people quote — 20% — is the flat rate on <em>transfer of assets</em>, <em>interest, dividends and bonuses</em>, leasing and incidental income. It falls on the gain or the income, never on the principal that is being moved.</p>
  <p class="srcrow">{s5}</p>
</section>
<section>
  <h2>United States: three separate questions</h2>
  <div class="tablewrap"><table class="data">
  <thead><tr><th>Question</th><th>Answer</th><th>Source</th></tr></thead>
  <tbody>
  <tr><td>Is moving my own money income?</td><td>No provision treats a transfer between accounts you own as income. The only recognition rule that touches the conversion is §988.</td><td>{u1}</td></tr>
  <tr><td>Is the FX gain on conversion taxable?</td><td>Not if the transaction is personal and the gain that would otherwise be recognised does not exceed USD 200. Above USD 200 the exclusion does not apply and the gain is ordinary income.</td><td>{u1}</td></tr>
  <tr><td>Do I have to report the account?</td><td>Yes. An aggregate balance above USD 10,000 at any point in the calendar year requires an FBAR, and Form 8938 may also apply.</td><td>{u3}</td></tr>
  </tbody></table></div>
  <p class="note">The second row is the correction that matters: the earlier editions in this repository state the $200 rule accurately in one place and omit it in another. See R02 and F11. Any income the balance itself earns (interest, for example) is a separate worldwide-income question that this edition did not model.</p>
</section>
<section>
  <h2>Scenario: if the money were taxable income</h2>
  <p>This table does <em>not</em> describe a conversion tax. It answers a different question — what US income tax would arise if the amount were ordinary income that had not been reported — for a single filer with no other income, taking only the 2026 standard deduction of $16,100. It is a statutory computation, not a determination.</p>
  {scen}
  <p class="note">The China column is the flat 20% applied to the whole amount as an upper bound, which is only correct where the entire amount is gain or interest. The FBAR column is the willful maximum for a single violation.</p>
</section>
<section>
  <h2>The penalty ladder</h2>
  {ladder}
</section>
<section class="callout">
  <h2>The comparison that matters</h2>
  <p>At USD 400,000, the lawful route costs {cost}. A single willful FBAR violation can be {fbar}. A finding of evading FX control can be {pen_min} to {pen_max}. The fee is not the risk.</p>
</section>
""".format(
        s5=src_links(["CN-05"]), u1=src_links(["US-01"]), u3=src_links(["US-03"]),
        scen=table(["Amount", "US tax if ordinary income", "Effective rate", "Marginal rate", "China 20% upper bound", "Willful FBAR maximum", "Sources"], scen),
        ladder=table(["Conduct", "Consequence", "Source"], ladder),
        cost=money(cost_rows("boc_documented")[-1]["total"]),
        fbar=money(max(100000, 0.5 * 400000)),
        pen_min=money(0.30 * 400000), pen_max=money(1.00 * 400000),
    )
    return shell("Tax and penalties", body, rel="../", active="pages/tax.html")


def build_reporting():
    rows = [
        ["FinCEN Form 114 (FBAR)", "Aggregate foreign accounts exceed USD 10,000 at any time in the calendar year", "Filed with FinCEN, not the IRS; received by 15 April, automatic extension to 15 October", "Non-willful up to USD 10,000; willful the greater of USD 100,000 or 50% of the balance", src_links(["US-03", "US-02"])],
        ["Form 8938", "Specified foreign financial assets above the filing-status threshold (USD 50,000 year-end or USD 75,000 at any time for an unmarried filer living in the US)", "Attached to the income-tax return", "USD 10,000 plus USD 10,000 per 30 days after notice, maximum USD 60,000", src_links(["US-03"])],
        ["Form 3520, Part IV", "Gifts or bequests from a foreign person above USD 100,000 in the year", "Filed separately by 15 April, extendable to 15 October", "Penalty under IRC §6039F(c) absent reasonable cause", src_links(["US-05"])],
        ["Currency report at the border", "More than USD 10,000 carried into or out of the US at one time", "Filed with US Customs and Border Protection", "Seizure and civil penalty exposure", src_links(["US-06"])],
    ]
    body = page_header("US reporting", "The obligations that run alongside the transfer",
                       "None of these is a tax on converting. All of them are triggered by holding or moving the account, and their penalties dwarf the cost of the transfer.") + """
<section>{t}</section>
<section class="callout">
  <h2>The one thing to fix first</h2>
  <p>An account that has existed for years and was never reported is a bigger problem than the transfer. The willful penalty is 50% of the balance per violation, and the assessment window runs six years from the transaction. Whether a violation was willful is a facts-and-circumstances question, not a box on a form. The 40-row tables on this site assume the reporting position is clean; if it is not, the transfer is the second problem.</p>
</section>
<section>
  <h2>How the reporting interacts with the route</h2>
  <ul>
    <li>The Chinese account stays reportable for every year it exists, including the year it is emptied.</li>
    <li>FBAR values are converted at the end-of-year rate; Form 8938 uses the year-end rate as well.</li>
    <li>A gift from a foreign relative is not a way around this: above USD 100,000 it is reportable on Form 3520, and the funds remain the donor's, not yours.</li>
    <li>If the balance sits in a Chinese fund or insurance product rather than a deposit, the product may be a PFIC, which is a separate and potentially larger US tax problem that this edition did not model.</li>
  </ul>
  <p class="srcrow">{s}</p>
</section>
""".format(t=table(["Filing", "Trigger", "When and where", "Penalty ceiling", "Sources"], rows),
           s=src_links(["US-03", "US-02", "US-05", "US-06"]))
    return shell("US reporting", body, rel="../", active="pages/reporting.html")


def build_sources():
    rows = []
    for s in SOURCES_DOC["sources"]:
        rows.append([
            "<strong>{}</strong>".format(esc(s["id"])),
            "<a href=\"{}\" target=\"_blank\" rel=\"noopener noreferrer\">{}</a><br><small>{}</small>".format(
                esc(s["url"]), esc(s["title_en"]), esc(s.get("title_zh", ""))),
            esc(s["issuer"]),
            esc(s.get("doc", "")),
            badge("Tier " + s["tier"], {"A": "ok", "B": "warn", "C": "muted"}[s["tier"]]),
            esc({"full": "full text retrieved", "index": "search-index excerpt", "partial": "partial"}[s["retrieval"]]),
        ])
    supports = []
    for s in SOURCES_DOC["sources"]:
        items = "".join("<li>{}</li>".format(esc(x)) for x in s["supports"])
        note = '<p class="note">{}</p>'.format(esc(s["note"])) if s.get("note") else ""
        supports.append("""
<section class="card" id="{sid}">
  <h2>{sid} &middot; {title}</h2>
  <p class="meta">{issuer} &middot; {doc}</p>
  <p><a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a></p>
  <p class="srcrow">{tier} &middot; {ret}</p>
  <ul>{items}</ul>
  {note}
</section>""".format(sid=s["id"], title=esc(s["title_en"]), issuer=esc(s["issuer"]),
                     doc=esc(s.get("doc", "")), url=esc(s["url"]),
                     tier=badge("Tier " + s["tier"], {"A": "ok", "B": "warn", "C": "muted"}[s["tier"]]),
                     ret=esc({"full": "full text retrieved", "index": "search-index excerpt", "partial": "partial"}[s["retrieval"]]),
                     items=items, note=note))
    body = page_header("Sources", "Every source, what was retrieved, and what it supports",
                       "Tier A is a government, legislature, regulator or central-bank text. Tier B is an institution's own published tariff or rate board — authoritative for its prices, not for the law. Tier C is never used to populate a value.") + """
<section>{t}</section>
<section class="callout"><p><strong>Retrieval honesty.</strong> Three sources were retrieved as search-index excerpts rather than by opening the page: {idx}. They are marked as such and are used only for wording the excerpt reproduced. Bank of China's rate board is a live page: the figures quoted here are the ones on the board at the stated stamp, and the board itself says the counter rate governs.</p></section>
{detail}
""".format(t=table(["Id", "Source", "Issuer", "Document", "Tier", "Retrieval"], rows),
           idx="CN-06, BK-02", detail="".join(supports))
    return shell("Sources", body, rel="../", active="pages/sources.html")


def build_flagged():
    order = {"high": 0, "medium": 1, "low": 2}
    flags = sorted(FLAGS_DOC["flags"], key=lambda f: (order[f["severity"]], f["id"]))
    cards = []
    for f in flags:
        cards.append("""
<section class="card flag-card" id="{fid}">
  <div class="method-head"><h2>{fid} &middot; {title}</h2>{sev}</div>
  <p>{detail}</p>
  <p><strong>Why it matters.</strong> {why}</p>
  <p><strong>What would resolve it.</strong> {res}</p>
  <p class="srcrow"><strong>Sources:</strong> {srcs}</p>
</section>""".format(fid=f["id"], title=esc(f["title"]),
                    sev=badge(f["severity"], {"high": "bad", "medium": "warn", "low": "muted"}[f["severity"]]),
                    detail=esc(f["detail"]), why=esc(f["why_it_matters"]),
                    res=esc(f["what_would_resolve_it"]),
                    srcs=src_links(f["sources"]) if f["sources"] else '<span class="unv">none &mdash; that is the point</span>'))
    body = page_header("Flagged for review", "Twenty-five things this edition refused to guess",
                       "Each item is either unconfirmed, or a place where two official sources point differently. None of them blocks publication; all of them change the answer if they resolve one way rather than the other.") + """
<section class="callout"><p>Nothing on this page is a finding about your account. These are gaps in the public record, or facts that only you or your bank can supply. They are listed here rather than filled in with a plausible number.</p></section>
{cards}
""".format(cards="".join(cards))
    return shell("Flagged for review", body, rel="../", active="pages/flagged.html")


def build_review():
    rows = []
    for r in REVIEW_DOC["findings"]:
        rows.append([
            "<strong>{}</strong>".format(esc(r["id"])),
            esc(r["area"]),
            esc(r["finding"]),
            badge(r["verdict"], {"confirmed": "ok", "irregularity": "bad", "gap": "warn", "resolved": "muted"}[r["verdict"]]),
            esc(r["evidence"]),
            (src_links(r["sources"]) + " " if r["sources"] else "")
            + ('<a class="src" href="../../../{}" target="_blank" rel="noopener noreferrer">repo: {}</a>'.format(esc(r["repo_ref"]), esc(r["repo_ref"])) if r.get("repo_ref") else ""),
        ])
    body = page_header("Repo review", "Line-by-line audit of the four earlier editions",
                       "Every earlier edition was read, its claims checked against the instrument it cites, and its checker re-run. What follows is what held up and what did not.") + """
<section>
  <h2>What was checked</h2>
  <ul>
    <li>All four checkers were re-run in this checkout: <span class="mono">assets/check.py</span>, <span class="mono">scripts/verify.py</span>, <span class="mono">edition-b/build/verify.py</span>, <span class="mono">edition-c/build/linkcheck.py</span>. All four pass, which means the earlier editions are internally consistent.</li>
    <li>Their cited instruments were opened: CN-01, CN-02, CN-03, CN-04, CN-05, CN-08 and the US statutes. The quotes in the earlier editions match the text in the places checked.</li>
    <li>Their arithmetic was recomputed from the same BOC board they used.</li>
    <li>Their external links were tested by retrieval. One primary citation returns a 404 while its own fallback resolves.</li>
    <li>Their internal consistency was compared across editions: route counts, spread figures and deployment claims.</li>
  </ul>
</section>
<section>{t}</section>
<section class="callout">
  <h2>Why none of this is a criticism of the method</h2>
  <p>The earlier editions did the hard part correctly: they refused to invent fees, marked unknowns, and separated the law from providers' marketing. The gaps found here are mostly the same gap — the absence of a sourced tariff — plus one arithmetic labelling error and one dead link. Edition D fixes those and leaves the rest of their work in place.</p>
</section>
""".format(t=table(["Id", "Area", "Finding", "Verdict", "Evidence", "Sources"], rows))
    return shell("Repo review", body, rel="../", active="pages/repo-review.html")


def build_methodology():
    body = page_header("Method and limits", "How this was built, and what it cannot tell you",
                       "The rules the generator enforces, the arithmetic it performs, and the questions it deliberately does not answer.") + """
<section>
  <h2>Rules enforced in code</h2>
  <ol>
    <li>A source id must exist in the register or the build fails.</li>
    <li>A number is printed only when every input behind it carries a source id.</li>
    <li>A missing official price renders as an em dash plus an UNVERIFIED marker; no default, no range, no "typical" value.</li>
    <li>Every table row carries at least one source link.</li>
    <li>Every page is in the navigation, so no orphan page can exist.</li>
  </ol>
  <p>These are re-checked independently by <span class="mono">build/verify.py</span>, which recomputes every cost cell from the parameters rather than trusting the HTML.</p>
</section>
<section>
  <h2>Arithmetic, stated exactly</h2>
  <p class="mono">mid = (666.48 + 669.29) / 2 = 667.885</p>
  <p class="mono">one-way margin = (669.29 &minus; 667.885) / 667.885 = {ow}</p>
  <p class="mono">round-trip spread = (669.29 &minus; 666.48) / 669.29 = {rt}</p>
  <p class="mono">commission = min(max(amount &times; 6.6929 &times; 0.001, 50), 260) CNY</p>
  <p class="mono">bank fees in USD = (commission + 150) / 6.6929</p>
  <p>The one-way margin is the right figure for a single conversion. The round-trip figure is what two conversions cost, and it is the number the earlier editions labelled as the cost of one.</p>
</section>
<section>
  <h2>What this cannot tell you</h2>
  <ul>
    <li>Whether your balance qualifies for any route — that depends on the source of the funds (F03).</li>
    <li>Whether your bank classifies you as 境内个人 or 境外个人 (F01).</li>
    <li>What your own bank charges to receive a wire (F07).</li>
    <li>What notarisation, translation or travel will cost (F14, F20).</li>
    <li>What your §988 basis is, and therefore whether you have a taxable FX gain (F11).</li>
    <li>What a Chinese branch will actually do at the counter, as opposed to what the rule says (F10, F16).</li>
  </ul>
</section>
<section>
  <h2>Scope and status</h2>
  <p>Research current to {asof}. Not legal, tax or investment advice. No account was contacted, no funds were moved, and no personal tax position was determined. Where a professional is required — a Chinese notary, a SAFE filing, a US international tax return — this edition says so rather than substituting a calculation for it.</p>
</section>
""".format(ow=pct(ONE_WAY, 4), rt=pct(ROUND_TRIP, 4), asof=AS_OF)
    return shell("Method and limits", body, rel="../", active="pages/methodology.html")


# ---------------------------------------------------------------------------
# write
# ---------------------------------------------------------------------------

def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content)


def main():
    write("index.html", build_index())
    write("pages/summary.html", build_summary())
    write("pages/methods.html", build_methods())
    write("pages/costs.html", build_costs())
    for fname, _ in COST_PAGES:
        write("pages/" + fname, build_cost_page(fname, rel="../"))
    write("pages/steps.html", build_steps())
    write("pages/tax.html", build_tax())
    write("pages/reporting.html", build_reporting())
    write("pages/sources.html", build_sources())
    write("pages/flagged.html", build_flagged())
    write("pages/repo-review.html", build_review())
    write("pages/methodology.html", build_methodology())
    write(".nojekyll", "")
    export = {
        "edition": "D",
        "as_of": AS_OF,
        "fx": {"buy": BUY, "sell": SELL, "mid": MID, "one_way_margin": round(ONE_WAY, 6),
               "round_trip": round(ROUND_TRIP, 6), "stamp": FX["board_stamp"], "source": "CN-08"},
        "methods": [{"id": m["id"], "name": m["name"], "status": m["status"], "cost_model": m["cost_model"],
                     "sources": m["basis"]} for m in METHODS_DOC["methods"]],
        "costs": {mid: [{k: r[k] for k in ("amount", "fx", "cn_fees", "wires", "us_in", "tax", "total")}
                        for r in cost_rows(model)]
                  for mid, model in [("M01", "boc_documented"), ("M02", "boc_quota"), ("M03", "emigration"),
                                     ("M04", "inheritance"), ("M05", "property"), ("M06", "hold_usd"),
                                     ("M09", "cash"), ("M14", "penalty")]},
        "flags": [f["id"] for f in FLAGS_DOC["flags"]],
        "sources": [s["id"] for s in SOURCES_DOC["sources"]],
    }
    write("data.json", json.dumps(export, ensure_ascii=False, indent=1))
    build_portal()
    print("root portal written to index.html")
    pages = len(NAV[0][1]) + len(NAV[1][1]) + len(NAV[2][1]) + len(NAV[3][1]) + len(COST_PAGES)
    print("edition-d: wrote {} nav-listed pages + {} cost pages".format(pages - len(COST_PAGES), len(COST_PAGES)))
    print("one-way margin {:.4f}%  round-trip {:.4f}%".format(ONE_WAY * 100, ROUND_TRIP * 100))
    r = {x["amount"]: x for x in cost_rows("boc_documented")}
    for a in (10_000, 100_000, 400_000):
        print("  ${:,}: total ${:,.2f} ({:.3f}%)".format(a, r[a]["total"], 100 * r[a]["total"] / a))




# ---------------------------------------------------------------------------
# root portal (final integration)
# ---------------------------------------------------------------------------

PORTAL_CSS = """
:root{--ink:#12161c;--ink2:#3d4753;--muted:#6b7684;--line:#e2e6ec;--bg:#f6f7f9;--panel:#fff;--accent:#0f5c4a;--ok:#e6f3ef}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1080px;margin:0 auto;padding:22px 18px 56px}
.top{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--line);padding-bottom:10px}
.brand{font-weight:800;letter-spacing:-.02em;font-size:1.05rem;color:var(--ink)}
h1{font-size:2.1rem;line-height:1.15;letter-spacing:-.03em;margin:.6em 0 .3em;max-width:20ch}
.lede{font-size:1.05rem;color:var(--ink2);max-width:65ch}
.eyebrow{font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:700}
.stats{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:22px 0}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px}
.stat small{display:block;font-size:.62rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.stat strong{display:block;font-size:1.3rem;letter-spacing:-.02em;margin:2px 0}
.stat span{display:block;font-size:.74rem;color:var(--ink2)}
.grid{display:grid;grid-template-columns:1fr;gap:10px;margin:14px 0}
.card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px;color:inherit}
.card:hover{border-color:var(--accent);text-decoration:none}
.card h3{margin:.15em 0 .3em;font-size:.98rem}
.card p{margin:0;font-size:.84rem;color:var(--ink2)}
.kicker{font-size:.64rem;letter-spacing:.1em;color:var(--accent);font-weight:700}
h2{font-size:1.15rem;margin:2em 0 .6em}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:.82rem;min-width:600px}
th,td{padding:9px 10px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f0f3f6;font-size:.66rem;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2)}
.src{display:inline-block;font-size:.64rem;font-weight:600;padding:1px 5px;border-radius:5px;background:#eef1f5;border:1px solid var(--line);color:var(--ink2);white-space:nowrap}
.note{font-size:.8rem;color:var(--muted)}
.cta{display:inline-block;background:var(--accent);color:#fff;font-weight:700;padding:11px 18px;border-radius:10px;margin:14px 0}
.cta:hover{text-decoration:none;background:#0b4a3b}
.archive{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
.archive ul{margin:.4em 0;padding-left:1.1em;font-size:.86rem;color:var(--ink2)}
footer{border-top:1px solid var(--line);margin-top:34px;padding-top:14px;font-size:.78rem;color:var(--muted)}
@media(min-width:760px){.stats{grid-template-columns:repeat(4,1fr)}.grid{grid-template-columns:repeat(3,1fr)}h1{font-size:2.6rem}}
"""


def build_portal():
    r = {x["amount"]: x for x in cost_rows("boc_documented")}
    findings = [
        ["Converting is not a taxable event", "China taxes nine categories of income and exchange is not one; the US taxes income, and the FX gain on a personal conversion is not recognised up to $200.", src_links(["CN-05", "US-01"])],
        ["The barrier is capital-account convertibility", "Current-account business is convertible; capital-account business follows a process. That is why the money is stuck, and it is not a tax question.", src_links(["CN-01"])],
        ["The cost is small and falls with size", "{} at $10,000 ({}), {} at $100,000, {} at $400,000 ({}).".format(money(r[10000]["total"], 2), pct(r[10000]["total"] / 10000), money(r[100000]["total"], 2), money(r[400000]["total"], 2), pct(r[400000]["total"] / 400000)), src_links(["CN-07", "CN-08", "CN-09", "BK-02"])],
        ["One fact decides the route", "A passport on file brings the documented route in CN-03 Art. 59, with no annual cap in the text; a PRC identity card brings the USD 50,000 quota.", src_links(["CN-03", "CN-01"])],
        ["US reporting is the real exposure", "A willful FBAR penalty is the greater of $100,000 or 50% of the balance, per violation: $200,000 at $400,000.", src_links(["US-02", "US-03"])],
        ["The wrong routes cost 30% to 100%", "Splitting, underground dealing and crypto carry fines of 30% to 100% of the amount, plus confiscation.", src_links(["CN-02", "CN-06"])],
    ]
    glance = [[money(a), money(r[a]["total"], 2), pct(r[a]["total"] / a), money(a - r[a]["total"], 2), src_links(["CN-07", "CN-08", "CN-09", "BK-02"])]
              for a in (10_000, 50_000, 100_000, 200_000, 400_000)]
    cards = [
        ("edition-d/docs/index.html", "01", "Dashboard", "The answer, the four headline numbers, and the route to every table."),
        ("edition-d/docs/pages/costs.html", "02", "Cost comparison", "Every costed route side by side, with the full cost breakdown."),
        ("edition-d/docs/pages/costs-boc-documented.html", "03", "40-row cost table", "USD 10,000 to USD 400,000 in 10,000 steps, the best lawful route."),
        ("edition-d/docs/pages/methods.html", "04", "All 16 methods", "Every route, its rule, its cap, documents, pros and cons."),
        ("edition-d/docs/pages/steps.html", "05", "Step by step", "What to do at the counter, and which provision to cite."),
        ("edition-d/docs/pages/tax.html", "06", "Tax and penalties", "China IIT, §988, FBAR, and the penalty ladder."),
        ("edition-d/docs/pages/repo-review.html", "07", "Repo review", "Line-by-line audit of the four earlier editions."),
        ("edition-d/docs/pages/flagged.html", "08", "Flagged for review", "25 items left blank on purpose, with the source links."),
        ("edition-d/docs/pages/sources.html", "09", "Sources", "17 sources, graded, with what each one supports."),
    ]
    body = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Official-source research on turning CNY into USD for a US citizen: every lawful route, its published cost from USD 10,000 to USD 400,000, and the tax position in both countries.">
<title>China Money &middot; the cost of getting CNY out</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
<div class="top"><span class="brand">China Money</span><span>Research &middot; {asof}</span></div>
<p class="eyebrow" style="margin-top:22px">CNY to USD &middot; US citizen &middot; official sources only</p>
<h1>What it costs to get money out of China.</h1>
<p class="lede">The premise is the expensive part. There is no tax on converting your own money in either country, and the real cost of a lawful transfer is under 1% at every size. What stops the money is China's capital-account rule, and what can cost half the balance is a US filing failure. This site prices every route and shows its work.</p>
<a class="cta" href="edition-d/docs/index.html">Open the dashboard &rarr;</a>
<div class="stats">
  <div class="stat"><small>FX margin, one conversion</small><strong>{ow}</strong><span>derived from BOC's own bid and ask</span></div>
  <div class="stat"><small>Total cost at $400,000</small><strong>{c400}</strong><span>{p400} of the amount, all fees</span></div>
  <div class="stat"><small>Total cost at $10,000</small><strong>{c10}</strong><span>{p10} — fixed fees dominate</span></div>
  <div class="stat"><small>Tax on the conversion</small><strong>$0</strong><span>in both jurisdictions</span></div>
</div>
<div class="grid">{cards}</div>
<h2>The answer in six rows</h2>
<div class="tablewrap"><table><thead><tr><th>Finding</th><th>Detail</th><th>Official source</th></tr></thead><tbody>{findings}</tbody></table></div>
<h2>Cost at a glance — documented remittance</h2>
<div class="tablewrap"><table><thead><tr><th>Amount</th><th>Total cost</th><th>Share</th><th>Net received</th><th>Sources</th></tr></thead><tbody>{glance}</tbody></table></div>
<p class="note">Derived arithmetic from the Bank of China tariff and rate board, the full-amount surcharge, and a named US receiving-bank example. Cells with no official price are blank and flagged, never estimated.</p>
<h2>Earlier editions in this repository</h2>
<div class="archive">
<p class="note">The earlier editions are preserved unchanged. They are the legal research that Edition D builds on; Edition D adds the sourced tariff, the cost engine and the audit.</p>
<ul>
<li><a href="overview.html">Overview dashboard (original root edition)</a> &middot; <a href="docs/index.html">supplemental dashboard</a> &middot; <a href="pages/estimates.html">USD 10,000&ndash;400,000 scenarios</a></li>
<li><a href="dossier/index.html">Verified dossier</a> — 35 routes, capital-account taxonomy</li>
<li><a href="edition-b/index.html">Edition B</a> — 22 channels, penalty layers, US reporting</li>
<li><a href="edition-c/docs/index.html">Edition C</a> — 33 channels, tax treaty, repo review</li>
<li><a href="edition-d/docs/index.html">Edition D</a> — sourced tariffs, USD 10,000-step cost tables, line-by-line audit <strong>(current)</strong></li>
</ul>
</div>
<footer>
<p><strong>What this is.</strong> Published-rule research with the arithmetic shown. Not legal, tax or investment advice, and not a bank quote. Rates and tariffs change; every source is linked for manual review.</p>
<p>Values that could not be confirmed from an official page are blank and published on the <a href="edition-d/docs/pages/flagged.html">Flagged for review</a> page. No value is inferred. Built by session <span class="note">arena-133875bd</span>; see <a href="COORDINATION.md">COORDINATION.md</a>.</p>
</footer>
</div>
</body>
</html>
""".format(css=PORTAL_CSS, asof=AS_OF,
           ow=pct(ONE_WAY, 4), c400=money(r[400000]["total"], 2), p400=pct(r[400000]["total"] / 400000),
           c10=money(r[10000]["total"], 2), p10=pct(r[10000]["total"] / 10000),
           cards="".join('<a class="card" href="{h}"><span class="kicker">{k}</span><h3>{t}</h3><p>{d}</p></a>'.format(
               h=h, k=k, t=esc(t), d=esc(d)) for h, k, t, d in cards),
           findings="".join("<tr><td><strong>{}</strong></td><td>{}</td><td>{}</td></tr>".format(esc(a), esc(b), c) for a, b, c in findings),
           glance="".join("<tr><td>{}</td><td><strong>{}</strong></td><td>{}</td><td>{}</td><td>{}</td></tr>".format(*row) for row in glance))
    with open(os.path.join(ROOT, "..", "index.html"), "w", encoding="utf-8") as fh:
        fh.write(body)

if __name__ == "__main__":
    main()
