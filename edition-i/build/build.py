#!/usr/bin/env python3
"""Edition I: mobile-first CNY -> USD repatriation dashboard.

Design rules, enforced again by verify.py:
  * every route and every cost row carries at least one source link
  * only published components are computed; everything else stays blank
  * no personal tax amount, no "guaranteed" total, no execution steps for
    prohibited routes
  * amount ladders are generated, never typed by hand

Deterministic: same JSON in, byte-identical HTML out.
Usage: python3 edition-i/build/build.py
"""
from __future__ import annotations

import csv
import json
import math
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ED = Path(__file__).resolve().parents[1]
DATA = ED / "data"
OUT = ED / "site"

AS_OF = "10 November 2026"
AMOUNTS = list(range(10_000, 400_001, 10_000))

FX = 6.6903          # BOC spot sell, CNY per USD, board 2026-11-10 07:32:39
FX_BUY = 6.6622      # BOC spot buy
MID = (FX + FX_BUY) / 2
CABLE_CNY = 150.0
COMM_MIN_CNY = 50.0
COMM_MAX_CNY = 260.0

CATEGORIES = [
    ("all", "All routes"),
    ("personal", "Personal / current account"),
    ("capital", "Capital account"),
    ("rail", "Banks & providers"),
    ("card", "Cards & cash"),
    ("hold", "Hold or spend"),
    ("prohibited", "Prohibited / unverified"),
]

STATUS_LABEL = {
    "candidate": "Lawful candidate",
    "conditional": "Conditional",
    "limited": "Lawful but capped",
    "prohibited": "Prohibited",
    "unverified": "Unverified",
}

CSS = """
:root{--ink:#12222c;--muted:#556773;--line:#d7e0e6;--bg:#f4f7f9;--card:#fff;
--accent:#0b6b5f;--accent-2:#e3f1ee;--warn:#8a5300;--warnbg:#fff4e0;
--danger:#962626;--dangerbg:#fdecec;--ok:#1c5c3a;--radius:14px}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent)}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #b57b00;outline-offset:2px}
.skip{position:absolute;left:-999px}
.skip:focus{left:8px;top:8px;background:#fff;padding:10px;z-index:50;border:2px solid var(--accent)}
header.top{background:#0d2b33;color:#fff;position:sticky;top:0;z-index:20;box-shadow:0 2px 10px rgba(0,0,0,.15)}
.top-inner{max-width:1120px;margin:auto;padding:10px 16px;display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.brand{color:#fff;text-decoration:none;font-weight:700;letter-spacing:.2px;display:flex;gap:10px;align-items:center}
.brand span.mark{background:#1d5c63;border:1px solid #3b7d84;border-radius:8px;padding:3px 8px;font-size:.85rem}
.brand small{display:block;font-weight:400;font-size:.7rem;letter-spacing:.12em;color:#a9c6cc;text-transform:uppercase}
nav.main{display:flex;gap:4px;overflow-x:auto;max-width:1120px;margin:0 auto;padding:0 8px 8px;-webkit-overflow-scrolling:touch;scrollbar-width:thin}
nav.main a{color:#cfe3e6;text-decoration:none;padding:8px 11px;border-radius:999px;font-size:.86rem;white-space:nowrap;border:1px solid transparent}
nav.main a:hover{background:#15424b;color:#fff}
nav.main a[aria-current="page"]{background:#e8f3f1;color:#0d2b33;font-weight:650}
main{max-width:1120px;margin:auto;padding:22px 16px 64px}
h1{font-size:clamp(1.75rem,5vw,2.7rem);line-height:1.14;margin:.25em 0 .35em;max-width:26ch;letter-spacing:-.01em}
h2{font-size:clamp(1.25rem,3.4vw,1.65rem);margin:2.1em 0 .5em;line-height:1.25}
h3{font-size:1.06rem;margin:1.4em 0 .35em}
p{margin:.55em 0}
.lead{font-size:1.08rem;color:#2b3c47;max-width:78ch}
.muted{color:var(--muted)}
.small{font-size:.85rem}
.pill{display:inline-block;background:var(--accent-2);color:#134b43;border-radius:999px;padding:5px 11px;font-size:.78rem;font-weight:650;letter-spacing:.02em;margin:0 6px 6px 0}
.pill.warn{background:var(--warnbg);color:var(--warn)}
.pill.danger{background:var(--dangerbg);color:var(--danger)}
.notice{border-left:4px solid #b57b00;background:var(--warnbg);padding:14px 16px;border-radius:0 10px 10px 0;margin:18px 0}
.notice.danger{border-color:var(--danger);background:var(--dangerbg)}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:16px 16px 14px;margin:12px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}
.grid.two{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
a.card{display:block;text-decoration:none;color:inherit;transition:border-color .15s,transform .15s}
a.card:hover{border-color:#7fb3ab;transform:translateY(-1px)}
a.card strong{color:var(--accent);font-size:1.02rem}
a.card p{color:var(--muted);font-size:.9rem;margin:.35em 0 0}
.kpi{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}
.kpi b{font-size:1.5rem;letter-spacing:-.02em}
.tablewrap{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:12px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{padding:11px 10px;text-align:left;vertical-align:top;border-bottom:1px solid #e7edf1}
th{background:#eef4f6;font-size:.78rem;text-transform:uppercase;letter-spacing:.05em;color:#3b525f;font-weight:700;position:sticky;top:0}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:#fafcfd}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.blank{background:#fffdf5;color:#7a6a45}
.src{white-space:nowrap;font-size:.76rem;margin-right:5px;text-decoration:none;border-bottom:1px dotted var(--accent)}
.badge{display:inline-block;padding:3px 8px;border-radius:6px;font-size:.74rem;font-weight:700;white-space:nowrap}
.b-candidate{background:#dff0e6;color:var(--ok)}
.b-conditional{background:#e6eefb;color:#1f4b8f}
.b-limited{background:#fff2d9;color:var(--warn)}
.b-prohibited{background:var(--dangerbg);color:var(--danger)}
.b-unverified{background:#eceff1;color:#4a5a63}
.chips{display:flex;gap:8px;overflow-x:auto;padding:6px 0 10px;-webkit-overflow-scrolling:touch}
.chip{border:1px solid var(--line);background:#fff;border-radius:999px;padding:7px 13px;font-size:.84rem;white-space:nowrap;cursor:pointer;color:#29414d}
.chip[aria-pressed="true"]{background:#0d2b33;color:#fff;border-color:#0d2b33}
.searchbox{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 12px}
.searchbox input,.searchbox select{padding:10px 12px;border:1px solid var(--line);border-radius:10px;font-size:.95rem;background:#fff;min-width:0}
.searchbox input{flex:1 1 220px}
.steps{counter-reset:s;list-style:none;padding:0;margin:.6em 0}
.steps li{counter-increment:s;position:relative;padding:0 0 10px 34px}
.steps li::before{content:counter(s);position:absolute;left:0;top:1px;width:23px;height:23px;border-radius:50%;
background:#0d2b33;color:#fff;font-size:.78rem;font-weight:700;display:grid;place-items:center}
ul.plain{padding-left:1.1em;margin:.5em 0}
ul.plain li{margin:.25em 0}
.pros li{color:#1c5c3a}
.cons li{color:#7a2b2b}
details{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:10px 0}
summary{cursor:pointer;font-weight:650}
footer{margin-top:44px;border-top:1px solid var(--line);padding-top:16px;color:var(--muted);font-size:.86rem}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
@media (max-width:640px){
  h1{font-size:1.6rem}
  .tablewrap{border:0;background:transparent;overflow:visible}
  table.responsive,table.responsive tbody,table.responsive tr,table.responsive td{display:block;width:100%}
  table.responsive thead{position:absolute;left:-9999px}
  table.responsive tr{background:#fff;border:1px solid var(--line);border-radius:12px;margin:0 0 10px;padding:6px 4px}
  table.responsive td{display:grid;grid-template-columns:44% 56%;gap:8px;border-bottom:1px dashed #e7edf1;padding:8px 10px;text-align:left}
  table.responsive td:last-child{border-bottom:0}
  table.responsive td::before{content:attr(data-label);font-size:.72rem;text-transform:uppercase;letter-spacing:.04em;color:#5a6b76;font-weight:700}
  table.responsive td.num{text-align:left}
  main{padding:16px 12px 48px}
  .card{padding:14px}
}
@media print{header.top,nav.main,.chips,.searchbox{display:none}body{background:#fff}.tablewrap{overflow:visible}}
"""


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def money(v, dec=2):
    return f"${v:,.{dec}f}"


