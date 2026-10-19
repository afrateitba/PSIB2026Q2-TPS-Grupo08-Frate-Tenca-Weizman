"""Descarga y carga de la Apnea-ECG Database (PhysioNet).

Consigna: contextualización del método de adquisición.  Esquema v2: §3 y §4.1.

Archivos por registro:
    <rec>.dat / .hea   ECG, 100 Hz, 16 bits, ~200 unidades A/D por mV
    <rec>.apn          etiqueta apnea (A) / normal (N) por minuto
    <rec>.qrs          QRS automáticos (sqrs125), sin auditar: contienen errores
    <rec>r.dat / .hea  respiración real (solo RESP_RECORDS)
Las etiquetas del set x también están en test-dataset-annos.txt.
additional-information.txt tiene, por registro, minutos, AI/HI/AHI, edad, sexo,
altura y peso.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import wfdb

from .config import (ALL_RECORDS, PHYSIONET_URL, RAW_DIR, RESP_RECORDS,
                     SAMPLES_PER_MIN)

EXTRA_FILES = ["test-dataset-annos.txt", "additional-information.txt"]


# --- Descarga ------------------------------------------------------------
def _download(fname: str, raw_dir: Path, overwrite: bool = False) -> bool:
    """Descarga un archivo. Devuelve False si no existe en PhysioNet (404)."""
    dest = raw_dir / fname
    if dest.exists() and not overwrite:
        return True
    r = requests.get(PHYSIONET_URL + fname, stream=True, timeout=60)
    if r.status_code == 404:
        return False
    r.raise_for_status()
    tmp = dest.with_name(dest.name + ".part")
    with open(tmp, "wb") as f:
        for chunk in r.iter_content(1 << 16):
            f.write(chunk)
    tmp.replace(dest)
    return True


def download_database(records=None, raw_dir: Path = RAW_DIR,
                      overwrite: bool = False) -> list[str]:
    """Descarga ECG, anotaciones y respiración. Devuelve los archivos faltantes.

    Los .apn del set x pueden no estar como archivo: en ese caso las
    etiquetas se leen de test-dataset-annos.txt y no se reportan como faltantes.
    """
    raw_dir.mkdir(parents=True, exist_ok=True)
    records = records or ALL_RECORDS
    missing = [f for f in EXTRA_FILES if not _download(f, raw_dir, overwrite)]
    for i, rec in enumerate(records, 1):
        print(f"[{i}/{len(records)}] {rec}", flush=True)
        for ext in (".hea", ".dat", ".qrs", ".apn"):
            if not _download(rec + ext, raw_dir, overwrite) and ext != ".apn":
                missing.append(rec + ext)
        if rec in RESP_RECORDS:
            for ext in (".hea", ".dat"):
                if not _download(f"{rec}r{ext}", raw_dir, overwrite):
                    missing.append(f"{rec}r{ext}")
    return missing


# --- Carga ---------------------------------------------------------------
def load_ecg(rec: str, raw_dir: Path = RAW_DIR) -> tuple[np.ndarray, float]:
    """ECG en mV y frecuencia de muestreo."""
    r = wfdb.rdrecord(str(raw_dir / rec))
    return r.p_signal[:, 0].astype(float), float(r.fs)


def load_qrs(rec: str, raw_dir: Path = RAW_DIR) -> np.ndarray:
    """Índices de muestra de los QRS de referencia (automáticos, sin auditar)."""
    return wfdb.rdann(str(raw_dir / rec), "qrs").sample


def load_respiration(rec: str, raw_dir: Path = RAW_DIR) -> tuple[dict, float]:
    """Señales respiratorias {nombre: señal} y fs. Solo para RESP_RECORDS."""
    if rec not in RESP_RECORDS:
        raise ValueError(f"{rec} no tiene respiración; disponibles: {RESP_RECORDS}")
    r = wfdb.rdrecord(str(raw_dir / f"{rec}r"))
    return dict(zip(r.sig_name, r.p_signal.T)), float(r.fs)


def load_apnea_labels(rec: str, raw_dir: Path = RAW_DIR) -> np.ndarray:
    """Etiqueta por minuto: 1 = apnea, 0 = normal, -1 = sin etiqueta.

    El minuto i abarca las muestras [i*6000, (i+1)*6000).
    """
    if (raw_dir / f"{rec}.apn").exists():
        ann = wfdb.rdann(str(raw_dir / rec), "apn")
        idx = ann.sample // SAMPLES_PER_MIN
        labels = np.full(idx.max() + 1, -1, dtype=np.int8)
        labels[idx] = [s == "A" for s in ann.symbol]
        return labels
    if rec.startswith("x"):
        return _test_labels(str(raw_dir / "test-dataset-annos.txt"))[rec].copy()
    raise FileNotFoundError(f"No hay anotaciones de apnea para {rec}")


@lru_cache(maxsize=1)
def _test_labels(path: str) -> dict[str, np.ndarray]:
    return parse_test_annotations(Path(path).read_text())


def parse_test_annotations(text: str) -> dict[str, np.ndarray]:
    """Parsea test-dataset-annos.txt: encabezado 'xNN' y filas '<i> NNAA...'."""
    out, cur, buf = {}, None, []

    def _flush():
        if cur is not None:
            out[cur] = np.array([c == "A" for c in "".join(buf)], dtype=np.int8)

    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if re.fullmatch(r"x\d{2}", s):
            _flush()
            cur, buf = s, []
        else:
            buf.append("".join(c for c in s.split()[-1] if c in "AN"))
    _flush()
    return out


def load_record_info(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Tabla de additional-information.txt, una fila por registro."""
    return parse_record_info((raw_dir / "additional-information.txt").read_text())


def parse_record_info(text: str) -> pd.DataFrame:
    """Parsea la tabla de additional-information.txt.

    Los conteos de minutos de esta tabla dan un minuto más que las anotaciones
    (.apn y test-dataset-annos.txt) en a01 y en los 35 registros x. Para contar
    minutos se usan las anotaciones; de esta tabla se toman AI/HI/AHI y el perfil
    del sujeto (edad, sexo, altura, peso).
    """
    cols = ["record", "length_min", "normal_min", "apnea_min", "hours_apnea",
            "AI", "HI", "AHI", "age", "sex", "height_cm", "weight_kg"]
    rows = [line.split()[:len(cols)] for line in text.splitlines()
            if re.match(r"[abcx]\d{2}\s", line)]
    df = pd.DataFrame(rows, columns=cols)
    ints = ["length_min", "normal_min", "apnea_min", "hours_apnea",
            "age", "height_cm", "weight_kg"]
    df[ints] = df[ints].astype(int)
    df[["AI", "HI", "AHI"]] = df[["AI", "HI", "AHI"]].astype(float)
    return df
