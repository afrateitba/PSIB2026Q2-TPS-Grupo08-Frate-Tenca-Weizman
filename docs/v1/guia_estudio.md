# Guía de estudio del trabajo de señales (Grupo 8)

**Acoplamiento cardiopulmonar derivado del electrocardiograma como criterio de detección de apnea del sueño**

**Cómo está armada.**
- Las etapas van en el orden en que se decidieron.
- Cada etapa responde lo mismo: qué pregunta tenía, qué se hizo, con qué parámetros y por qué, qué salió y qué se decidió.
- Las decisiones que no salen de datos están marcadas **[criterio]**. Todo lo demás se midió en los registros de desarrollo.
- Al final hay:
  - una tabla con todos los parámetros;
  - los desvíos declarados;
  - qué quedó de cada tema obligatorio;
  - preguntas probables de la defensa;
  - un glosario.

**Fuentes.** `docs/esquema_v3.md`, `docs/plan_test.md`, las salidas guardadas de los notebooks 00 a 14 y 99, y el código de `src/`.

**Palabras que se usan como abreviatura.**

| Palabra | Qué es |
|---|---|
| **Serie RR** | Los intervalos de tiempo entre picos R consecutivos. R es el nombre de la onda, no una sigla. |
| **Respiración derivada** | La respiración que se estima a partir del electrocardiograma. |
| **Variabilidad cardíaca** | La variabilidad de la frecuencia cardíaca. |
| **Referencia** | La mejor feature de variabilidad cardíaca, la que compite contra F. |
| **Área** | El área bajo la curva de sensibilidad contra 1 − especificidad, por minuto. |
| **Acierto por registro** | La correlación de Spearman entre la fracción de apnea estimada y la anotada de cada noche. |
| **Intervalo** | El intervalo de confianza del 95 %. |

---

## 0. El trabajo en una página

**Objetivo.** Decidir minuto a minuto, usando solo el electrocardiograma, si hay apnea. No se usa aprendizaje automático: hay una sola feature y un punto de corte estadístico, como pidió la docente.

**Hipótesis.**
- **H1.** Durante la apnea aparece un acoplamiento lento (0,01–0,1 Hz) entre la serie RR y la respiración derivada, dentro de cada sujeto. El acoplamiento respiratorio (0,15–0,4 Hz) no desaparece.
- **H2.** La feature que combina RR y respiración derivada (F) detecta la apnea mejor que la mejor feature de variabilidad cardíaca, que usa solo el RR.

**Detector final (congelado).**

```
electrocardiograma a 100 Hz
  → pasabanda Butterworth 0,5–45 Hz, orden 3, ida y vuelta
  → picos R: marcas de la base + búsqueda a ±30 ms + parábola de 3 puntos
       ├→ serie RR limpia (0,3–2 s; ±20 % de la mediana de 11 vecinos)
       └→ respiración derivada: área con signo del QRS en ±60 ms
  → las dos series remuestreadas a 2 Hz (spline cúbico)
  → F = log de la potencia cruzada media en 0,01–0,05 Hz
        (ventana de 240 s centrada en el minuto; Welch con 3 segmentos de 120 s)
  → el minuto es apnea si F ≥ −6,9486 (umbral de Youden fijado en desarrollo)
```

La referencia es la potencia de la serie RR en 0,01–0,04 Hz, estimada con Lomb en una ventana de 180 s. El minuto es apnea si esa potencia es ≥ 0,0012585.

**Resultados principales.**

| | Área: F | Área: referencia | Acierto por registro: F | Acierto por registro: referencia |
|---|---|---|---|---|
| Desarrollo completo (optimista) | 0,876 | 0,810 | 0,81 | 0,42 |
| Validación cruzada anidada (estimación honesta) | 0,851 | 0,729 | 0,807 | F la supera por +0,573 |
| Test (10 sujetos, una sola vez) | 0,785 | 0,793 | 0,634 | 0,613 |

**Conclusión.**
- **H1** se sostuvo en desarrollo, pero no se replicó en test.
- **H2** no se confirma ni se rechaza. En test, ninguna de las dos medidas muestra diferencia, y los intervalos son muy anchos.
- **La ventaja de desarrollo no se reprodujo,** sobre todo porque F rindió menos en test.

---

## 1. Datos y restricciones

### 1.1 La base Apnea-ECG (PhysioNet)

- **Registros.** Son 70 registros nocturnos de una derivación, a 100 Hz. Cada minuto tiene una etiqueta de apnea o normal, puesta por un experto a partir de la polisomnografía (dato citado de Penzel et al., 2000).
- **Origen.** Vienen del Challenge 2000: 35 del conjunto de aprendizaje (a01–a20, b01–b05, c01–c10) y 35 del de prueba (x01–x35). Se usan los 70 y la partición es propia.
- **Categorías.** A son las noches con apnea, B las limítrofes y C los controles.
- **Respiración real.** La traen 8 registros (a01–a04, b01, c01–c03), con tórax, abdomen y flujo nasal. Se usa **solo para validar**, nunca para detectar **[criterio: el detector usa solo el electrocardiograma]**.
- **Marcas de QRS.** Los archivos `.qrs` son automáticos (programa `sqrs125`) y no están auditados.

### 1.2 Restricciones

| De dónde | Qué exige |
|---|---|
| Consigna | **Temas obligatorios:** adquisición, filtros convencionales, filtros óptimos, segmentación, recorte en realizaciones, detección de QRS, variabilidad cardíaca y Lomb. **Informe:** 8 páginas más 4 de anexo. **Defensa:** todos responden sobre todo. |
| Devolución | Sin aprendizaje automático. Umbral por índice de Youden. Análisis nuevo respecto de cuatrimestres anteriores. Partición 70/30. |
| Propias | Solo el electrocardiograma para detectar. Cada decisión, con datos de desarrollo o declarada como criterio. Test una sola vez, con un plan cerrado. |

---

## 2. El método: cómo se decidió todo

Es lo que más se pregunta y vale para todas las etapas.

### 2.1 Reglas antes de correr

- **Cada notebook empieza con las reglas,** escritas antes de ejecutar:
  - la pregunta;
  - las candidatas;
  - la métrica;
  - cómo se elige;
  - qué se hace si hay empate.
- **Si hay que cambiar una regla después de ver los datos,** se declara como desvío (sección 20) y nunca se reescribe lo anterior.
- **Por qué:** elegir la regla después de ver el resultado es una forma de sobreajuste.

### 2.2 La unidad es el sujeto

- **Los minutos de una persona no son independientes.** Comparten fisiología y electrodos, y hay personas con varias noches. Tratar 22.000 minutos como independientes daría intervalos falsamente angostos.
- **Bootstrap por sujeto.** Se remuestrean sujetos enteros con reposición y se recalcula la medida:
  - 2.000 remuestreos en desarrollo, salvo el acierto por registro durante la elección, que usa 500;
  - 10.000 remuestreos en test;
  - semilla 2026 en todo.
- **Intervalo:** los percentiles 2,5 y 97,5.
- **Truco de velocidad.** El área es la fracción de pares (minuto con apnea, minuto normal) bien ordenados. Se cuentan esos pares una sola vez entre cada par de sujetos, y cada remuestreo es un producto de matrices (`compare.py`).

### 2.3 Las dos medidas

- **Área, con todos los minutos juntos.**
  - **Por qué juntos y no por sujeto:** el detector usa un único umbral para todos, así que los valores de F tienen que ser comparables entre personas.
  - Un área por sujeto premiaría una feature que ordena bien dentro de cada noche aunque tenga niveles distintos en cada persona.
- **Acierto por registro.** Es el Spearman, entre registros, de dos fracciones de minutos con apnea: la estimada (minutos con F ≥ umbral) y la anotada. Mide si el detector ordena bien las noches según cuánta apnea tienen.
  - **Cuidado:** como usa rangos, **no ve un sesgo parejo**. Un detector que sobreestima todas las noches por igual puede tener un Spearman alto.
  - Por eso, aparte, se reportan Bland–Altman y las categorías.
- **Por qué dos medidas:** una mejora por minuto puede empeorar la estimación por noche, y al revés. Una etapa se adopta solo si no empeora ninguna de las dos.

### 2.4 Elegir entre candidatas: regla de no inferioridad

1. **Se orienta cada candidata** para que "más alto" signifique "más apnea": si su área es menor que 0,5, se invierte. El sentido se fija con los datos de elección.
2. **Grupo:** las candidatas no inferiores a la mejor en área. El límite inferior del intervalo de (candidata − mejor) tiene que ser ≥ −0,02.
3. **Dentro del grupo,** quedan las que empatan con la mejor en acierto por registro: el intervalo de la diferencia llega a 0.
4. **Entre esas,** gana la más simple según un orden fijado antes.

**Por qué esta regla reemplazó a la original.** La original declaraba empate si el intervalo de la diferencia incluía el 0. Pero no poder probar que una candidata es peor no quiere decir que sea igual de buena.
- **Qué hacía mal:** metía candidatas ruidosas (de intervalo ancho) y dejaba afuera a las parecidas (de intervalo angosto).
  - Eligió una candidata de 0,825 dejando afuera otras de 0,850.
  - En un grupo de la validación cruzada eligió el intervalo medio, con área 0,51.
- **Con validación cruzada:**

  | Regla | Área en los sujetos de afuera | Optimismo |
  |---|---|---|
  | Original | 0,795 | 0,064 |
  | No inferioridad | 0,850 | 0,021 |

