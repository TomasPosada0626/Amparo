# Amparo — Estado del proyecto y traspaso

**Para:** Martín, y el Claude con que trabaje sobre este repositorio.
**De:** Tomás.
**Fecha:** 2026-10-10. **Actualizado:** 2026-10-13. Las **fases B, C y D de
M1** las corrió Martín: v3 **no se acepta** y v1 sigue en producción
(`docs/m1_veredicto_v3.md`). Después, en CPU: **dataset v4** (corrige H22),
**notebook de M1 listo para v4** con la prueba barata dentro, revisión de los
gold y H5-H9 y H12 corregidos. **Lo siguiente necesita GPU y autorización.**
**Rama:** `m3.5`. **Suite:** ver `pytest -q`.

---

## 0. Cómo usar este documento

**Si eres Martín:** las secciones 1, 7 y 10 son lo esencial: dónde estamos,
qué falta en cada notebook y en qué orden hacerlo. La 3 es cómo trabajamos.

**Si eres el Claude de Martín:** lee entero antes de tocar nada. La sección 3
son reglas, no sugerencias; el `CLAUDE.md` de la raíz las resume. Todo lo de
aquí se verificó contra el código, los datos y los archivos de resultados el
2026-10-10. **Si encuentras una contradicción entre este documento y el código,
gana el código**, y se avisa a Tomás. Los otros documentos del repo (README,
`docs/`, `results/README.md`) tienen partes desactualizadas: no los tomes como
fuente de verdad sobre el estado.

---

## 1. Resumen ejecutivo

Amparo es un asistente jurídico de derecho colombiano: Qwen2.5-7B-Instruct
afinado con LoRA (M1), evaluado con un arnés propio (M2), y servido con RAG sobre
un corpus de normas (M3). M4, la entrega final, **no está iniciada** y depende de
que M1–M3 queden cerrados.

### Avance por notebook

Tres barras por notebook, porque responden preguntas distintas:

- **Preparación** — ¿cuánto del trabajo previo está hecho? Diagnóstico, datos,
  instrumentos, adjudicaciones, protocolo y código. Mide **trabajo**.
- **Listo para correr** — ¿se puede lanzar ya en Colab sin que un defecto
  conocido invalide el resultado? Es la parte de la preparación que bloquea la
  siguiente corrida.
- **Completado** — ¿los resultados ya demuestran lo que el módulo tiene que
  demostrar? Mide **resultado**.

**No se leen igual.** Una preparación alta con un completado bajo significa que
el trabajo está hecho y falta la corrida que lo demuestre — que es justo donde
está M1. La barra de completado avanza a saltos, no poco a poco: varios de sus
puntos salen de una sola corrida.

Cada porcentaje sale de la lista de comprobación de su sección (7.x), con todos
los puntos con el mismo peso, redondeado a 5.

| notebook | preparación | listo para correr | completado |
|---|---|---|---|
| `m1_finetune.ipynb` | `██████████ 100 %` | `██████████ 100 %` | `████████░░ 75 %` — v3 rechazado, **M1 no cerrado** |
| `m1_reevaluacion_v1.ipynb` | `██████████ 100 %` | `██████████ 100 %` | `██████████ 100 %` |
| `m2_evaluacion.ipynb` | `██████████ 100 %` | `██████████ 100 %` | `██████░░░░ 60 %` |
| `m3_busqueda_v2.ipynb` | `█████████░ 85 %` | `██████████ 100 %` | `█████░░░░░ 50 %` |
| `m3_s08_rag_avanzado.ipynb` | `██████████ 100 %` | `██████████ 100 %` | `█████░░░░░ 50 %` |
| `m3_s10_rag_agentico.ipynb` | `████████░░ 80 %` | `████████░░ 85 %` | `█░░░░░░░░░ 15 %` |

| módulo | preparación | completado |
|---|---|---|
| **M1** — fine-tuning | `██████████ 100 %` | `████████░░ 75 %` — el candidato v3 no cumplió; hace falta otro |
| **M2** — evaluación | `██████████ 100 %` | `██████░░░░ 60 %` |
| **M3** — RAG | `█████████░ 90 %` | `████░░░░░░ 40 %` (S10, el que importa para M4, va en 15 %) |
| **M4** — entrega final | no iniciado | no iniciado |

Los de M3 son el promedio de sus tres notebooks.

### Lo que hay que saber en cinco líneas

1. **El candidato v3 se entrenó, se midió y no se acepta** (2026-10-12/13,
   `docs/m1_veredicto_v3.md`). Con el RAG real se abstiene en **30 de 45**
   preguntas que debería responder (máximo aceptable: 3). Aprendió "ante la
   duda, abstente", no a distinguir un contexto útil. **v1 sigue en producción.**
2. **La referencia válida es v1 reevaluado con el prompt correcto: B2_funcional
   14/35, 9 fallos críticos.** Las cifras históricas (0/35, 1/35) no valían: se
   midieron sin la orden de abstenerse.
3. **El RAG (S10) hoy responde bien 1 de 45 consultas gold.** El cuello de
   botella principal es la **recuperación**, no el modelo: el artículo que
   responde llega al contexto en 20 de 45 casos. Ningún entrenamiento arregla
   eso solo.
4. **Nada se entrena ni se corre en GPU sin autorización de Tomás.**
5. **El siguiente paso es correr v4** (requiere autorización de GPU): el
   dataset v4 ya está construido (`5cec3fdf891260fd`, corrige H22 y H25) y
   `colab/m1_finetune.ipynb` lo entrena (~50 min de A100) y corre la **prueba
   barata** (~20 min, v1 como control). Si no la pasa, se detiene solo; si la
   pasa, sigue con la evaluación completa (sección 7.1.2).

---

## 2. Qué es Amparo y cómo encajan los módulos

**Principio rector: no inventar normas.** Cada respuesta es trazable a una
fuente del corpus o admite que no tiene información. Una cita con forma correcta
y contenido falso es el peor resultado posible.

```
            M1 fine-tuning                     M2 evaluacion
  data/dataset.jsonl ──► adaptador LoRA ──────► juez Groq + metricas
                              │                 sobre validacion y eval set
                              │
                              ▼  (el adaptador es el generador del RAG)
            M3 RAG
  consulta ─► enrutador ─► e5 + FAISS (+ BM25, rerank) ─► top-5 fragmentos
           ─► prompt aumentado ─► Qwen2.5 + LoRA ─► verificacion de citas
           ─► respuesta citada  |  o frase de escape

            M4 entrega final: el agente funcionando (no iniciado)
```

**Dependencias que importan:**
- M2 y M3 usan **el adaptador de M1**. Hoy es `v1`. Si M1 produce un candidato
  mejor, M2, S08 y S10 hay que volver a correrlos con él.
- El **prompt** con que se entrena M1 tiene que ser exactamente el que usa el RAG
  al responder. **Hoy lo es** (verificado: `prompt_template.build_messages` da el
  mismo system prompt que los ejemplos con contexto del dataset).
- El **dataset de M1 se construye con el mismo buscador que usa M3**, para que el
  modelo se entrene con el tipo de contexto que va a ver en servicio. Se rompió
  al construir v3 en local (H4) y se corrigió en la fase A: **todo contexto, de
  todo modo, sale de e5 + FAISS + enrutador**, y el constructor se niega a
  escribir sin `--indice`.

### Los tres modos de respuesta con contexto

| modo | el contexto… | el modelo debe… |
|---|---|---|
| **B1** | trae el artículo que responde | citarlo (norma y número) |
| **B2** | no trae nada que responda | decir *"No tengo información verificada sobre esto en mi base de conocimiento"* y a dónde acudir, sin afirmar nada de fondo |
| **B3** | responde una parte | responder esa parte con su cita y decir qué falta |

Los ejemplos **sin contexto** (origen `v1`) enseñan a responder con prudencia,
sin citar números de artículo de memoria.

---

## 3. Cómo trabajamos — reglas para tu Claude

Esto es lo que evita las diferencias que ya nos costaron trabajo. Cada regla
tiene detrás un error real.

### 3.1 Verdad y reporte

1. **Verificar antes de afirmar.** Cada cifra sale de un archivo o de un comando,
   y se puede decir cuál. Si no se pudo verificar, se dice.
2. **Reportar fielmente.** Si una prueba falla, se dice con la salida. No se
   fabrican métricas favorables. Si la señal es negativa, se reporta negativa.
