"""Validación cruzada anidada de toda la elección del detector.  Notebook 12.

En cada grupo de sujetos se repite, solo con los sujetos de entrenamiento:
1. la elección de la feature (E3a): no inferioridad -> acierto por registro ->
   la más simple;
2. el post-procesado (E3b) sobre el grupo de no inferiores, con la misma regla;
3. el umbral de Youden.
Se hace para F y para la HRV de referencia, y lo elegido se aplica a los
sujetos de afuera. `select_pipeline` recibe solo filas de entrenamiento: los
sujetos de afuera nunca entran a la elección.

Los puntajes de grupos distintos pueden venir de features distintas, así que
el área bajo la curva se calcula por grupo y se promedia (`fold_auc`). Entre
grupos solo se juntan las decisiones y lo que se calcula por noche.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from ..evaluation.metrics import (apply_a_cut, apply_night_calibration, category_from_minutes,
                                  fit_a_cut, fit_night_calibration)
from ..features.variants import postprocess_variants
from .compare import pair_counts, select_variant
from .thresholds import roc_youden


def select_pipeline(wide: pd.DataFrame, meta: pd.DataFrame, labels: np.ndarray,
                    eval_idx: pd.MultiIndex, subjects: np.ndarray, n_boot: int = 1000,
                    n_boot_rec: int = 300, seed: int = 2026, delta: float = 0.02) -> dict:
    """Elección completa con los datos que recibe: feature -> post-procesado -> umbral.

    `wide`: candidatas por (record, minute), con todos los minutos de cada noche
    (la normalización y el suavizado usan la noche completa). `eval_idx`: los
    minutos donde se elige (con etiqueta, buena calidad y todas las candidatas
    calculables). `labels` y `subjects` van alineados con `eval_idx`.
    """
    recs = eval_idx.get_level_values("record").to_numpy()
    kw = dict(n_boot=n_boot, n_boot_rec=n_boot_rec, seed=seed, rule="noninferior", delta=delta)
    sel_a = select_variant(wide.loc[eval_idx], labels, subjects, recs, meta.complejidad, **kw)
    grupo = list(sel_a["grupo"])
    pp, meta_pp = postprocess_variants(wide[grupo], meta.loc[grupo])
    sel_b = select_variant(pp.loc[eval_idx], labels, subjects, recs, meta_pp.complejidad, **kw)
    win, sign = sel_b["ganadora"], float(sel_b["signo"])
    thr = roc_youden(sign * pp.loc[eval_idx, win].to_numpy(float), labels)["umbral"]
    row = meta_pp.loc[win]
    return {"elegida_e3a": sel_a["ganadora"], "grupo_e3a": grupo, "variante": win,
            "base": row["base"], "normalizacion": row["normalizacion"],
            "suavizado": int(row["suavizado"]), "signo": sign, "umbral": float(thr)}


def apply_choice(wide: pd.DataFrame, meta: pd.DataFrame, choice: dict) -> pd.Series:
    """Puntaje orientado de la variante elegida en todos los minutos de `wide`.

    El post-procesado usa solo la noche de cada registro, así que se puede
    aplicar a los sujetos de afuera sin información de nadie más.
    """
    base = choice["base"]
    pp, _ = postprocess_variants(wide[[base]], meta.loc[[base]],
                                 norms=(choice["normalizacion"],), ks=(choice["suavizado"],))
    return choice["signo"] * pp.iloc[:, 0]


def _evaluated(info: pd.DataFrame, records, scores: dict) -> pd.DataFrame:
    """Minutos evaluados como en plan_test.md §4: con etiqueta, 20 % o menos de
    RR corregidos y todos los puntajes calculables."""
    inf = info[info.index.get_level_values("record").isin(records)]
    d = inf.loc[(inf.label >= 0) & (inf.corrected <= 0.2), ["label"]].copy()
    for fam, s in scores.items():
        d[f"score_{fam}"] = s.reindex(d.index)
    return d.dropna()


def nested_cv(families: dict, info: pd.DataFrame, subject_of: pd.Series,
              eval_idx: pd.MultiIndex, folds: list, **kw) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validación cruzada anidada por sujetos.

    `families`: {nombre: (wide, meta)}, por ejemplo F y HRV. `info`: etiqueta
    (`label`) y fracción de RR corregidos (`corrected`) de todos los minutos,
    indexada por (record, minute). `subject_of`: sujeto de cada registro.
    `eval_idx`: minutos de elección (comunes a todas las candidatas). `folds`:
    lista de listas de sujetos; cada una queda afuera una vez.

    Devuelve (pred, choices):
    - pred: un renglón por minuto evaluado de los sujetos de afuera, con el
      grupo, la etiqueta, y por familia el puntaje, la decisión (puntaje >=
      umbral del grupo), la fracción estimada de su noche y la calibrada;
    - choices: lo elegido en cada grupo y familia, con su umbral y la recta de
      calibración por noche ajustada con las noches de entrenamiento.
    """
    rows, choices = [], []
    for k, fold in enumerate(folds, start=1):
        out = subject_of.index[subject_of.isin(fold)]
        tr_idx = eval_idx[~eval_idx.get_level_values("record").isin(out)]
        y_tr = info.loc[tr_idx, "label"].to_numpy(int)
        s_tr = subject_of.loc[tr_idx.get_level_values("record")].to_numpy()
        ch, sc_tr, sc_out = {}, {}, {}
        for fam, (wide, meta) in families.items():
            in_out = wide.index.get_level_values("record").isin(out)
            ch[fam] = select_pipeline(wide[~in_out], meta, y_tr, tr_idx, s_tr, **kw)
            sc_tr[fam] = apply_choice(wide[~in_out], meta, ch[fam])
            sc_out[fam] = apply_choice(wide[in_out], meta, ch[fam])
        d_tr = _evaluated(info, subject_of.index.difference(out), sc_tr)
        d = _evaluated(info, out, sc_out)
        d.insert(0, "grupo", k)
        for fam, c in ch.items():
            # Con las noches de entrenamiento: la recta por noche (fracción real
            # contra estimada) y el corte que separa las noches A del resto (notebook 13).
            p_tr = (d_tr[f"score_{fam}"] >= c["umbral"]).groupby(level="record").mean()
            real_tr = d_tr["label"].groupby(level="record").mean()
            a, b = fit_night_calibration(p_tr.to_numpy(), real_tr.loc[p_tr.index].to_numpy())
            min_tr = d_tr["label"].groupby(level="record").sum().loc[p_tr.index]
            cut_a = fit_a_cut(p_tr.to_numpy(), [category_from_minutes(m) == "A" for m in min_tr])
            d[f"pred_{fam}"] = (d[f"score_{fam}"] >= c["umbral"]).astype(int)
            frac = d[f"pred_{fam}"].groupby(level="record").transform("mean")
            d[f"frac_{fam}"] = frac
            d[f"frac_cal_{fam}"] = apply_night_calibration(frac.to_numpy(), a, b)
            d[f"a_corte_{fam}"] = apply_a_cut(frac.to_numpy(), cut_a)
            choices.append({"grupo": k, "familia": fam, "sujetos_afuera": len(fold),
                            "elegida_e3a": c["elegida_e3a"], "tamaño_grupo_e3a": len(c["grupo_e3a"]),
                            "variante": c["variante"], "signo": c["signo"], "umbral": c["umbral"],
                            "cal_a": a, "cal_b": b, "corte_a": cut_a})
        rows.append(d)
    return pd.concat(rows), pd.DataFrame(choices)