- **Desvío:** se cambió después de la primera corrida y se declaró.

**δ = 0,02 [criterio].** Es una tolerancia metodológica, sin justificación clínica, y se declara en la discusión.

**Por qué la más simple:** entre candidatas equivalentes, menos grados de libertad quieren decir menos sobreajuste y una decisión más fácil de explicar.

### 2.5 Verificar una etapa obligatoria (4.2, 4.3, 4.4 y minutos malos)

- **Es una verificación, no una búsqueda.** Se compara la versión nueva contra la vigente sobre los **mismos minutos** (los 22.123 de E3a) y con los mismos remuestreos.
- **Se adopta si es no inferior en las dos medidas:** el límite inferior de cada diferencia tiene que ser ≥ −0,02. Si no, se reporta y no se adopta.
- **Los controles se reportan pero no deciden.** Por ejemplo, la coherencia con la respiración real.
- **Por qué así [criterio]:** la consigna obliga a implementar los temas, no a usarlos. No se agrega una complejidad que no demostró que no empeora.

### 2.6 Controles del optimismo

1. **Validación cruzada por sujetos.**
   - 5 grupos de sujetos, con semilla 2026. Los sujetos con y sin apnea se reparten por separado, para que cada grupo tenga de las dos clases.
   - Se elige con 4 grupos y se mide en el quinto.
   - Se reporta el optimismo (el área al elegir menos el área afuera) y si la elección se repite.
2. **Validación cruzada anidada** (notebook 12). Repite toda la cadena de elecciones. Es la estimación de desarrollo que se reporta.
3. **Test.** Una sola vez, con un plan cerrado.

---

## 3. Sujetos y partición (notebook 01, `src/split.py`)

**Pregunta.** ¿Hay registros de la misma persona o de la misma grabación? Importa porque, si una persona está en desarrollo y en test, test deja de ser gente nueva y el resultado se infla.

**Grabaciones duplicadas.**
- **Cómo se buscaron:** se compara el latido promedio de cada par de registros (de −250 a +400 ms). Los pares con correlación ≥ 0,99 se confirman buscando un tramo de 5 minutos de uno dentro del otro.
- **Qué salió:** tres pares son la misma grabación.
  - c05 = c06, ya documentado por PhysioNet;
  - x22 = x35 y x33 = x34, encontrados acá.
- **Cuál se excluye:** la que empieza después: c05 (80 s más tarde), x22 (40 s) y x33 (70 s). Quedan **67 registros**.
- **Dato lateral:** las etiquetas de una misma grabación difieren en 1 a 3 minutos de apnea. Es una medida del ruido de las anotaciones.

**Misma persona.** La base no identifica a las personas. Se unen los registros con perfil idéntico (edad, sexo, altura y peso) **o** que son la misma grabación, porque la tabla de perfiles tiene errores: a los duplicados les asigna perfiles distintos. Quedan **29 sujetos**.
- **¿Puede ser casualidad?** Hay 52 pares con perfil idéntico. Mezclando las columnas al azar aparecen como mucho 3, en 10.000 mezclas: p ≈ 0,0001.
- **¿Lo confirma el electrocardiograma?** Sí:
  - la correlación mediana entre latidos promedio es 0,94 dentro del sujeto y 0,74 entre sujetos;
  - 40 de 64 registros tienen su vecino más parecido en el mismo sujeto.
- **Lo que no cerraba era, sobre todo, polaridad invertida:** electrodos al revés en alguna noche. Invirtiendo el latido, la correlación sube a 0,62–0,97.
  - **Consecuencia para todo el pipeline:** ningún paso puede suponer que el pico R es positivo.
- **Ante la duda se agrupa [criterio].** Juntar de más solo cuesta balance; separar a una misma persona filtra información a test.

**Partición 70/30 por sujeto.** Tiene que cumplir cuatro condiciones:
1. sujetos enteros;
2. los sujetos con respiración real, en desarrollo (validan la respiración derivada y el filtro de Wiener);
3. cuotas exactas por categoría (30 % de cada una);
4. una fracción de minutos con apnea que difiera 2 puntos o menos entre conjuntos.

Hay 853 particiones válidas. Se eligió una al azar con semilla 2026, todas con la misma probabilidad. Las condiciones usan solo etiquetas, nunca features.

| | A | B | C | Registros | Sujetos |
|---|---|---|---|---|---|
| Desarrollo | 28 | 7 | 12 | 47 | 19 |
| Test | 12 | 3 | 5 | 20 | 10 |

**Categoría.**
- **Regla:** A tiene 100 minutos de apnea o más, B de 5 a 99 y C menos de 5. Reproduce la letra oficial de los 35 registros de aprendizaje.
- **Lo que no se puede verificar:** Penzel también pide una hora con el índice de apnea-hipopnea alto, y eso no se puede comprobar con minutos.

De test no se calculó nada, ni siquiera estadísticas de sus etiquetas, hasta abrirlo.

---

## 4. Adquisición (etapa 4.1, notebook 00)

**Pregunta.** ¿Qué dicen realmente los archivos? ¿Sirve el refinamiento del pico R, que se usaba sin verificar?

**Formato.**
- **Medido:** 100 Hz, ganancia de 200 unidades por mV (5 µV por paso) y conversor de **12 bits** guardado en formato de 16 (los valores van de −2048 a 2047). El esquema anterior decía 16 bits y se corrigió.
- **Citado, no medible:** las etiquetas las puso un experto; las marcas de QRS son automáticas; la derivación no se conoce (el archivo solo dice "ECG").

**Desarrollo.**
- **Duración:** de 6,8 a 9,6 h por noche.
- **Minutos:** 23.138 con etiqueta, el 39,8 % con apnea.
- **Por qué la exactitud sola engaña:** un detector que dice siempre "normal" acierta el 60 %. Por eso se usan el área y el índice de Youden.

**Minutos con apnea contra el índice de apnea-hipopnea.** Spearman 0,94 (intervalo de 0,84 a 0,97). La B es la categoría menos consistente con la clínica: sus registros van de un índice de 0,1 a 33.

**Saturación.**
- **Cuánto pasa:** 28 de 47 registros tocan alguna vez el tope del conversor (±10,2 mV), casi siempre con pocas muestras.
- **Qué es:** señal perdida, no QRS recortados. Lo saturado está en tramos clavados en el tope (el más largo, de 245 s), y solo el 0,03 % de los latidos tiene el QRS saturado.
- No se asocia con la apnea.

### Cuantización del pico R a 10 ms

**El problema.**
- A 100 Hz el pico cae en una grilla de 10 ms. Si el error es uniforme en ±5 ms, su desvío es 10/√12 = 2,9 ms.
- En la diferencia entre dos intervalos sucesivos entran tres picos, así que el desvío sube a √6 × 2,9 = 7,1 ms. Eso infla la variabilidad latido a latido.

**La corrección.**
1. El pico se busca a ±30 ms de la marca, con la polaridad del registro.
2. Se ajusta una **parábola por tres puntos:** el máximo y sus dos vecinos.
3. El vértice da el tiempo entre muestras. El corrimiento queda acotado a ±0,5 muestras.

**Prueba de dos fases** (cómo verificarla sin una referencia de mayor frecuencia de muestreo).
- **Cómo se arma:**
  1. La señal se baja a 50 Hz dos veces: con las muestras pares y con las impares.
  2. Antes de bajarla se aplica un pasabajos a 22,5 Hz: el mismo ancho de banda relativo que 45 Hz a 100 Hz.
  3. Así, cada latido queda medido en dos grillas corridas 10 ms.
- **La idea:** si el refinamiento funciona, las dos mediciones coinciden más.
- **Regla fijada antes:** se queda si el límite inferior de la reducción del desacuerdo es mayor que 0 (bootstrap por sujeto).
- **Resultado:** el desacuerdo baja de 10,0 a 2,5 ms, en los 19 sujetos (reducción de 7,5 ms, con intervalo de 7,4 a 7,6). **Se queda.**

**Efecto en el pipeline.**
- **Nulo en F y en la referencia:** F da 0,875 y la referencia 0,81, con y sin refinar. Las dos miran 0,01–0,05 Hz, y el error de cuantización cambia latido a latido: es ruido de alta frecuencia.
- **Sí importa en la raíz cuadrática media de las diferencias sucesivas:** sin refinar sube un 4 %, y un 13 % en los minutos de valores bajos.
- **La teoría lo confirma:** el exceso de varianza medido (46 ms²) coincide con el esperado (50 ms²).

---

## 5. E1: cómo medir la respiración desde el electrocardiograma (notebook 02)

**Por qué existe la respiración derivada.** Al respirar cambian la posición del corazón respecto de los electrodos y la impedancia del tórax. Eso modula la forma y el tamaño del QRS latido a latido (Moody et al., 1985).

**Pregunta.** ¿Qué forma de medir esa modulación reproduce mejor la respiración real?

**Candidatas (9).**
- **Medidas de forma del QRS (4):**
  - amplitud del pico, con parábola;
  - pico a pico;
  - área con signo;
  - puntaje en la primera componente principal de los latidos.
- **Preprocesamientos (2):** pasabanda de 0,5–40 Hz, o señal cruda restándole a cada latido la mediana del segmento PR.
- **Una candidata más, la deriva de línea de base:** la mediana del segmento PR (de −100 a −50 ms) sobre el electrocardiograma crudo. Solo tiene sentido sin pasabanda, porque el filtro elimina la deriva.

