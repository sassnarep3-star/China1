# Independent site QA (handoff to integration owner)

This directory is an **independent audit tool**, not the site or a legal/tax research report. It does not modify anyone else's claimed files. The site integration owner can run it against the **built** GitHub Pages output:

```sh
python3 -m unittest discover -s qa -v
python3 qa/check_site.py docs --json  # or the actual published site's local output directory
```

The checker exits nonzero on problems. It checks static HTML table data rows for a visible HTTPS link on an allowlisted institutional host; local links and anchors; local image/script/style resources; presence of a `Flagged for Review` heading and a link to that page; missing home; and zero static table rows. Header-only rows are ignored. It is intentionally conservative: a missing source link is an issue even on a row labeled unverified, because the user's requirement is an official link **on every row**. To mark an unsupported value unverified, leave the value blank and link the relevant official rule or source of the attempted check on the review page; do not invent a value.

`official-hosts.json` contains only institutional home domains opened and identified in official pages on 2026-11-07:

| Domain | Institution | Official homepage checked |
| --- | --- | --- |
| `irs.gov` | US Internal Revenue Service | https://www.irs.gov/individuals/international-taxpayers/foreign-currency-and-currency-exchange-rates |
| `fincen.gov` | US Treasury Financial Crimes Enforcement Network | https://www.fincen.gov/ |
| `safe.gov.cn` | State Administration of Foreign Exchange | https://www.safe.gov.cn/en/ |
| `pbc.gov.cn` | People's Bank of China | https://www.pbc.gov.cn/english/130437/index.html |
| `chinatax.gov.cn` | State Taxation Administration | https://www.chinatax.gov.cn/eng/ |
| `gov.cn` | PRC central government portal | https://www.gov.cn/ |

Add other hosts **only after checking the actual institution's official site and documenting its homepage**. Host matching is an initial warning filter, not a guarantee of source authenticity, page availability, accuracy, relevance, or evidence that a source supports a claim. This checker does **not** follow outbound links (the shell has restricted outbound access), audit JS-rendered/JSON/Markdown data, verify tax law, calculate actual costs, identify personal eligibility, or test a GitHub Pages deployment. The integration owner must separately inspect each row, open each citation from an official source, verify every number and claim, confirm that missing data is blank and flagged, check client-rendered output manually, and confirm the Pages deployment. A passing checker is never a certification of line-by-line factual verification.
