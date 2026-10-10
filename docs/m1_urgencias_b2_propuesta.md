# Los 12 objetivos de urgencia de B2: propuesta para validacion

> **FUERA DE ALCANCE desde el 2026-10-10.** Por decision de producto, las
> urgencias dejaron de ser una dimension de aceptacion de Amparo. Este documento
> **no describe un requisito vivo**: queda como el analisis hecho y como el
> instrumento listo si la decision se revierte. La consecuencia aceptada esta
> escrita en `docs/m1_protocolo_aceptacion.md`.

**Ninguno esta aprobado.** Son propuestas; cada una necesita el visto
bueno juridico antes de entrar al entrenamiento. El dataset v3 los dejo
fuera a proposito, y mientras no se validen sigue entrenando sin ellos.

## De donde sale cada propuesta

Cada uno es la variante B2 de un ejemplo B1 **que ya existe y paso las
puertas**. La respuesta de ese B1 tiene dos partes: una orientacion de
seguridad que **no depende de ninguna cita**, y una afirmacion juridica que
si depende. En B2 la segunda se sustituye por la frase de escape y la
primera sobrevive, porque una ruta institucional sigue siendo valida aunque
la busqueda no haya traido nada.

## Criterios de aceptacion (fijados antes de redactar)

| criterio | de donde viene |
|---|---|
| empieza con la frase de escape exacta | `es_valvula_de_escape` y el juez la buscan literal |
| ofrece al menos una ruta de ayuda inmediata | `AYUDA_INMEDIATA`; es el fallo por omision de 9130 y 9133 |
| la ruta NO va condicionada | `ayuda_condicionada`; es el fallo de 9132, cuyo criterio lo prohibe |
| no cita ningun articulo | puerta `cita en escape`: el contexto no respalda nada |
| no propone un tramite escrito como unico paso | `actuacion_diferida`; es el fallo de 9129 |
| 10-45 palabras | mismo rango que los demas B2 (`PALABRAS` de dataset_v2_quality) |

---

# Clase A -- la clausula se reutiliza tal cual (5 casos)

La ruta de ayuda aparece **sin condicionar** en el B1 original, asi que
pasa los criterios sin reescribir nada. Lo que se pide validar es que la
ruta siga siendo la correcta cuando se retira la parte juridica.

### 4009 — Penal basico y derechos de las victimas

**Pregunta:** Un familiar esta detenido y no sabemos donde lo tienen.

**Objetivo propuesto:** No tengo informacion verificada sobre esto en mi base de conocimiento. Pide ayuda urgente a la Defensoría del Pueblo o a la Personería.

**Criterios automaticos:** TODOS OK

**Validar:** [ ] la ruta es la correcta para esta situacion  [ ] no falta un paso inmediato

### 4205 — Prestamos informales y usura

**Pregunta:** El prestamista me amenaza con violencia si no pago.

**Objetivo propuesto:** No tengo informacion verificada sobre esto en mi base de conocimiento. Si estás en peligro, llama ya a la Línea 123 de la Policía. Guarda audios, mensajes y nombres de testigos, y denuncia ante la Fiscalía.

**Criterios automaticos:** TODOS OK

**Validar:** [ ] la ruta es la correcta para esta situacion  [ ] no falta un paso inmediato

### 4206 — Prestamos informales y usura

**Pregunta:** El prestamista me amenaza con quitarme mis bienes sin ningun proceso.

**Objetivo propuesto:** No tengo informacion verificada sobre esto en mi base de conocimiento. Si llega a tu casa o intenta llevarse tus cosas, llama a la Línea 123 de la Policía y denuncia ante la Fiscalía;

**Criterios automaticos:** TODOS OK

**Validar:** [ ] la ruta es la correcta para esta situacion  [ ] no falta un paso inmediato

### 4605 — Violencia intrafamiliar y medidas de proteccion

**Pregunta:** Me fui de la casa por la violencia y no tengo donde quedarme.

**Objetivo propuesto:** No tengo informacion verificada sobre esto en mi base de conocimiento. Si estás en la calle o en riesgo, llama a la Línea 123 o a la Línea 155. Pide esa medida en la Comisaría de Familia y que te remitan a tu EPS.

**Criterios automaticos:** TODOS OK

**Validar:** [ ] la ruta es la correcta para esta situacion  [ ] no falta un paso inmediato

### 4607 — Violencia intrafamiliar y medidas de proteccion

**Pregunta:** Mi expareja me esta amenazando de muerte por mensajes.

**Objetivo propuesto:** No tengo informacion verificada sobre esto en mi base de conocimiento. Ante una amenaza de muerte, llama a la Línea 123 si sientes peligro inmediato y denuncia en la Fiscalía con capturas de los mensajes. la Línea 155 te orienta.

**Criterios automaticos:** TODOS OK

