# Auditoría de decisiones

Cada decisión del proyecto (código y notebooks `01`–`06`), con el tipo de justificación y si está justificada. Complementa a [`decisiones.md`](decisiones.md), que detalla los valores y la bibliografía completa.

**Estados.**
- ✅ **Justificada**: con datos (figura o número en un notebook), bibliografía o un argumento físico verificable.
- 🟡 **Parcial**: tiene un argumento razonable, pero el valor exacto es una convención o no se comparó con alternativas.
- ❌ **Sin justificar**: elección de implementación que no se discute en ningún lado.
- ⚠️ **Limitación**: está justificada pero se mostró que falla en algún caso.

**Tipos de justificación.** *Datos*: medido en desarrollo. *Bibliografía*: método publicado o recomendación. *Física*: propiedad de la señal o fisiología. *Convención*: valor habitual sin análisis propio. *Diseño*: regla de trabajo o pregunta que responde. *Grupo*: elección del grupo.

**Resumen:** 88 decisiones: ✅ 86 justificadas, 🟡 0 parciales, ❌ 0 sin justificar, ⚠️ 2 limitaciones.


## Base y partición

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 1 | Base de datos | Apnea-ECG (PhysioNet): ECG de una derivación, 100 Hz, etiqueta por minuto | Bibliografía, Diseño | Base pública de referencia para este problema (challenge de PhysioNet 2000), con ECG de una derivación y etiquetas de apnea por minuto (Penzel et al., 2000) | 01 §1 | ✅ Justificada |
| 2 | Unidad de decisión | 1 minuto | Datos | Las etiquetas de la base son por minuto | 01 §3; 04 §1 | ✅ Justificada |
| 3 | Excluir grabaciones duplicadas | c05, x22, x33 | Datos, Bibliografía | Muestras idénticas con desfase; c05/c06 documentado por PhysioNet, los otros dos pares encontrados comparando las señales | 01 §2 (decisión 1) | ✅ Justificada |
| 4 | Cuál de cada par se conserva | La que empieza antes | Convención | Es la misma señal: la elección no cambia nada | config.py | ✅ Justificada |
| 5 | Detección de duplicados | Plantilla de latido (0,5–40 Hz, horas 1–4, latidos estables) y correlación de 5 min; r ≥ 0,99 | Datos | Los tres duplicados tienen correlación de la señal 1,000; los 10 pares no duplicados con el latido más parecido no pasan de 0,29. El umbral de 0,99 queda en un hueco amplio. Usa el mismo filtro y criterio de latido normal que el pipeline | 01 §2 | ✅ Justificada |
| 6 | Agrupar registros por persona | Perfil idéntico (edad, sexo, altura, peso) | Datos | 52 pares con perfil idéntico contra ≤ 3 esperados por azar; verificación con la forma del latido (44 % contra 2 % de pares casi idénticos) | 01 §2 (decisión 2) | ✅ Justificada |
| 7 | Partir por persona | Ninguna persona en los dos conjuntos | Datos | Las noches de una persona se parecen: el latido más parecido es de la misma persona en 32 de 46 registros, y el % de apnea difiere 7 puntos entre noches de una persona contra 37,5 entre personas distintas | 01 §2 (decisión 3) | ✅ Justificada |
| 8 | Proporción de la partición | 70 % desarrollo, 30 % test | Bibliografía, Datos | Con muestras chicas conviene asignar más al entrenamiento; 2/3 resultó cercano al óptimo (Dobbin y Simon, 2011). Con 30 % test tiene personas de las tres categorías (12 A, 3 B, 5 C) | 01 §2 (decisión 4) | ✅ Justificada |
| 9 | Estratificar por categoría | Mismas proporciones de A, B y C | Diseño | El detector se evalúa también por noche y por categoría | 01 §2 (decisión 5) | ✅ Justificada |
| 10 | Balancear la apnea | Diferencia ≤ 2 puntos en % de minutos con apnea | Datos | Tolerancias de 0,5 a 5 puntos dejan de 262 a 1993 particiones; con 2 puntos quedan 853 y la diferencia final es de 0,5 puntos, chica frente a la variación entre noches (0–97 %) | 01 §2 (decisión 6) | ✅ Justificada |
| 11 | Registros con respiración | Siempre en desarrollo | Diseño | Son los únicos con los que se puede validar la EDR | 01 §2 (decisión 7) | ✅ Justificada |
| 12 | Elección de la partición | Sorteo con semilla 2026 entre las 853 válidas | Diseño | Nadie elige qué personas van a test | 01 §2 (decisión 8) | ✅ Justificada |
| 13 | Categoría de los registros x | Regla por minutos: ≥ 100 → A, < 5 → C, resto B | Bibliografía | Aproximación documentada a los criterios de Penzel et al. (2000), que además piden índices por hora | split.py; 01 §1 | ✅ Justificada |
| 14 | Uso de los datos de test antes de la evaluación | Solo los de la partición (categoría, minutos con apnea, perfil) | Diseño | Solo los datos de la partición (categoría, minutos con apnea, perfil) y la detección de duplicados, que necesariamente compara todas las grabaciones | 01 §2 | ✅ Justificada |

