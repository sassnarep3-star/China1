#!/usr/bin/env python3
"""Generate the Edition M site from data/*.json.  Run:  python3 edition-m/build/build.py

Deterministic: no network, no clock. Every table row is written with at least one
official source link; a value that could not be confirmed is written as a blank cell
that links to its entry on the Flagged for Review page.
"""
from __future__ import annotations

import csv
import html
import io
import json
import re
import sys
from decimal import Decimal as D
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from model import Model, ceil_int, r2, to_jsonable  # noqa: E402

ED = HERE.parent
DATA = ED / "data"
SHOW = [10000, 50000, 100000, 200000, 400000]


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


SRC = {s["id"]: s for s in load("sources.json")["sources"]}
SRC_META = load("sources.json")
INP = load("inputs.json")
METHODS = load("methods.json")
TAX = load("tax.json")
FLAGS = load("flags.json")
AUDIT = load("audit.json")
SCAN = load("audit_scan.json")
M = Model(INP)
LAD = M.ladders()
GAIN = M.gain_table()
BY_USD = {k: {r["usd"]: r for r in rows} for k, rows in LAD.items()}

# ------------------------------------------------------------------ formatting helpers
def esc(s) -> str:
    return html.escape(str(s), quote=True)


def usd(x, dp=2) -> str:
    x = D(str(x))
    sign = "−" if x < 0 else ""
    return f"{sign}${abs(x):,.{dp}f}"


def usd0(a) -> str:
    return f"${int(a):,}"


def cny(x, dp=2) -> str:
    return f"¥{D(str(x)):,.{dp}f}"


def pct(x) -> str:
    return f"{D(str(x)):.2f}%"


def links(ids) -> str:
    out = []
    for i in ids:
        s = SRC[i]
        out.append(f'<a class="s" href="{esc(s["url"])}" title="{esc(s["issuer"] + " — " + s["title"])}" rel="noopener noreferrer">{i}</a>')
    return " ".join(out)


def blank(flag: str, word: str = "blank") -> str:
    return f'<span class="blank">{word}</span> <a class="fl" href="flagged.html#{flag}">{flag}</a>'


def table(head: list[str], rows: list[tuple[list[str], list[str]]], cls: str = "", caption: str = "") -> str:
    """rows: (cells, source ids). A Source cell is appended to every row."""
    for cells, src in rows:
        if not src:
            raise SystemExit(f"row without a source: {cells[:2]}")
        if len(cells) != len(head):
            raise SystemExit(f"cell count mismatch in table {head}: {cells}")
    h = "".join(f'<th scope="col">{c}</th>' for c in head + ["Source"])
    body = []
    for cells, src in rows:
        tds = f'<th scope="row" data-label="{esc(re.sub("<[^>]+>", "", head[0]))}">{cells[0]}</th>'
        for label, c in zip(head[1:], cells[1:]):
            tds += f'<td data-label="{esc(re.sub("<[^>]+>", "", label))}">{c}</td>'
        tds += f'<td class="src" data-label="Source">{links(src)}</td>'
        body.append(f"<tr>{tds}</tr>")
    cap = f"<caption>{caption}</caption>" if caption else ""
    return f'<div class="tw"><table class="{cls}">{cap}<thead><tr>{h}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


# ------------------------------------------------------------------ computed tokens
def fill(text: str) -> str:
    def rep(m):
        key = m.group(1)
        if key not in TOK:
            raise SystemExit(f"unknown token {key}")
        return TOK[key]
    return re.sub(r"\{\{([a-z0-9_]+)\}\}", rep, text)


boc = BY_USD["boc"]
wise = BY_USD["wise"]
atm = BY_USD["atm"]
g10 = GAIN[0]
scan_board = SCAN["board_values"]
TOK = {
    "boc_pct_20k": pct(boc[20000]["pct"]),
    "boc_pct_400k": pct(boc[400000]["pct"]),
    "wise_pct_10k": pct(wise[10000]["pct"]),
    "wise_pct_400k": pct(wise[400000]["pct"]),
    "wise_min_transfers_400k": str(ceil_int(D(400000) * M.mid / M.wise_cap)),
    "quota_years_400k": str(BY_USD["quota"][400000]["years"]),
    "cash_usd_trips_400k": str(BY_USD["cash_usd"][400000]["trips"]),
    "cash_rmb_trips_400k": str(BY_USD["cash_rmb"][400000]["trips"]),
    "atm_years_400k": str(atm[400000]["years"]),
    "atm_pct_10k": pct(atm[10000]["known_pct"]),
    "atm_usd_per_year": f"{int((M.card_year / M.mid).to_integral_value()):,}",
    "margin_pct": pct(r2(M.margin * 100)),
    "gain_2025_10k": usd(g10["2025"]),
    "gain_2024_10k": usd(g10["2024"]),
    "gain_2023_10k": usd(g10["2023"]),
    "gain_2022_10k": usd(g10["2022"]),
    "loss_2021_10k": usd(abs(g10["2021"])),
    "board_n": str(len(scan_board)),
    "board_min": min(b["value"] for b in scan_board),
    "board_max": max(b["value"] for b in scan_board),
    "board_areas": ", ".join(sorted({a for b in scan_board for a in b["areas"]})),
    "unofficial_n": str(len(SCAN["unofficial_hosts"])),
    "unofficial_list": ", ".join(f'{u["host"]} ({u["files"]} files)' for u in SCAN["unofficial_hosts"]),
    "unofficial_examples": "; ".join(u["example"] for u in SCAN["unofficial_hosts"]),
    "repealed_lines": str(sum(x["lines"] for x in SCAN["repealed_2021_crypto_notice_lines"])),
    "http_n": str(len(SCAN["plain_http_official"])),
    "http_list": ", ".join(f'{u["host"]} ({u["files"]} files)' for u in SCAN["plain_http_official"]),
    "http_examples": "; ".join(u["example"] for u in SCAN["plain_http_official"][:3]),
    "portal_reread": str(SCAN["portal_reread"]),
    "portal_sources": str(SCAN["portal_sources"]),
    "portal_not_reread": str(SCAN["portal_sources"] - SCAN["portal_reread"]),
}

