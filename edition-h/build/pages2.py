# -*- coding: utf-8 -*-
"""Edition H — cost pages."""

from decimal import Decimal

from sitegen import (esc, money, pct, share, src_links, status_badge, page, COMPUTED, BLANK,
                     PROHIB, NEUTRAL, LEAD, METHOD, METHODS, SRC, ladder, compute)
from costs import (AMOUNTS, FX_MARGIN_PCT, FX_ROUND_TRIP_PCT, BUY_SPOT, SELL_SPOT,
                   MID, REFERENCE, q2, q4, usd_to_cny, commission_cny,
                   COMMISSION_MAX_CNY, RECEIVING_BANK_USD, FULL_AMOUNT_USD,
                   CABLE_FEE_CNY, deposit_cert_usd, carriage_cert_usd, cable_usd)

KEY = [10_000, 50_000, 100_000, 200_000, 300_000, 400_000]

LADDERS = {m["id"]: dict(ladder(m)) for m in COMPUTED}


# ==========================================================================
# The master ladder — every computed method side by side
# ==========================================================================

def p_costs():
    """Compact matrix on phones (amount + best route + all-in %), full table on desktop."""
    lead = LADDERS[LEAD["id"]]
    rows = []
    for a in AMOUNTS:
        c = lead[a]
        rows.append(
            '<tr><td data-l="Amount" class="num"><strong>{a}</strong></td>'
            '<td class="num" data-l="FX margin">{fx}</td>'
            '<td class="num" data-l="Commission">{cm}</td>'
            '<td class="num" data-l="Cable">{cb}</td>'
            '<td class="num" data-l="Full amount">{fa}</td>'
            '<td class="num" data-l="Receiving bank">{rb}</td>'
            '<td class="num" data-l="Documents">{doc}</td>'
            '<td class="num big" data-l="TOTAL">{t}</td>'
            '<td class="num" data-l="Share">{p}</td>'
            '<td data-l="Source">{s}</td></tr>'.format(
                a=money(a, 0), fx=money(c["fx_margin"]), cm=money(c["commission"]),
                cb=money(c["cable"]), fa=money(c["full_amount"]), rb=money(c["receiving"]),
                doc=money(c["documents"]), t=money(c["total"]),
                p=share(c["total"], a),
                s=src_links(["BK-01", "BK-03", "BK-04", "BK-08"])))

    # comparison at representative sizes across every computed method
    comp_head = "".join('<th class="num">{}</th>'.format(money(a, 0)) for a in KEY)
    comp_rows = []
    for m in COMPUTED:
        cells = []
        for a in KEY:
            c = LADDERS[m["id"]][a]
            cells.append('<td class="num" data-l="{}">{}</td>'.format(money(a, 0), money(c["total"])))
        comp_rows.append(
            '<tr><td data-l="Route"><a href="method-{i}.html">{n}</a></td>{c}'
            '<td data-l="Source">{s}</td></tr>'.format(
                i=m["id"], n=esc(m["short"] if "short" in m else m["name"]),
                c="".join(cells), s=src_links(m["sources"][:3])))
    comp = "".join(comp_rows)

    blank_rows = "".join(
        '<tr><td data-l="Route"><a href="method-{i}.html">{n}</a></td>'
        '<td data-l="Why blank">{w}</td><td data-l="Source">{s}</td></tr>'.format(
            i=m["id"], n=esc(m["name"]),
            w=esc(m.get("blank_reason", "No published price for at least one component.")),
            s=src_links(m["sources"][:3])) for m in BLANK)

    body = """
<p class="crumb"><a href="index.html">Dashboard</a> / Costs</p>
<h1>Cost at every USD 10,000 step, to USD 400,000</h1>
<p class="lede">40 rows, one per USD 10,000 increment. Every figure is computed from a published
tariff, and the arithmetic is re-run by the build. Where a route has no published price, its cells
are blank and it is listed at the bottom of this page — never estimated.</p>

<div class="ok">
<p><strong>Read this first.</strong> The whole ladder for the recommended route costs
<strong>{t400}</strong> at USD 400,000 and <strong>{t10}</strong> at USD 10,000. The cost is
front-loaded by fixed fees, so the percentage falls as the amount rises — from {p10} to {p400}.
Nothing in this table is a tax.</p>
</div>

<h2>Route A01 · documented overseas-individual purchase and remittance</h2>
<p class="note">FX margin on BOC's one-way bid/ask ({fxm}) + commission 0.1% (CNY 50 min, CNY 260 max)
+ CNY {cable} cable + USD {fa} full-amount arrival + USD {rb} named receiving bank + certificate of
deposit. Sources: {src}.</p>
<div class="tw"><table class="stack">
<thead><tr><th>Amount</th><th class="num">FX margin</th><th class="num">Commission</th>
<th class="num">Cable</th><th class="num">Full amount</th><th class="num">Receiving</th>
<th class="num">Documents</th><th class="num">TOTAL</th><th class="num">Share</th>
<th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>Every priced route side by side</h2>
<p class="note">Only routes with a complete published price can appear here. A dash would mean the
component is unknown, so those routes are excluded from this table entirely rather than shown as
zeros. Each route's own page has its full 40-row ladder.</p>
<div class="tw"><table class="stack">
<thead><tr><th>Route</th>{head}<th>Source</th></tr></thead>
<tbody>{comp}</tbody></table></div>

<h2>Routes with no published price</h2>
<p class="note">These are lawful or conditional routes whose all-in cost cannot be computed from an
official page. They are blank by rule, and each appears on the
<a href="flagged.html">Flagged for review</a> page.</p>
<div class="tw"><table class="stack">
<thead><tr><th>Route</th><th>Why the cells are blank</th><th>Source</th></tr></thead>
<tbody>{blank}</tbody></table></div>

<h2>The formula, stated plainly</h2>
<div class="block">
<p><strong>CNY to USD at the board.</strong> The board quotes CNY per 100 USD. Buying USD costs
{SELL} per 100; the midpoint of the buy and sell is {MID}. The one-way margin you pay is
(SELL − MID) ÷ MID = <strong>{fxm}</strong>. The frequently quoted 0.42% is the round trip — the cost
of converting twice — and is not the cost of converting once.</p>
<p><strong>Commission.</strong> 0.1% of the CNY equivalent, floored at CNY 50 and capped at CNY 260.
Because it is capped, its effective rate collapses as the amount rises: at USD 10,000 it is
{m10}; at USD 400,000 it is {m400}.</p>
<p><strong>Everything else is fixed.</strong> The cable fee is CNY 150, full-amount arrival is USD 15
or USD 25, the named receiving fee is USD 15, and the certificate of deposit is CNY 20–40. Fixed
costs are why the all-in percentage falls with size.</p>
</div>
<p class="note">Sources for the formula: {fsrc}</p>
<p class="note">Every other method's 40-row ladder is on its own page — see
<a href="methods.html">all routes</a>.</p>
""".format(t400=money(LADDERS[LEAD["id"]][400_000]["total"]),
           t10=money(LADDERS[LEAD["id"]][10_000]["total"]),
           p10=share(LADDERS[LEAD["id"]][10_000]["total"], 10_000),
           p400=share(LADDERS[LEAD["id"]][400_000]["total"], 400_000),
           fxm=pct(FX_MARGIN_PCT, 4), cable=CABLE_FEE_CNY, fa=FULL_AMOUNT_USD,
           rb=RECEIVING_BANK_USD,
           src=src_links(["BK-01", "BK-03", "BK-04", "BK-08"]),
           rows="".join(rows), head=comp_head, comp=comp, blank=blank_rows,
           SELL=SELL_SPOT, MID=q2(MID),
           m10=money(LADDERS[LEAD["id"]][10_000]["commission"]),
           m400=money(LADDERS[LEAD["id"]][400_000]["commission"]),
           fsrc=src_links(["BK-01", "BK-02", "BK-04"]))
    return page("Costs", body, "costs.html")


