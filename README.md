# PSIB2026Q2-TPS — Grupo 08 — Frate Tenca Weizman

**Acoplamiento cardiopulmonar derivado del ECG como criterio de detección de apnea del sueño**

Trabajo práctico de señales de Procesamiento de Señales e Imágenes Biomédicas (ITBA, 2026 Q2).

## Objetivo

Determinar, minuto a minuto y usando solo el ECG, si hay apnea del sueño. El criterio de decisión sale de análisis estadístico y puntos de corte; no se usa aprendizaje automático.

- **H1:** durante la apnea aparece un acoplamiento lento (0,01–0,1 Hz) entre la serie RR y el EDR (respiración derivada del ECG), dentro de cada sujeto; el acoplamiento respiratorio no desaparece. Se sostiene en desarrollo (`notebooks/03_E2_h1.ipynb`).
- **H2:** la feature conjunta F detecta la apnea mejor que la mejor feature de HRV (potencia VLF del RR con Lomb). Se prueba en test con el plan de `docs/plan_test.md`.

**Detector:** F = log de la potencia cruzada RR–EDR promediada en 0,01–0,05 Hz, en una ventana de 4 min centrada en cada minuto, con el EDR por área del QRS. Un minuto es apnea si F supera un umbral de Youden fijado en desarrollo.

**Documentos:**
- [`docs/esquema_v3.md`](docs/esquema_v3.md): pipeline vigente, qué se decidió y con qué datos, criterios de trabajo y lo que falta.
- [`docs/plan_test.md`](docs/plan_test.md): cómo y cuándo se evalúa en test.
- [`informe/informe.tex`](informe/informe.tex): el informe en LaTeX, con la bibliografía en `informe/referencias.bib` y las figuras en `informe/figuras/`. Se compila desde `informe/` con `latexmk -pdf informe.tex` (pdflatex y biber); también funciona en Overleaf.

## Datos

[Apnea-ECG Database](https://physionet.org/content/apnea-ecg/1.0.0/) (PhysioNet; Penzel et al., 2000): 70 registros nocturnos, ECG a 100 Hz con conversor de 12 bits, una etiqueta apnea/normal por minuto. Las señales respiratorias de 8 registros se usan solo para validar.

- Hay tres pares de registros que son la misma grabación: c05/c06 (documentado por PhysioNet), x22/x35 y x33/x34 (encontrados comparando las señales, `src/duplicates.py`). Se excluyen c05, x22 y x33; quedan 67 registros de 29 sujetos.
- Partición 70/30 por sujeto (`data/split.csv`): desarrollo 47 registros (19 sujetos), test 20 registros (10 sujetos). Está estratificada por categoría A/B/C y balanceada en minutos de apnea, con semilla fija. Los sujetos se infieren del perfil de cada registro (edad, sexo, altura, peso) y de las grabaciones duplicadas (`notebooks/01_verificacion_sujetos.ipynb`).
- Los sujetos con registros con respiración van siempre a desarrollo.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/download_data.py    # ~450 MB en data/raw/
pytest
```

`data/split.csv` ya está versionado: `scripts/make_split.py` no se vuelve a correr.

Para ejecutar un notebook con sus salidas:

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/07_filtro.ipynb
```

En Windows, `jupyter` tiene que ser el del `.venv` (agregar `.venv/Scripts` al PATH). Si la consola falla con los acentos, usar `python -X utf8`. Las verificaciones de las etapas toman los minutos de evaluación de la caché `results/e3/`, que no se versiona y se genera corriendo `notebooks/04_E3a_features.ipynb` (tarda bastante).

## Notebooks

| Notebook | Etapa | Resultado |
|---|---|---|
| `00_adquisicion` | 4.1 | 12 bits; el refinamiento parabólico del pico R se queda; calidad por registro; minutos con apnea contra AHI |
| `01_verificacion_sujetos` | partición | 3 grabaciones duplicadas; 67 registros de 29 sujetos |
| `02_E1_edr` | E1 | EDR por área del QRS (empatado con la deriva; lo resuelve E3) |
| `03_E2_h1` | E2 | H1 se sostiene, como un acoplamiento lento que se agrega |
| `04_E3a_features` | E3a / E4 | F = potencia cruzada RR–EDR en 0,01–0,05 Hz; HRV de referencia: VLF con Lomb |
| `05_E3a_descomposicion` | control | la coherencia no aporta para detectar |
| `06_E3b_postprocesado` | E3b | sin normalizar ni suavizar; ventana de 4 min |
| `07_filtro` | 4.2 | pasabanda 0,5–45 Hz, orden 3 |

Pendiente (ver `docs/esquema_v3.md`, sección 8): 4.3 detección QRS propia, 4.4 Wiener, política de minutos malos, umbrales, validación cruzada anidada y test.

## Estructura

| Tema de la consigna | Módulo |
|---|---|
| Adquisición | `src/data.py`, `src/preprocessing/quality.py`, `src/qrs/quantization.py` |
| Filtros convencionales | `src/preprocessing/filters.py` |
| Recorte en realizaciones + filtros óptimos | `src/preprocessing/wiener.py` |
| Detección QRS | `src/qrs/pan_tompkins.py`, `src/qrs/rr_clean.py` |
| Segmentación | `src/features/windows.py` |
| HRV | `src/features/hrv_time.py` |
| Periodograma de Lomb | `src/features/lomb.py` |
| Acoplamiento (aporte) | `src/features/edr.py`, `src/features/coupling.py`, `src/features/build.py`, `src/features/variants.py` |
| Análisis estadístico | `src/stats/` |
| Evaluación | `src/evaluation/metrics.py` |
| Figuras | `src/viz/plots.py`, `notebooks/` |

Las constantes del proyecto (rutas, filtro, bandas, semilla) están en `src/config.py`. Los resultados intermedios y las figuras van a `results/` y no se versionan.

## Flujo de trabajo

Los criterios completos están en `docs/esquema_v3.md`, sección 7. En resumen:

- Toda decisión se toma con datos de desarrollo y con reglas escritas en el notebook **antes** de correrlo. Si una regla cambia después de ver los datos, se declara como desvío.
- Una etapa obligatoria se adopta si F es no inferior a la versión vigente (δ = 0,02 en AUC por minuto y en acierto por registro).
- Una rama por bloque, integrada a `main` por pull request revisado por otro integrante. Commits chicos: primero las funciones con sus tests, y después el notebook con la decisión. `pytest` tiene que pasar antes de cada commit.
- `data/split.csv` no se modifica.
- El 30 % de test no se toca hasta la etiqueta `congelado-test`, y se usa una única vez (`docs/plan_test.md`).
