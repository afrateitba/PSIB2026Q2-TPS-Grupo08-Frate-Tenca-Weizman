"""Post-procesado de una feature por minuto: normalización por registro y suavizado.

Las dos operaciones usan solo la propia noche del registro y nunca las
etiquetas, así que se aplican igual en desarrollo y en test. Cuál conviene
(o ninguna) se elige con datos en E3b.
"""
import numpy as np
import pandas as pd

NORMALIZATIONS = ("none", "baseline", "zscore")


def normalize(values: pd.Series, records: pd.Series, method: str = "none",
              q: float = 10) -> pd.Series:
    """Normaliza una feature dentro de cada registro.

    - "none":     sin cambios.
    - "baseline": resta el percentil `q` de la noche (la "línea de base" de esa
                  persona); conserva la escala, así una noche con mucha apnea
                  sigue teniendo valores altos.
    - "zscore":   (x - media) / desvío de la noche; iguala todas las noches a
                  media 0 y desvío 1 (es lo que proponía el esquema v2).
    """
    g = values.groupby(records)
    if method == "none":
        return values.copy()
    if method == "baseline":
        return values - g.transform(lambda v: np.nanpercentile(v, q))
    if method == "zscore":
        return (values - g.transform("mean")) / g.transform("std")
    raise ValueError(f"normalización desconocida: {method} (opciones: {NORMALIZATIONS})")


def smooth(values: pd.Series, records: pd.Series, minutes: pd.Series, k: int = 1) -> pd.Series:
    """Mediana móvil centrada de `k` minutos dentro de cada registro.

    Respeta los huecos: un minuto faltante no se rellena ni hace que se
    mezclen minutos lejanos. k = 1 devuelve los valores sin cambios.
    """
    if k <= 1:
        return values.copy()
    out = pd.Series(np.nan, index=values.index, dtype=float)
    for _, idx in values.groupby(records).groups.items():
        m = minutes.loc[idx]
        full = pd.Series(values.loc[idx].to_numpy(), index=m.to_numpy()).reindex(
            np.arange(m.min(), m.max() + 1))
        sm = full.rolling(k, center=True, min_periods=1).median()
        out.loc[idx] = sm.loc[m.to_numpy()].to_numpy()
    return out
