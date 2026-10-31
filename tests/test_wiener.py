"""Pruebas con resultados conocidos para el bloque de Wiener."""

import numpy as np

from src.preprocessing.wiener import (
    extract_realizations,
    estimate_psds,
    wiener_filter
)


def test_recorte_fraccionario_y_bordes():
    # En una rampa, interpolar en una posición fraccionaria
    # debe devolver exactamente el valor de esa posición.
    ecg = np.arange(20, dtype=float)

    beats = extract_realizations(
        ecg,
        r_peaks=np.array([0, 5.5, 19]),
        fs=10,
        pre=0.2,
        post=0.3
    )

    # Los centros de los extremos no permiten un recorte completo.
    esperado = np.array([[3.5, 4.5, 5.5, 6.5, 7.5, 8.5]])
    np.testing.assert_allclose(beats, esperado)


def test_latidos_identicos_sin_residuo():
    fs = 100
    t = np.arange(100) / fs
    beat = np.sin(2 * np.pi * 10 * t)
    beats = np.tile(beat, (5, 1))

    f, s_s, s_n = estimate_psds(beats, fs)

    # Sin diferencias entre latidos, el residuo debe ser nulo.
    np.testing.assert_allclose(s_n, 0, atol=1e-25)

    # La señal conocida tiene su máximo espectral cerca de 10 Hz.
    assert abs(f[np.argmax(s_s)] - 10) < 0.5


def test_ganancia_unidad_conserva_senal():
    fs = 100
    x = np.random.default_rng(2026).normal(size=2000)
    f = np.linspace(0, fs / 2, 129)

    # Señal positiva y ruido nulo: la ganancia objetivo es 1.
    y = wiener_filter(x, f, np.ones_like(f), np.zeros_like(f), fs)

    assert y.shape == x.shape
    np.testing.assert_allclose(y, x, atol=1e-12, rtol=1e-12)


def test_atenua_componente_con_ruido_estimado():
    fs = 100
    t = np.arange(2000) / fs
    lenta = np.sin(2 * np.pi * 5 * t)
    rapida = np.sin(2 * np.pi * 20 * t)

    f = np.linspace(0, fs / 2, 257)

    # Modelo conocido: conservar hasta 8 Hz y rechazar desde 12 Hz.
    ganancia = np.interp(f, [0, 8, 12, 50], [1, 1, 0, 0])
    s_s = ganancia
    s_n = 1 - ganancia

    salida_lenta = wiener_filter(lenta, f, s_s, s_n, fs)
    salida_rapida = wiener_filter(rapida, f, s_s, s_n, fs)

    # Medir lejos de los bordes.
    interior = slice(200, -200)

    assert np.std(salida_lenta[interior]) > 0.9 * np.std(lenta[interior])
    assert np.std(salida_rapida[interior]) < 0.1 * np.std(rapida[interior])
