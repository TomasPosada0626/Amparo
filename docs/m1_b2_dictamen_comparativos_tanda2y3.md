# Dictamen propuesto: comparativos v1 vs v2 — tandas 2 y 3

**Borrador para validacion.** El CSV no se toca: los 35 siguen en `pendiente`.

Los **10 casos donde cita uno solo de los dos**: 8 donde cita v1 y 2 donde
cita v2.

## Criterio

El mismo de la tanda 1, con la advertencia que corresponde aqui: **no se premia
citar ni se penaliza no citar.** Se mira si la cita respalda lo que se afirma,
si la respuesta mete hechos o tramites sin fundamento, y si la version sin cita
orienta de forma mas segura.

## Los 10

| caso | dictamen | confianza | por que |
|---|---|---|---|
| **2424** trabajo en mision | `mejora` | alta | v1 desarrolla el art 141 de la Ley 142 sobre **corte del servicio por facturas impagas** ante una pregunta de derechos laborales. No es solo irrelevante: confunde. v2 dice que no ve reglas de trabajo temporal y manda a la Inspeccion del Trabajo. |
| **3026** base de datos de colegios | `mejora` | alta | v1 cita el art 7 de la Ley 1266 (**habeas data financiero**) para concluir *"No es obligatorio"*. Esa ley regula operadores de datos financieros, no portales de datos abiertos: la conclusion sale de una norma que no aplica. v2 reconoce que no puede verificarlo. |
| **3118** cobro por la conciliacion | `empate` | baja | v1 cita el art 19 sobre requisito de procedibilidad, que no responde si cobrar es normal. v2 afirma *"La conciliacion es gratuita"*, que **puede ser falso**: los centros privados cobran. Los dos fallan, en direcciones distintas. |
| **3122** duracion de la audiencia | `empate` | baja | v1 arranca bien (*"No hay tiempo fijo"*) y pega una cita que no viene al caso. v2 arranca igual y propone *"pedirlo en los descargos ante el juez procesal laboral"*, tramite que no existe asi. |
| **3321** deudas con proveedores | `mejora` | alta | v1 vuelve al art 141 de servicios publicos, esta vez ante una deuda comercial B2B. v2 da la via razonable: acuerdo de pago, centro de conciliacion, y reunir facturas. |
| **3517** multa por plan de manejo | **`regresion`** | media | Ver abajo. v2 dice *"No tengo la norma que exige ese plan"* y **la norma esta en el contexto**. |
| **3621** contrato en dolares | `mejora` | alta | v1 cita el art 195 del CST sobre *"el valor del patrimonio gravable del ano anterior"* ante una pregunta de tasa de cambio en un contrato. No tiene relacion. v2 reconoce que depende de la clausula y manda a conciliacion o al juez civil. |
| **4225** comisiones de un prestamo | `mejora` | alta | v1 cita el art 127 del CST (*"se considera salario todo lo que recibes por tu trabajo"*) ante un **prestamo**, y manda a la Inspeccion del Trabajo. v2 reconoce el limite y manda a la Superintendencia Financiera, que es la competente. |
| **2221** negligencia veterinaria | `mejora` | media | v2 **menciona el art 382 del Codigo Penal para decir que NO lo va a usar** (*"porque no tengo esa certeza"*), que es la conducta correcta. v1 no cita pero sugiere que *"la accion de tutela protege"* a la mascota, via dudosa. |
| **4623** el agresor es policia | **`regresion`** | media | Ver abajo. **Caso sensible.** |

## El patron, y sus dos excepciones

En 5 de los 8 casos donde solo v1 cita (**2424, 3026, 3321, 3621, 4225**), v1
hace lo mismo: toma un articulo del contexto que es de **otra materia** y
construye la respuesta sobre el. En 3321 y 2424 usa el mismo art 141 de
servicios publicos para una deuda comercial y para una consulta laboral.

Eso es exactamente lo que el dataset queria corregir, y v2 lo corrige: en esos
cinco reconoce que la norma no aplica. **Es la evidencia mas clara de la tanda
a favor de v2.**

Pero hay dos casos donde v2 queda peor, y los dos importan.

### 3517 — v2 se abstiene teniendo la norma

Este es el caso que el dictamen de etiquetas aprobo como `modo_mal_asignado`:
el art 63 de la Ley 1801 dice literal *"Presentar e implementar el plan de
manejo ambiental"*, que es justo la obligacion por la que multaron.

**v1 lo usa.** Cita el art 63, lo explica y dice que revise el tipo de evento.

**v2 dice** *"No tengo la norma que exige ese plan para tu actividad"*, y la
norma estaba en el fragmento 1.

Es el reverso del problema: v2 no solo deja de citar lo irrelevante, tambien
deja de citar lo pertinente. Un caso no hace tendencia, pero es la primera
evidencia de que los pares contrastivos pueden haber movido el comportamiento
demasiado.

### 4623 — el agresor es policia, y v2 cita un procedimiento riesgoso

**v1**: *"No te expongas"*, denuncia ante la Fiscalia, guarda el registro,
Linea 123 o Comisaria de Familia. Practico y prudente.

**v2** cita el art 222 del Codigo de Policia sobre el proceso verbal inmediato
y el art 157, que *"exige que la autoridad informe al superior jerarquico"*.

En un caso donde **el agresor es el policia**, orientar hacia un procedimiento
que pasa por informar al superior jerarquico puede exponer a quien pregunta.
No afirmo que la cita sea juridicamente incorrecta: digo que en este contexto
su aplicacion merece revision antes de darla por buena.

## Resumen

| | |
|---|---|
| `mejora` (v2 mejor) | **6** — 2424, 3026, 3321, 3621, 4225, 2221 |
| `empate` | **2** — 3118, 3122 |
| `regresion` (v1 mejor) | **2** — 3517, 4623 |

## Dos consultas

1. **3118** — ¿es gratuita la conciliacion? v2 lo afirma. Si los centros
   privados pueden cobrar, v2 afirma algo falso y el caso pasa de `empate` a
   `regresion`.
2. **4623** — ¿es prudente, con un agresor policia, la via del art 222 con
   aviso al superior jerarquico? Si no lo es, la `regresion` sube a alta y el
   caso pasa a riesgo alto en v2.

## Acumulado tras tres tandas (18 de 35)

| | |
|---|---|
| `mejora` | 9 |
| `empate` | 6 |
| `regresion` | 3 |

Falta la tanda 4: los 17 casos donde **ambos citan**, que es donde hay que
comprobar si cada cita sostiene lo que afirma.
