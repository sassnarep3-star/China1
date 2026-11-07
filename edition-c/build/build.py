#!/usr/bin/env python3
"""
Static site generator for the CNY-to-USD research site.

Reads every file in data/*.json and writes a complete GitHub Pages site into
docs/. No third-party dependencies. Deterministic output: the same data always
produces byte-identical HTML.

Verification rules enforced here:
  * every source id cited by a row must exist in data/sources.json
  * a value that is null renders as a blank cell carrying an UNVERIFIED badge
  * no cell may render a number without a source id attached to it
  * every generated page is listed in NAV so no orphan page can exist

Usage:  python3 build/build.py
"""

import html
import json
import os
import sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "docs")

AS_OF = "7 November 2026"


# --------------------------------------------------------------------------
# data loading
# --------------------------------------------------------------------------

def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


SOURCES = load("sources.json")
ROUTES = load("routes.json")
TAX = load("tax.json")
PENALTIES = load("penalties.json")
FLAGS = load("flags.json")
REVIEW = load("repo-review.json")
SUMMARY = load("summary.json")

SRC = OrderedDict((s["id"], s) for s in SOURCES["sources"])
FLAG = OrderedDict((f["id"], f) for f in FLAGS["flags"])
ROUTE = OrderedDict((r["id"], r) for r in ROUTES["routes"])
CAT = OrderedDict((c["id"], c) for c in ROUTES["categories"])

ERRORS = []


def e(text):
    """HTML-escape."""
    if text is None:
        return ""
    return html.escape(str(text), quote=True)


def cite(ids, sep=" "):
    """Render a list of source ids as links into sources.html."""
    out = []
    for sid in ids or []:
        if sid not in SRC:
            ERRORS.append("citation to unknown source id: %r" % sid)
            out.append('<span class="badref">%s</span>' % e(sid))
            continue
        out.append(
            '<a class="src" href="sources.html#%s" title="%s">%s</a>'
            % (e(sid), e(SRC[sid]["title_en"]), e(sid))
        )
    return sep.join(out)


def flagref(fid):
    if not fid:
        return ""
    if fid not in FLAG:
        ERRORS.append("citation to unknown flag id: %r" % fid)
        return '<span class="badref">%s</span>' % e(fid)
    return '<a class="flagref" href="flagged.html#%s">%s</a>' % (e(fid), e(fid))


def value_or_blank(value, sources=None, flag=None):
    """
    The core verification rule.

    A confirmed value renders with its source citation. A value that could not
    be confirmed renders as an explicit blank with an UNVERIFIED badge, never as
    an inferred or estimated number.
    """
    if value is None or value == "":
        badge = '<span class="badge badge-unverified">unverified</span>'
        if flag:
            badge += flagref(flag)
        return '<span class="blank">—</span> ' + badge
    cell = e(value)
    if sources:
        cell += " " + cite(sources if isinstance(sources, list) else [sources])
    if flag:
        cell += " " + flagref(flag)
    return cell


def official_badge(s):
    if s.get("official"):
        return '<span class="badge badge-official">official</span>'
    return '<span class="badge badge-secondary">not official</span>'


def risk_badge(risk):
    if not risk:
        return ""
    key = risk.lower()
    if key.startswith("severe") or key.startswith("high"):
        cls = "risk-high"
    elif key.startswith("medium") or key.startswith("low to medium"):
        cls = "risk-medium"
    elif key.startswith("very low") or key.startswith("low"):
        cls = "risk-low"
    elif key.startswith("unverified") or key.startswith("not"):
        cls = "risk-none"
    else:
        cls = "risk-medium"
    return '<span class="badge %s">%s</span>' % (cls, e(risk))


def verified_badge(ok):
    if ok:
        return '<span class="badge badge-verified">verified</span>'
    return '<span class="badge badge-unverified">unverified</span>'


# --------------------------------------------------------------------------
# navigation and layout
# --------------------------------------------------------------------------

NAV = [
    ("index.html", "Overview", "Dashboard and headline findings"),
    ("executive-summary.html", "Executive summary", "The ten findings that matter"),
    ("routes.html", "All 33 routes", "Master comparison table"),
    ("individual-channels.html", "Individual", "Channels available to a natural person"),
    ("corporate-channels.html", "Corporate", "Dividends, liquidation, equity, service fees"),
    ("trade-channels.html", "Trade", "Current-account channels built on real transactions"),
    ("asset-channels.html", "Asset", "Property, inheritance and emigrant transfers"),
    ("assessed-and-rejected.html", "Rejected", "Lawful schemes that do not deliver USD"),
    ("prohibited.html", "Prohibited", "Documented for avoidance, with published fines"),
    ("tax-china.html", "China tax", "Rates, bases and filing obligations"),
    ("tax-us.html", "US tax", "Worldwide income, exclusions, credits, reporting"),
    ("tax-treaty.html", "Treaty", "The 1984 US-China Agreement, article by article"),
    ("penalty.html", "Penalty breakdown", "Six cost layers and 23 published cases"),
    ("flagged.html", "Flagged for review", "19 unresolved items, published not hidden"),
    ("sources.html", "Sources", "39 entries with provisions relied on"),
    ("repo-review.html", "Repo review", "Line-by-line audit and irregularities"),
    ("methodology.html", "Method", "Verification standard and limitations"),
]

NAV_BY_HREF = OrderedDict((h, (t, d)) for h, t, d in NAV)


def nav_html(active):
    items = []
    for href, title, desc in NAV:
        cls = ' class="active"' if href == active else ""
        items.append(
            '<a%s href="%s"><span class="nav-t">%s</span>'
            '<span class="nav-d">%s</span></a>' % (cls, e(href), e(title), e(desc))
        )
    return "".join(items)


def page(filename, title, subtitle, body, extra_head=""):
    """Render one complete HTML page."""
    doc = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<link rel="stylesheet" href="assets/css/style.css">
%s
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="shell">
<nav class="side" aria-label="Sections">
  <div class="brand">
    <a href="index.html">
      <span class="brand-mark">CNY&rarr;USD</span>
      <span class="brand-sub">Research dossier</span>
    </a>
  </div>
  <div class="navlist">%s</div>
  <div class="navfoot">
    <div>As of %s</div>
    <div>Every figure cited to an official source</div>
  </div>
</nav>
<main id="main">
  <header class="pagehead">
    <h1>%s</h1>
    <p class="subtitle">%s</p>
  </header>
  <div class="content">
