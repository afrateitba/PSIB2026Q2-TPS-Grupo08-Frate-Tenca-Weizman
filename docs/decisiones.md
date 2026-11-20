# Decisiones, umbrales y ventanas

Este documento lista cada número que fija el pipeline, con lo que lo justifica y dónde se muestra. Responde al pedido de la devolución: "fundamentar en bibliografía los umbrales elegidos" y "tener consistencia en las decisiones (no cambiar el tamaño de las ventanas)".

Cada fila dice qué la justifica. Las citas están verificadas en fuentes oficiales (DOI en Crossref, doi.org y PubMed; páginas de PhysioNet) en [`referencias.md`](referencias.md). Hay tres tipos de justificación:
- **Datos**: se midió en los registros de desarrollo. El notebook muestra la medición y, cuando hay alternativas, la comparación.
- **Bibliografía**: es el valor de un método publicado o de una recomendación.
- **Física**: sale de una propiedad de la señal, como una resolución o el límite de Nyquist.

Test no interviene en ninguna decisión.

## 1. Ventanas y duraciones

Hay **una sola ventana de análisis**: 240 s centrada en cada minuto. Se usa igual para explorar la banda (`01` §7), para elegir la variante de EDR (`03` §6, medida B) y para el detector (`04`). Las demás duraciones de la tabla no son ventanas de análisis alternativas. Son el largo de un objeto, como un latido o un QRS, o se usan solo para mirar las señales.

