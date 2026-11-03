"""Arma las series RR y EDR de un registro y sus tablas de features por minuto.

Une los pasos del pipeline para no repetirlos en cada notebook:
ECG -> pasabanda -> picos R refinados -> RR limpio  \
                                                    -> remuestreo a 2 Hz -> coherencia por minuto
ECG -> EDR (área del QRS, deriva o combinado; E1)   /
RR limpio -> Lomb y HRV temporal por minuto (referencia de H2)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ECG_FILTER, RAW_DIR
from ..data import load_apnea_labels, load_ecg, load_qrs
from ..preprocessing.filters import apply_zero_phase, design_bandpass
from ..qrs.pan_tompkins import r_peaks_from_marks
from ..qrs.rr_clean import clean_rr, minute_quality
from .coupling import coherence_bands, resample_uniform
from .edr import EDR_METHODS, compute_edr, qrs_reference
from .hrv_time import hrv_time_features
from .lomb import HRV_BANDS, band_powers, lomb_psd
from .windows import centered_windows

ESTIMATORS = ("welch3", "welch7", "multitaper")


def record_series(rec: str, raw_dir: Path = RAW_DIR, fs_u: float = 2.0,
                  edr_method: str = "area", edr_methods: tuple = (),
                  filt: tuple = ECG_FILTER, refine: bool = True) -> dict:
    """RR limpio y EDR de un registro, remuestreados a `fs_u` en una grilla común.

    Devuelve t, rr, edr (el de `edr_method`), edrs ({método: serie} para
    `edr_method` y `edr_methods`), y t_rr, rr_beats, corrected (RR por latido)
    para la HRV y la calidad por minuto. Métodos de EDR: los de
    edr.compute_edr, y "combined": promedio del área y la deriva, cada una
    estandarizada sobre la noche (sin etiquetas). `filt`: pasabanda del ECG
    (corte bajo, corte alto, orden). `refine`: refinamiento parabólico del
    pico R (4.1).
    """
    ecg, fs = load_ecg(rec, raw_dir)
    qrs = load_qrs(rec, raw_dir)
    x = apply_zero_phase(ecg, design_bandpass(fs, *filt))
    off, sign = qrs_reference(x, qrs, fs)
    t_r, _ = r_peaks_from_marks(x, qrs, fs, off, sign, refine=refine)
    t_rr, rr, corrected = clean_rr(t_r)
    methods = list(dict.fromkeys((edr_method,) + tuple(edr_methods)))
    base = {m for m in methods if m in EDR_METHODS}
    if "combined" in methods:
        base |= {"area", "baseline"}
    grids = {"rr": resample_uniform(t_rr, rr, fs_u)}
    for m in sorted(base):
        grids[m] = resample_uniform(*compute_edr(ecg, qrs, fs, m, filt), fs_u)
    t0 = max(g[0][0] for g in grids.values())
    t1 = min(g[0][-1] for g in grids.values())
    cut = {k: g[1][(g[0] >= t0) & (g[0] <= t1)] for k, g in grids.items()}
    t = grids["rr"][0][(grids["rr"][0] >= t0) & (grids["rr"][0] <= t1)]
    z = lambda v: (v - v.mean()) / v.std()
    edrs = {m: cut[m] for m in methods if m in EDR_METHODS}
    if "combined" in methods:
        edrs["combined"] = (z(cut["area"]) + z(cut["baseline"])) / 2
    return {"t": t, "rr": cut["rr"], "edr": edrs[edr_method], "edrs": edrs, "fs": fs_u,
            "sign": sign, "t_rr": t_rr, "rr_beats": rr, "corrected": corrected,
            "edr_method": edr_method}


def minute_coupling(t: np.ndarray, x: np.ndarray, y: np.ndarray, fs: float,
                    n_minutes: int, width_s: float, bands: dict,
                    estimator: str = "welch3") -> pd.DataFrame:
    """Coherencia x-y por banda en una ventana de `width_s` s centrada en cada minuto.

    `estimator`: "welch3" (3 segmentos de media ventana, 50 % de solapamiento),
    "welch7" (7 segmentos de un cuarto de ventana) o "multitaper" (NW = 2).
    Los minutos cuya ventana no entra completa en la grilla t no aparecen. Si la
    ventana tiene muestras no finitas (la respiración real las tiene), sus
    valores quedan en NaN en lugar de rellenar datos.
    """
    if estimator not in ESTIMATORS:
        raise ValueError(f"estimador desconocido: {estimator} (opciones: {ESTIMATORS})")
    n = int(round(width_s * fs))
    nperseg = n // 4 if estimator == "welch7" else n // 2
    est = "multitaper" if estimator == "multitaper" else "welch"
    minutes, t0 = centered_windows(n_minutes, width_s, t[0], t[-1] + 1 / fs)
    nan = {f"{k}_{b}": np.nan for b in bands for k in ("coh", "xp", "cw", "px", "py")}
    rows = []
    for m, s in zip(minutes, t0):
        i = int(round((s - t[0]) * fs))
        xw, yw = x[i:i + n], y[i:i + n]
        ok = np.isfinite(xw).all() and np.isfinite(yw).all()
        rows.append({"minute": m, **(coherence_bands(xw, yw, fs, nperseg, bands, est) if ok else nan)})
    return pd.DataFrame(rows)


def _attach(tab: pd.DataFrame, rec: str, s: dict, raw_dir: Path) -> pd.DataFrame:
    labels = load_apnea_labels(rec, raw_dir)
    tab.insert(0, "record", rec)
    tab["label"] = labels[tab["minute"]]
    tab["corrected"] = minute_quality(s["t_rr"], s["corrected"], len(labels))[tab["minute"]]
    return tab


def record_minute_table(rec: str, width_s: float, bands: dict,
                        raw_dir: Path = RAW_DIR, series: dict | None = None,
                        edr_method: str = "area", estimator: str = "welch3",
                        filt: tuple = ECG_FILTER) -> pd.DataFrame:
    """Tabla por minuto de un registro: acoplamiento RR-EDR, etiqueta y calidad.

    `series` permite reutilizar record_series() al probar varias ventanas.
    """
    s = series or record_series(rec, raw_dir, edr_method=edr_method, filt=filt)
    edr = s["edrs"][edr_method] if "edrs" in s else s["edr"]
    n_min = len(load_apnea_labels(rec, raw_dir))
    tab = minute_coupling(s["t"], s["rr"], edr, s["fs"], n_min, width_s, bands, estimator)
    return _attach(tab, rec, s, raw_dir)


def minute_hrv(t_rr: np.ndarray, rr: np.ndarray, n_minutes: int, width_s: float,
               f: np.ndarray | None = None, bands: dict = HRV_BANDS) -> pd.DataFrame:
    """HRV por minuto con la misma ventana centrada que el acoplamiento.

    Lomb sobre los RR que caen en la ventana (sin remuestrear) y features
    temporales. Ventanas con menos de 20 latidos quedan en NaN.
    """
    f = np.arange(0.005, 0.5, 0.0025) if f is None else f
    minutes, t0 = centered_windows(n_minutes, width_s, t_rr[0], t_rr[-1])
    rows = []
    for m, s in zip(minutes, t0):
        sel = (t_rr >= s) & (t_rr < s + width_s)
        if sel.sum() < 20:
            rows.append({"minute": m})
            continue
        spec = band_powers(f, lomb_psd(t_rr[sel], rr[sel], f), bands)
        rows.append({"minute": m, **spec, **hrv_time_features(rr[sel])})
    return pd.DataFrame(rows)


def record_hrv_table(rec: str, width_s: float, raw_dir: Path = RAW_DIR,
                     series: dict | None = None) -> pd.DataFrame:
    """Tabla por minuto de HRV de un registro, con etiqueta y calidad."""
    s = series or record_series(rec, raw_dir)
    n_min = len(load_apnea_labels(rec, raw_dir))
    return _attach(minute_hrv(s["t_rr"], s["rr_beats"], n_min, width_s), rec, s, raw_dir)


def record_feature_tables(rec: str, widths: tuple, estimators: tuple, edr_methods: tuple,
                          bands: dict, raw_dir: Path = RAW_DIR,
                          refine: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Todas las tablas de E3a y E4 de un registro: (acoplamiento, HRV), en formato largo.

    Calcula las series una sola vez. Está a nivel de módulo para poder
    repartir los registros entre procesos.
    """
    s = record_series(rec, raw_dir, edr_method=edr_methods[0], edr_methods=edr_methods, refine=refine)
    coup = [record_minute_table(rec, w, bands, raw_dir, series=s, edr_method=m, estimator=e)
            .assign(edr=m, window=w, estimator=e)
            for m in edr_methods for w in widths for e in estimators]
    hrv = [record_hrv_table(rec, w, raw_dir, series=s).assign(window=w) for w in widths]
    return pd.concat(coup, ignore_index=True), pd.concat(hrv, ignore_index=True)


# --- Política de calidad: notebook 10 ---
def attach_window_quality(tab, rec, width_s=240.0,
                          raw_dir=RAW_DIR, exclude_lost=False):
    """Adjunta calidad del ECG a una tabla por minuto.

    Por defecto conserva todas las filas. exclude_lost=True aplica
    la regla candidata evaluada y no adoptada en el notebook 10.
    No modifica F ni aplica la regla de RR corregidos.
    """
    from ..data import load_ecg_digital, load_header
    from ..preprocessing.quality import window_signal_quality

    d = load_ecg_digital(rec, raw_dir)
    header = load_header(rec, raw_dir)
    calidad = window_signal_quality(
        d, header["fs"], header["bits"],
        tab["minute"].to_numpy(),
        width_s=width_s,
        adc_zero=header["cero"],
    )

    out = tab.copy()
    for col in ("ventana_completa", "segundos_perdidos", "sin_perdida"):
        out[col] = calidad[col].to_numpy()

    if exclude_lost:
        out = out.loc[out["sin_perdida"]].copy()
    return out
