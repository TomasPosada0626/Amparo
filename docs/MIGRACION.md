# Migración de notebooks a un paquete Python (`amparo/`)

Rama `migracion-py`, fusionada en `main` el 2026-11-03 (ver «Fusión con `main`» al final). El objetivo es que toda la lógica de fine-tuning (M1), harness (M2), RAG (M3) y el componente visual (M4) viva en módulos `.py` estructurados, y que los notebooks queden como envoltorios delgados que solo los llaman. **Esta etapa no incluye despliegue** (ni API, ni Docker, ni interfaz).

## Decisiones

| # | Decisión | Por qué |
|---|---|---|
| 1 | El estado entregado de M1–M4 queda marcado con el tag `entrega-m4` (commit `d158742`). | El sello del código (`corridas.version_codigo()`, `data/subida_sellada.txt`, `data/verificar_entrega.py`) hashea los `src/*.py` por nombre y está atado a los resultados publicados. Sobre ese tag sigue valiendo: quien quiera verificar una entrega hace checkout del tag. |
| 2 | `src/` se mueve al paquete `amparo/` con `git mv`, en subpaquetes por responsabilidad. No hay copias. | Una sola fuente de verdad. `git mv` conserva el historial de cada archivo (`git log --follow`). |
| 3 | En esta rama la huella del código pasa a cubrir `amparo/**/*.py` con la ruta relativa como clave. | La huella sigue sirviendo para lo que existe: saber si dos corridas usaron el mismo código. Las corridas nuevas no son comparables byte a byte con las del tag, y es correcto que la huella lo diga. |
| 4 | Las rutas del proyecto salen de `amparo/config.py` (`RAIZ`, `DATA`, `RESULTS`, `RUNS`, `MODELS`), con `AMPARO_RAIZ` para sobrescribirlas. | Hoy seis módulos calculan la raíz con `Path(__file__).parent.parent`. Al bajar un nivel dentro del paquete, ese cálculo apuntaría a `amparo/` y no encontraría `data/`. |
| 5 | Las importaciones planas (`import schema`) pasan a absolutas (`from amparo.nucleo import schema`). Los scripts de `data/` ponen la raíz del repo en `sys.path`, no `src/`. | `src/` no era un paquete y cada consumidor hacía su propio truco de `sys.path`. Con `pip install -e .` el paquete se importa desde cualquier lugar. |
| 6 | La lógica que vivía solo en los notebooks se extrae a módulos, con sus constantes parametrizadas y sin variables globales. Las duplicaciones se resuelven en un solo lugar. | Ver la tabla "Lo que sale de los notebooks". |
| 7 | Cada notebook se convierte en un pipeline `amparo/pipelines/mN_*.py`: una función por etapa más un `correr()` que las encadena. El notebook queda como envoltorio delgado que instala el paquete y llama a esas etapas. | Se mantiene la reproducción en Colab del curso, y la lógica se puede leer, importar y probar fuera del notebook. |
| 8 | Las autopruebas pasan a `tests/` y se pueden correr con pytest. Los tests de `m4/tests/` pasan a `tests/m4/`. | Un solo lugar para las pruebas. La línea base tiene que repetirse tras la migración (ver más abajo). |
| 9 | `pyproject.toml` declara el paquete con dependencias base livianas y extras: `[rag]`, `[entrenamiento]`, `[evaluacion]`, `[vlm]`, `[ragas]` y `[dev]`. `requirements.txt` no cambia. | `requirements.txt` es el registro de las versiones con las que corrieron M1–M3. El stack pesado (torch, transformers, peft) solo se instala cuando se pide su extra, para no pisar el torch con CUDA que ya trae Colab. |

## Mapa de archivos

| Antes | Después |
|---|---|
| `src/schema.py`, `src/reglas.py`, `src/terminos.py` | `amparo/nucleo/` |
| `src/rag.py` | `amparo/rag/recuperacion.py` |
| `src/ragas_eval.py` | `amparo/rag/ragas_eval.py` |
| `src/sistema.py`, `src/agente.py` | `amparo/sistemas/` |
| `src/metricas.py`, `src/juez.py`, `src/harness.py`, `src/costos.py` | `amparo/evaluacion/` |
| `src/tokenizadores.py`, `src/redaccion.py` | `amparo/finetuning/` |
| `src/corridas.py`, `src/arranque.py` | `amparo/ejecucion/` |
| `m4/pipeline/enchufe_m3.py` | `amparo/multimodal/enchufe.py` |
| `m4/harness/criterios.py`, `m4/harness/scorecard.py` | `amparo/multimodal/` |
| `src/autoprueba_integracion.py`, `src/autoprueba_agente.py` | `tests/` |
| `m4/tests/*` | `tests/m4/` |
| `m4/pipeline/multimodal.py` (llegó con la fusión) | `amparo/multimodal/sistema_visual.py` |
| `m4/pipeline/corrida.py` (llegó con la fusión) | `amparo/multimodal/corrida_m4.py` |

