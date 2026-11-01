"""Amparo: triaje de acciones constitucionales colombianas.

El LLM extrae hechos y el motor de reglas decide el mecanismo. Subpaquetes:

    nucleo       esquema del dominio, motor de reglas, terminos procesales
    rag          corpus, chunking, indice y metricas RAGAS propias
    sistemas     los brazos de M3 (SistemaRAG, SistemaReglas, Agente, ...) y generadores
    finetuning   datos, entrenamiento LoRA y generacion local (M1)
    evaluacion   metricas, juez, harness, costos y brazos (M2/M3)
    multimodal   VLM, enchufe con M3 y criterios del harness de M4
    ejecucion    corridas, arranque, entorno de Colab y publicacion en results/
    pipelines    cada notebook como funciones por etapa
"""
__version__ = "0.5.0"
