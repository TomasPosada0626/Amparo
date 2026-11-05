# Graph Report - Amparo  (2026-11-03)

## Corpus Check
- 99 files · ~226,303 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .ipynb 6, .csv 5, (none) 3)

## Summary
- 2077 nodes · 4633 edges · 117 communities (101 shown, 16 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 267 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7bae9009`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- generar_imagenes.py
- test_criterios.py
- m3_rag.py
- test_pipeline_m4.py
- Pipeline
- brazos.py
- Contexto
- csv
- despliegue.py
- medir
- seleccionar_checkpoint
- Agente
- preparar_dataset
- m1_finetuning.py
- entrenamiento.py
- casos_m4.csv: 11 casos sobre 6 imagenes
- arranque.py
- terminos.py
- Indice
- redaccion
- publicar_artefactos
- recuperacion.py
- Juez
- Hechos
- CorridaFalsa
- M4 - Amparo ya ve (README de entrega)
- test_multimodal.py
- test_despliegue.py
- test_scorecard.py
- re
- CorridaFalsa
- Migracion de notebooks a paquete Python amparo/
- Amparo: triaje de acciones constitucionales en Colombia
- Harness de M4: decisiones de T5 y T6 (y T7)
- Contexto
- pathlib
- datos.py
- brazo_hibrido
- Limitaciones: lo que este trabajo no puede concluir
- test_pipeline_m1.py
- costos.py
- test_despliegue.py
- sistema_visual.py
- corrida_m4.py
- render_salida
- T6 - Corrida del harness: notas para T8 (Lucas -> Nico)
- Corrida
- imprimir
- publicar_todo
- familia_de
- json
- TokFalso
- schema.py
- _ctx_medido
- TransformadorConsulta
- Agente
- citas
- correr_con_reloj
- acuerdo_entre_jueces
- M3: cuatro arquitecturas sobre 103 casos comunes
- REPORTE: Triaje de acciones constitucionales colombianas
- _ProfesorFalso
- doc03 Respuesta a derecho de peticion (cumplimiento, negativa a publicar contratos)
- medir
- delta_con_sin_imagen
- Oficio No. SPM-0412 (12 de agosto de 2026)
- doc04: Respuesta de la CAR a un derecho de petición (imagen del eval set M4)
- M1: el sistema afinado (base, hibrido, afinado)
- M2: el evaluador, evaluado (sondas de sesgo)
- m01 · doc01_respuesta_eps.png
- test_pipeline_m2.py
- metricas.py
- doc01_respuesta_eps.png (Respuesta a derecho de petición, EPS)
- doc06 Notificación por aviso borrosa (imagen eval M4)
- cargar_checkpoint
- m01 · doc01_respuesta_eps.png
- agente_estudiante
- Contexto
- doc05 Notificacion de Suspension del Servicio de Acueducto (imagen sintetica)
- JuezFalso
- m5_destilacion.py
- consultar
- autoprueba_integracion.py
- amparo
- test_de_punta_a_punta_sobre_el_eval_set_real
- redaccion.py
- correr_t6
- scorecard.py
- m5_cuantizacion.py
- test_pipeline_m3.py
- cargar_normas
- t_sonda_validez_ejecuta
- ctx
- t_inyeccion_sin_api
- reproducibilidad
- consultar_res
- t_reporte_no_afirma_de_mas
- time
- recortar_al_bloque
- comparar_con_previa
- latencia_por_componente
- test_compartidos.py
- ModeloFalso
- enchufar_m3
- test_pipeline_m5.py
- inyeccion
- leer_latencia_m3
- SinVision
- T7 - Enchufe real de M3
- m4_multimodal.py
- _Encoder
- collate_para
- _Enc
- t_salidas_fuera_de_la_huella
- test_los_notebooks_de_m4_clonan_demo_final

## God Nodes (most connected - your core abstractions)
1. `prueba()` - 77 edges
2. `parse_salida()` - 42 edges
3. `render_salida()` - 34 edges
4. `caso()` - 34 edges
5. `scorecard()` - 30 edges
6. `Hechos` - 29 edges
7. `Contexto` - 28 edges
8. `Agente` - 28 edges
9. `_cargar()` - 28 edges
10. `Contexto` - 26 edges

## Surprising Connections (you probably didn't know these)
- `Dónde está hoy el recorrido completo` --references--> `construir_responder_m3()`  [INFERRED]
  review/m4/PLAN_DEMO.md → amparo/multimodal/enchufe.py
- `H1 · El delta con/sin imagen no mide latencia` --references--> `delta_con_sin_imagen()`  [INFERRED]
  review/m4/README.md → amparo/multimodal/scorecard.py
- `Resultado: el contrato NO se cumple (3 de 5)` --references--> `latencias()`  [INFERRED]
  m5/README.md → amparo/pipelines/m5_cuantizacion.py
- `S15 · Parte B · La app` --references--> `config_desde_entorno()`  [INFERRED]
  m5/README.md → amparo/despliegue.py
- `S15 · Parte B · La app` --references--> `consultar()`  [INFERRED]
  m5/README.md → amparo/despliegue.py

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

## Communities (117 total, 16 thin omitted)

### Community 0 - "generar_imagenes.py"
Cohesion: 0.19
Nodes (14): doc01_respuesta_eps(), doc02_oficio_planeacion(), doc03_respuesta_cumplimiento(), doc04_respuesta_car(), doc05_notificacion_acueducto(), doc06_notificacion_borrosa(), encabezado(), F() (+6 more)

### Community 1 - "test_criterios.py"
Cohesion: 0.05
Nodes (71): _acierta_campo(), advertencias_lectura(), calificar(), cargar_casos(), _entero(), _es_nulo(), _esperado_campos(), _esperado_exacto() (+63 more)

### Community 2 - "m3_rag.py"
Cohesion: 0.10
Nodes (20): auditar_corpus(), brazo_uno(), cierre(), _ck_guardar(), _cliente_groq(), comprobar_ragas(), comunes(), consultas_fallidas() (+12 more)

### Community 3 - "test_pipeline_m4.py"
Cohesion: 0.10
Nodes (13): ClienteGuionado, _correr(), _Fn, IndiceFalso, main(), _Msg, _Resp, _TC (+5 more)

### Community 4 - "Pipeline"
Cohesion: 0.15
Nodes (15): casos_validos(), correr(), Pipeline, test_cada_imagen_se_carga_una_vez(), test_cronometro_mide_ver_mas_m3_y_deja_fuera_carga_y_juez(), test_csv_invalido_no_corre_nada(), test_excepcion_del_sistema_detiene_la_corrida(), test_guardar_escribe_scorecard_y_trazas() (+7 more)

### Community 5 - "brazos.py"
Cohesion: 0.07
Nodes (15): correr_brazo(), CostoPorBrazo, matriz_por_caso(), reloj_legible(), ResultadoBrazo, techo_union(), transformador_para(), Reloj (+7 more)

### Community 6 - "Contexto"
Cohesion: 0.12
Nodes (10): sesgo_posicion(), acuerdo_entre_jueces(), autopreferencia(), Contexto, respuestas_familia(), rouge_vs_acierto(), sesgo_longitud(), sesgo_posicion() (+2 more)

### Community 7 - "csv"
Cohesion: 0.17
Nodes (8): cargar_guardado(), delta_repetido(), guardar(), _mediana(), _schema_mecanismo(), tabla_desde_disco(), 5. Cómo reproducir lo verificado, test_cargar_guardado_devuelve_lo_mismo_que_se_guardo()

### Community 8 - "despliegue.py"
Cohesion: 0.14
Nodes (14): armar_amparo(), cargar_indice(), _chunks_de_m3(), formatear_para_usuario(), health(), _huella(), precalcular_indice(), _SinVision (+6 more)

### Community 9 - "medir"
Cohesion: 0.23
Nodes (9): medir(), adherencia_a_la_rubrica(), ClienteFalso, _fabrica(), test_medir_elige_el_primer_candidato_limpio_de_otra_familia(), test_medir_exige_los_25_sin_huecos_y_conserva_al_de_otra_familia(), test_medir_para_si_el_juez_principal_no_puntua(), test_medir_sin_ninguno_limpio_usa_el_menos_malo_y_lo_declara() (+1 more)

### Community 10 - "seleccionar_checkpoint"
Cohesion: 0.20
Nodes (5): comprobar_lora_b(), ModeloLora, _Param, _SinLora, test_comprobar_lora_b()

### Community 11 - "Agente"
Cohesion: 0.10
Nodes (7): abstenerse(), con_pregunta_triable(), leer_triable(), Agente, _json_de(), _prompt_hechos(), t_abstencion_del_motor()

### Community 13 - "m1_finetuning.py"
Cohesion: 0.05
Nodes (30): sembrar(), cargar_modelo(), generar_lote(), demostraciones_few_shot(), abstencion_validation(), aplicar_lora(), baseline(), baseline_few_shot() (+22 more)

### Community 14 - "entrenamiento.py"
Cohesion: 0.10
Nodes (13): aplicar_lora(), callbacks_parada(), crear_trainer(), filtrar_hiperparametros(), graficar_perdida(), hiperparametros(), registro_hiperparametros(), seleccionar_checkpoint() (+5 more)

### Community 15 - "casos_m4.csv: 11 casos sobre 6 imagenes"
Cohesion: 0.13
Nodes (25): casos_m4.csv: 11 casos sobre 6 imagenes, m01 - exacto: tutela (EPS niega cirugia), m02 - campos sobre doc01 (cadera), m03 - campos sobre doc02 (plazo_dias 15), m04 - exacto: accion_cumplimiento (Ley 1712), m05 - campos sobre doc03 (contratos), m06 - exacto: accion_popular (cuatro veredas), m07 - campos sobre doc04 (entidad 'claro') (+17 more)

### Community 16 - "arranque.py"
Cohesion: 0.17
Nodes (7): celda(), _en_colab(), guardar_checkpoint(), humo(), _procedencia(), version_codigo(), version_datos()

### Community 17 - "terminos.py"
Cohesion: 0.08
Nodes (21): calcular_termino(), contar_habiles(), es_habil(), festivos(), leer_fecha(), _lunes_siguiente(), pascua(), sumar_habiles() (+13 more)

### Community 18 - "Indice"
Cohesion: 0.15
Nodes (4): BM25, Indice, texto_indexable(), _tok()

### Community 19 - "redaccion"
Cohesion: 0.13
Nodes (9): medir(), _imprimir_redaccion(), redaccion(), HibridoFalso, _salida(), generar_lote(), test_legibles_cuenta_mecanismos_parseables(), test_redaccion_con_generador_redacta_sobre_el_ajustado() (+1 more)

### Community 20 - "publicar_artefactos"
Cohesion: 0.29
Nodes (5): guardar_adaptador(), ModeloQueGuarda, test_guardar_adaptador_versiona_y_apunta_cual_es(), test_publicar_artefactos_publica_todo_y_versiona_el_adaptador(), TokQueGuarda

### Community 21 - "recuperacion.py"
Cohesion: 0.12
Nodes (9): chunking(), recuperacion(), citas_esperadas(), comparar_chunking(), comparar_estrategias(), elegir_estrategia(), evaluar_recuperacion(), _percentil() (+1 more)

### Community 22 - "Juez"
Cohesion: 0.15
Nodes (4): _envolver(), Juez, puntuar_lote(), elegir_juez()

### Community 23 - "Hechos"
Cohesion: 0.14
Nodes (11): decidir(), Decision, estrato_verificacion(), explicar(), Hechos, pivota_en_juicio(), t_dataset_hechos(), t_estratos() (+3 more)

### Community 25 - "M4 - Amparo ya ve (README de entrega)"
Cohesion: 0.15
Nodes (12): M4 - Amparo ya ve (README de entrega), Brazo 4 - agente + reglas (M3), Tabla M3 (n=120, 0.675) vs M4 (n=3, 1.0), M4 Plan de trabajo - Su sistema ya ve, Qwen2-VL-2B-Instruct, Reparto de tareas T1-T9 (Santiago, Lucas, Nico, Martin/Tomas), Rubrica M4 (10 puntos), S13_Lab_Integracion_Visual_RESUELTO.ipynb (plantilla base) (+4 more)

### Community 26 - "test_multimodal.py"
Cohesion: 0.10
Nodes (21): Amparo, armar_relato(), formatear(), por_que(), _bloque(), _eval_repetido(), LectorFalso, _m3() (+13 more)

### Community 27 - "test_despliegue.py"
Cohesion: 0.17
Nodes (8): config_desde_entorno(), test_armar_en_zerogpu_precarga_m3_y_carga_el_vlm_sin_device_map(), test_config_desde_entorno(), test_config_rechaza_un_vlm_desconocido(), test_plantilla_por_mecanismo(), test_share_solo_con_la_variable(), test_sin_zerogpu_no_se_activa(), test_zerogpu_usa_fp16_aunque_torch_no_vea_gpu()

### Community 28 - "test_scorecard.py"
Cohesion: 0.20
Nodes (11): carpeta(), _diag(), ejemplo(), test_armar_relato_sin_json_usa_el_texto_crudo(), test_diagnostico_campos_nombra_lo_que_leyo_mal(), test_diagnostico_exacto_con_json_no_culpa_a_una_sola_etapa(), test_diagnostico_exacto_sin_json(), test_diagnostico_juez_distingue_no_de_ambiguo() (+3 more)

### Community 29 - "re"
Cohesion: 0.12
Nodes (16): _encoder(), citas(), cruce(), _media(), ragas_propio(), answer_relevancy(), context_precision_exacta(), context_precision_juez() (+8 more)

### Community 30 - "CorridaFalsa"
Cohesion: 0.14
Nodes (3): CorridaFalsa, ctx_con_salidas(), sin_clave()

### Community 31 - "Migracion de notebooks a paquete Python amparo/"
Cohesion: 0.16
Nodes (12): Logica extraida de los notebooks a modulos, Fuera de alcance: despliegue y reentrenamiento, Migracion de notebooks a paquete Python amparo/, Tag entrega-m4 (commit d158742), Verificacion: linea base antes y despues de migrar, Estructura del paquete amparo/, Huella del codigo y version de datos por corrida, De donde salen las cifras (corridas y huellas) (+4 more)

### Community 32 - "Amparo: triaje de acciones constitucionales en Colombia"
Cohesion: 0.16
Nodes (12): Amparo: triaje de acciones constitucionales en Colombia, M1: fine-tuning LoRA de Qwen2.5-7B-Instruct, M2: harness con LLM-as-a-judge y cinco sondas, M3: cuatro arquitecturas (fine-tuned, RAG basico, RAG avanzado, agente + reglas), M4: componente visual Qwen2-VL-2B (patron input), reproducir.py: entrada unica de reproduccion, Estabilidad entre corridas (m1_estabilidad.json), groq (juez y agente via API) (+4 more)

### Community 33 - "Harness de M4: decisiones de T5 y T6 (y T7)"
Cohesion: 0.18
Nodes (5): armar_relato(), correr_harness(), Harness de M4: decisiones de T5 y T6 (y T7), test_armar_relato_con_json_es_la_formula_del_notebook(), test_m3_recibe_el_relato_armado_con_el_json_de_ver()

### Community 34 - "Contexto"
Cohesion: 0.15
Nodes (11): gpu(), armar_profesor(), Contexto, correr(), descargar(), manifiesto(), preparar(), _ClienteRelatos (+3 more)

### Community 35 - "pathlib"
Cohesion: 0.19
Nodes (7): chunking_de_m3(), comprobar_brazo(), construir_responder_m3(), cargar_corpus(), test_el_brazo_enchufado_existe_en_el_scorecard_de_m3(), test_el_chunking_es_el_que_eligio_m3(), test_un_brazo_mal_escrito_falla_antes_de_la_gpu()

### Community 36 - "datos.py"
Cohesion: 0.22
Nodes (8): comprobar_truncados(), construir(), construir_datasets(), medir_max_len(), mensajes(), _texto_completo(), preparar_dataset(), test_construir_enmascara_el_prompt_y_no_trunca_con_max_len_medido()

### Community 37 - "brazo_hibrido"
Cohesion: 0.13
Nodes (13): brazo_hibrido(), cargar_datos(), comprobar_splits(), _imprimir_quien_decide(), resumen_sonda(), veredicto_adversarial(), _preparar_hibrido(), test_brazo_hibrido_corta_temprano_si_el_extractor_es_mudo() (+5 more)

### Community 38 - "Limitaciones: lo que este trabajo no puede concluir"
Cohesion: 0.16
Nodes (14): Eval set v3 con puente subconjunto_v1, Lo que NO esta establecido (limitaciones), Relatos sinteticos, no expedientes, accion_cumplimiento en el brazo del agente (F1 0.4615), Adherencia del juez a la rubrica (0.7573), Capa de depuracion de citas de categoria equivocada, Caso A09 (trampa accion_cumplimiento, art. 9 Ley 393), Desacuerdos juridicos vs reglas de codificacion (+6 more)

### Community 39 - "test_pipeline_m1.py"
Cohesion: 0.15
Nodes (15): _celdas_codigo(), _ic(), LoraConfigFalsa, _publicaciones_literales(), test_cada_artefacto_se_guarda_en_el_codigo_antes_de_publicarse(), test_destinos_literales_coinciden_con_lo_declarado_en_arranque(), test_el_notebook_conserva_los_pins_de_instalacion(), test_el_notebook_llama_todas_las_etapas_en_orden_y_compila() (+7 more)

### Community 40 - "costos.py"
Cohesion: 0.12
Nodes (8): BrazoNoMedido, Cronometro, imprimir(), tabla(), normas_por_id(), etiqueta(), tabla_costos(), test_brazo_no_medido_sale_en_none_y_no_en_cero()

### Community 41 - "test_despliegue.py"
Cohesion: 0.17
Nodes (14): bloque_para_redaccion(), plantilla(), redactar_respuesta(), _res(), test_bloque_para_redaccion_quita_el_derecho_y_su_articulo_en_via_ordinaria(), test_formatear_para_usuario_pone_el_parrafo_arriba_y_la_ficha_plegada(), test_la_abstencion_no_llama_al_redactor(), test_plantilla_de_abstencion_pide_los_hechos_y_da_el_motivo() (+6 more)

### Community 42 - "sistema_visual.py"
Cohesion: 0.11
Nodes (18): sistema_multimodal(), Al desplegar (M5), conviene…, Backlog (después de la Demo), Dónde está hoy el recorrido completo, Guion sugerido (bloques, sin minutos obligatorios), Plan para Demo Day — Amparo, Prioridad 1 · [P1] La experiencia de punta a punta en una sola llamada, con el fundamento a la vista, Prioridad 2 · [P1] La confianza como característica: «cuando no está seguro, lo dice» (+10 more)

### Community 43 - "corrida_m4.py"
Cohesion: 0.14
Nodes (10): version(), cerrar(), _git(), guardar(), huella_eval_set(), manifiesto(), nueva(), _sha() (+2 more)

### Community 44 - "render_salida"
Cohesion: 0.22
Nodes (7): sesgo_longitud(), mensajes_few_shot(), render_ejemplo(), render_entrada(), render_salida(), Profesor y estudiante, t_guia()

### Community 45 - "T6 - Corrida del harness: notas para T8 (Lucas -> Nico)"
Cohesion: 0.15
Nodes (11): m10 - valvula ADVERSARIAL (fecha|plazo_dias), Criterio valvula (campos que deben venir null), doc06_notificacion_borrosa.jpg - ADVERSARIAL mojada, sin fecha ni plazo, Hallazgo 1: entidad y plazo_dias salen null, Hallazgo 2: m10 inventa 'dos semanas' en pretension_visible, Hallazgo 5: el procedimiento desaparece (m01/m02), Hallazgo 3: sentido invertido en doc03 (m04/m05), T6 - Corrida del harness: notas para T8 (Lucas -> Nico) (+3 more)

### Community 46 - "Corrida"
Cohesion: 0.14
Nodes (6): ahora_bogota(), comparar(), Corrida, hardware(), listar(), ultimas()

### Community 47 - "imprimir"
Cohesion: 0.33
Nodes (4): comparar(), imprimir(), harness_completo(), comparar()

### Community 48 - "publicar_todo"
Cohesion: 0.20
Nodes (5): faltantes(), publicar_todo(), CorridaFalsa, test_publicar_todo_no_publica_nada_si_falta_uno_y_dice_quien_lo_genera(), test_publicar_todo_publica_solo_si_estan_todos()

### Community 49 - "familia_de"
Cohesion: 0.18
Nodes (7): candidatos(), familia_de(), orden_de_candidatos(), clave(), tamano_declarado(), test_candidatos_otra_familia_primero_y_sin_modelos_que_no_juzgan(), test_candidatos_sin_poder_listar_usa_la_lista_de_juez()

### Community 50 - "json"
Cohesion: 0.18
Nodes (10): guardar(), ids_eval_v1(), cobertura_clasificador(), imprimir(), main(), medir(), _palabras(), _textos() (+2 more)

### Community 51 - "TokFalso"
Cohesion: 0.20
Nodes (6): generador_hf(), ids_parada(), test_generador_hf_cuenta_tokens_y_apaga_el_adaptador_si_se_pide(), test_generador_hf_recorta_la_cola_y_anota_el_caso(), test_ids_parada_incluye_eos_y_marcas_de_turno(), TokFalso

### Community 52 - "schema.py"
Cohesion: 0.08
Nodes (9): _raiz(), nueva(), versiones(), preparar(), verificar_sello(), _lectura_familias(), misma_familia(), correr() (+1 more)

### Community 53 - "_ctx_medido"
Cohesion: 0.14
Nodes (15): acierto_por_item(), harness(), resumen_juez(), casos_perdidos(), guardar(), tabla(), _ctx_medido(), test_el_contrato_tiene_las_cinco_clausulas() (+7 more)

### Community 55 - "Agente"
Cohesion: 0.07
Nodes (14): Costos, cita_completa(), extraer_hechos(), formatear_contexto(), generador_groq(), generar(), _json_de(), SistemaHibrido (+6 more)

### Community 56 - "citas"
Cohesion: 0.11
Nodes (12): alucinacion_normativa(), citas_en_texto(), clasificar_cita(), _clave_sentencia(), _claves_jurisprudencia(), _jurisprudencia_conocida(), _limpiar_cita(), pertinencia_citas() (+4 more)

### Community 57 - "correr_con_reloj"
Cohesion: 0.22
Nodes (5): correr_con_reloj(), _AgenteQueTragaErrores, test_correr_con_reloj_retoma_y_no_inventa_respuestas(), test_medir_marca_vacio_si_la_extraccion_falla_por_otra_cosa(), test_medir_para_y_no_guarda_si_el_cupo_se_acaba_en_la_extraccion()

### Community 58 - "acuerdo_entre_jueces"
Cohesion: 0.25
Nodes (4): acuerdo_entre_jueces(), cohen_kappa(), _spearman(), ac()

### Community 60 - "M3: cuatro arquitecturas sobre 103 casos comunes"
Cohesion: 0.22
Nodes (7): Bug heredado latencia_s_por_caso = 0.0 (conservado), Desviaciones respecto a los notebooks, Art. 6 Decreto 2591 de 1991 (arbol de decision), Agente: pasos censurados y veredicto_presupuesto, Coste: GPU local vs llamadas API (m3_costos.json), M3: cuatro arquitecturas sobre 103 casos comunes, Tesis: modelo pequeno afinado sobre art. 6 supera a la recuperacion

### Community 61 - "REPORTE: Triaje de acciones constitucionales colombianas"
Cohesion: 0.28
Nodes (7): Corpus normativo (data/normas.json), Leonardo Galeano (abogado responsable del corpus), Apendice: cada cifra y su artefacto, Cobertura del corpus: techo de ranking, no de cobertura, Efectos adversos del RAG: abstencion indebida y citas incompletas, Recall en clases criticas (habeas_corpus, tutela), REPORTE: Triaje de acciones constitucionales colombianas

### Community 63 - "doc03 Respuesta a derecho de peticion (cumplimiento, negativa a publicar contratos)"
Cohesion: 0.32
Nodes (6): doc03 Respuesta a derecho de peticion (cumplimiento, negativa a publicar contratos), Accion de cumplimiento (accion judicial anunciada por el peticionario), Alcaldia de Puerto Almendro (entidad ficticia, radicado SG-0987), Derecho de peticion, Ley 1712 de 2014, articulo 10 (deber de publicar contratos), SECOP (Sistema Electronico de Contratacion Publica)

### Community 64 - "medir"
Cohesion: 0.29
Nodes (4): medir(), _CostosFalsos, test_medir_vacia_la_cache_del_estudiante_y_mide_las_llamadas(), test_rehacer_estudiante_borra_lo_ya_medido()

### Community 65 - "delta_con_sin_imagen"
Cohesion: 0.25
Nodes (6): delta_con_sin_imagen(), _media(), Delta: misma pregunta con imagen y sin ella, m01 no es estable (extractor de hechos de M3 no determinista), test_delta_con_sin_imagen_registra_latencia_de_las_dos_condiciones(), test_delta_con_sin_imagen_separa_lo_que_aporta_de_lo_que_no()

### Community 66 - "Oficio No. SPM-0412 (12 de agosto de 2026)"
Cohesion: 0.29
Nodes (6): doc02 Oficio Planeación (imagen sintética del eval set M4), Oficio No. SPM-0412 (12 de agosto de 2026), Plazo de quince (15) días hábiles, Requerimiento por obra de construcción sin licencia, Secretaría de Planeación Municipal de Puerto Almendro (entidad ficticia), Traslado a la Inspección de Policía (consecuencia por incumplimiento)

### Community 67 - "doc04: Respuesta de la CAR a un derecho de petición (imagen del eval set M4)"
Cohesion: 0.43
Nodes (7): doc04: Respuesta de la CAR a un derecho de petición (imagen del eval set M4), Corporación Autónoma Regional del Río Claro (CORPORIOCLARO, ficticia), Decisión: no adoptar medidas preventivas y archivar la queja, Junta de Acción Comunal de la vereda Los Naranjos (peticionaria), Sello 'Documento sintético / generado' (uso académico SI4006 · M4 · Amparo), Queja por vertimientos de curtiembre en la quebrada La Clara (fuente del acueducto veredal), Radicado CRCL-2231 (Villa Serena, 30 sep 2026)

### Community 68 - "M1: el sistema afinado (base, hibrido, afinado)"
Cohesion: 0.29
Nodes (7): Escalera de fiabilidad de etiquetas (nivel_fiabilidad), Baseline de formato few-shot (41.7%), Capa de redaccion sin normas intrusas, Degeneracion de salidas (m1_degeneracion.json), Descomposicion del salto: razonamiento vs formato, M1: el sistema afinado (base, hibrido, afinado), Niveles de verificacion: plano, derivado, juicio

### Community 69 - "M2: el evaluador, evaluado (sondas de sesgo)"
Cohesion: 0.29
Nodes (7): Acierto juridico (metrica de cabecera), Acuerdo entre jueces (kappa 0.481), Sesgo de auto-preferencia condicionado a calidad, Determinismo del juez (resolucion del instrumento), Los dos jueces son de la misma familia (gpt-oss), M2: el evaluador, evaluado (sondas de sesgo), ROUGE-L contra acierto

### Community 70 - "m01 · doc01_respuesta_eps.png"
Cohesion: 0.14
Nodes (13): Leído del documento por un modelo de visión · no verificado, Leído del documento por un modelo de visión · no verificado, Leído del documento por un modelo de visión · no verificado, m01 · doc01_respuesta_eps.png, m06 · doc04_respuesta_car.png, m10 · doc06_notificacion_borrosa.jpg, Plan B · salida GRABADA de la corrida 20261101T194319Z, Por qué (+5 more)

### Community 71 - "test_pipeline_m2.py"
Cohesion: 0.14
Nodes (11): a_csv(), publicar(), _corrida_previa(), _ctx_para_publicar(), test_cada_artefacto_se_guarda_en_el_codigo_antes_de_publicarse(), test_corridas_previas_salta_las_de_control_y_las_sin_scorecard(), test_estabilidad_atribuye_codigo_y_predicciones_de_m1(), test_formato_vocabulario_mide_las_tres_en_los_dos_brazos() (+3 more)

### Community 72 - "metricas.py"
Cohesion: 0.05
Nodes (34): sesgo_autopreferencia(), abstencion(), accuracy(), acierto_juridico(), acierto_por_caso(), adherencia_estructural(), adherencia_vocabulario(), _anatomia_de_la_cola() (+26 more)

### Community 73 - "doc01_respuesta_eps.png (Respuesta a derecho de petición, EPS)"
Cohesion: 0.40
Nodes (5): doc01_respuesta_eps.png (Respuesta a derecho de petición, EPS), EPS Salud Serena S.A.S. (entidad ficticia), Negación de autorización por falta de prestador contratado en la red, Procedimiento: reemplazo total de cadera derecha (ordenado por ortopedia), Respuesta a derecho de petición (radicado SS-AUT-0193)

### Community 74 - "doc06 Notificación por aviso borrosa (imagen eval M4)"
Cohesion: 0.47
Nodes (5): doc06 Notificación por aviso borrosa (imagen eval M4), Inspección Municipal de Policía de Villa Serena (entidad ficticia), Marca DOCUMENTO SINTÉTICO / GENERADO (uso académico SI4006 M4 Amparo, sin validez jurídica), Notificación por aviso (procedimiento por comportamiento contrario a la convivencia), Plazo de descargos en días hábiles ocluido por mancha de tinta

### Community 75 - "cargar_checkpoint"
Cohesion: 0.20
Nodes (5): cargar_checkpoint(), _cargar_ck(), CorridaFalsa, _ctx(), test_un_brazo_corrido_se_guarda_en_el_checkpoint_y_se_reutiliza()

### Community 76 - "m01 · doc01_respuesta_eps.png"
Cohesion: 0.14
Nodes (13): Leído del documento por un modelo de visión · no verificado, Leído del documento por un modelo de visión · no verificado, Leído del documento por un modelo de visión · no verificado, m01 · doc01_respuesta_eps.png, m06 · doc04_respuesta_car.png, m10 · doc06_notificacion_borrosa.jpg, Plan B · salida GRABADA de la corrida 20261101T203828Z, Por qué (+5 more)

### Community 77 - "agente_estudiante"
Cohesion: 0.11
Nodes (10): cargar_estudiante(), ClienteEstudiante, _construir(), entrenar_estudiante(), generador(), generar(), mensajes_estudiante(), _Respuesta (+2 more)

### Community 78 - "Contexto"
Cohesion: 0.17
Nodes (10): cargar_lector(), Contexto, correr(), correr_harness(), descargar(), miniaturas(), resumen(), validar_eval_set() (+2 more)

### Community 79 - "doc05 Notificacion de Suspension del Servicio de Acueducto (imagen sintetica)"
Cohesion: 0.50
Nodes (4): doc05 Notificacion de Suspension del Servicio de Acueducto (imagen sintetica), Acuerdo de pago como alternativa a la suspension, Aguas de Villa Serena S.A. E.S.P. (empresa ficticia de acueducto), Suspension del servicio publico domiciliario por saldo vencido (plazo 5 dias habiles)

### Community 80 - "JuezFalso"
Cohesion: 0.19
Nodes (8): puntuar_muestra(), construir(), JuezFalso, test_elegir_juez_cae_a_un_alternativo_y_para_si_no_hay_ninguno(), construir(), test_puntuar_muestra_abandona_tras_tres_fallos_seguidos_sin_gastar_el_resto(), test_puntuar_muestra_sin_fallos_puntua_los_n(), test_puntuar_muestra_un_fallo_aislado_deja_un_hueco_y_sigue()

### Community 81 - "m5_destilacion.py"
Cohesion: 0.15
Nodes (14): cargar(), acuerdo_profesor_gold(), cargar_eval(), _cliente_groq(), CupoAgotado, _es_cupo(), _escribir(), escribir_relatos() (+6 more)

### Community 82 - "consultar"
Cohesion: 0.11
Nodes (15): consultar(), presentar(), registrar(), responder(), _Agente, _Amparo, test_consulta_normal_registra_y_guarda_la_cache(), test_la_app_arma_la_interfaz_y_responde() (+7 more)

### Community 83 - "autoprueba_integracion.py"
Cohesion: 0.04
Nodes (66): tabla_puente(), trocear(), _agente_pelado(), _cargar(), _chunks(), _IndiceFalso, _nb(), _perfecta() (+58 more)

### Community 86 - "test_de_punta_a_punta_sobre_el_eval_set_real"
Cohesion: 0.16
Nodes (7): vaciar_caches(), cerrar(), delta_imagen(), delta_repetido(), plan_b(), AmparoFalso, test_de_punta_a_punta_sobre_el_eval_set_real()

### Community 87 - "redaccion.py"
Cohesion: 0.20
Nodes (5): citas_de(), construir_prompt(), redactar(), _texto_pivote(), verificar_texto()

### Community 88 - "correr_t6"
Cohesion: 0.18
Nodes (13): correr_t6(), leer_fila_m3(), escribir_costos(), escribir_m3(), _rutas(), test_correr_t6_de_punta_a_punta(), test_correr_t6_exige_el_brazo_antes_de_correr(), test_correr_t6_sin_results_guarda_el_scorecard_antes_de_fallar() (+5 more)

### Community 89 - "scorecard.py"
Cohesion: 0.17
Nodes (7): construir_tabla_delta(), tabla_markdown(), _tabla_y_guardar(), test_peor_caso_lista_todos_los_empatados_con_su_etapa(), test_tabla_delta_tiene_las_5_filas_con_metrica_nombrada(), test_tabla_delta_valores(), test_tabla_markdown_tiene_la_forma_de_la_plantilla_y_no_inventa_latencia()

### Community 90 - "m5_cuantizacion.py"
Cohesion: 0.05
Nodes (34): LectorVisual, armar_m3(), cargar(), Contexto, descargar(), _escribir(), guardar(), latencias() (+26 more)

### Community 91 - "test_pipeline_m3.py"
Cohesion: 0.18
Nodes (4): _salida(), SistemaFalso, test_correr_brazos_sin_gpu_corre_el_agente_y_el_brazo_uno(), test_matriz_por_caso_y_techo_de_la_union()

### Community 92 - "cargar_normas"
Cohesion: 0.15
Nodes (7): _degradar(), experimento_validez(), cargar_normas(), planos_normativos(), separar_planos(), validar(), validez()

### Community 94 - "ctx"
Cohesion: 0.20
Nodes (3): AgenteFalso, ctx(), LectorFalso

### Community 96 - "reproducibilidad"
Cohesion: 0.17
Nodes (7): corridas_previas(), estabilidad(), filas_por_caso(), limpiar(), reproducibilidad(), test_estabilidad_sin_corrida_previa_es_none_y_no_true(), test_limpiar_quita_el_entorno_sin_tocar_el_original()

### Community 97 - "consultar_res"
Cohesion: 0.17
Nodes (7): anonimizar(), consultar_res(), guardar_caches(), recargar_caches(), _consultar(), test_guardar_caches_guarda_las_dos(), test_recargar_caches_trae_lo_que_otro_proceso_escribio()

### Community 99 - "time"
Cohesion: 0.39
Nodes (4): _correr(), entorno(), _linea(), main()

### Community 100 - "recortar_al_bloque"
Cohesion: 0.20
Nodes (9): cargar_m1(), recortar(), generar(), recortar_al_bloque(), cargar_salidas(), _salida(), test_cargar_m1_desenvuelve_datos_y_conserva_la_corrida(), test_cargar_m1_exige_el_mismo_orden_que_el_eval_set() (+1 more)

### Community 101 - "comparar_con_previa"
Cohesion: 0.24
Nodes (7): comparar_con_previa(), estabilidad(), _previa(), test_comparar_con_previa_identicas_y_codigo_distinto(), test_comparar_con_previa_sin_artefactos_no_es_concluyente(), test_estabilidad_con_previa_guarda_y_publica(), test_estabilidad_en_la_primera_corrida_no_publica()

### Community 102 - "latencia_por_componente"
Cohesion: 0.24
Nodes (6): corrida_m4_con_tiempos(), _fila(), latencia_por_componente(), _pct(), test_latencia_por_componente_resta_bien(), test_latencia_por_componente_sobre_el_scorecard_de_m4()

### Community 103 - "test_compartidos.py"
Cohesion: 0.29
Nodes (3): cargar_clave_groq(), test_cargar_clave_groq_fuera_de_colab_y_sin_pedir_devuelve_false(), test_cargar_clave_groq_respeta_la_del_entorno()

### Community 105 - "enchufar_m3"
Cohesion: 0.29
Nodes (3): enchufar_m3(), test_enchufar_m3_arma_amparo_y_guarda_el_manifiesto(), _Transformador

### Community 106 - "test_pipeline_m5.py"
Cohesion: 0.18
Nodes (11): a_texto(), agente_estudiante(), objetivo(), _hechos(), _libres(), test_acuerdo_profesor_gold_con_un_profesor_perfecto(), test_el_estudiante_que_copia_al_profesor_decide_lo_mismo(), test_el_estudiante_recibe_el_relato_y_no_el_prompt_del_profesor() (+3 more)

### Community 107 - "inyeccion"
Cohesion: 0.33
Nodes (3): experimento_inyeccion(), respuesta_floja(), inyeccion()

### Community 108 - "leer_latencia_m3"
Cohesion: 0.40
Nodes (3): leer_latencia_m3(), test_latencia_m3_es_por_caso_y_no_por_llamada(), test_leer_latencia_m3()

### Community 109 - "SinVision"
Cohesion: 0.40
Nodes (3): ErrorAPI, SinVision, test_sin_vision_lo_dice()

### Community 110 - "T7 - Enchufe real de M3"
Cohesion: 0.40
Nodes (4): Corrida local T6 (RTX 5060, M3 sustituto), Corrida oficial en Colab (T4), T7 - Enchufe real de M3, Sustituto de responder_m3 (andamio temporal)

### Community 111 - "m4_multimodal.py"
Cohesion: 0.15
Nodes (10): cargar(), cargar_imagenes(), cronometrar(), _git(), preparar(), probar_ver(), tabla_casos(), test_cargar_imagenes_y_probar_ver() (+2 more)

## Knowledge Gaps
- **32 isolated node(s):** `amparo`, `casos_m4.ejemplo.csv`, `Checklist de anonimizacion (sin caras, nombres, cedulas, firmas ni sellos)`, `Entidades ficticias (EPS Salud Serena, Alcaldia de Puerto Almendro, CORPORIOCLARO, Aguas de Villa Serena)`, `INSTRUCCION_DOMINIO (5 campos JSON)` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 764 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **16 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Harness de M4: decisiones de T5 y T6 (y T7)` connect `Harness de M4: decisiones de T5 y T6 (y T7)` to `test_criterios.py`, `delta_con_sin_imagen`, `pathlib`, `csv`, `metricas.py`, `leer_latencia_m3`, `T6 - Corrida del harness: notas para T8 (Lucas -> Nico)`, `casos_m4.csv: 11 casos sobre 6 imagenes`, `correr_t6`, `scorecard.py`, `Migracion de notebooks a paquete Python amparo/`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **What connects `amparo`, `casos_m4.ejemplo.csv`, `Checklist de anonimizacion (sin caras, nombres, cedulas, firmas ni sellos)` to the rest of the system?**
  _32 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_criterios.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05207920792079208 - nodes in this community are weakly interconnected._
- **Why does `Migracion de notebooks a paquete Python amparo/` connect `Migracion de notebooks a paquete Python amparo/` to `Amparo: triaje de acciones constitucionales en Colombia`, `Harness de M4: decisiones de T5 y T6 (y T7)`, `M3: cuatro arquitecturas sobre 103 casos comunes`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Should `m3_rag.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Why does `parse_salida()` connect `metricas.py` to `test_criterios.py`, `test_pipeline_m4.py`, `brazos.py`, `Contexto`, `medir`, `Agente`, `m1_finetuning.py`, `redaccion`, `test_multimodal.py`, `test_despliegue.py`, `re`, `test_despliegue.py`, `schema.py`, `_ctx_medido`, `citas`, `test_pipeline_m3.py`, `reproducibilidad`, `consultar_res`, `test_pipeline_m5.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Should `test_pipeline_m4.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10114942528735632 - nodes in this community are weakly interconnected._