| Duración | Valor | Para qué | Por qué | Tipo | Dónde |
|---|---|---|---|---|---|
| Unidad de decisión | 1 min | El detector decide por minuto | Las etiquetas de la base son por minuto (Penzel et al., 2000) | Datos | `01` §3 |
| **Ventana de análisis** | **240 s, centrada en el minuto** | Estimar el espectro de RR y EDR de cada minuto | Con segmentos de 120 s la primera frecuencia de la banda (k = 2) es 0,017 Hz, un ciclo de 60 s, con dos ciclos completos en cada segmento; los ciclos de 60 a 100 s entran solo en parte (`08` §1). 3 segmentos de 120 s con 50 % de solapamiento ocupan 240 s. Con 180, 300 o 360 s la exactitud baja ~0,01; con Holm sobre las 13 variantes solo la caída con 360 s es significativa | Física + datos | `01` §7, `04` §1 y §15 |
| Segmento de Welch | 120 s, Hann, 50 % de solapamiento | Dentro de la ventana de 240 s | La resolución es 1/120 ≈ 0,008 Hz, y la banda son las frecuencias k = 2…6 (0,017–0,05 Hz), con bordes que caen a la mitad de la potencia en ~80 s y ~18 s de período (`08` §1). Promediar 3 segmentos baja la varianza (Welch, 1967) | Física + bibliografía | `04` §1 |
| Tendencia en cada segmento | Se quita una recta | Que una deriva lenta no se filtre a la banda | Práctica habitual en variabilidad cardíaca (Tarvainen et al., 2002). Con la ventana de Hann la deriva queda casi toda en k ≤ 1: no quitarla da la misma exactitud (+0,002, IC con el cero). Se mantiene como protección | Bibliografía + datos | `04` §15 |
| Alineación de la ventana | Centrada en el minuto | Contexto de los dos lados | El análisis es fuera de línea. Una ventana que termina al final del minuto (solo pasado) baja la exactitud (−0,005, significativo solo sin corregir) y el AUC dentro de la noche (0,894 contra 0,908) | Datos | `04` §15 |
| Término de la noche | Toda la noche (mediana) | Nivel nocturno de la EDR en C | El nivel de la EDR sigue a la cantidad de apnea de la noche, no al minuto. Con la media en lugar de la mediana da lo mismo (−0,001); la mediana es robusta a minutos con movimiento | Datos | `04` §6 y §15 |
| Realización de un latido | −250 a +400 ms del pico R | Estimar los espectros de señal y de ruido para el filtro de Wiener | Es el largo de un latido: cubre la onda P (el intervalo PR dura 120–200 ms), el QRS y casi toda la T. Promediado coherente (Sörnmo y Laguna, 2005) | Física + bibliografía | `03` §5 |
| Área del QRS | ±60 ms del pico R | Valor de la EDR en cada latido | El QRS dura ~80–100 ms. Las medidas de amplitud y área del QRS son métodos establecidos de EDR con una derivación (Charlton et al., 2018; Varon et al., 2020) | Física + bibliografía | `03` §2 |
| Deriva de la línea de base | −100 a −50 ms (segmento PR) | Medida alternativa de EDR, descartada | Es el tramo isoeléctrico antes del QRS | Física | `03` §2 y §6 |
| Integración de Pan-Tompkins | 150 ms | Juntar la energía de cada QRS | Valor del método (Pan y Tompkins, 1985) | Bibliografía | `02` §2 |
| Período refractario | 200 ms | No detectar dos QRS seguidos | Pan y Tompkins (1985) | Bibliografía | `02` §2 |
| Ventana de onda T | máx(360 ms; 0,5 RR medio) | Posible onda T después de un QRS | 360 ms es el valor de Pan y Tompkins (1985). Se alarga con el ritmo porque el QT ocupa ~40 % del ciclo (Bazett, 1920). Corrige `x17` | Bibliografía + datos | `02` §2 |
| Forma del QRS | ±100 ms, últimos 8 QRS, desde 3 QRS previos | Comparar un candidato con los QRS anteriores | Cubre el QRS completo; 8 latidos son ~7 s, así que la forma de referencia sigue cambios lentos. Con ±60 o ±140 ms, o con 2 o 5 QRS previos, cambia como mucho el 0,4 % de los latidos del peor registro | Física + datos | `02` §2 |
| Energía > 20 Hz | ±50 ms, pasaaltos de orden 2 | Distinguir QRS de onda T | El QRS tiene energía por encima de 20 Hz y la onda T casi no. Con ±30 u ±80 ms, o con orden 1 o 4, cambia como mucho el 0,2 % de los latidos | Física + datos | `02` §2 |
| Mediana de vecinos | 11 latidos (~10 s) | Limpieza del RR y filtro de Hampel de la EDR | Abarca 2–3 respiraciones: sigue la respiración y aparta solo latidos sueltos. Con 5 vecinos el AUC baja 0,001; con 21 vecinos o con el intervalo anterior se corrige un 50 % más de RR sin mejorar | Física + datos | `02` §4, `03` §6 |
| Envolvente de la respiración | Valor eficaz en 10 s | Referencia de la apnea para validar la EDR (no la usa el detector) | Son 2–3 respiraciones; sigue la amplitud y no cada respiración. Con 5 o 20 s el orden de las variantes de EDR es el mismo (ρ 1,00 y 0,95) | Física + datos | `03` §4 y §6 |
| Coherencia EDR–respiración (A1) | Segmentos de 32 s en ventanas de 120 s | Validar la EDR en la banda respiratoria (no la usa el detector) | Resolución de ~0,03 Hz para la banda de 0,1–0,5 Hz con seis segmentos por ventana; la coherencia con pocos segmentos tiene sesgo y varianza (Carter, 1987). Con 16 o 64 s el orden de las variantes es el mismo (ρ 1,00 y 0,95). La figura de toda la noche de `03` §3 usa el mismo segmento | Física + bibliografía + datos | `03` §3 y §6 |
| Exploración: PSD del ECG | Welch, 4096 muestras (~41 s) | Ver el espectro del ECG de cada registro | Resolución de 0,024 Hz, suficiente para el latido y sus armónicos. Solo descriptivo | Física | `01` §5 |
| Exploración: espectrograma | 30 s | Ver cómo cambia el espectro del ECG en la noche | Compromiso entre resolución en tiempo y en frecuencia (0,033 Hz). Solo descriptivo | Física | `01` §5 |
| Movimiento | La misma ventana de 240 s | Medida de confianza | Mismo soporte que la decisión | Consistencia | `04` §12 |

