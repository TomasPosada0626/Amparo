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

## Archivos incluidos (17)

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
