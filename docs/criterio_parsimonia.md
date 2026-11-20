# Criterio de sencillez para las etapas del detector

**Este documento se escribió y se subió al repositorio antes de correr el análisis que lo aplica** (`notebooks/07_simplificacion.ipynb`). El notebook aplica estas reglas sin cambiarlas. Si algo tuviera que cambiar después de ver los resultados, el cambio se agrega al final, con fecha y motivo, y no se borra lo que estaba.

## Por qué hace falta

La auditoría de decisiones (`docs/auditoria_decisiones.md`) encontró siete etapas que se agregaron por un razonamiento razonable pero sin mostrar que hacen falta: con los datos de desarrollo no se pudo confirmar que la versión sin la etapa sea peor. La regla que se aplica es la de sencillez: **si no se puede demostrar que la alternativa más simple es peor, se usa la más simple**. Es la misma idea que la regla de un error estándar para elegir modelos (Breiman et al., 1984; Hastie, Tibshirani y Friedman, 2009, §7.10): entre opciones que no se distinguen con los datos, la más simple.

## El criterio

Una etapa del detector se mantiene solo si cumple al menos una de estas condiciones con los datos de desarrollo:

- **(a) La exige la consigna.** La consigna pide implementar los temas obligatorios (entre ellos filtros óptimos, recorte en realizaciones y Lomb). El grupo la interpreta como implementarlos y analizarlos, no como usarlos en el detector final; ese ya era el criterio de la primera versión (`docs/v1/guia_estudio.md`, §2.5). Wiener, las realizaciones y Lomb están implementados y analizados en `03` y `04`, así que (a) no obliga a mantener ninguna de las siete etapas. Si la cátedra indica lo contrario para el filtro de Wiener, vuelve al detector por (a) y se informa.
- **(b) Mejora de forma demostrable la medición que es el objetivo de su paso**, comparada contra una referencia de los datos: la ubicación del pico R (objetivo 2) o el parecido de la EDR con la respiración registrada (objetivo 3).
- **(c) Mejora de forma demostrable el detector** en validación cruzada por personas.
- **(d) Corrige una falla demostrada del detector.** Se aplica a las dos etapas que no cambian la decisión sino cuándo se decide o qué se informa al lado: la exclusión de minutos y la confianza.

**"De forma demostrable"** quiere decir que la diferencia va a favor de la etapa y que su valor p, corregido por Holm dentro de su familia, es menor que 0,05.

Si una etapa no cumple ninguna condición, se reemplaza por la alternativa simple que fija la tabla de abajo. La alternativa simple es no hacer el paso. Cuando el paso es una opción de una herramienta estándar, es el valor por defecto de esa herramienta.

Este criterio no decide entre alternativas con la misma cantidad de pasos y parámetros, como la ventana de 240 s contra la de 300 s, o la mediana contra la media. Esas decisiones ya están justificadas en `docs/decisiones.md` y no se tocan.

## Las etapas, su alternativa simple y la prueba

