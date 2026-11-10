#!/usr/bin/env python3
"""Edition I site generator — deterministic; reads edition-i/data/*.json and writes edition-i/site/."""
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

BUILT = model["built"]
BOARD = model["fx_board"]
TARIFF = model["boc_tariff"]
TARGETS = model["targets_usd"]
SELL = BOARD["sell_per_usd"]
MID = BOARD["mid_per_usd"]
MARGIN_RATE = (BOARD["spot_sell"] - BOARD["mid"]) / BOARD["mid"]  # (669.03-667.625)/667.625


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
        '<nav aria-label="Main navigation"><strong>China Money · Edition I</strong>'
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
        f'<meta name="description" content="Verified CNY to USD repatriation research: methods, '
        f'cost tables at $10,000 increments to $400,000, tax and penalty breakdown.">'
        f"<title>{e(title)} · China Money</title>"
        '<link rel="stylesheet" href="assets/style.css"></head><body><main>'
        + nav
        + body
        + '<footer><p>Research, not legal or tax advice. Unknown is not zero. Blank cells are UNVERIFIED, '
          "not free. Government sources support rules; provider sources support only their own published "
          f"prices and terms. All model values are computed at the {BOARD['board_time']} BOC board snapshot "
          f"(S07), not an executable quote.</p>"
          '<p><a href="../../index.html">← Repository portal</a> · '
          f'<a href="../../COORDINATION.md">Coordination record</a> · Built {BUILT}</p></footer>'
        "</main></body></html>"
    )


def method_row(m):
    tag = "tag-prohib" if m["id"].startswith("P") else ("tag-cond" if "capital" in m["category"] or "Business" in m["category"] or "Provider" in m["category"] else "tag-lawful")
    label = "Prohibited" if m["id"].startswith("P") else ("Conditional" if tag == "tag-cond" else "Lawful route")
    return (
        f'<tr id="{m["id"]}"><td><a href="#{m["id"]}">{m["id"]}</a> {e(m["name"])}<br>'
        f'<span class="tag {tag}">{label}</span><small>{e(m["category"])}</small></td>'
        f"<td>{e(m['who'])}</td><td>{e(m['rule'])}</td><td>{src_links(m['sources'])}</td></tr>"
    )


