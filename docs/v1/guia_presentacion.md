# Guía para presentar las diapositivas 10 a 22

Presentación: `PSIB2026Q2_TPS_Grupo08_Defensa_con_curva_roc.pptx` (31 diapositivas). Me tocan las posiciones 10 a 22: las 10 a 19 de la presentación vieja más las tres que agregamos (1.134 combinaciones, 60 candidatas de la referencia y curva de sensibilidad contra especificidad).

**Ojo con la numeración:** en la presentación, la diapositiva de ventana y posprocesamiento (posición 16) muestra el número **17** y la de la curva (posición 17) muestra el **16**. Conviene corregir los números de esas dos o volver a ponerlas en orden antes de presentar.

Tiempo total orientativo: unos **11 minutos y medio**.

## El hilo de mi parte en una frase por diapositiva

| Posición | Tema | Idea que tiene que quedar |
|---|---|---|
| 10 | Respiración derivada | El área del QRS sí capta la respiración: 0,53 contra 0,16 del azar |
| 11 | H1 en desarrollo | Con la apnea aparece acoplamiento lento: 11 de 14 sujetos |
| 12 | Mapas nocturnos | Se ve el acoplamiento lento durante la apnea y el respiratorio sin ella |
| 13 | Selección de features | F = potencia cruzada en 0,01–0,05 Hz; la referencia = muy baja frecuencia con Lomb |
| 14 | 1.134 combinaciones | Qué se probó para F y con qué regla se eligió |
| 15 | 60 candidatas | La referencia se eligió con la misma regla, para que la comparación fuera justa |
| 16 | Ventana y posprocesamiento | 240 s, sin normalizar y sin suavizar: normalizar borra la información |
| 17 | Curva en desarrollo | F 0,873 contra 0,808, pero es optimista |
| 18 | Detector congelado | La receta exacta, fijada antes de abrir test |
| 19 | Validación anidada | Estimación más honesta: F 0,851 y la misma F en los 5 grupos |
| 20 | Test | No se demuestra superioridad: 0,785 contra 0,793, p de Holm 1 |
| 21 | Decisiones por minuto | F detecta más, pero con más falsas alarmas; misma exactitud |
| 22 | Apnea por noche | F sobreestima 7,3 minutos por hora; las noches de control quedan como B |

**Transición de entrada** (desde Wiener, diapositiva 9): "Con el electrocardiograma limpio y los latidos bien marcados, el siguiente paso fue sacar la respiración del propio electrocardiograma."

---

## 10 · Respiración derivada: elección y validación con respiración real (55 s)

**Qué muestra el gráfico.** Nueve formas de medir la respiración desde el electrocardiograma, comparadas con la respiración medida en los 8 registros que la tienen.
- Cada fila es un método.
- Los puntos grises son los registros.
- El punto de color es el promedio y la barra es el intervalo de confianza del 95 %, calculado con bootstrap.
- El eje horizontal es la coherencia con la respiración real.

| Método | Coherencia |
|---|---|
| **Área del QRS con filtro** (la que se usa) | **0,53** |
| Línea de base (sin filtro) | 0,45, empatada con el área |
| Pico a pico, amplitud | 0,31 a 0,41 |
| Componentes principales | 0,19 a 0,20, casi azar |
| **Azar** | **0,16** |

**Qué decir.** "Comparamos cinco métodos de respiración derivada, con y sin filtro, contra la respiración real en los ocho registros que la tienen. El área del QRS filtrado llegó a una coherencia de 0,53, contra 0,16 del azar. Empató con la línea de base, y el empate se resolvió después, por detección de apnea, a favor del área. Con el filtro final la coherencia fue 0,520. Esto muestra que la respiración derivada contiene información respiratoria, aunque no reproduce la respiración perfectamente."

**Trampa: el punto naranja.** La leyenda dice "elegida" y el naranja es la **línea de base**, no el área. Decirlo antes de que pregunten: "El naranja es lo que habría elegido la regla de esta etapa por simplicidad. Como estaba empatada con el área, el empate se resolvió en la etapa siguiente, mirando qué detectaba mejor la apnea con los 19 sujetos, y ganó el área."

