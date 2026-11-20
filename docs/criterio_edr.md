# Criterio para las decisiones de la EDR

**Este documento se escribió y se subió al repositorio antes de calcular P2 para cada variante de la EDR.** El notebook que lo aplique lo hará sin cambiarlo. Si algo tuviera que cambiar, se agrega al final, con fecha y motivo, y no se borra lo que estaba. Solo se usan los registros de desarrollo.

## Por qué hace falta un criterio propio para la EDR

En la feature C la EDR entra solo como **nivel de la noche**, que se compara entre personas. Sin embargo, sus variantes se eligieron en `03`, antes de que existiera C, con medidas *dentro* de la noche: el parecido con la respiración (A1, A2) y la separación de los minutos de una misma noche (B). Y la prueba de `07` (exactitud del detector) incluye el nivel de la EDR, pero mezclado con el término del RR, el peso y el umbral. Hace falta una medida que corresponda a lo que la EDR hace en el detector.

## Lo que ya se sabía antes de escribir esto

- P2 en desarrollo del detector evaluado en test (0,825) y del simplificado de `07` (0,778), en conjunto, no etapa por etapa.
- En `04` §13, P2 de la EDR relativa contra la EDR en mV·ms (0,83 contra 0,71), sin bootstrap.
- `03` §6: A1, A2 y B de cada variante; la amplitud R casi no sigue a la respiración.
- Sin etiquetas (simulación con latidos reales, 2026-11-20): el filtro del ECG y el Wiener conservan la modulación lenta del área; la interpolación lineal conserva la banda 0,01–0,05 Hz (pierde 1,5 % de potencia en 0,05 Hz), pero en 0,25 Hz pierde 32 % de la potencia, y la cúbica, 3 %.
- Con etiquetas, descriptivo (2026-11-20, resolución de 1/240 Hz, 32 registros): el aumento de potencia con la apnea es máximo en 0,021–0,025 Hz (RR +8,3 dB, EDR +5,1 dB) y cae por debajo de 0,017 Hz (en 80 s de período: RR +3,8 dB, EDR +2,6 dB). El estimador de Welch con segmentos de 120 s capta entre 26 % (0,01 Hz) y 80 % (0,016 Hz) de la potencia de esa parte de la banda.

## El criterio

1. **Requisito de validez: la EDR tiene que ser respiración.** Una variante que empeora de forma demostrable el parecido con la respiración registrada (A1, 8 registros) queda descartada, aunque mejore P2. Por eso la amplitud R no se prueba (`03` §6).

2. **Medida de decisión: P2 en desarrollo.** Es la ρ de Spearman entre el nivel nocturno de la EDR (mediana de P_EDR en la noche) y el % de minutos con apnea, en las 47 noches de desarrollo. Cada variante se compara con su alternativa sobre las mismas noches: ΔP2 = P2 con la etapa − P2 sin ella. P2 no ajusta nada, así que no hace falta validación cruzada ni repetir ningún ajuste. El intervalo y el valor p salen de un bootstrap pareado por personas (4000 sorteos, semilla 2026; `src/estadistica.py`).

3. **Regla de sencillez.** Una etapa que agrega pasos se mantiene solo si mejora P2 de forma demostrable: la diferencia va a su favor y su p, corregido por Holm, es menor que 0,05. Cuando dos alternativas tienen la misma cantidad de pasos y parámetros, se mantiene la actual, salvo que la otra mejore P2 de forma demostrable sin empeorar A1 de forma demostrable. Si no hay diferencia demostrable y la bibliografía tiene un estándar, se usa el estándar.

4. **Familia de Holm.** Las pruebas de este documento forman una sola familia junto con las 9 de `07` (con su p corregido, el que repite el ajuste). Así, agregar una vía nueva para que una etapa se quede no vuelve más permisivo el criterio.

## Qué se prueba

La base es la EDR del detector simplificado de `07`: área relativa del QRS (±60 ms) sobre el ECG filtrado de 0,5 a 45 Hz, sin Wiener, sin excluir latidos ectópicos ni atípicos, interpolada a 2 Hz. Se cambia un elemento por vez.

| # | Elemento | Alternativas | Cuál es la simple | Cómo se decide |
|---|---|---|---|---|
| E1 | Método | área (actual), deriva de línea de base, área + deriva (fusión) | Área y deriva tienen la misma complejidad; la fusión es más compleja | La deriva reemplaza al área solo si mejora P2 de forma demostrable sin empeorar A1 de forma demostrable. La fusión entra solo si mejora P2 de forma demostrable |
| E2 | Wiener | con / sin | Sin | Entra solo si mejora P2 de forma demostrable |
| E3 | Excluir latidos ectópicos (por el ritmo) | con / sin | Sin | Ídem |
| E4 | Excluir latidos atípicos | Hampel (nuestro), procedimiento publicado de Varon et al. (2020): se excluyen los QRS cuya varianza cae fuera de Q1 − 2,5·IQR a Q3 + 2,5·IQR; ninguno | Ninguno | Cada uno se compara contra ninguno. Si los dos mejoran P2 de forma demostrable, se usa el publicado, salvo que el nuestro sea demostrablemente mejor |
| E5 | Escala | EDR relativa (actual) / en mV·ms | En mV·ms (no dividir) | La relativa se mantiene solo si mejora P2 de forma demostrable |
| E6 | Interpolación a 2 Hz | spline cúbico / lineal | Igual complejidad: una sola operación cada una | Si no hay diferencia demostrable en P2, se usa el estándar de la bibliografía, el spline cúbico (Varon et al., 2020), que además conserva la banda respiratoria (simulación de arriba). La interpolación es la misma para el RR y la EDR |

**Sobre E6 y `07`.** En `07` se registró la interpolación lineal como la alternativa "simple" del spline cúbico. Eso fue un error de clasificación: las dos son una sola operación sin parámetros que elegir, así que la regla de sencillez no las ordena. Se corrige acá con la regla de igual complejidad. Como en `07` no hubo diferencia demostrable en la exactitud del detector (p = 0,93), si tampoco la hay en P2, la decisión pasa a ser el spline cúbico, para el RR y la EDR.

## Qué se informa

- Para cada prueba: ΔP2, su IC 95 %, el p y el p de Holm; ΔA1 cuando corresponde.
- La EDR resultante y el detector que resulta, medidos con la misma validación cruzada de `07`.
- Test no se usa. Cuando el detector final esté cerrado, se evalúa una sola vez en test con un notebook registrado antes de ejecutarse (ver `docs/objetivos_hipotesis.md`).

## Referencias

- Varon, C. et al. (2020). A comparative study of ECG-derived respiration in ambulatory monitoring using the single-lead ECG. *Scientific Reports*, 10, 5704. [doi:10.1038/s41598-020-62624-5](https://doi.org/10.1038/s41598-020-62624-5)
- Charlton, P. H. et al. (2018). Breathing rate estimation from the electrocardiogram and photoplethysmogram: a review. *IEEE Reviews in Biomedical Engineering*, 11, 2–20. [doi:10.1109/RBME.2017.2763681](https://doi.org/10.1109/RBME.2017.2763681)
- Aickin, M. y Gensler, H. (1996). Adjusting for multiple testing when reporting research results: the Bonferroni vs Holm methods. *American Journal of Public Health*, 86(5), 726–728. [doi:10.2105/AJPH.86.5.726](https://doi.org/10.2105/AJPH.86.5.726)
