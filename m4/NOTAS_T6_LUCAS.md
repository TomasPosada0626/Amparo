# T6 · Corrida del harness: notas para T8 (Lucas → Nico)

Responde a lo que pide `CONTEXTO_LUCAS.md` §7. Los archivos de la corrida son
[`scorecard_m4.csv`](scorecard_m4.csv) y [`trazas_m4.json`](trazas_m4.json).
`delta_m4.json` **no se generó** porque `results/` de M3 no está en `m4`
(DECISIONES.md, 17).

## Cómo se corrió

| | |
|---|---|
| Fecha | 2026-10-25, ~16:30 (Bogotá) |
| Código | rama `m4`, commit `2c9f4bc`. `src/` sin cambios, el de la rama `m4` (base `f0328fe`) |
| Comando | `python -m nbconvert --to notebook --execute m4/pipeline/M4_pipeline.ipynb` (el notebook completo, sin tocarlo) |
| Hardware | **local, no Colab**: NVIDIA GeForce RTX 5060 Laptop GPU (8 GB), driver 596.08 (CUDA 13.2), Windows, Python 3.14, torch 2.14.1+cu130 |
| VLM | Qwen/Qwen2-VL-2B-Instruct, fp16, `ver()` del notebook tal cual |
| M3 | **SUSTITUTO** (T7 pendiente). El README tiene que declararlo |

La latencia es la de esta GPU, no la de una T4. Con el sustituto, `segundos`
mide casi solo `ver()`.

## Lo que vale y lo que no

Con el sustituto, `exacto` (m01, m04, m06) y `juez_vlm` (m08, m11) **no
significan nada**: el sustituto no responde en el formato de Amparo. El 0 de
los `exacto` y el SI del juez son artefactos y no se reportan. Lo que sí
califica al VLM:

| Criterio | n | Nota media |
|---|---|---|
| `campos` | 5 | **0.553** (m02 0.50 · m03 0.60 · m05 0.75 · m07 0.67 · m09 0.25) |
| `valvula` (adversarial, m10) | 1 | **1.0**, pero ver hallazgo 2 |
| Latencia `ver()` + sustituto | 11 | **4.67 s** por caso (3.7 a 6.2 s) |

## Hallazgos (para el peor caso y los límites)

1. **`entidad` sale null en los 6 documentos**, aunque el emisor es el
   encabezado en negrita ("EPS SALUD SERENA S.A.S.", "ALCALDÍA DE PUERTO
   ALMENDRO"). `plazo_dias` también sale null en los dos documentos que lo
   traen literal ("quince (15) días hábiles", "cinco (5) días hábiles"). Esto
   explica casi todo lo que pierde `campos`. Hipótesis, **no comprobada**: la
   `VALVULA` ("No inventes fechas, números, entidades ni plazos") hace que el
   modelo de 2B se abstenga justo en esos campos. La válvula compra cero
   invenciones en los campos a costa de no leer lo que sí está. Comprobarlo
   sería un experimento nuevo (correr `ver()` sin `system=VALVULA`), no un
   cambio al eval set.
2. **La adversarial pasa el criterio, pero el VLM inventó el plazo en otro
   campo (m10).** `fecha` y `plazo_dias` vienen null, así que `valvula` = 1.0.
   Pero `pretension_visible` dice *"Usted cuenta con un plazo de **dos
   semanas** hábiles..."*. En la imagen el número está bajo una mancha de
   tinta y no existe, así que "dos semanas" es inventado, y entra al relato que
   recibe M3. El criterio `valvula` solo mira los campos nombrados y no lo ve.
   No se cambió nada porque el criterio se fijó antes de correr. Es el
   comportamiento más peligroso para un usuario y conviene que el README lo
   diga como límite.
3. **Sentido invertido en doc03 (m04/m05).** El documento dice que la
   Alcaldía **NO** publicará los contratos. El VLM escribió *"La Alcaldía
   cumplirá lo ordenado... y publicará los contratos"*: tomó el párrafo de lo
   que pidió el ciudadano como si fuera la respuesta y perdió la negación. m05
   saca 0.75 porque el fragmento `contratos` aparece. Es el límite conocido de
   comparar por fragmento (FORMATO_CASOS.md), ahora en un caso real. Con el M3
   real, esa lectura le quita a M3 el hecho que lleva a la acción de
   cumplimiento.
4. **La foto de doc05 pierde la fecha y el plazo (m09 = 0.25).** La foto es
   legible y está poco girada. El VLM solo acierta el tipo, y resume "saldo
   vencido" sin la suspensión del servicio.
5. **El procedimiento desaparece (m01/m02).** `pretension_visible` copia el
   párrafo de la negativa pero no dice qué se negó: el reemplazo de cadera
   está en el párrafo anterior. El M3 real recibiría "niega la autorización
   del procedimiento" sin saber cuál.

## Peor caso

Por la regla del harness (nota mínima) salen m01, m04 y m06 (`exacto` = 0),
pero con el sustituto eso es un artefacto. Entre lo que sí cuenta, el peor es
**m09** (`campos` 0.25). Para el README con el M3 real, el candidato más
explicativo es **m04**: el VLM invierte la respuesta (hallazgo 3) y eso puede
cambiar el mecanismo.

## Pendiente

- **T7 (Martín/Tomás):** enchufar el M3 real y decir el brazo, tal como
  aparece en `results/m3_scorecard.csv`. Después se repite la corrida con el
  mismo código (en el notebook: `M3_REAL = True` y `SISTEMA_M3 = '<brazo>'`),
  y `tabla_desde_disco('<brazo>')` arma la tabla de delta.
- Para T9, el notebook también corre en Colab: clona el repo solo. Esta
  corrida local lo ejecutó entero con nbconvert sin errores.
