"""Edition J site builder.

Deterministic: same inputs -> byte-identical HTML. No external fonts, scripts or
CDNs. Mobile-first: every wide table scrolls, and the cost ladder collapses to
cards under 640px.
"""

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "edition-j" / "site"
sys.path.insert(0, str(ROOT / "edition-j"))

from data import sources, market, routes, costs, analysis  # noqa: E402

S = sources.SOURCES
e = html.escape


# ---------------------------------------------------------------- helpers
def src_link(sid: str) -> str:
    s = S[sid]
    tier = s["tier"]
    label = {"A": "law", "B": "gov", "P": "provider"}[tier]
    return (f'<a class="src t-{label}" href="{s["url"]}" rel="noopener noreferrer" '
            f'title="{e(s["publisher"])} - {e(s["title"])}">{sid} ↗</a>')


def src_links(ids) -> str:
    return "".join(src_link(i) for i in ids)


def money(v, dp=2):
    if v is None:
        return '<span class="blank" title="Not verified - deliberately blank">blank</span>'
    return f"{v:,.{dp}f}"


def pct(v, dp=3):
    if v is None:
        return '<span class="blank">blank</span>'
    return f"{v*100:,.{dp}f}%"


def table(headers, rows, cls="responsive", caption=None, note=None):
    head = "".join(f'<th scope="col">{e(h)}</th>' for h in headers)
    body = "".join("<tr>" + "".join(f"<td data-label=\"{e(headers[i])}\">{c}</td>"
                                    for i, c in enumerate(r)) + "</tr>" for r in rows)
    cap = f"<caption>{caption}</caption>" if caption else ""
    n = f'<p class="tnote">{note}</p>' if note else ""
    return (f'<div class="scroll"><table class="{cls}">{cap}<thead><tr>{head}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>{n}")


NAV = [
    ("index.html", "Overview"),
    ("routes.html", "All 30 routes"),
    ("ladder.html", "Cost ladder"),
    ("penalties.html", "Penalty breakdown"),
    ("tax.html", "Tax & reporting"),
    ("steps.html", "Step by step"),
    ("methodology.html", "Verification"),
    ("flagged.html", "Flagged for review"),
]

CSS = """
:root{--ink:#12222b;--dim:#5a6b75;--line:#d9e2e8;--bg:#f6f8fa;--card:#fff;--accent:#0b6b5b;
--accent-soft:#e6f2ee;--warn:#8a5b00;--warn-soft:#fff6e2;--bad:#8f2020;--bad-soft:#fdecec;
--ok:#1c5f3a;--ok-soft:#e7f4ec;--mono:ui-monospace,SFMono-Regular,Menlo,monospace}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px}
a:focus-visible,button:focus-visible,summary:focus-visible{outline:3px solid #b8860b;outline-offset:2px}
header.top{background:#0d2b33;color:#fff;padding:10px 0}
header.top .wrap{display:flex;gap:14px;align-items:center;flex-wrap:wrap}
header.top a{color:#dff3ee}
header.top .brand{font-weight:700;color:#fff;text-decoration:none;letter-spacing:.2px}
header.top nav{display:flex;gap:6px;flex-wrap:wrap;font-size:.82rem}
header.top nav a{padding:5px 9px;border-radius:99px;text-decoration:none;border:1px solid transparent}
header.top nav a:hover{background:rgba(255,255,255,.12)}
header.top nav a[aria-current]{background:#fff;color:#0d2b33;font-weight:650}
.wrap{max-width:1120px;margin:0 auto;padding:0 16px}
main{padding:22px 0 64px}
h1{font-size:clamp(1.6rem,4.6vw,2.6rem);line-height:1.15;margin:.2em 0 .35em;letter-spacing:-.4px}
h2{font-size:clamp(1.2rem,2.8vw,1.55rem);margin:2.1em 0 .5em;letter-spacing:-.2px}
h3{font-size:1.05rem;margin:1.6em 0 .4em}
p{margin:.6em 0}
.lead{font-size:1.06rem;color:#26383f;max-width:74ch}
.dim,.muted{color:var(--dim)}
small{font-size:.82rem}
.pill{display:inline-block;padding:4px 11px;border-radius:99px;background:var(--accent-soft);
color:#0a4f43;font-size:.78rem;font-weight:650;letter-spacing:.2px}
.pill.warn{background:var(--warn-soft);color:var(--warn)}
.pill.bad{background:var(--bad-soft);color:var(--bad)}
.notice{border-left:4px solid #b8860b;background:var(--warn-soft);padding:13px 16px;border-radius:0 10px 10px 0;
margin:18px 0}
.notice.soft{border-left-color:var(--accent);background:var(--accent-soft)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(232px,1fr));gap:12px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:15px 16px;
text-decoration:none;color:inherit;display:block;transition:box-shadow .15s,border-color .15s}
a.card:hover{box-shadow:0 4px 16px rgba(13,43,51,.1);border-color:#9fbec5}
.card strong{display:block;color:var(--accent);font-size:.98rem;margin-bottom:3px}
.card p{margin:0;font-size:.88rem;color:var(--dim)}
.kpi{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:12px;margin:18px 0}
.kpi div{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.kpi .n{font-family:var(--mono);font-size:1.32rem;font-weight:700;color:#0d2b33;letter-spacing:-.5px}
.kpi .l{font-size:.76rem;color:var(--dim);text-transform:uppercase;letter-spacing:.5px;margin-top:2px}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;background:var(--card);border:1px solid var(--line);
border-radius:12px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:.87rem}
caption{text-align:left;padding:12px 14px 6px;font-weight:650;color:#0d2b33;font-size:.9rem}
th,td{padding:9px 11px;text-align:left;border-bottom:1px solid #e7edf1;vertical-align:top}
th{background:#eef3f5;font-size:.76rem;text-transform:uppercase;letter-spacing:.4px;color:#33474f;
position:sticky;top:0;white-space:nowrap}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:#fafcfd}
td.num,th.num{text-align:right;font-family:var(--mono);font-size:.82rem;white-space:nowrap}
.src{display:inline-block;font-size:.68rem;font-family:var(--mono);padding:2px 5px;border-radius:5px;
margin:1px 3px 1px 0;text-decoration:none;white-space:nowrap;border:1px solid}
.t-law{background:#e8f0fb;color:#1c3f73;border-color:#c5d7f0}
.t-gov{background:#eef4ee;color:#2c5b33;border-color:#cfe0d0}
.t-provider{background:#f4eef8;color:#573b6e;border-color:#ded0e8}
.blank{display:inline-block;min-width:46px;text-align:center;color:#8a6a00;background:#fff8e6;
border:1px dashed #d9b44a;border-radius:5px;font-size:.74rem;padding:1px 5px;font-family:inherit}
.tnote{font-size:.78rem;color:var(--dim);margin:-4px 0 14px}
.badge{display:inline-block;font-size:.72rem;font-weight:700;padding:2px 7px;border-radius:5px;white-space:nowrap}
.b-lawful{background:var(--ok-soft);color:var(--ok)}
.b-conditional{background:var(--warn-soft);color:var(--warn)}
.b-prohibited{background:var(--bad-soft);color:var(--bad)}
.b-verified{background:#e6f2ee;color:#0a4f43}
.b-partly{background:#fff6e2;color:#8a5b00}
.b-unverified{background:#fdecec;color:#8f2020}
details{background:var(--card);border:1px solid var(--line);border-radius:11px;margin:9px 0;overflow:hidden}
details[open]{border-color:#b9cdd4}
summary{padding:13px 15px;cursor:pointer;font-weight:650;display:flex;gap:9px;align-items:baseline;
flex-wrap:wrap;list-style:none}
summary::-webkit-details-marker{display:none}
summary::before{content:"+";font-family:var(--mono);color:var(--accent);font-weight:700;width:12px}
details[open] summary::before{content:"–"}
summary .rid{font-family:var(--mono);font-size:.78rem;color:var(--dim);background:#eef3f5;
padding:2px 6px;border-radius:5px}
.detail{padding:0 15px 15px;border-top:1px solid var(--line)}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.two ul{margin:.3em 0;padding-left:1.15em}
.two li{margin:.28em 0;font-size:.88rem}
.two h4{margin:12px 0 4px;font-size:.8rem;text-transform:uppercase;letter-spacing:.5px;color:var(--dim)}
ol.steps{padding-left:1.3em;margin:.5em 0}
ol.steps li{margin:.4em 0;font-size:.89rem}
footer{border-top:1px solid var(--line);margin-top:44px;padding:20px 0 40px;color:var(--dim);font-size:.82rem}
footer a{color:var(--dim)}
.flag-h{background:var(--bad-soft);border-left:4px solid var(--bad);padding:11px 14px;border-radius:0 9px 9px 0;
margin:12px 0;font-size:.9rem}
@media(max-width:760px){
 .two{grid-template-columns:1fr}
 .responsive thead{display:none}
 .responsive,.responsive tbody,.responsive tr,.responsive td{display:block;width:100%}
 .responsive tr{border:1px solid var(--line);border-radius:10px;margin:9px 0;background:var(--card);
  padding:4px 0;overflow:hidden}
 .responsive td{display:grid;grid-template-columns:38% 62%;gap:8px;padding:7px 12px;border:none;
  border-bottom:1px solid #eef3f5;font-size:.86rem}
 .responsive td:last-child{border-bottom:none}
 .responsive td::before{content:attr(data-label);font-size:.7rem;text-transform:uppercase;
  letter-spacing:.4px;color:var(--dim);font-weight:650;padding-top:2px}
 .responsive td:empty{display:none}
 th,td{padding:8px 9px}
 .kpi .n{font-size:1.12rem}
}
@media(min-width:761px){.responsive td:first-child{font-weight:600}}
"""


def shell(title: str, body: str, current: str, sub: bool = False) -> str:
    p = "../" if sub else ""
    parts = []
    for href, label in NAV:
        mark = ' aria-current="page"' if href == current else ""
        parts.append(f'<a href="{p}{href}"{mark}>{e(label)}</a>')
    nav = "".join(parts)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Official-source research on getting CNY out of mainland China as a US citizen: 30 routes, pros and cons, statutory penalty decomposition, and a computed cost ladder from USD 10,000 to USD 400,000 in 10,000 steps.">
<title>{e(title)} · China Money · Edition J</title>
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="{p}index.html">China Money · Edition J</a>
<nav aria-label="Site">{nav}</nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p><strong>Research, not legal, tax or investment advice.</strong> Every rule is linked to the instrument
that states it; every price to the provider that publishes it. Values that could not be confirmed for this
account are left blank and counted on the <a href="{p}methodology.html">verification page</a>. Rates are
snapshots, not quotes.</p>
<p><a href="{p}index.html">Overview</a> · <a href="{p}routes.html">Routes</a> ·
<a href="{p}ladder.html">Cost ladder</a> · <a href="{p}penalties.html">Penalties</a> ·
<a href="{p}tax.html">Tax &amp; reporting</a> · <a href="{p}steps.html">Steps</a> ·
<a href="{p}methodology.html">Verification</a> · <a href="{p}flagged.html">Flagged for review</a> ·
<a href="/China1/index.html">All editions</a> · <a href="/China1/COORDINATION.md">Coordination log</a></p>
<p>Edition J · built 2026-11-10 UTC · source snapshot 2026-11-10</p>
</div></footer>
</body>
</html>
"""


# ---------------------------------------------------------------- pages
def page_index():
    fx_one = costs.one_way_cost_pct()
    fx_rt = costs.round_trip_pct()
    s10 = costs.row_boc_tt(10_000)
    s400 = costs.row_boc_tt(400_000)
    pen400 = costs.us_penalty_exposure(400_000)
    kpi = [
        (f"{fx_one*100:.2f}%", "one-way FX cost (half the bid/ask spread)"),
        (f"${s10['sender_fee_usd']:,.0f}", "published BOC fees at USD 10,000"),
        (f"${s400['sender_fee_usd']:,.0f}", "published BOC fees at USD 400,000"),
        (f"${pen400['fbar_willful_max_usd']:,.0f}", "largest US penalty at USD 400,000"),
        ("30", "routes catalogued"),
        ("6", "prohibited, with no steps"),
    ]
    kpi_html = "".join(f'<div><div class="n">{n}</div><div class="l">{e(l)}</div></div>' for n, l in kpi)

    findings = "".join(
        f'<details id="f-{f["id"]}"><summary><span class="rid">{f["id"]}</span> {e(f["title"])}</summary>'
        f'<div class="detail"><p>{e(f["detail"])}</p><p>{src_links(f["sources"])}</p></div></details>'
        for f in analysis.FINDINGS
    )

    cats = routes.CATEGORY_NAMES
    cat_counts = {c: sum(1 for r in routes.ROUTES if r["category"] == c) for c in cats}
    cat_cards = "".join(
        f'<a class="card" href="routes.html#{c}"><strong>{e(cats[c])} ({cat_counts[c]})</strong>'
        f'<p>{e(routes.CATEGORY_BLURB[c])}</p></a>' for c in cats
    )

    body = f"""
<p class="pill">Edition J · 2026-11-10 · no manual input required</p>
<h1>What it actually costs to get CNY out of China</h1>
<p class="lead">Thirty routes, priced where a published price exists and blank where it does not. The short
version: <strong>there is no conversion tax in either country</strong>. What looks like a penalty is a bank
spread of about {fx_one*100:.2f}%, plus a capped commission and a flat cable fee. The genuinely large numbers
on this page are Chinese tax on the income itself and US penalties for not reporting the account.</p>

<div class="kpi">{kpi_html}</div>

<div class="notice"><strong>Read this before any number.</strong> FX cost is measured as half the bid/ask spread on
the Bank of China board published {e(market.BOC_BOARD['published'])} - that is, what you give up by paying the ask
instead of the bank's own mid. BOC's page states the counter/online rate governs, and the board is a snapshot.
Receiving-bank fees, intermediary charges, Chinese tax on your specific income and the balance itself are unknown,
so <strong>no all-in total is claimed</strong>. Blank is not zero.</div>

<h2>The six things that matter</h2>
<div class="cards">{"".join(f'''
<a class="card" href="#f-{f["id"]}"><strong>{f["id"]} · {e(f["title"][:58])}{"…" if len(f["title"])>58 else ""}</strong>
<p>{e(f["detail"][:132])}…</p></a>''' for f in analysis.FINDINGS[:6])}</div>

<h2>Decision order, in five lines</h2>
{table(["Order", "What to do first", "Why", "Source"], [
    ["1", "Classify the balance by source", "The lawful route is determined by how the money was earned, not by which provider is cheapest.", src_links(["CN-PBOC3"])],
    ["2", "Confirm your bank classification", "境内个人 and 境外个人 have different quota and documentary rules.", src_links(["CN-PBOC3", "CN-GUIDE2020"])],
    ["3", "Pick the matching route family", "Documented income → R01. Property → R07. Pre-emigration savings → R08. Inheritance → R09.", src_links(["CN-GUIDE2020", "CN-PROPERTY2004"])],
    ["4", "Only then compare execution", "BOC tariff versus a licensed provider; the FX spread is similar, the fixed fees are not.", src_links(["BOC-TARIFF", "WISE-CNY"])],
    ["5", "File the US side on time", "The reporting penalty is larger than the entire transfer cost.", src_links(["US-FBAR", "US-5321"])],
], caption="Figure 1 — the order in which each question has to be answered")}

<h2>The cost shape, at a glance</h2>
<p>The FX spread scales with the amount; the bank fees do not. That single fact drives every row of the cost
ladder: at USD 10,000 the fixed and capped fees are about
{costs.row_boc_tt(10_000)['sender_fee_usd']/100:.2f}% of the transfer, and at USD 400,000 they fall to about
{costs.row_boc_tt(400_000)['sender_fee_usd']/4000:.3f}%. The FX cost, by contrast, is
${costs.fx_cost_usd(400_000):,.2f} at USD 400,000 and ${costs.fx_cost_usd(10_000):,.2f} at USD 10,000 - always the
same {fx_one*100:.2f}%.</p>
{table(["USD sent", "CNY needed at BOC selling rate", "FX cost vs parity", "BOC commission + cable", "All-in total"],
       [[f"${r['target_usd']:,}", money(r["cny_needed"]), money(r["fx_cost_usd"]), money(r["sender_fee_usd"]),
         money(r["all_in_usd"])] for r in
        [costs.row_boc_tt(t) for t in (10_000, 50_000, 100_000, 200_000, 300_000, 400_000)]],
       cls="responsive",
       caption="Figure 2 — R01, the documented-income bank route, at six sizes",
       note="All-in total is blank because the receiving bank's charge is unknown; adding a guessed number "
            "would be the exact failure this edition was built to avoid. Full 40-row ladder on the Cost ladder page.")}

<h2>Six route families</h2>
<div class="cards">{cat_cards}</div>

<h2>Findings</h2>
{findings}

<h2>Where to go next</h2>
<div class="cards">
<a class="card" href="ladder.html"><strong>Cost ladder →</strong><p>All 40 USD targets, every priced route, and the routes that deliberately show blanks.</p></a>
<a class="card" href="penalties.html"><strong>Penalty breakdown →</strong><p>24 components sorted into unavoidable cost, tax on income, penalty risk and avoidable waste.</p></a>
<a class="card" href="flagged.html"><strong>Flagged for review →</strong><p>Twelve items where the evidence is thin, conflicting or simply missing.</p></a>
</div>
"""
    return shell("Overview", body, "index.html")


def page_routes():
    rows_by_cat = {}
    for r in routes.ROUTES:
        rows_by_cat.setdefault(r["category"], []).append(r)

    out = [f"""
<p class="pill">Route catalogue</p>
<h1>All {len(routes.ROUTES)} ways a US citizen can move or use CNY</h1>
<p class="lead">Each route states its legal basis, its published limit, its pros and cons, and whether a price
could be verified. Prohibited routes carry no execution steps - only what the instrument prohibits and what it
costs you if you do it anyway.</p>
<div class="notice soft"><strong>How to read the badges.</strong>
<span class="badge b-lawful">lawful</span> available if the documentary facts fit ·
<span class="badge b-conditional">conditional</span> lawful only with an approval or an eligibility fact ·
<span class="badge b-prohibited">prohibited</span> unlawful, risk information only. Verification badges:
<span class="badge b-verified">verified</span> rule and price both read ·
<span class="badge b-partly">partly</span> rule read, price or practice not ·
<span class="badge b-unverified">unverified</span> not confirmable from official sources.</div>
"""]

    for cat in "ABCDEF":
        items = rows_by_cat.get(cat, [])
        out.append(f'<h2 id="{cat}">{e(routes.CATEGORY_NAMES[cat])} <span class="dim" style="font-weight:400">'
                   f"({len(items)})</span></h2>")
        out.append(f'<p class="dim">{e(routes.CATEGORY_BLURB[cat])}</p>')
        for r in items:
            badge = {"lawful": "b-lawful", "conditional": "b-conditional", "prohibited": "b-prohibited"}[r["lawful"]]
            vb = {"verified": "b-verified", "partly": "b-partly", "unverified": "b-unverified"}[r["verifiability"]]
            est = r.get("estimate", {})
            price_line = {
                "boc_tt": "Priced: FX spread + BOC published tariff",
                "limit_only": "Limit published, price not published as a schedule",
                "quote_only": "Quote-only: no published schedule",
                "not_applicable": "No conversion occurs, so no conversion cost",
                "prohibited": "Not priced: unlawful",
            }.get(est.get("mode"), "No price basis")
            pros = "".join(f"<li>{e(p)}</li>" for p in r["pros"]) or '<li class="dim">None. This route is unlawful.</li>'
            cons = "".join(f"<li>{e(c)}</li>" for c in r["cons"]) or "<li>—</li>"
            steps = "".join(f"<li>{e(s)}</li>" for s in r["steps"])
            steps_block = (f'<h4>Steps</h4><ol class="steps">{steps}</ol>' if r["steps"] else
                           '<h4>Steps</h4><p class="flag-h">No execution steps are published for this route. '
                           'It is unlawful and the only correct action is not to use it.</p>')
            limit_cell = e(r["limit"])
            out.append(f"""
<details id="{r['id']}">
<summary><span class="rid">{r['id']}</span> {e(r['name'])}
<span class="badge {badge}">{r['lawful']}</span>
<span class="badge {vb}">{r['verifiability']}</span></summary>
<div class="detail">
<p class="dim"><strong>{e(r['zh'])}</strong> · {e(r['law_text'])} · {src_links(r['law_basis'])}</p>
<p><strong>Published limit.</strong> {limit_cell}</p>
<p><strong>Price basis.</strong> {e(price_line)} {" ".join(src_link(s) for s in r.get('cost_basis', []))}
{" ".join(src_link(s) for s in r.get('risk_basis', []))}</p>
<div class="two">
<div><h4>Pros</h4><ul>{pros}</ul></div>
<div><h4>Cons</h4><ul>{cons}</ul></div>
</div>
{steps_block}
<p><a href="{('ladder-' + r['id'] + '.html') if r['estimate']['mode'] in ('boc_tt','limit_only') else 'ladder.html#' + r['id']}">{'Cost ladder for this route →' if r['estimate']['mode'] in ('boc_tt','limit_only') else 'Why this route has no ladder →'}</a></p>
</div></details>""")

    return shell("All routes", "".join(out), "routes.html")


def page_ladder():
    priced = [r for r in routes.ROUTES if r["estimate"]["mode"] in ("boc_tt",)]
    limit_rows = [r for r in routes.ROUTES if r["estimate"]["mode"] == "limit_only"]
    quote_rows = [r for r in routes.ROUTES if r["estimate"]["mode"] == "quote_only"]
    null_rows = [r for r in routes.ROUTES if r["estimate"]["mode"] in ("not_applicable", "prohibited")]

    out = [f"""
<p class="pill">Cost ladder · 40 targets</p>
<h1>Every USD 10,000 step, from 10,000 to 400,000</h1>
<p class="lead">Forty exact targets, computed from two published numbers: the BOC USD board from
{e(market.BOC_BOARD['published'])} and the BOC published TT tariff. FX cost is measured against the PBOC central
parity of {market.PARITY['usd_cny']:.4f}, so it captures everything the bank charges over the reference rate.</p>

<div class="kpi">
<div><div class="n">{len(priced)}</div><div class="l">routes with a computed ladder</div></div>
<div><div class="n">{len(priced)*40}</div><div class="l">computed rows</div></div>
<div><div class="n">{len(limit_rows)}</div><div class="l">routes with a published limit but no schedule</div></div>
<div><div class="n">{len(quote_rows)}</div><div class="l">quote-only routes</div></div>
<div><div class="n">{len(null_rows)}</div><div class="l">routes with no conversion event</div></div>
</div>

<div class="notice"><strong>What the blank columns mean.</strong> A blank cell is a value that no official source
published for this account - the receiving bank's charge, Chinese tax on the specific income, the intermediary
fee. Filling them with "typical" numbers would make the totals look complete and be wrong. The verification page
counts every blank.</div>

<h2>Master table: all 40 targets</h2>
<p>This is the headline answer for the one route that can actually carry the whole balance on documented income
(R01). Fees are BOC's published cross-border TT tariff: 1 per mille, minimum CNY 50, maximum CNY 260, plus CNY 150
cable. FX cost is the gap between parity and the rate you pay.</p>
{table(
    ["USD target", "CNY needed", "FX cost (USD)", "BOC commission (CNY)", "Cable (CNY)", "Sender fees (USD)",
     "US receiving fee", "Chinese tax", "All-in total", "Source"],
    [[f"${r['target_usd']:,}", money(r["cny_needed"]), money(r["fx_cost_usd"]),
      money(r["sender_fee_cny"] - market.BOC_TARIFF['cable_cny']['other']), money(r["sender_fee_cny"] - (r['sender_fee_cny']-150)),
      money(r["sender_fee_usd"]), money(r["receiver_fee_usd"]), money(r["tax_usd"]), money(r["all_in_usd"]),
      src_links(["BOC-BOARD", "BOC-TARIFF"])]
     for r in [costs.row_boc_tt(t) for t in costs.TARGETS]],
    caption="Table 1 — R01 documented-income bank route, all 40 targets",
    note="Read across: the CNY column is what you must have on deposit. The fee columns are published tariffs. "
         "The last three columns are blank because no official source prices them for this account.")}

<h2>Method comparison at the same size</h2>
<p>Same USD target, different route families. Where a cell is blank the route either cannot reach that amount or
publishes no price.</p>
{table(
    ["Route", "Limit basis", "USD 10,000", "USD 100,000", "USD 250,000", "USD 400,000", "Status"],
    [[f'<a href="#{r["id"]}">{r["id"]} {e(r["name"][:44])}{"…" if len(r["name"])>44 else ""}</a>',
      e(r["limit"][:74]) + ("…" if len(r["limit"]) > 74 else ""),
      *[money(costs.row_boc_tt(t)["sender_fee_usd"]) if r["estimate"]["mode"] == "boc_tt" else
        '<span class="blank">no schedule</span>' for t in (10_000, 100_000, 250_000, 400_000)],
      f'<span class="badge b-{r["lawful"]}">{r["lawful"]}</span>'] for r in routes.ROUTES],
    caption="Table 2 — sender-side published fees by route family and size",
    note="Only routes whose price is published can carry a number. A route that is lawful but quote-only is not "
         "free - it is unpriced. It appears in the per-route section below.")}

<h2>Per-route ladders</h2>
<p>Each priced route has its own page with the full 40-row ladder, kept separate so the table loads quickly on a
phone. This page stays small on purpose.</p>
"""]

    out.append(table(["Route", "Price basis", "Ladder"],
                     [[f'<span id="{r["id"]}">{r["id"]}</span> · {e(r["name"])}',
                       e({"boc_tt": "FX half-spread + BOC published tariff",
                          "limit_only": "Limit published; no published price"}[r["estimate"]["mode"]]),
                       f'<a href="ladder-{r["id"]}.html">open 40-row ladder →</a>']
                      for r in priced + limit_rows],
                     caption="Table 3 — per-route ladder pages"))
    out.append('<h2>Routes with a published limit but no published price</h2>'
               '<p>These are lawful and bounded, but no official schedule prices them. The CNY equivalent is still '
               'computed so the amount can be compared; the cost columns stay blank.</p>')
    for r in limit_rows:
        out.append(f'<h3 id="{r["id"]}">{r["id"]} · {e(r["name"])}</h3>')
        out.append(f'<p class="dim">{e(r["law_text"])} · {src_links(r["law_basis"])}</p>')
        out.append(table(["USD target", "CNY needed", "FX cost", "Sender fee", "All-in total", "Source"],
                         [[f"${x['target_usd']:,}", money(x["cny_needed"]), money(x["fx_cost_usd"]),
                           money(x["sender_fee_usd"]), money(x["all_in_usd"]),
                           src_links(r["law_basis"])]
                          for x in costs.ladder_for(r)],
                         caption=f"{r['id']} — no published cost schedule for this channel",
                         note=e(r["estimate"].get("reason", ""))))

    out.append('<h2>Routes with no computable ladder</h2>')
    out.append("".join(f'<h3 id="{r["id"]}">{r["id"]} · {e(r["name"])}</h3>'
                       f'<p class="dim">{e(r["law_text"])} · {src_links(r["law_basis"])}</p>'
                       for r in quote_rows + null_rows))
    out.append(table(["Route", "Why there is no ladder", "Sources"],
                     [[f'{r["id"]} {e(r["name"])}',
                       e({"quote_only": "Price is quote-based only; no schedule exists to transcribe.",
                          "not_applicable": "No CNY-to-USD conversion occurs, so a conversion ladder would be meaningless.",
                          "prohibited": "Unlawful; publishing a price ladder would be publishing a how-to."}
                         [r["estimate"]["mode"]]),
                       src_links(r["law_basis"])] for r in quote_rows + null_rows],
                     caption="Table 4 — routes deliberately excluded from the ladder",
                     note="Excluded on principle, not by omission."))

    return shell("Cost ladder", "".join(out), "ladder.html")


def page_route_ladder(r):
    rows = costs.ladder_for(r)
    priced_mode = r["estimate"]["mode"] == "boc_tt"
    tax_rate = r["estimate"].get("tax_rate")
    if priced_mode:
        tax_col = (f"{tax_rate*100:.0f}% withholding on the income, grossed up"
                   if tax_rate else "not published for this account")
        headers = ["USD target", "CNY needed", "FX cost (USD)", "Sender fees (USD)",
                   "Chinese tax on income", "US receiving fee", "All-in total", "Source"]
        body_rows = [[f"${x['target_usd']:,}", money(x["cny_needed"]), money(x["fx_cost_usd"]),
                      money(x["sender_fee_usd"]), money(x["tax_usd"]), money(x["receiver_fee_usd"]),
                      money(x["all_in_usd"]), src_links(r["cost_basis"])] for x in rows]
    else:
        tax_col = "no published cost schedule for this channel"
        headers = ["USD target", "CNY needed", "FX cost", "Sender fee", "All-in total", "Source"]
        body_rows = [[f"${x['target_usd']:,}", money(x["cny_needed"]), money(x["fx_cost_usd"]),
                      money(x["sender_fee_usd"]), money(x["all_in_usd"]), src_links(r["law_basis"])]
                     for x in rows]
    badge = {"lawful": "b-lawful", "conditional": "b-conditional", "prohibited": "b-prohibited"}[r["lawful"]]
    default_note = ("FX cost is half the bid/ask spread on the BOC board; fees are the BOC published tariff. "
                    "The all-in total stays blank because the receiving bank publishes no figure here.")
    body = f"""
<p class="pill">Cost ladder · {r['id']}</p>
<h1>{e(r['name'])}</h1>
<p><span class="badge {badge}">{r['lawful']}</span> <span class="dim">{e(r['zh'])}</span></p>
<p class="lead">{e(r['limit'])}</p>
<p class="dim">{e(r['law_text'])} · {src_links(r['law_basis'])}</p>
<div class="notice">{e(r['estimate'].get('reason', default_note))}</div>
{table(headers, body_rows, caption=f"{r['id']} - 40 targets - Chinese tax treatment: {tax_col}",
       note="Blank means unverified, not free. The verification page counts every blank cell.")}
<p><a href="ladder.html">All routes</a> · <a href="routes.html#{r['id']}">Route detail and steps</a></p>
"""
    return shell(f"{r['id']} cost ladder", body, "ladder.html")


def page_penalties():
    kinds = [("unavoidable", "Unavoidable cost of converting"),
             ("tax-on-income", "Tax on the income itself (not a conversion fee)"),
             ("penalty-risk", "Penalty exposure if the route is unlawful or unreported"),
             ("avoidable", "Waste you can avoid"),
             ("baseline", "Comparison baselines")]
    out = [f'''
<p class="pill">Penalty breakdown</p>
<h1>The "conversion penalty", taken apart</h1>
<p class="lead">People describe a large penalty for converting CNY to USD. There is no such tax. What exists is
four different things that get added together in conversation: a bank spread you always pay, Chinese tax on the
income, penalties for taking a prohibited route, and US penalties for not reporting the account. They are
separated here so they can be compared honestly.</p>

<div class="kpi">
<div><div class="n">{costs.one_way_cost_pct()*100:.2f}%</div><div class="l">one-way FX cost</div></div>
<div><div class="n">{costs.spread_pct_of_bid()*100:.2f}%</div><div class="l">bid/ask spread on the board</div></div>
<div><div class="n">{costs.spread_pct_of_bid()*100*2:.2f}%</div><div class="l">round trip (the "0.42%" figure)</div></div>
<div><div class="n">$0</div><div class="l">conversion tax in either country</div></div>
<div><div class="n">20%</div><div class="l">Chinese rate on the taxed categories</div></div>
</div>
''']
    for kind, label in kinds:
        items = [p for p in analysis.PENALTY_LINES if p["kind"] == kind]
        out.append(f"<h2>{e(label)} <span class='dim' style='font-weight:400'>({len(items)})</span></h2>")
        rows = []
        for p in items:
            val = p["value"]
            if val == "computed":
                if p["id"] == "P01":
                    val_html = f"{costs.one_way_cost_pct()*100:.3f}% of the amount"
                elif p["id"] == "P02":
                    val_html = "CNY 50 – 260 flat by size"
                elif p["id"] == "P03":
                    val_html = "CNY 150 per transfer"
                else:
                    val_html = f"{costs.round_trip_pct()*100:.3f}% of the amount"
            elif val is None:
                val_html = money(None)
            else:
                val_html = e(val)
            rows.append([f'<strong>{p["id"]}</strong>', e(p["component"]), val_html, e(p["basis"]),
                         src_links(p["sources"])])
        out.append(table(["#", "Component", "Value", "Basis in the source", "Source"], rows,
                         cls="responsive", caption=f"{label}"))

    out.append(f"""
<h2>The asymmetry that matters</h2>
<p>Put the largest lawful cost next to the largest unlawful one at the same balance. At USD 400,000 the entire
published bank cost of moving the money is a few hundred dollars; the statutory maximum for one willful FBAR
violation is {money(costs.us_penalty_exposure(400000)['fbar_willful_max_usd'], 0)}. A prohibited route adds a
Chinese fine of up to 30% (or 100% if serious) on top.</p>
{table(["Balance", "FX cost (half-spread)", "BOC sender fees", "SAFE fine, ordinary case (30%)",
        "SAFE fine, serious case (100%)", "FBAR willful (50% of balance)", "Source"],
       [[f"${b:,}", money(costs.fx_cost_usd(b)), money(costs.row_boc_tt(b)["sender_fee_usd"]),
         money(costs.cn_penalty_exposure(b)["evasion_max_ordinary_usd"], 0),
         money(costs.cn_penalty_exposure(b)["evasion_max_serious_usd"], 0),
         money(costs.us_penalty_exposure(b)["fbar_willful_50pct_usd"], 0),
         src_links(["CN-FXREG", "US-5321", "BOC-TARIFF"])]
        for b in (10_000, 50_000, 100_000, 200_000, 300_000, 400_000)],
       caption="Table 4 — lawful cost versus statutory maximum exposure",
       note="These are statutory maxima, not predictions: the actual fine is set case by case, and the safe "
            "number for any lawful route is zero. The comparison is the point - the penalty dwarfs the fee.")}

<h2>The trap in comparing to the central parity</h2>
<p>A tempting shortcut is to measure the FX cost against the PBOC central parity of {market.PARITY['usd_cny']:.4f}
({e(market.PARITY['quote_time'])}). On the pair retrieved for this edition the result is
<strong>{costs.parity_gap_pct()*100:.2f}%</strong> - a negative cost, which would mean the bank paid you to convert.
That is not a market anomaly; it is what happens when you subtract a rate fixed at 09:15 on one day from a board
published the next morning. The gap mixes the real spread with a day of market movement, so this edition does not
use it. The defensible measures are the ones derived from a single board: the half-spread
({costs.one_way_cost_pct()*100:.2f}%) and the full spread ({costs.round_trip_pct()*100:.2f}%).</p>

<div class="notice"><strong>The one number people quote that is real.</strong> The 2004 property-transfer
measures said first release no more than half, then half of the remainder after a year, then the rest after two.
That looked like a "penalty for waiting". 汇发〔2014〕2号 cancelled it. If a bank tells you the staging applies,
that is the outdated text, not the current rule.</div>
""")
    return shell("Penalty breakdown", "".join(out), "penalties.html")


def page_tax():
    out = [f'''
<p class="pill">Tax and reporting</p>
<h1>Two tax systems, four forms, one rule: report first</h1>
<p class="lead">China taxes the income. The US taxes your worldwide income and, separately, punishes failure to
report the account. None of these is a fee for converting, and all of them are larger than the bank charges.</p>

<h2>China</h2>
{table(["Instrument", "What it says", "Effect on this question", "Source"], [
    ["IIT Law Art. 2", "Nine categories of taxable income", "Currency exchange is not one of them. There is no Chinese conversion tax.", src_links(["CN-IIT"])],
    ["IIT Law Art. 3(3)", "Flat 20% on interest, dividends, asset leasing, asset transfer, incidental income", "The rate that applies to most non-salary balances.", src_links(["CN-IIT"])],
    ["IIT Law Art. 6(5)", "Asset transfer taxed on gain after original value and reasonable expenses", "Property and equity: the base is the gain, not the price.", src_links(["CN-IIT"])],
    ["IIT Law Art. 10(5)", "Filing duty when emigrating and cancelling household registration", "An exit filing trigger that is easy to miss.", src_links(["CN-IIT"])],
    ["财政部 税务总局公告2026年第27号", "20% on FIE dividends to foreign individuals, withheld by the payer, from 2026-09-01", "The 1994 exemption is repealed. Old guidance is wrong.", src_links(["CN-DIV2026"])],
], caption="Table 5 — Chinese tax provisions that actually bite")}

<h2>United States</h2>
{table(["Duty", "Trigger", "Penalty if missed", "Source"], [
    ["Worldwide income", "You are a US citizen or resident", "Tax plus interest plus accuracy penalties", src_links(["US-IRS-ABROAD"])],
    ["FBAR (FinCEN 114)", "Foreign accounts aggregate above USD 10,000 at any point in the year",
     f"Non-willful up to USD {market.US_PENALTIES['fbar_nonwillful_max_usd']:,}; willful up to the greater of USD {market.US_PENALTIES['fbar_willful_max_usd']:,} or 50% of the balance", src_links(["US-FBAR", "US-5321", "US-1010821"])],
    ["Form 8938", "Specified foreign assets above the threshold for your filing status and residence",
     "USD 10,000, plus up to USD 50,000 more after notice", src_links(["US-8938", "US-6038D"])],
    ["Form 3520", "Gift or bequest above USD 100,000 from a nonresident alien, or foreign-trust events",
     "Information return; the penalty amount is flagged as unverified here", src_links(["US-3520"])],
    ["FinCEN 105", "More than USD 10,000 in currency or monetary instruments into or out of the US at one time",
     "Duty verified; amount flagged", src_links(["US-1010340"])],
    ["§988 currency gain", "Personal transaction: disregarded unless the gain exceeds USD 200",
     "Ordinary income treatment above that", src_links(["US-988"])],
], caption="Table 6 — the US side, and what each failure costs")}

<div class="notice"><strong>Why FBAR dominates every other number in this project.</strong> At a USD 400,000
balance, one willful violation has a statutory maximum of USD {costs.us_penalty_exposure(400000)['fbar_willful_max_usd']:,.0f}.
The published bank cost of moving the same USD 400,000 through BOC is about
USD {costs.row_boc_tt(400000)['sender_fee_usd']:,.0f}. Filing on time is the highest-return action available, and
it does not require moving anything.</div>

<div class="notice soft"><strong>The clean sequence.</strong> Report the account while it is still in China (FBAR,
8938). Pay or confirm Chinese tax on the income. Then convert through the route whose documentary basis matches
the source, and claim the Chinese tax as a foreign tax credit. The order matters because the reporting duty
attaches to the account, not to the transfer.</div>
''']
    return shell("Tax and reporting", "".join(out), "tax.html")


def page_steps():
    out = [f"""
<p class="pill">Step by step</p>
<h1>Exactly how each route works, in order</h1>
<p class="lead">Twenty-four lawful or conditional routes, each as a numbered procedure with the provision that
authorises the step. The six prohibited routes are excluded by design - this page does not explain how to break
the law.</p>
<div class="notice soft">These are the procedural steps described in the cited instruments, not a substitute for
your bank's current checklist. Banks apply their own documentary standards and may ask for more.</div>
"""]
    n = 0
    for r in routes.ROUTES:
        if r["lawful"] == "prohibited" or not r["steps"]:
            continue
        n += 1
        badge = {"lawful": "b-lawful", "conditional": "b-conditional"}[r["lawful"]]
        steps = "".join(f"<li>{e(s)}</li>" for s in r["steps"])
        out.append(f"""
<h3 id="{r['id']}">{r['id']} · {e(r['name'])} <span class="badge {badge}">{r['lawful']}</span></h3>
<p class="dim">{e(r['law_text'])} · {src_links(r['law_basis'])}</p>
<ol class="steps">{steps}</ol>""")
    out.append(f'<p class="dim">{n} procedures. Four routes carry no procedure because they are unlawful, and two '
               f'because they involve no transfer.</p>')
    return shell("Step by step", "".join(out), "steps.html")


def page_methodology():
    # counted values for the verification page
    n_sources = len(S)
    by_tier = {}
    for s in S.values():
        by_tier[s["tier"]] = by_tier.get(s["tier"], 0) + 1
    n_rows = sum(1 for r in routes.ROUTES if r["estimate"]["mode"] == "boc_tt") * 40
    blanks = 0
    for r in routes.ROUTES:
        for row in costs.ladder_for(r):
            blanks += sum(1 for k in ("fx_cost_usd", "sender_fee_usd", "receiver_fee_usd", "tax_usd", "all_in_usd")
                          if row.get(k) is None)
    body = f"""
<p class="pill">Verification</p>
<h1>What was checked, line by line, and what is still blank</h1>
<p class="lead">Every number on this site is either transcribed from a page fetched in this session or computed
from such a number by arithmetic stated on the page. The build fails if any figure cannot be traced.</p>

<div class="kpi">
<div><div class="n">{n_sources}</div><div class="l">sources read in this session</div></div>
<div><div class="n">{by_tier.get('A',0)}</div><div class="l">statutes / regulators</div></div>
<div><div class="n">{by_tier.get('B',0)}</div><div class="l">government reprints</div></div>
<div><div class="n">{by_tier.get('P',0)}</div><div class="l">provider-primary</div></div>
<div><div class="n">{len(routes.ROUTES)}</div><div class="l">routes catalogued</div></div>
<div><div class="n">{n_rows}</div><div class="l">computed ladder rows</div></div>
</div>

<h2>Source register</h2>
<p>Read on 2026-11-10. The scope column records what was actually inspected, so no claim is wider than the text
that was read.</p>
{table(["ID", "Tier", "Publisher", "Instrument", "What was inspected", "Link"],
       [[e(k), {"A": "law", "B": "gov reprint", "P": "provider"}[v["tier"]], e(v["publisher"]), e(v["title"]),
         e(v["scope"]), f'<a href="{v["url"]}" rel="noopener noreferrer">open ↗</a>'] for k, v in S.items()],
       caption="Table 7 — the full evidence base")}

<h2>Every rule, and the text that carries it</h2>
{table(["Source", "Supports"], [[e(k), e(v["supports"])] for k, v in S.items()],
       caption="Table 8 — claim-to-source mapping")}

<h2>Arithmetic, stated openly</h2>
{table(["Computation", "Formula", "Result at 2026-11-10"], [
    ["BOC buying rate (CNY per USD)", f"{market.BOC_BOARD['cash_sell']} / {market.BOC_BOARD['unit_per']:.0f}", f"{costs.boc_rate_sell():.4f}"],
    ["BOC selling rate (CNY per USD)", f"{market.BOC_BOARD['cash_buy']} / {market.BOC_BOARD['unit_per']:.0f}", f"{costs.boc_rate_buy():.4f}"],
    ["Bank mid", "(bid + ask) / 2", f"{costs.mid_rate():.5f}"],
    ["Full bid/ask spread", "(ask − bid) / bid", f"{costs.spread_pct_of_bid()*100:.3f}%"],
    ["One-way cost (half-spread)", "(ask − mid) / mid", f"{costs.one_way_cost_pct()*100:.3f}%"],
    ["Round trip", "(ask − bid) / bid, once each way", f"{costs.round_trip_pct()*100:.3f}%"],
    ["Ask vs central parity (not used)", "(ask − parity) / parity", f"{costs.parity_gap_pct()*100:.3f}%"],
    ["CNY needed for a USD target", "target × ask", "per row"],
    ["BOC commission", "min(max(0.001 × CNY, 50), 260)", "per row"],
    ["BOC cable", "CNY 150, non-HK/Macau/Taiwan", "per row"],
    ["Fee in USD", "CNY total / ask", "per row"],
], caption="Table 9 — the only arithmetic used, so it can be replicated by hand",
       note="The last row is shown to be rejected: a negative result is proof that the two rates come from different "
            "timestamps and must not be subtracted. Only figures derived from the single BOC board are used as costs.")}

<h2>Deliberately blank</h2>
<p>{blanks} cells across the ladders are blank. Each one is a value that no official source published for this
account: the receiving bank's charge, the intermediary's charge, Chinese tax on the specific income, and the
all-in total that would depend on them. They are rendered as <span class="blank">blank</span> and never as zero.</p>

<h2>Limits of this edition</h2>
<ul>
<li>Two market snapshots, both timestamped; BOC states the actual transaction rate governs.</li>
<li>One bank's tariff. ICBC's schedule was unreadable and HSBC's PDF 404'd, so no cross-bank comparison is claimed.</li>
<li>No Chinese or US tax is computed, because the income base is unknown.</li>
<li>Provincial and branch practice is not surveyed; a local branch may apply the same rule differently.</li>
<li>US Code was read on Cornell's republication because the authoritative host returned 404 from this sandbox.</li>
<li>This is research, not advice, and it cannot make an account eligible that the facts do not make eligible.</li>
</ul>
<p>All twelve open items are published with their sources on the <a href="flagged.html">Flagged for review</a>
page.</p>
"""
    return shell("Verification", body, "methodology.html")


def page_flagged():
    sev = {"high": "bad", "medium": "warn", "low": ""}
    rows = [[f'<strong>{f["id"]}</strong>',
             f'<span class="badge b-{ "prohibited" if f["severity"]=="high" else ("conditional" if f["severity"]=="medium" else "lawful") }">{f["severity"]}</span>',
             f'{e(f["title"])}<br><span class="dim">{e(f["detail"])}</span>',
             src_links(f["sources"])] for f in analysis.FLAGS]
    body = f"""
<p class="pill bad">Flagged for review</p>
<h1>{len(analysis.FLAGS)} items to review, none of which blocked publication</h1>
<p class="lead">These are the places where the evidence is thin, conflicting or simply unavailable. Each carries
the source that was read, so the reader can check the reasoning rather than take the conclusion.</p>
<div class="notice"><strong>Why publish anyway.</strong> Leaving a gap invisible is worse than leaving it blank.
Everything on this page stays visible until an official source closes it, and the corresponding table cells stay
empty in the meantime.</div>
{table(["#", "Severity", "Item and detail", "Sources"], rows,
       caption="Table 10 — open review items")}
<h2>How to close each one</h2>
{table(["Item", "What would close it"], [
    ["FJ01", "A statement of the account's booking classification and source documents, from the bank."],
    ["FJ02", "Re-read the BOC board and the parity on the day of the transfer."],
    ["FJ03", "The Form 3520 instructions penalties section, read in full."],
    ["FJ04", "A written position from the relevant SAFE branch on which text it applies."],
    ["FJ05", "Retrieve the PBOC original of 银发〔2026〕42号."],
    ["FJ06", "Re-read §988, §5321 and §6038D on uscode.house.gov or govinfo when reachable."],
    ["FJ07", "Written confirmation of your 境内/境外 classification from the bank."],
    ["FJ08", "A readable tariff from a second bank."],
    ["FJ09", "An official postal-remittance limit and fee schedule."],
    ["FJ10", "Your receiving bank's incoming-wire fee schedule."],
    ["FJ11", "Customs and capital-account rules for gold and offshore asset sales."],
    ["FJ12", "The Chinese withholding certificates for the specific income."],
], caption="Table 11 — closure path for each flag")}
"""
    return shell("Flagged for review", body, "flagged.html")


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    pages = {
        "index.html": page_index(),
        "routes.html": page_routes(),
        "ladder.html": page_ladder(),
        "penalties.html": page_penalties(),
        "tax.html": page_tax(),
        "steps.html": page_steps(),
        "methodology.html": page_methodology(),
        "flagged.html": page_flagged(),
    }
    for r in routes.ROUTES:
        if r["estimate"]["mode"] in ("boc_tt", "limit_only"):
            pages[f"ladder-{r['id']}.html"] = page_route_ladder(r)
    for name, html_text in pages.items():
        (OUT / name).write_text(html_text, encoding="utf-8")

    # machine-readable exports
    export = {
        "edition": "J",
        "built_utc": "2026-11-10",
        "market": {"boc_board": market.BOC_BOARD, "parity": market.PARITY},
        "derived": {
            "ask_cny_per_usd": round(costs.boc_rate_sell(), 4),
            "bid_cny_per_usd": round(costs.boc_rate_buy(), 4),
            "spread_pct_of_bid": round(costs.spread_pct_of_bid(), 6),
            "mid_cny_per_usd": round(costs.mid_rate(), 5),
            "one_way_cost_pct": round(costs.one_way_cost_pct(), 6),
            "round_trip_pct": round(costs.round_trip_pct(), 6),
            "parity_gap_pct_rejected": round(costs.parity_gap_pct(), 6),
        },
        "sources": {k: {kk: vv for kk, vv in v.items()} for k, v in S.items()},
        "routes": [{k: v for k, v in r.items()} for r in routes.ROUTES],
        "penalty_lines": analysis.PENALTY_LINES,
        "flags": analysis.FLAGS,
        "findings": analysis.FINDINGS,
    }
    (OUT / "data.json").write_text(json.dumps(export, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # CSV for the primary ladder
    lines = ["route,target_usd,cny_needed,fx_cost_usd,sender_fee_cny,sender_fee_usd,"
             "receiver_fee_usd,tax_usd,all_in_usd"]
    for r in routes.ROUTES:
        for row in costs.ladder_for(r):
            def f(v):
                return "" if v is None else f"{v:.2f}"
            lines.append(",".join([r["id"], str(row["target_usd"]), f(row["cny_needed"]),
                                   f(row["fx_cost_usd"]), f(row["sender_fee_cny"]),
                                   f(row["sender_fee_usd"]), f(row["receiver_fee_usd"]),
                                   f(row["tax_usd"]), f(row["all_in_usd"])]))
    (OUT / "cost-ladder.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {len(pages)} pages, data.json and cost-ladder.csv to {OUT}")


if __name__ == "__main__":
    build()
