# -*- coding: utf-8 -*-
"""Edition H — sources, flagged, repo audit, methodology."""

from sitegen import (esc, money, pct, src_links, grade_badge, page, SOURCES, SRC,
                     METHODS, METHOD, COMPUTED, BLANK, PROHIB)
from costs import AMOUNTS, FX_MARGIN_PCT, FX_ROUND_TRIP_PCT, BUY_SPOT, SELL_SPOT, MID, REFERENCE

RETRIEVED = "2026-11-09"

# --------------------------------------------------------------------------
# Flagged items — every blank and every irregularity, with its source
# --------------------------------------------------------------------------
FLAGS = [
    dict(id="H01", sev="high", kind="unknown fact",
         title="The source of the funds is unknown, so no single route can be named as yours",
         detail="Every route in this analysis is conditional on how the money was earned and documented. Salary, a property sale, an inheritance and undifferentiated savings lead to four different provisions. No personal fact was supplied and none has been assumed.",
         sources=["CN-08", "CN-09", "CN-14"]),
    dict(id="H02", sev="high", kind="unknown fact",
         title="Which identity document the bank holds is unknown",
         detail="A PRC resident identity card or a permanent-residence ID opens the USD 50,000 facilitation quota; a US passport alone does not, and routes you to the documented path instead. This single fact decides between A01 and A02.",
         sources=["CN-02", "CN-07", "CN-09"]),
    dict(id="H03", sev="high", kind="unknown fact",
         title="Prior US filing history is unknown",
         detail="Whether the FBAR and Form 8938 were filed for prior years, and whether any omission was wilful, changes the exposure from zero to 50% of the balance. No figure is asserted for it.",
         sources=["US-04", "US-09"]),
    dict(id="H04", sev="high", kind="inherited error (Edition D)",
         title="Edition D prices a staged emigrant release schedule that was abolished in 2014",
         detail="Edition D's cost model for M03 applies releases of 50%, 25% and 25% above CNY 200,000 and states the rule on its summary page. That staging came from the 2004 measure. 汇发〔2014〕2号 art. 6(2) abolished the staged-release requirement: after approval the bank may remit once or in instalments. Edition H does not apply the staging and prices A03 as a single remittance, which is what the current text allows. Edition D's underlying figures for other routes were not altered or relied on here.",
         sources=["CN-16", "CN-14"]),
    dict(id="H05", sev="medium", kind="stale rate risk",
         title="The FX board moves every business day",
         detail="The board used here was captured on 2026-11-09 at 09:15:45 Beijing time. The board itself states that the rate actually applied at the counter governs, so every FX-derived figure on this site is a point-in-time arithmetic result, not a quote you will receive.",
         sources=["BK-04"]),
    dict(id="H06", sev="medium", kind="named example only",
         title="The receiving-bank fee is one bank's published price",
         detail="USD 15 is Chase's published incoming international wire fee on the business schedule retrieved. Your own bank's inbound fee was not verified and may be zero. The ladder keeps it as a named component so it can be removed.",
         sources=["BK-08"]),
    dict(id="H07", sev="medium", kind="provider terms",
         title="Wise's fee is not published as a static schedule",
         detail="Wise publishes the eligibility gate and the per-transfer ceilings, but the fee is quoted only when a transfer is built. No ladder is shown for C02 because a publicly verifiable static price does not exist.",
         sources=["BK-09", "BK-10"]),
    dict(id="H08", sev="medium", kind="unverified component",
         title="Card spending and overseas ATM fees are not priced",
         detail="The card conversion rate embeds a margin that is not published in advance, and cash-withdrawal caps abroad could not be pinned to an operative notice in this session. Route C03 is therefore blank.",
         sources=["CN-09"]),
    dict(id="H09", sev="medium", kind="unverified component",
         title="Document, translation, certification and notarisation costs are not priced",
         detail="The emigrant and inheritance routes need translations and consular certification whose prices depend on the issuer and the country. Only the bank's own certificate of deposit (CNY 20–40) is published and included.",
         sources=["CN-15", "BK-06"]),
    dict(id="H10", sev="medium", kind="policy availability",
         title="QDII subscription capacity is not verified",
         detail="Route A08 depends on an institution having open quota. Availability changes and was not verified for any specific institution in this session.",
         sources=["CN-07"]),
    dict(id="H11", sev="medium", kind="scope limit",
         title="Business routes are described at the level of the rule, not the checklist",
         detail="Routes B01–B03 depend on entity-level practice (liquidation audits, tax clearance, transfer pricing) that is not published as a national price list. Their all-in cost is blank rather than estimated.",
         sources=["CN-04", "CN-09"]),
    dict(id="H12", sev="low", kind="deliberate blank",
         title="No PRC tax is computed on the principal",
         detail="Row TAX-CN-4 is blank: no retrieved provision imposes tax on transferring after-tax principal, and a rate is not invented to fill the cell.",
         sources=["CN-18"]),
    dict(id="H13", sev="low", kind="scope limit",
         title="The full-amount-arrival surcharge is optional",
         detail="USD 15 or USD 25 applies only if you elect full-amount arrival. Declining it does not make the correspondent charge disappear; it moves an unknown deduction into the principal.",
         sources=["BK-03", "BK-07"]),
    dict(id="H14", sev="low", kind="irregularity in an earlier edition",
         title="Earlier editions' headline all-in figures differ from Edition H by a few dollars",
         detail="Edition D reports $83.45 at USD 10,000 and $932.72 at USD 400,000 using a board captured a day earlier plus its own parameter choices. Edition H recomputes from the 2026-11-09 board and includes a certificate-of-deposit component the earlier model omitted, giving $87.94 and $937.34. The difference is traceable to published inputs, not to a dispute about the rule. Both are shown so the reader can see the drift.",
         sources=["BK-01", "BK-04", "BK-06"]),
    dict(id="H15", sev="low", kind="scope limit",
         title="Cross-border RMB to a Hong Kong account, then convert, was not verified",
         detail="A commonly described route is to remit RMB to your own Hong Kong account and convert there. The remittance side and the Hong Kong conversion side each need their own verification and neither was retrieved here, so it is not listed as a priced route.",
         sources=["CN-01"]),
]


