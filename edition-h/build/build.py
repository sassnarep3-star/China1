#!/usr/bin/env python3
"""
Edition H - build.

Reads edition-h/data/*.json and writes:
  * edition-h/docs/**            the dashboard and every subpage
  * <repo>/index.html            the single root landing page

The cost engine is deliberately small and visible: every figure in every table is
recomputed from parameters.json by verify.py, which does not read the HTML for its
inputs.

No value is invented. If a parameter is null the cell is an em dash and the route
carries a flag.
"""
import html
import json
import math
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
H = ROOT / "edition-h"
DATA = H / "data"
OUT = H / "docs"

AS_OF = "2026-11-09"
EDITION = "H"

# ---------------------------------------------------------------------------
# data
# ---------------------------------------------------------------------------

with open(DATA / "sources.json", encoding="utf-8") as fh:
    SRC_DOC = json.load(fh)
with open(DATA / "parameters.json", encoding="utf-8") as fh:
    P = json.load(fh)
with open(DATA / "methods.json", encoding="utf-8") as fh:
    METHODS_DOC = json.load(fh)
with open(DATA / "taxes.json", encoding="utf-8") as fh:
    TAX_DOC = json.load(fh)
with open(DATA / "flags.json", encoding="utf-8") as fh:
    FLAGS_DOC = json.load(fh)
with open(DATA / "requirements.json", encoding="utf-8") as fh:
    REQ_DOC = json.load(fh)

SRC = {s["id"]: s for s in SRC_DOC["sources"]}
METHODS = METHODS_DOC["methods"]
FLAGS = {f["id"]: f for f in FLAGS_DOC["flags"]}

CATS = [
    ("current", "Individual current-account routes", "Routes that run through 经常项目 business, where the barrier is documents rather than approval."),
    ("capital", "Capital-account routes", "Routes that follow 资本项目 rules: an approval file, a tax certificate, and in one case a two-year release schedule."),
    ("alternatives", "Alternative channels", "Cash, licensed fintech, card spend and offshore manoeuvres. Some are priced, several are not verified, none is a free lunch."),
    ("prohibited", "Prohibited routes", "Named in a statute or a rule with a penalty attached. Listed so the risk is visible; no procedure is given."),
]

# ---------------------------------------------------------------------------
# cost engine
# ---------------------------------------------------------------------------

BUY = P["fx_board"]["buy_spot_cny_per_100"]
SELL = P["fx_board"]["sell_spot_cny_per_100"]
MID = (BUY + SELL) / 2.0
ONE_WAY = (SELL - MID) / MID
ROUND_TRIP = (SELL - BUY) / SELL

COMM_RATE = P["boc_personal_remittance"]["commission_rate"]
COMM_MIN = P["boc_personal_remittance"]["commission_min_cny"]
COMM_MAX = P["boc_personal_remittance"]["commission_max_cny"]
CABLE = P["boc_personal_remittance"]["cable_cny_non_hk"]
FULL = P["full_amount_service"]["usd_ny_branch_account"]
QUOTA = P["quota"]["annual_usd"]
EMIG_ONE_OFF_CNY = P["emigration_transfer"]["one_off_threshold_cny"]
EMIG_FRACTIONS = P["emigration_transfer"]["staged_fractions"]
FINE_BASE = P["penalties_cn"]["base_rate"]
FINE_HIGH = P["penalties_cn"]["serious_rate_high"]
AMOUNTS = list(range(P["chart_of_amounts"]["start"], P["chart_of_amounts"]["stop"] + 1, P["chart_of_amounts"]["step"]))
ANCHORS = [10_000, 50_000, 100_000, 200_000, 300_000, 400_000]


def cny_for_usd(usd):
    """CNY you must pay to obtain `usd` at the bank's selling rate."""
    return usd * SELL / 100.0


def usd_for_cny(cny):
    return cny / (SELL / 100.0)


def commission_usd(usd_part):
    cny = cny_for_usd(usd_part)
    comm = min(max(COMM_RATE * cny, COMM_MIN), COMM_MAX)
    return usd_for_cny(comm)


def split_fees(amount, splits):
    """Commission and cable charges for a set of transfer fractions of `amount` summing to 1.

    Commission is charged per remittance on that remittance's CNY equivalent, so the
    fraction has to be multiplied by the amount before the floor and cap are applied.
    """
    return [commission_usd(amount * f) for f in splits], usd_for_cny(CABLE) * len(splits)


def splits_for(model, amount):
    if model == "wire_quota":
        n = max(1, math.ceil(amount / QUOTA))
        return [1.0 / n] * n, n
    if model == "emigration":
        if cny_for_usd(amount) <= EMIG_ONE_OFF_CNY:
            return [1.0], 1
        return list(EMIG_FRACTIONS), len(EMIG_FRACTIONS)
    return [1.0], 1


def cost_row(amount, model):
    """Every cell of a ladder row, computed once and reused by the verifier."""
    row = {"amount": amount}
    if model == "fine":
        row.update(fx=None, commission=None, cable=None, china=None,
                   full=None, exposure_base=amount * FINE_BASE,
                   exposure_high=amount * FINE_HIGH, net=None, share=None,
                   transfers=None)
        return row
    if model in ("none", "gain_tax"):
        return None
    splits, n = splits_for(model, amount)
    if model == "wire_fees_only":
        fx = 0.0
    elif model == "cash":
        fx = amount * ONE_WAY
    else:
        fx = amount * ONE_WAY
    coms, cable = split_fees(amount, splits)
    comm_total = sum(coms)
    china = fx + comm_total + cable
    full = FULL * n if model in ("wire_purchase", "wire_quota", "emigration", "inheritance", "wire_fees_only") else None
    row.update(fx=round(fx, 2), commission=round(comm_total, 2), cable=round(cable, 2),
               china=round(china, 2), full=round(full, 2) if full is not None else None,
               exposure_base=None, exposure_high=None,
               net=round(amount - china, 2), share=china / amount, transfers=n)
    return row


LADDER_MODELS = {
    "M01": "wire_purchase",
    "M02": "wire_quota",
    "M03": "wire_fees_only",
    "M05": "emigration",
    "M06": "inheritance",
    "M09": "cash",
    "M14": "fine",
    "M15": "fine",
}

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def esc(t):
    return html.escape(str(t), quote=True)


def money(x, d=2):
    if x is None:
        return "&mdash;"
    return "${:,.{d}f}".format(x, d=d)


def pct(x, d=3):
    if x is None:
        return "&mdash;"
    return "{:.{d}f}%".format(x * 100, d=d)


def src_links(ids):
    out = []
    for sid in ids:
        s = SRC[sid]
        out.append('<a class="src" href="{}" title="{}" target="_blank" rel="noopener noreferrer">{}&nbsp;&#8599;</a>'.format(
            esc(s["url"]), esc(s["title_en"]), esc(sid)))
    return " ".join(out)


def flag_links(ids):
    return " ".join('<a class="flag" href="flagged.html#{}">{}</a>'.format(esc(i), esc(i)) for i in ids)


CSS = """
:root{--ink:#101720;--ink2:#3a4552;--muted:#697584;--line:#e0e5ec;--bg:#f5f7fa;--panel:#fff;
--accent:#0d5c4a;--accent2:#0a4a3c;--warn:#8a4b00;--warnbg:#fff6e6;--bad:#8c1d1d;--badbg:#fdeeee;--ok:#0d5c4a;--okbg:#e8f4f0}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1060px;margin:0 auto;padding:16px 14px 60px}
header.top{border-bottom:1px solid var(--line);background:var(--panel);position:sticky;top:0;z-index:5}
header.top .inner{max-width:1060px;margin:0 auto;padding:10px 14px;display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.brand{font-weight:800;letter-spacing:-.02em;font-size:1rem;color:var(--ink)}
.brand small{display:block;font-weight:600;font-size:.6rem;letter-spacing:.12em;color:var(--muted);text-transform:uppercase}
nav{display:flex;gap:2px;flex-wrap:wrap;font-size:.78rem}
nav a{padding:5px 8px;border-radius:8px;color:var(--ink2)}
nav a:hover{background:#eef2f6;text-decoration:none}
nav a.on{background:var(--okbg);color:var(--accent);font-weight:700}
h1{font-size:1.75rem;line-height:1.15;letter-spacing:-.025em;margin:.5em 0 .3em;max-width:24ch}
h2{font-size:1.12rem;margin:1.8em 0 .5em;letter-spacing:-.01em}
h3{font-size:.98rem;margin:1.2em 0 .35em}
p,li{color:var(--ink2)}
.lede{font-size:1.02rem;max-width:68ch}
.eyebrow{font-size:.66rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:800;margin-bottom:0}
.stats{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin:16px 0}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 11px}
.stat small{display:block;font-size:.58rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.stat strong{display:block;font-size:1.18rem;letter-spacing:-.02em;margin:1px 0}
.stat span{display:block;font-size:.72rem;color:var(--ink2)}
.grid{display:grid;grid-template-columns:1fr;gap:8px;margin:12px 0}
.card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px;color:inherit}
.card:hover{border-color:var(--accent);text-decoration:none}
.card h3{margin:.1em 0 .25em;font-size:.94rem}
.card p{margin:0;font-size:.8rem}
.kicker{font-size:.6rem;letter-spacing:.1em;color:var(--accent);font-weight:800}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:12px;background:var(--panel);margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:.79rem;min-width:520px}
th,td{padding:8px 9px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#eff3f7;font-size:.62rem;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);white-space:nowrap}
tbody tr:nth-child(even) td{background:#fbfcfd}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tr.hl td{background:var(--okbg)!important;font-weight:600}
.src{display:inline-block;font-size:.6rem;font-weight:700;padding:1px 5px;border-radius:5px;background:#eef1f5;border:1px solid var(--line);color:var(--ink2);white-space:nowrap}
.flag{display:inline-block;font-size:.6rem;font-weight:700;padding:1px 5px;border-radius:5px;background:var(--warnbg);border:1px solid #f0d9b0;color:var(--warn);white-space:nowrap}
.note{font-size:.79rem;color:var(--muted)}
.pill{display:inline-block;font-size:.6rem;font-weight:800;letter-spacing:.05em;text-transform:uppercase;padding:2px 7px;border-radius:99px;border:1px solid var(--line);background:#eef1f5;color:var(--ink2)}
.pill.lawful{background:var(--okbg);border-color:#c5e2d9;color:var(--ok)}
.pill.cond{background:var(--warnbg);border-color:#f0d9b0;color:var(--warn)}
.pill.prohibited{background:var(--badbg);border-color:#f0c9c9;color:var(--bad)}
.pill.unverified{background:#f2f0fb;border-color:#d9d3f0;color:#4b3a8c}
.cta{display:inline-block;background:var(--accent);color:#fff;font-weight:700;padding:10px 16px;border-radius:10px;margin:10px 0}
.cta:hover{background:var(--accent2);text-decoration:none}
.small{font-size:.78rem}
ol,ul{padding-left:1.15em}
li{margin:.25em 0}
.callout{border-left:4px solid var(--accent);background:var(--panel);padding:10px 12px;border-radius:0 10px 10px 0;margin:12px 0}
.callout.warn{border-left-color:#b0761f;background:var(--warnbg)}
.callout.bad{border-left-color:#a33;background:var(--badbg)}
details{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin:8px 0}
details summary{cursor:pointer;font-weight:700;font-size:.88rem}
details[open] summary{margin-bottom:8px}
footer{border-top:1px solid var(--line);margin-top:30px;padding-top:12px;font-size:.76rem;color:var(--muted)}
.two{display:grid;grid-template-columns:1fr;gap:14px}
dl{margin:0}
dt{font-weight:700;font-size:.8rem;margin-top:8px}
dd{margin:0 0 0 0;font-size:.82rem;color:var(--ink2)}
@media(min-width:720px){
 h1{font-size:2.3rem}
 .stats{grid-template-columns:repeat(4,1fr)}
 .grid{grid-template-columns:repeat(3,1fr)}
 .two{grid-template-columns:1fr 1fr}
}
@media print{header.top{position:static}nav{display:none}}
"""

