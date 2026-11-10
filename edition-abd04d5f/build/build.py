#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Edition abd04d5f generator. Deterministic: no clock, no network. Run: python3 edition-abd04d5f/build/build.py"""
import csv, html, json, os, sys
from decimal import Decimal as D, ROUND_HALF_UP, ROUND_CEILING
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from content import S, MODEL, F, M, STEPS, CN_TAX, US_TAX, US_PEN, AUDIT, CHECKED
REPO = "https://github.com/sassnarep3-star/China1"
e = html.escape
m = {k: D(v) for k, v in MODEL.items() if k != "board_time"}
ASK, BID = m["ask"], m["bid"]; MID = (ASK + BID) / 2
AMTS = [D(10000) * i for i in range(1, 41)]
def q(x, p="0.01"): return x.quantize(D(p), ROUND_HALF_UP)
def ceil(x): return int(x.to_integral_value(ROUND_CEILING))
def clamp(x, lo, hi): return max(lo, min(hi, x))
def usd(x): return "$" + format(q(x), ",.2f")
def usd0(x): return "$" + format(int(q(x, "1")), ",d")
def cny(x): return "¥" + format(q(x), ",.2f")
def pct(x): return format(q(x * 100, "0.001"), "f") + "%"

def model(U):
    r = {"usd": U}
    principal = U * ASK
    r["cny_principal"] = principal
    r["spread"] = U * (ASK - MID) / MID
    r["boc_fee_cny"] = clamp(m["boc_rate"] * principal, m["boc_min"], m["boc_max"]) + m["boc_cable"]
    r["boc_fee_usd"] = r["boc_fee_cny"] / MID
    r["boc_std"] = r["spread"] + r["boc_fee_usd"] + m["chase_in"]
    r["boc_full"] = r["boc_std"] + m["boc_full_usd"]
    r["boc_cny_needed"] = principal + r["boc_fee_cny"]
    r["hsbc_fee_cny"] = clamp(m["hsbc_rate"] * principal, m["hsbc_min"], m["hsbc_max"]) + m["hsbc_cable"]
    r["hsbc_fee_usd"] = r["hsbc_fee_cny"] / MID
    r["ccb_fee_cny"] = clamp(m["ccb_rate"] * principal, m["ccb_min"], m["ccb_max"]) + m["ccb_cable"]
    r["ccb_fee_usd"] = r["ccb_fee_cny"] / MID
    at_mid = U * MID
    r["wise_n"] = ceil(at_mid / m["wise_cap_cny"])
    full, rem = divmod(at_mid, m["atm_day_cny"])
    fee = full * min(m["atm_max"], m["atm_fix"] + m["atm_pct"] * m["atm_day_cny"])
    if rem > 0: fee += min(m["atm_max"], m["atm_fix"] + m["atm_pct"] * rem)
    r["atm_n"] = int(full) + (1 if rem > 0 else 0)
    r["atm_fee_cny"] = fee; r["atm_fee_usd"] = fee / MID
    r["atm_years"] = ceil(at_mid / m["atm_year_cny"])
    r["cash_trips5"] = ceil(U / m["cash_nopermit"]); r["cash_trips10"] = ceil(U / m["cash_permit"])
    r["tax20"] = U * m["tax_flat"]; r["tax_lo"] = U * m["tax_lo"]; r["tax_hi"] = U * m["tax_hi"]
    r["late_year"] = r["tax20"] * m["late_day"] * 365
    r["pen_lo"] = r["tax20"] * m["pen_lo"]; r["pen_hi"] = r["tax20"] * m["pen_hi"]
    r["fine30"] = U * m["fx_fine"]; r["fine100"] = U; r["cash20"] = U * m["cash_fine"]
    r["fbar_w"] = max(m["fbar_w_base"], U * m["fbar_w_pct"])
    return r
ROWS = [model(U) for U in AMTS]
BY = {int(r["usd"]): r for r in ROWS}

# ------------------------------------------------------------------ html helpers
def src(ids):
    return " ".join('<a class="s" href="%s" title="%s" rel="noopener">%s</a>' % (e(S[i]["u"]), e(S[i]["t"]), i) for i in ids)
def flag(i): return '<a class="f" href="flagged.html#%s" title="%s">%s</a>' % (i, e(F[i][0]), i)
def blank(i): return '<span class="unv">unverified</span> ' + flag(i)
def gh(path): return '<a class="s" href="%s/blob/main/%s" rel="noopener">%s</a>' % (REPO, path, e(path))
def table(heads, rows, cls="stack", ids=None, nosrc=None):
    o = ['<div class="tw"><table class="data %s"><thead><tr>' % cls]
    o += ["<th>%s</th>" % h for h in heads]; o.append("</tr></thead><tbody>")
    for n, r in enumerate(rows):
        a = ""
        if ids: a += ' id="%s"' % ids[n]
        if nosrc and nosrc[n]: a += ' class="nosrc"'
        o.append("<tr%s>" % a)
        for h, c in zip(heads, r):
            k = ' class="blank"' if 'class="unv"' in c else ""
            o.append('<td data-label="%s"%s>%s</td>' % (e(h, quote=True), k, c))
        o.append("</tr>")
    o.append("</tbody></table></div>")
    return "".join(o)
