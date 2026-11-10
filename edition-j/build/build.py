#!/usr/bin/env python3
"""Edition J site generator — deterministic; reads edition-j/data/*.json and writes edition-j/site/."""
import json, math, shutil
from pathlib import Path
from html import escape as e

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
SITE = BASE / "site"

sources = json.loads((DATA / "sources.json").read_text())["sources"]
methods = json.loads((DATA / "methods.json").read_text())["methods"]
model = json.loads((DATA / "model.json").read_text())
flags = json.loads((DATA / "flags.json").read_text())["flags"]
taxrows = json.loads((DATA / "taxes.json").read_text())["rows"]
SRC = {s["id"]: s for s in sources}

BUILT = "2026-11-10"
BOARD = model["fx_board"]
TARIFF = model["boc_tariff"]
TARGETS = model["targets_usd"]
SELL = BOARD["sell_per_usd"]
MID = BOARD["mid_per_usd"]
MARGIN_RATE = (BOARD["spot_sell"] - BOARD["mid"]) / BOARD["mid"]

def usd(x):
    return f"${x:,.2f}"

def cny(x):
    return f"¥{x:,.2f}"

def pct(x):
    return f"{x:.4f}%"

def src_links(ids):
    out = []
    for i in ids:
        s = SRC[i]
        out.append(f'<a class="src" href="{s["url"]}" rel="noopener noreferrer">{i} ↗</a>')
    return " ".join(out)

def shell(title, body):
    nav = (
        '<nav aria-label="Main navigation"><strong>China Money · Edition J</strong>'
        '<a href="index.html">Dashboard</a>'
        '<a href="executive-summary.html">Executive summary</a>'
        '<a href="methods.html">Methods</a>'
        '<a href="steps.html">Step by step</a>'
        '<a href="costs.html">Cost tables</a>'
        '<a href="taxes.html">Tax &amp; penalties</a>'
        '<a href="sources.html">Sources</a>'
        '<a href="flagged.html">Flagged for Review</a>'
        "</nav>"
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta name="description" content="Verified CNY to USD repatriation research: methods, cost tables at $10,000 increments to $400,000, tax and penalty breakdown.">'
        f"<title>{e(title)} · China Money</title>"
        '<link rel="stylesheet" href="assets/style.css"></head><body><main>'
        + nav
        + body
        + '<footer><p>Research, not legal or tax advice. Unknown is not zero. Blank cells are UNVERIFIED, not free. Government sources support rules; provider sources support only their own published prices and terms. All model values are computed at the '
        + e(BOARD['board_time'])
        + ' BOC board snapshot (S07), not an executable quote.</p>'
        + '<p><a href="../../index.html">← Repository portal</a> · '
        + '<a href="../../COORDINATION.md">Coordination record</a> · Built 2026-11-10</p></footer>'
        "</main></body></html>"
    )

def method_row(m):
    tag = "tag-prohib" if m["id"].startswith("P") else ("tag-cond" if "capital" in m["category"] or "Business" in m["category"] or "Provider" in m["category"] else "tag-lawful")
    label = "Prohibited" if m["id"].startswith("P") else ("Conditional" if tag == "tag-cond" else "Lawful route")
    return (
        f'<tr id="{m["id"]}"><td data-label="Method"><a href="#{m["id"]}">{m["id"]}</a> {e(m["name"])}<br>'
        f'<span class="tag {tag}">{label}</span><small>{e(m["category"])}</small></td>'
        f"<td data-label=\"Who can use it\">{e(m['who'])}</td><td data-label=\"Rule & limit\">{e(m['rule'])}</td><td data-label=\"Sources\">{src_links(m['sources'])}</td></tr>"
    )

def wire_costs(target, n):
    margin = target * MARGIN_RATE
    handling = 0.0
    cable = 0.0
    remaining = target
    for _ in range(n):
        chunk = min(50000.0, remaining) if n > 1 else target
        cny_amount = chunk * SELL
        fee = min(max(TARIFF["handling_pct"] * cny_amount, TARIFF["handling_min_cny"]), TARIFF["handling_max_cny"])
        handling += fee
        cable += TARIFF["cable_cny_other"]
        remaining -= chunk
        if remaining <= 0:
            break
    known = margin + (handling + cable) / SELL
    return {"margin": margin, "handling": handling, "cable": cable, "known": known, "n": n}

