"""Widen every Taiwan event window to +/-20 sessions (c-271).

    py scripts\\tw_window_topup.py check     # what is missing
    py scripts\\tw_window_topup.py run       # fetch and merge
    py scripts\\tw_window_topup.py verify    # assert the target

WHY. The windows were harvested as ann MINUS 25 CALENDAR days
-> eff PLUS 25. After weekends and Taiwan holidays that is only
~17 sessions a side, and it varies event by event: 10 to 18
before the announcement, 15 to 19 after the effective close.
ZERO of the 136 analysable events have 20 clear sessions on
both sides.

That is not cosmetic. Any metric reaching past the end of the
series silently clamps to the last available day, so a
"20-session reversion" is really 15 to 19 sessions and a
DIFFERENT horizon for every event, averaged together as if it
were one measurement. The pre-announcement side is worse: the
nine shortest windows are almost all FEBRUARY reviews cut down
by Lunar New Year, so the truncation is seasonal rather than
random and biases anything measured across review months.

WHAT THIS DOES. For each window it fetches ONLY the sessions
that are missing — the calendar gap before the existing first
row and after the existing last row — and merges them in. Rows
already held are never re-fetched and never overwritten.

WHY IT ITERATES. The gap in SESSIONS is known; the gap in
CALENDAR DAYS is not, because holidays are not evenly spread.
Asking for a fixed 30 days back would be too few across Lunar
New Year and too many everywhere else. So it asks for a first
guess, measures what came back, and asks again for whatever is
still short, up to three rounds. The alternative — a generous
fixed pad — costs several hundred needless requests.

THE MERGE IS ADDITIVE AND ORDER-SAFE: rows are keyed by date,
existing values win on collision, and the series is re-sorted
after every merge. A partial or throttled fetch can therefore
only leave a window shorter than the target, never corrupt one,
and re-running the command resumes.
"""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
WINDOWS = ROOT / "data" / "tw_event_windows.json"

TARGET = 20             # sessions required each side
MAX_ROUNDS = 3
# first guess at calendar days per missing session. Taiwan
# trades ~21 sessions a month, so 1.5 covers ordinary weekends;
# the iteration handles Lunar New Year rather than a bigger
# constant punishing every other event.
DAYS_PER_SESSION = 1.5
TWSE_FLOOR = "2010-01-04"


def _load():
    return json.loads(WINDOWS.read_text(encoding="utf-8"))


def _save(d):
    WINDOWS.write_text(json.dumps(d, ensure_ascii=False),
                       encoding="utf-8")


def _counts(v):
    """(sessions before ann, sessions after eff) for one window."""
    ds = [r["d"] for r in v["px"]]
    a = [i for i, d in enumerate(ds) if d <= str(v["ann"])[:10]]
    e = [i for i, d in enumerate(ds) if d <= str(v["eff"])[:10]]
    if not a or not e:
        return None, None
    return a[-1], len(ds) - 1 - e[-1]


def _iso(d):
    return d.isoformat()


def check(quiet=False):
    d = _load()
    todo = []
    for k, v in d["windows"].items():
        if not (isinstance(v, dict) and v.get("px")):
            continue
        pre, post = _counts(v)
        if pre is None:
            continue
        if pre < TARGET or post < TARGET:
            todo.append((k, pre, post))
    if not quiet:
        n = sum(1 for v in d["windows"].values()
                if isinstance(v, dict) and v.get("px"))
        print(f"windows priced            : {n}")
        print(f"already at +/-{TARGET}         : {n - len(todo)}")
        print(f"short on at least one side: {len(todo)}")
        if todo:
            sp = sum(max(0, TARGET - p) for _, p, _ in todo)
            so = sum(max(0, TARGET - q) for _, _, q in todo)
            print(f"sessions to fetch         : {sp} pre + {so} "
                  f"post = {sp + so}")
    return todo


def run(limit=None):
    import tw_event_window as TW
    d = _load()
    todo = check(quiet=True)
    if limit:
        todo = todo[:limit]
    print(f"topping up {len(todo)} window(s) to +/-{TARGET} "
          f"sessions\n")
    done = 0
    for n, (key, pre0, post0) in enumerate(todo, 1):
        v = d["windows"][key]
        code = str(v["code"])
        for rnd in range(MAX_ROUNDS):
            pre, post = _counts(v)
            if pre >= TARGET and post >= TARGET:
                break
            ds = sorted(r["d"] for r in v["px"])
            first = dt.date.fromisoformat(ds[0])
            last = dt.date.fromisoformat(ds[-1])
            got = []
            if pre < TARGET:
                back = int((TARGET - pre) * DAYS_PER_SESSION) + 5
                s = _iso(first - dt.timedelta(days=back))
                if s < TWSE_FLOOR:
                    s = TWSE_FLOOR
                e = _iso(first - dt.timedelta(days=1))
                if s <= e:
                    got += TW.fetch_window(code, s, e)
            if post < TARGET:
                fwd = int((TARGET - post) * DAYS_PER_SESSION) + 5
                s = _iso(last + dt.timedelta(days=1))
                e = _iso(last + dt.timedelta(days=fwd))
                if s <= e:
                    got += TW.fetch_window(code, s, e)
            if not got:
                break
            # ADDITIVE MERGE: existing rows win, new rows fill in
            by_date = {r["d"]: r for r in got}
            by_date.update({r["d"]: r for r in v["px"]})
            v["px"] = [by_date[k2] for k2 in sorted(by_date)]
        pre, post = _counts(v)
        ok = pre >= TARGET and post >= TARGET
        done += ok
        _save(d)
        print(f"  [{n}/{len(todo)}] {key:<14} "
              f"{pre0}->{pre} pre, {post0}->{post} post"
              f"{'' if ok else '   STILL SHORT'}", flush=True)
    print(f"\nat target: {done}/{len(todo)}")
    verify()


def verify():
    d = _load()
    pre_min = post_min = 10 ** 6
    short = []
    for k, v in d["windows"].items():
        if not (isinstance(v, dict) and v.get("px")):
            continue
        if v.get("day0") != "registry":
            continue          # the analysable panel is what matters
        pre, post = _counts(v)
        if pre is None:
            continue
        pre_min, post_min = min(pre_min, pre), min(post_min, post)
        if pre < TARGET or post < TARGET:
            short.append((k, pre, post))
    print(f"\nVERIFY on the {len(d['windows'])}-window store, "
          f"registry-dated only")
    print(f"  minimum sessions before announcement : {pre_min}")
    print(f"  minimum sessions after effective     : {post_min}")
    if short:
        print(f"  STILL SHORT: {len(short)}")
        for s in short[:15]:
            print(f"     {s[0]:<14} pre={s[1]:<3} post={s[2]}")
        print("\n  Analysis must not treat these as +/-20. "
              "Re-run `run`, or exclude them explicitly.")
        return False
    print("  OK — every registry-dated window clears "
          f"+/-{TARGET} sessions.")
    return True


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "run":
        run(int(sys.argv[2]) if len(sys.argv) > 2 else None)
    elif cmd == "verify":
        verify()
    else:
        check()
