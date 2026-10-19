"""Limpieza de la serie RR.  Esquema v2 §4.5.
Bloque: Latidos (Integrante 1).

- Fuera de 0,3-2 s -> inválido.
- Cambio > 20 % respecto de la mediana local -> ectópico.
- Inválidos y ectópicos se interpolan; un minuto con > 20 % corregido se excluye.
"""
import numpy as np


def clean_rr(t_r: np.ndarray, rr: np.ndarray):
    """(rr_limpio, máscara de corregidos)."""
    raise NotImplementedError


def minute_quality(t_r: np.ndarray, corrected: np.ndarray, n_minutes: int) -> np.ndarray:
    """Fracción de latidos corregidos por minuto (para excluir minutos malos)."""
    raise NotImplementedError
