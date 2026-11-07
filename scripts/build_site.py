# -*- coding: utf-8 -*-
"""Static site generator for the China CNY→USD research dossier.

Renders every page in docs/ from the Python data modules, so the tables on the site
and the tables in the markdown deliverables can never drift apart. Also:
  * writes machine-readable JSON exports into data/
  * performs an internal link check over the generated HTML
  * fails loudly if a page references an unknown source id
"""
import html
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_sources import SOURCES
from data_channels import CHANNELS
from data_costs import COSTS, HEADLINE
from data_taxes import TAXES
from data_flagged import FLAGGED

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
DATA = os.path.join(ROOT, "data")

SRC = {s["id"]: s for s in SOURCES}
BUILT = "2026-11-07"

# --------------------------------------------------------------------------
# validation
# --------------------------------------------------------------------------
errors = []

for row in CHANNELS + COSTS + TAXES + FLAGGED:
    for sid in row.get("basis", []) + row.get("sources", []):
        if sid not in SRC:
            errors.append(f"{row['id']}: unknown source id {sid}")

ids_seen = set()
for group, rows in (("channel", CHANNELS), ("cost", COSTS), ("tax", TAXES), ("flag", FLAGGED)):
    for r in rows:
        if r["id"] in ids_seen:
            errors.append(f"duplicate id {r['id']}")
        ids_seen.add(r["id"])

if errors:
    print("BUILD FAILED:")
    for e in errors:
        print("  -", e)
    sys.exit(1)

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def e(x):
    return html.escape(str(x), quote=True)


TAG_CLASS = {
    "VERIFIED": "ok",
    "PARTIAL": "warn",
    "UNVERIFIED": "bad",
}
TAG_LABEL = {
    "VERIFIED": "Verified",
    "PARTIAL": "Partly verified",
    "UNVERIFIED": "Unverified — values blank",
}


def tag(v):
    return f'<span class="tag {TAG_CLASS.get(v, "warn")}">{TAG_LABEL.get(v, e(v))}</span>'


def sev_tag(sev):
    cls = {"High": "bad", "Medium": "warn", "Low": "ok"}.get(sev, "warn")
    return f'<span class="tag {cls}">{e(sev)}</span>'


def srclink(sid, short=False):
    s = SRC[sid]
    label = sid if short else f'{sid} · {s["publisher"]}'
    return (f'<a class="src" href="{e(s["url"])}" target="_blank" rel="noopener" '
            f'title="{e(s["title"])}">{e(label)}</a>')


def srcrow(sid):
    return srclink(sid)


def blank_or(val, vstatus):
    if vstatus == "UNVERIFIED" and not val:
        return '<span class="blank">— blank (unverified)</span>'
    if not val:
        return '<span class="blank">— blank (unverified)</span>'
    return e(val)


def li(items, cls=""):
    return "".join(f"<li>{e(i)}</li>" for i in items)


NAV = [
    ("index.html", "Overview"),
    ("channels.html", "Routes"),
    ("costs.html", "Conversion cost"),
    ("taxes.html", "Tax matrix"),
    ("strategy.html", "What to do"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
    ("methodology.html", "Method"),
]

CSS = """
:root{
  --bg:#f6f7f9; --panel:#ffffff; --ink:#12161c; --muted:#5b6673; --line:#e3e7ec;
  --accent:#0b5fff; --accent-soft:#eaf1ff;
  --ok:#0a7a44; --ok-bg:#e7f6ee; --warn:#8a5a00; --warn-bg:#fdf3e2; --bad:#a01b2e; --bad-bg:#fdecef;
  --shadow:0 1px 2px rgba(16,24,40,.06),0 1px 3px rgba(16,24,40,.06);
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,Helvetica,Arial,sans-serif;}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
header.top{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:40}
.topin{display:flex;align-items:center;gap:22px;height:62px}
.brand{display:flex;align-items:center;gap:10px;font-weight:700;letter-spacing:-.2px;white-space:nowrap}
.brand .dot{width:26px;height:26px;border-radius:7px;background:linear-gradient(135deg,#0b5fff,#00c2a8);display:inline-block}
nav.main{display:flex;gap:2px;overflow-x:auto;scrollbar-width:none}
nav.main::-webkit-scrollbar{display:none}
nav.main a{padding:8px 11px;border-radius:8px;color:var(--muted);font-size:14.5px;font-weight:500;white-space:nowrap}
nav.main a:hover{background:var(--accent-soft);color:var(--accent);text-decoration:none}
nav.main a.on{background:var(--accent-soft);color:var(--accent);font-weight:600}
.hero{padding:44px 0 10px}
.kicker{display:inline-block;font-size:12.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;
  color:var(--accent);background:var(--accent-soft);padding:5px 11px;border-radius:999px}
h1{font-size:clamp(28px,4vw,40px);line-height:1.15;letter-spacing:-.02em;margin:16px 0 12px;font-weight:750}
h2{font-size:23px;letter-spacing:-.01em;margin:38px 0 12px;font-weight:700;scroll-margin-top:80px}
h3{font-size:17px;margin:26px 0 8px;font-weight:700}
p.lead{font-size:18.5px;color:var(--muted);max-width:80ch;margin:0 0 8px}
p{max-width:88ch}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:22px 24px;box-shadow:var(--shadow)}
.grid{display:grid;gap:16px}
.g2{grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
.g3{grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}
.g4{grid-template-columns:repeat(auto-fit,minmax(205px,1fr))}
.stat{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px 18px 16px;box-shadow:var(--shadow)}
.stat .big{font-size:31px;font-weight:750;letter-spacing:-.03em;line-height:1.1}
.stat .lab{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:7px 0 6px}
.stat .desc{font-size:14px;color:var(--muted)}
.stat.risk .big{color:var(--bad)}
.stat.ok .big{color:var(--ok)}
.stat.mid .big{color:var(--warn)}
table{width:100%;border-collapse:collapse;background:#fff;font-size:14.5px}
.tablecard{background:#fff;border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:var(--shadow);margin:16px 0 26px}
.tablecard .hd{padding:14px 18px;border-bottom:1px solid var(--line);display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}
.tablecard .hd h3{margin:0;font-size:16px}
.tablecard .hd .n{font-size:13px;color:var(--muted)}
.scroll{overflow-x:auto}
th,td{text-align:left;padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:top}
th{background:#f9fafb;font-size:12.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);font-weight:700;white-space:nowrap}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:#fcfdff}
td.num{font-variant-numeric:tabular-nums;white-space:nowrap}
.tag{display:inline-block;font-size:11.5px;font-weight:700;padding:2px 8px;border-radius:999px;white-space:nowrap;letter-spacing:.01em}
.tag.ok{color:var(--ok);background:var(--ok-bg)}
.tag.warn{color:var(--warn);background:var(--warn-bg)}
.tag.bad{color:var(--bad);background:var(--bad-bg)}
.tag.cat{color:#243b53;background:#eef2f6}
.blank{color:var(--bad);font-style:italic;font-size:13.5px}
.src{font-family:var(--mono);font-size:12px}
ul.tight{margin:6px 0 0;padding-left:20px}
ul.tight li{margin:3px 0;font-size:14px}
.pros li{color:#12452c}
.cons li{color:#7a1424}
details{border-top:1px solid var(--line);padding:12px 18px;background:#fcfdff}
details summary{cursor:pointer;font-weight:650;font-size:14.5px;color:var(--accent)}
details .inner{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));margin-top:12px}
details h4{margin:0 0 6px;font-size:13px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted)}
.note{border-left:3px solid var(--accent);background:var(--accent-soft);padding:14px 18px;border-radius:0 10px 10px 0;margin:18px 0}
.note.warn{border-color:#e2a33c;background:var(--warn-bg)}
.note.bad{border-color:#d9463f;background:var(--bad-bg)}
.note p{margin:6px 0}
.fork{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.fork .card{border-top:4px solid var(--accent)}
.fork .card.b{border-top-color:#00a37a}
footer{margin-top:60px;border-top:1px solid var(--line);background:#fff;padding:26px 0 40px;font-size:13.5px;color:var(--muted)}
footer p{max-width:none}
.mono{font-family:var(--mono);font-size:13px}
.chip{display:inline-block;font-size:12px;padding:2px 8px;border:1px solid var(--line);border-radius:999px;color:var(--muted);background:#fff}
ol.steps{counter-reset:s;list-style:none;padding:0;margin:14px 0}
ol.steps li{position:relative;padding:0 0 18px 46px;border-left:2px solid var(--line);margin-left:14px}
ol.steps li:last-child{border-left-color:transparent}
ol.steps li::before{counter-increment:s;content:counter(s);position:absolute;left:-15px;top:-2px;width:28px;height:28px;
  border-radius:50%;background:var(--accent);color:#fff;font-weight:700;font-size:14px;display:grid;place-items:center}
ol.steps b{display:block;font-size:15.5px;margin-bottom:2px}
.toc{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 0}
.toc a{font-size:13.5px;padding:6px 12px;border:1px solid var(--line);border-radius:999px;background:#fff;color:var(--muted)}
.toc a:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
@media(max-width:720px){
  .topin{height:auto;padding:10px 0;flex-wrap:wrap;gap:10px}
  h1{font-size:27px}
  table{font-size:13.5px}
  th,td{padding:9px 10px}
}
"""


def shell(title, active, body, desc=""):
    on = ' class="on"'
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (f, on if f == active else "", e(t)) for f, t in NAV
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)} · China CNY→USD</title>
<meta name="description" content="{e(desc)}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<header class="top"><div class="wrap topin">
  <a class="brand" href="index.html"><span class="dot"></span>China CNY&nbsp;→&nbsp;USD</a>
  <nav class="main">{nav}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">