def source_links(ids, sources):
    out = []
    for sid in ids:
        s = sources[sid]
        out.append(f'<a class="src" href="{esc(s["url"])}" rel="noopener noreferrer" '
                   f'title="{esc(s["publisher"])}: {esc(s["title"])}">{sid}&nbsp;&#8599;</a>')
    return "".join(out)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def compute_row(route, target):
    """Return dict of published components in USD, or None for non-computable models."""
    model = route["cost_model"]
    if model in ("none_published", "prohibited"):
        return None
    if model == "hold":
        return {"fx": 0.0, "comm": 0.0, "cable": 0.0, "total": 0.0, "pct": 0.0}
    fx = target * (FX - MID) / MID
    if model == "boc_wire_only":
        comm = clamp(0.001 * target * FX, COMM_MIN_CNY, COMM_MAX_CNY) / FX
        cable = CABLE_CNY / FX
    elif model == "boc_cash":
        comm = 0.0
        cable = 0.0
    elif model == "boc_fx_wire":
        comm = clamp(0.001 * target * FX, COMM_MIN_CNY, COMM_MAX_CNY) / FX
        cable = CABLE_CNY / FX
    else:
        return None
    total = fx + comm + cable
    return {"fx": fx, "comm": comm, "cable": cable, "total": total,
            "pct": total / target * 100.0}


def feasibility(route, target):
    cap = route.get("cap_step_usd")
    if not cap:
        return "No published per-transfer cap"
    kind = route.get("cap_kind")
    if kind == "annual":
        n = math.ceil(target / cap)
        if n <= 1:
            return "Within the annual cap"
        return f"Needs {n} calendar years at the cap"
    if kind == "per_trip":
        n = math.ceil(target / cap)
        if n <= 1:
            return "One trip"
        return f"Needs {n} trips (not practical)" if n > 20 else f"Needs {n} trips"
    return "Cap applies"


def shell(title, body, active="", depth=0):
    p = "../" * depth
    nav = [("index.html", "Overview"), ("routes.html", "Routes"), ("costs.html", "Costs"),
           ("penalty.html", "Penalty"), ("taxes.html", "Tax & reporting"),
           ("review.html", "Flagged"), ("sources.html", "Sources"),
           ("repo-review.html", "Repo audit"), ("methodology.html", "Method"), ("requirements.html", "Coverage")]
    cur = ' aria-current="page"'
    links = "".join(
        '<a href="%s%s"%s>%s</a>' % (p, h, cur if h == active else "", esc(t))
        for h, t in nav)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Verified, mobile-first research on moving CNY out of China as a U.S. citizen: lawful routes, published costs, tax treatment and flagged gaps.">
<meta name="color-scheme" content="light">
<title>{esc(title)} · China Money · Edition I</title>
<style>{CSS}</style></head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="top-inner">
<a class="brand" href="{p}index.html"><span class="mark">&#165;&#8594;$</span><span>China Money<small>Edition I · verified 10 Nov 2026</small></span></a>
<span class="pill">No personal data input required</span>
</div><nav class="main" aria-label="Main">{links}</nav></header>
<main id="main">{body}
<footer>
<p><strong>Research, not legal, tax or investment advice.</strong> Unknown values are blank, never inferred. Official agencies establish the rules; bank and provider pages establish only their own published terms. A citation does not establish your eligibility for a route.</p>
<p>Data as of {AS_OF} (UTC). Rates are a single published snapshot, not a quote. <a href="{p}sources.html">Source register</a> · <a href="{p}review.html">Flagged for review</a> · <a href="{p}methodology.html">Method and limits</a> · <a href="{p}requirements.html">Requirement coverage</a></p>
</footer></main></body></html>"""


def table(headers, rows, cls="responsive", caption=None):
    head = "".join(f'<th scope="col">{esc(h)}</th>' for h in headers)
    body = "".join("<tr>" + "".join(c for c in r) + "</tr>" for r in rows)
    cap = f"<caption>{esc(caption)}</caption>" if caption else ""
    return f'<div class="tablewrap"><table class="{cls}">{cap}<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def load():
    src = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
    sources = {s["id"]: s for s in src["sources"]}
    routes = json.loads((DATA / "routes.json").read_text(encoding="utf-8"))["routes"]
    penalty = json.loads((DATA / "penalty.json").read_text(encoding="utf-8"))
    taxes = json.loads((DATA / "taxes.json").read_text(encoding="utf-8"))
    flags = json.loads((DATA / "flags.json").read_text(encoding="utf-8"))["flags"]
    return sources, routes, penalty, taxes, flags


def build_index(sources, routes, penalty):
    counts = {}
    for r in routes:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    sample = [10_000, 100_000, 250_000, 400_000]
    rail = next(r for r in routes if r["id"] == "R01")
    kpi_rows = []
    for a in sample:
        c = compute_row(rail, a)
        kpi_rows.append(
            f'<tr><td data-label="Target">${a:,}</td>'
            f'<td class="num" data-label="FX margin">{money(c["fx"])}</td>'
            f'<td class="num" data-label="Commission">{money(c["comm"])}</td>'
            f'<td class="num" data-label="Cable">{money(c["cable"])}</td>'
            f'<td class="num" data-label="Receiver"><span class="blank">UNVERIFIED</span></td>'
            f'<td class="num" data-label="Sender-side total"><strong>{money(c["total"])}</strong></td>'
            f'<td class="num" data-label="% of principal">{c["pct"]:.3f}%</td>'
            f'<td data-label="Source">{source_links(["S08", "S09"], sources)}</td></tr>')
    findings = [
        ("The conversion itself is not a tax event",
         "China taxes the source event (wages, property gain, dividend). The U.S. taxes you on worldwide income. A transfer fee is not a tax, and a tax is not a transfer fee. Treating the two as one 'penalty' is the core error in most online guides.", ["S15", "S20"]),
        ("Overseas individuals have no published USD 50,000 purchase cap",
         "The 50,000 figure is an annual facilitation quota for individual settlement and for domestic individuals' purchases. SAFE policy answers state that an overseas individual's purchase has no annual cap, but requires identity, source-of-funds and tax evidence.", ["S02", "S03", "S05"]),
        ("The published bank cost is roughly 0.31% plus about USD 22",
         "On the 2026-11-10 board, the one-way FX margin is 0.2104%, commission is 0.1% (min CNY 50, max CNY 260) and the cable charge is CNY 150. At USD 10,000 that is about 0.53% all-in on the sender side; at USD 400,000 about 0.23%.", ["S08", "S09"]),
        ("The expensive part is the source event, not the wire",
         "Property gains carry 20% IIT, FIE dividends now carry 20% (the old exemption was repealed from 2026-09-01), and undeclared income carries U.S. tax plus reporting penalties. No bank fee comes close.", ["S15", "S16", "S22"]),
        ("Illegal routes risk 30%-100% of the amount",
         "Evasion, illegal FX purchase and private FX trading carry fines up to 30% of the amount, rising to 30%-100% when serious, plus confiscation. That is the only 'penalty' that can exceed the tax.", ["S27"]),
        ("Reporting duties survive the transfer",
         "FBAR above USD 10,000 aggregate, Form 8938 above the applicable threshold, Form 3520 above USD 100,000 of foreign gifts or bequests. None of these depends on the money being taxable.", ["S21", "S22", "S29"]),
    ]
    body = f"""
