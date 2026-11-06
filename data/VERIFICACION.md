# Verificación de las descargas (05-11-2026)

Generado por `scripts/verificar_descargas.py`. Compara cada fichero de `data/raw/` con el portal oficial: filas frente al total de la API DataStore y huella SHA-256 frente a una descarga nueva. No sobrescribe nada.

| Dataset | Filas (nuestras) | Filas (API) | Huella | Estado |
|---|---|---|---|---|
| `1934246` | 32 | 32 | `316e6c3f4465` | ✅ mismo contenido (el portal regenera el fichero; solo cambian los bytes) |
| `1934258` | 108 | 108 | `15032e63a9fd` | ✅ mismo contenido (el portal regenera el fichero; solo cambian los bytes) |
| `1934261` | 108 | 108 | `de83350546fa` | ✅ mismo contenido (el portal regenera el fichero; solo cambian los bytes) |
| `1934430` | 294 | 294 | `c3cd6ca79188` | ✅ mismo contenido (el portal regenera el fichero; solo cambian los bytes) |
| `1934445` | 2520 | 2520 | `fdd1e626a3e5` | ✅ mismo contenido (el portal regenera el fichero; solo cambian los bytes) |
| `302038` | 4011 | 4011 | `96d5b9a1f6e0` | ✅ mismo contenido (el portal regenera el fichero; solo cambian los bytes) |
| `alquiler_medio_mensual_viviendas_arrendadas_valor_catastral_municipios_mas_20000` | 720 | 720 | `c7fda62530ca` | ✅ mismo contenido (el portal regenera el fichero; solo cambian los bytes) |
| `censo_2021_viviendas_familiares_por_tenencia` | 567 | 567 | `cb899424b614` | ✅ mismo contenido (el portal regenera el fichero; solo cambian los bytes) |
| `grado_juventud_por_edad` | 22156 | 22156 | `37ce49f9d837` | ✅ mismo contenido (el portal regenera el fichero; solo cambian los bytes) |
| `irpf_declaraciones_por_tramo` | 20089 | 2000 | `58ea903147ad` | 🔄 el portal tiene datos nuevos: +1530 / −0 filas (años de las filas nuevas: 2024) · la API DataStore da 2000 filas |
| `irpf_indicador_renta` | 5157 | 5730 | `bc23b1d2e3ee` | 🔄 el portal tiene datos nuevos: +573 / −0 filas (años de las filas nuevas: 2024) · la API DataStore da 5730 filas |
| `paro_registrado_edad_municipio` | 151434 | 151971 | `21d56bcca41a` | 🔄 el portal tiene datos nuevos: +537 / −0 filas (años de las filas nuevas: 2026) · la API DataStore da 151971 filas |
| `poblacion_censada_por_edad_nacionalidad_y_sexo` | 189090 | 189090 | `dd75084475aa` | ✅ mismo contenido (el portal regenera el fichero; solo cambian los bytes) |
| `serpavi_mivau` | Excel (varias hojas) | — | `md5 bff6497f571b` | ✅ idéntico (MD5 y tamaño) · servidor: Thu, 09 Jul 2026 06:11:57 GMT |
| `spacm_ayudas_alquiler_vivienda_jovenes_sectores_escasos_recursos` | 545 | 545 | `9bae1438e499` | ✅ idéntico al portal (byte a byte) |
| `spacm_bono_alquiler_joven_2022` | 160 | 160 | `af30b424617a` | ✅ idéntico al portal (byte a byte) |