**Preguntas probables.**
- *¿Cómo se midió el azar?* Se desplazó la respiración derivada 10 minutos respecto de la real, con desplazamiento circular, y se recalculó la misma coherencia. Así cada señal queda igual, pero se rompe su relación en el tiempo. No da 0 porque la coherencia estimada con pocos segmentos (unos 6 por ventana) siempre tiene un piso positivo, de alrededor de 1/6.
- *¿Qué es el área del QRS?* La integral con signo del electrocardiograma en ±60 ms alrededor del pico R, en cada latido. La respiración cambia la posición del corazón y la impedancia del tórax, y eso cambia la proyección del vector eléctrico sobre la derivación, y con ella el área.
- *¿0,53 no es poco?* Es una coherencia media sobre toda la banda respiratoria y toda la noche. Lo que importa es que está muy por encima del azar (0,16). No hace falta que la respiración derivada sea idéntica a la real, solo que lleve su ritmo.
- *¿El filtro se volvió a aplicar?* No: es el mismo filtro del preprocesamiento. El 0,520 es el resultado de repetir la medición con el filtro final.

---

## 11 · H1: aumento del cociente de coherencias en desarrollo (55 s)

**Qué muestran los dos gráficos.** La prueba de H1 sujeto por sujeto.
- Cada fila es uno de los 14 sujetos con noches A o B.
- El eje horizontal es cuánto cambia, dentro de ese sujeto, el cociente entre la coherencia lenta y la respiratoria en los minutos con apnea respecto de los normales.
- **Azul:** sube, como predice H1. **Naranja:** baja.

**Por qué hay dos gráficos.** Son los mismos datos y el mismo cálculo. Solo cambia **dónde se corta entre la banda lenta y la respiratoria**:

| | Izquierdo: acoplamiento publicado | Derecho: esquema anterior |
|---|---|---|
| Corte | 0,10 Hz | 0,15 Hz |
| Sujetos a favor | **11 de 14** | 10 de 14 |
| p de Holm | **0,011** | 0,03 |

Los dos cortes se fijaron antes de correr la prueba, porque no había uno "correcto" conocido. Elegir el corte después de ver los resultados sería hacer trampa.

**Qué decir.** "Comparamos, dentro de cada sujeto, el cociente entre la coherencia lenta y la respiratoria en minutos con y sin apnea. Con las bandas publicadas el cociente subió en 11 de 14 sujetos, con p corregido 0,011 y un tamaño de efecto de 0,81. Al separar el cociente vimos que sube la coherencia lenta, pero no baja la respiratoria. Por eso reformulamos H1 como la aparición de un componente lento adicional. Tres sujetos fueron en contra."

**Las dos medidas estadísticas, en simple.**
- **Prueba de Wilcoxon de rangos con signo:** para cada sujeto se toma su diferencia, se ordenan los valores absolutos y se suman los rangos de las positivas y de las negativas. Si no hubiera efecto, las dos sumas serían parecidas.
- **Rango-biserial (0,81):** (suma de rangos positivos − suma de negativos) / suma total. Va de −1 a +1. Un 0,81 quiere decir que casi todo el peso está del lado de H1. Es el tamaño del efecto, no la significación.
- **Holm:** se hicieron dos pruebas (dos cortes), y con dos pruebas aumenta la chance de un falso positivo por azar. Holm ordena los valores p y multiplica el menor por 2 y el siguiente por 1, sin dejar que baje. Por eso cada gráfico tiene su propio p de Holm.
- *El azar viene de los sujetos, no del cálculo:* el cálculo es exacto, pero con otros 14 sujetos de la misma población el resultado sería otro. El valor p responde qué tan raro sería este resultado si en la población no hubiera efecto.

**Preguntas probables.**
- *¿El p de 0,011 quiere decir que hay un 1,1 % de chance de que no se replique?* No. Quiere decir que, si no hubiera efecto, un resultado así o más extremo saldría alrededor del 1,1 % de las veces, ya corregido por las dos pruebas.
- *¿Se replicó en test?* No: 4 de 8 sujetos a favor con el corte de 0,10 y 3 de 8 con el de 0,15. Fue un análisis secundario.
- *¿Por qué sube la coherencia lenta?* Cada episodio de apnea produce una oscilación lenta: el ritmo cardíaco y la amplitud de la respiración suben y bajan juntos con cada ciclo de apnea y recuperación, cada 20 a 100 segundos, o sea entre 0,01 y 0,05 Hz.

