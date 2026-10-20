"""Comparación de features candidatas con AUC y bootstrap por sujeto.  E3 y E4.

El detector final usa un único umbral para todos, así que la métrica es el
AUC con todos los minutos juntos. Los minutos de una misma persona no son
independientes: la incertidumbre se calcula remuestreando sujetos.

Truco para que el bootstrap sea rápido: el AUC es la fracción de pares
(minuto con apnea, minuto sin apnea) bien ordenados. Si U[s, s'] cuenta los
pares bien ordenados entre los minutos con apnea del sujeto s y los sin apnea
del sujeto s', un remuestreo que repite cada sujeto w_s veces tiene
AUC = w·U·w / ((w·A)(w·N)). U se calcula una sola vez por variante.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import rankdata


def pair_counts(scores: np.ndarray, labels: np.ndarray,
                subjects: np.ndarray, order: list) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(U, A, N): pares bien ordenados entre sujetos, y minutos con y sin apnea por sujeto.

    Empates cuentan 1/2. Se ignoran los minutos con score no finito.
    """
    ok = np.isfinite(scores)
    s, y, g = scores[ok], labels[ok], subjects[ok]
    pos = [np.sort(s[(g == k) & (y == 1)]) for k in order]
    neg = [np.sort(s[(g == k) & (y == 0)]) for k in order]
    U = np.zeros((len(order), len(order)))
    for j, n in enumerate(neg):
        if len(n) == 0:
            continue
        for i, p in enumerate(pos):
            if len(p):
                lo = np.searchsorted(n, p, side="left")
                hi = np.searchsorted(n, p, side="right")
                U[i, j] = lo.sum() + 0.5 * (hi - lo).sum()
    return U, np.array([len(p) for p in pos], float), np.array([len(n) for n in neg], float)


def pooled_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """AUC directo (Mann-Whitney) con todos los minutos juntos."""
    ok = np.isfinite(scores)
    s, y = scores[ok], labels[ok]
    U, A, N = pair_counts(s, y, np.zeros(len(s)), [0])
    return float(U[0, 0] / (A[0] * N[0]))


def compare_variants(table: pd.DataFrame, labels: np.ndarray, subjects: np.ndarray,
                     n_boot: int = 2000, seed: int = 2026) -> pd.DataFrame:
    """Compara las columnas de `table` (una variante por columna) por AUC.

    Devuelve por variante: AUC, IC 95 %, probabilidad de ser la mejor,
    diferencia con la mejor, su IC 95 % y si empata con la mejor (el IC de
    la diferencia incluye 0). Los remuestreos son los mismos para todas.
    """
    order = list(pd.unique(subjects))
    W = np.random.default_rng(seed).multinomial(len(order), np.ones(len(order)) / len(order), size=n_boot)
    W = W.astype(float)
    auc, boot = [], []
    for col in table.columns:
        U, A, N = pair_counts(table[col].to_numpy(float), labels, subjects, order)
        auc.append(U.sum() / (A.sum() * N.sum()))
        boot.append(np.einsum("bi,ij,bj->b", W, U, W) / ((W @ A) * (W @ N)))
    auc, boot = np.array(auc), np.array(boot).T                 # boot: n_boot x variantes
    best = int(np.argmax(auc))
    dif = boot - boot[:, [best]]
    lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
    dlo, dhi = np.percentile(dif, [2.5, 97.5], axis=0)
    return pd.DataFrame({"auc": auc, "ic_lo": lo, "ic_hi": hi,
                         "p_mejor": np.bincount(boot.argmax(axis=1), minlength=len(auc)) / n_boot,
                         "dif": auc - auc[best], "dif_lo": dlo, "dif_hi": dhi,
                         "empata": dhi >= 0}, index=table.columns)


def orient(table: pd.DataFrame, labels: np.ndarray) -> tuple[pd.DataFrame, pd.Series]:
    """Da vuelta las columnas con AUC < 0,5 para que "más alto" sea siempre "más apnea".

    El sentido de una feature de HRV no se conoce de antemano (por ejemplo, el
    RR medio podría bajar con la apnea), así que se fija con los datos de
    elección y se reutiliza tal cual en los sujetos de validación.
    """
    signs = pd.Series({c: (-1.0 if pooled_auc(table[c].to_numpy(float), labels) < 0.5 else 1.0)
                       for c in table.columns})
    return table * signs, signs


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra, rb = rankdata(a), rankdata(b)
    return float(np.corrcoef(ra, rb)[0, 1]) if ra.std() > 0 and rb.std() > 0 else np.nan


