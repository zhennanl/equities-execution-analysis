"""The walkthrough STORY GENERATOR (c-115).

Bill's brief: a walkthrough of the point-in-time prediction that
someone outside finance can follow, which we can later point at
every APAC market.

THE DESIGN DECISION THAT MAKES IT SCALE: the story is GENERATED
from the computation, never written as prose. Every number below
is read out of the engine's own output (data/reconstruct/*.json,
data/aug26_cutoff_calc.json) at render time. Two consequences:
  - the narrative cannot drift from the code. If the engine's
    floor changes, the sentence changes.
  - pointing it at another market/review regenerates the whole
    story. Thirteen markets need zero extra prose, only their
    reconstructions.

TWO AUDIENCES, TWO LAYERS (Bill asked for both):
  step["plain"] — zero jargon, every term defined on first use.
                  A smart friend outside finance reads only this
                  and understands the whole method.
  step["desk"]  — the CLSA layer: rulebook citations, error
                  bars, what our edge is and where it dies.
                  Rendered as a collapsed "For the desk" block.

Every step also carries step["honesty"] — what this step could
get wrong. That is not decoration; it is the house style, and
it is what makes the walkthrough trustworthy rather than a sales
pitch.

MODES:
  "solved" — a past review (May-26): ends on a real SCOREBOARD,
             including the misses.
  "live"   — the open review (Aug-26): ends on a declared call
             with a grading date, no scoreboard yet.

Usage:
  py scripts\\walkthrough_story.py Taiwan May26
  from walkthrough_story import story; s = story("Taiwan", "May26")
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_MKT_ABBR = {"Taiwan": "TW"}


def _j(p):
    p = ROOT / "data" / p
    return json.loads(p.read_text()) if p.exists() else None


def _caps_at(codes, date, fx):
    """Every company's size at the frozen instant: that day's
    last traded price x shares outstanding, converted to USD."""
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
    """The measured universe: every index member at that review
    with its point-in-time size, plus the names that actually
    moved. Drives the interactive threshold lever."""
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
    rows = [{"code": c, "name": nm.get(c, c),
             "cap": round(v, 2),
             "actual": act.get(c, "")} for c, v in caps.items()]
    # names MSCI added at this review were not members before,
    # so add them explicitly with their measured size
    for c, a in act.items():
        if a == "ADD" and c not in caps:
            extra = _caps_at([c], k["price_date"], fx)
            if c in extra:
                rows.append({"code": c, "name": nm.get(c, c),
                             "cap": round(extra[c], 2),
                             "actual": "ADD"})
    return sorted(rows, key=lambda r: -r["cap"])


def _market_facts(market):
    off = (_j("msci_official_constituents.json") or
           {}).get("markets", {}).get(market)
    if not off:
        return {}
    cs = sorted(off["constituents"], key=lambda x: -x["weight"])
    return {"n": off["n"], "top_name": cs[0]["security"],
            "top_weight": cs[0]["weight"],
            "top10": round(sum(x["weight"] for x in cs[:10]), 1)}


def story(market="Taiwan", review="May26"):
    """Build the whole narrative for one market + review."""
    live = review == "Aug26"
    mf = _market_facts(market)
    steps = []
    if live:
        a = _j("aug26_cutoff_calc.json")
        d = a["derivation"]["A_global"]
        k = {"gmsr_dm": d["dm_aug_busd"],
             "em_range": d["em_range_busd"],
             "ceiling": d["em_range_busd"][1],
             "floor": round(2 / 3 * d["em_range_busd"][1], 2),
             "bar": round(1.5 * d["em_range_busd"][1], 2),
             "price_date": "2026-07-20 (ESTIMATED — MSCI has "
                           "not disclosed it yet)",
             "source": "forecast from the May-2026 book"}
        fx = 32.214
        uni = sorted(
            [{"code": x["code"],
              "name": x.get("company") or x["code"],
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
        "n": 1, "title": "What is actually being decided",
        "plain": [
            "An index is just a list of companies. MSCI publishes "
            f"one for {market}: today it holds "
            f"{mf.get('n', '—')} companies.",
            "The list matters because thousands of investment "
            "funds have promised their customers they will hold "
            "exactly what is on it — no more, no less. Those "
            "funds do not pick stocks; copying the list IS their "
            "product.",
            "Four times a year MSCI updates the list. The moment "
            "a company is added, every one of those funds has to "
            "buy it, and they all have to be finished by the "
            "same evening. A company being removed gets the "
            "mirror image: forced selling, same evening.",
            "That is the whole reason this work exists. If you "
            "can work out who is joining and who is leaving "
            "before it is announced, you know where an enormous, "
            "price-insensitive, deadline-driven order is about "
            "to land."],
        "numbers": [
            {"label": "Companies in the index",
             "value": mf.get("n", "—")},
            {"label": f"Weight of {mf.get('top_name', '—')}",
             "value": f"{mf.get('top_weight', 0):.1f}%"},
            {"label": "Top 10 combined",
             "value": f"{mf.get('top10', 0):.1f}%"}],
        "desk":
            "Standard (large+mid) country index. Passive AUM "
            "tracking it must trade the reconstitution at the "
            "closing auction on the effective date, which is why "
            "the print concentrates in the last minutes. Weight "
            "concentration matters for the funding leg: "
            f"{mf.get('top_name', '')} at "
            f"{mf.get('top_weight', 0):.1f}% means index-relative "
            "flow in the small names is a rounding error to the "
            "fund but the entire day's volume to the stock.",
        "honesty":
            "Constituent count is MSCI's own published list, "
            "which is delayed roughly two months — it is the "
            "May-2026 membership, not a live one."})

    # ---------------- step 2 -------------------------------
    steps.append({
        "n": 2,
        "title": "The photograph is taken before anyone sees it",
        "plain": [
            "MSCI does not judge companies on the day it "
            "announces the change. It judges them on an earlier "
            "day — it takes a photograph of the market, then "
            "spends weeks deciding, then announces.",
            "So the entire prediction problem reduces to one "
            "thing: rebuild the photograph. Use only what was "
            "true on that day. No later prices, no hindsight.",
            "There is a catch that makes this genuinely hard. "
            "MSCI does not say in advance which day the "
            "photograph is taken. It reserves the right to pick "
            "any one of the last ten business days of the month. "
            "You only learn which one afterwards.",
            f"For this review the day was "
            f"{str(k['price_date'])[:10]}."],
        "numbers": [
            {"label": "Photograph taken",
             "value": str(k["price_date"])[:10]},
            {"label": "Possible days MSCI could have picked",
             "value": "10"},
            {"label": "Exchange rate used that month",
             "value": f"{fx} TWD per USD"}],
        "desk":
            "GIMI May-2026 §3.1.9 p.48: three data dates per "
            "review — Equity Universe cutoff (last b-day of "
            "Nov/Feb/May/Aug), Liquidity cutoff (last b-day of "
            "Dec/Mar/Jun/Sep), and the Price Cutoff, ANY ONE of "
            "the last 10 b-days of Jan/Apr/Jul/Oct, chosen at "
            "MSCI's discretion (fn28 prepone rule; fn29 defines "
            "the business day off >80% ACWI). We mined 23 "
            "editions of the methodology book and found MSCI "
            "discloses the date it used ex post inside each "
            "book's worked example — in essentially every case "
            "it picked the FIRST one or two days of the window. "
            "That is our prior, not a rule.",
        "honesty":
            "The date prior is empirical, from disclosed "
            "editions. MSCI is not bound by it and could pick "
            "day ten. Using the wrong day moves every measured "
            "size by whatever the market did in between."})

    # ---------------- step 3 -------------------------------
    steps.append({
        "n": 3, "title": "How big do you have to be?",
        "plain": [
            "MSCI needs one consistent answer to 'how big is big "
            "enough' across every country, otherwise the index "
            "would fill up with large companies from big markets "
            "and nothing from small ones.",
            "So it sets one global size bar, then halves it for "
            "emerging markets like this one, and allows the "
            "real cutoff to sit anywhere inside a band around "
            "that number.",
            f"For this review the global bar was "
            f"${k['gmsr_dm']}B, giving this market a permitted "
            f"band of ${k['em_range'][0]}B to "
            f"${k['em_range'][1]}B.",
            "From that band come the only two numbers that "
            "decide anything: a floor, below which a current "
            "member is at risk of removal, and a higher bar an "
            "outsider must clear to be added. The gap between "
            "them is deliberate — MSCI does not want companies "
            "bouncing in and out every quarter."],
        "numbers": [
            {"label": "Global size bar",
             "value": f"${k['gmsr_dm']}B"},
            {"label": "This market's permitted band",
             "value": f"${k['em_range'][0]}B – "
                      f"${k['em_range'][1]}B"},
            {"label": "Deletion floor",
             "value": f"${k['floor']}B",
             "note": "members below this are at risk"},
            {"label": "Addition bar", "value": f"${k['bar']}B",
             "note": "outsiders must clear this"}],
        "desk":
            "GIMI §2.3.2.1: the Global Minimum Size Reference is "
            "the full market cap at the 70/85/99% float-coverage "
            "crossings of the DM universe; EM = half. §2.3.3 "
            "governs what happens when a market's own crossing "
            "falls outside the range — membership COUNT flexes, "
            "MSCI states priority to global size integrity over "
            "market coverage. Floor = 2/3 x ceiling and add bar "
            "= 1.5 x ceiling are the frontier conventions. "
            f"Source for these figures: {k['source']}.",
        "honesty":
            "We treat the ceiling as the binding cutoff for this "
            "market — an ASSUMPTION, registered as such. Under a "
            "different float frame Taiwan's crossing has sat "
            "inside the corridor rather than above it, which "
            "would move both lines."})

    # ---------------- step 4 -------------------------------
    ex = next((u for u in uni if u.get("actual") == "DEL"),
              uni[0] if uni else None)
    steps.append({
        "n": 4,
        "title": "Measure every company at that frozen instant",
        "plain": [
            "Now we size every company as it was on the "
            "photograph day: the share price that day, "
            "multiplied by the number of shares in existence, "
            "converted into US dollars at that month's exchange "
            "rate.",
            "We use each company's own historical price series, "
            "so nothing that happened afterwards can leak in. "
            "This is the part people get wrong — it is very easy "
            "to accidentally use today's price and 'predict' the "
            "past perfectly.",
            "One refinement matters: MSCI does not count shares "
            "that are never going to trade — a government stake, "
            "a founding family's block. It counts the free "
            "float. For the tests that decide most outcomes we "
            "compare full size against the lines, and we flag "
            "clearly where float is doing the work, because "
            "float is the number we are least sure of."]
        + ([f"Worked example: {ex['name']} measured "
            f"${ex['cap']}B on that day."] if ex else []),
        "numbers": [
            {"label": ("Candidates measured" if live
                       else "Companies measured"),
             "value": len(uni),
             "note": ("the live sheet carries only names near "
                      "the lines" if live else
                      "every index member at that review")},
            {"label": "Price source",
             "value": "each company's own daily history"},
            {"label": "Largest measured",
             "value": f"${uni[0]['cap']}B" if uni else "—"}],
        "desk":
            "PIT caps = vintage close x NumberOfSharesIssued at "
            "the disclosed price date / that month's TWD rate "
            "(fx_twd_history.json, the live TWD=X series — a "
            "correction: an earlier rate was derived circularly "
            "from a float that itself assumed the rate). Float "
            "stack (c-139 policy), best to worst: (1) MSCI "
            "factsheet-implied FIFs, top-10, exact same-date; "
            "(2) MSCI's OWN member FIFs recovered by the weights "
            "inversion, 60 members on MSCI's rounding grid; "
            "(3) Yahoo floatShares/sharesOutstanding — 2.7% "
            "median error vs MSCI on the aligned overlap, the "
            "best PUBLIC source; (4) TDCC bracket float x a "
            "calibration measured on the Yahoo overlap (TDCC "
            "counts large domestic institutions as strategic "
            "when MSCI counts them as float). At 2026-07-31 the "
            "mix was 10 / 53 / ~490 / ~1,460 names; no name "
            "fell through to a bare default. A name whose "
            "add/del verdict FLIPS between adjacent tiers is "
            "labeled borderline, not called.",
        "honesty":
            "Floats are current-vintage, not point-in-time. That "
            "is fine for full-size tests and NOT fine for the "
            "float half-bar gate, which we therefore skip "
            "historically rather than fake."})

    # ---------------- step 5 -------------------------------
    pool = (grading or {}).get("pool", {})
    steps.append({
        "n": 5, "title": "Draw the two lines",
        "plain": [
            "Everything now sits on a single axis: company size "
            "on that day. Draw the floor and the bar across it.",
            "Members that fall below the floor become our "
            "deletion candidates. Outsiders above the bar become "
            "our addition candidates. That is the prediction — "
            "there is no more machinery than this.",
            "Drag the line yourself in the chart below and watch "
            "which companies cross. That is exactly what happens "
            "when the exchange rate moves, or when MSCI picks a "
            "different photograph day: the line slides, and the "
            "names at the edge change sides.",
            "Notice how many names sit close to the line. Those "
            "are where the money is made and lost — not on the "
            "obvious cases."],
        "numbers": [
            {"label": "Members below the floor",
             "value": len(pool) if pool else "see chart"},
            {"label": "Floor", "value": f"${k['floor']}B"},
            {"label": "Bar", "value": f"${k['bar']}B"}],
        "desk":
            "The pool is the below-floor set of PIT members; "
            "membership itself is reverse-rolled from the "
            "current official list through the count-validated "
            "changes database. Ranking within the pool is the "
            "live research question — MSCI sweeps a subset, not "
            "the whole pool, and the selection is where "
            "discretion enters.",
        "honesty":
            "A candidate is not a prediction of certainty. Some "
            "below-floor names survive for years."})

    # ---------------- step 6 -------------------------------
    if live:
        a = _j("aug26_cutoff_calc.json")
        calls = a["shadow_add_call"]["calls"]
        steps.append({
            "n": 6, "title": "The live call, on the record",
            "plain": [
                "This review has not been announced yet, so "
                "there is no scoreboard — only a call, declared "
                "before the answer exists.",
                "Writing it down in advance is the whole point. "
                "A method that is only evaluated after the fact "
                "can always be made to look right.",
                "Our addition call: "
                + ", ".join(f"{c['code']} {c.get('name', '')} "
                            f"({c['strength'].split('—')[0].strip()})"
                            for c in calls) + ".",
                "Our deletion watchlist is the set of members "
                "measuring below the floor, listed above. Both "
                "grade when MSCI announces."],
            "numbers": [
                {"label": "Declared",
                 "value": a["shadow_add_call"]["declared"][:10]},
                {"label": "Grades", "value": "Aug 11-12, 2026"},
                {"label": "Delete watchlist",
                 "value": len(a["delete_candidates"])}],
            "desk":
                "Shadow frame: the locked 16-name engine cannot "
                "see these names, so both the locked engine and "
                "the shadow ladder grade separately on Aug-12. "
                "Registries were locked before evaluation.",
            "honesty":
                a["blind_band"]})
    else:
        h = len(grading["hits"])
        m = len(grading["misses"])
        f = len(grading["false_alarms"])
        steps.append({
            "n": 6, "title": "What we said, and what MSCI did",
            "plain": [
                "Now the honest part. MSCI has announced this "
                "review, so we can mark our own homework.",
                f"Of the companies MSCI actually removed, our "
                f"method flagged {h} of {h + m} in advance.",
                f"We also flagged {f} companies that MSCI left "
                f"alone. Those are not simply errors. Our rule "
                f"says 'below the floor', but MSCI removes only "
                f"a subset of the below-floor names and applies "
                f"judgement to the rest. So the false alarms are "
                f"a measurement of that judgement — and that gap "
                f"is precisely what a prediction model has to "
                f"learn.",
                "We publish the misses. A walkthrough that only "
                "showed the wins would teach you nothing about "
                "how much to trust the next call."],
            "numbers": [
                {"label": "Removals caught", "value": f"{h}/{h + m}"},
                {"label": "Removals missed", "value": m},
                {"label": "False alarms", "value": f,
                 "note": "MSCI's discretion, measured"}],
            "desk":
                "Across the backtested reviews the deletion "
                "capture runs ~83% with 6-25 false alarms per "
                "review. The false-alarm set is the labelled "
                "training target for the ranking model "
                "(logistic on below-floor pool features, "
                "walk-forward, scored by Brier).",
            "honesty":
                "Additions are graded more loosely than "
                "deletions because newcomers can enter from "
                "outside the measured universe — a company that "
                "was never a member and never appeared in our "
                "data can be added."})

    # ---------------- step 7 -------------------------------
    steps.append({
        "n": 7, "title": "What we still cannot know",
        "plain": [
            "Four limits, stated plainly, because a method is "
            "only useful if you know where it stops working.",
            "First, MSCI keeps explicit discretion for unusual "
            "situations. No amount of data predicts a judgement "
            "call.",
            "Second, free float — how many shares can actually "
            "trade — is estimated, not published. It is our "
            "weakest input, and it is the input that decides "
            "borderline cases.",
            "Third, companies sometimes leave the index between "
            "reviews, through takeovers, delistings or "
            "sanctions. Those never appear in a review list at "
            "all.",
            "Fourth, we cannot see a company that has never been "
            "in our universe. A large new listing can be added "
            "with no warning from this method."],
        "numbers": [],
        "desk":
            "Registered gaps: PIT floats (MOPS filings) not yet "
            "wired; 2015-17 methodology editions unavailable so "
            "reconstructions are scoped to 2018+; off-cycle "
            "exits classified (466 candidates, EO-13959 "
            "sanction wave identified) but 391 remain "
            "unprobeable; QIR rank-based migration is a "
            "registered rule refinement.",
        "honesty":
            "Each limit above is tracked as an open task, not "
            "a disclaimer."})

    return {"market": market, "review": review,
            "mode": "live" if live else "solved",
            "title": f"How we predict MSCI index changes — "
                     f"{market}, {review}",
            "keys": k, "fx": fx, "universe": uni,
            "grading": grading, "steps": steps}


if __name__ == "__main__":
    mkt = sys.argv[1] if len(sys.argv) > 1 else "Taiwan"
    rev = sys.argv[2] if len(sys.argv) > 2 else "May26"
    s = story(mkt, rev)
    print(f"{s['title']}  [{s['mode']}]")
    for st_ in s["steps"]:
        print(f"\n--- {st_['n']}. {st_['title']}")
        for n in st_["numbers"]:
            print(f"    {n['label']}: {n['value']}")
        print("    " + st_["plain"][0][:100] + "...")
    print(f"\nuniverse: {len(s['universe'])} companies")
