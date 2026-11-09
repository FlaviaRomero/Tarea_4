# Pedido al agente de investigación (Parte 3)

Ejecuta esta investigación de principio a fin en esta misma sesión, usando el servidor MCP `bcrp` y las Skills del
proyecto. No copies cifras a mano ni las inventes: cada número debe salir de una herramienta MCP o de un script de
una Skill. Si una herramienta falla o un dato no existe, dilo en el informe como limitación.

## Pregunta de investigación

> En 2024, ¿en qué contexto de precios y de política monetaria se encontraba el Perú según el BCRP, y cómo se
> distribuyó la pobreza monetaria entre áreas (urbana/rural) y departamentos según la ENAHO 2024 del INEI?

## Pasos

1. **Plan.** Escribe primero un plan breve: qué series del BCRP y qué indicadores de la ENAHO necesitas y con qué
   herramienta o Skill obtendrás cada uno.
2. **BCRP (MCP, mínimo 2 herramientas distintas).**
   - Con `buscar_series` encuentra la inflación a 12 meses de Lima Metropolitana (mensual) y la tasa de referencia
     de la política monetaria.
   - Con `resumen` obtén para 2024-01 a 2024-12 el primero, el último, el promedio, el máximo y el mínimo de cada serie.
   - Con `graficar_serie` guarda el gráfico de la inflación a 12 meses de 2023-01 a 2024-12.
3. **ENAHO (Skills, mínimo 2 distintas).**
   - Usa `limpiando-enaho` y lee `salidas/validacion.txt`. Si falla una validación esencial, detente y repórtalo.
   - Usa `graficando-enaho` para el gráfico por área (`--por area`) y por departamento (`--por departamento`).
   - Usa `mapeando-enaho` para el mapa departamental.
4. **Contrastar.** Compara tus cifras con las referencias oficiales: pobreza nacional 27.6 %, urbana 24.8 %, rural
   39.3 % (INEI) y la tabla departamental de `salidas/comparacion_mapa.csv`.
5. **Informe.** Escribe `informes/informe_final.md` con estas secciones, en este orden:
   1. **Pregunta de investigación:** tema, objetivo y delimitación (Perú, 2024, pobreza monetaria; sin causalidad).
   2. **Fuentes y metodología:** series del BCRP con su código; módulos 34 y 02 de la ENAHO 2024; filtro de
      residentes habituales; ponderación con `facpob07`; unión por `ubigeo[:2]` y `FIRST_IDDP`.
   3. **Resultados:** al menos 3 hallazgos numerados, cada uno con su cifra y su fuente (código de serie o archivo).
      Al menos uno debe venir del BCRP y al menos uno de la ENAHO.
   4. **Visualizaciones:** inserta con Markdown `../figuras/bcrp_PN01273PM.png` (o el código que corresponda),
      `../figuras/pobreza_area.png`, `../figuras/pobreza_departamento.png` y `../mapas/pobreza_departamento.png`.
   5. **Interpretación:** los patrones principales, sin afirmar causalidad entre inflación y pobreza.
   6. **Verificación de cifras:** una tabla con al menos 4 afirmaciones (2 del BCRP y 2 de la ENAHO) y las columnas
      Afirmación | Valor calculado | Fuente o procedimiento | Referencia oficial | ¿Coincide? | Diferencia.
   7. **Limitaciones:** cobertura temporal (la ENAHO es anual y la inflación mensual), la inflación es de Lima
      Metropolitana, el error muestral por departamento, y cualquier error que haya ocurrido en esta ejecución.
   8. **Reproducibilidad:** comandos para repetir todo (`uv run ...`), scripts de cada Skill, herramientas MCP y
      códigos de serie usados, y archivos de salida.
6. Al final, resume en el chat qué herramientas MCP y qué Skills usaste, en qué orden.
