"""THE REBALANCE AGENT (c-138) — the analyst-driven process,
inverted. Instead of Bill asking questions one at a time, an
expert agent runs the cycle: checks the situation, dispatches
data fetches, runs the analyses, consults specialist
subagents, and writes the client note — daily, unprompted.

ARCHITECTURE
  orchestrator (this file, "the strategist")
    tools  = scripts/agent_tools.py (deterministic; numbers
             ONLY come from here)
    subagents (consult tool -> second model call w/ role
             prompt, orchestrator passes them tool outputs):
       flow-analyst        who is buying/selling and why
       positioning-analyst crowding vs the 157-window history
       client-writer       the note a client can act on

HONESTY CONTRACT (in the system prompt, and structural):
  - every number must appear in a tool result; the raw tool
    log is appended to the saved note so any claim is
    auditable line-by-line
  - missing data -> the agent says NO_DATA and names the
    fetch; it never interpolates
  - anything abnormal (halted stock, off-cycle event, data
    contradiction) -> FLAG FOR ANALYST, stop, do not smooth

MODES
  py scripts\\rebalance_agent.py daily     the full loop
  py scripts\\rebalance_agent.py ask "..."  one question
  py scripts\\rebalance_agent.py offline   no-API fallback:
      deterministic pipeline only -> mechanical note (tables,
      no narrative). The automation NEVER depends on a key.

Needs ANTHROPIC_API_KEY on Bill's terminal for daily/ask.
Schedule: Windows Task Scheduler, weekdays 15:00 Taipei
(after the close + T86 publication), Aug-12 -> Sep-04.
"""
import datetime as dt
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_tools import TOOLS, data_status, save_note  # noqa: E402

MODEL = "claude-sonnet-4-5"

SYSTEM = """You are the index-rebalance strategist agent for
an agency program-trading desk covering MSCI Taiwan. You run
the announcement->effective cycle autonomously.

RULES (non-negotiable):
1. Numbers come ONLY from tool results. Cite the tool for
   every figure. If a tool returns NO_DATA, report the gap
   and which fetch fills it — never estimate around it.
2. Anything abnormal (contradictory data, a name behaving
   outside the historical p5-p95, suspected off-cycle event):
   write 'FLAG FOR ANALYST:' with the specifics and do not
   smooth over it.
3. Your product is the daily client note: current flow &
   positioning per shortlist name, the conditional-history
   read (which bucket, what that bucket did next), analogs
   where informative, and concrete stance per persona
   (tracker / hedge fund / agency desk). Medians with n;
   small n flagged.
4. Consult subagents via the consult tool when a section
   needs depth. Give them the tool outputs they need in the
   brief — they cannot call tools themselves.
5. Finish a daily run by calling save_note.

WORKFLOW for a daily run: data_status -> fetch_daily if stale
-> name_snapshot + crowding_read for every ADD and DEL on the
shortlist -> find_analogs for the names with 2+ sessions ->
consult(positioning-analyst) then consult(client-writer) ->
save_note."""

ROLES = {
    "flow-analyst": "You attribute flow: given snapshots "
        "(foreign net, borrow path, volume), say WHO is "
        "likely buying/selling (trackers pre-positioning, "
        "hedge funds, retail) and confidence. Only reason "
        "from the numbers in the brief.",
    "positioning-analyst": "You judge crowding: given "
        "per-name buckets and percentiles vs the historical "
        "windows, rank the shortlist from most to least "
        "crowded and state what each bucket historically did "
        "next (numbers from the brief only).",
    "client-writer": "You write the client-facing note: "
        "tight, desk-ready, per-name stance for tracker/HF/"
        "agency personas. Every figure must already be in "
        "the brief. Flag small n. No hedging filler."}


def _schema(fn):
    import inspect
    ps = inspect.signature(fn).parameters
    return {"name": fn.__name__,
            "description": (fn.__doc__ or "")[:900],
            "input_schema": {
                "type": "object",
                "properties": {p: {"type": "string"}
                               for p in ps},
                "required": [p for p, v in ps.items()
                             if v.default is
                             inspect.Parameter.empty]}}


