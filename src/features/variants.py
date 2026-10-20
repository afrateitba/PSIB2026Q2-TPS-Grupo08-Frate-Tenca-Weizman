"""Candidatas de E3a (acoplamiento) y E4 (HRV) como columnas de una tabla ancha.

Cada candidata es una forma de convertir las columnas por minuto (coherencia,
potencia cruzada, HRV) en un único número F. La tabla ancha tiene un renglón
por (registro, minuto) y una columna por candidata; `meta` describe cada una y
su orden de simplicidad para desempatar (fijado antes de correr E3a).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .postprocess import NORMALIZATIONS, normalize, smooth

BANDS = {"cpc_l": (0.01, 0.10), "cpc_r": (0.10, 0.40),
         "v2_l": (0.01, 0.15), "v2_r": (0.15, 0.40), "ap_l": (0.01, 0.05)}
BAND_CONFIGS = {"CPC": ("cpc_l", "cpc_r"), "v2": ("v2_l", "v2_r"), "apnea": ("ap_l", "v2_r")}

_log = lambda v: np.log(np.maximum(v, 1e-12))
FORMS = {
    "solo lenta":       lambda t, lo, hi: t[f"coh_{lo}"],
    # Control agregado después de la primera corrida de E3a: ¿aporta la
    # coherencia algo más que la potencia que comparten RR y EDR?
    "potencia sola":    lambda t, lo, hi: _log(t[f"xp_{lo}"]),
    "diferencia":       lambda t, lo, hi: t[f"coh_{lo}"] - t[f"coh_{hi}"],
    "log-cociente":     lambda t, lo, hi: _log(t[f"coh_{lo}"]) - _log(t[f"coh_{hi}"]),
    "lenta × potencia": lambda t, lo, hi: _log(t[f"coh_{lo}"] * t[f"xp_{lo}"]),
    "producto":         lambda t, lo, hi: _log(t[f"coh_{lo}"] * t[f"xp_{lo}"])
                                          - _log(t[f"coh_{hi}"] * t[f"xp_{hi}"]),
    "ponderada":        lambda t, lo, hi: t[f"cw_{lo}"],
}
HRV_FEATURES = ["mean_rr", "sdnn", "rmssd", "pnn50", "apnea", "vlf", "lf", "hf", "total", "lf_hf"]

# Orden de simplicidad (menor = más simple), en el orden de prioridad del desempate.
ORDER = {
    "estimador": {"welch3": 0, "welch7": 1, "multitaper": 2},
    "forma": {f: i for i, f in enumerate(FORMS)},
    "bandas": {"CPC": 0, "v2": 1, "apnea": 2},
    "edr": {"baseline": 0, "area": 1, "combined": 2},
    "hrv": {f: i for i, f in enumerate(HRV_FEATURES)},
    "normalizacion": {"none": 0, "baseline": 1, "zscore": 2},
}


def coupling_variants(tab: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(ancha, meta) a partir de la tabla larga de acoplamiento.

    `tab` tiene record, minute, edr, window, estimator y las columnas coh_/xp_/cw_
    de BANDS. Una candidata por EDR x ventana x estimador x bandas x forma.
    """
    cols, meta = {}, []
    for (edr, w, est), g in tab.groupby(["edr", "window", "estimator"], sort=True):
        g = g.set_index(["record", "minute"])
        for band, (lo, hi) in BAND_CONFIGS.items():
            for form, fn in FORMS.items():
                name = f"{edr}|{int(w)}s|{est}|{band}|{form}"
                cols[name] = fn(g, lo, hi)
                meta.append({"variante": name, "edr": edr, "ventana_s": int(w), "estimador": est,
                             "bandas": band, "forma": form,
                             "complejidad": (ORDER["estimador"][est], ORDER["forma"][form], int(w),
                                             ORDER["bandas"][band], ORDER["edr"][edr])})
    return pd.DataFrame(cols), pd.DataFrame(meta).set_index("variante")


def postprocess_variants(wide: pd.DataFrame, meta: pd.DataFrame,
                         norms: tuple = NORMALIZATIONS, ks: tuple = (1, 3, 5)
                         ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica a cada candidata todas las combinaciones de normalización y suavizado (E3b).

    `wide` está indexada por (record, minute) y tiene que incluir todos los
    minutos de cada noche: la normalización y el suavizado usan la noche
    completa, y recién después se filtran los minutos a evaluar. La
    complejidad nueva antepone (normalización, suavizado) a la de la candidata.
    """
    rec = pd.Series(wide.index.get_level_values("record"), index=wide.index)
    minute = pd.Series(wide.index.get_level_values("minute"), index=wide.index)
    cols, rows = {}, []
    for v in wide.columns:
        for n in norms:
            z = normalize(wide[v], rec, n)
            for k in ks:
                name = f"{v}|{n}|k{k}"
                cols[name] = smooth(z, rec, minute, k)
                rows.append({"variante": name, "base": v, "normalizacion": n, "suavizado": k,
                             "complejidad": (ORDER["normalizacion"][n], k) + tuple(meta.loc[v, "complejidad"])})
    return pd.DataFrame(cols, index=wide.index), pd.DataFrame(rows).set_index("variante")


def hrv_variants(tab: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(ancha, meta) de las features de HRV: una por ventana x feature."""
    cols, meta = {}, []
    for w, g in tab.groupby("window", sort=True):
        g = g.set_index(["record", "minute"])
        for feat in HRV_FEATURES:
            name = f"hrv|{int(w)}s|{feat}"
            cols[name] = g[feat]
            meta.append({"variante": name, "ventana_s": int(w), "feature": feat,
                         "complejidad": (ORDER["hrv"][feat], int(w))})
    return pd.DataFrame(cols), pd.DataFrame(meta).set_index("variante")
