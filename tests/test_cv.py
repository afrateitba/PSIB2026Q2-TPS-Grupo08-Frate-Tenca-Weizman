import numpy as np
import pandas as pd

from src.evaluation.cv import auc, cv_c, exactitud, grupos_personas, sorteos_personas


def _tabla(n_personas=10, n_min=60, seed=0):
    rng = np.random.default_rng(seed)
    filas = []
    for i in range(n_personas):
        y = rng.integers(0, 2, n_min)
        nivel = rng.normal()
        filas.append(pd.DataFrame({"subject": f"S{i:02d}", "record": f"r{i:02d}", "minute": np.arange(n_min),
                                   "label": y, "q": 0.0, "P_RR": y + rng.normal(0, 0.5, n_min),
                                   "EDR_noche": nivel + y.mean(), "mov_rel": rng.normal(0, 1, n_min)}))
    return pd.concat(filas, ignore_index=True)


def test_auc_extremos():
    assert auc([1, 2, 3, 4], [0, 0, 1, 1]) == 1.0
    assert auc([4, 3, 2, 1], [0, 0, 1, 1]) == 0.0
    assert np.isnan(auc([1, 2], [1, 1]))


def test_grupos_son_una_particion_de_las_personas():
    g = grupos_personas([f"S{i}" for i in range(19)] * 3)
    todas = np.concatenate(g)
    assert len(g) == 5 and len(todas) == 19 and len(set(todas)) == 19


def test_cv_c_no_ve_a_la_persona_que_clasifica():
    r = cv_c(_tabla())
    assert r.groupby("subject").grupo.nunique().max() == 1
    assert set(r.pred.unique()) <= {0, 1} and r.confianza.isin(["alta", "media", "baja"]).all()
    assert (r.pred == r.label).mean() > 0.7


def test_exactitud_bootstrap_pareada():
    ok = pd.Series([1, 1, 0, 1]); s = pd.Series(["a", "a", "b", "b"])
    assert exactitud(ok, s) == 0.75
    so = [np.array(["a", "a"]), np.array(["b", "b"])]
    assert list(exactitud(ok, s, so)) == [1.0, 0.5]
    assert len(sorteos_personas(["a", "b", "c"], n=7)) == 7
