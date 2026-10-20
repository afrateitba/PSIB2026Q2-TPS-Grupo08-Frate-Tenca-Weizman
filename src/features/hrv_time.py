"""HRV en el dominio temporal.

Consigna: análisis de HRV.  Esquema v2 §4.7.
Bloque: Espectral (Integrante 3).
"""
import numpy as np


def hrv_time_features(rr: np.ndarray) -> dict:
    """RR medio, SDNN, RMSSD (en s) y pNN50 de una ventana de RR."""
    d = np.diff(rr)
    return {"mean_rr": float(rr.mean()), "sdnn": float(rr.std(ddof=1)),
            "rmssd": float(np.sqrt(np.mean(d ** 2))) if len(d) else np.nan,
            "pnn50": float(np.mean(np.abs(d) > 0.05)) if len(d) else np.nan}
