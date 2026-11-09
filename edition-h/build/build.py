#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Edition H build entry point.

Usage: python3 edition-h/build/build.py
Writes edition-h/site/*.html and a JSON export of the whole dataset.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "data"))

import sitegen                                    # noqa: E402
from sitegen import write, METHODS, COMPUTED, BLANK, PROHIB, METHOD, SOURCES  # noqa: E402
import pages1, pages2, pages3, pages4             # noqa: E402
from costs import AMOUNTS, compute, FX_MARGIN_PCT, FX_ROUND_TRIP_PCT  # noqa: E402


def main():
    n = 0
    write("index.html", pages1.p_index()); n += 1
    write("answer.html", pages1.p_answer()); n += 1
    write("costs.html", pages2.p_costs()); n += 1

    for m in METHODS:
        write("method-{}.html".format(m["id"]), pages3.p_method(m)); n += 1
        if m["id"] in {x["id"] for x in COMPUTED}:
            write("cost-{}.html".format(m["id"]), pages2.p_method_cost(m)); n += 1

    write("methods.html", pages3.p_methods()); n += 1
    write("penalty.html", pages3.p_penalty()); n += 1
    write("tax.html", pages3.p_tax()); n += 1
    write("reporting.html", pages3.p_reporting()); n += 1
    write("steps.html", pages3.p_steps()); n += 1
    write("sources.html", pages4.p_sources()); n += 1
    write("flagged.html", pages4.p_flagged()); n += 1
    write("repo-review.html", pages4.p_repo_review()); n += 1
    write("methodology.html", pages4.p_methodology()); n += 1
    write(".nojekyll", "")

    export = {
        "edition": "H",
        "as_of": "2026-11-09",
        "fx": {"buy": str(sitegen.BUY_SPOT), "sell": str(sitegen.SELL_SPOT),
               "mid": str(round(float(sitegen.MID), 4)),
               "one_way_pct": round(float(FX_MARGIN_PCT), 4),
               "round_trip_pct": round(float(FX_ROUND_TRIP_PCT), 4)},
        "counts": {"methods": len(METHODS), "priced": len(COMPUTED),
                   "unpublished": len(BLANK), "prohibited": len(PROHIB),
                   "sources": len(SOURCES), "pages": n},
        "costs": {m["id"]: [{"amount": a, "total": None if compute(m, a)["total"] is None
                             else str(compute(m, a)["total"])} for a in AMOUNTS]
                  for m in COMPUTED},
        "sources": [{"id": s["id"], "grade": s["grade"], "url": s["url"],
                     "title": s["title"], "retrieved": s["retrieved"]} for s in SOURCES],
    }
    write("data.json", json.dumps(export, ensure_ascii=False, indent=1))

    lead = {a: compute(METHOD["A01"], a) for a in AMOUNTS}
    print("edition-h: {} pages, {} routes, {} priced, {} unpublished, {} prohibited, {} sources"
          .format(n, len(METHODS), len(COMPUTED), len(BLANK), len(PROHIB), len(SOURCES)))
    print("  one-way margin {:.4f}%  round-trip {:.4f}%".format(FX_MARGIN_PCT, FX_ROUND_TRIP_PCT))
    for a in (10_000, 100_000, 400_000):
        print("  ${:,}: total ${:,.2f} ({:.3f}%)".format(
            a, float(lead[a]["total"]), 100 * float(lead[a]["total"]) / a))


if __name__ == "__main__":
    main()
