# Dictamen propuesto: articulos gold, clases B y C

**Borrador para validacion.** El CSV conserva las 190 filas no adjudicadas en
`pendiente`.

Las **82 etiquetas de clase B** (casos que fallaron) y las **46 de clase C** (el
caso ya acerto por otro articulo). Son las de menor impacto sobre el acierto@k
-- ninguna lo mueve por si sola -- y por eso van al final. Pero cierran el gold
y dicen algo sobre su calidad.

## El resultado: el gold esta bien hecho

| clase | `responde` | `responde_parcial` | `no_responde` |
|---|---|---|---|
| B (82) | **64** | 15 | 3 |
| C (46) | **38** | 8 | 0 |
| **total** | **102** | **23** | **3** |

El **80 %** de las etiquetas de estas dos clases responde la consulta, y solo 3
de 128 no responden. Junto con el 69 % de `no_responde` en la clase B', el
cuadro completo es coherente: **quien etiqueto el gold sabia lo que hacia.**

Eso tiene una consecuencia que conviene dejar escrita: **el problema no es el
etiquetado, es la recuperacion.** Las clases A y B' corrigieron 4 aciertos
falsos y 3 omisiones -- 7 filas de 217, el 3 % -- y el resto se sostiene.

Los ejemplos mas claros, donde el articulo gold responde la pregunta de forma
casi literal y **no se recupero**:

| caso | consulta | gold que no llego |
|---|---|---|
| 9035 | *"el arrendador no me devuelve el deposito"* | Ley 820 art. 16: **"Prohibicion de depositos y cauciones reales"** |
| 9038 | *"contratista con horario fijo y jefe directo"* | CST arts. 23 y 24: elementos esenciales y **presuncion** de contrato de trabajo |
| 9041 | *"me embargaron la cuenta de nomina"* | CST art. 154: **"No es embargable el salario minimo"**; CGP art. 594 |
| 9042 | *"fotomulta de hace casi un año"* | Ley 769 art. 161: **"La accion por contravencion caduca al año"** |
| 9043 | *"compre unos zapatos por internet y no me gustaron"* | Ley 1480 art. 47: **Retracto** |
| 9049 | *"vendo ropa por Instagram, ¿registro en Camara de Comercio?"* | C.Co arts. 10, 13, 19, 26, 28: quien es comerciante y el deber de matricularse |
| 9007 | *"¿como se si es usura?"* | C.C. art. 2231, C.Co art. 884 (**limite de intereses**), C.P. art. 305 (**usura**) |
| 9009 | *"me dijeron que es confidencial"* | Ley 1712 art. 28: **carga de la prueba** del sujeto obligado |
| 9056 | *"el nombre y la cedula no son los mios"* | CGP art. 597: **levantamiento del embargo** |
| 9048 | *"me estafaron en una compra por internet"* | C.P. arts. 246 (estafa) y 269-J (transferencia no consentida) |

En cada uno de esos diez, un ranking que hubiera traido el articulo correcto
habria cambiado la respuesta. Es la mejor evidencia de que el trabajo esta en la
recuperacion.

## Las tres `no_responde`

| caso | articulo | por que |
|---|---|---|
| 9033 | Ley 361 art. 26 | *"estoy incapacitado por una cirugia y me despidieron"*. El art. 26 prohibe que **la discapacidad** obstaculice una vinculacion laboral. Una incapacidad temporal por cirugia no es lo mismo que una discapacidad, y la estabilidad laboral reforzada en incapacidad tiene otro fundamento. `no_responde`, confianza **media**: es el mas discutible de los tres y conviene que lo vea el abogado. |
| 9060 | C.P. art. 286 | *"me piden firmar actas de obras que no se han hecho"*. La falsedad ideologica en documento publico es del **servidor publico** que extiende el documento; quien pregunta es el contratista al que se lo piden firmar. El supuesto es cercano pero no es el suyo. `no_responde`, confianza media. El art. 287 (falsedad en documento privado) si encaja mejor y tambien esta etiquetado. |
| 9004 | D. 2591 art. 1 | *"llevo 3 meses esperando la cita"*. El art. 1 es el **objeto** de la tutela y repite el art. 86 de la Constitucion. No aporta nada que el 86 no diga, y ninguno de los dos resuelve la demora. `no_responde`, confianza baja -- es redundancia, no error. |

