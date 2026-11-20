#!/usr/bin/env python3
"""Calls one tool of servidor.py from the command line, through MCP with the official client (as an AI app does).
For people, and for testing the server with a model that runs commands (servidor_mcp/PRUEBA_CON_MODELO.md).

  python servidor_mcp/llamar.py --herramientas                    # the tools, with their descriptions and arguments
  python servidor_mcp/llamar.py ficha_municipio '{"municipio": "Parla"}'
  python servidor_mcp/llamar.py consulta_sql - <<'FIN'            # «-»: the arguments come from stdin
  {"sql": "SELECT COUNT(*) FROM municipios"}
  FIN

With --registro FILE every call and its answer are appended to FILE (one JSON per line), and
«--respuesta N -» (text from stdin) appends the final answer to question N: that is how a model's run is recorded,
and `probar_con_modelo.py --corregir FILE` grades it with the same rule as the open model's runs.
"""
import argparse
import asyncio
import datetime
import json
import os
import sys

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from probar_con_modelo import tool_text  # the same text (and the same cut) the open model got
from probar_servidor import SERVER, attr


def log(path, entry):
    if path:
        entry = {"hora": datetime.datetime.now().isoformat(timespec="seconds"), **entry}
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


async def run(args):
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=dict(os.environ))
    with open(os.devnull, "w") as quiet:  # the server's own log stays out: the answer is what an app shows the model
        return await call(args, params, quiet)


async def call(args, params, errlog):
    async with stdio_client(params, errlog=errlog) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            if args.herramientas:
                tools = [{"nombre": t.name, "descripcion": t.description or "",
                          "argumentos": attr(t, "input_schema", "inputSchema")}
                         for t in (await session.list_tools()).tools]
                log(args.registro, {"lista_de_herramientas": [t["nombre"] for t in tools]})
                return json.dumps(tools, ensure_ascii=False, indent=1)
            try:
                text = tool_text(await session.call_tool(args.herramienta, args.argumentos))
            except Exception as e:  # noqa: BLE001 - an unknown tool or bad arguments are answered as text
                text = f"ERROR: {type(e).__name__}: {e}"
            log(args.registro, {"herramienta": args.herramienta, "argumentos": args.argumentos, "respuesta": text[:600]})
            return text


def stdin_text():
    sys.stdin.reconfigure(encoding="utf-8")
    return sys.stdin.read().strip()


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("herramienta", nargs="?", help="the tool (or, with --respuesta, the text, or «-» for stdin)")
    p.add_argument("argumentos", nargs="?", help="the arguments in JSON, or «-» to read them from stdin")
    p.add_argument("--herramientas", action="store_true", help="list the tools")
    p.add_argument("--registro", help="append each call (and each --respuesta) to this file, one JSON per line")
    p.add_argument("--respuesta", type=int, metavar="N", help="record the final answer to question N")
    args = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    if args.respuesta is not None:
        if not args.registro or args.herramienta is None:
            p.error("--respuesta N necesita --registro y el texto (o «-» y el texto por stdin)")
        text = stdin_text() if args.herramienta == "-" else " ".join(filter(None, [args.herramienta, args.argumentos]))
        log(args.registro, {"respuesta_a": args.respuesta, "texto": text})
        print(f"anotada la respuesta a la pregunta {args.respuesta}")
        return
    if not args.herramientas:
        if not args.herramienta:
            p.error("falta la herramienta (o --herramientas para verlas)")
        raw = stdin_text() if args.argumentos == "-" else args.argumentos
        try:
            args.argumentos = json.loads(raw) if raw else {}
        except json.JSONDecodeError as e:
            msg = f"ERROR: los argumentos no son JSON válido ({e})"
            log(args.registro, {"herramienta": args.herramienta, "argumentos": raw, "respuesta": msg})
            print(msg)
            sys.exit(2)
    print(asyncio.run(run(args)))


if __name__ == "__main__":
    main()
