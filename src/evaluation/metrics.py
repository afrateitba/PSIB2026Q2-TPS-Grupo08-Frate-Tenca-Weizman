"""Evaluación en el 30 %, una sola vez.  Esquema v2 §6."""
import numpy as np


def minute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Matriz de confusión, Se, Esp, exactitud."""
    raise NotImplementedError


def record_metrics(minutes_pred_per_hour, minutes_true_per_hour) -> dict:
    """Correlación y Bland-Altman de minutos de apnea por hora; categoría A/B/C."""
    raise NotImplementedError
