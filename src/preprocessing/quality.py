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


# --- Calidad por ventana: notebook 10 ---
def window_signal_quality(d, fs, bits, minutes, width_s=240.0, adc_zero=0):
    """Calidad del ECG digital en ventanas centradas en cada minuto.

    Señal perdida: tramo plano o permanencia en los topes durante
    al menos un segundo. Las ventanas incompletas no son evaluables.
    """
    import pandas as pd

    d = np.asarray(d)
    minutes = np.asarray(minutes, dtype=int)

    if d.ndim != 1 or d.size == 0:
        raise ValueError("El ECG debe ser un vector no vacío.")
    if not np.isfinite(fs) or fs <= 0 or width_s <= 0:
        raise ValueError("fs y width_s deben ser positivos.")

    planos = flat_mask(d, fs, min_s=1.0)
    en_tope = saturated_mask(d - adc_zero, bits)
    saturados_largos = en_tope & flat_mask(
        en_tope.astype(np.int8), fs, min_s=1.0
    )
    perdida = planos | saturados_largos

    inicio = np.rint(
        (60 * minutes + 30 - width_s / 2) * fs
    ).astype(int)
    fin = np.rint(
        (60 * minutes + 30 + width_s / 2) * fs
    ).astype(int)
    completa = (inicio >= 0) & (fin <= len(d))

    acumulado = np.r_[0, np.cumsum(perdida, dtype=np.int64)]
    segundos = np.full(len(minutes), np.nan)
    segundos[completa] = (
        acumulado[fin[completa]] - acumulado[inicio[completa]]
    ) / fs

    return pd.DataFrame({
        "minute": minutes,
        "ventana_completa": completa,
        "segundos_perdidos": segundos,
        "sin_perdida": completa & (segundos == 0),
    })
