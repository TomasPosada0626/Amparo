# Corpus de normas — data/corpus/normas/

Textos legales colombianos descargados para alimentar el RAG de Amparo.

## Fuente

Los textos originales del acceso oficial (`secretariasenado.gov.co`, `funcionpublica.gov.co`,
`suin-juriscol.gov.co`) están bloqueados desde este entorno por la política de red de la
organización (egress allowlist). En su lugar se usó un espejo público en GitHub que republica,
sin modificar el contenido normativo, el texto consolidado y vigente tomado del **Sistema Único
de Información Normativa (SUIN-Juriscol)** del Ministerio de Justicia y del Derecho de Colombia
— la fuente oficial del Estado colombiano:

- Repositorio: https://github.com/scuervo91/leyes-colombianas (fork de
  https://github.com/legalize-dev/legalize-co)
- Pipeline generador: https://github.com/legalize-dev/legalize-pipeline (MIT)
- Fuente primaria citada en cada archivo: https://www.suin-juriscol.gov.co
- Licencia del contenido normativo: dominio público (según el propio repositorio)
- Descargado: 2026-09-21, rama `main`

Cada archivo `.md` conserva el frontmatter YAML original (`title`, `identifier`, `publication_date`,
`status`, `source`, `modification_summary`, etc.) seguido del texto consolidado de la norma, es
decir, ya incorpora las reformas vigentes (por ejemplo, el archivo de la Ley 1437 de 2011 ya trae
el Título II de derecho de petición tal como lo sustituyó la Ley 1755 de 2015).

**Advertencia:** es un espejo comunitario, no el boletín oficial. Antes de citar un artículo en
una respuesta de producción, verificar contra la fuente oficial (`suin-juriscol.gov.co` o
`secretariasenado.gov.co`) cuando haya acceso a internet sin restricciones.

## Archivos incluidos (28)

Los primeros 17 se descargaron el 2026-09-21. Los 11 de la sección "Agregadas el
2026-10-08" vienen del repositorio upstream del mismo espejo.

| Archivo | Norma |
|---|---|
| `codigo_penal_ley_599_2000.md` | Código Penal (Ley 599 de 2000) |
| `codigo_comercio_decreto_410_1971.md` | Código de Comercio (Decreto 410 de 1971) |
| `codigo_sustantivo_trabajo_decreto_2663_1950.md` | Código Sustantivo del Trabajo (Decreto 2663 de 1950) |
| `codigo_civil_ley_84_1873.md` | Código Civil (Ley 84 de 1873) |
| `codigo_general_proceso_ley_1564_2012.md` | Código General del Proceso (Ley 1564 de 2012) |
| `cpaca_ley_1437_2011.md` | CPACA — incluye derecho de petición vigente (Ley 1437 de 2011, sustituida por Ley 1755 de 2015) |
| `tutela_decreto_2591_1991.md` | Reglamentación de la acción de tutela (Decreto 2591 de 1991) |
| `habeas_data_datos_personales_ley_1581_2012.md` | Protección de datos personales (Ley 1581 de 2012) |
| `habeas_data_financiero_ley_1266_2008.md` | Hábeas data financiero (Ley 1266 de 2008) |
| `estatuto_consumidor_ley_1480_2011.md` | Estatuto del Consumidor (Ley 1480 de 2011) |
| `arrendamiento_vivienda_urbana_ley_820_2003.md` | Arrendamiento de vivienda urbana (Ley 820 de 2003) |
| `codigo_procedimiento_penal_ley_906_2004.md` | Código de Procedimiento Penal (Ley 906 de 2004) |
| `codigo_nacional_transito_ley_769_2002.md` | Código Nacional de Tránsito (Ley 769 de 2002) |
| `codigo_infancia_adolescencia_ley_1098_2006.md` | Código de la Infancia y la Adolescencia (Ley 1098 de 2006) |
| `ley_transparencia_acceso_info_ley_1712_2014.md` | Transparencia y acceso a la información pública (Ley 1712 de 2014) |
| `seguridad_social_ley_100_1993.md` | Sistema de seguridad social integral (Ley 100 de 1993) |
| `constitucion_politica_1991.md` | Constitución Política de Colombia de 1991 (texto completo, provisto por el usuario en PDF; ver detalle abajo) |

### Agregadas el 2026-10-08

Fuente: https://github.com/legalize-dev/legalize-co (el upstream del fork usado el 2026-09-21),
commit `c25da5b1a507dd681b6704334e284d2e60f8e6d3` (2026-09-05). Cada archivo es copia byte a
byte de `co/<IDENTIFIER>.md` en ese commit; solo cambia el nombre, para seguir la convención
del corpus. Se verificó además que los 16 archivos descargados el 2026-09-21 son idénticos a
los de ese commit: el corpus anterior sigue vigente tal cual.

