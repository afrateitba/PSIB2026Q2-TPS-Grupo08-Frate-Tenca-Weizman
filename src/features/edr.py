"""EDR: respiración derivada del ECG.

Aporte novedoso.  Esquema v2 §4.7 y §4.8.
Bloque: Señal (Integrante 2).

La respiración cambia la posición del corazón respecto de los electrodos y la
impedancia del tórax, y eso modula la forma del QRS latido a latido. Hay
varias formas de medir esa modulación; el experimento E1 las compara contra la
respiración real de los 8 registros que la tienen:
- edr_amplitude:    amplitud del pico dominante (refinada con una parábola).
- edr_peak_to_peak: máximo menos mínimo del QRS.
- edr_area:         área con signo del QRS.
- edr_pca:          puntaje en la primera componente principal de los latidos.
- edr_baseline:     línea de base del ECG crudo en cada latido (deriva).

La polaridad del QRS cambia entre registros (electrodos invertidos en algunas
noches), así que se mide en cada registro con qrs_reference() y no se supone.
"""
import numpy as np

from ..config import ECG_FILTER
from ..config import HAMPEL_K, HAMPEL_SIGMAS, QRS_AREA_HALF_S, RESP_COH_SEG_S
from ..features.coupling import weighted_coherence
from ..preprocessing.filters import apply_zero_phase, design_bandpass
from ..qrs.pan_tompkins import refine_peaks_parabolic
from ..qrs.rr_clean import rr_in_range


def qrs_reference(ecg: np.ndarray, qrs: np.ndarray, fs: float,
                  search: float = 0.15) -> tuple[int, int]:
    """(desfase, signo) del QRS del registro, a partir de su latido mediano.

    desfase: muestras desde la marca de `qrs` hasta la deflexión dominante
    (sqrs125 no marca el pico R). signo: +1 si esa deflexión es positiva.
    """
    h = int(round(search * fs))
    idx = qrs[(qrs >= h) & (qrs < len(ecg) - h)]
    med = np.median(np.stack([ecg[i - h: i + h + 1] for i in idx]), axis=0)
    med = med - np.median(med)
    k = int(np.argmax(np.abs(med)))
    return k - h, int(np.sign(med[k]))


def beat_matrix(ecg: np.ndarray, centers: np.ndarray, fs: float,
                half_width: float = QRS_AREA_HALF_S,
                baseline: tuple | None = None) -> tuple[np.ndarray, np.ndarray]:
    """(latidos, ok): ventana de ±`half_width` s alrededor de cada centro de QRS.

    `ok` marca los centros que entran completos en la señal. Si `baseline` es
    (inicio, fin) en segundos relativos al centro, a cada latido se le resta la
    mediana del ECG en ese intervalo (el segmento PR, que es isoeléctrico).
    """
    h = int(round(half_width * fs))
    lo = h if baseline is None else max(h, -int(round(baseline[0] * fs)))
    ok = (centers >= lo) & (centers < len(ecg) - h)
    c = centers[ok]
    beats = ecg[c[:, None] + np.arange(-h, h + 1)]
    if baseline is not None:
        b0, b1 = int(round(baseline[0] * fs)), int(round(baseline[1] * fs))
        beats = beats - np.median(ecg[c[:, None] + np.arange(b0, b1 + 1)], axis=1, keepdims=True)
    return beats, ok


def edr_amplitude(beats: np.ndarray, sign: int) -> np.ndarray:
    """Amplitud del pico dominante de cada latido, con la polaridad corregida."""
    x = sign * beats
    k = np.argmax(x, axis=1)
    flat = x.ravel()
    _, amp = refine_peaks_parabolic(flat, np.arange(len(x)) * x.shape[1] + k)
    edge = (k == 0) | (k == x.shape[1] - 1)          # sin vecinos dentro del latido
    return np.where(edge, x[np.arange(len(x)), k], amp)


def edr_peak_to_peak(beats: np.ndarray) -> np.ndarray:
    """Máximo menos mínimo de cada latido: no depende de la polaridad."""
    return beats.max(axis=1) - beats.min(axis=1)


def edr_area(beats: np.ndarray, sign: int, fs: float) -> np.ndarray:
    """Área con signo de cada latido (mV·s), con la polaridad corregida."""
    return sign * beats.sum(axis=1) / fs


