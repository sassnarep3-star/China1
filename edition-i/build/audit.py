#!/usr/bin/env python3
"""Deterministic line-by-line audit of the inherited repository.

The audit reads every tracked blob at the branch-point commit, not a moving
worktree. Edition I's own files, later coordination appends and open PRs are
therefore outside this snapshot. It records a hash and line count for every
text file and every line-level match of the claim/dead-link patterns below.
No inherited file is edited.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                 # edition-i/
REPO_ROOT = os.path.dirname(ROOT)            # repository root
sys.path.insert(0, HERE)
import model as M  # noqa: E402

SOURCE_BY_ID = {s["id"]: s for s in M.SOURCES}

PATTERNS = [
    ("P01", r"0\.42%|0\.420|0\.4199", "BOC board full spread used as a one-way cost", ["BOC-FX-BOARD"]),
    ("P02", r"分步汇出|分次汇出|staged release|three years|3 years", "Superseded staged emigration release", ["CN-CAP-2014"]),
    ("P03", r"1994.*exemption|1994.*免税|财税.{0,4}1994.{0,4}20|Caishui \[1994\]", "Repealed foreign-individual dividend exemption", ["CN-DIV-2026"]),
    ("P04", r"1% remittance|1% excise|remittance transfer tax|4475", "US 1% remittance excise tax scope", ["US-REMIT-TAX", "US-OBBBA"]),
    ("P05", r"\$100,000|USD 100,000|100,000.*FBAR|non-willful.{0,30}10,000", "FBAR statutory amounts without inflation adjustment", ["US-1010-821"]),
    ("P06", r"uscode\.house\.gov|granuleid", "Dead uscode.house.gov granuleid links", ["US-988", "US-5321"]),
    ("P07", r"fincen\.gov/reporting-international-transportation", "Dead FinCEN Form 105 link", ["US-CBP-CASH"]),
    ("P08", r"changsha_customs.{0,80}1316760", "HTTP 404 Changsha Customs link", ["CN-CASH-CUSTOMS"]),
    ("P09", r"xiamen\.chinatax\.gov\.cn/fgk/L4529", "HTTP 500 Xiamen tax link", ["CN-IIT-LAW"]),
    ("P10", r"m\.mof\.gov\.cn/zcjd/200810/t20081010_81240", "HTTP 502 MOF interest link", ["CN-INTEREST-2008"]),
    ("P11", r"wise\.com/pricing/send-money\?sourceCurrency=CNY", "Lost Wise general pricing link", ["WISE-GUIDE"]),
    ("P12", r"50% of the transferred|50%-of-transfer|50% of the transfer", "FBAR 50% basis misstated as transferred amount", ["US-5321"]),
    ("P13", r"0\.2104%|0\.2100%", "One-way spread derived from a different posted board", ["BOC-FX-BOARD"]),
    ("P14", r"2013 No\.40|2013年第40号|汇发.{0,4}2013.{0,4}40|40号公告", "2013 tax-filing vintage without 2021 repeal note", ["CN-TAXFILING-2021"]),
]


def git(*args):
    return subprocess.run(["git", "-C", REPO_ROOT, *args], check=True, capture_output=True).stdout


def blob_url(path):
    return f"https://github.com/sassnarep3-star/China1/blob/{M.REPO_BASE_COMMIT}/{path}"


def md_escape(s):
    return str(s).replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def sources_md(ids):
    return ", ".join(f"[{i}]({SOURCE_BY_ID[i]['url']})" for i in ids if i in SOURCE_BY_ID)


def scan():
    raw_paths = git("ls-tree", "-r", "--name-only", "-z", M.REPO_BASE_COMMIT)
    paths = sorted(p.decode("utf-8", "replace") for p in raw_paths.split(b"\0") if p)
    files = []
    hits = []
    skipped_binary = []
    total_lines = 0
    compiled = [(pid, re.compile(rx, re.IGNORECASE), label, ids) for pid, rx, label, ids in PATTERNS]
    for path in paths:
        raw = git("show", f"{M.REPO_BASE_COMMIT}:{path}")
        digest = hashlib.sha256(raw).hexdigest()
        if b"\x00" in raw:
            skipped_binary.append(dict(path=path, sha256=digest, bytes=len(raw)))
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            skipped_binary.append(dict(path=path, sha256=digest, bytes=len(raw)))
            continue
        lines = text.splitlines()
        total_lines += len(lines)
        files.append(dict(path=path, sha256=digest, bytes=len(raw), lines=len(lines),
                          blob_url=blob_url(path)))
        for lineno, line in enumerate(lines, 1):
            snippet = re.sub(r"\s+", " ", line.strip())[:240]
            for pid, rx, label, ids in compiled:
                if rx.search(line):
                    hits.append(dict(pattern_id=pid, label=label, path=path,
                                     line=lineno, snippet=snippet,
                                     blob_url=f"{blob_url(path)}#L{lineno}",
                                     official_sources=ids))
    hits.sort(key=lambda h: (h["pattern_id"], h["path"], h["line"]))
    return dict(
        session=M.SESSION,
        retrieved=M.RETRIEVED,
        base_commit=M.REPO_BASE_COMMIT,
        method="Every tracked blob at the branch-point commit was read line by line with a deterministic UTF-8 line iterator; binary blobs were hashed and skipped.",
        total_tracked_files=len(paths),
        text_files_scanned=len(files),
        binary_files_skipped=len(skipped_binary),
        lines_scanned=total_lines,
        line_level_matches=len(hits),
        patterns=[dict(id=p, regex=r, label=l, official_sources=s) for p, r, l, s in PATTERNS],
        files=files,
        skipped_binary=skipped_binary,
        hits=hits,
        repo_review_findings=M.REPO_REVIEW,
        dead_ends=M.DEAD_ENDS,
        scope_note="Edition I did not edit any file outside edition-i/**, an additive COORDINATION.md/README.md section, and its own workflow. Open PRs #12 and #14 were not merged, closed or overwritten.",
    )


def write(data, data_dir, research_dir):
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(research_dir, exist_ok=True)
    with open(os.path.join(data_dir, "repo_audit.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")

    out = []
    out.append("# Line-by-line repository audit — Edition I\n")
    out.append(f"Session `{M.SESSION}` · branch-point commit `{M.REPO_BASE_COMMIT}` · retrieved {M.RETRIEVED} UTC.\n")
    out.append("This audit is a deterministic snapshot of the **inherited** repository. It reads every tracked blob at the branch-point commit, line by line, so later Edition I files and coordination appends cannot change the result. It is not a claim that each legal proposition in those files is correct; the proposition-level corrections are in the findings below and on the site's [Repository review](../site/repo-review.html) page.\n")
    out.append("## Coverage\n")
    out.append(f"- **{data['total_tracked_files']}** tracked files at the base commit.\n")
    out.append(f"- **{data['text_files_scanned']}** text files scanned, **{data['lines_scanned']:,}** lines read.\n")
    out.append(f"- **{data['binary_files_skipped']}** binary blobs hashed and skipped (no line-level claim asserted).\n")
    out.append(f"- **{data['line_level_matches']:,}** line-level pattern matches across {len(PATTERNS)} audited claim / dead-link patterns.\n")
    out.append("- Every text line was iterated; pattern matches were captured with file, line number, short snippet and a manual-review blob link. No inherited file was modified.\n")
    out.append("\n## Audited patterns\n")
    out.append("| Pattern | Why it was checked | Matches | Official sources |\n|---|---|---:|---|\n")
    by_pid = {}
    for h in data["hits"]:
        by_pid.setdefault(h["pattern_id"], []).append(h)
    for pid, rx, label, ids in PATTERNS:
        out.append(f"| {pid} · {md_escape(label)} | `{md_escape(rx)}` | {len(by_pid.get(pid, []))} | {sources_md(ids)} |\n")
    out.append("\n### Representative line-level hits\n")
    out.append("| Pattern | File / line | Snippet | Manual review | Official sources |\n|---|---|---|---|---|\n")
    for pid, rx, label, ids in PATTERNS:
        sample = by_pid.get(pid, [])[:6]
        if not sample:
            out.append(f"| {pid} | none | — | — | {sources_md(ids)} |\n")
        for h in sample:
            out.append(f"| {pid} | `{md_escape(h['path'])}`:{h['line']} | {md_escape(h['snippet'])} | [open blob line]({h['blob_url']}) | {sources_md(h['official_sources'])} |\n")
    out.append("\nThe complete list of matches, with SHA-256 hashes for every inherited text file and skipped binary blob, is in [`data/repo_audit.json`](../data/repo_audit.json).\n")

    out.append("\n## Proposition-level findings (R01–R15)\n")
    out.append("| ID | Finding | Disposition in Edition I | Official sources |\n|---|---|---|---|\n")
    for r in M.REPO_REVIEW:
        out.append(f"| {r['id']} | {md_escape(r['finding'])} | {md_escape(r['disposition'])} | {sources_md(r['sources'])} |\n")

    out.append("\n## Observed dead ends and official replacements\n")
    out.append("| URL retrieved | Result | Replacement / note | Official sources |\n|---|---|---|---|\n")
    for d in M.DEAD_ENDS:
        out.append(f"| `{md_escape(d['url'])}` | {md_escape(d['status'])} | {md_escape(d['note'])} | {sources_md(d['replacement'])} |\n")

    out.append("\n## Complete inherited-file inventory\n")
    out.append("Each entry is a manual-review blob link at the pinned branch-point commit; the SHA-256 and line count are in `data/repo_audit.json`.\n\n")
    for f in data["files"]:
        out.append(f"- [`{f['path']}`]({f['blob_url']}) — {f['lines']:,} lines, `{f['sha256'][:12]}…`\n")
    for b in data["skipped_binary"]:
        out.append(f"- [`{b['path']}`]({blob_url(b['path'])}) — binary, {b['bytes']:,} bytes, `{b['sha256'][:12]}…`\n")

    out.append("\n## Coordination scope\n")
    out.append(data["scope_note"] + "\n")
    with open(os.path.join(research_dir, "repo-audit.md"), "w", encoding="utf-8") as f:
        f.write("".join(out))


def main():
    data = scan()
    write(data, os.path.join(ROOT, "data"), os.path.join(ROOT, "research"))
    print(f"Audited {data['total_tracked_files']} files / {data['lines_scanned']:,} lines / "
          f"{data['line_level_matches']:,} matches at {data['base_commit'][:8]}.")


if __name__ == "__main__":
    main()
