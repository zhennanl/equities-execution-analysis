# Foreign Flow vs a Normal Day

Generated 2026-08-11T14:48:41 by `scripts/tw_foreign_baseline.py`.

Events used: 97 (skipped 17 without flow fields, 10 with thin baselines).

| Side | Phase | median flow/session (ADV) | x a normal day |
| --- | --- | ---: | ---: |
| ADD | 30 sessions before ann | +0.021 | +0.3x |
| ADD | announcement to effective | +0.041 | +0.6x |
| ADD | the effective day | +0.134 | +3.2x |
| ADD | 10 sessions after | -0.018 | -0.2x |
| ADD | *normal day, absolute scale* | 0.073 | 1.0x |
| DEL | 30 sessions before ann | -0.101 | -0.7x |
| DEL | announcement to effective | -0.118 | -0.9x |
| DEL | the effective day | -0.430 | -5.1x |
| DEL | 10 sessions after | -0.247 | -1.8x |
| DEL | *normal day, absolute scale* | 0.152 | 1.0x |

Phases are per-session rates, so the four rows and the baseline share one unit. The T86 netting caveat applies: gross index demand is larger than any of these numbers.
