"""Segmentación en minutos y ventanas centradas.

Consigna: segmentación de señales.  Esquema v2 §4.6.
Bloque: Espectral (Integrante 3).

Unidad de decisión: 1 minuto (el minuto m abarca [60 m, 60 m + 60) s). Para
las features espectrales se usa una ventana más larga centrada en cada minuto;
su largo se elige con datos (E3).
"""
import numpy as np


def centered_windows(n_minutes: int, width_s: float,
                     t_start: float, t_end: float) -> tuple[np.ndarray, np.ndarray]:
    """(minutos, inicio [s]) de las ventanas de `width_s` s centradas en cada minuto.

    Solo quedan las ventanas que entran completas en [t_start, t_end].
    """
    m = np.arange(n_minutes)
    t0 = 60.0 * m + 30.0 - width_s / 2
    ok = (t0 >= t_start) & (t0 + width_s <= t_end)
    return m[ok], t0[ok]
