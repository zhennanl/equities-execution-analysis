"""Page: Ask the analyst (c-136) — a Claude-powered chat over
our own results, so users query the research in words instead
of writing pandas.

DESIGN (v1, deliberately safe):
  - Claude answers FROM OUR RESULT FILES, injected as context:
    the playbooks, the conditional study, the Q-bank answers,
    the strategist study, the Aug-26 shortlist + ledger. These
    are compact JSONs (~40KB total) — no code execution, no
    file access, no hallucinated numbers beyond the context.
  - The ANALOG MATCHER is exposed as a tool: when the user
    asks "find similar cases to X", Claude calls it and reads
    real matches back.
  - API key: ANTHROPIC_API_KEY env var, or pasted in the
    sidebar (kept in session only).

Cost note: each question sends ~40KB context to
claude-sonnet-4-5 — roughly a cent per question.
"""
import json
import os
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

CONTEXT_FILES = [
    ("Aug-26 declared shortlist + live ledger",
     "aug26_live_ledger.json"),
    ("Cross-market playbooks", "apac_event_playbooks.json"),
    ("Persona study (tracker/HF/desk)",
     "persona_study_tw.json"),
    ("Conditional study (early-strength attribution, "
     "hot-start, borrow, MAE)", "event_conditional_tw.json"),
    ("Strategist study (regime/sector/tide)",
     "strategist_tw.json"),
    ("Liquidity Q-bank answers (Q1-Q34 + auction)",
     "liquidity_qa_tw.json"),
]

SYSTEM = """You are the index-rebalance research assistant for
an execution-analytics project covering MSCI APAC reviews
(Taiwan in depth). Answer ONLY from the attached result JSONs
and tool results. Always cite which result block a number came
from (e.g. 'liquidity_qa: AUCTION'). If the context does not
contain the answer, say so and name which harvest or study
would produce it — never invent numbers. Keep answers short
and desk-ready; medians unless asked; flag small n."""


def _context():
    parts = []
    for label, fn in CONTEXT_FILES:
        p = ROOT / "data" / fn
        if p.exists():
            txt = p.read_text(encoding="utf-8")
            if len(txt) > 24000:
                txt = txt[:24000] + "...[truncated]"
            parts.append(f"=== {label} ({fn}) ===\n{txt}")
    return "\n\n".join(parts)


ANALOG_TOOL = {
    "name": "find_analogs",
    "description": "Find historical Taiwan index-event analogs:"
                   " given action (ADD/DEL), days since "
                   "announcement, cumulative return so far, and"
                   " optional sector (TECH/FINANCIAL/SHIPPING/"
                   "HEALTHCARE/OTHER), returns the closest "
                   "historical cases and what happened to them "
                   "into and after the effective day.",
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {"type": "string",
                       "enum": ["ADD", "DEL"]},
            "day": {"type": "integer"},
            "cum_ret": {"type": "number"},
            "sector": {"type": "string"}},
        "required": ["action", "day", "cum_ret"]}}


def render():
    st.title("Ask the analyst")
    st.caption(
        "Questions in plain words; answers from this project's "
        "own measured results (never invented). Try: *what does "
        "the close auction look like on effective days?* — or "
        "*my tech add is +5% at day 7, find similar cases.*")
    key = os.environ.get("ANTHROPIC_API_KEY") or \
        st.session_state.get("api_key")
    with st.sidebar:
        if not key:
            key = st.text_input("Anthropic API key",
                                type="password")
            if key:
                st.session_state["api_key"] = key
    if not key:
        st.info("Set ANTHROPIC_API_KEY (env) or paste a key in "
                "the sidebar to enable the chat.")
        return
    try:
        import anthropic
    except ImportError:
        st.error("pip install anthropic")
        return
    client = anthropic.Anthropic(api_key=key)
    if "chat" not in st.session_state:
        st.session_state.chat = []
    for m in st.session_state.chat:
        with st.chat_message(m["role"]):
            st.markdown(m["text"])
    q = st.chat_input("Ask about the Taiwan rebalance research")
    if not q:
        return
    st.session_state.chat.append({"role": "user", "text": q})
    with st.chat_message("user"):
        st.markdown(q)
    msgs = [{"role": m["role"], "content": m["text"]}
            for m in st.session_state.chat]
    msgs[0] = {"role": "user",
               "content": _context() + "\n\nQUESTION: "
               + st.session_state.chat[0]["text"]} \
        if len(msgs) == 1 else msgs[0]
    with st.chat_message("assistant"), st.spinner("thinking"):
        try:
            r = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1200, system=SYSTEM,
                tools=[ANALOG_TOOL], messages=msgs)
            while r.stop_reason == "tool_use":
                tu = next(b for b in r.content
                          if b.type == "tool_use")
                import sys
                sys.path.insert(0, str(ROOT / "scripts"))
                from analog_matcher import analogs
                res = analogs(**tu.input)
                msgs.append({"role": "assistant",
                             "content": r.content})
                msgs.append({"role": "user", "content": [
                    {"type": "tool_result",
                     "tool_use_id": tu.id,
                     "content": json.dumps(res)}]})
                r = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=1200, system=SYSTEM,
                    tools=[ANALOG_TOOL], messages=msgs)
            text = "".join(b.text for b in r.content
                           if b.type == "text")
        except Exception as e:                     # noqa: BLE001
            text = f"API error: {e}"
        st.markdown(text)
    st.session_state.chat.append({"role": "assistant",
                                  "text": text})