def page_index():
    kpis = (
        '<div class="kpi">'
        f"<div><b>{usd(400000*MARGIN_RATE + (TARIFF['handling_max_cny']+TARIFF['cable_cny_other'])/SELL)}</b>"
        "<span>known wire cost at $400k one transfer — 0.21% FX margin + capped ¥260 + ¥150 cable (S06/S07)</span></div>"
        f"<div><b>0%</b><span>tax on the conversion itself — China IIT (S09 Art.2) & U.S. §988 (S14)</span></div>"
        f"<div><b>$50,000/yr</b><span>domestic-individual convenience quota (S02 Art.2); documented income routes can exceed it</span></div>"
        f"<div><b>{len(methods)}</b><span>methods reviewed: {sum(1 for m in methods if not m['id'].startswith('P'))} lawful/conditional + {sum(1 for m in methods if m['id'].startswith('P'))} prohibited</span></div>"
        "</div>"
    )
    cards = [
        ("executive-summary.html", "Executive summary", "The direct answer for a US citizen with stuck CNY: what is taxed, what is not, and the ranked routes."),
        ("methods.html", "All methods — pros & cons", f"{len(methods)} routes: documented income, quota, property, trade, provider rails, cash; plus prohibited schemes to avoid."),
        ("steps.html", "Step-by-step procedures", "Exactly what to do, in order, for every lawful route — with the provision to cite."),
        ("costs.html", "Cost tables $10K → $400K", "10 ladders × 40 targets = 400 rows. Verified components priced; unknown components blank + flagged."),
        ("taxes.html", "Tax & penalty breakdown", "Conversion penalty decomposed: FX margin, fees, Chinese IIT, US §988, FBAR/8938, foreign tax credit, remittance tax."),
        ("sources.html", f"{len(sources)} verified sources", "Every row links to the official page it was checked against, with retrieval notes."),
        ("flagged.html", "Flagged for Review", f"{len(flags)} published irregularities and unverified values. Non-blocking."),
    ]
    body = (
        '<p class="pill">Edition J · independently researched and verified 2026-11-10 · no personal data required</p>'
        "<h1>Getting money out of China: what it actually costs — and what is actually taxed</h1>"
        '<p class="lead">For a US citizen holding CNY in a Chinese bank account, <strong>the FX conversion itself is not taxed in either country</strong>. The real costs are (1) the FX margin and wire fees you can compare, (2) any Chinese income tax that was never paid on the underlying money, and (3) US filing duties (FBAR, Form 8938, §988). The cheapest lawful route depends on one question: <strong>how was the money earned and what documents prove it?</strong></p>'
        '<div class="notice"><strong>Most important — read first:</strong> Do not try to optimize the FX rate before you know which route you are eligible for. A bank will first ask for transaction-amount proof and tax records (S01 Art.7, S02 Art.12–13, S08). If you can document the source, use the matching documented route — entitlement is the product. If you cannot, the $50k/year convenience quota (S02 Art.2) is the only simple lawful channel; splitting across relatives or using underground/crypto is prohibited (S01 Art.7, S08, S21) and carries criminal/penalty risk.</div>'
        '<div class="good"><strong>Bottom line on tax penalties:</strong> There is no single “40% conversion tax.” China IIT is on the original income categories (salary 3–45%, dividends/asset gains 20% per S09 Art.3) — not on converting. The US taxes worldwide income (IRS S15) but gives a foreign tax credit (S15) for qualifying Chinese taxes; mixing up the two systems creates the “considerable tax” fear. The FX move itself can create a small §988 gain only if CNY appreciated after you received it, and personal gains ≤$200 per transaction are excluded (S14 §988(e)(2)). FBAR/8938 are reporting, not extra tax.</div>'
        + kpis
        + '<div class="cards">'
        + "".join(f'<a class="card" href="{h}"><strong>{t} →</strong><p>{d}</p></a>' for h, t, d in cards)
        + "</div>"
        "<h2>The decision in seven rows — most important first</h2>"
    )
    decisions = [
        ("1 · Documented income (esp. foreign individual)", "Lawful current-account RMB income — salary, services, royalties — can be bought into FX and remitted with ID, transaction-amount proof and tax vouchers (S01 Art.13, S02 Art.13). No annual USD ceiling is stated in the rule text for foreign individuals.", ["S01", "S02"]),
        ("2 · Domestic individual, routine amounts", "USD 50k per calendar year on ID alone (S02 Art.2). Above that, same income converts with full documents (S02 Art.12).", ["S02", "S08"]),
        ("3 · Property sale proceeds", "Settle Chinese tax, get the tax voucher, and (if >$50k) the external-payment filing form, then buy FX and remit (S05, S02).", ["S05", "S01"]),
        ("4 · Pre-emigration / inheritance", "SAFE approval route (PBOC 2004 + S03 §VI 2014 reforms removed forced staged remittance and notarization). Own-account remittance only.", ["S03", "S04"]),
        ("5 · Real business flows", "Personal foreign-trade settlement accounts and company profit remittances have no quota ceiling for genuine transactions (S02 Art.9, S03 §V).", ["S02", "S03"]),
        ("6 · Tax & filing", "Conversion ≠ new tax. Pay/document underlying tax once, claim US foreign tax credit (Form 1116, S15), keep §988 FX gains ≤$200 or report them (S14), file FBAR/8938 on time (S10,S11).", ["S09", "S14", "S15", "S10", "S11"]),
        ("7 · What never to do", "Structuring across relatives, underground banking, false trade docs, crypto cash-out and quota misuse are prohibited — risk information only, no execution steps (S01,S08,S21).", ["S01", "S08", "S21"]),
    ]
    rows = "".join(f"<tr><td data-label=\"Priority\">{e(t)}</td><td data-label=\"What the sources support\">{e(d)}</td><td data-label=\"Source\">{src_links(s)}</td></tr>" for t, d, s in decisions)
    body += (
        '<div class="scroll"><table class="responsive"><thead><tr><th>Priority</th><th>What the verified sources support</th><th>Source</th></tr></thead><tbody>'
        + rows
        + "</tbody></table></div>"
    )
    body += "<h2>Known wire cost at key amounts — single transfer, verified components only</h2>"
    body += (
        f"<p>Model at the {BOARD['board_time']} BOC board (S07): one-way FX margin {pct(MARGIN_RATE*100)} vs board midpoint (S07 spot sell 669.03, midpoint 667.625); BOC handling 0.1% (¥50–¥260 cap) + ¥150 cable (S06). Receiving-bank, intermediary and tax columns are <strong>blank = UNVERIFIED</strong> (F03–F06). <a href=\"costs.html\">Full 40-target ladders →</a></p>"
    )
    ex_rows = ""
    for t in [10000, 50000, 100000, 200000, 400000]:
        m = wire_costs(t, 1)
        ex_rows += (
            f'<tr><td class="num" data-label="Target">{usd(t)}</td><td class="num" data-label="Known subtotal"><strong>{usd(m["known"])}</strong></td>'
            f'<td class="num" data-label="% of target">{pct(m["known"]*100/t)}</td><td class="num" data-label="FX margin">{usd(m["margin"])}</td>'
            f'<td class="num" data-label="Handling + cable">{cny(m["handling"])} + {cny(m["cable"])}</td>'
            f'<td class="blank" data-label="Receiving bank">⚠ UNVERIFIED</td><td class="blank" data-label="Taxes">⚠ UNVERIFIED</td>'
            f"<td data-label=\"Source\">{src_links(['S06','S07'])}</td></tr>"
        )
    body += (
        '<div class="scroll"><table class="responsive costs sticky-first"><thead><tr><th>Target</th><th>Known subtotal</th><th>%</th><th>FX margin</th><th>Handling + cable</th><th>Receiving bank</th><th>Taxes</th><th>Source</th></tr></thead><tbody>'
        + ex_rows
        + "</tbody></table></div>"
        '<div class="notice"><strong>How to read the 0.21%:</strong> BOC posts two prices (buy/sell). The midpoint is (669.03+666.22)/2 = 667.625 (S07). The one-way cost you pay over midpoint on a single conversion is (669.03-667.625)/667.625 = 0.2104%. The “0.42%” you may see elsewhere is the round-trip buy-then-sell spread — double-counting for one transfer. Fees are capped, so % falls as amount rises: 0.53% at $10k → 0.23% at $400k.</div>'
    )
    return shell("Dashboard", body)

