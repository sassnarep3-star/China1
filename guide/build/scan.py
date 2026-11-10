#!/usr/bin/env python3
"""Line-by-line rule scan of the archived parts of the repository.

Reads every line of every tracked text file in the scope listed in
guide/data/review.json, applies each rule's regular expression, and writes a
snapshot (guide/data/scan.json and guide/data/scan-hits.csv). The snapshot is
committed and treated as input by build.py; it is NOT re-run in CI, so later
changes to archived files do not silently rewrite published pages.
Standard library only.
"""
import csv, json, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "guide" / "data"
review = json.loads((DATA / "review.json").read_text(encoding="utf-8"))
tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split("\n")
tracked = sorted(set(t for t in tracked if t))
for extra in ("legacy-portal.html",):
    if (ROOT / extra).exists() and extra not in tracked:
        tracked.append(extra)
scope = review["scope"]
rules = [(r, re.compile(r["pattern"]), re.compile(r["ok_if"], re.I) if r["ok_if"] else None) for r in review["rules"]]

def top(path):
    return path.split("/")[0]

areas, hits = {}, []
for rel in sorted(tracked):
    if top(rel) not in scope:
        continue
    p = ROOT / rel
    if not p.is_file():
        continue
    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        a = areas.setdefault(top(rel), {"files": 0, "lines": 0, "binary": 0, "hits": 0})
        a["binary"] += 1
        continue
    lines = text.split("\n")
    a = areas.setdefault(top(rel), {"files": 0, "lines": 0, "binary": 0, "hits": 0})
    a["files"] += 1
    a["lines"] += len(lines)
    for n, line in enumerate(lines, 1):
        for rule, rx, ok in rules:
            m = rx.search(line)
            if not m:
                continue
            lo, hi = max(0, m.start() - 70), min(len(line), m.end() + 70)
            ctx = line[max(0, m.start() - 200):m.end() + 200]
            state = "consistent" if (ok is not None and ok.search(ctx)) else "check"
            hits.append({"rule": rule["id"], "file": rel, "line": n, "state": state,
                         "excerpt": re.sub(r"\s+", " ", line[lo:hi]).strip()})
            a["hits"] += 1

summary = {}
for r in review["rules"]:
    hs = [h for h in hits if h["rule"] == r["id"]]
    summary[r["id"]] = {
        "lines": len(hs), "files": len({h["file"] for h in hs}),
        "check": sum(h["state"] == "check" for h in hs),
        "consistent": sum(h["state"] == "consistent" for h in hs),
        "examples": [h for h in hs if h["state"] == "check"][:3] or hs[:3],
    }
head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
out = {"scanned_at_commit": head, "areas": areas,
       "total_files": sum(a["files"] for a in areas.values()),
       "total_lines": sum(a["lines"] for a in areas.values()),
       "total_hits": len(hits), "rules": summary}
(DATA / "scan.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
with (DATA / "scan-hits.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["rule", "state", "file", "line", "excerpt"])
    for h in hits:
        w.writerow([h["rule"], h["state"], h["file"], h["line"], h["excerpt"]])
print(f"scanned {out['total_files']} files / {out['total_lines']} lines; {len(hits)} rule hits")
