# Esquema general v3 — TPS PSIB 2026Q2, Grupo 08 (Frate, Tenca, Weizman)
## Acoplamiento cardiopulmonar derivado del ECG como criterio de detección de apnea del sueño

> **Estado al 20/10/2026.** Reemplaza al esquema v2. Todo lo que dice este documento está medido en los registros de desarrollo y tiene su notebook; lo que es una decisión de criterio, y no de datos, se marca como tal.
>
> **Cambios principales respecto de v2:** H1 se reformula (con apnea **aparece** un acoplamiento lento; el respiratorio no se pierde). El detector ya no es el cociente de coherencias CR sino **F = log de la potencia cruzada RR–EDR en 0,01–0,05 Hz**, en una ventana de 4 min. El EDR es el **área del QRS**. No se normaliza por noche. La referencia de H2 es la **mejor HRV elegida con datos** (VLF con Lomb), no el LF/HF. La partición es **por sujeto**, sin las grabaciones duplicadas. El filtro pasa a 0,5–45 Hz, orden 3. La base es de **12 bits**, no de 16. Las elecciones usan una **regla de no inferioridad**, y test tiene un plan cerrado (`docs/plan_test.md`).

---

### 0. Cómo usar este documento

- La sección 8 es el checklist: qué está hecho y, para lo que falta, qué hay que hacer, qué ya existe en el repo, qué hay que escribir y cuándo está terminado.
- Antes de cambiar cualquier cosa del pipeline, leer la sección 7. Son los criterios que se aplicaron en todas las etapas y que tienen que seguir valiendo.
- **Sobre test manda `docs/plan_test.md`.** Si este esquema y el plan dicen cosas distintas sobre test, vale el plan.
- Los números de desarrollo son **optimistas**: se usaron para elegir. La estimación honesta sale de la validación cruzada anidada (sección 8) y de test.

---

### 1. Restricciones

| Origen | Restricción |
|---|---|
| Consigna | Temas obligatorios: adquisición, filtros convencionales, filtros óptimos, segmentación, recorte en realizaciones, QRS, HRV, Lomb |
| Consigna | Informe de 8 páginas como máximo (+4 de anexo); repo con README, requirements y **commits balanceados**; defensa de 15–20 min donde todos responden sobre todo |
| Consigna | Fechas: avance obligatorio 27/10 (preprocesamiento y features); entrega 10/11 a las 17:00 (PDF, presentación y link al repo); defensa alrededor del 19 o el 26/11 |
| Devolución | Sin aprendizaje automático: los puntos de corte salen de un análisis estadístico justificado. **Umbral por índice de Youden** (lo pidió la docente) |
| Devolución | El análisis tiene que ser nuevo respecto de cuatrimestres anteriores |
| Devolución | Partición 70/30 |
| Propia | Para detectar se usa solo el ECG; la respiración real se usa solo para validar |
| Propia | Toda decisión se justifica con datos de desarrollo. Si no se puede decidir con datos, se declara como decisión de criterio |
| Propia | Test se usa **una sola vez**, con el plan de `docs/plan_test.md` |

---

### 2. Hipótesis

**H1 (reformulada).** Durante la apnea **aparece un acoplamiento lento** entre la serie RR y el EDR (respiración derivada del ECG), en la banda del ciclo de apnea (0,01–0,1 Hz, un ciclo cada 10–100 s), dentro de cada sujeto. El acoplamiento respiratorio (0,15–0,4 Hz) no desaparece.

- v2 decía que el acoplamiento se **desplazaba** de HF a VLF/LF. Los datos muestran otra cosa: la coherencia lenta sube, pero la respiratoria no baja (E2).
- **Estado:** se sostiene en desarrollo (E2, sección 5).

**H2 (reformulada).** La feature conjunta RR–EDR (F) detecta la apnea mejor que la mejor feature de HRV, que usa solo el RR.

- La referencia ya no es el LF/HF fijo: es la mejor HRV elegida con la misma regla que F (E4: potencia VLF del RR con Lomb, AUC 0,810; el LF/HF da 0,73). La comparación es más exigente para F.
- Se mide con dos medidas principales (`docs/plan_test.md`, sección 5): **M1**, el AUC por minuto con todos los minutos juntos, y **M2**, el acierto por registro (Spearman entre la fracción de apnea estimada y la real). Las dos van corregidas por Holm.
- **Estado:** se decide en test. Vista previa en desarrollo: AUC 0,876 contra 0,810 (diferencia 0,066; IC −0,004 a +0,142) y acierto por registro 0,81 contra 0,42 (diferencia significativa).

**Aporte original.** No es la sincronía entre las señales (la coherencia no aporta para detectar, sección 5). Es **sumar al RR la respiración derivada del ECG en la banda del ciclo de apnea**. Se nota sobre todo al estimar **cuánta** apnea tiene cada noche.

---

### 3. Datos y partición