def page_executive_summary():
    body = (
        "<h1>Executive summary — stuck CNY, least tax friction</h1>"
        '<p class="lead">You asked: as a US citizen with money stuck in a China bank account, what is the cheapest way to convert CNY to USD with the least tax penalties? This page answers that directly, with every claim linked to an official source.</p>'
        '<div class="good"><strong>Short answer in one paragraph:</strong> The wire itself is not the taxed event. China taxes the <em>original income</em> by category (S09 Art.2), the US taxes worldwide income (IRS S15 note) but lets you credit qualifying Chinese income taxes (S15). So the least-tax route is not a clever FX trick — it is the documented route whose required tax paperwork you can already satisfy for the provenance of this specific balance. Compare executable quotes for that route only.</div>'
        '<h2>Why it feels like a “huge conversion tax”</h2>'
        '<ul><li><strong>China side:</strong> IIT Law (S09) lists nine taxable categories — salary, services, dividends, asset transfers, etc. — each with its own rate (comprehensive 3–45%, business 5–35%, flat 20% for dividends/asset sales per Art.3). FX conversion is not a category. If salary was paid net of tax via payroll, IIT is already settled and the bank will want that tax voucher (S02 Art.10 requires “tax proof” for service income). If it was cash/under-reported savings, the IIT is still due and the bank review will stall without it.</li>'
        '<li><strong>US side:</strong> US citizens report worldwide income (S15). Moving already-taxed principal is not new income, but interest, dividends, gains, gifts and currency appreciation each have separate character. §988 (S14) treats personal FX gains &gt;$200 per transaction as ordinary income; the rest of the principal is not double-taxed — Form 1116 credit (S15) reduces US tax by qualifying Chinese taxes, subject to limitation.</li>'
        '<li><strong>Fees vs tax:</strong> What you see on the wire advice (BOC ¥50–260 + ¥150 cable, 0.21% margin) is a few hundred dollars even at $400k (S06/S07). That is not the “considerable tax” — the tax is on the underlying earning, not the wire.</li></ul>'
        '<h2>Ranked routes — match the source of funds</h2>'
        '<div class="scroll"><table class="responsive"><thead><tr><th>Rank</th><th>Route</th><th>When it is cheapest</th><th>Why not always</th><th>Source</th></tr></thead><tbody>'
        '<tr><td data-label="Rank">1</td><td data-label="Route">Documented foreign-individual income (M01/M14)</td><td data-label="When">You have pay slips, contract and tax receipts for salary/services performed in China (S02 Art.13 “含税务凭证”)</td><td data-label="Why not">Only covers documented amounts; each FX purchase needs the paper trail</td><td data-label="Source">' + src_links(["S01","S02"]) + '</td></tr>'
        '<tr><td data-label="Rank">2</td><td data-label="Route">Annual $50,000 convenience quota (M02)</td><td data-label="When">Small leftover savings, no deep documentation, and you can wait one calendar year per $50,000 chunk (S02 Art. 2)</td><td data-label="Why not">Above $50,000/yr requires documents anyway; splitting across relatives is banned (S08)</td><td data-label="Source">' + src_links(["S02","S08"]) + '</td></tr>'
        '<tr><td data-label="Rank">3</td><td data-label="Route">Property / vehicle / securities proceeds (M04)</td><td data-label="When">You actually sold an onshore asset and have transfer + tax filing form (S05)</td><td data-label="Why not">Fake sales are fraud (P03); capital-gains IIT 20% (S09) still applies</td><td data-label="Source">' + src_links(["S05","S09"]) + '</td></tr>'
        '<tr><td data-label="Rank">4</td><td data-label="Route">Emigration / inheritance approval (M05/M06)</td><td data-label="When">You are emigrating permanently or inheriting — 2014 reforms allow one or staged remittances within approval (S03 §VI)</td><td data-label="Why not">Needs household-registration, tax clearance, SAFE approval; not for routine savings</td><td data-label="Source">' + src_links(["S03","S04"]) + '</td></tr>'
        '<tr><td data-label="Rank">5</td><td data-label="Route">Trade / company profit (M07/M12)</td><td data-label="When">Real business; profit remittance via tax filing form (S03 §V)</td><td data-label="Why not">Cannot relabel personal savings as trade; corporate tax + withholding come first</td><td data-label="Source">' + src_links(["S02","S03"]) + '</td></tr>'
        "</tbody></table></div>"
        "<h2>What to do Monday morning — step order</h2>"
        "<ol>"
        "<li><strong>Classify the balance:</strong> salary vs asset sale vs inheritance vs savings. Each has its own document set (S02 Art.10 list: contracts, income proof, tax vouchers; S05 checklist for property; S03 §VI for emigration).</li>"
        "<li><strong>Gather tax vouchers:</strong> Chinese IIT receipts for that income. Those reduce US tax via Form 1116 (S15) — the legitimate way to cut ‘tax penalties’.</li>"
        "<li><strong>Ask the Chinese bank for the lawful procedure for that classification:</strong> which SAFE article, which forms, what FX rate they actually execute (not the board snapshot).</li>"
        "<li><strong>Get two executable quotes for the same CNY debit:</strong> BOC and HSBC published tariffs (S06, HSBC S18) are the only verified fixed-fee numbers; Wise from-CNY needs an in-app quote (S17). Compare net USD credited, not headline fee.</li>"
        "<li><strong>Retain the audit trail:</strong> slips, tax vouchers, SAFE approval, FX tickets — needed for FBAR/8938 and §988 basis (S10,S11,S14).</li>"
        "</ol>"
        '<div class="notice"><strong>The one number everyone wants but no source will give:</strong> “total all-in cost for my case.” Every advisor who quotes one without seeing your income source, tax history, and receiving-bank fee schedule is guessing. This dashboard leaves those cells visibly <strong>blank + UNVERIFIED</strong> and tells you which documents would fill each one.</div>'
    )
    return shell("Executive summary", body)

