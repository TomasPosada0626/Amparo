# Dictamen propuesto: articulos gold, clase A

**Borrador para validacion.** El CSV
`docs/m3_articulos_gold_validacion.csv` conserva las 217 filas en `pendiente`.

Las **27 etiquetas de clase A**: aquellas donde el sistema **si** trajo el
articulo gold y por eso el caso cuenta como acierto. Si una esta mal asignada,
el acierto es falso, y mediriamos cualquier mejora futura contra una linea base
inflada. Es el riesgo mas caro de los cuatro, y por eso va primero.

Texto de los articulos leido de la metadata del indice evaluado en S08 y S10
(`hash_metadata_indice = 8cd72136235d6dfe`, verificado), uniendo los chunks de
cada articulo. La matriz con el texto completo esta en
`docs/m3_articulos_gold_matriz.md`.

## Antes de nada: una correccion de alcance

El informe de auditoria hablaba de **53 observaciones** de articulo. Eso era el
numero de **fallos**, no el total de etiquetas. El archivo tiene:

| | |
|---|---|
| Casos etiquetados | 45 |
| Pares (caso, norma) | 75 |
| **Observaciones (caso, norma, articulo)** | **155** |
| Candidatos a omision detectados | 62 |
| **Total de filas a revisar** | **217** |

## La regla aplicada

La del propio archivo: *"un caso cuenta como acierto si la busqueda trae al
menos uno de sus articulos."* De ahi la pregunta de esta clase:

> ¿El articulo **responde** la consulta, o solo **toca el tema**?

- `responde` -> por si solo permite orientar la consulta.
- `responde_parcial` -> aporta una pieza necesaria (el derecho, la tarifa, la
  via) pero no resuelve lo que se pregunta.
- `no_responde` -> tematicamente cercano, no resuelve. **El acierto es falso.**

Para medir acierto@k, `responde` y `responde_parcial` cuentan igual: el sistema
trajo algo util. La distincion importa para interpretar el 47 %, no para
calcularlo.

## Las 27

