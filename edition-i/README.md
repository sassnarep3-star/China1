# Edition I — verified China-money dashboard

- **Live dashboard:** https://sassnarep3-star.github.io/China1/edition-i/site/index.html
- **Short redirect:** https://sassnarep3-star.github.io/China1/edition-i/
- **Session:** `arena-8344a869`; sources retrieved 2026-11-09 UTC.
- **Scope:** 23 routes, 6 categories, 40 USD amount steps per route (920 rows), 45 official/provider-primary sources, 20 flagged items, 15 repo-review findings, 21 requirements.

Pages: [overview](site/index.html), [executive summary](site/executive-summary.html), [cost ladder](site/costs.html),
[all methods](site/methods.html), [penalty breakdown](site/penalty.html), [China tax](site/tax-china.html),
[US tax & reporting](site/tax-us.html), [official sources](site/sources.html), [repo review](site/repo-review.html),
[Flagged for Review](site/flagged.html), [method & limits](site/methodology.html), [requirements](site/requirements.html).

Build and verify:

```sh
python3 edition-i/build/build.py
python3 edition-i/build/verify.py
```

No user input was required. Values not confirmed from an official page are blank and flagged. This is research, not
legal, tax or investment advice.
