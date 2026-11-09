#!/usr/bin/env python3
"""Build Edition H data and static pages using only Python's standard library.

Numeric cells are copied from registered primary sources or calculated with the
published formulas below. Unknown values stay JSON null and render as a blank
plus UNVERIFIED. N/A is reserved for non-executable/non-applicable candidates.
"""
from __future__ import annotations
import csv
import html
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SITE = ROOT / "site"
SITE.mkdir(parents=True, exist_ok=True)
TARGETS = list(range(10000, 400001, 10000))
RATE = Decimal("6.6919")  # BOC USD100 telegraphic/cash ask 669.19, 2026-11-09 09:15:45.
E = html.escape


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


SOURCES = {s["id"]: s for s in load("sources.json")["sources"]}
METHOD_DOC = load("methods.json")
METHODS = METHOD_DOC["methods"]
CATEGORIES = METHOD_DOC["categories"]
FLAGS = {f["id"]: f for f in load("flags.json")["flags"]}
TAXES = load("taxes.json")["positions"]
PENALTY = load("penalty.json")["layers"]
SUMMARY = load("summary.json")
REVIEW = load("repo-review.json") if (DATA / "repo-review.json").exists() else {"findings": [], "stats": {}}
WISE_QUOTES = [
    {"source_cny": 66929, "bank_fee": Decimal("436.18"), "balance_fee": Decimal("419.89"), "discount": None, "source": "S21"},
    {"source_cny": 133858, "bank_fee": Decimal("848.58"), "balance_fee": Decimal("832.29"), "discount": None, "source": "S22"},
    {"source_cny": 200787, "bank_fee": Decimal("1228.50"), "balance_fee": Decimal("1212.20"), "discount": Decimal("32.69"), "source": "S23"},
    {"source_cny": 267716, "bank_fee": Decimal("1574.72"), "balance_fee": Decimal("1558.43"), "discount": Decimal("99.27"), "source": "S24"},
]


def d2(x):
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def num(x):
    if x is None:
        return None
    return float(d2(x))


def fee_formula(profile, amount):
    """Return a row's verified/derived fields and an explicit scope note."""
    p = RATE * amount
    out = {
        "cny_estimate": None, "sender_cny": None, "sender_usd": None,
        "known_subtotal_usd": None, "charge_text": None, "note": "",
        "status": "unverified", "extra_sources": [],
    }
    if profile in {"boc_tt", "boc_tt_scenario", "boc_tt_quota", "boc_tt_already_fx"}:
        commission = min(Decimal(260), max(Decimal(50), p * Decimal("0.001")))
        fee = d2(commission + 150)
        if profile != "boc_tt_already_fx":
            out["cny_estimate"] = num(p)
        else:
            out["note"] = "Already foreign currency: no CNY purchase is modeled. Fee base is the USD-equivalent remittance. "
        out.update(sender_cny=num(fee), sender_usd=num(fee / RATE), known_subtotal_usd=num(fee / RATE), status="partial-estimate")
        out["note"] += "Conditional BOC TT: min(260,max(50,0.1%×CNY-equivalent principal))+CNY150 cable. USD conversion uses the same indicative ask. Excludes optional full-arrival USD15/25, other-bank charges, documents and tax."
        out["extra_sources"] = ["S14", "S16"]
        if profile == "boc_tt_scenario":
            out["note"] = "Chosen-rail scenario, not an entitlement surcharge. " + out["note"]
        if profile == "boc_tt_quota" and amount > 50000:
            out.update(sender_cny=None, sender_usd=None, known_subtotal_usd=None, status="not-applicable")
            out["note"] = "Exceeds the USD50,000 annual facilitation quota in one calendar year. No quota splitting is modeled. Above-quota genuine current-account expenditure is a different route (P09)."
        return out
    if profile == "boc_draft":
        fee = d2(min(Decimal(260), max(Decimal(50), p * Decimal("0.001"))))
        out.update(cny_estimate=num(p), sender_cny=num(fee), sender_usd=num(fee / RATE), known_subtotal_usd=num(fee / RATE), status="partial-estimate")
        out["note"] = "BOC demand-draft commission only: min(260,max(50,0.1%×P)). Postage, foreign collection, stop-payment and receiving charges are extra/unknown."
        out["extra_sources"] = ["S14", "S16"]
        return out
    if profile == "hsbc_tt_paid":
        fee = d2(min(Decimal(500), max(Decimal(100), p * Decimal("0.001"))) + 120)
        out.update(sender_cny=num(fee), sender_usd=num(fee / RATE), known_subtotal_usd=num(fee / RATE), status="partial-estimate")
        out["note"] = "HSBC Premier/Advance TT: min(500,max(100,0.1%×P))+CNY120 cable. CNY principal is blank because HSBC's executable FX rate was not captured; USD fee equivalent uses BOC's ask only for comparability."
        out["extra_sources"] = ["S18", "S19", "S16"]
        return out
    if profile == "hsbc_tt_private":
        out.update(sender_cny=0.0, sender_usd=0.0, known_subtotal_usd=0.0, status="partial-estimate")
        out["note"] = "HSBC Private Banking individual TT commission and cable are published as free. This is not zero total cost: FX, third-party charges, eligibility and relationship costs remain."
        out["extra_sources"] = ["S18", "S19"]
        return out
    if profile == "hsbc_global":
        out["charge_text"] = "USD0 PB/Premier; USD20 Advance per transfer"
        out["note"] = "Number of transfers N is unknown, so total is blank. CNY must first be lawfully converted using an HSBC executable rate; this rail does not create entitlement."
        out["extra_sources"] = ["S18", "S19"]
        return out
    if profile == "wise_bank":
        out["note"] = "No amount-specific current quote was verified for this exact grid cell. Four directly observed public quotes are shown on the Costs page and are not extrapolated. Bank-app cap CNY300,000 per transfer; overall limit depends on tax records."
        out["extra_sources"] = ["S20", "S21", "S22", "S23", "S24"]
        return out
    if profile == "wise_alipay":
        out["note"] = "Alipay funding cap CNY50,000 per transfer; current amount-specific fee and required transfer count are unverified. Overall eligibility and tax-record limits apply."
        out["extra_sources"] = ["S20"]
        return out
    if profile == "boc_atm":
        out["charge_text"] = "Per withdrawal: min(CNY112, CNY12 + 1%×withdrawal)"
        out["note"] = "Total is blank because withdrawal count, card/network, ATM surcharge and actual FX are unknown. Current tariff is used; announced 2026-11-11 changes are not applied early. Annual person cap CNY100,000 and daily card cap CNY10,000."
        out["extra_sources"] = ["S14", "S15", "S28"]
        if p > 100000:
            out["status"] = "not-applicable"
            out["note"] = "Exceeds SAFE's CNY100,000 per-person annual overseas ATM withdrawal cap. " + out["note"]
        return out
    if profile == "hsbc_atm":
        out["charge_text"] = "Premier HSBC ATM 0; UnionPay min(CNY110, CNY20 + 1%×withdrawal)"
        out["note"] = "Total is blank because withdrawal count, network/segment, surcharge and actual FX are unknown. Annual person cap CNY100,000 and daily card cap CNY10,000."
        out["extra_sources"] = ["S18", "S28"]
        if p > 100000:
            out["status"] = "not-applicable"
            out["note"] = "Exceeds SAFE's CNY100,000 per-person annual overseas ATM withdrawal cap. " + out["note"]
        return out
    if profile == "cash_permit":
        out.update(cny_estimate=num(p), sender_cny=0.0, sender_usd=0.0, known_subtotal_usd=0.0, status="partial-estimate")
        out["note"] = "BOC cash-selling-rate scenario; carry-permit fee CNY0 during the published waiver through 2026-12-31. Zero is the permit fee only, not conversion, transport, U.S. deposit or tax. Above USD10,000 requires a special-case SAFE permit; U.S. FinCEN 105 applies over USD10,000."
        out["extra_sources"] = ["S14", "S16", "S53", "S30"]
        return out
    if profile == "rail_required":
        out["note"] = "Legal/entity route only. No personal-bank tariff is assumed for an entity. Select and price the actual bank rail after eligibility, tax and registration review."
        return out
    if profile == "none":
        out["status"] = "not-applicable"
        out["note"] = "Not an executable CNY-to-USD repatriation route, or deliberately not priced because prohibited/not applicable. No cost estimate is appropriate."
        return out
    out["note"] = "No current amount-specific fee schedule or executable quote was verified. Unknown cells remain blank."
    return out


