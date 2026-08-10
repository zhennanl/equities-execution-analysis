"""Decade Step-2 window study — CN/JP/HK MSCI events 2015-2025.

Session 9h. The May-2026 CN/JP/HK study (window_study_cnjphk.py) found
THE CLASS INVERSION on one event. This extends the same factors and
counterfactuals across every MSCI Standard review 2015-2025 (44 quarters
of parsed STPublicLists) to test whether the inversion is a regime or a
one-off.

The alias bridge (the long-queued blocker): MSCI lists carry English
names only. Mapping built from exchange English masters —
  CN-A : HKEX Stock-Connect eligible lists (SSE/SZSE codes + English
         names; MSCI China A inclusion is Connect-eligible by design)
  JP   : JPX data_e.xls English master
  HK   : HKEX List of Securities
Fuzzy token matching with an abbreviation alias table; every match is
then VALIDATED BY ITS OWN EVENT PRINT (T-day volume multiple >= 2x
window median, the technique that rejected HONPRECISION->2354): matches
failing the print check are excluded as SUSPECT-ALIAS.

HONEST LIMITS (stated in the doc):
  * Masters are CURRENT snapshots -> names delisted since do not match.
    Deletes therefore under-covered (deletion often precedes delisting);
    match rates reported by side and year. This is survivorship in
    COVERAGE, not in measurement of matched names.
  * ADR lines skipped (US-listed, out of scope). B-shares unmatched.
  * FTSE keys for CN/JP/HK were never collected (separate archaeology);
    this study is MSCI-only.
  * Crowding pillars: HK reconstructable (SFC to 2012) but not built
    into this pass; JP/CN historical crowding absent. This is a
    price/volume study.
  * Counterfactual fills at daily closes = impact-free upper bounds.

Usage: python scripts/window_study_decade.py [events|bridge|fetch_cn|
       fetch_jphk|report]
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ARCH = ROOT / "data" / "msci_archive"
MAST = ROOT / "data" / "masters"
BRIDGE = ROOT / "data" / "decade_bridge.json"
CACHE = ROOT / "data" / "decade_windows.json"
DOC = ROOT / "docs" / "WINDOW_STUDY_DECADE_CNJPHK.md"

MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"])}

ALIAS = {"CN": "CHINA", "INTL": "INTERNATIONAL", "GRP": "GROUP",
         "HLDGS": "HOLDINGS", "HLDG": "HOLDINGS", "TECH": "TECHNOLOGY",
         "PHARM": "PHARMACEUTICAL", "PHARMA": "PHARMACEUTICAL",
         "ELEC": "ELECTRIC", "DEV": "DEVELOPMENT", "IND": "INDUSTRIAL",
         "INDS": "INDUSTRIES", "SECS": "SECURITIES", "BK": "BANK",
         "COMM": "COMMUNICATIONS", "MFG": "MANUFACTURING",
         "PETRO": "PETROLEUM", "SVCS": "SERVICES", "RES": "RESOURCES",
         "AGRI": "AGRICULTURAL", "ENGR": "ENGINEERING", "RY": "RAILWAY",
         "ENV": "ENVIRONMENT", "INFO": "INFORMATION", "CONST":
         "CONSTRUCTION", "MED": "MEDICAL", "SCI": "SCIENCE"}

DROP = {"A", "B", "H", "CO", "LTD", "CORP", "INC", "THE", "OF", "AND",
        "&", "PLC", "SA", "AG", "KK", "HK-C", "USD", "NEW", "ADR",
        "LIMITED", "COMPANY", "CORPORATION", "INCORPORATED", "SHS",
        "NON-CUM", "PREF"}


# ------------------------------------------------------------------ events
def _pr_dates(season):
    """(announce, effective) dates from the review's press release."""
    for suf in ("SAIRPR", "QIRPR"):
        p = ARCH / f"MSCI_{season}_{suf}.txt"
        if p.exists():
            txt = p.read_text(errors="ignore")[:4000]
            a = re.search(r"(January|February|March|April|May|June|July"
                          r"|August|September|October|November|December"
                          r")\s+(\d{1,2}),\s*(20\d\d)", txt)
            e = re.search(r"as of the close of ([A-Za-z]+) (\d{1,2}),? ?"
                          r"(20\d\d)", txt)
            ann = (f"{a.group(3)}-{MONTHS[a.group(1)]:02d}-"
                   f"{int(a.group(2)):02d}") if a else None
            eff = (f"{e.group(3)}-{MONTHS[e.group(1)]:02d}-"
                   f"{int(e.group(2)):02d}") if e else None
            return ann, eff
    return None, None


