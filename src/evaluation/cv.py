"""Validación cruzada por personas del detector C y bootstrap pareado de su exactitud.

Es la misma validación cruzada de notebooks/04_feature_y_detector.ipynb
(sección 15): las personas se reparten en 5 grupos; con los otros 4 se
estandarizan los términos de C, se elige w (0 a 3, cada 0,25) maximizando el
AUC y se fija el umbral de Youden; después se clasifica el grupo que quedó
afuera. La usa notebooks/07_simplificacion.ipynb para comparar variantes del
detector (docs/criterio_parsimonia.md).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from ..features.detector import c_score, fit_c, youden_threshold

GRILLA_W = np.arange(0, 3.01, 0.25)
N_GRUPOS = 5
SEMILLA = 2026
CUANTILES_CONFIANZA = (0.5, 0.9)   # cortes de la confianza: percentiles del movimiento (notebook 04, sección 12)


def auc(x, y) -> float:
    """AUC por rangos (probabilidad de que un minuto con apnea tenga un valor mayor que uno normal)."""
    x, y = np.asarray(x, float), np.asarray(y, int)
    n1 = int(y.sum()); n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    r = rankdata(x)
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def grupos_personas(sujetos, n_grupos: int = N_GRUPOS, semilla: int = SEMILLA) -> list:
    """Reparto de las personas en grupos (el mismo de notebooks/04 con la misma semilla)."""
    return np.array_split(np.random.default_rng(semilla).permutation(np.unique(sujetos)), n_grupos)


def cv_c(e: pd.DataFrame, n_grupos: int = N_GRUPOS, semilla: int = SEMILLA) -> pd.DataFrame:
    """Clasifica cada minuto de `e` con un detector ajustado sin su persona.

    `e`: una fila por minuto, con label (0/1), subject, P_RR y EDR_noche (y
    mov_rel para la confianza). Todas las filas se usan para ajustar y para
    clasificar: quien llama elige qué minutos entran (por ejemplo, solo los
    que tienen 20 % o menos de RR corregidos). Devuelve `e` con grupo, w,
    umbral, margen (C − umbral), pred y, si hay mov_rel, confianza (cortes en
    los percentiles 50 y 90 del movimiento de los grupos de entrenamiento).
    """
    e = e.reset_index(drop=True).copy()
    y = e["label"].to_numpy()
    s = e["subject"].to_numpy()
    out = {k: np.full(len(e), np.nan) for k in ("grupo", "w", "umbral", "margen")}
    conf = np.full(len(e), "", dtype=object)
    for k, gpo in enumerate(grupos_personas(s, n_grupos, semilla)):
        te = np.isin(s, gpo); tr = ~te
        e_tr = e[tr]
        p0 = fit_c(e_tr, 0.0, max_corrected=None)   # la estandarización no depende de w
        a_w = [auc(c_score(e_tr, {**p0, "w": float(w)}), y[tr]) for w in GRILLA_W]
        w = float(GRILLA_W[int(np.nanargmax(a_w))])
        p = {**p0, "w": w}
        u = youden_threshold(c_score(e_tr, p).to_numpy(), y[tr])
        out["grupo"][te], out["w"][te], out["umbral"][te] = k, w, u
        out["margen"][te] = c_score(e[te], p).to_numpy() - u
        if "mov_rel" in e:
            c1, c2 = np.quantile(e.loc[tr, "mov_rel"], CUANTILES_CONFIANZA)
            conf[te] = pd.cut(e.loc[te, "mov_rel"], [-np.inf, c1, c2, np.inf],
                              labels=["alta", "media", "baja"]).astype(str).to_numpy()
    for k, v in out.items():
        e[k] = v
    e["grupo"] = e["grupo"].astype(int)
    e["pred"] = (e["margen"] > 0).astype(int)
    if "mov_rel" in e:
        e["confianza"] = conf
    return e


def sorteos_personas(personas, n: int = 4000, semilla: int = SEMILLA) -> list:
    """Sorteos de personas con reposición para el bootstrap (los mismos para todas las comparaciones)."""
    personas = np.asarray(sorted(set(personas)))
    rng = np.random.default_rng(semilla)
    return [rng.choice(personas, len(personas)) for _ in range(n)]


def exactitud(acierto: pd.Series, sujetos: pd.Series, sorteos: list | None = None):
    """Exactitud con todos los minutos (si sorteos es None) o su distribución bootstrap.

    En cada sorteo se suman los aciertos y los minutos de las personas
    sorteadas (con repetición). Una persona sin minutos en `acierto` aporta
    cero; si un sorteo no tiene ningún minuto, da NaN.
    """
    g = pd.DataFrame({"ok": np.asarray(acierto, float), "s": np.asarray(sujetos)}).groupby("s").ok.agg(["sum", "size"])
    if sorteos is None:
        return float(g["sum"].sum() / g["size"].sum())
    tot, n = g["sum"], g["size"]
    res = np.empty(len(sorteos))
    for i, so in enumerate(sorteos):
        a, b = tot.reindex(so).sum(), n.reindex(so).sum()
        res[i] = a / b if b > 0 else np.nan
    return res


def metricas(y, pred) -> dict:
    """Sensibilidad, especificidad y exactitud por minuto."""
    y, pred = np.asarray(y, int), np.asarray(pred, int)
    tp = int(((pred == 1) & (y == 1)).sum()); tn = int(((pred == 0) & (y == 0)).sum())
    return {"sensibilidad": tp / max(int((y == 1).sum()), 1), "especificidad": tn / max(int((y == 0).sum()), 1),
            "exactitud": (tp + tn) / max(len(y), 1)}


def replicar_personas(e: pd.DataFrame, muestra) -> pd.DataFrame:
    """Tabla con los minutos de cada persona de `muestra`, repetidos tantas veces como aparece.

    Es un sorteo del bootstrap de personas que después se vuelve a ajustar
    entero (cv_c): así el intervalo incluye cuánto cambia el detector cuando
    cambian las personas con que se ajusta, y no solo con cuáles se mide
    (Bates, Hastie y Tibshirani, 2023). Una persona repetida conserva su
    identificador, así que sus copias caen siempre en el mismo grupo de la
    validación cruzada y nunca se entrena con una copia para clasificar la otra.
    """
    s = e["subject"].to_numpy()
    idx = np.concatenate([np.flatnonzero(s == u) for u in muestra])
    return e.iloc[idx].reset_index(drop=True)