def _consult(role, brief):
    import anthropic
    client = anthropic.Anthropic()
    r = client.messages.create(
        model=MODEL, max_tokens=1500,
        system=ROLES.get(role, ROLES["client-writer"]),
        messages=[{"role": "user", "content": brief}])
    return "".join(b.text for b in r.content
                   if b.type == "text")


def run_agent(objective, max_steps=24):
    import anthropic
    client = anthropic.Anthropic()
    tools = [_schema(f) for f in TOOLS.values()]
    tools.append({
        "name": "consult",
        "description": "Ask a specialist subagent. role in "
                       "{flow-analyst, positioning-analyst, "
                       "client-writer}; brief must contain "
                       "all numbers it needs.",
        "input_schema": {"type": "object", "properties": {
            "role": {"type": "string"},
            "brief": {"type": "string"}},
            "required": ["role", "brief"]}})
    msgs = [{"role": "user", "content": objective}]
    log = []
    for _ in range(max_steps):
        r = client.messages.create(
            model=MODEL, max_tokens=2500, system=SYSTEM,
            tools=tools, messages=msgs)
        if r.stop_reason != "tool_use":
            final = "".join(b.text for b in r.content
                            if b.type == "text")
            return final, log
        msgs.append({"role": "assistant",
                     "content": r.content})
        results = []
        for b in r.content:
            if b.type != "tool_use":
                continue
            try:
                if b.name == "consult":
                    out = _consult(**b.input)
                else:
                    inp = {k: (int(v) if k == "day" else
                               float(v) if k == "cum_ret"
                               else v)
                           for k, v in b.input.items()}
                    out = TOOLS[b.name](**inp)
            except Exception as e:                 # noqa: BLE001
                out = {"status": "TOOL_ERROR",
                       "error": str(e)[:300]}
            log.append({"tool": b.name, "input": b.input,
                        "output": out})
            results.append({"type": "tool_result",
                            "tool_use_id": b.id,
                            "content": json.dumps(out)
                            if not isinstance(out, str)
                            else out})
        msgs.append({"role": "user", "content": results})
    return "FLAG FOR ANALYST: step limit reached", log


def daily():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("No ANTHROPIC_API_KEY -> offline mode")
        return offline()
    final, log = run_agent(
        "Run today's daily cycle for the Aug-2026 Taiwan "
        "review shortlist. Follow the WORKFLOW. Today is "
        f"{dt.date.today()}.")
    audit = "\n\n---\n## Tool audit log\n```json\n" + \
        json.dumps(log, indent=1, default=str)[:20000] + \
        "\n```"
    save_note(f"Agent flow note {dt.date.today()}",
              final + audit)
    print(final)


def ask(q):
    final, log = run_agent(q)
    print(final)
    print(f"\n[{len(log)} tool calls]")


def offline():
    """The no-LLM fallback: run every deterministic tool and
    emit the mechanical note. Numbers identical to what the
    agent would narrate — automation survives without a key.
    """
    from agent_tools import name_snapshot, crowding_read
    s = data_status()
    lines = [f"MECHANICAL NOTE {s['today']} — phase "
             f"{s['phase']}, day {s['day_offset']}",
             f"data: {s['ledger_days_pulled']} days pulled, "
             f"last {s['last_pull']} "
             f"({'STALE' if s['ledger_stale'] else 'ok'})"]
    if s["ledger_stale"]:
        lines.append("-> run: py scripts\\event_window_live"
                     ".py pull   (then rerun)")
    for act in ("ADD", "DEL"):
        for c in (s.get("shortlist") or {}).get(act, []):
            r = crowding_read(c)
            if r.get("status") == "NO_DATA":
                lines.append(f"{act} {c}: NO_DATA "
                             f"({r['need']})")
                continue
            i = r["inputs"]
            lines.append(
                f"{act} {c}: cum {i['cum_return']:+.1%} "
                f"(pctile {i['cum_return_pctile_vs_hist_drift']})"
                f" | bucket {r['bucket']} -> {r['read']}")
    body = "\n".join(lines)
    save_note(f"Mechanical note {s['today']}", body)
    print(body)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "daily":
        daily()
    elif a and a[0] == "ask" and len(a) > 1:
        ask(" ".join(a[1:]))
    elif a and a[0] == "offline":
        offline()
    else:
        print(__doc__)