---

## 12 · Mapas nocturnos de acoplamiento (60 s)

**Qué muestra.** Cuatro mapas de coherencia a lo largo de toda la noche:

| | Izquierda: RR con respiración derivada | Derecha: RR con respiración real del tórax |
|---|---|---|
| **Arriba: a03** (categoría A) | Lo que ve nuestro método | Lo mismo con la respiración medida |
| **Abajo: c02** (control) | Lo que ve nuestro método | Lo mismo con la respiración medida |

Horizontal: horas. Vertical: frecuencia. Azul oscuro: más coherencia. Franja naranja arriba: minutos con apnea.

**Qué señalar con el puntero.**
1. **a03, abajo, cerca de 0,02 Hz:** franjas oscuras debajo de los bloques naranjas. Es el acoplamiento lento de la apnea.
2. **a03, cerca de 0,2 Hz:** manchas en los tramos sin apnea. Es el acoplamiento respiratorio normal.
3. **c02:** una banda casi continua en 0,22–0,25 Hz toda la noche, y nada abajo.
4. **Izquierda contra derecha:** los mismos patrones, más nítidos con la respiración real. La respiración derivada capta el fenómeno, aunque más atenuado.

**Qué decir.** "En a03, durante las apneas aparecen franjas de coherencia muy abajo, cerca de 0,02 Hz: es el acoplamiento lento de H1. Sin apnea, el acoplamiento está cerca de 0,2 Hz, el ritmo de la respiración. En el control domina el acoplamiento respiratorio toda la noche. A la izquierda usamos la respiración derivada y a la derecha la respiración real: los patrones coinciden, así que no son un artefacto del método. Son dos ejemplos elegidos con una regla previa; la evidencia de H1 es la prueba por sujetos."

**Preguntas probables.**
- *¿Por qué esos dos?* Regla previa: el registro A con respiración real más cercano al 50 % de apnea (para tener tramos con y sin apnea en la misma noche) y el control con respiración real con más minutos.
- *¿Por qué 512 s y no 240 s?* Son los mapas de la prueba de H1, que usa la configuración del acoplamiento publicado, fijada antes. Los 240 s del detector se eligieron después y con otro objetivo.
- *¿Las líneas punteadas?* Son los cortes de 0,10 y 0,15 Hz de los dos gráficos de la diapositiva 11.

---

## 13 · Selección de la feature conjunta y la referencia (55 s)

**Qué muestra.** El resumen de lo que se eligió: 1.134 candidatas para F y 60 para la referencia.
- **F:** potencia cruzada entre la serie RR y la respiración derivada, en 0,01–0,05 Hz.
- **Referencia:** potencia de la serie RR estimada con Lomb, en 0,01–0,04 Hz.

**Qué decir.** "No tomamos la candidata con mayor área: retuvimos las no inferiores y después priorizamos el acierto por registro y la simplicidad. Ganó la potencia cruzada en 0,01 a 0,05 Hz, sin ponderar por coherencia. La referencia fue la potencia de muy baja frecuencia del RR con Lomb, que no necesita interpolar los intervalos. Algunas reglas cambiaron después de una primera corrida; por eso son esenciales la validación anidada y el test."

Esta diapositiva puede ir rápido, porque las dos siguientes la detallan.

---

## 14 · Qué se probó: 1.134 combinaciones de F (50 s)

**Qué muestra.** 3 respiraciones × 6 ventanas × 3 estimadores × 3 bandas × 7 formas = 1.134. En marrón, lo que ganó.

| Elección | Opciones | Ganó |
|---|---|---|
| Respiración derivada | área, línea de base, combinada | área del QRS |
| Ventana | 3 a 8,5 minutos | 3 min en esta etapa; 4 min (240 s) en la siguiente |
| Estimador | Welch con 3 o 7 segmentos, multitaper | Welch con 3 segmentos |
| Banda lenta | 0,01–0,05 (apnea), 0,01–0,10 (publicada), 0,01–0,15 (esquema anterior) | apnea |
| Forma | 7, de coherencia sola a potencia cruzada | potencia cruzada |

**La regla, en tres pasos.**
1. **No inferioridad en área:** quedan las candidatas cuya diferencia con la mejor tiene un límite inferior del intervalo de confianza de al menos −0,02.
2. **Empate en acierto por registro (Spearman):** entre esas, las que no son peores en ordenar las noches.
3. **La más simple.**

