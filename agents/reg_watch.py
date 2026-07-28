"""Reg-Watch — regulatory-change monitoring for the PT desk (JD bullet 5).

Three layers, one discipline: NOTHING auto-mutates the rules the desk
trades on. Every change is proposed with a source, reviewed by a human,
and version-stamped on approval.

    1. RULES REGISTRY (single source of truth): versioned entries for
       limit bands, auction cutoffs, lot/short/settlement rules per
       market, seeded from the static tables in pt_dealer /
       program_trading (public exchange rules, approximations disclosed
       there). pt_dealer reads live values FROM this registry — an
       approved change propagates to limit_proximity, auction_countdown
       and the compliance pre-flight automatically.
    2. NOTICE TRIAGE: fetch public exchange notice feeds, classify with
       a deterministic multilingual keyword engine (offline-testable,
       desk-safe default), surface HIGH/MED relevance in a daily digest
       with pre-drafted registry diffs. An optional LLM hook
       (`llm_summarize_hook`) upgrades summaries where a desk permits
       LLM use — it is a slot, never a dependency.
    3. EMPIRICAL CROSS-CHECK: agents.market_structure drift detection
       catches rule changes the circulars (or the keyword net) miss —
       a tick/lot regime change shows up in spread/size distributions.

Feed status (probed 2026-07-28 from this sandbox; a desk network will
differ): TWSE openapi (zh) OK; JPX news json (ja/en titles) OK; NSE
circulars api (en) OK; TPEx/HKEX/KRX/SGX/SET blocked (403/JS) ->
PROTOCOL entries with the desk-side source named.
"""
from __future__ import annotations

import datetime as _dt
import json
import urllib.request
from pathlib import Path

import pandas as pd

REGISTRY_PATH = (Path(__file__).resolve().parent.parent / "data"
                 / "reg_registry.json")

_UA = {"User-Agent": "Mozilla/5.0"}


# ────────────────────────────────────────────── 1. the rules registry ──

def _seed_entries() -> list[dict]:
    """Version-1 entries from the project's static tables. Source labels
    are explicit that these are public-rule approximations."""
    from agents.program_trading import MARKET_REG
    from agents.pt_dealer import AUCTION_CUTOFFS, LIMIT_BANDS
    src = ("seed: project static tables (public exchange rules; "
           "approximations disclosed in pt_dealer/program_trading)")
    today = _dt.date.today().isoformat()
    entries = []

    def add(category, market, value):
        entries.append({
            "id": f"{category}:{market}:v1",
            "category": category, "market": market, "value": value,
            "version": 1, "status": "active", "effective_date": today,
            "source": src, "approved_by": "seed", "approved_at": today,
        })

    for m, v in LIMIT_BANDS.items():
        add("limit_band", m, v)
    for m, v in AUCTION_CUTOFFS.items():
        add("auction_cutoff", m, v)
    for m, v in MARKET_REG.items():
        add("market_reg", m, {k: str(val) for k, val in v.items()})
    return entries


def load_registry(path: Path = REGISTRY_PATH) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    reg = {"entries": _seed_entries(), "pending": [], "log": []}
    save_registry(reg, path)
    return reg


def save_registry(reg: dict, path: Path = REGISTRY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(reg, indent=1, default=str))


def current(reg: dict, category: str | None = None,
            market: str | None = None) -> pd.DataFrame:
    rows = [e for e in reg["entries"] if e["status"] == "active"
            and (category is None or e["category"] == category)
            and (market is None or e["market"] == market)]
    return pd.DataFrame(rows)


def current_value(reg: dict, category: str, market: str, default=None):
    for e in reg["entries"]:
        if (e["status"] == "active" and e["category"] == category
                and e["market"] == market):
            return e["value"]
    return default


def history(reg: dict, category: str, market: str) -> pd.DataFrame:
    rows = [e for e in reg["entries"]
            if e["category"] == category and e["market"] == market]
    return pd.DataFrame(sorted(rows, key=lambda e: e["version"]))


