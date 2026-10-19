"""Segmentación en minutos y ventanas centradas.

Consigna: segmentación de señales.  Esquema v2 §4.6.
Bloque: Espectral (Integrante 3).

Unidad de decisión: 1 minuto. Lomb y coherencia: ventana centrada de ~8,5 min
(largo final elegido en el 70 % entre {3; 5; 8,5} min).
"""


def centered_windows(n_minutes: int, width_min: float = 8.5):
    """Itera (minuto, t_inicio_s, t_fin_s) con la ventana centrada en cada minuto."""
    raise NotImplementedError