## 2. Parámetros de cada etapa

### Base y partición (`01`)

| Decisión | Valor | Justificación | Tipo |
|---|---|---|---|
| Registros excluidos | c05, x22, x33 | Son la misma grabación que c06, x35 y x34: tienen muestras idénticas con un desfase (correlación de la señal 1,000). c05/c06 lo documenta PhysioNet; los otros dos pares se encontraron comparando las señales. El criterio r ≥ 0,99 queda en un hueco: los 10 pares no duplicados más parecidos no pasan de 0,29 | Datos |
| Sujetos | 29 personas en 67 registros | Se infieren del perfil (edad, sexo, altura, peso): 52 pares con perfil idéntico contra ≤ 3 por azar. Se verifican con la forma del latido: 44 % de pares casi idénticos dentro de una misma persona contra 2 % entre personas distintas | Datos |
| Partición | Por persona, 70/30, estratificada por categoría, diferencia de apnea ≤ 2 puntos, semilla 2026 | Separar por persona evita que el detector "reconozca" a alguien de desarrollo. Con muestras chicas conviene asignar más al entrenamiento, y 2/3 resultó cercano al óptimo en estudios de simulación (Dobbin y Simon, 2011). Cualquier tolerancia de apnea entre 0,5 y 5 puntos deja cientos de particiones (262 a 1993); con 2 puntos quedan 853 y la diferencia final es de 0,5 puntos | Bibliografía + datos |
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
| Detalles internos | Búsqueda del pico R ±80 ms; prominencia en 2 s | Medio QRS más margen; 2 s incluyen al menos un latido a cualquier ritmo posible. Con ±50 u ±120 ms, o con 1 o 3 s, cambia como mucho el 0,5 % de los latidos del peor registro | Física + datos |
| Búsqueda hacia atrás | Hueco de 1,66 RR medios | Pan y Tompkins (1985) | Bibliografía |
| Pulso aislado | Prominencia ≥ 0,5 de la altura | Corrige los tramos sin ECG; la ablación muestra que hace falta | Datos |
| Piso de energía | 5 % de la mediana de los QRS | Corrige el ruido de `x28` (ablación) | Datos |
| Forma | Correlación ≥ 0,5 | Separa ondas T de QRS en la ventana de onda T | Datos |
| Energía rápida | ≥ 30 % de la energía > 20 Hz del QRS anterior | Corrige las ondas T altas de `x17` (ablación) | Datos |
| Sensibilidad de esos umbrales | Mover cada uno entre 40 % y 100 % de su valor | Cambia < 0,5 % de los latidos en el peor registro: el valor exacto no importa | Datos |
| Tolerancia de comparación | 100 ms | Cuando dos fuentes coinciden lo hacen a < 30 ms; entre 30 y 150 ms la sensibilidad y el VPP cambian < 1 punto. `bxb`, la implementación de referencia de PhysioNet para las normas ANSI/AAMI EC38 y EC57, usa por defecto 150 ms | Datos + bibliografía |
| Refinamiento del pico R | Parábola de 3 puntos | A 100 Hz el pico cae en una grilla de 10 ms (±5 ms de error). La prueba de dos fases a 50 Hz baja el desacuerdo de ~10 a 2,5 ms | Datos |
| RR posibles | 0,3–2 s | 200 a 30 latidos por minuto. En desarrollo solo el 0,07 % de los RR cae fuera, y el 99,8 % está entre 0,5 y 1,6 s; lo que cae fuera son pausas sin ECG (hasta ~9 s) y detecciones dobles | Fisiología + datos |
| RR atípico | > 20 % de la mediana de 11 vecinos | Criterio estándar de la variabilidad cardíaca (Clifford et al., 2002, que lo atribuye a los textos estándar). En estos datos separa el cuerpo de la distribución (97 % dentro de ±10 %) de las colas de errores (+100 %, −50 %, −80 %), no corrige más en los minutos con apnea (0,27 % contra 0,23 %), y entre 10 % y 40 % la detección no cambia (AUC 0,905–0,908); más estricta solo corrige y excluye el triple, más laxa empeora apenas | Bibliografía + datos |
| Reemplazo | Interpolación lineal | Welch necesita una serie continua. Interpolar puede sesgar el espectro si se corrigen muchos latidos (Lippman et al., 1994; Peltola, 2012); acá se corrige el 0,5 %, y lineal, cúbica y borrar el latido dan el mismo AUC (dentro de 0,001) | Bibliografía + datos |
| Minuto excluido | > 20 % de RR corregidos | Ahí la serie es más interpolación que dato. Con 10 %, 30 %, 50 % o sin excluir, el AUC va de 0,907 a 0,909: el límite cuesta el 0,2 % de los minutos y no cambia la detección | Datos |

