# -*- coding: utf-8 -*-
"""Edition H — route pages, penalty, tax, reporting, steps."""

from sitegen import (esc, money, pct, share, src_links, status_badge, page, CATEGORIES,
                     COMPUTED, BLANK, PROHIB, NEUTRAL, METHODS, METHOD, SRC, ladder)
from costs import AMOUNTS, FX_MARGIN_PCT, FX_ROUND_TRIP_PCT, BUY_SPOT, SELL_SPOT, MID, q2
from penalties import LAYER2, LAYER3, LAYER4, REPORTING, STRATEGY

CAT_TITLE = {c[0]: c[1] for c in CATEGORIES}
CAT_LEDE = {c[0]: c[2] for c in CATEGORIES}

LADDERS = {m["id"]: dict(ladder(m)) for m in COMPUTED}


def short(m):
    return m.get("short", m["name"])


# ==========================================================================
# All routes — index by category
# ==========================================================================

def p_methods():
    out = []
    for cid, title, lede in CATEGORIES:
        items = [m for m in METHODS if m["category"] == cid]
        if not items:
            continue
        rows = []
        for m in items:
            cost = "—"
            if m["id"] in LADDERS:
                cost = "{} at $400k".format(money(LADDERS[m["id"]][400_000]["total"]))
            elif m["cost_model"] == "prohibited":
                cost = "not priced"
            elif m["cost_model"] == "none":
                cost = "no conversion"
            else:
                cost = "unpublished"
            rows.append(
                '<tr><td data-l="Route"><a href="method-{i}.html"><strong>{i} · {n}</strong></a>'
                '<br><span class="note">{z}</span></td>'
                '<td data-l="Status">{st}</td>'
                '<td data-l="Cap">{cap}</td>'
                '<td data-l="Cost at $400k">{c}</td>'
                '<td data-l="Source">{s}</td></tr>'.format(
                    i=m["id"], n=esc(short(m)), z=esc(m["zh"]), st=status_badge(m["status"]),
                    cap=esc(m["cap"]), c=esc(cost), s=src_links(m["sources"][:3])))
        out.append("""
<h2 id="{cid}">{title} <span class="pill">{n}</span></h2>
<p class="note">{lede}</p>
<div class="tw"><table class="stack">
<thead><tr><th>Route</th><th>Status</th><th>Cap</th><th class="num">All-in at $400,000</th>
<th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>
""".format(cid=cid, title=esc(title), n=len(items), lede=esc(lede), rows="".join(rows)))

    body = """
<p class="crumb"><a href="index.html">Dashboard</a> / All routes</p>
<h1>{n} ways to get CNY out of China</h1>
<p class="lede">Every route this session could verify, grouped by category, with its legal status, the
provision behind it, and — where a published price exists — what it costs at the top of the range.
Prohibited routes are shown so you can recognise them; none of them has execution steps.</p>
<div class="card">
<p><strong>{n} routes.</strong> Classified as: {sl} {nl} · {sc} {nc} · {sp} {np_} · {sn} {nn}.</p>
<ul>
<li>{sl} — permitted, and the permitting provision was retrieved.</li>
<li>{sc} — permitted only if a stated condition is met: identity, documents, or a real underlying event.</li>
<li>{sp} — unlawful. Listed for recognition only, with no execution steps.</li>
<li>{sn} — a legitimate alternative that involves no conversion at all.</li>
</ul>
<p class="note">The classification is this site's editorial judgement applied to the quoted text; the
provision behind each route is linked on the route's own page.</p>
</div>
{out}
""".format(n=len(METHODS),
           sl=status_badge("lawful"), sc=status_badge("conditional"),
           sp=status_badge("prohibited"), sn=status_badge("not_a_transfer"),
           nl=sum(1 for m in METHODS if m["status"] == "lawful"),
           nc=sum(1 for m in METHODS if m["status"] == "conditional"),
           np_=sum(1 for m in METHODS if m["status"] == "prohibited"),
           nn=sum(1 for m in METHODS if m["status"] == "not_a_transfer"),
           out="".join(out))
    return page("All routes", body, "methods.html")