# ==========================================================================
# One page per priced route
# ==========================================================================

def p_method_cost(m):
    """Full 40-row ladder for one route."""
    L = LADDERS[m["id"]]
    if m["cost_model"] == "boc_cash":
        head = ('<th>Amount</th><th class="num">FX margin</th><th class="num">Commission</th>'
                '<th class="num">Carriage cert.</th><th class="num">TOTAL</th>'
                '<th class="num">Share</th><th>Source</th>')
        rows = "".join(
            '<tr><td data-l="Amount" class="num"><strong>{a}</strong></td>'
            '<td class="num" data-l="FX margin">{fx}</td>'
            '<td class="num" data-l="Commission">{cm}</td>'
            '<td class="num" data-l="Carriage cert.">{cc}</td>'
            '<td class="num big" data-l="TOTAL">{t}</td>'
            '<td class="num" data-l="Share">{p}</td>'
            '<td data-l="Source">{s}</td></tr>'.format(
                a=money(a, 0), fx=money(c["fx_margin"]), cm=money(c["commission"]),
                cc=money(c["carriage_cert"]), t=money(c["total"]), p=share(c["total"], a),
                s=src_links(["BK-01", "BK-04", "BK-05"]))
            for a, c in sorted(L.items()))
    elif m["cost_model"] == "boc_convert_only":
        head = ('<th>Amount</th><th class="num">FX margin</th><th class="num">Commission</th>'
                '<th class="num">Documents</th><th class="num">TOTAL</th>'
                '<th class="num">Share</th><th>Source</th>')
        rows = "".join(
            '<tr><td data-l="Amount" class="num"><strong>{a}</strong></td>'
            '<td class="num" data-l="FX margin">{fx}</td>'
            '<td class="num" data-l="Commission">{cm}</td>'
            '<td class="num" data-l="Documents">{doc}</td>'
            '<td class="num big" data-l="TOTAL">{t}</td>'
            '<td class="num" data-l="Share">{p}</td>'
            '<td data-l="Source">{s}</td></tr>'.format(
                a=money(a, 0), fx=money(c["fx_margin"]), cm=money(c["commission"]),
                doc=money(c["documents"]), t=money(c["total"]), p=share(c["total"], a),
                s=src_links(["BK-01", "BK-04"]))
            for a, c in sorted(L.items()))
    else:
        head = ('<th>Amount</th><th class="num">FX margin</th><th class="num">Commission</th>'
                '<th class="num">Cable</th><th class="num">Full amount</th>'
                '<th class="num">Receiving</th><th class="num">Documents</th>'
                '<th class="num">TOTAL</th><th class="num">Share</th><th>Source</th>')
        rows = "".join(
            '<tr><td data-l="Amount" class="num"><strong>{a}</strong></td>'
            '<td class="num" data-l="FX margin">{fx}</td>'
            '<td class="num" data-l="Commission">{cm}</td>'
            '<td class="num" data-l="Cable">{cb}</td>'
            '<td class="num" data-l="Full amount">{fa}</td>'
            '<td class="num" data-l="Receiving">{rb}</td>'
            '<td class="num" data-l="Documents">{doc}</td>'
            '<td class="num big" data-l="TOTAL">{t}</td>'
            '<td class="num" data-l="Share">{p}</td>'
            '<td data-l="Source">{s}</td></tr>'.format(
                a=money(a, 0), fx=money(c["fx_margin"]), cm=money(c["commission"]),
                cb=money(c["cable"]), fa=money(c["full_amount"]), rb=money(c["receiving"]),
                doc=money(c["documents"]), t=money(c["total"]), p=share(c["total"], a),
                s=src_links(m["sources"][:4]))
            for a, c in sorted(L.items()))

    body = """
<p class="crumb"><a href="index.html">Dashboard</a> / <a href="costs.html">Costs</a> /
<a href="method-{id}.html">{id}</a></p>
<h1>{name}</h1>
<p class="lede">{note}</p>
<div class="tw"><table class="stack">
<thead><tr>{head}</tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="note">Cost components: {src}. The arithmetic is recomputed from the tariff parameters on
every build; see <a href="methodology.html">method</a>.</p>
<p><a href="method-{id}.html">&larr; the rule, documents, pros and cons for {id}</a> ·
<a href="costs.html">the master ladder</a></p>
""".format(id=m["id"], name=esc(m["name"]), note=esc(L[AMOUNTS[0]]["note"]),
           head=head, rows=rows, src=src_links(m["sources"]))
    return page("Cost · " + m["id"], body, "costs.html")