def build_costs():
    rows = []
    for m in METHODS:
        for target in TARGETS:
            x = fee_formula(m["cost_profile"], Decimal(target))
            sources = list(dict.fromkeys(m["sources"] + x.pop("extra_sources")))
            rows.append({
                "method_id": m["id"], "target_usd_equivalent": target,
                **x,
                "fx_cost_usd": None, "downstream_usd": None,
                "documentation_usd": None, "tax_usd": None, "all_in_usd": None,
                "all_in_status": "unverified", "sources": sources,
                "flags": sorted(set(m["flags"] + ["F52"])),
            })
    doc = {
        "_meta": {
            "edition": "H", "researched_utc": "2026-11-09",
            "targets_usd_equivalent": TARGETS,
            "amount_definition": "USD-equivalent gross principal before fees, not guaranteed net receipt.",
            "boc_observation": {"usd100_bid_cny": 666.38, "usd100_ask_cny": 669.19, "usd100_reference_cny": 671.88, "published": "2026-11-09 09:15:45 China time", "source": "S16", "cny_per_usd_ask": float(RATE)},
            "policy": "Known charges are sourced or derived by printed formulas. FX cost, downstream, documents, personal tax and all-in totals are null unless confirmed. Blank is unverified, never zero. N/A is not a blank.",
            "wise_observed_quotes": [{**q, "bank_fee": num(q["bank_fee"]), "balance_fee": num(q["balance_fee"]), "discount": num(q["discount"]) if q["discount"] is not None else None, "observed_utc": "2026-11-09"} for q in WISE_QUOTES],
        }, "rows": rows,
    }
    (DATA / "costs.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with (SITE / "cost-ladder.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["method_id", "target_usd_equivalent", "cny_estimate", "sender_cny", "sender_usd", "known_subtotal_usd", "charge_text", "status", "fx_cost_usd", "downstream_usd", "documentation_usd", "tax_usd", "all_in_usd", "all_in_status", "note", "sources"]
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "sources": " ".join(r["sources"])})
    return doc


COSTS = build_costs()
ROWS = {}
for row in COSTS["rows"]:
    ROWS.setdefault(row["method_id"], []).append(row)