# ==========================================================================
# One page per route
# ==========================================================================

def p_method(m):
    pros = "".join("<li>{}</li>".format(esc(p)) for p in m["pros"])
    cons = "".join("<li>{}</li>".format(esc(c)) for c in m["cons"])
    docs = "".join("<li>{}</li>".format(esc(d)) for d in m["docs"]) or "<li>None.</li>"
    steps = "".join("<li>{}</li>".format(esc(s)) for s in m["steps"])
    costline = ""
    if m["id"] in LADDERS:
        L = LADDERS[m["id"]]
        costline = """
<h2>Cost at a glance</h2>
<div class="tw"><table class="stack">
<thead><tr><th class="num">Amount</th><th class="num">Total cost</th><th class="num">Share</th>
<th class="num">Net received</th><th>Source</th></tr></thead><tbody>{r}</tbody></table></div>
<p><a href="cost-{i}.html">Full 40-row ladder for {i} &rarr;</a></p>
""".format(i=m["id"], r="".join(
            '<tr><td class="num" data-l="Amount">{a}</td>'
            '<td class="num big" data-l="Total cost">{t}</td>'
            '<td class="num" data-l="Share">{p}</td>'
            '<td class="num" data-l="Net received">{n}</td>'
            '<td data-l="Source">{s}</td></tr>'.format(
                a=money(a, 0), t=money(L[a]["total"]), p=share(L[a]["total"], a),
                n=money(a - L[a]["total"]), s=src_links(m["sources"][:4]))
            for a in (10_000, 50_000, 100_000, 200_000, 400_000)))
    elif m["cost_model"] == "unknown":
        costline = """
<div class="flag"><strong>No all-in figure is published.</strong> At least one component of this
route has no official price, so every cell in its ladder would be an estimate. It is left blank and
appears on the <a href="flagged.html">Flagged for review</a> page instead.</div>
"""
    elif m["cost_model"] == "prohibited":
        costline = """
<div class="danger"><strong>Prohibited.</strong> No price, no ladder and no steps. The statutory
sanction range is on <a href="penalty.html">the penalty page</a>.</div>
"""
    else:
        costline = """
<div class="ok"><strong>No conversion cost.</strong> Nothing is exchanged, so there is no FX margin
or bank fee on this amount.</div>
"""

    body = """
<p class="crumb"><a href="index.html">Dashboard</a> / <a href="methods.html">All routes</a> /
<a href="methods.html#{cat}">{catname}</a> / {id}</p>
<p class="eyebrow">{catname} · {id}</p>
<h1>{name}</h1>
<p class="lede">{zh} &nbsp; {st}</p>

<h2>The rule</h2>
<div class="block"><p>{rule}</p><p class="note">Source: {s}</p></div>

<div class="two">
<div class="card"><h3>Who can use it</h3><p>{who}</p>
<h3 style="margin-top:18px">Cap or limit</h3><p>{cap}</p></div>
<div class="card"><h3>Documents</h3><ul>{docs}</ul></div>
</div>

<div class="two">
<div class="card"><h3>Pros</h3><ul class="pros">{pros}</ul></div>
<div class="card"><h3>Cons</h3><ul class="cons">{cons}</ul></div>
</div>

{costline}

<h2>Step by step</h2>
<ol>{steps}</ol>

<p class="note">All sources for this route: {allsrc}</p>
<p><a href="methods.html">&larr; all routes</a></p>
""".format(cat=m["category"], catname=esc(CAT_TITLE[m["category"]]), id=m["id"],
           name=esc(m["name"]), zh=esc(m["zh"]), st=status_badge(m["status"]),
           rule=esc(m["rule"]), s=src_links(m["sources"][:4]), who=esc(m["who"]),
           cap=esc(m["cap"]), docs=docs, pros=pros, cons=cons, costline=costline,
           steps=steps, allsrc=src_links(m["sources"]))
    return page(m["id"] + " · " + short(m), body, "methods.html")


# ==========================================================================
# Penalty
# ==========================================================================

