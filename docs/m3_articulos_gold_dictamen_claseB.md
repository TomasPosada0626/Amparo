# Dictamen propuesto: articulos gold, clase B' (candidatos a omision)

**Borrador para validacion.** No esta escrito en el CSV: las 190 filas no
adjudicadas siguen en `pendiente`.

Los **62 candidatos a omision** en 18 casos: articulos que el sistema **si
trajo** al top-5, de la norma correcta, y que **nadie etiqueto** como gold,
en casos que figuran como fallo. Si alguno responde, el fallo es falso.

Es el reverso de la clase A. Esa bajaba la linea base; esta la sube.

Texto leido de la metadata del indice evaluado
(`hash_metadata_indice = 8cd72136235d6dfe`, verificado).

## El efecto neto, que era la incognita

| | acierto@5 por articulo |
|---|---|
| Gold tal cual | 21 / 45 (47 %) |
| Depurando los `no_responde` de clase A | **17 / 45 (38 %)** |
| **Mas las 3 omisiones de esta clase** | **20 / 45 (44 %)** |

Las dos correcciones **se compensan casi del todo**. El 47 % original estaba
inflado; el 38 % estaba deprimido. La cifra defendible, con A y B' resueltas,
es **44 %**.

## Tres omisiones reales

Las tres convierten un fallo en acierto, y en las tres el articulo estaba en el
contexto que el modelo recibio.

### 9004 — *"mi EPS me autorizo una cirugia pero llevo 3 meses esperando"*

**Art. 10 de la Ley 1751**, literal a): derecho *"a acceder a los servicios y
tecnologias de salud, que le garanticen una atencion integral, **oportuna** y
de alta calidad"*. La consulta es exactamente una demora en el acceso. El gold
etiqueta los arts. 2 y 6 de la misma ley, que no se recuperaron.

`responde`, confianza **alta**.

### 9009 — *"me dijeron que el contrato es confidencial, ¿pueden negarse asi como asi?"*

**Art. 21 de la Ley 1712**: *"En aquellas circunstancias en que la totalidad de
la informacion contenida en un documento no este protegida por una excepcion
[...] **debe hacerse una version publica** que mantenga la reserva unicamente de
la parte indispensable."* Responde la pregunta de forma directa: no, no pueden
negarse en bloque.

`responde`, confianza **alta**.

### 9066 — *"mi vecino amplio su casa invadiendo el antejardin y la alcaldia no responde"*

**Art. 79 de la Ley 1801**: *"Ejercicio de las acciones de proteccion de los
bienes inmuebles [...] podran instaurar querella ante el inspector de
Policia"*. Es la via concreta ante una perturbacion, y el unico candidato del
caso.

`responde`, confianza **alta**.

## Un hallazgo que no venia a buscar: 142 chunks que solo dicen "Derogado"

Leyendo el caso 9058 aparecio esto, y es el defecto mas barato de corregir de
toda la auditoria.

**El 1.2 % del indice (142 de 11 975 chunks) tiene como contenido completo una
derogatoria**: *"Articulo 226. Derogado"*. No pueden responder nada, y **ocupan
sitio en el top-5**: 14 de ellos llegaron al contexto final en **7 de los 45
casos gold**.

El caso 9058 es el extremo. *"Expulsaron a mi hijo del colegio por un video que
circulo, sin llamarnos a nosotros antes"*:

| score | fragmento entregado al modelo |
|---|---|
| 0.8328 | Ley 1620, art. 2 (definiciones) |
| 0.8326 | **Ley 115, art. 172 — "Derogado"** |
| 0.8300 | **Ley 115, art. 82 — "Derogado"** |
| 0.8276 | **Ley 115, art. 134 — "Derogado"** |
| 0.8273 | **Ley 115, art. 149 — "Derogado"** |

**Cuatro de los cinco fragmentos eran la palabra "Derogado".** Y el caso 9005
(el del celular, que acierta) gasta tambien un sitio en el art. 80 de la Ley
1480, derogado.

Por norma: Codigo Civil 62, Codigo de Comercio 29, CST 9, Ley 115 7, Codigo
Penal 6, Ley 80 6.

Es un defecto de **ingesta**, no de corpus: los `.md` registran correctamente
que el articulo fue derogado, y esa informacion es legitima en el texto. Lo que
no tiene sentido es indexarla como fragmento recuperable.

| | |
|---|---|
| Correccion | excluir al ingerir los chunks cuyo contenido sea solo una derogatoria |
| Archivos | `tools/rag/chunk.py` o `tools/rag/ingest.py` |
| Impacto | libera 14 sitios del top-5 en 7 de 45 casos |
| Riesgo | bajo, pero hay que acotar el patron: un articulo **parcialmente** derogado si tiene texto util y no debe excluirse |
| Prueba de aceptacion | 0 chunks-derogatoria en el indice; `n_chunks` baja en ~142; ninguna categoria que hoy esta en 0.83-1.00 baja |
| Dependencia | requiere reindexar, asi que entra en la **unica** reconstruccion |

## Los 62, por caso

`no_responde` cuando el articulo es de otra materia o no toca la pregunta;
`responde_parcial` cuando aporta una pieza real pero no resuelve.

