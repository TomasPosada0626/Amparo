# Guía de autoría del dataset de M1

Esta guía define qué es una buena respuesta en `data/dataset_src/*.md`. Existe
porque la primera versión del dataset pasaba cualquier revisión manual —cada
ejemplo, leído suelto, se veía bien— y solo al medir el conjunto se vio que el
79% de las respuestas daba consejo genérico sin decirle a la persona a dónde
acudir. Lo que el modelo aprende aquí se arrastra a M2 y a M3, así que el
estándar se hace explícito y se verifica con `tools/dataset_quality.py`.

Referencia de calidad: **`despido.md`** (ya reescrito). Léelo antes de empezar.

## Formato del archivo

```
# Categoria: <nombre exacto, no cambiar>

## <id numérico, no cambiar>

P: <pregunta del usuario>

R: <respuesta del asistente>
```

**No cambies los IDs ni los nombres de categoría**: son la llave con la que se
cruzan los resultados de M1, M2 y M3.

## Qué hacer con las preguntas

**Déjalas como están.** Ya son buenas: registro coloquial, primera persona,
sin jerga. Están escritas sin tildes a propósito —así escribe mucha gente desde
el celular— y esa mezcla hace al modelo robusto a la entrada real.

Solo intervén si una pregunta es ambigua hasta el punto de no poder responderse.

## Qué debe tener una respuesta

1. **Una ruta concreta y nombrada.** Es el punto central. No basta con "reclama
   ante la autoridad competente": hay que decir **cuál**.
   - ✅ "presenta una querella ante la Inspección del Trabajo"
   - ✅ "la vía más rápida suele ser la acción de tutela"
   - ✅ "acude a la Comisaría de Familia"
   - ✅ "puedes demandar ante el juez civil"
   - ❌ "puedes reclamar ante la autoridad laboral" (¿cuál?)
   - ❌ "evalúa las acciones legales disponibles"

2. **Qué evidencia reunir.** Concreta y propia del caso (el contrato, la carta
   de despido, la historia clínica, el comparendo, las fechas de radicación).

3. **Lenguaje cotidiano.** Si usas un término técnico, explícalo en la misma
   frase. El lector no es abogado y muchas veces está angustiado.

4. **Ortografía correcta, con tildes.** Es la salida del producto.

5. **Entre 25 y 60 palabras.** Breve, pero con la ruta y la evidencia.

## Qué NO debe tener

- **Números de artículo, de ley, de decreto o de sentencia.** Nunca. Ese
  conocimiento verificable lo aporta el RAG de M3 contra el corpus real; si el
  modelo lo memoriza, inventa precisión que no puede respaldar. Di "la ley
  laboral exige", no "el artículo 64 del CST".
- **Plazos exactos** ("15 días hábiles", "en 3 meses"). Mismo motivo: cambian
  por trámite y por norma. Di "dentro del término legal" o "hay un plazo corto,
  verifícalo".
- **Promesas de resultado** ("vas a ganar", "te van a pagar seguro"). Orientar
  no es garantizar.
- **Arranques repetidos.** Si todas tus respuestas empiezan con "Reúne..." o
  "Solicita...", el modelo aprende la fórmula y no el contenido. Varía.

## Caso especial: urgencia

Si la pregunta describe **riesgo para la integridad o la salud** (amenazas,
violencia, desalojo inminente, urgencia médica negada), la respuesta debe
**empezar por la ayuda inmediata** y después explicar la ruta legal:

> "Lo primero es tu seguridad: si estás en riesgo, llama a la Línea 123 o acude
> a la Comisaría de Familia, que puede dictar una medida de protección. Después,
> para el contrato de arriendo, puedes..."

Nunca dejes a alguien en riesgo con una explicación puramente procedimental.

## Cómo verificar tu trabajo

Las puertas de calidad son ejecutables. Corre esto y no entregues hasta que
pasen todas:

```bash
python3 -c "
import pathlib
from tools.dataset_build import parsear_fuente, construir
from tools.dataset_quality import analizar, reportar
_, ej = parsear_fuente(pathlib.Path('data/dataset_src/TU_ARCHIVO.md'))
print(reportar(analizar(construir(ej))) or 'TODAS LAS PUERTAS PASAN')
"
```

Si la puerta de "mecanismo legal" marca como fallo una respuesta que **sí**
nombra una ruta real, el problema puede ser el catálogo de
`tools/dataset_quality.py` (`MECANISMOS`), no tu texto: repórtalo en vez de
retorcer la redacción para engañar a la métrica. La métrica está para medir el
contenido, no al revés.