def p_penalty():
    l3 = "".join(
        '<tr><td data-l="Conduct"><strong>{c}</strong><br><span class="note">{zh}</span></td>'
        '<td class="num" data-l="Fine">{f}</td>'
        '<td data-l="Escalation">{e}</td><td data-l="Also">{o}</td>'
        '<td data-l="Source">{s}</td></tr>'.format(
            c=esc(x["conduct"]), zh=esc(x["cn"]),
            f="up to {}%".format(x["max_pct"]) if x["max_pct"] else "see note",
            e=esc(x["escalator"]), o=esc(x["other"]), s=src_links(x["sources"]))
        for x in LAYER3)

    l4 = []
    for x in LAYER4:
        if x.get("amount") is not None:
            amt = "$%s" % "{:,.0f}".format(x["amount"])
        elif x.get("pct"):
            amt = "{}%".format(x["pct"])
        else:
            amt = "—"
        l4.append(
            '<tr><td data-l="Penalty"><strong>{i}</strong></td>'
            '<td class="num" data-l="{lab}">{a}</td>'
            '<td data-l="Basis">{b}</td><td data-l="Source">{s}</td></tr>'.format(
                i=esc(x["item"]), lab=esc(x["amount_label"]), a=esc(amt),
                b=esc(x["basis"]), s=src_links(x["sources"])))
    l4 = "".join(l4)

    # the layering table at a 400k balance, deliberately showing blanks where personal
    body = """
<p class="crumb"><a href="index.html">Dashboard</a> / Penalty</p>
<h1>Breaking down "the conversion penalty"</h1>
<p class="lede">The premise says converting triggers a considerable tax. Checked provision by
provision, that premise is four unrelated things stacked into one word. This page separates them and
puts a verified number on each, and leaves blank what cannot be known without your own facts.</p>

{nolayer}

<h2>Layer 1 · friction — the only real cost of converting</h2>
<p class="note">{l1note}</p>
<div class="tw"><table class="stack">
<thead><tr><th>Component</th><th class="num">At $10,000</th><th class="num">At $100,000</th>
<th class="num">At $400,000</th><th>Source</th></tr></thead>
<tbody>
<tr><td data-l="Component"><strong>FX margin, one conversion</strong></td>
<td class="num" data-l="$10,000">{fx10}</td><td class="num" data-l="$100,000">{fx100}</td>
<td class="num" data-l="$400,000">{fx400}</td><td data-l="Source">{s_fx}</td></tr>
<tr><td data-l="Component"><strong>Bank commission</strong></td>
<td class="num" data-l="$10,000">{cm10}</td><td class="num" data-l="$100,000">{cm100}</td>
<td class="num" data-l="$400,000">{cm400}</td><td data-l="Source">{s_cm}</td></tr>
<tr><td data-l="Component"><strong>Cable fee</strong></td>
<td class="num" data-l="$10,000">{cb10}</td><td class="num" data-l="$100,000">{cb100}</td>
<td class="num" data-l="$400,000">{cb400}</td><td data-l="Source">{s_cb}</td></tr>
<tr><td data-l="Component"><strong>Full-amount arrival</strong></td>
<td class="num" data-l="$10,000">{fa10}</td><td class="num" data-l="$100,000">{fa100}</td>
<td class="num" data-l="$400,000">{fa400}</td><td data-l="Source">{s_fa}</td></tr>
<tr><td data-l="Component"><strong>Receiving bank (named example)</strong></td>
<td class="num" data-l="$10,000">{rb10}</td><td class="num" data-l="$100,000">{rb100}</td>
<td class="num" data-l="$400,000">{rb400}</td><td data-l="Source">{s_rb}</td></tr>
<tr><td data-l="Component"><strong>Certificate of deposit</strong></td>
<td class="num" data-l="$10,000">{dc10}</td><td class="num" data-l="$100,000">{dc100}</td>
<td class="num" data-l="$400,000">{dc400}</td><td data-l="Source">{s_dc}</td></tr>
<tr style="background:#f7f9fa"><td data-l="Component"><strong>ALL-IN</strong></td>
<td class="num big" data-l="$10,000">{t10}</td><td class="num big" data-l="$100,000">{t100}</td>
<td class="num big" data-l="$400,000">{t400}</td><td data-l="Source">computed</td></tr>
<tr><td data-l="Component"><strong>as a share of the amount</strong></td>
<td class="num" data-l="$10,000">{p10}</td><td class="num" data-l="$100,000">{p100}</td>
<td class="num" data-l="$400,000">{p400}</td><td data-l="Source">computed</td></tr>
</tbody></table></div>

<h2>Layer 2 · PRC income tax — a rate on the income, never on the principal</h2>
<div class="tw"><table class="stack">
<thead><tr><th>Item</th><th class="num">Rate</th><th>Base</th><th>Finding</th><th>Source</th></tr></thead>
<tbody>{l2}</tbody></table></div>

<h2>Layer 3 · PRC conduct fines — what the prohibited routes actually cost</h2>
<div class="tw"><table class="stack">
<thead><tr><th>Conduct</th><th class="num">Fine</th><th>Escalation</th><th>Also</th>
<th>Source</th></tr></thead><tbody>{l3}</tbody></table></div>
<div class="danger"><p><strong>At USD 400,000 the statutory exposure on these is between
{a} and {b}.</strong> That is not a fee you negotiate; it is the range the regulation sets, before
confiscation of illegal gains and before any criminal referral.</p></div>

<h2>Layer 4 · US tax and filing penalties — usually the largest number</h2>
<p class="note">The largest exposure in this whole analysis is not on the Chinese side. It is a
filing failure on the US side, and it is triggered by not filing, not by transferring.</p>
<div class="tw"><table class="stack">
<thead><tr><th>Penalty</th><th class="num">Amount</th><th>Basis</th><th>Source</th></tr></thead>
<tbody>{l4}</tbody></table></div>
<p class="note">The willful FBAR penalty is the greater of the inflation-adjusted statutory figure or
50% of the account balance. At a USD 400,000 balance that second limb is <strong>$200,000</strong> —
{mul} times the total cost of moving the money lawfully.</p>

<h2>What this means in one paragraph</h2>
<p>The conversion itself is not taxed. The friction is under one per cent at every size. The tax that
does arise is on the income behind the money, at 20% of the gain where the transfer-of-assets rate
applies, and it is owed whether or not you move anything. The penalties that reach 30% to 100% are
for using a prohibited channel, and the penalties that reach 50% of the balance are for not filing in
the United States. Every one of those is avoidable by doing the documented thing in the right order.</p>
""".format(nolayer="", l1note=esc("Every cell is a published price, computed for that amount. "
                                 "The FX margin is the one-way bid/ask from BOC's board."),
           l2="".join(
               '<tr><td data-l="Item">{i}</td><td class="num" data-l="Rate">{r}</td>'
               '<td data-l="Base">{b}</td><td data-l="Finding">{f}</td>'
               '<td data-l="Source">{s}</td></tr>'.format(
                   i=esc(x["item"]), r=esc(x["rate"]) or "—", b=esc(x["base"]) or "—",
                   f=esc(x["finding"]), s=src_links(x["sources"])) for x in LAYER2),
           l3=l3, l4=l4,
           fx10=money(LADDERS["A01"][10_000]["fx_margin"]),
           fx100=money(LADDERS["A01"][100_000]["fx_margin"]),
           fx400=money(LADDERS["A01"][400_000]["fx_margin"]),
           cm10=money(LADDERS["A01"][10_000]["commission"]),
           cm100=money(LADDERS["A01"][100_000]["commission"]),
           cm400=money(LADDERS["A01"][400_000]["commission"]),
           cb10=money(LADDERS["A01"][10_000]["cable"]),
           cb100=money(LADDERS["A01"][100_000]["cable"]),
           cb400=money(LADDERS["A01"][400_000]["cable"]),
           fa10=money(LADDERS["A01"][10_000]["full_amount"]),
           fa100=money(LADDERS["A01"][100_000]["full_amount"]),
           fa400=money(LADDERS["A01"][400_000]["full_amount"]),
           rb10=money(LADDERS["A01"][10_000]["receiving"]),
           rb100=money(LADDERS["A01"][100_000]["receiving"]),
           rb400=money(LADDERS["A01"][400_000]["receiving"]),
           dc10=money(LADDERS["A01"][10_000]["documents"]),
           dc100=money(LADDERS["A01"][100_000]["documents"]),
           dc400=money(LADDERS["A01"][400_000]["documents"]),
           t10=money(LADDERS["A01"][10_000]["total"]),
           t100=money(LADDERS["A01"][100_000]["total"]),
           t400=money(LADDERS["A01"][400_000]["total"]),
           p10=share(LADDERS["A01"][10_000]["total"], 10_000),
           p100=share(LADDERS["A01"][100_000]["total"], 100_000),
           p400=share(LADDERS["A01"][400_000]["total"], 400_000),
           s_fx=src_links(["BK-04"]), s_cm=src_links(["BK-01"]), s_cb=src_links(["BK-01"]),
           s_fa=src_links(["BK-03"]), s_rb=src_links(["BK-08"]), s_dc=src_links(["BK-06"]),
           a=money(400_000 * 0.30, 0), b=money(400_000 * 1.00, 0),
           mul=round(200_000 / float(LADDERS["A01"][400_000]["total"])))
    return page("Penalty", body, "penalty.html")