**El dato clave:** potencia cruzada 0,871 contra coherencia sola 0,629. Lo que detecta la apnea es **cuánto oscilan juntas** las dos señales, no qué tan sincronizadas están.

**Preguntas probables.**
- *¿Qué es la potencia cruzada?* Para cada frecuencia, el producto entre la transformada de una señal y la conjugada de la otra. Su módulo es √coherencia × √(potencia del RR × potencia de la respiración derivada): crece si las dos oscilan fuerte **y** juntas. Después se promedia en la banda y se le aplica el logaritmo.
- *¿Por qué el logaritmo?* No cambia el orden de los minutos, así que el área bajo la curva es la misma. Sirve para que los valores, que varían en órdenes de magnitud, tengan una escala manejable para el umbral.
- *¿Por qué no se eligió la mayor área?* Porque entre muchas candidatas casi iguales la mayor gana en parte por azar. La no inferioridad deja todas las que están dentro del ruido y elige con otros criterios.
- *¿Multitaper?* Estima el espectro con varias ventanas ortogonales en vez de partir la señal en segmentos; reduce la varianza sin perder tanta resolución. No ganó.
- *¿Por qué 3 segmentos?* En 240 s, segmentos de 120 s dan una resolución de 1/120 ≈ 0,008 Hz, que alcanza para separar frecuencias dentro de 0,01–0,05. Con 7 segmentos son más cortos y la banda queda con muy pocas frecuencias.

---

## 15 · Qué se probó: 60 candidatas de la referencia (45 s)

**Qué muestra.** 10 features de variabilidad cardíaca × 6 ventanas, todas con la serie RR sola.
- **En el tiempo (4):** intervalo medio, desvío estándar, raíz cuadrática media de las diferencias sucesivas, porcentaje de diferencias mayores a 50 ms.
- **En frecuencia con Lomb (6):** muy baja (0,01–0,04), banda de apnea (0,01–0,05), baja (0,04–0,15), alta (0,15–0,40), total y el cociente baja / alta.

| Mejores en desarrollo | Área |
|---|---|
| **Muy baja frecuencia, 3 min** (ganó) | **0,810** |
| Banda de apnea, 3 min | 0,812 |
| Cociente baja / alta | 0,73 |

**Qué decir.** "La referencia no fue una feature fija: la elegimos entre 60 candidatas con la misma regla que F, para que la comparación fuera justa. Ganó la potencia de muy baja frecuencia con Lomb, con 0,810. Las features en el tiempo no ganaron porque miden cambios rápidos entre latidos y la apnea produce oscilaciones lentas."

**Preguntas probables.**
- *¿Qué es Lomb?* Estima el espectro ajustando senos y cosenos directamente sobre los latidos, que no están igualmente espaciados en el tiempo. No hace falta interpolar.
- *¿Por qué no se usó Lomb para F?* El espectro **cruzado** necesita las dos señales en los mismos instantes y con la fase; Welch lo da directamente sobre series remuestreadas. Lomb es un estimador de una sola señal.
- *¿La muy baja frecuencia no es justamente la de la apnea?* Sí: la referencia también mira la oscilación lenta, pero solo en el ritmo cardíaco. F mira casi la misma banda, pero exige que el ritmo cardíaco y la respiración derivada oscilen juntos.
- *¿En 3 minutos aparece una frecuencia tan lenta?* 0,01 Hz es un ciclo cada 100 s, así que en 180 s entran casi dos ciclos. Alcanza para estimar la potencia, con poca resolución.
- *¿Por qué la diferencia con la anidada?* En la validación anidada la referencia se volvía a elegir en cada grupo y fue inestable (0,729). La congelada, la que se usó en test, fue estable: 0,810 en desarrollo y 0,793 en test.

---

## 16 · Ventana temporal y posprocesamiento (50 s)

*(En la presentación aparece con el número 17.)*

**Qué muestran los gráficos.** Las tres opciones de normalización por noche, sin suavizar:
- **ninguna;**
- **línea de base:** a cada minuto se le resta el percentil 10 de su noche;
- **z-score:** a cada minuto se le resta la media de su noche y se lo divide por su desvío.