## Lo que sale de los notebooks

| Notebook (celdas) | Módulo nuevo | Qué |
|---|---|---|
| M1 (16) | `amparo/finetuning/datos.py` | `SISTEMA`, `mensajes`, `construir` (tokenizar y enmascarar el prompt) y `collate`, con tokenizer y `max_len` como parámetros. |
| M1 (18, 20, 32) y M3 (27) | `amparo/finetuning/generacion.py` | Generación por lotes con Hugging Face. `generar` y `generar_few_shot` se unen en una función con un constructor de prompt. `ids_parada` se define una sola vez. `generador_hf` sigue la interfaz `generar(sistema, usuario) -> str` que usan los sistemas y unifica `generar_texto` (M1) y `generar_qwen` (M3). |
| M1 (22–25, 36) | `amparo/finetuning/entrenamiento.py` | Configuración de LoRA, `TrainingArguments` filtrados contra la firma real, Trainer con parada temprana, verificación de `lora_B`, selección del mejor checkpoint, guardado del adaptador con su sha256 y curva de pérdida. |
| M2 (25) | `amparo/evaluacion/acuerdo.py` | `puntuar_muestra` (antes `_puntua`) y la búsqueda del segundo juez. |
| M3 (28, 41) | `amparo/evaluacion/brazos.py` | `correr_brazo` (antes `correr`: ETA, tolerancia a fallos de la API, latencias), `CostoPorBrazo` y `BrazoNoMedido` (antes `_BrazoUno`). |
| M1–M4 (setup) | `amparo/ejecucion/entorno.py` | Montar Drive y encontrar la raíz, leer `GROQ_API_KEY`, verificar el sello y `pip install -e .`. Antes estaba copiado en cada notebook. |
| M2 y M3 (publicación) | `amparo/ejecucion/publicacion.py` | `publicar_todo`: comprueba que estén todos los artefactos y recién entonces publica en `results/`. |
| M2 y M3 | `amparo/evaluacion/predicciones.py` | Cargar `results/m1_predicciones.json`, desenvolver `datos`, conservar `_corrida` y comprobar el orden de ids. |
| M4 | `amparo/multimodal/sistema_visual.py` | Lo sacó del notebook el propio equipo en `main` (`m4/pipeline/multimodal.py`, revisión docente): `LectorVisual` (`ver`, `preguntar`), `parsear_json`, `VALVULA`, `INSTRUCCION_DOMINIO` y `Amparo` con la respuesta en tres bloques. La migración lo trajo al paquete sin cambiar su lógica. |

## Verificación

**Línea base sobre `main` antes de migrar** (2026-11-01, `.venv`, Python 3.13.7):

| Prueba | Resultado |
|---|---|
| `src/autoprueba_integracion.py` | las 75 pruebas pasan |
| `src/autoprueba_agente.py` | los 8 escenarios dan salida válida |
| `m4/tests` (pytest) | 166 passed |

Después de migrar tienen que dar lo mismo. Las etapas que necesitan GPU o claves (entrenar, generar con Qwen, llamar a Groq) no se pueden ejecutar en local: se prueban con dobles (modelos y clientes falsos) y quedan marcadas como **no ejecutadas de verdad** hasta correrlas en Colab.

**Después de migrar** (rama `migracion-py`, mismo entorno):

| Prueba | Resultado |
|---|---|
| `tests/autoprueba_integracion.py` | las 75 pruebas pasan. Las cuatro que auditaban el contenido de los notebooks ahora auditan los pipelines. |
| `tests/autoprueba_agente.py` | los 8 escenarios dan salida válida |
| `pytest tests` (incluye `tests/m4`) | 270 passed, 2 skipped. Los skips son por pillow y matplotlib, que no están en el `.venv`. |
| `data/auditar_notebooks.py`, `auditar_proyecto.py`, `autoprueba_reporte.py`, `ampliar_eval_set.py` | exit 0, igual que sobre el tag |
| `data/verificar_entrega.py` | exit 1 con salida **idéntica** a la del tag: falta `runs/` en la máquina local |

**Sin ejecutar de verdad:** cargar Qwen-7B y Qwen2-VL-2B, el entrenamiento LoRA, la generación real, las llamadas a Groq (juez, agente, redacción) y los notebooks en Colab.

## Desviaciones respecto a los notebooks

Cada una está comentada en su módulo.

