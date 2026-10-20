"""Limpieza de la serie RR.  Esquema v2 §4.5.
Bloque: Latidos (Integrante 1).

- Fuera de 0,3-2 s -> inválido.
- Cambio > 20 % respecto de la mediana local -> ectópico.
- Inválidos y ectópicos se interpolan; un minuto con > 20 % corregido se excluye.
"""
import numpy as np
import pandas as pd


def rr_in_range(t_r: np.ndarray, lo: float = 0.3, hi: float = 2.0) -> np.ndarray:
    """Latidos cuyo RR con el anterior y con el siguiente está entre `lo` y `hi` s.

    El primer y el último latido quedan inválidos porque les falta un vecino.
    """
    rr = np.diff(t_r)
    ok = (rr >= lo) & (rr <= hi)
    valid = np.zeros(len(t_r), dtype=bool)
    valid[1:-1] = ok[:-1] & ok[1:]
    return valid


def clean_rr(t_r: np.ndarray, lo: float = 0.3, hi: float = 2.0, ectopic: float = 0.2,
             k: int = 11) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(t, rr_limpio, corregidos) a partir de los tiempos de los latidos.

    Cada RR se ubica en el tiempo del latido que lo cierra. Se corrige un RR si
    está fuera de [lo, hi] s o si se aparta más de `ectopic` de la mediana de
    los `k` RR vecinos válidos (un ectópico deja un RR corto y otro largo).
    Los corregidos se reemplazan por interpolación lineal de los válidos.
    """
    rr = np.diff(t_r)
    t = t_r[1:]
    bad = (rr < lo) | (rr > hi)
    med = (pd.Series(np.where(bad, np.nan, rr))
           .rolling(k, center=True, min_periods=1).median().to_numpy())
    corrected = bad | (np.abs(rr / med - 1) > ectopic)
    rr_c = rr.copy()
    rr_c[corrected] = np.interp(t[corrected], t[~corrected], rr[~corrected])
    return t, rr_c, corrected


def minute_quality(t: np.ndarray, corrected: np.ndarray, n_minutes: int) -> np.ndarray:
    """Fracción de RR corregidos en cada minuto (NaN si el minuto no tiene latidos)."""
    m = (t // 60).astype(int)
    keep = m < n_minutes
    total = np.bincount(m[keep], minlength=n_minutes)
    bad = np.bincount(m[keep], weights=corrected[keep].astype(float), minlength=n_minutes)
    return np.divide(bad, total, out=np.full(n_minutes, np.nan), where=total > 0)