# ==========================================================================
# Tax
# ==========================================================================

def p_tax():
    us = [
        dict(item="Is the conversion itself taxable in the US?",
             rate="0% up to $200 of FX gain", base="exchange-rate gain on a personal transaction",
             finding="No. §988(e)(2) recognises no gain on an individual's personal transaction, unless the gain that would otherwise be recognised exceeds USD 200. Above that the exclusion does not apply and ordinary treatment follows.",
             sources=["US-01"]),
        dict(item="Is the PRC tax creditable against US tax on the same income?",
             rate="credit, not deduction", base="foreign tax actually paid on the same income",
             finding="Yes, in principle, on Form 1116. A credit is generally better than a deduction. If you elect the foreign earned income exclusion you cannot also credit tax on the excluded income.",
             sources=["US-07"]),
        dict(item="Does the 1% remittance transfer tax apply?",
             rate="0%", base="not applicable to this direction",
             finding="No. It applies to remittances sent FROM the United States TO a foreign country when funded with cash, a money order, a cashier's cheque or a similar physical instrument.",
             sources=["US-06"]),
        dict(item="Is receiving money from China a taxable gift?",
             rate="", base="",
             finding="A transfer of your OWN money is not a gift, so the gift question does not arise. A genuine gift from a foreign individual above USD 100,000 in a year is reportable on Form 3520 Part IV — reporting, not tax.",
             sources=["US-05"]),
    ]
    usrows = "".join(
        '<tr><td data-l="Question">{i}</td><td class="num" data-l="Rate">{r}</td>'
        '<td data-l="Base">{b}</td><td data-l="Finding">{f}</td>'
        '<td data-l="Source">{s}</td></tr>'.format(
            i=esc(x["item"]), r=esc(x["rate"]) or "—", b=esc(x["base"]) or "—",
            f=esc(x["finding"]), s=src_links(x["sources"])) for x in us)

    cnrows = "".join(
        '<tr><td data-l="Question">{i}</td><td class="num" data-l="Rate">{r}</td>'
        '<td data-l="Base">{b}</td><td data-l="Finding">{f}</td>'
        '<td data-l="Source">{s}</td></tr>'.format(
            i=esc(x["item"]), r=esc(x["rate"]) or "—", b=esc(x["base"]) or "—",
            f=esc(x["finding"]), s=src_links(x["sources"])) for x in LAYER2)

    body = """
<p class="crumb"><a href="index.html">Dashboard</a> / Tax</p>
<h1>Tax on both sides</h1>
<p class="lede">Two countries, two different questions. China taxes the income that created the
money. The United States taxes your worldwide income and requires you to report the account
independently of any transfer. Neither taxes the act of changing currency.</p>

<h2>China</h2>
<p>The rate table is statutory and verified. The base is personal, so the dollar figure is blank
wherever it would depend on facts this site does not have.</p>
<div class="tw"><table class="stack">
<thead><tr><th>Question</th><th class="num">Rate</th><th>Base</th><th>Finding</th>
<th>Source</th></tr></thead><tbody>{cnrows}</tbody></table></div>

<h2>United States</h2>
<div class="tw"><table class="stack">
<thead><tr><th>Question</th><th class="num">Rate</th><th>Base</th><th>Finding</th>
<th>Source</th></tr></thead><tbody>{usrows}</tbody></table></div>

<h2>How the two interact, mechanically</h2>
<div class="block">
<p><strong>1.</strong> PRC tax is computed on the income under PRC law and paid in China. The
transfer is a separate administrative step that requires proof the tax was paid.</p>
<p><strong>2.</strong> The US taxes the same income under its own rules, in dollars, at the
§988 rate for any exchange-rate gain.</p>
<p><strong>3.</strong> The US grants a credit for the PRC tax paid on that same income, limited to
the US tax attributable to it. Where the PRC rate is higher than the US rate on that slice, the
excess generally cannot be refunded — that difference is the only sense in which double taxation
bites, and it is a rate difference, not a penalty.</p>
</div>

<div class="flag"><strong>What is deliberately not filled in.</strong> Your cost basis, holding
period, whether the money is salary or capital, whether you were tax-resident in China in the year,
and whether you have filed before. All of those change the answer, none of them are known, and
inventing them would produce a confident wrong number. See
<a href="flagged.html">Flagged for review</a>.</div>

<p class="note">Every rate above is quoted on the <a href="sources.html">sources</a> page with the
text retrieved, so it can be checked line by line.</p>
""".format(cnrows=cnrows, usrows=usrows)
    return page("Tax", body, "tax.html")


