#!/usr/bin/env python3
"""Render the independent QA report deterministically from reviewed evidence."""
from __future__ import annotations

import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "findings.json").read_text(encoding="utf-8"))
SOURCES = {s["id"]: s for s in DATA["sources"]}


def e(value: object) -> str:
    return html.escape(str(value), quote=True)


def refs(ids: list[str]) -> str:
    return " ".join(
        f'<a href="{e(SOURCES[sid]["url"])}" target="_blank" rel="noopener noreferrer">{e(SOURCES[sid]["label"])}</a>'
        for sid in ids
    )


def render() -> str:
    findings = []
    for item in DATA["items"]:
        findings.append(
            f'<tr id="{e(item["id"])}">'
            f'<td data-label="Priority"><span class="badge">{e(item["priority"])}</span><small>{e(item["id"])}</small></td>'
            f'<td data-label="Finding"><strong>{e(item["title"])}</strong><p>{e(item["observed"])}</p></td>'
            f'<td data-label="What the evidence means">{e(item["finding"])}</td>'
            f'<td data-label="Review action">{e(item["action"])}</td>'
            f'<td data-label="Official source">{refs(item["sources"])} '
            f'<a href="{e(item["code"])}" target="_blank" rel="noopener noreferrer">Baseline repository evidence</a></td></tr>'
        )
    sources = []
    for source in DATA["sources"]:
        sources.append(
            f'<tr id="S-{e(source["id"])}"><td data-label="Source"><a href="{e(source["url"])}" '
            f'target="_blank" rel="noopener noreferrer">{e(source["label"])}</a></td>'
            f'<td data-label="What was checked">{e(source["quote"])}</td></tr>'
        )
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Independent, source-linked quality review of the China Money guide, including cost assumptions and open questions.">
<title>Flagged for Review · Independent quality check</title>
<style>
:root{{--ink:#18283a;--muted:#526579;--line:#d7e1e8;--brand:#075d79;--paper:#fff;--bg:#f3f7fa;--warn:#80510a}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Arial,sans-serif}}
a{{color:var(--brand)}}a:focus-visible{{outline:3px solid #db8b18;outline-offset:2px}}
header{{background:#123047;color:white}}.bar{{max-width:1120px;margin:auto;padding:18px 18px 12px}}.brand{{font-weight:750;color:white;text-decoration:none;font-size:1.1rem}}
nav{{display:flex;gap:1rem;overflow-x:auto;padding-top:10px;white-space:nowrap}}nav a{{color:#d9edf4;padding:5px 0 9px}}
main,footer{{max-width:1120px;margin:auto;padding:24px 18px}}h1{{font-size:clamp(1.65rem,4vw,2.45rem);line-height:1.17;margin:.2em 0 .5em}}h2{{font-size:1.3rem;margin:1.7em 0 .5em}}p{{margin:.5em 0}}
.lead{{font-size:1.08rem;color:#345367;max-width:72ch}}.card{{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:18px;margin:16px 0}}
.notice{{border-left:5px solid #dfab48}}.checks{{border-left:5px solid #238367}}.small,small{{color:var(--muted);font-size:.86rem}}small{{display:block}}
.badge{{background:#fff1d5;color:var(--warn);border-radius:1rem;padding:2px 9px;font-size:.8rem;font-weight:700;white-space:nowrap}}
.wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:12px;background:white}}table{{width:100%;border-collapse:collapse;font-size:.91rem}}th,td{{text-align:left;vertical-align:top;padding:12px;border-bottom:1px solid var(--line)}}th{{background:#edf4f7;font-size:.78rem;letter-spacing:.02em;text-transform:uppercase}}td a{{display:inline-block;margin:2px 7px 2px 0}}td p{{margin:.35rem 0 0}}
footer{{border-top:1px solid var(--line);font-size:.87rem;color:var(--muted)}}ul{{padding-left:1.2rem}}
@media(max-width:719px){{table.stack thead{{position:absolute;left:-9999px}}table.stack,table.stack tbody,table.stack tr,table.stack td{{display:block;width:100%}}table.stack tr{{border-top:6px solid var(--bg);padding:8px 0}}table.stack tr:first-child{{border-top:0}}table.stack td{{border:0;padding:5px 14px}}table.stack td::before{{content:attr(data-label);display:block;text-transform:uppercase;color:var(--muted);font-size:.72rem;letter-spacing:.03em}}}}
</style>
</head>
<body>
<header><div class="bar"><a class="brand" href="../index.html">China Money</a><nav aria-label="Guide navigation"><a href="../index.html">Home</a><a href="../guide/summary.html">Summary</a><a href="../guide/costs.html">Costs</a><a href="../guide/flagged.html">Guide flags</a><a href="#findings" aria-current="page">Independent review</a><a href="#sources">Sources</a></nav></div></header>
<main>
<h1>Flagged for Review: independent quality check</h1>
<p class="lead">A focused review of cost assumptions, tax language and the site—not a personal transfer quote or a recommendation to bypass exchange controls.</p>
<section class="card notice"><strong>What is still unknown</strong><p>Your funds' source, account classification, tax and filing history, sending and receiving banks, and actual quotes were not supplied. Therefore eligibility, tax owed, the cheapest method and the all-in cost remain unverified. Do not interpret a blank as zero.</p><p class="small">Reviewed {e(DATA["reviewed_utc"])} UTC against repository snapshot <a href="https://github.com/sassnarep3-star/China1/commit/{e(DATA["baseline"])}">{e(DATA["baseline"])}</a>. Findings describe that snapshot; later changes may address them. Consult the canonical <a href="../guide/flagged.html">Flagged for Review page</a> and the decision questions linked from the <a href="../index.html">main guide</a>.</p></section>
<section class="card checks"><strong>What the independent checks can—and cannot—show</strong><p>The reproducible checks render the guide at five screen widths, inspect registered source links and local fragments, and compare the 40-step ladder with its recorded inputs. A passing check is not proof of legal interpretation, source availability, eligibility or an all-in price. This is a targeted review; it is not manual certification of every line in the archived editions.</p></section>
<h2 id="findings">Findings and suggested follow-up</h2>
<p class="small">These are review items, not findings that a specific individual violated a law. Each row links to the issuing authority or, for repository methodology, the source code itself.</p>
<div class="wrap"><table class="stack"><thead><tr><th>Priority</th><th>Finding</th><th>What the evidence means</th><th>Review action</th><th>Official source</th></tr></thead><tbody>{''.join(findings)}</tbody></table></div>
<h2 id="sources">Official source notes</h2>
<p class="small">Source pages were opened during this review. Quoted or summarized passages are shown for manual review; live pages and rates may change.</p>
<div class="wrap"><table class="stack"><thead><tr><th>Source</th><th>What was checked</th></tr></thead><tbody>{''.join(sources)}</tbody></table></div>
<h2>Practical next steps</h2>
<ul><li>Collect the documents matching the actual origin and ownership of the money; ask the mainland bank to classify the transaction and specify its requirements.</li><li>Ask eligible providers for comparable, timestamped end-to-end quotes, identifying the amount sent and the amount received and any extra charges.</li><li>Have qualified China and US tax advisers review the income, any exchange gain and foreign-account reporting before moving the funds.</li></ul>
<p><a href="../index.html">Return to the main guide</a> · <a href="../guide/costs.html">Open the cost ladder</a> · <a href="https://github.com/sassnarep3-star/China1">Repository</a></p>
</main>
<footer>Research and quality assurance only; not legal, tax or investment advice. Official sources and live quotes should be checked before acting.</footer>
</body>
</html>
'''


if __name__ == "__main__":
    (HERE / "index.html").write_text(render(), encoding="utf-8")
    print(f"Wrote {HERE / 'index.html'}: {len(DATA['items'])} findings, {len(SOURCES)} sources")
