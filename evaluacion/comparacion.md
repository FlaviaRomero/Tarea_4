# Comparación de modos: sin herramientas vs. con MCP del BCRP y Skills de ENAHO

Fuentes: `evaluacion/resultados.csv` y `evaluacion/resumen_metricas.md` (modelo Haiku, 10 preguntas por modo, una corrida por pregunta). No se modificaron `resultados.csv` ni `preguntas.csv`.

## 1. Correctas, incorrectas y sin respuesta por modo

| Modo | Correctas | Incorrectas | Sin respuesta | Segundos promedio |
|---|---:|---:|---:|---:|
| sin | 1 | 0 | 9 | 8.2 |
| con | 10 | 0 | 0 | 25.2 |

## 2. Correctas por tipo de pregunta

| Modo | BCRP (4 preguntas) | ENAHO (4 preguntas) | Combinada (2 preguntas) |
|---|---:|---:|---:|
| sin | 0 | 1 | 0 |
| con | 4 | 4 | 2 |

## 3. Mejoró, empeoró o quedó igual (sin → con)

| Pregunta | sin | con | Cambio |
|---|---|---|---|
| bcrp_ipc_set26 | sin respuesta | correcta | Mejoró |
| bcrp_ipc_dic25 | sin respuesta | correcta | Mejoró |
| bcrp_ref_set26 | sin respuesta | correcta | Mejoró |
| bcrp_pbi_2025 | sin respuesta | correcta | Mejoró |
| enaho_nacional | correcta | correcta | Igual |
| enaho_rural | sin respuesta | correcta | Mejoró |
| enaho_cusco | sin respuesta | correcta | Mejoró |
| enaho_cajamarca | sin respuesta | correcta | Mejoró |
| mixta_ipc_urbana | sin respuesta | correcta | Mejoró |
| mixta_ref_rural | sin respuesta | correcta | Mejoró |

Resumen: 9 mejoraron, 1 quedó igual, 0 empeoraron.

## 4. Errores principales de cada modo

**Modo sin.** La columna `error` está vacía en las 10 filas.
- 9 de 10 respuestas fueron «sin respuesta». Todas usaron solo `StructuredOutput` y dejaron `valores` en null.
- En `fuente_respuesta` explican que solo tenían la herramienta de salida estructurada. No podían leer archivos ni consultar el BCRP, y por eso no estimaron.
- En `bcrp_ref_set26` además dicen que su conocimiento llega hasta junio de 2026, así que no podían saber el valor de setiembre de 2026.
- Ninguna respuesta fue incorrecta. El modo fallaba por omisión y no por inventar cifras.
- La única correcta, `enaho_nacional` (27.6), la dio «de memoria» según `fuente_respuesta`, con la advertencia de que no la había verificado.

**Modo con.** La columna `error` está vacía en las 10 filas y no hubo respuestas incorrectas.
- **BCRP:** `mcp__bcrp__buscar_series` y `mcp__bcrp__serie`, con series `PN01273PM`, `PD04722MM` y `PM04923AA`, y URL de la fuente en `fuente_respuesta`.
- **ENAHO:** `Bash` (en una pregunta también `Read` y `Grep`) sobre `salidas/indicadores.csv` o `salidas/personas_2024.parquet`.
- **Mixtas:** combinan ambas vías.
- **Llamadas innecesarias al MCP:** en `enaho_nacional`, `enaho_rural` y `enaho_cusco` llamó a `mcp__bcrp__buscar_series` y reconoció en `fuente_respuesta` que no sirvió.
- **Desvíos frente a la referencia:** rural 39.44 frente a 39.3 y Cusco 18.54 frente a 18.5, ambos dentro de la tolerancia fijada.
- **Cifra sin contrastar:** en las dos mixtas aclara que no contrastó la cifra de pobreza con la publicación oficial del INEI.

## 5. Interpretación en las preguntas combinadas

| Pregunta | Modo | ¿Evita afirmar causalidad? | Valoración |
|---|---|---|---|
| mixta_ipc_urbana | sin | Sí: dice que una relación causal directa no puede establecerse con solo estos datos. Sin valores. | Coherente |
| mixta_ipc_urbana | con | Sí: no se puede concluir relación, hacen falta varios años, y el contraste «no indica nada sobre causa o efecto». | Coherente |
| mixta_ref_rural | sin | Sí: «un solo par de datos anuales tampoco permite inferir causalidad». Sin valores. | Coherente |
| mixta_ref_rural | con | Sí: no puede atribuirse la pobreza a la tasa; solo describe ambas cifras del mismo año. | Coherente |

Las cuatro interpretaciones son coherentes. En el modo «sin», la de `mixta_ipc_urbana` menciona que la inflación afecta la línea de pobreza, pero lo plantea como contexto metodológico y aclara que no se puede establecer causalidad. Además, esas dos respuestas no aportan cifras. Su coherencia es más débil como evidencia.

## 6. Herramientas habilitadas (de `resumen_metricas.md`)

- **sin:** ninguna herramienta; sin MCP, sin Skills, sin archivos, terminal ni web. Solo el conocimiento del modelo.
- **con:** MCP `bcrp` (`.mcp.json`), Skills del proyecto y de la cuenta, `Bash`, `Read`, `Glob` y `Grep`. Sin web.

## 7. Conclusión

Con el MCP del BCRP y las Skills, Haiku respondió correctamente 10 de 10 preguntas, frente a 1 de 10 sin herramientas. Las 9 restantes del modo «sin» quedaron sin respuesta, porque el modelo prefirió no estimar. El MCP aportó las cifras recientes del BCRP, que no estaban en su conocimiento: serie y periodo citados, con URL. Las Skills dieron cifras de ENAHO reproducibles desde los microdatos y validadas. El costo fue más tiempo (25.2 s frente a 8.2 s en promedio). Como hay una sola corrida por pregunta y un solo modelo, la comparación indica la diferencia entre modos pero no mide la variabilidad. Además, en ENAHO el modo «con» consulta resultados ya calculados en el proyecto, no hace un cálculo independiente.
