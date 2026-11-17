# Objetivos, hipótesis y limitaciones

Documento de referencia para el informe, la presentación y los notebooks. Responde a la devolución: los objetivos tienen que estar separados de la hipótesis, tiene que haber **una sola hipótesis** demostrada paso a paso y las limitaciones tienen que estar explícitas.

## Objetivo general

Desarrollar y evaluar un método de procesamiento de señales que detecte, **minuto a minuto**, la presencia de apnea del sueño a partir de un **ECG de una derivación**, combinando la variabilidad de la frecuencia cardíaca (serie RR) y la respiración derivada del ECG (EDR) en una única feature con un umbral (sin aprendizaje automático).

## Objetivos específicos

Cada objetivo es un paso del trabajo, tiene un resultado medible y un notebook donde se resuelve.

| # | Objetivo | Resultado que lo cumple | Notebook |
|---|---|---|---|
| 1 | Caracterizar la base Apnea-ECG: etiquetas, categorías, calidad y artefactos de las señales en tiempo y frecuencia | Requisitos del preprocesamiento justificados con figuras y medidas por registro | `01` |
| 2 | Diseñar un filtro a partir del espectro del ECG y obtener la serie RR con un detector de QRS propio | Filtro que cumple una especificación sacada de los datos; detector validado contra las marcas de la base y con revisión manual | `02` |
| 3 | Obtener la respiración derivada del ECG (EDR) y medir cuánto se parece a la respiración registrada; evaluar si el filtro de Wiener la mejora | Coherencia EDR–respiración en la banda respiratoria y en la banda del ciclo de apnea, para cada variante | `03` |
| 4 | Identificar en qué banda de frecuencias la apnea modifica la serie RR y la EDR, qué información aporta cada señal, y construir con eso una feature por minuto | Banda medida en desarrollo; aporte de cada señal medido dentro de la noche y entre noches; feature definida con una ventana única | `01`, `04` |
| 5 | Fijar el umbral de decisión en desarrollo y evaluar el detector una única vez en los sujetos de test | Sensibilidad, especificidad, AUC por minuto y error por noche, con intervalos de confianza por sujeto | `04` |

## Hipótesis

### Enunciado

**H.** En la apnea obstructiva, cada episodio sigue un ciclo de pausa respiratoria y recuperación que dura entre 20 y 100 s: la frecuencia cardíaca baja durante la pausa y se acelera al reanudarse la respiración, y la mecánica del tórax cambia con el mismo ritmo. Ese ciclo aumenta la potencia de la serie RR y de la EDR en la banda de **0,01 a 0,05 Hz**. Se espera que:

- **(a) Dentro de cada noche**, la potencia del RR en esa banda sea **mayor en los minutos con apnea que en los minutos normales de la misma noche**.
- **(b) Entre noches**, el **nivel nocturno de la potencia de la EDR** en esa banda sea **mayor cuanto más apnea tiene la noche**.
- **(c) Sumando la potencia del RR de cada minuto y el nivel nocturno de la EDR** en una única feature, C, un **único umbral fijado en desarrollo** permita clasificar cada minuto de personas nuevas como apnea o normal.

Cada señal se usa para lo que mide bien (`04`, sección 6): el RR ubica la apnea dentro de la noche, pero su nivel general cambia de una persona a otra y no acompaña a la cantidad de apnea; la EDR separa peor los minutos, pero su nivel nocturno acompaña a la cantidad de apnea. En C, el término de la EDR es el mismo para toda la noche: no cambia el orden de los minutos dentro de la noche, pero corre toda la noche hacia arriba o hacia abajo según cuánta apnea indica.

### Definiciones operativas