| Archivo | Norma | Categoría del dataset |
|---|---|---|
| `contratacion_estatal_ley_80_1993.md` | Estatuto General de Contratación (Ley 80 de 1993) | Contratación estatal |
| `contratacion_estatal_ley_1150_2007.md` | Eficiencia y transparencia en la contratación (Ley 1150 de 2007) | Contratación estatal |
| `sancionatorio_ambiental_ley_1333_2009.md` | Procedimiento sancionatorio ambiental (Ley 1333 de 2009) | Derecho ambiental sancionatorio |
| `ordenamiento_territorial_ley_388_1997.md` | Ordenamiento territorial (Ley 388 de 1997) | Licencias urbanísticas |
| `ley_general_educacion_ley_115_1994.md` | Ley General de Educación (Ley 115 de 1994) | Educación / debido proceso |
| `convivencia_escolar_ley_1620_2013.md` | Convivencia escolar (Ley 1620 de 2013) | Educación / debido proceso |
| `violencia_intrafamiliar_ley_294_1996.md` | Violencia intrafamiliar (Ley 294 de 1996) | Violencia intrafamiliar |
| `violencia_contra_la_mujer_ley_1257_2008.md` | Violencia contra la mujer (Ley 1257 de 2008) | Violencia intrafamiliar |
| `observancia_propiedad_industrial_ley_1648_2013.md` | Observancia de la propiedad industrial (Ley 1648 de 2013) | Propiedad intelectual - marcas |
| `competencia_desleal_ley_256_1996.md` | Competencia desleal (Ley 256 de 1996) | Propiedad intelectual - marcas |
| `discapacidad_estabilidad_reforzada_ley_361_1997.md` | Integración de personas con discapacidad (Ley 361 de 1997) | Despido (estabilidad reforzada) |

### Texto ajeno dentro de algunos archivos

El espejo intercala en algunos archivos texto de otra norma con su propia numeración. Si se
indexara, el sistema citaría un artículo que no es de esa norma. Los archivos no se modifican
(siguen siendo copia exacta del espejo); el texto ajeno se quita al ingerir, declarado en
`tools/rag/corpus.py` y con un test que falla si el marcador deja de encontrarse:

| Archivo | Texto ajeno | Cómo se quita |
|---|---|---|
| `ley_transparencia_acceso_info_ley_1712_2014.md` | Después de los 33 artículos, el proyecto de ley que revisó la Corte | `articulos_propios=33` |
| `habeas_data_datos_personales_ley_1581_2012.md` | Después de los 30 artículos, el proyecto de ley y extractos de otros instrumentos | `articulos_propios=30` |
| `codigo_comercio_decreto_410_1971.md` | Tras el art. 751, los 6 artículos de la ley de cheques fiscales numerados desde 1 | `fragmentos_ajenos` |
| `codigo_civil_ley_84_1873.md` | Antes del art. 1, un "Artículo 1" de un decreto de estado de sitio | `fragmentos_ajenos` |

Advertencia sobre el Código Civil: el espejo conserva en algunos artículos la redacción
original con expresiones que la Corte Constitucional declaró inexequibles (por ejemplo,
"legítimos" y "naturales" en el art. 411). Antes de citar un artículo del Código Civil en
producción, verificarlo contra la fuente oficial.

## Constitución Política de 1991

No estaba en el espejo de GitHub (SUIN-Juriscol no la indexa con el mismo esquema ley/decreto
del resto del repositorio) ni se pudo descargar de una fuente `.gov.co` por el bloqueo de red.
El usuario subió el PDF directamente (edición de Political Database of the Americas, Georgetown
University, con las notas de la Secretaría General de la Asamblea Nacional Constituyente sobre
la Gaceta Constitucional No.114). Se extrajo el texto con `pdftotext -layout` (440 apariciones de
"Artículo", articulado permanente + disposiciones transitorias) y se guardó en
`constitucion_politica_1991.md`. Verificar contra el Diario Oficial o `secretariasenado.gov.co`
antes de citar un artículo en producción.

## Pendiente

- Ley 1755 de 2015 como archivo independiente: no existe en el espejo, pero su contenido vigente
  ya está incorporado dentro de `cpaca_ley_1437_2011.md` (Título II).
- El espejo no trae leyes posteriores a 2014 ni la Ley 142 de 1994, y la Decisión 486 de la CAN
  no es norma colombiana, así que SUIN no la publica. Faltan, y hay que traerlas de
  `secretariasenado.gov.co` (como la Constitución, en PDF o HTML):
  - Ley 142 de 1994 (servicios públicos domiciliarios): hoy la categoría queda sin norma.
  - Ley 1801 de 2016 (Código de Policía): querellas policivas, linderos, licencias.
  - Ley 2220 de 2022 (estatuto de conciliación; la Ley 640 de 2001 está derogada).
  - Ley 1751 de 2015 (estatutaria de salud).
  - Ley 1010 de 2006 (acoso laboral).
  - Ley 2126 de 2021 (comisarías de familia).
  - Decisión 486 de 2000 de la CAN (régimen de propiedad industrial: marcas).
  La lista vive también en `tools/rag/corpus.py` (`NORMAS_PENDIENTES`).
