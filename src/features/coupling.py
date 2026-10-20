"""Acoplamiento cardiopulmonar: coherencia RR-EDR por banda.

Aporte novedoso (H1/H2).  Esquema v2 §2 y §4.7.
Bloque: Espectral (Integrante 3).

CR compara la coherencia RR-EDR en una banda lenta (ciclo de apnea) con la de
la banda respiratoria. Las bandas, la ventana y la forma de CR se eligen con
datos (E3); H1 se prueba con configuraciones fijadas de antemano (E2). RR y EDR
se remuestrean a 2 Hz porque Welch y el espectro cruzado necesitan muestreo
uniforme.
"""
from fractions import Fraction

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.signal import coherence, csd, resample_poly, welch


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


def coherence_spectrum(x: np.ndarray, y: np.ndarray, fs: float,
                       nperseg: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(f, coherencia, |potencia cruzada|) por Welch, con 50 % de solapamiento.

    Con una ventana de 2 * nperseg muestras quedan 3 segmentos.
    """
    kw = dict(fs=fs, nperseg=nperseg, noverlap=nperseg // 2, detrend="linear")
    f, cxy = coherence(x, y, **kw)
    _, pxy = csd(x, y, **kw)
    return f, cxy, np.abs(pxy)


def coherence_bands(x: np.ndarray, y: np.ndarray, fs: float, nperseg: int,
                    bands: dict) -> dict:
    """Coherencia media y potencia cruzada media en cada banda {nombre: (f1, f2)}.

    Devuelve {'coh_<nombre>': ..., 'xp_<nombre>': ...}. La banda incluye f1 y
    excluye f2. CR y sus variantes se arman a partir de estas columnas.
    """
    f, cxy, pxy = coherence_spectrum(x, y, fs, nperseg)
    out = {}
    for name, (f1, f2) in bands.items():
        m = (f >= f1) & (f < f2)
        out[f"coh_{name}"] = float(cxy[m].mean()) if m.any() else np.nan
        out[f"xp_{name}"] = float(pxy[m].mean()) if m.any() else np.nan
    return out


def surrogate_floor(rr_u: np.ndarray, edr_u: np.ndarray, fs: float = 2.0,
                    n: int = 200, rng=None) -> dict:
    """Percentil 95 de la coherencia con el EDR desplazado un lag aleatorio > ventana."""
    raise NotImplementedError
