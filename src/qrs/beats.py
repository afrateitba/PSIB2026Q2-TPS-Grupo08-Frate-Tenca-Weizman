"""Latidos de un registro: detector propio (por defecto) o marcas de la base.

Las marcas .qrs de la base son automáticas y no están auditadas: en algunos
registros se saltean latidos. El detector propio (Pan-Tompkins con las
mejoras de notebooks/02_filtro_y_latidos.ipynb) deja menos RR imposibles que
las marcas en los registros de desarrollo y de test, y es el que se usa. Las
marcas quedan disponibles para comparar.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from ..config import ECG_FILTER, RAW_DIR
from ..data import load_ecg, load_qrs
from ..features.edr import qrs_reference
from ..preprocessing.filters import apply_zero_phase, design_bandpass
from .pan_tompkins import detect_r_peaks, r_peaks_from_marks, refine_peaks_parabolic
from .rr_clean import clean_rr

SOURCES = ("pt", "pt_clasico", "marks")


def record_beats(rec: str, source: str = "pt", raw_dir: Path = RAW_DIR,
                 filt: tuple = ECG_FILTER, refine: bool = True) -> dict:
    """Tiempos de los picos R (s) de un registro.

    source: "pt" (detector propio mejorado), "pt_clasico" (Pan-Tompkins sin
    las mejoras) o "marks" (marcas de la base). Devuelve t_r, samples
    (índices enteros, para calcular la EDR), source, fs y la fracción de RR
    corregidos (corr).
    """
    if source not in SOURCES:
        raise ValueError(f"fuente desconocida: {source} (opciones: {SOURCES})")
    ecg, fs = load_ecg(rec, raw_dir)
    x = apply_zero_phase(ecg, design_bandpass(fs, *filt))
    if source == "marks":
        qrs = load_qrs(rec, raw_dir)
        off, sign = qrs_reference(x, qrs, fs)
        t_r = r_peaks_from_marks(x, qrs, fs, off, sign, refine=refine)[0]
    else:
        k = detect_r_peaks(x, fs, improved=(source == "pt"))
        t_r = refine_peaks_parabolic(x, k)[0] / fs if refine else k / fs
    return {"t_r": t_r, "samples": np.unique(np.rint(t_r * fs).astype(int)), "source": source,
            "fs": fs, "corr": float(clean_rr(t_r)[2].mean())}
