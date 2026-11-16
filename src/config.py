"""Constantes del proyecto: rutas, base de datos, partición y bandas."""
from pathlib import Path

# --- Rutas ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"          # no se versiona (ver .gitignore)
SPLIT_CSV = DATA_DIR / "split.csv"  # se versiona una sola vez
RESULTS_DIR = ROOT / "results"   # primera versión (cachés de notebooks/v1)

# --- Base de datos -------------------------------------------------------
PHYSIONET_URL = "https://physionet.org/files/apnea-ecg/1.0.0/"
FS = 100                    # Hz
SAMPLES_PER_MIN = 60 * FS   # una etiqueta apnea/normal por minuto

LEARNING_RECORDS = (
    [f"a{i:02d}" for i in range(1, 21)]
    + [f"b{i:02d}" for i in range(1, 6)]
    + [f"c{i:02d}" for i in range(1, 11)]
)
TEST_RECORDS = [f"x{i:02d}" for i in range(1, 36)]
ALL_RECORDS = LEARNING_RECORDS + TEST_RECORDS

# Registros con respiración real (a01r ... c03r): solo para validar EDR/Wiener.
RESP_RECORDS = ["a01", "a02", "a03", "a04", "b01", "c01", "c02", "c03"]

# Pares de registros que son la misma grabación: muestras idénticas, con un
# desfase. c05/c06 lo documenta PhysioNet (nota de 2013); x22/x35 y x33/x34 se
# encontraron comparando las señales (src/duplicates.py). En los tres pares,
# additional-information.txt les asigna perfiles distintos.
SAME_RECORDING = [("c05", "c06"), ("x22", "x35"), ("x33", "x34")]

# Registros que se excluyen del análisis, con el motivo. De cada par de
# SAME_RECORDING se conserva la grabación que empieza antes.
EXCLUDED = {
    "c05": "Misma grabación que c06; c05 empieza 80 s después (nota de PhysioNet 2013).",
    "x22": "Misma grabación que x35; x22 empieza 40 s después.",
    "x33": "Misma grabación que x34; x33 empieza 70 s después.",
}

# --- Partición -----------------------------------------------------------
SEED = 2026
TEST_FRAC = 0.30
# Diferencia máxima entre la fracción de minutos de apnea de test y la de dev.
MAX_APNEA_DIFF = 0.02

# --- Filtro del ECG ------------------------------------------------------
# Pasabanda Butterworth (corte bajo Hz, corte alto Hz, orden), aplicado ida y
# vuelta. Justificado en notebooks/02_filtro_y_latidos.ipynb, sección 1.
ECG_FILTER = (0.5, 45.0, 3)

# --- Bandas de HRV (Hz). Primera versión: el pipeline actual usa la banda
# 0,01-0,05 Hz de src/features/detector.py (BAND), medida en notebook 01.
BANDS = {
    "VLF": (0.01, 0.04),
    "LF": (0.04, 0.15),
    "HF": (0.15, 0.40),
}


# --- Detección de QRS (Pan-Tompkins a 100 Hz) -----------------------------
# Valores clásicos de Pan y Tompkins (1985), en segundos para que no dependan
# de fs. Se verifican en notebooks/02_filtro_y_latidos.ipynb, sección 2.
QRS_BAND = (5.0, 15.0, 2)      # pasabanda (Hz, Hz, orden), ida y vuelta
QRS_INTEGRATION_S = 0.150      # ventana de integración
QRS_REFRACTORY_S = 0.200       # período refractario entre dos QRS
QRS_TWAVE_S = 0.360            # un pico más cerca que esto puede ser onda T
QRS_SLOPE_WIN_S = 0.075        # ventana para medir la pendiente máxima
QRS_SEARCHBACK = 1.66          # hueco (en RR medios) que dispara la búsqueda hacia atrás
QRS_LOCATE_S = 0.080           # búsqueda del pico R alrededor del QRS detectado
QRS_TOLERANCE_S = 0.10         # tolerancia para emparejar con las .qrs

# Mejoras del detector propio (notebooks/02_filtro_y_latidos.ipynb). Cada una
# corrige un error que se vio en los registros de desarrollo.
QRS_PROMINENCE_MIN = 0.5       # un QRS es un pulso aislado: prominencia / altura en la señal integrada
QRS_FLOOR_FRAC = 0.05          # piso: fracción de la energía mediana de los QRS del registro
QRS_TWAVE_RR_FRAC = 0.5        # la ventana de onda T crece con el RR: máx(QRS_TWAVE_S, 0,5 RR medio)
QRS_TEMPLATE_CORR_MIN = 0.5    # en esa ventana, correlación mínima con la forma de los últimos QRS
QRS_HF_CUTOFF = 20.0           # Hz: la onda T casi no tiene energía por encima
QRS_HF_RATIO_MIN = 0.3         # en esa ventana, energía > 20 Hz mínima respecto del QRS anterior
QRS_TEMPLATE_N = 8             # latidos con que se arma la forma de referencia

# --- EDR (notebooks/03_edr_wiener.ipynb) -----------------------------------
# Área del QRS sobre el ECG filtrado con Wiener, sin latidos ectópicos ni atípicos.
EDR_EXCLUDE_ECTOPIC = True     # descarta los latidos que la limpieza del RR corrige
EDR_HAMPEL = True              # descarta los latidos atípicos (filtro de Hampel)
EDR_WIENER = True              # mide el QRS sobre el ECG filtrado con Wiener
EDR_RELATIVE = True            # divide el área por el tamaño típico del QRS (mediana del área sin signo; notebook 03, sección 7)
