# Decisiones, umbrales y ventanas

Este documento lista cada número que fija el pipeline, con lo que lo justifica y dónde se muestra. Responde al pedido de la devolución: "fundamentar en bibliografía los umbrales elegidos" y "tener consistencia en las decisiones (no cambiar el tamaño de las ventanas)".

Hay tres tipos de justificación:
- **Datos**: se midió en los registros de desarrollo. El notebook muestra la medición y, cuando hay alternativas, la comparación.
- **Bibliografía**: es el valor de un método publicado o de una recomendación.
- **Física**: sale de una propiedad de la señal, como una resolución o el límite de Nyquist.

Test no interviene en ninguna decisión.

## 1. Ventanas y duraciones

Hay **una sola ventana de análisis**: 240 s centrada en cada minuto. Se usa igual para explorar la banda (`01` §7), para elegir la variante de EDR (`03` §6, medida B) y para el detector (`04`). Las demás duraciones de la tabla no son ventanas de análisis alternativas. Son el largo de un objeto, como un latido o un QRS, o se usan solo para mirar las señales.

| Duración | Valor | Para qué | Por qué | Tipo | Dónde |
|---|---|---|---|---|---|
| Unidad de decisión | 1 min | El detector decide por minuto | Las etiquetas de la base son por minuto (Penzel et al., 2000) | Datos | `01` §3 |
| **Ventana de análisis** | **240 s, centrada en el minuto** | Estimar el espectro de RR y EDR de cada minuto | Para ver 0,01 Hz (período de 100 s), cada segmento del estimador tiene que durar más de 100 s. 3 segmentos de 120 s con 50 % de solapamiento ocupan 240 s. Con 180 a 360 s el resultado casi no cambia y 240 s queda apenas mejor | Física + datos | `01` §7, `04` §1 y §15 |
| Segmento de Welch | 120 s, Hann, 50 % de solapamiento | Dentro de la ventana de 240 s | La resolución es 1/120 ≈ 0,008 Hz, y la banda 0,01–0,05 Hz cae en k = 2…6. Promediar 3 segmentos baja la varianza (Welch, 1967) | Física + bibliografía | `04` §1 |
| Término de la noche | Toda la noche (mediana) | Nivel nocturno de la EDR en C | El nivel de la EDR sigue a la cantidad de apnea de la noche, no al minuto | Datos | `04` §6 |
| Realización de un latido | −250 a +400 ms del pico R | Estimar los espectros de señal y de ruido para el filtro de Wiener | Es el largo de un latido: cubre la onda P (el intervalo PR dura 120–200 ms), el QRS y casi toda la T. Promediado coherente (Sörnmo y Laguna, 2005) | Física + bibliografía | `03` §5 |
| Área del QRS | ±60 ms del pico R | Valor de la EDR en cada latido | El QRS dura ~80–100 ms. Área del QRS como EDR (Moody et al., 1985) | Física + bibliografía | `03` §2 |
| Deriva de la línea de base | −100 a −50 ms (segmento PR) | Medida alternativa de EDR, descartada | Es el tramo isoeléctrico antes del QRS | Física | `03` §2 y §6 |
| Integración de Pan-Tompkins | 150 ms | Juntar la energía de cada QRS | Valor del método (Pan y Tompkins, 1985) | Bibliografía | `02` §2 |
| Período refractario | 200 ms | No detectar dos QRS seguidos | Pan y Tompkins (1985) | Bibliografía | `02` §2 |
| Ventana de onda T | máx(360 ms; 0,5 RR medio) | Posible onda T después de un QRS | 360 ms es el valor de Pan y Tompkins (1985). Se alarga con el ritmo porque el QT ocupa ~40 % del ciclo (Bazett, 1920). Corrige `x17` | Bibliografía + datos | `02` §2 |
| Forma del QRS | ±100 ms, últimos 8 QRS | Comparar un candidato con los QRS anteriores | Cubre el QRS completo; 8 latidos son ~7 s, así que la forma de referencia sigue cambios lentos | Física + datos | `02` §2 |
| Energía > 20 Hz | ±50 ms | Distinguir QRS de onda T | El QRS tiene energía por encima de 20 Hz y la onda T casi no | Física | `02` §2 |
| Mediana de vecinos | 11 latidos (~10 s) | Limpieza del RR y filtro de Hampel de la EDR | Abarca 2–3 respiraciones: sigue la respiración y aparta solo latidos sueltos | Física + datos | `02` §4, `03` §6 |
| Envolvente de la respiración | Valor eficaz en 10 s | Referencia de la apnea para validar la EDR (no la usa el detector) | Son 2–3 respiraciones; sigue la amplitud y no cada respiración | Física | `03` §4 |
| Coherencia EDR–respiración | Segmentos de 120 s | Validar la EDR (no la usa el detector) | El mismo segmento que el detector | Consistencia | `03` §3 y §6 |
| Exploración: PSD del ECG | Welch, 4096 muestras (~41 s) | Ver el espectro del ECG de cada registro | Resolución de 0,024 Hz, suficiente para el latido y sus armónicos. Solo descriptivo | Física | `01` §5 |
| Exploración: espectrograma | 30 s | Ver cómo cambia el espectro del ECG en la noche | Compromiso entre resolución en tiempo y en frecuencia (0,033 Hz). Solo descriptivo | Física | `01` §5 |
| Movimiento | La misma ventana de 240 s | Medida de confianza | Mismo soporte que la decisión | Consistencia | `04` §12 |

