"""M3 · RAG con tool use: los cuatro brazos sobre el mismo harness de M2.

Antes: `notebooks/M3_rag.ipynb`. Ahora el notebook solo llama a estas
funciones, una por seccion, en orden; `correr()` las encadena todas.

    | | sistema                               | que aporta                          |
    | 1 | fine-tuned solo                     | baseline de M1, ya medido           |
    | 2 | fine-tuned + RAG ingenuo            | punto de partida del delta          |
    | 3 | fine-tuned + RAG avanzado           | la estrategia que gane la regla     |
    | 4 | agente con tool use + motor reglas  | el techo: enrutamiento determinista |

La seccion de recuperacion corre en CPU. Solo los brazos 2 y 3 necesitan GPU,
porque cargan el modelo ajustado. Sin GPU se miden recuperacion, herramientas
y el brazo 4, y se dice en vez de fallar.

Cada etapa recibe y modifica un `Contexto`. Los nombres de artefactos y sus
destinos en `results/` son los mismos que publicaba el notebook.
"""
from __future__ import annotations

import collections
import os
import subprocess
import sys
from dataclasses import dataclass, field

from amparo.config import RAIZ
from amparo.ejecucion import arranque
from amparo.ejecucion.publicacion import publicar_todo
from amparo.evaluacion import brazos as br
from amparo.evaluacion import costos, harness, metricas, predicciones
from amparo.nucleo import reglas, schema, terminos
from amparo.rag import ragas_eval
from amparo.rag import recuperacion as rag

# El nombre VIAJA A LOS ARTEFACTOS, asi que no se escribe dos veces: el
# artefacto `ganadores` decia "los N casos de eval_set_v2.json" mientras el
# notebook ya cargaba otro archivo. Una constante no puede discrepar.
ARCHIVO_EVAL = "eval_set_v3.json"
# El pin de `ragas`. Lo que importa de verdad es `langchain-community==0.3.27`
# (la celda de instalacion del notebook lo explica): `ragas/llms/base.py`
# importa `langchain_community.chat_models.vertexai`, que la 0.4.x elimino.
RAGAS_PIN = "0.2.15"
K = 5                       # top-k de la comparacion de recuperacion y brazos 2-3
K_AGENTE = 4
MUESTRA = 8                 # casos del contraste con la libreria `ragas`
MODELO_BASE = "Qwen/Qwen2.5-7B-Instruct"
ADAPTADOR = "models/m1-adaptador"
MAX_NEW = 220

BRAZO_1 = "1 · fine-tuned solo (M1)"
BRAZO_2 = "2 · fine-tuned + RAG ingenuo"
BRAZO_3 = "3 · fine-tuned + RAG avanzado"
BRAZO_4 = "4 · agente + reglas"


@dataclass
class Contexto:
    c: object                                   # la corrida (`corridas.Corrida`)
    hay_gpu: bool = False
    docs: list = field(default_factory=list)
    eval_set: list = field(default_factory=list)
    eval_m3: list = field(default_factory=list)
    configs: dict = field(default_factory=dict)
    dec_chunk: dict | None = None
    chunks: list = field(default_factory=list)
    indice: object = None
    tr: object = None
    resultados: list = field(default_factory=list)
    decision: dict | None = None
    generar_qwen: object = None
    recortes: list = field(default_factory=list)
    ruta_ck: object = None
    brazos: dict = field(default_factory=dict)
    latencias: dict = field(default_factory=dict)
    fallos_por_brazo: dict = field(default_factory=dict)
    corrida_m1: str | None = None
    s_ing: object = None
    s_adv: object = None
    ag: object = None
    estrategia_ganadora: str | None = None
    nombre_tr: str = "sin brazo 3 (no hay GPU)"
    juez: object = None
    por_id: dict = field(default_factory=dict)
    contextos: dict = field(default_factory=dict)
    rs: list = field(default_factory=list)
    ctx_ag: list = field(default_factory=list)
    filas_cruce: list = field(default_factory=list)
    sin_respaldo: list = field(default_factory=list)
    scorecards: list = field(default_factory=list)
    comunes: list = field(default_factory=list)
    scorecards_comunes: list = field(default_factory=list)
    mejor_glob: dict | None = None
    mejor_gold: dict | None = None
    mejor_adv: dict | None = None
    filas_costos: list = field(default_factory=list)

    @property
    def casos_todos(self) -> list:
        return self.eval_set + self.eval_m3


def _cliente_groq():
    from groq import Groq
    return Groq(api_key=os.environ["GROQ_API_KEY"])


# --------------------------------------------------------------------------
# 0 · Proyecto, clave y corrida
# --------------------------------------------------------------------------
def comprobar_ragas() -> None:
    """Que `ragas` quedo instalado Y EN LA VERSION PINEADA se comprueba al
    arrancar, no en la seccion 7: un aviso aqui cuesta un reinicio; alli cuesta
    la corrida (40 minutos de brazos)."""
    try:
        import ragas as _ragas
        v = _ragas.__version__
        print(f"ragas {v}" + ("" if v.startswith("0.2.") else
                              f"  <- NO es {RAGAS_PIN}: el contraste de la seccion 7 fallara"))
    except Exception as ex:                                  # noqa: BLE001
        print(f"ragas NO quedo instalado ({type(ex).__name__}: {str(ex)[:90]}).")
        print("   Entorno -> Reiniciar sesion y corre la celda de instalacion otra vez.")
        print("   Si insiste, la seccion 7 publica las metricas propias y declara")
        print("   que el contraste con la libreria no se pudo correr.")


def preparar(hay_gpu: bool | None = None) -> Contexto:
    """Corrida, sello, clave de Groq (se pide por teclado si falta) y arranque.
    Son 45 minutos: vale la pena gastar dos segundos en saber que el entorno
    esta listo."""
    from amparo.ejecucion import entorno
    if hay_gpu is None:
        import torch
        hay_gpu = torch.cuda.is_available()
    print("GPU:", "si" if hay_gpu else "no hay — se omiten los brazos 2 y 3")
    comprobar_ragas()
    c = entorno.preparar("m3", pedir_clave=True)
    return Contexto(c=c, hay_gpu=hay_gpu)