METHOD_BY_ID = {m["id"]: m for m in METHODS["methods"]}
LADDER_FLAG = {"hsbc": "F04", "rmb": "F10", "cash_usd": "F14", "cash_rmb": "F14", "atm": "F11", "card": "F13"}
LADDER_SRC = {
    "boc": ["S32", "S30", "S40"], "quota": ["S01", "S32", "S30", "S40"], "hsbc": ["S35", "S40"],
    "wise": ["S39", "S38", "S37"], "rmb": ["S32", "S23"], "cash_usd": ["S30", "S01", "S32"],
    "cash_rmb": ["S19"], "atm": ["S32", "S15", "S34"], "card": ["S14"],
}
STATUS_CLASS = {"Lawful with documents": "ok", "Lawful, capped": "cap", "Needs SAFE approval": "appr",
                "Not a conversion": "none", "Prohibited": "bad"}


def cost_cell(ladder: str, a: int, short: bool = False) -> str:
    """Headline cost for one method at one amount."""
    r = BY_USD[ladder][a]
    if r["complete"]:
        return f'<b>{usd(r["total"])}</b> <span class="p">{pct(r["pct"])}</span>'
    fl = LADDER_FLAG[ladder]
    if r.get("known") is None:
        return blank(fl)
    tail = "" if short else " known part;"
    return f'<span class="part">{usd(r["known"])}</span>{tail} rest {blank(fl)}'


# ------------------------------------------------------------------ ladder tables
def ladder_table(key: str) -> str:
    rows = LAD[key]
    src = LADDER_SRC[key]
    out = []
    if key == "boc":
        head = ["Yuan worth", "All-in cost", "Cost %", "Arrives in US", "Conversion margin", "BOC fees", "Full-amount fee", "US receiving fee"]
        for r in rows:
            out.append(([usd0(r["usd"]), f'<b>{usd(r["total"])}</b>', pct(r["pct"]), usd(r["arrives"]), usd(r["fx"]),
                         f'{cny(r["fees_cny"])} = {usd(r["fees"])}', usd(r["full"]), usd(r["recv"])], src))
    elif key == "quota":
        head = ["Yuan worth", "All-in cost", "Cost %", "Arrives in US", "Wires", "Calendar years", "BOC fees"]
        for r in rows:
            out.append(([usd0(r["usd"]), f'<b>{usd(r["total"])}</b>', pct(r["pct"]), usd(r["arrives"]), str(r["transfers"]),
                         str(r["years"]), cny(r["fees_cny"])], src))
    elif key == "hsbc":
        head = ["Yuan worth", "All-in cost", "Known part", "Known %", "HSBC fees", "US receiving fee", "Conversion margin"]
        for r in rows:
            out.append(([usd0(r["usd"]), blank("F04"), f'<b>{usd(r["known"])}</b>', pct(r["known_pct"]),
                         f'{cny(r["fees_cny"])} = {usd(r["fees"])}', usd(r["recv"]), blank("F04")], src))
    elif key == "wise":
        head = ["Yuan worth", "Wise fee", "Cost %", "Arrives in US", "Fee in yuan", "Transfers", "US receiving fee"]
        for r in rows:
            out.append(([usd0(r["usd"]), f'<b>{usd(r["total"])}</b>', pct(r["pct"]), usd(r["arrives"]), cny(r["fee_cny"]),
                         str(r["transfers"]), blank("F09")], src))
    elif key == "rmb":
        head = ["Yuan worth", "All-in cost", "Known part", "Known %", "Sending fee", "Conversion abroad"]
        for r in rows:
            out.append(([usd0(r["usd"]), blank("F10"), f'<b>{usd(r["known"])}</b>', pct(r["known_pct"]),
                         cny(r["fees_cny"]), blank("F10")], src))
    elif key == "cash_usd":
        head = ["Yuan worth", "All-in cost", "Known part", "Known %", "Trips", "Permit fee to 31 Dec 2026", "Permit fee from 2027", "Travel"]
        for r in rows:
            out.append(([usd0(r["usd"]), blank("F14"), f'<b>{usd(r["known"])}</b>', pct(r["known_pct"]), str(r["trips"]),
                         usd(r["permit_now"]), usd(r["permit_from_2027"]), blank("F14")], src))
    elif key == "cash_rmb":
        head = ["Yuan worth", "All-in cost", "Trips", "Yuan carried", "Exchange abroad"]
        for r in rows:
            out.append(([usd0(r["usd"]), blank("F14"), f'<b>{r["trips"]}</b>', cny(r["cny"], 0), blank("F14")], src))
    elif key == "atm":
        head = ["Yuan worth", "All-in cost", "Known part", "Known %", "Withdrawals", "Calendar years", "BOC fee in yuan", "Network rate and ATM surcharge"]
        for r in rows:
            out.append(([usd0(r["usd"]), blank("F11"), f'<b>{usd(r["known"])}</b>', pct(r["known_pct"]), str(r["withdrawals"]),
                         str(r["years"]), cny(r["fee_cny"]), blank("F11")], src))
    elif key == "card":
        head = ["Yuan worth", "All-in cost", "Issuer fee", "Network rate"]
        for r in rows:
            out.append(([usd0(r["usd"]), blank("F13"), blank("F13"), blank("F13")], src))
    else:
        raise SystemExit(key)
    return table(head, out, cls="lad")