| Término | Definición |
|---|---|
| Serie RR | Intervalos entre picos R del detector propio (`02`), con la limpieza del RR, interpolados a 2 Hz |
| EDR | Área con signo del QRS (±60 ms) sobre el ECG filtrado con Wiener, sin latidos ectópicos ni atípicos, dividida por el tamaño típico del QRS del registro (mediana del área sin signo), interpolada a 2 Hz (`03`) |
| Ventana de un minuto | 240 s centrados en el minuto |
| Potencia en la banda, P(m) | log₁₀ de la densidad espectral de potencia promediada en 0,01–0,05 Hz (las frecuencias k/120 Hz con k = 2, …, 6), estimada por Welch (3 segmentos de 120 s, Hann, 50 % de solapamiento) en la ventana del minuto m; P_RR para la serie RR y P_EDR para la EDR |
| Nivel nocturno de la EDR, P̄_EDR | Mediana de P_EDR en todas las ventanas de esa noche. No usa etiquetas: se calcula igual en test |
| Feature | **C(m) = [P_RR(m) − μ₁] / σ₁ + w · [P̄_EDR − μ₂] / σ₂**, con μ y σ medidos en los minutos de desarrollo y w = 1 elegido por validación cruzada por personas en desarrollo (`04`) |
| Decisión | Un minuto es apnea si C(m) supera el umbral de Youden de desarrollo |
| Minutos evaluados | Con etiqueta y con 20 % o menos de RR corregidos |

### Predicciones y criterio (fijados antes de abrir test)

| Predicción | Qué se mide en test | Se cumple si |
|---|---|---|
| **P1, dentro de la noche** (parte a) | AUC dentro de la noche de P_RR en cada registro con al menos 20 minutos de cada tipo | la media de esos AUC es mayor que 0,5 y su intervalo de confianza al 95 % (bootstrap por persona) no incluye 0,5 |
| **P2, entre noches** (parte b) | Correlación de Spearman entre P̄_EDR y el % de minutos con apnea de cada registro de test | ρ > 0 y su intervalo al 95 % (bootstrap por persona) no incluye 0 |
| **P3, detección** (parte c) | AUC de C con todos los minutos de test; sensibilidad, especificidad y exactitud con el umbral fijo | AUC > 0,5 con intervalo al 95 % (bootstrap por persona) que no incluye 0,5 |

**H se sostiene** si se cumplen las tres predicciones. Como hacen falta las tres, es una prueba de unión-intersección: la probabilidad de error de toda la prueba no supera el 5 % con que se evalúa cada predicción, así que no hace falta corregir por comparaciones múltiples (Berger, 1982). Si se cumplen P1 y P2 pero no P3, cada señal muestra el efecto esperado pero su suma no alcanza para detectar con un umbral. Si falla P2, la EDR no aporta lo que se esperaba entre noches y C se reduce, en la práctica, al RR solo.

### Preguntas secundarias (descriptivas, no son hipótesis)

1. **¿C mejora a las alternativas?** Se compara C con F (la potencia cruzada RR–EDR de la primera versión) y con el RR solo, dentro de la noche y con todos los minutos.
2. **¿Sirve la confianza?** Exactitud del detector en los minutos con poco y con mucho movimiento (`04`).
3. **Por noche:** fracción de minutos estimada contra la real (ρ de Spearman) y minutos marcados en los controles.

## Cambios hechos en desarrollo, antes de abrir test

| Cambio | Motivo | Dónde |
|---|---|---|
| La EDR se mide sobre los latidos del detector propio, con Wiener y sin latidos ectópicos ni atípicos | Mejora la detección dentro de la noche respecto de la primera versión sin empeorar el parecido con la respiración | `03`, sección 6 |
| La EDR es relativa: área con signo / mediana del área sin signo del QRS del registro | Sin etiquetas: la oscilación respiratoria de la EDR en mV·ms crece con el tamaño del QRS (ρ = 0,70) y en forma relativa deja de depender de él (ρ ≈ 0). Con etiquetas: con la EDR en mV·ms, dos personas con QRS chico quedaban casi sin minutos detectados | `03`, sección 7; `04`, sección 13 |
| La feature pasa de F (potencia cruzada RR–EDR) a C (potencia del RR de cada minuto + nivel nocturno de la EDR), y la hipótesis se reescribe | F resultó casi el promedio de las potencias del RR y de la EDR (r = 0,985): sumaba la EDR minuto a minuto y dentro de la noche quedaba peor que el RR solo (AUC medio 0,88 contra 0,91). C usa el RR para ubicar la apnea dentro de la noche y la EDR solo para el nivel de cada noche. Se probó también restarle al RR su mediana de la noche (variante G) y no mejoró (AUC con todos los minutos 0,921 contra 0,931 de C, sin diferencia), así que se eligió la versión más simple. En validación cruzada por personas, C: sensibilidad 0,81, especificidad 0,85, exactitud 0,836, AUC 0,907, AUC medio dentro de la noche 0,908, controles con 7 % de minutos marcados (F: 0,86 / 0,79 / 0,820 / 0,903 / 0,879 / 17 %). Con un bootstrap pareado de personas y sin corregir, C es mejor que F dentro de la noche (+0,029, IC 95 % +0,009 a +0,043) y en los controles (−9,4 puntos, IC −15,1 a −3,2); con la corrección de Holm sobre las 60 comparaciones, esas dos ventajas no resultan significativas en desarrollo. En test la ventaja en los controles y en la especificidad sí resiste la corrección (`06` §5) | `04`, secciones 6 y 7 |

