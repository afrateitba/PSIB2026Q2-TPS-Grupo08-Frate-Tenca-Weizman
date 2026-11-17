# PSIB2026Q2-TPS — Grupo 08 — Frate, Tenca, Weizman

**Detección de apnea del sueño minuto a minuto con un ECG de una derivación**

Trabajo práctico de señales de Procesamiento de Señales e Imágenes Biomédicas (ITBA, 2026 Q2). Versión del recuperatorio.

## Objetivo e hipótesis

Detectar, minuto a minuto y solo con el ECG, si hay apnea del sueño. Se usa una feature y un umbral, sin aprendizaje automático. El detalle está en [`docs/objetivos_hipotesis.md`](docs/objetivos_hipotesis.md).

**Hipótesis H.** El ciclo de pausa y recuperación de cada apnea (20–100 s) aumenta la potencia de la serie RR y de la respiración derivada del ECG (EDR) en la banda de 0,01–0,05 Hz. De ahí salen tres predicciones:
- **(a)** Dentro de cada noche, la potencia del RR es mayor en los minutos con apnea.
- **(b)** Entre noches, el nivel nocturno de la potencia de la EDR crece con la cantidad de apnea.
- **(c)** Con la feature C = potencia del RR del minuto + nivel nocturno de la EDR, ambos estandarizados, un único umbral fijado en desarrollo clasifica los minutos de personas nuevas.

## El pipeline, paso por paso

Cada notebook es un paso, usa lo que dejó el anterior y termina con una tabla de lo que se lleva el siguiente. Todo se desarrolla con los registros de desarrollo. **Test no se usó para nada**: se evalúa una sola vez, al final.

| Notebook | Qué hace | Qué deja |
|---|---|---|
| [`01_base_y_exploracion`](notebooks/01_base_y_exploracion.ipynb) | Base de datos, categorías A/B/C, partición por persona (cada decisión verificada), etiquetas, señales en tiempo y frecuencia, artefactos, qué cambia con la apnea | Requisitos del filtro; la banda 0,01–0,05 Hz, medida en los datos |
| [`02_filtro_y_latidos`](notebooks/02_filtro_y_latidos.ipynb) | Filtro 0,5–45 Hz diseñado con una especificación medida, detector de QRS propio (Pan-Tompkins con cinco mejoras), refinamiento del pico R, limpieza de la serie RR | Serie RR limpia |
| [`03_edr_wiener`](notebooks/03_edr_wiener.ipynb) | Por qué el QRS cambia con la respiración, medidas posibles, EDR contra la respiración real y durante la apnea, latidos como realizaciones y filtro de Wiener, elección de la variante, EDR relativa | EDR: área del QRS sobre el ECG filtrado con Wiener, sin ectópicos ni atípicos, relativa al tamaño del QRS |
| [`04_feature_y_detector`](notebooks/04_feature_y_detector.ipynb) | Métricas y niveles de análisis, qué mide cada señal, la feature C y su peso por validación cruzada, otras combinaciones, umbral de Youden, resultados por noche, dónde falla, confianza según el movimiento, robustez | Parámetros congelados en [`docs/parametros_test.json`](docs/parametros_test.json) |
| [`05_test`](notebooks/05_test.ipynb) | Evaluación única en test (20 registros, 10 personas) con los parámetros congelados: predicciones P1–P3, C contra F y RR, confianza y resultados por noche | **H se sostiene**: P1 0,87, P2 0,66, P3 0,85, los tres con IC que cumplen el criterio. Exactitud 0,78. Resultados en [`docs/resultados_test.json`](docs/resultados_test.json) |
| [`06_posterior_test`](notebooks/06_posterior_test.ipynb) | Análisis posterior, descriptivo, de por qué falla en algunas noches de test. No cambia `05` | Los errores son por noche: siguen al nivel de la EDR que no corresponde a la apnea y al nivel del RR de la persona. Una persona con ritmo muy irregular queda casi toda excluida |

**Detector final.** Para cada minuto se toma una ventana de 240 s centrada en él. En esa ventana se estiman por Welch (3 × 120 s, Hann) la potencia del RR y la de la EDR en 0,01–0,05 Hz:

C(m) = (P_RR(m) − μ₁)/σ₁ + w · (mediana de P_EDR en la noche − μ₂)/σ₂, con w = 1.

El minuto es apnea si C > 0,489 (umbral de Youden). La confianza (alta, media o baja) depende del movimiento en la ventana.

## Documentos

- [`docs/objetivos_hipotesis.md`](docs/objetivos_hipotesis.md): objetivo general, objetivos específicos, hipótesis, predicciones, parámetros fijados, alcance y limitaciones.
- [`docs/decisiones.md`](docs/decisiones.md): cada ventana, umbral y parámetro, con su justificación (datos, bibliografía o física) y dónde se muestra.
- [`docs/auditoria_decisiones.md`](docs/auditoria_decisiones.md): las 88 decisiones del proyecto, con el tipo de justificación (datos, bibliografía, física) y su estado: 86 justificadas y 2 limitaciones.
- [`docs/referencias.md`](docs/referencias.md): todas las fuentes citadas, con DOI o página oficial verificados en Crossref, doi.org y PubMed (se regenera con `python scripts/verificar_referencias.py`).
- [`docs/revision_devolucion.md`](docs/revision_devolucion.md): cada observación de la devolución, dónde se resolvió y qué falta.
- [`docs/plan_recuperatorio.md`](docs/plan_recuperatorio.md): plan de trabajo y regla de no tocar test.
- [`docs/parametros_test.json`](docs/parametros_test.json): lo que queda fijo para test.
- `docs/v1/`: documentos de la primera versión, como historia del trabajo.

