#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Edition H — deterministic static-site generator.

No third-party dependencies. Same data in, byte-identical HTML out.

Rules enforced by construction:
  * every table row that states a fact carries at least one source link
  * a figure is printed only if every input behind it has a source id
  * a method with an unpublished component shows an em dash and a flag,
    never an estimate
  * the cost ladder is exactly 40 points for every method
"""

import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "data"))

from sources import SOURCES, RETRIEVED              # noqa: E402
from methods import METHODS                          # noqa: E402
from costs import (AMOUNTS, compute, FX_MARGIN_PCT,  # noqa: E402
                   FX_ROUND_TRIP_PCT, BUY_SPOT, SELL_SPOT, REFERENCE, MID,
                   CABLE_FEE_CNY, COMMISSION_MAX_CNY, FULL_AMOUNT_USD,
                   RECEIVING_BANK_USD, q2, q4, usd_to_cny, cable_usd,
                   deposit_cert_usd, carriage_cert_usd)
from penalties import (LAYER2, LAYER3, LAYER4, REPORTING, STRATEGY,  # noqa: E402
                       LAYER1_NOTE)

OUT = os.path.join(ROOT, "site")
AS_OF = "9 November 2026"
AS_OF_TIME = "2026-11-09 01:30-02:10 UTC"

SRC = {s["id"]: s for s in SOURCES}
METHOD = {m["id"]: m for m in METHODS}

CATEGORIES = [
    ("personal", "Personal routes", "The routes an individual can actually use, in the order to try them."),
    ("business", "Business and entity routes", "Routes that only exist if there is a real company or a real trade behind the money."),
    ("rails", "Rails", "How the money physically travels once the purchase is allowed."),
    ("prohibited", "Prohibited", "Shown so you can recognise them. No execution steps are given."),
    ("alternatives", "Alternatives", "Ways to avoid converting at all, or to pay less to convert."),
]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def esc(t):
    return html.escape(str(t), quote=True)


def money(v, dp=2):
    if v is None:
        return "—"
    return "${:,.{}f}".format(float(v), dp)


def share(total, amount, dp=3):
    """total as a percentage of amount, printed as a percentage."""
    if total is None or not amount:
        return "—"
    return "{:.{}f}%".format(float(total) / float(amount) * 100.0, dp)


def pct(v, dp=3):
    if v is None:
        return "—"
    return "{:.{}f}%".format(float(v), dp)


def src_links(ids, rel=""):
    out = []
    for sid in ids:
        s = SRC.get(sid)
        if not s:
            continue
        out.append(
            '<a class="src" href="{u}" target="_blank" rel="noopener noreferrer" '
            'title="{t}">{i}</a>'.format(
                u=esc(s["url"]), t=esc(s["title"]), i=esc(sid)))
    return " ".join(out)


def grade_badge(g):
    return '<span class="g g{0}" title="{1}">{0}</span>'.format(
        esc(g), esc({"A": "statute or regulator rule",
                     "B": "official guidance or form instruction",
                     "C": "provider's own published price — binds that provider only"}[g]))


def status_badge(st):
    label = {"lawful": "Lawful", "conditional": "Conditional", "prohibited": "Prohibited",
             "not_a_transfer": "Not a transfer"}[st]
    return '<span class="st s-{0}">{1}</span>'.format(esc(st), esc(label))


CSS = """
:root{
 --ink:#10151b; --ink2:#39434f; --muted:#68737f; --line:#e3e7ec; --bg:#f5f6f8;
 --panel:#fff; --accent:#0d5c49; --accent2:#0a4537; --warn:#8a4b00; --warnbg:#fff6e8;
 --bad:#8c1d18; --badbg:#fdf0ef; --okbg:#eaf5f1; --chip:#eef1f5;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
 font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px 64px}
header.site{background:var(--panel);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20}
.hbar{max-width:1080px;margin:0 auto;padding:10px 16px;display:flex;align-items:center;
 gap:12px;justify-content:space-between}