def src_links(ids):
    return '<span class="sources">' + " ".join(f'<a href="{E(SOURCES[s]["url"])}" rel="noopener" title="{E(SOURCES[s]["title"])}">{E(s)} · {E(SOURCES[s]["issuer"])}</a>' for s in ids) + "</span>"


def flag_links(ids):
    return " ".join(f'<a class="badge flag" href="flagged.html#{E(i)}">{E(i)}</a>' for i in ids)


def blank(reason="Unverified"):
    return f'<span class="blank" title="{E(reason)}" aria-label="Blank, unverified"></span><span class="badge unverified">UNVERIFIED</span>'


def money(v, currency="USD"):
    if v is None:
        return blank()
    return f"{E(currency)} {v:,.2f}"


def status_badge(status):
    labels = {"partial-estimate": "PARTIAL ESTIMATE", "unverified": "UNVERIFIED", "not-applicable": "N/A"}
    cls = "ok" if status == "partial-estimate" else ("na" if status == "not-applicable" else "unverified")
    return f'<span class="badge {cls}">{labels.get(status, E(status))}</span>'


CSS = r"""
:root{--navy:#102a43;--blue:#1769aa;--teal:#087f5b;--ink:#172b3a;--muted:#5c6f7c;--bg:#f4f7fa;--card:#fff;--line:#d9e2ec;--warn:#8a4b00;--warnbg:#fff4d6;--bad:#9b1c1c;--badbg:#fee2e2}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.58 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}a{color:var(--blue);text-underline-offset:2px}.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:20}
header{background:var(--navy);color:#fff;padding:18px 16px}header a{color:#fff;text-decoration:none}.brand{font-size:1.15rem;font-weight:800}.subtitle{display:block;color:#d9eaf7;font-size:.85rem;margin-top:3px}nav{display:flex;gap:6px;overflow-x:auto;padding:10px 12px;background:#fff;border-bottom:1px solid var(--line);white-space:nowrap}nav a{text-decoration:none;padding:7px 10px;border-radius:8px;font-size:.88rem}nav a[aria-current]{background:var(--navy);color:#fff}main{max-width:1180px;margin:auto;padding:20px 14px 64px}h1{font-size:clamp(1.55rem,4vw,2.25rem);line-height:1.18;margin:.15em 0 .45em}h2{font-size:1.35rem;line-height:1.25;margin-top:1.8em}h3{font-size:1.08rem}p{max-width:85ch}.hero{padding:26px 20px;background:linear-gradient(135deg,#102a43,#1769aa);color:#fff;border-radius:16px}.hero a{color:#fff}.hero p{max-width:75ch}.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin:12px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}.kpi{font-size:1.7rem;font-weight:800;color:var(--teal)}.muted,small{color:var(--muted)}small{display:block;font-size:.78rem}.notice{border-left:5px solid #d97706;background:var(--warnbg);padding:12px 14px;border-radius:8px;margin:14px 0}.danger{border-left-color:var(--bad);background:var(--badbg)}.good{border-left-color:var(--teal);background:#e7f6ef}
.badge{display:inline-block;border-radius:5px;padding:2px 6px;font-size:.68rem;font-weight:800;letter-spacing:.02em;vertical-align:middle}.unverified{background:var(--warnbg);color:var(--warn)}.ok{background:#d9f2e5;color:#096542}.na{background:#e5e7eb;color:#374151}.flag{background:#e0effe;color:#175d91;text-decoration:none}.blank{display:inline-block;width:2.6em;border-bottom:2px dotted var(--warn);height:1em;margin-right:5px}.sources a{display:inline-block;font-size:.74rem;margin:2px 7px 2px 0}.steps li,.tight li{margin:.45em 0}.table-wrap{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:10px;margin:12px 0;-webkit-overflow-scrolling:touch}table{border-collapse:collapse;width:100%;font-size:.87rem}th,td{text-align:left;vertical-align:top;padding:10px;border-top:1px solid var(--line)}th{background:#eaf0f5;font-size:.73rem;text-transform:uppercase;letter-spacing:.035em}tbody tr:hover{background:#f8fafc}.num{white-space:nowrap;font-variant-numeric:tabular-nums}.method-links{display:flex;flex-wrap:wrap;gap:8px}.method-links a,.button{display:inline-block;background:var(--navy);color:#fff;text-decoration:none;padding:8px 12px;border-radius:8px}.toc{columns:2;column-gap:24px}.toc a{display:block;break-inside:avoid;padding:4px 0}.proscons{display:grid;grid-template-columns:1fr 1fr;gap:12px}footer{border-top:1px solid var(--line);padding:20px 14px;text-align:center;color:var(--muted);font-size:.83rem}.check{color:var(--teal);font-weight:700}.warning{color:var(--warn);font-weight:700}
@media(max-width:680px){main{padding:14px 10px 48px}.hero{padding:20px 15px}.proscons{grid-template-columns:1fr}.toc{columns:1}.responsive thead{position:absolute;left:-9999px}.responsive,.responsive tbody,.responsive tr,.responsive td{display:block;width:100%}.responsive tr{border-top:8px solid var(--line);padding:8px 0}.responsive tr:first-child{border-top:0}.responsive td{border:0;padding:6px 10px 6px 46%;position:relative;min-height:28px}.responsive td::before{content:attr(data-label);position:absolute;left:10px;top:6px;width:32%;font-size:.7rem;font-weight:800;text-transform:uppercase;color:var(--muted)}.responsive td:first-child{font-size:1.05rem;background:#f1f5f9}.table-wrap{border:0;overflow:visible;background:transparent}th,td{padding:8px}.kpi{font-size:1.4rem}}
@media print{header,nav,footer{display:none}main{max-width:none}.table-wrap{overflow:visible}.responsive thead{position:static}.responsive tr{display:table-row}.responsive td{display:table-cell}.responsive td::before{display:none}}
"""

