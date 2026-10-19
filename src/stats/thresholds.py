"""Puntos de corte por ROC e índice de Youden (solo con el 70 %).  Esquema v2 §5."""
import numpy as np


def roc_youden(scores: np.ndarray, labels: np.ndarray) -> dict:
    """Umbral óptimo, Se, Esp y AUC sobre la feature normalizada por registro."""
    raise NotImplementedError
