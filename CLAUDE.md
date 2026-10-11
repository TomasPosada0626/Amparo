# Amparo — instrucciones para Claude

Asistente jurídico de derecho colombiano: Qwen2.5-7B + LoRA (M1), arnés de
evaluación (M2), RAG (M3). M4 no está iniciado.

**Antes de hacer nada, lee `ESTADO_Y_TRASPASO.md`.** Ahí está dónde estamos, qué
falta en cada notebook, los artefactos congelados y la ruta crítica. Si el código
contradice ese documento, gana el código, y se avisa.

## Reglas que no se negocian

**Verdad.**
- Verificar antes de afirmar. Cada cifra sale de un archivo o un comando que se
  puede citar. Si no se pudo verificar, se dice.
- Reportar fielmente: lo que falla se dice con la salida. No se fabrican métricas
  favorables. Los errores propios se corrigen de forma explícita.
- Antes de reportar una discrepancia, comprobar que se mide igual: en este repo
  hay cuatro algoritmos de "huella" (`ESTADO_Y_TRASPASO.md`, 5.3).

**Qué no se toca sin decisión explícita de Tomás.**
- `data/dataset.jsonl`, el split, el corpus, el índice, los adaptadores y los
  resultados históricos. Las salidas guardadas en los notebooks tampoco.
- Un solo dataset con un solo nombre. No se crean `dataset_v3.jsonl` ni
  parecidos: la versión la lleva git.
- El adaptador `v1` es producción.
- **Sin GPU, entrenamiento, inferencia ni créditos** (Colab, Groq, W&B) sin
  autorización expresa. Preparar y probar en CPU, sí.

**Método.**
- Criterios antes que resultados: todo umbral se escribe en
  `docs/m1_protocolo_aceptacion.md` antes de ver la cifra que juzga.
- Progreso y aceptación de producto, siempre por separado.
- Una sola variable por experimento.
- El conjunto que diseñó una señal no la valida.
- Los veredictos jurídicos los da el abogado (Leonardo Galeano). No se inventan.
- Las decisiones de producto son de Tomás (por ejemplo, urgencias fuera de alcance).

**Código.**
- La lógica vive en `tools/` y se prueba en CPU; los notebooks la importan.
- `pytest -q` en verde antes de comitear.
- Notebooks: editar por JSON y escribir con
  `json.dumps(nb, indent=2, ensure_ascii=False) + "\n"`, que reproduce los
  `.ipynb` del repo byte a byte. Nunca reformatear; nunca tocar las salidas.
- En Windows, tras escribir código con barras invertidas, escanear bytes de
  control: un heredoc puede convertir `\b` en un retroceso. Finales de línea LF.
- Toda corrida de Colab con identidad (`tools/evaluation/corrida.py`): revisión
  del modelo base fijada, huellas de dataset y adaptador, directorio propio.

**Git.**
- Commits en español: qué cambió, por qué y con qué cifras.
- Sin la línea `Co-Authored-By`.
- `git add` con rutas explícitas, nunca `-A` ni `.`.
- Comitear y subir solo cuando Tomás lo pide. Nada de cambios masivos sin revisar.

## Comprobaciones rápidas (CPU)

```bash
pytest -q
python -c "from tools.evaluation import config; print(config.verificar_dataset())"   # 37e579ad0bfac6bd
```
