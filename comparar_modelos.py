"""Lanzador de conveniencia: python comparar_modelos.py

Abre la GUI de escritorio para comparar modelos de lenguaje candidatos para
Amparo. Requiere OPENROUTER_API_KEY configurada en un archivo .env (ver
.env.example) y las dependencias de requirements.txt instaladas.
"""

from tools.model_comparator.app import main

if __name__ == "__main__":
    main()