**Lo que queda fijo en todas.**
- **Centro y polaridad del QRS, medidos en cada registro.** Se arma el latido mediano a ±150 ms de la marca, y de él salen el desfase y el signo de la deflexión dominante. Hace falta porque `sqrs125` no marca el pico R y porque hay registros invertidos.
- Latidos con intervalos de 0,3 a 2 s.
- Ventana de ±60 ms.
- Remuestreo cúbico a 2 Hz.

**Métrica.** La coherencia entre la respiración derivada y la real.
- **Ponderada por el espectro de la respiración real:** así la banda la define la propia respiración, y no un rango elegido a mano.
- Solo frecuencias de 0,05 Hz o más, en ventanas de 2 minutos con segmentos de 32 s.
- Mediana por registro y promedio de los 3 canales.
- Bootstrap sobre los 8 registros, con 5.000 remuestreos.

**Piso de azar.** Si se desplaza la respiración derivada 10 minutos (en forma circular), la coherencia cae a 0,16.

**Resultado.**

| Candidata | Coherencia (intervalo) | Lectura |
|---|---|---|
| Área, con pasabanda | 0,531 (0,43 a 0,64) | La mejor en el 94 % de los remuestreos |
| Deriva de línea de base | 0,449 | **Empatada:** la diferencia va de −0,175 a +0,007 |
| Amplitud | 0,38 | Por debajo |
| Componentes principales | 0,19 | Casi azar |

- El pasabanda mejora a todas las medidas de forma.
- El ranking es idéntico con cada canal y con interpolación lineal.

**Decisión: pasan las dos a E3.**
- **Desvío declarado:** la regla decía desempatar por simplicidad, y ahí ganaba la deriva. En cambio, el empate se llevó a E3, que decide con la tarea real (detectar apnea) y con 19 sujetos en vez de 8.
- **Cómo se cerró:** en E3a, las 17 candidatas del grupo ganador usan el área. Queda el **área del QRS sobre el electrocardiograma filtrado**. Con el filtro final, la coherencia es 0,520.

---

## 6. E2: ¿se ve H1? (notebook 03)

**H1 original.** El acoplamiento se corre de la banda respiratoria a la lenta. Entonces, el cociente entre la coherencia lenta y la respiratoria sube con la apnea.

**Diseño fijado.** Es una prueba de hipótesis, así que la configuración no se elige con los datos.
- **Datos:** los registros A y B de desarrollo, 35 registros de 14 sujetos. Los C casi no tienen minutos con apnea.
- **Ventana de 512 s:** 1.024 muestras a 2 Hz, Welch con 3 segmentos de 256 s, resolución de 0,004 Hz.
- **Dos pares de bandas, con el mismo peso y corregidos por Holm:**
  - el acoplamiento cardiopulmonar publicado (Thomas et al., 2005): 0,01–0,1 y 0,1–0,4 Hz;
  - el esquema anterior: 0,01–0,15 y 0,15–0,4 Hz.
- **Por registro:** la mediana del cociente en los minutos con apnea menos la mediana en los minutos normales. Solo minutos con 20 % o menos de intervalos corregidos, y al menos 5 minutos de cada clase.
- **Por sujeto:** el promedio de sus registros.
- **Prueba:** Wilcoxon de rangos con signo, de dos colas, sobre una diferencia por sujeto. El tamaño del efecto es la correlación rango-biserial, y la mediana lleva intervalo por bootstrap.
- **Por qué Wilcoxon directo y no "Shapiro, después t o Wilcoxon" [criterio]:** con 14 sujetos el Shapiro tiene poca potencia, y elegir la prueba según una prueba previa distorsiona el error de tipo I.
- **Regla:** H1 se sostiene si al menos una configuración da p de Holm < 0,05 a favor y ninguna da un resultado significativo en contra.

**Resultado.**

| Configuración | Sujetos a favor | Rango-biserial | p de Holm |
|---|---|---|---|
| Acoplamiento publicado | 11 de 14 | 0,81 | 0,011 |
| Esquema anterior | 10 de 14 | 0,66 | 0,03 |

- **El mecanismo no era el propuesto:**
  - la coherencia lenta **sube** (11 y 12 de 14 sujetos; p de Holm 0,03);
  - la respiratoria **no baja** (8 de 14; p de Holm 1).
- **Por eso H1 se reformula:** con la apnea *aparece* un acoplamiento lento, y el respiratorio no se pierde.
- **Robusto.** Se probaron 36 configuraciones (3 ventanas × 3 pares de bandas × 4 formas del cociente):
  - todas van en la dirección de H1;
  - 13 son significativas después de Holm, y ninguna en contra;
  - la banda de apnea (0,01–0,05 Hz) da efectos más grandes. Anticipa E3, pero no se usa para elegir.
- **Sin la exclusión por calidad,** el resultado es el mismo.
- **Con la respiración real en lugar de la derivada,** el efecto aparece en los 5 registros con apnea y casi siempre es más grande. Es fisiológico, y la respiración derivada lo capta atenuado.
- **Mapas nocturnos** (a03 y c02, elegidos por una regla fijada antes):
  - en a03 hay franjas de coherencia cerca de 0,02 Hz durante las apneas;
  - en c02 domina el acoplamiento respiratorio, cerca de 0,2 Hz.

**Para la defensa.**
- La reformulación se hizo después de ver los datos, así que su respaldo en desarrollo tiene un componente exploratorio. Se reconoce en la discusión.
- En test, H1 **no se replicó**.

---

## 7. E3a y E4: la feature F y la referencia (notebooks 04 y 05)

**Preguntas.**
- **E3a:** ¿cómo convertir el acoplamiento en un número por minuto que separe los minutos con y sin apnea?
- **E4:** ¿cuál es la mejor feature de variabilidad cardíaca medida con la misma vara? Esa es la referencia de H2.

### Candidatas de acoplamiento: 1.134

Salen de combinar 3 respiraciones derivadas × 6 ventanas × 3 estimadores × 3 pares de bandas × 7 formas:

| Elemento | Opciones |
|---|---|
| Respiración derivada | área, deriva, combinada |
| Ventana | 3, 4, 5, 6, 7 y 8,5 min |
| Estimador | **Welch con 3 segmentos:** de media ventana, con 50 % de solapamiento. **Welch con 7:** de un cuarto de ventana. **Multitaper:** producto tiempo-ancho de banda 2, con 3 ventanas de Slepian. |
| Bandas (lenta / respiratoria) | **Publicado:** 0,01–0,1 / 0,1–0,4 Hz. **Esquema anterior:** 0,01–0,15 / 0,15–0,4 Hz. **Apnea:** 0,01–0,05 / 0,15–0,4 Hz. |
| Formas | coherencia lenta sola; **potencia cruzada lenta sola (log)**; diferencia de coherencias; log-cociente de coherencias; coherencia × potencia cruzada; "producto" (cociente lenta/respiratoria de coherencia × potencia, como el acoplamiento publicado); coherencia ponderada por la potencia cruzada |

**Cómo se diferencian los estimadores.** Welch promedia segmentos: baja la varianza a costa de resolución. El multitaper promedia varias ventanas ortogonales sobre toda la ventana.

### Candidatas de variabilidad cardíaca: 60

Salen de combinar 6 ventanas × 10 features:
- **En el tiempo:**
  - intervalo medio;
  - desvío estándar de los intervalos;
  - raíz cuadrática media de las diferencias sucesivas;
  - porcentaje de diferencias sucesivas mayores a 50 ms.
- **Con Lomb, la potencia en cada banda:**
  - apnea (0,01–0,05 Hz);
  - muy baja frecuencia (0,01–0,04 Hz);
  - baja (0,04–0,15 Hz);
  - alta (0,15–0,40 Hz);
  - total (0,01–0,40 Hz);
  - y el cociente entre baja y alta.

### Condiciones de la comparación

- **Minutos:** 22.123, con etiqueta, con 20 % o menos de intervalos corregidos y con **todas** las candidatas calculables. La ventana de 8,5 minutos recorta los bordes de la noche. Todas las candidatas se comparan sobre los mismos minutos.
- **Orden de simplicidad [criterio, fijado antes]:**
  1. estimador: Welch 3 < Welch 7 < multitaper;
  2. forma: en el orden de la lista;
  3. ventana: la más corta;
  4. bandas: publicado < anterior < apnea;
  5. respiración derivada: deriva < área < combinada.
- **Comparación fija:** la configuración publicada que usó E2.

### Resultado

- **Regla.** La validación cruzada no distingue la no inferioridad de "la de mayor área" (0,850 y 0,849 afuera). Por la regla fijada (una diferencia menor que 0,01 cuenta como empate y gana la no inferioridad, que da una configuración más simple), se usa **no inferioridad**.
- **F elegida en E3a:** área del QRS, 180 s, Welch 3, banda de apnea, **potencia cruzada sola**. Área de 0,871 (intervalo de 0,81 a 0,92).
- **Estable.** Los 5 grupos de la validación cruzada eligieron exactamente la misma configuración. Afuera rinde 0,85 (de 0,69 a 0,96), contra 0,60 de la configuración publicada.
- **La coherencia no aporta:**

  | Forma | Área |
  |---|---|
  | Potencia cruzada sola | 0,871 |
  | Coherencia × potencia | 0,855 (significativamente peor) |
  | Coherencia sola | 0,629 |

  El cociente de coherencias queda descartado como detector.
