"""Descarga la Apnea-ECG Database a data/raw/ (~450 MB).

Uso:  python scripts/download_data.py               # todo
      python scripts/download_data.py a01 c01       # solo algunos registros
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data import download_database  # noqa: E402

if __name__ == "__main__":
    records = sys.argv[1:] or None
    missing = download_database(records)
    if missing:
        print("\nFaltan archivos:", ", ".join(missing))
        sys.exit(1)
    print("\nDescarga completa.")
