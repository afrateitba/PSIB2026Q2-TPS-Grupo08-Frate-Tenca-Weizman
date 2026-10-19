"""EDR: respiración derivada del ECG a partir de la amplitud de la onda R.

Aporte novedoso.  Esquema v2 §4.7 y §4.8.
Bloque: Señal (Integrante 2).
"""
import numpy as np


def edr_series(t_r: np.ndarray, amp_r: np.ndarray):
    """(t, edr): amplitud R por latido, sin tendencia lenta (cambios de posición)."""
    raise NotImplementedError


def validate_edr(edr_u: np.ndarray, resp_u: np.ndarray, fs: float) -> dict:
    """Correlación y coherencia EDR vs respiración real (solo RESP_RECORDS)."""
    raise NotImplementedError
