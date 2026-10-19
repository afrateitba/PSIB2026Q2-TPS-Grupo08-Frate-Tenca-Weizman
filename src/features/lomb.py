"""Espectro de HRV con periodograma de Lomb (RR muestreado de forma irregular).

Consigna: periodograma de Lomb.  Esquema v2 §4.7.
Bloque: Espectral (Integrante 3).
"""
import numpy as np


def lomb_psd(t: np.ndarray, rr: np.ndarray, f: np.ndarray) -> np.ndarray:
    """PSD de Lomb de la serie RR en las frecuencias f (Hz). No requiere remuestrear."""
    raise NotImplementedError


def band_powers(f: np.ndarray, pxx: np.ndarray, bands: dict) -> dict:
    """Potencia por banda (VLF, LF, HF) y cociente LF/HF."""
    raise NotImplementedError