NAV = [("index.html", "Summary"), ("methods.html", "Methods"), ("costs.html", "Costs"), ("steps.html", "Steps"),
       ("taxes.html", "Taxes &amp; penalties"), ("flagged.html", "Flagged for Review"), ("sources.html", "Sources"), ("review.html", "Repo review")]
def page(fn, title, lead, body):
    nav = "".join('<a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if h == fn else "", t) for h, t in NAV)
    doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>%s · China Money</title><meta name="description" content="%s"><link rel="stylesheet" href="style.css"></head><body>'
           '<header><a class="brand" href="index.html">China Money <span>CNY → USD</span></a><nav aria-label="Sections">%s</nav></header>'
           '<main><h1>%s</h1><p class="lead">%s</p>%s</main>'
           '<footer><p>Sources read %s (UTC). Rates and fees change; confirm with your bank before acting. Research, not legal or tax advice. '
           'Blank means not confirmed from an official source — never zero.</p><p><a href="flagged.html">Flagged for Review</a> · '
           '<a href="sources.html">Sources</a> · <a href="data/costs.csv">Cost data (CSV)</a> · <a href="../index.html">Earlier editions</a> · '
           '<a href="%s" rel="noopener">Repository</a></p></footer></body></html>') % (e(title), e(lead, quote=True), nav, e(title), lead, body, CHECKED, REPO)
    open(os.path.join(OUT, fn), "w", encoding="utf-8").write(doc)

A = lambda r: "<b>%s</b>" % usd0(r["usd"])
RATE_SRC = ["S09"]

