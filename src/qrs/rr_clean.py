"""Limpieza de la serie RR.  Esquema v2 §4.5.
Bloque: Latidos (Integrante 1).

- Fuera de 0,3-2 s -> inválido.
- Cambio > 20 % respecto de la mediana local -> ectópico.
- Inválidos y ectópicos se interpolan; un minuto con > 20 % corregido se excluye.
"""
import numpy as np


def rr_in_range(t_r: np.ndarray, lo: float = 0.3, hi: float = 2.0) -> np.ndarray:
    """Latidos cuyo RR con el anterior y con el siguiente está entre `lo` y `hi` s.

    El primer y el último latido quedan inválidos porque les falta un vecino.
    """
    rr = np.diff(t_r)
    ok = (rr >= lo) & (rr <= hi)
    valid = np.zeros(len(t_r), dtype=bool)
    valid[1:-1] = ok[:-1] & ok[1:]
    return valid


def clean_rr(t_r: np.ndarray, rr: np.ndarray):
    """(rr_limpio, máscara de corregidos)."""
    raise NotImplementedError


def minute_quality(t_r: np.ndarray, corrected: np.ndarray, n_minutes: int) -> np.ndarray:
    """Fracción de latidos corregidos por minuto (para excluir minutos malos)."""
    raise NotImplementedError
