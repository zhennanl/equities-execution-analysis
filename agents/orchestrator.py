"""
Orchestrator

Wraps Agents 1-8 behind a single call that populates a shared
ExecutionContext (agents/context.py) rather than app.py importing and
threading every agent's dataclass through explicit function parameters.
This is the dynamic-orchestration half of the multi-agent design write-up
in PROJECT_CONTEXT.md:

  - Conditional/dynamic invocation: some steps are skipped at runtime based
    on data actually available (e.g. Agent 6's pre-trade spread estimate is
    skipped outright -- not attempted and caught -- when there isn't enough
    daily history for a stable read), rather than every step always running
    unconditionally in a fixed sequence.
  - Graceful partial failure: each agent is wrapped independently. One
    agent failing (e.g. the earnings calendar being unavailable for an
    obscure ticker) records the failure in ctx.errors and lets every other
    agent still run, instead of the whole request hard-stopping the way
    app.py's old per-agent `except: st.stop()` pattern did.
  - New agents are additive: Agent 7 (earnings) and Agent 8 (critic) plug in
    here without touching Agents 1-6's code or app.py's rendering logic for
    the sections that already existed.

Deliberately NOT wrapping Agent 1 (market data fetch) -- app.py keeps
calling `_cached_fetch()` itself so `@st.cache_data(ttl=300)` continues to
cache only the network-bound fetch, not the whole pipeline (re-running the
simulation for a different order size or urgency on the same ticker
shouldn't be blocked by a stale cached full-pipeline result).
"""

from agents.context import ExecutionContext
from agents.agent2_market_regime import assess_regime
from agents.agent3_algo_simulation import simulate_algos
from agents.agent4_performance_comparison import compare_performance
from agents.agent13_venue_router import route_order, bar_volumes_for, DEFAULT_HALF_SPREAD_BPS
from agents.agent5_recommendation import generate_memo
from agents.agent6_pretrade_posttrade import build_pretrade_estimate, build_posttrade_tca
from agents.agent7_earnings_calendar import check_earnings_calendar
from agents.agent8_critic import review_recommendation
from agents.agent9_microstructure import assess_microstructure

# Corwin-Schultz needs >= window+2 daily bars (see agent6); skip the attempt
# entirely below that rather than calling it and catching the "unavailable" result.
MIN_DAILY_BARS_FOR_SPREAD = 22


