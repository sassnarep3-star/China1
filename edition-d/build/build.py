#!/usr/bin/env python3
"""Edition D generator. Reads edition-d/data/*.json, writes costs.json and docs/.

Deterministic: no timestamps injected at build time. Unknown values are None
and rendered as blank + UNVERIFIED badge, never zero.
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs"
TARGETS = list(range(10000, 400001, 10000))


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


SOURCES = {s["id"]: s for s in load("sources.json")["sources"]}
METHODS_DOC = load("methods.json")
METHODS = METHODS_DOC["methods"]
CATEGORIES = METHODS_DOC["categories"]
FLAGS = {f["id"]: f for f in load("flags.json")["flags"]}
TAXES = load("taxes.json")["positions"]
PENALTY = load("penalty.json")["layers"]
SUMMARY = load("summary.json")
REVIEW = load("repo-review.json")

E = html.escape


def src_links(ids):
    out = []
    for sid in ids:
        s = SOURCES[sid]
        out.append(f'<a href="{E(s["url"])}" rel="noopener">{E(sid)} · {E(s["issuer"])}</a>')
    return '<span class="srcs">' + " ".join(out) + "</span>"


def flag_links(ids):
    return " ".join(f'<a class="badge flag" href="flagged.html#{E(fid)}">{E(fid)}</a>' for fid in ids)


def blank(reason="Unverified"):
    return f'<span class="blank" title="{E(reason)}"></span><span class="badge unverified">UNVERIFIED</span>'


def money(v, cur="USD"):
    if v is None:
        return blank()
    return f"{cur} {v:,.0f}" if isinstance(v, (int, float)) else E(str(v))


# ---------------------------------------------------------------- cost model
def sender_fee(profile):
    """Return (fee_dict, note). Only published bounds/zeros/observed quotes."""
    if profile == "boc_tt":
        return {"currency": "CNY", "min": 200, "max": 410, "unit": "per remittance",
                "formula": "min(260, max(50, 0.001×P)) + 150"}, "Commission 0.1% (CNY50–260) + international cable CNY150. P = CNY principal, unknown."
    if profile == "boc_draft":
        return {"currency": "CNY", "min": 50, "max": 260, "unit": "commission only; postage extra",
                "formula": "min(260, max(50, 0.001×P)) + actual postage"}, "Postage is charged at actual cost and is unverified."
    if profile == "hsbc_tt_paid":
        return {"currency": "CNY", "min": 220, "max": 620, "unit": "per remittance",
                "formula": "min(500, max(100, 0.001×P)) + 120"}, "Premier/Advance commission 0.1% (CNY100–500) + cable CNY120."
    if profile == "hsbc_tt_private":
        return {"currency": "CNY", "min": 0, "max": 0, "unit": "HSBC commission + cable",
                "formula": "0"}, "Published HSBC sender commission/cable free; other institutions' charges and FX are excluded."
    if profile == "hsbc_global":
        return {"currency": "USD", "min": 0, "max": 20, "unit": "per transfer (segment-dependent)",
                "formula": "PB/Premier 0; Advance 20"}, "Actual Advance charge USD20/transfer; CNY145 is indicative only. Number of transfers needed is unverified."
    if profile == "boc_atm":
        return {"currency": "CNY", "min": 12, "max": 112, "unit": "per withdrawal; foreign surcharge extra",
                "formula": "min(112, 12 + 0.01×W)"}, "W = CNY withdrawal amount. SAFE caps: CNY100k/person/year, CNY10k/card/day. Total withdrawals needed is unverified."
    if profile == "hsbc_atm":
        return {"currency": "CNY", "min": 0, "max": 110, "unit": "per withdrawal (network/segment-dependent)",
                "formula": "Premier HSBC ATM 0; UnionPay min(110, 20 + 0.01×W)"}, "Foreign surcharge may apply; SAFE cash caps apply."
    if profile == "cash_permit":
        return {"currency": "CNY", "min": 0, "max": 0, "unit": "BOC carry-permit fee during waiver",
                "formula": "0 (waived through 2026-12-31)"}, "Permit fee waived at BOC through 2026-12-31; conversion, withdrawal, transport and deposit costs are unverified."
    if profile == "rail_required":
        return None, "Legal entitlement only. Price the chosen execution rail (R01–R13); do not add a rail fee twice."
    if profile == "none":
        return None, "Not an executable transfer route; no cost is estimated."
    return None, "No current numeric fee schedule or quote was verified."


def fee_cell(fee):
    if fee is None:
        return blank("No verified sender fee")
    lo, hi = fee["min"], fee["max"]
    cur = fee["currency"]
    if lo == hi:
        txt = f"{cur} {lo:,.0f}"
    else:
        txt = f"{cur} {lo:,.0f}–{hi:,.0f}"
    return f'<span class="fee">{txt}</span><small>{E(fee["unit"])}</small>'


def build_costs():
    rows = []
    for m in METHODS:
        fee, note = sender_fee(m["cost_profile"])
        for t in TARGETS:
            rows.append({
                "method_id": m["id"], "target_usd": t,
                "cny_principal": None,
                "sender_fee": fee, "sender_fee_note": note,
                "fx_cost_usd": None, "downstream_usd": None,
                "documentation_usd": None, "tax_usd": None,
                "all_in_usd": None, "all_in_status": "unverified",
                "sources": m["sources"], "flags": m["flags"] + ["F02"],
            })
    doc = {
        "_meta": {
            "edition": "D", "researched_utc": "2026-11-08",
            "targets_usd": TARGETS,
            "policy": "Blank means unverified, never zero. Sender-fee bounds are published tariff bounds, not amount-specific estimates. FX, downstream, documentation, tax and all-in totals are blank until a live quote and personal facts exist.",
            "observed_wise_quotes": [
                {"source_cny": 66929, "bank_fee_cny": 436.18, "balance_fee_cny": 419.89, "source": "S21"},
                {"source_cny": 133858, "bank_fee_cny": 848.58, "balance_fee_cny": 832.29, "source": "S22"},
                {"source_cny": 200787, "bank_fee_cny": 1228.46, "balance_fee_cny": 1212.16, "discount_cny": 32.73, "source": "S23"},
                {"source_cny": 267716, "bank_fee_cny": 1574.68, "balance_fee_cny": 1558.39, "discount_cny": 99.31, "source": "S24"},
            ],
        },
        "rows": rows,
    }
    (DATA / "costs.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return doc


COSTS = build_costs()
ROWS_BY_METHOD = {}
for r in COSTS["rows"]:
    ROWS_BY_METHOD.setdefault(r["method_id"], []).append(r)

# ---------------------------------------------------------------- html helpers
CSS = """
:root{--ink:#182420;--muted:#5c6b64;--green:#14532d;--accent:#0f766e;--line:#dde5df;--bg:#f7faf7;--card:#fff;--warn:#92400e;--warnbg:#fef3c7;--bad:#991b1b;--badbg:#fee2e2}
*{box-sizing:border-box}body{margin:0;font:16px/1.55 system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;color:var(--ink);background:var(--bg)}
a{color:var(--accent)}header.site{background:var(--green);color:#fff;padding:14px 16px}header.site a{color:#fff;text-decoration:none}
header.site .brand{font-weight:700;font-size:1.05rem}nav.main{display:flex;flex-wrap:wrap;gap:6px;padding:10px 12px;background:#fff;border-bottom:1px solid var(--line)}
nav.main a{padding:6px 10px;border-radius:8px;text-decoration:none;font-size:.9rem;background:var(--bg)}nav.main a[aria-current]{background:var(--green);color:#fff}
main{max-width:1100px;margin:0 auto;padding:18px 14px 60px}h1{font-size:1.6rem;line-height:1.2;margin:.2em 0}h2{font-size:1.25rem;margin-top:1.6em}h3{font-size:1.05rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:12px 0}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.badge{display:inline-block;font-size:.7rem;font-weight:700;border-radius:6px;padding:2px 6px;vertical-align:middle}
.badge.unverified{background:var(--warnbg);color:var(--warn)}.badge.flag{background:#e0f2fe;color:#075985;text-decoration:none}
.badge.ok{background:#dcfce7;color:#166534}.badge.no{background:var(--badbg);color:var(--bad)}
.blank{display:inline-block;min-width:2.2em;border-bottom:2px dotted var(--warn);height:1em}
.table-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:#fff;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:.88rem;min-width:640px}th,td{padding:8px 10px;border-top:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#eef4ee;position:sticky;top:0;font-size:.78rem;text-transform:uppercase;letter-spacing:.03em}
td:first-child,th:first-child{position:sticky;left:0;background:#fff;font-weight:700;white-space:nowrap}th:first-child{background:#eef4ee}
small{display:block;color:var(--muted);font-size:.75rem}.srcs a{display:inline-block;margin:2px 6px 2px 0;font-size:.78rem}
.notice{background:var(--warnbg);border:1px solid #fcd34d;border-radius:10px;padding:10px 14px;margin:12px 0;font-size:.92rem}
.kpi{font-size:1.5rem;font-weight:800;color:var(--green)}ol.steps li,ul.req li{margin:6px 0}
footer{border-top:1px solid var(--line);padding:18px 14px;color:var(--muted);font-size:.85rem;text-align:center}
.method-head{display:flex;flex-wrap:wrap;gap:8px;align-items:center}.status{font-size:.8rem;font-weight:700}
@media(max-width:640px){h1{font-size:1.35rem}table{min-width:560px;font-size:.82rem}th,td{padding:6px 7px}}
@media print{nav.main,header.site{display:none}table{min-width:0}}
"""

NAV = [
    ("index.html", "Overview"),
    ("executive-summary.html", "Executive summary"),
    ("costs.html", "Cost explorer"),
    ("category-personal.html", "Personal"),
    ("category-rails.html", "Rails"),
    ("category-business.html", "Business"),
    ("category-alternatives.html", "Alternatives"),
    ("category-rejected.html", "Rejected"),
    ("taxes.html", "Tax"),
    ("penalty.html", "Penalty breakdown"),
    ("requirements.html", "Requirements"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for Review"),
    ("repo-review.html", "Repo audit"),
    ("methodology.html", "Methodology"),
]


def page(slug, title, body, current=None):
    parts = []
    for href, label in NAV:
        cur = ' aria-current="page"' if (current or slug) == href else ""
        parts.append(f'<a href="{href}"{cur}>{E(label)}</a>')
    nav = "".join(parts)
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} · China Money · Edition D</title><style>{CSS}</style></head><body>
<header class="site"><a class="brand" href="index.html">China Money · Edition D</a> <small style="display:inline;color:#d1fae5">CNY → USD · researched 2026-11-08 UTC</small></header>
<nav class="main" aria-label="Main">{nav}</nav>
<main id="main">{body}</main>
<footer>Edition D is additive. Earlier editions remain intact; see <a href="repo-review.html">repo audit</a> and <a href="flagged.html">Flagged for Review</a>. Blank = unverified, never zero. Not legal or tax advice.</footer>
</body></html>"""
    (DOCS / slug).write_text(doc, encoding="utf-8")


def cost_table(m):
    rows = ROWS_BY_METHOD[m["id"]]
    trs = []
    for r in rows:
        trs.append(
            "<tr>"
            f'<td>${r["target_usd"]:,}</td>'
            f'<td>{fee_cell(r["sender_fee"])}<small>{E(r["sender_fee_note"])}</small></td>'
            f'<td>{blank("No executable FX quote")}</td>'
            f'<td>{blank("Correspondent/receiver/downstream charges unknown")}</td>'
            f'<td>{blank("Personal tax facts unknown")}</td>'
            f'<td>{blank("All-in total cannot be verified")}<small>{flag_links(sorted(set(r["flags"])))}</small></td>'
            f'<td>{src_links(r["sources"])}</td>'
            "</tr>"
        )
    return (
        '<div class="table-wrap" role="region" aria-label="Cost grid" tabindex="0"><table>'
        "<thead><tr><th>Target USD</th><th>Verified sender fee</th><th>FX cost</th><th>Downstream</th><th>Tax</th><th>All-in total</th><th>Official / provider sources</th></tr></thead>"
        f'<tbody>{"".join(trs)}</tbody></table></div>'
    )


def method_page(m):
    cat = next(c for c in CATEGORIES if c["id"] == m["category"])
    status_badge = {
        "lawful-conditional": '<span class="badge ok">LAWFUL · CONDITIONAL</span>',
        "available-conditional": '<span class="badge ok">AVAILABLE · CONDITIONAL</span>',
        "unverified": '<span class="badge unverified">UNVERIFIED</span>',
        "prohibited": '<span class="badge no">PROHIBITED</span>',
        "not-repatriation": '<span class="badge flag">NOT REPATRIATION</span>',
        "alternative": '<span class="badge flag">ALTERNATIVE</span>',
        "not-applicable": '<span class="badge no">NOT APPLICABLE</span>',
    }[m["status"]]
    steps = "".join(f"<li>{E(s)}</li>" for s in m["steps"]) or "<li>No execution instructions: rejected or verification-only.</li>"
    pros = "".join(f"<li>{E(s)}</li>" for s in m["pros"])
    cons = "".join(f"<li>{E(s)}</li>" for s in m["cons"])
    req = "".join(f"<li>{E(s)}</li>" for s in m["requirements"])
    elig = "".join(f"<li>{E(s)}</li>" for s in m["eligibility"])
    body = f"""
<h1>{E(m['id'])} · {E(m['name'])}</h1>
<div class="method-head">{status_badge}<a href="{cat['page']}">{E(cat['title'])}</a>{flag_links(m['flags'])}</div>
<div class="card"><p>{E(m['summary'])}</p>{src_links(m['sources'])}</div>
<h2 id="cost">Most important: cost grid ($10k–$400k)</h2>
<div class="notice">Sender-fee cells show only published tariff bounds/zeros. FX, downstream charges, tax and all-in totals are blank and flagged because no executable quote or personal tax facts exist. A legal entitlement is priced by choosing a rail; do not double-count.</div>
{cost_table(m)}
<h2>Eligibility</h2><ul class="req">{elig or '<li>Not established / not applicable.</li>'}</ul>
<h2>Pros</h2><ul>{pros or '<li>None claimed.</li>'}</ul>
<h2>Cons</h2><ul>{cons or '<li>See status.</li>'}</ul>
<h2>Step-by-step</h2><ol class="steps">{steps}</ol>
<h2>Requirements</h2><ul class="req">{req or '<li>None — do not execute.</li>'}</ul>
"""
    page(f"method-{m['id']}.html", f"{m['id']} {m['name']}", body)


def category_page(c):
    ms = [m for m in METHODS if m["category"] == c["id"]]
    cards = []
    for m in ms:
        cards.append(
            f'<div class="card"><h3><a href="method-{m["id"]}.html">{E(m["id"])} · {E(m["name"])}</a></h3>'
            f'<p>{E(m["summary"])}</p><p>{src_links(m["sources"])} {flag_links(m["flags"])}</p></div>'
        )
    body = f"<h1>{E(c['title'])}</h1><p>{E(c['description'])}</p>" + "".join(cards)
    page(c["page"], c["title"], body)


def build_pages():
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / ".nojekyll").write_text("")
    # Overview
    kpis = f"""
<div class="grid">
<div class="card"><div class="kpi">{len(METHODS)}</div>distinct candidates<small>Entitlements, rails, alternatives and rejected candidates are counted separately, not added as independent routes.</small></div>
<div class="card"><div class="kpi">{len(COSTS['rows'])}</div>cost-grid rows<small>40 USD increments × every candidate. Unknown values are blank + UNVERIFIED.</small></div>
<div class="card"><div class="kpi">{len(SOURCES)}</div>registered sources<small>Official regulator/government/court pages plus provider-origin tariff/eligibility pages. One secondary cross-check is excluded from row citations.</small></div>
<div class="card"><div class="kpi">{len(FLAGS)}</div>review flags<small>Published on Flagged for Review; none silently fixed in other editions.</small></div>
</div>"""
    findings = "".join(
        f'<div class="card"><h3>{E(f["title"])}</h3><p>{E(f["detail"])}</p>{src_links(f["sources"])}</div>'
        for f in SUMMARY["findings"]
    )
    body = f"""
<h1>Lawful CNY → USD routes for a U.S. citizen</h1>
<p class="notice">{E(SUMMARY['headline'])}</p>
{kpis}
<h2>Start here</h2>
<div class="grid">
<div class="card"><h3><a href="executive-summary.html">Executive summary →</a></h3><p>Least-tax-penalty path and decision order.</p></div>
<div class="card"><h3><a href="costs.html">Cost explorer →</a></h3><p>$10k–$400k grids for every candidate.</p></div>
<div class="card"><h3><a href="requirements.html">Full requirements →</a></h3><p>Documents and prerequisites by route.</p></div>
<div class="card"><h3><a href="flagged.html">Flagged for Review →</a></h3><p>Open questions and irregularities.</p></div>
</div>
<h2>Key findings</h2>{findings}
"""
    page("index.html", "Overview", body)

    # Executive summary
    order = "".join(f"<li>{E(s)}</li>" for s in SUMMARY["decision_order"])
    body = f"""
<h1>Executive summary</h1><p class="notice">{E(SUMMARY['headline'])}</p>
{''.join(f'<div class="card"><h3>{E(f["title"])}</h3><p>{E(f["detail"])}</p>{src_links(f["sources"])}</div>' for f in SUMMARY['findings'])}
<h2>Least-tax-penalty decision order</h2><ol class="steps">{order}</ol>
<p>There is no verified universal percentage. The lawful path with the least tax penalty is the one that matches the real source of funds and completes the underlying tax before remitting; execution-rail fees are then compared with live quotes.</p>
"""
    page("executive-summary.html", "Executive summary", body)

    # Cost explorer
    links = "".join(
        f'<tr><td><a href="method-{m["id"]}.html">{E(m["id"])}</a></td><td>{E(m["name"])}</td>'
        f'<td>{E(m["status"])}</td><td><a href="method-{m["id"]}.html#cost">40-row grid</a></td></tr>'
        for m in METHODS
    )
    wise = "".join(
        f'<tr><td>CNY {q["source_cny"]:,}</td><td>CNY {q["bank_fee_cny"]:,.2f}</td>'
        f'<td>CNY {q["balance_fee_cny"]:,.2f}</td><td>{src_links([q["source"]])}</td></tr>'
        for q in COSTS["_meta"]["observed_wise_quotes"]
    )
    body = f"""
<h1>Cost explorer</h1>
<div class="notice">Every candidate has all 40 increments from $10,000 to $400,000 on its method page. Only published sender-fee bounds/zeros are populated. FX, downstream, documentation, tax and all-in totals are blank + UNVERIFIED. Wise public examples below are observed source-CNY quotes, not a verified current schedule and not mapped onto the USD grid.</div>
<div class="table-wrap"><table><thead><tr><th>ID</th><th>Candidate</th><th>Status</th><th>Grid</th></tr></thead><tbody>{links}</tbody></table></div>
<h2>Directly observed Wise public quotes (not locked)</h2>
<div class="table-wrap"><table><thead><tr><th>Send amount</th><th>Bank-funded fee</th><th>Wise-balance fee</th><th>Source</th></tr></thead><tbody>{wise}</tbody></table></div>
"""
    page("costs.html", "Cost explorer", body)

    for c in CATEGORIES:
        category_page(c)
    for m in METHODS:
        method_page(m)

    # Taxes
    trs = "".join(
        f'<tr><td>{E(t["id"])}</td><td>{E(t["topic"])}</td><td>{E(t["jurisdiction"])}</td>'
        f'<td>{E(t["position"])}</td><td>{E(t["rate"]) if t["rate"] else blank("No single rate")}</td>'
        f'<td>{src_links(t["sources"])} {flag_links(t["flags"])}</td></tr>'
        for t in TAXES
    )
    body = f"""<h1>Tax positions</h1><p class="notice">Rates are statutory/treaty positions, not personalized advice. Amounts are blank because residence, character, basis and filing history are unknown.</p>
<div class="table-wrap"><table><thead><tr><th>ID</th><th>Topic</th><th>Jurisdiction</th><th>Position</th><th>Rate</th><th>Sources / flags</th></tr></thead><tbody>{trs}</tbody></table></div>"""
    page("taxes.html", "Tax", body)

    # Penalty
    cards = "".join(
        f'<div class="card"><h3>{E(l["id"])} · {E(l["name"])}</h3><p>{E(l["what"])}</p>'
        f'<p><strong>Verified:</strong> {E(l["verified"])}</p><p><strong>Amount:</strong> {blank("Not a verified amount")}</p>'
        f'{src_links(l["sources"])} {flag_links(l["flags"])}</div>'
        for l in PENALTY
    )
    body = f"<h1>Decomposing the 'conversion penalty'</h1><p class=\"notice\">There is no single verified penalty. These are distinct layers; statutory penalty ceilings are not added to ordinary transfer costs.</p>{cards}"
    page("penalty.html", "Penalty breakdown", body)

    # Requirements
    secs = []
    for m in METHODS:
        if not m["requirements"]:
            continue
        req = "".join(f"<li>{E(r)}</li>" for r in m["requirements"])
        secs.append(f'<div class="card" id="req-{m["id"]}"><h3><a href="method-{m["id"]}.html">{E(m["id"])} · {E(m["name"])}</a></h3><ul class="req">{req}</ul>{src_links(m["sources"])}</div>')
    body = "<h1>Full requirements list</h1><p>Prerequisites and documents by route. Verification-only and rejected candidates list what must be confirmed before any execution.</p>" + "".join(secs)
    page("requirements.html", "Requirements", body)

    # Sources
    trs = []
    for s in SOURCES.values():
        check = "VERIFIED" if s["verified"] else '<span class="badge unverified">UNVERIFIED</span>'
        trs.append(
            f'<tr id="{E(s["id"])}"><td>{E(s["id"])}</td><td><a href="{E(s["url"])}" rel="noopener">{E(s["title"])}</a></td>'
            f'<td>{E(s["issuer"])}</td><td>{E(s["type"])}</td><td>{check}</td>'
            f'<td>{E(s["locator"])}<small>{E(s["supports"])}</small></td></tr>'
        )
    trs = "".join(trs)
    body = f"""<h1>Source register</h1><p class="notice">Every cost-grid row links to registry entries. Government/regulator/court pages verify legal rules; provider pages verify their own tariffs/eligibility only. S52 is a secondary cross-check and is not used as an official row citation.</p>
<div class="table-wrap"><table><thead><tr><th>ID</th><th>Title</th><th>Issuer</th><th>Type</th><th>Check</th><th>Locator / supports</th></tr></thead><tbody>{trs}</tbody></table></div>"""
    page("sources.html", "Sources", body)

    # Flagged
    cards = "".join(
        f'<div class="card" id="{E(f["id"])}"><div class="method-head"><span class="badge {"no" if f["severity"]=="high" else "flag"}">{E(f["severity"].upper())}</span>'
        f'<span class="status">{E(f["status"])}</span></div><h3>{E(f["id"])} · {E(f["title"])}</h3><p>{E(f["detail"])}</p>{src_links(f["sources"])}</div>'
        for f in FLAGS.values()
    )
    body = f"<h1>Flagged for Review</h1><p class=\"notice\">{len(FLAGS)} items are published openly. Open flags do not block the site; affected values are blank or the candidate is rejected.</p>{cards}"
    page("flagged.html", "Flagged for Review", body)

    # Repo review
    meta = REVIEW["_meta"]
    finding_rows = "".join(
        f'<tr><td>{E(f["rule"])}</td><td>{E(f["path"])}:{f["line"]}</td><td>{E(f["detail"])}</td>'
        f'<td><small>{E(f.get("excerpt",""))}</small></td></tr>'
        for f in REVIEW["findings"]
    )
    body = f"""<h1>Repository audit</h1>
<div class="card"><p><strong>Method:</strong> {E(meta['method'])}</p>
<p><span class="kpi">{meta['files_scanned']}</span> files · <span class="kpi">{meta['lines_scanned']}</span> lines scanned · <span class="kpi">{meta['findings']}</span> findings.</p></div>
<p>Earlier editions are preserved unchanged. Findings below are flagged for review, not silently edited in other sessions' files.</p>
<div class="table-wrap"><table><thead><tr><th>Rule</th><th>Location</th><th>Issue</th><th>Excerpt</th></tr></thead><tbody>{finding_rows}</tbody></table></div>
"""
    page("repo-review.html", "Repo audit", body)

    # Methodology
    body = f"""<h1>Methodology</h1>
<div class="card"><h2>Counting</h2><p>A legal entitlement, an execution rail, an adjacent alternative and a rejected candidate are different objects. They are not added together as independent ways to move the same money. Every candidate still receives a full 40-point cost grid so omissions are visible.</p></div>
<div class="card"><h2>Verification</h2><p>Only directly checked official regulator/government/court pages and provider-origin tariff/eligibility pages are marked verified. Provider pages verify product terms, not legal entitlement. Unknown values are blank and flagged, never inferred or set to zero.</p></div>
<div class="card"><h2>Cost model</h2><p>Target USD is the desired receipt amount. CNY principal is unknown without an executable quote. Sender-fee cells show published tariff bounds/zeros only. FX cost, downstream charges, documentation, tax and all-in totals remain blank + UNVERIFIED. Observed Wise quotes are listed separately and not extrapolated.</p></div>
<div class="card"><h2>Reproducibility</h2><p><code>python3 edition-d/build/audit.py</code> regenerates the repo-review manifest; <code>python3 edition-d/build/build.py</code> regenerates costs.json and docs; <code>python3 edition-d/build/verify.py</code> gates citations, grids, blanks and links. CI runs the same commands and requires a clean diff.</p></div>
"""
    page("methodology.html", "Methodology", body)


if __name__ == "__main__":
    build_pages()
    print(f"Built {len(list(DOCS.glob('*.html')))} pages; {len(COSTS['rows'])} cost rows.")
