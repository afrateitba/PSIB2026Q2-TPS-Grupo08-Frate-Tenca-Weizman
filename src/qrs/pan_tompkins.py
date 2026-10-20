"""Detección de QRS: Pan-Tompkins adaptado a 100 Hz.

Consigna: detección de complejo QRS.  Esquema v2 §4.3.
Bloque: Latidos (Integrante 1).

Fecha de corte 20/10: si no llega a Se/VPP >= 99 % contra las .qrs de la
base, las features se calculan con las .qrs y este detector queda como
validación.
"""
import numpy as np


def detect_r_peaks(ecg: np.ndarray, fs: float) -> np.ndarray:
    """Índices de muestra de los picos R (umbral adaptativo)."""
    raise NotImplementedError


def refine_peaks_parabolic(ecg: np.ndarray, peaks: np.ndarray):
    """Interpolación parabólica de 3 puntos: (tiempos fraccionarios [muestras], amplitudes).

    Corrige la resolución de 10 ms del muestreo a 100 Hz en RR y amplitud R.
    Ajusta una parábola por el pico y sus dos vecinos y devuelve su vértice.
    Sirve igual para máximos y mínimos. En los bordes de la señal, o si los
    tres puntos están alineados, devuelve la muestra sin corregir.
    """
    p = np.asarray(peaks, dtype=int)
    inner = (p > 0) & (p < len(ecg) - 1)
    y1 = ecg[p].astype(float)
    y0 = np.where(inner, ecg[np.clip(p - 1, 0, None)], y1)
    y2 = np.where(inner, ecg[np.clip(p + 1, None, len(ecg) - 1)], y1)
    den = y0 - 2 * y1 + y2
    delta = np.divide(0.5 * (y0 - y2), den, out=np.zeros_like(y1), where=den != 0)
    delta = np.clip(delta, -0.5, 0.5)
    return p + delta, y1 - 0.25 * (y0 - y2) * delta


def validate_against_reference(detected: np.ndarray, reference: np.ndarray,
                               fs: float, tol: float = 0.10) -> dict:
    """Se, VPP, TP, FP, FN con tolerancia `tol` en segundos."""
    raise NotImplementedError
