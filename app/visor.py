"""Visor de registros: el detector de apnea aplicado a una noche, minuto a minuto.

Uso, desde la raíz del repositorio:
    streamlit run app/visor.py

Muestra los registros de desarrollo. Los de test quedan ocultos hasta la
evaluación final; después se pueden ver con VISOR_INCLUIR_TEST=1.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.detector import BANDA_EFECTIVA as BAND, WINDOW_S  # noqa: E402
from src.viz.plots import APNEA, NORMAL  # noqa: E402
from src.viz.visor_data import (VERSIONES, analizar_noche, ecg_minuto, registros_visibles,  # noqa: E402
                                resumen_noche, ventana_minuto)

GRIS = "#B8B8B8"
CONF_COLOR = {"alta": "#3B8E5A", "media": "#E3B23C", "baja": "#C0392B"}
INCLUIR_TEST = os.environ.get("VISOR_INCLUIR_TEST") == "1"

st.set_page_config(page_title="Visor de apnea", layout="wide")


@st.cache_data(max_entries=3, show_spinner="Procesando la noche (detector de latidos, EDR y espectros)…")
def cargar(rec: str, version: str) -> dict:
    return analizar_noche(rec, version=version)


def tira(x, valores, colores: dict, nombre: str):
    """Una fila de colores, un rectángulo por minuto (para etiquetas, decisión y confianza)."""
    claves = list(colores)
    z = [[claves.index(v) if v in claves else np.nan for v in valores]]
    n = len(claves)
    escala = []
    for k, c in enumerate(colores.values()):
        escala += [(k / n, c), ((k + 1) / n, c)]
    return go.Heatmap(x=x, z=z, y=[nombre], colorscale=escala, zmin=-0.5, zmax=n - 0.5, showscale=False,
                      hoverinfo="skip")


# --- Barra lateral -------------------------------------------------------------
regs = registros_visibles(INCLUIR_TEST)
st.sidebar.title("Visor de apnea")
st.sidebar.caption("ECG de una derivación · Apnea-ECG · Grupo 8")
etiqueta_reg = {r.record: f"{r.record} · categoría {r.category} · {100 * r.apnea_minutes / r.n_minutes:.0f} % apnea"
                for r in regs.itertuples()}
rec = st.sidebar.selectbox("Registro", list(etiqueta_reg), format_func=etiqueta_reg.get,
                           index=list(etiqueta_reg).index("a03") if "a03" in etiqueta_reg else 0)
if not INCLUIR_TEST:
    st.sidebar.caption("Solo registros de desarrollo: test no se mira hasta la evaluación final.")

version = st.sidebar.radio("Detector", list(VERSIONES), format_func=VERSIONES.get)
an = cargar(rec, version)
tab, p = an["tabla"], an["params"]
CON_CONFIANZA = "confianza" in tab
minutos = tab["minute"].to_numpy()

errores = tab[tab["evaluado"] & (tab["decision"] != tab["label"])]["minute"].to_numpy()
if "minuto" not in st.session_state or st.session_state.get("rec") != rec:
    st.session_state.rec = rec
    st.session_state.minuto = int(errores[0]) if len(errores) else int(minutos[len(minutos) // 2])
st.sidebar.caption(f"Saltar entre los {len(errores)} minutos mal clasificados")
c1, c2 = st.sidebar.columns(2)
if c1.button("◀ anterior", disabled=not len(errores), width="stretch"):
    previos = errores[errores < st.session_state.minuto]
    st.session_state.minuto = int(previos[-1] if len(previos) else errores[-1])
if c2.button("siguiente ▶", disabled=not len(errores), width="stretch"):
    siguientes = errores[errores > st.session_state.minuto]
    st.session_state.minuto = int(siguientes[0] if len(siguientes) else errores[0])
minuto = st.sidebar.slider("Minuto", int(minutos.min()), int(minutos.max()), key="minuto")
if minuto not in set(minutos):
    minuto = int(minutos[np.argmin(np.abs(minutos - minuto))])
crudo = st.sidebar.checkbox("Mostrar también el ECG sin filtrar")

with st.sidebar.expander("Parámetros fijados en desarrollo"):
    st.markdown(f"""
