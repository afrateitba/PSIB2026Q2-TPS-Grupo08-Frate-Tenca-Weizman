"""Wiener estimado a partir de latidos alineados en R.

El promedio de ensamble representa la señal y las diferencias respecto
al promedio representan el ruido estimado. Esas diferencias también
pueden contener variaciones fisiológicas.

El filtro se aplica al ECG continuo, sin reemplazar los latidos
individuales por el promedio.
"""

import numpy as np

from scipy.signal import periodogram, firwin2, fftconvolve

from ..config import REALIZATION_S


def extract_realizations(ecg, r_peaks, fs, pre=REALIZATION_S[0], post=REALIZATION_S[1]):
    """Recorta latidos alrededor de R.

    r_peaks contiene posiciones en muestras, que pueden ser fraccionarias.
    Descarta los recortes incompletos e interpola para alinear los picos.
    Devuelve una matriz: filas = latidos, columnas = muestras.
    """
    x = np.asarray(ecg, dtype=float)
    peaks = np.asarray(r_peaks, dtype=float)

    if x.ndim != 1 or peaks.ndim != 1:
        raise ValueError("ECG y picos deben ser vectores.")
    if not np.isfinite(fs) or fs <= 0:
        raise ValueError("fs debe ser positiva.")
    if not np.isfinite([pre, post]).all() or pre < 0 or post < 0:
        raise ValueError("pre y post deben ser finitos y no negativos.")
    if len(x) == 0 or not np.isfinite(x).all():
        raise ValueError("El ECG debe ser no vacío y finito.")

    before = int(round(pre * fs))
    after = int(round(post * fs))
    offsets = np.arange(-before, after + 1)

    valid = (
        np.isfinite(peaks)
        & (peaks - before >= 0)
        & (peaks + after <= len(x) - 1)
    )
    centers = peaks[valid]

    if len(centers) == 0:
        return np.empty((0, len(offsets)))

    positions = centers[:, None] + offsets
    return np.interp(
        positions.ravel(), np.arange(len(x)), x
    ).reshape(positions.shape)


def estimate_psds(realizations, fs, template="mean"):
    """Devuelve frecuencias, PSD de la forma del latido y PSD media del residuo.

    `template`: "mean" (promediado coherente, el de mínima varianza con ruido
    gaussiano) o "median" (robusta a latidos raros); notebook 03, sección 5.
    """
    beats = np.asarray(realizations, dtype=float)

    if beats.ndim != 2 or beats.shape[0] < 2 or beats.shape[1] < 2:
        raise ValueError("Se necesitan al menos dos latidos de dos muestras.")
    if not np.isfinite(beats).all():
        raise ValueError("Los latidos deben contener valores finitos.")
    if not np.isfinite(fs) or fs <= 0:
        raise ValueError("fs debe ser positiva.")

    template = np.median(beats, axis=0) if template == "median" else beats.mean(axis=0)
    residuals = beats - template

    # Potencia de dos para incluir Nyquist y evitar truncar los recortes.
    # El relleno con ceros no aumenta la resolución espectral real.
    nfft = max(256, 1 << (beats.shape[1] - 1).bit_length())
    options = dict(
        fs=fs,
        window="hann",
        detrend="constant",
        scaling="density",
        nfft=nfft
    )

    f, s_s = periodogram(template, **options)
    _, residual_psds = periodogram(residuals, axis=1, **options)
    s_n = residual_psds.mean(axis=0)

    return f, s_s, s_n


def wiener_filter(ecg, f, s_s, s_n, fs, numtaps=129):
    """Aplica una aproximación FIR de H = Ss / (Ss + Sn).

    Usa `numtaps` coeficientes simétricos (129 por defecto; notebook 03, sección 5), extensión por reflexión y
    compensación del retardo. Es un procesamiento fuera de línea.
    """
    x = np.asarray(ecg, dtype=float)
    f = np.asarray(f, dtype=float)
    s_s = np.asarray(s_s, dtype=float)
    s_n = np.asarray(s_n, dtype=float)

    if not np.isfinite(fs) or fs <= 0:
        raise ValueError("fs debe ser positiva.")
    if x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("El ECG debe ser un vector finito de al menos dos muestras.")
    if (
        f.ndim != 1 or len(f) < 2
        or s_s.shape != f.shape or s_n.shape != f.shape
    ):
        raise ValueError("Frecuencias y espectros deben ser vectores del mismo tamaño.")
    if not all(np.isfinite(v).all() for v in (f, s_s, s_n)):
        raise ValueError("Frecuencias y espectros deben ser finitos.")
    if (s_s < 0).any() or (s_n < 0).any():
        raise ValueError("Los espectros no pueden ser negativos.")
    if (
        f[0] != 0 or not np.isclose(f[-1], fs / 2)
        or (np.diff(f) <= 0).any()
    ):
        raise ValueError("Las frecuencias deben crecer desde 0 hasta fs/2.")

    total = s_s + s_n
    gain = np.divide(s_s, total, out=np.zeros_like(s_s), where=total > 0)

    # Asegurar extremos exactos para firwin2.
    frequencies = f.copy()
    frequencies[-1] = fs / 2

    coefficients = firwin2(numtaps, frequencies, gain, fs=fs)

    margin = (len(coefficients) - 1) // 2
    padded = np.pad(x, margin, mode="reflect")
    filtered = fftconvolve(padded, coefficients, mode="same")

    return filtered[margin:-margin]


def wiener_from_beats(ecg, t_r, fs, pre=REALIZATION_S[0], post=REALIZATION_S[1], numtaps=None, template=None):
    """Wiener del registro estimado con sus propios latidos y aplicado al ECG.

    Recorta las realizaciones alrededor de cada pico R (`t_r` en segundos),
    estima Ss (promedio) y Sn (residuo) y aplica H = Ss / (Ss + Sn).
    """
    from ..config import WIENER_NUMTAPS, WIENER_TEMPLATE
    numtaps = WIENER_NUMTAPS if numtaps is None else numtaps
    template = WIENER_TEMPLATE if template is None else template
    f, s_s, s_n = estimate_psds(extract_realizations(ecg, np.asarray(t_r) * fs, fs, pre, post), fs, template)
    return wiener_filter(ecg, f, s_s, s_n, fs, numtaps)