## Lo que queda fijo para test

- **Preprocesamiento:** `02` y `03` tal como están en `src/` (configuración en `src/config.py`).
- **Feature:** C como en las definiciones, con los parámetros de desarrollo (`04`, sección 14; archivo `docs/parametros_test.json`, que es el que lee el notebook de test):

  | Parámetro | Valor |
  |---|---|
  | μ₁, σ₁ (potencia del RR) | −1,492 y 0,590 |
  | μ₂, σ₂ (nivel nocturno de la EDR) | −2,197 y 0,636 |
  | w | 1 |
  | Umbral | C > 0,489 |
  | Confianza | alta si el movimiento relativo ≤ −0,001; media hasta 0,702; baja por encima |

- **En desarrollo** (validación cruzada por personas): sensibilidad 0,81, especificidad 0,85, exactitud 0,84; P1 = 0,91, P2 = 0,83, P3 = 0,93. Se cumplen las tres, como era de esperar con datos que se usaron para armar la hipótesis.
- **Minutos evaluados, predicciones y preguntas secundarias:** como arriba.
- Test se corre **una sola vez**, con un notebook que solo lee estos valores.

## Resultado en test

Se evaluó una sola vez en `05`, con el notebook registrado sin ejecutar antes de abrir test (commit `414d3e0`). **Se cumplen las tres predicciones, así que H se sostiene.**

| Predicción | Test | IC 95 % (bootstrap por persona) |
|---|---|---|
| P1 · AUC dentro de la noche de P_RR (media, 13 noches de 7 personas) | 0,869 | 0,827 a 0,930 |
| P2 · ρ entre el nivel nocturno de la EDR y el % de apnea (20 noches) | 0,658 | 0,117 a 0,786 |
| P3 · AUC de C con todos los minutos | 0,849 | 0,688 a 0,938 |

- **Con el umbral fijo:** sensibilidad 0,709, especificidad 0,834 y exactitud 0,780. En desarrollo, con validación cruzada, eran 0,814, 0,851 y 0,836.
- **C contra F y el RR solo:** C tiene mayor especificidad que las dos y marca menos minutos en los controles. Con la corrección de Holm sobre las 13 comparaciones resisten tres: los controles contra F y contra el RR solo, y la especificidad contra F (`06` §5). En exactitud y AUC no hay diferencia demostrable.
- **Confianza por movimiento:** no separa de forma clara en test.
- **Dónde falla:** los errores son por noche entera. Hay noches con apnea subestimadas (a11, a06, x15) y controles sobreestimados (c08).

Detalle en `notebooks/05_test.ipynb` (sección 6) y en `docs/resultados_test.json`. El análisis posterior de por qué falla en algunas noches está en `notebooks/06_posterior_test.ipynb`: es descriptivo y no cambia estos resultados.

## Alcance

