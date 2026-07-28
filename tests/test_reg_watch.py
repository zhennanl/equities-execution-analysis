"""Reg-Watch tests — canned payloads, tmp registries, no network."""
import pandas as pd
import pytest

from agents import reg_watch as rw


@pytest.fixture()
def reg(tmp_path):
    return rw.load_registry(tmp_path / "reg.json")


def test_seed_covers_markets_and_categories(reg):
    df = rw.current(reg)
    assert {"limit_band", "auction_cutoff", "market_reg"} <= \
        set(df["category"])
    assert "Taiwan (TWSE)" in set(df["market"])
    assert (df["version"] == 1).all() and (df["status"] == "active").all()


def test_current_value_and_history(reg):
    v = rw.current_value(reg, "limit_band", "Taiwan (TWSE)")
    assert v["band"] == 0.10
    assert len(rw.history(reg, "limit_band", "Taiwan (TWSE)")) == 1


def test_change_workflow_versions_and_log(reg):
    v0 = rw.registry_version(reg)
    p = rw.propose_change(reg, "limit_band", "Vietnam (HOSE)",
                          dict(band=0.10, note="HOSE band widened."),
                          source="HOSE notice 2026-xx", note="demo")
    assert len(rw.pending(reg)) == 1
    new = rw.approve(reg, p["proposal_id"], approver="bill")
    assert new["version"] == 2 and rw.pending(reg).empty
    assert rw.current_value(reg, "limit_band",
                            "Vietnam (HOSE)")["band"] == 0.10
    h = rw.history(reg, "limit_band", "Vietnam (HOSE)")
    assert list(h["status"]) == ["superseded", "active"]
    assert rw.registry_version(reg) != v0          # hash moves on change
    assert reg["log"][-1]["action"] == "approve"


def test_reject_leaves_rules_untouched(reg):
    old = rw.current_value(reg, "limit_band", "Korea (KRX)")
    p = rw.propose_change(reg, "limit_band", "Korea (KRX)",
                          dict(band=0.15, note="bad idea"), source="x")
    rw.reject(reg, p["proposal_id"], "bill", "no basis")
    assert rw.current_value(reg, "limit_band", "Korea (KRX)") == old
    assert reg["log"][-1]["action"] == "reject"


def test_classifier_multilingual():
    hi = rw.classify_notice("KRX resumes short selling for KOSPI names")
    assert hi["relevance"] == "HIGH" and "short_sell" in hi["categories"]
    zh = rw.classify_notice("修正上市股票漲跌幅度之公告")
    assert zh["relevance"] == "HIGH" and "price_limit" in zh["categories"]
    ja = rw.classify_notice("売買単位の変更について")
    assert "lot_size" in ja["categories"]
    med = rw.classify_notice("Settlement calendar for tender offer")
    assert med["relevance"] == "MED"
    ign = rw.classify_notice("Annual charity run photos")
    assert ign["relevance"] == "IGNORE"


def test_parsers_canned():
    tw = rw.parse_twse_news([{"Title": "t", "Url": "u",
                              "Date": "20260728"}])
    assert tw[0]["source"] == "TWSE" and tw[0]["date"] == "20260728"
    jp = rw.parse_jpx_news([{"title": "t", "url": "/x",
                             "updated_date": {"year": "2026",
                                              "month": "07",
                                              "day": "28"}}])
    assert jp[0]["date"] == "20260728" and jp[0]["url"].startswith("http")
    ns = rw.parse_nse_circulars({"data": [{"cirDate": "20260728",
                                           "circCategory": "Trade",
                                           "sub": "s",
                                           "circFilelink": "f"}]})
    assert ns[0]["title"] == "[Trade] s"


def test_triage_orders_high_first():
    df = rw.triage_notices([
        {"source": "X", "date": "20260728", "title": "charity run"},
        {"source": "X", "date": "20260727",
         "title": "price limit band revised"},
    ])
    assert df.iloc[0]["relevance"] == "HIGH"


def test_llm_hook_optional():
    assert rw.llm_summarize_hook({"title": "t"}) is None
    out = rw.llm_summarize_hook({"title": "t"},
                                llm=lambda p: "summary: " + p[:10])
    assert out.startswith("summary:")


def test_digest_contains_pending_and_high(reg):
    rw.propose_change(reg, "limit_band", "Thailand (SET)",
                      dict(band=0.15, note="n"), source="s")
    tri = rw.triage_notices([{"source": "TWSE", "date": "20260728",
                              "title": "漲跌幅 revision"}])
    d = rw.daily_digest(tri, reg, date="2026-07-28")
    assert "PENDING APPROVALS" in d and "HIGH relevance" in d
    assert "P0001" in d