NAV = [
    ("index.html", "Overview"), ("executive-summary.html", "Summary"),
    ("costs.html", "Costs"), ("category-personal.html", "Personal"),
    ("category-rails.html", "Rails"), ("category-business.html", "Business"),
    ("category-alternatives.html", "Alternatives"), ("category-rejected.html", "Rejected"),
    ("taxes.html", "Tax & reporting"), ("penalty.html", "Penalty layers"),
    ("sources.html", "Sources"), ("flagged.html", "Flagged for Review"),
    ("repo-review.html", "Repo audit"), ("requirements.html", "Requirements"),
    ("methodology.html", "Methodology"),
]


def page(slug, title, body):
    nav_items = []
    for href, label in NAV:
        current = ' aria-current="page"' if href == slug else ""
        nav_items.append(f'<a href="{href}"{current}>{E(label)}</a>')
    nav = "".join(nav_items)
    doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Verified CNY to USD routes, conditional cost estimates, China and U.S. tax analysis"><title>{E(title)} · China Money · Edition H</title><link rel="stylesheet" href="assets/style.css"></head><body><a class="skip" href="#main">Skip to content</a><header><a class="brand" href="index.html">China Money · Edition H</a><span class="subtitle">CNY → USD · official-source review 2026-11-09 · additive independent edition</span></header><nav aria-label="Main navigation">{nav}</nav><main id="main">{body}</main><footer>Blank = unverified, never zero · N/A = not applicable · Partial estimates are not all-in quotes.<br>Educational research, not individualized legal, tax, investment or immigration advice. Earlier editions remain unchanged; see <a href="repo-review.html">repo audit</a>.</footer></body></html>'''
    (SITE / slug).write_text(doc, encoding="utf-8")


def method_link(m):
    return f'<a href="method-{m["id"]}.html">{E(m["id"])} · {E(m["name"])}</a>'


def overview_table():
    ids = ["P01", "R01", "R03", "R04", "R05", "R06", "R08"]
    trs = []
    for mid in ids:
        m = next(x for x in METHODS if x["id"] == mid)
        r10, r400 = ROWS[mid][0], ROWS[mid][-1]
        def charge(r):
            if r["known_subtotal_usd"] is not None:
                return money(r["known_subtotal_usd"])
            if r["charge_text"]:
                return E(r["charge_text"])
            if r["status"] == "not-applicable":
                return "N/A"
            return blank()
        trs.append(f'<tr><td data-label="Route">{method_link(m)}<small>{E(m["status"])}</small></td><td data-label="USD10k known charge">{charge(r10)}</td><td data-label="USD400k known charge">{charge(r400)}</td><td data-label="Scope">Partial only; all-in blank.<small>{flag_links(r400["flags"])}</small></td><td data-label="Sources">{src_links(r400["sources"])}</td></tr>')
    return '<div class="table-wrap"><table class="responsive"><thead><tr><th>Route</th><th>USD10k known charge</th><th>USD400k known charge</th><th>Scope</th><th>Sources</th></tr></thead><tbody>' + "".join(trs) + '</tbody></table></div>'


def build_index():
    findings = "".join(f'<article class="card"><h3>{E(f["title"])}</h3><p>{E(f["detail"])}</p>{src_links(f["sources"])}</article>' for f in SUMMARY["findings"][:4])
    body = f'''<section class="hero"><h1>Move money from China with the least avoidable cost—lawfully.</h1><p>{E(SUMMARY["headline"])}</p><p><a class="button" href="executive-summary.html">Read the recommendation</a> <a class="button" href="costs.html">Compare all 40 amounts</a></p></section>
<div class="notice"><strong>Most important:</strong> a wire of your own after-tax principal is not automatically a new China tax. The large cost usually comes from unresolved source-of-funds/tax evidence, not a universal “CNY conversion penalty.” No personal all-in total can be verified from the supplied facts.</div>
<div class="grid"><div class="card"><span class="kpi">43</span><br>candidates, including rejected and adjacent options</div><div class="card"><span class="kpi">1,720</span><br>cost rows: 43 × 40 USD-equivalent amounts</div><div class="card"><span class="kpi">CNY 6.6919</span><br>BOC indicative ask per USD1, timestamped—not executable</div><div class="card"><span class="kpi">{len(FLAGS)}</span><br>published review flags; unknowns are not hidden</div></div>
<h2>Known-charge comparison</h2><p>Known charges only. They exclude FX-benchmark differences, intermediary/receiver charges, documents and tax. A legal entitlement and its execution rail are alternatives, not costs to add twice.</p>{overview_table()}
<h2>What the evidence says</h2><div class="grid">{findings}</div>
<h2>Start in the right category</h2><div class="method-links"><a href="category-personal.html">Personal entitlements</a><a href="category-rails.html">Banks & transfer rails</a><a href="category-business.html">Business & assets</a><a href="category-alternatives.html">Adjacent alternatives</a><a href="category-rejected.html">Rejected options</a></div>'''
    page("index.html", "Overview", body)


