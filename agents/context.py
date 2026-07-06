"""
Shared Execution Context ("blackboard")

Replaces explicit dataclass threading (agent4 imports agent3's types, agent5
imports agent1-4's types, app.py imports and threads all of them by name)
with a single mutable object every agent reads from and writes to. This is
the loose-coupling half of the multi-agent design write-up in
PROJECT_CONTEXT.md: adding a new specialist agent means adding one field
here and one call in orchestrator.py, not touching every downstream
function's parameter list or import block.

Each field is Optional and defaults to None/empty so partial pipelines are a
first-class, inspectable state (e.g. if Agent 6's spread estimator fails,
ctx.pretrade is None but ctx.errors["pretrade"] explains why, and everything
computed before/after that point is still usable) -- this is what
`orchestrator.run_pipeline()` relies on to keep going after a non-fatal
agent failure instead of hard-stopping the whole request, unlike the
try/except-then-st.stop() pattern app.py used per-agent before this.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class ExecutionContext:
    # -- Request parameters (set at construction) ----------------------------
    ticker_base: str = ""
    market: str = ""
    order_pct_adv: float = 0.0
    urgency: str = "Medium"
    benchmark_target: str = "Arrival"   # "Arrival" | "VWAP" | "Close" | "Open" -- client's stated TCA objective

    # -- Derived once market_data is available --------------------------------
    order_shares: float = 0.0

    # -- Agent outputs (populated incrementally by the orchestrator) --------
    market_data: Optional[Any] = None      # agent1: MarketData
    regime: Optional[Any] = None           # agent2: RegimeAssessment
    sim: Optional[Any] = None              # agent3: SimulationResult
    comp: Optional[Any] = None             # agent4: PerformanceComparison
    memo: Optional[Any] = None             # agent5: RecommendationMemo
    pretrade: Optional[Any] = None         # agent6: PreTradeEstimate
    posttrade: Optional[Any] = None        # agent6: PostTradeTCA
    earnings: Optional[Any] = None         # agent7: EarningsFlag
    critic: Optional[Any] = None           # agent8: CriticReview
    microstructure: Optional[Any] = None   # agent9: MicrostructureAssessment

    # -- Orchestration audit trail --------------------------------------------
    trace: List[Dict[str, str]] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)

    def record(self, agent_name: str, status: str, detail: str = "") -> None:
        """status: 'ran' | 'skipped' | 'failed'"""
        self.trace.append({"agent": agent_name, "status": status, "detail": detail})
        if status == "failed":
            self.errors[agent_name] = detail

    def succeeded(self, agent_name: str) -> bool:
        return any(t["agent"] == agent_name and t["status"] == "ran" for t in self.trace)