## 2. Parámetros de cada etapa

### Base y partición (`01`)

| Decisión | Valor | Justificación | Tipo |
|---|---|---|---|
| Registros excluidos | c05, x22, x33 | Son la misma grabación que c06, x35 y x34: tienen muestras idénticas con un desfase. c05/c06 lo documenta PhysioNet; los otros dos pares se encontraron comparando las señales | Datos |
| Sujetos | 29 personas en 67 registros | Se infieren del perfil (edad, sexo, altura, peso) y se verifican con la forma del latido: 46 % de pares de latidos casi idénticos dentro de una misma persona contra 2 % entre personas distintas | Datos |
| Partición | Por persona, 70/30, estratificada por categoría, diferencia de apnea ≤ 2 puntos, semilla 2026 | Separar por persona evita que el detector "reconozca" a alguien de desarrollo. La proporción 70/30 es una convención; la estratificación y el balance de apnea hacen que los dos conjuntos sean comparables. La semilla queda fija entre 853 particiones válidas | Datos + convención |
| Personas con respiración | Siempre en desarrollo | Sus registros se usan para validar la EDR | Diseño |

### Filtro (`02` §1)

| Parámetro | Valor | Justificación | Tipo |
|---|---|---|---|
| Banda de paso | 0,77–41,8 Hz con ≤ 1 dB | 0,77 Hz es el percentil 1 de la frecuencia cardíaca. 41,8 Hz es el percentil 95 entre registros de la frecuencia que deja abajo el 99 % de la energía del latido | Datos |
| Atenuación de la deriva | ≥ 20 dB a 0,1 Hz | La deriva y el movimiento están por debajo de ~0,5 Hz (`01` §5) | Datos |
| Diseño | Butterworth 0,5–45 Hz, orden 3, ida y vuelta | El orden 3 es el menor que cumple la especificación. El filtro de fase cero no corre el pico R. La AHA admite un corte inferior de hasta 0,67 Hz con filtros de fase cero (Kligfield et al., 2007). El corte alto queda por debajo de 50 Hz (Nyquist e interferencia de línea) | Datos + bibliografía |

### Latidos (`02` §2–4)

| Parámetro | Valor | Justificación | Tipo |
|---|---|---|---|
| Detector | Pan-Tompkins propio, pasabanda 5–15 Hz, derivada de 5 puntos | Pan y Tompkins (1985) | Bibliografía |
| Búsqueda hacia atrás | Hueco de 1,66 RR medios | Pan y Tompkins (1985) | Bibliografía |
| Pulso aislado | Prominencia ≥ 0,5 de la altura | Corrige los tramos sin ECG; la ablación muestra que hace falta | Datos |
| Piso de energía | 5 % de la mediana de los QRS | Corrige el ruido de `x28` (ablación) | Datos |
| Forma | Correlación ≥ 0,5 | Separa ondas T de QRS en la ventana de onda T | Datos |
| Energía rápida | ≥ 30 % de la energía > 20 Hz del QRS anterior | Corrige las ondas T altas de `x17` (ablación) | Datos |
| Sensibilidad de esos umbrales | Mover cada uno entre 40 % y 100 % de su valor | Cambia < 0,5 % de los latidos en el peor registro: el valor exacto no importa | Datos |
| Tolerancia de comparación | 100 ms | Cuando dos fuentes coinciden lo hacen a < 30 ms; entre 30 y 150 ms la sensibilidad y el VPP cambian < 1 punto. La norma ANSI/AAMI EC57 usa 150 ms | Datos + bibliografía |
| Refinamiento del pico R | Parábola de 3 puntos | A 100 Hz el pico cae en una grilla de 10 ms (±5 ms de error). La prueba de dos fases a 50 Hz baja el desacuerdo de ~10 a 2,5 ms | Datos |
| RR posibles | 0,3–2 s | 200 a 30 latidos por minuto: fuera de ese rango no es un ritmo posible durante el sueño | Fisiología |
| RR atípico | > 20 % de la mediana de 11 vecinos | Separa el cuerpo de la distribución (casi todo dentro de ±10 %) de las colas de errores (+100 %, −50 %, −80 %). No corrige más en los minutos con apnea (0,27 % contra 0,23 %), y una regla más laxa no detecta mejor | Datos |
| Reemplazo | Interpolación lineal | Pocos latidos seguidos; conserva la variación lenta | Datos |
| Minuto excluido | > 20 % de RR corregidos | Ahí la serie es más interpolación que dato | Datos + convención |

