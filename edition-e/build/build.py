#!/usr/bin/env python3
"""Deterministic static-site builder for Edition E. Python standard library only."""
from __future__ import annotations
import csv, html, io, json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"
D = Decimal

def load(name): return json.loads((DATA / name).read_text(encoding="utf-8"))
SOURCES = {s["id"]: s for s in load("sources.json")["sources"]}
ROUTES_DOC = load("routes.json"); ROUTES = ROUTES_DOC["routes"]; CATS = {c["id"]: c for c in ROUTES_DOC["categories"]}
TAX = load("tax.json")["rows"]; FLAGS = {f["id"]: f for f in load("flags.json")["flags"]}
AUDIT = load("audit.json")["findings"]; PENALTIES = load("penalties.json")["rows"]; SUMMARY = load("summary.json"); P = load("parameters.json")
AMOUNTS = [P["amounts"]["start_usd"] + i * P["amounts"]["step_usd"] for i in range(P["amounts"]["count"])]

def q2(x: Decimal) -> str: return str(x.quantize(D("0.01"), rounding=ROUND_HALF_UP))
def money(x): return "blank" if x is None else f"{D(str(x)):,.2f}"
def esc(x): return html.escape(str(x), quote=True)
def src_links(ids):
    return " ".join(f'<a class="src" href="sources.html#{esc(i)}" title="{esc(SOURCES[i]["title"])}">{esc(i)}</a>' for i in ids)
def ext_src_links(ids):
    return " ".join(f'<a class="src" href="{esc(SOURCES[i]["url"])}" rel="noopener noreferrer" target="_blank">{esc(i)} ↗</a>' for i in ids)
def blank(): return '<span class="blank">blank<span class="sr"> unverified</span></span>'
def cell(v, cls=""):
    if v is None: return f'<td class="num {cls}">{blank()}</td>'
    return f'<td class="num {cls}">{esc(v)}</td>'

def compute_row(route, amount):
    a = D(amount); model = route["cost_model"]
    row = {"route_id": route["id"], "amount_usd": amount, "status": route["status"],
           "fx_spread_proxy_usd": None, "sender_fee_cny": None, "sender_fee_usd": None,
           "sc_personal_cny": None, "sc_ease_cny": None, "sc_priority_cny": None, "sc_priority_private_cny": None,
           "receiving_fee_usd": None, "personal_tax_usd": None, "all_in_total_usd": None,
           "feasibility": feasibility(route, amount), "sources": sorted(set(route["sources"] + cost_sources(model)))}
    if route["status"] in ("prohibited", "unverified"):
        row["feasibility"] = "No lawful/verified cost scenario"
        return row
    if model == "boc_tt":
        fx = P["fx"]; boc = P["boc_tt"]
        sell = D(fx["boc_spot_sell_cny_per_usd"]); spread = D(fx["spread_proxy_cny_per_usd"])
        purchase = a * sell
        fee = min(max(purchase * D(boc["commission_rate"]), D(boc["commission_min_cny"])), D(boc["commission_max_cny"])) + D(boc["international_cable_cny"])
        row["fx_spread_proxy_usd"] = q2(a * spread / sell)
        row["sender_fee_cny"] = q2(fee)
        row["sender_fee_usd"] = q2(fee / sell)
    elif model == "sc_tiers":
        for tier, vals in P["sc_electronic_our"]["tiers"].items():
            total = sum(D(v) for v in vals.values())
            row["sc_" + tier + "_cny"] = q2(total)
    return row

def cost_sources(model):
    if model == "boc_tt": return ["S15", "S16"]
    if model == "sc_tiers": return ["S18"]
    return []

