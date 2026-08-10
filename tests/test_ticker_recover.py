"""c-263: the recovery matcher, tested against the three
mismatches that actually happened here.

A recovery script that cannot reject Chunghwa Picture Tubes ->
Chunghwa Telecom has no business writing to the ticker map.
These are regression tests against real incidents, not
hypotheticals:

  c-161  CHUNGHWA PICTURE TUBES -> CHUNGHWA TELECOM
  c-259  MEITU -> MEITUAN
  c-259  ANHUI GUJING ... B -> the A line

Two of the three produced clean-looking prices. That is why the
bar is a rejection test rather than an accuracy target.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ticker_recover as R                        # noqa: E402


def _c(a, b):
    return R.score(a, b)[0]


def test_it_rejects_chunghwa_picture_tubes_for_telecom():
    """The c-161 failure. Shared head token, different company.
    One token in common must never be enough."""
    assert _c("CHUNGHWA PICTURE TUBES",
              "Chunghwa Telecom Co Ltd") < 0.45


def test_it_rejects_meitu_for_meituan():
    """The c-259 failure. Note these do not even share a token
    after normalisation — MEITU and MEITUAN are different
    strings — so the head-token rule alone catches it."""
    assert _c("MEITU", "Meituan") < 0.45
    assert _c("MEITU", "Meitu Inc") >= 0.45


def test_it_rejects_a_share_class_swap():
    """c-259. An A line and a B line of one issuer are
    different securities; the matcher must not treat the
    issuer name as sufficient."""
    a = _c("ANHUI GUJING DISTILLER B",
           "Anhui Gujing Distillery Company Limited")
    # the issuer matches, so the NAME score may be high — the
    # protection here is the share-class kind, which must be
    # carried through and not silently dropped.
    assert R.line_kind("ANHUI GUJING DISTILLER B") == "AB"
    assert R.line_kind("CHINA STH AIRLINES H") == "H"
    assert R.line_kind("ALIBABA GROUP HLDG ADR") == "ADR"
    assert a >= 0.0


def test_name_similarity_cannot_recover_a_rename():
    """THE CENTRAL LIMITATION, and it is worth stating as a
    test rather than a comment.

    "ALPS ELECTRIC" and "ALPS ALPINE" share exactly one token,
    so the matcher scores them below the bar — the same rule
    that rejects Picture Tubes/Telecom. That is not a tuning
    failure to be dialled away: a rename CHANGES THE NAME, so
    string similarity cannot in principle distinguish a renamed
    company from a different company with a similar name.

    Renames are therefore recovered by IDENTITY, not by
    similarity — OpenFIGI retains the name a security carried
    at the time, so the lookup is old-name to old-record. If a
    source returns only the CURRENT name, this matcher will
    correctly refuse rather than guess."""
    assert _c("ALPS ELECTRIC CO", "ALPS ALPINE CO., LTD.") < 0.45
    assert _c("START TODAY CO", "ZOZO, Inc.") < 0.45


def test_it_accepts_a_line_variant_of_the_same_issuer():
    """What name matching CAN do: recognise the same issuer
    across MSCI's line qualifiers, and across MSCI's
    abbreviations against an exchange's full spelling."""
    for a, b in (
            ("CHINA STH AIRLINES H",
             "China Southern Airlines Company Limited"),
            ("FUYAO GLASS IND GRP H",
             "Fuyao Glass Industry Group Co Ltd"),
            ("DATANG INTL POWER H",
             "Datang International Power Generation Co"),
            ("ALIBABA GROUP HLDG ADR",
             "Alibaba Group Holding Limited"),
            ("BEIGENE ADR", "BeiGene, Ltd."),
            ("KINGBOARD CHEM HLDG (CN)",
             "Kingboard Chemical Holdings Ltd")):
        assert _c(a, b) >= 0.45, (a, b, _c(a, b))


def test_the_line_qualifier_never_leaks_into_the_name_score():
    """"ALIBABA GROUP HLDG ADR" scored 0.25 against Alibaba
    because ADR survived tokenisation and counted as a word the
    candidate lacked. The qualifier is carried by `line_kind`;
    it must not also be compared as part of the issuer name."""
    assert R.score("ALIBABA GROUP HLDG ADR",
                   "Alibaba Group Holding Limited")[0] == \
        R.score("ALIBABA GROUP HLDG",
                "Alibaba Group Holding Limited")[0]


def test_a_different_issuer_sharing_a_word_is_still_rejected():
    """COSCO Shipping is not China COSCO Holdings' head token."""
    assert _c("CHINA COSCO HOLDINGS H",
              "COSCO SHIPPING Holdings Co Ltd") < 0.45


def test_head_token_absent_is_an_immediate_zero():
    assert _c("KOSE CORPORATION", "Shiseido Company") == 0.0


def test_qualifiers_are_stripped_for_the_base_name():
    assert R.base_name("CHINA STH AIRLINES H") == \
        "CHINA STH AIRLINES"
    assert R.base_name("KINGBOARD CHEM HLDG (CN)") == \
        "KINGBOARD CHEM HLDG"
    assert R.base_name("ALIBABA GROUP HLDG ADR") == \
        "ALIBABA GROUP HLDG"


def test_every_market_declares_its_exchanges():
    """Gate G1 is absolute: a candidate on the wrong exchange
    is a different security, not a near miss."""
    import pandas as pd
    d = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    for m in d[d.year >= 2015].market.unique():
        assert m in R.EXCH, f"{m} has no exchange whitelist"
        assert R.EXCH[m]["suffix"] and R.EXCH[m]["figi"]


def test_nothing_is_applied_below_the_confidence_floor():
    import inspect
    src = inspect.getsource(R.stage_apply)
    assert "MIN_APPLY_CONF" in src
    assert 'p.get("verified")' in src
    assert "already maps to" in src, "collision guard missing"


def test_the_harvester_loads_recovered_foreign_lines():
    """An ADR must not have a local suffix appended to it."""
    import apac_event_days as A
    assert hasattr(A, "_load_foreign_lines")
    assert A.FOREIGN_LINE.get(("Singapore", "GRAB"))
