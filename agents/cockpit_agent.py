"""Pre-open T-day cockpit agent — Layer-1 (c-40, STEP34 build #3).

Assembles per-name cockpit cards BEFORE the desk sits down, purely
from existing artifacts (no new computation — plumbing, exactly as
designed): Step-2 scenario + advice, expected print prior, playbook
split, T-day forecast card fields, sentinel headline. Emits a JSON
for the UI and a markdown desk-note DRAFT (analyst signs; agent
never sends).

Usage: python -m agents.cockpit_agent [event_tag]   (default may26
rehearsal — the graded event, so the output can be checked against
what actually happened; run with aug26 after the announcement)
"""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(p):
    f = ROOT / "data" / p
    return json.loads(f.read_text()) if f.exists() else None


def build_cockpit(event_tag="may26"):
    from agents.post_event import PLAYBOOK_SPLITS
    liq = _load(f"liquidity_forecast_{event_tag}.json") or {}
    sent = _load("sentinel_report.json") or {}
    cards = []
    for r in liq.get("names", []):
        w = PLAYBOOK_SPLITS.get(r["scenario"], (0, 1, 0))
        cards.append({
            "code": r["code"], "side": r["side"],
            "scenario": r["scenario"],
            "flow_completion": r["flow_completion"],
            "foreign_consistent": r["foreign_direction_consistent"],
            "expected_print_x_adv": r["expected_flow_x_adv"],
            "playbook_split": f"{w[0]:.0%} window / {w[1]:.0%} MOC "
                              f"/ {w[2]:.0%} T+1",
            "advice": r["advice"]})
    return {"event_tag": event_tag,
            "generated": dt.datetime.now()
            .isoformat(timespec="seconds"),
            "sentinel_overall": sent.get("overall", "not run"),
            "t_day": liq.get("eff"), "cards": cards}


def render_note(ck):
    L = [f"# T-day Desk Note DRAFT — {ck['event_tag']} "
         f"(T = {ck.get('t_day')})",
         f"*Assembled {ck['generated']} by the cockpit agent from "
         f"graded artifacts. Sentinels: {ck['sentinel_overall']}. "
         "DRAFT — advice requires trader sign-off.*\n"]
    for c in ck["cards"]:
        L.append(f"## {c['side'].upper()} {c['code']} — "
                 f"{c['scenario']}")
        L.append(f"- completion {c['flow_completion']}x expected "
                 f"flow; foreign direction "
                 f"{'consistent' if c['foreign_consistent'] else 'WRONG-WAY'}"
                 f"; expected print ~{c['expected_print_x_adv']}x "
                 "ADV")
        L.append(f"- split: {c['playbook_split']}")
        L.append(f"- {c['advice']}\n")
    return "\n".join(L)


if __name__ == "__main__":
    import sys
    tag = sys.argv[1] if len(sys.argv) > 1 else "may26"
    ck = build_cockpit(tag)
    (ROOT / "data" / f"cockpit_{tag}.json").write_text(
        json.dumps(ck, indent=1))
    (ROOT / "docs" / "case_studies" /
     f"DESK_NOTE_{tag.upper()}.md").write_text(
        render_note(ck), encoding="utf-8")
    print(f"cockpit {tag}: {len(ck['cards'])} cards; sentinels "
          f"{ck['sentinel_overall']}")