def build_summary():
    order = "".join(f"<li>{E(x)}</li>" for x in SUMMARY["decision_order"])
    findings = "".join(f'<tr><td data-label="Finding"><strong>{E(f["title"])}</strong><br>{E(f["detail"])}</td><td data-label="Sources">{src_links(f["sources"])}</td></tr>' for f in SUMMARY["findings"])
    body = f'''<h1>Executive summary</h1><div class="notice good"><strong>Best available answer:</strong> if the balance is lawful, documented, after-tax current-account RMB income of a U.S. passport holder, use SAFE's overseas-individual current-income purchase/remittance process (P01), then compare executable BOC, HSBC and eligible Wise quotes. If it is not current income, do not relabel it: use the matching property, inheritance, insurance or business route.</div>
<h2>Recommended sequence</h2><ol class="steps">{order}</ol>
<h2>Cost answer in plain English</h2><ul><li><strong>BOC standard TT scenario:</strong> CNY216.92 (USD32.42) at USD10,000 and CNY410.00 (USD61.27) at USD400,000. Published 0.1% commission is capped, so the known sender fee stops rising at USD40,000 in this scenario.</li><li><strong>HSBC Premier/Advance TT:</strong> CNY220.00 (USD32.88) at USD10,000 and CNY620.00 (USD92.65) at USD400,000, with the USD figures converted at BOC's ask only for comparability.</li><li><strong>HSBC Private Banking:</strong> published individual TT commission/cable is zero, but eligibility, FX and third-party charges are not zero.</li><li><strong>Wise:</strong> four observed public bank-fee examples range from CNY436.18 to CNY1,574.72. They are point-in-time source-amount quotes, not a formula or a guaranteed 40-row schedule.</li><li><strong>Not included:</strong> live FX difference, intermediary/receiving-bank charges, notarization/translation, underlying income tax and U.S. tax. Therefore no honest all-in total is available.</li></ul><p>{src_links(['S03','S14','S16','S18','S20','S21','S22','S23','S24'])}</p>
<h2>Findings register</h2><div class="table-wrap"><table class="responsive"><thead><tr><th>Finding</th><th>Official / primary sources</th></tr></thead><tbody>{findings}</tbody></table></div>
<div class="notice danger"><strong>Avoid:</strong> borrowing quotas, underground banks, fabricated trade, or crypto/stablecoin bridges. Besides legal exposure, these can destroy the documentation trail needed for future banking and U.S. reporting. {src_links(['S01','S03','S45'])}</div>'''
    page("executive-summary.html", "Executive summary", body)


def build_categories():
    for c in CATEGORIES:
        ms = [m for m in METHODS if m["category"] == c["id"]]
        trs = []
        for m in ms:
            trs.append(f'<tr><td data-label="Candidate">{method_link(m)}<small>{E(m["kind"])} · {E(m["status"])}</small></td><td data-label="Analysis"><strong>Pros:</strong> {E(" ".join(m["pros"]))}<br><strong>Cons:</strong> {E(" ".join(m["cons"]))}</td><td data-label="Sources">{src_links(m["sources"])}</td></tr>')
        body = f'<h1>{E(c["title"])}</h1><p>{E(c["description"])}</p><div class="notice">Every candidate has its own step-by-step page and 40-row cost grid. Prohibited candidates have risk information but no execution instructions.</div><div class="table-wrap"><table class="responsive"><thead><tr><th>Candidate</th><th>Pros & cons</th><th>Sources</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div>'
        page(c["page"], c["title"], body)


def charge_cell(r):
    if r["charge_text"]:
        return E(r["charge_text"])
    if r["sender_cny"] is not None:
        usd = money(r["sender_usd"]) if r["sender_usd"] is not None else ""
        return f'{money(r["sender_cny"], "CNY")}<small>≈ {usd} using stated comparison rate</small>'
    if r["status"] == "not-applicable":
        return "N/A"
    return blank("No amount-specific provider charge verified")


def build_methods():
    for m in METHODS:
        rows = ROWS[m["id"]]
        trs = []
        for r in rows:
            cny = money(r["cny_estimate"], "CNY") if r["cny_estimate"] is not None else ("N/A" if m["id"] == "P07" else blank("No provider-specific CNY quote"))
            subtotal = money(r["known_subtotal_usd"]) if r["known_subtotal_usd"] is not None else ("N/A" if r["status"] == "not-applicable" else blank("Known subtotal unavailable"))
            trs.append(f'<tr><td data-label="USD-equivalent" class="num">USD {r["target_usd_equivalent"]:,}</td><td data-label="CNY principal scenario">{cny}</td><td data-label="Published / derived charge">{charge_cell(r)}</td><td data-label="Known subtotal">{subtotal}<small>Not all-in</small></td><td data-label="All-in total">{blank("FX, downstream, documents and/or tax unknown")}</td><td data-label="Status & scope">{status_badge(r["status"])}<small>{E(r["note"])}</small>{flag_links(r["flags"])}</td><td data-label="Sources">{src_links(r["sources"])}</td></tr>')
        steps = "".join(f"<li>{E(s)}</li>" for s in m.get("steps", [])) or "<li>No execution instructions are provided for this prohibited or non-applicable candidate.</li>"
        eligibility = "".join(f"<li>{E(s)}</li>" for s in m.get("eligibility", []))
        pros = "".join(f"<li>{E(s)}</li>" for s in m["pros"])
        cons = "".join(f"<li>{E(s)}</li>" for s in m["cons"])
        body = f'''<p><a href="{next(c["page"] for c in CATEGORIES if c["id"] == m["category"])}">← {E(next(c["title"] for c in CATEGORIES if c["id"] == m["category"]))}</a></p><h1>{E(m["id"])} · {E(m["name"])}</h1><p><span class="badge na">{E(m["status"])}</span> <span class="badge flag">{E(m["kind"])}</span></p><div class="card"><p>{E(m["summary"])}</p>{src_links(m["sources"])}</div>
<h2>Step by step</h2><ol class="steps">{steps}</ol>{("<h2>Eligibility / conditions</h2><ul>" + eligibility + "</ul>") if eligibility else ""}<div class="proscons"><section class="card"><h2>Pros</h2><ul>{pros}</ul></section><section class="card"><h2>Cons</h2><ul>{cons}</ul></section></div>
<h2>Costs at every USD10,000 increment</h2><div class="notice"><strong>Amount means gross USD-equivalent principal, not guaranteed net receipt.</strong> Blank values are unverified. Known subtotals include only the printed charge; all-in totals remain blank. <a href="cost-ladder.csv">Download the full CSV</a>.</div><div class="table-wrap"><table class="responsive"><thead><tr><th>USD-equivalent</th><th>CNY principal scenario</th><th>Published / derived charge</th><th>Known subtotal</th><th>All-in total</th><th>Status & scope</th><th>Sources</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div>'''
        page(f'method-{m["id"]}.html', f'{m["id"]} {m["name"]}', body)


