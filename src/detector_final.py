"""El detector final, congelado: la configuración con nombre que se evalúa en test.

Es el detector que dejaron los notebooks 07 a 09, armado y ajustado solo con
los 47 registros de desarrollo:
- detector de QRS de Pan y Tompkins (1985) con sus seis etapas (09);
- refinamiento del pico R;
- EDR: área relativa del QRS, sin Wiener y sin latidos ectópicos ni
  atípicos (Hampel), interpolada con spline cúbico (08);
- Welch quitando la recta en cada segmento;
- no se decide en los minutos con más de 20 % de RR corregidos;
- sin medida de confianza.

Sus parámetros están en docs/parametros_final.json. El archivo queda
congelado con su hash SHA-256: si cambia, cargar_params() falla. Así el
notebook de test usa exactamente lo que se fijó en desarrollo.

Los valores por defecto de src/config.py siguen siendo los de la versión
evaluada en test (notebooks 04 y 05), para que esos notebooks se puedan
reproducir. Este módulo pasa todas las opciones explícitamente.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from .config import RAW_DIR, ROOT
from .features.build import record_series
from .features.detector import c_score, evaluable, load_params, minute_table
from .qrs import pan_tompkins as _pt

PARAMS_PATH = ROOT / "docs" / "parametros_final.json"
SHA256_PARAMS = "73344a364ee3bd27616c8a1eff5f65fdc9dcd58f59e516290ebcf6615d2b0b8d"

# etapa del QRS en parametros_final.json -> (parámetro de src/config.py, si está activa)
_ETAPAS_QRS = {
    "reaprendizaje": lambda: bool(_pt.QRS_RELEARN),
    "pulso_aislado": lambda: _pt.QRS_PROMINENCE_MIN > 0,
    "piso_de_energía": lambda: _pt.QRS_FLOOR_FRAC > 0,
    "ventana_según_el_ritmo": lambda: _pt.QRS_TWAVE_RR_FRAC > 0,
    "forma": lambda: _pt.QRS_TEMPLATE_CORR_MIN > -1,
    "energía_rápida": lambda: _pt.QRS_HF_RATIO_MIN > 0,
}


def sha256(path: Path = PARAMS_PATH) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cargar_params(path: Path = PARAMS_PATH, verificar: bool = True) -> dict:
    """Parámetros del detector final. Falla si el archivo no es el congelado."""
    if verificar and sha256(path) != SHA256_PARAMS:
        raise ValueError(f"{path} no es el archivo congelado del detector final (SHA-256 distinto)")
    return load_params(path)


def opciones_edr(p: dict) -> dict:
    """Opciones de record_series que fija el detector final."""
    e = p["etapas"]
    return {"edr_method": "area", "wiener": e["wiener_edr"], "exclude_ectopic": e["excluir_ectopicos_edr"],
            "hampel": e["hampel_edr"], "aberrant": e["aberrantes_varon_edr"], "relative": e["edr_relativa"],
            "interp": e["interpolacion"], "refine": e["refinamiento_pico_r"]}


def verificar_qrs(p: dict) -> None:
    """El detector de QRS de src/qrs tiene que tener las mismas etapas que el congelado."""
    for etapa, activa in _ETAPAS_QRS.items():
        if activa() != p["etapas_qrs"][etapa]:
            raise ValueError(f"la etapa del QRS '{etapa}' no coincide con el detector final congelado")


def tabla_final(rec: str, raw_dir: Path = RAW_DIR, params: dict | None = None) -> tuple[pd.DataFrame, dict]:
    """Aplica el detector final a un registro. No ajusta nada.

    Devuelve (tabla, series): una fila por minuto con P_RR, EDR_noche, los dos
    términos de C, C, la decisión (1 apnea), la etiqueta y si el minuto se
    evalúa; y el resultado de record_series (latidos, RR y EDR).
    """
    p = params or cargar_params()
    verificar_qrs(p)
    e = p["etapas"]
    s = record_series(rec, raw_dir, **opciones_edr(p))
    tab = minute_table(rec, raw_dir, series=s, detrend_type=e["tendencia_welch"])
    pc = {k: p[k] for k in ("mu1", "s1", "mu2", "s2", "w")}
    tab["termino_rr"] = (tab["P_RR"] - p["mu1"]) / p["s1"]
    tab["termino_edr"] = p["w"] * (tab["EDR_noche"] - p["mu2"]) / p["s2"]
    tab["C"] = c_score(tab, pc)
    tab["decision"] = (tab["C"] > p["umbral"]).astype(int)
    tab["evaluado"] = evaluable(tab, e["max_rr_corregidos_por_minuto"])
    return tab, s