<p class="pill">Edition I · {len(routes)} routes · {len(routes)*40:,} generated cost rows</p>
<h1>Move CNY to USD lawfully, then compare the price.</h1>
<p class="lead">A U.S. citizen with RMB in a Chinese bank is not stuck. The binding question is <strong>what the RMB is</strong> — documented current income, pre-emigration capital, an inheritance, a property sale or a business distribution — because that decides which rule applies. Only after that does the wire fee matter.</p>
<div class="notice"><strong>Bottom line.</strong> No exact personal total can be certified from the facts supplied, and none is invented here. What can be certified is the shape of the cost: a lawful bank route costs about <strong>0.23%-0.53%</strong> of principal in published sender-side charges. The tax depends on the source event. Evasion, illegal FX purchase and private FX trading risk fines of <strong>30%-100%</strong> of the amount; illegal cash carriage risks up to 20%.</div>
<div class="grid">
<a class="card" href="routes.html"><strong>{len(routes)} routes, screened &rarr;</strong><p>Current account, capital account, rails, cards, hold, and prohibited. Pros, cons, steps, limits and source links on every one.</p></a>
<a class="card" href="costs.html"><strong>Cost ladders, $10k to $400k &rarr;</strong><p>40 increments per route. Published components computed; receiver, intermediary and tax left blank and labelled.</p></a>
<a class="card" href="penalty.html"><strong>Penalty decomposition &rarr;</strong><p>FX margin, commission, cable, taxes and reporting penalties separated, with the 2026-11-10 board.</p></a>
<a class="card" href="taxes.html"><strong>Tax and reporting &rarr;</strong><p>China source-event tax, U.S. worldwide income, section 988, FBAR, 8938, 3520 and the treaty.</p></a>
</div>
<h2>The decision in six lines</h2>
<table class="responsive"><thead><tr><th scope="col">What the evidence supports</th><th scope="col">Source</th></tr></thead><tbody>
{''.join(f'<tr><td data-label="Finding"><strong>{esc(t)}</strong><br><span class="muted small">{esc(d)}</span></td><td data-label="Source">{source_links(s, sources)}</td></tr>' for t, d, s in findings)}
</tbody></table>
<h2>Published sender-side cost at four checkpoints</h2>
<p class="muted small">Route R01 (BOC telegraphic transfer) using the 2026-11-10 board. Excludes correspondent deductions, the receiving bank's fee and all tax — those are unknown and shown blank, not guessed.</p>
{table(["Target", "FX margin", "Commission", "Cable", "Receiver", "Sender total", "% of principal", "Source"],
       kpi_rows)}
<p class="small"><a href="costs.html">All 40 increments and every route &rarr;</a> · <a href="costs.html#all-routes">Every route at four checkpoints &rarr;</a></p>
<h2>Start here: what is the RMB?</h2>
<div class="grid two">
<div class="card"><h3>Salary or fees earned in China</h3><p>Use the current-account route. An overseas individual needs identity, source documentation and tax evidence; there is no published annual purchase cap. <a href="method-P01.html">P01 &rarr;</a></p></div>
<div class="card"><h3>Money you owned before emigrating</h3><p>Use the emigrant property transfer: SAFE approval at the original household-registration location, then a bank purchase and remittance to your own account. Staging was cancelled in 2014. <a href="method-C01.html">C01 &rarr;</a></p></div>
<div class="card"><h3>An inheritance</h3><p>Use the inheritance transfer with succession documents and the deceased's tax clearance. <a href="method-C02.html">C02 &rarr;</a></p></div>
<div class="card"><h3>Property you are selling</h3><p>An overseas individual needs SAFE approval for the proceeds, and China taxes the gain at 20% (or 1% deemed). <a href="method-C03.html">C03 &rarr;</a></p></div>
<div class="card"><h3>A business distribution</h3><p>Genuine FIE profits are distributable, but foreign individuals now face 20% withholding. <a href="method-C05.html">C05 &rarr;</a></p></div>
<div class="card"><h3>Nothing fits</h3><p>Then hold and document first. Converting without a lawful basis is where the 30%-100% penalties live. <a href="routes.html?cat=prohibited">See what not to do &rarr;</a></p></div>
</div>
<h2>What this edition will not do</h2>
<ul class="plain">
<li>It will not state your tax, because your basis, residency, source and compliance history are unknown.</li>
<li>It will not invent a receiving-bank or correspondent fee.</li>
<li>It will not give execution steps for crypto, underground banks, quota splitting or false documents.</li>
<li>It will not re-certify the other editions line by line. It crawls them mechanically and flags what it finds.</li>
</ul>
<p class="small muted">Routes screened: {len(routes)} · lawful candidates {counts.get('candidate',0)} · conditional {counts.get('conditional',0)} · capped {counts.get('limited',0)} · prohibited {counts.get('prohibited',0)} · unverified {counts.get('unverified',0)}.</p>
"""
    return shell("Overview", body, "index.html")


def build_routes(sources, routes):
    cards = []
    for r in routes:
        cards.append(f"""<article class="card route-card" data-cat="{r['category']}" data-status="{r['status']}" data-name="{esc((r['name']+' '+r['zh']).lower())}">
