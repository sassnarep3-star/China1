#!/usr/bin/env python3
"""Mechanical audit of the whole repository.

Checks internal links, fragments, duplicate IDs, JSON validity and a small set
of known content risks. Writes edition-i/data/repo-review.json, which build.py
turns into the published audit page.

Usage: python3 edition-i/build/audit.py
"""
from __future__ import annotations

import collections
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
ED = Path(__file__).resolve().parents[1]
OUT = ED / "data" / "repo-review.json"

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv"}

STALE_PATTERNS = [
    ("Staged release (2004 rule)", r"Staged release|50% now, 25%|\u5206\u6b65\u6c47\u51fa"),
    ("Exact all-in total $83.45", r"\$83\.45"),
    ("Exact all-in total $932.72", r"\$932\.72"),
    ("Blanket tax-free claim", r"tax[- ]free"),
    ("Under-1% universal claim", r"under 1%|less than 1%"),
]


class Parser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: list[str] = []
        self.refs: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "a" and "href" in a:
            self.refs.append(a["href"])
        if tag in ("img", "script", "link", "source", "iframe"):
            for k in ("src", "href"):
                if k in a:
                    self.refs.append(a[k])


def crawl() -> dict:
    files = [p for p in ROOT.rglob("*.html") if not (set(p.parts) & SKIP_DIRS)]
    ids: dict[str, list[str]] = {}
    refs: dict[str, list[str]] = {}
    sizes = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        p = Parser()
        p.feed(text)
        rel = str(f.relative_to(ROOT))
        ids[rel] = p.ids
        refs[rel] = p.refs
        sizes.append({"path": rel, "bytes": f.stat().st_size, "lines": text.count("\n") + 1})

    missing: list[dict] = []
    bad_anchor: list[dict] = []
    internal = 0
    external = 0
    for rel, links in refs.items():
        base = (ROOT / rel).parent
        for link in links:
            u = urlparse(link)
            if u.scheme in ("http", "https"):
                external += 1
                continue
            if u.scheme in ("mailto", "tel", "javascript", "data"):
                continue
            if not link.strip():
                continue
            internal += 1
            if u.path.startswith("/"):
                target = (ROOT / unquote(u.path.lstrip("/"))).resolve()
            elif u.path:
                target = (base / unquote(u.path)).resolve()
            else:
                target = (ROOT / rel).resolve()
            try:
                target.relative_to(ROOT.resolve())
            except ValueError:
                missing.append({"page": rel, "link": link, "reason": "outside repository"})
                continue
            if not target.exists():
                missing.append({"page": rel, "link": link, "reason": "file not found"})
                continue
            if u.fragment and target.suffix == ".html":
                key = str(target.relative_to(ROOT.resolve()))
                if u.fragment not in ids.get(key, []):
                    bad_anchor.append({"page": rel, "link": link, "reason": "fragment not found"})

    dups = {rel: [i for i, c in collections.Counter(v).items() if c > 1]
            for rel, v in ids.items() if any(c > 1 for c in collections.Counter(v).values())}

    # JSON validity across the repository
    bad_json = []
    json_files = [p for p in ROOT.rglob("*.json") if not (set(p.parts) & SKIP_DIRS)]
    for p in json_files:
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            bad_json.append({"path": str(p.relative_to(ROOT)), "error": str(exc)[:120]})

    # content risk scan
    findings = []
    md_html = [p for p in ROOT.rglob("*") if p.suffix in (".html", ".md")
               and not (set(p.parts) & SKIP_DIRS) and p.is_file()]
    for label, pattern in STALE_PATTERNS:
        hits = []
        rx = re.compile(pattern, re.IGNORECASE)
        for p in md_html:
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                continue
            for m in rx.finditer(txt):
                start = max(0, m.start() - 70)
                hits.append({"path": str(p.relative_to(ROOT)),
                             "context": txt[start:m.end() + 70].replace("\n", " ")[:180]})
                if len(hits) >= 8:
                    break
            if len(hits) >= 8:
                break
        if hits:
            findings.append({"pattern": label, "count_capped": len(hits), "hits": hits})

    issues = [
        {"check": "HTML pages parsed", "result": f"{len(files)}",
         "detail": "Every committed .html file was parsed."},
        {"check": "Internal references resolved", "result": f"{internal}",
         "detail": f"{len(missing)} broken (file or path missing)."},
        {"check": "Fragment (anchor) targets", "result": f"{internal}",
         "detail": f"{len(bad_anchor)} fragments did not resolve to an element ID."},
        {"check": "Duplicate element IDs", "result": f"{len(dups)}",
         "detail": "Duplicate IDs break in-page navigation and accessibility."},
        {"check": "JSON documents parsed", "result": f"{len(json_files)}",
         "detail": f"{len(bad_json)} failed to parse."},
        {"check": "External references", "result": f"{external}",
         "detail": "Not fetched during the audit; external availability is not assured."},
        {"check": "Stale or risky content patterns", "result": f"{len(findings)}",
         "detail": "Patterns are reported as leads for human review, not as verdicts."},
    ]

    if missing:
        issues.append({"check": "Broken internal links", "result": f"{len(missing)}",
                       "detail": "; ".join(f'{m["page"]} -> {m["link"]}' for m in missing[:5])})
    if bad_anchor:
        issues.append({"check": "Unresolved fragments", "result": f"{len(bad_anchor)}",
                       "detail": "; ".join(f'{m["page"]} -> {m["link"]}' for m in bad_anchor[:5])})
    if dups:
        issues.append({"check": "Duplicate IDs detail", "result": f"{len(dups)}",
                       "detail": "; ".join(list(dups)[:5])})
    if bad_json:
        issues.append({"check": "Invalid JSON", "result": f"{len(bad_json)}",
                       "detail": "; ".join(b["path"] for b in bad_json[:5])})

    sizes.sort(key=lambda x: x["bytes"], reverse=True)
    return {
        "generated_utc": "2026-11-10",
        "summary": {
            "html_files": len(files),
            "internal_refs": internal,
            "external_refs": external,
            "missing_links": len(missing),
            "bad_anchors": len(bad_anchor),
            "duplicate_ids": len(dups),
            "json_files": len(json_files),
            "invalid_json": len(bad_json),
            "content_leads": len(findings),
        },
        "issues": issues,
        "missing": missing[:40],
        "bad_anchor": bad_anchor[:40],
        "duplicate_id_pages": list(dups)[:40],
        "largest": sizes[:12],
        "content_findings": findings,
        "limits": ("A mechanical audit proves internal consistency and navigability. "
                   "It does not prove any legal proposition, and it does not fetch external URLs."),
    }


def main():
    data = crawl()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    s = data["summary"]
    print(json.dumps({"status": "PASS" if s["missing_links"] == 0 and s["bad_anchors"] == 0
                      and s["duplicate_ids"] == 0 and s["invalid_json"] == 0 else "REVIEW",
                      "summary": s, "issues": data["issues"]}, indent=1))


if __name__ == "__main__":
    main()