- Banda: {BAND[0]:.3f}–{BAND[1]:.2f} Hz (ciclos de 20 a 60 s) · ventana de {WINDOW_S} s
- μ₁ = {p['mu1']:.3f}, σ₁ = {p['s1']:.3f}
- μ₂ = {p['mu2']:.3f}, σ₂ = {p['s2']:.3f}, w = {p['w']:g}
- Umbral: C > {p['umbral']:.3f}
""")
    if CON_CONFIANZA:
        st.markdown(f"- Confianza: movimiento relativo > {p['cortes_confianza_mov_rel'][0]:.2f} (media), "
                    f"> {p['cortes_confianza_mov_rel'][1]:.2f} (baja)")
    else:
        st.markdown("- Sin medida de confianza: salió del detector en el notebook 07.")

# --- La noche ---------------------------------------------------------------------
st.header(f"Registro {rec}")
res = resumen_noche(tab)
k = st.columns(6)
k[0].metric("Minutos evaluados", f"{res['evaluados']} / {res['minutos']}")
k[1].metric("Apnea real", f"{res['apnea_real']:.0f} %")
k[2].metric("Apnea estimada", f"{res['apnea_estimada']:.0f} %")
coma = lambda txt: txt.replace(".", ",")
fmt = lambda v: "—" if np.isnan(v) else coma(f"{v:.2f}")
k[3].metric("Sensibilidad", fmt(res["sensibilidad"]))
k[4].metric("Especificidad", fmt(res["especificidad"]))
k[5].metric("Exactitud", fmt(res["exactitud"]))

with st.expander("Cómo leer el visor"):
    st.markdown(f"""
Para cada minuto se toma una ventana de {WINDOW_S} s centrada en él. En esa ventana se calcula la potencia de la serie RR y de la
respiración derivada del ECG (EDR) entre {BAND[0]:.3f} y {BAND[1]:.2f} Hz (ciclos de 20 a 60 s), la banda del ciclo de la apnea. La feature combina dos términos:

- **término del RR**: la potencia del RR en ese minuto, estandarizada. Cambia de un minuto a otro y dice **cuándo** hay apnea en la noche.
- **término de la EDR**: el nivel de la potencia de la EDR en toda la noche (su mediana), estandarizado. Es el mismo para todos los minutos y dice **cuánta** apnea tiene la noche: corre la curva de C hacia arriba o hacia abajo.

