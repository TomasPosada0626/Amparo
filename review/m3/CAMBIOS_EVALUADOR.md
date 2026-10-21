# Evaluador migrado: validación y cobertura del juez

Base de esta sugerencia: `f0328fead270ad8e91b950b988c4a59292b1f1b6`, octubre. **No cambia la entrega de septiembre ni su calificación.**

## Cambios acotados

- `faithfulness_juez`: admite únicamente conteos enteros reales (no booleanos), no negativos y con sostenidas <= total. No recorta conteos inválidos. Total cero válido es no aplicable. Se conserva la razón agregada por afirmaciones.
- `context_precision_juez`: exige booleanos JSON. `false` es cero medido; `"false"`, 0 y JSON malformado no son booleanos. Un fragmento sin veredicto válido invalida la medición de esa consulta, sin comprimir el ranking. Se conserva la convención existente de cero para una consulta sin fragmentos recuperados.
- `answer_relevancy`: exige una lista no vacía de preguntas no vacías; no itera por caracteres de un string ni filtra silenciosamente elementos de tipos incorrectos. Se conserva el coseno medio con el encoder normalizado del equipo. Un error operativo del encoder se propaga, no se convierte en métrica.
- Sin medición válida, estas funciones devuelven `None`, serializable como `null`. Los ceros válidos se conservan. Las excepciones operativas de `_llamar`/`guardar_cache` no se ocultan.
- `evaluar` conserva sus claves existentes y añade `protocolo_juez` y `cobertura_juez`, con estados e índices de entrada (base cero), valores válidos y denominador/unidad por métrica. Impide truncar lotes con `zip` al recibir longitudes distintas.
- `imprimir` admite `None`, muestra N/D y cobertura; mantiene compatibilidad con artefactos anteriores que no incluyen los campos nuevos.

Las tres funciones de métricas exactas, prompts del juez y sus fórmulas permanecen idénticos. No se modifica el corpus, modelos, criterio jurídico, cache del juez, notebooks ni resultados históricos. El cambio no demuestra que el juez real haya emitido los casos inválidos usados en las pruebas.

## Validación

Desde la raíz de la rama correctiva:

```bash
python -m unittest discover -s review/m3/tests -p test_ragas_revision.py -v
```

38 tests docentes aprobados sobre el módulo completo. `schema` y `rag` se sustituyen al importar; juez y encoder son dobles controlados. Se prueban las funciones corregidas, integración de `evaluar`, serialización y `imprimir`. La copia original del archivo se verificó con Git blob `e794383d4ec844038f32b268f1a973bd3df84128`; se conservaron sus finales CRLF.

No se ejecutaron los modelos, las APIs, la suite completa del equipo ni el notebook completo. No se certifica validez jurídica ni funcionamiento end-to-end. La evidencia se encuentra en `review/m3/evidence/`.

## Antes de fusionar y medir

1. Validar en el entorno del equipo un lote pequeño, un caso de fallo del juez y la serialización de N/D en los consumidores del notebook/reporte. Aquí se validaron `evaluar` e `imprimir`; no se auditó cada consumidor externo.
2. Regenerar los sellos de código de la NUEVA corrida y guardar sus artefactos por separado. No atribuir a la nueva versión resultados producidos por la anterior.
3. Invalidar o separar caches con veredictos defectuosos persistidos. Este patch los detecta, pero no elimina el cache ni reintenta automáticamente un resultado ya almacenado.
4. Comparar M3/M4 bajo el mismo protocolo y cobertura. Si se excluyen casos inválidos, el promedio es parcial; no comparar cifras con denominadores distintos como si midieran exactamente lo mismo.

No se imponen APIs de pago ni una sustitución por la biblioteca RAGAS. La implementación propia permanece; se valida lo que acepta y lo que reporta.
