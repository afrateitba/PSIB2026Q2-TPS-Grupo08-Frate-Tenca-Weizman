"""Latidos de un registro: marcas de la base, detector propio o el mejor de los dos.

Las marcas .qrs de la base son automáticas y no están auditadas. En algunos
registros se saltean latidos (el RR aparece al doble); el detector propio
(Pan-Tompkins) los encuentra, pero en otros marca también la onda T. Los dos
errores dejan intervalos RR imposibles, que la limpieza del RR corrige: un
latido perdido deja un RR largo y uno de más, dos cortos. Por eso la fracción
de RR corregidos mide los errores de detección sin usar etiquetas, y con
source="auto" se usa, en cada registro, la fuente que deja menos RR
corregidos. Se justifica en notebooks/02_filtro_y_latidos.ipynb.
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

SOURCES = ("marks", "pt", "auto")


def _peaks_pt(x: np.ndarray, fs: float, refine: bool) -> np.ndarray:
    k = detect_r_peaks(x, fs)
    if not refine:
        return k / fs
    return refine_peaks_parabolic(x, k)[0] / fs


def record_beats(rec: str, source: str = "auto", raw_dir: Path = RAW_DIR,
                 filt: tuple = ECG_FILTER, refine: bool = True) -> dict:
    """Tiempos de los picos R (s) de un registro y la fuente usada.

    source: "marks" (marcas de la base), "pt" (detector propio) o "auto" (la
    de menos RR corregidos). Devuelve t_r, samples (índices enteros, para
    calcular la EDR), source y la fracción de RR corregidos de cada fuente
    calculada (corr_marks, corr_pt).
    """
    if source not in SOURCES:
        raise ValueError(f"fuente desconocida: {source} (opciones: {SOURCES})")
    ecg, fs = load_ecg(rec, raw_dir)
    x = apply_zero_phase(ecg, design_bandpass(fs, *filt))
    out = {}
    if source in ("marks", "auto"):
        qrs = load_qrs(rec, raw_dir)
        off, sign = qrs_reference(x, qrs, fs)
        out["marks"] = r_peaks_from_marks(x, qrs, fs, off, sign, refine=refine)[0]
    if source in ("pt", "auto"):
        out["pt"] = _peaks_pt(x, fs, refine)
    corr = {k: float(clean_rr(t)[2].mean()) for k, t in out.items()}
    chosen = min(corr, key=corr.get) if source == "auto" else source
    t_r = out[chosen]
    return {"t_r": t_r, "samples": np.unique(np.rint(t_r * fs).astype(int)), "source": chosen,
            "fs": fs, **{f"corr_{k}": v for k, v in corr.items()}}
