# Architecture Diagrams — Execution Simulator & Index Rebalancing Tool

*2026-07-08. Single source of truth for the platform's flow diagrams.
Written in Mermaid so they are text, versioned with the code, and render
automatically on GitHub / VS Code / mermaid.live — when the design changes,
edit the block here (each diagram carries a node→module map telling you what
to touch), commit, done. No image files to regenerate.*

**How to update:** each node label carries the module/agent it represents.
Add an agent → add one node + one arrow. Rename a section in `app.py` → rename
the matching node. Keep labels in double quotes; use `<br/>` for line breaks.
Preview at https://mermaid.live or in the GitHub file view.

**Standalone copies:** `docs/diagrams/D1–D4.mermaid` are extracted previews
for viewers that render `.mermaid` files directly. THIS file is canonical —
if you edit a diagram here, re-extract the block to its `.mermaid` twin
(copy-paste the block body) or delete the twins if they drift.

---

## D1 — Page 1: Execution Algorithm Simulator (order lifecycle)

Node → module map: Ticket/compliance = `agents/order_ticket.py` (+ I-9 checks
in app.py) · Data = `agent1_market_data` · Regime = `agent2` · Pre-trade =
`agent6.build_pretrade_estimate` (+ `explicit_costs`, Almgren-2005 cross-check)
· Earnings = `agent7` · Microstructure = `agent9` · Venue/SOR = `agent13` ·
Simulator = `agent3` · Comparison = `agent4` · Recommendation = `agent5` ·
Critic = `agent8` · A/B = `agent10` · Cost model = `cost_model`/`cost_panel` ·
Post-trade = `agent6.build_posttrade_tca` (incl. `build_is_attribution`, I-5)
· Research analytics = `microstructure_analytics`/`asian_markets`/
`client_analytics` · Live = `agent11` + `agent3.simulate_with_interventions`.
Orchestration/graceful degradation = `agents/orchestrator.py` (ctx.trace).

```mermaid
flowchart TD
    T["🎫 Order Ticket<br/>side · size %ADV · urgency · limit ·<br/>window · participation cap · locate<br/>(order_ticket.py, FIX-tagged)"] --> C{"Pre-trade compliance<br/>restricted list · fat-finger ·<br/>short-locate (I-9)"}
    C -- "BLOCK (with reason)" --> X["❌ Run refused"]
    C -- pass --> A1["Agent 1 — Market Data<br/>yfinance intraday+daily, cached"]

    subgraph S1["Stage 1 — Pre-Trade Analytics (orchestrator: skip ≠ fail, all recorded in ctx.trace)"]
        A2["Agent 2 — Market Regime<br/>vol · volume shape · variance-ratio trend"]
        A6a["Agent 6 — Pre-Trade Estimate<br/>cost/impact + spread blend CS·AR ·<br/>capacity · explicit costs · Almgren-2005 cross-check"]
        A7["Agent 7 — Earnings Calendar<br/>overnight-gap event risk"]
        A9["Agent 9 — Microstructure<br/>Kyle's λ · VPIN (BVC)"]
    end
    A1 --> S1

    subgraph S2["Stage 2 — Strategy & Venue"]
        A5["Agent 5 — Rule-based<br/>Recommendation memo"]
        A8["Agent 8 — Critic<br/>flags disagreements —<br/>NEVER silently overrides"]
        A13["Agent 13 — Venue Router<br/>stylized SOR + venue TCA"]
    end
    S1 --> S2

    A3["Agent 3 — Algo Simulator<br/>VWAP · TWAP · POV · IS(AC) · MOC ·<br/>MOO · LIQ · STEALTH<br/>ticket constraints bind fills"]
    S2 --> A3
    A3 --> A4["Agent 4 — Comparison<br/>cross-day · size grid · AC frontier"]
    A4 --> A10["Agent 10 — Hypothesis Testing<br/>paired A/B backtest"]
    A10 --> CM["Cost Model — TCA Regression<br/>OLS + HC1/HAC · diagnostics ·<br/>A/B-with-controls"]
    CM --> PT["Post-Trade TCA (Agent 6)<br/>multi-benchmark · reversion · perm/temp ·<br/>🆕 IS attribution waterfall (I-5) ·<br/>🆕 parent/child order detail (I-8)"]
    PT --> MA["Microstructure & Client Analytics<br/>EDGE · Amihud · seasonality ·<br/>price limits · client one-pager"]
    MA --> LV["🔴 Live Session (Agent 11)<br/>replay + alerts (I-4) · interventions ·<br/>re-recommendation"]
    A8 -. "findings surface beside every stage" .-> PT
```