<p><b>Research dossier, not advice.</b> Every legal proposition is traced to a published instrument with a link, and every number is either quoted from an official source or plainly labelled as derived from one. Values that could not be confirmed from an official source are left blank and listed on the <a href="flagged.html">Flagged for review</a> page. Built {BUILT}. For a live decision, engage a PRC-qualified lawyer for the China side and a US CPA or tax attorney for the US side.</p>
<p style="margin-top:10px"><a href="sources.html">Source registry</a> · <a href="methodology.html">Verification method</a> · <a href="https://github.com/sassnarep3-star/China1">Repository</a></p>
</div></footer>
</body>
</html>
"""


# --------------------------------------------------------------------------
# page: overview
# --------------------------------------------------------------------------
def page_index():
    stats = ""
    cls = ["ok", "ok", "ok", "mid", "risk"]
    for (big, lab, desc), c in zip(HEADLINE, cls):
        stats += (f'<div class="stat {c}"><div class="big">{e(big)}</div>'
                  f'<div class="lab">{e(lab)}</div><div class="desc">{e(desc)}</div></div>')

    cat_counts = {}
    for c in CHANNELS:
        cat_counts[c["cat"]] = cat_counts.get(c["cat"], 0) + 1
    cats = "".join(
        f'<div class="stat"><div class="big">{n}</div><div class="lab">{e(k)}</div></div>'
        for k, n in sorted(cat_counts.items())
    )

    body = f"""
<section class="hero">
  <span class="kicker">Research dossier · verified {BUILT}</span>
  <h1>Getting money out of China, with the smallest lawful penalty</h1>
  <p class="lead">A US citizen has CNY stuck in a mainland bank account and believes that converting it to USD costs a large amount in tax. This dossier tests that belief against the actual instruments — the PRC FX regulations, the Individual Income Tax Law, the US Internal Revenue Code and the IRS filing rules — and finds that the premise is the most expensive thing in the problem.</p>
  <div class="toc">
    <a href="#finding">The five findings</a>
    <a href="#fork">The decision fork</a>
    <a href="#numbers">The numbers</a>
    <a href="channels.html">All {len(CHANNELS)} routes</a>
    <a href="strategy.html">What to actually do</a>
    <a href="flagged.html">What is unverified</a>
  </div>
</section>

