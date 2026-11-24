# Revisión de la devolución, punto por punto

Cada observación de la devolución (nota 3, recuperatorio), dónde se trabajó y en qué estado está. Los notebooks se nombran por su número (`01` = `notebooks/01_base_y_exploracion.ipynb`, etc.). Las decisiones y sus justificaciones están juntas en [`decisiones.md`](decisiones.md); los objetivos y la hipótesis, en [`objetivos_hipotesis.md`](objetivos_hipotesis.md).

**Estados.**
- **Resuelto**: el análisis está hecho y su justificación está en el repositorio.
- **Falta en informe/presentación**: el análisis está en el repositorio, pero todavía hay que llevarlo al informe o a la presentación.
- **Pendiente**: no está hecho.

## Entrega

| Observación | Qué hacer | Estado |
|---|---|---|
| No se entregó a tiempo; se cambió el PowerPoint después de entregar | Entregar informe, presentación y repositorio juntos, en fecha, y no modificar nada después de enviar | Pendiente (es de organización) |

## 1. Introducción

| Observación | Dónde se trabajó | Estado |
|---|---|---|
| **a) Marco teórico.** La presentación no menciona la apnea, su fisiología ni cómo se estudia | La fisiología de la apnea obstructiva y su efecto en el RR y en la respiración está en `01` §6 (ciclos de 20–100 s, Guilleminault et al., 1984) y en `03` §4. Cómo se puntúan las etiquetas a partir de la polisomnografía está en `01` §1; la envolvente de la respiración como referencia, en `03` §4 | Falta en informe/presentación: una sección y una diapositiva de fisiología de la apnea y de su diagnóstico |
| Falta explicar en profundidad la EDR y el acoplamiento, que no se vieron en clase | La EDR: por qué el QRS cambia con la respiración, con figuras y datos de un control (r = 0,93), en `03` §1. Las medidas posibles están en `03` §2 y la validación contra la respiración real en `03` §3–4. El acoplamiento: el espectro cruzado y la coherencia, con su interpretación, en `03` §3 y `04` §1. Por qué el detector final no usa el acoplamiento sino C está en `04` §6 | Falta en informe/presentación |
| **b) Estado del arte.** No está en la presentación y las referencias son viejas | La bibliografía de métodos está en `decisiones.md` §4 | Pendiente: buscar trabajos recientes de detección de apnea con ECG de una derivación (EDR, HRV, Apnea-ECG) para el informe y la presentación |
| **c) Objetivos.** No son claros; el informe pone hipótesis en lugar de objetivos | `objetivos_hipotesis.md`: un objetivo general, cinco específicos (uno por notebook), una sola hipótesis con tres partes y predicciones medibles, alcance y limitaciones | Resuelto en el repositorio. Falta en informe/presentación |
| **d) Base de datos.** No se explican las categorías A, B y C; el criterio de la partición es poco claro | `01` §1: qué es cada categoría según el criterio de PhysioNet (horas con índice de apnea ≥ 10 y minutos con apnea en la noche; describe la noche, no a la persona), con figura. `01` §2: ocho decisiones de la partición, cada una con su verificación (duplicados, sujetos inferidos y verificados con la forma del latido, partición por persona, estratificación, balance de apnea, tabla de verificación) | Resuelto. Falta en informe/presentación |

## 2. Materiales y métodos

### a) Preprocesamiento

| Observación | Dónde se trabajó | Estado |
|---|---|---|
| La especificación del filtro no tiene espectrograma ni análisis temporal que la respalde | `01` §5: PSD de cada registro, espectrograma de una noche y problemas en el tiempo. `02` §1: la especificación medida en desarrollo, la respuesta del filtro y su efecto en el tiempo sobre registros reales. Justificación bibliográfica del corte de 0,5 Hz (Kligfield et al., 2007) | Resuelto |
| Falta una exploración sistemática de los registros, con sus artefactos en tiempo y frecuencia, que justifique aplicar el mismo preprocesamiento a todos | `01` §4–5: ejemplos de ECG con cada problema, tabla de calidad por registro (saturación, tramos planos, ruido, deriva) y figura de problemas a lo largo de la noche. Las consecuencias para el preprocesamiento están en `01` §8 | Resuelto |
| No hay análisis que justifique refinar el pico R a 100 Hz | `02` §3: el error de cuantización (±5 ms en el pico, ±10 ms en el RR) y la prueba de dos fases a 50 Hz (el desacuerdo baja de ~10 a 2,5 ms). También se muestra que en la banda de la feature el efecto es chico | Resuelto |

### b) Procesamiento y extracción de características

