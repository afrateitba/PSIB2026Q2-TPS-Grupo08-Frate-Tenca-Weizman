
import numpy as np
import pytest

from src.stats.thresholds import (
    roc_youden,
    umbral_proporcion,
    mediana_youden_sujetos,
    combinar_predicciones,
)


def test_proporcion_exacta():
    s = np.array([0., 1., 2., 3.])
    y = np.array([0, 0, 1, 1])
    t = umbral_proporcion(s, y)
    assert t == 2.
    assert (s >= t).sum() == y.sum()


def test_proporcion_respeta_empates():
    s = np.array([1., 1., 2., 2.])
    y = np.array([0, 0, 0, 1])
    # No se puede clasificar solo uno de los dos valores iguales a 2.
    # Dos positivos y cero positivos empatan: se prioriza sensibilidad.
    t = umbral_proporcion(s, y)
    assert t == 2.
    assert (s >= t).sum() == 2


def test_proporcion_clases_extremas():
    s = np.array([1., 2., 3.])
    assert not (s >= umbral_proporcion(s, [0, 0, 0])).any()
    assert (s >= umbral_proporcion(s, [1, 1, 1])).all()


def test_bootstrap_un_sujeto_resultado_conocido():
    s = np.array([0., 1., 2., 3.])
    y = np.array([0, 0, 1, 1])
    t = mediana_youden_sujetos(s, y, ["A"] * 4, n_boot=20)
    assert t == roc_youden(s, y)["umbral"] == 2.


def test_bootstrap_reproducible():
    s = np.array([0., 3., 1., 4., 2., 5.])
    y = np.array([0, 1, 0, 1, 0, 1])
    g = np.array(["A", "A", "B", "B", "C", "C"])
    a = mediana_youden_sujetos(s, y, g, n_boot=50, seed=2026)
    b = mediana_youden_sujetos(s, y, g, n_boot=50, seed=2026)
    assert a == b


def test_combinaciones():
    f = [0, 0, 1, 1]
    h = [0, 1, 0, 1]
    np.testing.assert_array_equal(
        combinar_predicciones(f, h, "AND"), [0, 0, 0, 1]
    )
    np.testing.assert_array_equal(
        combinar_predicciones(f, h, "OR"), [0, 1, 1, 1]
    )


def test_entradas_invalidas():
    with pytest.raises(ValueError):
        umbral_proporcion([1., np.nan], [0, 1])
    with pytest.raises(ValueError):
        mediana_youden_sujetos([1., 2.], [0, 0], ["A", "A"])
    with pytest.raises(ValueError):
        combinar_predicciones([0, 1], [0], "AND")
    with pytest.raises(ValueError):
        combinar_predicciones([0], [1], "XOR")