<h2 id="finding">The five findings</h2>
<div class="grid g2">
  <div class="card">
    <h3>1. There is no tax on converting your own money</h3>
    <p>Neither China nor the United States imposes a tax on an exchange of currency or on moving your own after-tax principal between your own accounts. China's Individual Income Tax Law taxes nine enumerated categories of <i>income</i> — wages, services, royalties, business income, interest/dividends, rent, property transfers, incidental gains. A transfer of principal is not one of them {srclink('CN-14')}. On the US side a transfer between your own accounts is not income, and a personal currency conversion is not even recognised as a gain unless it exceeds USD 200 {srclink('US-04')}.</p>
  </div>
  <div class="card">
    <h3>2. The real conversion cost is about 0.42%</h3>
    <p>Bank of China quoted USD at 666.48 (bid) and 669.29 (ask) CNY per 100 on 2026-11-08 {srclink('CN-11')}. That spread — the only cost of a lawful conversion that is actually a percentage — is <b>0.42%</b>, or about CNY 4,200 on a CNY 1,000,000 conversion. Wire fees are extra and are small on large amounts; where they could not be verified they are left blank.</p>
  </div>
  <div class="card">
    <h3>3. The binding constraint is legal, not fiscal</h3>
    <p>China's FX framework splits <i>current account</i> (convertible) from <i>capital account</i> (gradual, approval-based) {srclink('CN-01')}. Buying USD with the annual USD 50,000 quota is a current-account convenience; parking savings abroad is a capital-account act and is closed except through enumerated channels. This — not tax — is why the money is stuck.</p>
  </div>
  <div class="card">
    <h3>4. One fact decides everything: how the bank classifies you</h3>
    <p>A US citizen is <b>境外个人</b> unless the bank still holds a PRC 居民身份证 for them {srclink('CN-01')}. For 境外个人, Art. 59 of 汇发[2020]14号 allows a purchase against lawful China-source RMB income on ID plus source documents, with <b>no annual cap in the rule text</b> {srclink('CN-03')}. For 境内个人, the USD 50,000 annual quota governs. Same person, same money, two different countries' worth of difficulty.</p>
  </div>
  <div class="card">
    <h3>5. The only number that is genuinely dangerous is 50%</h3>
    <p>The Chinese penalties are administrative, capped at 30% of the amount (30%–100% for serious cases) {srclink('CN-08')}. The genuinely catastrophic exposure is the US willful-FBAR penalty: the greater of USD 100,000 or <b>50% of the account balance</b>, per year {srclink('US-03')}. Non-reporting, not conversion, is where a life's savings actually goes. Handle the reporting before touching the transfer.</p>
  </div>
  <div class="card">
    <h3>What this is not</h3>
    <p>It is not legal or tax advice, and it does not tell you to break a rule. It does list the unlawful routes, because they are what people are actually offered, and because the penalty for each is knowable. {srclink('CN-08')} Every value that could not be sourced from an official page is left blank and published on the <a href="flagged.html">Flagged for review</a> page.</p>
  </div>
</div>

<h2 id="fork">The decision fork</h2>
<p class="lead">Before any route is chosen, one question has to be answered at the bank counter.</p>
<div class="fork">
  <div class="card">
    <span class="chip">If the bank holds a PRC 居民身份证 → 境内个人</span>
    <h3>You are inside the USD 50,000 quota</h3>
    <ul class="tight">
      <li>Annual purchase cap: USD 50,000 per person per year {srclink('CN-02', True)}</li>
      <li>Above the cap: still possible, but only for a documented <i>current-account</i> purpose {srclink('CN-05', True)}</li>
      <li>Whole-balance exit: requires the capital-account route, or a change of status {srclink('CN-06', True)}</li>
      <li>Moving USD 50,000 per <i>day</i> out of an FX account is a separate, larger allowance {srclink('CN-04', True)}</li>
    </ul>
    <p><a href="strategy.html">Which route →</a></p>
  </div>
  <div class="card b">
    <span class="chip">If the bank holds a US passport → 境外个人</span>
    <h3>The quota does not bind you in the rule text</h3>
    <ul class="tight">
      <li>Buy FX against lawful China-source RMB income with ID + source documents {srclink('CN-03', True)}</li>
      <li>Remit FX already in the account on ID alone {srclink('CN-03', True)}</li>
      <li>Property-sale proceeds out with SAFE approval {srclink('CN-01', True)}</li>
      <li>Bank branches vary — get refusals in writing (see flagged item F16)</li>
    </ul>
    <p><a href="strategy.html">Which route →</a></p>
  </div>
</div>

<h2 id="numbers">The numbers, with nothing invented</h2>
<div class="grid g4">{stats}</div>
<p style="margin-top:14px;color:var(--muted);font-size:14px">Read the full decomposition — including every item left blank — on <a href="costs.html">Conversion cost</a>.</p>

<h2>Scope of what was reviewed</h2>
<div class="grid g3">
  <div class="stat"><div class="big">{len(CHANNELS)}</div><div class="lab">Routes mapped</div><div class="desc">Current-account, capital-account, cash &amp; cards, keep-in-place, and the unlawful ones people are actually offered.</div></div>
  <div class="stat"><div class="big">{len(TAXES)}</div><div class="lab">Tax positions</div><div class="desc">Separated by jurisdiction, because the two sides answer different questions.</div></div>
  <div class="stat"><div class="big">{len(COSTS)}</div><div class="lab">Cost lines</div><div class="desc">Each one quoted, derived, or left blank and flagged.</div></div>
  <div class="stat"><div class="big">{len(SOURCES)}</div><div class="lab">Official sources</div><div class="desc">Regulators, statutes and the issuing authority's own pages.</div></div>
  <div class="stat"><div class="big">{len(FLAGGED)}</div><div class="lab">Flagged items</div><div class="desc">Gaps left blank on purpose, and irregularities found while verifying.</div></div>
  <div class="stat"><div class="big">{sum(1 for c in CHANNELS if c['vstatus']=='VERIFIED')}</div><div class="lab">Fully verified rows</div><div class="desc">Route and every stated number traceable to a tier-A page.</div></div>
</div>

<h2>How to read the tables</h2>
<div class="tablecard">
  <div class="scroll"><table>
    <thead><tr><th>Badge</th><th>Meaning</th></tr></thead>
    <tbody>
      <tr><td>{tag('VERIFIED')}</td><td>The rule and every number in the row is quoted from a primary instrument or the issuing authority's own page.</td></tr>
      <tr><td>{tag('PARTIAL')}</td><td>The route exists in an official source, but a limit or an institution's offer could not be pinned to one. Blank cells stay blank.</td></tr>
      <tr><td>{tag('UNVERIFIED')}</td><td>No official source found this session. Every value in the row is deliberately empty.</td></tr>
    </tbody>
  </table></div>
</div>
"""
    return shell("Overview", "index.html", body,
                 "Verified research on converting CNY to USD: routes, costs, tax treatment, and what is unverified.")


# --------------------------------------------------------------------------
# page: channels
# --------------------------------------------------------------------------
def page_channels():
    groups = {}
    for c in CHANNELS:
        groups.setdefault(c["cat"], []).append(c)

    order = sorted(groups.keys())
    def anchor_of(k):
        return re.sub(r"^([A-Z])\..*", r"\1", k)
    toc = "".join(
        '<a href="#%s">%s (%d)</a>' % (e(anchor_of(k)), e(k), len(groups[k])) for k in order
    )

    out = [f"""
