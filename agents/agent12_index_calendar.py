"""
Agent 12 — Index Rebalance Calendar Monitor.

Fetches recent index constituent changes (adds/deletes) from the three major
global index providers and normalizes them into IndexChangeEvent records that
Page 2 (Index Rebalancing Analysis) can consume with one click, instead of the
user manually typing a ticker + effective date.

Provider-specific methods (each provider publishes differently, so each gets
its own adapter — all degrade independently):

  * MSCI        — structured public announcement feed (app2.msci.com). List
                  page → per-security DocGet detail pages with labelled fields
                  (COUNTRY CODE / SECURITY NAME / ADDED|DELETED / EFFECTIVE
                  DATE). Fully parsed.
  * FTSE Russell — LSEG press releases. The listing page is JS-rendered, so
                  candidate URLs are *constructed from the review calendar*
                  (quarterly reviews: Mar/Jun/Sep/Dec) using the known slug
                  patterns, then the additions/deletions tables are parsed
                  from each release that exists.
  * S&P DJI     — PR Newswire company feed. Release pages carry a summary
                  table (Effective Date / Index / Action / Company / Ticker /
                  GICS Sector) that is fully parsed, with a sentence-level
                  regex fallback ("X will replace Y in the S&P 500 ...").

Also exposes the providers' review calendars (approximate next announcement /
effective dates) so the app can display *when* to expect the next wave of
changes, and a JSON cache so a scheduled job (GitHub Actions) can refresh the
data out-of-band while the app itself only reads the cache or refreshes
on-demand.

Terms-of-use note: these are public web pages intended for manual reading,
not formal APIs. Fetching is designed to be low-volume and on-demand
(a handful of requests per manual refresh, or one scheduled refresh per day
during demos). Do not turn this into a high-frequency poller.

Run `python -m agents.agent12_index_calendar` to refresh the local cache from
the command line (used by the scheduled GitHub Actions workflow).
"""

from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

import requests

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:          # pragma: no cover - bs4 is in requirements.txt
    HAS_BS4 = False

# ──────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────

UA_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/126.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 20

MSCI_LIST_URL = ("https://app2.msci.com/webapp/index_ann/Announcement"
                 "?doc_type=ANNOUNCEMENT&lang=en&prod_type=STANDARD"
                 "&visibility=public&format=html")
MSCI_BASE_URL = "https://app2.msci.com/webapp/index_ann/"

LSEG_PR_BASE = "https://www.lseg.com/en/media-centre/press-releases/ftse-russell"

SPDJI_LIST_URL = "https://www.prnewswire.com/news/s%26p-dow-jones-indices/"

PROVIDERS = ("MSCI", "FTSE Russell", "S&P DJI")

# MSCI two-letter country code → this app's MARKET_INFO key (agent1).
# Countries outside the app's supported market list map to None — the event
# is still shown, but can't be auto-run through the event study.
COUNTRY_TO_MARKET = {
    "US": "US",
    "TW": "Taiwan (TWSE)",
    "HK": "Hong Kong (HKEX)",
    "JP": "Japan (TSE)",
    "KR": "Korea (KRX)",
    "SG": "Singapore (SGX)",
    "CN": "China-A Shanghai",
    "IN": "India (NSE)",
    "AU": "Australia (ASX)",
    "TH": "Thailand (SET)",
    "ID": "Indonesia (IDX)",
    "MY": "Malaysia (KLSE)",
    "VN": "Vietnam (HOSE)",
    "GB": "UK (LSE)",
}

DEFAULT_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "index_changes_cache.json"


# ──────────────────────────────────────────────────────────────────────────
# Data model
# ──────────────────────────────────────────────────────────────────────────

@dataclass
class IndexChangeEvent:
    provider: str                    # "MSCI" | "FTSE Russell" | "S&P DJI"
    index_name: str                  # e.g. "S&P 500", "FTSE 100", "MSCI Global Standard"
    action: str                      # "Add" | "Delete" | "Other"
    security_name: str
    ticker: str = ""                 # exchange ticker if the provider publishes it
    country: str = ""                # ISO-2 where known
    market: str = ""                 # this app's MARKET_INFO key, "" if unsupported
    effective_date: str = ""         # ISO yyyy-mm-dd, "" if not stated
    announced_date: str = ""         # ISO yyyy-mm-dd, "" if unknown
    event_type: str = ""             # e.g. "SPIN OFF", "QUARTERLY REVIEW"
    source_url: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "IndexChangeEvent":
        known = {f: d.get(f, "") for f in cls.__dataclass_fields__}
        return cls(**known)


