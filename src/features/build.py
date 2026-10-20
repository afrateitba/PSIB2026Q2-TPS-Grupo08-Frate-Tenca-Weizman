"""Arma las series RR y EDR de un registro y su tabla de features por minuto.

Une los pasos del pipeline para no repetirlos en cada notebook:
ECG -> pasabanda -> picos R refinados -> RR limpio  \
                                                    -> remuestreo a 2 Hz -> coherencia por minuto
ECG -> EDR (área del QRS o deriva; ver E1)          /
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import RAW_DIR
from ..data import load_apnea_labels, load_ecg, load_qrs
from ..preprocessing.filters import apply_zero_phase, design_bandpass
from ..qrs.pan_tompkins import r_peaks_from_marks
from ..qrs.rr_clean import clean_rr, minute_quality
from .coupling import coherence_bands, resample_uniform
from .edr import compute_edr, qrs_reference
from .windows import centered_windows


def record_series(rec: str, raw_dir: Path = RAW_DIR, fs_u: float = 2.0,
                  edr_method: str = "area") -> dict:
    """RR limpio y EDR de un registro, remuestreados a `fs_u` en una grilla común.

    Devuelve t, rr, edr (uniformes), y t_rr, corrected (RR original) para
    medir la calidad por minuto. `edr_method`: ver edr.compute_edr.
    """
    ecg, fs = load_ecg(rec, raw_dir)
    qrs = load_qrs(rec, raw_dir)
    x = apply_zero_phase(ecg, design_bandpass(fs, 0.5, 40, 2))
    off, sign = qrs_reference(x, qrs, fs)
    t_r, _ = r_peaks_from_marks(x, qrs, fs, off, sign)
    t_rr, rr, corrected = clean_rr(t_r)
    t_e, edr = compute_edr(ecg, qrs, fs, edr_method)
    tu_rr, rr_u = resample_uniform(t_rr, rr, fs_u)
    tu_e, edr_u = resample_uniform(t_e, edr, fs_u)
    t0, t1 = max(tu_rr[0], tu_e[0]), min(tu_rr[-1], tu_e[-1])
    a, b = (tu_rr >= t0) & (tu_rr <= t1), (tu_e >= t0) & (tu_e <= t1)
    return {"t": tu_rr[a], "rr": rr_u[a], "edr": edr_u[b], "fs": fs_u, "sign": sign,
            "t_rr": t_rr, "corrected": corrected, "edr_method": edr_method}


def minute_coupling(t: np.ndarray, x: np.ndarray, y: np.ndarray, fs: float,
                    n_minutes: int, width_s: float, bands: dict) -> pd.DataFrame:
    """Coherencia x-y por banda en una ventana de `width_s` s centrada en cada minuto.

    Welch con 3 segmentos (nperseg = la mitad de la ventana, 50 % de solapamiento).
    Los minutos cuya ventana no entra completa en la grilla t no aparecen. Si la
    ventana tiene muestras no finitas (la respiración real las tiene), sus
    valores quedan en NaN en lugar de rellenar datos.
    """
    n = int(round(width_s * fs))
    minutes, t0 = centered_windows(n_minutes, width_s, t[0], t[-1] + 1 / fs)
    nan = {f"{k}_{b}": np.nan for b in bands for k in ("coh", "xp")}
    rows = []
    for m, s in zip(minutes, t0):
        i = int(round((s - t[0]) * fs))
        xw, yw = x[i:i + n], y[i:i + n]
        ok = np.isfinite(xw).all() and np.isfinite(yw).all()
        rows.append({"minute": m, **(coherence_bands(xw, yw, fs, n // 2, bands) if ok else nan)})
    return pd.DataFrame(rows)


def record_minute_table(rec: str, width_s: float, bands: dict,
                        raw_dir: Path = RAW_DIR, series: dict | None = None,
                        edr_method: str = "area") -> pd.DataFrame:
    """Tabla por minuto de un registro: features de acoplamiento, etiqueta y calidad.

    `series` permite reutilizar record_series() al probar varias ventanas.
    """
    s = series or record_series(rec, raw_dir, edr_method=edr_method)
    labels = load_apnea_labels(rec, raw_dir)
    tab = minute_coupling(s["t"], s["rr"], s["edr"], s["fs"], len(labels), width_s, bands)
    tab.insert(0, "record", rec)
    tab["label"] = labels[tab["minute"]]
    tab["corrected"] = minute_quality(s["t_rr"], s["corrected"], len(labels))[tab["minute"]]
    return tab
