"""Configuracion central del harness de evaluacion de M2."""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# El unico dataset. Trae los 1536 ejemplos sin contexto (origen v1), los 755
# con contexto (v2) y las 289 variantes contrastivas, cada uno con su origen y
# su split ya resueltos. `dataset.load_records()` lo filtra por origen.
#
# Sin numero de version en el nombre a proposito: hubo cinco archivos de datos
# -- dos fuentes y tres derivados -- y decidir con cual se entrenaba era una
# pregunta abierta en cada corrida. La version la lleva el hash, que es donde
# tiene que estar.
DATASET_PATH = PROJECT_ROOT / "data" / "dataset.jsonl"

# El hash del dataset validado, en un solo lugar.
#
# Se calcula sobre el contenido con los finales de linea normalizados a LF, NO
# sobre los bytes del archivo. En una copia de Windows las lineas terminan en
# CRLF y el sha1 de los bytes sale distinto (79bcc7e328a1f146) aunque el
# contenido sea identico: ese valor, tomado de un working copy, hizo fallar la
# primera corrida de M1 v2 en Colab. Usar `huella_dataset()` y no hashear a
# mano.
#
# **Es un sha1 de 16 caracteres y NO es la huella del manifiesto.**
# `data/dataset_manifiesto.json` trae `91a871d60eca2097`, que es un sha256 sobre
# los registros canonicos (json ordenado, uno por linea). Son dos algoritmos
# sobre dos cosas distintas y copiarse uno en el otro hace fallar la corrida
# antes de empezar. Lo comprueba `tests/evaluation/test_config_dataset.py`.
#
# Historico, para que un cambio no pase por despiste:
#   db0b6e65126cab25  hasta 9c9f5a9  dataset de 2709 (contrastivos con la regla B2 vieja)
#   37e579ad0bfac6bd  33cc019        dataset de 2626 (REGLA_B2_V3, construido con BM25)
#   a13e6d32629eb6a9  fase A         dataset de 2580: contextos con e5 + FAISS (H4),
#                                    validacion congelada (H3), punteros solo de train
DATASET_SHA1 = "a13e6d32629eb6a9"

# Nombre anterior, cuando apuntaba a data/dataset_legal.jsonl. Se conserva para
# no romper lo que lo importa, pero lo que antes era un archivo de 1536 ahora es
# uno de 2580: quien necesite solo los de v1 debe usar dataset.load_records().
LOCAL_DATASET_PATH = DATASET_PATH


def huella_dataset(path=None) -> str:
    """El sha1 corto del dataset, igual en cualquier sistema operativo.

    Normaliza CRLF a LF antes de hashear, que es lo que hace que el valor
    coincida con DATASET_SHA1 tanto en una copia local de Windows como en el
    clon que baja Colab.
    """
    import hashlib

    datos = (path or DATASET_PATH).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(datos).hexdigest()[:16]


def verificar_dataset(path=None, esperado: str = DATASET_SHA1) -> str:
    """Falla si el dataset en disco no es el validado. Devuelve su huella."""
    real = huella_dataset(path)
    if real != esperado:
        raise SystemExit(
            f"El dataset tiene huella {real} y se esperaba {esperado}. "
            f"Regeneralo, o actualiza DATASET_SHA1 si el cambio es intencional.")
    return real

# Deben coincidir con RANDOM_SEED/VAL_FRACTION de colab/m1_finetune.ipynb
# (celda 3 y 7) para evaluar sobre el mismo split de validacion que uso M1.
RANDOM_SEED = 42
VAL_FRACTION = 0.15

BASE_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

# Respuestas del asistente. Era 300: el baseline escribe ~180 palabras con
# listas y 159 de sus 213 respuestas quedaban cortadas a mitad de frase
# (corrida M2 del 2026-10-02), lo que sesgaba la comparacion contra el. 900
# deja margen de sobra para que el baseline termine sus respuestas (no solo
# las de largo medio); el fine-tuned (~46 palabras) no cambia. El scorecard
# reporta igual el % de respuestas cortadas de cada modelo.
MAX_NEW_TOKENS_GENERATION = 900
# El juez es Groq (external_judge.py): sus presupuestos de tokens viven ahi
# (GROQ_MAX_TOKENS_*). El juez local Qwen, con MAX_NEW_TOKENS_JUDGE=512, se
# quito en m3.5: era de la misma familia que el modelo evaluado.

BERTSCORE_MODEL = "dccuchile/bert-base-spanish-wwm-cased"
BERTSCORE_NUM_LAYERS = 10

# Pares de la comparacion cara a cara. None = todos (231 pares x 2 ordenes).
# Era una muestra de 30: poca para concluir quien gana.
PAIRWISE_SAMPLE_SIZE = None

# Rutas de Google Drive. Son simples strings (no se tocan fuera de Colab), por
# eso es seguro importar este modulo tambien fuera de Colab (p. ej. en tests).
DRIVE_ROOT = "/content/drive/MyDrive/Colab Notebooks/Amparo"
DRIVE_ADAPTER_DIR = f"{DRIVE_ROOT}/amparo-lora-adapter"
DRIVE_EVAL_OUTPUT_ROOT = f"{DRIVE_ROOT}/evaluacion"

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