# ------------------------------------------------------------------ index
def build_index():
    lo, hi = BY[10000], BY[400000]
    pick = [10000, 50000, 100000, 200000, 300000, 400000]
    quick = table(["Amount sent", "Estimated total cost", "As % of amount", "Of which exchange margin", "Of which bank fees", "Source"],
        [[A(BY[u]), "<b>%s</b>" % usd(BY[u]["boc_std"]), pct(BY[u]["boc_std"] / BY[u]["usd"]), usd(BY[u]["spread"]),
          usd(BY[u]["boc_fee_usd"] + m["chase_in"]), src(["S09", "S10", "S31"])] for u in pick], cls="num")
    cases = table(["If the money is…", "Use this route", "What the bank needs", "Chinese tax to expect", "Source"], [
        ["Salary or fees you earned in China, tax already withheld", '<a href="steps.html#M01">Income route</a>', "Passport, contract or income proof, tax record", "None further", src(["S03", "S04"])],
        ["Income earned in China on which tax was never paid", '<a href="steps.html#M01">Income route, after paying the tax</a>', "As above, once the tax certificate exists", "The unpaid income tax (3%–45% wages, 20% flat categories) plus 0.05% a day", src(["S14", "S16"])],
        ["RMB you exchanged from dollars you brought in, less than 24 months ago", '<a href="steps.html#M02">Convert-back route</a>', "Passport and the original exchange memo", "None", src(["S03"])],
        ["Proceeds of selling your home", '<a href="steps.html#M04">Home-sale route</a>', "Sale contract, registration proof, tax proof", "20% of the gain on the sale", src(["S18", "S14"])],
        ["An inheritance", '<a href="steps.html#M05">Inheritance transfer</a>', "SAFE approval; proof of inheritance, property and tax documents", "Tax certificates of the estate's assets", src(["S05", "S06"])],
        ["Your pre-emigration assets (you were once a mainland resident)", '<a href="steps.html#M06">Emigrant transfer</a>', "SAFE approval; cancelled household registration, consular proof", "Tax certificates for the assets", src(["S05", "S06"])],
        ["Profit or liquidation proceeds of your China company", '<a href="steps.html#M07">Company route</a>', "Profit resolution or liquidation papers, tax filing", "Company and withholding taxes first", src(["S01", "S06"])],
        ["Bank interest on any of the above", "Follows the principal", "Bank interest record (acceptance not verified — %s)" % flag("F21"), "Exempt", src(["S15"])],
        ["Money with no papers at all", "No lawful conversion route was found", "Nothing replaces proof of where the money came from", "Not applicable", src(["S01", "S02"])],
    ])
    body = (
      '<section class="bluf"><h2>The short answer</h2><ol>'
      '<li><b>Converting and wiring the money is not what gets taxed.</b> China has no tax item for exchanging currency. The US taxes only a currency gain above $200 if the yuan rose in dollar terms while you held it. What the Chinese bank asks for is <b>proof that tax on the underlying income was already dealt with</b> — that is the "tax" people run into. %s</li>'
      '<li><b>If the money is documented and already taxed, the cheapest lawful route costs about %s on $10,000 and %s on $400,000</b> (%s falling to %s): buy dollars at your Chinese bank and wire them to your own US account. %s</li>'
      '<li><b>If Chinese tax was never paid on the income, that tax is the real cost</b>: 20%% for dividends, property gains and similar; 3%%–45%% for wages; plus 0.05%% per day late, and fines of 50%% to 5 times the tax where it counts as evasion. %s</li>'
      '<li><b>Shortcuts cost more than the tax.</b> Underground banks, borrowed quotas, false papers and crypto carry fines up to 30%% of the amount (up to 100%% if serious) and criminal exposure. %s</li>'
      '<li><b>On the US side, report rather than pay</b>: FBAR above $10,000 in foreign accounts, Form 8938 above its thresholds, Form 3520 if the money is a gift or inheritance above $100,000. %s</li></ol></section>'
      ) % (src(["S14", "S03", "S04", "S27"]), usd(lo["boc_std"]), usd(hi["boc_std"]), pct(lo["boc_std"] / lo["usd"]), pct(hi["boc_std"] / hi["usd"]),
           src(["S09", "S10", "S31"]), src(["S14", "S16"]), src(["S01", "S21", "S20"]), src(["S23", "S24"]))
    body += ('<section class="cards">'
      '<div class="card"><small>Tax on the conversion itself</small><b>None in China</b><span>US: only a currency gain over $200. Read %s</span></div>'
      '<div class="card"><small>Exchange margin, one way</small><b>%s</b><span>Bank of China board, %s</span></div>'
      '<div class="card"><small>Bank fee per wire</small><b>%s – %s</b><span>0.1%%, min ¥50, max ¥260, + ¥150 cable</span></div>'
      '<div class="card warn"><small>Fine on unlawful routes</small><b>up to 30%% – 100%%</b><span>of the amount, plus criminal exposure</span></div>'
      '</section>') % (CHECKED, pct((ASK - MID) / MID), e(MODEL["board_time"]), cny(lo["boc_fee_cny"]), cny(hi["boc_fee_cny"]))
    body += '<h2>What a lawful wire costs</h2><p>Bank of China, standard wire to a Chase account, one wire per amount. Charges that intermediary banks may deduct are not published and are not included (%s). <a href="costs.html">Every $10,000 step and every method →</a></p>' % flag("F04") + quick
    body += '<h2>Which route applies to your money</h2><p>The route is set by where the money came from, not by your citizenship. Your case was not supplied (%s), so every case is listed.</p>' % flag("F01") + cases
    body += ('<h2>Why the money looks stuck</h2><p>For a foreign passport holder the bank does not apply the USD 50,000 yearly quota that Chinese citizens have. Instead it must see where each yuan came from and that tax was handled. '
             'With papers, there is no fixed ceiling. Without papers, the bank must refuse — and the missing paper is usually the tax certificate. %s</p>') % src(["S03", "S04", "S01"])
    body += ('<h2>Explore</h2><section class="tiles">'
      '<a href="methods.html"><b>Methods</b><span>%d routes with pros, cons and cost</span></a>'
      '<a href="costs.html"><b>Costs</b><span>$10,000 to $400,000 in 40 steps, every method</span></a>'
      '<a href="steps.html"><b>Steps</b><span>Exactly what to do, in order</span></a>'
      '<a href="taxes.html"><b>Taxes &amp; penalties</b><span>China and US, with amounts</span></a>'
      '<a href="flagged.html"><b>Flagged for Review</b><span>%d items not confirmed</span></a>'
      '<a href="sources.html"><b>Sources</b><span>%d official documents</span></a>'
      '<a href="review.html"><b>Repo review</b><span>%d findings on earlier work</span></a></section>') % (len(M), len(F), len(S), len(AUDIT))
    page("index.html", "Getting money out of China as a US citizen", "What it costs to turn yuan in a Chinese bank account into dollars in a US account, which routes are lawful, and where tax really bites.", body)

# ------------------------------------------------------------------ methods
def cost3(mm):
    c = mm["cost"]; out = []
    for u in (10000, 100000, 400000):
        r = BY[u]
        if c == "boc_std": out.append(usd(r["boc_std"]))
        elif c == "boc_full": out.append(usd(r["boc_full"]))
        elif c == "hsbc": out.append(usd(r["hsbc_fee_usd"]) + " fees")
        elif c == "ccb": out.append(usd(r["ccb_fee_usd"]) + " fees")
        elif c == "atm": out.append("%s fees, %d yr" % (usd(r["atm_fee_usd"]), r["atm_years"]))
        elif c == "cash": out.append("%s margin, %d trips" % (usd(r["spread"]), r["cash_trips5"]))
        elif c == "wise": out.append("%d transfer%s" % (r["wise_n"], "" if r["wise_n"] == 1 else "s"))
        elif c == "penalty": out.append("fine to " + usd0(r["fine30"]))
    return out