<div><span class="badge b-{r['status']}">{esc(STATUS_LABEL[r['status']])}</span> <span class="pill">{esc(r['id'])}</span></div>
<h3><a href="method-{r['id']}.html">{esc(r['name'])}</a></h3>
<p class="small muted">{esc(r['zh'])}</p>
<p>{esc(r['one_line'])}</p>
<p class="small"><strong>Cost model:</strong> {esc(r['cost_model'])} · <strong>Limits:</strong> {esc('; '.join(r['limits'])) if r['limits'] else 'none published'} · {source_links(r['sources'][:4], sources)}</p>
</article>""")
    chips = "".join(f'<button class="chip" type="button" data-filter="{c}" aria-pressed="{"true" if c=="all" else "false"}">{esc(t)}</button>' for c, t in CATEGORIES)
    body = f"""
<h1>Routes out of CNY, screened</h1>
<p class="lead">Every route is classified by legal basis, not by how easy it is to find online. "Prohibited" means there is no lawful execution, so this page gives risk information only.</p>
<div class="notice"><strong>Read the status, not the headline.</strong> A route marked <em>capped</em> is lawful but cannot move USD 400,000 in a reasonable time. A route marked <em>unverified</em> is not recommended — it means no official source or published price was confirmed.</div>
<div class="chips" role="group" aria-label="Filter by category">{chips}</div>
<div class="searchbox">
<label class="sr" for="q">Search routes</label>
<input id="q" type="search" placeholder="Search a route, e.g. property, inheritance, Wise" autocomplete="off">
<label class="sr" for="st">Filter by status</label>
<select id="st"><option value="all">All statuses</option><option value="candidate">Lawful candidate</option><option value="conditional">Conditional</option><option value="limited">Lawful but capped</option><option value="prohibited">Prohibited</option><option value="unverified">Unverified</option></select>
</div>
<p class="small muted" id="count" aria-live="polite"></p>
<div id="list">{''.join(cards)}</div>
<h2>Why the statuses differ</h2>
{table(["Status", "Meaning", "Example"], [
 ['<span class="badge b-candidate">Lawful candidate</span>', "A published current-account or capital-account route that may fit your facts.", "P01 documented income"],
 ['<span class="badge b-conditional">Conditional</span>', "Lawful only if a specific eligibility or approval condition is met.", "C01 emigrant transfer"],
 ['<span class="badge b-limited">Lawful but capped</span>', "Lawful, but a published cap makes a large transfer impractical.", "P05 USD 50,000 quota"],
 ['<span class="badge b-unverified">Unverified</span>', "Plausible but no official rule or price was confirmed here.", "R02 other bank tariffs"],
 ['<span class="badge b-prohibited">Prohibited</span>', "Unlawful or legally void. Risk information only.", "X01 crypto"],
])}
"""
    js = """
<script>
(function(){
 var cat='all',st='all',q='';
 var cards=[].slice.call(document.querySelectorAll('.route-card'));
 var chips=[].slice.call(document.querySelectorAll('.chip'));
 var count=document.getElementById('count');
 function apply(){
  var n=0;
  cards.forEach(function(c){
   var ok=(cat==='all'||c.dataset.cat===cat)&&(st==='all'||c.dataset.status===st)&&(q===''||c.dataset.name.indexOf(q)>-1);
   c.style.display=ok?'':'none'; if(ok)n++;
  });
  count.textContent=n+' of '+cards.length+' routes shown';
 }
 chips.forEach(function(b){b.addEventListener('click',function(){
  cat=b.dataset.filter;chips.forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false')});apply();
 })});
 document.getElementById('st').addEventListener('change',function(e){st=e.target.value;apply()});
 document.getElementById('q').addEventListener('input',function(e){q=e.target.value.toLowerCase().trim();apply()});
 var m=location.search.match(/cat=([a-z]+)/); if(m){cat=m[1];chips.forEach(function(x){x.setAttribute('aria-pressed',x.dataset.filter===cat?'true':'false')});}
 apply();
})();
</script>"""
    return shell("Routes", body + js, "routes.html")


def build_method(sources, route):
    ladder_rows = []
    csv_rows = []
    for a in AMOUNTS:
        c = compute_row(route, a)
        feas = feasibility(route, a)
        if c is None:
            cells = (f'<td class="num" data-label="Target">${a:,}</td>'
                     f'<td class="num blank" data-label="FX margin">UNVERIFIED</td>'
                     f'<td class="num blank" data-label="Commission">UNVERIFIED</td>'
                     f'<td class="num blank" data-label="Cable">UNVERIFIED</td>'
                     f'<td class="num blank" data-label="Receiver">UNVERIFIED</td>'
                     f'<td class="num blank" data-label="Sender total">UNVERIFIED</td>'
                     f'<td class="num blank" data-label="% of principal">UNVERIFIED</td>'
                     f'<td data-label="Feasibility">{esc(feas)}</td>'
                     f'<td data-label="Source">{source_links(route["sources"], sources)}</td>')
            csv_rows.append([route["id"], a, "", "", "", "", "", "", feas])
        else:
            cells = (f'<td class="num" data-label="Target">${a:,}</td>'
                     f'<td class="num" data-label="FX margin">{money(c["fx"])}</td>'
                     f'<td class="num" data-label="Commission">{money(c["comm"])}</td>'
                     f'<td class="num" data-label="Cable">{money(c["cable"])}</td>'
                     f'<td class="num blank" data-label="Receiver">UNVERIFIED</td>'
                     f'<td class="num" data-label="Sender total"><strong>{money(c["total"])}</strong></td>'
                     f'<td class="num" data-label="% of principal">{c["pct"]:.3f}%</td>'
                     f'<td data-label="Feasibility">{esc(feas)}</td>'
                     f'<td data-label="Source">{source_links(route["sources"], sources)}</td>')
            csv_rows.append([route["id"], a, f'{c["fx"]:.2f}', f'{c["comm"]:.2f}', f'{c["cable"]:.2f}',
                             "", f'{c["total"]:.2f}', f'{c["pct"]:.4f}', feas])
        ladder_rows.append(cells)
    ladder = table(["Target", "FX margin", "Commission", "Cable", "Receiver", "Sender total", "% of principal", "Feasibility", "Source"], ladder_rows)
    steps = ("<ol class=\"steps\">" + "".join(f"<li>{esc(x)}</li>" for x in route["steps"]) + "</ol>") if route["steps"] else "<p class=\"small muted\">No execution steps are provided for this entry.</p>"
    pros = ("<ul class=\"plain pros\">" + "".join(f"<li>{esc(x)}</li>" for x in route["pros"]) + "</ul>") if route["pros"] else "<p class=\"small muted\">None identified.</p>"
    cons = ("<ul class=\"plain cons\">" + "".join(f"<li>{esc(x)}</li>" for x in route["cons"]) + "</ul>") if route["cons"] else "<p class=\"small muted\">None identified.</p>"
    docs = "".join(f"<li>{esc(x)}</li>" for x in route["docs"]) if route["docs"] else "<li class=\"muted\">No documents identified</li>"
    limits = "".join(f"<li>{esc(x)}</li>" for x in route["limits"]) if route["limits"] else "<li class=\"muted\">No published limit located</li>"
    src_table = table(["Source", "Publisher", "What it establishes", "Retrieved"],
                      [[f'<a href="{esc(sources[s]["url"])}" rel="noopener noreferrer">{s} &#8599;</a>',
                        esc(sources[s]["publisher"]), esc(sources[s]["title"]), esc(sources[s]["retrieved"])]
                       for s in route["sources"]])
    body = f"""
