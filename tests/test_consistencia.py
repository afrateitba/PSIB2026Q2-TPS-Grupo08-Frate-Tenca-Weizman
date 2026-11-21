"""Consistencia del proyecto: cada número del pipeline está definido en un solo lugar.

La devolución marcó decisiones inconsistentes (por ejemplo, ventanas que cambiaban
de una sección a otra). Estos tests fallan si un notebook o un módulo vuelve a
escribir a mano una ventana, una banda o un umbral que ya está fijado en
src/config.py o en src/features/detector.py.
"""
import inspect
import json
import re
from pathlib import Path

import numpy as np
import pytest

from src import config as cfg
from src import duplicates
from src.features import detector, edr
from src.preprocessing import filters, wiener
from src.qrs import rr_clean

ROOT = Path(__file__).resolve().parents[1]
# 05 y 11 quedan afuera: se registraron sin ejecutar antes de abrir test y no se modifican.
NOTEBOOKS = [p for p in sorted((ROOT / "notebooks").glob("[01][0-9]_*.ipynb")) if not p.name.startswith(("05", "11"))]


def _defaults(f):
    return {k: v.default for k, v in inspect.signature(f).parameters.items() if v.default is not inspect.Parameter.empty}


def test_ventana_banda_y_grilla():
    assert detector.WINDOW_S == 240 and detector.FS_U == 2.0 and detector.BAND == (0.01, 0.05)
    n = int(detector.WINDOW_S * detector.FS_U) // 2                     # segmento de Welch: 120 s
    f = np.fft.rfftfreq(n, 1 / detector.FS_U)
    k = np.flatnonzero((f >= detector.BAND[0] - 1e-9) & (f <= detector.BAND[1] + 1e-9))
    assert np.isclose(f[k].min(), detector.BANDA_EFECTIVA[0]) and np.isclose(f[k].max(), detector.BANDA_EFECTIVA[1])
    assert list(k) == [2, 3, 4, 5, 6]                                   # 1/60, 1/40, 1/30, 1/24 y 1/20 Hz


def test_limpieza_del_rr_usa_config():
    d = _defaults(rr_clean.clean_rr)
    assert (d["lo"], d["hi"]) == cfg.RR_RANGE_S
    assert d["ectopic"] == cfg.RR_ECTOPIC_FRAC and d["k"] == cfg.RR_NEIGHBORS


def test_minutos_evaluados_usan_config():
    import pandas as pd
    t = pd.DataFrame({"label": [1, 0, -1, 1], "q": [0.0, cfg.MINUTE_MAX_CORRECTED, 0.0, cfg.MINUTE_MAX_CORRECTED + 0.01]})
    assert list(detector.evaluable(t)) == [True, True, False, False]


def test_etapas_del_pipeline_usan_config():
    from src.features import build
    d = _defaults(build.record_series)
    assert d["wiener"] == cfg.EDR_WIENER and d["exclude_ectopic"] == cfg.EDR_EXCLUDE_ECTOPIC
    assert d["hampel"] == cfg.EDR_HAMPEL and d["interp"] == cfg.RR_INTERP
    assert d["relative"] == cfg.EDR_RELATIVE and d["aberrant"] == cfg.EDR_ABERRANT
    assert _defaults(edr.aberrant_qrs)["k"] == cfg.ABERRANT_IQR_K
    assert _defaults(detector.minute_table)["detrend_type"] is None
    assert _defaults(detector.evaluable)["max_corrected"] == cfg.MINUTE_MAX_CORRECTED
    assert _defaults(detector.fit_c)["max_corrected"] == cfg.MINUTE_MAX_CORRECTED


def test_realizacion_del_latido_es_la_misma_en_todos_lados():
    pre, post = cfg.REALIZATION_S
    for f in (wiener.extract_realizations, wiener.wiener_from_beats, filters.beat_spectrum):
        d = _defaults(f)
        assert (d["pre"], d["post"]) == (pre, post), f.__name__
    assert (duplicates.PRE, duplicates.POST) == (round(pre * cfg.FS), round(post * cfg.FS))


def test_edr_y_hampel_usan_config():
    assert _defaults(edr.beat_matrix)["half_width"] == cfg.QRS_AREA_HALF_S
    d = _defaults(edr.hampel_outliers)
    assert d["k"] == cfg.HAMPEL_K and d["n_sigmas"] == cfg.HAMPEL_SIGMAS


def test_movimiento_mide_lo_que_saca_el_filtro():
    assert cfg.MOV_LOWPASS[0] == cfg.ECG_FILTER[0]


# Literales prohibidos en el código de los notebooks: deben importarse las constantes.
PROHIBIDOS = {
    r"0\.016|0\.051": "banda escrita a mano: usar detector.BAND",
    r"\(0\.01,\s*0\.05\)": "banda escrita a mano: usar detector.BAND",
    r"\b2\.0,\s*240\b|\b240,\s*2\.0\b": "ventana y grilla escritas a mano: usar detector.WINDOW_S y FS_U",
    r"(?<![\w.])(W|ANCHO_VENTANA)\s*(,\s*\w+\s*)*=\s*240\b": "ventana escrita a mano: usar detector.WINDOW_S",
    r"centered_windows\([^)]*\b240\b": "ventana escrita a mano: usar detector.WINDOW_S",
    r"nperseg\s*=\s*128\b": "segmento de coherencia distinto del de A1: usar config.RESP_COH_SEG_S",
    r"AUC dentro de la noche \(mediana\)|B \(mediana": "el AUC dentro de la noche se resume con la media en todo el trabajo",
    r">=\s*20\s+and": "mínimo de minutos escrito a mano: usar config.MIN_MINUTES_PER_CLASS",
}


@pytest.mark.parametrize("nb", NOTEBOOKS, ids=lambda p: p.name)
def test_notebooks_sin_numeros_sueltos(nb):
    celdas = json.loads(nb.read_text())["cells"]
    codigo = "\n".join("".join(c["source"]) for c in celdas if c["cell_type"] == "code")
    errores = [f"{msg}: {m.group(0)!r}" for pat, msg in PROHIBIDOS.items() for m in re.finditer(pat, codigo)]
    assert not errores, "\n".join(errores)