def registry_version(reg: dict) -> str:
    """Content hash of ACTIVE entries — consumed by pt_dealer's
    rules_version so audit packs pin the registry state, not just the
    static tables."""
    import hashlib
    active = sorted((e["id"] for e in reg["entries"]
                     if e["status"] == "active"))
    payload = json.dumps(active) + json.dumps(
        [e["value"] for e in reg["entries"] if e["status"] == "active"],
        sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


# ──────────────────────────────── change workflow (human-gated) ──

def propose_change(reg: dict, category: str, market: str, new_value,
                   source: str, note: str = "",
                   notice_ref: str | None = None) -> dict:
    pid = f"P{len(reg['log']) + len(reg['pending']) + 1:04d}"
    prop = {"proposal_id": pid, "category": category, "market": market,
            "new_value": new_value,
            "old_value": current_value(reg, category, market),
            "source": source, "note": note, "notice_ref": notice_ref,
            "proposed_at": _dt.datetime.now().isoformat(timespec="seconds")}
    reg["pending"].append(prop)
    return prop


def pending(reg: dict) -> pd.DataFrame:
    return pd.DataFrame(reg["pending"])


def approve(reg: dict, proposal_id: str, approver: str,
            effective_date: str | None = None) -> dict:
    """Supersede the active entry, activate the new one (version+1),
    log the decision. The ONLY path by which a rule value changes."""
    prop = _pop_pending(reg, proposal_id)
    old_ver = 0
    for e in reg["entries"]:
        if (e["status"] == "active" and e["category"] == prop["category"]
                and e["market"] == prop["market"]):
            e["status"] = "superseded"
            old_ver = e["version"]
    new = {"id": f"{prop['category']}:{prop['market']}:v{old_ver + 1}",
           "category": prop["category"], "market": prop["market"],
           "value": prop["new_value"], "version": old_ver + 1,
           "status": "active",
           "effective_date": effective_date or _dt.date.today().isoformat(),
           "source": prop["source"], "approved_by": approver,
           "approved_at": _dt.datetime.now().isoformat(timespec="seconds")}
    reg["entries"].append(new)
    reg["log"].append({"action": "approve", "proposal": prop,
                       "by": approver, "at": new["approved_at"]})
    return new


def reject(reg: dict, proposal_id: str, approver: str,
           reason: str) -> dict:
    prop = _pop_pending(reg, proposal_id)
    rec = {"action": "reject", "proposal": prop, "by": approver,
           "reason": reason,
           "at": _dt.datetime.now().isoformat(timespec="seconds")}
    reg["log"].append(rec)
    return rec


def _pop_pending(reg: dict, proposal_id: str) -> dict:
    for i, p in enumerate(reg["pending"]):
        if p["proposal_id"] == proposal_id:
            return reg["pending"].pop(i)
    raise KeyError(f"no pending proposal {proposal_id}")


# ──────────────────────────── 2. notice triage (keyword engine) ──

# Multilingual term map. Deterministic and offline-testable by design:
# desk-safe default where LLM use is restricted. Terms are matched
# case-insensitively as substrings (CJK needs no tokenization for this).
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "short_sell": ["short sell", "short-sell", "short sale", "sbl",
                   "securities lending", "空売り", "融券", "借券", "賣空",
                   "공매도", "uptick"],
    "price_limit": ["price limit", "circuit breaker", "limit up",
                    "limit down", "値幅制限", "漲跌幅", "漲跌停", "서킷",
                    "vcm", "luld", "volatility interruption",
                    "daily price"],
    "lot_size": ["board lot", "lot size", "trading unit", "odd lot",
                 "売買単位", "交易單位", "最小交易", "매매단위", "zero board"],
    "auction": ["auction", "closing call", "opening call", "板寄せ",
                "集合競價", "收盤前", "동시호가", "cas ", "closing session",
                "pre-close"],
    "fees_tax": ["fee", "levy", "stamp duty", "transaction tax", "手数料",
                 "證交稅", "手續費", "인지세"],
    "settlement": ["settlement", "t+1", "t+2", "clearing", "決済", "交割",
                   "결제", "buy-in", "fails"],
    "session_hours": ["trading hours", "session", "half-day", "holiday",
                      "休場", "休市", "開市", "휴장", "typhoon",
                      "severe weather", "lunch"],
    "index_event": ["index review", "rebalanc", "constituent", "指數",
                    "採用銘柄", "리밸런싱", "inclusion"],
}

