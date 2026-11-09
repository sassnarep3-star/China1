# -*- coding: utf-8 -*-
"""Edition H — page bodies. Imported by build.py."""

from decimal import Decimal

from sitegen import (esc, money, pct, share, src_links, grade_badge, status_badge, page,
                     CATEGORIES, COMPUTED, BLANK, PROHIB, NEUTRAL, LEAD, METHOD,
                     METHODS, SRC, SOURCES, AS_OF, ladder, compute)
from costs import (AMOUNTS, FX_MARGIN_PCT, FX_ROUND_TRIP_PCT, BUY_SPOT, SELL_SPOT,
                   MID, REFERENCE, q2, q4, usd_to_cny, commission_cny,
                   COMMISSION_MAX_CNY, RECEIVING_BANK_USD, FULL_AMOUNT_USD)
from penalties import LAYER2, LAYER3, LAYER4, REPORTING, STRATEGY

KEY = [10_000, 50_000, 100_000, 200_000, 300_000, 400_000]

LEAD_ROWS = dict(ladder(LEAD))


def lead_at(a):
    return LEAD_ROWS[a]


def total_at(a):
    return LEAD_ROWS[a]["total"]


# ==========================================================================
# 1. Dashboard
# ==========================================================================

def p_index():
    r10, r50, r100, r200, r400 = (lead_at(a) for a in
                                  (10_000, 50_000, 100_000, 200_000, 400_000))
    glance = []
    for a in (10_000, 50_000, 100_000, 200_000, 400_000):
        c = lead_at(a)
        glance.append(
            '<tr><td data-l="Amount"><strong>{a}</strong></td>'
            '<td class="num big" data-l="Total cost">{t}</td>'
            '<td class="num" data-l="Share of amount">{p}</td>'
            '<td class="num" data-l="Net received">{n}</td>'
            '<td data-l="Source">{s}</td></tr>'.format(
                a=money(a, 0), t=money(c["total"]), p=share(c["total"], a),
                n=money(a - c["total"]), s=src_links(["BK-01", "BK-03", "BK-04", "BK-08"])))

    cards = [
        ("answer.html", "01", "The answer", "The least-penalty sequence, in four steps, and why the premise is the expensive part."),
        ("costs.html", "02", "Costs at every $10,000", "USD 10,000 to USD 400,000, 40 rows, for every route that has a published price."),
        ("methods.html", "03", "All {n} routes".format(n=len(METHODS)), "Lawful, conditional, prohibited and the alternatives that avoid converting."),
        ("penalty.html", "04", "The penalty, decomposed", "FX friction, PRC income tax, PRC conduct fines, US filing penalties — separated."),
        ("tax.html", "05", "Tax in both countries", "PRC IIT categories, §988, the $200 rule, the foreign tax credit."),
        ("reporting.html", "06", "US filing", "FBAR, 8938, 3520 and the 1% remittance tax that does not apply here."),
        ("steps.html", "07", "Step by step", "The exact order of operations, and the document each step needs."),
        ("sources.html", "08", "Sources", "{n} pages, graded, with the quoted text and the time retrieved.".format(n=len(SOURCES))),
        ("flagged.html", "09", "Flagged for review", "Every blank, every unverified value, every irregularity in the earlier editions."),
    ]
    nav = "".join(
        '<a class="nav-card" href="{h}"><span class="kicker">{k}</span><h3>{t}</h3><p>{d}</p></a>'.format(
            h=h, k=k, t=esc(t), d=esc(d)) for h, k, t, d in cards)

    body = """
<p class="eyebrow">CNY to USD · US citizen · official sources only</p>
<h1>What it actually costs to get money out of China</h1>
<p class="lede">The premise is the expensive part. Converting your own money is not a taxable event in
either country, and doing it lawfully costs between 0.23% and 0.88% of the amount. What produces the
"considerable tax" people describe is either a PRC tax on the income behind the money, a fine for
using a prohibited channel, or a US filing failure. This site prices the first, separates the other
three, and shows its work for every figure.</p>

<div class="answer">
<h2>The short answer</h2>
<p class="big">Use the documented route that matches the money's real source, settle the PRC tax on the
income first, and fix your US reporting before you move a single dollar.</p>
<p>At <strong>USD 400,000</strong> that is <strong>{c400}</strong> — {p400} of the amount. The same
amount moved through an underground bank carries a statutory exposure of 30% to 100%, which is
between {d120} and {d400}. There is no arrangement in which the prohibited route is cheaper.</p>
<p><a href="answer.html">Read the full answer &rarr;</a></p>
</div>

<div class="stats">
  <div class="stat"><small>FX margin, one conversion</small><strong>{fx}</strong>
    <em>one-way bid/ask on BOC's own board</em></div>
  <div class="stat"><small>All-in at $10,000</small><strong>{c10}</strong>
    <em>{p10} — fixed fees dominate</em></div>
  <div class="stat"><small>All-in at $400,000</small><strong>{c400}</strong>
    <em>{p400} of the amount</em></div>
  <div class="stat"><small>Tax on the conversion itself</small><strong>$0</strong>
    <em>in both jurisdictions</em></div>
</div>

<h2>The headline table</h2>
<p class="note">The documented overseas-individual route, fully costed. Every row is built from the
banks' published tariffs, not from an estimate. On a phone each row appears as a card.</p>
<div class="tw"><table class="stack">
<thead><tr><th>Amount</th><th class="num">Total cost</th><th class="num">Share</th>
<th class="num">Net received</th><th>Source</th></tr></thead>
<tbody>{glance}</tbody></table></div>
<p class="note">Cost = FX margin + BOC commission (0.1%, CNY 50 min, CNY 260 max) + CNY 150 cable +
USD 15 full-amount arrival + USD 15 named US receiving fee + a CNY 20–40 certificate of deposit.
Sources: {glancesrc}. The rate board and the tariff pages are re-checked on every build.</p>

<h2>Where the money actually goes</h2>
<p class="note">Four different things get called "the conversion penalty". Only the first is a cost
of converting.</p>
<div class="tw"><table class="stack">
<thead><tr><th>Layer</th><th>What it is</th><th class="num">Size</th><th>Source</th></tr></thead>
<tbody>
<tr><td data-l="Layer"><strong>1 · Friction</strong></td>
 <td data-l="What">FX margin, commission, cable, correspondent, receiving bank, documents. Published, unavoidable, charged once.</td>
 <td class="num" data-l="Size">0.23%–0.88%</td>
 <td data-l="Source">{s1}</td></tr>
<tr><td data-l="Layer"><strong>2 · PRC income tax</strong></td>
 <td data-l="What">IIT on the income or gain behind the money. Due whether or not you ever move it. The principal is never taxed.</td>
 <td class="num" data-l="Size">20% of the gain</td>
 <td data-l="Source">{s2}</td></tr>
<tr><td data-l="Layer"><strong>3 · PRC conduct fine</strong></td>
 <td data-l="What">The sanction for using a prohibited channel — splitting, underground dealing, crypto, false invoices, illegal cash carriage.</td>
 <td class="num" data-l="Size">20%–100%</td>
 <td data-l="Source">{s3}</td></tr>
<tr><td data-l="Layer"><strong>4 · US filing penalty</strong></td>
 <td data-l="What">FBAR, 8938 and 3520 failures, plus failure-to-file and accuracy additions. Triggered by not filing, not by transferring.</td>
 <td class="num" data-l="Size">20%–50%</td>
 <td data-l="Source">{s4}</td></tr>
</tbody></table></div>

<h2>Every page</h2>
<div class="grid">{nav}</div>
""".format(
        c10=money(total_at(10_000)), p10=share(total_at(10_000), 10_000),
        c400=money(total_at(400_000)), p400=share(total_at(400_000), 400_000),
        fx=pct(FX_MARGIN_PCT, 4),
        d120=money(400_000 * 0.30, 0), d400=money(400_000 * 1.00, 0),
        glance="".join(glance),
        glancesrc=src_links(["BK-01", "BK-02", "BK-03", "BK-04", "BK-08"]),
        s1=src_links(["BK-01", "BK-04", "BK-08"]),
        s2=src_links(["CN-18", "CN-19"]),
        s3=src_links(["CN-04", "CN-05", "CN-06", "CN-20"]),
        s4=src_links(["US-09", "US-10", "US-11"]),
        nav=nav)
    return page("Dashboard", body, "index.html")