def edr_pca(beats: np.ndarray) -> np.ndarray:
    """Puntaje de cada latido en la primera componente principal.

    El signo se elige para que un puntaje mayor sea un latido más parecido
    (en proyección) al latido medio, o sea, un QRS más grande.
    """
    centered = beats - beats.mean(axis=0)
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    score = centered @ vt[0]
    if np.corrcoef(score, beats @ beats.mean(axis=0))[0, 1] < 0:
        score = -score
    return score


def edr_baseline(ecg: np.ndarray, centers: np.ndarray, fs: float,
                 interval: tuple = (-0.10, -0.05)) -> tuple[np.ndarray, np.ndarray]:
    """(valores, ok): línea de base del ECG crudo en cada latido.

    Mediana del segmento PR (`interval` en s relativo al centro del QRS). Es el
    EDR por deriva de línea de base: no mira la forma del QRS y solo tiene
    sentido sobre la señal sin pasabanda, porque el filtro elimina la deriva.
    """
    b0, b1 = int(round(interval[0] * fs)), int(round(interval[1] * fs))
    ok = (centers + b0 >= 0) & (centers + b1 < len(ecg))
    c = centers[ok]
    return np.median(ecg[c[:, None] + np.arange(b0, b1 + 1)], axis=1), ok


def edr_series(t_beats: np.ndarray, values: np.ndarray,
               valid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(t, edr) con solo los latidos válidos y valores finitos."""
    keep = valid & np.isfinite(values)
    return t_beats[keep], values[keep]


EDR_METHODS = ("area", "baseline")


def compute_edr(ecg: np.ndarray, qrs: np.ndarray, fs: float, method: str = "area",
                filt: tuple = ECG_FILTER) -> tuple[np.ndarray, np.ndarray]:
    """(t, edr) con uno de los dos métodos que E1 no pudo separar.

    E1 (notebooks/02_E1_edr.ipynb) dejó empatadas dos variantes y E3 eligió
    el área:
    - "area": área con signo del QRS (±60 ms del centro, polaridad del
      registro) sobre el ECG con el pasabanda `filt` (corte bajo, corte alto,
      orden; por defecto config.ECG_FILTER).
    - "baseline": mediana del segmento PR (-100 a -50 ms) del ECG crudo.
    En los dos casos solo se usan latidos con RR de 0,3 a 2 s.
    """
    if method == "area":
        x = apply_zero_phase(ecg, design_bandpass(fs, *filt))
        off, sign = qrs_reference(x, qrs, fs)
        centers = qrs + off
        beats, ok = beat_matrix(x, centers, fs, QRS_AREA_HALF_S)
        values = edr_area(beats, sign, fs)
    elif method == "baseline":
        off, _ = qrs_reference(ecg, qrs, fs)
        centers = qrs + off
        values, ok = edr_baseline(ecg, centers, fs, (-0.10, -0.05))
    else:
        raise ValueError(f"método de EDR desconocido: {method} (opciones: {EDR_METHODS})")
    valid = rr_in_range(centers / fs)
    return edr_series(centers[ok] / fs, values, valid[ok])


def validate_edr(edr_u: np.ndarray, resp_u: np.ndarray, fs: float,
                 win_s: float = 120, seg_s: float = RESP_COH_SEG_S, fmin: float = 0.05) -> np.ndarray:
    """Coherencia ponderada EDR-respiración real en ventanas de `win_s` s, sin solapar.

    Las dos series tienen que estar muestreadas en la misma grilla uniforme.
    El peso es el espectro de la respiración, así que la banda la define la
    propia señal medida (solo RESP_RECORDS). Una ventana con alguna muestra
    no finita (la respiración tiene muestras inválidas) da NaN: se descarta en
    lugar de rellenarla.
    """
    n, nseg = int(win_s * fs), int(seg_s * fs)
    m = min(len(edr_u), len(resp_u)) // n
    out = np.full(m, np.nan)
    for i in range(m):
        a, b = edr_u[i * n:(i + 1) * n], resp_u[i * n:(i + 1) * n]
        if np.isfinite(a).all() and np.isfinite(b).all():
            out[i] = weighted_coherence(a, b, fs, nseg, fmin)
    return out


# --- EDR a partir de los latidos del detector propio (notebook 03) -----------
BEAT_METHODS = ("area", "amplitude", "baseline", "combined")


def hampel_outliers(values: np.ndarray, k: int = HAMPEL_K, n_sigmas: float = HAMPEL_SIGMAS) -> np.ndarray:
    """Latidos atípicos según el filtro de Hampel, con un piso para el desvío.

    Un valor es atípico si se aparta de la mediana de sus `k` vecinos más de
    `n_sigmas` desvíos robustos (1,4826 × la mediana de los desvíos absolutos
    en la ventana). En una oscilación suave y limpia ese desvío local se hace
    casi cero en las crestas, y el filtro marcaría las crestas como atípicas;
    por eso el desvío no puede bajar del nivel de ruido de la serie, estimado
    con las diferencias entre latidos consecutivos (1,4826 × mediana |Δx| / √2).
    """
    import pandas as pd
    s = pd.Series(np.asarray(values, float))
    med = s.rolling(k, center=True, min_periods=1).median()
    resid = (s - med).abs()
    local = 1.4826 * resid.rolling(k, center=True, min_periods=1).median()
    floor = 1.4826 * float(np.median(np.abs(np.diff(s.to_numpy())))) / np.sqrt(2)
    return (resid > n_sigmas * np.maximum(local, floor)).to_numpy()


def beat_edr(ecg: np.ndarray, t_r: np.ndarray, fs: float, method: str = "area",
             filt: tuple = ECG_FILTER, exclude: np.ndarray | None = None,
             hampel: bool = False, prefilter=None, relative: bool = False,
             return_scale: bool = False):
    """(t, edr) a partir de los tiempos de los picos R `t_r` (s).

    method: "area" (área con signo del QRS en ±60 ms, sobre el ECG filtrado),
    "amplitude" (amplitud del pico dominante), "baseline" (mediana del segmento
    PR del ECG crudo) o "combined" (promedio del área y la deriva, cada una
    estandarizada sobre la noche).
    exclude: latidos a descartar (por ejemplo, los ectópicos que marca la
    limpieza del RR). hampel: descarta además los atípicos (hampel_outliers).
    prefilter: función que se aplica al ECG filtrado antes de medir el QRS
    (por ejemplo, un filtro de Wiener).
    relative (solo "area"): divide el área de cada latido por el tamaño típico
    del QRS del registro, la mediana del área sin signo (∫|QRS|). Así la EDR
    no depende del tamaño del QRS, que cambia entre personas por la anatomía
    y la posición de los electrodos (notebooks/03_edr_wiener.ipynb, sección 7).
    No se usa la mediana del área con signo: en un QRS con R y S la parte
    positiva y la negativa se cancelan y esa mediana no mide el tamaño.
    return_scale: devuelve también esa escala (NaN si relative es False).
    """
    if method not in BEAT_METHODS:
        raise ValueError(f"método desconocido: {method} (opciones: {BEAT_METHODS})")
    centers = np.unique(np.rint(np.asarray(t_r) * fs).astype(int))
    keep = rr_in_range(centers / fs)
    if exclude is not None:
        keep &= ~np.asarray(exclude, bool)[:len(centers)]
    x = apply_zero_phase(ecg, design_bandpass(fs, *filt))
    if prefilter is not None:
        x = prefilter(x)
    _, sign = qrs_reference(x, centers, fs)
    vals = {}
    size = np.full(len(centers), np.nan)
    if method in ("area", "amplitude", "combined"):
        beats, ok = beat_matrix(x, centers, fs, QRS_AREA_HALF_S)
        v = np.full(len(centers), np.nan)
        v[ok] = edr_area(beats, sign, fs) if method != "amplitude" else edr_amplitude(beats, sign)
        size[ok] = np.abs(beats).sum(axis=1) / fs
        vals["qrs"] = v
    if method in ("baseline", "combined"):
        b, ok = edr_baseline(ecg, centers, fs, (-0.10, -0.05))
        v = np.full(len(centers), np.nan)
        v[ok] = b
        vals["baseline"] = v
    keep &= np.all([np.isfinite(v) for v in vals.values()], axis=0)
    if hampel:
        for v in vals.values():
            bad = np.zeros(len(centers), bool)
            bad[keep] = hampel_outliers(v[keep])
            keep &= ~bad
    if method == "combined":
        z = lambda v: (v - np.mean(v[keep])) / np.std(v[keep])
        values = (z(vals["qrs"]) + z(vals["baseline"])) / 2
    else:
        values = next(iter(vals.values()))
    scale = np.nan
    if relative:
        if method != "area":
            raise ValueError("relative solo está definido para method='area'")
        scale = float(np.median(size[keep]))
        values = values / scale
    if return_scale:
        return centers[keep] / fs, values[keep], scale
    return centers[keep] / fs, values[keep]
