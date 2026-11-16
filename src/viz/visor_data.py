"""Datos del visor de registros (app/visor.py).

El visor no ajusta nada. Aplica a un registro el detector tal como quedó
fijado en desarrollo (docs/parametros_test.json) y prepara lo que se muestra:
- la noche: C de cada minuto con el umbral, la decisión, la confianza y las
  etiquetas;
- un minuto: el ECG con los picos R, la serie RR y la EDR en su ventana de
  240 s, sus espectros con la banda, y el cálculo de C paso a paso.

Mismo código que el pipeline: record_series y minute_table.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from ..config import ECG_FILTER, RAW_DIR, ROOT, SPLIT_CSV
from ..data import load_ecg
from ..features.build import record_series
from ..features.coupling import welch_spectra
from ..features.detector import (BAND, FS_U, WINDOW_S, c_score, confidence, evaluable, load_params,
                                 minute_table)
from ..preprocessing.filters import apply_zero_phase, design_bandpass

PARAMS_PATH = ROOT / "docs" / "parametros_test.json"


def registros_visibles(incluir_test: bool = False) -> pd.DataFrame:
    """Registros que muestra el visor: los de desarrollo y, solo si se pide, los de test.

    Test queda fuera por defecto: hasta la evaluación final no se miran ni sus
    señales ni sus etiquetas.
    """
    split = pd.read_csv(SPLIT_CSV)
    return split if incluir_test else split[split["set"] == "dev"].reset_index(drop=True)


def analizar_noche(rec: str, raw_dir: Path = RAW_DIR, params: dict | None = None) -> dict:
    """Corre el detector fijado sobre un registro y devuelve todo lo que muestra el visor.

    tabla: una fila por minuto con P_RR, EDR_noche, los dos términos de C, C,
    la decisión (1 apnea), la confianza, la etiqueta y si el minuto se evalúa.
    """
    p = params or load_params(PARAMS_PATH)
    s = record_series(rec, raw_dir)
    tab = minute_table(rec, raw_dir, series=s)
    pc = {"mu1": p["mu1"], "s1": p["s1"], "mu2": p["mu2"], "s2": p["s2"], "w": p["w"]}
    tab["termino_rr"] = (tab["P_RR"] - p["mu1"]) / p["s1"]
    tab["termino_edr"] = p["w"] * (tab["EDR_noche"] - p["mu2"]) / p["s2"]
    tab["C"] = c_score(tab, pc)
    tab["decision"] = (tab["C"] > p["umbral"]).astype(int)
    tab["confianza"] = confidence(tab["mov_rel"], tuple(p["cortes_confianza_mov_rel"]))
    tab["evaluado"] = evaluable(tab)
    ecg, fs = load_ecg(rec, raw_dir)
    return {"rec": rec, "tabla": tab, "params": p, "ecg": ecg,
            "ecg_f": apply_zero_phase(ecg, design_bandpass(fs, *ECG_FILTER)), "fs": fs,
            "t_r": s["t_r"], "t": s["t"], "rr": s["rr"], "edr": s["edr"]}


def resumen_noche(tab: pd.DataFrame) -> dict:
    """Medidas de la noche con los minutos evaluados (etiqueta y ≤ 20 % de RR corregidos)."""
    e = tab[tab["evaluado"]]
    y, d = e["label"].to_numpy(), e["decision"].to_numpy()
    n1, n0 = int((y == 1).sum()), int((y == 0).sum())
    out = {"minutos": len(tab), "evaluados": len(e),
           "apnea_real": 100 * y.mean() if len(e) else np.nan,
           "apnea_estimada": 100 * d.mean() if len(e) else np.nan,
           "sensibilidad": ((d == 1) & (y == 1)).sum() / n1 if n1 else np.nan,
           "especificidad": ((d == 0) & (y == 0)).sum() / n0 if n0 else np.nan,
           "exactitud": (d == y).mean() if len(e) else np.nan}
    out["confianza"] = e["confianza"].value_counts(normalize=True).reindex(["alta", "media", "baja"]).fillna(0).to_dict()
    return out


def ventana_minuto(an: dict, minuto: int) -> dict:
    """La ventana de 240 s centrada en `minuto`: RR, EDR, espectros de Welch y la banda.

    Recalcula los espectros con el mismo estimador que minute_table, así que
    P_RR y P_EDR coinciden con la tabla.
    """
    tab = an["tabla"]
    fila = tab[tab["minute"] == minuto]
    if fila.empty:
        raise ValueError(f"el minuto {minuto} no tiene una ventana completa de {WINDOW_S} s")
    t, n = an["t"], int(WINDOW_S * FS_U)
    inicio = 60 * minuto + 30 - WINDOW_S / 2
    i = int(round((inicio - t[0]) * FS_U))
    x, y = an["rr"][i:i + n], an["edr"][i:i + n]
    f, sxx, syy, _ = welch_spectra(x, y, FS_U, n // 2)
    banda = (f >= BAND[0] - 1e-9) & (f <= BAND[1] + 1e-9)
    return {"fila": fila.iloc[0], "t": t[i:i + n], "rr": x, "edr": y, "f": f, "s_rr": sxx, "s_edr": syy,
            "banda": banda, "P_RR": float(np.log10(sxx[banda].mean())),
            "P_EDR": float(np.log10(syy[banda].mean())), "inicio": inicio}


def ecg_minuto(an: dict, minuto: int) -> dict:
    """ECG crudo y filtrado de un minuto, con los picos R detectados en él."""
    fs = an["fs"]
    a, b = int(60 * minuto * fs), int(60 * (minuto + 1) * fs)
    t_r = an["t_r"][(an["t_r"] >= a / fs) & (an["t_r"] < b / fs)]
    idx = np.clip(np.rint(t_r * fs).astype(int), a, b - 1)
    return {"t": np.arange(a, b) / fs, "crudo": an["ecg"][a:b], "filtrado": an["ecg_f"][a:b],
            "t_r": t_r, "amp_r": an["ecg_f"][idx]}
