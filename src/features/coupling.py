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
from functools import lru_cache

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.signal import coherence, detrend, get_window, resample_poly, welch
from scipy.signal.windows import dpss


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


def welch_spectra(x: np.ndarray, y: np.ndarray, fs: float,
                  nperseg: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """(f, Sxx, Syy, Sxy) por Welch con 50 % de solapamiento, en una sola pasada.

    Igual que scipy.signal.welch y csd: ventana de Hann, detrend lineal por
    segmento y densidad unilateral. Sxy es complejo.
    """
    step = nperseg - nperseg // 2
    n_seg = 1 + (len(x) - nperseg) // step
    idx = np.arange(nperseg)[None, :] + step * np.arange(n_seg)[:, None]
    win = get_window("hann", nperseg)
    fx = np.fft.rfft(detrend(x[idx], axis=1, type="linear") * win, axis=1)
    fy = np.fft.rfft(detrend(y[idx], axis=1, type="linear") * win, axis=1)
    scale = np.full(fx.shape[1], 2.0 / (fs * (win ** 2).sum()))
    scale[0] /= 2
    if nperseg % 2 == 0:
        scale[-1] /= 2
    sxx, syy = (np.abs(fx) ** 2).mean(0) * scale, (np.abs(fy) ** 2).mean(0) * scale
    sxy = (np.conj(fx) * fy).mean(0) * scale
    return np.fft.rfftfreq(nperseg, 1 / fs), sxx, syy, sxy


def _coherence(sxx, syy, sxy):
    return np.divide(np.abs(sxy) ** 2, sxx * syy, out=np.zeros(len(sxx)), where=sxx * syy > 0)


def coherence_spectrum(x: np.ndarray, y: np.ndarray, fs: float,
                       nperseg: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(f, coherencia, |potencia cruzada|) por Welch, con 50 % de solapamiento.

    Con una ventana de 2 * nperseg muestras quedan 3 segmentos. Da lo mismo que
    scipy.signal.coherence y csd, pero calcula los espectros en una sola pasada.
    """
    f, sxx, syy, sxy = welch_spectra(x, y, fs, nperseg)
    return f, _coherence(sxx, syy, sxy), np.abs(sxy)


@lru_cache(maxsize=16)
def _tapers(n: int, nw: float) -> np.ndarray:
    """Tapers DPSS (se calculan una vez por largo de ventana)."""
    return dpss(n, nw, int(2 * nw - 1))


def multitaper_spectra(x: np.ndarray, y: np.ndarray, fs: float,
                       nw: float = 2.0) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """(f, Sxx, Syy, Sxy) por multitaper sobre toda la ventana (escala relativa).

    Usa K = 2*nw - 1 tapers DPSS (Slepian). Cada taper da una estimación casi
    independiente del espectro y se promedian, en lugar de partir la ventana
    en segmentos como Welch: se gana estabilidad sin perder resolución
    (ancho de banda ±nw/T).
    """
    n = len(x)
    tapers = _tapers(n, nw)                                    # k x n
    xd, yd = detrend(x, type="linear"), detrend(y, type="linear")
    fx, fy = np.fft.rfft(tapers * xd, axis=1), np.fft.rfft(tapers * yd, axis=1)
    sxx, syy = (np.abs(fx) ** 2).mean(0) / fs, (np.abs(fy) ** 2).mean(0) / fs
    sxy = (fx * np.conj(fy)).mean(0) / fs
    return np.fft.rfftfreq(n, 1 / fs), sxx, syy, sxy


def coherence_multitaper(x: np.ndarray, y: np.ndarray, fs: float,
                         nw: float = 2.0) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(f, coherencia, |potencia cruzada|) por multitaper sobre toda la ventana."""
    f, sxx, syy, sxy = multitaper_spectra(x, y, fs, nw)
    return f, _coherence(sxx, syy, sxy), np.abs(sxy)


def coherence_bands(x: np.ndarray, y: np.ndarray, fs: float, nperseg: int,
                    bands: dict, estimator: str = "welch") -> dict:
    """Coherencia y potencias en cada banda {nombre: (f1, f2)}.

    `estimator`: "welch" (segmentos de `nperseg`, 50 % de solapamiento) o
    "multitaper" (NW = 2 sobre toda la ventana; ignora `nperseg`).
    Devuelve por banda:
    - coh_<nombre>: coherencia media en la banda;
    - xp_<nombre>:  potencia cruzada |Sxy| media en la banda;
    - cw_<nombre>:  coherencia ponderada por la potencia cruzada (pesa más las
                    frecuencias donde las dos señales tienen potencia común, así
                    un acoplamiento que ocupa pocas frecuencias no se diluye);
    - px_<nombre>, py_<nombre>: potencia media de x y de y en la banda.
    La banda incluye f1 y excluye f2.
    """
    if estimator == "welch":
        f, sxx, syy, sxy = welch_spectra(x, y, fs, nperseg)
    elif estimator == "multitaper":
        f, sxx, syy, sxy = multitaper_spectra(x, y, fs)
    else:
        raise ValueError(f"estimador desconocido: {estimator}")
    cxy, pxy = _coherence(sxx, syy, sxy), np.abs(sxy)
    out = {}
    for name, (f1, f2) in bands.items():
        m = (f >= f1) & (f < f2)
        if not m.any():
            out.update({f"{k}_{name}": np.nan for k in ("coh", "xp", "cw", "px", "py")})
            continue
        w = pxy[m].sum()
        out[f"coh_{name}"] = float(cxy[m].mean())
        out[f"xp_{name}"] = float(pxy[m].mean())
        out[f"cw_{name}"] = float((cxy[m] * pxy[m]).sum() / w) if w > 0 else np.nan
        out[f"px_{name}"] = float(sxx[m].mean())
        out[f"py_{name}"] = float(syy[m].mean())
    return out


def surrogate_floor(rr_u: np.ndarray, edr_u: np.ndarray, fs: float = 2.0,
                    n: int = 200, rng=None) -> dict:
    """Percentil 95 de la coherencia con el EDR desplazado un lag aleatorio > ventana."""
    raise NotImplementedError