# ==========================================================================
# US filing
# ==========================================================================

def p_reporting():
    rows = "".join(
        '<tr><td data-l="Form"><strong>{f}</strong></td><td data-l="Who">{w}</td>'
        '<td data-l="Threshold">{t}</td><td data-l="When">{d}</td>'
        '<td data-l="Does it apply">{a}</td><td data-l="Source">{s}</td></tr>'.format(
            f=esc(x["form"]), w=esc(x["who"]), t=esc(x["threshold"]), d=esc(x["when"]),
            a=esc(x["applies_here"]), s=src_links(x["sources"])) for x in REPORTING)

    body = """
<p class="crumb"><a href="index.html">Dashboard</a> / US filing</p>
<h1>What you have to file, before and after you move anything</h1>
<p class="lede">This is the part that actually carries the large numbers. The filing duties attach to
holding the account, not to transferring out of it — which is why they should be fixed first.</p>

<div class="tw"><table class="stack">
<thead><tr><th>Form</th><th>Who</th><th>Threshold</th><th>When</th><th>Does it apply here?</th>
<th>Source</th></tr></thead>
<tbody>{rows}</tbody></table></div>

<h2>The three that matter, in plain terms</h2>
<div class="block">
<p><strong>FBAR.</strong> If the aggregate value of your foreign financial accounts exceeded
USD 10,000 at any point in the calendar year, you file FinCEN Form 114. It goes to FinCEN, not the
IRS. Due 15 April, with an automatic extension to 15 October. It applies whether or not the money
earns anything and whether or not it ever moves.</p>
</div>
<div class="block">
<p><strong>Form 8938.</strong> A separate statement of specified foreign financial assets, filed with
your return. The threshold depends on whether you live inside or outside the United States. It does
not replace the FBAR and the FBAR does not replace it.</p>
</div>
<div class="block">
<p><strong>Form 3520 Part IV.</strong> Only for a genuine gift or bequest from a foreign person above
USD 100,000 in the year. Your own money coming back to you is not that. Report the receipt; there is
no tax on the receipt itself in the ordinary case.</p>
</div>

<div class="flag"><strong>The one people get wrong.</strong> The 1% remittance transfer excise tax
introduced from 1 January 2026 is widely repeated as a cost of getting money out of China. It is not:
it applies to money sent <em>from</em> the United States <em>to</em> a foreign recipient, funded with
cash or a similar physical instrument. China-to-US is the opposite direction.</div>

<div class="danger"><strong>Why the order matters.</strong> A willful FBAR penalty is the greater of
USD 165,353 (inflation-adjusted) or 50% of the account balance at the time of the violation. At a
USD 400,000 balance that is USD 200,000 — more than 200 times the entire lawful cost of moving the
same money. Fix the filings first; the transfer is cheap by comparison.</div>

<p class="note">Sources: {s}</p>
""".format(rows=rows, s=src_links(["US-02", "US-03", "US-04", "US-05", "US-06", "US-08"]))
    return page("US filing", body, "reporting.html")