<section class="hero">
  <span class="kicker">{len(CHANNELS)} routes</span>
  <h1>Every route from CNY to USD</h1>
  <p class="lead">Grouped by the legal category that actually governs them. The grouping is the analysis: a current-account route and a capital-account route are not interchangeable, and a route in group D is not a cheaper option, it is a different legal universe.</p>
  <div class="toc">{toc}</div>
</section>
"""]

    for g in order:
        anchor = anchor_of(g)
        out.append(f'<h2 id="{e(anchor)}">{e(g)}</h2>')
        out.append('<div class="tablecard"><div class="scroll"><table>')
        out.append("<thead><tr><th>Route</th><th>Applies to</th><th>Cap / limit</th><th>Status</th></tr></thead><tbody>")
        for c in groups[g]:
            out.append(
                f'<tr><td><b>{e(c["name"])}</b><br><span style="color:var(--muted);font-size:13px">{e(c["name_zh"])}</span></td>'
                f'<td>{e(c["who"])}</td>'
                f'<td>{blank_or(c["cap"], c["vstatus"])}</td>'
                f'<td>{tag(c["vstatus"])}<br><span class="mono">{e(c["id"])}</span></td></tr>'
            )
            out.append(
                f'<tr><td colspan="4" style="padding:0;background:#fcfdff">'
                f'<details><summary>Detail, pros and cons — {e(c["id"])}</summary><div class="inner">'
                f'<div><h4>Documents</h4><p>{blank_or(c["docs"], c["vstatus"])}</p></div>'
                f'<div><h4>Cost</h4><p>{blank_or(c["cost"], c["vstatus"])}</p></div>'
                f'<div><h4>Chinese tax treatment</h4><p>{blank_or(c["tax_cn"], c["vstatus"])}</p></div>'
                f'<div><h4>US tax treatment</h4><p>{blank_or(c["tax_us"], c["vstatus"])}</p></div>'
                f'<div><h4>Pros</h4><ul class="tight pros">{li(c["pros"])}</ul></div>'
                f'<div><h4>Cons</h4><ul class="tight cons">{li(c["cons"])}</ul></div>'
                f'<div><h4>Sources</h4><p>{"<br>".join(srcrow(s) for s in c["basis"]) if c["basis"] else "<i>No official source found — see the Flagged page.</i>"}</p></div>'
                f'</div></details></td></tr>'
            )
        out.append("</tbody></table></div></div>")

    out.append("""
<div class="note warn">
<p><b>Why the unlawful routes are listed at all.</b> Because they are what a bank clerk, a friend or a WeChat group will suggest first, and because the penalty for each is a knowable number rather than a vague warning. Listing them is not an endorsement; the strategy page never selects one.</p>
</div>
<div class="note">
<p><b>Reading a "no annual cap" claim carefully.</b> Where a row says no annual cap, the claim is that the <i>rule text</i> contains no cap — not that any bank will process any amount. Bank-level source-of-funds review is the real constraint, and it is flagged as irregularity F16.</p>
</div>
""")
    return shell("Routes", "channels.html", "\n".join(out),
                 "Every lawful and unlawful route for converting CNY to USD, grouped by the legal category that governs it.")


# --------------------------------------------------------------------------
# page: costs
# --------------------------------------------------------------------------
def page_costs():
    bands = {}
    for k in COSTS:
        bands.setdefault(k["band"], []).append(k)

    head = "".join(
        f'<div class="stat {"ok" if i in (0,1,2) else ("risk" if i==4 else "mid")}">'
        f'<div class="big">{e(b)}</div><div class="lab">{e(l)}</div><div class="desc">{e(d)}</div></div>'
        for i, (b, l, d) in enumerate(HEADLINE)
    )

    out = [f"""
<section class="hero">
  <span class="kicker">Penalty breakdown</span>
  <h1>What the conversion actually costs</h1>
  <p class="lead">The brief asked for the conversion penalty to be broken down. Here it is, line by line, split into the cost you cannot avoid, the Chinese tax that is real but unrelated to converting, and the penalty exposure you only meet by skipping a lawful route.</p>
</section>
<div class="grid g4" style="margin-bottom:8px">{head}</div>
<div class="note">
<p><b>The arithmetic behind the 0.42%.</b> Bank of China's own board on 2026-11-08 quoted USD at a 现汇买入价 of 666.48 and a 现汇卖出价 of 669.29 CNY per 100 USD {srclink('CN-11')}. Dividing the 2.81 CNY gap by the price you pay (669.29) gives 0.4199%. That is the round-trip cost of a single conversion at one of China's four largest banks, and it is the largest percentage cost of a lawful conversion anywhere in this dossier.</p>
</div>
"""]

    for band in sorted(bands.keys()):
        out.append(f'<h2>{e(band)}</h2>')
        out.append('<div class="tablecard"><div class="scroll"><table>')
        out.append("<thead><tr><th>Item</th><th>Value</th><th>Derivation / rule</th><th>On CNY 1,000,000</th><th>Status</th></tr></thead><tbody>")
        for k in bands[band]:
            one_m = blank_or(k["on1m"], k["vstatus"]) if k["on1m"] else '<span class="blank">—</span>'
            out.append(
                f'<tr><td><b>{e(k["item"])}</b><br><span class="mono" style="color:var(--muted)">{e(k["id"])}</span></td>'
                f'<td class="num">{blank_or(k["value"], k["vstatus"])}</td>'
                f'<td>{e(k["how"])}<br>{" ".join(srcrow(s) for s in k["basis"])}</td>'
                f'<td class="num">{one_m}</td>'
                f'<td>{tag(k["vstatus"])}</td></tr>'
            )
        out.append("</tbody></table></div></div>")

    out.append("""
<h2>What this decomposition shows</h2>
<div class="grid g2">
  <div class="card">
    <h3>The lawful route is cheap</h3>
    <p>Add the verified percentage items and a lawful conversion costs roughly 0.4%–0.5% of principal, plus fixed wire charges that are small relative to a large balance. On CNY 1,000,000 that is about CNY 4,200 of spread. There is no 20% conversion tax in either jurisdiction.</p>
  </div>
  <div class="card">
    <h3>The 20% is real — but it belongs to the gain</h3>
    <p>If the CNY came from selling a property, 20% of the <i>gain</i> was always owed under the Individual Income Tax Law, and no remittance route avoids it. If it came from salary, the tax was already withheld. If it is deposit interest, 20% is withheld at source. This is why identifying the source of funds (flagged item F03) matters more than choosing a channel.</p>
  </div>
  <div class="card">
    <h3>The penalties are where the money goes</h3>
    <p>A 30%-of-the-amount Chinese fine for evasion, or a 50%-of-the-balance US willful-FBAR penalty, dwarfs a 0.42% spread by two orders of magnitude. Skipping a lawful route to save four tenths of a percent is the worst trade in the entire problem.</p>
  </div>
  <div class="card">
    <h3>Six lines are deliberately blank</h3>
    <p>Wire commission, correspondent charges, the receiving bank's inbound fee, notarisation cost, the deposit rate and the USD rate could not be confirmed from a tier-A source in this session. Rather than put a plausible-looking number in the table, they are empty and published on the <a href="flagged.html">Flagged for review</a> page.</p>
  </div>
