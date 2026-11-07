#!/usr/bin/env python3
"""
Static site generator for the China1 evidence pack.

Design decision: pages are generated as static HTML rather than rendered client-side
from JSON. Reasons:
  1. Every table row and every source link exists in the page source, so the
     verification script in build/verify.py can check them statically.
  2. No dependency on fetch() succeeding on GitHub Pages.
  3. The site works with JavaScript disabled.
"""

import json
import html
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

SITE_TITLE = "CNY → USD Evidence Pack"
SITE_SUB = "A sourced, verified reference on moving money out of mainland China as a US person"

NAV = [
    ("index.html", "Dashboard"),
    ("executive-summary.html", "Executive summary"),
    ("methods.html", "All channels"),
    ("lawful.html", "Lawful routes"),
    ("prohibited.html", "Prohibited routes"),
    ("penalty.html", "The penalty"),
    ("us-reporting.html", "US reporting"),
    ("sources.html", "Sources"),
    ("flagged.html", "Flagged for review"),
]

CATEGORY_LABEL = {
    "lawful-current-account": "Lawful · current account",
    "lawful-capital-account": "Lawful · capital account",
    "not-a-transfer": "Not a transfer",
    "prohibited": "Prohibited",
    "tax-planning": "Tax rule",
    "note": "Note",
}

LEGALITY_CLASS = {
    "lawful": "ok",
    "conditional": "warn",
    "not_a_transfer": "neutral",
    "prohibited": "bad",
    "unverified": "unknown",
}

LEGALITY_LABEL = {
    "lawful": "Lawful",
    "conditional": "Conditional",
    "not_a_transfer": "Not a transfer",
    "prohibited": "Prohibited",
    "unverified": "Unverified",
}

CONF_CLASS = {"verified": "ok", "partial": "warn", "unverified": "unknown"}


def load():
    with open(DATA / "sources.json", encoding="utf-8") as f:
        sources = json.load(f)
    with open(DATA / "methods.json", encoding="utf-8") as f:
        methods = json.load(f)
    with open(DATA / "penalties.json", encoding="utf-8") as f:
        penalties = json.load(f)
    with open(DATA / "flagged.json", encoding="utf-8") as f:
        flagged = json.load(f)
    return sources, methods, penalties, flagged


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def src_link(sid, srcmap):
    s = srcmap.get(sid)
    if not s:
        return esc(sid)
    return (
        f'<a href="{esc(s["url"])}" target="_blank" rel="noopener" '
        f'title="{esc(s["title"])} — {esc(s["publisher"])}">{esc(sid)}</a>'
    )


def src_links(csv, srcmap):
    ids = [x.strip() for x in (csv or "").split(",") if x.strip()]
    if not ids:
        return '<span class="muted">—</span>'
    return " ".join(src_link(i, srcmap) for i in ids)


def cell(value, note="", blank_flag=True):
    """Render a value. If blank, render an explicit unverified marker, never a guess."""
    if value == "not_applicable":
        return '<span class="muted" title="This concept does not arise for this channel">n/a</span>'
    if value == "" or value is None:
        if blank_flag:
            return '<span class="blank" title="No official source confirmed a value; left blank deliberately">unverified</span>'
        return '<span class="muted">—</span>'
    out = esc(value)
    if note:
        out += f'<span class="subnote">{esc(note)}</span>'
    return out


