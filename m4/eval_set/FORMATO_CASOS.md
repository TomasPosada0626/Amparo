# Formato de `casos_m4.csv` (contrato entre T4 y T5)

El harness de M4 (`m4/harness/criterios.py`, T5) lee `m4/eval_set/casos_m4.csv`
tal cual. Este documento fija qué tiene que traer cada fila para que el harness
la califique. Lo define T5 (Nico) y lo usa T4 (Lucas) para escribir los casos.
Un ejemplo válido está en [`casos_m4.ejemplo.csv`](casos_m4.ejemplo.csv): pasa
`validar_casos()` y lo prueban los tests.

**Regla de M2 que no cambia:** el `criterio` y el `esperado` de cada caso se
escriben **antes** de correr el sistema. Elegirlos después de ver la respuesta
no es evaluación.

## Columnas

CSV en UTF-8, con o sin BOM; Excel lo agrega al guardar "CSV UTF-8" y no pasa
nada. Una fila por caso.

| Columna | Qué va |
|---|---|
| `id` | Identificador único del caso, p. ej. `m01`. No se repite. |
| `pregunta` | Lo que el usuario escribe junto con la imagen. |
| `imagen` | Nombre del archivo dentro de `m4/eval_set/imagenes/`. Tiene que existir. |
| `esperado` | Depende del criterio (ver abajo). |
| `criterio` | Uno de `exacto`, `campos`, `valvula`, `juez_vlm`. |
| `tipo` | `normal` o `adversarial`, en minúsculas. No hay otros valores. |

Reglas del conjunto: **al menos 5 casos** y **exactamente 1 adversarial**, que
lleva criterio `valvula`.

## `esperado` por criterio

| Criterio | Qué califica | `esperado` | Ejemplo |
|---|---|---|---|
| `exacto` | El mecanismo que da M3 al final | Una clave: `tutela`, `accion_popular`, `accion_cumplimiento`, `habeas_corpus`, `via_ordinaria`, o `no_determinable` si lo correcto es abstenerse | `tutela` |
| `campos` | Lo que el VLM leyó del documento (su JSON) | Objeto JSON con los campos que se exigen (ver tabla siguiente). Los demás campos no se califican | `{"tipo_documento": "oficio", "plazo_dias": 15}` |
| `valvula` | Que el VLM deje en null lo que no se ve | Los campos que **deben** venir null, separados por `\|` | `fecha\|plazo_dias` |
| `juez_vlm` | Que la respuesta final se sostenga en la imagen | **Vacío** | |

### Cómo se compara cada campo en `campos`

Los cinco campos son los que el VLM tiene que extraer (`INSTRUCCION_DOMINIO`,
celda 8 del notebook). Antes de comparar se pasa todo a minúsculas, se quitan
las tildes y se juntan los espacios repetidos.

| Campo | Qué escribir en `esperado` | Acierta si |
|---|---|---|
| `tipo_documento` | Uno de `notificacion`, `oficio`, `respuesta_peticion`, `sentencia`, `otro` | el VLM dio ese mismo valor |
| `plazo_dias` | Un número entero, p. ej. `15` | el VLM dio ese número (`15`, `"15"` y `15.0` valen igual; `"15 días"` no) |
| `entidad`, `fecha`, `pretension_visible` | Un **fragmento** que tiene que aparecer en lo que lea el VLM, p. ej. `alcaldia de medellin` | el fragmento está dentro del valor del VLM |

La nota es la fracción de campos exigidos que aciertan. Por ejemplo, 2 de 3 da 0.67.

**Por qué la comparación depende del campo.** `tipo_documento` y `plazo_dias`
tienen un valor cerrado, así que se pide igualdad. Los otros tres son texto
libre: el VLM los parafrasea o les añade texto ("Alcaldía de Medellín -
Secretaría de Salud"), y con igualdad exacta fallarían lecturas correctas. Por
eso se escribe el fragmento que **no puede faltar**, y conviene que sea corto y
literal del documento. Para fechas, usa la forma en que aparece en la imagen
(`15 de enero de 2026` no es lo mismo que `2026-01-15`).

**Límite conocido.** Un valor del VLM muy largo podría contener el fragmento por
casualidad. Con fragmentos específicos el riesgo es bajo. Si un caso lo
necesita, que lo juzgue `juez_vlm`.

**No se admite `null` en `campos`.** Si lo que quieres medir es que un dato
**no** se invente, ese caso es `valvula`. Así cada criterio mide una sola cosa:
`campos` mide lo que se leyó bien y `valvula` lo que no se inventó.

## Qué cuenta como nota 0 y qué es un error del CSV

- **Nota 0 (fallo del sistema):** el VLM no devolvió un JSON que se pueda leer
  (en `campos` y `valvula`), inventó un valor que debía ser null, o el juez no
  contestó exactamente SI. "Probablemente sí" vale 0.
- **Error del CSV:** un `esperado` mal formado (clave de mecanismo que no
  existe, JSON roto, campo que el VLM no extrae, `null` en `campos`, fragmento
  vacío, `esperado` lleno en `juez_vlm`), un `tipo` o `criterio` desconocido,
  un id repetido o una imagen que no existe. **No se califica:** contarlo como
  fallo del sistema falsearía el scorecard. Se corrige el CSV y se vuelve a
  validar.

## Cómo validar el CSV antes de entregarlo

Desde la raíz del repo, sin GPU:

```python
import sys; sys.path.insert(0, "m4/harness")
from pathlib import Path
from criterios import cargar_casos, validar_casos

casos = cargar_casos("m4/eval_set/casos_m4.csv")
print(validar_casos(casos, carpeta_imagenes=Path("m4/eval_set/imagenes")))
# []  -> listo para correr
```

Cada problema sale en una línea con el `id` del caso.
