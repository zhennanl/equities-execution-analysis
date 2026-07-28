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
    # Country size-segment migration (May-2026 Taiwan backtest lesson:
    # SAIR deletions are usually Standard->SmallCap MIGRATIONS at the
    # country coverage cutoff, NOT global-minimum-size failures — the
    # global floor caught 0/7 actual deletions; this rule caught 7/7).
    # None disables. 0.85 = members below 85% cumulative country FF
    # coverage (with buffer) are flagged as migration deletions.
    country_coverage: float = None
    country_buffer: float = 0.05      # extra coverage grace before migrating
    # GIMI also requires the FREE-FLOAT cap to clear a fraction of the size
    # cutoff (~50% in the book) — a big-cap/low-float name (state holdings,
    # anchor shareholders) can pass the full-cap hurdle yet stay out.
    min_ffcap_frac_of_add: float = 0.5


@dataclass
class FTSERules:
    """FTSE 100-style rank-buffer approximation (published ground rules)."""
    index_size: int = 100
    add_rank: int = 90                # non-member risen to <= 90 -> add
    delete_rank: int = 111            # member fallen to >= 111 -> delete
    min_float: float = 0.10           # UK-incorporated floor (foreign 25% — note)
    min_atvr: float = 0.05
    allowed_suffixes: tuple = None    # listing-venue eligibility (the MPI
                                      # lesson: TPEx names can't join a
                                      # TWSE-only index); None = no screen
    assumed_cap_sigma: float = 0.15   # cap-estimate error for the
                                      # probabilistic confidence column


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
        ffcap = cap * float(r["free_float_frac"])
        if not r["is_member"]:
            if (r["eligible"] and cap >= add_thr
                    and ffcap < rules.min_ffcap_frac_of_add * add_thr):
                watch.append({"ticker": r["ticker"], "side": "blocked add",
                              "distance": f"FF cap {ffcap:,.0f} < "
                              f"{rules.min_ffcap_frac_of_add:.0%} of add "
                              "threshold — full cap qualifies, float does not"})
            elif r["eligible"] and cap >= add_thr:
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
    # country size-segment migration (SAIR mechanism; optional)
    if rules.country_coverage:
        mem = u[u["is_member"] & u["eligible"]].copy()
        mem["ff"] = mem["full_mktcap_usd"] * mem["free_float_frac"]
        mem = mem.sort_values("ff", ascending=False)
        cum = mem["ff"].cumsum() / mem["ff"].sum()
        cut = rules.country_coverage + rules.country_buffer
        flagged = set(mem.loc[cum > cut, "ticker"])
        already = {d["ticker"] for d in dels}
        for t in sorted(flagged - already):
            row = u.loc[u["ticker"] == t].iloc[0]
            dels.append({"ticker": t,
                         "full_mktcap_usd": float(row["full_mktcap_usd"]),
                         "reason": f"segment migration: below "
                         f"{rules.country_coverage:.0%} country FF coverage "
                         f"(+{rules.country_buffer:.0%} buffer) — "
                         "Standard->SmallCap candidate"})

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
    if rules.allowed_suffixes is not None:
        from agents.universe_builder import _suffix_ok
        u["eligible"] &= u["ticker"].map(
            lambda t: _suffix_ok(t, rules.allowed_suffixes))
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

    # boundary-confidence tags: how much cap change would flip each call?
    # (first-order margin vs the name on the other side of the boundary —
    # rank deletions proved noise-fragile in the Taiwan-50 backtest, so
    # fragile calls must label themselves in EVERY market.)
    def _cap_at(rk):
        m = su[su["rank"] == rk]
        return float(m["full_mktcap_usd"].iloc[0]) if len(m) else np.nan
    add_bnd, del_bnd = _cap_at(rules.add_rank + 1), _cap_at(rules.delete_rank - 1)
    for a_ in adds:
        cap = float(su.loc[su["ticker"] == a_["ticker"],
                           "full_mktcap_usd"].iloc[0])
        mg = (cap / add_bnd - 1.0) if np.isfinite(add_bnd) else np.nan
        a_["margin_pct"] = round(mg * 100, 1) if np.isfinite(mg) else None
        a_["confidence"] = ("HIGH" if np.isfinite(mg) and mg >= 0.10
                            else "LOW (watch zone)")
    for d_ in dels:
        m = su.loc[su["ticker"] == d_["ticker"], "full_mktcap_usd"]
        cap = float(m.iloc[0]) if len(m) else np.nan
        mg = (1.0 - cap / del_bnd) if np.isfinite(del_bnd) and np.isfinite(cap) else np.nan
        d_["margin_pct"] = round(mg * 100, 1) if np.isfinite(mg) else None
        d_["confidence"] = ("HIGH" if np.isfinite(mg) and mg >= 0.10
                            else "LOW (watch zone)")

    # probabilistic column: P(call survives cap noise) under a normal
    # approximation at the assumed cap error — the Monte-Carlo finding
    # (rank-boundary fragility) as a per-name number, not just a tag.
    from math import erf, sqrt
    def _p_survive(mg_pct):
        if mg_pct is None:
            return None
        z = (mg_pct / 100.0) / max(rules.assumed_cap_sigma, 1e-6)
        return round(0.5 * (1 + erf(z / sqrt(2))), 2)
    for row in adds + dels:
        row["p_survives_noise"] = _p_survive(row.get("margin_pct"))

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
    # reserve list (FTSE publishes one; we should EMIT one, not just grade
    # against it): the best-ranked eligible non-members below the add
    # boundary, after this review's changes.
    reserve = su[(~su["is_member"]) & su["eligible"]
                 & (~su["ticker"].isin(in_add))
                 & (su["rank"] > rules.add_rank)].head(5)
    reserve_list = reserve[["ticker", "rank", "full_mktcap_usd"]].reset_index(drop=True)

    return {"available": True, "provider": f"FTSE-style ({rules.index_size})",
            "adds": pd.DataFrame(adds), "deletes": pd.DataFrame(dels),
            "watchlist": pd.DataFrame(watch),
            "reserve_list": reserve_list,
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


# ── robustness: is a backtest result an artifact of measurement error? ─────

def robustness_check(universe: pd.DataFrame, members: set,
                     actual_adds: set, actual_deletes: set,
                     rules: MSCIRules = None, n_draws: int = 500,
                     cap_sigma: float = 0.2, float_sigma: float = 0.05,
                     seed: int = 0, ignore_prefix: str = "TAIL",
                     predict_fn=None) -> dict:
    """Monte-Carlo the input-data uncertainty: perturb every cap by
    lognormal noise (sigma = your honest estimate of cap error) and every
    float by clipped normal noise, re-run predict_msci each draw, and
    report the DISTRIBUTION of add/delete precision and recall vs the
    actual outcome.

    This is the answer to 'with approximate caps, borderline names could
    flip': instead of asserting robustness, measure it. A conclusion that
    survives 90% of draws at the claimed error level is evidence; one
    that collapses was an artifact of the reconstruction."""
    rng = np.random.default_rng(seed)
    rules = rules or MSCIRules()
    add_rec, add_prec, del_rec, del_prec = [], [], [], []
    for _ in range(n_draws):
        u = universe.copy()
        u["full_mktcap_usd"] = (u["full_mktcap_usd"]
                                * np.exp(rng.normal(0, cap_sigma, len(u))))
        u["free_float_frac"] = np.clip(
            u["free_float_frac"] + rng.normal(0, float_sigma, len(u)),
            0.05, 1.0)
        r = (predict_fn(u, members) if predict_fn is not None
             else predict_msci(u, members, rules))
        pa = {t for t in r["adds"].get("ticker", [])
              if not str(t).startswith(ignore_prefix)}
        pdl = {t for t in r["deletes"].get("ticker", [])
               if not str(t).startswith(ignore_prefix)}
        add_rec.append(len(pa & actual_adds) / max(len(actual_adds), 1))
        add_prec.append(len(pa & actual_adds) / max(len(pa), 1) if pa else 1.0)
        del_rec.append(len(pdl & actual_deletes) / max(len(actual_deletes), 1))
        del_prec.append(len(pdl & actual_deletes) / max(len(pdl), 1)
                        if pdl else 1.0)

    def _s(x):
        x = np.array(x)
        return {"mean": round(float(x.mean()), 3),
                "p10": round(float(np.percentile(x, 10)), 3),
                "p50": round(float(np.percentile(x, 50)), 3),
                "share_perfect": round(float((x >= 0.999).mean()), 3)}
    return {"n_draws": n_draws, "cap_sigma": cap_sigma,
            "float_sigma": float_sigma,
            "add_recall": _s(add_rec), "add_precision": _s(add_prec),
            "delete_recall": _s(del_rec), "delete_precision": _s(del_prec),
            "note": f"Caps perturbed lognormal(sigma={cap_sigma}), floats "
                    f"normal(sigma={float_sigma}) clipped, {n_draws} draws. "
                    "share_perfect = fraction of draws with metric = 1.0."}


# ════════════════ 7x: membership ledger & factual reconciliation ════════
# The Feng Tay incident: our Aug draft carried a DELETE call on a name
# MSCI had already deleted in February. The fix is mechanical — MSCI
# publishes every change as a free PDF; membership state must be
# reconciled against that ledger BEFORE any prediction is issued.

import re as _re


def parse_msci_public_list(text: str) -> dict:
    """Parse an MSCI Global Standard public change list (pdftotext
    -layout output) -> {COUNTRY: {"adds": [...], "deletes": [...]}}."""
    out, country = {}, None
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        m = _re.match(r"\s*MSCI ([A-Z ]+?) INDEX\s*$", ln)
        if m:
            country = m.group(1).strip()
            out[country] = {"adds": [], "deletes": []}
            continue
        if country is None:
            continue
        s = ln.rstrip()
        if not s or "Additions" in s or "Page " in s or "©" in s:
            # blank line ends a section only after content collected
            if not s and (out[country]["adds"] or
                          out[country]["deletes"]):
                country = None
            continue
        # two-column layout: split on 3+ spaces
        parts = _re.split(r"\s{3,}", s.strip())
        indent = len(ln) - len(ln.lstrip())
        if len(parts) == 2:
            a, d = parts
            if a.strip() not in ("None", ""):
                out[country]["adds"].append(a.strip())
            if d.strip() not in ("None", ""):
                out[country]["deletes"].append(d.strip())
        elif len(parts) == 1 and parts[0] not in ("None",):
            # single column: right column (deletion) if indented deep
            if indent >= 25:
                out[country]["deletes"].append(parts[0])
            else:
                out[country]["adds"].append(parts[0])
    return {c: v for c, v in out.items() if v["adds"] or v["deletes"]}


def reconcile_membership(members: dict, ledgers: list[dict],
                         country: str) -> list[dict]:
    """members: {official_name: is_member_bool} (names as they appear
    in MSCI lists — supply an alias map for tickers). ledgers: parsed
    public lists, OLDEST first. Returns violations:
       STALE_MEMBER     we say member, ledger says deleted since
       STALE_NONMEMBER  we say non-member, ledger says added since
    Later ledgers override earlier ones (delete then re-add is legal)."""
    state = {}                       # name -> last known action
    for ledger in ledgers:
        ch = ledger.get(country, {})
        for n in ch.get("adds", []):
            state[n.upper()] = "added"
        for n in ch.get("deletes", []):
            state[n.upper()] = "deleted"
    violations = []
    for name, is_member in members.items():
        last = state.get(name.upper())
        if is_member and last == "deleted":
            violations.append({"name": name, "type": "STALE_MEMBER",
                               "fix": "set member=0 (deleted in a prior "
                                      "official list)"})
        if not is_member and last == "added":
            violations.append({"name": name, "type": "STALE_NONMEMBER",
                               "fix": "set member=1 (added in a prior "
                                      "official list)"})
    return violations


def explain_call(kind: str, ticker: str, cap_usd: float,
                 gmsr_usd: float, threshold_usd: float,
                 float_frac: float | None = None,
                 membership_verified: bool = False,
                 crowding: str | None = None) -> dict:
    """Structured, client-readable rationale for one call — every field
    is a checkable fact, and verification status is explicit."""
    ratio = cap_usd / gmsr_usd if gmsr_usd else float("nan")
    checks = {
        "mechanism": (f"{'non-member above' if kind == 'ADD' else 'member below'} "
                      f"threshold: cap ${cap_usd/1e9:.1f}B = "
                      f"{ratio:.2f}x GMSR (${gmsr_usd/1e9:.1f}B); "
                      f"threshold ${threshold_usd/1e9:.1f}B"),
        "float_screen": (f"free float {float_frac:.2f} — min-FF-cap rule "
                         f"{'passes' if float_frac and float_frac > 0.3 else 'CHECK'}"
                         if float_frac is not None else "not evaluated"),
        "membership_verified": ("YES — reconciled vs official change "
                                "ledger" if membership_verified else
                                "NO — verify before committing (Feng "
                                "Tay rule)"),
        "positioning": crowding or "no read",
    }
    return {"call": kind, "ticker": ticker, **checks}
