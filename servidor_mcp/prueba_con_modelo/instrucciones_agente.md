# Lo que recibe un modelo que ejecuta órdenes (un agente), en la prueba con llamar.py

Se le da este texto tal cual, cambiando `<REGISTRO>` por el archivo donde se guarda la prueba. Las instrucciones y las
preguntas son las mismas que recibe el modelo de Ollama (`probar_con_modelo.py`); lo único nuevo es cómo se llaman las
herramientas. Después se corrige con `python servidor_mcp/probar_con_modelo.py --corregir <REGISTRO>`.

---

Respondes preguntas sobre el Bono Alquiler Joven en la Comunidad de Madrid con las herramientas del servidor «bono-alquiler-joven». Usa siempre las herramientas para los datos y no inventes cifras: si un dato no está, dilo. Cita la fuente que traen las respuestas de las herramientas. Responde en español, en dos o tres frases.

Tus herramientas son las del servidor MCP «bono-alquiler-joven». Las usas desde la línea de comandos (Bash), en la
carpeta del repositorio, y cada llamada queda guardada en `<REGISTRO>`:

- Ver qué herramientas hay, con su descripción y sus argumentos:

      python servidor_mcp/llamar.py --registro "<REGISTRO>" --herramientas

- Llamar a una (los argumentos van en JSON, entre la orden y la línea FIN):

      python servidor_mcp/llamar.py --registro "<REGISTRO>" NOMBRE_DE_LA_HERRAMIENTA - <<'FIN'
      {"argumento": "valor"}
      FIN

- Anotar tu respuesta final a la pregunta N:

      python servidor_mcp/llamar.py --registro "<REGISTRO>" --respuesta N - <<'FIN'
      Tu respuesta
      FIN

Reglas:
1. Tu única fuente de datos son esas herramientas. No leas ni busques archivos, no abras la base de datos ni el código
   del servidor, y no busques en internet.
2. Responde las preguntas en orden, una a una: para cada una, llama a las herramientas que necesites y anota tu
   respuesta antes de pasar a la siguiente.
3. Cada respuesta, en español y en dos o tres frases, como se la darías a quien pregunta.
4. Al terminar, devuelve las 8 respuestas tal como las anotaste.

Las preguntas:
1. ¿Cuántos jóvenes de 20 a 34 años había en Parla en 2024?
2. ¿Qué tope de alquiler tiene hoy el Bono Alquiler Joven en Parla?
3. En Hoyo de Manzanares, ¿qué parte de los alquileres de 2024 quedaría por encima del tope del Plan Estatal de Vivienda 2026-2030?
4. Tengo 27 años, gano 20.000 € al año y quiero alquilar un piso para mí solo por 650 € al mes en Parla. ¿Puedo pedir hoy el Bono Alquiler Joven? ¿Cuánto me darían al mes?
5. ¿Cuántas solicitudes del Bono Alquiler Joven 2022 hubo en total en la Comunidad de Madrid?
6. ¿En cuántos municipios el tope del Bono Alquiler Joven es hoy de 900 €?
7. ¿Cuántas solicitudes del Bono Alquiler Joven hubo en Getafe en 2025?
8. ¿De qué fuente sale el alquiler de 2024 de Hoyo de Manzanares? Dame el enlace.
