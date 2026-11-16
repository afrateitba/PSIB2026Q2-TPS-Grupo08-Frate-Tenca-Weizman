import numpy as np
import pandas as pd
import pytest

from src.config import RAW_DIR
from src.features.detector import WINDOW_S
from src.viz.visor_data import (analizar_noche, ecg_minuto, registros_visibles, resumen_noche,
                                ventana_minuto)


def test_el_visor_no_muestra_test_por_defecto():
    assert set(registros_visibles()["set"]) == {"dev"}
    assert "test" in set(registros_visibles(incluir_test=True)["set"])


def test_resumen_noche():
    tab = pd.DataFrame({"label": [1, 1, 0, 0, -1], "decision": [1, 0, 0, 1, 1],
                        "evaluado": [True, True, True, True, False],
                        "confianza": ["alta", "alta", "media", "baja", "alta"]})
    r = resumen_noche(tab)
    assert r["evaluados"] == 4 and r["sensibilidad"] == 0.5 and r["especificidad"] == 0.5
    assert r["apnea_real"] == 50 and r["exactitud"] == 0.5
    assert r["confianza"] == {"alta": 0.5, "media": 0.25, "baja": 0.25}


def test_resumen_sin_apnea_no_inventa_sensibilidad():
    tab = pd.DataFrame({"label": [0, 0], "decision": [0, 1], "evaluado": [True, True], "confianza": ["alta"] * 2})
    assert np.isnan(resumen_noche(tab)["sensibilidad"])


@pytest.mark.skipif(not (RAW_DIR / "a03.dat").exists(), reason="faltan los datos")
def test_analizar_noche_a03():
    an = analizar_noche("a03")
    tab, p = an["tabla"], an["params"]
    assert np.allclose(tab.C, tab.termino_rr + tab.termino_edr)
    assert ((tab.C > p["umbral"]).astype(int) == tab.decision).all()
    assert tab.termino_edr.nunique() == 1                   # constante en la noche
    m = int(tab.minute.iloc[len(tab) // 2])
    v = ventana_minuto(an, m)
    assert len(v["rr"]) == WINDOW_S * 2
    assert np.isclose(v["P_RR"], v["fila"].P_RR) and np.isclose(v["P_EDR"], v["fila"].P_EDR)
    e = ecg_minuto(an, m)
    assert len(e["crudo"]) == 60 * an["fs"] and 40 < len(e["t_r"]) < 120
