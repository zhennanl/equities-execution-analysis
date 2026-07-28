"""Universe builder & validator — the generic fix for the FTSE-backtest
failure mode (session 6y).

Three real reviews taught the same lesson three ways: every false
prediction traced to the UNIVERSE FILE, not the rules — a mis-counted
membership (49 where the index holds 50), a missing boundary-zone name
compressing the rank ladder, an ineligible listing (TPEx-listed MPI in a
TWSE-only index). The rules engine was innocent each time; the input
wasn't.

So the fix is an input pre-flight, same design language as the client-file
normalizer: `validate_universe` checks the universe against a per-market
`UniverseSpec` and returns an explicit ISSUES list — it never silently
fixes anything. Run it before every screen, every backtest, every
pre-registered prediction; a backtest whose universe fails validation is
reporting on its own reconstruction, not the engine.

Checks:
    membership count vs index size        (caught the 49-member bug)
    listing-venue eligibility             (caught TPEx-listed MPI)
    duplicate tickers
    float / cap sanity (missing, non-positive, float>1)
    BOUNDARY DENSITY — are there enough names per rank around the
        add/delete boundaries for ranks to mean anything? A thin ladder
        was why round 1 promoted five spurious adds.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

# listing-venue eligibility per market: which ticker suffixes belong to
# the PRIMARY exchange an index of that market may draw from. The MPI
# lesson: 6223.TWO (TPEx) is not eligible for a TWSE-only index.
LISTING_ELIGIBILITY: dict[str, tuple] = {
    "Taiwan (TWSE)": (".TW",),          # NOT .TWO (TPEx)
    "Japan (TSE)": (".T",),
    "Korea (KRX)": (".KS",),            # NOT .KQ (KOSDAQ) for KOSPI indices
    "Hong Kong (HKEX)": (".HK",),
    "China-A Shanghai": (".SS",),
    "China-A Shenzhen": (".SZ",),
    "Singapore (SGX)": (".SI",),
    "India (NSE)": (".NS",),
    "Australia (ASX)": (".AX",),
    "US": ("",),                        # no suffix
}


@dataclass
class UniverseSpec:
    """What a valid universe for one index looks like."""
    market: str
    index_size: int = None              # None = coverage-based (MSCI-style)
    add_rank: int = None                # rank-based boundaries (FTSE-style)
    delete_rank: int = None
    allowed_suffixes: tuple = None      # default: LISTING_ELIGIBILITY[market]
    min_names_per_boundary_decile: int = 5
    require_adv: bool = True

    def suffixes(self):
        if self.allowed_suffixes is not None:
            return self.allowed_suffixes
        return LISTING_ELIGIBILITY.get(self.market, None)


def _suffix_ok(ticker: str, suffixes) -> bool:
    t = str(ticker).split()[0]          # allow "2330.TW TSMC" style labels
    if suffixes is None:
        return True
    if suffixes == ("",):
        return "." not in t
    return any(t.endswith(sfx) for sfx in suffixes)


def validate_universe(universe: pd.DataFrame, members: set,
                      spec: UniverseSpec,
                      ignore_prefix: str = "TAIL") -> dict:
    """Pre-flight the universe. Returns {"ok", "issues", "warnings"} —
    issues are disqualifying for a graded backtest; warnings degrade
    confidence. Nothing is silently fixed."""
    issues, warnings = [], []
    u = universe.copy()
    named = u[~u["ticker"].astype(str).str.startswith(ignore_prefix)]

    # 1) membership count vs index size (the 49-member bug)
    if spec.index_size is not None:
        n_mem = len(set(u["ticker"]) & set(members))
        if n_mem != spec.index_size:
            issues.append(f"membership count {n_mem} != index size "
                          f"{spec.index_size} — fix before grading anything "
                          "(off-by-one memberships create phantom adds/deletes)")

    # 2) listing-venue eligibility (the MPI bug)
    sfx = spec.suffixes()
    if sfx is not None:
        bad = [t for t in named["ticker"] if not _suffix_ok(t, sfx)]
        for t in bad:
            where = "MEMBER" if t in members else "candidate"
            issues.append(f"{t} ({where}): listing venue not eligible for "
                          f"{spec.market} index (allowed: {sfx})")

    # 3) duplicates
    dup = u["ticker"][u["ticker"].duplicated()].tolist()
    if dup:
        issues.append(f"duplicate tickers: {dup}")

    # 4) data sanity
    if (u["full_mktcap_usd"] <= 0).any():
        issues.append("non-positive market caps present")
    if "free_float_frac" in u.columns:
        bad_f = u[(u["free_float_frac"] <= 0) | (u["free_float_frac"] > 1)]
        if len(bad_f):
            issues.append(f"{len(bad_f)} rows with float outside (0, 1]")
    if spec.require_adv and ("adv_usd" not in u.columns
                             or u["adv_usd"].isna().any()):
        warnings.append("ADV missing for some rows — liquidity screens and "
                        "flow estimates will be unreliable")

    # 5) boundary density (the thin-ladder bug): enough names per rank
    #    around each boundary for ranks to be meaningful?
    if spec.add_rank or spec.delete_rank:
        su = u.sort_values("full_mktcap_usd",
                           ascending=False).reset_index(drop=True)
        for nm, rk in (("add", spec.add_rank), ("delete", spec.delete_rank)):
            if not rk:
                continue
            lo, hi = max(0, rk - 6), min(len(su), rk + 5)
            zone = su.iloc[lo:hi]
            if len(zone) < spec.min_names_per_boundary_decile:
                issues.append(f"{nm}-boundary (rank {rk}): only {len(zone)} "
                              "names in the +/-5 rank zone — ladder too thin, "
                              "ranks unreliable")
            else:
                caps = zone["full_mktcap_usd"].to_numpy(dtype=float)
                spread = float(caps.max() / max(caps.min(), 1.0))
                if spread > 3.0:
                    warnings.append(f"{nm}-boundary (rank {rk}): cap ratio "
                                    f"{spread:.1f}x across +/-5 ranks — gaps "
                                    "in the ladder; boundary names may be "
                                    "mis-ranked")
    return {"ok": not issues, "issues": issues, "warnings": warnings,
            "note": "A graded backtest on a universe with ISSUES reports on "
                    "its own reconstruction, not on the engine."}
