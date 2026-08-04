#!/usr/bin/env python3
"""TIP news enumerator (session 8x). Discovery chain: TIP's news
LIST is client-side JS (sandbox-blind), but DETAIL pages /news/{id}
are SSR — and the Chrome session revealed ids are numeric (1..~445).
So: enumerate ids threaded, index titles/dates, keep full text of
every TWSE-FTSE review announcement (定期審核結果 + 成分股異動).

Usage: index [lo hi] | status
Cache: data/tip_news_index.json + data/tip_news/{id}.txt (reviews)
"""
import concurrent.futures as cf
import json
import re
import sys
import urllib.request
from pathlib import Path

IDX = Path("data/tip_news_index.json")
DIR = Path("data/tip_news")
DIR.mkdir(exist_ok=True)
KEEP = ("富時", "指數系列成分股")     # TWSE-FTSE co-compiled items


def fetch_one(i):
    try:
        req = urllib.request.Request(
            f"https://www.taiwanindex.com.tw/news/{i}",
            headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=15).read() \
            .decode("utf-8", "ignore")
        text = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
        text = re.sub(r"<style.*?</style>", " ", text, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)
        m = re.search(r"(20\d\d/\d\d/\d\d)", text)
        date = m.group(1) if m else None
        # title = text before the date marker, tail end of breadcrumb
        head = text[:text.find(date)] if date else text[:300]
        title = head.strip()[-120:]
        keep = any(k in text[:3000] for k in KEEP) and "審核" in text
        if keep or any(k in title for k in ("異動", "調整")):
            (DIR / f"{i}.txt").write_text(text[:20000],
                                          encoding="utf-8")
        return i, {"date": date, "title": title[-80:],
                   "kept": keep}
    except Exception as e:
        return i, {"err": str(e)[:40]}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "status"
    idx = json.loads(IDX.read_text()) if IDX.exists() else {}
    if mode == "index":
        lo, hi = int(sys.argv[2]), int(sys.argv[3])
        todo = [i for i in range(lo, hi + 1) if str(i) not in idx]
        with cf.ThreadPoolExecutor(max_workers=10) as ex:
            for i, r in ex.map(fetch_one, todo):
                idx[str(i)] = r
        IDX.write_text(json.dumps(idx, ensure_ascii=False))
        kept = sum(1 for v in idx.values() if v.get("kept"))
        print(f"indexed {len(idx)}, review-pages kept {kept}")
    else:
        kept = {i: v for i, v in idx.items() if v.get("kept")}
        for i, v in sorted(kept.items(), key=lambda x: int(x[0])):
            print(i, v.get("date"), v.get("title", "")[:60])
        print("total kept:", len(kept))


if __name__ == "__main__":
    main()