- **Base:** Apnea-ECG (PhysioNet), Opción 11 de la consigna. 70 registros nocturnos, con una etiqueta de apnea o normal por minuto.
- **Grabaciones duplicadas:** c05 = c06 (documentado por PhysioNet), x22 = x35 y x33 = x34 (encontrados comparando las señales). Se excluyen c05, x22 y x33. Quedan **67 registros**.
- **Sujetos:** se agrupan los registros con el mismo perfil (edad, sexo, altura, peso) **o** que son la misma grabación. Quedan **29 sujetos**. Los perfiles repetidos no son casualidad (p ≈ 0,0001), y el ECG lo confirma: el r mediano entre latidos promedio es 0,94 dentro del sujeto y 0,74 entre sujetos. Algunos registros tienen la **polaridad invertida**, así que ningún paso puede suponer que el pico R es positivo (`01_verificacion_sujetos.ipynb`).
- **Partición por sujeto**, con cuatro condiciones (`src/split.py`):
  1. sujetos enteros;
  2. los sujetos con respiración real, en desarrollo;
  3. cuotas exactas por categoría;
  4. una fracción de minutos de apnea que difiera 2 puntos o menos entre conjuntos.

  Hay 853 particiones válidas y se eligió una al azar con semilla 2026 (`data/split.csv`, commit `8d4ca2f`). No se toca más.

| | A | B | C | Registros | Sujetos |
|---|---|---|---|---|---|
| Desarrollo | 28 | 7 | 12 | 47 | 19 |
| Test | 12 | 3 | 5 | 20 | 10 |

- **Categoría:** A tiene 100 o más minutos de apnea, B de 5 a 99 y C menos de 5. Esta regla reproduce la letra oficial de los 35 registros de aprendizaje.
- **De test no se calcula nada**, ni siquiera estadísticas de sus etiquetas, hasta abrirlo.

---

### 4. Pipeline vigente

| Paso | Valor vigente | Estado | Dónde |
|---|---|---|---|
| Filtro | Butterworth pasabanda 0,5–45 Hz, orden 3, ida y vuelta (`config.ECG_FILTER`) | ✓ 4.2 | `07_filtro.ipynb` |
| Latidos | marcas `.qrs` de la base; el pico R se busca a ±30 ms con la polaridad del registro y se refina con una parábola de 3 puntos | refinamiento ✓ 4.1; detector propio pendiente (4.3) | `00_adquisicion.ipynb` |
| Wiener | no se aplica todavía | pendiente (4.4) | — |
| RR | se corrige si está fuera de 0,3–2 s o si se aparta más de 20 % de la mediana de 11 vecinos; se interpola | vigente (supuesto, ver 4.5) | `src/qrs/rr_clean.py` |
| Minutos evaluados | con etiqueta, con 20 % o menos de RR corregidos y con la feature calculable | vigente (supuesto, ver 4.5) | `plan_test.md` §4 |
| EDR | área con signo del QRS (±60 ms del centro, polaridad medida en cada registro), sobre el ECG filtrado | ✓ E1 + E3a | `02_E1_edr.ipynb` |
| Remuestreo | RR y EDR a 2 Hz con interpolación cúbica | ✓ (lineal da el mismo ranking, E1) | `src/features/coupling.py` |
| **F (detector)** | log de la potencia cruzada RR–EDR promediada en 0,01–0,05 Hz; ventana de **240 s** centrada en cada minuto; Welch con 3 segmentos y 50 % de solapamiento; sin normalizar ni suavizar | ✓ E3a + E3b | `04`, `06` |
| HRV de referencia | potencia del RR en VLF (0,01–0,04 Hz) con periodograma de Lomb, ventana de 180 s; sin normalizar ni suavizar | ✓ E4 + E3b | `04`, `06` |
| Umbral | índice de Youden en desarrollo; un minuto es apnea si F ≥ umbral | pendiente | — |

Números vigentes de F en desarrollo (con el filtro de 4.2, sobre los 22.123 minutos de evaluación de E3a): AUC **0,875** y acierto por registro **0,810**.

**4.1 Adquisición ✓** (`00_adquisicion.ipynb`)
- **Medido en los 47 registros:** 100 Hz, ganancia de 200 unidades por mV (5 µV por paso) y conversor de **12 bits**, guardado en formato de 16 bits. Los valores van de −2048 a 2047. v2 decía 16 bits.
- **Citado** (los archivos no lo dicen): las etiquetas las puso un experto a partir de la polisomnografía (Penzel et al., 2000); las `.qrs` son automáticas y no están auditadas; la derivación.
- **Desarrollo:** de 6,8 a 9,6 h por noche; 23.138 minutos con etiqueta, 39,8 % con apnea. Un detector que dice siempre "normal" acierta el 60 % de los minutos.
- **Minutos con apnea contra AHI:** Spearman 0,94 (IC 0,84 a 0,97). La categoría B es la menos consistente con la clínica: sus registros van de un AHI de 0,1 a 33.
- **Cuantización a 10 ms:** la parábola mueve cada pico con un desvío de 2,65 ms (2,9 ms para un error uniforme). En la prueba de dos fases a 50 Hz baja el desacuerdo de 10,0 a 2,5 ms, en los 19 sujetos, así que se queda. No cambia F ni la HRV de referencia, pero sin ella el RMSSD sube un 4 % (13 % en los minutos de RMSSD bajo).
- **Saturación = señal perdida:** casi todo lo saturado está en tramos clavados en el tope del conversor (hasta 245 s), y solo el 0,03 % de los latidos tiene el QRS saturado. 91 minutos (0,4 %) tienen algo de señal perdida y la regla del 20 % deja pasar 40. No se asocia con la apnea.