def page_index():
    kpis = (
        '<div class="kpi">'
        f"<div><b>{usd(400000*MARGIN_RATE + (TARIFF['handling_max_cny']+TARIFF['cable_cny_other'])/SELL)}</b>"
        "<span>known wire cost at $400,000, one transfer (0.21% FX margin + capped ¥260 + ¥150 cable)</span></div>"
        f"<div><b>0%</b><span>tax on the conversion itself — China and the U.S. (S09, S14)</span></div>"
        f"<div><b>$50,000/yr</b><span>domestic-individual convenience quota (S02 Art. 2); documented income routes can exceed it</span></div>"
        f"<div><b>{len(methods)}</b><span>methods reviewed: {sum(1 for m in methods if not m['id'].startswith('P'))} lawful/conditional, "
        f"{sum(1 for m in methods if m['id'].startswith('P'))} prohibited</span></div>"
        "</div>"
    )
    cards = [
        ("executive-summary.html", "Executive summary", "The direct answer: how to move CNY out with the least tax friction, ranked by source of funds."),
        ("methods.html", "All methods with pros &amp; cons", f"{len(methods)} routes — documented income, quota, property, trade, provider rails, cash — and the prohibited schemes to avoid."),
        ("steps.html", "Step-by-step procedures", "Exactly what to do, in order, for every lawful route."),
        ("costs.html", "Cost tables $10K → $400K", "Ten ladders × 40 targets. Verified components priced; unknown components blank + flagged."),
        ("taxes.html", "Tax &amp; penalty breakdown", "China IIT, U.S. §988, FBAR, Form 8938, foreign tax credit — what is actually taxed and what is not."),
        ("sources.html", f"{len(sources)} verified sources", "Every row links to the official page it was checked against, with retrieval notes."),
        ("flagged.html", "Flagged for Review", f"{len(flags)} published irregularities and unverified values. Non-blocking."),
    ]
    body = (
        '<p class="pill">Edition I · independently researched and verified 2026-11-10 · no personal data required</p>'
        "<h1>Getting money out of China: what it actually costs, and what is actually taxed</h1>"
        '<p class="lead">For a U.S. citizen holding CNY in a Chinese bank account, <strong>the conversion itself '
        "is not taxed in either country</strong>. The friction is (1) FX margin and wire fees, (2) Chinese income "
        "tax on the money if it was never taxed, and (3) U.S. filing duties (FBAR/8938/§988). The fastest lawful "
        "route depends on one question: <strong>how was the money earned and what documents prove it?</strong></p>"
        '<div class="good"><strong>Bottom line:</strong> if the balance is documented (after-tax salary, service '
        "income, sale proceeds), use the matching documented route in the methods table — the paperwork is the "
        "product. If it is undocumented savings, no channel makes it tax-free; the quota route (USD 50,000/year) "
        "is the only simple one. Never split transfers across people or use crypto/underground banking: those are "
        "prohibited and carry criminal risk (S01 Art. 7, S08, S18).</div>"
        + kpis
        + '<div class="cards">'
        + "".join(f'<a class="card" href="{h}"><strong>{t} →</strong><p>{d}</p></a>' for h, t, d in cards)
        + "</div>"
        "<h2>The decision in seven rows</h2>"
    )
    decisions = [
        ("1. Documented income (esp. foreign individual)", "Lawful current-account RMB income can be bought into FX and remitted with ID, proof and tax vouchers; no annual USD ceiling is stated in the rule text for foreign individuals.", ["S01", "S02"]),
        ("2. Domestic individual, routine amounts", "USD 50,000 per calendar year convenience quota on ID alone; above-quota income converts with documents.", ["S02", "S08"]),
        ("3. Property sale proceeds", "Settle the tax, get the tax voucher and (over $50K) the external-payment filing form, then buy FX and remit.", ["S05", "S01"]),
        ("4. Pre-emigration assets / inheritance", "SAFE approval route (emigration or inheritance transfer); 2014 reforms removed forced staged remittance and document notarization.", ["S03", "S04"]),
        ("5. Real business flows", "Personal foreign-trade settlement accounts and company profit remittances have no quota ceiling for genuine transactions.", ["S02", "S03"]),
        ("6. Tax side", "Conversion is untaxed; pay/document the underlying tax once, claim the U.S. foreign tax credit (Form 1116), keep §988 FX gains ≤ $200 per personal transaction or report them, file FBAR/8938 on time.", ["S09", "S14", "S15", "S10", "S11"]),
        ("7. What not to do", "Structuring across relatives, underground banking, false trade documents, crypto cash-out and quota misuse are prohibited — risk information only, no steps published.", ["S01", "S08", "S21"]),
    ]
    rows = "".join(f"<tr><td>{e(t)}</td><td>{e(d)}</td><td>{src_links(s)}</td></tr>" for t, d, s in decisions)
    body += (
        '<div class="scroll"><table class="responsive"><thead><tr><th>Priority</th><th>What the verified sources support</th><th>Source</th></tr></thead><tbody>'
        + rows
        + "</tbody></table></div>"
    )
    # headline ladder excerpt: single-wire known costs at key targets
    body += "<h2>Known wire cost at key amounts (single transfer, verified components only)</h2>"
    body += (
        f"<p>Model at the {BOARD['board_time']} BOC board (S07): one-way FX margin {pct(MARGIN_RATE*100)} vs board "
        f"midpoint; BOC published handling 0.1% (min ¥50, max ¥260) + ¥150 cable (S06). Receiving-bank, "
        "intermediary and tax columns are <strong>blank = UNVERIFIED</strong> (F03–F05). "
        '<a href="costs.html">Full 40-target ladders →</a></p>'
    )
    ex_rows = ""
    for t in [10000, 50000, 100000, 200000, 400000]:
        m = wire_costs(t, 1)
        ex_rows += (
            f'<tr><td class="num">{usd(t)}</td><td class="num"><strong>{usd(m["known"])}</strong></td>'
            f'<td class="num">{pct(m["known"]*100/t)}</td><td class="num">{usd(m["margin"])}</td>'
            f'<td class="num">{cny(m["handling"])} + {cny(m["cable"])}</td>'
            f'<td class="blank">⚠ UNVERIFIED</td><td class="blank">⚠ UNVERIFIED</td>'
            f"<td>{src_links(['S06','S07'])}</td></tr>"
        )
    body += (
        '<div class="scroll"><table class="costs sticky-first"><thead><tr><th>Target</th><th>Known subtotal</th>'
        "<th>%</th><th>FX margin</th><th>Handling + cable</th><th>Receiving bank</th><th>Taxes</th><th>Source</th>"
        "</tr></thead><tbody>"
        + ex_rows
        + "</tbody></table></div>"
    )
    return shell("Dashboard", body)