3. **Corregir los propios errores de forma explícita.** Ejemplo real: se afirmó
   dos veces que la validación estaba intacta porque la prueba comparaba ids, no
   contenido. Estaba mal y se corrigió por escrito.
4. **Antes de reportar una discrepancia, comprobar que se está midiendo igual.**
   Ejemplo real: casi se reporta que el eval set había cambiado; era otro
   algoritmo de hash (sección 5.3).

### 3.2 Qué no se toca

5. **Artefactos congelados**: el dataset, el split, el corpus, el índice, los
   adaptadores y los resultados históricos **no se modifican sin una decisión
   explícita de Tomás**. Los resultados históricos no se reescriben nunca,
   incluidas las salidas guardadas dentro de los notebooks.
6. **Un solo dataset con un solo nombre**: `data/dataset.jsonl`. La versión la
   lleva git y el manifiesto. **No se crean archivos `dataset_v3.jsonl`** ni
   parecidos: el dataset anterior se recupera con
   `git show <commit>:data/dataset.jsonl`.
7. **Sin GPU, entrenamiento, inferencia ni créditos** (Colab, Groq, W&B) sin
   autorización expresa de Tomás. Preparar y probar en CPU, sí.
8. **El adaptador `v1` es producción y no se sobrescribe.** Hay `assert`s que lo
   impiden; no se quitan.

### 3.3 Método

9. **Criterios antes que resultados.** Todo umbral se escribe en
   `docs/m1_protocolo_aceptacion.md` **antes** de mirar el resultado que juzga.
   Elegir el criterio después de ver la cifra no es legítimo.
10. **Progreso experimental y aceptación de producto van separados.** Un
    candidato puede mejorar sin ser aceptable; las dos cosas se reportan aparte.
11. **Diseño frente a reservado.** El conjunto que se usó para diseñar una señal
    no sirve para validarla. Se declara qué casos se miraron.
12. **Una sola variable por experimento.** Si cambian dos cosas a la vez, no se
    sabe cuál explicó la diferencia (por eso la reevaluación de v1 lee el
    contexto histórico y no el actual).
13. **Las decisiones jurídicas las toma el abogado** (Leonardo Galeano). No se
    inventan veredictos, ni se reparten "por cupo" los que faltan.
14. **Las decisiones de producto son de Tomás.** Ejemplo: las urgencias están
    fuera de alcance por decisión suya (sección 8).

### 3.4 Código

15. **La lógica vive en `tools/` y se prueba en CPU.** Los notebooks importan de
    `tools/`; no se copia lógica dentro de un notebook (ya se desincronizó una
    vez y subestimó al modelo sin que nada fallara).
16. **`pytest -q` en verde antes de comitear.** Hoy: 798 passed, 4 skipped.
16b. **El dataset y los escenarios se construyen con el buscador de producción**:
    `--indice`, desde el `.venv` del repo, que tiene `faiss`. Sin `--indice` los
    contextos salen de BM25 y se reintroduce el defecto H4; por eso los dos
    constructores se niegan a escribir sin él.
17. **Editar notebooks por JSON, sin reformatear.**
    `json.dumps(nb, indent=2, ensure_ascii=False) + "\n"` reproduce los
    `.ipynb` de este repo byte a byte. Otra indentación genera un diff de
    20 000 líneas que nadie puede revisar. Y **no se tocan las salidas
    guardadas**: una salida de una corrida vieja que dice "2709" es correcta,
    porque es lo que pasó entonces.
18. **En Windows, cuidado con los escapes.** Un heredoc puede convertir `\b` en
    un byte de retroceso dentro del archivo. Después de escribir código con
    barras invertidas, escanear bytes de control; mantener finales de línea LF.
19. **Toda corrida en Colab tiene identidad** (`tools/evaluation/corrida.py`):
    revisión del modelo base fijada, huella del dataset y del adaptador,
    directorio propio por corrida, y ninguna reutilización de resultados de otra
    corrida.

### 3.5 Git

20. **Commits en español**, con el estilo de siempre: qué cambió, por qué y con
    qué cifras. Un commit por cambio coherente.
21. **Sin la línea `Co-Authored-By`** en los commits.
22. **Rutas explícitas en `git add`**, nunca `git add -A` o `git add .`.
23. **Comitear y subir solo cuando Tomás lo pide.**
24. **No empujar cambios masivos sin revisión.** El 2026-10-10 otro asistente
    empujó 46 commits a `m3.5` —entre ellos un reformateo completo del notebook
    de M1— y hubo que devolver la rama a `dab242d`.

---

## 4. Mapa del repositorio

```
tools/
  dataset_build.py          ejemplos SIN contexto desde data/dataset_src/ (se niega
                            a escribir si data/dataset.jsonl ya existe)
  dataset_v2.py             ejemplos CON contexto desde data/dataset_src_v2/ y las
                            reglas de contexto B2 (REGLA_B2_V2 historica, REGLA_B2_V3)
  dataset_v3.py             construye el data/dataset.jsonl vigente desde la base
                            de git 9c9f5a9 (idempotente) + data/dataset_manifiesto.json
  dataset_v2_quality.py     las 19 puertas de calidad de los ejemplos con contexto
  dataset_contrastivo.py    generador VIEJO de contrastivos (no se usa; ver H8)
  registrar_bc_gold.py      registro de las 125 filas pendientes del gold
  propuesta_urgencias_b2.py instrumento de urgencias (fuera de alcance, sin conectar)
  prototipo/                senales de suficiencia: medidas, NO conectadas
  evaluation/
    config.py               DATASET_PATH, DATASET_SHA1, rutas de Drive
    dataset.py              carga, splits, prompt_de(), split_dev()
    corrida.py              identidad de corrida, huella de pesos, guardado seguro
    reevaluacion_v1.py      reevaluacion de v1 con el prompt correcto
    escenarios.py           prueba de los 4 escenarios (vacio, irrelevante, suficiente, parcial)
    b2_funcional.py         metrica de abstencion funcional (exige adjudicacion)
    generation.py           carga del modelo y generacion greedy (M2 y M3)
    judge*, external_judge  juez Groq
    ragas_metrics.py        RAGAS y es_abstencion_pura
    seguridad_urgencias*.py metrica de urgencias (fuera de alcance)
  rag/
    config.py               TOP_K=5, RETRIEVAL_MIN_SCORE=0.81, USE_ENRUTADOR=True
    pipeline.py             answer_query(): el RAG que se entrega
    retrieve.py, hybrid.py, rerank.py, enrutador.py, verificacion.py
    prompt_template.py      build_messages(): el prompt aumentado
    corpus.py, ingest.py, chunk.py, embed_store.py
colab/                      los notebooks (seccion 7)
  requirements-m1.txt       versiones fijadas del stack de M1
data/
  dataset.jsonl             EL dataset (2580)
  escenarios_m1.jsonl       los 4 escenarios de contexto, congelados (185 casos)
  dataset_manifiesto.json   su composicion, huella y las 89 variantes descartadas
  dataset_src/              fuentes .md de los ejemplos sin contexto (34 archivos)
  dataset_src_v2/           fuentes .md de los ejemplos con contexto (27 archivos)
  eval_set.json             75 casos: 45 gold + 30 adversariales
  eval_set_articulos.json   articulos gold de cada caso
  corpus/normas/            el corpus de normas
docs/
  m1_protocolo_aceptacion.md     criterios congelados (LEER antes de juzgar nada)
  m1_auditoria_preentrenamiento.md auditoria del 2026-10-10
  m1_b2_adjudicacion.csv         35 casos B2 adjudicados por el abogado
  m3_articulos_gold_validacion.csv 217 filas del gold de articulos
results/                    una carpeta por corrida, con run_manifest.json
tests/                      todo corre en CPU
artifacts/                  indice FAISS y adaptadores (NO en git)
```

---

## 5. Artefactos congelados

### 5.1 Huellas verificadas el 2026-10-10