def build_costs_page():
    trs = []
    for m in METHODS:
        r10, r400 = ROWS[m["id"]][0], ROWS[m["id"]][-1]
        def short(r):
            if r["known_subtotal_usd"] is not None:
                return money(r["known_subtotal_usd"])
            if r["charge_text"]:
                return E(r["charge_text"])
            return "N/A" if r["status"] == "not-applicable" else blank()
        trs.append(f'<tr><td data-label="Method">{method_link(m)}<small>{E(m["status"])}</small></td><td data-label="USD10k known">{short(r10)}</td><td data-label="USD400k known">{short(r400)}</td><td data-label="All-in">{blank("Not verifiable")}</td><td data-label="Sources">{src_links(m["sources"])}</td></tr>')
    qrows = "".join(f'<tr><td data-label="Source CNY">CNY {q["source_cny"]:,}</td><td data-label="Bank-app fee">CNY {q["bank_fee"]:,.2f}</td><td data-label="Wise-balance fee">CNY {q["balance_fee"]:,.2f}</td><td data-label="Discount">{("CNY " + format(q["discount"], ",.2f")) if q["discount"] is not None else "N/A"}</td><td data-label="Source">{src_links([q["source"]])}</td></tr>' for q in WISE_QUOTES)
    body = f'''<h1>Cost explorer</h1><div class="notice"><strong>Most important first:</strong> click any method for all 40 rows from USD10,000 through USD400,000. Figures below are known/partial charges, not all-in totals. Blank means unverified; zero appears only where a tariff explicitly says free.</div><h2>Methods at the lowest and highest requested amounts</h2><div class="table-wrap"><table class="responsive"><thead><tr><th>Method</th><th>USD10k known</th><th>USD400k known</th><th>All-in</th><th>Sources</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div>
<h2>Directly observed Wise public quotes</h2><p>Observed 2026-11-09. Source CNY includes the fee. Public pages display a rounded 1 CNY = 0.1498 USD. These examples are not extrapolated, not locked quotes, and do not override Wise eligibility or its CNY300,000 bank-app/CNY50,000 Alipay per-transfer caps. {src_links(['S20'])}</p><div class="table-wrap"><table class="responsive"><thead><tr><th>Source CNY</th><th>Bank-app fee</th><th>Wise-balance fee</th><th>Displayed discount</th><th>Source</th></tr></thead><tbody>{qrows}</tbody></table></div>
<h2>Arithmetic used for BOC scenario</h2><div class="card"><p><strong>P = USD-equivalent × 6.6919.</strong> BOC TT sender fee = min(CNY260, max(CNY50, 0.001×P)) + CNY150. USD fee equivalent = CNY fee ÷ 6.6919. The BOC board says actual transaction rates control, so this is a reproducible estimate, not a guaranteed receipt or measured spread.</p>{src_links(['S14','S16'])}</div><p><a class="button" href="cost-ladder.csv">Download all 1,720 rows (CSV)</a></p>'''
    page("costs.html", "Cost explorer", body)


def build_taxes():
    trs = "".join(f'<tr><td data-label="Topic"><strong>{E(t["id"])} · {E(t["topic"])}</strong><small>{E(t["jurisdiction"])}</small></td><td data-label="Position">{E(t["position"])}</td><td data-label="Rate / threshold">{E(t["rate"]) if t["rate"] else blank("No universal personal rate")}</td><td data-label="Sources">{src_links(t["sources"])}<br>{flag_links(t["flags"])}</td></tr>' for t in TAXES)
    body = f'''<h1>China and U.S. tax & reporting</h1><div class="notice"><strong>Tax follows the income, not the wire.</strong> Moving your own principal does not automatically create a new tax, but the original salary, rent, dividend, property sale, gift or FX gain can matter. A foreign tax credit is not an automatic full offset.</div><div class="table-wrap"><table class="responsive"><thead><tr><th>Topic</th><th>Verified position</th><th>Rate / threshold</th><th>Sources & flags</th></tr></thead><tbody>{trs}</tbody></table></div><h2>Practical U.S. compliance checklist</h2><ol class="steps"><li>Reconstruct annual maximum CNY balances and convert for FBAR using the required year-end rate; aggregate accounts exceed USD10,000 triggers FinCEN Form 114.</li><li>Check Form 8938 separately using residence, filing status and year-end/anytime thresholds.</li><li>Report worldwide income and analyze any personal FX gain using acquisition basis and dates; USD200 is a transaction threshold, not a deduction.</li><li>Keep China tax receipts and evaluate Form 1116. Treaty-reduced rates and FEIE interactions require care.</li><li>For genuine foreign gifts/bequests, check Form 3520. Do not relabel your own existing balance as a gift.</li></ol><p>{src_links(['S36','S37','S38','S39','S40','S43'])}</p>'''
    page("taxes.html", "Tax and reporting", body)


