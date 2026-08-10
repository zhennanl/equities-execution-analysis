"""Pattern-discovery study — window features vs effective-date
outcomes, every MSCI TW change 2015-2026 (c-65, EXPLORATORY).

Features (PIT, announcement -> T-1): completion (abnormal volume /
per-stock expected), foreign_pp (SIGNED institutional flow),
wrongway flag, window price drift, volume-of-volume shift.
Outcomes (effective date +): T-day return, print multiple,
T+1..3 favorable move.

Methods: event-clustered Spearman correlations with permutation
p-values (labels shuffled BY EVENT, respecting clustering),
quartile contrasts, and a depth-limited tree with
leave-one-EVENT-out cross-validation. Exploratory: findings are
REGISTERED as hypotheses unless they replicate known adopted
results — nothing here is auto-adopted.

Data limitation stated: borrow (SBL) history in our caches begins
Apr-2026 — borrow-rate hypotheses are testable only on the May-26
cross-section (n=7); margin-short history is a fetchable weak
proxy for a future pass.

Usage: python scripts/pattern_study.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np                                     # noqa: E402
import pandas as pd                                    # noqa: E402

RNG = np.random.default_rng(7)


def build_panel():
    cache = json.loads((ROOT / "data" / "tw_vintage_cache.json")
                       .read_text(encoding="utf-8"))
    events = json.loads((ROOT / "data" / "msci_tw_events.json")
                        .read_text(encoding="utf-8"))
    base_panel = {(r["season"], r["code"]): r for r in json.loads(
        (ROOT / "data" / "liquidity_panel_tw.json")
        .read_text(encoding="utf-8"))["panel"]}
    rows = []
    for season, ev in sorted(events.items(),
                             key=lambda kv: kv[1]["ann"]):
        for side, key in (("add", "adds"), ("del", "dels")):
            for code in ev[key]:
                b = base_panel.get((season, code))
                px = cache.get(f"px|{code}")
                if not b or not px:
                    continue
                df = pd.DataFrame(px).set_index("date").sort_index()
                pre = df[df.index < ev["ann"]]
                win = df[(df.index >= ev["ann"])
                         & (df.index < ev["eff"])]
                t_rows = df[df.index >= ev["eff"]]
                if len(pre) < 40 or len(win) < 3 or not len(t_rows):
                    continue
                t = t_rows.index[0]
                i = df.index.get_loc(t)
                if i == 0:
                    continue
                prev_c = df.iloc[i - 1]["close"]
                tday_ret = (df.iloc[i]["close"] / prev_c - 1) * 100
                drift = (win["close"].iloc[-1]
                         / pre["close"].iloc[-1] - 1) * 100
                pre_vol = pre["close"].pct_change().tail(60).std()
                win_vol = win["close"].pct_change().std()
                rows.append({
                    "season": season, "code": code, "side": side,
                    "completion": b["completion"],
                    "foreign_pp": b["foreign_pp"],
                    "wrongway": b["wrongway"],
                    "window_drift_pct": round(float(drift), 1),
                    "vol_ratio": round(float(win_vol / pre_vol), 2)
                    if pre_vol else None,
                    "tday_ret_pct": round(float(tday_ret), 1),
                    "t_mult": b["t_mult"],
                    "fav3_pct": b["fav3_pct"]})
    return pd.DataFrame(rows)


def clustered_spearman(df, x, y, n_perm=2000):
    """Spearman rho + permutation p (shuffle y BY EVENT blocks)."""
    from scipy import stats as st
    sub = df.dropna(subset=[x, y])
    if len(sub) < 20:
        return None
    rho = float(st.spearmanr(sub[x], sub[y]).statistic)
    seasons = sub["season"].values
    yv = sub[y].values
    uniq = np.unique(seasons)
    count = 0
    for _ in range(n_perm):
        perm = {s: p for s, p in
                zip(uniq, RNG.permutation(uniq))}
        # map each event's y-block to another event's block
        y_shuf = np.empty_like(yv)
        for s in uniq:
            src = yv[seasons == perm[s]]
            dst_idx = np.where(seasons == s)[0]
            take = RNG.choice(src, size=len(dst_idx),
                              replace=True)
            y_shuf[dst_idx] = take
        r2 = st.spearmanr(sub[x].values, y_shuf).statistic
        if abs(r2) >= abs(rho):
            count += 1
    return {"rho": round(rho, 3),
            "perm_p": round(count / n_perm, 4),
            "n": int(len(sub)),
            "n_events": int(sub["season"].nunique())}


def quartile_contrast(df, x, y):
    sub = df.dropna(subset=[x, y])
    if len(sub) < 24:
        return None
    q1 = sub[sub[x] <= sub[x].quantile(0.25)][y]
    q4 = sub[sub[x] >= sub[x].quantile(0.75)][y]
    return {"bottom_q_mean": round(float(q1.mean()), 1),
            "top_q_mean": round(float(q4.mean()), 1),
            "spread": round(float(q4.mean() - q1.mean()), 1),
            "n_q": int(len(q4))}


def loo_event_tree(df, feats, target_col):
    """Depth-2 tree, leave-one-EVENT-out CV, sign prediction."""
    try:
        from sklearn.tree import DecisionTreeClassifier
    except Exception:                          # noqa: BLE001
        return {"note": "sklearn unavailable — skipped"}
    sub = df.dropna(subset=feats + [target_col]).copy()
    sub["y"] = (sub[target_col] > 0).astype(int)
    base = max(sub["y"].mean(), 1 - sub["y"].mean())
    hits = tot = 0
    for s in sub["season"].unique():
        tr, te = sub[sub["season"] != s], sub[sub["season"] == s]
        if not len(te) or tr["y"].nunique() < 2:
            continue
        m = DecisionTreeClassifier(max_depth=2, random_state=0)
        m.fit(tr[feats], tr["y"])
        hits += int((m.predict(te[feats]) == te["y"]).sum())
        tot += len(te)
    full = DecisionTreeClassifier(max_depth=2, random_state=0)
    full.fit(sub[feats], sub["y"])
    imp = dict(zip(feats, [round(float(v), 2)
                           for v in full.feature_importances_]))
    return {"loo_event_accuracy": round(hits / tot, 3) if tot
            else None, "base_rate": round(float(base), 3),
            "n": int(len(sub)), "feature_importance": imp}


def main():
    df = build_panel()
    dels = df[df["side"] == "del"]
    adds = df[df["side"] == "add"]
    tests = {}
    # T-day PRINT return relationships (deletions)
    for x, y, tag in (
            ("foreign_pp", "tday_ret_pct", "D1_foreign_vs_tdayret"),
            ("completion", "tday_ret_pct", "D2_compl_vs_tdayret"),
            ("window_drift_pct", "tday_ret_pct",
             "D3_drift_vs_tdayret"),
            ("window_drift_pct", "fav3_pct", "D4_drift_vs_fav3"),
            ("completion", "t_mult", "D5_compl_vs_tmult"),
            ("vol_ratio", "tday_ret_pct", "D6_vol_vs_tdayret"),
            ("foreign_pp", "fav3_pct", "D7_foreign_vs_fav3")):
        tests[tag] = {"spearman": clustered_spearman(dels, x, y),
                      "quartiles": quartile_contrast(dels, x, y)}
    # adds (smaller n)
    for x, y, tag in (
            ("foreign_pp", "tday_ret_pct", "A1_foreign_vs_tdayret"),
            ("window_drift_pct", "tday_ret_pct",
             "A2_drift_vs_tdayret")):
        tests[tag] = {"spearman": clustered_spearman(adds, x, y),
                      "quartiles": quartile_contrast(adds, x, y)}
    ml = {
        "del_sign_fav3": loo_event_tree(
            dels, ["completion", "foreign_pp",
                   "window_drift_pct", "vol_ratio"], "fav3_pct"),
        "del_sign_tday": loo_event_tree(
            dels, ["completion", "foreign_pp",
                   "window_drift_pct", "vol_ratio"],
            "tday_ret_pct")}
    out = {"n_name_events": int(len(df)),
           "n_dels": int(len(dels)), "n_adds": int(len(adds)),
           "borrow_limitation": "SBL history held only from "
           "Apr-2026 — borrow hypotheses testable on May-26 "
           "cross-section only (n=7); margin-short proxy fetch "
           "queued",
           "tests": tests, "ml": ml,
           "panel": df.to_dict("records")}
    (ROOT / "data" / "pattern_study_tw.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    for tag, t in tests.items():
        s = t["spearman"]
        q = t["quartiles"]
        if s:
            print(f"{tag:24s} rho {s['rho']:+.3f} p {s['perm_p']:.3f} "
                  f"(n {s['n']}/{s['n_events']}ev)"
                  + (f" | Q1 {q['bottom_q_mean']} Q4 "
                     f"{q['top_q_mean']} spread {q['spread']}"
                     if q else ""))
    print("ML:", json.dumps(ml, indent=1))


if __name__ == "__main__":
    main()
