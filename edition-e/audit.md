# Edition E inherited-edition audit

Prior editions are preserved. This audit adjudicates selected load-bearing claims against the retrieved evidence in `data/sources.json`.

| ID | Severity | Subject | Finding | Adjudication |
|---|---|---|---|---|
| A01 | medium | Root summary / data/costs.json | 0.42% is full bid/ask gap divided by ask, described as round-trip loss. | Different metric, not a universal conversion cost. Edition E labels a one-way midpoint proxy. |
| A02 | high | data/costs.json K9 / scripts/data_costs.py | Blanket 20% CNY deposit coupon / nets 80% statement conflicts with savings-deposit interest exemption from 2008-10-09. | Overbroad. Personal tax remains blank. |
| A03 | high | Older crypto authority | 2021 No.237 is cited; PBOC 2026 No.42 expressly repeals it. | Outdated authority; current notice cited. |
| A04 | high | Emigrant staging | 50%/25%/25% schedule presented as current; 2014 circular allows lump sum/batches within approval; full current section 6.4 not isolated. | Not confirmed current; staging blank. |
| A05 | medium | Older no-tariff statements | Current BOC personal and SC China provider tariffs were retrieved. | Historical limitation superseded for Edition E; provider prices are not government rates. |
| A06 | high | Published Edition D receiving-bank assumption | USD 15 Chase assumption completes totals although user supplied no receiving bank. | Labelled assumption is not verified personal value; Edition E leaves receiving/all-in blank. |
| A07 | medium | Edition D BOC tariff vintage | Edition D uses 2014 personal e-banking tariff and corporate full-arrival announcement; current personal tariff effective 2025-11-11 retrieved. | Edition E uses current personal schedule; optional surcharge separate. |
| A08 | medium | Edition D board timezone | Edition D labels board stamp Beijing time; retrieved board did not establish timezone for this session. | Preserve timestamp; flag mismatch. |
| A09 | low | IRS Publication 525 | USD 200 tip verified by official search excerpt; targeted full body not isolated. | Disclosed; no personal gain computed. |
| A10 | process | Concurrent edition collision | Another session published edition-d during research; untracked-file rebase conflict prevented overwrite. | Relocated isolated outputs to edition-e; merged main; preserved Edition D. |

Machine-readable version: `data/audit.json`. Site version: `site/audit.html`.
