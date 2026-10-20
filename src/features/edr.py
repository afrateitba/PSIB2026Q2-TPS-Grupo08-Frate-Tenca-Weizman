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

La polaridad del QRS cambia entre registros (electrodos invertidos en algunas
noches), así que se mide en cada registro con qrs_reference() y no se supone.
"""
import numpy as np

from ..features.coupling import weighted_coherence
from ..qrs.pan_tompkins import refine_peaks_parabolic


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
                half_width: float = 0.06,
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


def edr_series(t_beats: np.ndarray, values: np.ndarray,
               valid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(t, edr) con solo los latidos válidos y valores finitos."""
    keep = valid & np.isfinite(values)
    return t_beats[keep], values[keep]


def validate_edr(edr_u: np.ndarray, resp_u: np.ndarray, fs: float,
                 win_s: float = 120, seg_s: float = 32, fmin: float = 0.05) -> np.ndarray:
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
