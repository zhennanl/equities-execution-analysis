#!/usr/bin/env python3
"""TDCC weekly shareholder dispersion, per stock, one year deep.

    py scripts\\tdcc_dispersion_harvest.py probe     # test the connection
    py scripts\\tdcc_dispersion_harvest.py harvest   # backfill 1 year
    py scripts\\tdcc_dispersion_harvest.py snapshot  # append this week
    py scripts\\tdcc_dispersion_harvest.py repair    # re-derive, no network
    py scripts\\tdcc_dispersion_harvest.py status

WHY THIS IS WORTH A HARVEST. Everything else this project has on
positioning is a FLOW: T86 says who bought today, SBL says what
was borrowed today. None of it says who HOLDS the stock. TDCC's
集保戶股權分散表 is the only free Taiwanese source that does — a
weekly census, ID-aggregated, of every custody account holding a
security, bucketed by size.

Bracket 15 (>1,000 lots, i.e. >1,000,000 shares) is where
non-resident institutions, government funds and the ETF trusts
sit. If passive money were pre-positioning ahead of an index
addition, the bracket-15 share would rise BEFORE the effective
date and the small brackets would fall. That is a position test,
not a flow test, and it is the one instrument here that would
catch a fund that bought in May and has sat still since —
precisely the case tw_prepositioning.py declares itself blind to.

WHAT WAS ALREADY ON DISK, AND WHY IT WAS NOT ENOUGH.
opendata.tdcc.com.tw/getOD.ashx?id=1-5 is a whole-market CSV and
is already used by tw_universe_pit.py — but it serves the LATEST
WEEK ONLY. data/event_data_cache.json has archived two weeks of
it by capture-forward. Two weeks cannot show a trend. The query
page at tdcc.com.tw/portal/zh/smWeb/qryStock serves ONE STOCK
across every retained week, and TDCC states the retention:

    "本歷史檔案資料自97年7月份起建置，資料保存期間為一年。"
    (built from July 2008; retained for one year)

Observed on 2026-08-10, the date dropdown offered 51 weekly
stamps, 20250815 -> 20260807. So this harvest is ONE YEAR DEEP
AND NO DEEPER, and it must be re-run to keep the tail. That
is a real constraint on the analysis, not a footnote: it cannot
reach the May-2026 review, only the August one.

THE ENDPOINT IS A STATEFUL FORM POST, NOT A JSON API, and the
first attempt got that wrong in four ways at once (c-331). The
probe came back 200 with 55KB of HTML and no table, which is the
worst kind of failure — it looks like success. Reading the saved
reply showed the POST had simply re-rendered the empty form.

What the form actually is:

    <form action="/portal/zh/smWeb/qryStock" method="post">
      <input name="SYNCHRONIZER_TOKEN" value="a47c2d93-...">
      <input name="SYNCHRONIZER_URI"   value="/portal/zh/smWeb/qryStock">
      <input name="method"             value="submit">
      <input name="firDate"            value="20260807">
      <select name="scaDate">...51 options...</select>
      <input name="sqlMethod" type="radio" value="StockNo">
      <input name="stockNo"   type="text">
      <input name="stockName" type="text">

Against which the first version posted `SqlMethod`, `StockNo`,
`scaDates`, `REQ_OPR` and `clkStockNo` — wrong case on two,
invented on three, and MISSING the CSRF token entirely. Every
field name here is now copied off the live form rather than
guessed, which is why `_form_state` PARSES the hidden inputs
instead of hard-coding them.

SYNCHRONIZER_TOKEN IS THE PART THAT MATTERS. It is a per-session
CSRF token, and this project should assume it is single-use: the
token is re-read from every response and carried into the next
request. A harvest that grabbed one token and reused it 204
times would work for one request and then silently return empty
forms for the rest — the same failure that already cost a probe.
Cookies are held by the shared `tw_http.session()`.

COST. 4 names x 51 weeks = 204 requests at 2.0s = about 7
minutes. Resumable by (code, week); a week already stored is
never refetched.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import tw_http as H                                    # noqa: E402

OUT = ROOT / "data" / "tdcc_dispersion.json"
PROBE = ROOT / "data" / "tdcc_probe.html"
URL = "https://www.tdcc.com.tw/portal/zh/smWeb/qryStock"
# c-330: TDCC also exposes an OpenAPI feed for the same table.
# It is CURRENT-WEEK ONLY, so it cannot replace the form scrape
# for history — but it is JSON, it needs no parsing of rendered
# HTML, and it is the right way to keep the series alive once the
# one-year backfill is banked. `snapshot` uses it.
OPENAPI = "https://openapi.tdcc.com.tw/v1/opendata/1-5"
FORM_HEADERS = {"Content-Type": "application/x-www-form-urlencoded",
                "Referer": URL}
PACE = 2.0

TPEX_CODES = {"8299", "6274", "3529", "3293", "8069"}
FALLBACK = ["2408", "8046", "2344", "8299"]

# The 15 holding brackets, in lots (1 lot = 1,000 shares). Row 16
# is TDCC's own adjustment row and 17 is the total; both are kept
# raw and neither is treated as a bracket.
BRACKETS = ["1-999", "1,000-5,000", "5,001-10,000",
            "10,001-15,000", "15,001-20,000", "20,001-30,000",
            "30,001-40,000", "40,001-50,000", "50,001-100,000",
            "100,001-200,000", "200,001-400,000",
            "400,001-600,000", "600,001-800,000",
            "800,001-1,000,000", "over 1,000,001"]


def shortlist():
    p = ROOT / "data" / "aug26_scenarios.json"
    if not p.exists():
        return list(FALLBACK)
    rows = json.loads(p.read_text(encoding="utf-8")).get("names") or {}
    return sorted(rows) if isinstance(rows, dict) else list(FALLBACK)


def _save(obj):
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    tmp.replace(OUT)


def _load():
    return json.loads(OUT.read_text(encoding="utf-8")) \
        if OUT.exists() else {}


def _num(x):
    try:
        return float(str(x).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


# ── the two pure functions, both offline-testable ──────────────

def parse_dates(html):
    """Every 資料日期 the page offers, newest first.

    TDCC's retention rolls, so the available set is READ rather
    than generated from a calendar — a generated Friday sequence
    would request weeks that were never published (the stamps
    move for holidays: 20260709 and 20260703 are both present)
    and would miss the ones that were."""
    seen, out = set(), []
    for m in re.finditer(r'value="(20\d{6})"', html):
        if m.group(1) not in seen:
            seen.add(m.group(1))
            out.append(m.group(1))
    return out


def _is_total(row):
    """The 合計 row, found by its LABEL.

    c-332 BUG, caught by Bill asking whether the harvest was
    complete. It was not: `total_shares` and `total_holders` came
    back null on 96 of 204 weeks.

    THE CAUSE. TDCC publishes the table in TWO layouts and the
    first version keyed on the row NUMBER:

        16 rows: 1-15 brackets, 16 = 合計                 (total)
        17 rows: 1-15 brackets, 16 = 差異數調整, 17 = 合計 (total)

    So "16 is the adjustment, 17 is the total" is true of the
    long layout and false of the short one, where 16 IS the
    total — and the old code then looked for a level 17 that does
    not exist and stored None. The 96 nulls split 37/27/16/16
    across the four names, i.e. it was not one bad stock; it was
    whichever weeks TDCC happened to publish without an
    adjustment row.

    The irony is that the docstring already argued for
    identifying rows by number rather than by position, "because
    a page with a missing bracket would silently shift a
    positional slice". A row NUMBER is still positional when the
    set of rows varies. The label is not.
    """
    return "合" in str(row.get("lots") or "")


def _is_adjustment(row):
    return "差異數調整" in str(row.get("lots") or "")


def _summarise(rows, src="form"):
    """Turn bracket rows into the fields the analysis reads.

    Shared by the HTML parser and the OpenAPI reader so the two
    routes cannot drift into producing different shapes for the
    same week — which would be invisible until a chart mixed
    them."""
    brackets = [r for r in rows
                if not _is_total(r) and not _is_adjustment(r)]
    tot = next((r for r in rows if _is_total(r)), None)
    adj = next((r for r in rows if _is_adjustment(r)), None)
    # Bracket 15 is holdings above 1,000,000 shares — where the
    # non-resident institutions and the ETF trusts sit. Taken as
    # the LAST bracket rather than as level 15, for the same
    # reason as above.
    b15 = brackets[-1] if brackets else None
    top3 = sorted(brackets, key=lambda r: -(r["pct"] or 0))[:3]
    return {"rows": rows,
            "total_holders": tot["holders"] if tot else None,
            "total_shares": tot["shares"] if tot else None,
            "adjustment_shares": adj["shares"] if adj else None,
            "layout_rows": len(rows),
            "b15_pct": b15["pct"] if b15 else None,
            "b15_shares": b15["shares"] if b15 else None,
            "b15_holders": b15["holders"] if b15 else None,
            "top3_pct": sum(r["pct"] or 0 for r in top3),
            "n_brackets": len(brackets), "_src": src}


def parse_table(html):
    """The dispersion table for one (stock, week), or None.

    c-331: returning None is a REAL ANSWER here and the caller
    must not treat it as data. The first probe got a 200 with 55KB
    of HTML that contained no result table at all — the form had
    simply re-rendered — so "no rows" has to be distinguishable
    from "rows I failed to read". `probe` prints the row count
    and the first cells so the two are told apart by eye before
    a harvest is spent.

    Level 16 is TDCC's adjustment row and 17 the total; both are
    identified by their LEVEL NUMBER and excluded from the bracket
    list rather than by position, because a page with a missing
    bracket would silently shift a positional slice.
    """
    body = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    out = []
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", body, flags=re.S):
        cells = [re.sub(r"<[^>]+>", " ", c).replace("&nbsp;", " ")
                 .replace(",", "").strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>",
                                     r, flags=re.S)]
        # The form page's own rows are (label, control) pairs and
        # its first cell is never a bare integer, which is what
        # separates a result page from an empty one.
        if len(cells) < 5 or not cells[0].isdigit():
            continue
        lvl = int(cells[0])
        if not 1 <= lvl <= 17:
            continue
        out.append({"level": lvl, "lots": cells[1],
                    "holders": _num(cells[2]),
                    "shares": _num(cells[3]),
                    "pct": _num(cells[4])})
    return _summarise(out) if out else None


# ── network ────────────────────────────────────────────────────

def _form_state(html):
    """Every hidden field the form will post back, read off the
    page rather than assumed.

    c-331: the first version hard-coded five field names and got
    three of them wrong. Parsing means a rename upstream shows up
    as a missing key here, not as a silent empty result."""
    state = {}
    for tag in re.findall(r"<input[^>]*>", html):
        name = re.search(r'name="([^"]+)"', tag)
        val = re.search(r'value="([^"]*)"', tag)
        typ = re.search(r'type="([^"]+)"', tag)
        if not name:
            continue
        if (typ and typ.group(1).lower() == "hidden") or \
                name.group(1) in ("firDate",):
            state[name.group(1)] = val.group(1) if val else ""
    return state


def _post(code, date, state):
    """One (stock, week). Returns (html, next_state).

    The caller MUST thread `next_state` into the following call —
    see the SYNCHRONIZER_TOKEN note in the module docstring."""
    form = dict(state)
    form.update({"method": "submit",
                 "scaDate": date,
                 "sqlMethod": "StockNo",
                 "stockNo": code,
                 "stockName": ""})
    r = H.post(URL, data=form, headers=FORM_HEADERS)
    r.encoding = "utf-8"
    return r.text, _form_state(r.text)


def _form_page():
    r = H.get(URL)
    r.encoding = "utf-8"
    return r.text


def snapshot():
    """Append THIS WEEK from TDCC's OpenAPI feed.

    c-330. The form scrape backfills one year and no more, because
    that is TDCC's retention. This keeps the series growing past
    it: run it weekly (the table publishes each Saturday) and the
    history stops being capped at twelve months a year from now.

    The feed is whole-market JSON, so it is filtered to the
    shortlist here rather than fetched per name."""
    codes = set(shortlist())
    rows = H.get(OPENAPI).json()
    by = {}
    for row in rows:
        c = str(row.get("證券代號") or row.get("stock_id") or "").strip()
        if c not in codes:
            continue
        by.setdefault(c, []).append({
            "level": int(_num(row.get("持股分級")
                              or row.get("level")) or 0),
            "lots": row.get("持股分級"),
            "holders": _num(row.get("人數") or row.get("people")),
            "shares": _num(row.get("股數") or row.get("shares")),
            "pct": _num(row.get("占集保庫存數比例%")
                        or row.get("percent"))})
    if not by:
        print("feed returned no rows for the shortlist. Keys seen: "
              f"{sorted(rows[0]) if rows else 'none'}")
        return 1
    date = str(rows[0].get("資料日期") or rows[0].get("date") or "")
    date = date.replace("-", "").replace("/", "")
    store = _load()
    for c, rs in by.items():
        store.setdefault(c, {})[date] = _summarise(rs, src="openapi")
        print(f"  {c} {date} b15 "
              f"{store[c][date].get('b15_pct') or 0:.2f}%")
    _save(store)
    return 0


def probe():
    """Fetch one (stock, week), save the raw HTML, and print what
    the parser makes of it. Run this FIRST. If TDCC has changed
    the form or the table, this is where it shows up — cheaply,
    on one request, instead of after 204."""
    H.probe(URL)
    print("-" * 52)
    html = _form_page()
    state = _form_state(html)
    print(f"hidden fields: {sorted(state)}")
    dates = parse_dates(html)
    print(f"date stamps offered: {len(dates)}  "
          f"{dates[-1] if dates else '?'} -> "
          f"{dates[0] if dates else '?'}")
    if not dates:
        print("NO DATES — the page shape changed. Stop here.")
        return 1
    code = shortlist()[0]
    html, _ = _post(code, dates[0], state)
    PROBE.write_text(html, encoding="utf-8")
    print(f"saved {PROBE.name} ({len(html):,} bytes)")
    t = parse_table(html)
    if not t:
        # c-331: say WHICH failure this is. "No table" and "a
        # table I could not read" need different fixes and the
        # first probe could not tell them apart.
        import re as _re
        ntr = len(_re.findall(r"<tr", html))
        has = "持股分級" in html and "人數" in html
        print(f"NO BRACKET ROWS PARSED.  <tr> tags: {ntr}  "
              f"result-table headers present: {has}")
        print("  -> if headers are absent, the POST was rejected "
              "and re-rendered the empty form: check the field "
              "names in _form_state/_post against the saved HTML.")
        print("  -> if headers are present, the row shape changed: "
              "fix parse_table.")
        return 1
    print(f"{code} @ {dates[0]}: {t['n_brackets']} brackets, "
          f"{t['total_holders']:,.0f} holders, "
          f"bracket-15 {t['b15_pct']:.2f}% of custody")
    return 0


def harvest():
    store = _load()
    html = _form_page()
    state = _form_state(html)
    dates = parse_dates(html)
    if not dates:
        print("no dates offered — aborting")
        return 1
    codes = shortlist()
    todo = [(c, d) for c in codes for d in dates
            if d not in (store.get(c) or {})]
    print(f"{len(codes)} codes x {len(dates)} weeks — "
          f"{len(todo)} to fetch")
    fails = 0
    for i, (code, date) in enumerate(todo, 1):
        try:
            body, nxt = _post(code, date, state)
            if nxt.get("SYNCHRONIZER_TOKEN"):
                state = nxt
            t = parse_table(body)
            # An empty table is a REAL answer for a week before
            # listing, so it is cached as {} and never retried.
            # A timeout stores nothing and is picked up next run.
            store.setdefault(code, {})[date] = t or {}
            got = f"b15 {t['b15_pct']:.2f}%" if t else "empty"
            print(f"  {i:>4}/{len(todo)} {code} {date} {got}")
            fails = 0
        except Exception as ex:                        # noqa: BLE001
            fails += 1
            print(f"  {i:>4}/{len(todo)} {code} {date} ERR "
                  f"{str(ex)[:60]}"
                  + ("  — backing off 60s" if fails >= 3 else ""))
            if fails >= 3:
                time.sleep(60)
                fails = 0
        if i % 25 == 0:
            _save(store)
        time.sleep(PACE)
    store["_meta"] = {"harvested": dt.datetime.now().isoformat(
        timespec="seconds"), "dates_offered": dates,
        "retention_note": "TDCC retains one year; re-run to keep "
                          "the tail"}
    _save(store)
    print(f"saved {OUT.name}")
    return 0


def repair():
    """Re-derive every stored week's summary from its OWN rows.

    c-332. The raw `rows` were always correct — the harvest cost
    seven minutes and there is no reason to spend it again for a
    summariser bug. This rewrites the derived fields in place and
    reports what changed, which is also the check that the fix
    did something."""
    store = _load()
    fixed = 0
    for c, wk in store.items():
        if c.startswith("_") or not isinstance(wk, dict):
            continue
        for date, v in wk.items():
            if not v or not v.get("rows"):
                continue
            before = v.get("total_shares")
            wk[date] = _summarise(v["rows"], src=v.get("_src", "form"))
            if before is None and wk[date]["total_shares"] is not None:
                fixed += 1
    _save(store)
    print(f"re-derived; {fixed} weeks gained a total row")
    return 0


def status():
    if not OUT.exists():
        print(f"  {OUT.name}: not harvested")
        return
    s = _load()
    print(f"  {OUT.name}  {OUT.stat().st_size / 1024:,.0f} KB")
    for c, wk in sorted(s.items()):
        if c.startswith("_") or not isinstance(wk, dict):
            continue
        real = {d: v for d, v in wk.items() if v}
        if not real:
            print(f"    {c}: 0 weeks with data")
            continue
        ds = sorted(real)
        print(f"    {c}: {len(real):>3} weeks  {ds[0]} -> {ds[-1]}"
              f"   b15 {real[ds[0]]['b15_pct']:.2f}% -> "
              f"{real[ds[-1]]['b15_pct']:.2f}%")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    sys.exit({"probe": probe, "harvest": harvest,
              "snapshot": snapshot, "repair": repair}.get(
                  cmd, status)() or 0)
