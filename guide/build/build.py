#!/usr/bin/env python3
"""Build the China Money guide (standard library only).

Inputs : guide/data/*.json  (sources, prices, methods, taxes, flagged, review, scan)
Outputs: index.html (repository root landing page), guide/*.html,
         guide/data/cost-ladder.csv, EXECUTIVE_SUMMARY.md

Rules enforced here and re-checked by guide/build/verify.py:
  * every table row carries at least one link to an official source;
  * a value that could not be confirmed on an official page is rendered blank
    and linked to its entry on the Flagged for Review page - never estimated;
  * all arithmetic uses Decimal on figures quoted in guide/data/sources.json.
"""
import csv
import html
import io
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "guide"
DATA = GUIDE / "data"
REPO_URL = "https://github.com/sassnarep3-star/China1"
TARGETS = list(range(10_000, 400_001, 10_000))


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


SRC_DOC = load("sources.json")
SOURCES = {s["id"]: s for s in SRC_DOC["sources"]}
PRICES = load("prices.json")
METHODS_DOC = load("methods.json")
METHODS = METHODS_DOC["methods"]
TAXES = load("taxes.json")
FLAGS = {f["id"]: f for f in load("flagged.json")["items"]}
REVIEW = load("review.json")
SCAN = load("scan.json")
QUESTIONS_DOC = load("questions.json")
QUESTIONS = QUESTIONS_DOC["questions"]
RETRIEVED = SRC_DOC["retrieved"]

D = Decimal
BUY = D(PRICES["boc_buy_per_100"]) / 100
SELL = D(PRICES["boc_sell_per_100"]) / 100
MID = (BUY + SELL) / 2


def q2(x):
    return x.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def clamp(x, lo, hi):
    return max(D(lo), min(D(hi), x))


def e(text):
    return html.escape(str(text), quote=True)


def usd(x, cents=True):
    x = D(x)
    return f"${x:,.2f}" if cents else f"${x:,.0f}"


def cny(x):
    return f"CNY {D(x):,.2f}"


def pct(x, places=2):
    return f"{(D(x) * 100).quantize(D(1).scaleb(-places), rounding=ROUND_HALF_UP)}%"


# --------------------------------------------------------------------------
# Cost model. Framing for every route: you hold CNY worth N US dollars at the
# midpoint of Bank of China's own buy and sell quotes; cost = dollars lost on
# the way to a US account.
# --------------------------------------------------------------------------
B = PRICES["boc"]
H = PRICES["hsbc"]
A = PRICES["atm"]
W = PRICES["wise"]
CHASE = D(PRICES["receiving"]["chase_incoming_wire_usd"])
FULL = D(B["full_amount_usd"])
FX_SHARE = 1 - MID / SELL  # one-way margin against the midpoint
WISE_Q = {D(qt["send_cny"]): qt for qt in W["quotes"]}


def boc_parts(n):
    held = D(n) * MID
    fx = D(n) * FX_SHARE
    commission = clamp(held * D(B["commission_rate"]), B["commission_min_cny"], B["commission_max_cny"])
    fees_cny = commission + D(B["cable_cny"])
    fees_usd = fees_cny / SELL
    total = fx + fees_usd + FULL + CHASE
    return {"held": held, "fx": fx, "fees_cny": fees_cny, "fees_usd": fees_usd, "total": total}


def row(n, kind, total=None, share=None, detail="", src=(), flags=()):
    return {"usd": n, "kind": kind, "total": total, "share": share, "detail": detail,
            "src": list(src), "flags": list(flags)}


