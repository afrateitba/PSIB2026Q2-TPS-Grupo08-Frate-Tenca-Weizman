import numpy as np
import pandas as pd
import pytest

from src.evaluation.final import fill_from_nearest, h1_subject_deltas, h2_bootstrap
from src.stats.compare import pooled_auc


# --- fill_from_nearest ---------------------------------------------------
def test_fill_takes_nearest_valid_minute():
    m = np.arange(6)
    ok = np.array([False, True, False, False, True, False])
    v = np.array([np.nan, 10., np.nan, np.nan, 40., np.nan])
    out = fill_from_nearest(m, {"F": v}, ok)["F"]
    # 0->1, 2->1, 3->4, 5->4
    np.testing.assert_array_equal(out, [10, 10, 10, 40, 40, 40])


def test_fill_tie_goes_to_earlier():
    out = fill_from_nearest([0, 1, 2], {"x": [1., np.nan, 3.]}, [True, False, True])["x"]
    assert out[1] == 1.0


def test_fill_keeps_valid_and_handles_unsorted_and_single():
    out = fill_from_nearest([5, 3, 4], {"x": [50., np.nan, np.nan]}, [True, False, False])["x"]
    np.testing.assert_array_equal(out, [50, 50, 50])
    m = np.array([3, 0, 2, 1])
    ok = np.array([True, True, False, False])
    out = fill_from_nearest(m, {"x": [30., 0., np.nan, np.nan]}, ok)["x"]
    np.testing.assert_array_equal(out, [30, 0, 30, 0])     # 2->3, 1->0


def test_fill_without_valid_minutes_is_nan():
    out = fill_from_nearest([0, 1], {"x": [1., 2.]}, [False, False])["x"]
    assert np.isnan(out).all()


def test_fill_invalid_lengths():
    with pytest.raises(ValueError):
        fill_from_nearest([0, 1], {"x": [1.]}, [True, True])


# --- h2_bootstrap --------------------------------------------------------
def _toy(seed=0, n_subj=8, recs_per=2, n_min=80):
    rng = np.random.default_rng(seed)
    rows = []
    for s in range(n_subj):
        for k in range(recs_per):
            frac = rng.uniform(0.05, 0.8)
            y = (rng.random(n_min) < frac).astype(int)
            rows.append(pd.DataFrame({"record": f"r{s}_{k}", "subject": f"S{s}", "y": y,
                                      "good": y * 2.0 + rng.normal(0, 0.5, n_min),
                                      "noise": rng.normal(0, 1, n_min)}))
    return pd.concat(rows, ignore_index=True)


def test_h2_good_feature_beats_noise():
    d = _toy()
    r = h2_bootstrap(d.good, d.noise, d.y, d.record, d.subject, 1.0, 0.0, n_boot=500)
    m1 = r.loc["M1: AUC por minuto"]
    assert m1.F == pytest.approx(pooled_auc(d.good.to_numpy(), d.y.to_numpy()))
    assert m1.F > 0.9 and 0.35 < m1.referencia < 0.65
    assert m1.ic_lo > 0 and m1.p < 0.01
    m2 = r.loc["M2: acierto por registro"]
    assert m2.F > 0.8 and m2.diferencia > 0 and m2.p < 0.05


def test_h2_identical_features_no_difference():
    d = _toy(1)
    r = h2_bootstrap(d.good, d.good, d.y, d.record, d.subject, 1.0, 1.0, n_boot=200)
    assert (r.diferencia == 0).all() and (r.ic_lo == 0).all() and (r.ic_hi == 0).all()
    assert (r.p == 1.0).all()


def test_h2_reproducible_and_validates():
    d = _toy(2)
    a = h2_bootstrap(d.good, d.noise, d.y, d.record, d.subject, 1.0, 0.0, n_boot=100, seed=7)
    b = h2_bootstrap(d.good, d.noise, d.y, d.record, d.subject, 1.0, 0.0, n_boot=100, seed=7)
    pd.testing.assert_frame_equal(a, b)
    bad = d.good.to_numpy().copy(); bad[0] = np.nan
    with pytest.raises(ValueError):
        h2_bootstrap(bad, d.noise, d.y, d.record, d.subject, 1.0, 0.0, n_boot=10)


# --- h1_subject_deltas ---------------------------------------------------
def test_h1_deltas_known_values():
    t = pd.DataFrame({"record": ["a"] * 12 + ["b"] * 12, "subject": ["S1"] * 24,
                      "label": ([1] * 6 + [0] * 6) * 2, "corrected": 0.0})
    v = np.r_[[3.] * 6, [1.] * 6, [5.] * 6, [1.] * 6]       # a: +2, b: +4
    subj, per_rec = h1_subject_deltas(t, v)
    assert subj["S1"] == pytest.approx(3.0)
    assert list(per_rec.record) == ["a", "b"]


def test_h1_deltas_quality_and_minimum():
    t = pd.DataFrame({"record": "a", "subject": "S1", "label": [1] * 6 + [0] * 6,
                      "corrected": [0.5] * 2 + [0.0] * 10})
    v = np.r_[[3.] * 6, [1.] * 6]
    assert len(h1_subject_deltas(t, v)[0]) == 0                 # quedan 4 de apnea < 5
    assert len(h1_subject_deltas(t, v, max_corrected=None)[0]) == 1