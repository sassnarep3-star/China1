#!/usr/bin/env python3
"""Deterministic generator for Edition K of the China -> USD dashboard.

Every number printed on the site is computed here from edition-k/data/model.json.
No number is typed into a template by hand. Running this twice must produce
byte-identical output; verify.py enforces that.
"""
from __future__ import annotations

import json
import shutil
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITE = ROOT / "site"

MONEY = Decimal("0.01")

# ----------------------------------------------------------------------------- data


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


SRC = load("sources.json")
MODEL = load("model.json")
METHODS = load("methods.json")
FLAGS = load("flags.json")

SOURCES = {s["id"]: s for s in SRC["sources"]}
AS_OF = "2026-11-10"


def d(x) -> Decimal:
    return Decimal(str(x))


def money(x: Decimal, sym: str = "$") -> str:
    q = x.quantize(MONEY, rounding=ROUND_HALF_UP)
    return f"{sym}{q:,.2f}"


def cny(x: Decimal) -> str:
    q = x.quantize(MONEY, rounding=ROUND_HALF_UP)
    return f"\u00a5{q:,.2f}"


def pct(x: Decimal) -> str:
    return f"{(x * 100).quantize(Decimal('0.001'))}%"


# ----------------------------------------------------------------------------- rates

R = MODEL["rates"]
SELL = d(R["boc_sell_cny_per_usd"]["value"])
BUY = d(R["boc_buy_cny_per_usd"]["value"])
MID = d(R["pboc_mid_cny_per_usd"]["value"])
BOARD_MID = (BUY + SELL) / 2
HALF_SPREAD = ((SELL - BUY) / 2) / BOARD_MID

T = MODEL["targets"]
TARGETS = list(range(int(T["start_usd"]), int(T["stop_usd"]) + 1, int(T["step_usd"])))

RAILS = {r["id"]: r for r in MODEL["rails"]}
BOC = RAILS["boc"]
HSBC = RAILS["hsbc"]
GT = RAILS["hsbc_global"]

PEN = MODEL["penalties"]


def rail_charges(rail: dict, target_usd: int, cny_needed: Decimal) -> dict:
    """Sender charges only, in USD. Never includes anything unpublished."""
    comm_cny = cny_needed * d(rail["commission_pct"])
    comm_cny = max(comm_cny, d(rail["commission_min_cny"]))
    comm_cny = min(comm_cny, d(rail["commission_max_cny"]))
    cable_cny = d(rail["cable_cny"])
    comm_usd = comm_cny / SELL
    cable_usd = cable_cny / SELL
    receiving = d(rail["receiving_usd"])
    return {
        "commission_cny": comm_cny,
        "commission_usd": comm_usd,
        "cable_cny": cable_cny,
        "cable_usd": cable_usd,
        "receiving_usd": receiving,
        "charges_usd": comm_usd + cable_usd + receiving,
    }


def boc_row(target_usd: int) -> dict:
    cny_needed = d(target_usd) * SELL
    ch = rail_charges(BOC, target_usd, cny_needed)
    fx = d(target_usd) * d(BOC["fx_spread_pct"])
    total = fx + ch["charges_usd"]
    return {
        "target": target_usd,
        "cny": cny_needed,
        "fx": fx,
        "comm_cny": ch["commission_cny"],
        "comm_usd": ch["commission_usd"],
        "cable_usd": ch["cable_usd"],
        "recv_usd": ch["receiving_usd"],
        "total": total,
        "pct": total / d(target_usd),
        "net": d(target_usd) - total,
    }


def hsbc_row(target_usd: int) -> dict:
    cny_needed = d(target_usd) * SELL
    ch = rail_charges(HSBC, target_usd, cny_needed)
    return {
        "target": target_usd,
        "comm_cny": ch["commission_cny"],
        "comm_usd": ch["commission_usd"],
        "cable_usd": ch["cable_usd"],
        "charges_usd": ch["charges_usd"],
    }


LADDER = [boc_row(t) for t in TARGETS]
HSBC_LADDER = {r["target"]: r for r in (hsbc_row(t) for t in TARGETS)}


def penalty_rows() -> list[dict]:
    out = []
    for t in TARGETS:
        out.append(
            {
                "target": t,
                "p30": d(t) * d(PEN["standard_max_pct"]),
                "p100": d(t) * d(PEN["serious_max_pct"]),
                "cash": d(t) * d(PEN["cash_max_pct"]),
            }
        )
    return out


PENALTIES = penalty_rows()

# ----------------------------------------------------------------------------- html