**4.2 Filtro convencional ✓** (`07_filtro.ipynb`)
- **Especificación sacada de desarrollo, sin etiquetas:** el ritmo más bajo es 0,77 Hz y el 99 % de la energía del latido queda bajo 41,8 Hz. Se pide atenuar 1 dB o menos en esa banda y 20 dB o más a 0,1 Hz, con la ganancia ida y vuelta.
- El filtro de v2 (0,5–40 Hz, orden 2) atenuaba 10,4 dB a 41,8 Hz. Ganó el de menor orden que cumple.
- **Verificación:** F no inferior (AUC 0,876 → 0,875; acierto 0,813 → 0,810). Control E1: 0,531 → 0,520.

**4.3 Detección QRS: pendiente** (sección 8).

**4.4 Recorte en realizaciones y Wiener: pendiente** (sección 8).
- Por qué no borra el EDR (vale lo de v2): un filtro LTI aplica la misma ganancia a todos los latidos. Lo que no se hace es promediar latidos ni empujarlos hacia el template.

**4.5 Limpieza de RR y minutos malos**
- Las reglas del RR y la del 20 % de minutos corregidos vienen de v2 y **no se verificaron con datos**.
- **Medido en 4.1:** la regla del 20 % excluye una mediana de 0,2 % de los minutos por registro, pero a02 pierde el 41 % y x17 el 27 %. Saca algo más de minutos con apnea que normales (3,5 % contra 2,3 %; IC de la diferencia −2,8 a +6,8 puntos). No ve la señal perdida.
- La política se decide antes de los umbrales (sección 8).

**4.6 Segmentación ✓**
- La unidad de decisión es **1 minuto**, alineado con las etiquetas.
- La feature usa una ventana de **240 s centrada** en el minuto, elegida en E3a/E3b entre 3, 4, 5, 6, 7 y 8,5 min. Con 3 segmentos de 120 s, la resolución es de 0,008 Hz, menor que el 0,01 Hz del borde de la banda.
- **Costo, a reportar:** la ventana mezcla minutos vecinos, y en los bordes de la noche hay minutos sin feature.
- La ventana de 512 s (8,5 min) quedó solo para la prueba de H1 (E2), que reproduce el CPC publicado.

**4.7 Features ✓**
- **F**, la potencia cruzada (ver la tabla). Lo que detecta es **cuánto oscilan juntos** RR y EDR en la banda de apnea, no qué tan sincronizados están.
- **Descartados con datos:**
  - el cociente de coherencias CR y la coherencia sola (AUC 0,63);
  - la normalización por noche (empeora el AUC de 0,876 a 0,68–0,73);
  - el suavizado (cambia menos de 0,005).
- **Ya no aplica:** el piso de ruido de la coherencia por *surrogates*, porque F no usa la coherencia. `surrogate_floor` queda sin implementar y se declara en el informe.
- **Lomb y Welch conviven:** Lomb da el espectro de HRV sobre el RR irregular, sin interpolar. Welch necesita muestreo uniforme para el espectro cruzado.

**4.8 Validación del EDR ✓** (`02_E1_edr.ipynb`, `03_E2_h1.ipynb`)
- Con los 8 registros con respiración real, el área del QRS da 0,53 de coherencia con la respiración, contra 0,16 por azar. Con el filtro de 4.2 da 0,520.
- Con la respiración real en lugar del EDR, el efecto de H1 aparece en los 5 registros con apnea y casi siempre es mayor: es fisiológico, y el EDR lo capta atenuado.

---

### 5. Experimentos hechos y qué respondieron

| Etapa | Pregunta | Respuesta | Números clave | Notebook |
|---|---|---|---|---|
| Sujetos | ¿Hay registros de la misma persona o la misma grabación? | Sí: 3 grabaciones duplicadas; 67 registros de 29 sujetos | p ≈ 0,0001 para los perfiles; r 0,94 dentro del sujeto contra 0,74 entre sujetos | `01` |
| E1 | ¿Qué EDR reproduce mejor la respiración? | Área del QRS con pasabanda, empatada con la deriva de línea de base; el empate se resuelve en E3 | 0,531 contra 0,449; azar 0,16 | `02` |
| E2 | ¿Se ve H1? | Sí, como un acoplamiento lento que se agrega | CPC: 11 de 14 sujetos, rango-biserial 0,81, Holm p = 0,011; coherencia respiratoria: 8 de 14, Holm p = 1; 36 de 36 configuraciones en la dirección de H1 | `03` |
| E3a / E4 | ¿Cómo se calcula F? ¿Cuál es la mejor HRV? | Potencia cruzada RR–EDR en 0,01–0,05 Hz; HRV: VLF con Lomb | F 0,871; en validación cruzada, 0,85 en los sujetos de afuera y la misma configuración en los 5 grupos; la configuración publicada da 0,60 | `04` |
| Control E3a | ¿Qué parte de F detecta? | La potencia, no la coherencia; RR y EDR solos detectan parecido | sin coherencia 0,874 contra 0,871; RR solo 0,817; EDR solo 0,822 | `05` |
| E3b | ¿Normalizar o suavizar? | Ninguna de las dos; ventana de 4 min | F 0,876 (IC 0,81 a 0,93); acierto por registro F 0,81 contra HRV 0,42 | `06` |
| 4.2 | ¿El filtro cumple la especificación? | No; pasa a 0,5–45 Hz, orden 3 | F no inferior | `07` |
| 4.1 | ¿Qué dicen los archivos? ¿Sirve el refinamiento? | 12 bits; el refinamiento recupera el tiempo entre muestras | 10,0 → 2,5 ms | `00` |

