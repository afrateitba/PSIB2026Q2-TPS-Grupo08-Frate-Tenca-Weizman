import numpy as np

from src.estadistica import holm, p_bootstrap, tabla_holm


def test_p_bootstrap():
    assert p_bootstrap(np.r_[np.ones(990), -np.ones(10)]) == 0.02
    assert p_bootstrap(np.ones(100)) == 0.0
    assert np.isnan(p_bootstrap(np.zeros(50)))


def test_holm_ejemplo_de_libro():
    # p = 0,01; 0,02; 0,03 con m = 3 → 0,03; 0,04; 0,04 (el máximo acumulado mantiene el orden)
    ph = holm({"a": 0.01, "b": 0.02, "c": 0.03})
    assert np.allclose([ph["a"], ph["b"], ph["c"]], [0.03, 0.04, 0.04])


def test_holm_nunca_baja_un_p_y_satura_en_1():
    pv = {k: v for k, v in zip("abcd", (0.2, 0.5, 0.001, 0.9))}
    ph = holm(pv)
    assert all(ph[k] >= pv[k] for k in pv) and ph["d"] == 1.0


def test_tabla_holm():
    rng = np.random.default_rng(0)
    fam = {"grande": (1.0, rng.normal(1, 0.2, 2000)), "chica": (0.05, rng.normal(0.05, 0.03, 2000))}
    t = tabla_holm(fam)
    assert t.loc["grande", "resiste Holm"] == "sí" and t.loc["chica", "resiste Holm"] == "no"