- **Referencia (E4).** Gana la potencia de muy baja frecuencia de la serie RR, con Lomb y 180 s: 0,810.
  - Es casi igual a la banda de apnea (0,812). El cociente entre baja y alta da 0,73.
  - Afuera rinde 0,731: es más optimista que F.
- **Vista previa de H2:** 0,871 contra 0,810. La diferencia (0,061; de −0,009 a 0,137) no se distingue con 19 sujetos.

### Control (notebook 05): ¿qué parte de F detecta?

En cada frecuencia, |potencia cruzada| = √coherencia × √(potencia del RR × potencia de la respiración derivada).

| Variante | Área |
|---|---|
| F | 0,871 |
| Las dos potencias sin coherencia (media geométrica) | 0,874: la √coherencia que F tiene adentro no suma |
| RR solo | 0,817 |
| Respiración derivada sola | 0,822 |

Juntar las dos señales sube la estimación (+0,056), pero el intervalo incluye 0 (de −0,014 a +0,131).

**Lectura.** F detecta **cuánto oscilan juntas** las dos señales en la banda de apnea, no qué tan sincronizadas están. El aporte original pasa a ser **sumar al RR la respiración derivada en la banda del ciclo de apnea**.

### Por qué cada elección tiene sentido

- **La banda de 0,01–0,05 Hz.** Un ciclo de apnea (un evento de 10 s o más, seguido de la recuperación) dura de 20 a 100 s, o sea, de 0,01 a 0,05 Hz. En cada ciclo el ritmo cardíaco baja durante el evento y sube al retomar la respiración, y el esfuerzo respiratorio cambia el QRS con el mismo ritmo.
- **El logaritmo.** Es una transformación creciente, así que no cambia el área ni el umbral. Sirve para llevar una potencia que varía en órdenes de magnitud a una escala manejable, y para que las formas compuestas sean sumas. Se toma log(máx(potencia, 10⁻¹²)) para evitar el log de 0.
- **Welch para F y Lomb para la referencia.** El espectro cruzado necesita las dos señales en la misma grilla uniforme: por eso se remuestrean a 2 Hz y se usa Welch. La variabilidad cardíaca sola se puede estimar sobre los latidos irregulares, sin interpolar: por eso Lomb, que además es tema obligatorio.

---

## 8. E3b: normalizar, suavizar y la ventana final (notebook 06)

**Candidatas.**
- **Base:**
  - las 17 del grupo de F (todas potencia cruzada sola con área);
  - el grupo de la referencia;
  - dos controles: RR solo y respiración derivada sola.
- **Nueve posprocesados para cada una:** normalización × suavizado.

  | Normalización por noche | Suavizado |
  |---|---|
  | ninguna | ninguno |
  | línea de base: restar el percentil 10 de la noche | mediana móvil de 3 minutos |
  | z-score de la noche | mediana móvil de 5 minutos |

- **Cómo se aplican:** sobre la noche completa y sin etiquetas. Después se evalúan los mismos minutos, con la misma regla de elección.

**Normalizar empeora en todas las familias.**
- **El área de F cae:** de 0,876 a 0,68 con línea de base y a 0,73 con z-score.
- **La línea de base arruina el acierto por registro:** de 0,81 a 0,13.
- **Por qué:** normalizar iguala las noches y borra justamente la diferencia de nivel entre una noche con mucha apnea y otra sin apnea. Con un umbral común, esa diferencia es información.

**Suavizar cambia el área en menos de 0,005.** Por simplicidad, queda sin suavizar.

**F final:** área del QRS, **240 s**, Welch 3, banda de apnea, potencia cruzada sola, sin posprocesar. Área de 0,876 (de 0,81 a 0,93).
- **Qué cambió respecto de E3a:** solo la ventana, de 3 a 4 minutos.
  - **Quién la eligió:** la misma regla fijada antes de correr, aplicada a las 153 combinaciones. No fue una decisión a mano.
  - **Qué se sabe del paso:** como la ventana más corta es la más simple, la de 180 s habría ganado si llegaba al final. Quedó afuera en alguno de los dos filtros de la regla (área o acierto por registro), pero el notebook no guarda en cuál.
  - **Confirmación:** en la validación anidada (notebook 12), los cinco grupos volvieron a elegir 240 s sin ver a sus sujetos de afuera, y con todos los sujetos también.
  - **Cuánto importa:** poco, porque las dos rinden prácticamente igual (0,876 contra 0,871).
- **Una explicación coherente, aunque no fue lo que decidió:** con 240 s cada segmento de Welch dura 120 s, así que la resolución es 1/120 = 0,008 Hz, más fina que el borde de 0,01 Hz de la banda. Con 180 s sería de 0,011 Hz.

**Referencia final:** potencia de muy baja frecuencia con Lomb, 180 s, sin posprocesar.

**Acierto por registro.**
- **Resultados:**

  | Feature | Acierto por registro | Intervalo |
  |---|---|---|
  | F | 0,81 | 0,56 a 0,94 |
  | Referencia | 0,42 | −0,09 a 0,79 |
  | Respiración derivada sola | 0,74 | — |
  | RR solo | 0,39 | — |

- **La diferencia entre F y la referencia fue significativa en desarrollo.**
- **Lectura:** era el aporte más claro de la respiración derivada: estimar **cuánta** apnea tiene cada noche.

**¿Era un efecto de escala entre pacientes?** El RR solo no es no inferior a F (−0,058; de −0,133 a +0,011). No se puede atribuir la ventaja a la escala, pero tampoco queda confirmada.

**Validación cruzada.** Los 5 grupos eligieron "sin posprocesar". Afuera, F rinde 0,853 y la referencia 0,807.

**Vista previa de H2.**
- **Números:** 0,876 contra 0,810. La diferencia es de 0,066 (de −0,004 a +0,142), y F es mejor en el 96,5 % de los remuestreos.
- **Lectura:** está cerca, pero **el intervalo incluye el 0**. Es clave para entender test.

---

## 9. Filtro convencional (etapa 4.2, notebook 07)

**Qué hace.** Saca la deriva lenta de la línea de base (respiración, movimiento, contacto de los electrodos) y el ruido de alta frecuencia, sin deformar el QRS, que es de donde salen los picos R y el área.

**Especificación sacada de los datos, sin etiquetas.**
- **Borde inferior de la banda de paso:** el ritmo cardíaco más bajo de desarrollo (percentil 1 del ritmo instantáneo): **0,77 Hz**, o sea, 46 latidos por minuto.
- **Borde superior:** la frecuencia por debajo de la cual queda el 99 % de la energía del latido mediano (percentil 95 entre registros): **41,8 Hz**.
- **Exigencias, con el filtrado ida y vuelta [criterio: los valores de 1 dB y 20 dB]:**
  - 1 dB de atenuación o menos entre 0,77 y 41,8 Hz;
  - 20 dB o más a 0,1 Hz, donde está la deriva.

**Candidatos y regla.**
- **Candidatos:** Butterworth con corte bajo de 0,3, 0,5 o 0,7 Hz, corte alto de 35, 40 o 45 Hz y orden de 1 a 6.
- **Regla:**
  - si el filtro vigente (0,5–40 Hz, orden 2) cumple, se queda;
  - si no, gana el de menor orden que cumpla y, a igual orden, el de cortes más cercanos a los anteriores.

**Elección.**
- **El vigente no cumplía:** atenuaba 10,4 dB a 41,8 Hz y 1,4 dB a 0,77 Hz. Ningún candidato con corte alto de 35 o 40 Hz cumple.
- **Elegido: 0,5–45 Hz, orden 3.** Atenúa 0,4 dB a 41,8 Hz, 0,6 dB a 0,77 Hz y 84 dB a 0,1 Hz.

**Por qué este diseño.**
- **Butterworth [criterio]:** tiene la banda de paso máximamente plana, sin ondulación, así que no altera la amplitud del QRS dentro de la banda.
- **Ida y vuelta (`sosfiltfilt`):**
  - **Ventaja:** la fase queda en cero, así que no corre el pico R ni deforma el QRS.
  - **Consecuencia:** la ganancia efectiva es |H|² (en dB, el doble). Por eso la especificación se mide con la ida y vuelta.
  - **Costo:** no es causal, es procesamiento fuera de línea.
  - **Implementación:** en secciones de segundo orden, por estabilidad numérica.

**Verificación.**

| | Antes | Después | Diferencia (intervalo) |
|---|---|---|---|
| Área de F | 0,876 | 0,875 | −0,001 |
| Acierto por registro | 0,813 | 0,810 | −0,003 (−0,018 a +0,004) |

- **No inferior en las dos medidas: se adopta.**
- **Control:** la coherencia con la respiración real pasa de 0,531 a 0,520, casi todo por c01.
- **No es una mejora de rendimiento:** es corregir el filtro para que respete la banda del QRS medida en los datos.
- **Qué pasa con los notebooks 02 a 06:** quedaron con el filtro anterior. Sus conclusiones no cambian, porque F casi no se mueve.

---

## 10. Detección de QRS propia (etapa 4.3, notebook 08)

**Pregunta.** ¿Un detector propio puede reemplazar a las marcas de la base, que son automáticas y no están auditadas?

**Pan-Tompkins adaptado a 100 Hz.** Usa los valores clásicos de Pan y Tompkins (1985), expresados en segundos para que no dependan de la frecuencia de muestreo. No se ajustaron con datos.