| caso | consulta | candidatos y veredicto |
|---|---|---|
| **9004** salud, demora de cirugia | | **art. 10 Ley 1751 `responde` alta** · art. 17 D.2591 (correccion de la solicitud de tutela) `no_responde` alta |
| **9007** usura | *"¿como se si es usura?"* | art. 1163 C.Co (presuncion y pago de intereses comerciales) `responde_parcial` media -- fija la tasa de referencia, no el limite · arts. 2172 (mandatario), 2234 (presuncion de pago), 2309 (agencia oficiosa) del C.C. `no_responde` alta |
| **9009** informacion confidencial | | **art. 21 Ley 1712 `responde` alta** · art. 9 Ley 1712 (informacion minima proactiva) `responde_parcial` media · arts. 141 (controversias contractuales) y 217 (confesion de representantes) CPACA `no_responde` alta |
| **9010** conciliacion previa | | art. 526 CGP (vinculacion de socios) `no_responde` alta |
| **9035** deposito no devuelto | | art. 8 Ley 820 (obligaciones del arrendador) `no_responde` media -- no trata depositos · arts. 15, 22, 23, 25 `no_responde` alta |
| **9038** contratista con horario y jefe | | art. 43 CST (clausulas ineficaces) `responde_parcial` media -- sirve al contrato realidad, que es el gold (arts. 23 y 24) · arts. 48 (clausula de reserva), 140 (salario sin prestacion) `no_responde` alta |
| **9039** deuda pagada hace 6 años | | art. 16 Ley 1266 (peticiones y reclamos) `responde_parcial` media · arts. 14 (contenido de la informacion), 19-A (responsabilidad demostrada) `no_responde` media |
| **9041** embargo de cuenta de nomina | | arts. 65 (indemnizacion por falta de pago), 290 (nomina para seguro colectivo), 393 (libros del sindicato), 433 (iniciacion de conversaciones) del CST: **los cuatro `no_responde` alta** |
| **9043** zapatos por internet | *"no me gustaron"* | art. 51 Ley 1480 (reversion del pago) `responde_parcial` media -- la reversion opera por no entrega o defecto, no por arrepentimiento; el gold es el art. 47, retracto · art. 50 (deberes en comercio electronico) `responde_parcial` baja · art. 58 (procedimiento) `responde_parcial` baja · art. 18 (entrega de bien para servicio) `no_responde` alta |
| **9046** peticion a telefonia sin respuesta | | arts. 16 (contenido de las peticiones) `no_responde` media · 21 (funcionario sin competencia), 225 (llamamiento en garantia) `no_responde` alta |
| **9050** cheque sin fondos | | arts. 714 (provision de fondos), 720 (banco obligado hasta el saldo), 721 (pago dentro de seis meses) C.Co `responde_parcial` media -- describen la relacion librador-banco, no la accion del tenedor, que es el gold · arts. 724 (revocacion), 728 (devolucion de cheques pagados) `no_responde` alta |
| **9056** embargo con cedula parecida | | art. 593 CGP (como se efectuan los embargos, con los datos de inscripcion) `responde_parcial` media · arts. 468 (garantia real), 598 (familia) `no_responde` alta · art. 599 `no_responde` media |
| **9057** codeudor embargado sin aviso | | art. 593 `responde_parcial` media · art. 470 `no_responde` media · art. 468 `no_responde` alta |
| **9058** expulsion del colegio | | art. 2 Ley 1620 (definiciones) `no_responde` media · **arts. 82, 134, 149, 172 de la Ley 115: los cuatro son chunks cuyo texto completo es "Derogado"** -- `no_responde` **alta**, y ver el hallazgo de arriba |
| **9060** actas de obras no hechas | | arts. 4 (derechos y deberes de las entidades) `no_responde` media · 25 (principio de economia), 32 (contratos estatales) `no_responde` alta |
| **9063** pension menor a lo calculado | | arts. 33 (requisitos de pension de vejez), 35 (pension minima), 117 (valor de los bonos pensionales) `responde_parcial` media -- los tres rozan el calculo, que es el gold (arts. 21 y 34) · art. 14 (reajuste) `no_responde` media · art. 27 (recursos del fondo) `no_responde` alta |
| **9066** antejardin invadido | | **art. 79 Ley 1801 `responde` alta** |
| **9068** el abogado no apelo a tiempo | | art. 321 CGP (procedencia de la apelacion) `responde_parcial` media · art. 352 (recurso de queja) `responde_parcial` media -- pertinente si la apelacion se denego, no si no se interpuso · art. 159 (interrupcion del proceso) `no_responde` alta |

## Reparto

| | |
|---|---|
| `responde` | **3** |
| `responde_parcial` | **16** |
| `no_responde` | **43** |

## Lo que esto dice del etiquetado original

El 69 % de los candidatos no responde, asi que **el gold no es laxo: es
exigente**, y en general bien hecho. Las tres omisiones no son descuido
sistematico sino tres casos concretos.

Pero si dice algo del **sistema**: en 9041 los cuatro articulos del CST que se
recuperaron son de otra materia (indemnizacion por despido, libros
sindicales, negociacion colectiva) ante una pregunta de inembargabilidad del
salario, con los arts. 154-156 sin recuperar. No es un problema de gold.

## Lo que pedimos a Leonardo

1. **Las tres `responde`** (9004 art. 10, 9009 art. 21, 9066 art. 79). Cada una
   convierte un fallo en acierto y por tanto sube la linea base.
2. **9043**: ¿la reversion del pago del art. 51 cubre el arrepentimiento, o solo
   la no entrega y el defecto? Si lo cubriera, pasaria a `responde`.
3. **9038**: ¿sirve el art. 43 del CST para el contrato realidad, o la via es
   solo el art. 23?
4. **9068**: ¿el recurso de queja del art. 352 sirve cuando el apoderado **no
   interpuso** la apelacion, o solo cuando se le denego?
5. Lo que no pueda establecerse con certeza, **en `pendiente`**.

## Alcance

Esto no valida las otras dos clases: quedan 82 etiquetas de clase B y 46 de
clase C. El CSV conserva las 190 en `pendiente`. No se toco el corpus, el
chunker, el indice ni el dataset, y 6.1 sigue sin ejecutarse.