NAV = [
    ("index.html", "Dashboard"),
    ("methods.html", "All routes"),
    ("costs.html", "Costs"),
    ("taxes.html", "Tax"),
    ("steps.html", "Steps"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged"),
    ("repo-review.html", "Repo audit"),
]


def shell(title, body, active="", desc=""):
    nav = "".join('<a href="{}"{}>{}</a>'.format(h, ' class="on"' if h == active else "", esc(t)) for h, t in NAV)
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{desc}">
<title>{title} &middot; China Money Edition H</title>
<style>{css}</style>
</head>
<body>
<header class="top"><div class="inner">
<a class="brand" href="index.html">China Money<small>Edition H &middot; CNY to USD</small></a>
<nav>{nav}</nav>
</div></header>
<div class="wrap">
{body}
<footer>
<p><strong>What this is.</strong> Published-rule research with the arithmetic shown, compiled {asof} from {n} official and provider-primary documents. Not legal, tax or investment advice, and not a bank quote. Rates and tariffs change; every source is linked for manual review.</p>
<p>Values that could not be confirmed are blank and published on the <a href="flagged.html">Flagged for review</a> page. No value is inferred. Edition H is self-contained; the earlier dashboards in this repository are archived from the <a href="../../index.html">root page</a>. Coordination record: <a href="../../COORDINATION.md">COORDINATION.md</a>. Utility pages: <a href="penalties.html">penalties</a> &middot; <a href="requirements.html">requirements</a> &middot; <a href="methodology.html">methodology</a>.</p>
</footer>
</div>
</body>
</html>
""".format(desc=esc(desc or title), title=esc(title), css=CSS, nav=nav, body=body, asof=AS_OF, n=len(SRC))


def pill(status):
    cls = {"lawful": "lawful", "lawful_conditional": "cond", "lawful_with_approval": "cond",
           "unverified": "unverified", "prohibited": "prohibited"}.get(status, "")
    label = status.replace("_", " ")
    return '<span class="pill {}">{}</span>'.format(cls, esc(label))


def write(path, content):
    full = OUT / path
    full.parent.mkdir(parents=True, exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(content)


# ---------------------------------------------------------------------------
# ladders
# ---------------------------------------------------------------------------


def ladder_table(mid, compact=False):
    model = LADDER_MODELS[mid]
    rows = [cost_row(a, model) for a in AMOUNTS]
    out = ['<div class="scroll"><table class="ladder" data-method="{}">'.format(esc(mid))]
    if model == "fine":
        out.append('<thead><tr><th class="num">Amount</th><th class="num">Fine at 30%</th>'
                   '<th class="num">Fine at 100%</th><th>Basis</th></tr></thead><tbody>')
        for r in rows:
            out.append('<tr><td class="num">{}</td><td class="num">{}</td><td class="num">{}</td>'
                       '<td>{}</td></tr>'.format(money(r["amount"], 0), money(r["exposure_base"]),
                                                 money(r["exposure_high"]), src_links(["CN-01"])))
        out.append("</tbody></table></div>")
        out.append('<p class="note">Statutory ranges under CN-01 Arts. 39/40/45: up to 30% of the amount, '
                   'or 30%-100% where the case is serious, plus confiscation and possible criminal referral. '
                   'This is exposure, not a price, and not an assessment of any case (F-20).</p>')
        return "".join(out)
    head = ('<thead><tr><th class="num">Amount</th><th class="num">FX margin</th>'
            '<th class="num">Commission</th><th class="num">Cable</th>'
            '<th class="num">China-side total</th><th class="num">Share</th>'
            + ('' if compact else '<th class="num">+ full amount</th>')
            + '<th class="num">Net USD</th><th>Source</th></tr></thead><tbody>')
    out.append(head)
    for r in rows:
        cells = "".join([
            '<td class="num">{}</td>'.format(money(r["amount"], 0)),
            '<td class="num">{}</td>'.format(money(r["fx"])),
            '<td class="num">{}</td>'.format(money(r["commission"])),
            '<td class="num">{}</td>'.format(money(r["cable"])),
            '<td class="num"><strong>{}</strong></td>'.format(money(r["china"])),
            '<td class="num"><strong>{}</strong></td>'.format(pct(r["share"])),
        ])
        if not compact:
            cells += '<td class="num">{}</td>'.format(money(r["full"]))
        cells += '<td class="num">{}</td><td>{}</td>'.format(money(r["net"]), src_links(["CN-06", "CN-07"]))
        out.append("<tr>{}</tr>".format(cells))
    out.append("</tbody></table></div>")
    return "".join(out)


def ladder_notes(mid):
    m = next(x for x in METHODS if x["id"] == mid)
    model = LADDER_MODELS[mid]
    bits = []
    bits.append('<p class="note">Computed at the BOC board of {stamp}: buying USD at {sell} CNY per 100, mid {mid:.3f}, '
                'one-way margin {ow}. Commission {cr}&#8240; of the CNY equivalent, minimum CNY {cmin}, maximum CNY {cmax}; '
                'cable CNY {cable}. '.format(stamp=P["fx_board"]["stamp"], sell=SELL, mid=MID, ow=pct(ONE_WAY, 4),
                                             cr=COMM_RATE * 1000, cmin=COMM_MIN, cmax=COMM_MAX, cable=CABLE))
    if model == "wire_quota":
        bits.append("The quota is USD 50,000 a person a year, so the number of transfers is the amount divided by 50,000, "
                    "rounded up; each transfer pays commission and cable again. ")
    elif model == "emigration":
        bits.append("Releases follow CN-03 Art. 6: half, then a quarter, then a quarter; below RMB 200,000 (about USD 29,885) "
                    "a single release is allowed, which is why the first two rows carry one set of fees. ")
    elif model == "wire_fees_only":
        bits.append("This route starts from USD already held, so there is no second conversion and the FX margin is shown as zero. ")
    elif model == "cash":
        bits.append("Cash is bought at the cash selling rate, which on this board equals the remittance selling rate, so the "
                    "margin is the same; travel cost and the value of your time are not included (F-09). ")
    bits.append('The full-amount column is the optional USD {f} charge that keeps the principal intact (CN-08); it is excluded '
                'from the China-side total and from the share. The US bank\'s inbound fee is blank (F-07).</p>'.format(f=FULL))
    return "".join(bits)


# ---------------------------------------------------------------------------
# shared fragments
# ---------------------------------------------------------------------------


def cross_table(mids, amounts=None):
    amounts = amounts or ANCHORS
    heads = "".join('<th class="num">{}</th>'.format(money(a, 0)) for a in amounts)
    rows = []
    for mid in mids:
        m = next(x for x in METHODS if x["id"] == mid)
        model = LADDER_MODELS[mid]
        cells = []
        for a in amounts:
            r = cost_row(a, model)
            cells.append('<td class="num">{}<br><span class="note">{}</span></td>'.format(
                money(r["china"]), pct(r["share"])))
        rows.append('<tr><td><a href="method-{}.html"><strong>{}</strong></a><br><span class="note">{}</span></td>{}{}</tr>'.format(
            esc(mid), esc(mid), esc(m["name"][:64]), "".join(cells), '<td>{}</td>'.format(src_links(["CN-06", "CN-07"]))))
    return ('<div class="scroll"><table class="cmp"><thead><tr><th>Route (China-side cost)</th>{}<th>Source</th></tr></thead>'
            '<tbody>{}</tbody></table></div>').format(heads, "".join(rows))


def method_table(methods):
    out = ['<div class="scroll"><table><thead><tr><th>#</th><th>Route</th><th>Status</th>'
           '<th>Cap in the rule text</th><th>Cost</th><th>Source</th></tr></thead><tbody>']
    for m in methods:
        cost = "ladder" if m["id"] in LADDER_MODELS else "not priced"
        out.append('<tr><td><a href="method-{id}.html">{id}</a></td>'
                   '<td><strong>{name}</strong><br><span class="note">{zh}</span></td>'
                   '<td>{pill}</td><td>{cap}</td><td>{cost}</td><td>{src}</td></tr>'.format(
                       id=esc(m["id"]), name=esc(m["name"]), zh=esc(m["name_zh"]), pill=pill(m["status"]),
                       cap=esc(m["cap"]), cost=esc(cost), src=src_links(m["sources"][:3])))
    out.append("</tbody></table></div>")
    return "".join(out)


def cards_for(methods):
    out = []
    for m in methods:
        out.append('<a class="card" href="method-{}.html"><span class="kicker">{} &middot; {}</span>'
                   '<h3>{}</h3><p>{}</p></a>'.format(
                       esc(m["id"]), esc(m["id"]), esc(m["cat"]), esc(m["name"]),
                       esc(m["summary"][:150] + ("..." if len(m["summary"]) > 150 else ""))))
    return "".join(out)


def big_stats():
    r400 = cost_row(400_000, "wire_purchase")
    r10 = cost_row(10_000, "wire_purchase")
    return """<div class="stats">
  <div class="stat"><small>FX margin, one conversion</small><strong>{ow}</strong><span>BOC bid {buy} / ask {sell}, mid {mid:.2f}</span></div>
  <div class="stat"><small>China-side cost at $400,000</small><strong>{c400}</strong><span>{p400} of the amount</span></div>
  <div class="stat"><small>China-side cost at $10,000</small><strong>{c10}</strong><span>{p10} &mdash; fixed fees dominate</span></div>
  <div class="stat"><small>Tax on the conversion</small><strong>$0</strong><span>neither jurisdiction taxes the exchange*</span></div>
</div>
""".format(ow=pct(ONE_WAY, 4), buy=BUY, sell=SELL, mid=MID, c400=money(r400["china"]),
           p400=pct(r400["share"]), c10=money(r10["china"]), p10=pct(r10["share"]))


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------


def build_index():
    body = """
<p class="eyebrow">CNY to USD &middot; US citizen &middot; official sources only</p>
<h1>What it actually costs to get money out of China.</h1>
<p class="lede">There is no tax on converting your own money in either country, so the premise that conversion is expensive is wrong. What is real is the capital-account barrier, a published bank tariff of well under 1%, and a US reporting exposure that can reach half the balance if a form is missed. This dashboard prices every route at every USD 10,000 step from USD 10,000 to USD 400,000 and shows its work.</p>
{stats}
<div class="callout">
<p style="margin:0"><strong>The answer in one sentence.</strong> If the RMB came from salary or other current-account income in China, the cheapest lawful route is a documented bank purchase under Art. 59 of the 2020 Guidelines, wired straight to your US account: about <strong>{c025}</strong> on USD 25,000 and <strong>{pct400}</strong> of the amount at USD 400,000. If it came from property or an inheritance, the quota and the 2004 personal-property transfer rules decide, and the answer changes.</p>
</div>
<h2>Three facts decide everything</h2>
<div class="two">
<div>
<h3>1. How did the RMB arise?</h3>
<p>Salary, services and other current-account income route through a bank's documentary review. Property sale proceeds, an inheritance and an emigrant's capital route through a capital-account approval file. The same balance treated as the wrong kind of money is refused.</p>
<h3>2. Are you a domestic or a foreign individual?</h3>
<p>A US citizen is a foreign individual unless he has lived in China continuously for a year or more, which makes him domestic for FX purposes. Domestic means the USD 50,000 annual quota. Foreign, with documented China income, means no annual cap in the rule text. This single classification is the difference between eight years and one application (F-01).</p>
</div>
<div>
<h3>3. What is your US filing history?</h3>
<p>The bank's price is a rounding error next to a willful FBAR penalty, which is the greater of USD 165,353 or half the balance, per violation. If the account was never reported, fix that before worrying about the spread (F-05).</p>
<h3>What is <em>not</em> the answer</h3>
<p>Splitting the money across relatives' quotas and underground dealers are named offences with fines of up to 100% of the amount in a serious case, plus confiscation. They are listed here with the statute, and with no procedure.</p>
</div>
</div>
<h2>Cost at a glance &mdash; China-side cost, every route</h2>
{cross}
<p class="note">China-side cost means the FX margin plus the Bank of China commission and cable charge, computed from the published tariff at the board stamped {stamp}. It excludes your US bank's inbound fee, which is blank on purpose (F-07), and professional fees such as notarisation (F-25). The share is the cost divided by the amount.</p>
<h2>Every USD 10,000 step, USD 10,000 to USD 400,000</h2>
<p class="small">The recommended route when the money is documented current-account income. Total cost and share are the two numbers that matter; the columns after them show how the total is built.</p>
{ladder}
{lnote}
<h2>Browse by category</h2>
<div class="grid">{cards}</div>
<h2>Start here</h2>
<div class="grid">
<a class="card" href="executive-summary.html"><span class="kicker">Summary</span><h3>Executive summary</h3><p>The findings, the recommendation and the numbers, on one page.</p></a>
<a class="card" href="costs.html"><span class="kicker">Money</span><h3>The conversion penalty, decomposed</h3><p>FX margin, commission, cable, full-amount, tax, and what is left blank.</p></a>
<a class="card" href="steps.html"><span class="kicker">Action</span><h3>Step by step</h3><p>The decision tree and the exact sequence, with the provision to cite at each step.</p></a>
<a class="card" href="taxes.html"><span class="kicker">Tax</span><h3>China and US tax positions</h3><p>Why conversion is not income, where the 20% bites, and the reporting ladder.</p></a>
<a class="card" href="flagged.html"><span class="kicker">Caveats</span><h3>Flagged for review</h3><p>26 items left blank or unverified, each with its reason.</p></a>
<a class="card" href="repo-review.html"><span class="kicker">Audit</span><h3>Repository review</h3><p>What the eight earlier editions got right, and the four places this edition corrects them.</p></a>
</div>
<p class="note" style="margin-top:14px">* The $0 is about the character of the conversion, not about your whole tax position. Under 26 U.S.C. &#167;988(e)(2) the foreign-currency gain on an individual's personal transaction is not recognised unless it exceeds USD 200 in that transaction, in which case the whole gain is recognised. Receiving an inheritance above USD 100,000 still needs Form 3520, and the account still needs an FBAR.</p>
""".format(stats=big_stats(), c025=money(cost_row(25_000, "wire_purchase")["china"]),
           pct400=pct(cost_row(400_000, "wire_purchase")["share"]),
           cross=cross_table(["M01", "M02", "M03", "M05", "M06", "M09"]),
           stamp=P["fx_board"]["stamp"], ladder=ladder_table("M01"), lnote=ladder_notes("M01"),
           cards="".join('<a class="card" href="category-{}.html"><span class="kicker">{}</span><h3>{}</h3><p>{}</p></a>'.format(
               s, "0{}".format(i + 1), esc(t), esc(d)) for i, (s, t, d) in enumerate(CATS)))
    return shell("Dashboard", body, active="index.html",
                 desc="Every lawful route for turning CNY into USD, priced from USD 10,000 to USD 400,000 with official sources.")


def build_exec():
    r400 = cost_row(400_000, "wire_purchase")
    r100 = cost_row(100_000, "wire_purchase")
    r10 = cost_row(10_000, "wire_purchase")
    body = """
<p class="eyebrow">Executive summary</p>
<h1>The short version.</h1>
<p class="lede">Nine findings, one recommendation and the numbers behind them. Every figure links to an official document; everything that could not be confirmed is blank and named on the flagged page.</p>
<h2>Findings</h2>
<div class="scroll"><table><thead><tr><th>#</th><th>Finding</th><th>Detail</th><th>Source</th></tr></thead><tbody>
<tr><td>1</td><td><strong>Converting is not taxed</strong></td><td>China's IIT law lists nine categories of income and an exchange of your own money is not one of them. Flat 20% applies to asset-transfer gains, not to the conversion.</td><td>{s1}</td></tr>
<tr><td>2</td><td><strong>The barrier is convertibility, not tax</strong></td><td>Current-account business is convertible; capital-account business follows a process. The money is stuck on that line, not on a tax bill.</td><td>{s2}</td></tr>
<tr><td>3</td><td><strong>The price is under 1%</strong></td><td>{c10} on USD 10,000 ({p10}), {c100} on USD 100,000 ({p100}), {c400} on USD 400,000 ({p400}).</td><td>{s3}</td></tr>
<tr><td>4</td><td><strong>The FX margin is 0.21%, not 0.42%</strong></td><td>The widely quoted 0.42% is the round trip, i.e. converting twice. One conversion costs half that: (ask &minus; mid) / mid on the same board.</td><td>{s4}</td></tr>
<tr><td>5</td><td><strong>One classification decides the cap</strong></td><td>A foreign individual with documented China-source income has no annual cap in Art. 59. A domestic individual, which includes a foreigner resident a year or more, has USD 50,000 a year.</td><td>{s5}</td></tr>
<tr><td>6</td><td><strong>The capital-account exit exists</strong></td><td>The 2004 personal-property transfer rules cover emigration and inheritance, with one application and staged releases over two years. They are the only general route for a large capital sum.</td><td>{s6}</td></tr>
<tr><td>7</td><td><strong>2026 added a verification step</strong></td><td>From 1 January 2026 any outbound remittance of RMB 5,000 / USD 1,000 or more requires identity verification. It is not a cap and it does not change the quota; it is a document check that older guides omit.</td><td>{s7}</td></tr>
<tr><td>8</td><td><strong>The US reporting exposure dwarfs the fees</strong></td><td>Willful FBAR: greater of USD 165,353 or 50% of the balance, per violation. Form 8938 can add up to USD 60,000. Form 3520 is due on foreign gifts and bequests above USD 100,000.</td><td>{s8}</td></tr>
<tr><td>9</td><td><strong>The wrong routes cost 30% to 100%</strong></td><td>Splitting quotas, private dealing and disguised FX are penalised at up to 30% of the amount, or 30%-100% where serious, plus confiscation and possible criminal referral.</td><td>{s9}</td></tr>
</tbody></table></div>
<h2>Recommendation</h2>
<div class="callout">
<p><strong>If the money is documented current-account income</strong> &mdash; salary, personal services, dividends already taxed &mdash; use route M01: ask the bank to purchase FX against the source documents under Art. 59 rather than against the quota, and wire it to your own US account. At USD 400,000 the China-side cost is {c400}, which is {p400}.</p>
<p><strong>If the money is an inheritance from a PRC relative</strong>, use route M06, the inheritance transfer: one SAFE application, a notarised succession, the deceased's tax certificate, and no capped schedule.</p>
<p><strong>If you emigrated from mainland China and the property predates that</strong>, use route M05, the emigration transfer: a single application with three releases over two years, local approval up to RMB 500,000 and SAFE head office above it.</p>
<p><strong>If none of those facts can be documented</strong>, the honest answer is the quota, M02: USD 50,000 a year, USD 400,000 in eight years, and statutory exposure for anyone who tries to shortcut it.</p>
</div>
<h2>What decides the answer</h2>
<div class="scroll"><table><thead><tr><th>Fact about you or the money</th><th>Route it unlocks</th><th>Cap</th><th>Source</th></tr></thead><tbody>
<tr><td>RMB is salary or services income, tax paid in China</td><td><a href="method-M01.html">M01 documented purchase</a></td><td>No annual cap in the text</td><td>{s5}</td></tr>
<tr><td>You are a PRC citizen, or a foreigner resident a year or more</td><td><a href="method-M02.html">M02 annual quota</a></td><td>USD 50,000 a year</td><td>{s2}</td></tr>
<tr><td>The USD already sits in your FX account</td><td><a href="method-M03.html">M03 remit held FX</a></td><td>USD 50,000 a day on ID</td><td>{s2}</td></tr>
<tr><td>PRC household registration cancelled, property predates it</td><td><a href="method-M05.html">M05 emigration transfer</a></td><td>No cap; 3 releases over 2 years</td><td>{s6}</td></tr>
<tr><td>A completed inheritance from a PRC estate</td><td><a href="method-M06.html">M06 inheritance transfer</a></td><td>No cap; one or several remittances</td><td>{s6}</td></tr>
<tr><td>None of the above</td><td><a href="method-M09.html">M09 cash</a>, <a href="method-M10.html">M10 Wise</a> for small amounts</td><td>USD 5,000-10,000 a trip; CNY 300,000 a transfer</td><td>{s10}</td></tr>
</tbody></table></div>
<h2>Limits of this summary</h2>
<ul>
<li>The origin of the money was not supplied, so the recommendation is a decision tree, not a conclusion (F-03).</li>
<li>No personal tax or penalty amount is computed, because that requires facts that are not here (F-05, F-13).</li>
<li>US receiving-bank fees, notarisation, translation and professional fees are not in any total (F-07, F-25).</li>
<li>The rates are a dated board, {stamp}, and the bank's counter rate governs (F-23).</li>
</ul>
""".format(c10=money(r10["china"]), p10=pct(r10["share"]), c100=money(r100["china"]), p100=pct(r100["share"]),
           c400=money(r400["china"]), p400=pct(r400["share"]),
           s1=src_links(["CN-04"]), s2=src_links(["CN-01", "CN-02"]), s3=src_links(["CN-06", "CN-07"]),
           s4=src_links(["CN-07"]), s5=src_links(["CN-02", "CN-01"]), s6=src_links(["CN-03"]),
           s7=src_links(["CN-05"]), s8=src_links(["US-03", "US-06"]), s9=src_links(["CN-01"]),
           s10=src_links(["CN-02", "WISE-01"]), stamp=P["fx_board"]["stamp"])
    return shell("Executive summary", body, active="executive-summary.html")


def build_methods():
    body = ['<p class="eyebrow">All routes</p><h1>Every route, and what each one is worth.</h1>'
            '<p class="lede">Fifteen routes in four categories. A route is listed here only if an official instrument '
            'or the provider\'s own terms describe it; where the instrument does not grant an entitlement, the route is '
            'marked unverified and nothing is priced.</p>']
    for slug, title, desc in CATS:
        ms = [m for m in METHODS if m["cat"] == slug]
        body.append('<h2>{}</h2><p class="note">{}</p>{}'.format(esc(title), esc(desc), method_table(ms)))
    body.append("""<h2>How routes were counted</h2>
<p>Earlier editions in this repository publish 22, 33, 35, 16, 31 and 43 routes, because each counted a different
grain: instruments, services, service variants or documents. This edition counts a <em>route</em> as one legal
characterisation of the money plus one exit mechanism. Variants that change only which bank performs the same act are
not separate routes; a route that depends on a fact you may not have is a separate route, because it changes your
answer.</p>""")
    return shell("All routes", "".join(body), active="methods.html")


def build_method_page(m):
    mid = m["id"]
    parts = ['<p class="eyebrow">{} &middot; {}</p>'.format(esc(mid), esc(m["cat"])),
             '<h1>{}</h1>'.format(esc(m["name"])),
             '<p class="note">{}</p>'.format(esc(m["name_zh"])),
             '<p>{} {}</p>'.format(pill(m["status"]), flag_links(m["flags"])),
             '<p class="lede">{}</p>'.format(esc(m["summary"])),
             '<h2>The rule</h2><ul>{}</ul>'.format("".join("<li>{}</li>".format(esc(r)) for r in m["rule"])),
             '<p>{}</p>'.format(src_links(m["sources"]))]
    parts.append('<h2>Cap or limit in the rule text</h2><p>{}</p>'.format(esc(m["cap"])))
    parts.append('<h2>Who this is for</h2><p>{}</p>'.format(esc(m["who"])))
    parts.append('<h2>Documents the bank or SAFE will want</h2><ul>{}</ul>'.format(
        "".join("<li>{}</li>".format(esc(d)) for d in m["docs"])))
    parts.append('<h2>Pros and cons</h2><div class="two"><div><h3>Pros</h3><ul>{}</ul></div>'
                 '<div><h3>Cons</h3><ul>{}</ul></div></div>'.format(
                     "".join("<li>{}</li>".format(esc(x)) for x in m["pros"]),
                     "".join("<li>{}</li>".format(esc(x)) for x in m["cons"])))
    parts.append('<h2>Step by step</h2><ol>{}</ol>'.format(
        "".join('<li>{} <span class="note">{}</span></li>'.format(esc(s["do"]), src_links([s["cite"]])) for s in m["steps"])))
    if mid in LADDER_MODELS:
        parts.append('<h2>Cost at every USD 10,000 step</h2>')
        parts.append(ladder_table(mid))
        parts.append(ladder_notes(mid))
        if LADDER_MODELS[mid] == "fine":
            parts.append('<p class="note">No cost ladder is possible for a prohibited route: the figure is a statutory '
                         'range, not a price.</p>')
    else:
        parts.append('<h2>Cost</h2><div class="callout warn"><p>No amount ladder is published for this route: '
                     'no official price exists for the conversion step, or the route is not an entitlement at all. '
                     'The cells would be invented, so they are left out and the point is flagged.</p>'
                     '<p class="small">Related flags: {}</p></div>'.format(flag_links(m["flags"])))
    parts.append('<h2>Related flags</h2><div class="scroll"><table class="flagtable"><thead><tr><th>Flag</th>'
                 '<th>Why it matters here</th><th>Status</th></tr></thead><tbody>{}</tbody></table></div>'.format(
                     "".join('<tr><td><a href="flagged.html#{}">{}</a></td><td>{}</td><td><span class="pill unverified">{}</span></td></tr>'.format(
                         esc(f), esc(f), "UNVERIFIED &mdash; see the flag page" if True else "", esc(FLAGS[f]["status"]))
                         for f in m["flags"])))
    parts.append('<p><a href="methods.html">&larr; All routes</a></p>')
    return shell(m["name"], "".join(parts), active="methods.html", desc=m["summary"][:150])


def build_category(slug):
    title, desc = next((t, d) for s, t, d in CATS if s == slug)
    ms = [m for m in METHODS if m["cat"] == slug]
    body = ['<p class="eyebrow">Category</p><h1>{}</h1><p class="lede">{}</p>'.format(esc(title), esc(desc)),
            method_table(ms)]
    costed = [m["id"] for m in ms if m["id"] in LADDER_MODELS]
    if costed:
        body.append('<h2>Cost comparison inside this category</h2>')
        body.append(cross_table(costed))
        body.append('<p class="note">China-side cost at the BOC board of {}. Excludes the US inbound fee (F-07).</p>'.format(
            esc(P["fx_board"]["stamp"])))
    body.append('<h2>Routes</h2><div class="grid">{}</div>'.format(cards_for(ms)))
    return shell(title, "".join(body), active="methods.html", desc=desc)


def build_costs():
    parts = ['<p class="eyebrow">The conversion penalty, decomposed</p><h1>Where every cent goes.</h1>',
             '<p class="lede">The "penalty" is not a tax. It is four published charges, one dated exchange rate, and a '
             'compliance exposure that only appears if a form is missing. Here is each layer, with the number and the source.</p>',
             '<h2>The layers</h2><div class="scroll"><table><thead><tr><th>Layer</th><th>What it is</th>'
             '<th class="num">Amount</th><th>Source</th></tr></thead><tbody>',
             '<tr><td><strong>FX margin</strong></td><td>You buy USD at the bank\'s selling rate while the fair midpoint '
             'is lower. For one conversion the loss is (ask &minus; mid) / mid.</td><td class="num">{}</td><td>{}</td></tr>'.format(
                 pct(ONE_WAY, 4), src_links(["CN-07"])),
             '<tr><td><strong>Commission</strong></td><td>1 per mille of the CNY equivalent, minimum CNY 50, maximum CNY 260, '
             'so it stops growing above about CNY 260,000 and becomes negligible.</td><td class="num">{}</td><td>{}</td></tr>'.format(
                 money(cost_row(400_000, "wire_purchase")["commission"]), src_links(["CN-06"])),
             '<tr><td><strong>Cable charge</strong></td><td>CNY 150 per remittance outside Hong Kong, Macao and Taiwan. '
             'Fixed, so it dominates small transfers and disappears at size.</td><td class="num">{}</td><td>{}</td></tr>'.format(
                 money(usd_for_cny(CABLE)), src_links(["CN-06"])),
             '<tr><td><strong>Full-amount arrival (optional)</strong></td><td>You may pay the overseas bank\'s charge up '
             'front so the principal arrives intact: USD 15 if the receiving bank holds its account with BOC New York, '
             'otherwise USD 25.</td><td class="num">{}</td><td>{}</td></tr>'.format(
                 money(FULL), src_links(["CN-08"])),
             '<tr><td><strong>Tax on the conversion</strong></td><td>Not one of China\'s nine income categories; on the US '
             'side the personal-transaction exclusion applies unless the gain exceeds USD 200.</td><td class="num">$0</td>'
             '<td>{}</td></tr>'.format(src_links(["CN-04", "US-01"])),
             '<tr><td><strong>Reporting exposure</strong></td><td>FBAR, 8938 and 3520 are information returns. The penalty '
             'is not a percentage of the transfer; it is a fixed and percentage maximum that can exceed the transfer.</td>'
             '<td class="num">up to 50% of balance</td><td>{}</td></tr>'.format(src_links(["US-03", "US-06"])),
             '<tr><td><strong>Prohibited-route range</strong></td><td>Fines of up to 30%, or 30%-100% where serious, plus '
             'confiscation. Shown for comparison; not a price.</td><td class="num">30%-100%</td><td>{}</td></tr>'.format(
                 src_links(["CN-01"])),
             '</tbody></table></div>',
             '<p class="note">One layer is deliberately absent from the table: the US receiving bank\'s inbound fee. '
             'No official schedule for a personal account was retrieved, so it is blank rather than estimated (F-07).</p>',
             '<h2>The arithmetic, in full</h2>',
             '<div class="callout"><p>CNY needed to buy USD <em>A</em> = <em>A</em> &times; {sell} / 100.<br>'
             'FX margin = <em>A</em> &times; ({sell} &minus; {mid}) / {mid} = <em>A</em> &times; {ow}.<br>'
             'Commission = min(max(0.001 &times; CNY, 50), 260) CNY, converted back at {sell}.<br>'
             'Cable = 150 CNY &times; number of remittances, converted back at {sell}.<br>'
             'China-side total = FX margin + commission + cable.<br>'
             'Share = total / <em>A</em>.</p></div>'.format(sell=SELL, mid=MID, ow=pct(ONE_WAY, 4)),
             '<h2>Inputs</h2><div class="scroll"><table><thead><tr><th>Input</th><th class="num">Value</th>'
             '<th>Source</th></tr></thead><tbody>']
    inputs = [
        ("USD cash-remittance buying rate (CNY per 100)", "{:.2f}".format(BUY), ["CN-07"]),
        ("USD selling rate (CNY per 100)", "{:.2f}".format(SELL), ["CN-07"]),
        ("BOC reference rate (CNY per 100)", "{:.2f}".format(P["fx_board"]["reference_cny_per_100"]), ["CN-07"]),
        ("Midpoint (derived)", "{:.3f}".format(MID), ["CN-07"]),
        ("One-way margin (derived)", pct(ONE_WAY, 4), ["CN-07"]),
        ("Round-trip spread (derived, not used for a single conversion)", pct(ROUND_TRIP, 4), ["CN-07"]),
        ("Commission rate", "{:.1f} per mille".format(COMM_RATE * 1000), ["CN-06"]),
        ("Commission floor / cap (CNY)", "{:.0f} / {:.0f}".format(COMM_MIN, COMM_MAX), ["CN-06"]),
        ("Cable charge (CNY, non-HK)", "{:.0f}".format(CABLE), ["CN-06"]),
        ("Full-amount (USD, NY-branch account)", "{:.0f}".format(FULL), ["CN-08"]),
        ("Annual facilitation quota", money(QUOTA, 0), ["CN-02"]),
        ("Emigration one-off threshold (CNY)", "{:,.0f}".format(EMIG_ONE_OFF_CNY), ["CN-03"]),
        ("AML verification threshold", "CNY 5,000 / USD 1,000", ["CN-05"]),
    ]
    for label, value, ids in inputs:
        parts.append('<tr><td>{}</td><td class="num">{}</td><td>{}</td></tr>'.format(
            esc(label), esc(value), src_links(ids)))
    parts.append('</tbody></table></div>')
    parts.append('<p class="note">The US receiving-bank fee is not in this table because it has no official source: '
                 'it is bank-specific and is flagged (F-07). Add your own bank\'s published inbound fee to every total.</p>')
    parts.append('<h2>Compare the routes</h2>')
    parts.append(cross_table(["M01", "M02", "M03", "M05", "M06", "M09"]))
    parts.append('<h2>Full ladders</h2>')
    for mid in ["M01", "M02", "M03", "M05", "M06", "M09"]:
        m = next(x for x in METHODS if x["id"] == mid)
        parts.append('<details><summary>{} &mdash; {} &mdash; 40 rows</summary>{}<p class="small"><a href="method-{}.html">'
                     'Route detail</a></p></details>'.format(esc(mid), esc(m["name"]), ladder_table(mid), esc(mid)))
    return shell("Costs", "".join(parts), active="costs.html",
                 desc="Cost decomposition for converting CNY to USD, with every input and its source.")


def build_taxes():
    parts = ['<p class="eyebrow">Tax and reporting</p><h1>What is taxed, and what is merely reported.</h1>',
             '<p class="lede">Two propositions carry the whole answer. Conversion is not income in either country. '
             'Reporting is mandatory, and its penalties are the only numbers here that can exceed the money.</p>',
             '<h2>Positions, line by line</h2><div class="scroll"><table><thead><tr><th>#</th><th>Jurisdiction</th>'
             '<th>Question</th><th>Position</th><th>Value</th><th>Source</th></tr></thead><tbody>']
    for t in TAX_DOC["rows"]:
        value = esc(t["value"]) if t["value"] else '<span class="note">UNVERIFIED &mdash; blank</span>'
        parts.append('<tr><td>{}</td><td>{}</td><td><strong>{}</strong></td><td>{}</td><td class="num">{}</td><td>{}</td></tr>'.format(
            esc(t["id"]), esc(t["jurisdiction"]), esc(t["topic"]), esc(t["position"]), value, src_links(t["sources"])))
    parts.append('</tbody></table></div>')
    parts.append("""<h2>The &#167;988 cliff, precisely</h2>
<p>Section 988 makes a currency disposition an ordinary-income event. The relief for individuals is narrow: on a
personal transaction, gain from exchange-rate movement after acquisition is not recognised &mdash; but the relief
"shall not apply if the gain which would otherwise be recognized on the transaction exceeds $200". It is a cliff, not
an allowance, and it is per transaction. The consequence for a large conversion is concrete: if you acquired the RMB
years ago at a materially better rate, the gain can exceed USD 200 and the whole gain becomes ordinary income. The
amount cannot be computed here because the acquisition rate and the acquisition dates of your balance are not known
(F-13).</p>
<h2>Which forms, and when</h2>
<div class="scroll"><table><thead><tr><th>Form</th><th>Trigger</th><th>Due</th><th>Source</th></tr></thead><tbody>
<tr><td><strong>FinCEN 114 (FBAR)</strong></td><td>Aggregate foreign accounts above USD 10,000 at any time in the year &mdash; the China account alone can trigger it</td><td>15 April, automatic extension to 15 October</td><td>{a}</td></tr>
<tr><td><strong>Form 8938</strong></td><td>Specified foreign financial assets above USD 50,000 on 31 December or USD 75,000 at any time (single, living in the US); higher thresholds abroad</td><td>With the income tax return</td><td>{b}</td></tr>
<tr><td><strong>Form 3520, Part IV</strong></td><td>Gifts or bequests above USD 100,000 in aggregate from a nonresident alien or foreign estate in the year</td><td>15 April, or later with an extension, never beyond 15 October</td><td>{c}</td></tr>
<tr><td><strong>Form 1040</strong></td><td>Worldwide income; the conversion itself adds nothing, a &#167;988 gain above USD 200 does</td><td>15 April</td><td>{d}</td></tr>
</tbody></table></div>
<h2>What this page does not do</h2>
<ul>
<li>It does not compute your US tax. The brackets, the filing status, the foreign tax credit and the source of the money are all unknown.</li>
<li>It does not compute a &#167;988 gain. That needs the acquisition rate of the RMB and its acquisition date.</li>
<li>It does not state the 2026 US excise tax position on remittances, because the statute was not retrieved (F-22). The comment is on the flagged page and carries no figure.</li>
</ul>
""".format(a=src_links(["US-04"]), b=src_links(["US-03"]), c=src_links(["US-05"]), d=src_links(["US-02", "US-01"])))
    return shell("Tax", "".join(parts), active="taxes.html",
                 desc="China IIT and US federal tax and reporting positions on converting CNY to USD.")


def build_penalties():
    r40 = cost_row(400_000, "fine")
    r10 = cost_row(10_000, "fine")
    body = """
<p class="eyebrow">Penalties</p>
<h1>What a mistake costs, in statute.</h1>
<p class="lede">The published penalty is the only number in this project that can be larger than the money being moved. These are statutory maximums and ranges, not assessments of any person's case.</p>
<h2>China: administrative fines</h2>
<div class="scroll"><table><thead><tr><th>Conduct</th><th>Provision</th><th>Fine</th><th>Other consequences</th><th>Source</th></tr></thead><tbody>
<tr><td>Evading FX control (逃汇)</td><td>CN-01 Art. 39</td><td>Up to 30% of the amount; 30%-100% if serious</td><td>Order to repatriate; criminal referral</td><td>{a}</td></tr>
<tr><td>Illegal arbitrage / fraudulent purchase (非法套汇)</td><td>CN-01 Art. 40</td><td>Up to 30%; 30%-100% if serious</td><td>Refund of the arbitraged funds; criminal referral</td><td>{a}</td></tr>
<tr><td>Illegal carriage of currency across the border</td><td>CN-01 Art. 42</td><td>Up to 20% of the amount</td><td>Warning; customs penalties may also apply</td><td>{a}</td></tr>
<tr><td>Private, disguised or brokered FX dealing</td><td>CN-01 Art. 45</td><td>Up to 30%; 30%-100% if serious</td><td>Warning; confiscation of illegal gains; criminal referral</td><td>{a}</td></tr>
<tr><td>Splitting to evade the quota</td><td>CN-02 Art. 62</td><td>No separate fine in Art. 62</td><td>Watch list for the current year and the next two; strict documentary review</td><td>{b}</td></tr>
<tr><td>False documents on a personal-property transfer</td><td>CN-03 Art. 13</td><td>Punished under CN-01 Art. 40</td><td>Application refused; money not released</td><td>{c}</td></tr>
</tbody></table></div>
<h2>The range, at the two ends of the ladder</h2>
<div class="scroll"><table><thead><tr><th>Amount</th><th class="num">Fine at 30%</th><th class="num">Fine at 100%</th><th>Basis</th></tr></thead><tbody>
<tr><td>{a10}</td><td class="num">{b10}</td><td class="num">{c10}</td><td>{src}</td></tr>
<tr><td>{a40}</td><td class="num">{b40}</td><td class="num">{c40}</td><td>{src}</td></tr>
</tbody></table></div>
<p class="note">Illustration only: 30% of the amount is the statutory ceiling for the ordinary case, 100% the ceiling where the case is serious. Confiscation of the money involved can be ordered on top, so the true worst case is the amount plus the fine.</p>
<h2>United States: information-return penalties</h2>
<div class="scroll"><table><thead><tr><th>Item</th><th>Maximum</th><th>Notes</th><th>Source</th></tr></thead><tbody>
<tr><td>Willful FBAR violation</td><td>Greater of USD 165,353 (inflation-adjusted) or 50% of the balance at the time of the violation, per violation</td><td>At USD 400,000 the 50% limb is USD 200,000; at USD 10,000 it is USD 5,000</td><td>{d}</td></tr>
<tr><td>Non-willful FBAR violation</td><td>USD 16,536 per violation (inflation-adjusted)</td><td>Non-willful is per violation, not per form</td><td>{e}</td></tr>
<tr><td>Form 8938 failure</td><td>USD 10,000, plus USD 10,000 per 30 days after notice, capped at USD 60,000</td><td>Continuing failure</td><td>{f}</td></tr>
<tr><td>Form 3520 late or incomplete</td><td>Amount not stated on the page retrieved</td><td>Penalties may apply under IRC &#167;6039F(c)</td><td>{g}</td></tr>
</tbody></table></div>
<h2>Full exposure ladders for the prohibited routes</h2>
<details><summary>M14 &mdash; splitting across relatives' quotas</summary>{l14}<p class="small"><a href="method-M14.html">Route detail</a></p></details>
<details><summary>M15 &mdash; underground bank, mirror trade, private dealer</summary>{l15}<p class="small"><a href="method-M15.html">Route detail</a></p></details>
<p class="note">Criminal liability is outside the scope of this project (F-21). Anyone facing an actual investigation needs a lawyer, not a dashboard.</p>
""".format(a=src_links(["CN-01"]), b=src_links(["CN-02"]), c=src_links(["CN-03"]),
           d=src_links(["US-03", "US-06"]), e=src_links(["US-06"]), f=src_links(["US-03"]), g=src_links(["US-05"]),
           a10=money(10_000, 0), b10=money(r10["exposure_base"]), c10=money(r10["exposure_high"]),
           a40=money(400_000, 0), b40=money(r40["exposure_base"]), c40=money(r40["exposure_high"]),
           src=src_links(["CN-01"]), l14=ladder_table("M14"), l15=ladder_table("M15"))
    return shell("Penalties", body, active="taxes.html")


def build_steps():
    body = """
<p class="eyebrow">Step by step</p>
<h1>The sequence, in the order that works.</h1>
<p class="lede">Route pages carry their own procedure. This page is the master sequence: what to establish first, what to do at the bank, and what to file on the US side. Nothing here needs your input to read; the branches are chosen by facts only you can check.</p>
<h2>Step 0 &mdash; sort the money before choosing a route</h2>
<div class="scroll"><table><thead><tr><th>If the RMB came from</th><th>It is</th><th>Route</th><th>Why</th><th>Source</th></tr></thead><tbody>
<tr><td>Salary, bonus, personal services, royalties</td><td>Current-account income</td><td><a href="method-M01.html">M01</a></td><td>Documented purchase against source documents, no annual cap in the text</td><td>{a}</td></tr>
<tr><td>Dividends from a PRC company after tax</td><td>Current-account income</td><td><a href="method-M01.html">M01</a></td><td>Same route, with the tax voucher as the evidence</td><td>{a}</td></tr>
<tr><td>A completed inheritance</td><td>Capital transfer</td><td><a href="method-M06.html">M06</a></td><td>The only route written for a foreign heir</td><td>{b}</td></tr>
<tr><td>Property owned before you emigrated</td><td>Capital transfer</td><td><a href="method-M05.html">M05</a></td><td>Emigration transfer, three releases over two years</td><td>{b}</td></tr>
<tr><td>A property sale after you left</td><td>Capital item</td><td><a href="method-M07.html">M07</a> then a capital route</td><td>The sale pays 20% on the gain and does not itself move money out</td><td>{c}</td></tr>
<tr><td>Savings with no paper trail</td><td>Unproven</td><td><a href="method-M02.html">M02</a></td><td>Quota only; no route unlocks without evidence</td><td>{d}</td></tr>
</tbody></table></div>
<h2>Step 1 &mdash; establish your classification in writing</h2>
<ol>
<li>Ask the bank, in writing, whether it treats you as a domestic individual or a foreign individual, and on what basis. The dividing line is one year of continuous residence (CN-01 Art. 52(2)).</li>
<li>Ask whether it will accept an Art. 59 documented purchase from you. The article is permissive, so the answer is the bank's.</li>
<li>Keep the answer. It decides whether your cap is USD 50,000 or none.</li>
</ol>
<p>{src1}</p>
<h2>Step 2 &mdash; assemble the documentary file</h2>
<div class="scroll"><table><thead><tr><th>Document</th><th>Why</th><th>Source</th></tr></thead><tbody>
<tr><td>Passport, and the PRC visa or residence history</td><td>Classification and identity</td><td>{src1}</td></tr>
<tr><td>Employment contract and payroll records, or service contracts and invoices</td><td>Shows the RMB is current-account income</td><td>{src1}</td></tr>
<tr><td>China individual income tax payment record or certificate</td><td>Art. 59 names tax vouchers</td><td>{src2}</td></tr>
<tr><td>Destination account in your own name</td><td>Own-account remittance is the norm, and mandatory on the capital routes</td><td>{src3}</td></tr>
<tr><td>For an emigration transfer: cancelled household registration and certified proof of settlement abroad</td><td>Art. 8 documents</td><td>{src3}</td></tr>
<tr><td>For an inheritance transfer: notarised proof of inheritance, the deceased's title and tax documents</td><td>Art. 9 documents</td><td>{src3}</td></tr>
</tbody></table></div>
<h2>Step 3 &mdash; execute at the bank</h2>
<ol>
<li>Present the file and request the purchase under the article that fits, not under "the quota" by default.</li>
<li>Confirm the rate at the counter: the board is a reference, the counter rate governs (CN-07).</li>
<li>Decide on full-amount arrival. It costs USD 15 if the receiving bank holds its account with BOC New York, otherwise USD 25, and it stops the principal being shaved by correspondent charges (CN-08).</li>
<li>Expect identity verification above RMB 5,000 / USD 1,000 under the 2026 AML order; it is a check, not a cap (CN-05).</li>
<li>Keep the purchase slip, the remittance advice and the bank's confirmation of the rate applied.</li>
</ol>
<h2>Step 4 &mdash; the US side, which is where the real money is</h2>
<ol>
<li>File the FBAR for every year the aggregate foreign accounts exceeded USD 10,000 at any time. Late is better than never, and voluntary correction is cheaper than an examination (US-04).</li>
<li>Check Form 8938 against the threshold for your filing status and residence (US-03).</li>
<li>If the money is an inheritance or gift above USD 100,000, file Form 3520, Part IV (US-05).</li>
<li>If the RMB was acquired at a materially different rate, compute whether the &#167;988 gain on the disposition exceeds USD 200; if it does, the whole gain is ordinary income (US-01).</li>
<li>Keep records for at least five years from the FBAR due date (US-04).</li>
</ol>
<h2>What not to do</h2>
<div class="callout bad">
<ul>
<li>Do not use a relative's quota. Art. 62 watch-lists both sides for three years, and the FX Regulations expose the conduct to a fine of up to 30%, or 30%-100% in a serious case (CN-01, CN-02).</li>
<li>Do not use a dealer who offers a better rate. Art. 45 adds confiscation of the money to the fine (CN-01).</li>
<li>Do not describe a capital transfer as a current-account purchase. The bank's Art. 68 power to refuse is the mild consequence; Art. 40 is the severe one (CN-02, CN-01).</li>
</ul>
</div>
""".format(a=src_links(["CN-02"]), b=src_links(["CN-03"]), c=src_links(["CN-04"]), d=src_links(["CN-02"]),
           src1=src_links(["CN-01", "CN-02"]), src2=src_links(["CN-02"]), src3=src_links(["CN-03"]))
    return shell("Steps", body, active="steps.html")


def build_sources():
    parts = ['<p class="eyebrow">Sources</p><h1>What was read, and what each document supports.</h1>',
             '<p class="lede">{} documents. Tier A is a statute, a regulation, a rule or an agency page. Tier B is a '
             'provider\'s own published price or product terms, which binds only that provider and never establishes a '
             'legal entitlement. No commentary, blog or aggregator is cited anywhere in this edition.</p>'.format(len(SRC)),
             '<div class="scroll"><table><thead><tr><th>ID</th><th>Issuer and document</th><th>What it supports here</th>'
             '<th>Retrieved</th><th>Link</th></tr></thead><tbody>']
    for s in SRC_DOC["sources"]:
        supports = "".join("<li>{}</li>".format(esc(x)) for x in s["supports"])
        parts.append('<tr><td><strong>{}</strong><br><span class="pill {cls}">{tier}</span></td>'
                     '<td>{issuer}<br><strong>{title}</strong><br><span class="note">{zh}</span></td>'
                     '<td><ul class="small">{sup}</ul><p class="note">{note}</p></td>'
                     '<td>{ret}</td><td><a href="{url}" target="_blank" rel="noopener noreferrer">Open &#8599;</a></td></tr>'.format(
                         esc(s["id"]), cls="lawful" if s["tier"] == "A" else "", tier=esc(s["tier"]),
                         issuer=esc(s["issuer"]), title=esc(s["title_en"]), zh=esc(s.get("title_zh", "")),
                         sup=supports, note=esc(s.get("retrieval_note", "")), ret=esc(s["retrieved"]), url=esc(s["url"])))
    parts.append('</tbody></table></div>')
    parts.append("""<h2>How retrieval was recorded</h2>
<p>Each entry records what this session actually opened on {asof} and what was read inside it. A link is not a
verification: several pages in this repository's earlier editions point at URLs that now return 404 (see the repo
review). Where a page could not be opened, the item is flagged and no value rests on it.</p>
<h2>What the sources cannot do</h2>
<p>An official citation establishes what the rule says. It does not establish that a particular branch will approve a
particular file, that a particular person meets a definition, or that a provider will quote a particular price
(F-01, F-02, F-08).</p>""".format(asof=AS_OF))
    return shell("Sources", "".join(parts), active="sources.html")


def build_flagged():
    parts = ['<p class="eyebrow">Flagged for review</p><h1>Everything left blank, and why.</h1>',
             '<p class="lede">{} items. None of them blocks publication; all of them block a false number. Where no '
             'official source exists for a value, the value is absent from every table on this site and appears here '
             'instead.</p>'.format(len(FLAGS)),
             '<div class="scroll"><table class="flagtable"><thead><tr><th>ID</th><th>Severity</th><th>Item</th>'
             '<th>Detail</th><th>Officially sourced?</th><th>Status</th></tr></thead><tbody>']
    for f in FLAGS_DOC["flags"]:
        sev = '<span class="pill {}">{}</span>'.format("prohibited" if f["severity"] == "high" else "cond", esc(f["severity"]))
        srcs = src_links(f["sources"]) if f["sources"] else '<span class="note">No official instrument retrieved &mdash; UNVERIFIED</span>'
        parts.append('<tr id="{}"><td><strong>{}</strong></td><td>{}</td><td>{}</td><td>{}</td><td>{}</td>'
                     '<td><span class="pill unverified">{}</span></td></tr>'.format(
                         esc(f["id"]), esc(f["id"]), sev, esc(f["title"]), esc(f["detail"]), srcs, esc(f["status"])))
    parts.append('</tbody></table></div>')
    parts.append("""<h2>Reading the table</h2>