**Validar:** [ ] la ruta es la correcta para esta situacion  [ ] no falta un paso inmediato

---

# Clase B -- hay que descondicionar la ruta (7 casos)

**No se propone un texto.** En estos la ruta va detras de una condicion
(*"si estas en riesgo, llama al 123"*). En un B1 eso es aceptable porque
la respuesta de fondo tambien se da; en un **B2** se retira el fondo, la
ruta queda como lo unico accionable, y condicionarla es **el fallo del caso
9132**, cuyo criterio lo prohibe expresamente.

Descondicionar una orientacion de seguridad -- decidir que la persona debe
llamar **ya**, no "si lo cree necesario" -- es una decision de producto con
revision juridica, no una operacion de texto. Por eso aqui va la clausula
original y la casilla vacia.

### 2105 — Salud / EPS

**Pregunta:** Necesito atencion psiquiatrica urgente y la EPS me da cita para dentro de dos meses.

**Clausula del B1 (condicionada):** Si hay riesgo de que se haga daño, vayan a urgencias o llamen a la Línea 123.

**Condicionada en:** urgencias, Línea 123

**Objetivo a redactar:** _(vacio a proposito)_

```
No tengo informacion verificada sobre esto en mi base de conocimiento. 
```

### 2411 — Relaciones laborales

**Pregunta:** Mi jefe me amenazo con despedirme si me afilio al sindicato.

**Clausula del B1 (condicionada):** si te sientes en peligro, acude a la Defensoría del Pueblo.

**Condicionada en:** Defensoría del Pueblo

**Objetivo a redactar:** _(vacio a proposito)_

```
No tengo informacion verificada sobre esto en mi base de conocimiento. 
```

### 2508 — Arriendo

**Pregunta:** Estoy en una situacion de violencia intrafamiliar y necesito salir del contrato de arriendo antes de tiempo.

**Clausula del B1 (condicionada):** Si estás en riesgo, llama a la Línea 155 o a la Línea 123 y acude a la Comisaría de Familia.

**Condicionada en:** Línea 155, Línea 123, Comisaría de Familia

**Objetivo a redactar:** _(vacio a proposito)_

```
No tengo informacion verificada sobre esto en mi base de conocimiento. 
```

### 2613 — Reporte en centrales de riesgo

**Pregunta:** Una empresa me amenaza con reportarme si no pago en 24 horas.

**Clausula del B1 (condicionada):** Si la presión incluye intimidaciones, acude a la Personería o a la Policía.

**Condicionada en:** Personería, Policía

**Objetivo a redactar:** _(vacio a proposito)_

```
No tengo informacion verificada sobre esto en mi base de conocimiento. 
```

### 4207 — Prestamos informales y usura

**Pregunta:** El prestamista me amenaza con denunciarme falsamente si no pago rapido.

**Clausula del B1 (condicionada):** Guarda los mensajes con la amenaza y, si te intimida o la cumple, denúncialo ante la Fiscalía; si temes por tu seguridad, llama a la Línea 123.

**Condicionada en:** Fiscalía, Línea 123

**Objetivo a redactar:** _(vacio a proposito)_

```
No tengo informacion verificada sobre esto en mi base de conocimiento. 
```

### 4219 — Prestamos informales y usura

**Pregunta:** El prestamista me amenaza con contarle a toda mi familia sobre la deuda.

**Clausula del B1 (condicionada):** Guarda los mensajes y, si la intimidación crece o temes por tu seguridad, denuncia ante la Fiscalía o llama a la Línea 123.

**Condicionada en:** Fiscalía, Línea 123

**Objetivo a redactar:** _(vacio a proposito)_

```
No tengo informacion verificada sobre esto en mi base de conocimiento. 
```

### 4617 — Violencia intrafamiliar y medidas de proteccion

**Pregunta:** Necesito que valoren mis golpes pero me da pena ir al medico.

**Clausula del B1 (condicionada):** si tienes heridas, ve a urgencias primero. Si hay riesgo, llama a la Línea 123, y la Línea 155 puede orientarte.

**Condicionada en:** urgencias, Línea 123, Línea 155

**Objetivo a redactar:** _(vacio a proposito)_

```
No tengo informacion verificada sobre esto en mi base de conocimiento. 
```

---

# Resumen

| clase | casos | que falta |
|---|---|---|
| A reutilizable | 5 | confirmar que la ruta sigue siendo la correcta |
| B descondicionar | 7 | redactar la orientacion sin condicion |
| **total** | **12** | |

Mientras no se validen, el entrenamiento corre **sin** estos 12. Son 12 de
2703 ejemplos: la perdida en masa de entrenamiento es despreciable y el
riesgo que se evita -- ensenar una abstencion peligrosa sobre una urgencia
-- es el peor del dataset.