### EDR y filtro de Wiener (`03`)

| Parámetro | Valor | Justificación | Tipo |
|---|---|---|---|
| Medida | Área del QRS (±60 ms) | Método establecido de EDR (Charlton et al., 2018; Varon et al., 2020 comparan diez métodos). Sigue mejor la respiración que la amplitud R y la deriva, y detecta mejor que la deriva | Bibliografía + datos |
| Filtro de Wiener | H = S_s / (S_s + S_n), con S_s y S_n estimados de las realizaciones | Filtro lineal de mínimo error cuadrático (Wiener, 1949). Promediado coherente (Sörnmo y Laguna, 2005) | Bibliografía |
| Implementación del Wiener | FIR simétrico de 129 coeficientes (`firwin2`, Virtanen et al., 2020); forma del latido = media de las realizaciones | H(f) se estima con realizaciones de 0,65 s (resolución real ~1,5 Hz); 129 coeficientes siguen ~0,8 Hz. Desde 65 coeficientes ni A1 ni B cambian más de 0,004, y la mediana da lo mismo que la media (0,001) | Física + bibliografía + datos |
| Latidos excluidos | Ectópicos (los que corrige la limpieza del RR) y atípicos de Hampel (3 desvíos robustos, 11 vecinos, con piso de ruido) | Hampel (1974). Con una distribución normal, 3 desvíos dejan afuera ~0,3 %. El piso evita marcar las crestas de la respiración | Bibliografía + datos |
| Variante elegida | Wiener + exclusiones juntas | La combinación mejora en promedio las tres medidas; en el AUC dentro de la noche +0,036 [+0,005; +0,087], significativo sin corregir (p = 0,006) pero no con Holm sobre las 12 comparaciones (0,066). No empeora nada | Datos |
| EDR relativa | Área / mediana del área sin signo del registro | El tamaño del QRS cambia entre personas (electrodos, anatomía). Sin dividir, el nivel de la EDR sigue al tamaño del QRS (ρ 0,70); dividiendo, no (ρ −0,02) | Datos |
| Interpolación | Spline cúbico a 2 Hz | Ver la sección 3 | Física + datos |

### Feature y detector (`04`)

