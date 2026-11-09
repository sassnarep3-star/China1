# Verification log — Edition I
Session `arena-8344a869` · 2026-11-09 UTC.
The deterministic verifier is [`build/verify.py`](../build/verify.py). It recomputes the cost ladder from [`build/model.py`](../build/model.py) rather than trusting HTML, checks the official-source registry and allowlist, checks that every generated table row has a source link, checks blank-not-zero and flagged-item discipline, resolves internal links and anchors, proves byte-identical rebuilds, and performs local HTTP 200 checks.

| Check | Status at build time | Evidence |
|---|---|---|
| Deterministic rebuild | pending local run | [build/verify.py](../build/verify.py), [site/sources.html](../site/sources.html) |
| Arithmetic recomputation of 920 ladder rows and 40 exposure rows | pending local run | [build/verify.py](../build/verify.py), [site/sources.html](../site/sources.html) |
| Official-source registry / allowlist / citation-row gate | pending local run | [build/verify.py](../build/verify.py), [site/sources.html](../site/sources.html) |
| Blank-not-zero, flagged-item and prohibited-route gates | pending local run | [build/verify.py](../build/verify.py), [site/sources.html](../site/sources.html) |
| Internal links, fragments and orphan-page graph | pending local run | [build/verify.py](../build/verify.py), [site/sources.html](../site/sources.html) |
| Local HTTP 200 for every HTML, CSS, CSV and JSON page | pending local run | [build/verify.py](../build/verify.py), [site/sources.html](../site/sources.html) |
| Inherited checkers | pending local run | [build/verify.py](../build/verify.py), [site/sources.html](../site/sources.html) |
| GitHub Actions check run | pending PR | [build/verify.py](../build/verify.py), [site/sources.html](../site/sources.html) |
| GitHub Pages deployment | pending merge | [build/verify.py](../build/verify.py), [site/sources.html](../site/sources.html) |

External links are the exact official URLs in [`research/retrieval-log.md`](retrieval-log.md); they were retrieved during research and are presented for manual review. Internal checkers prove deterministic generation and link resolution, not continuous external retrievability or factual correctness of a personal eligibility determination.
