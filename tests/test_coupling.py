import numpy as np
import pytest

from src.config import RAW_DIR
from src.features.build import minute_coupling, record_minute_table
from src.features.coupling import coherence_bands
from src.features.edr import compute_edr
from src.features.windows import centered_windows
from src.preprocessing.filters import apply_zero_phase, design_bandpass
from src.qrs.pan_tompkins import r_peaks_from_marks
from src.qrs.rr_clean import clean_rr, minute_quality
from src.stats.tests import holm, paired_subject_test

FS = 100.0


@pytest.mark.parametrize("sign", [1, -1])
def test_r_peaks_from_marks_subsample(sign):
    centers = np.arange(1, 50) * 80 + 0.3                  # picos entre muestras
    k = np.arange(4100)
    ecg = sign * np.exp(-0.5 * ((k[:, None] - centers) / 1.5) ** 2).sum(axis=1)
    marks = np.rint(centers).astype(int) - 4                # sqrs125 marca antes del pico
    t, amp = r_peaks_from_marks(ecg, marks, FS, offset=4, sign=sign)
    assert np.allclose(t * FS, centers, atol=0.05)
    assert np.allclose(amp, 1.0, atol=0.03)


def test_clean_rr_fixes_ectopic_and_out_of_range():
    rr = np.full(40, 0.8)
    rr[10], rr[11] = 0.5, 1.1                               # ectópico: corto + compensatorio
    rr[25] = 2.5                                            # imposible
    t_r = np.concatenate([[0.0], np.cumsum(rr)])
    t, rr_c, corrected = clean_rr(t_r)
    assert set(np.flatnonzero(corrected)) == {10, 11, 25}
    assert np.allclose(rr_c, 0.8, atol=0.05)
    q = minute_quality(t, corrected, 1)
    assert q[0] == pytest.approx(3 / np.sum(t < 60))


def test_centered_windows():
    m, t0 = centered_windows(10, 300, 0, 600)
    assert m.tolist() == [2, 3, 4, 5, 6, 7]
    assert t0[0] == 0 and t0[-1] + 300 == 600


def test_coherence_bands_separates_bands():
    rng = np.random.default_rng(0)
    n = 4096                                                # 34 min a 2 Hz
    # Componente lenta común de banda ancha (0,01-0,05 Hz), como el ciclo de apnea
    slow = apply_zero_phase(rng.standard_normal(n), design_bandpass(2.0, 0.01, 0.05, 2))
    slow /= slow.std()
    hf = lambda: apply_zero_phase(rng.standard_normal(n), design_bandpass(2.0, 0.15, 0.4, 2))
    x = slow + hf() + 0.1 * rng.standard_normal(n)          # HF propia de cada señal
    y = slow + hf() + 0.1 * rng.standard_normal(n)
    c = coherence_bands(x, y, 2.0, 1024, {"low": (0.01, 0.05), "high": (0.15, 0.4)})
    assert c["coh_low"] > 0.8 and c["coh_high"] < 0.5
    assert c["xp_low"] > 0


def test_minute_coupling_marks_invalid_windows():
    rng = np.random.default_rng(3)
    t = np.arange(0, 1200, 0.5)                             # 20 min a 2 Hz
    x, y = rng.standard_normal(len(t)), rng.standard_normal(len(t))
    y[1000] = np.nan                                        # cae en las ventanas cercanas al minuto 8
    tab = minute_coupling(t, x, y, 2.0, 20, 300, {"b": (0.1, 0.4)})
    bad = tab.loc[tab.coh_b.isna(), "minute"]
    assert len(bad) > 0 and bad.between(5, 11).all() and tab.coh_b.notna().any()


def test_compute_edr_follows_modulation():
    k = np.arange(40_000)
    centers = np.arange(1, 480) * 80
    amps = 1 + 0.2 * np.sin(2 * np.pi * 0.25 * centers / FS)
    ecg = np.zeros(len(k))
    for c, a in zip(centers, amps):
        ecg[c - 6:c + 7] += a * np.exp(-0.5 * (np.arange(-6, 7) / 1.5) ** 2)
    t, v = compute_edr(ecg, centers - 3, FS)
    assert np.all(np.diff(t) > 0)
    assert np.corrcoef(v, amps[np.isin(centers, np.rint(t * FS).astype(int))])[0, 1] > 0.98
    drift = 0.3 * np.sin(2 * np.pi * 0.25 * k / FS)          # deriva respiratoria
    t, v = compute_edr(ecg + drift, centers - 3, FS, method="baseline")
    assert np.corrcoef(v, drift[np.rint(t * FS).astype(int) - 7])[0, 1] > 0.98
    with pytest.raises(ValueError):
        compute_edr(ecg, centers, FS, method="otro")


def test_paired_subject_test():
    r = paired_subject_test(np.arange(1, 15) / 10)          # 14 diferencias positivas
    assert r["positivos"] == 14 and r["r_rb"] == pytest.approx(1.0) and r["p"] < 0.001
    r = paired_subject_test(np.array([-3, -2, -1, 1, 2, 3.0]))
    assert r["r_rb"] == pytest.approx(0.0) and r["p"] > 0.5


def test_holm():
    assert np.allclose(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
    assert np.allclose(holm([0.5, 0.9]), [1.0, 1.0])       # 0,5 x 2 = 1; el siguiente no puede ser menor


@pytest.mark.skipif(not (RAW_DIR / "a03.dat").exists(), reason="faltan señales")
def test_record_minute_table_real():
    tab = record_minute_table("a03", 512, {"low": (0.01, 0.1), "high": (0.1, 0.4)})
    assert {"record", "minute", "coh_low", "coh_high", "label", "corrected"} <= set(tab.columns)
    assert tab.minute.is_monotonic_increasing and len(tab) > 400
    assert tab[["coh_low", "coh_high"]].notna().all().all()
