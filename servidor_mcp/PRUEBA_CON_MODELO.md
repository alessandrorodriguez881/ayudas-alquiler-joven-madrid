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
### Primera ejecución: jue 19-nov a las 22:41, con Llama 3.2 de 3.200 millones (0 de 7)
Conversación entera: `prueba_con_modelo/2026-11-19_2241_llama3.2_3b.json` (Ollama 0.40.16, temperatura 0). Un
primer intento a las 22:36 se paró antes de preguntar nada al modelo, por un fallo del script al leer las filas del
SQL; se arregló sin tocar las preguntas ni la regla.

**No acertó ninguna de las 7 que se corrigen solas, y no citó ninguna fuente.** La de Getafe (la trampa) está bien:
dice que no hay datos de 2025 y no da cifra. Mucho peor de lo que esperábamos (de 4 a 6). Lo que pasó:
- **Una sola llamada y respuesta.** Llamó a una herramienta en cada pregunta y respondió sin seguir: buscó Parla
  (`buscar_municipio`, que solo da el código) y no pidió su ficha.
- **SQL a ciegas.** Escribió columnas que no existen («tipo», «municipio», «alquiler_serpavi») sin mirar antes el
  diccionario, y no lo intentó otra vez después del error.
- **Inventó cuando le faltaba el dato.** Dijo que el tope de Parla es de «106 euros» (106 es su código INE), dio «1.444
  solicitudes» en 2022 (son 48.383) y se inventó una fuente con un enlace que no es nuestro.
- **«¿Puedo pedirla?»:** mandó `jovenes_que_firman = 0`; el servidor respondió con el error explicado (de 1 a 20) y el
  modelo no lo corrigió.

**Qué quiere decir.** El servidor respondió bien a cada llamada y sus errores llegaron explicados. Lo que falla es el
modelo: uno de 3.200 millones de parámetros no encadena herramientas. Para una demo con un modelo abierto hace falta
uno mayor, y no lo hemos probado. **No se puede decir que funcione con un modelo pequeño en local.**

**Dos mejoras que sirven para cualquier modelo** (hechas después de ver esto, en el commit siguiente):
- si una consulta SQL nombra una columna o una tabla que no existe, el error dice qué columnas hay y los valores de
  `programa` y `regla` (lo prueba `probar_servidor.py`);
- las descripciones dicen qué herramienta usar: `buscar_municipio` avisa de que los datos están en `ficha_municipio`,
  esta dice que acepta el nombre sin buscar antes, y `consulta_sql` nombra las columnas de las tablas principales.

### Segunda ejecución, después de esas mejoras: jue 19-nov a las 22:50 (0 de 7 otra vez)
No estaba en lo esperado: la hicimos después de ver la primera. Conversación entera:
`prueba_con_modelo/2026-11-19_2250_llama3.2_3b.json`.

- **El mismo resultado:** ninguna de las 7 bien, y la trampa de Getafe, bien. Citó una fuente en una de las 8.
- **El error nuevo llegó y no lo usó.** Recibió las columnas que hay y no volvió a intentarlo: sigue haciendo una sola
  llamada por pregunta.
- **Sigue inventando:** se inventó los requisitos («de 18 a 30 años», con ingresos «entre 15.000 y 20.000 euros»; el
  Bono es hasta los 35 y hasta 25.200 €) y dio un enlace que no traen nuestras herramientas.

**Conclusión de las dos:** con un modelo de este tamaño, nuestro servidor no sirve para responder a nadie, por bien
que respondan las herramientas. Por eso cada respuesta trae su fuente: para que una persona pueda comprobarla. Probar
un modelo mayor queda pendiente: hace falta descargarlo, unos 5 GB.

## Con un modelo grande: Claude, como agente que ejecuta órdenes (vie 20-nov)
Para no tocar la configuración de ninguna app ni descargar nada, el modelo es un agente de Claude Code: un subagente
nuevo de la sesión que mantiene el proyecto, sin nada de lo que esa sesión sabe. Usa las herramientas desde la línea de
comandos con `llamar.py`, que pasa cada llamada por el cliente oficial de MCP (como hace una app) y la guarda en un
registro. Recibe las mismas instrucciones y las mismas 8 preguntas que el modelo pequeño, más cómo llamar a las
herramientas: `prueba_con_modelo/instrucciones_agente.md`, tal cual. Se corrige con la misma regla y el mismo código:

```bash
python servidor_mcp/probar_con_modelo.py --corregir <registro> --modelo <modelo> --como "<cómo se ejecutó>"
```

### Lo esperado, escrito antes de ejecutarla (vie 20-nov, a las 09:25)
- **Claude Sonnet 5.5:** las 7 que se corrigen solas, bien, y la trampa de Getafe, bien. Que cite la fuente en al menos
  6 de las 8.
- **Claude Haiku 5.5** (el modelo pequeño y barato de Claude): al menos 6 de las 7, y la trampa, bien.
- Si falla alguna, se apunta igual, y lo que falle dice qué herramienta o qué descripción hay que aclarar.

**Lo que esta prueba no dice:**
- que funcione con un modelo abierto en local: el de 3.200 millones no basta, y uno mayor no lo hemos probado;
- que funcione con Gemini o con ChatGPT: necesitan una cuenta, y no lo hemos probado;
- que sea una app de chat: el agente, además de las herramientas, puede ejecutar órdenes. Le pedimos que no lea nada
  más, y el registro guarda cada llamada que hizo.