| caso | norma · art | veredicto | conf | por que |
|---|---|---|---|---|
| **9001** arriendo subido al doble | Ley 820 · 20 | `responde` | alta | Reajuste del canon con tope del 100 % del IPC del año anterior. Exacto. |
| **9002** renuncia por presion | CST · 62 | `responde_parcial` | media | El literal B) da las justas causas del trabajador, que es la base de la renuncia motivada. Pero *"¿puedo reclamar algo?"* se responde con el art. 64 (indemnizacion), que no esta etiquetado. |
| **9005** celular de 8 meses | Ley 1480 · 8 | `responde` | alta | *"el termino sera de un año para productos nuevos"*. Resuelve el caso. |
| **9005** | Ley 1480 · 11 | `responde` | alta | Que cubre la garantia: reparacion gratuita, reposicion o devolucion. |
| **9005** | Ley 1480 · 58 | `responde_parcial` | media | Es la via procesal ante la SIC, no si la garantia cubre. |
| **9031** pago previo en urgencias | Ley 100 · 168 | `responde` | alta | *"independientemente de la capacidad de pago... no requiere contrato ni orden previa"*. Exacto. |
| **9032** EPS niega tratamiento | Ley 1751 · 10 | `responde_parcial` | media | Da el derecho de acceso integral. Lo que decide las exclusiones es el art. 15, que no esta etiquetado. |
| **9034** desalojo en una semana | Ley 820 · 22 | `responde` | alta | Lista las causales de terminacion por el arrendador, y *"quiere el apartamento"* no esta entre ellas. Responde por exclusion. |
| **9036** horas extra sin pagar | CST · 168 | `responde_parcial` | media | Da los recargos (25 %, 75 %), o sea cuanto se debe. El *"¿que puedo hacer?"* no esta cubierto. |
| **9037** jefe grita y humilla | Ley 1010 · 2 | `responde` | alta | Definicion de acoso laboral. Exacto. |
| **9037** | Ley 1010 · 7 | `responde` | alta | *"se presumira que hay acoso si se acredita la ocurrencia repetida y publica"*, incluidas las expresiones ultrajantes. Encaja con el hecho descrito. |
| **9040** SOAT no cubre | Ley 769 · 42 | **`no_responde`** | media | **Ver abajo.** |
| **9044** aumentar cuota de alimentos | Ley 1098 · 111 | `responde_parcial` | media | Reglas de **fijacion** de la cuota, incluida la citacion a conciliacion. El aumento es una revision por cambio de circunstancias. |
| **9044** | Ley 1098 · 129 | `responde_parcial` | media | Cuota **provisional** en el auto de traslado. Pieza del procedimiento, no la respuesta. |
| **9045** tutela contra un banco | C.P. · 86 | `responde_parcial` | alta | Funda la tutela, pero el inciso que la abre a particulares esta al final del articulo; lo que el chunk destaca es *"cualquier autoridad publica"*. Por si solo no resuelve *"¿aunque sea privada?"*. |
| **9045** | Decreto 2591 · 42 | `responde` | alta | *"procedera contra acciones u omisiones de particulares en los siguientes casos"*. Es exactamente la pregunta. |
| **9051** turnos de noche de un dia para otro | CST · 161 | **`no_responde`** | media | **Ver abajo.** |
| **9052** deuda pagada, reportada de nuevo | Ley 1266 · 13 | `responde` | alta | Permanencia de la informacion y termino maximo. Es el nucleo del caso. |
| **9053** deuda de la empresa, no mia | Ley 1266 · 16 | `responde_parcial` | media | Da el tramite de peticiones y reclamos, o sea el camino. No resuelve a quien se atribuye la deuda. |
| **9054** choque con nota del conductor | Ley 769 · 144 | `responde_parcial` | media | Informe policial cuando no hay conciliacion. Util pero lateral a *"¿que hago con la nota?"*. |
| **9054** | Ley 769 · 149 | **`no_responde`** | media | **Comprobado a peticion del abogado: no es duplicado.** Ver abajo. |
| **9059** penalidad no mostrada | Ley 1480 · 43 | `responde` | alta | Clausulas abusivas ineficaces de pleno derecho. Encaja directo. |
| **9061** ruido del vecino con permiso ambiental | Ley 1801 · 33 | `responde` | alta | Perturbar el sosiego con ruidos. Exacto, y el permiso ambiental no lo excusa. |
| **9064** respuesta incongruente de la alcaldia | CPACA · 21 | **`no_responde`** | media | **Ver abajo.** |
| **9065** competidor registro nombre parecido | Decision 486 · 136 | `responde` | alta | Irregistrabilidad por semejanza y riesgo de confusion. |
| **9067** distribuidor rompe exclusividad | C.Co. · 1318 | `responde` | alta | *"el empresario no podra servirse de varios agentes en una misma zona"*. Exacto. |
| **9069** notificado por correo no autorizado | CGP · 292 | **`no_responde`** | media | **Ver abajo.** |

## Las cuatro que pueden ser aciertos falsos

Las cuatro son el **unico** punto de acierto de su caso: si no responden, el
caso pasa a fallo. Comprobado.

| | acierto@5 por articulo |
|---|---|
| Hoy | **21 / 45 (47 %)** |
| Si las cuatro no responden | **17 / 45 (38 %)** |

### 9040 — *"el hospital dice que el SOAT no cubre mis gastos"*

El art. 42 dice que todo vehiculo debe estar amparado por un seguro obligatorio
y que *"el SOAT se regira por las normas actualmente vigentes o aquellas que lo
modifiquen o sustituyan"*. Establece la obligatoriedad y **remite** a otras
normas para el contenido. No dice que cubre ni hasta cuanto, que es lo que se
pregunta. El otro gold del caso es el art. 167 de la Ley 100, que **esta
partido en 2 chunks** y no se recupero.

### 9051 — *"me paso a turnos de noche de un dia para otro y tengo un hijo de dos años"*

El art. 161 regula la **duracion** de la jornada (42 horas semanales). La
consulta es sobre el cambio unilateral del horario y los limites del *ius
variandi* cuando hay cuidado de un menor. Comparte la palabra "jornada" y poco
mas.

### 9064 — *"me respondieron algo que no tiene nada que ver con lo que pregunte"*

El art. 21 del CPACA es **funcionario sin competencia**: que hacer cuando la
peticion se dirige a quien no es competente. La consulta es una respuesta
**incongruente** de la autoridad competente, que es otra cosa. Lo pertinente
seria el deber de resolver de fondo. El otro gold del caso es el art. 23 de la
Constitucion, que si se recupero segun el registro -- conviene que Leonardo
revise si ese basta por si solo.

### 9069 — *"me notificaron por un correo electronico que yo nunca autorice"*

