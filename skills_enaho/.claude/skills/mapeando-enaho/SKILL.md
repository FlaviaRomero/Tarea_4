---
name: mapeando-enaho
description: Hace un mapa coroplético de la pobreza monetaria por departamento del Perú con la ENAHO 2024 del INEI, uniendo por código de ubigeo con el GeoJSON departamental y validando los 25 departamentos. Úsala cuando pidan un mapa de pobreza, una comparación territorial o regional en mapa, o la pobreza por departamento vista en el territorio.
---
# Mapear la pobreza de la ENAHO por departamento

Todo se corre desde la raíz del proyecto.

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho` y espera a que sus
   validaciones salgan aprobadas.
2. Corre exactamente:
   `uv run python "${CLAUDE_SKILL_DIR}/scripts/mapear.py"`
   El script baja `datos/peru_departamental_simple.geojson` del repositorio del curso si falta.
3. Si el script termina con `ERROR`, detente y explica el problema; no unas por nombres para arreglarlo.
4. Muestra `mapas/pobreza_departamento.png`, el departamento con mayor y menor pobreza, y la diferencia máxima con
   la referencia de la Sesión 16 (`salidas/comparacion_mapa.csv`). Si alguna diferencia supera 0.5 pp, avísalo.

## Reglas que el script ya cumple (no las cambies)

| Regla | Cómo |
|---|---|
| Unir por código, nunca por nombre | `ubigeo[:2]` con `FIRST_IDDP`, ambos como texto de 2 dígitos, `validate="1:1"` |
| 25 departamentos con dato | Se detiene si falta alguno |
| Lima (15) y Callao (07) separados | Se detiene si no están los dos |
| Escala interpretable | Un solo tono (`Reds`) de claro a oscuro, desde 0 |
| Unidad en la leyenda | «% de personas en pobreza monetaria» |
| Validación externa | Compara con `referencias/pobreza_departamento_2024.csv` (Sesión 16) |
| Salida | `mapas/pobreza_departamento.png` a 200 dpi |