---

### 6. Cambios respecto de v2

| Tema | v2 | v3 | Por qué |
|---|---|---|---|
| H1 | el acoplamiento migra de HF a VLF/LF | aparece un acoplamiento lento; el respiratorio no baja | E2: la coherencia lenta sube en 11–12 de 14 sujetos; la respiratoria no baja (Holm p = 1) |
| Detector | CR = coherencia(VLF+LF) / coherencia(HF) | F = log potencia cruzada en 0,01–0,05 Hz | E3a: F 0,871; la configuración publicada da 0,60 en los sujetos de afuera; la coherencia sola, 0,63 |
| Referencia de H2 | LF/HF | la mejor HRV elegida con la misma regla (VLF con Lomb) | E4: LF/HF 0,73, VLF 0,81. Es una comparación más exigente |
| Prueba de H2 | Wilcoxon sobre AUC por sujeto | M1 (AUC con todos los minutos) y M2 (acierto por registro); bootstrap por sujeto de 10.000 remuestreos; Holm | El detector usa un único umbral para todos: importa el AUC con todos los minutos juntos, no por sujeto (`plan_test.md`) |
| Prueba de H1 | Shapiro → t pareada o Wilcoxon | Wilcoxon de rangos con signo, directo | **Criterio:** con 14 sujetos el Shapiro tiene poca potencia, y elegir el test según un pretest distorsiona el error tipo I |
| EDR | amplitud del pico R | área del QRS sobre el ECG filtrado | E1: área 0,53 contra amplitud 0,38; E3a: las 17 mejores candidatas usan el área |
| Ventana | ~8,5 min | 4 min | E3a/E3b |
| Normalización | z-score por registro | ninguna | E3b: empeora en todas las familias |
| Piso de coherencia | *surrogates* | no aplica | F no usa coherencia |
| Filtro | 0,5–40 Hz, orden 2 | 0,5–45 Hz, orden 3 | 4.2 |
| Resolución | 16 bits | 12 bits (formato de 16) | 4.1 |
| Partición | por registro: 49 / 21 | por sujeto, sin duplicados: 47 / 20 (19 / 10 sujetos) | registros de la misma persona en los dos conjuntos inflarían test |
| Regla de elección | empate si el IC de la diferencia incluye 0 | no inferioridad con δ = 0,02 | E3a: la regla original metía candidatas ruidosas (optimismo de 0,064 contra 0,021) |
| Detector propio | Plan B si no llega a Se/VPP ≥ 99 % | decide la no inferioridad de F; Se/VPP se reportan | **Criterio:** el 99 % era supuesto; lo que importa es que no empeore la detección |
| Test | evaluación final | plan cerrado, con condiciones para abrirlo | `plan_test.md` |

---

### 7. Criterios de trabajo (valen para todo lo que falta)

**7.1 Cómo se decide**
1. **Solo con desarrollo.** Test no se mira ni se describe.
2. **Reglas antes de correr.** Cada notebook empieza con la pregunta y las reglas: candidatas, métrica, cómo se elige y qué se hace si hay empate. Se escriben antes de ejecutar.
3. **Si después de ver los datos hay que cambiar una regla,** se declara como desvío en el notebook, con su motivo. Si afecta a test, se agrega además en `plan_test.md`, sección 9, con fecha. Nunca se reescribe lo anterior.
4. **Datos o criterio.** Si algo no se puede decidir con datos, se dice que es una decisión de criterio y por qué.
5. **Sin supuestos heredados.** Lo que viene del esquema v2 o de la literatura se verifica antes de usarlo; si no se puede, se marca como supuesto.

**7.2 Estadística**
- **La unidad es el sujeto.** Los minutos de una misma persona no son independientes. La incertidumbre sale de un **bootstrap por sujeto**: se remuestrean sujetos enteros, con 2.000 remuestreos en desarrollo y 10.000 en test.
- **AUC por minuto con todos los minutos juntos**, porque el detector usa un único umbral para todos (`compare_variants`, que es rápido gracias al truco de la matriz de pares).
- **Acierto por registro:** Spearman entre la fracción de apnea estimada (minutos con feature ≥ umbral de Youden) y la real (`agreement_compare`). Acepta otra referencia, como el AHI.
- **Sentido de cada feature:** se fija con los datos de elección para que "más alto = más apnea" (`orient`).
- **Pruebas de hipótesis:** Wilcoxon de rangos con signo por sujeto, de dos colas, con rango-biserial e IC por bootstrap (`paired_subject_test`). Si hay varias configuraciones, Holm (`holm`).
- **Siempre tamaño del efecto con IC.** "Sin diferencia" no quiere decir "iguales".

