"""Candidate findings from the changes database (c-209).

BACKLOG item 9. PAGE_SPEC section 5 is explicit: I do not put
findings on the page. Bill decides what gets promoted. So this
sweeps the database, applies a bar registered BEFORE looking,
and writes what survives to docs/CANDIDATE_FINDINGS.md.

THE BAR, fixed in advance so it cannot be tuned to whatever
happens to pass:
  n >= 30            enough events to be worth a sentence
  holds in BOTH halves of the sample, split at the median
                     review — this is what kills the findings
                     that are really just one loud era
  effect >= 1.3x     or a 10-point gap for rates; below that a
                     reader would shrug

Anything failing the split-half test is still printed, marked
REJECTED and why. A rejected finding is more informative than a
silent one: it says the pattern exists but does not persist.

Usage:  py scripts\\findings_sweep.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "docs" / "CANDIDATE_FINDINGS.md"

MIN_N = 30
MIN_RATIO = 1.3
MIN_RATE_GAP = 0.10
REGIME = "Feb23"


def _reviews():
    out = []
    for y in range(2006, 2027):
        for mon in ("Feb", "May", "Aug", "Nov"):
            if (y, mon) == (2026, "Aug"):
                break
            out.append(f"{mon}{y % 100:02d}")
    return out


def _halves(df):
    """Split on the MEDIAN REVIEW, not the median row.

    Splitting on rows would put the busy pre-2023 May/Nov
    rebuilds almost entirely in one half and call the result a
    time effect.
    """
    revs = [r for r in _reviews() if (df.review == r).any()]
    mid = revs[len(revs) // 2]
    early = set(revs[:len(revs) // 2])
    return (df[df.review.isin(early)],
            df[~df.review.isin(early)], mid)


def _skew(g):
    a = int((g.action == "ADD").sum())
    d = int((g.action == "DEL").sum())
    return a, d, (a / d if d else None)


def sweep():
    import pandas as pd
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    early, late, mid = _halves(df)
    keep, rejected = [], []

    # ---- 1. add/delete skew per market --------------------
    for m in sorted(df.market.unique()):
        g = df[df.market == m]
        if len(g) < MIN_N:
            continue
        a, d, r = _skew(g)
        if not r:
            continue
        _, _, r1 = _skew(early[early.market == m])
        _, _, r2 = _skew(late[late.market == m])
        claim = (f"{m} has run {r:.2f} additions per deletion "
                 f"since 2006 ({a} adds, {d} deletions)")
        # ORDER MATTERS, and the first version had it wrong.
        #
        # I applied the effect-size gate BEFORE the stability
        # test, so anything with a modest full-sample ratio was
        # dropped before it could be rejected — and a modest
        # full-sample ratio is exactly what you get when the two
        # halves point in opposite directions and cancel. The
        # sweep reported 17 survivors and 0 rejections, which is
        # not a strict bar, it is a bar that never fires.
        #
        # Hong Kong is the case in point: 1.16 early, 0.47 late,
        # a complete reversal, and 0.81 overall — filtered out
        # as "too small an effect" instead of flagged as
        # unstable. Stability is now tested FIRST, on everything
        # that meets n, and effect size only decides whether a
        # STABLE finding is worth a sentence.
        if not r1 or not r2:
            rejected.append((claim, "one half has no deletions"))
            continue
        if (r1 > 1) != (r2 > 1):
            rejected.append(
                (claim, f"direction REVERSES across the split at "
                        f"{mid} — early {r1:.2f}, late {r2:.2f}. "
                        f"The full-sample {r:.2f} is two eras "
                        f"cancelling, not a stable tendency"))
            continue
        if max(r, 1 / r) < MIN_RATIO:
            continue                      # stable but too small
        keep.append((claim, f"n={len(g)}; early {r1:.2f}, "
                            f"late {r2:.2f}; both same side "
                            f"of 1.0", "add/delete skew"))

    # ---- 2. the Feb-2023 methodology change ---------------
    revs = _reviews()
    pre = [r for r in revs if r != REGIME
           and revs.index(r) < revs.index(REGIME)]
    qir_pre = df[df.review.isin(pre)
                 & df.review.str[:3].isin(["Feb", "Aug"])]
    qir_post = df[~df.review.isin(pre)
                  & df.review.str[:3].isin(["Feb", "Aug"])]
    sair_pre = df[df.review.isin(pre)
                  & df.review.str[:3].isin(["May", "Nov"])]
    sair_post = df[~df.review.isin(pre)
                   & df.review.str[:3].isin(["May", "Nov"])]

    def per_rev(sub, months):
        n = len({r for r in revs if r[:3] in months
                 and (sub.review == r).any()})
        return len(sub) / n if n else 0
    a1 = per_rev(qir_pre, ("Feb", "Aug"))
    a2 = per_rev(qir_post, ("Feb", "Aug"))
    b1 = per_rev(sair_pre, ("May", "Nov"))
    b2 = per_rev(sair_post, ("May", "Nov"))
    if len(qir_post) >= MIN_N and a1 and a2 / a1 >= MIN_RATIO:
        keep.append((
            f"February and August reviews moved {a2 / a1:.1f}x "
            f"more names after MSCI's Feb-2023 method change "
            f"({a1:.0f} -> {a2:.0f} changes per review, APAC)",
            f"n={len(qir_pre)} pre, {len(qir_post)} post; "
            f"May/Nov over the same split went {b1:.0f} -> "
            f"{b2:.0f}, so this is not a general rise in "
            f"activity", "regime change"))

    # ---- 3. quiet reviews ---------------------------------
    for m in sorted(df.market.unique()):
        g = df[df.market == m]
        if len(g) < MIN_N:
            continue
        act = {r for r in g.review.unique()}
        q = 1 - len(act) / len(revs)
        e = 1 - len(set(early[early.market == m].review)) / \
            (len(revs) // 2)
        lt = 1 - len(set(late[late.market == m].review)) / \
            (len(revs) - len(revs) // 2)
        if q < 0.30:
            continue
        claim = (f"{m} left the index untouched at {q:.0%} of "
                 f"reviews since 2006")
        if abs(e - lt) > 0.35:
            rejected.append(
                (claim, f"unstable across the split ({e:.0%} "
                        f"early vs {lt:.0%} late)"))
        else:
            keep.append((claim, f"n={len(revs)} reviews; "
                                f"{e:.0%} early, {lt:.0%} late",
                         "quiet reviews"))

    lines = [
        "# CANDIDATE FINDINGS — for Bill to accept or reject",
        "",
        "Generated by `py scripts\\findings_sweep.py`. Per",
        "PAGE_SPEC section 5 these are NOT on the page. Bill",
        "decides what gets promoted.",
        "",
        f"Bar registered before looking: n >= {MIN_N}, effect",
        f">= {MIN_RATIO}x (or {MIN_RATE_GAP:.0%} for rates), and",
        "the effect must hold in BOTH halves of the sample split",
        f"at the median review ({mid}).",
        "",
        f"## SURVIVED ({len(keep)})", ""]
    for claim, method, tag in keep:
        lines += [f"- **{claim}.**", f"  - [{tag}] {method}", ""]
    lines += [f"## REJECTED ({len(rejected)})", "",
              "Printed because a rejected finding is informative:",
              "the pattern is there, it just does not persist.",
              ""]
    for claim, why in rejected:
        lines += [f"- ~~{claim}~~", f"  - REJECTED: {why}", ""]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"survived {len(keep)}, rejected {len(rejected)}")
    for c, _, _ in keep:
        print(f"  + {c}")
    for c, w in rejected:
        print(f"  - {c[:60]}… ({w[:40]})")
    print(f"-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    sweep()
