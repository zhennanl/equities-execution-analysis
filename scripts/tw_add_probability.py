#!/usr/bin/env python3
"""P(addition) per candidate, from evidence rather than a zone.

    py scripts\\tw_add_probability.py

THE PROBLEM WITH THE NUMBER ON THE PAGE. The registered call
gives every guaranteed-zone name the same probability — 0.6177 =
a base rate x four haircuts. Sensible, but it throws away the one
thing the size screen measures: HOW FAR each name clears. Nanya
clears the addition bar by 4.78x the cutoff, Winbond by 2.50x,
Phison by 1.55x against a 1.50x bar. Those are not the same risk,
and a model that prints one number for all of them is leaving its
own best input on the table.

────────────────────────────────────────────────────────────────
HOW INSTITUTIONS MODEL THIS, from the published record

1. DETERMINISTIC REPLICATION, SCORED. Index-tracking managers
   (L&G publishes theirs quarterly) rebuild the rulebook and
   issue binary calls, then track a hit rate — theirs was 57 of
   64 on MSCI World last quarter, ~86-90 long-run. The published
   methodology is the model; the accuracy score is the implied
   probability. Works best in DM where inputs are clean.

2. DISTANCE-TO-THRESHOLD PROBITS. The Russell-reconstitution
   literature (Chang/Hong/Liskovich; Ben-David/Franzoni/Moussawi;
   the NBER "improved method" paper) models P(assignment) as a
   smooth function of distance from the reconstructed threshold —
   a fuzzy regression discontinuity. The insight: THE RULE IS
   SHARP BUT THE RESEARCHER'S INPUTS ARE NOT, so the probability
   that the TRUE cap clears is Phi(measured clearance /
   measurement error). Probability rises smoothly with distance
   for exactly one reason: estimation error.

3. HISTORICAL CALIBRATION. Condition on the setup — "of
   candidates that looked like this, how many were added?" —
   which is what the registered base rates already do, coarsely.

4. DISCRETION PRICED SEPARATELY. Whatever the arithmetic says,
   MSCI keeps degrees of freedom no simulation reaches: the
   member count can flex (§2.3.3), ATVR liquidity is computed on
   data nobody outside sees, and the price date is one of ten
   days MSCI picks. Institutions carry this as a haircut
   CALIBRATED ON HISTORY, not as a guess.

This file implements 2 + 3 + 4 on this project's own data:

    P(add) = P_size(name)        (c-360: discretion is a NAMED
             ^ Monte Carlo        unpriced risk, multiplied
                                  nowhere — see main())

────────────────────────────────────────────────────────────────
LENS 1 — P_size BY MONTE CARLO, name by name

Each draw perturbs the two inputs of the size verdict that are
genuinely unknowable before the announcement, and asks whether
the name still clears both bars:

  cutoff        uniform +-5% — the site's standing band on the
                85% coverage walk over an estimated float stack.
                COMMON across names within a draw: if the cutoff
                is off, it is off for everyone. Both derived
                bars move with it (addition bar = 1.5x, minimum
                float = 0.5x).

  price date    MSCI uses one of the last ten business days of
                the prior month (GIMI; confirmed in L&G's
                process note). Our caps are struck 2026-07-31,
                the window's last day. A draw picks d ~ U{0..9}
                days back and moves the cap by a normal shock
                scaled sqrt(d) x the name's own realised daily
                vol (`prevol` from the scenarios file).

  free float    NOT drawn (c-365, Bill). The error study —
                Yahoo FIF vs the FIF implied by MSCI's own
                factsheet weights (tw_fif_aligned_jul31.json:
                mean -3.7%, sd 6.0%) — has n=10, too thin to
                parameterize a distribution, so drawing from it
                dressed two shaky moments as measurement. The
                FIF is taken as computed; float-stack error is
                what the ±5% cutoff band already generalizes
                over, since the cutoff is struck ON that stack.
                The study stays recorded as evidence, unused.

  P_size = share of 20,000 draws clearing BOTH the full-cap
  addition bar and the free-float minimum (at the computed FIF).

WHY THIS IS THE RUSSELL METHOD AND NOT A NEW IDEA: the rule
stays sharp inside every draw; only the inputs move. The output
is the probability that the TRUE inputs sit on the passing side
of a rule we can see exactly.

────────────────────────────────────────────────────────────────
LENS 2 — DISCRETION (formerly P_gates; NOT multiplied since
c-360, kept here as the reasoning record)

The 32-review backtest (data/backtest_taiwan.json) counts, at
each clearance threshold, how many crossers were added and how
many were not. Differencing the sweep gives per-band precision:

    1.00-1.25x bar   6 added, 4 not    ~60%
    1.25-1.50x bar   5 added, 3 not    ~63%
    >1.50x bar       1 added, 19 not   ~5%   <- READ ON

That last band is not evidence that clearing hugely is BAD. It
is contamination: a handful of very large names sit above the
bar at every review and are never added because they fail the
FLOAT and FOREIGN-ROOM screens — each one recurs ~8 times in 32
reviews. Size clearance alone is nowhere near sufficient, which
is the single most instructive number in the backtest.

Our four candidates are already screened through those gates in
the MIEU build, so the contaminated band does not price THEIR
risk. What survives as the gate haircut is the two pieces of
MSCI discretion nothing public can model:

    count flex (§2.3.3)      0.85     the member count can flex,
    ATVR unobservable        0.85     liquidity screens run on
                                      MSCI's own data

    P_gates = 0.85 x 0.85 = 0.7225

both registered before the announcement in the call file. The
float haircut from the old model is DELIBERATELY DROPPED here:
float error now lives inside the Monte Carlo with a measured
distribution, and keeping the flat 0.90 as well would count the
same risk twice. Same for the blind-band haircut — the price
window closed 31 Jul and the data reaches 31 Jul, so there is
nothing blind left; the price-date draw carries what remains.

────────────────────────────────────────────────────────────────
WHAT THE ANSWER LOOKS LIKE, AND HOW TO READ IT

The three carried names come out ~0.72 — their P_size is ~1.0
(no plausible input error bridges a 2.5-4.8x clearance), so ALL
their residual risk is MSCI discretion. Phison separates: its
1.55x sits close enough to the 1.5x bar that input error alone
fails it in a material fraction of draws, before any discretion.

That is the behaviour the old model could not produce, and it is
the point: the probability now RESPONDS to the same evidence the
size chart shows.

HONEST LIMITS. The FIF is taken as computed — its error exists
but is measured on too few names to draw from; the empirical
bands carry Wilson intervals wide enough to drive a truck
through; and none of this prices an off-cycle corporate action
between now and the effective date. With MSCI's licensed files, lens 1
collapses to near-certainty and the whole question reduces to
discretion — which is what "institutional data access" buys.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import pathlib
import random

ROOT = pathlib.Path(__file__).resolve().parents[1]
CALL = ROOT / "data" / "aug26_tw_call_v2.json"
SCN = ROOT / "data" / "aug26_scenarios.json"
FIF = ROOT / "data" / "tw_fif_aligned_jul31.json"
BT = ROOT / "data" / "backtest_taiwan.json"
OUT = ROOT / "data" / "tw_add_probability.json"
DOC = ROOT / "docs" / "ADD_PROBABILITY.md"

DRAWS = 20_000
SEED = 20260812          # the announcement date; fixed for replay
CUTOFF_BAND = 0.05       # the site's standing +-5%
ADD_BAR_X = 1.5          # GIMI: addition bar = 1.5x cutoff
FLOAT_BAR_X = 0.5        # GIMI §2.3.6.1: min float = 0.5x cutoff
PRICE_WINDOW_DAYS = 10   # MSCI picks one of ten sessions


def _fif_error():
    """Mean and sd of (our FIF / MSCI's implied FIF - 1), from
    the ten-name aligned comparison. The BIAS is kept: our floats
    run ~4% low against MSCI's, and a model that centres the
    error at zero would quietly flatter every float verdict."""
    d = json.loads(FIF.read_text(encoding="utf-8"))
    errs = [r["yahoo"] / r["implied"] - 1 for r in d["rows"]
            if r.get("yahoo") and r.get("implied")]
    n = len(errs)
    mu = sum(errs) / n
    sd = math.sqrt(sum((e - mu) ** 2 for e in errs) / n)
    return {"n": n, "mean": round(mu, 4), "sd": round(sd, 4),
            "source": FIF.name}


def _wilson(k, n, z=1.96):
    if not n:
        return (0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(max(0, mid - half), 3), round(min(1, mid + half), 3))


def _empirical_bands():
    """Per-band precision from the 32-review sweep, by
    differencing adjacent thresholds. Kept as EVIDENCE, not as an
    input — see the module docstring for why the top band is
    contaminated by structural gate-failures."""
    bt = json.loads(BT.read_text(encoding="utf-8"))
    sw = sorted(bt["add_sweep"], key=lambda r: r["x_ceiling"])
    bands = []
    for a, b in zip(sw, sw[1:]):
        hits = a["hits"] - b["hits"]
        other = a["flagged_other"] - b["flagged_other"]
        n = hits + other
        bands.append({
            "band_x_bar": [round(a["x_ceiling"] / ADD_BAR_X, 3),
                           round(b["x_ceiling"] / ADD_BAR_X, 3)],
            "added": hits, "not_added": other,
            "precision": round(hits / n, 3) if n else None,
            "wilson_95": _wilson(hits, n)})
    top = sw[-1]
    n = top["hits"] + top["flagged_other"]
    bands.append({
        "band_x_bar": [round(top["x_ceiling"] / ADD_BAR_X, 3), None],
        "added": top["hits"], "not_added": top["flagged_other"],
        "precision": round(top["hits"] / n, 3) if n else None,
        "wilson_95": _wilson(top["hits"], n),
        "contaminated": "recurring names failing float/foreign "
                        "gates sit here every review; size "
                        "clearance alone is not sufficient"})
    return bands


def p_size(row, prevol, rng):
    """Monte Carlo share of draws where the TRUE inputs clear
    both bars. The rule stays sharp inside each draw. Two dice
    only (c-365): the FIF is taken as computed — see the module
    docstring for why the n=10 error study is not drawn from."""
    full = row["full_cap_usd_b"]
    fif = row["fif"]
    ok = 0
    for _ in range(DRAWS):
        cut = 7.22 * (1 + rng.uniform(-CUTOFF_BAND, CUTOFF_BAND))
        d = rng.randrange(PRICE_WINDOW_DAYS)
        px_shock = (rng.gauss(0, prevol * math.sqrt(d))
                    if d else 0.0)
        cap = full * (1 + px_shock)
        if (cap >= ADD_BAR_X * cut
                and cap * fif >= FLOAT_BAR_X * cut):
            ok += 1
    return ok / DRAWS


DEL_FLOOR_X = 2 / 3      # GIMI: deletion floor = 2/3 x cutoff
QUOTES = ROOT / "data" / "tw_history" / "quotes.json"


def _daily_vol(code, n=60):
    """Realised daily vol from the quotes harvest, for names the
    scenarios file does not carry (the deletion side). Returns
    (vol, asof) or (None, None) if the name is not covered."""
    import math
    if not QUOTES.exists():
        return None, None
    q = json.loads(QUOTES.read_text(encoding="utf-8"))
    days = sorted(q)
    px = [(d, q[d][code][2]) for d in days
          if code in q[d] and q[d][code][2]]
    if len(px) < n // 2:
        return None, None
    rets = [math.log(b[1] / a[1]) for a, b in zip(px, px[1:])
            if a[1] and b[1]][-n:]
    mu = sum(rets) / len(rets)
    sd = math.sqrt(sum((r - mu) ** 2 for r in rets) / len(rets))
    return sd, px[-1][0]


def p_del_size(cap, vol, rng):
    """Monte Carlo share of draws where the TRUE cap sits BELOW
    the deletion floor — the mirror of p_size, with one
    difference: the deletion floor tests FULL market cap only, so
    the FIF error does not enter."""
    ok = 0
    for _ in range(DRAWS):
        cut = 7.22 * (1 + rng.uniform(-CUTOFF_BAND, CUTOFF_BAND))
        d = rng.randrange(PRICE_WINDOW_DAYS)
        px_shock = rng.gauss(0, vol * math.sqrt(d)) if d else 0.0
        if cap * (1 + px_shock) < DEL_FLOOR_X * cut:
            ok += 1
    return ok / DRAWS


def conversion_curve(vol, fif):
    """P_size swept over hypothetical clearance multiples — the
    picture of how distance from the bar converts to probability
    (c-367, Bill asked to SEE the conversion). The rule is sharp
    at 1.5x; the cutoff band and the price-date draw blur it
    into an S-curve, and the curve IS that blur.

    Drawn at one representative vol and FIF (the candidates'
    medians) — each actual name's dot is its own full draw, so a
    name with unusual vol sits a little off the curve, which is
    itself informative. OWN RNG, seeded: adding the curve must
    not shift the registered per-name numbers by consuming their
    stream."""
    rng = random.Random(SEED ^ 0xC0FFEE)
    pts = []
    x = 0.80
    while x <= 5.001:
        row = {"full_cap_usd_b": 7.22 * x, "fif": fif}
        pts.append({"x": round(x, 2),
                    "p": round(p_size(row, vol, rng), 4)})
        x += 0.05
    return pts


def del_conversion_curve(vol):
    """The deletion mirror of `conversion_curve` (c-369, Bill):
    P(delete) swept over hypothetical distances from the floor.
    x is full cap ÷ the deletion floor (2/3 x cutoff); at
    exactly 1.0x the two symmetric dice make it a coin toss, by
    the same construction that puts the addition curve at 50% on
    its bar. Drawn at the border member's own vol — there is one
    dot, so there is no median to prefer. Own seeded rng."""
    rng = random.Random(SEED ^ 0xDE1E7E)
    floor = DEL_FLOOR_X * 7.22
    pts = []
    x = 0.70
    while x <= 1.601:
        pts.append({"x": round(x, 2),
                    "p": round(p_del_size(x * floor, vol, rng),
                               4)})
        x += 0.02
    return pts


def border_deletions(rng):
    """P(delete) for members inside the floor's +5% band (c-359).

    The scan carries them with verdict "held"; the registered
    call file, struck before c-358 put them on the table, does
    not price them. Same construction as the addition side —
    P_size by Monte Carlo x the registered discretion haircuts —
    and the same reading: the number responds to distance, so a
    member 2.7% over the floor prices near a coin-toss with the
    band while one 15% over would price near zero."""
    sys_path = str(ROOT / "scripts")
    import sys
    if sys_path not in sys.path:
        sys.path.insert(0, sys_path)
    import walkthrough_story as W
    s = W.story("Taiwan", "Aug26")
    k = s["keys"]
    out = []
    for r in (s.get("scan") or {}).get("deletes", []):
        cap = r.get("cap_usd_b")
        if cap is None or not (
                k["floor"] <= cap < k["floor"] * 1.05):
            continue
        vol, asof = _daily_vol(str(r["code"]))
        vol_src = f"quotes.json 60d to {asof}" if vol else             "market-typical 5% (name not in quotes harvest)"
        ps = p_del_size(cap, vol or 0.05, rng)
        out.append({
            "code": str(r["code"]),
            "name": (r.get("name") or "").title(),
            "full_cap_usd_b": cap,
            "x_floor": round(cap / k["floor"], 4),
            "vol_daily": round(vol or 0.05, 4),
            "vol_source": vol_src,
            "p_size_mc": round(ps, 4),
            "p_delete": round(ps, 4)})
    return out


def main():
    for p in (CALL, SCN, FIF, BT):
        if not p.exists():
            raise SystemExit(f"missing {p.name}")
    call = json.loads(CALL.read_text(encoding="utf-8"))
    scn = json.loads(SCN.read_text(encoding="utf-8"))
    # c-365, Bill: the FIF die comes OUT of the draw. The study
    # is still computed and recorded — it is the evidence for the
    # decision — but n=10 is too thin to parameterize a
    # distribution, so the model no longer draws from it.
    fif_study = _fif_error()
    rng = random.Random(SEED)

    # c-360, Bill: P_gates COMES OUT OF THE PRODUCT. The model
    # now reports the measured thing and only the measured thing:
    # the probability that the rule fires given the measured
    # errors in its inputs. MSCI's discretion — the member count
    # can flex (§2.3.3), ATVR runs on data nobody outside sees —
    # is real, but multiplying by 0.85 x 0.85 priced it with two
    # judgement constants dressed as data. It is now carried as a
    # NAMED UNPRICED RISK: stated wherever the probability is
    # shown, multiplied nowhere. A reader who wants to haircut
    # for it can; the model no longer does it for them with fake
    # precision.
    hc = call["registered_haircuts"]
    unpriced = {
        "what": "MSCI discretion is NOT in these numbers",
        "count_flex": "the member count can flex (§2.3.3)",
        "atvr": "ATVR liquidity screens run on MSCI's own data",
        "was": f"previously priced as "
               f"{hc['count_flex']} x {hc['atvr_not_evaluated']} "
               f"= {hc['count_flex'] * hc['atvr_not_evaluated']:.4f}, "
               f"removed at c-360 — two judgement constants "
               f"dressed as data"}

    names = []
    for r in call["calls"]:
        if r["action"] != "ADD":
            continue
        s = scn["names"][str(r["code"])]
        ps = p_size(r, s["prevol"], rng)
        names.append({
            "code": str(r["code"]),
            "name": s["name"],
            "carried": bool(s.get("carried")),
            "x_cutoff": r["x_cutoff"],
            "full_cap_usd_b": r["full_cap_usd_b"],
            "fif": r["fif"],
            "float_cap_usd_b": r["float_cap_usd_b"],
            "prevol_daily": round(s["prevol"], 4),
            "p_size_mc": round(ps, 4),
            "p_add": round(ps, 4),
            "p_registered": r["prob"],
        })

    dels = border_deletions(rng)

    vols = sorted(r["prevol_daily"] for r in names)
    fifs = sorted(r["fif"] for r in names)
    med_vol = vols[len(vols) // 2]
    med_fif = fifs[len(fifs) // 2]
    curve = {"vol_daily": med_vol, "fif": med_fif,
             "note": "curve at the candidates' median vol and "
                     "FIF; each name's dot is its own full "
                     "draw, so unusual vol sits slightly off "
                     "the curve",
             "points": conversion_curve(med_vol, med_fif)}
    del_curve = None
    if dels:
        del_curve = {
            "vol_daily": dels[0]["vol_daily"],
            "floor_usd_b": round(DEL_FLOOR_X * 7.22, 4),
            "note": "drawn at the border member's own vol; x is "
                    "full cap over the deletion floor",
            "points": del_conversion_curve(dels[0]["vol_daily"])}

    o = {"_what": "P(add) = the Monte Carlo probability that "
                  "the rule fires given the measured errors in "
                  "its inputs; MSCI discretion is a named "
                  "UNPRICED risk, not a multiplier",
         "generated": dt.datetime.now().isoformat(timespec="seconds"),
         "method": {
             "draws": DRAWS, "seed": SEED,
             "cutoff_usd_b": call["cutoff_usd_b"],
             "cutoff_band": CUTOFF_BAND,
             "addition_bar_x": ADD_BAR_X,
             "float_bar_x": FLOAT_BAR_X,
             "price_window_days": PRICE_WINDOW_DAYS,
             "fif_treatment": {
                 "drawn": False,
                 "reason": "removed at c-365 — the error study "
                           "has n=10 datapoints, too thin to "
                           "parameterize a distribution; the FIF "
                           "is taken as computed, and float-"
                           "stack error is generalized by the "
                           "±5% cutoff band, which is struck on "
                           "that same stack",
                 "study_kept_as_evidence": fif_study},
             "unpriced_discretion": unpriced},
         "empirical_bands": _empirical_bands(),
         "names": names,
         "border_deletions": dels,
         "conversion_curve": curve,
         "del_conversion_curve": del_curve,
         "reading": [
             "The three carried names separate from Phison "
             "because P_size responds to clearance distance — "
             "the thing the flat zone probability ignored.",
             "For the carried names essentially all residual "
             "risk is MSCI discretion, which no public data "
             "models. That is what institutional access buys "
             "down.",
         ]}
    OUT.write_text(json.dumps(o, indent=1), encoding="utf-8")

    d = ["# P(Addition), From Evidence", "",
         f"Generated {o['generated']} by "
         "`scripts/tw_add_probability.py` — nothing typed.", "",
         "## Model", "",
         "```", "P(add) = P_size   (discretion NOT priced)",
         "```", "",
         "`P_size`: 20,000 Monte Carlo draws over the two "
         "inputs unknowable before the announcement — the "
         "cutoff (±5%, the site's standing band on an estimated "
         "float stack) and MSCI's one-of-ten price dates, "
         "scaled by each name's realised daily vol. The rule "
         "stays sharp in every draw; only inputs move — the "
         "Russell-literature fuzzy-threshold method.", "",
         "**Free float is taken as computed** (c-365): the FIF "
         "error study against MSCI's implied FIFs "
         f"(n={fif_study['n']}) is too thin to parameterize a "
         "distribution, so it is recorded as evidence and not "
         "drawn from. Float-stack error is generalized by the "
         "cutoff band, which is struck on that same stack.", "",
         "**Not priced:** MSCI discretion — the member count "
         "can flex (§2.3.3) and ATVR runs on MSCI's own data. "
         "Stated wherever the probability is shown, multiplied "
         "nowhere.", "",
         "| Name | x cutoff | **P(add)** | old flat |",
         "| --- | ---: | ---: | ---: |"]
    for r in names:
        d.append(f"| {r['name'][:24]} ({r['code']}) | "
                 f"{r['x_cutoff']:.2f}x | **{r['p_add']:.0%}** | "
                 f"{r['p_registered']:.0%} |")
    d += ["", "## The backtest's warning", "",
          "Per-band precision across 32 reviews (cap as a "
          "multiple of the addition bar):", "",
          "| Band | added | not | precision | 95% CI |",
          "| --- | ---: | ---: | ---: | --- |"]
    for b in o["empirical_bands"]:
        lo, hi = b["band_x_bar"]
        lab = f"{lo}-{hi}x" if hi else f">{lo}x"
        d.append(f"| {lab} | {b['added']} | {b['not_added']} | "
                 f"{b['precision']} | {b['wilson_95']} |")
    d += ["",
          "The top band reads 5% because a handful of very large "
          "names fail the float and foreign-room gates at every "
          "review — size clearance alone is nowhere near "
          "sufficient. Our candidates are screened through those "
          "gates before any probability is struck.", ""]
    DOC.write_text("\n".join(d), encoding="utf-8")

    print(f"two dice: cutoff ±{CUTOFF_BAND:.0%}, price date "
          f"1-of-{PRICE_WINDOW_DAYS} x vol   (FIF as computed; "
          f"n={fif_study['n']} study recorded, not drawn; "
          f"discretion unpriced)")
    for r in names:
        print(f"{r['code']} {r['name'][:22]:24} "
              f"x={r['x_cutoff']:4.2f}  P_size={r['p_size_mc']:6.1%}  "
              f"P(add)={r['p_add']:6.1%}  (old {r['p_registered']:.1%})")
    for r in dels:
        print(f"{r['code']} {r['name'][:22]:24} "
              f"floor x={r['x_floor']:4.2f}  "
              f"P_size={r['p_size_mc']:6.1%}  "
              f"P(delete)={r['p_delete']:6.1%}")
    print(f"wrote {OUT.name}, {DOC.name}")


if __name__ == "__main__":
    main()