</div>
""")
    return shell("Conversion cost", "costs.html", "\n".join(out),
                 "Line-by-line breakdown of the CNY to USD conversion penalty: spread, Chinese tax, and penalty exposure.")


# --------------------------------------------------------------------------
# page: taxes
# --------------------------------------------------------------------------
def page_taxes():
    cn = [t for t in TAXES if t["side"] == "China"]
    us = [t for t in TAXES if t["side"] == "United States"]

    def tbl(rows, heading):
        o = [f'<h2>{e(heading)}</h2><div class="tablecard"><div class="scroll"><table>',
             "<thead><tr><th>Question</th><th>Rate / result</th><th>Rule and source</th><th>Status</th></tr></thead><tbody>"]
        for t in rows:
            o.append(
                f'<tr><td><b>{e(t["topic"])}</b><br><span class="mono" style="color:var(--muted)">{e(t["id"])}</span></td>'
                f'<td><b>{e(t["rate"])}</b></td>'
                f'<td>{e(t["rule"])}<br><span style="color:var(--muted);font-size:13.5px"><i>Consequence:</i> {e(t["consequence"])}</span>'
                f'<br>{" ".join(srcrow(s) for s in t["basis"])}</td>'
                f'<td>{tag(t["vstatus"])}</td></tr>'
            )
        o.append("</tbody></table></div></div>")
        return "\n".join(o)

    body = f"""
<section class="hero">
  <span class="kicker">Two jurisdictions, two different questions</span>
  <h1>Tax matrix</h1>
  <p class="lead">China asks "is this income, and has it been taxed?" The United States asks "is this income, and have you disclosed the account?" Neither asks "how much tax is due on the conversion?" — because neither taxes it.</p>
</section>

<div class="note">
<p><b>The single most useful sentence in this dossier.</b> China's Individual Income Tax Law lists nine chargeable categories of income {srclink('CN-14')}. Moving your own already-taxed principal from a Chinese account to a US account is not one of the nine. The US treats a transfer between your own accounts as neither income nor gift, and does not recognise personal-currency exchange-rate gain below USD 200 {srclink('US-04')}.</p>
</div>

{tbl(cn, "China side")}
{tbl(us, "United States side")}

<h2>The reporting stack, in one table</h2>
<p>These four obligations run in parallel. Completing one does not satisfy any other, and each has its own penalty.</p>
<div class="tablecard"><div class="scroll"><table>
<thead><tr><th>Filing</th><th>Trigger</th><th>Filed with</th><th>Deadline</th><th>Penalty ceiling</th></tr></thead>
<tbody>
<tr><td><b>FinCEN Form 114 (FBAR)</b></td><td>Aggregate foreign accounts over USD 10,000 at any point in the calendar year</td><td>FinCEN (BSA E-Filing), not the IRS</td><td>15 April, automatic extension to 15 October</td><td>Non-willful up to USD 10,000; willful greater of USD 100,000 or 50% of the balance {srclink('US-01', True)}</td></tr>
<tr><td><b>Form 8938</b></td><td>Specified foreign financial assets above the filing-status threshold</td><td>IRS, attached to the return</td><td>With the return, including extensions</td><td>USD 10,000 plus USD 10,000 per 30 days after notice, max USD 60,000 {srclink('US-01', True)}</td></tr>
<tr><td><b>Schedule B, Part III</b></td><td>Any foreign financial account or signature authority</td><td>IRS, on the return</td><td>With the return</td><td>Part of the return's accuracy penalty exposure {srclink('US-07', True)}</td></tr>
<tr><td><b>Form 3520, Part IV</b></td><td>Gifts or bequests from foreign persons above the threshold</td><td>IRS, filed separately</td><td>With the return, including extensions</td><td>5% of the amount per month, capped at 25% {srclink('US-05', True)}</td></tr>
<tr><td><b>FinCEN Form 105</b></td><td>Currency or monetary instruments over USD 10,000 carried into or out of the US</td><td>CBP</td><td>At the time of transport</td><td>Seizure of the entire amount plus civil and criminal penalties {srclink('US-11', True)}</td></tr>
</tbody></table></div></div>

<div class="note bad">
<p><b>Do this first, before moving anything.</b> If the account has existed for years without FBAR or Form 8938 filings, a large inbound transfer is the event most likely to draw attention to the gap — and the penalty for the gap is calculated on the balance, not on what you moved. Get the filing history reviewed before the transfer, not after. See flagged item F04.</p>
</div>
"""
    return shell("Tax matrix", "taxes.html", body,
                 "Chinese and US tax treatment of converting CNY to USD, plus the full US reporting stack.")


# --------------------------------------------------------------------------
# page: strategy
# --------------------------------------------------------------------------
def page_strategy():
    body = """
<section class="hero">
  <span class="kicker">Sequenced, not ranked by headline rate</span>
  <h1>What to actually do</h1>
  <p class="lead">The right answer is not a single channel. It is a sequence: establish the facts, fix the US reporting, then move the money through the route that matches where it came from. Doing these out of order is what creates the losses.</p>
</section>

