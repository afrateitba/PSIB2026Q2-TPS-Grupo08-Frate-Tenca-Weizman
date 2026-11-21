# Segunda evaluación en test: el detector final

**Este documento y `notebooks/11_test_final.ipynb` sin ejecutar se escribieron y se subieron antes de correr el notebook en test.** El notebook se corre una sola vez. Si algo tuviera que cambiar después, se agrega al final con fecha y motivo, y los resultados de la única ejecución quedan como salieron.

## Qué se evalúa

El **detector final** de `src/detector_final.py`, armado y ajustado solo con los 47 registros de desarrollo (`07` a `09`):
- parámetros en `docs/parametros_final.json`, congelado con su SHA-256 (`73344a36…`); si el archivo cambia, el notebook no carga;
- detector de QRS con sus seis etapas (`verificar_qrs`);
- EDR relativa, sin Wiener, sin latidos ectópicos ni atípicos (Hampel), con spline cúbico; Welch quitando la recta; no decide en los minutos con más de 20 % de RR corregidos.

En test no se ajusta nada: ni los parámetros de C, ni el umbral, ni los umbrales de F y del RR solo. Esos dos se fijan con desarrollo, como en `05`.

## Por qué esta evaluación no es ciega

- **Test ya se usó.** Los 20 registros de 10 personas se evaluaron en `05` con la versión anterior, y `06` analizó por qué falla en algunas de esas noches. Las decisiones de `07` a `09` se tomaron solo con desarrollo y con criterios escritos antes de aplicarlos, pero quienes las tomaron conocían esos resultados (`objetivos_hipotesis.md`, limitación 10). Este resultado dice si el detector final se sostiene en esas personas. Es menos limpio que el de `05`.
- **P1 no aporta evidencia nueva.** Depende solo de la potencia del RR, que es la misma en las dos versiones: μ₁ y σ₁ coinciden en todos los dígitos, porque el RR sale del mismo detector de QRS, el mismo refinamiento y la misma limpieza. Se espera que P1 repita exactamente el 0,869 de `05`. Sirve como control del cálculo: si no lo repite, algo cambió en el RR y hay que explicarlo.

## Controles antes de abrir test

El notebook se detiene antes de calcular nada en test si falla alguno:
1. El hash de `parametros_final.json` y las etapas del QRS coinciden con las congeladas (`cargar_params`, `verificar_qrs`).
2. Con los 47 registros de desarrollo, el pipeline final reproduce los parámetros del archivo: μ₁, σ₁, μ₂ y σ₂ con w = 1, y el umbral de Youden (tolerancia 1e-9).
3. La validación cruzada por personas en desarrollo reproduce la exactitud de `08` §7 (0,830, a tres decimales).

## Predicciones y criterio

Las mismas de `objetivos_hipotesis.md`, con las cantidades del detector final:

| Predicción | Qué se mide en test | Se cumple si |
|---|---|---|
| **P1**, dentro de la noche | AUC dentro de la noche de P_RR, media sobre los registros con al menos 20 minutos de cada tipo | la media es > 0,5 y su IC 95 % no incluye 0,5 |
| **P2**, entre noches | Spearman entre el nivel nocturno de la EDR (la EDR final) y el % de minutos con apnea de cada registro | ρ > 0 y su IC 95 % no incluye 0 |
| **P3**, detección | AUC de C con todos los minutos evaluados; sensibilidad, especificidad y exactitud con el umbral fijo | AUC > 0,5 y su IC 95 % no incluye 0,5 |

**H se sostiene con el detector final si se cumplen las tres.** Es una prueba de unión-intersección, así que no se corrige por comparaciones múltiples (Berger, 1982).

**Intervalos.** Bootstrap de personas con reposición, 4000 sorteos, semilla 2026, intervalo percentil del 95 %, como en `05`. En test el detector no se vuelve a ajustar: sus predicciones son fijas y lo único que varía entre sorteos es qué personas entran. Por eso acá corresponde el bootstrap con las predicciones fijas, y no el que repite el ajuste, que es para las comparaciones con validación cruzada en desarrollo.

## Preguntas secundarias (descriptivas)

1. **Detector final contra la versión evaluada, en test.** La versión evaluada se recalcula sobre test con `docs/parametros_test.json` y los valores por defecto de `src/config.py`. Primero se verifica que reproduce `docs/resultados_test.json` (P1 a P3 y la clasificación). Después, la diferencia final − evaluada en sensibilidad, especificidad, exactitud y AUC de C, en los minutos que evalúan las dos, con bootstrap pareado de personas (2000 sorteos), p bilateral (`src/estadistica.py`) y Holm sobre las 4.
2. **C contra F y el RR solo**, con el pipeline final, en las 7 medidas de `05` §3.1: sensibilidad, especificidad, exactitud, AUC con todos los minutos, AUC dentro de la noche, ρ por noche y % marcado en los controles. Bootstrap pareado de personas (2000 sorteos), p bilateral y Holm sobre todas las diferencias que tengan un p, como en `06` §5.
3. **Por noche:** % de minutos marcados contra el % real (ρ de Spearman con IC), % marcado en los controles, exactitud de cada noche y minutos evaluados de cada noche.
4. **Desarrollo y test:** las medidas en test al lado de las de la validación cruzada por personas del detector final en desarrollo.

## Qué se hace con el resultado

- **Se informa tal como sale.** El detector no se cambia por lo que dé test.
- **Si la versión evaluada resulta mejor en test, no se vuelve a ella.** Elegir entre versiones con test haría que test deje de ser una evaluación. Cualquier cambio posterior necesitaría datos nuevos.
- **Si H no se sostiene con el detector final,** se informa qué predicción falla y qué dice eso de cada parte de la hipótesis, como prevé `objetivos_hipotesis.md`.
- **La conclusión se escribe después de la única ejecución**, solo con sus resultados, sin recalcular nada ni cambiar el código.
- Los resultados se guardan en `docs/resultados_test_final.json`.

## Cómo se prueba el código sin abrir test

El notebook tiene un **modo ensayo** (`NB11_ENSAYO=1`), como `05`: usa 10 personas de desarrollo en lugar de test, no guarda resultados ni figuras, y sirve solo para ver que el código corre. La versión que se sube sin ejecutar es la misma que se probó en ese modo.

## Referencias

- Berger, R. L. (1982). Multiparameter hypothesis testing and acceptance sampling. *Technometrics*, 24(4), 295–300. [doi:10.1080/00401706.1982.10487790](https://doi.org/10.1080/00401706.1982.10487790)
- Efron, B. y Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall/CRC. [doi:10.1201/9780429246593](https://doi.org/10.1201/9780429246593)
