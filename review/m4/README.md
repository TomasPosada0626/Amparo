# Revisión M4 — Integración visual y evaluación

**Repositorio:** `TomasPosada0626/Amparo` · **Commit revisado:** [`d158742`](https://github.com/TomasPosada0626/Amparo/tree/d158742db641560ab4b0d5f29b7d5e75b4e15f08) (`main`, incluye la rama `m4` en [`f01bb0e`](https://github.com/TomasPosada0626/Amparo/commit/f01bb0efa971580e12afc2b99a3ea89651438909)) y la página de la Wiki «M4 ‐ Componente visual — decisiones».

Esta revisión es técnica. La calificación se comunica por canal privado. Las sugerencias no son requisitos retroactivos ni cambian los criterios que ustedes pre-registraron.

---

## 1. Cómo se verificó

| Qué | Cómo | Resultado |
|---|---|---|
| Pruebas del harness | `pytest m4/tests` en entorno aislado | 166 pruebas aprobadas |
| Scorecard y deltas | Recálculo de `scorecard_m4.csv`, `delta_m4.json` y `delta_imagen_m4.json` desde `trazas_m4.json` | 0 discrepancias |
| Componente visual | `ver()` del notebook con su prompt y post-proceso, Qwen2-VL-2B en fp16 sobre Apple MPS (sin 4-bit, que MPS no soporta) | 9 de 11 lecturas idénticas a sus trazas; cambia doc03 (m04/m05), como ustedes ya documentan entre GPUs |
| Cadena completa | M3 real (`openai/gpt-oss-120b` en Groq), caché vacía, en m10, m04, m01 y m06 | Ver §3 (H2 y H4) |

Las diferencias de hardware (Apple MPS frente a la T4 de Colab, ambas en fp16) no se consideran defectos de la entrega. Las latencias medidas aquí sirven como orden de magnitud y no reemplazan las suyas.

## 2. Fortalezas

1. **Harness con contrato y totalmente recalculable.** `validar_casos` se ejecuta antes de gastar GPU, los errores de autoría no se convierten en un 0 silencioso y cada fallo se diagnostica por etapa.
2. **Delta del componente bien planteado.** Comparan la misma pregunta con y sin imagen sobre el mismo M3 (`delta_con_sin_imagen`), declaran que la comparación contra M3 (0.675, n=120) no es directa e incluyen el caso en que la imagen no aporta. También corrigieron la latencia de M3, de por llamada a por caso.
3. **Adversarial verdadero por construcción.** En doc06 el número no existe debajo de la mancha ([`m4/eval_set/generar_imagenes.py` L348–360](https://github.com/TomasPosada0626/Amparo/blob/d158742db641560ab4b0d5f29b7d5e75b4e15f08/m4/eval_set/generar_imagenes.py#L348-L360)), así que la válvula se evalúa contra una verdad conocida.
4. **Peor caso expuesto con honestidad.** Reconocen que m10 pasa la válvula pero inventa un plazo, que m04 invierte la negación y que `entidad` queda null en 6/6.
5. **Datos sintéticos, anonimizados y etiquetados**, con checklist y etiqueta visible en las seis imágenes.
6. **Justificación del patrón *input*** frente a *tool* y *output*, atada a la arquitectura y los costos de M3.

## 3. Observaciones

### H1 · El delta con/sin imagen no mide latencia
- **Dónde:** [`m4/harness/scorecard.py` L425–467](https://github.com/TomasPosada0626/Amparo/blob/d158742db641560ab4b0d5f29b7d5e75b4e15f08/m4/harness/scorecard.py#L425-L467) (`delta_con_sin_imagen`); [`m4/README.md` L77–78](https://github.com/TomasPosada0626/Amparo/blob/d158742db641560ab4b0d5f29b7d5e75b4e15f08/m4/README.md#L77-L78) y [L100–103](https://github.com/TomasPosada0626/Amparo/blob/d158742db641560ab4b0d5f29b7d5e75b4e15f08/m4/README.md#L100-L103).
- **Qué se observa:**
  - La tabla que mide el componente (con y sin imagen) no tiene columna de latencia.
  - La única comparación de latencia es 10.9 s (M4, n=11) frente a 13.65 s (M3, n=120), que son corridas y conjuntos distintos.
  - El README dice que «el primero tarda 30.8 s», pero en `scorecard_m4.csv` ese valor (30.797 s) corresponde a **m02**; m01 tardó 7.573 s.
  - La caché persistente del agente puede abaratar re-ejecuciones en la misma VM sin que quede marcado.
- **Por qué importa:** S13 pide el delta «con latencia». Hoy se sabe cuánto acierta el componente, pero no cuánto cuesta.
- **Sugerencia:** cronometrar también la condición sin imagen, leer los segundos con imagen del scorecard y reportar mediana y media sin el arranque. Vaciar la caché antes de cronometrar o marcar los aciertos de caché. Corregir la atribución de los 30.8 s.
- **Criterio de cierre:** `delta_imagen_m4.json` trae segundos con y sin imagen por caso, y el README reporta la latencia del componente con una nota sobre la caché.

### H2 · El texto libre del VLM entra al relato como hecho
- **Dónde:** [`armar_relato`, `scorecard.py` L51–54](https://github.com/TomasPosada0626/Amparo/blob/d158742db641560ab4b0d5f29b7d5e75b4e15f08/m4/harness/scorecard.py#L51-L54) (réplica de `sistema_multimodal` del notebook); [`nota_valvula`, `criterios.py` L245–255](https://github.com/TomasPosada0626/Amparo/blob/d158742db641560ab4b0d5f29b7d5e75b4e15f08/m4/harness/criterios.py#L245-L255).
- **Qué se observa:**
  - En m10, `plazo_dias` es null, pero `pretension_visible` dice «…un plazo de dos semanas hábiles…».
  - En m04 la lectura dice «cumplirá» donde el documento dice «NO realizará».
  - Las dos lecturas entran a M3 bajo «DATOS DEL DOCUMENTO ADJUNTO», sin marca de que provienen de un modelo.
  - Con M3 real, en estos casos el error **no** llegó a la respuesta: m10 responde «no determinable» sin mencionar plazo.
- **Por qué importa:** en la Demo, una lectura inventada o invertida puede mostrarse en pantalla como si fuera un hecho del documento, junto a citas normativas reales.
- **Sugerencia:** rotular el bloque como «leído de la imagen por un modelo; no verificado» y añadir una guarda posterior a `ver()` que avise cuando el texto libre menciona un plazo y `plazo_dias` es null. Esa guarda marca solo m10 tanto en sus trazas como en las lecturas reproducidas. La inversión de m04 necesitaría otra estrategia, por ejemplo mostrar la imagen junto a la lectura.
- **Criterio de cierre:** la salida de la Demo muestra la advertencia en m10, y m04 aparece como limitación declarada.

### H3 · La corrida oficial es poco trazable
- **Dónde:** `m4/pipeline/M4_pipeline.ipynb`. La celda 4 hace `git clone` de `main`, que es una referencia móvil, y el notebook no tiene salidas guardadas.
- **Qué se observa:** los artefactos no registran commit, GPU, versión del modelo, reranker ni hora. El README declara la diferencia de lecturas entre GPUs, pero no queda registrado cuál GPU produjo el scorecard oficial.
- **Sugerencia:** clonar un SHA o tag fijo (`m4`), escribir `m4/corrida_m4.json` con commit, GPU, versiones, reranker y timestamp, y guardar las salidas de las celdas clave.
- **Criterio de cierre:** el manifiesto existe y el notebook apunta a un SHA o tag.

### H4 · El efecto de la imagen en m06 varía entre corridas
- **Dónde:** `m4/delta_imagen_m4.json` (m06: con imagen 1, sin imagen 0); [`m4/README.md` L90–98](https://github.com/TomasPosada0626/Amparo/blob/d158742db641560ab4b0d5f29b7d5e75b4e15f08/m4/README.md#L90-L98).
- **Qué se observa:** al re-ejecutar M3 con caché vacía, m06 sin imagen también acierta («acción popular, Ley 472 de 1998»). En esa corrida los tres casos `exacto` aciertan con y sin imagen.
- **Por qué importa:** ustedes ya advierten que M3 no es determinista en m01. Con un solo caso favorable que cambia entre corridas, la conclusión «la imagen aporta» necesita repeticiones. Esto no invalida su medición, que está bien construida.
- **Sugerencia:** repetir el delta k≥3 veces por caso con caché vacía y reportar la tasa con y sin imagen y su rango, por ejemplo «en m06 la imagen aportó en 2 de 3 corridas».
- **Criterio de cierre:** `delta_imagen_m4.json` incluye repeticiones y el README reporta tasas.

**Puntos ya reconocidos por ustedes, que no se repiten aquí:** `juez_vlm` es juzgado por el mismo VLM; `ver()` y `sistema_multimodal` viven en celdas; hay un solo adversarial y solo 3 casos `exacto`; `entidad` es null en 6/6.

## 4. Prioridades para Demo Day

La Demo presenta el sistema completo como producto. [`PLAN_DEMO.md`](PLAN_DEMO.md) muestra dónde está hoy el recorrido M1–M4 y propone tres prioridades sobre el camino que ya existe:

1. **[P1] Experiencia de punta a punta en una sola llamada:** `sistema_multimodal()` como módulo importable y una salida con tres bloques (las cinco líneas, el «Por qué» con la regla y el artículo, y lo leído del documento), más una frase sobre el lugar de M1 en el producto.
2. **[P1] La confianza como característica:** m10 como caso de seguridad, con la lectura rotulada «no verificado», una advertencia y la abstención de M3 (H2).
3. **[P1] Tres cifras de valor con denominador, sobre una versión fija y ensayada:** el delta repetido (H4), la latencia sin arranque (H1), un tag/SHA con manifiesto (H3) y un plan B rotulado.

Incluye un guion sugerido y sugerencias para cuando desplieguen en M5.

## 5. Cómo reproducir lo verificado

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt pytest
python -m pytest m4/tests -q
```

Para el recálculo se cargaron `scorecard_m4.csv` y `trazas_m4.json` con `cargar_guardado()` y se compararon con `tabla_desde_disco()` y los criterios de `m4/harness/criterios.py`, sin GPU ni API.

La reproducción del componente visual requiere el notebook `m4/pipeline/M4_pipeline.ipynb` con GPU. La de M3 requiere la clave de Groq del equipo.
