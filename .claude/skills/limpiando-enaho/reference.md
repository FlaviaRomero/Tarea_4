# Diccionario mínimo de la ENAHO 2024

## Archivos

| Módulo | Archivo en el zip | Una fila por | Filas | Llaves | Factor |
|---|---|---|---|---|---|
| 34, sumaria | `Sumaria-2024.dta` | hogar | 33,691 | `conglome`, `vivienda`, `hogar` | `factor07` (hogares) |
| 02, miembros | `Enaho01-2024-200.dta` | persona | 117,721 | las tres + `codperso` | `facpob07` (personas) |

## Variables usadas

| Variable | Módulo | Qué es | Valores |
|---|---|---|---|
| `ubigeo` | ambos | Ubicación geográfica | 6 dígitos; los 2 primeros son el departamento (01–25) |
| `dominio` | 34 | Dominio geográfico | 1–7 regiones naturales por área; 8 = Lima Metropolitana |
| `estrato` | 34 | Estrato por tamaño de centro poblado | 1–5 urbano, 6–8 rural |
| `pobreza` | 34 | Pobreza monetaria | 1 pobre extremo, 2 pobre no extremo, 3 no pobre |
| `mieperho` | 34 | Miembros del hogar (sin trabajadores del hogar ni pensionistas) | número |
| `factor07` | 34 | Factor de expansión del hogar | número |
| `p203` | 02 | Relación de parentesco con el jefe | 1 jefe, 2 cónyuge, 3 hijo, … |
| `p204` | 02 | ¿Es miembro del hogar? | 1 sí, 2 no |
| `p205` | 02 | ¿Estuvo ausente 30 días o más? | 1 sí, 2 no |
| `p206` | 02 | ¿Estuvo presente 30 días o más? (no miembros) | 1 sí, 2 no |
| `p207` | 02 | Sexo | 1 hombre, 2 mujer |
| `p208a` | 02 | Edad en años cumplidos | número |
| `facpob07` | 02 | Factor de expansión de la población | número |

## Cifras oficiales 2024 para validar

| Cifra | Valor |
|---|---|
| Pobreza monetaria nacional | 27.6 % (27.58 % sumaria con `factor07 × mieperho`; 27.53 % personas con `facpob07`) |
| Pobreza extrema | 5.5 % |
| Urbana / rural (`estrato <= 5`) | 24.8 % / 39.3 % |
| Lima Metropolitana (`dominio == 8`) | 28.2 % |
| Residentes habituales | 108,664 |

## Trampas

- Leer las llaves como número borra los ceros: `01` se vuelve `1` y el mapa pierde departamentos.
- Sin filtrar residentes habituales se cuentan visitas y la pobreza cambia.
- Un promedio simple de `pobre` no es la pobreza: hay que ponderar.
- Unir sin `validate="m:1"` puede duplicar personas sin avisar.