El art. 292 es **notificacion por aviso**, el mecanismo subsidiario cuando no
se logra la personal. La consulta es sobre notificacion electronica a un correo
no autorizado, que se rige por el art. 291 y por el regimen de notificaciones
electronicas. Mismo capitulo, articulo equivocado -- y es justo el patron de
vecindad que documento el anexo de chunking.

## Reparto

| | |
|---|---|
| `responde` | **13** |
| `responde_parcial` | **9** |
| `no_responde` | **5** |

Correccion a la primera version de este dictamen: su resumen decia 12 / 11 / 4.
Las filas individuales sumaban 13 / 10 / 4 -- fue un error de aritmetica en la
tabla de resumen, no en los veredictos. Con el cambio de 9054 queda 13 / 9 / 5.

Que 11 de 27 sean `responde_parcial` no invalida nada para el calculo del
acierto@k, pero si dice algo sobre el etiquetado: en varios casos el articulo
que **resolveria** la consulta no esta etiquetado (el art. 64 del CST en 9002,
el art. 15 de la Ley 1751 en 9032, el art. 23 del CPACA en 9064). Son
omisiones candidatas, y si se agregan, el gold se vuelve mas exigente, no menos.

## Las dos comprobaciones que pidio el abogado

### Ley 769, articulos 144 y 149: no hay duplicado

Tienen redaccion casi igual -- 56 % de similitud literal, y las dos listan el
mismo contenido minimo del informe -- pero **ambitos distintos**, y la
diferencia esta en su primera linea:

- El **144** aplica *"en los casos en que no fuere posible la conciliacion entre
  los conductores"*, y viene inmediatamente despues del **143**, que regula los
  **daños materiales**.
- El **149** aplica *"en los casos a que se refiere el articulo anterior"*, y el
  anterior es el **148: Funciones de Policia Judicial**, para *"hechos que
  puedan constituir infraccion penal"*.

Es el mismo formulario para dos situaciones juridicas distintas. **No infla el
gold por duplicacion**, pero si cambia el dictamen: el caso 9054 es un choque
contra un carro parqueado, sin lesiones, asi que el supuesto penal del 149 no
aplica y pasa a `no_responde`.

El caso no deja de acertar: el 144 si aplica. Y vale notar que el articulo que
**resolveria** la consulta es el **143** -- en daños materiales el material
probatorio de las partes *"reemplazara el informe policial"*, que es justo el
valor de la nota con el numero --, esta etiquetado como gold y **no se
recupero**.

### CGP, articulos 291 y 292: no son intercambiables

- El **291** regula la practica de la notificacion personal e incluye el regimen
  de la direccion electronica: *"deberan registrar, ademas, una direccion
  electronica. Esta disposicion tambien se aplicara a las personas naturales que
  **hayan suministrado al juez** su direccion de correo electronico."* Eso es
  exactamente lo que discute el caso 9069.
- El **292** es la notificacion **por aviso**, remitido *"a traves de servicio
  postal autorizado"*, para cuando la personal no se pudo hacer.

Se confirma `no_responde`. Una nota metodologica: buscar palabras clave no sirve
para distinguirlos -- las dos disposiciones mencionan "electronico" y "correo",
porque el 292 remite al numeral 3 del 291. Lo que decide es el ambito de
aplicacion, leido.

## Validacion

**Clase A aprobada por Leonardo Galeano (abogado) el 2026-10-10**, con las dos
comprobaciones de arriba hechas a su peticion. Su aprobacion **cubre solo la
clase A**: no valida las 190 filas restantes.

## Lo que pedimos a Leonardo

1. **Las cuatro `no_responde`**, por orden de impacto. Cada una convierte un
   acierto en fallo.
2. **9054**: ¿los articulos 144 y 149 de la Ley 769 son el mismo contenido? Si
   lo son, hay un duplicado que infla el gold.
3. **9045**: ¿el art. 86 de la Constitucion, por si solo, responde si la tutela
   procede contra un particular? Propongo `responde_parcial`; si fuera
   `responde`, no cambia el acierto porque el art. 42 del Decreto 2591 ya
   acierta.
4. Si una no se puede resolver con certeza, **dejarla en `pendiente`**. Un gold
   dudoso marcado como dudoso es informacion; forzado, es un diagnostico
   equivocado del sistema de recuperacion.

## Lo que esto no decide

Nada sobre las otras tres clases: 62 candidatos a omision (clase B'), 82
etiquetas de casos fallidos (B) y 46 redundantes (C). Y nada sobre el
chunker, el corpus ni el indice, que siguen sin tocarse.