| Paso | Valor | Para qué |
|---|---|---|
| Pasabanda | 5–15 Hz, orden 2, ida y vuelta | Deja la banda donde se concentra el QRS y saca las ondas P y T y la deriva |
| Derivada | 5 puntos, simétrica | Resalta las pendientes empinadas del QRS |
| Cuadrado | — | Todo queda positivo, así que no importa la polaridad, y realza lo grande |
| Integración | Ventana de 150 ms centrada | Da un solo pulso por QRS, del ancho típico del complejo |
| Período refractario | 200 ms | Evita detectar dos veces el mismo latido |
| Onda T | A menos de 360 ms del QRS anterior y con menos de la mitad de su pendiente (medida en ±75 ms) | Descarta las ondas T empinadas |
| Umbral | Ruido + 0,25 × (señal − ruido), con niveles actualizados con pesos 0,125 / 0,875 | Se adapta a los cambios de amplitud |
| Búsqueda hacia atrás | Si el hueco supera 1,66 intervalos medios (los últimos 8), recupera el pico de ruido más alto si pasa la mitad del umbral | Recupera latidos perdidos |
| Aprendizaje inicial | 2 s: señal = máximo/3, ruido = media/2 | Arranca los umbrales |
| Ubicación del R | El extremo con la polaridad del registro, a ±80 ms | Encuentra el pico real |

- **Sin retardo:** todas las etapas lineales están centradas.
- **Cambio declarado.** En una corrida exploratoria el detector quedaba ciego en a03 (sensibilidad 0,51) y en a17 (0,78), porque el umbral quedaba por encima de los QRS. Se agregó que **los umbrales se vuelvan a aprender si la búsqueda hacia atrás falla**.

**Validación contra las marcas de la base** (tolerancia de 100 ms; es descriptiva, no decide).
- Con todos los latidos: sensibilidad 0,996 y valor predictivo positivo 0,972.
- El peor registro es x17: 0,92 y 0,59.

**Revisión manual de 50 discrepancias,** sorteadas antes de mirarlas (semilla 2026).

| Clasificación | Casos |
|---|---|
| Errores del detector | 21 |
| Errores de las marcas | 18 |
| Dudosas | 11 |

- **Conclusión:** una discrepancia no es necesariamente un error del detector.
- **Errores del detector:**
  - unas 13 detecciones de más al final de ondas T empinadas, en x17 y x12 (queda una prueba marcada como falla esperada);
  - 5 oscilaciones al inicio del registro, donde el detector aprende los umbrales de un artefacto;
  - 2 casos aislados.
- **Errores de las marcas:** sobre todo QRS claros sin marca, a menudo negativos o bifásicos.

**Verificación con F.**

| Medida | Diferencia | Intervalo | ¿No inferior? |
|---|---|---|---|
| Área | +0,0038 | −0,0004 a +0,0079 | Sí |
| Acierto por registro | −0,024 | **−0,097** a +0,019 | No |

**Decisión: se mantienen las marcas de la base.**
- **Control con respiración real:** la coherencia pasa de 0,521 a 0,535 y sube en 6 de los 8 registros (descriptivo).
- **Matiz:** no cumplir la no inferioridad **no demuestra** que el detector sea peor. Dice que los datos no descartan una pérdida mayor que 0,02.
- **Consecuencia:** el detector final no es un sistema autónomo, porque usa las marcas de la base.

---

## 11. Recorte en realizaciones y filtro de Wiener (etapa 4.4, notebook 09)

**Para qué.** Es el filtro óptimo, en el sentido del menor error cuadrático medio, para limpiar el electrocardiograma y medir mejor el área del QRS. Cubre dos temas obligatorios: recorte en realizaciones y filtros óptimos.

**Cómo se hace, en cada registro.**
1. **Realizaciones.** Se recorta cada latido de −250 a +400 ms alrededor del pico R: son 66 muestras, que cubren la onda P, el QRS y la onda T.
   - Como el R está refinado entre muestras, el recorte se alinea interpolando.
   - Se descartan los latidos incompletos.
2. **Señal.** Es el promedio de las realizaciones (la plantilla). Lo que se repite queda, y el ruido no correlacionado con el latido baja con la raíz de la cantidad de latidos.
3. **Ruido.** Es cada latido menos la plantilla.
   - **Advertencia:** el residuo también incluye variación real entre latidos, como la respiratoria.
4. **Densidades espectrales.** Se calculan con un periodograma con ventana de Hann, rellenando a 256 puntos:
   - S_s, de la plantilla;
   - S_n, el promedio de los periodogramas de los residuos.
5. **Ganancia.** H(f) = S_s / (S_s + S_n). Vale cerca de 1 donde domina el latido y cerca de 0 donde domina el ruido.
6. **Filtro aplicable.** Se diseña un filtro de respuesta finita al impulso de **129 coeficientes simétricos** (`firwin2`) que aproxima H(f).
   - **Simétrico:** la fase es lineal y se compensa el retardo, así que no corre el R.
   - **Bordes:** se extienden por reflexión.
   - **Largo:** 129 coeficientes son 1,28 s a 100 Hz **[criterio]**.
7. **Se aplica al electrocardiograma continuo.** La plantilla solo sirve para diseñar el filtro; nunca reemplaza a los latidos.

**Por qué no borra la respiración derivada.**
- **El argumento:** un filtro lineal e invariante en el tiempo aplica la misma operación a todos los latidos. Si un latido es la plantilla multiplicada por un factor aₖ, después de filtrar sigue siendo la plantilla filtrada multiplicada por aₖ. La relación de amplitudes entre latidos se conserva.
- **Lo que sí la borraría, y no se hace:** reemplazar los latidos por el promedio, o adaptar el filtro latido a latido.
- **Matiz:** si los latidos cambian de forma, y no solo de escala, esa diferencia se atenúa donde H es baja.

**Resultado.**
- **En a01:** la respiración derivada de antes y de después correlaciona 0,9994. Cambia la escala, no la evolución.
- **Verificación:**

  | Medida | Diferencia | Intervalo | ¿No inferior? |
  |---|---|---|---|
  | Área | +0,0041 | −0,0093 a +0,0167 | Sí |
  | Acierto por registro | −0,0471 | **−0,1649** a +0,0380 | No |

- **Decisión: no se adopta.**
- **Control con respiración real:** la coherencia pasa de 0,5205 a 0,5343; sube en 7 de los 8 registros y baja en c02 (descriptivo).

**Hipótesis de por qué no ayudó** (no se midió). El residuo que se trata como ruido contiene la modulación respiratoria entre latidos, que es justamente lo que necesita F.

---

## 12. Limpieza de la serie RR y minutos malos (etapa 4.5, notebook 10)

**Reglas de la serie RR.** Vienen del esquema anterior y **no se verificaron con datos**: queda como limitación.
- **Inválido:** un intervalo fuera de 0,3–2 s (de 30 a 200 latidos por minuto).
- **Ectópico:** un intervalo que se aparta más del 20 % de la mediana de sus 11 vecinos válidos. Un latido prematuro deja un intervalo corto y otro largo.
- **Corrección:** los inválidos y los ectópicos se reemplazan por interpolación lineal.
- **Exclusión:** se descarta el minuto que tiene más del 20 % de sus intervalos corregidos.
- **Para la respiración derivada:** solo se usan latidos con intervalos de 0,3–2 s a los dos lados.

**Medido en la 4.1 sobre la regla del 20 %.**
- Excluye una mediana del 0,2 % de los minutos por registro, pero a02 pierde el 41 % y x17 el 27 %.
- Saca algo más de minutos con apnea que normales (3,5 % contra 2,3 %), sin diferencia significativa.
- No detecta la señal perdida.

**Pregunta del notebook 10.** ¿Hay que excluir además los minutos cuya ventana de 240 s tiene señal perdida? Se considera señal perdida un tramo plano o clavado en el tope durante 1 s o más, medido sobre el electrocardiograma digital.
- **Cuánto sacaría:** 160 minutos más (0,72 %): el 0,68 % de los normales y el 0,78 % de los minutos con apnea. La diferencia es de 0,10 puntos (de −0,47 a +0,68): no sesga entre clases.
- **Efecto:**

  | Medida | Sin la regla | Con la regla | Diferencia |
  |---|---|---|---|
  | Área | 0,8733 | 0,8771 | Mejora |
  | Acierto por registro | 0,8134 | 0,8119 | −0,0015, con límite inferior **−0,0209** |

- **Decisión:** el límite queda apenas debajo de −0,02, así que no cumple. **Se mantiene la regla vigente.**

**Minutos del pipeline final: 22.275.** Tienen etiqueta, 20 % o menos de intervalos corregidos, y F y referencia calculables. Son más que los 22.123 de E3a, que exigían todas las candidatas.

**Limitación.** Algunos minutos con señal perdida se siguen evaluando. En el notebook 14 aparecen casi siempre como falsos positivos.

---

## 13. Umbral (notebook 11)

**Índice de Youden.** J = sensibilidad + especificidad − 1. Se elige el umbral que lo maximiza, que es el punto de la curva de sensibilidad contra 1 − especificidad más alejado de la diagonal del azar. Un minuto es apnea si F ≥ umbral.

**Por qué Youden.** Lo pidió la docente **[criterio de la devolución, contrastado con datos]**. Además:
- pesa igual la sensibilidad y la especificidad;
- **no depende de la prevalencia:** con un 60 % de minutos normales, maximizar la exactitud empujaría a decir "normal".