def fold_auc(pred: pd.DataFrame, subject_of: pd.Series, fams=("F", "HRV"),
             n_boot: int = 2000, seed: int = 2026) -> pd.DataFrame:
    """Área bajo la curva por grupo, promediada entre grupos, con bootstrap por sujeto.

    Cada grupo usa sus propios puntajes (pueden ser features distintas). En
    cada remuestreo se sortean los sujetos de todos los grupos con reposición
    y se recalcula el área de cada grupo con sus sujetos sorteados; un grupo
    sin minutos de alguna clase en ese sorteo no entra al promedio.
    Devuelve una fila por familia y otra para la diferencia entre las dos primeras.
    """
    subj = subject_of.loc[pred.index.get_level_values("record")].to_numpy()
    order = list(pd.unique(subj))
    W = np.random.default_rng(seed).multinomial(len(order), np.ones(len(order)) / len(order),
                                                size=n_boot).astype(float)
    y = pred["label"].to_numpy(int)
    point, boot, per_fold = {}, {}, {}
    for fam in fams:
        s = pred[f"score_{fam}"].to_numpy(float)
        pts, bts = [], []
        for g in sorted(pred["grupo"].unique()):
            m = (pred["grupo"] == g).to_numpy()
            U, A, N = pair_counts(s[m], y[m], subj[m], order)
            pts.append(U.sum() / (A.sum() * N.sum()))
            with np.errstate(invalid="ignore", divide="ignore"):
                bts.append(np.einsum("bi,ij,bj->b", W, U, W) / ((W @ A) * (W @ N)))
        per_fold[fam] = pts
        point[fam] = float(np.mean(pts))
        boot[fam] = np.nanmean(np.array(bts), axis=0)
    rows = {fam: {"media": point[fam], "ic_lo": np.nanpercentile(boot[fam], 2.5),
                  "ic_hi": np.nanpercentile(boot[fam], 97.5),
                  "por_grupo": np.round(per_fold[fam], 3).tolist()} for fam in fams}
    a, b = fams[0], fams[1]
    dif = boot[a] - boot[b]
    rows[f"{a} - {b}"] = {"media": point[a] - point[b], "ic_lo": np.nanpercentile(dif, 2.5),
                          "ic_hi": np.nanpercentile(dif, 97.5),
                          "por_grupo": np.round(np.array(per_fold[a]) - np.array(per_fold[b]), 3).tolist()}
    return pd.DataFrame(rows).T


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra, rb = rankdata(a), rankdata(b)
    return float(np.corrcoef(ra, rb)[0, 1]) if ra.std() > 0 and rb.std() > 0 else np.nan