- Se detecta **apnea o hipopnea por minuto**, como las etiquetas de la base. No se distingue apnea de hipopnea ni obstructiva de central.
- **No es un diagnóstico.** La categoría de cada noche (A, B, C) y los minutos de apnea por hora se informan como resultado secundario, no como un índice clínico.
- **Sin aprendizaje automático**: una feature, un umbral. El objetivo es mostrar el fenómeno de forma interpretable, no competir con los métodos del estado del arte.

## Limitaciones a considerar

**De la base**

1. **Tamaño y composición.** 70 registros, 67 sin las grabaciones duplicadas, de 29 personas; 57 de los 67 registros son de hombres. Los resultados pueden no generalizar a mujeres ni a otras poblaciones.
2. **Una sola derivación de ECG a 100 Hz y 12 bits.** El pico R queda cuantizado a 10 ms (se corrige con interpolación) y la EDR depende de dónde quedaron los electrodos, que no se puede controlar.
3. **Etiquetas por minuto de un solo experto.** No dicen dónde empieza ni termina cada evento. En las grabaciones duplicadas, las etiquetas de una misma señal difieren en 1 o 2 minutos: hay ruido en la referencia.
4. **Personas inferidas.** La base no identifica a las personas; se agruparon por perfil (edad, sexo, altura, peso) y por parecido del latido. Un error de agrupación podría poner a una persona en desarrollo y en test.

**Del método**

5. **Ventana de 240 s.** Hace falta para ver oscilaciones de 0,01 Hz, pero diluye los episodios de un solo minuto (22 % de los episodios en desarrollo) y suaviza los bordes de cada episodio.
6. **Minutos excluidos.** El detector no decide en los minutos con más de 20 % de RR corregidos (señal perdida, ritmos irregulares). En pacientes con arritmias frecuentes el método no se puede aplicar.
7. **La EDR solo se valida en 8 registros**, y en la banda lenta solo en los 4 con mucha apnea. Por diseño están todos en desarrollo, así que esa validación no se repite en test.
8. **Las decisiones de preprocesamiento se tomaron mirando desarrollo** (por ejemplo, las mejoras del detector de QRS). Se controlan con la revisión manual y con que ningún registro empeore, pero solo test mide si generalizan.

**De la evaluación**

9. **Test chico: 20 registros de 10 personas.** Los intervalos de confianza son anchos: un resultado no significativo no demuestra que no haya efecto. Además, test quedó con algo menos de hombres y con un índice de masa corporal mayor que desarrollo (31 contra 27; no se controló al partir).
10. **Test ya se usó en la primera entrega.** La evaluación del recuperatorio no es ciega en sentido estricto. Para que no influya, todas las decisiones nuevas se toman solo con desarrollo, se escriben antes de correr test y test se corre una sola vez al final.
11. **Los minutos de una misma noche no son independientes** (los episodios duran una mediana de 6 minutos). Por eso los intervalos de confianza se calculan remuestreando sujetos, no minutos.
12. **El nivel de la EDR también acompaña a la edad y al IMC** (en desarrollo, ρ ≈ 0,4–0,5 en los minutos normales), que a su vez van con la cantidad de apnea. No se puede separar si la parte (b) de la hipótesis refleja la apnea o el tipo de persona que la tiene; test tiene un IMC mayor que desarrollo.
13. **La hipótesis se reformuló después de analizar desarrollo.** C salió de mirar qué mide bien cada señal en esos mismos registros. Lo atenúa que C casi no tiene parámetros (un peso elegido por validación cruzada por personas, que resultó 1, y una mediana sin etiquetas), pero solo test dice si generaliza.
14. **El método supone ritmo sinusal.** En test, una persona (c04 y x29) tiene un ritmo muy irregular. Los latidos se detectan bien, pero la limpieza del RR corrige el 36–41 % de los intervalos y se excluyen la mayoría de sus minutos (`06`, sección 3). Con una arritmia sostenida, la serie RR no refleja la modulación por la apnea.
15. **Los errores son por persona o por noche.** Dependen de dónde queda la vara de cada noche: el nivel de la EDR que no corresponde a su cantidad de apnea, o el nivel general del RR de la persona (`04` sección 11, `06` sección 2). En test el error de cada noche sigue a esas dos cantidades (ρ = 0,67 y 0,75).