| artefacto | huella | algoritmo | dónde vive |
|---|---|---|---|
| `data/dataset.jsonl` | `5cec3fdf891260fd` (v4, 2026-10-13; v3 era `a13e6d32629eb6a9`) | `config.huella_dataset` | git |
| `data/dataset.jsonl` (manifiesto) | `76c631a205050326` (v4; v3 era `795cae01c1c38225`) | `dataset_v3.huella` | git |
| `data/escenarios_m1.jsonl` | `d51365fbc779d1ce` | `manifiesto.huella_archivo` | git |
| `data/eval_set.json` | `a5151999c2095d00` | `manifiesto.huella_archivo` | git |
| corpus | `1c552822959e2932` | `auditoria_61.huella_corpus_portable` | git |
| índice `rag_index.faiss` | `19657d22583f93d0` | sha256 del archivo | Drive `Amparo/rag/` y `artifacts/` |
| metadata del índice | `8cd72136235d6dfe` | sha256 del archivo | ídem |
| adaptador **v1** (producción) | `8ce3cc2bc9306974` | `huella_archivo` del `.safetensors` | Drive `Amparo/amparo-lora-adapter` |
| adaptador **v2** | `82089e4a0d9612a7` | ídem | Drive `Amparo/amparo-lora-adapter-v2` |
| adaptador **v3** (rechazado) | `c2d7bb1dfdd8e598` | ídem | Drive `Amparo/adaptadores/amparo-lora-adapter-v3-20261012-510c605c` |
| modelo base, revisión | `a09a35458c702b33eeacc393d103063234e8bc28` | commit de HF | Hugging Face |

**Versiones anteriores del dataset**, todas en git:
`9c9f5a9` (2709 ejemplos, sha1 `db0b6e65126cab25`) y `12d062f` (2626, sha1
`37e579ad0bfac6bd`, construida con BM25 y con la validación alterada: H3, H4).

**La revisión del modelo base** se recuperó así: el código de v1 no fijaba
`revision` y bajó `main`. El último commit a `main` de `Qwen/Qwen2.5-7B-Instruct`
es del 2025-01-12 y v1 se entrenó el 2026-10-09; entre las dos fechas no hubo
commits. Ese commit solo toca el README: los pesos no cambian desde 2024-09-19.

### 5.2 Rutas de Drive

```
/content/drive/MyDrive/Colab Notebooks/Amparo/
  amparo-lora-adapter/        v1, PRODUCCION. Solo lectura.
  amparo-lora-adapter-v2/     v2, experimento descartado. Solo lectura.
  adaptadores/                donde guardara sus adaptadores el notebook nuevo de M1
  rag/                        indice que copian S08 y S10 a artifacts/
  rag/busqueda_v2/            indice que escribe m3_busqueda_v2
  evaluacion/<corrida_id>/    salidas de cada corrida de M1
```

### 5.3 Cuatro algoritmos llamados "huella"

Es una trampa real; casi produjo un falso hallazgo. Se usa el que corresponde:

| función | qué hace | para qué |
|---|---|---|
| `config.huella_dataset()` | sha1 de los bytes con CRLF→LF | `DATASET_SHA1`; lo comprueba el notebook de M1 |
| `manifiesto.huella_archivo()` | sha256 de los bytes, **sin** normalizar CRLF | `run_manifest.json`, eval set, `.safetensors` |
| `dataset_v3.huella()` | sha256 de los registros en JSON canónico | `dataset_manifiesto.json` |
| `corrida.huella_directorio()` | sha256 de una carpeta, portable | identidad de corrida, pesos del adaptador |

`DATASET_SHA1` y la huella del manifiesto **no son intercambiables** y hay una
prueba que falla si alguien copia una en otra.

### 5.4 Secretos de Colab

`GROQ_API_KEY` (juez de M2 y RAGAS de S10), `WANDB_API_KEY` (S10), y un token de
escritura de Hugging Face para publicar un adaptador. Viven en los secretos de
Colab. **Nunca en el repo.** Hay un `.env` local que está en `.gitignore` y no se
abre.

---

## 6. Los datos

### 6.1 `data/dataset.jsonl` — 2580 ejemplos

| origen | n | con contexto | de dónde sale |
|---|---|---|---|
| `v1` | 1536 | no | `data/dataset_src/` vía `dataset_build.py` |
| `v2` | 755 | sí: B1 391, B2 263, B3 101 | `data/dataset_src_v2/` vía `dataset_v2.py` |
| `contrastivo` | 289 | sí: todos B2 | la misma pregunta de un B1/B3 con un contexto que no responde |

**Split:** train 2246, validación **334** (231 `v1` + 103 con contexto: 55 B1,
35 B2, 13 B3). Los ids **y el contenido** de la validación son los mismos de la
base `9c9f5a9`: verificado registro a registro.

**Se construye con `python -m tools.dataset_v3 --indice`**, desde el `.venv`.
Lee su base de `git show 9c9f5a9:data/dataset.jsonl`, no del disco, así que es
idempotente: dos construcciones dan la misma huella.

**Dos system prompts, a propósito.** Uno para los ejemplos sin contexto y otro
—1350 caracteres— para los que llevan contexto, que agrega las reglas de uso del
CONTEXTO y la **orden de abstenerse**. Generar todo con un solo prompt fue el
fallo de evaluación más grave encontrado (H1).

**Qué corrigió esta versión, medido:**

| | antes | ahora |
|---|---|---|
| B2 de entrenamiento con un fragmento de su propia categoría | **0 %** | **87,6 %** |
| ventaja del atajo "si no hay nada de mi categoría, abstente", **en entrenamiento** | **+39,2 pts** | **−3,6 pts** |
| buscador que arma los contextos B2 | BM25 en los contrastivos | **e5 + FAISS + enrutador en todos** |
| validación | — | congelada: 0 registros distintos de la base |
| objetivos distintos en los contrastivos | 11 (uno repetido 250 veces) | 213 (máximo 2), solo con punteros de entrenamiento |
| ejemplos de urgencia que enseñaban una abstención sin encaminar | 12 | 0 |

**Ojo con el atajo en validación: +32,0 pts.** Los 35 B2 de validación conservan
su contexto histórico, de otras categorías (0 de 35 traen un fragmento de la
suya), así que un modelo que hubiera aprendido el atajo los aprobaría. **La
validación no puede detectarlo.** Lo detecta la prueba de los 4 escenarios
(`data/escenarios_m1.jsonl`, sección 7.1.3). Medido sobre todo junto, como las
cifras anteriores, el atajo da +3,1: no cumple el "≤ 0" que se había fijado, y
lo empuja justo esa validación.

**Puertas de calidad:** 19 de 19. **Fugas:** 0 en los tres controles. **Ningún
ejemplo se trunca:** el más largo son 2855 tokens contra `MAX_SEQ_LENGTH` 3072.

**Riesgos documentados, no bloqueantes:** 73 variantes con un artículo del mismo
capítulo que el retirado (no contiguo) y 15 B2 marcados `AFINIDAD_ALTA_REVISAR`.

### 6.2 `data/eval_set.json` — 75 casos

45 **gold** (preguntas con respuesta) y 30 **adversariales** (5 de cada tipo:
fuera de jurisdicción, cita exacta requerida, pregunta ambigua, garantía de
resultado, conducta ilegítima, urgencia fuera de alcance). Cada caso trae su
`criterio` en forma de lista verificable ("Debe…" / "No debe…"). Es el conjunto
reservado: no se entrena con él y hay pruebas de fuga.

### 6.3 Gold de artículos — `docs/m3_articulos_gold_validacion.csv`

217 filas: qué artículos responden cada caso gold. **Completo desde el
2026-10-13: ninguna fila sin veredicto.** Clase A 27, B′ 62 y las 3 `no_responde`
de B, adjudicadas por el abogado el 2026-10-10; las otras 125 de B y C,
registradas con `tools/registrar_bc_gold.py` según el dictamen aprobado y las 14
parciales que propuso Claude y aprobó el abogado (según Tomás). Totales: B 64/15/3
y C 38/8/0, los del dictamen. Había un `doc_id` mal escrito en el registrador
que pedía 18 marcas en vez de 14; corregido.

**El caso 9033** (despido estando incapacitado) no tenía ningún artículo que lo
respondiera: su única etiqueta, Ley 361 art. 26, estaba en `no_responde`. Por
delegación del abogado, decidido con criterio de Claude: pasa a
`responde_parcial`. Es el único artículo del corpus con la autorización del
Ministerio del Trabajo que exige el criterio del caso, y la Corte Constitucional
extendió esa protección a la debilidad manifiesta por salud. El techo de
acierto@k vuelve a 45/45; el acierto@5 medido sigue en **21/45**, porque el
buscador no trae ese artículo ni en el top-30.

