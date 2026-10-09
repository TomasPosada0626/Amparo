# Abstencion: medirla por subcadena daba el diagnostico al reves

Corrida `m3_s10_2026-10-09` (commit `5c884760`, adaptador `8ce3cc2bc9306974`,
indice `19657d22583f93d0`, eval set `a5151999c2095d00`, 11975 chunks).

La fase 5c de S10 **nunca habia ejecutado** antes del 2026-10-09: un bug de
variable la rompia en silencio desde el 7 de octubre. Al correr, la tasa de
escape en gold salio 0.60 y la primera lectura de este documento fue "el modelo
sobre-abstiene con retrieval real". **Esa lectura era un artefacto de la
medicion.** Lo que sigue es la version corregida.

## El fallo de medicion

`es_valvula_de_escape` busca la frase de escape como subcadena, asi que marca
igual dos cosas distintas:

- **abstenerse**: negarse a orientar;
- **orientar y acotar**: responder con la norma que corresponde y decir, de
  paso, que hay algo que no puede afirmar.

El caso 9002 es el ejemplo. Conto como escape:

> "El articulo 62 del Codigo Sustantivo del Trabajo permite terminar el
> contrato cuando el empleador incumple sistematicamente sus obligaciones...
> **No tengo informacion verificada** sobre como se valoran esas causales en un
> despido por presion. Reune el acta, mensajes y testigos, y consulta en un
> consultorio juridico universitario."

Eso no es abstenerse: es exactamente el comportamiento que piden los ejemplos
B3 del dataset.

`es_abstencion_pura` separa las dos: exige la frase **y** que la respuesta no
cite ningun articulo.

## Las cifras, separadas

| S10 `una_pasada` | n | abstencion pura | orienta y acota | orienta sin la frase |
|---|---|---|---|---|
| gold | 45 | **8** (18 %) | 19 | 18 |
| adversarial | 30 | **20** (67 %) | 4 | 6 |

| S08 `config C` | n | abstencion pura | orienta y acota | orienta sin la frase |
|---|---|---|---|---|
| gold | 45 | **14** (31 %) | 14 | 17 |
| adversarial | 30 | **19** (63 %) | 8 | 3 |

**El modelo si discrimina**: en S10 se abstiene de verdad 3.7 veces mas en
adversariales que en gold (67 % contra 18 %), y 37 de 45 casos gold reciben una
respuesta de fondo. La subcadena convertia eso en "60 % de escape en gold".

Las 19 respuestas que orientan y acotan tambien corrigen otra lectura: en M1,
B3 daba 0 de 13 y se concluyo que el comportamiento de avisar del hueco no
estaba en el modelo. Con retrieval real aparece en 19 de 45 casos. Lo que falla
en B3 es el formato que el criterio exige, no la conducta.

## Lo que queda en pie

### Quien decide el escape

Ninguna de las respuestas con la frase en gold la fuerza el pipeline:

```
lo decidio el MODELO         27
por codigo (umbral/citas)     0
```

Asi que **no es el umbral** `RETRIEVAL_MIN_SCORE = 0.81` (`escape_por_codigo`
es `null` en todas), **no es el verificador de citas** (`citas_rechazadas`
vacio) y **no es la cantidad de contexto** (52 de 72 casos con 5 fragmentos la
contienen). Bajar el umbral o subir TOP_K no toca nada de esto.

### Las abstenciones puras y la evidencia

Cruzando con `context_recall` por caso, las 8 abstenciones puras en gold:

| | n |
|---|---|
| `context_recall = 0` | 5 |
| `0 < recall < 0.5` | 2 |
| `recall >= 0.5` | **1** |

Es decir: **una sola** abstencion en 45 casos gold ocurrio con evidencia
razonable. Las 5 con `recall = 0` son correctas: no habia nada que usar.

### La recuperacion es el problema grande

17 de 45 casos gold tienen `context_recall = 0`:

| config | gold | `recall = 0` |
|---|---|---|
| A_denso | 45 | 17 |
| B_hybrid | 45 | 17 |
| C_rerank | 45 | 15 |
| una_pasada | 45 | 17 |

Hibrido y reranking no los mueven, asi que no es ranking. Estan repartidos
entre categorias (1 o 2 cada una), y 8 de esas categorias tienen solo 1 o 2
casos gold en total.

**Esto todavia no prueba que falten normas en el corpus.** `context_recall`
mide cobertura contra una respuesta de referencia, no suficiencia juridica: un
`recall = 0` puede ser que el corpus no la tenga, que la busqueda no la
encuentre, o que la metrica no reconozca evidencia que si sirve. Para
separarlo hay que comprobar, caso por caso, la norma esperada, si esta en el
corpus y en que posicion del ranking aparece.

Una muestra de los contextos recuperados sugiere que el problema es real: para
"renuncie por presion de mi jefe" (9002, `recall = 1.00`) los 5 fragmentos
fueron el articulo 342 del CST sobre prestaciones renunciables, el 18 del CPACA
sobre desistimiento, el 41 sobre agencia oficiosa y el 21 sobre funcionario sin
competencia. Solo uno servia. Que `recall` diera 1.00 ahi es otra razon para no
tratar esa metrica como prueba de suficiencia.

## Que arreglar

1. **Recuperacion** (17 casos sin evidencia): auditar norma esperada, presencia
   en el corpus y posicion en el ranking antes de tocar el corpus. La Ley 2466
   de 2025 sigue pendiente para lo laboral (`docs/m3_cobertura_corpus.md`).
2. **Las metricas publicadas**: `escape_en_gold = 0.60` y
   `escape_en_adversariales = 0.80` cuentan subcadenas. Los scorecards deben
   reportar abstencion pura aparte, y mostrar los denominadores:
   `faithfulness = 0.51` se promedia sobre `n = 18`, no sobre 45.
3. **Un solo caso de sobre-abstencion** en 45 gold no justifica tocar el
   entrenamiento. La comparacion base contra LoRA sigue valiendo, pero ya no
   para explicar un fallo masivo.

**No reentrenar.** El fallo que motivaba hacerlo no existe en la magnitud que
se creyo.

## Lo que sigue abierto

- **B2 en los ejemplos sinteticos: 0 de 35.** Ahi la frase no aparece ni una
  vez, asi que no es el fallo de medicion: con contextos que traen articulos
  bien formados pero de otra materia, el modelo cita en 25 de 35. Convive con
  lo de arriba y es el hallazgo que no se cayo.
- **B_hybrid** es la peor configuracion en la decision que importa, con la
  medicion por subcadena. Hay que recalcularlo con `es_abstencion_pura`.