def feasibility(route, amount):
    rid = route["id"]
    if route["status"] == "prohibited": return "Prohibited — do not use"
    if route["status"] == "unverified": return "Unverified — no cost populated"
    if route["status"] == "closed_loop": return "Closed-loop investment; not direct US repatriation"
    if rid == "R19": return "Grid amount exceeds the USD 5,000 no-permit carry tier"
    if rid == "R20": return "Bank-permit tier only at USD 10,000; larger grid amounts exceed it" if amount == 10000 else "Exceeds the USD 10,000 bank-permit carry tier"
    if rid == "R21": return "Exceptional SAFE approval only; not routine"
    if rid == "R22": return "CNY 100,000/person/year and CNY 10,000/card/day aggregation; not a scalable wire"
    if rid == "R23": return "Genuine spending only; not cash repatriation"
    if rid == "R32": return "Only if bank classifies person as domestic; USD 50,000/year convenience quota"
    return "Conditional on source, documents, classification and bank review"

GRIDS = {r["id"]: [compute_row(r, a) for a in AMOUNTS] for r in ROUTES}

NAV = [("index.html","Dashboard"),("executive-summary.html","Summary"),("costs.html","Costs"),("tax.html","Tax"),("penalties.html","Penalties"),("sources.html","Sources"),("flagged.html","Flagged"),("audit.html","Audit"),("methodology.html","Method"),("requirements.html","Requirements")]
for c in ROUTES_DOC["categories"]: NAV.append((c["page"], c["name"].split(" and ")[0]))

def page(title, body, active="index.html", desc=None):
    nav = "".join('<a href="{}"{}>{}</a>'.format(esc(h), ' aria-current="page"' if h == active else '', esc(t)) for h, t in NAV)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Edition E</title><meta name="description" content="{esc(desc or title)}">
<link rel="stylesheet" href="assets/style.css"></head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap bar"><a class="brand" href="index.html">CNY → USD <small>Edition E · verified blanks</small></a><nav>{nav}</nav></div></header>
<main id="main" class="wrap">{body}</main>
<footer class="wrap foot"><p>Report date 2026-11-08 UTC. Research, not legal/tax advice or a bank quote. Unknown personal values are blank. <a href="methodology.html">Method</a> · <a href="flagged.html">Flagged</a> · <a href="../EXECUTIVE_SUMMARY.md">Markdown summary</a> · <a href="../../index.html">Repository portal</a> · <a href="../../COORDINATION.md">Coordination</a></p></footer>
</body></html>'''

def table(headers, rows, cls=""):
    h = "".join(f"<th>{x}</th>" for x in headers)
    b = "".join("<tr>"+"".join(r)+"</tr>" for r in rows)
    return f'<div class="tablewrap"><table class="{cls}"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>'

def grid_table(route):
    rows=[]
    for g in GRIDS[route["id"]]:
        if route["cost_model"] == "sc_tiers":
            cells=[f'<td class="num">{g["amount_usd"]:,}</td>', f'<td>{esc(g["feasibility"])}</td>',
                   cell(g["sc_personal_cny"]), cell(g["sc_ease_cny"]), cell(g["sc_priority_cny"]), cell(g["sc_priority_private_cny"]),
                   cell(None), cell(None), cell(None), f'<td>{src_links(g["sources"])}</td>']
            headers=["USD","Feasibility","Personal CNY","Ease CNY","Priority CNY","Private CNY","FX/receiving","Personal tax","All-in total","Sources"]
        else:
            cells=[f'<td class="num">{g["amount_usd"]:,}</td>', f'<td>{esc(g["feasibility"])}</td>',
                   cell(g["fx_spread_proxy_usd"]), cell(g["sender_fee_cny"]), cell(g["sender_fee_usd"]),
                   cell(None), cell(None), cell(None), f'<td>{src_links(g["sources"])}</td>']
            headers=["USD","Feasibility","FX spread proxy USD","Sender fee CNY","Sender fee USD","Receiving fee","Personal tax","All-in total","Sources"]
        rows.append(cells)
    return table(headers, rows, "grid")

def route_card(r):
    pros="".join(f"<li>{esc(x)}</li>" for x in r["pros"]); cons="".join(f"<li>{esc(x)}</li>" for x in r["cons"])
    flags=" ".join(f'<a class="flag" href="flagged.html#{esc(f)}">{esc(f)}</a>' for f in r["flags"])
    return f'''<article class="card route" id="{esc(r['id'])}"><div class="rowhead"><h3>{esc(r['id'])} · {esc(r['name'])}</h3><span class="badge {esc(r['status'])}">{esc(r['status'])}</span></div>