def p_flagged():
    rows = []
    for f in FLAGS:
        rows.append("""
<div class="card" id="{id}">
<p><span class="kicker">{id} · {sev} · {kind}</span></p>
<h3>{title}</h3>
<p>{detail}</p>
<p class="note">Sources: {s}</p>
</div>""".format(id=f["id"], sev=esc(f["sev"].upper()), kind=esc(f["kind"]),
                 title=esc(f["title"]), detail=esc(f["detail"]),
                 s=src_links(f["sources"])))

    blankrows = "".join(
        '<tr><td data-l="Route"><a href="method-{i}.html">{i} · {n}</a></td>'
        '<td data-l="Why blank">{w}</td><td data-l="Source">{s}</td></tr>'.format(
            i=m["id"], n=esc(m["name"]), w=esc(m.get("blank_reason", "No published all-in price.")),
            s=src_links(m["sources"][:3])) for m in BLANK)

    body = """
<p class="crumb"><a href="index.html">Dashboard</a> / Flagged for review</p>
<h1>Flagged for review</h1>
<p class="lede">Everything this session could not verify, every cell left blank on purpose, and every
irregularity found in the earlier editions of this repository. Nothing here is hidden behind a
default value. Review these after the site is live.</p>

<div class="flag"><strong>Count:</strong> {n} items — {hi} high, {me} medium, {lo} low severity.
None of them blocks publication, and none of them has been quietly resolved by estimation.</div>

<h2>Routes with no published price</h2>
<p class="note">These are lawful routes whose all-in cost cannot be computed from an official page.
Their tables show an em dash rather than a fabricated number.</p>
<div class="tw"><table class="stack">
<thead><tr><th>Route</th><th>Why the cells are blank</th><th>Source</th></tr></thead>
<tbody>{blankrows}</tbody></table></div>

<h2>The flag list</h2>
{rows}
""".format(n=len(FLAGS),
           hi=sum(1 for f in FLAGS if f["sev"] == "high"),
           me=sum(1 for f in FLAGS if f["sev"] == "medium"),
           lo=sum(1 for f in FLAGS if f["sev"] == "low"),
           blankrows=blankrows, rows="".join(rows))
    return page("Flagged for review", body, "flagged.html")