### EDR y filtro de Wiener (`03`)

| Parámetro | Valor | Justificación | Tipo |
|---|---|---|---|
| Medida | Área del QRS (±60 ms) | Fisiología (Moody et al., 1985). Mejor coherencia con la respiración y mejor AUC dentro de la noche que la amplitud R y la deriva | Bibliografía + datos |
| Filtro de Wiener | H = S_s / (S_s + S_n), con S_s y S_n estimados de las realizaciones | Filtro lineal de mínimo error cuadrático (Wiener, 1949). Promediado coherente (Sörnmo y Laguna, 2005) | Bibliografía |
| Latidos excluidos | Ectópicos (los que corrige la limpieza del RR) y atípicos de Hampel (3 desvíos robustos, 11 vecinos, con piso de ruido) | Hampel (1974). Con una distribución normal, 3 desvíos dejan afuera ~0,3 %. El piso evita marcar las crestas de la respiración | Bibliografía + datos |
| Variante elegida | Wiener + exclusiones juntas | Solo la combinación mejora de forma significativa el AUC dentro de la noche: +0,036 [+0,005; +0,087] | Datos |
| EDR relativa | Área / mediana del área sin signo del registro | El tamaño del QRS cambia entre personas (electrodos, anatomía). Sin dividir, el nivel de la EDR sigue al tamaño del QRS (ρ 0,70); dividiendo, no (ρ −0,02) | Datos |
| Interpolación | Spline cúbico a 2 Hz | Ver la sección 3 | Física + datos |

### Feature y detector (`04`)

| Parámetro | Valor | Justificación | Tipo |
|---|---|---|---|
| Banda | 0,01–0,05 Hz | Donde más sube la potencia del RR durante la apnea, dentro de cada registro (máximo en 0,025 Hz; −3 dB entre 0,017 y 0,05 Hz). Coincide con los ciclos de 20–100 s de la apnea (Guilleminault et al., 1984) | Datos + bibliografía |
| Potencia | log10 del promedio en la banda | La potencia varía en órdenes de magnitud entre minutos y personas | Física |
| Combinación | C = RR estandarizado + w · nivel nocturno de la EDR estandarizado | Cada señal en lo que mide bien: el RR marca cuándo dentro de la noche y el nivel de la EDR cuánta apnea tiene la noche (§6). Le gana al RR solo de forma significativa y empata con G, F y una regresión logística (§8) | Datos |
| Peso w | 1 | Validación cruzada por personas, grilla de 0 a 3 cada 0,25 (§7) | Datos |
| μ1, σ1, μ2, σ2 | −1,492; 0,590; −2,197; 0,636 | Media y desvío en desarrollo. Son solo un cambio de unidades: no cambian el orden dentro de una noche | Datos |
| Umbral | C > 0,489 | Índice de Youden (Youden, 1950): no hay costos definidos para cada tipo de error y las clases tienen tamaños parecidos (40 % de apnea). Fluss et al. (2005) | Bibliografía + datos |
| Confianza | Movimiento relativo a la noche: cortes en los percentiles 50 y 90 de desarrollo (−0,001 y 0,702) | El acierto baja en el decil de más movimiento | Datos |
| Minutos evaluados | Con etiqueta y ≤ 20 % de RR corregidos | Igual que la limpieza del RR | Datos |
| AUC dentro de la noche | Registros con ≥ 20 minutos de cada tipo | Con menos minutos el AUC de un registro es muy inestable | Convención |

### Estadística

