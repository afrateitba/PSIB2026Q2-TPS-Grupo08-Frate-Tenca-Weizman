"""Puntos de corte por ROC e índice de Youden (solo con desarrollo).  Esquema v2 §5."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from .compare import pooled_auc


def roc_youden(scores: np.ndarray, labels: np.ndarray) -> dict:
    """Umbral que maximiza Se + Esp - 1, con su Se, Esp y el AUC.

    Un minuto se clasifica como apnea si score >= umbral.
    """
    ok = np.isfinite(scores)
    s, y = scores[ok], labels[ok]
    thr = np.unique(s)
    pos, neg = np.sort(s[y == 1]), np.sort(s[y == 0])
    se = 1 - np.searchsorted(pos, thr, side="left") / len(pos)     # fracción de apnea >= umbral
    sp = np.searchsorted(neg, thr, side="left") / len(neg)         # fracción normal < umbral
    k = int(np.argmax(se + sp - 1))
    return {"umbral": float(thr[k]), "se": float(se[k]), "esp": float(sp[k]),
            "auc": pooled_auc(s, y)}


def record_agreement(scores: np.ndarray, labels: np.ndarray, records: np.ndarray,
                     threshold: float) -> dict:
    """Acierto por registro: fracción de minutos de apnea estimada contra la real.

    Devuelve la correlación de Spearman entre las dos fracciones y la tabla
    por registro. Solo cuentan los minutos con score finito.
    """
    d = pd.DataFrame({"r": records, "y": labels, "s": scores})
    d = d[np.isfinite(d.s)]
    t = d.groupby("r").agg(real=("y", "mean"), estimada=("s", lambda v: float((v >= threshold).mean())))
    return {"spearman": float(spearmanr(t.real, t.estimada).statistic), "tabla": t}


# --- Alternativas de umbral: notebook 11 ---
def _threshold_inputs(scores, labels):
    """Valida puntuaciones finitas y etiquetas binarias."""
    s = np.asarray(scores, dtype=float)
    y = np.asarray(labels)

    if s.ndim != 1 or y.ndim != 1 or len(s) != len(y) or len(s) == 0:
        raise ValueError("scores y labels deben ser vectores de igual largo.")
    if not np.isfinite(s).all() or not np.isin(y, [0, 1]).all():
        raise ValueError("Se requieren scores finitos y etiquetas 0/1.")
    return s, y.astype(int)


def umbral_proporcion(scores, labels):
    """Aproxima la cantidad real de positivos manteniendo juntos los empates.

    Clasificación: score >= umbral. Ante empate en la distancia a la
    cantidad real, se elige el menor umbral, priorizando sensibilidad.
    """
    s, y = _threshold_inputs(scores, labels)
    ordenados = np.sort(s)
    candidatos = np.r_[
        np.unique(ordenados),
        np.nextafter(ordenados[-1], np.inf),
    ]
    positivos = len(s) - np.searchsorted(
        ordenados, candidatos, side="left"
    )
    return float(candidatos[np.argmin(np.abs(positivos - y.sum()))])


def mediana_youden_sujetos(scores, labels, subjects,
                          n_boot=2000, seed=2026):
    """Mediana de Youden remuestreando sujetos completos.

    Descarta remuestreos sin ambas clases. Solo deben proporcionarse
    los sujetos usados para ajustar el umbral.
    """
    s, y = _threshold_inputs(scores, labels)
    g = np.asarray(subjects)

    if g.ndim != 1 or len(g) != len(s) or pd.isna(g).any():
        raise ValueError("subjects debe identificar cada observación.")
    if np.unique(y).size != 2:
        raise ValueError("Youden requiere ambas clases.")
    if not isinstance(n_boot, (int, np.integer)) or n_boot <= 0:
        raise ValueError("n_boot debe ser un entero positivo.")

    sujetos = pd.unique(g)
    filas = [np.flatnonzero(g == sujeto) for sujeto in sujetos]
    rng = np.random.default_rng(seed)
    umbrales = []

    for _ in range(n_boot):
        seleccion = rng.integers(0, len(sujetos), size=len(sujetos))
        indices = np.concatenate([filas[i] for i in seleccion])
        if np.unique(y[indices]).size == 2:
            umbrales.append(roc_youden(s[indices], y[indices])["umbral"])

    if not umbrales:
        raise ValueError("No hubo remuestreos válidos con ambas clases.")
    return float(np.median(umbrales))


def combinar_predicciones(pred_f, pred_hrv, metodo):
    """Combina dos vectores binarios mediante AND u OR."""
    f, h = np.asarray(pred_f), np.asarray(pred_hrv)
    if f.ndim != 1 or h.shape != f.shape:
        raise ValueError("Las predicciones deben ser vectores de igual largo.")
    if not np.isin(f, [0, 1]).all() or not np.isin(h, [0, 1]).all():
        raise ValueError("Las predicciones deben ser binarias.")

    if metodo == "AND":
        return f.astype(bool) & h.astype(bool)
    if metodo == "OR":
        return f.astype(bool) | h.astype(bool)
    raise ValueError("metodo debe ser AND u OR.")
