"""FIF recovery for EVERY MSCI country index (c-144).

Generalizes the Taiwan weights inversion (QA Q76/Q77) to all
13 APAC markets, with one methodological upgrade that removes
the need for a date-matched INDEX float cap:

  GRID-SNAP CALIBRATION.
  FIF_i = c_m x (weight_i / full_cap_i), all on the weights'
  own date. The market constant c_m is unknown (it is
  IndexFloatCap/100), but MSCI rounds every FIF onto a 2.5%
  grid (Appendix VI). So we choose c_m to MINIMIZE total
  distance to that grid. Control test on Taiwan, where the
  truth is known: grid-snap recovered c = 33.27 vs the true
  33.314 (0.13% error) and FIFs to a median 0.0011 — without
  ever being told the index float cap.

  This also self-validates per market: if the recovered FIFs
  do NOT concentrate on the grid, the inputs are wrong
  (mismatched dates, bad ticker map) and the market is
  reported as FAILED rather than published.

DATE ALIGNMENT is the whole ballgame (Q76): weight and full
cap must be the same day. Weights are the ESMA-delayed
vintage (~Jun-1 2026), so full caps are rebuilt as
    close(Jun-1, Yahoo chart) x shares(current) / FX(Jun-1)
Shares drift <1%/quarter (recorded tolerance); prices do not.

NEW ZEALAND has no constituents page (registered gap). But
the NZ index has only 5 members and the Jul-31 factsheet
publishes all 5 float caps -> NZ is solved by the ordinary
implied-FIF route instead, at its own date.

Usage (resumable; Yahoo get_info throttles ~60 calls, so run
per market and re-run to continue):
  py scripts\\apac_fif_inversion.py control          # TW test
  py scripts\\apac_fif_inversion.py market Singapore
  py scripts\\apac_fif_inversion.py all
Out: data/apac_fif_inverted.json (per-market rows + QC)
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "apac_fif_inverted.json"
CACHE = ROOT / "data" / "apac_inv_cache.json"
WEIGHT_DATE = "2026-06-01"      # ESMA vintage of the weights
GRID = 0.025
UA = {"User-Agent": "Mozilla/5.0"}

YAHOO_OK = {   # c-146 venue probe (all verified live)
    "Australia": ".AX ASX", "HongKong": ".HK HKG",
    "India": ".NS NSI", "Indonesia": ".JK JKT",
    "Japan": ".T JPX", "Korea": ".KS KSC",
    "Malaysia": ".KL KLS", "NewZealand": ".NZ NZE",
    "Singapore": ".SI SES", "Thailand": ".BK SET",
    "Taiwan": ".TW TWSE", "China": ".SS/.SZ",
    "Philippines": "NONE — Yahoo has no PH data"}

# c-148: full Yahoo symbols that do NOT follow the market's
# suffix rule, or whose MSCI name won't prefix-match. Extend
# per market as runs expose gaps (this is the Taiwan-style
# OVERRIDES pass, one market at a time).
OVERRIDES = {
    "Singapore": {"OCBC BANK": "O39.SI",
                  "SINGAPORE TECH ENGR": "S63.SI",
                  "SEA A ADR": "SE",            # NYSE line
                  "GRAB HOLDINGS A": "GRAB",    # NASDAQ line
                  "CAPITALAND INTEGRATED COMMERCIAL T":
                      "C38U.SI",
                  "CAPITALAND ASCENDAS REIT": "A17U.SI",
                  "CAPITALAND INTEGRATED": "C38U.SI"},
}

SUFFIX = {"Australia": ".AX", "HongKong": ".HK", "India": ".NS",
          "Indonesia": ".JK", "Japan": ".T", "Korea": ".KS",
          "Malaysia": ".KL", "NewZealand": ".NZ",
          "Philippines": ".PS", "Singapore": ".SI",
          "Taiwan": ".TW", "Thailand": ".BK", "China": ""}
CCY = {"Australia": "AUD", "HongKong": "HKD", "India": "INR",
       "Indonesia": "IDR", "Japan": "JPY", "Korea": "KRW",
       "Malaysia": "MYR", "NewZealand": "NZD",
       "Philippines": "PHP", "Singapore": "SGD",
       "Taiwan": "TWD", "Thailand": "THB", "China": "CNY"}


def _cache():
    return json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() \
        else {"shares": {}, "close": {}, "fx": {}}


def _save(c):
    CACHE.write_text(json.dumps(c, indent=1), encoding="utf-8")


def grid_snap(scores, lo=1.0, hi=100000.0):
    """Pick the market constant that puts the most FIFs on
    MSCI's rounding grid. Coarse-to-fine search."""
    def cost(c):
        # c-148 FIX: FIF <= 1 BY DEFINITION (float can't exceed
        # shares). Without a hard constraint the search is
        # degenerate at small n — the 2.5% grid is dense, so a
        # constant ~1.7x too big also lands names "on grid".
        # Indonesia exposed it: state banks came out 0.775 (true
        # ~0.45) and GOTO 1.617 (impossible). Any c that implies
        # ANY FIF above 1.02 is now infeasible, not merely
        # penalised.
        t = 0.0
        for v in scores:
            f = c * v
            if f <= 0 or f > 1.02:
                return float("inf")
            t += min(abs(f - round(f / GRID) * GRID),
                     GRID / 2) ** 2
        return t
    best, step = None, None
    grid_pts = [lo * (1.0008 ** i) for i in
                range(int(__import__("math").log(hi / lo)
                          / __import__("math").log(1.0008)))]
    for c in grid_pts:
        k = cost(c)
        if best is None or k < best[0]:
            best, step = (k, c), c
    if best is None or best[0] == float("inf"):
        return None            # no feasible constant
    # fine pass
    for c in [step * (1 + d / 20000) for d in range(-40, 41)]:
        k = cost(c)
        if k < best[0]:
            best = (k, c)
    return best[1]


