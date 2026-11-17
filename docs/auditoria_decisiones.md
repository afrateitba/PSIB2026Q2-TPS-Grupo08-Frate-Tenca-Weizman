# Auditoría de decisiones

Cada decisión del proyecto (código y notebooks `01`–`06`), con el tipo de justificación y si está justificada. Complementa a [`decisiones.md`](decisiones.md), que detalla los valores y la bibliografía completa.

**Estados.**
- ✅ **Justificada**: con datos (figura o número en un notebook), bibliografía o un argumento físico verificable.
- 🟡 **Parcial**: tiene un argumento razonable, pero el valor exacto es una convención o no se comparó con alternativas.
- ❌ **Sin justificar**: elección de implementación que no se discute en ningún lado.
- ⚠️ **Limitación**: está justificada pero se mostró que falla en algún caso.

**Tipos de justificación.** *Datos*: medido en desarrollo. *Bibliografía*: método publicado o recomendación. *Física*: propiedad de la señal o fisiología. *Convención*: valor habitual sin análisis propio. *Diseño*: regla de trabajo o pregunta que responde. *Grupo*: elección del grupo.

**Resumen:** 85 decisiones: ✅ 58 justificadas, 🟡 21 parciales, ❌ 4 sin justificar, ⚠️ 2 limitaciones.


## Base y partición

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 1 | Base de datos | Apnea-ECG (PhysioNet): ECG de una derivación, 100 Hz, etiqueta por minuto | Bibliografía, Diseño | Base pública de referencia para este problema (challenge de PhysioNet 2000), con ECG de una derivación y etiquetas de apnea por minuto (Penzel et al., 2000) | 01 §1 | ✅ Justificada |
| 2 | Unidad de decisión | 1 minuto | Datos | Las etiquetas de la base son por minuto | 01 §3; 04 §1 | ✅ Justificada |
| 3 | Excluir grabaciones duplicadas | c05, x22, x33 | Datos, Bibliografía | Muestras idénticas con desfase; c05/c06 documentado por PhysioNet, los otros dos pares encontrados comparando las señales | 01 §2 (decisión 1) | ✅ Justificada |
| 4 | Cuál de cada par se conserva | La que empieza antes | Convención | Es la misma señal: la elección no cambia nada | config.py | ✅ Justificada |
| 5 | Detección de duplicados | Plantilla de latido (0,5–40 Hz, horas 1–4, latidos estables) y correlación de 5 min; r ≥ 0,99 | Datos | Los pares duplicados dan r ≈ 1 y el resto queda muy por debajo; los parámetros internos no se analizaron, pero el resultado no es ambiguo | 01 §2; duplicates.py | 🟡 Parcial |
| 6 | Agrupar registros por persona | Perfil idéntico (edad, sexo, altura, peso) | Datos | 52 pares con perfil idéntico contra ≤ 3 esperados por azar; verificación con la forma del latido (46 % contra 2 % de pares casi idénticos) | 01 §2 (decisión 2) | ✅ Justificada |
| 7 | Partir por persona | Ninguna persona en los dos conjuntos | Datos | Las noches de una persona se parecen: el latido más parecido es de la misma persona en 32 de 46 registros, y el % de apnea difiere 7 puntos entre noches de una persona contra 37,5 entre personas distintas | 01 §2 (decisión 3) | ✅ Justificada |
| 8 | Proporción de la partición | 70 % desarrollo, 30 % test | Convención | Equilibrio entre personas para decidir y para evaluar; no se analizó otra proporción | 01 §2 (decisión 4) | 🟡 Parcial |
| 9 | Estratificar por categoría | Mismas proporciones de A, B y C | Diseño | El detector se evalúa también por noche y por categoría | 01 §2 (decisión 5) | ✅ Justificada |
| 10 | Balancear la apnea | Diferencia ≤ 2 puntos en % de minutos con apnea | Diseño, Convención | Exactitud y umbral dependen de la prevalencia; el valor de 2 puntos es convencional | 01 §2 (decisión 6) | 🟡 Parcial |
| 11 | Registros con respiración | Siempre en desarrollo | Diseño | Son los únicos con los que se puede validar la EDR | 01 §2 (decisión 7) | ✅ Justificada |
| 12 | Elección de la partición | Sorteo con semilla 2026 entre las 853 válidas | Diseño | Nadie elige qué personas van a test | 01 §2 (decisión 8) | ✅ Justificada |
| 13 | Categoría de los registros x | Regla por minutos: ≥ 100 → A, < 5 → C, resto B | Bibliografía | Aproximación documentada a los criterios de Penzel et al. (2000), que además piden índices por hora | split.py; 01 §1 | ✅ Justificada |
| 14 | Uso de los datos de test antes de la evaluación | Solo los de la partición (categoría, minutos con apnea, perfil) | Diseño | Regla de trabajo: test no se toca hasta 05 | plan_recuperatorio.md §0 | ✅ Justificada |

