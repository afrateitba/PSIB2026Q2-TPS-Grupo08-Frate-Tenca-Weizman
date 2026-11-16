"""Detector de apnea por minuto: feature combinada C, umbral y confianza.

Hipótesis y definiciones: docs/objetivos_hipotesis.md. Justificación con datos:
notebooks/04_feature_y_detector.ipynb.

Para cada minuto m (ventana de 240 s centrada en él):
- P_RR(m), P_EDR(m): log10 de la potencia de la serie RR y de la EDR en
  0,01-0,05 Hz (Welch, 3 segmentos de 120 s, Hann, 50 % de solapamiento).
- F(m): log10 del módulo del espectro cruzado RR-EDR en la misma banda
  (feature de la primera versión; se conserva para comparar).
- mov(m): varianza del ECG crudo por debajo de 0,5 Hz en la ventana
  (movimiento); mov_rel es su log10 respecto de la mediana del registro.

La feature combinada C usa cada señal en lo que mide bien:
    C(m) = (P_RR(m) - mu1) / s1 + w * (mediana_noche(P_EDR) - mu2) / s2
El primer término ubica la apnea dentro de la noche (es el que cambia de un
minuto a otro); el segundo es el mismo para toda la noche y dice cuánta
apnea tiene, corrigiendo el nivel general del RR, que cambia entre personas.
La mediana no usa etiquetas. Se probó también centrar el RR en su noche
(restarle su mediana) y no mejoró (notebook 04).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import butter, sosfiltfilt

from ..config import RAW_DIR
from ..data import load_apnea_labels, load_ecg
from ..qrs.rr_clean import minute_quality
from .build import record_series
from .coupling import welch_spectra
from .windows import centered_windows

BAND = (0.01, 0.05)
WINDOW_S = 240
FS_U = 2.0
CONFIANZA = ("alta", "media", "baja")


def minute_table(rec: str, raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Una fila por minuto con ventana completa: etiqueta, calidad, P_RR, P_EDR, F y movimiento.

    label: 1 apnea, 0 normal, -1 sin etiqueta. q: fracción de RR corregidos
    en el minuto. No usa las etiquetas para nada más que copiarlas.
    """
    s = record_series(rec, raw_dir)
    lab = load_apnea_labels(rec, raw_dir)
    q = minute_quality(s["t_rr"], s["corrected"], len(lab))
    ecg, fs = load_ecg(rec, raw_dir)
    lento = sosfiltfilt(butter(2, 0.5, "low", fs=fs, output="sos"), ecg)
    t = s["t"]
    minutos, inicios = centered_windows(len(lab), WINDOW_S, t[0], t[-1] + 1 / FS_U)
    n = int(WINDOW_S * FS_U)
    filas = []
    for m, a in zip(minutos, inicios):
        i = int(round((a - t[0]) * FS_U))
        x, y = s["rr"][i:i + n], s["edr"][i:i + n]
        if len(x) < n:
            continue
        f, sxx, syy, sxy = welch_spectra(x, y, FS_U, n // 2)
        b = (f >= BAND[0] - 1e-9) & (f <= BAND[1] + 1e-9)
        filas.append({"record": rec, "minute": int(m), "label": int(lab[m]), "q": float(q[m]),
                      "P_RR": float(np.log10(sxx[b].mean())), "P_EDR": float(np.log10(syy[b].mean())),
                      "F": float(np.log10(np.abs(sxy[b]).mean())),
                      "mov": float(np.var(lento[int(a * fs):int((a + WINDOW_S) * fs)])),
                      "escala_qrs": float(s["edr_scale"])})
    return add_night_terms(pd.DataFrame(filas))


def add_night_terms(tab: pd.DataFrame) -> pd.DataFrame:
    """Agrega los términos de la noche, calculados con todos los minutos de cada registro.

    RR_dev = P_RR - mediana_noche(P_RR); EDR_noche = mediana_noche(P_EDR);
    mov_rel = log10(mov / mediana_noche(mov)).
    """
    out = tab.copy()
    g = out.groupby("record")
    out["RR_dev"] = out["P_RR"] - g["P_RR"].transform("median")
    out["EDR_noche"] = g["P_EDR"].transform("median")
    out["mov_rel"] = np.log10(out["mov"] / g["mov"].transform("median"))
    return out


def evaluable(tab: pd.DataFrame) -> pd.Series:
    """Minutos que se evalúan: con etiqueta y con 20 % o menos de RR corregidos."""
    return (tab["label"] >= 0) & (tab["q"] <= 0.2)


def fit_c(tab: pd.DataFrame, w: float, rr: str = "P_RR") -> dict:
    """Parámetros de estandarización de C con los minutos evaluables de `tab`.

    `rr`: columna del término del RR ("P_RR"; "RR_dev" para la variante
    centrada en la noche, que se usa solo para comparar).
    """
    e = tab[evaluable(tab)]
    return {"mu1": float(e[rr].mean()), "s1": float(e[rr].std()), "mu2": float(e["EDR_noche"].mean()),
            "s2": float(e["EDR_noche"].std()), "w": float(w), "rr": rr}


def c_score(tab: pd.DataFrame, p: dict) -> pd.Series:
    """C de cada minuto con los parámetros `p` (los de fit_c)."""
    rr = p.get("rr", "P_RR")
    return (tab[rr] - p["mu1"]) / p["s1"] + p["w"] * (tab["EDR_noche"] - p["mu2"]) / p["s2"]


def youden_threshold(x: np.ndarray, y: np.ndarray) -> float:
    """Umbral que maximiza sensibilidad + especificidad − 1 (x > umbral es apnea)."""
    x, y = np.asarray(x, float), np.asarray(y, int)
    o = np.argsort(-x)
    xs, ys = x[o], y[o]
    tpr = np.cumsum(ys) / ys.sum()
    fpr = np.cumsum(1 - ys) / (1 - ys).sum()
    k = int(np.argmax(tpr - fpr))
    return float((xs[k] + xs[min(k + 1, len(xs) - 1)]) / 2)


def confidence(mov_rel: pd.Series, cortes: tuple) -> pd.Series:
    """Confianza de la decisión según el movimiento: alta, media o baja.

    `cortes` = (c1, c2) en unidades de mov_rel, fijados en desarrollo.
    """
    return pd.cut(mov_rel, [-np.inf, cortes[0], cortes[1], np.inf], labels=list(CONFIANZA)).astype(str)


def save_params(path: Path, params: dict) -> None:
    """Guarda los parámetros fijados en desarrollo (los lee el notebook de test)."""
    Path(path).write_text(json.dumps(params, indent=2, ensure_ascii=False))


def load_params(path: Path) -> dict:
    return json.loads(Path(path).read_text())
