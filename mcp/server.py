"""Servidor MCP del BCRP: busca, descarga y resume series oficiales del Banco Central de Reserva del Perú.

    uv run pytest -q mcp/                                       # las pruebas
    uv run mcp/server.py                                        # el servidor, por stdio
    claude mcp add --scope project bcrp -- uv run mcp/server.py # conectarlo a Claude Code

Las cuentas las hace Python, no el modelo: así cada cifra sale de una llamada que se puede repetir.
"""
import re
import time
import unicodedata
from functools import cache
from pathlib import Path

import httpx
import pandas as pd
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

AQUI = Path(__file__).parent
CATALOGO = AQUI.parent / "datos" / "catalogo_bcrp.csv"     # datos/ en la raíz de la tarea
URL_CATALOGO = "https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata"
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
SOLO_LECTURA = {"readOnlyHint": True, "openWorldHint": True}

mcp = FastMCP("bcrp", instructions=(
    "Series oficiales del Banco Central de Reserva del Perú (BCRP). Primero busca el código con buscar_series; "
    "luego usa resumen para variaciones, promedios y extremos, y serie para los datos. No calcules a mano: "
    "cita siempre el código de la serie y el periodo."))


def _sin_tildes(s):
    return unicodedata.normalize("NFD", str(s).lower()).encode("ascii", "ignore").decode()


@cache
def catalogo():
    """El catálogo oficial: 17 mil series en unos 7 MB. Se baja una vez y queda en datos/."""
    if not CATALOGO.exists():
        CATALOGO.parent.mkdir(exist_ok=True)
        r = httpx.get(URL_CATALOGO, timeout=120)
        r.raise_for_status()
        CATALOGO.write_text(r.content.decode("latin-1"), encoding="utf-8")
    df = pd.read_csv(CATALOGO, sep=";", dtype=str).fillna("")
    df = df.rename(columns={"Código de serie": "codigo", "Categoría de serie": "categoria", "Grupo de serie": "grupo",
                            "Nombre de serie": "nombre", "Frecuencia": "frecuencia",
                            "Fecha de actualización": "actualizada", "Fecha de inicio": "inicio"})
    df["texto"] = (df.categoria + " " + df.grupo + " " + df.nombre).map(_sin_tildes)
    return df


def _ficha(codigo):
    fila = catalogo().query("codigo == @codigo")
    if fila.empty:
        raise ToolError(f"No existe el código de serie {codigo!r}. Búsquenlo con buscar_series.")
    f = fila.iloc[0]
    return {"codigo": f.codigo, "nombre": f"{f.grupo} - {f.nombre}", "categoria": f.categoria,
            "frecuencia": f.frecuencia, "inicio": f.inicio, "actualizada": f.actualizada}


@mcp.tool(annotations=SOLO_LECTURA)
def buscar_series(texto: str, frecuencia: str | None = None, limite: int = 10) -> list[dict]:
    """Busca series del BCRP por palabras: todas deben aparecer en la categoría, el grupo o el nombre.

    Ejemplos: "ipc 12 meses", "tipo de cambio interbancario venta", "reservas internacionales netas",
    "tasa de referencia", "cobre precio". frecuencia: "Diaria", "Mensual", "Trimestral" o "Anual".
    Devuelve el código, el nombre completo, la frecuencia y desde cuándo hay datos. Si no hay resultados,
    prueben con menos palabras.
    """
    df = catalogo()
    m = pd.Series(True, index=df.index)
    for palabra in _sin_tildes(texto).split():
        m &= df.texto.str.contains(re.escape(palabra))
    if frecuencia:
        m &= df.frecuencia.str.lower() == frecuencia.lower()
    sel = df[m]
    orden = sel.assign(vieja=sel.actualizada < "2025", largo=(sel.grupo + sel.nombre).str.len())
    return [_ficha(c) for c in orden.sort_values(["vieja", "largo"]).head(limite).codigo]


# ---------- TODO 1 · serie ----------
MESES = {"Ene": 1, "Feb": 2, "Mar": 3, "Abr": 4, "May": 5, "Jun": 6, "Jul": 7,
         "Ago": 8, "Sep": 9, "Set": 9, "Oct": 10, "Nov": 11, "Dic": 12}


def _fecha_api(fecha, frecuencia):
    """Convierte nuestra fecha al formato que pide la API: '2025-01' -> '2025-1'."""
    f = frecuencia.lower()
    if f == "diaria":
        return fecha
    if f == "anual":
        return fecha[:4]
    anio, resto = fecha.split("-")[:2]
    return f"{anio}-{int(resto.lstrip('T'))}"


def _periodo(nombre, frecuencia):
    """Convierte el periodo que responde la API a uno estándar: 'Ene.2025' -> '2025-01'."""
    f = frecuencia.lower()
    if f == "mensual":
        m, a = nombre.split(".")
        return f"{a}-{MESES[m[:3]]:02d}"
    if f == "diaria":
        d, m, a = nombre.split(".")
        return f"20{a}-{MESES[m[:3]]:02d}-{int(d):02d}"
    if f == "trimestral":
        t, a = nombre.split(".")
        return f"20{a}-{t}"
    return nombre


