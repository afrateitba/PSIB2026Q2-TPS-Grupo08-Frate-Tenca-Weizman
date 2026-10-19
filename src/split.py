"""Partición 70/30 por sujeto, estratificada por categoría.  Esquema v2 §3.

Una partición es válida si cumple las cuatro condiciones:
1. Sujetos enteros: todos los registros de un sujeto (assign_subjects) van al
   mismo conjunto, para que el test sea gente que el método no vio.
2. Los sujetos con algún registro con respiración real (RESP_RECORDS) van a
   desarrollo, porque con ellos se ajustan y validan el EDR y el Wiener.
3. Cuotas exactas: test lleva round(TEST_FRAC * n) registros de cada categoría.
4. Balance de minutos: la fracción de minutos de apnea de test y la de
   desarrollo difieren a lo sumo MAX_APNEA_DIFF.
Se enumeran todas las particiones válidas y se elige una al azar con SEED, así
que todas tienen la misma probabilidad. Las condiciones usan solo etiquetas,
nunca features. Los registros de EXCLUDED quedan afuera.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import (ALL_RECORDS, EXCLUDED, MAX_APNEA_DIFF, RAW_DIR,
                     RESP_RECORDS, SEED, SUBJECT_ALIASES, TEST_FRAC)
from .data import load_apnea_labels, load_record_info

PROFILE = ["age", "sex", "height_cm", "weight_kg"]
MAX_POOL = 25   # 2^25 combinaciones x 3 categorías en int16 ~ 200 MB


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


def candidate_splits(table: pd.DataFrame, test_frac: float = TEST_FRAC,
                     max_diff: float = MAX_APNEA_DIFF) -> tuple[list[str], np.ndarray]:
    """Todas las particiones válidas: (sujetos sorteables, máscaras).

    El bit i de cada máscara vale 1 si el sujeto pool[i] va a test. `table`
    necesita las columnas record, subject, category, has_resp, n_minutes y
    apnea_minutes. Se enumeran las 2^n combinaciones de los sujetos sorteables,
    así que solo sirve para n <= MAX_POOL.
    """
    cats = sorted(table["category"].unique())
    quota = np.array([round(test_frac * (table["category"] == c).sum()) for c in cats])
    fixed = set(table.loc[table["has_resp"], "subject"])
    pool = sorted(set(table["subject"]) - fixed)
    if len(pool) > MAX_POOL:
        raise ValueError(f"{len(pool)} sujetos sorteables: demasiados para enumerar")

    # Cuotas: counts[m] = registros por categoría en test con la máscara m.
    # Se arma duplicando: con cada sujeto nuevo, las combinaciones sin él y con él.
    per_cat = (pd.crosstab(table["subject"], table["category"])
               .reindex(index=pool, columns=cats, fill_value=0))
    counts = np.zeros((1, len(cats)), dtype=np.int16)
    for v in per_cat.to_numpy(dtype=np.int16):
        counts = np.concatenate([counts, counts + v])
    masks = np.flatnonzero((counts == quota).all(axis=1))

    # Balance de minutos, solo sobre las máscaras que ya cumplen las cuotas.
    bits = (masks[:, None] >> np.arange(len(pool))) & 1
    by_subject = table.groupby("subject")[["apnea_minutes", "n_minutes"]].sum().loc[pool]
    apnea_test = bits @ by_subject["apnea_minutes"].to_numpy()
    min_test = bits @ by_subject["n_minutes"].to_numpy()
    apnea_all, min_all = table["apnea_minutes"].sum(), table["n_minutes"].sum()
    diff = apnea_test / min_test - (apnea_all - apnea_test) / (min_all - min_test)
    return pool, masks[np.abs(diff) <= max_diff]


def make_split(table: pd.DataFrame, test_frac: float = TEST_FRAC,
               seed: int = SEED, max_diff: float = MAX_APNEA_DIFF) -> pd.DataFrame:
    """Agrega la columna 'set' ('dev' o 'test') con una partición válida al azar.

    Las particiones válidas salen de candidate_splits(); todas tienen la misma
    probabilidad de ser elegidas.
    """
    pool, masks = candidate_splits(table, test_frac, max_diff)
    if len(masks) == 0:
        raise ValueError("Ninguna partición cumple las cuotas y el balance de minutos")
    mask = np.random.default_rng(seed).choice(masks)
    test = [s for i, s in enumerate(pool) if mask >> i & 1]
    out = table.copy()
    out["set"] = np.where(out["subject"].isin(test), "test", "dev")
    return out.sort_values("record").reset_index(drop=True)