def control():
    """Taiwan: grid-snap vs the known truth."""
    W = json.loads((ROOT / "data" /
                    "tw_member_fifs_weights.json").read_text(encoding="utf-8"))
    U = json.loads((ROOT / "data" / "tw_universe_pit.json")
                   .read_text(encoding="utf-8"))["dates"]["20260601"]["rows"]
    rows = [(r["code"], r["weight_pct"] /
             U[r["code"]]["cap_usd_b"], r["fif_weights"])
            for r in W["rows"] if r["code"] in U]
    c = grid_snap([s for _, s, _ in rows])
    errs = sorted(abs(c * s - t) for _, s, t in rows)
    print(f"grid-snap c = {c:.3f} | true = "
          f"{W['idxcap_jun01_busd'] / 100:.3f}")
    print(f"median |err| {errs[len(errs) // 2]:.4f} | max "
          f"{errs[-1]:.4f} | n {len(rows)}")
    return c


def _yahoo(sym, want, cache):
    """shares (get_info, throttled) + Jun-1 close (chart,
    not throttled). Cached; safe to re-run."""
    import requests
    if want == "close":
        if sym in cache["close"]:
            return cache["close"][sym]
        u = (f"https://query1.finance.yahoo.com/v8/finance/"
             f"chart/{sym}?period1=1779667200&period2="
             f"1780358400&interval=1d")
        try:
            j = requests.get(u, headers=UA, timeout=25).json()
            q = j["chart"]["result"][0]["indicators"]["quote"][0]
            v = next((x for x in reversed(q["close"]) if x),
                     None)
        except Exception:                          # noqa: BLE001
            v = None
        cache["close"][sym] = v
        return v
    if sym in cache["shares"]:
        return cache["shares"][sym]
    u = ("https://query2.finance.yahoo.com/v10/finance/"
         f"quoteSummary/{sym}?modules=defaultKeyStatistics")
    try:
        j = requests.get(u, headers=UA, timeout=25).json()
        v = j["quoteSummary"]["result"][0][
            "defaultKeyStatistics"]["sharesOutstanding"]["raw"]
    except Exception:                              # noqa: BLE001
        v = None
    cache["shares"][sym] = v
    return v


def _close31(sym, cache):
    """Jul-31 close — needed to roll the published Jul-31
    index float cap back to the weights' date (c-148)."""
    k = sym + "|31"
    if k in cache["close"]:
        return cache["close"][k]
    import requests
    u = (f"https://query1.finance.yahoo.com/v8/finance/chart/"
         f"{sym}?period1=1784937600&period2=1785628800"
         "&interval=1d")
    try:
        j = requests.get(u, headers=UA, timeout=25).json()
        q = j["chart"]["result"][0]["indicators"]["quote"][0]
        v = next((x for x in reversed(q["close"]) if x), None)
    except Exception:                              # noqa: BLE001
        v = None
    if v:
        cache["close"][k] = v
    return v


