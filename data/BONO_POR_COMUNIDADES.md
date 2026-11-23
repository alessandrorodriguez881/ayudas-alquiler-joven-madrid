# ¿Quién publica el Bono Alquiler Joven por municipio?

> Búsqueda del 16 y el 17-nov-2026, **ampliada el 23-nov** a toda la web pública (Asamblea de Madrid, BOE, Ministerio de Vivienda, Tribunal de Cuentas, AIReF, prensa, GitHub, Kaggle y el portal europeo de datos). La primera, solo en fuentes públicas: los portales de datos abiertos de las 17 comunidades, más Ceuta y Melilla, el catálogo nacional (datos.gob.es) y la Base de Datos Nacional de Subvenciones (BDNS). Lo clave lo comprobé yo el 17-nov a las 00:08: la búsqueda en datos.gob.es y el registro de Cataluña.
>
> ✅ comprobado, con enlace · ❓ no encontrado («no lo encontramos» no es lo mismo que «no existe»).

## En pocas palabras
- **En datos abiertos, que sepamos, Madrid es la única de las 17 comunidades que publica el Bono por municipio,** y solo de 2022: [Bono Alquiler Joven (2022)](https://datos.comunidad.madrid/dataset/spacm_bono_alquiler_joven_2022). Tiene solicitudes, aceptadas y rechazadas de 159 municipios, más una fila «Otro», en CSV y JSON, con licencia CC BY 4.0 ✅
  - En datos.gob.es, buscando «bono alquiler joven» o «alquiler joven» en el título, sale un solo conjunto: ese ✅ ([API](https://datos.gob.es/apidata/catalog/dataset/title/bono%20alquiler%20joven))
  - En el portal europeo (data.europa.eu, que busca también en las descripciones e incluye datos.gob.es), «bono alquiler joven» solo devuelve ese ✅ (23-nov)
  - En el portal de la Comunidad no hay Bono de 2023, 2024 ni 2025, y el de 2022 sigue con sus dos ficheros ✅ (23-nov, su buscador)
- **En datos abiertos, nadie publica 2023, 2024 ni 2025 por municipio, tampoco Madrid.** Pero el Gobierno de Madrid sí dio en la Asamblea **las ayudas concedidas de la convocatoria de 2024 por municipio, en PDF y a medias** (ver abajo): no son datos abiertos ni traen las solicitudes ✅
- **Los datos existen:** el art. 134 del RD 42/2022 obliga a cada comunidad a enviar al Ministerio, cada semestre, las solicitudes del Bono (favorables, desfavorables y pendientes) y las personas beneficiarias, «desglosado por provincias y municipios» ✅ ([BOE](https://www.boe.es/buscar/act.php?id=BOE-A-2022-802)). No hemos encontrado que se publiquen
- **Lo más parecido fuera de Madrid es Cataluña:** su registro de subvenciones da una fila por concesión del Bono (convocatorias de 2022 y de 2025), con la comarca y no el municipio, y solo las concedidas ✅ ([Concessions del RAISC](https://analisi.transparenciacatalunya.cat/d/s9xt-n979))
- **En el País Vasco y en Navarra el Bono no se aplica** (RD 42/2022), y tampoco el Plan 2026-2030 (RD 326/2026, art. 1.5) ✅

Por eso pedimos que el portal de la Comunidad publique el Bono cada año, por municipio. Así se puede comprobar la predicción de 2024 ([PREREGISTRO.md](../PREREGISTRO.md)) y rehacer cada año la base del estudio del art. 135. El contraste de este proyecto necesita las solicitudes por municipio: hoy, que sepamos, solo se puede hacer en Madrid.

## Lo que el Gobierno de Madrid ha dado en la Asamblea (PDF, no datos abiertos)
- **Convocatoria de 2024** (plazo abierto desde el 3-feb-2025): [BOAM núm. 126](https://www.asambleamadrid.es/static/doc/publicaciones/BOAM_13_00126.pdf), 30-oct-2025, págs. 28282-28285, respuesta a la PE-3506/2025. Unas 13.460 solicitudes, **sin municipio**, y una tabla de expedientes admitidos por municipio de las órdenes del 18-jun-2025 (1.999) y del 12-ago-2025 (782), con el plazo aún abierto ✅. Son concesiones, no solicitudes, y la tabla se descoloca al copiar el texto del PDF
- **Por sexo, edad y código postal:** [BOAM núm. 131](https://www.asambleamadrid.es/static/doc/publicaciones/BOAM_13_00131.pdf), 27-nov-2025, PE-4037/2025: 2.771 admitidos de 2024 con la convocatoria abierta ✅. Un código postal no es un municipio
- **El Bono de 2022, en el mismo BOAM 131 (PE-4038/2025):** 51.735 solicitudes y 11.477 personas beneficiarias. El presupuesto (63,6 M€) se declaró agotado el 6-nov-2023, y «algo más de 27.000 solicitantes fueron excluidos por ese único motivo»; unos 10.550, por no acreditar los requisitos ✅. O sea: **más de la mitad de quienes lo pidieron se quedaron fuera solo porque se acabó el dinero.** Por eso importa cómo se reparte
- **¿Sirve para comprobar la predicción?** Todavía no: la predicción es sobre solicitudes por joven ([PREREGISTRO.md](../PREREGISTRO.md)), y esto son concesiones, parciales y en PDF
- **Otro conjunto que no es el Bono:** [Ayudas al alquiler para jóvenes y sectores de escasos recursos (2022 y 2023)](https://datos.comunidad.madrid/dataset/spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos), por municipio. Es la ayuda del Plan 2022-2025 (programa 5.1 para jóvenes), con los mismos topes. Ya lo usamos: es la prueba de robustez de [ANALISIS.md](../ANALISIS.md)

## Comunidad a comunidad
| Comunidad | Qué publica del Bono | Dónde se buscó |
|---|---|---|
| **Madrid** | ✅ Por municipio, solo 2022 (CSV y JSON, CC BY 4.0). La convocatoria de 2024 está en la BDNS, sin municipio | [Portal de datos abiertos](https://datos.comunidad.madrid/dataset/spacm_bono_alquiler_joven_2022) |
| **Cataluña** | ✅ Por comarca, solo las concedidas (2022 y 2025) | [RAISC](https://analisi.transparenciacatalunya.cat/d/s9xt-n979) |
| Andalucía, Aragón, Illes Balears, Canarias, Comunitat Valenciana, Murcia | ❓ Nada del Bono en sus portales (búsqueda en su catálogo CKAN) | Sus portales y datos.gob.es |
| Castilla y León | ❓ Nada en su portal (OpenDataSoft). Las resoluciones, en PDF | Su portal y datos.gob.es |
| Galicia | ❓ Nada con «aluguer», «bono», «xove» ni «mocidade» | abertos.xunta.gal y datos.gob.es |
| Asturias, Cantabria, Castilla-La Mancha, Extremadura, La Rioja, Ceuta y Melilla | ❓ Nada en datos.gob.es. Sus portales no se pudieron buscar por conjunto, o no tienen | datos.gob.es |
| País Vasco y Navarra | No se aplica el Bono | RD 42/2022 |

## Límites
- En datos.gob.es se busca por el título: un conjunto del Bono con otro título se pudo escapar
- No abrimos los PDF de los boletines, así que no sabemos si traen el municipio
- Los registros generales de subvenciones concedidas solo se miraron en Cataluña, en la Comunitat Valenciana (un mes) y en Andalucía
- El 23-nov se leyeron 64 boletines de la Asamblea de Madrid (oct-2025 a nov-2026): solo el 126 y el 131 traen datos del Bono. No se miraron a fondo los boletines en PDF de las demás comunidades ni las webs de los ayuntamientos
- No se copió ningún dato personal: solo recuentos y nombres de campos
