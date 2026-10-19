"""Filtro convencional: pasabanda Butterworth de fase cero.

Consigna: filtros convencionales (diseño).  Esquema v2 §4.2.
Bloque: Señal (Integrante 2).
"""
import numpy as np


def design_bandpass(fs: float, low: float, high: float, order: int):
    """Coeficientes SOS del pasabanda. Justificar orden y cortes con la respuesta en frecuencia."""
    raise NotImplementedError


def apply_zero_phase(x: np.ndarray, sos) -> np.ndarray:
    """Filtrado ida y vuelta (sosfiltfilt): fase cero, no corre el pico R."""
    raise NotImplementedError
