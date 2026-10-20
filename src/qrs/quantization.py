"""Cuantización del tiempo del pico R a 100 Hz.  Esquema v2 §4.1.

A 100 Hz el pico R cae en una grilla de 10 ms. El refinamiento parabólico
(pan_tompkins.refine_peaks_parabolic) busca el vértice entre muestras. Para
medir si de verdad lo recupera, sin una referencia de mayor resolución, se
usa una prueba de dos fases: la misma señal se baja a fs/2 tomando las
muestras pares y las impares, así cada latido queda medido en dos grillas
corridas 1/fs. Sin refinar, los dos tiempos difieren alrededor de 1/fs; si
el refinamiento funciona, esa diferencia baja.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import butter

from ..preprocessing.filters import apply_zero_phase
from .pan_tompkins import refine_peaks_parabolic


def _peak_index(x: np.ndarray, centers: np.ndarray, h: int, sign: int) -> np.ndarray:
    return centers - h + np.argmax(sign * x[centers[:, None] + np.arange(-h, h + 1)], axis=1)


def two_phase_peaks(x: np.ndarray, marks: np.ndarray, fs: float, offset: int, sign: int,
                    band_ratio: float = 0.45, order: int = 3,
                    search: float = 0.03) -> pd.DataFrame:
    """Tiempo de cada pico R medido en las dos fases a fs/2, sin y con refinamiento.

    Antes de diezmar se aplica un pasabajos ida y vuelta con corte en
    `band_ratio` × fs/2: el mismo ancho de banda relativo a la frecuencia de
    muestreo que tiene el pipeline (45 Hz a 100 Hz). Devuelve una fila por
    marca con los tiempos en segundos del reloj original: "par" e "impar" (en
    la muestra entera) y "par_ref" e "impar_ref" (refinados). Si dos marcas
    caen en el mismo pico, queda una.
    """
    fs2 = fs / 2
    h = int(round(search * fs2))
    y = apply_zero_phase(x, butter(order, band_ratio * fs2, fs=fs, output="sos"))
    c = np.asarray(marks) + offset
    c = c[(c >= 2 * h + 2) & (c < len(x) - 2 * h - 2)]
    out = {}
    for p, name in ((0, "par"), (1, "impar")):
        xp = sign * y[p::2]
        k = _peak_index(xp, (c - p) // 2, h, 1)
        out[name] = (2 * k + p) / fs
        out[f"{name}_ref"] = (2 * refine_peaks_parabolic(xp, k)[0] + p) / fs
    return pd.DataFrame(out).drop_duplicates("par").reset_index(drop=True)