## Exploración y calidad

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 15 | Umbrales descriptivos de calidad | Tramo plano ≥ 1 s; sin ECG si la energía en 5–15 Hz < 10 %; deriva o interferencia > 10 % | Convención | Solo describen los problemas de la base; no se usan en el pipeline | 01 §5 | 🟡 Parcial |
| 16 | PSD del ECG | Welch, 4096 muestras (~41 s) | Física | Resolución de 0,024 Hz, suficiente para el latido y sus armónicos; descriptivo | 01 §5 | ✅ Justificada |
| 17 | Espectrograma | Ventanas de 30 s | Física | Compromiso tiempo–frecuencia; descriptivo | 01 §5 | ✅ Justificada |
| 18 | Banda de la apnea | 0,01–0,05 Hz | Datos, Bibliografía | Máximo aumento de potencia del RR con apnea dentro de cada registro (pico 0,025 Hz; −3 dB entre 0,017 y 0,05 Hz); ciclos de 20–100 s (Guilleminault et al., 1984) | 01 §7 | ✅ Justificada |
| 19 | Misma banda para la EDR | 0,01–0,05 Hz | Datos | La banda se midió con el RR; para la EDR se verificó que la potencia sube en esa banda, pero no se optimizó por separado | 01 §7 | 🟡 Parcial |

## Filtro

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 20 | Tipo de filtro | Butterworth pasabanda | Física | Respuesta plana en la banda de paso | 02 §1 | ✅ Justificada |
| 21 | Fase cero | Ida y vuelta (sosfiltfilt) | Física | No corre el pico R ni deforma el QRS | 02 §1 | ✅ Justificada |
| 22 | Especificación | ≤ 1 dB entre 0,77 y 41,8 Hz; ≥ 20 dB a 0,1 Hz | Datos | 0,77 Hz = percentil 1 de la frecuencia cardíaca; 41,8 Hz = percentil 95 entre registros del 99 % de la energía del latido. Los percentiles y los dB son convencionales | 02 §1 | ✅ Justificada |
| 23 | Cortes | 0,5–45 Hz | Datos, Bibliografía | Cumplen la especificación; la AHA admite hasta 0,67 Hz con fase cero (Kligfield et al., 2007); 45 Hz < Nyquist e interferencia de 50 Hz | 02 §1 | ✅ Justificada |
| 24 | Orden | 3 | Datos | El menor que cumple la especificación | 02 §1 | ✅ Justificada |

