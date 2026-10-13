"""Prueba de humo de S08 y S10 en CPU, antes de gastar unidades de Colab.

Ejecuta las celdas de codigo de `colab/m3_s08_rag_avanzado.ipynb` y
`colab/m3_s10_rag_agentico.ipynb` en un solo espacio de nombres, como un kernel
de Colab, con 5 casos del eval set. Sustituye SOLO lo que exige GPU o red: Qwen
(un generador que cita el articulo del contexto y, 1 de cada 4 veces, uno
inexistente para ejercitar la correccion de citas), el juez de Groq (RAGAS y
criterio, con el formato real), Drive (una carpeta temporal) y nvidia-smi.
Corren de verdad: e5 + FAISS, el enrutador, BM25, el cross-encoder, la
verificacion de citas, RAGAS con los embeddings de e5, la decision de busqueda,
las rutas, wandb sin conexion y los manifiestos.

Despues repite S10 en una sesion NUEVA sin generar (el camino recomendado para
hacer RAGAS en un entorno sin GPU) y comprueba que no llama al generador.

    .venv/Scripts/python.exe -m tools.humo_m3              # unos 5 minutos
    HUMO_FORZAR_C=1 .venv/Scripts/python.exe -m tools.humo_m3   # el camino "gana C"

Necesita el `.venv` del repo (faiss, sentence-transformers, wandb), el indice en
`artifacts/` y el adaptador v1 en `artifacts/amparo-lora-adapter`. No escribe
nada en el repo. Termina con "RESULTADO: TODO OK" o con la celda que fallo.
"""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile, types, traceback

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
TMP = pathlib.Path(tempfile.mkdtemp(prefix="humo_m3_"))
DRIVE = TMP / "drive"
(DRIVE / "rag").mkdir(parents=True)
os.environ["WANDB_MODE"] = "offline"
os.environ["WANDB_DIR"] = str(TMP)
os.environ["WANDB_SILENT"] = "true"

# --- Drive: el indice en la carpeta temporal, y config apuntando ahi ----------
from tools.rag import config as rc
for n in ("rag_index.faiss", "rag_index_metadata.jsonl"):
    shutil.copy(RAIZ / "artifacts" / n, DRIVE / "rag" / n)
rc.DRIVE_ROOT = str(DRIVE)
rc.ARTIFACTS_DIR = TMP / "artifacts"
rc.FAISS_INDEX_PATH = rc.ARTIFACTS_DIR / "rag_index.faiss"
rc.FAISS_METADATA_PATH = rc.ARTIFACTS_DIR / "rag_index_metadata.jsonl"
rc.LORA_ADAPTER_PATH = str(RAIZ / "artifacts" / "amparo-lora-adapter")   # v1 real

# --- google.colab falso --------------------------------------------------------
colab = types.ModuleType("google.colab")
colab.drive = types.SimpleNamespace(mount=lambda *a, **k: print("[humo] drive.mount simulado"))
colab.userdata = types.SimpleNamespace(get=lambda k: "clave-falsa" if k == "GROQ_API_KEY" else None)
import google                      # el paquete real (protobuf lo necesita wandb)
google.colab = colab; sys.modules["google.colab"] = colab

# --- nvidia-smi ------------------------------------------------------------------
_run = subprocess.run
def run(cmd, *a, **k):
    if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == "nvidia-smi":
        return subprocess.CompletedProcess(cmd, 0, stdout="GPU simulada, 0 MiB\n", stderr="")
    return _run(cmd, *a, **k)
subprocess.run = run

# --- Qwen falso: cita el primer articulo del contexto; 1 de cada 4 cita uno inexistente
from tools.evaluation import generation
LLAMADAS = {"n": 0, "corregidas": 0}
generation.load_base_model = lambda *a, **k: ("modelo-falso", "tokenizer-falso")
generation.attach_adapter = lambda model, ruta: model
def run_chat_generation(model, tokenizer, system_prompt, user_content, max_new_tokens, return_n_tokens=False, **k):
    LLAMADAS["n"] += 1
    m = re.search(r"Art[ií]culo\s+(\d+)", user_content)
    if "Verificacion de citas" in user_content:
        LLAMADAS["corregidas"] += 1
    if m and (LLAMADAS["n"] % 4 or "Verificacion de citas" in user_content):
        texto = (f"Segun el articulo {m.group(1)} del contexto, tienes derecho a reclamar. "
                 "Reune las pruebas y presenta un derecho de peticion.")
    else:
        texto = "Segun el articulo 9999 de la Ley 1 de 1900, tienes derecho a reclamar."
    return (texto, 40) if return_n_tokens else texto