# --------------------------------------------------------------------------
# 1 · Corpus: procedencia y responsabilidad
# --------------------------------------------------------------------------
def corpus(ctx: Contexto) -> None:
    ctx.docs = docs = rag.cargar_corpus()
    print(f"{len(docs)} fragmentos · {sum(len(d['texto']) for d in docs)} caracteres")
    print(f"verificados contra fuente oficial : {sum(d['verificado'] for d in docs)}/{len(docs)}")
    print(f"transcripciones literales         : "
          f"{sum(d['transcripcion'] == 'literal' for d in docs)}/{len(docs)}")
    print()
    for norma, n in collections.Counter(d["norma"] for d in docs).most_common():
        print(f"  {n:>3}  {norma}")
    print()
    print("--- fragmentos con nota de vigencia que NO es 'vigente' ---")
    for d in docs:
        if d["vigencia"] != "vigente":
            print(f"  {d['id']:<12}{d['vigencia']}")


def auditar_corpus(ctx: Contexto) -> None:
    """Auditoria del corpus + chequeo de cobertura, ejecutados aqui para que el
    resultado quede en la salida de la corrida y no solo en la consola de alguien."""
    print(subprocess.run([sys.executable, "data/auditar_corpus.py"],
                         capture_output=True, text=True, cwd=str(RAIZ)).stdout)


# --------------------------------------------------------------------------
# 2 · Chunking: por articulo o por tamano fijo
# --------------------------------------------------------------------------
def chunking(ctx: Contexto) -> None:
    """La regla de decision (`rag.REGLA_CHUNKING`) esta fijada ANTES de correr."""
    print(rag.REGLA_CHUNKING)
    ctx.eval_set = schema.cargar(archivo=ARCHIVO_EVAL)
    ctx.eval_m3 = schema.cargar(archivo="eval_set_m3.json")
    print(f"eval compartido: {len(ctx.eval_set)} casos · eval solo-M3: {len(ctx.eval_m3)} casos")
    ctx.configs = {
        "articulo (nuestro)": rag.trocear,
        "fijo 400/60": rag.trocear_fijo,
        "fijo 900/120": lambda d: rag.trocear_fijo(d, 900, 120),
    }
    ctx.dec_chunk = rag.comparar_chunking(ctx.docs, ctx.eval_set, ctx.configs,
                                          estrategia="hibrido", k=K)
    ctx.c.guardar_json("chunking", ctx.dec_chunk)
    ctx.chunks = ctx.configs[ctx.dec_chunk["elegido"]](ctx.docs)
    ctx.indice = rag.Indice(ctx.chunks).construir()
    print(f"indice: {len(ctx.chunks)} chunks con el chunking '{ctx.dec_chunk['elegido']}'")


# --------------------------------------------------------------------------
# 3 · Seis configuraciones de retrieval, con el delta medido
# --------------------------------------------------------------------------
def recuperacion(ctx: Contexto) -> None:
    """Lo unico que cambia entre filas es el retrieval: mismo corpus, mismo
    chunking, mismo k, mismas consultas. La regla (`rag.REGLA_DECISION`) trae
    una guarda: una tecnica que recupere menos que el ingenuo queda descalificada."""
    print(rag.REGLA_DECISION)
    c, ind, ev = ctx.c, ctx.indice, ctx.eval_set
    tr = ctx.tr = rag.TransformadorConsulta(cache=c.ruta_cache("consultas.json"))
    res = [
        rag.evaluar_recuperacion(ind, ev, "ingenuo", k=K),
        rag.evaluar_recuperacion(ind, ev, "hibrido", k=K),
        rag.evaluar_recuperacion(ind, ev, "reranked", k=K),
        rag.evaluar_recuperacion(ind, ev, "reranked", k=K,
                                 transformador=br.CostoPorBrazo(tr, tr)),
        rag.evaluar_recuperacion(ind, ev, "hibrido", k=K,
                                 transformador=br.CostoPorBrazo(lambda r: tr.multiples(r, 3), tr)),
        rag.evaluar_recuperacion(ind, ev, "hibrido", k=K,
                                 transformador=br.CostoPorBrazo(tr.hyde, tr)),
    ]
    # Nombre propio para los brazos con transformacion: sin el, "reranked +
    # reescritura" chocaba en la tabla con el "reranked" sin transformacion.
    res[3]["estrategia"] = "reranked + reescritura"
    res[4]["estrategia"] = "hibrido + multiconsulta"
    res[5]["estrategia"] = "hibrido + hyde"
    tr.guardar()
    ctx.resultados = res

    print("costo de transformacion por brazo (no acumulado):")
    for r in res[3:]:
        kk = r["costo_transformacion"]
        print(f"  {r['estrategia']:<26} {kk['llamadas_reales']:>3} reales + "
              f"{kk['desde_cache']:>3} cache de {kk['transformaciones']} · "
              f"{kk['latencia_ms_media']} ms media / {kk['latencia_ms_p95']} ms p95")
    print("acumulado del transformador compartido:", tr.costo())
    print()

    ctx.decision = rag.comparar_estrategias(res, k=K)
    c.guardar_json("retrieval", [{k2: v for k2, v in r.items() if k2 != "detalle"} for r in res])
    c.guardar_json("decision_retrieval", ctx.decision)


def consultas_fallidas(ctx: Contexto) -> None:
    """Los casos donde el retrieval no trajo ni un articulo esperado (tarea de
    S07, insumo de S08). Se cuentan los que la elegida ARREGLO y tambien los que
    ROMPIO: una tecnica puede subir el recall global y aun asi perder casos que
    el ingenuo si recuperaba. Se guarda en la corrida, no se publica."""
    peor = ctx.resultados[0]
    elegida = ctx.decision["elegida"]
    mejor = next(r for r in ctx.resultados if r["estrategia"] == elegida)
    for etiqueta, r in (("INGENUO", peor), (f"ELEGIDA ({elegida})", mejor)):
        fallos = [d for d in r["detalle"] if d["recall"] == 0]
        print(f"{etiqueta}: {len(fallos)}/{r['n']} casos sin recuperar ningun articulo esperado")
        for d in fallos[:6]:
            e = next(x for x in ctx.eval_set if x["id"] == d["id"])
            print(f"   {d['id']:<5} {e['categoria']:<30} esperaba {d['esperadas']}")
            print(f"         obtuvo  {d['obtenidas'][:3]}")
        print()
    vacios = lambda r: {d["id"] for d in r["detalle"] if d["recall"] == 0}  # noqa: E731
    arreglados, rotos = vacios(peor) - vacios(mejor), vacios(mejor) - vacios(peor)
    print(f"casos que la elegida ARREGLO respecto del ingenuo: {sorted(arreglados)}")
    print(f"casos que la elegida ROMPIO respecto del ingenuo : {sorted(rotos)}")
    ctx.c.guardar_json("consultas_fallidas", {
        "estrategia_elegida": elegida,
        "ingenuo": [d for d in peor["detalle"] if d["recall"] == 0],
        "elegida": [d for d in mejor["detalle"] if d["recall"] == 0],
        "arreglados_por_la_elegida": sorted(arreglados),
        "rotos_por_la_elegida": sorted(rotos)})