def run_pipeline(market_data, order_pct_adv: float, urgency: str, log=None,
                 benchmark_target: str = "Arrival", ticket=None) -> ExecutionContext:
    def _log(msg):
        if log:
            log(msg)

    ctx = ExecutionContext(
        ticker_base=market_data.ticker, market=market_data.market,
        order_pct_adv=order_pct_adv, urgency=urgency, benchmark_target=benchmark_target,
    )
    ctx.market_data = market_data
    ctx.order_shares = market_data.adv_shares * (order_pct_adv / 100)
    ctx.order_ticket = ticket
    ctx.record("agent1_market_data", "ran", "supplied by caller (cached fetch)")

    # Agent 2 — regime (always; cheap, foundational for Agent 5's rules)
    try:
        ctx.regime = assess_regime(market_data)
        ctx.record("agent2_market_regime", "ran")
    except Exception as e:
        ctx.record("agent2_market_regime", "failed", str(e))

    # Agent 3 — single-day simulation (always; the core deliverable)
    try:
        ctx.sim = simulate_algos(market_data, order_pct_adv, urgency, log=log, ticket=ticket)
        ctx.record("agent3_algo_simulation", "ran")
    except Exception as e:
        ctx.record("agent3_algo_simulation", "failed", str(e))

    # Agent 4 — multi-day comparison (always; Agent 5 depends on it)
    try:
        ctx.comp = compare_performance(market_data, order_pct_adv, urgency, log=log, ticket=ticket)
        ctx.record("agent4_performance_comparison", "ran")
    except Exception as e:
        ctx.record("agent4_performance_comparison", "failed", str(e))

    # Agent 5 — recommendation memo (needs regime, sim, comp)
    if ctx.regime is not None and ctx.sim is not None and ctx.comp is not None:
        try:
            ctx.memo = generate_memo(market_data, ctx.regime, ctx.sim, ctx.comp, urgency, order_pct_adv, log=log,
                                     benchmark_target=benchmark_target)
            if ticket is not None and not ticket.is_default():
                ctx.memo.risk_flags.extend("🎫 Order ticket constraint — " + c
                                           for c in ticket.constraint_summary())
                if ctx.sim is not None and getattr(ctx.sim, "excluded", None):
                    ctx.memo.risk_flags.extend(f"🎫 Excluded from consideration — {k}: {v}"
                                               for k, v in ctx.sim.excluded.items())
            ctx.record("agent5_recommendation", "ran")
        except Exception as e:
            ctx.record("agent5_recommendation", "failed", str(e))
    else:
        ctx.record("agent5_recommendation", "skipped", "missing upstream agent output (regime/sim/comp)")

    # Agent 6a — pre-trade estimate (needs comp; runtime-conditional on daily history length)
    if ctx.comp is not None:
        n_daily = len(market_data.daily)
        if n_daily < MIN_DAILY_BARS_FOR_SPREAD:
            ctx.record("agent6_pretrade", "skipped",
                      f"daily history too short for a spread estimate ({n_daily} bars, need >= {MIN_DAILY_BARS_FOR_SPREAD})")
        else:
            try:
                ctx.pretrade = build_pretrade_estimate(market_data, ctx.comp, ctx.order_shares, order_pct_adv, urgency, ticket=ticket)
                ctx.record("agent6_pretrade", "ran")
            except Exception as e:
                ctx.record("agent6_pretrade", "failed", str(e))
    else:
        ctx.record("agent6_pretrade", "skipped", "comparison data unavailable")

    # Agent 7 — earnings calendar (always attempt; independent of every other agent)
    try:
        ctx.earnings = check_earnings_calendar(market_data.ticker, log=log)
        ctx.record("agent7_earnings_calendar", "ran")
    except Exception as e:
        ctx.record("agent7_earnings_calendar", "failed", str(e))

    # Agent 6b — post-trade TCA (needs sim, comp, and memo.primary_algo)
    if ctx.sim is not None and ctx.comp is not None and ctx.memo is not None:
        try:
            ctx.posttrade = build_posttrade_tca(market_data, ctx.sim, ctx.comp, ctx.memo.primary_algo)
            ctx.record("agent6_posttrade", "ran")
        except Exception as e:
            ctx.record("agent6_posttrade", "failed", str(e))
    else:
        ctx.record("agent6_posttrade", "skipped", "missing upstream agent output (sim/comp/memo)")

    # Agent 9 — market microstructure & order-flow toxicity (Kyle's lambda,
    # VPIN, Almgren et al. (2005) calibrated cross-check). Independent of
    # every other agent except the raw market_data/order size, so it's
    # attempted regardless of whether upstream agents succeeded -- the
    # critic (below) uses it if available but doesn't require it.
    try:
        ctx.microstructure = assess_microstructure(market_data, ctx.order_shares, urgency, log=log)
        ctx.record("agent9_microstructure", "ran")
    except Exception as e:
        ctx.record("agent9_microstructure", "failed", str(e))

    # Agent 13 — venue selection & smart-order-routing simulation (routes the
    # recommended algo's schedule across the market's venue set; needs sim +
    # memo, uses Agent 6's spread estimate when available)
    if ctx.sim is not None and ctx.memo is not None and ctx.memo.primary_algo in ctx.sim.algos:
        try:
            _hs = (ctx.pretrade.half_spread_bps
                   if ctx.pretrade is not None and ctx.pretrade.half_spread_bps
                   else DEFAULT_HALF_SPREAD_BPS)
            _sched = ctx.sim.algos[ctx.memo.primary_algo].schedule
            ctx.routing = route_order(
                _sched, bar_volumes_for(_sched, market_data.intraday),
                market_data.market,
                policy=getattr(ticket, "sor_policy", "Cost-optimized") if ticket else "Cost-optimized",
                half_spread_bps=_hs,
                allow_dark=getattr(ticket, "allow_dark", True) if ticket else True,
                excluded=getattr(ticket, "excluded_venues", None) if ticket else None)
            ctx.record("agent13_venue_router", "ran")
        except Exception as e:
            ctx.routing = None
            ctx.record("agent13_venue_router", "failed", str(e))
    else:
        ctx.routing = None
        ctx.record("agent13_venue_router", "skipped", "missing sim/memo output")

    # Agent 8 — critic (runs last; reviews whatever combination of the above is available)
    try:
        ctx.critic = review_recommendation(ctx, log=log)
        ctx.record("agent8_critic", "ran")
    except Exception as e:
        ctx.record("agent8_critic", "failed", str(e))

    _log("Orchestrator complete.")
    return ctx