## Datos

[Apnea-ECG Database](https://physionet.org/content/apnea-ecg/1.0.0/) (PhysioNet; Penzel et al., 2000). Tiene 70 registros nocturnos de ECG a 100 Hz con conversor de 12 bits y una etiqueta apnea/normal por minuto. Las señales respiratorias de 8 registros se usan solo para validar la EDR.

- Tres pares de registros son la misma grabación: c05/c06 (documentado por PhysioNet), x22/x35 y x33/x34. Se excluyen c05, x22 y x33, y quedan 67 registros de 29 personas.
- La partición es por persona (`data/split.csv`). Desarrollo tiene 47 registros de 19 personas y test 20 registros de 10 personas. Está estratificada por categoría y balanceada en minutos de apnea, con semilla 2026. Las personas con respiración registrada van a desarrollo.

## Instalación y uso

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/download_data.py    # ~450 MB en data/raw/
pytest
```

`data/split.csv` ya está versionado: `scripts/make_split.py` no se vuelve a correr.

Para ejecutar un notebook con sus salidas (en orden, `01` a `04`):

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/02_filtro_y_latidos.ipynb
```

## Interfaz gráfica

```bash
streamlit run app/visor.py
```

Se abre en el navegador un visor que aplica a una noche el detector tal como quedó fijado en desarrollo:
- **La noche**: C de cada minuto con el umbral y el término de la EDR, las tiras de etiqueta, decisión y confianza, y la sensibilidad, especificidad y exactitud de esa noche.
- **Un minuto**: se elige con el deslizador, o saltando entre los minutos mal clasificados. Muestra el ECG con los picos R, la serie RR y la EDR en su ventana de 240 s, sus espectros con la banda, y el cálculo de C paso a paso.

Muestra solo los registros de desarrollo. Los de test quedan ocultos hasta la evaluación final; después se pueden ver con `VISOR_INCLUIR_TEST=1 streamlit run app/visor.py`. Cada noche tarda unos segundos en procesarse la primera vez.

Las figuras de los notebooks se guardan en `informe/figuras/`. En Windows, `jupyter` tiene que ser el del `.venv`; si la consola falla con los acentos, usar `python -X utf8`.

## Código

Las constantes (rutas, filtro, parámetros del detector de QRS y de la EDR) están en `src/config.py`, con el notebook que justifica cada una.

| Etapa (consigna) | Módulo | Notebook |
|---|---|---|
| Lectura de la base | `src/data.py` | `01` |
| Duplicados y partición por persona | `src/duplicates.py`, `src/split.py` | `01` |
| Calidad de la señal (saturación, tramos planos) | `src/preprocessing/quality.py` | `01` |
| Filtro convencional | `src/preprocessing/filters.py` | `02` |
| Detección de QRS | `src/qrs/pan_tompkins.py`, `src/qrs/beats.py` | `02` |
| Cuantización y refinamiento del pico R | `src/qrs/quantization.py`, `src/qrs/pan_tompkins.py` | `02` |
| Limpieza de la serie RR | `src/qrs/rr_clean.py` | `02` |
| Realizaciones y filtro de Wiener | `src/preprocessing/wiener.py` | `03` |
| EDR | `src/features/edr.py` | `03` |
| Series por registro (RR y EDR a 2 Hz) | `src/features/build.py` | `03`, `04` |
| Segmentación (ventana centrada) | `src/features/windows.py` | `01`, `04` |
| Espectros de Welch y espectro cruzado | `src/features/coupling.py` | `01`, `03`, `04` |
| Periodograma de Lomb (comparación) | `src/features/lomb.py` | `04` |
| **Detector**: tabla por minuto, C, umbral y confianza | `src/features/detector.py` | `04` |
| Figuras | `src/viz/plots.py` | todos |
| Interfaz gráfica | `app/visor.py` (pantalla), `src/viz/visor_data.py` (datos) | — |

**Primera versión.** Lo que no usa el pipeline actual quedó como historia del trabajo, marcado en el encabezado de cada módulo:
- los notebooks de `notebooks/v1/`;
- los paquetes `src/evaluation/` y `src/stats/`;
- los módulos `src/features/hrv_time.py`, `postprocess.py` y `variants.py`;
- sus tests.

## Reglas de trabajo

- Toda decisión se toma con los registros de desarrollo y se justifica con un análisis de las señales: una figura y un número.
- El 30 % de test no se mira (ni señales, ni etiquetas, ni resultados) hasta la evaluación final, que se corre una sola vez con los parámetros de `docs/parametros_test.json`.
- `pytest` tiene que pasar antes de cada commit. `tests/test_consistencia.py` verifica que ventanas, bandas y umbrales estén definidos en un solo lugar (`src/config.py`, `src/features/detector.py`) y que ningún notebook los escriba a mano.
- `data/split.csv` no se modifica.
