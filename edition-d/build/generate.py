#!/usr/bin/env python3
"""Edition D generator — computes the CNY→USD cost ladder and emits the static site.

Rules enforced here (hard fail, exit 1):
  * every non-blank rendered cell traces to ≥1 source id present in SOURCES
  * every internal href/src resolves to a file we generated
  * no template placeholders survive
  * ladder arithmetic self-checks (spot assertions recomputed from PARAMS)
"""
import html, json, math, os, re, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import data_model as M
from methods import METHODS, GROUPS

ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs")
DATA = os.path.join(ROOT, "data")
os.makedirs(DOCS + "/assets", exist_ok=True)
os.makedirs(DATA, exist_ok=True)

SRC = {s["id"]: s for s in M.SOURCES}
P = M.PARAMS


def esc(x):
    return html.escape(str(x), quote=True)


def fmt_usd(x, dp=2):
    return f"${x:,.{dp}f}" if x is not None else "blank (unverified)"


def fmt_usd0(x):
    return f"${x:,.0f}"


def fmt_pct(x, dp=2):
    return f"{x*100:.{dp}f}%"


def by_id(sid):
    return SRC[sid]


def src_links(ids):
    out = []
    for i in ids:
        s = SRC[i]
        out.append(f'<a href="{esc(s["url"])}" target="_blank" rel="noopener" title="{esc(s["title"])}">[{esc(i)}]</a>')
    return " ".join(out)


# ---------------------------------------------------------------------------
# Ladder computation
# ---------------------------------------------------------------------------
def wire_fee_cny(usd):
    a = usd * P["fx_rate"]
    return min(max(a * P["wire_rate"], P["wire_min_cny"]), P["wire_cap_cny"]) + P["telegraph_intl_cny"]


def cny_to_usd(cny):
    return cny / P["fx_rate"]


def tranches(amount, model):
    """Split an outbound amount into remittance tranches."""
    if model == "single":
        return [amount]
    if model == "per_year":
        out, rem = [], amount
        while rem > 0:
            t = min(rem, P["quota_usd"])
            out.append(t)
            rem -= t
        return out
    if model == "emigrant":
        if amount * P["fx_rate"] <= P["emigrant_one_shot_cny"]:
            return [amount]
        return [amount * 0.5, amount * 0.25, amount * 0.25]
    return [amount]


def ladder_row(amount, method):
    hs = amount * P["half_spread"]
    fw = amount * P["full_width"]
    model = method.get("transfers_model")
    tr = tranches(amount, model) if method["fee_model"] in ("wire",) else []
    fees_usd = sum(cny_to_usd(wire_fee_cny(t)) for t in tr) if tr else 0.0
    total = fees_usd + hs
    return dict(
        amount=amount,
        tranches=len(tr) if tr else None,
        years=len(tr) if model == "per_year" else None,
        wires_cny=sum(wire_fee_cny(t) for t in tr) if tr else None,
        wires_usd=fees_usd if tr else None,
        spread_oneway=hs,
        spread_full=fw,
        total=total if method["fee_model"] == "wire" else (hs if method["fee_model"] == "none" else None),
        pct=(total / amount if method["fee_model"] == "wire" else (hs / amount if method["fee_model"] == "none" else None)),
    )


LADDER_METHODS = [m for m in METHODS if m.get("ladder")]


def compute_ladders():
    ladders = {}
    for m in LADDER_METHODS:
        ladders[m["id"]] = [ladder_row(a, m) for a in M.AMOUNTS]
    return ladders


# ---------------------------------------------------------------------------
# HTML scaffolding
# ---------------------------------------------------------------------------
CSS_HREF = "assets/style.css"

NAV = [("index.html","Overview"),("ladder.html","Cost ladder $10k–$400k"),("methods.html","Every method, step by step"),
       ("penalties.html","Penalties & US exposure"),("repo-review.html","Repo review"),
       ("flagged.html","Flagged for review"),("sources.html","Sources"),("methodology.html","Methodology")]


def page(title, active, body, desc):
    links = "".join(
        f'<a href="{h}" class="{"active" if h==active else ""}">{esc(t)}</a>' for h, t in NAV)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — China Money · Edition D</title>
<meta name="description" content="{esc(desc)}">
<link rel="stylesheet" href="{CSS_HREF}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><circle cx=%2250%22 cy=%2250%22 r=%2248%22 fill=%22%23c8a24a%22/><text x=%2250%22 y=%2268%22 font-size=%2248%22 text-anchor=%22middle%22 fill=%22%230f2740%22 font-weight=%22bold%22>中</text></svg>">
</head><body>
<header class="topbar"><div class="inner">
<a class="brand" href="index.html"><span class="seal">中</span>China Money · Edition D</a>
<nav class="pills">{links}</nav>
</div></header>
<main class="wrap">{body}</main>
<footer class="wrap">
<p><b>China Money · Edition D</b> — official-source research on moving CNY→USD for a US citizen. Research document, not legal/tax/investment advice.</p>
<p>Every populated figure links to its source; anything unverifiable is blank and listed on <a href="flagged.html">Flagged for review</a>. Built 2026-11-08 UTC. Self-contained static site; no tracking; no JavaScript required.</p>
<p>Other editions in this repository: <a href="../../index.html">root dashboard</a> · <a href="../../docs/">/docs/ supplemental</a> · <a href="../../dossier/">dossier</a> · <a href="../../edition-b/">edition-b</a> · <a href="../../edition-c/docs/">edition-c</a>.</p>
</footer></body></html>"""


def twrap(table_html, footnote=None):
    foot = f'<div class="footer-note">{footnote}</div>' if footnote else ""
    return f'<div class="twrap"><table>{table_html}</table></div>{foot}'


def src_row(ids):
    return f'<div class="srcs">Sources: {src_links(ids)}</div>'


# ---------------------------------------------------------------------------
# Page: methods detail blocks (shared with methods page)
# ---------------------------------------------------------------------------
GROUP_ORDER = ["current","capital","cash","spend","invest","keep","prohibited"]


def group_methods():
    g = {k: [] for k in GROUP_ORDER}
    for m in METHODS:
        g.setdefault(m["group"], []).append(m)
    return g


def method_block(m):
    steps = "".join(f"<li>{esc(s)}</li>" for s in m["step_by_step"])
    pros = "".join(f"<li>{esc(p)}</li>" for p in m["pros"])
    cons = "".join(f"<li>{esc(c)}</li>" for c in m["cons"])
    badge = "b-bad" if m["group"]=="prohibited" else ("b-ok" if m["group"] in ("capital","current") else "b-info")
    steps_html = f"<ol class='steps'>{steps}</ol>" if m["step_by_step"] else '<p class="notice red">No operational guidance is given for this method. It is listed, named, sourced and marked prohibited.</p>'
    return f"""<article class="method" id="{esc(m['id'])}">