@cache
def _descargar(url):
    for intento in range(4):            # si hay muchos pedidos seguidos, la API responde HTML
        try:
            return httpx.get(url, timeout=60).json()
        except ValueError:
            time.sleep(2 * (intento + 1))
    raise ToolError("El BCRP no respondió con datos; reintenta en unos segundos.")


def _serie(codigo, desde, hasta):
    ficha = _ficha(codigo)              # si el código no existe, lanza ToolError con el código
    fr = ficha["frecuencia"]
    url = f"{API}/{codigo}/json/{_fecha_api(desde, fr)}/{_fecha_api(hasta, fr)}"
    datos = [{"periodo": _periodo(p["name"], fr), "valor": float(p["values"][0])}
             for p in _descargar(url).get("periods", []) if p["values"][0] != "n.d."]
    return {"codigo": codigo, "nombre": ficha["nombre"], "frecuencia": fr,
            "datos": datos, "fuente": url}


@mcp.tool(annotations=SOLO_LECTURA)
def serie(codigo: str, desde: str, hasta: str) -> dict:
    """Descarga los datos de una serie del BCRP entre dos fechas.

    Fechas: '2025-01' (mensual), '2025-01-15' (diaria), '2025-T1' (trimestral), '2025' (anual).
    Devuelve los periodos con su valor y la URL de la fuente. Primero obtén el código con buscar_series.
    """
    return _serie(codigo, desde, hasta)


# ---------- TODO 2 · resumen ----------
@mcp.tool(annotations=SOLO_LECTURA)
def resumen(codigo: str, desde: str, hasta: str) -> dict:
    """Primero, último, cambio, variación %, promedio, máximo y mínimo de una serie del BCRP.

    Úsala siempre en vez de calcular a mano. Mismo formato de fechas que la herramienta serie.
    """
    s = _serie(codigo, desde, hasta)
    d = s["datos"]
    if not d:
        raise ToolError(f"La serie {codigo} no tiene datos entre {desde} y {hasta}.")
    primero, ultimo = d[0], d[-1]
    cambio = ultimo["valor"] - primero["valor"]
    return {"codigo": codigo, "nombre": s["nombre"], "desde": desde, "hasta": hasta,
            "primero": primero, "ultimo": ultimo, "cambio": round(cambio, 4),
            "variacion_pct": round(cambio / primero["valor"] * 100, 2) if primero["valor"] else None,
            "promedio": round(sum(x["valor"] for x in d) / len(d), 4),
            "maximo": max(d, key=lambda x: x["valor"]),
            "minimo": min(d, key=lambda x: x["valor"]),
            "fuente": s["fuente"]}


# ---------- TODO 3 · herramienta propia ----------
@mcp.tool(annotations=SOLO_LECTURA)
def correlacion(codigo_a: str, codigo_b: str, desde: str, hasta: str) -> dict:
    """Correlación de Pearson entre dos series del BCRP de la misma frecuencia, usando solo los periodos comunes.

    Úsala para preguntas como '¿se mueven juntas la inflación y la tasa de referencia?'.
    Ejemplo: codigo_a='PN01273PM', codigo_b='PD04722MM', desde='2023-01', hasta='2026-09'.
    """
    a = pd.DataFrame(_serie(codigo_a, desde, hasta)["datos"], columns=["periodo", "valor"]).set_index("periodo")["valor"]
    b = pd.DataFrame(_serie(codigo_b, desde, hasta)["datos"], columns=["periodo", "valor"]).set_index("periodo")["valor"]
    comun = pd.concat([a, b], axis=1, join="inner").dropna()
    if len(comun) < 3:
        raise ToolError("Hay menos de 3 periodos en común; revisen que ambas series tengan la misma frecuencia.")
    return {"codigo_a": codigo_a, "codigo_b": codigo_b, "desde": desde, "hasta": hasta,
            "periodos": len(comun),
            "correlacion": round(float(comun.iloc[:, 0].corr(comun.iloc[:, 1])), 4),
            "fuente": [f"{API}/{codigo_a}", f"{API}/{codigo_b}"]}


# ---------- TODO 4 · recurso ----------
@mcp.resource("bcrp://serie/{codigo}")
def ficha_serie(codigo: str) -> dict:
    """Ficha descriptiva de una serie: nombre, categoría, frecuencia y desde cuándo hay datos."""
    return _ficha(codigo)


# ---------- TODO 5 · prompt ----------
@mcp.prompt
def informe(tema: str) -> str:
    """Plantilla para un informe breve sobre un indicador del BCRP."""
    return (f"Escribe un informe breve sobre {tema} en el Perú. Busca la serie con buscar_series, "
            "usa resumen para las cifras y no calcules a mano. Cita el código de serie, el periodo "
            "y la URL de la fuente de cada cifra.")


if __name__ == "__main__":
    mcp.run()