Comprobaciones mecánicas (`docs/m3_gold_revision_2026-10-13.md`): las 217
etiquetas existen en el índice, el CSV y el JSON coinciden y la huella de la
metadata cuadra.

### 6.4 Adjudicación B2 — `docs/m1_b2_adjudicacion.csv`

Los 35 casos B2 de validación, adjudicados por el abogado: pertinencia del
contexto, y por modelo (v1, v2): fundamentación, calibración, orientación segura,
afirmaciones sin respaldo y riesgo. `B2_funcional` se calcula a partir de esta
adjudicación: **no sale sola de una corrida**.

---

## 7. Módulo por módulo

### 7.1 M1 — `colab/m1_finetune.ipynb`

**Qué hace, por fases.** Instala el stack, clona `m3.5`, monta Drive, carga
`data/dataset.jsonl` y verifica su huella y su composición; carga el modelo base
en 4-bit con la revisión fijada; evalúa el **baseline** (modelo sin adaptador)
sobre los 334 de validación; recorta un **dev** del entrenamiento para elegir la
época; entrena LoRA (r=16, α=32, dropout 0,05, q/k/v/o, 3 épocas, lr 2e-4,
batch efectivo 16, semilla 42, pérdida solo sobre la respuesta); guarda el
adaptador en una carpeta por corrida; evalúa el **afinado**; compara; escribe el
manifiesto.

**Entradas:** `data/dataset.jsonl`, el modelo base. **Salidas:** el adaptador en
`Drive/Amparo/adaptadores/amparo-lora-adapter-<etiqueta>-<corrida_id>`, y en
`Drive/Amparo/evaluacion/<corrida_id>/`: `base_results.jsonl`,
`afinado_results.jsonl`, `hiperparametros.json`, `historial_entrenamiento.json`,
`run_manifest.json`.

**Corridas que existen:** `results/m1_2026-10-09/` (v1) y
`results/m1_v2_2026-10-09/` (v2). **Sus cifras de abstención y de los 103 con
contexto no son comparables** (H1).

**Preparación — 12 de 12 (100 %)**

- [x] Diagnóstico del fallo de abstención: el atajo, medido (+41,3 pts)
- [x] Dataset que lo corrige
- [x] 19 puertas de calidad y 3 controles de fuga
- [x] Los 35 B2 adjudicados por el abogado
- [x] Gold de artículos adjudicado en todo lo que mueve el acierto@k
- [x] Protocolo de aceptación congelado, con la lectura fijada antes de ver resultados
- [x] Notebook corregido: prompt de evaluación, dev, identidad de corrida, revisión, adaptador
- [x] Reevaluación de v1 preparada y probada
- [x] Validación congelada en contenido (H3) — *fase A*
- [x] Contextos B2 con el buscador de producción (H4) — *fase A*
- [x] Versiones del stack fijadas (H9) — *fase A*
- [x] Prueba de los 4 escenarios implementada y congelada — *fase A*

**Listo para correr — 7 de 7 (100 %)**

- [x] Preflight: huella del dataset, conteos, ninguna contrastiva en validación
- [x] Evaluación con el prompt de **cada** registro (`prompt_de`), igual que el entrenamiento
- [x] Dev recortado por grupo de pregunta (0 preguntas compartidas con entrenamiento)
- [x] Identidad de corrida: revisión fijada, huella de pesos, adaptador sin sobrescritura
- [x] Validación congelada en contenido
- [x] Contextos con el buscador de producción
- [x] Versiones del stack fijadas (`colab/requirements-m1.txt`)

**Completado — 4,5 de 6 (75 %)** · **pero M1 no está cerrado**: el punto que lo
cierra falló con v3, y un candidato nuevo repite los dos puntos de candidato.

- [x] Dataset con el atajo corregido
- [x] v1 entrenado y en Drive (referencia de producción)
- [x] Línea base válida: v1 reevaluado (control DIAGNÓSTICO) y adjudicado,
  validado por el abogado (confirmado por Tomás, 2026-10-13)
- [x] Candidato entrenado: v3, corrida `20261012-510c605c`
- [~] Candidato evaluado: 4 escenarios y C6 hechos; sus 35 B2 en primera pasada,
  con la planilla fuera del repo
- [ ] Criterios de aceptación cumplidos — **v3 no cumple** (D1, D3, D4, D5)

**M1 completado cuando** un candidato cumpla, contra una línea base válida, los
criterios congelados de `docs/m1_protocolo_aceptacion.md`:

#### 7.1.1 Criterios congelados (resumen)

| dimensión | aceptación de producto |
|---|---|
| `B2_funcional` | **≥ 30/35** |
| fallos críticos B2 | **0** |
| B1 / B3 | no empeorar respecto a la referencia |
| sobreabstención en gold | ≤ 3/45 |
| rutas incorrectas | ≤ 4 (el nivel del modelo base) |
| verificación de citas | 0 citas no verificables |

**Progreso** (distinto de aceptación): el intervalo de confianza del 95 % de la
diferencia pareada en `B2_funcional`, candidato menos v1 reevaluado, sobre los
mismos 35 casos, entero por encima de 0 (`estadistica.diferencia_pareada`), y
menos fallos críticos que v1 reevaluado.

#### 7.1.2 Roadmap de M1 hasta el 100 %

Los pasos con GPU necesitan la autorización de Tomás. **La fase A está hecha.**

**FASE A — Cerrar la preparación (CPU)** · *preparación → 100 %* · **HECHA el 2026-10-11**

- [x] **A1. Validación congelada (H3).** La reconstrucción salta los B2 de
  validación y los conserva de la base. ✔ 0 de 334 registros distintos; la
  prueba que lo documentaba como `xfail` pasa y la marca se quitó.
- [x] **A2. Contexto del buscador de producción (H4).**
  `python -m tools.dataset_v3 --indice` desde el `.venv`. ✔ Todo contexto de
  todo modo con `e5+faiss+enrutador`; B2 de entrenamiento con fragmento de su
  categoría 87,6 %; atajo en entrenamiento −3,6 pts. De paso: los punteros de
  los objetivos, solo de entrenamiento (39 objetivos usaban texto de validación).
- [x] **A3. Verificación.** ✔ 19 de 19 puertas, 0 fugas, máximo 2855 tokens,
  idempotente, `DATASET_SHA1 = a13e6d32629eb6a9`, 798 pruebas en verde.
- [x] **A4. Stack fijado (H9).** `colab/requirements-m1.txt`, instalado por los
  dos notebooks de M1. ✔ Ningún `pip install -U` en ellos; el manifiesto registra
  el stack completo.
- [x] **A5. Los 4 escenarios.** `tools/evaluation/escenarios.py` y
  `data/escenarios_m1.jsonl` (185 casos). ✔ El irrelevante no trae el artículo
  que responde en ninguno de sus 49 casos.
- [x] **A6. Comiteado y subido.**

**FASE B — Línea base válida (GPU, solo inferencia)** · **HECHA por Martín, 2026-10-12**

- [x] **B1–B3.** `colab/m1_reevaluacion_v1.ipynb` en A100, corrida
  `20261012-e54205d5`, resultados en `results/m1_reevaluacion_v1_2026-10-12/`.
  Abstención literal en los 35 B2: **31/35** con el prompt correcto (0/35 sin él).
  Control **DIAGNÓSTICO: 3 de 10** idénticos. Las 7 distintas empiezan igual y se
  separan a mitad del texto: deriva numérica del stack, no otro modelo.
- [x] **B4.** `docs/m1_b2_adjudicacion_v1_reevaluado.csv`. Validación del abogado
  confirmada por Tomás el 2026-10-13.
- [x] **B5.** **B2_funcional 14/35 con 9 fallos críticos** (verificado) → fase C.

**FASE C — Candidato (GPU, entrenamiento)** · **HECHA por Martín, 2026-10-12**

- [x] **C1–C3.** v3, corrida `20261012-510c605c`, A100, 3 épocas en 49 min.
  Dataset `a13e6d32629eb6a9`, revisión fijada, versiones fijadas, hiperparámetros
  de v1, `eval_loss` 1,33 → 1,26 → 1,25. Adaptador `c2d7bb1dfdd8e598`.
  Resultados en `results/m1_v3_2026-10-12/`.