def page_methods():
    cats = {}
    for m in methods:
        cats.setdefault(m["category"], []).append(m)
    body = "<h1>All methods — with pros and cons and who they are for</h1>"
    body += '<p class="lead">Every lawful method has the same core requirement: a genuine underlying transaction and the documents to prove it. That is SAFE’s authenticity principle (S01 Art.7). Prohibited methods are listed only with risk information — no execution steps — so you know what to avoid.</p>'
    body += '<div class="scroll"><table class="responsive"><thead><tr><th>Method</th><th>Who can use it</th><th>Rule & limit</th><th>Sources</th></tr></thead><tbody>'
    for m in methods:
        body += method_row(m)
    body += "</tbody></table></div>"
    body += "<h2>Pros and cons — read before you pick</h2>"
    for m in methods:
        tag = "tag-prohib" if m["id"].startswith("P") else ("tag-cond" if "capital" in m["category"] or "Business" in m["category"] or "Provider" in m["category"] else "tag-lawful")
        label = "Prohibited" if m["id"].startswith("P") else ("Conditional" if tag == "tag-cond" else "Lawful route")
        body += f'<div class="flag" id="procon-{m["id"]}"><h3>{m["id"]}: {e(m["name"])} <span class="tag {tag}">{label}</span></h3><p><strong>Rule:</strong> {e(m["rule"])}</p><p><strong>Docs typically required:</strong> {e(", ".join(m.get("docs", [])) or "—")}</p>'
        if m.get("pros"):
            body += "<p><strong>Pros:</strong></p><ul>" + "".join(f"<li>{e(p)}</li>" for p in m["pros"]) + "</ul>"
        if m.get("cons"):
            body += "<p><strong>Cons / limits:</strong></p><ul>" + "".join(f"<li>{e(c)}</li>" for c in m["cons"]) + "</ul>"
        if m.get("steps"):
            if m.get("cost_ladder"):
                body += f'<p><a href="steps.html#{m["id"]}">See step-by-step →</a> &nbsp; <a href="costs.html#{e(m["cost_ladder"])}">See cost ladder {e(m["cost_ladder"])} →</a></p>'
            else:
                body += f'<p><a href="steps.html#{m["id"]}">See step-by-step →</a></p>'
        else:
            body += '<p><em>No execution steps — risk information only.</em></p>'
        body += f'<p><small>Sources: {src_links(m["sources"])}</small></p></div>'
    return shell("Methods with pros & cons", body)

