# Revisión de las comparaciones de `04` §8 y §15 con el bootstrap que repite el ajuste

**Este documento se escribió y se subió antes de correr `notebooks/10_revision_04.ipynb`.** Si algo tuviera que cambiar, se agrega al final, con fecha y motivo. Solo se usan los registros de desarrollo.

## Por qué

En `04` hay dos familias de comparaciones cuyos valores p salieron de un bootstrap que sortea personas pero deja fijas las predicciones de la validación cruzada:
- **§8, otras combinaciones de RR y EDR:** C contra 9 alternativas en 7 medidas. Resisten Holm 4 de 60 diferencias.
- **§15, decisiones de diseño:** 13 variantes en exactitud. Resisten Holm 2: la ventana de 360 s y las potencias en escala lineal.

Ese bootstrap da valores p demasiado chicos, porque no incluye cuánto cambia el ajuste cuando cambian las personas (`criterio_parsimonia.md`, agregado del 2026-11-20; Bates, Hastie y Tibshirani, 2023). Los textos de `04`, `decisiones.md` y la auditoría afirman que esas diferencias son demostrables, y puede que no lo sean.

## Qué se calcula

Las mismas dos familias, con el **detector final** (`docs/parametros_final.json`: EDR relativa, sin latidos ectópicos ni atípicos por Hampel, spline cúbico, quitando la recta en Welch y sin decidir en los minutos con más de 20 % de RR corregidos):

- **§8:** C contra las mismas 9 alternativas y la regresión logística de referencia, en las mismas 7 medidas: sensibilidad, especificidad, exactitud, AUC con personas no vistas, AUC dentro de la noche, ρ por noche y % de minutos marcados en los controles. Holm sobre todas las diferencias que tengan un p.
- **§15:** las mismas 13 variantes contra el detector final, en exactitud. Holm sobre las 13.

## Cómo

- **Bootstrap que repite el ajuste:** 2000 sorteos de las 19 personas con reposición (semilla 2026). En cada sorteo se repite toda la validación cruzada para C y para la alternativa: la estandarización, los pesos, el umbral y, en la regresión logística, sus coeficientes. Después se recalculan todas las medidas.
- **Personas repetidas:** las copias de una persona caen en el mismo grupo de la validación cruzada, como en `src/evaluation/cv.py`. En las medidas por noche, cada copia cuenta como una noche aparte.
- **Minutos que se comparan:** en §8, todas las alternativas usan los mismos minutos. En §15, una variante puede cambiar los minutos que se pueden evaluar (por ejemplo, la ventana), y la exactitud se compara en los minutos comunes, como en `07` a `09`.
- **p e intervalos:** p bilateral (`src/estadistica.py`) e intervalo percentil del 95 %.

## Qué se hace con el resultado

- **No decide nada.** Las decisiones de `04` no cambian. Son alternativas con la misma cantidad de pasos, y `criterio_parsimonia.md` las deja como estaban.
- **Si una alternativa resulta mejor de forma demostrable** con el detector final, se informa y se consulta antes de cambiar nada.
- **Los textos se corrigen:** los de `04`, `decisiones.md` y la auditoría que afirmen diferencias demostrables se corrigen con estos p, con una nota fechada. Los resultados de `04` con el bootstrap anterior quedan como estaban, para que se pueda ver la diferencia.
- Test no se usa.

## Referencias

- Bates, S., Hastie, T. y Tibshirani, R. (2023). Cross-validation: what does it estimate and how well does it do it? *Journal of the American Statistical Association*, 119(546), 1434–1445. [doi:10.1080/01621459.2023.2197686](https://doi.org/10.1080/01621459.2023.2197686)
- Efron, B. y Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall/CRC. [doi:10.1201/9780429246593](https://doi.org/10.1201/9780429246593)

## Agregado del 2026-11-21: la primera corrida se cortó

La primera corrida completa de `notebooks/10_revision_04.ipynb` se cortó a las 2 horas, que es el tiempo máximo de una tarea en este entorno, y no guardó ningún resultado. Se aceleró el código sin cambiar lo que calcula:
- `cv_c` (`src/evaluation/cv.py`) filtra los minutos de entrenamiento una sola vez por grupo en vez de una vez por cada w. La estandarización no depende de w.
- En §15, la validación cruzada del detector actual se hace una vez por sorteo y se compara con las 13 variantes, en vez de repetirla para cada variante.
- Las tablas que entran al bootstrap tienen solo las columnas que usa el ajuste.

Se verificó que el código nuevo da exactamente los mismos números que el anterior: `cv_c` en 40 sorteos (con 5, 10 y 19 grupos) y las diferencias de §15 y las medidas de §8 en la estimación y en varios sorteos. El plan no cambia.