Una línea por familia: F (azul), referencia (naranja), RR solo (negro), respiración derivada sola (gris). Izquierda: área por minuto. Derecha: acierto por registro.

| | Área: ninguna | línea de base | z-score | Acierto: ninguna | línea de base | z-score |
|---|---|---|---|---|---|---|
| **F** | **0,876** | 0,677 | 0,732 | **0,813** | 0,125 | 0,664 |
| Referencia | 0,810 | 0,793 | 0,750 | 0,422 | 0,478 | 0,683 |

**Qué decir.** "Probamos normalizar cada noche. En los dos gráficos lo mejor es no normalizar: normalizar empeora el área de todas las features, y con la línea de base F casi deja de ordenar las noches, de 0,81 a 0,13. Normalizar iguala las noches y borra la diferencia de nivel entre una noche con mucha apnea y una sin apnea, que con un umbral común es justamente la información. El suavizado casi no cambiaba nada. Quedamos con 240 segundos, sin normalizar ni suavizar."

**Preguntas probables.**
- *¿Por qué 240 s si en la etapa anterior ganó 180?* Se volvió a aplicar la regla en esta etapa: 240 s dio 0,876 contra 0,871, y por la regla quedó 240. La validación anidada la volvió a elegir en los cinco grupos. La resolución en frecuencia es una explicación posible, no el motivo de la elección.
- *¿Por qué no se mantuvo el z-score para la referencia, si mejoraba el acierto (0,42 a 0,68)?* La regla filtra primero por área, y su área bajó a 0,750: quedó afuera en el primer paso. Saltarse la regla sería elegir después de mirar, y además tiene que ser la misma regla para las dos.
- *¿Qué costo tiene una ventana de 240 s?* Cada decisión de un minuto usa unos dos minutos a cada lado, y los bordes de los episodios se suavizan.
- *¿Suavizado?* Mediana móvil de 3 o 5 minutos: cambiaba el área en menos de 0,005, así que por simplicidad no se agregó.

---

## 17 · Curva de sensibilidad contra especificidad en desarrollo (45 s)

*(En la presentación aparece con el número 16.)*

**Qué muestra.** Para cada umbral posible, la sensibilidad (eje vertical) contra 1 − especificidad (eje horizontal), para F y para la referencia, con los 22.275 minutos finales de los 19 sujetos.

**Qué decir.** "La curva muestra, para cada umbral, qué fracción de los minutos con apnea se detecta contra qué fracción de los normales se marca por error. La diagonal es el azar. El área es la probabilidad de que un minuto con apnea tenga un valor más alto que uno normal. En desarrollo F queda por encima en todo el recorrido: 0,873 contra 0,808. El punto es el umbral de Youden, con sensibilidad 0,84 y especificidad 0,75. Pero esta curva usa los mismos datos con los que se eligió todo, así que es optimista. En test, las áreas fueron 0,785 y 0,793, y las curvas casi se superponen."

**Definiciones.**
- **Sensibilidad:** de los minutos con apnea, qué fracción se detecta.
- **Especificidad:** de los minutos normales, qué fracción se deja como normal.
- **Youden:** el umbral que maximiza sensibilidad + especificidad − 1. Pesa igual los dos errores y no depende de la proporción de apnea.

**Preguntas probables.**
- *¿Por qué 0,873 y no 0,876?* 0,876 es el valor del promedio de la etapa de posprocesamiento; 0,873 es el área con los 22.275 minutos finales juntos. Son la misma configuración.
- *¿Por qué no está la curva de test?* El notebook de test guardó las áreas y el gráfico de Bland–Altman, no la curva. No se volvió a abrir test para dibujarla.
- *¿Por qué umbral único y no uno por persona?* Para usarlo en una persona nueva habría que conocer de antemano sus minutos con apnea. El umbral único se puede aplicar a cualquiera.

---

## 18 · Detector final congelado (50 s)

**La receta, paso a paso.**
1. Electrocardiograma filtrado y marcas de los QRS refinadas.
2. Serie RR limpia y respiración derivada por área.
3. Las dos series se remuestrean a 2 Hz con interpolación cúbica.
4. Ventana centrada de 240 s alrededor de cada minuto.
5. Welch con tres segmentos de 120 s y 50 % de solapamiento.
6. Se promedia el módulo de la potencia cruzada en las K frecuencias entre 0,01 y 0,05 Hz y se aplica el logaritmo.
7. Si el valor supera **−6,9486**, el minuto es apnea (1); si no, normal (0).

