# Agente de investigación: MCP del BCRP + Skills de la ENAHO 2024

## 1. Objetivo del proyecto

Construir un agente en Claude Code que responda preguntas sobre el contexto de precios y política monetaria del Perú (series oficiales del BCRP) y sobre la pobreza monetaria 2024 (ENAHO del INEI). Cada cifra debe salir de una herramienta o de un script reproducible, no de la memoria del modelo.

El proyecto tiene cuatro partes:
1. Un servidor MCP propio para el BCRP.
2. Tres Skills que limpian, grafican y mapean la ENAHO 2024.
3. Un agente que integra ambos y produce un informe.
4. Una evaluación de 10 preguntas sin y con esas herramientas.

## 2. Arquitectura general del agente

```
                  Claude Code (el agente)
                 /                        \
   MCP "bcrp" (mcp/server.py)       Skills (.claude/skills/)
   - buscar_series                  - limpiando-enaho
   - serie                              |  salidas/personas_2024.parquet
   - resumen                            v
   - correlacion                    - graficando-enaho -> figuras/
   - graficar_serie                 - mapeando-enaho   -> mapas/
   - recurso bcrp://serie/{codigo}
   - prompt informe
            |                              |
   API del BCRP (internet)         datos/ (ENAHO 966 + GeoJSON)
            \                             /
                 informes/informe_final.md
```

## 3. Herramientas MCP (`mcp/server.py`)

- `buscar_series(texto, frecuencia, limite)`: busca en el catálogo oficial del BCRP por palabras y devuelve código, nombre, frecuencia y fecha de inicio.
- `serie(codigo, desde, hasta)`: descarga los datos de una serie entre dos fechas y devuelve la URL de la fuente.
- `resumen(codigo, desde, hasta)`: primero, último, cambio, variación %, promedio, máximo y mínimo de una serie.
- `correlacion(codigo_a, codigo_b, desde, hasta)` (propia): correlación de Pearson entre dos series de la misma frecuencia, sobre los periodos comunes.
- `graficar_serie(codigo, desde, hasta)`: guarda un gráfico de línea en `figuras/bcrp_<codigo>.png`.
- Recurso `bcrp://serie/{codigo}`: ficha descriptiva de una serie (nombre, categoría, frecuencia, inicio).
- Prompt `informe(tema)`: plantilla para un informe breve que obliga a citar código de serie, periodo y fuente.

## 4. Las tres Skills (`.claude/skills/`)

| Skill | Qué hace | Entra | Sale |
|---|---|---|---|
| `limpiando-enaho` | Limpia y une los módulos 34 y 02, filtra residentes habituales y valida contra cifras oficiales. | `datos/966-Modulo34.zip`, `datos/966-Modulo02.zip` | `salidas/personas_2024.parquet`, `salidas/indicadores.csv`, `salidas/validacion.txt` |
| `graficando-enaho` | Gráficos de barras ponderados de la pobreza por `area`, `sexo`, `edad` o `departamento`. | `salidas/personas_2024.parquet` | `figuras/pobreza_<grupo>.png` |
| `mapeando-enaho` | Mapa coroplético por departamento, unido por código `ubigeo[:2]` con `FIRST_IDDP`, validado con 25 departamentos. | `salidas/personas_2024.parquet`, `datos/peru_departamental_simple.geojson` | `mapas/pobreza_departamento.png`, `salidas/comparacion_mapa.csv` |

Las cifras de personas se ponderan siempre con `facpob07`.

## 5. Fuentes y enlaces de descarga

- **ENAHO 2024 (código 966), INEI.** Guardar los zip en `datos/` **sin descomprimir**:
  - https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip
  - https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip
- **GeoJSON departamental** (repositorio del curso). El script de mapas lo baja a `datos/peru_departamental_simple.geojson` si falta:
  - https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson
- **API y catálogo del BCRP.**
  - Series: https://estadisticas.bcrp.gob.pe/estadisticas/series/api
  - Catálogo: https://estadisticas.bcrp.gob.pe/estadisticas/series/metadata. Se descarga una vez a `datos/catalogo_bcrp.csv`.

`datos/` está en `.gitignore`: los datos no se suben al repositorio.

## 6. Instalación con uv

```
uv sync
```

Requiere Python 3.11 o superior (`pyproject.toml`). Dependencias principales: `fastmcp`, `pandas`, `geopandas`, `matplotlib`, `pyarrow`, `httpx` y `tabulate`. `pytest` está en el grupo de desarrollo.

## 7. Conectar el MCP a Claude Code

El archivo `.mcp.json` de la raíz ya declara el servidor `bcrp` (stdio, `uv run mcp/server.py`). Para registrarlo a mano:

```
claude mcp add --scope project bcrp -- uv run mcp/server.py
```

Dentro de Claude Code, `/mcp` muestra el estado del servidor y sus herramientas.

## 8. Comandos para reproducir

Todo se corre desde la raíz del proyecto.

```
# Pruebas del servidor MCP
uv run pytest -q mcp/

# Skills (en este orden)
uv run python ".claude/skills/limpiando-enaho/scripts/limpiar.py" --anio 2024
uv run python ".claude/skills/graficando-enaho/scripts/graficar.py" --por area
uv run python ".claude/skills/graficando-enaho/scripts/graficar.py" --por departamento
uv run python ".claude/skills/mapeando-enaho/scripts/mapear.py"

# Pedido completo al agente (dentro de Claude Code)
#   Lee informes/prompt_agente.md y ejecútalo completo.

# Evaluación (20 sesiones de claude -p; tarda varios minutos y consume uso de la cuenta)
uv run python evaluacion/evaluar.py
```

### Pruebas y validación

- **Pruebas del MCP:** 10 pruebas aprobadas (`10 passed in 19.03s`, ver `evidencias_ia/mcp/pytest_10_passed.txt`).
- **Validación ENAHO (`salidas/validacion.txt`):** las 11 validaciones salieron APROBADAS. Algunas cifras clave:
  - 108,664 residentes habituales (referencia 108,664) y 33,691 hogares.
  - La unión no duplica ni pierde filas.
  - 25 códigos territoriales.
  - Pobreza nacional 27.53 % (referencia 27.6 %, tolerancia ±0.1 pp).
  - Pobreza urbana 24.74 % (referencia 24.8 %) y rural 39.44 % (referencia 39.3 %).

## 9. Resultados de la evaluación

Resumen de `evaluacion/resumen_metricas.md` (modelo Haiku, 10 preguntas por modo, una corrida por pregunta). Comparación completa en [`evaluacion/comparacion.md`](evaluacion/comparacion.md).

| Modo | Correctas | Sin respuesta | Segundos promedio |
|---|---:|---:|---:|
| sin (sin herramientas) | 1 | 9 | 8.2 |
| con (MCP bcrp + Skills + Bash/Read/Glob/Grep) | 10 | 0 | 25.2 |

Correctas por tipo (BCRP / ENAHO / Combinada): sin = 0 / 1 / 0; con = 4 / 4 / 2.

Sin herramientas, el modelo prefirió responder `null` antes que estimar. Solo acertó la pobreza nacional.

## 10. Limitaciones y problemas encontrados

- **Cobertura:** la ENAHO es anual y la inflación es mensual y solo de Lima Metropolitana. El informe es descriptivo y no afirma causalidad entre inflación y pobreza.
- **Error muestral:** las estimaciones por departamento tienen márgenes de error que no se calculan aquí. El mapa difiere hasta 0.5 pp de la referencia (Huánuco y Puno).
- **Contraste de las cifras del BCRP:** en `informes/informe_final.md` la inflación y la tasa de referencia de diciembre de 2024 se contrastaron a mano con las tablas web del BCRP (coinciden, 0.00 pp). El contraste es manual y solo cubre esas dos cifras.
- **Evaluación:**
  - Una sola corrida por pregunta y un solo modelo, así que no mide variabilidad.
  - En las preguntas de ENAHO, el modo «con» lee resultados ya calculados en `salidas/`; no es un cálculo desde cero.
  - Varias sesiones llamaron al MCP del BCRP sin necesitarlo.