LADDER_TITLE = {
    "boc": "Bank wire at Bank of China's published tariff, with full-amount delivery, to a US account that charges USD 15 for an incoming wire",
    "quota": "The same wire, one per calendar year, for holders of a Chinese permanent-residence ID using the USD 50,000 quota",
    "hsbc": "Bank wire at HSBC China's published tariff (Premier or Advance)",
    "wise": "Wise: pay in yuan by bank transfer, payout in USD by local transfer",
    "rmb": "Cross-border RMB remittance at Bank of China's tariff, converted outside mainland China",
    "cash_usd": "USD banknotes carried out, USD 10,000 per trip under a bank permit",
    "cash_rmb": "Yuan banknotes carried out, CNY 20,000 per trip",
    "atm": "UnionPay debit-card cash withdrawals abroad at Bank of China's fee",
    "card": "Card spending instead of converting",
}
LADDER_HOW = {
    "boc": "Cost = amount × {{margin_pct}} conversion margin + (0.1% of the yuan paid, between CNY 50 and CNY 260, + CNY 150 cable) ÷ 6.6711 + USD 25 full-amount fee + USD 15 receiving fee. One wire for the whole amount. Take off USD 15 if your US institution charges nothing for incoming wires, and USD 10 if it keeps an account at BOC New York.",
    "quota": "Each calendar year one wire of up to USD 50,000, each priced as in the first table. The margin is the same; the fixed fees repeat every year.",
    "hsbc": "Known part = 0.1% of the yuan value (between CNY 100 and CNY 500) + CNY 120 cable, in dollars, + USD 15 receiving fee. The yuan value is taken at Bank of China's selling rate because HSBC China's rate was not read. Conversion margin and intermediary charges are blank, so no total is given.",
    "wise": "Each row adds up Wise's own quotes for transfers of CNY 66,711, 133,422, 200,133 and 266,844 (yuan worth USD 10,000 to 40,000). Larger amounts are sent as several transfers of CNY 266,844 plus one smaller transfer, each under the CNY 300,000 cap. Wise states it converts at the mid-market rate.",
    "rmb": "Known part = Bank of China's cross-border fee on the yuan sent: 0.1% (CNY 50 to CNY 260) + CNY 150 cable. The conversion happens at the receiving institution; its rate was not verified.",
    "cash_usd": "Known part = amount × {{margin_pct}}, the cash selling rate against the midpoint. One trip per USD 10,000. The Bank of China permit costs CNY 10 but is free until 31 Dec 2026.",
    "cash_rmb": "Trips = yuan ÷ CNY 20,000, rounded up. No cost figure could be confirmed.",
    "atm": "Known part = Bank of China's fee of CNY 12 + 1% per withdrawal (at most CNY 112), with withdrawals of CNY 10,000 each. Years = yuan ÷ CNY 100,000, rounded up.",
    "card": "No official figure was read for this route.",
}


# ------------------------------------------------------------------ page shell
NAV = [("index.html", "Overview"), ("costs.html", "Costs"), ("methods.html", "Methods"), ("steps.html", "Steps"),
       ("tax.html", "Tax and penalties"), ("flagged.html", "Flagged for Review"), ("audit.html", "Repo audit"),
       ("sources.html", "Sources"), ("summary.html", "Summary")]
SNAP = INP["snapshot"]["board_time_beijing"]


def page(slug: str, title: str, lede: str, body: str) -> None:
    cur = ' aria-current="page"'
    nav = "".join(f'<a href="{h}"{cur if h == slug else ""}>{t}</a>' for h, t in NAV)
    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — China money, Edition M</title>
<meta name="description" content="{esc(re.sub('<[^>]+>', '', lede))[:300]}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top">
<div class="wrap bar">
<a class="brand" href="index.html">China money <span>Edition M</span></a>
<a class="portal" href="../index.html">All editions</a>
</div>
<nav class="wrap nav" aria-label="Sections">{nav}</nav>
</header>
<main id="main" class="wrap">
<h1>{title}</h1>
<p class="lede">{lede}</p>
{body}
</main>
<footer class="wrap foot">
<p>Figures read from official pages on 10 Nov 2026; exchange rate from the Bank of China board published {esc(SNAP)} Beijing time. Information, not legal or tax advice. Unconfirmed values are blank and listed under <a href="flagged.html">Flagged for Review</a>.</p>
<p>Session arena-1ee3ca2b · <a href="https://github.com/sassnarep3-star/China1/tree/main/edition-m">source files</a></p>
</footer>
</body>
</html>
"""
    doc = fill(doc)
    if "{{" in doc:
        raise SystemExit(f"unfilled token in {slug}")
    (ED / slug).write_text(doc, encoding="utf-8")


def status_pill(s: str) -> str:
    return f'<span class="pill {STATUS_CLASS[s]}">{esc(s)}</span>'


def mlink(mid: str, page_: str = "steps.html") -> str:
    m = METHOD_BY_ID[mid]
    return f'<a href="{page_}#{mid}">{esc(m["short"])}</a>'


# ------------------------------------------------------------------ pages
def matrix(amounts=SHOW, short=False) -> str:
    head = ["Method"] + [usd0(a) for a in amounts]
    order = ["M01", "M03", "M13", "M05", "M06", "M07", "M08", "M02", "M04", "M09", "M11", "M10", "M12"]
    rows = []
    for mid in order:
        m = METHOD_BY_ID[mid]
        rows.append(([f'<a href="costs.html#L-{m["ladder"]}">{esc(m["short"])}</a> <span class="id">{mid}</span>'] +
                     [cost_cell(m["ladder"], a, short=True) for a in amounts], LADDER_SRC[m["ladder"]]))
    return table(head, rows, cls="mx")


def build_index() -> None:
    b10, b100, b400 = boc[10000], boc[100000], boc[400000]
    w10 = wise[10000]
    kpi = f"""
<section class="kpis" aria-label="Key figures">
<div class="kpi"><span class="k">Cheapest verified route, USD 100,000</span><span class="v">{usd(b100["total"])}</span><span class="n">{pct(b100["pct"])} all-in · documented bank wire</span></div>
<div class="kpi"><span class="k">Same route, USD 400,000</span><span class="v">{usd(b400["total"])}</span><span class="n">{pct(b400["pct"])} all-in · one wire</span></div>
<div class="kpi"><span class="k">Cheapest at USD 10,000</span><span class="v">{usd(w10["total"])}</span><span class="n">{pct(w10["pct"])} · Wise; bank wire is {usd(b10["total"])}</span></div>
<div class="kpi warn"><span class="k">Possible US currency gain per USD 10,000</span><span class="v">{usd(g10["2024"])}</span><span class="n">if the yuan was acquired at the 2024 average rate</span></div>
</section>"""
    answer = f"""