# --------------------------------------------------------------------------
# 4 · Tool use · 5 · el motor de reglas  (demostraciones, sin artefactos)
# --------------------------------------------------------------------------
def demo_terminos(ctx: Contexto | None = None) -> None:
    """La herramienta externa `calcular_termino`. Un LLM no sabe que el 6 de
    enero se corre al lunes por la Ley 51 de 1983 ni que el Corpus Christi
    depende de la Pascua; y si no puede calcular, devuelve `calculable: False`
    con el motivo en vez de adivinar."""
    for a in (2024, 2025, 2026, 2027):
        f = terminos.festivos(a)
        colision = [(d.isoformat(), n) for d, n in f.items() if "/" in n]
        print(f"  {a}: {len(f)} festivos" + (f"   colision -> {colision}" if colision else ""))
    print()
    print("2025 tiene 17 y no 18 porque San Pedro (29/6, domingo -> 30/6) coincide con")
    print("el Sagrado Corazon (Pascua + 71 = 30/6). La version anterior perdia uno en")
    print("silencio al sobrescribir la clave del diccionario, y un festivo que")
    print("desaparece corre TODOS los plazos del anio.")
    print("\nLa herramienta sobre casos reales, incluidos los que debe rechazar:\n")
    for tipo, txt in [
        ("peticion_general", "Radique una carta en la alcaldia hace dos meses"),
        ("peticion_documentos", "Pedi copia de mi historia clinica el 3 de marzo de 2026"),
        ("impugnacion", "me notificaron el fallo el 12/10/2026"),
        ("peticion_general", "Eso fue en marzo, estamos en junio"),
        ("fallo_tutela", "no hay ninguna fecha aqui"),
        ("inventado", "da igual"),
    ]:
        r = terminos.calcular_termino(tipo, relato=txt)
        if r["calculable"]:
            print(f"  OK      {tipo:<20} {r['fecha_inicio']} -> {r['fecha_vencimiento']}"
                  f"  vencido={r['vencido']}")
        else:
            print(f"  RECHAZA {tipo:<20} {r['motivo'][:62]}")


def fallas_agente(ctx: Contexto | None = None) -> None:
    """Las cinco fallas del agente, provocadas a proposito con un cliente
    guionado: deterministas y sin gastar un token. Documentar "esto nos paso en
    una corrida" deja la cobertura al azar."""
    print(subprocess.run([sys.executable, "tests/autoprueba_agente.py"],
                         capture_output=True, text=True, cwd=str(RAIZ)).stdout)


# Hechos a mano de casos del gold, para ver el motor contra la etiqueta.
CASOS_MOTOR = {
    "E01": dict(afectacion_individual=True),
    "E31": dict(privacion_libertad=True),
    "A10": dict(privacion_libertad=True),
    "E09": dict(derecho_colectivo=True),
    "E28": dict(derecho_colectivo=True),
    "E29": dict(incumplimiento_normativo=True),
    "A09": dict(incumplimiento_normativo=True, afectacion_individual=True),
    "A11": dict(otro_medio_judicial=True, medio_eficaz=False, perjuicio_irremediable=True),
    "A01": dict(dano_consumado=True),
    "A07": dict(dano_consumado=True),
    "A12": dict(dano_consumado=True),
    "E10": dict(otro_medio_judicial=True, medio_eficaz=True),
    "A06": dict(otro_medio_judicial=True, medio_eficaz=True, sujeto_especial_proteccion=True),
    "M04": dict(otro_medio_judicial=True, medio_eficaz=True),
    "M06": dict(acto_general=True, afectacion_individual=False),
    "M08": dict(privacion_libertad=True),
    "M09": dict(incumplimiento_normativo=True, afectacion_individual=False),
    "M15": dict(derecho_colectivo=True, titular_pide_lo_suyo=True,
                perjuicio_irremediable=True, afectacion_individual=True),
}


def motor_reglas(ctx: Contexto) -> None:
    """El art. 6 del Decreto 2591 son cinco causales tasadas que se aplican en
    orden. Pedirle a un modelo que adivine el resultado de aplicar reglas
    escritas es lo que produce el colapso a "tutela": aqui el LLM extrae hechos
    y el motor decide."""
    todos = {e["id"]: e for e in schema.cargar() + ctx.eval_set + ctx.eval_m3}
    ok, discrepan = 0, []
    for cid, h in CASOS_MOTOR.items():
        d = reglas.decidir(reglas.Hechos(**h))
        bien = d.mecanismo == todos[cid]["mecanismo"]
        ok += bien
        if not bien:
            discrepan.append((cid, todos[cid]["mecanismo"], d.mecanismo))
    print(f"el motor coincide con el gold en {ok}/{len(CASOS_MOTOR)} casos")
    for cid, g, m in discrepan:
        print(f"  DISCREPA {cid}: gold={g} motor={m}")
    print()
    print("=== traza de M15: situacion colectiva pero el titular pide lo suyo ===")
    print(reglas.explicar(reglas.decidir(reglas.Hechos(**CASOS_MOTOR["M15"]))))


# --------------------------------------------------------------------------
# 6 · Los cuatro brazos
# --------------------------------------------------------------------------
def modelos(ctx: Contexto) -> None:
    """El modelo ajustado de M1 para los brazos 2 y 3, solo con GPU.

    El generador recorta la cola degenerada (el adaptador abre turnos falsos
    del chat en una fraccion de los casos) y anota en `ctx.recortes` el
    comienzo de cada caso recortado. Ya no se construye el generador de Groq
    que la celda creaba y nadie usaba.
    """
    if not ctx.hay_gpu:
        print("sin GPU: los brazos 2 y 3 se omiten")
        return
    from amparo.finetuning import generacion
    mdl, tok = generacion.cargar_modelo(MODELO_BASE, adaptador=RAIZ / ADAPTADOR)
    parada = generacion.ids_parada(tok)
    print("tokens de parada:", parada)
    ctx.generar_qwen = generacion.generador_hf(mdl, tok, parada=parada, max_new=MAX_NEW,
                                               recortar=True, recortes=ctx.recortes)
    print(f"modelo ajustado cargado desde {ADAPTADOR}")