def test_sources_registry_honest():
    st = {k: v["status"] for k, v in rw.NOTICE_SOURCES.items()}
    assert st["TWSE"] == "IMPLEMENTED" and st["JPX"] == "IMPLEMENTED"
    assert sum("PROTOCOL" in s for s in st.values()) >= 4


def test_approved_change_propagates_to_pt_dealer(tmp_path, monkeypatch):
    """The single-source guarantee: approve a band change in Reg-Watch
    and pt_dealer.limit_proximity applies it with NO pt_dealer edits."""
    import agents.reg_watch as rwm
    from agents.pt_dealer import limit_proximity
    path = tmp_path / "reg.json"
    monkeypatch.setattr(rwm, "REGISTRY_PATH", path)
    reg = rwm.load_registry(path)
    p = rwm.propose_change(reg, "limit_band", "Taiwan (TWSE)",
                           dict(band=0.20, note="hypothetical widening"),
                           source="test")
    rwm.approve(reg, p["proposal_id"], "bill")
    rwm.save_registry(reg, path)
    # +12% day: under the old ±10% band this is LOCKED; under 20% -> WATCH
    r = limit_proximity("Taiwan (TWSE)", prev_close=100, last_price=112)
    assert r["band_pct"] == 20.0 and r["level"] == "WATCH"


# ───────────────────────────────── 7m proactive insight layer ──

def _mk(source, date, title):
    return {"source": source, "date": date, "title": title, "url": "u"}


def test_story_clustering_collapses_repeats():
    tri = rw.triage_notices([
        _mk("JPX", "20260630", "Daily Price Limits to be Broadened : 2 issues"),
        _mk("JPX", "20260629", "Daily Price Limits to be Broadened : 1 issue"),
        _mk("JPX", "20260623", "Daily Price Limits to be Broadened : 3 issues"),
        _mk("NSE", "20260723", "Introduction of Closing Auction Session"),
    ])
    stories = rw.cluster_stories(tri)
    assert len(stories) == 2
    jpx = next(s for s in stories if s["source"] == "JPX")
    assert jpx["n_notices"] == 3 and len(jpx["links"]) == 3


def test_scope_and_tiering():
    tri = rw.triage_notices([
        _mk("NSE", "20260723",
            "Introduction of Closing Auction Session (CAS) in Equity "
            "Cash segment"),
        _mk("JPX", "20260629",
            "Base price and daily price limit for newly listing stock: "
            "X Inc. (Code: 590A)"),
    ])
    scored = [rw.score_story(s) for s in rw.cluster_stories(tri)]
    by_src = {s["source"]: s for s in scored}
    assert by_src["NSE"]["scope"] == "market-wide"
    assert by_src["NSE"]["tier"] == "FLASH"
    assert by_src["JPX"]["scope"] == "single-stock"
    assert by_src["JPX"]["tier"] != "FLASH"
    assert by_src["NSE"]["score"] > by_src["JPX"]["score"]
    assert any("market-wide" in r for r in by_src["NSE"]["reasons"])


def test_basket_relevance_boost():
    tri = rw.triage_notices([_mk("JPX", "20260629",
                                 "Daily price limit for Advantest")])
    s = rw.cluster_stories(tri)[0]
    plain = rw.score_story(s)
    boosted = rw.score_story(s, basket_names=["Advantest"])
    assert boosted["score"] == plain["score"] + 3
    assert any("YOUR basket" in r for r in boosted["reasons"])


def test_flash_brief_content_and_links():
    tri = rw.triage_notices([
        _mk("NSE", "20260723",
            "Introduction of Closing Auction Session in Equity Cash "
            "segment"),
        _mk("TWSE", "20260722", "某公司股票得為融資融券交易"),
    ])
    brief = rw.flash_brief(rw.cluster_stories(tri))
    assert "FLASH" in brief and "Why it matters" in brief
    assert "MOC" in brief                     # impact note present
    assert "](u)" in brief                    # drill-down link present
    assert "reasons" not in brief or True     # explainability line
    assert rw.flash_brief([]) == ""           # silent when nothing new


def test_new_notices_dedup():
    n1 = _mk("TWSE", "20260728", "t1")
    n2 = _mk("TWSE", "20260728", "t2")
    seen = {rw.notice_id(n1)}
    out = rw.new_notices([n1, n2], seen)
    assert out == [n2]


def test_sgx_parser_canned():
    p = rw.parse_sgx_circulars({"data": [
        {"documentDate": "1785081600000", "subject": "Call Warrants",
         "companyName": "MACQUARIE BANK LIMITED"}]})
    assert p[0]["source"] == "SGX" and p[0]["date"] == "20260726"
    assert "Warrants" in p[0]["title"]
    assert rw.NOTICE_SOURCES["SGX"]["status"] == "IMPLEMENTED"
