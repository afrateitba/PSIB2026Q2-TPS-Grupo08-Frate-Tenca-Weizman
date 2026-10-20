"""Detección de grabaciones duplicadas en la base.  Esquema v2 §3 y §4.1.

PhysioNet documenta que c05 y c06 son la misma grabación. Comparando las
señales aparecen dos pares más: x22 = x35 y x33 = x34 (ver SAME_RECORDING).
Dos registros son la misma grabación si un tramo de uno aparece, muestra a
muestra, dentro del otro.

Correlacionar las señales completas de los 2.346 pares es caro, así que primero
se compara el latido promedio de cada registro y solo los pares con latidos
casi idénticos se confirman con la señal. El latido promedio no alcanza para
decidir si dos registros son de la misma persona (cambia con la posición de los
electrodos), pero dos copias de la misma grabación lo tienen idéntico.
"""
from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import butter, fftconvolve, sosfiltfilt

from .config import RAW_DIR
from .data import load_ecg, load_qrs

PRE, POST = 25, 40   # ventana del latido en muestras a 100 Hz: -250 ms a +400 ms
SHIFT = 3            # alineación fina de ±30 ms al comparar latidos


def beat_template(ecg: np.ndarray, qrs: np.ndarray, fs: float,
                  hours: tuple = (1, 4)) -> np.ndarray:
    """Latido mediano (z-score) de los latidos con RR estable entre `hours`.

    El pasabanda de 0,5-40 Hz es solo para comparar morfologías; el filtro del
    pipeline está en preprocessing/filters.py.
    """
    sos = butter(2, [0.5, 40], btype="band", fs=fs, output="sos")
    x = sosfiltfilt(sos, ecg)
    q = qrs[(qrs > hours[0] * 3600 * fs) & (qrs < hours[1] * 3600 * fs)]
    rr = np.diff(q) / fs
    stable = (rr[:-1] > 0.4) & (rr[:-1] < 1.6) & (np.abs(rr[1:] / rr[:-1] - 1) < 0.2)
    beats = np.stack([x[i - PRE: i + POST] for i in q[np.flatnonzero(stable) + 1]])
    t = np.median(beats, axis=0)
    return (t - t.mean()) / t.std()


def template_similarity(a: np.ndarray, b: np.ndarray, shift: int = SHIFT) -> float:
    """Máxima correlación de Pearson entre dos latidos con desfases de ±`shift`."""
    best = -1.0
    for s in range(-shift, shift + 1):
        aa, bb = (a[s:], b[:len(b) - s]) if s >= 0 else (a[:s], b[-s:])
        best = max(best, float(np.corrcoef(aa, bb)[0, 1]))
    return best


def signal_match(x: np.ndarray, y: np.ndarray, fs: float,
                 start_min: float = 60, dur_min: float = 5) -> tuple[int, float]:
    """Busca un tramo de `x` dentro de todo `y`.

    Devuelve (lag, r): y[t + lag] ~ x[t] con correlación normalizada r. Un r de
    1 indica la misma grabación; lag > 0 quiere decir que `y` empieza antes.
    """
    i0, n = int(start_min * 60 * fs), int(dur_min * 60 * fs)
    seg = x[i0: i0 + n]
    seg = (seg - seg.mean()) / seg.std()
    xc = fftconvolve(y, seg[::-1], mode="valid")          # sum(y[k:k+n] * seg)
    cs = np.concatenate([[0], np.cumsum(y)])
    cs2 = np.concatenate([[0], np.cumsum(y ** 2)])
    mu = (cs[n:] - cs[:-n]) / n
    sd = np.sqrt(np.maximum((cs2[n:] - cs2[:-n]) / n - mu ** 2, 1e-12))
    r = xc / (n * sd)
    k = int(np.argmax(r))
    return k - i0, float(r[k])


def find_duplicates(records: list[str], raw_dir: Path = RAW_DIR,
                    r_template: float = 0.99, r_signal: float = 0.99) -> pd.DataFrame:
    """Pares de `records` que son la misma grabación, con su desfase en segundos.

    Lee el ECG de todos los registros: tarda unos minutos.
    """
    templates, fs = {}, None
    for rec in records:
        ecg, fs = load_ecg(rec, raw_dir)
        templates[rec] = beat_template(ecg, load_qrs(rec, raw_dir), fs)
    rows = []
    for a, b in combinations(records, 2):
        rt = template_similarity(templates[a], templates[b])
        if rt < r_template:
            continue
        lag, rs = signal_match(load_ecg(a, raw_dir)[0], load_ecg(b, raw_dir)[0], fs)
        if rs >= r_signal:
            rows.append({"a": a, "b": b, "r_template": rt, "lag_s": lag / fs, "r_signal": rs})
    return pd.DataFrame(rows, columns=["a", "b", "r_template", "lag_s", "r_signal"])