**Qué decir.** Recorrer los pasos y terminar con: "Todo esto se congeló, con una etiqueta en el repositorio, antes de abrir test."

**Preguntas probables.**
- *¿Por qué 2 Hz?* La banda que interesa llega a 0,05 Hz y el ritmo respiratorio a unos 0,4 Hz: 2 Hz cubre todo con margen (el límite es 1 Hz) y mantiene las series cortas.
- *¿Por qué interpolación cúbica?* Los latidos no están igualmente espaciados y Welch necesita muestras regulares. La cúbica da una curva suave sin escalones.
- *¿Qué es K?* La cantidad de frecuencias del espectro que caen dentro de la banda; se usa para promediar.
- *¿Qué es congelar?* Fijar el código y los parámetros con una etiqueta de git antes de mirar test, para que nada se ajuste a esos datos.

---

## 19 · Validación cruzada anidada en desarrollo (55 s)

**Qué es.** Los 19 sujetos se dividen en 5 grupos. En cada vuelta se repite **toda** la selección (feature, posprocesamiento y umbral) con 4 grupos y se mide en el quinto, que no se usó para elegir.

| Medida en sujetos reservados | F | Referencia |
|---|---|---|
| Área media entre grupos | **0,851** | 0,729 |
| Sensibilidad | 0,839 | 0,690 |
| Especificidad | 0,748 | 0,602 |
| Acierto por registro | **0,807** | 0,234 |

Intervalo del 95 % para el área de F: 0,760 a 0,916. Los cinco grupos eligen exactamente la misma F.

**Qué decir.** "Para una estimación menos optimista repetimos toda la selección dejando afuera grupos completos de sujetos. F alcanzó un área media de 0,851 y un acierto por registro de 0,807, y los cinco grupos eligieron la misma F; la referencia, en cambio, cambió entre grupos. Algunas decisiones anteriores, como agregar la banda de apnea o cambiar la regla, ya habían usado todos los sujetos. Por eso queda algo de optimismo y esto no reemplaza al test."

**Trampa: el 0,729 de la referencia exagera la ventaja.** En cada grupo la referencia se volvía a elegir y fue inestable (cuatro grupos eligieron la banda de apnea y uno el cociente baja / alta; en dos grupos el área quedó cerca de 0,53). La referencia **congelada** dio 0,810 en desarrollo y 0,793 en test. La ventaja real de F frente a ella en desarrollo era de unos +0,066, con un intervalo de −0,004 a +0,142 que ya incluía el cero.

**Preguntas probables.**
- *¿Por qué difiere de la curva (0,873)?* La curva mide con los mismos sujetos con que se eligió y calcula una sola área con todos los minutos; la anidada promedia cinco áreas de sujetos de afuera.
- *¿Por qué la sensibilidad casi no cambia?* Todos los grupos eligieron la misma F, con umbrales entre −6,96 y −6,91, casi el congelado.
- *¿Por qué menos sorteos de bootstrap acá?* 1.000 para el área y 300 para el acierto, por tiempo de cálculo: cada sorteo repite toda la selección.

---

## 20 · Test: no se demuestra superioridad de F (65 s) — la más importante

| Medida | F | Referencia | Diferencia e intervalo del 95 % |
|---|---|---|---|
| Área por minuto | 0,785 | 0,793 | −0,007 [−0,162 a +0,112] |
| Acierto por registro | 0,634 | 0,613 | +0,021 [−0,543 a +0,514] |

20 registros de 10 sujetos. p de Holm = 1 en las dos medidas.

**Qué decir.** "El resultado principal es que la ventaja de desarrollo no se sostuvo en test: 0,785 para F y 0,793 para la referencia, y en el acierto por registro la diferencia también fue chica. Los dos intervalos incluyen el cero y los p corregidos fueron 1. No confirmamos H2, y tampoco podemos afirmar equivalencia. Diez sujetos hacen imprecisas las estimaciones, pero no alcanza con culpar a la falta de potencia: las diferencias puntuales también fueron chicas."