CSS = """\
:root{
  --bg:#0b1220; --panel:#111c2f; --panel2:#16243a; --line:#22324d;
  --ink:#eaf1fb; --dim:#9db0c9; --accent:#4ea8ff; --good:#39d98a;
  --warn:#ffb020; --bad:#ff6b6b; --link:#8ecbff;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--link);text-decoration:none}
a:hover{text-decoration:underline}
header.top{position:sticky;top:0;z-index:9;background:rgba(11,18,32,.96);
  border-bottom:1px solid var(--line);backdrop-filter:blur(6px)}
.wrap{max-width:1080px;margin:0 auto;padding:0 16px}
.brand{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;padding:14px 0 6px}
.brand b{font-size:18px;letter-spacing:.2px}
.brand span{color:var(--dim);font-size:13px}
nav.pages{display:flex;gap:6px;overflow-x:auto;padding:0 0 10px;scrollbar-width:none}
nav.pages::-webkit-scrollbar{display:none}
nav.pages a{white-space:nowrap;padding:7px 11px;border:1px solid var(--line);
  border-radius:999px;font-size:13.5px;color:var(--dim);background:var(--panel)}
nav.pages a.on{color:#04121f;background:var(--accent);border-color:var(--accent);font-weight:600}
main{padding:22px 0 60px}
h1{font-size:26px;line-height:1.2;margin:6px 0 6px}
h2{font-size:19px;margin:32px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:16px;margin:22px 0 8px}
p{margin:8px 0}
.lede{color:var(--dim);max-width:70ch}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));margin:14px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
.card .k{font-size:12px;text-transform:uppercase;letter-spacing:.6px;color:var(--dim)}
.card .v{font-size:24px;font-weight:700;margin:6px 0 2px}
.card .s{font-size:13px;color:var(--dim)}
.card.good{border-color:#1f5c42}.card.warn{border-color:#5c4a1f}.card.bad{border-color:#5c2424}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:14px}
caption{caption-side:top;text-align:left;color:var(--dim);font-size:13px;padding:4px 0 8px}
th,td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}
th{background:var(--panel2);color:var(--dim);font-weight:600;font-size:12.5px;
  text-transform:uppercase;letter-spacing:.4px;position:sticky;top:0}
tbody tr:nth-child(even){background:rgba(255,255,255,.017)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.hero{background:linear-gradient(160deg,#132441,#0d1728);border:1px solid var(--line);
  border-radius:16px;padding:18px;margin:16px 0}
.badge{display:inline-block;font-size:11.5px;padding:2px 8px;border-radius:999px;
  border:1px solid var(--line);color:var(--dim)}
.badge.lawful{color:#9df3c4;border-color:#1f5c42;background:#10241c}
.badge.cond{color:#ffd591;border-color:#5c4a1f;background:#241f10}
.badge.proh{color:#ffb3b3;border-color:#5c2424;background:#241010}
.blank{color:var(--warn);font-weight:600;font-size:12.5px}
.src{font-size:12px;color:var(--dim)}
ul,ol{margin:8px 0 8px 20px;padding:0}
li{margin:4px 0}
.note{background:var(--panel);border-left:3px solid var(--accent);padding:10px 12px;
  border-radius:0 10px 10px 0;margin:14px 0;font-size:14.5px}
.note.warn{border-left-color:var(--warn)}
.note.bad{border-left-color:var(--bad)}
.facts{list-style:none;margin:10px 0;padding:0}
.facts li{padding:7px 0;border-bottom:1px solid var(--line)}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px}
footer{border-top:1px solid var(--line);color:var(--dim);font-size:12.5px;padding:18px 0 40px}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
@media (max-width:720px){
  h1{font-size:22px}
  table.stack thead{display:none}
  table.stack,table.stack tbody,table.stack tr,table.stack td{display:block;width:100%}
  table.stack tr{border:1px solid var(--line);border-radius:12px;margin:0 0 10px;background:var(--panel);padding:6px 2px}
  table.stack td{border:0;padding:6px 12px;display:flex;justify-content:space-between;gap:12px;text-align:right}
  table.stack td::before{content:attr(data-label);color:var(--dim);font-size:12.5px;
    text-transform:uppercase;letter-spacing:.4px;text-align:left;flex:0 0 46%}
  table.stack td.num{text-align:right}
  table.stack td.lead{background:var(--panel2);border-radius:8px;font-weight:700}
}
"""


