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



def test_recovers_after_amplitude_drop():
    """Si el ECG baja de amplitud a mitad de la noche (como en a03), el detector no queda ciego."""
    x, true_r = _synthetic_ecg(dur=1200.0)
    a = int(300 * FS)
    x[a:] *= 0.15
    m = validate_against_reference(detect_r_peaks(x, FS), true_r, FS, tol=0.02)
    assert m["Se"] >= 0.98 and m["VPP"] >= 0.98


def test_recovers_after_artifact_burst():
    """Después de varios minutos de artefacto fuerte, vuelve a detectar los latidos."""
    import time
    x, true_r = _synthetic_ecg(dur=1200.0)
    rng = np.random.default_rng(SEED)
    a, b = int(200 * FS), int(400 * FS)
    x[a:b] += 4.0 * rng.standard_normal(b - a)
    t0 = time.time()
    det = detect_r_peaks(x, FS)
    assert time.time() - t0 < 5
    after = true_r[true_r > b + int(10 * FS)]
    m = validate_against_reference(det[det > b + int(10 * FS)], after, FS, tol=0.02)
    assert m["Se"] >= 0.98 and m["VPP"] >= 0.98


def _x17_like(dur=600.0, seed=SEED, early=None):
    """ECG como x17: QRS negativo y angosto, onda T positiva, alta y empinada a ~0,35 s; RR ~1,2 s."""
    rng = np.random.default_rng(seed)
    t_r = np.cumsum(rng.uniform(1.1, 1.3, size=int(dur / 1.1)))
    t_r = t_r[t_r < dur - 2]
    if early is not None:                                  # latido prematuro a 0,45 RR
        t_r = np.sort(np.append(t_r, t_r[early] + 0.45 * 1.2))
    t = np.arange(0, dur, 1 / FS)
    x = np.zeros_like(t)
    for tr in t_r:
        x -= 0.35 * np.exp(-0.5 * ((t - tr) / 0.010) ** 2)                 # QRS negativo
        tt = t - tr - 0.33
        x += 0.30 * np.exp(-0.5 * (tt / np.where(tt < 0, 0.045, 0.022)) ** 2)  # T asimétrica, bajada empinada
    x += 0.005 * rng.standard_normal(len(t))
    return x, np.round(t_r * FS).astype(int)


@pytest.mark.xfail(strict=True, reason="Limitación conocida: una onda T empinada (como en x17) tiene "
                   "más de la mitad de la pendiente del QRS y la regla clásica no la descarta.")
def test_tall_t_wave_not_counted():
    """Con ondas T altas y empinadas (como x17), no debería contar la T como otro latido."""
    x, true_r = _x17_like()
    m = validate_against_reference(detect_r_peaks(x, FS), true_r, FS, tol=0.03)
    assert m["Se"] >= 0.99 and m["VPP"] >= 0.99


def test_premature_beat_still_detected():
    """Un latido prematuro (a 0,45 RR) tiene pendiente de QRS: no se descarta como onda T."""
    x, true_r = _x17_like(early=200)
    det = detect_r_peaks(x, FS)
    k = true_r[np.argmin(np.abs(np.diff(true_r)))+1]       # el latido prematuro
    assert np.min(np.abs(det - k)) <= 3