<ol class="steps">
  <li><b>Establish what the bank thinks you are</b>
    Ask, in writing, for the account's 账户主体类别 (境内个人 or 境外个人) and which identity document is on file. This is not a formality: it determines whether the USD 50,000 annual quota applies at all. <a href="channels.html#A">See routes A1–A5</a> · flagged item F01.</li>

  <li><b>Fix the US filing position before the money moves</b>
    Confirm the FBAR, Form 8938 and Schedule B history. If there are gaps, deal with them while the balance is still small enough to matter less — the willful penalty is 50% of the balance per year, and a large inbound transfer is what invites the question. flagged item F04.</li>

  <li><b>Identify where the money came from, tranche by tranche</b>
    Salary already taxed in China → the current-account route. Property sale → SAFE approval plus 20% IIT on the gain. Inheritance → 继承转移. Unused inward remittance → return it. Investment gain → capital account. The route follows the source; it cannot precede it. flagged item F03.</li>

  <li><b>Match the route to the category, not to the rumour</b>
    For a 境外个人 whose balance is lawful China-source income, routes <a href="channels.html#A">A3 and A4</a> are the strongest in the entire dossier, because the rule text imposes no annual cap and requires only ID plus source documents. For a 境内个人, <a href="channels.html#A">A1/A2</a> handle current-account needs and <a href="channels.html#B">B1</a> is the only general capital-account exit.</li>

  <li><b>Convert once, at the best quote you can get, and wire directly</b>
    Converting twice (CNY→USD→something→USD) doubles the 0.42% spread for no benefit. Avoid cash: it is the most expensive form and it triggers a customs reporting duty at the US end above USD 10,000. <a href="costs.html">Cost breakdown</a>.</li>

  <li><b>Report the arrival</b>
    The receiving US account is not reportable as a foreign account, but the Chinese account remains reportable for every year it exists, including the year you empty it. File for that year. <a href="taxes.html">Tax matrix</a>.</li>

  <li><b>Do not use group D</b>
    Splitting across relatives' quotas, underground banks, stablecoins, fabricated invoices and undeclared cash are all penalised by name in instruments linked from this site. Each converts a 0.42% cost into a 30%–100% or 50%-of-balance loss. <a href="channels.html#D">Group D</a>.</li>
</ol>

<h2>Ranked by outcome for the fact pattern in the brief</h2>
<p class="lead">A US citizen, CNY in a mainland bank account, no desire to break a rule. The ranking below is by expected net outcome, not by effort.</p>

<div class="grid g2">
  <div class="card" style="border-top:4px solid var(--ok)">
    <span class="tag ok">Best available, if the facts fit</span>
    <h3>境外个人 current-account purchase and remit — A3 / A4</h3>
    <p>If the bank holds a US passport and the balance is lawful China-source income that has already borne Chinese tax, this is the route the regulation actually provides. No annual cap appears in the text, and the documentary burden is source-of-funds evidence, which a US citizen should be able to produce anyway for their own US filings.</p>
    <p><b>Estimated cost:</b> ~0.42% spread plus fixed wire charges. <b>Estimated tax:</b> none on the transfer. <b>Main risk:</b> branch-level discretion — flagged F16.</p>
  </div>

  <div class="card" style="border-top:4px solid var(--ok)">
    <span class="tag ok">Best available for a whole balance</span>
    <h3>Emigration asset transfer — B1</h3>
    <p>If the person has genuinely emigrated from the PRC and can produce a hukou cancellation certificate plus an authenticated foreign-settlement certificate, this is the only written-in-law route that moves an entire personal balance. It is staged over up to two years, and a declared total of CNY 200,000 or less can be released at once.</p>
    <p><b>Estimated cost:</b> spread plus notarisation/translation. <b>Estimated tax:</b> none on the transfer, but a tax clearance is mandatory. <b>Main risk:</b> the owning-before-emigration test — flagged F17.</p>
  </div>

  <div class="card">
    <span class="tag warn">Right answer for a dollar need</span>
    <h3>Consume it rather than repatriate it — C3 / E3</h3>
    <p>If the underlying need is "pay US tuition, US medical bills, US insurance, US travel", a mainland-issued card settles those abroad directly, consumes no quota, requires no approval and creates no taxable event. For a household with recurring USD expenses this is often worth more than any transfer scheme.</p>
    <p><b>Estimated cost:</b> card-network rate plus any issuing-bank FX fee (not verified). <b>Estimated tax:</b> none.</p>
  </div>

  <div class="card">
    <span class="tag warn">Slow but lawful</span>
    <h3>Stage it through the annual quota — A1 / E4</h3>
    <p>USD 50,000 per person per year, ID only, over the phone. Perfectly lawful for genuine current-account uses and the least administrative effort of any route. But USD 500,000 takes a decade, and each year's declared purpose has to be honest.</p>
    <p><b>Estimated cost:</b> ~0.42% per conversion. <b>Main risk:</b> a decade of currency exposure dwarfing the spread saved.</p>
  </div>

  <div class="card" style="border-top:4px solid var(--bad)">
    <span class="tag bad">Never</span>
    <h3>Group D — the routes people are offered</h3>
    <p>Splitting across relatives' quotas is prohibited by name and gets the person watch-listed. Underground banks and mirror trades carry a fine of up to 30% of the amount, or 30%–100% for serious cases. Stablecoin bridges are classified as illegal financial activity. Fabricated invoices are 逃汇 with the same penalty band. Undeclared cash is forfeited in full at the US border.</p>
    <p><b>Estimated cost:</b> 30% to 100% of the amount, or 50% of the balance in the US willful case. This is the only place a "considerable amount" genuinely appears.</p>
  </div>

  <div class="card" style="border-top:4px solid var(--bad)">
    <span class="tag bad">Not a solution</span>
    <h3>Renouncing citizenship, or moving it through crypto</h3>
    <p>Renunciation creates a mark-to-market exit tax under §877A, which is a far bigger event than the one being avoided. A crypto bridge is illegal financial activity on the China side and creates two taxable dispositions plus a reportable offshore exchange account on the US side.</p>
  </div>
</div>

<h2>What would change the answer</h2>
<div class="tablecard"><div class="scroll"><table>
<thead><tr><th>If this were true…</th><th>…the answer becomes</th></tr></thead>
<tbody>
<tr><td>The bank still holds a PRC 居民身份证</td><td>You are inside the USD 50,000 quota and routes A3/A4 are unavailable until the classification is corrected — which is itself a legal question (flagged F02).</td></tr>
<tr><td>The balance came from a property sale</td><td>20% IIT on the gain is unavoidable, and the exit requires SAFE approval under Art. 22 (route A7), not a current-account purchase.</td></tr>
<tr><td>The balance is inherited</td><td>Route B2, with a Chinese consular certificate of foreign settlement and a Form 3520 filing in the US.</td></tr>
<tr><td>The money is in a Chinese fund or investment-linked insurance</td><td>PFIC exposure on the US side may exceed every other cost in this dossier. Classify the product before doing anything.</td></tr>
<tr><td>There are unfiled FBARs</td><td>Nothing should move until the history is reviewed. The exposure is 50% of the balance, per year.</td></tr>
</tbody></table></div></div>
"""
    return shell("What to do", "strategy.html", body,
                 "A sequenced, source-based plan for moving CNY to USD lawfully with the smallest penalty.")


# --------------------------------------------------------------------------
# page: flagged
# --------------------------------------------------------------------------
def page_flagged():
    gaps = [f for f in FLAGGED if f["kind"] == "GAP"]
    irr = [f for f in FLAGGED if f["kind"] == "IRREG"]

    def tbl(rows, title, blurb):
        o = [f'<h2>{e(title)}</h2><p class="lead">{blurb}</p>',
             '<div class="tablecard"><div class="scroll"><table>',
             "<thead><tr><th>Ref</th><th>Severity</th><th>Item</th><th>What is unclear / missing</th><th>What you should do</th><th>Sources</th></tr></thead><tbody>"]
        for f in rows:
            o.append(
                f'<tr><td class="mono"><b>{e(f["id"])}</b></td>'
                f'<td>{sev_tag(f["severity"])}</td>'
                f'<td><b>{e(f["item"])}</b><br><span style="color:var(--muted);font-size:13px">{e(f["why_it_matters"])}</span></td>'
                f'<td>{e(f["detail"])}</td>'
                f'<td>{e(f["action"])}</td>'
                f'<td>{"<br>".join(srcrow(s) for s in f["sources"]) if f["sources"] else "<i>none</i>"}</td></tr>'
            )
        o.append("</tbody></table></div></div>")
        return "\n".join(o)

    body = f"""
