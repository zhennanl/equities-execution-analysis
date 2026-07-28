# Deployment Notes (Streamlit Community Cloud)

The app is live at https://equities-execution-analysis.streamlit.app/ and
auto-redeploys on every push to `main` — no action needed beyond `git push`.

## What keeps the cloud app healthy

- **The Guided Demo (Page 0) and Pages 3-4 run with zero network** — demo
  data only — so the landing experience never depends on Yahoo rate limits.
  Send interviewers the link; the first page always works.
- **yfinance on shared cloud IPs gets rate-limited.** Pages 1-2 fetch on
  demand and cache 5 minutes; if a fetch fails, the app shows the friendly
  error rather than crashing. For a live interview demo of Pages 1-2,
  running locally (`streamlit run app.py`) is the reliable route.
- **Dependencies** are pinned in `requirements.txt` (no sklearn — the ML
  gate deliberately falls back to numpy ridge). Python version is set by
  the cloud default; the suite runs on 3.11+ in CI.
- **No secrets.** Nothing to configure in the cloud dashboard.
- Derived JSON stores (event/run/audit libraries) are ephemeral on the
  cloud (reset on redeploy) — by design; they're gitignored working data.

## Redeploy checklist (after a big merge)

1. CI badge green (the same offline suite the repo runs locally).
2. Open the live URL in a private window; walk Page 0 top to bottom.
3. Spot-check Page 3 cockpit + Page 4 demo quarter (offline paths).
4. Try one Page-1 fetch; if rate-limited, note it and move on — the
   in-app error message explains itself.

## Case studies with real events

`scripts/run_case_study.py` (run LOCALLY — needs network) pushes real
MSCI/S&P events through the event study and records them to the event
library, e.g.:

    python scripts/run_case_study.py SMCI US "S&P 500" 2024-03-18 --announced 2024-03-01