def build_methods():
    label = {"lawful": "Lawful", "conditional": "Lawful if you qualify", "unverified": "Not verified", "prohibited": "Prohibited"}
    def rows(kind):
        rs, ids, ns = [], [], []
        for mm in [x for x in M if x["kind"] == kind]:
            c = mm["cost"]
            if c == "rail": cc = ['%s <a href="costs.html#boc">by BOC wire</a>' % usd(BY[u]["boc_std"]) for u in (10000, 100000, 400000)]
            elif c is None: cc = [blank(mm["flag"]) if mm.get("flag") else "—"] * 3
            else:
                cc = cost3(mm)
                if c == "wise": cc = [x + "; fee " + blank("F09") for x in cc]
                if c in ("hsbc", "ccb"): cc = [x + " only " + flag("F08") for x in cc]
            steps = ' <a href="steps.html#%s">steps</a>' % mm["id"] if any(s[0] == mm["id"] for s in STEPS) else ""
            tx = lambda v: e(v) if v else (blank(mm["flag"]) if mm.get("flag") else "—")
            rs.append(["<b>%s</b>%s" % (e(mm["name"]), steps), '<span class="st %s">%s</span>' % (mm["status"], label[mm["status"]]),
                       cc[0], cc[1], cc[2], tx(mm["limit"]), tx(mm["who"]), tx(mm["pros"]), tx(mm["cons"]), src(mm["src"]) if mm["src"] else '<span class="unv">no official source found</span>'])
            ids.append(mm["id"]); ns.append(not mm["src"])
        return table(["Method", "Status", "Cost at $10,000", "Cost at $100,000", "Cost at $400,000", "Limit", "Who can use it", "Pros", "Cons", "Source"], rs, ids=ids, nosrc=ns)
    body = ('<p class="note">Two things are needed for every lawful transfer: a <b>reason the money may leave</b> (first table) and a <b>way to send it</b> (second table). Costs come from the second table. Prohibited routes are listed so you can recognise them; no instructions are given for them.</p>'
            '<h2 id="entitlement">1. Reasons the money may be converted</h2>' + rows("entitlement") +
            '<h2 id="rail">2. Ways to send it</h2><p>"fees" = bank fees only where that bank\'s exchange margin was not verified.</p>' + rows("rail") +
            '<h2 id="prohibited">3. Prohibited routes</h2><p>Cost shown is the statutory fine ceiling of 30% of the amount; see <a href="taxes.html#exposure">exposure by amount</a>.</p>' + rows("prohibited"))
    page("methods.html", "Every method, with pros and cons", "%d routes: %d lawful reasons to convert, %d ways to send, %d prohibited." % (len(M), sum(x["kind"] == "entitlement" for x in M), sum(x["kind"] == "rail" for x in M), sum(x["kind"] == "prohibited" for x in M)), body)

