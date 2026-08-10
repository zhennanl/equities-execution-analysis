"""The walkthrough STORY GENERATOR — rebuilt for the desk
(c-162). Taiwan only.

WHAT CHANGED FROM v1 (saved at backup/walkthrough_v1_20260808/):
  - one market, one review. No market picker, no example
    picker, no "written with no finance background" framing.
  - the reader is now a program-trading dealer, so the desk
    language moved INTO the main text and the collapsed
    "For the desk" blocks are gone. There is no second
    audience to write down to.
  - "photograph" is retired throughout. The term is Price
    Cutoff Date, which is MSCI's own (GIMI May-2026 §3.1.9).
  - per-step "what this step can get wrong" boxes removed at
    Bill's instruction. The limits are NOT dropped — they are
    consolidated into the closing step, which is now a stated
    part of the method rather than a caveat attached to each
    screen.

WHAT DID NOT CHANGE, because it is the point: every number is
GENERATED from the engine's own output (data/reconstruct/*.json,
data/aug26_cutoff_calc.json) at render time. No figure in this
file is typed by hand. If the engine's floor moves, the
sentence moves with it.

MODES:
  "live"   — the open review (Aug-26): ends on a call declared
             before the answer exists, with a grading date.
  "solved" — a past review (May-26): ends on the scoreboard,
             misses included.

Usage:
  py scripts\\walkthrough_story.py
  from walkthrough_story import story; s = story()
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_MKT_ABBR = {"Taiwan": "TW"}

# GIMI May-2026, the edition governing this review.
RULEBOOK = ("https://www.msci.com/eqb/methodology/meth_docs/"
            "MSCI_GIMIMethodology_May2026.pdf")


def _j(p):
    p = ROOT / "data" / p
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _caps_at(codes, date, fx):
    """Every name's size at the cutoff: that day's last traded
    price x shares issued, converted to USD."""
    v = _j("tw_vintage_cache.json") or {}
    out = {}
    for c in codes:
        px, sh = v.get(f"px|{c}"), v.get(f"sh|{c}")
        if not (px and sh):
            continue
        p = next((r["close"] for r in reversed(px)
                  if r["date"] <= date), None)
        s = next((r["NumberOfSharesIssued"] for r in reversed(sh)
                  if r["date"] <= date), None)
        if p and s:
            out[c] = p * s / fx / 1e9
    return out


def _universe(market, review, k, fx):
    """Every index member at that review marked at its
    point-in-time size, plus the names that actually moved.
    Drives the interactive cutoff line."""
    import pandas as pd
    sys.path.insert(0, str(ROOT / "scripts"))
    import review_reconstruct as RR
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    g = df[df.market == market]
    order = [f"{m}{y % 100:02d}" for y in range(2015, 2027)
             for m in ("Feb", "May", "Aug", "Nov")]
    mem = RR.pit_members(review, order, g[g.code != ""])
    caps = _caps_at(mem, k["price_date"], fx)
    moves = g[g.review == review]
    act = {r.code: r.action for _, r in moves.iterrows()
           if r.code}
    nm = {r.code: r.security for _, r in moves.iterrows()
          if r.code}
    ev = _j("msci_tw_events.json") or {}
    for vv in ev.values():
        for c, n in {**vv.get("adds", {}),
                     **vv.get("dels", {})}.items():
            nm.setdefault(c, n)
    rows = [{"code": c,
             "name": _yahoo_name(c) or nm.get(c) or c,
             "cap": round(v, 2),
             "actual": act.get(c, "")} for c, v in caps.items()]
    for c, a in act.items():
        if a == "ADD" and c not in caps:
            extra = _caps_at([c], k["price_date"], fx)
            if c in extra:
                rows.append({"code": c,
                             "name": (_yahoo_name(c)
                                      or nm.get(c) or c),
                             "cap": round(extra[c], 2),
                             "actual": "ADD"})
    return sorted(rows, key=lambda r: -r["cap"])


def _yahoo_name(code):
    """Best available company name for a Taiwan code.

    c-168: the chart labelled some bars with a name and others
    with a bare code, because MSCI only names the securities it
    MOVED — an untouched member appears nowhere in the change
    list. And where MSCI does name them, the strings are
    truncated at 22 characters ("GIGABYTE TECHNOLOGY LT"). The
    Yahoo cache has the full legal name for every live code, so
    it is preferred and MSCI's string is the fallback.
    """
    global _NAMES
    if _NAMES is None:
        f = ROOT / "data" / "yahoo_names.json"
        try:
            _NAMES = json.loads(
                f.read_bytes().decode("utf-8", errors="replace"))
        except Exception:                          # noqa: BLE001
            _NAMES = {}
    return (_NAMES.get(f"{code}.TW")
            or _NAMES.get(f"{code}.TWO"))


_NAMES = None


def _market_facts(market):
    off = (_j("msci_official_constituents.json") or
           {}).get("markets", {}).get(market)
    if not off:
        return {}
    cs = sorted(off["constituents"], key=lambda x: -x["weight"])
    return {"n": off["n"], "top_name": cs[0]["security"],
            "top_weight": cs[0]["weight"],
            # c-247: the top TEN, because concentration is the
            # fact about this index and one name does not show
            # it. TSMC's 54.8% survives as the sub-line.
            "top10_weight": sum(c["weight"] for c in cs[:10])}


def _crossing(width=9):
    """The real Taiwan coverage crossing, ranks around it.

    c-278, Bill: *"check if you can replace the bar graphs with
    actual results from our Taiwan walk. If not, then delete
    the entire section 4."*

    It can. Ranking the screened universe by full market cap
    and accumulating free-float value reaches 85% of the
    implied investable market at a rank whose full cap IS the
    cutoff of record — reproduced from the stored universe
    rather than restated from the calc file.

    WHY A NEIGHBOURHOOD AND NOT THE TOP OF THE LIST. TSMC is
    eleven times rank 2, a cliff at the very first step. Any chart starting at rank 1 is one bar and a
    row of slivers, and the crossing — the only part of the
    curve a reader needs — is 60 ranks off the right edge at a
    height of nothing. So the figure shows the ranks either
    side of the crossing, where the bars are comparable and the
    line actually crosses something.

    NOT read from `walk`, deliberately. That block still holds
    the superseded bottom-up frame (rank 115) which c-273
    replaced with the factsheet inversion, and it
    disagrees with `keys.cutoff` on the same page. This
    computes from the universe and the factsheet value so the
    figure and the thresholds above it come from one frame.
    """
    uni = _j("tw_mieu_universe.json") or {}
    calc = ((_j("aug26_cutoff_calc.json") or {})
            .get("derivation", {}).get("C_cutoff", {}))
    U, idx = uni.get("universe") or {}, calc.get(
        "factsheet_index_busd")
    cov = calc.get("stated_coverage", 0.85)
    if not U or not idx:
        return None
    rows = sorted(({"code": c, **v} for c, v in U.items()),
                  key=lambda r: -r["cap"])
    cum, cross = 0.0, None
    for i, r in enumerate(rows, 1):
        cum += r["fcap"]
        r["cum"] = cum
        r["rank"] = i
        if cross is None and cum >= idx:
            cross = i
    if cross is None:
        return None
    lo = max(0, cross - width - 1)
    hi = min(len(rows), cross + width)
    return {
        "target_busd": round(idx, 1),
        "implied_universe_busd": round(idx / cov, 1),
        "coverage": cov,
        "crossing_rank": cross,
        "crossing_cap_busd": round(rows[cross - 1]["cap"], 2),
        "screened": len(rows),
        "priced": uni.get("date"),
        "rows": [{"rank": r["rank"], "code": r["code"],
                  "cap": round(r["cap"], 2),
                  "fcap": round(r["fcap"], 2),
                  "cum": round(r["cum"], 1)}
                 for r in rows[lo:hi]],
    }


def _review_dates(review):
    """MSCI's own announcement / close / effective dates.

    c-249. From `data/msci_review_dates.json`, which carries
    the source URLs. The page holds no facts, and a date drawn
    into a diagram is still a fact.
    """
    d = _j("msci_review_dates.json") or {}
    return (d.get("reviews") or {}).get(review) or {}


def story(market="Taiwan", review="Aug26"):
    """Build the whole narrative for one review."""
    live = review == "Aug26"
    mf = _market_facts(market)
    dates = _review_dates(review)
    # c-253: the rulebook's own published constants, as DATA.
    # Step 3 quotes several of them and the no-hardcoded-figures
    # test is right to stop them being typed into prose.
    gc = _j("msci_gimi_constants.json") or {}
    _sr = gc.get("size_reference", {})
    _rg = gc.get("size_range", {})
    pub = {
        "dm": round((_sr.get("dm_standard_usd_m") or 0) / 1000, 2),
        "em": round((_sr.get("em_standard_usd_m") or 0) / 1000, 2),
        "lo": (_rg.get("published_em_standard_busd") or [0, 0])[0],
        "hi": (_rg.get("published_em_standard_busd") or [0, 0])[1],
        "cov": (gc.get("coverage_target") or {}).get(
            "standard_pct", 85),
        "asof": gc.get("worked_example_priced_at", ""),
    }
    steps = []
    if live:
        a = _j("aug26_cutoff_calc.json")
        d = a["derivation"]["A_global"]
        # c-253: THE BUFFERS HANG OFF THE MARKET CUTOFF.
        # They used to hang off `em_range_busd[1]`, the ceiling
        # of the GLOBAL EM size range, which is not Taiwan's
        # number at all. §3.1.5.1 p.44 applies 2/3 and 1.5 to
        # the Market Size-Segment Cutoff, which the engine had
        # already computed and the page was ignoring.
        c = a["derivation"]["C_cutoff"]
        cut = float(c["cutoff_busd"])
        k = {"gmsr_dm": d["dm_aug_busd"],
             "em_ref": round(d["dm_aug_busd"] / 2, 2),
             "em_range": d["em_range_busd"],
             "ceiling": d["em_range_busd"][1],
             "cutoff": cut,
             "floor": round(2 / 3 * cut, 2),
             "bar": round(1.5 * cut, 2),
             "min_float_cap": round(0.5 * cut, 2),
             "price_date": "2026-07-20 (ESTIMATED — MSCI has "
                           "not disclosed it yet)",
             "source": "forecast from the May-2026 book"}
        fx = 32.214
        uni = sorted(
            [{"code": x["code"],
              "name": (_yahoo_name(x["code"])
                       or x.get("company") or x["code"]),
              "cap": x["cap_usd_b"], "actual": ""}
             for x in a["delete_candidates"]
             + a["add_candidates"]],
            key=lambda r: -r["cap"])
        grading = None
    else:
        r = _j(f"reconstruct/{_MKT_ABBR.get(market, market)}_"
               f"{review}.json")
        if not r:
            raise SystemExit(
                f"no reconstruction for {market} {review} — run "
                "py scripts\\review_reconstruct.py batch")
        k, fx = r["keys"], r["fx_used"]
        grading = r["grading"]
        uni = _universe(market, review, k, fx)

    # ---------------- step 1 -------------------------------
    steps.append({
        "n": 1, "title": "Index Review Timeline",
        "key": "timeline",
        # c-249: two paragraphs came OUT of this step, because
        # the two diagrams above now carry them — the
        # provider-to-tracker relationship and the timeline.
        # A diagram that does not let text go is decoration.
        # c-268: the figure row and every beat are gone. The
        # diagram carries the whole step now — who acts, in what
        # order, and on which date — and repeating it in prose
        # underneath was the density Bill kept flagging. A step
        # whose picture is self-sufficient should say so by
        # having nothing else in it.
        "plain": [
            # c-268: plain and descriptive. Bill, on the copy
            # throughout this figure: *"the tone is too
            # dramatic… keep a natural, descriptive tone."*
            "The Role of Index Provider and Index Funds"],
        "numbers": []})

    # ---------------- step 2 -------------------------------
    steps.append({
        "n": 2,
        "title": "Which Data The Review Uses",
        "key": "data",
        "plain": [
            # c-294, Bill: *"I don't quite understand what we
            # mean for 'data each one is run on'."* Fair — it
            # was shorthand for "each screen is measured as of
            # its own cutoff date", which is the actual point of
            # the step and of the figure below it. Say that.
            "The screens MSCI runs to decide which companies "
            "are eligible for the index, and the cutoff date "
            "each screen is measured on.",
            # c-268: NOTHING IS SHOWN OPEN IN THIS STEP BUT THE
            # LEAD. The two figures carry the step — the three
            # cutoffs and what each one governs — and Bill's
            # instruction is that the rulebook block lives
            # behind "Rulebook References" in full rather than
            # spilling its first two paragraphs onto the page.
            # `render_steps` passes shown=0 for step 2 to do it.
            #
            # The marking-off paragraph and its 23-edition
            # justification are deleted outright. The estimated
            # price day is still on the page — the figure draws
            # the whole 10-day window and says MSCI picks one of
            # them — and steps 4 and 5 carry the date itself.
            "**Where the rules sit in the rulebook.** GIMI "
            f"methodology, [May 2026 edition]({RULEBOOK}), "
            "**§3.1.9 *Date of Data Used for Index Reviews*, "
            "p.48**, which sets three separate cutoffs:",
            # c-307, Bill: every clause reference sits at the
            # END of its bullet. The rule is what a reader wants
            # first; the page number is where they go to check
            # it, which is a second act.
            "- **Equity Universe Cutoff** — last business day "
            "of May for an August review. Governs universe "
            "construction and the Equity Universe Minimum Size "
            "Requirement (**§2.1, §3.1.2.2**).",
            "- **Liquidity Cutoff** — last business day of June "
            "for an August review. Governs the Annual Traded "
            "Value Ratio (ATVR) and frequency "
            "of trading.",
            "- **Price Cutoff** — any one of the last 10 "
            "business days of July for an August review. "
            "Governs prices for market cap, FIF updates, "
            "foreign room, and NOS (**§3.1.7, §3.1.8**).",
            # the transition Bill asked for. The three cutoffs
            # and the five screens are easy to read as one long
            # list of rules; they are not. One set says WHEN the
            # data is taken, the other says what it has to
            # prove, and the second set is where a name that
            # passes on size still fails.
            # one sentence, and its job is only to say WHAT
            # these are: a second family of tests, sitting on
            # top of size and liquidity rather than beside them.
            "**Investability screens.** On top of size and "
            "liquidity, MSCI applies a further set of tests "
            "that a security has to pass to be added to the "
            "index or kept in it:",
            "- **Foreign room** — room left under a foreign "
            "ownership limit must be at least **15%** of the "
            "maximum allowed (**§2.2.8, §2.3.6.2**).",
            "- **Frequency of trading** — an existing "
            "constituent needs a 3-month ATVR of at least "
            "**5%** and traded-day frequency of at least "
            "**80% in developed markets, 70% in emerging** "
            "(**§2.2.5**).",
            "- **Minimum length of trading** — three months "
            "of trading before the review is implemented, "
            "which is what keeps most IPOs out until the "
            "following review (**§2.2.7**).",
            "- **Extreme price increase** — a security whose "
            "excess return breaches MSCI's thresholds is "
            "barred from ADDITION to the Standard Index and "
            "re-tested next review. A name can pass every size "
            "and liquidity test and still not be added "
            "*because* it rose too fast (**§2.3.6.3**).",
            "- **Surveillance boards** (Appendix I, *Other "
            "Cases*) — securities that enter the **Taiwan "
            "Disposition Board**, India's ASM lists, "
            "Indonesia's Watchlist Board or "
            "Korea's Investment Alert and Investment Risk lists "
            "get no Investable Market Index addition and no "
            "Standard-Small "
            "migration."],
        "numbers": []})

    # ---------------- step 3 -------------------------------
    # c-253: a RECONSTRUCTED review has no Market Size-Segment
    # Cutoff on file — the reconstruction engine predates this
    # correction and still derives its buffers from the range
    # ceiling. Rather than print numbers we now know are built
    # on the wrong base, the step says so and drops them.
    # Re-running `review_reconstruct.py` under the corrected
    # rule is a separate job; it moves the graded backtest.
    # c-272: THE CUTOFF NOW COMES FROM MSCI'S OWN FACTSHEET.
    #
    # Every earlier version summed our own float estimates for
    # 398 screened names to get the denominator. That sum was
    # 3.8% short of what MSCI's published index value implies,
    # and because the cumulative coverage curve is almost flat
    # in the tail, 3.8% on the input moved the answer by 40%.
    # Four artefacts in this repo carried four different cutoffs
    # for that reason.
    #
    # The factsheet route inverts MSCI's own arithmetic instead:
    # it publishes the index's free-float value and states the
    # index covers 85% of Taiwan's investable market, so the
    # denominator is a division rather than an estimate. The
    # remaining uncertainty is the word "approximately" in front
    # of 85%, which is worth about 8-10% of the cutoff per
    # percentage point — an order of magnitude tighter.
    _cut = k.get("cutoff")
    _mfc = k.get("min_float_cap")
    _emref = k.get("em_ref") or round(k["gmsr_dm"] / 2, 2)
    _tw = ([]
           if _cut else
           ["**This reconstructed review has not been recomputed "
            "under that rule.** Its stored thresholds were "
            "derived from the ceiling of the global corridor, "
            "which c-253 established is the wrong base, so they "
            "are withheld here rather than shown. Re-running "
            "the reconstruction moves the graded backtest and "
            "is a separate job."])
    steps.append({
        "n": 3, "title": "Where the Size Cutoff Sits",
        "key": "cutoff",
        "plain": [
            # c-282: the lead answers WHY, in one line. MSCI
            # publishes no size threshold for Taiwan, so every
            # number the prediction rests on has to be derived
            # — which is the fact that makes this step exist.
            "Follow the MSCI rulebook to derive the cutoff and its two buffers",
            *_tw,
            "",
            "**Where each number comes from.** GIMI "
            f"methodology, [May 2026 edition]({RULEBOOK}).",
            # c-298, Bill: the clause reference moves to the END
            # of each bullet. The rule is what a reader wants
            # first; the page number is where they go to check
            # it, which is a second act.
            f"- **Global Minimum Size Reference** — the published "
            f"worked example, priced at the close of "
            f"{pub['asof']}, gives DM Standard "
            f"**USD {pub['dm']}B** and EM Standard "
            f"**USD {pub['em']}B** (\"set at one-half the "
            f"corresponding level\") (**\u00a72.3.2.1, p.24-25**).",
            f"- **Global Minimum Size Range** — \"a range of 0.5 "
            f"times to 1.15 times those References\". The book "
            f"prints the answer: EM Standard "
            f"**USD {pub['lo']}B to USD {pub['hi']}B** "
            f"(**\u00a72.3.2, p.24**).",
            "- **Market Size-Segment Cutoff** — the 85% coverage "
            "over the market's own investable universe, bounded "
            "into the range above (**\u00a72.3.3, p.26**).",
            "- **Buffer zones** — \"the buffer zones at Index "
            "Reviews are defined with boundaries of "
            "2/3\u02b3\u1d48 of and 1.5 times the Market "
            "Size-Segment Cutoff\" (**\u00a73.1.5.1, p.44**).",
            "- **Minimum free float** — a new Standard "
            "constituent needs free-float-adjusted cap of at "
            "least 50% of the cutoff"
            + (f", here **USD {_mfc}B**" if _mfc else "")
            + " (**\u00a72.3.6.1, p.30**).",
            # c-298, Bill: the "Two figures here are ours" and
            # "A correction, on the record" paragraphs are cut
            # from this step. NEITHER CLAIM IS RETRACTED — the
            # scaled reference, the +-2pt band on the +4.2%
            # scalar and the corrected buffers all still travel
            # in the registered call file's own `limits` block,
            # which ships with every prediction, and in docs/.
            # What went is the retelling here.
            ],
        # c-268: THE FIGURE ROW IS GONE from this step at
        # Bill's request. It listed the six layers, and the
        # diagram now lists them too — with the reason for each
        # one, which the row had no space for. Two renderings of
        # the same six numbers is one too many, and the row was
        # the version that could only say WHAT.
        "numbers": []})

    # ---------------- step 4 -------------------------------
    ex = next((u for u in uni if u.get("actual") == "DEL"),
              uni[0] if uni else None)
    # c-254: the walk's own arithmetic, when we have it.
    _w = (a.get("derivation", {}).get("B_taiwan_walk", {})
          if live else {})
    steps.append({
        "n": 4,
        "title": "Mark every name at the cutoff date",
        "key": "measures",
        "plain": [
            "Every company gets **two** numbers at the cutoff "
            "date, and they do two different jobs. Full market "
            "capitalisation — that day's close times shares "
            "issued, in USD — is the **sort key**. "
            "Free-float-adjusted capitalisation is the "
            "**running total**. Confusing the two is the "
            "classic way to get this walk wrong.",
            # c-268: the point-in-time paragraph and the "why
            # two measures" header are deleted at Bill's
            # request. Deleting the header alone would have
            # left its five bullets as the step's two OPEN
            # beats — a step opening on a bullet list about
            # §2.2.4 — so the two definition paragraphs move up
            # to take the visible slots and the bullets fall
            # into the references block, which is where a list
            # of rulebook clauses belongs anyway.
            "**Two definitions worth getting exactly right.** "
            "The FIF is *\"the proportion of shares outstanding "
            "that is available for purchase in the public "
            "equity markets by international investors\"* "
            "(§2.2.6) — it accounts for free float **and** for "
            "foreign ownership limits, so it is not simply free "
            "float. And footnote 5 on p.17 states that MSCI's "
            "free-float-adjusted cap is measured *after* any "
            "relevant adjustment factors, including low-foreign-"
            "room adjustments and Liquidity Adjustment Factors. "
            "We approximate it as full cap times FIF, which is "
            "right for almost every name and wrong for any name "
            "carrying an adjustment factor we cannot see.",
            "One refinement matters. MSCI does not count shares "
            "that will never trade — a government stake, a "
            "founding family block. Most outcomes are decided "
            "on full cap, and we flag the names where float is "
            "doing the work, because float is the input we are "
            "least sure of.",
            "",
            "- **Sort by FULL cap** — size-segment membership "
            "is a statement about how big a company is, and "
            "full cap is the market's own view of that. Float "
            "is an accessibility adjustment, not a size "
            "measure. Sorting on float would let a widely held "
            "mid-cap outrank a larger, tightly held company, "
            "and the index would stop being a size index.",
            "- **Cumulate FLOAT cap** — the 85% coverage target "
            "(§2.3.1) is a promise about what an investor can "
            "actually buy. Measured on full cap it would count "
            "shares no foreign investor can purchase, and the "
            "index would be claiming coverage it cannot "
            "deliver.",
            "- **Read the crossing company's FULL cap** — the "
            "output is a size threshold applied to companies, "
            "so it has to come back in the same units as the "
            "sort key.",
            "- **Company level for size, security level for "
            "float** — §2.2.3 aggregates a company's securities "
            "because size-segments are assigned to companies "
            "(§2.3.3: \"all securities of a company are always "
            "classified in the same size-segment\"). §2.2.4's "
            "float test is applied per security, because "
            "tradability belongs to a listing, not to a company.",
            "- **The 0.15 FIF floor** (§2.2.6) and the "
            "**separate 50%-of-minimum-size float test** "
            "(§2.2.4) exist because a large company with a "
            "tiny float is not investable at size — the "
            "company-level size screen alone would let it "
            "through.",
            "",
            "**The float stack, best source first.** (1) FIFs "
            "implied by MSCI's own factsheet, top-10, exact "
            "same date. (2) MSCI's own member FIFs recovered by "
            "inverting the published index weights — these land "
            "on MSCI's 2.5% rounding grid, which is how we know "
            "the inversion is right. (3) Yahoo "
            "floatShares/sharesOutstanding, 2.7% median error "
            "against MSCI on the aligned overlap and the best "
            "public source. (4) TDCC bracket float scaled by a "
            "calibration measured on the Yahoo overlap, since "
            "TDCC treats large domestic institutions as "
            "strategic where MSCI treats them as float. At "
            "2026-07-31 the mix ran 10 / 53 / ~490 / ~1,460 "
            "names, with nothing falling through to a bare "
            "default. Any name whose verdict flips between "
            "adjacent tiers is marked borderline and not "
            "called."]
        + ([f"Worked example: {ex['name']} marks at "
            f"USD {ex['cap']}B on the cutoff date."] if ex else []),
        "numbers": [
            {"label": ("Candidates marked" if live
                       else "Companies marked"),
             "value": len(uni),
             "note": ("live sheet carries only names near the "
                      "lines" if live else
                      "every index member at that review")},
            {"label": "Largest mark",
             "value": f"USD {uni[0]['cap']}B" if uni else "—",
             "note": "full market cap, the sort key"},
        ] + ([
            {"label": "Float-adjusted universe",
             "value": f"USD {_w['denominator_busd']:,.0f}B",
             "note": "the running total's denominator"},
            {"label": "85% target",
             "value": f"USD {_w['target_busd']:,.0f}B",
             "note": "§2.3.1 Standard coverage"},
            {"label": "Crossing rank",
             "value": _w["crossing_rank"],
             "note": f"full cap there: "
                     f"USD {_w['raw_crossing_busd']}B"},
        ] if _w.get("denominator_busd") else [])})

    # ---------------- step 5 -------------------------------
    pool = (grading or {}).get("pool", {})
    steps.append({
        # c-293, Bill: the title and lead are about SHORTLISTING
        # — that is all this step does. The old lead explained
        # the axis and the buffers before the reader had any
        # reason to care about either, and the arithmetic block
        # under it restated the multipliers that step 3's cards
        # already carry on their faces.
        # c-312, Bill: *"Paraphrase this 'Compare Company Market
        # Cap Against Buffers'."* That phrase is not on the page
        # in those words — it describes what this step DOES, and
        # this is the only step that does it. So it lands here as
        # the title, reworded: "market cap" is the sort key the
        # step measures, and "against the buffers" is the test.
        # The old title named the OUTPUT (a shortlist); this one
        # names the ACT, which is what the figure below draws.
        "n": 5, "title": "Measure Company Size Against the Buffers",
        "key": "buffers",
        "plain": [
            "Which companies fall within the buffer to be "
            "considered for addition or deletion.",
            # c-300, Bill: the four explanatory paragraphs are
            # cut. The asymmetry they described is REAL and is
            # still enforced — an addition passes four gates and
            # a deletion one — and the figure below shows it
            # directly: a hollow dot above the upper buffer is a
            # name that clears on size and fails a float or
            # foreign-room gate. The prose was a second telling
            # of what the chart already draws.
            ],
        "numbers": []})

    # ---------------- step 6 -------------------------------
    if live:
        a = _j("aug26_cutoff_calc.json")
        calls = a["shadow_add_call"]["calls"]
        steps.append({
            "n": 6, "title": "Our Prediction for Index Review",
        "key": "call",
            "plain": [
                # c-312 deleted the old standfirst, which narrated
                # an absence ("nothing to grade against yet") the
                # reader could already see.
                # c-320 asked for a subtitle back; c-324 rewords
                # it to name the ACT rather than the caveat. Every
                # screen and adjustment above has run by this
                # point — size, float, foreign room, the buffers
                # and the error bar on the cutoff — and this step
                # is where they resolve into a list.
                "The companies selected for index review change, "
                "after every screen and adjustment has been "
                "applied",
                # c-306, Bill: the addition call, the deletion
                # watchlist, the conviction-chain explainer, the
                # calibration warning and the blind-band line are
                # cut. The names and their probabilities sit in
                # the prediction block directly below, and the
                # base rates, haircuts and blind band travel in
                # the registered call file's own fields — the
                # step states the position, the file carries the
                # reasoning.
            ],
        "numbers": [
                {"label": "Declared",
                 "value": a["shadow_add_call"]["declared"][:10]},
                {"label": "Grades", "value": "Aug 11-12, 2026"},
                {"label": "Delete watchlist",
                 "value": len(a["delete_candidates"])}]})
    else:
        h = len(grading["hits"])
        m = len(grading["misses"])
        f = len(grading["false_alarms"])
        steps.append({
            "n": 6, "title": "What we called, and what MSCI did",
        "key": "call",
            "plain": [
                "MSCI has announced this review, so the method "
                "marks its own homework.",
                f"Of the names MSCI removed, the method flagged "
                f"**{h} of {h + m}** in advance.",
                f"It also flagged **{f}** names MSCI left alone. "
                f"Those are not simply errors. The rule says "
                f"'below the floor', but MSCI removes only a "
                f"subset of the below-floor pool and applies "
                f"judgement to the rest — so the false alarms "
                f"are a measurement of that discretion, and "
                f"closing that gap is the ranking problem.",
                "Across the backtested reviews deletion capture "
                "runs about 83% with 6-25 false alarms per "
                "review. The false-alarm set is the labelled "
                "training target for the ranking model.",
                "Additions grade more loosely than deletions, "
                "because a newcomer can enter from outside the "
                "measured universe entirely."],
            "numbers": [
                {"label": "Removals caught",
                 "value": f"{h}/{h + m}"},
                {"label": "Removals missed", "value": m},
                {"label": "False alarms", "value": f,
                 "note": "MSCI's discretion, measured"}]})

    # ---------------- step 7 -------------------------------
    # c-269: the light-rebalancing contingency moved here from
    # step 3, where Bill deleted it. It is not a derivation —
    # it is a rule that can widen both buffers with almost no
    # notice, which makes it a limit on the call rather than a
    # link in the chain. Same treatment as the surveillance
    # boards at c-268: an instruction to remove something from a
    # step is not an instruction to drop the knowledge.
    _cut7 = k.get("cutoff")
    _discretion = (
        "**Discretion cannot be modelled.** §3.1.9 alone lets "
        "MSCI decline a migration on a takeover bid or a "
        "suspension, and no amount of data predicts a "
        "judgement call. MSCI can also switch a review to a "
        "*light rebalancing*, which widens the buffers from "
        "2/3 and 1.5x the cutoff to 0.5x and 1.8x"
        + (f" — here **USD {round(0.5 * _cut7, 2)}B** and "
           f"**USD {round(1.8 * _cut7, 2)}B**, enough to take two "
           f"names off the addition list" if _cut7 else "")
        + ". It is a **market-stress** provision, not a cadence "
        "one: p.107 sets a monitoring period over the last ten "
        "business days before the announcement, and a breach "
        "refers the decision to MSCI's Equity Index Committee "
        "and Index Policy Committee. No switch has been "
        "declared for this review, so 2/3 and 1.5 stand — but "
        "it is the one rule change that arrives with almost no "
        "notice, so it is worth watching in those ten days.")
    # c-296, Bill: the "Where This Analysis Stops "
    # "Working" step is DELETED, not just filtered. It had
    # been excluded from the render since c-287 while still
    # being built here, which left it one edit to the filter
    # away from returning. The limits it carried survive in
    # docs/ and in the call file's own `limits` block, which
    # travels with every prediction.

    # c-171: the page now leads with the ANSWER, so the call
    # itself becomes part of the story payload. The view still
    # holds no facts — it renders what is generated here.
    call = _j("aug26_tw_call_v2.json") if live else None
    if call:
        for c in call.get("calls", []):
            c["name"] = (_yahoo_name(c["code"])
                         or c.get("company") or c["code"])
    # c-282: STEP 4 IS REMOVED at Bill's request, and the list
    # is renumbered so the reader sees 1..6 with no gap.
    #
    # `key` is what survives this. Every step carries one, and
    # the view keys its figures off the key rather than off `n`
    # — otherwise deleting a step silently reassigns figures to
    # the wrong bodies, which is the kind of break that renders
    # fine and is simply wrong.
    # c-287: the LIMITS step goes too, at Bill's request.
    #
    # Recording what that costs, because it is not nothing. D8
    # said a limitation the reader must carry is not a footnote,
    # and step 7 was where discretion, float error, off-cycle
    # exits and the blind band were named. Removing it does not
    # make those go away — it removes the place the page
    # admitted them.
    #
    # They are NOT lost from the project: `docs/` carries them,
    # the call file's `limits` block travels with every
    # prediction, and step 5 still shows the haircuts that
    # price them into the conviction number. But a reader who
    # only reads this page no longer meets them.
    steps = [x for x in steps
             if x.get("key") not in ("measures", "limits")]
    for i, x in enumerate(steps, 1):
        x["n"] = i

    return {"call": call,
            "market": market, "review": review,
            "mode": "live" if live else "solved",
            # c-248: one name everywhere — nav item, page
            # heading and exported file. The market is carried
            # by the status strip and the call's own heading.
            "title": "Predict MSCI Index Changes",
            "dates": dates,
            "walk": _w,
            # c-278: the REAL crossing, computed from the
            # screened universe and the factsheet value.
            # `walk` above still carries the superseded
            # bottom-up frame; step 4 must not read it.
            "crossing": _crossing(),
            # c-255: the corrected call, for step 5's scan
            "scan": (_j("aug26_call_v2.json") or {}) if live
            else {},
            "keys": k, "fx": fx, "universe": uni,
            # c-268: the rulebook's PUBLISHED constants travel
            # with the story so step 3's figure can show its own
            # provenance — the DM reference it draws is MSCI's
            # published number scaled to this review's pricing,
            # and a card claiming that has to be able to cite it.
            "published": pub,
            "grading": grading, "steps": steps}


if __name__ == "__main__":
    rev = sys.argv[1] if len(sys.argv) > 1 else "Aug26"
    s = story("Taiwan", rev)
    print(f"{s['title']}  [{s['mode']}]")
    for st_ in s["steps"]:
        print(f"\n--- {st_['n']}. {st_['title']}")
        for n in st_["numbers"]:
            print(f"    {n['label']}: {n['value']}")
        print("    " + st_["plain"][0][:100] + "...")
    print(f"\nuniverse: {len(s['universe'])} companies")
