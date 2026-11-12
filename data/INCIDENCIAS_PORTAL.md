# Incidencias en los datos abiertos que usamos

Para devolverlas al Portal de Datos Abiertos de la Comunidad de Madrid. Generado por `scripts/incidencias_portal.py`: cada una se comprueba con los ficheros, así que no depende de lo que digamos nosotros. Ninguna cambia nuestros resultados: todas tienen su solución en el código. Las 6 se enviaron a la Comunidad el 8-nov-2026, por su canal de atención al ciudadano (012), para el equipo del portal.

| # | Tipo | Conjunto | Qué pasa | Propuesta | Comprobado |
|---|---|---|---|---|---|
| 1 | error | [irpf_declaraciones_por_tramo](https://datos.comunidad.madrid/dataset/irpf_declaraciones_por_tramo) | El tramo «Entre 12.020,01 y 18.030,00 euros» dice «Miles euros» en la columna Unidad, pero es un número de declaraciones, como los demás tramos | Cambiar la unidad de ese tramo a «Número» | ✅ |
| 2 | aviso | [spacm_bono_alquiler_joven_2022](https://datos.comunidad.madrid/dataset/spacm_bono_alquiler_joven_2022) | 20 de los 179 municipios no tienen fila en el Bono 2022, y ninguna fila tiene 0 solicitudes: no se sabe si en esos municipios nadie la pidió o si falta el dato | Publicar los 179 municipios, con 0 donde no hubo solicitudes (o decir en la descripción que las filas que faltan son ceros) | ✅ |
| 3 | aviso | [spacm_bono_alquiler_joven_2022](https://datos.comunidad.madrid/dataset/spacm_bono_alquiler_joven_2022) | Hay una fila «Otro» con «-» como código de municipio: en el Bono 2022, 3.352 solicitudes, todas rechazadas. La descripción no dice qué son | Explicar en la descripción qué recoge «Otro» (por ejemplo, solicitudes sin vivienda en la Comunidad) y dejar vacío el código en vez de «-» | ✅ |
| 4 | aviso | [spacm_bono_alquiler_joven_2022](https://datos.comunidad.madrid/dataset/spacm_bono_alquiler_joven_2022) | Dentro del mismo portal, el municipio va con dos códigos distintos: el INE de 3 cifras en los datos del Bono y de las Ayudas, y el código estadístico de la Comunidad (INE × 10 + dígito de control) en el IRPF, la población o el paro. Para cruzarlos hace falta una tabla de equivalencias | Añadir en todos los conjuntos una columna con el código INE de 5 cifras (28106 para Parla) | ✅ |
| 5 | aviso | [irpf_declaraciones_por_tramo](https://datos.comunidad.madrid/dataset/irpf_declaraciones_por_tramo) | Entre el 21-oct y el 6-nov estos ficheros pasaron de Latin-1 a UTF-8 (además de añadir el último año). Un programa que lea la codificación fija deja de funcionar o lee mal las tildes | Mantener una codificación (UTF-8) en todos los ficheros y anotar los cambios de formato en el historial del conjunto | ✅ |
| 6 | aviso | [irpf_declaraciones_por_tramo](https://datos.comunidad.madrid/dataset/irpf_declaraciones_por_tramo) | La tabla mezcla dos juegos de tramos: en unos años el último es «Más de 21.035,00 euros» y en otros hay tres tramos por encima de 21.035 €. La descripción del conjunto no lo dice | Decirlo en la descripción, o publicar los años antiguos en un recurso aparte | ✅ |

## Pruebas y cómo lo resolvemos

**1. irpf_unidad** — scripts/requisito_ingresos.py lo trata como número y comprueba que los tramos suman el total.

```json
{
 "unidades_que_no_son_numero": {
  "Entre 12.020,01 y 18.030,00 euros": [
   "Miles euros"
  ]
 },
 "filas_con_ese_tramo": 2865,
 "municipios_2024_donde_los_tramos_suman_el_total": "157 de 157"
}
```

**2. cero_o_sin_dato** — El contraste solo usa los 159 municipios con fila y no los trata como ceros (PREREGISTRO.md).

```json
{
 "spacm_bono_alquiler_joven_2022": [
  {
   "grupo": "todo",
   "municipios_con_fila": 159,
   "municipios_sin_fila": 20,
   "filas_con_0_solicitudes": 0
  }
 ],
 "spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos": [
  {
   "grupo": "2.0 2022",
   "municipios_con_fila": 136,
   "municipios_sin_fila": 43,
   "filas_con_0_solicitudes": 0
  },
  {
   "grupo": "2.0 2023",
   "municipios_con_fila": 143,
   "municipios_sin_fila": 36,
   "filas_con_0_solicitudes": 0
  },
  {
   "grupo": "5.1 2022",
   "municipios_con_fila": 127,
   "municipios_sin_fila": 52,
   "filas_con_0_solicitudes": 0
  },
  {
   "grupo": "5.1 2023",
   "municipios_con_fila": 135,
   "municipios_sin_fila": 44,
   "filas_con_0_solicitudes": 0
  }
 ]
}
```

**3. fila_otro** — scripts/base_datos.py guarda solo los códigos de 3 cifras y lleva la cifra de «Otro» a la tabla metadatos.

```json
{
 "spacm_bono_alquiler_joven_2022": {
  "filas": 1,
  "codigos": [
   "-"
  ],
  "solicitudes": 3352,
  "aceptadas": 0,
  "la_descripcion_lo_explica": false
 },
 "spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos": {
  "filas": 4,
  "codigos": [
   "-"
  ],
  "solicitudes": 46,
  "aceptadas": 0,
  "la_descripcion_lo_explica": false
 }
}
```

**4. dos_codigos** — scripts/codigos_municipios.py hace la tabla de equivalencias de los 179 municipios.

```json
{
 "parla": {
  "bono_2022": "106",
  "irpf_por_tramo": "1065"
 }
}
```

**5. codificacion** — scripts/comun.py (leer_csv) prueba las dos codificaciones.

```json
{
 "irpf_declaraciones_por_tramo": {
  "21-oct": "Latin-1",
  "6-nov": "UTF-8"
 },
 "irpf_indicador_renta": {
  "21-oct": "Latin-1",
  "6-nov": "UTF-8"
 },
 "paro_registrado_edad_municipio": {
  "21-oct": "Latin-1",
  "6-nov": "UTF-8"
 }
}
```

**6. irpf_tramos** — Solo usamos 2021 y 2024, que tienen los tramos completos.

```json
{
 "anios_con_mas_de_21035": [
  2010,
  2011,
  2012,
  2013,
  2014
 ],
 "anios_con_tramos_hasta_60101": [
  2015,
  2016,
  2017,
  2018,
  2019,
  2020,
  2021,
  2022,
  2023,
  2024
 ]
}
```
