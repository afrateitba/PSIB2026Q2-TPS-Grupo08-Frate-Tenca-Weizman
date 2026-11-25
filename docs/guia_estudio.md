# Guía de estudio · Detección de apnea del sueño con un ECG de una derivación

**Grupo 8 · Procesamiento de Señales e Imágenes Biomédicas · Recuperatorio 2026 Q2**

**Para qué sirve.** La devolución de la primera entrega pidió que los tres puedan explicar cada técnica, a nivel de una señal y a nivel de toda la base, y que la defensa respete el tiempo. Esta guía está armada para eso:
- sigue el orden de la presentación;
- explica cada técnica con lo mismo: qué es, cómo se calcula, qué parámetros usamos y por qué, qué se ve en una señal y qué se ve en la base;
- junta los números que hay que saber;
- trae las preguntas probables de la defensa con una respuesta corta.

**Fuentes.** El informe del recuperatorio, la presentación (45 diapositivas, con sus notas) y el repositorio en el commit `7793ce4`. Los números son los del informe y del repositorio. Si la presentación dice otra cosa, está marcado en la sección 9 para corregirlo antes de presentar.

---

## Índice

1. [El trabajo en una página](#1-el-trabajo-en-una-página)
2. [La presentación: recorrido, tiempos y reparto](#2-la-presentación-recorrido-tiempos-y-reparto)
3. [Fisiología: por qué el ECG sirve](#3-fisiología-por-qué-el-ecg-sirve)
4. [La base y la partición](#4-la-base-y-la-partición)
5. [Las técnicas, una por una](#5-las-técnicas-una-por-una)
6. [Los resultados que hay que saber](#6-los-resultados-que-hay-que-saber)
7. [Cómo explicar los resultados](#7-cómo-explicar-los-resultados)
8. [Preguntas probables de la defensa](#8-preguntas-probables-de-la-defensa)
9. [Correcciones antes de presentar](#9-correcciones-antes-de-presentar)
10. [Glosario español–inglés](#10-glosario-españolinglés)

---

## 1. El trabajo en una página

**Pregunta.** ¿Qué minutos de una noche se pueden identificar como compatibles con apnea a partir de un solo canal de ECG?

**Idea.** El ECG trae dos señales de la respiración:
- el **RR**, el tiempo entre latidos: en la apnea la frecuencia cardíaca baja durante la pausa y sube al volver a respirar;
- la **EDR** (respiración derivada del ECG): al respirar cambia el tamaño del QRS, y medirlo latido a latido da una estimación de la respiración.

**Hipótesis H.** El ciclo de pausa y recuperación de la apnea (20 a 100 s) aumenta la potencia del RR y de la EDR en la banda lenta, 0,017–0,05 Hz (ciclos de 20 a 60 s). De H salen tres predicciones, y H se sostiene solo si se cumplen las tres:

| Predicción | Qué dice | Cómo se mide | Se cumple si |
|---|---|---|---|
| **P1** | Dentro de cada noche, el RR tiene más potencia lenta en los minutos con apnea | AUC dentro de la noche de P_RR, media de las noches con al menos 20 minutos de cada tipo | > 0,5 y el IC 95 % no incluye 0,5 |
| **P2** | Entre noches, el nivel de la EDR sube con la cantidad de apnea | Spearman entre la mediana nocturna de P_EDR y el % de minutos con apnea | > 0 y el IC 95 % no incluye 0 |
| **P3** | La feature C con un solo umbral detecta apnea en personas nuevas | AUC de C con todos los minutos de test | > 0,5 y el IC 95 % no incluye 0,5 |

**El detector final**, en una línea: ECG → filtro → latidos → RR y EDR → potencia en la banda lenta (Welch, 240 s) → C → umbral.

**C(m) = [P_RR(m) − μ₁] / σ₁ + w · [P̃_EDR − μ₂] / σ₂**
- P_RR(m): log₁₀ de la potencia del RR en la banda, en la ventana del minuto m.
- P̃_EDR: mediana de P_EDR en todas las ventanas de la noche. Es una sola cifra por noche y no usa etiquetas.
- μ₁ = −1,491573, σ₁ = 0,590230, μ₂ = −1,991986, σ₂ = 0,599205, w = 1.
- Un minuto es apnea si **C > 0,481350** (umbral de Youden de desarrollo).

**Resultados.**

| | Desarrollo (validación cruzada) | Prueba 1 (`05`, con Wiener) | Prueba 2 (`11`, detector final, sin Wiener) |
|---|---|---|---|
| P1 | 0,908 | 0,869 (0,827–0,930) ✓ | 0,869 (0,827–0,930) ✓ |
| P2 | 0,787 | 0,658 (0,117–0,786) ✓ | **0,531 (−0,152–0,732) ✗** |
| P3 | 0,888 | 0,849 (0,688–0,938) ✓ | 0,827 (0,627–0,937) ✓ |
| Exactitud | 0,830 | 0,780 | 0,775 |
| % marcado en controles | 9,5 % | 11,2 % | 6,1 % |

La columna de desarrollo es la del detector final. La versión evaluada en la prueba 1 tenía, en desarrollo, exactitud 0,836 y P2 0,83.

**Conclusión en una frase.** El RR ubica la apnea dentro de la noche y C la detecta en personas nuevas, con muchas menos falsas alarmas que el RR solo. Pero con el detector final no se demostró que el nivel de la EDR acompañe a la cantidad de apnea de cada noche, así que la hipótesis se sostiene solo en parte.

---

## 2. La presentación: recorrido, tiempos y reparto

Los tiempos son los de las notas de cada diapositiva. En total suman unos **16,5 minutos**. La devolución marcó que no se cumplió el tiempo: hay que ensayar con cronómetro.

| # | Diapositiva | Tiempo | Mensaje en una frase | Número clave | Guía |
|---|---|---|---|---|---|
| 1 | Portada | 30 s | Una hipótesis, tres predicciones, un umbral | — | §1 |
| 2–3 | Agenda y separador | 18 s | — | — | §9 (la agenda tiene 4 partes y las notas dicen 5) |
| 4 | La apnea del sueño | 45 s | La pausa baja la frecuencia cardíaca y la recuperación la sube, en ciclos de 20 a 100 s | AHI: < 5 normal, ≥ 30 grave | §3 |
| 5 | El ECG como punto de partida | 50 s | El ECG trae dos señales de la respiración: RR y EDR | — | §3 |
| 6 | Estado del arte y aporte | 60 s | Una combinación explícita de dos medidas y un umbral, para ver qué aporta cada una | Varon et al., 2020: 10 métodos de EDR | §8, pregunta 1 |
| 7 | Objetivos e hipótesis | 60 s | H se sostiene solo si se cumplen P1, P2 y P3 | banda 0,017–0,05 Hz | §1, §5.15 |
| 8 | Preparación de datos | 60 s | Partición por persona, 70/30, con las mismas proporciones de A, B y C | 47 / 20 registros; 19 / 10 personas | §4 |
| 9–10 | El detector, de punta a punta | 48 s | El detector recibe solo el ECG; las etiquetas se usan solo en desarrollo | C > 0,481 | §1 |
| 11 | Señales y filtro | 50 s | Un mismo filtro para todos, porque el latido está entre 1 y 40 Hz en todos | ≤ 1 dB en 0,77–41,8 Hz; ≥ 20 dB a 0,1 Hz | §5.1 |
| 12 | Latidos y serie RR | 60 s | Cada mejora del detector corrige una falla vista | RR corregidos: 0,57 % → 0,36 % (mediana) | §5.2–5.4 |
| 13 | La EDR | 50 s | Área del QRS relativa; el Wiener salió por sencillez | ρ con el tamaño del QRS: 0,70 → ≈ 0 | §5.5, §5.7 |
| 14 | La banda de la apnea | 45 s | La banda se midió en los datos | 31 de 31 registros | §5.8 |
| 15 | De F a C | 50 s | El RR dice cuándo; la EDR dice cuánta apnea tiene la noche | F ≈ promedio de las dos potencias (r = 0,985) | §5.6, §5.9 |
| 16 | Selección del umbral | 45 s | Sin costos definidos, Youden | 0,481 | §5.10 |
| 17 | Resumen del desarrollo | 50 s | C acierta más y marca menos en los controles | 0,836 (versión evaluada) | §6.1 |
| 18–19 | Revisión: qué etapas se quedan | 78 s | Dos reglas escritas antes: sencillez y robustez | 8 de 88 decisiones revisadas | §5.16 |
| 20 | Prueba del detector final | 70 s | P1 y P3 sí, P2 no | P2 = 0,531 (−0,152 a 0,732) | §6.3 |
| 21 | Dónde falla y por qué falla P2 | 60 s | Errores por noche entera; sin Wiener, el ruido sube el nivel de la EDR de dos noches | sin esa persona, ρ = 0,67 | §6.5 |
| 22–23 | Conclusiones | 53 s | La hipótesis se sostiene en parte | 6 % contra 34 % en controles | §7 |
| 24 | Gracias | — | — | — | — |
| 25–45 | Referencias y respaldo | — | Para responder preguntas | — | §8 |

**Reparto en tres partes parecidas.** La devolución pidió que participen los tres por igual, y Leah puede presentar en inglés (el glosario de la sección 10 sirve para eso). Una división posible, cortando en los cambios de tema:

| Parte | Diapositivas | Tema | Tiempo |
|---|---|---|---|
| A | 1–8 | Contexto, base y partición | ~5 min 20 s |
| B | 9–15 | El detector: filtro, latidos, EDR, banda y C | ~5 min |
| C | 16–24 | Umbral, revisión, prueba y conclusiones | ~6 min |

Las diapositivas de respaldo (25–45) las puede usar cualquiera al responder. Cada uno tiene que poder explicar todas las técnicas, no solo las de su parte.

---

## 3. Fisiología: por qué el ECG sirve

**Apnea obstructiva.** Durante el sueño la vía aérea superior se cierra aunque la persona siga haciendo esfuerzo para respirar. La respiración se corta 10 s o más. Al final hay un microdespertar y la respiración vuelve. Se repite toda la noche, en ciclos de 20 a 100 s.

**Qué le pasa al corazón (Guilleminault et al., 1984).** Durante la pausa la frecuencia cardíaca baja (el RR se alarga), y al volver a respirar sube (el RR se acorta). Esa "variación cíclica de la frecuencia cardíaca" es lo que mide el RR en la banda lenta.

**Por qué el QRS cambia con la respiración (Charlton et al., 2018; Varon et al., 2020).** Al respirar cambian la impedancia del tórax y la orientación del corazón respecto de los electrodos. Una derivación ve la actividad eléctrica en una dirección, así que el tamaño y la forma del QRS cambian con cada respiración. Medir ese cambio latido a latido da la EDR. En la apnea, la amplitud de la respiración también sube y baja con el ciclo de pausa y recuperación, y eso aparece en la EDR como potencia lenta.

**Diferencia con la arritmia sinusal respiratoria.** En cada respiración normal la frecuencia cardíaca sube al inspirar y baja al espirar. Eso pasa a unos 0,25 Hz (una respiración cada 4 s). La apnea agrega una oscilación mucho más lenta, de 0,01 a 0,05 Hz. Por eso el trabajo mira la banda lenta y no la respiratoria.

**Cómo se diagnostica hoy.** Con polisomnografía: flujo de aire, esfuerzo respiratorio, saturación de oxígeno y EEG, toda la noche en un laboratorio (Kapur et al., 2017). Es cara y poco accesible. La gravedad se mide con el **AHI** (apneas más hipopneas por hora), con los cortes clínicos habituales: normal < 5, leve 5–14, moderada 15–29, grave ≥ 30.

**Qué no hace nuestro detector.** Cuenta minutos con apnea, no eventos por hora. No reemplaza el diagnóstico: la idea es mostrar el fenómeno de forma interpretable.

---

## 4. La base y la partición

**Apnea-ECG (PhysioNet; Penzel et al., 2000).**
- 70 registros nocturnos de 7 a 10 horas, una derivación de ECG a 100 Hz y 12 bits.
- Un experto puso una etiqueta a cada minuto a partir de la polisomnografía: apnea (o hipopnea) o normal.
- 8 registros tienen además respiración medida (tórax, abdomen y flujo). Se usaron para validar la EDR, y por diseño están todos en desarrollo.

**Categorías A, B y C.** Describen la noche, no a la persona.
- A: 100 minutos de apnea o más. B: de 5 a 99. C (control): menos de 5.
- PhysioNet además pide al menos una hora con un índice de apnea ≥ 10 (A) o ≥ 5 (B). Con etiquetas por minuto esa condición no se puede verificar, así que la regla usa solo los minutos.

**Duplicados.** Tres registros son la misma grabación con otro nombre: c05 = c06, x22 = x35 y x33 = x34 (correlación de la señal 1,000). Los 10 pares no duplicados más parecidos llegan a 0,29, así que el corte r ≥ 0,99 cae en un hueco amplio. Quedan 67 registros. En las grabaciones duplicadas las etiquetas difieren en 1 o 2 minutos: es el ruido de la referencia.

**Personas.** La base no dice qué noches son de la misma persona. Se agruparon por perfil idéntico (edad, sexo, altura y peso) y se verificó con la forma del latido: tiene |r| > 0,95 en el 44 % de los pares de la misma persona y en el 2 % de los pares de personas distintas. Quedan **29 personas**.

**Por qué partir por persona.** Dos noches de una misma persona difieren en promedio 7 puntos en el % de apnea, y dos de personas distintas, 37. Si una persona estuviera en desarrollo y en test, el resultado sería optimista.

**La partición** (`data/split.csv`, semilla 2026):

| | Personas | Registros | A | B | C | Minutos con apnea |
|---|---|---|---|---|---|---|
| Desarrollo | 19 | 47 | 28 | 7 | 12 | 39,8 % |
| Test | 10 | 20 | 12 | 3 | 5 | 39,3 % |

70/30 por persona, con las mismas proporciones de A, B y C y la misma fracción de apnea (±2 puntos).

**Regla de trabajo.** Todo se desarrolla con los 47 registros de desarrollo. Test se corre una sola vez, con el notebook y el plan registrados en el repositorio antes de correrlo.

---

## 5. Las técnicas, una por una

Cada técnica tiene cinco partes: **qué es**, **en nuestro trabajo**, **en una señal** (un registro), **en la base** (todos los registros) y **en 30 segundos** (cómo decirlo en la defensa).

### 5.1 Filtro pasabanda Butterworth

**Qué es.** Un filtro deja pasar una banda de frecuencias y atenúa el resto. El Butterworth tiene la banda de paso lo más plana posible, sin ondulación, y cae de forma monótona. El orden fija qué tan rápido cae fuera de la banda.

**Filtrado de ida y vuelta (fase cero).** Se filtra hacia adelante y después hacia atrás (`filtfilt`). La fase de las dos pasadas se cancela, así que la señal no se desplaza en el tiempo y **el pico R queda donde estaba**. La magnitud se aplica dos veces: la atenuación en dB se duplica, y el filtro equivale a uno del doble de orden en magnitud. La especificación se verificó con la respuesta de ida y vuelta.

**En nuestro trabajo.** Butterworth de 0,5 a 45 Hz, orden 3, ida y vuelta. La especificación salió de los datos:
- **≤ 1 dB de pérdida entre 0,77 y 41,8 Hz.** 0,77 Hz es el percentil 1 de la frecuencia cardíaca instantánea (unos 46 latidos por minuto). 41,8 Hz es el percentil 95, entre registros, de la frecuencia por debajo de la cual está el 99 % de la energía del latido.
- **≥ 20 dB de atenuación a 0,1 Hz,** para sacar la deriva de la línea de base.
- **El corte inferior de 0,5 Hz** es compatible con las recomendaciones para filtrar el ECG con fase cero (Kligfield et al., 2007).

**En una señal.** En b03 la deriva de la línea de base desaparece, y en x08 se atenúa la interferencia de 50 Hz. El QRS no cambia de forma ni de lugar.

**En la base.** Se recorrieron los 47 registros de desarrollo:
- 20 tienen más del 10 % de su potencia por debajo de 0,5 Hz (deriva);
- 23 tienen un pico en 50 Hz diez veces mayor que su fondo espectral;
- 7 tienen más del 1 % de señal perdida.

Los problemas cambian de tamaño entre registros, pero no de lugar en el espectro: el latido está entre ~1 y 40 Hz en todos. Por eso se usa un mismo filtro para todos.

**En 30 segundos.** "Medimos en qué frecuencias está el latido en los 47 registros y en cuáles están los problemas. El latido está entre 1 y 40 Hz en todos, así que un mismo pasabanda sirve para todos. Un Butterworth de orden 3, de 0,5 a 45 Hz, cumple la especificación: pierde menos de 1 dB donde está el latido y atenúa 20 dB la deriva. Lo aplicamos ida y vuelta para que el pico R no se mueva."

### 5.2 Detección de latidos: Pan-Tompkins

**Qué es (Pan y Tompkins, 1985).** Un detector de QRS en cuatro etapas lineales y una regla de decisión:
1. **Pasabanda de 5 a 15 Hz:** deja la energía del QRS y saca la onda T y el ruido de alta frecuencia.
2. **Derivada:** realza las pendientes empinadas del QRS.
3. **Cuadrado:** todo queda positivo y las pendientes grandes pesan más.
4. **Integración móvil de 150 ms:** junta la energía de cada QRS en un solo pulso.
5. **Umbrales adaptativos:** se siguen dos niveles, el de los picos de señal (SPKI) y el de ruido (NPKI). Cada pico nuevo los actualiza con un peso de 0,125. El umbral es NPKI + 0,25 · (SPKI − NPKI). Si pasa demasiado tiempo sin latido (1,66 veces el RR medio), se busca hacia atrás con la mitad del umbral. Un pico a menos de 200 ms del anterior se descarta (período refractario). Uno a menos de 360 ms con poca pendiente se toma como onda T.

**En nuestro trabajo.** Adaptado a 100 Hz y con las etapas lineales centradas, sin retardo. Tiene seis etapas agregadas, cada una por una falla vista en desarrollo:

| Etapa | Falla que evita | Regla |
|---|---|---|
| Reaprendizaje de los umbrales | Tras un artefacto el umbral queda arriba y el detector queda ciego | Si la búsqueda hacia atrás no encuentra latido, se reaprenden los umbrales |
| Pulso aislado | Oscilaciones sin un QRS aislado | En la señal integrada, prominencia / altura ≥ 0,5 |
| Piso de energía | Ruido de amplitud baja tomado como ECG (c09, x28) | Energía ≥ 5 % de la mediana de los QRS del registro |
| Ventana de onda T según el ritmo | Ondas T que terminan después de 360 ms | La ventana crece con el RR: máx(360 ms; 0,5 · RR medio) |
| Forma | Ondas T altas (x17) | Correlación ≥ 0,5 con la forma de los últimos 8 QRS |
| Energía > 20 Hz | Ondas T altas | Energía rápida ≥ 0,3 de la del QRS anterior; la onda T casi no tiene |

En las diapositivas se habla de "Pan-Tompkins + 5 mejoras": el reaprendizaje se cuenta aparte. En el informe son "seis reglas adicionales". Es lo mismo.

**Cómo se evaluó.**
- **Contra las marcas de PhysioNet,** que son automáticas. Se aceptan como el mismo latido dos picos a menos de 100 ms. Entre 30 y 150 ms de tolerancia la sensibilidad y el valor predictivo positivo cambian menos de un punto. ANSI/AAMI EC57 usa 150 ms.
- **Revisión manual de 50 discrepancias:** 21 eran errores del detector clásico y 18 de la base. El grupo a +380 ms del clásico eran ondas T. La versión mejorada elimina 19 de los 20 errores y conserva 17 de los 18 latidos que la base perdía. La revisión fue dirigida a las discrepancias, así que no estima la tasa de error general.
- **Porcentaje de RR corregidos en desarrollo:**

  | | Marcas de la base | Clásico | Mejorado |
  |---|---|---|---|
  | Mediana por registro | 0,57 % | 0,63 % | 0,36 % |
  | Media | 1,98 % | 3,21 % | 0,88 % |

  En x17 baja de 72 % a menos de 2 %.
- **Robustez (`09`):** con pruebas de estrés (tramos sin ECG, ondas T altas, caída de amplitud) protegen el reaprendizaje, el piso, la ventana según el ritmo, la forma y la energía rápida. Sin el reaprendizaje, 10 noches de desarrollo quedan casi sin latidos. El pulso aislado no protege en ninguna prueba, pero se mantiene porque baja los RR corregidos de forma demostrable.

**En una señal.** En x17 la onda T es alta y empinada, y el clásico la marca como un latido más. Con la forma y la energía rápida se descarta.

**En 30 segundos.** "Pan-Tompkins realza las pendientes del QRS con un pasabanda, una derivada, un cuadrado y una integración, y decide con un umbral que se adapta. A 100 Hz fallaba en tramos sin ECG y con ondas T altas. Agregamos cinco mejoras y el reaprendizaje de los umbrales, cada una por una falla vista, y verificamos con una revisión manual y con pruebas de estrés."

### 5.3 Refinamiento del pico R

**Qué es.** A 100 Hz hay una muestra cada 10 ms, así que el pico R puede estar hasta ±5 ms del verdadero, y cada RR arrastra ±10 ms. Se ajusta una parábola por la muestra máxima y sus dos vecinas, y se toma el tiempo de su vértice.

**La cuenta.** Con las muestras y₋₁, y₀ (máxima) e y₊₁, el vértice está a δ = (y₋₁ − y₊₁) / [2 (y₋₁ − 2y₀ + y₊₁)] muestras de la máxima. Como y₀ es la mayor, |δ| ≤ 0,5.

**Cómo se verificó.** Con la prueba de dos fases: se submuestrea a 50 Hz tomando las muestras pares y, por otro lado, las impares, y se compara dónde queda cada pico. Sin refinar, las dos fases difieren unos 10 ms; refinando, 2,3 ms (en los 47 registros). Es una prueba de consistencia, no de exactitud: no hay una referencia temporal verdadera de mayor resolución.

**¿Importa?** El error de cuantización es como ruido blanco agregado al RR: se reparte en todas las frecuencias, y en la banda lenta su efecto es chico. Se mantiene porque mejora la medición de su paso de forma demostrable, y es lo único que la regla de sencillez dejó.

### 5.4 La serie RR y su limpieza

**Qué es.** Se restan los tiempos de picos consecutivos. Un latido omitido genera un intervalo muy largo, y una detección espuria parte un intervalo en dos.

**En nuestro trabajo.**
- **RR atípico:** fuera de 0,3–2 s (30 a 200 latidos por minuto) o a más del 20 % de la mediana de sus 11 vecinos (~10 s).
- **Los atípicos se reemplazan por interpolación lineal** de los válidos.
- **En desarrollo, el 97 % de los RR queda a menos del 10 % de su mediana local.** Un RR +100 % es un latido perdido, −50 % es un latido de más y −80 % suele ser una onda T.
- **Un minuto con más del 20 % de sus RR corregidos no se evalúa:** ahí la serie es más interpolación que dato. Con el detector final son el 0,6 % de los minutos de desarrollo. Con límites entre 10 % y 40 %, el AUC dentro de la noche queda entre 0,905 y 0,908.
- **Remuestreo a 2 Hz con spline cúbico.** Welch necesita muestras equiespaciadas. La frecuencia de Nyquist (1 Hz) cubre las bandas que se analizan. Interpolar no agrega información fisiológica. A 0,25 Hz el spline conserva el 97 % de la potencia y la interpolación lineal el 68 %; en la banda lenta las dos conservan casi todo.

**En la base.** En la prueba, la persona S21 (c04 y x29) tiene un ritmo muy irregular: el 73 % y el 85 % de sus minutos tienen más del 20 % de RR corregidos y no se evalúan. El ECG está limpio y los latidos se detectan bien; es el ritmo el que no es sinusal (`06` §3). Es un límite del método: supone ritmo sinusal.

### 5.5 La EDR: área del QRS relativa

**Qué es.** Una medida del tamaño del QRS en cada latido, que sube y baja con la respiración.

**En nuestro trabajo.**
- **Área con signo del QRS:** la suma de las muestras del ECG filtrado entre −60 y +60 ms del pico R, por el intervalo entre muestras. Se asigna al instante del latido y se interpola a 2 Hz.
- **Signo:** se orienta según la polaridad dominante del QRS de cada registro.
- **Relativa:** se divide por la mediana del área sin signo de la noche. Así no depende de dónde quedaron los electrodos. La correlación entre la oscilación respiratoria de la EDR y el tamaño del QRS baja de 0,70 a casi 0.
- **Latidos ectópicos fuera:** se excluyen los latidos con RR corregido, que tienen otra forma y cuya área no es respiración.
- **Valores atípicos fuera (Hampel):** se descarta un valor de EDR que se aparta más de 3 escalas robustas de la mediana de sus 11 vecinos. La escala es la desviación absoluta mediana, con un piso para no rechazar crestas suaves.
- **Sin Wiener:** el detector final mide el área sobre el ECG filtrado con el pasabanda solo (§5.7).

**Por qué el área.** Se compararon tres medidas contra la respiración medida en los 8 registros:

| Medida | Coherencia con la respiración (banda respiratoria) | AUC dentro de la noche |
|---|---|---|
| Área del QRS | 0,535 | 0,767 |
| Deriva de la línea de base (segmento PR) | 0,456 | — |
| Amplitud del pico R | 0,336 | 0,838 |

El área es la que mejor sigue la respiración. La amplitud R separa mejor los minutos como indicador aislado, pero se priorizó la EDR como estimador de la respiración. Además, el área usa todo el complejo y es poco sensible a que el pico caiga entre muestras. La deriva no mira el QRS y es muy sensible al movimiento.

**En una señal.** En a03, con apnea, el área del QRS sube y baja cada 30 a 60 s, al mismo ritmo que la envolvente de la respiración medida.

**En la base.** El nivel nocturno de la EDR sube con la cantidad de apnea de la noche en desarrollo (ρ = 0,78), y es lo que mide P2.

### 5.6 Espectro cruzado, coherencia y la feature F

**Espectro cruzado.** Para dos señales x e y, S_xy(f) mide cuánta potencia comparten en cada frecuencia y con qué desfase. Se estima con Welch: en cada segmento se multiplica la transformada de una por el conjugado de la otra, y se promedian los segmentos.

**Coherencia.** C(f) = |S_xy(f)|² / [S_xx(f) · S_yy(f)], entre 0 y 1 (Carter, 1987). No compara alturas: mide si la relación de amplitud y fase entre las dos señales se mantiene de un segmento a otro.
- **Con un solo segmento da 1 siempre:** hace falta promediar varios segmentos.
- **Puede ser alta aunque los espectros sean distintos,** si la relación se mantiene.

**Dónde la usamos.** Para validar la EDR contra la respiración medida:
- **A1, la respiración:** segmentos de 32 s dentro de ventanas de 120 s, con una resolución de ~0,03 Hz, suficiente para la banda respiratoria (0,1–0,5 Hz).
- **A2, la envolvente de la respiración:** en 4 noches con mucha apnea. Mide si la EDR sigue cómo cambia la amplitud de la respiración, que es lo que importa en la banda lenta.

**La feature F de la primera versión.** F es el log₁₀ del promedio de |S_RR,EDR| en la banda: la potencia que comparten el RR y la EDR.

**Por qué F se reemplazó por C.** F resultó casi el promedio de las dos potencias (r = 0,985), y tiene una explicación:
- Siempre se cumple |S_xy| ≤ √(S_xx · S_yy).
- Con coherencia alta, |S_xy| ≈ √(S_xx · S_yy).
- Y log √(S_xx · S_yy) = ½ (log S_xx + log S_yy): el promedio de las dos potencias en log.

Así, F sumaba la EDR minuto a minuto, y dentro de la noche separaba peor que el RR solo (AUC 0,879 contra 0,908). C usa cada señal para lo que mide bien. C no mide acoplamiento ni coherencia.

### 5.7 Filtro de Wiener por realizaciones

**Qué es (Wiener, 1949; Sörnmo y Laguna, 2005).** El filtro lineal que minimiza el error cuadrático medio entre la señal estimada y la verdadera, si se conocen el espectro de la señal S_s(f) y el del ruido S_n(f). Su respuesta es **H(f) = S_s(f) / [S_s(f) + S_n(f)]**:
- donde domina la señal, H ≈ 1;
- donde domina el ruido, H ≈ 0.

**Realizaciones.** Cada latido se toma como una realización de la misma señal más ruido. Se recortan de −250 a +400 ms alrededor del pico R; es el largo de un latido, no una ventana de análisis.
- **Señal:** el promedio de los latidos estima la forma común, y su periodograma da S_s.
- **Ruido:** lo que cada latido se aparta del promedio es el ruido, y el promedio de sus periodogramas da S_n.
- **El filtro:** H(f) se aproxima con un FIR de 129 coeficientes y se aplica al ECG antes de medir el área. Es un solo filtro por registro, igual para todos los latidos, así que la variación del área entre latidos se conserva.

**Qué hacía.**
- **Mediana de H en los 47 registros:** ~0,96 entre 5 y 25 Hz, ~0,7 entre 25 y 40 Hz y ~0,3 entre 40 y 50 Hz.
- **Por encima de ~10 Hz sobra,** porque el área (13 muestras) ya promedia ese ruido. Por debajo de ~5 Hz saca ~12 % de la variación latido a latido, hasta 70 % en algunas noches.
- **En la mayoría de las noches la EDR casi no cambia** (correlación mediana 0,998).
- **Excepción, x17:** el QRS cambia de forma a mitad de la noche, y el promedio no representa a ningún latido.

**Por qué salió.** En la revisión con desarrollo (`07` §9) no mejoraba ninguna medida de forma demostrable (coherencia +0,009, IC −0,003 a +0,027), y la regla de sencillez lo sacó. No se lo consideró una etapa protectora, así que no pasó por las pruebas de estrés de la regla de robustez.

**Qué se vio en la prueba (`12` §4.4).**
- **Las dos noches con el latido más ruidoso** son b05 (SNR −7,6 dB) y x29 (−8,1 dB): el ruido tiene más potencia que el latido.
- **Sin Wiener, el nivel de su EDR sube mucho:** +1,82 y +1,40 en log₁₀. x11, de la misma persona que b05, sube +1,00.
- **Por qué el ruido sube la potencia:** el ruido sobre el QRS entra en el área de cada latido. Si es ruido distinto en cada latido, se reparte en todas las frecuencias, también en la banda lenta, y la potencia sube.
- **Es compatible con que el Wiener protegía la EDR del ruido en esas noches.** Es una lectura posterior y con pocas noches: no se puso a prueba, y no se puede volver a ponerlo por lo que se vio en test.

### 5.8 Welch y la banda de la apnea

**El periodograma y su problema.** El periodograma, el módulo al cuadrado de la transformada de Fourier de un tramo, es un estimador de la densidad espectral de potencia con mucha varianza. Aunque el tramo sea más largo, la varianza en cada frecuencia no baja.

**Welch (1967).** Parte el tramo en segmentos solapados, multiplica cada uno por una ventana, calcula su periodograma y los promedia. Promediar baja la varianza; a cambio, cada segmento es más corto y la resolución en frecuencia es peor (Δf = 1 / largo del segmento).

**En nuestro trabajo.**
- **Ventana de análisis de 240 s centrada en cada minuto,** con un avance de 60 s. Es la misma en todo el trabajo.
- **Welch con 3 segmentos de 120 s,** ventana de Hann y 50 % de solapamiento, quitando la recta de cada segmento.
- **La banda:** con segmentos de 120 s, el espectro está en las frecuencias k/120 Hz. En la banda caen k = 2 a 6: 0,017, 0,025, 0,033, 0,042 y 0,05 Hz, que son ciclos de 60, 40, 30, 24 y 20 s. La banda efectiva es 0,0167–0,05 Hz.
- **P(m):** el log₁₀ de la densidad espectral media en esas cinco frecuencias, por separado para el RR (P_RR) y la EDR (P_EDR).

**Por qué 240 s.** Para ver 0,017 Hz (ciclos de 60 s) con dos ciclos completos en cada segmento hacen falta segmentos de 120 s. Tres segmentos de 120 s solapados al 50 % ocupan 240 s. Con 180, 300 o 360 s la exactitud no cambia de forma demostrable (`10` §1).

**Los bordes de la banda.** La ventana de Hann ensancha cada frecuencia en unos ±0,008 Hz, así que la banda no tiene bordes ideales:
- capta del 83 % al 100 % de la potencia de los ciclos de 20 a 60 s;
- de los ciclos más largos capta solo una parte: una oscilación de 100 s aporta ~26 % de su potencia.

Por eso en el código la banda nominal es 0,01–0,05 Hz, pero se miden 0,017–0,05 Hz.

**Por qué quitar la recta.** Con la ventana de Hann, quitar la media no cambia nada en la banda: una constante solo deja potencia en k = 0 y 1. Quitar la recta saca además la deriva lenta dentro del segmento.

**Lomb.** Para comparar se calculó el RR con Lomb (Lomb, 1976; Laguna et al., 1998), que trabaja con muestras irregulares sin interpolar. Se usó la misma ventana y la misma banda nominal.

**En la base.** En las 31 noches de desarrollo con al menos 20 minutos de cada tipo, el aumento mediano de la potencia del RR con la apnea es máximo en 0,025 Hz (ciclos de 40 s). Con el doble de resolución (`08` §1), el aumento vuelve a concentrarse en ciclos de 20 a 60 s.

### 5.9 La feature C

**Qué es.** C(m) = [P_RR(m) − μ₁] / σ₁ + w · [P̃_EDR − μ₂] / σ₂.
- **Primer término (término RR):** cambia minuto a minuto y dice **cuándo** hay apnea dentro de la noche.
- **Segundo término (término EDR):** es el mismo para toda la noche y dice **cuánta** apnea tiene la noche. Sube o baja todos los minutos de la noche en la misma cantidad, sin cambiar su orden.

**La vara de cada noche.** Un minuto se marca si C > u, es decir, si **término RR > u − término EDR**. A u − término EDR la llamamos la vara de la noche:
- si el nivel de la EDR de la noche es bajo, la vara queda alta y cuesta marcar minutos;
- si es alto, la vara queda baja y se marcan muchos.

Es la mejor forma de explicar los errores (§6.5).

**Cómo se ajustó (solo con desarrollo).**
- **μ y σ:** media y desvío de cada medida en los minutos evaluables de desarrollo.
- **w:** se probó de 0 a 3 cada 0,25 con validación cruzada por personas y se eligió el de mayor AUC. La curva es plana alrededor del máximo, así que el peso exacto importa poco: w = 1.
- **P̃_EDR:** la mediana de P_EDR en todas las ventanas completas de la noche, incluso las que después no se evalúan. No usa etiquetas, así que se calcula igual en test.

**Alternativas que se probaron (`04` §8, `10`).** Ninguna es mejor que C de forma demostrable, ni siquiera sin corregir:
- el RR solo y la EDR sola;
- F;
- sumas minuto a minuto del RR y la EDR;
- G, que centra el RR en su noche y empata con C (se eligió C, que es más simple);
- C con el desvío de la EDR;
- una regresión logística con cuatro términos, como techo.

### 5.10 Umbral de Youden

**Qué es (Youden, 1950).** J = sensibilidad + especificidad − 1. El umbral de Youden es el que maximiza J. En la curva ROC es el punto más alejado de la diagonal.

**Por qué Youden.**
- **Pesa igual los dos errores:** no hay costos definidos, porque el detector no es un diagnóstico.
- **No depende de la prevalencia,** que en estas noches va de 0 % a 97 % de minutos con apnea.

**Otros criterios (validación cruzada, versión evaluada).** Los cuatro separan igual; solo cambia el punto de la curva.

| Criterio | Umbral | Exactitud balanceada |
|---|---|---|
| Youden (elegido) | 0,489 | 0,832 |
| Más cercano a (0, 1) | 0,394 | 0,831 |
| Máxima exactitud | 0,596 | 0,831 |
| Sensibilidad = especificidad | 0,331 | 0,830 |

La máxima exactitud elige un umbral más alto solo porque en desarrollo hay más minutos normales: depende de la prevalencia. **El detector final tiene umbral 0,481350**; 0,489 era el de la versión con Wiener.

### 5.11 Curva ROC y AUC

**Curva ROC.** Para cada umbral posible se calculan la sensibilidad y 1 − especificidad, y se grafican. Muestra todos los compromisos posibles entre detectar y dar falsas alarmas.

**AUC.** El área bajo la curva ROC. Es la probabilidad de que un minuto con apnea tenga un puntaje mayor que un minuto normal elegido al azar, contando los empates como medio acierto (estadístico de Mann–Whitney; Hanley y McNeil, 1982). 0,5 es el azar y 1 es separación perfecta. No depende del umbral.

**AUC dentro de la noche (P1).** Se calcula el AUC con los minutos de cada noche por separado y se promedia. Solo entran las noches con al menos 20 minutos de cada tipo: con menos, el AUC de una noche es muy inestable (13 noches de 7 personas en test). Quita las diferencias entre personas, porque solo compara minutos de la misma noche.

**¿Por qué el AUC dentro de la noche de C es igual al del RR?** Porque dentro de una noche el término EDR es constante: sumarle una constante a todos los minutos no cambia su orden.

**AUC con todos los minutos (P3).** Mezcla los minutos de todas las noches, así que incluye las diferencias entre noches. Por eso es el que mide si C detecta en personas nuevas.

### 5.12 Correlación de Spearman

**Qué es.** La correlación de Pearson calculada sobre los rangos (los puestos) de los valores en lugar de los valores. Mide si dos cantidades suben juntas de forma monótona, aunque la relación no sea lineal, y es poco sensible a valores extremos.

**Dónde la usamos.**
- **P2:** el nivel nocturno de la EDR contra el % de minutos con apnea de cada noche (20 noches en test).
- **ρ por noche:** el % de minutos marcados contra el % real de cada noche.

Son medidas distintas: P2 usa directamente el nivel de la EDR, y el ρ por noche usa la salida del detector.

### 5.13 Bootstrap por personas

**Qué es (Efron y Tibshirani, 1993).** Se estima la variabilidad de un resultado remuestreando los datos con reposición muchas veces y recalculándolo. El intervalo de confianza del 95 % son los percentiles 2,5 y 97,5 de esos valores.

**Por qué por personas.** Los minutos de una noche no son independientes: los episodios duran una mediana de 6 minutos, y las noches de una misma persona se parecen. Si se remuestrearan minutos, los intervalos saldrían demasiado angostos. Por eso se sortean personas, y cada persona entra con todas sus noches y sus minutos.

**En nuestro trabajo.**
- **P1, P2 y P3:** 4000 sorteos, semilla 2026.
- **Comparaciones pareadas** (C contra F, final contra versión evaluada): 2000 sorteos. En cada sorteo las dos versiones se evalúan con las mismas personas.
- **p de una diferencia:** p = 2 · mín(P(d ≤ 0), P(d ≥ 0)) sobre los sorteos.

**Predicciones fijas o repetir el ajuste.** Esta es una corrección importante del trabajo:
- **En test el detector está fijo:** sus predicciones no cambian, y lo único que varía entre sorteos es qué personas entran. Ahí corresponde dejar fijas las predicciones.
- **En desarrollo, al comparar versiones con validación cruzada,** el ajuste (μ, σ, w y umbral) cambia si cambian las personas. Hay que repetir toda la validación cruzada en cada sorteo.
- **Con las predicciones fijas, los p salían demasiado chicos.** Ejemplo: el p de Hampel era < 0,001 con predicciones fijas, y 0,61 repitiendo el ajuste. El efecto venía de una sola persona (c10 y x18).

### 5.14 Validación cruzada por personas

**Qué es.** Se parte desarrollo en grupos de personas. Cada grupo se evalúa con lo que se ajustó en los demás, y así se estima cómo rinde el procedimiento en personas no vistas.

**En nuestro trabajo.** 5 grupos de personas (semilla 2026). En cada vuelta se ajustan con cuatro grupos μ, σ, w y el umbral de Youden, y se evalúa el quinto. Es la estimación de desarrollo que se compara con test: exactitud 0,830 para el detector final.

**Qué se ajusta y con qué datos.**

| Qué | Con qué datos |
|---|---|
| Filtro, banda, ventana, etapas del detector | Análisis de las señales de desarrollo (sin ajustar a la etiqueta del minuto) |
| μ₁, σ₁, μ₂, σ₂ | Minutos evaluables de desarrollo |
| w | Validación cruzada por personas en desarrollo (máximo AUC) |
| Umbral | Youden en desarrollo |
| En test | Nada: el detector se aplica con los parámetros congelados |

### 5.15 Comparaciones múltiples: Holm y unión-intersección

**El problema.** Con muchas comparaciones, alguna sale "significativa" por azar.

**Holm (1979; Aickin y Gensler, 1996).**
1. Se ordenan los m valores p de menor a mayor.
2. El i-ésimo se multiplica por (m − i + 1), y se toma el máximo acumulado para mantener el orden.
3. Una diferencia resiste si su p corregido es < 0,05.

Controla la probabilidad de declarar al menos una diferencia falsa en toda la familia, y es siempre al menos tan potente como Bonferroni.

**Por qué P1–P3 no se corrigen.** H se sostiene solo si se cumplen las tres. Es una prueba de unión-intersección: para declarar que H se sostiene hay que rechazar las tres hipótesis nulas, así que el error de toda la prueba no supera el 5 % con que se evalúa cada una (Berger, 1982). Corregir sería exigir de más.

### 5.16 Las reglas de revisión: sencillez y robustez

**Por qué.** Al auditar las 88 decisiones aparecieron 8 etapas con una razón física, pero sin una demostración con datos de que hicieran falta. Se revisaron con dos reglas, escritas y subidas al repositorio antes de aplicarlas, y solo con desarrollo.

**Regla de sencillez (`07`, `docs/criterio_parsimonia.md`).** Una etapa queda solo si mejora de forma demostrable la medición de su paso o el detector (bootstrap que repite el ajuste, Holm). Solo quedaba el refinamiento del pico R.

**El problema de esa regla.** También sacaba etapas que protegen contra fallas raras o concentradas en pocas personas. Con 19 personas su beneficio no se puede demostrar.

**Regla de robustez (`08`–`09`, `docs/criterio_robustez.md`).** Una etapa protectora se mantiene, salvo que empeore el detector de forma demostrable o que una prueba de estrés sin etiquetas muestre que no protege. Cada prueba de estrés perturba los registros de una forma que imita la falla y mide cuánto cambia la salida con la etapa y sin ella:

| Etapa | Prueba de estrés | Resultado |
|---|---|---|
| EDR relativa | ECG ×0,5 o ×2 | Con la EDR en mV·ms cambia la decisión en el 15 % de los minutos; con la relativa, en ninguno |
| Excluir ectópicos | 5 % de latidos ectópicos | El nivel de la EDR se mueve 1,31 sin excluirlos y 0,52 excluyéndolos |
| Hampel | 5 % de artefactos | 1,36 sin excluirlos, 0,67 con el procedimiento de Varon y 0,06 con Hampel |
| Minutos con > 20 % de RR corregidos | Ritmo irregular simulado | Sin la exclusión cambia la decisión en el 10 % de esos minutos |
| Quitar la recta en Welch | Deriva lenta | P_RR se mueve 0,008 quitando la media y 0,003 quitando la recta |

**Resultado.** Se mantienen las etapas protectoras y el spline cúbico, que conserva la respiración. Salen el Wiener y la medida de confianza por movimiento. El detector final tiene exactitud 0,830 en validación cruzada, contra 0,836 de la versión evaluada; la diferencia no es demostrable.

**Dos agregados posteriores, declarados como decisiones adaptativas:**
- **La comparación directa de Hampel con Varon** se agregó después de ver la prueba S2, aunque antes de calcularla. Sí cambió la elección: la regla original elegía el procedimiento publicado (Varon) si los dos protegían, y la comparación mostró que Hampel protege unas diez veces más.
- **La vía de las fallas reales del detector de QRS** se agregó después de una corrida preliminar con 16 registros. En la corrida completa no cambió ninguna decisión.

---

## 6. Los resultados que hay que saber

### 6.1 Desarrollo (validación cruzada por personas)

| | Versión evaluada (con Wiener) | Detector final (sin Wiener) |
|---|---|---|
| Exactitud | 0,836 | 0,830 |
| Sensibilidad · especificidad | 0,81 · 0,85 | 0,780 · 0,863 |
| AUC con todos los minutos | 0,907 | 0,888 |
| AUC dentro de la noche | 0,908 | 0,908 |
| % marcado en controles | 7,4 % | 9,5 % |
| P2 | 0,83 | 0,787 |

Con el bootstrap que repite el ajuste, la diferencia de exactitud es +0,006 (IC −0,051 a +0,049): no es demostrable.

**C contra las alternativas (versión evaluada, `04` §8):**
- el RR solo acierta 0,740 y marca el 36,9 % de los minutos en las noches sin apnea;
- F acierta 0,820 y marca el 16,7 %;
- C acierta 0,836 y marca el 7,4 %.

Ninguna de las 60 diferencias resiste Holm con el bootstrap que repite el ajuste (`10`).

### 6.2 Prueba 1 (`05`): la versión evaluada, con Wiener

- **H se sostiene:** P1 0,869 (0,827–0,930), P2 0,658 (0,117–0,786) y P3 0,849 (0,688–0,938).
- **Con el umbral fijo:** sensibilidad 0,709, especificidad 0,834 y exactitud 0,780.
- **En controles,** C marca el 11,2 % de los minutos, F el 21,6 % y el RR solo el 34,1 %.
- **Con Holm resisten 3 de 13 diferencias, las tres a favor de C en falsas alarmas:** los controles contra F (−10,4 puntos) y contra el RR solo (−22,9), y la especificidad contra F (+0,072).

### 6.3 Prueba 2 (`11`): el detector final

**Por qué hay una segunda prueba.** El detector cambió después de la primera (se sacaron el Wiener y la confianza), así que ninguna de las versiones nuevas tenía una evaluación independiente. Se registró un plan (`docs/plan_test_final.md`) y el notebook sin ejecutar, y se corrió una sola vez.

**No es ciega.** Esas 20 noches se usaron en la primera entrega y en `05`, y `06` analizó sus fallas.

**P1 no es evidencia nueva.** El RR es idéntico en las dos versiones, así que P1 tenía que repetir exactamente el valor de `05`, y lo repitió. Sirvió como control del cálculo.

**Los minutos.** Se evaluaron 8844 de 9639 minutos (91,8 %), de 20 noches y 10 personas.

| Predicción | Valor | IC 95 % | ¿Se cumple? |
|---|---|---|---|
| P1 · AUC dentro de la noche del RR | 0,869 | 0,827–0,930 | sí |
| P2 · nivel de la EDR contra % de apnea | 0,531 | −0,152–0,732 | **no** |
| P3 · AUC de C | 0,827 | 0,627–0,937 | sí |

| | Predice apnea | Predice normal | Total |
|---|---|---|---|
| Apnea | 2671 | 1151 | 3822 |
| Normal | 839 | 4183 | 5022 |

Sensibilidad 0,699 (0,303–0,905), especificidad 0,833 (0,727–0,927) y exactitud 0,775 (0,692–0,862).

**C contra F y el RR solo:**

| | C | F | RR solo |
|---|---|---|---|
| Exactitud | 0,775 | 0,740 | 0,717 |
| Especificidad · sensibilidad | 0,833 · 0,699 | 0,726 · 0,758 | 0,698 · 0,742 |
| AUC | 0,827 | 0,814 | 0,807 |
| % marcado en controles | 6,1 % | 19,5 % | 34,1 % |

Resisten Holm las mismas tres diferencias que en `05`: la especificidad contra F (+0,107) y los controles contra F (−13,4 puntos) y contra el RR solo (−28,0).

**El % marcado en controles** es la media de los porcentajes de las cinco noches de control (6,1 %). Si se juntan sus minutos, C marca 119 de 1556 (7,6 %). Son dos ponderaciones distintas.

### 6.4 El detector final contra la versión con Wiener, en test

| | Final | Con Wiener | Diferencia (IC 95 %) | p de Holm |
|---|---|---|---|---|
| Sensibilidad | 0,699 | 0,709 | −0,010 (−0,078 a +0,071) | 1 |
| Especificidad | 0,833 | 0,834 | −0,001 (−0,131 a +0,100) | 1 |
| Exactitud | 0,775 | 0,780 | −0,005 (−0,067 a +0,054) | 1 |
| AUC de C | 0,827 | 0,849 | −0,021 (−0,098 a +0,023) | 1 |
| P2 | 0,531 | 0,658 | no se puso a prueba | — |

- **Las dos versiones deciden distinto en 933 minutos (10,5 %).** El final acierta en 444 y la versión con Wiener en 489: casi un empate.
- **Con Wiener se acierta más en b05 y x11; sin Wiener, en c08, b04 y x30.**
- **No se vuelve al Wiener,** porque elegir con test haría que test deje de ser una evaluación.

### 6.5 Dónde falla y por qué (`12`)

**Los errores vienen en noches enteras.**
- 5 noches de 3 personas concentran el 82 % de los minutos con apnea perdidos: a11, x26, a06, x15 y x13.
- 5 noches concentran el 61 % de las falsas alarmas: b05, a07, c08, x30 y x11.

**Por qué se pierde apnea:**
- **a11 (48 % de apnea, 0 % marcado):** el RR sube en cada episodio, pero el nivel de la EDR de la noche es el de un control (término EDR −1,42). La vara queda en 1,90 y ningún minuto la alcanza.
- **x15 y a06 (misma persona):** el RR sube durante la apnea hasta cerca de 1, justo en la vara (0,97). Se marcan muy pocos minutos.
- **x26:** la vara es baja (0,30), pero el RR de muchos minutos con apnea queda alrededor de ella. Se detecta la mitad.
- **Lo que tienen en común:** estas personas tienen un RR que oscila poco en la banda aunque no tengan apnea. Su AUC dentro de la noche es alto (0,83 a 0,86): el RR ordena bien la noche, y el error está en dónde queda la vara.

**Por qué se marca de más:**
- **b05 (14 % de apnea, 59 % marcado):** tiene el término EDR más alto de test (+0,87), así que la vara queda en −0,39 y el RR de casi toda la noche la supera.
- **c08 (control):** el RR de esta persona oscila cerca de la vara toda la noche.

**Por qué falla P2:**
- **a11** tiene, con 48 % de apnea, el nivel de un control.
- **Sin Wiener, b05 y x11 (misma persona, S17, con 14 % y 3 % de apnea) suben su nivel de EDR.** b05 pasa del segundo nivel más bajo de test al más alto. Son noches con el latido muy ruidoso.
- **Sin esa persona, ρ = 0,67.** En los sorteos con ρ más bajo, S17, S10 y S06 aparecen más seguido.

**Otros resultados:**
- **Categoría de cada noche:** coincide en 14 de 20.
- **Exactitud por persona:** de 0,52 a 0,97.
- **Test contra desarrollo:** las personas de test tienen un índice de masa corporal mayor (31 contra 27). En las noches con poca apnea el nivel de la EDR es más alto en test, y su rango queda más comprimido. El término RR se reparte igual en las dos bases.

---

## 7. Cómo explicar los resultados

**Qué se sostiene y qué no.**
- **(a) Dentro de la noche, se sostiene.** El RR tiene más potencia lenta en los minutos con apnea, en todas las noches. Se cumple en las dos pruebas.
- **(b) Entre noches, no se demostró con el detector final.** Con Wiener se cumplió (0,658) y sin él no (0,531, con un intervalo que incluye el 0). Un resultado no significativo no demuestra que la relación no exista: con 10 personas el intervalo es muy ancho.
- **(c) La detección se sostiene.** C clasifica los minutos de personas nuevas mejor que el azar, en las dos pruebas.

**Lo que aporta la EDR aunque falle P2.** El plan decía que, si fallaba P2, C se reduciría en la práctica al RR solo. No pasó: C marca el 6 % de los minutos en las noches sin apnea, contra el 34 % del RR solo, y esa diferencia resiste Holm en las dos pruebas. El nivel de la EDR separa bien las noches sin apnea de las que tienen mucha, aunque no ordene las noches con apnea por cantidad.

**Por qué no se vuelve al Wiener.** Con Wiener se cumplía P2, pero elegir la versión que mejor dio en test haría que test deje de ser una evaluación: el resultado sería optimista. Para decidirlo hace falta otra base, con personas nuevas.

**Qué aprendimos del Wiener.** La regla de sencillez sacó una etapa porque con 19 personas no se podía demostrar que mejorara algo. Es lo mismo que pasaba con las etapas protectoras, pero el Wiener no se trató como protector y no pasó por las pruebas de estrés. En la prueba, sin él, el ruido de dos noches entró en la EDR.

**Limitaciones que hay que poder nombrar:**
- **Test chico y ya usado:** 10 personas, y ya se usó en la primera entrega y en `05`.
- **Personas inferidas:** el agrupamiento se reconstruyó, no viene en la base.
- **EDR validada en pocas noches:** 8, con respiración medida, todas en desarrollo.
- **Supone ritmo sinusal:** no sirve con arritmias sostenidas (S21).
- **Es retrospectivo:** usa la mediana de toda la noche y una ventana centrada.
- **El nivel de la EDR también acompaña al índice de masa corporal,** que a su vez va con la cantidad de apnea. No se puede separar del todo.

**Próximo paso.** Hacer la EDR robusta al ruido del QRS y validar en otra base, con personas nuevas.

---

## 8. Preguntas probables de la defensa

Cada respuesta está pensada para decirse en 20 a 40 segundos.

**Contexto y diseño**

1. **¿Por qué no usaron aprendizaje automático, si el estado del arte lo usa?** El objetivo es mostrar el fenómeno de forma interpretable: qué aporta cada señal y dónde falla. Una combinación explícita de dos medidas y un umbral permite explicar cada error con la vara de la noche. Los trabajos con redes usan otros protocolos, así que sus exactitudes no se comparan directamente con las nuestras.
2. **¿El detector diagnostica apnea?** No. Cuenta minutos con apnea, no eventos por hora, y usa toda la noche de forma retrospectiva. La categoría de cada noche se informa solo como resultado secundario.
3. **¿Por qué la unidad es el minuto?** Porque las etiquetas de la base son por minuto. La ventana de 240 s es el contexto del minuto, no la unidad.
4. **¿Por qué partir por persona?** Dos noches de una misma persona se parecen mucho (difieren 7 puntos de apnea contra 37 entre personas). Si una persona estuviera en los dos lados, el resultado sería optimista.
5. **¿Cómo saben qué noches son de la misma persona?** Por el perfil idéntico (edad, sexo, altura y peso), verificado con la forma del latido.

**Señales y latidos**

6. **¿Por qué ese filtro?** La especificación salió de medir dónde está el latido y dónde los problemas en los 47 registros. Es Butterworth porque es plano en la banda de paso; orden 3 porque cumple la especificación; ida y vuelta para que el pico R no se mueva.
7. **¿Por qué no un notch de 50 Hz?** El pasabanda corta en 45 Hz y ya atenúa los 50 Hz. Además, las features miran frecuencias mucho más bajas que el latido.
8. **¿Cómo saben que el detector de latidos anda bien, si las marcas de la base son automáticas?** Por la revisión manual de 50 discrepancias: la versión mejorada corrige 19 de los 20 errores del clásico y conserva 17 de los 18 latidos que la base perdía. También porque tiene menos RR corregidos que las marcas de la base, y por las pruebas de estrés de `09`.
9. **¿Para qué refinar el pico R?** A 100 Hz el pico tiene ±5 ms de error y cada RR ±10 ms. La parábola baja el desacuerdo entre fases de 10 a 2,3 ms. En la banda lenta el efecto es chico, pero es una mejora demostrable de su paso.
10. **¿Qué hacen con los latidos mal detectados o ectópicos?** En el RR, los intervalos imposibles o muy distintos de sus vecinos se interpolan, y los minutos con más del 20 % corregido no se evalúan. En la EDR, los latidos con RR corregido se excluyen, y los valores atípicos se sacan con Hampel.

**EDR, Wiener y espectro**

11. **¿Por qué el área y no la amplitud R, si la amplitud R separaba mejor los minutos?** Porque el área sigue mejor la respiración medida (coherencia 0,535 contra 0,336), y la EDR tiene que estimar la respiración. Además, el área usa todo el complejo y depende menos de que el pico caiga entre muestras.
12. **¿Por qué la EDR relativa?** Para que no dependa de dónde quedaron los electrodos. En mV·ms, la oscilación de la EDR crece con el tamaño del QRS (ρ = 0,70); en forma relativa, no (≈ 0). En la prueba de estrés, con el ECG ×0,5 o ×2, ningún minuto cambia de decisión con la EDR relativa.
13. **¿Qué es la coherencia y por qué no la usaron como feature?** Mide si la relación de amplitud y fase entre dos señales se mantiene en cada frecuencia. La usamos para validar la EDR contra la respiración. Como feature, la primera versión usaba F, la potencia cruzada, y resultó casi el promedio de las dos potencias.
14. **¿Qué es el filtro de Wiener por realizaciones?** Cada latido es una realización: el promedio estima la señal y el residuo el ruido. H(f) = S_s / (S_s + S_n) deja pasar donde domina la señal y atenúa donde domina el ruido.
15. **¿Sacar el Wiener fue un error?** Siguió la regla registrada: en desarrollo no mejoraba nada de forma demostrable. En la prueba, sin él, dos noches con el latido muy ruidoso subieron mucho su nivel de EDR, y eso es lo que más bajó P2. Lo que aprendimos es que el Wiener protegía contra el ruido y no lo probamos como etapa protectora. No se puede volver a ponerlo por lo que se vio en test.
16. **¿Por qué Welch y no el periodograma?** Porque el periodograma tiene mucha varianza, y promediar segmentos la baja.
17. **¿Por qué ventana de Hann?** Reduce la fuga espectral, es decir, que la potencia de una frecuencia aparezca en las vecinas.
18. **¿Por qué 240 s?** Para ver ciclos de 60 s con dos ciclos completos por segmento hacen falta segmentos de 120 s, y tres segmentos solapados al 50 % ocupan 240 s. Con 180, 300 o 360 s no cambia de forma demostrable.
19. **¿Por qué 0,017–0,05 Hz si la apnea dura hasta 100 s?** Con segmentos de 120 s la primera frecuencia útil es 1/60 Hz. Los ciclos de 60 a 100 s entran solo en parte. Medido con el doble de resolución, el aumento con la apnea se concentra entre 20 y 60 s.
20. **¿Por qué remuestrear a 2 Hz?** Welch necesita muestras equiespaciadas, y 2 Hz tiene un Nyquist de 1 Hz, que cubre las bandas que se analizan.

**Feature, umbral y estadística**

21. **¿Por qué la mediana de toda la noche para la EDR?** El nivel de la EDR dice cuánta apnea tiene la noche, no cuándo. La mediana es robusta y no usa etiquetas. Es retrospectiva: hace falta la noche completa.
22. **¿Por qué w = 1?** Se probó de 0 a 3 con validación cruzada por personas. La curva es plana alrededor del máximo, así que el peso exacto importa poco.
23. **¿Por qué Youden?** No hay costos definidos para cada error, y Youden no depende de la prevalencia, que cambia de 0 % a 97 % entre noches. Otros criterios dan la misma exactitud balanceada.
24. **¿Qué mide el AUC dentro de la noche, y por qué es igual para C y para el RR?** Si el puntaje ordena bien los minutos de una misma noche, sin las diferencias entre personas. Es igual porque el término EDR es constante dentro de la noche.
25. **¿Por qué Spearman?** Porque mide si dos cantidades suben juntas aunque la relación no sea lineal, y es poco sensible a valores extremos.
26. **¿Por qué el bootstrap es por personas?** Porque los minutos de una persona no son independientes. Remuestrear minutos daría intervalos demasiado angostos.
27. **¿Por qué no corrigen P1–P3 por comparaciones múltiples?** Porque hacen falta las tres: es una prueba de unión-intersección, y el error de toda la prueba no supera el 5 % (Berger, 1982).
28. **¿Qué es Holm?** Una corrección para muchas comparaciones: ordena los p y multiplica el i-ésimo por (m − i + 1). Es más potente que Bonferroni.
29. **¿Qué se ajusta en desarrollo y qué en test?** En desarrollo, μ, σ, w y el umbral. En test, nada: el detector se aplica con los parámetros congelados y verificados con un hash.

**Las pruebas**

30. **¿Por qué evaluaron dos veces en test? ¿No es hacer trampa?** La primera evaluó la versión con Wiener. Después se revisaron las etapas solo con desarrollo, con reglas escritas antes, y el detector cambió. La segunda evalúa el detector final una sola vez, con el plan registrado antes. Decimos explícitamente que no es ciega y no usamos test para elegir: aunque con Wiener dio mejor, no se vuelve atrás.
31. **¿Entonces la hipótesis es falsa?** Se sostiene en parte. Dentro de la noche y la detección se cumplen en las dos pruebas. La parte entre noches se cumplió con Wiener y no con el detector final. Con 10 personas, que no se cumpla no demuestra que no exista la relación.
32. **¿Por qué falla en a11?** El RR sube en cada episodio, pero el nivel de la EDR de esa noche es el de un control. La vara queda tan alta que no marca ningún minuto.
33. **¿Por qué falla en b05?** Su nivel de EDR es el más alto de test con solo 14 % de apnea. Es una de las noches con el latido más ruidoso, y sin Wiener el ruido entra en la EDR.
34. **¿C es mejor que el RR solo?** En falsas alarmas sí, de forma demostrable: 6 % contra 34 % en los controles. En exactitud y AUC está arriba, pero sin diferencia demostrable. El RR solo tiene algo más de sensibilidad porque marca muchos más minutos.
35. **¿Qué pasa con los minutos que no se evalúan?** Son el 8 % en test, casi todos de una persona con un ritmo muy irregular (c04 y x29). El método supone ritmo sinusal.
36. **¿Qué son las pruebas de estrés?** Perturbaciones simuladas, sin etiquetas, que imitan una falla. Se mide cuánto cambia la salida con la etapa y sin ella. Muestran si una etapa protege, no cuánto aparece la falla en los datos reales.

---

## 9. Correcciones antes de presentar

Al comparar la presentación con el informe y el repositorio aparecieron estas diferencias. Conviene corregirlas antes de la defensa, o al menos saber qué decir si preguntan.

| Diapositiva | Qué dice | Qué corresponde |
|---|---|---|
| 2, 22 | La agenda tiene 4 partes, las notas dicen "cinco partes", y el separador de conclusiones se llama "5. Conclusiones" | Unificar: 4 partes, y "4. Conclusiones" |
| 8 | Cita `data/particion.csv` | El archivo es `data/split.csv` |
| 12, 30 | El refinamiento baja el desacuerdo de 10 a 2,5 ms | El informe y la diapositiva 19 dicen 2,3 ms, que es el valor en los 47 registros (`07`). 2,5 ms sale de `02`. Usar 2,3 |
| 12 | Los minutos con más de 20 % de RR corregidos son el 0,2 % | Con el detector final son el 0,6 % de los minutos de desarrollo (131 de 22 907). 0,2 % salía de una versión anterior en `02` |
| 10, 12 | "Pan-Tompkins + 5 mejoras" | El informe dice seis reglas adicionales. Es lo mismo si se aclara: el reaprendizaje de los umbrales más cinco mejoras |
| 17 | "C: exactitud 0,836 · sensibilidad 0,81 · especificidad 0,85" | Son de la versión evaluada (con Wiener). El detector final tiene 0,830 · 0,780 · 0,863. Aclararlo oralmente o poner "versión evaluada" |
| 26 | "Bootstrap, 2000 réplicas" | P1–P3 usan 4000 sorteos y las comparaciones pareadas 2000, como dice el informe |
| 7 | Cinco objetivos específicos | El informe tiene tres. No es un error, pero conviene que coincidan |

**Del informe** no aparecieron diferencias con el repositorio en los números revisados: la partición, los parámetros, las tres predicciones, la clasificación, las comparaciones con F y el RR solo, y el análisis posterior.

---

## 10. Glosario español–inglés

Para quien presente en inglés, y para leer las referencias.

| Español | Inglés |
|---|---|
| apnea obstructiva del sueño | obstructive sleep apnea (OSA) |
| índice de apnea-hipopnea | apnea–hypopnea index (AHI) |
| polisomnografía | polysomnography (PSG) |
| derivación del ECG | ECG lead |
| intervalo RR | RR interval |
| frecuencia cardíaca | heart rate |
| variación cíclica de la frecuencia cardíaca | cyclic variation of heart rate |
| arritmia sinusal respiratoria | respiratory sinus arrhythmia |
| respiración derivada del ECG | ECG-derived respiration (EDR) |
| área del QRS | QRS area |
| deriva de la línea de base | baseline wander |
| interferencia de línea (50 Hz) | power-line interference |
| filtro de fase cero (ida y vuelta) | zero-phase (forward–backward) filter |
| detector de QRS | QRS detector |
| período refractario | refractory period |
| búsqueda hacia atrás | search-back |
| latido ectópico | ectopic beat |
| realizaciones del latido | beat realizations (ensemble) |
| filtro de Wiener | Wiener filter |
| densidad espectral de potencia | power spectral density (PSD) |
| espectro cruzado | cross-spectrum (cross-power spectral density) |
| coherencia | (magnitude-squared) coherence |
| ventana de Hann | Hann window |
| solapamiento | overlap |
| fuga espectral | spectral leakage |
| umbral | threshold |
| índice de Youden | Youden's index |
| curva ROC, área bajo la curva | ROC curve, area under the curve (AUC) |
| sensibilidad, especificidad, exactitud | sensitivity, specificity, accuracy |
| correlación de Spearman | Spearman rank correlation |
| intervalo de confianza | confidence interval |
| remuestreo bootstrap por personas | subject-level (cluster) bootstrap |
| validación cruzada por personas | subject-wise cross-validation |
| corrección de Holm | Holm correction (Holm–Bonferroni) |
| prueba de unión-intersección | intersection–union test |
| conjunto de desarrollo, de prueba | development set, test set |
| prueba de estrés | stress test |

---

**Referencias principales.** Están completas, con DOI, en el informe y en `docs/referencias.md`: Pan y Tompkins (1985), Welch (1967), Wiener (1949), Sörnmo y Laguna (2005), Carter (1987), Youden (1950), Efron y Tibshirani (1993), Holm (1979), Aickin y Gensler (1996), Berger (1982), Guilleminault et al. (1984), Charlton et al. (2018), Varon et al. (2020), Penzel et al. (2000), Kapur et al. (2017), Kligfield et al. (2007), Lomb (1976), Laguna et al. (1998) y Hanley y McNeil (1982).
