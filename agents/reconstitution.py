"""Rulebook-based index reconstitution predictor — MSCI GIMI and FTSE
rank-buffer approximations.

What this is: a screening engine that applies the PUBLIC structure of each
provider's methodology to a candidate universe and predicts adds/deletes
with reasons and a passive-flow estimate — the desk's "who's in scope this
review" list, generated weeks before the announcement.

What this is NOT: a replica of the provider's process. Honest omissions,
disclosed in every output: country-level minimum size interplay with the
global reference, FIF granularity (foreign room, strategic holdings detail),
multiple listing lines, corporate-event windows, provider discretion, and
exact interim cutoff dates. The parameters encode the published anchors —
MSCI: Global Minimum Size Reference (GMSR) at 85% cumulative free-float
coverage of the sorted universe, Global Minimum Size Range 0.5x-1.15x GMSR
(GIMI methodology); higher size hurdle for QIR additions vs SAIR
(configurable multiple — verify current book). FTSE 100-style: add at rank
<= 90, delete at rank >= 111, index size maintained by best-ranked
reserves (published ground rules). Every threshold is a dataclass field the
desk can retune when the books change.

Universe frame columns:
    ticker, full_mktcap_usd, free_float_frac, adv_usd
    [, atvr = annualized traded value ratio; is_member bool]
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

WATCH_BAND = 0.15          # within +/-15% of a threshold -> watchlist


@dataclass
class MSCIRules:
    """MSCI Standard (GIMI) approximation."""
    coverage_target: float = 0.85     # GMSR: 85% cumulative FF coverage
    buffer_lo: float = 0.50           # existing members keep membership down to
    buffer_hi: float = 1.15           # ...and adds enter above (SAIR)
    qir_add_multiple: float = 1.80    # stricter size hurdle for QIR adds (verify book)
    min_float: float = 0.15           # minimum free float (FIF proxy)
    min_atvr: float = 0.15            # liquidity screen (EM level; DM 0.20)
    review: str = "SAIR"              # "SAIR" | "QIR"


@dataclass
class FTSERules:
    """FTSE 100-style rank-buffer approximation (published ground rules)."""
    index_size: int = 100
    add_rank: int = 90                # non-member risen to <= 90 -> add
    delete_rank: int = 111            # member fallen to >= 111 -> delete
    min_float: float = 0.10           # UK-incorporated floor (foreign 25% — note)
    min_atvr: float = 0.05


def _screens(u: pd.DataFrame, min_float: float, min_atvr: float) -> pd.Series:
    atvr = u["atvr"] if "atvr" in u.columns else pd.Series(np.inf, index=u.index)
    return (u["free_float_frac"] >= min_float) & (atvr.fillna(np.inf) >= min_atvr)


# ── MSCI ───────────────────────────────────────────────────────────────────

def predict_msci(universe: pd.DataFrame, members: set,
                 rules: MSCIRules = None) -> dict:
    """Predict adds/deletes for an MSCI-Standard-style review.

    Mechanics: sort the ELIGIBLE universe by full market cap; the GMSR is
    the full cap of the company at which cumulative free-float coverage
    crosses `coverage_target`. Non-members add above `buffer_hi x GMSR`
    (SAIR) or `qir_add_multiple x GMSR` (QIR); members delete below
    `buffer_lo x GMSR` or on failing the float/liquidity screens.
    Watchlist: within +/-15% of the relevant threshold."""
    rules = rules or MSCIRules()
    u = universe.copy()
    u["is_member"] = u["ticker"].isin(members)
    u["eligible"] = _screens(u, rules.min_float, rules.min_atvr)
    su = u[u["eligible"]].sort_values("full_mktcap_usd",
                                      ascending=False).reset_index(drop=True)
    if su.empty:
        return {"available": False, "reason": "no eligible names after screens"}
    ff = su["full_mktcap_usd"] * su["free_float_frac"]
    cum = ff.cumsum() / ff.sum()
    idx = int(np.searchsorted(cum.to_numpy(), rules.coverage_target))
    idx = min(idx, len(su) - 1)
    gmsr = float(su["full_mktcap_usd"].iloc[idx])
    add_thr = gmsr * (rules.qir_add_multiple if rules.review == "QIR"
                      else rules.buffer_hi)
    del_thr = gmsr * rules.buffer_lo

    adds, dels, watch = [], [], []
    for _, r in u.iterrows():
        cap = float(r["full_mktcap_usd"])
        if not r["is_member"]:
            if r["eligible"] and cap >= add_thr:
                adds.append({"ticker": r["ticker"], "full_mktcap_usd": cap,
                             "reason": f"non-member above {rules.review} add "
                             f"threshold {add_thr:,.0f} "
                             f"({cap / gmsr:.2f}x GMSR)"})
            elif r["eligible"] and cap >= add_thr * (1 - WATCH_BAND):
                watch.append({"ticker": r["ticker"], "side": "potential add",
                              "distance": f"{cap / add_thr - 1:+.1%} vs add threshold"})
        else:
            if not r["eligible"]:
                dels.append({"ticker": r["ticker"], "full_mktcap_usd": cap,
                             "reason": "member fails float/liquidity screens"})
            elif cap < del_thr:
                dels.append({"ticker": r["ticker"], "full_mktcap_usd": cap,
                             "reason": f"member below {rules.buffer_lo}x GMSR "
                             f"({cap / gmsr:.2f}x)"})
            elif cap < del_thr * (1 + WATCH_BAND):
                watch.append({"ticker": r["ticker"], "side": "deletion risk",
                              "distance": f"{cap / del_thr - 1:+.1%} vs deletion floor"})
    return {"available": True, "provider": f"MSCI-style ({rules.review})",
            "gmsr_usd": gmsr, "add_threshold_usd": round(add_thr, 0),
            "delete_threshold_usd": round(del_thr, 0),
            "adds": pd.DataFrame(adds), "deletes": pd.DataFrame(dels),
            "watchlist": pd.DataFrame(watch),
            "note": "GIMI approximation: GMSR at "
                    f"{rules.coverage_target:.0%} cumulative FF coverage; "
                    f"range {rules.buffer_lo}-{rules.buffer_hi}x; QIR add "
                    f"multiple {rules.qir_add_multiple}x (verify current "
                    "book). Country-level size interplay, FIF granularity, "
                    "corporate events NOT modeled."}


# ── FTSE ───────────────────────────────────────────────────────────────────

def predict_ftse(universe: pd.DataFrame, members: set,
                 rules: FTSERules = None) -> dict:
    """FTSE 100-style quarterly review: rank the eligible universe by full
    market cap; non-members at rank <= add_rank come in, members at rank
    >= delete_rank drop out, then the index is topped up / trimmed from the
    best-ranked reserves to hold `index_size` (published pairing logic)."""
    rules = rules or FTSERules()
    u = universe.copy()
    u["is_member"] = u["ticker"].isin(members)
    u["eligible"] = _screens(u, rules.min_float, rules.min_atvr)
    su = u[u["eligible"] | u["is_member"]].sort_values(
        "full_mktcap_usd", ascending=False).reset_index(drop=True)
    su["rank"] = su.index + 1

    auto_add = su[(~su["is_member"]) & su["eligible"]
                  & (su["rank"] <= rules.add_rank)]
    auto_del = su[su["is_member"] & (su["rank"] >= rules.delete_rank)]
    adds = [{"ticker": r["ticker"], "rank": int(r["rank"]),
             "reason": f"risen to rank {int(r['rank'])} <= {rules.add_rank}"}
            for _, r in auto_add.iterrows()]
    dels = [{"ticker": r["ticker"], "rank": int(r["rank"]),
             "reason": f"fallen to rank {int(r['rank'])} >= {rules.delete_rank}"}
            for _, r in auto_del.iterrows()]

    # pairing: hold index size — top up from best-ranked non-members, or trim
    # lowest-ranked members, until counts balance
    n_after = int(u["is_member"].sum()) + len(adds) - len(dels)
    pool_add = su[(~su["is_member"]) & su["eligible"]
                  & (~su["ticker"].isin([a["ticker"] for a in adds]))]
    pool_del = su[su["is_member"]
                  & (~su["ticker"].isin([d["ticker"] for d in dels]))]
    while n_after < rules.index_size and len(pool_add):
        r = pool_add.iloc[0]; pool_add = pool_add.iloc[1:]
        adds.append({"ticker": r["ticker"], "rank": int(r["rank"]),
                     "reason": "reserve top-up to hold index size"})
        n_after += 1
    while n_after > rules.index_size and len(pool_del):
        r = pool_del.iloc[-1]; pool_del = pool_del.iloc[:-1]
        dels.append({"ticker": r["ticker"], "rank": int(r["rank"]),
                     "reason": "lowest-ranked member trimmed to hold index size"})
        n_after -= 1

    in_add = {a["ticker"] for a in adds}
    in_del = {d["ticker"] for d in dels}
    watch = [{"ticker": r["ticker"],
              "side": "potential add" if not r["is_member"] else "deletion risk",
              "rank": int(r["rank"])}
             for _, r in su.iterrows()
             if r["ticker"] not in in_add and r["ticker"] not in in_del
             and ((not r["is_member"] and rules.add_rank < r["rank"]
                   <= rules.add_rank + 5)
                  or (r["is_member"] and rules.delete_rank - 5 <= r["rank"]
                      < rules.delete_rank))]
    return {"available": True, "provider": f"FTSE-style ({rules.index_size})",
            "adds": pd.DataFrame(adds), "deletes": pd.DataFrame(dels),
            "watchlist": pd.DataFrame(watch),
            "note": f"Rank-buffer approximation: add <= {rules.add_rank}, "
                    f"delete >= {rules.delete_rank}, reserves hold size "
                    f"{rules.index_size} (published FTSE UK ground-rule "
                    "structure). Nationality tests, fast entry, multiple "
                    "lines NOT modeled."}


# ── flow estimate ──────────────────────────────────────────────────────────

def expected_flow(universe: pd.DataFrame, tickers, passive_aum_usd: float,
                  index_ff_cap_usd: float = None) -> pd.DataFrame:
    """Naive passive-demand estimate per predicted change: weight = FF cap /
    index FF cap; demand = weight x tracked AUM; days-to-trade = demand /
    ADV. `passive_aum_usd` is an INPUT (the desk's estimate of AUM
    benchmarked to the index) — not a claim."""
    u = universe.set_index("ticker")
    idx_ff = index_ff_cap_usd or float(
        (u["full_mktcap_usd"] * u["free_float_frac"]).sum())
    rows = []
    for t in tickers:
        if t not in u.index:
            continue
        ff = float(u.loc[t, "full_mktcap_usd"] * u.loc[t, "free_float_frac"])
        demand = ff / idx_ff * passive_aum_usd
        adv = float(u.loc[t, "adv_usd"])
        rows.append({"ticker": t, "ff_cap_usd": round(ff, 0),
                     "est_passive_demand_usd": round(demand, 0),
                     "days_of_adv": round(demand / adv, 1) if adv > 0
                     else np.inf})
    return pd.DataFrame(rows)


# ── demo universe ──────────────────────────────────────────────────────────

def demo_universe(n: int = 120, seed: int = 21):
    """Synthetic universe with planted stories: a big eligible non-member
    (clear add), a shrunken incumbent (clear delete), a low-float large name
    (screened out), and borderline names for the watchlist. Returns
    (universe_df, members set) — members are the top names by cap minus the
    planted outsiders."""
    rng = np.random.default_rng(seed)
    caps = np.sort(np.exp(rng.normal(22.5, 1.2, n)))[::-1]        # ~ $1-80B
    u = pd.DataFrame({
        "ticker": [f"STK{i:03d}" for i in range(n)],
        "full_mktcap_usd": caps,
        "free_float_frac": rng.uniform(0.25, 0.9, n).round(2),
        "adv_usd": (caps * rng.uniform(0.001, 0.004, n)).round(0),
        "atvr": rng.uniform(0.2, 1.5, n).round(2),
    })
    members = set(u["ticker"].iloc[:60])
    u.loc[2, "ticker"] = "NEWBIG"          # large non-member -> clear add
    members.discard("NEWBIG"); members.discard(u["ticker"].iloc[2])
    u.loc[55, "full_mktcap_usd"] = caps[-1] * 0.5   # incumbent collapsed
    u.loc[58, "free_float_frac"] = 0.05             # incumbent fails float
    return u, members