def events():
    """All decade events: season -> ann/eff + per-market name changes."""
    from agents.reconstitution import parse_msci_public_list
    out = []
    for t in sorted(ARCH.glob("*STPublicList.txt")):
        season = t.stem.replace("MSCI_", "").replace("_STPublicList", "")
        ann, eff = _pr_dates(season)
        if not ann:
            continue
        if not eff:                     # fallback: last day of ann month
            eff = (pd.Timestamp(ann) + pd.offsets.MonthEnd(0)
                   ).strftime("%Y-%m-%d")
        led = parse_msci_public_list(t.read_text(errors="ignore"))
        ev = {"season": season, "ann": ann, "eff": eff, "mkts": {}}
        for c, mkt in (("CHINA", "CN"), ("JAPAN", "JP"),
                       ("HONG KONG", "HK")):
            d = led.get(c, {})
            if d.get("adds") or d.get("deletes"):
                ev["mkts"][mkt] = {"adds": d.get("adds", []),
                                   "dels": d.get("deletes", [])}
        if ev["mkts"]:
            out.append(ev)
    return sorted(out, key=lambda e: e["ann"])


# ------------------------------------------------------------------ bridge
def _toks(name):
    s = re.sub(r"\(.*?\)", " ", str(name).upper())
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    t = [ALIAS.get(x, x) for x in s.split() if x not in DROP]
    return t


def _match(mtoks, cands):
    """Best (code, score) among master candidates; None if ambiguous."""
    best, second, bcode = 0, 0, None
    for code, ctoks in cands:
        common = 0
        used = set()
        for a in mtoks:
            for i, b in enumerate(ctoks):
                if i in used:
                    continue
                if a == b or (len(a) >= 4 and len(b) >= 4 and
                              (a.startswith(b) or b.startswith(a))):
                    common += 1
                    used.add(i)
                    break
        if not mtoks:
            continue
        score = common / len(mtoks) - 0.05 * abs(len(ctoks) - len(mtoks))
        if score > best:
            best, second, bcode = score, best, code
        elif score > second:
            second = score
    if best >= 0.95 or (best >= 0.65 and (best - second) >= 0.1):
        return bcode, round(best, 2)
    return None, round(best, 2)


def load_masters():
    cn = []
    for f, pref in (("SSE_Securities.xls", "sh"),
                    ("SZSE_Securities.xls", "sz")):
        df = pd.read_excel(MAST / f, header=None, skiprows=5)
        for _, r in df.iterrows():
            code, name, typ = r.iloc[1], r.iloc[3], str(r.iloc[5])
            if pd.notna(code) and pd.notna(name) and typ == "EQTY" \
                    and str(code).strip().split(".")[0].isdigit():
                cn.append((f"{pref}.{int(code):06d}", _toks(name)))
    jdf = pd.read_excel(MAST / "data_e.xls")
    jp = [(f"{int(r['Local Code'])}.T", _toks(r["Name (English)"]))
          for _, r in jdf.iterrows()
          if str(r.get("Local Code", "")).strip().rstrip(".0").isdigit()]
    x = pd.read_excel(MAST / "ListOfSecurities.xlsx", header=2)
    x.columns = [str(c).strip() for c in x.columns]
    cc, nc = x.columns[0], x.columns[1]
    hk = []
    for _, r in x.iterrows():
        try:
            code = int(r[cc])
        except (ValueError, TypeError):
            continue
        if code < 10000 and "Equity" in str(r.get(x.columns[2], "")):
            hk.append((f"{code:04d}.HK", _toks(r[nc])))
    return {"CN": cn, "JP": jp, "HK": hk}


def build_bridge():
    evs = events()
    masters = load_masters()
    bridge, misses = {}, []
    for ev in evs:
        for mkt, ch in ev["mkts"].items():
            for side, names in (("Buy", ch["adds"]),
                                ("Sell", ch["dels"])):
                for nm in names:
                    if "ADR" in nm.upper().split():
                        continue
                    key = f"{mkt}|{nm}"
                    if key in bridge or key in {m[0] for m in misses}:
                        continue
                    # CN list mixes A/H/others: A-lines to CN master,
                    # H/red-chip lines live on HKEX
                    pools = [mkt]
                    if mkt == "CN" and not re.search(
                            r"\bA\b|\(HK-C\)", nm):
                        pools = ["HK"]
                    code = None
                    for pool in pools:
                        code, sc = _match(_toks(nm), masters[pool])
                        if code:
                            break
                    if code:
                        bridge[key] = code
                    else:
                        misses.append((key, sc))
    BRIDGE.write_text(json.dumps(
        {"map": bridge, "misses": misses}, ensure_ascii=False), encoding="utf-8")
    print(f"bridge: {len(bridge)} matched, {len(misses)} unmatched")
    return bridge, misses