def page_steps():
    body = "<h1>Step-by-step procedures — exactly how each lawful route works</h1>"
    body += '<p class="lead">Follow the steps in order. Every step cites the provision that requires it. If a step seems missing for your case, that is the flag to ask the handling bank — do not improvise a workaround.</p>'
    for m in methods:
        if not m.get("steps"):
            continue
        ladder = m.get("cost_ladder")
        body += f'<div class="flag" id="{m["id"]}"><h3>{m["id"]}: {e(m["name"])}</h3>'
        body += f'<p><strong>Category:</strong> {e(m["category"])} &nbsp; <span class="tag tag-lawful">Lawful route</span></p>'
        body += f'<p><strong>Who:</strong> {e(m["who"])}</p><p><strong>Rule:</strong> {e(m["rule"])}</p>'
        body += "<ol>" + "".join(f"<li>{e(s)}</li>" for s in m["steps"]) + "</ol>"
        if ladder:
            body += f'<p><a href="costs.html#{ladder}">Cost ladder {e(ladder)} — $10k→$400k →</a></p>'
        body += f'<p><small>Sources: {src_links(m["sources"])} &nbsp; Docs: {e(", ".join(m.get("docs", [])) or "per bank checklist")}</small></p></div>'
    body += '<div class="notice"><strong>What about the 6 prohibited methods?</strong> They have no steps in this dashboard. Each is listed on the <a href="methods.html">methods page</a> with the specific prohibition (S01 Art.7 false vouchers & splitting; S08 lending quota / underground banking; S21 crypto ban). Knowing <em>why</em> they are banned is the service; reproducing them is not.</div>'
    return shell("Step by step", body)

