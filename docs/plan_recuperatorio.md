# Plan para el recuperatorio

La devolución (nota 3) no cuestiona que el análisis esté mal hecho: dice que no se entiende. Hay muchas decisiones sin mostrar las señales que las respaldan, no hay un hilo que una métodos y resultados, y el alcance es demasiado grande. El pedido explícito es **limitar el alcance a una sola hipótesis y construirla paso a paso**, justificando cada decisión con un análisis cualitativo (figuras) y cuantitativo de las señales, y con bibliografía.

El estado de cada observación de la devolución está en [`revision_devolucion.md`](revision_devolucion.md), y cada decisión con su justificación, en [`decisiones.md`](decisiones.md).

## 0. Regla de trabajo

Durante el desarrollo **solo se usan los 47 registros de desarrollo**. Test no se toca —ni señales, ni etiquetas, ni para verificar— hasta la evaluación final, que se corre una sola vez con todo fijado. De test solo se usan los datos con los que se armó la partición (categoría, cantidad de minutos con apnea y perfil de cada registro), para explicarla y verificarla.

## 1. Hipótesis única y objetivos

Están en [`objetivos_hipotesis.md`](objetivos_hipotesis.md): objetivo general, objetivos específicos (uno por notebook), la hipótesis con sus tres predicciones y el criterio para sostenerla, el alcance y las limitaciones.

Sale del informe: H1 de la primera versión (coherencia y cociente de coherencias), la validación cruzada anidada, las reglas de no inferioridad, Holm, rango-biserial y los desvíos declarados. Quedan en `notebooks/v1/` como historia del trabajo.

## 2. Decisiones que se unifican

| Tema | Antes | Ahora |
|---|---|---|
| Ventana de análisis | 100, 120, 180, 240 y 512 s según la sección | **240 s** centrada en cada minuto, para todas las features |
| Feature de comparación (solo RR) | Lomb en 0,01–0,04 Hz y 180 s, elegida con datos | Lomb en **la misma banda y la misma ventana** que F |
| Qué se ajusta en desarrollo | feature, posprocesamiento, umbral | **solo el umbral**; banda y ventana salen del análisis de las señales |
| Niveles de análisis | mezclados | **minuto** (decisión), **registro** (noche), **sujeto** (intervalos de confianza) — se dice en cada resultado |

La ventana de 240 s tiene una justificación física: con segmentos de 120 s la banda empieza en 0,017 Hz (ciclos de 60 s, dos por segmento); Welch con 3 segmentos de 120 s solapados al 50 % ocupa 240 s. Los ciclos de 60 a 100 s entran solo en parte (`08` §1). Las realizaciones de Wiener (−250 a +400 ms alrededor del pico R) no son una ventana de análisis sino un latido, y se aclara así.

## 3. Cada observación y su respuesta

| Observación | Respuesta | Dónde |
|---|---|---|
| Presentación sin fisiología de la apnea ni diagnóstico | Diapositiva de apnea obstructiva, polisomnografía, AHI y por qué se ve en el ECG (bradicardia–taquicardia cíclica, modulación respiratoria del QRS) | informe §1, presentación |
| EDR y acoplamiento sin explicar | EDR: qué es, por qué el QRS cambia con la respiración, cómo se calcula, figura contra la respiración real. Potencia cruzada: definición, cómo se estima (Welch), qué significa | informe §1–2, nb `03` y `04` |
| Estado del arte viejo | Agregar trabajos de 2015 en adelante (verificar cada cita antes de usarla) | informe §1 |
| Objetivos confundidos con hipótesis | Objetivo general + específicos (sección 1 de este plan) | informe §1 |
| Categorías A/B/C sin explicar; partición confusa | Definición de PhysioNet de cada categoría; partición por sujeto explicada paso a paso, con figura | nb `01` |
| Filtro sin espectro que lo respalde | Espectro medio del ECG y de los latidos con las frecuencias de corte marcadas; ECG antes y después | nb `02` |
| Falta exploración sistemática de los registros | Ejemplos en tiempo de registros limpios y con artefactos, espectrograma, calidad por registro | nb `01` |
| Refinamiento del pico R a 100 Hz sin análisis | Figura de un latido muestreado con el vértice de la parábola; distribución de la corrección; efecto en el RR | nb `02` |
| Tolerancia de ±100 ms e interpolación sin analizar | Distribución de las diferencias detector–marca (muestra que la tolerancia no cambia el resultado); casos de error con figura; ejemplos de RR corregidos | nb `02` |
| Wiener sin motivo ni relación con el EDR | El EDR depende de la forma del QRS; Wiener busca limpiar el QRS sin cambiar su amplitud. Se evalúa con la coherencia EDR–respiración | nb `03` |
| EDR vs deriva de línea de base sin análisis | Comparación con figura y números contra la respiración real | nb `03` |
| Remuestreo a 2 Hz sin justificar | La potencia cruzada necesita las dos señales en una grilla común; 2 Hz cubre hasta 1 Hz, por encima de la respiración (≤ 0,4 Hz) | nb `04` |
| De dónde sale F | Espectro medio de RR y EDR en minutos con y sin apnea: la diferencia está en 0,017–0,05 Hz | nb `04` |
| Referencia HRV sin paper y con otra ventana | Lomb (Task Force 1996; Laguna et al. 1998) en la misma banda y ventana | nb `04` |
| ¿Por qué Youden? | Sin costo distinto para falsos positivos y negativos, maximiza sensibilidad + especificidad; cita Youden 1950 y Fluss et al. 2005 | nb `04` |
| ¿Una sola feature alcanza? | Distribuciones de F con y sin apnea, curva ROC, comparación contra RR solo y EDR solo | nb `04` |
| Métricas sin explicar | Tabla con cada métrica: qué mide y cómo se calcula | informe §2 |
| Sin gráficos de resultados | F a lo largo de la noche con las etiquetas, ROC, fracción estimada vs real por registro, matriz de confusión | nb `04` |
| No queda claro qué se ajusta en train | Solo el umbral; se dice explícitamente | informe §2 |
| Sin interfaz gráfica | Visor de registros (ECG, RR, EDR, espectrograma, F y etiquetas) | `app/` |
| Código difícil de seguir | Notebooks nuevos lineales `01`–`04`; los anteriores pasan a `notebooks/v1/` | `notebooks/` |
| Entrega tarde; PowerPoint cambiado después de entregar | Entregar a tiempo y no tocar nada después | — |
| Tiempo de defensa excedido; poca participación de Leah | Ensayar con cronómetro; repartir bloques; Leah puede presentar en inglés | guía de presentación |

## 4. Notebooks nuevos

| Notebook | Contenido |
|---|---|
| `01_base_y_exploracion` | Base, categorías, etiquetas, partición; señales en tiempo y frecuencia, artefactos, calidad |
| `02_filtro_y_latidos` | Filtro con su espectro; detector propio contra las marcas; refinamiento; serie RR y su limpieza |
| `03_realizaciones_wiener_edr` | Latidos como realizaciones, Wiener, EDR contra respiración real |
| `04_feature_y_detector` | RR y EDR durante la apnea, espectros, potencia cruzada, umbral y evaluación |