def _fx31(mkt, cache):
    ccy = CCY[mkt]
    k = ccy + "|31"
    if k in cache["fx"]:
        return cache["fx"][k]
    v = _close31(f"{ccy}USD=X", cache)
    if v:
        cache["fx"][k] = v
    return v


def _fx(mkt, cache):
    """Local->USD at the weights date (Jun-1 2026)."""
    ccy = CCY[mkt]
    if ccy in cache["fx"]:
        return cache["fx"][ccy]
    import requests
    u = ("https://query1.finance.yahoo.com/v8/finance/chart/"
         f"{ccy}USD=X?period1=1779667200&period2=1780358400"
         "&interval=1d")
    try:
        j = requests.get(u, headers=UA, timeout=25).json()
        q = j["chart"]["result"][0]["indicators"]["quote"][0]
        v = next((x for x in reversed(q["close"]) if x), None)
    except Exception:                              # noqa: BLE001
        v = None
    cache["fx"][ccy] = v
    return v


def _shares(sym, cache):
    if sym in cache["shares"]:
        return cache["shares"][sym]
    import yfinance as yf
    v = None
    try:
        v = yf.Ticker(sym).fast_info.get("shares")
    except Exception:                              # noqa: BLE001
        pass
    if not v:
        try:
            v = yf.Ticker(sym).get_info().get(
                "sharesOutstanding")
        except Exception:                          # noqa: BLE001
            v = None
    if v:                    # c-148: never cache a failure —
        cache["shares"][sym] = v   # else re-runs skip the name
    return v


def _publish(name, res):
    """Merge one market into data/apac_fif_inverted.json."""
    out = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    out[name] = res
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")


MARKETS = ["Korea", "Australia", "HongKong", "Indonesia",
           "Malaysia", "Thailand", "India", "Japan", "China"]


def run_all(markets=None):
    """Sequential, resumable driver. Re-run until every market
    reports PASS — each pass continues from the cache."""
    for m in (markets or MARKETS):
        print(f"\n=== {m} ===", flush=True)
        try:
            r = market(m)
        except Exception as e:                     # noqa: BLE001
            r = {"status": "ERROR", "err": str(e)[:200]}
        qc = r.get("qc") or {}
        print(f"--- {m}: {qc.get('verdict') or r.get('status')}"
              f"  scored {qc.get('n_scored', 0)}/"
              f"{qc.get('n_members', '?')}"
              f"  on-grid {qc.get('on_grid_pct', '—')}",
              flush=True)


def status():
    """Coverage table — what still needs a re-run."""
    out = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    print(f"{'market':12} {'scored':>10} {'on-grid':>8}  verdict")
    tw = ROOT / "data" / "tw_member_fifs_weights.json"
    if tw.exists():
        d = json.loads(tw.read_text(encoding="utf-8"))
        print(f"{'Taiwan':12} {d['n_mapped']}/{d['n_index']:<7}"
              f"{'1.0':>8}  PASS (own inversion)")
    for m in ["NewZealand", "Singapore"] + MARKETS:
        r = out.get(m) or {}
        qc = r.get("qc") or {}
        n = (f"{qc.get('n_scored', len(r.get('rows', [])))}/"
             f"{qc.get('n_members', len(r.get('rows', [])) or '?')}")
        print(f"{m:12} {n:>10} "
              f"{str(qc.get('on_grid_pct', '—')):>8}  "
              f"{qc.get('verdict') or r.get('status') or 'NOT RUN'}")


