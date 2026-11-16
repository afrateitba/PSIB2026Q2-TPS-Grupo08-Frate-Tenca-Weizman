"""Estilo y utilidades comunes para las figuras de los notebooks y del informe.

Todas las figuras usan los mismos colores: naranja para la apnea y azul para
lo normal, y se guardan en informe/figuras/ con el mismo tamaño de letra.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from ..config import ROOT

FIG_DIR = ROOT / "informe" / "figuras"

APNEA = "#D9662B"      # naranja
NORMAL = "#2F6DB5"     # azul
GRIS = "#7A7A7A"
ANCHO = 6.3            # pulgadas: ancho de texto del informe
COLORES_CAT = {"A": APNEA, "B": "#C9A227", "C": NORMAL}


def setup() -> None:
    """Estilo común: letra chica, sin bordes de arriba ni de la derecha."""
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 220, "savefig.bbox": "tight",
        "font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5,
        "legend.fontsize": 7.5, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.titleweight": "bold", "axes.titlelocation": "left",
        "lines.linewidth": 0.9, "legend.frameon": False,
    })


def save(fig, name: str, fig_dir: Path = FIG_DIR) -> Path:
    """Guarda la figura como PNG en informe/figuras/<name>.png."""
    fig_dir.mkdir(parents=True, exist_ok=True)
    path = fig_dir / f"{name}.png"
    fig.savefig(path)
    return path


def shade_apnea(ax, labels: np.ndarray, t0_min: float = 0.0, unit: float = 1.0,
                alpha: float = 0.18, label: str | None = "minuto con apnea") -> None:
    """Pinta de naranja los minutos con apnea en un eje cuyo x está en minutos/`unit`.

    `labels`: 1 apnea, 0 normal, -1 sin etiqueta, empezando en el minuto t0_min.
    `unit`: divide los minutos (1 para minutos, 1/60 para segundos, 60 para horas).
    """
    lab = np.asarray(labels)
    edges = np.flatnonzero(np.diff(np.r_[0, (lab == 1).astype(int), 0]))
    for k, (a, b) in enumerate(zip(edges[::2], edges[1::2])):
        ax.axvspan((t0_min + a) / unit, (t0_min + b) / unit, color=APNEA, alpha=alpha,
                   lw=0, label=label if k == 0 else None)


def label_strip(ax, labels: np.ndarray, unit: float = 1.0) -> None:
    """Franja con las etiquetas por minuto (naranja apnea, azul normal)."""
    lab = np.asarray(labels, float)
    lab[lab < 0] = np.nan
    ax.imshow(lab[None, :], aspect="auto", cmap=plt.matplotlib.colors.ListedColormap([NORMAL, APNEA]),
              extent=[0, len(lab) / unit, 0, 1], vmin=0, vmax=1, interpolation="nearest")
    ax.set_yticks([])
