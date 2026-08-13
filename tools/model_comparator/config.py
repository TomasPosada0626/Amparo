"""Configuración del comparador de modelos: proveedor y catálogo de modelos.

Unico proveedor: Ollama local (http://localhost:11434), 100% gratis, sin
API key ni limites de uso mas alla de tu propio hardware.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
PRIVATE_DATASET_PATH = PROJECT_ROOT / "private" / "dataset_legal_30_ejemplos.md"

load_dotenv(PROJECT_ROOT / ".env")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1").strip()

SYSTEM_PROMPT = (
    "Eres un asistente juridico que responde consultas de derecho colombiano. "
    "Responde de forma breve, fundamentada y prudente. No inventes normas ni cites "
    "fuentes que no existan; si no estas seguro, dilo explicitamente."
)


@dataclass(frozen=True)
class ModelSpec:
    """Un modelo candidato disponible para comparar."""

    id: str  # clave interna estable, usada en resultados/exportes
    label: str  # nombre mostrado en la interfaz
    slug: str  # tag de Ollama (p. ej. "qwen2.5:7b")
    provider: str = "ollama"
    notes: str = ""  # contexto adicional


# Modelos locales via Ollama: gratis, sin limite de uso, corren en tu maquina.
# Requiere tener Ollama instalado y corriendo (https://ollama.com/download) y
# haber descargado cada modelo una vez con "ollama pull <tag>". Los tags se
# verificaron contra ollama.com/library (y ollama.com/search para Salamandra)
# el 2026-08-12.
DEFAULT_MODELS: list[ModelSpec] = [
    ModelSpec("qwen25_7b", "Qwen2.5 7B Instruct", "qwen2.5:7b", "ollama",
               "Candidato principal M1 (wiki)"),
    ModelSpec("qwen25_14b", "Qwen2.5 14B Instruct", "qwen2.5:14b", "ollama",
               "Variante grande de Qwen2.5 para contraste (~9GB)"),
    ModelSpec("llama31_8b", "Llama 3.1 8B Instruct", "llama3.1:8b", "ollama",
               "Candidato M1 (wiki)"),
    ModelSpec("llama32_3b", "Llama 3.2 3B Instruct", "llama3.2:3b", "ollama",
               "Modelo pequeno/rapido para contraste"),
    ModelSpec("mistral_7b", "Mistral 7B Instruct v0.3", "mistral:7b", "ollama",
               "Candidato M1 descartado en fase temprana (wiki); tag confirmado v0.3"),
    ModelSpec("gemma2_9b", "Gemma 2 9B Instruct", "gemma2:9b", "ollama", ""),
    ModelSpec("phi35_mini", "Phi-3.5 Mini Instruct", "phi3.5", "ollama", ""),
    ModelSpec("deepseek_r1_7b", "DeepSeek-R1 Distill Qwen 7B", "deepseek-r1:7b", "ollama",
               "Modelo de razonamiento (chain-of-thought)"),
    ModelSpec("aya_expanse_8b", "Aya Expanse 8B", "aya-expanse:8b", "ollama",
               "Cohere, optimizado para multilinguismo (fuerte en espanol)"),
    ModelSpec("salamandra_7b", "Salamandra 7B Instruct (BSC)", "hdnh2006/salamandra-7b-instruct", "ollama",
               "Candidato M1 alternativo documentado (wiki); GGUF comunitario del modelo BSC-LT, "
               "sobre-muestreado en espanol/catalan/gallego/euskera"),
]