<p><strong>Who:</strong> {esc(r['who'])}</p><p><strong>Mechanism:</strong> {esc(r['mechanism'])}</p>
<p><strong>Limit:</strong> {esc(r['limit'])}</p><p><strong>Documents:</strong> {esc(r['documents'])}</p>
<div class="cols"><div><h4>Pros</h4><ul>{pros}</ul></div><div><h4>Cons</h4><ul>{cons}</ul></div></div>
<p><strong>China tax:</strong> {esc(r['tax_cn'])}</p><p><strong>US tax:</strong> {esc(r['tax_us'])}</p>
<p class="links">{ext_src_links(r['sources'])} {flags}</p><details><summary>Forty amount steps</summary>{grid_table(r)}</details></article>'''

def build_index():
    stats=[("Methods",SUMMARY["headline"]["methods"]),("Amount steps",40),("Grid rows",SUMMARY["headline"]["grid_rows"]),("Sources",len(SOURCES)),("Personal tax","blank"),("All-in total","blank")]
    stat="".join(f'<div class="stat"><small>{esc(k)}</small><strong>{esc(v)}</strong></div>' for k,v in stats)
    findings="".join(f'<article class="card"><h3>{esc(f["title"])}</h3><p>{esc(f["body"])}</p><p>{src_links(f["sources"])}</p></article>' for f in SUMMARY["findings"])
    rows=[]
    for r in ROUTES:
        rows.append([f'<td><a href="{esc(CATS[r["category"]]["page"])}#{esc(r["id"])}">{esc(r["id"])}</a></td>',f'<td>{esc(r["name"])}</td>',f'<td><span class="badge {esc(r["status"])}">{esc(r["status"])}</span></td>',f'<td>{esc(CATS[r["category"]]["name"])}</td>',f'<td>{src_links(r["sources"])}</td>'])
    boc=ROUTES[0]
    sample=[g for g in GRIDS["R01"] if g["amount_usd"] in (10000,50000,100000,200000,400000)]
    srows=[[f'<td class="num">{g["amount_usd"]:,}</td>',cell(g["fx_spread_proxy_usd"]),cell(g["sender_fee_cny"]),cell(g["sender_fee_usd"]),cell(None),cell(None),f'<td>{src_links(g["sources"])}</td>'] for g in sample]
    body=f'''<p class="eyebrow">US citizen · mainland CNY · official rules + provider tariffs</p><h1>What can actually move, and what remains blank.</h1><p class="lede">{esc(SUMMARY['answer'])}</p><div class="stats">{stat}</div>
