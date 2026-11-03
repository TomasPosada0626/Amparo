# Graph Report - Amparo  (2026-11-03)

## Corpus Check
- 85 files · ~165,381 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 14 file(s) not represented in the graph (top: .ipynb 7, .csv 5, (none) 2)

## Summary
- 1601 nodes · 3423 edges · 100 communities (86 shown, 14 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 219 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `074ce2b1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- generar_imagenes.py
- Criterios del harness M4
- Pipeline M3 RAG
- test_pipeline_m4.py
- Pipeline
- pertinencia_por_plano
- Pipeline M2 harness
- correr_t6
- Contexto
- Acuerdo entre jueces (tests)
- Costos
- Harness de tres dimensiones
- Tests del pipeline M1
- Pipeline M1 fine-tuning
- Entrenamiento LoRA
- casos_m4.csv: 11 casos sobre 6 imagenes
- scorecard.py
- Términos procesales
- Índice de recuperación
- Baselines y generación M1
- Sistemas RAG de M3
- Corpus y evaluación retrieval
- Juez LLM (clase)
- Motor de reglas art. 6
- Estabilidad M1
- Plan y entrega M4
- test_multimodal.py
- corridas.py
- schema.py
- RAGAS propio
- Estabilidad M2
- Migración y sello
- README y módulos
- Decisiones del harness M4
- pathlib
- json
- Datos de entrenamiento
- Brazo híbrido M1
- Limitaciones y citas
- Tests compartidos
- Tabla de costos
- test_pipeline_m3.py
- sistema_multimodal
- corrida_m4.py
- Collate y tokenizer (tests)
- T6 - Corrida del harness: notas para T8 (Lucas -> Nico)
- cargar_checkpoint
- Generación local HF
- Publicación en results
- Correr brazos M3
- Intervalos y F1
- Generador HF (tests)
- Tokenizadores
- Publicación M1
- Transformación de consulta
- Agente
- se_abstuvo
- Fertilidad de tokenizadores
- SistemaReglas y plazos
- Reproducir
- Tesis y arquitecturas M3
- Reporte y corpus
- Publicación M2
- Doc03 acción de cumplimiento
- entrenar
- delta_con_sin_imagen
- Doc02 oficio de planeación
- Doc04 respuesta de la CAR
- Hallazgos de M1
- Hallazgos de M2
- m01 · doc01_respuesta_eps.png
- metricas.py
- Jurisprudencia conocida
- Doc01 respuesta EPS
- Doc06 notificación borrosa
- Corrida falsa M3
- m01 · doc01_respuesta_eps.png
- Curva de pérdida
- m4_multimodal.py
- Doc05 notificación acueducto
- Sesgo de longitud
- correr_brazos
- Proyecto (pyproject)
- test_scorecard.py
- ctx
- ._hechos
- construir_tabla_delta
- LectorVisual
- render_salida
- parse_salida
- tabla_puente
- BM25
- enchufar_m3
- test_delta_repetido_cuenta_por_corrida_y_vacia_antes_de_cada_llamada
- etiquetas_presentes
- descargar

## God Nodes (most connected - your core abstractions)
1. `caso()` - 34 edges
2. `parse_salida()` - 28 edges
3. `Contexto` - 28 edges
4. `scorecard()` - 26 edges
5. `Contexto` - 26 edges
6. `Pipeline` - 26 edges
7. `Harness de M4: decisiones de T5 y T6 (y T7)` - 24 edges
8. `correr()` - 23 edges
9. `render_salida()` - 22 edges
10. `validar_casos()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `Dónde está hoy el recorrido completo` --references--> `construir_responder_m3()`  [INFERRED]
  review/m4/PLAN_DEMO.md → amparo/multimodal/enchufe.py
- `H1 · El delta con/sin imagen no mide latencia` --references--> `delta_con_sin_imagen()`  [INFERRED]
  review/m4/README.md → amparo/multimodal/scorecard.py
- `4. Prioridades para Demo Day` --references--> `sistema_multimodal()`  [INFERRED]
  review/m4/README.md → amparo/multimodal/sistema_visual.py
- `Criterio exacto (mecanismo final de M3)` --implements--> `nota_exacto()`  [INFERRED]
  m4/eval_set/FORMATO_CASOS.md → amparo/multimodal/criterios.py
- `Comparacion por fragmento en campos de texto libre` --rationale_for--> `_acierta_campo()`  [INFERRED]
  m4/eval_set/FORMATO_CASOS.md → amparo/multimodal/criterios.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Defecto de citas impertinentes: medicion, causa y mitigacion** — reporte_pertinencia_citas, reporte_fusion_fundamentos, reporte_capa_depuracion_citas, reporte_juez_vs_abogado [EXTRACTED 1.00]
- **Cuatro criterios del harness M4 (exacto, campos, valvula, juez_vlm)** — m4_eval_set_formato_casos_criterio_exacto, m4_eval_set_formato_casos_criterio_campos, m4_eval_set_formato_casos_criterio_valvula, m4_eval_set_formato_casos_criterio_juez_vlm, amparo_multimodal_criterios_calificar [EXTRACTED 1.00]
- **Caso de prueba: dato crítico (plazo) ilegible por degradación, esperando que el VLM no invente el número** — m4_eval_set_imagenes_doc06_notificacion_borrosa, m4_eval_set_imagenes_doc06_notificacion_borrosa_plazo_descargos_ocluido, m4_eval_set_imagenes_doc06_notificacion_borrosa_degradaciones_foto_simulada [INFERRED 0.75]
- **Auditoria del juez LLM (validez, escala, acuerdo humano, familias, determinismo)** — readme_sonda_validez, readme_adherencia_escala_juez, reporte_juez_vs_abogado, reporte_acuerdo_entre_jueces, reporte_jueces_misma_familia, reporte_determinismo_juez, reporte_autopreferencia [INFERRED 0.85]
- **Campos clave que el VLM debe extraer del oficio doc02** — m4_eval_set_imagenes_doc02_oficio_planeacion_oficio_spm_0412, m4_eval_set_imagenes_doc02_oficio_planeacion_requerimiento_obra_sin_licencia, m4_eval_set_imagenes_doc02_oficio_planeacion_plazo_15_dias_habiles, m4_eval_set_imagenes_doc02_oficio_planeacion_traslado_inspeccion_policia [INFERRED 0.85]
- **Renuencia documentada: peticion bajo Ley 1712 art. 10, negativa de la entidad, base para accion de cumplimiento** — m4_eval_set_imagenes_doc03_respuesta_cumplimiento_derecho_de_peticion, m4_eval_set_imagenes_doc03_respuesta_cumplimiento_ley_1712_2014_art_10, m4_eval_set_imagenes_doc03_respuesta_cumplimiento_negativa_actualizacion_tecnologica, m4_eval_set_imagenes_doc03_respuesta_cumplimiento_accion_de_cumplimiento [INFERRED 0.85]
- **Campos del oficio que el VLM debe extraer (entidad, radicado, peticionario, asunto, decisión)** — m4_eval_set_imagenes_doc04_respuesta_car_corporioclaro, m4_eval_set_imagenes_doc04_respuesta_car_radicado_crcl_2231, m4_eval_set_imagenes_doc04_respuesta_car_jac_los_naranjos, m4_eval_set_imagenes_doc04_respuesta_car_queja_vertimientos_la_clara, m4_eval_set_imagenes_doc04_respuesta_car_decision_archivo_sin_medidas [INFERRED 0.85]
- **Sellado y trazabilidad de corridas (huella, manifiesto, sello, tag)** — readme_huella_codigo, subir_huella_manifiesto, subir_sello_subida, docs_migracion_tag_entrega_m4, docs_migracion_huella_amparo, reporte_origen_cifras [INFERRED 0.85]
- **Invencion del plazo en m10 que la valvula no detecta** — m4_eval_set_casos_m4_m10, m4_eval_set_imagenes_anonimizacion_doc06_notificacion_borrosa, m4_notas_t6_lucas_hallazgo_invento_plazo_m10, m4_readme_peor_caso_m10, m4_eval_set_formato_casos_criterio_valvula [INFERRED 0.95]

## Communities (100 total, 14 thin omitted)

### Community 0 - "generar_imagenes.py"
Cohesion: 0.19
Nodes (14): doc01_respuesta_eps(), doc02_oficio_planeacion(), doc03_respuesta_cumplimiento(), doc04_respuesta_car(), doc05_notificacion_acueducto(), doc06_notificacion_borrosa(), encabezado(), F() (+6 more)

### Community 1 - "Criterios del harness M4"
Cohesion: 0.05
Nodes (69): _acierta_campo(), advertencias_lectura(), calificar(), cargar_casos(), _entero(), _es_nulo(), _esperado_campos(), _esperado_exacto() (+61 more)

### Community 2 - "Pipeline M3 RAG"
Cohesion: 0.09
Nodes (24): cargar(), auditar_corpus(), chunking(), cierre(), _ck_guardar(), comparar(), comprobar_ragas(), consultas_fallidas() (+16 more)

### Community 3 - "test_pipeline_m4.py"
Cohesion: 0.14
Nodes (4): cargar(), AmparoFalso, test_cargar_normaliza_a_rgb(), test_los_notebooks_de_m4_clonan_demo_final()

### Community 4 - "Pipeline"
Cohesion: 0.16
Nodes (14): casos_validos(), correr(), Pipeline, test_cada_imagen_se_carga_una_vez(), test_cronometro_mide_ver_mas_m3_y_deja_fuera_carga_y_juez(), test_csv_invalido_no_corre_nada(), test_excepcion_del_sistema_detiene_la_corrida(), test_imagen_faltante_no_corre_nada() (+6 more)

### Community 5 - "pertinencia_por_plano"
Cohesion: 0.16
Nodes (7): alucinacion_normativa(), citas_en_texto(), clasificar_cita(), _limpiar_cita(), pertinencia_citas(), pertinencia_por_plano(), _vocabulario_normas()

### Community 6 - "Pipeline M2 harness"
Cohesion: 0.08
Nodes (20): sesgo_posicion(), acuerdo_entre_jueces(), autopreferencia(), Contexto, correr(), elegir_juez(), filas_por_caso(), formato_vocabulario() (+12 more)

### Community 7 - "correr_t6"
Cohesion: 0.13
Nodes (16): correr_t6(), leer_fila_m3(), escribir_costos(), escribir_m3(), _rutas(), test_armar_relato_sin_json_usa_el_texto_crudo(), test_correr_t6_de_punta_a_punta(), test_correr_t6_exige_el_brazo_antes_de_correr() (+8 more)

### Community 8 - "Contexto"
Cohesion: 0.15
Nodes (13): vaciar_caches(), cerrar(), Contexto, correr(), correr_harness(), delta_imagen(), delta_repetido(), miniaturas() (+5 more)

### Community 9 - "Acuerdo entre jueces (tests)"
Cohesion: 0.10
Nodes (23): candidatos(), medir(), puntuar_muestra(), ClienteFalso, _corrida_previa(), _fabrica(), construir(), JuezFalso (+15 more)

### Community 10 - "Costos"
Cohesion: 0.15
Nodes (5): Costos, SistemaHibrido, SistemaOraculo, SistemaRAG, T7 - Enchufe real de M3

### Community 11 - "Harness de tres dimensiones"
Cohesion: 0.07
Nodes (15): acierto_por_item(), acuerdo_entre_jueces(), adherencia_a_la_rubrica(), cohen_kappa(), harness(), _lectura_familias(), resumen_juez(), _spearman() (+7 more)

### Community 12 - "Tests del pipeline M1"
Cohesion: 0.17
Nodes (12): _celdas_codigo(), _ic(), LoraConfigFalsa, _publicaciones_literales(), test_cada_artefacto_se_guarda_en_el_codigo_antes_de_publicarse(), test_destinos_literales_coinciden_con_lo_declarado_en_arranque(), test_el_notebook_conserva_los_pins_de_instalacion(), test_el_notebook_llama_todas_las_etapas_en_orden_y_compila() (+4 more)

### Community 13 - "Pipeline M1 fine-tuning"
Cohesion: 0.09
Nodes (19): aplicar_lora(), abstencion_validation(), aplicar_lora(), cargar_modelo(), cerrar(), cobertura_clasificador(), comparar_con_base(), Contexto (+11 more)

### Community 14 - "Entrenamiento LoRA"
Cohesion: 0.16
Nodes (9): callbacks_parada(), crear_trainer(), filtrar_hiperparametros(), hiperparametros(), registro_hiperparametros(), configurar_entrenamiento(), test_filtrar_traduce_warmup_ratio_a_pasos_y_registra_lo_omitido(), test_filtrar_usa_evaluation_strategy_en_versiones_viejas() (+1 more)

### Community 15 - "casos_m4.csv: 11 casos sobre 6 imagenes"
Cohesion: 0.11
Nodes (28): casos_m4.csv: 11 casos sobre 6 imagenes, m01 - exacto: tutela (EPS niega cirugia), m02 - campos sobre doc01 (cadera), m03 - campos sobre doc02 (plazo_dias 15), m04 - exacto: accion_cumplimiento (Ley 1712), m05 - campos sobre doc03 (contratos), m06 - exacto: accion_popular (cuatro veredas), m07 - campos sobre doc04 (entidad 'claro') (+20 more)

### Community 16 - "scorecard.py"
Cohesion: 0.16
Nodes (8): cargar_guardado(), delta_repetido(), guardar(), _mediana(), _schema_mecanismo(), tabla_desde_disco(), test_cargar_guardado_devuelve_lo_mismo_que_se_guardo(), test_guardar_escribe_scorecard_y_trazas()

### Community 17 - "Términos procesales"
Cohesion: 0.19
Nodes (8): calcular_termino(), contar_habiles(), es_habil(), festivos(), leer_fecha(), _lunes_siguiente(), pascua(), sumar_habiles()

### Community 19 - "Baselines y generación M1"
Cohesion: 0.10
Nodes (12): imprimir(), baseline(), baseline_few_shot(), evaluar_ajustado(), _generar_y_puntuar(), legibles(), HibridoFalso, _salida() (+4 more)

### Community 20 - "Sistemas RAG de M3"
Cohesion: 0.13
Nodes (10): con_pregunta_triable(), leer_triable(), trocear(), cita_completa(), extraer_hechos(), formatear_contexto(), generador_groq(), generar() (+2 more)

### Community 21 - "Corpus y evaluación retrieval"
Cohesion: 0.14
Nodes (8): _cita_de(), citas_esperadas(), comparar_chunking(), comparar_estrategias(), elegir_estrategia(), evaluar_recuperacion(), _percentil(), trocear_fijo()

### Community 22 - "Juez LLM (clase)"
Cohesion: 0.08
Nodes (11): _degradar(), _envolver(), experimento_inyeccion(), experimento_validez(), familia_de(), Juez, orden_de_candidatos(), clave() (+3 more)

### Community 23 - "Motor de reglas art. 6"
Cohesion: 0.18
Nodes (6): decidir(), Decision, estrato_verificacion(), explicar(), Hechos, pivota_en_juicio()

### Community 24 - "Estabilidad M1"
Cohesion: 0.11
Nodes (9): comparar_con_previa(), estabilidad(), CorridaFalsa, ctx(), _previa(), test_comparar_con_previa_identicas_y_codigo_distinto(), test_comparar_con_previa_sin_artefactos_no_es_concluyente(), test_estabilidad_con_previa_guarda_y_publica() (+1 more)

### Community 25 - "Plan y entrega M4"
Cohesion: 0.16
Nodes (11): M4 - Amparo ya ve (README de entrega), Tabla M3 (n=120, 0.675) vs M4 (n=3, 1.0), M4 Plan de trabajo - Su sistema ya ve, Qwen2-VL-2B-Instruct, Reparto de tareas T1-T9 (Santiago, Lucas, Nico, Martin/Tomas), Rubrica M4 (10 puntos), S13_Lab_Integracion_Visual_RESUELTO.ipynb (plantilla base), Tabla de delta M3 vs M4 (+3 more)

### Community 26 - "test_multimodal.py"
Cohesion: 0.15
Nodes (13): Amparo, formatear(), por_que(), LectorFalso, _m3(), test_al_abstenerse_no_muestra_una_regla_que_cerro_el_caso(), test_el_caso_de_seguridad_muestra_el_aviso(), test_manifiesto_registra_lo_que_atribuye_las_cifras() (+5 more)

### Community 27 - "corridas.py"
Cohesion: 0.05
Nodes (21): celda(), _en_colab(), guardar_checkpoint(), humo(), _procedencia(), ahora_bogota(), comparar(), Corrida (+13 more)

### Community 28 - "schema.py"
Cohesion: 0.16
Nodes (7): cargar_normas(), citas(), demostraciones_few_shot(), _norm(), planos_normativos(), separar_planos(), validar()

### Community 29 - "RAGAS propio"
Cohesion: 0.18
Nodes (11): _encoder(), answer_relevancy(), context_precision_exacta(), context_precision_juez(), context_recall_exacto(), evaluar(), faithfulness_exacta(), faithfulness_juez() (+3 more)

### Community 30 - "Estabilidad M2"
Cohesion: 0.10
Nodes (6): corridas_previas(), estabilidad(), CorridaFalsa, ctx_con_salidas(), sin_clave(), test_estabilidad_sin_corrida_previa_es_none_y_no_true()

### Community 31 - "Migración y sello"
Cohesion: 0.16
Nodes (12): Logica extraida de los notebooks a modulos, Fuera de alcance: despliegue y reentrenamiento, Migracion de notebooks a paquete Python amparo/, Tag entrega-m4 (commit d158742), Verificacion: linea base antes y despues de migrar, Estructura del paquete amparo/, Huella del codigo y version de datos por corrida, De donde salen las cifras (corridas y huellas) (+4 more)

### Community 32 - "README y módulos"
Cohesion: 0.16
Nodes (12): Amparo: triaje de acciones constitucionales en Colombia, M1: fine-tuning LoRA de Qwen2.5-7B-Instruct, M2: harness con LLM-as-a-judge y cinco sondas, M3: cuatro arquitecturas (fine-tuned, RAG basico, RAG avanzado, agente + reglas), M4: componente visual Qwen2-VL-2B (patron input), reproducir.py: entrada unica de reproduccion, Estabilidad entre corridas (m1_estabilidad.json), groq (juez y agente via API) (+4 more)

### Community 33 - "Decisiones del harness M4"
Cohesion: 0.14
Nodes (7): armar_relato(), correr_harness(), leer_latencia_m3(), Harness de M4: decisiones de T5 y T6 (y T7), test_armar_relato_con_json_es_la_formula_del_notebook(), test_latencia_m3_es_por_caso_y_no_por_llamada(), test_m3_recibe_el_relato_armado_con_el_json_de_ver()

### Community 34 - "pathlib"
Cohesion: 0.20
Nodes (3): _raiz(), normas_por_id(), etiqueta()

### Community 35 - "json"
Cohesion: 0.11
Nodes (15): guardar(), chunking_de_m3(), comprobar_brazo(), construir_responder_m3(), cargar_corpus(), _json_de(), Brazo 4 - agente + reglas (M3), _responder() (+7 more)

### Community 36 - "Datos de entrenamiento"
Cohesion: 0.22
Nodes (8): comprobar_truncados(), construir(), construir_datasets(), medir_max_len(), mensajes(), _texto_completo(), preparar_dataset(), test_construir_enmascara_el_prompt_y_no_trunca_con_max_len_medido()

### Community 37 - "Brazo híbrido M1"
Cohesion: 0.16
Nodes (11): brazo_hibrido(), cargar_datos(), comprobar_splits(), resumen_sonda(), _preparar_hibrido(), test_brazo_hibrido_corta_temprano_si_el_extractor_es_mudo(), test_brazo_hibrido_guarda_por_encima_del_10_por_ciento(), test_brazo_hibrido_guarda_sus_tres_artefactos() (+3 more)

### Community 38 - "Limitaciones y citas"
Cohesion: 0.16
Nodes (14): Eval set v3 con puente subconjunto_v1, Lo que NO esta establecido (limitaciones), Relatos sinteticos, no expedientes, accion_cumplimiento en el brazo del agente (F1 0.4615), Adherencia del juez a la rubrica (0.7573), Capa de depuracion de citas de categoria equivocada, Caso A09 (trampa accion_cumplimiento, art. 9 Ley 393), Desacuerdos juridicos vs reglas de codificacion (+6 more)

### Community 39 - "Tests compartidos"
Cohesion: 0.15
Nodes (9): cargar_m1(), recortar(), generar(), recortar_al_bloque(), cargar_salidas(), _salida(), test_cargar_m1_desenvuelve_datos_y_conserva_la_corrida(), test_cargar_m1_exige_el_mismo_orden_que_el_eval_set() (+1 more)

### Community 40 - "Tabla de costos"
Cohesion: 0.14
Nodes (6): BrazoNoMedido, Cronometro, imprimir(), tabla(), tabla_costos(), test_brazo_no_medido_sale_en_none_y_no_en_cero()

### Community 41 - "test_pipeline_m3.py"
Cohesion: 0.09
Nodes (12): CostoPorBrazo, _ctx(), Reloj, _salida(), test_correr_brazo_latencia_por_caso(), test_correr_brazo_tolera_un_fallo_de_api_con_salida_vacia(), test_correr_brazos_sin_gpu_corre_el_agente_y_el_brazo_uno(), test_costo_por_brazo_cuenta_reales_y_cache_y_cronometra_solo_las_reales() (+4 more)

### Community 42 - "sistema_multimodal"
Cohesion: 0.12
Nodes (17): armar_relato(), sistema_multimodal(), Al desplegar (M5), conviene…, Backlog (después de la Demo), Dónde está hoy el recorrido completo, Guion sugerido (bloques, sin minutos obligatorios), Plan para Demo Day — Amparo, Prioridad 1 · [P1] La experiencia de punta a punta en una sola llamada, con el fundamento a la vista (+9 more)

### Community 43 - "corrida_m4.py"
Cohesion: 0.18
Nodes (10): cerrar(), _git(), gpu(), guardar(), huella_eval_set(), manifiesto(), nueva(), _sha() (+2 more)

### Community 44 - "Collate y tokenizer (tests)"
Cohesion: 0.15
Nodes (4): collate_para(), _Enc, test_collate_rellena_a_la_derecha_con_pad_0_y_menos_100(), TokFalso

### Community 45 - "T6 - Corrida del harness: notas para T8 (Lucas -> Nico)"
Cohesion: 0.15
Nodes (13): m10 - valvula ADVERSARIAL (fecha|plazo_dias), Criterio valvula (campos que deben venir null), doc06_notificacion_borrosa.jpg - ADVERSARIAL mojada, sin fecha ni plazo, Corrida local T6 (RTX 5060, M3 sustituto), Hallazgo 1: entidad y plazo_dias salen null, Hallazgo 2: m10 inventa 'dos semanas' en pretension_visible, Hallazgo 3: sentido invertido en doc03 (m04/m05), T6 - Corrida del harness: notas para T8 (Lucas -> Nico) (+5 more)

### Community 46 - "cargar_checkpoint"
Cohesion: 0.33
Nodes (4): cargar_checkpoint(), _cargar_ck(), SistemaFalso, test_un_brazo_corrido_se_guarda_en_el_checkpoint_y_se_reutiliza()

### Community 47 - "Generación local HF"
Cohesion: 0.18
Nodes (5): cargar_modelo(), generar_lote(), ids_parada(), test_generar_lote_es_greedy_con_padding_izquierdo_y_lo_restaura(), test_ids_parada_incluye_eos_y_marcas_de_turno()

### Community 48 - "Publicación en results"
Cohesion: 0.20
Nodes (5): faltantes(), publicar_todo(), CorridaFalsa, test_publicar_todo_no_publica_nada_si_falta_uno_y_dice_quien_lo_genera(), test_publicar_todo_publica_solo_si_estan_todos()

### Community 49 - "Correr brazos M3"
Cohesion: 0.19
Nodes (7): correr_brazo(), matriz_por_caso(), reloj_legible(), ResultadoBrazo, techo_union(), comunes(), test_reloj_legible()

### Community 50 - "Intervalos y F1"
Cohesion: 0.14
Nodes (9): accuracy(), baseline_clase_mayoritaria(), bootstrap_ic(), f1_por_clase(), macro_f1(), recall_clase_critica(), scorecard(), similitud_embeddings() (+1 more)

### Community 51 - "Generador HF (tests)"
Cohesion: 0.20
Nodes (4): generador_hf(), ModeloFalso, test_generador_hf_cuenta_tokens_y_apaga_el_adaptador_si_se_pide(), test_generador_hf_recorta_la_cola_y_anota_el_caso()

### Community 52 - "Tokenizadores"
Cohesion: 0.31
Nodes (6): cobertura_clasificador(), imprimir(), main(), medir(), _palabras(), _textos()

### Community 53 - "Publicación M1"
Cohesion: 0.18
Nodes (8): guardar_adaptador(), predicciones(), publicar_artefactos(), ModeloQueGuarda, test_guardar_adaptador_versiona_y_apunta_cual_es(), test_predicciones_tiene_lo_que_consumen_m2_y_m3(), test_publicar_artefactos_publica_todo_y_versiona_el_adaptador(), TokQueGuarda

### Community 56 - "se_abstuvo"
Cohesion: 0.22
Nodes (4): abstencion(), acierto_juridico(), acierto_por_caso(), se_abstuvo()

### Community 57 - "Fertilidad de tokenizadores"
Cohesion: 0.25
Nodes (6): fertilidad_tokenizadores(), medir_fertilidad(), test_fertilidad_tokenizadores_guarda_el_artefacto(), test_medir_fertilidad_ordena_y_registra_errores(), cargar(), TokFert

### Community 59 - "Reproducir"
Cohesion: 0.36
Nodes (4): _correr(), entorno(), _linea(), main()

### Community 60 - "Tesis y arquitecturas M3"
Cohesion: 0.22
Nodes (7): Bug heredado latencia_s_por_caso = 0.0 (conservado), Desviaciones respecto a los notebooks, Art. 6 Decreto 2591 de 1991 (arbol de decision), Agente: pasos censurados y veredicto_presupuesto, Coste: GPU local vs llamadas API (m3_costos.json), M3: cuatro arquitecturas sobre 103 casos comunes, Tesis: modelo pequeno afinado sobre art. 6 supera a la recuperacion

### Community 61 - "Reporte y corpus"
Cohesion: 0.28
Nodes (7): Corpus normativo (data/normas.json), Leonardo Galeano (abogado responsable del corpus), Apendice: cada cifra y su artefacto, Cobertura del corpus: techo de ranking, no de cobertura, Efectos adversos del RAG: abstencion indebida y citas incompletas, Recall en clases criticas (habeas_corpus, tutela), REPORTE: Triaje de acciones constitucionales colombianas

### Community 62 - "Publicación M2"
Cohesion: 0.32
Nodes (6): a_csv(), publicar(), _ctx_para_publicar(), test_publicar_no_publica_nada_si_falta_un_artefacto(), test_publicar_publica_los_diez_y_el_acuerdo_aparte(), test_publicar_sin_acuerdo_no_lo_publica()

### Community 63 - "Doc03 acción de cumplimiento"
Cohesion: 0.32
Nodes (6): doc03 Respuesta a derecho de peticion (cumplimiento, negativa a publicar contratos), Accion de cumplimiento (accion judicial anunciada por el peticionario), Alcaldia de Puerto Almendro (entidad ficticia, radicado SG-0987), Derecho de peticion, Ley 1712 de 2014, articulo 10 (deber de publicar contratos), SECOP (Sistema Electronico de Contratacion Publica)

### Community 64 - "entrenar"
Cohesion: 0.13
Nodes (8): comprobar_lora_b(), seleccionar_checkpoint(), entrenar(), ModeloLora, _Param, _SinLora, test_comprobar_lora_b(), test_seleccionar_checkpoint_documenta_la_mejor_epoca()

### Community 65 - "delta_con_sin_imagen"
Cohesion: 0.13
Nodes (11): delta_con_sin_imagen(), _media(), Delta: misma pregunta con imagen y sin ella, m01 no es estable (extractor de hechos de M3 no determinista), 1. Cómo se verificó, 2. Fortalezas, 4. Prioridades para Demo Day, 5. Cómo reproducir lo verificado (+3 more)

### Community 66 - "Doc02 oficio de planeación"
Cohesion: 0.29
Nodes (6): doc02 Oficio Planeación (imagen sintética del eval set M4), Oficio No. SPM-0412 (12 de agosto de 2026), Plazo de quince (15) días hábiles, Requerimiento por obra de construcción sin licencia, Secretaría de Planeación Municipal de Puerto Almendro (entidad ficticia), Traslado a la Inspección de Policía (consecuencia por incumplimiento)

### Community 67 - "Doc04 respuesta de la CAR"
Cohesion: 0.43
Nodes (7): doc04: Respuesta de la CAR a un derecho de petición (imagen del eval set M4), Corporación Autónoma Regional del Río Claro (CORPORIOCLARO, ficticia), Decisión: no adoptar medidas preventivas y archivar la queja, Junta de Acción Comunal de la vereda Los Naranjos (peticionaria), Sello 'Documento sintético / generado' (uso académico SI4006 · M4 · Amparo), Queja por vertimientos de curtiembre en la quebrada La Clara (fuente del acueducto veredal), Radicado CRCL-2231 (Villa Serena, 30 sep 2026)

### Community 68 - "Hallazgos de M1"
Cohesion: 0.29
Nodes (7): Escalera de fiabilidad de etiquetas (nivel_fiabilidad), Baseline de formato few-shot (41.7%), Capa de redaccion sin normas intrusas, Degeneracion de salidas (m1_degeneracion.json), Descomposicion del salto: razonamiento vs formato, M1: el sistema afinado (base, hibrido, afinado), Niveles de verificacion: plano, derivado, juicio

### Community 69 - "Hallazgos de M2"
Cohesion: 0.29
Nodes (7): Acierto juridico (metrica de cabecera), Acuerdo entre jueces (kappa 0.481), Sesgo de auto-preferencia condicionado a calidad, Determinismo del juez (resolucion del instrumento), Los dos jueces son de la misma familia (gpt-oss), M2: el evaluador, evaluado (sondas de sesgo), ROUGE-L contra acierto

### Community 70 - "m01 · doc01_respuesta_eps.png"
Cohesion: 0.14
Nodes (13): Leído del documento por un modelo de visión · no verificado, Leído del documento por un modelo de visión · no verificado, Leído del documento por un modelo de visión · no verificado, m01 · doc01_respuesta_eps.png, m06 · doc04_respuesta_car.png, m10 · doc06_notificacion_borrosa.jpg, Plan B · salida GRABADA de la corrida 20261101T194319Z, Por qué (+5 more)

### Community 71 - "metricas.py"
Cohesion: 0.15
Nodes (6): _anatomia_de_la_cola(), _cola_tras_el_bloque(), degeneracion(), ic_se_solapan(), _lcs(), rouge_l()

### Community 72 - "Jurisprudencia conocida"
Cohesion: 0.40
Nodes (3): _clave_sentencia(), _claves_jurisprudencia(), _jurisprudencia_conocida()

### Community 73 - "Doc01 respuesta EPS"
Cohesion: 0.40
Nodes (5): doc01_respuesta_eps.png (Respuesta a derecho de petición, EPS), EPS Salud Serena S.A.S. (entidad ficticia), Negación de autorización por falta de prestador contratado en la red, Procedimiento: reemplazo total de cadera derecha (ordenado por ortopedia), Respuesta a derecho de petición (radicado SS-AUT-0193)

### Community 74 - "Doc06 notificación borrosa"
Cohesion: 0.47
Nodes (5): doc06 Notificación por aviso borrosa (imagen eval M4), Inspección Municipal de Policía de Villa Serena (entidad ficticia), Marca DOCUMENTO SINTÉTICO / GENERADO (uso académico SI4006 M4 Amparo, sin validez jurídica), Notificación por aviso (procedimiento por comportamiento contrario a la convivencia), Plazo de descargos en días hábiles ocluido por mancha de tinta

### Community 76 - "m01 · doc01_respuesta_eps.png"
Cohesion: 0.14
Nodes (13): Leído del documento por un modelo de visión · no verificado, Leído del documento por un modelo de visión · no verificado, Leído del documento por un modelo de visión · no verificado, m01 · doc01_respuesta_eps.png, m06 · doc04_respuesta_car.png, m10 · doc06_notificacion_borrosa.jpg, Plan B · salida GRABADA de la corrida 20261101T203828Z, Por qué (+5 more)

### Community 77 - "Curva de pérdida"
Cohesion: 0.40
Nodes (3): graficar_perdida(), curva_de_perdida(), test_graficar_perdida_guarda_la_imagen()

### Community 78 - "m4_multimodal.py"
Cohesion: 0.19
Nodes (8): cargar_imagenes(), cronometrar(), _git(), preparar(), probar_ver(), tabla_casos(), test_cargar_imagenes_y_probar_ver(), test_preparar_para_sin_clave_y_crea_la_carpeta_de_la_corrida()

### Community 79 - "Doc05 notificación acueducto"
Cohesion: 0.50
Nodes (4): doc05 Notificacion de Suspension del Servicio de Acueducto (imagen sintetica), Acuerdo de pago como alternativa a la suspension, Aguas de Villa Serena S.A. E.S.P. (empresa ficticia de acueducto), Suspension del servicio publico domiciliario por saldo vencido (plazo 5 dias habiles)

### Community 81 - "correr_brazos"
Cohesion: 0.29
Nodes (4): transformador_para(), brazo_uno(), _cliente_groq(), correr_brazos()

### Community 86 - "test_scorecard.py"
Cohesion: 0.24
Nodes (9): carpeta(), _diag(), ejemplo(), test_diagnostico_campos_nombra_lo_que_leyo_mal(), test_diagnostico_exacto_con_json_no_culpa_a_una_sola_etapa(), test_diagnostico_exacto_sin_json(), test_diagnostico_juez_distingue_no_de_ambiguo(), test_diagnostico_ok_cuando_la_nota_es_1() (+1 more)

### Community 87 - "ctx"
Cohesion: 0.17
Nodes (4): cargar_lector(), AgenteFalso, ctx(), LectorFalso

### Community 89 - "construir_tabla_delta"
Cohesion: 0.20
Nodes (7): construir_tabla_delta(), tabla_markdown(), _tabla_y_guardar(), test_peor_caso_lista_todos_los_empatados_con_su_etapa(), test_tabla_delta_tiene_las_5_filas_con_metrica_nombrada(), test_tabla_delta_valores(), test_tabla_markdown_tiene_la_forma_de_la_plantilla_y_no_inventa_latencia()

### Community 90 - "LectorVisual"
Cohesion: 0.20
Nodes (3): LectorVisual, parsear_json(), test_parsear_json()

### Community 91 - "render_salida"
Cohesion: 0.25
Nodes (5): sesgo_autopreferencia(), mensajes_few_shot(), render_ejemplo(), render_entrada(), render_salida()

### Community 92 - "parse_salida"
Cohesion: 0.22
Nodes (4): adherencia_vocabulario(), coherencia(), depurar_citas(), parse_salida()

### Community 93 - "tabla_puente"
Cohesion: 0.25
Nodes (4): ids_eval_v1(), tabla_puente(), comparar(), harness_completo()

### Community 94 - "BM25"
Cohesion: 0.29
Nodes (3): BM25, texto_indexable(), _tok()

### Community 95 - "enchufar_m3"
Cohesion: 0.29
Nodes (3): enchufar_m3(), test_enchufar_m3_arma_amparo_y_guarda_el_manifiesto(), _Transformador

### Community 96 - "test_delta_repetido_cuenta_por_corrida_y_vacia_antes_de_cada_llamada"
Cohesion: 0.60
Nodes (5): _bloque(), _eval_repetido(), test_delta_repetido_cuenta_por_corrida_y_vacia_antes_de_cada_llamada(), m3(), test_delta_repetido_exige_vaciar_la_cache()

## Knowledge Gaps
- **32 isolated node(s):** `amparo`, `Checklist de anonimizacion (sin caras, nombres, cedulas, firmas ni sellos)`, `Entidades ficticias (EPS Salud Serena, Alcaldia de Puerto Almendro, CORPORIOCLARO, Aguas de Villa Serena)`, `INSTRUCCION_DOMINIO (5 campos JSON)`, `casos_m4.ejemplo.csv` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 586 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Harness de M4: decisiones de T5 y T6 (y T7)` connect `Decisiones del harness M4` to `Criterios del harness M4`, `delta_con_sin_imagen`, `json`, `correr_t6`, `casos_m4.csv: 11 casos sobre 6 imagenes`, `scorecard.py`, `se_abstuvo`, `construir_tabla_delta`, `corridas.py`, `Migración y sello`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **What connects `amparo`, `Checklist de anonimizacion (sin caras, nombres, cedulas, firmas ni sellos)`, `Entidades ficticias (EPS Salud Serena, Alcaldia de Puerto Almendro, CORPORIOCLARO, Aguas de Villa Serena)` to the rest of the system?**
  _32 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Criterios del harness M4` be split into smaller, more focused modules?**
  _Cohesion score 0.05256648113790971 - nodes in this community are weakly interconnected._
- **Why does `Migracion de notebooks a paquete Python amparo/` connect `Migración y sello` to `README y módulos`, `Decisiones del harness M4`, `Tesis y arquitecturas M3`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Should `Pipeline M3 RAG` be split into smaller, more focused modules?**
  _Cohesion score 0.09191919191919191 - nodes in this community are weakly interconnected._
- **Why does `Amparo: triaje de acciones constitucionales en Colombia` connect `README y módulos` to `Hallazgos de M1`, `Limitaciones y citas`, `Tesis y arquitecturas M3`, `Reporte y corpus`, `Migración y sello`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Should `test_pipeline_m4.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._