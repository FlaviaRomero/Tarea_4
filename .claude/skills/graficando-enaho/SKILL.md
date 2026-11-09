---
name: graficando-enaho
description: Hace gráficos de barras de la pobreza monetaria de la ENAHO 2024 del INEI, ponderados con factor de expansión, por área urbana/rural, sexo, grupo de edad o departamento. Úsala cuando pidan graficar, visualizar o comparar la pobreza en el Perú por algún grupo.
argument-hint: [area|sexo|edad|departamento|todos]
---
# Graficar la pobreza de la ENAHO

Todo se corre desde la raíz del proyecto.

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho` y espera a que sus
   validaciones salgan aprobadas.
2. Elige el grupo según el pedido: `area` (urbano/rural), `sexo`, `edad`, `departamento` o `todos`.
3. Corre exactamente:
   `uv run python "${CLAUDE_SKILL_DIR}/scripts/graficar.py" --por <grupo>`
4. Muestra la ruta del PNG en `figuras/` y las cifras que imprime el script. Interpreta la diferencia en puntos
   porcentuales (pp) entre grupos y frente al promedio nacional. No inventes causas que los datos no muestran.

## Reglas que el script ya cumple (no las cambies)

| Regla | Cómo |
|---|---|
| Ponderar siempre | `facpob07` |
| Barras desde cero, ordenadas | Eje x desde 0; ordenadas de menor a mayor (edad en su orden natural) |
| Un solo color y el valor en cada barra | Etiqueta con un decimal y `%` |
| Referencia | Línea punteada con el promedio nacional |
| Título analítico | Qué, dónde, cuándo y la brecha entre el mayor y el menor |
| Unidad y fuente | Eje «% de personas en pobreza monetaria»; nota «Fuente: INEI, ENAHO 2024» |
| Salida | PNG a 200 dpi en `figuras/pobreza_<grupo>.png` |