def page_costs():
    body = (
        "<h1>Cost tables — $10,000 to $400,000 in $10,000 steps</h1>"
        '<p class="lead">Most important first: the <strong>Known subtotal</strong> column is every component you can verify from a published tariff. Receiving-bank, intermediary and tax columns are <strong>blank = UNVERIFIED</strong> on purpose — no source supports filling them generically. Never read a blank as zero.</p>'
        f'<div class="good"><strong>Model snapshot:</strong> BOC board {BOARD["board_time"]} (S07) — spot sell ¥{BOARD["spot_sell"]} per $100 ⇒ ¥{SELL}/$1; midpoint ¥{BOARD["mid"]} ⇒ one-way margin {pct(MARGIN_RATE*100)} vs midpoint. BOC tariff (S06) 0.1% min ¥{TARIFF["handling_min_cny"]} max ¥{TARIFF["handling_max_cny"]} + ¥{TARIFF["cable_cny_other"]} cable. Every figure below is recomputed from those two sources and verified in <code>verify.py</code>.</div>'
        '<p>Three distinct fee profiles are priced (single-wire, $50k-chunked quota, and cross-reference HSBC tariffs in the integration portal). Wise fees are quote-time only (S17) — no fixed table exists — and card/cash/crypto routes have no verified official price schedule; those ladders show all money cells blank+flagged.</p>'
    )
    for lid, lad in model["ladders"].items():
        priced = lad["priced"]
        body += f'<h2 id="{lid}">{e(lad["label"])} — {e(lid)}</h2>'
        body += f'<p><em>Transfers:</em> {e(lad["transfers"])}'
        if lad.get("priced_note"):
            body += f' — {e(lad["priced_note"])}'
        body += "</p>"
        # table header: most important first
        body += '<div class="scroll"><table class="responsive costs sticky-first"><thead><tr><th>USD target</th><th>Known subtotal</th><th>% of target</th><th>FX margin</th><th>Handling + cable</th><th>Receiving bank</th><th>Intermediary</th><th>Taxes</th><th>Source</th></tr></thead><tbody>'
        for target in TARGETS:
            if priced:
                n = math.ceil(target / 50000) if lid == "L2" else 1
                c = wire_costs(target, n)
                handling_cny = c["handling"]
                cable_cny = c["cable"]
                body += (
                    f'<tr><td class="num" data-label="USD target"><strong>{usd(target)}</strong></td>'
                    f'<td class="num" data-label="Known subtotal"><strong>{usd(c["known"])}</strong></td>'
                    f'<td class="num" data-label="% of target">{pct(c["known"]*100/target)}</td>'
                    f'<td class="num" data-label="FX margin">{usd(c["margin"])}</td>'
                    f'<td class="num" data-label="Handling + cable">{cny(handling_cny)} + {cny(cable_cny)}</td>'
                    f'<td class="blank" data-label="Receiving bank">⚠ UNVERIFIED</td><td class="blank" data-label="Intermediary">⚠ UNVERIFIED</td><td class="blank" data-label="Taxes">⚠ UNVERIFIED</td>'
                    f'<td data-label="Source">{src_links([lad["fee_source"], lad["fx_source"]])}</td></tr>'
                )
            else:
                # unpriced: all money cells blank
                body += (
                    f'<tr><td class="num" data-label="USD target"><strong>{usd(target)}</strong></td>'
                    f'<td class="blank" data-label="Known subtotal">⚠ UNVERIFIED</td><td class="blank" data-label="% of target">⚠ UNVERIFIED</td>'
                    f'<td class="blank" data-label="FX margin">⚠ UNVERIFIED</td><td class="blank" data-label="Handling + cable">⚠ UNVERIFIED</td>'
                    f'<td class="blank" data-label="Receiving bank">⚠ UNVERIFIED</td><td class="blank" data-label="Intermediary">⚠ UNVERIFIED</td><td class="blank" data-label="Taxes">⚠ UNVERIFIED</td>'
                    f'<td data-label="Source">{src_links([x for x in [lad.get("fee_source"), lad.get("fx_source")] if x]) if lad.get("fee_source") else src_links([lad.get("fx_source")]) if lad.get("fx_source") else e(lad.get("priced_note") or "")}</td></tr>'
                )
        body += "</tbody></table></div>"
        body += f'<p><small>Sources: {src_links([lad["fee_source"], lad["fx_source"]] if priced else [x for x in [lad.get("fee_source"), lad.get("fx_source")] if x]) if any([lad.get("fee_source"), lad.get("fx_source")]) else ""} · Blanks = F03–F06 (receiving/intermediary/tax unknown) · Model verified by independent Decimal recomputation in <code>verify.py</code>.</small></p>'
    body += '<div class="notice"><strong>How to use this to comparison-shop:</strong> For the same CNY debit, request the <em>net USD credited</em> from each eligible provider at the same timestamp. Effective cost = (CNY debited ÷ USD credited) − market mid — lower is better. Do not add a “sender fee” ladder to a “property entitlement” ladder; entitlement establishes <em>whether</em> you may remit, the rail determines the price of the wire.</div>'
    body += '<p><a href="../../integration/costs.html">Compare with HSBC P/A published tariff (integration portal) →</a> · <a href="../../edition-h/site/costs.html">Historical 1,720-row grid (43 methods, 2026-11-09 rate) →</a></p>'
    return shell("Cost tables $10K→$400K", body)

