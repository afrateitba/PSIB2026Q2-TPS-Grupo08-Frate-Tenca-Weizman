"""HRV en el dominio temporal.

Consigna: análisis de HRV.  Esquema v2 §4.7.
Bloque: Espectral (Integrante 3).
"""
import numpy as np


def hrv_time_features(rr: np.ndarray) -> dict:
    """RR medio, SDNN, RMSSD, pNN50 de un minuto."""
    raise NotImplementedError