## Exploración y calidad

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 15 | Umbrales descriptivos de calidad | Tramo plano ≥ 1 s; sin ECG si la energía en 5–15 Hz < 10 %; deriva o interferencia > 10 % | Física, Datos | Solo describen la base; ninguno excluye datos. La señal perdida es estable entre 1 y 2 s (191 y 190 minutos) porque un ECG de 12 bits no queda constante un segundo; la deriva marca los mismos 20 registros con 5, 10 o 20 %. El resto mide magnitud y cambia con el umbral, como se espera | 01 §5 | ✅ Justificada |
| 16 | PSD del ECG | Welch, 4096 muestras (~41 s) | Física | Resolución de 0,024 Hz, suficiente para el latido y sus armónicos; descriptivo | 01 §5 | ✅ Justificada |
| 17 | Espectrograma | Ventanas de 30 s | Física | Compromiso tiempo–frecuencia; descriptivo | 01 §5 | ✅ Justificada |
| 18 | Banda de la apnea | 0,01–0,05 Hz | Datos, Bibliografía | Máximo aumento de potencia del RR con apnea dentro de cada registro (pico 0,025 Hz; −3 dB entre 0,017 y 0,05 Hz, las mismas cinco frecuencias k = 2…6); ciclos de 20–100 s (Guilleminault et al., 1984) | 01 §7 | ✅ Justificada |
| 19 | Misma banda para la EDR | 0,01–0,05 Hz | Datos | En la EDR la banda a −3 dB es 0,017–0,033 Hz, dentro de la elegida y con el mismo pico (0,025 Hz). Limitar la EDR a 0,01–0,033 Hz baja la exactitud (−0,011, IC sin el cero) | 01 §7; 04 §15 | ✅ Justificada |

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
| 28 | Detalles internos del detector | Ubicación del pico ±80 ms; ventana de forma ±100 ms; mínimo 3 plantillas; prominencia en 2 s; energía rápida en ±50 ms con Butterworth de orden 2 | Física, Datos | Búsqueda del pico R, ventana y mínimo de la forma, ventana de la prominencia, ventana y orden de la energía rápida: moviendo cada uno cambia como mucho el 0,5 % de los latidos del peor registro y ningún registro supera el 1 % | 02 §2 | ✅ Justificada |
| 29 | Tolerancia de comparación | 100 ms | Datos, Bibliografía | Las fuentes coinciden a < 30 ms; entre 30 y 150 ms cambia < 1 punto; bxb, la implementación de referencia de PhysioNet para ANSI/AAMI EC38/EC57, usa 150 ms | 02 §2 | ✅ Justificada |
| 30 | Refinamiento del pico R | Parábola de 3 puntos | Datos | Prueba de dos fases a 50 Hz: el desacuerdo baja de ~10 a 2,5 ms | 02 §3 | ✅ Justificada |