| Observación | Dónde se trabajó | Estado |
|---|---|---|
| **Latidos.** Decisiones sin analizar: la tolerancia de ±100 ms y la interpolación de los QRS no detectados | Tolerancia: `02` §2, figura de acuerdo según la tolerancia (de 30 a 150 ms cambia < 1 punto; AAMI EC57 usa 150 ms). Interpolación: `02` §4, distribución del RR respecto de sus vecinos, verificación con etiquetas (no corrige más en apnea) y comparación con reglas más laxas | Resuelto |
| **Latidos.** No se muestra el desempeño del detector ni dónde falla, cuantitativa y cualitativamente | `02` §2: acuerdo con las marcas de la base, revisión manual de 50 casos, figuras de los casos donde falla cada fuente, cinco mejoras con su ablación y su sensibilidad, verificación en todo desarrollo (19/20 detecciones falsas eliminadas y 17/18 verdaderas conservadas en la revisión manual) | Resuelto |
| **Realizaciones y Wiener.** No queda claro por qué se hace, cómo se eligen las ventanas ni su relación con la EDR; no hay citas | `03` §5: por qué (el ruido sobre el QRS entra en la EDR), qué es un latido como realización, de dónde sale la ventana de −250 a +400 ms (el largo de un latido, no una ventana de análisis), el H(f) de los 47 registros y la excepción de `x17`. Su efecto en la EDR se mide en `03` §6 con tres medidas y bootstrap pareado. Citas: Wiener (1949), Sörnmo y Laguna (2005) | Resuelto |
| **Wiener.** La sección siguiente usa otra ventana sin justificar | Hay una sola ventana de análisis (240 s) en todo el trabajo. Las otras duraciones son largos de objetos (latido, QRS) y están en `decisiones.md` §1. La robustez entre 180 y 360 s está en `04` §15 | Resuelto |
| **Features.** No se justifica la EDR frente a la deriva de la línea de base | `03` §2: las tres medidas (área, amplitud R, deriva) con figura. `03` §6: comparación de todas las variantes con coherencia contra la respiración, coherencia con la envolvente y AUC dentro de la noche. La deriva y la combinación área + deriva salen peor | Resuelto |
| **Features.** Por qué remuestrear a 2 Hz con interpolación cúbica | `04` §1 (y `decisiones.md` §3): la serie es irregular y Welch necesita muestras equiespaciadas; 2 Hz supera la frecuencia cardíaca (0,8–1,4 Hz) y su Nyquist cubre la respiración. `04` §15: cúbica y lineal dan lo mismo | Resuelto |
| **Features.** En qué se basa F (potencia cruzada) | `04` §1 define el espectro cruzado y qué mide. `04` §6 muestra con datos que F casi es el promedio de las dos potencias (r = 0,985) y que cada señal mide algo distinto: el RR, cuándo hay apnea dentro de la noche; el nivel de la EDR, cuánta apnea tiene la noche. Por eso F se reemplazó por C, que combina las dos de forma explícita (`04` §7). F queda solo como comparación | Resuelto |
| **Features.** Qué paper respalda la referencia de Lomb; se introduce otra ventana | Lomb (1976), Laguna et al. (1998) y Task Force (1996), en `04` §1. El RR con Lomb se calcula ahora con la misma ventana de 240 s y la misma banda | Resuelto |
| **Features.** Por qué Youden | `04` §9: no hay costos definidos para cada error, el detector no es un diagnóstico y las clases tienen tamaños parecidos (Youden, 1950; Fluss et al., 2005). Se muestra la curva ROC con el punto elegido | Resuelto |
| **Features.** ¿Una sola feature? No queda clara la longitud del segmento ni por qué alcanzaría una feature | `04` §1 ("Qué se clasifica"): la unidad es el minuto (las etiquetas son por minuto) y la ventana de 240 s es su contexto. `04` §8: C junta dos señales, y agregar más términos, incluso una regresión logística con cuatro, no mejora con personas no vistas | Resuelto |
| **Estadística.** No se explica cómo se calcula el acoplamiento ni por qué usarlo | `04` §1 (espectro cruzado) y `03` §3 (coherencia y por qué puede ser alta donde los espectros difieren). La hipótesis ya no depende del acoplamiento; por qué, en `04` §6 | Resuelto |
| **Estadística.** Muchas medidas sin explicar qué son ni cómo se calculan | `04`, sección "Cómo se evalúa": sensibilidad, especificidad, exactitud, ROC/AUC, AUC dentro de la noche, Youden, Spearman, bootstrap por personas y validación cruzada por personas, cada una con qué mide y cómo se calcula | Resuelto. Falta en informe |

## 3. Resultados

| Observación | Dónde se trabajó | Estado |
|---|---|---|
| **a) Análisis visual.** No hay gráficos de resultados | `04`: la noche de `a03` con C, el umbral y las etiquetas (`04_noche_a03`), el AUC dentro de cada noche, la ROC, el umbral, el % de apnea estimado contra el real por noche (`04_por_noche`), las noches donde falla (`04_fallas_noches`) y la confianza según el movimiento. Para el detector final en test, `12`: resultados por minuto, noche, persona, categoría y base, cada uno con su figura, y los errores explicados con las señales | Resuelto. Falta en informe/presentación |
| **b) La Tabla 2 no es adecuada; las afirmaciones no tienen respaldo** | Cada resultado de `04` tiene su tabla con intervalos de confianza por bootstrap de personas y su figura. Las comparaciones son pareadas (por ejemplo, C contra cada alternativa en §8) | Resuelto. Falta rehacer la tabla de resultados del informe |
| No hay tablas ni visualizaciones para interpretar los resultados; no se introducen las técnicas de evaluación | Ver arriba, y la sección "Cómo se evalúa" de `04` | Resuelto. Falta en informe |
| No queda claro el nivel de cada análisis (ventana, señal, sujeto, grupo, base) | `04`, sección "Cómo se evalúa": tabla de niveles (minuto, noche, persona, categoría, base) y en qué resultados aparece cada uno. `04` §5 muestra por qué el resultado cambia según el nivel | Resuelto |
| No queda claro qué se ajusta en train y qué se evalúa en test | `04`, "Cómo se evalúa": tabla de qué se ajusta, cómo y con qué datos. `04` §14 y `docs/parametros_test.json`: los parámetros congelados (μ, σ, w, umbral y cortes de confianza). Test no se usó para nada hasta `05`, que se corrió una sola vez después de registrar el notebook sin ejecutar (commit `414d3e0`) | Resuelto |

