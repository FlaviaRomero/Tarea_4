---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI y arma una base de personas con pobreza monetaria, departamento, área y factor de expansión, validada contra las cifras oficiales. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular la pobreza nacional, por departamento, área urbana/rural, sexo o edad. También la necesitan graficando-enaho y mapeando-enaho si falta la base limpia.
argument-hint: [año]
---
# Limpiar la ENAHO

Todo se corre desde la raíz del proyecto. El script hace la limpieza completa; no la reescribas a mano.

1. Revisa que existan `datos/966-Modulo34.zip` y `datos/966-Modulo02.zip` (966 = ENAHO 2024). Si faltan, pide al
   usuario bajarlos de `https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip` y
   `.../966-Modulo02.zip` y guardarlos en `datos/`. No inventes datos.
2. Corre exactamente:
   `uv run python "${CLAUDE_SKILL_DIR}/scripts/limpiar.py" --anio 2024`
   Por ahora el script solo conoce 2024; si piden otro año, avisa que falta su código INEI.
3. Lee `salidas/validacion.txt`.
   - Si el script terminó con error o dice `FALLÓ` en una validación esencial, **detente** y explica cuál falló.
     No cambies filtros, factores ni referencias para forzar que coincida.
   - Si todo está `APROBADA`, continúa.
4. Responde con las cifras de `salidas/indicadores.csv` o calcula otras desde `salidas/personas_2024.parquet`.
   Toda cifra de personas va ponderada con `facpob07`: `(pobre * facpob07).sum() / facpob07.sum() * 100`.
   Nunca uses promedios simples.
5. Cita siempre: «Fuente: INEI, ENAHO 2024; estimación ponderada».
6. Antes de usar una variable que no está en la base, lee `reference.md` de esta carpeta.

## Qué hace el script

| Paso | Regla |
|---|---|
| Leer | `pd.read_stata(..., convert_categoricals=False)`; llaves `conglome`, `vivienda`, `hogar`, `codperso`, `ubigeo` como texto con ceros iniciales |
| Normalizar | Columnas en minúscula y sin tildes (`aÑo` → `ano`) |
| Filtrar | Residentes habituales: `((p204 == 1) & (p205 == 2)) \| ((p204 == 2) & (p206 == 1))` |
| Unir | Personas con sumaria por `conglome`, `vivienda`, `hogar` con `merge(..., validate="m:1")` |
| Construir | `departamento = ubigeo[:2]`, `urbano = estrato <= 5`, `pobre = pobreza <= 2` |
| Validar | Llaves únicas, 108,664 residentes, sin duplicar ni perder filas, 25 departamentos, pobreza 27.6 % ± 0.1 |
| Guardar | `salidas/personas_2024.parquet`, `salidas/indicadores.csv`, `salidas/validacion.txt` |