generation.run_chat_generation = run_chat_generation

# --- eval set reducido: 3 gold y 2 adversariales -------------------------------
from tools.evaluation import eval_set as es
_load = es.load_eval_set
def load_eval_set(*a, **k):
    regs = _load(*a, **k)
    return es.gold_examples(regs)[:3] + es.adversarial_examples(regs)[:2]
es.load_eval_set = load_eval_set

# --- juez Groq falso, con el formato real ---------------------------------------
from tools.evaluation import ragas_metrics as rm
def juez_falso(system, user, max_tokens):
    if "CONTEXTOS RECUPERADOS" in user:
        n = len(re.findall(r"^\[\d+\]", user, re.M))
        return json.dumps({"afirmaciones": [{"texto": "a", "respaldada": True}],
                           "contextos_utiles": [i == 0 for i in range(n)],
                           "referencia": [{"oracion": "o", "en_contexto": True}]}), 120
    return json.dumps({"preguntas": ["¿que puedo hacer?"] * 3}), 60
rm.juez_groq = lambda: juez_falso
if os.environ.get("HUMO_FORZAR_C"):
    from tools.evaluation import decision_busqueda as _db
    _db.decidir = lambda r: {"elegida": _db.C, "motivo": "forzado en la prueba", "medias": {}, "diferencias": {}}
from tools.evaluation import criterio as _criterio
_veredictos = iter(["cumple", "parcial", "no_cumple"] * 1000)
_criterio.generador_groq = lambda: (lambda system, user, max_tokens: json.dumps(
    {"veredicto": next(_veredictos), "errores_juridicos": [], "justificacion": "prueba"}))

# --- ejecutar los notebooks --------------------------------------------------------
def celdas(nb):
    nbj = json.loads((RAIZ / "colab" / nb).read_bytes().decode("utf-8"))
    for i, c in enumerate(nbj["cells"]):
        if c["cell_type"] != "code":
            continue
        src = "".join(c["source"])
        lineas = [l for l in src.splitlines() if not l.lstrip().startswith(("!", "%"))]
        yield i, "\n".join(lineas)

ESPACIO = {"__name__": "__main__"}
ok = True
for nb, saltar in (("m3_s08_rag_avanzado.ipynb", {1}), ("m3_s10_rag_agentico.ipynb", {1})):
    print(f"\n======== {nb}")
    for i, codigo in celdas(nb):
        if i in saltar or not codigo.strip():
            continue
        try:
            exec(compile(codigo, f"{nb}:celda{i}", "exec"), ESPACIO)
            print(f"[humo] celda {i}: OK")
        except SystemExit as e:
            print(f"[humo] celda {i}: SystemExit -> {e}"); ok = False; break
        except Exception:
            print(f"[humo] celda {i}: ERROR"); traceback.print_exc(); ok = False; break

# --- fase 2: sesion NUEVA sin GPU, solo RAGAS (como se recomienda para ahorrar unidades)
if ok:
    print("\n======== m3_s10 en sesion nueva, sin generar (RAGAS en CPU)")
    antes = LLAMADAS["n"]
    ESPACIO = {"__name__": "__main__"}
    for i, codigo in celdas("m3_s10_rag_agentico.ipynb"):
        if i in {1, 8, 10, 11} or not codigo.strip():
            continue
        try:
            exec(compile(codigo, f"s10-cpu:celda{i}", "exec"), ESPACIO)
            print(f"[humo] celda {i}: OK")
        except SystemExit as e:
            print(f"[humo] celda {i}: SystemExit -> {e}"); ok = False; break
        except Exception:
            print(f"[humo] celda {i}: ERROR"); traceback.print_exc(); ok = False; break
    print("[humo] llamadas al generador en la fase 2:", LLAMADAS["n"] - antes, "(debe ser 0)")
    ok = ok and LLAMADAS["n"] == antes

print("\n[humo] llamadas al generador:", LLAMADAS)
print("[humo] archivos escritos en Drive simulado:")
for p in sorted((DRIVE / "rag").rglob("*")):
    if p.is_file() and p.suffix != ".faiss" and p.name != "rag_index_metadata.jsonl":
        print("   ", p.relative_to(DRIVE), p.stat().st_size)
print("\n[humo] RESULTADO:", "TODO OK" if ok else "FALLO")
sys.exit(0 if ok else 1)