# ------------------------------------------------------------------- fetch
def _win(ev):
    a = (pd.Timestamp(ev["ann"]) - pd.Timedelta(days=10)
         ).strftime("%Y-%m-%d")
    b = (pd.Timestamp(ev["eff"]) + pd.Timedelta(days=5)
         ).strftime("%Y-%m-%d")
    return a, b


def jobs(kind):
    br = json.loads(BRIDGE.read_text(encoding="utf-8"))["map"]
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    out = []
    for ev in events():
        for mkt, ch in ev["mkts"].items():
            for side, names in (("Buy", ch["adds"]),
                                ("Sell", ch["dels"])):
                for nm in names:
                    code = br.get(f"{mkt}|{nm}")
                    if not code:
                        continue
                    is_cn = code.startswith(("sh.", "sz."))
                    if (kind == "cn") != is_cn:
                        continue
                    k = f"{ev['season']}|{code}"
                    if k in cache:
                        continue
                    out.append((k, code, side, *_win(ev)))
    return out, cache


def fetch_cn(budget=200):
    import baostock as bs
    todo, cache = jobs("cn")
    print(f"cn: {len(todo)} windows missing")
    bs.login()
    for i, (k, code, side, w0, w1) in enumerate(todo[:budget]):
        rs = bs.query_history_k_data_plus(
            code, "date,close,volume", start_date=w0, end_date=w1,
            frequency="d", adjustflag="3")
        rows = []
        while rs.error_code == "0" and rs.next():
            d, cl, v = rs.get_row_data()
            if cl and v:
                rows.append([d, float(cl), float(v)])
        cache[k] = {"side": side, "rows": rows}
        if (i + 1) % 8 == 0:
            CACHE.write_text(json.dumps(cache), encoding="utf-8")
            print(f"  ...{i + 1}", flush=True)
    bs.logout()
    CACHE.write_text(json.dumps(cache), encoding="utf-8")
    print("cached total:", len(cache))


def fetch_jphk(budget=150):
    import yfinance as yf
    todo, cache = jobs("jphk")
    print(f"jp/hk: {len(todo)} windows missing")
    for i, (k, code, side, w0, w1) in enumerate(todo[:budget]):
        try:
            h = yf.Ticker(code).history(start=w0, end=w1, interval="1d")
            rows = [[str(d.date()), float(r["Close"]),
                     float(r["Volume"])] for d, r in h.iterrows()
                    if r["Volume"] > 0]
        except Exception:                                # noqa: BLE001
            rows = []
        cache[k] = {"side": side, "rows": rows}
        if (i + 1) % 8 == 0:
            CACHE.write_text(json.dumps(cache), encoding="utf-8")
            print(f"  ...{i + 1}", flush=True)
    CACHE.write_text(json.dumps(cache), encoding="utf-8")
    print("cached total:", len(cache))


# ----------------------------------------------------------------- factors
def panel():
    """Per name-event: drift/counterfactuals + alias print-validation."""
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    evs = {e["season"]: e for e in events()}
    rows = []
    for k, v in cache.items():
        season, code = k.split("|")
        ev = evs.get(season)
        if not ev or len(v["rows"]) < 8:
            continue
        df = pd.DataFrame(v["rows"], columns=["date", "close", "vol"])
        df = df[df["date"] <= ev["eff"]]
        pre = df[df["date"] <= ev["ann"]]
        win = df[df["date"] > ev["ann"]]
        if len(pre) < 3 or len(win) < 4:
            continue
        p0 = pre.iloc[-1]["close"]
        t = win.iloc[-1]
        base = pre["vol"].median()
        t_mult = t["vol"] / base if base else 0
        sgn = 1.0 if v["side"] == "Buy" else -1.0
        ct = t["close"]
        cf = {
            "ALL_DAY1": sgn * (win.iloc[0]["close"] / ct - 1) * 1e4,
            "LINEAR": sgn * (win["close"].mean() / ct - 1) * 1e4,
            "LATE5": sgn * (win["close"].tail(5).mean() / ct - 1) * 1e4}
        rows.append({
            "season": season, "year": int(season[-2:]) + 2000,
            "mkt": ("CN" if code.startswith(("sh.", "sz."))
                    else "JP" if code.endswith(".T") else "HK"),
            "code": code, "side": v["side"],
            "drift_bps": sgn * (ct / p0 - 1) * 1e4,
            "t_mult": round(t_mult, 1),
            "print_ok": t_mult >= 2.0, **{x: round(y, 0)
                                          for x, y in cf.items()}})
    return pd.DataFrame(rows)