| Etapa | Actual | Alternativa simple | Evidencia de (b) | Prueba de (c) o (d) en validación cruzada |
|---|---|---|---|---|
| 1. Refinamiento del pico R | Vértice de una parábola por 3 muestras | El pico en la muestra (resolución de 10 ms) | Prueba de dos fases (`02` §3), en los 47 registros de desarrollo. Medida: desacuerdo medio entre fases por registro, sin refinar menos refinado. p por bootstrap de personas. Es una familia de una sola comparación | (c) exactitud del actual menos la de "sin refinamiento" |
| 2. Filtro de Wiener antes de medir la EDR | FIR de 129 coeficientes | Sin Wiener | `03` §6: ninguna comparación de coherencia con la respiración resiste Holm. Se toma como ya evaluada, sin repetirla | (c) actual − sin Wiener |
| 3. Excluir de la EDR los latidos ectópicos | Sí | No | Igual que la 2 | (c) actual − sin excluirlos |
| 4. Filtro de Hampel en la EDR | Sí | No | Igual que la 2 | (c) actual − sin Hampel |
| 5. Interpolación a 2 Hz | Spline cúbico | Lineal | No tiene una referencia | (c) actual − lineal |
| 6. Tendencia en cada segmento de Welch | Se quita una recta | Se quita la media, que es el valor por defecto de `scipy.signal.welch`. Con la ventana de Hann periódica, la media solo llega a las frecuencias k = 0 y 1, fuera de la banda (k = 2…6), así que quitarla o no da exactamente lo mismo en la banda | No tiene una referencia | (c) actual − quitando la media |
| 7a. Excluir los minutos con más de 20 % de RR corregidos | No se clasifican ni se usan para ajustar | Se clasifican todos y se ajusta con todos | No corresponde | (d) Con el detector sin exclusión: exactitud en los minutos con 20 % o menos menos la exactitud en los minutos con más de 20 %. Si es positiva y resiste, el detector falla en los minutos que se excluyen |
| 7b. Ídem, efecto sobre el ajuste | Ídem | Ídem | No corresponde | (c) Sobre los minutos con 20 % o menos: exactitud del actual menos la del detector ajustado con todos los minutos |
| 8. Confianza según el movimiento | Alta, media o baja (percentiles 50 y 90 del movimiento) | No se informa | No corresponde | (d) Exactitud en los minutos de confianza alta menos la exactitud en los de baja, con el detector actual. Los cortes se calculan en cada grupo de entrenamiento |

La exclusión de minutos se mantiene si resiste 7a o 7b.

**Lo que ya se sabía.** Algunas de estas comparaciones ya se habían hecho con otra pregunta: interpolación y tendencia en `04` §15, como controles de robustez; Wiener y la limpieza de la EDR en `03` §6. Por eso este documento fija cómo se decide y no anticipa ningún resultado. Las demás pruebas (1c, 3c, 4c, 7a, 7b y 8) no se habían corrido así.

## Cómo se mide

- **Validación cruzada:** la misma de `04` §15. Las 19 personas de desarrollo se reparten en 5 grupos (semilla 2026). Para cada grupo, con los otros 4 se estandarizan los términos de C, se elige w entre 0 y 3 cada 0,25 maximizando el AUC y se fija el umbral de Youden. Después se clasifica el grupo que quedó afuera.
- **Medida principal:** la exactitud por minuto de la validación cruzada. Es la calidad de la decisión final del detector, con umbral incluido, y es la medida con la que se compararon todas las variantes de `04` §15. Las comparaciones de (c) son pareadas, sobre los mismos minutos.
- **Diferencias y valores p:** bootstrap de personas pareado (4000 sorteos, semilla 2026). En cada sorteo se recalcula la exactitud con todos los minutos de las personas sorteadas. El p es bilateral (`src/estadistica.py`).
- **Familias de Holm:**
  - Prueba del detector: las 9 comparaciones de (c) y (d) de la tabla (1c, 2c, 3c, 4c, 5c, 6c, 7a, 7b y 8).
  - Medición del pico R (1b): una sola comparación.
  - Medición de la EDR (2b, 3b y 4b): ya corregida en `03` §6.

  Controlar el error de toda la familia equivale a que la probabilidad de conservar alguna etapa innecesaria no supere el 5 %.
- **Medidas descriptivas, que no deciden:** sensibilidad, especificidad, AUC con personas no vistas, AUC dentro de la noche, ρ por noche y porcentaje de minutos marcados en los controles. También P1, P2 y P3 calculados en desarrollo.

## Procedimiento

1. Cada etapa se prueba por separado contra el detector actual, con las demás sin cambios.
2. Las etapas que no cumplen ninguna condición se reemplazan juntas por su alternativa simple. Eso da el **detector simplificado**.
3. **Chequeo de la combinación:** exactitud del simplificado contra la del actual, como comparación única. Si el simplificado es peor de forma demostrable (p < 0,05), se restituye la etapa quitada con la mayor diferencia individual a su favor y se repite el chequeo.
4. Con todo desarrollo se ajustan los parámetros del detector simplificado (μ, σ, w y umbral), como en `04` §14.

## Qué se informa y qué no se toca

