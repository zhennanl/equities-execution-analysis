"""The agent's TOOL LAYER (c-138) — every deterministic
capability the rebalance agent can invoke, as plain functions.

DESIGN CONTRACT (the honesty culture, mechanized):
  - Tools compute; the LLM narrates. Every number in an agent
    conclusion must have come out of a tool — the agent layer
    (rebalance_agent.py) enforces this by prompt + by keeping
    tools' raw outputs in the note's appendix.
  - Tools NEVER guess. Missing data returns
    {"status": "NO_DATA", "need": "<which harvester>"} so the
    agent can dispatch a fetch instead of inventing.
  - Fetching is terminal-gated (TWSE one-consumer rule): in
    the sandbox, fetch tools return the command Bill runs.

Every function here is also directly usable by a human:
  py scripts\\agent_tools.py status
  py scripts\\agent_tools.py snapshot 2408
"""
import datetime as dt
import json
import statistics as stx
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def _j(name):
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _pctile(xs, v):
    xs = sorted(x for x in xs if x is not None)
    if not xs or v is None:
        return None
    return round(sum(1 for x in xs if x <= v) / len(xs), 2)


# ------------------------------------------------------------
# 1. SITUATIONAL AWARENESS
# ------------------------------------------------------------
def data_status():
    """Where are we in the cycle and what data is fresh/stale?
    The agent calls this FIRST every run."""
    led = _j("aug26_live_ledger.json") or {}
    today = dt.date.today()
    ann = dt.date.fromisoformat(led.get("ann", "2026-08-11"))
    eff = dt.date.fromisoformat(led.get("eff", "2026-08-31"))
    # count only NON-EMPTY days (c-138: an empty saved day is
    # not data)
    days = sorted(d for d, v in led.get("days", {}).items()
                  if any(p.get("close") for p in v.values()))
    last = days[-1] if days else None
    phase = ("PRE_ANNOUNCEMENT" if today <= ann else
             "ANNOUNCEMENT_TO_EFFECTIVE" if today <= eff else
             "POST_EFFECTIVE")
    stale = bool(last is None or last <
                 today.strftime("%Y%m%d"))
    return {
        "today": str(today), "phase": phase,
        "announcement": str(ann), "effective": str(eff),
        "day_offset": (today - ann).days,
        "shortlist": led.get("shortlist"),
        "ledger_days_pulled": len(days),
        "last_pull": last, "ledger_stale": stale,
        "historical_windows": len(
            (_j("event_window_metrics.json") or {})
            .get("windows", [])),
        "note": ("ledger stale -> call fetch_daily before "
                 "analysis" if stale else "data current")}


# ------------------------------------------------------------
# 2. DATA ACQUISITION (dispatchable)
# ------------------------------------------------------------
def fetch_daily(date=None):
    """Pull today's closes/foreign/borrow for the shortlist.
    Terminal-gated: on Bill's machine this RUNS; elsewhere it
    returns the command (one-TWSE-consumer rule)."""
    try:
        from event_window_live import pull
        pull(date)
        return {"status": "OK", "detail": "ledger updated"}
    except Exception as e:                         # noqa: BLE001
        return {"status": "DISPATCH",
                "run_on_terminal":
                    "py scripts\\event_window_live.py pull",
                "reason": str(e)[:200]}


# ------------------------------------------------------------
# 3. ANALYSIS (the automated versions of Bill's questions)
# ------------------------------------------------------------
def name_snapshot(code):
    """Everything known about one shortlist name TODAY, scored
    against the 157-window history at the same day-offset."""
    led = _j("aug26_live_ledger.json") or {}
    hist = (_j("event_window_metrics.json") or {}) \
        .get("windows", [])
    sl = led.get("shortlist", {})
    action = next((a for a in ("ADD", "DEL", "BUBBLE",
                               "BLOCKED")
                   for c in sl.get(a, []) if c == code), None)
    if action is None:
        return {"status": "NO_DATA",
                "need": f"{code} not on the shortlist"}
    days = sorted(led.get("days", {}))
    path = [led["days"][d].get(code, {}) for d in days]
    closes = [(d, p["close"]) for d, p in zip(days, path)
              if p.get("close")]
    if len(closes) < 2:
        return {"status": "NO_DATA", "code": code,
                "action": action,
                "need": "2+ pulled sessions "
                        "(fetch_daily after the Taipei close)"}
    cum = closes[-1][1] / closes[0][1] - 1
    fsum = sum(p.get("foreign_net") or 0 for p in path)
    borrows = [p.get("borrow_bal") for p in path
               if p.get("borrow_bal")]
    ann = dt.date.fromisoformat(led["ann"])
    t = len([d for d, _ in closes
             if dt.date(int(d[:4]), int(d[4:6]),
                        int(d[6:])) > ann])
    side = [w for w in hist if w["action"] == action] \
        if action in ("ADD", "DEL") else hist
    return {
        "status": "OK", "code": code, "action": action,
        "day_offset": t, "cum_return": round(cum, 4),
        "cum_return_pctile_vs_hist_drift":
            _pctile([w["drift"] for w in side], cum),
        "cum_foreign_net_sh": fsum,
        "borrow_path": borrows[-5:],
        "borrow_build": (round(borrows[-1] / borrows[0], 3)
                         if len(borrows) >= 2 and borrows[0]
                         else None),
        "borrow_build_pctile": _pctile(
            [w["borrow_build_pre"] for w in side],
            (borrows[-1] / borrows[0]
             if len(borrows) >= 2 and borrows[0] else None)),
        "hist_median_drift": round(stx.median(
            [w["drift"] for w in side
             if w["drift"] is not None]), 4) if side else None}


