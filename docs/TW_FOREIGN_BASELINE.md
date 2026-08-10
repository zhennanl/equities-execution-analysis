# Foreign Flow vs a Normal Day

Generated 2026-08-11T05:18:56 by `scripts/tw_foreign_baseline.py`.

Events used: 97 (skipped 17 without flow fields, 10 with thin baselines).

| Side | Phase | median flow/session (ADV) | x a normal day |
| --- | --- | ---: | ---: |
| ADD | 20 sessions before ann | +0.020 | +0.3x |
| ADD | announcement to effective | +0.041 | +0.5x |
| ADD | the effective day | +0.134 | +3.3x |
| ADD | 10 sessions after | -0.018 | -0.2x |
| ADD | *normal day, absolute scale* | 0.080 | 1.0x |
| DEL | 20 sessions before ann | -0.106 | -0.6x |
| DEL | announcement to effective | -0.118 | -0.8x |
| DEL | the effective day | -0.430 | -4.7x |
| DEL | 10 sessions after | -0.247 | -1.8x |
| DEL | *normal day, absolute scale* | 0.163 | 1.0x |

Phases are per-session rates, so the four rows and the baseline share one unit. The T86 netting caveat applies: gross index demand is larger than any of these numbers.
