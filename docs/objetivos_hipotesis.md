# Objetivos, hipótesis y limitaciones

Documento de referencia para el informe, la presentación y los notebooks. Responde a la devolución: los objetivos tienen que estar separados de la hipótesis, tiene que haber **una sola hipótesis** demostrada paso a paso y las limitaciones tienen que estar explícitas.

## Objetivo general

Desarrollar y evaluar un método de procesamiento de señales que detecte, **minuto a minuto**, la presencia de apnea del sueño a partir de un **ECG de una derivación**, usando la variación conjunta de la frecuencia cardíaca y de la respiración derivada del ECG, con una única feature y un umbral (sin aprendizaje automático).

## Objetivos específicos

Cada objetivo es un paso del trabajo, tiene un resultado medible y un notebook donde se resuelve.

| # | Objetivo | Resultado que lo cumple | Notebook |
|---|---|---|---|
| 1 | Caracterizar la base Apnea-ECG: etiquetas, categorías, calidad y artefactos de las señales en tiempo y frecuencia | Requisitos del preprocesamiento justificados con figuras y medidas por registro | `01` |
| 2 | Diseñar un filtro a partir del espectro del ECG y obtener la serie RR con un detector de QRS propio | Filtro que cumple una especificación sacada de los datos; detector validado contra las marcas de la base y con revisión manual | `02` |
| 3 | Obtener la respiración derivada del ECG (EDR) y medir cuánto se parece a la respiración registrada; evaluar si el filtro de Wiener la mejora | Coherencia EDR–respiración en la banda respiratoria y en la banda del ciclo de apnea, para cada variante | `03` |
| 4 | Identificar en qué banda de frecuencias la apnea modifica la serie RR y la EDR, y construir con ella una feature por minuto | Banda medida en desarrollo; feature definida con una ventana única | `01`, `04` |
| 5 | Fijar el umbral de decisión en desarrollo y evaluar el detector una única vez en los sujetos de test | Sensibilidad, especificidad, AUC por minuto y error por noche, con intervalos de confianza por sujeto | `04` |

## Hipótesis

**H.** Durante la apnea, la frecuencia cardíaca y la respiración oscilan juntas al ritmo del ciclo apnea–recuperación (períodos de ~20 a 100 s). Por eso, **en los minutos con apnea la potencia cruzada entre la serie RR y la EDR en la banda de 0,01 a 0,05 Hz es mayor que en los minutos normales, y alcanza para clasificar cada minuto con un único umbral**.

**Cómo se pone a prueba** (definido antes de mirar test):

- **Feature.** F = logaritmo de la potencia cruzada RR–EDR promediada en la banda, estimada por Welch en una ventana de 240 s centrada en cada minuto. Es la misma ventana para todo el trabajo.
- **Predicción 1: el fenómeno existe dentro de cada noche.** En los registros de desarrollo con los dos tipos de minuto, F es mayor en los minutos con apnea que en los normales del mismo registro: AUC dentro de la noche mayor que 0,5 en la mayoría de los registros. Se mide por registro para que no influya que una persona tenga más apnea o más variabilidad que otra.
- **Predicción 2: alcanza para detectar.** Con el umbral fijado en desarrollo, en test el AUC por minuto de F es mayor que 0,5 y su intervalo de confianza al 95 % (bootstrap por sujeto) no incluye 0,5. Se informan sensibilidad, especificidad y exactitud con ese umbral.
- **H se sostiene** si se cumplen las dos predicciones. Si se cumple solo la primera, el fenómeno existe pero no alcanza para detectar con un umbral.

**Pregunta secundaria (descriptiva, no es una hipótesis):** ¿la EDR aporta información sobre la apnea que no está en la serie RR sola? Se compara F con la potencia del RR solo en la misma banda y la misma ventana. La exploración (`01`) muestra que el RR solo ya tiene un contraste grande entre apnea y normal; por eso la respuesta no se da por supuesta. Si en desarrollo la feature cambiara, el cambio se escribe acá antes de correr test.

## Alcance

- Se detecta **apnea o hipopnea por minuto**, como las etiquetas de la base. No se distingue apnea de hipopnea ni obstructiva de central.
- **No es un diagnóstico.** La categoría de cada noche (A, B, C) y los minutos de apnea por hora se informan como resultado secundario, no como un índice clínico.
- **Sin aprendizaje automático**: una feature, un umbral. El objetivo es mostrar el fenómeno de forma interpretable, no competir con los métodos del estado del arte.

## Limitaciones a considerar

**De la base**

1. **Tamaño y composición.** 70 registros, 67 sin las grabaciones duplicadas, de 29 personas; 57 de los 67 registros son de hombres. Los resultados pueden no generalizar a mujeres ni a otras poblaciones.
2. **Una sola derivación de ECG a 100 Hz y 12 bits.** El pico R queda cuantizado a 10 ms (se corrige con interpolación) y la EDR depende de dónde quedaron los electrodos, que no se puede controlar.
3. **Etiquetas por minuto de un solo experto.** No dicen dónde empieza ni termina cada evento. En las grabaciones duplicadas las etiquetas difieren en 1 a 3 minutos: hay ruido en la referencia.
4. **Sujetos inferidos.** La base no identifica a las personas; se agruparon por perfil (edad, sexo, altura, peso) y por parecido del latido. Un error de agrupación podría poner a una persona en desarrollo y en test.

**Del método**

5. **Ventana de 240 s.** Hace falta para ver oscilaciones de 0,01 Hz, pero diluye los episodios de un solo minuto (22 % de los episodios en desarrollo) y suaviza los bordes de cada episodio.
6. **Minutos excluidos.** El detector no decide en los minutos con más de 20 % de RR corregidos (señal perdida, ritmos irregulares). En pacientes con arritmias frecuentes el método no se puede aplicar.
7. **La EDR solo se valida en 8 registros**, y en la banda lenta solo en los 4 con mucha apnea. Por diseño están todos en desarrollo, así que esa validación no se repite en test.
8. **Las decisiones de preprocesamiento se tomaron mirando desarrollo** (por ejemplo, las mejoras del detector de QRS). Se controlan con la revisión manual y con que ningún registro empeore, pero solo test mide si generalizan.

**De la evaluación**

9. **Test chico: 20 registros de 10 personas.** Los intervalos de confianza son anchos: un resultado no significativo no demuestra que no haya efecto.
10. **Test ya se usó en la primera entrega.** La evaluación del recuperatorio no es ciega en sentido estricto. Para que no influya, todas las decisiones nuevas se toman solo con desarrollo, se escriben antes de correr test y test se corre una sola vez al final.
11. **Los minutos de una misma noche no son independientes** (los episodios duran una mediana de 6 minutos). Por eso los intervalos de confianza se calculan remuestreando sujetos, no minutos.
