# Criterio de robustez para las etapas que protegen contra fallas

**Este documento se escribió y se subió al repositorio antes de correr las pruebas que lo aplican** (`notebooks/08_edr_nivel_noche.ipynb`, secciones 4 a 6). Si algo tuviera que cambiar, se agrega al final, con fecha y motivo, y no se borra lo que estaba. Solo se usan los registros de desarrollo.

## Por qué

La regla de sencillez (`criterio_parsimonia.md`) deja entrar una etapa solo si mejora de forma demostrable. Eso castiga a las etapas que **protegen contra fallas** poco frecuentes o concentradas en pocas personas: con 19 personas su beneficio no se puede demostrar, aunque exista. El notebook 08 lo mostró: al sacar la EDR relativa, la exactitud en validación cruzada cayó de 0,821 a 0,768. Es el compromiso de la estadística robusta (Hampel, 1974): se cede un poco de eficiencia cuando todo es ideal, a cambio de no romperse cuando aparece algo raro.

## Qué etapas protegen y contra qué

| Etapa | Falla que previene | Respaldo bibliográfico |
|---|---|---|
| EDR relativa (dividir por el tamaño típico del QRS) | Distinto tamaño del QRS entre personas, por la anatomía o los electrodos | Varon et al. (2020) normalizan el ECG antes de extraer la EDR |
| Excluir los latidos ectópicos de la EDR | Latidos de otra forma cuya área no es respiración | Lippman et al. (1994): la corrección de los ectópicos es necesaria; Varon et al. (2020) excluyen los QRS aberrantes |
| Excluir los latidos atípicos de la EDR: Hampel o el procedimiento de Varon et al. (2020) | Artefactos de movimiento | Varon et al. (2020) publican su procedimiento; Hampel (1974) |
| Excluir los minutos con más de 20 % de RR corregidos | RR que no se midió; ritmos irregulares | Peltola (2012): la mayoría de los estudios rechaza los segmentos con menos de 80 % de latidos normales |
| Quitar la recta en cada segmento de Welch | Una deriva lenta dentro del segmento | Tarvainen et al. (2002) |
| Refinamiento del pico R | El error de muestrear el pico R a 100 Hz | Merri et al. (1990); ya se mantiene por la condición (b) de `07` |

**No protegen** y siguen la regla de sencillez de `07`: el Wiener (sale; además es frágil cuando la forma del latido cambia en la noche y ningún trabajo publicado lo usa) y la medida de confianza (sale). La interpolación se decide como en `criterio_edr.md` (E6): spline cúbico, el estándar.

## La regla

Una etapa protectora **se mantiene**, salvo en dos casos:

1. **Empeora de forma demostrable.** Se prueba sacándola del detector candidato (abajo), de a una:
   - la exactitud en validación cruzada por personas, con el bootstrap que repite el ajuste en cada sorteo (2000 sorteos);
   - para las etapas de la EDR, además P2 en desarrollo, con bootstrap pareado por personas (4000 sorteos).

   Empeora de forma demostrable si la diferencia va en contra de la etapa y su p, corregido por Holm en la familia de estas pruebas, es menor que 0,05.
2. **Su prueba de estrés no muestra protección.** Entonces no protege, y pasa a la regla de sencillez de `07`.

Entre Hampel y el procedimiento de Varon, si los dos protegen y ninguno empeora, se usa el **publicado** (Varon). Si protege solo uno, se usa ese.

## Las pruebas de estrés

Se perturban los registros de desarrollo de una forma que imita la falla, sin usar etiquetas. Se mide cuánto cambia la salida con la etapa y sin ella. Una etapa protege si, con la perturbación, la salida cambia menos con la etapa que sin ella en la mayoría de las personas. Se usa una prueba de signos sobre las 19 personas (cada persona aporta la mediana de sus noches) con p < 0,05, y Holm sobre las pruebas de estrés.

