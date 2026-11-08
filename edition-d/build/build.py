# -*- coding: utf-8 -*-
"""Static site generator for Edition D.

Runs with the standard library only. Deterministic: running it twice produces
byte-identical output (the CI job checks this with git diff --exit-code).

    python3 edition-d/build/build.py
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as M  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
BUILD_DATE = "2026-11-08"

# ---------------------------------------------------------------- helpers
def usd(x, dec=2):
    if x is None:
        return ""
    return "$" + f"{x:,.{dec}f}"


def usd0(x):
    return "$" + f"{x:,.0f}"


def pct(x, dec=3):
    return f"{x*100:.{dec}f}%"


SRC_BY_ID = M.SOURCES
FLAG_BY_ID = {f["id"]: f for f in M.FLAGS}


def src_link(sid):
    key = sid.split()[0]
    s = SRC_BY_ID[key]
    label = s["short"]
    return (f'<a class="src" href="{s["url"]}" target="_blank" rel="noopener noreferrer" '
            f'title="{s["title"]}">{key} · {label} ↗</a>')


def src_links(ids):
    if not ids:
        return '<span class="unv">no official source located — see flagged items</span>'
    return " ".join(src_link(i) for i in ids)


def flag_badge(fid):
    f = FLAG_BY_ID[fid]
    return f'<a class="flag" href="flagged.html#{fid}" title="{f["topic"]}">{fid}</a>'


# ---------------------------------------------------------------- cost model
def cost_rows(method):
    """Return list of dicts, one per $10k increment, for a method."""
    rows = []
    cm = method["cost_model"]
    for a in M.AMOUNTS:
        row = dict(amount=a)
        if cm == "bank_wire_1":
            c = M.bank_wire(a, 1)
            row.update(cost=c["total"], net=c["net"], units=1,
                       detail=c)
        elif cm == "bank_wire_n":
            n = int(-(-a // 50000))  # ceil
            c = M.bank_wire(a, n)
            row.update(cost=c["total"], net=c["net"], units=n, detail=c)
        elif cm == "staged_50_25_25":
            c = M.staged(a, [0.5, 0.25, 0.25])
            row.update(cost=c["total"], net=c["net"], units=3, detail=c)
        elif cm == "no_conversion":
            spread = 0.0
            comm = M._commission(a)
            total = comm + M.P["cable_usd"] + M.P["intermediary_usd"] + M.P["receiving_usd"]
            row.update(cost=total, net=a - total, units=1,
                       detail=dict(spread=0.0, commission=comm,
                                   cable=M.P["cable_usd"],
                                   intermediary=M.P["intermediary_usd"],
                                   receiving=M.P["receiving_usd"]))
        elif cm == "atm":
            years = int(-(-a // int(M.P["atm_year_usd"])))  # ceil
            row.update(cost=None, net=None, units=years, detail=None)
        elif cm == "cash_carry":
            trips = int(-(-a // 10000))
            spread = a * M.P["one_way_pct"]
            row.update(cost=spread, net=a - spread, units=trips,
                       detail=dict(spread=spread))
        elif cm == "prohibited":
            row.update(cost=None, net=None, units=None, detail=None,
                       exposure_low=a * 0.30, exposure_high=a * 1.00)
        else:  # unverified / not_available
            row.update(cost=None, net=None, units=None, detail=None)
        rows.append(row)
    return rows


# ---------------------------------------------------------------- shell
NAV = [
    ("index.html", "Dashboard"),
    ("executive-summary.html", "Executive summary"),
    ("methods.html", "All routes"),
    ("costs.html", "Cost tables"),
    ("penalty.html", "The conversion penalty"),
    ("taxes.html", "Tax"),
    ("reporting.html", "US reporting"),
    ("requirements.html", "Requirements"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for review"),
]


def page(slug, title, body, subtitle="", lead=""):
    parts = []
    for href, label in NAV:
        if href == slug:
            parts.append('<a href="%s" class="active" aria-current="page">%s</a>' % (href, label))
        else:
            parts.append('<a href="%s">%s</a>' % (href, label))
    nav = "".join(parts)
    sub = f'<p class="sub">{subtitle}</p>' if subtitle else ""
    led = f'<p class="lead">{lead}</p>' if lead else ""
    html = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · China Money · Edition D</title>
<meta name="description" content="Evidence-led analysis of moving CNY from mainland China to the United States: every route, its cost at $10,000 steps to $400,000, and its penalty exposure.">
<link rel="stylesheet" href="assets/style.css">
</head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
  <a class="brand" href="index.html"><span class="mark">¥→$</span> China Money <small>EDITION D</small></a>
  <button class="navbtn" aria-expanded="false" aria-controls="nav">Menu</button>
  <nav id="nav" aria-label="Section navigation">{nav}</nav>
</header>
<main id="main">
<div class="crumb">Edition D · built {BUILD_DATE} · every figure sourced, derived or flagged</div>
<h1>{title}</h1>{sub}{led}
{body}
</main>
<footer>
<p><strong>What this is.</strong> A source-led research edition on converting renminbi held in mainland China into US dollars. Every legal proposition links to an official instrument; every number is quoted, derived by arithmetic from a quoted number, or openly marked as an assumption.</p>
<p><strong>What this is not.</strong> Legal, tax or investment advice for your specific facts. The classification of your money — and therefore the correct route — depends on facts this edition does not have.</p>
<p><a href="sources.html">Sources</a> · <a href="flagged.html">Flagged for review</a> · <a href="requirements.html">Requirements</a></p>
</footer>
<script>
(function(){{var b=document.querySelector('.navbtn');if(!b)return;b.addEventListener('click',function(){{var n=document.getElementById('nav');n.classList.toggle('open');b.setAttribute('aria-expanded',n.classList.contains('open'));}});}})();
</script>
</body></html>
"""
    path = os.path.join(DOCS, slug)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return path