## Serie RR

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 31 | RR posibles | 0,3–2 s | Física, Datos | 30 a 200 lpm. En desarrollo solo el 0,07 % de los RR cae fuera y el 99,8 % está entre 0,5 y 1,6 s; lo que cae fuera son pausas sin ECG y detecciones dobles | 02 §4 | ✅ Justificada |
| 32 | RR atípico | > 20 % de la mediana de 11 vecinos | Bibliografía, Datos | Criterio estándar (Clifford et al., 2002). Separa la variación normal (97 % dentro de ±10 %) de los errores, no corrige más en apnea, y entre 10 % y 40 % el AUC no cambia (0,905–0,908) | 02 §4 | ✅ Justificada |
| 33 | Referencia local | Mediana de 11 vecinos (en vez del intervalo anterior) | Bibliografía, Datos | Clifford et al. (2002) usan el intervalo anterior. Con la mediana de 5 o 21 vecinos o con el intervalo anterior el AUC no mejora (diferencias ≤ 0,002) y con 21 o el anterior se corrige un 50 % más de RR | 02 §4 | ✅ Justificada |
| 34 | Reemplazo de los RR corregidos | Interpolación lineal | Bibliografía, Datos | Interpolar puede sesgar el espectro con muchos ectópicos (Lippman et al., 1994; Peltola, 2012). Con el 0,5 % corregido, lineal, cúbica y borrar el latido dan el mismo AUC (dentro de 0,001) | 02 §4 | ✅ Justificada |
| 35 | Exclusión de minutos | > 20 % de RR corregidos | Datos | Con 10 %, 30 %, 50 % o sin excluir, el AUC va de 0,907 a 0,909; el límite de 20 % cuesta el 0,2 % de los minutos | 02 §4 | ✅ Justificada |
| 36 | Supuesto de ritmo sinusal | La limpieza toma la irregularidad como error | Datos | Con una arritmia sostenida (c04, x29) se excluye casi toda la noche | 06 §3 | ⚠️ Limitación |

## EDR y Wiener

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 37 | Medida de la EDR | Área con signo del QRS | Bibliografía, Datos | Método establecido de EDR (Charlton et al., 2018; Varon et al., 2020). Sigue mejor la respiración que la amplitud R y la deriva, y detecta mejor que la deriva | 03 §1, §2, §6 | ✅ Justificada |
| 38 | Ventana del área | ±60 ms del pico R | Física, Bibliografía | El QRS dura ~80–100 ms; métodos de área del QRS (Varon et al., 2020) | 03 §2 | ✅ Justificada |
| 39 | Polaridad por registro | Signo de la deflexión dominante | Datos | Hay registros con el QRS invertido | 03 §2; edr.py | ✅ Justificada |
| 40 | Filtro de Wiener | H = S_s / (S_s + S_n) | Bibliografía, Datos | Wiener (1949); promediado coherente (Sörnmo y Laguna, 2005); su efecto se mide en 03 §6 | 03 §5 | ✅ Justificada |
| 41 | Realizaciones | −250 a +400 ms del pico R | Física | El largo de un latido (onda P, QRS y casi toda la T) | 03 §5 | ✅ Justificada |
| 42 | Implementación del Wiener | FIR de 129 coeficientes (firwin2), plantilla = media de las realizaciones, extensión por reflexión | Física, Bibliografía, Datos | H(f) tiene una resolución real de ~1,5 Hz (realizaciones de 0,65 s) y 129 coeficientes siguen ~0,8 Hz (firwin2; Virtanen et al., 2020). Desde 65 coeficientes A1 y B no cambian más de 0,004; media y mediana dan lo mismo (0,001) | 03 §5–6 | ✅ Justificada |
| 43 | Excluir latidos ectópicos | Los que corrige la limpieza del RR | Datos | Parte de la variante elegida (03 §6) | 03 §6 | ✅ Justificada |
| 44 | Filtro de Hampel | 3 desvíos robustos, 11 vecinos, piso de ruido por diferencias | Bibliografía, Datos | Hampel (1974); el piso evita marcar las crestas de la respiración (visto en datos) | 03 §6 | ✅ Justificada |
| 45 | Variante de EDR elegida | Wiener + exclusiones juntas | Datos | Solo la combinación mejora de forma significativa el AUC dentro de la noche (+0,036 [+0,005; +0,087]) | 03 §6 | ✅ Justificada |
| 46 | Medidas para elegir la variante | A1 coherencia con la respiración, A2 con la envolvente, B AUC dentro de la noche | Diseño | Cada una responde una pregunta (sigue cada respiración, sigue el ciclo de apnea, detecta) | 03 §6 | ✅ Justificada |
| 47 | Detalles de A1 y A2 | Segmentos de 32 s dentro de ventanas de 120 s; ponderada por el espectro de la respiración; media de los tres canales respiratorios | Bibliografía, Datos | Segmentos de 32 s: resolución de ~0,03 Hz con seis segmentos por ventana; la coherencia con pocos segmentos tiene sesgo (Carter, 1987). Con 16 o 64 s el orden de las variantes es el mismo (ρ 1,00 y 0,95) | 03 §6 | ✅ Justificada |
| 48 | Envolvente de la respiración | Valor eficaz en 10 s | Física, Datos | 2–3 respiraciones. Con 5 o 20 s el orden de las variantes en A2 es el mismo (ρ 1,00 y 0,95) | 03 §4, §6 | ✅ Justificada |
| 49 | EDR relativa | Área / mediana del área sin signo del registro | Datos | Sin dividir, el nivel de la EDR sigue al tamaño del QRS (ρ 0,70); dividiendo, no (ρ −0,02) | 03 §7; 04 §13 | ✅ Justificada |
| 50 | Remuestreo | 2 Hz, spline cúbico | Física, Bibliografía, Datos | Welch necesita muestras equiespaciadas (Task Force, 1996); 2 Hz > frecuencia cardíaca (0,8–1,4 Hz); lineal da lo mismo (04 §15) | 04 §1, §15 | ✅ Justificada |