# ------------------------------------------------------------------ costs
def build_costs():
    inputs = table(["Input", "Value", "Source"], [
        ["Bank of China selling rate (you buy dollars)", "¥%s per $1" % ASK, src(["S09"])],
        ["Bank of China buying rate", "¥%s per $1" % BID, src(["S09"])],
        ["Midpoint of the two (reference value)", "¥%s per $1" % MID, src(["S09"])],
        ["Exchange margin, one way = (selling − midpoint) ÷ midpoint", pct((ASK - MID) / MID), src(["S09"])],
        ["Bank of China wire fee", "0.1%, min ¥50, max ¥260, plus ¥150 cable", src(["S10"])],
        ["Bank of China full-amount arrival", "+$25 per wire", src(["S10"])],
        ["HSBC China wire fee (Premier, Advance)", "0.1%, min ¥100, max ¥500, plus ¥120 cable; private-banking individual customers free", src(["S11"])],
        ["CCB wire fee (page dated 2016, %s)" % flag("F07"), "0.1%, min ¥20, max ¥300, plus ¥80 cable", src(["S12"])],
        ["Chase incoming wire", "$15 ($0 in the cases Chase lists)", src(["S31"])],
        ["Wise per-transfer cap", "¥300,000 from a China bank app", src(["S13"])],
        ["Overseas ATM cap", "¥100,000 per person per year; ¥10,000 per card per day", src(["S08"])],
        ["Bank of China overseas ATM fee", "¥12 + 1% per withdrawal, max ¥112", src(["S10"])],
        ["Cash carried out", "$5,000 without permit; $10,000 with a bank permit", src(["S07"])],
        ["Intermediary-bank deductions", blank("F04"), src(["S10"])],
        ["Other US banks' incoming fees", blank("F05"), src(["S31"])],
    ])
    s_all = ["S09", "S10", "S31"]
    summary = table(["Amount", "BOC standard wire", "% of amount", "BOC full-amount wire", "HSBC fees only", "CCB fees only", "Source"],
        [[A(r), "<b>%s</b>" % usd(r["boc_std"]), pct(r["boc_std"] / r["usd"]), usd(r["boc_full"]), usd(r["hsbc_fee_usd"]), usd(r["ccb_fee_usd"]), src(["S09", "S10", "S11", "S12", "S31"])] for r in ROWS], cls="num")
    t1 = table(["Amount", "Total estimated cost", "% of amount", "Exchange margin", "BOC fee", "BOC fee in ¥", "Chase incoming", "Intermediary banks", "Yuan needed", "Source"],
        [[A(r), "<b>%s</b>" % usd(r["boc_std"]), pct(r["boc_std"] / r["usd"]), usd(r["spread"]), usd(r["boc_fee_usd"]), cny(r["boc_fee_cny"]), usd(m["chase_in"]), blank("F04"), cny(r["boc_cny_needed"]), src(s_all)] for r in ROWS], cls="num")
    t2 = table(["Amount", "Total estimated cost", "% of amount", "Exchange margin", "BOC fee", "Full-amount fee", "Chase incoming", "Source"],
        [[A(r), "<b>%s</b>" % usd(r["boc_full"]), pct(r["boc_full"] / r["usd"]), usd(r["spread"]), usd(r["boc_fee_usd"]), usd(m["boc_full_usd"]), usd(m["chase_in"]), src(s_all)] for r in ROWS], cls="num")
    t3 = table(["Amount", "HSBC fee (Premier, Advance)", "In ¥", "Private-banking individuals", "Exchange margin", "Source"],
        [[A(r), "<b>%s</b>" % usd(r["hsbc_fee_usd"]), cny(r["hsbc_fee_cny"]), "$0.00", blank("F08"), src(["S11", "S09"])] for r in ROWS], cls="num")
    t4 = table(["Amount", "CCB fee", "In ¥", "Exchange margin", "Source"],
        [[A(r), "<b>%s</b>" % usd(r["ccb_fee_usd"]), cny(r["ccb_fee_cny"]), blank("F08"), src(["S12", "S09"])] for r in ROWS], cls="num")
    t5 = table(["Amount", "Transfers needed", "Wise fee", "Source"],
        [[A(r), "<b>%d</b>" % r["wise_n"], blank("F09"), src(["S13", "S09"])] for r in ROWS], cls="num")
    t6 = table(["Amount", "Calendar years needed", "Withdrawals", "Card-issuer fees", "% of amount", "Network rate and ATM surcharge", "Source"],
        [[A(r), "<b>%d</b>" % r["atm_years"], "%d" % r["atm_n"], usd(r["atm_fee_usd"]), pct(r["atm_fee_usd"] / r["usd"]), blank("F17"), src(["S08", "S10", "S09"])] for r in ROWS], cls="num")
    t7 = table(["Amount", "Crossings, no permit ($5,000)", "Crossings, bank permit ($10,000)", "Exchange margin", "Travel cost", "Source"],
        [[A(r), "<b>%d</b>" % r["cash_trips5"], "%d" % r["cash_trips10"], usd(r["spread"]), blank("F18"), src(["S07", "S09", "S10"])] for r in ROWS], cls="num")
    body = ('<p class="note"><b>How to read this.</b> "Amount" is the dollars you buy and send. Cost = exchange margin + Chinese bank fee + US receiving fee, each from a published figure. Anything not published is blank and flagged — not zero. One wire per amount; each extra wire repeats the fixed fees. Tax on the underlying income is separate: see <a href="taxes.html">Taxes &amp; penalties</a>.</p>'
        '<nav class="toc"><a href="#summary">Summary</a><a href="#boc">BOC standard</a><a href="#bocfull">BOC full-amount</a><a href="#hsbc">HSBC</a><a href="#ccb">CCB</a><a href="#wise">Wise</a><a href="#atm">ATM abroad</a><a href="#cash">Cash</a><a href="#inputs">Inputs</a></nav>'
        '<h2 id="summary">Summary: bank wires side by side</h2>' + summary +
        '<h2 id="boc">Bank of China, standard wire — complete estimate</h2><p>The only route for which every main component is published. Intermediary deductions stay blank.</p>' + t1 +
        '<h2 id="bocfull">Bank of China, full-amount arrival</h2><p>Adds $25 so that intermediary banks deduct nothing.</p>' + t2 +
        '<h2 id="hsbc">HSBC China — bank fees only</h2><p>Percentage fee valued at the Bank of China rate. HSBC\'s own exchange margin was not verified.</p>' + t3 +
        '<h2 id="ccb">China Construction Bank — bank fees only</h2><p>From a page dated 2016 (%s).</p>' % flag("F07") + t4 +
        '<h2 id="wise">Wise — how many transfers</h2><p>Yuan valued at the Bank of China midpoint; each transfer is capped at ¥300,000 and the total at about your after-tax China salary.</p>' + t5 +
        '<h2 id="atm">Cash withdrawals abroad with a mainland card</h2><p>Capped at ¥100,000 a year, so larger amounts take years. Fees assume full ¥10,000 withdrawals on a Bank of China debit card; yuan valued at the midpoint.</p>' + t6 +
        '<h2 id="cash">Carrying dollar cash</h2><p>How many border crossings the legal limits require. The dollars must still be bought lawfully first.</p>' + t7 +
        '<h2 id="inputs">Inputs and formula</h2>' + inputs +
        '<p class="formula">cost = amount × (selling − midpoint) ÷ midpoint &nbsp;+&nbsp; [ clamp(0.1% × amount × selling, min, max) + cable ] ÷ midpoint &nbsp;+&nbsp; US receiving fee</p>')
    page("costs.html", "Cost of every method, $10,000 to $400,000", "Estimated from published rates and tariffs read on %s. Most important figure first in every table." % CHECKED, body)

