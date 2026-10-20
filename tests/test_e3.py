import numpy as np
import pandas as pd
import pytest
from scipy.stats import mannwhitneyu

from src.config import RAW_DIR
from src.features.build import record_hrv_table, record_minute_table, record_series
from src.features.coupling import coherence_bands, coherence_multitaper
from src.features.hrv_time import hrv_time_features
from src.features.lomb import band_powers, lomb_psd
from src.features.postprocess import normalize, smooth
from src.preprocessing.filters import apply_zero_phase, design_bandpass
from src.stats.compare import compare_variants, pair_counts, pooled_auc
from src.stats.thresholds import record_agreement, roc_youden


def _slow_common(n=1024, seed=0):
    rng = np.random.default_rng(seed)
    slow = apply_zero_phase(rng.standard_normal(n), design_bandpass(2.0, 0.01, 0.05, 2))
    slow /= slow.std()
    hf = lambda: apply_zero_phase(rng.standard_normal(n), design_bandpass(2.0, 0.15, 0.4, 2))
    return slow + hf() + 0.1 * rng.standard_normal(n), slow + hf() + 0.1 * rng.standard_normal(n)


def test_multitaper_coherence_separates_bands():
    x, y = _slow_common()
    f, c, p = coherence_multitaper(x, y, 2.0)
    assert c[(f >= 0.01) & (f < 0.05)].mean() > 0.7
    assert c[(f >= 0.15) & (f < 0.4)].mean() < 0.5
    out = coherence_bands(x, y, 2.0, 512, {"lenta": (0.01, 0.05)}, estimator="multitaper")
    assert set(out) == {"coh_lenta", "xp_lenta", "cw_lenta", "px_lenta", "py_lenta"}