## Feature y detector

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 51 | Ventana de análisis | 240 s | Física, Datos | Para ver 0,01 Hz cada segmento debe durar > 100 s. Con 180, 300 o 360 s la exactitud baja ~0,01 (IC sin el cero) | 01 §7; 04 §1, §15 | ✅ Justificada |
| 52 | Ventana centrada en el minuto | Usa 90 s antes y después del minuto | Datos | El análisis es fuera de línea. Con una ventana que termina al final del minuto la exactitud baja 0,005 (IC sin el cero) y el AUC dentro de la noche pasa de 0,908 a 0,894 | 04 §15 | ✅ Justificada |
| 53 | Estimador espectral | Welch, 3 segmentos de 120 s, Hann, 50 % de solapamiento | Bibliografía, Física | Welch (1967); resolución 1/120 Hz | 04 §1 | ✅ Justificada |
| 54 | Quitar la tendencia lineal en cada segmento | detrend lineal antes de la FFT | Bibliografía, Datos | Práctica habitual (Tarvainen et al., 2002). La figura muestra que con Hann la deriva queda casi toda en k ≤ 1; con los datos, no quitarla da lo mismo (+0,002, IC con el cero). Se mantiene como protección | 04 §15 | ✅ Justificada |
| 55 | Banda de la EDR | La misma que la del RR (0,01–0,05 Hz) | Datos | Limitarla a su banda a −3 dB (0,01–0,033 Hz) baja la exactitud (−0,011, IC sin el cero) | 04 §15 | ✅ Justificada |
| 56 | Escala logarítmica | log10 de la potencia | Física, Datos | En escala lineal C es la peor variante: exactitud −0,052 (IC sin el cero) y ρ por noche 0,66 | 04 §15 | ✅ Justificada |
| 57 | Potencia en la banda | Promedio de la PSD en k = 2…6 (k/120 Hz) | Física | Son las 5 frecuencias de la grilla que caen en la banda | 04 §1 | ✅ Justificada |
| 58 | Feature combinada C | RR del minuto + w · nivel nocturno de la EDR | Datos | El RR ubica la apnea dentro de la noche y el nivel de la EDR estima cuánta tiene la noche (04 §6); le gana al RR solo y empata con G, F y la logística (04 §8) | 04 §6–8 | ✅ Justificada |
| 59 | Nivel nocturno | Mediana de P_EDR en la noche | Datos | Con la media da lo mismo (−0,001, IC con el cero); la mediana es robusta a minutos con movimiento | 04 §15 | ✅ Justificada |
| 60 | Estandarización | μ y σ globales de desarrollo | Datos | Es un cambio de unidades; centrar por noche (G) no mejora | 04 §7 | ✅ Justificada |
| 61 | Peso w | 1 (grilla 0–3 cada 0,25) | Datos | Validación cruzada por personas; el rango de la grilla es convencional | 04 §7 | ✅ Justificada |
| 62 | Conservar F como comparación | F = potencia cruzada RR–EDR | Diseño | Permite medir cuánto cambia respecto de la primera versión | 04 §1, §8 | ✅ Justificada |
| 63 | Umbral | Youden: C > 0,489 | Bibliografía, Datos | Youden (1950); óptimo según costos y prevalencia (Metz, 1978; Zweig y Campbell, 1993; Habibzadeh et al., 2016); recomendado frente al punto más cercano a (0,1) (Perkins y Schisterman, 2006; Ünal, 2017); la estimación empírica tiene sesgo (Fluss et al., 2005) y se evalúa con validación cruzada; los criterios alternativos dan la misma exactitud balanceada | 04 §9 | ✅ Justificada |
| 64 | Minutos evaluados | Con etiqueta y ≤ 20 % de RR corregidos | Datos | Mismo criterio que la limpieza del RR, cuyas alternativas no cambian la detección (02 §4) | 04 §1; 02 §4 | ✅ Justificada |
| 65 | Vigilia y primera hora | Se evalúan como el resto (no se excluyen) | Datos | Sin la primera hora la exactitud no cambia (−0,004, IC con el cero); se evalúa toda la noche porque así está etiquetada la base | 04 §11, §15 | ✅ Justificada |
| 66 | Medida de movimiento | Varianza del ECG < 0,5 Hz (Butterworth orden 2), relativa a la noche | Datos | Mide lo que el filtro saca (< 0,5 Hz); en desarrollo el acierto baja en el decil de más movimiento. El orden 2 del pasabajos quedó fijado antes de test y no se cambia | 04 §12 | ✅ Justificada |
| 67 | Cortes de la confianza | Percentiles 50 y 90 del movimiento | Convención | Convencionales; en test la confianza no separa (exactitud 0,79 / 0,77 / 0,76) | 04 §12; 05 §3.2 | ⚠️ Limitación |
| 68 | RR con Lomb (comparación) | Grilla de 0,0025 Hz; ≥ 20 latidos en la ventana | Bibliografía | Lomb (1976); Laguna et al. (1998); solo para comparar | 04 §1 | ✅ Justificada |