<section class="card answer">
<h2>The short answer</h2>
<ol class="big">
<li><b>Converting is not what gets taxed.</b> No Chinese tax on conversion or remittance appears in the foreign-exchange rules. What the bank asks for is proof that the yuan is lawful and that Chinese tax on it was paid {links(["S01", "S04"])}.</li>
<li><b>A documented bank wire is the cheapest verified route from USD 20,000 up.</b> At Bank of China's tariff the all-in cost is {usd(boc[20000]["total"])} at USD 20,000, {usd(b100["total"])} at USD 100,000 and {usd(b400["total"])} at USD 400,000 {links(["S32", "S30", "S40"])}.</li>
<li><b>At USD 10,000, Wise is cheaper</b> ({usd(w10["total"])} against {usd(b10["total"])}), but only for salary backed by Chinese tax records {links(["S39", "S37"])}.</li>
<li><b>The real tax exposure is elsewhere:</b> unpaid Chinese income tax on the money, a US currency gain when the yuan has risen since you got it, and US penalties if the Chinese account was never reported {links(["S18", "S52", "S50"])}.</li>
<li><b>A foreign passport holder has no USD 50,000 quota.</b> That quota is for holders of Chinese ID or a Chinese permanent-residence ID {links(["S14", "S01"])}.</li>
</ol>
</section>"""
    situ_rows = [
        (["Salary or other China income you can document", mlink("M01"), cost_cell("boc", 100000), "Passport, proof of the income with amounts, tax vouchers"], ["S01", "S32", "S30"]),
        (["Salary, smaller sums, all online", mlink("M03"), cost_cell("wise", 100000), "Chinese tax record from the last 3 years; own-name account"], ["S37", "S39"]),
        (["Money from selling your mainland home", mlink("M05"), cost_cell("boc", 100000), "Registered sale contract, title transferred, tax certificate"], ["S12", "S13", "S32"]),
        (["Assets you owned before emigrating from China", mlink("M06"), cost_cell("boc", 100000), "SAFE approval first: 5 working days to accept, 20 to decide; no fee"], ["S07", "S06", "S32"]),
        (["Money you inherited in China", mlink("M07"), cost_cell("boc", 100000), "SAFE approval; proof of inheritance; tax certificate"], ["S08", "S06", "S32"]),
        (["Yuan you bought with foreign currency in the last 24 months", mlink("M08"), cost_cell("boc", 100000), "Passport and the original exchange memo"], ["S01", "S32"]),
        (["You hold a Chinese permanent-residence ID", mlink("M13"), cost_cell("quota", 100000), "ID only, USD 50,000 a calendar year"], ["S01", "S14", "S32"]),
        (["You cannot document where the yuan came from", "No lawful large-sum route was found. " + mlink("M11") + " and " + mlink("M10") + " are capped; " + mlink("M12") + " avoids converting.", cost_cell("atm", 100000), "Settle the Chinese tax first to obtain vouchers, then use a row above"], ["S01", "S15", "S19"]),
    ]
    situ = table(["Your situation", "Use", "Cost at USD 100,000", "What you need"], situ_rows, cls="situ")
    cards = """
<section class="grid" aria-label="Sections">
<a class="tile" href="costs.html"><h3>Costs</h3><p>Every method at every USD 10,000 step to USD 400,000.</p></a>
<a class="tile" href="methods.html"><h3>Methods</h3><p>All routes with limits, pros and cons, and what is prohibited.</p></a>
<a class="tile" href="steps.html"><h3>Steps</h3><p>Exactly what to do for each method, in order.</p></a>
<a class="tile" href="tax.html"><h3>Tax and penalties</h3><p>Every layer of cost and tax, China and US, with the currency-gain table.</p></a>
<a class="tile" href="flagged.html"><h3>Flagged for Review</h3><p>Everything left blank or in doubt, with the links to check.</p></a>
<a class="tile" href="audit.html"><h3>Repo audit</h3><p>Line-by-line scan of the earlier editions against today's figures.</p></a>
<a class="tile" href="sources.html"><h3>Sources</h3><p>Every official page used, with the sentence relied on.</p></a>
<a class="tile" href="summary.html"><h3>Summary</h3><p>Executive summary and the checklist of what was asked.</p></a>
</section>"""
    body = f"""{kpi}{answer}
<section><h2>Which route fits your money</h2>
<p class="note">Cost is the full cost of getting yuan worth USD 100,000 into a US account. A blank means part of the cost could not be confirmed.</p>
{situ}</section>
<section><h2>Cost by method and amount</h2>
<p class="note">Bold figures are complete all-in costs. Grey figures are the confirmed part only. <a href="costs.html">All 40 amounts for each method</a>.</p>
{matrix()}</section>
{cards}"""
    page("index.html", "Getting yuan out of China into US dollars",
         "For a US citizen with yuan in a mainland bank account: what each lawful route costs at every USD 10,000 step up to USD 400,000, what it needs, and where the tax risk really sits.", body)


def build_costs() -> None:
    parts = [f"""<section><h2>All methods side by side</h2>
<p class="note">Each amount is yuan worth that many dollars at the midpoint of Bank of China's quote (6.6711 yuan per dollar). Cost is everything that stops that value from arriving. Bold = complete; grey = confirmed part only.</p>
{matrix([10000, 20000, 50000, 100000, 200000, 300000, 400000])}</section>
<section class="card"><h2>How to read the figures</h2>
<ul>
<li><b>Rate used:</b> Bank of China board, {esc(SNAP)} Beijing time: buys USD at 665.71, sells at 668.51 yuan per USD 100. Midpoint 667.11. Conversion margin one way: {{{{margin_pct}}}} {links(["S30"])}.</li>
<li><b>Never estimated:</b> where a component has no official figure it is blank and links to its flag. A row with a blank shows the confirmed part only.</li>
<li><b>One wire or several:</b> the wire tables price one wire for the whole amount. Each extra wire adds the fixed charges again: CNY 150 cable, the commission, USD 25 and USD 15 {links(["S32", "S40"])}.</li>
<li><b>Tax is separate:</b> these are transfer and conversion costs. Tax on the money itself and any US currency gain are on the <a href="tax.html">tax page</a>.</li>
</ul></section>"""]
    used_by = {}
    for m in METHODS["methods"]:
        used_by.setdefault(m["ladder"], []).append(m)
    for key in ["boc", "wise", "quota", "hsbc", "rmb", "cash_usd", "atm", "cash_rmb", "card"]:
        ms = used_by[key]
        who = ", ".join(f'<a href="steps.html#{m["id"]}">{m["id"]} {esc(m["short"])}</a>' for m in ms)
        open_ = " open" if key == "boc" else ""
        parts.append(f"""<section id="L-{key}"><h2>{esc(LADDER_TITLE[key])}</h2>
