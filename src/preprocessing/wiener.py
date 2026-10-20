"""Filtro óptimo (Wiener) estimado a partir de realizaciones (latidos).

Consigna: recorte en realizaciones + filtros óptimos.  Esquema v2 §4.4.
Bloque: Señal (Integrante 2).

Idea: latidos alineados en R = realizaciones. Promedio de ensamble -> PSD de
señal; residuo -> PSD de ruido; H(f) = Ss / (Ss + Sn), aplicado como filtro
LTI sobre el ECG continuo. Al ser LTI conserva la relación de amplitudes entre
latidos (el EDR). Nunca promediar ni empujar latidos hacia el template.
"""
import numpy as np


def extract_realizations(ecg: np.ndarray, r_peaks: np.ndarray, fs: float,
                         pre: float = 0.25, post: float = 0.40) -> np.ndarray:
    """Matriz (n_latidos, n_muestras) de latidos recortados alrededor de cada R."""
    raise NotImplementedError


def estimate_psds(realizations: np.ndarray, fs: float):
    """(f, S_s, S_n): PSD del promedio de ensamble y PSD media del residuo."""
    raise NotImplementedError


def wiener_filter(ecg: np.ndarray, f: np.ndarray, s_s: np.ndarray,
                  s_n: np.ndarray, fs: float) -> np.ndarray:
    """Aplica H(f) = Ss / (Ss + Sn) al ECG continuo."""
    raise NotImplementedError