def record_table(pred: pd.DataFrame, subject_of: pd.Series, fams=("F", "HRV")) -> pd.DataFrame:
    """Una fila por noche: sujeto, minutos evaluados, fracción real y estimadas."""
    g = pred.groupby(level="record")
    t = pd.DataFrame({"minutos": g.size(), "real": g["label"].mean()})
    for fam in fams:
        t[f"est_{fam}"] = g[f"frac_{fam}"].first()
        t[f"cal_{fam}"] = g[f"frac_cal_{fam}"].first()
    t.insert(0, "subject", subject_of.loc[t.index].to_numpy())
    return t


def record_agreement_boot(t: pd.DataFrame, cols=("est_F", "est_HRV"), n_boot: int = 2000,
                          seed: int = 2026) -> pd.DataFrame:
    """Spearman entre cada fracción estimada y la real, y la diferencia entre las
    dos primeras columnas, con bootstrap por sujeto (se sortean sujetos enteros)."""
    rng = np.random.default_rng(seed)
    by_subj = [np.flatnonzero(t["subject"].to_numpy() == s) for s in pd.unique(t["subject"])]
    real = t["real"].to_numpy()
    point = {c: _spearman(t[c].to_numpy(), real) for c in cols}
    boot = {c: [] for c in cols}
    for _ in range(n_boot):
        d = np.concatenate([by_subj[i] for i in rng.integers(0, len(by_subj), len(by_subj))])
        for c in cols:
            boot[c].append(_spearman(t[c].to_numpy()[d], real[d]))
    rows = {c: {"spearman": point[c], "ic_lo": np.nanpercentile(boot[c], 2.5),
                "ic_hi": np.nanpercentile(boot[c], 97.5)} for c in cols}
    a, b = cols[0], cols[1]
    dif = np.array(boot[a]) - np.array(boot[b])
    rows[f"{a} - {b}"] = {"spearman": point[a] - point[b], "ic_lo": np.nanpercentile(dif, 2.5),
                          "ic_hi": np.nanpercentile(dif, 97.5)}
    return pd.DataFrame(rows).T


def category_agreement_boot(t: pd.DataFrame, real: str, cols, n_boot: int = 2000,
                            seed: int = 2026) -> pd.DataFrame:
    """Fracción de noches con la categoría correcta para cada columna de `cols`, y
    la diferencia (segunda - primera) con bootstrap por sujeto."""
    rng = np.random.default_rng(seed)
    hit = {c: (t[c].to_numpy() == t[real].to_numpy()).astype(float) for c in cols}
    by_subj = [np.flatnonzero(t["subject"].to_numpy() == s) for s in pd.unique(t["subject"])]
    a, b = cols[0], cols[1]
    dif = []
    for _ in range(n_boot):
        d = np.concatenate([by_subj[i] for i in rng.integers(0, len(by_subj), len(by_subj))])
        dif.append(hit[b][d].mean() - hit[a][d].mean())
    rows = {c: {"acierto": hit[c].mean(), "ic_lo": np.nan, "ic_hi": np.nan} for c in cols}
    rows[f"{b} - {a}"] = {"acierto": hit[b].mean() - hit[a].mean(),
                          "ic_lo": np.percentile(dif, 2.5), "ic_hi": np.percentile(dif, 97.5)}
    return pd.DataFrame(rows).T