def wire_costs(target, n):
    """Costs for moving `target` USD in n transfers (last transfer takes the remainder)."""
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
    return {
        "cny_needed": target * SELL,
        "margin": margin,
        "handling": handling,
        "cable": cable,
        "n": n,
        "known": known,
    }


def page_costs():
    body = (
        "<h1>Cost tables — $10,000 to $400,000 in $10,000 steps</h1>"
        '<p class="lead">Most important number first: the <strong>known subtotal</strong> column contains every '
        "component that is priced from a verified published source. Everything else is blank on purpose. "
        "Blank = UNVERIFIED, not zero (F17).</p>"
        f'<div class="notice"><strong>Model basis:</strong> BOC board snapshot {BOARD["board_time"]} (S07): '
        f'sell {BOARD["spot_sell"]} / buy {BOARD["spot_buy"]} CNY per 100 USD; one-way FX margin '
        f"{pct(MARGIN_RATE*100)} vs midpoint {BOARD['mid']}. BOC e-banking cross-border TT tariff (S06): "
        "0.1% handling, min ¥50, max ¥260, plus ¥150 cable per transfer (non-HK/Macau/Taiwan). "
        "These are published reference values at one moment — not an executable quote (F02, F12).</div>"
    )
    for lid, lad in model["ladders"].items():
        body += f'<h2 id="{lid}">{lid} — {e(lad["label"])}</h2>'
        body += f"<p class=\"muted\">Transfer pattern: {e(lad['transfers'])}. "
        if lad.get("priced_note"):
            body += e(lad["priced_note"]) + " "
        body += f"Method pages: {', '.join(m['id'] for m in methods if m.get('cost_ladder')==lid) or '—'}. </p>"
        if lad["priced"]:
            body += priced_ladder_table(lid)
        else:
            body += unpriced_ladder_table(lid)
    body += (
        "<h2>How each cell is computed</h2><ul>"
        f"<li><strong>CNY needed</strong> = target × {SELL} (BOC sell board, snapshot).</li>"
        f"<li><strong>FX margin</strong> = target × {MARGIN_RATE:.9f} (one-way margin vs board midpoint "
        f"({BOARD['spot_sell']}−{BOARD['mid']})/{BOARD['mid']}).</li>"
        f"<li><strong>Handling</strong> per transfer = min(max(0.1% × CNY amount, ¥50), ¥260) (S06).</li>"
        f"<li><strong>Cable</strong> = ¥{TARIFF['cable_cny_other']} per transfer (S06).</li>"
        "<li><strong>Known subtotal</strong> = FX margin + (handling + cable) summed over transfers ÷ 6.6903.</li>"
        "<li><strong>All-in</strong> stays blank: receiving bank (F03), intermediary (F04) and taxes (F05/F06) "
        "are unverified. A blank cell is never added into the known subtotal.</li></ul>"
    )
    return shell("Cost tables", body)


