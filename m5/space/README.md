---
title: Amparo
emoji: ⚖️
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: 6.31.0
python_version: "3.12"
app_file: app.py
pinned: false
license: apache-2.0
short_description: Triaje de acciones constitucionales colombianas
---

# Amparo · Space de la demo (M5)

Esta carpeta es lo que se sube al Space: `app.py`, `requirements.txt` y este `README.md`.
El código de Amparo no se copia. Al arrancar, `app.py` clona el repo
<https://github.com/TomasPosada0626/Amparo> en la rama o tag `AMPARO_REF`, y ese tag es la
versión que muestra la pestaña Estado.

**Secrets** (*Settings → Variables and secrets*):
- `GROQ_API_KEY`: obligatoria. M3 razona con gpt-oss-120b por Groq.
- `WANDB_API_KEY`: opcional. Activa el tablero de W&B (proyecto `amparo-m5`).

**Variables:**

| variable | defecto | qué hace |
|---|---|---|
| `AMPARO_REF` | `m5` | rama o tag del repo que se clona (para la demo: un tag fijo) |
| `AMPARO_VLM` | `auto` | `auto`: fp16 con GPU y CPU sin ella · `fp16` · `int4` · `off` (solo texto) |
| `AMPARO_MAX_PIXELS` | 200704 en CPU | tope de resolución de la foto |
| `AMPARO_SHARE` | `0` | `1` para el enlace público de Gradio (Kaggle) |

**En Kaggle (T4):** se clona el repo y se corre
`AMPARO_SHARE=1 python m5/space/app.py`. Con la GPU, el VLM va en **fp16**: la
cuantización int4 no cumplió su contrato (`m5/cuantizacion.json`, ver el README de M5).