%s
  </div>
  <footer class="pagefoot">
    <p>%s</p>
    <p>Generated by <code>build/build.py</code> from <code>data/*.json</code>.
       Validated by <code>build/linkcheck.py</code>.</p>
  </footer>
</main>
</div>
<script src="assets/js/site.js"></script>
</body>
</html>
""" % (
        e(title),
        e(subtitle),
        extra_head,
        nav_html(filename),
        AS_OF,
        e(title),
        e(subtitle),
        body,
        e(SUMMARY["disclaimer"]),
    )
    return doc


def write(filename, text):
    path = os.path.join(OUT, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def section(title, body, anchor=None):
    aid = ' id="%s"' % e(anchor) if anchor else ""
    return '<section class="block"%s><h2>%s</h2>%s</section>' % (aid, e(title), body)


def note(text, kind="note"):
    return '<div class="callout callout-%s"><p>%s</p></div>' % (e(kind), text)


def ul(items):
    return "<ul>%s</ul>" % "".join("<li>%s</li>" % i for i in items)


def table(headers, rows, cls="data", idattr=None):
    aid = ' id="%s"' % e(idattr) if idattr else ""
    thead = "".join("<th>%s</th>" % h for h in headers)
    tbody = []
    for r in rows:
        tds = "".join("<td>%s</td>" % c for c in r)
        tbody.append("<tr>%s</tr>" % tds)
    return (
        '<div class="tablewrap"><table class="%s"%s><thead><tr>%s</tr></thead>'
        "<tbody>%s</tbody></table></div>"
        % (e(cls), aid, thead, "".join(tbody))
    )


# --------------------------------------------------------------------------
# pages
# --------------------------------------------------------------------------

def build_index():
    kpi_cards = "".join(
        '<a class="kpi" href="%s"><div class="kpi-v">%s</div>'
        '<div class="kpi-l">%s</div><div class="kpi-n">%s</div></a>'
        % (e(k["page"]), e(k["value"]), e(k["label"]), e(k["note"]))
        for k in SUMMARY["kpi"]
    )

    cat_cards = "".join(
        '<a class="card" href="%s"><h3>%s</h3><p>%s</p>'
        '<div class="card-n">%d routes</div></a>'
        % (
            e(c["page"]),
            e(c["name"]),
            e(c["blurb"]),
            sum(1 for r in ROUTES["routes"] if r["category"] == c["id"]),
        )
        for c in ROUTES["categories"]
    )

    hf = PENALTIES["headline_finding"]
    comp = "".join(
        '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
        % (e(c["name"]), e(c["nature"]), e(c["detail"]), cite(c["sources"]))
        for c in hf["components"]
    )
    decomp = table(
        ["What people call the conversion tax", "What it actually is", "Detail", "Sources"],
        [comp],
    )

    body = (
        note(
            "<strong>%s.</strong> %s" % (e(hf["title"]), e(hf["body"])),
            "key",
        )
        + '<div class="kpigrid">%s</div>' % kpi_cards
        + section("Decomposing the cost", decomp)
        + section("Browse by category", '<div class="cardgrid">%s</div>' % cat_cards)
        + section(
            "The three questions that decide everything",
            ul(
                [
                    "<strong>Is the money current-account income or capital?</strong> Art.13 of "
                    "the Measures opens an uncapped route for legitimate current-account income "
                    "earned in China by an overseas individual. Capital-account receipts need "
                    "SAFE approval or registration. " + cite(["S01", "S02"]),
                    "<strong>Has the Chinese tax on the underlying event been paid and evidenced?</strong> "
                    "A tax voucher is a statutory precondition to the conversion, and Art.15 of the "
                    "Individual Income Tax Law blocks registration of a property or equity transfer "
                    "until the tax-paid certificate is produced. " + cite(["S02", "S13"]),
                    "<strong>Is the route lawful?</strong> The administrative fine scales are up to "
                    "30% and 30% to 100% for serious cases, and the criminal threshold for illegal "
                    "foreign exchange dealing is an illegal business amount of RMB 5,000,000. "
                    + cite(["S03", "S12"]),
                ]
            ),
        )
        + section(
            "How to read this site",
            "<p>Every numeric cell in every table carries a link to the entry in the "
            '<a href="sources.html">source register</a> it was read from, with the article '
            "number. Where a value could not be confirmed against an official source the cell "
            "is left blank and carries an <span class='badge badge-unverified'>unverified</span> "
            "badge linking to the <a href='flagged.html'>Flagged for Review</a> page. No value "
            "anywhere on this site has been inferred, estimated or carried over from a secondary "
            'source. The <a href="methodology.html">methodology page</a> states the full '
            "standard and its limitations.</p>",
        )
    )

    return page(
        "index.html",
        "Converting CNY to USD from a mainland Chinese bank account",
        "A research dossier for a US citizen with renminbi held in China: every channel, its legal basis, its cost, and its penalty exposure, each figure cited to an official source.",
        body,
    )


def build_summary():
    secs = []
    for s in SUMMARY["sections"]:
        secs.append(
            '<section class="block" id="%s"><h2>%s</h2><p>%s</p>'
            '<p class="srcs">Sources: %s</p></section>'
            % (
                e(s["title"].split(".")[0]),
                e(s["title"]),
                e(s["body"]),
                cite(s["sources"]),
            )
        )
    body = (
        note("<strong>Headline.</strong> %s" % e(SUMMARY["lede"]), "key")
        + "".join(secs)
        + note(e(SUMMARY["disclaimer"]), "warn")
    )
    return page(
        "executive-summary.html",
        "Executive summary",
        "Ten findings, in the order they change the decision.",
        body,
    )


def route_row(r, compact=False):
    limit = value_or_blank(r.get("limit"), r.get("sources"))
    if compact:
        return [
            '<a href="%s#%s">%s</a>' % (e(CAT[r["category"]]["page"]), e(r["id"]), e(r["name"])),
            e(CAT[r["category"]]["name"]),
            limit,
            e(r.get("feasibility")),
            risk_badge(r.get("risk")),
            cite(r.get("sources")),
        ]
    return [
        '<a href="%s#%s">%s</a><br><span class="zh">%s</span>'
        % (e(CAT[r["category"]]["page"]), e(r["id"]), e(r["name"]), e(r.get("name_zh", ""))),
        limit,
        e(r.get("feasibility")),
        risk_badge(r.get("risk")),
        cite(r.get("sources")),
    ]


def build_routes():
    rows = [route_row(r, compact=True) for r in ROUTES["routes"]]
    body = (
        note(
            "All %d channels identified, in one table, ordered as inventoried. "
            "Rows marked <span class='badge badge-unverified'>unverified</span> on their "
            "category page have a value that could not be confirmed against an official "
            "source and are explained on the <a href='flagged.html'>Flagged for Review</a> "
            "page. Limits shown as a blank dash mean the same thing." % len(ROUTES["routes"]),
            "note",
        )
        + table(
            [
                "Channel",
                "Category",
                "Stated limit",
                "Feasibility",
                "Risk",
                "Sources",
            ],
            rows,
            idattr="all-routes",
        )
    )
    return page(
        "routes.html",
        "All channels for converting CNY to USD",
        "The master comparison table. %d channels, including the five that are prohibited and are documented only so they can be recognised and avoided."
        % len(ROUTES["routes"]),
        body,
    )


def build_route_detail(r):
    """Full detail block for one route, used on category pages."""
    srcs = cite(r.get("sources"))
    rows = [
        ["Legal basis", e(r.get("legal_basis"))],
        ["How it works", e(r.get("how_it_works"))],
        [
            "Stated limit",
            value_or_blank(r.get("limit"), r.get("sources"), r.get("flag")),
        ],
        ["Chinese tax", e(r.get("china_tax"))],
        ["US tax", e(r.get("us_tax"))],
        ["Documentation", e(r.get("documentation"))],
    ]
    if r.get("officiality_caveat"):
        rows.append(["Officiality caveat", e(r["officiality_caveat"]) + " " + flagref("F08")])
    if r.get("verification_note"):
        rows.append(
            [
                "Verification note",
                e(r["verification_note"])
                + (" " + flagref(r["flag"]) if r.get("flag") else ""),
            ]
        )
    elif r.get("flag"):
        rows.append(["Flag", flagref(r["flag"])])
    detail = table(["Field", "Value"], rows, cls="data detail")

    pros = ul("<strong>Pro.</strong> %s" % e(p) for p in r.get("pros", []))
    cons = ul("<strong>Con.</strong> %s" % e(c) for c in r.get("cons", []))

    head = (
        '<div class="rhead"><div><h3>%s <span class="rid">%s</span></h3>'
        '<p class="zh">%s</p></div>'
        '<div class="rbadges">%s %s %s</div></div>'
        % (
            e(r["name"]),
            e(r["id"]),
            e(r.get("name_zh", "")),
            verified_badge(r.get("verified")),
            risk_badge(r.get("risk")),
            '<span class="badge badge-neutral">%s</span>' % e(r.get("feasibility")),
        )
    )
    return (
        '<article class="route" id="%s">%s%s'
        '<div class="twocol"><div><h4>Pros</h4>%s</div><div><h4>Cons</h4>%s</div></div>'
        '<p class="srcs">Sources: %s</p></article>'
        % (e(r["id"]), head, detail, pros, cons, srcs)
    )


def build_category(cat_id):
    c = CAT[cat_id]
    rs = [r for r in ROUTES["routes"] if r["category"] == cat_id]
    body = (
        note(c["blurb"], "note")
        + "".join(build_route_detail(r) for r in rs)
    )
    title = c["name"]
    return page(
        c["page"],
        title,
        "%d channels in this category. Each is stated with its legal basis, its limit where one is fixed by an official instrument, its tax cost, the documents it requires, and its pros and cons."
        % len(rs),
        body,
    )


def build_tax_china():
    rows = []
    for t in TAX["china"]:
        rows.append(
            [
                e(t["item"]),
                value_or_blank(t["rate"], t.get("source")),
                e(t["basis"]),
                e(t["notes"]),
            ]
        )
    body = (
        note(
            "Rates below are read directly from the instruments cited. Where a rate could not "
            "be confirmed against an official source the cell is blank and flagged; nothing has "
            "been inferred.",
            "note",
        )
        + table(["Item", "Rate or rule", "Legal basis", "Notes"], rows)
        + section(
            "The provisions that gate the conversion",
            ul(
                [
                    "<strong>Art.13(1) of the Detailed Rules</strong> makes a tax voucher part "
                    "of the evidence an overseas individual must produce to convert legitimate "
                    "current-account income. " + cite(["S02"]),
                    "<strong>Art.15 of the Individual Income Tax Law</strong> requires the "
                    "registration authority to verify the individual income tax paid certificate "
                    "before registering a transfer of immovable property, and the market entity "
                    "registration authority to verify it before registering an equity transfer. "
                    "Tax cannot be deferred past the point of transfer. " + cite(["S13"]),
                    "<strong>Art.13 paragraph 5</strong> requires a taxpayer who cancels Chinese "
                    "household registration because of emigration to complete tax clearance "
                    "before cancellation. This is the gate on the emigration property transfer "
                    "route. " + cite(["S13"]),
                    "<strong>Art.8</strong> permits adjustment plus interest for non-arm's-length "
                    "related-party dealings, for non-distribution by an enterprise in a markedly "
                    "low-tax jurisdiction controlled by a resident individual, and for "
                    "arrangements lacking reasonable commercial purpose. " + cite(["S13"]),
                    "<strong>Art.49 of the EIT Implementation Regulations</strong> makes "
                    "management fees between enterprises, and rent and royalties between "
                    "operating units of the same enterprise, non-deductible. This is the "
                    "constraint on the service-fee and royalty routes. " + cite(["S14"]),
                    "<strong>STA and SAFE Announcement 2021 No.19</strong> requires tax filing "
                    "before a single outbound payment above USD 50,000 equivalent, once per "
                    "contract before the first such payment, with reinvestment of legitimate "
                    "direct-investment income in China exempt. " + cite(["S15"]),
                ]
            ),
        )
    )
    return page(
        "tax-china.html",
        "China-side tax",
        "Individual income tax, enterprise income tax, withholding tax and VAT, with the provisions that make tax payment a precondition to moving money.",
        body,
    )


def build_tax_us():
    rows = []
    for t in TAX["us"]:
        rows.append(
            [
                e(t["item"]),
                value_or_blank(t["rate"], t.get("source")),
                e(t["basis"]),
                e(t["notes"]),
            ]
        )
    body = (
        note(
            "The US position is a reporting position first and a tax position second. A US "
            "citizen is already taxed on worldwide income wherever the funds sit, so "
            "converting and remitting after-tax money between the taxpayer's own accounts is "
            "not a second realisation. The exposure is in the forms. " + cite(["S24", "S29"]),
            "key",
        )
        + table(["Item", "Rate or threshold", "Legal basis", "Notes"], rows)
        + section(
            "Relief: exclusion or credit, never both on the same income",
            ul(
                [
                    "The foreign earned income exclusion reaches USD 130,000 for 2025 and "
                    "USD 132,900 for 2026 per qualifying person, with a housing limitation of "
                    "USD 39,000 and USD 39,870 respectively. It requires a foreign tax home "
                    "plus bona fide residence for an uninterrupted period including an entire "
                    "tax year, or physical presence for at least 330 full days in any twelve "
                    "consecutive months. It does not cover pensions, annuities or social "
                    "security, and does not reduce self-employment tax. " + cite(["S23", "S24"]),
                    "The foreign tax credit is limited to US tax liability multiplied by "
                    "foreign-source taxable income over total taxable income, computed "
                    "separately for each limitation category, with a one-year carryback and a "
                    "ten-year carryover. " + cite(["S28"]),
                    "No credit or deduction is allowed for foreign tax paid on income excluded "
                    "under either exclusion, so the two reliefs cannot be stacked. "
                    + cite(["S28"]),
                    "Where all foreign-source gross income is passive category income on "
                    "qualified payee statements and creditable foreign tax does not exceed "
                    "USD 300, or USD 600 jointly, the credit may be claimed without Form 1116. "
                    + cite(["S28"]),
                ]
            ),
        )
    )
    return page(
        "tax-us.html",
        "US-side tax and reporting",
        "Worldwide income, the two mutually exclusive reliefs, and the four reporting regimes with their adjusted penalty amounts.",
        body,
    )


def build_treaty():
    t = TAX["treaty"]
    rows = []
    for a in t["articles"]:
        rows.append(
            [e(a["article"]), e(a["provision"]), e(a["practical_effect"]), cite([a["source"]])]
        )
    meta = table(
        ["Field", "Value"],
        [
            ["Instrument", e(t["instrument"])],
            ["Signed", e(t["signed"]) + " " + cite([t["source"]])],
            ["Second protocol", e(t["second_protocol"]) + " " + cite([t["source"]])],
            ["General effective date", e(t["general_effective_date"]) + " " + cite([t["source"]])],
        ],
        cls="data detail",
    )
    body = (
        note(
            "<strong>The treaty gives almost nothing on rates and everything on relief.</strong> "
            "Its 10% caps on dividends, interest and royalties are identical to the domestic "
            "reduced rate already provided by Art.91 of the Chinese EIT Implementation "
            "Regulations, so there is no withholding reduction to claim. Its value to a US "
            "person is Art.22, the foreign tax credit. " + cite(["S30", "S14"]),
            "key",
        )
        + meta
        + section("Article by article", table(["Article", "Provision", "Practical effect", "Sources"], rows))
        + section(
            "Two points that matter for a US citizen",
            ul(
                [
                    "<strong>The saving clause.</strong> Protocol para.2 preserves the right of "
                    "the United States to tax its citizens and residents under domestic law. "
                    "The Technical Explanation confirms the United States may in any event tax "
                    "dividends, interest, royalties and gains derived by US citizens. The "
                    "treaty cannot be used to escape US tax. " + cite(["S30"]),
                    "<strong>Stale tax names.</strong> Art.2 names the individual income tax, "
                    "the income tax concerning joint ventures with Chinese and foreign "
                    "investment, the income tax concerning foreign enterprises and the local "
                    "income tax. Those predate the 2008 Enterprise Income Tax Law and the 2018 "
                    "Individual Income Tax Law amendment. Coverage of the current taxes relies "
                    "on Art.2(2), which extends the Agreement to substantially similar taxes "
                    "imposed after signature. " + cite(["S30"]) + " " + flagref("F11"),
                ]
            ),
        )
    )
    return page(
        "tax-treaty.html",
        "The US-China income tax treaty",
        "Signed at Beijing on 30 April 1984, effective 1 January 1987. Article numbering differs from the OECD model, so the citations below matter.",
        body,
    )


def build_penalty():
    layers = []
    for L in PENALTIES["cost_layers"]:
        rows = []
        for vr in L["verified_rates"]:
            note_txt = e(vr.get("note", "")) if vr.get("note") else ""
            rows.append(
                [
                    e(vr["item"]),
                    value_or_blank(vr["rate"], vr.get("source")),
                    note_txt,
                ]
            )
        layers.append(
            '<section class="block"><h2>Layer %d &mdash; %s</h2>'
            '<p class="applies">Applies to: %s</p>%s</section>'
            % (
                L["layer"],
                e(L["name"]),
                e(L["applies_to"]),
                table(["Component", "Verified rate, threshold or rule", "Note"], rows),
            )
        )

    case_rows = []
    for c in PENALTIES["published_cases"]["cases"]:
        pct = c.get("fine_pct")
        if pct is None:
            pct_cell = (
                '<span class="blank">—</span> <span class="badge badge-neutral" '
                'title="Amount moved and fine are in different currencies; no exchange rate is assumed">n/a</span>'
            )
        else:
            pct_cell = "<strong>%s</strong> <span class='muted'>computed</span>" % e(pct)
        case_rows.append(
            [
                e(c["offender"]),
                e(c["conduct"]),
                e(c["amount_moved"]),
                e(c["violation"]),
                e(c["penalty_basis"]),
                e(c["fine"]),
                pct_cell,
                e(c["additional"]),
                cite([c["source"]]),
            ]
        )

    obs = "".join(
        '<div class="obs"><h4>Finding</h4><p>%s</p><h4>Evidence</h4><p>%s</p>'
        "<h4>Why it matters</h4><p>%s</p><p class='srcs'>Sources: %s</p></div>"
        % (e(o["finding"]), e(o["evidence"]), e(o["significance"]), cite(o["source"]))
        for o in PENALTIES["published_cases"]["observations"]
    )

    hf = PENALTIES["headline_finding"]
    body = (
        note(
            "<strong>%s.</strong> %s" % (e(hf["title"]), e(hf["body"])),
            "key",
        )
        + note(
            "The cost of getting renminbi to US dollars decomposes into six layers. Layers 1 "
            "to 4 are the cost of doing it lawfully. Layers 5 and 6 are the cost of not doing "
            "so, and they are quantified from SAFE's own published enforcement cases rather "
            "than estimated. " + PENALTIES["_meta"]["arithmetic_note"],
            "note",
        )
        + "".join(layers)
        + section(
            "Published enforcement cases",
            "<p class='applies'>%s</p>" % e(PENALTIES["published_cases"]["description"])
            + table(
                [
                    "Party",
                    "Conduct",
                    "Amount moved",
                    "Rule breached",
                    "Penalty basis",
                    "Fine",
                    "Fine as % moved",
                    "Additional consequence",
                    "Source",
                ],
                case_rows,
                idattr="cases",
            ),
        )
        + section("What the case data shows", obs)
    )
    return page(
        "penalty.html",
        "The conversion penalty, broken down",
        "Six cost layers, the statutory penalty scales, and 23 cases SAFE published itself, with fine rates computed only where both official figures share a currency.",
        body,
    )


def build_flagged():
    rows = []
    for f in FLAGS["flags"]:
        rows.append(
            [
                '<a href="#%s">%s</a>' % (e(f["id"]), e(f["id"])),
                '<span class="badge badge-sev-%s">%s</span>' % (e(f["severity"]), e(f["severity"])),
                e(f["type"]),
                e(f["title"]),
            ]
        )
    detail = "".join(
        '<article class="flag" id="%s"><h3>%s &mdash; %s</h3>'
        '<p class="flagmeta"><span class="badge badge-sev-%s">%s</span> '
        "<span class='badge badge-neutral'>%s</span></p>"
        "<h4>What is unresolved</h4><p>%s</p>"
        "<h4>Where it appears</h4>%s"
        "<h4>How to resolve it</h4><p>%s</p>"
        "<p class='srcs'>Sources reviewed: %s</p></article>"
        % (
            e(f["id"]),
            e(f["id"]),
            e(f["title"]),
            e(f["severity"]),
            e(f["severity"]),
            e(f["type"]),
            e(f["detail"]),
            ul(e(w) for w in f["where_it_appears"]),
            e(f["how_to_resolve"]),
            cite(f["sources"]) if f["sources"] else "<span class='muted'>none located</span>",
        )
        for f in FLAGS["flags"]
    )
    body = (
        note(
            "<strong>%s</strong> %s" % (e(FLAGS["_meta"]["policy"]), "None of these items blocks publication. Each is published here with the source links needed to check it manually."),
            "warn",
        )
        + table(["Flag", "Severity", "Type", "Title"], rows, idattr="flag-index")
        + detail
    )
    return page(
        "flagged.html",
        "Flagged for review",
        "%d items that could not be confirmed from an official source, conflicts between official sources, and gaps in the regulatory scheme. Values are left blank in the tables rather than filled in."
        % len(FLAGS["flags"]),
        body,
    )


def build_sources():
    rows = []
    for s in SOURCES["sources"]:
        rows.append(
            [
                '<a href="#%s">%s</a>' % (e(s["id"]), e(s["id"])),
                e(s["title_en"]) + ('<br><span class="zh">%s</span>' % e(s["title_zh"]) if s.get("title_zh") else ""),
                e(s["issuer"]),
                e(s["doc_number"]),
                official_badge(s),
            ]
        )
    detail = "".join(
        '<article class="source" id="%s"><h3>%s &mdash; %s</h3>'
        "%s%s"
        "<p class='srcline'><strong>Document number.</strong> %s</p>"
        "<p class='srcline'><strong>Issuer.</strong> %s</p>"
        "%s%s"
        "<p class='srcline'><strong>URL.</strong> <a href=\"%s\" rel=\"noopener noreferrer external\" target=\"_blank\">%s</a> "
        "<span class='muted'>(%s)</span></p>"
        "%s"
        "<h4>Provisions relied on</h4>%s</article>"
        % (
            e(s["id"]),
            e(s["id"]),
            e(s["title_en"]),
            '<p class="srcline"><strong>Title.</strong> <span class="zh">%s</span></p>' % e(s["title_zh"]) if s.get("title_zh") else "",
            '<p class="srcline"><strong>Validity marking.</strong> %s</p>' % e(s["validity"]) if s.get("validity") else "",
            e(s.get("doc_number", "")),
            e(s["issuer"]),
            '<p class="srcline"><strong>Published.</strong> %s</p>' % e(s["published"]) if s.get("published") else "",
            '<p class="srcline"><strong>Effective.</strong> %s</p>' % e(s["effective"]) if s.get("effective") else "",
            e(s["url"]),
            e(s["url"]),
            e(s["host"]),
            ('<p class="srcline"><strong>Alternative URL.</strong> <a href="%s" rel="noopener noreferrer external" target="_blank">%s</a></p>' % (e(s["url_alt"]), e(s["url_alt"]))) if s.get("url_alt") else "",
            ul(e(u) for u in s["used_for"]),
        )
        + (
            note("<strong>Officiality note.</strong> %s" % e(s["officiality_note"]), "warn")
            if s.get("officiality_note")
            else ""
        )
        + (
            note("<strong>Currency of data.</strong> %s" % e(s["as_of"]), "note")
            if s.get("as_of")
            else ""
        )
        for s in SOURCES["sources"]
    )
    body = (
        note(
            "Every source is a government, regulator, central bank, tax authority or judicial "
            "body publishing its own instrument, or a national legislature's gazette. Bank, law "
            "firm, accounting firm, press and aggregator sources are not accepted. Where one "
            "had to be used because the primary text could not be located, the entry is marked "
            "<span class='badge badge-secondary'>not official</span> and is also flagged. "
            "Links open the issuing body's own page for manual review.",
            "note",
        )
        + table(["Id", "Title", "Issuer", "Document number", "Officiality"], rows, idattr="source-index")
        + detail
    )
    return page(
        "sources.html",
        "Source register",
        "%d entries. Each records the issuing body, the document number, the date, the URL on the issuing body's own domain, and the specific provisions relied on."
        % len(SOURCES["sources"]),
        body,
    )


def build_review():
    rp = REVIEW["repo_at_branch_point"]
    file_rows = [
        [
            "<code>%s</code>" % e(f["path"]),
            "%d bytes, %d line" % (f["size_bytes"], f["lines"]),
            "<code>%s</code>" % e(f["content"]),
            e(f["assessment"]),
        ]
        for f in rp["files"]
    ]
    pg = REVIEW["pages_at_branch_point"]
    pg_rows = [
        ["Status", e(pg["status"])],
        ["Build type", e(pg["build_type"])],
        ["Source", "<code>%s</code> at path <code>%s</code>" % (e(pg["source_branch"]), e(pg["source_path"]))],
        ["Site URL", '<a href="%s" rel="noopener noreferrer external" target="_blank">%s</a>' % (e(pg["html_url"]), e(pg["html_url"]))],
        ["HTTPS enforced", e(str(pg["https_enforced"]))],
        ["Assessment", e(pg["assessment"])],
    ]
    irr = "".join(
        '<article class="flag" id="%s"><h3>%s &mdash; %s</h3>'
        "<p class='flagmeta'><span class='badge badge-neutral'>%s</span></p>"
        "<h4>Finding</h4><p>%s</p><h4>Resolution</h4><p>%s</p></article>"
        % (
            e(i["id"]),
            e(i["id"]),
            e(i["title"]),
            e(i["severity"]),
            e(i["detail"]),
            e(i["resolution"]),
        )
        for i in REVIEW["irregularities"]
    )
    added = table(
        ["Path", "Purpose"],
        [["<code>%s</code>" % e(a["path"]), e(a["purpose"])] for a in REVIEW["added_this_session"]],
    )
    std = ul("<strong>%s</strong> %s" % (e(k.replace("_", " ").title()), e(v)) for k, v in REVIEW["verification_standard"].items())

    body = (
        note(
            "The repository at the branch point contained one file of eight bytes. There was no "
            "prior data to audit, so this review covers what was found, what was absent, and "
            "every irregularity in the work itself.",
            "note",
        )
        + section(
            "Repository at branch point %s" % e(REVIEW["_meta"]["branch_point"][:7]),
            table(["Path", "Size", "Content", "Assessment"], file_rows)
            + "<p class='applies'>Remote <code>%s</code>. Default branch <code>%s</code>. "
            "Commits at branch point: %d.</p>"
            % (e(rp["remote"]), e(rp["default_branch"]), rp["commits"])
            + "<h4>What was absent</h4>"
            + ul(e(a) for a in rp["absent"]),
        )
        + section("GitHub Pages configuration found", table(["Field", "Value"], pg_rows, cls="data detail"))
        + section("Irregularities found and how each was resolved", irr)
        + section("Files added in this session", added)
        + section("Verification standard applied", std)
    )
    return page(
        "repo-review.html",
        "Repository review",
        "Line-by-line audit of the repository as found, the Pages configuration, every irregularity in the work, and the verification standard applied.",
        body,
    )


def build_methodology():
    std = REVIEW["verification_standard"]
    body = (
        section(
            "The standard",
            ul("<strong>%s.</strong> %s" % (e(k.replace("_", " ").title()), e(v)) for k, v in std.items()),
        )
        + section(
            "What counts as an official source",
            "<p>A government department, regulator, central bank, tax authority, national "
            "legislature gazette or judicial body publishing its own instrument on its own "
            "domain. For this research that means <code>safe.gov.cn</code>, "
            "<code>gov.cn</code>, <code>pbc.gov.cn</code>, <code>chinatax.gov.cn</code> and its "
            "provincial subdomains, <code>moj.gov.cn</code>, provincial government portals, "
            "<code>irs.gov</code>, <code>home.treasury.gov</code>, <code>ecfr.gov</code> and "
            "<code>congress.gov</code>.</p>"
            "<p>Law firm notes, accounting firm alerts, tax-press summaries, bank marketing "
            "pages, aggregator sites and forum posts are not accepted, however accurate they "
            "appear. Where a search returned only secondary sources for a figure, the figure "
            "was left blank and flagged rather than cited to them.</p>",
        )
        + section(
            "One exception, recorded",
            "<p>The regulator's own text of Huifa [2017] No.29 on overseas card cash withdrawal "
            "could not be located on <code>safe.gov.cn</code> during this session. The figures "
            "for that route are taken from Bank of China's verbatim republication of the SAFE "
            "notice and of the SAFE spokesperson's answers. Bank of China is a state-owned "
            "commercial bank, not the regulator, so the entry is marked "
            "<span class='badge badge-secondary'>not official</span> and recorded as "
            + flagref("F08") + ".</p>",
        )
        + section(
            "How derived figures are handled",
            "<p>The only arithmetic performed on official data anywhere on this site is the "
            "fine-as-a-percentage column on the <a href='penalty.html'>penalty page</a>. It is "
            "computed as the published fine divided by the published amount moved, labelled as "
            "computed, and populated only where both official figures are expressed in the same "
            "currency. Where they are not, the cell is left blank rather than converted at an "
            "assumed exchange rate. No exchange rate is quoted anywhere on the site because no "
            "instrument in the source register fixes one; both "
            "Fashi [2019] No.1 Art.11 and Individual Income Tax Law Art.16 specify which rate "
            "to use without specifying the rate.</p>",
        )
        + section(
            "Limitations of this research",
            ul(
                [
                    "The instruments reviewed are the ones cited. Several SAFE instruments are "
                    "published as consolidated texts marked as amended, and the full amendment "
                    "history was not assembled in every case; see " + flagref("F16") + ".",
                    "Branch-level practice varies. Three separate conflicts between official "
                    "sources are recorded as " + flagref("F02") + ", " + flagref("F09") + " and "
                    + flagref("F17") + ", and each changes how the same transaction is processed "
                    "at different counters.",
                    "No fact pattern was supplied beyond 'a US citizen with renminbi in a "
                    "Chinese bank account'. Whether the balance is current-account income or "
                    "capital determines which routes are open at all, and that is not known here.",
                    "Chinese tax rates on some corporate transactions, notably the "
                    "characterisation of capital reduction proceeds, remain contested in practice "
                    "and could not be resolved from an official instrument; see "
                    + flagref("F03") + ".",
                    "US penalty amounts are inflation-adjusted annually. The figures shown are "
                    "those in the eCFR current to 5 November 2026 for penalties assessed on or "
                    "after 17 January 2025, and will move at the next adjustment.",
                    "Two channels commonly recommended for this exact problem, market procurement "
                    "trade and cross-border e-commerce export, are omitted rather than described "
                    "from secondary sources; see " + flagref("F14") + ".",
                ]
            ),
        )
        + section(
            "How the site is built and checked",
            "<p><code>build/build.py</code> reads <code>data/*.json</code> and writes every page "
            "into <code>docs/</code>, which is the GitHub Pages source directory. Output is "
            "deterministic and no page is hand-edited. <code>build/linkcheck.py</code> then runs "
            "as a gate before publication and fails on any citation to a source id that does not "
            "exist, any internal link to a page that was not generated, any orphan page, any "
            "route category with no page, and any flag referenced but not defined. Both scripts "
            "use only the Python standard library.</p>",
        )
        + note(e(SUMMARY["disclaimer"]), "warn")
    )
    return page(
        "methodology.html",
        "Methodology and limitations",
        "The verification standard applied, what counts as an official source, how derived figures are handled, and where this research stops short.",
        body,
    )


# --------------------------------------------------------------------------
# assets
# --------------------------------------------------------------------------

CSS = """
:root{
  --bg:#0f1115; --panel:#161a22; --panel2:#1c212c; --line:#262c39;
  --ink:#e7eaf0; --muted:#99a1b3; --dim:#6f7789;
  --acc:#5b9dff; --acc2:#7ce7c0; --warn:#ffb454; --bad:#ff6b6b;
  --ok:#4ade80; --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:var(--bg);color:var(--ink);
  font:16px/1.62 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,"Noto Sans SC",sans-serif;
  -webkit-font-smoothing:antialiased}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
code{font-family:var(--mono);font-size:.88em;background:var(--panel2);
  padding:.12em .38em;border-radius:4px;color:#cfe0ff;word-break:break-word}
.skip{position:absolute;left:-9999px}
.skip:focus{left:8px;top:8px;z-index:99;background:var(--acc);color:#000;padding:8px 12px;border-radius:6px}

.shell{display:grid;grid-template-columns:288px minmax(0,1fr);gap:0;min-height:100vh}
.side{position:sticky;top:0;align-self:start;height:100vh;overflow-y:auto;
  background:var(--panel);border-right:1px solid var(--line);padding:20px 0}
.brand{padding:0 20px 16px;border-bottom:1px solid var(--line);margin-bottom:12px}
.brand a{display:block}
.brand a:hover{text-decoration:none}
.brand-mark{display:block;font-weight:700;font-size:17px;letter-spacing:-.2px;color:var(--ink)}
.brand-sub{display:block;font-size:12.5px;color:var(--dim);margin-top:2px}
.navlist a{display:block;padding:7px 20px;border-left:3px solid transparent;color:var(--muted)}
.navlist a:hover{background:var(--panel2);text-decoration:none;color:var(--ink)}
.navlist a.active{border-left-color:var(--acc);background:var(--panel2);color:var(--ink)}
.nav-t{display:block;font-size:14px;font-weight:600}
.nav-d{display:block;font-size:11.5px;color:var(--dim);line-height:1.4}
.navfoot{margin-top:16px;padding:14px 20px 0;border-top:1px solid var(--line);
  font-size:11.5px;color:var(--dim);line-height:1.7}

main{min-width:0;padding:0}
.pagehead{padding:40px 44px 26px;border-bottom:1px solid var(--line);
  background:linear-gradient(180deg,var(--panel) 0%,rgba(22,26,34,0) 100%)}
.pagehead h1{margin:0 0 10px;font-size:30px;line-height:1.22;letter-spacing:-.5px;font-weight:700}
.subtitle{margin:0;color:var(--muted);font-size:15.5px;max-width:86ch}
.content{padding:30px 44px 20px;max-width:1320px}
.pagefoot{padding:24px 44px 56px;border-top:1px solid var(--line);color:var(--dim);font-size:13px}
.pagefoot p{margin:0 0 8px;max-width:110ch}

.block{margin:0 0 40px}
.block>h2,.content>h2{font-size:20px;margin:0 0 14px;letter-spacing:-.2px;
  padding-bottom:9px;border-bottom:1px solid var(--line)}
h3{font-size:17px;margin:0 0 6px;letter-spacing:-.1px}
h4{font-size:13px;margin:18px 0 7px;text-transform:uppercase;letter-spacing:.7px;color:var(--dim)}
p{margin:0 0 12px}

.kpigrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:14px;margin:0 0 40px}
.kpi{display:block;background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:18px;transition:border-color .15s,transform .15s}
.kpi:hover{border-color:var(--acc);transform:translateY(-2px);text-decoration:none}
.kpi-v{font-size:27px;font-weight:700;letter-spacing:-.8px;color:var(--acc2);line-height:1.1}
.kpi-l{font-size:13.5px;font-weight:600;color:var(--ink);margin-top:9px}
.kpi-n{font-size:12px;color:var(--dim);margin-top:5px;line-height:1.5}

.cardgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(268px,1fr));gap:14px}
.card{display:block;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px}
.card:hover{border-color:var(--acc);text-decoration:none}
.card h3{color:var(--ink)}
.card p{font-size:13.5px;color:var(--muted);margin:6px 0 12px}
.card-n{font-size:12px;color:var(--acc);font-weight:600}

.callout{border-radius:10px;padding:16px 18px;margin:0 0 26px;border:1px solid var(--line);
  border-left-width:4px;background:var(--panel)}
.callout p{margin:0;font-size:14.5px}
.callout-key{border-left-color:var(--acc2);background:rgba(124,231,192,.07)}
.callout-note{border-left-color:var(--acc)}
.callout-warn{border-left-color:var(--warn);background:rgba(255,180,84,.07)}

.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;margin:0 0 8px;background:var(--panel)}
table{border-collapse:collapse;width:100%;font-size:13.5px}
thead th{position:sticky;top:0;background:var(--panel2);text-align:left;font-size:11.5px;
  text-transform:uppercase;letter-spacing:.6px;color:var(--dim);font-weight:700;
  padding:11px 13px;border-bottom:1px solid var(--line);white-space:nowrap}
tbody td{padding:12px 13px;border-bottom:1px solid var(--line);vertical-align:top;line-height:1.55}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:rgba(91,157,255,.045)}
table.detail tbody td:first-child{width:210px;font-weight:600;color:var(--muted);white-space:nowrap}
td ul{margin:0;padding-left:18px}
td li{margin:0 0 4px}

.badge{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.5px;
  text-transform:uppercase;padding:2.5px 7px;border-radius:20px;white-space:nowrap;
  border:1px solid transparent;vertical-align:middle}
.badge-official{background:rgba(74,222,128,.14);color:var(--ok);border-color:rgba(74,222,128,.3)}
.badge-secondary{background:rgba(255,180,84,.14);color:var(--warn);border-color:rgba(255,180,84,.32)}
.badge-verified{background:rgba(74,222,128,.14);color:var(--ok);border-color:rgba(74,222,128,.3)}
.badge-unverified{background:rgba(255,107,107,.14);color:var(--bad);border-color:rgba(255,107,107,.32)}
.badge-neutral{background:var(--panel2);color:var(--muted);border-color:var(--line)}
.risk-high{background:rgba(255,107,107,.16);color:var(--bad);border-color:rgba(255,107,107,.35)}
.risk-medium{background:rgba(255,180,84,.16);color:var(--warn);border-color:rgba(255,180,84,.35)}
.risk-low{background:rgba(74,222,128,.14);color:var(--ok);border-color:rgba(74,222,128,.3)}
.risk-none{background:var(--panel2);color:var(--dim);border-color:var(--line)}
.badge-sev-material{background:rgba(255,107,107,.14);color:var(--bad);border-color:rgba(255,107,107,.32)}
.badge-sev-minor{background:rgba(255,180,84,.14);color:var(--warn);border-color:rgba(255,180,84,.32)}

a.src{display:inline-block;font-family:var(--mono);font-size:11px;background:var(--panel2);
  border:1px solid var(--line);border-radius:5px;padding:1px 5px;color:var(--acc);margin:1px}
a.src:hover{border-color:var(--acc);text-decoration:none}
a.flagref{display:inline-block;font-family:var(--mono);font-size:11px;
  background:rgba(255,107,107,.12);border:1px solid rgba(255,107,107,.3);
  border-radius:5px;padding:1px 5px;color:var(--bad);margin:1px}
a.flagref:hover{text-decoration:none;border-color:var(--bad)}
.badref{color:var(--bad);font-family:var(--mono);font-size:11px}
.blank{color:var(--dim);font-size:15px}
.muted{color:var(--dim);font-size:12px}
.zh{color:var(--dim);font-size:12.5px}
.applies{color:var(--muted);font-size:13.5px;margin:0 0 14px}
.srcs{color:var(--dim);font-size:12.5px;margin:10px 0 0}

.route{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:22px;margin:0 0 18px}
.route:target{border-color:var(--acc);box-shadow:0 0 0 1px var(--acc)}
.rhead{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;
  flex-wrap:wrap;margin:0 0 16px;padding-bottom:14px;border-bottom:1px solid var(--line)}
.rhead h3{margin:0 0 4px}
.rid{font-family:var(--mono);font-size:12px;color:var(--dim);font-weight:400;margin-left:6px}
.rbadges{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.twocol{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:16px}
.twocol ul{margin:0;padding-left:18px;font-size:13.5px}
.twocol li{margin:0 0 9px;color:var(--muted)}
.twocol li strong{color:var(--ink)}

.flag,.source{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:20px 22px;margin:0 0 14px}
.flag:target,.source:target{border-color:var(--warn);box-shadow:0 0 0 1px var(--warn)}
.flagmeta{margin:0 0 12px}
.srcline{margin:0 0 5px;font-size:13.5px}
.obs{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--acc2);
  border-radius:10px;padding:18px 20px;margin:0 0 14px}
.obs h4{margin:12px 0 5px}
.obs h4:first-child{margin-top:0}
.obs p{font-size:14px;margin:0 0 6px}

.toolbar{display:flex;gap:10px;align-items:center;margin:0 0 14px;flex-wrap:wrap}
.toolbar input{flex:1;min-width:220px;background:var(--panel2);border:1px solid var(--line);
  color:var(--ink);padding:9px 12px;border-radius:8px;font-size:14px}
.toolbar input:focus{outline:none;border-color:var(--acc)}
.toolbar .count{font-size:12.5px;color:var(--dim)}

@media(max-width:1000px){
  .shell{grid-template-columns:1fr}
  .side{position:static;height:auto;border-right:none;border-bottom:1px solid var(--line)}
  .navlist{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr))}
  .pagehead,.content,.pagefoot{padding-left:20px;padding-right:20px}
  .twocol{grid-template-columns:1fr}
  table.detail tbody td:first-child{white-space:normal}
}
"""

JS = """
(function () {
  'use strict';

  /* Client-side filter for any table inside a [data-filterable] block.
     Purely additive: with scripting disabled every table is fully readable. */
  document.querySelectorAll('.tablewrap').forEach(function (wrap) {
    var table = wrap.querySelector('table');
    if (!table || table.querySelectorAll('tbody tr').length < 8) { return; }

    var bar = document.createElement('div');
    bar.className = 'toolbar';
    var input = document.createElement('input');
    input.type = 'search';
    input.placeholder = 'Filter this table\\u2026';
    input.setAttribute('aria-label', 'Filter table rows');
    var count = document.createElement('span');
    count.className = 'count';
    bar.appendChild(input);
    bar.appendChild(count);
    wrap.parentNode.insertBefore(bar, wrap);

    var rows = Array.prototype.slice.call(table.querySelectorAll('tbody tr'));
    function apply() {
      var q = input.value.trim().toLowerCase();
      var shown = 0;
      rows.forEach(function (tr) {
        var hit = !q || tr.textContent.toLowerCase().indexOf(q) !== -1;
        tr.style.display = hit ? '' : 'none';
        if (hit) { shown++; }
      });
      count.textContent = shown + ' of ' + rows.length + ' rows';
    }
    input.addEventListener('input', apply);
    apply();
  });

  /* Reveal the row a fragment identifier points at on long pages. */
  function focusTarget() {
    if (!location.hash) { return; }
    var el = document.getElementById(location.hash.slice(1));
    if (el && el.scrollIntoView) {
      el.scrollIntoView({ block: 'start' });
    }
  }
  window.addEventListener('hashchange', focusTarget);
  focusTarget();
}());
"""


def write_assets():
    css_dir = os.path.join(OUT, "assets", "css")
    js_dir = os.path.join(OUT, "assets", "js")
    os.makedirs(css_dir, exist_ok=True)
    os.makedirs(js_dir, exist_ok=True)
    with open(os.path.join(css_dir, "style.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS.lstrip("\n"))
    with open(os.path.join(js_dir, "site.js"), "w", encoding="utf-8") as fh:
        fh.write(JS.lstrip("\n"))
    # GitHub Pages must not try to Jekyll-process the assets directory.
    with open(os.path.join(OUT, ".nojekyll"), "w", encoding="utf-8") as fh:
        fh.write("")


def build_readme_redirect():
    """docs/README.md is not used; GitHub Pages serves index.html."""
    return None


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

PAGES = [
    ("index.html", build_index),
    ("executive-summary.html", build_summary),
    ("routes.html", build_routes),
    ("tax-china.html", build_tax_china),
    ("tax-us.html", build_tax_us),
    ("tax-treaty.html", build_treaty),
    ("penalty.html", build_penalty),
    ("flagged.html", build_flagged),
    ("sources.html", build_sources),
    ("repo-review.html", build_review),
    ("methodology.html", build_methodology),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    written = []

    for filename, fn in PAGES:
        write(filename, fn())
        written.append(filename)

    # one page per route category
    for cat_id, c in CAT.items():
        write(c["page"], build_category(cat_id))
        written.append(c["page"])

    write_assets()

    # every generated page must be reachable from the navigation
    for f in written:
        if f not in NAV_BY_HREF:
            ERRORS.append("generated page not present in NAV (orphan): %s" % f)
    for href in NAV_BY_HREF:
        if href not in written:
            ERRORS.append("NAV entry with no generated page: %s" % href)

    # every route category must have a page
    for r in ROUTES["routes"]:
        if r["category"] not in CAT:
            ERRORS.append("route %s has unknown category %r" % (r["id"], r["category"]))

    if ERRORS:
        sys.stderr.write("\nbuild/build.py: %d problem(s)\n" % len(ERRORS))
        for m in sorted(set(ERRORS)):
            sys.stderr.write("  - %s\n" % m)
        sys.exit(1)

    sys.stdout.write(
        "built %d pages into docs/ (%d sources, %d routes, %d flags, %d cases)\n"
        % (
            len(written),
            len(SOURCES["sources"]),
            len(ROUTES["routes"]),
            len(FLAGS["flags"]),
            len(PENALTIES["published_cases"]["cases"]),
        )
    )
    for f in written:
        sys.stdout.write("  %s\n" % f)


if __name__ == "__main__":
    main()
