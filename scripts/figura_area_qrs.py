"""Figura: por qué la EDR se mide con el área del QRS (datos de notebooks/03_edr_wiener.ipynb, §6).

Compara las tres formas de medir el QRS que se pueden calcular en la base (área, amplitud del pico R y
deriva de la línea de base) y su combinación, todas con la misma limpieza que usa el detector final
(sin latidos ectópicos ni atípicos por Hampel), con las tres medidas de 03 §6:
- A1: coherencia con la respiración medida (8 registros con respiración);
- A2: coherencia con la envolvente de la respiración en la banda lenta (los 4 con mucha apnea);
- B: AUC dentro de la noche de la potencia en la banda (31 noches con al menos 20 minutos de cada tipo).
Mismo código y mismos parámetros que 03 §6. Solo usa registros de desarrollo.

Uso: python scripts/figura_area_qrs.py  → informe/figuras/03_area_qrs.png
"""
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import csd, welch
from scipy.stats import mannwhitneyu

from src.config import (ENVELOPE_RMS_S, MIN_MINUTES_PER_CLASS, MINUTE_MAX_CORRECTED, RESP_COH_SEG_S, RESP_RECORDS,
                        SPLIT_CSV)
from src.data import load_apnea_labels, load_ecg, load_respiration
from src.features.coupling import downsample, resample_uniform, welch_spectra
from src.features.detector import BAND, FS_U, WINDOW_S
from src.features.edr import beat_edr, validate_edr
from src.features.windows import centered_windows
from src.qrs.beats import record_beats
from src.qrs.rr_clean import clean_rr, minute_quality
from src.viz.plots import ANCHO, APNEA, GRIS, NORMAL, save, setup

VARIANTES = {                       # nombre en la figura: argumentos de beat_edr (como en 03 §6)
    "Área del QRS": dict(method="area"),
    "Amplitud del pico R": dict(method="amplitude"),
    "Deriva de la línea de base": dict(method="baseline"),
    "Área + deriva": dict(method="combined"),
}
MEDIDAS = {
    "A1": ("A1 · ¿Sigue cada respiración?", "coherencia con la respiración"),
    "A2": ("A2 · ¿Sigue el ciclo de la apnea?", "coherencia con la envolvente"),
    "B": ("B · ¿Separa los minutos con apnea?", "AUC dentro de la noche"),
}
NSEG = int(WINDOW_S * FS_U) // 2


def envolvente(s, fs_, win=ENVELOPE_RMS_S):
    s = np.nan_to_num(s - np.nanmedian(s))
    n = int(win * fs_)
    return np.sqrt(np.convolve(s ** 2, np.ones(n) / n, mode="same"))