HIGH_CATEGORIES = {"short_sell", "price_limit", "lot_size", "auction",
                   "session_hours"}


def classify_notice(title: str, body: str = "") -> dict:
    text = f"{title} {body}".lower()
    cats, terms = [], []
    for cat, kws in CATEGORY_KEYWORDS.items():
        hit = [k for k in kws if k.lower() in text]
        if hit:
            cats.append(cat)
            terms.extend(hit)
    relevance = ("HIGH" if any(c in HIGH_CATEGORIES for c in cats)
                 else "MED" if cats else "IGNORE")
    return {"categories": cats, "relevance": relevance,
            "matched_terms": terms}


def triage_notices(notices: list[dict]) -> pd.DataFrame:
    """notices: [{source, date, title, url, body?}] -> ranked table."""
    rows = []
    for n in notices:
        c = classify_notice(n.get("title", ""), n.get("body", ""))
        rows.append({**{k: n.get(k, "") for k in
                        ("source", "date", "title", "url")}, **c})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    order = {"HIGH": 0, "MED": 1, "IGNORE": 2}
    return (df.assign(_o=df["relevance"].map(order))
              .sort_values(["_o", "date"], ascending=[True, False])
              .drop(columns="_o").reset_index(drop=True))


def llm_summarize_hook(notice: dict, llm=None) -> str | None:
    """The optional LLM slot. `llm` is any callable(prompt)->str the
    deployment provides (desk-approved endpoint, or none). Returns None
    when no LLM is configured — the digest then uses the deterministic
    template. This function is deliberately trivial: the design point
    is WHERE the hook sits (after fetch, before human review; public
    notice text only, never client or order data)."""
    if llm is None:
        return None
    return llm("Summarize this exchange notice for a program-trading "
               "desk in <=2 sentences, flagging any rule change and its "
               f"effective date:\n{notice.get('title','')}\n"
               f"{notice.get('body','')[:2000]}")


# ─────────────────────────────────────────────── notice fetchers ──

