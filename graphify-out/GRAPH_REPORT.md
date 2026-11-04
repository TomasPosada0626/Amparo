# Graph Report - Amparo  (2026-11-03)

## Corpus Check
- 92 files · ~213,987 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: .ipynb 5, .csv 5, (none) 3)

## Summary
- 1896 nodes · 4221 edges · 101 communities (89 shown, 12 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 255 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f8c0e6c0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- generar_imagenes.py
- test_criterios.py
- m3_rag.py
- test_pipeline_m4.py
- Pipeline
- alucinacion_normativa
- m2_harness.py
- test_scorecard.py
- test_de_punta_a_punta_sobre_el_eval_set_real
- test_pipeline_m2.py
- Costos
- harness.py
- test_pipeline_m1.py
- m1_finetuning.py
- entrenamiento.py
- casos_m4.csv: 11 casos sobre 6 imagenes
- correr_t6
- terminos.py
- Indice
- _salida
- SistemaOraculo
- recuperacion.py
- Juez
- Hechos
- CorridaFalsa
- M4 - Amparo ya ve (README de entrega)
- test_multimodal.py
- corridas.py
- schema.py
- re
- CorridaFalsa
- Migracion de notebooks a paquete Python amparo/
- Amparo: triaje de acciones constitucionales en Colombia
- Harness de M4: decisiones de T5 y T6 (y T7)
- m5_destilacion.py
- pathlib
- datos.py
- brazo_hibrido
- Limitaciones: lo que este trabajo no puede concluir
- test_compartidos.py
- tabla
- test_pipeline_m3.py
- sistema_multimodal
- corrida_m4.py
- TokFalso
- T6 - Corrida del harness: notas para T8 (Lucas -> Nico)
- Corrida
- generacion.py
- publicar_todo
- juez.py
- metricas.py
- ModeloFalso
- json
- _ctx_medido
- TransformadorConsulta
- Agente
- escribir_relatos
- test_pipeline_m5.py
- redaccion.py
- time
- M3: cuatro arquitecturas sobre 103 casos comunes
- REPORTE: Triaje de acciones constitucionales colombianas
- Contexto
- doc03 Respuesta a derecho de peticion (cumplimiento, negativa a publicar contratos)
- medir
- delta_con_sin_imagen
- Oficio No. SPM-0412 (12 de agosto de 2026)
- doc04: Respuesta de la CAR a un derecho de petición (imagen del eval set M4)
- M1: el sistema afinado (base, hibrido, afinado)
- M2: el evaluador, evaluado (sondas de sesgo)
- m01 · doc01_respuesta_eps.png
- degeneracion
- _jurisprudencia_conocida
- doc01_respuesta_eps.png (Respuesta a derecho de petición, EPS)
- doc06 Notificación por aviso borrosa (imagen eval M4)
- CorridaFalsa
- m01 · doc01_respuesta_eps.png
- ClienteEstudiante
- m4_multimodal.py
- doc05 Notificacion de Suspension del Servicio de Acueducto (imagen sintetica)
- sesgo_longitud
- latencia_por_componente
- autoprueba_integracion.py
- amparo
- SistemaHibrido
- ctx
- recortar_al_bloque
- scorecard.py
- sistema_visual.py
- render_salida
- preparar
- t_sonda_validez_ejecuta
- BM25
- t_inyeccion_sin_api
- pytest
- collate_para
- t_reporte_no_afirma_de_mas
- cargar
- tabla_casos

## God Nodes (most connected - your core abstractions)
1. `prueba()` - 77 edges
2. `parse_salida()` - 36 edges
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
- `4. Prioridades para Demo Day` --references--> `sistema_multimodal()`  [INFERRED]
  review/m4/README.md → amparo/multimodal/sistema_visual.py
- `H4 · El efecto de la imagen en m06 varía entre corridas` --references--> `sistema_multimodal()`  [INFERRED]
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

## Communities (101 total, 12 thin omitted)

### Community 0 - "generar_imagenes.py"
Cohesion: 0.19
Nodes (14): doc01_respuesta_eps(), doc02_oficio_planeacion(), doc03_respuesta_cumplimiento(), doc04_respuesta_car(), doc05_notificacion_acueducto(), doc06_notificacion_borrosa(), encabezado(), F() (+6 more)

### Community 1 - "test_criterios.py"
Cohesion: 0.05
Nodes (70): _acierta_campo(), advertencias_lectura(), calificar(), cargar_casos(), _entero(), _es_nulo(), _esperado_campos(), _esperado_exacto() (+62 more)

### Community 2 - "m3_rag.py"
Cohesion: 0.07
Nodes (32): cargar_checkpoint(), auditar_corpus(), brazo_uno(), _cargar_ck(), chunking(), cierre(), _ck_guardar(), _cliente_groq() (+24 more)

### Community 3 - "test_pipeline_m4.py"
Cohesion: 0.08
Nodes (11): ClienteGuionado, _correr(), _Fn, IndiceFalso, main(), _Msg, _Resp, _TC (+3 more)

### Community 4 - "Pipeline"
Cohesion: 0.15
Nodes (15): casos_validos(), correr(), Pipeline, test_cada_imagen_se_carga_una_vez(), test_cronometro_mide_ver_mas_m3_y_deja_fuera_carga_y_juez(), test_csv_invalido_no_corre_nada(), test_excepcion_del_sistema_detiene_la_corrida(), test_imagen_faltante_no_corre_nada() (+7 more)

### Community 5 - "alucinacion_normativa"
Cohesion: 0.19
Nodes (8): alucinacion_normativa(), clasificar_cita(), pertinencia_citas(), pertinencia_por_plano(), _vocabulario_normas(), t_cp_sin_verificar(), t_juris(), t_no_medible()

### Community 6 - "m2_harness.py"
Cohesion: 0.07
Nodes (22): comparar(), acuerdo_entre_jueces(), autopreferencia(), cargar_salidas(), Contexto, correr(), corridas_previas(), estabilidad() (+14 more)

### Community 7 - "test_scorecard.py"
Cohesion: 0.11
Nodes (24): leer_fila_m3(), carpeta(), _diag(), ejemplo(), escribir_costos(), escribir_m3(), _rutas(), test_armar_relato_con_json_es_la_formula_del_notebook() (+16 more)

### Community 8 - "test_de_punta_a_punta_sobre_el_eval_set_real"
Cohesion: 0.15
Nodes (7): vaciar_caches(), cerrar(), delta_imagen(), delta_repetido(), plan_b(), AmparoFalso, test_de_punta_a_punta_sobre_el_eval_set_real()

### Community 9 - "test_pipeline_m2.py"
Cohesion: 0.08
Nodes (24): candidatos(), medir(), puntuar_muestra(), elegir_juez(), ClienteFalso, _corrida_previa(), _fabrica(), construir() (+16 more)

### Community 10 - "Costos"
Cohesion: 0.15
Nodes (7): Costos, cita_completa(), formatear_contexto(), generador_groq(), generar(), SistemaRAG, t_costos()

### Community 11 - "harness.py"
Cohesion: 0.11
Nodes (11): acuerdo_entre_jueces(), adherencia_a_la_rubrica(), cohen_kappa(), guardar(), ids_eval_v1(), _lectura_familias(), sesgo_posicion(), _spearman() (+3 more)

### Community 12 - "test_pipeline_m1.py"
Cohesion: 0.07
Nodes (25): guardar_adaptador(), _celdas_codigo(), _ic(), LoraConfigFalsa, ModeloLora, ModeloQueGuarda, _Param, _publicaciones_literales() (+17 more)

### Community 13 - "m1_finetuning.py"
Cohesion: 0.06
Nodes (28): aplicar_lora(), generar_lote(), abstencion_validation(), aplicar_lora(), baseline(), baseline_few_shot(), cerrar(), cobertura_clasificador() (+20 more)

### Community 14 - "entrenamiento.py"
Cohesion: 0.09
Nodes (15): callbacks_parada(), comprobar_lora_b(), crear_trainer(), filtrar_hiperparametros(), graficar_perdida(), hiperparametros(), registro_hiperparametros(), seleccionar_checkpoint() (+7 more)

### Community 15 - "casos_m4.csv: 11 casos sobre 6 imagenes"
Cohesion: 0.12
Nodes (28): casos_m4.csv: 11 casos sobre 6 imagenes, m01 - exacto: tutela (EPS niega cirugia), m02 - campos sobre doc01 (cadera), m03 - campos sobre doc02 (plazo_dias 15), m04 - exacto: accion_cumplimiento (Ley 1712), m05 - campos sobre doc03 (contratos), m06 - exacto: accion_popular (cuatro veredas), m07 - campos sobre doc04 (entidad 'claro') (+20 more)

### Community 16 - "correr_t6"
Cohesion: 0.23
Nodes (7): cargar_guardado(), correr_t6(), guardar(), tabla_desde_disco(), test_cargar_guardado_devuelve_lo_mismo_que_se_guardo(), test_guardar_escribe_scorecard_y_trazas(), test_tabla_desde_disco_da_la_misma_tabla_que_la_corrida_completa()

### Community 17 - "terminos.py"
Cohesion: 0.12
Nodes (14): calcular_termino(), contar_habiles(), es_habil(), festivos(), leer_fecha(), _lunes_siguiente(), pascua(), sumar_habiles() (+6 more)

### Community 19 - "_salida"
Cohesion: 0.18
Nodes (6): legibles(), HibridoFalso, _salida(), generar_lote(), test_legibles_cuenta_mecanismos_parseables(), test_redaccion_con_generador_redacta_sobre_el_ajustado()

### Community 20 - "SistemaOraculo"
Cohesion: 0.21
Nodes (8): trocear(), SistemaOraculo, _chunks(), t_cobertura(), t_corpus_amplia(), t_oraculo(), t_oraculo_sin_gold(), t_precision_acotada()

### Community 21 - "recuperacion.py"
Cohesion: 0.13
Nodes (8): _cita_de(), citas_esperadas(), comparar_chunking(), comparar_estrategias(), elegir_estrategia(), evaluar_recuperacion(), _percentil(), trocear_fijo()

### Community 22 - "Juez"
Cohesion: 0.17
Nodes (3): _envolver(), Juez, puntuar_lote()

### Community 23 - "Hechos"
Cohesion: 0.08
Nodes (17): decidir(), Decision, estrato_verificacion(), explicar(), Hechos, pivota_en_juicio(), extraer_hechos(), _json_de() (+9 more)

### Community 24 - "CorridaFalsa"
Cohesion: 0.11
Nodes (9): comparar_con_previa(), estabilidad(), CorridaFalsa, ctx(), _previa(), test_comparar_con_previa_identicas_y_codigo_distinto(), test_comparar_con_previa_sin_artefactos_no_es_concluyente(), test_estabilidad_con_previa_guarda_y_publica() (+1 more)

### Community 25 - "M4 - Amparo ya ve (README de entrega)"
Cohesion: 0.16
Nodes (11): M4 - Amparo ya ve (README de entrega), Tabla M3 (n=120, 0.675) vs M4 (n=3, 1.0), M4 Plan de trabajo - Su sistema ya ve, Qwen2-VL-2B-Instruct, Reparto de tareas T1-T9 (Santiago, Lucas, Nico, Martin/Tomas), Rubrica M4 (10 puntos), S13_Lab_Integracion_Visual_RESUELTO.ipynb (plantilla base), Tabla de delta M3 vs M4 (+3 more)

### Community 26 - "test_multimodal.py"
Cohesion: 0.15
Nodes (13): Amparo, formatear(), por_que(), LectorFalso, _m3(), test_al_abstenerse_no_muestra_una_regla_que_cerro_el_caso(), test_el_caso_de_seguridad_muestra_el_aviso(), test_manifiesto_registra_lo_que_atribuye_las_cifras() (+5 more)

### Community 27 - "corridas.py"
Cohesion: 0.10
Nodes (10): _raiz(), celda(), _en_colab(), humo(), _procedencia(), nueva(), version_codigo(), version_datos() (+2 more)

### Community 28 - "schema.py"
Cohesion: 0.24
Nodes (5): cargar_normas(), demostraciones_few_shot(), planos_normativos(), separar_planos(), validar()

### Community 29 - "re"
Cohesion: 0.17
Nodes (12): _encoder(), citas(), answer_relevancy(), context_precision_exacta(), context_precision_juez(), context_recall_exacto(), evaluar(), faithfulness_exacta() (+4 more)

### Community 30 - "CorridaFalsa"
Cohesion: 0.13
Nodes (7): a_csv(), publicar(), CorridaFalsa, _ctx_para_publicar(), test_publicar_no_publica_nada_si_falta_un_artefacto(), test_publicar_publica_los_diez_y_el_acuerdo_aparte(), test_publicar_sin_acuerdo_no_lo_publica()

### Community 31 - "Migracion de notebooks a paquete Python amparo/"
Cohesion: 0.16
Nodes (12): Logica extraida de los notebooks a modulos, Fuera de alcance: despliegue y reentrenamiento, Migracion de notebooks a paquete Python amparo/, Tag entrega-m4 (commit d158742), Verificacion: linea base antes y despues de migrar, Estructura del paquete amparo/, Huella del codigo y version de datos por corrida, De donde salen las cifras (corridas y huellas) (+4 more)

### Community 32 - "Amparo: triaje de acciones constitucionales en Colombia"
Cohesion: 0.16
Nodes (12): Amparo: triaje de acciones constitucionales en Colombia, M1: fine-tuning LoRA de Qwen2.5-7B-Instruct, M2: harness con LLM-as-a-judge y cinco sondas, M3: cuatro arquitecturas (fine-tuned, RAG basico, RAG avanzado, agente + reglas), M4: componente visual Qwen2-VL-2B (patron input), reproducir.py: entrada unica de reproduccion, Estabilidad entre corridas (m1_estabilidad.json), groq (juez y agente via API) (+4 more)

### Community 33 - "Harness de M4: decisiones de T5 y T6 (y T7)"
Cohesion: 0.18
Nodes (4): correr_harness(), leer_latencia_m3(), Harness de M4: decisiones de T5 y T6 (y T7), test_latencia_m3_es_por_caso_y_no_por_llamada()

### Community 34 - "m5_destilacion.py"
Cohesion: 0.12
Nodes (16): a_texto(), armar_profesor(), cargar_estudiante(), _construir(), correr(), entrenar_estudiante(), _escribir(), generador() (+8 more)

### Community 35 - "pathlib"
Cohesion: 0.11
Nodes (14): chunking_de_m3(), comprobar_brazo(), construir_responder_m3(), armar_relato(), cargar_corpus(), Brazo 4 - agente + reglas (M3), _responder(), test_el_brazo_enchufado_existe_en_el_scorecard_de_m3() (+6 more)

### Community 36 - "datos.py"
Cohesion: 0.22
Nodes (8): comprobar_truncados(), construir(), construir_datasets(), medir_max_len(), mensajes(), _texto_completo(), preparar_dataset(), test_construir_enmascara_el_prompt_y_no_trunca_con_max_len_medido()

### Community 37 - "brazo_hibrido"
Cohesion: 0.10
Nodes (15): ic_se_solapan(), imprimir(), brazo_hibrido(), cargar_datos(), comprobar_splits(), _imprimir_quien_decide(), resumen_sonda(), veredicto_adversarial() (+7 more)

### Community 38 - "Limitaciones: lo que este trabajo no puede concluir"
Cohesion: 0.16
Nodes (14): Eval set v3 con puente subconjunto_v1, Lo que NO esta establecido (limitaciones), Relatos sinteticos, no expedientes, accion_cumplimiento en el brazo del agente (F1 0.4615), Adherencia del juez a la rubrica (0.7573), Capa de depuracion de citas de categoria equivocada, Caso A09 (trampa accion_cumplimiento, art. 9 Ley 393), Desacuerdos juridicos vs reglas de codificacion (+6 more)

### Community 39 - "test_compartidos.py"
Cohesion: 0.18
Nodes (7): cargar_clave_groq(), cargar_m1(), _salida(), test_cargar_clave_groq_fuera_de_colab_y_sin_pedir_devuelve_false(), test_cargar_clave_groq_respeta_la_del_entorno(), test_cargar_m1_desenvuelve_datos_y_conserva_la_corrida(), test_cargar_m1_exige_el_mismo_orden_que_el_eval_set()

### Community 40 - "tabla"
Cohesion: 0.22
Nodes (5): BrazoNoMedido, tabla(), normas_por_id(), etiqueta(), test_brazo_no_medido_sale_en_none_y_no_en_cero()

### Community 41 - "test_pipeline_m3.py"
Cohesion: 0.06
Nodes (19): correr_brazo(), CostoPorBrazo, matriz_por_caso(), reloj_legible(), ResultadoBrazo, techo_union(), transformador_para(), Reloj (+11 more)

### Community 42 - "sistema_multimodal"
Cohesion: 0.15
Nodes (12): armar_relato(), sistema_multimodal(), Al desplegar (M5), conviene…, Backlog (después de la Demo), Dónde está hoy el recorrido completo, Guion sugerido (bloques, sin minutos obligatorios), Plan para Demo Day — Amparo, Prioridad 1 · [P1] La experiencia de punta a punta en una sola llamada, con el fundamento a la vista (+4 more)

### Community 43 - "corrida_m4.py"
Cohesion: 0.15
Nodes (10): versiones(), cerrar(), _git(), gpu(), guardar(), huella_eval_set(), manifiesto(), _sha() (+2 more)

### Community 44 - "TokFalso"
Cohesion: 0.20
Nodes (3): _Enc, test_ids_parada_incluye_eos_y_marcas_de_turno(), TokFalso

### Community 45 - "T6 - Corrida del harness: notas para T8 (Lucas -> Nico)"
Cohesion: 0.16
Nodes (12): m10 - valvula ADVERSARIAL (fecha|plazo_dias), Criterio valvula (campos que deben venir null), doc06_notificacion_borrosa.jpg - ADVERSARIAL mojada, sin fecha ni plazo, Corrida local T6 (RTX 5060, M3 sustituto), Hallazgo 1: entidad y plazo_dias salen null, Hallazgo 2: m10 inventa 'dos semanas' en pretension_visible, Hallazgo 3: sentido invertido en doc03 (m04/m05), T6 - Corrida del harness: notas para T8 (Lucas -> Nico) (+4 more)

### Community 46 - "Corrida"
Cohesion: 0.14
Nodes (6): ahora_bogota(), comparar(), Corrida, hardware(), listar(), ultimas()

### Community 47 - "generacion.py"
Cohesion: 0.20
Nodes (4): sembrar(), cargar_modelo(), ids_parada(), cargar_modelo()

### Community 48 - "publicar_todo"
Cohesion: 0.20
Nodes (5): faltantes(), publicar_todo(), CorridaFalsa, test_publicar_todo_no_publica_nada_si_falta_uno_y_dice_quien_lo_genera(), test_publicar_todo_publica_solo_si_estan_todos()

### Community 49 - "juez.py"
Cohesion: 0.11
Nodes (10): _degradar(), experimento_inyeccion(), experimento_validez(), familia_de(), orden_de_candidatos(), clave(), respuesta_floja(), tamano_declarado() (+2 more)

### Community 50 - "metricas.py"
Cohesion: 0.06
Nodes (26): abstencion(), accuracy(), acierto_juridico(), acierto_por_caso(), adherencia_estructural(), adherencia_vocabulario(), baseline_clase_mayoritaria(), bootstrap_ic() (+18 more)

### Community 51 - "ModeloFalso"
Cohesion: 0.18
Nodes (5): generador_hf(), ModeloFalso, test_generador_hf_cuenta_tokens_y_apaga_el_adaptador_si_se_pide(), test_generador_hf_recorta_la_cola_y_anota_el_caso(), test_generar_lote_es_greedy_con_padding_izquierdo_y_lo_restaura()

### Community 52 - "json"
Cohesion: 0.19
Nodes (7): cobertura_clasificador(), imprimir(), main(), medir(), _palabras(), _textos(), _json_de()

### Community 53 - "_ctx_medido"
Cohesion: 0.16
Nodes (14): acierto_por_item(), harness(), resumen_juez(), casos_perdidos(), tabla(), _ctx_medido(), test_el_contrato_tiene_las_cinco_clausulas(), test_guardar_escribe_lo_que_va_al_repo() (+6 more)

### Community 55 - "Agente"
Cohesion: 0.09
Nodes (6): abstenerse(), con_pregunta_triable(), leer_triable(), Agente, T7 - Enchufe real de M3, t_abstencion_del_motor()

### Community 56 - "escribir_relatos"
Cohesion: 0.11
Nodes (11): _cliente_groq(), correr_con_reloj(), CupoAgotado, _es_cupo(), escribir_relatos(), fuga_contra_eval(), _prompt_relato(), _AgenteQueTragaErrores (+3 more)

### Community 57 - "test_pipeline_m5.py"
Cohesion: 0.17
Nodes (11): agente_estudiante(), objetivo(), _hechos(), _libres(), test_acuerdo_profesor_gold_con_un_profesor_perfecto(), test_el_estudiante_que_copia_al_profesor_decide_lo_mismo(), test_el_estudiante_recibe_el_relato_y_no_el_prompt_del_profesor(), test_el_prompt_del_estudiante_nombra_todos_los_hechos_extraibles() (+3 more)

### Community 58 - "redaccion.py"
Cohesion: 0.16
Nodes (7): citas_en_texto(), citas_de(), construir_prompt(), medir(), redactar(), _texto_pivote(), verificar_texto()

### Community 59 - "time"
Cohesion: 0.16
Nodes (6): Cronometro, imprimir(), _correr(), entorno(), _linea(), main()

### Community 60 - "M3: cuatro arquitecturas sobre 103 casos comunes"
Cohesion: 0.22
Nodes (7): Bug heredado latencia_s_por_caso = 0.0 (conservado), Desviaciones respecto a los notebooks, Art. 6 Decreto 2591 de 1991 (arbol de decision), Agente: pasos censurados y veredicto_presupuesto, Coste: GPU local vs llamadas API (m3_costos.json), M3: cuatro arquitecturas sobre 103 casos comunes, Tesis: modelo pequeno afinado sobre art. 6 supera a la recuperacion

### Community 61 - "REPORTE: Triaje de acciones constitucionales colombianas"
Cohesion: 0.28
Nodes (7): Corpus normativo (data/normas.json), Leonardo Galeano (abogado responsable del corpus), Apendice: cada cifra y su artefacto, Cobertura del corpus: techo de ranking, no de cobertura, Efectos adversos del RAG: abstencion indebida y citas incompletas, Recall en clases criticas (habeas_corpus, tutela), REPORTE: Triaje de acciones constitucionales colombianas

### Community 62 - "Contexto"
Cohesion: 0.17
Nodes (8): cargar(), acuerdo_profesor_gold(), Contexto, descargar(), etiquetar_con_profesor(), _ProfesorFalso, test_etiquetar_descarta_lo_que_el_profesor_no_pudo_extraer(), test_etiquetar_para_con_el_cupo_y_retoma()

### Community 63 - "doc03 Respuesta a derecho de peticion (cumplimiento, negativa a publicar contratos)"
Cohesion: 0.32
Nodes (6): doc03 Respuesta a derecho de peticion (cumplimiento, negativa a publicar contratos), Accion de cumplimiento (accion judicial anunciada por el peticionario), Alcaldia de Puerto Almendro (entidad ficticia, radicado SG-0987), Derecho de peticion, Ley 1712 de 2014, articulo 10 (deber de publicar contratos), SECOP (Sistema Electronico de Contratacion Publica)

### Community 64 - "medir"
Cohesion: 0.24
Nodes (6): cargar_eval(), medir(), _CostosFalsos, test_escribir_relatos_retoma_y_filtra_la_fuga(), test_medir_vacia_la_cache_del_estudiante_y_mide_las_llamadas(), test_rehacer_estudiante_borra_lo_ya_medido()

### Community 65 - "delta_con_sin_imagen"
Cohesion: 0.10
Nodes (16): delta_con_sin_imagen(), _media(), Delta: misma pregunta con imagen y sin ella, m01 no es estable (extractor de hechos de M3 no determinista), 1. Cómo se verificó, 2. Fortalezas, 3. Observaciones, 4. Prioridades para Demo Day (+8 more)

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

### Community 71 - "degeneracion"
Cohesion: 0.33
Nodes (3): _anatomia_de_la_cola(), _cola_tras_el_bloque(), degeneracion()

### Community 72 - "_jurisprudencia_conocida"
Cohesion: 0.40
Nodes (3): _clave_sentencia(), _claves_jurisprudencia(), _jurisprudencia_conocida()

### Community 73 - "doc01_respuesta_eps.png (Respuesta a derecho de petición, EPS)"
Cohesion: 0.40
Nodes (5): doc01_respuesta_eps.png (Respuesta a derecho de petición, EPS), EPS Salud Serena S.A.S. (entidad ficticia), Negación de autorización por falta de prestador contratado en la red, Procedimiento: reemplazo total de cadera derecha (ordenado por ortopedia), Respuesta a derecho de petición (radicado SS-AUT-0193)

### Community 74 - "doc06 Notificación por aviso borrosa (imagen eval M4)"
Cohesion: 0.47
Nodes (5): doc06 Notificación por aviso borrosa (imagen eval M4), Inspección Municipal de Policía de Villa Serena (entidad ficticia), Marca DOCUMENTO SINTÉTICO / GENERADO (uso académico SI4006 M4 Amparo, sin validez jurídica), Notificación por aviso (procedimiento por comportamiento contrario a la convivencia), Plazo de descargos en días hábiles ocluido por mancha de tinta

### Community 76 - "m01 · doc01_respuesta_eps.png"
Cohesion: 0.14
Nodes (13): Leído del documento por un modelo de visión · no verificado, Leído del documento por un modelo de visión · no verificado, Leído del documento por un modelo de visión · no verificado, m01 · doc01_respuesta_eps.png, m06 · doc04_respuesta_car.png, m10 · doc06_notificacion_borrosa.jpg, Plan B · salida GRABADA de la corrida 20261101T203828Z, Por qué (+5 more)

### Community 77 - "ClienteEstudiante"
Cohesion: 0.18
Nodes (4): ClienteEstudiante, _Respuesta, _ClienteRelatos, test_escribir_relatos_para_si_se_acaba_el_cupo_y_guarda()

### Community 78 - "m4_multimodal.py"
Cohesion: 0.15
Nodes (15): cargar_imagenes(), cargar_lector(), Contexto, correr(), correr_harness(), cronometrar(), descargar(), enchufar_m3() (+7 more)

### Community 79 - "doc05 Notificacion de Suspension del Servicio de Acueducto (imagen sintetica)"
Cohesion: 0.50
Nodes (4): doc05 Notificacion de Suspension del Servicio de Acueducto (imagen sintetica), Acuerdo de pago como alternativa a la suspension, Aguas de Villa Serena S.A. E.S.P. (empresa ficticia de acueducto), Suspension del servicio publico domiciliario por saldo vencido (plazo 5 dias habiles)

### Community 80 - "sesgo_longitud"
Cohesion: 0.25
Nodes (3): sesgo_longitud(), _JuezGuionado, t_longitud()

### Community 81 - "latencia_por_componente"
Cohesion: 0.29
Nodes (6): corrida_m4_con_tiempos(), _fila(), latencia_por_componente(), _pct(), test_latencia_por_componente_resta_bien(), test_latencia_por_componente_sobre_el_scorecard_de_m4()

### Community 83 - "autoprueba_integracion.py"
Cohesion: 0.04
Nodes (46): guardar_checkpoint(), _agente_pelado(), _IndiceFalso, _nb(), _pipeline(), prueba(), t_acuerdo_jueces(), t_anotacion() (+38 more)

### Community 86 - "SistemaHibrido"
Cohesion: 0.29
Nodes (3): SistemaHibrido, t_extractor_mudo(), t_hibrido()

### Community 87 - "ctx"
Cohesion: 0.20
Nodes (3): AgenteFalso, ctx(), LectorFalso

### Community 88 - "recortar_al_bloque"
Cohesion: 0.40
Nodes (4): recortar(), generar(), recortar_al_bloque(), test_recortar_quita_la_cola_degenerada()

### Community 89 - "scorecard.py"
Cohesion: 0.14
Nodes (9): construir_tabla_delta(), _mediana(), _schema_mecanismo(), tabla_markdown(), _tabla_y_guardar(), test_peor_caso_lista_todos_los_empatados_con_su_etapa(), test_tabla_delta_tiene_las_5_filas_con_metrica_nombrada(), test_tabla_delta_valores() (+1 more)

### Community 90 - "sistema_visual.py"
Cohesion: 0.16
Nodes (3): LectorVisual, parsear_json(), test_parsear_json()

### Community 91 - "render_salida"
Cohesion: 0.10
Nodes (22): sesgo_autopreferencia(), tabla_puente(), mensajes_few_shot(), render_ejemplo(), render_entrada(), render_salida(), Profesor y estudiante, _cargar() (+14 more)

### Community 92 - "preparar"
Cohesion: 0.33
Nodes (4): nueva(), _git(), preparar(), test_preparar_para_sin_clave_y_crea_la_carpeta_de_la_corrida()

### Community 94 - "BM25"
Cohesion: 0.29
Nodes (3): BM25, texto_indexable(), _tok()

### Community 96 - "pytest"
Cohesion: 0.36
Nodes (6): delta_repetido(), _bloque(), _eval_repetido(), test_delta_repetido_cuenta_por_corrida_y_vacia_antes_de_cada_llamada(), m3(), test_delta_repetido_exige_vaciar_la_cache()

## Knowledge Gaps
- **32 isolated node(s):** `amparo`, `Checklist de anonimizacion (sin caras, nombres, cedulas, firmas ni sellos)`, `Entidades ficticias (EPS Salud Serena, Alcaldia de Puerto Almendro, CORPORIOCLARO, Aguas de Villa Serena)`, `INSTRUCCION_DOMINIO (5 campos JSON)`, `casos_m4.ejemplo.csv` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 699 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Harness de M4: decisiones de T5 y T6 (y T7)` connect `Harness de M4: decisiones de T5 y T6 (y T7)` to `test_criterios.py`, `delta_con_sin_imagen`, `pathlib`, `test_scorecard.py`, `casos_m4.csv: 11 casos sobre 6 imagenes`, `correr_t6`, `metricas.py`, `scorecard.py`, `corridas.py`, `Migracion de notebooks a paquete Python amparo/`?**
  _High betweenness centrality (0.066) - this node is a cross-community bridge._
- **What connects `amparo`, `Checklist de anonimizacion (sin caras, nombres, cedulas, firmas ni sellos)`, `Entidades ficticias (EPS Salud Serena, Alcaldia de Puerto Almendro, CORPORIOCLARO, Aguas de Villa Serena)` to the rest of the system?**
  _32 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `test_criterios.py` be split into smaller, more focused modules?**
  _Cohesion score 0.051287128712871284 - nodes in this community are weakly interconnected._
- **Why does `Migracion de notebooks a paquete Python amparo/` connect `Migracion de notebooks a paquete Python amparo/` to `Amparo: triaje de acciones constitucionales en Colombia`, `Harness de M4: decisiones de T5 y T6 (y T7)`, `M3: cuatro arquitecturas sobre 103 casos comunes`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Should `m3_rag.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06662770309760374 - nodes in this community are weakly interconnected._
- **Why does `Amparo: triaje de acciones constitucionales en Colombia` connect `Amparo: triaje de acciones constitucionales en Colombia` to `M1: el sistema afinado (base, hibrido, afinado)`, `Limitaciones: lo que este trabajo no puede concluir`, `M3: cuatro arquitecturas sobre 103 casos comunes`, `REPORTE: Triaje de acciones constitucionales colombianas`, `Migracion de notebooks a paquete Python amparo/`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Should `test_pipeline_m4.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._