# ROADMAP #32. El fallo del brazo 4 casi se llevo 18 minutos de trabajo de los
# brazos 2 y 3, que estaban solo en memoria. Un brazo que ya corrio es un hecho:
# no tiene por que depender de que el siguiente no reviente. Se guarda tras
# CADA brazo en `brazos_checkpoint.json` y se relee al empezar, asi que volver a
# correr la etapa retoma donde quedo en vez de repetir llamadas ya pagadas.
def _cargar_ck(ctx: Contexto) -> None:
    ctx.ruta_ck = ctx.c.ruta_cache("brazos_checkpoint.json")
    ck = arranque.cargar_checkpoint(ctx.ruta_ck)
    ctx.brazos = ck.get("brazos", {})
    ctx.latencias = ck.get("latencias", {})
    ctx.fallos_por_brazo = ck.get("fallos", {})
    if ctx.brazos:
        print(f"checkpoint: {len(ctx.brazos)} brazo(s) ya calculado(s), se reutilizan")
        for n in ctx.brazos:
            print(f"   {n}")


def _ck_guardar(ctx: Contexto) -> None:
    arranque.guardar_checkpoint(ctx.ruta_ck, {"brazos": ctx.brazos,
                                              "latencias": ctx.latencias,
                                              "fallos": ctx.fallos_por_brazo})


def _correr_o_reusar(ctx: Contexto, sis, nombre_corto: str) -> None:
    if sis.etiqueta in ctx.brazos:
        print(f"  {sis.etiqueta}: ya estaba en el checkpoint, se salta")
        return
    r = br.correr_brazo(sis, nombre_corto, ctx.casos_todos)
    ctx.brazos[sis.etiqueta] = r.salidas
    # BUG HEREDADO DEL NOTEBOOK, CONSERVADO A PROPOSITO EN LA MIGRACION: las
    # latencias y fallos se guardan con el nombre corto ("brazo 2"), pero
    # `scorecards()` busca la latencia por etiqueta ("2 · fine-tuned + RAG
    # ingenuo") y cae a 0.0, asi que `latencia_s_por_caso` sale 0.0 en todos
    # los brazos (solo en `scorecards.json` de la corrida, no en lo publicado).
    # Arreglarlo es cambiar una cifra: se decide fuera de la migracion.
    ctx.latencias[nombre_corto] = r.latencia_s
    ctx.fallos_por_brazo[nombre_corto] = r.fallos
    _ck_guardar(ctx)


def brazo_uno(ctx: Contexto) -> None:
    """El brazo 1 son las predicciones de M1, y solo existe para el eval
    compartido: M1 nunca vio el eval de M3. Tambien se registra de QUE corrida
    de M1 salen, que es la linea base de toda la comparacion."""
    preds, ctx.corrida_m1 = predicciones.cargar_m1(eval_set=ctx.eval_set)
    ctx.brazos[BRAZO_1] = {e["id"]: p["finetuned"] for e, p in zip(ctx.eval_set, preds)}


def correr_brazos(ctx: Contexto, cliente=None) -> None:
    """Brazos 2 y 3 (si hay modelo) y brazo 4 (agente), con checkpoint."""
    from amparo.sistemas import agente, sistema
    c = ctx.c
    _cargar_ck(ctx)
    brazo_uno(ctx)

    elegida = ctx.decision["elegida"]
    if ctx.generar_qwen is not None:
        ctx.s_ing = sistema.SistemaRAG(ctx.generar_qwen, ctx.indice, "ingenuo", k=K,
                                       etiqueta=BRAZO_2)
        ctx.estrategia_ganadora, tr3, ctx.nombre_tr = br.transformador_para(elegida, ctx.tr)
        print(f"brazo 3 despliega -> estrategia: {ctx.estrategia_ganadora} · "
              f"transformacion: {ctx.nombre_tr}   (ganadora: {elegida})")
        ctx.s_adv = sistema.SistemaRAG(ctx.generar_qwen, ctx.indice, ctx.estrategia_ganadora,
                                       k=K, transformador=tr3, etiqueta=BRAZO_3)
        _correr_o_reusar(ctx, ctx.s_ing, "brazo 2")
        _correr_o_reusar(ctx, ctx.s_adv, "brazo 3")

    ctx.ag = ag = agente.Agente(cliente or _cliente_groq(), ctx.indice, estrategia="reranked",
                                k=K_AGENTE, transformador=ctx.tr,
                                cache_path=c.ruta_cache("agente.json"), etiqueta=BRAZO_4)
    _correr_o_reusar(ctx, ag, "brazo 4")
    ag.guardar_cache()
    ctx.tr.guardar()

    ag.imprimir_resumen()
    c.guardar_json("agente_resumen", ag.resumen())
    c.guardar_json("config_brazos", {
        "corrida_m1_del_brazo_1": ctx.corrida_m1,
        "ganadora_de_recuperacion": elegida,
        "estrategia_desplegada_brazo3": ctx.estrategia_ganadora,
        "transformacion_desplegada_brazo3": ctx.nombre_tr,
        "fallos_de_api_por_brazo": {k: len(v) for k, v in ctx.fallos_por_brazo.items()},
    })
    # Los casos que el generador local recorto. Antes se juntaban en
    # `RECORTES_M3` y no se guardaban en ninguna parte.
    c.guardar_json("recortes_m3", {"n": len(ctx.recortes), "casos": ctx.recortes})
    c.nota(f"brazo 1 desde la corrida m1 {ctx.corrida_m1 or 'sin registrar'}")
    c.nota(f"brazo 3 desplego {ctx.estrategia_ganadora} + {ctx.nombre_tr} (ganadora: {elegida})")
    c.guardar_json("agente_trazas", ag.trazas)