def page_taxes():
    body = (
        "<h1>Tax &amp; penalty breakdown — the “conversion penalty” is three separate things</h1>"
        '<p class="lead">If you fear a single huge “conversion tax,” you are adding together three different liabilities that the sources keep separate. This page splits them so you can address each with the right evidence.</p>'
        '<div class="scroll"><table class="responsive"><thead><tr><th>Item</th><th>Finding (verified)</th><th>Amount</th><th>Source</th></tr></thead><tbody>'
    )
    for r in taxrows:
        amount = f'<span class="num">{e(r["amount"])}</span>' if r["amount"] else '<span class="blank">⚠ UNVERIFIED</span>'
        body += (
            f'<tr id="{r["id"]}" data-label="Row"><td data-label="Item">{e(r["id"])} · {e(r["jurisdiction"])}<br><strong>{e(r["item"])}</strong></td>'
            f"<td data-label=\"Finding\">{e(r['finding'])}</td><td data-label=\"Amount\">{amount}<br><small>{e(r['amount_note'])}</small></td>"
            f"<td data-label=\"Source\">{src_links(r['sources'])}</td></tr>"
        )
    body += "</tbody></table></div>"
    body += (
        '<h2>1 · The FX spread is not a tax — it is the bank’s price</h2>'
        f'<p>At the {BOARD["board_time"]} snapshot (S07), BOC posts buy 666.22 / sell 669.03 per $100. Midpoint 667.625 is the reference. Your one-way cost over midpoint is (669.03−667.625)/667.625 = 0.2104% (S07). Add BOC handling 0.1% capped at ¥260 + ¥150 cable (S06) and the known cost at $400k is just under $1k — not a “40% tax”.</p>'
        '<h2>2 · Chinese IIT is on the <em>earning</em>, not the wire</h2>'
        '<p>IIT Law Art.2 (S09) taxes salary, services, dividends, asset transfers, etc. — conversion is not listed. Art.3 sets rates: comprehensive income 3–45% progressive; business 5–35%; flat 20% for interest/dividends, leasing, asset transfer, incidental. If your balance is salary already net-taxed via payroll, the IIT is already paid and the bank wants that voucher (S02 Art.10/13). If it is untaxed savings or an undeclared gain, that IIT is the “penalty” that must be settled before SAFE/bank will let it through (S03 §VI, S05 checklist).</p>'
        '<h2>3 · US worldwide income &amp; FX gain — separate from the wire fee</h2>'
        '<p>US citizens report worldwide income (IRS S15). Already-taxed principal moved to the US is <em>not</em> new income, but you must characterize interest, dividends, gains, gifts and currency gains separately. §988 (S14) taxes personal FX gains &gt;$200 per transaction as ordinary income; personal losses are disallowed and personal transactions ≤$200 are excluded (S14 §988(e)(2)). Basis is the USD value when you received the CNY (S13, S16 practice unit). The foreign tax credit (S15, Form 1116) reduces US tax by qualifying Chinese income taxes — the lawful relief — but cannot be used on excluded foreign-earned income and is limited by category.</p>'
        '<h2>4 · Reporting &amp; penalty exposure — not fees, but real</h2>'
        '<p>FBAR (S10): aggregate foreign accounts &gt;$10k at any point ⇒ FinCEN 114; willful violation up to $100k or 50% of balance. Form 8938 (S11): specified foreign assets &gt;thresholds (e.g. $200k on last day for single expat). Form 3520: gifts from foreign persons &gt;$100k aggregated (S12). Penalties are per-form, per-year and increase with willfulness — they dwarf wire fees, so timely filing is the cheapest “tax” move.</p>'
        '<div class="good"><strong>Least-tax checklist:</strong><ol><li>Document the underlying income and keep Chinese tax receipts → preserves FTC eligibility (S15).</li><li>Use the route whose tax paperwork you can already meet — don’t create a fake asset sale to chase a lower FX fee (P03 is fraud, S01 Art.7).</li><li>Keep §988 gain ≤$200 per wire by timing (S14) or be ready to report it (S13). </li><li>File FBAR/8938/3520 on time (S10–S12) — penalties are the biggest avoidable “penalty”.</li></ol></div>'
        '<h2>5 · What is <em>not</em> a China→US tax</h2>'
        '<ul><li>No general USD 50k gift-tax threshold (S12: foreign-person gift reporting &gt;$100k; 2026 entity purported-gift threshold $20,573 — not a blanket tax).</li>'
        '<li>No universal USD 5k cash exemption — SAFE caps overseas card cash at ¥100k/yr, ¥10k/day (customs S19) and Customs declaration is separate.</li>'
        '<li>The new 1% US remittance excise is on US→abroad wires funded by cash/money orders/cashier’s checks (IRS S22), not China→US.</li>'
        '<li>The PBOC 2021 crypto notice (S18) is repealed by 2026 No.42 (S21) — crypto cash-out is still banned illegal financial activity (S21).</li></ul>'
        '<div class="notice"><strong>This is the breakdown you asked for:</strong> FX 0.21% margin + ¥50–260/¥150 fees (verified, S06/S07) vs Chinese IIT 3–45% or 20% on the original earning (S09) vs US tax reduced by FTC on that same earning (S15) vs §988 FX gain &gt;$200 (S14) vs FBAR/8938/3520 penalties (S10–S12). Which of those actually applies depends on the undocumented facts in flag F01 — so none is filled in as your personal number; the table tells you which evidence would decide each one.</div>'
    )
    return shell("Tax & penalty breakdown", body)