def priced_ladder_table(lid):
    rows = ""
    for t in TARGETS:
        if lid == "L2":
            n = math.ceil(t / 50000)
        else:
            n = 1
        c = wire_costs(t, n)
        rows += (
            f'<tr><td class="num"><strong>{usd(t)}</strong></td>'
            f'<td class="num"><strong>{usd(c["known"])}</strong></td>'
            f'<td class="num">{pct(c["known"]*100/t)}</td>'
            f'<td class="num">{usd(c["margin"])}</td>'
            f'<td class="num">{cny(c["handling"])}</td>'
            f'<td class="num">{cny(c["cable"])}</td>'
            f'<td class="num">{c["n"]}</td>'
            f'<td class="num">{cny(c["cny_needed"])}</td>'
            '<td class="blank">⚠ UNVERIFIED</td><td class="blank">⚠ UNVERIFIED</td>'
            '<td class="blank">⚠ UNVERIFIED</td><td class="blank">⚠ UNVERIFIED</td>'
            f"<td>{src_links(['S06','S07'])}</td></tr>"
        )
    return (
        '<div class="scroll"><table class="costs sticky-first"><thead><tr>'
        "<th>Target USD</th><th>Known subtotal</th><th>% of target</th><th>FX margin</th>"
        "<th>Handling ¥</th><th>Cable ¥</th><th>Transfers</th><th>CNY needed</th>"
        "<th>Receiving bank</th><th>Intermediary</th><th>CN tax</th><th>All-in</th><th>Source</th>"
        "</tr></thead><tbody>" + rows + "</tbody></table></div>"
    )


def unpriced_ladder_table(lid):
    lad = model["ladders"][lid]
    rows = ""
    for t in TARGETS:
        if lid == "L7":
            per = 300000 / SELL  # CNY 300,000 cap per bank-app transfer
            n = math.ceil(t / per)
            note = f"≤ ¥300,000/transfer → {n} transfer(s) at this snapshot (S17)"
        elif lid == "L8":
            n = 0
            note = "consumption channel — no wire"
        elif lid == "L9":
            n = math.ceil(t / 5000)
            note = f"~{n} crossing(s) at the USD 5,000 permit-free band; above: bank/SAFE permit (S19/S20)"
        else:
            n = 1
            note = "per declared distribution (S03 Section V)"
        rows += (
            f'<tr><td class="num"><strong>{usd(t)}</strong></td><td class="num">{n or "—"}</td>'
            f'<td class="blank">⚠ UNVERIFIED</td><td class="blank">⚠ UNVERIFIED</td>'
            f'<td class="blank">⚠ UNVERIFIED</td><td>{e(note)}</td>'
            + f"<td>{src_links([s for s in (lad.get('fee_source'), lad.get('fx_source')) if s] or ['S07'])}</td></tr>"
        )
    return (
        '<div class="scroll"><table class="costs sticky-first"><thead><tr>'
        "<th>Target USD</th><th>Transfers/crossings</th><th>Provider fee</th><th>FX cost</th>"
        "<th>All-in</th><th>Verified limits / note</th><th>Source</th></tr></thead><tbody>" + rows + "</tbody></table></div>"
    )


