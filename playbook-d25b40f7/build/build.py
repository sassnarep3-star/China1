#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the Playbook site and data exports. Standard library only; deterministic."""
import csv, glob, html, io, json, os, sys
from decimal import Decimal as D, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import content as C   # noqa: E402
import model as M     # noqa: E402

OUT = os.path.abspath(os.path.join(HERE, ".."))
REPO_BLOB = C.REPO + "/blob/"


def e(s):
    return html.escape(str(s), quote=True)


def load_evidence():
    ev = {}
    for f in sorted(glob.glob(os.path.join(OUT, "research", "evidence_*.json"))):
        for s in json.load(open(f, encoding="utf-8")):
            assert s["id"] not in ev, s["id"]
            ev[s["id"]] = s
    return ev


EV = load_evidence()
FLAG = {f[0]: f for f in C.FLAGS}
METH = {m["id"]: m for m in C.METHODS}
AUDIT = json.load(open(os.path.join(OUT, "data", "repo_audit.json"), encoding="utf-8"))
EARLIER = json.load(open(os.path.join(OUT, "data", "earlier_candidates.json"), encoding="utf-8"))


def qtext(sid):
    return " ".join(q["text"] for q in EV[sid]["quotes"])


def validate():
    for k, (v, u, sid, needle) in C.PARAMS.items():
        assert needle in qtext(sid), ("parameter not found in quoted text", k, sid)
    for q in C.WISE_QUOTES:
        assert q[3] in qtext(q[2]) and q[4] in qtext(q[2]), q[2]
    for sid, needle in C.FACT_CHECKS:
        assert needle in qtext(sid), (sid, needle)
    used_f = set()
    for m in C.METHODS:
        used_f.update(m["flags"])
        for s in m["src"] + [x for st in m["steps"] for x in st[1]]:
            assert s in EV, (m["id"], s)
        if m["model"] is None:
            assert not m["steps"], m["id"]
    for f in C.FLAGS:
        assert f[3] and all(s in EV for s in f[3]), f[0]
    for f in used_f:
        assert f in FLAG, f


# ---------- formatting
def q(x, dp=2):
    return x.quantize(D(1).scaleb(-dp), rounding=ROUND_HALF_UP)


def money(x, dp=2):
    return "$" + format(q(x, dp), ",.%df" % dp)


def money0(x):
    return money(x, 0)


def cny(x, dp=2):
    return "CNY " + format(q(x, dp), ",.%df" % dp)


def pct(x, dp=2):
    return format(q(x * 100, dp), ".%df" % dp) + "%"


BL = '<span class="blank">blank</span>'


def mb(x):
    return BL if x is None else money(x)


def S(ids):
    return '<span class="srcs">' + " ".join(
        '<a class="src" href="%s" title="%s" rel="noopener">%s</a>' % (e(EV[i]["url"]), e(EV[i]["title"]), i) for i in ids) + "</span>"


def F(ids):
    return " ".join('<a class="flag" href="flagged.html#%s" title="%s">%s</a>' % (f, e(FLAG[f][1]), f) for f in ids)


def badge(v):
    cls = "b-ok" if v in ("Recommended", "Lawful") else ("b-lim" if v == "Capacity-limited" else "b-no")
    return '<span class="badge %s">%s</span>' % (cls, e(v))


def ul(items):
    return '<ul class="pc">' + "".join("<li>%s</li>" % e(i) for i in items) + "</ul>" if items else ""


