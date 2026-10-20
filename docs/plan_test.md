# Plan de evaluación en test

Este documento fija **antes de abrir test** qué se evalúa, cómo y qué cuenta como resultado. Se commitea antes de calcular cualquier cosa sobre los registros de test, para que el historial de git muestre que el plan es previo a los resultados. Cualquier cambio posterior se agrega al final como desvío, con su fecha y su motivo, y nunca reemplaza lo que dice este texto.

## 1. Conjunto de test

- Los 20 registros con `set == "test"` en `data/split.csv` (commit `8d4ca2f`): 12 A, 3 B y 5 C, de 10 sujetos. Ningún sujeto está también en desarrollo.
- Hasta la evaluación final no se calcula nada sobre estos registros: ni features ni estadísticas descriptivas de sus etiquetas.

## 2. Condiciones para abrir test

Test se abre **una sola vez**, cuando se cumplan todas estas condiciones:

1. **Pipeline congelado.** Están cerradas en desarrollo las etapas obligatorias que faltan:
   - 4.2 filtro pasabanda;
   - 4.3 detector QRS propio (Pan-Tompkins);
   - 4.4 recorte en realizaciones y filtro de Wiener.

   Cada una se trata como **verificación, no como búsqueda**. La versión de la etapa se compara contra la configuración actual con el AUC por minuto y el acierto por registro, y se adopta si es no inferior (límite inferior del IC 95 % de la diferencia ≥ −0,02). Si empeora, se reporta y no se adopta.
2. **Umbrales fijados.** El umbral de F y el de la HRV de referencia salen del índice de Youden sobre todos los minutos de desarrollo (sección 3). Quedan escritos en el notebook de umbrales y commiteados.
3. **Estimación honesta en desarrollo.** Está hecha la validación cruzada anidada por sujetos de todo el procedimiento de elección (E3a → E3b → umbral). Sus números (AUC, exactitud y acierto por registro en los sujetos que quedan afuera) son la estimación de desarrollo que se reporta.
4. **Commit de congelamiento.** Todo lo anterior está commiteado y la versión se marca con la etiqueta `congelado-test`. La evaluación se corre sobre esa versión.

## 3. Qué se congela

Valores vigentes al escribir este plan. Los marcados con † pueden cambiar en las etapas de verificación del punto 2.1; el valor definitivo es el del commit `congelado-test`.

| Componente | Valor |
|---|---|
| Registros excluidos | c05, x22, x33 (grabaciones duplicadas) |
| Filtro del ECG | Butterworth pasabanda 0,5–45 Hz, orden 3, fase cero (fijado en 4.2, `notebooks/07_filtro.ipynb`) |
| Latidos † | marcas `.qrs` de la base, pico R refinado con parábola de 3 puntos (refinamiento verificado en 4.1, `notebooks/00_adquisicion.ipynb`) |
| RR | se corrige si está fuera de 0,3–2 s o si se aparta más de 20 % de la mediana de 11 vecinos; se interpola |
| EDR † | área con signo del QRS (±60 ms del centro, polaridad medida por registro) |
| F (detector) | log de la potencia cruzada RR–EDR promediada en 0,01–0,05 Hz; ventana de 240 s centrada en cada minuto; Welch con 3 segmentos de 50 % de solapamiento; RR y EDR remuestreados a 2 Hz; sin normalizar ni suavizar |
| HRV de referencia | potencia del RR en 0,01–0,04 Hz (VLF) con periodograma de Lomb, ventana de 180 s; sin normalizar ni suavizar |
| Umbral de F y de la HRV † | índice de Youden en desarrollo; un minuto es apnea si la feature es ≥ umbral |

## 4. Minutos que se evalúan

- **Análisis principal:** los minutos con etiqueta que cumplen las mismas condiciones que en desarrollo: 20 % o menos de RR corregidos, y F y HRV calculables (la ventana entra completa en la grabación). Las dos features se evalúan sobre **los mismos minutos**. Se reporta qué fracción de los minutos con etiqueta queda afuera.
- **Sensibilidad:** todos los minutos con etiqueta. Un minuto sin feature válida toma la decisión del minuto válido más cercano del mismo registro.

## 5. Hipótesis principal: H2

**H2.** La feature conjunta RR–EDR (F) detecta la apnea mejor que la mejor HRV, que usa solo el RR.

Hay dos medidas principales, con el mismo peso:

| | Medida | Qué mide |
|---|---|---|
| **M1** | AUC por minuto, con todos los minutos de test juntos | separar minutos con y sin apnea con un único umbral para todos |
| **M2** | Acierto por registro: correlación de Spearman, sobre los 20 registros, entre la fracción de minutos de apnea estimada (minutos con feature ≥ umbral de desarrollo, sobre los minutos evaluados) y la fracción anotada | estimar cuánta apnea tiene cada noche |