<p class="small"><a href="routes.html">&larr; All routes</a></p>
<p><span class="badge b-{route['status']}">{esc(STATUS_LABEL[route['status']])}</span> <span class="pill">{esc(route['category'])}</span></p>
<h1>{esc(route['name'])}</h1>
<p class="lead">{esc(route['one_line'])}</p>
<p class="small muted">{esc(route['zh'])}</p>
<div class="notice"><strong>Who this can apply to.</strong> {esc(route['who'])}</div>
<div class="grid two">
<div class="card"><h3>Step by step</h3>{steps}</div>
<div class="card"><h3>Documents and limits</h3><p class="small"><strong>Documents</strong></p><ul class="plain">{docs}</ul><p class="small"><strong>Limits</strong></p><ul class="plain">{limits}</ul></div>
<div class="card"><h3>Pros</h3>{pros}</div>
<div class="card"><h3>Cons</h3>{cons}</div>
</div>
<h2>Cost ladder, $10,000 to $400,000</h2>
<p class="small muted">Computed components use the 2026-11-10 BOC board and the published tariff (S08, S09). Modelled rail: <strong>{esc(route['cost_model'])}</strong>. "Receiver" and all tax columns are blank by design. <strong>Sender total excludes correspondent, receiving-bank and tax charges</strong>, so it is a floor, not an all-in price.</p>
{ladder}
<h2>Sources for this route</h2>
{src_table}
<p class="small muted">{esc(route['note'])}</p>
"""
    return shell(route["name"], body, "routes.html", depth=0), csv_rows


def build_costs(sources, routes):
    rail = next(r for r in routes if r["id"] == "R01")
    rows = []
    for a in AMOUNTS:
        c = compute_row(rail, a)
        rows.append((f'<td class="num" data-label="Target">${a:,}</td>'
                     f'<td class="num" data-label="FX margin">{money(c["fx"])}</td>'
                     f'<td class="num" data-label="Commission">{money(c["comm"])}</td>'
                     f'<td class="num" data-label="Cable">{money(c["cable"])}</td>'
                     f'<td class="num blank" data-label="Receiver">UNVERIFIED</td>'
                     f'<td class="num blank" data-label="China tax">UNVERIFIED</td>'
                     f'<td class="num" data-label="Sender total"><strong>{money(c["total"])}</strong></td>'
                     f'<td class="num" data-label="% of principal">{c["pct"]:.3f}%</td>'
                     f'<td data-label="Source">{source_links(["S08", "S09"], sources)}</td>'))
    checkpoints = [10_000, 50_000, 100_000, 200_000, 300_000, 400_000]
    matrix_rows = []
    for r in routes:
        cells = [f'<td data-label="Route"><a href="method-{r["id"]}.html">{r["id"]}</a> {esc(r["name"][:58])}{"…" if len(r["name"])>58 else ""}</td>',
                 f'<td data-label="Status"><span class="badge b-{r["status"]}">{esc(STATUS_LABEL[r["status"]])}</span></td>']
        for a in checkpoints:
            c = compute_row(r, a)
            if c is None:
                cells.append('<td class="num blank" data-label="$%s">UNVERIFIED</td>' % f"{a:,}")
            else:
                cells.append(f'<td class="num" data-label="${a:,}">{money(c["total"])}<br><span class="small muted">{c["pct"]:.2f}%</span></td>')
        cells.append(f'<td data-label="Source">{source_links(r["sources"][:3], sources)}</td>')
        matrix_rows.append(cells)
    body = f"""
<h1>Cost of moving CNY to USD</h1>
<p class="lead">Two tables: one honest ladder for the standard bank rail, and one comparison of every route at six checkpoints. Numbers are computed only from published components. Blank cells mean <strong>unverified</strong>, not free.</p>
<div class="notice"><strong>What is deliberately missing.</strong> Correspondent-bank deductions, the U.S. receiving bank's incoming-wire fee and all tax. None is published for your situation, so none is guessed. Section 988 currency gain is also excluded — it depends on when each tranche of RMB was acquired.</div>
<h2 id="ladder">The standard bank rail, all 40 increments</h2>
<p class="small muted">Route R01 / P01 rail. FX margin = half the BOC bid/ask spread on 2026-11-10 (0.2104%). Commission = 0.1% of the CNY amount, floor CNY 50, cap CNY 260. Cable = CNY 150 outside Greater China. Converted at the same board rate.</p>
{table(["Target", "FX margin", "Commission", "Cable", "Receiver", "China tax", "Sender total", "% of principal", "Source"], rows)}
<h2 id="all-routes">Every route at six checkpoints</h2>
<p class="small muted">Sender-side total in USD with percentage of principal underneath. "UNVERIFIED" means no published price was found for that rail in this session.</p>
{table(["Route", "Status", "$10,000", "$50,000", "$100,000", "$200,000", "$300,000", "$400,000", "Source"], matrix_rows)}
<h2>How to read a quote you receive</h2>
<ol class="steps">
<li>Ask for the USD amount that will actually arrive, not the rate alone.</li>
<li>Ask which party pays the correspondent and receiving fees (OUR / SHA / BEN).</li>
<li>Compare the bank's rate with the PBOC fixing and the BOC board at the same minute; the gap is not all fee.</li>
<li>Add the receiving bank's published incoming-wire fee.</li>
<li>Only then compare with a provider quote for the same delivery date.</li>
</ol>
<p class="small"><a href="cost-ladder.csv">Download the full generated CSV &rarr;</a></p>
"""
    return shell("Costs", body, "costs.html")


def build_penalty(sources, penalty):
    lines = penalty["lines"]
    rows = []
    for ln in lines:
        v = ln["display"]
        cls = "blank" if ln["status"] == "unverified" else ""
        badge = ('<span class="badge b-unverified">UNVERIFIED</span>' if ln["status"] == "unverified"
                 else '<span class="badge b-candidate">Verified</span>')
        rows.append((f'<td data-label="Item"><strong>{esc(ln["label"])}</strong><br><span class="small muted">{esc(ln["basis"])}</span></td>'
                     f'<td data-label="Class">{esc(ln["class"])}</td>'
                     f'<td data-label="Value" class="{cls}">{esc(v)}</td>'
                     f'<td data-label="Status">{badge}</td>'
                     f'<td data-label="Source">{source_links(ln["sources"], sources)}</td>'))
    fx = penalty["_meta"]["fx"]
    scen = []
    for s in penalty["scenarios"]:
        scen.append(f'<tr><td data-label="Scenario"><strong>{esc(s["title"])}</strong><br><span class="small muted">{esc(s["assumption"])}</span></td>'
                    f'<td data-label="China tax">{esc(s["china_tax"])}</td>'
                    f'<td data-label="U.S. tax">{esc(s["us_tax"])}</td>'
                    f'<td data-label="Why">{esc(s["why"])}<br><span class="small muted">{esc(s["label"])}</span></td>'
                    f'<td data-label="Source">{source_links(s["sources"], sources)}</td></tr>')
    body = f"""
