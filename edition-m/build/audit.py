#!/usr/bin/env python3
"""Line-by-line scan of the rest of the repository against figures read on 2026-11-10.

Run from the repository root:  python3 edition-m/build/audit.py
Writes edition-m/data/audit_scan.json. It is NOT run in CI: the result depends on the
other editions, which other sessions may still change.
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "edition-m" / "data" / "audit_scan.json"
TEXT_EXT = {".md", ".json", ".html", ".py", ".csv", ".yml", ".yaml", ".txt", ".css", ".js"}

OFFICIAL_SUFFIXES = (
    ".gov.cn", ".gov", ".gov.hk", "boc.cn", "bankofchina.com", "icbc.com.cn", "icbcasia.com",
    "hsbc.com.cn", "ccb.com", "cmbchina.com", "sc.com", "wise.com", "chase.com", "schwab.com",
    "bankofamerica.com", "westernunion.com", "moneygram.com", "paypal.com", "skyremit.cn",
    "chinamoney.com.cn", "hkex.com.hk", "uscode.house.gov",
)
OWN_HOSTS = ("github.com", "sassnarep3-star.github.io", "githubusercontent.com")

CHECKS = [
    # id, title, regex that selects a line, regex for the figure, values read today, source ids
    ("K01", "Bank of China wire commission cap (CNY per wire)",
     r"(?i)(bank of china|\bBOC\b|中国银行|中行).{0,160}(max|maximum|最高|cap)", r"\b(2[0-9]0)\b", {"260"}, ["S32"]),
    ("K02", "Bank of China international cable fee (CNY)",
     r"(?i)(cable|电讯费|电报费).{0,60}(CNY|RMB|元|¥)\s?\d|(CNY|RMB|¥)\s?\d{2,3}.{0,30}cable", r"\b(80|100|120|140|150|200)\b", {"150", "80", "120"}, ["S32", "S35"]),
    ("K03", "FBAR non-willful penalty, inflation-adjusted (USD)",
     r"(?i)non-?willful", r"\b(1[2-9],\d{3})\b", {"16,536"}, ["S58"]),
    ("K04", "FBAR willful penalty floor, inflation-adjusted (USD)",
     r"(?i)willful", r"\b(1[2-9]\d,\d{3})\b", {"165,353", "100,000", "150,000"}, ["S58"]),
    ("K05", "Form 3520 threshold for purported gifts from foreign entities (USD)",
     r"(?i)(3520|foreign (corporation|partnership|entit))", r"\b(1[5-9],\d{3}|2[0-2],\d{3})\b", {"20,573", "20,116"}, ["S51"]),
    ("K06", "Wise cap per transfer from a bank app (CNY)",
     r"(?i)wise.{0,200}(bank app|per transfer|per-transfer|single transfer)", r"\b(\d{2,3},000)\b", {"300,000", "50,000"}, ["S37"]),
    ("K07", "Overseas card cash cap per calendar year (CNY)",
     r"(?i)(ATM|card|银行卡).{0,120}(year|年)", r"\b(100,000|10万|50,000|5万)\b", {"100,000", "10万"}, ["S15"]),
    ("K08", "SAFE decision period for property-transfer approval (working days)",
     r"(?i)(working days|个工作日)", r"\b(\d{1,2})\s?(?:working days|个工作日)", {"20", "5", "10", "30"}, ["S07"]),
    ("K09", "Chase incoming wire fee (USD)",
     r"(?i)chase.{0,160}(incoming|inbound|receiv)", r"\$\s?(\d{1,2})\b|USD\s?(\d{1,2})\b", {"15", "0"}, ["S40"]),
]

BOARD_RE = re.compile(r"\b(66[0-9]\.[0-9]{2})\b")
URL_RE = re.compile(r"https?://[^\s\"'<>)\]\\]+")
REPEALED_RE = re.compile(r"(〔2021〕237号|\[2021\] ?No\. ?237|2021 No\. ?237)")
DEAD_IRS = "irs.gov/individuals/international-taxpayers/delinquent-fbar-submission-procedures"


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    files = []
    for name in out.splitlines():
        if name.startswith("edition-m/") or name.startswith(".github/workflows/edition-m"):
            continue
        p = ROOT / name
        if p.suffix.lower() in TEXT_EXT and p.is_file():
            files.append(p)
    return files


def area(rel: str) -> str:
    return rel.split("/")[0] if "/" in rel else "(root)"


def main() -> None:
    head = subprocess.run(["git", "rev-parse", "--short", "origin/main"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    files = tracked_files()
    n_lines = 0
    per_area_files = Counter()
    per_area_lines = Counter()
    check_hits = {c[0]: {"same": 0, "other": Counter(), "examples": []} for c in CHECKS}
    board = defaultdict(Counter)
    hosts = Counter()
    unofficial = defaultdict(set)
    plain_http = defaultdict(set)
    repealed = Counter()
    dead = []

    compiled = [(cid, re.compile(sel), re.compile(fig), vals) for cid, _t, sel, fig, vals, _s in CHECKS]

    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        a = area(rel)
        per_area_files[a] += 1
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            n_lines += 1
            per_area_lines[a] += 1
            if len(line) > 6000:      # minified blobs: URL scan only
                scan = line[:6000]
            else:
                scan = line
            for u in URL_RE.findall(line):
                h = re.sub(r"^https?://", "", u).split("/")[0].lower()
                hosts[h] += 1
                if h.endswith(OWN_HOSTS) or h in ("www.w3.org", "schema.org", "localhost", "example.com"):
                    continue
                if not h.endswith(OFFICIAL_SUFFIXES):
                    unofficial[h].add(rel)
                elif u.startswith("http://"):
                    plain_http[h].add(rel)
                if DEAD_IRS in u:
                    dead.append(f"{rel}:{i}")
            if REPEALED_RE.search(scan):
                repealed[a] += 1
            for m in BOARD_RE.findall(scan):
                if re.search(r"(?i)(usd|美元|board|牌价|bid|ask|sell|buy|现汇|rate)", scan):
                    board[m][a] += 1
            for cid, sel, fig, vals in compiled:
                if not sel.search(scan):
                    continue
                found = [x for t in fig.findall(scan) for x in (t if isinstance(t, tuple) else (t,)) if x]
                for v in found:
                    if v in vals:
                        check_hits[cid]["same"] += 1
                    else:
                        check_hits[cid]["other"][v] += 1
                        if len(check_hits[cid]["examples"]) < 6:
                            check_hits[cid]["examples"].append({"where": f"{rel}:{i}", "value": v, "text": scan.strip()[:220]})

    norm = lambda u: u.replace("http://", "https://").replace("//m.safe.gov.cn", "//www.safe.gov.cn").rstrip("/")
    mine = {norm(x["url"]) for x in json.loads((ROOT / "edition-m" / "data" / "sources.json").read_text(encoding="utf-8"))["sources"]}
    portal = json.loads((ROOT / "integration" / "evidence.json").read_text(encoding="utf-8"))["sources"]
    portal = list(portal.values()) if isinstance(portal, dict) else portal
    reread = sum(1 for x in portal if norm(x.get("url", "")) in mine)

    result = {
        "scanned_commit": head,
        "portal_sources": len(portal),
        "portal_reread": reread,
        "scanned_on": "2026-11-10",
        "scope": "Every tracked text file outside edition-m/ (md, json, html, py, csv, yml, txt, css, js), read line by line.",
        "files": len(files),
        "lines": n_lines,
        "by_area": [{"area": a, "files": per_area_files[a], "lines": per_area_lines[a]} for a in sorted(per_area_files)],
        "checks": [
            {"id": cid, "title": title, "read_today": sorted(vals), "src": srcs,
             "lines_matching_today": check_hits[cid]["same"],
             "other_values": [{"value": v, "lines": n} for v, n in check_hits[cid]["other"].most_common(8)],
             "examples": check_hits[cid]["examples"]}
            for cid, title, _sel, _fig, vals, srcs in CHECKS
        ],
        "board_values": [{"value": v, "lines": sum(c.values()), "areas": sorted(c)} for v, c in sorted(board.items())],
        "distinct_hosts": len(hosts),
        "unofficial_hosts": [{"host": h, "files": len(f), "example": sorted(f)[0]} for h, f in sorted(unofficial.items())],
        "plain_http_official": [{"host": h, "files": len(f), "example": sorted(f)[0]} for h, f in sorted(plain_http.items())],
        "repealed_2021_crypto_notice_lines": [{"area": a, "lines": n} for a, n in sorted(repealed.items())],
        "dead_irs_link_uses": dead,
    }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"scanned {len(files)} files, {n_lines} lines at {head}; wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