.brand{font-weight:800;letter-spacing:-.02em;font-size:1rem;color:var(--ink);white-space:nowrap}
.brand span{color:var(--accent)}
nav.main{display:flex;gap:4px;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none}
nav.main::-webkit-scrollbar{display:none}
nav.main a{font-size:.82rem;font-weight:600;padding:8px 10px;border-radius:8px;white-space:nowrap;color:var(--ink2)}
nav.main a:hover{background:var(--chip);text-decoration:none}
nav.main a[aria-current]{background:var(--accent);color:#fff}
h1{font-size:1.65rem;line-height:1.2;letter-spacing:-.025em;margin:22px 0 8px}
h2{font-size:1.2rem;letter-spacing:-.01em;margin:32px 0 10px}
h3{font-size1rem;font-size:1rem;margin:20px 0 6px}
p.lede{font-size:1.02rem;color:var(--ink2);margin:0 0 18px;max-width:68ch}
p{max-width:75ch}
.eyebrow{font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);font-weight:700;margin:24px 0 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;margin:14px 0}
.answer{background:linear-gradient(180deg,#0d5c49,#0a4537);color:#fff;border:0}
.answer h2{color:#fff;margin-top:0;font-size:1.05rem;letter-spacing:.02em;text-transform:uppercase;font-size:.78rem}
.answer .big{font-size:1.5rem;font-weight:800;letter-spacing:-.02em;line-height:1.25;margin:0 0 8px}
.answer p{color:#d8ece5;margin:.5em 0}
.answer a{color:#bff0e0}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:16px 0}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px}
.stat small{display:block;font-size:.63rem;letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
.stat strong{display:block;font-size:1.28rem;letter-spacing:-.02em;margin:3px 0 1px}
.stat em{display:block;font-size:.73rem;color:var(--ink2);font-style:normal}
.grid{display:grid;grid-template-columns:1fr;gap:10px;margin:14px 0}
.nav-card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;
 padding:14px;color:inherit}
.nav-card:hover{border-color:var(--accent);text-decoration:none}
.nav-card h3{margin:2px 0 4px;font-size:1rem}
.nav-card p{margin:0;font-size:.85rem;color:var(--ink2)}
.kicker{font-size:.63rem;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);font-weight:700}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:var(--panel);
 -webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.86rem}
th,td{padding:10px 11px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#eff2f5;font-size:.66rem;letter-spacing:.05em;text-transform:uppercase;color:var(--ink2);
 font-weight:700;position:sticky;top:0}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:#fafbfc}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td.big{font-weight:700}
.src{display:inline-block;font-size:.63rem;font-weight:700;padding:2px 5px;border-radius:5px;
 background:var(--chip);border:1px solid var(--line);color:var(--ink2);white-space:nowrap;margin:1px 0}
.src:hover{background:var(--accent);color:#fff;border-color:var(--accent);text-decoration:none}
.g{display:inline-block;font-size:.6rem;font-weight:800;width:16px;height:16px;line-height:16px;
 text-align:center;border-radius:4px;color:#fff}
.gA{background:#0d5c49}.gB{background:#3f5a8a}.gC{background:#7a5a1e}
.st{display:inline-block;font-size:.67rem;font-weight:700;padding:2px 7px;border-radius:999px;white-space:nowrap}
.s-lawful{background:var(--okbg);color:#0a4537}
.s-conditional{background:var(--warnbg);color:var(--warn)}
.s-prohibited{background:var(--badbg);color:var(--bad)}
.s-not_a_transfer{background:var(--chip);color:var(--ink2)}
.note{font-size:.82rem;color:var(--muted);max-width:75ch}
.flag{background:var(--warnbg);border:1px solid #f2ddbb;border-radius:10px;padding:12px;margin:12px 0}
.flag strong{color:var(--warn)}
.danger{background:var(--badbg);border:1px solid #f3cfcb;border-radius:10px;padding:12px;margin:12px 0}
.danger strong{color:var(--bad)}
.ok{background:var(--okbg);border:1px solid #cfe6de;border-radius:10px;padding:12px;margin:12px 0}
ul,ol{padding-left:1.15em;max-width:75ch}
li{margin:.3em 0}
.crumb{font-size:.78rem;color:var(--muted);margin:16px 0 0}
.crumb a{color:var(--muted)}
details{border:1px solid var(--line);border-radius:10px;padding:10px 12px;background:var(--panel);margin:10px 0}
summary{cursor:pointer;font-weight:650;font-size:.9rem}
.block{border-left:3px solid var(--accent);padding-left:12px;margin:14px 0}
footer.site{border-top:1px solid var(--line);margin-top:40px;padding:18px 0 0;font-size:.8rem;color:var(--muted)}
footer.site p{max-width:none}
.pill{display:inline-block;font-size:.66rem;font-weight:700;padding:2px 7px;border-radius:999px;
 background:var(--chip);color:var(--ink2);margin-left:4px}
.two{display:grid;grid-template-columns:1fr;gap:14px}
.pros li{color:#0a4537}
.cons li{color:#5c2a26}
.mobonly{display:block}
@media(min-width:760px){
 h1{font-size:2.1rem}
 .stats{grid-template-columns:repeat(4,1fr)}
 .grid{grid-template-columns:repeat(3,1fr)}
 .two{grid-template-columns:1fr 1fr}
 .mobonly{display:none}
}
@media(max-width:640px){
 /* stacked cards for the key tables so nothing needs horizontal scrolling */
 table.stack thead{display:none}
 table.stack tr{display:block;border:1px solid var(--line);border-radius:10px;margin:8px;background:var(--panel)}
 table.stack td{display:flex;justify-content:space-between;gap:12px;border:0;padding:6px 10px}
 table.stack td::before{content:attr(data-l);font-size:.66rem;letter-spacing:.05em;
  text-transform:uppercase;color:var(--muted);font-weight:700;flex:0 0 42%}
 table.stack td.num{justify-content:space-between}
 table.stack tr td:first-child{background:#f7f9fa;border-radius:10px 10px 0 0;font-weight:700}
 .tw{border:0;background:transparent}
}
.py{display:none}
"""


def page(title, body, current, rel=""):
    nav = [("index.html", "Dashboard"), ("answer.html", "The answer"),
           ("costs.html", "Costs $10k–$400k"), ("methods.html", "All routes"),
           ("penalty.html", "Penalty"), ("tax.html", "Tax"),
           ("reporting.html", "US filing"), ("steps.html", "Step by step"),
           ("sources.html", "Sources"), ("flagged.html", "Flagged"),
           ("repo-review.html", "Repo audit"), ("methodology.html", "Method")]
    links = "".join(
        '<a href="{h}"{c}>{t}</a>'.format(
            h=esc(rel + h), t=esc(t),
            c=' aria-current="page"' if h == current else "")
        for h, t in nav)
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Getting CNY out of China as a US citizen: every lawful route, the published cost at every USD 10,000 step from 10,000 to 400,000, and where the tax penalties actually come from.">
<meta name="color-scheme" content="light">
<title>{title} · China Money</title>
<style>{css}</style>
</head>
<body>
<header class="site"><div class="hbar">
<a class="brand" href="{rel}index.html">CNY<span>&rarr;</span>USD <span style="color:#68737f;font-weight:600">research</span></a>
<nav class="main">{nav}</nav>
</div></header>
<div class="wrap">
{body}
<footer class="site">
<p><strong>What this is.</strong> Published-rule research with the arithmetic shown, built from official
government, regulator, statute and provider pages retrieved on {asof}. It is not legal, tax or
investment advice, and it is not a bank quote. Rates and tariffs change — every source is linked so
you can re-check it by hand.</p>
<p>Values that could not be confirmed from an official page are left blank and published on the
<a href="{rel}flagged.html">Flagged for review</a> page. Nothing is inferred or estimated.
Edition H · session arena-e01cf383 · <a href="https://github.com/sassnarep3-star/China1">repository</a></p>
</footer>
</div>
</body>
</html>
""".format(title=esc(title), css=CSS, nav=links, body=body, rel=rel, asof=esc(AS_OF))


def write(name, content):
    path = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


# --------------------------------------------------------------------------
# computed route list
# --------------------------------------------------------------------------
COMPUTED = [m for m in METHODS if m["cost_model"] in
            ("boc_documented", "boc_convert_only", "boc_cash")]
BLANK = [m for m in METHODS if m["cost_model"] == "unknown"]
PROHIB = [m for m in METHODS if m["cost_model"] == "prohibited"]
NEUTRAL = [m for m in METHODS if m["cost_model"] == "none"]

# the headline route: the documented overseas-individual purchase
LEAD = METHOD["A01"]


def ladder(method):
    return [(a, compute(method, a)) for a in AMOUNTS]