**Alternativas evaluadas dejando sujetos afuera.** Se usaron 5 grupos, y cada umbral se ajustó solo con los sujetos de entrenamiento:
- la mediana de los umbrales de Youden de 2.000 remuestreos de sujetos;
- el umbral que iguala la proporción de apnea estimada con la real;
- combinar F y la referencia con "y" o con "o".

**Ninguna mejoró**, así que queda Youden.

**Umbrales finales,** ajustados con todo desarrollo (22.275 minutos) y guardados en `docs/umbrales_desarrollo.json`:
- F ≥ −6,948641…
- referencia ≥ 0,001258477…

**Con sujetos de afuera:**

| Medida | Valor |
|---|---|
| Sensibilidad | 0,839 |
| Especificidad | 0,749 |
| Exactitud balanceada | 0,794 |
| Acierto por registro | 0,807 |

**Limitación.** El detector estima un 48,5 % de minutos con apnea, contra el 39,8 % anotado: **sobreestima**. Youden equilibra la sensibilidad y la especificidad, no la cantidad total.

---

## 14. Validación cruzada anidada (notebook 12)

**Por qué.** Los números de desarrollo son optimistas: F, su posprocesado y su umbral se eligieron con esos mismos sujetos.
- **Qué hace:** repite **toda** la elección con solo 4 de los 5 grupos (la feature con la regla de E3a, el posprocesado con la de E3b y el umbral de Youden) y evalúa en el quinto.
- **Por qué hacía falta:** es la condición 3 para abrir test.

**Cómo.**
- **Candidatas:** las 1.134 + 60, recalculadas con el pipeline vigente.
- **Bootstrap:** 1.000 remuestreos para el área y 300 para el acierto por registro.
- **El área se calcula por grupo** y se promedia, porque cada grupo puede elegir otra feature y sus puntajes no se mezclan.

**Resultado: la estimación honesta que se reporta.**

| Medida | Valor |
|---|---|
| Área | 0,851 (intervalo de 0,760 a 0,916; por grupo, de 0,689 a 0,964) |
| Sensibilidad | 0,839 |
| Especificidad | 0,748 |
| Acierto por registro | 0,807 (de 0,547 a 0,936) |
| Optimismo | 0,024 |

**F es estable.** Los 5 grupos eligieron la misma F, con umbrales de −6,96 a −6,91. Con todos los sujetos sale exactamente la F congelada.

**La referencia es inestable y optimista.**
- 4 grupos eligieron la potencia en la banda de apnea con 180 s, y uno, el cociente entre baja y alta con 240 s.
- Afuera rinde 0,729, contra 0,810 con todos los sujetos.

**F contra la referencia, afuera** (descriptivo):
- área: +0,122 (de 0,022 a 0,193);
- acierto por registro: +0,573 (de 0,217 a 0,929).

**Por noche.**
- **Sesgo:** +5,0 minutos de apnea por hora, con límites de acuerdo de −21 a +31.
- **Categoría correcta:** en el 57 % de las noches.
- **Las 12 noches de control quedan como B.** F marca como apnea entre el 5 % y el 16 % de sus minutos (de 22 a 70), y para ser C hay que tener menos de 5. Con una especificidad de alrededor de 0,89, ese corte es inalcanzable para un detector minuto a minuto.

**Calibración por noche (candidata).** Es una recta, ajustada con las noches de entrenamiento, que lleva la fracción estimada a la real.
- **Efecto:** baja el error de 10,6 a 9,8 minutos por hora.
- **Decisión:** el intervalo de la diferencia (de −2,7 a +1,2) incluye 0, así que **no se adopta**.

**Control contra filtraciones.** Se mezclaron al azar las etiquetas de los sujetos de afuera del grupo 1 y todo lo elegido dio idéntico: la elección no ve a los sujetos de afuera.

**Qué esperar de test.**
- **Simulación:** se sortearon 10 de los 19 sujetos de desarrollo. H2 se confirmaría por acierto por registro en el 62 al 79 % de los sorteos.
- **Lectura:** aunque F sea mejor, hay entre un 20 % y un 40 % de chances de no verlo con 10 sujetos.

**Optimismo residual declarado.**
- La banda de apnea entró después de verla fuerte en E2.
- La forma "potencia sola" y la regla de no inferioridad se agregaron después de la primera corrida.
- Las etapas 4.1 a 4.4 se decidieron con todos los sujetos.

---

## 15. Categoría de cada noche: A contra el resto (notebook 13)

**Problema.** Con la regla de la base (A con 100 minutos estimados o más, B de 5 a 99, C menos de 5), las noches de control salen como B por la sobreestimación.

**Decisión de criterio, declarada: dos clases, A contra el resto.**
- **Por qué no B:** tiene pocas noches (7 en desarrollo y 3 en test) y es inconsistente con el índice de apnea-hipopnea.
- **Por qué A:** es consistente (27 de 28 noches son moderadas o graves) y responde la pregunta clínica: ¿hay apnea relevante?
- **Cuándo se decidió:** **después** de ver la matriz del notebook 12. Una versión de tres clases con dos cortes se descartó sin mirar sus resultados.

**Candidata.** Un corte calibrado sobre el porcentaje de minutos marcados como apnea, elegido con las noches de entrenamiento. Se adopta si mejora con el intervalo completo por encima de 0.

**Resultado.**

| Regla | Noches bien clasificadas |
|---|---|
| Regla de la base, en dos clases | **83 %** (39 de 47) |
| Corte calibrado | 77 % (−0,064; de −0,196 a +0,042) |

- **El corte calibrado no se adopta.** Además, varía del 21 % al 48 % entre grupos.
- **Con la regla de la base:**
  - 25 de las 27 noches A salen como A;
  - las 12 de control salen como "resto";
  - 6 de las 8 B salen como A.

**En test.** Se reporta la matriz A/B/C, como estaba fijado, y se agrega "A contra el resto" con la regla de la base. Es el desvío 9.3 y no agrega parámetros.

---

## 16. Diagnóstico de errores (notebook 14; descriptivo)

**Falsos positivos: 3.377.**
- **Dónde caen:** el 53 % en noches A, donde se marca el 37,5 % de los minutos normales.
- **Cerca de los episodios:** el 27 % cae a 1 o 2 minutos de una apnea. La ventana de 240 s abarca ±2 minutos, y alrededor de los episodios persiste la oscilación lenta.
- **Calidad:** con algún intervalo corregido en el minuto, la tasa sube del 22 % al 36–37 %.
- **Señal perdida:** los minutos con señal perdida en la ventana son falsos positivos el 96 % de las veces, porque el hueco interpolado parece una oscilación lenta. Pero son solo el 2,6 % del total.

**Falsos negativos: 1.428.**
- **No son episodios cortos ni bordes:** el 92 % está dentro de episodios de más de 10 minutos.
- **Se concentran en dos sujetos:** S09 detecta el 39 % de su apnea y S02, el 26 %. En esas personas F queda por debajo del umbral común.

**Variación entre grupos.**
- **El caso:** el grupo 4 (0,689) junta a S02 con un control.
- **Por qué baja:** dentro de cada sujeto el área es razonable (de 0,78 a 0,88), pero F tiene niveles distintos en cada persona.

**Lejos de los bordes de los episodios,** la especificidad sube de 0,748 a 0,796.

**Decisión en dos niveles.** Sería clasificar primero la noche y usar un umbral más exigente en las que no son A.
- **Techo realista:** la especificidad pasaría de 0,748 a 0,804 y el sesgo, de +5,0 a +2,8.
- **No se prueba:**
  - la ganancia es chica;
  - cambiaría las decisiones por minuto de una medida principal;
  - agregaría un parámetro elegido después de mirar los datos.

---

## 17. Congelamiento y test (plan de test y notebook 99)

### Plan cerrado antes de abrir

Se commiteó antes de calcular nada sobre test.

- **Condiciones para abrir:**
  - las etapas obligatorias cerradas como verificación;
  - los umbrales fijados;
  - la validación anidada hecha;
  - un commit con la etiqueta `congelado-test`.
- **Minutos:** los mismos criterios que en desarrollo. Como análisis de sensibilidad se usan todos los minutos con etiqueta, y los inválidos toman la decisión del minuto válido más cercano.
- **H2, con dos medidas principales del mismo peso:**
  - **M1:** el área con todos los minutos;
  - **M2:** el acierto por registro, sobre 20 registros.
- **Procedimiento para cada medida:**
  1. diferencia = F − referencia;
  2. bootstrap de los 10 sujetos, con 10.000 remuestreos;
  3. intervalo por percentiles;
  4. p bilateral = 2 × mín(fracción ≤ 0, fracción ≥ 0);
  5. corrección de Holm sobre los dos p.
- **Regla de decisión:**
  - se confirma si el p de Holm es < 0,05 a favor de F;
  - se rechaza si es < 0,05 a favor de la referencia;
  - si no, "no muestra diferencia", que no quiere decir que sean iguales.
  - Las conclusiones se dan por medida, sin combinarlas.
- **Por qué Holm:** controla la probabilidad de al menos un falso positivo entre las dos pruebas, y es menos conservador que Bonferroni.
- **Resultados secundarios (descriptivos):**
  - sensibilidad, especificidad y exactitud;
  - minutos de apnea por hora, con Bland–Altman;
  - la matriz A/B/C y "A contra el resto";
  - el Spearman con el índice de apnea-hipopnea (desvío 9.2);
  - la réplica de H1.
