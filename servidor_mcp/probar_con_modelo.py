#!/usr/bin/env python3
"""A real test of the MCP server with a language model: an open model running locally (Ollama) gets 8 questions in
Spanish and the 6 tools of servidor.py, decides by itself which tools to call, and answers. Every answer is checked
against what the tools return (the expected figure is read from the same tools before asking the model).

What we expect and when a question counts as right were written before the first run, in PRUEBA_CON_MODELO.md (same
commit as this script). A question counts as right only if the model called at least one tool and the expected figure
or name is in its final answer; question 7 (a year that is not in the data) is graded by hand with the rule written
there. «Cita la fuente» is separate: the answer names a source that the tools returned.

Not part of scripts/rehacer_todo.py: it needs Ollama, and a model's answers can change from one machine or version to
another, so this is a recorded run (servidor_mcp/prueba_con_modelo/), not a result that is rebuilt.

Run:  ollama pull llama3.2:3b   (once)
      python servidor_mcp/probar_con_modelo.py [--modelo llama3.2:3b]

A model that runs commands instead (an agent) answers the same 8 questions with llamar.py, which records every call
and answer (prueba_con_modelo/instrucciones_agente.md); then the run is graded with the same rule and the same code:
      python servidor_mcp/probar_con_modelo.py --corregir REGISTRO.jsonl --modelo NOMBRE --como "CÓMO SE EJECUTÓ"
"""
import argparse
import asyncio
import datetime
import json
import os
import platform
import re
import sys
import time
import urllib.request
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from probar_servidor import SERVER, attr, content

OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
OUT = Path(__file__).with_name("prueba_con_modelo")
MAX_ROUNDS = 6
MAX_TOOL_CHARS = 8000  # a tool answer longer than this reaches the model cut (said in the transcript)

SYSTEM = ("Respondes preguntas sobre el Bono Alquiler Joven en la Comunidad de Madrid con las herramientas del servidor "
          "«bono-alquiler-joven». Usa siempre las herramientas para los datos y no inventes cifras: si un dato no está, "
          "dilo. Cita la fuente que traen las respuestas de las herramientas. Responde en español, en dos o tres frases.")

QUESTIONS = [
    ("jovenes_parla", "¿Cuántos jóvenes de 20 a 34 años había en Parla en 2024?"),
    ("tope_hoy_parla", "¿Qué tope de alquiler tiene hoy el Bono Alquiler Joven en Parla?"),
    ("hoyo_plan", "En Hoyo de Manzanares, ¿qué parte de los alquileres de 2024 quedaría por encima del tope del Plan "
                  "Estatal de Vivienda 2026-2030?"),
    ("puedo_parla", "Tengo 27 años, gano 20.000 € al año y quiero alquilar un piso para mí solo por 650 € al mes en "
                    "Parla. ¿Puedo pedir hoy el Bono Alquiler Joven? ¿Cuánto me darían al mes?"),
    ("total_2022", "¿Cuántas solicitudes del Bono Alquiler Joven 2022 hubo en total en la Comunidad de Madrid?"),
    ("municipios_900", "¿En cuántos municipios el tope del Bono Alquiler Joven es hoy de 900 €?"),
    ("trampa_2025", "¿Cuántas solicitudes del Bono Alquiler Joven hubo en Getafe en 2025?"),
    ("fuente_hoyo", "¿De qué fuente sale el alquiler de 2024 de Hoyo de Manzanares? Dame el enlace."),
]

SOURCE_WORDS = ("serpavi", "mivau", "datos.comunidad.madrid", "portal de datos abiertos", "boe", "bdns",
                "infosubvenciones", "ine.es", "real decreto", "rd 326", "github.com/alessandrorodriguez881")


def number_forms(n):
    """22649 -> 22649, 22.649, 22,649, 22 649 (and the narrow no-break space)."""
    n = int(round(n))
    plain = str(n)
    if n < 1000:
        return [plain]
    grouped = f"{n:,}"
    return [plain, grouped, grouped.replace(",", "."), grouped.replace(",", " "), grouped.replace(",", " ")]


def percent_forms(share):
    """0.928 -> 92,8 / 92.8 / 93 followed by % (with or without space) or «por ciento»."""
    one = f"{100 * share:.1f}"
    nums = {one, one.replace(".", ","), str(round(100 * share))}
    return [f"{x}{sep}" for x in nums for sep in ("%", " %", " %", " por ciento")]


