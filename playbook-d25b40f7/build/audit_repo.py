#!/usr/bin/env python3
"""One-off line-by-line scan of every tracked text file outside this directory.

Writes data/repo_audit.json (a committed snapshot, so the site build stays
deterministic while other sessions keep adding files). Re-run by hand only.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "..", "data", "repo_audit.json")
OWN = "playbook-d25b40f7/"

PATTERNS = [
 ("staging", "Emigrant transfer described as staged 50% / 25% / 25%",
  r"50\s*%[^\n]{0,120}?25\s*%[^\n]{0,120}?25\s*%"),
 ("staging_cancelled", "Staging requirement described as cancelled (correct)",
  r"(?i)(cancel|abolish|remov|no longer|取消)[^\n]{0,120}?(stag|instal|tranche|分次)|(stag|instal|tranche|分次)[^\n]{0,120}?(cancel|abolish|remov|no longer|取消)"),
 ("fbar_adjusted", "FBAR maxima quoted at the inflation-adjusted amounts (16,536 / 165,353)",
  r"16,536|165,353"),
 ("fbar_statutory", "FBAR non-willful maximum quoted as the statutory $10,000",
  r"(?i)non-?willful[^\n]{0,100}?\$\s?10,000|\$\s?10,000[^\n]{0,100}?non-?willful"),
 ("crypto_237", "Crypto authority cited as Yinfa [2021] No. 237",
  r"237号|\[2021\]\s*No\.?\s*237|2021[^\n]{0,20}?No\.?\s*237"),
 ("crypto_42", "Crypto authority cited as Yinfa [2026] No. 42",
  r"〔2026〕\s*42号|\[2026\]\s*No\.?\s*42"),
 ("div_2026_27", "FIE dividend rule cited as MOF/STA Announcement 2026 No. 27",
  r"2026年第27号|2026\s*No\.?\s*27\b"),
 ("div_1994_20", "FIE dividend exemption cited from Caishui [1994] No. 20",
  r"〔1994〕\s*20号|\[1994\]\s*(No\.?\s*)?20\b"),
 ("spread_042", "FX spread quoted as 0.42%", r"0\.42\s*%"),
 ("spread_021", "FX one-way margin quoted as about 0.21%", r"0\.21\d*\s*%"),
]

# Earlier-edition candidates that this session did not re-verify. Snapshot only.
NOT_REVERIFIED = ["P05", "P09", "R02", "R05", "R08", "R10", "R12", "R13", "B02", "B03", "B04",
                  "B06", "B07", "B08", "A01", "A02", "A03", "A04", "A05", "X05", "X07"]

def earlier_candidates():
    h = os.path.join(ROOT, "edition-h", "data")
    def rows(name, key):
        d = json.load(open(os.path.join(h, name), encoding="utf-8"))
        return d if isinstance(d, list) else d[key]
    methods = rows("methods.json", "methods")
    sources = {x["id"]: x for x in rows("sources.json", "sources")}
    by = {m["id"]: m for m in methods}
    out = []
    for mid in NOT_REVERIFIED:
        m = by[mid]
        src = [sources[x] for x in m.get("sources", []) if x in sources and sources[x].get("url", "").startswith("http")]
        page = "edition-h/site/method-%s.html" % mid
        assert os.path.exists(os.path.join(ROOT, page)), page
        out.append({"id": mid, "name": m["name"], "category": m["category"], "status": m["status"], "page": page,
                    "sources": [{"id": x["id"], "title": x["title"], "url": x["url"]} for x in src[:2]]})
    with open(os.path.join(HERE, "..", "data", "earlier_candidates.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True); fh.write("\n")
    print("earlier candidates:", len(out), "without source:", [o["id"] for o in out if not o["sources"]])

def main():
    head = subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD"], text=True).strip()
    files = subprocess.check_output(["git", "-C", ROOT, "ls-files"], text=True).splitlines()
    files = [f for f in files if not f.startswith(OWN)]
    stats = {"files": 0, "text_files": 0, "lines": 0, "binary_or_unreadable": 0}
    comp = [(k, d, re.compile(p)) for k, d, p in PATTERNS]
    hits = {k: {"description": d, "regex": p, "total_lines": 0, "by_area": {}, "examples": []}
            for k, d, p in PATTERNS}
    area_lines = {}
    for f in sorted(files):
        stats["files"] += 1
        try:
            with open(os.path.join(ROOT, f), encoding="utf-8") as fh:
                lines = fh.read().split("\n")
        except (UnicodeDecodeError, OSError):
            stats["binary_or_unreadable"] += 1
            continue
        stats["text_files"] += 1
        stats["lines"] += len(lines)
        area = f.split("/")[0] if "/" in f else "(root files)"
        area_lines[area] = area_lines.get(area, 0) + len(lines)
        for n, line in enumerate(lines, 1):
            if len(line) > 20000:      # minified bundles: scan but never quote
                short = None
            else:
                short = line.strip()[:220]
            for k, d, rx in comp:
                if rx.search(line):
                    h = hits[k]
                    h["total_lines"] += 1
                    h["by_area"][area] = h["by_area"].get(area, 0) + 1
                    if short and sum(1 for e in h["examples"] if e["area"] == area) < 2 and len(h["examples"]) < 14:
                        h["examples"].append({"area": area, "file": f, "line": n, "text": short})
    out = {"scanned_commit": head, "scope": "every git-tracked file outside " + OWN,
           "stats": stats, "lines_by_area": dict(sorted(area_lines.items())), "patterns": hits}
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps(stats), head[:7])
    for k in hits:
        print(k, hits[k]["total_lines"], dict(sorted(hits[k]["by_area"].items())))
    earlier_candidates()

if __name__ == "__main__":
    sys.exit(main())
