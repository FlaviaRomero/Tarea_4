"""Limpia la ENAHO del INEI: une sumaria (módulo 34) y miembros (módulo 02) en una base de personas.

    uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024

Entra:  datos/966-Modulo34.zip y datos/966-Modulo02.zip (o los .dta ya descomprimidos en datos/)
Sale:   salidas/personas_2024.parquet, salidas/indicadores.csv y salidas/validacion.txt

Si falla una validación esencial, escribe validacion.txt igual y termina con código de error 1.
Nunca ajusta los resultados para que coincidan con las referencias.
"""
import argparse
import io
import sys
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd

RAIZ = Path.cwd()
DATOS = RAIZ / "datos"
SALIDAS = RAIZ / "salidas"

CODIGO_INEI = {2024: "966"}          # código de la ENAHO de cada año en el portal de microdatos del INEI
LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
LLAVES_PERSONA = LLAVES_HOGAR + ["codperso"]
ANCHOS = {"conglome": 6, "vivienda": 3, "hogar": 2, "codperso": 2, "ubigeo": 6}

# Referencias oficiales 2024 (INEI). Solo se usan para COMPARAR, nunca para corregir.
REF = {"pobreza_nacional": 27.6, "pobreza_urbana": 24.8, "pobreza_rural": 39.3,
       "residentes": 108_664, "hogares": 33_691, "departamentos": 25}
TOLERANCIA_PP = 0.1                   # puntos porcentuales


def _sin_tildes(s):
    return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode()


def _normalizar_columnas(df):
    """Minúsculas y sin tildes: 'aÑo' -> 'ano', 'CONGLOME' -> 'conglome'."""
    df.columns = [_sin_tildes(c).lower().strip() for c in df.columns]
    return df


def _elegir_dta(nombres, modulo):
    """Dentro del zip del INEI elige el .dta correcto del módulo."""
    dtas = [n for n in nombres if n.lower().endswith(".dta")]
    if modulo == "34":
        cand = [n for n in dtas if "sumaria" in n.lower() and "12g" not in n.lower()]
    else:
        cand = [n for n in dtas if "200" in Path(n).name]
    cand = cand or dtas
    if not cand:
        raise FileNotFoundError(f"No hay archivos .dta del módulo {modulo}")
    return sorted(cand, key=len)[0]


def leer_modulo(codigo, modulo):
    """Lee el .dta del módulo desde el zip o desde datos/, sin convertir categorías y con llaves como texto."""
    zip_path = DATOS / f"{codigo}-Modulo{modulo}.zip"
    if zip_path.exists():
        with zipfile.ZipFile(zip_path) as z:
            nombre = _elegir_dta(z.namelist(), modulo)
            df = pd.read_stata(io.BytesIO(z.read(nombre)), convert_categoricals=False)
        origen = f"{zip_path.name}:{nombre}"
    else:
        sueltos = [str(p) for p in DATOS.rglob("*.dta")]
        if not sueltos:
            sys.exit(f"ERROR: falta {zip_path}. Bájenlo de "
                     f"https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/{codigo}-Modulo{modulo}.zip")
        nombre = _elegir_dta(sueltos, modulo)
        df = pd.read_stata(nombre, convert_categoricals=False)
        origen = nombre
    df = _normalizar_columnas(df)
    for c, ancho in ANCHOS.items():      # las llaves como texto, sin perder los ceros iniciales
        if c in df.columns:
            if pd.api.types.is_numeric_dtype(df[c]):
                df[c] = df[c].astype("Int64").astype(str).str.zfill(ancho)
            else:
                df[c] = df[c].astype(str).str.strip()
    return df, origen