<div class="notice"><strong>Do not read a computed cell as a quote.</strong> FX is a labelled snapshot proxy; sender tariffs are conditional provider arithmetic. Receiving fees, personal tax and all-in totals are blank because the facts were not supplied.</div>
<h2>Decision fork</h2><div class="grid"><article class="card"><h3>1 · Documented current-account income?</h3><p>Start with Article 59 source/tax evidence and the bank’s classification. <a href="earned.html">Earned routes</a>.</p></article><article class="card"><h3>2 · Real capital transaction?</h3><p>Emigration, inheritance, property sale or corporate liquidation must be genuine. <a href="capital.html">Capital routes</a>.</p></article><article class="card"><h3>3 · Investment or cash/card?</h3><p>Closed-loop investment is not US repatriation; cash/ATM limits are narrow. <a href="investment.html">Investment</a> · <a href="cash.html">Cash/cards</a>.</p></article></div>
<h2>Important findings</h2><div class="grid">{findings}</div>
<h2>Conditional BOC reference rows</h2><p>One international TT, base sender tariff only; optional USD full-arrival surcharge and receiving charges excluded. <a href="costs.html">Full forty-step grids</a>.</p>{table(["USD","FX spread proxy USD","Sender fee CNY","Sender fee USD","Receiving","Personal tax","Sources"],srows)}
<h2>Method directory</h2>{table(["ID","Method","Status","Category","Sources"],rows)}'''
    return page("Dashboard",body,"index.html",SUMMARY["answer"])

def build_summary():
    items="".join(f'<li><strong>{esc(f["title"])}.</strong> {esc(f["body"])} {src_links(f["sources"])}</li>' for f in SUMMARY["findings"])
    body=f'<h1>Executive summary</h1><p class="lede">{esc(SUMMARY["answer"])}</p><ol class="summary">{items}</ol><p><a class="button" href="../EXECUTIVE_SUMMARY.md">Open Markdown version</a></p>'
    return page("Executive summary",body,"executive-summary.html")

def build_category(cat):
    rs=[r for r in ROUTES if r["category"]==cat["id"]]
    body=f'<h1>{esc(cat["name"])}</h1><p class="lede">{esc(cat["intro"])}</p>' + "".join(route_card(r) for r in rs)
    return page(cat["name"],body,cat["page"])

def penalty_table():
    rows=[[f'<td>{esc(p["id"])}</td>',f'<td>{esc(p["jurisdiction"])}</td>',f'<td>{esc(p["conduct"])}</td>',f'<td>{esc(p["statutory_scale"])}</td>',f'<td>{blank()}</td>',f'<td>{src_links(p["sources"])}</td>'] for p in PENALTIES]
    return table(["ID","Jurisdiction","Conduct","Statutory scale","Personal amount","Sources"],rows)

def build_penalties():
    body='<h1>Penalty breakdown</h1><p class="lede">The large numbers in this problem are enforcement/reporting exposure, not a tax on converting principal. No personal penalty is computed.</p>'+penalty_table()
    return page("Penalties",body,"penalties.html")

def build_costs():
    fx=P["fx"]; boc=P["boc_tt"]
    params=[["BOC spot sell",fx["boc_spot_sell_cny_per_usd"]+" CNY/USD",src_links(["S16"])],["BOC spot buy",fx["boc_spot_buy_cny_per_usd"]+" CNY/USD",src_links(["S16"])],["Bid/ask midpoint",fx["bid_ask_midpoint_cny_per_usd"]+" CNY/USD",src_links(["S16"])],["Spread proxy",fx["spread_proxy_cny_per_usd"]+" CNY/USD",src_links(["S16"])],["Treasury reporting",fx["treasury_reporting_cny_per_usd"]+" CNY/USD",src_links(["S17"])],["BOC commission","0.1%, min CNY 50, max CNY 260",src_links(["S15"])],["BOC international cable","CNY 150",src_links(["S15"])],["BOC optional USD full arrival","USD 15 via BOC New York; otherwise USD 25, conditional",src_links(["S15"])]]
    body=f'''<h1>Costs: arithmetic, not quotes</h1><p class="lede">Every method has forty USD 10,000-step rows. Unknown values are blank. Prohibited/unverified routes have no lawful cost scenario.</p>