# ──────────────────────────────────────────────────────────────────────────
# Small helpers
# ──────────────────────────────────────────────────────────────────────────

def _get(url: str) -> str:
    resp = requests.get(url, headers=UA_HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text


def _soup(html: str) -> "BeautifulSoup":
    return BeautifulSoup(html, "html.parser")


def _text(html: str) -> str:
    """Whitespace-normalized visible text of an HTML document."""
    if HAS_BS4:
        txt = _soup(html).get_text(" ")
    else:
        txt = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", txt)


_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}


def _parse_date_words(s: str) -> str:
    """'June 30, 2026' or '23 March 2026' or '06 Jul 2026' → '2026-06-30' (ISO)."""
    s = s.strip().rstrip(".,")
    m = re.match(r"(\w+)\s+(\d{1,2}),?\s+(\d{4})$", s)          # June 30, 2026
    if m:
        mon = _MONTHS.get(m.group(1).lower()[:20])
        if mon is None:
            mon = _month_from_abbrev(m.group(1))
        if mon:
            return f"{int(m.group(3)):04d}-{mon:02d}-{int(m.group(2)):02d}"
    m = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})$", s)             # 23 March 2026
    if m:
        mon = _MONTHS.get(m.group(2).lower()) or _month_from_abbrev(m.group(2))
        if mon:
            return f"{int(m.group(3)):04d}-{mon:02d}-{int(m.group(1)):02d}"
    return ""


def _month_from_abbrev(word: str) -> Optional[int]:
    w = word.lower()[:3]
    for name, i in _MONTHS.items():
        if name.startswith(w):
            return i
    return None


def _third_friday(year: int, month: int) -> dt.date:
    d = dt.date(year, month, 1)
    # weekday(): Mon=0 ... Fri=4
    first_friday = d + dt.timedelta(days=(4 - d.weekday()) % 7)
    return first_friday + dt.timedelta(days=14)


def _last_weekday_of_month(year: int, month: int) -> dt.date:
    nxt = dt.date(year + (month == 12), (month % 12) + 1, 1)
    d = nxt - dt.timedelta(days=1)
    while d.weekday() > 4:
        d -= dt.timedelta(days=1)
    return d


# ──────────────────────────────────────────────────────────────────────────
# Review calendar (approximate, for display + calendar-aware fetching)
# ──────────────────────────────────────────────────────────────────────────

def upcoming_reviews(today: Optional[dt.date] = None, quarters_ahead: int = 2) -> list[dict]:
    """Approximate next announcement/effective dates per provider.

    These follow each provider's published cadence rules; exact dates can
    shift (holidays, provider discretion), so they're labelled approximate.
    """
    today = today or dt.date.today()
    rows: list[dict] = []

    # MSCI: quarterly index reviews Feb/May/Aug/Nov; results announced ~9
    # business days before month-end; effective close of last business day.
    count = 0
    y, m = today.year, today.month
    for _ in range(24):
        if m in (2, 5, 8, 11):
            eff = _last_weekday_of_month(y, m)
            ann = eff - dt.timedelta(days=13)
            if eff >= today:
                rows.append({"provider": "MSCI",
                             "event": f"{'Semi-Annual' if m in (5, 11) else 'Quarterly'} Index Review ({eff:%b %Y})",
                             "announcement (approx)": ann.isoformat(),
                             "effective (approx)": eff.isoformat()})
                count += 1
                if count >= quarters_ahead:
                    break
        m += 1
        if m > 12:
            m, y = 1, y + 1

    # FTSE UK: quarterly reviews Mar/Jun/Sep/Dec; announced early in the
    # month, implemented after third Friday, effective the following Monday.
    count = 0
    y, m = today.year, today.month
    for _ in range(24):
        if m in (3, 6, 9, 12):
            eff = _third_friday(y, m) + dt.timedelta(days=3)
            ann = dt.date(y, m, 1) + dt.timedelta(days=3)
            if eff >= today:
                rows.append({"provider": "FTSE Russell",
                             "event": f"FTSE UK Quarterly Review ({eff:%b %Y})",
                             "announcement (approx)": ann.isoformat(),
                             "effective (approx)": eff.isoformat()})
                count += 1
                if count >= quarters_ahead:
                    break
        m += 1
        if m > 12:
            m, y = 1, y + 1

    # S&P DJI: quarterly rebalance effective prior to the open of the Monday
    # after the third Friday of Mar/Jun/Sep/Dec; ad-hoc changes announced
    # ~2-5 business days ahead year-round.
    count = 0
    y, m = today.year, today.month
    for _ in range(24):
        if m in (3, 6, 9, 12):
            eff = _third_friday(y, m) + dt.timedelta(days=3)
            ann = eff - dt.timedelta(days=17)
            if eff >= today:
                rows.append({"provider": "S&P DJI",
                             "event": f"Quarterly Rebalance ({eff:%b %Y})",
                             "announcement (approx)": ann.isoformat(),
                             "effective (approx)": eff.isoformat()})
                count += 1
                if count >= quarters_ahead:
                    break
        m += 1
        if m > 12:
            m, y = 1, y + 1

    rows.sort(key=lambda r: r["effective (approx)"])
    return rows


