"""May-2026 PIT workbench — the engine test frame, visualized (c-32).

Pretend date: ONE DAY BEFORE the May-2026 announcement. Every number
here is computable at that date — caps from the vintage cache as of
Apr-30-2026, membership reconstructed from official review history,
nothing post-announcement enters.

MEMBERSHIP PER VINTAGE (the user's data question, answered in code):
MSCI sells constituent lists, but membership is DERIVABLE free: any
name's membership interval is bounded by its official add/delete
events (46 reviews, print-verified aliases). A name deleted at
review R was a member until R; added at R, member from R. Names
never appearing in 11 years of change lists keep their verified
current status (giants like 2330 — member throughout). The
unnamed remainder of the 83 members is carried as the
count-anchored tail, exactly like the live engine.

TENTATIVE ADD SHORTLIST derivation (explicit, for the UI):
  1. universe = 110 vintage-cached names (every name that mattered
     at a review since 2015 + boundary set)
  2. keep NON-members as of Apr-30-2026
  3. PIT cap = shares(Apr-30) x close(Apr-30) / FX
  4. SAIR add bar = 1.15 x GMSR from the 85% coverage walk
  5. rank by cap / add bar; x >= 0.85 makes the tentative list
  6. graded vs the official May-26 key (known now — this is the
     validation view; the ADDED/RETAINED column is the answer)

Usage: python scripts/pit_workbench_may26.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd                                    # noqa: E402

ASOF = "2026-04-30"
FX = 32.5
OUT = ROOT / "data" / "universe_workbench_tw_may26pit.json"


def membership_asof(events, asof):
    """Membership at `asof` = EWT holdings anchor (full current
    constituent list, free public CSV) REVERSE-ROLLED through every
    official review between `asof` and the anchor date: an add after
    asof means NOT yet a member at asof; a delete after asof means
    STILL a member at asof. Names absent from both anchor and change
    history fall back to the interval logic (covers delisted names).
    Returns ({code: bool}, source_map)."""
    ewt = json.loads((ROOT / "data" / "ewt_members.json")
                     .read_text())
    anchor = set(ewt["codes"])
    mem, src = {}, {}
    post = [ev for ev in events.values() if ev["ann"] > asof]
    # forward interval pass (for delisted/older names)
    for season, ev in sorted(events.items(),
                             key=lambda kv: kv[1]["ann"]):
        if ev["ann"] >= asof:
            continue
        for c in ev["adds"]:
            mem[c], src[c] = True, "official change interval"
        for c in ev["dels"]:
            mem[c], src[c] = False, "official change interval"
    # anchor pass overrides for all names visible today
    seen_post_add = {c for ev in post for c in ev["adds"]}
    seen_post_del = {c for ev in post for c in ev["dels"]}
    for c in anchor | seen_post_add | seen_post_del:
        m = c in anchor
        if c in seen_post_add:
            m = False                 # added after asof
        if c in seen_post_del:
            m = True                  # deleted after asof
        mem[c] = m
        src[c] = (f"EWT holdings anchor ({ewt['asof']}) "
                  "reverse-rolled through official reviews")
    return mem, src


def main():
    cache = json.loads((ROOT / "data" / "tw_vintage_cache.json")
                       .read_text())
    events = json.loads((ROOT / "data" / "msci_tw_events.json")
                        .read_text())
    pitc = json.loads((ROOT / "data" / "pit_may26_asia_cache.json")
                      .read_text())
    interval, mem_srcs = membership_asof(events, ASOF)
    may = events["May26"]
    rows = []
    codes = sorted({k.split("|")[1] for k in cache
                    if k.startswith("sh|")})
    for c in codes:
        px = pd.DataFrame(cache[f"px|{c}"]).set_index("date")
        sh = pd.DataFrame(cache[f"sh|{c}"]).set_index("date")
        px = px[px.index <= ASOF]
        sh = sh[sh.index <= ASOF]
        if len(px) < 10 or len(sh) < 1:
            continue
        shares = sh["NumberOfSharesIssued"].iloc[-1]
        close = px["close"].iloc[-1]
        cap = close * shares / FX
        mem = interval.get(c, False)
        mem_src = mem_srcs.get(
            c, "not in EWT anchor nor any change list -> non-member")
        f_now = sh["ForeignInvestmentSharesRatio"].iloc[-1]
        f_then = (sh["ForeignInvestmentSharesRatio"].iloc[-250]
                  if len(sh) >= 250 else None)
        cap250 = (px["close"].iloc[-250] * FX and
                  close / px["close"].iloc[-250] - 1
                  if len(px) >= 250 else None)
        adv = ((px["close"] * px["Trading_Volume"]).tail(60).mean()
               / FX)
        ffv = None
        for suf in (".TW", ".TWO"):
            v = pitc.get(c + suf, {})
            if "ff" in v:
                ffv = min(v["ff"], 1.0)
        rows.append({
            "code": c, "member_apr30": bool(mem),
            "membership_source": mem_src,
            "cap_usd_b_apr30": round(cap / 1e9, 2),
            "free_float_est": round(ffv, 3) if ffv else 0.7,
            "ff_estimated": ffv is None,
            "foreign_pct_apr30": round(float(f_now), 1)
            if f_now == f_now else None,
            "foreign_12m_pp": round(float(f_now - f_then), 1)
            if f_then is not None and f_now == f_now else None,
            "cap_12m_chg_pct": round(100 * cap250, 1)
            if cap250 is not None else None,
            "adv_usd_m": round(adv / 1e6, 1)})
    df = pd.DataFrame(rows)
    # GMSR walk on this PIT universe (named + count-anchored tail)
    from agents.review_engine import screen_market
    uni = pd.DataFrame({
        "ticker": df["code"], "full_mktcap_usd":
        df["cap_usd_b_apr30"] * 1e9,
        "free_float_frac": df["free_float_est"],
        "adv_usd": df["adv_usd_m"] * 1e6, "atvr": 1.0,
        "member": df["member_apr30"].astype(int)})
    s = screen_market(uni, review="SAIR", member_count=83,
                      tail_hi=10e9, tail_n=500)
    gmsr, add_thr = s["gmsr"], s["add_thr"]
    df["x_add_bar"] = (df["cap_usd_b_apr30"] * 1e9
                       / add_thr).round(2)
    # GIMI dual hurdle: float-adjusted cap must clear HALF the bar
    df["x_add_float"] = (df["cap_usd_b_apr30"] * 1e9
                         * df["free_float_est"]
                         / (0.5 * add_thr)).round(2)
    df["x_floor"] = (df["cap_usd_b_apr30"] * 1e9
                     / (0.5 * gmsr)).round(2)
    # tentative ADD shortlist: non-members within reach of BOTH
    # hurdles (full cap >= 0.85x bar AND float cap >= 0.85x half-bar)
    # plus the 0.15 float floor
    tent = df[(~df["member_apr30"]) & (df["x_add_bar"] >= 0.85)
              & (df["x_add_float"] >= 0.85)
              & (df["free_float_est"] >= 0.15)] \
        .sort_values("x_add_bar", ascending=False)
    last_del = {}
    for season, ev in sorted(events.items(),
                             key=lambda kv: kv[1]["ann"]):
        for c in ev["dels"]:
            last_del[c] = season
    graded = []
    for _, r in tent.iterrows():
        offi = ("ADDED (official May-26)" if r["code"] in may["adds"]
                else "not added")
        prior = (f"ex-member (deleted {last_del[r['code']]})"
                 if r["code"] in last_del else "never a member")
        graded.append({**{k: r[k] for k in
                          ("code", "cap_usd_b_apr30", "x_add_bar",
                           "x_add_float", "free_float_est",
                           "ff_estimated", "foreign_12m_pp",
                           "cap_12m_chg_pct")},
                       "prior_status": prior, "official": offi})
    out = {
        "asof": ASOF, "event": "MSCI May-2026 SAIR (PIT validation)",
        "fx": FX,
        "thresholds": {"gmsr_usd_b": round(gmsr / 1e9, 2),
                       "add_bar_usd_b": round(add_thr / 1e9, 2),
                       "floor_usd_b": round(0.5 * gmsr / 1e9, 2)},
        "members": int(df["member_apr30"].sum()),
        "n_names": len(df),
        "derivation": [
            "1. Universe: 110 vintage-cached names (every review "
            "name 2015-2026 + boundary set); the rest of the 83 "
            "members is the count-anchored tail",
            "2. Membership as of Apr-30: FULL current constituent "
            "list from iShares EWT holdings CSV (free, daily, "
            "public — MSCI Taiwan 25/50, membership ~= Standard) "
            "REVERSE-ROLLED through official reviews after Apr-30 "
            "(May-26 adds removed, May-26 deletes restored); "
            "delisted/older names via change-interval logic",
            "3. PIT cap = shares(Apr-30, TWSE filings via FinMind) "
            "x close(Apr-30) / FX 32.5 — nothing after Apr-30 "
            "enters",
            "4. GMSR = 85% coverage walk on this universe -> add "
            "bar = 1.15x (SAIR)",
            "5. Tentative adds: non-members clearing BOTH GIMI "
            "hurdles at >= 0.85x — full cap vs the bar AND "
            "float-adjusted cap vs half the bar (GIMI dual "
            "requirement) — plus the 0.15 float floor; ranked by "
            "full-cap distance. Names where ff is our default "
            "estimate are flagged: float error is our stated #1 "
            "miss source",
            "6. Graded vs the official May-26 result (shown because "
            "this is the validation view; on a live event this "
            "column does not exist)"],
        "tentative_adds": graded,
        "rows": df.sort_values("cap_usd_b_apr30", ascending=False)
        .to_dict("records")}
    OUT.write_text(json.dumps(out, indent=1))
    print("members reconstructed:", out["members"], "of", len(df),
          "named; GMSR", out["thresholds"])
    print("tentative adds:")
    for g in graded:
        print("  ", g["code"], g["x_add_bar"], "->", g["official"])


if __name__ == "__main__":
    main()
