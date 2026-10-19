# PSIB2026Q2-TPS — Grupo 08 — Frate Tenca Weizman

**Acoplamiento cardiopulmonar derivado del ECG como criterio de detección de apnea del sueño**

Trabajo práctico de señales de Procesamiento de Señales e Imágenes Biomédicas (ITBA, 2026 Q2).

## Objetivo

Determinar, minuto a minuto y usando solo el ECG, si hay apnea del sueño. El criterio de decisión sale de análisis estadístico y puntos de corte; no se usa aprendizaje automático.

- **H1:** durante la apnea, la coherencia entre la serie RR y el EDR (respiración derivada del ECG) se desplaza de la banda respiratoria (HF, 0,15–0,4 Hz) a VLF/LF (0,01–0,15 Hz), y el cociente CR = coh(VLF+LF) / coh(HF) aumenta dentro de cada sujeto.
- **H2:** CR separa los minutos con y sin apnea mejor que el LF/HF clásico de HRV.

## Datos

[Apnea-ECG Database](https://physionet.org/content/apnea-ecg/1.0.0/) (PhysioNet; Penzel et al., 2000): 70 registros nocturnos, ECG a 100 Hz, una etiqueta apnea/normal por minuto. Las señales respiratorias de 8 registros se usan solo para validar.

- Partición 70/30 por registro, estratificada por categoría A/B/C, con semilla fija (`data/split.csv`).
- Los registros con respiración van siempre a desarrollo.
- Se excluye c05: es la misma grabación que c06.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/download_data.py    # ~450 MB en data/raw/
python scripts/make_split.py       # solo la primera vez; split.csv se versiona
pytest
```

## Estructura

| Tema de la consigna | Módulo |
|---|---|
| Adquisición | `src/data.py` |
| Filtros convencionales | `src/preprocessing/filters.py` |
| Recorte en realizaciones + filtros óptimos | `src/preprocessing/wiener.py` |
| Detección QRS | `src/qrs/pan_tompkins.py`, `src/qrs/rr_clean.py` |
| Segmentación | `src/features/windows.py` |
| HRV | `src/features/hrv_time.py` |
| Periodograma de Lomb | `src/features/lomb.py` |
| Acoplamiento (aporte) | `src/features/edr.py`, `src/features/coupling.py` |
| Análisis estadístico | `src/stats/` |
| Evaluación | `src/evaluation/metrics.py` |
| Figuras | `src/viz/plots.py`, `notebooks/` |

Las constantes del proyecto (rutas, bandas, semilla) están en `src/config.py`. Los resultados intermedios van a `results/` y no se versionan.

## Flujo de trabajo

- Una rama por bloque: `latidos`, `senal`, `espectral`. Se integra a `main` por pull request revisado por otro integrante.
- Commits chicos y frecuentes, con mensaje en imperativo (por ejemplo, "Agrega interpolación parabólica del pico R").
- `data/split.csv` no se modifica después del primer commit.
- El 30 % de test se usa una única vez, para la evaluación final.
