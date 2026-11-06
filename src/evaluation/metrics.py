"""Medidas para la evaluación en test (una sola vez).  plan_test.md §6.
 
Las dos funciones reciben valores ya calculados: qué minutos se evalúan y con
qué umbral lo decide el notebook (plan_test.md §4). Se usan igual con F y con
la HRV de referencia.
"""
from __future__ import annotations
 
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
 
CATEGORIES = ("A", "B", "C")
 
 
def _binary(x, name: str) -> np.ndarray:
    v = np.asarray(x)
    if v.ndim != 1 or len(v) == 0:
        raise ValueError(f"{name} debe ser un vector no vacío.")
    if not np.isin(v, [0, 1]).all():
        raise ValueError(f"{name} debe tener solo 0/1 (o False/True).")
    return v.astype(int)
 
 
def _ratio(num: int, den: int) -> float:
    return num / den if den else np.nan
 
 
def minute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Matriz de confusión, Se, Esp, exactitud y exactitud balanceada.
 
    `y_true` es la etiqueta del minuto (1 = apnea) y `y_pred` la decisión
    (1 si la feature es >= umbral). Si una clase no aparece, la medida que la
    necesita vale nan.
    """
    y, p = _binary(y_true, "y_true"), _binary(y_pred, "y_pred")
    if len(y) != len(p):
        raise ValueError("y_true y y_pred deben tener el mismo largo.")
    tp = int(((y == 1) & (p == 1)).sum())
    fn = int(((y == 1) & (p == 0)).sum())
    tn = int(((y == 0) & (p == 0)).sum())
    fp = int(((y == 0) & (p == 1)).sum())
    se, esp = _ratio(tp, tp + fn), _ratio(tn, tn + fp)
    matriz = pd.DataFrame([[tn, fp], [fn, tp]],
                          index=pd.Index(["normal", "apnea"], name="real"),
                          columns=pd.Index(["normal", "apnea"], name="estimado"))
    return {"TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "Se": se, "Esp": esp,
            "exactitud": _ratio(tp + tn, len(y)),
            "exactitud_balanceada": (se + esp) / 2,
            "matriz": matriz}
 
 
def category_from_minutes(apnea_minutes: float) -> str:
    """Categoría por minutos de apnea: A >= 100, B 5-99, C < 5.
 
    Misma regla que split.category_from_labels, aplicada a un conteo de
    minutos (que puede ser estimado y no entero).
    """
    if apnea_minutes >= 100:
        return "A"
    return "C" if apnea_minutes < 5 else "B"
 
 
def record_metrics(minutes_pred, minutes_true, hours, records=None) -> dict:
    """Medidas por registro: minutos de apnea por hora y categoría A/B/C.
 
    Recibe, por registro, los minutos de apnea estimados, los anotados y las
    horas sobre las que se cuentan. Devuelve:
    - `spearman` entre los minutos por hora estimados y los anotados;
    - Bland-Altman de los minutos por hora (estimado - anotado): `sesgo` y
      límites de acuerdo `lim_inf`, `lim_sup` (sesgo ± 1,96 desvíos);
    - `matriz_categorias`: categoría real contra estimada (A, B, C), y
      `acierto_categoria`, la fracción de registros en la categoría correcta;
    - `tabla`: una fila por registro con todo lo anterior.
    """
    est = np.asarray(minutes_pred, dtype=float)
    real = np.asarray(minutes_true, dtype=float)
    h = np.asarray(hours, dtype=float)
    if not (est.ndim == real.ndim == h.ndim == 1) or not (len(est) == len(real) == len(h)):
        raise ValueError("Las entradas deben ser vectores del mismo largo.")
    if len(est) < 2:
        raise ValueError("Hacen falta al menos 2 registros.")
    if not (np.isfinite(est).all() and np.isfinite(real).all()):
        raise ValueError("Los minutos deben ser finitos.")
    if (est < 0).any() or (real < 0).any() or not (h > 0).all():
        raise ValueError("Minutos >= 0 y horas > 0.")
 
    idx = pd.Index(records if records is not None else np.arange(len(est)), name="registro")
    t = pd.DataFrame({"min_estimados": est, "min_anotados": real, "horas": h}, index=idx)
    t["por_hora_estimado"] = t.min_estimados / t.horas
    t["por_hora_anotado"] = t.min_anotados / t.horas
    t["diferencia"] = t.por_hora_estimado - t.por_hora_anotado
    t["media"] = (t.por_hora_estimado + t.por_hora_anotado) / 2
    t["categoria_estimada"] = [category_from_minutes(m) for m in est]
    t["categoria_real"] = [category_from_minutes(m) for m in real]
 
    sesgo = float(t.diferencia.mean())
    sd = float(t.diferencia.std(ddof=1))
    matriz = pd.crosstab(pd.Categorical(t.categoria_real, CATEGORIES),
                         pd.Categorical(t.categoria_estimada, CATEGORIES),
                         rownames=["real"], colnames=["estimada"], dropna=False)
    return {"spearman": float(spearmanr(t.por_hora_estimado, t.por_hora_anotado).statistic),
            "sesgo": sesgo, "sd": sd,
            "lim_inf": sesgo - 1.96 * sd, "lim_sup": sesgo + 1.96 * sd,
            "matriz_categorias": matriz,
            "acierto_categoria": float((t.categoria_estimada == t.categoria_real).mean()),
            "tabla": t}
