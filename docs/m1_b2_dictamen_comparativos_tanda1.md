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
| **2822** embargo de indemnizacion | `mejora` | **alta** | Arrancan igual. v1 cierra pidiendo *"el certificado de la **Comision de Trabajo**"*, entidad que no reconozco como existente en Colombia para esto. v2 pide *"el certificado de pago"*, que es generico y seguro. |
| **3423** norma derogada | `regresion` | media | v1 da la ruta correcta y concreta: consultar el **Diario Oficial**, derecho de peticion, reposicion y apelacion, nulidad. v2 solo remite a un consultorio. Aqui el mas util es v1 y ninguno afirma de mas. |
| **3428** horario de la ventanilla | `mejora` | alta | v1 reconoce que no lo sabe y acto seguido afirma *"La ventanilla unica funciona para tramitar licencias y certificaciones ante varios entes"*, dato sobre la entidad que no esta en el contexto. v2 reconoce y remite a la pagina o al telefono, sin inventar. |
| **4026** costo del certificado | `empate` | baja | Los dos agregan especificos sin respaldo. v1 nombra *"la Policia o la Fiscalia"* como emisoras; v2 inventa factores de precio (*"si eres menor de edad, si tienes antecedentes penales o civiles"*). Fallan igual, en direcciones distintas. |
| **4127** cotizaciones en el exterior | **`empate`** | baja | v1 pide la historia laboral y remite a la Superintendencia Financiera. v2 propone *"reclamacion de habeas data pidiendo que se verifique la documentacion"*, una via concreta cuya pertinencia para semanas cotizadas en el exterior habria que validar. |
| **4321** demanda vs denuncia | `empate` | media | Los dos explican bien la diferencia y ninguno cita. v1 nombra la Inspeccion de Trabajo como receptora de denuncias; v2 presume el juzgado civil. Diferencias de enfasis, no de calidad. |
| **4324** formato del recurso | `empate` | baja | **Los dos afirman lo mismo sin respaldo**: que no existe un formato oficial. El contexto no lo dice (es la razon por la que el caso quedo `valido` en el dictamen de etiquetas). v2 agrega *"orientacion gratuita en un centro de conciliacion"*, que no es la via para un recurso. |
| **4630** permiso por violencia | `mejora` | media | **Caso sensible.** v1 es confuso: *"No es tema de permiso: el permiso te lo da tu jefe, y eso no te libera de ir"*. v2 es claro y remite a la Personeria o la Inspeccion del Trabajo, pero afirma que negarlo *"puede ser una discriminacion laboral"*, calificacion juridica sin respaldo. Mejor v2, con reserva. |

## Resumen de la tanda

| | |
|---|---|
| `mejora` (v2 mejor) | 3 — 2822, 3428, 4630 |
| `empate` | **4** — 4026, 4127, 4321, 4324 |
| `regresion` (v1 mejor) | **1** — 3423 |

Sin ganador claro en los casos sin citas. La ventaja de v2 aparece cuando v1
afirma datos de entidades que no estan en el contexto (3428, 2822); la de v1
cuando da rutas correctas y concretas que v2 cambia por un reenvio generico
(3423).

## Las tres consultas, respondidas

Se consultaron y el dictamen cambia en tres filas. Lo que sigue son las
respuestas recibidas, con su efecto.

### 2822 — la "Comision de Trabajo" no es la autoridad

No es una entidad competente para certificar la naturaleza de una
indemnizacion ni para levantar un embargo. **`mejora` sube de media a alta.**

Con una reserva que no estaba en mi dictamen: v2 tampoco acierta del todo. Un
certificado de pago sirve como prueba pero no demuestra que el dinero sea
inembargable. Lo que corresponde es pedir copia de la providencia que ordeno
el embargo y acreditar el origen del dinero ante el juzgado.

### 4127 — mi `regresion` era excesiva

El habeas data **no es necesariamente incorrecto**: sirve cuando el problema
es que los registros estan ausentes o inexactos en la administradora. Lo que
no hace es resolver si las cotizaciones del exterior cuentan, que depende del
pais, del regimen y de que exista un convenio internacional.

Pero ninguna de las dos respuestas menciona el convenio, y esa omision pesa
igual en las dos. **Cambia de `regresion` a `empate`**, confianza baja.

### 4630 — hay un derecho que ninguno menciona, y el corpus no lo tiene

La reforma laboral de 2025 modifico el regimen de licencias del articulo 57
del CST e incorporo supuestos de citaciones judiciales, administrativas y
legales. Si la Comisaria cito formalmente, no es un permiso discrecional del
jefe: puede ser una licencia.

**Comprobado en el corpus**: el articulo 57 indexado es la version anterior.
Concede licencias para sufragio, cargos oficiales transitorios y grave
calamidad, y **no menciona** citacion, comisaria, violencia ni actuacion
judicial o administrativa.

Eso significa que **la recuperacion no podia traer ese derecho ni con un
ranking perfecto**: no esta en el texto indexado. Es la brecha de la Ley 2466
de 2025 de `docs/m3_cobertura_corpus.md`, apareciendo en un caso concreto y
sensible.

El dictamen se mantiene en `mejora` y sube a confianza media: v2 orienta mejor
-- pide el tiempo por escrito, con copia a la Personeria o la Inspeccion --
mientras v1 presenta el asunto como si dependiera solo del jefe. Una respuesta
puede omitir una regla y aun asi orientar mejor que otra que induce a una
lectura equivocada. **La omision queda anotada en las dos.**

Tampoco es cierto que toda negativa del empleador sea discriminacion laboral,
como afirma v2: eso depende de la citacion y de la justificacion.

## Tres que pedian atencion (resueltas arriba)

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