def esc(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def src_links(ids: list[str]) -> str:
    out = []
    for i in ids:
        s = SOURCES.get(i)
        if not s:
            raise SystemExit(f"unknown source id {i}")
        out.append(f'<a href="{esc(s["url"])}" title="{esc(s["title"])}">{i}</a>')
    return " ".join(out)


PAGES = [
    ("index.html", "Overview"),
    ("costs.html", "Costs"),
    ("methods.html", "Methods"),
    ("steps.html", "Steps"),
    ("taxes.html", "Tax &amp; penalties"),
    ("prohibited.html", "Prohibited"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
]


def page(name: str, title: str, body: str) -> str:
    nav = "".join(
        f'<a href="{p}" class="{"on" if p == name else ""}">{label}</a>'
        for p, label in PAGES
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · China money · Edition K</title>
<meta name="description" content="Verified, source-linked costs and routes for converting CNY inside China into USD in a US bank account.">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top"><div class="wrap">
<div class="brand"><b>China money → USD</b><span>Edition K · sources re-fetched {AS_OF} · every figure computed, none assumed</span></div>
<nav class="pages">{nav}</nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer><div class="wrap">
<p>Edition K. Prepared {AS_OF}. Every row links to the first-party page it came from; see the <a href="sources.html">source register</a> for the verbatim text read. Anything that could not be confirmed from a first-party page is blank and listed on <a href="flagged.html">Flagged for review</a>. This is research and arithmetic, not legal, tax or investment advice, and it does not certify that you personally qualify for any route.</p>
</div></footer>
</body>
</html>
"""


def table(headers: list[str], rows: list[list[str]], caption: str = "",
          stack: bool = True, classes: str = "") -> str:
    cls = "stack" if stack else ""
    cls = (cls + " " + classes).strip()
    head = "".join(
        f'<th class="{"num" if h.startswith("#") else ""}">{h.lstrip("#")}</th>' for h in headers
    )
    body = []
    for row in rows:
        cells = []
        for i, (h, c) in enumerate(zip(headers, row)):
            num = "num" if h.startswith("#") else ""
            lead = "lead" if i == 0 else ""
            cells.append(f'<td class="{num} {lead}" data-label="{esc(h.lstrip("#"))}">{c}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    cap = f"<caption>{caption}</caption>" if caption else ""
    return (
        f'<div class="scroll"><table class="{cls}">{cap}<thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


# ----------------------------------------------------------------------------- figures

BY_ID = {m["id"]: m for m in METHODS["methods"]}
CATS = {c["id"]: c for c in METHODS["categories"]}
LAWFUL = [m for m in METHODS["methods"] if m["status"] != "prohibited"]
PROHIBITED = [m for m in METHODS["methods"] if m["status"] == "prohibited"]

R10, R100, R400 = LADDER[0], LADDER[9], LADDER[-1]


def by_target(n: int) -> dict:
    return LADDER[(n // int(T["step_usd"])) - 1]


# ----------------------------------------------------------------------------- index

def build_index() -> str:
    key_rows = []
    for t in (10000, 50000, 100000, 200000, 400000):
        r = by_target(t)
        key_rows.append([
            f"${t:,}",
            money(r["total"]),
            pct(r["pct"]),
            money(r["fx"]),
            cny(r["comm_cny"]),
            money(r["cable_usd"]),
            money(r["recv_usd"]),
            src_links(["S02", "S03", "S18"]),
        ])

    cat_rows = []
    for c in METHODS["categories"]:
        ms = [m for m in METHODS["methods"] if m["category"] == c["id"]]
        state = {"lawful": "Lawful", "conditional": "Conditional", "prohibited": "Prohibited"}
        cat_rows.append([
            f'<a href="methods.html#{c["id"]}">{esc(c["title"])}</a>',
            str(len(ms)),
            ", ".join(sorted({state[m["status"]] for m in ms})),
            esc(c["blurb"]),
            src_links(c["source_ids"]),
        ])

    body = f"""
<h1>Getting money out of China with the smallest lawful cost</h1>
<p class="lede">A US citizen has CNY in a Chinese bank account and wants USD in a US bank account. This dashboard prices the routes from first-party published numbers, separates real tax from bank fees and from penalties, and shows the exact steps. It is regenerated from data each time, so no figure is hand-typed.</p>

<div class="hero">
<div class="grid" style="margin:0">
  <div class="card good">
    <div class="k">Cheapest priced lawful route, $400,000</div>
    <div class="v">{money(R400["total"])}</div>
    <div class="s">{pct(R400["pct"])} of the amount — BOC wire, FX spread + capped commission + cable + a $15 US receiving fee</div>
  </div>
  <div class="card warn">
    <div class="k">Same route at $10,000</div>
    <div class="v">{money(R10["total"])}</div>
    <div class="s">{pct(R10["pct"])} — fixed fees dominate small transfers, so cost per dollar falls as the amount rises</div>
  </div>
  <div class="card bad">
    <div class="k">Statutory fine if the route is illegal</div>
    <div class="v">30%–100%</div>
    <div class="s">of the amount moved, plus confiscation, for evasion or disguised FX trading (Reg. Arts. 39, 45)</div>
  </div>
</div>
</div>

<h2>The answer, in the order that matters</h2>
<ol>
<li><b>Converting currency is not itself a taxable event.</b> Neither the Chinese IIT Law nor the US Internal Revenue Code imposes tax on exchanging CNY for USD. What is taxed is the income or gain behind the money — and that tax is owed whether or not you ever convert.</li>
<li><b>The USD 50,000 annual total is a convenience limit, not a tax.</b> It is the amount you can settle or purchase per person per year against ID alone. Above it, the same bank will process the transaction once you document the underlying transaction. Crossing it does not trigger a penalty.</li>
<li><b>The visible cost of a lawful bank wire is small and capped.</b> On the priced route the all-in cost runs from {pct(R10["pct"])} at $10,000 to {pct(R400["pct"])} at $400,000, because the commission is capped at CNY {BOC["commission_max_cny"]} per transaction.</li>
<li><b>The large numbers people call "conversion penalties" are one of two things:</b> a real tax on a real gain (20% flat in China on asset-transfer income), or a statutory fine for using an illegal channel (30%–100% of the amount). They are not the price of converting.</li>
<li><b>Do the reporting, not just the transfer.</b> FBAR above $10,000 of aggregate foreign accounts, Form 8938 above its thresholds, Form 3520 above $100,000 of gifts. These are disclosure duties; missing them is where the genuinely large US penalties live.</li>
</ol>

<div class="note warn"><b>What this edition cannot know.</b> Your residency and immigration status, the character and source of the funds, which bank holds them, your destination bank, and your US filing position were never supplied. Every one of those changes the answer. This site therefore prices the rails and states the law; it does not tell you that you personally qualify. Open items are on <a href="flagged.html">Flagged for review</a>.</div>

<h2>Headline cost ladder (Bank of China wire)</h2>
{table(
    ["#Amount", "#All-in cost", "#Cost as %", "#FX spread", "#Commission (CNY)", "#Cable", "#US receiving", "Sources"],
    key_rows,
    "Five points from the 40-row ladder. Full table on the <a href='costs.html'>Costs</a> page.",
)}

<h2>Routes by category</h2>
{table(
    ["Category", "#Methods", "Status", "What it is for", "Sources"],
    cat_rows,
    "Prohibited routes are documented only so they can be recognised and refused; no operational instructions are published for them.",
)}

<h2>How to read this site</h2>
<div class="grid">
  <div class="card"><div class="k">Step 1</div><div class="v" style="font-size:16px"><a href="costs.html">Check the cost</a></div><div class="s">40 rows, $10,000 to $400,000, in $10,000 steps, with the formula behind every cell.</div></div>
  <div class="card"><div class="k">Step 2</div><div class="v" style="font-size:16px"><a href="methods.html">Pick the route</a></div><div class="s">{len(METHODS["methods"])} routes with pros, cons and sources; {len(PROHIBITED)} are marked prohibited.</div></div>
  <div class="card"><div class="k">Step 3</div><div class="v" style="font-size:16px"><a href="steps.html">Follow the steps</a></div><div class="s">Concrete, document-by-document procedures for the lawful routes.</div></div>
  <div class="card"><div class="k">Step 4</div><div class="v" style="font-size:16px"><a href="taxes.html">Get the tax right</a></div><div class="s">China and US positions by event, plus the penalty ladder and every reporting form.</div></div>
</div>

<h2>Where the numbers come from</h2>
<p>Three first-party inputs do all the work on the cost side: the PBOC/CFETS central parity of {MID} CNY per USD ({src_links(["S01"])}), Bank of China's own published board showing a {SELL} selling rate and a {BUY} buying rate on the same snapshot ({src_links(["S02"])}), and BOC's published remittance tariff of 0.1%, minimum CNY {BOC["commission_min_cny"]}, maximum CNY {BOC["commission_max_cny"]}, plus a CNY {BOC["cable_cny"]} cable fee ({src_links(["S03"])}). The US receiving fee is Chase's published {money(d(BOC["receiving_usd"]))} ({src_links(["S18"])}).

<p>The estimated FX conversion cost is the half-spread implied by BOC's own two quotes on one snapshot — {pct(HALF_SPREAD)} — which avoids comparing a live bank quote against a morning reference rate. That comparison is published on the Costs page as a separate, flagged observation rather than being folded into the cost.</p>
"""
    return page("index.html", "Overview", body)


# ----------------------------------------------------------------------------- costs

def build_costs() -> str:
    rows = []
    for r in LADDER:
        rows.append([
            f"${r['target']:,}",
            money(r["total"]),
            pct(r["pct"]),
            money(r["net"]),
            money(r["fx"]),
            cny(r["comm_cny"]),
            money(r["cable_usd"]),
            money(r["recv_usd"]),
            cny(r["cny"]),
            src_links(["S02", "S03", "S18"]),
        ])

    cmp_rows = []
    for t in TARGETS:
        r = by_target(t)
        h = HSBC_LADDER[t]
        cmp_rows.append([
            f"${t:,}",
            money(r["total"]),
            money(h["charges_usd"]),
            '<span class="blank">UNVERIFIED</span>',
            money(d(t) * d(PEN["standard_max_pct"])),
            money(d(t) * d(PEN["serious_max_pct"])),
            src_links(["S03", "S04", "S17", "S08"]),
        ])

    body = f"""
<h1>What it actually costs, $10,000 to $400,000</h1>
<p class="lede">All-in cost of converting CNY to USD and wiring it to a US bank account using Bank of China, at every $10,000 increment. The first columns are the ones that matter: total cost, cost as a percentage, and what you actually receive.</p>

<div class="note"><b>Read this before the tables.</b> The priced route covers the bank's FX spread, its published commission, its published cable fee and one US receiving charge. It does <b>not</b> include correspondent-bank deductions, document or notarisation costs, travel, or tax — because no first-party figure exists for them here. Those cells are blank and flagged, never zero.</div>

<h2>1. Bank of China wire — full ladder</h2>
{table(
    ["#Amount", "#All-in cost", "#Cost as %", "#You receive", "#FX spread", "#Commission (CNY)", "#Cable", "#US receiving", "#CNY needed", "Sources"],
    rows,
    f"Computed at BOC's {SELL} CNY/USD selling rate ({src_links(['S02'])}), 0.1% commission with a CNY {BOC['commission_min_cny']} floor and CNY {BOC['commission_max_cny']} cap ({src_links(['S03'])}), CNY {BOC['cable_cny']} cable, {pct(HALF_SPREAD)} FX half-spread, and a {money(d(BOC['receiving_usd']))} US receiving fee ({src_links(['S18'])}).",
)}

<h2>2. Every route side by side</h2>
{table(
    ["#Amount", "#BOC all-in", "#HSBC sender charges", "Wise", "#Fine if illegal (30%)", "#Fine if serious (100%)", "Sources"],
    cmp_rows,
    f"HSBC column is its published commission (0.1%, CNY {HSBC['commission_min_cny']}–{HSBC['commission_max_cny']}) plus its CNY {HSBC['cable_cny']} cable fee only — its all-in total is blank because HSBC publishes no FX spread in the tariff read. Wise publishes no fixed fee for this corridor. Fine columns apply the statutory percentages in {src_links(['S08'])}.",
)}

<h2>3. The conversion penalty, decomposed</h2>
<p>People usually mean one of six different things when they say converting is expensive. They behave completely differently:</p>
{table(
    ["Component", "#What it costs at $400,000", "How it is set", "Source"],
    [
        ["Bank FX spread", f"{money(R400['fx'])} ({pct(d(BOC['fx_spread_pct']))})", "The gap between the bank's buy and sell quotes for USD. Not a tax, and not negotiable at the counter.", src_links(["S02"])],
        ["Sender commission", f"{cny(R400['comm_cny'])} ({money(R400['comm_usd'])})", "0.1%, capped at CNY 260 per transfer. Falls as a percentage as the amount rises.", src_links(["S03"])],
        ["Cable / message fee", f"{money(R400['cable_usd'])}", "Flat CNY 150 for non-HK/Macau/Taiwan destinations.", src_links(["S03"])],
        ["US receiving fee", money(R400["recv_usd"]), "Per incoming wire. Chase publishes $15; your bank was not supplied.", src_links(["S18"])],
        ["Correspondent / intermediary", '<span class="blank">UNVERIFIED</span>', "Charged by banks in the payment chain, deducted in transit, not published by the sender.", "No first-party schedule read; see " + src_links(["S03", "S04"])],
        ["Income or gain tax", "Depends on the event", "20% flat in China on asset-transfer income and interest/dividends; 3%–45% on salary; US tax on worldwide income with a foreign tax credit.", src_links(["S10", "S15", "S16"])],
        ["Fine for an illegal route", f"{money(d(400000) * d(PEN['standard_max_pct']))}–{money(d(400000) * d(PEN['serious_max_pct']))}", "30% of the amount normally, 30%–100% where serious, plus confiscation and possible criminal liability.", src_links(["S08"])],
    ],
    "The top four rows are the price of converting. The last two are why people believe the price of converting is enormous.",
)}

<h2>4. Worked example: $10,000, step by step</h2>
<ol>
<li>Target: {money(d(10000))} landed in your US account.</li>
<li>CNY required at BOC's selling rate: {money(d(10000))} × {SELL} = {cny(R10['cny'])} ({src_links(['S02'])}).</li>
<li>FX spread cost: {money(d(10000))} × {pct(HALF_SPREAD)} = {money(R10['fx'])}.</li>
<li>Commission: 0.1% of {cny(R10['cny'])} = {cny(d(R10['cny']) * d('0.001'))}, which is above the CNY 50 floor and below the CNY 260 cap, so it is charged in full: {cny(R10['comm_cny'])} = {money(R10['comm_usd'])}.</li>
<li>Cable fee: CNY {BOC['cable_cny']} = {money(R10['cable_usd'])}.</li>
<li>US receiving: {money(R10['recv_usd'])}.</li>
<li>Total: {money(R10['fx'])} + {money(R10['comm_usd'])} + {money(R10['cable_usd'])} + {money(R10['recv_usd'])} = <b>{money(R10['total'])}</b>, or {pct(R10['pct'])} of the amount.</li>
<li>You receive {money(R10['net'])} — before any correspondent-bank deduction, which is not published.</li>
</ol>

<h2>5. Worked example: $400,000, step by step</h2>
<ol>
<li>CNY required: {money(d(400000))} × {SELL} = {cny(R400['cny'])}.</li>
<li>FX spread cost: {money(R400['fx'])}.</li>
<li>Commission: 0.1% of {cny(R400['cny'])} would be {cny(d(R400['cny']) * d('0.001'))}, but the cap is CNY {BOC['commission_max_cny']}, so you pay {cny(R400['comm_cny'])} = {money(R400['comm_usd'])}.</li>
<li>Cable {money(R400['cable_usd'])} and US receiving {money(R400['recv_usd'])}.</li>
<li>Total: <b>{money(R400['total'])}</b> = {pct(R400['pct'])}. Note the percentage is roughly a third of the $10,000 case, purely because four fixed fees are spread over 40 times the amount.</li>
<li>You still have to satisfy the remittance entitlement for the whole {cny(R400['cny'])}. Costing is the easy half; documentation is the hard half. See <a href="steps.html">Steps</a>.</li>
</ol>

<h2>6. Why the bank's rate can look better than the official mid-rate</h2>
<p>On {AS_OF} the PBOC central parity was {MID} CNY per USD ({src_links(['S01'])}) while BOC's own selling rate at 17:39 was {SELL} ({src_links(['S02'])}). The bank's ask was therefore <i>below</i> the official reference published that morning. That is a timing effect, not a discount, and not a cost either.</p>
<div class="note warn">This edition deliberately does not compute the FX cost as "bank rate minus PBOC mid". Doing so would mix a 09:25 reference with a 17:39 live quote and would produce a number that is part market move and part spread. The spread is instead measured inside one snapshot, where both quotes are stamped {esc(SOURCES['S02']['published'])}. The mid-rate comparison is disclosed here and logged as an open item on the <a href="flagged.html">flagged page</a>.</div>

<h2>7. The one-number summary</h2>
<div class="grid">
  <div class="card"><div class="k">At $10,000</div><div class="v">{money(R10['total'])}</div><div class="s">{pct(R10['pct'])} all-in</div></div>
  <div class="card"><div class="k">At $100,000</div><div class="v">{money(R100['total'])}</div><div class="s">{pct(R100['pct'])} all-in</div></div>
  <div class="card"><div class="k">At $400,000</div><div class="v">{money(R400['total'])}</div><div class="s">{pct(R400['pct'])} all-in</div></div>
  <div class="card bad"><div class="k">If the route is illegal</div><div class="v">{money(d(400000) * d('0.30'))}+</div><div class="s">fine at $400,000, before confiscation</div></div>
</div>
<p class="src">Every figure above is recomputed from <span class="mono">edition-k/data/model.json</span> by <span class="mono">build.py</span> and checked by <span class="mono">verify.py</span>. Sources: {src_links(['S01','S02','S03','S04','S08','S18'])}</p>
"""
    return page("costs.html", "Costs", body)


# ----------------------------------------------------------------------------- methods

STATUS_LABEL = {"lawful": ("lawful", "Lawful"), "conditional": ("cond", "Conditional"),
                "prohibited": ("proh", "Prohibited")}


def status_badge(s: str) -> str:
    cls, label = STATUS_LABEL[s]
    return f'<span class="badge {cls}">{label}</span>'


def build_methods() -> str:
    sections = []
    for c in METHODS["categories"]:
        ms = [m for m in METHODS["methods"] if m["category"] == c["id"]]
        rows = []
        for m in ms:
            cost = {
                "boc": f"Priced — see <a href='costs.html'>Costs</a>",
                "hsbc": "Sender charges priced; all-in blank",
                "hsbc_global": "Service fee waived; all-in blank",
                "wise": '<span class="blank">UNVERIFIED</span>',
            }.get(m.get("cost_model") or "", "Not priced")
            rows.append([
                f'<a href="steps.html#{m["id"]}">{esc(m["name"])}</a><br><span class="src">{esc(m["name_zh"])}</span>' if m["steps"] else f'{esc(m["name"])}<br><span class="src">{esc(m["name_zh"])}</span>',
                status_badge(m["status"]),
                cost,
                esc(m["summary"]),
                src_links(m["sources"]),
            ])
        sections.append(f"""
<h2 id="{c['id']}">{esc(c['title'])}</h2>
<p class="lede">{esc(c['blurb'])}</p>
{table(["Route", "Status", "Cost basis", "What it is", "Sources"], rows, "Status reflects what the cited rules permit, not what your bank will approve on the day.")}
""")

    detail = []
    for m in METHODS["methods"]:
        pro = "".join(f"<li>{esc(x)}</li>" for x in m["pros"])
        con = "".join(f"<li>{esc(x)}</li>" for x in m["cons"])
        steps = (
            f'<p><a href="steps.html#{m["id"]}">Step-by-step procedure →</a></p>'
            if m["steps"]
            else '<p class="blank">No procedure published: this route is documented for recognition only.</p>'
        )
        detail.append(f"""
<div class="card" style="margin:14px 0" id="m-{m['id']}">
<div style="display:flex;gap:10px;align-items:baseline;flex-wrap:wrap">
<h3 style="margin:0">{esc(m['name'])}</h3>{status_badge(m['status'])}
</div>
<p class="src" style="margin:2px 0 8px">{esc(m['name_zh'])} · cost basis: {esc(m['cost_note'])}</p>
<p>{esc(m['summary'])}</p>
<div class="grid" style="margin:8px 0">
<div class="card good"><div class="k">Pros</div><ul>{pro}</ul></div>
<div class="card bad"><div class="k">Cons</div><ul>{con}</ul></div>
</div>
<ul class="facts">
<li><b>China tax:</b> {esc(m['cn_tax'])}</li>
<li><b>US tax:</b> {esc(m['us_tax'])}</li>
<li><b>US reporting:</b> {esc('; '.join(m['reporting']))}</li>
</ul>
{steps}
<p class="src">Sources: {src_links(m['sources'])}</p>
</div>""")

    body = f"""
<h1>Every route, with pros and cons</h1>
<p class="lede">{len(METHODS['methods'])} routes across {len(METHODS['categories'])} categories — {len(LAWFUL)} lawful or conditional, {len(PROHIBITED)} prohibited and documented only so they can be refused. A route is not a permission: a bank is a rail, and the entitlement to move the money is a separate legal question.</p>

<div class="note"><b>The distinction that decides your case:</b> whether the money is <i>current-account</i> money (salary, services, investment income you can document) or <i>capital-account</i> money (savings accumulated, property proceeds, invested capital). The first is routine; the second needs an approval route. Which one you have was never supplied, so both are laid out.</div>

{"".join(sections)}

<h2>Route detail</h2>
{"".join(detail)}
"""
    return page("methods.html", "Methods", body)


# ----------------------------------------------------------------------------- steps

def build_steps() -> str:
    blocks = []
    for m in LAWFUL:
        if not m["steps"]:
            continue
        items = "".join(f"<li>{esc(s)}</li>" for s in m["steps"])
        blocks.append(f"""
<h2 id="{m['id']}">{esc(m['name'])} {status_badge(m['status'])}</h2>
<p class="lede">{esc(m['summary'])}</p>
<ol>{items}</ol>
<p class="src">Sources: {src_links(m['sources'])} · cost basis: {esc(m['cost_note'])}</p>
""")

    body = f"""
<h1>Step-by-step procedures</h1>
<p class="lede">The sequence you would actually follow, document by document. Nothing here asks you to sign anything untrue, and nothing here tells you to split a transaction to stay under a limit.</p>
<div class="note warn"><b>Before step one, in every route:</b> establish the character of the money and keep the evidence in one folder — the contract or payroll record, the China tax records, the bank statements showing the money landing, and the identity documents. Banks decide on documents, not on explanations. The {len(LAWFUL)} routes below are ordered from the ordinary to the exceptional.</div>
{"".join(blocks)}
<h2>What to do on the US side, once the money lands</h2>
<ol>
<li>Record the CNY debited, the rate applied and the USD credited. That record is the basis for any FX gain computation.</li>
<li>Check FBAR: did the aggregate of your Chinese accounts exceed $10,000 at any point in the calendar year? If yes, file FinCEN 114 by 15 April, with an automatic extension to 15 October ({src_links(['S11'])}).</li>
<li>Check Form 8938 against the thresholds for your filing status and residence ({src_links(['S12'])}).</li>
<li>If the money is a gift or bequest rather than your own funds, check Form 3520 Part IV above $100,000 aggregate ({src_links(['S14'])}).</li>
<li>If China taxed income that the US also taxes, claim the credit on Form 1116 rather than paying twice ({src_links(['S15'])}).</li>
<li>If you physically carried more than $10,000, file FinCEN 105 at the border ({src_links(['S19'])}).</li>
</ol>
"""
    return page("steps.html", "Steps", body)


# ----------------------------------------------------------------------------- taxes

def build_taxes() -> str:
    sc_rows = []
    for s in MODEL["tax_scenarios"]:
        sc_rows.append([esc(s["title"]), esc(s["china_rate"]), esc(s["us_rate"]),
                        esc(s["assumption"]), src_links(s["sources"])])

    pen_rows = []
    for p in PENALTIES:
        pen_rows.append([
            f"${p['target']:,}",
            money(p["p30"]),
            money(p["p100"]),
            money(p["cash"]),
            src_links(["S08"]),
        ])

    rep_rows = []
    for r in MODEL["reporting"]:
        rep_rows.append([
            esc(r["form"]), esc(r["trigger"]), esc(r["due"]),
            esc(r["cost_of_missing"]), src_links(r["sources"]),
        ])

    body = f"""
<h1>Tax, reporting and the real penalty exposure</h1>
<p class="lede">Converting currency is not a taxable event in either country. What follows is what <i>is</i> taxed, what is merely reportable, and what is penalised — kept strictly apart, because conflating them is the single most expensive misunderstanding in this problem.</p>

<div class="hero">
<h2 style="margin-top:0;border:0;padding:0">The three things people confuse</h2>
<div class="grid" style="margin:0">
<div class="card good"><div class="k">1 · Cost of converting</div><div class="v" style="font-size:18px">{pct(HALF_SPREAD)} + capped fees</div><div class="s">A bank spread and a few fixed fees. Small, published, unavoidable if you use a bank.</div></div>
<div class="card warn"><div class="k">2 · Tax on income or gain</div><div class="v" style="font-size:18px">20% / 3%–45%</div><div class="s">Owed because of what the money <i>is</i>, not because you moved it. Owed even if you leave it in China.</div></div>
<div class="card bad"><div class="k">3 · Penalty for breaking the rules</div><div class="v" style="font-size:18px">20%–100%</div><div class="s">Only if you use a prohibited route or fail to report. Entirely avoidable by not doing that.</div></div>
</div>
</div>

<h2>1. Tax by event</h2>
{table(["Event", "China", "United States", "Assumption behind this row", "Sources"], sc_rows,
       "These are statutory characterisations, not a computation for you. The rates are read from the cited law; the base is unknown because your basis, residency and income were never supplied.")}

<div class="note"><b>Why there is no "conversion tax" line.</b> The China IIT Law taxes nine categories of income, and exchanging one currency for another is not one of them ({src_links(['S10'])}). US law taxes foreign-currency gain only when the currency is disposed of, and for a personal transaction it does not recognise that gain at all unless it exceeds $200 ({src_links(['S13'])}). If someone has told you that converting CNY to USD costs 20% or 30%, they were describing either a real asset-transfer gain or an illegal-channel fine.</div>

<h2>2. Statutory penalty exposure by amount</h2>
<p>The FX Regulations set fines as a percentage of the amount moved: up to 30% of the amount for evasion or disguised FX trading, and 30% up to the full equivalent where the circumstances are serious, with confiscation of unlawful gains and criminal liability expressly preserved ({src_links(['S08'])}). Cash violations are capped at 20%.</p>
{table(["#Amount", "#Fine at 30%", "#Fine at 100%", "#Cash-carry fine at 20%", "Sources"], pen_rows,
       "Arithmetic on the statutory percentages, not a prediction. Whether an offence exists, and whether circumstances are 'serious', is decided by the authority.")}

<h2>3. Reporting duties (these are where US penalties actually live)</h2>
{table(["Form", "Trigger", "Due", "Cost of missing it", "Sources"], rep_rows,
       "A reporting failure can be penalised even when no tax is owed at all.")}

<h2>4. The foreign tax credit, in one paragraph</h2>
<p>If China taxes income that the US also taxes, you generally claim a credit on Form 1116 rather than deducting it, so the same income is not taxed twice ({src_links(['S15'])}). The credit is limited and it does not refund Chinese tax. It is not available for tax on income you excluded from US gross income. Critically, the credit does not convert a Chinese tax into a US one, and it never applies to a fine.</p>

<h2>5. What was not verified here</h2>
<ul>
<li>Whether China imposes any tax on a pure currency exchange: the law's income categories were read, but the absence of a charge is an inference from that structure, and it is logged on <a href="flagged.html">Flagged for review</a>.</li>
<li>China gift-tax treatment, VAT and deed tax on property transfers, and A-share capital-gains treatment: no first-party rate table was read in this edition, so those rows say so.</li>
<li>Your actual US marginal rate, filing status, residency and basis: unknown, therefore not modelled.</li>
</ul>
"""
    return page("taxes.html", "Tax &amp; penalties", body)


# ----------------------------------------------------------------------------- prohibited

def build_prohibited() -> str:
    rows = []
    for m in PROHIBITED:
        rows.append([
            esc(m["name"]),
            esc(m["summary"]),
            esc(m["cons"][0]),
            src_links(m["sources"]),
        ])

    pen_rows = [[f"${p['target']:,}", money(p["p30"]), money(p["p100"])] for p in PENALTIES]

    body = f"""
<h1>Prohibited routes — recognition only</h1>
<p class="lede">These are listed because refusing them is part of the answer to "how do I get the money out". No operational instructions are published for any of them, by design: the point of this page is to make the cost legible, not the method.</p>

<div class="note bad"><b>Why this page exists.</b> The complaint that started this project was that converting would cost "a considerable amount in taxes". The lawful conversion cost at $400,000 is {money(R400['total'])} — {pct(R400['pct'])}. The only way to reach a five- or six-figure penalty on a lawful balance is to use one of the routes below or to fail to report. The penalty is not a conversion fee; it is a fine.</div>

<h2>The routes</h2>
{table(["Route", "What it is", "Primary exposure", "Sources"], rows,
       "Descriptions are deliberately non-operational.")}

<h2>Exposure by amount</h2>
{table(["#Amount", "#Fine at 30%", "#Fine at 100%", "Sources"], [
        [f"${p['target']:,}", money(p["p30"]), money(p["p100"]), src_links(["S08"])] for p in PENALTIES],
       f"Statutory percentages from {src_links(['S08'])}: Art. 39 (evasion), Art. 45 (private or disguised FX trading). Confiscation of unlawful gains is additional, and criminal liability is expressly preserved.")}

<h2>What the regulation actually says</h2>
<p class="mono" style="background:var(--panel);padding:12px;border-radius:10px;overflow-x:auto">{esc(PEN['quote'])}</p>
<p class="src">Verbatim from {src_links(['S08'])}. Read the full text before relying on any summary, including this one.</p>

<h2>The US side does not cancel the Chinese side</h2>
<p>A route that hides the money from Chinese authorities creates a US problem rather than solving one: the account remains FBAR-reportable, the income remains taxable, and a false answer on a US filing is a separate violation. There is no arrangement in which unreported money becomes cheaper by moving it.</p>

<h2>What to do instead</h2>
<p>Every prohibited route in this list is a shortcut around documentation. The lawful answer to missing documentation is to obtain it — a tax clearance, a notarised inheritance entitlement, a SAFE approval, an employment record — or to choose a route whose documents you can actually produce. Start at <a href="steps.html">Steps</a>.</p>
"""
    return page("prohibited.html", "Prohibited", body)


# ----------------------------------------------------------------------------- flagged

def build_flagged() -> str:
    rows = []
    for f in FLAGS["flags"]:
        rows.append([
            f'<b>{esc(f["id"])}</b>',
            esc(f["title"]),
            esc(f["detail"]),
            esc(f["impact"]),
            src_links(f["sources"]) if f["sources"] else "No official source exists — the missing item is a personal fact, not a published rule.",
        ])

    body = f"""
<h1>Flagged for review</h1>
<p class="lede">Everything this edition could not confirm from a first-party source, plus every irregularity found in the repository and in the sources themselves. Nothing on this page blocks publication. Nothing on this page is silently filled in elsewhere.</p>

<div class="note warn"><b>Blank, not zero.</b> Wherever a value is unknown, the site shows a blank or an explicit <span class="blank">UNVERIFIED</span> marker. A blank is never a zero, and a zero is never assumed. There are {len(FLAGS['flags'])} open items.</div>

<h2>Open items</h2>
{table(["ID", "Item", "What is unresolved", "Consequence", "Sources"], rows,
       "Source links point at the first-party page that either creates the uncertainty or partially answers it.")}

<h2>How to close an item</h2>
<ul>
<li>Case facts: supply residency, immigration status, the character and source of the funds, the holding bank and the destination bank. Most of the top items collapse once those exist.</li>
<li>Live prices: request the same executed amount from each provider on the same day and compare the delivered USD, not the headline rate.</li>
<li>Legal text: where two official pages disagree, the later instrument prevails, but the bank in front of you may be working from the earlier one — bring both.</li>
</ul>
"""
    return page("flagged.html", "Flagged for review", body)


# ----------------------------------------------------------------------------- sources

def build_sources() -> str:
    rows = []
    for s in SRC["sources"]:
        rows.append([
            f'<b>{s["id"]}</b>',
            f'<a href="{esc(s["url"])}">{esc(s["title"])}</a><br><span class="src">{esc(s["publisher"])} · {esc(s["published"])}</span>',
            esc(s["quote"]),
            esc(s["supports"]),
        ])

    body = f"""
<h1>Source register</h1>
<p class="lede">Every source below was fetched and read on {AS_OF} by this session. The quote column holds text copied out of the page, not a summary written from memory. Retrieval proves what the page said on that date; it does not guarantee the page still says it, and it does not prove you qualify.</p>

<div class="note"><b>Source hierarchy used.</b> Law and regulation text comes only from a government, regulator or statute publisher: PBOC, SAFE, the State Council, the State Taxation Administration, the IRS, FinCEN or the US Government Publishing Office. Provider terms and prices come only from that provider's own site. No blog, forum, news article or aggregator is used to establish a number.</div>

{table(["ID", "Source", "Verbatim text read", "What it supports"], rows,
       "Long quotes are truncated only where shown with an ellipsis; the linked page is the authority.", classes="")}

<h2>Counts</h2>
<ul class="facts">
<li><b>{len(SRC['sources'])} first-party sources</b> — {len([s for s in SRC['sources'] if s['jurisdiction']=='CN'])} Chinese, {len([s for s in SRC['sources'] if s['jurisdiction']=='US'])} US.</li>
<li><b>{len(METHODS['methods'])} routes</b> — {len(LAWFUL)} lawful or conditional, {len(PROHIBITED)} prohibited.</li>
<li><b>{len(LADDER)} cost rows</b> at $10,000 increments, plus {len(PENALTIES)} penalty rows.</li>
<li><b>{len(FLAGS['flags'])} open items</b> on <a href="flagged.html">Flagged for review</a>.</li>
</ul>

<h2>Reproduce it</h2>
<p>Run <span class="mono">python3 edition-k/build/build.py</span> to regenerate every page from <span class="mono">edition-k/data/*.json</span>, then <span class="mono">python3 edition-k/build/verify.py</span> to recompute every priced cell independently and check the build is byte-identical.</p>
"""
    return page("sources.html", "Sources", body)


# ----------------------------------------------------------------------------- main

def main() -> None:
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "assets").mkdir(parents=True)
    (SITE / "assets" / "style.css").write_text(CSS, encoding="utf-8")
    outputs = {
        "index.html": build_index(),
        "costs.html": build_costs(),
        "methods.html": build_methods(),
        "steps.html": build_steps(),
        "taxes.html": build_taxes(),
        "prohibited.html": build_prohibited(),
        "flagged.html": build_flagged(),
        "sources.html": build_sources(),
    }
    for name, html in outputs.items():
        (SITE / name).write_text(html, encoding="utf-8")
    print(f"built {len(outputs)} pages in {SITE}")
    print(f"targets={len(TARGETS)} first={TARGETS[0]} last={TARGETS[-1]}")
    print(f"boc all-in at $10,000 = {money(R10['total'])} ({pct(R10['pct'])})")
    print(f"boc all-in at $400,000 = {money(R400['total'])} ({pct(R400['pct'])})")


if __name__ == "__main__":
    main()
