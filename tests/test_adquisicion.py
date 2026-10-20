import numpy as np
import pandas as pd
import pytest

from src.config import RAW_DIR
from src.data import load_ecg, load_ecg_digital, load_header
from src.preprocessing.quality import extreme_fraction, flat_fraction, flat_mask, saturated_mask
from src.qrs.pan_tompkins import r_peaks_from_marks
from src.qrs.quantization import two_phase_peaks
from src.stats.compare import agreement_compare

FS = 100.0


def _beats(n=300, rr=0.8, width=1.5, seed=0):
    """ECG sintético: picos gaussianos en tiempos que no caen sobre la grilla."""
    rng = np.random.default_rng(seed)
    true = (np.arange(1, n + 1) * rr + rng.uniform(0, 0.01, n)) * FS   # en muestras
    k = np.arange(int(true[-1] + 2 * FS))
    x = np.zeros(len(k))
    for c in true:
        sel = slice(int(c) - 10, int(c) + 11)
        x[sel] += np.exp(-0.5 * ((k[sel] - c) / width) ** 2)
    return x, true / FS, np.rint(true).astype(int)


def test_r_peaks_without_refinement_stay_on_the_grid():
    x, true, marks = _beats()
    t_int, _ = r_peaks_from_marks(x, marks, FS, 0, 1, refine=False)
    t_ref, _ = r_peaks_from_marks(x, marks, FS, 0, 1)
    assert np.allclose(t_int * FS, np.rint(t_int * FS))
    assert np.abs(t_ref - true).max() < np.abs(t_int - true).max()
    assert np.sqrt(np.mean((t_ref - true) ** 2)) < 0.001             # < 1 ms


def test_two_phase_refinement_shrinks_disagreement():
    x, true, marks = _beats()
    d = two_phase_peaks(x, marks, FS, 0, 1)
    raw = 1000 * (d.par - d.impar)
    ref = 1000 * (d.par_ref - d.impar_ref)
    assert np.sqrt(np.mean(raw ** 2)) == pytest.approx(10, abs=1.5)   # una muestra a 100 Hz
    assert np.sqrt(np.mean(ref ** 2)) < 3
    assert np.abs(d.par_ref - true[: len(d)]).max() < 0.005


def test_extreme_and_flat_fraction():
    t = np.arange(0, 60, 1 / FS)
    d = np.rint(400 * np.sin(2 * np.pi * 1.1 * t) + np.random.default_rng(1).normal(0, 5, len(t))).astype(int)
    assert extreme_fraction(d) < 0.001
    assert extreme_fraction(np.clip(d, -300, 300)) > 0.1             # recorte -> se acumula en el tope
    d[1000:1200] = 7                                                 # 2 s planos
    assert flat_fraction(d, FS) == pytest.approx(200 / len(d))
    assert flat_fraction(d, FS, min_s=3) == 0
    m = flat_mask(d, FS)
    assert m[1000:1200].all() and m.sum() == 200
    d[3000:3150] = 2047                                              # 1,5 s clavado en el tope
    assert saturated_mask(d, 12)[3000:3150].all() and saturated_mask(d, 12).sum() == 150
    assert flat_mask(d, FS)[3000:3150].all()


def test_agreement_with_external_reference():
    rng = np.random.default_rng(0)
    recs = np.repeat([f"r{i}" for i in range(12)], 50)
    frac = np.linspace(0, 0.9, 12)
    y = (rng.uniform(size=len(recs)) < np.repeat(frac, 50)).astype(int)
    score = pd.DataFrame({"f": y + rng.normal(0, 0.5, len(y))})
    subj = recs.copy()
    base = agreement_compare(score, y, recs, subj, n_boot=50)
    same = agreement_compare(score, y, recs, subj, n_boot=50,
                             reference=pd.Series(y, index=recs).groupby(level=0).mean())
    assert same.spearman.iloc[0] == pytest.approx(base.spearman.iloc[0])
    flip = agreement_compare(score, y, recs, subj, n_boot=50,
                             reference=-pd.Series(y, index=recs).groupby(level=0).mean())
    assert flip.spearman.iloc[0] == pytest.approx(-base.spearman.iloc[0])


@pytest.mark.skipif(not (RAW_DIR / "a01.hea").exists(), reason="faltan señales")
def test_header_and_digital_match_physical():
    h = load_header("a01")
    assert h["fs"] == 100 and h["ganancia"] == 200 and h["bits"] == 12
    d = load_ecg_digital("a01")
    ecg, _ = load_ecg("a01")
    assert len(d) == h["muestras"]
    assert np.allclose((d[:1000] - h["cero"]) / h["ganancia"], ecg[:1000])
