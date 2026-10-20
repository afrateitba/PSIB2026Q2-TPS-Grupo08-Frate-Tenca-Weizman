"""Filtro convencional: pasabanda Butterworth de fase cero.

Consigna: filtros convencionales (diseño).  Esquema v2 §4.2.
Bloque: Señal (Integrante 2).

Los cortes y el orden del pipeline (config.ECG_FILTER) se justifican en
notebooks/07_filtro.ipynb a partir del espectro del ECG y de una
especificación de la respuesta en frecuencia.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfiltfilt, sosfreqz, welch


def design_bandpass(fs: float, low: float, high: float, order: int):
    """Coeficientes SOS de un pasabanda Butterworth de orden `order`."""
    return butter(order, [low, high], btype="band", fs=fs, output="sos")


def apply_zero_phase(x: np.ndarray, sos) -> np.ndarray:
    """Filtrado ida y vuelta (sosfiltfilt): fase cero, no corre el pico R.

    El orden efectivo queda duplicado y la ganancia es |H(f)|^2.
    """
    return sosfiltfilt(sos, x)


def mean_psd(signals: list, fs: float, nperseg: int = 4096) -> tuple[np.ndarray, np.ndarray]:
    """(f, PSD media) de varias señales; cada PSD se normaliza a potencia total 1.

    Normalizar hace que todos los registros pesen igual, aunque tengan
    amplitudes distintas.
    """
    psds = []
    for x in signals:
        f, p = welch(x, fs=fs, nperseg=nperseg)
        psds.append(p / np.trapezoid(p, f))
    return f, np.mean(psds, axis=0)


def cumulative_energy_freq(f: np.ndarray, power: np.ndarray, frac: float) -> float:
    """Frecuencia por debajo de la cual queda la fracción `frac` de la energía."""
    c = np.cumsum(power)
    return float(f[np.searchsorted(c / c[-1], frac)])


def beat_spectrum(ecg: np.ndarray, peaks: np.ndarray, fs: float, pre: float = 0.25,
                  post: float = 0.40, nfft: int = 1024) -> tuple[np.ndarray, np.ndarray]:
    """(f, |X|^2) del latido mediano (de -pre a +post s alrededor de cada pico).

    Se resta la mediana del latido para sacar la línea de base y se completa con
    ceros hasta `nfft` muestras para tener más puntos en frecuencia.
    """
    a, b = int(round(pre * fs)), int(round(post * fs))
    peaks = peaks[(peaks >= a) & (peaks < len(ecg) - b)]
    beat = np.median(ecg[peaks[:, None] + np.arange(-a, b)], axis=0)
    beat = beat - np.median(beat)
    return np.fft.rfftfreq(nfft, 1 / fs), np.abs(np.fft.rfft(beat, nfft)) ** 2


def frequency_response(sos, fs: float, n: int = 8192) -> dict:
    """Respuesta del filtro: ganancia (dB) de una pasada y de ida y vuelta, fase y retardo de grupo."""
    f, h = sosfreqz(sos, worN=n, fs=fs)
    mag = np.maximum(np.abs(h), 1e-12)
    phase = np.unwrap(np.angle(h))
    gd = -np.gradient(phase, 2 * np.pi * f)                    # segundos
    return {"f": f, "ganancia_db": 20 * np.log10(mag), "ganancia_db_ida_vuelta": 40 * np.log10(mag),
            "fase": phase, "retardo_s": gd}


def meets_spec(sos, fs: float, passband: tuple, stop: dict, max_pass_db: float) -> bool:
    """¿Cumple la especificación con el filtrado ida y vuelta?

    En la banda de paso la atenuación no supera `max_pass_db`; en cada
    frecuencia de `stop` ({f: dB}) la atenuación es al menos esos dB.
    """
    r = frequency_response(sos, fs)
    g = r["ganancia_db_ida_vuelta"]
    inband = (r["f"] >= passband[0]) & (r["f"] <= passband[1])
    if -g[inband].min() > max_pass_db:
        return False
    return all(-np.interp(fz, r["f"], g) >= db for fz, db in stop.items())