def page_methods():
    body = (
        "<h1>Every method found — with pros and cons</h1>"
        '<p class="lead">Lawful routes are conditional entitlements: the rule text allows them when the facts '
        "fit. Prohibited routes are listed with risk information only and <strong>no execution steps</strong>. "
        'Every row links the official source it was verified against.</p>'
        '<div class="notice"><strong>Classification matters:</strong> 境内个人 (mainland-ID holder) and '
        "境外个人 (everyone else) follow different rules (S01 Art. 37). A U.S. citizen is a 境外个人 unless "
        "they also hold a PRC resident ID. The bank makes this call at account level — confirm it first (F01).</div>"
    )
    body += "<h2>Lawful and conditional routes</h2>"
    body += (
        '<div class="scroll"><table class="responsive"><thead><tr><th>Method</th><th>Who qualifies</th>'
        "<th>Rule and cap</th><th>Source</th></tr></thead><tbody>"
        + "".join(method_row(m) for m in methods if not m["id"].startswith("P"))
        + "</tbody></table></div>"
    )
    body += "<h2>Prohibited and high-risk schemes — do not use</h2>"
    body += (
        '<div class="scroll"><table class="responsive"><thead><tr><th>Scheme</th><th>—</th>'
        "<th>Why it is prohibited</th><th>Source</th></tr></thead><tbody>"
        + "".join(method_row(m) for m in methods if m["id"].startswith("P"))
        + "</tbody></table></div>"
    )
    body += "<h2>Pros and cons in detail</h2>"
    for m in methods:
        pros = "".join(f"<li>✅ {e(p)}</li>" for p in m["pros"]) or "<li>—</li>"
        cons = "".join(f"<li>⚠️ {e(c)}</li>" for c in m["cons"]) or "<li>—</li>"
        docs = e(m["docs"]) if m["docs"] != "—" else "—"
        body += (
            f'<div class="flag" id="{m["id"]}-detail"><h3>{m["id"]} — {e(m["name"])}</h3>'
            f"<p><strong>Documents:</strong> {docs}</p>"
            f"<div class=\"cards\"><div><strong>Pros</strong><ul>{pros}</ul></div>"
            f"<div><strong>Cons</strong><ul>{cons}</ul></div></div>"
            f'<p class="muted">{src_links(m["sources"])}</p></div>'
        )
    return shell("Methods", body)


def page_steps():
    body = (
        "<h1>Step by step — exactly how each lawful route works</h1>"
        '<p class="lead">Steps are drawn from the official rule text and guidance pages cited beside each '
        "procedure. Prohibited schemes get no steps.</p>"
    )
    for m in methods:
        if m["id"].startswith("P"):
            continue
        steps = "".join(f"<li>{e(s)}</li>" for s in m["steps"])
        lad = m.get("cost_ladder")
        lad_link = f' · <a href="costs.html#{lad}">cost ladder {lad}</a>' if lad else ""
        body += (
            f'<div class="flag" id="{m["id"]}"><h3>{m["id"]} — {e(m["name"])}</h3>'
            f"<ol>{steps}</ol>"
            f'<p class="muted">{src_links(m["sources"])}{lad_link}</p></div>'
        )
    body += (
        '<div class="notice"><strong>Prohibited schemes (P01–P06):</strong> no step-by-step instructions are '
        'published on this site by design. See <a href="methods.html">Methods</a> for the risk information and '
        "official sources.</div>"
    )
    return shell("Step by step", body)


def page_taxes():
    body = (
        "<h1>Tax and penalty breakdown</h1>"
        '<p class="lead">The &quot;considerable tax&quot; usually feared is not a conversion tax. It is '
        "(a) Chinese income tax on untaxed underlying earnings, (b) U.S. tax on unreported income or §988 "
        "gains, and (c) filing penalties. Each row below is checked against the official source linked in "
        'the last column. Unknown amounts are blank, never inferred.</p>'
    )
    rows = ""
    for r in taxrows:
        amount = f'<span class="num">{e(r["amount"])}</span>' if r["amount"] else '<span class="blank">⚠ UNVERIFIED</span>'
        rows += (
            f'<tr id="{r["id"]}"><td>{e(r["id"])} · {e(r["jurisdiction"])}<br><strong>{e(r["item"])}</strong></td>'
            f"<td>{e(r['finding'])}</td><td>{amount}<br><small>{e(r['amount_note'])}</small></td>"
            f"<td>{src_links(r['sources'])}</td></tr>"
        )
    body += (
        '<div class="scroll"><table class="responsive"><thead><tr><th>Item</th><th>Finding (verified)</th>'
        "<th>Amount</th><th>Source</th></tr></thead><tbody>" + rows + "</tbody></table></div>"
    )
    body += (
        '<div class="good"><strong>The least-tax playbook (compliance, not avoidance):</strong>'
        "<ol><li>Document the source once — tax vouchers are the currency of every Chinese FX route (S02 Art. 13).</li>"
        "<li>Use the matching lawful route; pay any Chinese IIT due on the underlying income (S09).</li>"
        "<li>Claim the U.S. foreign tax credit on Form 1116 for Chinese tax paid (S15).</li>"
        "<li>Keep §988 gains at or below $200 per personal transaction where legitimate (basis = USD value at "
        "receipt), or report the gain as ordinary income (S14).</li>"
        "<li>File FBAR (aggregate &gt; $10,000) and Form 8938 (thresholds above) every year the balances "
        "qualify — filing is cheap; penalties are not (S10, S11, S12).</li></ol></div>"
    )
    return shell("Tax & penalties", body)


