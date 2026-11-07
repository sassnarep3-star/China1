# China Money

An evidence-led static research dashboard about lawful conversion and transfer of money from mainland China to the United States. Start at [the site](https://sassnarep3-star.github.io/China1/) or open `index.html` locally. This is educational research, not individualized legal, tax, or investment advice. The source, balance, tax history and account status are unknown; conclusions are conditional and unresolved items are on the Flagged for Review page.

## Build and verify

No dependencies or credentials are required:

```sh
python3 assets/build.py
python3 assets/check.py
```

The build generates the five checked-in static HTML pages. The checker validates deterministic generation, local linked files, and an official HTTPS citation on every data row; it does **not** prove legal interpretation or live availability of external sources. Pages publishes from `main` using the repository's existing GitHub Pages configuration. See [COORDINATION.md](COORDINATION.md) for the task log and verification scope.