**7.3 Elegir entre candidatas** (`select_variant`, regla "noninferior")
1. Grupo: las candidatas no inferiores a la mejor en AUC (límite inferior del IC 95 % de la diferencia ≥ −0,02).
2. Dentro del grupo, las que empatan con la mejor en acierto por registro.
3. Entre esas, la más simple según un orden fijado antes de correr.
4. Control: **validación cruzada por sujetos** (5 grupos, separando sujetos con y sin apnea; `subject_folds`, `cross_validate_selection`). Se reporta el optimismo (AUC al elegir menos AUC afuera) y si la elección es estable entre grupos.

**7.4 Verificar una etapa obligatoria** (4.3, 4.4, minutos malos; `plan_test.md` 2.1)
- Se calcula F con la versión nueva y con la vigente, **sobre los mismos minutos** (los 22.123 de E3a) y con los mismos remuestreos.
- **Se adopta si es no inferior en las dos medidas:** AUC por minuto y acierto por registro, con el límite inferior del IC 95 % de (nueva − vigente) ≥ −0,02.
- Si empeora, se reporta y no se adopta.
- Los controles (por ejemplo E1) se reportan, pero no deciden si no se fijó así antes.
- Ejemplo completo: `07_filtro.ipynb`.

**7.5 Código**
- Funciones en `src/` con docstring en castellano. Los parámetros van en `src/config.py`, no escritos en el código.
- Reutilizar lo que hay: `build.record_series` y `record_feature_tables` (arman RR, EDR y features por minuto; aceptan `filt` y `refine`) y `stats.compare` (AUC, acierto, elección y validación cruzada).
- Cada función nueva lleva su test en `tests/`. Si se puede, con una señal sintética de resultado conocido; con datos reales, con `skipif` si faltan los archivos. **`pytest` tiene que pasar antes de cada commit** (hoy: 72 tests).
- Semilla 2026 en todo lo aleatorio.

**7.6 Notebooks**
- Un notebook por etapa, numerado, con esta estructura:
  1. qué hace y las reglas fijadas;
  2. resultados;
  3. **Decisión**, escrita después de correr, con los números.
- Se commitea ejecutado, con sus salidas. Las figuras van a `results/figuras/`, que no se versiona.
- Se corre con `jupyter nbconvert --to notebook --execute --inplace notebooks/<nombre>.ipynb`. En Windows, con `.venv/Scripts` en el PATH, y `python -X utf8` si se imprimen acentos.
- La caché de E3 (`results/e3/`) no se versiona. Se regenera corriendo `04_E3a_features.ipynb`, que tarda mucho. La usan las verificaciones para tomar los minutos de E3a.

**7.7 Commits y revisión**
- **Pasos chicos.** Cada etapa va en dos commits: primero las funciones con sus tests, y después el notebook con la decisión y el cambio de configuración.
- Mensajes en castellano: "Agrega las funciones de …" y "<etapa>: <qué se decidió>".
- **Antes de commitear, otro integrante revisa los resultados.**
- Commits balanceados (lo pide la consigna): cada integrante commitea su bloque, en una rama por bloque, con un PR que revisa otro.

---

### 8. Checklist: lo hecho y lo que falta

✅ hecho · ⬜ falta · ➖ no aplica (se declara en el informe). "Vacía" quiere decir que la función existe en el repo con su firma y su docstring, pero todavía lanza `NotImplementedError`.

#### 8.1 Hecho

