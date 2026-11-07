# China Money

Official-source research dashboard on lawful mainland-China CNY → USD transfers for a US citizen.

**Live site:** https://sassnarep3-star.github.io/China1/

## Contents
- Executive summary and conditional route recommendation
- 18 routes, service variants and excluded workarounds, with pros/cons
- Cost/tax components with unknown personal values left blank
- US reporting requirements and published evidence limitations
- Official-source registry and verification method

No private financial records, credentials, live exchange-rate guesses or personal tax determinations are stored. Provider guidance is not legislation; editorial comparisons are labeled. Review `docs/review.html` before acting.

## Build and checks
```sh
python scripts/build.py
python scripts/verify.py
python -m http.server 8000 --bind 0.0.0.0 --directory docs
```
No dependencies or external fonts/scripts. Generated HTML supports navigation without JavaScript; JavaScript only filters the transfer table. Edit research records in `scripts/build.py`, regenerate and run verification. Pages serves `main:/`; the supplemental site is under `/docs/`. See COORDINATION.md for deployment and PR records.

## Preserved earlier dashboard

The concurrent session’s original dashboard remains at the repository root, with its pages and assets preserved. The expanded research dashboard is at https://sassnarep3-star.github.io/China1/docs/.