# --------------------------------------------------------------------------
# 7 · RAGAS y el harness, cruzados
# --------------------------------------------------------------------------
def ragas_propio(ctx: Contexto, juez=None) -> None:
    """Las cuatro metricas RAGAS de `amparo/rag/ragas_eval.py`: dos se calculan
    de forma EXACTA, porque el `fundamento` del gold dice que articulos debian
    recuperarse, y no gastan tokens; las otras las puntua el juez.

    LAS DOS COLUMNAS NO SE PUEDEN LEER POR SEPARADO, Y SE DICE DENTRO DEL
    ARTEFACTO. En m3/20261016T215955Z `faithfulness` exacta daba 0.589 para el
    brazo 2 y el juez 0.143, mientras en `context_precision` el juez era MAS
    generoso: divergencia, no un desfase corregible con un offset.
    """
    import importlib.util
    from amparo.evaluacion.juez import Juez
    ctx.juez = j = juez or Juez(cache=ctx.c.ruta_cache("juez.json"))
    ctx.por_id = {ch["id"]: ch for ch in ctx.chunks}
    ctx.contextos = {}
    for s in (ctx.s_ing, ctx.s_adv, ctx.ag):
        if s is not None:
            ctx.contextos[s.etiqueta] = [t["recuperados"] for t in s.trazas]

    casos = ctx.casos_todos
    rs = []
    for nombre, ids_por_caso in ctx.contextos.items():
        cx = [[ctx.por_id[i] for i in ids if i in ctx.por_id] for ids in ids_por_caso]
        sal = [ctx.brazos[nombre][e["id"]] for e in casos]
        rs.append(ragas_eval.evaluar(nombre, sal, cx, casos,
                                     relatos=[e["relato"] for e in casos], juez=j))
    ragas_eval.imprimir(rs)

    lib = importlib.util.find_spec("ragas") is not None
    for r in rs:
        e, jz = r.get("exactas", {}), r.get("juez", {})
        r["_implementacion"] = ("libreria ragas" if lib
                                else "implementacion propia (amparo/rag/ragas_eval.py); "
                                     "la libreria `ragas` NO esta instalada")
        r["_divergencia_exacta_vs_juez"] = {k: round(jz[k] - e[k], 4) for k in set(e) & set(jz)}
        r["_lectura"] = (
            "`exactas` se calcula contra el gold con reglas deterministas; `juez` "
            "lo puntua un LLM. Divergen, y no con un desfase constante: en esta "
            "corrida el juez fue mucho mas severo en faithfulness y mas generoso "
            "en context_precision. Ninguna de las dos se puede reportar sola. "
            "Coherente con la dimension 2 de M2, donde el juez coincide con otro "
            "juez (kappa 0.76) mucho mejor que con la verdad de dominio (0.26).")
    print()
    if rs:
        print(f"  implementacion: {rs[0]['_implementacion']}")
    print("  divergencia juez - exacta, por brazo:")
    for r in rs:
        d = r["_divergencia_exacta_vs_juez"]
        print(f"    {r['sistema']:<32}" + "  ".join(f"{k}={v:+.3f}" for k, v in sorted(d.items())))
    print("  Signos opuestos entre metricas = divergencia, no calibracion.")
    ctx.rs = rs
    ctx.c.guardar_json("ragas", rs)


def _media(filas, m):
    return sum(f[m] for f in filas) / len(filas) if filas else 0.0


def cruce(ctx: Contexto) -> None:
    """¿Los aciertos del brazo 4 son del retrieval? Un caso puede acertar sin
    que el contexto respalde la respuesta; se mide caso por caso con las
    metricas exactas, que no cuestan tokens.

    EL DELTA VA SOBRE LOS EVALUABLES. Los casos de abstencion no tienen
    mecanismo gold: `acierta` es False por construccion y sus metricas son 0.0.
    Meterlos en "fallan" infla el delta; sobre m3/20261016T215955Z la
    faithfulness CAMBIABA DE SIGNO (+0.012 contra -0.018 real). Se imprimen las
    dos columnas para que la diferencia quede a la vista.
    """
    nombre_ag = ctx.ag.etiqueta
    ctx.ctx_ag = [[ctx.por_id[i] for i in ids if i in ctx.por_id]
                  for ids in ctx.contextos[nombre_ag]]
    filas = []
    for e, cx in zip(ctx.casos_todos, ctx.ctx_ag):
        sal = ctx.brazos[nombre_ag][e["id"]]
        p = schema.parse_salida(sal)
        filas.append({
            # `evaluable` es False en los casos de abstencion: sin esta columna,
            # `acierta=False` se lee como "fallo" cuando significa "no aplica".
            "id": e["id"], "tipo": e["tipo"],
            "evaluable": e["mecanismo"] is not None,
            "acierta": p.get("mecanismo") == e["mecanismo"],
            "context_recall": round(ragas_eval.context_recall_exacto([cx], [e]), 3),
            "context_precision": round(ragas_eval.context_precision_exacta([cx], [e]), 3),
            "faithfulness": round(ragas_eval.faithfulness_exacta([sal], [cx]), 3),
        })
    ctx.filas_cruce = filas

    evaluables = [f for f in filas if f["evaluable"]]
    ac = [f for f in evaluables if f["acierta"]]
    fa = [f for f in evaluables if not f["acierta"]]
    todo_ac = [f for f in filas if f["acierta"]]
    todo_fa = [f for f in filas if not f["acierta"]]
    print(f"  evaluables {len(evaluables)} · abstencion {len(filas) - len(evaluables)} "
          f"(sin mecanismo gold, fuera del delta)")
    print()
    print(f"  {'metrica':<20}{'aciertan':>10}{'fallan':>10}{'delta':>10}"
          f"{'si entrara abstencion':>24}")
    print("  " + "-" * 74)
    for m in ("context_recall", "context_precision", "faithfulness"):
        a, b = _media(ac, m), _media(fa, m)
        sesgado = _media(todo_ac, m) - _media(todo_fa, m)
        marca = "  <-- cambia de signo" if (a - b) * sesgado < 0 else ""
        print(f"  {m:<20}{a:>10.3f}{b:>10.3f}{a - b:>+10.3f}{sesgado:>+24.3f}{marca}")
    print(f"  {'':<20}{'n=' + str(len(ac)):>10}{'n=' + str(len(fa)):>10}")
    print()
    print("  La ultima columna NO es un resultado: es lo que daria metiendo las")
    print("  filas de abstencion, y esta ahi para que no se vuelva a colar.")
    print()
    ctx.sin_respaldo = [f["id"] for f in ac if f["context_recall"] == 0]
    print(f"ACIERTOS CON context_recall = 0: {len(ctx.sin_respaldo)} de {len(ac)}")
    print(f"  {ctx.sin_respaldo}")
    if ctx.sin_respaldo:
        print("Esos aciertos NO se pueden atribuir al retrieval. En el brazo 4 la")
        print("explicacion es el motor de reglas: el mecanismo lo deriva el art. 6")
        print("del Decreto 2591, no el texto recuperado. Acierto legitimo, de otra fuente.")
    else:
        print("Todos los aciertos tienen respaldo en el contexto recuperado.")
    ctx.c.guardar_csv("cruce_ragas_harness", filas)