def build_penalty():
    trs = "".join(f'<tr><td data-label="Layer"><strong>{E(p["id"])} · {E(p["name"])}</strong></td><td data-label="What it is">{E(p["what"])}</td><td data-label="Verified detail">{E(p["verified"])}</td><td data-label="Personal amount">{blank("Case-specific value unknown")}</td><td data-label="Sources">{src_links(p["sources"])}<br>{flag_links(p["flags"])}</td></tr>' for p in PENALTY)
    body = f'''<h1>“Conversion penalty” breakdown</h1><p>There is no single verified government conversion penalty for a lawful CNY→USD remittance. Separate seven different things: price, bank fees, downstream fees, documents, underlying tax, U.S. exposure, and penalties for unlawful behavior.</p><div class="table-wrap"><table class="responsive"><thead><tr><th>Layer</th><th>What it is</th><th>Verified detail</th><th>Personal amount</th><th>Sources</th></tr></thead><tbody>{trs}</tbody></table></div><div class="notice danger"><strong>Penalty ceilings are not expected costs.</strong> PRC percentages apply to specified violations. FBAR/FATCA penalties apply to reporting non-compliance, not ordinary conversion. The U.S. 1% remittance excise tax covers specified U.S.-outbound physical-instrument transfers, not China→U.S. transfers.</div>'''
    page("penalty.html", "Penalty breakdown", body)


def build_sources():
    trs = "".join(f'<tr><td data-label="ID"><strong>{E(s["id"])}</strong></td><td data-label="Source"><a href="{E(s["url"])}" rel="noopener">{E(s["title"])}</a><small>{E(s["issuer"])} · {E(s["type"])}</small></td><td data-label="Locator">{E(s["locator"])}</td><td data-label="Supports">{E(s["supports"])}</td><td data-label="Review">{E(s.get("verification", "Not reviewed"))}<br>{"VERIFIED SOURCE" if s["verified"] else "EXCLUDED / UNVERIFIED"}</td></tr>' for s in SOURCES.values())
    body = f'<h1>Source register</h1><p>{len(SOURCES)} registered sources. Government/regulator/statute sources support legal propositions. Provider-primary pages support only that provider\'s prices and product rules. S52 is retained as a secondary historical cross-check but excluded from all row citations.</p><div class="table-wrap"><table class="responsive"><thead><tr><th>ID</th><th>Source</th><th>Operative locator</th><th>Supports</th><th>Review</th></tr></thead><tbody>{trs}</tbody></table></div>'
    page("sources.html", "Sources", body)


def build_flags():
    trs = "".join(f'<tr id="{E(f["id"])}"><td data-label="Flag"><strong>{E(f["id"])}</strong><br><span class="badge {"unverified" if f["severity"] == "high" else "flag"}">{E(f["severity"])}</span></td><td data-label="Issue"><strong>{E(f["title"])}</strong><br>{E(f["detail"])}<small>Status: {E(f["status"])}</small></td><td data-label="Sources">{src_links(f["sources"])}</td></tr>' for f in FLAGS.values())
    body = f'<h1>Flagged for Review</h1><div class="notice"><strong>{len(FLAGS)} published flags.</strong> These items are explicitly non-blocking. Unverified values remain blank; an official citation does not prove personal eligibility. Resolved-for-Edition-H items document corrections to this edition or irregularities in earlier editions.</div><div class="table-wrap"><table class="responsive"><thead><tr><th>Flag</th><th>Issue</th><th>Sources</th></tr></thead><tbody>{trs}</tbody></table></div>'
    page("flagged.html", "Flagged for Review", body)


def build_review():
    stats = REVIEW.get("stats", {})
    findings = REVIEW.get("findings", [])
    trs = "".join(f'<tr><td data-label="Finding"><strong>{E(f["id"])} · {E(f["title"])}</strong><small>{E(f.get("severity", "review"))}</small></td><td data-label="Evidence">{E(f["detail"])}<small>{E(f.get("files", ""))}</small></td><td data-label="Disposition">{E(f["disposition"])}</td><td data-label="Sources">{src_links(f["sources"])}</td></tr>' for f in findings)
    body = f'''<h1>Repository review</h1><div class="grid"><div class="card"><span class="kpi">{stats.get("tracked_files", 0):,}</span><br>tracked files scanned</div><div class="card"><span class="kpi">{stats.get("text_lines", 0):,}</span><br>text lines read</div><div class="card"><span class="kpi">{len(findings)}</span><br>material review findings</div></div><p>The audit reads the tracked checkout line by line for authority, pricing and consistency markers. It does not certify every claim in inherited editions. Earlier work is preserved; irregularities are disclosed here and on Flagged for Review.</p><div class="table-wrap"><table class="responsive"><thead><tr><th>Finding</th><th>Evidence</th><th>Disposition</th><th>Sources</th></tr></thead><tbody>{trs}</tbody></table></div>'''
    page("repo-review.html", "Repository review", body)