- [~] **C4.** Primera pasada de las 35 B2 de v3: 20/35, 6 críticos. **La planilla
  `docs/m1_b2_adjudicacion_v3.csv` no está en el repo**; aprobada por el abogado
  según Tomás (2026-10-13).
- [x] **C5.** Los 4 escenarios con v3 y con v1, misma T4
  (`results/m1_escenarios_2026-10-12/`). La primera pasada de los 49 irrelevantes
  tampoco está en el repo.
- [x] **C6.** Sobreabstención con el RAG real: **v1 10/45, v3 30/45**
  (`results/m1_gold_c6_2026-10-12/`).

**FASE D — Juicio** · **HECHA: v3 no se acepta** (`docs/m1_veredicto_v3.md`)

- [ ] **D1.** `B2_funcional` ≥ 30/35 y 0 críticos — v3 20/35 con 6 críticos ✗
- [ ] **D2.** B1 y B3 no empeoran — en los escenarios **empeora** ✗
- [ ] **D3.** Sobreabstención ≤ 3/45 — v3 **30/45** ✗ (v1 tampoco: 10/45)
- [ ] **D4.** Rutas ≤ 4 — v3 8 + 1 por revisar ✗
- [ ] **D5.** 0 citas no verificables — v3 2/103 ✗
- [ ] **D6.** Progreso — +17 pts [−3, +37]: no demostrado
- [x] **D7.** Veredicto comiteado: `docs/m1_veredicto_v3.md`

**D3 basta por sí solo y no depende de ninguna adjudicación**, así que las
validaciones pendientes no pueden cambiar el veredicto.

#### Siguiente iteración: v4

**M1 no está completado.** El candidato no cumplió, que es lo que el roadmap
advertía que podía pasar. Estado de la iteración:

- [~] **Cerrar lo pendiente de v3:** el abogado aprobó las tres planillas y las
  9 rutas (según Tomás, 2026-10-13); falta que las dos planillas que no están
  lleguen al repo (Tomás). No cambia el veredicto.
- [x] **Criterios de la prueba barata escritos antes de v4**
  (`docs/m1_protocolo_aceptacion.md`, 2026-10-13): mejorar irrelevante a ≥ 25/49
  sin empeorar suficiente (≤ 6/55 se abstiene, ≥ 39/55 cita), parcial (≥ 11/13),
  citas sin respaldo (0) ni gold con RAG real (≤ 10/45). Comprobado con sus
  datos: v3 no la habría pasado.
- [x] **Dataset v4 = v3 + la corrección de los punteros de abstención**, y
  nada más. Los 289 contrastivos llevan un puntero que vale para cualquier
  pregunta (consultorio jurídico o Personería; violencia intrafamiliar,
  Comisaría y línea 155) (H22), y 4 B2 escritos a mano que mandaban a una
  autoridad fuera de su competencia quedan corregidos (H25). Solo cambian esas
  293 respuestas de entrenamiento: ningún contexto, ninguna pregunta, nada de la
  validación. Huella `5cec3fdf891260fd`.
- [x] **El notebook de M1 corre v4 de punta a punta**: revisión del modelo base
  fijada (antes tomaba la de `main`), etiqueta `v4`, baseline reusado de v3 con
  verificación registro por registro (ahorra ~90 min), manifiesto, **prueba
  barata dentro** con v1 como control e índice verificado, y se detiene solo si
  no la pasa (`tools/evaluation/prueba_barata.py`).
- [ ] **Correr v4** (GPU, requiere autorización): ~50 min de entrenamiento y
  ~20 min de prueba barata en A100.
- [ ] Si pasa: fases C y D completas (35 B2 para el abogado, rutas, veredicto).
- [ ] Si no pasa: la hipótesis de Martín (menos contrastivos) como variable
  del siguiente candidato. **No entró en v4 a propósito**: con dos cambios a la
  vez, un resultado no se puede atribuir a ninguno.

#### 7.1.3 La prueba de los 4 escenarios

**Por qué:** los 35 B2 de validación no pueden detectar el atajo (sección 6.1).
Esta prueba sí, con un diseño **pareado**: la misma pregunta con un contexto que
la responde y con uno de la misma materia que no.

| escenario | n | de dónde sale | qué se espera |
|---|---|---|---|
| `suficiente` | 55 | los B1 de validación, con su contexto | citar el artículo que responde |
| `parcial` | 13 | los B3 de validación, con su contexto | responder la parte y decir qué falta |
| `irrelevante` | 49 | las mismas preguntas, del buscador de producción sin el artículo que responde ni sus contiguos | abstenerse |
| `vacio` | 68 | las mismas preguntas, sin fragmentos | la frase de escape **por código**, sin llamar al modelo |

El irrelevante trae un fragmento de su propia categoría en **44 de 49** casos.
Se descartaron 19 por traer un artículo contiguo al que responde. Está congelado
en `data/escenarios_m1.jsonl` (huella `d51365fbc779d1ce`) para que v1 y el
candidato reciban exactamente lo mismo. 117 generaciones en GPU (~40 min).

    python -m tools.evaluation.escenarios --verificar        # CPU, sin faiss
    python -m tools.evaluation.escenarios --correr --adaptador <dir> --salida <dir>   # Colab

### 7.2 M1 — `colab/m1_reevaluacion_v1.ipynb`

**Qué hace:** regenera las respuestas del adaptador **v1 existente**, sin
entrenar, dándole a cada registro **su propio** prompt. Lee los 103 registros con
contexto de `results/m1_2026-10-09/finetuned_results.jsonl`, donde están los
mensajes exactos que vio v1: así **cambia una sola variable**, el prompt.
Antes corre un **control de reproducción**: 10 registros sin contexto que deben
salir idénticos a los de 2026-10-09. Con 10 de 10 es **REPRODUCCIÓN**; con
cualquier diferencia, **DIAGNÓSTICO**. La regla se fijó antes de correr.

**Coste:** unos 35–40 min en A100. Solo inferencia.

**Preparación — 6 de 6 (100 %)**: es la misma lista que *listo para correr*;
este notebook es solo una corrida.

**Listo para correr — 6 de 6 (100 %)**

- [x] Plan probado en CPU con `--dry-run`
- [x] Fuente histórica: solo cambia el prompt
- [x] Revisión del modelo base recuperada y fijada
- [x] Huella del adaptador verificada (acepta v1, rechaza v2)
- [x] Control de reproducción con regla fijada
- [x] Instala las versiones fijadas de `colab/requirements-m1.txt`

**Completado — 3 de 3 (100 %)**

- [x] Ejecutada: corrida `20261012-e54205d5`, control DIAGNÓSTICO (3 de 10)
- [x] Las 35 respuestas B2 adjudicadas y validadas por el abogado (confirmado por Tomás, 2026-10-13)
- [x] Leída con la tabla del protocolo: **14/35, entre 2 y 29** → el prompt
  explicaba una parte del fallo (de 1/35 a 14/35); v3 se justificaba

**Cómo se lee el resultado (fijado antes de correr):**

| `B2_funcional` de v1 con el prompt correcto | lectura |
|---|---|
| ≥ 30/35 y 0 críticos | el fallo era la evaluación; entrenar un candidato no se justifica por B2 |
| entre 2/35 y 29/35 | el prompt explica una parte; el candidato se justifica y esta cifra es su referencia |
| ≤ 1/35 | el prompt no explica el fallo; el diagnóstico del atajo se sostiene |

### 7.3 M2 — `colab/m2_evaluacion.ipynb`

**Qué hace, por fases.** (1) Genera las respuestas del modelo base y del
afinado sobre los 231 de validación **sin contexto** y sobre el eval set.
(2) Métricas sin juez: clásicas, citas numeradas, guardia de rutas y entidades.
(3) Guarda en Drive. (4) Juez **Groq** (`openai/gpt-oss-120b`, de otra familia
que Qwen): eval set contra su criterio, rúbrica 1–5 de las 231 y comparación
cara a cara en los dos órdenes. (4b) El juez sobre los ejemplos con contexto.
(5) Scorecard y archivos para `results/`. Se puede retomar otro día sin GPU.

**Corrida vigente:** `results/m2_2026-10-09/`, con v1.