- **M1:** `estabilidad` solo se publica si hay una corrida previa con la que compararse; el notebook la publicaba siempre y en la primera corrida lanzaba `FileNotFoundError`. La fertilidad de tokenizadores se queda en el pipeline y no se delega a `tokenizadores.medir()`, porque usan candidatos, corpus y esquema distintos. El `@torch.no_grad()` mal colocado desaparece, porque `generar_lote` ya genera sin gradientes.
- **M2:** el cliente de Groq y la fábrica del juez se inyectan, para poder probar sin red; los valores por defecto se comportan igual que antes.
- **M3:** se eliminó `generar_groq`, que se creaba y nadie usaba. `RECORTES_M3` se guarda como artefacto de la corrida (`recortes_m3`, sin publicar); antes se perdía. **Bug heredado, conservado a propósito:** `latencia_s_por_caso` sale siempre 0.0 en el `scorecards.json` de la corrida, porque la latencia se guarda con el nombre corto del brazo y se busca por su etiqueta. No afecta a lo publicado; arreglarlo cambia una cifra y queda a decisión del equipo.
- **M4:** no usa `entorno.preparar("m4")`, porque `arranque.ORDEN` no tiene `m4`. Solo carga la clave de Groq. Los notebooks de M4 no son envoltorios: ver «Fusión con `main`».
- **`celda_acuerdo_jueces.py`** se retiró: era una copia anterior de la celda 25 de M2, sin la comparación entre familias. Lo vigente es `amparo/evaluacion/acuerdo.py`.

## Pendiente antes de correr en Colab

1. **Sellar y subir:** correr `python -I data/preparar_subida.py --sellar` y subir a Drive. Hasta entonces, la verificación del sello detiene cada notebook. Es lo correcto, porque Drive no tiene el código nuevo.
2. **Publicar el tag:** el tag `entrega-m4` solo existe en local.
3. `reproducir.py` regenera `REPORTE.md`. Sin `runs/` en la máquina, el reporte pierde la huella de las corridas. Esto ya pasaba antes de la migración: no hay que commitear un `REPORTE.md` regenerado así.

## Fuera de alcance

- Despliegue (API, contenedor, interfaz).
- Reentrenar o volver a correr M1–M4 para obtener cifras nuevas.
- Regenerar el sello `data/subida_sellada.txt`, que se hace con `data/preparar_subida.py --sellar` cuando se vuelva a subir a Drive.

## Fusión con `main` (2026-11-03)

Mientras la migración estaba en su rama, `main` recibió 9 commits de M4: la revisión docente (PR #15 y #16) y la corrida de la demo. Al fusionar, la migración y esos cambios se cruzaron en M4.

| # | Decisión | Por qué |
|---|---|---|
| 10 | **Manda el código de M4 de `main`.** `m4/pipeline/multimodal.py` y `corrida.py` entran al paquete como `amparo/multimodal/sistema_visual.py` y `corrida_m4.py`. Solo cambian sus imports; la lógica, no. Los cambios de `main` en `criterios.py`, `scorecard.py`, `enchufe.py` y los tests los aplicó git siguiendo los renombres. | Es el código evaluado y el que vio el público en la demo. `tests/m4/test_multimodal.py` fija el prompt por SHA-256, así que un cambio en el prompt rompería una prueba. |
| 11 | **Se retira `amparo/multimodal/vlm.py`**, y `amparo/pipelines/m4_multimodal.py` se rehace sobre los módulos de `main`, siguiendo el notebook de evaluación vigente: manifiesto, `LectorVisual`, la respuesta en tres bloques, los dos deltas, el plan B y el cierre. | `vlm.py` era mi port del notebook de `d158742` y quedó superado: duplicaba en versión vieja lo que `main` ya había sacado del notebook. |
| 12 | **Los notebooks de M4 (`M4_pipeline.ipynb` y `M4_demo.ipynb`) siguen anclados al tag `demo-final`.** En el conflicto del notebook se quedó la versión de `main`. No son envoltorios del paquete. | Revisión docente, H3: reproducen exactamente lo que se evaluó y lo que vio el público, con la estructura de entonces (`m4/pipeline/`, `m4/harness/`, `src/`). El pipeline del paquete es la misma secuencia para correrla desde `main`. |
| 13 | **`m4/README.md`:** en los dos conflictos se quedó el texto de `main` (vigente tras la revisión), con las rutas del código actualizadas y una nota sobre dónde vive el código. | La migración solo había cambiado rutas en ese archivo. |
| 14 | **`tests/m4/test_multimodal.py`** (nuevo en `main`, en la carpeta que la migración movió) queda en `tests/m4/` e importa del paquete con los mismos alias. | No parchea módulos por nombre, así que los alias bastan. |

**Verificación después de fusionar:** se repite la batería (ver el mensaje del commit de fusión).
