# Graph Report - Amparo  (2026-11-01)

## Corpus Check
- 73 files · ~146,924 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .ipynb 4, .csv 3, (none) 2)

## Summary
- 1482 nodes · 3171 edges · 86 communities (76 shown, 10 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 207 edges (avg confidence: 0.86)
- Token cost: 482,863 input · 0 output

## Community Hubs (Navigation)
- Imágenes y casos M4
- Criterios del harness M4
- Pipeline M3 RAG
- VLM y patrón input
- Tests del scorecard M4
- Métricas del dominio
- Pipeline M2 harness
- Scorecard y delta M4
- Pipeline M4 multimodal
- Acuerdo entre jueces (tests)
- Agente y costos
- Harness de tres dimensiones
- Tests del pipeline M1
- Pipeline M1 fine-tuning
- Entrenamiento LoRA
- Juez y familias de modelos
- Validación del eval set
- Términos procesales
- Índice de recuperación
- Baselines y generación M1
- Sistemas RAG de M3
- Corpus y evaluación retrieval
- Juez LLM (clase)
- Motor de reglas art. 6
- Estabilidad M1
- Plan y entrega M4
- Arranque y checkpoints
- Corridas (clase Corrida)
- Esquema del dominio
- RAGAS propio
- Estabilidad M2
- Migración y sello
- README y módulos
- Decisiones del harness M4
- Configuración y entorno
- Enchufe M3 brazo 4
- Datos de entrenamiento
- Brazo híbrido M1
- Limitaciones y citas
- Tests compartidos
- Tabla de costos
- Costo por brazo
- Capa de redacción
- Comparación entre corridas
- Collate y tokenizer (tests)
- Redacción M1
- Tests del pipeline M3
- Generación local HF
- Publicación en results
- Correr brazos M3
- Intervalos y F1
- Generador HF (tests)
- Tokenizadores
- Publicación M1
- Transformación de consulta
- Tests del enchufe
- Abstención y etiquetas
- Fertilidad de tokenizadores
- SistemaReglas y plazos
- Reproducir
- Tesis y arquitecturas M3
- Reporte y corpus
- Publicación M2
- Doc03 acción de cumplimiento
- Selección de checkpoint
- Delta con y sin imagen
- Doc02 oficio de planeación
- Doc04 respuesta de la CAR
- Hallazgos de M1
- Hallazgos de M2
- Reloj falso (tests)
- Degeneración de la salida
- Jurisprudencia conocida
- Doc01 respuesta EPS
- Doc06 notificación borrosa
- Corrida falsa M3
- Recorte de la cola
- Curva de pérdida
- Auto-preferencia del juez
- Doc05 notificación acueducto
- Sesgo de longitud
- Estrategia a transformador
- Proyecto (pyproject)

## God Nodes (most connected - your core abstractions)
1. `caso()` - 34 edges
2. `Contexto` - 28 edges
3. `parse_salida()` - 27 edges
4. `scorecard()` - 26 edges
5. `Contexto` - 26 edges
6. `Pipeline` - 26 edges
7. `Harness de M4: decisiones de T5 y T6 (y T7)` - 24 edges
8. `correr()` - 23 edges
9. `render_salida()` - 22 edges
10. `validar_casos()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `INSTRUCCION_DOMINIO (5 campos JSON)` --conceptually_related_to--> `ver()`  [INFERRED]
  m4/README_PLAN.md → amparo/multimodal/vlm.py
- `Criterio exacto (mecanismo final de M3)` --implements--> `nota_exacto()`  [INFERRED]
  m4/eval_set/FORMATO_CASOS.md → amparo/multimodal/criterios.py
- `Comparacion por fragmento en campos de texto libre` --rationale_for--> `_acierta_campo()`  [INFERRED]
  m4/eval_set/FORMATO_CASOS.md → amparo/multimodal/criterios.py
- `Criterio campos (JSON leido por el VLM)` --implements--> `nota_campos()`  [INFERRED]
  m4/eval_set/FORMATO_CASOS.md → amparo/multimodal/criterios.py
- `Criterio valvula (campos que deben venir null)` --implements--> `nota_valvula()`  [INFERRED]
  m4/eval_set/FORMATO_CASOS.md → amparo/multimodal/criterios.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Auditoria del juez LLM (validez, escala, acuerdo humano, familias, determinismo)** — readme_sonda_validez, readme_adherencia_escala_juez, reporte_juez_vs_abogado, reporte_acuerdo_entre_jueces, reporte_jueces_misma_familia, reporte_determinismo_juez, reporte_autopreferencia [INFERRED 0.85]
- **Sellado y trazabilidad de corridas (huella, manifiesto, sello, tag)** — readme_huella_codigo, subir_huella_manifiesto, subir_sello_subida, docs_migracion_tag_entrega_m4, docs_migracion_huella_amparo, reporte_origen_cifras [INFERRED 0.85]
- **Defecto de citas impertinentes: medicion, causa y mitigacion** — reporte_pertinencia_citas, reporte_fusion_fundamentos, reporte_capa_depuracion_citas, reporte_juez_vs_abogado [EXTRACTED 1.00]
- **Cuatro criterios del harness M4 (exacto, campos, valvula, juez_vlm)** — m4_eval_set_formato_casos_criterio_exacto, m4_eval_set_formato_casos_criterio_campos, m4_eval_set_formato_casos_criterio_valvula, m4_eval_set_formato_casos_criterio_juez_vlm, amparo_multimodal_criterios_calificar [EXTRACTED 1.00]
- **Invencion del plazo en m10 que la valvula no detecta** — m4_eval_set_casos_m4_m10, m4_eval_set_imagenes_anonimizacion_doc06_notificacion_borrosa, m4_notas_t6_lucas_hallazgo_invento_plazo_m10, m4_readme_peor_caso_m10, m4_eval_set_formato_casos_criterio_valvula [INFERRED 0.95]
- **Flujo input: ver() -> relato -> responder_m3 (brazo 4) -> motor de reglas** — amparo_multimodal_vlm_ver, amparo_multimodal_vlm_sistema_multimodal, amparo_multimodal_enchufe_construir_responder_m3, amparo_nucleo_reglas, m4_readme_plan_extraer_hechos_reglas_deciden [INFERRED 0.85]
- **Campos clave que el VLM debe extraer del oficio doc02** — m4_eval_set_imagenes_doc02_oficio_planeacion_oficio_spm_0412, m4_eval_set_imagenes_doc02_oficio_planeacion_requerimiento_obra_sin_licencia, m4_eval_set_imagenes_doc02_oficio_planeacion_plazo_15_dias_habiles, m4_eval_set_imagenes_doc02_oficio_planeacion_traslado_inspeccion_policia [INFERRED 0.85]
- **Renuencia documentada: peticion bajo Ley 1712 art. 10, negativa de la entidad, base para accion de cumplimiento** — m4_eval_set_imagenes_doc03_respuesta_cumplimiento_derecho_de_peticion, m4_eval_set_imagenes_doc03_respuesta_cumplimiento_ley_1712_2014_art_10, m4_eval_set_imagenes_doc03_respuesta_cumplimiento_negativa_actualizacion_tecnologica, m4_eval_set_imagenes_doc03_respuesta_cumplimiento_accion_de_cumplimiento [INFERRED 0.85]
- **Campos del oficio que el VLM debe extraer (entidad, radicado, peticionario, asunto, decisión)** — m4_eval_set_imagenes_doc04_respuesta_car_corporioclaro, m4_eval_set_imagenes_doc04_respuesta_car_radicado_crcl_2231, m4_eval_set_imagenes_doc04_respuesta_car_jac_los_naranjos, m4_eval_set_imagenes_doc04_respuesta_car_queja_vertimientos_la_clara, m4_eval_set_imagenes_doc04_respuesta_car_decision_archivo_sin_medidas [INFERRED 0.85]
- **Caso de prueba: dato crítico (plazo) ilegible por degradación, esperando que el VLM no invente el número** — m4_eval_set_imagenes_doc06_notificacion_borrosa, m4_eval_set_imagenes_doc06_notificacion_borrosa_plazo_descargos_ocluido, m4_eval_set_imagenes_doc06_notificacion_borrosa_degradaciones_foto_simulada [INFERRED 0.75]

## Communities (86 total, 10 thin omitted)

### Community 0 - "Imágenes y casos M4"
Cohesion: 0.06
Nodes (52): casos_m4.csv: 11 casos sobre 6 imagenes, m01 - exacto: tutela (EPS niega cirugia), m02 - campos sobre doc01 (cadera), m03 - campos sobre doc02 (plazo_dias 15), m04 - exacto: accion_cumplimiento (Ley 1712), m05 - campos sobre doc03 (contratos), m06 - exacto: accion_popular (cuatro veredas), m07 - campos sobre doc04 (entidad 'claro') (+44 more)

### Community 1 - "Criterios del harness M4"
Cohesion: 0.07
Nodes (53): _acierta_campo(), calificar(), _entero(), _es_nulo(), _esperado_campos(), _esperado_exacto(), _esperado_juez_vlm(), _esperado_valvula() (+45 more)

### Community 2 - "Pipeline M3 RAG"
Cohesion: 0.08
Nodes (29): auditar_corpus(), brazo_uno(), _cargar_ck(), chunking(), cierre(), _ck_guardar(), _cliente_groq(), comparar() (+21 more)

### Community 3 - "VLM y patrón input"
Cohesion: 0.06
Nodes (25): armar_relato(), armar_relato(), cargar(), cargar_vlm(), cronometrar(), dispositivo(), lector(), ver_ligada() (+17 more)

### Community 4 - "Tests del scorecard M4"
Cohesion: 0.10
Nodes (32): carpeta(), casos_validos(), correr(), _diag(), ejemplo(), Pipeline, _rutas(), test_armar_relato_sin_json_usa_el_texto_crudo() (+24 more)

### Community 5 - "Métricas del dominio"
Cohesion: 0.08
Nodes (18): accuracy(), acierto_juridico(), acierto_por_caso(), adherencia_vocabulario(), alucinacion_normativa(), baseline_clase_mayoritaria(), clasificar_cita(), coherencia() (+10 more)

### Community 6 - "Pipeline M2 harness"
Cohesion: 0.07
Nodes (19): cargar(), acuerdo_entre_jueces(), cargar_salidas(), Contexto, correr(), elegir_juez(), filas_por_caso(), formato_vocabulario() (+11 more)

### Community 7 - "Scorecard y delta M4"
Cohesion: 0.09
Nodes (20): cargar_guardado(), construir_tabla_delta(), correr_t6(), guardar(), leer_fila_m3(), _media(), tabla_desde_disco(), tabla_markdown() (+12 more)

### Community 8 - "Pipeline M4 multimodal"
Cohesion: 0.10
Nodes (18): cargar_imagenes(), cargar_modelo(), Contexto, correr(), correr_harness(), delta_imagen(), descargar(), enchufar_m3() (+10 more)

### Community 9 - "Acuerdo entre jueces (tests)"
Cohesion: 0.11
Nodes (17): medir(), puntuar_muestra(), ClienteFalso, _fabrica(), construir(), JuezFalso, test_cada_artefacto_se_guarda_en_el_codigo_antes_de_publicarse(), test_elegir_juez_cae_a_un_alternativo_y_para_si_no_hay_ninguno() (+9 more)

### Community 10 - "Agente y costos"
Cohesion: 0.10
Nodes (5): Costos, abstenerse(), Agente, SistemaHibrido, SistemaRAG

### Community 11 - "Harness de tres dimensiones"
Cohesion: 0.08
Nodes (16): acierto_por_item(), acuerdo_entre_jueces(), adherencia_a_la_rubrica(), cohen_kappa(), guardar(), harness(), ids_eval_v1(), _lectura_familias() (+8 more)

### Community 12 - "Tests del pipeline M1"
Cohesion: 0.11
Nodes (16): _celdas_codigo(), _ic(), LoraConfigFalsa, ModeloLora, _Param, _publicaciones_literales(), _SinLora, test_cada_artefacto_se_guarda_en_el_codigo_antes_de_publicarse() (+8 more)

### Community 13 - "Pipeline M1 fine-tuning"
Cohesion: 0.12
Nodes (13): ic_se_solapan(), cerrar(), cobertura_clasificador(), comparar_con_base(), Contexto, correr(), _imprimir_quien_decide(), notas_de_cierre() (+5 more)

### Community 14 - "Entrenamiento LoRA"
Cohesion: 0.11
Nodes (12): aplicar_lora(), callbacks_parada(), crear_trainer(), filtrar_hiperparametros(), guardar_adaptador(), hiperparametros(), registro_hiperparametros(), aplicar_lora() (+4 more)

### Community 15 - "Juez y familias de modelos"
Cohesion: 0.11
Nodes (10): candidatos(), _degradar(), experimento_inyeccion(), familia_de(), orden_de_candidatos(), clave(), respuesta_floja(), tamano_declarado() (+2 more)

### Community 16 - "Validación del eval set"
Cohesion: 0.17
Nodes (15): cargar_casos(), validar_casos(), validar_eval_set(), _con(), escribir_csv(), filas_validas(), test_cargar_casos_tolera_bom_de_excel(), test_csv_de_ejemplo_para_lucas_es_valido_y_cubre_los_cuatro_criterios() (+7 more)

### Community 17 - "Términos procesales"
Cohesion: 0.15
Nodes (8): calcular_termino(), contar_habiles(), es_habil(), festivos(), leer_fecha(), _lunes_siguiente(), pascua(), sumar_habiles()

### Community 18 - "Índice de recuperación"
Cohesion: 0.15
Nodes (3): BM25, Indice, texto_indexable()

### Community 19 - "Baselines y generación M1"
Cohesion: 0.10
Nodes (13): imprimir(), generar_lote(), demostraciones_few_shot(), abstencion_validation(), baseline(), baseline_few_shot(), evaluar_ajustado(), _generar_y_puntuar() (+5 more)

### Community 20 - "Sistemas RAG de M3"
Cohesion: 0.12
Nodes (10): con_pregunta_triable(), leer_triable(), cita_completa(), extraer_hechos(), formatear_contexto(), generador_groq(), generar(), _json_de() (+2 more)

### Community 21 - "Corpus y evaluación retrieval"
Cohesion: 0.14
Nodes (10): _cita_de(), citas_esperadas(), comparar_chunking(), comparar_estrategias(), cubre(), elegir_estrategia(), evaluar_recuperacion(), _percentil() (+2 more)

### Community 22 - "Juez LLM (clase)"
Cohesion: 0.17
Nodes (3): _envolver(), Juez, puntuar_lote()

### Community 23 - "Motor de reglas art. 6"
Cohesion: 0.15
Nodes (8): decidir(), Decision, estrato_verificacion(), explicar(), Hechos, pivota_en_juicio(), motor_reglas(), _json_de()

### Community 24 - "Estabilidad M1"
Cohesion: 0.11
Nodes (9): comparar_con_previa(), estabilidad(), CorridaFalsa, ctx(), _previa(), test_comparar_con_previa_identicas_y_codigo_distinto(), test_comparar_con_previa_sin_artefactos_no_es_concluyente(), test_estabilidad_con_previa_guarda_y_publica() (+1 more)

### Community 25 - "Plan y entrega M4"
Cohesion: 0.11
Nodes (15): Corrida local T6 (RTX 5060, M3 sustituto), M4 - Amparo ya ve (README de entrega), Tabla M3 (n=120, 0.675) vs M4 (n=3, 1.0), Corrida oficial en Colab (T4), T7 - Enchufe real de M3, M4 Plan de trabajo - Su sistema ya ve, Qwen2-VL-2B-Instruct, Reparto de tareas T1-T9 (Santiago, Lucas, Nico, Martin/Tomas) (+7 more)

### Community 26 - "Arranque y checkpoints"
Cohesion: 0.15
Nodes (8): cargar_checkpoint(), celda(), _en_colab(), guardar_checkpoint(), humo(), _procedencia(), version_codigo(), version_datos()

### Community 28 - "Esquema del dominio"
Cohesion: 0.16
Nodes (9): experimento_validez(), cargar_normas(), mensajes_few_shot(), planos_normativos(), render_ejemplo(), render_entrada(), render_salida(), separar_planos() (+1 more)

### Community 29 - "RAGAS propio"
Cohesion: 0.19
Nodes (10): _encoder(), citas(), answer_relevancy(), context_precision_exacta(), context_precision_juez(), context_recall_exacto(), evaluar(), faithfulness_exacta() (+2 more)

### Community 30 - "Estabilidad M2"
Cohesion: 0.13
Nodes (7): corridas_previas(), estabilidad(), _corrida_previa(), CorridaFalsa, test_corridas_previas_salta_las_de_control_y_las_sin_scorecard(), test_estabilidad_atribuye_codigo_y_predicciones_de_m1(), test_estabilidad_sin_corrida_previa_es_none_y_no_true()

### Community 31 - "Migración y sello"
Cohesion: 0.16
Nodes (12): Logica extraida de los notebooks a modulos, Fuera de alcance: despliegue y reentrenamiento, Migracion de notebooks a paquete Python amparo/, Tag entrega-m4 (commit d158742), Verificacion: linea base antes y despues de migrar, Estructura del paquete amparo/, Huella del codigo y version de datos por corrida, De donde salen las cifras (corridas y huellas) (+4 more)

### Community 32 - "README y módulos"
Cohesion: 0.16
Nodes (12): Amparo: triaje de acciones constitucionales en Colombia, M1: fine-tuning LoRA de Qwen2.5-7B-Instruct, M2: harness con LLM-as-a-judge y cinco sondas, M3: cuatro arquitecturas (fine-tuned, RAG basico, RAG avanzado, agente + reglas), M4: componente visual Qwen2-VL-2B (patron input), reproducir.py: entrada unica de reproduccion, Estabilidad entre corridas (m1_estabilidad.json), groq (juez y agente via API) (+4 more)

### Community 33 - "Decisiones del harness M4"
Cohesion: 0.16
Nodes (5): correr_harness(), leer_latencia_m3(), Harness de M4: decisiones de T5 y T6 (y T7), test_latencia_m3_es_por_caso_y_no_por_llamada(), test_leer_latencia_m3()

### Community 34 - "Configuración y entorno"
Cohesion: 0.17
Nodes (4): _raiz(), nueva(), preparar(), verificar_sello()

### Community 35 - "Enchufe M3 brazo 4"
Cohesion: 0.15
Nodes (9): chunking_de_m3(), comprobar_brazo(), construir_responder_m3(), cargar_corpus(), trocear_fijo(), Brazo 4 - agente + reglas (M3), test_el_brazo_enchufado_existe_en_el_scorecard_de_m3(), test_el_chunking_es_el_que_eligio_m3() (+1 more)

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
Cohesion: 0.19
Nodes (8): cargar_clave_groq(), cargar_m1(), _salida(), test_cargar_clave_groq_fuera_de_colab_y_sin_pedir_devuelve_false(), test_cargar_clave_groq_respeta_la_del_entorno(), test_cargar_m1_desenvuelve_datos_y_conserva_la_corrida(), test_cargar_m1_exige_el_mismo_orden_que_el_eval_set(), test_recortar_quita_la_cola_degenerada()

### Community 40 - "Tabla de costos"
Cohesion: 0.14
Nodes (5): BrazoNoMedido, Cronometro, imprimir(), tabla(), test_brazo_no_medido_sale_en_none_y_no_en_cero()

### Community 41 - "Costo por brazo"
Cohesion: 0.19
Nodes (4): CostoPorBrazo, test_costo_por_brazo_cuenta_reales_y_cache_y_cronometra_solo_las_reales(), test_costo_por_brazo_reparte_el_contador_compartido(), TransformadorFalso

### Community 42 - "Capa de redacción"
Cohesion: 0.19
Nodes (6): citas_en_texto(), citas_de(), construir_prompt(), redactar(), _texto_pivote(), verificar_texto()

### Community 43 - "Comparación entre corridas"
Cohesion: 0.18
Nodes (5): comparar(), hardware(), listar(), ultimas(), versiones()

### Community 44 - "Collate y tokenizer (tests)"
Cohesion: 0.15
Nodes (4): collate_para(), _Enc, test_collate_rellena_a_la_derecha_con_pad_0_y_menos_100(), TokFalso

### Community 45 - "Redacción M1"
Cohesion: 0.15
Nodes (7): medir(), _imprimir_redaccion(), redaccion(), HibridoFalso, _salida(), test_redaccion_con_generador_redacta_sobre_el_ajustado(), test_redaccion_sin_clave_queda_registrada_como_no_medida()

### Community 46 - "Tests del pipeline M3"
Cohesion: 0.22
Nodes (5): _ctx(), _salida(), SistemaFalso, test_correr_brazos_sin_gpu_corre_el_agente_y_el_brazo_uno(), test_un_brazo_corrido_se_guarda_en_el_checkpoint_y_se_reutiliza()

### Community 47 - "Generación local HF"
Cohesion: 0.18
Nodes (5): sembrar(), cargar_modelo(), ids_parada(), cargar_modelo(), test_ids_parada_incluye_eos_y_marcas_de_turno()

### Community 48 - "Publicación en results"
Cohesion: 0.20
Nodes (5): faltantes(), publicar_todo(), CorridaFalsa, test_publicar_todo_no_publica_nada_si_falta_uno_y_dice_quien_lo_genera(), test_publicar_todo_publica_solo_si_estan_todos()

### Community 49 - "Correr brazos M3"
Cohesion: 0.21
Nodes (7): correr_brazo(), matriz_por_caso(), reloj_legible(), ResultadoBrazo, techo_union(), test_matriz_por_caso_y_techo_de_la_union(), test_reloj_legible()

### Community 50 - "Intervalos y F1"
Cohesion: 0.17
Nodes (6): sesgo_autopreferencia(), bootstrap_ic(), f1_por_clase(), macro_f1(), recall_clase_critica(), _wilson()

### Community 51 - "Generador HF (tests)"
Cohesion: 0.20
Nodes (4): generador_hf(), ModeloFalso, test_generador_hf_cuenta_tokens_y_apaga_el_adaptador_si_se_pide(), test_generador_hf_recorta_la_cola_y_anota_el_caso()

### Community 52 - "Tokenizadores"
Cohesion: 0.33
Nodes (6): cobertura_clasificador(), imprimir(), main(), medir(), _palabras(), _textos()

### Community 53 - "Publicación M1"
Cohesion: 0.20
Nodes (7): predicciones(), publicar_artefactos(), ModeloQueGuarda, test_guardar_adaptador_versiona_y_apunta_cual_es(), test_predicciones_tiene_lo_que_consumen_m2_y_m3(), test_publicar_artefactos_publica_todo_y_versiona_el_adaptador(), TokQueGuarda

### Community 55 - "Tests del enchufe"
Cohesion: 0.29
Nodes (5): _responder(), test_el_mecanismo_lo_decide_el_motor(), test_la_etiqueta_es_la_del_brazo(), test_responde_en_el_formato_de_amparo(), _Transformador

### Community 56 - "Abstención y etiquetas"
Cohesion: 0.22
Nodes (5): abstencion(), adherencia_estructural(), etiquetas_presentes(), _norm(), se_abstuvo()

### Community 57 - "Fertilidad de tokenizadores"
Cohesion: 0.25
Nodes (6): fertilidad_tokenizadores(), medir_fertilidad(), test_fertilidad_tokenizadores_guarda_el_artefacto(), test_medir_fertilidad_ordena_y_registra_errores(), cargar(), TokFert

### Community 59 - "Reproducir"
Cohesion: 0.39
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

### Community 64 - "Selección de checkpoint"
Cohesion: 0.29
Nodes (4): comprobar_lora_b(), seleccionar_checkpoint(), entrenar(), test_seleccionar_checkpoint_documenta_la_mejor_epoca()

### Community 65 - "Delta con y sin imagen"
Cohesion: 0.33
Nodes (4): delta_con_sin_imagen(), Delta: misma pregunta con imagen y sin ella, m01 no es estable (extractor de hechos de M3 no determinista), test_delta_con_sin_imagen_separa_lo_que_aporta_de_lo_que_no()

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

### Community 70 - "Reloj falso (tests)"
Cohesion: 0.29
Nodes (3): Reloj, test_correr_brazo_latencia_por_caso(), test_correr_brazo_tolera_un_fallo_de_api_con_salida_vacia()

### Community 71 - "Degeneración de la salida"
Cohesion: 0.33
Nodes (3): _anatomia_de_la_cola(), _cola_tras_el_bloque(), degeneracion()

### Community 72 - "Jurisprudencia conocida"
Cohesion: 0.40
Nodes (3): _clave_sentencia(), _claves_jurisprudencia(), _jurisprudencia_conocida()

### Community 73 - "Doc01 respuesta EPS"
Cohesion: 0.40
Nodes (5): doc01_respuesta_eps.png (Respuesta a derecho de petición, EPS), EPS Salud Serena S.A.S. (entidad ficticia), Negación de autorización por falta de prestador contratado en la red, Procedimiento: reemplazo total de cadera derecha (ordenado por ortopedia), Respuesta a derecho de petición (radicado SS-AUT-0193)

### Community 74 - "Doc06 notificación borrosa"
Cohesion: 0.47
Nodes (5): doc06 Notificación por aviso borrosa (imagen eval M4), Inspección Municipal de Policía de Villa Serena (entidad ficticia), Marca DOCUMENTO SINTÉTICO / GENERADO (uso académico SI4006 M4 Amparo, sin validez jurídica), Notificación por aviso (procedimiento por comportamiento contrario a la convivencia), Plazo de descargos en días hábiles ocluido por mancha de tinta

### Community 76 - "Recorte de la cola"
Cohesion: 0.40
Nodes (3): recortar(), generar(), recortar_al_bloque()

### Community 77 - "Curva de pérdida"
Cohesion: 0.40
Nodes (3): graficar_perdida(), curva_de_perdida(), test_graficar_perdida_guarda_la_imagen()

### Community 78 - "Auto-preferencia del juez"
Cohesion: 0.40
Nodes (3): autopreferencia(), respuestas_familia(), test_respuestas_familia_usa_el_cache_en_la_segunda_pasada()

### Community 79 - "Doc05 notificación acueducto"
Cohesion: 0.50
Nodes (4): doc05 Notificacion de Suspension del Servicio de Acueducto (imagen sintetica), Acuerdo de pago como alternativa a la suspension, Aguas de Villa Serena S.A. E.S.P. (empresa ficticia de acueducto), Suspension del servicio publico domiciliario por saldo vencido (plazo 5 dias habiles)

## Knowledge Gaps
- **31 isolated node(s):** `amparo`, `Leonardo Galeano (abogado responsable del corpus)`, `Baseline de formato few-shot (41.7%)`, `Degeneracion de salidas (m1_degeneracion.json)`, `Capa de redaccion sin normas intrusas` (+26 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 532 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Harness de M4: decisiones de T5 y T6 (y T7)` connect `Decisiones del harness M4` to `Imágenes y casos M4`, `Criterios del harness M4`, `Delta con y sin imagen`, `VLM y patrón input`, `Enchufe M3 brazo 4`, `Métricas del dominio`, `Scorecard y delta M4`, `Validación del eval set`, `Arranque y checkpoints`, `Migración y sello`?**
  _High betweenness centrality (0.132) - this node is a cross-community bridge._
- **What connects `amparo`, `Leonardo Galeano (abogado responsable del corpus)`, `Baseline de formato few-shot (41.7%)` to the rest of the system?**
  _31 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Imágenes y casos M4` be split into smaller, more focused modules?**
  _Cohesion score 0.061938061938061936 - nodes in this community are weakly interconnected._
- **Why does `Migracion de notebooks a paquete Python amparo/` connect `Migración y sello` to `README y módulos`, `Decisiones del harness M4`, `Tesis y arquitecturas M3`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Should `Criterios del harness M4` be split into smaller, more focused modules?**
  _Cohesion score 0.06918918918918919 - nodes in this community are weakly interconnected._
- **Why does `Amparo: triaje de acciones constitucionales en Colombia` connect `README y módulos` to `Hallazgos de M1`, `Limitaciones y citas`, `Tesis y arquitecturas M3`, `Reporte y corpus`, `Migración y sello`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Should `Pipeline M3 RAG` be split into smaller, more focused modules?**
  _Cohesion score 0.07826694619147449 - nodes in this community are weakly interconnected._