| Parámetro | Valor | Justificación | Tipo |
|---|---|---|---|
| Banda | 0,017–0,05 Hz (k = 2…6; se escribía 0,01–0,05 Hz) | Donde más sube la potencia del RR durante la apnea, dentro de cada registro (máximo en 0,025 Hz; −3 dB entre 0,017 y 0,05 Hz). Con segmentos de 120 s se suman las cinco frecuencias k = 2…6; el borde de 0,01 Hz era nominal. Corresponde a ciclos de 20 a 60 s; la apnea puede tener ciclos de hasta 100 s (Guilleminault et al., 1984), que la banda capta solo en parte, pero con el doble de resolución el aumento con la apnea se concentra entre 20 y 60 s (`08` §1). En la EDR la banda a −3 dB es 0,017–0,033 Hz, dentro de la elegida; limitar la EDR a esa banda no mejora (−0,011, significativo solo sin corregir) | Datos + bibliografía |
| Potencia | log10 del promedio en la banda | La potencia varía en órdenes de magnitud entre minutos y personas. En escala lineal C es la peor variante: exactitud −0,052 y ρ por noche 0,66, porque unas pocas noches dominan la estandarización | Física + datos |
| Combinación | C = RR estandarizado + w · nivel nocturno de la EDR estandarizado | Cada señal en lo que mide bien: el RR marca cuándo dentro de la noche y el nivel de la EDR cuánta apnea tiene la noche (§6). Frente al RR solo marca ~30 puntos menos en los controles (resiste Holm); su mayor exactitud (+0,096) es significativa solo sin corregir. No se distingue de G, F ni de una regresión logística (§8) | Datos |
| Peso w | 1 | Validación cruzada por personas, grilla de 0 a 3 cada 0,25 (§7) | Datos |
| μ1, σ1, μ2, σ2 | −1,492; 0,590; −2,197; 0,636 | Media y desvío en desarrollo. Son solo un cambio de unidades: no cambian el orden dentro de una noche | Datos |
| Umbral | C > 0,489 | Índice de Youden (Youden, 1950). El umbral óptimo depende de la prevalencia y de los costos de cada error (Metz, 1978; Zweig y Campbell, 1993; Habibzadeh et al., 2016), que acá no están definidos. Youden maximiza la exactitud balanceada: pesa igual la sensibilidad y la especificidad y no depende de la prevalencia. Es el criterio recomendado frente al punto más cercano a (0, 1) (Perkins y Schisterman, 2006; Ünal, 2017). Su estimación empírica tiene sesgo (Fluss et al., 2005), y por eso el desempeño se mide con validación cruzada. Con personas no vistas, los criterios alternativos dan la misma exactitud balanceada (`04` §9) | Bibliografía + datos |
| Confianza | Movimiento relativo a la noche: cortes en los percentiles 50 y 90 de desarrollo (−0,001 y 0,702) | En desarrollo el acierto baja en el decil de más movimiento; en test la confianza casi no separa (0,79 / 0,77 / 0,76). Limitación | Datos |
| Minutos evaluados | Con etiqueta y ≤ 20 % de RR corregidos, toda la noche | Igual que la limpieza del RR. Sin la primera hora (vigilia) la exactitud no cambia (−0,004); se evalúa toda la noche porque así está etiquetada la base | Datos |
| AUC dentro de la noche | Registros con ≥ 20 minutos de cada tipo; se resume con la media | Con 20 minutos de cada tipo el error estándar del AUC de una noche es ~0,05 (fórmula de Hanley y McNeil, 1982); con 10, ~0,07 y solo 3 noches más; con 30 o 40 el AUC medio no cambia. La media es la medida fijada para P1 y se usa en todo el trabajo | Bibliografía + datos |

### Estadística

| Decisión | Valor | Justificación | Tipo |
|---|---|---|---|
| Unidad de remuestreo | La persona | Los minutos de una noche no son independientes, y una persona puede tener varias noches | Datos (`01`) |
| Intervalos de confianza | Bootstrap de personas, 2000–4000 repeticiones, percentiles 2,5 y 97,5 | Efron y Tibshirani (1993). Con 2000 remuestreos los extremos cambian menos de 0,002 entre semillas y con 4000 menos de 0,001, frente a intervalos de ~0,07 | Bibliografía + datos |
| Validación cruzada | 5 grupos de personas, semilla 2026 | Cada persona queda en un solo grupo. Compromiso habitual entre sesgo y varianza (Arlot y Celisse, 2010); con 10 grupos o una persona por grupo la exactitud estimada es la misma (−0,001 y +0,006) | Bibliografía + datos |
| Predicciones de la hipótesis | IC 95 % sin corregir | H se sostiene solo si se cumplen las tres: en esa prueba de unión-intersección el error total no supera el de cada parte (Berger, 1982) | Bibliografía |
| Comparaciones entre features | Holm sobre todas las diferencias | Muchas comparaciones a la vez; Holm controla el error de toda la familia y es más potente que Bonferroni (Aickin y Gensler, 1996). Se aplica en cada familia de comparaciones (02, 03, 04, 06; `src/estadistica.py`). En la comparación de features de desarrollo resisten 4 de 21; en test, 3 de 13 (las tres: C da menos falsas alarmas). La mejora de la variante de EDR (0,066) y varias diferencias de robustez no resisten | Bibliografía + datos |
| AUC | Igual al estadístico U de Mann–Whitney normalizado | Hanley y McNeil (1982) | Bibliografía |
| Correlación por noche | Spearman | No supone una relación lineal y no la dominan unas pocas noches extremas | Bibliografía |