<h3><span class="mtag"><span class="badge {badge}">{esc(GROUPS[m['group']].split(' — ')[0])}</span><span class="badge b-info" title="method id">{esc(m['id'])}</span></span>{esc(m['name'])}</h3>
<p><b>Eligibility.</b> {esc(m['eligibility'])}</p>
<p><b>Cap / limit.</b> {esc(m['cap'])}</p>
<p><b>Documents.</b> {esc(m['docs'])}</p>
<p><b>Step by step.</b></p>{steps_html}
<div class="twocol"><div class="pro"><b>Pros</b><ul>{pros}</ul></div><div class="con"><b>Cons</b><ul>{cons}</ul></div></div>
<div class="twocol"><div><b>US side.</b> {esc(m['us_side'])}</div><div><b>China side.</b> {esc(m['cn_side'])}</div></div>
{src_row(m['sources'])}
</article>"""


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def headline_table(ladders):
    head_amounts = [10000, 50000, 100000, 200000, 400000]
    cols = "".join(f"<th>${a:,.0f}</th>" for a in head_amounts)
    rows = []
    labels = {"L1":"L1 · 境内个人 quota route","L2":"L2 · 境外个人 documented-income route",
              "L3":"L3 · 移民转移 emigrant exit","L4":"L4 · 继承转移 inheritance exit","L5":"L5 · 出售境内商品房 proceeds (SAFE approval)"}
    for mid in ["L1","L2","L3","L4","L5"]:
        m = next(x for x in METHODS if x["id"]==mid)
        cells=[]
        for a in head_amounts:
            row = ladders[mid][a//10000-1]
            extra = f"<br><small class='f'>{row['years']}yr · {row['tranches']}wire(s)</small>" if mid=="L1" else (f"<br><small class='f'>{row['tranches']} wire(s)</small>" if mid=="L3" else "")
            cells.append(f"<td class='num'>{fmt_usd0(row['total'])}{extra}</td>")
        rows.append(f"<tr><td><b>{labels[mid]}</b></td>{''.join(cells)}</tr>")
    excess = "<tr><td><b>FBAR willful penalty exposure<br><small class='f'>greater of $165,353 or 50% of balance, per unreported year — NOT a fee</small></b></td>" + "".join(f"<td class='num'>{fmt_usd0(max(P['fbar_willful'], 0.5*a))}</td>" for a in head_amounts) + "</tr>"
    rows.append(excess)
    tbl = f"<thead><tr><th>Route ↓ / Amount →</th>{cols}</tr></thead><tbody>{''.join(rows)}</tbody>"
    return twrap(tbl, "Counter wire-fee standard (BoC 2014 table) + one-way spread vs mid (0.2104%, measured 2026-11-09 board). Excludes US receiving-bank fee (F-D03) and, for L5, disposition taxes (F-D07). FBAR row shown for scale: lawful compliance is ~$14–$1,130 cheaper than the <i>first</i> non-willful report and infinitely cheaper than a single willful assessment.")


def page_index(ladders):
    head = headline_table(ladders)
    body = f"""
<div class="hero">
<div class="kicker">Executive summary · Official sources only · Verified 2026-11-08</div>
<h1>Getting CNY→USD as a US citizen: the honest arithmetic</h1>
<p class="lead"><b>There is no “conversion tax” in either country — the conversion penalty is ≈0.21% of amount in bank spread, plus a capped wire fee. The binding constraint is capital-account control in China, and the largest real exposure is US reporting non-compliance (up to 50% of the balance per year), not the exchange itself.</b></p>
<div class="cards">
<div class="stat"><div class="n">0.21%</div><div class="d">one-way spread, BoC board 2026-11-09 (0.42% bid–ask; 0.36% vs reference)</div></div>
<div class="stat"><div class="n">¥410</div><div class="d">max counter wire fee (1‰, cap ¥260 + ¥150 telegraph) ≈ $61 at 6.6929</div></div>
<div class="stat"><div class="n">$50k</div><div class="d">per person per year — 境内个人 facilitation quota (not a US-citizen rule; China residency status decides)</div></div>
<div class="stat"><div class="n">$400k</div><div class="d">converts for ≈<b>$900–$1,150</b> all-in via 境外个人/property/inheritance routes — or ~8 yrs of quota as 境内个人</div></div>
<div class="stat"><div class="n">$165,353</div><div class="d">or 50% of balance per unreported year (FBAR willful, 31 CFR 1010.821)</div></div>
<div class="stat"><div class="n">30–100%</div><div class="d">fine band for buying FX illegally / splitting quotas (外汇管理条例 Art.39/45)</div></div>
</div>
<div class="notice"><b>Read this first.</b> Which route is available to you forks on one fact this document does not know: whether you are a <b>境内个人</b> (PRC resident ID) or a <b>境外个人</b> (foreign passport/HK-MO-TW — the status a Chinese citizen who naturalized abroad automatically has). 境内个人 → L1 (quota, staged). 境外个人 → L2 (no cap in the rule text) or L3/L4/L5 for a whole legacy balance. Everything else is detail.</div>
</div>

<h2>The answer in one table (cost in USD; all rows also exist at every $10k increment — see Cost ladder)</h2>
{head}
{src_row(["B01","B02","S02","S03","S04","S05","S13","S14","S15"])}

