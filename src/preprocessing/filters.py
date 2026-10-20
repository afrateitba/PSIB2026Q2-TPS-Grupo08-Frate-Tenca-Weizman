"""Filtro convencional: pasabanda Butterworth de fase cero.

Consigna: filtros convencionales (diseño).  Esquema v2 §4.2.
Bloque: Señal (Integrante 2).

Las funciones son genéricas: el orden y los cortes del pipeline se eligen en
la etapa 4.2, con la respuesta en frecuencia y con datos.
"""
import numpy as np
from scipy.signal import butter, sosfiltfilt


def design_bandpass(fs: float, low: float, high: float, order: int):
    """Coeficientes SOS de un pasabanda Butterworth de orden `order`."""
    return butter(order, [low, high], btype="band", fs=fs, output="sos")


def apply_zero_phase(x: np.ndarray, sos) -> np.ndarray:
    """Filtrado ida y vuelta (sosfiltfilt): fase cero, no corre el pico R.

    El orden efectivo queda duplicado y la ganancia es |H(f)|^2.
    """
    return sosfiltfilt(sos, x)
