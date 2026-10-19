"""Acoplamiento cardiopulmonar: coherencia RR-EDR por banda.

Aporte novedoso (H1/H2).  Esquema v2 §2 y §4.7.
Bloque: Espectral (Integrante 3).

CR = coherencia(VLF+LF) / coherencia(HF). RR y EDR se remuestrean a 2 Hz
porque Welch y el espectro cruzado necesitan muestreo uniforme.
"""
import numpy as np


def resample_uniform(t: np.ndarray, x: np.ndarray, fs: float = 2.0):
    """(t_u, x_u): interpolación a muestreo uniforme."""
    raise NotImplementedError


def coherence_bands(rr_u: np.ndarray, edr_u: np.ndarray, fs: float = 2.0,
                    nperseg: int = 512) -> dict:
    """Coherencia media por banda, potencia cruzada y CR para una ventana."""
    raise NotImplementedError


def surrogate_floor(rr_u: np.ndarray, edr_u: np.ndarray, fs: float = 2.0,
                    n: int = 200, rng=None) -> dict:
    """Percentil 95 de la coherencia con el EDR desplazado un lag aleatorio > ventana."""
    raise NotImplementedError