def ladder(method):
    model, out = method["ladder"], []
    for n in TARGETS:
        p = boc_parts(n)
        held = p["held"]
        if model in ("boc", "pr_quota"):
            if model == "pr_quota" and n > 50_000:
                out.append(row(n, "na", detail="Above the USD 50,000 annual quota; use M01 with documents for the excess.",
                               src=["CN-PR", "CN-RULES"]))
                continue
            det = (f"FX margin {usd(q2(p['fx']))} + bank fees {cny(q2(p['fees_cny']))} (≈ {usd(q2(p['fees_usd']))}) "
                   f"+ full-amount delivery {usd(FULL)} + Chase incoming wire {usd(CHASE)}")
            out.append(row(n, "value", q2(p["total"]), p["total"] / n, det,
                           src=["CN-FXBOARD", "CN-BOCTARIFF", "US-CHASE"]))
        elif model == "hsbc":
            fees = clamp(held * D(H["commission_rate"]), H["commission_min_cny"], H["commission_max_cny"]) \
                + D(H["cable_cny"]) + D(H["full_amount_precollect_cny"])
            det = (f"Published fees {cny(q2(fees))} (≈ {usd(q2(fees / SELL))} at the Bank of China selling rate) "
                   f"+ Chase incoming wire {usd(CHASE)}. FX margin not published, so no total.")
            out.append(row(n, "partial", None, None, det, src=["PR-HSBC", "US-CHASE"], flags=["F02"]))
        elif model == "rmb":
            det = (f"Sender fees {cny(q2(p['fees_cny']))} (≈ {usd(q2(p['fees_usd']))}). "
                   "Conversion cost at the receiving bank not verified, so no total.")
            out.append(row(n, "partial", None, None, det, src=["CN-BOCTARIFF", "CN-RMBX"], flags=["F09"]))
        elif model == "wise":
            qt = WISE_Q.get(held)
            if qt:
                lost = D(n) - D(qt["received_usd"])
                det = (f"Quote: send {cny(held)} → fee {cny(qt['fee_cny'])} → receive {usd(qt['received_usd'])}. "
                       "Any fee of the receiving bank is not included.")
                out.append(row(n, "value", q2(lost), lost / n, det, src=["PR-WISEFEE", "PR-WISE"], flags=["F06"]))
            elif held > D(W["per_transfer_cap_cny"]):
                out.append(row(n, "blank", detail="Above the CNY 300,000 per-transfer limit; several transfers would be needed and no quote exists.",
                               src=["PR-WISE", "PR-WISEFEE"], flags=["F06"]))
            else:
                out.append(row(n, "blank", detail="No quote sampled at this amount.", src=["PR-WISEFEE"], flags=["F06"]))
        elif model == "cash":
            if n <= int(PRICES["cash"]["permit_max_usd"]):
                det = "FX margin on buying USD cash at the bank. Bank permit needed above USD 5,000 (fee waived until 2026-12-31). No wire fees."
                out.append(row(n, "value", q2(p["fx"]), p["fx"] / n, det, src=["CN-FXBOARD", "CN-CASH", "CN-BOCTARIFF"]))
            else:
                out.append(row(n, "na", detail="Not allowed in one trip: in principle no more than USD 10,000 may be carried out.",
                               src=["CN-CASH"]))
        elif model == "atm":
            if held <= D(A["per_person_year_cny"]):
                per_day = D(A["per_card_day_cny"])
                full_days = int(held // per_day)
                rest = held - per_day * full_days
                fee = full_days * min(D(A["max_cny"]), D(A["fixed_cny"]) + per_day * D(A["rate"]))
                if rest > 0:
                    fee += min(D(A["max_cny"]), D(A["fixed_cny"]) + rest * D(A["rate"]))
                det = (f"Bank of China card fee {cny(q2(fee))} (≈ {usd(q2(fee / SELL))}) for {full_days + (1 if rest > 0 else 0)} "
                       "daily withdrawals. Card-scheme exchange rate and ATM-owner surcharge not verified, so no total.")
                out.append(row(n, "partial", None, None, det, src=["CN-BOCTARIFF", "CN-CARD"], flags=["F08"]))
            else:
                out.append(row(n, "na", detail="Above the CNY 100,000 per-person annual cap on overseas cash withdrawals.",
                               src=["CN-CARD"]))
        elif model == "penalty":
            fine = D(n) * D(PRICES["penalty"]["fine_up_to"])
            det = (f"Fine up to 30% of the amount ({usd(fine, False)}); 30%–100% if serious ({usd(fine, False)}–{usd(n, False)}); "
                   "criminal liability where a crime is constituted. This is exposure, not a price.")
            out.append(row(n, "penalty", q2(fine), D(PRICES["penalty"]["fine_up_to"]), det, src=["CN-FXREG"]))
        elif model == "crypto":
            out.append(row(n, "na", detail="Illegal financial activity in China; banks may not process it and losses are your own. The notice states no fine scale.",
                           src=["CN-CRYPTO"]))
        elif model == "blank":
            out.append(row(n, "blank", detail="No official price found for this route.", src=method["src"], flags=method["flags"]))
        else:
            raise SystemExit(f"unknown ladder model {model}")
    return out


LADDERS = {m["id"]: ladder(m) for m in METHODS}

# --------------------------------------------------------------------------
# HTML helpers
# --------------------------------------------------------------------------
NAV = [
    ("index.html", "Home"), ("guide/summary.html", "Summary"), ("guide/methods.html", "Methods"),
    ("guide/costs.html", "Costs"), ("guide/steps.html", "Steps"), ("guide/taxes.html", "Taxes"),
    ("guide/questions.html", "Decide"),
    ("guide/flagged.html", "Flagged"), ("guide/sources.html", "Sources"),
    ("guide/repo-review.html", "Repo review"), ("guide/archive.html", "Archive"),
]

CSS = """
:root{--bg:#f5f7fa;--card:#fff;--ink:#16202b;--mut:#5b6877;--line:#dde3ea;--brand:#0b5cab;--ok:#11734b;--okbg:#e4f5ec;--warn:#8a5300;--warnbg:#fff1d6;--bad:#a4262c;--badbg:#fde7e9;--blank:#6b4fa0;--blankbg:#f0eafa}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,"PingFang SC","Microsoft YaHei",sans-serif}
a{color:var(--brand)}a:focus-visible,summary:focus-visible{outline:3px solid #f5a623;outline-offset:2px}
.skip{position:absolute;left:-999px}.skip:focus{left:8px;top:8px;background:#fff;padding:8px;z-index:9}
header.top{background:#0d2238;color:#fff}
.bar{max-width:1100px;margin:0 auto;padding:12px 16px 0;display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 14px}
.brand{color:#fff;text-decoration:none;font-weight:700;font-size:1.15rem}.brand span{color:#8fc3ff}
.tag{color:#b9c7d6;font-size:.82rem}
nav.main{max-width:1100px;margin:0 auto;padding:8px 10px 0;display:flex;gap:2px;overflow-x:auto;scrollbar-width:thin}
nav.main a{color:#d7e3f0;text-decoration:none;padding:9px 11px;border-radius:8px 8px 0 0;white-space:nowrap;font-size:.92rem}
nav.main a[aria-current=page]{background:var(--bg);color:var(--ink);font-weight:600}
main{max-width:1100px;margin:0 auto;padding:18px 16px 40px}
h1{font-size:1.65rem;line-height:1.25;margin:.2em 0 .35em}h2{font-size:1.22rem;margin:1.7em 0 .5em}h3{font-size:1.02rem;margin:1.2em 0 .35em}
p{margin:.5em 0}.lead{font-size:1.06rem;color:#2b3947;max-width:75ch}.mut{color:var(--mut)}.small{font-size:.86rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin:12px 0}
.answer{border-left:6px solid var(--ok)}.answer h2{margin-top:0}
.kpis{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin:14px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.kpi b{display:block;font-size:1.45rem;line-height:1.2}.kpi span{display:block;color:var(--mut);font-size:.84rem;margin-top:2px}.kpi a{font-size:.8rem}
.tiles{display:grid;grid-template-columns:1fr;gap:10px}
.tile{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:13px 15px;text-decoration:none;color:var(--ink)}
.tile b{color:var(--brand);display:block}.tile span{color:var(--mut);font-size:.88rem}.tile:hover{border-color:var(--brand)}
.badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.76rem;font-weight:600;white-space:nowrap}
.b-ok{background:var(--okbg);color:var(--ok)}.b-warn{background:var(--warnbg);color:var(--warn)}.b-bad{background:var(--badbg);color:var(--bad)}.b-blank{background:var(--blankbg);color:var(--blank)}
.blank{display:inline-block;background:var(--blankbg);color:var(--blank);border:1px dashed #b9a5e0;border-radius:6px;padding:0 7px;font-size:.8rem;font-weight:600}
.src{font-size:.8rem;white-space:nowrap}.srcs{display:flex;flex-wrap:wrap;gap:2px 9px}
.wrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:12px;margin:10px 0}
table{border-collapse:collapse;width:100%;font-size:.9rem}
caption{text-align:left;padding:10px 12px 4px;font-weight:600}
th,td{padding:8px 10px;text-align:left;vertical-align:top;border-top:1px solid var(--line)}
thead th{border-top:0;background:#eef2f6;font-size:.8rem;text-transform:uppercase;letter-spacing:.03em;color:#3d4a58;position:sticky;top:0}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
td small{display:block;color:var(--mut);font-size:.78rem}
td ul{margin:0;padding-left:1.05em}
tr.best td{background:#f1faf5}
details{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:10px 0;padding:0 14px}
details[open]{padding-bottom:10px}summary{cursor:pointer;padding:12px 0;font-weight:600}
summary small{font-weight:400;color:var(--mut);display:block}
ol.steps{padding-left:1.3em}ol.steps li{margin:.45em 0}
ul.plain{padding-left:1.1em}
.note{background:var(--warnbg);border:1px solid #f0d49b;border-radius:10px;padding:10px 13px;margin:12px 0;font-size:.92rem}
.danger{background:var(--badbg);border:1px solid #f1b9be;border-radius:10px;padding:10px 13px;margin:12px 0;font-size:.92rem}
footer{max-width:1100px;margin:0 auto;padding:18px 16px 40px;color:var(--mut);font-size:.84rem;border-top:1px solid var(--line)}
@media(min-width:720px){.kpis{grid-template-columns:repeat(4,1fr)}.tiles{grid-template-columns:repeat(3,1fr)}h1{font-size:2rem}}
@media(max-width:719px){
 table.stack thead{position:absolute;left:-9999px}
 table.stack,table.stack tbody,table.stack tr,table.stack td{display:block;width:100%}
 table.stack tr{border-top:6px solid var(--bg);padding:6px 0}
 table.stack tr:first-child{border-top:0}
 table.stack td{border:0;padding:4px 12px}
 table.stack td::before{content:attr(data-label);display:block;font-size:.72rem;text-transform:uppercase;letter-spacing:.03em;color:var(--mut)}
 table.stack td.num{text-align:left}
 table.tight{font-size:.8rem}table.tight th,table.tight td{padding:6px 5px}
 table.tight .srcs{flex-direction:column;gap:0}table.tight .src{white-space:normal}table.tight .blank{white-space:normal}
}
"""


def src_links(ids, compact=False):
    parts = []
    for sid in ids:
        s = SOURCES[sid]
        mark = ' <span class="badge b-blank">excerpt only</span>' if s["level"] == "excerpt" else ""
        if compact:
            parts.append(f'<a class="src" href="{e(s["url"])}" rel="noopener">{e(s["short"])}</a>{mark}')
            continue
        parts.append(f'<a class="src" href="{e(s["url"])}" target="_blank" rel="noopener" title="{e(s["publisher"])} — {e(s["title"])}">{e(s["short"])}</a>{mark}')
    return '<span class="srcs">' + "".join(parts) + "</span>"


def flag_links(ids, prefix):
    return " ".join(f'<a class="badge b-blank" href="{prefix}guide/flagged.html#{fid}" title="{e(FLAGS[fid]["topic"])}">{fid}</a>' for fid in ids)


def blank(flags, prefix):
    assert flags, "a blank cell must point to a flagged item"
    return f'<span class="blank" title="Not confirmed on an official page – left blank">blank · unverified</span> {flag_links(flags, prefix)}'


def table(headers, rows, cls="stack", caption=None, row_classes=None):
    """headers: list of (label, css). rows: list of lists of html strings."""
    cap = f"<caption>{e(caption)}</caption>" if caption else ""
    head = "".join(f'<th scope="col" class="{c}">{e(h)}</th>' for h, c in headers)
    body = []
    for i, r in enumerate(rows):
        rc = f' class="{row_classes[i]}"' if row_classes and row_classes[i] else ""
        cells = "".join(f'<td class="{headers[j][1]}" data-label="{e(headers[j][0])}">{c}</td>' for j, c in enumerate(r))
        body.append(f"<tr{rc}>{cells}</tr>")
    return f'<div class="wrap"><table class="{cls}">{cap}<thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def page(slug, title, description, body):
    depth = slug.count("/")
    prefix = "../" * depth
    cur = ' aria-current="page"'
    nav = "".join(
        f'<a href="{prefix}{href}"{cur if href == slug else ""}>{e(label)}</a>' for href, label in NAV)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{e(description)}">
<title>{e(title)} · China Money</title>
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
<div class="bar"><a class="brand" href="{prefix}index.html">China Money <span>CNY → USD</span></a><span class="tag">Official sources read {RETRIEVED} · blank means unverified</span></div>
<nav class="main" aria-label="Main">{nav}</nav>
</header>
<main id="main">
{body}
</main>
<footer>
<p>Research guide, not legal or tax advice. Every figure links to the official page it was read on ({RETRIEVED}). Anything that could not be confirmed is left blank and listed on the <a href="{prefix}guide/flagged.html">Flagged for Review</a> page. Rules, rates and fees change — re-check the linked page before you act.</p>
<p><a href="{REPO_URL}">Repository</a> · <a href="{REPO_URL}/blob/main/COORDINATION.md">Coordination log</a> · <a href="{prefix}guide/archive.html">Archived editions</a></p>
</footer>
</body>
</html>
"""


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def method(mid):
    return next(m for m in METHODS if m["id"] == mid)


def status_badge(m):
    cls = {"Prohibited": "b-bad", "Limited": "b-warn"}.get(m["status"], "b-ok" if m["status"] == "Lawful" else "b-warn")
    return f'<span class="badge {cls}">{e(m["status"])}</span>'


def at(mid, n):
    return next(r for r in LADDERS[mid] if r["usd"] == n)


# Facts derived from the ladders, used in prose so text can never drift from the tables.
BOC10, BOC100, BOC400 = at("M01", 10_000), at("M01", 100_000), at("M01", 400_000)
WISE_ROWS = [r for r in LADDERS["M10"] if r["kind"] == "value"]
RECHECKED = sum(1 for s in SOURCES.values() if s.get("checked") == RETRIEVED)
N_FULL = sum(1 for s in SOURCES.values() if s["level"] == "full")
N_EXC = len(SOURCES) - N_FULL
LAWFUL = [m for m in METHODS if m["cat"] != "prohibited"]
BANNED = [m for m in METHODS if m["cat"] == "prohibited"]


def wise_sentence():
    lo, hi = WISE_ROWS[0], WISE_ROWS[-1]
    s = (f"Wise quoted {usd(lo['total'])} ({pct(lo['share'])}) at {usd(lo['usd'], False)} and "
         f"{usd(hi['total'])} ({pct(hi['share'])}) at {usd(hi['usd'], False)}")
    return s + (". These are historical modelled shortfalls, not executable or complete quotes: Wise figures exclude any receiving-bank fee. "
                "A cheapest route cannot be determined. China bank-app transfers are limited to CNY 300,000 each; other channels have different limits.")


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
def build_home():
    p = ""
    kpis = [
        (usd(BOC10["total"]), f"to move {usd(10_000, False)} by Bank of China wire ({pct(BOC10['share'])})", "CN-BOCTARIFF"),
        (usd(BOC400["total"]), f"to move {usd(400_000, False)} the same way ({pct(BOC400['share'])})", "CN-BOCTARIFF"),
        ("30%–100%", "fine on the amount for evading the rules, if serious", "CN-FXREG"),
        ("$10,000", "aggregate foreign-account balance: FBAR generally required if it exceeds this", "US-8938FBAR"),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><b>{e(v)}</b><span>{e(t)}</span>{src_links([s])}</div>' for v, t, s in kpis)

    fit = [
        ("Salary or other work pay already taxed in China", "M01", "Passport, proof of the amount, tax payment record", ["CN-ART59"]),
        ("After-tax salary, smaller amounts, no branch visit", "M10", "China tax record from the last 3 years", ["PR-WISE"]),
        ("Proceeds of selling a home", "M05", "Sale contract, registration certificate, tax voucher", ["CN-SHPROP"]),
        ("Inheritance from someone in China", "M07", "SAFE approval, inheritance papers, tax certificate", ["CN-PROPTRANS", "CN-CAP2014"]),
        ("Assets you owned before emigrating from China", "M06", "SAFE approval, proof of lawful source, tax certificate", ["CN-PROPTRANS", "CN-CAP2014"]),
        ("Dividends or other investment income", "M08", "Tax voucher; tax filing above USD 50,000 per payment", ["CN-TAXFILING"]),
        ("You hold a China permanent-resident card", "M04", "The card; USD 50,000 a year", ["CN-PR"]),
        ("CNY you exchanged from foreign currency less than 24 months ago", "M15", "Passport and the original exchange memo", ["CN-RULES"]),
    ]
    fit_rows = []
    for money, mid, docs, src in fit:
        m = method(mid)
        r10, r400 = at(mid, 10_000), at(mid, 400_000)

        def cell(r, m=m):
            if r["kind"] == "value":
                return f'{usd(r["total"])}<small>{pct(r["share"])}</small>'
            if r["kind"] == "na":
                return '<span class="badge b-warn">not available</span>'
            return blank(r["flags"], p)
        fit_rows.append([
            e(money),
            f'<a href="guide/steps.html#{mid}"><b>{e(m["name"])}</b></a>',
            e(docs), cell(r10), cell(r400), src_links(src)])
    fit_tbl = table([("Where the CNY came from", ""), ("Route to use", ""), ("What the bank needs", ""),
                     ("Cost at $10,000", "num"), ("Cost at $400,000", "num"), ("Official source", "")], fit_rows)

    tiles = [
        ("guide/summary.html", "Executive summary", "The answer, the numbers and the risks on one page."),
        ("guide/questions.html", "What must be answered first", "16 blocking questions, what we already know, and the 8-step plan to find the missing facts."),
        ("guide/methods.html", f"All {len(METHODS)} methods", f"{len(LAWFUL)} lawful routes and {len(BANNED)} prohibited ones, with pros and cons."),
        ("guide/costs.html", "Cost ladder", "Every method at every $10,000 step up to $400,000."),
        ("guide/steps.html", "Step by step", "Exactly what to do for each lawful route."),
        ("guide/taxes.html", "Taxes and penalties", "The 'conversion penalty' broken down: China tax, fines, US tax and filings."),
        ("guide/flagged.html", f"Flagged for Review ({len(FLAGS)})", "Everything left blank because it could not be confirmed, with links to check."),
        ("guide/sources.html", f"Sources ({len(SOURCES)})", "Every official page relied on, with the text quoted."),
        ("guide/repo-review.html", "Repository review", f"{SCAN['total_lines']:,} archived lines scanned against the official sources; irregularities listed."),
        ("guide/archive.html", "Archive", "Earlier editions kept for reference; superseded by this guide."),
    ]
    tiles_html = "".join(f'<a class="tile" href="{h}"><b>{e(t)}</b><span>{e(d)}</span></a>' for h, t, d in tiles)

    body = f"""
<h1>Getting money out of a China bank account and into US dollars</h1>
<p class="lead">For a US citizen holding CNY in a mainland account. Which routes are lawful, what each costs at every size up to $400,000, and what tax and reporting follow.</p>

<section class="card answer" aria-labelledby="ans">
<h2 id="ans">The short answer</h2>
<ul class="plain">
<li><b>No rule read for this guide taxes the conversion itself.</b> Underlying income, bank charges and possible US foreign-currency gain require separate review; prior payment of China tax does not establish that no other tax applies. {src_links(["CN-ART59", "CN-IIT"])}</li>
<li><b>Lawful route:</b> take your passport and evidence of the lawful source and amount to the bank; provide a tax record where tax applies. SAFE says a tax voucher is not required where qualifying current-account income is not taxable under the rules. Ask the branch to confirm its evidence checklist, then buy USD and wire it to your own US account. The cited rule states no fixed cap for this documented-income route. {src_links(["CN-ART59", "CN-WORKFX2025", "CN-MEASURES"])}</li>
<li><b>Cost by Bank of China wire into a Chase account:</b> {usd(BOC10["total"])} for $10,000 ({pct(BOC10["share"])}), {usd(BOC100["total"])} for $100,000 ({pct(BOC100["share"])}), {usd(BOC400["total"])} for $400,000 ({pct(BOC400["share"])}). {src_links(["CN-FXBOARD", "CN-BOCTARIFF", "US-CHASE"])}</li>
<li><b>Do not split the amount, borrow other people's quotas, use money changers or crypto.</b> Fines run up to 30% of the amount, and 30%–100% if serious, with possible criminal liability. {src_links(["CN-MEASURES", "CN-FXREG", "CN-CRYPTO"])}</li>
<li><b>In the US:</b> the pages read tax the income in the year it is earned, not the later transfer. File the FBAR and Form 8938 if the account passed the thresholds. {src_links(["US-ABROAD", "US-8938FBAR"])}</li>
</ul>
</section>

<div class="kpis">{kpi_html}</div>

<h2>Pick the route that matches where the money came from</h2>
<p class="mut small">Costs are for a Bank of China wire with full-amount delivery into a Chase account, on the {e(PRICES["snapshot"])} rates. Blank means not confirmed.</p>
{fit_tbl}
<div class="note"><b>If you cannot document where the money came from, the amount, or its applicable tax treatment:</b> no lawful route was verified for it. Property whose lawful source cannot be proved is refused. Confirm whether tax is due and what evidence the bank accepts before proceeding. {src_links(["CN-PROPTRANS", "CN-ART59", "CN-WORKFX2025"])}</div>

<h2>Explore</h2>
<div class="tiles">{tiles_html}</div>

<h2>How to read this site</h2>
<ul class="plain">
<li>Every table row links to the official page the figure was read on.</li>
<li><span class="blank">blank · unverified</span> means no official figure was found. It is never an estimate and never zero.</li>
<li>{N_FULL} sources were opened and read in full; {N_EXC} were seen only as excerpts and are flagged.</li>
</ul>
"""
    write(ROOT / "index.html", page("index.html", "Home", "Lawful ways for a US citizen to convert CNY in a China bank account to USD, with costs at every $10,000 step to $400,000, taxes, and official sources.", body))


def build_summary():
    p = "../"
    top = []
    for mid in ("M01", "M10", "M02", "M05", "M07", "M06", "M12", "M13"):
        m = method(mid)
        cells = []
        for n in (10_000, 100_000, 400_000):
            r = at(mid, n)
            if r["kind"] == "value":
                cells.append(f'{usd(r["total"])}<small>{pct(r["share"])}</small>')
            elif r["kind"] == "na":
                cells.append('<span class="badge b-warn">not available</span>')
            else:
                cells.append(blank(r["flags"], p))
        top.append([f'<a href="methods.html#{mid}"><b>{e(m["name"])}</b></a><small>{e(m["verdict"])}</small>', *cells, src_links(m["src"])])
    top_tbl = table([("Route", ""), ("$10,000", "num"), ("$100,000", "num"), ("$400,000", "num"), ("Official source", "")], top)

    risk = [
        ("Splitting, borrowed quotas, money changers, false documents", "Fine up to 30% of the amount; 30%–100% if serious; possible criminal liability", ["CN-FXREG", "CN-MEASURES"]),
        ("Crypto", "Illegal financial activity in China; losses are your own", ["CN-CRYPTO"]),
        ("Missing a US FBAR", "Up to USD 16,536 non-willful; USD 165,353 willful", ["US-FBARPEN"]),
        ("Missing US Form 8938", "USD 10,000, up to USD 60,000", ["US-8938FBAR"]),
        ("Carrying more than USD 10,000 in cash", "Not allowed out of China in principle; unreported cash can be seized in the US", ["CN-CASH", "US-CBP"]),
    ]
    risk_tbl = table([("Risk", ""), ("Exposure", ""), ("Official source", "")],
                     [[e(a), e(b), src_links(s)] for a, b, s in risk])
    body = f"""
<h1>Executive summary</h1>
<p class="lead">You are a US citizen with CNY in a mainland bank account. This page gives the answer first, then the numbers, then the risks.</p>

<section class="card answer"><h2>Answer</h2>
<ol class="steps">
<li><b>There is no separate conversion tax in the rules read.</b> What people call the "conversion penalty" is made of: tax on the underlying income if it was never taxed, bank charges, fines if a prohibited route is used, and US filing penalties if reports are missed. {src_links(["CN-IIT", "CN-FXREG", "US-FBARPEN"])}</li>
<li><b>Use the documented bank route.</b> As a foreign passport holder you may buy foreign exchange with lawful China current-account income by showing your ID and proof of source and amount. Tax vouchers are part of the evidence where tax applies; SAFE says no voucher is needed if qualifying income is not taxable under the rules. No fixed cap is stated for this documented-income route. {src_links(["CN-ART59", "CN-WORKFX2025", "CN-RULES"])}</li>
<li><b>The USD 50,000 yearly total is not written as a cap on your purchase of USD.</b> As written it covers everyone's sale of foreign exchange and a domestic individual's purchase of it; a foreign passport holder's purchase is document-driven (art. 13), and the holder of a Foreign Permanent Resident ID Card gets the total as a convenience. {src_links(["CN-RULES", "CN-ART59", "CN-PR"])}</li>
<li><b>Send it in one wire.</b> Bank of China's commission is capped at CNY 260 and the cable fee is fixed, so one large wire costs {pct(BOC400["share"])} at $400,000 against {pct(BOC10["share"])} at $10,000. Splitting to avoid review is prohibited. {src_links(["CN-BOCTARIFF", "CN-MEASURES"])}</li>
<li><b>Match the route to the money.</b> Property-sale proceeds, inheritance and pre-emigration assets each have their own route and papers. {src_links(["CN-SHPROP", "CN-PROPTRANS", "CN-CAP2014"])}</li>
<li><b>Keep the US side clean.</b> Report worldwide income in the year earned, consider a foreign tax credit if eligible, and check FBAR reporting if the aggregate foreign-account balance exceeded $10,000. {src_links(["US-ABROAD", "US-FTC", "US-8938FBAR"])}</li>
</ol></section>

<h2>What it costs</h2>
<p>Bank of China wire into a Chase account, all published charges included. {e(wise_sentence())} The property, inheritance and emigrant routes use the same bank charges; their taxes and approvals come on top. Full table: <a href="costs.html">Cost ladder</a>.</p>
{top_tbl}

<h2>What the "conversion penalty" is made of</h2>
{table([("Part", ""), ("Size", ""), ("When it applies", ""), ("Official source", "")], [
    ["FX margin", e(pct(FX_SHARE, 4)) + " of the amount", "Always. Bank of China selling rate against the midpoint of its buy and sell quotes.", src_links(["CN-FXBOARD"])],
    ["Bank and wire fees", e(f"{usd(q2(boc_parts(10_000)['total'] - boc_parts(10_000)['fx']))} at $10,000; {usd(q2(boc_parts(400_000)['total'] - boc_parts(400_000)['fx']))} at $400,000"), "Per wire: commission, cable, full-amount delivery, receiving-bank fee.", src_links(["CN-BOCTARIFF", "US-CHASE"])],
    ["China income tax", "3%–45% salary; 20% gains, dividends, interest", "Only if the income was not yet taxed. The rules read add no further tax to money already taxed.", src_links(["CN-IIT"])],
    ["US income tax", "Depends on income and eligibility", "A foreign tax credit may be available subject to requirements and limitations.", src_links(["US-ABROAD", "US-FTC"])],
    ["Exchange gain in the US", "Depends on transaction", "The USD 200 exception has conditions; review gain and loss: " + blank(["F13"], p), src_links(["US-988"])],
    ["Fines for prohibited routes", "Up to 30%; 30%–100% if serious", "Only if you break the rules.", src_links(["CN-FXREG"])],
])}

<h2>Main risks</h2>
{risk_tbl}

<h2>What is still open</h2>
<p>{len(FLAGS)} items could not be confirmed on an official page and are left blank. The ones that matter most: whether your bank wants the tax-filing form for salary above USD 50,000 ({flag_links(["F01"], p)}), exchange rates at banks other than Bank of China ({flag_links(["F02", "F03"], p)}), and the US treatment of an exchange gain above USD 200 ({flag_links(["F13"], p)}). See <a href="flagged.html">Flagged for Review</a>.</p>
"""
    write(GUIDE / "summary.html", page("guide/summary.html", "Executive summary", "Executive summary: lawful CNY to USD route for a US citizen, costs, tax and risks, with official sources.", body))


def build_methods():
    p = "../"
    out = ['<h1>Methods</h1>',
           f'<p class="lead">{len(METHODS)} ways of turning CNY in a mainland account into USD: {len(LAWFUL)} lawful, {len(BANNED)} prohibited. The first row in each group is the one to look at first.</p>']
    for cat, label in METHODS_DOC["categories"].items():
        ms = [m for m in METHODS if m["cat"] == cat]
        rows = []
        for m in ms:
            def txt(v, m=m):
                return e(v) if v else blank(m["flags"], p)
            r10, r400 = at(m["id"], 10_000), at(m["id"], 400_000)

            def cc(r, m=m):
                if r["kind"] == "value":
                    return f'{usd(r["total"])} ({pct(r["share"])})'
                if r["kind"] == "penalty":
                    return f'fine up to {usd(r["total"], False)}'
                if r["kind"] == "na":
                    return "not available"
                return blank(r["flags"], p)
            if cat == "prohibited":
                rows.append([
                    f'<b id="{m["id"]}">{e(m["name"])}</b><small>{m["id"]}</small> {status_badge(m)}',
                    txt(m["cost"]) if m["cost"] else "No fine scale stated in the notice",
                    "<ul>" + "".join(f"<li>{e(c)}</li>" for c in m["cons"]) + "</ul>",
                    src_links(m["src"])])
            else:
                flags = f"<small>Open points: {flag_links(m['flags'], p)}</small>" if m["flags"] else ""
                rows.append([
                    f'<b id="{m["id"]}">{e(m["name"])}</b><small>{m["id"]}</small> {status_badge(m)}',
                    f'{e(m["verdict"])}{flags}',
                    f'$10,000: {cc(r10)}<br>$400,000: {cc(r400)}<small>{txt(m["cost"])}</small>',
                    txt(m["limit"]), e(m["who"]),
                    "<ul>" + "".join(f"<li>{e(c)}</li>" for c in m["pros"]) + "</ul>",
                    "<ul>" + "".join(f"<li>{e(c)}</li>" for c in m["cons"]) + "</ul>",
                    f'<a href="steps.html#{m["id"]}">Steps</a> · <a href="costs.html#L-{m["id"]}">Ladder</a>',
                    src_links(m["src"])])
        out.append(f"<h2>{e(label)}</h2>")
        if cat == "prohibited":
            out.append('<div class="danger">Listed so you can recognise them. No instructions are given. They carry fines of up to 30% of the amount, 30%–100% if serious, and possible criminal liability.</div>')
            out.append(table([("Method", ""), ("Penalty exposure", ""), ("Why not", ""), ("Official source", "")], rows))
        else:
            out.append(table([("Method", ""), ("Bottom line", ""), ("Cost", ""), ("Limit", ""), ("Who qualifies", ""),
                              ("Pros", ""), ("Cons", ""), ("More", ""), ("Official source", "")], rows))
    write(GUIDE / "methods.html", page("guide/methods.html", "Methods", "All methods for converting CNY to USD from a mainland account, with pros, cons, limits and official sources.", "\n".join(out)))


def build_costs():
    p = "../"
    rows, classes = [], []
    for n in TARGETS:
        b, w, h = at("M01", n), at("M10", n), at("M02", n)
        wcell = f'<b>{usd(w["total"])}</b><small>{pct(w["share"])}</small>' if w["kind"] == "value" else blank(["F06"], p)
        hs = h["detail"].split("(≈ ")[1].split(" at")[0]
        best = blank(["F24"], p)
        rows.append([
            f'<b>{usd(n, False)}</b>',
            f'<b>{usd(b["total"])}</b><small>{pct(b["share"])}</small>',
            wcell,
            f'{e(hs)}<small>bank fees only · FX {flag_links(["F02"], p)}</small>',
            best,
            src_links(["CN-BOCTARIFF", "PR-WISEFEE", "PR-HSBC"])])
        classes.append("")
    main_tbl = table([("Amount", "num"), ("Bank of China wire", "num"), ("Wise", "num"), ("HSBC China", "num"),
                      ("Cheapest route (unverified)", ""), ("Official source", "")], rows, cls="tight", row_classes=classes)

    comp = table([("Component", ""), ("Figure", ""), ("How it is used", ""), ("Official source", "")], [
        ["Bank of China selling rate", f"CNY {SELL:.4f} per USD", "Rate at which your CNY buys USD (telegraphic and cash selling rates were the same).", src_links(["CN-FXBOARD"])],
        ["Bank of China buying rate", f"CNY {BUY:.4f} per USD", f"Used only to find the midpoint, CNY {MID:.4f}.", src_links(["CN-FXBOARD"])],
        ["FX margin", pct(FX_SHARE, 4), "1 − midpoint ÷ selling rate. Charged on the whole amount.", src_links(["CN-FXBOARD"])],
        ["Bank of China commission", "1‰, minimum CNY 50, maximum CNY 260", "Per wire, on the CNY amount.", src_links(["CN-BOCTARIFF", "CN-BOCFEE"])],
        ["Bank of China cable fee", "CNY 150", "Per international wire.", src_links(["CN-BOCTARIFF", "CN-BOCFEE"])],
        ["Full-amount delivery", "USD 25 (USD 15 if the receiving bank has an account with BOC New York)", "Replaces deductions by correspondent banks. USD 25 is used.", src_links(["CN-BOCTARIFF"])],
        ["Receiving bank", "Chase: USD 15 per incoming wire", "Other US banks: " + blank(["F05"], p), src_links(["US-CHASE"])],
        ["HSBC China commission and cable", "0.1%, minimum CNY 100, maximum CNY 500; cable CNY 120; CNY 200 pre-collected for full-amount delivery", "Premier and Advance. FX rate: " + blank(["F02"], p), src_links(["PR-HSBC"])],
        ["Wise", "Historical comparison quotes: fee shown", "Five samples; no interpolation. Receiving fees excluded; not a complete current quote.", src_links(["PR-WISEFEE"])],
    ])

    out = [f"""
<h1>Cost ladder</h1>
<p class="lead">What it costs to turn CNY into dollars in a US account, at every $10,000 step up to $400,000.</p>
<section class="card answer"><h2>What the numbers say</h2>
<ul class="plain">
<li>Bank of China wire: {usd(BOC10["total"])} at $10,000 ({pct(BOC10["share"])}), falling to {pct(BOC400["share"])} at $400,000 ({usd(BOC400["total"])}) because the fees are capped and only the FX margin grows.</li>
<li>{e(wise_sentence())}</li>
<li>HSBC China publishes its fees but not its rate here, so it has no total.</li>
<li>Every other route is either capped far below these amounts or has no official price; those cells are blank.</li>
</ul>
<p class="small mut">How to read a row: you hold CNY worth the amount shown at the midpoint of Bank of China's buy and sell quotes ({e(PRICES["snapshot"])}). The cost is the dollars lost between that and your US account. One wire per amount.</p>
</section>

<h2>Priced routes side by side</h2>
{main_tbl}
<p class="small"><a href="data/cost-ladder.csv">Download all {len(METHODS)} methods × {len(TARGETS)} amounts as CSV</a></p>

<h2>What goes into the price</h2>
{comp}

<h2>Every method at every amount</h2>
<p class="mut small">Open a method to see all {len(TARGETS)} steps. "Not available" means a published rule rules it out at that amount. Blank means no official price.</p>
"""]
    for m in METHODS:
        rws = []
        for r in LADDERS[m["id"]]:
            if r["kind"] == "value":
                tot, sh = f'<b>{usd(r["total"])}</b>', pct(r["share"])
            elif r["kind"] == "penalty":
                tot, sh = f'<b>fine up to {usd(r["total"], False)}</b>', "up to 30%"
            elif r["kind"] == "na":
                tot, sh = '<span class="badge b-warn">not available</span>', "—"
            else:
                tot, sh = blank(r["flags"], p), blank(r["flags"], p)
            extra = f" {flag_links(r['flags'], p)}" if r["flags"] and r["kind"] == "value" else ""
            rws.append([f'<b>{usd(r["usd"], False)}</b>', tot, sh, e(r["detail"]) + extra, src_links(r["src"], compact=True)])
        first = at(m["id"], 10_000)
        hint = {"value": "priced from official figures", "penalty": "penalty exposure, not a price",
                "na": "not available at these amounts", "partial": "partly priced", "blank": "no official price"}[first["kind"]]
        if first["kind"] == "value":
            hint = f"{usd(first['total'])} at $10,000"
        head = "Penalty exposure" if m["cat"] == "prohibited" else "Total cost"
        out.append(f'<details id="L-{m["id"]}"><summary>{m["id"]} · {e(m["name"])}<small>{e(hint)}</small></summary>'
                   + table([("Amount", "num"), (head, "num"), ("Share of amount", "num"), ("Made up of", ""), ("Official source", "")], rws)
                   + "</details>")
    write(GUIDE / "costs.html", page("guide/costs.html", "Cost ladder", "Transfer and conversion cost of every CNY to USD method at each $10,000 step up to $400,000, from official tariffs.", "\n".join(out)))

    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["method_id", "method", "amount_usd", "status", "total_cost_usd", "share_of_amount", "made_up_of", "flags", "source_urls"])
    for m in METHODS:
        for r in LADDERS[m["id"]]:
            w.writerow([m["id"], m["name"], r["usd"], r["kind"],
                        "" if r["total"] is None else f'{r["total"]:.2f}',
                        "" if r["share"] is None else f'{D(r["share"]):.6f}',
                        r["detail"], " ".join(r["flags"]), " ".join(SOURCES[s]["url"] for s in r["src"])])
    write(DATA / "cost-ladder.csv", buf.getvalue())


def build_steps():
    out = ['<h1>Step by step</h1>',
           '<p class="lead">Exactly what to do for each lawful route, in order. Each step links to the rule or price list behind it.</p>',
           '<div class="note"><b>Before any route:</b> the money must have a lawful, documented source and the tax on it must be paid. Bring originals. Do not split one amount into several to avoid review. '
           + src_links(["CN-ART59", "CN-MEASURES"]) + "</div>"]
    for m in LAWFUL:
        rows = [[f"<b>{i}</b>", e(s["t"]), src_links(s["src"])] for i, s in enumerate(m["steps"], 1)]
        flags = f'<p class="small">Open points: {flag_links(m["flags"], "../")}</p>' if m["flags"] else ""
        out.append(f'<h2 id="{m["id"]}">{m["id"]} · {e(m["name"])} {status_badge(m)}</h2>'
                   f'<p><b>Who:</b> {e(m["who"])}</p>'
                   + table([("Step", "num"), ("What to do", ""), ("Official source", "")], rows) + flags
                   + f'<p class="small"><a href="costs.html#L-{m["id"]}">Cost at every amount</a> · <a href="methods.html#{m["id"]}">Pros and cons</a></p>')
    out.append('<h2>Prohibited routes</h2><div class="danger">No steps are given for splitting, borrowed quotas, money changers, false documents or crypto. See <a href="methods.html#X01">Methods</a> for why. '
               + src_links(["CN-FXREG", "CN-CRYPTO"]) + "</div>")
    write(GUIDE / "steps.html", page("guide/steps.html", "Step by step", "Step-by-step instructions for each lawful way to convert CNY to USD and wire it to the US, with official sources.", "\n".join(out)))


def tax_table(items, prefix="../"):
    rows = []
    for it in items:
        fig = e(it["figure"]) if it["figure"] else blank(it["flags"], prefix)
        extra = f"<small>Open: {flag_links(it['flags'], prefix)}</small>" if it["flags"] and it["figure"] else ""
        rows.append([f"<b>{e(it['item'])}</b>", fig, e(it["explain"]) + extra, src_links(it["src"])])
    return table([("Item", ""), ("Figure", ""), ("What it means for you", ""), ("Official source", "")], rows)


def build_taxes():
    pen_rows = []
    for n in (10_000, 50_000, 100_000, 200_000, 400_000):
        b = at("M01", n)
        fine = D(n) * D("0.30")
        pen_rows.append([f"<b>{usd(n, False)}</b>", f'{usd(b["total"])}<small>{pct(b["share"])}</small>',
                         f"up to {usd(fine, False)}", f"{usd(fine, False)}–{usd(n, False)}",
                         src_links(["CN-BOCTARIFF", "CN-FXREG"])])
    body = f"""
<h1>Taxes and penalties</h1>
<p class="lead">The "conversion penalty" is not one charge. The parts below depend on the transaction and personal facts; amounts cannot be assumed to be zero.</p>

<section class="card answer"><h2>In one paragraph</h2>
<p>Converting and wiring is not itself taxed in the rules read. China taxes the income (salary 3%–45%, gains and investment income 20%) and the bank wants proof that this was paid. The US generally taxes citizens on worldwide income; a foreign tax credit may be available subject to conditions and limits. Currency conversion may separately produce a US exchange gain or loss. What can go wrong: income never taxed, a prohibited route, or missed US reports. {src_links(["CN-IIT", "US-ABROAD", "US-FTC"])}</p></section>

<h2>China: tax on the money</h2>
{tax_table(TAXES["china"])}

<h2>China: fines for breaking the foreign-exchange rules</h2>
{tax_table(TAXES["china_penalties"])}

<h2>Lawful cost against penalty exposure</h2>
<p class="mut small">Why the prohibited routes are never worth it: the lawful cost next to the fine range on the same amount.</p>
{table([("Amount", "num"), ("Lawful cost (Bank of China wire)", "num"), ("Fine, ordinary case", "num"), ("Fine, serious case", "num"), ("Official source", "")], pen_rows)}

<h2>United States: tax</h2>
{tax_table(TAXES["us"])}

<h2>United States: reports and their penalties</h2>
{tax_table(TAXES["us_reporting"])}

<div class="note">This page reports what the cited pages say. It does not know your residence history, what was withheld, or what you filed. Take the linked sources and your records to a China tax office (12366) and a US tax preparer before a large transfer.</div>
"""
    write(GUIDE / "taxes.html", page("guide/taxes.html", "Taxes and penalties", "Breakdown of China and US tax, fines and reporting penalties when converting CNY to USD, with official sources.", body))


def build_flagged():
    rows = []
    for f in FLAGS.values():
        manual = "".join(f'<br><a class="src" href="{e(m["url"])}" target="_blank" rel="noopener">{e(m["label"])}</a>' for m in f.get("manual", []))
        rows.append([f'<b id="{f["id"]}">{f["id"]}</b>', f"<b>{e(f['topic'])}</b>", e(f["gap"]), e(f["action"]), src_links(f["src"]) + manual])
    exc = [[f"<b>{e(s['id'])}</b>", e(s["title"]), e(s["quote"]), src_links([s["id"]])] for s in SOURCES.values() if s["level"] == "excerpt"]
    body = f"""
<h1>Flagged for Review</h1>
<p class="lead">{len(FLAGS)} unresolved questions, assumptions and source limitations. Some prevent a personalized decision or complete cost estimate; blank values are not zero. Review all items that touch your case.</p>
{table([("ID", ""), ("Topic", ""), ("What is missing", ""), ("What to do", ""), ("Where to check", "")], rows)}

<p>Additional independent reviews: <a href="../audit-edbb7990/index.html">source-access and dated-quote audit</a> and <a href="../quality-713a97b7/index.html">cost and tax quality review</a>. They describe earlier snapshots and may include findings corrected since then.</p>

<h2>Sources seen only as an excerpt</h2>
<p class="mut small">The official page exists, but this session saw its text only in a search-engine excerpt. Figures from these are treated as unverified.</p>
{table([("Source", ""), ("Document", ""), ("Text seen", ""), ("Link to check", "")], exc)}
"""
    write(GUIDE / "flagged.html", page("guide/flagged.html", "Flagged for Review", "Unverified items left blank in the China Money guide, with links for manual review.", body))


def build_sources():
    used = {}
    for m in METHODS:
        for sid in m["src"] + [x for s in m["steps"] for x in s["src"]]:
            used.setdefault(sid, set()).add(m["id"])
    out = ['<h1>Sources</h1>',
           f'<p class="lead">{len(SOURCES)} official pages: regulators, tax authorities, statutes, and the banks\' and providers\' own price lists. {RECHECKED} were re-opened and re-read on {RETRIEVED} for this edition; the other {N_FULL - RECHECKED} were read in full on 2026-11-10 and keep that date. {N_EXC} were seen only as excerpts and are marked.</p>',
           '<p class="mut small">The quoted text is what was on the page when read. Chinese text is quoted in the original so it can be searched on the page.</p>']
    groups = []
    for s in SOURCES.values():
        if s["group"] not in groups:
            groups.append(s["group"])
    for g in groups:
        rows = []
        for s in SOURCES.values():
            if s["group"] != g:
                continue
            lvl = ('<span class="badge b-ok">read in full</span> ' if s["level"] == "full" else '<span class="badge b-blank">excerpt only</span> ') + f'<small>{e(s.get("checked", "2026-11-10"))}</small>'
            usedby = ", ".join(sorted(used.get(s["id"], []))) or "tables"
            rows.append([f'<b id="{s["id"]}">{e(s["id"])}</b>',
                         f'<a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["title"])}</a><small>{e(s["publisher"])}</small>',
                         e(s["quote"]), lvl, e(usedby)])
        out.append(f"<h2>{e(g)}</h2>" + table([("ID", ""), ("Official page", ""), ("Text relied on", ""), ("Checked", ""), ("Used by", "")], rows))
    write(GUIDE / "sources.html", page("guide/sources.html", "Sources", "Official sources behind every figure in the China Money guide, with quoted text.", "\n".join(out)))


def build_review():
    rules = []
    for r in REVIEW["rules"]:
        s = SCAN["rules"][r["id"]]
        ex = "".join(f'<small><code>{e(h["file"])}:{h["line"]}</code> — {e(h["excerpt"])}</small>' for h in s["examples"])
        state = (f'<span class="badge b-warn">{s["check"]} to check</span> ' if s["check"] else "") + \
                (f'<span class="badge b-ok">{s["consistent"]} consistent</span>' if s["consistent"] else "")
        if not s["lines"]:
            state = '<span class="badge b-ok">no lines found</span>'
        rules.append([f'<b>{r["id"]}</b>', f"<b>{e(r['label'])}</b>{ex}", f'{s["lines"]:,} lines in {s["files"]} files<br>{state}',
                      e(r["verdict"]), src_links(r["src"])])
    manual = [[f"<code>{e(m['where'])}</code>", e(m["finding"]), e(m["fix"]), src_links(m["src"])] for m in REVIEW["manual"]]
    areas = "".join(
        f'<li><code>{e(k)}</code> — {v["files"]} files, {v["lines"]:,} lines, {v["hits"]} rule matches</li>' for k, v in sorted(SCAN["areas"].items()))
    proc = "".join(f"<li>{e(x)}</li>" for x in REVIEW["process"])
    body = f"""
<h1>Repository review</h1>
<p class="lead">The repository holds {len(SCAN["areas"])} earlier editions and components of this research. An automated text scan applied a small set of rules to archived text. It does not substantively verify every line against its official source; matches and selected irregularities are listed for manual review.</p>

<div class="kpis">
<div class="kpi"><b>{SCAN["total_files"]:,}</b><span>archived files read</span></div>
<div class="kpi"><b>{SCAN["total_lines"]:,}</b><span>lines read</span></div>
<div class="kpi"><b>{len(REVIEW["rules"])}</b><span>rules, each tied to an official source</span></div>
<div class="kpi"><b>{SCAN["total_hits"]:,}</b><span>lines matched a rule</span></div>
</div>

<div class="note"><b>What "line by line" means here.</b> A script read every line of every archived text file and tested it against {len(REVIEW["rules"])} rules. Each rule states a fact confirmed on an official page. A matching line is marked "consistent" when its own wording already agrees with the fact, otherwise "to check". The marking is a text heuristic, not a legal judgment; the full list with file and line number is in <a href="data/scan-hits.csv">scan-hits.csv</a>. Snapshot taken at commit <code>{e(SCAN["scanned_at_commit"])}</code>.</div>

<h2>Irregularities found by rule</h2>
{table([("Rule", ""), ("What the line says", ""), ("Found", ""), ("What the official source says", ""), ("Official source", "")], rules)}

<h2>Irregularities found by reading</h2>
{table([("Where", ""), ("Irregularity", ""), ("What this guide does", ""), ("Official source", "")], manual)}

<h2>Process irregularities</h2>
<ul class="plain">{proc}</ul>

<h2>Audit of the 2026-11-11 refresh</h2>
<p>The inherited research records a dated recheck of priced inputs and sources; the per-source record distinguishes pages re-opened from older checks. The working record — which source was re-opened, what the re-read found, and the irregularities that came out of it — is in <a href="{REPO_URL}/blob/main/edition-db079cfc/verification/findings.md">edition-db079cfc/verification/findings.md</a> with the per-source table in <a href="{REPO_URL}/blob/main/edition-db079cfc/verification/source-recheck.md">source-recheck.md</a>.</p>

<h2>What was read</h2>
<ul class="plain small">{areas}</ul>
"""
    write(GUIDE / "repo-review.html", page("guide/repo-review.html", "Repository review", "Line-by-line rule scan of the archived repository against official sources, with irregularities.", body))


ARCHIVE = [(x["href"], x["title"], x["note"]) for x in load("archive.json")["entries"]]


def build_archive():
    for href, _, _ in ARCHIVE:
        assert (ROOT / href).is_file(), href
    tiles = "".join(f'<a class="tile" href="../{h}"><b>{e(t)}</b><span>{e(d) or "Archived edition."}</span></a>' for h, t, d in ARCHIVE)
    body = f"""
<h1>Archive</h1>
<p class="lead">Earlier editions built by parallel sessions. They are kept unchanged for reference and are superseded by this guide.</p>
<div class="danger"><b>Do not take figures from these pages.</b> They use different exchange-rate snapshots and some state rules that were abolished or repealed. See the <a href="repo-review.html">repository review</a> for what differs.</div>
<div class="tiles">{tiles}</div>
"""
    write(GUIDE / "archive.html", page("guide/archive.html", "Archive", "Archived earlier editions of the China Money research.", body))



def build_questions():
    pfx = "../"
    kd = QUESTIONS_DOC
    # Best way card
    best = kd["best_way"]
    best_routes = []
    for r in best["routes"]:
        if r["rank"] == "not":
            badge = '<span class="badge b-bad">Do not use</span>'
            rank = "✕"
        else:
            badge = '<span class="badge b-warn">Option ' + e(str(r["rank"])) + '</span>'
            rank = e(str(r["rank"]))
        best_routes.append([
            badge,
            f'<b>{e(r["route"])}</b><small>When: {e(r["when"])}</small>',
            e(r["why"]),
            e(r["when"]),
            src_links(r["src"])
        ])
    # Actually we want rank, route, why, when, source - but simpler table
    best_tbl = table([("Option", ""), ("Possible route", ""), ("Considerations", ""), ("When it applies", ""), ("Official source", "")], best_routes)

    # Known facts table
    known_rows = []
    for k in kd["known"]:
        known_rows.append([e(k["fact"]), e(k["implication"]), src_links(k["src"])])
    known_tbl = table([("What we already know (official source)", ""), ("What it means for your decision", ""), ("Official source", "")], known_rows)

    # Questions table - group by category
    # Build one big table with category grouping using <tr><th colspan>
    # For mobile, we use data-label, so we need to flatten but keep category as header row
    q_rows = []
    current_cat = None
    # We'll create category header rows manually via custom html, but easier: prepend category bold in question cell
    for q in QUESTIONS:
        cat = q["category"]
        # Compose question cell with category + ID
        qcell = f'<b id="{q["id"]}">{e(q["id"])} — {e(q["question"])}</b><small>Category: {e(cat)}</small>'
        have = f'<b>Have:</b> {e(q["have"])}<br><b>Missing:</b> {e(q["have_not"])}'
        ans = e(q["answer_if_known"])
        how = e(q["how_to_find"])
        flags = flag_links(q["flags"], pfx) if q["flags"] else '<span class="badge b-ok">no flag</span>'
        # flags column shows open items
        q_rows.append([qcell, have, ans, how, flags, src_links(q["src"])])

    q_tbl = table([("Question that blocks a decision", ""), ("Have vs. Missing", ""), ("Answer once known", ""), ("How to find the missing fact", ""), ("Open flag", ""), ("Official source", "")], q_rows)

    # Suggestions steps
    sugg_rows = []
    for s in kd["suggestions"]:
        sugg_rows.append([f'<b>Step {e(str(s["step"]))}: {e(s["title"])}</b>', e(s["action"]), e(s["delivers"]), src_links(s["src"])])
    sugg_tbl = table([("Step", ""), ("Do this", ""), ("It answers", ""), ("Official source", "")], sugg_rows)

    # Summary answer block
    body = f""" 
<h1>{e(kd["title"])}</h1>
<p class="lead">{e(kd["intro"])}</p>

<div class="note"><b>How to use this page.</b> If you cannot answer a question in the second column, you cannot yet pick a method or estimate a cost. Work the 8 steps at the bottom — they turn each blank into a paper you can hand to the bank.</div>

<h2>Best way to get money out with the least tax penalty (from official sources)</h2>
<p>{e(best["preamble"])}</p>
{best_tbl}
<div class="note"><b>Why no universal percentage?</b> Tax depends on the source of funds, tax residence, reporting history and other facts. A US foreign-currency gain may need separate analysis, and any foreign tax credit is conditional. Prior payment of China tax does not establish that only bank charges remain. {src_links(["CN-IIT", "US-ABROAD", "US-FTC", "US-988"])} {flag_links(["F23"], pfx)}</div>

<h2>What we already know — and what it decides</h2>
<p>These points are general research, not a determination of your eligibility, taxes or executable costs.</p>
{known_tbl}

<h2>16 questions that must be answered before any decision</h2>
<p class="mut small">Ordered from "who you are" → "where the money came from" → "tax paid" → "bank" → "US filing". Every row links to the rule that makes the question mandatory. <span class="badge b-blank">Flag</span> means the answer was left blank in the guide and is listed on Flagged for Review.</p>
{q_tbl}

<div class="danger"><b>Cannot be answered from the account balance alone.</b> Two people with USD 400,000 in the same bank will get different answers to Q02–Q05, Q07 and Q10–Q13 — one may wire in one step, the other may need a different procedure or approval. No estimate in the guide determines your eligibility.</div>

<h2>How to discover the missing information — 8 concrete steps</h2>
<p>Do these in order. Each step is a visit, call or download that replaces a blank with a document the bank will accept.</p>
{sugg_tbl}

<h2>What can be answered now vs. what needs your records</h2>
{table([("Can be answered now (no personal data needed)", ""), ("Needs your records before a decision", ""), ("Official source", "")], [
    ["<ul><li>Bank evidence requirements depend on the funds and the route.</li><li>The cited SAFE work-income rule requires identity and source evidence including tax documents; it does not establish eligibility for all assets.</li><li>Do not evade review or use false documents.</li><li>US currency gains, credits, reporting thresholds and penalties depend on the circumstances.</li></ul>", "<ul><li>Which of the 19 methods actually applies to your money (Q02–Q07).</li><li>Whether the China tax filing form is required above USD 50,000 (Q05).</li><li>Your bank's single-wire limit and its exact selling rate on the day (Q08, F02/F03).</li><li>Whether Wise eligibility and caps cover your amount (Q09).</li><li>Your prior US reporting and exposure to FBAR/8938/3520 and exchange gain (Q10–Q13).</li><li>The final all-in cost for your amount at that bank on that day — use the cost ladder as a cross-check.</li></ul>", src_links(["CN-ART59", "CN-FXREG", "US-8938FBAR", "US-988"])],
])}

<div class="card answer"><h2>Minimal viable next action (15 minutes)</h2><p>Open your bank app, export the 36-month statement and the current CNY balance. The statement may help identify the balance and source of funds; it may not answer either question on its own. If you do one thing, do step 1.</p></div>

<p class="mut small">Every row on this page carries an official source link per the verification rule. A blank or a flag means the value depends on your own documents — it was never estimated. Bring the sources and your papers to the bank (12366 for China tax, a US preparer for the US side) before a large transfer.</p>
""" 
    write(GUIDE / "questions.html", page("guide/questions.html", "Decision readiness", "Clear list of questions, information and answers that must be addressed before any decision, with suggestions to discover missing facts.", body))


def build_summary_md():
    def r(mid, n):
        x = at(mid, n)
        return f"{usd(x['total'])} ({pct(x['share'])})" if x["kind"] == "value" else "blank (unverified)"

    def link(sid):
        return f"[{SOURCES[sid]['short']}]({SOURCES[sid]['url']})"
    lines = [
        "# Executive summary — China money (CNY → USD)",
        "",
        f"Generated by `guide/build/build.py` from `guide/data/`. Official sources read {RETRIEVED}. "
        "Live site: https://sassnarep3-star.github.io/China1/ · full version: `guide/summary.html`.",
        "",
        "## Answer",
        "",
        f"1. **No rule read for this guide taxes the conversion itself.** The exposure is tax on the underlying income if tax is due but unpaid; SAFE says a tax voucher is not required for qualifying current-account income that is not taxable under the rules. {link('CN-ART59')}, {link('CN-WORKFX2025')}, {link('CN-IIT')}",
        f"2. **Lawful route:** passport + evidence of lawful source and amount + tax record where applicable; buy USD and wire to your own US account. The cited rule states no fixed cap for this documented-income route; the bank must confirm your eligibility and evidence. {link('CN-ART59')}, {link('CN-WORKFX2025')}, {link('CN-PR')}",
        f"3. **Cost (Bank of China wire into a Chase account):** {r('M01', 10_000)} at $10,000; {r('M01', 100_000)} at $100,000; {r('M01', 400_000)} at $400,000. {link('CN-FXBOARD')}, {link('CN-BOCTARIFF')}, {link('US-CHASE')}",
        f"4. **{wise_sentence()}** {link('PR-WISEFEE')}",
        f"5. **Avoid prohibited conduct:** evasion through splitting or false documents, illegal currency dealing, and prohibited virtual-currency activities. Fines up to 30% of the amount, 30%–100% if serious, possible criminal liability. {link('CN-FXREG')}, {link('CN-MEASURES')}, {link('CN-CRYPTO')}",
        f"6. **US side:** worldwide income may be taxable; a foreign tax credit may be available subject to conditions. Converting currency may create a separate US exchange gain or loss. FBAR generally applies if aggregate foreign accounts exceed $10,000; Form 8938 thresholds depend on residence and filing status. Penalties depend on facts and assessment date. {link('US-ABROAD')}, {link('US-FTC')}, {link('US-8938FBAR')}, {link('US-FBARPEN')}, {link('US-988')}",
        "",
        "## Cost at selected amounts",
        "",
        "| Amount | Bank of China wire | Wise | Source |",
        "|---|---|---|---|",
    ]
    for n in (10_000, 20_000, 30_000, 40_000, 50_000, 100_000, 200_000, 300_000, 400_000):
        lines.append(f"| {usd(n, False)} | {r('M01', n)} | {r('M10', n)} | {link('CN-BOCTARIFF')} · {link('PR-WISEFEE')} |")
    lines += [
        "",
        f"All {len(METHODS)} methods at all {len(TARGETS)} amounts: `guide/costs.html` and `guide/data/cost-ladder.csv`.",
        "",
        "## Open points",
        "",
        f"{len(FLAGS)} items are listed on `guide/flagged.html`; they include issues that prevent a personalized decision. Most relevant:",
        "",
    ]
    for fid in ("F01", "F02", "F03", "F13", "F22", "F23", "F24"):
        f = FLAGS[fid]
        lines.append(f"- **{fid} {f['topic']}** — {f['gap']} ({', '.join(link(s) for s in f['src'])})")
    lines += ["", "Research guide, not legal or tax advice.", ""]
    write(ROOT / "EXECUTIVE_SUMMARY.md", "\n".join(lines))


def build():
    build_home()
    build_summary()
    build_questions()
    build_methods()
    build_costs()
    build_steps()
    build_taxes()
    build_flagged()
    build_sources()
    build_review()
    build_archive()
    build_summary_md()


if __name__ == "__main__":
    build()
    print(f"built guide: {len(METHODS)} methods × {len(TARGETS)} amounts, {len(SOURCES)} sources, {len(FLAGS)} flagged items")