| | Ítem | Qué se hizo | Dónde |
|---|---|---|---|
| ✅ | Carga de la base | Descarga y lectura del ECG (en mV y en unidades del conversor), encabezado, `.qrs`, etiquetas por minuto, respiración y tabla de perfiles y AHI | `src/data.py`, `scripts/download_data.py` |
| ✅ | Sujetos y duplicados | Se excluyen 3 grabaciones duplicadas (c05, x22, x33); quedan 67 registros de 29 sujetos | `01`, `src/split.py`, `src/duplicates.py` |
| ✅ | Partición 70/30 | Por sujeto, con cuotas exactas, balance de ±2 puntos y semilla 2026: 47 registros de desarrollo y 20 de test | `data/split.csv` (commit `8d4ca2f`) |
| ✅ | Plan de test | Condiciones para abrirlo, qué se congela, H2 con M1 y M2 y Holm, secundarios y los desvíos 9.1 y 9.2 | `docs/plan_test.md` |
| ✅ | 4.1 Adquisición | Formato medido (12 bits), descripción del dataset, calidad por registro, cuantización (el refinamiento parabólico se queda) y AHI | `00`, `src/preprocessing/quality.py`, `src/qrs/quantization.py` |
| ✅ | 4.2 Filtro convencional | Especificación sacada de los datos; pasabanda 0,5–45 Hz, orden 3, ida y vuelta; F no inferior | `07`, `src/preprocessing/filters.py` |
| ✅ | 4.5 Limpieza de RR | Rango de 0,3–2 s, ectópicos con 20 % sobre la mediana local, interpolación y calidad por minuto. Las reglas se usan, pero no se verificaron (ver minutos malos) | `src/qrs/rr_clean.py` |
| ✅ | 4.6 Segmentación | Ventana centrada en cada minuto; 240 s elegidos con datos | `src/features/windows.py` |
| ✅ | 4.7 HRV y Lomb | RR medio, SDNN, RMSSD y pNN50; periodograma de Lomb con potencias por banda | `src/features/hrv_time.py`, `lomb.py` |
| ✅ | 4.7 EDR y acoplamiento | 5 métodos de EDR, coherencia, potencia cruzada, Welch y multitaper, y todas las candidatas de E3 | `src/features/edr.py`, `coupling.py`, `build.py`, `variants.py` |
| ✅ | 4.8 Validación del EDR | Contra la respiración real en los 8 registros que la tienen (E1), y H1 con la respiración real (E2) | `02`, `03` |
| ✅ | E1 | EDR por área del QRS | `02` |
| ✅ | E2 (H1) | H1 se sostiene: con apnea aparece un acoplamiento lento | `03` |
| ✅ | E3a / E4 | F = potencia cruzada RR–EDR en 0,01–0,05 Hz; HRV de referencia = VLF con Lomb | `04` |
| ✅ | Control de E3a | La coherencia no aporta para detectar | `05` |
| ✅ | E3b | Sin normalizar ni suavizar; ventana de 240 s | `06` |
| ✅ | Herramientas estadísticas | AUC con bootstrap por sujeto, acierto por registro, orientación, regla de elección, validación cruzada por sujetos, Wilcoxon por sujeto, Holm y Youden | `src/stats/` |
| ✅ | Documentación | Esquema v3 y README actualizado | `docs/`, `README.md` |
| ➖ | Piso de coherencia por *surrogates* | No aplica, porque F no usa la coherencia. `surrogate_floor` queda vacía | `src/features/coupling.py` |

#### 8.2 Falta