def table(heads, rows, cls="stack", cap=None, right=()):
    out = ['<div class="tw"><table class="%s">' % cls]
    if cap:
        out.append("<caption>%s</caption>" % cap)
    out.append("<thead><tr>" + "".join(
        '<th scope="col"%s>%s</th>' % (' class="r"' if i in right else "", e(h)) for i, h in enumerate(heads)) + "</tr></thead><tbody>")
    for r in rows:
        rid = ""
        if isinstance(r, tuple):
            rid, r = ' id="%s"' % r[0], r[1]
        assert len(r) == len(heads), (heads, r[:2])
        assert any('class="src"' in c for c in r), ("row without an official source link", r[:2])
        out.append("<tr%s>" % rid + "".join(
            '<td data-label="%s"%s>%s</td>' % (e(h), ' class="r"' if i in right else "", c)
            for i, (h, c) in enumerate(zip(heads, r))) + "</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


NAV = [("index.html", "Home"), ("summary.html", "Summary"), ("methods.html", "Methods"), ("steps.html", "Steps"),
       ("costs.html", "Costs"), ("breakdown.html", "Breakdown"), ("china-tax.html", "China tax"), ("us-tax.html", "US tax"),
       ("prohibited.html", "Prohibited"), ("review.html", "Repo review"), ("flagged.html", "Flagged"),
       ("sources.html", "Sources"), ("methodology.html", "Method")]
PAGES = {}


def page(slug, title, lead, body):
    cur = "costs.html" if slug.startswith("ladder-") else slug
    nav = "".join('<a href="%s"%s>%s</a>' % (h, ' aria-current="page"' if h == cur else "", t) for h, t in NAV)
    PAGES[slug] = (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>%s · CNY to USD Playbook</title>"
        '<meta name="description" content="%s">'
        '<link rel="stylesheet" href="style.css"></head><body>'
        '<header class="top"><a class="brand" href="index.html">CNY→USD Playbook</a><nav aria-label="Sections">%s</nav></header>'
        '<main><h1>%s</h1><p class="lead">%s</p>%s</main>'
        '<footer>Figures as of %s. General information, not legal or tax advice. Every figure links to the page it was read from; '
        'blank cells are explained on <a href="flagged.html">Flagged for review</a>. '
        '<a href="../index.html">All editions in this repository</a>.</footer></body></html>\n'
    ) % (e(title), e(title + ". Sourced figures as of " + C.AS_OF + "."), nav, e(title), lead, body, C.AS_OF)


# ---------- model helpers
MODEL_SRC = {
    "boc_full": ["FEE-01", "FEE-02", "FEE-09"], "boc_sha": ["FEE-01", "FEE-02", "FEE-09"],
    "boc_property": ["FEE-01", "FEE-02", "FEE-09", "CN-TAX-07"], "boc_wire_only": ["FEE-02", "FEE-09"],
    "boc_quota": ["FEE-01", "FEE-02", "FEE-09", "CN-FX-02"], "hsbc_premier": ["FEE-06", "FEE-09"],
    "hsbc_pb": ["FEE-06", "FEE-09"], "wise": ["FEE-07"], "boc_dividend": ["CN-TAX-05", "US-07"],
    "cash": ["FEE-01", "FEE-02", "CN-FX-02"], "atm": ["FEE-04", "CN-FX-10"], "small_recon": ["FEE-01", "FEE-02", "CN-FX-02"],
}
FEE_LABEL = {"wise": "Wise fee", "cash": "Permit fee", "atm": "Bank withdrawal fees", "small_recon": "Exchange fee"}
ADDON_LABEL = {"boc_full": "Full-amount fee", "boc_quota": "Full-amount fee", "boc_property": "Full-amount fee",
               "boc_wire_only": "Full-amount fee", "boc_sha": "Intermediary deductions", "hsbc_premier": "Pay Exact",
               "hsbc_pb": "Overseas bank charges"}
RECV_LABEL = {"cash": "US deposit charge", "small_recon": "US deposit charge", "atm": "ATM owner surcharge", "wise": "US receiving fee"}
WITH_CNY = ("boc_full", "boc_sha", "boc_quota", "boc_property", "cash", "small_recon")
LADDERS = {m["id"]: M.ladder(m["model"]) for m in C.METHODS if m["model"]}
COMPLETE = {mid: all(r["total"] is not None for r in rows) for mid, rows in LADDERS.items()}


def at(mid, amount):
    return next(r for r in LADDERS[mid] if r["amount"] == D(amount))


def row_src(m, r):
    ids = list(MODEL_SRC[m["model"]])
    if "wise_src" in r:
        ids.append(r["wise_src"])
    return S(ids) + (" " + F(r["flags"]) if r["flags"] else "")


def cell_total(r):
    if r["total"] is not None:
        return money(r["total"])
    if r.get("tax") is not None:
        return "%s tax + %s" % (money0(r["tax"]), BL)
    if r["known"] is not None:
        return "%s + %s" % (money(r["known"]), BL)
    return BL


def mlink(m, text=None):
    return '<a href="methods.html#%s">%s</a>' % (m["id"], e(text or m["id"]))


# ---------- pages
def p_index():
    a10, a100, a400 = at("M01", 10000), at("M01", 100000), at("M01", 400000)
    w10 = at("M05", 10000)
    bank10_before = a10["total"] - a10["recv"]
    answer = (
        '<div class="answer"><ol>'
        "<li><b>Use documents, not the USD 50,000 quota.</b> With a foreign passport you are an “overseas individual” under China's "
        "foreign-exchange rules. RMB that is lawful income earned in China can be converted and wired on your ID plus proof of where it "
        "came from, including tax records. The rule text sets no yearly cap for this. %s</li>"
        "<li><b>Lowest cost among paths with every charge published: one Bank of China wire with full-amount arrival.</b> Total %s on $10,000 (%s), "
        "%s on $100,000 (%s) and %s on $400,000 (%s), including a $15 receiving fee at Chase. %s</li>"
        "<li><b>Send one wire, not several.</b> Fixed charges reach %s per wire once the amount passes %s. "
        "Splitting $400,000 into eight wires costs %s instead of %s. %s</li>"
        "<li><b>Under about $20,000, Wise's from-CNY service costs less.</b> Its fee on $10,000 is %s, against %s for the bank wire before "
        "any US receiving fee. It is limited to CNY 300,000 per transfer and to what your China tax records support. %s</li>"
        "<li><b>The route depends on where the money came from.</b> Wages, pre-emigration assets, an inheritance, a home sale and company "
        "profits each have their own rule. Pick yours in the table below.</li>"
        "<li><b>Moving your own money is not taxed. The income behind it is.</b> China taxes dividends at 20%% since 1 September 2026 and "
        "home-sale gains at 20%%. The US taxes worldwide income and credits China income tax. %s</li>"
        "</ol></div>"
    ) % (S(["CN-FX-01", "CN-FX-02"]),
         money(a10["total"]), pct(a10["pct"]), money(a100["total"]), pct(a100["pct"]), money(a400["total"]), pct(a400["pct"]),
         S(["FEE-01", "FEE-02", "FEE-09"]),
         money(M.FIXED_AT_CAP), money0(M.COMM_CAP_AT), money(M.many_wires(D(400000), 8)), money(a400["total"]), S(["FEE-02"]),
         money(w10["known"]), money(bank10_before), S(["FEE-07", "FEE-10"]),
         S(["CN-TAX-05", "CN-TAX-04", "US-08", "US-05"]))
    risk = (
        '<div class="answer risk"><ul>'
        "<li><b>China:</b> unlawful routes carry fines of up to 30%% of the amount, or 30%% up to the whole amount in serious cases, plus "
        "criminal liability. Splitting amounts or borrowing other people's quotas puts you on a watch list for three years. %s</li>"
        "<li><b>United States:</b> a China account above $10,000 must be reported on the FBAR. The maximum penalty is $16,536 when "
        "non-willful; a willful violation is far higher. Form 8938 and Form 3520 have their own thresholds. %s</li>"
        "<li><b>Not found in the rules read:</b> a bulk route for savings with no income or tax paper trail. %s</li>"
        "</ul></div>"
    ) % (S(["CN-FX-03", "CN-FX-02"]), S(["US-02", "US-03", "US-04"]), S(["CN-FX-02"]))
    kpis = [
        (pct(M.ONE_WAY), "exchange margin, one way, on Bank of China's board"),
        (money(M.FIXED_AT_CAP), "fixed charges per large wire"),
        (money(a100["total"]), "total cost on $100,000, one wire"),
        (money(a400["total"]), "total cost on $400,000, one wire"),
        (str(len(C.METHODS)), "methods examined here"),
        (str(len(C.FLAGS)), "items flagged for review"),
    ]
    grid = '<div class="grid">' + "".join('<div class="kpi"><b>%s</b><span>%s</span></div>' % (e(a), e(b)) for a, b in kpis) + "</div>"
    dec = table(["Your situation", "Route", "Why", "Sources"],
                [[e(d[0]), ('%s %s' % (mlink(METH[d[1]]), e(METH[d[1]]["name"]))) if d[1] else '<a href="methods.html#cat-D">No bulk route found</a>',
                  e(d[2]), S(d[3])] for d in C.DECISION])
    cards = [("summary.html", "Executive summary", "Ten findings on one page"),
             ("methods.html", "Methods by category", "Who qualifies, limits, pros and cons"),
             ("steps.html", "Step by step", "Numbered steps for each lawful method"),
             ("costs.html", "Cost ladders", "$10,000 to $400,000 in 40 steps"),
             ("breakdown.html", "Cost and penalty breakdown", "Where each dollar goes; legal exposure"),
             ("china-tax.html", "China tax", "By type of income"),
             ("us-tax.html", "US tax and reporting", "FBAR, Form 8938, Form 3520"),
             ("prohibited.html", "Prohibited schemes", "What not to do, and the penalties"),
             ("review.html", "Repository review", "Errors found in earlier editions"),
             ("flagged.html", "Flagged for review", "Everything left blank, and why"),
             ("sources.html", "Sources", "%d official pages with the quoted text" % len(EV)),
             ("methodology.html", "Method", "How the numbers are built and checked")]
    links = '<div class="grid">' + "".join(
        '<a class="card" href="%s"><b>%s</b><span>%s</span></a>' % (h, e(t), e(d)) for h, t, d in cards) + "</div>"
    body = ("<h2>The short answer</h2>" + answer + "<h2>Key numbers</h2>" + grid +
            "<h2>Pick your route by where the money came from</h2>" + dec +
            "<h2>Cost at a glance</h2>" + glance_table() +
            '<p class="note">Totals appear only where every input is a published figure. '
            "“+ blank” means part of the cost has no published figure; the flag in the last column explains which part.</p>"
            "<h2>What can go badly wrong</h2>" + risk + "<h2>All sections</h2>" + links)
    page("index.html", "Moving RMB out of China into US dollars",
         "A decision guide for a US citizen with money in mainland China. Figures as of 10 November 2026. "
         "Every figure links to the official page it was read from.", body)


def glance_table():
    heads = ["Method"] + [money0(a) for a in M.BENCH] + ["Sources"]
    rows = []
    for m in C.METHODS:
        if not m["model"]:
            continue
        r100 = at(m["id"], 100000)
        rows.append(['%s %s' % (mlink(m), e(m["name"]))] + [cell_total(at(m["id"], a)) for a in M.BENCH] +
                    ['<a href="ladder-%s.html">all 40 rows</a> ' % m["id"] + row_src(m, r100)])
    return table(heads, rows, cls="num", right=(1, 2, 3, 4, 5))


def p_summary():
    a10, a100, a400 = at("M01", 10000), at("M01", 100000), at("M01", 400000)
    rows = [
        ["1", "You are an overseas individual, and that helps",
         "China's quota of USD 50,000 a year is for Chinese residents and for holders of the Foreign Permanent Resident ID Card. "
         "A passport holder converts lawful China income on documents instead, with no yearly cap in the rule.",
         S(["CN-FX-01", "CN-FX-02"]) + " " + F(["F08"])],
        ["2", "The document that matters is the tax record",
         "The bank asks for proof of the source of the RMB, including tax evidence, checks it, and may refuse with a stated reason. "
         "A single payment above USD 50,000 may also need a tax filing.", S(["CN-FX-02", "CN-TAX-02"]) + " " + F(["F24"])],
        ["3", "One Bank of China wire has the lowest fully published cost",
         "%s on $10,000, %s on $100,000, %s on $400,000. That is exchange margin plus commission, cable fee, the full-amount fee and "
         "Chase's receiving fee. HSBC's exchange rate is not published, so its total cannot be compared." % (money(a10["total"]), money(a100["total"]), money(a400["total"])),
         S(["FEE-01", "FEE-02", "FEE-09", "FEE-06"]) + " " + F(["F17", "F19", "F03", "F02"])],
        ["4", "Most of the cost at large sizes is the exchange margin",
         "Buying USD costs %s against the midpoint of the board. The %s often quoted is the full distance between the bank's buying and "
         "selling rates. On $400,000 the margin is %s of the %s total." % (
             pct(M.ONE_WAY, 4), pct(M.WIDTH, 2), money(a400["fx"]), money(a400["total"])), S(["FEE-01"])],
        ["5", "Do not split a large amount into small wires",
         "The commission stops at CNY 260 and the other charges are per wire. $400,000 costs %s in one wire, %s in four, %s in eight." % (
             money(M.many_wires(D(400000), 1)), money(M.many_wires(D(400000), 4)), money(M.many_wires(D(400000), 8))), S(["FEE-02"])],
        ["6", "Wise is cheaper only for small amounts",
         "Wise's quoted fee is %s on CNY 66,763 and %s on CNY 300,000, its limit per transfer. The bank wire is cheaper from about $20,000 "
         "upward." % (cny(C.WISE_QUOTES[0][1]), cny(C.WISE_QUOTES[-1][1])), S(["FEE-10", "FEE-08", "FEE-07"]) + " " + F(["F04"])],
        ["7", "Naturalised citizens and heirs have approval routes",
         "Assets owned before you took foreign citizenship, and estates you inherit, leave through a SAFE approval: no fee, a decision "
         "within 20 working days, and the money may go in one remittance. The old 50/25/25 staging was abolished.",
         S(["CN-FX-04", "CN-FX-07", "CN-FX-08"]) + " " + F(["F25"])],
        ["8", "Converting is not a taxable event; the income is",
         "Wages were taxed when paid. Dividends from a foreign-invested company bear 20% from 1 September 2026. A home sale bears 20% of the "
         "gain, or 1%–3% of the price where cost records are incomplete. Bank interest is exempt for now.",
         S(["CN-TAX-04", "CN-TAX-05", "CN-TAX-07", "CN-TAX-06"])],
        ["9", "The US taxes the income, not the transfer",
         "A US citizen reports worldwide income and may credit China income tax. A currency gain on a personal conversion is ignored up to "
         "$200. An inheritance is not income but is reported on Form 3520 above $100,000.", S(["US-08", "US-05", "US-06", "US-04"])],
        ["10", "Reporting failures cost more than any fee",
         "FBAR above $10,000 in foreign accounts; Form 8938 above its thresholds; currency above $10,000 carried across the border. "
         "The FBAR maximum is $16,536 when non-willful.", S(["US-02", "US-03", "US-09"]) + " " + F(["F11"])],
        ["11", "Shortcuts are where people lose real money",
         "Splitting, borrowed quotas, underground banks, false documents and crypto bridges are prohibited. Fines run to 30% of the amount, "
         "or up to the whole amount in serious cases.", S(["CN-FX-03", "CN-FX-02", "CN-FX-09"])],
        ["12", "What stays unverified",
         "%d items are left blank rather than estimated, including intermediary-bank deductions, HSBC's exchange rate, the current desk "
         "procedure for home-sale proceeds and the cost of notarised documents." % len(C.FLAGS),
         S(["FEE-02", "FEE-06", "CN-FX-11"]) + ' <a href="flagged.html">all flags</a>'],
    ]
    nxt = ("<h2>What to do, in order</h2><div class=\"answer\"><ol>"
           "<li>Work out where the RMB came from and find the matching route on the <a href=\"index.html\">home page</a>.</li>"
           "<li>Collect the tax records for that income before visiting the bank.</li>"
           "<li>Ask the bank which category your account carries (overseas or domestic individual) and which documents it wants.</li>"
           "<li>Convert and send in one wire with full-amount arrival, to an account in your own name.</li>"
           "<li>File the US reports that apply for the year: FBAR, Form 8938, Form 3520.</li></ol></div>")
    page("summary.html", "Executive summary",
         "Twelve findings, most important first. Each row links to the official text behind it.",
         table(["#", "Finding", "Detail", "Sources"], rows) + nxt)


def p_methods():
    body = ['<p class="note">%d methods were worked through in this session. A further %d candidates from earlier editions are listed at '
            'the end as not re-verified.</p>' % (len(C.METHODS), len(EARLIER))]
    for cid, cname, cdesc in C.CATS:
        body.append('<h2 id="cat-%s">%s. %s</h2><p class="note">%s</p>' % (cid, cid, e(cname), e(cdesc)))
        rows = []
        for m in C.METHODS:
            if m["cat"] != cid:
                continue
            cost = cell_total(at(m["id"], 100000)) if m["model"] else BL
            more = ('<a href="steps.html#%s">steps</a> · <a href="ladder-%s.html">costs</a> ' % (m["id"], m["id"])) if m["model"] else ""
            rows.append((m["id"], [
                "<b>%s</b> %s<br>%s" % (m["id"], e(m["name"]), badge(m["verdict"])),
                e(m["who"]) or "–", e(m["cap"]) or "–", e(m["time"]) or "–", ul(m["pros"]) or "–", ul(m["cons"]) or "–",
                cost, more + S(m["src"]) + " " + F(m["flags"])]))
        body.append(table(["Method", "Who can use it", "Limit", "Time", "Advantages", "Drawbacks", "Cost on $100,000", "Sources and flags"], rows))
    rows = []
    for c in EARLIER:
        rows.append(['<b>%s</b> %s' % (c["id"], e(c["name"])), e(c["status"]),
                     '<a href="../%s">Edition H page</a>' % e(c["page"]),
                     " ".join('<a class="src" href="%s" title="%s" rel="noopener">%s</a>' % (e(s["url"]), e(s["title"]), e(s["id"])) for s in c["sources"])])
    body.append('<h2 id="earlier">Candidates from earlier editions, not re-verified here</h2>'
                '<p class="note">Listed so nothing is lost. Status and source links are Edition H\'s; this session did not re-read them, '
                'so they carry no steps or costs here.</p>')
    body.append(table(["Candidate", "Edition H status", "Detail", "Official source cited by Edition H"], rows))
    page("methods.html", "Methods by category",
         "Every lawful way found to turn RMB in China into dollars in a US account, with who qualifies, the limit, and the trade-offs.",
         "".join(body))


def p_steps():
    body = []
    for m in C.METHODS:
        if not m["steps"]:
            continue
        rows = [[str(i), e(t), S(src)] for i, (t, src) in enumerate(m["steps"], 1)]
        body.append('<h2 id="%s">%s. %s</h2><p class="note">%s %s · <a href="ladder-%s.html">cost ladder</a> · %s</p>' % (
            m["id"], m["id"], e(m["name"]), badge(m["verdict"]), e(m["who"]), m["id"], F(m["flags"])))
        body.append(table(["#", "Step", "Sources"], rows))
    body.append('<p class="note">Prohibited schemes and unconfirmed candidates have no steps on this site.</p>')
    page("steps.html", "Step by step",
         "Numbered steps for each lawful method. Each step links to the rule or tariff line it rests on.", "".join(body))


def ladder_table(m):
    model = m["model"]
    rows_ = LADDERS[m["id"]]
    cols = [("Amount", lambda r: money0(r["amount"]))]
    if model in WITH_CNY:
        cols.append(("CNY to buy it", lambda r: cny(r["cny"])))
    if model == "wise":
        cols.append(("CNY sent", lambda r: cny(r["wise_cny"], 0) if "wise_cny" in r else BL))
    if model == "boc_dividend":
        cols += [("China tax withheld, 20%", lambda r: money0(r["tax"])),
                 ("If the treaty ceiling of 10% applied", lambda r: money0(r["tax_treaty"])),
                 ("Dividend left after 20%", lambda r: money0(r["amount"] - r["tax"])),
                 ("Wire cost", lambda r: BL)]
    else:
        if model != "boc_wire_only":
            cols.append(("Exchange margin", lambda r: mb(r["fx"])))
        cols.append((FEE_LABEL.get(model, "Commission + cable"), lambda r: mb(r["fees"])))
        if model in ADDON_LABEL:
            cols.append((ADDON_LABEL[model], lambda r: mb(r["addon"])))
        cols.append((RECV_LABEL.get(model, "US receiving fee"), lambda r: mb(r["recv"])))
        if COMPLETE[m["id"]]:
            cols += [("Total", lambda r: "<b>%s</b>" % money(r["total"])), ("% of amount", lambda r: pct(r["pct"]))]
        else:
            cols += [("Published costs", lambda r: mb(r["known"])), ("Total", lambda r: BL)]
    if model == "boc_property":
        cols += [("Income tax if 1% of price", lambda r: money0(r["tax_low"])), ("if 3% of price", lambda r: money0(r["tax_high"]))]
    cols.append(("How many", lambda r: e(r["units"])))
    cols.append(("Sources", lambda r: row_src(m, r)))
    heads = [c[0] for c in cols]
    rows = [[c[1](r) for c in cols] for r in rows_]
    return table(heads, rows, cls="num", right=tuple(range(0, len(heads) - 2)))


LADDER_NOTE = {
    "boc_full": "One wire. Exchange margin = amount × (selling rate − midpoint) ÷ midpoint. Commission = 0.1% of the amount, at least CNY 50 and at most CNY 260, plus CNY 150 cable, converted at the midpoint. Full-amount fee $25. Receiving fee $15 (Chase).",
    "boc_sha": "As M01 without the full-amount fee. Foreign banks then deduct their charges from the principal; no figure is published, so the total stays blank.",
    "boc_wire_only": "No exchange takes place. Commission, cable, full-amount fee and the receiving fee only.",
    "boc_quota": "At most USD 50,000 a year on ID alone, so larger amounts need one wire per calendar year. Each wire is costed as in M01.",
    "boc_property": "Wire cost as M01. The two tax columns illustrate the deemed income tax if the sale price equalled the amount; with full cost records the tax is 20% of the gain instead.",
    "hsbc_premier": "Commission 0.1% (CNY 100 to CNY 500) plus CNY 120 cable and CNY 200 Pay Exact, converted at Bank of China's midpoint. HSBC's exchange rate was not retrieved, so the margin and the total are blank.",
    "hsbc_pb": "Commission and cable are free for individual Private Banking customers. The exchange rate and overseas bank charges were not retrieved.",
    "wise": "Fees are Wise's own quotes read on 10 November 2026 for CNY 66,763, 133,525, 200,288 and 267,050, converted at Bank of China's midpoint. Wise states it applies the mid-market rate. Amounts above CNY 300,000 need several transfers and are not quoted.",
    "boc_dividend": "The amount is the gross dividend declared. The company withholds 20%. The company's own wire tariff was not retrieved.",
    "cash": "Exchange margin on the cash selling rate, which equals the wire rate on the board. The carrying permit costs CNY 10, waived until 31 December 2026. Travel is not counted.",
    "atm": "Bank of China charges CNY 12 plus 1% per withdrawal, at most CNY 112. The card network's exchange rate and the ATM owner's surcharge are not published in advance.",
    "small_recon": "USD 500 a day on ID alone. Bank of China branches charge no exchange fee.",
}


def p_costs():
    prm = []
    names = {"boc_bid": "Bank of China buys USD at", "boc_ask": "Bank of China sells USD at", "boc_comm_rate": "Commission rate",
             "boc_comm_min_cny": "Commission minimum", "boc_comm_max_cny": "Commission maximum", "boc_cable_cny": "Cable fee, international",
             "boc_full_arrival_usd": "Full-amount arrival fee", "boc_full_arrival_ny_usd": "Full-amount fee if the receiving bank has an account at BOC New York",
             "chase_incoming_usd": "Chase incoming wire fee", "hsbc_comm_rate": "HSBC commission rate", "hsbc_comm_min_cny": "HSBC commission minimum",
             "hsbc_comm_max_cny": "HSBC commission maximum", "hsbc_cable_cny": "HSBC cable charge", "hsbc_payexact_cny": "HSBC Pay Exact",
             "wise_cap_cny": "Wise limit per transfer from a bank app", "atm_fixed_cny": "Overseas ATM fee, fixed part", "atm_rate": "Overseas ATM fee, variable part",
             "atm_max_cny": "Overseas ATM fee, maximum", "card_day_cny": "Overseas cash by card, daily limit", "card_year_cny": "Overseas cash by card, yearly limit",
             "cash_no_permit_usd": "Cash carried out without a permit", "cash_permit_usd": "Cash carried out with a bank permit",
             "cash_withdraw_day_usd": "Foreign cash withdrawal on ID", "recon_day_usd": "Small conversion back on ID", "quota_usd": "Yearly purchase quota",
             "div_rate": "Tax on dividends to foreign individuals", "treaty_div_cap": "Treaty ceiling on dividend tax",
             "deemed_low": "Deemed tax on a home sale, low end", "deemed_high": "Deemed tax on a home sale, high end",
             "fbar_threshold": "FBAR threshold", "fbar_nonwillful": "FBAR maximum, non-willful", "fbar_willful": "FBAR willful figure in the table",
             "f3520_threshold": "Form 3520 threshold for foreign gifts and bequests", "cbp_threshold": "Currency report at the US border",
             "s988_threshold": "Personal currency gain ignored up to"}
    for k, (v, unit, sid, needle) in C.PARAMS.items():
        prm.append([e(names[k]), e(format(v, "f")), e(unit), "<code>%s</code>" % e(needle), S([sid])])
    derived = [
        ["Midpoint", e(format(M.MID, "f")), "CNY per USD", "(buy + sell) ÷ 2 ÷ 100", S(["FEE-01"])],
        ["Exchange margin, one way", pct(M.ONE_WAY, 4), "of amount", "(sell − midpoint) ÷ midpoint", S(["FEE-01"])],
        ["Bid–ask width", pct(M.WIDTH, 4), "of amount", "(sell − buy) ÷ midpoint", S(["FEE-01"])],
        ["Amount at which the commission reaches CNY 260", money(M.COMM_CAP_AT), "USD", "260 ÷ (0.001 × midpoint)", S(["FEE-02", "FEE-01"])],
        ["Fixed charges per wire above that amount", money(M.FIXED_AT_CAP), "USD", "(260 + 150) ÷ midpoint + 25 + 15", S(["FEE-02", "FEE-09"])],
    ]
    sens = []
    one = M.many_wires(D(400000), 1)
    for n in (1, 2, 4, 8):
        t = M.many_wires(D(400000), n)
        sens.append([str(n), money0(D(400000) / n), money(t), money(t - one), S(["FEE-01", "FEE-02", "FEE-09"])])
    wq = []
    for amt, fee, sid, _, _ in C.WISE_QUOTES:
        usd_eq = amt / M.MID
        bank = M.boc_wire(usd_eq)
        bank_before = bank["fx"] + bank["fees"] + bank["addon"]
        wq.append([cny(amt, 0), money(usd_eq), cny(fee), pct(fee / amt), money(fee / M.MID), money(bank_before),
                   "Wise" if fee / M.MID < bank_before else "Bank wire", S([sid, "FEE-01", "FEE-02"]) + " " + F(["F04"])])
    lad = '<div class="grid">' + "".join(
        '<a class="card" href="ladder-%s.html"><b>%s</b><span>%s</span></a>' % (m["id"], m["id"], e(m["name"]))
        for m in C.METHODS if m["model"]) + "</div>"
    formula = ('<div class="formula"><b>Bank of China wire, one transfer of A dollars</b><br>'
               "exchange margin = A × (%s − %s) ÷ %s<br>"
               "commission = min(260, max(50, 0.001 × A × %s)) CNY<br>"
               "cable = 150 CNY · full-amount fee = $25 · receiving fee = $15<br>"
               "total = exchange margin + (commission + cable) ÷ %s + 25 + 15</div>") % (
        format(M.ASK, "f"), format(M.MID, "f"), format(M.MID, "f"), format(M.MID, "f"), format(M.MID, "f"))
    body = ("<h2>Compare methods</h2>" + glance_table() +
            '<p class="note">“+ blank” marks a cost with no published figure. Nothing is estimated to fill it.</p>'
            "<h2>Full ladders, $10,000 to $400,000</h2>" + lad +
            '<p class="note">All rows are also in <a href="data/costs.csv">costs.csv</a> and <a href="data/costs.json">costs.json</a>.</p>'
            "<h2>How the total is computed</h2>" + formula +
            "<h2>One wire or several</h2>" +
            table(["Wires", "Each wire", "Total on $400,000", "Extra over one wire", "Sources"], sens, cls="num", right=(0, 1, 2, 3)) +
            "<h2>Wise quotes against the bank wire</h2>" +
            table(["CNY sent", "USD at midpoint", "Wise fee", "Fee rate", "Wise fee in USD", "Bank wire before US receiving fee", "Cheaper", "Sources"],
                  wq, cls="num", right=(0, 1, 2, 3, 4, 5)) +
            '<p class="note">Both columns leave out the US receiving fee: Chase publishes $15 for incoming wires, and whether a bank charges for '
            "Wise's local payout was not checked.</p>"
            "<h2>Inputs</h2>" +
            table(["Input", "Value", "Unit", "Text found in the source", "Source"], prm) +
            "<h2>Derived values</h2>" +
            table(["Value", "Result", "Unit", "Formula", "Source of inputs"], [[e(r[0]), r[1], e(r[2]), e(r[3]), r[4]] for r in derived]))
    page("costs.html", "Costs from $10,000 to $400,000",
         "What each method costs at every $10,000 step. A total is shown only when every input is a published figure.", body)
    for m in C.METHODS:
        if not m["model"]:
            continue
        b = ('<p class="note">%s %s</p><p class="note">%s</p>' % (badge(m["verdict"]), e(m["cap"]), e(LADDER_NOTE[m["model"]])) +
             ladder_table(m) +
             '<p class="note"><a href="methods.html#%s">Method details</a> · <a href="steps.html#%s">Steps</a> · '
             '<a href="costs.html">All methods</a> · %s</p>' % (m["id"], m["id"], F(m["flags"])))
        page("ladder-%s.html" % m["id"], "%s cost ladder" % m["id"], e(m["name"]) + ".", b)


def p_breakdown():
    amts = [D(10000), D(100000), D(400000)]

    def comp(fn):
        return [money(fn(a)) for a in amts]
    rows = [
        ["Exchange margin", "A × (sell − midpoint) ÷ midpoint"] + comp(lambda a: a * M.ONE_WAY) + [S(["FEE-01"]) + " " + F(["F19"])],
        ["Commission", "0.1% of A, CNY 50 to CNY 260"] + comp(lambda a: M.boc_comm_cny(a) / M.MID) + [S(["FEE-02"]) + " " + F(["F17"])],
        ["Cable fee", "CNY 150"] + comp(lambda a: M.P["boc_cable_cny"] / M.MID) + [S(["FEE-02"])],
        ["Full-amount arrival", "$25 per wire"] + comp(lambda a: M.P["boc_full_arrival_usd"]) + [S(["FEE-02"])],
        ["US receiving fee", "$15 at Chase"] + comp(lambda a: M.P["chase_incoming_usd"]) + [S(["FEE-09"]) + " " + F(["F03"])],
        ["<b>Total</b>", "sum"] + ["<b>%s</b>" % money(at("M01", a)["total"]) for a in amts] + [S(["FEE-01", "FEE-02", "FEE-09"])],
        ["Share of the amount", "total ÷ A"] + [pct(at("M01", a)["pct"]) for a in amts] + [S(["FEE-01", "FEE-02", "FEE-09"])],
    ]
    t1 = table(["Component", "Formula", "$10,000", "$100,000", "$400,000", "Sources"], rows, cls="num", right=(2, 3, 4))
    rows = []
    for m in C.METHODS:
        if not m["model"]:
            continue
        rows.append(['%s %s' % (mlink(m), e(m["name"])), e(m["cn_tax"]), e(m["us"]), S(m["src"])])
    t2 = table(["Method", "China tax the route adds", "US side", "Sources"], rows)
    fines = []
    for a in amts:
        fines.append([money0(a), money0(a * D("0.30")), money0(a), money0(a * D("0.20")), S(["CN-FX-03"])])
    t3 = table(["Amount involved", "Fine ceiling, ordinary case (30%)", "Ceiling, serious case (100%)", "Unlawful cash carrying (20%)", "Source"],
               fines, cls="num", right=(0, 1, 2, 3))
    t4 = table(["Report", "When it applies", "Due", "Penalty", "Sources"],
               [[e(r[0]), e(r[1]), e(r[2]), e(r[3]), S(r[4]) + " " + F(r[5])] for r in C.US_REPORT])
    body = ("<h2>Where the money goes on a lawful wire</h2>"
            '<p class="note">Method M01, one Bank of China wire with full-amount arrival.</p>' + t1 +
            "<h2>Tax each route adds</h2>" + t2 +
            "<h2>China: exposure if the rules are broken</h2>"
            '<p class="note">Ceilings computed from the percentages in the Regulation. Confiscation of gains and criminal liability come on top.</p>' + t3 +
            '<p class="note">Details by scheme are on <a href="prohibited.html">Prohibited schemes</a>.</p>'
            "<h2>United States: reporting penalties</h2>" + t4)
    page("breakdown.html", "Cost and penalty breakdown",
         "What you lose on a lawful transfer, component by component, and what is at stake if a rule is broken.", body)


def p_tax():
    t = table(["Type of income", "China tax", "What it means for the transfer", "Sources"],
              [[e(r[0]), e(r[1]), e(r[2]), S(r[3]) + " " + F(r[4])] for r in C.CN_TAX])
    page("china-tax.html", "China tax by type of income",
         "Converting and remitting is not itself taxed. The tax depends on what the RMB is: wages, interest, dividends, sale proceeds or an inheritance.",
         t + '<p class="note">Residence for China tax: domicile in China, or 183 days or more in the tax year. %s</p>' % S(["CN-TAX-04"]))
    t1 = table(["Item", "US treatment", "Detail", "Sources"],
               [[e(r[0]), e(r[1]), e(r[2]), S(r[3]) + " " + F(r[4])] for r in C.US_TAX])
    t2 = table(["Report", "When it applies", "Due", "Penalty", "Sources"],
               [[e(r[0]), e(r[1]), e(r[2]), e(r[3]), S(r[4]) + " " + F(r[5])] for r in C.US_REPORT])
    page("us-tax.html", "US tax and reporting",
         "The transfer is not taxed. The income is, and the foreign account and large foreign gifts must be reported.",
         "<h2>Tax</h2>" + t1 + "<h2>Reports</h2>" + t2)


def p_prohibited():
    t = table(["Scheme", "What the rule says", "Consequence", "Sources"],
              [(r[0], ["<b>%s</b> %s" % (r[0], e(r[1])), e(r[2]), e(r[3]), S(r[4])]) for r in C.PROHIBITED])
    page("prohibited.html", "Prohibited schemes",
         "Listed so they can be recognised and refused. No steps are given for any of them.",
         t + '<p class="note">Fine ceilings in dollars are on <a href="breakdown.html">Cost and penalty breakdown</a>.</p>')


def p_review():
    st = AUDIT["stats"]
    sha = AUDIT["scanned_commit"]
    pats = AUDIT["patterns"]
    adjud = {"staging": ["CN-FX-04"], "staging_cancelled": ["CN-FX-04"], "fbar_adjusted": ["US-03"], "fbar_statutory": ["US-03"],
             "crypto_237": ["CN-FX-09"], "crypto_42": ["CN-FX-09"], "div_2026_27": ["CN-TAX-05"], "div_1994_20": ["CN-TAX-05"],
             "spread_042": ["FEE-01"], "spread_021": ["FEE-01"]}
    rows = []
    for r in C.REVIEW:
        if not r[4]:
            continue
        n = pats[r[2]]["total_lines"] if r[2] else None
        where = ", ".join("%s %d" % (k, v) for k, v in sorted(pats[r[2]]["by_area"].items())) if r[2] else "–"
        rows.append((r[0], ["<b>%s</b> %s" % (r[0], e(r[1])), e(r[3]), ("%d lines" % n) if n is not None else "–", e(where), S(r[4])]))
    t1 = table(["Finding", "Adjudication", "Lines matched", "Where", "Official source"], rows)
    proc = "".join("<li><b>%s</b> %s. %s</li>" % (r[0], e(r[1]), e(r[3])) for r in C.REVIEW if not r[4])
    rows = []
    for k in sorted(pats):
        h = pats[k]
        ex = "".join('<li><a href="%s%s/%s#L%d" rel="noopener"><code>%s:%d</code></a></li>' % (
            REPO_BLOB, sha, e(x["file"]), x["line"], e(x["file"]), x["line"]) for x in h["examples"][:6])
        rows.append([e(h["description"]), "<code>%s</code>" % e(h["regex"]), str(h["total_lines"]),
                     e(", ".join("%s %d" % (a, n) for a, n in sorted(h["by_area"].items()))),
                     "<details><summary>examples</summary><ul class=\"pc\">%s</ul></details>" % ex if ex else "–", S(adjud[k])])
    t2 = table(["Pattern", "Search expression", "Lines", "By directory", "Examples", "Adjudicating source"], rows)
    areas = ", ".join("%s %s" % (e(k), format(v, ",")) for k, v in sorted(AUDIT["lines_by_area"].items()))
    body = ('<div class="grid"><div class="kpi"><b>%s</b><span>tracked files read</span></div>'
            '<div class="kpi"><b>%s</b><span>lines scanned</span></div>'
            '<div class="kpi"><b>%d</b><span>findings</span></div>'
            '<div class="kpi"><b>%s</b><span>commit scanned</span></div></div>'
            "<h2>Findings</h2>%s<h2>Process irregularities</h2><ul>%s</ul>"
            "<h2>Line counts behind the findings</h2>"
            '<p class="note">Every tracked file outside this directory was read line by line with the expressions below. A match is a line to look at, '
            "not a verdict: some matches are audit notes that already correct the error.</p>%s"
            '<p class="note">Lines scanned by top-level directory: %s.</p>') % (
        format(st["text_files"], ","), format(st["lines"], ","), len(C.REVIEW), sha[:7], t1, proc, t2, areas)
    page("review.html", "Repository review",
         "What a line-by-line read of the earlier editions turned up, checked against the official text.", body)


def p_flagged():
    affects = {}
    for m in C.METHODS:
        for f in m["flags"]:
            affects.setdefault(f, []).append(m["id"])
    rows = []
    for fid, title, why, src in C.FLAGS:
        aff = " ".join(mlink(METH[x]) for x in affects.get(fid, [])) or "–"
        rows.append((fid, ["<b>%s</b>" % fid, e(title), e(why), aff, S(src)]))
    page("flagged.html", "Flagged for review",
         "Everything that could not be confirmed from an official page in this session. These cells are blank on the site; nothing was filled in.",
         table(["ID", "Item", "Why it is flagged", "Methods affected", "Sources to check"], rows))


def p_sources():
    rows = []
    for sid in sorted(EV):
        s = EV[sid]
        quotes = "".join("<blockquote><b>%s</b> %s</blockquote>" % (e(x["loc"]), e(x["text"])) for x in s["quotes"])
        kind = "Government or regulator" if s["kind"] == "official" else "Provider's own page"
        if s.get("paraphrase_only"):
            kind += " (not read verbatim)"
        rows.append((sid, ["<b>%s</b>" % sid, "%s<br><span class=\"note\">%s%s</span>" % (e(s["title"]), e(s["issuer"]), (" · " + e(s["doc_no"])) if s["doc_no"] else ""),
                           e(kind), e(s["retrieval"]),
                           "<details><summary>%d quoted passages</summary>%s</details>" % (len(s["quotes"]), quotes),
                           '<a class="src" href="%s" rel="noopener">open page</a>' % e(s["url"])]))
    n_q = sum(len(s["quotes"]) for s in EV.values())
    page("sources.html", "Sources",
         "%d pages read on 10 November 2026, with the %d passages quoted from them. Government and regulator pages support the rules; a provider's own page supports only that provider's prices and terms." % (len(EV), n_q),
         table(["ID", "Source", "Type", "How it was read", "Quoted text", "Link"], rows))


def p_method():
    reqs = "".join('<li><b>%s.</b> <a href="%s">%s</a></li>' % (e(r[0]), r[1], e(r[2])) for r in C.REQS)
    body = (
        "<h2>How a number gets onto this site</h2><ol>"
        "<li>An official page is read and the relevant passage is stored verbatim in <code>research/evidence_*.json</code>.</li>"
        "<li>Each model input names the stored passage and the exact text that must appear in it. The build stops if the text is missing.</li>"
        "<li>Totals are plain arithmetic on those inputs, shown on <a href=\"costs.html\">Costs</a>. The exchange margin is measured against the midpoint of the bank's own buying and selling rates.</li>"
        "<li>If any input of a total has no published figure, the total is left blank and the row links to a flag. Nothing is estimated or interpolated.</li>"
        "<li>A separate script recomputes every row with exact fractions, checks every link and anchor, and checks that every table row carries a source link.</li></ol>"
        "<h2>What the totals include and leave out</h2><ul>"
        "<li>Included: exchange margin, the sending bank's commission and cable fee, the full-amount arrival fee, and Chase's published incoming-wire fee.</li>"
        "<li>Left out: the cost of obtaining documents, travel, and anything your own US bank charges beyond the Chase figure.</li>"
        "<li>Tax is shown separately because it depends on what the money is, not on how it is sent.</li></ul>"
        "<h2>Limits</h2><ul>"
        "<li>The exchange board is a snapshot stamped 2026/11/10 07:32:39 and the bank says the executed rate governs.</li>"
        "<li>Eight sources were read as official-domain text returned by a search tool rather than opened directly; they are listed in flag F21.</li>"
        "<li>Banks decide which documents satisfy them. A rule that allows a transfer does not guarantee a branch will process it.</li>"
        "<li>This is general information, not legal or tax advice.</li></ul>"
        "<h2>The brief, item by item</h2><ul>%s</ul>"
        "<h2>Rebuild and verify</h2>"
        "<p><code>python3 playbook-d25b40f7/build/build.py</code> then <code>python3 playbook-d25b40f7/build/verify.py</code>. "
        "Standard library only. Data exports: <a href=\"data/costs.csv\">costs.csv</a>, <a href=\"data/costs.json\">costs.json</a>, "
        "<a href=\"data/methods.json\">methods.json</a>, <a href=\"data/parameters.json\">parameters.json</a>, "
        "<a href=\"data/flags.json\">flags.json</a>, <a href=\"data/sources.json\">sources.json</a>, <a href=\"data/repo_audit.json\">repo_audit.json</a>.</p>"
        "<h2>Coordination</h2>"
        "<p>Built by session <code>%s</code> in its own directory. It edits no other edition. The claim, log and release record are in "
        "<a href=\"%s/blob/main/COORDINATION.md\" rel=\"noopener\">COORDINATION.md</a>.</p>") % (reqs, C.SESSION, C.REPO)
    page("methodology.html", "Method", "How the figures are produced, what they leave out, and how to check them.", body)


# ---------- data exports
def ds(x, dp=2):
    return None if x is None else format(q(x, dp), "f")


def exports():
    rows = []
    for m in C.METHODS:
        if not m["model"]:
            continue
        for r in LADDERS[m["id"]]:
            src = list(MODEL_SRC[m["model"]]) + ([r["wise_src"]] if "wise_src" in r else [])
            tax = r.get("tax")
            rows.append({"method_id": m["id"], "method": m["name"], "model": m["model"], "amount_usd": ds(r["amount"], 0),
                         "cny_to_buy": ds(r["cny"]) if m["model"] in WITH_CNY else None,
                         "exchange_margin_usd": ds(r["fx"]), "bank_fees_usd": ds(r["fees"]), "addon_usd": ds(r["addon"]),
                         "receiving_usd": ds(r["recv"]), "published_costs_usd": ds(r["known"]), "total_usd": ds(r["total"]),
                         "total_pct": ds(r["pct"] * 100, 4) if r["pct"] is not None else None,
                         "china_tax_usd": ds(tax), "deemed_tax_low_usd": ds(r.get("tax_low")), "deemed_tax_high_usd": ds(r.get("tax_high")),
                         "units": r["units"], "flags": r["flags"], "sources": src})
    files = {}
    files["data/costs.json"] = json.dumps({"as_of": C.AS_OF, "midpoint_cny_per_usd": format(M.MID, "f"), "rows": rows}, ensure_ascii=False, indent=1) + "\n"
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    keys = list(rows[0].keys())
    w.writerow(keys)
    for r in rows:
        w.writerow(["" if r[k] is None else (" ".join(r[k]) if isinstance(r[k], list) else r[k]) for k in keys])
    files["data/costs.csv"] = buf.getvalue()
    files["data/parameters.json"] = json.dumps(
        {k: {"value": format(v[0], "f"), "unit": v[1], "source": v[2], "text_in_source": v[3]} for k, v in C.PARAMS.items()},
        ensure_ascii=False, indent=1) + "\n"
    files["data/methods.json"] = json.dumps(
        [{k: ([{"step": s[0], "sources": s[1]} for s in v] if k == "steps" else v) for k, v in m.items()} for m in C.METHODS],
        ensure_ascii=False, indent=1) + "\n"
    files["data/flags.json"] = json.dumps([{"id": f[0], "item": f[1], "why": f[2], "sources": f[3]} for f in C.FLAGS], ensure_ascii=False, indent=1) + "\n"
    files["data/sources.json"] = json.dumps([EV[k] for k in sorted(EV)], ensure_ascii=False, indent=1) + "\n"
    files["data/wise_quotes.json"] = json.dumps(
        [{"cny_sent": format(a, "f"), "fee_cny": format(f, "f"), "source": s} for a, f, s, _, _ in C.WISE_QUOTES], indent=1) + "\n"
    return files


def main():
    validate()
    p_index(); p_summary(); p_methods(); p_steps(); p_costs(); p_breakdown(); p_tax(); p_prohibited()
    p_review(); p_flagged(); p_sources(); p_method()
    files = exports()
    files.update(PAGES)
    for stale in glob.glob(os.path.join(OUT, "ladder-*.html")):
        if os.path.basename(stale) not in files:
            os.remove(stale)
    for name, text in sorted(files.items()):
        path = os.path.join(OUT, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    print("built %d pages, %d data files, %d sources, %d methods, %d flags" % (
        len(PAGES), len(files) - len(PAGES), len(EV), len(C.METHODS), len(C.FLAGS)))


if __name__ == "__main__":
    main()