## 4. Conclusiones

| Observación | Dónde se trabajó | Estado |
|---|---|---|
| No hay un hilo entre los resultados | Los notebooks siguen un solo camino: `01` explora y mide la banda; `02` obtiene la serie RR; `03` la EDR; `04` arma C, la evalúa y fija los parámetros. Cada notebook termina con una tabla de lo que se lleva el siguiente. La hipótesis H tiene predicciones P1–P3 que se verifican en `04` §14 y se prueban en `05`: las tres se cumplen en test | Resuelto en el repositorio. Falta en informe: conclusiones que respondan P1–P3 con los resultados de test (`05` §6) |

## 5. Interfaz gráfica

| Observación | Estado |
|---|---|
| No hay interfaz | Resuelto: `app/visor.py` (`streamlit run app/visor.py`). Para una noche muestra C con el umbral, la decisión, la confianza y las etiquetas. Para cada minuto muestra el ECG con los picos R, la serie RR y la EDR en su ventana, los espectros con la banda y el cálculo de C. Permite saltar entre los minutos mal clasificados. Solo muestra registros de desarrollo |

## Informe y código

| Observación | Dónde se trabajó | Estado |
|---|---|---|
| Informe prolijo pero sin hilo conductor | La estructura sigue a los notebooks y a la hipótesis | Pendiente: reescribir el informe |
| El código cuesta entender: etapas y qué partes aportan al análisis final | README con el pipeline actual, notebook por notebook. Los módulos que el pipeline actual no usa están marcados como de la primera versión. Las constantes están en `src/config.py`, con referencias al notebook que las justifica | Resuelto |

## Defensa oral

| Observación | Estado |
|---|---|
| Faltó participación de Leah (puede presentar en inglés) | Pendiente: repartir la presentación en tres partes parecidas |
| No se cumplió el tiempo | Pendiente: ensayar con cronómetro y dejar fuera lo que no sostiene la hipótesis |
| No se transmitió conocimiento de la materia | Pendiente: guía de estudio para que los tres puedan explicar cada técnica (filtro, Pan-Tompkins, Wiener, Welch, espectro cruzado, ROC, bootstrap) a nivel señal y a nivel base |

## Comentario final

| Pedido | Cómo se respondió |
|---|---|
| Limitar el alcance a una sola hipótesis | Una hipótesis H, con tres partes y tres predicciones (`objetivos_hipotesis.md`) |
| Construirla en forma escalonada y clara | `01` → `02` → `03` → `04`, cada paso usa lo anterior |
| Justificar cada decisión con análisis cualitativo y cuantitativo de las señales | Cada decisión tiene figura y número en su notebook; resumen en `decisiones.md` |
| Fundamentar los umbrales en bibliografía | `decisiones.md` y `auditoria_decisiones.md`: las 88 decisiones con su justificación (86 justificadas con datos, bibliografía o física; 2 limitaciones declaradas). Cada umbral propio tiene su sensibilidad medida, y cada cita tiene DOI o página oficial verificados (`referencias.md`) |
| Consistencia en las ventanas | Una sola ventana de análisis, 240 s, con robustez verificada (`04` §15). Todas las constantes (ventana, banda, grilla, reglas del RR, mínimo de minutos) están en un solo lugar y `tests/test_consistencia.py` falla si un notebook las vuelve a escribir a mano |
| Explicar las técnicas y métricas fuera de lo visto en clase | EDR (`03` §1–2), espectro cruzado y coherencia (`03` §3, `04` §1), Lomb (`04` §1), métricas (`04`, "Cómo se evalúa") |
| Visualizar las señales y sus derivados | ECG crudo y filtrado, espectros, espectrograma, serie RR, EDR contra respiración, espectros con y sin apnea, C en una noche |
| Que todos puedan explicar las técnicas | Pendiente: guía de estudio y ensayo |

## Resumen de lo que falta

1. **Informe**: marco teórico (apnea, EDR, acoplamiento), estado del arte con referencias recientes, objetivos, métodos siguiendo `01`–`04`, resultados con figuras y conclusiones según P1–P3.
2. **Presentación y defensa**: diapositiva de fisiología de la apnea, reparto entre los tres, tiempo ensayado y guía de estudio.
