"""Calidad de la señal por registro (descriptiva).  Esquema v2 §4.1.

Trabaja sobre el ECG en unidades del conversor (data.load_ecg_digital), donde
la igualdad entre muestras es exacta.
"""
from __future__ import annotations

import numpy as np


def extreme_fraction(d: np.ndarray) -> float:
    """Fracción de muestras iguales al mínimo o al máximo del registro.

    Una señal que no satura tiene muy pocas muestras justo en sus extremos. Si
    el amplificador o el conversor recortan, se acumulan ahí.
    """
    d = np.asarray(d)
    return float(np.mean((d == d.min()) | (d == d.max())))


def saturated_mask(d: np.ndarray, bits: int) -> np.ndarray:
    """Muestras en los topes de un conversor de `bits` bits con signo."""
    d = np.asarray(d)
    return (d <= -2 ** (bits - 1) + 1) | (d >= 2 ** (bits - 1) - 1)


def flat_mask(d: np.ndarray, fs: float, min_s: float = 1.0) -> np.ndarray:
    """Muestras en tramos de `min_s` s o más sin ningún cambio.

    Un ECG real no queda exactamente constante durante un segundo: esos
    tramos son señal perdida (electrodo suelto, señal cortada o clavada en
    el tope del conversor).
    """
    d = np.asarray(d)
    bounds = np.r_[0, np.flatnonzero(np.diff(d) != 0) + 1, len(d)]
    runs = np.diff(bounds)
    return np.repeat(runs >= min_s * fs, runs)


def flat_fraction(d: np.ndarray, fs: float, min_s: float = 1.0) -> float:
    """Fracción de muestras en tramos planos de `min_s` s o más (ver flat_mask)."""
    return float(flat_mask(d, fs, min_s).mean())
