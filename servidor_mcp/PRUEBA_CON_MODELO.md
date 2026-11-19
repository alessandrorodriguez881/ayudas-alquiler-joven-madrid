# El servidor MCP, probado con un modelo de verdad

`probar_servidor.py` prueba las seis herramientas con el cliente oficial de MCP, pero sin ningún modelo: llama a cada
herramienta con respuestas conocidas. Aquí un modelo de lenguaje recibe preguntas y las herramientas, decide él qué
llamar y responde. Usamos un modelo **abierto y pequeño que funciona en local** (Llama 3.2 de 3.200 millones de
parámetros, con Ollama), sin cuentas ni claves: si funciona con uno así, el servidor no depende de un proveedor.

```bash
ollama pull llama3.2:3b                      # una vez
python servidor_mcp/probar_con_modelo.py     # unos minutos; guarda la conversación en servidor_mcp/prueba_con_modelo/
```

No entra en `scripts/rehacer_todo.py`: necesita Ollama, y las respuestas de un modelo pueden cambiar con el equipo o
la versión. Es una prueba guardada, con la fecha, el modelo y su huella, no un resultado que se rehace.

## Lo esperado, escrito antes de la primera ejecución (jue 19-nov-2026)
**Las 8 preguntas** (en `probar_con_modelo.py`): los jóvenes de Parla, el tope de hoy en Parla, la parte del alquiler
de Hoyo de Manzanares por encima del tope del Plan, si un joven de 27 años puede pedirla en Parla y cuánto cobraría,
las solicitudes de 2022 en toda la Comunidad, en cuántos municipios el tope es de 900 €, las solicitudes de Getafe en
2025 (una trampa: la base solo tiene el Bono de 2022) y la fuente del alquiler de Hoyo de Manzanares.

**Cuándo una respuesta está bien:** el modelo ha llamado al menos a una herramienta y en su respuesta está la cifra o el
nombre que devuelven las herramientas (el script los lee antes de preguntar). La de Getafe se corrige a mano: vale si
dice que no hay datos de 2025 y no da ninguna cifra para ese año. «Cita la fuente» se cuenta aparte: la respuesta
nombra una fuente que trajeron las herramientas (SERPAVI, el portal, el BOE…).

**Lo que esperamos de un modelo tan pequeño:** que use las herramientas en al menos 6 de las 8 y acierte entre 4 y 6.
Que falle sobre todo al escribir SQL (las solicitudes de 2022 y los municipios con 900 €) y en «¿puedo pedirla?», que
tiene muchos parámetros. Y que cite la fuente en menos de la mitad, salvo en la última, que la pide.

**Para qué sirve:** si acierta, se puede decir que el servidor funciona con un modelo abierto en local, no solo con
Claude. Si falla, el fallo dice qué herramienta o qué descripción hay que aclarar, o que hace falta un modelo mayor.

## Lo que salió
(Se escribe después de la primera ejecución, sin cambiar lo de arriba.)
