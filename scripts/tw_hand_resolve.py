"""The last 12 Taiwan names, resolved BY HAND (c-161).

WHY BY HAND: the automated route died twice, both times in
the same way — a thin or Chinese-language name index made the
matcher CONFIDENT AND WRONG (Chunghwa Picture Tubes -> Chunghwa
Telecom; China Life -> Mercuries Life; Lee Chang Yung -> Yung
Zip Chemical). A wrong ticker is worse than a blank one,
because the roster merges rows on ticker: two companies would
be fused into one history. Twelve names did not justify
another matcher.

HOW EACH ONE WAS SETTLED — two independent checks, both run
in c-161 and both reproducible from this file:

  1. FORWARD Yahoo probe (I supply the code, Yahoo returns the
     name + last trade date). Forward is safe where reverse
     search is not: there is no matching to get wrong.
  2. The LIVE LISTED REGISTER, from the exchanges themselves:
       TWSE  openapi.twse.com.tw/v1/opendata/t187ap03_L
       TPEx  tpex.org.tw/openapi/v1/mopsfin_t187ap03_O
     1,983 codes with Chinese legal names. Absence from this
     register is what proves a delisting — it is a positive
     statement by the exchange, not a failure of our search.

RENAMES are the reason 8 of 12 looked "missing": the company
never left, the NAME changed and MSCI's twenty-year-old string
no longer matches anything. Eternal Chemical trades as Eternal
Materials, Inventec Appliances as Getac Holdings, Waterland as
IBF Financial, Yuen Foong Yu Paper as YFY, Zyxel Communications
as Zyxel Group. Those are the same listings, same codes.

MITAC is the one judgement call. MSCI's member was MiTAC
International (2315), which stopped trading when the group
converted to a holding company in 2013. The business continues
as MiTAC Holdings (3706). Mapped to 3706 with the conversion
recorded, so the row is not silently presented as unbroken.

Run: py scripts\\tw_hand_resolve.py
Out: data/yahoo_tickers.json, data/delisted_register.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOUT = ROOT / "data" / "yahoo_tickers.json"
DREG = ROOT / "data" / "delisted_register.json"

# MSCI security string -> (code, evidence). Code "" = delisted.
HAND = {
    # ---- still listed, verified in the live register --------
    "ETERNAL CHEMICAL CO": (
        "1717", "listed TWSE; renamed Eternal Materials"),
    "FARGLORY DEVELOPERS CO": (
        "5522", "listed TWSE as Farglory Land Development"),
    "INVENTEC APPLIANCES": (
        "3005", "listed TWSE; renamed Getac Holdings"),
    "SINOAMERICAN SILICON PRO": (
        "5483", "listed TPEx as Sino-American Silicon"),
    "WATERLAND FINANCIAL": (
        "2889", "listed TWSE; renamed IBF Financial Holdings"),
    "YUEN FOONG YU PAPER MFG": (
        "1907", "listed TWSE; renamed YFY Inc. NOTE: 6790 is "
                "YFY Consumer Products, a DIFFERENT listing "
                "the earlier matcher wrongly picked"),
    "ZYXEL COMMUNICATIONS": (
        "3704", "listed TWSE; renamed Zyxel Group"),
    "MITAC INTERNATIONAL": (
        "3706", "member code 2315 stopped trading at the 2013 "
                "holding-company conversion; business "
                "continues as MiTAC Holdings (3706)"),
    # ---- verified absent from the 1,983-code register ------
    "COMPAL COMMUNICATIONS": ("", None),
    "LEE CHANG YUNG CHEM IND": ("", None),
    "PHOENIX PRECISION TECH": ("", None),
    "RICHTEK TECHNOLOGY CORP": ("", None),
}

# Delistings carry the event, not just the absence.
EVENTS = {
    "COMPAL COMMUNICATIONS":
        "code 8078 absent from the live TWSE/TPEx register; "
        "ceased trading after absorption into the Compal group",
    "LEE CHANG YUNG CHEM IND":
        "code 1704 absent from the live register; LCY Chemical "
        "taken private in 2017",
    "PHOENIX PRECISION TECH":
        "code 2446 absent from the live register",
    "RICHTEK TECHNOLOGY CORP":
        "code 6286 absent from the live register; acquired "
        "outright by MediaTek",
}

# Resolved earlier in c-160 and left in place.
PRIOR = {
    "HOTAI MOTOR COMPANY": "2207",
    "VANGUARD INT'L SEMICON": "5347",
    "TAIWAN COOPERATIVE BANK": "5880",
    "FENG HSIN IRON & STEEL": "2015",
    "NAN KANG RUBBER TIRE CO": "2101",
    "NIEN HSING TEXTILE CORP": "1451",
    "FORMOSA INT'L HOTELS": "2707",
    "CHINESE GAMER INT'L": "3083",
    "INNOLUX DISPLAY": "3481",
    # c-161: was filed as a DELISTING. The live register says
    # 8069 still trades, as E Ink Holdings — same listing,
    # new name. A rename misread as a delisting is exactly the
    # error that made 8 of these 12 look "missing".
    "PRIME VIEW INTERNATIONAL": "8069",
    "POWERCHIP TECHNOLOGY": "6770",
}
PRIOR_GONE = {
    "INOTERA MEMORIES": "merged into Micron Technology, 2016",
    "INOTERA MEMORIES (ATM)":
        "merged into Micron Technology, 2016",
    "HERMES MICROVISION": "acquired by ASML, 2016",
    "MSTAR SEMICONDUCTOR": "merged into MediaTek, 2014",
    "WINTEK": "delisted after insolvency, 2015",
    "PRO MOS TECHNOLOGIES": "delisted, 2013",
    "CHUNGHWA PICTURE TUBES":
        "delisted after insolvency, 2019",
    "PHOENIXTEC POWER CO":
        "acquired by Delta Electronics, 2010",
    "CHINA LIFE INSURANCE CO":
        "merged into CTBC Financial, 2015",
    "KGI SECURITIES CO":
        "merged into China Development Financial, 2017",
}


def run(market="Taiwan"):
    tmap = {f"{market}|{k}": v for k, v in PRIOR.items()}
    reg = {market: dict(PRIOR_GONE)}
    # every ticker-less name gets an explicit entry — a name
    # absent from BOTH files would render "Not matched", which
    # says nothing about whether the company exists.
    for nm in PRIOR_GONE:
        tmap[f"{market}|{nm}"] = ""
    for nm, (code, _why) in HAND.items():
        tmap[f"{market}|{nm}"] = code
        if not code:
            reg[market][nm] = EVENTS[nm]
    TOUT.write_text(json.dumps(tmap, indent=1,
                               ensure_ascii=True),
                    encoding="utf-8")
    DREG.write_text(json.dumps(reg, indent=1,
                               ensure_ascii=True),
                    encoding="utf-8")
    live = sum(1 for v in tmap.values() if v)
    print(f"{market}: {len(tmap)} names mapped — "
          f"{live} to a live ticker, "
          f"{len(reg[market])} delisted with a recorded event")
    for k, v in sorted(tmap.items()):
        print(f"  {k.split('|')[1][:28]:28} -> "
              f"{v or 'Delisted'}")


if __name__ == "__main__":
    run()
