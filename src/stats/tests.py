"""Tests estadísticos.  Esquema v2 §5.
Bloque: los tres.

Unidad de inferencia principal: el sujeto (minutos de un mismo registro no
son independientes). Los tests por minuto son solo descriptivos.

Las diferencias pareadas se prueban con Wilcoxon directamente. Elegir el test
según el resultado de un Shapiro previo (como decía el esquema v2) cambia el
nivel de significación real; con n ~ 14 sujetos el test no paramétrico es el
natural. El Shapiro se puede reportar como dato descriptivo.
"""
import numpy as np
from scipy.stats import rankdata, wilcoxon


def paired_subject_test(diffs: np.ndarray, n_boot: int = 5000, seed: int = 2026) -> dict:
    """Wilcoxon de rangos con signo (dos colas) sobre una diferencia por sujeto.

    Devuelve n, cuántos son positivos, W, p, la correlación rango-biserial
    (de -1 a 1: proporción neta de rangos a favor de diferencias positivas),
    la mediana y su IC 95 % por bootstrap de sujetos.
    """
    d = np.asarray(diffs, dtype=float)
    d = d[np.isfinite(d)]
    res = wilcoxon(d, alternative="two-sided")
    nz = d[d != 0]
    ranks = rankdata(np.abs(nz))                     # empates: rango promedio
    r_plus, r_minus = ranks[nz > 0].sum(), ranks[nz < 0].sum()
    boot = np.median(np.random.default_rng(seed).choice(d, size=(n_boot, len(d))), axis=1)
    return {"n": len(d), "positivos": int((d > 0).sum()), "W": float(res.statistic),
            "p": float(res.pvalue), "r_rb": float((r_plus - r_minus) / (r_plus + r_minus)),
            "mediana": float(np.median(d)), "ic_mediana": tuple(np.percentile(boot, [2.5, 97.5]))}


def mann_whitney_cliff(x_normal: np.ndarray, x_apnea: np.ndarray) -> dict:
    """Descriptivo por minuto: U, p y delta de Cliff."""
    raise NotImplementedError


def holm(pvals) -> np.ndarray:
    """p ajustados por Holm (paso a paso hacia abajo), en el orden original."""
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    adj = np.maximum.accumulate((len(p) - np.arange(len(p))) * p[order])
    out = np.empty_like(p)
    out[order] = np.minimum(adj, 1.0)
    return out