- **Evidencias e informes:**
  - `evidencias_ia/integracion/sesion_agente_completa.jsonl` (transcripción cruda de la sesión) no está versionado. Contiene rutas locales y datos de la cuenta; se decidió no subirlo y se dejó `conversacion_agente.txt`.
  - Se eliminó la carpeta duplicada `skills_enaho/`; las Skills vigentes están en `.claude/skills/`.
  - En Windows, la consola puede mostrar mal los acentos de la salida de los scripts; los archivos (`salidas/validacion.txt`, informes) están en UTF-8. Para verlos bien, usar `Get-Content ... -Encoding UTF8`.
- **No versionados (por `.gitignore`):** `datos/` y `salidas/*.parquet`. Hay que regenerarlos con los comandos de la sección 8.

## 11. Ejemplo de una ejecución completa

**Pedido** (en Claude Code): `Lee informes/prompt_agente.md y ejecútalo completo.`

**Qué hizo el agente**, en este orden:
1. Plan breve de series e indicadores.
2. MCP `bcrp`: `buscar_series` (inflación y tasa de referencia), `resumen` (2024-01 a 2024-12) y `graficar_serie` (`PN01273PM`, 2023-01 a 2024-12).
3. Skills: `limpiando-enaho`, `graficando-enaho` (`--por area` y `--por departamento`) y `mapeando-enaho`.
4. Contraste con las referencias oficiales y escritura del informe.

**Qué produjo:**
- `informes/informe_final.md`.
- Series usadas: `PN01273PM` (IPC Lima Metropolitana, var. % 12 meses) y `PD04722MM` (tasa de referencia).
- Cifras principales del informe:
  - La inflación pasó de 3.02 % (enero) a 1.97 % (diciembre).
  - La tasa de referencia bajó de 6.50 % a 5.00 %.
  - La pobreza fue 27.53 % a nivel nacional, 24.7 % urbana y 39.4 % rural, desde 45.0 % en Cajamarca hasta 5.9 % en Ica.
- Archivos: `figuras/bcrp_PN01273PM.png`, `figuras/pobreza_area.png`, `figuras/pobreza_departamento.png`, `mapas/pobreza_departamento.png`, `salidas/comparacion_mapa.csv`.

## 12. Evidencias del uso de IA (`evidencias_ia/`)

- [`evidencias_ia/mcp/`](evidencias_ia/mcp/): conversación de construcción del servidor MCP (`conversacion_mcp.txt`), la salida de las pruebas (`pytest_10_passed.txt`) y 4 capturas de pantalla del 2026-11-08.
- [`evidencias_ia/skills/`](evidencias_ia/skills/): conversación de construcción de las Skills (`conversacion_skills.txt`) y una captura de pantalla del 2026-11-09.
- [`evidencias_ia/integracion/`](evidencias_ia/integracion/): conversación exportada de la ejecución del agente integrado (`conversacion_agente.txt`).
- [`evidencias_ia/evaluacion/`](evidencias_ia/evaluacion/): conversación exportada de la sesión de evaluación y del README (`conversacion_evaluacion_readme.txt`).

## Estructura del repositorio

```
.mcp.json            conexión del MCP bcrp
mcp/                 server.py y test_server.py
.claude/skills/      limpiando-enaho, graficando-enaho, mapeando-enaho
evaluacion/          preguntas.csv, evaluar.py, resultados.csv, resumen_metricas.md, comparacion.md
informes/            prompt_agente.md, informe_final.md
figuras/  mapas/     gráficos y mapa generados
salidas/             validacion.txt, indicadores.csv, comparacion_mapa.csv
evidencias_ia/       conversaciones y capturas
```
