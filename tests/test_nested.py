import numpy as np
import pandas as pd
import pytest

from src.evaluation.metrics import apply_night_calibration, fit_night_calibration, night_minutes
from src.stats.nested import (fold_auc, nested_cv, record_agreement_boot, record_table,
                              select_pipeline, subsample_h2)


def _toy(n_subj=10, n_min=120, seed=0):
    """Un registro por sujeto. 'buena' separa la apnea, 'ruido' no; la HRV es más débil."""
    rng = np.random.default_rng(seed)
    recs = [f"r{i:02d}" for i in range(n_subj)]
    frac = np.linspace(0.05, 0.7, n_subj)
    idx = pd.MultiIndex.from_product([recs, range(n_min)], names=["record", "minute"])
    y = np.concatenate([(rng.uniform(size=n_min) < f).astype(int) for f in frac])
    wf = pd.DataFrame({"buena": y + rng.normal(0, 0.6, len(y)),
                       "ruido": rng.normal(0, 1, len(y))}, index=idx)
    mf = pd.DataFrame({"complejidad": [(1,), (0,)]}, index=["buena", "ruido"])
    wh = pd.DataFrame({"hrv": y + rng.normal(0, 1.5, len(y)),
                       "hrv_ruido": rng.normal(0, 1, len(y))}, index=idx)
    mh = pd.DataFrame({"complejidad": [(1,), (0,)]}, index=["hrv", "hrv_ruido"])
    info = pd.DataFrame({"label": y, "corrected": 0.0}, index=idx)
    subject_of = pd.Series([f"S{i}" for i in range(n_subj)], index=recs)
    folds = [[f"S{i}", f"S{i + 5}"] for i in range(5)]
    return {"F": (wf, mf), "HRV": (wh, mh)}, info, subject_of, idx, folds


KW = dict(n_boot=100, n_boot_rec=50)


def test_select_pipeline_picks_informative_feature():
    fams, info, subject_of, idx, _ = _toy()
    subj = subject_of.loc[idx.get_level_values("record")].to_numpy()
    ch = select_pipeline(*fams["F"], info.label.to_numpy(), idx, subj, **KW)
    assert ch["base"] == "buena" and ch["signo"] == 1.0
    assert 0 < ch["umbral"] < 1                       # entre las dos clases (0 y 1 más ruido)


def test_nested_cv_covers_each_subject_once():
    fams, info, subject_of, idx, folds = _toy()
    pred, choices = nested_cv(fams, info, subject_of, idx, folds, **KW)
    recs = pred.index.get_level_values("record")
    assert set(recs) == set(subject_of.index)
    assert pred.groupby(level="record")["grupo"].nunique().max() == 1
    assert len(choices) == len(folds) * 2
    assert {"pred_F", "frac_F", "frac_cal_F", "score_HRV"} <= set(pred.columns)


def test_nested_cv_never_uses_heldout_labels():
    """Mezclar las etiquetas de los sujetos de afuera no cambia nada de lo elegido."""
    fams, info, subject_of, idx, folds = _toy()
    _, ch1 = nested_cv(fams, info, subject_of, idx, folds[:1], **KW)
    out = subject_of.index[subject_of.isin(folds[0])]
    perm = info.copy()
    m = perm.index.get_level_values("record").isin(out)
    perm.loc[m, "label"] = np.random.default_rng(1).permutation(perm.loc[m, "label"].to_numpy())
    pred2, ch2 = nested_cv(fams, perm, subject_of, idx, folds[:1], **KW)
    cols = ["variante", "signo", "umbral", "cal_a", "cal_b"]
    pd.testing.assert_frame_equal(ch1[cols], ch2[cols])


def test_fold_auc_and_record_agreement():
    fams, info, subject_of, idx, folds = _toy()
    pred, _ = nested_cv(fams, info, subject_of, idx, folds, **KW)
    a = fold_auc(pred, subject_of, n_boot=200)
    assert a.loc["F", "media"] > a.loc["HRV", "media"] > 0.5
    assert a.loc["F", "ic_lo"] <= a.loc["F", "media"] <= a.loc["F", "ic_hi"]
    t = record_table(pred, subject_of)
    r = record_agreement_boot(t, n_boot=200)
    assert r.loc["est_F", "spearman"] > 0.8


def test_perfect_scores_give_auc_one():
    fams, info, subject_of, idx, folds = _toy()
    pred, _ = nested_cv(fams, info, subject_of, idx, folds, **KW)
    pred["score_F"] = pred["label"].astype(float)
    assert fold_auc(pred, subject_of, n_boot=50).loc["F", "media"] == pytest.approx(1.0)


def test_night_minutes_and_calibration():
    t = night_minutes(["a", "a", "a", "b", "b"], [1, 0, 1, 0, 0], [1, 1, 1, 0, 1])
    assert t.loc["a", "min_anotados"] == 2 and t.loc["a", "min_estimados"] == 3
    assert t.loc["b", "horas"] == pytest.approx(2 / 60)
    x = np.array([0.1, 0.3, 0.5, 0.7])
    a, b = fit_night_calibration(x, 0.05 + 0.5 * x)
    assert a == pytest.approx(0.05) and b == pytest.approx(0.5)
    assert apply_night_calibration([-1.0, 0.5, 3.0], 0.0, 1.0).tolist() == [0.0, 0.5, 1.0]
    assert fit_night_calibration([0.2, 0.2], [0.1, 0.3]) == (0.0, 1.0)


def test_subsample_h2_runs_and_detects_a_clear_difference():
    fams, info, subject_of, idx, folds = _toy(n_subj=10, n_min=150)
    pred, _ = nested_cv(fams, info, subject_of, idx, folds, **KW)
    res = subsample_h2(pred, subject_of, n_subjects=8, n_draws=20, n_boot=200)
    assert len(res) == 20 and {"p_M1_holm", "p_M2_holm", "confirma_M1"} <= set(res.columns)
    assert (res["dif_M1"] > 0).mean() > 0.8