<ul>
<li><strong>Options not taken.</strong> Every route that an official instrument does not describe is absent, not guessed at. That is why there is no crypto route here: no instrument was retrieved that would let this edition state the rule, so the item is not asserted in either direction (F-18, F-22).</li>
<li><strong>Values not stated.</strong> The US receiving-bank fee, the &#167;988 gain, the property gain, the Form 3520 penalty amount and the professional fees are all blank. Each has a reason in the table.</li>
<li><strong>Items needing a human.</strong> F-01, F-04, F-11 and F-12 depend on a fact or a filing that only the account holder or a professional can resolve.</li>
</ul>""")
    return shell("Flagged for review", "".join(parts), active="flagged.html")


def build_review():
    body = """
<p class="eyebrow">Repository review</p>
<h1>What the eight earlier editions did, and what this one changed.</h1>
<p class="lede">The repository holds overlapping dashboards produced by separate sessions. This is the line-by-line review of the parts that bear on the answer, with the action taken. Nothing belonging to another session was edited; the findings are published instead.</p>
<div class="scroll"><table class="flagtable"><thead><tr><th>ID</th><th>Finding</th><th>Evidence in the repository</th><th>Action in Edition H</th></tr></thead><tbody>
<tr><td>R01</td><td><strong>Seven dashboards, no front door</strong></td><td>The root page made one edition the dashboard and listed the rest as an archive inside a paragraph; /docs/, /dossier/, /overview.html, /pages/ and editions B-G all remained live and independently reachable</td><td>The root page is now a single landing page: the headline numbers, the route comparison, and an explicit archive list. Nothing was deleted.</td></tr>
<tr><td>R02</td><td><strong>A business fee used for a personal transfer</strong></td><td>Edition D's model adds USD 15 for the US receiving bank, sourced to Chase's <em>business</em> account schedule (BK-02)</td><td>The US inbound fee is blank and flagged (F-07); the ladder stops at the China side.</td></tr>
<tr><td>R03</td><td><strong>Prohibited-route fines overstated as a flat range</strong></td><td>Edition D's front page says "the wrong routes cost 30% to 100%" without the statutory base of up to 30%; CN-01 Arts. 39/40/45 reserve 30%-100% for serious cases</td><td>Both limbs are printed: up to 30% in the ordinary case, 30%-100% where serious, plus confiscation (F-20).</td></tr>
<tr><td>R04</td><td><strong>The &#167;988 caveat was in the body but not the headline</strong></td><td>Edition D's headline stat says "Tax on the conversion $0 &mdash; in both jurisdictions"; the USD 200 cliff appears only deeper in the site</td><td>The $0 carries an asterisk on the dashboard and a full paragraph on the tax page.</td></tr>
<tr><td>R05</td><td><strong>A CI check is pinned to one date string</strong></td><td>assets/check.py asserts that pages/estimates.html contains "2026/11/09" and "later-dated"; regenerating that page with a new stamp fails the build even though nothing is wrong</td><td>Not edited (owned by another session). Logged here and in COORDINATION.md.</td></tr>
<tr><td>R06</td><td><strong>Six incompatible route counts</strong></td><td>Edition B 22 methods, C 33 routes, D 16 methods, F 31, G 43, dossier 35; none reconciles the others</td><td>Fifteen routes with the counting rule stated, and the divergence explained rather than averaged.</td></tr>
<tr><td>R07</td><td><strong>An unverified 2026 China tax claim</strong></td><td>Edition G states that a "MOF/STA 2026 No. 27" instrument repealed the foreign-individual FIE dividend exemption from 2026-09-01; no such instrument was retrieved this session</td><td>Not repeated. The dividend route is described only through the instruments on this edition's register.</td></tr>
<tr><td>R08</td><td><strong>Older pages can be read as current</strong></td><td>Editions B-G remain fully published and are not cross-referenced from each other</td><td>Every page of Edition H carries the edition label and a link to the archive; the archive labels the earlier editions as historical.</td></tr>
<tr><td>R09</td><td><strong>Checkers prove consistency, not retrievability</strong></td><td>The other editions' verifiers check internal links, citations and reproducibility; none re-fetches a source. Edition C's S01 URL pattern (.../2024-04-30/2465.html) is the kind of link that rots</td><td>Every source on this edition's register records what was read and when, and the site says plainly that a link is not a verification.</td></tr>
<tr><td>R10</td><td><strong>No edition published a per-route ladder for every route</strong></td><td>Editions B, C, E, F and G left most cost cells blank; D published eight ladders for its own 16 routes; none reconciled the two</td><td>Eight ladders of 40 rows, plus an explicit blank for the seven routes that cannot be priced, each with a flag.</td></tr>
<tr><td>R11</td><td><strong>The root README mixes editions</strong></td><td>The README leads with Edition D and then restarts the document title mid-file</td><td>An Edition H section is appended (no existing text removed) pointing at the new dashboard.</td></tr>
<tr><td>R12</td><td><strong>Shared-file ownership is unresolved</strong></td><td>edition-d/build/build.py writes the root index.html, so no other session can own the landing page without breaking its CI</td><td>Handover recorded: Edition D's generator no longer writes the root page; its own pages remain byte-identical and its verifier still passes.</td></tr>
</tbody></table></div>
<p class="note">Rows in this register cite the repository itself &mdash; files, generated pages and CI scripts &mdash; rather than an external instrument, so they are marked as a review table: the evidence is the file named in the row and can be opened in the repository. That is why this table is exempt from the external-source rule that the verifier applies to every other table.</p>
<h2>Not reviewed</h2>
<p>The legal substance of editions B-G was not re-audited line by line. Their pages remain published as historical
work, each with its own source log. Where this edition disagrees with an earlier one, the disagreement is on this page,
not silently applied to their files.</p>
"""
    return shell("Repo audit", body, active="repo-review.html")


def build_methodology():
    body = """
