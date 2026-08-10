"""STAGE 1 of the APAC screen chain: size only (c-165).

Bill's design, and it is the right one: do not fetch float,
ATVR, foreign room or anything else for a whole market. Fetch
ONLY what §2.2.3 needs — full market cap — for every listed
name, rank, cut, and then re-fetch the expensive attributes for
the shortlist alone. In Taiwan that took 1,955 names down to
~425 before any costly call was made.

WHY THIS IS NOW POSSIBLE OUTSIDE TAIWAN (c-164 probe):
Yahoo's v7/finance/quote returns 500 symbols per call carrying
marketCap, sharesOutstanding and price. All of Japan is nine
requests. It needs a crumb; without one it is a flat 401.

TWO TRAPS, both found by probing and both handled below:

1. DEPOSITARY RECEIPTS. The Thai screener's top names are
   NVDA80.BK, KO80.BK, BRKB80.BK — Thai DRs over foreign
   parents, and Yahoo reports the PARENT's market cap. Left
   in, NVIDIA would rank first in Thailand and the cutoff walk
   would be nonsense. DRs are excluded on currency mismatch,
   name pattern, and (where a master exists) absence from the
   exchange's own list.

2. THE SCREENER OVER-COUNTS. Taiwan's region query returns
   19,535 rows against 1,955 real listings — warrants, ETFs and
   funds leak through despite quoteType=EQUITY. So the screener
   is used ONLY where no exchange master exists; where a master
   is available it wins.

SURVIVORSHIP, stated once and carried in the output: Yahoo
lists the living. This file supports the FORWARD call. It does
NOT support a deletion backtest, because the deleted names are
exactly the ones Yahoo has dropped. Taiwan and India keep the
archival day-files for that.

Run:
  py scripts\\apac_size_harvest.py                  (all)
  py scripts\\apac_size_harvest.py Japan Korea      (some)
  py scripts\\apac_size_harvest.py shortlist Japan 5.0
Out:
  data/apac_size/<Market>.json      every name, cap in USD
  data/apac_shortlist/<Market>.json the band, for stage 2
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "apac_size"
SHORT = ROOT / "data" / "apac_shortlist"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# region code, Yahoo suffix, local currency
MARKETS = {
    "Japan": ("jp", ".T", "JPY"),
    "HongKong": ("hk", ".HK", "HKD"),
    "China": ("cn", ".SS", "CNY"),
    "Korea": ("kr", ".KS", "KRW"),
    "Thailand": ("th", ".BK", "THB"),
    "Malaysia": ("my", ".KL", "MYR"),
    "Indonesia": ("id", ".JK", "IDR"),
    "Singapore": ("sg", ".SI", "SGD"),
    "India": ("in", ".NS", "INR"),
    "Australia": ("au", ".AX", "AUD"),
    "NewZealand": ("nz", ".NZ", "NZD"),
    "Taiwan": ("tw", ".TW", "TWD"),
}

# name fragments that mark a depositary receipt or a fund
_JUNK = re.compile(
    r"\b(DR|SDR|ADR|GDR|DEPOSITARY|ETF|FUND|TRUST INDEX|INDEX "
    r"FUND|WARRANT|RIGHTS|PREF|PREFERENCE)\b", re.I)


def session():
    """A crumbed session. Two extra calls, then 500 names each."""
    import requests
    s = requests.Session()
    s.headers.update(UA)
    s.get("https://fc.yahoo.com", timeout=20)
    c = s.get("https://query1.finance.yahoo.com/v1/test/getcrumb",
              timeout=20).text.strip()
    if not c or "<" in c:
        raise SystemExit("no crumb — Yahoo refused the session")
    return s, c


def fx_usd(s, ccy):
    """Local units per USD."""
    if ccy == "USD":
        return 1.0
    j = s.get("https://query1.finance.yahoo.com/v8/finance/chart/"
              f"USD{ccy}=X?range=5d&interval=1d", timeout=25).json()
    r = (j.get("chart", {}).get("result") or [None])[0]
    return r["meta"]["regularMarketPrice"] if r else None


def quotes(s, crumb, syms):
    """Batched quote. 500 is proven; we send 400 for headroom."""
    out = {}
    for i in range(0, len(syms), 400):
        chunk = syms[i:i + 400]
        r = s.get("https://query1.finance.yahoo.com/v7/finance/"
                  f"quote?symbols={','.join(chunk)}&crumb={crumb}",
                  timeout=45)
        if r.status_code != 200:
            print(f"    batch {i}: HTTP {r.status_code}")
            time.sleep(3)
            continue
        for q in r.json()["quoteResponse"]["result"]:
            out[q["symbol"]] = q
        print(f"    {min(i + 400, len(syms))}/{len(syms)}",
              flush=True)
        time.sleep(0.4)
    return out


def _master(market):
    """The exchange's own listing file, where one exists. Always
    preferred over the screener — see trap 2."""
    import io
    import requests
    try:
        if market == "Japan":
            import pandas as pd
            x = requests.get(
                "https://www.jpx.co.jp/markets/statistics-equities"
                "/misc/tvdivq0000001vg2-att/data_j.xls",
                headers=UA, timeout=90).content
            df = pd.read_excel(io.BytesIO(x))
            return [f"{c}.T" for c in
                    df.iloc[:, 1].astype(str).str.strip()
                    if c.isdigit() and len(c) == 4]
        if market == "Taiwan":
            out = []
            for u, k in [
                ("https://openapi.twse.com.tw/v1/opendata/"
                 "t187ap03_L", "公司代號"),
                ("https://www.tpex.org.tw/openapi/v1/"
                 "mopsfin_t187ap03_O", "SecuritiesCompanyCode")]:
                for r in requests.get(u, headers=UA,
                                      timeout=60).json():
                    out.append(f"{r[k]}"
                               f"{'.TW' if k.startswith('公司') else '.TWO'}")
            return out
    except Exception as e:                         # noqa: BLE001
        print(f"  master unavailable ({e}) — using screener")
    return None


def _screener(s, crumb, region, cap_floor_usd=2e8, pages=40):
    """Cap-ranked enumeration. Because it sorts DESC we can stop
    early: once a page is entirely below the floor, the tail is
    too."""
    syms, seen = [], set()
    for p in range(pages):
        body = {"size": 100, "offset": p * 100,
                "sortField": "intradaymarketcap",
                "sortType": "DESC", "quoteType": "EQUITY",
                "topOperator": "AND",
                "query": {"operator": "AND", "operands": [
                    {"operator": "or", "operands": [
                        {"operator": "EQ",
                         "operands": ["region", region]}]}]},
                "userId": "", "userIdType": "guid"}
        r = s.post("https://query1.finance.yahoo.com/v1/finance/"
                   f"screener?crumb={crumb}", json=body,
                   timeout=45)
        if r.status_code != 200:
            break
        qs = r.json()["finance"]["result"][0]["quotes"]
        if not qs:
            break
        live = 0
        for q in qs:
            sym = q.get("symbol", "")
            if sym in seen:
                continue
            seen.add(sym)
            if (q.get("marketCap") or 0) >= cap_floor_usd:
                live += 1
            syms.append(sym)
        print(f"    page {p + 1}: {len(syms)} cum", flush=True)
        if live == 0:            # whole page under the floor
            break
        time.sleep(0.4)
    return syms


def harvest(market, s=None, crumb=None):
    region, sfx, ccy = MARKETS[market]
    if s is None:
        s, crumb = session()
    s_sess = s
    print(f"\n{market}: enumerating…")
    syms = _master(market)
    src = "exchange master"
    if not syms:
        syms = _screener(s, crumb, region)
        src = "yahoo screener"
    # c-176: SEED WITH THE KNOWN MEMBERS. A company MSCI holds
    # cannot legitimately be missing from a cap-ranked universe,
    # so if one is absent that is our bug, not a fact. The
    # screener's coverage turned out to be patchy in exactly the
    # wrong places — ADANIENT, ANZ, CSL, NAB and MQG were all
    # absent from their market's universe. Asking for every
    # member by name closes that hole by construction and makes
    # the member-match rate a real test rather than a formality.
    try:
        _mm = json.loads((ROOT / "data" / "apac_members.json")
                         .read_text(encoding="utf-8"))["markets"].get(market, {})
        _seed = []
        for t in (_mm.get("standard_members") or []):
            t = str(t).strip()
            if not t:
                continue
            t = t.replace("-R", "").replace(".R", "")
            _seed.append(t if "." in t else t + sfx)
        _new = [x for x in _seed if x not in set(syms)]
        if _new:
            print(f"  + {len(_new)} MSCI members not returned by "
                  f"the {src}")
            syms = list(syms) + _new
    except Exception as e:                         # noqa: BLE001
        print(f"  member seed skipped: {e}")
    print(f"  {len(syms)} symbols ({src}); quoting…")
    qs = quotes(s, crumb, syms)
    rate = fx_usd(s, ccy)
    if not rate:
        raise SystemExit(f"no USD{ccy} rate")
    # c-181: overrides for members Yahoo cannot size. Applied
    # AFTER the normal pass so a live quote always wins; the
    # override only fills a hole.
    try:
        import share_overrides as _so
        _ovr = {k.split("|", 1)[1]: v for k, v in _so.load().items()
                if k.startswith(market + "|")}
    except Exception:                              # noqa: BLE001
        _ovr = {}
    rows, dropped = {}, {"no_cap": 0, "dr_or_fund": 0,
                         "wrong_ccy": 0, "not_equity": 0,
                         "cap_identity": 0, "th_dr": 0}
    # NB: cap_identity now counts RE-BASED names, not dropped
    # ones — they stay in the universe.
    for sym, q in qs.items():
        nm = q.get("longName") or q.get("shortName") or ""
        if q.get("quoteType") != "EQUITY":
            dropped["not_equity"] += 1
            continue
        if _JUNK.search(nm):
            dropped["dr_or_fund"] += 1
            continue
        # TRAP 1: a DR quotes in local currency but carries the
        # PARENT's cap. Currency alone will not catch it, so the
        # name pattern above does the work and this catches the
        # cross-listed rest.
        if q.get("currency") and q["currency"] != ccy:
            dropped["wrong_ccy"] += 1
            continue
        cap = q.get("marketCap")
        if not cap:
            # Yahoo has price but NO share count for some large
            # names (ANZ, CSL, NAB, MQG, Kweichow Moutai) — in
            # quote AND quoteSummary. They cannot be sized here,
            # but dropping them silently hid the gap. Record it.
            dropped["no_cap"] += 1
            dropped.setdefault("no_cap_symbols", []).append(sym)
            continue
        # TRAP 1a — THE CAP IDENTITY, corrected in c-169.
        #
        # The first version DROPPED any name where marketCap !=
        # price x sharesOutstanding. That was wrong and it cost
        # us real index members: Ping An (2318.HK), ICBC
        # (1398.HK), Kweichow Moutai (600519.SS) and Hyundai
        # Motor (005380.KS) all vanished. The identity breaks
        # for two completely different reasons and the filter
        # could not tell them apart:
        #   LEGITIMATE — a dual-listed A+H company or a
        #     multi-class Korean issuer, where Yahoo reports the
        #     WHOLE company's cap against ONE listing line's
        #     share count.
        #   CONTAMINATION — an SGX SDR, where the cap belongs to
        #     a foreign parent entirely.
        # Dropping both to catch the second is a bad trade: 373
        # HK names went, and HK only has ~1,700.
        #
        # So divergence no longer deletes. Where the two
        # disagree we take price x shares, which is specific to
        # THE LISTING LINE and is what MSCI sizes, and record
        # the reported cap beside it so nothing is hidden.
        px, sh = (q.get("regularMarketPrice") or 0), \
            (q.get("sharesOutstanding") or 0)
        basis, flag = "marketCap", None
        if px and sh:
            implied = px * sh
            if not (0.8 <= cap / implied <= 1.25):
                flag = {"reported_cap_usd_b":
                        round(cap / rate / 1e9, 4),
                        "ratio": round(cap / implied, 3)}
                cap, basis = implied, "price x shares"
                dropped["cap_identity"] += 1
        # TRAP 1b — THAI DRs pass the identity test, because
        # Yahoo carries the parent's shares too (NVDA80.BK is
        # internally consistent and simply enormous). Thai DRs
        # are spelled TICKER+ratio digits, and every genuine
        # Thai listco carries "Public Company" in its name.
        # c-174: widened from {2,5} to {2,9}. The country check
        # caught six DRs the old pattern missed purely on name
        # length — ITOCHU19, XIAOMI80, CHHONGQ19, JDHEAL19,
        # TENCENT11, SINGTEL80. ITOCHU at $92.1B was ranking
        # near the top of Thailand.
        if sfx == ".BK" and re.match(r"^[A-Z]{2,9}\d{2}$",
                                     sym.split(".")[0]) \
                and "PUBLIC COMPANY" not in nm.upper():
            dropped["th_dr"] += 1
            continue
        # TRAP 1c — the SET NVDR line. DELTA-R.BK is the same
        # company as DELTA.BK and Yahoo gives it the same cap,
        # so leaving both in double-counts the name and ranked
        # the NVDR first in Thailand. Keep the ordinary line.
        if sym.split(".")[0].endswith("-R"):
            dropped["th_nvdr"] = dropped.get("th_nvdr", 0) + 1
            continue
        rows[sym] = {
            "name": nm, "cap_basis": basis,
            "identity_flag": flag,
            "cap_local_b": round(cap / 1e9, 4),
            "cap_usd_b": round(cap / rate / 1e9, 4),
            "shares": q.get("sharesOutstanding"),
            "price": q.get("regularMarketPrice"),
            "exchange": q.get("fullExchangeName")}
    for _code, _o in _ovr.items():
        if any(k.split(".")[0] == _code for k in rows):
            continue
        _cap = _o.get("cap_usd_b")
        if _cap is None and _o.get("cap_local"):
            _cap = _o["cap_local"] / rate / 1e9
        if _cap is None:
            continue
        rows[f"{_code}{sfx}"] = {
            "name": _o.get("name", _code),
            "cap_basis": "OVERRIDE — " + _o.get("source", "")[:70],
            "identity_flag": None,
            "cap_local_b": round(_cap * rate, 4),
            "cap_usd_b": round(_cap, 4),
            "shares": _o.get("shares"), "price": None,
            "exchange": "override"}
        dropped["overrides_applied"] = \
            dropped.get("overrides_applied", 0) + 1

    # c-169: India returned 1,198 .NS AND 1,433 .BO symbols with
    # 1,147 overlapping bases — the same company counted twice,
    # which corrupts every rank and therefore the cutoff. MSCI
    # India prices off the NSE line, so NSE wins and the BSE
    # duplicate is dropped.
    if market == "India":
        # c-172, step 1: RECOVER the NSE line before deduping.
        # 289 names survived the first dedupe as BSE-only —
        # including Reliance and TCS, which obviously trade on
        # NSE. The screener's coverage is simply patchy, so we
        # ASK for the .NS symbol rather than accept the BSE
        # line. A probe found 11 of 12 exist. This matters
        # because MSCI India prices off NSE, and a BSE close is
        # a different (if similar) number.
        ns = {k[:-3] for k in rows if k.endswith(".NS")}
        want = [k[:-3] + ".NS" for k in rows
                if k.endswith(".BO") and k[:-3] not in ns]
        rec = 0
        if want:
            print(f"  recovering {len(want)} NSE lines…")
            for sym, q in quotes(s_sess, crumb, want).items():
                cap2 = q.get("marketCap")
                px2 = q.get("regularMarketPrice") or 0
                sh2 = q.get("sharesOutstanding") or 0
                if not cap2:
                    continue
                if px2 and sh2 and not (0.8 <= cap2 / (px2 * sh2)
                                        <= 1.25):
                    cap2 = px2 * sh2
                rows[sym] = {
                    "name": q.get("longName")
                    or q.get("shortName") or "",
                    "cap_basis": "marketCap",
                    "identity_flag": None,
                    "cap_local_b": round(cap2 / 1e9, 4),
                    "cap_usd_b": round(cap2 / rate / 1e9, 4),
                    "shares": sh2, "price": px2,
                    "exchange": q.get("fullExchangeName")}
                rec += 1
        dropped["nse_recovered"] = rec
        ns = {k[:-3] for k in rows if k.endswith(".NS")}
        dup = [k for k in rows
               if k.endswith(".BO") and k[:-3] in ns]
        for k in dup:
            del rows[k]
        dropped["bse_duplicate"] = len(dup)
    ranked = sorted(rows.items(),
                    key=lambda kv: -kv[1]["cap_usd_b"])
    for i, (k, v) in enumerate(ranked, 1):
        v["rank"] = i
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{market}.json").write_text(json.dumps({
        "market": market, "asof": time.strftime("%Y-%m-%d"),
        "universe_source": src, "fx_usd_per_local": rate,
        "currency": ccy, "n_symbols": len(syms),
        "n_priced": len(rows), "dropped": dropped,
        "survivorship": "LIVE LISTINGS ONLY — supports the "
                        "forward call, NOT a deletion backtest",
        "stage": "1 of 2 — size (§2.2.3) only. Float, ATVR, "
                 "foreign room are fetched for the shortlist "
                 "in stage 2.",
        "rows": dict(ranked)}, indent=1), encoding="utf-8")
    print(f"  {len(rows)} priced, dropped {dropped}")
    if ranked:
        print(f"  largest: {ranked[0][0]} "
              f"${ranked[0][1]['cap_usd_b']:.1f}B | "
              f"#100: ${ranked[min(99, len(ranked) - 1)][1]['cap_usd_b']:.2f}B")
    return s, crumb


def derive_cutoff(market):
    """DERIVE the seed cutoff — never type it.

    c-166. The first version took the cutoff as a command-line
    number ("shortlist Japan 5.0"). That is a hand-typed figure
    in a project whose whole claim is that nothing on screen is
    typed by hand, and it silently made Japan the only market
    anyone would run. Both wrong.

    Two independent anchors, from data we already hold:

      COUNT anchor  — MSCI publishes how many companies each
        country index holds (apac_members.json). §2.3.3 uses the
        Segment Number of Companies to maintain the index over
        time, so the full cap at rank N in the size-ranked
        universe approximates the Market Size-Segment Cutoff.
        This is the same anchor the Taiwan call used at rank 77.

      MEMBERSHIP anchor — the smallest CURRENT member's cap. On
        its own this one is circular (a cutoff defined as the
        smallest member is by construction <= every member, and
        in the Taiwan control it returned zero deletions), so it
        is reported as a cross-check, never as the cutoff.

    The seed is the COUNT anchor. It is only a seed: the real
    §2.3.3 cutoff comes from the float-coverage walk in stage 2,
    which needs float we have not fetched yet. The band around
    it is deliberately wide so a seed error does not lose names.
    """
    d = json.loads((OUT / f"{market}.json").read_text(encoding="utf-8"))
    rows = d["rows"]
    # c-173: EXCLUDE country-flagged names from the count
    # anchor. This was an ordering bug with real consequences:
    # the anchor is the cap at rank N, so foreign cross-listings
    # sitting in the top N push it up mechanically. Singapore
    # had 7 flagged names inside its top 16 (HSBC, Alibaba,
    # Tencent, ...) and its cutoff came out at $10.51B against
    # $5.61B on domestic names only — a 47% error that then
    # sized the whole shortlist. New Zealand was -34%.
    #
    # Note this EXCLUDES from the anchor while the size file
    # still KEEPS the name and its flag: MSCI's country
    # assignment has special cases, so the analyst can put one
    # back. Excluding from a derived number is reversible;
    # deleting the row is not.
    # ...BUT NEVER exclude a CURRENT MSCI MEMBER. c-173b: the
    # Taiwan run flagged Zhen Ding (4958) and Silergy (6415) as
    # Cayman-incorporated, and both sit in MSCI Taiwan today.
    # MSCI has already made the country call for anything it
    # holds, so incorporation cannot overrule it — a flagged
    # member is evidence the flag is a false positive, not
    # evidence the member is foreign. Hong Kong is the mirror
    # case: Tencent and Alibaba flag as China AND are not MSCI
    # Hong Kong members, so they are correctly excluded.
    _mem0 = json.loads((ROOT / "data" / "apac_members.json")
                       .read_text(encoding="utf-8"))["markets"].get(market, {})
    _held0 = {str(x).strip() for x in
              _mem0.get("standard_members", []) if x}
    def _norm(x):
        x = str(x).split(".")[0].strip()
        return x.lstrip("0") or x       # HK stores "1", we hold "0001"
    _held0 = {_norm(x) for x in _held0} | _held0

    def _is_member(sym):
        return _norm(sym) in _held0 or sym in _held0
    flagged = sum(1 for k, v in rows.items()
                  if v.get("country_flag") and not _is_member(k))
    caps = [v["cap_usd_b"] for k, v in rows.items()
            if not (v.get("country_flag") and not _is_member(k))]
    if not d.get("country_check"):
        print(f"  ! {market}: country check NOT run — cutoff "
              f"may be inflated by foreign cross-listings")
    mem = json.loads((ROOT / "data" / "apac_members.json")
                     .read_text(encoding="utf-8"))["markets"].get(market, {})
    held = [str(x).strip() for x in
            mem.get("standard_members", []) if x]
    n = len(held)
    # c-177: PREFER MSCI'S OWN CONSTITUENT COUNT. `held` comes
    # from a tracking FUND's holdings (EWT for Taiwan), and a
    # fund is not the index: EWT reports 79 lines where the
    # MSCI Taiwan factsheet lists 77. Since the count anchor IS
    # the cap at rank N, a fund artefact of +2 moves the cutoff.
    # The published factsheet count is authoritative; the fund
    # list stays as the ticker source for the membership
    # cross-check.
    off = (json.loads((ROOT / "data" /
                       "msci_official_constituents.json")
                      .read_text(encoding="utf-8")).get("markets", {})
           .get(market) or {})
    n_off = off.get("n")
    n_src = "fund holdings"
    if n_off:
        if n_off != n:
            print(f"  {market}: member count {n} (fund) vs "
                  f"{n_off} (MSCI factsheet) — using {n_off}")
        n, n_src = n_off, "MSCI factsheet"
    if not n or n > len(caps):
        return None, {"error": "no member count for this market"}
    count_anchor = caps[n - 1]          # rows are cap-ranked
    # membership anchor: match members to harvested symbols.
    # c-166b: the first run reported a $0.00B smallest member
    # for Malaysia and Thailand — the cross-check had matched
    # NOTHING and said so as a zero, which reads like a real
    # number. apac_members holds MSCI's strings ("MAYBANK")
    # while Yahoo uses Bursa's code ("1155"), so the map built
    # in c-165 is applied here before matching, and an empty
    # match now returns None rather than a misleading 0.
    base = {k.split(".")[0]: v["cap_usd_b"]
            for k, v in rows.items()}      # members: unfiltered
    tmap = {}
    f = ROOT / "data" / "apac_ticker_map.json"
    if f.exists():
        tmap = {k.split("|", 1)[1]: v
                for k, v in json.loads(f.read_text(encoding="utf-8")).items()
                if k.startswith(market + "|")}
    # Malaysia's members are Bursa SHORT NAMES ("AMBANK"), not
    # codes and not MSCI's security strings, so neither `base`
    # nor the map keys on them. apac_members carries a `names`
    # field — go member -> security name -> mapped code.
    mnames = mem.get("names") or {}
    hit = []
    for c in held:
        code = c if c in base else tmap.get(c)
        if code is None and mnames.get(c):
            code = tmap.get(str(mnames[c]).strip().upper()) \
                or tmap.get(str(mnames[c]).strip())
        # SET members carry the NVDR suffix; the ordinary line
        # is the one we harvested
        if code is None and (c.endswith("-R") or c.endswith(".R")):
            code = c[:-2]                  # SET NVDR -> ordinary
        if code in base:
            hit.append(base[code])
    # MEMBER COVERAGE GATE (c-180). The count anchor is the cap
    # at rank N. If k index members are missing from the ranked
    # list, every rank below them shifts up by k and the cutoff
    # is UNDERSTATED — we would predict too many additions and
    # too few deletions. Where k is small the arithmetic can be
    # corrected (read rank N-k instead); where k is large the
    # correction is meaningless. Singapore is the proof: 8 of 16
    # members missing turns a $15.17B cutoff into $55.08B, a
    # +263% "correction" that is really just an admission the
    # ladder is unusable. So coverage is measured, published,
    # and gated rather than assumed.
    _held_live = [c for c in held]
    _base = {(_norm(k2)) for k2 in rows}
    _k = 0
    for c in _held_live:
        cand = {_norm(c), _norm(c.replace("-R", "").replace(".R", ""))}
        if tmap.get(c):
            cand.add(_norm(tmap[c]))
        if not (cand & _base):
            _k += 1
    cover = 1 - _k / n if n else 0
    gate = ("USABLE" if cover >= 0.95 else
            "DEGRADED — correct the rank arithmetic" if cover >= 0.90
            else "DO NOT PUBLISH — too many members unsized")

    # CONFIDENCE. Where most of the top of the board is foreign
    # by incorporation, the count anchor stops meaning much. Hong
    # Kong is the extreme: 111 of the 165 names checked flagged,
    # and the ones that DON'T flag include China Mobile and CNOOC
    # — HK-INCORPORATED companies that nevertheless sit in MSCI
    # China. Incorporation cannot separate MSCI HK from MSCI
    # China, so the anchor is reported with a warning rather than
    # dressed up as precise.
    cc = d.get("country_check") or {}
    frac = (cc.get("flagged", 0) / cc["checked"]
            if cc.get("checked") else None)
    conf = ("LOW — >40% of the top of this board is foreign by "
            "incorporation; the count anchor cannot be trusted "
            "without MSCI's own member list"
            if frac and frac > 0.4 else "OK")
    return count_anchor, {
        "member_coverage": round(cover, 3),
        "members_unsized": _k,
        "coverage_gate": gate,
        "confidence": conf,
        "flagged_fraction_of_checked": (round(frac, 3)
                                        if frac else None),
        "count_anchor_usd_b": round(count_anchor, 3),
        "n_members": n, "n_members_source": n_src,
        "country_flagged_excluded": flagged,
        "country_check_run": bool(d.get("country_check")),
        "smallest_member_usd_b": (round(min(hit), 3)
                                  if hit else None),
        "members_matched": f"{len(hit)}/{n}",
        "note": "seed only — the binding cutoff comes from the "
                "stage-2 float-coverage walk"}


def shortlist(market, cutoff_usd_b=None, lo=0.5, hi=2.0):
    """Stage 1 -> stage 2 handoff: only these names get the
    expensive per-name calls. Band is deliberately wide, since
    the cutoff itself is an estimate."""
    diag = {}
    if cutoff_usd_b is None:
        cutoff_usd_b, diag = derive_cutoff(market)
        if cutoff_usd_b is None:
            print(f"{market}: {diag.get('error')}")
            return {}
    d = json.loads((OUT / f"{market}.json").read_text(encoding="utf-8"))
    keep = {k: v for k, v in d["rows"].items()
            if lo * cutoff_usd_b <= v["cap_usd_b"]
            <= hi * cutoff_usd_b}
    SHORT.mkdir(parents=True, exist_ok=True)
    (SHORT / f"{market}.json").write_text(json.dumps({
        "market": market,
        "cutoff_usd_b": round(cutoff_usd_b, 3),
        "cutoff_derivation": diag or "supplied by caller",
        "band": [lo, hi], "n": len(keep),
        "of_universe": d["n_priced"],
        "next": "stage 2 — float (§2.2.4/§2.2.6), ATVR "
                "(§2.2.5), foreign room (§2.2.8) for these "
                "names only",
        "rows": keep}, indent=1), encoding="utf-8")
    print(f"{market:12} cutoff ${cutoff_usd_b:7.2f}B "
          f"(rank {diag.get('n_members', '?')}) | smallest "
          f"member "
          f"{('$%.2fB' % diag['smallest_member_usd_b']) if diag.get('smallest_member_usd_b') else 'UNMATCHED':>9}"
          f" ({diag.get('members_matched', '-')})"
          f" | shortlist {len(keep):4} of {d['n_priced']}"
          + (f"  [{diag['coverage_gate'].split(' —')[0]}"
             f" {diag['member_coverage']:.0%}]"
             if diag.get("coverage_gate", "").split(" —")[0] != "USABLE"
             else "")
          + ("  [LOW CONFIDENCE]"
             if str(diag.get("confidence", "")).startswith("LOW")
             else ""))
    return keep


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "shortlist":
        # no market named -> every market already harvested
        want = a[1:] or sorted(f.stem for f in OUT.glob("*.json"))
        cut = None
        if len(want) == 2 and want[1].replace(".", "").isdigit():
            want, cut = [want[0]], float(want[1])
        for mk in want:
            shortlist(mk, cut)
    else:
        s = crumb = None
        for m in (a or list(MARKETS)):
            s, crumb = harvest(m, s, crumb)