## Latidos

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 25 | Fuente de los latidos | Detector propio en todos los registros (no las marcas .qrs) | Datos | Las marcas pierden latidos en algunos registros; revisión manual de 50 casos | 02 §2 | ✅ Justificada |
| 26 | Algoritmo base | Pan-Tompkins: 5–15 Hz, derivada de 5 puntos, integración 150 ms, refractario 200 ms, onda T 360 ms, búsqueda hacia atrás a 1,66 RR, umbrales adaptativos | Bibliografía | Pan y Tompkins (1985) | 02 §2 | ✅ Justificada |
| 27 | Cinco mejoras | Prominencia ≥ 0,5; piso 5 %; ventana T máx(360 ms; 0,5 RR); forma (r ≥ 0,5 con 8 QRS); energía > 20 Hz ≥ 30 % | Datos, Bibliografía | Cada una corrige un error visto en desarrollo (ablación); el valor exacto no importa (< 0,5 % de latidos cambian moviendo cada umbral); Bazett (1920), Sörnmo y Laguna (2005) | 02 §2 | ✅ Justificada |
| 28 | Detalles internos del detector | Ubicación del pico ±80 ms; ventana de forma ±100 ms; mínimo 3 plantillas; prominencia en 2 s; energía rápida en ±50 ms con Butterworth de orden 2 | Física | Elegidos por el ancho del QRS; no se analizaron por separado (la sensibilidad cubre solo los umbrales principales) | pan_tompkins.py | 🟡 Parcial |
| 29 | Tolerancia de comparación | 100 ms | Datos, Bibliografía | Las fuentes coinciden a < 30 ms; entre 30 y 150 ms cambia < 1 punto; AAMI EC57 usa 150 ms | 02 §2 | ✅ Justificada |
| 30 | Refinamiento del pico R | Parábola de 3 puntos | Datos | Prueba de dos fases a 50 Hz: el desacuerdo baja de ~10 a 2,5 ms | 02 §3 | ✅ Justificada |

## Serie RR

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 31 | RR posibles | 0,3–2 s | Física | 30 a 200 latidos por minuto: fuera de ese rango no es un ritmo posible en reposo. Argumento fisiológico sin cita | 02 §4 | 🟡 Parcial |
| 32 | RR atípico | > 20 % de la mediana de 11 vecinos | Bibliografía, Datos | Criterio estándar (Malik y Camm, 1995; Clifford et al., 2002); en los datos separa la variación normal de los errores, no corrige más en apnea, y entre 10 % y 40 % la detección no cambia | 02 §4 | ✅ Justificada |
| 33 | Referencia local | Mediana de 11 vecinos (en vez del intervalo anterior) | Física | Robusta a un valor raro suelto; 11 latidos ≈ 10 s ≈ 2–3 respiraciones. No se comparó con otras referencias | 02 §4 | 🟡 Parcial |
| 34 | Reemplazo de los RR corregidos | Interpolación lineal | Bibliografía, Datos | Welch necesita una serie continua; interpolar puede sesgar el espectro con muchos latidos corregidos (Lippman et al., 1994), acá son el 0,36 %. No se comparó con borrarlos | 02 §4 | 🟡 Parcial |
| 35 | Exclusión de minutos | > 20 % de RR corregidos | Convención, Datos | Ahí la serie es más interpolación que dato; se verificó que no excluye más minutos con apnea. El valor de 20 % es convencional | 02 §4 | 🟡 Parcial |
| 36 | Supuesto de ritmo sinusal | La limpieza toma la irregularidad como error | Datos | Con una arritmia sostenida (c04, x29) se excluye casi toda la noche | 06 §3 | ⚠️ Limitación |

