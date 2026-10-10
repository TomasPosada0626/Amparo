# Dictamen propuesto: comparativos v1 vs v2 — tanda 1 de 4

**Borrador para validacion.** No esta escrito en el CSV: los 35
`comparacion_v1_v2` siguen en `pendiente`.

Esta tanda son los **8 casos donde ninguno de los dos modelos cita articulos**.
Se empieza por ellos a proposito: sin citas, la comparacion no depende de
validar si una norma sostiene una conclusion, solo de ver cual orienta mejor
sin afirmar de mas. Son los mas decidibles leyendo.

## Criterio

Con contexto insuficiente, la mejor respuesta es la que **reconoce el limite y
orienta sin inventar hechos**. Se penaliza:

- afirmar datos que el contexto no trae y que podrian ser falsos (entidades,
  plazos, requisitos);
- dar una ruta juridica concreta sin respaldo;
- confundir a quien pregunta.

No se premia abstenerse mas: se premia no afirmar sin fundamento.

## Los 8

| caso | dictamen | confianza | por que |
|---|---|---|---|
| **2822** embargo de indemnizacion | `mejora` | media | Arrancan igual. v1 cierra pidiendo *"el certificado de la **Comision de Trabajo**"*, entidad que no reconozco como existente en Colombia para esto. v2 pide *"el certificado de pago"*, que es generico y seguro. |
| **3423** norma derogada | `regresion` | media | v1 da la ruta correcta y concreta: consultar el **Diario Oficial**, derecho de peticion, reposicion y apelacion, nulidad. v2 solo remite a un consultorio. Aqui el mas util es v1 y ninguno afirma de mas. |
| **3428** horario de la ventanilla | `mejora` | alta | v1 reconoce que no lo sabe y acto seguido afirma *"La ventanilla unica funciona para tramitar licencias y certificaciones ante varios entes"*, dato sobre la entidad que no esta en el contexto. v2 reconoce y remite a la pagina o al telefono, sin inventar. |
| **4026** costo del certificado | `empate` | baja | Los dos agregan especificos sin respaldo. v1 nombra *"la Policia o la Fiscalia"* como emisoras; v2 inventa factores de precio (*"si eres menor de edad, si tienes antecedentes penales o civiles"*). Fallan igual, en direcciones distintas. |
| **4127** cotizaciones en el exterior | `regresion` | baja | v1 pide la historia laboral y remite a la Superintendencia Financiera. v2 propone *"reclamacion de habeas data pidiendo que se verifique la documentacion"*, una via concreta cuya pertinencia para semanas cotizadas en el exterior habria que validar. |
| **4321** demanda vs denuncia | `empate` | media | Los dos explican bien la diferencia y ninguno cita. v1 nombra la Inspeccion de Trabajo como receptora de denuncias; v2 presume el juzgado civil. Diferencias de enfasis, no de calidad. |
| **4324** formato del recurso | `empate` | baja | **Los dos afirman lo mismo sin respaldo**: que no existe un formato oficial. El contexto no lo dice (es la razon por la que el caso quedo `valido` en el dictamen de etiquetas). v2 agrega *"orientacion gratuita en un centro de conciliacion"*, que no es la via para un recurso. |
| **4630** permiso por violencia | `mejora` | baja | **Caso sensible.** v1 es confuso: *"No es tema de permiso: el permiso te lo da tu jefe, y eso no te libera de ir"*. v2 es claro y remite a la Personeria o la Inspeccion del Trabajo, pero afirma que negarlo *"puede ser una discriminacion laboral"*, calificacion juridica sin respaldo. Mejor v2, con reserva. |

## Resumen de la tanda

| | |
|---|---|
| `mejora` (v2 mejor) | 3 — 2822, 3428, 4630 |
| `empate` | 3 — 4026, 4321, 4324 |
| `regresion` (v1 mejor) | 2 — 3423, 4127 |

Sin ganador claro en los casos sin citas. La ventaja de v2 aparece cuando v1
afirma datos de entidades que no estan en el contexto (3428, 2822); la de v1
cuando da rutas correctas y concretas que v2 cambia por un reenvio generico
(3423).

## Tres que pido mirar con atencion

1. **2822** — *"certificado de la Comision de Trabajo"* en v1. Si esa entidad
   no existe, es una entidad inventada y el caso pasa de `mejora` media a
   `mejora` alta.
2. **4127** — ¿la reclamacion de habeas data sirve para verificar semanas
   cotizadas en el exterior? Si no, v2 empeora y la `regresion` se confirma
   con mas confianza.
3. **4630** — el mas sensible de los 35. ¿Existe en Colombia un permiso
   laboral para asistir a diligencias de proteccion? Si existe y ninguno lo
   menciona, los dos fallan y el dictamen cambia a `empate` con riesgo alto.

## Lo que falta

| tanda | casos | dificultad |
|---|---|---|
| 1 (esta) | 8 | ninguno cita |
| 2 | 8 | solo v1 cita |
| 3 | 2 | solo v2 cita |
| 4 | 17 | **ambos citan** -- la mas dificil: hay que ver si cada cita sostiene lo que afirma |
