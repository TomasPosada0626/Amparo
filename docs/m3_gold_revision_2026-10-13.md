# Revisión del gold de artículos — 2026-10-13

**Para Leonardo Galeano.** Primera pasada de Claude, a pedido de Tomás.

> **Resuelto el 2026-10-13.** Leonardo aprobó la propuesta de las 14 marcas
> (decisión 2) y delegó en Claude la decisión 1, por ser un proyecto de curso.
> Las 14 quedaron registradas con `registrar_bc_gold` y el art. 26 de la Ley 361
> pasó a `responde_parcial` para 9033 (justificación en el CSV). El gold no tiene
> filas pendientes. Lo de abajo es la propuesta tal como se presentó.

## Lo que se comprobó y está bien

Comprobaciones mecánicas sobre las 217 filas del gold y los 45 casos:

| comprobación | resultado |
|---|---|
| cada artículo del gold existe en el índice evaluado | **217/217** |
| el CSV y `data/eval_set_articulos.json` traen las mismas etiquetas | **sí**, 0 diferencias |
| la huella de la metadata del índice coincide con la del CSV | **sí**, `8cd72136235d6dfe` en las 217 |
| filas con veredicto individual tuyo | **92** (A 27, B′ 62, B nombradas 3), sin cambios |

## Un error de código, corregido

`tools/registrar_bc_gold.py` escribía mal el `doc_id` de los cuatro artículos de
la Ley 2220 que el dictamen nombró como `responde_parcial` (9010, arts. 67, 68,
70 y 71): `conciliacion_ley_2220_2022` en vez de
`estatuto_conciliacion_ley_2220_2022`. Por eso la planilla
`docs/m3_articulos_gold_bc_para_marcar.md` traía 5 parciales marcadas en vez de
9, y faltaban 18 casillas en lugar de 14. Ya está corregido, la planilla está
regenerada y una prueba impide que vuelva a pasar
(`tests/test_registrar_bc_gold.py`).

## Decisión 1 — El caso 9033 no tiene ningún artículo que lo responda

*"Estoy incapacitado por una cirugía y mi empresa me acaba de despedir, ¿es
válido?"*

Su única etiqueta, Ley 361 art. 26, la marcaste `no_responde` el 2026-10-10. Así
el caso **no puede acertar nunca**: el techo de acierto@k es 44/45, no 45/45.

Además hay una **tensión con el criterio del propio caso**, que exige *"mencionar
la posible estabilidad laboral reforzada por salud y la necesidad de autorización
del Ministerio del Trabajo"*. En el corpus, esa autorización **solo aparece en el
art. 26 de la Ley 361** (*"ninguna persona en situación de discapacidad podrá ser
despedida... salvo que medie autorización del Ministerio del Trabajo"*). Si el
art. 26 no responde, el criterio pide algo que ningún artículo del corpus
sostiene.

Candidatos del corpus, para que elijas (puede ser más de uno, o ninguno):

| norma | art. | qué aporta |
|---|---|---|
| Ley 361 de 1997 | 26 | la autorización del Ministerio del Trabajo y la indemnización de 180 días. **¿Revisar el `no_responde`?** La Corte Constitucional extendió esta protección a quien está en debilidad manifiesta por salud aunque no tenga discapacidad calificada. Eso lo valoras tú |
| Constitución | 13 | *"protegerá especialmente a aquellas personas que por su condición económica, física o mental, se encuentren en circunstancia de debilidad manifiesta"* |
| Constitución | 53 | la estabilidad en el empleo como principio mínimo del trabajo |
| Ley 2452 de 2025 (CPT) | 7, lit. c | el juez laboral conoce de *"los asuntos sobre estabilidad laboral reforzada"*: la vía |

Cualquiera que agregues entra como `candidato_omision` con veredicto `responde`,
igual que las tres omisiones de B′.

## Decisión 2 — Las 14 casillas `responde_parcial` que faltan

El dictamen de B y C está aprobado con totales por clase: B 64/15/3 y C 38/8/0.
Ya están marcadas las 9 parciales que el dictamen nombró. Faltan **8 de la clase
B y 6 de la C**. `responde_parcial` = el artículo da **el derecho o la vía, no
las dos**, o trata el tema de forma general sin tocar lo que se pregunta.

Mi propuesta, leído el texto de cada artículo:

**Clase B (8)**

| caso | norma | art. | por qué parcial |
|---|---|---|---|
| 9050 | Código de Comercio | 712 | regula cómo se expide un cheque, no qué hacer si lo devuelven |
| 9004 | Constitución | 49 | el derecho general a la salud; nada sobre la oportunidad de la cita ni la vía |
| 9041 | CST | 156 | la excepción para cooperativas y alimentos, no la regla que protege el salario |
| 9062 | Ley 100 | 33 | requisitos de la pensión de vejez; no dice cómo corregir semanas faltantes |
| 9058 | Ley 1620 | 21 | qué debe contener el manual de convivencia, en general |
| 9049 | Código de Comercio | 26 | para qué sirve el registro mercantil, no quién debe matricularse |
| 9060 | Ley 80 | 5 | derechos y deberes generales del contratista, no las actas falsas |
| 9066 | Ley 388 | 99 | el régimen de licencias, no la queja contra la obra del vecino |

Suplentes, si alguno de los ocho te parece `responde`: 9050 C.Co. 784, 9048
Ley 906 art. 67, 9060 Ley 80 art. 26, 9066 Ley 1801 art. 140, 9049 C.Co. 10.

**Clase C (6)**

| caso | norma | art. | por qué parcial |
|---|---|---|---|
| 9036 | CST | 179 | trabajo dominical y festivo; la pregunta es por horas extra |
| 9032 | Constitución | 49 | el derecho general a la salud, igual que en 9004 |
| 9051 | CST | 57 | obligaciones generales del empleador, nada sobre el cambio de turno |
| 9061 | Ley 1333 | 1 | quién tiene la potestad sancionatoria ambiental; no el ruido ni la vía |
| 9067 | Código Civil | 1602 | el contrato es ley para las partes, sin la exclusividad ni la acción |
| 9044 | Código Civil | 411 | quiénes deben alimentos, no cómo aumentar la cuota |

Suplentes: 9002 Ley 1010 art. 2, 9067 C.Co. 1317, 9051 CST 158.

**Cómo se registra cuando decidas:** marca las 14 en
`docs/m3_articulos_gold_bc_para_marcar.md` y corre
`python -m tools.registrar_bc_gold --registrar --escribir`. El registro se niega
a escribir si los totales no cuadran con el dictamen.

## Qué cambia en las métricas

- **Decisión 2: nada en el acierto@k.** Ninguna de las 125 filas se recuperó;
  solo cuentan para el techo de suficiencia.
- **Decisión 1: el techo de acierto@k pasa de 44/45 a 45/45.** El acierto
  medido puede subir en un caso si el artículo que agregues ya se está
  recuperando. Se vuelve a medir después de registrarlo, no antes.
