"""Valores p por bootstrap y corrección de Holm para familias de comparaciones.

Cuando una conclusión se apoya en varias comparaciones a la vez, alguna puede
salir "significativa" por azar. La corrección de Holm controla la probabilidad
de declarar al menos una diferencia falsa en toda la familia, y es siempre al
menos tan potente como la de Bonferroni (Aickin y Gensler, 1996,
doi:10.2105/AJPH.86.5.726).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def p_bootstrap(diferencias) -> float:
    """p bilateral de una diferencia a partir de su distribución bootstrap.

    p = 2 · min(P(d ≤ 0), P(d ≥ 0)), acotado a 1. Con B remuestreos el p más
    chico que se puede distinguir de cero es ~2/B.
    """
    d = np.asarray(diferencias, float)
    d = d[np.isfinite(d)]
    if len(d) == 0 or np.allclose(d, 0):
        return np.nan
    return float(min(1.0, 2 * min(np.mean(d <= 0), np.mean(d >= 0))))


def holm(pvals: dict) -> dict:
    """p corregidos por Holm para un diccionario {comparación: p}.

    Se ordenan los m valores de menor a mayor; el i-ésimo (desde 1) se
    multiplica por (m − i + 1), y se toma el máximo acumulado para que el orden
    se mantenga. Una comparación resiste la corrección si su p corregido < 0,05.
    """
    validos = {k: v for k, v in pvals.items() if np.isfinite(v)}
    orden = sorted(validos, key=validos.get)
    m = len(orden)
    out, acumulado = {}, 0.0
    for i, k in enumerate(orden):
        acumulado = max(acumulado, min(1.0, (m - i) * validos[k]))
        out[k] = acumulado
    return out


def tabla_holm(familia: dict, alfa: float = 0.05) -> pd.DataFrame:
    """Tabla con diferencia, p, p de Holm y si resiste, para {nombre: (diferencia, distribución bootstrap)}."""
    pv = {k: p_bootstrap(b) for k, (_, b) in familia.items()}
    ph = holm(pv)
    filas = [{"comparación": k, "diferencia": d, "p": pv[k], "p de Holm": ph.get(k, np.nan),
              "significativa sin corregir": "sí" if pv[k] < alfa else "no",
              "resiste Holm": "sí" if ph.get(k, 1.0) < alfa else "no"}
             for k, (d, _) in familia.items() if np.isfinite(pv[k])]
    return pd.DataFrame(filas).set_index("comparación").sort_values("p")
