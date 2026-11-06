# DataMad 2026: preregistro del contraste principal

**Escrito el 2-nov-2026, antes de ejecutar ningún modelo con datos reales.** El contraste con datos reales se ejecuta a partir del sáb 7-nov (periodo de desarrollo). `scripts/contraste.py` se niega a usar los datos reales antes de esa fecha.

**Lo que ya se ha visto (27-oct, declarado en `TRABAJO_PREVIO.md`)**
- La tasa de aceptación del Bono es plana (~24 %)
- Hay menos solicitudes por joven donde más mercado supera el tope (r = −0,53, sin controles), y un 32 % menos con tope de 600 € que con 900 €, con alquileres parecidos
- Por eso este contraste **no es independiente** de esa pista: se usan los mismos municipios. Lo que añade es los controles, la inferencia por permutación, la réplica en otro programa y los topes falsos, todo fijado antes

## Pregunta
¿El tope de alquiler del Bono Alquiler Joven (600 €, o 900 € en los 29 municipios del Anexo II) **disuade** de pedir la ayuda donde el alquiler típico lo supera?

## Datos
- **Unidad:** municipio. Entran los municipios del CSV del Bono con código real (159) que tengan alquiler del SERPAVI 2022 y todos los controles. Los 20 municipios que no salen en el CSV no se tratan como ceros, porque no sabemos si tuvieron 0 solicitudes
- **Resultado:** solicitudes del Bono 2022 (recuento)
- **Exposición** (*offset*): jóvenes de 20 a 34 años en 2022 (censo anual)
- **Variable de interés:** `share_above_cap` = parte estimada del mercado de alquiler por encima del tope **del propio municipio**. Se calcula con un alquiler log-normal ajustado al p25 y al p75 del SERPAVI 2022 (vivienda colectiva)
- **Controles** (fijados ahora; no se añaden otros):
  1. log del alquiler mediano 2022 (SERPAVI)
  2. log de la renta disponible bruta per cápita 2022 (portal)
  3. % de hogares que viven de alquiler (Censo 2021, portal)
  4. paro registrado de menores de 25 años (media de 2022) por cada 1.000 jóvenes de 15 a 24 (portal)
  5. log de la población total 2022 (portal)
- Tabla única: `data/interim/municipios.csv`, hecha por `scripts/preparar_datos.py` (diccionario en `data/DICCIONARIO.md`)

## Modelos (no hay más; cualquier otro análisis se marca como «exploratorio»)
**M1, principal.** Poisson por pseudo-máxima verosimilitud con *offset* log(jóvenes) y errores robustos (HC1):
`solicitudes ~ share_above_cap + 5 controles + offset(log jóvenes)`
- Efecto de interés: β₁. Se cuenta como «+10 puntos de mercado por encima del tope → las solicitudes por joven cambian un (e^(0,1·β₁) − 1) %»

**H1 se da por confirmada solo si se cumplen las tres:**
1. β₁ < 0 y su intervalo de confianza al 95 % (HC1) no incluye el 0
2. **Permutación estratificada:** 2.000 sorteos de la etiqueta «tope 900» entre municipios del mismo tercio de población, recalculando `share_above_cap` y β₁. El p unilateral (parte de los sorteos con β₁ ≤ el real) tiene que ser ~~< 0,05~~ **< 0,01** (enmienda 4)
3. β₁ < 0 también **sin Madrid capital** (es el 64 % de las solicitudes)

**H2, experimento natural (secundaria, se informa con su intervalo).** M1 solo con los municipios del tramo de alquiler común a los dos grupos (mismo criterio que la regla F4 del 27-oct), cambiando `share_above_cap` por un indicador «tope 600». Se espera una razón de tasas < 1.

**R1, réplica en otro programa.** M1 con las solicitudes de las Ayudas al alquiler para jóvenes (programa 5.1, 2022 + 2023). Tienen los mismos topes de 600 y 900 €, pero se reparten por concurrencia competitiva. Se espera β₁ < 0. **No es un placebo:** comparte topes y tipo de municipio. Si sale con el signo contrario, se dice.

**Comprobación con topes falsos.** M1 con la parte del mercado por encima de un tope **igual para todos** (600 € y, aparte, 900 €) en vez del tope real. Si el mecanismo es el tope, el modelo con el tope real tiene que ajustar mejor (menor desviación). Se informa siempre, salga lo que salga.

**Robustez** (se informa; no sirve para elegir el resultado):
- Binomial negativa (NB2) en vez de Poisson
- Solicitudes por cada 1.000 hogares de alquiler (*offset* log de los hogares de alquiler)
- Alquiler del SERPAVI 2023 en vez de 2022
- Alquiler medio del portal (municipios de más de 20.000 habitantes, 2023) en vez del SERPAVI
- ~~Quitar los municipios con menos de 20 solicitudes~~ → quitar los municipios con **menos de 1.000 jóvenes** (ver enmienda 2)