| Prueba | Perturbación | Salida que se mide | Etapa |
|---|---|---|---|
| S1 · Ectópicos | El 5 % de los latidos pasa a ser un latido prematuro (60 % del RR anterior) de otra forma: invertido, más ancho y 1,5 veces más grande | Cambio absoluto del nivel nocturno de la EDR | Excluir ectópicos |
| S2 · Artefactos | Al 5 % de los latidos se le suma un pulso de 80 ms con el doble de la amplitud del QRS, sin cambiar el ritmo | Ídem | Hampel; procedimiento de Varon |
| S3 · Tamaño del QRS | El ECG entero se multiplica por 0,5 y por 2 | Fracción de minutos cuya decisión cambia, con los parámetros ajustados en desarrollo | EDR relativa |
| S4 · Deriva | A la serie RR se le suma una oscilación de 600 s de período, con amplitud igual al desvío de su serie RR | Cambio absoluto de P_RR por minuto (mediana de la noche) | Quitar la recta |
| S5 · Ritmo irregular | 30 minutos de cada noche se reemplazan por intervalos RR irregulares (RR medio × (1 + 0,25 · ruido normal), entre 0,3 y 2 s) | Fracción de esos minutos cuya decisión cambia; con la exclusión, los minutos excluidos no tienen decisión | Excluir minutos con > 20 % de RR corregidos |

Los niveles de perturbación son ilustrativos. El 5 % es del orden de lo que se ve en noches con muchos ectópicos o artefactos, y en las figuras se muestran también 2 % y 10 %. La decisión usa solo el 5 %.

## El detector candidato y el chequeo de la combinación

El **candidato** es el detector con todas las etapas protectoras, el refinamiento del pico R, spline cúbico, sin Wiener y sin medida de confianza. Para los atípicos se usa lo que resulte de S2. Al final, el detector que resulte se compara con la versión evaluada en test, con el bootstrap que repite el ajuste. Si es peor de forma demostrable (p < 0,05), se informa y se revisa cuál de los cambios lo explica. El detector resultante no tiene una evaluación independiente hasta que se evalúe en test, una sola vez, con un notebook registrado antes de ejecutarse.

## Agregados después de registrar el criterio

**2026-11-21: Hampel o el procedimiento de Varon para los atípicos (`08` §7).** La regla de arriba elegía el procedimiento publicado (Varon) si los dos protegían y ninguno empeoraba, y eso fue lo que pasó (`08` §6). Pero esa regla suponía que los dos protegían parecido, y la prueba de estrés S2 mostró que Hampel protege unas diez veces más: con artefactos en el 5 % de los latidos, el nivel de la EDR se mueve 0,06 con Hampel y 0,67 con Varon.

Se agrega una comparación directa, decidida después de ver S2 y antes de calcularla. En S2 al 5 %, se toma la diferencia del cambio del nivel de la EDR, Varon menos Hampel, por registro. Cada persona aporta la mediana de sus noches, y se hace una prueba de signos con p < 0,05. Si Hampel protege más de forma demostrable, reemplaza a Varon. Si no, queda Varon.

La decisión se apoya solo en S2, que no usa etiquetas. No usa los minutos marcados en los controles: ese número se conoce, pero depende de una sola persona (c10 y x18) y no decide nada. Con Hampel se repiten la prueba de no inferioridad y el chequeo contra la versión evaluada en test.

*Resultado (`08` §7):* Hampel protegió más en las 19 personas (p = 2·10⁻⁶) y reemplazó a Varon. Las pruebas de signos de este documento son unilaterales, porque la pregunta tiene dirección (la etapa protege). Con la bilateral el p se duplica y ninguna decisión cambia.

**2026-11-21: las mejoras del detector de QRS (`09`).** Se escribió antes de correr `notebooks/09_robustez_qrs.ipynb`. El detector de QRS es el de Pan y Tompkins (1985) con cinco mejoras agregadas en `02` §2, más un reaprendizaje de los umbrales que está en las dos versiones de `02`, la clásica y la mejorada. Las seis protegen contra fallas que se vieron en desarrollo. En `02` se justificaron con una ablación sin valores p: la mediana de RR corregidos y que ningún registro quede más de un punto peor que las marcas de la base. Se revisan con la misma regla de arriba.

