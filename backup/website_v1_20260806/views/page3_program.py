"""Page 3 — Program Trading Desk (extracted from app.py, B8)."""
from views.common import *          # noqa: F401,F403 — shared imports
from views.common import _badge, _AC, _VC, _TC, _cached_fetch  # noqa: F401


def render():

    from agents.program_trading import (market_status_board, regulation_reference,
                                        run_program_pretrade, wave_plan, program_recon)

    st.title("🧺 Program Trading Desk — Asia Cross-Market")
    st.markdown(
        "Basket execution support across the platform's 15 markets: live session "
        "clock, market-microstructure regulation reference (lot sizes, short-sale "
        "regimes, circuit breakers, settlement cycles), a program pre-trade blotter "
        "with per-name compliance and capacity flags, a cross-market execution wave "
        "plan, and a simulated end-of-day reconciliation."
    )
    st.caption("⚠️ Desk-reference quality, honestly labelled: session times and "
               "regulatory notes are stylized (no exchange holiday calendars, DST "
               "approximated for US/UK/AU, HK board lots vary per stock) — always "
               "verify against the exchange notice.")

    st.markdown("### 🕐 Market Session Board")
    _now_utc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    st.caption(f"As of **{_now_utc.strftime('%H:%M')} UTC** — open markets first, "
               "earliest close first (the order a program desk works them).")
    _board = market_status_board(_now_utc)
    def _phase_style(row):
        color = {"Open": "background-color:#dcfce7;", "Lunch": "background-color:#fef9c3;",
                 "Pre-open": "background-color:#e0f2fe;", "Closed": "background-color:#f3f4f6;"}
        return [color.get(row["phase"], "")] * len(row)
    st.dataframe(_board.style.apply(_phase_style, axis=1), use_container_width=True,
                 hide_index=True)

    st.markdown("### 📜 Regulation & Microstructure Reference")
    st.dataframe(regulation_reference(), use_container_width=True, hide_index=True,
                 height=560)

    st.markdown("### 📦 Program Pre-Trade Blotter")
    st.caption("Upload the program as CSV: `ticker,market,side[,shares][,locate]` "
               "(shares default to 5% of each name's ADV; locate=true for confirmed "
               "borrows on sells). One data fetch per name — run once, not repeatedly.")
    pt_file = st.file_uploader("Program CSV", type="csv", key="p3_csv")
    if st.button("▶ Run program pre-trade", key="p3_run", disabled=pt_file is None):
        try:
            pt_df = pd.read_csv(pt_file)
            pt_df.columns = [c.strip().lower() for c in pt_df.columns]
            missing = {"ticker", "market"} - set(pt_df.columns)
            if missing:
                st.error(f"❌ CSV missing column(s): {', '.join(sorted(missing))}")
            else:
                with st.spinner(f"Pre-trading {len(pt_df)} names…"):
                    st.session_state["p3_blotter"] = run_program_pretrade(pt_df)
        except Exception as e:
            st.error(f"❌ Program failed: {e}")

    pt_res = st.session_state.get("p3_blotter")
    if pt_res is not None:
        _nred = int((pt_res["Flag"] == "RED").sum())
        _nerr = int((pt_res["Error"] != "").sum())
        _nblock = int(pt_res["Notes"].str.contains("BLOCK", na=False).sum())
        st.markdown(f"**{len(pt_res)} name(s)** · {_nred} capacity RED · "
                    f"{_nblock} short-sale BLOCK · {_nerr} failed")
        st.dataframe(pt_res, use_container_width=True, hide_index=True)
        pc1, pc2 = st.columns(2)
        with pc1:
            st.download_button("⬇️ Blotter (.csv)", pt_res.to_csv(index=False),
                               file_name="program_blotter.csv", use_container_width=True)
        with pc2:
            st.download_button("⬇️ Reconciliation report (.txt)", program_recon(pt_res),
                               file_name="program_recon.txt", use_container_width=True)

        st.markdown("### 🌏 Execution Wave Plan")
        st.caption("The program's markets ordered by closing time (UTC) — work the "
                   "earliest close first; names in already-closed markets roll to the "
                   "next session.")
        st.dataframe(wave_plan(pt_res["Market"].dropna().unique().tolist(), _now_utc),
                     use_container_width=True, hide_index=True)
        st.caption("Coordination logic: complete Tokyo/Taipei before the China lunch "
                   "reopen, HK/China before India's close, and carry residuals into "
                   "EU/US. Names flagged RED here are candidates for multi-day "
                   "schedules (gap register I-10).")


    # ── PT Dealer Cockpit (session 6h — CLSA PT Dealer JD) ────────────────
    st.markdown("### 🎛️ PT Dealer Cockpit")
    st.caption("The minute-to-minute view: limit proximity, close-auction "
               "cutoffs, and a ranked attention queue with explicit reasons. "
               "Load the demo basket or edit it into your own. Rule tables "
               "are static approximations of public exchange rules — a desk "
               "deployment swaps in exchange parameter feeds.")
    from agents.pt_dealer import (demo_basket, attention_queue,
                                  auction_countdown, build_audit_pack)
    import datetime as _dtc
    import json as _jsonc
    if "pt_basket" not in st.session_state:
        st.session_state["pt_basket"] = demo_basket()
    basket = st.data_editor(st.session_state["pt_basket"], num_rows="dynamic",
                            use_container_width=True, key="pt_basket_editor")
    _now = _dtc.datetime.now(_dtc.timezone.utc).replace(tzinfo=None)
    try:
        st.markdown("**⏱ Close-auction cutoffs (most urgent first)**")
        st.dataframe(auction_countdown(basket["market"].dropna().unique(), _now),
                     use_container_width=True, hide_index=True)
        st.markdown("**🚨 Attention queue — who needs your eyes now, and why**")
        q = attention_queue(basket.dropna(subset=["ticker", "market"]), _now)
        st.dataframe(q, use_container_width=True, hide_index=True)
        _pack = build_audit_pack(basket.dropna(subset=["ticker", "market"]),
                                 f"PGM-{_now:%Y%m%d}",
                                 _now.replace(tzinfo=_dtc.timezone.utc))
        st.download_button("⬇️ Audit pack (.json) — timestamped checks, "
                           "written now, not reconstructed later",
                           _jsonc.dumps(_pack, indent=1),
                           file_name=f"audit_pack_{_now:%Y%m%d_%H%M}.json",
                           use_container_width=True)
    except Exception as e:
        st.warning(f"Cockpit needs a valid basket (ticker/market/side/"
                   f"prev_close/last_price/filled_frac/elapsed_frac): {e}")


    # ── Desk automations (session 6i — "what would you automate?") ────────
    st.markdown("### 🤖 Desk Automations")
    st.caption("Each of these is the implemented answer to \"what would you "
               "automate if you joined the desk?\" — pre-open pack, "
               "transition-based alerts with acknowledged audit trail, EOD "
               "client draft, recon break classifier, index-event radar. "
               "All from the basket above.")
    from agents.pt_automation import (preopen_pack, alert_scan, acknowledge,
                                      eod_client_summary, classify_breaks,
                                      event_radar)
    _bk = basket.dropna(subset=["ticker", "market"])
    with st.expander("📋 A1 — Pre-open basket pack"):
        try:
            _pp = preopen_pack(_bk)
            st.code(_pp["text"])
            st.dataframe(_pp["per_name"], use_container_width=True,
                         hide_index=True)
            st.download_button("⬇️ Pack (.txt)", _pp["text"],
                               file_name="preopen_pack.txt")
        except Exception as e:
            st.warning(f"Pack needs shares/prev_close (+ optional "
                       f"adv_shares): {e}")
    with st.expander("🔔 A2 — Intraday alerts (fire on transition, ack → audit log)"):
        try:
            _alerts, _state = alert_scan(_bk,
                                         st.session_state.get("pt_alert_state"),
                                         _now)
            st.session_state["pt_alert_state"] = _state
            if _alerts:
                st.dataframe(pd.DataFrame(_alerts), use_container_width=True,
                             hide_index=True)
                if st.button(f"Acknowledge {len(_alerts)} alert(s) → audit log"):
                    acknowledge(_alerts, who="dealer")
                    st.success("Logged with rules version — the ack IS the "
                               "audit record.")
            else:
                st.info("No NEW alerts this scan (transition-based — "
                        "existing conditions don't re-page).")
        except Exception as e:
            st.warning(f"Alert scan: {e}")
    with st.expander("✉️ A3 — EOD client summary draft"):
        try:
            _txt = eod_client_summary(_bk, f"PGM-{_now:%Y%m%d}")
            st.code(_txt)
            st.download_button("⬇️ Draft (.txt)", _txt,
                               file_name="eod_summary.txt")
        except Exception as e:
            st.warning(f"Draft: {e}")
    with st.expander("🧾 A4 — Recon break classifier (demo street confirms)"):
        try:
            _ours = _bk[["ticker", "market"]].copy()
            _ours["shares"] = _bk["shares"] * _bk["filled_frac"]
            _ours["avg_price"] = _bk["last_price"]
            _street = _ours.copy()
            _street.loc[_street.index[0], "shares"] *= 0.98        # qty break
            _street.loc[_street.index[1], "avg_price"] *= 1.001    # px break
            _street = _street.iloc[:-1]                            # missing street
            _br, _sm = classify_breaks(_ours, _street)
            st.dataframe(_br, use_container_width=True, hide_index=True)
            st.caption(f"Summary: {_sm} — AUTO_CLEAR handled; humans keep "
                       "the ambiguous tail.")
        except Exception as e:
            st.warning(f"Recon demo: {e}")
    with st.expander("📡 A5 — Index-event radar (offline cadence rules)"):
        try:
            st.dataframe(event_radar(_bk), use_container_width=True,
                         hide_index=True)
            st.caption("Approximate provider cadence (Agent 12); the dealer "
                       "confirms actual membership from announcements. "
                       "Volume multiple from the event library when it has "
                       "history.")
        except Exception as e:
            st.warning(f"Radar: {e}")
    st.caption("A6 — every artifact above is stamped with the rule-table "
               "version hash; the QBR module (Page 4) is automation #7, the "
               "quarterly client review pack.")

    st.markdown("### 🧰 Desk Automations — round 2 (session 6m)")
    from agents.pt_ops import (normalize_client_file, closure_warnings,
                               settlement_date_holiday_aware, crossing_report,
                               exposure_schedule, FX_NOTES)
    with st.expander("📥 A8 — Client file normalizer (Bloomberg codes, "
                     "sides, notional→shares)"):
        _demo_file = pd.DataFrame({
            "Symbol": ["2330 TT", "700 HK", "7203 JT", "700 HK", "MYSTERY XX"],
            "Side": ["B", "SELL", "1", "S", "B"],
            "Qty": [1000, 2000, 300, 1000, 100]})
        st.dataframe(_demo_file, use_container_width=True, hide_index=True)
        _nr = normalize_client_file(_demo_file)
        st.dataframe(_nr["basket"], use_container_width=True, hide_index=True)
        for _i in _nr["issues"]:
            st.warning(_i, icon="📎")
        st.caption("The file is never silently 'fixed' — every guess and "
                   "skip is an explicit issue for the dealer to confirm.")
    with st.expander("📅 A9 — Holiday-aware settlement & closures (+FX notes)"):
        _today = _now.date()
        for _w in closure_warnings(
                [m for m in basket["market"].dropna().unique()], _today):
            st.warning(_w, icon="📅")
        _sd = [{"Market": m,
                **{k: str(v) for k, v in
                   settlement_date_holiday_aware(m, _today).items()
                   if k != "holidays_skipped"}}
               for m in basket["market"].dropna().unique()]
        st.dataframe(pd.DataFrame(_sd), use_container_width=True,
                     hide_index=True)
        st.dataframe(pd.DataFrame(FX_NOTES), use_container_width=True,
                     hide_index=True)
        st.caption("2026 calendar is approximate & partial — production "
                   "wires the exchange calendar feed (automation A7).")
    with st.expander("🔀 A10 — Internal crossing detector (per-market "
                     "mechanism)"):
        _cb = pd.DataFrame({
            "client": ["FundA", "FundB", "FundC", "FundA", "FundB"],
            "ticker": ["0700.HK", "0700.HK", "0700.HK", "600519.SS",
                       "600519.SS"],
            "market": ["Hong Kong (HKEX)"] * 3 + ["China-A Shanghai"] * 2,
            "side": ["Buy", "Sell", "Sell", "Buy", "Sell"],
            "shares": [10000, 6000, 3000, 5000, 5000],
            "price": [350.0] * 3 + [1500.0] * 2})
        _crx = crossing_report(_cb)
        st.dataframe(_crx["crosses"], use_container_width=True,
                     hide_index=True)
        st.caption(_crx["note"])
    with st.expander("⚖️ A11 — Two-sided exposure scheduler (urgency vs "
                     "funding path)"):
        _esb = basket.dropna(subset=["ticker"]).copy()
        _esb["price"] = _esb["last_price"]
        _es = exposure_schedule(_esb[["side", "shares", "price"]])
        if _es.get("available"):
            st.dataframe(_es["schedule"], use_container_width=True,
                         hide_index=True)
            st.caption(_es["note"])
        else:
            st.info(_es.get("reason", ""))
