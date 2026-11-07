#!/usr/bin/env python3
"""Build the static China-money evidence dashboard from research/*.json.

The generator is deliberately deterministic and dependency-light. It validates
source references before rendering, leaves unverified numeric cells visually
blank, and writes a self-contained site to site/public (no CDN or analytics).
"""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path
from typing import Any, Iterable

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
SITE = ROOT / "site"
OUT = SITE / "public"
VERIFIED_ON = "2026-11-07"
DOMAINS = ("china", "us", "routes", "analysis")
DOMAIN_LABEL = {"china": "China", "us": "United States", "routes": "Routes", "analysis": "Analysis"}

NAV = [
    ("index", "Overview"),
    ("china", "China rules"),
    ("us", "US tax"),
    ("routes", "Routes"),
    ("requirements", "Requirements"),
    ("costs", "Costs"),
    ("analysis", "Analysis"),
    ("flagged", "Flagged"),
    ("sources", "Sources"),
]

STATUS_LABEL = {
    "conditional": "Conditional",
    "verified_provider_conditional_user": "Provider verified · user unverified",
    "unverified_candidate": "Unverified candidate",
    "prohibited_high_risk": "Prohibited / high risk",
    "not_repatriation": "Not repatriation",
    "conditional_not_savings_transfer": "Conditional · not savings transfer",
    "conditional_small_amount": "Conditional · small amount",
    "verified_rule_unverified_applicability": "Rule verified · applicability unverified",
    "verified_with_scope_limit": "Verified with scope limit",
    "historical_superseded": "Historical / superseded",
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
}
STATUS_CLASS = {
    "conditional": "conditional",
    "verified_provider_conditional_user": "provider",
    "unverified_candidate": "unverified",
    "prohibited_high_risk": "prohibited",
    "not_repatriation": "non_equivalent",
    "conditional_not_savings_transfer": "conditional",
    "conditional_small_amount": "conditional",
    "verified_rule_unverified_applicability": "verified",
    "verified_with_scope_limit": "verified",
    "historical_superseded": "unverified",
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
}


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def iter_rows(obj: Any) -> Iterable[dict]:
    if isinstance(obj, dict):
        if "source_ids" in obj:
            yield obj
        for value in obj.values():
            yield from iter_rows(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from iter_rows(value)


def load_data() -> tuple[dict[str, dict], dict[str, dict]]:
    data: dict[str, dict] = {}
    sources: dict[str, dict] = {}
    for domain in DOMAINS:
        path = RESEARCH / f"{domain}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("verified_on") != VERIFIED_ON:
            raise ValueError(f"{path}: unexpected verification date")
        data[domain] = payload
        for source in payload.get("sources", []):
            sid = source["id"]
            if sid in sources:
                raise ValueError(f"duplicate source id {sid}")
            if not source.get("url", "").startswith(("http://", "https://")):
                raise ValueError(f"{sid}: missing official URL")
            if source.get("verified_on") != VERIFIED_ON:
                raise ValueError(f"{sid}: missing verification date")
            sources[sid] = {**source, "domain": domain}
    for domain, payload in data.items():
        for row in iter_rows(payload):
            refs = row.get("source_ids") or []
            if not refs:
                raise ValueError(f"{domain}/{row.get('id')}: row has no source")
            for ref in refs:
                if ref not in sources:
                    raise ValueError(f"{domain}/{row.get('id')}: unknown source {ref}")
    for route in data["routes"]["routes"]:
        if any(value is not None for value in route["costs"].values()):
            raise ValueError(f"{route['id']}: commercial cost must remain null")
    for component in data["analysis"]["cost_model"]["components"]:
        if component["value"] is not None:
            raise ValueError(f"{component['id']}: user cost must remain null")
    return data, sources


def source_links(refs: list[str], sources: dict[str, dict]) -> str:
    links = []
    for ref in refs:
        source = sources[ref]
        title = f"{source['publisher']} — {source['title']}"
        links.append(
            f'<a class="source-link" href="{esc(source["url"])}" '
            f'aria-label="Open source {esc(ref)}: {esc(title)}" title="{esc(title)}">'
            f'{esc(ref)}<span class="arrow" aria-hidden="true">↗</span></a>'
        )
    return '<div class="source-list">' + "".join(links) + "</div>"


def badge(status: str) -> str:
    label = STATUS_LABEL.get(status, status.replace("_", " ").title())
    cls = STATUS_CLASS.get(status, "info")
    return f'<span class="badge {esc(cls)}">{esc(label)}</span>'


def td(content: str = "", cls: str = "") -> str:
    attr = f' class="{esc(cls)}"' if cls else ""
    return f"<td{attr}>{content}</td>"


def blank_td(label: str = "Unverified — left blank") -> str:
    return f'<td class="blank-cell"><span class="sr-only">{esc(label)}</span></td>'


def value_td(value: Any, unit: Any = None) -> str:
    if value is None:
        return blank_td()
    text = esc(value)
    if unit:
        text += f' <span class="muted small">{esc(unit)}</span>'
    return td(text)


def list_html(items: list[str]) -> str:
    if not items:
        return ""
    return "<ul>" + "".join(f"<li>{esc(item)}</li>" for item in items) + "</ul>"


def tr(cells: list[str], status: str = "") -> str:
    attr = f' data-status="{esc(status)}"' if status else ""
    return f"<tr{attr}>" + "".join(cells) + "</tr>"


def table(table_id: str, headers: list[str], rows: list[str], caption: str = "", cls: str = "") -> str:
    classes = ("table-wrap",)
    table_cls = f' class="{esc(cls)}"' if cls else ""
    cap = f"<caption>{esc(caption)}</caption>" if caption else ""
    head = "<thead><tr>" + "".join(f"<th scope=\"col\">{esc(h)}</th>" for h in headers) + "</tr></thead>"
    return (
        f'<div class="{classes[0]}"><table id="{esc(table_id)}"{table_cls}>{cap}{head}'
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def externalize_links(markup: str) -> str:
    def repl(match: re.Match) -> str:
        tag = match.group(0)
        if "target=" in tag:
            return tag
        return tag[:-1] + ' target="_blank" rel="noopener noreferrer">'
    return re.sub(r'<a\b[^>]*href="https?://[^"]*"[^>]*>', repl, markup)


def page(slug: str, title: str, description: str, body: str) -> str:
    nav = []
    for target, label in NAV:
        current = ' aria-current="page"' if target == slug else ""
        nav.append(f'<a href="{target}.html"{current}>{esc(label)}</a>')
    markup = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{esc(description)}">
<meta name="color-scheme" content="light">
<title>{esc(title)} · China money</title>
<link rel="stylesheet" href="assets/styles.css">
<script src="assets/app.js" defer></script>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true">¥$</span><span>China money<small>CNY → USD evidence guide</small></span></a>
    <nav class="nav" aria-label="Primary">{''.join(nav)}</nav>
  </div>
</header>
<main id="main" class="container">
{body}
</main>
<footer class="site-footer">
  <div class="container footer-inner">
    <p>Evidence checked {VERIFIED_ON}. Rules are source-linked; applicability to you remains unverified unless stated. Blank cells are intentionally empty, not zero. This is research, not personalized tax or legal advice.</p>
    <div class="footer-links"><a href="executive-summary.html">Executive summary</a><a href="sources.html">Source register</a><a href="flagged.html">Flagged for Review</a></div>
  </div>
</footer>
</body>
</html>
"""
    return externalize_links(markup)


def page_head(title: str, lede: str, meta: str = "") -> str:
    meta_html = f'<div class="meta">{meta}</div>' if meta else ""
    return f'<div class="page-head"><p class="eyebrow">Evidence-led research</p><h1>{esc(title)}</h1><p class="lede">{esc(lede)}</p>{meta_html}</div>'


def notice(text: str, kind: str = "") -> str:
    cls = f"notice {kind}".strip()
    return f'<div class="{cls}">{text}</div>'


def toolbar(table_id: str, placeholder: str, statuses: list[tuple[str, str]] | None = None) -> str:
    select = ""
    if statuses:
        options = '<option value="">All statuses</option>' + "".join(
            f'<option value="{esc(value)}">{esc(label)}</option>' for value, label in statuses
        )
        select = f'<label for="{table_id}-status">Status</label><select id="{table_id}-status" data-status-filter="{table_id}">{options}</select>'
    return (
        f'<div class="toolbar"><label for="{table_id}-search">Search</label>'
        f'<input id="{table_id}-search" type="search" placeholder="{esc(placeholder)}" data-table-filter="{table_id}">'
        f'{select}<span class="result-count" data-count-for="{table_id}" aria-live="polite"></span></div>'
    )


def requirements_table(rows: list[dict], sources: dict[str, dict], table_id: str, jurisdiction: str | None = None) -> str:
    headers = (["Jurisdiction"] if jurisdiction else []) + ["ID", "Topic", "Requirement", "Value", "Condition / status", "Sources"]
    body = []
    for row in rows:
        cells = []
        if jurisdiction:
            cells.append(td(esc(jurisdiction)))
        condition = esc(row.get("condition") or "")
        flag = row.get("flag")
        status = badge(row.get("status", "")) if row.get("status") else ""
        flag_html = f'<p class="flag-text">{esc(flag)}</p>' if flag else ""
        cells += [
            td(f'<span class="id">{esc(row["id"])}</span>'),
            td(esc(row["topic"]), "row-title"),
            td(esc(row["requirement"])),
            value_td(row.get("value"), row.get("unit")),
            td(f"{status}<p class=\"small muted\">{condition}</p>{flag_html}"),
            td(source_links(row["source_ids"], sources)),
        ]
        body.append(tr(cells, row.get("status", "")))
    return table(table_id, headers, body, cls="wide-table")


def findings_table(rows: list[dict], sources: dict[str, dict], table_id: str) -> str:
    body = []
    for row in rows:
        flag = f'<p class="flag-text">{esc(row["flag"])}</p>' if row.get("flag") else ""
        cells = [
            td(f'<span class="id">{esc(row["id"])}</span>'),
            td(esc(row["topic"]), "row-title"),
            td(esc(row["finding"])),
            td(esc(row["implication"])),
            td(badge(row.get("status", "")) + flag),
            td(source_links(row["source_ids"], sources)),
        ]
        body.append(tr(cells, row.get("status", "")))
    return table(table_id, ["ID", "Topic", "Finding", "Implication", "Status / flag", "Sources"], body, cls="wide-table")


def unknowns_table(rows: list[dict], sources: dict[str, dict], table_id: str, domain_label: str | None = None) -> str:
    headers = (["Domain"] if domain_label else []) + ["ID", "Unknown input", "Value", "Needed for", "Flag", "Sources"]
    body = []
    for row in rows:
        cells = []
        if domain_label:
            cells.append(td(esc(domain_label)))
        cells += [
            td(f'<span class="id">{esc(row["id"])}</span>'),
            td(esc(row["field"]), "row-title"),
            blank_td(),
            td(esc(row["needed_for"])),
            td(esc(row["flag"]), "flag-text"),
            td(source_links(row["source_ids"], sources)),
        ]
        body.append(tr(cells))
    return table(table_id, headers, body, cls="wide-table")


def build_index(data: dict, sources: dict) -> str:
    linked_rows = sum(1 for payload in data.values() for _ in iter_rows(payload))
    flag_count = sum(len(payload.get("flags", [])) for payload in data.values())
    unknown_count = len(data["china"]["user_unknowns"]) + len(data["us"]["user_unknowns"])
    route_count = len(data["routes"]["routes"])
    body = f"""
<section class="hero">
  <div class="hero-copy">
    <p class="eyebrow">US citizen · CNY in a mainland-China bank</p>
    <h1>Move CNY to USD without guessing.</h1>
    <p class="lede">A source-linked decision guide for conversion, remittance, tax and reporting. Start with the lawful source of the money, then compare only routes you can actually document and execute.</p>
    <div class="hero-actions"><a class="button" href="executive-summary.html">Read executive summary</a><a class="button secondary" href="routes.html">Browse {route_count} routes</a><a class="button secondary" href="flagged.html">Review flags</a></div>
  </div>
  <aside class="hero-panel" aria-label="Key conclusion">
    <h2>No universal “conversion tax” verified</h2>
    <p>China FX controls, China income tax, US federal tax, currency gain/loss, reporting penalties and commercial transfer costs are separate buckets.</p>
    <ul><li>Balance, source, residence/status and filings are unknown.</li><li>No cheapest provider is ranked without comparable quotes.</li><li>Unverified values stay blank and flagged.</li></ul>
  </aside>
</section>
{notice('<strong>Read this first:</strong> the best first step is to classify the CNY and use the matching documented bank/approval route. A listed candidate is not proof that it is available to you.')}
<section class="stats" aria-label="Research coverage">
  <div class="stat"><span class="number">{route_count}</span><span class="label">routes inventoried</span></div>
  <div class="stat"><span class="number">{len(sources)}</span><span class="label">official / primary sources</span></div>
  <div class="stat"><span class="number">{linked_rows}</span><span class="label">source-linked rows</span></div>
  <div class="stat"><span class="number">{flag_count}</span><span class="label">review flags · {unknown_count} unknown inputs</span></div>
</section>
<h2>Explore the evidence</h2>
<div class="cards">
  <article class="card"><h3>China rules</h3><p>Exchange-control requirements, tax findings, quotas, approval routes and superseded rules.</p><a class="card-link" href="china.html">Open China rules →</a></article>
  <article class="card"><h3>US tax &amp; reporting</h3><p>Worldwide income, FEIE/FTC, currency gain, FBAR/FATCA, gifts, trusts and compliance procedures.</p><a class="card-link" href="us.html">Open US analysis →</a></article>
  <article class="card"><h3>Route inventory</h3><p>Bank, provider, asset, cash/card, non-equivalent and prohibited routes with pros, cons and limits.</p><a class="card-link" href="routes.html">Compare routes →</a></article>
  <article class="card"><h3>Requirements checklist</h3><p>Identity, source-of-funds, tax evidence, asset history, US filings and live-quote inputs.</p><a class="card-link" href="requirements.html">Build your checklist →</a></article>
  <article class="card"><h3>Cost breakdown</h3><p>Delivered-USD formula and separate tax, FX-spread, fee, approval and penalty buckets. Prices remain blank.</p><a class="card-link" href="costs.html">See cost model →</a></article>
  <article class="card"><h3>Flagged for Review</h3><p>Unknown inputs, provider gaps, currentness limits and row-level applicability caveats with source links.</p><a class="card-link" href="flagged.html">Open review register →</a></article>
</div>
<h2>How to use this site</h2>
<div class="cards">
  <article class="card"><h3>1 · Classify the money</h3><p>Salary, business income, dividends, sale proceeds, inheritance or prior exchange — each has different evidence and tax treatment.</p><a class="card-link" href="analysis.html">Decision steps →</a></article>
  <article class="card"><h3>2 · Match the legal route</h3><p>Use the genuine income/asset process. Do not force unrelated savings through a fabricated transaction or quota split.</p><a class="card-link" href="routes.html">Route conditions →</a></article>
  <article class="card"><h3>3 · Compare delivered USD</h3><p>Record the same-time customer rate, all fees and amount delivered. Then model tax separately; never add a blanket “repatriation tax”.</p><a class="card-link" href="costs.html">Cost formula →</a></article>
</div>
"""
    return page("index", "Overview", "Source-linked CNY to USD conversion and remittance guide for a US citizen with funds in mainland China.", body)


def build_domain(slug: str, data: dict, sources: dict) -> str:
    payload = data[slug]
    title = "China exchange-control & tax rules" if slug == "china" else "US federal tax & reporting"
    body = page_head(title, payload["scope"], f'<span>Evidence date: {VERIFIED_ON}</span><span>{len(payload.get("sources", []))} sources in this domain</span>')
    body += notice(f'<strong>Method:</strong> {esc(payload["method"])}', "info")
    body += '<div class="section-head"><div><h2>Requirements</h2><p>Values are blank where the user-specific fact or amount was not supplied.</p></div></div>'
    body += requirements_table(payload["requirements"], sources, f"{slug}-requirements")
    body += '<div class="section-head"><div><h2>Findings and implications</h2><p>Rule-level conclusions with scope limits and applicability flags.</p></div></div>'
    body += findings_table(payload["findings"], sources, f"{slug}-findings")
    body += '<div class="section-head"><div><h2>Unknown user inputs</h2><p>These remain blank; see the combined checklist and review register.</p></div></div>'
    body += unknowns_table(payload["user_unknowns"], sources, f"{slug}-unknowns")
    return page(slug, title, payload["scope"], body)


def build_routes(data: dict, sources: dict) -> str:
    routes = data["routes"]["routes"]
    statuses = []
    seen = set()
    for route in routes:
        if route["status"] not in seen:
            seen.add(route["status"])
            statuses.append((route["status"], STATUS_LABEL.get(route["status"], route["status"])))
    body = page_head("Route inventory", data["routes"]["scope"], f'<span>{len(routes)} routes</span><span>All commercial costs unverified</span>')
    body += notice(f'<strong>Source policy:</strong> {esc(data["routes"]["source_policy"])}')
    body += toolbar("routes-table", "Search routes, providers, limits…", statuses)
    rows = []
    for route in routes:
        cost_note = '<a href="costs.html#route-costs">Cost breakdown</a><p class="small muted">FX spread, fees and taxes: blank / unverified.</p>'
        cells = [
            td(f'<span class="id">{esc(route["id"])}</span>'),
            td(f'<span class="row-title">{esc(route["name"])}</span><p>{badge(route["status"])}</p><p class="flag-text">{esc(route["flag"])}</p>'),
            td(esc(route["category"])),
            td(f'<p>{esc(route["mechanism"])}</p><p class="small muted"><strong>Eligibility:</strong> {esc(route["eligibility"])}</p>'),
            td(list_html(route["requirements"])),
            td(f'<p>{esc(route["limits"])}</p><p class="small muted"><strong>Tax:</strong> {esc(route["tax_treatment"])}</p>'),
            td(f'<p class="small"><strong>Pros</strong></p>{list_html(route["pros"])}<p class="small"><strong>Cons</strong></p>{list_html(route["cons"])}'),
            td(cost_note),
            td(source_links(route["source_ids"], sources)),
        ]
        rows.append(tr(cells, route["status"]))
    body += table(
        "routes-table",
        ["ID", "Route / status", "Category", "Mechanism / eligibility", "Requirements", "Limits / tax", "Pros / cons", "Costs", "Sources"],
        rows,
        caption="Every route is conditional on its cited rules and the user's unverified facts.",
        cls="routes-table",
    )
    return page("routes", "Routes", "Inventory of CNY conversion and repatriation routes with conditions, limits, pros, cons and source links.", body)


def build_requirements(data: dict, sources: dict) -> str:
    body = page_head("Requirements checklist", "Combined China and US evidence checklist. Route-specific document lists remain on the route inventory; unknown user inputs stay blank.")
    rows = []
    for domain in ("china", "us"):
        for row in data[domain]["requirements"]:
            cells = [
                td(esc(DOMAIN_LABEL[domain])),
                td(f'<span class="id">{esc(row["id"])}</span>'),
                td(esc(row["topic"]), "row-title"),
                td(esc(row["requirement"])),
                value_td(row.get("value"), row.get("unit")),
                td(f'{badge(row.get("status", ""))}<p class="small muted">{esc(row.get("condition") or "")}</p><p class="flag-text">{esc(row.get("flag") or "")}</p>'),
                td(source_links(row["source_ids"], sources)),
            ]
            rows.append(tr(cells, row.get("status", "")))
    body += table("requirements-table", ["Domain", "ID", "Topic", "Requirement", "Value", "Condition / flag", "Sources"], rows, cls="wide-table")
    body += '<div class="section-head"><div><h2>Unknown inputs to resolve</h2><p>No balance, source, residence, filing history or eligibility is inferred.</p></div></div>'
    unknown_rows = []
    for domain in ("china", "us"):
        for row in data[domain]["user_unknowns"]:
            unknown_rows.append(tr([
                td(esc(DOMAIN_LABEL[domain])),
                td(f'<span class="id">{esc(row["id"])}</span>'),
                td(esc(row["field"]), "row-title"),
                blank_td(),
                td(esc(row["needed_for"])),
                td(esc(row["flag"]), "flag-text"),
                td(source_links(row["source_ids"], sources)),
            ]))
    body += table("unknown-inputs", ["Domain", "ID", "Unknown input", "Value", "Needed for", "Flag", "Sources"], unknown_rows, cls="wide-table")
    return page("requirements", "Requirements", "Source-linked requirements and unknown inputs for converting and remitting CNY.", body)


def build_costs(data: dict, sources: dict) -> str:
    model = data["analysis"]["cost_model"]
    body = page_head("Conversion-penalty breakdown", "Keep execution cost, underlying income tax, currency gain/loss and compliance penalties separate. No live quote or user-specific tax amount was supplied.")
    body += notice('<strong>Blank ≠ zero.</strong> Every commercial cost and user-specific tax value below is intentionally blank until a like-for-like quote or actual tax facts exist.')
    formulas = []
    for formula in model["formulas"]:
        formulas.append(
            f'<article class="formula"><h3>{esc(formula["name"])}</h3><code>{esc(formula["formula"])}</code>'
            f'<p>{esc(formula["condition"])}</p><p>{source_links(formula["source_ids"], sources)}</p></article>'
        )
    body += '<div class="formula-grid">' + "".join(formulas) + "</div>"
    def_rows = [tr([
        td(f'<span class="id">{esc(row["id"])}</span>'),
        td(f'<code>{esc(row["term"])}</code>', "row-title"),
        td(esc(row["definition"])),
        td(source_links(row["source_ids"], sources)),
    ]) for row in model["definitions"]]
    body += '<h2>Formula definitions</h2>' + table("cost-definitions", ["ID", "Term", "Definition", "Sources"], def_rows)
    comp_rows = []
    for row in model["components"]:
        comp_rows.append(tr([
            td(f'<span class="id">{esc(row["id"])}</span>'),
            td(esc(row["component"]), "row-title"),
            blank_td(),
            td(esc(row["basis"])),
            td(esc(row["flag"]), "flag-text"),
            td(source_links(row["source_ids"], sources)),
        ]))
    body += '<h2>Cost and tax components</h2>' + table("cost-components", ["ID", "Component", "User value", "Basis", "Flag", "Sources"], comp_rows, cls="wide-table")
    body += '<div class="section-head" id="route-costs"><div><h2>Route-level commercial costs</h2><p>All values remain blank because no comparable outbound quotes were verified.</p></div></div>'
    cost_rows = []
    for route in data["routes"]["routes"]:
        cost_rows.append(tr([
            td(f'<span class="id">{esc(route["id"])}</span>'),
            td(f'<span class="row-title">{esc(route["name"])}</span><p>{badge(route["status"])}</p>'),
            blank_td("FX spread unverified"),
            blank_td("Transfer fee unverified"),
            blank_td("Intermediary fee unverified"),
            blank_td("Receiving fee unverified"),
            blank_td("Other cost unverified"),
            td(source_links(route["source_ids"], sources)),
        ], route["status"]))
    body += table("route-costs-table", ["ID", "Route", "FX spread", "Transfer fee", "Intermediary fee", "Receiving fee", "Other", "Sources"], cost_rows, cls="costs-table")
    return page("costs", "Costs", "Delivered-USD cost model and separate tax, fee, FX-spread and penalty buckets with blank unverified values.", body)


def build_analysis(data: dict, sources: dict) -> str:
    analysis = data["analysis"]
    body = page_head("Deep analysis & decision logic", analysis["scope"])
    body += notice(f'<strong>Headline:</strong> {esc(analysis["headline"])}', "info")
    step_rows = [tr([
        td(f'<span class="id">{esc(row["id"])}</span>'),
        td(esc(row["step"]), "row-title"),
        td(esc(row["action"])),
        td(esc(row["why"])),
        td(esc(row["output"])),
        td(source_links(row["source_ids"], sources)),
    ]) for row in analysis["decision_steps"]]
    body += '<h2>Decision steps</h2>' + table("decision-steps", ["ID", "Step", "Action", "Why", "Output", "Sources"], step_rows, cls="wide-table")
    rec_rows = [tr([
        td(f'<span class="id">{esc(row["id"])}</span>'),
        td(esc(row["rank"])),
        td(esc(row["condition"]), "row-title"),
        td(esc(row["recommendation"])),
        td(esc(row["rationale"])),
        td(esc(row["flag"]), "flag-text"),
        td(source_links(row["source_ids"], sources)),
    ]) for row in sorted(analysis["conditional_recommendations"], key=lambda r: r["rank"])]
    body += '<h2>Conditional recommendations</h2>' + notice('The order below is a conditional workflow priority, not a cheapest-provider or lowest-tax ranking for this user.') + table("recommendations", ["ID", "Priority", "Condition", "Recommendation", "Rationale", "Flag", "Sources"], rec_rows, cls="wide-table")
    scenario_rows = [tr([
        td(f'<span class="id">{esc(row["id"])}</span>'),
        td(esc(row["scenario"]), "row-title"),
        td(esc(row["analysis"])),
        td(esc(row["flag"]), "flag-text"),
        td(source_links(row["source_ids"], sources)),
    ]) for row in analysis["tax_scenarios"]]
    body += '<h2>Tax scenarios</h2>' + table("tax-scenarios", ["ID", "Scenario", "Analysis", "Flag", "Sources"], scenario_rows, cls="wide-table")
    myth_rows = [tr([
        td(f'<span class="id">{esc(row["id"])}</span>'),
        td(esc(row["myth"]), "row-title"),
        td(esc(row["correction"])),
        td(source_links(row["source_ids"], sources)),
    ]) for row in analysis["myths"]]
    body += '<h2>Myths corrected</h2>' + table("myths", ["ID", "Myth", "Correction", "Sources"], myth_rows, cls="wide-table")
    return page("analysis", "Analysis", "Conditional decision logic, tax scenarios and myth corrections for CNY to USD repatriation.", body)


def build_flagged(data: dict, sources: dict) -> str:
    body = page_head("Flagged for Review", "Unverified inputs, source/currentness limits, provider gaps and row-level applicability caveats. These flags do not block publication; they prevent unsupported values from being presented as facts.")
    flag_rows = []
    for domain in DOMAINS:
        for row in data[domain].get("flags", []):
            flag_rows.append(tr([
                td(esc(DOMAIN_LABEL[domain])),
                td(f'<span class="id">{esc(row["id"])}</span>'),
                td(badge(row["severity"])),
                td(esc(row["topic"]), "row-title"),
                td(esc(row["finding"])),
                td(esc(row["resolution"])),
                td(source_links(row["source_ids"], sources)),
            ], row["severity"]))
    body += '<h2>Review register</h2>' + toolbar("flags-table", "Search flags…") + table("flags-table", ["Domain", "ID", "Severity", "Topic", "Finding", "Resolution", "Sources"], flag_rows, cls="wide-table")
    unknown_rows = []
    for domain in ("china", "us"):
        for row in data[domain]["user_unknowns"]:
            unknown_rows.append(tr([
                td(esc(DOMAIN_LABEL[domain])),
                td(f'<span class="id">{esc(row["id"])}</span>'),
                td(esc(row["field"]), "row-title"),
                blank_td(),
                td(esc(row["needed_for"])),
                td(esc(row["flag"]), "flag-text"),
                td(source_links(row["source_ids"], sources)),
            ]))
    body += '<h2>Unknown user inputs</h2>' + table("flagged-unknowns", ["Domain", "ID", "Input", "Value", "Needed for", "Flag", "Sources"], unknown_rows, cls="wide-table")
    route_rows = [tr([
        td(f'<span class="id">{esc(row["id"])}</span>'),
        td(esc(row["name"]), "row-title"),
        td(badge(row["status"])),
        td(esc(row["flag"]), "flag-text"),
        td(source_links(row["source_ids"], sources)),
    ], row["status"]) for row in data["routes"]["routes"]]
    body += '<h2>Route availability and cost caveats</h2>' + table("flagged-routes", ["ID", "Route", "Status", "Flag", "Sources"], route_rows, cls="wide-table")
    other_rows = []
    collections = [
        ("china", "requirements"), ("china", "findings"),
        ("us", "requirements"), ("us", "findings"),
        ("analysis", "conditional_recommendations"), ("analysis", "tax_scenarios"),
    ]
    for domain, key in collections:
        for row in data["analysis" if domain == "analysis" else domain][key]:
            if row.get("flag"):
                label = row.get("topic") or row.get("condition") or row.get("scenario") or row["id"]
                other_rows.append(tr([
                    td(esc(DOMAIN_LABEL[domain])),
                    td(f'<span class="id">{esc(row["id"])}</span>'),
                    td(esc(label), "row-title"),
                    td(esc(row["flag"]), "flag-text"),
                    td(source_links(row["source_ids"], sources)),
                ]))
    for row in data["analysis"]["cost_model"]["components"]:
        other_rows.append(tr([
            td("Analysis"),
            td(f'<span class="id">{esc(row["id"])}</span>'),
            td(esc(row["component"]), "row-title"),
            td(esc(row["flag"]), "flag-text"),
            td(source_links(row["source_ids"], sources)),
        ]))
    body += '<h2>Row-level applicability flags</h2>' + table("flagged-rows", ["Domain", "ID", "Row", "Flag", "Sources"], other_rows, cls="wide-table")
    return page("flagged", "Flagged for Review", "All review flags, unknown inputs and unverified route/cost caveats with official source links.", body)


def build_sources(data: dict, sources: dict) -> str:
    body = page_head("Source register", "Every table row links to at least one source below. Government/regulator sources support legal rules; provider-owned pages support only their own product terms, not legal conclusions.")
    body += notice('<strong>Verification method:</strong> sources were read directly where available; historical provisions are labeled and read with identified amendments. Failed or insufficient retrievals are recorded in the research notes and are not used as evidence.', "info")
    body += toolbar("sources-table", "Search sources, publishers, locators…")
    rows = []
    for sid, source in sources.items():
        rows.append(tr([
            td(f'<span class="id">{esc(sid)}</span>'),
            td(badge(source["domain"]) if source["domain"] in STATUS_CLASS else f'<span class="badge info">{esc(DOMAIN_LABEL[source["domain"]])}</span>'),
            td(f'<span class="row-title">{esc(source["title"])}</span><p class="small muted">{esc(source["publisher"])}</p>'),
            td(esc(source.get("published") or "")),
            td(esc(source.get("locator") or "")),
            td(esc(source.get("supports") or "")),
            td(esc(source.get("access") or "")),
            td(esc(source.get("verified_on") or "")),
            td(f'<a class="source-link" href="{esc(source["url"])}">Open source<span class="arrow" aria-hidden="true">↗</span></a>'),
        ]))
    body += table("sources-table", ["ID", "Domain", "Title / publisher", "Published", "Locator", "Supports", "Access", "Checked", "Link"], rows, cls="sources-table")
    return page("sources", "Sources", "Official and primary source register with locators, verification dates and links.", body)


def build_executive_summary() -> str:
    markdown = (ROOT / "EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
    renderer = MarkdownIt("commonmark").enable("table")
    rendered = renderer.render(markdown)
    rendered = rendered.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    body = f'<div class="prose">{rendered}</div>'
    return page("executive-summary", "Executive summary", "Executive summary of source-backed CNY to USD conversion, remittance, tax and reporting analysis.", body)


def main() -> None:
    data, sources = load_data()
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    shutil.copyfile(SITE / "styles.css", OUT / "assets" / "styles.css")
    shutil.copyfile(SITE / "app.js", OUT / "assets" / "app.js")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    pages = {
        "index": build_index(data, sources),
        "china": build_domain("china", data, sources),
        "us": build_domain("us", data, sources),
        "routes": build_routes(data, sources),
        "requirements": build_requirements(data, sources),
        "costs": build_costs(data, sources),
        "analysis": build_analysis(data, sources),
        "flagged": build_flagged(data, sources),
        "sources": build_sources(data, sources),
        "executive-summary": build_executive_summary(),
    }
    for slug, markup in pages.items():
        (OUT / f"{slug}.html").write_text(markup, encoding="utf-8")
    linked_rows = sum(1 for payload in data.values() for _ in iter_rows(payload))
    print(f"Built {len(pages)} pages, {len(sources)} sources, {linked_rows} linked rows -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
