# Comentarios docentes sobre la Wiki de M3

**Estado:** anexo publicado en el repositorio mediante PR, no edición ya aplicada a la Wiki. El acceso Git a la Wiki no estuvo disponible desde el entorno revisor. El equipo puede incorporar este anexo como página nueva y enlazarla desde M3, preservando la página histórica.

**Fuente:** «M3 · Sistema RAG — decisiones», commit de Wiki `607fce63805a980dd1f17096c9c0a7ddea3cdd18` (27/09/2026 21:55:14, Colombia), idéntico en `ecd20988eafa4a0a391b342592084d38c5711750`. La revisión se basa en el bundle aportado, no en una lectura de la Wiki remota en vivo. No contiene calificación.

## Secciones 20–24: contratos, evaluación y DSPy

**Reconocimiento.** Es valioso que usen el mismo contrato de registros para comparar rutas y conservar respuesta/contexto. También se reconoce la decisión de no adoptar DSPy cuando la ventaja en dev no se sostiene en test: es una conclusión experimental, no una integración fallida por no adoptarse.

**Sugerencia.** Mantener explícitos el medidor, su versión y los denominadores junto a las tablas. No interpretar como mejora del sistema una diferencia producida al cambiar el formato o la forma de evaluar. Este comentario refuerza una distinción que ustedes ya explican.

## Sección 25 y notebook S10, fases 5 / 5b: reanudación

**Lo que ya está bien.** La fase 5b firma el archivo de entrada y el reuso entre rutas comprueba pregunta, respuesta, contextos y referencia. Los casos donde el juez no responde no se dan por evaluados.

**Hallazgo acotado.** El checkpoint de la fase 5 se nombra por ruta y LoRA/base, y `evaluar_corrida` acepta una fila existente por clave antes de contrastar su huella. Un id repetido con otra respuesta puede reutilizar una nota anterior. Se reprodujo con un juez controlado, no se demostró que ocurriera en su corrida final.

**Sugerencia.** Validar huella y protocolo del juez/embeddings al reanudar; rechazar o separar el checkpoint incompatible. Probar: mismo id y mismo contenido no hace llamadas; mismo id y cambio de pregunta, respuesta, contexto o referencia no reutiliza la nota. No se pide construir reanudación desde cero.

Fuente: [evaluar_corrida histórico](https://github.com/TomasPosada0626/Amparo/blob/0c9078097de77ccaabe9070dedcde9c0a59452b4/tools/evaluation/ragas_metrics.py) y [notebook S10](https://github.com/TomasPosada0626/Amparo/blob/0c9078097de77ccaabe9070dedcde9c0a59452b4/colab/m3_s10_rag_agentico.ipynb).

## Secciones 19 y 27: procedencia, citas y cálculos

**Reconocimiento.** La documentación ya distingue verificar que se vio un artículo de comprobar que sostiene la afirmación. También reconoce que una cuenta bloqueada puede figurar como intentada en la traza, sin haberse ejecutado. No presentamos esos límites como si ustedes los hubieran ignorado.

**Sugerencia de fechas.** Normalizar día, mes y año completos; resolver referencias relativas frente a una fecha base explícita. Cuando falta el año o el ancla, pedir aclaración o devolver un estado no verificable, en lugar de aceptar una fecha cualquiera. Pruebas mínimas: mismo día/mes con otro año; «ayer» sin fecha base; fecha absoluta concordante; ausencia de fecha.

**Sugerencia de citas.** Separar la mención del usuario de la evidencia recuperada y usar el par norma–artículo. Reconocer o refutar la referencia del usuario es distinto de aceptarla como sustento. Probar dos normas de ejemplo con el mismo número de artículo, sin atribuir a estas pruebas una validación jurídica.

**Sugerencia de traza.** Distinguir solicitado, bloqueado, fallido y ejecutado; solo el último acredita que la cuenta se realizó. Este ajuste corresponde al pendiente que ya declararon en la revisión de la corrida final.

Fuente: [agente histórico](https://github.com/TomasPosada0626/Amparo/blob/0c9078097de77ccaabe9070dedcde9c0a59452b4/tools/rag/agentico.py) y [sección 27 archivada](https://github.com/TomasPosada0626/Amparo/blob/0c9078097de77ccaabe9070dedcde9c0a59452b4/docs/m3_decisiones_rag.md).

## Sección 27: cierre M3 y transición a M4

Se reconoce que cierran M3 con una corrida concreta y distinguen pendientes de M4. Completar o retirar la tabla vacía de detalle del [reporte S10](https://github.com/TomasPosada0626/Amparo/blob/0c9078097de77ccaabe9070dedcde9c0a59452b4/results/m3_s10_rutas_2026-09-27.md) mejoraría la lectura; no implica que falten las métricas finales, que sí están.

La arquitectura de octubre cambia estructura y producto. Estas observaciones históricas no autorizan aplicar automáticamente un patch de `tools/` a `src/`. Mantener referencias separadas y evaluar el sistema migrado con sus propios datos, corridas y versiones. La corrección de tipos del nuevo `src/ragas_eval.py` se entrega en otro PR, sin efecto retroactivo sobre M3.

## Incorporación sugerida a la Wiki

Crear una página nueva, «Revisión docente M3», con este contenido o enlazar a este anexo. Añadir desde la página M3 un enlace a esa revisión sin reemplazar resultados ni reescribir el cierre histórico. Los enlaces a los PR se encuentran en la conversación de revisión del repositorio. La nota permanece en el canal privado del curso.