def ragas_libreria(ctx: Contexto) -> None:
    """Contraste con la libreria `ragas` real sobre MUESTRA casos. Si divergen,
    el sospechoso somos nosotros. El LLM juez va EXPLICITO: `ragas.evaluate()`
    sin `llm=` apunta a OpenAI, y este proyecto solo tiene clave de Groq, que
    sirve un endpoint compatible con OpenAI.

    La instalacion esta en la primera celda del notebook: un `pip install` a
    estas alturas actualizaria paquetes ya importados y el fallo saldria como un
    error de atributo dentro de ragas, lejos de su causa.
    """
    from amparo.evaluacion.juez import MODELO as modelo_juez
    nombre_ag = ctx.ag.etiqueta
    try:
        from datasets import Dataset as HFDataset
        from langchain_openai import ChatOpenAI
        import ragas as ragas_lib
        from ragas import evaluate as ragas_evaluate
        from ragas.llms import LangchainLLMWrapper
        from ragas.metrics import faithfulness as m_faith

        casos_m = ctx.casos_todos[:MUESTRA]
        ctx_m = ctx.ctx_ag[:MUESTRA]
        filas = {
            "question": [e["relato"] for e in casos_m],
            "answer": [ctx.brazos[nombre_ag][e["id"]] for e in casos_m],
            "contexts": [[f"[{x['articulo']} {x['norma']}] {x['texto']}" for x in cx]
                         for cx in ctx_m],
            "ground_truth": [schema.render_salida(e) for e in casos_m],
        }
        llm = LangchainLLMWrapper(ChatOpenAI(
            model=modelo_juez, base_url="https://api.groq.com/openai/v1",
            api_key=os.environ["GROQ_API_KEY"], temperature=0))
        print(f"ragas {ragas_lib.__version__} sobre {MUESTRA} casos, "
              f"juzgando con {modelo_juez} via Groq...")
        res = ragas_evaluate(HFDataset.from_dict(filas), metrics=[m_faith], llm=llm)
        print("libreria :", res)
        nuestro = ragas_eval.faithfulness_exacta(filas["answer"], ctx_m)
        print(f"nuestro faithfulness EXACTO sobre los mismos {MUESTRA}: {nuestro:.3f}")
        ctx.c.guardar_json("ragas_libreria", {
            "muestra": MUESTRA, "resultado": str(res), "nuestro_exacto": nuestro,
            "version_ragas": ragas_lib.__version__, "llm_juez_de_ragas": modelo_juez,
            "lectura": (
                "La libreria y la metrica propia NO miden lo mismo y no deberian "
                "coincidir: la libreria le pregunta a un LLM si el contexto "
                "sostiene cada afirmacion; la nuestra comprueba si cada CITA esta "
                "respaldada por el contexto. El contraste sirve para ver si "
                "apuntan en la misma direccion, no para validar una con la otra.")})
    except Exception as ex:                                  # noqa: BLE001
        print("no se pudo correr la libreria:", str(ex)[:300])
        print("Las metricas exactas y con juez de la etapa anterior NO dependen de esto.")
        ctx.c.guardar_json("ragas_libreria", {
            "error": str(ex)[:300], "pin_intentado": RAGAS_PIN,
            "llm_juez_intentado": modelo_juez,
            "lectura": (
                "El contraste contra la libreria no se pudo correr. Las metricas "
                "RAGAS que el reporte publica son implementacion propia "
                "(`amparo/rag/ragas_eval.py`) y no dependen de esto; lo que falta "
                "es el contraste que diria si apuntan en la misma direccion.")})


# --------------------------------------------------------------------------
# 8 · El harness de M2, sin un solo cambio
# --------------------------------------------------------------------------
def scorecards(ctx: Contexto) -> None:
    """Cada brazo sobre todo lo que puede responder: el 1 solo sobre el eval
    compartido, los 2-4 sobre compartido + M3."""
    ctx.scorecards = []
    for nombre, salidas_por_id in ctx.brazos.items():
        casos = ctx.eval_set if nombre.startswith("1 ") else ctx.casos_todos
        sal = [salidas_por_id[e["id"]] for e in casos]
        sc = harness.tabla_puente(casos, sal, nombre, juez=ctx.juez)
        sc["latencia_s_por_caso"] = round(ctx.latencias.get(nombre, 0.0), 2)
        ctx.scorecards.append(sc)
        metricas.imprimir(sc)


