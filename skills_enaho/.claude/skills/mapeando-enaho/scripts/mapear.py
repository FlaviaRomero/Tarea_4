"""Mapa coroplético de la pobreza monetaria por departamento con la ENAHO limpia.

    uv run python .claude/skills/mapeando-enaho/scripts/mapear.py

Entra salidas/personas_2024.parquet y el GeoJSON departamental del curso (se baja a datos/ si falta).
Sale mapas/pobreza_departamento.png y salidas/comparacion_mapa.csv (contra la referencia de la Sesión 16).
Une por código (ubigeo[:2] con FIRST_IDDP), nunca por nombre. Lima (15) y Callao (07) van separados.
"""
import argparse
import sys
from pathlib import Path

import geopandas as gpd
import httpx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path.cwd()
AQUI = Path(__file__).resolve().parent
GEOJSON = RAIZ / "datos" / "peru_departamental_simple.geojson"
URL_GEOJSON = ("https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/"
               "sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson")
REFERENCIA = AQUI.parent / "referencias" / "pobreza_departamento_2024.csv"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anio", type=int, default=2024)
    anio = ap.parse_args().anio
    base = RAIZ / "salidas" / f"personas_{anio}.parquet"
    if not base.exists():
        sys.exit(f"ERROR: no existe {base.relative_to(RAIZ)}. Corran primero la skill limpiando-enaho.")
    if not GEOJSON.exists():
        GEOJSON.parent.mkdir(exist_ok=True)
        r = httpx.get(URL_GEOJSON, timeout=60, follow_redirects=True)
        r.raise_for_status()
        GEOJSON.write_bytes(r.content)

    df = pd.read_parquet(base)
    pob = (df.groupby("departamento")
             .apply(lambda d: (d.pobre * d.facpob07).sum() / d.facpob07.sum() * 100, include_groups=False)
             .rename("pobreza_pct").reset_index())

    geo = gpd.read_file(GEOJSON)
    geo["FIRST_IDDP"] = geo.FIRST_IDDP.astype(str).str.zfill(2)
    mapa = geo.merge(pob, left_on="FIRST_IDDP", right_on="departamento", how="left", validate="1:1")

    # Validaciones del mapa
    faltan = mapa[mapa.pobreza_pct.isna()].NOMBDEP.tolist()
    if len(mapa) != 25 or faltan:
        sys.exit(f"ERROR: el mapa debe tener 25 departamentos con dato; hay {len(mapa)} y sin dato: {faltan}")
    if not {"07", "15"} <= set(mapa.FIRST_IDDP):
        sys.exit("ERROR: Lima (15) y Callao (07) deben ir separados.")

    # Comparación con la referencia de la Sesión 16
    ref = pd.read_csv(REFERENCIA, dtype={"ccdd": str}).rename(
        columns={"departamento": "nombre", "pobreza_pct": "referencia_pct"})
    calc = pob.rename(columns={"departamento": "ccdd", "pobreza_pct": "calculado_pct"})
    comp = ref.merge(calc, on="ccdd", how="outer", validate="1:1")
    comp["calculado_pct"] = comp.calculado_pct.round(1)
    comp["diferencia_pp"] = (comp.calculado_pct - comp.referencia_pct).round(1)
    (RAIZ / "salidas").mkdir(exist_ok=True)
    comp.to_csv(RAIZ / "salidas" / "comparacion_mapa.csv", index=False, encoding="utf-8")
    max_dif = comp.diferencia_pp.abs().max()

    # Mapa: un solo tono de claro a oscuro, desde 0
    fig, ax = plt.subplots(figsize=(7, 9))
    mapa.plot(column="pobreza_pct", cmap="Reds", vmin=0, vmax=max(50, mapa.pobreza_pct.max()),
              edgecolor="white", linewidth=0.5, ax=ax, legend=True,
              legend_kwds={"label": "% de personas en pobreza monetaria", "shrink": 0.6})
    puntos = mapa.copy()
    puntos["geometry"] = mapa.representative_point()
    for _, f in puntos.iterrows():
        ax.annotate(f"{f.pobreza_pct:.0f}", (f.geometry.x, f.geometry.y), ha="center", va="center", fontsize=7,
                    color="white" if f.pobreza_pct > 30 else "#222")
    alto, bajo = mapa.loc[mapa.pobreza_pct.idxmax()], mapa.loc[mapa.pobreza_pct.idxmin()]
    ax.set_title(f"Pobreza monetaria por departamento, Perú {anio}\n"
                 f"Va de {bajo.pobreza_pct:.1f} % en {bajo.NOMBDEP.title()} a {alto.pobreza_pct:.1f} % en "
                 f"{alto.NOMBDEP.title()}", loc="left", fontsize=11)
    ax.set_axis_off()
    fig.text(0.02, 0.02, f"Fuente: INEI, ENAHO {anio}. Estimaciones ponderadas con facpob07; "
             "Lima y Callao por separado.", fontsize=8, color="#555")
    (RAIZ / "mapas").mkdir(exist_ok=True)
    ruta = RAIZ / "mapas" / "pobreza_departamento.png"
    fig.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"Guardé {ruta.relative_to(RAIZ)}: 25 departamentos con dato, unidos por FIRST_IDDP.")
    print(f"Diferencia máxima con la referencia de la Sesión 16: {max_dif:.1f} pp (detalle en salidas/comparacion_mapa.csv)")
    print(comp.to_string(index=False))


if __name__ == "__main__":
    main()
