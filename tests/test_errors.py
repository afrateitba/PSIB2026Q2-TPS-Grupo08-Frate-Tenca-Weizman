import numpy as np
import pandas as pd
import pytest

from src.evaluation.errors import distance_to_other, episode_lengths, error_table, subject_scores


def test_distance_to_other():
    y = np.array([0, 0, 1, 1, 1, 0, -1, 0])
    d = distance_to_other(y)
    assert d[[0, 1, 2, 3, 4, 5, 7]].tolist() == [2, 1, 1, 2, 1, 1, 3]
    assert np.isnan(d[6])                                   # sin etiqueta
    assert np.isinf(distance_to_other([0, 0, 0])).all()     # noche sin apnea
    assert distance_to_other([1, 0]).tolist() == [1, 1]


def test_episode_lengths():
    e = episode_lengths([0, 1, 1, 0, 1, 1, 1, 0, 1])
    assert np.isnan(e[[0, 3, 7]]).all()
    assert e[[1, 2, 4, 5, 6, 8]].tolist() == [2, 2, 3, 3, 3, 1]


def _pred():
    idx = pd.MultiIndex.from_tuples([("r1", m) for m in range(6)] + [("r2", m) for m in range(4)],
                                    names=["record", "minute"])
    label = [0, 0, 1, 1, 0, 0, 0, 0, 0, 0]
    predf = [0, 1, 1, 0, 0, 0, 1, 0, 0, 0]
    score = [0.1, 0.6, 0.9, 0.4, 0.2, 0.1, 0.7, 0.2, 0.1, 0.3]
    return pd.DataFrame({"label": label, "pred_F": predf, "score_F": score}, index=idx)


def test_error_table():
    pred = _pred()
    labs = {"r1": np.array([0, 0, 1, 1, 0, 0]), "r2": np.zeros(4, int)}
    t = error_table(pred, labs)
    assert t.tipo.tolist() == ["VN", "FP", "VP", "FN", "VN", "VN", "FP", "VN", "VN", "VN"]
    assert t.loc[("r1", 1), "distancia"] == 1 and np.isinf(t.loc[("r2", 0), "distancia"])
    assert t.loc[("r1", 3), "largo_episodio"] == 2
    assert (t.xs("r1").categoria == "C").all()              # 2 minutos de apnea: menos de 5


def test_subject_scores():
    pred = _pred()
    s = subject_scores(pred, pd.Series({"r1": "S1", "r2": "S2"}))
    assert s.loc["S1", "sensibilidad"] == 0.5 and s.loc["S1", "especificidad"] == 0.75
    assert s.loc["S1", "auc"] == pytest.approx(7 / 8)          # 0,4 queda debajo de un normal (0,6)
    assert np.isnan(s.loc["S2", "auc"]) and np.isnan(s.loc["S2", "sensibilidad"])
