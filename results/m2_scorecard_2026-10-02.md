# Scorecard M2 — Evaluación del Modelo

Generado: 2026-10-02T19:52:43.400861+00:00 · commit `1c75fc47d0ce34e80cc215fc6088a754938c83cd` · seed 42 · hardware: NVIDIA A100-SXM4-80GB, 81920 MiB

## Resumen por modelo

| Modelo | N | Exact Match | F1 | BLEU | ROUGE-L | BERTScore | Similitud (%) | Juez (1-5) | Cumplimiento citas (%) | Latencia (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 213 | 0.0% | 0.187 | 1.267 | 0.124 | 68.507 | 3.284 | 3.674 | 89.2% | 13.533 |
| fine_tuned | 213 | 0.0% | 0.34 | 7.202 | 0.233 | 76.936 | 6.043 | 3.769 | 100.0% | 5.718 |

## Sesgos

- **length_bias_pearson_r_baseline**: -0.112
- **length_bias_pearson_r_fine_tuned**: 0.045
- **self_preference_judge_gap**: 0.024
- **self_preference_similarity_gap**: 0.028
- **self_preference_divergence**: -0.004
- **self_preference_flagged**: False
- **position_bias_flip_rate_pct**: 14.8
- **position_bias_n_pairs**: 30

## Conclusión

Se evaluaron 213 ejemplos de validacion (mismo split de M1, seed=42, val_fraction=0.15).

Juez (compuesto 1-5): baseline 3.674, fine-tuned 3.769. Similitud lexica: baseline 3.284%, fine-tuned 6.043%. Cumplimiento de no-inventar-citas: baseline 89.2%, fine-tuned 100.0%.

Fallos de parseo del juez: baseline 36/213, fine-tuned 25/213 (excluidos de los promedios de judge_composite).