def comunes(ctx: Contexto) -> None:
    """Los cuatro brazos sobre LOS MISMOS casos: es la tabla que hay que citar
    para decir cual es mejor. La anterior pone en columnas contiguas conjuntos
    distintos, con clases mayoritarias distintas.

    El ganador NO es el mismo segun el tipo de caso, y esa es la conclusion: el
    agregado esta dominado por los gold y premia al brazo que ya los resolvia.
    """
    ev = ctx.eval_set
    ctx.comunes = [e["id"] for e in ev]
    # Conteos derivados, nunca cableados: el eval set crecio de 46 a 69 casos
    # y los numeros escritos a mano quedaron mintiendo.
    n_gold = sum(e["tipo"] == "gold" for e in ev)
    n_juzgables = sum(e["mecanismo"] is not None for e in ev)
    ctx.scorecards_comunes = []
    for nombre, salidas_por_id in ctx.brazos.items():
        if any(i not in salidas_por_id for i in ctx.comunes):
            print(f"  {nombre}: no cubre los {len(ctx.comunes)} comunes, se omite")
            continue
        ctx.scorecards_comunes.append(
            metricas.scorecard([salidas_por_id[i] for i in ctx.comunes], ev, nombre))

    print(f"{'brazo':<34}{'n':>4}{'acc_mec':>9}{'macroF1':>9}{'juridico':>10}"
          f"{'gold':>8}{'advers':>8}")
    print("-" * 82)
    for sc in ctx.scorecards_comunes:
        pt = sc.get("por_tipo", {})
        print(f"{sc['sistema']:<34}{sc['n']:>4}"
              f"{sc['campos']['mecanismo']['accuracy']:>9.3f}"
              f"{sc['campos']['mecanismo']['macro_f1']:>9.3f}"
              f"{sc['acierto_juridico']:>10.3f}"
              f"{pt.get('gold', {}).get('acierto_juridico', 0):>8.3f}"
              f"{pt.get('adversarial', {}).get('acierto_juridico', 0):>8.3f}")

    scs = ctx.scorecards_comunes
    ctx.mejor_glob = max(scs, key=lambda s: s["acierto_juridico"])
    ctx.mejor_gold = max(scs, key=lambda s: s["por_tipo"].get("gold", {}).get("acierto_juridico", 0))
    ctx.mejor_adv = max(scs, key=lambda s: s["por_tipo"].get("adversarial", {}).get("acierto_juridico", 0))
    print()
    print(f"  mejor en agregado   : {ctx.mejor_glob['sistema']}")
    print(f"  mejor en gold       : {ctx.mejor_gold['sistema']}")
    print(f"  mejor en adversarial: {ctx.mejor_adv['sistema']}")
    if ctx.mejor_gold["sistema"] != ctx.mejor_adv["sistema"]:
        print()
        print("  No hay un ganador unico: el agregado esta dominado por los")
        print(f"  casos gold ({n_gold} de {n_juzgables} juzgables), asi que premia")
        print("  al brazo que ya los resolvia. En los adversariales gana otro.")
        print("  Reportar solo el agregado esconde eso.")

    por_caso = br.matriz_por_caso(ctx.brazos, ev, ctx.comunes)
    techo = br.techo_union(por_caso)
    n = techo["n"]
    print()
    print(f"  TECHO DE COMBINAR BRAZOS sobre {n} casos")
    for nombre, v in sorted(techo["por_brazo"].items(), key=lambda x: -x[1]):
        print(f"    {nombre:<34}{v:>4}/{n}  {v/n:.1%}")
    print(f"    {'acierta ALGUN brazo (union)':<34}{techo['union']:>4}/{n}  {techo['union']/n:.1%}")
    print(f"    margen sobre el mejor brazo suelto: {techo['margen_sobre_el_mejor']:+.1%}")
    print("    Es una COTA SUPERIOR y no un resultado: la daria un enrutador perfecto.")
    techo["lectura"] = ("COTA SUPERIOR, no un resultado: la daria un enrutador "
                        "perfecto. Si el margen es cero, ninguna combinacion de "
                        "estos brazos puede superar al mejor suelto.")
    ctx.c.guardar_json("por_caso", {
        "_que_es": ("la matriz por caso y brazo de la que salen los agregados. "
                    "Permite preguntar que casos rescata un brazo que otro falla, "
                    "que es lo que define el techo de cualquier combinacion."),
        "techo_union": techo,
        "casos": por_caso})
    ctx.c.guardar_json("scorecards_comunes", ctx.scorecards_comunes)
    ctx.c.guardar_json("ganadores", {
        "subconjunto": f"los {len(ctx.comunes)} casos de {ARCHIVO_EVAL}, "
                       f"comunes a los cuatro brazos",
        "agregado": ctx.mejor_glob["sistema"],
        "gold": ctx.mejor_gold["sistema"],
        "adversarial": ctx.mejor_adv["sistema"]})


def comparar(ctx: Contexto) -> None:
    metricas.comparar(ctx.scorecards[0], ctx.scorecards[-1])
    print()
    print(f"{'sistema':<34}{'acc_mec':>9}{'gold':>8}{'advers':>8}{'abstenc':>9}{'s/caso':>8}")
    print("-" * 76)
    for sc in ctx.scorecards:
        ab = sc.get("abstencion")
        # `acierto_abstencion` es None cuando el conjunto no trae casos sin
        # respuesta correcta, asi que no basta comprobar que `ab` exista.
        ab_txt = ("n/a" if not ab or ab.get("acierto_abstencion") is None
                  else f"{ab['acierto_abstencion']:.0%}")
        print(f"{sc['sistema']:<34}{sc['campos']['mecanismo']['accuracy']:>9.1%}"
              f"{sc['por_tipo'].get('gold', {}).get('acierto_juridico', 0):>8.1%}"
              f"{sc['por_tipo'].get('adversarial', {}).get('acierto_juridico', 0):>8.1%}"
              f"{ab_txt:>9}{sc['latencia_s_por_caso']:>8.1f}")


def tabla_costos(ctx: Contexto) -> None:
    """Lo que CUESTA conseguir cada acierto (p50, llamadas reales frente a
    cache, tokens). El brazo 1 aparece en None, no en 0: su coste es el de M1."""
    sistemas = [s for s in (ctx.s_ing, ctx.s_adv, ctx.ag) if s is not None]
    ctx.filas_costos = costos.tabla([br.BrazoNoMedido(BRAZO_1)] + sistemas)
    costos.imprimir(ctx.filas_costos)
    ctx.c.guardar_json("costos", ctx.filas_costos)