| | baseline | afinado |
|---|---|---|
| juez compuesto 1–5 | 3,47 | **4,121** (IC +0,527 a +0,773) |
| eval set gold: cumple / parcial / no cumple | 4 / 20 / 21 | 6 / 27 / 12 |
| eval set adversarial: cumple / parcial / no cumple | 10 / 6 / 14 | 9 / 15 / 6 |
| **cara a cara** (231 pares) | **106** | 73 (10 empates, 42 inconsistentes, 19 % de cambio según el orden) |

**El desacuerdo está sin resolver:** el compuesto favorece al afinado y el cara a
cara al baseline. Hasta resolverlo **no se puede afirmar** que el afinado sea
globalmente mejor.

**M2 no tiene el fallo del prompt de M1:** carga solo los registros sin contexto
(`load_records()` con `origen="v1"`), y para ellos un único prompt es el correcto.

**Preparación — 8 de 8 (100 %)**

- [x] Eval set: 45 gold + 30 adversariales
- [x] Criterio verificable por caso ("Debe…" / "No debe…")
- [x] Juez externo con controles de sesgo (otra familia, los dos órdenes)
- [x] Métricas sin juez y guardia de rutas y entidades
- [x] Reanudación por días sin GPU
- [x] Revisión del modelo base fijada (H6, en el cargador compartido)
- [x] Verificación de la huella del dataset y del adaptador evaluados, antes de generar
- [x] Apunta a un candidato sin mezclar: `ADAPTADOR_DIR` + su huella, y el
  manifiesto firma ese adaptador y la revisión

**Listo para correr — 5 de 5 (100 %)**

- [x] Corre contra el repo actual (sus `assert` de 1536 y 231 se cumplen)
- [x] Juez con reanudación por días y checkpoints por texto
- [x] Revisión del modelo base fijada (H6)
- [x] Verifica la huella del dataset y del adaptador que evalúa
- [x] Apunta al adaptador que se declare (`ADAPTADOR_DIR`, por defecto v1); M2
  no corre hasta que haya un candidato aceptado

**Completado — 3 de 5 (60 %)**

- [x] Eval set: 45 gold + 30 adversariales con criterio verificable
- [x] Corrida con v1: baseline sin cortar, juez contra criterio, cara a cara
- [x] Resultados en `results/m2_2026-10-09/`
- [ ] Desacuerdo entre jueces explicado
- [ ] Corrida con el adaptador candidato

**M2 completado cuando** se corra con el adaptador que M1 acepte, con la
revisión fijada, y el desacuerdo entre jueces tenga una explicación medida.

### 7.4 M3 — `colab/m3_busqueda_v2.ipynb`

**Qué hace:** (1) reconstruye el índice FAISS desde el corpus; (2) mide si la
búsqueda trae el artículo gold en su top-k, con y sin enrutador, y barre el piso
de la válvula de escape; (3) regenera los contextos del dataset con el buscador
real.

**Resultados:** el índice vigente (`19657d22583f93d0`, 11 975 fragmentos) y el
barrido que fijó `RETRIEVAL_MIN_SCORE = 0.81` y `USE_ENRUTADOR = True`.

**Preparación — 6 de 7 (85 %)**

- [x] Corpus en alcance: 36 normas para las 27 categorías
- [x] Índice reconstruido y verificado
- [x] Medición de acierto@k contra el gold
- [x] Barrido del piso y del enrutador
- [x] Fase 3 **retirada** (H7): sobrescribía `data/dataset.jsonl` con otro
  constructor; el dataset se construye en local con `tools.dataset_v3 --indice`
- [x] Configuración de la sesión: la muestra, ya no la pisa (H7)
- [~] Correcciones de corpus: derogatorias **implementadas y apagadas** (H12);
  falta el artículo 57 del CST (H11, exige reconstruir el índice)

**Listo para correr — 4 de 4 (100 %)**

- [x] Fase 1: reconstruye el índice
- [x] Fase 2: mide acierto@k contra el gold
- [x] Fase 3 retirada: se detiene sin escribir nada (H7)
- [x] La celda de decisión muestra la configuración del repo en vez de pisarla (H7)

**Completado — 2 de 4 (50 %)**

- [x] Índice verificado
- [x] Configuración de búsqueda justificada (piso 0,81, enrutador)
- [ ] Correcciones de corpus agrupadas (artículo 57 del CST, derogatorias)
- [ ] Ranking suficiente (hoy el artículo gold está en el top-5 en 20 de 45)

### 7.5 M3 — `colab/m3_s08_rag_avanzado.ipynb`

**Qué hace:** compara tres recuperaciones sobre el eval set con el mismo prompt y
el mismo generador. **A** denso puro; **B** denso + BM25 con fusión RRF; **C** B
+ reordenamiento con cross-encoder. Copia el índice de `Drive/Amparo/rag/` a
`artifacts/`.

**Corrida vigente:** `results/m3_s08_2026-10-09/`, con v1. **Producción quedó en
denso + enrutador** (`USE_HYBRID = False`, `USE_RERANK = False`).

**Preparación — 6 de 6 (100 %)**

- [x] Hybrid (BM25 + RRF) implementado y probado
- [x] Reordenamiento con cross-encoder implementado
- [x] A/B/C sobre un solo camino de código
- [x] Manifiesto de corrida
- [x] Revisión fijada (H6)
- [x] Verificación de la huella del índice antes de correr

**Listo para correr — 4 de 4 (100 %)**

- [x] Usa los artefactos verificados
- [x] Las tres configuraciones sobre un solo camino de código
- [x] Revisión fijada (H6)
- [x] Verifica la huella del índice **antes** de correr

**Completado — 2 de 4 (50 %)**

- [x] A/B/C medido
- [x] Configuración de producción fijada
- [ ] Ranking suficiente
- [ ] Corrida con el adaptador final

### 7.6 M3 — `colab/m3_s10_rag_agentico.ipynb` — **el RAG que se entrega**

**Qué hace:** corre el RAG de una pasada (`pipeline.answer_query`) sobre los 75
casos del eval set; lo evalúa con **RAGAS** (juez Groq); compara las búsquedas de
S08 con RAGAS; mide la guardia de rutas; registra en W&B. Las rutas agénticas
(*tool use*, ReAct) se retiraron el 2026-10-08: el modelo nunca decidió buscar
por sí mismo y costaban 2,2 veces la latencia sin ganar nada.

**Corrida vigente:** `results/m3_s10_2026-10-09/`, con v1, índice
`19657d22`, corpus `1c552822`, eval set `a5151999`. **Generó con el prompt
correcto** (con la orden de abstenerse): el fallo de M1 no le afecta.

**Cómo responde hoy, de verdad:**

| | resultado |
|---|---|
| gold que **cumplen** su criterio (juez Groq) | **1 de 45** (17 parcial, 27 no cumple) |
| adversariales que cumplen | 8 de 30 (11 parcial, 11 no cumple) |
| artículo gold en el contexto entregado (top-5) | **20 de 45** |
| … en el top-30 | 37 de 45 |
| abstención pura en gold (debería responder) | 8 de 45 |
| abstención pura en adversariales | 20 de 30 |
| respuestas cortadas | 0 |
| latencia media | 7,9 s |
| RAGAS: context precision / recall / answer relevancy | 0,56 / 0,39 / 0,34 |
| RAGAS: faithfulness | 0,51 **sobre solo 18 de 45** (H5) |

**Lectura honesta.** El modelo no puede citar un artículo que no le llega: en 25
de 45 casos el artículo que responde **no está en el contexto**. Pero sí está en
el top-30 en 37: **el problema es el orden**, no la cobertura. Esa es la palanca
más grande para que S10 responda bien, y es de recuperación, no de
entrenamiento.

**Preparación — 9 de 11 (80 %)**

- [x] RAG de una pasada (`answer_query`)
- [x] Verificación de citas, incluidas las normas citadas que no se recuperaron
- [x] Prompt idéntico al de entrenamiento
- [x] RAGAS, guardia de rutas y W&B
- [x] Auditoría de recuperación caso por caso (6.1)
- [x] Diagnóstico del cuello de botella: el orden de la recuperación
- [x] Revisión fijada (H6)
- [x] RAGAS con abstención estricta (H5)
- [x] Filtro de derogatorias (H12): implementado y **apagado**; medido, libera
  6 puestos del top-5 y el acierto@5 sigue en 21/45
- [ ] Corrección del enrutamiento (H13)
- [ ] Mejora del ranking implementada

**Listo para correr — 5 de 6 (85 %)**

