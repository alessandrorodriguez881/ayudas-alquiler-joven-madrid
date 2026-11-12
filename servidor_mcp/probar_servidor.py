#!/usr/bin/env python3
"""Starts servidor.py as an AI client would (stdio), connects with the official MCP client and calls every tool with
answers known from the database and the rules (as the training's probar_servidor.py, with checks).
Run:  python servidor_mcp/probar_servidor.py   (needs: pip install mcp)"""
import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

SERVER = Path(__file__).with_name("servidor.py")
TOOLS = {"buscar_municipio", "ficha_municipio", "puedo_pedirla", "reglas", "diccionario", "consulta_sql"}


def attr(obj, *names):
    """Attribute in mcp 1.x (camelCase) or 2.x (snake_case)."""
    for n in names:
        if hasattr(obj, n):
            return getattr(obj, n)
    return None


def content(result):
    data = attr(result, "structured_content", "structuredContent")
    if data is None:
        texts = [c.text for c in result.content if getattr(c, "text", None)]
        data = json.loads(texts[0]) if len(texts) == 1 else texts
    return data["result"] if isinstance(data, dict) and set(data) == {"result"} else data


def ok(what):
    print("ok", what)  # plain text: some Windows consoles are cp1252


async def main():
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            info = await session.initialize()
            assert attr(info, "server_info", "serverInfo").name == "bono-alquiler-joven"
            names = {t.name for t in (await session.list_tools()).tools}
            assert names == TOOLS, names
            ok(f"servidor conectado, {len(names)} herramientas")

            call = lambda tool, **args: session.call_tool(tool, args)  # noqa: E731
            found = content(await call("buscar_municipio", texto="parla"))
            assert [m["ine"] for m in found] == ["106"], found
            ok("buscar_municipio: parla -> 106")
            found = content(await call("buscar_municipio", texto="las rozas"))
            assert [m["municipio"] for m in found] == ["Rozas de Madrid (Las)"], found
            ok("buscar_municipio: las rozas -> Las Rozas de Madrid (y no Rozas de Puerto Real)")

            card = content(await call("ficha_municipio", municipio="Parla"))
            caps = {c["regla"]: c["tope_piso"] for c in card["topes"]}
            assert caps == {"bono_2022": 900, "bono_2024": 900, "plan_2026_2030": 1000, "propuesta": 1000}, caps
            assert card["fuentes"] and all(f["url"] for f in card["fuentes"])
            ok(f"ficha_municipio: Parla, {card['jovenes_20_34_2024']} jóvenes, topes {caps}, {len(card['fuentes'])} fuentes")

            res = content(await call("puedo_pedirla", municipio="Parla", edad=27, precio=750, ingresos=18000))
            assert [(res[k]["cumple"], res[k]["ayuda_al_mes"]) for k in ("hoy", "plan", "propuesta")] == \
                [(True, 250), (True, 300), (True, 300)], res
            ok("puedo_pedirla: piso de 750 euros en Parla -> 250 hoy, 300 con el Plan")
            res = content(await call("puedo_pedirla", municipio="Parla", edad=24, precio=800, ingresos=10000,
                                     con_quien="otros", ingresos_otros=20000))
            assert (res["hoy"]["cumple"], res["plan"]["cumple"]) == (False, True), res
            ok("puedo_pedirla: con su familia (30.000 euros entre todos) -> no hoy, sí con el Plan")
            bad = await call("puedo_pedirla", municipio="Parla", edad=27, precio=750, ingresos=18000, exclusiones=["x"])
            assert attr(bad, "is_error", "isError")
            ok("puedo_pedirla: una exclusión que no existe da error")

            assert len(content(await call("reglas"))) == 8
            assert {c["columna"] for c in content(await call("diccionario", tabla="topes"))} == \
                {"ine", "regla", "tope_piso", "tope_habitacion"}
            ok("reglas (8) y diccionario de topes")

            n = content(await call("consulta_sql", sql="SELECT COUNT(*) AS n FROM municipios"))
            assert n["filas"] == [[179]], n
            for sql in ("DELETE FROM municipios", "WITH x AS (SELECT 1) DELETE FROM municipios",
                        "SELECT 1; DROP TABLE municipios"):
                assert attr(await call("consulta_sql", sql=sql), "is_error", "isError"), sql
            ok("consulta_sql: lee (179 municipios) y no deja escribir")

            # expected errors reach the AI with their text, so it can correct the call
            why = lambda r: " ".join(c.text for c in r.content if getattr(c, "text", None))  # noqa: E731
            r = await call("ficha_municipio", municipio="rozas")
            assert attr(r, "is_error", "isError") and "Rozas de Puerto Real" in why(r), why(r)
            r = await call("consulta_sql", sql="DELETE FROM municipios")
            assert "Solo se admite" in why(r), why(r)
            ok("los errores esperados llegan con su explicación (nombre ambiguo, escritura)")
            r = await call("consulta_sql", sql="WITH RECURSIVE x(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM x) "
                                               "SELECT COUNT(*) FROM x")
            assert attr(r, "is_error", "isError") and "se ha parado" in why(r), why(r)
            ok("consulta_sql: una consulta que no acaba se para a los 5 s")
            for args, word in (({"con_quien": "jovenes", "jovenes_que_firman": 0}, "jovenes_que_firman"),
                               ({"precio": -1}, "precio")):
                r = await call("puedo_pedirla", **{"municipio": "Parla", "edad": 27, "precio": 750, "ingresos": 18000,
                                                   **args})
                assert attr(r, "is_error", "isError") and word in why(r), why(r)
            ok("puedo_pedirla: 0 jóvenes que firman o un precio negativo dan un error explicado")


if __name__ == "__main__":
    asyncio.run(main())