| | Ítem | Qué hay que hacer | Qué ya existe → qué hay que escribir | Terminado cuando |
|---|---|---|---|---|
| ⬜ | **Avance obligatorio (27/10)** | Mostrar el preprocesamiento y las features, y confirmar con la docente que el aporte es nuevo (lo pedía v2) | Todo el contenido existe (notebooks `00` a `07` y figuras en `results/figuras/`) → armar la presentación del avance | Presentado, con la devolución anotada en el esquema |
| ⬜ | **4.3 Detección QRS** | Pan-Tompkins propio con las etapas clásicas (pasabanda de ~5–15 Hz, derivada, cuadrado, integración en ventana de ~150 ms, umbrales adaptativos con búsqueda hacia atrás), con los coeficientes llevados a 100 Hz y **sin suponer la polaridad del R**. Antes, revisar a mano una muestra de las `.qrs`, elegida con semilla antes de mirarla, porque son automáticas. Validar contra las `.qrs` con Se y VPP, tolerancia de 100 ms | Existe: `qrs_reference` (polaridad por registro), `r_peaks_from_marks` y `refine_peaks_parabolic` (refinamiento) y `record_series`. Hay que escribir: `detect_r_peaks` y `validate_against_reference` (vacías), una opción en `record_series` para usar el detector propio, los tests y el notebook `08` | F con el detector propio es no inferior a F con las `.qrs` (7.4): se adopta. Si no, se siguen usando las `.qrs` y el detector se reporta como validación |
| ⬜ | **4.4 Realizaciones y Wiener** | Recortar latidos alineados en R (−250 a +400 ms); cada uno es una realización. Promedio de ensamble → PSD de la señal; latido menos promedio → PSD del ruido. H = S_s / (S_s + S_n) por registro, aplicado como filtro LTI sobre el ECG continuo, antes de calcular el EDR | Existe: picos R refinados, `beat_matrix` (recorta ventanas simétricas: sirve de base) y `validate_edr` (la métrica de E1). Hay que escribir: `extract_realizations`, `estimate_psds` y `wiener_filter` (vacías), una opción en `record_series`, los tests y el notebook `09` | F es no inferior (7.4): se adopta (plan de test 2.1). La métrica de E1 en los 8 registros con respiración se reporta como control. Si no mejora, se reporta igual |
| ⬜ | **Minutos malos** | Decidir qué minutos se evalúan: (a) la regla del 20 % de RR corregidos, que se asumió; (b) la señal perdida (tramos planos o clavados en el tope de 1 s o más), que hoy se interpola y que la regla del 20 % no ve. Regla candidata, sin parámetros libres: un minuto se evalúa solo si su ventana de 240 s no tiene señal perdida | Existe: `flat_mask`, `saturated_mask`, `minute_quality` y la medición de la 4.1. Hay que escribir: la máscara por ventana y la regla en `build`, los tests y el notebook `10` | Medidos cuántos minutos y registros pierde, el sesgo entre minutos con apnea y normales (IC por sujeto) y la no inferioridad de F. Si cambia los minutos evaluados, se agrega como desvío en `plan_test.md` §9 |
| ⬜ | **Umbrales** | Youden de F y de la HRV en desarrollo. Alternativas fijadas antes de correr: la mediana de los Youden de los remuestreos por sujeto, y el umbral que iguala la apnea total estimada con la real. Combinar F con la HRV (AND u OR) | Existe: `roc_youden`, `record_agreement` y `subject_folds`. Hay que escribir: las alternativas, la combinación y el notebook `11` | Youden es la referencia. Otra opción se adopta solo si mejora en los sujetos de afuera de la validación cruzada, con IC. Los umbrales quedan escritos y commiteados (condición 2 del plan de test) |
| ⬜ | **Descriptivo de las features** | Mann-Whitney y delta de Cliff de todas las features (HRV y acoplamiento) entre minutos con y sin apnea, con Holm | Hay que escribir: `mann_whitney_cliff` (vacía) y la tabla para el informe | Tabla con el tamaño del efecto y su IC por feature. Con ~20.000 minutos el p no informa |
| ⬜ | **Validación cruzada anidada** | Repetir toda la elección (E3a → E3b → umbral) dejando afuera cada grupo de sujetos | Existe: `subject_folds` y `cross_validate_selection`, que repite solo la elección de un nivel. Hay que escribir: la versión anidada con el umbral y el notebook `12` | AUC, exactitud y acierto por registro en los sujetos de afuera: es la estimación de desarrollo que se reporta (condición 3 del plan) |
| ⬜ | **Congelar** | Actualizar las filas † de `plan_test.md` §3, este esquema y el README; commitear y poner la etiqueta | — | Están cumplidas las 4 condiciones de `plan_test.md` §2 y existe la etiqueta `congelado-test` |
| ⬜ | **Test** | Correr `notebooks/99_test.ipynb` una sola vez sobre la etiqueta, con el plan (§4 a §6) | Existe: `compare_variants`, `agreement_compare`, `paired_subject_test` y `holm`. Hay que escribir: `minute_metrics` y `record_metrics` (vacías) y el notebook | Ejecutado una vez y commiteado con sus salidas tal como quedaron |
| ⬜ | **Figuras finales** | La central: el mapa nocturno de acoplamiento con las apneas superpuestas, en un registro A y uno C. Además: ECG filtrado con los R refinados, RR, EDR, ROC de F contra la HRV y apnea estimada contra real a lo largo de la noche | Existe: los mapas de E2 (a03 y c02, en `03`) y las figuras de cada notebook en `results/figuras/`. Hay que escribir: `coherence_night_map` (vacía) y las figuras finales con un estilo común | Cada figura del informe se genera desde código del repo |
| ⬜ | **Informe** | 8 páginas como máximo, más 4 de anexo, con la estructura de la sección 12 | Existe: las decisiones con sus números en cada notebook y en este esquema | Entregado en PDF el 10/11 |
| ⬜ | **Presentación** | 15–20 min | — | Lista para la defensa |
| ⬜ | **Preparación de la defensa** | Todos responden sobre todo (lo pide la consigna): cada integrante tiene que poder explicar los bloques de los otros | Existe: las preguntas probables de la sección 10 | Cada uno repasó la sección 10 y los notebooks de los otros bloques |
| ⬜ | **Commits balanceados** | Cada integrante commitea su bloque, en una rama por bloque con un PR que revisa otro (7.7). Hoy todos los commits están a nombre de una sola persona | — | El historial muestra commits de los tres |
| ⬜ | GUI (opcional) | Visor del mapa nocturno por registro. Solo si sobra tiempo después de lo demás | — | — |

**Orden:** avance → 4.3 → 4.4 → minutos malos → umbrales → validación cruzada anidada → congelar → test → figuras de resultados, informe, presentación y defensa. El descriptivo va en cualquier momento antes de congelar.
- Los minutos malos van después de 4.3 y 4.4, porque esas etapas pueden cambiar qué latidos se usan; así los minutos evaluados cambian una sola vez.
- Los umbrales van después de los minutos malos, porque dependen de qué minutos se evalúan.
- La validación cruzada anidada necesita el umbral definido.

**Bloques sugeridos** (como en v2; los responsables los define el grupo):

| Bloque | Ítems |
|---|---|
| Latidos | 4.3 y minutos malos |
| Señal | 4.4 |
| Estadística | umbrales, descriptivo, validación cruzada anidada y test |
| Todos | avance, figuras, informe, presentación y defensa |

---

### 9. Riesgos

