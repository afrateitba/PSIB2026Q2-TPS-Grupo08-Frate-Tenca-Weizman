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
