import pytest

from src.config import RAW_DIR
from src.qrs.beats import record_beats


def test_fuente_desconocida():
    with pytest.raises(ValueError):
        record_beats("a01", source="otra")


@pytest.mark.skipif(not (RAW_DIR / "a02.dat").exists(), reason="faltan los datos")
def test_auto_elige_la_fuente_con_menos_rr_corregidos():
    b = record_beats("a02", "auto")
    assert b["source"] == min(("marks", "pt"), key=lambda k: b[f"corr_{k}"])
    # En a02 las marcas de la base pierden latidos: el detector propio deja menos RR corregidos.
    assert b["source"] == "pt"