## EDR y Wiener

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 37 | Medida de la EDR | Área con signo del QRS | Bibliografía, Datos | Moody et al. (1985); mejor que la amplitud R, la deriva y área + deriva en coherencia y AUC | 03 §1, §2, §6 | ✅ Justificada |
| 38 | Ventana del área | ±60 ms del pico R | Física, Bibliografía | El QRS dura ~80–100 ms (Moody et al., 1985) | 03 §2 | ✅ Justificada |
| 39 | Polaridad por registro | Signo de la deflexión dominante | Datos | Hay registros con el QRS invertido | 03 §2; edr.py | ✅ Justificada |
| 40 | Filtro de Wiener | H = S_s / (S_s + S_n) | Bibliografía, Datos | Wiener (1949); promediado coherente (Sörnmo y Laguna, 2005); su efecto se mide en 03 §6 | 03 §5 | ✅ Justificada |
| 41 | Realizaciones | −250 a +400 ms del pico R | Física | El largo de un latido (onda P, QRS y casi toda la T) | 03 §5 | ✅ Justificada |
| 42 | Implementación del Wiener | FIR de 129 coeficientes (firwin2), plantilla = media de las realizaciones, extensión por reflexión | — | No se discute por qué 129 coeficientes ni media en lugar de mediana | wiener.py | ❌ Sin justificar |
| 43 | Excluir latidos ectópicos | Los que corrige la limpieza del RR | Datos | Parte de la variante elegida (03 §6) | 03 §6 | ✅ Justificada |
| 44 | Filtro de Hampel | 3 desvíos robustos, 11 vecinos, piso de ruido por diferencias | Bibliografía, Datos | Hampel (1974); el piso evita marcar las crestas de la respiración (visto en datos) | 03 §6 | ✅ Justificada |
| 45 | Variante de EDR elegida | Wiener + exclusiones juntas | Datos | Solo la combinación mejora de forma significativa el AUC dentro de la noche (+0,036 [+0,005; +0,087]) | 03 §6 | ✅ Justificada |
| 46 | Medidas para elegir la variante | A1 coherencia con la respiración, A2 con la envolvente, B AUC dentro de la noche | Diseño | Cada una responde una pregunta (sigue cada respiración, sigue el ciclo de apnea, detecta) | 03 §6 | ✅ Justificada |
| 47 | Detalles de A1 y A2 | Segmentos de 32 s dentro de ventanas de 120 s; ponderada por el espectro de la respiración; media de los tres canales respiratorios | Diseño | Elegidos para la banda respiratoria; no se analizaron otras opciones | 03 §6; edr.py | 🟡 Parcial |
| 48 | Envolvente de la respiración | Valor eficaz en 10 s | Física | 2–3 respiraciones: sigue la amplitud y no cada respiración. Sin cita ni comparación | 03 §4 | 🟡 Parcial |
| 49 | EDR relativa | Área / mediana del área sin signo del registro | Datos | Sin dividir, el nivel de la EDR sigue al tamaño del QRS (ρ 0,70); dividiendo, no (ρ −0,02) | 03 §7; 04 §13 | ✅ Justificada |
| 50 | Remuestreo | 2 Hz, spline cúbico | Física, Bibliografía, Datos | Welch necesita muestras equiespaciadas (Task Force, 1996); 2 Hz > frecuencia cardíaca (0,8–1,4 Hz); lineal da lo mismo (04 §15) | 04 §1, §15 | ✅ Justificada |

