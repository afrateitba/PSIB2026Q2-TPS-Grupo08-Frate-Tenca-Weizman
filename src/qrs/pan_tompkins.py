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
    """
    raise NotImplementedError


def validate_against_reference(detected: np.ndarray, reference: np.ndarray,
                               fs: float, tol: float = 0.10) -> dict:
    """Se, VPP, TP, FP, FN con tolerancia `tol` en segundos."""
    raise NotImplementedError