def page_sources():
    body = (
        f"<h1>Source register — {len(sources)} entries, all retrieved 2026-11-10</h1>"
        '<p class="lead">Each source was opened and read during this edition\'s verification pass. '
        "Government sources support law and tax claims; provider sources (BOC, Wise) support only their own "
        "published prices and terms.</p>"
    )
    rows = ""
    for s in sources:
        rows += (
            f'<tr id="{s["id"]}"><td>{s["id"]}<br><strong>{e(s["title"])}</strong><br><small>{e(s["publisher"])}</small></td>'
            f'<td><span class="tag {"tag-prohib" if s["kind"]=="provider" else "tag-lawful"}">{s["kind"]}</span></td>'
            f'<td><a href="{s["url"]}" rel="noopener noreferrer">{e(s["url"])}</a></td>'
            f"<td>{e(s['supports'])}</td></tr>"
        )
    body += (
        '<div class="scroll"><table class="responsive"><thead><tr><th>Source</th><th>Kind</th><th>Link</th>'
        "<th>What was verified from it</th></tr></thead><tbody>" + rows + "</tbody></table></div>"
    )
    body += (
        '<div class="notice"><strong>Retrieval method:</strong> direct fetch of each URL on 2026-11-10; quoted '
        "figures were read from the fetched text (BOC board values, tariff percentages, quota amounts, statutory "
        "thresholds). Live availability of external links after publication is not guaranteed. Irregularities "
        'found during retrieval are on the <a href="flagged.html">Flagged for Review</a> page.</div>'
    )
    return shell("Sources", body)


def page_flagged():
    body = (
        "<h1>Flagged for Review</h1>"
        '<p class="lead">These items are published, not hidden. None of them blocks the findings that are '
        "verified; each explains why a cell is blank or why two sources disagree.</p>"
    )
    for f in flags:
        body += (
            f'<div class="flag" id="{f["id"]}"><h3>{f["id"]} — {e(f["title"])}</h3>'
            f"<p>{e(f['detail'])}</p>"
            '<p class="muted">Status: published · non-blocking</p></div>'
        )
    return shell("Flagged for Review", body)