| Decisión | Valor | Justificación | Tipo |
|---|---|---|---|
| Unidad de remuestreo | La persona | Los minutos de una noche no son independientes, y una persona puede tener varias noches | Datos (`01`) |
| Intervalos de confianza | Bootstrap de personas, 2000–4000 repeticiones, percentiles 2,5 y 97,5 | Efron y Tibshirani (1993) | Bibliografía |
| Validación cruzada | 5 grupos de personas, semilla 2026 | Cada persona queda en un solo grupo; con 19 personas, 5 grupos dejan ~4 personas por grupo | Convención |
| AUC | Igual al estadístico U de Mann–Whitney normalizado | Hanley y McNeil (1982) | Bibliografía |
| Correlación por noche | Spearman | No supone una relación lineal y no la dominan unas pocas noches extremas | Bibliografía |

## 3. Por qué 2 Hz y spline cúbico

El RR y la EDR tienen un valor por latido, en instantes irregulares. El método de Welch necesita muestras equiespaciadas, así que hay que remuestrear la serie (Task Force, 1996). El valor de 2 Hz se eligió por tres razones:
- **Supera la frecuencia cardíaca.** En desarrollo, la frecuencia típica de cada noche va de 0,8 a 1,4 Hz. A 2 Hz no se pierde ningún latido.
- **El límite de Nyquist (1 Hz) cubre la respiración** (≤ 0,5 Hz), que se usa para validar la EDR, y queda muy por encima de la banda de la apnea (0,05 Hz).
- **Más alto no agrega información:** solo agrega muestras interpoladas.

El spline cúbico da una curva suave, con derivada continua. Interpolar en forma lineal da el mismo resultado en la banda de la apnea (`04` §15).

## 4. Bibliografía citada en los notebooks

- Bazett, H. C. (1920). An analysis of the time-relations of electrocardiograms. *Heart*, 7, 353–370.
- Efron, B. y Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman & Hall.
- Fluss, R., Faraggi, D. y Reiser, B. (2005). Estimation of the Youden index and its associated cutoff point. *Biometrical Journal*, 47(4), 458–472.
- Guilleminault, C., Connolly, S., Winkle, R., Melvin, K. y Tilkian, A. (1984). Cyclical variation of the heart rate in sleep apnoea syndrome. *The Lancet*, 323(8369), 126–131.
- Hampel, F. R. (1974). The influence curve and its role in robust estimation. *Journal of the American Statistical Association*, 69(346), 383–393.
- Hanley, J. A. y McNeil, B. J. (1982). The meaning and use of the area under a receiver operating characteristic (ROC) curve. *Radiology*, 143(1), 29–36.
- Kligfield, P. et al. (2007). Recommendations for the standardization and interpretation of the electrocardiogram: Part I. *Circulation*, 115(10), 1306–1324.
- Laguna, P., Moody, G. B. y Mark, R. G. (1998). Power spectral density of unevenly sampled data by least-square analysis. *IEEE Transactions on Biomedical Engineering*, 45(6), 698–715.
- Lomb, N. R. (1976). Least-squares frequency analysis of unequally spaced data. *Astrophysics and Space Science*, 39, 447–462.
- Moody, G. B., Mark, R. G., Zoccola, A. y Mantero, S. (1985). Derivation of respiratory signals from multi-lead ECGs. *Computers in Cardiology*, 12, 113–116.
- Pan, J. y Tompkins, W. J. (1985). A real-time QRS detection algorithm. *IEEE Transactions on Biomedical Engineering*, 32(3), 230–236.
- Penzel, T., Moody, G. B., Mark, R. G., Goldberger, A. L. y Peter, J. H. (2000). The Apnea-ECG Database. *Computers in Cardiology*, 27, 255–258.
- Sörnmo, L. y Laguna, P. (2005). *Bioelectrical Signal Processing in Cardiac and Neurological Applications*. Elsevier Academic Press.
- Spearman, C. (1904). The proof and measurement of association between two things. *American Journal of Psychology*, 15(1), 72–101.
- Task Force of the European Society of Cardiology and the North American Society of Pacing and Electrophysiology (1996). Heart rate variability: standards of measurement, physiological interpretation and clinical use. *Circulation*, 93(5), 1043–1065.
- Welch, P. D. (1967). The use of fast Fourier transform for the estimation of power spectra. *IEEE Transactions on Audio and Electroacoustics*, 15(2), 70–73.
- Wiener, N. (1949). *Extrapolation, Interpolation, and Smoothing of Stationary Time Series*. MIT Press.
- Youden, W. J. (1950). Index for rating diagnostic tests. *Cancer*, 3(1), 32–35.
- ANSI/AAMI EC57 (2012). Testing and reporting performance results of cardiac rhythm and ST segment measurement algorithms.

**Falta para el informe**: el estado del arte con trabajos recientes (la devolución dice que las referencias eran viejas). Esa bibliografía va en el informe, no en este documento.