async def expected_values(session):
    """The right answers, read from the same tools the model gets."""
    call = lambda tool, **args: session.call_tool(tool, args)  # noqa: E731
    parla = content(await call("ficha_municipio", municipio="Parla"))
    hoyo = content(await call("ficha_municipio", municipio="Hoyo de Manzanares"))
    cap = lambda card, rule: next(t for t in card["topes"] if t["regla"] == rule)  # noqa: E731
    can = content(await call("puedo_pedirla", municipio="Parla", edad=27, precio=650, ingresos=20000))
    total = content(await call("consulta_sql", sql="SELECT SUM(solicitudes) AS n FROM solicitudes "
                                                   "WHERE programa = 'bono_alquiler_joven' AND anio_convocatoria = 2022"))
    n900 = content(await call("consulta_sql", sql="SELECT COUNT(*) AS n FROM topes "
                                                  "WHERE regla = 'bono_2024' AND tope_piso = 900"))
    years = content(await call("consulta_sql", sql="SELECT DISTINCT anio_convocatoria FROM solicitudes "
                                                   "WHERE programa = 'bono_alquiler_joven'"))
    serpavi = [f for f in hoyo["fuentes"] if "serpavi" in (f.get("fuente", "") + f.get("url", "")).lower()]
    assert can["hoy"]["cumple"] and serpavi
    return {
        "jovenes_parla": {"valor": parla["jovenes_20_34_2024"], "vale": number_forms(parla["jovenes_20_34_2024"])},
        "tope_hoy_parla": {"valor": cap(parla, "bono_2024")["tope_piso"],
                           "vale": number_forms(cap(parla, "bono_2024")["tope_piso"])},
        "hoyo_plan": {"valor": cap(hoyo, "plan_2026_2030")["parte_alquiler_2024_por_encima"],
                      "vale": percent_forms(cap(hoyo, "plan_2026_2030")["parte_alquiler_2024_por_encima"])},
        "puedo_parla": {"valor": {"cumple_hoy": can["hoy"]["cumple"], "ayuda_al_mes": can["hoy"]["ayuda_al_mes"]},
                        "vale": number_forms(can["hoy"]["ayuda_al_mes"])},
        "total_2022": {"valor": total["filas"][0][0], "vale": number_forms(total["filas"][0][0])},
        "municipios_900": {"valor": n900["filas"][0][0], "vale": number_forms(n900["filas"][0][0])},
        "trampa_2025": {"valor": {"anios_del_bono_en_la_base": [r[0] for r in years["filas"]]},
                        "vale": None},
        "fuente_hoyo": {"valor": serpavi[0], "vale": ["serpavi", "mivau.gob.es"]},
    }


def ollama(path, payload=None, timeout=900):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def as_ollama_tools(tools):
    return [{"type": "function", "function": {"name": t.name, "description": t.description or "",
                                              "parameters": attr(t, "input_schema", "inputSchema")}} for t in tools]


def tool_text(result):
    if attr(result, "is_error", "isError"):
        return "ERROR: " + " ".join(c.text for c in result.content if getattr(c, "text", None))
    text = json.dumps(content(result), ensure_ascii=False)
    if len(text) > MAX_TOOL_CHARS:
        text = text[:MAX_TOOL_CHARS] + f" …[cortado: {len(text)} caracteres]"
    return text


async def ask(session, model, tools, question):
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    calls, start = [], time.time()
    for _ in range(MAX_ROUNDS):
        reply = ollama("/api/chat", {"model": model, "messages": messages, "tools": tools, "stream": False,
                                     "options": {"temperature": 0, "seed": 42, "num_ctx": 8192}})
        msg = reply["message"]
        messages.append({k: v for k, v in msg.items() if k in ("role", "content", "tool_calls")})
        if not msg.get("tool_calls"):
            return msg.get("content", ""), calls, round(time.time() - start, 1)
        for tc in msg["tool_calls"]:
            name, args = tc["function"]["name"], tc["function"].get("arguments") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            try:
                text = tool_text(await session.call_tool(name, args))
            except Exception as e:  # noqa: BLE001 - an unknown tool or bad arguments go back to the model as text
                text = f"ERROR: {type(e).__name__}: {e}"
            calls.append({"herramienta": name, "argumentos": args, "respuesta": text[:600]})
            messages.append({"role": "tool", "tool_name": name, "content": text})
    return "(sin respuesta final: se acabaron las rondas)", calls, round(time.time() - start, 1)


def grade(qid, answer, calls, expected):
    low = answer.lower()
    cites = any(w in low for w in SOURCE_WORDS)
    if expected["vale"] is None:
        return {"acierta": None, "cita_fuente": cites, "nota": "se corrige a mano (regla en PRUEBA_CON_MODELO.md)"}
    found = any(v.lower() in low for v in expected["vale"])
    if qid == "puedo_parla":  # also has to say yes
        found = found and not re.search(r"\bno (puedes|cumples|podr[ií]as)\b", low)
    return {"acierta": bool(found and calls), "cifra_bien": bool(found), "cita_fuente": cites,
            "nota": "" if calls else "no llamó a ninguna herramienta"}


def read_log(path):
    """A run recorded by llamar.py --registro: the calls made before an answer belong to that question."""
    entries = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    answers, pending, made = {}, [], 0
    for e in entries:
        if "herramienta" in e:
            pending.append({k: e[k] for k in ("herramienta", "argumentos", "respuesta")})
            made += 1
        elif "respuesta_a" in e:  # an answer given twice keeps the last text and every call
            calls = answers.get(e["respuesta_a"], {}).get("llamadas", []) + pending
            answers[e["respuesta_a"]] = {"texto": e["texto"], "llamadas": calls, "hora": e["hora"],
                                         "llamadas_antes_en_la_conversacion": made}
            pending = []
    return entries, answers, pending


