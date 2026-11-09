# Métricas de la evaluación (haiku)

## Por modo

| modo   |   correcta |   sin respuesta |   segundos_promedio |
|:-------|-----------:|----------------:|--------------------:|
| con    |         10 |               0 |                25.2 |
| sin    |          1 |               9 |                 8.2 |

## Correctas por tipo de pregunta

| modo   |   BCRP |   Combinada |   ENAHO |
|:-------|-------:|------------:|--------:|
| con    |      4 |           2 |       4 |
| sin    |      0 |           0 |       1 |

## Pregunta por pregunta

| id               | con      | sin           |
|:-----------------|:---------|:--------------|
| bcrp_ipc_dic25   | correcta | sin respuesta |
| bcrp_ipc_set26   | correcta | sin respuesta |
| bcrp_pbi_2025    | correcta | sin respuesta |
| bcrp_ref_set26   | correcta | sin respuesta |
| enaho_cajamarca  | correcta | sin respuesta |
| enaho_cusco      | correcta | sin respuesta |
| enaho_nacional   | correcta | correcta      |
| enaho_rural      | correcta | sin respuesta |
| mixta_ipc_urbana | correcta | sin respuesta |
| mixta_ref_rural  | correcta | sin respuesta |

## Herramientas habilitadas

- **sin**: Ninguna herramienta: sin MCP, sin Skills, sin archivos, terminal ni web. Solo el conocimiento del modelo.
- **con**: MCP bcrp (.mcp.json), Skills del proyecto y de la cuenta, Bash, Read, Glob y Grep. Sin web.