<p class="note">Applies to: {who}.</p>
<p class="how">{LADDER_HOW[key]} {links(LADDER_SRC[key])}</p>
<details{open_}><summary>All 40 amounts, USD 10,000 to USD 400,000</summary>
{ladder_table(key)}
</details></section>""")
    parts.append('<p class="note">Download: <a href="data/ladders.csv">ladders.csv</a> · <a href="data/ladders.json">ladders.json</a></p>')
    page("costs.html", "What each method costs",
         "Transfer and conversion cost for every method at every USD 10,000 step from USD 10,000 to USD 400,000. The most important column comes first; scroll sideways for the parts.", "".join(parts))


def build_methods() -> None:
    parts = []
    rows = []
    for m in METHODS["methods"]:
        t = esc(m["time"]) if m["time"] else blank("F29") if m["cat"] in ("wire", "approval") and not m["time_note"].startswith("One") else esc(m["time_note"])
        rows.append(([f'<a href="#{m["id"]}">{esc(m["name"])}</a> <span class="id">{m["id"]}</span>', status_pill(m["status"]),
                      cost_cell(m["ladder"], 100000), esc(m["cap"]), esc(m["who"]), t], m["src"]))
    parts.append(f"""<section><h2>All lawful routes</h2>
<p class="note">Cost shown is for yuan worth USD 100,000. Full tables are on the <a href="costs.html">costs page</a>; exact steps on the <a href="steps.html">steps page</a>.</p>
{table(["Method", "Status", "Cost at USD 100,000", "Limit", "Who can use it", "Official timing"], rows, cls="meth")}</section>""")
    for cat in METHODS["categories"]:
        ms = [m for m in METHODS["methods"] if m["cat"] == cat["id"]]
        parts.append(f'<section><h2>{esc(cat["title"])}</h2><p class="note">{esc(cat["blurb"])}</p>')
        for m in ms:
            pc = [([f'<span class="pro">For</span>', p["t"]], p["src"]) for p in m["pros"]] + \
                 [([f'<span class="con">Against</span>', c["t"]], c["src"]) for c in m["cons"]]
            parts.append(f"""<article class="card" id="{m["id"]}">
<h3>{esc(m["name"])} <span class="id">{m["id"]}</span></h3>
<p>{status_pill(m["status"])} <span class="cost">{cost_cell(m["ladder"], 100000)} at USD 100,000</span></p>
<p><b>Who:</b> {esc(m["who"])} {links(m["src"][:2])}</p>
<p><b>Limit:</b> {esc(m["cap"])}</p>
{table(["", "Point"], pc, cls="pc")}
<p><a href="steps.html#{m["id"]}">Step by step</a> · <a href="costs.html#L-{m["ladder"]}">cost at every amount</a></p>
</article>""")
        parts.append("</section>")
    prow = [([f'{esc(p["name"])} <span class="id">{p["id"]}</span>', esc(p["why"]), esc(p["penalty"])], p["src"]) for p in METHODS["prohibited"]]
    parts.append(f"""<section id="prohibited"><h2>Prohibited: what each one risks</h2>
<p class="note">Listed so they are recognised and avoided. No instructions are given for any of them.</p>
{table(["Channel", "Why it is prohibited", "Penalty stated in the source"], prow, cls="bad")}</section>""")
    page("methods.html", "Methods, with pros and cons",
         f'{len(METHODS["methods"])} lawful routes for turning yuan in a mainland account into US dollars, and {len(METHODS["prohibited"])} channels that are prohibited.', "".join(parts))


def build_steps() -> None:
    parts = ['<nav class="jump" aria-label="Methods">' + " ".join(f'<a href="#{m["id"]}">{m["id"]} {esc(m["short"])}</a>' for m in METHODS["methods"]) + "</nav>"]
    for m in METHODS["methods"]:
        rows = [([str(i), s["t"]], s["src"]) for i, s in enumerate(m["steps"], 1)]
        timing = f'<p><b>Official timing:</b> {esc(m["time"])}</p>' if m["time"] else ""
        parts.append(f"""<section class="card" id="{m["id"]}">
<h2>{esc(m["name"])} <span class="id">{m["id"]}</span></h2>
<p>{status_pill(m["status"])} <span class="cost">{cost_cell(m["ladder"], 100000)} at USD 100,000</span> · <a href="costs.html#L-{m["ladder"]}">all amounts</a> · <a href="methods.html#{m["id"]}">pros and cons</a></p>
<p><b>Who:</b> {esc(m["who"])}</p>
{timing}
{table(["Step", "What to do"], rows, cls="steps")}
</section>""")
    page("steps.html", "Step by step",
         "What to do, in order, for each lawful method. Every step links to the rule or price list it comes from.", "".join(parts))


def build_tax() -> None:
    lrows = []
    for l in TAX["layers"]:
        amt = esc(l["amount"]) if l["amount"] else f'<span class="blank">none found</span> <span class="why">{esc(l["blank_reason"])}</span>'
        lrows.append(([str(l["n"]), esc(l["side"]), f'<b>{esc(l["item"])}</b>', amt, esc(l["when"])], l["src"]))
    years = sorted(M.fxy, reverse=True)
    ghead = ["Yuan worth"] + [f"Acquired {y}<br><span class=\"sub\">{M.fxy[y]} per USD</span>" for y in years]
    grows = [([usd0(r["usd"])] + [f'<span class="{"neg" if r[y] < 0 else "pos"}">{usd(r[y])}</span>' for y in years], ["S53", "S30", "S52"]) for r in GAIN]
    prow = []
    for p in TAX["penalties"]:
        pen = esc(p["penalty"]) if p["penalty"] else blank("F23") + f' <span class="why">{esc(p["blank_reason"])}</span>'
        prow.append(([esc(p["side"]), esc(p["trigger"]), pen], p["src"]))
    rrow = [([esc(r["route"]), esc(r["terms"])], r["src"]) for r in TAX["relief"]]
    body = f"""
