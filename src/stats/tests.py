"""Tests estadísticos.  Esquema v2 §5.
Bloque: los tres.

Unidad de inferencia principal: el sujeto (minutos de un mismo registro no
son independientes). Los tests por minuto son solo descriptivos.
"""
import numpy as np


def paired_subject_test(diffs: np.ndarray) -> dict:
    """H1/H2. Shapiro sobre las diferencias pareadas -> t pareada o Wilcoxon.

    Devuelve test usado, estadístico, p, tamaño de efecto e IC.
    """
    raise NotImplementedError


def mann_whitney_cliff(x_normal: np.ndarray, x_apnea: np.ndarray) -> dict:
    """Descriptivo por minuto: U, p y delta de Cliff."""
    raise NotImplementedError


def holm(pvals) -> np.ndarray:
    """p ajustados por Holm."""
    raise NotImplementedError