## Las 15 + 8 `responde_parcial`

El patron es el mismo en casi todas: el articulo da **el derecho** o **la via**,
pero no las dos cosas, y el gold etiqueta las dos piezas por separado. No es un
defecto del etiquetado: la regla del archivo es que basta traer **uno** de los
articulos.

Ejemplos: en 9004, los arts. 13 y 14 del CPACA dan los terminos del derecho de
peticion, que es el vehiculo, no el derecho a la cita; en 9010, el art. 90 del
CGP regula la admision de la demanda y los arts. 67, 68, 70 y 71 de la Ley 2220
son los que resuelven el requisito de procedibilidad; en 9036, los arts. 159 y
160 del CST definen el trabajo suplementario y el nocturno, y el 168 pone las
tasas.

## Tres cosas que aparecieron de paso

### 1. El caso 9051 no se puede responder bien ni con recuperacion perfecta

Su gold de clase C incluye el **art. 57 del CST**, que es el articulo cuya
version indexada es anterior a la reforma de 2025 (hallazgo H6 de la auditoria
integral). La consulta es *"mi jefe me paso a turnos de noche de un dia para
otro y yo tengo un hijo de dos años"*.

Es el **segundo** caso en esta situacion, despues del 4630 de B2. No es
coincidencia: los dos son laborales, que es la categoria mas frecuente. Refuerza
que la actualizacion del art. 57 es la correccion de corpus con mas respaldo.

### 2. El articulo 292 del CGP es gold en 9057 y `no_responde` en 9069

Puede parecer una contradiccion y no lo es. En **9057** (*"me embargaron sin
avisarme nada antes"*) el regimen de notificaciones es exactamente lo que se
discute, y el 292 -- la notificacion por aviso -- forma parte de el. En **9069**
(*"me notificaron por un correo que yo nunca autorice"*) lo que se discute es si
ese canal era valido, y eso lo resuelve el 291.

El mismo articulo responde una consulta y no la otra. Lo anoto porque un
revisor que compare las dos filas sin leer las preguntas lo leeria como un
error.

### 3. Los articulos 154 y 155 del CST comparten chunk

En 9041 los dos renderizan el mismo texto, que empieza en el encabezado del
154. Es el caso `FUSIONADO` del anexo de chunking: dos articulos en un solo
chunk. Para el gold da igual -- traer ese chunk acierta los dos -- pero es un
dato mas sobre la granularidad.

## Lo que pedimos a Leonardo

1. **9033**: ¿el art. 26 de la Ley 361 cubre una incapacidad temporal por
   cirugia, o la estabilidad laboral reforzada en incapacidad tiene otro
   fundamento? Es la mas discutible de las tres `no_responde`.
2. **9060**: ¿la falsedad ideologica del art. 286 alcanza al contratista al que
   le piden firmar, o solo al servidor publico que extiende el documento?
3. Confirmar que los diez casos de la tabla de arriba estan bien etiquetados.
   Si alguno no lo esta, el diagnostico de "el problema es la recuperacion"
   pierde fuerza en esa medida.
4. Lo que no pueda establecerse con certeza, en `pendiente`.

## Estado del gold tras las cuatro clases

| clase | filas | dictaminada | aprobada |
|---|---|---|---|
| A | 27 | si | **si**, 2026-10-10 |
| B' | 62 | si | no |
| B | 82 | si | no |
| C | 46 | si | no |

El acierto@5 por articulo con A y B' resueltas es **20/45 (44 %)**. Las clases B
y C **no lo mueven**: ninguna de sus filas es el unico punto de acierto de su
caso, por definicion de las clases.

No se toco el corpus, el chunker, el indice ni el dataset. 6.1 sigue sin
ejecutarse.
