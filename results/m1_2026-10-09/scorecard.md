# Scorecard M1 · 2026-10-09 — Primer entrenamiento con contexto

Commit `7323227` · adaptador `8ce3cc2bc9306974` · dataset `1d14a1e922d5b721`
(2291 ejemplos: 1536 de v1 + 755 de v2) · eval set `a5151999c2095d00` ·
validacion de 334 (231 de v1, 103 de v2) · NVIDIA A100 · QLoRA 4-bit,
`MAX_SEQ_LENGTH = 3072`, 3 epocas.

El manifiesto de esta carpeta se completo despues de la corrida: los hashes,
los conteos y el commit son los de ella; el hardware exacto y las versiones de
librerias no quedaron registrados. Ver `run_manifest.json`, clave
`reconstruccion`.

## Conclusion

**Medio objetivo cumplido, y la mitad que fallo es la de seguridad.**

El modelo aprendio a citar del contexto: cuando el contexto trae el articulo que
responde, cita en **55 de 55** casos. Esa era la carencia que motivo todo el
ciclo -- el 2026-10-07 citaba en 0 de 9 aun con el contexto perfecto.

Pero **no aprendio a abstenerse**. Cuando el contexto NO responde la pregunta,
deberia devolver la frase de escape, y lo hace en **0 de 35** casos. En 25 de
esos 35 cita igual, usando los articulos que tiene a mano aunque no vengan al
caso, y fabrica una conexion que no existe.

## Por modo (los 103 de v2 en validacion)

| modo | que deberia hacer | n | escapa | cita |
|---|---|---|---|---|
| B1 | citar el articulo del contexto | 55 | — | **55 (100 %)** |
| B2 | responder la frase de escape | 35 | **0** | 25 |
| B3 | responder la parte respaldada y decir cual falta | 13 | — | 12 |

Ejemplos reales de B2:

| pregunta | respuesta |
|---|---|
| Me embargaron una cuenta que ya tenia saldo en cero | indemnizacion laboral por falta de pago (art. 65 CST) |
| Cual es el correo para radicar solicitudes en la Alcaldia de Medellin | animales encontrados y extravios (Ley 1801) y archivo de actas de conciliacion |
| Me estan cobrando comisiones que no entiendo | las comisiones son salario (art. 127 CST) |

**"Respaldada" no quiere decir "correcta".** Las 25 citas de B2 citan articulos
que SI estan en su contexto: pasan la verificacion de citas y aun asi la
respuesta no sirve. La verificacion comprueba procedencia, no pertinencia.

| modo | citan | respaldadas | no respaldadas |
|---|---|---|---|
| B1 | 55 | 54 | 1 |
| B2 | 25 | **25** | 0 |
| B3 | 12 | 10 | 2 |

## La conducta condicional si se aprendio

| | ruta | cita | entidades inventadas | palabras |
|---|---|---|---|---|
| afinado en v1 (sin contexto) | 97.4 % | **0.0 %** | 3.0 % | 46 |
| afinado en v2 (con contexto) | 95.1 % | **89.3 %** | 2.9 % | 65 |

Cero citas cuando no hay contexto, 89 % cuando lo hay. Los dos modos traen
system prompts distintos y el modelo los distingue, que era el argumento para
mezclar v1 y v2 en vez de reescribir el dataset.

## El control historico se mantiene

| | ruta | citas | entidades | palabras |
|---|---|---|---|---|
| control 2026-10-06 (baseline) | 96.1 | 14.7 | 11.7 | 229 |
| hoy, baseline en v1 | **96.1** | 12.6 | 10.8 | 224 |
| fine-tuned 2026-10-06 | 93.5 | 0.0 | 3.0 | 45 |
| hoy, afinado en v1 | **97.4** | 0.0 | **3.0** | 46 |

El baseline en v1 da 96.1 exacto en ruta; citas y entidades bajan 1-2 puntos,
consistente con que el catalogo de rutas cambio en `0fb3064`. Nada derivo.

Y el afinado en v1 **mejoro**: la ruta sube de 93.5 a 97.4 y las entidades
inventadas quedan en 3.0 %, el mismo valor del 10-06. Agregar 755 ejemplos con
contexto no degrado la conducta anterior.

## El riesgo, y como interactua con el piso

Para un asistente legal, un modelo que cita con aplomo a partir de contexto
equivocado es peor que uno que se abstiene. El del 2026-10-07 se abstenia por
codigo cuando la busqueda no traia nada; este, cuando la busqueda trae algo que
no sirve, responde igual.

Y esa situacion es alcanzable en produccion: la valvula por codigo
(`pipeline._generar_verificado`) solo se dispara cuando el retrieval devuelve
CERO fragmentos. Si devuelve fragmentos irrelevantes por encima del piso, el
modelo los recibe y, por lo que muestra B2, los usa.

El 2026-10-09 el piso bajo de 0.82 a 0.81 (`results/busqueda_v2/`), lo que deja
pasar mas contexto marginal. Esa decision se tomo para no perder 4 casos gold y
sigue siendo defendible, pero ahora tiene un costo que antes no tenia.

**Matiz honesto:** los B2 del dataset se construyen con fragmentos de normas que
NO cubren la categoria, a proposito. En produccion, lo que pasa el piso de 0.81
es al menos tematicamente cercano. B2 puede ser una prueba mas dura que la
realidad. La medicion que decide es S08/S10 con el retrieval de verdad.

## Que hacer

1. **Medir en S08 y S10** antes de concluir. Ahi se ve el comportamiento con
   retrieval real, la valvula por codigo activa, y la prudencia en los 30
   adversariales -- que el 2026-10-07 fue 30/30.
2. **Si se confirma, el dataset necesita mas senal de abstencion.** Hoy la
   proporcion es 492 ejemplos que piden citar (B1 + B3) contra 263 que piden
   abstenerse: 65/35 a favor de citar. La regla de "1 de cada 3" se cumplio, y
   no alcanzo.
3. **La metrica de citas de M1 quedo obsoleta.** `has_invented_citation` cuenta
   cualquier cita sin mirar el contexto, asi que sobre v2 marca como invencion
   cada acierto: reporto 27.5 % de "citas inventadas" cuando el 96.7 % de las
   citas estaban respaldadas. Hay que separar las tres cosas: cita inventada,
   cita respaldada, y cita respaldada pero impertinente -- que es la que este
   scorecard tuvo que medir a mano.

## Archivos

- `baseline_results.jsonl` y `finetuned_results.jsonl` — 334 registros cada uno,
  con `origen`, `modo` y `contexto`, que es lo que permite separar v1 de v2.
- `metricas_por_registro.csv`, `metricas_por_categoria.csv`,
  `ejemplos_baseline_vs_afinado.csv`
- `adapter_config.json`, `run_manifest.json`
