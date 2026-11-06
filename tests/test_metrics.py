import numpy as np
import pytest

from src.evaluation.metrics import category_from_minutes, minute_metrics, record_metrics
from src.split import category_from_labels


# --- minute_metrics ------------------------------------------------------
def test_minute_metrics_known_counts():
    y = np.array([1, 1, 1, 1, 0, 0, 0, 0, 0, 0])
    p = np.array([1, 1, 1, 0, 1, 0, 0, 0, 0, 0])
    m = minute_metrics(y, p)
    assert (m["TP"], m["FN"], m["FP"], m["TN"]) == (3, 1, 1, 5)
    assert m["Se"] == pytest.approx(0.75)
    assert m["Esp"] == pytest.approx(5 / 6)
    assert m["exactitud"] == pytest.approx(0.8)
    assert m["exactitud_balanceada"] == pytest.approx((0.75 + 5 / 6) / 2)
    assert m["matriz"].loc["apnea", "apnea"] == 3
    assert m["matriz"].loc["normal", "apnea"] == 1
    assert m["matriz"].to_numpy().sum() == 10


def test_minute_metrics_accepts_bool_and_perfect():
    y = np.array([True, False, True])
    m = minute_metrics(y, y)
    assert m["Se"] == m["Esp"] == m["exactitud"] == 1.0


def test_minute_metrics_missing_class_gives_nan():
    m = minute_metrics([0, 0, 0], [0, 1, 0])
    assert np.isnan(m["Se"]) and m["Esp"] == pytest.approx(2 / 3)


def test_minute_metrics_invalid():
    with pytest.raises(ValueError):
        minute_metrics([0, 1], [0])
    with pytest.raises(ValueError):
        minute_metrics([0, 2], [0, 1])
    with pytest.raises(ValueError):
        minute_metrics([], [])


# --- categorías ----------------------------------------------------------
@pytest.mark.parametrize("m, cat", [(0, "C"), (4.9, "C"), (5, "B"), (99, "B"),
                                    (99.9, "B"), (100, "A"), (400, "A")])
def test_category_from_minutes(m, cat):
    assert category_from_minutes(m) == cat


@pytest.mark.parametrize("n", [0, 4, 5, 99, 100, 250])
def test_category_matches_split_rule(n):
    labels = np.r_[np.ones(n), np.zeros(300)]
    assert category_from_minutes(n) == category_from_labels(labels)


# --- record_metrics ------------------------------------------------------
def test_record_metrics_perfect_estimate():
    real = np.array([300.0, 50.0, 2.0, 150.0])
    h = np.array([8.0, 7.0, 9.0, 8.0])
    r = record_metrics(real, real, h, records=["a", "b", "c", "d"])
    assert r["spearman"] == pytest.approx(1.0)
    assert r["sesgo"] == 0 and r["lim_inf"] == 0 and r["lim_sup"] == 0
    assert r["acierto_categoria"] == 1.0
    assert list(r["tabla"].index) == ["a", "b", "c", "d"]
    assert r["tabla"].loc["a", "por_hora_anotado"] == pytest.approx(37.5)


def test_record_metrics_constant_overestimate():
    real = np.array([80.0, 160.0, 240.0])
    est = real + 8.0                                  # +1 min/h en 8 h
    r = record_metrics(est, real, [8.0, 8.0, 8.0])
    assert r["sesgo"] == pytest.approx(1.0)
    assert r["sd"] == pytest.approx(0.0, abs=1e-12)
    # 80 -> 88 sigue en B; los otros dos son A en los dos casos.
    assert r["acierto_categoria"] == 1.0


def test_record_metrics_category_matrix():
    est = np.array([120.0, 3.0, 10.0])   # A, C, B
    real = np.array([120.0, 10.0, 3.0])  # A, B, C
    r = record_metrics(est, real, [8.0, 8.0, 8.0])
    mat = r["matriz_categorias"]
    assert list(mat.index) == ["A", "B", "C"] and list(mat.columns) == ["A", "B", "C"]
    assert mat.loc["A", "A"] == 1 and mat.loc["B", "C"] == 1 and mat.loc["C", "B"] == 1
    assert mat.to_numpy().sum() == 3
    assert r["acierto_categoria"] == pytest.approx(1 / 3)


def test_record_metrics_invalid():
    with pytest.raises(ValueError):
        record_metrics([1.0, 2.0], [1.0], [8.0, 8.0])
    with pytest.raises(ValueError):
        record_metrics([1.0], [1.0], [8.0])
    with pytest.raises(ValueError):
        record_metrics([1.0, -1.0], [1.0, 1.0], [8.0, 8.0])
    with pytest.raises(ValueError):
        record_metrics([1.0, 1.0], [1.0, 1.0], [8.0, 0.0])