# ──────────────────────────────────────────────────────────────────────────
# MSCI — structured announcement feed (full parse)
# ──────────────────────────────────────────────────────────────────────────

_MSCI_SEC_TITLE = re.compile(r"^([A-Z]{2})\s*:\s*(.+)$")


def fetch_msci_changes(max_details: int = 12) -> list[IndexChangeEvent]:
    """List page → per-security DocGet detail pages → structured events."""
    html = _get(MSCI_LIST_URL)
    events: list[IndexChangeEvent] = []

    # (announced_date, title, detail_url) triples from the list page
    items: list[tuple[str, str, str]] = []
    if HAS_BS4:
        soup = _soup(html)
        for a in soup.find_all("a", href=re.compile(r"DocGet")):
            title = a.get_text(" ", strip=True)
            href = a["href"]
            url = href if href.startswith("http") else MSCI_BASE_URL + href.lstrip("/")
            announced = ""
            tr = a.find_parent("tr")
            if tr:
                cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
                for c in cells:
                    iso = _parse_date_words(c)
                    if iso:
                        announced = iso
                        break
            items.append((announced, title, url))
    else:
        for m in re.finditer(r'href="([^"]*DocGet[^"]*)"[^>]*>\s*([^<]+?)\s*<', html):
            href, title = m.group(1), m.group(2)
            url = href if href.startswith("http") else MSCI_BASE_URL + href.lstrip("/")
            items.append(("", title, url))

    fetched = 0
    for announced, title, url in items:
        tm = _MSCI_SEC_TITLE.match(title)
        if not tm:
            continue                       # methodology notes, consultations, ...
        if fetched >= max_details:
            break
        fetched += 1
        country = tm.group(1)
        try:
            detail = _text(_get(url.replace("&amp;", "&")))
        except Exception:
            events.append(IndexChangeEvent(
                provider="MSCI", index_name="MSCI Global Standard",
                action="Other", security_name=tm.group(2), country=country,
                market=COUNTRY_TO_MARKET.get(country, ""),
                announced_date=announced, source_url=url,
                notes="Detail page could not be fetched"))
            continue

        name_m = re.search(r"SECURITY NAME\s+(.+?)\s+(?:STANDARD|LARGE CAP|MID CAP|SMALL CAP|ASIA|TYPE OF EVENT|EFFECTIVE)", detail)
        sec_name = name_m.group(1).strip() if name_m else tm.group(2)

        act_m = re.search(r"STANDARD\s+(ADDED|DELETED)", detail) or \
                re.search(r"\b(ADDED|DELETED)\b", detail)
        action = {"ADDED": "Add", "DELETED": "Delete"}.get(
            act_m.group(1) if act_m else "", "Other")

        type_m = re.search(r"TYPE OF EVENT\s+([A-Z][A-Z /&-]*?)\s+EFFECTIVE", detail)
        eff_m = re.search(r"EFFECTIVE DATE\s+(\w+ \d{1,2},? \d{4})", detail)

        cc_m = re.search(r"COUNTRY CODE\s+([A-Z]{2})", detail)
        if cc_m:
            country = cc_m.group(1)

        events.append(IndexChangeEvent(
            provider="MSCI",
            index_name="MSCI Global Standard",
            action=action,
            security_name=sec_name,
            country=country,
            market=COUNTRY_TO_MARKET.get(country, ""),
            effective_date=_parse_date_words(eff_m.group(1)) if eff_m else "",
            announced_date=announced,
            event_type=type_m.group(1).strip() if type_m else "",
            source_url=url,
            notes="" if COUNTRY_TO_MARKET.get(country) else
                  f"Market '{country}' not in this app's supported market list",
        ))
    return events


