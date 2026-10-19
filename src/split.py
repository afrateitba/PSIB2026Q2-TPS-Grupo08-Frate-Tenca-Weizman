"""Partición 70/30 por registro, estratificada por categoría.  Esquema v2 §3.

Reglas:
- Se separa por registro: ningún sujeto aparece en desarrollo y test a la vez.
- Los registros con respiración real (RESP_RECORDS) van fijos a desarrollo,
  porque con ellos se ajustan y validan el EDR y el filtro de Wiener.
- Los registros de EXCLUDED quedan afuera.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import ALL_RECORDS, EXCLUDED, RAW_DIR, RESP_RECORDS, SEED, TEST_FRAC
from .data import load_apnea_labels


def category_from_labels(labels: np.ndarray) -> str:
    """Categoría por minutos de apnea: A >= 100, B 5-99, C < 5.

    Aproxima los criterios de Penzel et al. (2000), que además piden al menos
    una hora con IAH >= 10 (A) o >= 5 (B). Con solo minutos no se puede
    verificar esa condición; en el set x esta regla da 20 A / 5 B / 10 C,
    la misma proporción que el set de aprendizaje.
    """
    m = int((labels == 1).sum())
    if m >= 100:
        return "A"
    return "C" if m < 5 else "B"


def record_table(raw_dir=RAW_DIR) -> pd.DataFrame:
    """Una fila por registro incluido, con categoría y minutos de apnea."""
    rows = []
    for rec in ALL_RECORDS:
        if rec in EXCLUDED:
            continue
        lab = load_apnea_labels(rec, raw_dir)
        by_rule = category_from_labels(lab)
        rows.append({
            "record": rec,
            # Set de aprendizaje: la categoría viene en el nombre (a/b/c).
            "category": rec[0].upper() if rec[0] in "abc" else by_rule,
            "rule_category": by_rule,
            "n_minutes": int((lab >= 0).sum()),
            "apnea_minutes": int((lab == 1).sum()),
            "has_resp": rec in RESP_RECORDS,
        })
    return pd.DataFrame(rows)


def make_split(table: pd.DataFrame, test_frac: float = TEST_FRAC,
               seed: int = SEED) -> pd.DataFrame:
    """Agrega la columna 'set' ('dev' o 'test') con muestreo estratificado."""
    rng = np.random.default_rng(seed)
    out = table.copy()
    out["set"] = "dev"
    for cat, g in out.groupby("category", sort=True):
        n_test = int(round(test_frac * len(g)))
        pool = np.sort(g.loc[~g["has_resp"], "record"].to_numpy())
        if n_test > len(pool):
            raise ValueError(f"Categoría {cat}: no alcanzan registros sin respiración")
        chosen = rng.choice(pool, size=n_test, replace=False)
        out.loc[out["record"].isin(chosen), "set"] = "test"
    return out.sort_values("record").reset_index(drop=True)
