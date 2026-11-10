"""Edition J verifier — independent recomputation and integrity checks.

Recomputes every priced cell from data/model.json (not from build.py internals),
checks the exact 40-target grid, UNVERIFIED markers on every unconfirmed cell,
internal link/anchor resolution, external URLs restricted to registered sources,
prohibited methods carry no steps, and byte-identical rebuild.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DATA = ROOT / "data"

errors: list[str] = []
checks = 0


def check(cond: bool, msg: str) -> None:
    global checks
    checks += 1
    if not cond:
        errors.append(msg)


def q2(x: Decimal) -> Decimal:
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


model = json.loads((DATA / "model.json").read_text())
sources = json.loads((DATA / "sources.json").read_text())
methods = json.loads((DATA / "methods.json").read_text())
costs = json.loads((DATA / "costs.json").read_text())

SELL = Decimal(str(model["sell_rate_cny_per_usd"]))
BUY = Decimal(str(model["buy_rate_cny_per_usd"]))
MID = (Decimal(model["usd_per_100"]["buy"]) + Decimal(model["usd_per_100"]["sell"])) / 2 / 100
FXM = (Decimal(model["usd_per_100"]["sell"]) - MID * 100) / (MID * 100)
TARGETS = list(range(10_000, 400_001, 10_000))

# --- 1. Independent recomputation of every priced cell ---
for t in TARGETS:
    p = Decimal(t) * SELL
    boc = min(Decimal("260"), max(Decimal("50"), Decimal("0.001") * p)) + Decimal("150")
    hsbc = min(Decimal("500"), max(Decimal("100"), Decimal("0.001") * p)) + Decimal("120")
    fx = q2(Decimal(t) * FXM)
    check(Decimal(costs["boc_sender_cny"][str(t)]) == boc, f"BOC sender mismatch at {t}")
    check(Decimal(costs["hsbc_sender_cny"][str(t)]) == hsbc, f"HSBC sender mismatch at {t}")
    check(Decimal(costs["boc_subtotal_usd"][str(t)]) == q2(fx + boc / SELL), f"BOC subtotal mismatch at {t}")
    check(Decimal(costs["hsbc_subtotal_usd"][str(t)]) == q2(fx + hsbc / SELL), f"HSBC subtotal mismatch at {t}")
    # tranche recomputation
    def tr_sub(sender_fn):
        tot = Decimal("0")
        rem = t
        while rem > 0:
            take = min(50_000, rem)
            pp = Decimal(take) * SELL
            tot += q2(Decimal(take) * FXM) + sender_fn(pp) / SELL
            rem -= take
        return q2(tot)
    check(Decimal(costs["boc_tranche_subtotal_usd"][str(t)]) == tr_sub(lambda pp: min(Decimal("260"), max(Decimal("50"), Decimal("0.001") * pp)) + Decimal("150")),
          f"BOC tranche mismatch at {t}")
    check(Decimal(costs["hsbc_tranche_subtotal_usd"][str(t)]) == tr_sub(lambda pp: min(Decimal("500"), max(Decimal("100"), Decimal("0.001") * pp)) + Decimal("120")),
          f"HSBC tranche mismatch at {t}")

# Fixed endpoints (hand-computed from the fetched tariffs; sender stored unrounded, compared at 2dp)
check(q2(Decimal(costs["boc_sender_cny"]["10000"])) == Decimal("216.87"), "BOC 10k endpoint")
check(q2(Decimal(costs["boc_sender_cny"]["400000"])) == Decimal("410.00"), "BOC 400k endpoint")
check(q2(Decimal(costs["hsbc_sender_cny"]["10000"])) == Decimal("220.00"), "HSBC 10k endpoint")
check(q2(Decimal(costs["hsbc_sender_cny"]["400000"])) == Decimal("620.00"), "HSBC 400k endpoint")
check(Decimal(costs["boc_subtotal_usd"]["10000"]) == Decimal("53.41"), "BOC subtotal 10k endpoint")
check(Decimal(costs["boc_subtotal_usd"]["400000"]) == Decimal("900.57"), "BOC subtotal 400k endpoint")
check(Decimal(costs["hsbc_subtotal_usd"]["400000"]) == Decimal("931.97"), "HSBC subtotal 400k endpoint")

# --- 2. Grid shape ---
check(len(TARGETS) == 40 and TARGETS[0] == 10_000 and TARGETS[-1] == 400_000, "40-target grid")
check(len(costs["targets"]) == 40, "costs.json 40 targets")

# --- 3. HTML checks ---
PAGES = ["index.html", "executive-summary.html", "methods.html", "steps.html",
         "costs.html", "taxes.html", "sources.html", "flagged.html", "methodology.html"]
allowed_hosts = set()
for s in sources.values():
    allowed_hosts.add(re.sub(r"^https?://([^/]+).*$", r"\1", s["url"]))

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []
        self.ids: set[str] = set()
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d:
            self.ids.add(d["id"])
        if tag == "a" and "href" in d:
            self.links.append(d["href"])

all_ids: dict[str, set[str]] = {}
for pg in PAGES:
    p = SITE / pg
    check(p.exists(), f"missing page {pg}")
    if not p.exists():
        continue
    html = p.read_text()
    parser = LinkParser()
    parser.feed(html)
    all_ids[pg] = parser.ids
    # every table row must carry a source link (except header)
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.S)
    for r in rows:
        if "<th" in r:
            continue
        check('class="source"' in r or 'href="http' in r, f"{pg}: table row without source link: {r[:100]}")
    # external links restricted to registered sources
    for href in parser.links:
        if href.startswith("http"):
            host = re.sub(r"^https?://([^/]+).*$", r"\1", href)
            check(host in allowed_hosts, f"{pg}: unregistered external host {host}")
            check(href in [s["url"] for s in sources.values()], f"{pg}: external URL not in registry: {href}")
    # internal links resolve
    for href in parser.links:
        if href.startswith("http") or href.startswith("mailto:"):
            continue
        if href.startswith("#"):
            frag = href[1:]
            check(frag in parser.ids, f"{pg}: unresolved fragment {href}")
        else:
            target, _, frag = href.partition("#")
            if target.startswith("../"):
                # portal / audit links: resolve against repo root
                resolved = (SITE / target).resolve()
                check(resolved.exists(), f"{pg}: missing local target {href}")
            else:
                check((SITE / target).exists(), f"{pg}: missing local target {href}")
                if frag:
                    check(frag in all_ids.get(target, set()), f"{pg}: unresolved fragment {href}")

# --- 4. Blank semantics: every cost ladder row has UNVERIFIED where all-in is blank ---
costs_html = (SITE / "costs.html").read_text()
check(costs_html.count("UNVERIFIED") >= 320, f"costs.html UNVERIFIED markers: {costs_html.count('UNVERIFIED')}")
check("Blank = unverified, never zero" in (SITE / "index.html").read_text(), "blank disclaimer present")

# --- 5. Prohibited methods carry no steps ---
for m in methods:
    if m["status"].startswith("Prohibited"):
        check(m["steps"] == [], f"{m['id']} prohibited but has steps")
    else:
        check(len(m["steps"]) >= 2, f"{m['id']} lawful but missing steps")

# --- 6. CSV shape ---
csv_lines = (SITE / "costs.csv").read_text().strip().splitlines()
check(len(csv_lines) == 1 + 320, f"costs.csv rows: {len(csv_lines)}")
check(all(l.split(",")[5] == "" for l in csv_lines[1:]), "costs.csv all-in column must be blank")

# --- 7. Byte-identical rebuild ---
def snapshot_hashes() -> dict[str, str]:
    h = {}
    for f in sorted(SITE.rglob("*")):
        if f.is_file():
            h[str(f.relative_to(ROOT))] = hashlib.sha256(f.read_bytes()).hexdigest()
    for f in sorted(DATA.rglob("*")):
        if f.is_file():
            h[str(f.relative_to(ROOT))] = hashlib.sha256(f.read_bytes()).hexdigest()
    return h

before = snapshot_hashes()
subprocess.run([sys.executable, str(ROOT / "build" / "build.py")], check=True, capture_output=True)
after = snapshot_hashes()
check(before == after, "rebuild is not byte-identical")

print(f"edition-j verify: {checks} checks, {len(errors)} errors")
for err in errors[:30]:
    print("ERROR:", err)
sys.exit(1 if errors else 0)