# ==========================================================================
# Steps
# ==========================================================================

def p_steps():
    body = """
<p class="crumb"><a href="index.html">Dashboard</a> / Step by step</p>
<h1>Exactly what happens, in order</h1>
<p class="lede">No manual input is needed from you to use this page: it is the sequence itself. Work
down it once, at the top, and stop at the first step whose condition you cannot meet — that is the
answer to which route you can use.</p>

<h2>Step 0 · three facts you must establish before anything else</h2>
<div class="tw"><table class="stack">
<thead><tr><th>Fact</th><th>Why it decides everything</th><th>If the answer is no</th><th>Source</th></tr></thead>
<tbody>
<tr><td data-l="Fact"><strong>Is the money income you declared in China, with a PRC tax record?</strong></td>
 <td data-l="Why">This is the document the bank reviews on the current-account route, and a required attachment on the capital-account routes.</td>
 <td data-l="If no">Skip to step 3. The current-account route is closed until the tax position is settled.</td>
 <td data-l="Source">{s1}</td></tr>
<tr><td data-l="Fact"><strong>What identity document does the bank hold?</strong></td>
 <td data-l="Why">A PRC resident ID or permanent-residence ID opens the USD 50,000 quota. A US passport alone does not.</td>
 <td data-l="If US passport">Use the documented route A01, not the quota route A02.</td>
 <td data-l="Source">{s2}</td></tr>
<tr><td data-l="Fact"><strong>Is this about pre-emigration property, an inheritance, or a property sale?</strong></td>
 <td data-l="Why">Each of those has its own capital-account route with its own approval step.</td>
 <td data-l="If none">Those routes are unavailable; you are on the current-account path.</td>
 <td data-l="Source">{s3}</td></tr>
</tbody></table></div>

<h2>Step 1 · fix the US side first</h2>
<ol>
<li>List every foreign account, with its maximum value in each calendar year you held it.</li>
<li>File or correct the FBAR for each of those years if the aggregate exceeded USD 10,000 at any point.</li>
<li>Check whether Form 8938 applies at your threshold and living situation, and file it with the return.</li>
<li>Do this <em>before</em> moving money. The penalty is for the omission, not the transfer.</li>
</ol>
<p class="note">{s4}</p>

<h2>Step 2 · assemble the evidence pack</h2>
<div class="tw"><table class="stack">
<thead><tr><th>Document</th><th>Where it comes from</th><th>Which route needs it</th><th>Source</th></tr></thead>
<tbody>
<tr><td data-l="Document">Passport</td><td data-l="Where">You</td><td data-l="Route">All</td><td data-l="Source">{s_pass}</td></tr>
<tr><td data-l="Document">PRC individual income tax record or duty-paid voucher</td>
 <td data-l="Where">PRC tax authority portal, or the withholding employer</td>
 <td data-l="Route">A01, A03, A04, A05, A06</td><td data-l="Source">{s_tax}</td></tr>
<tr><td data-l="Document">Employment contract, payslips, payroll records</td>
 <td data-l="Where">Employer</td><td data-l="Route">A01, A06</td><td data-l="Source">{s_tax}</td></tr>
<tr><td data-l="Document">Property title deed and sale contract</td>
 <td data-l="Where">Registry and the sale file</td><td data-l="Route">A03, A05</td><td data-l="Source">{s_prop}</td></tr>
<tr><td data-l="Document">Cancelled PRC household registration certificate</td>
 <td data-l="Where">Public security bureau</td><td data-l="Route">A03</td><td data-l="Source">{s_emig}</td></tr>
<tr><td data-l="Document">Proof of settlement abroad, certified by a PRC embassy or consulate</td>
 <td data-l="Where">The consulate</td><td data-l="Route">A03, A04</td><td data-l="Source">{s_cons}</td></tr>
<tr><td data-l="Document">Certificate of deposit or account statement</td>
 <td data-l="Where">The bank, CNY 20–40 a copy</td><td data-l="Route">Supporting evidence</td><td data-l="Source">{s_cert}</td></tr>
</tbody></table></div>
<p class="note">{s5}</p>

<h2>Step 3 · make the purchase at the bank</h2>
<ol>
<li>Go to the branch that holds the account and ask for <em>境外个人购汇</em> — overseas-individual
purchase — rather than anything described as a quota purchase.</li>
<li>Hand over the evidence pack. The bank reviews it; it may refuse, and the guideline expressly
permits a bank to refuse a transaction whose authenticity it doubts.</li>
<li>The applied rate is the counter rate. The public board is indicative only and says so itself.</li>
<li>Ask for full-amount arrival if you want a known total. Without it, a correspondent bank may
deduct an unpublished amount from the principal instead.</li>
</ol>
<p class="note">{s6}</p>

<h2>Step 4 · send the wire</h2>
<ol>
<li>The destination must be an account in your own name.</li>
<li>Commission is 0.1% of the CNY equivalent, minimum CNY 50, maximum CNY 260, plus a CNY 150 cable
fee outside Hong Kong, Macau and Taiwan.</li>
<li>At USD 400,000 that commission is still only CNY 260 — the cap is why the effective rate falls
as the amount rises.</li>
<li>Keep the purchase advice, the remittance advice and the arrival statement together. That bundle
is the contemporaneous record for both countries.</li>
</ol>
<p class="note">{s7}</p>

<h2>Step 5 · if step 3 is refused</h2>
<ol>
<li>Ask the bank to state, in writing, which document or which element of the transaction is not
accepted. That is the input to whatever you do next.</li>
<li>If the money is pre-emigration property, switch to route A03 and start the SAFE application.</li>
<li>If it is a property sale, route A05 with SAFE approval.</li>
<li>If it is an inheritance, route A04.</li>
<li>Do not substitute splitting, a private dealer or crypto. Those convert a documentary refusal into
a 20%-100% statutory exposure.</li>
</ol>
<p class="note">{s8}</p>

<h2>Cost of the whole sequence, at each size</h2>
<div class="tw"><table class="stack">
<thead><tr><th class="num">Amount</th><th class="num">Total cost</th><th class="num">Share</th>
<th class="num">Net received</th><th>Source</th></tr></thead>
<tbody>{ladder}</tbody></table></div>
""".format(
        s1=src_links(["CN-08", "CN-09", "CN-15"]),
        s2=src_links(["CN-02", "CN-07", "CN-09"]),
        s3=src_links(["CN-14", "CN-16"]),
        s4=src_links(["US-04", "US-08", "US-02"]),
        s5=src_links(["CN-15", "BK-06"]),
        s_pass=src_links(["CN-09"]), s_tax=src_links(["CN-15"]),
        s_prop=src_links(["CN-14"]), s_emig=src_links(["CN-15"]),
        s_cons=src_links(["CN-15"]), s_cert=src_links(["BK-06"]),
        s6=src_links(["CN-08", "BK-04", "BK-03"]),
        s7=src_links(["BK-01", "BK-02"]),
        s8=src_links(["CN-14", "CN-16", "CN-04"]),
        ladder="".join(
            '<tr><td class="num" data-l="Amount">{a}</td>'
            '<td class="num big" data-l="Total cost">{t}</td>'
            '<td class="num" data-l="Share">{p}</td>'
            '<td class="num" data-l="Net received">{n}</td>'
            '<td data-l="Source">{s}</td></tr>'.format(
                a=money(a, 0), t=money(LADDERS["A01"][a]["total"]),
                p=share(LADDERS["A01"][a]["total"], a), n=money(a - LADDERS["A01"][a]["total"]),
                s=src_links(["BK-01", "BK-04"]))
            for a in (10_000, 50_000, 100_000, 200_000, 300_000, 400_000)))
    return page("Step by step", body, "steps.html")