# ------------------------------------------------------------------ steps
def build_steps():
    names = {x["id"]: x["name"] for x in M}
    body = '<p class="note">Lawful routes only. Each step cites the rule or tariff it rests on. Start with the route that matches where your money came from (<a href="index.html">Summary</a>).</p><nav class="toc">'
    body += "".join('<a href="#%s">%s</a>' % (i, e(names[i])) for i, _, _ in STEPS) + "</nav>"
    for i, title, st in STEPS:
        body += '<h2 id="%s">%s</h2>' % (i, e(title))
        body += table(["Step", "What to do", "Source"], [["<b>%d</b>" % (n + 1), e(t), src(s)] for n, (t, s) in enumerate(st)])
    page("steps.html", "Step by step", "Exactly how each lawful route works, in order.", body)

# ------------------------------------------------------------------ taxes
def build_taxes():
    f = lambda rows: [["<b>%s</b>" % e(a), e(b) if b else blank("F11"), e(c), src(s)] for a, b, c, s in rows]
    ladder = table(["Amount", "Already taxed or exempt", "20% flat categories", "Wages, lowest rate 3%", "Wages, highest rate 45%", "Late surcharge per year on the 20% tax", "Evasion fine on the 20% tax", "Source"],
        [[A(r), "$0", "<b>%s</b>" % usd0(r["tax20"]), usd0(r["tax_lo"]), usd0(r["tax_hi"]), usd(r["late_year"]), "%s – %s" % (usd0(r["pen_lo"]), usd0(r["pen_hi"])), src(["S14", "S16"])] for r in ROWS], cls="num")
    expo = table(["Amount", "China: fine up to 30%", "China: serious cases up to 100%", "China: cash breach up to 20%", "US: willful FBAR, greater of $100,000 or 50%", "Source"],
        [[A(r), "<b>%s</b>" % usd0(r["fine30"]), usd0(r["fine100"]), usd0(r["cash20"]), usd0(r["fbar_w"]), src(["S01", "S23"])] for r in ROWS], cls="num")
    body = ('<p class="note"><b>The breakdown of the "conversion penalty".</b> It has three separate parts: (1) the exchange margin and bank fees — about 0.2% to 0.7%, on the <a href="costs.html">Costs</a> page; (2) Chinese income tax on the underlying income, only if it was not already paid; (3) penalties, only if rules are broken. Nothing is charged for the conversion as such.</p>'
        '<h2 id="cn">China: what is taxed</h2>' + table(["Item", "Rate", "Detail", "Source"], f(CN_TAX)) +
        '<h2 id="cnladder">China: tax if the whole amount were untaxed income</h2><p>A scenario table, not a bill: it assumes the full amount is taxable income of that type. If only part is untaxed, apply the rate to that part. Wage tax per amount is not computed (%s); the 3%% and 45%% columns are the statutory floor and ceiling.</p>' % flag("F02") + ladder +
        '<h2 id="us">United States: tax and reporting</h2>' + table(["Item", "Rule", "Detail", "Source"], f(US_TAX)) +
        '<h2 id="uspen">United States: penalties for not reporting</h2>' + table(["Failure", "Penalty", "Detail", "Source"], f(US_PEN)) +
        '<h2 id="exposure">Exposure on prohibited routes, by amount</h2><p>Statutory ceilings, computed from the rates in the State Council Regulation and the IRS table. The willful FBAR figure uses the statutory base before inflation adjustment (%s).</p>' % flag("F10") + expo)
    page("taxes.html", "Taxes and penalties", "What China and the United States tax, what must be reported, and what breaking the rules costs.", body)

# ------------------------------------------------------------------ flagged, sources, review
def build_flagged():
    rows, ids, ns = [], [], []
    for k, (t, d, s) in F.items():
        rows.append(["<b>%s</b>" % k, e(t), e(d), src(s) if s else ('<span class="unv">no official source applies</span> <a href="review.html">Repo review</a>' if k == "F22" else '<span class="unv">no official source found</span>')])
        ids.append(k); ns.append(not s)
    body = '<p class="note">Everything on this site that could not be confirmed from an official source, or where official sources disagree. These items did not block publication. Values behind them are left blank on the other pages.</p>' + table(["ID", "Issue", "What is missing or uncertain", "Source"], rows, ids=ids, nosrc=ns)
    page("flagged.html", "Flagged for Review", "%d open items for you to review. Tell us which to resolve." % len(F), body)