@pytest.mark.parametrize("n, nperseg", [(1024, 512), (1024, 256), (360, 90), (600, 300)])
def test_welch_matches_scipy(n, nperseg):
    from scipy.signal import coherence, csd
    from src.features.coupling import coherence_spectrum
    x, y = _slow_common(n)
    kw = dict(fs=2.0, nperseg=nperseg, noverlap=nperseg // 2, detrend="linear")
    f, c, p = coherence_spectrum(x, y, 2.0, nperseg)
    f2, c2 = coherence(x, y, **kw)
    _, p2 = csd(x, y, **kw)
    assert np.allclose(f, f2) and np.allclose(c, c2) and np.allclose(p, np.abs(p2))
    from scipy.signal import welch
    from src.features.coupling import welch_spectra
    _, sxx, syy, _ = welch_spectra(x, y, 2.0, nperseg)
    kw.pop("detrend"); kw["detrend"] = "linear"
    assert np.allclose(sxx, welch(x, **kw)[1]) and np.allclose(syy, welch(y, **kw)[1])


def test_cross_power_decomposition():
    # |Sxy| = sqrt(coherencia) * sqrt(Sxx * Syy), frecuencia por frecuencia
    from src.features.coupling import welch_spectra
    x, y = _slow_common()
    _, sxx, syy, sxy = welch_spectra(x, y, 2.0, 512)
    coh = np.abs(sxy) ** 2 / (sxx * syy)
    assert np.allclose(np.abs(sxy), np.sqrt(coh) * np.sqrt(sxx * syy))
    out = coherence_bands(x, y, 2.0, 512, {"b": (0.01, 0.05)})
    assert {"px_b", "py_b"} <= set(out) and out["px_b"] > 0 and out["py_b"] > 0


def test_weighted_coherence_resists_dilution():
    # Acoplamiento en una sola frecuencia: el promedio se diluye, el ponderado no.
    rng = np.random.default_rng(1)
    t = np.arange(4096) / 2.0
    s = 3 * np.sin(2 * np.pi * 0.03 * t)
    x, y = s + rng.standard_normal(len(t)), s + rng.standard_normal(len(t))
    out = coherence_bands(x, y, 2.0, 1024, {"b": (0.01, 0.05)})
    assert out["cw_b"] > out["coh_b"] + 0.2


def test_lomb_recovers_power_of_sine_with_irregular_sampling():
    rng = np.random.default_rng(2)
    t = np.cumsum(rng.uniform(0.7, 1.1, 400))                # latidos irregulares
    rr = 0.9 + 0.05 * np.sin(2 * np.pi * 0.25 * t)
    f = np.arange(0.005, 0.5, 0.001)
    p = lomb_psd(t, rr, f)
    assert abs(f[np.argmax(p)] - 0.25) < 0.005
    bp = band_powers(f, p)
    assert bp["hf"] == pytest.approx(0.05 ** 2 / 2, rel=0.25)  # varianza de la senoidal
    assert bp["lf_hf"] < 0.1


def test_hrv_time_features():
    rr = np.array([0.8, 0.9, 0.8, 0.9, 0.8])
    h = hrv_time_features(rr)
    assert h["mean_rr"] == pytest.approx(0.84) and h["rmssd"] == pytest.approx(0.1)
    assert h["pnn50"] == 1.0


def test_normalize():
    v = pd.Series([1.0, 2, 3, 10, 20, 30])
    r = pd.Series(["a", "a", "a", "b", "b", "b"])
    assert normalize(v, r, "none").equals(v)
    z = normalize(v, r, "zscore")
    assert np.allclose(z.groupby(r).mean(), 0) and np.allclose(z.groupby(r).std(), 1)
    b = normalize(v, r, "baseline", q=0)
    assert b.tolist() == [0, 1, 2, 0, 10, 20]


def test_smooth_respects_records_and_gaps():
    v = pd.Series([0, 9, 0, 0, 5, 5, 5.0])
    r = pd.Series(["a"] * 4 + ["b"] * 3)
    m = pd.Series([0, 1, 2, 3, 0, 1, 5])                    # en b falta un tramo
    s = smooth(v, r, m, 3)
    assert s.iloc[1] == 0                                    # el pico aislado desaparece
    assert s.iloc[6] == 5                                    # el minuto 5 no se mezcla con el 1
    assert smooth(v, r, m, 1).equals(v)


def test_pair_counts_match_direct_auc():
    rng = np.random.default_rng(3)
    y = rng.integers(0, 2, 600)
    s = rng.standard_normal(600) + 0.8 * y
    s[:20] = np.round(s[:20])                               # algunos empates
    g = rng.integers(0, 5, 600)
    U, A, N = pair_counts(s, y, g, list(range(5)))
    direct = mannwhitneyu(s[y == 1], s[y == 0]).statistic / ((y == 1).sum() * (y == 0).sum())
    assert U.sum() / (A.sum() * N.sum()) == pytest.approx(direct)
    assert pooled_auc(s, y) == pytest.approx(direct)


def test_compare_variants():
    rng = np.random.default_rng(4)
    y = rng.integers(0, 2, 2000)
    g = np.repeat(np.arange(20), 100)
    tab = pd.DataFrame({"buena": rng.standard_normal(2000) + 1.5 * y,
                        "casi": rng.standard_normal(2000) + 1.45 * y,
                        "azar": rng.standard_normal(2000)})
    r = compare_variants(tab, y, g, n_boot=500)
    assert r.auc.idxmax() == "buena" and r.loc["buena", "empata"]
    assert not r.loc["azar", "empata"] and r.loc["azar", "auc"] == pytest.approx(0.5, abs=0.05)
    assert r.p_mejor.sum() == pytest.approx(1.0)


def test_roc_youden_and_record_agreement():
    y = np.array([0] * 50 + [1] * 50)
    s = np.r_[np.linspace(0, 1, 50), np.linspace(2, 3, 50)]
    r = roc_youden(s, y)
    assert r["se"] == 1 and r["esp"] == 1 and r["auc"] == 1 and 1 < r["umbral"] <= 2
    recs = np.repeat(["a", "b", "c", "d"], 25)
    a = record_agreement(s, y, recs, r["umbral"])
    assert a["spearman"] == pytest.approx(1.0)


def test_variants_build_all_combinations():
    from src.features.variants import BAND_CONFIGS, BANDS, FORMS, coupling_variants, hrv_variants
    rng = np.random.default_rng(5)
    rows = []
    for edr in ("area", "baseline"):
        for w in (180, 300):
            for m in range(10):
                r = {"record": "a01", "minute": m, "edr": edr, "window": w, "estimator": "welch3"}
                for b in BANDS:
                    r.update({f"coh_{b}": rng.uniform(0.1, 0.9), f"xp_{b}": rng.uniform(0.1, 2),
                              f"cw_{b}": rng.uniform(0.1, 0.9)})
                rows.append(r)
    wide, meta = coupling_variants(pd.DataFrame(rows))
    assert wide.shape == (10, 2 * 2 * len(BAND_CONFIGS) * len(FORMS)) and len(FORMS) == 7
    assert "area|180s|welch3|CPC|potencia sola" in wide.columns
    assert np.isfinite(wide.to_numpy()).all()
    assert meta.loc["area|180s|welch3|CPC|solo lenta", "complejidad"] < meta.loc["area|300s|welch3|CPC|solo lenta", "complejidad"]
    hrv = pd.DataFrame({"record": "a01", "minute": range(10), "window": 300,
                        **{f: rng.uniform(size=10) for f in ("mean_rr", "sdnn", "rmssd", "pnn50", "apnea",
                                                             "vlf", "lf", "hf", "total", "lf_hf")}})
    hw, hm = hrv_variants(hrv)
    assert hw.shape == (10, 10) and "hrv|300s|lf_hf" in hm.index


def test_postprocess_variants():
    from src.features.variants import postprocess_variants
    idx = pd.MultiIndex.from_product([["a", "b"], range(6)], names=["record", "minute"])
    wide = pd.DataFrame({"f": [0, 9, 0, 0, 0, 0, 10, 10, 30, 10, 10, 10.0]}, index=idx)
    meta = pd.DataFrame({"complejidad": [(3,)]}, index=["f"])
    pw, pm = postprocess_variants(wide, meta)
    assert pw.shape == (12, 9) and pm.loc["f|none|k1", "complejidad"] == (0, 1, 3)
    assert pw["f|none|k1"].equals(wide["f"])
    assert pw.loc[("a", 1), "f|none|k3"] == 0                     # el pico aislado se suaviza
    assert pw["f|baseline|k1"].groupby(level=0).min().tolist() == [0, 0]
    assert min(pm.complejidad) == (0, 1, 3) and max(pm.complejidad) == (2, 5, 3)


def _toy_selection_data(seed=6, n_subj=12, per=150):
    rng = np.random.default_rng(seed)
    g = np.repeat(np.arange(n_subj), per)
    recs = np.array([f"r{s}" for s in g])
    y = (rng.uniform(size=len(g)) < np.repeat(rng.uniform(0.1, 0.6, n_subj), per)).astype(int)
    tab = pd.DataFrame({"compleja": rng.standard_normal(len(g)) + 1.2 * y,
                        "simple": rng.standard_normal(len(g)) + 1.2 * y,
                        "invertida": -(rng.standard_normal(len(g)) + 0.3 * y),
                        "azar": rng.standard_normal(len(g))})
    comp = pd.Series({"compleja": (2,), "simple": (0,), "invertida": (1,), "azar": (3,)})
    return tab, y, g, recs, comp


def test_select_variant_orients_and_prefers_simple():
    from src.stats.compare import select_variant
    tab, y, g, recs, comp = _toy_selection_data()
    for rule in ("original", "noninferior"):
        sel = select_variant(tab, y, g, recs, comp, n_boot=300, n_boot_rec=200, rule=rule, delta=0.05)
        assert sel["signos"]["invertida"] == -1.0            # se dio vuelta
        assert {"compleja", "simple"} <= set(sel["grupo"]) and "azar" not in sel["grupo"]
        assert sel["ganadora"] == "simple"                   # empate -> la más simple
    sel = select_variant(tab, y, g, recs, comp, n_boot=300, n_boot_rec=200, rule="max")
    assert sel["grupo"] == [sel["auc"].auc.idxmax()] and sel["ganadora"] == sel["grupo"][0]


def test_noninferior_excludes_noisy_and_keeps_close():
    # La falla de la regla original: una candidata ruidosa "empata" y una parecida no.
    from src.stats.compare import select_variant
    rng = np.random.default_rng(10)
    n_subj, per = 16, 200
    g = np.repeat(np.arange(n_subj), per)
    recs = np.array([f"r{s}" for s in g])
    y = (rng.uniform(size=len(g)) < 0.4).astype(int)
    base = rng.standard_normal(len(g)) + 1.4 * y
    efecto = np.repeat(rng.uniform(0.0, 2.8, n_subj), per)   # funciona muy distinto según el sujeto
    tab = pd.DataFrame({"mejor": base,
                        "parecida": base + 0.25 * rng.standard_normal(len(g)),
                        "ruidosa": rng.standard_normal(len(g)) + efecto * y})
    comp = pd.Series({"mejor": (2,), "parecida": (1,), "ruidosa": (0,)})
    kw = dict(n_boot=500, n_boot_rec=200)
    orig = select_variant(tab, y, g, recs, comp, rule="original", **kw)
    nonin = select_variant(tab, y, g, recs, comp, rule="noninferior", delta=0.02, **kw)
    assert "ruidosa" in orig["grupo"] and "ruidosa" not in nonin["grupo"]
    assert "parecida" in nonin["grupo"]


def test_folds_and_cross_validation():
    from src.stats.compare import cross_validate_selection, subject_folds
    tab, y, g, recs, comp = _toy_selection_data()
    has = pd.Series({s: s % 3 != 0 for s in range(12)})
    folds = subject_folds(has, k=4)
    assert sorted(sum(folds, [])) == list(range(12))
    assert all(any(has[s] for s in f) and any(not has[s] for s in f) for f in folds)
    cv = cross_validate_selection(tab, y, g, recs, comp, folds, reference="compleja",
                                  n_boot=200, n_boot_rec=100)
    assert len(cv) == 4 and (cv["AUC afuera"] > 0.7).all()
    assert (cv["referencia afuera"] > 0.7).all()


@pytest.mark.skipif(not (RAW_DIR / "a03.dat").exists(), reason="faltan señales")
def test_record_feature_tables_real():
    from src.features.build import record_feature_tables
    from src.features.variants import BANDS
    coup, hrv = record_feature_tables("a03", (300,), ("welch3", "multitaper"), ("area", "combined"), BANDS)
    assert set(coup.edr) == {"area", "combined"} and set(coup.estimator) == {"welch3", "multitaper"}
    assert {"coh_ap_l", "xp_cpc_r", "cw_v2_l", "label", "corrected"} <= set(coup.columns)
    assert set(hrv.window) == {300}


@pytest.mark.skipif(not (RAW_DIR / "a03.dat").exists(), reason="faltan señales")
def test_real_record_tables():
    s = record_series("a03", edr_methods=("baseline", "combined"))
    assert set(s["edrs"]) == {"area", "baseline", "combined"}
    assert all(len(v) == len(s["t"]) for v in s["edrs"].values())
    bands = {"lenta": (0.01, 0.05), "resp": (0.15, 0.4)}
    for est in ("welch3", "welch7", "multitaper"):
        tab = record_minute_table("a03", 300, bands, series=s, edr_method="combined", estimator=est)
        assert len(tab) > 400 and tab[["coh_lenta", "cw_lenta"]].notna().all().all()
    hrv = record_hrv_table("a03", 300, series=s)
    assert {"apnea", "lf_hf", "sdnn", "rmssd", "label"} <= set(hrv.columns)
    assert hrv.apnea.notna().mean() > 0.95