# ──────────────────────────────────────────────────────────────────────────
# FTSE Russell — calendar-constructed LSEG press-release URLs (table parse)
# ──────────────────────────────────────────────────────────────────────────

_FTSE_MONTHS = {3: "march", 6: "june", 9: "september", 12: "december"}


def _ftse_candidate_urls(today: Optional[dt.date] = None,
                         lookback_quarters: int = 3) -> list[str]:
    """LSEG's press-release listing is JS-rendered, so instead of scraping a
    listing we *construct* candidate URLs from the review calendar using the
    observed slug patterns, and keep whichever ones exist."""
    today = today or dt.date.today()
    urls: list[str] = []
    y, m = today.year, today.month
    # walk backwards over review months (+ include the next upcoming one)
    months: list[tuple[int, int]] = []
    yy, mm = y, m
    for _ in range(15):                     # forward to next review month
        if mm in _FTSE_MONTHS:
            months.append((yy, mm))
            break
        mm += 1
        if mm > 12:
            mm, yy = 1, yy + 1
    yy, mm = y, m
    for _ in range(4 * lookback_quarters):  # backwards
        if mm in _FTSE_MONTHS and (yy, mm) not in months:
            months.append((yy, mm))
            if len(months) >= lookback_quarters + 1:
                break
        mm -= 1
        if mm < 1:
            mm, yy = 12, yy - 1
    for yy, mm in months:
        name = _FTSE_MONTHS[mm]
        urls += [
            f"{LSEG_PR_BASE}/{yy}/ftse-uk-index-series-review-{name}-{yy}",
            f"{LSEG_PR_BASE}/{yy}/ftse-uk-index-series-indicative-review-{name}-{yy}",
            f"{LSEG_PR_BASE}/{yy}/ftse-uk-index-series-review",
            f"{LSEG_PR_BASE}/{yy}/ftse-uk-index-series-indicative-review",
        ]
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def fetch_ftse_changes(lookback_quarters: int = 3) -> list[IndexChangeEvent]:
    events: list[IndexChangeEvent] = []
    if not HAS_BS4:
        raise RuntimeError("beautifulsoup4 is required for the FTSE parser "
                           "(pip install beautifulsoup4)")
    for url in _ftse_candidate_urls(lookback_quarters=lookback_quarters):
        try:
            html = _get(url)
        except Exception:
            continue                        # slug doesn't exist this quarter
        if "FTSE" not in html:
            continue

        text = _text(html)
        eff = ""
        eff_m = (re.search(r"take effect from the start of trading on\s+\w+,?\s+(\d{1,2} \w+ \d{4})", text)
                 or re.search(r"implemented at the close of business on\s+\w+,?\s+(\d{1,2} \w+ \d{4})", text))
        if eff_m:
            eff = _parse_date_words(eff_m.group(1))
        ann = ""
        ann_m = re.search(r'w_published_date:\s*(\d{4}-\d{2}-\d{2})', html) or \
                re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', html)
        if ann_m:
            ann = ann_m.group(1)
        indicative = "indicative" in url

        soup = _soup(html)
        for table in soup.find_all("table"):
            headers = [th.get_text(" ", strip=True) for th in table.find_all("th")]
            if not headers:                 # some releases use <td> header rows
                first_row = table.find("tr")
                if first_row:
                    headers = [td.get_text(" ", strip=True) for td in first_row.find_all("td")]
            cols: list[tuple[str, str]] = []
            for h in headers:
                hm = re.match(r"(FTSE \d+)\s+(Addition|Deletion)s?", h, re.I)
                cols.append((hm.group(1), "Add" if hm.group(2).lower() == "addition" else "Delete") if hm else ("", ""))
            if not any(ix for ix, _ in cols):
                continue
            body_rows = table.find_all("tr")[1:]
            for tr in body_rows:
                cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
                for i, cell in enumerate(cells):
                    if i >= len(cols) or not cols[i][0] or not cell:
                        continue
                    index_name, action = cols[i]
                    events.append(IndexChangeEvent(
                        provider="FTSE Russell",
                        index_name=index_name,
                        action=action,
                        security_name=cell,
                        country="GB",
                        market=COUNTRY_TO_MARKET["GB"],
                        effective_date=eff,
                        announced_date=ann,
                        event_type="Quarterly Review" + (" (indicative)" if indicative else ""),
                        source_url=url,
                        notes="Indicative — subject to confirmation" if indicative else "",
                    ))
    # de-dupe (indicative + confirmed releases repeat names; prefer confirmed)
    uniq: dict[tuple, IndexChangeEvent] = {}
    for ev in events:
        key = (ev.index_name, ev.action, ev.security_name.lower())
        if key not in uniq or "indicative" not in ev.event_type.lower():
            uniq[key] = ev
    return list(uniq.values())