- [x] Artefactos verificados
- [x] El prompt del pipeline es el de entrenamiento
- [x] RAGAS, guardia de rutas y W&B
- [x] Revisión fijada (H6) e índice verificado antes de medir
- [x] RAGAS excluye solo la abstención pura (H5)
- [ ] Adaptador final

**Completado — 1 de 7 (15 %)**

- [x] Corrida completa (2026-10-09)
- [ ] Gold que cumplen su criterio (hoy 1/45)
- [ ] Recuperación: artículo gold en el top-5 (hoy 20/45)
- [ ] Sobreabstención en gold ≤ 3/45 (hoy 8)
- [ ] Rutas incorrectas ≤ 4 (v1 tiene 6)
- [ ] Correcciones de corpus (artículo 57, derogatorias)
- [ ] Corrida con el adaptador final

---

## 8. M4 y lo que queda fuera de alcance

**M4 no está iniciado.** Su alcance lo define Tomás cuando M1–M3 estén
cerrados. **No se planifica ni se escribe código para M4 antes.**

**Urgencias: fuera de alcance**, por decisión de producto de Tomás del
2026-10-10. Los 5 casos históricos (9129–9133) y su línea base 0/5 se conservan
como registro, sin criterio asociado. La consecuencia aceptada es que, ante *"mi
vecina está siendo golpeada en este momento"*, el sistema no encaminará a la
Línea 123. El instrumento queda en el repo sin conectar, por si la decisión
cambia. **No es evidencia de que el sistema sea seguro ante urgencias.**

---

## 9. Hallazgos abiertos

| # | hallazgo | sev. | estado | dónde |
|---|---|---|---|---|
| **H1** | La evaluación de M1 generaba las 334 respuestas con el prompt de `records[0]` (sin contexto): los 35 B2 se evaluaron **sin la orden de abstenerse**. Invalida 0/35, 1/35 y 15/35 | crítica | **resuelto**: v1 reevaluado con el prompt correcto el 2026-10-12 (fase B): 14/35 | `m1_finetune` celda 13 |
| **H2** | El dev que elige la época compartía el 63 % de sus preguntas con el entrenamiento | alta | **corregido** (`split_dev`) | celda 22 |
| **H3** | Al construir v3 se reconstruyó también el contexto de **los 35 B2 de validación**. Validación con los mismos ids y otro contenido | alta | **corregido** en la fase A: 0 registros distintos de la base | `tools/dataset_v3.py` |
| **H4** | Al construir v3 en local, los **263 B2 escritos a mano pasaron de e5 + FAISS a BM25**: todos los B2 con BM25 y todos los B1/B3 con e5, posible atajo por el estilo del contexto | alta | **corregido** en la fase A: todo contexto con e5 + FAISS, y escribir exige `--indice` | `tools/dataset_v3.py` |
| **H5** | RAGAS de S10 excluyó 27 respuestas por **contener** la frase de escape, no por ser abstención: *faithfulness* sobre 18 de 45 | media | **corregido**: faithfulness excluye solo la abstención pura; las filas viejas del checkpoint se rehacen donde la regla cambia | `ragas_metrics`, S10 |
| **H6** | `generation.load_base_model` (M2 y M3) no fija la revisión del modelo base | media | **corregido**: `config.BASE_MODEL_REVISION` en el cargador compartido, C6 y el notebook de M1 | `tools/evaluation/generation.py` |
| **H7** | `m3_busqueda_v2` llama a un módulo que ya no existe y sobrescribe la config en sesión con valores viejos | media | **corregido**: fase 3 retirada (escribía `data/dataset.jsonl`) y la celda de config solo muestra | `m3_busqueda_v2` celdas 10 y 13 |
| **H8** | `dataset_contrastivo.py` sigue generando los contrastivos viejos (a un archivo de revisión, no al dataset) | baja | **corregido**: escribir exige `--legado`; queda como biblioteca | `tools/dataset_contrastivo.py` |
| **H9** | El stack se instalaba con `pip install -U`, sin versiones fijadas; las de v1 no se registraron | media | **corregido en todos**: `colab/requirements-m{1,2,3}.txt` con las versiones registradas por las corridas | celda de instalación |
| **H10** | Regresión de rutas incorrectas: base 4 → v1 6 → v2 8. *Ojo: medida sobre los 334, que incluyen los 103 generados con el prompt equivocado* | media | medido, sin corregir | `results/m1_rutas_2026-10-10/` |
| **H11** | Artículo 57 del CST indexado anterior a la reforma de 2025 (casos 9051, 4630). **Única corrección que exige reconstruir el índice** | media | abierto | corpus |
| **H12** | 64 fragmentos puramente derogatorios ocupan 6 puestos del top-5 en 3 casos gold. Se arregla con un filtro **posterior** a la recuperación, sin reconstruir | media | **implementado y apagado** (`config.FILTRAR_DEROGATORIAS`): 109 fragmentos; medido, libera 6 puestos y el acierto@5 queda en 21/45 | `tools/rag/retrieve.py` |
| **H13** | 4 categorías gold no son enrutables y el enrutador entierra 3 casos que el denso solo encontraba | media | medido | `tools/rag/enrutador.py` |
| **H14** | Desacuerdo entre jueces en M2 (compuesto frente a cara a cara) | media | abierto | `results/m2_2026-10-09/` |
| **H15** | No hay negativos adjudicados con recuperación real: ninguna señal de suficiencia se puede usar como puerta | media | abierto | `tools/prototipo/` |
| **H16** | Los punteros de los objetivos contrastivos salían también de los B2 de validación: 39 de 289 objetivos de entrenamiento usaban texto que solo existía en validación | media | **corregido** en la fase A: solo punteros de entrenamiento | `tools/dataset_v3.py` |
| **H17** | Los 35 B2 de validación conservan su contexto histórico, de otras categorías: **no pueden detectar el atajo** (+32 pts de ventaja sobre ellos) | alta | **mitigado**: lo detecta la prueba de los 4 escenarios, que hay que correr con el candidato (C5) | `data/escenarios_m1.jsonl` |
| **H18** | El repo **público** de Hugging Face servía v3, un candidato rechazado. Ya no era v1 desde el 2026-10-10, cuando lo pisó v2: la celda del notebook publicaba en cada corrida completa | alta | **resuelto**: celda protegida (`PUBLICAR_EN_HF = False`) y `main` restaurado a v1 el 2026-10-13 (commit `52a79fb3ab`, huella `8ce3cc2bc9306974` comprobada desde fuera). v2 y v3 siguen en el historial del repo | `colab/m1_finetune.ipynb`, celda 39 |
| **H19** | Las planillas de primera pasada de las 35 B2 de v3 y de los 49 irrelevantes **no están en el repo**: D1 de v3, los irrelevantes adjudicados y D6 no se pueden verificar | media | abierto, **no bloquea**: v3 se rechaza por D3 y v4 genera sus propias respuestas. No están en el Drive (buscado el 2026-10-13): viven en el repo local de Martín, `docs/m1_b2_adjudicacion_v3.csv` y `docs/m1_escenarios_irrelevante_adjudicacion.csv` | `docs/` |
| **H20** | Control de reproducción de v1 reevaluado: 3 de 10. Las 7 distintas empiezan igual y divergen a mitad del texto: deriva numérica del stack, no otro modelo | baja | explicado: v1 reevaluado no reproduce exactamente la corrida del 9 de octubre, pero se compara con v3 en el mismo stack | `results/m1_reevaluacion_v1_2026-10-12/` |
| **H21** | La línea base de D3 en el protocolo (1/45) no correspondía a la medición con el RAG real: 8/45 (S10) y 10/45 (v1 hoy). **v1 tampoco cumple D3** | media | corregida la línea base, **sin tocar el umbral** | `docs/m1_protocolo_aceptacion.md` |
| **H22** | **El dataset enseña a encaminar a donde no corresponde.** Los 289 contrastivos llevan un puntero escrito para **otra** pregunta de su categoría (0 de 289 propios; 113 nombran una autoridad concreta): a *"me cortaron el agua sin avisarme"* se le enseña *"pide la cancelación por escrito al operador... queja ante la Superintendencia de Industria y Comercio"*. Y de los 146 B2 escritos a mano que nombran una autoridad concreta, en 138 esa autoridad no está en el contexto. **6 de los 9 fallos críticos de v1 reevaluado están en ese puntero**, no en el contenido jurídico | alta | **corregido en el dataset v4** (contrastivos). Lo de los B2 escritos a mano sigue abierto: H25 | `data/dataset.jsonl`, `tools/dataset_v3.py` (`objetivo`) |
| **H23** | **D3 mezcla la búsqueda con el modelo.** El artículo gold llega al contexto en 21 de 45 consultas. Con el artículo delante, v1 se abstiene en 4/21 y v3 en 13/21 (v3 sobreabstiene de verdad); sin él, 6/24 y 17/24. Mientras la búsqueda traiga 21/45, ≤ 3/45 exige responder también cuando falta el artículo | media | documentado; **el umbral no se toca**. Leer D3 en dos partes en el próximo veredicto | `docs/m1_protocolo_aceptacion.md`, fila 8 |
| **H24** | El caso gold 9033 no tiene ningún artículo que lo responda, y su criterio pide la autorización del Ministerio del Trabajo, que en el corpus solo está en el artículo que se marcó `no_responde` (Ley 361 art. 26) | media | **resuelto** (criterio de Claude, por delegación del abogado): Ley 361 art. 26 pasa a `responde_parcial`; el caso ya tiene artículo y el techo vuelve a 45/45 | `docs/m3_gold_revision_2026-10-13.md` |
| **H25** | De los 146 B2 escritos a mano que nombran una autoridad concreta, en 138 esa autoridad no está en el contexto: el modelo aprende a decir "no tengo información" y a la vez a nombrar de memoria la autoridad competente. Es la fuente probable de los 3 fallos de autoridad equivocada de v1 | media | **decidido y corregido** (criterio de Claude, delegado por Tomás): de los 36 que nombran una Superintendencia o Secretaría, 32 son correctos para su pregunta y se conservan; 4 reproducían el patrón de los fallos de v1 y se corrigen en el constructor (`CORRECCIONES_B2`): 4718 y 4719 dicen el alcance de la SIC (internet, no agua, luz ni gas), 3319 deja la SIC fuera de un contrato entre empresas y 2725 separa aseguradora de alquiler | `data/dataset.jsonl`, B2 de origen v2 |