def crowding_read(code):
    """The positioning verdict for one name: which conditional
    bucket is it tracking (accumulation/froth; light/crowded
    short) and what did that bucket historically do next?"""
    snap = name_snapshot(code)
    if snap.get("status") != "OK":
        return snap
    cond = _j("event_conditional_tw.json") or {}
    out = {"code": code, "action": snap["action"],
           "inputs": snap}
    if snap["action"] == "ADD":
        A = cond.get("A_early_attribution_ADD", {})
        strong = (snap["cum_return_pctile_vs_hist_drift"]
                  or 0) >= 0.67
        flow = (snap["cum_foreign_net_sh"] or 0) > 0
        b = ("strong_early_with_flow" if strong and flow else
             "strong_early_no_flow" if strong else
             "weak_early")
        out["bucket"] = b
        out["bucket_history"] = A.get(
            b, A.get("weak_early", {}))
        out["read"] = ("accumulation — historically sticks"
                       if b == "strong_early_with_flow" else
                       "froth — runs hot, round-trips"
                       if b == "strong_early_no_flow" else
                       "cold — historically stays cold")
    else:
        C = cond.get("C_del_borrow", {})
        bb = snap.get("borrow_build")
        cuts = C.get("window_build_cutoffs", [1.02, 1.14])
        b = ("NO_DATA" if bb is None else
             "light_short" if bb < cuts[0] else
             "mid_short" if bb < cuts[1] else "crowded_short")
        out["bucket"] = b
        out["bucket_history"] = C.get(b, {})
        out["read"] = ("crowded short — deepest window drop "
                       "AND the only reliable post-E bounce"
                       if b == "crowded_short" else
                       "borrow data needed" if b == "NO_DATA"
                       else "not crowded — fade has no edge")
    return out


def find_analogs(action, day, cum_ret, sector=None):
    """Bill's analog distribution (analog_matcher)."""
    from analog_matcher import analogs
    return analogs(action, int(day), float(cum_ret), sector)


def result_block(study, key=None):
    """Read any registered result block (the agent's library).
    study in {persona, conditional, strategist, qa, playbooks}
    """
    files = {"persona": "persona_study_tw.json",
             "conditional": "event_conditional_tw.json",
             "strategist": "strategist_tw.json",
             "qa": "liquidity_qa_tw.json",
             "playbooks": "apac_event_playbooks.json"}
    d = _j(files[study]) if study in files else None
    if d is None:
        return {"status": "NO_DATA",
                "need": f"unknown study {study}; "
                        f"options {list(files)}"}
    if study == "qa":
        d = d.get("answers", d)
    if key:
        return d.get(key,
                     {"status": "NO_DATA",
                      "need": f"key {key} not in {study}; "
                              f"keys: {list(d)[:40]}"})
    return {"keys": list(d)}


# ------------------------------------------------------------
# 4. OUTPUT
# ------------------------------------------------------------
def save_note(title, body):
    """Persist a client note under reports/ (append-only,
    timestamped — corrections are new notes, never edits)."""
    rep = ROOT / "reports"
    rep.mkdir(exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M")
    p = rep / f"flow_note_{ts}.md"
    p.write_text(f"# {title}\n\n{body}\n", encoding="utf-8")
    return {"status": "OK", "saved": str(p)}


TOOLS = {f.__name__: f for f in (
    data_status, fetch_daily, name_snapshot, crowding_read,
    find_analogs, result_block, save_note)}


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "status":
        print(json.dumps(data_status(), indent=1))
    elif a and a[0] == "snapshot":
        print(json.dumps(name_snapshot(a[1]), indent=1))
    elif a and a[0] == "crowding":
        print(json.dumps(crowding_read(a[1]), indent=1))
    else:
        print("commands: status | snapshot CODE | "
              "crowding CODE")
