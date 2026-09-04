"""Configuracion central del harness de evaluacion de M2."""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LOCAL_DATASET_PATH = PROJECT_ROOT / "data" / "dataset_legal.jsonl"

# Deben coincidir con RANDOM_SEED/VAL_FRACTION de colab/baseline_finetune.ipynb
# (celda 3 y 7) para evaluar sobre el mismo split de validacion que uso M1.
RANDOM_SEED = 42
VAL_FRACTION = 0.15

BASE_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

MAX_NEW_TOKENS_GENERATION = 300
MAX_NEW_TOKENS_JUDGE = 200
MAX_NEW_TOKENS_PAIRWISE_JUDGE = 100

BERTSCORE_MODEL = "dccuchile/bert-base-spanish-wwm-cased"
BERTSCORE_NUM_LAYERS = 10

POSITION_BIAS_SAMPLE_SIZE = 30
SELF_PREF_DIVERGENCE_THRESHOLD = 0.10

# Rutas de Google Drive. Son simples strings (no se tocan fuera de Colab), por
# eso es seguro importar este modulo tambien fuera de Colab (p. ej. en tests).
DRIVE_ROOT = "/content/drive/MyDrive/Colab Notebooks/Amparo"
DRIVE_ADAPTER_DIR = f"{DRIVE_ROOT}/amparo-lora-adapter"
DRIVE_EVAL_OUTPUT_ROOT = f"{DRIVE_ROOT}/evaluacion"

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