def build_sources():
    how = {"full": "Official page opened and read", "excerpt": "Official page text read via search-index excerpt"}
    rows = [["<b>%s</b>" % k, e(v["t"]), e(v["pub"]), e(v["v"]), how[v["how"]], '<a class="s" href="%s" rel="noopener">Open</a>' % e(v["u"])] for k, v in S.items()]
    nfull = sum(v["how"] == "full" for v in S.values())
    body = '<p class="note">%d official documents, all read on %s: %d opened in full, %d read through an excerpt of the official page. "Confirmed" lists exactly what was read; nothing else is claimed.</p>' % (len(S), CHECKED, nfull, len(S) - nfull) + table(["ID", "Document", "Publisher", "What was confirmed", "How", "Link"], rows, ids=list(S))
    page("sources.html", "Sources", "Official documents behind every row on this site.", body)
def build_review():
    inv = json.load(open(os.path.join(OUT, "data", "repo_inventory.json"), encoding="utf-8"))
    paths = {"R01": "README.md", "R02": "README.md", "R03": "README.md", "R04": "EXECUTIVE_SUMMARY.md", "R05": "EXECUTIVE_SUMMARY.md", "R06": "EXECUTIVE_SUMMARY.md",
             "R07": "EXECUTIVE_SUMMARY.md", "R08": "integration/costs.html", "R09": "EXECUTIVE_SUMMARY.md", "R10": "README.md", "R11": "integration/evidence.json", "R12": "COORDINATION.md", "R13": "COORDINATION.md", "R14": "EXECUTIVE_SUMMARY.md", "R15": "edition-l/data/costs.csv", "R16": "COORDINATION.md"}
    rows = [["<b>%s</b>" % i, '<span class="sev %s">%s</span>' % (sv.lower(), sv), e(w), e(d), e(fx), (src(s) + " " if s else "") + gh(paths[i])] for i, sv, w, d, fx, s in AUDIT]
    tot = {k: sum(v[k] for v in inv["dirs"].values()) for k in ("files", "html", "tr", "ext_links")}
    irows = [["<b>%s</b>" % e(k), str(v["files"]), str(v["html"]), format(v["tr"], ","), format(v["ext_links"], ","),
              '<a class="s" href="%s/tree/main%s" rel="noopener">Open</a>' % (REPO, "" if k == "(root)" else "/" + k)] for k, v in inv["dirs"].items()]
    irows.append(["<b>Total</b>", str(tot["files"]), str(tot["html"]), format(tot["tr"], ","), format(tot["ext_links"], ","), '<a class="s" href="%s" rel="noopener">Open</a>' % REPO])
    body = ('<p class="note">Review of the repository outside this edition as it stood on <code>main</code> at commit <code>%s</code>. The two root documents a reader meets first were checked line by line against sources re-read on %s. Every committed page was machine-scanned for broken local links (%d found) and external hosts (%d). The earlier editions\' thousands of rows were not individually re-certified — that is stated, not hidden.</p>'
            '<h2 id="findings">Findings</h2>' % (inv["snapshot_commit"][:7], CHECKED, inv["broken_local_links"], len(inv["hosts"])) +
            table(["ID", "Severity", "Where", "Finding", "Suggested fix", "Source"], rows, ids=[a[0] for a in AUDIT]) +
            '<h2 id="inventory">Inventory at review time</h2>' + table(["Folder", "Files", "HTML pages", "Table rows", "External links", "Source"], irows, cls="num"))
    page("review.html", "Repo review", "%d findings on the earlier editions, with the evidence for each." % len(AUDIT), body)