def publicar(ctx: Contexto):
    """Escribe los dos CSV, comprueba TODOS los artefactos y publica.

    `m3_scorecard.csv` pone el brazo 1 con su n al lado de los brazos 2-4 con
    otro n y otra base mayoritaria: son conjuntos distintos, porque M1 no tiene
    predicciones sobre `eval_set_m3.json`. La tabla sobre los COMUNES es la que
    se puede leer como comparacion, y se publican las dos.
    """
    c = ctx.c
    harness.a_csv(ctx.scorecards, str(c.dir / "scorecard.csv"))
    c.artefactos["scorecard"] = "scorecard.csv"
    c.guardar_json("scorecards", ctx.scorecards)
    c.guardar_json("salidas", ctx.brazos)
    harness.a_csv(ctx.scorecards_comunes, str(c.dir / "scorecard_comunes.csv"))
    c.artefactos["scorecard_comunes"] = "scorecard_comunes.csv"

    A_PUBLICAR = [
        ("scorecard", "results/m3_scorecard.csv"),
        ("costos", "results/m3_costos.json"),
        ("retrieval", "results/m3_retrieval.json"),
        ("ragas", "results/m3_ragas.json"),
        ("chunking", "results/m3_chunking.json"),
        ("agente_resumen", "results/m3_agente.json"),
        ("cruce_ragas_harness", "results/m3_cruce.csv"),
        ("scorecard_comunes", "results/m3_scorecard_comunes.csv"),
        ("scorecards_comunes", "results/m3_scorecards_comunes.json"),
        # La matriz por caso y brazo: define el techo de cualquier combinacion.
        ("por_caso", "results/m3_por_caso.json"),
        ("ganadores", "results/m3_ganadores.json"),
        ("decision_retrieval", "results/m3_decision_retrieval.json"),
        ("ragas_libreria", "results/m3_ragas_libreria.json"),
        # Las trazas del agente: la evidencia para saber que hechos extrae en
        # los casos de `accion_cumplimiento` (ROADMAP3 M3-1).
        ("agente_trazas", "results/m3_agente_trazas.json"),
    ]
    QUIEN_LO_GENERA = {
        "chunking": "etapa `chunking` (seccion 2)",
        "retrieval": "etapa `recuperacion` (seccion 3)",
        "decision_retrieval": "etapa `recuperacion` (seccion 3)",
        "agente_resumen": "etapa `correr_brazos` (seccion 6)",
        "agente_trazas": "etapa `correr_brazos` (seccion 6)",
        "ragas": "etapa `ragas_propio` (seccion 7)",
        "ragas_libreria": "etapa `ragas_libreria` (seccion 7)",
        "cruce_ragas_harness": "etapa `cruce` (seccion 7)",
        "scorecards_comunes": "etapa `comunes` (seccion 8)",
        "por_caso": "etapa `comunes` (seccion 8)",
        "ganadores": "etapa `comunes` (seccion 8)",
        "costos": "etapa `tabla_costos` (seccion 8)",
    }
    publicar_todo(c, A_PUBLICAR, QUIEN_LO_GENERA)

    print()
    print("  CUAL ES CUAL, porque se publican las dos:")
    print(f"    m3_scorecard_comunes.csv   n={ctx.scorecards_comunes[0]['n']} en los "
          f"cuatro brazos  <- COMPARABLE")
    print(f"    m3_scorecard.csv           n mixta ("
          f"{', '.join(str(s['n']) for s in ctx.scorecards)})  <- cada brazo sobre su "
          f"propio conjunto")
    print("    Para afirmar que un brazo es mejor que otro, la de los comunes.")

    ag = ctx.ag
    mejor_sc = max(ctx.scorecards, key=lambda s: s["acierto_juridico"])
    fallas = sum(v for k, v in ag.contadores.items()
                 if k.startswith(("argumentos", "herramienta", "llamada", "pasos")))
    c.cerrar(valida=bool(ag.contadores["tool_invocada"]), notas=[
        f"chunking elegido: {ctx.dec_chunk['elegido']}",
        f"retrieval elegido: {ctx.decision['elegida']} "
        f"(descalificadas: {ctx.decision['descalificadas'] or 'ninguna'})",
        # Sobre los COMUNES y desglosado por tipo: el agregado solo esconde
        # justamente el hallazgo.
        f"sobre los {len(ctx.comunes)} comunes -> agregado: {ctx.mejor_glob['sistema']} · "
        f"gold: {ctx.mejor_gold['sistema']} · adversarial: {ctx.mejor_adv['sistema']}",
        f"(sobre su propio conjunto, mejor agregado: {mejor_sc['sistema']} "
        f"con acierto juridico {mejor_sc['acierto_juridico']:.4f})",
        f"herramientas invocadas: {ag.contadores['tool_invocada']}, fallas manejadas: {fallas}",
        f"aciertos sin respaldo en el contexto: {len(ctx.sin_respaldo)}",
    ])
    import pandas as pd
    return pd.read_csv(RAIZ / "results" / "m3_scorecard.csv").set_index("sistema").T


# --------------------------------------------------------------------------
# 10 · Cierre de la entrega
# --------------------------------------------------------------------------
# Los cuatro pasos de "ya acabo, ¿quedo bien?", juntos: por separado es facil
# correr uno y olvidar los otros, y el que se olvida siempre es el que habria
# avisado. `verificar_entrega.py` existia desde el ROADMAP v1 y no se habia
# corrido NI UNA VEZ. Ninguno escribe en `results/`, y ninguno corta el cierre
# si falla: se corren los cuatro y se resume al final.
PASOS_CIERRE = [
    (["data/verificar_entrega.py"], "artefactos, corridas y huellas",
     "la entrega NO es coherente: o faltan artefactos, o no son del mismo "
     "experimento. Las cifras no se pueden comparar"),
    (["data/reporte.py"], "genera REPORTE.md desde los artefactos",
     "el reporte no se escribio: falta algun artefacto"),
    (["data/diagnostico_cumplimiento.py"], "cual de las 6 causas rompe accion_cumplimiento",
     "no se pudo leer las trazas del agente"),
    (["data/calibracion_juez.py", "--preparar"],
     "formulario de calibracion (10 casos, para una persona)", "falta M1 o M2"),
]


def cierre(ctx: Contexto | None = None) -> list[tuple[str, int]]:
    res = []
    for args, que, si_falla in PASOS_CIERRE:
        print()
        print("=" * 74)
        print(f"  {args[0].split('/')[-1]} · {que}")
        print("=" * 74)
        r = subprocess.run([sys.executable, "-I"] + args, capture_output=True,
                           text=True, cwd=str(RAIZ))
        print((r.stdout or "").rstrip()[-4000:])
        if r.stderr.strip():
            print("  stderr:", r.stderr.strip()[-600:])
        res.append((args[0], r.returncode, si_falla))

    print()
    print("#" * 74)
    print("  RESUMEN DEL CIERRE")
    print("#" * 74)
    for a, codigo, si in res:
        print(f"  {'OK   ' if codigo == 0 else 'FALLA'} {a.split('/')[-1]:32s}"
              + ("" if codigo == 0 else f"  <- {si}"))
    malos = [a for a, codigo, _ in res if codigo != 0]
    print()
    if not malos:
        print("  Los cuatro pasan. La entrega es coherente, REPORTE.md esta escrito")
        print("  y data/calibracion_1.csv espera a que una persona lo califique.")
    else:
        print(f"  {len(malos)} paso(s) con problemas. Arriba esta el detalle de cada uno.")
    print("#" * 74)
    print()
    print("  LO QUE SIGUE, Y NO SE PUEDE HACER AQUI:")
    print("  · Bajar data/calibracion_1.csv y darselo a la MISMA persona externa")
    print("    que hizo la doble anotacion. Son 10 casos, ~15 min.")
    print("  · Al devolverlo:  python -I data/calibracion_juez.py --medir \\")
    print("                      --anotador persona-externa")
    return [(a, codigo) for a, codigo, _ in res]


def correr(ctx: Contexto | None = None) -> Contexto:
    """Todas las etapas en orden, como el notebook de punta a punta."""
    ctx = ctx or preparar()
    for etapa in (corpus, auditar_corpus, chunking, recuperacion, consultas_fallidas,
                  demo_terminos, fallas_agente, motor_reglas, modelos, correr_brazos,
                  ragas_propio, cruce, ragas_libreria, scorecards, comunes, comparar,
                  tabla_costos, publicar, cierre):
        etapa(ctx)
    return ctx
