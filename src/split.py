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

from .config import (ALL_RECORDS, EXCLUDED, RAW_DIR, RESP_RECORDS, SEED,
                     SUBJECT_ALIASES, TEST_FRAC)
from .data import load_apnea_labels, load_record_info

PROFILE = ["age", "sex", "height_cm", "weight_kg"]


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


def assign_subjects(info: pd.DataFrame,
                    aliases: dict = SUBJECT_ALIASES) -> pd.Series:
    """Sujeto de cada registro ('S01', 'S02', ...), indexado por registro.

    PhysioNet no dice qué registros son del mismo sujeto. Se infiere así:
    1. Mismo perfil exacto (edad, sexo, altura, peso) -> mismo sujeto. Que
       coincidan los cuatro valores por azar es muy improbable, y varios de
       estos grupos tienen además el mismo AI/HI.
    2. Cada registro de `aliases` toma el perfil de su destino (c06 -> c05).
    Ante la duda conviene agrupar: juntar de más solo cuesta balance en la
    partición; separar a una misma persona filtra información al test.
    Los sujetos se numeran por orden de su primer registro.
    """
    key = info.set_index("record")[PROFILE].astype(str).agg(" ".join, axis=1)
    for rec, target in aliases.items():
        key[rec] = key[target]
    first = key.index.to_series().groupby(key).min().sort_values()
    ids = {k: f"S{i:02d}" for i, k in enumerate(first.index, 1)}
    return key.map(ids).rename("subject")


def record_table(raw_dir=RAW_DIR) -> pd.DataFrame:
    """Una fila por registro incluido, con categoría, minutos de apnea y sujeto."""
    subjects = assign_subjects(load_record_info(raw_dir))
    rows = []
    for rec in ALL_RECORDS:
        if rec in EXCLUDED:
            continue
        lab = load_apnea_labels(rec, raw_dir)
        by_rule = category_from_labels(lab)
        rows.append({
            "record": rec,
            "subject": subjects[rec],
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