## D2 — Page 2: Index Rebalancing Analysis (event → strategy → trader pack)

Node → module map: Calendar/feeds = `agent12_index_calendar` · Event study +
insights = `rebalancing_event_study` · Strategist = `agent14_rebalance_
strategist` · Verdict/card/playbook/basket/library/crowding/expected-move =
`trader_view` · UI wiring = `views/page2_rebalancing.py` (B8 refactor 2026-07-08; app.py is
now a thin dispatcher — Page 1 = `views/page1_simulator.py`, Page 3 =
`views/page3_program.py`, shared helpers = `views/common.py`).

```mermaid
flowchart TD
    A12["📅 Agent 12 — Calendar Monitor<br/>MSCI feed · FTSE releases · S&P DJI ·<br/>review calendar + JSON cache"] -- "⤵️ Use selected event<br/>(prefills ticker/market/dates/side)" --> IN["Inputs<br/>index proxy · market · effective date T ·<br/>±window · ticker"]
    OPT["Optional inputs<br/>objective · announcement date ·<br/>weight Δ% · tracked AUM ·<br/>float mcap · short-interest Δ"] --> IN
    IN --> ES["Event Study (run_event_study)<br/>market model α,β on T−70..T−11 ·<br/>CAR · abnormal volume · indexed price"]

    ES --> V["🎯 Verdict banner (F1)<br/>side·size·strategy·cost·tracking ·<br/>auction RAG 🟢🟡🔴"]
    ES --> LIB[("Event Library (F5)<br/>data/event_library.json<br/>runup · reversal · drift · η · side")]

    ES --> INS["Execution-Cost Insights<br/>auction concentration · reversal class ·<br/>drift decomposition · flow-to-trade ·<br/>η calibration · 🆕 crowding score ·<br/>🆕 expected-move bands"]
    LIB -. "medians (n≥3) → thresholds & η band" .-> INS
    INS --> REC{"Objective?"}
    REC -- "Index Tracker" --> MOC["MOC — trade the print"]
    REC -- "Cost-Minimizing" --> CMIN["STEALTH / LIQ / IS<br/>by reversal & drift rules"]

    ES --> A14["Agent 14 — Strategy Simulator<br/>S1 Tracker · S2 Pre-position ·<br/>S3 Post-effective · S4 Announcement<br/>cost-vs-tracking frontier"]
    A14 --> TP["🧾 Trader Pack (F2/F3)<br/>trade card .txt · schedules .csv ·<br/>conditional playbook (triggers)"]
    LIB -. "thresholds" .-> TP

    BK["📦 Basket mode (F4)<br/>program CSV → per-name studies →<br/>severity-ranked exception blotter"] --> ES
```

## D3 — The trader's event timeline (how the tools are used around T)

```mermaid
flowchart LR
    P1["T−10…T−5<br/>Agent 12 refresh ·<br/>seed library with<br/>past events"] --> P2["T−5<br/>run study · flow sizing ·<br/>read verdict + crowding ·<br/>if RED plan pre-position"]
    P2 --> P3["T−4<br/>basket mode on full program ·<br/>circulate blotter ·<br/>agree playbook triggers"]
    P3 --> P4["T−1<br/>re-run · trigger 3 check ·<br/>download final cards +<br/>schedules"]
    P4 --> P5["T-day<br/>execute playbook ·<br/>auction bucket MOC ·<br/>card is the reference"]
    P5 --> P6["T+1…T+m<br/>work post bucket<br/>per reversal trigger"]
    P6 --> P7["T+5<br/>re-run study →<br/>outcome into library"]
    P7 -. "priors tighten next cycle" .-> P1
```

## D4 — Learning loops (what accumulates, what it feeds)

Run library on Page 1 is proposed (assessment P-C), shown dashed.

```mermaid
flowchart TD
    subgraph P2L["Page 2 — shipped"]
        R1["Every completed<br/>event study"] --> EL[("event_library.json<br/>runup · reversal · drift ·<br/>implied η · Add/Delete")]
        EL --> O1["Playbook thresholds<br/>(source + n displayed)"]
        EL --> O2["Expected-move η band"]
        EL --> O3["'This event vs library'<br/>context line"]
    end
    subgraph P1L["Page 1 — proposed (assessment P-C)"]
        R2["Every pipeline run"] -.-> RL[("run library<br/>conditions · algo ·<br/>predicted vs realized")]
        RL -.-> O4["Cost-model refits"]
        RL -.-> O5["Algo-wheel league table (I-7)"]
        RL -.-> O6["Persistent percentiles"]
    end
```
