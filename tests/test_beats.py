import pytest

from src.config import RAW_DIR
from src.qrs.beats import record_beats


def test_fuente_desconocida():
    with pytest.raises(ValueError):
        record_beats("a01", source="otra")


@pytest.mark.skipif(not (RAW_DIR / "a02.dat").exists(), reason="faltan los datos")
def test_detector_propio_recupera_latidos_que_la_base_pierde():
    # En a02 las marcas de la base se saltean latidos: el RR queda al doble y se corrige.
    propio, base = record_beats("a02", "pt"), record_beats("a02", "marks")
    assert len(propio["t_r"]) > len(base["t_r"])
    assert propio["corr"] < base["corr"] / 5
