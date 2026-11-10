#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent checks of the Playbook. Standard library only.

Recomputes every cost row with exact fractions from data/parameters.json (not
from the build's model), re-checks that each input appears verbatim in its
quoted source, crawls every local link and anchor, and enforces the table rules.
"""
import csv, glob, hashlib, json, os, re, subprocess, sys
from decimal import Decimal as D
from fractions import Fraction as Fr
from html.parser import HTMLParser
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))
ERR = []
HOSTS = ("gov.cn", "safe.gov.cn", "pbc.gov.cn", "chinatax.gov.cn", "boc.cn", "bankofchina.com", "hsbc.com.cn",
         "irs.gov", "ecfr.gov", "govinfo.gov", "cbp.gov", "wise.com", "chase.com")


def bad(msg):
    ERR.append(msg)


def load(name):
    return json.load(open(os.path.join(OUT, name), encoding="utf-8"))


def r2(x, dp=2):
    """Round a non-negative Fraction half-up to dp places, as a Decimal."""
    k = 10 ** dp
    n = (x * k * 2 + 1).__floor__() // 2
    return D(n) / D(k)


# ---------- 1. evidence
def check_evidence():
    ev = {}
    for f in sorted(glob.glob(os.path.join(OUT, "research", "evidence_*.json"))):
        for s in json.load(open(f, encoding="utf-8")):
            if s["id"] in ev:
                bad("duplicate source id " + s["id"])
            ev[s["id"]] = s
            for k in ("title", "issuer", "kind", "url", "retrieved_utc", "retrieval", "quotes"):
                if not s.get(k):
                    bad("%s missing %s" % (s["id"], k))
            host = urlparse(s["url"]).hostname or ""
            if not any(host == h or host.endswith("." + h) for h in HOSTS):
                bad("%s host not on the official list: %s" % (s["id"], host))
            if s["kind"] not in ("official", "provider-primary"):
                bad("%s kind" % s["id"])
            for qd in s["quotes"]:
                if not qd.get("text") or not qd.get("loc"):
                    bad("%s empty quote" % s["id"])
    exported = {s["id"]: s for s in load("data/sources.json")}
    if exported != ev:
        bad("data/sources.json differs from research/evidence_*.json")
    return ev


def check_params(ev):
    prm = load("data/parameters.json")
    for k, v in prm.items():
        text = " ".join(x["text"] for x in ev[v["source"]]["quotes"])
        if v["text_in_source"] not in text:
            bad("parameter %s: text not found in %s" % (k, v["source"]))
    for wq in load("data/wise_quotes.json"):
        text = " ".join(x["text"] for x in ev[wq["source"]]["quotes"]).replace(",", "")
        if "%s CNY" % wq["cny_sent"] not in text or "%s CNY" % wq["fee_cny"] not in text:
            bad("wise quote %s not found in %s" % (wq["cny_sent"], wq["source"]))
    return {k: Fr(v["value"]) for k, v in prm.items()}


# ---------- 2. independent cost model
def expected(P, wise, model, a):
    bid, ask = P["boc_bid"] / 100, P["boc_ask"] / 100
    mid = (bid + ask) / 2
    one = (ask - mid) / mid

    def boc(x, fx=True, full=True):
        comm = min(P["boc_comm_max_cny"], max(P["boc_comm_min_cny"], P["boc_comm_rate"] * x * mid))
        return [x * one if fx else Fr(0), (comm + P["boc_cable_cny"]) / mid,
                P["boc_full_arrival_usd"] if full else None, P["chase_incoming_usd"]]
    fx = fees = addon = recv = None
    if model in ("boc_full", "boc_property"):
        fx, fees, addon, recv = boc(a)
    elif model == "boc_sha":
        fx, fees, addon, recv = boc(a, full=False)
    elif model == "boc_wire_only":
        fx, fees, addon, recv = boc(a, fx=False)
    elif model == "boc_quota":
        parts, left = [], a
        while left > 0:
            parts.append(min(left, P["quota_usd"]))
            left -= parts[-1]
        cols = list(zip(*[boc(x) for x in parts]))
        fx, fees, addon, recv = [sum(c) for c in cols]
    elif model == "hsbc_premier":
        comm = min(P["hsbc_comm_max_cny"], max(P["hsbc_comm_min_cny"], P["hsbc_comm_rate"] * a * mid))
        fees, addon, recv = (comm + P["hsbc_cable_cny"]) / mid, P["hsbc_payexact_cny"] / mid, P["chase_incoming_usd"]
    elif model == "hsbc_pb":
        fees, recv = Fr(0), P["chase_incoming_usd"]
    elif model == "wise":
        sent = a * mid
        hit = [k for k in wise if abs(k - sent) <= 1]
        if hit:
            fx, fees, addon = Fr(0), wise[hit[0]] / mid, Fr(0)
    elif model == "boc_dividend":
        pass
    elif model in ("cash", "small_recon"):
        fx, fees, addon = a * one, Fr(0), Fr(0)
    elif model == "atm":
        left, fee = a * mid, Fr(0)
        while left > 0:
            x = min(left, P["card_day_cny"])
            fee += min(P["atm_max_cny"], P["atm_fixed_cny"] + P["atm_rate"] * x)
            left -= x
        fees = fee / mid
    else:
        bad("unknown model " + model)
    parts = [fx, fees, addon, recv]
    known = [x for x in parts if x is not None]
    total = sum(known) if len(known) == 4 else None
    pub = sum(known) if known and model != "boc_dividend" else None
    return {"exchange_margin_usd": fx, "bank_fees_usd": fees, "addon_usd": addon, "receiving_usd": recv,
            "published_costs_usd": pub, "total_usd": total,
            "china_tax_usd": a * P["div_rate"] if model == "boc_dividend" else None,
            "deemed_tax_low_usd": a * P["deemed_low"] if model == "boc_property" else None,
            "deemed_tax_high_usd": a * P["deemed_high"] if model == "boc_property" else None,
            "cny_to_buy": a * ask if model in ("boc_full", "boc_sha", "boc_quota", "boc_property", "cash", "small_recon") else None}


def check_costs(P):
    costs = load("data/costs.json")
    wise = {Fr(x["cny_sent"]): Fr(x["fee_cny"]) for x in load("data/wise_quotes.json")}
    flags = {f["id"] for f in load("data/flags.json")}
    methods = {m["id"]: m for m in load("data/methods.json")}
    by = {}
    for r in costs["rows"]:
        by.setdefault(r["method_id"], []).append(r)
    want = [m for m in methods.values() if m["model"]]
    if set(by) != {m["id"] for m in want}:
        bad("cost ladders do not cover every costed method")
    n_checked = 0
    for mid_, rows in by.items():
        if [r["amount_usd"] for r in rows] != [str(10000 * i) for i in range(1, 41)]:
            bad("%s: amounts are not 10,000..400,000 in 40 steps" % mid_)
        for r in rows:
            exp = expected(P, wise, r["model"], Fr(r["amount_usd"]))
            for k, v in exp.items():
                got = r[k]
                if (v is None) != (got is None):
                    bad("%s %s %s: blank mismatch" % (mid_, r["amount_usd"], k))
                elif v is not None and r2(v) != D(got):
                    bad("%s %s %s: %s != %s" % (mid_, r["amount_usd"], k, got, r2(v)))
                n_checked += 1
            if r["total_usd"] is not None:
                pc = r2(exp["total_usd"] / Fr(r["amount_usd"]) * 100, 4)
                if D(r["total_pct"]) != pc:
                    bad("%s %s pct" % (mid_, r["amount_usd"]))
            elif not r["flags"]:
                bad("%s %s: blank total without a flag" % (mid_, r["amount_usd"]))
            for f in r["flags"]:
                if f not in flags:
                    bad("unknown flag " + f)
            if not r["sources"]:
                bad("%s row without sources" % mid_)
    with open(os.path.join(OUT, "data", "costs.csv"), encoding="utf-8", newline="") as fh:
        rows_csv = list(csv.DictReader(fh))
    if len(rows_csv) != len(costs["rows"]):
        bad("csv row count")
    for a, b in zip(rows_csv, costs["rows"]):
        for k in ("method_id", "amount_usd", "total_usd", "published_costs_usd"):
            if a[k] != ("" if b[k] is None else b[k]):
                bad("csv differs from json at %s %s %s" % (b["method_id"], b["amount_usd"], k))
    for m in methods.values():
        if not m["model"] and m["steps"]:
            bad("%s has steps without being a costed lawful method" % m["id"])
        for f in m["flags"]:
            if f not in flags:
                bad("unknown flag " + f)
    return n_checked, len(costs["rows"])


# ---------- 3. pages
class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.rows, self.h1 = set(), [], [], 0
        self.viewport = self.lang = False
        self.in_tbody = False
        self.cur = None
        self.tags = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(tag)
        if "id" in a:
            if a["id"] in self.ids:
                bad("duplicate id " + a["id"])
            self.ids.add(a["id"])
        if tag == "html" and a.get("lang"):
            self.lang = True
        if tag == "meta" and a.get("name") == "viewport":
            self.viewport = True
        if tag == "h1":
            self.h1 += 1
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.cur = {"src": 0, "blank": 0, "flag": 0}
        if tag == "a" and "href" in a:
            self.links.append(a["href"])
            if self.cur is not None:
                cls = a.get("class", "")
                if cls == "src" and a["href"].startswith(("https://", "http://")):
                    self.cur["src"] += 1
                if cls == "flag":
                    self.cur["flag"] += 1
        if tag == "span" and a.get("class") == "blank" and self.cur is not None:
            self.cur["blank"] += 1
        if tag in ("link", "img", "script", "iframe"):
            ref = a.get("href") or a.get("src") or ""
            if tag != "link" or ref.startswith(("http:", "https:", "//")):
                self.links.append("!external-asset:" + tag + ":" + ref)

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.cur is not None:
            self.rows.append(self.cur)
            self.cur = None


def check_pages():
    pages = {}
    for f in sorted(glob.glob(os.path.join(OUT, "*.html"))):
        text = open(f, encoding="utf-8").read()
        p = Page()
        p.feed(text)
        name = os.path.basename(f)
        pages[name] = p
        if not text.startswith("<!doctype html>"):
            bad(name + ": doctype")
        if not (p.lang and p.viewport and p.h1 == 1):
            bad(name + ": lang, viewport or single h1 missing")
        for i, r in enumerate(p.rows):
            if r["src"] < 1:
                bad("%s: table row %d has no official source link" % (name, i + 1))
            if r["blank"] and not r["flag"]:
                bad("%s: table row %d has a blank cell without a flag" % (name, i + 1))
    n_links = n_rows = 0
    for name, p in pages.items():
        n_rows += len(p.rows)
        for h in p.links:
            n_links += 1
            if h.startswith("!external-asset"):
                bad("%s: %s" % (name, h))
            elif h.startswith(("https://", "http://")):
                continue
            elif h.startswith(("mailto:", "javascript:")):
                bad("%s: link %s" % (name, h))
            else:
                path, _, frag = h.partition("#")
                target = os.path.normpath(os.path.join(OUT, path)) if path else os.path.join(OUT, name)
                if not os.path.isfile(target):
                    bad("%s: broken link %s" % (name, h))
                elif frag:
                    tname = os.path.basename(target)
                    if os.path.dirname(target) == OUT and tname in pages:
                        if frag not in pages[tname].ids:
                            bad("%s: missing anchor %s" % (name, h))
    need = {"index.html", "summary.html", "methods.html", "steps.html", "costs.html", "breakdown.html", "china-tax.html",
            "us-tax.html", "prohibited.html", "review.html", "flagged.html", "sources.html", "methodology.html"}
    if not need <= set(pages):
        bad("missing pages: %s" % sorted(need - set(pages)))
    proh = open(os.path.join(OUT, "prohibited.html"), encoding="utf-8").read()
    if "<ol" in proh:
        bad("prohibited.html must not contain step lists")
    steps = pages["steps.html"]
    for m in load("data/methods.json"):
        if (m["id"] in steps.ids) != bool(m["steps"]):
            bad("steps.html: %s" % m["id"])
        if m["model"] and "ladder-%s.html" % m["id"] not in pages:
            bad("missing ladder page for " + m["id"])
    for f in load("data/flags.json"):
        if f["id"] not in pages["flagged.html"].ids:
            bad("flag not published: " + f["id"])
    for name in glob.glob(os.path.join(OUT, "ladder-*.html")):
        if len(pages[os.path.basename(name)].rows) != 40:
            bad(os.path.basename(name) + ": expected 40 rows")
    return len(pages), n_links, n_rows


# ---------- 4. determinism
def digest():
    h = hashlib.sha256()
    for f in sorted(glob.glob(os.path.join(OUT, "*.html")) + glob.glob(os.path.join(OUT, "data", "*"))):
        h.update(os.path.basename(f).encode())
        h.update(open(f, "rb").read())
    return h.hexdigest()


def check_determinism():
    before = digest()
    subprocess.run([sys.executable, os.path.join(HERE, "build.py")], check=True, stdout=subprocess.DEVNULL)
    if digest() != before:
        bad("rebuilding changes the output: committed files are stale or the build is not deterministic")


def main():
    check_determinism()
    ev = check_evidence()
    P = check_params(ev)
    n_cells, n_rows = check_costs(P)
    n_pages, n_links, n_trs = check_pages()
    if ERR:
        print("FAILED: %d problem(s)" % len(ERR))
        for x in ERR[:60]:
            print(" -", x)
        return 1
    n_q = sum(len(s["quotes"]) for s in ev.values())
    print("OK: %d sources / %d quoted passages; %d cost rows and %d cells recomputed with exact fractions; "
          "%d pages, %d table rows each with a source link, %d links and anchors resolved; rebuild is byte-identical"
          % (len(ev), n_q, n_rows, n_cells, n_pages, n_trs, n_links))
    return 0


if __name__ == "__main__":
    sys.exit(main())