def page_summary():
    body = (
        '<p class="pill">Executive summary · Edition I · verified against ' + str(len(sources)) + ' official sources</p>'
        "<h1>Executive summary</h1>"
        '<h2 style="border:none;margin-top:.6em">Question</h2>'
        "<p>Money is stuck in a Chinese bank account as CNY. What is the best way to convert and move it to "
        "USD for a U.S. citizen, with the least tax penalty? What does it cost at each size from $10,000 to "
        "$400,000?</p>"
        '<h2>Answer in five points</h2>'
        "<ol>"
        "<li><strong>There is no conversion tax in either country.</strong> China's IIT Law taxes nine income "
        "categories — currency exchange is not one (S09 Art. 2). The U.S. exempts personal-transaction FX gains "
        "of $200 or less (26 U.S.C. §988(e)(2), S14) and taxes larger gains as ordinary income. Fees are not "
        "taxes; the conversion cost is FX margin + bank fees.</li>"
        "<li><strong>The real tax question is the source of the money.</strong> If it is salary or service "
        "income already taxed in China, the documented-income route (M01/M03) moves it with tax vouchers and "
        "adds no new Chinese tax; claim the U.S. foreign tax credit (Form 1116, S15) so it is not taxed twice. "
        "If it was never taxed, no channel legalizes it — the tax on the underlying income (3–45% comprehensive, "
        "20% flat on some categories, S09) is the cost to make it movable.</li>"
        "<li><strong>Least-friction routes by source:</strong> after-tax salary/income → documented income wire "
        "(no per-year USD ceiling stated for foreign individuals, S01/S02 Art. 13); routine savings of a "
        "mainland-ID holder → the $50,000/year quota (S02 Art. 2); sold property → property route with tax "
        "voucher (S05); pre-emigration assets or inheritance → SAFE-approved transfer (S03/S04); real business "
        "receipts → trade settlement account (no quota, S02 Art. 9).</li>"
        f"<li><strong>Published cost of the wire mechanics:</strong> at the {BOARD['board_time']} BOC board "
        f"(S07), moving $400,000 as one wire costs {usd(wire_costs(400000,1)['known'])} in verified components "
        f"({pct(wire_costs(400000,1)['known']*100/400000)}: FX margin {pct(MARGIN_RATE*100)} + capped ¥260 "
        f"handling + ¥150 cable); as eight $50,000 quota wires it costs "
        f"{usd(wire_costs(400000,8)['known'])} ({pct(wire_costs(400000,8)['known']*100/400000)}). Receiving-bank "
        "fees, intermediaries and taxes are unverified and shown blank (F03–F05).</li>"
        "<li><strong>Avoid every shortcut.</strong> Splitting transfers across relatives, underground banking, "
        "false trade papers and crypto cash-out are prohibited (S01 Art. 7, S08, S21 — the 2021 crypto notice "
        "S18 was expressly repealed by Yin Fa [2026] No. 42 and the ban continues under it) with criminal "
        "exposure. The penalties that actually get charged in practice are filing penalties: FBAR up to $10,000 "
        "(non-willful) or 50% of balances (willful), Form 8938 up to $10,000 + $10,000/30 days capped at "
        "$60,000 (S12).</li>"
        "</ol>"
        '<div class="notice"><strong>Limits of this summary:</strong> the account holder\'s source of funds, ID '
        "classification, tax history and destination bank are unknown (F01). Nothing here is a personal tax "
        "determination or an executable quote. Blank cells are unverified, not zero. Review the "
        '<a href="flagged.html">Flagged for Review</a> page before acting.</div>'
        '<h2>Cost preview — verified components at each $50,000 step</h2>'
    )
    rows = ""
    for t in range(50000, 400001, 50000):
        c1 = wire_costs(t, 1)
        c2 = wire_costs(t, math.ceil(t / 50000))
        rows += (
            f'<tr><td class="num">{usd(t)}</td><td class="num">{usd(c1["known"])} · {pct(c1["known"]*100/t)}</td>'
            f'<td class="num">{usd(c2["known"])} · {pct(c2["known"]*100/t)}</td>'
            '<td class="blank">⚠ UNVERIFIED</td><td class="blank">⚠ UNVERIFIED</td>'
            f"<td>{src_links(['S06','S07'])}</td></tr>"
        )
    body += (
        '<div class="scroll"><table class="costs sticky-first"><thead><tr><th>Target</th>'
        "<th>Single wire known cost</th><th>Quota-chunked known cost</th><th>Taxes</th><th>All-in</th><th>Source</th>"
        "</tr></thead><tbody>" + rows + "</tbody></table></div>"
        '<p><a href="costs.html">All 10 ladders × 40 targets →</a></p>'
    )
    return shell("Executive summary", body)


def build():
    SITE.mkdir(exist_ok=True)
    (SITE / "assets").mkdir(exist_ok=True)
    shutil.copy(BASE / "build" / "style.css", SITE / "assets" / "style.css")
    (SITE / ".nojekyll").write_text("")
    pages = {
        "index.html": page_index(),
        "executive-summary.html": page_summary(),
        "methods.html": page_methods(),
        "steps.html": page_steps(),
        "costs.html": page_costs(),
        "taxes.html": page_taxes(),
        "sources.html": page_sources(),
        "flagged.html": page_flagged(),
    }
    for name, html in pages.items():
        (SITE / name).write_text(html, encoding="utf-8")
    print(f"built {len(pages)} pages into {SITE}")


if __name__ == "__main__":
    build()
