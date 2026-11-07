"""Diagnóstico de errores del detector, minuto a minuto.  Notebook 14.

Descriptivo: no elige ni cambia nada del pipeline. Trabaja sobre las
predicciones de los sujetos de afuera de la validación anidada (notebook 12)
y sobre las etiquetas completas de cada noche.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .metrics import category_from_minutes
from ..stats.compare import pooled_auc


def distance_to_other(labels) -> np.ndarray:
    """Para cada minuto, la distancia (en minutos) al minuto más cercano con la
    otra etiqueta. Para un minuto normal es la distancia a la apnea más
    cercana; para uno con apnea, 1 si está en el borde del episodio. Los
    minutos sin etiqueta (-1) no cuentan como otra etiqueta y reciben NaN.
    Si en la noche no hay minutos con la otra etiqueta, la distancia es infinita.
    """
    y = np.asarray(labels)
    pos = {v: np.flatnonzero(y == v) for v in (0, 1)}
    out = np.full(len(y), np.nan)
    for v, other in ((0, 1), (1, 0)):
        idx = pos[v]
        if len(idx) == 0:
            continue
        p = pos[other]
        if len(p) == 0:
            out[idx] = np.inf
            continue
        j = np.clip(np.searchsorted(p, idx), 1, len(p) - 1) if len(p) > 1 else np.zeros(len(idx), int)
        d = np.abs(p[j] - idx)
        if len(p) > 1:
            d = np.minimum(d, np.abs(p[j - 1] - idx))
        out[idx] = d
    return out


def episode_lengths(labels) -> np.ndarray:
    """Para cada minuto con apnea, el largo del episodio (minutos seguidos con
    apnea) que lo contiene; NaN para los demás."""
    y = np.asarray(labels) == 1
    out = np.full(len(y), np.nan)
    edges = np.diff(np.r_[0, y.astype(np.int8), 0])
    for s, e in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
        out[s:e] = e - s
    return out


def error_table(pred: pd.DataFrame, labels_by_record: dict, fam: str = "F") -> pd.DataFrame:
    """Una fila por minuto evaluado: etiqueta, decisión, tipo (VP, FP, FN, VN),
    distancia a la otra etiqueta, largo del episodio y categoría real de la
    noche (minutos anotados sobre los minutos evaluados, como en el plan).

    `pred` es la salida de nested_cv (indexada por record y minute) y
    `labels_by_record` tiene las etiquetas completas de cada noche.
    """
    rows = []
    for rec, g in pred.groupby(level="record", sort=False):
        lab = np.asarray(labels_by_record[rec])
        m = g.index.get_level_values("minute").to_numpy()
        rows.append(pd.DataFrame({"distancia": distance_to_other(lab)[m],
                                  "largo_episodio": episode_lengths(lab)[m]}, index=g.index))
    t = pd.concat(rows).loc[pred.index]
    t.insert(0, "label", pred["label"].to_numpy(int))
    t.insert(1, "pred", pred[f"pred_{fam}"].to_numpy(int))
    t["tipo"] = np.select([(t.label == 1) & (t.pred == 1), (t.label == 0) & (t.pred == 1),
                           (t.label == 1) & (t.pred == 0)], ["VP", "FP", "FN"], "VN")
    cat = t.groupby(level="record")["label"].sum().map(category_from_minutes)
    t["categoria"] = cat.reindex(t.index.get_level_values("record")).to_numpy()
    return t


def subject_scores(pred: pd.DataFrame, subject_of: pd.Series, fam: str = "F") -> pd.DataFrame:
    """Por sujeto: minutos, % con apnea, área bajo la curva dentro del sujeto
    (NaN si le falta una clase), sensibilidad, especificidad y exactitud."""
    subj = subject_of.loc[pred.index.get_level_values("record")].to_numpy()
    rows = []
    for s in pd.unique(subj):
        m = subj == s
        y, p = pred["label"].to_numpy(int)[m], pred[f"pred_{fam}"].to_numpy(int)[m]
        sc = pred[f"score_{fam}"].to_numpy(float)[m]
        both = 0 < y.sum() < len(y)
        rows.append({"subject": s, "minutos": int(m.sum()), "apnea": y.mean(),
                     "auc": pooled_auc(sc, y) if both else np.nan,
                     "sensibilidad": p[y == 1].mean() if (y == 1).any() else np.nan,
                     "especificidad": 1 - p[y == 0].mean() if (y == 0).any() else np.nan,
                     "exactitud": (p == y).mean()})
    return pd.DataFrame(rows).set_index("subject")
