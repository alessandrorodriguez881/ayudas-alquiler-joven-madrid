#!/usr/bin/env python3
"""MCP server with the project's indicators by municipality (DataMad 2026), so an AI assistant can answer questions
about the Bono Alquiler Joven, its caps and the Plan Estatal 2026-2030 citing the source of every figure.

Built on the template of the DataMad training (github.com/albertoabellagarcia/DATAMAD2026, MCP/servidor.py), which
serves the portal's catalogue; this one serves our own indicators, already computed, from data/bono_alquiler_joven.sqlite
(read-only). Works with the official MCP SDK 1.x (FastMCP) and 2.x (MCPServer).

Tools:
  buscar_municipio(texto)          municipalities whose name contains the text
  ficha_municipio(municipio)       young people, need, rent 2024, caps of each rule and the share of rents above them,
                                   requests by programme and year, simulated bonos; with sources
  puedo_pedirla(...)               does a young person meet the requirements today, with the Plan and with the proposal,
                                   article by article (scripts/reglas_bono.py)
  reglas()                         each call or rule: norm, income limit, aid, months
  diccionario(tabla)               what every column of the database is
  consulta_sql(sql)                one SELECT on the read-only database (at most 500 rows)

Claude Desktop (claude_desktop_config.json; change the path):
  {"mcpServers": {"bono-alquiler-joven": {"command": "python", "args": ["C:/ruta/servidor_mcp/servidor.py"]}}}
Test without an AI client:  python servidor_mcp/probar_servidor.py
"""
import sqlite3
from contextlib import contextmanager
from typing import Literal

import consultas as q

try:  # mcp 2.x
    from mcp.server.mcpserver import MCPServer as Servidor
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as Servidor
    from mcp.server.fastmcp.exceptions import ToolError

mcp = Servidor("bono-alquiler-joven")


@contextmanager
def explained():
    """Expected errors (a name that matches several municipalities, a write in consulta_sql) reach the AI with their
    text, so it can correct the call; in mcp 2.x any other exception reaches it only as "Error executing tool"."""
    try:
        yield
    except (ValueError, sqlite3.Error) as e:
        raise ToolError(str(e)) from e


@mcp.tool()
def buscar_municipio(texto: str) -> list[dict]:
    """Busca municipios de la Comunidad de Madrid cuyo nombre contiene el texto (sin importar tildes ni artículos).
    Devuelve el código INE, el nombre oficial y la población de 2024."""
    with explained():
        return q.buscar_municipio(texto)


@mcp.tool()
def ficha_municipio(municipio: str) -> dict:
    """Indicadores de un municipio (nombre o código INE de 3 cifras): jóvenes de 20 a 34 años, índice de necesidad
    (0-100), alquiler mensual de 2024 (SERPAVI), el tope del alquiler con el Bono 2022, el Bono 2024 (hoy), el Plan
    Estatal 2026-2030 y la propuesta del proyecto, con la parte de los alquileres de 2024 que queda por encima de cada
    tope; solicitudes del Bono 2022 y de las Ayudas al alquiler de 2022 y 2023; las solicitudes del Bono 2022 que no se
    hicieron por el tope (estimación del modelo) y los bonos simulados con cada regla. Incluye las fuentes: cítalas."""
    with explained():
        return q.ficha_municipio(municipio)


@mcp.tool()
def puedo_pedirla(municipio: str, edad: int, precio: float, ingresos: float,
                  tipo: Literal["piso", "habitacion"] = "piso",
                  con_quien: Literal["solo", "jovenes", "otros"] = "solo",
                  jovenes_que_firman: int = 1, ingresos_otros: float = 0.0,
                  incluye: Literal["vivienda", "garaje", "trastero", "garaje_trastero"] = "vivienda",
                  gastos_sin_separar: bool = False, fuente_regular_de_ingresos: bool = True,
                  nacionalidad_o_residencia: bool = True, discapacidad: Literal["no", "33", "65"] = "no",
                  exclusiones: list[str] | None = None, otra_ayuda_al_alquiler: bool = False) -> dict:
    """¿Cumple un joven los requisitos de la ayuda al alquiler hoy (Bono Alquiler Joven 2024), con el Plan Estatal
    2026-2030 y con la propuesta del proyecto? Devuelve, para cada regla, si cumple, la ayuda al mes, el total y cada
    requisito con su artículo y la explicación.
    precio: euros al mes del contrato (si comparten piso y firman todos, el del piso entero). ingresos: euros al año del
    último año declarado. con_quien (solo si tipo es "piso"): "solo"; "jovenes" (otros de hasta 35 años que también
    firman y la piden; di cuántos son, contándole, en jovenes_que_firman); "otros" (familia u otras personas; sus
    ingresos al año en ingresos_otros). incluye: si el precio lleva garaje o trastero sin separar. discapacidad: "33"
    (33 % o más, o hijo o hija de víctima de violencia de género) o "65". exclusiones, de esta lista: vivienda_propia,
    vivienda_conviviente, familiar_casero, familiar_casero_conviviente, socio_casero, socio_casero_conviviente.
    Es orientativo: decide la Comunidad de Madrid."""
    with explained():
        unknown = set(exclusiones or ()) - set(q.rb.EXCLUSIONS)
        if unknown:
            raise ValueError(f"Exclusiones desconocidas: {sorted(unknown)}; valen: {sorted(q.rb.EXCLUSIONS)}")
        return q.puedo_pedirla(municipio, edad, precio, ingresos, tipo, con_quien, jovenes_que_firman, ingresos_otros,
                               incluye, gastos_sin_separar, fuente_regular_de_ingresos, nacionalidad_o_residencia,
                               discapacidad, tuple(exclusiones or ()), otra_ayuda_al_alquiler)


@mcp.tool()
def reglas() -> list[dict]:
    """Cada convocatoria o regla (Bono Alquiler Joven 2022 y 2024, Ayudas al alquiler para jóvenes 2022-2025, Plan
    Estatal 2026-2030 y la propuesta): norma, estado, cómo se fija el tope, límite de ingresos, ayuda máxima y meses."""
    return q.reglas()


@mcp.tool()
def diccionario(tabla: str = "") -> list[dict]:
    """Qué es cada columna de la base de datos (tipo, unidad, descripción y fuente). Tablas: municipios, reglas, topes,
    solicitudes, alquiler_serpavi, simulacion, fuentes, diccionario y metadatos; también la vista ficha_municipio.
    Sin tabla, todas."""
    with explained():
        return q.diccionario(tabla or None)


@mcp.tool()
def consulta_sql(sql: str) -> dict:
    """Una consulta SELECT (SQLite) sobre la base de datos del proyecto, solo de lectura, de hasta 500 filas. Mira antes
    diccionario() para conocer las tablas. La clave de municipio es «ine» (3 cifras)."""
    with explained():
        return q.consulta_sql(sql)


if __name__ == "__main__":
    mcp.run()
