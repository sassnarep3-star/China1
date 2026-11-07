# CNY → USD: every channel, its legal basis, its cost and its penalty exposure

Research dossier for a US citizen holding renminbi in a mainland Chinese bank account.

**Live site:** <https://sassnarep3-star.github.io/China1/>

The question this repository answers is what it actually costs to turn onshore renminbi into US
dollars, through every channel that exists, and what the penalty is if the channel chosen is not
lawful. Every figure on the site is cited to an official source with an article number. Where a
value could not be confirmed against an official source it is left blank and published on the
[Flagged for Review](https://sassnarep3-star.github.io/China1/flagged.html) page rather than
estimated.

## The headline finding

**China levies no tax on the act of converting CNY into USD.** No instrument reviewed — the
Individual Income Tax Law, the Enterprise Income Tax Law, the Regulation on Foreign Exchange
Administration, the Measures for the Administration of Individual Foreign Exchange or the
Detailed Rules — imposes a tax, levy or conversion charge on the exchange itself.

Chinese tax attaches to the event that created the money, and is owed whether or not the money
ever leaves China. What the conversion attracts instead is **foreign exchange control**, which is
documentary rather than fiscal, plus a commercial bank spread, plus penalty exposure only if the
route chosen is unlawful.

A second finding follows from the first. The USD 50,000 per person per year limit is routinely
described as the ceiling on all money leaving China. Art.9 of the Measures applies annual
total-amount management to only two things: individual FX settlement, and FX purchase by a
**domestic individual**. Art.37(2) defines a domestic individual as a Chinese citizen holding a
resident identity card, and an overseas individual as a foreign citizen presenting a passport. A
US citizen is therefore an overseas individual, and Art.13 lets an overseas individual convert
legitimate current-account renminbi income earned in China **with no stated annual ceiling**,
against identity documents and supporting evidence including tax vouchers.

## What is in the repository

| Path | Contents |
| --- | --- |
| `data/sources.json` | 39 entries. Issuing body, document number, date, URL on the issuing body's own domain, and the specific provisions relied on. |
| `data/routes.json` | 33 identified channels across 6 categories, each with legal basis, limit, tax cost, documentation, pros, cons, feasibility and risk. |
| `data/tax.json` | Chinese rates, US rates and treaty provisions, cited by article. |
| `data/penalties.json` | Six cost layers, the statutory penalty scales, and 23 enforcement cases SAFE published itself. |
| `data/flags.json` | 19 unresolved items: values left blank, conflicts between official sources, and gaps in the scheme. |
| `data/repo-review.json` | Repository audit, irregularities found and how each was resolved, and the verification standard. |
| `data/summary.json` | Executive summary narrative and dashboard figures. |
| `build/build.py` | Static site generator. Reads `data/*.json`, writes 17 pages into `docs/`. Standard library only. |
| `build/linkcheck.py` | Validation gate. Fails on any unresolved citation, broken link, orphan page, unsourced value, or blank that is not flagged. |
| `docs/` | The generated site. This is the GitHub Pages source directory. |
| `COORDINATION.md` | Shared task board, source register summary, irregularity log and handoff record. |

## Building

```bash
python3 build/build.py       # regenerate docs/ from data/
python3 build/linkcheck.py   # must pass before publishing
```

Output is deterministic: rebuilding from unchanged data produces byte-identical files.
`python3 build/linkcheck.py --rewrite-check` records the current digests to
`data/.build-digests.json` so the next run can prove reproducibility.

No page under `docs/` is hand-edited. Change the data, rebuild.

## The verification standard

1. A numeric limit, rate, threshold or fine appears in a table only where it was read in a source
   listed in `data/sources.json`, cited by article number.
2. Where a value could not be confirmed against an official source, the cell is blank and the item
   appears on the Flagged for Review page with an explanation and a route to resolution.
3. No value anywhere on the site is inferred, estimated, interpolated or carried over from a
   secondary source.
4. Derived figures are labelled as computed and show their inputs. The fine-as-a-percentage column
   is populated only where both official figures are in the same currency, so no exchange rate has
   been assumed. `linkcheck.py` recomputes every such percentage independently and fails on a
   mismatch.
5. Official means a government department, regulator, central bank, tax authority, national
   legislature gazette or judicial body publishing its own instrument. Law firm notes, accounting
   firm alerts, tax press, bank marketing pages and aggregators are not accepted. Where one had to
   be used because the primary text could not be located, the entry is marked not official and
   flagged.
6. `linkcheck.py` runs before publication and fails the build on any unresolved citation, broken
   internal link, orphan page, or unflagged blank.

## Scope of the pages

- [Overview](https://sassnarep3-star.github.io/China1/) — dashboard and headline findings
- [Executive summary](https://sassnarep3-star.github.io/China1/executive-summary.html) — ten findings, in the order they change the decision
- [All 33 routes](https://sassnarep3-star.github.io/China1/routes.html) — master comparison table
- [Individual](https://sassnarep3-star.github.io/China1/individual-channels.html) · [Corporate](https://sassnarep3-star.github.io/China1/corporate-channels.html) · [Trade](https://sassnarep3-star.github.io/China1/trade-channels.html) · [Asset](https://sassnarep3-star.github.io/China1/asset-channels.html) — the lawful channels, by category
- [Rejected](https://sassnarep3-star.github.io/China1/assessed-and-rejected.html) — lawful schemes that do not deliver USD
- [Prohibited](https://sassnarep3-star.github.io/China1/prohibited.html) — documented for avoidance, with published fines
- [China tax](https://sassnarep3-star.github.io/China1/tax-china.html) · [US tax](https://sassnarep3-star.github.io/China1/tax-us.html) · [Treaty](https://sassnarep3-star.github.io/China1/tax-treaty.html)
- [Penalty breakdown](https://sassnarep3-star.github.io/China1/penalty.html) — six cost layers and 23 published cases
- [Flagged for review](https://sassnarep3-star.github.io/China1/flagged.html) — 19 unresolved items
- [Sources](https://sassnarep3-star.github.io/China1/sources.html) — the full register
- [Repo review](https://sassnarep3-star.github.io/China1/repo-review.html) · [Methodology](https://sassnarep3-star.github.io/China1/methodology.html)

## Not advice

This is research, published with its sources. It is not legal, tax or investment advice and creates
no professional relationship. Chinese foreign exchange practice varies by branch and by officer,
several official instruments conflict with each other as recorded on the Flagged for Review page,
and both the Chinese and the US positions depend on facts about the origin of the funds that are
not known here.