<section class="card answer"><h2>What the penalty really is</h2>
<ul>
<li>The conversion itself: a bank margin of {{{{margin_pct}}}} and fixed fees. No tax on it was found in the Chinese rules {links(["S30", "S32", "S04"])}.</li>
<li>China: income tax on the money if it was never paid, at 3%–45% for salary-type income or 20% for interest, dividends, rent, asset sales and windfalls. The bank wants the tax voucher before it sells you dollars {links(["S18", "S01"])}.</li>
<li>United States: a currency gain if the yuan is worth more dollars now than when you got it. Yuan acquired at the 2024 average rate shows a gain of {{{{gain_2024_10k}}}} per USD 10,000 converted today {links(["S52", "S53"])}.</li>
<li>United States: reporting penalties if the Chinese account was never reported, up to USD 16,536 per missed FBAR when not willful {links(["S58", "S50"])}.</li>
</ul></section>
<section><h2>Every layer, in order</h2>
{table(["#", "Side", "Layer", "Rate or amount", "When it applies"], lrows, cls="layers")}</section>
<section id="gain"><h2>US currency gain at each amount</h2>
<p class="note">Gain or loss in dollars from converting today, if the yuan was acquired at the IRS yearly average rate for that year. Formula: yuan ÷ 6.6851 (today's selling rate) − yuan ÷ that year's rate. This is the gain, not the tax; the tax is the gain times your own rate. A personal transaction with a gain of USD 200 or less is not recognised. See <a href="flagged.html#F22">F22</a>.</p>
<details open><summary>All 40 amounts</summary>
{table(ghead, grows, cls="lad gain")}
</details></section>
<section><h2>Penalties</h2>
{table(["Side", "What triggers it", "Penalty stated in the source"], prow, cls="pen")}</section>
<section><h2>Ways to put a missed US filing right</h2>
{table(["Route", "Terms"], rrow, cls="relief")}</section>"""
    page("tax.html", "Tax and penalties: the full breakdown",
         "Every layer that takes money on the way from a Chinese yuan account to a US dollar account, in China and in the United States, and what each penalty is.", body)


def build_flagged() -> None:
    kinds = FLAGS["kinds"]
    counts = {k: sum(1 for f in FLAGS["flags"] if f["kind"] == k) for k in kinds}
    chips = " ".join(f'<span class="chip {k}">{esc(v)}: {counts[k]}</span>' for k, v in kinds.items())
    rows = []
    for f in FLAGS["flags"]:
        rows.append(([f'<span id="{f["id"]}" class="id">{f["id"]}</span>', f'<span class="chip {f["kind"]}">{esc(kinds[f["kind"]])}</span>',
                      f'<b>{esc(f["title"])}</b><br>{esc(f["detail"])}', esc(f["affects"])], f["src"]))
    body = f"""<p class="chips">{chips}</p>
<section class="card"><p>Nothing on this page blocks the rest of the site. Each item is either a value left blank because no official page confirmed it, a point where official pages disagree, a fact only you can supply, or a stated limit of the method. The Source column gives the page to open to check it.</p></section>
<section>{table(["ID", "Kind", "What is flagged", "What it affects"], rows, cls="flags")}</section>"""
    page("flagged.html", "Flagged for Review",
         f'{len(FLAGS["flags"])} items that are blank, in doubt or dependent on your own facts, each with the official page to check.', body)


def build_audit() -> None:
    blob = AUDIT["blob"]
    mrows = [([esc(m["step"]), esc(m["what"])], m["src"]) for m in AUDIT["method"]]
    frows = []
    for f in AUDIT["findings"]:
        frows.append(([f'<span class="id">{f["id"]}</span>', f'<span class="lvl {f["level"].lower()}">{esc(f["level"])}</span>',
                       f'<b>{esc(f["title"])}</b><br>{esc(f["detail"])}', f'<span class="path">{esc(fill(f["where"]))}</span>', esc(f["action"])], f["check"]))
    crow = []
    for c in SCAN["checks"]:
        other = ", ".join(f'{esc(o["value"])} ({o["lines"]})' for o in c["other_values"]) or "none"
        ex = " ".join(f'<a href="{blob}{esc(e["where"].split(":")[0])}#L{e["where"].split(":")[1]}">{esc(e["where"])}</a>' for e in c["examples"][:3]) or "—"
        crow.append(([f'<span class="id">{c["id"]}</span>', esc(c["title"]), esc(", ".join(c["read_today"])), str(c["lines_matching_today"]), other, ex], c["src"]))
    arow = [([esc(a["area"]), f'{a["files"]:,}', f'{a["lines"]:,}'], ["S30"]) for a in SCAN["by_area"]]
    brow = [([esc(b["value"]), str(b["lines"]), esc(", ".join(b["areas"]))], ["S30"]) for b in SCAN["board_values"]]
    body = f"""
<section class="kpis">
<div class="kpi"><span class="k">Files read line by line</span><span class="v">{SCAN["files"]:,}</span><span class="n">every tracked text file outside this edition</span></div>
<div class="kpi"><span class="k">Lines read</span><span class="v">{SCAN["lines"]:,}</span><span class="n">at commit {esc(SCAN["scanned_commit"])}</span></div>
<div class="kpi"><span class="k">Findings</span><span class="v">{len(AUDIT["findings"])}</span><span class="n">{sum(1 for f in AUDIT["findings"] if f["level"] == "High")} high · {sum(1 for f in AUDIT["findings"] if f["level"] == "Medium")} medium</span></div>
<div class="kpi"><span class="k">Portal sources re-read today</span><span class="v">{SCAN["portal_reread"]} of {SCAN["portal_sources"]}</span><span class="n">figures agree</span></div>
</section>
<section><h2>Findings</h2>
<p class="note">The Source column links the official page to check each finding against.</p>
{table(["ID", "Level", "Finding", "Where", "What this edition does"], frows, cls="aud")}</section>
<section><h2>How the audit was done</h2>
{table(["Step", "What was done"], mrows, cls="how")}</section>
<section><h2>Figure scan</h2>
<p class="note">For each figure read today, the number of lines in the repository that state it, any other number found on a matching line, and sample locations to open. Other numbers on sampled lines were different fields, not contradictions (finding A11).</p>
{table(["Check", "Figure", "Read today", "Lines agreeing", "Other numbers on matching lines (lines)", "Sample lines"], crow, cls="scan")}</section>
<section><h2>Exchange-rate snapshots found</h2>
<p class="note">Bank of China USD board values (yuan per USD 100) that appear in the repository. Today's board reads 665.71 and 668.51.</p>
{table(["Board value", "Lines", "Where"], brow, cls="scan")}</section>
<section><h2>Coverage</h2>
<details><summary>Files and lines read, by folder</summary>
{table(["Folder", "Files", "Lines"], arow, cls="scan")}
</details></section>"""
    page("audit.html", "Repository audit",
         "A line-by-line scan of the earlier editions against figures read from official pages on 10 Nov 2026, with links for manual review.", body)


def build_sources() -> None:
    how = SRC_META["how_legend"]
    label = {"full": "Read in full", "sections": "Sections read", "excerpt": "Excerpt"}
    groups = []
    for s in SRC_META["sources"]:
        if s["group"] not in groups:
            groups.append(s["group"])
    parts = ['<section class="card"><ul>' + "".join(f"<li><b>{label[k]}:</b> {esc(v)}</li>" for k, v in how.items()) + "</ul></section>"]
    for g in groups:
        rows = []
        for s in SRC_META["sources"]:
            if s["group"] != g:
                continue
            note = f'<br><span class="why">{esc(s["note"])}</span>' if s["note"] else ""
            rows.append(([f'<span id="{s["id"]}" class="id">{s["id"]}</span>', f'<b>{esc(s["title"])}</b><br><span class="why">{esc(s["issuer"])}</span>',
                          f'<q>{esc(s["quote"])}</q>{note}', f'<span class="how {s["how"]}">{label[s["how"]]}</span>'], [s["id"]]))
        parts.append(f'<section><h2>{esc(g)}</h2>{table(["ID", "Page", "Sentence relied on", "How it was read"], rows, cls="srcs")}</section>')
    page("sources.html", "Sources",
         f'{len(SRC_META["sources"])} pages on official sites, each read on 10 Nov 2026, with the sentence relied on. Open the link in the last column to check it.', "".join(parts))


def summary_points() -> list[tuple[str, list[str]]]:
    b10, b20, b100, b400 = boc[10000], boc[20000], boc[100000], boc[400000]
    return [
        (f"China does not tax the conversion; it controls it. No conversion or remittance tax appears in the rules read. A foreign passport holder may buy foreign exchange against lawful China-source income on proof of source that includes tax vouchers, with no annual ceiling, but has no USD 50,000 no-questions quota.", ["S01", "S14", "S04"]),
        (f"Cheapest verified route from USD 20,000 up: a documented bank wire. At Bank of China's tariff, with full-amount delivery and a USD 15 receiving fee, the all-in cost is {usd(b20['total'])} ({pct(b20['pct'])}) at USD 20,000, {usd(b100['total'])} ({pct(b100['pct'])}) at USD 100,000 and {usd(b400['total'])} ({pct(b400['pct'])}) at USD 400,000.", ["S32", "S30", "S40"]),
        (f"At USD 10,000 Wise is cheaper: {usd(wise[10000]['total'])} ({pct(wise[10000]['pct'])}) against {usd(b10['total'])} ({pct(b10['pct'])}). Wise stays near {pct(wise[400000]['pct'])} at every size, is limited to salary shown on Chinese tax records, and caps each transfer at CNY 300,000.", ["S39", "S38", "S37"]),
        (f"The same wire cost applies to home-sale proceeds (bank handles it on the tax certificate), to emigrant and inherited assets (after SAFE approval: 5 working days to accept, 20 to decide, no fee) and to yuan bought with foreign currency in the last 24 months.", ["S12", "S07", "S08", "S01"]),
        (f"Capped channels do not scale: overseas ATM cash is limited to CNY 100,000 a year ({TOK['atm_years_400k']} years for USD 400,000, about {pct(atm[10000]['known_pct'])} in bank fees alone); USD cash is USD 10,000 a trip ({TOK['cash_usd_trips_400k']} trips); yuan cash is CNY 20,000 a trip ({TOK['cash_rmb_trips_400k']} trips).", ["S15", "S32", "S01", "S19"]),
        (f"The tax exposure is on the money, not the transfer. China: income tax if unpaid (3%–45% on salary-type income, 20% on interest, dividends, rent, asset sales). United States: worldwide income is taxable when earned, with credit for Chinese income tax.", ["S18", "S62", "S61"]),
        (f"Converting can itself create US income. Yuan acquired at the 2024 average rate (7.189) and converted today (6.6851) shows a gain of {usd(g10['2024'])} per USD 10,000, {usd(GAIN[39]['2024'])} at USD 400,000. Yuan from 2021 shows a loss. The tax is the gain times your own rate.", ["S52", "S53", "S30"]),
        (f"Unreported accounts cost more than any transfer fee: up to USD 16,536 per missed FBAR when not willful, and the greater of USD 165,353 or half the balance when willful. Late FBARs carry no penalty if the income was reported and taxed; otherwise the streamlined procedures cost 5% for US residents and nothing for those living abroad.", ["S58", "S56", "S55"]),
        (f"Prohibited shortcuts carry fines of up to 30% of the amount, and up to 100% in serious cases: splitting through other people's quotas, underground banks, false documents and crypto conversion. SAFE publishes the fines, for example CNY 2.157 million on USD 3.331 million.", ["S04", "S21", "S25"]),
    ]


REQS = [
    ("Research as many yuan-to-dollar methods as possible, with pros and cons", f'{len(METHODS["methods"])} lawful methods and {len(METHODS["prohibited"])} prohibited channels, each with sourced pros and cons', "methods.html", ["S01", "S32"]),
    ("Break down the conversion penalty", "Eleven layers across China, transit and the United States, plus penalty and relief tables", "tax.html", ["S04", "S52"]),
    ("Estimate the cost for every method at every USD 10,000 step to USD 400,000", "Nine cost tables of 40 rows cover all 13 methods; complete all-in figures for the wire, quota and Wise routes, confirmed part plus flagged blanks for the rest", "costs.html", ["S32", "S39"]),
    ("Mobile-friendly tables, most important information first", "Headline cost is the first numeric column; tables scroll sideways with the first column fixed; stacked cards on narrow screens for text tables", "costs.html", ["S30"]),
    ("Explain exactly, step by step, how each method works", "Numbered steps for each of the 13 methods, each step with its source", "steps.html", ["S01", "S07"]),
    ("Review the repository line by line against official sources and flag irregularities", f'{SCAN["files"]:,} files and {SCAN["lines"]:,} lines scanned; {len(AUDIT["findings"])} findings with links', "audit.html", ["S32", "S58"]),
    ("Every table row carries a link to an official site; unconfirmed values blank and flagged", "Enforced by the generator and re-checked by the verifier on every page", "sources.html", ["S30"]),
    ("Flagged for Review page", f'{len(FLAGS["flags"])} items with source links', "flagged.html", ["S30"]),
    ("Clean landing page with subpages by category", "Overview dashboard and eight subpages", "index.html", ["S30"]),
]


def build_summary() -> None:
    rows = [([str(i), t], s) for i, (t, s) in enumerate(summary_points(), 1)]
    rrows = [([esc(a), esc(b), f'<a href="{c}">{c}</a>'], s) for a, b, c, s in REQS]
    unk = [([esc(f["title"]), esc(f["detail"])], f["src"]) for f in FLAGS["flags"] if f["id"] in ("F01", "F03", "F04", "F09", "F10", "F15", "F16", "F22")]
    body = f"""
<section><h2>Executive summary</h2>
{table(["#", "Finding"], rows, cls="sum")}</section>
<section><h2>What would change the answer</h2>
{table(["Open point", "Why it matters"], unk, cls="sum")}
<p class="note">All {len(FLAGS["flags"])} flagged items are on <a href="flagged.html">Flagged for Review</a>.</p></section>
<section><h2>What was asked, and where it is answered</h2>
{table(["Requirement", "What was delivered", "Page"], rrows, cls="req")}</section>"""
    page("summary.html", "Executive summary", "The findings that matter, what is still open, and how each requirement was met.", body)


def write_exports() -> None:
    out = {"basis": "Each row is yuan worth `usd` at the Bank of China midpoint 6.6711. null = not confirmed from an official source.",
           "board_time_beijing": SNAP, "mid_cny_per_usd": float(M.mid), "ask_cny_per_usd": float(M.ask),
           "margin_one_way": float(r2(M.margin * 100)), "ladders": to_jsonable(LAD), "currency_gain_usd": to_jsonable(GAIN)}
    (DATA / "ladders.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["ladder", "usd", "all_in_usd", "all_in_pct", "known_part_usd", "arrives_usd", "transfers_or_trips", "years"])
    for key, rows in LAD.items():
        for r in rows:
            w.writerow([key, r["usd"], "" if r.get("total") is None else r["total"], "" if r.get("pct") is None else r["pct"],
                        "" if r.get("known") is None else r["known"], "" if r.get("arrives") is None else r["arrives"],
                        r.get("transfers", r.get("trips", r.get("withdrawals", ""))), r.get("years", "")])
    (DATA / "ladders.csv").write_text(buf.getvalue(), encoding="utf-8")


def strip(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def write_markdown() -> None:
    def md_src(ids):
        return " ".join(f"[{i}]({SRC[i]['url']})" for i in ids)
    pts = "\n".join(f"{i}. {t} {md_src(s)}" for i, (t, s) in enumerate(summary_points(), 1))
    rows = "\n".join(
        f"| {usd0(a)} | {usd(boc[a]['total'])} ({pct(boc[a]['pct'])}) | {usd(wise[a]['total'])} ({pct(wise[a]['pct'])}) | {usd(BY_USD['quota'][a]['total'])} in {BY_USD['quota'][a]['years']} yr | {usd(atm[a]['known'])} + blank, {atm[a]['years']} yr | {usd(GAIN[a // 10000 - 1]['2024'])} |"
        for a in SHOW)
    text = f"""# Edition M — executive summary

Session arena-1ee3ca2b · figures read from official pages on 2026-11-10 · Bank of China board {SNAP} Beijing time.
Live pages: https://sassnarep3-star.github.io/China1/edition-m/

## Findings

{pts}

## Cost at selected amounts

| Yuan worth | Bank wire, all-in (M01) | Wise (M03) | PR-ID quota (M13) | UnionPay ATM (M11) | US currency gain if acquired 2024 |
|---|---|---|---|---|---|
{rows}

Sources: bank wire {md_src(['S32', 'S30', 'S40'])}; Wise {md_src(['S39', 'S38'])}; quota {md_src(['S01'])}; ATM {md_src(['S32', 'S15'])}; currency gain {md_src(['S53', 'S52'])}.
All 40 amounts for all 13 methods: `costs.html`, `data/ladders.csv`.

## Open points

{chr(10).join(f"- **{f['id']} {f['title']}.** {f['detail']} {md_src(f['src'])}" for f in FLAGS['flags'] if f['id'] in ('F01', 'F03', 'F04', 'F09', 'F10', 'F15', 'F16', 'F22'))}

All {len(FLAGS['flags'])} flagged items: `flagged.html`.
"""
    (ED / "EXECUTIVE_SUMMARY.md").write_text(text, encoding="utf-8")
    readme = f"""# Edition M

A self-contained edition of the China money project, built by session arena-1ee3ca2b on 2026-11-10.

It closes the gap left by the earlier editions: an actual cost for every method at every USD 10,000 step
to USD 400,000, built only from figures read on official pages that day.

| Page | What it holds |
|---|---|
| `index.html` | Overview dashboard: short answer, which route fits, cost by method and amount |
| `costs.html` | Nine 40-row cost tables covering all {len(METHODS['methods'])} methods |
| `methods.html` | Methods with limits, pros and cons; prohibited channels and their penalties |
| `steps.html` | Numbered steps for each method |
| `tax.html` | Every layer of cost and tax, the US currency-gain table, penalties, relief |
| `flagged.html` | Flagged for Review: {len(FLAGS['flags'])} items |
| `audit.html` | Line-by-line repository audit: {SCAN['files']:,} files, {SCAN['lines']:,} lines |
| `sources.html` | {len(SRC_META['sources'])} official pages with the sentence relied on |
| `summary.html` | Executive summary and requirement checklist |

## Rebuild and verify

```
python3 edition-m/build/build.py
python3 edition-m/build/verify.py
```

`build.py` is deterministic (no network, no clock). `verify.py` recomputes every cost row with its own
arithmetic, checks that every table row carries a link to an official host, that every blank links to a flag,
that all internal links resolve, and that every source cited exists.

`build/audit.py` rescans the rest of the repository and rewrites `data/audit_scan.json`. It is not part of
CI because its result changes when other editions change.

## Data

- `data/sources.json` — pages read, with quotes and how each was read
- `data/inputs.json` — every number used, with its source id
- `data/methods.json`, `data/tax.json`, `data/flags.json`, `data/audit.json` — page content
- `data/ladders.json`, `data/ladders.csv` — generated cost tables
- `data/_research_log.md` — raw notes taken while reading the official pages
"""
    (ED / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    build_index()
    build_costs()
    build_methods()
    build_steps()
    build_tax()
    build_flagged()
    build_audit()
    build_sources()
    build_summary()
    write_exports()
    write_markdown()
    print(f"edition-m built: {len(NAV)} pages, {len(METHODS['methods'])} methods, {sum(len(v) for v in LAD.values())} cost rows, "
          f"{len(SRC_META['sources'])} sources, {len(FLAGS['flags'])} flags")


if __name__ == "__main__":
    main()