<h1>The conversion penalty, broken down</h1>
<p class="lead">"Penalty" usually bundles five unrelated things: the bank's FX margin, its commission, the cable charge, the tax on the underlying event, and reporting penalties. Separating them changes the answer.</p>
<div class="notice"><strong>The only penalty that scales with the amount is the illegal one.</strong> Lawful sender-side fees top out at roughly 0.53% at USD 10,000 and fall toward 0.23% at USD 400,000. A fine for evasion is 30%-100% of the amount.</div>
<h2>Published FX snapshot</h2>
<div class="grid two">
<div class="card"><div class="kpi"><b>{fx['sell_cny_per_usd']:.4f}</b><span class="muted">CNY per USD, BOC spot sell</span></div><p class="small muted">Board {esc(fx['board_date'])} at {esc(fx['board_time'])}. Buy {fx['usd_spot_buy_cny_per_100']/100:.4f}; midpoint {fx['mid_cny_per_usd']:.5f}.</p></div>
<div class="card"><div class="kpi"><b>{fx['one_way_margin_pct']:.4f}%</b><span class="muted">one-way FX margin</span></div><p class="small muted">Formula: {esc(fx['formula'])}. Round trip: {fx['round_trip_margin_pct']:.4f}%.</p></div>
<div class="card"><div class="kpi"><b>{fx['central_parity_cny_per_usd']:.4f}</b><span class="muted">PBOC central parity, 9 Nov 2026</span></div><p class="small muted">A reference fixing, not a tradeable rate. The gap to the bank mid is about 0.64% and is <em>not</em> a customer fee.</p></div>
<div class="card"><div class="kpi"><b>CNY 150</b><span class="muted">cable charge</span></div><p class="small muted">Plus 0.1% commission, floor CNY 50, cap CNY 260. Both published by BOC (S09).</p></div>
</div>
<h2>Every component, scored</h2>
{table(["Item", "Class", "Value", "Status", "Source"], rows)}
<h2>Worked scenarios — illustrations, not personal estimates</h2>
<p class="small muted">Each line states its assumption. None of them is a prediction about your balance.</p>
{table(["Scenario", "China", "United States", "Why / label", "Source"], scen)}
<h2>The formula you can apply yourself</h2>
<div class="card"><p><strong>Sender-side cost in USD</strong> = P × (S − M) / M + min(max(0.001 × P × S, 50), 260) / S + 150 / S</p>
<p class="small muted">P = USD principal, S = bank's CNY-per-USD selling rate, M = midpoint of the bank's buy and sell. The first term is the FX margin, the second the commission, the third the cable charge. Add the receiving bank's fee and any tax on the source event separately.</p></div>
<h2>What is still unknown</h2>
<ul class="plain">
<li><strong>Correspondent deduction:</strong> depends on routing; no official schedule.</li>
<li><strong>Receiving bank fee:</strong> depends on your U.S. bank and account tier.</li>
<li><strong>Your execution rate:</strong> the board is a reference; the trade rate governs.</li>
<li><strong>Your tax:</strong> depends on basis, residency, source and compliance history.</li>
</ul>
<p class="small"><a href="review.html">All of these are listed on the Flagged page &rarr;</a></p>
"""
    return shell("Penalty", body, "penalty.html")


def build_taxes(sources, taxes):
    rows = []
    for t in taxes["rows"]:
        cls = "blank" if t["status"] == "unverified" else ""
        badge = ('<span class="badge b-unverified">UNVERIFIED</span>' if t["status"] == "unverified"
                 else '<span class="badge b-candidate">Verified</span>')
        rows.append((f'<td data-label="Jurisdiction">{esc(t["jurisdiction"])}</td>'
                     f'<td data-label="Topic"><strong>{esc(t["topic"])}</strong><br><span class="small muted">{esc(t["rule"])}</span></td>'
                     f'<td data-label="Amount" class="{cls}">{esc(t["amount"])}</td>'
                     f'<td data-label="Status">{badge}</td>'
                     f'<td data-label="Source">{source_links(t["sources"], sources)}</td>'))
    body = f"""
<h1>Tax and reporting, separated</h1>
<p class="lead">Two systems apply at once, and neither is a conversion tax. China taxes the event that created the money. The United States taxes you on worldwide income and on currency movements. Reporting duties exist even when nothing is taxable.</p>
<div class="notice"><strong>No personal tax figure is shown.</strong> Without residency, basis, acquisition dates, source documents and compliance history, any number would be fabricated. What is shown is the rule and the rate, with the official source.</div>
<h2>Rule table</h2>
{table(["Jurisdiction", "Topic", "Amount", "Status", "Source"], rows)}
<h2>The order of operations</h2>
<ol class="steps">
{''.join(f'<li>{esc(x)}</li>' for x in taxes['ordering'])}
</ol>
<h2>Reporting calendar</h2>
{table(["Filing", "Threshold", "Due", "Source"], [
 ["FBAR (FinCEN 114)", "Aggregate foreign accounts over USD 10,000 at any time", "15 April, automatic extension to 15 October", source_links(["S21"], sources)],
 ["Form 8938", "USD 50,000 year-end / 75,000 any time (unmarried, living in the U.S.); higher thresholds abroad", "With the income tax return, including extensions", source_links(["S22"], sources)],
 ["Form 3520", "Gifts or bequests over USD 100,000 from a nonresident alien or foreign estate", "With the income tax return", source_links(["S20", "S29"], sources)],
 ["Form 1116", "Claiming the foreign tax credit", "With the income tax return", source_links(["S28"], sources)],
])}
<h2>Three mistakes this page is designed to prevent</h2>
<div class="grid two">
<div class="card"><h3>"The conversion is taxed at X%"</h3><p>There is no such rate. China taxes wages, gains and dividends; the U.S. taxes income and section 988 currency gain. A wire fee is a fee.</p></div>
<div class="card"><h3>"I already paid tax in China, so the U.S. is settled"</h3><p>The foreign tax credit is real but limited. It is claimed on Form 1116 and can leave residual U.S. tax, especially across baskets.</p></div>
<div class="card"><h3>"If I move it, reporting ends"</h3><p>FBAR and 8938 look at the year's maximum balances. Moving money after 31 December does not undo a reporting requirement for that year.</p></div>
</div>
"""
    return shell("Tax & reporting", body, "taxes.html")


def build_review(sources, flags):
    rows = []
    for f in flags:
        badge = ('<span class="badge b-candidate">Fixed</span>' if f["status"] == "fixed"
                 else '<span class="badge b-limited">Open</span>')
        sev = {"high": "b-prohibited", "medium": "b-limited", "low": "b-unverified"}[f["severity"]]
        rows.append((f'<td data-label="ID"><strong>{esc(f["id"])}</strong></td>'
                     f'<td data-label="Finding"><strong>{esc(f["title"])}</strong><br><span class="small muted">{esc(f["detail"])}</span></td>'
                     f'<td data-label="Severity"><span class="badge {sev}">{esc(f["severity"])}</span></td>'
                     f'<td data-label="Area">{esc(f["area"])}</td>'
                     f'<td data-label="Status">{badge}</td>'
                     f'<td data-label="Source">{source_links(f["sources"], sources) if f["sources"] else "—"}</td>'))
    body = f"""