def build_requirements():
    items = [
        ("Collect, organize and analyze full requirements", "43 candidates in five categories; methodology, tax, penalty and decision findings.", "category-personal.html"),
        ("Executive summary", "Conditional best-route answer, sequence, known-cost examples and exclusions.", "executive-summary.html"),
        ("List many CNY→USD ways with pros and cons", "Every candidate has a pros/cons register and detail page.", "category-rails.html"),
        ("Break down conversion penalty", "Seven layers; no invented universal penalty.", "penalty.html"),
        ("USD10,000 increments through USD400,000", "Exact 40-point grid for each of 43 candidates; 1,720 rows and CSV.", "costs.html"),
        ("Actually estimate every method", "Amount-specific arithmetic wherever supported; per-transaction formulas or blank unverified values otherwise. Prohibited/non-applicable routes are N/A.", "methodology.html"),
        ("Step by step", "Every lawful/available candidate has detailed steps; prohibited schemes have none.", "category-personal.html"),
        ("Official links and line-by-line verification", "Claim-level source register, operative locators, deterministic citation and arithmetic checks.", "sources.html"),
        ("Blank and flag unknown values", "JSON null renders as a visibly blank cell plus UNVERIFIED; 52 review flags.", "flagged.html"),
        ("Repo review and irregularities", "Tracked files/lines scanned; superseded authority, quote drift and historical issues published.", "repo-review.html"),
        ("Clean categorized GitHub Pages dashboard", "Static HTML/CSS, no dependencies or required JavaScript; mobile card tables and source links.", "index.html"),
        ("Coordination, PR, merge and deploy", "Isolated scope claimed before work; final results recorded in root COORDINATION.md after deployment.", "requirements.html"),
    ]
    cards = "".join(f'<section class="card"><h2>{E(title)}</h2><p>{E(detail)}</p><a href="{href}">Open evidence</a></section>' for title, detail, href in items)
    body = f'<h1>Requirements traceability</h1><p>Each requirement maps to a reviewable artifact. Cost completeness means every route has a disposition at every amount; it does not mean unknown values were invented.</p><div class="grid">{cards}</div><h2>Verification commands</h2><pre><code>python3 edition-h/build/audit.py\npython3 edition-h/build/build.py\npython3 edition-h/build/verify.py</code></pre><p>CI additionally runs earlier-edition checkers to catch accidental regressions.</p>'
    page("requirements.html", "Requirements", body)


def build_methodology():
    body = f'''<h1>Methodology and limitations</h1><h2>Source hierarchy</h2><ol class="steps"><li>Government, regulator, statute, court and official tax guidance for legal/tax claims.</li><li>Bank/provider official tariff, help and public quote pages for that provider's own product terms only.</li><li>No blogs, forums, aggregators or law-firm summaries support numeric or legal rows. S52 is excluded from citations.</li></ol><h2>Cost model</h2><ul><li>Requested amounts are gross USD-equivalent principal before fees, not net receipt.</li><li>Personal legal entitlements use a clearly labeled conditional BOC TT scenario so each requested amount has useful arithmetic. This is not proof of eligibility and is not added to a separate rail.</li><li>BOC CNY scenario uses its 2026-11-09 09:15:45 board: USD100 telegraphic/cash ask CNY669.19, hence CNY6.6919 per USD1. The same ask converts CNY fees to USD for comparison.</li><li>HSBC's own executable FX was not captured, so CNY principal remains blank. Its fee arithmetic still uses CNY-equivalent principal; the resulting USD fee comparison uses BOC's ask and says so.</li><li>Wise fees are direct public observations only. No interpolation, regression or extrapolation.</li><li>FX cost is blank because a retail board and a reference rate do not establish a one-way executable spread. The observed BOC ask was below its reference rate.</li><li>All-in requires live FX, exact transfer count, correspondent/receiver charges, documents, source-of-funds and tax facts. Those are absent, so all-in is blank.</li></ul><p>{src_links(['S03','S14','S16','S18','S20','S31','S37'])}</p><h2>What “verified” does and does not mean</h2><p>Verified means the displayed source was inspected for the cited proposition on 2026-11-09 and arithmetic can be reproduced. It does not mean a bank will approve a transaction, a source will always remain online, a tax authority accepts a treaty position, or a quote is executable now.</p><h2>Safety and legality</h2><p>Rejected candidates are included to answer “as many as possible” and to warn about common suggestions. They receive no operational steps and no price that could make them appear legitimate. Lawful alternatives such as QDII or Wealth Management Connect are investment channels, not free repatriation of an existing bank balance.</p>'''
    page("methodology.html", "Methodology", body)


def main():
    (SITE / "assets").mkdir(exist_ok=True)
    (SITE / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    build_index(); build_summary(); build_categories(); build_methods(); build_costs_page()
    build_taxes(); build_penalty(); build_sources(); build_flags(); build_review()
    build_requirements(); build_methodology()
    print(f"Built {len(list(SITE.glob('*.html')))} HTML pages, {len(METHODS)} methods and {len(COSTS['rows'])} cost rows")


if __name__ == "__main__":
    main()