- **Por qué el índice de apnea-hipopnea no es una medida principal:**
  - correlaciona 0,94 con la fracción de minutos, así que repetiría M2;
  - el detector cuenta minutos, y el índice cuenta eventos por hora de sueño.
- **Después de abrir no se cambia nada.** Si apareciera un error de código, se reportarían las dos corridas.

### Resultados (corrida única, 9/11/2026)

| | F | Referencia | Diferencia (intervalo) | p de Holm |
|---|---|---|---|---|
| M1: área | 0,785 | 0,793 | −0,007 (−0,162 a +0,112) | 1 |
| M2: acierto por registro | 0,634 | 0,613 | +0,021 (−0,543 a +0,514) | 1 |

**H2 no se confirma ni se rechaza.** Los intervalos son enormes: son compatibles con una ventaja clara de cualquiera de las dos.

**Minutos.** Se evaluaron 8.556 de los 9.754 minutos con etiqueta. El 12,3 % que quedó afuera es casi todo de c04 (74 %) y x29 (86 %), por la regla del 20 %.

**Secundarios.**

| Medida | F | Referencia |
|---|---|---|
| Sensibilidad | 0,790 | 0,735 |
| Especificidad | 0,642 | 0,686 |
| Exactitud | 0,706 | 0,707 |
| Sesgo (minutos de apnea por hora) | +7,3 (límites de −27,9 a +42,5) | — |
| Categoría A/B/C correcta | 45 % | 60 % |
| A contra el resto correcta | 70 % | 70 % |
| Spearman con el índice de apnea-hipopnea | 0,70 (0,15 a 0,91) | 0,68 (−0,04 a 0,91) |

Las 5 noches C quedan como B.

**H1 no se replica.** El cociente sube con la apnea en 4 de 8 sujetos con las bandas publicadas y en 3 de 8 con las del esquema anterior; p de Holm 1.

**Con todos los minutos, nada cambia.** M2 da 0,610 contra 0,463, también sin diferencia.

---

## 18. Cómo leer los resultados (lo que hay que poder explicar)

1. **La ventaja de desarrollo ya era incierta frente a la referencia congelada:** 0,876 contra 0,810, y el intervalo de la diferencia (de −0,004 a +0,142) incluía el 0.
2. **La comparación de la anidada (0,851 contra 0,729) exageraba la ventaja.** Ahí la referencia se volvía a elegir en cada grupo y fue inestable: dos grupos dieron cerca de 0,53. La referencia congelada fue estable: 0,810 en desarrollo y 0,793 en test.
3. **Lo que cambió fue F:** de 0,851 en la anidada a 0,785 en test.
4. **El acierto por registro era la ventaja más clara de desarrollo** (0,81 contra 0,42) y es la que menos se reprodujo. Con 20 registros, y 5 casi sin apnea, es una medida muy variable.
5. **Potencia:** con 10 sujetos, aun siendo F mejor, había entre un 20 % y un 40 % de chances de no verlo.
6. **Adaptación a los datos.** Algunas decisiones se tomaron mirando todo desarrollo: la banda de apnea, la regla de no inferioridad y la reformulación de H1. La anidada no elimina ese optimismo.
7. **Sobreestimación.** Youden equilibra sensibilidad y especificidad, pero no la cantidad. Un Spearman alto no es concordancia: el detector ordena bien las noches y aun así sobreestima.
8. **Qué no se puede hacer ahora.** Cambiar el pipeline y volver a medir sobre el mismo test deja de ser una validación independiente. Una continuación necesita datos nuevos.

---

## 19. Todos los parámetros

| Parámetro | Valor | Por qué | Origen |
|---|---|---|---|
| Frecuencia de muestreo | 100 Hz | La de la base | dato |
| Resolución | 12 bits, 5 µV por paso | Medida en los archivos | dato |
| Registros excluidos | c05, x22, x33 | Grabaciones duplicadas; se queda la que empieza antes | dato |
| Partición | 70/30 por sujeto, semilla 2026, ±2 puntos de apnea, cuotas por categoría | Lo pidió la devolución y evita filtrar personas a test | criterio |
| Categorías | A ≥ 100, B 5–99, C < 5 minutos de apnea | Reproduce las letras oficiales | dato |
| Filtro | Butterworth 0,5–45 Hz, orden 3, ida y vuelta | Cumple la especificación medida con el menor orden | dato; los límites de 1 dB y 20 dB son criterio |
| Desfase y polaridad del QRS | Latido mediano a ±150 ms de la marca | `sqrs125` no marca el R y hay registros invertidos | criterio |
| Búsqueda del R | ±30 ms alrededor de la marca corregida | Margen menor que el ancho del QRS, para no saltar a otra onda | criterio |
| Refinamiento | Parábola de 3 puntos, corrimiento de ±0,5 muestras como máximo | Verificado con la prueba de dos fases | dato |
| Rango de intervalos | 0,3–2 s | Rango fisiológico (30 a 200 latidos por minuto) | supuesto heredado |
| Ectópicos | > 20 % de la mediana de 11 vecinos; interpolación lineal | Heredado | supuesto, sin verificar |
| Exclusión de minutos | > 20 % de intervalos corregidos | Heredado; solo se verificó que no sesga | supuesto |
| Señal perdida | Tramo plano o en el tope durante ≥ 1 s | Un electrocardiograma real no queda constante 1 s; excluirla no se adoptó | criterio + dato |
| Respiración derivada | Área con signo del QRS, ±60 ms, sobre la señal filtrada | Ganó en E1 y en E3a; ±60 ms ≈ el ancho del QRS | dato + criterio |
| Segmento de la deriva (candidata) | De −100 a −50 ms | Es el segmento PR, isoeléctrico | criterio |
| Remuestreo | 2 Hz, spline cúbico | Cubre hasta 1 Hz y las bandas llegan a 0,4 Hz; con interpolación lineal el ranking es igual | criterio + chequeo |
| Unidad de decisión | 1 minuto | Las etiquetas son por minuto | dato |
| Ventana de F | 240 s centrada en el minuto | Elegida entre 3 y 8,5 minutos (E3a y E3b); da una resolución de 0,008 Hz | dato |
| Estimador de F | Welch, 3 segmentos de 120 s, 50 % de solapamiento, Hann, tendencia lineal restada por segmento | Welch 3 ganó en E3a; Hann y 50 % son lo habitual | dato + criterio |
| Banda de F | 0,01–0,05 Hz | Ganó en E3a; es el ciclo de apnea de 20 a 100 s | dato + fisiología |
| Transformación | log(máx(potencia, 10⁻¹²)) | No cambia el orden; evita el log de 0 | criterio |
| Posprocesado | Ninguno | Normalizar empeora y suavizar no cambia (E3b) | dato |
| Referencia | Potencia de muy baja frecuencia (0,01–0,04 Hz), Lomb, 180 s | Ganó en E4 y en E3b | dato |
| Lomb | Grilla de 0,005 a 0,5 Hz cada 0,0025 Hz; mínimo de 20 latidos por ventana | Resolución suficiente para las bandas | criterio |
| Umbrales | F ≥ −6,9486; referencia ≥ 0,0012585 | Índice de Youden con todo desarrollo | devolución + dato |
| Margen de no inferioridad | δ = 0,02 | Tolerancia metodológica | criterio |
| Remuestreos | 2.000 en desarrollo (500 para el acierto al elegir), 1.000 y 300 en la anidada, 10.000 en test; semilla 2026 | Precisión contra tiempo de cálculo | criterio |
| Validación cruzada | 5 grupos de sujetos, separados por apnea | Que cada grupo tenga de las dos clases | criterio |
| Wiener (no adoptado) | Realizaciones de −250 a +400 ms; 129 coeficientes | Cubre P, QRS y T; aproxima bien H(f) | criterio |
| Pan-Tompkins (no adoptado) | Valores clásicos (tabla de la sección 10); tolerancia de 100 ms | Literatura | supuesto de la literatura |
| H1 | Ventana de 512 s; bandas publicadas y del esquema anterior; ≥ 5 minutos por clase | Fijado antes de la prueba | criterio |
| E1 | Ventanas de 2 minutos, segmentos de 32 s, ≥ 0,05 Hz; desfase de 10 minutos para el azar | Fijado antes | criterio |
| Test | 10.000 remuestreos, Holm, nivel de 0,05 | Plan cerrado | criterio |

---

## 20. Desvíos declarados

| Dónde | Desvío | Motivo |
|---|---|---|
| E1 | La deriva de línea de base se agregó en una segunda versión, antes de correrla | Faltaba un método que no usara la forma del QRS |
| E1 | El empate entre área y deriva no se desempató por simplicidad: pasó a E3 | E3 decide con la tarea real y con 19 sujetos en lugar de 8 |
| E2 | H1 se reformuló después de ver los datos: "aparece un acoplamiento lento" | La coherencia respiratoria no bajaba |
| E3a | Se agregaron la regla de no inferioridad, la de mayor área y la forma "potencia sola" después de la primera corrida | La regla original era defectuosa; la forma nueva era un control. La regla la eligió la validación cruzada |
| 4.3 | Los umbrales del detector se vuelven a aprender si falla la búsqueda hacia atrás | El detector quedaba ciego en a03 y a17 |
| Plan 9.1 | La 4.1 se agregó a las condiciones para abrir test | El refinamiento del R no estaba verificado |
| Plan 9.2 | El índice de apnea-hipopnea entró como resultado secundario | Es la medida clínica; como medida principal repetiría M2 |
| Plan 9.3 | Se agregó "A contra el resto" | La regla de la base deja las noches de control como B; se eligió por criterio clínico después de ver el notebook 12 |

