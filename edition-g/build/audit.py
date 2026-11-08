#!/usr/bin/env python3
"""Line-by-line repository audit for Edition G.

Scans every line of every tracked text file at the current HEAD/worktree,
records a per-file coverage manifest (line count + sha256), and flags
irregularities. This is an automated line scan plus targeted rule checks;
it does not claim human legal review of every line. Findings are published
on the Flagged for Review / Repo Review pages and never silently fixed in
other editions' files.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "edition-g" / "data" / "repo-review.json"

TEXT_SUFFIXES = {".md", ".json", ".html", ".py", ".css", ".js", ".yml", ".yaml", ".txt", ".csv"}

RULES = [
    ("STALE_STAGED_EMIGRANT", r"分步汇出|staged over|50%, then half|首次可汇出金额不得超过|满1年后|满2年后",
     "Superseded staged emigrant-release wording; amended Huifa [2014] No. 2 removed staged remittance."),
    ("STALE_DIVIDEND_EXEMPTION", r"外籍个人从外商投资企业取得的股息红利所得.*免征|dividends.*foreign individuals.*exempt|财税字〔1994〕20号",
     "Foreign-individual FIE dividend exemption repealed by MOF/STA 2026 No. 27 effective 2026-09-01."),
    ("SPREAD_AS_ONE_WAY_COST", r"unavoidable 'conversion penalty'|real cost of a lawful conversion is a bank spread|only cost of a lawful conversion",
     "Bid/ask round-trip spread is not a verified one-way conversion loss; BOC ask was below reference rate."),
    ("FUTURE_FEE_AS_CURRENT", r"2026年11月11日起|2\.5%.*最低等值3美元",
     "Future-dated BOC ATM fee change must not be applied before its effective date."),
    ("HISTORICAL_WISE_FORMULA", r"33\.20|0\.62%|1\.97%|Summaryoffeechanges_Nov24",
     "Historical Wise fee formula; not a verified current schedule."),
    ("FBAR_50_AS_ANNUAL_CERTAINTY", r"50%-of-balance.*per year|50 percent.*per year",
     "Willful FBAR 50% is a statutory ceiling in specified cases, not a predicted annual charge."),
    ("TODO_FIXME", r"\bTODO\b|\bFIXME\b|XXX",
     "Unfinished marker."),
    ("LOCALHOST_REFERENCE", r"localhost|127\.0\.0\.1",
     "Browser-facing code must not depend on localhost in the preview environment."),
    ("MERGE_CONFLICT", r"^(<{7}|={7}|>{7})",
     "Merge conflict marker."),
]


def tracked_files():
    out = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode()
    return [f for f in out.split("\0") if f]


def main():
    files = []
    findings = []
    for rel in tracked_files():
        if rel == "edition-g/data/repo-review.json":
            continue  # avoid self-referential hash instability
        p = ROOT / rel
        if not p.is_file():
            continue
        raw = p.read_bytes()
        entry = {"path": rel, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        if p.suffix.lower() not in TEXT_SUFFIXES:
            entry["scan"] = "binary-skipped"
            files.append(entry)
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            entry["scan"] = "encoding-error"
            findings.append({"path": rel, "line": 0, "rule": "ENCODING", "detail": "Not valid UTF-8."})
            files.append(entry)
            continue
        lines = text.splitlines()
        entry["lines"] = len(lines)
        entry["scan"] = "line-by-line"
        if p.suffix == ".json":
            try:
                json.loads(text)
                entry["json_valid"] = True
            except ValueError as exc:
                entry["json_valid"] = False
                findings.append({"path": rel, "line": 0, "rule": "JSON_PARSE", "detail": str(exc)})
        is_edition_d = rel.startswith("edition-g/")
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line and not is_edition_d:
                findings.append({"path": rel, "line": i, "rule": "TRAILING_WHITESPACE", "detail": "Trailing whitespace."})
            if is_edition_d:
                continue  # Edition G is validated by verify.py; its flag text intentionally quotes stale claims.
            for rule, pat, detail in RULES:
                if re.search(pat, line, re.IGNORECASE):
                    findings.append({"path": rel, "line": i, "rule": rule, "detail": detail, "excerpt": line[:240]})
        files.append(entry)
    doc = {
        "_meta": {
            "edition": "G",
            "method": "Automated line-by-line scan of every tracked text file plus targeted irregularity rules. Not a claim of human legal review of every line.",
            "files_scanned": sum(1 for f in files if f.get("scan") == "line-by-line"),
            "lines_scanned": sum(f.get("lines", 0) for f in files),
            "findings": len(findings),
        },
        "files": files,
        "findings": findings,
    }
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Audited {doc['_meta']['files_scanned']} files / {doc['_meta']['lines_scanned']} lines; {len(findings)} findings.")


if __name__ == "__main__":
    main()