def pct(pobre, peso):
    """Porcentaje ponderado."""
    return float((pobre * peso).sum() / peso.sum() * 100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anio", type=int, default=2024)
    anio = ap.parse_args().anio
    codigo = CODIGO_INEI.get(anio)
    if codigo is None:
        sys.exit(f"ERROR: no conozco el código INEI de la ENAHO {anio}. Agréguenlo a CODIGO_INEI.")
    SALIDAS.mkdir(exist_ok=True)

    # 1-2. Leer y normalizar
    sumaria, origen34 = leer_modulo(codigo, "34")
    miembros, origen02 = leer_modulo(codigo, "02")
    filas_02 = len(miembros)

    # 3. Residentes habituales
    res = (((miembros.p204 == 1) & (miembros.p205 == 2)) | ((miembros.p204 == 2) & (miembros.p206 == 1)))
    personas = miembros[res].copy()

    # 4. Unir personas con hogares (muchas personas -> un hogar)
    cols_hogar = LLAVES_HOGAR + ["ubigeo", "dominio", "estrato", "pobreza", "factor07", "mieperho"]
    cols_hogar = [c for c in cols_hogar if c in sumaria.columns]
    personas = personas.drop(columns=[c for c in cols_hogar if c not in LLAVES_HOGAR and c in personas.columns])
    antes = len(personas)
    base = personas.merge(sumaria[cols_hogar], on=LLAVES_HOGAR, how="left", validate="m:1", indicator=True)
    sin_hogar = int((base["_merge"] != "both").sum())
    base = base.drop(columns="_merge")

    # 5. Indicadores
    base["departamento"] = base.ubigeo.str[:2]
    base["urbano"] = base.estrato <= 5
    base["area"] = base.urbano.map({True: "Urbana", False: "Rural"})
    base["pobre"] = (base.pobreza <= 2).astype(int)
    base["pobre_extremo"] = (base.pobreza == 1).astype(int)
    if "p207" in base.columns:
        base["sexo"] = base.p207.map({1: "Hombre", 2: "Mujer"})
    if "p208a" in base.columns:
        base["grupo_edad"] = pd.cut(base.p208a, [-1, 13, 17, 29, 59, 200],
                                    labels=["0-13", "14-17", "18-29", "30-59", "60 y más"]).astype(str)

    # 6. Factores de expansión: personas con facpob07; hogares con factor07 × mieperho
    peso = base.facpob07
    nacional = pct(base.pobre, peso)
    sum_ok = sumaria.dropna(subset=["pobreza", "factor07", "mieperho"])
    nacional_sumaria = pct((sum_ok.pobreza <= 2).astype(int), sum_ok.factor07 * sum_ok.mieperho)
    urbana = pct(base.pobre[base.urbano], peso[base.urbano])
    rural = pct(base.pobre[~base.urbano], peso[~base.urbano])
    extrema = pct(base.pobre_extremo, peso)
    simple = float(base.pobre.mean() * 100)

    # 7. Validaciones (esenciales: si fallan, se detiene)
    chequeos = []

    def chequear(nombre, ok, detalle, esencial=True):
        chequeos.append((nombre, bool(ok), detalle, esencial))

    chequear("Llaves de hogar únicas en sumaria", not sumaria.duplicated(LLAVES_HOGAR).any(),
             f"{len(sumaria):,} hogares (referencia {REF['hogares']:,})")
    chequear("Llaves de persona únicas en miembros", not miembros.duplicated(LLAVES_PERSONA).any(),
             f"{filas_02:,} filas en el módulo 02")
    chequear("Residentes habituales", len(personas) == REF["residentes"],
             f"{len(personas):,} (referencia {REF['residentes']:,})")
    chequear("La unión no duplica filas", len(base) == antes, f"{antes:,} antes y {len(base):,} después")
    chequear("Toda persona tiene hogar en la sumaria", sin_hogar == 0, f"{sin_hogar} personas sin hogar")
    chequear("Factor de expansión facpob07 completo y positivo",
             peso.notna().all() and (peso > 0).all(), f"{int(peso.isna().sum())} faltantes")
    deps = sorted(base.departamento.dropna().unique())
    chequear("25 códigos territoriales", len(deps) == REF["departamentos"] and deps == [f"{i:02d}" for i in range(1, 26)],
             f"{len(deps)} códigos: {deps[0]}–{deps[-1]}")
    chequear("Pobreza nacional ponderada (personas, facpob07)",
             abs(nacional - REF["pobreza_nacional"]) <= TOLERANCIA_PP,
             f"{nacional:.2f} % (referencia {REF['pobreza_nacional']} %, tolerancia ±{TOLERANCIA_PP} pp)")
    chequear("Pobreza nacional ponderada (hogares, factor07 × mieperho)",
             abs(nacional_sumaria - REF["pobreza_nacional"]) <= TOLERANCIA_PP, f"{nacional_sumaria:.2f} %")
    chequear("Pobreza urbana (estrato <= 5)", abs(urbana - REF["pobreza_urbana"]) <= 0.15,
             f"{urbana:.2f} % (referencia {REF['pobreza_urbana']} %)", esencial=False)
    chequear("Pobreza rural (estrato >= 6)", abs(rural - REF["pobreza_rural"]) <= 0.15,
             f"{rural:.2f} % (referencia {REF['pobreza_rural']} %)", esencial=False)

    lineas = [f"VALIDACIÓN ENAHO {anio} (código INEI {codigo})", "",
              f"Módulo 34: {origen34}", f"Módulo 02: {origen02}", ""]
    for nombre, ok, detalle, esencial in chequeos:
        marca = "APROBADA" if ok else ("FALLÓ" if esencial else "FALLÓ (no esencial)")
        lineas.append(f"[{marca:^19}] {nombre}: {detalle}")
    lineas += ["", "Otras cifras (informativas):",
               f"  Pobreza extrema ponderada: {extrema:.2f} %",
               f"  Pobreza SIN ponderar (promedio simple, NO usar): {simple:.2f} %",
               f"  Población expandida: {peso.sum():,.0f} personas"]
    fallas = [n for n, ok, _, esencial in chequeos if esencial and not ok]
    lineas += ["", "RESULTADO: " + ("TODAS LAS VALIDACIONES ESENCIALES APROBADAS" if not fallas
                                    else "FALLÓ: " + "; ".join(fallas))]
    texto = "\n".join(lineas)
    (SALIDAS / "validacion.txt").write_text(texto, encoding="utf-8")
    print(texto)
    if fallas:
        sys.exit(1)

    # Guardar la base y los indicadores ponderados
    columnas = LLAVES_PERSONA + ["ubigeo", "departamento", "dominio", "estrato", "urbano", "area", "sexo",
                                 "p208a", "grupo_edad", "pobreza", "pobre", "pobre_extremo", "facpob07",
                                 "factor07", "mieperho"]
    base[[c for c in columnas if c in base.columns]].to_parquet(SALIDAS / f"personas_{anio}.parquet", index=False)

    filas = [{"nivel": "Nacional", "grupo": "Perú", "pobreza_pct": nacional}]
    for col, nivel in [("area", "Área"), ("sexo", "Sexo"), ("grupo_edad", "Edad"), ("departamento", "Departamento")]:
        if col in base.columns:
            for g, d in base.groupby(col):
                filas.append({"nivel": nivel, "grupo": g, "pobreza_pct": pct(d.pobre, d.facpob07)})
    ind = pd.DataFrame(filas)
    ind["pobreza_pct"] = ind.pobreza_pct.round(2)
    ind["fuente"] = f"INEI, ENAHO {anio}; ponderado con facpob07"
    ind.to_csv(SALIDAS / "indicadores.csv", index=False, encoding="utf-8")
    print(f"\nGuardé salidas/personas_{anio}.parquet ({len(base):,} personas) y salidas/indicadores.csv")


if __name__ == "__main__":
    main()
