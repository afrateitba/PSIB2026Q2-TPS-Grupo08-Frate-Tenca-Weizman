"""Segmentación en minutos y ventanas centradas.

Unidad de decisión: 1 minuto (el minuto m abarca [60 m, 60 m + 60) s), porque
las etiquetas de la base son por minuto. Las features espectrales se calculan
en una ventana de 240 s centrada en cada minuto (src/features/detector.py;
justificación en notebooks/01 sección 7 y 04 secciones 1 y 15).
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
