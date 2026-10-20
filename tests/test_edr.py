import numpy as np
import pytest

from src.features.coupling import downsample, resample_uniform, weighted_coherence
from src.features.edr import (beat_matrix, edr_amplitude, edr_area, edr_pca,
                              edr_peak_to_peak, edr_series, qrs_reference, validate_edr)
from src.preprocessing.filters import apply_zero_phase, design_bandpass
from src.qrs.pan_tompkins import refine_peaks_parabolic
from src.qrs.rr_clean import rr_in_range

FS = 100.0


def _synthetic_ecg(n_beats=400, rr=0.8, sign=1, offset=0, mod=0.2, seed=0):
    """ECG con un QRS gaussiano por latido, amplitud modulada a 0,25 Hz.

    Devuelve (ecg, marcas, centros, amplitudes). Las marcas están `offset`
    muestras antes del pico, como las de sqrs125.
    """
    rng = np.random.default_rng(seed)
    centers = (np.arange(1, n_beats + 1) * rr * FS).astype(int)
    amps = 1 + mod * np.sin(2 * np.pi * 0.25 * centers / FS)
    ecg = 0.01 * rng.standard_normal(centers[-1] + 200)
    k = np.arange(-6, 7)
    for c, a in zip(centers, amps):
        ecg[c + k] += sign * a * np.exp(-0.5 * (k / 1.5) ** 2)
    return ecg, centers - offset, centers, amps


def test_bandpass_keeps_inside_and_removes_outside():
    t = np.arange(0, 60, 1 / FS)
    sos = design_bandpass(FS, 0.5, 40, order=2)
    inside = apply_zero_phase(np.sin(2 * np.pi * 10 * t), sos)
    outside = apply_zero_phase(np.sin(2 * np.pi * 0.05 * t), sos)
    mid = slice(1000, -1000)
    assert np.std(inside[mid]) / np.std(np.sin(2 * np.pi * 10 * t)[mid]) > 0.95
    assert np.std(outside[mid]) < 0.05
    assert np.argmax(inside[2000:2010]) == np.argmax(np.sin(2 * np.pi * 10 * t)[2000:2010])  # fase cero


def test_parabolic_recovers_vertex():
    i = np.arange(10, dtype=float)
    up = 2 - (i - 3.3) ** 2
    t, a = refine_peaks_parabolic(up, np.array([3]))
    assert t[0] == pytest.approx(3.3) and a[0] == pytest.approx(2.0)
    t, a = refine_peaks_parabolic(-up, np.array([3]))        # mínimo
    assert t[0] == pytest.approx(3.3) and a[0] == pytest.approx(-2.0)
    t, a = refine_peaks_parabolic(up, np.array([0]))         # borde: sin corregir
    assert t[0] == 0 and a[0] == up[0]


@pytest.mark.parametrize("sign", [1, -1])
def test_qrs_reference_finds_offset_and_polarity(sign):
    ecg, marks, _, _ = _synthetic_ecg(sign=sign, offset=4)
    assert qrs_reference(ecg, marks, FS) == (4, sign)


@pytest.mark.parametrize("sign", [1, -1])
def test_edr_methods_recover_modulation(sign):
    ecg, _, centers, amps = _synthetic_ecg(sign=sign)
    beats, ok = beat_matrix(ecg, centers, FS, baseline=(-0.10, -0.07))
    assert ok.all()
    for v in (edr_amplitude(beats, sign), edr_peak_to_peak(beats),
              edr_area(beats, sign, FS), edr_pca(beats)):
        assert np.corrcoef(v, amps)[0, 1] > 0.98     # el área suma ruido de las 13 muestras


def test_beat_matrix_drops_beats_at_edges():
    ecg = np.zeros(1000)
    _, ok = beat_matrix(ecg, np.array([2, 500, 998]), FS)
    assert ok.tolist() == [False, True, False]


def test_rr_in_range_and_edr_series():
    t = np.array([0.0, 0.8, 1.6, 1.7, 2.5, 3.3, 6.0, 6.8])
    valid = rr_in_range(t)
    assert valid.tolist() == [False, True, False, False, True, False, False, False]
    tt, vv = edr_series(t, np.array([1, 2, np.nan, 4, 5, 6, 7, 8.0]), valid)
    assert tt.tolist() == [0.8, 2.5] and vv.tolist() == [2.0, 5.0]


def test_resample_uniform():
    t = np.sort(np.random.default_rng(0).uniform(0, 100, 150))
    for kind in ("cubic", "linear"):
        tu, xu = resample_uniform(t, 3 * t + 1, fs=2.0, kind=kind)
        assert tu[0] >= t[0] and tu[-1] <= t[-1] and np.allclose(np.diff(tu), 0.5)
        assert np.allclose(xu, 3 * tu + 1)


def test_downsample_keeps_slow_sine():
    t = np.arange(0, 120, 1 / FS)
    y = downsample(np.sin(2 * np.pi * 0.3 * t), FS, 2.0)
    tu = np.arange(len(y)) / 2.0
    mid = slice(10, -10)
    assert np.allclose(y[mid], np.sin(2 * np.pi * 0.3 * tu)[mid], atol=0.02)


def test_weighted_coherence():
    rng = np.random.default_rng(1)
    t = np.arange(0, 240, 0.5)
    resp = np.sin(2 * np.pi * 0.25 * t) + 0.1 * rng.standard_normal(len(t))
    same = resp + 0.1 * rng.standard_normal(len(t))
    other = rng.standard_normal(len(t))
    assert weighted_coherence(same, resp, 2.0, 64) > 0.9
    assert weighted_coherence(other, resp, 2.0, 64) < 0.4
    w = validate_edr(np.concatenate([same, same]), np.concatenate([resp, resp]), 2.0)
    assert len(w) == 4 and (w > 0.9).all()          # 480 s a 2 Hz en ventanas de 120 s
    con_nan = np.concatenate([resp, resp])
    con_nan[300] = np.nan                           # cae en la segunda ventana
    w = validate_edr(np.concatenate([same, same]), con_nan, 2.0)
    assert np.isnan(w[1]) and np.isfinite(w[[0, 2, 3]]).all()
