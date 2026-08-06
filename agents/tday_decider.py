"""T-day decider — early-vs-MOC split + attention-budgeted
alerts for the effective date (c-75).

THE DECISION, stated once: the MOC benchmark is the close, so
100% MOC = zero tracking error BY DEFINITION. Trading early
buys nothing unless the expected close dislocation is ADVERSE
to the order by more than (impact cost of early + the client's
tracking-error tolerance). Our own panel says the print
usually helps the forced side (deletes close +45 bps above the
last tape; Q38) — so the default is MOC, and deviation needs a
named reason. This module produces that reason, or stays
silent.

Split priors per v2 scenario are DECLARED (not fitted — the
per-scenario dislocation history is too thin to fit); every
plan logs its prediction so Aug-2026 forward events grade
them.

ALERT PHILOSOPHY (busy-desk contract):
  - Decisions happen at 4 moments only: T-1 plan, 09:00
    confirm, 13:00 checkpoint, 13:20 final call. Everything
    else is monitoring.
  - Checkpoint output is ONE batched digest, not a stream.
  - RED interrupts exist for at most 4 trigger classes, fire on
    STATE TRANSITIONS only (never re-fire on a level), and
    respect a hard budget (default 5/day): overflow collapses
    into a single MARKET-MODE banner instead of per-name spam.
  - Thresholds come from OUR measured dislocation distribution
    (data/auction_expost.json percentiles), not intuition.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---- thresholds from the panel (recomputed if file present) ---
_DEF = {"amber_bps": 146.0, "red_bps": 281.0}   # p75 / p90


def thresholds():
    p = ROOT / "data" / "auction_expost.json"
    if not p.exists():
        return dict(_DEF)
    import numpy as np
    rows = json.loads(p.read_text())["rows"]
    pr = [abs(r["pressure_bps"]) for r in rows]
    return {"amber_bps": float(np.percentile(pr, 75)),
            "red_bps": float(np.percentile(pr, 90))}


# ---- the split decision -------------------------------------
# (early_linear, moc, t1) for the OBLIGATED-side client, by v2
# scenario. DECLARED priors; graded from Aug-2026.
V2_SPLITS = {
    "SQUEEZE-RISK":   (0.0, 1.0, 0.0),
    "OVERSUPPLIED":   (0.2, 0.8, 0.0),
    "COMMITTED":      (0.0, 1.0, 0.0),
    "PARTIAL":        (0.3, 0.7, 0.0),
    "TOLL-DEPENDENT": (0.5, 0.5, 0.0),
}

V2_RATIONALE = {
    "SQUEEZE-RISK": "wrong-way positioning: the cross likely "
        "clears IN the obligated side's favor (covering lifts a "
        "delete print / supply caps an add print) — lean fully "
        "on the close; do NOT pre-trade into your own tailwind",
    "OVERSUPPLIED": "supply exceeds demand: clean print likely "
        "but post-print crack risk (2324 pattern) — mostly MOC, "
        "small early leg, avoid holding past T",
    "COMMITTED": "inventory matches demand: the panel's median "
        "case — the print helps the forced side; MOC is the "
        "trade",
    "PARTIAL": "supply still building: moderate early leg "
        "reduces reliance on a cross whose depth is unproven",
    "TOLL-DEPENDENT": "no committed supply: the close leans on "
        "day-traders, expect a discount print ADVERSE to the "
        "obligated side — the one scenario where early trading "
        "buys real edge (if the mandate allows)",
}


def decide_split(code, side, scenario, client_flex=True):
    """Returns the plan for one name. client_flex=False forces
    MOC-only and demotes everything else to advice."""
    base = V2_SPLITS.get(scenario, (0.0, 1.0, 0.0))
    why = V2_RATIONALE.get(scenario, "unknown scenario -> "
                           "default MOC (benchmark-neutral)")
    if not client_flex:
        return {"code": code, "side": side,
                "split": (0.0, 1.0, 0.0),
                "advice_only_split": base,
                "rationale": "MANDATE IS MOC-ONLY. " + why,
                "scenario": scenario, "status": "DECLARED"}
    return {"code": code, "side": side, "split": base,
            "rationale": why, "scenario": scenario,
            "status": "DECLARED"}


# ---- the alert engine ---------------------------------------
RED_TRIGGERS = ("DISLOCATION",   # |indicative disl| >= red_bps
                "LIMIT_WATCH",   # indicative inside 1% of band
                "PACE_COLLAPSE",  # 13:00 volume < 0.5x floor
                "HALT")          # trading halt / news sentinel


class TdayAlertEngine:
    def __init__(self, red_budget=5):
        self.th = thresholds()
        self.red_budget = red_budget
        self.reds_fired = 0
        self.market_mode = False
        self.state = {}          # code -> level
        self.log = []

    def _level(self, disl_bps, at_limit, pace, halted):
        if halted or at_limit:
            return "RED"
        if disl_bps is not None and abs(disl_bps) >= \
                self.th["red_bps"]:
            return "RED"
        if pace is not None and pace < 0.5:
            return "RED"
        if (disl_bps is not None and abs(disl_bps) >=
                self.th["amber_bps"]) or \
                (pace is not None and pace < 0.8):
            return "AMBER"
        return "SILENT"

    def observe(self, code, disl_bps=None, at_limit=False,
                pace=None, halted=False):
        """Feed one observation; returns an alert dict ONLY on
        an upward state transition — else None (logged)."""
        new = self._level(disl_bps, at_limit, pace, halted)
        old = self.state.get(code, "SILENT")
        self.state[code] = new
        rank = {"SILENT": 0, "AMBER": 1, "RED": 2}
        self.log.append((code, new, disl_bps, pace))
        if rank[new] <= rank[old]:
            return None                     # no re-fire, ever
        if new == "RED":
            self.reds_fired += 1
            if self.reds_fired > self.red_budget:
                if not self.market_mode:
                    self.market_mode = True
                    return {"level": "MARKET-MODE",
                            "msg": "RED budget exhausted — "
                                   "event-wide stress; switch "
                                   "to the market banner, stop "
                                   "per-name interrupts"}
                return None
            return {"level": "RED", "code": code,
                    "msg": f"{code}: "
                    + ("HALT" if halted else
                       "at limit band" if at_limit else
                       f"disl {disl_bps:+.0f}bps" if disl_bps
                       is not None and abs(disl_bps) >=
                       self.th["red_bps"] else
                       f"pace {pace:.0%} of floor")}
        return None                          # AMBER: digest-only

    def digest(self):
        """The batched checkpoint line-set (09:00/13:00/13:20):
        one line per non-silent name, nothing else."""
        return [f"{c}: {lvl}" for c, lvl in
                sorted(self.state.items()) if lvl != "SILENT"]


def render_tday_plan(names, client_flex=True):
    """Morning one-pager: names = [(code, side, scenario)]."""
    plans = [decide_split(c, s, sc, client_flex)
             for c, s, sc in names]
    return {"plans": plans,
            "checkpoints": ["T-1 plan lock", "09:00 confirm "
                            "(gap/news only)", "13:00 pace + "
                            "drift digest", "13:20 final peel "
                            "call", "13:25-13:30 monitor-only "
                            "(RED interrupts live)"],
            "thresholds": thresholds(),
            "alert_contract": "AMBER batches to checkpoints; "
                              "RED fires on transitions, "
                              "budget 5; overflow = one "
                              "MARKET-MODE banner"}