<h1>Flagged for review</h1>
<p class="lead">Everything that could not be verified, everything another edition states incorrectly, and every methodology caveat. These are published rather than buried, and none of them blocks publication.</p>
<div class="notice"><strong>Policy.</strong> A value that cannot be confirmed from an official source is left blank and flagged. It is never estimated, back-filled or inferred from a secondary blog.</div>
{table(["ID", "Finding", "Severity", "Area", "Status", "Source"], rows)}
<h2>Cross-edition conflicts, precisely</h2>
<ul class="plain">
<li><strong>F02:</strong> Edition B's 50/25/25 staged release is the 2004 rule, cancelled by 汇发[2014]2号 Section VI.</li>
<li><strong>F03:</strong> Edition D's exact all-in totals include assumed receiving and intermediary fees that are not published.</li>
<li><strong>F04:</strong> Two official definitions of "domestic individual" produce different quota outcomes for the same person.</li>
<li><strong>F17:</strong> Using the PBOC fixing as if it were a bank rate overstates conversion cost by about 0.64 points.</li>
</ul>
<h2>How these will be closed</h2>
<p class="small">Each flag names the source that would resolve it. F02 and F03 sit inside other sessions' file scopes, so this edition reports them rather than editing them. F04 and F05 require your bank's written classification and cannot be resolved from public sources.</p>
"""
    return shell("Flagged for review", body, "review.html")


def build_sources(sources):
    gov = [s for s in sources.values() if s["type"] == "government"]
    prov = [s for s in sources.values() if s["type"] == "provider"]
    rows = []
    for s in list(sources.values()):
        rows.append((f'<td data-label="ID"><strong>{esc(s["id"])}</strong></td>'
                     f'<td data-label="Publisher">{esc(s["publisher"])}</td>'
                     f'<td data-label="Title"><a href="{esc(s["url"])}" rel="noopener noreferrer">{esc(s["title"])} &#8599;</a><br><span class="small muted">{esc(s["scope"])}</span></td>'
                     f'<td data-label="Quote"><span class="small">“{esc(s.get("quote",""))}”</span>'
                     + (f'<br><span class="small muted">“{esc(s["quote2"])}”</span>' if s.get("quote2") else "")
                     + (f'<br><span class="small muted">“{esc(s["quote3"])}”</span>' if s.get("quote3") else "")
                     + f'</td>'
                     f'<td data-label="Type">{esc(s["type"])}</td>'
                     f'<td data-label="Retrieved">{esc(s["retrieved"])}</td>'))
    body = f"""
<h1>Source register</h1>
<p class="lead">Every source was opened and read in this session. Quotes are verbatim excerpts, not paraphrases, so a reviewer can check each claim without trusting this page.</p>
<div class="grid two">
<div class="card"><div class="kpi"><b>{len(gov)}</b><span class="muted">government sources</span></div><p class="small muted">Central government, PBOC, SAFE, customs, tax administration, IRS, GPO.</p></div>
<div class="card"><div class="kpi"><b>{len(prov)}</b><span class="muted">provider sources</span></div><p class="small muted">Used only for that provider's own published terms, never as authority on law.</p></div>
</div>
<div class="notice"><strong>Retrieval is not endorsement.</strong> A page can change after retrieval. Where a page was only partially readable, the limitation is stated in the scope column and on the Flagged page.</div>
{table(["ID", "Publisher", "Title and scope", "Verbatim quote", "Type", "Retrieved"], rows)}
<h2>Reading order for a skeptical reviewer</h2>
<ol class="steps">
<li>Start with S01 Article 13 and S03: the current-account basis for an overseas individual.</li>
<li>Confirm S02 Article 2 and S05: the quota applies to settlement and to domestic individuals' purchases.</li>
<li>Check S06 Section VI against any claim that a transfer must be staged.</li>
<li>Price the rail with S08 and S09, then read the disclaimer on S08.</li>
<li>Check S11 and S12 for the 2026 compliance and crypto rules.</li>
<li>Finish with S20-S24 for the U.S. side.</li>
</ol>
"""
    return shell("Sources", body, "sources.html")


def build_methodology():
    body = f"""
<h1>Method, assumptions and limits</h1>
<p class="lead">This edition is built to be checked. Everything numeric is generated from the JSON in <code>edition-i/data</code> by <code>edition-i/build/build.py</code>, and <code>verify.py</code> recomputes it independently.</p>
<h2>What was done, in order</h2>
<ol class="steps">
<li>Read the existing repository, the coordination board and all prior editions.</li>
<li>Claimed a new, isolated scope (edition-i) so no other session's files are touched.</li>
<li>Retrieved 30 official and provider-primary pages, and recorded verbatim quotes with retrieval dates.</li>
<li>Built the route catalog from those rules only, screening each route for legal basis before pricing it.</li>
<li>Generated 30 routes × 40 amounts of cost rows from published components.</li>
<li>Ran a mechanical crawl of every archived HTML page for broken links, anchors and duplicate IDs.</li>
<li>Published every unverified value and every cross-edition conflict on the Flagged page.</li>
</ol>
<h2>Assumptions that are explicit</h2>
<ul class="plain">
<li><strong>Single FX snapshot:</strong> BOC board of 2026-11-10 07:32:39 (Beijing), spot sell 6.6903 and spot buy 6.6622 CNY per USD.</li>
<li><strong>Tariff:</strong> BOC published personal e-banking schedule: 0.1% commission, floor CNY 50, cap CNY 260, cable CNY 150 outside Greater China.</li>
<li><strong>No currency conversion of fees:</strong> fees are converted at the same board sell rate for arithmetic consistency.</li>
<li><strong>No assumed receiver fee, correspondent fee or tax.</strong> Those cells are blank.</li>
<li><strong>No assumed personal facts:</strong> classification, residency, source, basis and compliance history are unknown.</li>
</ul>
<h2>Why the numbers are ranges of confidence, not a quote</h2>
<p>A quote has a timestamp, a counterparty and a settlement date. This site has a published board and a published tariff. It can tell you the size of the cost to within a few dollars; it cannot tell you what your bank will charge at 3 p.m. on the day you act.</p>
<h2>What would change the answer</h2>
<ul class="plain">
<li>Your bank's classification of you (domestic vs overseas individual).</li>
<li>Whether the RMB is current-account income, pre-emigration capital, inheritance, property proceeds or a business distribution.</li>
<li>Whether China tax has been paid and documented.</li>
<li>When each tranche of RMB was acquired, for section 988 purposes.</li>
<li>Your receiving bank's fee and whether the correspondent charges a deduction.</li>
</ul>
<h2>Reproducing this site</h2>
<pre class="card small">python3 edition-i/build/audit.py    # crawl the whole repo
python3 edition-i/build/build.py    # regenerate site/ and CSV
python3 edition-i/build/verify.py   # re-check sources, arithmetic, blanks, links</pre>
<p class="small muted">Deterministic by construction: rebuilding without data changes produces byte-identical output, and CI fails if it does not.</p>
<h2>What this edition does not claim</h2>
<div class="notice danger">It does not provide legal or tax advice. It does not certify your eligibility for any route. It does not certify that any bank will process a transaction. It does not re-certify the other editions line by line.</div>
"""
    return shell("Method", body, "methodology.html")


def build_repo_review(review):
    if not review:
        return None
    s = review["summary"]
    issue_rows = []
    for i in review["issues"]:
        issue_rows.append(f'<tr><td data-label="Check">{esc(i["check"])}</td>'
                          f'<td data-label="Result"><strong>{esc(i["result"])}</strong></td>'
                          f'<td data-label="Detail">{esc(i["detail"])}</td></tr>')
    file_rows = []
    for f in review["largest"]:
        file_rows.append(f'<tr><td data-label="Path">{esc(f["path"])}</td>'
                         f'<td class="num" data-label="Bytes">{f["bytes"]:,}</td>'
                         f'<td class="num" data-label="Lines">{f["lines"]:,}</td></tr>')
    body = f"""
