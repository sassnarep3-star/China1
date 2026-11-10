#!/usr/bin/env python3
"""Snapshot of the repository outside edition-abd04d5f/ for the Repo review page. Run by hand
(python3 edition-abd04d5f/build/inventory.py); it is NOT part of build.py so that later commits by
other sessions cannot make the committed pages look stale in CI."""
import collections, json, os, re, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(ROOT)
files = [f for f in subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split("\n") if f and not f.startswith("edition-abd04d5f/") and f != ".github/workflows/edition-abd04d5f.yml"]
top = collections.OrderedDict(); hosts = collections.Counter(); broken = 0
for f in sorted(files):
    t = f.split("/")[0] if "/" in f else "(root)"
    d = top.setdefault(t, {"files": 0, "html": 0, "tr": 0, "ext_links": 0}); d["files"] += 1
    if not f.endswith(".html"): continue
    s = open(f, encoding="utf-8", errors="replace").read(); d["html"] += 1; d["tr"] += len(re.findall(r"<tr[\s>]", s))
    for h in re.findall(r'href="([^"]+)"', s):
        if h.startswith("http"):
            d["ext_links"] += 1; hosts[re.sub(r"^https?://([^/]+).*", r"\1", h)] += 1
        elif not h.startswith(("#", "mailto:", "javascript:", "data:")):
            p = h.split("#")[0].split("?")[0]
            if not p: continue
            tgt = os.path.normpath(os.path.join(os.path.dirname(f), p))
            if os.path.isdir(tgt): tgt = os.path.join(tgt, "index.html")
            if not os.path.exists(tgt): broken += 1
commit = subprocess.run(["git", "merge-base", "HEAD", "origin/main"], capture_output=True, text=True).stdout.strip()
json.dump({"snapshot_commit": commit, "dirs": top, "broken_local_links": broken, "hosts": sorted(hosts.items(), key=lambda x: (-x[1], x[0]))},
          open("edition-abd04d5f/data/repo_inventory.json", "w"), indent=1)
tot = {k: sum(v[k] for v in top.values()) for k in ("files", "html", "tr", "ext_links")}
print(commit[:7], tot, "broken:", broken, "hosts:", len(hosts), "folders:", len(top))
