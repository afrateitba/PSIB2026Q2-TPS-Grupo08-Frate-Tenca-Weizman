import numpy as np
import pytest

from src.config import RAW_DIR, SAME_RECORDING
from src.data import load_ecg, load_qrs
from src.duplicates import beat_template, signal_match, template_similarity


def test_signal_match_finds_shift():
    rng = np.random.default_rng(0)
    y = rng.standard_normal(100 * 60 * 80)            # 80 min a 100 Hz
    x = y[4000:]                                      # x empieza 40 s después
    lag, r = signal_match(x, y, fs=100)
    assert lag == 4000 and r == pytest.approx(1.0)
    _, r_other = signal_match(rng.standard_normal(len(x)), y, fs=100)
    assert r_other < 0.1


def test_template_similarity():
    t = np.sin(np.linspace(0, 3 * np.pi, 65))
    assert template_similarity(t, t) == pytest.approx(1.0)
    assert template_similarity(t, np.roll(t, 2)) > 0.99     # desfase dentro de ±3
    assert template_similarity(t, -t) < 0


_DUPS = [rec for pair in SAME_RECORDING for rec in pair]


@pytest.mark.skipif(not all((RAW_DIR / f"{r}.dat").exists() for r in _DUPS),
                    reason="faltan señales (scripts/download_data.py)")
@pytest.mark.parametrize("a, b, lag_s", [("c05", "c06", 80), ("x22", "x35", 40), ("x33", "x34", 70)])
def test_same_recording_pairs(a, b, lag_s):
    assert (a, b) in SAME_RECORDING
    xa, fs = load_ecg(a)
    xb, _ = load_ecg(b)
    lag, r = signal_match(xa, xb, fs)
    assert lag == lag_s * fs and r > 0.999
    ta = beat_template(xa, load_qrs(a), fs)
    tb = beat_template(xb, load_qrs(b), fs)
    assert template_similarity(ta, tb) > 0.99