## Evaluación y estadística

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 69 | Medidas de clasificación | Sensibilidad, especificidad, exactitud | Diseño | Estándar; explicadas en 04 'Cómo se evalúa' | 04 | ✅ Justificada |
| 70 | AUC | Igual al U de Mann–Whitney normalizado | Bibliografía | Hanley y McNeil (1982) | 04 | ✅ Justificada |
| 71 | AUC dentro de la noche | Comparar minutos de una misma noche | Diseño | Aísla las diferencias entre personas | 04 §3 | ✅ Justificada |
| 72 | Mínimo por noche para el AUC dentro de la noche | ≥ 20 minutos de cada tipo | Bibliografía, Datos | Error estándar con 20 minutos de cada tipo ≈ 0,05 (Hanley y McNeil, 1982); con 10, ≈ 0,07 y solo 3 noches más; con 30 o 40 el AUC medio no cambia | 04 §15 | ✅ Justificada |
| 73 | Resumen del AUC dentro de la noche | Media en P1 y en 05; mediana en las tablas de 04 | Diseño | Media en todo el trabajo, la medida fijada para P1. Un test automático impide volver a usar la mediana | 04; tests/test_consistencia.py | ✅ Justificada |
| 74 | Correlación por noche | Spearman | Bibliografía | No supone relación lineal (Spearman, 1904) | 04 | ✅ Justificada |
| 75 | Intervalos de confianza | Bootstrap por personas, percentiles 2,5–97,5 | Bibliografía, Datos | Efron y Tibshirani (1993); los minutos de una noche no son independientes | 04 | ✅ Justificada |
| 76 | Cantidad de remuestreos | 2000 o 4000 | Bibliografía, Datos | Efron y Tibshirani (1993). Con 2000 los extremos del intervalo cambian < 0,002 entre semillas; con 4000, < 0,001 | 04 §15 | ✅ Justificada |
| 77 | Validación cruzada | 5 grupos de personas, semilla 2026 | Bibliografía, Datos | Compromiso entre sesgo y varianza (Arlot y Celisse, 2010); con 10 grupos o una persona por grupo la exactitud es la misma (−0,001 y +0,006) | 04 §7, §15 | ✅ Justificada |
| 78 | Criterio de las predicciones | IC 95 % que no incluye 0,5 (AUC) o 0 (ρ) | Bibliografía | IC 95 % fijado antes de abrir test; como hacen falta las tres, la prueba de unión-intersección no necesita corrección (Berger, 1982) | objetivos_hipotesis.md; 04 §14 | ✅ Justificada |
| 79 | Comparaciones múltiples | Muchas diferencias con IC 95 % sin corrección | Bibliografía, Datos | Corrección de Holm (Aickin y Gensler, 1996). En desarrollo resisten 4 de 21 diferencias (las ventajas de C sobre F no); en test, 3 de 13: C da menos falsas alarmas que F y que el RR solo | 04 §8; 06 §5 | ✅ Justificada |
| 80 | Reformular la hipótesis con C | Después de analizar desarrollo | Datos | Justificada por 04 §6; el riesgo está declarado (limitación 13) y test la confirmó | objetivos_hipotesis.md | ✅ Justificada |