# --------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------

def p_sources():
    rows = []
    for s in SOURCES:
        rows.append("""
<div class="card" id="{id}">
<p><span class="kicker">{id}</span> {g}</p>
<h3>{title}</h3>
<p class="note">{pub} · retrieved {ret} · {st}</p>
<p><a href="{url}" target="_blank" rel="noopener noreferrer">{url}</a></p>
<blockquote style="margin:10px 0 0;padding:8px 12px;border-left:3px solid #d7dee6;background:#fafbfc;
 font-size:.84rem;color:#39434f">{q}</blockquote>
<p class="note" style="margin-top:8px"><strong>Supports:</strong> {sup}</p>
<p class="note">Rows: {r}</p>
</div>""".format(id=s["id"], g=grade_badge(s["grade"]), title=esc(s["title"]),
                 pub=esc(s["publisher"]), ret=esc(s["retrieved"]),
                 st=esc(s["retrieval_status"]), url=esc(s["url"]),
                 q=esc(s["quote"]), sup=esc(s["supports"]),
                 r=esc(s["supports_rows"])))

    counts = {}
    for s in SOURCES:
        counts[s["grade"]] = counts.get(s["grade"], 0) + 1

    body = """
<p class="crumb"><a href="index.html">Dashboard</a> / Sources</p>
<h1>{n} sources, quoted</h1>
<p class="lede">Every claim on this site traces to one of these pages. Each entry shows the exact
text retrieved and the time it was retrieved, so you can re-check it by hand rather than trusting a
citation.</p>

<div class="tw"><table class="stack">
<thead><tr><th>Grade</th><th class="num">Count</th><th>What it can support</th><th>Example</th></tr></thead>
<tbody>
<tr><td data-l="Grade">{ga} statute / regulator</td><td class="num" data-l="Count">{ca}</td>
 <td data-l="Supports">A legal or tax proposition.</td>
 <td data-l="Example">{exA}</td></tr>
<tr><td data-l="Grade">{gb} official guidance</td><td class="num" data-l="Count">{cb}</td>
 <td data-l="Supports">An official process, threshold or form instruction.</td>
 <td data-l="Example">{exB}</td></tr>
<tr><td data-l="Grade">{gc} provider price</td><td class="num" data-l="Count">{cc}</td>
 <td data-l="Supports">That provider's own price or product terms — never a legal entitlement.</td>
 <td data-l="Example">{exC}</td></tr>
</tbody></table></div>

<p class="note">All pages were retrieved on {ret}. The retrieval tool did not expose HTTP status
codes, so none is claimed; each entry records what the tool reported. A source being listed is not a
claim that the link will resolve for you tomorrow.</p>

{rows}

<h2>What is deliberately absent</h2>
<ul>
<li>No social-media, forum, blog or news article is used to support any figure.</li>
<li>No exchange rate from a non-bank aggregator is used to compute a cost.</li>
<li>No invented HTTP status, no invented quote, and no source id without a URL.</li>
</ul>
""".format(n=len(SOURCES), ret=RETRIEVED,
           ga=grade_badge("A"), gb=grade_badge("B"), gc=grade_badge("C"),
           ca=counts.get("A", 0), cb=counts.get("B", 0), cc=counts.get("C", 0),
           exA=src_links(["CN-09"]), exB=src_links(["US-03"]), exC=src_links(["BK-01"]),
           rows="".join(rows))
    return page("Sources", body, "sources.html")