## Enmiendas (2-nov, al programar `contraste.py` y **antes de ver datos reales**)
1. **H2:** el tramo de alquiler común se calcula con **todos los municipios del modelo**, no solo con los de ≥ 50 solicitudes como en la regla F4. Elegir la muestra por el número de solicitudes sería elegirla por el resultado
2. **Robustez:** por la misma razón, se quitan los municipios pequeños según sus **jóvenes** (menos de 1.000) y no según sus solicitudes (menos de 20)
3. **Muestra efectiva:** 132 municipios (103 con tope de 600 € y 29 con 900 €), con 48.298 de las 48.383 solicitudes con municipio. Salen 27 municipios sin alquiler del SERPAVI 2022 o sin algún control

4. **Umbral de la permutación** (2-nov, tras la primera prueba de potencia con datos inventados y antes de ver datos reales): sin efecto plantado, la regla daba un «sí» falso en el **10 % y el 8 %** de las simulaciones, el doble de lo aceptable. **Regla para fijar el umbral, escrita antes de la segunda prueba:** se usa el umbral más alto de {0,05; 0,025; 0,01} con el que, sin efecto, la regla completa dé «sí» en **≤ 5 %** de las simulaciones con los dos niveles de ruido (200 simulaciones por caso). El resultado y el umbral elegido se apuntan abajo, en «Potencia»

## Qué se cuenta según el resultado (escrito antes)
- **Si H1 se confirma:** titular «Donde el alquiler supera el tope, los jóvenes ni piden el Bono». El impacto se calcula con β₁ y su intervalo: cuántas solicitudes más habría con un tope indexado al alquiler local. Siempre con el intervalo y aclarando que es un efecto **por municipio**, no por persona
- **Si H1 no se confirma:** no se dice que el tope disuade. La historia pasa a la **cobertura**: el dinero se agotó (BOCM, nov-2023) y las ayudas por cada 1.000 jóvenes cambian mucho entre municipios con la misma necesidad. El producto propone cómo repartir mejor el mismo presupuesto, sin afirmar un efecto del tope
- **En los dos casos** se enseña lo que no salió (réplica, topes falsos), como pide el PLAYBOOK: mejor contarlo nosotros que que lo encuentre el jurado

## Potencia (datos inventados, antes de ver datos reales; 2-nov)
Hecho con `scripts/contraste.py --sintetico`. Se usan las **covariables reales** de los 132 municipios y un **resultado inventado** con efectos conocidos, escalado a unas 48.000 solicitudes. Hay dos niveles de ruido por municipio (DE 0,2 y 0,4 en el logaritmo de la tasa) y 199 permutaciones por simulación. Detalle en `resultados/potencia_sintetica_*.json`.

**Ensayo de punta a punta** (un conjunto inventado con β₁ = −1,1): el script recupera β₁ = −0,90 (IC −1,43 a −0,36; p de permutación 0,01). H2 da una razón de 0,66, los topes falsos ajustan peor que el real y la réplica sale con el mismo signo. Además cazó un fallo del código (H2 con una columna de ceros), ya arreglado.

**Umbral (enmienda 4):** con 200 simulaciones sin efecto, la regla completa da «sí» falso en un 8,0 / 5,5 % con p < 0,05, en un 6,5 / 5,0 % con p < 0,025 y en un **4,5 / 4,0 % con p < 0,01** (ruido bajo / alto). Se fija **0,01**. Por separado, el intervalo HC1 y la permutación por tercios son algo optimistas (falsos «sí» del 6-9 % y del 10-14 %); por eso se exigen juntos.

**Potencia con el umbral 0,01:**
| Efecto plantado | Por cada +10 puntos de mercado sobre el tope | Ruido bajo | Ruido alto |
|---|---|---|---|
| β₁ = 0 (sin efecto) | 0 % | 4,5 % de «sí» falsos | 4,0 % |
| β₁ = −0,5 | −4,9 % de solicitudes | 51 % | 22 % |
| β₁ = −1,1 (lo que sugería la pista del 27-oct, sin controles) | −10,4 % | **99 %** | **57 %** |

Archivos: `potencia_sintetica_200x199.json` (β₁ = 0 y −0,5) y `potencia_sintetica_100x199.json` (β₁ = −1,1). `potencia_sintetica.json` es la primera pasada, con el umbral antiguo de 0,05.

**Cómo leer un «no»:** con un efecto pequeño (−5 % por cada 10 puntos), un «no» puede ser falta de datos (potencia del 22-51 %), así que se dirá «no se puede confirmar», no «no hay efecto».
