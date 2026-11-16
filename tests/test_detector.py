import numpy as np
import pandas as pd
import pytest

from src.config import RAW_DIR
from src.features.detector import (add_night_terms, c_score, confidence, fit_c, minute_table,
                                   youden_threshold)


def _tabla():
    rng = np.random.default_rng(0)
    filas = []
    for rec, nivel_edr in (("r1", -3.0), ("r2", -2.0)):
        for m in range(200):
            lab = int(m >= 100)
            filas.append({"record": rec, "minute": m, "label": lab, "q": 0.0,
                          "P_RR": -1.5 + 0.8 * lab + 0.1 * rng.standard_normal(),
                          "P_EDR": nivel_edr + 0.1 * rng.standard_normal(), "mov": 1.0 + rng.random()})
    return add_night_terms(pd.DataFrame(filas))


def test_c_dentro_de_la_noche_ordena_como_el_rr():
    t = _tabla()
    c = c_score(t, fit_c(t, 1.0))
    for _, gr in t.assign(c=c).groupby("record"):
        assert np.corrcoef(gr.c, gr.P_RR)[0, 1] > 0.999       # el término de la EDR es constante en la noche


def test_c_corre_la_noche_segun_la_edr():
    t = _tabla()
    c = t.assign(c=c_score(t, fit_c(t, 1.0)))
    assert c[c.record == "r2"].c.median() > c[c.record == "r1"].c.median()


def test_youden_separa_clases_disjuntas():
    x = np.r_[np.zeros(50), np.ones(50)]
    y = np.r_[np.zeros(50, int), np.ones(50, int)]
    u = youden_threshold(x, y)
    assert 0 < u < 1


def test_confianza():
    c = confidence(pd.Series([-1.0, 0.1, 2.0]), (0.0, 0.5))
    assert list(c) == ["alta", "media", "baja"]


@pytest.mark.skipif(not (RAW_DIR / "a03.dat").exists(), reason="faltan los datos")
def test_minute_table_a03():
    t = minute_table("a03")
    assert {"P_RR", "P_EDR", "F", "RR_dev", "EDR_noche", "mov_rel"} <= set(t.columns)
    assert t.EDR_noche.nunique() == 1 and abs(t.RR_dev.median()) < 1e-9
