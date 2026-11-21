"""Detección de QRS: Pan-Tompkins adaptado a 100 Hz, con cinco mejoras.

Pan y Tompkins (1985), con las etapas lineales centradas (sin retardo). Las
mejoras (pulso aislado, piso de energía, ventana de onda T según el ritmo,
forma y energía por encima de 20 Hz) corrigen los errores que se vieron en
los registros de desarrollo. Justificación, ablación y sensibilidad de los
umbrales: notebooks/02_filtro_y_latidos.ipynb, sección 2. Es el detector
que usa todo el pipeline (src/qrs/beats.py, fuente "pt").
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, find_peaks, peak_prominences, sosfiltfilt

from .. import config as _cfg
from ..config import (QRS_BAND, QRS_FLOOR_FRAC, QRS_HF_CUTOFF, QRS_HF_RATIO_MIN,
                      QRS_INTEGRATION_S, QRS_LOCATE_S, QRS_PROMINENCE_MIN, QRS_REFRACTORY_S, QRS_RELEARN,
                      QRS_SEARCHBACK, QRS_SLOPE_WIN_S, QRS_TEMPLATE_CORR_MIN, QRS_TEMPLATE_N,
                      QRS_TOLERANCE_S, QRS_TWAVE_RR_FRAC, QRS_TWAVE_S)
QRS_TEMPLATE_HALF_S = _cfg.QRS_TEMPLATE_HALF_S
QRS_TEMPLATE_MIN = _cfg.QRS_TEMPLATE_MIN
QRS_PROMINENCE_WLEN_S = _cfg.QRS_PROMINENCE_WLEN_S
QRS_HF_HALF_S = _cfg.QRS_HF_HALF_S
QRS_HF_ORDER = _cfg.QRS_HF_ORDER
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


def _learn(mwi: np.ndarray, start: int, fs: float) -> tuple[float, float]:
    """(nivel de señal, nivel de ruido) iniciales a partir de 2 s de señal integrada."""
    w = mwi[start:start + int(2 * fs)]
    return w.max() / 3, w.mean() / 2


def high_freq_energy(ecg: np.ndarray, fs: float, fc: float = QRS_HF_CUTOFF,
                     half: float | None = None) -> np.ndarray:
    """Energía por encima de `fc` Hz en una ventana de ±`half` s alrededor de cada muestra.

    El QRS es rápido y tiene energía por encima de 20 Hz; la onda T es lenta y
    casi no tiene. Sirve para separarlos cuando la T deja en la señal
    integrada un pulso tan grande como el del QRS.
    """
    half = QRS_HF_HALF_S if half is None else half
    e = sosfiltfilt(butter(QRS_HF_ORDER, fc, "high", fs=fs, output="sos"), np.asarray(ecg, float)) ** 2
    n = int(round(half * fs))
    return np.convolve(e, np.ones(2 * n + 1), mode="same")


def _classify(mwi: np.ndarray, d: np.ndarray, fs: float, bp: np.ndarray | None = None,
              hf: np.ndarray | None = None, improved: bool = False,
              floor: float = 0.0) -> np.ndarray:
    """Umbrales adaptativos, búsqueda hacia atrás y descarte de ondas T.

    Devuelve los índices de los picos de la señal integrada que son QRS.

    Si la búsqueda hacia atrás no encuentra un latido (el umbral quedó por
    encima de los QRS, por ejemplo después de un artefacto o si baja la
    amplitud del ECG), los umbrales se vuelven a aprender con los 2 s que
    siguen, igual que al principio del registro. Sin esto el detector puede
    quedar ciego durante minutos (QRS_RELEARN; se revisa en
    notebooks/09_robustez_qrs.ipynb).

    Con `improved=True` (necesita `bp` y `hf`) se agregan las mejoras de
    notebooks/02_filtro_y_latidos.ipynb:
    - Un candidato solo puede ser QRS si es un pulso aislado de la señal
      integrada (prominencia relativa ≥ QRS_PROMINENCE_MIN) y supera el piso
      `floor`. Sin esto, en tramos sin ECG (oscilaciones regulares o ruido) el
      umbral se adapta al ruido y se marca un latido cada 0,2-0,3 s.
    - La ventana de onda T crece con el RR (QRS_TWAVE_RR_FRAC): con ritmo
      lento la T termina después de los 360 ms fijos.
    - Dentro de esa ventana, además de la pendiente, el candidato se descarta
      si su forma no se parece a la de los últimos QRS (correlación con la
      mediana de QRS_TEMPLATE_N latidos) o si tiene poca energía por encima
      de 20 Hz respecto del QRS anterior.
    """
    cand, _ = find_peaks(mwi, distance=max(1, int(round(QRS_REFRACTORY_S * fs))))
    if len(cand) == 0:
        return np.array([], dtype=int)
    if improved:
        rel = peak_prominences(mwi, cand, wlen=int(QRS_PROMINENCE_WLEN_S * fs))[0] / np.maximum(mwi[cand], 1e-12)
        eligible = (rel >= QRS_PROMINENCE_MIN) & (mwi[cand] >= floor)
    else:
        eligible = np.ones(len(cand), dtype=bool)
    spki, npki = _learn(mwi, 0, fs)
    h = int(round(QRS_SLOPE_WIN_S * fs))
    w = int(round(QRS_TEMPLATE_HALF_S * fs))
    twave = QRS_TWAVE_S * fs

    def slope(k):
        return np.abs(d[max(k - h, 0):k + h + 1]).max()

    templates: list = []

    def remember(k):
        if improved and w <= k < len(bp) - w:
            templates.append(bp[k - w:k + w + 1])
            if len(templates) > QRS_TEMPLATE_N:
                templates.pop(0)

    def looks_like_t(k):
        if not improved:
            return False
        if len(templates) >= QRS_TEMPLATE_MIN and w <= k < len(bp) - w:
            if np.corrcoef(bp[k - w:k + w + 1], np.median(templates, axis=0))[0, 1] < QRS_TEMPLATE_CORR_MIN:
                return True
        return last_hf is not None and hf[k] < QRS_HF_RATIO_MIN * last_hf

    # nmax: el pico de ruido más alto desde el último QRS. Alcanza con ese para
    # la búsqueda hacia atrás, y guardar solo ese hace que cada paso cueste lo
    # mismo aunque pasen minutos sin latidos.
    qrs, rr, nmax, last_slope, last_hf = [], [], None, None, None
    for i, k in enumerate(cand):
        thr = npki + 0.25 * (spki - npki)
        # Búsqueda hacia atrás: hueco mayor que 1,66 RR medios -> latido perdido.
        if rr and nmax is not None and k - qrs[-1] > QRS_SEARCHBACK * np.mean(rr[-8:]):
            j, nmax = nmax, None
            if mwi[j] > 0.5 * thr:
                rr.append(j - qrs[-1])
                qrs.append(j)
                last_slope = slope(j)
                remember(j)
                if improved:
                    last_hf = hf[j]
                spki = 0.25 * mwi[j] + 0.75 * spki
            elif QRS_RELEARN:
                spki, npki = _learn(mwi, k, fs)
            thr = npki + 0.25 * (spki - npki)
        if mwi[k] > thr and eligible[i]:
            s = slope(k)
            win = max(twave, QRS_TWAVE_RR_FRAC * np.mean(rr[-8:])) if (improved and rr) else twave
            # Onda T: muy cerca del QRS anterior y con menos de la mitad de su pendiente
            # (o, en la versión mejorada, con otra forma o sin energía rápida).
            if qrs and k - qrs[-1] < win and (s < 0.5 * last_slope or looks_like_t(k)):
                npki = 0.125 * mwi[k] + 0.875 * npki
                if nmax is None or mwi[k] > mwi[nmax]:
                    nmax = k
                continue
            if qrs:
                rr.append(k - qrs[-1])
            qrs.append(k)
            last_slope = s
            remember(k)
            if improved:
                last_hf = hf[k]
            spki = 0.125 * mwi[k] + 0.875 * spki
            nmax = None
        else:
            npki = 0.125 * mwi[k] + 0.875 * npki
            if nmax is None or mwi[k] > mwi[nmax]:
                nmax = k
    return np.array(qrs, dtype=int)


def detect_r_peaks(ecg: np.ndarray, fs: float, improved: bool = True) -> np.ndarray:
    """Índices de muestra de los picos R (umbral adaptativo).

    No supone la polaridad del R: el cuadrado de la derivada es igual para un R
    positivo que para uno invertido. Para ubicar el R se mide la polaridad del
    registro como el signo mediano de la deflexión dominante alrededor de cada
    QRS, y en cada latido se toma el extremo con ese signo a ±QRS_LOCATE_S.

    `improved=False` es el algoritmo clásico de Pan y Tompkins (1985). La
    versión mejorada (ver _classify) corre dos pasadas: la primera estima la
    energía típica de los QRS del registro y la segunda usa una fracción de
    ella (QRS_FLOOR_FRAC) como piso.
    """
    ecg = np.asarray(ecg, float)
    bp, d, mwi = pan_tompkins_signals(ecg, fs)
    if improved:
        hf = high_freq_energy(ecg, fs)
        q = _classify(mwi, d, fs, bp, hf, improved=True)
        if len(q):
            q = _classify(mwi, d, fs, bp, hf, improved=True,
                          floor=QRS_FLOOR_FRAC * float(np.median(mwi[q])))
    else:
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