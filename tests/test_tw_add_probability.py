"""Guards for the evidence-based P(addition) model (c-355).

WHAT THIS MODEL IS, in one line: the registered rule kept sharp,
Monte Carlo'd over the measured errors in its inputs, times a
registered haircut for MSCI's discretion. The failure modes worth
guarding are not arithmetic slips — they are the quiet edits that
would turn an evidence-based number back into a vibe:

  * the FIF error losing its BIAS (our floats run ~4% low; a
    zero-centred draw flatters every float verdict);
  * the float haircut creeping back in beside the Monte Carlo,
    double-counting the same risk;
  * the probabilities collapsing back to one flat number per
    zone, which is the exact defect this model exists to fix;
  * the contaminated top band of the backtest being read as
    calibration instead of as a warning.
"""
import json
import math
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
SRC = ROOT / "data" / "tw_add_probability.json"
DOC = ROOT / "docs" / "ADD_PROBABILITY.md"

pytestmark = pytest.mark.skipif(
    not SRC.exists(), reason="run scripts/tw_add_probability.py")


@pytest.fixture(scope="module")
def d():
    return json.loads(SRC.read_text(encoding="utf-8"))


def test_p_is_the_measured_probability_and_nothing_else(d):
    """c-360, Bill: the gates haircut is out of the product.
    P(add) IS P_size — the measured thing — and MSCI discretion
    is a named unpriced risk, not a multiplier."""
    for r in d["names"]:
        assert r["p_add"] == r["p_size_mc"], r["code"]
        assert "p_gates" not in r
        assert 0 < r["p_add"] <= 1


def test_probability_responds_to_clearance_distance(d):
    """THE POINT OF THE MODEL. The flat zone number could not
    tell 4.78x from 1.55x; this one must. Monotonicity is not
    strictly guaranteed (float and vol differ per name), so the
    guard is the economically meaningful contrast: every name
    clearing above 2x carries a higher P_size than the name
    nearest the bar."""
    rows = sorted(d["names"], key=lambda r: r["x_cutoff"])
    nearest = rows[0]
    assert nearest["x_cutoff"] < 2.0
    for r in rows[1:]:
        assert r["p_size_mc"] > nearest["p_size_mc"], (
            r["code"], nearest["code"])
    # and the near-bar name must NOT be near-certain — if input
    # error cannot fail a 1.55x clearance, the error model has
    # quietly been shrunk
    assert nearest["p_size_mc"] < 0.9, nearest


def test_the_fif_error_keeps_its_measured_bias(d):
    """Our floats run LOW against MSCI's implied FIFs. Centring
    the error at zero would flatter every float verdict, so the
    recorded distribution must keep both moments of the actual
    comparison, re-derived here from the source file."""
    fe = d["method"]["fif_error"]
    src = ROOT / "data" / "tw_fif_aligned_jul31.json"
    if not src.exists():
        pytest.skip("fif comparison missing")
    rows = json.loads(src.read_text(encoding="utf-8"))["rows"]
    errs = [r["yahoo"] / r["implied"] - 1 for r in rows
            if r.get("yahoo") and r.get("implied")]
    mu = sum(errs) / len(errs)
    sd = math.sqrt(sum((e - mu) ** 2 for e in errs) / len(errs))
    assert fe["n"] == len(errs)
    assert abs(fe["mean"] - mu) < 5e-4
    assert abs(fe["sd"] - sd) < 5e-4
    assert fe["mean"] < -0.01, "the bias is the point"


def test_discretion_is_named_but_never_multiplied(d):
    """c-360. The unpriced-risk block must NAME both pieces of
    MSCI discretion — a model that silently dropped the haircut
    without keeping the warning would overclaim — and no gates
    factor may survive anywhere in the output."""
    u = d["method"]["unpriced_discretion"]
    assert "count" in u["count_flex"].lower()
    assert "ATVR" in u["atvr"]
    assert "removed" in u["was"]
    raw = json.dumps(d)
    assert "p_gates" not in raw


def test_the_empirical_bands_reconcile_to_the_backtest(d):
    """The band table is differenced from the sweep; both must
    add back to the same totals, and the top band must carry its
    contamination note — 1-in-20 up there is gate-failure
    recurrence, not evidence that clearing hugely is bad."""
    bt = json.loads((ROOT / "data" / "backtest_taiwan.json")
                    .read_text(encoding="utf-8"))
    sw = sorted(bt["add_sweep"], key=lambda r: r["x_ceiling"])
    lo = sw[0]
    got_hits = sum(b["added"] for b in d["empirical_bands"])
    got_other = sum(b["not_added"] for b in d["empirical_bands"])
    assert got_hits == lo["hits"]
    assert got_other == lo["flagged_other"]
    top = d["empirical_bands"][-1]
    assert top["band_x_bar"][1] is None
    assert "contaminated" in top
    assert top["precision"] < 0.2
    # Wilson intervals are present and sane on every band
    for b in d["empirical_bands"]:
        lo_, hi_ = b["wilson_95"]
        assert 0 <= lo_ <= hi_ <= 1


def test_the_model_is_reproducible(d):
    """Seeded, so a re-run on the same inputs returns the same
    probabilities — the property that makes a registered number
    auditable rather than a one-off draw."""
    assert d["method"]["seed"] == 20260812
    import tw_add_probability as M
    assert M.SEED == d["method"]["seed"]
    assert M.DRAWS == d["method"]["draws"]


