"""Evaluación de la Tarea 4: las mismas 10 preguntas sin y con el MCP del BCRP y las Skills de ENAHO.

    uv run python evaluacion/evaluar.py                 # los dos modos, con Haiku
    uv run python evaluacion/evaluar.py --modelo sonnet --paralelo 2

Cada pregunta se hace en una sesión nueva e independiente de Claude Code (claude -p --no-session-persistence).
Las respuestas esperadas están fijadas en evaluacion/preguntas.csv ANTES de correr; no se cambian después.

Modo A, "sin": sin MCP, sin Skills y sin herramientas (no puede leer archivos, usar la terminal ni la web).
               Así no puede acceder indirectamente a las cifras ya calculadas en salidas/.
Modo B, "con": el MCP bcrp de .mcp.json, las Skills de .claude/skills y Bash/Read/Glob/Grep para correrlas.
Escribe evaluacion/resultados.csv y evaluacion/resumen_metricas.md.
"""
import argparse
import json
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
EVAL = RAIZ / "evaluacion"
ESQUEMA = {"type": "object", "required": ["valores", "fuente"],
           "properties": {"valores": {"type": "array", "items": {"type": ["number", "null"]}},
                          "fuente": {"type": "string"}, "interpretacion": {"type": "string"}}}
INSTRUCCION = ("Responde en «valores» con la lista de números que pide la pregunta, en la unidad pedida y en el orden "
               "pedido (un solo número si pide uno). Si no puedes saber un valor con certeza, pon null: no estimes. "
               "En «fuente» di de dónde sale cada cifra (código de serie, archivo o tabla). Si la pregunta pide "
               "interpretar, hazlo en «interpretacion».\n\n")
MODOS = {
    "sin": {"args": ["--tools", "", "--strict-mcp-config", "--disable-slash-commands"],
            "habilitado": "Ninguna herramienta: sin MCP, sin Skills, sin archivos, terminal ni web. Solo el conocimiento del modelo."},
    "con": {"args": ["--tools", "Bash,Read,Glob,Grep,Skill", "--strict-mcp-config", "--mcp-config", str(RAIZ / ".mcp.json"),
                     "--allowedTools", "mcp__bcrp,Skill,Bash,Read,Glob,Grep"],
            "habilitado": "MCP bcrp (.mcp.json), Skills del proyecto y de la cuenta, Bash, Read, Glob y Grep. Sin web."},
}


def preguntar(pregunta, modo, modelo):
    cmd = [shutil.which("claude") or "claude", "-p", INSTRUCCION + pregunta, "--output-format", "stream-json",
           "--verbose", "--json-schema", json.dumps(ESQUEMA), "--no-session-persistence", "--model", modelo,
           *MODOS[modo]["args"]]
    t = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=900, cwd=RAIZ)
        salida, error = proc.stdout, (proc.stderr or "")[-300:]
    except subprocess.TimeoutExpired:
        salida, error = "", "tiempo agotado (900 s)"
    herramientas, final = [], {}
    for linea in salida.splitlines():
        try:
            m = json.loads(linea)
        except json.JSONDecodeError:
            continue
        if m.get("type") == "assistant":
            for b in m.get("message", {}).get("content", []):
                if b.get("type") == "tool_use":
                    n = b.get("name", "")
                    if n == "Skill":
                        n += ":" + str(b.get("input", {}).get("skill", b.get("input", {}).get("command", "")))
                    herramientas.append(n)
        elif m.get("type") == "result":
            final = m
    r = final.get("structured_output") or {}
    if not r and final.get("result"):
        try:
            r = json.loads(final["result"])
        except (json.JSONDecodeError, TypeError):
            r = {}
    if final.get("is_error"):
        error = (error + " " + str(final.get("result", "")))[-300:]
    return {"valores": r.get("valores") or [], "fuente": r.get("fuente", ""), "interpretacion": r.get("interpretacion", ""),
            "herramientas": ", ".join(dict.fromkeys(herramientas)) or "ninguna",
            "segundos": round(time.time() - t, 1), "error": error.strip() if not r else ""}


def calificar(valores, esperado, tolerancia):
    esp = [float(x) for x in str(esperado).split(";")]
    tol = [float(x) for x in str(tolerancia).split(";")]
    vals = list(valores) + [None] * (len(esp) - len(valores))
    if all(v is None for v in vals[:len(esp)]):
        return "sin respuesta"
    ok = all(v is not None and abs(float(v) - e) <= t for v, e, t in zip(vals, esp, tol))
    return "correcta" if ok else "incorrecta"


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--modos", nargs="+", default=["sin", "con"], choices=list(MODOS))
    p.add_argument("--modelo", default="haiku")
    p.add_argument("--paralelo", type=int, default=2)
    a = p.parse_args()
    if not (RAIZ / "salidas" / "personas_2024.parquet").exists():
        raise SystemExit("Falta salidas/personas_2024.parquet: corran primero la skill limpiando-enaho.")

    preguntas = pd.read_csv(EVAL / "preguntas.csv", dtype={"esperado": str, "tolerancia": str})
    casos = [(q, m) for q in preguntas.itertuples() for m in a.modos]
    print(f"{len(casos)} sesiones independientes de claude -p con {a.modelo}; puede tardar varios minutos...")
    with ThreadPoolExecutor(a.paralelo) as ex:
        respuestas = list(ex.map(lambda c: preguntar(c[0].pregunta, c[1], a.modelo), casos))

    filas = []
    for (q, m), r in zip(casos, respuestas):
        filas.append({"id": q.id, "tipo": q.tipo, "modo": m, "pregunta": q.pregunta, "esperado": q.esperado,
                      "tolerancia": q.tolerancia, "respuesta": ";".join("null" if v is None else str(v) for v in r["valores"]),
                      "resultado": calificar(r["valores"], q.esperado, q.tolerancia), "fuente_respuesta": r["fuente"],
                      "interpretacion": r["interpretacion"], "herramientas_usadas": r["herramientas"],
                      "segundos": r["segundos"], "error": r["error"]})
    res = pd.DataFrame(filas)
    res.to_csv(EVAL / "resultados.csv", index=False, encoding="utf-8")

    tabla = res.groupby("modo").resultado.value_counts().unstack(fill_value=0)
    tabla["segundos_promedio"] = res.groupby("modo").segundos.mean().round(1)
    por_tipo = res[res.resultado == "correcta"].groupby(["modo", "tipo"]).size().unstack(fill_value=0)
    cruce = res.pivot(index="id", columns="modo", values="resultado")
    texto = (f"# Métricas de la evaluación ({a.modelo})\n\n## Por modo\n\n{tabla.to_markdown()}\n\n"
             f"## Correctas por tipo de pregunta\n\n{por_tipo.to_markdown()}\n\n## Pregunta por pregunta\n\n{cruce.to_markdown()}\n\n"
             "## Herramientas habilitadas\n\n" + "\n".join(f"- **{m}**: {MODOS[m]['habilitado']}" for m in a.modos) + "\n")
    (EVAL / "resumen_metricas.md").write_text(texto, encoding="utf-8")
    print("\n" + texto)