---

## 10. Ruta crítica para dejar M1–M3 cerrados

En este orden. **Los pasos con GPU necesitan la autorización de Tomás.**

```
DATOS (CPU)                                         -- HECHO, fase A (2026-10-11)
 1. [x] H3  validacion congelada
 2. [x] H4  todo contexto con el buscador de produccion (e5 + FAISS)
 3. [x]     verificado: 19 puertas, 0 fugas, idempotente, xfail retirado
 4. [x] H9  stack de M1 fijado
 4b.[x]     prueba de los 4 escenarios implementada y congelada

LINEA BASE (GPU, solo inferencia)                   -- HECHO, Martin (2026-10-12)
 5. [x]     v1 reevaluado: B2_funcional 14/35, 9 criticos
 6. [x]     adjudicado y validado por el abogado
 7. [x]     leido: el prompt explicaba una parte; se justifica un candidato

M1 (GPU, entrenamiento)                             -- HECHO, v3 RECHAZADO
 8. [x]     v3 entrenado
 9. [~]     evaluado; faltan en el repo dos planillas de adjudicacion
10. [x]     juzgado: no cumple (docs/m1_veredicto_v3.md)
10b.[x]     dataset v4 (H22) y notebook listo con la prueba barata dentro
10c.[ ]     correr v4 (GPU, autorizacion); si pasa la prueba barata, fases C y D

M3 (CPU y GPU)
11. [x] H12 filtro de derogatorias: implementado, APAGADO, medido (21/45 igual)
12. [ ] H13 enrutamiento; medir por separado (sin diseno de correccion todavia)
13. [ ] H11 articulo 57 del CST: reconstruir el indice UNA vez, con su linea base
14. [ ]     ranking: es la palanca mas grande de S10 (top-5 21/45, top-30 37/45)
15. [x] H5, H6  RAGAS con abstencion estricta y revision fijada
16. [ ]     S08 y S10 con el adaptador final

M2 (GPU + Groq)
17. [x] H6  revision fijada; adaptador y dataset verificados por huella
18. [ ]     M2 con el adaptador final; resolver H14
```

**Por qué en este orden.** Los pasos 1–4 tocaban el dataset y convenía hacerlos
de una vez, antes de cualquier corrida: ya están hechos. El roadmap detallado de
M1, paso por paso y con su comprobación, está en la sección 7.1.2. El 5
es barato y decide si el 8 hace falta. M3 depende de M1 solo en el paso 16;
todo lo de recuperación (11–14) se puede avanzar en paralelo.

---

## 11. Qué resultados valen

| carpeta | adaptador | qué vale | qué NO vale |
|---|---|---|---|
| `m1_2026-10-09/` | v1 | las 231 sin contexto; citas sin contexto 0 % | abstención (0/35), B2_funcional (1/35), fallos críticos (15/35), B1/B3 de los 103 — H1 |
| `m1_v2_2026-10-09/` | v2 | ídem | ídem |
| `m1_rutas_2026-10-10/` | base, v1, v2 | la tendencia | la cifra exacta de los 103 con contexto — H1 |
| `m2_2026-10-09/` | v1 | todo, con el desacuerdo H14 a la vista | — |
| `m3_s08_2026-10-09/` | v1 | A/B/C | — |
| `m3_s10_2026-10-09/` | v1 | veredictos por criterio, recuperación, latencia | *faithfulness* (H5) |
| `m3_61_2026-10-10/` | — | acierto@k por caso (auditoría 6.1) | — |
| `busqueda_v2/` | — | el barrido del piso y el enrutador | — |

---

## 12. Glosario

| término | qué es |
|---|---|
| **B1 / B2 / B3** | los tres modos con contexto (sección 2) |
| **A / B / C** *(abstención)* | abstención literal, piso verificable, comunicación. **No confundir** con A/B/C de S08 |
| **A / B / C** *(S08)* | denso, denso + BM25, + rerank |
| **`B2_funcional`** | reconoce la insuficiencia **y** no excede el contexto. Exige adjudicación |
| **fallo crítico** | uno de 6 tipos; basta uno. Ver `tools/evaluation/b2_funcional.py` |
| **atajo** | predecir el modo sin leer el contexto. Estaba en el dataset viejo: +41,3 pts |
| **contrastivo** | la misma pregunta de un B1/B3, con un contexto que no responde |
| **gold / adversarial** | caso con respuesta / caso donde lo correcto es no responder de fondo |
| **acierto@k** | si el artículo gold está entre los k primeros recuperados |
| **válvula de escape** | la frase de abstención; el pipeline la emite sin llamar al modelo si no recupera nada |
| **enrutador** | clasificador TF-IDF de categoría que prioriza las normas de esa categoría |
| **`corrida_id`** | identidad de una corrida: fecha + hash de su configuración |
| **huella** | hash corto (16 caracteres); hay cuatro algoritmos (sección 5.3) |
| **REPRODUCCIÓN / DIAGNÓSTICO** | veredicto del control de la reevaluación de v1 |

---

## 13. Para arrancar: comprobaciones en CPU

```bash
git pull origin m3.5
pip install -r requirements.txt
pytest -q                                   # 798 passed, 4 skipped
#   Sin artifacts/ (los adaptadores no estan en git) algunas pruebas se SALTAN
#   en vez de pasar: mas "skipped", ninguna "failed". Un "failed" si es un aviso.

python -c "from tools.evaluation import config; print(config.verificar_dataset())"
#   -> 5cec3fdf891260fd

python -m tools.evaluation.escenarios --verificar
#   -> OK, huella d51365fbc779d1ce (no necesita faiss)

python -m tools.evaluation.reevaluacion_v1 --adaptador artifacts/amparo-lora-adapter --dry-run
#   -> 103 registros, 10 de control, huella 8ce3cc2bc9306974
#      (requiere el adaptador v1 en artifacts/; esta en Drive)

# Reconstruir el dataset exige el buscador de produccion: el indice en
# artifacts/ (esta en Drive) y el .venv del repo, que tiene faiss.
.venv/Scripts/python -m tools.dataset_v3 --check --indice   # verifica, no escribe
```

Si algo de esto no da lo esperado, **para y avisa antes de seguir**: es la forma
más barata de descubrir que algo cambió.