| Riesgo | Qué se sabe | Qué se hace |
|---|---|---|
| H2 no se confirma en test | En desarrollo, la diferencia de AUC tiene un IC que incluye 0; test tiene 10 sujetos | Se reportan el efecto y su IC. M2 es la medida más fuerte (0,81 contra 0,42) |
| El Pan-Tompkins propio empeora F | Las `.qrs` funcionan hoy | Se siguen usando las `.qrs` y el detector se reporta como validación |
| Wiener no mejora el EDR | — | Se reporta como resultado |
| La política de minutos malos sesga contra la apnea | Hoy la regla del 20 % no muestra sesgo significativo, pero el IC llega a +6,8 puntos | Se mide con IC antes de adoptarla |
| Números de desarrollo optimistas | Se eligió con desarrollo; el optimismo de E3a fue de 0,021 | Validación cruzada anidada y test |
| La matriz A/B/C de test es inestable | Hay solo 3 registros B, y B es la categoría menos consistente con el AHI | Se dice en el informe |
| Commits desbalanceados | Hoy todos los commits están a nombre de una sola persona | Repartir los bloques de la sección 8 |

---

### 10. Preguntas probables de la defensa

1. **¿Por qué la potencia cruzada y no la coherencia?** Porque sin la coherencia se detecta igual (0,874 contra 0,871) y la coherencia sola detecta mal (0,63). Lo que separa es cuánto oscilan juntas las señales, no la sincronía (E3a y su control).
2. **¿Por qué no normalizan cada noche?** Porque empeora el AUC en todas las familias (de 0,876 a 0,68–0,73) y arruina el acierto por registro (E3b).
3. **¿Por qué 4 min si las etiquetas son de 1 min?** Para resolver 0,01 Hz hacen falta segmentos de más de 100 s. La ventana se eligió con datos entre 3 y 8,5 min. El costo en los bordes de los episodios se reporta.
4. **¿El EDR no es ruido?** Con la respiración real da 0,53 de coherencia, contra 0,16 por azar. Y con la respiración real, el efecto de H1 aparece en los 5 registros (E1 y E2).
5. **¿Por qué el sujeto es la unidad?** Porque los minutos de una persona no son independientes, y hay personas con varias noches y grabaciones duplicadas en la base.
6. **¿Cómo evitan el sobreajuste?** Con reglas fijadas antes de correr, no inferioridad en lugar de "el máximo", validación cruzada por sujetos y test una sola vez con un plan cerrado.
7. **¿Por qué Lomb si después remuestrean?** Lomb da el espectro de HRV sin interpolar el RR irregular. El espectro cruzado necesita muestreo uniforme.
8. **¿El Wiener no les borra el EDR?** Es un filtro LTI: aplica la misma ganancia a todos los latidos y conserva la relación de amplitudes entre ellos.
9. **¿Qué es nuevo?** Sumar al RR la respiración derivada del ECG en la banda del ciclo de apnea. Mejora sobre todo la estimación de cuánta apnea tiene cada noche.
10. **¿Por qué importan los 100 Hz?** Porque redondean el pico R a 10 ms e inflan el RMSSD. Se mide y se corrige con interpolación parabólica (4.1).

---

### 11. Desvíos declarados hasta ahora

| # | Dónde | Desvío | Motivo |
|---|---|---|---|
| 1 | E1 (`02`) | La deriva de línea de base se agregó en una segunda versión, antes de correrla | Faltaba un método de EDR que no usa la forma del QRS |
| 2 | E1 (`02`) | El empate área–deriva no se desempató por simplicidad: se llevó a E3 | E3 decide con la detección (la tarea real) y con 19 sujetos, en lugar de 8 |
| 3 | E3a (`04`) | Se agregaron la regla de no inferioridad (B) y la de mayor AUC (C), y la forma "potencia sola", después de la primera corrida | La regla original era defectuosa; la nueva forma es un control. Cuál regla se usa lo decidió la validación cruzada |
| 4 | Plan de test 9.1 | La 4.1 se agrega a las condiciones para abrir test | El refinamiento no estaba verificado |
| 5 | Plan de test 9.2 | El AHI entra como resultado secundario | Es la medida clínica; como principal repetiría M2 (Spearman 0,94) |

---

### 12. Consigna → informe → código

| Tema obligatorio | Sección del informe | Código | Notebook |
|---|---|---|---|
| Adquisición | Materiales: base de datos | `src/data.py`, `src/preprocessing/quality.py`, `src/qrs/quantization.py` | `00`, `01` |
| Filtros convencionales | Métodos: preprocesamiento | `src/preprocessing/filters.py` | `07` |
| Recorte en realizaciones | Métodos: filtro óptimo | `src/preprocessing/wiener.py` | `09` (pendiente) |
| Filtros óptimos | Métodos: filtro óptimo | `src/preprocessing/wiener.py` | `09` (pendiente) |
| Detección QRS | Métodos: detección de latidos | `src/qrs/pan_tompkins.py`, `src/qrs/rr_clean.py` | `08` (pendiente) |
| Segmentación | Métodos: ventanas | `src/features/windows.py` | `04`, `06` |
| HRV | Métodos: features | `src/features/hrv_time.py` | `04` |
| Lomb | Métodos: features espectrales | `src/features/lomb.py` | `04` |
| (aporte) Acoplamiento | Métodos y resultados | `src/features/edr.py`, `coupling.py`, `build.py`, `variants.py` | `02` a `06` |
| Análisis estadístico | Resultados | `src/stats/` | `03` a `06`, `11`, `12`, `99` |