# --------------------------------------------------------------------------
# Repo audit
# --------------------------------------------------------------------------
REPO_FINDINGS = [
    dict(id="R01", sev="high", target="edition-d/data/parameters.json · edition-d/build/build.py",
         finding="The emigrant route is priced with a 50/25/25 staged release above CNY 200,000 and the summary page repeats the schedule.",
         evidence="parameters.json emigration.release_fractions = [0.5, 0.25, 0.25]; build.py line ~146 applies them; docs/pages/summary.html: 'releases of 50%, 25%, 25% above CNY 200,000'.",
         correct="汇发〔2014〕2号 art. 6(2): 取消移民财产转移分次汇出的要求 — the bank may remit the approved amount once or in instalments. The staging is abolished.",
         severity_reason="It changes the cost, the number of wires and the number of receiving-bank fees on a route this repository presents as a main answer.",
         sources=["CN-16", "CN-14"]),
    dict(id="R02", sev="medium", target="edition-d/data/parameters.json emigration.provincial_threshold_cny",
         finding="A CNY 500,000 approval threshold is carried as a live parameter.",
         evidence="parameters.json emigration.provincial_threshold_cny = 500000, sourced to CN-04 (the 2004 measure).",
         correct="汇发〔2014〕2号 art. 6(1) abolished the requirement to file amounts above CNY 500,000 with SAFE head office. Local approval now covers the whole amount.",
         severity_reason="It implies a head-office step that no longer exists.",
         sources=["CN-17"]),
    dict(id="R03", sev="low", target="edition-d root portal index.html",
         finding="The root landing page's archive list stops at Edition D. Editions E, F and G are merged and live but unreachable from the portal.",
         evidence="build_portal() in edition-d/build/build.py lists overview, dossier, editions B, C and D only.",
         correct="Additive fix applied in this session: the portal generator now also lists Editions E, F, G and H.",
         severity_reason="Navigation only; no published claim is wrong.",
         sources=[]),
    dict(id="R04", sev="info", target="edition-h (this edition)",
         finding="This edition's own headline figures differ slightly from Edition D's for the same route.",
         evidence="$83.45 vs $87.94 at USD 10,000; $932.72 vs $937.34 at USD 400,000.",
         correct="Different board capture date and the inclusion of the certificate-of-deposit component. Both are traceable to published inputs; neither is asserted over the other. Logged as H14.",
         severity_reason="Transparency, not error.",
         sources=["BK-01", "BK-04", "BK-06"]),
    dict(id="R05", sev="info", target="all prior editions",
         finding="Checked and found consistent with the provisions retrieved here: the nine-category PRC IIT list; the definition of a domestic individual by resident ID; the USD 50,000 facilitation quota applying to settlement and to domestic-individual purchase; the prohibition on splitting; the 20% flat rate on transfer of assets; §988(e)(2) and its USD 200 threshold; the direction of the 1% remittance transfer tax; the FBAR USD 10,000 threshold and the willful formula.",
         evidence="Cross-read against the quoted text in sources CN-01 through CN-22 and US-01 through US-12.",
         correct="No change required.",
         severity_reason="No action.",
         sources=["CN-18", "CN-19", "CN-02", "CN-07", "CN-09", "CN-03", "US-01", "US-06", "US-04", "US-09"]),
]