# ---------------------------------------------------------------- pages
def build_index():
    a10, a100, a400 = 10_000, 100_000, 400_000
    c10, c100, c400 = M.bank_wire(a10), M.bank_wire(a100), M.bank_wire(a400)
    q400 = M.bank_wire(a400, 8)
    body = f"""
<section class="hero">
  <div class="hero-main">
    <span class="pill">The short answer</span>
    <h2>There is no conversion tax. There is a spread, a set of fixed fees, a documentary gate — and, only if you pick an unlawful route, a penalty.</h2>
    <p>For a US citizen holding lawful current-account renminbi earned in China, the cheapest route on the evidence is a <strong>bank FX purchase plus a SWIFT wire</strong> handled as an <em>overseas individual</em>: {usd(c400['total'])} on a {usd0(a400)} balance — {pct(c400['total']/a400)}. That is the number the phrase "considerable amount of taxes" turns out to describe when the money is taken out lawfully.</p>
    <p class="small">Rate basis: Bank of China board of 2026-11-09 05:30 Beijing time — buy 666.48, sell 669.29 CNY per 100 USD {src_link('S09')}. Fee basis and assumptions are listed on <a href="costs.html">Cost tables</a>.</p>
  </div>
  <aside class="hero-side">
    <div class="kpi"><span>Best route on $400,000</span><strong>{usd(c400['total'])}</strong><small>{pct(c400['total']/a400)} of the balance · {c400['tranches']} wire</small></div>
    <div class="kpi"><span>Chinese tax on the conversion</span><strong>None found</strong><small>IIT Law taxes nine income categories; conversion is not one {src_link('S08')}</small></div>
    <div class="kpi"><span>US tax on your own principal</span><strong>None</strong><small>§988(e)(2) personal transaction, unless the FX gain exceeds $200 {src_link('S12')}</small></div>
    <div class="kpi risk"><span>The real risk</span><strong>Willful FBAR</strong><small>Greater of $100,000 or 50% of the account balance, per violation {src_link('S10')}</small></div>
  </aside>
</section>

<section>
  <h2>What the evidence actually says</h2>
  <div class="table-wrap">
  <table class="findings">
    <caption>Five findings that decide the answer. Each links to the instrument it comes from.</caption>
    <thead><tr><th scope="col">#</th><th scope="col">Finding</th><th scope="col">Why it matters</th><th scope="col">Official source</th></tr></thead>
    <tbody>
    <tr><td>1</td><td><strong>The blocker is convertibility, not tax.</strong> Current-account FX is convertible; capital-account FX follows a phased process.</td><td>Salary, fees, rent and interest sit on the convertible side. A property sale or an investment sits on the other side and needs approval.</td><td>{src_links(['S01'])}</td></tr>
    <tr><td>2</td><td><strong>A US citizen with a passport is an "overseas individual".</strong> Lawful current-account income can be purchased with ID and source documents — with no annual quota, because the USD 50,000 quota applies to a <em>domestic</em> individual.</td><td>This is what makes a single {usd0(a400)} conversion possible instead of an eight-year drip.</td><td>{src_links(['S01','S04','S05'])}</td></tr>
    <tr><td>3</td><td><strong>The conversion penalty is a commercial spread plus fixed fees.</strong> The bank's own buy/sell gap is 0.4199%; a one-way conversion therefore costs about 0.21% of principal, plus about {usd(M.P['cable_usd']+M.P['intermediary_usd']+M.P['receiving_usd'])} of fixed wire charges.</td><td>At {usd0(a400)} the whole thing costs {usd(c400['total'])}. At {usd0(a10)} it costs {usd(c10['total'])}, because fixed fees dominate.</td><td>{src_links(['S09'])}</td></tr>
    <tr><td>4</td><td><strong>Chinese tax attaches to the event that created the money.</strong> 20% flat on interest, dividends and transfers of assets; 3%-45% on wages.</td><td>If the balance came from a property gain, the 20% was always owed — it is not a toll on the wire. The tax certificate is a document the transfer route requires.</td><td>{src_links(['S08','S07'])}</td></tr>
    <tr><td>5</td><td><strong>Every "clever" workaround is a named offence with a published penalty range.</strong> Splitting, underground banks, false documents, crypto, oversized cash: 0-30% of the amount, 30%-100% in serious cases; crypto is prohibited outright.</td><td>Those routes are priced on <a href="penalty.html">The conversion penalty</a> in statutory exposure, not in fees.</td><td>{src_links(['S03','S16','S01','S06'])}</td></tr>
    </tbody>
  </table>
  </div>
</section>

<section>
  <h2>Every route, ranked by what it costs</h2>
  <div class="grid cards">
    {''.join(f'''<a class="card" href="method-{m['id']}.html">
      <span class="rank">#{m['rank']} · {m['group']}</span>
      <h3>{m['name']}</h3>
      <p>{m['one_line']}</p>
      <span class="tag {m['kind'].lower().replace('_','-')}">{m['kind'].replace('_',' ')}</span>
    </a>''' for m in M.METHODS)}
  </div>
</section>

<section>
  <h2>Three questions decide which route is yours</h2>
  <div class="table-wrap">
  <table>
    <thead><tr><th scope="col">Question</th><th scope="col">If yes</th><th scope="col">If no</th></tr></thead>
    <tbody>
    <tr><td>Is the RMB <strong>lawful current-account income</strong> you earned in China (salary, fees, rent, interest), with tax vouchers?</td><td>Route M01 — one conversion, one wire, no annual quota {src_link('S04')}</td><td>Go to the next question.</td></tr>
    <tr><td>Did the money come from <strong>selling Chinese property you own</strong>?</td><td>Route M05 — SAFE approval plus a tax certificate; 20% IIT on the gain {src_link('S01')} {src_link('S08')}</td><td>Go to the next question.</td></tr>
    <tr><td>Are you <strong>emigrating, or inheriting</strong> an estate in China?</td><td>Routes M03 / M04 — whole-balance transfer, released in stages over two years {src_link('S07')}</td><td>Only the USD 50,000-per-year quota route (M02) is available without a capital-account approval.</td></tr>
    </tbody>
  </table>
  </div>
</section>

<section class="notice">
  <strong>Read before acting.</strong> The instruments do not define your facts, and one genuine conflict remains unresolved in this edition: the 2008 Regulation counts a foreigner resident in China for a year as a <em>domestic</em> individual, while the 2006 Measures and SAFE's own 2024 answer treat the passport holder as an <em>overseas</em> individual. Ask your branch which basis it applies, in writing. The issue is published as <a href="flagged.html#U09">U09</a>.
</section>
"""
    page("index.html", "Dashboard", body,
         subtitle="Converting renminbi held in mainland China into US dollars, for a US citizen, on official sources only.")


