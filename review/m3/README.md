# Revisión docente de M3 — Amparo

## Alcance y referencias

Esta revisión distingue la entrega histórica de M3 del seguimiento de la arquitectura migrada. La calificación se comunica por el canal privado del curso; no forma parte de este documento.

| Referencia | Uso |
|---|---|
| [Código histórico `0c9078097de7`](https://github.com/TomasPosada0626/Amparo/tree/0c9078097de77ccaabe9070dedcde9c0a59452b4) | M3 conservado en el historial de `archivo/amparo-v1`. Fecha Git: 27/09/2026 22:16:12, Colombia. |
| Wiki, `607fce63805a980dd1f17096c9c0a7ddea3cdd18` | Página «M3 · Sistema RAG — decisiones», con resultados y pendientes, 27/09/2026 21:55:14, Colombia. |
| Wiki, `ecd20988eafa4a0a391b342592084d38c5711750` | Home actualiza enlace y estado de M3 a las 21:59:37 del mismo día. |
| [Base migrada `f0328fead270`](https://github.com/TomasPosada0626/Amparo/tree/f0328fead270ad8e91b950b988c4a59292b1f1b6) | Seguimiento de octubre; no sustituye la referencia histórica ni se atribuye a septiembre. |

La Wiki se leyó desde un bundle aportado a la revisión. Su historial autocontenido de 44 commits pasó la verificación de integridad de Git; la página M3 no cambia entre los dos commits citados. Sus fechas respaldan el registro documental antes del cierre del 27/09 a las 23:59. No certifican la hora del push ni sustituyen el comprobante de Interactiva. La migración de octubre no se interpreta como entrega tardía.

Este PR documental no corrige el sistema. Las sugerencias ejecutables para el main migrado se presentan por separado. No fusionar historias no relacionadas ni reintroducir automáticamente `tools/` en el nuevo `src/`.

## Fortalezas reconocidas

**Integración y comparación controlada.** El M3 histórico compara búsqueda densa, híbrida y reranking con el mismo generador/prompt; luego contrasta una pasada, tool use y ReAct sobre 56 preguntas (50 gold y 6 adversariales). Reutiliza Qwen+LoRA de M1 y el instrumental de M2. Se valoran los contratos compartidos y los deltas medidos, no solamente la lista de técnicas.

**Criterio experimental.** Los resultados reportados no respaldan usar el agente como ruta predeterminada frente a una pasada. También se decide no adoptar el prompt optimizado por DSPy tras contrastarlo en test y analizar el efecto del formato en dev. No se exige que lo opcional mejore para reconocer que se investigó con criterio.

**Harness y trazabilidad.** Ya conservan respuestas/contextos, checkpoints, conteos de valores válidos, fallos de parseo y mediciones reutilizables de contenido idéntico. Su RAGAS propio está explicado y probado con inyección de juez/embeddings. No se propone añadir estas capacidades como si estuvieran ausentes.

**Limitaciones explícitas.** Distinguen búsquedas del modelo de búsquedas forzadas por código; reconocen límites de citas, corpus, recuperación, LoRA y cálculos. Se leyeron esos apartados antes de formular los comentarios. Una métrica baja no se convierte automáticamente en incumplimiento.

Fuentes: [resultados S08](https://github.com/TomasPosada0626/Amparo/blob/0c9078097de77ccaabe9070dedcde9c0a59452b4/results/m3_s08_busqueda_2026-09-27.md), [resultados S10/DSPy](https://github.com/TomasPosada0626/Amparo/blob/0c9078097de77ccaabe9070dedcde9c0a59452b4/results/m3_s10_rutas_2026-09-27.md), [notebook S10](https://github.com/TomasPosada0626/Amparo/blob/0c9078097de77ccaabe9070dedcde9c0a59452b4/colab/m3_s10_rag_agentico.ipynb) y [Wiki](https://github.com/TomasPosada0626/Amparo/wiki).

## Observaciones históricas, sin parche automático al nuevo main

1. **Identidad del checkpoint.** `evaluar_corrida` puede reanudar por id/ruta sin contrastar contenido. La fase 5b sí protege mediante huella de archivo y el reuso entre rutas sí comprueba contenido: el hallazgo no invalida esos mecanismos ni demuestra contaminación histórica. Al mantener esa arquitectura, conviene validar contenido y configuración del evaluador antes del reuso.
2. **Procedencia de fechas y citas.** La validación de fecha no contrasta íntegramente el año ni ancla referencias como «ayer». El verificador de citas compara números sin distinguir norma; este último límite ya está documentado por el equipo. Convertir esos límites en pruebas y mantener separados «mencionado por el usuario» y «recuperado como evidencia».
3. **Cierre documental.** Completar o retirar la tabla vacía de detalle de la corrida final en S10, sin confundirla con ausencia de resultados: el resumen y las métricas finales sí están presentes.

Fuentes: [evaluador histórico](https://github.com/TomasPosada0626/Amparo/blob/0c9078097de77ccaabe9070dedcde9c0a59452b4/tools/evaluation/ragas_metrics.py), [agente histórico](https://github.com/TomasPosada0626/Amparo/blob/0c9078097de77ccaabe9070dedcde9c0a59452b4/tools/rag/agentico.py). Los comentarios por sección de la Wiki se incorporan en un anexo separado.

## Seguimiento de octubre

En `src/ragas_eval.py` del main migrado, el evaluador puede aceptar tipos/rangos inválidos y convertir ausencia de medición en cero. La corrección propuesta valida veredictos, distingue `None`/`null` de ceros medidos y declara cobertura. Es seguimiento para nuevas corridas, no un defecto atribuido a la entrega histórica de septiembre. No se mezclan resultados de ambos productos.

## Relación con el curso y límites de la validación

[S08](https://github.com/manularrea/EAFIT-SI4006/blob/753c4ac955e927172dcf4e5a710a2e0cb062f781/sesiones/s08/README.md) pide comparación de técnicas y latencia. [S10](https://github.com/manularrea/EAFIT-SI4006/blob/753c4ac955e927172dcf4e5a710a2e0cb062f781/sesiones/s10/README.md) pide RAG, herramientas, harness, cuatro métricas y lectura honesta; enseña RAGAS a mano y presenta W&B/DSPy como opcionales. No se exige sustituir la implementación propia ni contratar APIs de pago.

El preview registró 21 tests originales seleccionados y 22 caracterizaciones docentes (17 históricas y 5 de octubre), con las limitaciones indicadas en el reporte de revisión: archivos completos verificados y funciones auxiliares transcritas. Los tests de caracterización pueden confirmar un defecto; no son todos pruebas de corrección. Esta fase no ejecuta nuevamente las corridas con modelos.

El PR correctivo tiene su propia evidencia de regresión sobre el módulo completo. No se ejecutó el pipeline completo, GPU ni APIs; antes de incorporar cambios, el equipo debe validar con sus dependencias y consumidores. Las sugerencias no certifican validez jurídica ni representan trabajo atribuible al equipo en la entrega original.

## Prioridad hacia M4 y Demo

Conservar el snapshot de septiembre; comprobar el nuevo sistema bajo su propio protocolo y no atribuirle las cifras del anterior. Comparar versiones con el mismo medidor, mostrando cobertura y límites. Priorizar correcciones acotadas antes que una reescritura general. Las sugerencias futuras no son requisitos retroactivos.
