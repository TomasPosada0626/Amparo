# Dictamen propuesto: las 8 etiquetas B2 pendientes

**Borrador para validacion del abogado.** No esta escrito en
`docs/m1_b2_adjudicacion.csv`: las ocho siguen en `pendiente` hasta que el
abogado apruebe o cambie cada una.

Esta primera pasada la redacto Claude verificando cada fragmento contra la
pregunta, partiendo de una propuesta previa de ChatGPT. **Donde discrepo lo
digo y explico por que**, para que el abogado vea las dos lecturas.

## La regla aplicada

> ¿El contexto permite dar **al menos una orientacion sustantiva y pertinente**,
> aunque sea parcial, o solo contiene normas **relacionadas superficialmente**
> que no permiten orientar el caso?

La distincion que decide: **"el fragmento menciona un tema parecido" no es lo
mismo que "el fragmento permite responder una parte de la pregunta".**

- `valido` -> el ejemplo exige abstencion con razon; B2 esta bien.
- `modo_mal_asignado` -> el contexto si permite orientar algo; deberia ser B3,
  que es el modo de responder la parte respaldada y avisar que falta.

Esto responde **solo** si el ejemplo requiere abstencion. No dice nada sobre la
legalidad de las multas, becas, recursos ni reclamaciones.

## Los ocho

| caso | dictamen | confianza | por que |
|---|---|---|---|
| **3328** entrega internacional B2B | `valido` | baja | El art 50 de la Ley 1480 fija el plazo de entrega **en comercio electronico al consumidor** (30 dias calendario). El caso es B2B con proveedor extranjero: el tema se parece, el regimen probablemente no aplica. |
| **3517** multa por no presentar PMA | `modo_mal_asignado` | media | El art 63 de la Ley 1801 dice literal *"Presentar e implementar el plan de manejo ambiental"* como obligacion **del organizador de un evento**. Permite orientar condicionalmente: si el caso es un evento, la obligacion existe y recae en quien lo organiza. |
| **3822** beca retirada sin explicacion | `valido` | media | El art 18 regula la devolucion de bienes dejados para un servicio; el art 58, el procedimiento de reclamacion de consumo. Que el regimen de consumo cubra una beca universitaria es justo lo que el contexto no permite afirmar. |
| **3920** licencia negada por certificado | `valido` | alta | El art 25 de la Ley 142 trata las **concesiones y permisos ambientales que necesita un prestador** de servicios publicos. La pregunta es por el certificado de disponibilidad exigido a quien pide una licencia urbanistica. Son dos cosas distintas que comparten la palabra "servicios publicos". |
| **4226** donde denunciar un gota a gota | `modo_mal_asignado` | alta | El art 67 del CPP dice *"Toda persona debe denunciar **a la autoridad**"* y el 68 las exoneraciones. Permite orientar sobre el deber de denunciar y sus limites, aunque no sobre ante que entidad concreta. |
| **4321** diferencia demanda / denuncia | `modo_mal_asignado` | alta | El art 69 fija los **requisitos de la denuncia** y el 66 dice que la accion penal la ejerce el Estado por la Fiscalia. Eso es, literalmente, la mitad de la comparacion que se pregunta. |
| **4324** formato del recurso de reposicion | **`valido`** | baja | **Discrepo de la propuesta previa.** Ver abajo. |
| **4724** sin energia en la vereda | **`valido`** | baja | **Discrepo de la propuesta previa.** Ver abajo. |

## Las dos discrepancias

### 4324 — formato del recurso de reposicion

La propuesta previa decia `modo_mal_asignado` (media-baja). Yo propongo
`valido`.

El art 227 de la Ley 2452 cubre **procedencia, oportunidad y tramite**: contra
que autos procede, que debe interponerse y sustentarse en la misma audiencia, y
que fuera de audiencia hay tres dias desde la notificacion.

La pregunta es otra: *"¿hay algun formato oficial para escribirlo o lo puedo
hacer a mano?"*. El articulo **no dice nada sobre la forma documental** -- ni
que exista un formato, ni que no exista, ni si vale manuscrito.

Es pertinente al **tema** (el recurso de reposicion) pero no a la **pregunta**
(el formato). Esa es exactamente la distincion que la regla pide no confundir.

Confianza baja: alguien podria sostener que *"interpuesto y sustentado"* ya
dice algo sobre la forma. Es el dictamen mas discutible de los ocho junto con
el 3328.

### 4724 — sin energia en la vereda

La propuesta previa decia `modo_mal_asignado` (media). Yo propongo `valido`.

El art 34 de la Ley 388 define el **suelo suburbano** como categoria de
ordenamiento territorial, y menciona que debe garantizarse *"el
autoabastecimiento en servicios publicos domiciliarios"* y que los municipios
deben expedir regulaciones complementarias.

La pregunta es de una persona que **no tiene energia en su vereda**. El
articulo habla de como se clasifica el suelo y que obligaciones de
planificacion tiene el municipio, no del derecho de un habitante a que le
lleven la red ni de a quien reclamar.

Menciona "servicios publicos" y "energia" en un contexto de ordenamiento
territorial. Eso cae del lado de **tema parecido**, no de responder una parte.

## Tres casos para atencion especial del abogado

1. **3328** -- el mas fronterizo. La norma de entregas es tematicamente
   cercana; la duda es de aplicabilidad del regimen de consumo a una relacion
   B2B internacional. Si aplicara, el dictamen cambia a `modo_mal_asignado`.
2. **4324** -- discrepancia abierta, arriba.
3. **4724** -- discrepancia abierta, arriba.

## Resumen

| | |
|---|---|
| `valido` (B2 correcto, el modelo debia abstenerse) | **5** -- 3328, 3822, 3920, 4324, 4724 |
| `modo_mal_asignado` (deberia ser B3) | **3** -- 3517, 4226, 4321 |

Si el abogado confirma los 3 `modo_mal_asignado`, esos ejemplos del dataset
tienen el target equivocado: les pide abstencion cuando el contexto permitia
orientar parcialmente. Es el primer resultado accionable sobre los 594.

## Que NO decide esto

Ningun campo `comparacion_v1_v2`. Cual modelo respondio mejor es una decision
independiente, y los 35 siguen en `pendiente`.