## Test

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 81 | Evaluación única con registro previo | Notebook sin ejecutar registrado (commit 414d3e0), probado en modo ensayo | Diseño | Evita ajustar el análisis después de ver test | 05 | ✅ Justificada |
| 82 | Parámetros congelados | parametros_test.json verificado por hash | Diseño | Garantiza que test usa lo fijado en 04 | 05 §1 | ✅ Justificada |
| 83 | Umbrales de F y RR solo | Youden con desarrollo | Diseño | Mismo criterio que C; solo para las preguntas secundarias | 05 §1 | ✅ Justificada |
| 84 | Análisis posterior | Descriptivo, en un notebook aparte, a pedido del grupo | Diseño | No cambia la evaluación; queda marcado como posterior | 06 | ✅ Justificada |

## Interfaz

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 85 | Tecnología | Streamlit + Plotly | Grupo | Elegida por el grupo: fácil de mostrar en la defensa | app/visor.py | ✅ Justificada |
| 86 | Registros que muestra | Solo desarrollo; test con VISOR_INCLUIR_TEST=1 | Diseño | Regla de no mirar test antes de la evaluación | app/visor.py | ✅ Justificada |

## Evaluación y estadística

| # | Decisión | Valor | Justificación | Fundamento | Dónde | Estado |
|---|---|---|---|---|---|---|
| 87 | Constantes en un solo lugar | src/config.py y src/features/detector.py | Diseño | Ventana, banda, grilla, regla del RR, mínimo de minutos, realización del latido y segmentos están definidos una vez; un test falla si un notebook los vuelve a escribir a mano | tests/test_consistencia.py | ✅ Justificada |
| 88 | Fuentes citadas | Solo con DOI o página oficial | Diseño | Cada referencia verificada en Crossref, doi.org y PubMed (o PhysioNet); Moody et al. (1985), sin DOI ni copia oficial, se reemplazó por revisiones abiertas | docs/referencias.md; scripts/verificar_referencias.py | ✅ Justificada |

## Limitaciones

| # | Decisión | Qué pasa |
|---|---|---|
| 36 | Supuesto de ritmo sinusal | Con una arritmia sostenida (c04, x29) se excluye casi toda la noche |
| 67 | Cortes de la confianza | Convencionales; en test la confianza no separa (exactitud 0,79 / 0,77 / 0,76) |

## Cómo se verificó

- **Datos:** cada número de la columna Fundamento sale de un notebook ejecutado; las alternativas se compararon con la misma validación (AUC dentro de la noche o validación cruzada por personas) e intervalos por bootstrap de personas.
- **Bibliografía:** cada cita tiene DOI o página oficial, verificados en Crossref, doi.org y PubMed o PhysioNet ([`referencias.md`](referencias.md)).
- **Consistencia:** `tests/test_consistencia.py` falla si un notebook vuelve a escribir a mano una ventana, una banda, el mínimo de minutos o la forma de resumir el AUC.
- **Test intacto:** ninguna de estas pruebas cambió los parámetros congelados para test (`docs/parametros_test.json` tiene el mismo hash que antes de abrir test).