Un minuto se marca como apnea si C supera el umbral.
Los minutos grises no se evalúan: no tienen etiqueta o más del 20 % de sus latidos se corrigieron.
""")
    if CON_CONFIANZA:
        st.markdown("En la versión evaluada en test, la **confianza** baja cuando hay mucho movimiento en la ventana, "
                    "respecto de lo habitual en esa noche.")

horas = tab["minute"].to_numpy() / 60
etiq = np.where(tab["label"] == 1, "apnea", np.where(tab["label"] == 0, "normal", "sin etiqueta"))
deci = np.where(~tab["evaluado"], "no evaluado", np.where(tab["decision"] == 1, "apnea", "normal"))
filas = 4 if CON_CONFIANZA else 3
fig = make_subplots(rows=filas, cols=1, shared_xaxes=True, vertical_spacing=0.025,
                    row_heights=[0.09, 0.09, 0.73, 0.09] if CON_CONFIANZA else [0.1, 0.1, 0.8])
fig.add_trace(tira(horas, etiq, {"normal": NORMAL, "apnea": APNEA, "sin etiqueta": GRIS}, "etiqueta"), 1, 1)
fig.add_trace(tira(horas, deci, {"normal": NORMAL, "apnea": APNEA, "no evaluado": GRIS}, "detector"), 2, 1)
for nombre, color in (("apnea", APNEA), ("normal", NORMAL), ("sin etiqueta", GRIS)):
    sel = etiq == nombre
    fig.add_trace(go.Scatter(x=horas[sel], y=tab["C"].to_numpy()[sel], mode="markers", marker=dict(color=color, size=4),
                             name=f"C · minuto {nombre}", customdata=minutos[sel],
                             hovertemplate="minuto %{customdata}<br>C = %{y:.2f}<extra></extra>"), 3, 1)
fig.add_trace(go.Scatter(x=horas, y=tab["C"], mode="lines", line=dict(color="black", width=0.6), showlegend=False,
                         hoverinfo="skip"), 3, 1)
fig.add_hline(y=p["umbral"], line=dict(color="black", dash="dash", width=1), row=3, col=1,
              annotation_text=coma(f"umbral {p['umbral']:.2f}"), annotation_position="top left")
fig.add_hline(y=float(tab["termino_edr"].iloc[0]), line=dict(color=APNEA, dash="dot", width=1), row=3, col=1,
              annotation_text="término de la EDR (constante en la noche)", annotation_position="bottom right")
if CON_CONFIANZA:
    fig.add_trace(tira(horas, tab["confianza"], CONF_COLOR, "confianza"), 4, 1)
fig.add_vline(x=minuto / 60, line=dict(color="#555", width=1.5))
fig.update_yaxes(title_text="C", row=3, col=1)
fig.update_xaxes(title_text="horas desde el inicio", row=filas, col=1)
fig.update_layout(height=470, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=1.08))
st.plotly_chart(fig, width="stretch")
st.caption("Tiras de etiqueta y detector: azul normal, naranja apnea, gris sin etiqueta o no evaluado. "
           + ("Confianza: verde alta, amarillo media, rojo baja. " if CON_CONFIANZA else "")
           + "La línea vertical marca el minuto elegido.")

# --- Un minuto ----------------------------------------------------------------------
v = ventana_minuto(an, minuto)
f_ = v["fila"]
st.subheader(f"Minuto {minuto} ({minuto // 60} h {minuto % 60:02d} min)")
etq = {1: "apnea", 0: "normal"}.get(int(f_["label"]), "sin etiqueta")
dec = "apnea" if f_["decision"] else "normal"
if not f_["evaluado"]:
    st.info("Este minuto no se evalúa: no tiene etiqueta o tiene más del 20 % de latidos corregidos.")
else:
    conf = f" (confianza {f_['confianza']})" if CON_CONFIANZA else ""
    if etq == dec:
        st.success(f"Acierto: el detector dice **{dec}** y la etiqueta es **{etq}**{conf}.")
    else:
        tipo = "falso positivo" if dec == "apnea" else "falso negativo"
        st.error(f"Error ({tipo}): el detector dice **{dec}** y la etiqueta es **{etq}**{conf}.")

tex = lambda v: f"{v:.2f}".replace(".", "{,}")
st.latex(r"C = \underbrace{\frac{P_{RR} - \mu_1}{\sigma_1}}_{%s} + w\,\underbrace{\frac{\tilde P_{EDR} - \mu_2}{\sigma_2}}_{%s}"
         r" = %s \;%s\; %s" % (tex(f_["termino_rr"]), tex(f_["termino_edr"]), tex(f_["C"]),
                                 ">" if f_["decision"] else r"\le", tex(p["umbral"])))
m = st.columns(4)
m[0].metric("P_RR (log₁₀ potencia del RR)", coma(f"{f_['P_RR']:.2f}"))
m[1].metric("Nivel de la EDR en la noche", coma(f"{f_['EDR_noche']:.2f}"))
m[2].metric("P_EDR del minuto (no entra en C)", coma(f"{f_['P_EDR']:.2f}"))
m[3].metric("Movimiento relativo", coma(f"{f_['mov_rel']:+.2f}"))

izq, der = st.columns([3, 2])
with izq:
    e = ecg_minuto(an, minuto)
    fe = go.Figure()
    if crudo:
        fe.add_trace(go.Scatter(x=e["t"] - e["t"][0], y=e["crudo"], line=dict(color=GRIS, width=0.8), name="sin filtrar"))
    fe.add_trace(go.Scatter(x=e["t"] - e["t"][0], y=e["filtrado"], line=dict(color="black", width=0.8),
                            name="filtrado 0,5–45 Hz"))
    fe.add_trace(go.Scatter(x=e["t_r"] - e["t"][0], y=e["amp_r"], mode="markers", marker=dict(color=APNEA, size=6),
                            name="pico R"))
    fe.update_layout(title="ECG del minuto", height=260, margin=dict(l=10, r=10, t=40, b=10),
                     xaxis_title="s", yaxis_title="mV", legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(fe, width="stretch")

    fw = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08)
    tw = v["t"] - v["inicio"]
    fw.add_trace(go.Scatter(x=tw, y=v["rr"], line=dict(color="black", width=1), name="RR"), 1, 1)
    fw.add_trace(go.Scatter(x=tw, y=v["edr"], line=dict(color=APNEA, width=1), name="EDR"), 2, 1)
    for r_ in (1, 2):
        fw.add_vrect(x0=WINDOW_S / 2 - 30, x1=WINDOW_S / 2 + 30, fillcolor="#999", opacity=0.15, line_width=0,
                     row=r_, col=1)
    fw.update_yaxes(title_text="RR (s)", row=1, col=1)
    fw.update_yaxes(title_text="EDR (relativa)", row=2, col=1)
    fw.update_xaxes(title_text=f"s dentro de la ventana de {WINDOW_S} s (sombreado: el minuto)", row=2, col=1)
    fw.update_layout(title="Serie RR y EDR en la ventana", height=330, margin=dict(l=10, r=10, t=40, b=10),
                     showlegend=False)
    st.plotly_chart(fw, width="stretch")

with der:
    fs_ = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=(coma(f"Espectro del RR · P_RR = {v['P_RR']:.2f}"),
                                        coma(f"Espectro de la EDR · P_EDR = {v['P_EDR']:.2f}")))
    sel = (v["f"] > 0) & (v["f"] <= 0.5)
    fs_.add_trace(go.Scatter(x=v["f"][sel], y=v["s_rr"][sel], mode="lines+markers", marker=dict(size=3),
                             line=dict(color="black", width=1.2)), 1, 1)
    fs_.add_trace(go.Scatter(x=v["f"][sel], y=v["s_edr"][sel], mode="lines+markers", marker=dict(size=3),
                             line=dict(color=APNEA, width=1.2)), 2, 1)
    for r_ in (1, 2):
        fs_.add_vrect(x0=BAND[0], x1=BAND[1], fillcolor=NORMAL, opacity=0.15, line_width=0, row=r_, col=1)
        fs_.update_yaxes(type="log", exponentformat="power", row=r_, col=1)
        fs_.update_xaxes(type="log", tickvals=[0.01, 0.02, 0.05, 0.1, 0.25, 0.5],
                         ticktext=["0,01", "0,02", "0,05", "0,1", "0,25", "0,5"], row=r_, col=1)
    fs_.update_xaxes(title_text="Hz, escala logarítmica (sombreado: banda de la apnea)", row=2, col=1)
    fs_.update_layout(height=590, margin=dict(l=10, r=10, t=40, b=10), showlegend=False)
    st.plotly_chart(fs_, width="stretch")
    st.caption("Welch: 3 segmentos de 120 s, ventana de Hann, 50 % de solapamiento. P es el log₁₀ del promedio "
               "del espectro en la banda (los puntos son la grilla k/120 Hz: en la banda caen 5). "
               "La respiración aparece como un pico cerca de 0,25 Hz.")
