"""PIT constituent time-travel — any date, Taiwan (c-43).

Given ANY date D:
  1. MEMBERSHIP as of D = EWT anchor reverse-rolled through every
     official review whose EFFECTIVE date is after D (changes bind
     at the effective close, so "the most recent index list before
     D"); delisted/older names via forward change intervals.
  2. CAPS as of D from the vintage cache (shares x close, last row
     <= D) — full member ladder RANKED BY CAP.
  3. CANDIDATES: GMSR walk on the PIT universe -> delete candidates
     (members inside the buffer band, hard-floor breaches flagged)
     and add candidates (non-members near/over the bar, GIMI dual
     hurdle + 0.15 float floor). Breadth honesty: the non-member
     universe is the vintage set (every name that mattered at a
     review 2015-2026 + boundary) — the blind band below it is
     stated, not denied.

Validated: ladder_asof around May-26 / Nov-25 reproduces the
7/7 + 7/7 delete-pool results (pinned).
"""
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FX = 32.5
FLAGGED = {"4551"}            # EWT-vs-history inconsistency


@lru_cache(maxsize=1)
def _data():
    cache = json.loads((ROOT / "data" / "tw_vintage_cache.json")
                       .read_text())
    events = json.loads((ROOT / "data" / "msci_tw_events.json")
                        .read_text())
    ewt = set(json.loads((ROOT / "data" / "ewt_members.json")
                         .read_text())["codes"])
    names = (json.loads((ROOT / "data" / "apac_members.json")
                        .read_text())["markets"]["Taiwan"]
             .get("names", {}))
    try:
        pitc = json.loads((ROOT / "data" /
                           "pit_may26_asia_cache.json").read_text())
    except Exception:                          # noqa: BLE001
        pitc = {}
    return cache, events, ewt, names, pitc


def members_asof(date: str) -> tuple[dict, str]:
    """{code: bool}, plus the resolved-state line ("after the
    <season> review, effective <eff>")."""
    _, events, ewt, _, _ = _data()
    mem = {c: True for c in ewt if c not in FLAGGED}
    # forward pass for names not visible today (delisted etc.)
    last_eff = None
    for season, ev in sorted(events.items(),
                             key=lambda kv: kv[1]["eff"]):
        if ev["eff"] <= date:
            for c in ev["adds"]:
                if c in FLAGGED:
                    continue
                mem.setdefault(c, True)
                mem[c] = True if c not in ewt else mem[c]
            for c in ev["dels"]:
                if c not in ewt:
                    mem[c] = False
            last_eff = (season, ev["eff"])
    # reverse-roll the anchor through events effective AFTER date
    for season, ev in events.items():
        if ev["eff"] > date:
            for c in ev["adds"]:
                mem[c] = False        # not yet added at D
            for c in ev["dels"]:
                mem[c] = True         # not yet deleted at D
    line = (f"most recent index state before {date}: after the "
            f"{last_eff[0]} review (effective {last_eff[1]})"
            if last_eff else f"state before the first cached "
                             f"review; anchor reverse-rolled")
    return mem, line


def _cap_asof(code, date):
    cache = _data()[0]
    px, sh = cache.get(f"px|{code}"), cache.get(f"sh|{code}")
    if not px or not sh:
        return None
    p = [r for r in px if r["date"] <= date]
    s = [r for r in sh if r["date"] <= date]
    if not p or not s:
        return None
    return (p[-1]["close"] * s[-1]["NumberOfSharesIssued"] / FX,
            p[-1]["date"])


def ladder_asof(date: str) -> dict:
    import pandas as pd
    from agents.review_engine import screen_market
    cache, events, ewt, names, pitc = _data()
    mem, line = members_asof(date)
    codes = sorted({k.split("|")[1] for k in cache
                    if k.startswith("sh|")})
    rows, unpriced = [], []
    import datetime as _dt
    stale_cut = str(_dt.date.fromisoformat(date)
                    - _dt.timedelta(days=45))
    for c in sorted(set(mem) | set(codes)):
        is_m = mem.get(c, False)
        capd = _cap_asof(c, date)
        if capd is None or capd[1] < stale_cut:
            # no price, or last trade >45d before the date —
            # delisted/suspended by then (the Inotera-at-2019 trap)
            if is_m:
                unpriced.append(c)
            continue
        cap, asof = capd
        ffv = None
        for suf in (".TW", ".TWO"):
            v = pitc.get(c + suf, {})
            if "ff" in v:
                ffv = min(v["ff"], 1.0)
        rows.append({"code": c, "member": bool(is_m),
                     "company": names.get(c, ""),
                     "cap_usd_b": round(cap / 1e9, 2),
                     "price_asof": asof,
                     "ff": ffv if ffv else 0.7,
                     "ff_estimated": ffv is None})
    df = pd.DataFrame(rows).sort_values("cap_usd_b",
                                        ascending=False)
    df["rank"] = range(1, len(df) + 1)
    memdf = df[df["member"]]
    uni = pd.DataFrame({
        "ticker": df["code"], "full_mktcap_usd":
        df["cap_usd_b"] * 1e9, "free_float_frac": df["ff"],
        "adv_usd": 1e7, "atvr": 1.0,
        "member": df["member"].astype(int)})
    s = screen_market(uni, review="SAIR",
                      member_count=int(df["member"].sum()),
                      tail_hi=10e9, tail_n=400)
    gmsr = s["gmsr"]
    dels, adds = [], []
    for _, r in df.iterrows():
        x = r["cap_usd_b"] * 1e9 / gmsr
        if r["member"] and x < 1.15:
            dels.append({"code": r["code"],
                         "company": r["company"],
                         "cap_usd_b": r["cap_usd_b"],
                         "x_gmsr": round(x, 2),
                         "class": ("BELOW HARD FLOOR (0.5x)"
                                   if x < 0.5 else
                                   "below GMSR — sweep zone"
                                   if x < 1.0 else
                                   "buffer band 1.0-1.15x")})
        if not r["member"]:
            xf = (r["cap_usd_b"] * 1e9 * r["ff"]
                  / (0.5 * 1.15 * gmsr))
            if (x >= 0.85 * 1.15 and xf >= 0.85
                    and r["ff"] >= 0.15):
                adds.append({"code": r["code"],
                             "company": r["company"],
                             "cap_usd_b": r["cap_usd_b"],
                             "x_add_bar": round(x / 1.15, 2),
                             "ff": r["ff"],
                             "ff_estimated": bool(
                                 r["ff_estimated"])})
    return {"date": date, "resolved": line,
            "n_members": int(df["member"].sum()),
            "unpriced_members": unpriced,
            "gmsr_usd_b": round(gmsr / 1e9, 2),
            "ladder": df[["rank", "code", "company", "member",
                          "cap_usd_b", "price_asof"]]
            .to_dict("records"),
            "delete_candidates": sorted(dels,
                                        key=lambda r: r["x_gmsr"]),
            "add_candidates": sorted(adds,
                                     key=lambda r: -r["x_add_bar"]),
            "breadth_note": (
                "Add-side universe = names that mattered at a "
                "review 2015-2026 + the boundary set; a name never "
                "near the index before is invisible here — the "
                "blind band, stated. Delete-side is COMPLETE "
                "(full member ladder).")}