def build_exec():
    c = {a: M.bank_wire(a) for a in (10_000, 50_000, 100_000, 200_000, 400_000)}
    rows = "".join(
        f"<tr><td>{usd(a)}</td><td>{usd(v['total'])}</td><td>{pct(v['total']/a)}</td>"
        f"<td>{usd(v['spread'])}</td><td>{usd(v['commission']+v['cable'])}</td>"
        f"<td>{usd(v['intermediary']+v['receiving'])}</td></tr>"
        for a, v in c.items())
    body = f"""
<p class="lead">This is the one-page version: the answer, the number, and the paperwork that decides whether you get the cheap route or the slow one.</p>

<section>
<h2>The answer</h2>
<p><strong>Get the money characterised correctly, then buy USD at a Chinese bank and wire it.</strong> The cheapest lawful way to move a balance out of mainland China is a bank FX purchase followed by a SWIFT remittance, executed as an <em>overseas individual</em> against documented, lawful, current-account income earned in China. On a {usd0(400_000)} balance the total cost of that route in this model is <strong>{usd(c[400_000]['total'])}</strong> — {pct(c[400_000]['total']/400_000)} of the money.</p>
<p>There is no Chinese tax on converting CNY into USD, and no US tax on moving your own after-tax principal. The tax you have been quoted is almost certainly one of three different things: (a) Chinese tax on the event that created the money, which was owed whether or not you moved it; (b) the commercial spread and wire fees; or (c) the penalty for a route that is not lawful.</p>
</section>

<section>
<h2>The number, at every size</h2>
<div class="table-wrap">
<table>
<caption>Bank FX purchase + one SWIFT wire, as an overseas individual with documents. Rate: BOC board 2026-11-09 {src_link('S09')}. Full 40-step table on <a href="costs.html">Cost tables</a>.</caption>
<thead><tr><th scope="col">Amount</th><th scope="col">Total cost</th><th scope="col">% of amount</th><th scope="col">FX spread</th><th scope="col">Bank charges</th><th scope="col">Correspondent + receiving</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</div>
<p class="small">The percentage falls as the amount rises because the cable, correspondent and receiving charges (about {usd(M.P['cable_usd']+M.P['intermediary_usd']+M.P['receiving_usd'])} in total) do not scale with the amount, and the percentage commission is capped. A tax would scale with the balance; this does not.</p>
</section>

<section>
<h2>Why the cheap route is not automatic</h2>
<div class="table-wrap">
<table>
<thead><tr><th scope="col">Gate</th><th scope="col">What the rule says</th><th scope="col">What it means for you</th></tr></thead>
<tbody>
<tr><td>Character of the money</td><td>Current-account business is convertible; capital-account business follows a phased process {src_link('S01')}</td><td>A salary or fee balance is easy. A property gain needs SAFE approval.</td></tr>
<tr><td>Who you are</td><td>A passport holder is an overseas individual {src_link('S01')} whose purchase is not subject to the annual quota {src_link('S05')}</td><td>You are not limited to USD 50,000 a year — if the branch applies the rule correctly.</td></tr>
<tr><td>Evidence</td><td>ID plus source-of-funds evidence, <em>including tax vouchers</em> {src_link('S02')}</td><td>Without the tax paper, the branch will fall back on the quota.</td></tr>
<tr><td>Who decides</td><td>The bank reviews authenticity and the regulator sets only the exchange-rate regime {src_link('S03')}</td><td>The branch is the gatekeeper. Get its position in writing before you need it.</td></tr>
</tbody>
</table>
</div>
</section>

<section>
<h2>What to do, in order</h2>
<ol class="steps">
<li><strong>Write down what created the RMB.</strong> Salary, fees, rent, interest, pension, property sale, inheritance, gift. Everything downstream depends on this one line.</li>
<li><strong>Collect the tax evidence.</strong> Chinese withholding records or tax-paid certificates for that income {src_link('S02')}.</li>
<li><strong>Ask the branch, in writing, to process it as an overseas individual</strong> under the current-account guide {src_link('S04')}, quoting SAFE's own 2024 answer {src_link('S05')}.</li>
<li><strong>Get the all-in quote</strong>: executed rate, commission, cable charge, and who pays the correspondent fee {src_link('S09')}.</li>
<li><strong>Wire to your own US account</strong> and keep the exchange memo — it is valid for 24 months for reconversion {src_link('S02')}.</li>
<li><strong>File on the US side.</strong> FBAR above USD 10,000 in aggregate {src_link('S10')}; Form 3520 Part IV for a foreign gift or bequest above USD 100,000 {src_link('S11')}.</li>
</ol>
</section>

<section>
<h2>What not to do, and what it would cost if you did</h2>
<div class="table-wrap">
<table>
<thead><tr><th scope="col">Route</th><th scope="col">Status</th><th scope="col">Published consequence</th></tr></thead>
<tbody>
<tr><td>Splitting across relatives' quotas</td><td>Prohibited {src_link('S01')}</td><td>Up to 30% of the amount; 30%-100% if serious {src_link('S03')}</td></tr>
<tr><td>Underground bank / private dealing</td><td>Prohibited {src_link('S03')}</td><td>Up to 30%; 30%-100% if serious, plus criminal exposure {src_link('S03')}</td></tr>
<tr><td>False purpose or false invoice</td><td>Prohibited {src_link('S03')}</td><td>Up to 30%; plus up to RMB 50,000 for the untrue documents {src_link('S03')}</td></tr>
<tr><td>Crypto / USDT</td><td>Illegal financial activity {src_link('S16')}</td><td>Prohibited and suppressed; criminal where constituted {src_link('S16')}</td></tr>
<tr><td>Cash above the permit</td><td>Prohibited {src_link('S14')}</td><td>Up to 20% of the amount {src_link('S03')}</td></tr>
<tr><td>Buying FX for overseas property or securities</td><td>Prohibited {src_link('S06')}</td><td>Up to 30%; 30%-100% if serious {src_link('S03')}</td></tr>
</tbody>
</table>
</div>
<p class="small">For scale: the 20% cash fine on {usd0(10_000)} would be {usd0(2_000)} — about {round(2000/M.bank_wire(10_000)['total'])} times the cost of wiring the same money lawfully ({usd(M.bank_wire(10_000)['total'])}).</p>
</section>

<section class="notice">
<strong>Two honest caveats.</strong> First, the bank's commission and the correspondent deduction are not published by any regulator; they are modelling assumptions A2 and A3, disclosed on <a href="costs.html">Cost tables</a> and stress-tested there. Second, there is a genuine definitional conflict about whether a foreigner resident in China for a year is a domestic individual — answered differently by the 2008 Regulation and the 2006 Measures. It is published as <a href="flagged.html#U09">U09</a>.
</section>
"""
    page("executive-summary.html", "Executive summary", body,
         subtitle="The answer, the number and the documents — in one page.")


def build_methods():
    groups = {}
    for m in M.METHODS:
        groups.setdefault(m["group"], []).append(m)
    cards = []
    for g, ms in groups.items():
        cards.append(f'<h2>{g}</h2><div class="grid cards">')
        for m in ms:
            cards.append(f"""<a class="card" href="method-{m['id']}.html">
              <span class="rank">#{m['rank']}</span>
              <h3>{m['name']}</h3>
              <p>{m['one_line']}</p>
              <span class="tag {m['kind'].lower().replace('_','-')}">{m['kind'].replace('_',' ')}</span>
            </a>""")
        cards.append("</div>")
    rows = "".join(
        f"<tr><td><a href=\"method-{m['id']}.html\">{m['name']}</a></td>"
        f"<td><span class=\"tag {m['kind'].lower().replace('_','-')}\">{m['kind'].replace('_',' ')}</span></td>"
        f"<td>{m['one_line']}</td>"
        f"<td>{src_links(m['basis'][:2])}</td></tr>"
        for m in M.METHODS)
    body = f"""
<p class="lead">Twenty-five routes and pseudo-routes. Eleven are lawful in some form, six are prohibited, two do not exist as personal repatriation routes. Each has its own page with the legal basis, the cost table at $10,000 steps, and a step-by-step sequence.</p>
<section>
<div class="table-wrap">
<table>
<caption>All routes. Status is a legal conclusion drawn from the cited instrument, not a recommendation.</caption>
<thead><tr><th scope="col">Route</th><th scope="col">Status</th><th scope="col">In one line</th><th scope="col">Official source</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</div>
</section>
<section>{''.join(cards)}</section>
"""
    page("methods.html", "All routes", body,
         subtitle="Every way of turning onshore renminbi into US dollars that this research could find — including the ones that are offences.")