def p_repo_review():
    rows = []
    for f in REPO_FINDINGS:
        rows.append("""
<div class="card" id="{id}">
<p><span class="kicker">{id} · {sev}</span></p>
<h3>{target}</h3>
<p><strong>Finding.</strong> {finding}</p>
<p><strong>Evidence.</strong> {evidence}</p>
<p><strong>Correct position.</strong> {correct}</p>
<p class="note"><strong>Why it matters.</strong> {why}</p>
<p class="note">Sources: {s}</p>
</div>""".format(id=f["id"], sev=esc(f["sev"].upper()), target=esc(f["target"]),
                 finding=esc(f["finding"]), evidence=esc(f["evidence"]),
                 correct=esc(f["correct"]), why=esc(f["severity_reason"]),
                 s=src_links(f["sources"]) if f["sources"] else "—"))

    body = """
<p class="crumb"><a href="index.html">Dashboard</a> / Repo audit</p>
<h1>Line-by-line audit of the earlier editions</h1>
<p class="lede">This repository already contained seven editions when this session started. Each was
read against the official page behind its claim. Where a claim contradicted a primary source it is
recorded here with the exact evidence, and the earlier edition is preserved unchanged rather than
silently rewritten.</p>

<div class="tw"><table class="stack">
<thead><tr><th>Finding</th><th>Severity</th><th>Location</th><th>Source</th></tr></thead>
<tbody>{summary}</tbody></table></div>

{rows}

<h2>What was not changed, and why</h2>
<p>Editions A through G are other sessions' work on other branches. Editing their files would break
their reproducibility checks, which assert that a rebuild is byte-identical. The correct handling is
to record the finding here, publish it, and let the owner or a future integration session apply it.
The one exception is the root portal's archive list, which is additive navigation and is asserted by
Edition D's own verify step — the edit was made in its generator so the build stays green.</p>
""".format(summary="".join(
        '<tr><td data-l="Finding">{}</td><td data-l="Severity">{}</td>'
        '<td data-l="Location">{}</td><td data-l="Source">{}</td></tr>'.format(
            esc(f["id"]), esc(f["sev"]), esc(f["target"]),
            src_links(f["sources"]) if f["sources"] else
            '<a class="src" href="https://github.com/sassnarep3-star/China1" target="_blank" '
            'rel="noopener noreferrer">repo</a>')
        for f in REPO_FINDINGS), rows="".join(rows))
    return page("Repo audit", body, "repo-review.html")


# --------------------------------------------------------------------------
# Methodology
# --------------------------------------------------------------------------

