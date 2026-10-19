"""Constantes del proyecto: rutas, base de datos, partición y bandas."""
from pathlib import Path

# --- Rutas ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"          # no se versiona (ver .gitignore)
SPLIT_CSV = DATA_DIR / "split.csv"  # se versiona una sola vez
RESULTS_DIR = ROOT / "results"

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

# Registros que se excluyen del análisis, con el motivo.
EXCLUDED = {
    "c05": "Misma grabación que c06 (c05 empieza 80 s después, nota de PhysioNet "
           "2013). Se conserva c06 para no contar dos veces al mismo sujeto.",
}

# --- Partición -----------------------------------------------------------
SEED = 2026
TEST_FRAC = 0.30

# --- Bandas espectrales (Hz) ---------------------------------------------
BANDS = {
    "VLF": (0.01, 0.04),
    "LF": (0.04, 0.15),
    "HF": (0.15, 0.40),
}