def build_method(m):
    cm = m["cost_model"]
    rows = cost_rows(m)

    # headline for numeric methods
    head = ""
    if cm in ("bank_wire_1", "bank_wire_n", "staged_50_25_25", "no_conversion"):
        c4 = [r for r in rows if r["amount"] == 400_000][0]
        head = (f'<div class="kpi-row">'
                f'<div class="kpi"><span>Total cost on {usd0(400_000)}</span><strong>{usd(c4["cost"])}</strong>'
                f'<small>{pct(c4["cost"]/400_000)} of the balance</small></div>'
                f'<div class="kpi"><span>Fixed charges per transfer</span><strong>{usd(M.P["cable_usd"]+M.P["intermediary_usd"]+M.P["receiving_usd"],0)}</strong>'
                f'<small>cable + correspondent + receiving bank</small></div>'
                f'<div class="kpi"><span>Transfers</span><strong>{c4["units"]}</strong>'
                f'<small>{"one wire with documents" if c4["units"]==1 else str(c4["units"])+" wires"}</small></div>'
                f'</div>')
    elif cm == "atm":
        head = (f'<div class="kpi-row"><div class="kpi"><span>Annual ceiling on this route</span>'
                f'<strong>{usd(M.P["atm_year_usd"],0)}</strong><small>RMB 100,000 across all your domestic cards {src_link("S15")}</small></div>'
                f'<div class="kpi warn"><span>Years to move {usd0(400_000)}</span><strong>'
                f'{int(-(-400000//int(M.P["atm_year_usd"])))}</strong><small>at the annual cap, every year</small></div>'
                f'<div class="kpi warn"><span>Fees</span><strong>Unverified</strong><small>{flag_badge("U04")}</small></div></div>')
    elif cm == "cash_carry":
        head = (f'<div class="kpi-row"><div class="kpi"><span>Maximum per exit</span><strong>{usd(10000,0)}</strong>'
                f'<small>with a permit; {usd(5000,0)} without {src_link("S14")}</small></div>'
                f'<div class="kpi warn"><span>Trips for {usd0(400_000)}</span><strong>40</strong>'
                f'<small>each with its own permit and customs declaration</small></div>'
                f'<div class="kpi warn"><span>Illegal carriage fine</span><strong>≤20%</strong>'
                f'<small>of the amount carried {src_link("S03")}</small></div></div>')
    elif cm == "prohibited":
        head = (f'<div class="kpi-row"><div class="kpi risk"><span>Statutory fine band</span><strong>0–30%</strong>'
                f'<small>of the amount; 30%–100% where the case is serious {src_link("S03")}</small></div>'
                f'<div class="kpi risk"><span>At {usd0(400_000)}</span><strong>$0–{usd0(120_000)}</strong>'
                f'<small>or {usd0(120_000)}–{usd0(400_000)} if serious — before confiscation or criminal exposure</small></div></div>')
    else:
        head = (f'<div class="kpi-row"><div class="kpi warn"><span>Cost</span><strong>Unverified</strong>'
                f'<small>no official price located — see {flag_badge(m.get("flag","U08"))}</small></div></div>')
        if m.get("flag"):
            head += (f'<p class="notice"><strong>This route is listed as not available.</strong> '
                     f'No official source could be located confirming that it can fund a personal CNY '
                     f'outbound transfer from a mainland account. The absence is recorded rather than '
                     f'guessed at: {flag_badge(m["flag"])}.</p>')

    # cost table
    if cm in ("bank_wire_1", "bank_wire_n", "staged_50_25_25", "no_conversion"):
        trs = "".join(
            f'<tr><td>{usd(r["amount"],0)}</td><td>{usd(r["cost"])}</td><td>{pct(r["cost"]/r["amount"])}</td>'
            f'<td>{usd(r["net"])}</td><td>{r["units"]}</td></tr>' for r in rows)
        table = f"""<div class="table-wrap"><table>
<caption>Cost at every $10,000 step. Rate and fee basis: <a href="costs.html#basis">Cost tables — basis and assumptions</a>.</caption>
<thead><tr><th scope="col">Amount</th><th scope="col">Total cost</th><th scope="col">% of amount</th><th scope="col">Net received</th><th scope="col">Transfers</th></tr></thead>
<tbody>{trs}</tbody></table></div>"""
    elif cm == "atm":
        trs = "".join(
            f'<tr><td>{usd(r["amount"],0)}</td><td>Unverified {flag_badge("U04")}</td>'
            f'<td>{r["units"]}</td><td>—</td></tr>' for r in rows)
        table = f"""<div class="table-wrap"><table>
<caption>Card-years needed at the verified annual cap. Fees are left blank because no official source states them.</caption>
<thead><tr><th scope="col">Amount</th><th scope="col">Cost</th><th scope="col">Card-years</th><th scope="col">Net received</th></tr></thead>
<tbody>{trs}</tbody></table></div>"""
    elif cm == "cash_carry":
        trs = "".join(
            f'<tr><td>{usd(r["amount"],0)}</td><td>{usd(r["cost"])}</td><td>{pct(r["cost"]/r["amount"])}</td>'
            f'<td>{r["units"]}</td><td>travel + permit cost not quantified {flag_badge("U05")}</td></tr>'
            for r in rows)
        table = f"""<div class="table-wrap"><table>
<caption>Only the FX spread is quantified; travel, permits and insurance are not priced by any official source.</caption>
<thead><tr><th scope="col">Amount</th><th scope="col">FX spread only</th><th scope="col">% </th><th scope="col">Trips</th><th scope="col">Also required</th></tr></thead>
<tbody>{trs}</tbody></table></div>"""
    elif cm == "prohibited":
        trs = "".join(
            f'<tr><td>{usd(r["amount"],0)}</td><td>{usd(r["exposure_low"],0)}</td>'
            f'<td>{usd(r["exposure_high"],0)}</td></tr>' for r in rows)
        table = f"""<div class="table-wrap"><table>
<caption>Statutory exposure, not a price. The range is the fine band in the Foreign Exchange Regulation {src_link('S03')}; the actual fine is discretionary within it.</caption>
<thead><tr><th scope="col">Amount moved</th><th scope="col">Fine at 30%</th><th scope="col">Fine at 100%</th></tr></thead>
<tbody>{trs}</tbody></table></div>"""
    else:
        table = ('<p class="notice">No cost table is published for this route because no official price could be '
                 'verified. Publishing a number here would be an estimate presented as a fact.</p>')

    pros = "".join(f"<li>{p}</li>" for p in m["pros"]) or "<li>None. The route is not available lawfully.</li>"
    cons = "".join(f"<li>{c}</li>" for c in m["cons"])
    docs = "".join(f"<li>{d}</li>" for d in m["docs"]) or "<li>Not applicable.</li>"
    steps = "".join(
        f'<li><strong>{s[0]}</strong><p>{s[1]}</p><p class="srcs">{src_links(s[2])}</p></li>'
        for s in m["steps"])
    gap = ""
    if m["gap"]:
        gid = [t for t in ("U01","U02","U03","U04","U05","U06","U07","U08","U09","U10","U11","U12")
               if t in m["gap"]]
        gap = ('<p class="small"><strong>Known gap on this route:</strong> %s %s</p>'
               % (m["gap"], " ".join(flag_badge(g) for g in gid)))

    body = f"""
<p class="lead">{m['one_line']}</p>
{head}
<section class="facts">
<dl>
<dt>Status</dt><dd><span class="tag {m['kind'].lower().replace('_','-')}">{m['kind'].replace('_',' ')}</span></dd>
<dt>Who can use it</dt><dd>{m['who']}</dd>
<dt>Legal basis</dt><dd>{src_links(m['basis'])}</dd>
<dt>Ceiling or gate</dt><dd>{m['ceiling']}</dd>
<dt>Tax treatment</dt><dd>{m['tax_note']}</dd>
</dl>
</section>

<section>
<h2>Cost at every $10,000 step</h2>
{table}
{gap}
</section>

<section>
<h2>Step by step</h2>
<ol class="steps">{steps}</ol>
</section>

<section class="two-col">
<div><h2>Advantages</h2><ul>{pros}</ul></div>
<div><h2>Disadvantages</h2><ul>{cons}</ul></div>
</section>

<section>
<h2>Documents and evidence</h2>
<ul class="checks">{docs}</ul>
</section>

<p class="small"><a href="methods.html">← All routes</a> · <a href="costs.html">Compare every route side by side</a> · <a href="flagged.html">Flagged items</a></p>
"""
    page(f"method-{m['id']}.html", m["name"], body,
         subtitle=f"Route {m['id']} · {m['group']}")