- **Test no se usa.** Sus 20 registros (10 personas) se usaron una sola vez para evaluar la versión que se congeló antes de abrirlo (`docs/parametros_test.json`, `notebooks/05_test.ipynb`). Esos resultados siguen siendo la evaluación independiente de esa versión, y no se atribuyen a la simplificada.
- **El detector simplificado se informa solo con validación cruzada en desarrollo**, aclarando que no tiene una evaluación independiente.
- No cambian la banda, la ventana, la forma de C, la partición, las semillas ni ninguna decisión fuera de la tabla.

## Agregados después de registrar el criterio

**2026-11-20: validación cruzada anidada (`07` §6 y §10).** Después de correr las secciones 2 a 5 se vio que la exactitud del detector simplificado se mide con la misma validación cruzada que se usó para elegir qué etapas quitar, y por eso puede ser optimista (Varma y Simon, 2006). Se agrega un control: se deja afuera cada grupo de personas, se repite todo el procedimiento con las demás (pruebas, Holm, decisión, chequeo de la combinación y ajuste de los parámetros) y se clasifica a las que quedaron afuera. El control no cambia la regla ni ninguna decisión: estima cuánto vale el procedimiento con personas que no intervinieron en él, y muestra si las decisiones cambian según qué personas se usan.

**2026-11-20: el valor p tiene que repetir el ajuste (`07` §7).** La validación anidada mostró que la decisión sobre Hampel (p < 0,001 con las 19 personas) no se repetía en ninguno de los 5 grupos externos, y que todo su efecto venía de una sola persona (las noches c10 y x18). La causa es que el bootstrap registrado sortea personas pero deja fijas las predicciones de la validación cruzada. Cuando una persona cambia el ajuste de los demás grupos, su efecto aparece repartido en muchas personas y el p queda demasiado chico. Se sabe que los intervalos que tratan las predicciones de la validación cruzada como fijas son demasiado angostos (Nadeau y Bengio, 2003; Bates, Hastie y Tibshirani, 2023).

La corrección es repetir toda la validación cruzada en cada sorteo de personas, porque el bootstrap tiene que repetir todos los pasos que dependen de los datos (Efron y Tibshirani, 1993). Se aplica a las 9 pruebas por igual y también al chequeo de la combinación. La regla de decisión no cambia. Con el p corregido ninguna prueba de (c) ni de (d) se cumple, y la decisión cambia solo para Hampel, que pasa de mantenerse a reemplazarse. El notebook muestra las dos decisiones.

## Referencias

- Breiman, L., Friedman, J. H., Olshen, R. A. y Stone, C. J. (1984). *Classification and Regression Trees*. Chapman & Hall/CRC. [doi:10.1201/9781315139470](https://doi.org/10.1201/9781315139470)
- Hastie, T., Tibshirani, R. y Friedman, J. (2009). *The Elements of Statistical Learning* (2.ª ed.), §7.10. Springer. [doi:10.1007/978-0-387-84858-7](https://doi.org/10.1007/978-0-387-84858-7)
- Aickin, M. y Gensler, H. (1996). Adjusting for multiple testing when reporting research results: the Bonferroni vs Holm methods. *American Journal of Public Health*, 86(5), 726–728. [doi:10.2105/AJPH.86.5.726](https://doi.org/10.2105/AJPH.86.5.726)
- Varma, S. y Simon, R. (2006). Bias in error estimation when using cross-validation for model selection. *BMC Bioinformatics*, 7, 91. [doi:10.1186/1471-2105-7-91](https://doi.org/10.1186/1471-2105-7-91)
- Bates, S., Hastie, T. y Tibshirani, R. (2023). Cross-validation: what does it estimate and how well does it do it? *Journal of the American Statistical Association*, 119(546), 1434–1445. [doi:10.1080/01621459.2023.2197686](https://doi.org/10.1080/01621459.2023.2197686)
- Nadeau, C. y Bengio, Y. (2003). Inference for the generalization error. *Machine Learning*, 52(3), 239–281. [doi:10.1023/A:1024068626366](https://doi.org/10.1023/A:1024068626366)
- Efron, B. y Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall/CRC. [doi:10.1201/9780429246593](https://doi.org/10.1201/9780429246593)