<section class="hero">
  <span class="kicker">{len(FLAGGED)} items · nothing here blocks publication</span>
  <h1>Flagged for review</h1>
  <p class="lead">Two kinds of entry live here. <b>Gaps</b> are values that could not be confirmed from an official source — they are left blank everywhere on this site rather than estimated. <b>Irregularities</b> are ambiguities, contradictions and practice-versus-rule divergences noticed while verifying. Review these after the site is live and request changes.</p>
</section>

<div class="note warn">
<p><b>Nothing on this page has been filled in.</b> Where a number was unavailable, the table cells on the other pages say "blank (unverified)". No midpoint, no typical range, no "industry average" has been substituted anywhere in this project.</p>
</div>

{tbl(gaps, "Gaps — values deliberately left blank", "Each of these would materially improve the answer if it could be sourced. None of them could be, from an official page, in this session.")}
{tbl(irr, "Irregularities found while verifying", "These are the places where the documents themselves, or the practice around them, do not line up neatly.")}

<h2>What is NOT flagged</h2>
<p>For clarity about what has been verified rather than merely asserted: the USD 50,000 annual figure, the USD 50,000 daily remittance line, the three-tier cash-carry permit ladder, the CNY 20,000 RMB cash limit, the CNY 10,000/day and CNY 100,000/year card-withdrawal caps, the CNY 200,000 one-shot and CNY 500,000 approval thresholds in the emigration-transfer procedure, the two-year staged release, the 20% IIT rates, the 30%/30%-100% FX penalty bands, the USD 10,000 FBAR threshold, the FBAR and Form 8938 penalty ceilings, the USD 10,000 FinCEN 105 threshold, the 20% Form 3520 penalty ceiling, and the 0.42% spread are all traced to a linked official source. Click any source tag to read the instrument itself.</p>
"""
    return shell("Flagged for review", "flagged.html", body,
                 "Unverified values and irregularities found while researching CNY to USD conversion.")


# --------------------------------------------------------------------------
# page: sources
# --------------------------------------------------------------------------
def page_sources():
    tiers = {
        "A": ("Primary instruments and issuing-authority pages",
              "Statutes, regulations, regulator guidance and the filing authority's own pages. These carry the weight of the dossier."),
        "B": ("Official publications of an authority on another official domain",
              "Gazette republications and state news agency reports of the instrument itself. Used only where the primary page was not retrievable."),
        "C": ("Regulated institutions publishing their own data",
              "Bank rate boards, exchange benchmarks. Authoritative for the institution's own numbers, not for policy."),
    }

    by_tier = {}
    for s in SOURCES:
        by_tier.setdefault(s["tier"], []).append(s)

    out = [f"""
<section class="hero">
  <span class="kicker">{len(SOURCES)} sources · all opened during this session</span>
  <h1>Source registry</h1>
  <p class="lead">Every row on this site points back into this list. Nothing in this project is sourced to a law-firm blog, a news aggregator or an SEO tax site — where a fact could only be found on one of those, it went to the <a href="flagged.html">Flagged</a> page instead of onto a table.</p>
</section>
"""]

    for t in ["A", "B", "C"]:
        rows = by_tier.get(t, [])
        if not rows:
            continue
        title, blurb = tiers[t]
        out.append(f'<h2>Tier {t} — {e(title)}</h2><p class="lead">{e(blurb)}</p>')
        out.append('<div class="tablecard"><div class="scroll"><table>')
        out.append("<thead><tr><th>Ref</th><th>Document</th><th>What it verifies</th><th>Link</th></tr></thead><tbody>")
        for s in rows:
            alt = (f'<br><span class="mono" style="font-size:11.5px">alt: '
                   f'<a href="{e(s["url_alt"])}" target="_blank" rel="noopener">{e(s["url_alt"])}</a></span>'
                   if s.get("url_alt") else "")
            out.append(
                f'<tr id="{e(s["id"])}"><td class="mono"><b>{e(s["id"])}</b></td>'
                f'<td><b>{e(s["title"])}</b><br><span style="color:var(--muted);font-size:13px">{e(s["publisher"])} · {e(s["lang"])}</span>'
                f'<br><span class="mono" style="font-size:12px;color:var(--muted)">{e(s["key_text"][:340])}{"…" if len(s["key_text"])>340 else ""}</span></td>'
                f'<td>{e(s["verifies"])}</td>'
                f'<td><a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["url"])}</a>{alt}</td></tr>'
            )
        out.append("</tbody></table></div></div>")

    out.append("""
<h2>Sources deliberately rejected</h2>
<p>Numerous search results during this session were law-firm marketing pages, accounting blogs and news aggregators stating FBAR penalty figures, Form 3520 thresholds and Chinese quota rules. Several of them disagreed with each other and at least two disagreed with the statute. They were not used, and no number in this dossier depends on one. Where they were the only source available for a fact, that fact is blank and flagged.</p>
""")
    return shell("Sources", "sources.html", "\n".join(out),
                 "Registry of every official source used, with links and what each one verifies.")


# --------------------------------------------------------------------------
# page: methodology
# --------------------------------------------------------------------------
def page_methodology():
    body = f"""
<section class="hero">
  <span class="kicker">How this was built</span>
  <h1>Verification method</h1>
  <p class="lead">The brief required line-by-line verification against official sources, with nothing inferred and nothing filled in. This page states exactly how that was done, and where the method has limits.</p>
