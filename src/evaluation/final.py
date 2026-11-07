"""Funciones de la evaluación final en test.  plan_test.md §4 a §6.

- `fill_from_nearest`: análisis de sensibilidad con todos los minutos (§4).
- `h2_bootstrap`: H2 con M1 y M2, diferencia F - referencia, IC y p (§5).
- `h1_subject_deltas`: diferencia de CR por sujeto, como en E2 (§6.3).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..stats.compare import _spearman, pair_counts


def fill_from_nearest(minutes, values: dict, valid) -> dict:
    """Completa los minutos no válidos de UN registro con el minuto válido más cercano.

    `minutes`: número de minuto de cada fila; `values`: {nombre: vector};
    `valid`: True si la fila es válida. Cada fila no válida toma los valores
    del minuto válido más cercano (si hay empate, el anterior). Si no hay
    ningún minuto válido, todo queda en NaN.
    """
    m = np.asarray(minutes, dtype=float)
    ok = np.asarray(valid, dtype=bool)
    if len(m) != len(ok) or any(len(v) != len(m) for v in values.values()):
        raise ValueError("minutes, valid y cada vector de values deben tener el mismo largo.")
    if not ok.any():
        return {k: np.full(len(m), np.nan) for k in values}
    vm = m[ok]
    order = np.argsort(vm, kind="stable")
    vm_sorted, src = vm[order], np.flatnonzero(ok)[order]
    i = np.clip(np.searchsorted(vm_sorted, m), 1, len(vm_sorted) - 1) if len(vm_sorted) > 1 else np.zeros(len(m), int)
    if len(vm_sorted) > 1:
        left, right = i - 1, i
        pick = np.where(np.abs(m - vm_sorted[left]) <= np.abs(m - vm_sorted[right]), left, right)
    else:
        pick = i
    nearest = src[pick]
    take = np.where(ok, np.arange(len(m)), nearest)
    return {k: np.asarray(v, dtype=float)[take] for k, v in values.items()}


def _p_two_sided(d: np.ndarray) -> float:
    d = d[np.isfinite(d)]
    if len(d) == 0:
        return np.nan
    return float(min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean())))


def h2_bootstrap(score_f, score_h, labels, records, subjects, thr_f: float, thr_h: float,
                 n_boot: int = 10_000, seed: int = 2026) -> pd.DataFrame:
    """H2 en test (plan_test.md §5): M1 y M2 de F y de la referencia, y su diferencia.

    - M1: AUC por minuto con todos los minutos juntos (scores tal cual, sin
      reorientar: el sentido quedó fijado en desarrollo).
    - M2: Spearman, sobre los registros, entre la fracción de minutos con
      score >= umbral de desarrollo y la fracción anotada.
    El bootstrap remuestrea sujetos enteros con reposición (los mismos
    remuestreos para las dos medidas y las dos features). Devuelve una fila
    por medida con F, referencia, diferencia (F - ref), su IC 95 % y el p
    bilateral = 2 * min(fracción de diferencias <= 0, fracción >= 0).
    """
    sf, sh = np.asarray(score_f, float), np.asarray(score_h, float)
    y, r, g = np.asarray(labels, int), np.asarray(records), np.asarray(subjects)
    if not (len(sf) == len(sh) == len(y) == len(r) == len(g)):
        raise ValueError("Todas las entradas deben tener el mismo largo.")
    if not (np.isfinite(sf).all() and np.isfinite(sh).all()):
        raise ValueError("H2 se evalúa sobre minutos con F y referencia calculables.")
    order = list(pd.unique(g))
    W = np.random.default_rng(seed).multinomial(len(order), np.ones(len(order)) / len(order),
                                                size=n_boot).astype(float)
    # M1
    m1, m1_boot = {}, {}
    for name, s in (("F", sf), ("ref", sh)):
        U, A, N = pair_counts(s, y, g, order)
        m1[name] = U.sum() / (A.sum() * N.sum())
        with np.errstate(invalid="ignore", divide="ignore"):
            m1_boot[name] = np.einsum("bi,ij,bj->b", W, U, W) / ((W @ A) * (W @ N))
    # M2
    d = pd.DataFrame({"r": r, "g": g, "y": y, "F": sf >= thr_f, "ref": sh >= thr_h})
    t = d.groupby("r", sort=False).agg(g=("g", "first"), real=("y", "mean"),
                                       F=("F", "mean"), ref=("ref", "mean"))
    rec_subj = np.array([order.index(s) for s in t.g])
    real = t.real.to_numpy()
    m2 = {k: _spearman(t[k].to_numpy(), real) for k in ("F", "ref")}
    m2_boot = {k: np.empty(n_boot) for k in ("F", "ref")}
    for b in range(n_boot):
        rows = np.repeat(np.arange(len(t)), W[b, rec_subj].astype(int))
        for k in ("F", "ref"):
            m2_boot[k][b] = _spearman(t[k].to_numpy()[rows], real[rows])
    out = []
    for medida, pt, bt in (("M1: AUC por minuto", m1, m1_boot),
                           ("M2: acierto por registro", m2, m2_boot)):
        dif = bt["F"] - bt["ref"]
        lo, hi = np.nanpercentile(dif, [2.5, 97.5])
        out.append({"medida": medida, "F": pt["F"], "referencia": pt["ref"],
                    "diferencia": pt["F"] - pt["ref"], "ic_lo": lo, "ic_hi": hi,
                    "p": _p_two_sided(dif), "remuestreos_validos": int(np.isfinite(dif).sum())})
    return pd.DataFrame(out).set_index("medida")


def h1_subject_deltas(table: pd.DataFrame, values, max_corrected: float | None = 0.2,
                      min_minutes: int = 5) -> tuple[pd.Series, pd.DataFrame]:
    """Diferencia por sujeto de E2 (notebook 03): mediana con apnea - mediana sin apnea.

    `table` tiene record, subject, label y corrected; `values`, el valor por
    fila (por ejemplo CR). Se excluyen minutos sin etiqueta o con valor no
    finito y, si `max_corrected` no es None, los que superan esa fracción de
    RR corregidos. Un registro entra si tiene al menos `min_minutes` de cada
    clase; el sujeto es el promedio de sus registros.
    """
    d = table.assign(v=np.asarray(values, dtype=float))
    d = d[(d.label >= 0) & np.isfinite(d.v)]
    if max_corrected is not None:
        d = d[d.corrected <= max_corrected]
    rows = []
    for rec, g in d.groupby("record"):
        a, n = g.v[g.label == 1], g.v[g.label == 0]
        if len(a) >= min_minutes and len(n) >= min_minutes:
            rows.append({"record": rec, "subject": g.subject.iloc[0], "delta": a.median() - n.median(),
                         "min_apnea": len(a), "min_normal": len(n)})
    per_rec = pd.DataFrame(rows, columns=["record", "subject", "delta", "min_apnea", "min_normal"])
    return per_rec.groupby("subject").delta.mean(), per_rec