CSS = """:root{--bg:#f6f7f9;--card:#fff;--ink:#16202c;--mut:#5b6775;--line:#e2e6eb;--acc:#0b5cab;--warn:#b42318;--ok:#0a7c4a;--amb:#9a6700}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header{background:var(--card);border-bottom:1px solid var(--line);padding:.7rem 1rem;position:sticky;top:0;z-index:5}
.brand{font-weight:700;color:var(--ink);text-decoration:none;font-size:1.05rem}.brand span{color:var(--mut);font-weight:500;margin-left:.3rem}
header nav{display:flex;gap:.35rem;overflow-x:auto;margin-top:.5rem;padding-bottom:.15rem}
header nav a{white-space:nowrap;text-decoration:none;color:var(--ink);padding:.3rem .7rem;border-radius:999px;border:1px solid var(--line);font-size:.9rem;background:var(--bg)}
header nav a[aria-current]{background:var(--acc);border-color:var(--acc);color:#fff}
main{max-width:1100px;margin:0 auto;padding:1rem}h1{font-size:1.6rem;line-height:1.2;margin:.6rem 0 .3rem}h2{font-size:1.15rem;margin:1.8rem 0 .5rem;scroll-margin-top:6.5rem}
.lead{color:var(--mut);margin:0 0 1rem}a{color:var(--acc)}p{margin:.5rem 0}
.bluf{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:10px;padding:.4rem 1rem .8rem}.bluf h2{margin-top:.6rem}.bluf ol{margin:0;padding-left:1.2rem}.bluf li{margin:.45rem 0}
.cards,.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:.7rem;margin:1rem 0}
.card,.tiles a{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.8rem;display:block;text-decoration:none;color:var(--ink)}
.card small{display:block;color:var(--mut);font-size:.78rem;text-transform:uppercase;letter-spacing:.03em}.card b{display:block;font-size:1.35rem;margin:.15rem 0}.card span,.tiles span{display:block;color:var(--mut);font-size:.85rem}
.card.warn b{color:var(--warn)}.tiles a:hover{border-color:var(--acc)}.tiles b{color:var(--acc)}
.note,.formula{background:#eef4fb;border:1px solid #d3e3f5;border-radius:8px;padding:.6rem .8rem;font-size:.95rem}.formula{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.82rem;overflow-x:auto}
.toc{display:flex;flex-wrap:wrap;gap:.35rem;margin:.8rem 0}.toc a{font-size:.85rem;padding:.2rem .6rem;border:1px solid var(--line);border-radius:999px;background:var(--card);text-decoration:none}
.tw{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px;margin:.5rem 0 1rem}
table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{padding:.45rem .6rem;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:#f0f2f5;font-size:.78rem;text-transform:uppercase;letter-spacing:.02em;color:var(--mut);position:sticky;top:0}tbody tr:last-child td{border-bottom:0}
table.num td,table.num th{white-space:nowrap;text-align:right}table.num td:first-child,table.num th:first-child{text-align:left;position:sticky;left:0;background:var(--card);border-right:1px solid var(--line)}table.num th:first-child{background:#f0f2f5}
table.num td:last-child,table.num th:last-child{text-align:left}tr:target td{background:#fff8e1}
a.s,a.f{display:inline-block;font-size:.75rem;padding:0 .35rem;border-radius:4px;border:1px solid #c9dcf2;background:#f2f7fd;text-decoration:none;margin:1px 0}a.f{border-color:#f1d9a8;background:#fff7e6;color:var(--amb)}
.unv{font-size:.72rem;color:var(--amb);border:1px dashed #e0b860;border-radius:4px;padding:0 .3rem;white-space:nowrap}td.blank{background:#fffdf5}
.st,.sev{font-size:.75rem;padding:.05rem .45rem;border-radius:999px;white-space:nowrap;border:1px solid}.st.lawful,.sev.verified{color:var(--ok);border-color:#a6dcc0;background:#effaf3}
.st.conditional,.sev.medium{color:var(--amb);border-color:#f1d9a8;background:#fff7e6}.st.unverified,.sev.low{color:var(--mut);border-color:var(--line);background:#f4f5f7}.st.prohibited,.sev.high{color:var(--warn);border-color:#f3b8b2;background:#fef3f2}
code{background:#eef0f3;padding:0 .25rem;border-radius:4px;font-size:.85em}footer{max-width:1100px;margin:1.5rem auto;padding:1rem;color:var(--mut);font-size:.82rem;border-top:1px solid var(--line)}
@media(max-width:760px){h1{font-size:1.3rem}table.stack thead{display:none}table.stack,table.stack tbody,table.stack tr,table.stack td{display:block;width:100%}
table.stack tr{border-bottom:6px solid var(--bg);padding:.3rem 0}table.stack td{border:0;padding:.25rem .7rem}table.stack td::before{content:attr(data-label);display:block;font-size:.7rem;text-transform:uppercase;letter-spacing:.03em;color:var(--mut)}
table.stack td:first-child::before{display:none}table.stack td:first-child{font-size:1rem;padding-top:.5rem}table.num{font-size:.82rem}table.num td,table.num th{padding:.35rem .5rem}}
"""

def main():
    os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
    open(os.path.join(OUT, "style.css"), "w", encoding="utf-8").write(CSS)
    keys = ["usd", "cny_principal", "spread", "boc_fee_cny", "boc_fee_usd", "boc_std", "boc_full", "boc_cny_needed", "hsbc_fee_cny", "hsbc_fee_usd", "ccb_fee_cny", "ccb_fee_usd",
            "wise_n", "atm_years", "atm_n", "atm_fee_cny", "atm_fee_usd", "cash_trips5", "cash_trips10", "tax20", "tax_lo", "tax_hi", "late_year", "pen_lo", "pen_hi", "fine30", "fine100", "cash20", "fbar_w"]
    out = [{k: (int(r[k]) if isinstance(r[k], int) else str(q(r[k]))) for k in keys} for r in ROWS]
    with open(os.path.join(OUT, "data", "costs.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator="\n"); w.writeheader(); w.writerows(out)
    dump = lambda name, obj: json.dump(obj, open(os.path.join(OUT, "data", name), "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    dump("costs.json", {"checked": CHECKED, "model": MODEL, "midpoint": str(MID), "rows": out})
    dump("sources.json", S); dump("methods.json", M)
    dump("flags.json", {k: {"title": t, "detail": d, "sources": s} for k, (t, d, s) in F.items()})
    build_index(); build_methods(); build_costs(); build_steps(); build_taxes(); build_flagged(); build_sources(); build_review()
    print("edition-abd04d5f built: 8 pages, %d sources, %d methods, %d flags, %d cost rows" % (len(S), len(M), len(F), len(ROWS)))
if __name__ == "__main__": main()