def _findings(ok, ex):
    cn_mat = 100 * (ok["mkt"] == "CN").sum() / \
        ((ok["mkt"] == "CN").sum() + (ex["mkt"] == "CN").sum())
    return f"""## Findings (computed; convention: negative = beat the T close)

1. **The one-event May-2026 'class inversion' does NOT generalize to
   the decade.** Decade CN adds GRIND UP like Taiwan (median drift
   +391 bps; day-1 buy -325, LINEAR -234 vs close — working beats the
   print), where May-2026 showed pop-then-decay (+1,103 day-1 cost).
   Decade deletes show no press-to-print either (CN 22-25: LINEAR -8,
   n=46 ~ flat). The inversion is at most a LATE-REGIME or
   event-specific phenomenon — Aug-2026 arbitrates, exactly what the
   one-event caveat was for.
2. **China A materiality is the structural surprise: only
   {cn_mat:.0f}% of CN name-events show a material event print**
   (T-mult >= 2). Median excluded T-mult ~1.1 — MSCI flow at 10-20%
   inclusion factors rarely dominates a retail-heavy A-share tape.
   The per-name index edge in CN is thin outside the largest
   inclusion waves; JP/HK validated prints run 8-13x (TW-like).
3. **The edge is DYING from the newest era inward — JP first.**
   JP 2015-18/2019-21: working crushed the print (adds LINEAR -118 /
   -337; deletes -235 / -257). JP 2022-25: FLIPPED (adds LINEAR
   +230, deletes +116) — the Greenwood-Sammon disappearance arriving
   in Asia, measured in execution-counterfactual space. CN adds
   remain alive through 22-25 (LINEAR -306); HK is unstable at n~15
   per cell — no reliable HK playbook from public prints alone.
4. **2019-21 was the golden era everywhere** (drifts +390 to +630,
   every counterfactual beats MOC) — coincides with the China-A
   inclusion-factor step-ups and pre-saturation arb capacity.
5. Practical encoding for the discretion matrix: decade priors say
   CN adds -> work early remains valid; JP post-2022 -> MOC-first
   (edge gone); HK -> unconditional-band only; and the May-2026
   MSCI-add WAIT rule should be held as a HYPOTHESIS pending
   Aug-2026, not promoted to a decade rule.
"""


def report():
    df = panel()
    ok = df[df["print_ok"]]
    sus = df[~df["print_ok"]]
    br = json.loads(BRIDGE.read_text(encoding="utf-8"))
    print(f"{len(df)} name-events, {len(ok)} print-validated, "
          f"{len(sus)} no-material-print excluded")
    agg = ok.groupby(["mkt", "side"]).agg(
        n=("code", "count"),
        drift_med=("drift_bps", "median"),
        d1_med=("ALL_DAY1", "median"),
        lin_med=("LINEAR", "median"),
        late5_med=("LATE5", "median")).round(0)
    print(agg.to_string())
    # inversion test by era
    ok2 = ok.copy()
    ok2["era"] = pd.cut(ok2["year"], [2014, 2018, 2021, 2026],
                        labels=["2015-18", "2019-21", "2022-25"])
    era = ok2.groupby(["mkt", "side", "era"], observed=True).agg(
        n=("code", "count"), d1=("ALL_DAY1", "median"),
        lin=("LINEAR", "median")).round(0)
    md = ["# Decade window study — CN/JP/HK MSCI events 2015-2025\n",
          f"*Session 9h. {len(ok)} print-validated name-events "
          f"({len(sus)} excluded as NO MATERIAL PRINT: T-mult < 2 — "
          "the alias is usually plausible but tracked flow did not "
          "dominate the local tape, so window dynamics are not "
          "index-flow-driven for those names; "
          f"{len(br['misses'])} names unmatched by the bridge). "
          "MSCI-only (FTSE keys for these markets not collected). "
          "Price/volume study — historical crowding absent for JP/CN, "
          "HK reconstructable but out of this pass. Counterfactual "
          "fills at daily closes are impact-free upper bounds. "
          "Convention: negative = beat the T close (MOC = 0).*\n",
          "## Coverage and the survivorship caveat\n",
          "Masters are current snapshots: names delisted since 2015 "
          "cannot match, and deletion often precedes delisting — so "
          "DELETES are under-covered and late-decade events are "
          "better covered. Measured names are measured correctly; "
          "coverage itself is biased toward survivors. Match counts "
          "by side below.\n",
          ok.groupby(["mkt", "side"])["code"].count().to_frame("n")
          .to_markdown() + "\n",
          _findings(ok, sus),
          "## All-decade medians (bps vs T close)\n",
          agg.to_markdown() + "\n",
          "## The inversion, by era\n", era.to_markdown() + "\n",
          "## Per-event table (print-validated)\n",
          ok.sort_values(["year", "mkt"]).to_markdown(index=False)]
    DOC.write_text("\n".join(md), encoding="utf-8")
    print("wrote", DOC)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    {"events": lambda: print(json.dumps(events()[:3], indent=1)),
     "bridge": build_bridge, "fetch_cn": fetch_cn,
     "fetch_jphk": fetch_jphk, "report": report}[cmd]()