**Procedimiento.** Para cada medida:
1. Diferencia = medida de F − medida de la HRV, sobre los mismos minutos y registros.
2. Bootstrap por sujeto, 10.000 remuestreos: se remuestrean los 10 sujetos con reposición y se recalculan las dos medidas sobre los minutos y registros de los sujetos elegidos.
3. IC 95 % de la diferencia (percentiles 2,5 y 97,5).
4. p bilateral = 2 × min(fracción de remuestreos con diferencia ≤ 0, fracción con diferencia ≥ 0).

Los dos p se corrigen por **Holm**.

**Regla de decisión.**
- **H2 se confirma en una medida** si su p de Holm es < 0,05 y la diferencia favorece a F.
- **H2 se rechaza en esa medida** si su p de Holm es < 0,05 y la diferencia favorece a la HRV.
- En cualquier otro caso, la medida **no muestra diferencia** con estos datos.
- Las conclusiones se dan por medida. No se combinan en un solo veredicto.

**Potencia.** Con 10 sujetos la prueba tiene poca potencia. Un resultado "sin diferencia" no se interpreta como "son iguales": se reportan el tamaño de la diferencia y su IC.

## 6. Resultados secundarios (descriptivos, sin tests de hipótesis)

1. **Por minuto, con los umbrales de desarrollo, para F y la HRV:** sensibilidad, especificidad, exactitud y matriz de confusión. Como referencia (no como meta) se cita el ~90 % de exactitud por minuto que alcanzaron con aprendizaje automático los mejores métodos del Challenge 2000.
2. **Por registro:**
   - minutos de apnea por hora estimados contra anotados, con gráfico de Bland–Altman;
   - categoría A/B/C estimada (≥ 100 minutos de apnea: A; 5–99: B; < 5: C) contra la real, con su matriz de confusión. Con 3 registros B, esa clase pesa poco y se dice.
3. **Replicación de H1:** en los registros A/B de test (15 registros, 8 sujetos) se repite la prueba principal de E2 con su misma configuración (CR como cociente de coherencias, ventana de 512 s, bandas del CPC publicado y de v2, Wilcoxon por sujeto, Holm). Es una replicación con poca potencia y se reporta como tal.
4. **Sensibilidad** de todo lo anterior con todos los minutos (sección 4).

## 7. Qué se reporta y qué no se hace

- Se reportan **todos** los resultados de las secciones 5 y 6, sean favorables o no.
- Después de abrir test no se cambia nada del pipeline, de los umbrales ni de las medidas para mejorar un resultado.
- **Si aparece un error de código** después de abrir test: se corrige, se declara en este documento (sección 9) y se reportan **las dos** corridas, la original y la corregida.
- En el informe, los números de desarrollo completo se presentan como optimistas (se usaron para elegir). Los resultados principales son los de test y los de la validación cruzada anidada.

## 8. Cómo se corre

Un solo notebook, `notebooks/99_test.ipynb`, ejecutado una vez sobre el commit `congelado-test`, calcula todo lo de las secciones 4 a 6. Se commitea con sus salidas tal como quedan.

## 9. Desvíos posteriores a este plan

### 9.1 (20/10/2026, antes de abrir test) Se agrega la etapa 4.1 a las condiciones del punto 2.1

La lista del punto 2.1 dejó afuera la 4.1 (contexto de la adquisición). Casi toda es descriptiva, pero una parte toca el pipeline: el refinamiento parabólico del pico R (fila "Latidos" de la sección 3) se usaba sin haberse verificado. La 4.1 lo verifica con una prueba de dos fases a 50 Hz, con una regla fijada antes de correr, y queda como una condición más para abrir test.

### 9.2 (20/10/2026, antes de abrir test) Nuevo resultado secundario: acierto por registro contra el AHI

Se agrega al punto 2 de la sección 6: Spearman, sobre los 20 registros, entre la fracción de minutos de apnea estimada (la misma de M2) y el AHI de la base, para F y para la HRV, con IC por bootstrap por sujeto. Es descriptivo, sin test de hipótesis, como el resto de la sección 6.

Motivo: M2 usa la fracción de minutos anotados, y el AHI es la medida clínica de gravedad. No pasa a ser una medida principal por dos razones:
- **Con datos:** en desarrollo, la fracción de minutos con apnea y el AHI tienen un Spearman de 0,94 (IC 0,84 a 0,97). Como tercera medida principal repetiría casi lo mismo que M2 y le quitaría potencia a la corrección de Holm.
- **Metodológica:** el detector estima minutos y el AHI cuenta eventos por hora de sueño, que desde el ECG no se conoce. Es una decisión de criterio, no algo que los datos puedan decidir.
