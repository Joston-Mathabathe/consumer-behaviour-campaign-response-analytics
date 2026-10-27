import numpy as np
import pandas as pd
import pytest

from src import business, data, modelling


@pytest.fixture(scope="module")
def df():
    return data.clean(data.load_raw())


def test_row_count_and_target(df):
    assert len(df) == 41188
    assert set(df.subscribed.unique()) == {0, 1}
    assert abs(df.subscribed.mean() - 0.1127) < 1e-3


def test_no_missing_after_clean(df):
    assert df[data.CAT_MISSING].isna().sum().sum() == 0


def test_duration_never_in_model_features():
    for macro in (True, False):
        assert "duration" not in modelling.feature_cols(macro)
        assert "subscribed" not in modelling.feature_cols(macro)


def test_oot_split_is_chronological(df):
    tr, te = modelling.split(df, "oot")
    assert tr.campaign_order.max() < te.campaign_order.min()


def test_gains_table_is_consistent():
    rng = np.random.default_rng(0)
    s = rng.random(1000); y = (rng.random(1000) < s * 0.3).astype(int)
    g = business.gains_table(y, s)
    assert g.contacts.sum() == 1000 and g.subscribers.sum() == y.sum()
    assert g.cum_capture_pct.iloc[-1] == pytest.approx(1.0)
    assert g.lift.iloc[0] > g.lift.iloc[-1]


def test_profit_curve_endpoints():
    y = np.array([1, 0, 0, 0, 1, 0, 0, 0, 0, 0]); s = np.linspace(1, 0, 10)
    c = business.profit_curve(y, s, cost_per_call=5, value_per_sub=100, points=10)
    assert c.profit.iloc[-1] == 2 * 100 - 10 * 5      # call everyone
    assert c.profit.max() >= c.profit.iloc[-1]


def test_exclude_removes_feature():
    assert "campaign" not in modelling.feature_cols(True, exclude=("campaign",))
    assert "campaign" in modelling.feature_cols(True)


def test_sensitivity_grid_is_complete_and_sane():
    rng = np.random.default_rng(1)
    s = rng.random(2000); y = (rng.random(2000) < s * 0.4).astype(int)
    g = business.sensitivity(y, s, [2, 20], [50, 300])
    assert len(g) == 4
    assert (g.uplift_vs_call_everyone >= -1e-9).all()          # optimal cutoff never loses to "call everyone"
    hi = g[(g.cost_per_call == 20) & (g.value_per_subscriber == 50)].optimal_pct_contacted.iloc[0]
    lo = g[(g.cost_per_call == 2) & (g.value_per_subscriber == 300)].optimal_pct_contacted.iloc[0]
    assert hi < lo                                              # dearer calls / lower value -> contact fewer


def test_segmentation_returns_one_label_per_row(df):
    from src import segmentation
    sub = df.sample(1500, random_state=0)
    labels = segmentation.fit_segments(sub, 4)
    assert len(labels) == len(sub) and len(set(labels)) == 4