## Feature y detector

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 51 | Ventana de análisis | 240 s | Física, Datos | Para ver 0,01 Hz cada segmento debe durar > 100 s; entre 180 y 360 s el resultado casi no cambia | 01 §7; 04 §1, §15 | ✅ Justificada |
| 52 | Ventana centrada en el minuto | Usa 90 s antes y después del minuto | — | Implícita: el análisis es fuera de línea, así que puede usar datos posteriores. No se discute | detector.py | 🟡 Parcial |
| 53 | Estimador espectral | Welch, 3 segmentos de 120 s, Hann, 50 % de solapamiento | Bibliografía, Física | Welch (1967); resolución 1/120 Hz. La ventana de Hann no tiene cita (podría citarse Harris, 1978) | 04 §1 | ✅ Justificada |
| 54 | Quitar la tendencia lineal en cada segmento | detrend lineal antes de la FFT | — | No se discute; evita que una tendencia dentro del segmento se filtre a las frecuencias más bajas de la banda | coupling.py | ❌ Sin justificar |
| 55 | Escala logarítmica | log10 de la potencia | Física | La potencia varía en órdenes de magnitud; no se muestra la distribución | 04 §1 | 🟡 Parcial |
| 56 | Potencia en la banda | Promedio de la PSD en k = 2…6 (k/120 Hz) | Física | Son las 5 frecuencias de la grilla que caen en la banda | 04 §1 | ✅ Justificada |
| 57 | Feature combinada C | RR del minuto + w · nivel nocturno de la EDR | Datos | El RR ubica la apnea dentro de la noche y el nivel de la EDR estima cuánta tiene la noche (04 §6); le gana al RR solo y empata con G, F y la logística (04 §8) | 04 §6–8 | ✅ Justificada |
| 58 | Nivel nocturno | Mediana de P_EDR en la noche | Física | Robusta y sin etiquetas; no se comparó con la media | 04 §6 | 🟡 Parcial |
| 59 | Estandarización | μ y σ globales de desarrollo | Datos | Es un cambio de unidades; centrar por noche (G) no mejora | 04 §7 | ✅ Justificada |
| 60 | Peso w | 1 (grilla 0–3 cada 0,25) | Datos | Validación cruzada por personas; el rango de la grilla es convencional | 04 §7 | ✅ Justificada |
| 61 | Conservar F como comparación | F = potencia cruzada RR–EDR | Diseño | Permite medir cuánto cambia respecto de la primera versión | 04 §1, §8 | ✅ Justificada |
| 62 | Umbral | Youden: C > 0,489 | Bibliografía, Datos | Youden (1950); óptimo según costos y prevalencia (Metz, 1978; Zweig y Campbell, 1993; Habibzadeh et al., 2016); recomendado frente al punto más cercano a (0,1) (Perkins y Schisterman, 2006; Ünal, 2017); optimismo corregido con validación cruzada (Fluss et al., 2005); los criterios alternativos dan la misma exactitud balanceada | 04 §9 | ✅ Justificada |
| 63 | Minutos evaluados | Con etiqueta y ≤ 20 % de RR corregidos | Convención, Datos | Mismo criterio que la limpieza del RR | 04 §1 | 🟡 Parcial |
| 64 | Vigilia y primera hora | Se evalúan como el resto (no se excluyen) | Datos | Implícita; el análisis de errores muestra más falsos positivos en la primera hora | 04 §11 | 🟡 Parcial |
| 65 | Medida de movimiento | Varianza del ECG < 0,5 Hz (Butterworth orden 2), relativa a la noche | Datos | En desarrollo el acierto baja en el decil de más movimiento; el filtro de orden 2 no se discute | 04 §12 | 🟡 Parcial |
| 66 | Cortes de la confianza | Percentiles 50 y 90 del movimiento | Convención | Convencionales; en test la confianza no separa (exactitud 0,79 / 0,77 / 0,76) | 04 §12; 05 §3.2 | ⚠️ Limitación |
| 67 | RR con Lomb (comparación) | Grilla de 0,0025 Hz; ≥ 20 latidos en la ventana | Bibliografía | Lomb (1976); Laguna et al. (1998); solo para comparar | 04 §1 | ✅ Justificada |

