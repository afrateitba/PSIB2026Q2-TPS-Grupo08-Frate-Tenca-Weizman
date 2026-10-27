import numpy as np
import pytest

from src.config import SEED
from src.qrs.pan_tompkins import detect_r_peaks, validate_against_reference

FS = 100.0


def _synthetic_ecg(dur=300.0, seed=SEED):
    """ECG sintético con R, S y T, deriva de línea de base y ruido; RR de 0,6 a 1,2 s."""
    rng = np.random.default_rng(seed)
    t_r = np.cumsum(rng.uniform(0.6, 1.2, size=int(dur / 0.6)))
    t_r = t_r[t_r < dur - 1]
    t = np.arange(0, dur, 1 / FS)
    x = np.zeros_like(t)
    for tr in t_r:
        x += np.exp(-0.5 * ((t - tr) / 0.012) ** 2)               # R
        x -= 0.2 * np.exp(-0.5 * ((t - tr - 0.03) / 0.010) ** 2)  # S
        x += 0.3 * np.exp(-0.5 * ((t - tr - 0.25) / 0.050) ** 2)  # T
    x += 0.3 * np.sin(2 * np.pi * 0.2 * t) + 0.03 * rng.standard_normal(len(t))
    return x, np.round(t_r * FS).astype(int)


def test_detects_synthetic_beats():
    x, true_r = _synthetic_ecg()
    m = validate_against_reference(detect_r_peaks(x, FS), true_r, FS, tol=0.02)
    assert m["Se"] >= 0.99 and m["VPP"] >= 0.99


def test_inverted_polarity_gives_same_peaks():
    x, _ = _synthetic_ecg()
    assert np.array_equal(detect_r_peaks(x, FS), detect_r_peaks(-x, FS))


def test_searchback_recovers_small_beat():
    x, true_r = _synthetic_ecg()
    k = true_r[150]                                # un latido chico a mitad de registro
    x[k - 5:k + 6] -= 0.6 * np.exp(-0.5 * ((np.arange(-5, 6)) / 1.2) ** 2)
    m = validate_against_reference(detect_r_peaks(x, FS), true_r, FS, tol=0.02)
    assert m["FN"] == 0


def test_validate_against_reference_counts():
    m = validate_against_reference(np.array([100, 200, 305, 500]),
                                   np.array([100, 205, 300, 400]), FS, tol=0.10)
    assert (m["TP"], m["FP"], m["FN"]) == (3, 1, 1)
    assert m["Se"] == pytest.approx(0.75) and m["VPP"] == pytest.approx(0.75)


def test_validate_empty():
    m = validate_against_reference(np.array([]), np.array([10, 20]), FS)
    assert m["TP"] == 0 and m["FN"] == 2 and np.isnan(m["VPP"])