async def grade_log(path, model, how, instructions):
    entries, answers, leftover = read_log(path)
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            expected = await expected_values(session)
    rows = []
    for n, (qid, question) in enumerate(QUESTIONS, 1):
        given = answers.get(n, {"texto": "(sin respuesta)", "llamadas": [], "hora": None,
                                "llamadas_antes_en_la_conversacion": 0})
        row = {"id": qid, "pregunta": question, "respuesta": given["texto"], "herramientas": given["llamadas"],
               "hora": given["hora"], "esperado": expected[qid]["valor"]}
        row.update(grade(qid, given["texto"], given["llamadas"], expected[qid]))
        # Added after the first agent runs (20-nov): all 8 questions go in one conversation, and a model may answer
        # with what an earlier call already brought (the card of Parla answers questions 1 and 2). This second count
        # takes any call made before the answer; the rule written before stays in «acierta».
        before = given["llamadas_antes_en_la_conversacion"]
        row["llamadas_antes_en_la_conversacion"] = before
        row["acierta_con_lo_ya_traido"] = None if row["acierta"] is None else bool(row["cifra_bien"] and before)
        rows.append(row)
        print(f"{qid}: acierta={row['acierta']} cifra_bien={row.get('cifra_bien')} "
              f"con_lo_ya_traido={row['acierta_con_lo_ya_traido']} cita_fuente={row['cita_fuente']} "
              f"herramientas={[c['herramienta'] for c in given['llamadas']]}", flush=True)
    start = datetime.datetime.fromisoformat(entries[0]["hora"])
    path_out = OUT / f"{start:%Y-%m-%d_%H%M}_{model.replace(':', '_').replace('/', '_')}.json"
    record = {"fecha": entries[0]["hora"], "fin": entries[-1]["hora"], "modelo": model, "como": how,
              "registro": Path(path).name, "equipo": platform.platform(),
              "instrucciones": Path(instructions).read_text(encoding="utf-8") if instructions else None,
              "llamadas_sin_respuesta_despues": leftover, "preguntas": rows,
              "aciertos": sum(r["acierta"] is True for r in rows),
              "aciertos_con_lo_ya_traido": sum(r["acierta_con_lo_ya_traido"] is True for r in rows),
              "corregidas_solas": sum(r["acierta"] is not None for r in rows),
              "citan_fuente": sum(r["cita_fuente"] for r in rows)}
    path_out.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{record['aciertos']} de {record['corregidas_solas']} corregidas solas con la regla escrita antes; "
          f"{record['aciertos_con_lo_ya_traido']} con lo ya traído en la conversación; citan fuente "
          f"{record['citan_fuente']} de {len(rows)} -> {path_out.name}")


async def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--modelo", default="llama3.2:3b")
    parser.add_argument("--corregir", metavar="REGISTRO", help="grade a run recorded by llamar.py (no Ollama)")
    parser.add_argument("--como", default="", help="with --corregir: how the model was run")
    parser.add_argument("--instrucciones", help="with --corregir: the file with the instructions the model got")
    opts = parser.parse_args()
    if opts.corregir:
        return await grade_log(opts.corregir, opts.modelo, opts.como, opts.instrucciones)
    model = opts.modelo
    version = ollama("/api/version")["version"]
    info = next(m for m in ollama("/api/tags")["models"] if m["name"] == model)

    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            expected = await expected_values(session)
            rows = []
            for qid, question in QUESTIONS:
                answer, calls, seconds = await ask(session, model, as_ollama_tools(tools), question)
                row = {"id": qid, "pregunta": question, "respuesta": answer, "herramientas": calls,
                       "segundos": seconds, "esperado": expected[qid]["valor"]}
                row.update(grade(qid, answer, calls, expected[qid]))
                rows.append(row)
                print(f"{qid}: acierta={row['acierta']} cita_fuente={row['cita_fuente']} "
                      f"herramientas={[c['herramienta'] for c in calls]} ({seconds} s)", flush=True)

    now = datetime.datetime.now()
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{now:%Y-%m-%d_%H%M}_{model.replace(':', '_').replace('/', '_')}.json"
    record = {"fecha": now.isoformat(timespec="seconds"), "modelo": model, "digest": info["digest"],
              "parametros": info["details"].get("parameter_size"), "cuantizacion": info["details"].get("quantization_level"),
              "ollama": version, "opciones": {"temperature": 0, "seed": 42, "num_ctx": 8192},
              "equipo": platform.platform(), "instrucciones": SYSTEM, "preguntas": rows,
              "aciertos": sum(r["acierta"] is True for r in rows),
              "corregidas_solas": sum(r["acierta"] is not None for r in rows),
              "citan_fuente": sum(r["cita_fuente"] for r in rows)}
    path.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{record['aciertos']} de {record['corregidas_solas']} corregidas solas; citan fuente {record['citan_fuente']} "
          f"de {len(rows)} -> {path.name}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main())