---

## 21. Qué quedó de cada tema obligatorio

| Tema | Qué se hizo | ¿Está en el detector final? |
|---|---|---|
| Adquisición | Formato medido, calidad, saturación y cuantización | Sí: el refinamiento del R |
| Filtros convencionales | Pasabanda diseñado con una especificación medida | Sí |
| Recorte en realizaciones | Latidos alineados en R para estimar señal y ruido | No (es parte del Wiener) |
| Filtros óptimos | Wiener por registro | No: falló la no inferioridad en el acierto por registro |
| Detección de QRS | Pan-Tompkins propio, validado y revisado a mano | No: se usan las marcas de la base, con el R refinado |
| Segmentación | Minuto como unidad; ventana centrada de 240 s | Sí |
| Variabilidad cardíaca | 10 features candidatas; la mejor es la referencia | Sí, como referencia de H2 |
| Lomb | Espectro de la serie RR sin interpolar | Sí, en la referencia |
| Aporte propio | Potencia cruzada entre la serie RR y la respiración derivada en la banda de apnea | Sí: es F |

---

## 22. Preguntas probables de la defensa

1. **¿Por qué potencia cruzada y no coherencia?** Porque sin la coherencia se detecta igual (0,874 contra 0,871) y la coherencia sola detecta mal (0,63). Lo que separa es cuánto oscilan juntas las señales, no la sincronía.
2. **¿Por qué no normalizan cada noche?** Porque empeora el área en todas las familias (de 0,876 a 0,68–0,73) y arruina el acierto por registro. Con un umbral común, el nivel de cada noche es información.
3. **¿Por qué 4 minutos si las etiquetas son de 1?** Para resolver 0,01 Hz hacen falta segmentos de más de 100 s. La ventana se eligió con datos entre 3 y 8,5 minutos. El costo, que es mezclar minutos vecinos en los bordes de los episodios, se reporta.
4. **¿La respiración derivada no es ruido?** No: con la respiración real da 0,53 de coherencia, contra 0,16 por azar. Y con la respiración real, el efecto de H1 aparece en los 5 registros.
5. **¿Por qué el sujeto es la unidad?** Porque los minutos de una persona no son independientes, y hay personas con varias noches y grabaciones duplicadas.
6. **¿Cómo evitaron el sobreajuste?**
   - reglas fijadas antes de correr;
   - no inferioridad en lugar de "el máximo";
   - la más simple entre las equivalentes;
   - validación cruzada por sujetos, simple y anidada;
   - test una sola vez, con un plan cerrado.
7. **¿Por qué Lomb si después remuestrean?** Lomb da el espectro de la variabilidad cardíaca sin interpolar los latidos irregulares. El espectro cruzado necesita dos series en la misma grilla uniforme.
8. **¿El Wiener no borra la respiración derivada?** No, porque es lineal e invariante en el tiempo: aplica la misma ganancia a todos los latidos y conserva la relación de amplitudes entre ellos.
9. **¿Qué es nuevo?** Sumar al RR la respiración derivada en la banda del ciclo de apnea, con un punto de corte estadístico. En desarrollo mejoraba sobre todo la estimación de cuánta apnea tiene cada noche; en test no se confirmó.
10. **¿Por qué importan los 100 Hz?** Porque redondean el pico R a 10 ms e inflan la variabilidad latido a latido. Se midió y se corrigió con la parábola, verificada con la prueba de dos fases.
11. **¿Por qué Youden?** Lo pidió la docente. Además pesa igual la sensibilidad y la especificidad y no depende de la prevalencia. Las alternativas probadas no mejoraron con sujetos de afuera.
12. **Si el detector propio da 0,996 de sensibilidad, ¿por qué no lo usan?** Porque la regla exige no empeorar F en las dos medidas, y en el acierto por registro el límite fue −0,097. Además, la mitad de las discrepancias eran errores de las marcas o dudosas.
13. **¿Fracasó el método porque H2 no se confirmó?** No se puede decir que fracasó ni que funcionó:
    - en test no hay diferencia en ninguna medida, con intervalos enormes;
    - la ventaja de desarrollo ya era incierta frente a la referencia congelada;
    - en test, la que cayó fue F.
    El método de evaluación sí cumplió su función: mostró honestamente que la ventaja no se sostiene.
14. **¿Por qué Wilcoxon y no t?** Con 14 sujetos no se puede verificar la normalidad, y elegir la prueba según una prueba previa distorsiona el error de tipo I.
15. **¿Por qué el área con todos los minutos juntos?** Porque el detector usa un único umbral para todas las personas. En la anidada se calcula por grupo porque cada grupo puede elegir otra feature.
16. **¿Por qué no siguen probando cambios ahora que vieron test?** Porque cualquier cambio medido sobre el mismo test deja de ser una validación independiente. Hace falta otra base.
17. **¿Por qué las noches de control salen B?** Porque F marca como apnea entre el 5 % y el 16 % de sus minutos, y para ser C hay que tener menos de 5 minutos en toda la noche. Ningún detector minuto a minuto con una especificidad cercana a 0,9 llega a eso.
18. **¿Qué es la no inferioridad y por qué 0,02?** Es exigir, con un 95 % de confianza, que la candidata no sea más de 0,02 peor. El 0,02 es una tolerancia metodológica, no clínica, y se declara.
19. **¿Funciona en tiempo real?** No: el filtrado ida y vuelta y la ventana centrada usan muestras futuras. Es un análisis fuera de línea.
20. **¿Por qué la ventana pasó de 3 a 4 minutos entre E3a y E3b?** La eligió la regla fijada antes de correr, aplicada a todas las combinaciones con posprocesado. En la validación anidada, los cinco grupos volvieron a elegir 4 minutos. Las dos ventanas rinden casi igual (0,871 contra 0,876), así que la elección casi no cambia el resultado.

---

## 23. Glosario breve

| Término | Qué es |
|---|---|
| **Coherencia** | La correlación entre dos señales en cada frecuencia, normalizada entre 0 y 1. Mide sincronía, no tamaño. |
| **Potencia cruzada** | El módulo del espectro cruzado: es grande cuando las dos señales oscilan fuerte y juntas en esa frecuencia. |
| **Welch** | Promedia los periodogramas de segmentos solapados. Baja la varianza a costa de resolución. |
| **Multitaper** | Promedia espectros calculados con varias ventanas ortogonales (de Slepian) sobre toda la señal. |
| **Lomb** | Estima el espectro ajustando senoides por cuadrados mínimos sobre muestras irregulares, sin interpolar. |
| **Índice de Youden** | Sensibilidad + especificidad − 1. Su máximo da el umbral. |
| **Área bajo la curva** | La probabilidad de que un minuto con apnea tenga F mayor que un minuto normal elegido al azar. |
| **Bootstrap por sujeto** | Remuestrear sujetos enteros con reposición para obtener intervalos que respeten la dependencia entre minutos. |
| **No inferioridad** | Que el límite inferior del intervalo de la diferencia sea ≥ −δ. |
| **Wilcoxon de rangos con signo** | Prueba no paramétrica sobre diferencias pareadas, una por sujeto. |
| **Rango-biserial** | El tamaño del efecto del Wilcoxon, de −1 a 1. |
| **Holm** | Corrección por comparaciones múltiples, paso a paso. Controla la probabilidad de al menos un falso positivo. |
| **Spearman** | Correlación entre rangos. Mide el orden, no la concordancia. |
| **Bland–Altman** | La diferencia entre lo estimado y lo real contra su promedio. Da el sesgo y los límites de acuerdo. |
| **Delta de Cliff** | Probabilidad de que un valor con apnea supere a uno normal, menos la inversa (de −1 a 1). En desarrollo, F 0,75 y la potencia de muy baja frecuencia 0,62. |
| **Validación cruzada anidada** | Repetir toda la elección sin ver a los sujetos con los que después se evalúa. |
| **Optimismo** | El área al elegir menos el área en los sujetos de afuera. |

---

## Anexo: equivalencias con las siglas del informe y del código

Esta guía no usa siglas, pero el informe, los notebooks y los profesores sí. Para reconocerlas:

| Sigla | En esta guía |
|---|---|
| ECG | electrocardiograma |
| EDR | respiración derivada (del electrocardiograma) |
| HRV | variabilidad cardíaca |
| VLF / LF / HF | potencia de muy baja / baja / alta frecuencia |
| LF/HF | cociente entre baja y alta frecuencia |
| AUC | área bajo la curva |
| ROC | la curva de sensibilidad contra 1 − especificidad |
| IC | intervalo de confianza |
| AHI | índice de apnea-hipopnea |
| CPC | acoplamiento cardiopulmonar publicado (Thomas et al., 2005) |
| CR | cociente de coherencias (lenta / respiratoria) |
| M1 / M2 | las dos medidas principales de H2 (área y acierto por registro) |
| FIR | filtro de respuesta finita al impulso |
| LTI | lineal e invariante en el tiempo |
| PSD | densidad espectral de potencia |
| Se / VPP | sensibilidad / valor predictivo positivo |
| SDNN / RMSSD / pNN50 | desvío estándar de los intervalos / raíz cuadrática media de las diferencias sucesivas / porcentaje de diferencias mayores a 50 ms |
| PCA | componentes principales |