def head(title, rel="", extra_css=""):
    nav = "\n".join(
        f'<a href="{rel}{href}">{esc(label)}</a>' for href, label in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · {esc(SITE_TITLE)}</title>
<meta name="description" content="{esc(SITE_SUB)}. Every figure is tied to a cited official source; unconfirmed values are left blank and flagged.">
<link rel="stylesheet" href="{rel}assets/style.css">
{extra_css}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="topbar">
  <div class="wrap">
    <div class="brand">
      <a href="{rel}index.html" class="brandmark">CNY<span>→</span>USD</a>
      <span class="brandsub">Evidence pack · built 2026-11-07</span>
    </div>
    <nav class="nav" aria-label="Primary">
      {nav}
    </nav>
  </div>
</header>
<main id="main" class="wrap">
"""


def foot(rel=""):
    return f"""</main>
<footer class="foot">
  <div class="wrap">
    <p><strong>What this site is.</strong> A documented evidence pack. Every figure traces to an official
    government source listed on the <a href="{rel}sources.html">Sources</a> page. Where no official source
    confirmed a value, the cell says <span class="blank">unverified</span> and the item appears on
    <a href="{rel}flagged.html">Flagged for review</a>. Nothing was inferred, estimated or filled from memory.</p>
    <p><strong>What it is not.</strong> It is not tax, legal or investment advice, and it is not a plan for your
    specific facts. Classification as a domestic vs foreign individual, prior-year filing history, and
    willfulness are decisive and cannot be determined from this dataset. Consult a qualified adviser.</p>
    <p class="muted">Built by session <code>arena-d7e7ed3b</code>. Source snapshot 2026-11-07.
    Working notes and the verification log are in <a href="../COORDINATION.md">COORDINATION.md</a>.</p>
  </div>
</footer>
</body>
</html>
"""


def badge(text, cls):
    return f'<span class="badge {cls}">{esc(text)}</span>'


# ----------------------------------------------------------------------------- index
def page_index(methods, sources, penalties, flagged):
    srcmap = {s["id"]: s for s in sources["sources"]}
    ms = methods["methods"]

    counts = {}
    for m in ms:
        counts[m["category"]] = counts.get(m["category"], 0) + 1

    verified = sum(1 for m in ms if m["confidence"] == "verified")
    partial = sum(1 for m in ms if m["confidence"] == "partial")
    unver = sum(1 for m in ms if m["confidence"] == "unverified")
    prohibited = sum(1 for m in ms if m["legality"] == "prohibited")

    def card(href, kicker, big, label, desc):
        return f"""<a class="card" href="{href}">
  <div class="card-kicker">{esc(kicker)}</div>
  <div class="card-big">{esc(big)}</div>
  <div class="card-label">{esc(label)}</div>
  <p class="card-desc">{esc(desc)}</p>
</a>"""

    cards = "\n".join([
        card("executive-summary.html", "Start here", "1 page",
             "Executive summary",
             "The whole finding in one page: what the tax actually is, where the real cost sits, and what to do first."),
        card("methods.html", "Inventory", str(len(ms)),
             "Channels catalogued",
             "Every route considered — lawful, conditional, non-transfer and prohibited — with limits, sources and pros/cons."),
        card("penalty.html", "Cost breakdown", "6 layers",
             "Where the money goes",
             "PRC conversion tax, execution spread, US income tax, US reporting penalties, PRC enforcement fines, and relief paths."),
        card("prohibited.html", "Risk", str(prohibited),
             "Prohibited routes",
             "Named and sourced, so you can recognise them. Statutory range 30%–100% of the amount."),
        card("us-reporting.html", "Compliance", "4 forms",
             "US reporting duties",
             "FBAR, Form 8938, Form 3520 and §988 — thresholds and penalties, all from IRS and eCFR pages."),
        card("flagged.html", "Transparency", str(flagged["meta"]["counts"]["unverified_rows"] + flagged["meta"]["counts"]["partially_verified_rows"]),
             "Items flagged",
             "Everything this project could not confirm from an official source, with what was left blank and why."),
    ])

    # headline findings with source links
    findings = [
        ("The PRC does not tax the conversion.",
         "Individual income tax applies to nine enumerated categories of income. Foreign-exchange gain and currency "
         "conversion are not among them. Savings-deposit interest has been provisionally exempt since 9 October 2008. "
         "A lawful conversion through a lawful channel therefore carries a <strong>0% PRC conversion tax</strong>.",
         "S05,S06,S07"),
        ("The wall is a quota, not a tax.",
         "The binding constraint is USD 50,000 per person per year of FX purchase and settlement. Above that, a genuine "
         "current-account purpose with documents is required. A USD 1,000,000 balance needs 20 person-years of quota.",
         "S04,S11"),
        ("Only two lawful routes can move a whole balance.",
         "Emigrant transfer and inheritance transfer under PBoC 2004 No.16 are the only general-purpose capital-account "
         "exits. Emigrant transfer requires cancelling PRC household registration first, and a PRC tax clearance certificate.",
         "S02,S03"),
        ("The genuine large liability on the US side is reporting, not tax.",
         "FBAR exposure is USD 16,536 per report non-willfully and USD 165,353 or 50% of the balance willfully. One missed "
         "year on a USD 500,000 account can exceed the entire tax you are worried about.",
         "S17,S19,S27"),
        ("Every prohibited route is 30%–100% of the amount.",
         "Evasion and illegal FX arbitrage carry fines up to 30% of the amount, rising to 30%–100% where serious, plus "
         "criminal liability — several times any plausible tax. All ten of SAFE's published individual cases in March "
         "2024 were underground-bank cases.",
         "S01,S15"),
        ("Getting it wrong costs three years, not one.",
         "Misdeclaring the purpose, or lending/borrowing a quota, puts you on the watch list: no facilitation quota for "
         "the listing year plus the following two years.",
         "S12,S16"),
    ]

    fl = "\n".join(
        f"""<article class="finding">
  <h3>{i+1}. {txt}</h3>
  <p>{body}</p>
  <div class="finding-src">Source: {src_links(src, srcmap)}</div>
</article>"""
        for i, (txt, body, src) in enumerate(findings)
    )

    body = f"""
<section class="hero">
  <h1>What does it actually cost to get CNY out of China as a US citizen?</h1>
  <p class="lede">Short answer, from the primary sources: <strong>the PRC does not tax the conversion.</strong>
  The cost you are feeling is three separate things, and only one of them is a real tax — a quota wall, a retail
  FX spread, and US <em>reporting</em> exposure on the account. This pack documents each one against an official
  source, and leaves blanks where nothing official exists.</p>
  <div class="hero-stats">
    <div class="stat"><div class="stat-num">0%</div><div class="stat-lab">PRC tax on the conversion itself</div></div>
    <div class="stat"><div class="stat-num">$50k</div><div class="stat-lab">Annual quota per person, current account</div></div>
    <div class="stat"><div class="stat-num">30–100%</div><div class="stat-lab">PRC fine range for the wrong route</div></div>
    <div class="stat"><div class="stat-num">$16,536</div><div class="stat-lab">Max FBAR penalty per report, non-willful</div></div>
  </div>
</section>

<section class="panel">
  <h2 id="findings">Six findings that decide the answer</h2>
  <div class="findings">{fl}</div>
</section>

<section>
  <h2>Navigate</h2>
  <div class="grid">{cards}</div>
</section>

<section class="panel">
  <h2 id="integrity">Data integrity</h2>
  <div class="integrity">
    <div class="int-item"><span class="badge ok">{verified}</span><span>channels fully verified</span></div>
    <div class="int-item"><span class="badge warn">{partial}</span><span>partially verified (core rule sourced, some cells blank)</span></div>
    <div class="int-item"><span class="badge unknown">{unver}</span><span>retained but unverified (all values blank)</span></div>
    <div class="int-item"><span class="badge ok">{len(sources['sources'])}</span><span>official sources retrieved and read</span></div>
    <div class="int-item"><span class="badge warn">{len(flagged['items'])}</span><span>items on the flagged register</span></div>
  </div>
  <p class="note">The three categories above are mutually exclusive and sum to {len(ms)} channels.
  Nothing is counted as verified unless every populated cell traces to a primary official source.</p>
</section>

<section class="panel">
  <h2 id="at-a-glance">All channels at a glance</h2>
  <div class="tablewrap">
  <table class="tbl compact">
    <thead><tr><th>ID</th><th>Channel</th><th>Type</th><th>Legality</th><th>Annual limit</th><th>PRC tax on conversion</th><th>Confidence</th></tr></thead>
    <tbody>
    {"".join(
        f'''<tr>
      <td class="mono">{esc(m["id"])}</td>
      <td><a href="methods.html#{esc(m["id"])}">{esc(m["name"])}</a></td>
      <td><span class="cat">{esc(CATEGORY_LABEL.get(m["category"], m["category"]))}</span></td>
      <td>{badge(LEGALITY_LABEL.get(m["legality"], m["legality"]), LEGALITY_CLASS.get(m["legality"], "neutral"))}</td>
      <td>{cell(("USD " + format(m["annual_limit_usd"], ",")) if m["annual_limit_usd"] not in ("", None) else "", m.get("annual_limit_note","")[:110])}</td>
      <td>{cell(m["china_tax_on_conversion"])}</td>
      <td>{badge(m["confidence"], CONF_CLASS[m["confidence"]])}</td>
    </tr>'''
        for m in ms
    )}
    </tbody>
  </table>
  </div>
</section>
"""
    return head("Dashboard") + body + foot()


# ----------------------------------------------------------------------------- methods
def page_methods(methods, sources, title, filt, intro, anchor="all"):
    srcmap = {s["id"]: s for s in sources["sources"]}
    ms = [m for m in methods["methods"] if filt(m)]

    rows = []
    for m in ms:
        lim = ""
        if m["annual_limit_usd"] not in ("", None):
            lim = "USD " + format(m["annual_limit_usd"], ",")
        lim_html = cell(lim, m.get("annual_limit_note", ""))
        rows.append(f"""
    <tr id="{esc(m["id"])}">
      <td class="mono">{esc(m["id"])}</td>
      <td><strong>{esc(m["name"])}</strong><span class="zh">{esc(m["name_zh"])}</span>
          <span class="what">{esc(m["what_it_is"])}</span></td>
      <td><span class="cat">{esc(CATEGORY_LABEL.get(m["category"], m["category"]))}</span></td>
      <td>{badge(LEGALITY_LABEL.get(m["legality"], m["legality"]), LEGALITY_CLASS.get(m["legality"], "neutral"))}</td>
      <td>{lim_html}</td>
      <td>{cell(m["china_tax_on_conversion"], m.get("china_tax_note", ""))}<div class="srcs">Source: {src_links(m.get("china_tax_source",""), srcmap)}</div></td>
      <td>{cell(m["us_tax_treatment"])}<div class="srcs">Source: {src_links(m.get("us_tax_source",""), srcmap)}</div></td>
      <td>{cell(m["us_reporting"])}<div class="srcs">Source: {src_links(m.get("us_reporting_source",""), srcmap)}</div></td>
      <td class="pen">{cell(m["penalty_if_misused"])}<div class="srcs">Source: {src_links(m.get("penalty_source",""), srcmap)}</div></td>
      <td><ul class="pros">{"".join(f"<li>{esc(p)}</li>" for p in m["pros"])}</ul></td>
      <td><ul class="cons">{"".join(f"<li>{esc(c)}</li>" for c in m["cons"])}</ul></td>
      <td>{badge(m["confidence"], CONF_CLASS[m["confidence"]])}
          <div class="srcs">{src_links(",".join(m["sources"]), srcmap)}</div></td>
    </tr>""")

    flag_html = ""
    allflags = [(m["id"], f) for m in ms for f in m.get("flags", [])]
    if allflags:
        flag_html = (
            '<div class="callout warn"><strong>Flagged on this page:</strong><ul>'
            + "".join(f"<li><code>{esc(mid)}</code> — {esc(f)}</li>" for mid, f in allflags)
            + '</ul><a href="flagged.html">See the full flagged register →</a></div>'
        )

    body = f"""
<section class="pagehead">
  <h1>{esc(title)}</h1>
  <p class="lede">{intro}</p>
  <p class="count"><strong>{len(ms)}</strong> channel{'s' if len(ms) != 1 else ''} on this page.</p>
</section>
{flag_html}
<div class="tablewrap wide">
<table class="tbl">
  <thead><tr>
    <th>ID</th><th>Channel</th><th>Type</th><th>Legality</th><th>Annual limit</th>
    <th>PRC tax on conversion</th><th>US income tax</th><th>US reporting</th>
    <th>Penalty if misused</th><th>Pros</th><th>Cons</th><th>Confidence / sources</th>
  </tr></thead>
  <tbody>
  {''.join(rows) if rows else '<tr><td colspan="12" class="muted">No channels in this category.</td></tr>'}
  </tbody>
</table>
</div>
<p class="note">Hover or click any source ID to open the official page. A cell reading
<span class="blank">unverified</span> means no official source confirmed a value — it was left blank rather than guessed.</p>
"""
    return head(title) + body + foot()


# ----------------------------------------------------------------------------- penalty
def page_penalty(penalties, sources):
    srcmap = {s["id"]: s for s in sources["sources"]}
    layers = penalties["layers"]

    secs = []
    for L in layers:
        rows = "".join(
            f"""<tr>
      <td>{esc(f["item"])}</td>
      <td>{cell(f["value"])}</td>
      <td class="expl">{esc(f["basis"])}
          <div class="srcs">Source: {src_links(f["source"], srcmap)}</div></td>
    </tr>"""
            for f in L["findings"]
        )
        secs.append(f"""
<section class="panel">
  <h2 id="{esc(L["layer"].split(".")[0].strip().lower())}">{esc(L["layer"])}</h2>
  <div class="tablewrap">
  <table class="tbl">
    <thead><tr><th style="width:26%">Item</th><th style="width:22%">Value</th><th>Basis (verbatim rule + official source)</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
</section>""")

    synth = "".join(f"<li>{esc(s)}</li>" for s in penalties["synthesis"])

    body = f"""
<section class="pagehead">
  <h1>The conversion penalty, broken down</h1>
  <p class="lede">{esc(penalties["meta"]["headline"])}</p>
</section>

<section class="panel callout">
  <strong>Read this first.</strong> "Penalty" is used loosely in most material on this topic. Here it is split into
  six layers that behave completely differently: a statutory tax rate, a commercial spread, a US income-tax rule,
  a US information-reporting penalty, a PRC enforcement fine, and a relief path. Conflating them is what makes the
  problem look unsolvable.
</section>

{"".join(secs)}

<section class="panel">
  <h2 id="synthesis">Synthesis</h2>
  <ol class="synth">{synth}</ol>
</section>
"""
    return head("The penalty") + body + foot()


# ----------------------------------------------------------------------------- us reporting
def page_us(sources):
    srcmap = {s["id"]: s for s in sources["sources"]}

    forms = [
        ("FBAR — FinCEN Form 114",
         "A US person with a financial interest in, or signature authority over, foreign financial accounts whose "
         "aggregate value exceeded USD 10,000 at any time in the calendar year.",
         "Due 15 April, automatic extension to 15 October. Filed with FinCEN, not with the tax return. Keep records 5 years.",
         "Non-willful: USD 16,536 maximum per report (penalties assessed on or after 2025-01-17). Willful: USD 165,353 "
         "maximum, or 50% of the account balance, whichever is greater.",
         "S17,S19,S27",
         "A single CN¥ account in a Chinese bank is a foreign financial account. Whether it produced taxable income is irrelevant."),
        ("Form 8938 — Statement of Specified Foreign Financial Assets",
         "A specified individual holding specified foreign financial assets above the applicable threshold. "
         "US resident unmarried: above USD 50,000 at year end or USD 75,000 at any time. US resident MFJ: above "
         "USD 100,000 / USD 150,000. Living abroad unmarried: above USD 200,000 / USD 300,000. Living abroad MFJ: "
         "above USD 400,000 / USD 600,000.",
         "Attached to the annual income tax return. Not required if no income tax return is required for the year.",
         "USD 10,000, plus USD 10,000 per 30-day period after a 90-day IRS notice, capped at USD 50,000 additional.",
         "S20",
         "Overlaps FBAR but is not the same test — different statute (Title 26 vs Title 31), different thresholds, different scope."),
        ("Form 3520 — Part IV — large foreign gifts and bequests",
         "Aggregate gifts or bequests from a nonresident alien or foreign estate exceeding USD 100,000 in the tax year. "
         "Each gift over USD 5,000 must be separately identified. For purported gifts from foreign corporations or "
         "partnerships the threshold is USD 20,116 for 2025 and USD 20,573 for 2026.",
         "Due the 15th day of the 4th month after year end (6th month if living and working abroad); extendable to the "
         "10th month. Filed separately from the income tax return.",
         "5% of the amount of the foreign gifts per month the failure continues, capped at 25% in total.",
         "S21,S22",
         "Receiving a gift or bequest is not taxable income. The penalty is for not reporting it."),
        ("§988 — foreign currency gain on disposing of the CNY",
         "A disposition of nonfunctional currency is a §988 transaction. For an individual's personal transaction, no "
         "gain is recognised by reason of exchange-rate movement unless the gain would exceed USD 200.",
         "Reported on the return for the year of disposition where the threshold is exceeded.",
         "Not a penalty — the consequence is that the gain is ordinary income, not capital.",
         "S24",
         "The USD 200 test is a cliff applied per transaction, not an annual allowance. Just over USD 200 and the whole gain is in."),
    ]

    rows = "".join(f"""
  <tr>
    <td><strong>{esc(n)}</strong></td>
    <td>{esc(who)}</td>
    <td>{esc(when)}</td>
    <td class="pen">{esc(pen)}</td>
    <td>{esc(note)}<div class="srcs">Source: {src_links(src, srcmap)}</div></td>
  </tr>""" for n, who, when, pen, src, note in forms)

    body = f"""
<section class="pagehead">
  <h1>US reporting duties on money sitting in China</h1>
  <p class="lede">This is where a US citizen's real exposure lives. Note the distinction the IRS itself draws:
  whether the account produced taxable income has no effect on whether it is reportable. Reporting and taxation are
  separate questions, and the penalties attach to the reporting.</p>
</section>

<div class="tablewrap wide">
<table class="tbl">
  <thead><tr><th>Form</th><th>Who must file / threshold</th><th>When</th><th>Penalty</th><th>Note</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
</div>

<section class="panel">
  <h2 id="relief">Penalty relief: the streamlined procedures</h2>
  <p>The IRS offers two tracks to a taxpayer who certifies that the failure to report foreign financial assets and pay
  all tax was <em>not</em> willful. Non-willful conduct means negligence, inadvertence, mistake, or a good-faith
  misunderstanding of the law.</p>
  <div class="tablewrap">
  <table class="tbl">
    <thead><tr><th>Track</th><th>Who</th><th>Offshore penalty</th></tr></thead>
    <tbody>
      <tr><td><strong>Streamlined Domestic Offshore Procedures (SDOP)</strong></td>
          <td>US residents — taxpayers who do not meet the non-residency test</td>
          <td>A single 5% Title 26 miscellaneous offshore penalty <span class="blankmini">(percentage flagged — see F-note on the Flagged page)</span></td></tr>
      <tr><td><strong>Streamlined Foreign Offshore Procedures (SFOP)</strong></td>
          <td>Taxpayers meeting the non-residency test (e.g. 330 full days abroad in one of the covered years)</td>
          <td>No miscellaneous offshore penalty</td></tr>
    </tbody>
  </table>
  </div>
  <p class="note">Source: {src_links("S23", srcmap)}. Two hard limits: the procedures are
  <strong>unavailable</strong> if the IRS has begun a civil examination of your returns for any taxable year, or if you
  are under IRS Criminal Investigation. And they are not amnesty — returns may still be audited, and additional civil
  penalties and even criminal liability remain possible if the conduct was in fact willful.</p>
</section>

<section class="panel callout bad">
  <strong>The one line that removes an excuse people rely on.</strong> The Form 3520 instructions state expressly that
  <em>"the fact that a foreign country would impose penalties for disclosing the required information is not reasonable
  cause."</em> You cannot defend a missing FBAR or Form 3520 by pointing at PRC secrecy law.
  <div class="srcs">Source: {src_links("S21", srcmap)}</div>
</section>

<section class="panel">
  <h2 id="treaty">The treaty does not help here</h2>
  <p>The 1984 US–PRC Income Tax Convention (in force 1 January 1987) primarily allocates taxing rights and provides a
  foreign tax credit in Article 22 and information exchange in Article 25. Its Saving Clause — Protocol 1, paragraph 2 —
  preserves the US right to tax its citizens and residents as if the treaty had not come into effect. A treaty does not
  create a currency-mobility right, and it does not displace FBAR.</p>
  <div class="srcs">Source: {src_links("S25,S26", srcmap)}</div>
</section>
"""
    return head("US reporting") + body + foot()


# ----------------------------------------------------------------------------- sources
def page_sources(sources):
    ss = sources["sources"]
    rows = "".join(f"""
  <tr id="{esc(s["id"])}">
    <td class="mono">{esc(s["id"])}</td>
    <td><a href="{esc(s["url"])}" target="_blank" rel="noopener"><strong>{esc(s["short"])}</strong></a>
        <span class="zh">{esc(s["title"])}</span></td>
    <td>{esc(s["publisher"])}</td>
    <td>{badge(s["tier"], "ok" if s["tier"] == "primary" else "warn")}</td>
    <td>{esc(s["verified_on"])}</td>
    <td class="expl"><ul class="ticks">{"".join(f"<li>{esc(x)}</li>" for x in s["supports"])}</ul>
        {"<div class='callout warn mini'>" + esc(s.get("note","")) + "</div>" if s.get("note") else ""}</td>
  </tr>""" for s in ss)

    body = f"""
<section class="pagehead">
  <h1>Sources</h1>
  <p class="lede">Every one of these was retrieved and read during this session. The "supports" column records the
  exact propositions taken from that page — so you can check the claim, not just the topic.</p>
  <p class="count"><strong>{len(ss)}</strong> sources ·
  <strong>{sum(1 for s in ss if s["tier"]=="primary")}</strong> primary official ·
  <strong>{sum(1 for s in ss if s["tier"]!="primary")}</strong> secondary</p>
</section>
<div class="tablewrap wide">
<table class="tbl">
  <thead><tr><th>ID</th><th>Document</th><th>Publisher</th><th>Tier</th><th>Retrieved</th><th>What it supports</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
</div>
"""
    return head("Sources") + body + foot()


# ----------------------------------------------------------------------------- flagged
def page_flagged(flagged, sources):
    srcmap = {s["id"]: s for s in sources["sources"]}
    items = flagged["items"]
    counts = flagged["meta"]["counts"]

    sev_class = {"high": "bad", "medium": "warn", "low": "neutral"}

    rows = "".join(f"""
  <tr id="{esc(it["id"])}">
    <td class="mono">{esc(it["id"])}</td>
    <td>{badge(it["severity"], sev_class.get(it["severity"], "neutral"))}
        <span class="cat">{esc(it["type"])}</span></td>
    <td><strong>{esc(it["subject"])}</strong></td>
    <td class="expl">{esc(it["finding"])}</td>
    <td class="expl">{esc(it["action_taken"])}</td>
    <td class="expl">{esc(it["why_it_matters"])}
        <div class="srcs">{" ".join(f'<a href="{esc(u)}" target="_blank" rel="noopener">official link</a>' for u in it["source_links"]) or '<span class="muted">no official source exists</span>'}</div></td>
  </tr>""" for it in items)

    body = f"""
<section class="pagehead flaghead">
  <h1>Flagged for review</h1>
  <p class="lede">This page exists because of the verification rule: <strong>if a value cannot be confirmed from an
  official source, it is left blank and flagged — never inferred.</strong> Everything below is either something this
  project could not confirm, or a scope limit you need to know about before relying on any answer.</p>
  <div class="hero-stats small">
    <div class="stat"><div class="stat-num">{counts["unverified_rows"]}</div><div class="stat-lab">rows left entirely unverified</div></div>
    <div class="stat"><div class="stat-num">{counts["partially_verified_rows"]}</div><div class="stat-lab">rows partially verified</div></div>
    <div class="stat"><div class="stat-num">{counts["secondary_source_uses"]}</div><div class="stat-lab">secondary-source use, disclosed</div></div>
    <div class="stat"><div class="stat-num">{counts["open_legal_questions"]}</div><div class="stat-lab">open legal questions</div></div>
  </div>
</section>

<div class="tablewrap wide">
<table class="tbl">
  <thead><tr>
    <th>ID</th><th>Severity / type</th><th>Subject</th><th>What could not be confirmed</th>
    <th>What was done instead</th><th>Why it matters</th>
  </tr></thead>
  <tbody>{rows}</tbody>
</table>
</div>

<section class="panel">
  <h2 id="what-blank-means">What a blank means</h2>
  <p>A cell reading <span class="blank">unverified</span> is not a missing datum to be filled in later by guesswork.
  It is an assertion that <em>the official record does not state a number</em>, or that no official page could be
  retrieved for it. Filling those cells is exactly how the bad advice circulating on this topic is produced.</p>
  <p>The four blank value families this project deliberately left empty:</p>
  <ul>
    <li><strong>Retail CNY/USD spread and wire fees</strong> — commercial, unpublished, and moving. No official schedule exists.</li>
    <li><strong>PRC exit tax on cancelling household registration</strong> — a tax settlement is required; whether it operates as an exit tax is unresolved.</li>
    <li><strong>Treaty interest rate</strong> — largely moot because savings interest is already exempt.</li>
    <li><strong>Penalty provision for virtual-currency conversion</strong> — the activity is prohibited; mapping it to a specific FX fine is legal characterisation, not a sourced fact.</li>
  </ul>
</section>
"""
    return head("Flagged for review") + body + foot()


# ----------------------------------------------------------------------------- exec summary page
def page_exec(md_html):
    body = f"""
<section class="pagehead">
  <h1>Executive summary</h1>
  <p class="lede">One page. The question, the answer, the numbers, the risks, and the order of operations.</p>
</section>
<article class="prose">
{md_html}
</article>
"""
    return head("Executive summary") + body + foot()


def md_to_html(md):
    """Small, dependency-free markdown subset renderer."""
    try:
        import markdown  # noqa
        return markdown.markdown(md, extensions=["tables", "toc"])
    except Exception:
        pass
    # fallback: minimal renderer
    lines = md.split("\n")
    out, in_tbl, in_ul, in_ol, in_p = [], False, False, False, False
    def close():
        nonlocal in_tbl, in_ul, in_ol, in_p
        if in_tbl: out.append("</tbody></table>"); in_tbl = False
        if in_ul: out.append("</ul>"); in_ul = False
        if in_ol: out.append("</ol>"); in_ol = False
        if in_p: out.append("</p>"); in_p = False
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            close(); i += 1; continue
        if ln.startswith("#"):
            close()
            lvl = len(ln) - len(ln.lstrip("#"))
            out.append(f"<h{lvl}>{esc(ln[lvl:].strip())}</h{lvl}>"); i += 1; continue
        if ln.startswith("|") and i + 1 < len(lines) and set(lines[i+1].replace("|","").replace(" ","")) <= set("-:"):
            close()
            hdr = [c.strip() for c in ln.strip("|").split("|")]
            out.append('<table class="tbl"><thead><tr>' + "".join(f"<th>{esc(h)}</th>" for h in hdr) + "</tr></thead><tbody>")
            in_tbl = True; i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in cells) + "</tr>")
                i += 1
            out.append("</tbody></table>"); in_tbl = False; continue
        if ln.startswith(("- ", "* ")):
            if not in_ul: close(); out.append("<ul>"); in_ul = True
            out.append(f"<li>{esc(ln[2:])}</li>"); i += 1; continue
        if ln[:3].strip().rstrip(".").isdigit():
            if not in_ol: close(); out.append("<ol>"); in_ol = True
            out.append(f"<li>{esc(ln.split('.',1)[1].strip())}</li>"); i += 1; continue
        if ln.startswith(">"):
            close(); out.append(f"<blockquote>{esc(ln[1:].strip())}</blockquote>"); i += 1; continue
        if not in_p: out.append("<p>"); in_p = True
        out.append(esc(ln)); i += 1
    close()
    return "\n".join(out)


def main():
    sources, methods, penalties, flagged = load()

    (ROOT / "index.html").write_text(page_index(methods, sources, penalties, flagged), encoding="utf-8")
    (ROOT / "methods.html").write_text(
        page_methods(methods, sources, "All channels",
                     lambda m: True,
                     "The full inventory. Every route this project could identify, whether lawful, conditional, "
                     "a non-transfer, or prohibited — with the limit, the tax treatment, the penalty, and the pros and cons."),
        encoding="utf-8")
    (ROOT / "lawful.html").write_text(
        page_methods(methods, sources, "Lawful and conditional routes",
                     lambda m: m["legality"] in ("lawful", "conditional", "not_a_transfer"),
                     "Routes that are permitted, either outright or on stated conditions. Note carefully which of these "
                     "do <em>not</em> actually move ownership of the money out of China — that distinction is the whole game."),
        encoding="utf-8")
    (ROOT / "prohibited.html").write_text(
        page_methods(methods, sources, "Prohibited routes",
                     lambda m: m["legality"] in ("prohibited", "unverified"),
                     "Routes that are criminal or administrative offences under PRC law, plus two intermediate products "
                     "that could not be verified. They are named and sourced so you can recognise them — not explained, "
                     "because a how-to would be assisting an offence."),
        encoding="utf-8")
    (ROOT / "penalty.html").write_text(page_penalty(penalties, sources), encoding="utf-8")
    (ROOT / "us-reporting.html").write_text(page_us(sources), encoding="utf-8")
    (ROOT / "sources.html").write_text(page_sources(sources), encoding="utf-8")
    (ROOT / "flagged.html").write_text(page_flagged(flagged, sources), encoding="utf-8")

    exec_md = (ROOT / "EXECUTIVE-SUMMARY.md").read_text(encoding="utf-8")
    (ROOT / "executive-summary.html").write_text(page_exec(md_to_html(exec_md)), encoding="utf-8")

    print("generated:")
    for p in ["index.html", "executive-summary.html", "methods.html", "lawful.html",
              "prohibited.html", "penalty.html", "us-reporting.html", "sources.html", "flagged.html"]:
        size = (ROOT / p).stat().st_size
        print(f"  {p:28} {size:>8,} bytes")


if __name__ == "__main__":
    main()
