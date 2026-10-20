"""Espectro de HRV con periodograma de Lomb (RR muestreado de forma irregular).

Consigna: periodograma de Lomb.  Esquema v2 §4.7.
Bloque: Espectral (Integrante 3).

El RR existe solo en los instantes de cada latido, que no están equiespaciados.
Lomb estima el espectro directamente sobre esos instantes, sin interpolar.
"""
import numpy as np
from scipy.signal import lombscargle

HRV_BANDS = {
    "apnea": (0.01, 0.05),     # ciclo de apnea (20-100 s)
    "vlf": (0.01, 0.04),
    "lf": (0.04, 0.15),
    "hf": (0.15, 0.40),
    "total": (0.01, 0.40),
}


def lomb_psd(t: np.ndarray, rr: np.ndarray, f: np.ndarray) -> np.ndarray:
    """PSD de Lomb de la serie RR (s^2/Hz) en las frecuencias f (Hz).

    Se resta la media. lombscargle sin normalizar equivale al periodograma
    clásico |X|^2 / N; la PSD unilateral es 2 P / fs, con fs = latidos por
    segundo, y así su integral aproxima la varianza del RR.
    """
    x = rr - rr.mean()
    p = lombscargle(t, x, 2 * np.pi * f, normalize=False)
    fs = (len(t) - 1) / (t[-1] - t[0])
    return 2 * p / fs


def band_powers(f: np.ndarray, pxx: np.ndarray, bands: dict = HRV_BANDS) -> dict:
    """Potencia integrada por banda (s^2) y LF/HF si están las dos bandas."""
    out = {}
    for name, (f1, f2) in bands.items():
        m = (f >= f1) & (f < f2)
        out[name] = float(np.trapezoid(pxx[m], f[m])) if m.sum() > 1 else np.nan
    if "lf" in out and "hf" in out:
        out["lf_hf"] = out["lf"] / out["hf"] if out["hf"] > 0 else np.nan
    return out