</section>

<h2>The rules this project followed</h2>
<div class="tablecard"><div class="scroll"><table>
<thead><tr><th>Rule</th><th>How it was applied</th></tr></thead>
<tbody>
<tr><td><b>Every number has an official source</b></td><td>Each value in the route, cost and tax tables is either quoted from a tier-A instrument (or a tier-C institution for that institution's own quote) and linked, or independently derived by arithmetic on a quoted value and labelled "derived".</td></tr>
<tr><td><b>Nothing is inferred</b></td><td>Where a rule could not be read directly, the cell says "blank (unverified)" and the item appears on the <a href="flagged.html">Flagged</a> page. There is no midpoint, range, "typically" or "around" anywhere in a numeric cell.</td></tr>
<tr><td><b>Quotation over paraphrase</b></td><td>The source registry stores the operative Chinese text (article and clause) alongside the link, so a reader can check the sentence rather than trust a summary. The Chinese is kept in the original because translation changes meaning in this field.</td></tr>
<tr><td><b>Three-tier source grading</b></td><td>Tier A: the instrument or the issuing authority's own page. Tier B: an official republication of the instrument. Tier C: a regulated institution's own data. Nothing below tier C is used for a factual claim.</td></tr>
<tr><td><b>Negative findings stated as such</b></td><td>"There is no Chinese exit tax" is recorded as a negative finding from the charging provisions of the IIT Law, not as proof that no administrative practice exists anywhere. It is marked PARTIAL for that reason.</td></tr>
<tr><td><b>Unlawful routes included and labelled</b></td><td>Documenting a prohibited route with its statutory penalty is not advice to use it. Omitting them would leave the reader unable to recognise the option they are about to be offered.</td></tr>
</tbody></table></div></div>

<h2>Reproducibility</h2>
<p>All content lives in Python data modules under <span class="mono">scripts/</span>, and the pages are generated from them by <span class="mono">scripts/build_site.py</span>. The generator refuses to build if a table row cites a source id that does not exist, or if two rows share an id. The same data is exported to <span class="mono">data/*.json</span> so the tables can be re-used without scraping the HTML.</p>
<p>The build also runs an internal link check across every generated page and fails on any internal <span class="mono">href</span> that does not resolve to a file that exists.</p>

<h2>Known limits of the method</h2>
<div class="grid g2">
  <div class="card"><h3>Dynamic values</h3><p>The FX spread is a live quotation. It was captured on 2026-11-08 from Bank of China's published board and will move daily. The <i>structure</i> of the cost is stable; the number is a snapshot. The page states the capture time so the snapshot can be re-checked.</p></div>
  <div class="card"><h3>Bank practice</h3><p>Regulation and bank practice diverge in this field, in both directions. The dossier analyses the rule text and flags the divergence rather than pretending to know what a particular branch will do. See F16.</p></div>
  <div class="card"><h3>Untranslated instruments</h3><p>The PRC instruments are not officially translated. Key clauses are reproduced in Chinese so they can be checked against the linked page rather than against this site's paraphrase.</p></div>
  <div class="card"><h3>Not advice</h3><p>Application to a specific person requires a PRC-qualified lawyer and a US CPA or tax attorney. Cross-border work of this kind is routinely done by a pair. See F19.</p></div>
  <div class="card"><h3>Currency of the law</h3><p>The framework instruments in use are: PBOC Order No. 3 [2006], 汇发[2007]1号, 汇发[2020]14号, PBOC Announcement [2004] No. 16, State Council Order No. 532, 国家税务总局/外汇局公告2013年第40号, and the 2018 IIT Law. SAFE FAQ pages dated 2026 confirm the 2020 guidance is still the operative reading.</p></div>
  <div class="card"><h3>What would change the answer</h3><p>Three facts: how the bank classifies the account holder, where the money came from, and whether the US filings are current. The dossier is built so that each of those forks is visible rather than buried.</p></div>
</div>
"""
    return shell("Method", "methodology.html", body,
                 "Verification method, source grading, reproducibility and known limits.")


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
def main():
    if os.path.isdir(DOCS):
        shutil.rmtree(DOCS)
    os.makedirs(os.path.join(DOCS, "assets"), exist_ok=True)
    os.makedirs(DATA, exist_ok=True)

    with open(os.path.join(DOCS, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(CSS)

    pages = {
        "index.html": page_index(),
        "channels.html": page_channels(),
        "costs.html": page_costs(),
        "taxes.html": page_taxes(),
        "strategy.html": page_strategy(),
        "flagged.html": page_flagged(),
        "sources.html": page_sources(),
        "methodology.html": page_methodology(),
    }
    for name, content in pages.items():
        with open(os.path.join(DOCS, name), "w", encoding="utf-8") as f:
            f.write(content)

    # JSON exports
    exports = {
        "sources.json": SOURCES,
        "channels.json": CHANNELS,
        "costs.json": {"headline": [{"value": a, "label": b, "note": c} for a, b, c in HEADLINE],
                       "items": COSTS},
        "taxes.json": TAXES,
        "flagged.json": FLAGGED,
    }
    for name, obj in exports.items():
        with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)

    # link check
    internal = set(os.listdir(DOCS))
    bad = []
    for name, content in pages.items():
        for href in re.findall(r'href="([^"#][^"]*)"', content):
            if href.startswith(("http://", "https://", "mailto:")):
                continue
            target = href.split("#")[0]
            if target and target not in internal and not os.path.exists(os.path.join(DOCS, target)):
                bad.append(f"{name} -> {href}")
    # anchor check
    for name, content in pages.items():
        anchors = set(re.findall(r'id="([^"]+)"', content))
        for page, anchor in re.findall(r'href="([a-z0-9_]+\.html)#([^"]+)"', content):
            if page not in pages:
                bad.append(f"{name} -> {page}#{anchor} (missing page)")
            elif anchor not in set(re.findall(r'id="([^"]+)"', pages[page])):
                if anchor not in ("A", "B", "C", "D", "E") or f'id="{anchor}"' not in pages[page]:
                    bad.append(f"{name} -> {page}#{anchor} (missing anchor)")

    if bad:
        print("LINK CHECK FAILED:")
        for b in sorted(set(bad)):
            print("  -", b)
        sys.exit(1)

    print(f"Built {len(pages)} pages, {len(SOURCES)} sources, {len(CHANNELS)} routes, "
          f"{len(COSTS)} cost lines, {len(TAXES)} tax positions, {len(FLAGGED)} flagged items.")
    print("Internal link check: clean.")


if __name__ == "__main__":
    main()
