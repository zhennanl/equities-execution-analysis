#!/usr/bin/env python3
"""Build data/ftse_tw50_changes.json from the TIP review pages
(session 8x). Parses each saved announcement's 臺灣50指數 section:
納入 (adds), 刪除 (deletes), 候補名單 (reserve list), effective
date sentence. Quarters with 成分股無變動 recorded as empty lists.
Pre-TIP quarters (2015 - 2016Q3) recorded NOT FOUND with the
documented path (TWSE-era announcements, 證交資料月刊).
"""
import json
import re
from pathlib import Path

DIR = Path("data/tip_news")
IDX = json.loads(Path("data/tip_news_index.json").read_text(encoding="utf-8"))
OUT = Path("data/ftse_tw50_changes.json")

PAIR = re.compile(r"([\w\-\*．·＊]+?)\s*[（(]\s*(\d{4}[A-Z]?)\s*[）)]")


def parse_page(pid, text):
    date = IDX[pid].get("date")
    # the preamble ALSO enumerates "臺灣50指數、臺灣中型100指數..."
    # — pick the occurrence whose following section carries content
    sec = None
    for m in re.finditer(r"臺灣\s*50\s*指數(.*?)(?:臺灣\s*中型\s*100\s*指數|"
                         r"臺灣\s*資訊科技\s*指數|臺灣\s*發達\s*指數|"
                         r"臺灣\s*高股息\s*指數|$)", text, re.S):
        cand = m.group(1)
        if ("成分股" in cand or "無變動" in cand) and len(cand) > 20:
            sec = cand
            break
    if sec is None:
        return None
    eff = re.search(r"自\s*(20\d\d)\s*年\s*(\d+)\s*月\s*(\d+)\s*日"
                    r"[^生]{0,20}(?:交易結束後)?生效", text)
    eff_date = (f"{eff.group(1)}-{int(eff.group(2)):02d}-"
                f"{int(eff.group(3)):02d}" if eff else None)

    def grab(label):
        mm = re.search(label + r"[：:]\s*(.*?)(?:成分股|候補|備註|$)",
                       sec)
        if not mm:
            return []
        return [{"code": c, "name": n}
                for n, c in PAIR.findall(mm.group(1))]
    adds, dels = grab("成分股納入"), grab("成分股刪除")
    reserve = grab("候補名單")
    unchanged = ("無變動" in sec or "沒有變動" in sec) and not (adds or dels)
    return {"ann_date": date, "effective": eff_date,
            "adds": adds, "dels": dels, "reserve": reserve,
            "unchanged": bool(unchanged),
            "source": f"https://www.taiwanindex.com.tw/news/{pid}"}


def main():
    out = {}
    for f in sorted(DIR.glob("*.txt"), key=lambda p: int(p.stem)):
        pid = f.stem
        r = parse_page(pid, f.read_text(encoding="utf-8"))
        if r and r["ann_date"]:
            key = r["ann_date"][:7].replace("/", "-")
            # keep the richer entry if two share a month (ad-hoc vs
            # quarterly): quarterly has reserve list
            if key in out and not r["reserve"] and out[key]["reserve"]:
                key = key + "-adhoc"
            out[key] = r
    # pre-TIP gap, stated
    for q in ("2015-03", "2015-06", "2015-09", "2015-12",
              "2016-03", "2016-06", "2016-09"):
        out.setdefault(q, {"status": "NOT FOUND — pre-TIP era; "
                           "path: TWSE-era announcements / "
                           "證交資料月刊 (manual)"})
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n_q = sum(1 for v in out.values() if "adds" in v)
    n_chg = sum(len(v.get("adds", [])) + len(v.get("dels", []))
                for v in out.values())
    print(f"quarters/events keyed: {n_q}; TW50 adds+dels total: "
          f"{n_chg}; NOT FOUND: "
          f"{sum(1 for v in out.values() if 'status' in v)}")
    for k in sorted(out):
        v = out[k]
        if "adds" in v:
            print(k, "eff", v["effective"],
                  "+" + ",".join(x["code"] for x in v["adds"]) or "-",
                  "-" + ",".join(x["code"] for x in v["dels"]))


if __name__ == "__main__":
    main()