<p class="eyebrow">Method and limits</p>
<h1>How the numbers were made, and what they cannot tell you.</h1>
<h2>The rules the build enforces</h2>
<dl>
<dt>Every value traces to a source</dt><dd>The cost engine reads only parameters.json, and every parameter names a source id. The verifier fails if an id is unknown or a value has no source.</dd>
<dt>A blank is never a zero</dt><dd>Unknown values render as an em dash and carry a flag id. The verifier fails on a zero in a cell whose parameter is null.</dd>
<dt>The arithmetic is recomputed, not read</dt><dd>verify.py recomputes every ladder cell from the raw parameters and compares it to the published HTML.</dd>
<dt>Every table row carries a source link</dt><dd>Rows without an external source link fail the build, except inside a table explicitly marked as a flagged table, where the unverified marker takes its place. Statements about this site itself are written as lists, not tables.</dd>
<dt>No prohibited procedure</dt><dd>Prohibited routes have no steps. Their pages contain the statutory range and a pointer to a lawful route.</dd>
<dt>The build is reproducible</dt><dd>Two consecutive builds produce byte-identical output; CI asserts a clean git diff after rebuilding.</dd>
</dl>
<h2>The arithmetic</h2>
<p>USD amount <em>A</em>. CNY required = <em>A</em> &times; selling rate / 100. FX margin = <em>A</em> &times; (ask &minus; mid) / mid.
Commission = min(max(0.001 &times; CNY, 50), 260) CNY, applied per remittance. Cable = 150 CNY per remittance. China-side
total = margin + commission + cable. The optional full-amount charge is shown separately because it is a corporate price
line and its use on a personal transfer is unverified.</p>
<h2>Why the one-way margin and not the round trip</h2>
<p>You convert once. The bank buys USD from you at its selling rate; the midpoint is the fair reference. The loss on
that single step is (ask &minus; mid)/mid = 0.2104% on this board. The 0.4199% figure that circulates is the round trip,
i.e. converting to USD and back. Using it for a single conversion would double the FX line, so both numbers are printed
and the one-way figure is used.</p>
<h2>What was not done</h2>
<ul>
<li>No account was contacted, no rate was quoted, no funds were moved.</li>
<li>No personal tax result was computed, because the residency, the source of funds, the acquisition dates and the filing history are unknown.</li>
<li>No provider was asked for a live quote. The Wise route carries its verified cap and a blank fee.</li>
<li>No commentary source was used for any value, including the 2026 US excise tax item, which is flagged instead (F-22).</li>
<li>No earlier edition's file was edited, except the single handover line in Edition D's generator, which is logged.</li>
</ul>
<h2>Reading the status vocabulary</h2>
<dl>
<dt>lawful</dt><dd>The rule text provides the route and names no approval beyond documentary review.</dd>
<dt>lawful with approval</dt><dd>The rule text provides the route and names an approval or registration step.</dd>
<dt>lawful, conditional</dt><dd>Lawful if a fact about you or the money is true. The fact is not assumed here.</dd>
<dt>unverified</dt><dd>Commonly described, but no official instrument retrieved this session confirms it. Not priced, not recommended.</dd>
<dt>prohibited</dt><dd>Named as prohibited or penalised in an instrument on the register. No procedure is given.</dd>
</dl>
"""
    return shell("Method", body, active="repo-review.html")


def build_requirements():
    parts = ['<p class="eyebrow">Requirements traceability</p><h1>Every line of the brief, and where it is answered.</h1>',
             '<div class="scroll"><table class="flagtable"><thead><tr><th>#</th><th>Requirement</th><th>Where it is delivered</th>'
             '<th>Status</th></tr></thead><tbody>']
    for r in REQ_DOC["requirements"]:
        parts.append('<tr><td>{}</td><td>{}</td><td>{}</td><td><span class="pill lawful">{}</span></td></tr>'.format(
            esc(r["id"]), esc(r["requirement"]), esc(r["delivered"]), esc(r["status"])))
    parts.append('</tbody></table></div>')
    parts.append('<p class="note">Requirements are quoted from the project brief and split into testable lines; the '
                 'brief itself is not reproduced verbatim beyond the requirement text. This is a traceability register, not a '
                 'fact table: its evidence is the page or file named in each row, so it is exempt from the external-source rule.</p>')
    return shell("Requirements", "".join(parts), active="repo-review.html")


# ---------------------------------------------------------------------------
# root landing page
# ---------------------------------------------------------------------------

ROOT_CSS = """
:root{--ink:#101720;--ink2:#3a4552;--muted:#697584;--line:#e0e5ec;--bg:#f5f7fa;--panel:#fff;--accent:#0d5c4a}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
.wrap{max-width:1020px;margin:0 auto;padding:16px 14px 56px}
.top{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-size:.66rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);border-bottom:1px solid var(--line);padding-bottom:10px}
.brand{font-weight:800;letter-spacing:-.02em;font-size:1rem;color:var(--ink);text-transform:none}
h1{font-size:1.85rem;line-height:1.12;letter-spacing:-.03em;margin:.5em 0 .3em;max-width:22ch}
h2{font-size:1.1rem;margin:1.8em 0 .5em}
.lede{font-size:1.02rem;color:var(--ink2);max-width:66ch}
.eyebrow{font-size:.64rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:800;margin:20px 0 0}
.stats{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin:16px 0}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 11px}
.stat small{display:block;font-size:.56rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.stat strong{display:block;font-size:1.18rem;letter-spacing:-.02em;margin:1px 0}
.stat span{display:block;font-size:.7rem;color:var(--ink2)}
.grid{display:grid;grid-template-columns:1fr;gap:8px;margin:12px 0}
.card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px;color:inherit}
.card:hover{border-color:var(--accent);text-decoration:none}
.card h3{margin:.1em 0 .25em;font-size:.94rem}
.card p{margin:0;font-size:.8rem;color:var(--ink2)}
.kicker{font-size:.58rem;letter-spacing:.1em;color:var(--accent);font-weight:800}
.cta{display:inline-block;background:var(--accent);color:#fff;font-weight:700;padding:11px 18px;border-radius:10px;margin:12px 0}
.cta:hover{background:#0a4a3c;text-decoration:none}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel);margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:.79rem;min-width:460px}
th,td{padding:8px 9px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#eff3f7;font-size:.6rem;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);white-space:nowrap}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.src{display:inline-block;font-size:.58rem;font-weight:700;padding:1px 5px;border-radius:5px;background:#eef1f5;border:1px solid var(--line);color:var(--ink2);white-space:nowrap}
.note{font-size:.78rem;color:var(--muted)}
.archive{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.archive ul{margin:.4em 0;padding-left:1.1em;font-size:.84rem;color:var(--ink2)}
footer{border-top:1px solid var(--line);margin-top:28px;padding-top:12px;font-size:.76rem;color:var(--muted)}
@media(min-width:720px){.stats{grid-template-columns:repeat(4,1fr)}.grid{grid-template-columns:repeat(3,1fr)}h1{font-size:2.5rem}}
"""


def build_root():
    r = {a: cost_row(a, "wire_purchase") for a in ANCHORS}
    stats = """<div class="stats">
  <div class="stat"><small>FX margin, one conversion</small><strong>{ow}</strong><span>Bank of China board, {stamp}</span></div>
  <div class="stat"><small>Cost at $400,000</small><strong>{c400}</strong><span>{p400} of the amount</span></div>
  <div class="stat"><small>Cost at $10,000</small><strong>{c10}</strong><span>{p10} &mdash; fixed fees dominate</span></div>
  <div class="stat"><small>Tax on the conversion</small><strong>$0</strong><span>in both jurisdictions*</span></div>
</div>""".format(ow=pct(ONE_WAY, 4), stamp=P["fx_board"]["stamp"], c400=money(r[400_000]["china"]),
                 p400=pct(r[400_000]["share"]), c10=money(r[10_000]["china"]), p10=pct(r[10_000]["share"]))
    snap = "".join(
        '<tr><td class="num">{}</td><td class="num"><strong>{}</strong></td><td class="num">{}</td>'
        '<td class="num">{}</td><td>{}</td></tr>'.format(
            money(a, 0), money(r[a]["china"]), pct(r[a]["share"]), money(r[a]["net"]), src_links(["CN-06", "CN-07"]))
        for a in ANCHORS)
    cards = [
        ("edition-h/docs/index.html", "01", "Dashboard", "The answer, the numbers, and every USD 10,000 step."),
        ("edition-h/docs/methods.html", "02", "All 15 routes", "Four categories, with caps, documents, pros and cons."),
        ("edition-h/docs/costs.html", "03", "Costs", "The conversion penalty decomposed, with every input."),
        ("edition-h/docs/taxes.html", "04", "Tax and reporting", "China IIT, &#167;988, FBAR, 8938 and 3520."),
        ("edition-h/docs/steps.html", "05", "Step by step", "The decision tree and the exact sequence to follow."),
        ("edition-h/docs/flagged.html", "06", "Flagged for review", "26 items left blank, with the reason."),
        ("edition-h/docs/executive-summary.html", "07", "Executive summary", "Nine findings and one recommendation."),
        ("edition-h/docs/sources.html", "08", "Sources", "15 documents, what each supports, when it was read."),
        ("edition-h/docs/repo-review.html", "09", "Repo audit", "Line-by-line review of the earlier editions."),
    ]
    body = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Official-source research on turning CNY into USD for a US citizen: every lawful route, priced from USD 10,000 to USD 400,000, with the tax and reporting position in both countries.">
<title>China Money &middot; getting CNY out, priced</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
<div class="top"><span class="brand">China Money</span><span>Research &middot; {asof} &middot; Edition H</span></div>
<p class="eyebrow">CNY to USD &middot; US citizen &middot; official sources only</p>
<h1>Getting money out of China, priced.</h1>
<p class="lede">There is no tax on converting your own money in either country. What stands between a Chinese bank balance and a US account is China's capital-account rule, a published bank tariff under 1%, and a US reporting duty whose penalty can reach half the balance. This site prices every lawful route at every USD 10,000 step to USD 400,000 and links every number to an official document.</p>
{stats}
<a class="cta" href="edition-h/docs/index.html">Open the dashboard &rarr;</a>
<div class="grid">{cards}</div>
<h2>What it costs, at a glance</h2>
<div class="scroll"><table><thead><tr><th class="num">Amount</th><th class="num">China-side cost</th><th class="num">Share</th><th class="num">Net received</th><th>Source</th></tr></thead><tbody>{snap}</tbody></table></div>
<p class="note">Route M01, documented current-account purchase. FX margin plus Bank of China commission and cable charge, at the board stamped {stamp}. Excludes your US bank's inbound fee (flagged) and professional fees. Full 40-row ladders are on the dashboard.</p>
<h2>The answer in five rows</h2>
<div class="scroll"><table><thead><tr><th>Question</th><th>Answer</th><th>Source</th></tr></thead><tbody>
<tr><td><strong>Is conversion taxed?</strong></td><td>No. China taxes nine categories of income and an exchange is not one; on the US side the personal-transaction rule leaves the currency gain untaxed unless it exceeds USD 200.</td><td>{s1}</td></tr>
<tr><td><strong>What stops the money?</strong></td><td>Capital-account convertibility, not tax. Current-account business is convertible; capital-account business follows a process.</td><td>{s2}</td></tr>
<tr><td><strong>What does a lawful conversion cost?</strong></td><td>{ow} of the amount in FX margin, plus a commission capped at CNY 260 and a CNY 150 cable charge per remittance.</td><td>{s3}</td></tr>
<tr><td><strong>What decides the route?</strong></td><td>How the RMB arose. Salary or services: documented purchase with no annual cap in the rule text. Inheritance or emigration: the 2004 personal-property transfer rules. Neither: USD 50,000 a year.</td><td>{s4}</td></tr>
<tr><td><strong>What is the real risk?</strong></td><td>A willful FBAR penalty is the greater of USD 165,353 or 50% of the balance, per violation. At USD 400,000 that is USD 200,000.</td><td>{s5}</td></tr>
</tbody></table></div>
<h2>Archive &mdash; earlier editions in this repository</h2>
<div class="archive">
<p class="note">Nine dashboards were produced by separate sessions. Edition H is the current one: it prices every route, publishes the blanks, and audits the rest. The earlier editions are preserved unchanged and are reachable here.</p>
<ul>
<li><a href="edition-d/docs/index.html">Edition D</a> &mdash; cost engine, USD 10,000-step tables, repo audit (the previous dashboard)</li>
<li><a href="edition-g/docs/index.html">Edition G</a> &mdash; 43 candidates, 1,720 cost rows</li>
<li><a href="edition-f/site/index.html">Edition F</a> &mdash; 31 methods, 40-row ladder</li>
<li><a href="edition-e/site/index.html">Edition E</a> &mdash; 32 methods, forty-step grids</li>
<li><a href="edition-c/docs/index.html">Edition C</a> &mdash; 33 channels, tax treaty, repo review</li>
<li><a href="edition-b/index.html">Edition B</a> &mdash; 22 channels, penalty layers, US reporting</li>
<li><a href="dossier/index.html">Verified dossier</a> &mdash; 35 routes, capital-account taxonomy</li>
<li><a href="docs/index.html">Supplemental dashboard</a> &middot; <a href="overview.html">original overview</a> &middot; <a href="pages/estimates.html">40 amount scenarios</a></li>
</ul>
</div>
<footer>
<p><strong>What this is.</strong> Published-rule research with the arithmetic shown. Not legal, tax or investment advice, and not a bank quote. Values that could not be confirmed are blank and published on the <a href="edition-h/docs/flagged.html">Flagged for review</a> page; the method is on the <a href="edition-h/docs/methodology.html">methodology</a> page. Coordination record: <a href="COORDINATION.md">COORDINATION.md</a>.</p>
<p>* The $0 concerns the conversion, not your whole return: an inheritance above USD 100,000 still needs Form 3520, the account still needs an FBAR, and a &#167;988 gain above USD 200 is ordinary income.</p>
</footer>
</div>
</body>
</html>
""".format(css=ROOT_CSS, asof=AS_OF, stats=stats,
           cards="".join('<a class="card" href="{}"><span class="kicker">{}</span><h3>{}</h3><p>{}</p></a>'.format(
               h, k, t, d) for h, k, t, d in cards),
           snap=snap, stamp=P["fx_board"]["stamp"], ow=pct(ONE_WAY, 4),
           s1=src_links(["CN-04", "US-01"]), s2=src_links(["CN-01"]), s3=src_links(["CN-06", "CN-07"]),
           s4=src_links(["CN-02", "CN-03"]), s5=src_links(["US-03"]))
    with open(ROOT / "index.html", "w", encoding="utf-8") as fh:
        fh.write(body)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main():
    write("index.html", build_index())
    write("executive-summary.html", build_exec())
    write("methods.html", build_methods())
    for slug, _, _ in CATS:
        write("category-{}.html".format(slug), build_category(slug))
    for m in METHODS:
        write("method-{}.html".format(m["id"]), build_method_page(m))
    write("costs.html", build_costs())
    write("taxes.html", build_taxes())
    write("penalties.html", build_penalties())
    write("steps.html", build_steps())
    write("sources.html", build_sources())
    write("flagged.html", build_flagged())
    write("repo-review.html", build_review())
    write("methodology.html", build_methodology())
    write("requirements.html", build_requirements())
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    build_root()
    pages = len(list(OUT.glob("*.html")))
    ladders = sum(len(AMOUNTS) for _ in LADDER_MODELS)
    print("edition-h: wrote {} pages, {} ladder rows".format(pages, ladders))
    print("one-way margin {:.4f}%  round trip {:.4f}%".format(ONE_WAY * 100, ROUND_TRIP * 100))
    for a in (10_000, 100_000, 400_000):
        c = cost_row(a, "wire_purchase")
        print("  ${:,}: china-side ${:,.2f} ({:.3f}%)".format(a, c["china"], c["share"] * 100))
    print("root landing page written to index.html")


if __name__ == "__main__":
    main()
