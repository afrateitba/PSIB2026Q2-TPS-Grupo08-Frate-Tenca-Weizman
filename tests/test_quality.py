
import numpy as np
import pandas as pd

from src.preprocessing.quality import window_signal_quality


def signal():
    # Señal variable, sin tramos planos ni saturación.
    return np.tile([-2, 2], 3000)


def test_ventanas_completas_y_sin_perdida():
    q = window_signal_quality(signal(), 10, 12, [0, 2])
    assert not q.loc[0, "ventana_completa"]
    assert np.isnan(q.loc[0, "segundos_perdidos"])
    assert not q.loc[0, "sin_perdida"]
    assert q.loc[1, "sin_perdida"]


def test_duracion_minima_y_limites():
    d = signal()
    d[1000:1009] = 0  # 0,9 s: no alcanza el mínimo.
    q = window_signal_quality(d, 10, 12, [2])
    assert q.loc[0, "sin_perdida"]

    d = signal()
    d[1000:1010] = 0  # 1 s dentro de la ventana.
    q = window_signal_quality(d, 10, 12, [2])
    assert q.loc[0, "segundos_perdidos"] == 1.0

    d = signal()
    d[290:300] = 0  # Termina justo donde empieza la ventana.
    q = window_signal_quality(d, 10, 12, [2])
    assert q.loc[0, "sin_perdida"]


def test_permanencia_en_topes():
    d = signal()
    # Alterna entre topes: no es plano, pero permanece saturado 1 s.
    d[1000:1010] = np.tile([-2048, 2047], 5)
    q = window_signal_quality(d, 10, 12, [2])
    assert q.loc[0, "segundos_perdidos"] == 1.0
    assert not q.loc[0, "sin_perdida"]


def test_exclusion_es_opcional(monkeypatch):
    import src.data as data
    from src.features.build import attach_window_quality

    d = signal()
    d[1000:1010] = 0

    monkeypatch.setattr(data, "load_ecg_digital", lambda *args: d)
    monkeypatch.setattr(
        data, "load_header",
        lambda *args: {"fs": 10, "bits": 12, "cero": 0},
    )

    tab = pd.DataFrame({"minute": [2, 6], "F": [1.0, 2.0]})
    actual = attach_window_quality(tab, "sintetico")
    candidata = attach_window_quality(
        tab, "sintetico", exclude_lost=True
    )

    pd.testing.assert_frame_equal(actual[tab.columns], tab)
    assert candidata["minute"].tolist() == [6]