def potencia_por_minuto(t, v, lab, q):
    minutos, inicios = centered_windows(len(lab), WINDOW_S, t[0], t[-1] + 1 / FS_U)
    n = int(WINDOW_S * FS_U)
    P, L = [], []
    for m, a in zip(minutos, inicios):
        if lab[m] < 0 or not q[m] <= MINUTE_MAX_CORRECTED:
            continue
        i = int(round((a - t[0]) * FS_U))
        s = v[i:i + n]
        if len(s) < n:
            continue
        f_, sxx, _, _ = welch_spectra(s, s, FS_U, n // 2)
        P.append(np.log10(sxx[(f_ >= BAND[0] - 1e-9) & (f_ <= BAND[1] + 1e-9)].mean()))
        L.append(lab[m])
    return np.array(P), np.array(L)


def evaluar(rec):
    ecg, fs = load_ecg(rec)
    t_r = record_beats(rec)["t_r"]
    t_rr, rr, corr = clean_rr(t_r)
    ect = np.r_[False, corr]
    lab = load_apnea_labels(rec)
    q = minute_quality(t_rr, corr, len(lab))
    series = {"RR": resample_uniform(t_rr, rr, FS_U)}
    for nombre, kw in VARIANTES.items():
        series[nombre] = resample_uniform(*beat_edr(ecg, t_r, fs, exclude=ect, hampel=True, **kw), FS_U)
    resp = load_respiration(rec) if rec in RESP_RECORDS else None
    filas = []
    for nombre, (t, v) in series.items():
        fila = {"record": rec, "variante": nombre}
        P, L = potencia_por_minuto(t, v, lab, q)
        if min((L == 1).sum(), (L == 0).sum()) >= MIN_MINUTES_PER_CLASS:
            fila["B"] = mannwhitneyu(P[L == 1], P[L == 0]).statistic / ((L == 1).sum() * (L == 0).sum())
        if resp is not None:
            r, fr = resp
            idx = np.rint(t * FS_U).astype(int)
            a1, a2 = [], []
            for canal in ("Resp C", "Resp A", "Resp N"):
                r2 = downsample(r[canal], fr, FS_U)
                ok = idx < len(r2)
                a1.append(np.nanmedian(validate_edr(v[ok], r2[idx[ok]], FS_U, seg_s=RESP_COH_SEG_S)))
                e = downsample(envolvente(r[canal], fr), fr, FS_U)
                f_, pxy = csd(v[ok], e[idx[ok]], fs=FS_U, nperseg=NSEG)
                _, pvv = welch(v[ok], fs=FS_U, nperseg=NSEG)
                _, pee = welch(e[idx[ok]], fs=FS_U, nperseg=NSEG)
                mb = (f_ >= BAND[0] - 1e-9) & (f_ <= BAND[1] + 1e-9)
                a2.append((np.abs(pxy[mb]) ** 2 / (pvv[mb] * pee[mb])).mean())
            fila["A1"] = np.mean(a1)
            if (lab == 1).sum() >= 100:
                fila["A2"] = np.mean(a2)
        filas.append(fila)
    return filas


if __name__ == "__main__":
    setup()
    split = pd.read_csv(SPLIT_CSV)
    dev = split[split.set == "dev"].record.tolist()
    with ProcessPoolExecutor(4) as ex:
        ev = pd.DataFrame([f for fs_ in ex.map(evaluar, dev) for f in fs_])

    medias = ev.groupby("variante")[list(MEDIDAS)].mean().loc[["RR", *VARIANTES]]
    print(medias.round(3))
    filas_g = []
    for k in MEDIDAS:
        w = ev.pivot(index="record", columns="variante", values=k).dropna()
        for otra in list(VARIANTES)[1:]:
            filas_g.append({"medida": k, "área contra": otra, "gana el área": f"{int((w['Área del QRS'] > w[otra]).sum())}/{len(w)}"})
    gana = pd.DataFrame(filas_g)
    print(gana.to_string(index=False))

    fig, axs = plt.subplots(1, 3, figsize=(9.6, 3.5), sharey=True)
    nombres = list(VARIANTES)
    ys = np.arange(len(nombres))[::-1]
    titulos = {"A1": "A1 · ¿Sigue cada respiración?", "A2": "A2 · ¿Sigue el ciclo de la apnea?", "B": "B · ¿Separa los minutos con apnea?"}
    for ax, (k, (_, xlabel)) in zip(axs, MEDIDAS.items()):
        n_reg = ev.loc[ev.variante == "RR", k].notna().sum()
        ax.axvline(medias.loc["RR", k], color=APNEA, ls="--", lw=0.9)
        for y, v_ in zip(ys, nombres):
            vals = ev.loc[ev.variante == v_, k].dropna()
            es_area = v_ == "Área del QRS"
            jit = np.random.default_rng(0).uniform(-0.14, 0.14, len(vals))
            ax.scatter(vals, y + jit, s=11 if es_area else 8, color=NORMAL if es_area else GRIS, alpha=0.75, lw=0)
            m = vals.mean()
            ax.plot([m, m], [y - 0.3, y + 0.3], color="black" if es_area else "#555555", lw=2.4 if es_area else 1.4)
            ax.text(m, y + 0.34, f"{m:.3f}".replace(".", ","), ha="center", va="bottom", fontsize=7.5,
                    fontweight="bold" if es_area else "normal")
        g = gana[gana.medida == k].set_index("área contra")["gana el área"]
        ax.set_title(titulos[k], fontsize=9)
        ax.set_xlabel(f"{xlabel} · {n_reg} registros\nárea mejor que amplitud R: {g['Amplitud del pico R']}"
                      f" · que deriva: {g['Deriva de la línea de base']}", fontsize=7.5)
        ax.set_ylim(ys[-1] - 0.7, ys[0] + 0.85)
    axs[0].set_yticks(ys)
    axs[0].set_yticklabels(nombres, fontsize=8.5)
    axs[0].get_yticklabels()[0].set_fontweight("bold")
    axs[2].axvline(0.5, color=GRIS, ls=":", lw=0.7)
    axs[0].text(medias.loc["RR", "A1"] + 0.01, ys[-1] - 0.55, "RR (referencia)", color=APNEA, fontsize=7)
    fig.suptitle("Por qué la EDR se mide con el área del QRS", fontsize=11, fontweight="bold", x=0.02, ha="left")
    fig.tight_layout()
    print(save(fig, "03_area_qrs"))