def market(name, limit=None):
    """Full inversion for one market. Resumable: every Yahoo
    hit is cached, so re-running continues where it stopped
    (Yahoo throttles get_info at ~60 calls/session)."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from ticker_backfill import prefix_match
    cons = json.loads((ROOT / "data" /
                       "msci_official_constituents.json")
                      .read_text(encoding="utf-8"))["markets"]
    if name not in cons:
        return {"market": name, "status": "NO_WEIGHTS",
                "need": "not on MSCI's constituents tool "
                        "(NewZealand: run `nz`)"}
    fund = json.loads((ROOT / "data" / "apac_members.json")
                      .read_text(encoding="utf-8"))["markets"][name]
    names = fund.get("names")
    if isinstance(names, str):
        names = eval(names)                    # stored repr
    t2n = {k: v for k, v in (names or {}).items()}
    n2t = {v.upper(): k for k, v in t2n.items()}
    cache = _cache()
    fxr = _fx(name, cache)
    rows, miss = [], []
    members = cons[name]["constituents"]
    if limit:
        members = members[:limit]
    ov = OVERRIDES.get(name, {})
    fails = 0
    for i, m in enumerate(members, 1):
        nm = m["security"].upper()
        sym = ov.get(nm)
        tick = (sym.split(".")[0] if sym else
                (n2t.get(nm) or prefix_match(nm, n2t)))
        if not tick:
            miss.append((m["security"], m["weight"]))
            print(f"  [{i}/{len(members)}] {nm[:28]:28} "
                  "UNMAPPED", flush=True)
            continue
        sym = sym or (tick + SUFFIX[name])
        S = _shares(sym, cache)
        px = _yahoo(sym, "close", cache)
        _save(cache)
        # THROTTLE BACKOFF: Yahoo starts returning empty after
        # ~60 get_info calls. Pause, then bail with a clear
        # message so the re-run picks up from the cache.
        if S is None:
            fails += 1
            if fails in (5, 10):
                print("   ...pausing 60s (possible throttle)",
                      flush=True)
                time.sleep(60)
            if fails >= 18:
                print(f"  THROTTLED after {i} names — re-run "
                      "the same command later; the cache "
                      "resumes.", flush=True)
                break
        else:
            fails = 0
        print(f"  [{i}/{len(members)}] {sym:14} "
              f"shares={'ok' if S else '—'} "
              f"px={'ok' if px else '—'}", flush=True)
        cap = (S * px * fxr / 1e9) if (S and px and fxr) \
            else None
        rows.append({"code": tick, "name": m["security"],
                     "weight_pct": m["weight"],
                     "full_cap_usd_b": (round(cap, 3) if cap
                                        else None),
                     "_px": px, "_sh": S, "_sym": sym,
                     "score": (m["weight"] / cap if cap
                               else None)})
        time.sleep(0.4)
    sc = [r["score"] for r in rows if r["score"]]
    if len(sc) < 5:
        # c-146: say WHY, per failure mode, instead of a bare
        # "INSUFFICIENT" (Bill's Philippines run)
        no_px = sum(1 for r in rows if r.get("_px") is None)
        no_sh = sum(1 for r in rows if r.get("_sh") is None)
        why = ("NO_PRICE_SOURCE — Yahoo does not cover this "
               "market at all (verified: every .PS symbol "
               "resolves to the empty 'YHD' venue). Needs PSE "
               "EDGE or a paid feed; registered gap."
               if name == "Philippines" else
               "no shares from Yahoo for most names"
               if no_sh > no_px else
               "no prices at the weights date")
        _publish(name, {"market": name,
                        "status": "INSUFFICIENT", "why": why})
        return {"market": name, "status": "INSUFFICIENT",
                "why": why, "n_scored": len(sc),
                "n_members": len(members),
                "names_missing_price": no_px,
                "names_missing_shares": no_sh,
                "unmapped": miss}
    # ---- PRIMARY CALIBRATION (c-148) --------------------
    # The 2.5% grid is dense, so with 10-20 names grid-snap has
    # many near-equal optima and can land on a WRONG MULTIPLE
    # (Indonesia: state banks came out 0.775 when the state
    # owns ~55%). Anchor it instead on a published number:
    #   IdxCap(Jun-1) = IdxCap(Jul-31) / R
    # where R is the float-cap-weighted USD return of the
    # membership Jun-1 -> Jul-31 (the index's own return, given
    # FIFs/NOS unchanged — which Q80/Q82 verified). Then
    #   c = IdxCap(Jun-1) / 100
    # and grid-snap becomes a VALIDATION, not the calibration.
    arch = json.loads((ROOT / "data" /
                       "apac_factsheet_archive.json").read_text(encoding="utf-8"))
    idx31 = ((arch.get(name) or {}).get("2026-07") or {}).get(
        "index_float_cap_musd")
    c_anchor = None
    if idx31:
        f31 = _fx31(name, cache)
        num = den = 0.0
        for r in rows:
            if not r.get("score"):
                continue
            sym = r.get("_sym")
            p31 = _close31(sym, cache) if sym else None
            p01 = r.get("_px")
            if p31 and p01 and f31 and fxr:
                num += r["weight_pct"] * (p31 * f31) / \
                    (p01 * fxr)
                den += r["weight_pct"]
        _save(cache)
        if den > 50:                     # >half the index
            R = num / den
            c_anchor = (idx31 / 1000 / R) / 100
    # c-148: one bad share count (dual class, ADR line, stale
    # Yahoo count) makes the whole market infeasible. Drop the
    # binding outlier — the name whose score forces the
    # smallest constant — and refit, up to 20% of the members.
    dropped = []
    c = c_anchor or grid_snap(sc)
    while c is None and len(dropped) < max(1, len(sc) // 5):
        worst = max(sc)
        nm = next((r["name"] for r in rows
                   if r.get("score") == worst), "?")
        dropped.append(nm)
        sc = [x for x in sc if x != worst]
        for r in rows:
            if r.get("score") == worst:
                r["score"] = None
                r["excluded"] = ("share count implausible — "
                                 "forces FIF > 1")
        c = c_anchor or (grid_snap(sc) if len(sc) >= 5
                         else None)
    if c is None:
        _publish(name, {"market": name, "status": "NO_FIT",
                        "why": "no constant keeps every FIF "
                               "<= 1.0 — a full cap is wrong "
                               "(share class / dual listing?)"})
        return {"market": name, "status": "NO_FIT",
                "why": "no feasible calibration constant; "
                       "check share counts for dual-listed or "
                       "multi-class names",
                "n_scored": len(sc)}
    for r in rows:
        r["fif"] = (round(c * r["score"], 3) if r["score"]
                    else None)
        r["grid_dist"] = (round(abs(r["fif"] - round(
            r["fif"] / GRID) * GRID), 3)
            if r.get("fif") else None)
        r.pop("score", None)
        r.pop("_px", None)
        r.pop("_sh", None)
        r.pop("_sym", None)
    ok = [r for r in rows if r.get("fif")]
    on = sum(1 for r in ok if r["grid_dist"] <= 0.01)
    bad = sum(1 for r in ok if r["fif"] > 1.05)
    qc = {"n_members": len(members), "n_scored": len(ok),
          "calibration": ("index-float-cap anchor" if c_anchor
                          else "grid-snap (no factsheet cap)"),
          "excluded_bad_share_count": dropped,
          "calib_c": round(c, 3),
          "on_grid_pct": round(on / len(ok), 3),
          "impossible_fif_gt_1.05": bad,
          "unmapped": miss,
          "verdict": ("PASS" if on / len(ok) >= 0.6 and not bad
                      else "FAILED — inputs suspect, not "
                           "published as FIFs")}
    res = {"market": name, "weights_vintage": WEIGHT_DATE,
           "fx_local_usd": fxr, "qc": qc, "rows": rows}
    _publish(name, res)
    return res


def newzealand():
    """NZ index = 5 members, all in the Jul-31 factsheet
    top-10 -> ordinary implied FIF, no inversion needed."""
    fs = json.loads((ROOT / "data" /
                     "apac_factsheet_top10.json").read_text(encoding="utf-8"))
    caps = json.loads((ROOT / "data" / "apac_caps_cache.json")
                      .read_text(encoding="utf-8")).get("NewZealand", {})
    import requests
    fx = requests.get("https://query1.finance.yahoo.com/v8/"
                      "finance/chart/NZDUSD=X?interval=1d",
                      headers=UA, timeout=25).json()
    r = fx["chart"]["result"][0]["meta"]["regularMarketPrice"]
    out = []
    for m in fs.get("NewZealand", []):
        nm = m["name"]
        hit = next((v for k, v in caps.items()
                    if k.upper() in nm.upper()
                    or nm.upper().startswith(k.upper())), None)
        cap_usd = (hit["cap_local"] * r / 1e9) if hit else None
        out.append({
            "name": nm, "float_cap_usd_b": m["float_cap_usd_b"],
            "full_cap_usd_b": (round(cap_usd, 2)
                               if cap_usd else None),
            "fif": (round(m["float_cap_usd_b"] / cap_usd, 3)
                    if cap_usd else None),
            "note": "" if hit else "NO_CAP — needs NZ shares"})
    return {"market": "NewZealand", "method":
            "factsheet-implied (all 5 members in top-10)",
            "asof": "2026-07-31", "rows": out}


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "control":
        control()
    elif a and a[0] == "nz":
        print(json.dumps(newzealand(), indent=1))
    elif a and a[0] == "market" and len(a) > 1:
        r = market(a[1])
        qc = r.get("qc") or {}
        print(json.dumps(qc or r, indent=1))
    elif a and a[0] == "all":
        run_all(a[1:] or None)
    elif a and a[0] == "status":
        status()
    else:
        print(__doc__)
