"""Acoplamiento cardiopulmonar: coherencia RR-EDR por banda.

Aporte novedoso (H1/H2).  Esquema v2 §2 y §4.7.
Bloque: Espectral (Integrante 3).

CR = coherencia(VLF+LF) / coherencia(HF). RR y EDR se remuestrean a 2 Hz
porque Welch y el espectro cruzado necesitan muestreo uniforme.
"""
from fractions import Fraction

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.signal import coherence, resample_poly, welch


def resample_uniform(t: np.ndarray, x: np.ndarray, fs: float = 2.0,
                     kind: str = "cubic") -> tuple[np.ndarray, np.ndarray]:
    """(t_u, x_u): interpolación a una grilla uniforme de `fs` Hz.

    La grilla arranca en el primer múltiplo de 1/fs dentro de [t[0], t[-1]],
    así dos series con distintos latidos caen en los mismos instantes.
    `kind`: "cubic" (spline cúbico) o "linear".
    """
    t_u = np.arange(np.ceil(t[0] * fs), np.floor(t[-1] * fs) + 1) / fs
    if kind == "cubic":
        return t_u, CubicSpline(t, x)(t_u)
    if kind == "linear":
        return t_u, np.interp(t_u, t, x)
    raise ValueError(f"kind desconocido: {kind}")


def downsample(x: np.ndarray, fs_in: float, fs_out: float) -> np.ndarray:
    """Cambia la frecuencia de muestreo con filtro antialias (resample_poly).

    La muestra 0 de la salida corresponde a la muestra 0 de la entrada.
    """
    r = Fraction(fs_out / fs_in).limit_denominator(1000)
    return resample_poly(x, r.numerator, r.denominator)


def weighted_coherence(x: np.ndarray, y: np.ndarray, fs: float, nperseg: int,
                       fmin: float = 0.05) -> float:
    """Coherencia de Welch entre x e y, promediada con el espectro de y como peso.

    Solo cuentan las frecuencias >= `fmin`. Así la banda de interés la define
    dónde tiene potencia y (la respiración real) y no un rango fijado a mano.
    """
    kw = dict(fs=fs, nperseg=nperseg, noverlap=nperseg // 2, detrend="linear")
    f, cxy = coherence(x, y, **kw)
    _, pyy = welch(y, **kw)
    m = f >= fmin
    w = pyy[m].sum()
    return float((cxy[m] * pyy[m]).sum() / w) if w > 0 else np.nan


def coherence_bands(rr_u: np.ndarray, edr_u: np.ndarray, fs: float = 2.0,
                    nperseg: int = 512) -> dict:
    """Coherencia media por banda, potencia cruzada y CR para una ventana."""
    raise NotImplementedError


def surrogate_floor(rr_u: np.ndarray, edr_u: np.ndarray, fs: float = 2.0,
                    n: int = 200, rng=None) -> dict:
    """Percentil 95 de la coherencia con el EDR desplazado un lag aleatorio > ventana."""
    raise NotImplementedError