**Cómo se calcularon los intervalos.** Bootstrap por sujeto con 10.000 sorteos: se sortean 10 sujetos con reposición, se recalculan las dos medidas de F y de la referencia, se guarda la diferencia, y el intervalo son los percentiles 2,5 y 97,5. Se sortean sujetos, no minutos, porque los minutos de una misma persona no son independientes.

**Por qué el p de Holm da 1.** Los p sin corregir fueron 0,897 (área) y 0,841 (acierto): las diferencias de los sorteos cayeron mitad de cada lado de cero. Holm multiplica el menor por 2 (1,68) y lo recorta en 1, y el otro no puede quedar por debajo.

**Preguntas probables.**
- *¿Qué significa p = 1?* Que el resultado es exactamente lo esperable si F y la referencia rindieran igual. **No** significa que sean iguales: los intervalos también son compatibles con una ventaja clara de cualquiera de las dos.
- *Si F se hubiera alejado de la referencia, ¿bajaba el p?* Sí. Si casi todos los sorteos dieran diferencias positivas, la fracción del otro lado sería chica y el p también.
- *¿Por qué no se sostuvo?* La referencia congelada fue estable (0,810 → 0,793); fue F la que bajó (0,851 en la anidada → 0,785). Y la ventaja contra la referencia congelada ya era incierta en desarrollo.
- *¿Era esperable no ver diferencia con 10 sujetos?* La simulación en desarrollo (sortear 10 de los 19 sujetos) daba entre un 20 % y un 40 % de chance de no ver la ventaja aunque existiera. Pero en test la diferencia puntual misma fue casi cero.
- *¿Se cambió algo después de ver test?* No. Test se abrió una sola vez, el 9 de noviembre, y todo lo posterior es exploratorio.

---

## 21 · Test: decisiones por minuto y cobertura (50 s)

| Con los umbrales de desarrollo | F | Referencia |
|---|---|---|
| Sensibilidad | 0,790 | 0,735 |
| Especificidad | 0,642 | 0,686 |
| Exactitud | 0,706 | 0,707 |

8.556 de 9.754 minutos evaluados; 12,3 % excluido, sobre todo por intervalos RR corregidos.

**Qué decir.** "Con los umbrales congelados, F detectó más minutos con apnea, pero también dio más falsos positivos. La exactitud fue prácticamente igual, alrededor del 71 %. Se evaluaron 8.556 de 9.754 minutos: el 12,3 % excluido se concentró en dos registros con muchos intervalos corregidos. El análisis con todos los minutos mantuvo las conclusiones."

**Preguntas probables.**
- *¿Por qué se excluyen minutos?* Por la regla de calidad: si más del 20 % de los intervalos RR del minuto fueron corregidos (latidos ectópicos o mal detectados), el valor no es confiable y el minuto no se evalúa. Casi todo lo excluido es de c04 (74 % de sus minutos) y x29 (86 %).
- *¿Cómo se completaron en el análisis de sensibilidad?* Con la decisión del minuto vecino. Eso no valida esos tramos; solo muestra que excluirlos no cambia la conclusión.
- *¿Por qué bajó la especificidad respecto de desarrollo (0,75 → 0,64)?* El umbral es común y se fijó en desarrollo; en personas cuya F tiene otro nivel de base, más minutos normales pasan el umbral.

---

## 22 · Test: sobreestimación de apnea por noche (55 s)

**Qué muestra el gráfico de Bland–Altman.** Una noche por punto.
- **Horizontal:** el promedio entre los minutos de apnea por hora estimados y los anotados.
- **Vertical:** estimado − anotado.
- **Línea central:** el sesgo (+7,3 para F). Las otras dos: los límites de acuerdo, donde cae el 95 % de las noches (−27,9 a +42,5).
- Izquierda: F. Derecha: referencia (sesgo +5,1, límites −25,4 a +35,6).

**Lo ideal** sería que todos los puntos quedaran cerca de 0, en una franja angosta y sin tendencia.

**Cómo se reparten los puntos de F.**

| Noches | Dónde quedan | Lectura |
|---|---|---|
| A (12) | Las más leves, por debajo de 0 (hasta −27); las de más apnea, cerca de 0 o arriba | En promedio, casi centradas |
| B (3) | +17, +40 y +53 | Muy sobreestimadas |
| C (5) | +3 a +12 | Sobreestimadas: por eso las cinco quedan como B |