def page_sources():
    body = "<h1>Sources — every row linked to the official page it was verified against</h1>"
    body += '<p class="lead">Government/ regulator sources support law and tax rules. Provider sources (BOC, Wise) support only that provider’s own tariff or product terms. All sources were fetched and read on 2026-11-10; an official page’s availability can change after that date.</p>'
    for s in sources:
        body += f'<div class="flag"><h3>{s["id"]}: {e(s["title"])} <span class="pill">{e(s["kind"])}</span></h3><p>{e(s["supports"])}</p><p><a href="{s["url"]}" rel="noopener noreferrer">{e(s["url"])} ↗</a></p></div>'
    return shell("Sources", body)

def page_flagged():
    body = "<h1>Flagged for Review — what this dashboard deliberately leaves blank</h1>"
    body += '<p class="lead">A blank means “no official source supports a generic fill-in for your case” — never “zero.” Nothing flagged blocks the build; all flags are published here by design.</p>'
    for f in flags:
        body += f'<div class="flag" id="{f["id"]}"><h3>{f["id"]}: {e(f["title"])}</h3><p>{e(f["detail"])}</p><p><small>Blocking: {f["blocking"]} — flagged, not merged as fact.</small></p></div>'
    body += '<div class="notice"><strong>Audit scope:</strong> This edition’s verifier recomputes every priced cell independently from <code>data/model.json</code>, checks byte-identical rebuild, 40-target grid completeness, blank semantics, prohibited-route step prohibition, and internal/external link resolution. Prior editions’ claim sets (e.g. Edition H 1,720 rows) retain their own verifiers and are not re-certified here — flagged as A12 in the edition-i audit and preserved unchanged via the portal.</div>'
    return shell("Flagged for Review", body)

def main():
    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy(BASE / "build" / "style.css", SITE / "assets" / "style.css")
    pages = {
        "index.html": page_index(),
        "executive-summary.html": page_executive_summary(),
        "methods.html": page_methods(),
        "steps.html": page_steps(),
        "costs.html": page_costs(),
        "taxes.html": page_taxes(),
        "sources.html": page_sources(),
        "flagged.html": page_flagged(),
    }
    for name, html in pages.items():
        (SITE / name).write_text(html, encoding="utf-8")
    print(f"Edition J: {len(pages)} pages → {SITE}/")

if __name__ == "__main__":
    main()