<h2>Recorded inputs</h2>{table(["Input","Value","Sources"],[[f'<td>{esc(a)}</td>',f'<td>{esc(b)}</td>',f'<td>{c}</td>'] for a,b,c in params])}
<div class="notice">BOC publisher timestamp: {esc(fx['publisher_timestamp'])}; timezone not established; later than report date. Actual transaction rates govern. Treasury rate is a reporting benchmark only.</div>
<h2>Formulas</h2><pre>purchase_CNY = USD × 6.6929
spread_proxy_CNY = USD × 0.01405
spread_proxy_USD = spread_proxy_CNY ÷ 6.6929
BOC_sender_CNY = min(max(purchase_CNY × 0.001, 50), 260) + 150
BOC_sender_USD = BOC_sender_CNY ÷ 6.6929</pre>
<h2>BOC documented current-account TT</h2>{grid_table(ROUTES[0])}
<h2>SC electronic overseas transfer, OUR components</h2>{grid_table(ROUTES[1])}
<h2>Penalty exposure is not a conversion fee</h2><p>Statutory scales below are not personal assessments. Personal penalty amounts are blank.</p>{penalty_table()}
<h2>All method grids</h2><p>Open a category and expand “Forty amount steps” on any method.</p><ul>{''.join(f'<li><a href="{esc(c["page"])}">{esc(c["name"])}</a></li>' for c in ROUTES_DOC["categories"])}</ul>
<p><a class="button" href="data/grids.csv">Download all grids CSV</a> <a class="button" href="data/grids.json">JSON</a></p>'''
    return page("Costs",body,"costs.html")

def build_tax():
    rows=[[f'<td>{esc(t["id"])}</td>',f'<td>{esc(t["jurisdiction"])}</td>',f'<td>{esc(t["item"])}</td>',f'<td>{esc(t["rule"])}</td>',f'<td>{esc(t["rate"]) if t["rate"] else blank()}</td>',f'<td>{blank()}</td>',f'<td>{src_links(t["sources"])}</td>'] for t in TAX]
    body='<h1>Tax and reporting positions</h1><p class="lede">Statutory rules and thresholds are not a personal tax bill. Every personal amount is blank.</p>'+table(["ID","Jurisdiction","Item","Rule","Rate/threshold","Personal amount","Sources"],rows)
    return page("Tax",body,"tax.html")

def build_sources():
    rows=[]
    for s in SOURCES.values():
        rows.append([f'<td id="{esc(s["id"])}">{esc(s["id"])}</td>',f'<td><a href="{esc(s["url"])}" rel="noopener noreferrer" target="_blank">{esc(s["title"])} ↗</a></td>',f'<td>{esc(s["issuer"])}</td>',f'<td>{esc(s["kind"])}</td>',f'<td>{esc(s["locator"])}</td>',f'<td>{esc(s["claim"])}</td>',f'<td>{esc(s["retrieval"])}</td>',f'<td>{esc(s["limitations"])}</td>'])
    body='<h1>Source register</h1><p class="lede">government = issuing authority/regulator/government-hosted text. provider_primary = the provider itself, never labelled government. operator_primary is labelled separately.</p>'+table(["ID","Title/link","Issuer","Kind","Locator","Claim supported","Retrieval","Limitations"],rows)
    return page("Sources",body,"sources.html")

def build_flagged():
    rows=[]
    for f in FLAGS.values():
        routes=" ".join(f'<a href="{esc(CATS[next(r for r in ROUTES if r["id"]==rid)["category"]]["page"])}#{esc(rid)}">{esc(rid)}</a>' for rid in f["routes"]) or "General"
        rows.append([f'<td id="{esc(f["id"])}">{esc(f["id"])}</td>',f'<td>{esc(f["severity"])}</td>',f'<td>{esc(f["title"])}</td>',f'<td>{esc(f["detail"])}</td>',f'<td>{routes}</td>',f'<td>{src_links(f["sources"])}</td>'])
    body='<h1>Flagged for review</h1><p class="lede">Blank values, conflicts, excerpt-only evidence and inherited-edition issues. None is silently filled.</p>'+table(["ID","Severity","Issue","Detail","Routes","Sources"],rows)
    return page("Flagged",body,"flagged.html")

def build_audit():
    rows=[[f'<td>{esc(a["id"])}</td>',f'<td>{esc(a["severity"])}</td>',f'<td>{esc(a["subject"])}</td>',f'<td>{esc(a["finding"])}</td>',f'<td>{esc(a["adjudication"])}</td>',f'<td>{src_links(a["sources"]) if a["sources"] else "Process record"}</td>',f'<td>{"<br>".join(esc(p) for p in a["paths"])}</td>'] for a in AUDIT]
    body='<h1>Inherited-edition audit</h1><p class="lede">Prior editions are preserved. This page adjudicates selected load-bearing claims against the retrieved evidence.</p>'+table(["ID","Severity","Subject","Finding","Adjudication","Sources","Paths"],rows)+'<p><a href="../audit.md">Markdown audit</a></p>'
    return page("Audit",body,"audit.html")

def build_method():
    body='''<h1>Method and limits</h1><ol><li>Read inherited requirements and prior editions without editing them.</li><li>Prefer issuing authority text; label provider tariffs as provider-primary.</li><li>Record locator, proposition, retrieval mode and limitation for each source.</li><li>Leave personal tax, executable FX, receiving fees and unavailable prices blank.</li><li>Compute only transparent Decimal arithmetic from recorded inputs.</li><li>Verify citations, links, blanks, grids and deterministic rebuilds.</li></ol><h2>Known limits</h2><ul><li>No personal facts, bank quote or receiving-bank fee supplied.</li><li>BOC board timestamp is later than report date; timezone unestablished.</li><li>IRS Publication 525 USD 200 tip is official-search-excerpt evidence.</li><li>SAFE 2024 capital section 6.4 was not isolated.</li><li>External links are recorded as retrieved, not continuously monitored.</li></ul><p><a href="../research/README.md">Research record</a> · <a href="../research/retrieval-log.md">Retrieval log</a> · <a href="../research/arithmetic.md">Arithmetic</a></p>'''
    return page("Method",body,"methodology.html")

def build_requirements():
    rows=[["R1–R6","Research routes, pros/cons, cost breakdown, best-route analysis","met","32 methods; category pages; costs/tax/summary"],["R7–R13","Official/provider-primary sourcing, row links, blanks, line-by-line evidence","met","sources.json; row-level links; flagged blanks"],["R14–R18","Requirements, executive summary, repo audit, irregularities","met","this page; summary; audit"],["R19–R25","Live site, clean dashboard, categories, tables, links","met with deployment recorded after merge","site/; verifier; coordination"],["R26–R36","Coordination, claims, small commits, CI, PR/merge, flagged page","met with deployment recorded after merge","COORDINATION.md; edition-e.yml"],["R37–R42","No toolchain risk, no-JS, mobile, reproducible, machine-readable, honest limits","met","stdlib builder; CSS; JSON/CSV; method"]]
    body='<h1>Requirements traceability</h1>'+table(["Requirement","Restatement","Status","Evidence"],[[f'<td>{esc(a)}</td>',f'<td>{esc(b)}</td>',f'<td>{esc(c)}</td>',f'<td>{esc(d)}</td>'] for a,b,c,d in rows])
    return page("Requirements",body,"requirements.html")

def write(rel, content):
    p=SITE/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content,encoding="utf-8")

def main():
    SITE.mkdir(exist_ok=True)
    write("assets/style.css", CSS)
    write("index.html", build_index()); write("executive-summary.html", build_summary())
    for c in ROUTES_DOC["categories"]: write(c["page"], build_category(c))
    write("costs.html", build_costs()); write("tax.html", build_tax()); write("penalties.html", build_penalties()); write("sources.html", build_sources())
    write("flagged.html", build_flagged()); write("audit.html", build_audit()); write("methodology.html", build_method()); write("requirements.html", build_requirements())
    write(".nojekyll","")
    export={"meta":{"edition":"E","report_date":"2026-11-08"},"amounts":AMOUNTS,"routes":ROUTES,"grids":GRIDS,"parameters":P}
    write("data/grids.json", json.dumps(export,ensure_ascii=False,indent=2)+"\n")
    buf=io.StringIO(); w=csv.writer(buf,lineterminator="\n")
    w.writerow(["route_id","amount_usd","status","feasibility","fx_spread_proxy_usd","sender_fee_cny","sender_fee_usd","sc_personal_cny","sc_ease_cny","sc_priority_cny","sc_priority_private_cny","receiving_fee_usd","personal_tax_usd","all_in_total_usd","sources"])
    for r in ROUTES:
        for g in GRIDS[r["id"]]:
            w.writerow([g["route_id"],g["amount_usd"],g["status"],g["feasibility"],g["fx_spread_proxy_usd"],g["sender_fee_cny"],g["sender_fee_usd"],g["sc_personal_cny"],g["sc_ease_cny"],g["sc_priority_cny"],g["sc_priority_private_cny"],g["receiving_fee_usd"],g["personal_tax_usd"],g["all_in_total_usd"],"|".join(g["sources"])])
    write("data/grids.csv",buf.getvalue())
    print(f"edition-e: wrote {len(list(SITE.rglob('*.html')))} HTML pages, {len(ROUTES)*len(AMOUNTS)} grid rows")

CSS = '''
:root{--ink:#101820;--muted:#5b6673;--line:#dfe5ec;--bg:#f5f7fa;--panel:#fff;--accent:#0b5cad;--ok:#0f6b4f;--warn:#8a5a00;--bad:#9b1c1c}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}a{color:var(--accent)}.wrap{max-width:1180px;margin:0 auto;padding:0 16px}.top{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}.bar{display:flex;gap:12px;align-items:center;justify-content:space-between;padding-top:10px;padding-bottom:10px;flex-wrap:wrap}.brand{font-weight:800;text-decoration:none;color:var(--ink)}.brand small{display:block;font-weight:500;color:var(--muted);font-size:.72rem}nav{display:flex;gap:8px;flex-wrap:wrap;font-size:.82rem}nav a{text-decoration:none;padding:4px 6px;border-radius:6px}nav a[aria-current]{background:#e8f0fb;font-weight:700}main{padding-top:22px;padding-bottom:40px}h1{font-size:clamp(1.7rem,4vw,2.5rem);line-height:1.15;margin:.2em 0}.lede{font-size:1.05rem;color:var(--muted);max-width:75ch}.eyebrow{text-transform:uppercase;letter-spacing:.1em;font-size:.72rem;color:var(--accent);font-weight:700}.stats{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:18px 0}.stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px}.stat small{display:block;color:var(--muted);text-transform:uppercase;font-size:.68rem;letter-spacing:.08em}.stat strong{font-size:1.35rem}.grid{display:grid;grid-template-columns:1fr;gap:12px}.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px;margin:12px 0}.card h3{margin:.1em 0 .4em}.notice{background:#fff7e6;border:1px solid #f0d9a8;border-radius:12px;padding:12px;margin:14px 0}.tablewrap{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:12px;margin:12px 0}table{border-collapse:collapse;width:100%;font-size:.84rem;min-width:720px}th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{background:#eef2f7;font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}.num{text-align:right;white-space:nowrap}.src,.flag{display:inline-block;font-size:.7rem;border:1px solid var(--line);border-radius:5px;padding:1px 5px;margin:1px;text-decoration:none;background:#f6f8fb}.flag{background:#fff7e6}.blank{color:var(--muted);font-style:italic}.badge{font-size:.7rem;border-radius:999px;padding:2px 8px;border:1px solid var(--line);white-space:nowrap}.badge.conditional{background:#e8f0fb}.badge.approval{background:#fff7e6}.badge.closed_loop{background:#eef}.badge.prohibited{background:#fde8e8;color:var(--bad)}.badge.unverified{background:#eee}.rowhead{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}.cols{display:grid;grid-template-columns:1fr;gap:8px}.button{display:inline-block;background:var(--accent);color:#fff;padding:8px 12px;border-radius:8px;text-decoration:none;margin:4px 4px 4px 0}pre{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px;overflow:auto}.foot{border-top:1px solid var(--line);padding-top:14px;padding-bottom:30px;color:var(--muted);font-size:.82rem}.skip{position:absolute;left:-9999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:10}.sr{position:absolute;left:-9999px}summary{cursor:pointer;font-weight:700;margin:8px 0}@media(min-width:760px){.stats{grid-template-columns:repeat(6,1fr)}.grid{grid-template-columns:repeat(3,1fr)}.cols{grid-template-columns:1fr 1fr}}@media(max-width:600px){nav{font-size:.75rem}table{font-size:.78rem}}
'''
if __name__=="__main__": main()