def night_error_boot(t: pd.DataFrame, est: str, alt: str, n_boot: int = 2000,
                     seed: int = 2026) -> dict:
    """Error absoluto medio de los minutos de apnea por hora (60 x fracción) con
    `est` y con `alt`, y la diferencia alt - est con bootstrap por sujeto."""
    rng = np.random.default_rng(seed)
    e1 = 60 * (t[est] - t["real"]).abs().to_numpy()
    e2 = 60 * (t[alt] - t["real"]).abs().to_numpy()
    by_subj = [np.flatnonzero(t["subject"].to_numpy() == s) for s in pd.unique(t["subject"])]
    dif = []
    for _ in range(n_boot):
        d = np.concatenate([by_subj[i] for i in rng.integers(0, len(by_subj), len(by_subj))])
        dif.append(e2[d].mean() - e1[d].mean())
    return {"error_" + est: float(e1.mean()), "error_" + alt: float(e2.mean()),
            "diferencia": float(e2.mean() - e1.mean()),
            "ic_lo": float(np.percentile(dif, 2.5)), "ic_hi": float(np.percentile(dif, 97.5))}


def subsample_h2(pred: pd.DataFrame, subject_of: pd.Series, n_subjects: int = 10,
                 n_draws: int = 500, n_boot: int = 1000, seed: int = 2026,
                 with_auc: bool = True) -> pd.DataFrame:
    """Qué esperar de test: se sortean `n_subjects` sujetos y se aplica el
    procedimiento de plan_test.md §5 (bootstrap por sujeto, p bilateral, Holm).

    M1 junta los puntajes de los sujetos sorteados, así que solo vale si todos
    los grupos eligieron la misma feature (`with_auc`). M2 usa las fracciones
    estimadas por noche, que siempre son comparables. Holm se aplica sobre las
    medidas presentes: sin M1, `p_M2_holm` es el p sin corregir, y el notebook
    tiene que aplicar el umbral de Holm para dos medidas.
    """
    rng = np.random.default_rng(seed)
    subj_all = subject_of.loc[pred.index.get_level_values("record")].to_numpy()
    t = record_table(pred, subject_of)
    subjects = pd.unique(t["subject"])
    y = pred["label"].to_numpy(int)
    out = []
    for _ in range(n_draws):
        pick = rng.choice(subjects, size=n_subjects, replace=False)
        W = rng.multinomial(n_subjects, np.ones(n_subjects) / n_subjects, size=n_boot).astype(float)
        row = {}
        if with_auc:
            m = np.isin(subj_all, pick)
            order = list(pick)
            aucs, boots = [], []
            for fam in ("F", "HRV"):
                U, A, N = pair_counts(pred[f"score_{fam}"].to_numpy(float)[m], y[m], subj_all[m], order)
                aucs.append(U.sum() / (A.sum() * N.sum()))
                with np.errstate(invalid="ignore", divide="ignore"):
                    boots.append(np.einsum("bi,ij,bj->b", W, U, W) / ((W @ A) * (W @ N)))
            d = boots[0] - boots[1]
            d = d[np.isfinite(d)]
            row["dif_M1"] = aucs[0] - aucs[1]
            row["p_M1"] = min(1.0, 2 * min((d <= 0).mean(), (d >= 0).mean()))
        tt = t[t["subject"].isin(pick)]
        by_subj = [np.flatnonzero(tt["subject"].to_numpy() == s) for s in pick]
        real, eF, eH = tt["real"].to_numpy(), tt["est_F"].to_numpy(), tt["est_HRV"].to_numpy()
        difs = []
        for w in W.astype(int):
            idx = np.concatenate([np.repeat(by_subj[i], w[i]) for i in range(n_subjects) if w[i]])
            difs.append(_spearman(eF[idx], real[idx]) - _spearman(eH[idx], real[idx]))
        difs = np.array(difs)
        difs = difs[np.isfinite(difs)]
        row["dif_M2"] = _spearman(eF, real) - _spearman(eH, real)
        row["p_M2"] = min(1.0, 2 * min((difs <= 0).mean(), (difs >= 0).mean()))
        out.append(row)
    res = pd.DataFrame(out)
    ps = [c for c in ("p_M1", "p_M2") if c in res]
    # Holm sobre las medidas presentes, sorteo por sorteo.
    P = res[ps].to_numpy(float)
    o = np.argsort(P, axis=1)
    srt = np.take_along_axis(P, o, axis=1) * (len(ps) - np.arange(len(ps)))
    adj = np.empty_like(P)
    np.put_along_axis(adj, o, np.maximum.accumulate(np.minimum(1, srt), axis=1), axis=1)
    for j, c in enumerate(ps):
        res[f"{c}_holm"] = adj[:, j]
    for c in ps:
        m = c.split("_")[1]
        res[f"confirma_{m}"] = (res[f"{c}_holm"] < 0.05) & (res[f"dif_{m}"] > 0)
    return res
