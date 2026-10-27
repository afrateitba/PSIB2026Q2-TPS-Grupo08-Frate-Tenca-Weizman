"""Detección de QRS: Pan-Tompkins adaptado a 100 Hz.

Consigna: detección de complejo QRS.  Esquema v3 §4.3.
Bloque: Latidos.

Criterio de adopción (esquema v3 §7.4): si F calculada con este detector es
no inferior a F calculada con las .qrs de la base, se adopta. Si no, se siguen
usando las .qrs y este detector queda como validación. Se y VPP contra las
.qrs se reportan, pero no deciden.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks

from ..config import (QRS_BAND, QRS_INTEGRATION_S, QRS_LOCATE_S, QRS_REFRACTORY_S,
                      QRS_SEARCHBACK, QRS_SLOPE_WIN_S, QRS_TOLERANCE_S, QRS_TWAVE_S)
from ..preprocessing.filters import apply_zero_phase, design_bandpass


def pan_tompkins_signals(ecg: np.ndarray, fs: float):
    """(pasabanda, derivada, integrada): las etapas lineales de Pan-Tompkins.

    Todas centradas, sin retardo: el pasabanda va ida y vuelta, la derivada de
    5 puntos es simétrica y la ventana de integración está centrada. Así los
    picos de la señal integrada caen sobre el QRS y no hay que corregir demoras.
    """
    low, high, order = QRS_BAND
    bp = apply_zero_phase(np.asarray(ecg, float), design_bandpass(fs, low, high, order))
    # d[n] = (2x[n+1] + x[n+2] - 2x[n-1] - x[n-2]) * fs / 8
    d = np.convolve(bp, np.array([1, 2, 0, -2, -1]) * fs / 8, mode="same")
    n = max(1, int(round(QRS_INTEGRATION_S * fs)))
    mwi = np.convolve(d ** 2, np.ones(n) / n, mode="same")
    return bp, d, mwi


def _classify(mwi: np.ndarray, d: np.ndarray, fs: float) -> np.ndarray:
    """Umbrales adaptativos, búsqueda hacia atrás y descarte de ondas T.

    Devuelve los índices de los picos de la señal integrada que son QRS.
    """
    cand, _ = find_peaks(mwi, distance=max(1, int(round(QRS_REFRACTORY_S * fs))))
    if len(cand) == 0:
        return np.array([], dtype=int)
    learn = mwi[: int(2 * fs)]                      # fase de aprendizaje: 2 s
    spki, npki = learn.max() / 3, learn.mean() / 2  # nivel de señal y de ruido
    h = int(round(QRS_SLOPE_WIN_S * fs))
    twave = QRS_TWAVE_S * fs

    def slope(k):
        return np.abs(d[max(k - h, 0):k + h + 1]).max()

    qrs, rr, noise, last_slope = [], [], [], None
    for k in cand:
        thr = npki + 0.25 * (spki - npki)
        # Búsqueda hacia atrás: hueco mayor que 1,66 RR medios -> latido perdido.
        if len(rr) and noise and k - qrs[-1] > QRS_SEARCHBACK * np.mean(rr[-8:]):
            j = max(noise, key=lambda c: mwi[c])
            if mwi[j] > 0.5 * thr:
                rr.append(j - qrs[-1])
                qrs.append(j)
                last_slope = slope(j)
                spki = 0.25 * mwi[j] + 0.75 * spki
                noise = []
                thr = npki + 0.25 * (spki - npki)
        if mwi[k] > thr:
            s = slope(k)
            # Onda T: muy cerca del QRS anterior y con menos de la mitad de su pendiente.
            if qrs and k - qrs[-1] < twave and s < 0.5 * last_slope:
                npki = 0.125 * mwi[k] + 0.875 * npki
                noise.append(k)
                continue
            if qrs:
                rr.append(k - qrs[-1])
            qrs.append(k)
            last_slope = s
            spki = 0.125 * mwi[k] + 0.875 * spki
            noise = []
        else:
            npki = 0.125 * mwi[k] + 0.875 * npki
            noise.append(k)
    return np.array(qrs, dtype=int)


def detect_r_peaks(ecg: np.ndarray, fs: float) -> np.ndarray:
    """Índices de muestra de los picos R (umbral adaptativo).

    No supone la polaridad del R: el cuadrado de la derivada es igual para un R
    positivo que para uno invertido. Para ubicar el R se mide la polaridad del
    registro como el signo mediano de la deflexión dominante alrededor de cada
    QRS, y en cada latido se toma el extremo con ese signo a ±QRS_LOCATE_S.
    """
    ecg = np.asarray(ecg, float)
    _, d, mwi = pan_tompkins_signals(ecg, fs)
    q = _classify(mwi, d, fs)
    h = int(round(QRS_LOCATE_S * fs))
    q = q[(q >= h) & (q < len(ecg) - h)]
    if len(q) == 0:
        return np.array([], dtype=int)
    win = ecg[q[:, None] + np.arange(-h, h + 1)]
    dev = win - np.median(win, axis=1, keepdims=True)
    dominant = dev[np.arange(len(q)), np.argmax(np.abs(dev), axis=1)]
    sign = 1 if np.median(dominant) >= 0 else -1
    return np.unique(q - h + np.argmax(sign * win, axis=1))


def refine_peaks_parabolic(ecg: np.ndarray, peaks: np.ndarray):
    """Interpolación parabólica de 3 puntos: (tiempos fraccionarios [muestras], amplitudes).

    Corrige la resolución de 10 ms del muestreo a 100 Hz en RR y amplitud R.
    Ajusta una parábola por el pico y sus dos vecinos y devuelve su vértice.
    Sirve igual para máximos y mínimos. En los bordes de la señal, o si los
    tres puntos están alineados, devuelve la muestra sin corregir.
    """
    p = np.asarray(peaks, dtype=int)
    inner = (p > 0) & (p < len(ecg) - 1)
    y1 = ecg[p].astype(float)
    y0 = np.where(inner, ecg[np.clip(p - 1, 0, None)], y1)
    y2 = np.where(inner, ecg[np.clip(p + 1, None, len(ecg) - 1)], y1)
    den = y0 - 2 * y1 + y2
    delta = np.divide(0.5 * (y0 - y2), den, out=np.zeros_like(y1), where=den != 0)
    delta = np.clip(delta, -0.5, 0.5)
    return p + delta, y1 - 0.25 * (y0 - y2) * delta


def r_peaks_from_marks(ecg: np.ndarray, marks: np.ndarray, fs: float, offset: int,
                       sign: int, search: float = 0.03,
                       refine: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """(t_r [s], amplitud): pico R real cerca de cada marca, refinado con la parábola.

    Busca la deflexión dominante (con la polaridad `sign` del registro) a
    ±`search` s de marca + `offset` (ver edr.qrs_reference). Si dos marcas
    caen en el mismo pico, queda uno solo. Con `refine=False` devuelve el
    pico en la muestra entera (lo usa la verificación de 4.1).
    """
    h = int(round(search * fs))
    c = marks + offset
    c = c[(c >= h) & (c < len(ecg) - h)]
    k = np.unique(c - h + np.argmax(sign * ecg[c[:, None] + np.arange(-h, h + 1)], axis=1))
    if not refine:
        return k / fs, sign * ecg[k]
    t, amp = refine_peaks_parabolic(sign * ecg, k)
    return t / fs, amp


def validate_against_reference(detected: np.ndarray, reference: np.ndarray,
                               fs: float, tol: float = QRS_TOLERANCE_S) -> dict:
    """Se, VPP, TP, FP, FN con tolerancia `tol` en segundos.

    `detected` y `reference` en muestras. Cada referencia se empareja con a lo
    sumo una detección (y al revés), recorriendo las dos listas ordenadas.
    """
    det = np.sort(np.asarray(detected, float))
    ref = np.sort(np.asarray(reference, float))
    t = tol * fs
    i = j = tp = 0
    while i < len(det) and j < len(ref):
        if abs(det[i] - ref[j]) <= t:
            tp += 1; i += 1; j += 1
        elif det[i] < ref[j]:
            i += 1
        else:
            j += 1
    fp, fn = len(det) - tp, len(ref) - tp
    return {"Se": tp / (tp + fn) if tp + fn else np.nan,
            "VPP": tp / (tp + fp) if tp + fp else np.nan,
            "TP": tp, "FP": fp, "FN": fn}