def _get_json(url: str, timeout: int = 20):
    req = urllib.request.Request(url, headers=_UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def parse_twse_news(payload: list) -> list[dict]:
    return [{"source": "TWSE", "date": n.get("Date", ""),
             "title": n.get("Title", ""), "url": n.get("Url", "")}
            for n in payload]


def fetch_twse_news() -> list[dict]:
    return parse_twse_news(
        _get_json("https://openapi.twse.com.tw/v1/news/newsList"))


def parse_jpx_news(payload: list) -> list[dict]:
    out = []
    for n in payload:
        d = n.get("updated_date", {}) or {}
        date = (f"{d.get('year','')}{d.get('month','')}{d.get('day','')}"
                if isinstance(d, dict) else str(d))
        out.append({"source": "JPX", "date": date,
                    "title": n.get("title", ""),
                    "url": "https://www.jpx.co.jp" + n.get("url", "")})
    return out


def fetch_jpx_news() -> list[dict]:
    return parse_jpx_news(
        _get_json("https://www.jpx.co.jp/english/news/news_ym_01.json"))


def parse_nse_circulars(payload: dict) -> list[dict]:
    return [{"source": "NSE", "date": n.get("cirDate", ""),
             "title": f"[{n.get('circCategory','')}] {n.get('sub','')}",
             "url": n.get("circFilelink", "")}
            for n in payload.get("data", [])]


def fetch_nse_circulars() -> list[dict]:
    return parse_nse_circulars(
        _get_json("https://www.nseindia.com/api/circulars"))


NOTICE_SOURCES: dict[str, dict] = {
    "TWSE": {"lang": "zh", "status": "IMPLEMENTED",
             "feed": "openapi.twse.com.tw/v1/news/newsList"},
    "JPX": {"lang": "ja/en", "status": "IMPLEMENTED",
            "feed": "jpx.co.jp/english/news/news_ym_01.json"},
    "NSE": {"lang": "en", "status": "IMPLEMENTED",
            "feed": "nseindia.com/api/circulars"},
    "TPEx": {"lang": "zh", "status": "PROTOCOL (403 from sandbox; desk "
             "network fetches tpex.org.tw news)"},
    "HKEX": {"lang": "en/zh", "status": "PROTOCOL (JS-rendered; desk "
             "uses HKEX news/circular subscription email or API)"},
    "KRX": {"lang": "ko/en", "status": "PROTOCOL (desk fetches KRX "
            "notice board / KIND)"},
    "SGX": {"lang": "en", "status": "PROTOCOL (api.sgx.com 403 from "
            "sandbox)"},
    "SET": {"lang": "th/en", "status": "PROTOCOL (403 from sandbox)"},
}


# ─────────────────────────────────────────────── 3. daily digest ──

def daily_digest(triaged: pd.DataFrame, reg: dict,
                 date: str | None = None) -> str:
    date = date or _dt.date.today().isoformat()
    lines = [f"# Reg-Watch daily digest — {date}", ""]
    pend = pending(reg)
    lines.append(f"Registry: {sum(e['status']=='active' for e in reg['entries'])} "
                 f"active rules, version {registry_version(reg)}; "
                 f"{len(pend)} pending proposal(s) awaiting review.")
    lines.append("")
    if not pend.empty:
        lines.append("## PENDING APPROVALS (human action required)")
        for _, p in pend.iterrows():
            lines.append(f"- **{p['proposal_id']}** {p['category']} / "
                         f"{p['market']}: {p['old_value']} → "
                         f"{p['new_value']}  ({p['source']})")
        lines.append("")
    for level, label in (("HIGH", "## HIGH relevance — read today"),
                         ("MED", "## MED relevance — skim")):
        sub = triaged[triaged["relevance"] == level] if not triaged.empty \
            else pd.DataFrame()
        if sub.empty:
            continue
        lines.append(label)
        for _, n in sub.iterrows():
            cats = ",".join(n["categories"])
            lines.append(f"- [{n['source']} {n['date']}] {n['title']} "
                         f"({cats}) {n['url']}")
        lines.append("")
    ignored = 0 if triaged.empty else int((triaged["relevance"] ==
                                           "IGNORE").sum())
    lines.append(f"*{ignored} notices classified IGNORE (kept in cache, "
                 "not shown). Keyword engine is deterministic; LLM "
                 "summaries appear here only where a desk-approved "
                 "endpoint is configured.*")
    return "\n".join(lines)


# ════════════════════════ 7m: proactive insight layer ════════════════════
# Raw notices are INPUT, not output. Pipeline:
#   fetch -> dedup vs seen-state -> cluster into STORIES -> score
#   importance (explainable, deterministic) -> flash brief: headline +
#   what-it-means-for-execution + drill-down links to the underlying
#   notices. Traders read stories; notices are one click deeper.

import hashlib as _hashlib
import re as _re


def notice_id(n: dict) -> str:
    return _hashlib.sha256(
        f"{n.get('source')}|{n.get('date')}|{n.get('title')}"
        .encode()).hexdigest()[:16]


def new_notices(notices: list[dict], seen_ids: set[str]) -> list[dict]:
    return [n for n in notices if notice_id(n) not in seen_ids]


_CODE_PAT = _re.compile(
    r"\(code:? ?[0-9A-Za-z]+\)|\b\d[\d,./:-]*\b|（[^）]*）", _re.I)


def story_key(source: str, title: str) -> str:
    """Cluster key: source + title with digits/codes/dates stripped —
    'Daily Price Limits to be Broadened : 3 issues' and ': 1 issue'
    collapse into one story."""
    t = _re.sub(r"^\[[^\]]*\]\s*", "", title.lower())   # dept prefixes
    t = _CODE_PAT.sub("", t)
    t = _re.sub(r"\bissues?\b|\bupdate\b|-", "", t)
    return f"{source}:" + _re.sub(r"\s+", " ", t).strip()[:80]


_SINGLE_STOCK = ["(code", "newly listing", "股份有限公司", "公司",
                 "warrant", "individual", "issue"]
_MARKET_WIDE = ["introduction", "revision", "amendment", "all ",
                "segment", "market", "rules", "regulation", "framework",
                "制度", "modalities", "reform", "regime"]


def detect_scope(title: str) -> str:
    t = title.lower()
    if any(k in t for k in _MARKET_WIDE):
        return "market-wide"
    if any(k in t for k in _SINGLE_STOCK):
        return "single-stock"
    return "subset"


IMPACT_NOTES = {
    "price_limit": "Band mechanics change how limit-locked names queue; "
                   "re-check limit_proximity thresholds before working "
                   "affected names.",
    "auction": "Close/open auction mechanics drive MOC benchmarks and "
               "cutoff discipline — schedule and submission logic may "
               "need re-dating.",
    "session_hours": "Session/holiday changes move every cutoff in the "
                     "cascade run-sheet for that market.",
    "short_sell": "Short-sell/SBL rule shifts change sell-side "
                  "eligibility, locate needs, and hedge feasibility.",
    "lot_size": "Lot/unit changes alter order slicing and odd-lot "
                "handling; basket files priced on old lots will fail "
                "validation.",
    "settlement": "Settlement changes move value dates, funding, and "
                  "recon expectations.",
    "fees_tax": "Cost-model inputs change; update explicit-cost tables.",
    "index_event": "Index flow event — hand to the rebalance desk "
                   "pipeline (screener/flow sim).",
}

CATEGORY_WEIGHT = {"price_limit": 3, "auction": 3, "session_hours": 3,
                   "short_sell": 3, "settlement": 2, "lot_size": 2,
                   "index_event": 2, "fees_tax": 1}
SCOPE_MULT = {"market-wide": 3, "subset": 2, "single-stock": 1}
_MOCK_TERMS = ("mock", "testing", "test ", "模擬", "simulation")


def cluster_stories(triaged: pd.DataFrame) -> list[dict]:
    """Relevant notices -> deduplicated stories with drill-down links."""
    rel = triaged[triaged["relevance"] != "IGNORE"] if not triaged.empty \
        else pd.DataFrame()
    stories: dict[str, dict] = {}
    for _, n in rel.iterrows():
        k = story_key(n["source"], n["title"])
        s = stories.setdefault(k, {
            "key": k, "source": n["source"], "headline": n["title"],
            "categories": [], "scope": detect_scope(n["title"]),
            "n_notices": 0, "first_date": n["date"],
            "last_date": n["date"], "links": []})
        s["n_notices"] += 1
        s["categories"] = sorted(set(s["categories"]) |
                                 set(n["categories"]))
        s["first_date"] = min(s["first_date"], n["date"])
        s["last_date"] = max(s["last_date"], n["date"])
        s["links"].append({"date": n["date"], "title": n["title"],
                           "url": n["url"]})
    return list(stories.values())


def score_story(story: dict, basket_names: list[str] | None = None) -> dict:
    """Deterministic, explainable importance score -> tier + reasons."""
    reasons = []
    cat_pts = max((CATEGORY_WEIGHT.get(c, 1) for c in
                   story["categories"]), default=1)
    reasons.append(f"category {'/'.join(story['categories'])} "
                   f"(+{cat_pts})")
    mult = SCOPE_MULT[story["scope"]]
    reasons.append(f"{story['scope']} (x{mult})")
    score = cat_pts * mult
    title_l = story["headline"].lower()
    if any(m in title_l for m in _MOCK_TERMS):
        score *= 0.6
        reasons.append("mock/test session (x0.6) — but a mock is the "
                       "PRECURSOR of a real change: note the go-live")
    if story["n_notices"] > 1:
        score += 1
        reasons.append(f"{story['n_notices']} related notices (+1): "
                       "the exchange is drumbeating this")
    if basket_names:
        hit = [b for b in basket_names if b.lower() in title_l]
        if hit:
            score += 3
            reasons.append(f"names in YOUR basket: {hit} (+3)")
    tier = ("FLASH" if score >= 8 else
            "NOTABLE" if score >= 4 else "ROUTINE")
    impact = " ".join(IMPACT_NOTES[c] for c in story["categories"]
                      if c in IMPACT_NOTES) or "Monitor."
    return {**story, "score": round(score, 1), "tier": tier,
            "reasons": reasons, "impact": impact}


def flash_brief(stories: list[dict], top_n: int = 6,
                basket_names: list[str] | None = None) -> str:
    """The proactive trader-facing artifact: ranked stories, one glance
    each, links one click deeper. Only FLASH/NOTABLE appear."""
    scored = sorted((score_story(s, basket_names) for s in stories),
                    key=lambda s: -s["score"])
    hot = [s for s in scored if s["tier"] in ("FLASH", "NOTABLE")][:top_n]
    if not hot:
        return ""
    lines = ["# ⚡ Reg-Watch flash brief", ""]
    for s in hot:
        badge = "🔴 FLASH" if s["tier"] == "FLASH" else "🟡 NOTABLE"
        lines.append(f"## {badge} [{s['source']}] {s['headline']}")
        lines.append(f"**Why it matters:** {s['impact']}")
        lines.append(f"*Scoring: {'; '.join(s['reasons'])} — score "
                     f"{s['score']}. {s['n_notices']} notice(s), "
                     f"{s['first_date']}→{s['last_date']}.*")
        for l in s["links"][:5]:
            lines.append(f"- [{l['date']}] [{l['title'][:90]}]"
                         f"({l['url']})")
        if len(s["links"]) > 5:
            lines.append(f"- …{len(s['links'])-5} more in cache")
        lines.append("")
    lines.append(f"*{len(scored)-len(hot)} lower-scored stories in the "
                 "daily digest. Scores are deterministic and "
                 "explainable — every ranking shows its reasons.*")
    return "\n".join(lines)


def parse_sgx_circulars(payload: dict) -> list[dict]:
    out = []
    for n in payload.get("data", []):
        try:
            ts = int(n.get("documentDate", 0)) / 1000
            date = _dt.datetime.utcfromtimestamp(ts).strftime("%Y%m%d")
        except Exception:
            date = ""
        out.append({"source": "SGX", "date": date,
                    "title": f"{n.get('subject','')} "
                             f"({n.get('companyName','')})".strip(),
                    "url": "https://www.sgx.com/regulation/circulars"})
    return out


def fetch_sgx_circulars(pagesize: int = 50) -> list[dict]:
    req = urllib.request.Request(
        f"https://api.sgx.com/circulars/v1.0?pagesize={pagesize}",
        headers={**_UA, "Referer": "https://www.sgx.com/"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return parse_sgx_circulars(json.load(r))


NOTICE_SOURCES["SGX"] = {"lang": "en", "status": "IMPLEMENTED",
                         "feed": "api.sgx.com/circulars/v1.0 (needs "
                                 "Referer header)"}
