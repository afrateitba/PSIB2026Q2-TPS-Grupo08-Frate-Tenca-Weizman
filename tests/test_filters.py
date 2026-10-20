import numpy as np
import pytest

from src.config import ECG_FILTER
from src.preprocessing.filters import (beat_spectrum, cumulative_energy_freq, design_bandpass,
                                       frequency_response, mean_psd, meets_spec)

FS = 100.0


def test_frequency_response_shape_and_zero_phase_gain():
    sos = design_bandpass(FS, 0.5, 40, 2)
    r = frequency_response(sos, FS)
    k = np.argmin(np.abs(r["f"] - 10))
    assert abs(r["ganancia_db"][k]) < 0.1                    # 10 Hz pasa
    assert r["ganancia_db_ida_vuelta"][k] == pytest.approx(2 * r["ganancia_db"][k])
    k40 = np.argmin(np.abs(r["f"] - 40))
    assert r["ganancia_db"][k40] == pytest.approx(-3.01, abs=0.1)   # -3 dB en el corte
    assert r["ganancia_db"][-1] < -100                        # Nyquist (50 Hz) anulado


def test_meets_spec():
    sos = design_bandpass(FS, 0.5, 40, 2)
    assert meets_spec(sos, FS, (2, 30), {0.05: 20}, max_pass_db=1)
    assert not meets_spec(sos, FS, (0.5, 30), {0.05: 20}, max_pass_db=1)  # el corte pierde 6 dB
    assert not meets_spec(sos, FS, (2, 30), {0.3: 40}, max_pass_db=1)     # orden 2 no alcanza


def test_mean_psd_and_cumulative_energy():
    t = np.arange(0, 600, 1 / FS)
    x = np.sin(2 * np.pi * 5 * t) + 0.1 * np.sin(2 * np.pi * 20 * t)
    f, p = mean_psd([x, 3 * x], FS, nperseg=1024)
    assert f[np.argmax(p)] == pytest.approx(5, abs=0.2)
    assert np.trapezoid(p, f) == pytest.approx(1.0, rel=1e-6)
    assert 4 < cumulative_energy_freq(f, p, 0.5) < 6
    assert cumulative_energy_freq(f, p, 0.999) > 19


def test_beat_spectrum_of_narrow_vs_wide_beat():
    k = np.arange(10_000)
    peaks = np.arange(1, 120) * 80
    narrow = np.zeros(len(k)); wide = np.zeros(len(k))
    for c in peaks:
        narrow[c - 10:c + 11] += np.exp(-0.5 * (np.arange(-10, 11) / 1.0) ** 2)
        wide[c - 10:c + 11] += np.exp(-0.5 * (np.arange(-10, 11) / 4.0) ** 2)
    fn, pn = beat_spectrum(narrow, peaks, FS)
    fw, pw = beat_spectrum(wide, peaks, FS)
    assert cumulative_energy_freq(fn, pn, 0.99) > cumulative_energy_freq(fw, pw, 0.99)


def test_config_filter_is_valid():
    low, high, order = ECG_FILTER
    assert 0 < low < high < FS / 2 and order >= 1
