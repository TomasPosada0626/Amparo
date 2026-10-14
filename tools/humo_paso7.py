"""Prueba de humo del notebook de la corrida final del paso 7, en CPU.

Ejecuta las celdas de `colab/m3_paso7_corrida_final.ipynb` en un solo espacio de
nombres, como un kernel de Colab, sustituyendo solo lo que exige GPU o red: Qwen
(un generador falso que registra el prompt que recibe), Drive (una carpeta
temporal), nvidia-smi y el cross-encoder (un puntuador falso, para no cargar
2 GB en CPU). Corren de verdad: e5 + FAISS, el enrutador, la verificacion por
huella del indice y del adaptador, el armado del prompt y el guardado.

Comprueba ademas lo que importa de esta corrida:
  - que los sistemas R usan el reranker elegido y A no;
  - que los sistemas *_servicio llevan el bloque de servicio y los demas no;
  - que al volver a correr la generacion no se repite nada (retoma).

    .venv/Scripts/python.exe -m tools.humo_paso7
"""
import json, pathlib, re, shutil, subprocess, sys, tempfile, traceback, types

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
TMP = pathlib.Path(tempfile.mkdtemp(prefix="humo_paso7_"))
DRIVE = TMP / "drive"
(DRIVE / "rag").mkdir(parents=True)

from tools.rag import config as rc
for n in ("rag_index.faiss", "rag_index_metadata.jsonl"):
    shutil.copy(RAIZ / "artifacts" / n, DRIVE / "rag" / n)
rc.DRIVE_ROOT = str(DRIVE)
rc.ARTIFACTS_DIR = TMP / "artifacts"
rc.FAISS_INDEX_PATH = rc.ARTIFACTS_DIR / "rag_index.faiss"
rc.FAISS_METADATA_PATH = rc.ARTIFACTS_DIR / "rag_index_metadata.jsonl"
rc.LORA_ADAPTER_PATH = str(RAIZ / "artifacts" / "amparo-lora-adapter")

colab = types.ModuleType("google.colab")
colab.drive = types.SimpleNamespace(mount=lambda *a, **k: print("[humo] drive.mount simulado"))
import google
google.colab = colab; sys.modules["google.colab"] = colab

_run = subprocess.run
def run(cmd, *a, **k):
    if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == "nvidia-smi":
        return subprocess.CompletedProcess(cmd, 0, stdout="GPU simulada, 0 MiB\n", stderr="")
    return _run(cmd, *a, **k)
subprocess.run = run

# --- Qwen falso: registra el system prompt de cada llamada -------------------
from tools.evaluation import generation
from tools.rag.prompt_template import INSTRUCCIONES_DE_SERVICIO
LLAMADAS = []
generation.load_base_model = lambda *a, **k: ("modelo-falso", "tokenizer-falso")
generation.attach_adapter = lambda model, ruta: model
def run_chat_generation(model, tokenizer, system_prompt, user_content, max_new_tokens, return_n_tokens=False, **k):
    LLAMADAS.append({"servicio": INSTRUCCIONES_DE_SERVICIO in system_prompt})
    m = re.search(r"Art[ií]culo\s+(\d+)", user_content)
    texto = f"Segun el articulo {m.group(1)} del contexto, puedes reclamar." if m else "Puedes reclamar."
    return (texto, 20) if return_n_tokens else texto
generation.run_chat_generation = run_chat_generation

# --- cross-encoder falso: registra que modelo se pidio -------------------------
from tools.rag import rerank
RERANKERS = []
class _CE:
    def __init__(self, mid): self.mid = mid
    def predict(self, pares): RERANKERS.append(self.mid); return [float(-i) for i in range(len(pares))]
rerank.load_reranker = lambda model_id=rc.RERANK_MODEL_ID: _CE(model_id)

# --- conjuntos reducidos ------------------------------------------------------
from tools.evaluation import eval_set as es, preguntas_confirmacion as pc
_load, _cargar = es.load_eval_set, pc.cargar
es.load_eval_set = lambda *a, **k: es.gold_examples(_load(*a, **k))[:2] + es.adversarial_examples(_load(*a, **k))[:1]
pc.cargar = lambda *a, **k: _cargar(*a, **k)[:2]


def celdas(nb):
    nbj = json.loads((RAIZ / "colab" / nb).read_bytes().decode("utf-8"))
    for i, c in enumerate(nbj["cells"]):
        if c["cell_type"] == "code":
            src = "".join(c["source"])
            yield i, "\n".join(l for l in src.splitlines() if not l.lstrip().startswith(("!", "%")))


def correr(saltar=(1,)):
    espacio = {"__name__": "__main__"}
    for i, codigo in celdas("m3_paso7_corrida_final.ipynb"):
        if i in saltar or not codigo.strip():
            continue
        try:
            exec(compile(codigo, f"paso7:celda{i}", "exec"), espacio)
            print(f"[humo] celda {i}: OK")
        except BaseException:
            print(f"[humo] celda {i}: ERROR"); traceback.print_exc(); return None
    return espacio


ok = True
esp = correr()
ok = esp is not None
if ok:
    destino = DRIVE / "rag" / "corridas_paso7"
    recs = {p.stem.replace("eval_records_", ""): [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines()]
            for p in destino.glob("eval_records_*.jsonl")}
    print("[humo] archivos:", {k: len(v) for k, v in recs.items()})
    esperado = {"A_confirmacion", "A_servicio_eval_set", "A_servicio_confirmacion",
                "R_eval_set", "R_confirmacion", "R_servicio_eval_set", "R_servicio_confirmacion"}
    ok &= set(recs) == esperado
    for k, v in recs.items():
        sistema = v[0]["sistema_paso7"]
        es_r = sistema.startswith("R")
        ok &= all(r["used_rerank"] == es_r for r in v)
        ok &= all((r["reranker"] == "BAAI/bge-reranker-v2-m3") == es_r for r in v)
        ok &= all(r["prompt_servicio"] == sistema.endswith("servicio") for r in v)
    ok &= set(RERANKERS) == {"BAAI/bge-reranker-v2-m3"}
    ok &= any(l["servicio"] for l in LLAMADAS) and not all(l["servicio"] for l in LLAMADAS)
    print("[humo] rerankers pedidos:", set(RERANKERS), "| llamadas con bloque de servicio:",
          sum(l["servicio"] for l in LLAMADAS), "de", len(LLAMADAS))
    # retoma: una segunda pasada no genera nada
    antes = len(LLAMADAS)
    esp2 = correr()
    ok &= esp2 is not None and len(LLAMADAS) == antes
    print("[humo] llamadas al generador en la segunda pasada:", len(LLAMADAS) - antes, "(debe ser 0)")
print("\n[humo] RESULTADO:", "TODO OK" if ok else "FALLO")
sys.exit(0 if ok else 1)