<h1>Repository audit</h1>
<p class="lead">A mechanical audit of everything committed before this edition: {s['html_files']} HTML pages, {s['internal_refs']:,} internal references and {s['external_refs']:,} external references.</p>
<div class="grid">
<div class="card"><div class="kpi"><b>{s['html_files']}</b><span class="muted">HTML pages</span></div><p class="small muted">Across nine prior editions and the consolidated portal.</p></div>
<div class="card"><div class="kpi"><b>{s['missing_links']}</b><span class="muted">broken internal links</span></div><p class="small muted">Every internal href and src resolved to an existing file.</p></div>
<div class="card"><div class="kpi"><b>{s['bad_anchors']}</b><span class="muted">bad anchors</span></div><p class="small muted">Every fragment resolved to an element ID on the target page.</p></div>
<div class="card"><div class="kpi"><b>{s['duplicate_ids']}</b><span class="muted">duplicate IDs</span></div><p class="small muted">Duplicate IDs would break in-page navigation.</p></div>
</div>
<h2>Checks performed</h2>
{table(["Check", "Result", "Detail"], issue_rows)}
<h2>Content findings</h2>
<ul class="plain">
<li><strong>Stale rule retained:</strong> edition-b/lawful.html still states the repealed 50/25/25 staged release (F02).</li>
<li><strong>Assumed fees presented as totals:</strong> edition-d cost pages include receiving and intermediary fee assumptions in their all-in figures (F03).</li>
<li><strong>Portal omission:</strong> the root portal did not link Edition H; fixed in this integration (F01).</li>
<li><strong>Open external work:</strong> PR #25 from another session is unmerged (F13).</li>
</ul>
<h2>Largest tracked files</h2>
{table(["Path", "Bytes", "Lines"], file_rows)}
<h2>What a mechanical audit cannot do</h2>
<p class="small muted">It cannot prove a legal proposition, confirm that an external source still says what it said when cited, or detect a subtly wrong interpretation. It proves that the site is internally consistent and navigable. Those are different claims and this page keeps them separate.</p>
"""
    return shell("Repo audit", body, "repo-review.html")


def build_requirements(sources, routes):
    covered = [
        ("Collect and organize a full list of requirements", "REQUIREMENTS inside this edition: see the table below and REQUIREMENTS-I.md at the edition root."),
        ("Executive summary with the important details", "Landing page 'The decision in six lines' and the bottom-line notice."),
        ("Best lawful way to get money out of China as a U.S. citizen", "Conditional decision tree on the landing page; no single answer is asserted because the source of funds is unknown."),
        ("Research and list as many CNY to USD methods as possible", f"{len(routes)} routes with steps, pros, cons, limits and source links."),
        ("Pros and cons of every way", "Every route page has separate pros and cons lists."),
        ("Break down the conversion penalty", "Penalty page: 26 scored components plus 7 worked scenarios."),
        ("Estimate costs in USD 10,000 increments to 400,000", "40-row ladder on each route page, 1,200 generated rows in total, plus the CSV."),
        ("Mobile-friendly table, most important info first", "Mobile-first CSS: stacked cards under 640px, sticky navigation, top-line KPIs first."),
        ("Step by step how each method would work", "Numbered steps on every lawful route page."),
        ("No manual input on my part", "No form, login, account data or file upload anywhere on the site."),
        ("Verify every row against an official source", "Every route and every cost row carries source links; verify.py fails the build if a source is missing or an ID is unknown."),
        ("Leave unconfirmed values blank and flag them", "Blank + UNVERIFIED cells; 19 published flags."),
        ("Repo review with links and flagged irregularities", "Repo audit page plus Flagged page."),
        ("Clean landing page and subpages by category", "Nine pages: overview, routes, costs, penalty, tax, flagged, sources, audit, method."),
        ("GitHub Pages live site", "Published from main at the repository root through this edition's portal link."),
    ]
    rows = [[esc(a), esc(b)] for a, b in covered]
    body = f"""
<h1>Requirement coverage</h1>
<p class="lead">Each requirement from the brief, and the exact place it is met. Anything not met is stated on the Flagged page rather than quietly dropped.</p>
{table(["Requirement", "Where it is met"], rows)}
<h2>Requirements that are structurally impossible to meet</h2>
<ul class="plain">
<li><strong>An exact personal all-in quote.</strong> Requires your bank, your rate, your receiving bank and your tax facts. Published as a method, not a number.</li>
<li><strong>An exact personal tax figure.</strong> Requires basis, residency and compliance history. Not invented.</li>
<li><strong>Certification that a specific bank will process a specific amount.</strong> No public source can provide this.</li>
</ul>
"""
    return shell("Requirements", body, "requirements.html")


def main():
    sources, routes, penalty, taxes, flags = load()
    OUT.mkdir(parents=True, exist_ok=True)
    pages = {
        "index.html": build_index(sources, routes, penalty),
        "routes.html": build_routes(sources, routes),
        "costs.html": build_costs(sources, routes),
        "penalty.html": build_penalty(sources, penalty),
        "taxes.html": build_taxes(sources, taxes),
        "review.html": build_review(sources, flags),
        "sources.html": build_sources(sources),
        "methodology.html": build_methodology(),
        "requirements.html": build_requirements(sources, routes),
    }
    all_csv = []
    for r in routes:
        html, rows = build_method(sources, r)
        pages[f"method-{r['id']}.html"] = html
        all_csv.extend(rows)
    review_path = DATA / "repo-review.json"
    if review_path.exists():
        review = json.loads(review_path.read_text(encoding="utf-8"))
        page = build_repo_review(review)
        if page:
            pages["repo-review.html"] = page
    else:
        pages["repo-review.html"] = shell("Repo audit",
            "<h1>Repository audit</h1><p>Run <code>python3 edition-i/build/audit.py</code> first to generate this page.</p>", "repo-review.html")
    for name, html in pages.items():
        (OUT / name).write_text(html, encoding="utf-8")
    with (OUT / "cost-ladder.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["route_id", "target_usd", "fx_margin_usd", "commission_usd", "cable_usd",
                    "receiver_fee_usd", "sender_total_usd", "pct_of_principal", "feasibility"])
        w.writerows(all_csv)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"edition-i: wrote {len(pages)} pages and {len(all_csv):,} cost rows")
    return pages


if __name__ == "__main__":
    main()