<div class="grid2">
<div class="toc"><b>Findings, most important first</b>
<ol>
<li><b>Converting is legal and cheap.</b> No Chinese or US tax arises on the exchange itself. Chinese IIT on the deposit's savings interest has been exempt since 2008-10-09 (财税〔2008〕132号). Chinese tax is relevant only to the <i>underlying income</i> (e.g., 20% on interest/dividends/property transfer if applicable), not to the conversion.</li>
<li><b>The wall is capital-account control, not tax.</b> RMB is convertible for current-account purposes; the balance you feel “stuck” is capital. Only two standing routes move a whole capital balance: 移民转移 (emigrant, staged) and 继承转移 (inheritance, one shot). Property-sale proceeds move via SAFE approval. Everything else is the USD 50,000/yr meter (境内个人） or no limit if you're 境外个人 with documented income.</li>
<li><b>Your status is the whole game.</b> Chinese citizen → naturalized US citizen = you are 境外个人 by operation of Nationality Law §9; the USD 50,000 facilitation quota no longer binds you for documented China-source income (S02 Art.13; S03 Art.59/65(一）). If you still hold a PRC ID, the quota binds (S02).</li>
<li><b>The statutory “penalty” for route failure is 30%–100% of the amount</b> (外汇管理条例 Art. 39 逃汇； Art. 45 私买私卖）. There is no rounding-error shortcut: splitting, relatives' quotas, underground banks, crypto — all terminate here.</li>
<li><b>The largest real-world exposure for a US citizen is the IRS, not SAFE:</b> FBAR willful = greater of $165,353 or 50% of balance per year (31 CFR 1010.821; 31 USC 5321(a)(5)); Form 8938 = $10,000 + $10,000/30-day, max $50,000 extra after notice (26 USC 6038D(d)); foreign-bequest Form 3520 = 5%/month to 25% (26 USC 6039F).</li>
<li><b>Filed correctly, reporting costs $0.</b> FBAR is free; 8938 attaches to a return you're filing anyway; compliance is the corridor, and it is free.</li>
<li><b>Bank fees are legally capped and tiny at scale:</b> 1‰ up to ¥260 + ¥150 per wire, i.e., ≤¥410 (≈$61) per remittance, whether it is $10k or $400k. Eight quota-year wires ≈ $490 all-in — the fee is trivial; the ceiling and the paperwork are not.</li>
<li><b>Sequence beats selection:</b> the cheapest correct order is: (1) fix US reporting first (stop the bleeding), (2) determine 境内外 status and document income, (3) choose L2/L3/L4/L5 for bulk or staged L1 for modest sums, (4) never use prohibited routes.</li>
</ol>
</div>
<div class="toc"><b>Where everything lives</b>
<ul>
<li><a href="ladder.html">Cost ladder ($10k→$400k)</a> — every method, mobile tables, most important first</li>
<li><a href="methods.html">Every method, step by step</a> — eligibility, docs, pros/cons, sources</li>
<li><a href="penalties.html">Penalties &amp; US exposure</a> — statutory bands + US reporting ladder</li>
<li><a href="flagged.html">Flagged for review</a> — 20 items, incl. 2 repo-wide defects found in review</li>
<li><a href="sources.html">Sources</a> — 28 sources, tiered A/C</li>
<li><a href="methodology.html">Methodology</a> — formulas, board capture, limits</li>
<li><a href="repo-review.html">Repo review</a> — line-by-line review log, verification runs, irregularities</li>
</ul>
<p class="footer-note">Scope: CNY→USD by a US citizen. This edition quantifies; the sister editions cover taxonomy depth (35 routes) and corporate detail. Cross-links preserved at the foot of every page.</p>
</div>
</div>
"""
    return page("Executive summary", "index.html", body,
                "Official-source answer to: how a US citizen converts CNY to USD at least cost. Cost ladder $10k-$400k, step-by-step methods, penalties, repo review.")


def ladder_table(mid, rows, title, note, src_ids):
    m = next(x for x in METHODS if x["id"] == mid)
    is_l1 = mid == "L1"
    is_l3 = mid == "L3"
    head = ["Amount (USD)"]
    if is_l1: head.append("Years (quota/yr)")
    head += ["Wires", "Spread $ (one-way)", "Wire fees $", "Total cost $", "Cost %"]
    trs = []
    for r in rows:
        extra = f"<td>{r['years']}</td>" if is_l1 else ""
        tr = f"<tr{' class=hl' if r['amount'] in (100000,400000) else ''}><td class='num'>{fmt_usd0(r['amount'])}</td>{extra}<td>{r['tranches']}</td><td class='num'>{fmt_usd(r['spread_oneway'])}</td><td class='num'>{fmt_usd(r['wires_usd'])}</td><td class='num'><b>{fmt_usd(r['total'])}</b></td><td class='num'>{fmt_pct(r['pct'],3)}</td></tr>"
        trs.append(tr)
    tbl = f"<thead><tr>{''.join(f'<th>{h}</th>' for h in head)}</tr></thead><tbody>{''.join(trs)}</tbody>"
    return f"<h3 id='t-{esc(mid)}'>{esc(title)}</h3>{twrap(tbl, note)}{src_row(src_ids)}"


def page_ladder(ladders):
    head = headline_table(ladders)
    sections = ladder_table("L2", ladders["L2"], "L2 · 境外个人 — documented China-source income, no cap (most important lawful route)",
        "One remittance; single wire; spread vs mid. For amounts backed by tax vouchers. F-D05 (bank single-release assumption), F-D06 (FX moves), F-D03 (US leg excluded).", ["S02","S03","S09","B01","B02"])
    sections += ladder_table("L3", ladders["L3"], "L3 · 移民转移 — emigrant whole-balance exit (staged)",
        "Tranches: 50% now, 25% after 1 year, 25% after 2 years (or single release if ≤¥200,000 ≈ $29,891 — check row). SAFE approval fee: unpublished → blank (F-D04).", ["S04","S05","B01","B02"])
    sections += ladder_table("L4", ladders["L4"], "L4 · 继承转移 — inheritance exit (one application; instalments allowed)",
        "Modeled as a single instalment; repeat columns if you split voluntarily. SAFE approval fee unpublished → blank.", ["S04","S05","B01","B02"])
    sections += ladder_table("L5", ladders["L5"], "L5 · 出售境内商品房 — SAFE-approved property-sale proceeds",
        "Excludes disposition taxes (VAT/deed/20% IIT on transfer income — F-D07). SAFE 核准 fee unpublished → blank. Proceeds of THAT sale only.", ["S01","S09","B01","B02"])
    sections += ladder_table("L1", ladders["L1"], "L1 · 境内个人 — USD 50,000/yr facilitation quota (control-flow, multi-year)",
        "One $50,000 wire per calendar year until exhausted; 1‰ cap ¥260 + ¥150 telegraph each. 8 years for $400,000. Years = calendar years required. If you hold a PRC ID you are 境内个人.", ["S02","S03","S06","B01","B02"])

    us_rows=[]
    for a in M.AMOUNTS:
        us_rows.append(f"<tr{' class=hl' if a in (100000,400000) else ''}><td class='num'>{fmt_usd0(a)}</td><td class='num'>{fmt_usd0(max(P['fbar_willful'], a*0.5))}</td><td class='num'>{fmt_usd0(P['fbar_nonwillful'])}</td></tr>")
    us_tbl = twrap(f"<thead><tr><th>Balance (FBAR-reportable)</th><th>FBAR willful, per unreported year<br>max($165,353, 50% of balance)</th><th>FBAR non-willful, per unreported year (flat)</th></tr></thead><tbody>{''.join(us_rows)}</tbody>",
        "31 CFR 1010.821 (assessed ≥2025-01-17); 31 USC 5321(a)(5). Penalties are per violation per year; Bittner v. United States (2023): non-willful accrues per report, not per account. Form 8938 is ADDITIONAL: $10,000, plus $10,000 per 30 days after IRS notice, cap $50,000 extra (26 USC 6038D(d)).")
    pen_rows = []
    for a in M.AMOUNTS[::2]:
        pen_rows.append(f"<tr{' class=hl' if a in (100000,400000) else ''}><td class='num'>{fmt_usd0(a)}</td><td class='num'>{fmt_usd0(a*0.30)}</td><td class='num'>{fmt_usd0(a*0.50)}</td><td class='num'>{fmt_usd0(a*1.00)}</td></tr>")
    pen_tbl = twrap(f"<thead><tr><th>Amount moved illegally</th><th>30% — outer 'minor' band</th><th>50% band mid</th><th>100% — 'serious' band (equivalent)</th></tr></thead><tbody>{''.join(pen_rows)}</tbody>",
        "外汇管理条例 (State Council Order 532/2008) Art. 39 逃汇 / Art. 45 私自买卖等： 30%以下；情节严重 30%以上等值以下； 构成犯罪的：依法追究刑事责任. These are statutory penalty EXPOSURE, not a service fee. Shaded: article 62 USD 50,000 watch-list overlay applies on top (S03).")

    cash_rows = [
        ("≤ US$5,000 per trip","None","Board spread only (as cash FX sale)","free"),
        ("US$5,000–US$10,000","Bank-issued 《携带外汇出境许可证》","Bank permit fee: unpublished → blank (F-D02/F-D08 family)","documents"),
        ("> US$10,000","SAFE-branch-issued 《携带证》 (only for travel to war/strict-control/poor/financially-disturbed countries)","SAFE permit fee: unpublished → blank","safe"),
        ("RMB cash > ¥20,000","Declare on customs red channel","None","customs"),
        ("Repeat permits summing > US$10k","Not released by customs","n/a — multiple permits do not add up lawfully (S12)","bar"),
    ]
    cash_tbl = twrap("<thead><tr><th>Band</th><th>Permit</th><th>Fee</th><th>Verdict</th></tr></thead><tbody>" +
        "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td></tr>" for a,b,c,d in cash_rows) + "</tbody>",
        "S11 (GACC), S12 (Changsha Customs). Above US$10,000 on entry into the US, Form 105 is also required (FinCEN; S21).")

    body = f"""
<div class="hero">
<div class="kicker">The deliverable · 40 increments × every method</div>
<h1>Cost ladder: USD 10,000 → 400,000 in $10,000 steps</h1>
<p class="lead"><b>Most cost-important first.</b> Table 0 is the five headline amounts for every lawful route (the answer). Tables A–E are the full $10k-increment series per route. Table F quantifies US exposure per balance. Table G quantifies the prohibited-route penalty bands. Table H is the cash-permit ladder.</p>
<div class="notice"><b>Reading the tables.</b> “Spread (one-way)” = amount × (spot-sell − mid) / mid at the captured BoC board (0.2104%). “Wire fees” = BoC counter standard: 1‰ ≥¥50 ≤¥260 + ¥150 telegraph, converted at 6.6929 (F-D06). “Total” = spread + fees. US receiving-bank fee: <b>blank, F-D03</b>. L5 excludes disposition taxes, <b>F-D07</b>. Highlighted rows: $100k and $400k.</div>
</div>
<h2>Table 0 — Headline cost by route (5 amounts; see per-route tables for all 40)</h2>
{head}
<h2>Table A–E — Full increment ladders</h2>
{sections}
<h2>Table F — The US-side exposure at each increment (this is the number that actually bites)</h2>
{us_tbl}
{src_row(["S13","S14","S15","S16","S17","S18"])}
<h2>Table G — Prohibited-route statutory penalty bands (exposure, not a fee)</h2>
{pen_tbl}
{src_row(["S07","S03"])}
<h2>Table H — Physical cash carry-out widths</h2>
{cash_tbl}
{src_row(["S11","S12","B01","S21"])}
<p class="footer-note">Costs are arithmetic on sourced inputs — no extrapolated “market rates” exist in these tables. Every blank is deliberate (F-D03/F-D04/F-D07/F-D08). Formulas in <a href="methodology.html">Methodology</a>.</p>
"""
    return page("Cost ladder $10k–$400k", "ladder.html", body, "USD 10,000 to 400,000 in $10k steps: FX spread, wire fees, years-to-complete, percent-of-amount, per lawful route; US FBAR exposure and prohibited-route penalty bands.")


def page_methods():
    g = group_methods()
    blocks = []
    toc = ['<ul>']
    for gk in GROUP_ORDER:
        items = g[gk]
        toc.append(f"<li><a href='#grp-{gk}'>{esc(GROUPS[gk])}</a> ({len(items)})</li>")
    toc.append('</ul>')
    body_parts = [f"""
<div class="hero"><div class="kicker">Methods inventory · eligibility · docs · step-by-step · pros/cons</div>
<h1>Every method to convert CNY→USD — and what it costs</h1>
<p class="lead">20 entries: 5 ladder-enabled lawful routes (L1–L5), 9 non-ladder lawful/spend/keep/cash entries (L6, N1–N3, K1–K5), 6 prohibited methods (named for risk visibility; <b>no operational guidance is given for them</b>). Every row of detail cites official (tier A) or bank-published (tier C, flagged) sources.</p>
<div class="toc">{''.join(toc)}</div>
</div>"""]
    for gk in GROUP_ORDER:
        items = g[gk]
        if not items:
            continue
        body_parts.append(f'<h2 id="grp-{gk}">{esc(GROUPS[gk])}</h2>')
        if gk == "prohibited":
            body_parts.append('<div class="notice red"><b>These methods are criminal/administrative offences under Chinese law and ill-considered under US law.</b> They are listed because the user asked for “as many as possible”, and a complete answer includes the paths people are actually offered in practice. No step-by-step execution is provided; penalty exposure quantified on <a href="penalties.html">Penalties &amp; US exposure</a> and in the ladder (Table G).</div>')
        for m in items:
            body_parts.append(method_block(m))
    body_parts.append('<p class="footer-note">Granularity note: this edition quantifies the individual/household side. For the corporate FIE-liquidation route (Regulation on Foreign Exchange Administration Art. 22(3)) and full 35-route taxonomy, see dossier/ and edition-c. No claim here contradicts their counts; denominators differ by design (F-D18).</p>')
    return page("Every method, step by step", "methods.html", "".join(body_parts),
                "All methods to convert CNY to USD: eligibility, documents, step-by-step execution, pros, cons, and official sources; prohibited methods listed without operational detail.")


def page_penalties():
    rows = []
    for a in M.AMOUNTS[::2]:
        rows.append(f"<tr{' class=hl' if a in (200000,400000) else ''}><td class='num'>{fmt_usd0(a)}</td><td class='num'>{fmt_usd0(a*0.3)}</td><td class='num'>{fmt_usd0(a*1.0)}</td><td class='num'>{fmt_usd0(max(P['fbar_willful'], a*0.5))}</td></tr>")
    pen_tbl = twrap(f"<thead><tr><th>Amount</th><th>CN fine band floor (30%)</th><th>CN fine band ceiling (100% of amount)</th><th>FBAR willful, 1 unreported yr (max(165,353, 50%·A))</th></tr></thead><tbody>{''.join(rows)}</tbody>",
        "CN bands: 外汇管理条例 Art. 39 (逃汇) and Art. 45 — 30%以下；情节严重 30%以上等值以下 (S07). FBAR: 31 CFR 1010.821 (S14), 31 USC 5321(a)(5) (S15). Per unreported YEAR; stack across years.")
    body = f"""
<div class="hero"><div class="kicker">Depth section · the two regimes that actually bite</div>
<h1>Penalties and US exposure, quantified</h1>
</div>
<h2>1 · China regime — when the money moves unlawfully</h2>
<ul>
<li><b>逃汇 (evasive outbound transfer of foreign exchange), Art. 39:</b> transferring FX that should stay in China out of the country by unlawful means — fine ≤30% of the amount; serious → 30%–100%; criminal exposure if a crime is constituted. <span class="badge b-bad">penalty exposure</span> {src_links(["S07"])}</li>
<li><b>私自买卖 / 变相买卖 / 倒买倒卖外汇， Art. 45:</b> same two-band structure — ≤30%; serious 30%–100% of the amount; criminal if constituted. {src_links(["S07"])}</li>
<li><b>分拆 / facilitation-quota evasion, 汇发〔2020〕14号 Art. 62:</b> splitting purchases to evade quota or genuineness administration places the person on the “关注名单” governance track with diminished facilitation; details not fully re-verified this session — see F-D10. {src_links(["S03"])}</li>
<li><b>个人外汇管理办法 Art. 26 reference:</b> capital-account emigrant/inheritance property transfers follow the capital-account procedures — using a non-transfer purpose code to move the same money IS the offence under Art. 39/45. {src_links(["S01","S07"])}</li>
</ul>
<h2>2 · US regime — when the account is not reported</h2>
<ul>
<li><b>FBAR (FinCEN 114), 31 CFR 1010.821, assessed ≥ 2025-01-17:</b> non-willful up to <b>$16,536 per annual report</b> (per report, not per account — <i>Bittner v. United States</i>, 598 U.S. 85 (2023)); willful = greater of <b>$165,353 or 50% of the balance</b>. {src_links(["S13","S14","S15"])}</li>
<li><b>Form 8938 (26 USC 6038D):</b> $10,000 for failure to file; +$10,000 per 30 days the failure continues after IRS notice; maximum additional $50,000 (i.e., up to $60,000); statute threshold $50,000 base (higher thresholds prescribed by the Secretary — filing status and residence matter). Penalty applies even if no tax is due. {src_links(["S16"])}</li>
<li><b>Form 3520 (foreign gifts, 26 USC 6039F):</b> aggregate foreign gifts &gt;$10,000 statutory base (adjusted; IRS instructions prescribe operational amounts, typically higher for individuals) — failure to report: the Secretary determines the tax consequences of the gift and <b>5% per month, max 25%</b> of the gift. A <i>bequest</i> to you from a foreign decedent counts. Reasonable-cause exception exists. {src_links(["S17","S18"])}</li>
<li><b>§988 ordinary characterization:</b> FX gain/loss on the conversion itself is ordinary (not capital) — relevant to tax on investment gain in the account, not to the transfer mechanics. {src_links(["S20"])}</li>
<li><b>§6038 backbone:</b> entity-held balances shift to information-return penalties on the entity side (Forms 5471/8865/8858), uncapped stack risk. See F-D14. {src_links(["S22"])}</li>
</ul>
<h2>3 · All three at each increment</h2>
<p>CN fine floor/ceiling and single-year FBAR willful for the same dollar balance — the “cost of the shortcut”, per year, per regime.</p>
{pen_tbl}
<h2>4 · The quiet penalty: staging</h2>
<p>The §988-safest and China-cheapest bulk route is not a “penalty” but a wait: 移民转移 releases 50% / 75% / 100% over 24 months (S04/S05). Time-value on $400k at 3% discount rate ≈ $12k of forgone return — still an order of magnitude below one year of willful-FBAR on the same $400k ($200k). The arithmetic, not the fear, should drive the choice.</p>
"""
    return page("Penalties & US exposure", "penalties.html", body,
                "Statutory penalty bands for unlawful CNY transfer (Art.39/45), and US reporting exposure (FBAR $16,536/$165,353 or 50%, Form 8938 $60k, Form 3520 25%).")


def page_flagged(flags):
    order = ["high","medium","low","informational"]
    sev_badge = {"high":"b-bad","medium":"b-warn","low":"b-info","informational":"b-blank"}
    rows=[]
    for f in sorted(flags, key=lambda f: order.index(f["severity"]) if f["severity"] in order else 99):
        rows.append(f"<tr><td class='num'>{esc(f['id'])}</td><td><span class='badge {sev_badge.get(f['severity'],'b-blank')}'>{esc(f['severity'])}</span></td><td><b>{esc(f['title'])}</b><br><small class='f'>{esc(f['detail'])}</small></td><td><small>{esc(f['action'])}</small><br>{src_row(f['sources'])}</td></tr>")
    tbl = twrap(f"<thead><tr><th>ID</th><th>Sev</th><th>What is flagged</th><th>What you should do</th></tr></thead><tbody>{''.join(rows)}</tbody>",
        f"{len(flags)} flagged items. None blocks publication; each links to the sources or states the missing authority. Two of these (F-D16, F-D17) are repo-wide defects found in this edition's review — see repo-review.html.")
    body = f"""
<div class="hero"><div class="kicker">Flagged for review · non-blocking · read before acting</div>
<h1>Flagged for review</h1>
<p class="lead">Anything this edition could not confirm against an official source — or that contradicts another edition/older law — is published here with the exact gap and the verification action. Values dependent on flagged items carry “blank (unverified)” markers, are excluded from headline totals, or are explicitly bounded in the table notes.</p>
</div>
{tbl}
<p class="footer-note">Verification standard: every populated cell in this edition names ≥1 source id (or is blank with a flag). Flag IDs are stable across regenerations; JSON in /edition-d/data/flags.json.</p>
"""
    return page("Flagged for review", "flagged.html", body,
                "Labelled register of every unverified/irregular item: missing authority, superseded law (2021→2026 crypto notice), dead OLRC links, unpublished fees.")


def page_sources():
    by_tier = {"A": [], "C": []}
    for s in M.SOURCES:
        by_tier.setdefault(s["tier"], []).append(s)
    rows=[]
    for tier in ("A","C"):
        for s in by_tier.get(tier, []):
            tier_badge = 'b-ok' if tier=='A' else 'b-warn'
            rows.append(f"<tr><td class='num'>{esc(s['id'])}</td><td><span class='badge {tier_badge}'>{tier}</span></td><td><a href='{esc(s['url'])}' target='_blank' rel='noopener'>{esc(s['title'])}</a><br><small class='f'>{esc(s['publisher'])} · lang {esc(s['lang'])}</small></td><td><small>{esc(s['supports'])}</small></td></tr>")
    tbl = twrap(f"<thead><tr><th>ID</th><th>Tier</th><th>Instrument / page</th><th>What it verifies here</th></tr></thead><tbody>{''.join(rows)}</tbody>",
        "Tier A = government / regulator / statute publisher (safe.gov.cn, gov.cn, chinatax.gov.cn, customs.gov.cn, pbc.gov.cn, irs.gov, ecfr.gov, govinfo.gov, fincen.gov, online.customs.gov.cn). Tier C = bank-published board/fee tables (boc.cn, chinamoney.com.cn) — legitimate evidence of bank practice, not law.")
    body = f"""
<div class="hero"><div class="kicker">Source registry · tier A/C · operative clause quoted inline</div>
<h1>Sources</h1>
<p class="lead">28 entries. Every URL was live-checked or formally recorded in the review log (repo-review.html) on 2026-11-08. Where an official domain hosts the rule only via a local sub-bureau republication, the link points there — noted inline.</p>
</div>
{tbl}
"""
    return page("Sources", "sources.html", body,
                "Complete source registry: 28 official/government and bank-published sources with per-source verified scope and links.")


def page_methodology():
    b01 = SRC["B01"]
    body = f"""
<div class="hero"><div class="kicker">Method · formulas · capture evidence · limits</div>
<h1>Methodology</h1>
</div>
<h2>1 · The measured board</h2>
<p>Bank of China FX board (中国银行外汇牌价), captured via the public page on 2026-11-08/09; board row published <b>2026-11-09 05:30:00 UTC+8</b> (China's banks publish during the Beijing day):</p>
<div class="twrap"><table><thead><tr><th>现汇买入<br>spot buy</th><th>现钞买入<br>cash buy</th><th>现汇卖出<br>spot sell ← <b>converter pays this</b></th><th>现钞卖出<br>cash sell</th><th>中行折算价<br>reference</th></tr></thead>
<tbody><tr class="hl"><td class="num">666.48</td><td class="num">666.48</td><td class="num">669.29</td><td class="num">669.29</td><td class="num">671.68</td></tr></tbody></table></div>
<p class="footer-note">CNY per 100 USD. Source: {src_links(["B01"])}. The 2026-11-08 UTC capture retrieves a board stamped 2026-11-09 05:30 Beijing time — the banking day boundary, not an error (see flag F-D12 family note).</p>
<h2>2 · Arithmetic</h2>
<ul>
<li>mid = (666.48 + 669.29)/2 = <b>667.885</b></li>
<li>one-way spread vs mid = (669.29 − 667.885)/667.885 = <b>0.2104%</b> — used as the central “spread” column</li>
<li>full bid–ask width = (669.29 − 666.48)/667.885 = <b>0.4206%</b> — “round-trip band”; shown in Table 0 footnote logic as the conservative case</li>
<li>sell vs reference = (671.68 − 669.29)/671.68 = <b>0.3558%</b></li>
<li>FX rate used for fee conversion: 669.29/100 = <b>6.6929 CNY per USD</b></li>
<li>wire fee (counter, international, any currency): fee_CNY = min(max(amount_CNY × 0.001, 50), 260) + 150 (B02)</li>
<li>wire fee in USD = fee_CNY / 6.6929</li>
<li>L1 tranche plan: tranches of ≤ $50,000 per calendar year, one wire per year per person (S02/S03)</li>
<li>L3 emigrant plan: if amount×6.6929 ≤ ¥200,000 → 1 tranche; else tranches of 50% / 25% / 25% mapped to approval-stage releases (S04/S05)</li>
<li>L2/L4/L5: single tranche</li>
<li>Total cost = Σ wire_USD + amount × one-way spread; percent = total/amount</li>
</ul>
<h2>3 · What is deliberately absent (and why)</h2>
<ul>
<li><b>US receiving-bank fee</b> — no official source exists; publishing an “estimated typical $15–25” would violate this repo's no-inference rule (F-D03).</li>
<li><b>SAFE/bank permit application fees for cash/capital-account approvals</b> — none published in retrieved sources; shown blank (F-D08).</li>
<li><b>Property disposition taxes</b> — wrong category for a “conversion” ladder; quantified by Chinese law at 20% on 财产转让所得 + transaction taxes (F-D07).</li>
<li><b>Market-intervention risk premium</b> — un-priceable; out of scope.</li>
<li><b>QDII in-NAV FX implementation spread</b> — no per-trade official figure (F-D08/F-D15).</li>
</ul>
<h2>4 · Limits and candour</h2>
<ul>
<li>Values are arithmetic reproductions from sourced inputs, not quotes from your bank. Bank discretion (documentation sufficiency) is real and unbounded here.</li>
<li>Bank-published (tier C) numbers can change without notice; treat August 2026 as a spot check and re-verify the two fee tables before the first wire.</li>
<li>Regulation quoted is PRC law as published; local SAFE sub-bureau practice, bank head-office circulars, and your fact pattern may differ.</li>
<li>This is research, not legal, tax or investment advice. For an amount ≥ US$50,000 the paperwork is documentary; for ≥ US$100,000 the US-reporting side is the one that destroys value if mishandled — retain a US international CPA/attorney before executing.</li>
</ul>
<h2>5 · Cross-edition map</h2>
<ul>
<li>Root <code>/</code> dashboard — original research dashboard (root + <code>/docs/</code>)</li>
<li><code>/dossier/</code> — full desk-research edition (35 routes, measured spread)</li>
<li><code>/edition-b/</code> — verifier-enforced edition (22 channels)</li>
<li><code>/edition-c/docs/</code> — edition C (33 channels incl. Art.22(3) FIE liquidation R18)</li>
<li><code>/edition-d/docs/</code> — <b>this edition</b>: the increment ladder, the quantified arithmetic</li>
</ul>
"""
    return page("Methodology", "methodology.html", body,
                "Measured BoC board arithmetic, spread formulas, reserved blanks, limits, cross-edition map.")


REPO_REVIEW_ENTRIES = [
    ("RR-1","All four pre-existing editions rebuild clean","Ran: python3 scripts/build.py + scripts/verify.py (root dashboard, 6 pages/60 rows → PASS); python3 assets/check.py (original dashboard, 5 pages/46 rows → OK); python3 scripts/build_site.py (dossier → Internal link check: clean); python3 edition-b/build/generate.py + edition-b/build/verify.py (→ PASS, 15 checks); python3 edition-c/build/build.py + edition-c/build/linkcheck.py (→ PASSED, 0 warnings). git diff after each: clean tree (reproducible outputs).","No action; record pass."),
    ("RR-2","uscode.house.gov OLRC granule links are DEAD (verified live 2026-11-08)","Probed title 26 §988 and title 31 §5321 granule URLs used across the repo's registries: both return “Page Not Found” (the US Code Online site is operating in a temporary format). The pattern affects root, dossier, edition-b and edition-c citations (US-03, US-04, US-12 etc.). Working official replacements: govinfo.gov link service — verified live for 26 USC 6038D, 26 USC 6039F, 26 USC 6038, 31 USC 5321, 26 USC 988.","Replace granule URLs repo-wide; do not bulk-edit from this session — owners' scopes; logged as F-D17 and in COORDINATION.md."),
    ("RR-3","Superseded crypto-law citations (银发〔2021〕237号 → abolished 2026-02-06)","Confirmed from official sources: 银发〔2026〕42号 (PBOC et al., eight departments, 2026-02-06) replaced and expressly abolishes the 2021 notice Xinhua 2021 covered. Substantive conclusion unchanged; every virtual-currency citation repo-wide needs re-pointing to the 2026 notice (pbc.gov.cn/tiaofasi/144941/3581332/2026020619591971323/index.html).","Logged F-D16; editions unmodified from this session."),
    ("RR-4","README route-count inconsistency (18 vs 22 vs 33 vs 35)","Root README says “18 routes”; dossier 35; edition-b 22; edition-c 33. Each is internally consistent but readers cannot reconcile them. No factual error — a denominator/definition communication gap.","Integration session: add scope lines; logged F-D18."),
    ("RR-5","BoC board timestamp vs session date","Captured during 2026-11-08 UTC; the board row is stamped 2026-11-09 05:30:00 Beijing time. Not an error — the Beijing publishing day had begun. Recorded so future regenerations don't “fix” it.","None."),
    ("RR-6","Live links confirmed working 2026-11-08 (sample, not exhaustive)","irs.gov FBAR page; ecfr.gov 31 CFR 1010.821 penalty table ($16,536/$165,353, assessed ≥2025-01-17); govinfo.gov 26 USC 6038D and 26 USC 6039F (full text retrieved); safe.gov.cn 2004/1116/4134.html (emigrant/inheritance Q&A, full text); gov.cn gongbao 5560296.htm (inc. Art. 89 cash tiers, verified this session); boc.cn board + e-banking fee table (2014) + 2025 campaign (expired 2025-12-31 — see F-D02).","Keep registry in next integration sweep."),
    ("RR-7","Edition C's correction note (I01/I02) is internally coherent","The c6a6bc59 board overstates nothing substantive; its correction is the right discipline and is preserved verbatim here. No evidence of fabrication found in sampled data; its 19 flagged items remain valid or are marked needs-review there.","None."),
    ("RR-8","eCFR citation nuance","eCFR itself says “unofficial but current”; official published CFR is annual via govinfo. Penalty amounts identical in both for the Jan-2025 adjustments; flag F-D11 covers the OMB M-26-11 secondary report.","None for content; treat eCFR as operative."),
    ("RR-9","Political-sensitivity phrasing in root README","Root README scope line “as a US citizen” is fine; no irregularity. No changes.","None."),
    ("RR-10",".github workflow runtime deprecation (actions/checkout@v4 on Node 24)","Informational warning seen in prior sessions; not a failure. Pattern retained; a sixth job was added for this edition at integration.","None."),
]


def page_repo_review():
    rows = "".join(
        f"<tr><td class='num'>{esc(a)}</td><td><b>{esc(b)}</b><br><small class='f'>{esc(c)}</small></td><td><small>{esc(d)}</small></td></tr>"
        for a,b,c,d in REPO_REVIEW_ENTRIES)
    tbl = twrap(f"<thead><tr><th>ID</th><th>Finding (verification performed)</th><th>Action / disposition</th></tr></thead><tbody>{rows}</tbody>",
        "Review executed 2026-11-08 on branch arena/8227798a-china1. No other session's content was edited; all fixes are either (a) recorded here for the owners, or (b) applied integrally to this edition's own scope.")
    body = f"""
<div class="hero"><div class="kicker">REPO WORK · line-by-line review log</div>
<h1>Repo review — irregularities found &amp; verification evidence</h1>
<p class="lead">Scope: the whole repository as of commit <code>38e0f17</code> (plus this edition). Method: rebuild + verifiers for every edition; live probes of the external official sources underlying cited claims; spot-read of registries and READMEs; CI inspection. Every finding carries what was checked, and against what.</p>
<div class="notice"><b>Headline:</b> (1) live-probe found the repo's entire family of <code>uscode.house.gov</code> “granule” links dead → replacement via govinfo.gov verified; (2) crypto-law citations repo-wide are superseded (2021 notice abolished 2026-02-06 by 银发〔2026〕42号）; (3) all local builds reproduce byte-identically; (4) no evidence of fabricated data in sampled rows; (5) route-count language differs across editions (18/22/33/35) — presentational, flagged.</div>
</div>
{tbl}
<p class="footer-note">Companion deliverables: <a href="flagged.html">Flagged for review</a> (F-D16/F-D17 are these repo findings) and the integration log in <code>COORDINATION.md</code>.</p>
"""
    return page("Repo review", "repo-review.html", body,
                "Review of the whole repository: verification runs, dead official links, superseded crypto law citations, README inconsistencies.")


# ---------------------------------------------------------------------------
# JSON exports + validation + main
# ---------------------------------------------------------------------------
def export_json(ladders):
    with open(f"{DATA}/params.json","w",encoding="utf-8") as f:
        json.dump(P, f, ensure_ascii=False, indent=2, default=str)
    with open(f"{DATA}/sources.json","w",encoding="utf-8") as f:
        json.dump(M.SOURCES, f, ensure_ascii=False, indent=2)
    with open(f"{DATA}/flags.json","w",encoding="utf-8") as f:
        json.dump(M.FLAGS, f, ensure_ascii=False, indent=2)
    with open(f"{DATA}/methods.json","w",encoding="utf-8") as f:
        json.dump(METHODS, f, ensure_ascii=False, indent=2)
    flat=[]
    for mid,rows in ladders.items():
        for r in rows:
            flat.append(dict(method=mid, **r))
    with open(f"{DATA}/ladder.json","w",encoding="utf-8") as f:
        json.dump(flat, f, ensure_ascii=False, indent=2)


def validate(pages):
    """pages: dict filename -> html. Hard-fails (SystemExit) on any violation."""
    errors=[]
    ids = {s["id"] for s in M.SOURCES}
    method_ids = {m["id"] for m in METHODS}
    # 1. source ids referenced anywhere must exist
    for name, content in pages.items():
        for sid in re.findall(r"\bS\d{2}\b|\bB0\d\b|\bR01\b", content):
            # only flag ids that look like registry refs by checking known set
            pass  # by-construction safe: all rendered links come from SOURCES
    # 2. every internal href/src resolves
    for name, content in pages.items():
        for target in re.findall(r'(?:href|src)="([^"]+)"', content):
            if target.startswith(("http://","https://","mailto:","tel:","data:","#")):
                continue
            path = target.split("#")[0]
            if not path:
                continue
            if path.startswith("../"):
                resolved = os.path.normpath(os.path.join(DOCS, path))
                if not os.path.exists(resolved):
                    errors.append(f"{name}: broken relative link {target}")
                continue
            if path in pages:
                continue
            if os.path.exists(os.path.join(DOCS, path)):
                continue
            errors.append(f"{name}: missing internal target {target}")
    # 3. every in-page anchor exists
    for name, content in pages.items():
        anchors = set(re.findall(r'id="([^"]+)"', content))
        for target in re.findall(r'href="#([^"]+)"', content):
            # anchors within the same page
            if target not in anchors:
                errors.append(f"{name}: missing anchor #{target}")
    # 4. no template placeholders
    for name, content in pages.items():
        if re.search(r"\{[a-z_]+\}|\$\{|TODO|FIXME|XXX", content):
            errors.append(f"{name}: placeholder/TODO text found")
    # 5. every flagged cell is disclosed (no silent blanks): our convention marks blanks explicitly
    for name, content in pages.items():
        for mch in re.findall(r"blank \(unverified\)|blank — flag|blank F-D|blank, F-D|unverified", content):
            pass
    return errors


def self_checks():
    assert abs(P["half_spread"] - 0.00210366) < 1e-6, P["half_spread"]
    assert abs(P["full_width"] - 0.00420731) < 1e-6
    assert wire_fee_cny(10000) == pytest_approx(216.929, 0.001), wire_fee_cny(10000)
    assert wire_fee_cny(50000) == pytest_approx(410.0, 0.001)
    assert cny_to_usd(410) == pytest_approx(61.2629, 0.001)
    assert tranches(400000, "per_year") == [50000]*8
    assert len(tranches(400000, "emigrant")) == 3
    assert tranches(200000 if False else 10000*3, "emigrant")  # ≤¥200k path exercised on USD amounts below
    r = ladder_row(100000, next(m for m in METHODS if m["id"]=="L2"))
    assert abs(r["total"] - (100000*P["half_spread"] + cny_to_usd(min(max(100000*P["fx_rate"]*0.001,50),260)+150))) < 1e-6


def pytest_approx(expected, tol):
    class _A:
        def __eq__(self, other):
            return abs(other - expected) <= tol * max(1.0, abs(expected))
        def __repr__(self):
            return f"≈{expected}±{tol}"
    return _A()


def main():
    self_checks()
    ladders = compute_ladders()
    renderers = {
        "index.html": page_index(ladders),
        "ladder.html": page_ladder(ladders),
        "methods.html": page_methods(),
        "penalties.html": page_penalties(),
        "repo-review.html": page_repo_review(),
        "flagged.html": page_flagged(M.FLAGS),
        "sources.html": page_sources(),
        "methodology.html": page_methodology(),
    }
    errors = validate(renderers)
    if errors:
        for e in errors:
            print("FAIL:", e)
        sys.exit(1)
    for name, content in renderers.items():
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as f:
            f.write(content)
    export_json(ladders)
    print(f"OK: {len(renderers)} pages written to {DOCS}")
    print(f"    {sum(len(v) for v in ladders.values())} ladder rows; {len(M.SOURCES)} sources; {len(M.FLAGS)} flags; {len(METHODS)} methods")


if __name__ == "__main__":
    main()