# ==========================================================================
# 2. The answer
# ==========================================================================

def p_answer():
    rows = []
    for s in STRATEGY:
        rows.append(
            '<tr><td data-l="Step"><strong>{r}</strong></td>'
            '<td data-l="Do this"><strong>{t}</strong><br><span class="note">{w}</span></td>'
            '<td data-l="Exposure">{e}</td>'
            '<td data-l="Source">{src}</td></tr>'.format(
                r=s["rank"], t=esc(s["title"]), w=esc(s["why"]),
                e=esc(s["penalty_exposure"]), src=src_links(s["sources"])))

    lay2 = "".join(
        '<tr><td data-l="Item">{i}</td><td class="num" data-l="Rate">{r}</td>'
        '<td data-l="Base">{b}</td><td data-l="Finding">{f}</td>'
        '<td data-l="Source">{s}</td></tr>'.format(
            i=esc(x["item"]), r=esc(x["rate"]) if x["rate"] else "—",
            b=esc(x["base"]) if x["base"] else "—",
            f=esc(x["finding"]), s=src_links(x["sources"])) for x in LAYER2)

    body = """
<p class="crumb"><a href="index.html">Dashboard</a> / The answer</p>
<h1>The least-tax-penalty way out</h1>
<p class="lede">Ranked by what actually reduces the penalty, not by what looks cheapest on a fee
page. The first step is free and removes most of the risk.</p>

<div class="ok">
<p><strong>The one-sentence answer.</strong> There is no tax on converting your own CNY into USD in
either country — so the least-penalty strategy is not a clever conversion trick, it is to use the
documented route that matches how the money was earned, pay the PRC tax that was already due on that
income, and be current on your US filings <em>before</em> the money moves.</p>
</div>

<h2>The four steps, in order</h2>
<div class="tw"><table class="stack">
<thead><tr><th>Step</th><th>Do this</th><th>What it removes</th><th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>Why the premise is wrong, specifically</h2>
<div class="block">
<p><strong>PRC tax law lists nine categories of income. Currency exchange is not one of them.</strong>
Individual income tax attaches to salary, service remuneration, author's remuneration, royalties,
business operation, interest/dividends/bonuses, leasing of assets, transfer of assets and incidental
income. Moving your own after-tax principal between currencies falls outside all nine. That is the
whole of the reason there is no conversion tax.</p>
<p class="note">Quote: "The following categories of individual income shall be subject to individual
income tax: (1) Income from salary and wages; … (9) Incidental income." — {s_cn18}</p>
</div>
<div class="block">
<p><strong>On the US side, a personal conversion recognises no FX gain up to USD 200.</strong>
§988(e)(2) disapplies the recognition rule for an individual's personal transaction, unless the gain
that would otherwise be recognised exceeds USD 200. Above that threshold the exclusion simply does
not apply and ordinary-income treatment follows.</p>
<p class="note">Quote: "no gain shall be recognized … The preceding sentence shall not apply if the
gain which would otherwise be recognized on the transaction exceeds $200." — {s_us01}</p>
</div>
<div class="block">
<p><strong>The 1% remittance transfer tax does not apply to this direction.</strong> It is imposed on
remittances sent FROM the United States TO a recipient in a foreign country, when the sender hands
over cash, a money order, a cashier's cheque or a similar physical instrument. A China-to-United-States
transfer is the opposite direction.</p>
<p class="note">Quote: "a 1% remittance transfer tax applies to remittances sent from the United
States to recipients in foreign countries when the sender provides cash, a money order, a cashier's
check, or other similar physical instrument" — {s_us06}</p>
</div>

<h2>What the PRC tax layer actually is</h2>
<p class="note">Rates are statutory and verified. The <em>base</em> is personal and unknown, so no
dollar figure is invented for it. Where a rate could not be pinned down, the cell is blank.</p>
<div class="tw"><table class="stack">
<thead><tr><th>Item</th><th class="num">Rate</th><th>Base</th><th>Finding</th><th>Source</th></tr></thead>
<tbody>{lay2}</tbody></table></div>

<h2>The single fact that decides your route</h2>
<p>Read the definition, not the folklore. The USD 50,000 annual facilitation quota applies to
individual <em>settlement</em> and to foreign-exchange <em>purchase by a domestic individual</em> —
and a domestic individual is defined by holding a PRC resident identity card.</p>
<div class="tw"><table class="stack">
<thead><tr><th>If the bank has this on file</th><th>You are</th><th class="num">Annual quota</th>
<th>Route to use</th><th>Source</th></tr></thead>
<tbody>
<tr><td data-l="On file"><strong>PRC resident ID, or a permanent-residence ID</strong></td>
 <td data-l="You are">Domestic individual, or an overseas individual expressly allowed the quota</td>
 <td class="num" data-l="Quota">USD 50,000</td>
 <td data-l="Route"><a href="method-A02.html">A02 quota purchase</a></td>
 <td data-l="Source">{q1}</td></tr>
<tr><td data-l="On file"><strong>A US passport only</strong></td>
 <td data-l="You are">Overseas individual (境外个人)</td>
 <td class="num" data-l="Quota">No figure in the rule</td>
 <td data-l="Route"><a href="method-A01.html">A01 documented purchase</a></td>
 <td data-l="Source">{q2}</td></tr>
<tr><td data-l="On file"><strong>Cancelled PRC household registration + pre-emigration property</strong></td>
 <td data-l="You are">Emigrant</td>
 <td class="num" data-l="Quota">No statutory ceiling</td>
 <td data-l="Route"><a href="method-A03.html">A03 emigrant transfer</a></td>
 <td data-l="Source">{q3}</td></tr>
</tbody></table></div>

<h2>What you should not do</h2>
<div class="danger">
<p><strong>Splitting the amount across family and friends.</strong> The prohibition is in the
administrative measure itself, and the watchlist lasts the year of listing plus two more, during
which every FX transaction you make is pushed to the counter under strict documentary review. It
applies to the person who lends a quota as well as the one who borrows.</p>
<p class="note">{p4}</p>
</div>
<div class="danger">
<p><strong>Underground banking, crypto, false invoices, undeclared cash.</strong> The statutory range
for the FX-control offences is a fine of up to 30% of the amount, and 30% to 100% where the
circumstances are serious, plus confiscation. At USD 400,000 that is between {a} and {b} — larger
than every lawful fee in this entire analysis, added together, many times over.</p>
<p class="note">{p123}</p>
</div>

<h2>The realistic path if your balance is not salary</h2>
<p>If the money is not documented current-account income, the honest position is that no clean route
matches it. The three real options are: give it a genuine current-account character by earning it
via a real activity (a registered trade or e-commerce business); use the capital-account route that
fits the underlying event (property sale, emigration, inheritance); or leave some of it in RMB for
future RMB needs and convert only the rest. Inventing a character for it is the offence described
above.</p>
<p class="note">Detail on each: <a href="methods.html">all routes</a> ·
<a href="methodology.html">method and limits</a></p>
""".format(
        rows="".join(rows), lay2=lay2,
        s_cn18=src_links(["CN-18"]), s_us01=src_links(["US-01"]), s_us06=src_links(["US-06"]),
        q1=src_links(["CN-09", "CN-07"]), q2=src_links(["CN-02", "CN-08", "CN-09"]),
        q3=src_links(["CN-14", "CN-16"]),
        p4=src_links(["CN-03", "CN-11"]),
        p123=src_links(["CN-04", "CN-05", "CN-06", "CN-20"]),
        a=money(400_000 * 0.30, 0), b=money(400_000 * 1.00, 0))
    return page("The answer", body, "answer.html")