## 3. Por qué 2 Hz y spline cúbico

El RR y la EDR tienen un valor por latido, en instantes irregulares. El método de Welch necesita muestras equiespaciadas, así que hay que remuestrear la serie (Task Force, 1996). El valor de 2 Hz se eligió por tres razones:
- **Supera la frecuencia cardíaca.** En desarrollo, la frecuencia típica de cada noche va de 0,8 a 1,4 Hz. A 2 Hz no se pierde ningún latido.
- **El límite de Nyquist (1 Hz) cubre la respiración** (≤ 0,5 Hz), que se usa para validar la EDR, y queda muy por encima de la banda de la apnea (0,05 Hz).
- **Más alto no agrega información:** solo agrega muestras interpoladas.

El spline cúbico da una curva suave, con derivada continua. Interpolar en forma lineal da el mismo resultado (exactitud −0,005, IC con el cero; `04` §15).

## 5. Simplificación con el criterio de sencillez (`07`)

Las ocho etapas que se habían agregado sin demostrar que hacen falta se probaron contra su alternativa simple, con el criterio escrito antes de correr el análisis ([`criterio_parsimonia.md`](criterio_parsimonia.md)). Una etapa queda si mejora de forma demostrable la medición de su paso o el detector, con la corrección de Holm y un bootstrap que repite el ajuste en cada sorteo. Todo se hace en desarrollo; test no interviene.

| Etapa | Versión evaluada en test | Detector simplificado | Por qué |
|---|---|---|---|
| Refinamiento del pico R | Parábola de 3 puntos | Igual | El desacuerdo entre las dos fases baja de 10,0 a 2,3 ms, en los 47 registros |
| Wiener en la EDR | FIR de 129 coeficientes | Sin Wiener | No mejora ninguna medida; el área del QRS ya promedia el ruido rápido; ningún trabajo publicado de apnea o EDR con ECG lo usa (`07` §9) |
| Excluir ectópicos de la EDR | Sí | No | No mejora la EDR ni el detector |
| Hampel en la EDR | Sí | No | Su efecto viene de una sola persona; repitiendo el ajuste, p = 0,61 |
| Interpolación a 2 Hz | Spline cúbico | Lineal | No cambia el detector |
| Tendencia en cada segmento de Welch | Se quita una recta | Se quita la media | Con la ventana de Hann la media no llega a la banda; la recta no cambia el detector |
| Minutos con > 20 % de RR corregidos | No se clasifican | Se clasifican | Son el 0,6 % de los minutos: muy pocos para demostrar que el detector falla en ellos |
| Confianza según el movimiento | Alta, media o baja | No se informa | No es demostrable que la exactitud cambie con el movimiento (p = 0,056) |

Exactitud en validación cruzada: 0,836 la versión evaluada en test y 0,821 la simplificada. La diferencia no es demostrable; la simplificada marca más minutos en los controles (12 % contra 7 %), casi todo por las dos noches de una misma persona que sin Hampel tienen un nivel de EDR inflado.

## 4. Bibliografía

La lista completa, con el DOI o la página oficial de cada fuente, la verificación en Crossref, doi.org y PubMed, y el tipo de acceso (texto libre o suscripción), está en [`referencias.md`](referencias.md). Se regenera con `python scripts/verificar_referencias.py`.

**Falta para el informe**: el estado del arte con trabajos recientes (la devolución dice que las referencias eran viejas). Esa bibliografía va en el informe, no en este documento.
