# Documentos oficiales guardados (leídos el 27-oct-2026)

| Archivo | Qué es | Fuente | MD5 |
|---|---|---|---|
| `BASES_DATAMAD_2026.pdf` | Bases de DataMad 2026 (8 páginas) | [Google Drive de la organización](https://drive.google.com/file/d/1ZL2NdY1P5FxTgfFX5Zeb2qnVcoxxo9zm/view), enlazado desde [eventos.urjc.es](https://eventos.urjc.es/155632/detail/datamad-2026.html) | da0ce34967ea975790643f0524e8345b |
| `Acuerdo_CG_14-09-2022_Bono_Alquiler_Joven.pdf` | Acuerdo del Consejo de Gobierno: requisitos (art. 4), crédito (art. 9) y Anexo II con los 29 municipios de tope 900 € | [sede.comunidad.madrid](https://sede.comunidad.madrid/sites/default/files/ADEL/ckeditor/ayudas%20becas%20y%20subvenciones/A235/acuerdo_del_consejo_de_gobierno_bono_alquiler_joven.pdf) | 38933840d1d885741eb9ae466631ddfa |
| `BOCM-20220920-16_extracto_acuerdo.pdf` | Extracto del Acuerdo en el BOCM n.º 224 (tope 600/300 € y 900/450 €) | [bocm.es](https://www.bocm.es/boletin/CM_Orden_BOCM/2022/09/20/BOCM-20220920-16.PDF) | 7870588bd7158d77b08f0007701b4572 |
| `BOCM-20240816-2_excluidos_credito_agotado.pdf` | Orden de 1-ago-2024: excluidos por requisitos o por **crédito agotado** (agotado por Orden de 6-nov-2023, BOCM n.º 271) | [bocm.es](https://www.bocm.es/boletin/CM_Orden_BOCM/2024/08/16/BOCM-20240816-2.PDF) | 38aacf3d6884141321312bf2775fe561 |

No se ha descargado el listado nominativo de excluidos (está en la sede y trae nombres y DNI): datos personales, fuera de lo que pide el proyecto (bases, apartado 6.6).

## Listas de municipios con tope de 900 € por convocatoria (añadido el 6-nov-2026)
Textos completos sacados de la Base de Datos Nacional de Subvenciones (BDNS) con su API pública (`https://www.infosubvenciones.es/bdnstrans/api/convocatorias/documentos?idDocumento=<id>`). Son versiones anonimizadas: no traen datos personales. Los lee `scripts/topes_convocatorias.py`, que los vuelve a bajar si faltan y comprueba el MD5.

| Archivo | Qué es | Municipios con 900 € | MD5 |
|---|---|---|---|
| `BDNS_654786_convocatoria_ayudas_alquiler_jovenes_2022.pdf` | Ayudas al alquiler y jóvenes 2022 (doc. 804712) | 29 (Comisión de Seguimiento de 23-sep-2022) | 4862c65f6f47da691294509a9756702d |
| `BDNS_721190_convocatoria_ayudas_alquiler_jovenes_2023.pdf` | Ayudas al alquiler y jóvenes 2023 (doc. 963957) | 29 (los mismos) | 4763566415618964cc0a9f6cb16b3344 |
| `BDNS_793423_convocatoria_ayudas_alquiler_jovenes_2024.pdf` | Ayudas al alquiler, programa de jóvenes 2024 (doc. 1150270) | 55 (Comisión de Seguimiento de 23-sep-2024) | 4f10f497e15fe7b28c7cd34610f67492 |
| `BDNS_805618_certificado_ACG_bono_2024.pdf` | Certificado del Acuerdo del Consejo de Gobierno de 26-dic-2024, Bono Alquiler Joven 2024, con su Anexo II (doc. 1505247) | 55 (Comisión Bilateral de 12-dic-2024) | e4ec7a352bb13a1dc015e77ca9ade822 |
| `BDNS_864406_convocatoria_ayudas_alquiler_jovenes_2025.pdf` | Ayudas al alquiler, programa de jóvenes 2025 (doc. 1342309); solicitudes del 4-nov al 15-dic-2025 | 55 | b300d8279a3975179487ef046593c3a8 |
| `BOCM-20251028-25.pdf` | Extracto de esa convocatoria de 2025 en el BOCM n.º 257: 21,7 M€ (10,3 M€ para jóvenes) | — | f2006f0be07b7ebdfcedea2b2b86e5a8 |

Detalles de lectura: el Anexo I de 2024 y 2025 escribe «Carmarma de Esteruelas» (es Camarma) y «Paracuellos del Jarama» (el nombre oficial es «de Jarama»); el texto de 2023 sale con letras separadas al extraerlo; en el Anexo II del Bono 2024 pone «90 0 euros» en Ajalvir. El script tiene en cuenta los tres casos y comprueba que salen 29 o 55.