| Etapa | Falla que previene | Dónde se vio | Respaldo bibliográfico |
|---|---|---|---|
| Reaprender los umbrales si la búsqueda hacia atrás no encuentra un latido | El umbral queda por encima de los QRS, después de un artefacto o si baja la amplitud del ECG, y el detector queda ciego | a03, según `tests/test_pan_tompkins.py` (la amplitud baja a mitad de la noche); no se documentó en `02` | Pan y Tompkins (1985) aprenden los umbrales con los primeros 2 s; acá se repite ese aprendizaje |
| Pulso aislado | Tramos sin ECG: el umbral baja hasta el nivel del ruido y marca un latido cada 0,2–0,3 s | c09 (oscilación de ~7 Hz) | No tiene; lo respalda la ablación de `02` |
| Piso de energía | Ídem | x28 (ruido de ~0,01 mV) | No tiene; ídem |
| Ventana de onda T según el ritmo | Con ritmo lento la onda T termina después de los 360 ms fijos | x17 | El QT dura ~40 % del ciclo (Bazett, 1920) |
| Forma | Ondas T altas marcadas como QRS | x17 | No tiene; ídem |
| Energía por encima de 20 Hz | Ídem | x17 | No tiene; ídem |

*Pruebas de estrés.* Se perturban los 47 registros de desarrollo, y la perturbación es la misma para todas las versiones del detector. Cada versión (el detector completo, y el completo sin una etapa) se corre sobre el ECG original y sobre el perturbado. La salida es el **porcentaje de latidos que cambian**:
- se cuentan las detecciones de más o de menos respecto de las de la misma versión sobre el ECG original, con la tolerancia de 100 ms;
- los latidos originales que caen dentro de un tramo reemplazado no cuentan, y toda detección dentro de él es de más;
- el total se divide por los latidos originales que cuentan.

| Prueba | Perturbación | Etapas |
|---|---|---|
| Q1 · Sin ECG, oscilación | Los primeros 10 minutos se reemplazan por una sinusoide de 7 Hz y 0,04 mV de amplitud, como en c09 | Pulso aislado; piso |
| Q2 · Sin ECG, ruido | Los 10 minutos que empiezan en la mitad del registro se reemplazan por ruido blanco de 0,01 mV de desvío, como en x28 | Pulso aislado; piso |
| Q3 · Ondas T altas | En cada latido se agranda la onda T hasta que la relación entre la onda T y el QRS sea la de x17 (la mediana de sus latidos). Si el registro ya la tiene, no cambia | Ventana según el ritmo; forma; energía rápida |
| Q4 · Caída de amplitud | Desde la mitad del registro el ECG se multiplica por 0,3, como cuando se mueve un electrodo | Reaprendizaje |

Los tramos de Q1 y Q2 se reemplazan en el ECG crudo, que después se filtra como siempre. Q3 se arma sobre el ECG filtrado, con los latidos del detector completo:
- las amplitudes se miden respecto del nivel del segmento PR (mediana entre −100 y −50 ms);
- el QRS es el máximo absoluto a ±60 ms del pico R;
- la onda T es el máximo absoluto entre +150 ms y el 60 % del RR siguiente;
- la onda T se agranda multiplicando su apartamiento del nivel del PR, con una ventana de Tukey (α = 0,5) para no dejar escalones.

Los niveles de Q1 a Q3 copian lo que se vio en c09, x28 y x17; el de Q4 es ilustrativo. Una etapa protege si en alguna de sus pruebas la salida cambia menos con ella que sin ella. Se usa la prueba de signos de arriba (19 personas, unilateral, p < 0,05), con Holm sobre las 8 combinaciones de etapa y prueba de la tabla. Todas las versiones se corren en las cuatro pruebas. Si una etapa empeora la salida en otra prueba, se informa, pero no cambia la decisión.

