# Scorecard M2 — Evaluación del Modelo

Generado: 2026-09-19T01:00:48.124583+00:00 · commit `c0d4afd818831cc658ae1ead1516be5ef5089f57` · seed 42 · hardware: NVIDIA L4, 23034 MiB

## Resumen por modelo

| Modelo | N | Exact Match | F1 | BLEU | ROUGE-L | BERTScore | Similitud (%) | Juez (1-5) | Cumplimiento citas (%) | Latencia (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 201 | 0.0% | 0.177 | 1.691 | 0.122 | 69.742 | 3.411 | 4.024 | 73.6% | 12.199 |
| fine_tuned | 201 | 0.0% | 0.318 | 8.638 | 0.246 | 78.781 | 18.54 | 4.277 | 100.0% | 4.296 |

## Resumen por categoría

### baseline

| Categoría | N | Similitud (%) | Juez (1-5) | Cumplimiento citas (%) |
|---|---|---|---|---|
| Acceso a informacion publica | 8 | 2.65 | 4.125 | 37.5% |
| Accidentes de transito | 9 | 3.567 | 4.194 | 88.9% |
| Arriendo | 9 | 2.978 | 3.694 | 55.6% |
| Comparendos de transito | 9 | 3.167 | 3.944 | 55.6% |
| Conciliacion prejudicial | 8 | 5.488 | 4.0 | 87.5% |
| Contratacion estatal y facturacion | 8 | 2.35 | 3.656 | 62.5% |
| Contratos empresariales (B2B) | 8 | 4.737 | 3.906 | 100.0% |
| Derecho administrativo general | 8 | 3.263 | 4.143 | 100.0% |
| Derecho ambiental sancionatorio | 8 | 2.962 | 3.719 | 37.5% |
| Derecho contractual general | 8 | 3.337 | 4.312 | 87.5% |
| Derecho de familia - alimentos | 8 | 3.975 | 4.281 | 100.0% |
| Despido | 9 | 3.222 | 4.25 | 44.4% |
| Educacion / debido proceso disciplinario | 8 | 3.375 | 4.036 | 87.5% |
| Embargos | 9 | 3.133 | 3.889 | 100.0% |
| Garantias de consumo | 9 | 2.222 | 4.194 | 77.8% |
| Licencias urbanisticas | 8 | 5.237 | 3.571 | 87.5% |
| Pensiones y seguridad social | 8 | 3.65 | 3.688 | 50.0% |
| Prestamos informales y usura | 8 | 3.413 | 4.219 | 75.0% |
| Procedimiento civil - recursos | 8 | 4.6 | 4.219 | 62.5% |
| Propiedad intelectual - marcas | 8 | 3.825 | 4.5 | 75.0% |
| Propiedad y linderos | 8 | 2.962 | 4.071 | 100.0% |
| Relaciones laborales | 9 | 3.289 | 4.25 | 55.6% |
| Reporte en centrales de riesgo | 9 | 2.278 | 3.806 | 100.0% |
| Salud / EPS | 9 | 2.711 | 3.889 | 44.4% |

### fine_tuned

| Categoría | N | Similitud (%) | Juez (1-5) | Cumplimiento citas (%) |
|---|---|---|---|---|
| Acceso a informacion publica | 8 | 13.525 | 4.344 | 100.0% |
| Accidentes de transito | 9 | 16.622 | 4.139 | 100.0% |
| Arriendo | 9 | 13.678 | 4.556 | 100.0% |
| Comparendos de transito | 9 | 25.911 | 4.417 | 100.0% |
| Conciliacion prejudicial | 8 | 14.537 | 3.875 | 100.0% |
| Contratacion estatal y facturacion | 8 | 18.663 | 4.281 | 100.0% |
| Contratos empresariales (B2B) | 8 | 24.55 | 4.25 | 100.0% |
| Derecho administrativo general | 8 | 19.562 | 4.125 | 100.0% |
| Derecho ambiental sancionatorio | 8 | 28.1 | 4.625 | 100.0% |
| Derecho contractual general | 8 | 14.012 | 4.438 | 100.0% |
| Derecho de familia - alimentos | 8 | 13.188 | 3.906 | 100.0% |
| Despido | 9 | 12.311 | 4.167 | 100.0% |
| Educacion / debido proceso disciplinario | 8 | 22.675 | 4.375 | 100.0% |
| Embargos | 9 | 19.389 | 4.194 | 100.0% |
| Garantias de consumo | 9 | 16.778 | 4.5 | 100.0% |
| Licencias urbanisticas | 8 | 26.2 | 4.312 | 100.0% |
| Pensiones y seguridad social | 8 | 12.438 | 4.062 | 100.0% |
| Prestamos informales y usura | 8 | 10.662 | 4.531 | 100.0% |
| Procedimiento civil - recursos | 8 | 25.238 | 4.281 | 100.0% |
| Propiedad intelectual - marcas | 8 | 14.6 | 4.219 | 100.0% |
| Propiedad y linderos | 8 | 17.525 | 4.219 | 100.0% |
| Relaciones laborales | 9 | 21.144 | 4.444 | 100.0% |
| Reporte en centrales de riesgo | 9 | 19.789 | 4.167 | 100.0% |
| Salud / EPS | 9 | 23.567 | 4.194 | 100.0% |

## Sesgos

- **length_bias_pearson_r_baseline**: -0.411
- **length_bias_pearson_r_fine_tuned**: 0.042
- **self_preference_judge_gap**: 0.063
- **self_preference_similarity_gap**: 0.151
- **self_preference_divergence**: -0.088
- **self_preference_flagged**: False
- **position_bias_flip_rate_pct**: 0.0
- **position_bias_n_pairs**: 30

## Conclusión

Se evaluaron 201 ejemplos de validacion (mismo split de M1, seed=42, val_fraction=0.15).

Juez (compuesto 1-5): baseline 4.024, fine-tuned 4.277. Similitud lexica: baseline 3.411%, fine-tuned 18.54%. Cumplimiento de no-inventar-citas: baseline 73.6%, fine-tuned 100.0%.

Fallos de parseo del juez: baseline 4/201, fine-tuned 0/201 (excluidos de los promedios de judge_composite).

Sesgos: length_bias_pearson_r_baseline=-0.411; length_bias_pearson_r_fine_tuned=0.042; self_preference_judge_gap=0.063; self_preference_similarity_gap=0.151; self_preference_divergence=-0.088; self_preference_flagged=False; position_bias_flip_rate_pct=0.0; position_bias_n_pairs=30

---

**Nota:** este scorecard es la salida cruda de `scorecard.export_markdown` (Fase 7 del notebook), generada *antes* del sondeo con el juez externo (Groq) y del eval set adversarial -- por eso las cifras de sesgos de arriba (`self_preference_*`, `position_bias_flip_rate_pct=0.0`) reflejan solo el juez Qwen y quedan corregidas en la wiki. Ver [M2 - Evaluación del Modelo](https://github.com/TomasPosada0626/Amparo/wiki/M2-‐-Evaluación-del-Modelo) para el análisis completo con el juez de Groq y los resultados del eval set (`data/eval_set.json`). El CSV por registro (`metricas_por_registro.csv`) y los JSONL crudos quedan en Google Drive (`MyDrive/Colab Notebooks/Amparo/evaluacion/2026-09-19_010048/`), no en este repo -- ver la justificación de esa decisión en la sección de Reproducibilidad de la wiki de M2.
