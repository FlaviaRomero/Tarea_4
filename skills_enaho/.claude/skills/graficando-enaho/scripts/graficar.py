"""Gráficos de pobreza monetaria ponderada con la ENAHO limpia.

    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --por area
    uv run python .claude/skills/graficando-enaho/scripts/graficar.py --por todos

--por: area, sexo, edad, departamento o todos. Entra salidas/personas_2024.parquet; sale figuras/pobreza_<por>.png.
Toda cifra se pondera con facpob07.
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path.cwd()
FIGURAS = RAIZ / "figuras"
COLOR = "#2b6c8f"
NOMBRES = {"01": "Amazonas", "02": "Áncash", "03": "Apurímac", "04": "Arequipa", "05": "Ayacucho",
           "06": "Cajamarca", "07": "Callao", "08": "Cusco", "09": "Huancavelica", "10": "Huánuco",
           "11": "Ica", "12": "Junín", "13": "La Libertad", "14": "Lambayeque", "15": "Lima",
           "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua", "19": "Pasco", "20": "Piura",
           "21": "Puno", "22": "San Martín", "23": "Tacna", "24": "Tumbes", "25": "Ucayali"}
GRUPOS = {"area": ("area", "área de residencia"), "sexo": ("sexo", "sexo"),
          "edad": ("grupo_edad", "grupo de edad"), "departamento": ("departamento", "departamento")}


def ponderada(df, col):
    g = df.groupby(col).apply(lambda d: (d.pobre * d.facpob07).sum() / d.facpob07.sum() * 100,
                              include_groups=False)
    return g.rename("pobreza_pct")


def graficar(df, por, anio):
    col, etiqueta = GRUPOS[por]
    datos = ponderada(df, col)
    nacional = (df.pobre * df.facpob07).sum() / df.facpob07.sum() * 100
    if por == "departamento":
        datos.index = datos.index.map(NOMBRES)
    if por == "edad":
        datos = datos.reindex(["0-13", "14-17", "18-29", "30-59", "60 y más"])
    else:
        datos = datos.sort_values()

    alto = 8 if por == "departamento" else 3.6
    fig, ax = plt.subplots(figsize=(8, alto))
    barras = ax.barh(datos.index.astype(str), datos.values, color=COLOR)
    ax.bar_label(barras, labels=[f"{v:.1f} %" for v in datos.values], padding=3, fontsize=9)
    ax.axvline(nacional, color="#555", ls="--", lw=1)
    ax.text(nacional, len(datos) - 0.4, f" Perú: {nacional:.1f} %", color="#555", fontsize=9, va="bottom")
    ax.set_xlim(0, max(datos.max(), nacional) * 1.18)          # siempre desde cero
    ax.set_xlabel("% de personas en pobreza monetaria")
    brecha = datos.max() - datos.min()
    ax.set_title(f"Pobreza monetaria por {etiqueta}, Perú {anio}\n"
                 f"Brecha entre el mayor ({datos.idxmax()}) y el menor ({datos.idxmin()}): {brecha:.1f} pp",
                 loc="left", fontsize=11)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    fig.text(0.01, 0.01, f"Fuente: INEI, ENAHO {anio}. Residentes habituales; estimaciones ponderadas con facpob07.",
             fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    FIGURAS.mkdir(exist_ok=True)
    ruta = FIGURAS / f"pobreza_{por}.png"
    fig.savefig(ruta, dpi=200)
    plt.close(fig)
    print(f"Guardé {ruta.relative_to(RAIZ)}")
    print(datos.round(1).to_string())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--por", default="todos", choices=[*GRUPOS, "todos"])
    ap.add_argument("--anio", type=int, default=2024)
    a = ap.parse_args()
    base = RAIZ / "salidas" / f"personas_{a.anio}.parquet"
    if not base.exists():
        sys.exit(f"ERROR: no existe {base.relative_to(RAIZ)}. Corran primero la skill limpiando-enaho.")
    df = pd.read_parquet(base)
    for por in (GRUPOS if a.por == "todos" else [a.por]):
        graficar(df, por, a.anio)


if __name__ == "__main__":
    main()