# ──────────────────────────────────────────────────────────────────────────
# S&P DJI — PR Newswire feed (table parse + sentence fallback)
# ──────────────────────────────────────────────────────────────────────────

_SP_LINK = re.compile(
    r'href="((?:https://www\.prnewswire\.com)?/news-releases/[a-z0-9-]+-\d{9}\.html)"')
_SP_REPLACE_SENT = re.compile(
    r"([A-Z][\w.,'&()\- ]{2,60}?)\s*\((?:NYSE|NASD|NASDAQ|CBOE|BATS)[A-Z]*:\s*([A-Z.]{1,6})\)\s*"
    r"will replace\s+([A-Z][\w.,'&()\- ]{2,60}?)\s*\((?:NYSE|NASD|NASDAQ|CBOE|BATS)[A-Z]*:\s*([A-Z.]{1,6})\)\s*"
    r"in the\s+(S&P[\w /]*\d+|Dow Jones[\w ]+?)(?:\s+effective|\s+prior|[.,])", re.I)


def fetch_sp_changes(max_releases: int = 6) -> list[IndexChangeEvent]:
    html = _get(SPDJI_LIST_URL)
    urls: list[str] = []
    for m in _SP_LINK.finditer(html):
        u = m.group(1)
        if u.startswith("/"):
            u = "https://www.prnewswire.com" + u
        slug = u.rsplit("/", 1)[-1]
        if re.search(r"join|replace|changes-to", slug) and u not in urls:
            urls.append(u)
    events: list[IndexChangeEvent] = []
    for url in urls[:max_releases]:
        try:
            page = _get(url)
        except Exception:
            continue
        text = _text(page)

        ann = ""
        ann_m = re.search(r"NEW YORK\s*,?\s+(\w+ \d{1,2},? \d{4})\s*/PRNewswire/", text)
        if ann_m:
            ann = _parse_date_words(ann_m.group(1))

        parsed_table = False
        if HAS_BS4:
            soup = _soup(page)
            for table in soup.find_all("table"):
                rows = table.find_all("tr")
                if not rows:
                    continue
                head = " ".join(td.get_text(" ", strip=True) for td in rows[0].find_all(["td", "th"]))
                if "Effective Date" not in head or "Action" not in head:
                    continue
                for tr in rows[1:]:
                    cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
                    if len(cells) < 5:
                        continue
                    eff_iso = _parse_date_words(cells[0])
                    action = {"addition": "Add", "deletion": "Delete"}.get(cells[2].strip().lower(), "Other")
                    events.append(IndexChangeEvent(
                        provider="S&P DJI",
                        index_name=cells[1],
                        action=action,
                        security_name=cells[3],
                        ticker=cells[4],
                        country="US",
                        market=COUNTRY_TO_MARKET["US"],
                        effective_date=eff_iso,
                        announced_date=ann,
                        event_type="Index Change",
                        source_url=url,
                    ))
                    parsed_table = True

        if not parsed_table:                # sentence-level fallback
            eff = ""
            eff_m = re.search(r"prior to the open(?:ing)? of trading on\s+(?:\w+,\s+)?(\w+ \d{1,2},? \d{4})", text)
            if eff_m:
                eff = _parse_date_words(eff_m.group(1))
            for sm in _SP_REPLACE_SENT.finditer(text):
                add_name, add_tkr, del_name, del_tkr, idx = sm.groups()
                for nm, tk, act in ((add_name, add_tkr, "Add"), (del_name, del_tkr, "Delete")):
                    events.append(IndexChangeEvent(
                        provider="S&P DJI", index_name=idx.strip(), action=act,
                        security_name=nm.strip(), ticker=tk, country="US",
                        market=COUNTRY_TO_MARKET["US"], effective_date=eff,
                        announced_date=ann, event_type="Index Change",
                        source_url=url))
    # de-dupe across releases (updates repeat earlier announcements)
    uniq: dict[tuple, IndexChangeEvent] = {}
    for ev in events:
        key = (ev.index_name, ev.action, ev.ticker or ev.security_name.lower())
        uniq.setdefault(key, ev)
    return list(uniq.values())