def test_the_page_renders_the_json_numbers():
    """Rendered-output guard, per the project's standing rule:
    the step-5 block must show each name's P(add) exactly as the
    JSON carries it, and the working must be inside a dropdown a
    reader can open."""
    from conftest import real_streamlit
    real_streamlit()
    from streamlit.testing.v1 import AppTest
    h = ROOT / "tests" / "_walk_prob_harness.py"
    h.write_text(
        f"import sys; sys.path.insert(0, {str(ROOT)!r})\n"
        "from views import walkthrough\nwalkthrough.render()\n",
        encoding="utf-8")
    try:
        at = AppTest.from_file(str(h), default_timeout=300).run()
        assert not at.exception, [e.value for e in at.exception]
        s = " ".join(m.value for m in at.markdown)
    finally:
        h.unlink(missing_ok=True)
    d = json.loads(SRC.read_text(encoding="utf-8"))
    # c-362: the section header, the institutional framing, the
    # discretion essay and the backtest warning are all cut at
    # Bill's request — the expander carries the method and the
    # per-name arithmetic, nothing else, and the cuts stay cut
    for gone in ("Probability of Addition, Name by Name",
                 "shape institutions use", "NOT priced",
                 "backtest's warning", "L&G"):
        assert gone not in s, gone
    for r in d["names"]:
        want = (">95%" if r["p_add"] > 0.95
                else f"{r['p_add']:.0%}")
        assert want in s, r["code"]
        assert f"{r['x_cutoff']:.2f}x" in s, r["code"]
    # the method expander exists (its LABEL is not markdown, so
    # it is asserted on the expander widget) and names its inputs
    # in the body
    try:
        h.write_text(
            f"import sys; sys.path.insert(0, {str(ROOT)!r})\n"
            "from views import walkthrough\nwalkthrough.render()\n",
            encoding="utf-8")
        at2 = AppTest.from_file(str(h), default_timeout=300).run()
        labs = [e.label for e in at2.expander]
    finally:
        h.unlink(missing_ok=True)
    assert any("how P(addition) is built" in x for x in labs), labs
    for token in ("20,000", "cutoff", "price date", "free float"):
        assert token in s, token


def test_border_deletions_are_priced_symmetrically(d):
    """c-359. The deletion side runs the SAME construction as the
    addition side — Monte Carlo distance from the floor times the
    registered gates — so the two columns of the step-5 table are
    one model, not two. Re-derived: P(delete) is the measured
    P_size with nothing multiplied in (c-360), the floor multiple
    matches the cap, and the vol input names its source."""
    dels = d.get("border_deletions")
    assert dels, "the border-deletion block is missing"
    for r in dels:
        assert r["p_delete"] == r["p_size_mc"], r["code"]
        # inside the +5% band by construction
        assert 1.0 <= r["x_floor"] < 1.05, r
        # a member 3% over the floor must price as genuinely
        # uncertain — neither ~0 nor ~1
        assert 0.1 < r["p_size_mc"] < 0.9, r
        assert r["vol_source"]
    # and P(delete) < P(add) of every carried add — a member
    # HELD by the rule cannot be more likely to leave than a
    # clearing candidate is to enter
    max_del = max(r["p_delete"] for r in dels)
    for r in d["names"]:
        if r["p_size_mc"] > 0.95:
            assert r["p_add"] > max_del


def test_the_table_carries_the_probability_column():
    """c-359, Bill: P(add) / P(delete) on the step-5 table. The
    rendered rows must show the model's numbers, labelled per
    side."""
    from conftest import real_streamlit
    real_streamlit()
    from streamlit.testing.v1 import AppTest
    h = ROOT / "tests" / "_walk_pcol_harness.py"
    h.write_text(
        f"import sys; sys.path.insert(0, {str(ROOT)!r})\n"
        "from views import walkthrough\nwalkthrough.render()\n",
        encoding="utf-8")
    try:
        at = AppTest.from_file(str(h), default_timeout=300).run()
        assert not at.exception, [e.value for e in at.exception]
        s = " ".join(m.value for m in at.markdown)
    finally:
        h.unlink(missing_ok=True)
    d = json.loads(SRC.read_text(encoding="utf-8"))
    # c-362: the headers lose the suffix; the label moves into
    # each row's right-most cell, per side
    assert "· P(add)**" not in s
    assert "· P(delete)**" not in s
    for r in d["names"]:
        # the display gap sits at 95% (c-362, Bill) — near-
        # certainties share one honest ">95%" label instead of a
        # false ranking among 99s
        want = (">95%" if r["p_add"] > 0.95
                else f"{r['p_add']:.0%}")
        assert f"P(add) {want}" in s, r["code"]
    for bad in ("P 100%", "P(add) 100%", ">99%"):
        assert bad not in s, bad
    for r in d["border_deletions"]:
        assert f"P(delete) {r['p_delete']:.0%}" in s, r["code"]


def test_the_doc_quotes_the_json(d):
    if not DOC.exists():
        pytest.skip("doc missing")
    doc = DOC.read_text(encoding="utf-8")
    for r in d["names"]:
        assert r["code"] in doc
        assert f"{r['p_add']:.0%}" in doc
    assert "discretion NOT priced" in doc