## Evaluación y estadística

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 68 | Medidas de clasificación | Sensibilidad, especificidad, exactitud | Diseño | Estándar; explicadas en 04 'Cómo se evalúa' | 04 | ✅ Justificada |
| 69 | AUC | Igual al U de Mann–Whitney normalizado | Bibliografía | Hanley y McNeil (1982) | 04 | ✅ Justificada |
| 70 | AUC dentro de la noche | Comparar minutos de una misma noche | Diseño | Aísla las diferencias entre personas | 04 §3 | ✅ Justificada |
| 71 | Mínimo por noche para el AUC dentro de la noche | ≥ 20 minutos de cada tipo | Convención | Con menos minutos el AUC de una noche es inestable; el valor 20 no se analizó | 04 §3 | 🟡 Parcial |
| 72 | Resumen del AUC dentro de la noche | Media en P1 y en 05; mediana en las tablas de 04 | — | Inconsistencia: conviene usar una sola o explicar por qué cambia | 04 §3, §8, §14; 05 | ❌ Sin justificar |
| 73 | Correlación por noche | Spearman | Bibliografía | No supone relación lineal (Spearman, 1904) | 04 | ✅ Justificada |
| 74 | Intervalos de confianza | Bootstrap por personas, percentiles 2,5–97,5 | Bibliografía, Datos | Efron y Tibshirani (1993); los minutos de una noche no son independientes | 04 | ✅ Justificada |
| 75 | Cantidad de remuestreos | 2000 o 4000 | Convención | No se verificó la estabilidad de los intervalos | 04; 05 | 🟡 Parcial |
| 76 | Validación cruzada | 5 grupos de personas, semilla 2026 | Convención | ~4 personas por grupo con 19 personas; no se probaron otros números de grupos | 04 §7 | 🟡 Parcial |
| 77 | Criterio de las predicciones | IC 95 % que no incluye 0,5 (AUC) o 0 (ρ) | Convención | Nivel de confianza estándar, fijado antes de abrir test | objetivos_hipotesis.md | ✅ Justificada |
| 78 | Comparaciones múltiples | Muchas diferencias con IC 95 % sin corrección | — | No se discute la multiplicidad (9 candidatas × 7 medidas en 04 §8) | 04 §8; 05 §3.1 | ❌ Sin justificar |
| 79 | Reformular la hipótesis con C | Después de analizar desarrollo | Datos | Justificada por 04 §6; el riesgo está declarado (limitación 13) y test la confirmó | objetivos_hipotesis.md | ✅ Justificada |

## Test

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 80 | Evaluación única con registro previo | Notebook sin ejecutar registrado (commit 414d3e0), probado en modo ensayo | Diseño | Evita ajustar el análisis después de ver test | 05 | ✅ Justificada |
| 81 | Parámetros congelados | parametros_test.json verificado por hash | Diseño | Garantiza que test usa lo fijado en 04 | 05 §1 | ✅ Justificada |
| 82 | Umbrales de F y RR solo | Youden con desarrollo | Diseño | Mismo criterio que C; solo para las preguntas secundarias | 05 §1 | ✅ Justificada |
| 83 | Análisis posterior | Descriptivo, en un notebook aparte, a pedido del grupo | Diseño | No cambia la evaluación; queda marcado como posterior | 06 | ✅ Justificada |

## Interfaz

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 84 | Tecnología | Streamlit + Plotly | Grupo | Elegida por el grupo: fácil de mostrar en la defensa | app/visor.py | ✅ Justificada |
| 85 | Registros que muestra | Solo desarrollo; test con VISOR_INCLUIR_TEST=1 | Diseño | Regla de no mirar test antes de la evaluación | app/visor.py | ✅ Justificada |

## Lo que falta justificar

| # | Decisión | Qué hacer |
|---|---|---|
| 42 | Implementación del Wiener | Explicar los 129 coeficientes (respuesta al impulso de 1,3 s, más larga que un latido) y por qué la media, o probar la sensibilidad a esos valores |
| 54 | Quitar la tendencia lineal en cada segmento | Explicar que evita que la tendencia dentro de cada segmento de 120 s infle las frecuencias más bajas; opcional: comparar con quitar solo la media |
| 72 | Resumen del AUC dentro de la noche | Unificar (media en todo el trabajo) o explicar por qué P1 usa la media |
| 78 | Comparaciones múltiples | Aclarar que las comparaciones de 04 §8 y 05 §3.1 son descriptivas y que la prueba de la hipótesis son las tres predicciones con criterio fijado de antemano |

Las 🟡 son en su mayoría convenciones razonables (70/30, 5 grupos, 20 minutos por noche, cantidad de remuestreos, percentiles de la confianza). En la defensa conviene decir que son convenciones; donde se probó la sensibilidad (ventana, interpolación, umbrales del detector, regla del 20 %, criterio del umbral), el resultado no cambió.