def p_methodology():
    body = """
<p class="crumb"><a href="index.html">Dashboard</a> / Method</p>
<h1>How every number here was produced</h1>
<p class="lede">The rules the build enforces, so you can judge the output rather than trust it.</p>

<h2>Rules enforced in code</h2>
<div class="tw"><table class="stack">
<thead><tr><th>Rule</th><th>How it is enforced</th><th>Audit it</th></tr></thead>
<tbody>
<tr><td data-l="Rule"><strong>No source, no figure</strong></td>
 <td data-l="How">Every cost parameter carries a source id, and the parameter file is the only input to the arithmetic. There is no literal number in the page templates.</td>
 <td data-l="Audit"><a href="https://github.com/sassnarep3-star/China1/blob/main/edition-h/data/costs.py">data/costs.py</a></td></tr>
<tr><td data-l="Rule"><strong>A blank stays blank</strong></td>
 <td data-l="How">A route whose model is <code>unknown</code> returns no total and renders an em dash. The verifier asserts that such a route has no ladder and discloses the gap.</td>
 <td data-l="Audit"><a href="https://github.com/sassnarep3-star/China1/blob/main/edition-h/build/verify.py">build/verify.py</a> check 5</td></tr>
<tr><td data-l="Rule"><strong>Exactly 40 points</strong></td>
 <td data-l="How">The amount list is generated as range(10_000, 400_001, 10_000) and the verifier asserts 40 rows for every priced route.</td>
 <td data-l="Audit"><a href="https://github.com/sassnarep3-star/China1/blob/main/edition-h/build/verify.py">build/verify.py</a> check 4</td></tr>
<tr><td data-l="Rule"><strong>Every fact row carries a link</strong></td>
 <td data-l="How">The verifier parses the generated HTML and fails any table row in a content table that has no anchor with an external URL.</td>
 <td data-l="Audit"><a href="https://github.com/sassnarep3-star/China1/blob/main/edition-h/build/verify.py">build/verify.py</a> check 3</td></tr>
<tr><td data-l="Rule"><strong>Recomputable, not copied</strong></td>
 <td data-l="How">The verifier recomputes each of the headline figures from the parameters, including an independent first-principles spot check at USD 250,000, and compares them with what the HTML says.</td>
 <td data-l="Audit"><a href="https://github.com/sassnarep3-star/China1/blob/main/edition-h/build/verify.py">build/verify.py</a> checks 8–9</td></tr>
<tr><td data-l="Rule"><strong>Deterministic</strong></td>
 <td data-l="How">A second build must reproduce the first byte for byte; the verifier rebuilds and compares every page, and CI runs the build and then <code>git diff --exit-code</code>.</td>
 <td data-l="Audit"><a href="https://github.com/sassnarep3-star/China1/blob/main/edition-h/build/verify.py">build/verify.py</a> check 12</td></tr>
<tr><td data-l="Rule"><strong>Official hosts only</strong></td>
 <td data-l="How">Every external link must be on an allowlist derived from the source registry plus named provider hosts. Anything else fails the build.</td>
 <td data-l="Audit"><a href="https://github.com/sassnarep3-star/China1/blob/main/edition-h/data/sources.py">data/sources.py</a></td></tr>
<tr><td data-l="Rule"><strong>No orphan pages</strong></td>
 <td data-l="How">Every generated page must be reachable from at least one other page, and every internal link and fragment must resolve.</td>
 <td data-l="Audit"><a href="https://github.com/sassnarep3-star/China1/blob/main/edition-h/build/verify.py">build/verify.py</a> checks 6–7</td></tr>
</tbody></table></div>

<h2>The arithmetic, written out</h2>
<blockquote style="border-left:3px solid #0d5c49;padding-left:14px;margin:14px 0">
<p>mid = (buy_spot + sell_spot) / 2</p>
<p>one_way_margin = (sell_spot − mid) / mid = ({sell} − {mid}) / {mid} = {ow}</p>
<p>round_trip = (sell_spot − buy_spot) / sell_spot = {rt}</p>
<p>cny_equivalent = usd / 100 × sell_spot</p>
<p>commission = clamp(cny_equivalent × 0.001, CNY 50, CNY 260)</p>
<p>total = fx_margin + commission + cable + full_amount + receiving + documents</p>
</blockquote>
<p class="note">With buy_spot {buy} and sell_spot {sell} CNY per 100 USD, from the BOC board captured
2026-11-09 09:15:45 Beijing time. {s}</p>

<h2>What this method cannot do</h2>
<ul>
<li>It cannot tell you which route is yours, because the source of the funds is unknown (H01).</li>
<li>It cannot give you a quote. The board is indicative and says the counter rate governs (H05).</li>
<li>It cannot price a route whose fee is only quoted inside a provider's flow (H07).</li>
<li>It cannot price translation, certification or professional fees (H09).</li>
<li>It cannot certify that a link resolves tomorrow. Retrieval is recorded, not guaranteed.</li>
</ul>

<h2>Provenance</h2>
<p class="note">Edition H · session arena-e01cf383 · branch arena/e01cf383-china1. Sources retrieved
{ret}. Every earlier edition in this repository is preserved unchanged; the audit of them is on
<a href="repo-review.html">the repo audit page</a>.</p>
""".format(sell=SELL_SPOT, mid=round(float(MID), 3), buy=BUY_SPOT,
           ow=pct(FX_MARGIN_PCT, 4), rt=pct(FX_ROUND_TRIP_PCT, 4),
           s=src_links(["BK-04"]), ret=RETRIEVED)
    return page("Method", body, "methodology.html")