*¿Empeora el detector?* Como en la regla de arriba, cada etapa se saca del detector final de `08`, de a una. Se comparan dos medidas, porque los latidos se usan para el RR y para la EDR:
- la exactitud en validación cruzada, con el bootstrap que repite el ajuste (2000 sorteos);
- P2 (4000 sorteos).

La familia de Holm son esas 12 comparaciones.

*Si una etapa no protege,* pasa a la regla de sencillez de `07`. Se mantiene solo si mejora de forma demostrable una de dos cosas:
- (b) la detección de los latidos, medida como el porcentaje medio de RR corregidos por registro (bootstrap pareado por personas, 4000 sorteos; Holm sobre las 6 etapas);
- (c) la exactitud del detector, con las comparaciones de arriba.

*Chequeo de la combinación.*
- Si se saca más de una etapa, el detector resultante se compara con el completo en las cuatro pruebas de estrés (prueba de signos, p < 0,05). Si en alguna protege menos de forma demostrable, se restituye la etapa sacada que, agregada sola, más reduce el cambio mediano en esa prueba, y se repite.
- Si se saca alguna etapa, el detector resultante se compara además con el final de `08` en exactitud, con el bootstrap que repite el ajuste. Si es peor de forma demostrable, se informa y se revisa.

Las etiquetas se usan solo en la exactitud y en P2. Test no se usa.

## Referencias

- Bazett, H. C. (1920). An analysis of the time-relations of electrocardiograms. *Heart*, 7, 353–370. Reimpreso en *Annals of Noninvasive Electrocardiology*, 2(2), 177–194 (1997). [doi:10.1111/j.1542-474X.1997.tb00325.x](https://doi.org/10.1111/j.1542-474X.1997.tb00325.x)
- Hampel, F. R. (1974). The influence curve and its role in robust estimation. *JASA*, 69(346), 383–393. [doi:10.1080/01621459.1974.10482962](https://doi.org/10.1080/01621459.1974.10482962)
- Lippman, N., Stein, K. M. y Lerman, B. B. (1994). Comparison of methods for removal of ectopy in measurement of heart rate variability. *American Journal of Physiology*, 267(1), H411–H418. [doi:10.1152/ajpheart.1994.267.1.H411](https://doi.org/10.1152/ajpheart.1994.267.1.H411)
- Merri, M., Farden, D. C., Mottley, J. G. y Titlebaum, E. L. (1990). Sampling frequency of the electrocardiogram for spectral analysis of the heart rate variability. *IEEE Transactions on Biomedical Engineering*, 37(1), 99–106. [doi:10.1109/10.43621](https://doi.org/10.1109/10.43621)
- Pan, J. y Tompkins, W. J. (1985). A real-time QRS detection algorithm. *IEEE Transactions on Biomedical Engineering*, 32(3), 230–236. [doi:10.1109/TBME.1985.325532](https://doi.org/10.1109/TBME.1985.325532)
- Peltola, M. A. (2012). Role of editing of R–R intervals in the analysis of heart rate variability. *Frontiers in Physiology*, 3, 148. [doi:10.3389/fphys.2012.00148](https://doi.org/10.3389/fphys.2012.00148)
- Tarvainen, M. P., Ranta-aho, P. O. y Karjalainen, P. A. (2002). An advanced detrending method with application to HRV analysis. *IEEE Transactions on Biomedical Engineering*, 49(2), 172–175. [doi:10.1109/10.979357](https://doi.org/10.1109/10.979357)
- Varon, C. et al. (2020). A comparative study of ECG-derived respiration in ambulatory monitoring using the single-lead ECG. *Scientific Reports*, 10, 5704. [doi:10.1038/s41598-020-62624-5](https://doi.org/10.1038/s41598-020-62624-5)