def agreement_compare(table: pd.DataFrame, labels: np.ndarray, records: np.ndarray,
                      subjects: np.ndarray, n_boot: int = 500, seed: int = 2026) -> pd.DataFrame:
    """Acierto por registro de cada columna, con bootstrap por sujeto.

    Para cada candidata: umbral de Youden con todos sus minutos, fracción de
    minutos de apnea estimada y real por registro, y la correlación de
    Spearman entre las dos. Devuelve el Spearman, su IC y si empata con el mejor.
    """
    from .thresholds import roc_youden
    rec_list = list(pd.unique(records))
    rec_subj = pd.Series(subjects, index=records).groupby(level=0).first().loc[rec_list].to_numpy()
    real = pd.Series(labels, index=records).groupby(level=0).mean().loc[rec_list].to_numpy()
    subj_list = list(pd.unique(rec_subj))
    by_subj = [np.flatnonzero(rec_subj == s) for s in subj_list]
    rng = np.random.default_rng(seed)
    draws = [np.concatenate([by_subj[i] for i in rng.integers(0, len(subj_list), len(subj_list))])
             for _ in range(n_boot)]
    rho, boot = [], []
    for col in table.columns:
        s = table[col].to_numpy(float)
        thr = roc_youden(s, labels)["umbral"]
        est = pd.Series((s >= thr).astype(float), index=records)[np.isfinite(s)]
        est = est.groupby(level=0).mean().reindex(rec_list).to_numpy()
        rho.append(_spearman(real, est))
        boot.append([_spearman(real[d], est[d]) for d in draws])
    rho, boot = np.array(rho), np.array(boot).T
    best = int(np.nanargmax(rho))
    dlo, dhi = np.nanpercentile(boot - boot[:, [best]], [2.5, 97.5], axis=0)
    lo, hi = np.nanpercentile(boot, [2.5, 97.5], axis=0)
    return pd.DataFrame({"spearman": rho, "ic_lo": lo, "ic_hi": hi, "dif": rho - rho[best],
                         "dif_lo": dlo, "dif_hi": dhi, "empata": dhi >= 0}, index=table.columns)


RULES = ("original", "noninferior", "max")


def select_variant(table: pd.DataFrame, labels: np.ndarray, subjects: np.ndarray,
                   records: np.ndarray, complexity: pd.Series, n_boot: int = 2000,
                   n_boot_rec: int = 500, seed: int = 2026, rule: str = "noninferior",
                   delta: float = 0.02) -> dict:
    """Regla de elección de E3/E4.

    1. Se orienta cada candidata (más alto = más apnea).
    2. AUC con todos los minutos juntos y un grupo de candidatas equivalentes
       a la mejor, según `rule`:
       - "original": el IC 95 % de la diferencia con la mejor incluye 0. Es la
         regla fijada al principio; resultó defectuosa porque mete en el grupo
         a las candidatas ruidosas (IC ancho) y deja afuera a las parecidas.
       - "noninferior": con 95 % de confianza la candidata es como mucho
         `delta` peor que la mejor (límite inferior del IC de la diferencia
         >= -delta).
       - "max": solo la de mayor AUC (sin desempate).
    3. Dentro del grupo, acierto por registro (Spearman); se quedan las que no
       se distinguen de la mejor en ese criterio.
    4. Entre esas, la más simple según `complexity` (tuplas: menor = más simple).
    """
    if rule not in RULES:
        raise ValueError(f"regla desconocida: {rule} (opciones: {RULES})")
    oriented, signs = orient(table, labels)
    auc = compare_variants(oriented, labels, subjects, n_boot, seed)
    if rule == "original":
        grupo = list(auc.index[auc.empata])
    elif rule == "noninferior":
        grupo = list(auc.index[auc.dif_lo >= -delta])
    else:
        grupo = [auc.auc.idxmax()]
    agr = agreement_compare(oriented[grupo], labels, records, subjects, n_boot_rec, seed)
    grupo2 = list(agr.index[agr.empata])
    winner = min(grupo2, key=lambda v: complexity[v])
    return {"ganadora": winner, "signo": float(signs[winner]), "signos": signs, "auc": auc,
            "grupo": grupo, "acuerdo": agr, "grupo2": grupo2, "regla": rule}


def subject_folds(has_apnea: pd.Series, k: int = 5, seed: int = 2026) -> list[list]:
    """Reparte los sujetos en k grupos, separando a los que tienen apnea de los que no.

    Así cada grupo tiene sujetos de las dos clases en proporciones parecidas.
    """
    rng = np.random.default_rng(seed)
    folds = [[] for _ in range(k)]
    i = 0
    for flag in (True, False):
        subj = has_apnea.index[has_apnea == flag].to_numpy()
        for s in rng.permutation(subj):
            folds[i % k].append(s)
            i += 1
    return folds


def cross_validate_selection(table: pd.DataFrame, labels: np.ndarray, subjects: np.ndarray,
                             records: np.ndarray, complexity: pd.Series, folds: list,
                             reference: str | None = None, **kw) -> pd.DataFrame:
    """Repite la elección dejando afuera un grupo de sujetos por vez.

    Para cada grupo: la ganadora elegida con los demás, su AUC donde se eligió
    y en los sujetos que quedaron afuera (con el signo fijado al elegir), y el
    AUC afuera de una configuración de referencia fija, si se da.
    """
    rows = []
    for k, fold in enumerate(folds):
        out = np.isin(subjects, fold)
        sel = select_variant(table[~out], labels[~out], subjects[~out], records[~out],
                             complexity, **kw)
        w, sg = sel["ganadora"], sel["signo"]
        row = {"grupo": k + 1, "sujetos afuera": len(fold), "ganadora": w,
               "AUC al elegir": float(sel["auc"].loc[w, "auc"]),
               "AUC afuera": pooled_auc(sg * table[w].to_numpy(float)[out], labels[out]),
               "tamaño del grupo empatado": len(sel["grupo"])}
        if reference is not None:
            sr = sel["signos"][reference]
            row["referencia afuera"] = pooled_auc(sr * table[reference].to_numpy(float)[out], labels[out])
        rows.append(row)
    return pd.DataFrame(rows).set_index("grupo")