# ──────────────────────────────────────────────────────────────────────────
# Ticker suggestion (Yahoo symbol search, best-effort)
# ──────────────────────────────────────────────────────────────────────────

def suggest_yahoo_ticker(security_name: str, market: str = "") -> str:
    """Best-effort Yahoo symbol lookup for providers that don't publish
    tickers (MSCI, FTSE). Returns '' when nothing plausible is found —
    the UI keeps the field editable either way."""
    try:
        from agents.agent1_market_data import MARKET_INFO
        suffix = MARKET_INFO[market]["suffix"] if market in MARKET_INFO else None
    except Exception:
        suffix = None
    try:
        resp = requests.get(
            "https://query2.finance.yahoo.com/v1/finance/search",
            params={"q": security_name, "quotesCount": 8, "newsCount": 0},
            headers=UA_HEADERS, timeout=10)
        resp.raise_for_status()
        quotes = resp.json().get("quotes", [])
    except Exception:
        return ""
    equities = [q for q in quotes if q.get("quoteType") == "EQUITY" and q.get("symbol")]
    if suffix is not None:
        for q in equities:
            sym = q["symbol"]
            if (suffix == "" and "." not in sym) or (suffix and sym.endswith(suffix)):
                return sym
    return equities[0]["symbol"] if equities else ""


# ──────────────────────────────────────────────────────────────────────────
# Orchestration + cache
# ──────────────────────────────────────────────────────────────────────────

def fetch_all(providers: tuple[str, ...] = PROVIDERS) -> tuple[list[IndexChangeEvent], dict[str, str]]:
    """Fetch from each requested provider; failures degrade independently
    (same philosophy as the main agent pipeline)."""
    fetchers = {
        "MSCI": fetch_msci_changes,
        "FTSE Russell": fetch_ftse_changes,
        "S&P DJI": fetch_sp_changes,
    }
    events: list[IndexChangeEvent] = []
    errors: dict[str, str] = {}
    for name in providers:
        try:
            events.extend(fetchers[name]())
        except Exception as e:
            errors[name] = f"{type(e).__name__}: {e}"
    events.sort(key=lambda ev: ev.effective_date or "0000", reverse=True)
    return events, errors


def save_cache(events: list[IndexChangeEvent], errors: dict[str, str],
               path: Path = DEFAULT_CACHE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "errors": errors,
        "events": [ev.to_dict() for ev in events],
    }
    path.write_text(json.dumps(payload, indent=1), encoding="utf-8")


def load_cache(path: Path = DEFAULT_CACHE_PATH) -> Optional[dict]:
    """Returns {'fetched_at', 'errors', 'events': [IndexChangeEvent, ...]} or None."""
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["events"] = [IndexChangeEvent.from_dict(d) for d in payload.get("events", [])]
        return payload
    except Exception:
        return None


def refresh_cache(providers: tuple[str, ...] = PROVIDERS,
                  path: Path = DEFAULT_CACHE_PATH) -> tuple[list[IndexChangeEvent], dict[str, str]]:
    events, errors = fetch_all(providers)
    if events or not load_cache(path):      # don't clobber a good cache with an all-failed run
        save_cache(events, errors, path)
    return events, errors


if __name__ == "__main__":                  # used by the scheduled GitHub Actions job
    evs, errs = refresh_cache()
    print(f"Fetched {len(evs)} index-change events -> {DEFAULT_CACHE_PATH}")
    for p, msg in errs.items():
        print(f"  [WARN] {p}: {msg}")