**El sesgo positivo viene de las noches B y C**, no de las A: el detector marca apnea de más en noches que casi no tienen.

**Qué decir.** "La correlación por noche no alcanza: el Bland–Altman muestra que F sobreestimó en promedio 7,3 minutos de apnea por hora, con límites de acuerdo amplios, de −27,9 a +42,5. Las cinco noches de control quedaron como B y la clasificación A/B/C acertó en el 45 % de las noches. Agrupar A contra el resto llegó al 70 %, pero fue un análisis agregado después de mirar desarrollo. Y no hay que confundir minutos con apnea por hora con el índice de apnea-hipopnea, que cuenta eventos por hora de sueño."

**Preguntas probables.**
- *¿Por qué sobreestima?* Youden equilibra sensibilidad y especificidad, no busca acertar la cantidad total. Con especificidad 0,64, una noche sin apnea acumula muchos minutos marcados por error.
- *¿Se intentó corregir?* Sí, con una calibración por noche en la validación anidada: una recta que lleva la fracción estimada a la real. Bajaba el error de 10,6 a 9,8 minutos por hora, con un intervalo de la diferencia que incluía el cero, así que no se adoptó.
- *¿Ya se sabía que las noches de control quedarían como B?* Sí: en la validación anidada pasó con las 12 de desarrollo. Para ser C hay que tener menos de 5 minutos con apnea, y un detector minuto a minuto con falsas alarmas no llega a eso.
- *¿Por qué se subestiman algunas noches A?* En desarrollo los falsos negativos se concentraban dentro de episodios largos y en pocos sujetos (S09 y S02), cuya F tiene un nivel más bajo que el umbral común.
- *¿Minutos con apnea por hora es lo mismo que el índice de apnea-hipopnea?* No. La base anota cada minuto como apnea o normal; el índice clínico cuenta eventos. Un minuto puede tener más de un evento, y un evento largo ocupa varios minutos.

---

## Números para memorizar

| Qué | Valor |
|---|---|
| Coherencia de la respiración derivada / azar | 0,53 (0,520 con el filtro final) / 0,16 |
| H1 en desarrollo | 11 de 14 sujetos, rango-biserial 0,81, p de Holm 0,011 (y 0,03) |
| H1 en test | 4 de 8 y 3 de 8: no se replicó |
| Candidatas | 1.134 para F, 60 para la referencia |
| Potencia cruzada contra coherencia sola | 0,871 contra 0,629 |
| Área en desarrollo (curva final) | F 0,873, referencia 0,808 |
| Validación anidada | F 0,851 (0,760 a 0,916), referencia reelegida 0,729 |
| Acierto por registro en la anidada | F 0,807, referencia 0,234 |
| Umbral de F | −6,9486 |
| Youden en desarrollo | sensibilidad 0,84, especificidad 0,75 |
| Test, área | F 0,785, referencia 0,793, diferencia −0,007 [−0,162 a +0,112] |
| Test, acierto por registro | F 0,634, referencia 0,613 |
| Test, p de Holm | 1 en las dos (sin corregir: 0,897 y 0,841) |
| Test, por minuto (F / referencia) | sensibilidad 0,790 / 0,735; especificidad 0,642 / 0,686; exactitud 0,71 |
| Cobertura en test | 8.556 de 9.754 minutos, 12,3 % excluido |
| Bland–Altman de F | sesgo +7,3 min/h, límites −27,9 a +42,5 |
| Clasificación por noche | 45 % A/B/C; 70 % A contra el resto |
| Bootstrap | 2.000 en desarrollo, 10.000 en test, 1.000 / 300 en la anidada |

## Cómo aparecen los términos en las diapositivas

| En la diapositiva | Qué quiere decir |
|---|---|
| EDR | respiración derivada del electrocardiograma |
| HRV | variabilidad cardíaca (la referencia) |
| AUC | área bajo la curva de sensibilidad contra 1 − especificidad |
| ROC | esa curva |
| VLF | muy baja frecuencia (0,01–0,04 Hz) |
| CPC | acoplamiento cardiopulmonar (las bandas publicadas) |
| IC 95 % | intervalo de confianza del 95 % |
| AHI | índice de apnea-hipopnea |
| Spearman por registro | acierto por registro: correlación de rangos entre la apnea estimada y la anotada de cada noche |