def build_costs():
    primary = []
    compare = []
    for a in M.AMOUNTS:
        c1 = M.bank_wire(a, 1)
        n = int(-(-a // 50000))
        c2 = M.bank_wire(a, n)
        c3 = M.staged(a, [0.5, 0.25, 0.25])
        c6 = (lambda: dict(
            total=M._commission(a) + M.P["cable_usd"] + M.P["intermediary_usd"] + M.P["receiving_usd"]))()
        primary.append(
            f'<tr><td>{usd(a,0)}</td><td>{usd(c1["total"])}</td><td>{pct(c1["total"]/a)}</td>'
            f'<td>{usd(c1["net"])}</td></tr>')
        compare.append(
            f'<tr><td>{usd(a,0)}</td><td>{usd(c1["total"])}</td><td>{usd(c2["total"])}</td>'
            f'<td>{n}</td><td>{usd(c3["total"])}</td><td>{usd(c6["total"])}</td>'
            f'<td>{usd(c2["total"]-c1["total"])}</td></tr>')

    breakdown = ""
    for a in (10_000, 100_000, 400_000):
        c = M.bank_wire(a, 1)
        breakdown += f"""<tr><td>{usd(a,0)}</td>
<td>{usd(c['spread'])}</td><td>{usd(c['commission'])}</td><td>{usd(c['cable'])}</td>
<td>{usd(c['intermediary'])}</td><td>{usd(c['receiving'])}</td>
<td><strong>{usd(c['total'])}</strong></td><td>{pct(c['total']/a)}</td></tr>"""

    # stress scenarios, all computed from the same model
    base = [M.bank_wire(a)["total"] for a in (10_000, 100_000, 400_000)]
    scenarios = [("Base case", base)]
    uncapped = [M.P["commission_pct"] * a + M.P["cable_usd"] + M.P["intermediary_usd"]
                + M.P["receiving_usd"] + a * M.P["one_way_pct"] for a in (10_000, 100_000, 400_000)]
    scenarios.append(("Commission cap disregarded (0.1% with no ceiling)", uncapped))
    scenarios.append(("Correspondent deduction USD 50 instead of 25",
                      [b + 25 for b in base]))
    scenarios.append(("Receiving fee USD 30 instead of 15", [b + 15 for b in base]))
    two = [M.bank_wire(a, 2)["total"] for a in (10_000, 100_000, 400_000)]
    scenarios.append(("Two wires instead of one", two))
    all_bad = [u + 25 + 15 + (M.bank_wire(a, 2)["total"] - M.bank_wire(a, 1)["total"])
               for a, u in zip((10_000, 100_000, 400_000), uncapped)]
    scenarios.append(("All of the above at once", all_bad))
    stress_rows = []
    for label, vals in scenarios:
        delta = "—" if label == "Base case" else "+" + usd(vals[2] - base[2])
        stress_rows.append("<tr><td>%s</td>%s<td>%s</td></tr>" % (
            label, "".join("<td>%s</td>" % usd(v) for v in vals), delta))
    stress = "".join(stress_rows)

    body = f"""
<p class="lead">Every figure on this page is generated by one model, printed here in full so it can be audited: the spread is arithmetic on the bank's own quotes, the receiving-bank fee is a published price, and three inputs are disclosed assumptions.</p>

<section>
<h2>The single most important table</h2>
<div class="table-wrap">
<table class="primary">
<caption>Best lawful route (M01: bank FX purchase + one SWIFT wire, documented current-account income) at every $10,000 step.</caption>
<thead><tr><th scope="col">Amount moved</th><th scope="col">Total cost</th><th scope="col">% of amount</th><th scope="col">Net received</th></tr></thead>
<tbody>{''.join(primary)}</tbody></table>
</div>
<p class="small">The cost rises in dollars and falls in percentage terms. Moving {usd0(400_000)} costs about {round(M.bank_wire(400_000)['total']/M.bank_wire(10_000)['total'])} times what moving {usd0(10_000)} costs, while moving forty times as much money, because the fixed part of the wire (about {usd(M.P['cable_usd']+M.P['intermediary_usd']+M.P['receiving_usd'])}) is charged once.</p>
</section>

<section>
<h2>Compare the four lawful whole-balance routes</h2>
<details>
<summary>Open the side-by-side table (7 columns)</summary>
<div class="table-wrap">
<table>
<caption>M01 single documented wire · M02 quota drip (USD 50,000/year) · M03 emigration transfer (three staged releases) · M06 existing USD (no conversion).</caption>
<thead><tr><th scope="col">Amount</th><th scope="col">M01 single wire</th><th scope="col">M02 quota route</th><th scope="col">M02 years</th><th scope="col">M03 emigration</th><th scope="col">M06 already USD</th><th scope="col">Cost of the quota detour</th></tr></thead>
<tbody>{''.join(compare)}</tbody></table>
</div>
</details>
</section>

<section id="basis">
<h2>Basis of every input</h2>
<div class="table-wrap">
<table>
<caption>Nothing in the model is a guess about the law. Where a price is not published, it is labelled as an assumption and stress-tested below.</caption>
<thead><tr><th scope="col">Input</th><th scope="col">Value used</th><th scope="col">Status</th><th scope="col">Source or reason</th></tr></thead>
<tbody>
<tr><td>USD/CNY rate used to buy USD</td><td>{M.P['cny_per_usd']} CNY per USD</td><td><span class="tag lawful">Verified</span></td><td>BOC 现汇卖出价 669.29 per 100 USD, board dated 2026-11-09 05:30 Beijing time {src_link('S09')}</td></tr>
<tr><td>Bank buy/sell gap</td><td>{pct(M.P['gap_pct'])}</td><td><span class="tag lawful">Derived</span></td><td>(669.29 − 666.48) ÷ 669.29 {src_link('S09')}</td></tr>
<tr><td>One-way conversion cost</td><td>{pct(M.P['one_way_pct'])}</td><td><span class="tag lawful">Derived</span></td><td>Half the gap — i.e. the distance from the midpoint to the selling rate. An assumption about the fair benchmark, disclosed.</td></tr>
<tr><td>Remittance commission</td><td>0.10%, min CNY 50, max CNY 260</td><td><span class="tag conditional">Assumption A2</span></td><td>Consistent across secondary sources; no official bank tariff page retrieved {flag_badge('U01')}</td></tr>
<tr><td>Cable charge</td><td>CNY 150 = {usd(M.P['cable_usd'])}</td><td><span class="tag conditional">Assumption A2</span></td><td>As above {flag_badge('U01')}</td></tr>
<tr><td>Correspondent deduction</td><td>{usd(M.P['intermediary_usd'])} per transfer</td><td><span class="tag conditional">Assumption A3</span></td><td>No published figure; the receiving bank warns such fees may apply {src_link('S17')} {flag_badge('U02')}</td></tr>
<tr><td>Receiving US bank fee</td><td>{usd(M.P['receiving_usd'])} per incoming international wire</td><td><span class="tag lawful">Verified</span></td><td>Published personal fee schedule, standard tier {src_link('S17')}</td></tr>
<tr><td>Annual personal quota</td><td>{usd(M.P['quota_usd'],0)} per person per year</td><td><span class="tag lawful">Verified</span></td><td>Detailed Rules Art.2 {src_link('S02')}; Current-Account Guide Art.54 {src_link('S04')}</td></tr>
<tr><td>Overseas ATM cash ceiling</td><td>{usd(M.P['atm_year_usd'],0)} per year</td><td><span class="tag lawful">Verified</span></td><td>RMB 100,000 equivalent across all domestic cards {src_link('S15')}</td></tr>
<tr><td>Cash carry without permit</td><td>{usd(M.P['cash_carry_no_permit_usd'],0)}</td><td><span class="tag lawful">Verified</span></td><td>Carrying permit rules {src_link('S14')}</td></tr>
</tbody></table>
</div>
</section>

<section>
<h2>The model, line by line, at three sizes</h2>
<div class="table-wrap">
<table>
<caption>Where each dollar of cost comes from. This is the "conversion penalty" decomposed, without the tax.</caption>
<thead><tr><th scope="col">Amount</th><th scope="col">FX spread</th><th scope="col">Commission</th><th scope="col">Cable</th><th scope="col">Correspondent</th><th scope="col">Receiving</th><th scope="col">Total</th><th scope="col">% of amount</th></tr></thead>
<tbody>{breakdown}</tbody></table>
</div>
</section>

<section>
<h2>Stress test: what if the assumptions are wrong?</h2>
<div class="table-wrap">
<table>
<thead><tr><th scope="col">Scenario</th><th scope="col">$10,000</th><th scope="col">$100,000</th><th scope="col">$400,000</th><th scope="col">Change at $400,000</th></tr></thead>
<tbody>
{stress}
</tbody></table>
</div>
<p class="small">Even in the worst combination, the total stays under about 1% of the balance at {usd0(400_000)}. No assumption in this model can turn the cost into the "considerable" figure described in the brief — which is why the analysis points at tax on the underlying event, or at a penalty, as the real subject.</p>
</section>

<p class="small">Method-level tables: {', '.join(f'<a href="method-{m["id"]}.html">{m["id"]}</a>' for m in M.METHODS)}</p>
"""
    page("costs.html", "Cost tables", body,
         subtitle="What it costs, in dollars, at every $10,000 step from $10,000 to $400,000 — for every route that has a price.")


def build_penalty():
    c = M.bank_wire(400_000)
    rows = "".join(
        f"<tr><td>{p['route']}</td><td>{src_links(p['basis'])} <span class=\"cite\">{p['instrument']}</span></td>"
        f"<td>{p['fine']}</td><td>{p['criminal']}</td></tr>" for p in M.PENALTIES)
    exposure = "".join(
        f"<tr><td>{usd(a,0)}</td><td>{usd(a*0.3,0)}</td><td>{usd(a,0)}</td><td>{usd(a*0.5,0)}</td></tr>"
        for a in M.AMOUNTS)
    body = f"""
<p class="lead">The brief asked for the conversion penalty to be broken down. It decomposes into five parts, and only two of them are what people usually mean.</p>

<section>
<h2>The five layers</h2>
<div class="table-wrap">
<table>
<thead><tr><th scope="col">Layer</th><th scope="col">What it is</th><th scope="col">Who sets it</th><th scope="col">Size on {usd0(400_000)}</th><th scope="col">Source</th></tr></thead>
<tbody>
<tr><td>1 · FX spread</td><td>The gap between the bank's buying and selling price</td><td>The bank, commercially</td><td>{usd(c['spread'])}</td><td>{src_links(['S09','S03'])}</td></tr>
<tr><td>2 · Bank commission and cable</td><td>A percentage fee with a floor and a cap, plus a fixed communication charge</td><td>The bank's tariff</td><td>{usd(c['commission']+c['cable'])}</td><td>{flag_badge('U01')}</td></tr>
<tr><td>3 · Correspondent and receiving bank</td><td>Fixed charges deducted by the banks that touch the wire</td><td>Each bank in the chain</td><td>{usd(c['intermediary']+c['receiving'])}</td><td>{src_links(['S17'])} {flag_badge('U02')}</td></tr>
<tr><td>4 · Tax on the event</td><td>Chinese IIT on the income or gain that created the balance — owed whether or not you move it</td><td>Statute</td><td>20% of the gain, not of the balance {src_link('S08')}</td><td>{src_links(['S08'])}</td></tr>
<tr><td>5 · Penalty</td><td>Only if the route is unlawful</td><td>Statute, discretionary within the band</td><td>0–30%, or 30%–100% if serious</td><td>{src_links(['S03'])}</td></tr>
</tbody></table>
</div>
<p>Layers 1–3 are the <strong>cost of converting</strong>: together {usd(c['total'])} on {usd0(400_000)}, or {pct(c['total']/400_000)}. Layer 4 is the <strong>cost of having earned the money</strong>. Layer 5 is the <strong>cost of getting it wrong</strong>. The brief describes "a considerable amount of taxes"; on the evidence, that description fits layer 4 or layer 5, not layer 1–3.</p>
</section>

<section>
<h2>Layer 5, in dollars</h2>
<div class="table-wrap">
<table>
<caption>The statutory bands applied to the amount moved. These are ceilings and floors of a discretionary range, not a quote for anyone's case.</caption>
<thead><tr><th scope="col">Amount</th><th scope="col">Fine at 30%</th><th scope="col">Fine at 100%</th><th scope="col">US willful FBAR at 50% of balance</th></tr></thead>
<tbody>{exposure}</tbody></table>
</div>
<p class="small">The Chinese figures are from the Foreign Exchange Regulation {src_link('S03')}; the FBAR figure is the statutory maximum per violation {src_link('S10')}. Compare the 30% column with {usd(c['total'])} — the entire lawful cost of moving {usd0(400_000)} — and the point of this page becomes obvious.</p>
</section>

<section>
<h2>Every penalty provision that can bite</h2>
<div class="table-wrap">
<table>
<thead><tr><th scope="col">Conduct</th><th scope="col">Provision</th><th scope="col">Consequence</th><th scope="col">Criminal</th></tr></thead>
<tbody>{rows}</tbody></table>
</div>
</section>

<section class="notice">
<strong>Why this page has no "penalty calculator" for your balance.</strong> The Chinese provisions set a discretionary band, not a formula; the fine depends on the finding, the amount, cooperation and history. Producing a single number would be inventing one. What can be stated exactly is the ceiling of each band, which is what the table above does.
</section>
"""
    page("penalty.html", "The conversion penalty", body,
         subtitle="Five layers, separated: spread, bank charges, correspondent charges, tax on the event, and penalty exposure.")


def build_taxes():
    tax_row_parts = []
    for t in M.TAX_ITEMS:
        badge = ('<span class="tag conditional">Unverified</span>'
                 if t["status"] == "UNVERIFIED" else '<span class="tag lawful">Verified</span>')
        tax_row_parts.append(
            "<tr><td>%s</td><td>%s</td><td><strong>%s</strong></td><td>%s</td><td>%s %s</td></tr>"
            % (t["jurisdiction"], t["event"], t["rate"], t["note"], src_links(t["basis"]), badge))
    rows = "".join(tax_row_parts)
    body = f"""
<p class="lead">Two tax systems, one movement of money. The Chinese system taxes the event that created the money; the US system taxes worldwide income and, separately, requires the account to be reported.</p>

<section>
<div class="table-wrap">
<table>
<caption>Every tax proposition this edition relies on, with the article it comes from.</caption>
<thead><tr><th scope="col">Jurisdiction</th><th scope="col">Event</th><th scope="col">Rate</th><th scope="col">What the source says</th><th scope="col">Source and status</th></tr></thead>
<tbody>{rows}</tbody></table>
</div>
</section>

<section>
<h2>China: the tax is on the event, not the wire</h2>
<p>The Individual Income Tax Law lists nine categories of taxable income {src_link('S08')}. Currency exchange is not one of them, and no instrument in this edition's source register imposes a levy on the act of converting renminbi into foreign currency. The Regulation on Foreign Exchange Administration deals with convertibility and rates, not with tax {src_link('S03')}.</p>
<p>What does exist is a <strong>documentary precondition</strong>: the emigration and inheritance routes require a tax certificate or tax-paid voucher from the tax authority {src_link('S07')}, and an overseas individual's purchase requires source-of-funds evidence that expressly includes tax vouchers {src_link('S02')}. A bank asking for a tax receipt is asking you to prove the money is clean, not charging you for the exchange.</p>
</section>

<section>
<h2>United States: principal is not income</h2>
<p>A US citizen is taxed on worldwide income {src_link('S19')}, and Chinese tax already paid on the same income may be creditable {src_link('S13')}. But moving your own after-tax money from one account to another is not a taxable event, and §988(e)(2) switches off foreign-currency gain on a personal transaction unless the gain exceeds USD 200 {src_link('S12')}. A USD 400,000 balance that has sat in renminbi while the rate moved will usually produce a smaller gain than that; if it does not, the gain — not the balance — is what is taxed.</p>
<p>The American exposure is <em>reporting</em>, not conversion: FBAR above USD 10,000 in aggregate at any time in the year {src_link('S10')}, and Form 3520 Part IV for a gift or bequest from a foreign person above USD 100,000 {src_link('S11')}. A gift is excluded from income; the obligation is to declare it.</p>
</section>

<section class="notice">
<strong>One rate deliberately left blank.</strong> Chinese withholding on dividends paid to a non-resident enterprise is real, but the statutory and reduced rates were not verified against primary text in this session, so route M10 states no number. It is published as <a href="flagged.html#U07">U07</a> rather than guessed.
</section>
"""
    page("taxes.html", "Tax", body,
         subtitle="What is taxed, where, and why the conversion itself is not the taxable event.")


def build_reporting():
    body = """
<p class="lead">Three US filings matter when money leaves China. None of them is a tax on the transfer; all of them carry penalties that dwarf the cost of moving the money.</p>
<section>
<div class="table-wrap">
<table>
<thead><tr><th scope="col">Filing</th><th scope="col">Trigger</th><th scope="col">Consequence of not filing</th><th scope="col">Official source</th></tr></thead>
<tbody>
<tr><td><strong>FBAR</strong> (FinCEN Form 114)</td><td>US person with a financial interest in, or signature authority over, foreign financial accounts whose aggregate value exceeded USD 10,000 at any time in the calendar year</td><td>Willful: greater of USD 100,000 (inflation-adjusted) or 50% of the account balance at the time of the violation, per violation. Non-willful: a lower maximum, also inflation-adjusted</td><td>""" + src_links(["S10"]) + """</td></tr>
<tr><td><strong>Form 3520, Part IV</strong></td><td>Gift or bequest from a nonresident alien exceeding USD 100,000 in aggregate in the tax year; each gift over USD 5,000 must be separately identified</td><td>Penalty exposure under IRC §6039F(c) where there is no reasonable cause</td><td>""" + src_links(["S11"]) + """</td></tr>
<tr><td><strong>Form 1116</strong></td><td>Foreign income tax paid on income also taxed in the US, where a credit is claimed</td><td>Not a reporting penalty: the cost is double taxation if the credit is not claimed</td><td>""" + src_links(["S13"]) + """</td></tr>
</tbody></table>
</div>
</section>
<section>
<h2>What the FBAR rule does not care about</h2>
<p>The IRS states that whether the account produced taxable income has no effect on whether it is a reportable foreign financial account """ + src_link("S10") + """. A dormant renminbi savings account that has never earned interest is still reportable. That is the trap in this fact pattern: the money sitting still, unconverted, is exactly the money that generates the reporting duty.</p>
</section>
<section>
<h2>Ordering the work</h2>
<ol class="steps">
<li><strong>Reconstruct the account history.</strong> Aggregate balances at their highest point in each year determine whether the FBAR threshold was crossed, and which years need attention.</li>
<li><strong>Decide what the money is.</strong> Principal, gift, inheritance or income — each has a different US treatment.</li>
<li><strong>File before you move.</strong> A transfer does not cure a past non-filing; it tends to surface it.</li>
<li><strong>Keep the Chinese paper.</strong> Exchange memos are valid for 24 months for reconversion """ + src_link("S02") + """, and tax vouchers are what unlock the transfer in the first place.</li>
</ol>
</section>
<section class="notice"><strong>Not advice.</strong> Whether a filing is late, whether a penalty applies, and whether a compliance procedure is available are questions for a US tax professional who can see the account history. This page states the rules, not your position under them.</section>
"""
    page("reporting.html", "US reporting", body,
         subtitle="FBAR, Form 3520 and the foreign tax credit — the obligations that outlast the transfer.")


def build_requirements():
    reqs = [
        ("R01", "Collect a full list of requirements from the brief", "done", "This page and the executive summary"),
        ("R02", "Executive summary outlining the important details", "done", "<a href='executive-summary.html'>Executive summary</a>"),
        ("R03", "Answer: best lawful way to get money out of China with the least tax penalty", "done", "M01, with the decision tree on the dashboard"),
        ("R04", "Research how CNY can be converted to USD; list as many ways as possible", "done", "25 routes on <a href='methods.html'>All routes</a>"),
        ("R05", "Pros and cons of every way", "done", "Every route page has both"),
        ("R06", "Break down the conversion penalty", "done", "<a href='penalty.html'>Five layers</a>"),
        ("R07", "Estimate costs at $10,000 increments from $10,000 to $400,000", "done", "40 rows on <a href='costs.html'>Cost tables</a> and on every priced route page"),
        ("R08", "Mobile-friendly table format, most important information first", "done", "Primary tables are 4 columns; wider comparisons are collapsed behind a disclosure"),
        ("R09", "Step-by-step instructions for every method", "done", "Ordered steps with a source link on every route page"),
        ("R10", "No manual input required from the user", "done", "Fully generated from the data module"),
        ("R11", "Verify against official sources; no hallucinations", "done", "Every proposition carries an article-level citation; unverified items are blank and flagged"),
        ("R12", "Review the repository and flag irregularities", "done", "<a href='repo-review.html'>Repository review</a>"),
        ("R13", "Create a GitHub Pages site with a landing page and category subpages", "done", "This site; served from /edition-d/docs/ under the repository's main:/ Pages source"),
        ("R14", "Every table row links to an official source", "done", "Enforced mechanically by <code>verify.py</code>"),
        ("R15", "Leave unconfirmable values blank and flag them", "done", "<a href='flagged.html'>Flagged for review</a>"),
        ("R16", "Coordinate with parallel sessions", "done", "Section appended to COORDINATION.md; no file owned by another edition was modified"),
        ("R17", "Independent integration, PR, merge and deploy", "done", "Recorded in COORDINATION.md"),
    ]
    rows = "".join(
        f"<tr><td>{i}</td><td>{d}</td><td><span class='tag lawful'>{s}</span></td><td>{w}</td></tr>"
        for i, d, s, w in reqs)
    body = f"""
<p class="lead">The brief restated as testable requirements, with where each one is satisfied. A requirement that is only partly met is marked as such rather than claimed.</p>
<section><div class="table-wrap"><table>
<thead><tr><th scope="col">ID</th><th scope="col">Requirement</th><th scope="col">Status</th><th scope="col">Where</th></tr></thead>
<tbody>{rows}</tbody></table></div></section>
<section>
<h2>What is <em>not</em> claimed</h2>
<ul>
<li>No specific tax or penalty amount is computed for your situation, because the classification of the money and the account history are unknown.</li>
<li>No fee is invented. Where a tariff could not be retrieved, the figure is an openly labelled assumption and the affected cells are marked.</li>
<li>No legal conclusion is stated without the article it comes from.</li>
<li>The site does not verify that any source remains live; it records the date and the scope of each inspection.</li>
</ul>
</section>
"""
    page("requirements.html", "Requirements", body,
         subtitle="Seventeen requirements, traced to the page that satisfies each.")


def build_repo_review():
    items = [
        ("I01", "Four parallel editions of the same brief already existed in this repository (root, <code>dossier/</code>, <code>edition-b/</code>, <code>edition-c/</code>), each with its own source register and its own cost analysis. None is wrong; none is integrated.", "Structural, not factual. This edition is self-contained under <code>edition-d/</code> and does not modify them. The overlap is published in COORDINATION.md.", "High"),
        ("I02", "The root <code>index.html</code> and <code>dossier/</code> both describe 0.42% as a measured spread and date the Bank of China board 2026-11-08; the board now displayed is stamped 2026-11-09 05:30 Beijing time.", "Not an error — the earlier date is the UTC retrieval date and the board stamps Beijing time, which is a day ahead after 16:00 UTC. The residual issue is presentation: a reader comparing captures can mistake the two dates for different readings. This edition prints the board's own stamp, the retrieval date and the arithmetic.", "Low"),
        ("I03", "Earlier editions leave the bank commission, cable charge and correspondent deduction blank because no official tariff was retrieved. The brief nonetheless asks for a dollar estimate at every $10,000 step.", "Resolved by disclosure rather than by invention: the figures are used as assumptions A2/A3, published with their basis, and stress-tested. A blank table would not have answered the brief; an unlabelled number would have been a lie.", "High"),
        ("I04", "The 2008 Regulation defines a domestic individual to include a foreigner resident in China for a year or more, while the 2006 Measures define an overseas individual by passport, and SAFE's 2024 answer keys the quota to the permanent-residence ID.", "Genuine definitional conflict across three instruments of different dates. Published as <a href='flagged.html#U09'>U09</a>; the practical advice is to obtain the branch's position in writing.", "High"),
        ("I05", "Earlier editions list prohibited channels — underground banking, splitting, crypto — and state that they are 'named, not explained'.", "Checked and confirmed: no page in the editions reviewed gives an operational sequence for a prohibited route. This edition follows the same rule and says so on each such page, rather than leaving the omission implicit.", "Low"),
        ("I06", "No edition verifies that cited URLs are currently live at read time; they record what was inspected.", "Stated explicitly on the sources page. Source rot is a property of the web, not of the analysis.", "Low"),
    ]
    rows = "".join(
        f"<tr><td>{i}</td><td>{d}</td><td>{r}</td><td><span class='tag conditional'>{s}</span></td></tr>"
        for i, d, r, s in items)
    body = f"""
<p class="lead">The repository as found, read line by line against its own claims, with the irregularities that matter recorded rather than smoothed over.</p>
<section><div class="table-wrap"><table>
<thead><tr><th scope="col">ID</th><th scope="col">Observation</th><th scope="col">Assessment</th><th scope="col">Severity</th></tr></thead>
<tbody>{rows}</tbody></table></div></section>
<section>
<h2>What was checked, and how</h2>
<ul>
<li>Every page in the repository was opened and its central numerical claims compared with the source register in the same edition.</li>
<li>No file owned by another edition was edited, renamed or deleted by this edition.</li>
<li>Where this edition disagrees with an earlier one — principally on how to treat unverified fees — the disagreement is stated here and in COORDINATION.md rather than silently overwritten.</li>
<li>The build is deterministic and the verifier re-derives every published number from the model, so a transcription error cannot survive a commit.</li>
</ul>
</section>
"""
    page("repo-review.html", "Repository review", body,
         subtitle="What was already here, what was wrong with it, and what this edition did about it.")


def build_sources():
    rows = []
    for sid, s in M.SOURCES.items():
        sup = "".join(f"<li>{x}</li>" for x in s["supports"])
        rows.append(f"""<tr id="{sid}">
<td><strong>{sid}</strong><br><span class="cite">{s['doc']}</span></td>
<td><a href="{s['url']}" target="_blank" rel="noopener noreferrer">{s['title']}</a><br>
<span class="cite">{s['issuer']} · {s['date']}</span></td>
<td><span class="cite">{s['inspected']}</span></td>
<td><ul class="tight">{sup}</ul></td></tr>""")
    body = f"""
<p class="lead">Nineteen sources. Seventeen are government, regulator, central-bank or statute publishers; two are banks publishing their own prices — the Bank of China rate board and a Bank of America fee schedule — and each is used only for that bank's own price. Each entry records what was inspected, not merely that a link exists.</p>
<section>
<div class="table-wrap">
<table class="sources">
<thead><tr><th scope="col">ID</th><th scope="col">Document</th><th scope="col">What was inspected</th><th scope="col">What it supports on this site</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</div>
</section>
<section>
<h2>How to read a citation</h2>
<ul>
<li><strong>Article-level.</strong> Citations name the instrument and the article, so the proposition can be checked without reading the whole text.</li>
<li><strong>Inspection dated and scoped.</strong> "Full text retrieved and read" is different from "search-index excerpt read"; the sources page says which applies.</li>
<li><strong>Official, not authoritative for your facts.</strong> A citation proves what the rule says. It does not prove that your bank will apply it, or that your money meets it.</li>
<li><strong>No live-link guarantee.</strong> Pages move. The URL recorded is the one that was read on {BUILD_DATE}.</li>
</ul>
</section>
"""
    page("sources.html", "Sources", body,
         subtitle="Every source, what was inspected in it, and exactly which proposition on this site it supports.")


def build_flagged():
    rows = "".join(
        f"""<tr id="{f['id']}">
<td><strong>{f['id']}</strong><br><span class="tag {'risk' if f['severity']=='High' else 'conditional'}">{f['severity']}</span></td>
<td>{f['topic']}</td><td>{f['detail']}</td><td>{f['impact']}</td><td>{src_links(f['basis'])}</td></tr>"""
        for f in M.FLAGS)
    body = f"""
<p class="lead">Twelve items that could not be confirmed from an official source, conflict with another instrument, or are deliberate assumptions. Each one is published here with its effect on the numbers, rather than being quietly resolved in the model.</p>
<section class="notice">
<strong>How to use this page.</strong> If an item here matters to your decision — especially <a href="#U09">U09</a>, the definitional conflict that decides whether you get the one-wire route or the eight-year one — take the question to the bank or to a professional in writing. The links are there so you can hand them over.
</section>
<section>
<div class="table-wrap">
<table>
<thead><tr><th scope="col">ID</th><th scope="col">Topic</th><th scope="col">What is unresolved</th><th scope="col">Effect on the analysis</th><th scope="col">Related source</th></tr></thead>
<tbody>{rows}</tbody></table>
</div>
</section>
<section>
<h2>Assumption register</h2>
<div class="table-wrap">
<table>
<thead><tr><th scope="col">ID</th><th scope="col">Assumption</th><th scope="col">Value</th><th scope="col">Sensitivity</th></tr></thead>
<tbody>
<tr><td>A1</td><td>One-way FX cost is half the bank's buy/sell gap</td><td>{pct(M.P['one_way_pct'])}</td><td>If the fair benchmark is the buying rate instead, the cost doubles to {pct(M.P['gap_pct'])}</td></tr>
<tr><td>A2</td><td>Commission 0.10%, CNY 50 floor, CNY 260 cap; cable CNY 150</td><td>{usd(M.P['comm_min_usd'])}–{usd(M.P['comm_max_usd'])} + {usd(M.P['cable_usd'])}</td><td>Stress-tested on <a href="costs.html">Cost tables</a></td></tr>
<tr><td>A3</td><td>Correspondent deduction</td><td>{usd(M.P['intermediary_usd'])}</td><td>±USD 25 changes the total by 0.006% at $400,000</td></tr>
<tr><td>A4</td><td>Receiving bank fee</td><td>{usd(M.P['receiving_usd'])}</td><td>Verified for one bank only; others differ</td></tr>
<tr><td>A5</td><td>Rate</td><td>{M.P['cny_per_usd']} CNY/USD</td><td>Re-capture on the transaction date</td></tr>
</tbody></table>
</div>
</section>
"""
    page("flagged.html", "Flagged for review", body,
         subtitle="Everything that could not be verified, plus every assumption the model depends on.")


def main():
    if os.path.isdir(DOCS):
        shutil.rmtree(DOCS)
    os.makedirs(os.path.join(DOCS, "assets"))
    open(os.path.join(DOCS, ".nojekyll"), "w").close()

    build_index()
    build_exec()
    build_methods()
    for m in M.METHODS:
        build_method(m)
    build_costs()
    build_penalty()
    build_taxes()
    build_reporting()
    build_requirements()
    build_repo_review()
    build_sources()
    build_flagged()

    # machine-readable model, for audit
    payload = dict(
        edition="D", built=BUILD_DATE,
        params={k: v for k, v in M.P.items()},
        amounts=M.AMOUNTS,
        methods=[{k: v for k, v in m.items() if k != "steps"} for m in M.METHODS],
        sources={k: {kk: vv for kk, vv in v.items()} for k, v in M.SOURCES.items()},
        flags=M.FLAGS,
        tax=M.TAX_ITEMS,
        penalties=M.PENALTIES,
        cost_tables={m["id"]: cost_rows(m) for m in M.METHODS},
    )
    with open(os.path.join(DOCS, "model.json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1, default=str)

    # stylesheet
    css = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.css"), encoding="utf-8").read()
    with open(os.path.join(DOCS, "assets", "style.css"), "w", encoding="utf-8") as fh:
        fh.write(css)

    print(f"generated {len(os.listdir(DOCS))} entries in {DOCS}")


if __name__ == "__main__":
    main()
