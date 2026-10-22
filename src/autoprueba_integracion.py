"""
Autoprueba de integracion: toda la fontaneria, sin GPU y sin API.

    python -I src/autoprueba_integracion.py

POR QUE EXISTE

Los tres notebooks tardan 7, 3 y 45 minutos y necesitan A100, API de Groq y
Drive montado. Entre bloques de trabajo se acumula codigo que solo se ha
probado a mano y a pedazos, y el costo de depurar N cambios a la vez es mucho
peor que lineal: si M3 revienta en el minuto 45, hay que bisecar entre todo lo
que se toco desde la ultima corrida.

Esto ejercita lo que NO necesita modelo: los artefactos de datos, el motor de
reglas, las metricas, el scorecard, el puente v1/v2, el brazo oraculo, los
costos, los terminos y el kit de doble anotacion. Con generadores de mentira,
deterministas y gratis.

QUE NO PUEDE ATRAPAR, para no dar falsa seguridad:

  - el comportamiento real del modelo: degeneracion, tokenizacion, si el
    ajustado responde distinto en los 23 casos nuevos de v2;
  - el comportamiento real de la API: 400 de Groq, el juez ante
    `mecanismo: null`, el no-determinismo del juez;
  - choques de dependencias en Colab;
  - si los arreglos del presupuesto del agente sirven (ROADMAP #9), que es
    justamente lo que solo una corrida dice.

Complementa `src/autoprueba_agente.py`, que cubre los cinco modos de falla del
agente con un cliente guionado. Esta cubre el resto.
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "src"))

import costos                                   # noqa: E402
import metricas                                 # noqa: E402
import ragas_eval                               # noqa: E402
import rag                                      # noqa: E402
import schema                                   # noqa: E402
import sistema                                  # noqa: E402
import terminos                                 # noqa: E402
import harness                                  # noqa: E402
from reglas import (CAMPOS_DESGLOSE, HECHOS_EXTRAIBLES, Hechos, decidir,
                    estrato_verificacion)        # noqa: E402

DATA = RAIZ / "data"
PRUEBAS = []


def prueba(nombre: str):
    def deco(fn):
        PRUEBAS.append((nombre, fn))
        return fn
    return deco


def _cargar(a):
    return schema.cargar(archivo=a)


def _perfecta(casos):
    """Predicciones perfectas: el gold renderizado. La referencia de todo."""
    return [schema.render_salida(c) for c in casos]


# ==========================================================================
# 1 · artefactos de datos
# ==========================================================================
@prueba("los cinco artefactos de datos cargan y validan")
def t_cargan():
    n = {}
    for a in ("dataset.json", "eval_set.json", "eval_set_v2.json",
              "eval_set_v3.json", "eval_set_m3.json"):
        n[a] = len(_cargar(a))
    err = schema.validar(_cargar("dataset.json") + _cargar("eval_set_v3.json")
                         + _cargar("eval_set_m3.json"))
    assert not err, f"schema.validar: {err[:3]}"
    assert n["eval_set.json"] == 46, n
    assert n["eval_set_v2.json"] == 69, n
    # v3 ES EL EVAL SET QUE USAN LOS TRES NOTEBOOKS. La version anterior de
    # esta prueba validaba v2 y m3, y por eso no cubria el archivo que de
    # verdad se evalua: el guardian de datos no miraba los datos usados.
    assert n["eval_set_v3.json"] == 109, n
    return (f"dataset {n['dataset.json']} · v1 46 · v2 69 · "
            f"v3 {n['eval_set_v3.json']} · m3 {n['eval_set_m3.json']} · "
            "0 errores")


@prueba("cada version del eval set contiene la anterior SIN TOCAR")
def t_superconjunto():
    """La vara no se mueve: v2 contiene v1 y v3 contiene v2, byte a byte.

    Es lo que permite comparar contra las corridas viejas: el puente
    `subconjunto_v1` de cada scorecard mide sobre los casos COMUNES, y eso
    solo vale si los comunes son realmente identicos. Ampliar en sitio, o
    "mejorar" de paso la redaccion de un relato viejo, destruiria doce
    corridas de comparabilidad sin que ninguna cifra lo delatara.
    """
    campos = ("relato", "mecanismo", "procede", "derecho", "fundamento",
              "tipo", "categoria", "razon", "pretension", "accionado",
              "hechos")
    cadena = [("eval_set.json", "eval_set_v2.json", 46),
              ("eval_set_v2.json", "eval_set_v3.json", 69)]
    for antes, despues, n in cadena:
        a, d = _cargar(antes), _cargar(despues)
        m = {c["id"]: c for c in d}
        faltan = [c["id"] for c in a if c["id"] not in m]
        assert not faltan, f"{despues} perdio casos de {antes}: {faltan[:5]}"
        dif = [f"{c['id']}.{k}" for c in a for k in campos
               if m[c["id"]].get(k) != c.get(k)]
        assert not dif, f"{antes} cambio dentro de {despues}: {dif[:5]}"
        assert [c["id"] for c in d[:n]] == [c["id"] for c in a], (
            f"{despues} altero el orden de los {n} de {antes}")
    return ("v1 (46) identico dentro de v2 y v2 (69) identico dentro de v3, "
            "en el mismo orden y con los mismos `hechos`")


@prueba("cero fuga de relatos entre entrenamiento y evaluacion")
def t_fuga():
    # `cargar(split)` es posicional; `cargar(archivo=...)` es otra cosa.
    tr = {c["relato"] for c in schema.cargar("train") + schema.cargar("validation")}
    for a in ("eval_set.json", "eval_set_v2.json", "eval_set_v3.json",
              "eval_set_m3.json"):
        ev = {c["relato"] for c in _cargar(a)}
        assert not (tr & ev), f"FUGA en {a}: {len(tr & ev)} relatos"
    ids = {c["id"] for c in _cargar("eval_set_v3.json")}
    ids_m3 = {c["id"] for c in _cargar("eval_set_m3.json")}
    assert not (ids & ids_m3), f"ids repetidos: {sorted(ids & ids_m3)[:5]}"
    # Y que los 33 casos nuevos de v3 no repitan un relato entre ellos: un
    # copia-pega al redactarlos daria dos casos con la misma historia y
    # distinta etiqueta, que es peor que no tenerlos.
    rel = [" ".join(c["relato"].split()).lower()
           for c in _cargar("eval_set_v3.json")]
    import collections as _col
    rep = [r[:60] for r, k in _col.Counter(rel).items() if k > 1]
    assert not rep, f"relatos repetidos dentro de v3: {rep[:3]}"
    return "0 relatos compartidos, 0 ids compartidos, 0 relatos repetidos"


@prueba("v3 no deja ninguna clase de `derecho` con soporte minimo")
def t_soporte_de_clases():
    """M1-4: el defecto que v3 vino a cerrar, y que no puede volver.

    `m1_scorecard_finetuned.json` de la corrida 20261018T200907Z reportaba
    SEIS clases del campo `derecho` con soporte <= 3 --- `minimo_vital` con
    **1** --- y `clases_con_soporte_minimo` las nombraba en cada scorecard.
    Un F1 de 0.000 con soporte 1 no dice nada sobre el sistema: dice que no
    hay muestra. El umbral <= 3 es el que usa `metricas.py`, asi que esta
    prueba vigila exactamente la cifra que el scorecard publica.

    Tambien se comprueba que el MECANISMO de cada caso siga siendo el que
    deriva el motor. Si alguien edita un `hechos` a mano, o cambia una
    etiqueta "para que cuadre", la etiqueta y los hechos dejan de
    corresponder y el gold queda plausible y falso. Esto lo caza sobre el
    archivo, no solo en el momento de generarlo.
    """
    import collections as _col
    from reglas import Hechos, decidir, estrato_verificacion

    v3 = _cargar("eval_set_v3.json")
    juzgables = [c for c in v3 if c.get("mecanismo")]
    sop = _col.Counter(c["derecho"] for c in juzgables)
    flacas = {k: v for k, v in sop.items() if v <= 3}
    assert not flacas, f"clases con soporte <= 3: {flacas}"
    assert len(juzgables) == 103, len(juzgables)

    # El motor y el archivo tienen que decir lo mismo, caso por caso.
    discrepan, estratos = [], []
    for c in juzgables:
        h = Hechos(**c["hechos"])
        d = decidir(h)
        if d.mecanismo != c["mecanismo"]:
            discrepan.append(f"{c['id']}: archivo {c['mecanismo']} vs motor "
                             f"{d.mecanismo}")
        if d.procede_tutela != c["procede"]:
            discrepan.append(f"{c['id']}: `procede` no coincide")
        est, _piv = estrato_verificacion(h)
        if est != c.get("estrato_verificacion"):
            estratos.append(f"{c['id']}: {c.get('estrato_verificacion')} "
                            f"vs {est}")
    assert not discrepan, f"etiquetas que el motor no respalda: {discrepan[:5]}"
    assert not estratos, f"estratos que el motor no respalda: {estratos[:5]}"

    adv = sum(1 for c in v3 if c["tipo"] == "adversarial")
    assert adv >= 39, f"el estrato adversarial bajo a {adv} (T-3 lo necesita)"
    return (f"{len(sop)} clases, la mas pequena con {min(sop.values())}; "
            f"{len(juzgables)} etiquetas derivadas del motor sin una sola "
            f"discrepancia; adversarial n={adv}")


# ==========================================================================
# 2 · motor de reglas
# ==========================================================================
@prueba("el motor deriva la etiqueta de todos los casos codificados")
def t_reglas():
    out = {}
    for a in ("dataset.json", "eval_set.json", "eval_set_v2.json"):
        ok = mal = 0
        for c in _cargar(a):
            if not c.get("hechos") or not c.get("mecanismo"):
                continue
            d = decidir(Hechos(**c["hechos"]))
            if d.mecanismo == c["mecanismo"] and d.procede_tutela == c["procede"]:
                ok += 1
            else:
                mal += 1
        assert not mal, f"{a}: {mal} casos que el motor no deriva"
        out[a] = ok
    return f"dataset {out['dataset.json']} · v1 {out['eval_set.json']} · v2 {out['eval_set_v2.json']}, 0 fallos"


@prueba("el test conjuntivo del desglose MUERDE")
def t_conjuntivo():
    # coherente: pasa
    Hechos(otro_medio_judicial=True, perjuicio_irremediable=True,
           pi_inminencia=True, pi_gravedad=True, pi_urgencia=True,
           pi_impostergabilidad=True)
    # incoherente: tiene que levantar
    for kw, que in (
        (dict(perjuicio_irremediable=True, pi_inminencia=True, pi_gravedad=True,
              pi_urgencia=False, pi_impostergabilidad=True), "falta un elemento"),
        (dict(perjuicio_irremediable=True, pi_inminencia=True), "desglose parcial"),
        (dict(medio_eficaz=True, me_idoneo=True, me_oportuno=False,
              me_accesible=True), "eficacia incoherente"),
    ):
        try:
            Hechos(**kw)
        except ValueError:
            continue
        raise AssertionError(f"NO levanto con {que}")
    return "3 combinaciones incoherentes rechazadas, la coherente aceptada"


@prueba("el extractor NO recibe los campos del desglose")
def t_extraibles():
    assert not (set(HECHOS_EXTRAIBLES) & CAMPOS_DESGLOSE), "se cruzan"
    assert "medio_eficaz" in HECHOS_EXTRAIBLES, "falta medio_eficaz"
    assert "me_idoneo" not in HECHOS_EXTRAIBLES, "me_idoneo no es extraible"
    # el bug real: armar Hechos con todos los campos en False
    booleanos = {k: False for k in HECHOS_EXTRAIBLES}
    booleanos["medio_eficaz"] = True
    Hechos(**booleanos)                  # no debe levantar
    return f"{len(HECHOS_EXTRAIBLES)} extraibles, {len(CAMPOS_DESGLOSE)} de desglose, disjuntos"


@prueba("los estratos de verificacion cuadran")
def t_estratos():
    from collections import Counter
    c = Counter(x["estrato_verificacion"] for x in _cargar("eval_set_v2.json")
                if x.get("estrato_verificacion"))
    assert sum(c.values()) == 63, f"suman {sum(c.values())}, deberian 63"
    assert c["juicio"] == 3, f"juicio={c['juicio']}, esperaba 3"
    for x in _cargar("eval_set_v2.json"):
        if not x.get("hechos") or not x.get("mecanismo"):
            continue
        est, _ = estrato_verificacion(Hechos(**x["hechos"]))
        assert est == x["estrato_verificacion"], f"{x['id']}: {est} != anotado"
    return f"plano {c['plano']} · derivado {c['derivado']} · juicio {c['juicio']}, recalculados"


# ==========================================================================
# 3 · los dos planos de la cita
# ==========================================================================
@prueba("una prediccion PERFECTA no produce ni una cita mal clasificada")
def t_planos():
    out = []
    for a in ("eval_set.json", "eval_set_v2.json", "eval_set_m3.json"):
        e = _cargar(a)
        pp = metricas.pertinencia_citas(_perfecta(e), e)["por_plano"]
        assert pp["disponible"], f"{a}: sin planos; corre anotar_fundamentos.py"
        cj = pp["cajas"]
        assert not cj.get("mecanismo_equivocado"), \
            f"{a}: {cj['mecanismo_equivocado']} citas de mecanismo mal clasificadas"
        assert not cj.get("derecho_impertinente"), \
            f"{a}: {cj['derecho_impertinente']} citas de fondo mal clasificadas"
        assert not cj.get("inventada"), f"{a}: {cj['inventada']} inventadas"
        out.append(f"{a.replace('eval_set', '').replace('.json', '') or 'v1'}:"
                   f"{cj['mecanismo_correcto']}+{cj['derecho_correcto']}")
    return "mec+fondo correctas, 0 errores · " + " ".join(out)


@prueba("la precision por plano dice `no medible` en vez de 0")
def t_no_medible():
    e = _cargar("eval_set_v2.json")
    vacias = ["Derecho: salud\nAccionado: EPS\nMecanismo: tutela\n"
              "Procedencia: si\nPretension: x\nFundamento: "] * len(e)
    pp = metricas.pertinencia_por_plano(vacias, e)
    assert pp["precision_mecanismo"] is None, pp["precision_mecanismo"]
    assert pp["precision_derecho"] is None, pp["precision_derecho"]
    return "sin citas emitidas -> None en los dos planos, no 0.0"


# ==========================================================================
# 4 · scorecard y sus secciones nuevas
# ==========================================================================
@prueba("el scorecard trae sus cinco secciones en los tres eval sets")
def t_scorecard():
    out = []
    for a in ("eval_set.json", "eval_set_v2.json", "eval_set_m3.json"):
        e = _cargar(a)
        sc = metricas.scorecard(_perfecta(e), e, "ctl")
        for k in ("ic", "por_tipo", "abstencion", "campos", "pertinencia_citas"):
            assert k in sc, f"{a}: falta {k}"
        assert sc["campos"]["mecanismo"]["accuracy"] == 1.0, \
            f"{a}: la perfecta no da 1.0"
        if any(x.get("fiabilidad_etiqueta") for x in e):
            assert "por_fiabilidad_etiqueta" in sc, f"{a}: falta fiabilidad"
        out.append(f"{a.split('_')[-1].replace('.json','')} n={sc['n']}")
    return " · ".join(out)


@prueba("los IC: reproducibles, acotados, y Wilson donde el bootstrap degenera")
def t_ic():
    a = metricas.bootstrap_ic([True] * 30 + [False] * 33)
    b = metricas.bootstrap_ic([True] * 30 + [False] * 33)
    assert a == b, "no reproducible"
    assert a["metodo"] == "bootstrap_percentil"
    deg = metricas.bootstrap_ic([True] * 45)
    assert deg["metodo"] == "wilson", deg["metodo"]
    assert deg["ic_bajo"] < 1.0, f"Wilson deberia dar < 1, dio {deg['ic_bajo']}"
    for v in (a, deg, metricas.bootstrap_ic([False] * 18)):
        assert 0.0 <= v["ic_bajo"] <= v["ic_alto"] <= 1.0, v
    x = metricas.bootstrap_ic([True] * 6 + [False] * 12)
    y = metricas.bootstrap_ic([True] * 8 + [False] * 10)
    assert metricas.ic_se_solapan(x, y), "2 casos de 18 NO deberia distinguirse"
    return (f"n=63 ±{a['amplitud']/2:.3f} · 45/45 -> wilson "
            f"[{deg['ic_bajo']:.3f}, 1.0] · solape detectado")


# ==========================================================================
# 5 · puente v1/v2
# ==========================================================================
@prueba("tabla_puente es sustituible por harness (devuelve un scorecard)")
def t_puente_dropin():
    v2 = _cargar("eval_set_v2.json")
    sc = harness.tabla_puente(v2, _perfecta(v2), "ctl")
    for k in ("sistema", "n", "campos", "acierto_juridico", "por_tipo",
              "abstencion", "ic", "puente"):
        assert k in sc, f"falta {k}: rompe los consumidores de aguas abajo"
    assert sc["puente"]["subconjunto_v1"]["n"] == 46
    assert sc["puente"]["completo"]["n"] == 63
    assert sc["puente"]["completo_es_eval_v2"] is True
    return "claves de scorecard presentes · v1 n=46 · completo n=63"


@prueba("el puente aisla el cambio de vara (control del colapso a tutela)")
def t_puente_control():
    v2 = _cargar("eval_set_v2.json")
    sal = []
    for c in v2:
        x = dict(c)
        x["mecanismo"], x["procede"] = "tutela", True
        sal.append(schema.render_salida(x))
    p = harness.tabla_puente(v2, sal, "colapso")["puente"]
    a = p["subconjunto_v1"]["acc_mecanismo"]
    b = p["completo"]["acc_mecanismo"]
    assert abs(a - 0.587) < 0.002, f"v1 deberia dar la baseline 0.587, dio {a}"
    assert abs(b - 0.4286) < 0.002, f"v2 deberia dar 0.4286, dio {b}"
    return (f"un sistema que colapsa saca exactamente las dos baselines: "
            f"{a:.4f} y {b:.4f}")


@prueba("el puente se marca NO disponible si no contiene todo v1")
def t_puente_degrada():
    m3 = _cargar("eval_set_m3.json")
    sc = harness.tabla_puente(m3, _perfecta(m3), "solo m3")
    assert sc["puente"]["disponible"] is False, "deberia marcarse no disponible"
    assert "motivo" in sc["puente"]
    return "sobre eval_m3 solo: no disponible, con motivo, sin excepcion"


@prueba("a_csv escribe con valores no medibles")
def t_csv():
    v2 = _cargar("eval_set_v2.json")
    sc = harness.tabla_puente(v2, _perfecta(v2), "ctl")
    m3 = _cargar("eval_set_m3.json")
    vacias = ["Derecho: salud\nAccionado: x\nMecanismo: tutela\n"
              "Procedencia: si\nPretension: x\nFundamento: "] * len(m3)
    sc2 = metricas.scorecard(vacias, m3, "sin citas")
    ruta = Path(tempfile.gettempdir()) / "_ap_integracion.csv"
    harness.a_csv([sc, sc2], str(ruta))
    cols = ruta.read_text(encoding="utf-8").splitlines()[0].split(",")
    os.remove(ruta)
    for c in ("precision_citas_mecanismo", "precision_citas_fondo"):
        assert c in cols, f"falta la columna {c}"
    return f"{len(cols)} columnas, incluidas las dos por plano"


# ==========================================================================
# 6 · RAG: oraculo y metricas de contexto
# ==========================================================================
def _chunks():
    d = json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))
    return rag.trocear(d["documentos"] if isinstance(d, dict) else d)


@prueba("el brazo oraculo tiene contexto PERFECTO (recall y precision = 1.0)")
def t_oraculo():
    casos = _cargar("eval_set_v2.json")
    ora = sistema.SistemaOraculo(lambda s, u: "", _chunks(), casos)
    ctx = [ora.contexto_gold(c) for c in casos]
    r = ragas_eval.context_recall_exacto(ctx, casos)
    p = ragas_eval.context_precision_exacta(ctx, casos)
    assert abs(r - 1.0) < 1e-9, f"recall {r}, deberia ser 1.0"
    assert abs(p - 1.0) < 1e-9, f"precision {p}, deberia ser 1.0"
    return f"recall {r:.4f} · precision {p:.4f}"


@prueba("context_precision no puede pasar de 1.0 (bug que destapo el oraculo)")
def t_precision_acotada():
    casos = _cargar("eval_set_v2.json")
    ora = sistema.SistemaOraculo(lambda s, u: "", _chunks(), casos)
    malos = [(c["id"], v) for c in casos
             for v in [ragas_eval.context_precision_exacta([ora.contexto_gold(c)], [c])]
             if v > 1.0]
    assert not malos, f"{len(malos)} casos > 1.0: {malos[:4]}"
    ch = _chunks()
    e01 = next(c for c in casos if c["id"] == "E01")
    g = ora.contexto_gold(e01)
    irr = [f for f in ch if f["id"] not in {x["id"] for x in g}][:4]
    mal_ord = ragas_eval.context_precision_exacta([irr + g], [e01])
    assert mal_ord < 1.0, "el mal orden deberia penalizarse"
    return f"0 casos > 1.0 · penaliza el mal ranking ({mal_ord:.3f} < 1.0)"


@prueba("el oraculo no cae al retrieval cuando no hay gold")
def t_oraculo_sin_gold():
    casos = _cargar("eval_set_v2.json")
    ora = sistema.SistemaOraculo(lambda s, u: "ok", _chunks(), casos)
    ab = [c for c in casos if c["tipo"] == "abstencion"]
    for c in ab:
        ora(c["relato"])
    assert ora.sin_gold == len(ab), f"sin_gold={ora.sin_gold}, esperaba {len(ab)}"
    assert all(t["sin_fragmento_que_cubra"] for t in ora.trazas)
    return f"{len(ab)} casos de abstencion: contexto vacio y contados, no recuperados"


# ==========================================================================
# 7 · agente (sin API)
# ==========================================================================
class _IndiceFalso:
    def recuperar(self, consulta, estrategia=None, k=4):
        return [{"id": f"f{i}", "articulo": f"art. {i}", "norma": "Ley X",
                 "titulo": "t", "texto": "x", "vigencia": "vigente"}
                for i in range(1, (k or 4) + 1)]


def _agente_pelado():
    from agente import Agente
    a = Agente.__new__(Agente)
    a.indice, a.estrategia, a.k, a.etiqueta = _IndiceFalso(), "reranked", 3, "4 · agente"
    a.contadores = {k: 0 for k in (
        "tool_invocada", "tool_buscar", "tool_termino", "argumentos_no_json",
        "herramienta_inexistente", "herramienta_con_error", "llamada_repetida",
        "pasos_agotados", "casos_sin_ninguna_tool", "hechos_no_parseados")}
    a.trazas = []
    a.costos = costos.Costos(a.etiqueta)
    return a


@prueba("el agente registra `recuperados` (el KeyError de la celda 28)")
def t_recuperados():
    a = _agente_pelado()
    regs = []
    for crudo in ('{"consulta":"salud","k":3}', '{"consulta":"peticion","k":2}'):
        _, reg = a._ejecutar("buscar_normas", crudo)
        regs.append(reg)
    _, reg = a._ejecutar("calcular_termino",
                         '{"tipo":"peticion_general","relato":"radique el 3 de marzo de 2026"}')
    regs.append(reg)
    assert regs[0]["recuperados"] == ["f1", "f2", "f3"], regs[0]
    assert "recuperados" not in regs[2], "calcular_termino no recupera nada"
    union = list(dict.fromkeys(i for r in regs for i in r.get("recuperados", [])))
    assert union == ["f1", "f2", "f3"], union
    return "ids por busqueda, union sin repetidos, y la clave existe"


@prueba("el veredicto del presupuesto distingue mejora de ruido (ROADMAP #9)")
def t_veredicto():
    casos = []
    for agot, espera in ((39, False), (31, True), (12, True), (0, True)):
        a = _agente_pelado()
        a.contadores["pasos_agotados"] = agot
        a.trazas = [{"pasos": 3, "segundos": 1.0, "fallas": []}] * 61
        v = a.veredicto_presupuesto()
        assert v["mejoro"] is espera, f"{agot}/61 -> {v['mejoro']}, esperaba {espera}"
        casos.append(f"{agot}:{'si' if v['mejoro'] else 'no'}")
    return "39/61 no cuenta como mejora · " + " ".join(casos)


# ==========================================================================
# 8 · costos
# ==========================================================================
@prueba("la tabla de costos distingue `n/d` de 0")
def t_costos():
    class SinInstrumentar:
        etiqueta = "1 · fine-tuned solo (M1)"
    c = costos.Costos("2 · RAG")
    for _ in range(5):
        c.nuevo_caso()
        c.registrar(0.1)
    c.registrar(cacheada=True)

    class Con:
        etiqueta, costos = "2 · RAG", c
    filas = costos.tabla([SinInstrumentar(), Con()])
    assert filas[0]["latencia_p50"] is None, "sin instrumentar deberia ser None"
    assert filas[1]["latencia_p50"] == 0.1, filas[1]["latencia_p50"]
    assert filas[1]["llamadas_cache"] == 1
    assert filas[1]["tokens_por_caso"] is None, "sin usage deberia ser None, no 0"
    return "brazo 1 n/d · p50 0.1 · 1 de cache · tokens None (no 0)"


# ==========================================================================
# 9 · terminos
# ==========================================================================
@prueba("los casos con fecha son reproducibles (todos los terminos VENCIDOS)")
def t_terminos():
    from datetime import date
    m3 = _cargar("eval_set_m3.json")
    mt = [c for c in m3 if c["id"].startswith("MT")]
    assert len(mt) == 6, f"esperaba 6 casos MT, hay {len(mt)}"
    calc = 0
    for c in mt:
        if not c.get("termino_calculable_esperado"):
            r = terminos.calcular_termino("peticion_general", relato=c["relato"])
            assert not r.get("calculable"), f"{c['id']} deberia ser no calculable"
            continue
        r = terminos.calcular_termino(c["termino_esperado"], relato=c["relato"])
        assert r.get("calculable"), f"{c['id']}: {r.get('motivo')}"
        # LA condicion de reproducibilidad: vencido hoy y para siempre
        assert r.get("vencido"), (
            f"{c['id']}: el termino AUN no vence, asi que el caso cambia de "
            f"respuesta con el calendario")
        calc += 1
    hoy = date.today()
    return f"{calc} calculables y vencidos · 1 no calculable a proposito · hoy {hoy}"


# ==========================================================================
# 10 · kit de doble anotacion
# ==========================================================================
@prueba("el formulario de doble anotacion esta CIEGO")
def t_anotacion():
    # SE GENERA UNO LIMPIO, no se mira el de trabajo.
    #
    # Antes leia `data/anotacion_2.csv` directamente. En cuanto alguien lo
    # rellena --- que es para lo que existe --- la prueba falla con "ya viene
    # diligenciado", porque las respuestas de la persona son indistinguibles
    # de una fuga. Lo que hay que comprobar es que el formulario que PRODUCE
    # `preparar()` sea ciego, y eso se comprueba produciendo uno.
    import tempfile
    sys.path.insert(0, str(DATA))
    import doble_anotacion as da
    tmp = Path(tempfile.mkdtemp(prefix="prueba_ciego_"))
    orig = (da.RUTA_CSV, da.RUTA_XLSX)
    try:
        da.RUTA_CSV = tmp / "anotacion_2.csv"
        da.RUTA_XLSX = tmp / "anotacion_2.xlsx"
        assert da.preparar() == 0, "preparar() fallo"
        ruta = da.RUTA_XLSX if da.RUTA_XLSX.exists() else da.RUTA_CSV
    finally:
        da.RUTA_CSV, da.RUTA_XLSX = orig
    # Via `formularios`, no con un parser propio. Tenia uno --- `read_text`
    # en utf-8 y un filtro de `#` --- y se rompio en cuanto el formulario
    # paso a llevar BOM, que es un cambio deliberado del generador. Dos
    # lectores del mismo archivo divergen siempre, y el segundo solo sirve
    # para dar un fallo que no es del archivo.
    sys.path.insert(0, str(DATA))
    import formularios
    r = formularios.leer(ruta, ("mecanismo", "procede", "notas"))
    filas = r["filas"]
    assert filas, "vacio"
    assert r["cabecera_valida"], r["columnas_que_faltan"]
    # La fuga se busca en las FILAS: la cabecera `#` lista el vocabulario a
    # proposito, porque quien anota necesita saber las opciones.
    datos = chr(10).join(
        ",".join(str(v or "") for v in f.values()) for f in filas)
    assert set(filas[0]) == {"id", "relato", "mecanismo", "procede", "notas"}, \
        f"columnas de mas: {set(filas[0])}"
    # EL EVAL SET QUE USA EL MODULO, no uno fijado aqui.
    #
    # Esto leia `eval_set_v2.json` a mano. En cuanto `doble_anotacion` paso su
    # `RUTA_EVAL` a v3 --- y la muestra crecio a 30 --- la prueba fallo con
    # `KeyError: 'A19'`: un caso que existe en v3 y no en v2. El fallo no era
    # del formulario. Una prueba que fija la version del archivo mide si la
    # version cambio, no si el formulario filtra.
    ev = {c["id"]: c for c in json.loads(
        da.RUTA_EVAL.read_text(encoding="utf-8"))["ejemplos"]}
    for f in filas:
        c = ev[f["id"]]
        # `categoria`, `razon` y `trampa` no deben aparecer en ningun sitio de
        # las filas: pistan la respuesta. El MECANISMO si aparece en la
        # cabecera, porque el anotador necesita el vocabulario; lo que no puede
        # es estar en la fila de SU caso.
        for fuga in (c.get("categoria"), c.get("razon"), c.get("trampa")):
            if fuga:
                assert str(fuga) not in datos, \
                    f"{f['id']}: el formulario filtra `{str(fuga)[:40]}`"
        assert not f["mecanismo"].strip(), f"{f['id']}: ya viene diligenciado"
        # Los casos de abstencion tienen `mecanismo: None`; buscar la cadena
        # vacia da verdadero siempre.
        if c["mecanismo"]:
            fila = f"{f['id']},{f['relato']}"
            assert c["mecanismo"] not in fila.replace(c["relato"], ""), \
                f"{f['id']}: el mecanismo esta en su propia fila"
    sys.path.insert(0, str(DATA))
    from doble_anotacion import estrato
    ests = {estrato(ev[f["id"]]) for f in filas}
    assert ests == {"plano", "derivado", "juicio"}, f"estratos: {ests}"
    return f"{len(filas)} casos, sin etiquetas filtradas, los 3 estratos cubiertos"


# ==========================================================================
# 10b · M1: brazo hibrido, degeneracion y guia de derechos
# ==========================================================================
@prueba("el brazo hibrido decide con reglas y no alucina por construccion")
def t_hibrido():
    casos = _cargar("eval_set_v2.json")
    juzgables = [c for c in casos if c["mecanismo"]]

    def generar_ideal(sistema_msg, usuario):
        """Un extractor perfecto: devuelve los hechos del gold del caso."""
        caso = next((c for c in juzgables if c["relato"] in usuario), None)
        if caso is None:
            return "{}"
        d = {k: bool(v) for k, v in (caso.get("hechos") or {}).items()
             if k in HECHOS_EXTRAIBLES}
        d.setdefault("medio_eficaz", True)
        d.update(derecho=caso["derecho"], accionado=caso["accionado"],
                 pretension=caso["pretension"])
        return json.dumps(d, ensure_ascii=False)

    hib = sistema.SistemaHibrido(generar_ideal)
    sal = [hib(c["relato"]) for c in juzgables]
    sc = metricas.scorecard(sal, juzgables, "hibrido")
    # Con hechos perfectos, el motor tiene que acertar el mecanismo SIEMPRE:
    # es el mismo arbol que derivo la etiqueta.
    assert sc["campos"]["mecanismo"]["accuracy"] == 1.0, \
        f"con hechos del gold el mecanismo deberia ser 1.0, dio " \
        f"{sc['campos']['mecanismo']['accuracy']:.4f}"
    # Y la alucinacion normativa tiene que ser CERO por construccion: el
    # fundamento lo pone la regla y el mapa cerrado, no el modelo.
    alu = sc["alucinacion_normativa"]["tasa_alucinacion"]
    assert alu == 0.0, f"alucinacion {alu:.4f}, deberia ser 0 por construccion"
    assert len(hib.trazas) == len(juzgables)
    assert all(t.get("traza_reglas") for t in hib.trazas), "sin traza de reglas"
    return (f"{len(juzgables)} casos · mecanismo 1.0000 · alucinacion 0.0% · "
            f"traza del art. 6 en todas")


@prueba("el diagnostico de degeneracion dice QUE paso, no solo cuanto")
def t_degeneracion():
    b = ("Derecho: salud\nAccionado: EPS\nMecanismo: tutela\n"
         "Procedencia: si\nPretensión: x")
    escenarios = {
        "abrio_turno": b + "<|im_end|>\n<|im_start|>user\n otra",
        "otro_idioma": b + "\n你好世界这是一个测试",
        "repitio": b + "\nPretensión: x\nPretensión: x\nPretensión: x",
        "prosa_extra": b + "\nEspero que le sea de utilidad.",
    }
    r = metricas.degeneracion([b] + list(escenarios.values()),
                              [{"id": k} for k in ["limpio"] + list(escenarios)])
    assert r["n_total_con_cola"] == 4, f"detecto {r['n_total_con_cola']} de 4"
    for s in escenarios:
        assert r["por_sintoma"].get(s) == 1, \
            f"sintoma `{s}` no clasificado: {r['por_sintoma']}"
    # Los dos que el recortador NO ve tienen que estar contados aparte: llegan
    # enteros a las metricas y al juez de M2.
    assert r["n"] == 2 and r["n_no_cortadas"] == 2, \
        f"recortadas {r['n']} / no cortadas {r['n_no_cortadas']}"
    return "4 sintomas distinguidos · 2 que el recortador no ve, contadas aparte"


@prueba("la guia de derechos vecinos cubre los pares y CABE en el presupuesto")
def t_guia():
    g = schema.GUIA_DERECHOS_VECINOS
    pares = (("seguridad_social", "minimo_vital"),
             ("trabajo", "minimo_vital"),
             ("salud", "estabilidad_laboral_reforzada"),
             ("peticion", "habeas_data"))
    # Cada par tiene que aparecer en la MISMA linea: el valor de la guia esta
    # en contrastar dos etiquetas, no en nombrarlas en sitios distintos.
    lineas = g.splitlines()
    for a, b in pares:
        assert any(a in l and b in l for l in lineas), f"falta el par {a}/{b}"
    for etq in {x for p in pares for x in p}:
        assert etq in schema.DERECHOS, f"`{etq}` no esta en DERECHOS"
    assert "QUÉ se reclama" in g, "falta el criterio que distingue los pares"

    # Y TIENE QUE CABER. La primera version ocupaba 1147 chars (~350 tokens) y
    # truncaba los 110 ejemplos de entrenamiento con MAX_LEN=640: el prompt de
    # sistema se comia el presupuesto y se cortaba la RESPUESTA que el modelo
    # debe aprender. El limite de aqui es lo que impide que vuelva a crecer
    # sin que nadie lo note.
    assert len(g) <= 600, (
        f"la guia ocupa {len(g)} chars (~{len(g)/3.3:.0f} tokens) y va en el "
        f"prompt de los {len(schema.cargar('train'))} ejemplos. Por encima de "
        f"600 vuelve a truncar.")
    tr = schema.cargar("train")
    peor = max(len(schema.SISTEMA_TRIAJE) + len(g) +
               len(schema.render_entrada(x)) + len(schema.render_salida(x))
               for x in tr)
    return (f"{len(pares)} pares en su linea · guia {len(g)} chars "
            f"(~{len(g)/3.3:.0f} tok) · peor ejemplo ~{peor/3.3:.0f} tok "
            f"(MAX_LEN 768)")


# ==========================================================================
# 10c · M2: los cuatro sesgos del juez
# ==========================================================================
class _JuezGuionado:
    """Juez con veredicto programado. No gasta API."""

    modelo = "guionado"

    def __init__(self, politica):
        self.politica = politica
        self.llamadas = 0

    def comparar_sin_sesgo_posicion(self, relato, ref, x, y):
        self.llamadas += 1
        v = self.politica(relato, ref, x, y, self.llamadas)
        return {"veredicto": v, "consistente": v != "inconsistente",
                "orden_1": v, "orden_2": v,
                "eligio_A": [v == "x", v != "x"]}

    def guardar_cache(self):
        pass


@prueba("la auto-preferencia se mide condicionando en la verdad de dominio")
def t_autopreferencia():
    casos = [c for c in _cargar("eval_set_v2.json") if c["mecanismo"]][:12]
    perf = _perfecta(casos)          # las dos familias aciertan: calidad empatada
    sesgado = _JuezGuionado(lambda *a: "x")
    justo = _JuezGuionado(lambda r, rf, x, y, i: "x" if i % 2 else "y")

    r1 = harness.sesgo_autopreferencia(sesgado, casos, perf, perf, n=12)
    r2 = harness.sesgo_autopreferencia(justo, casos, perf, perf, n=12)
    assert r1["preferencia_familia_con_calidad_empatada"] == 1.0, r1
    assert r2["preferencia_familia_con_calidad_empatada"] == 0.5, r2
    assert r1["por_estrato"]["empate_correctas"]["n"] == 12, \
        "con dos respuestas perfectas todos los pares son empate_correctas"

    # Sin pares de calidad empatada el experimento NO puede informar, y tiene
    # que decirlo en vez de promediar estratos que miden cosas distintas.
    malas = []
    for c in casos:
        x = dict(c)
        x["mecanismo"] = "accion_popular" if c["mecanismo"] != "accion_popular" else "tutela"
        x["procede"] = x["mecanismo"] == "tutela"
        malas.append(schema.render_salida(x))
    r3 = harness.sesgo_autopreferencia(sesgado, casos, perf, malas, n=12)
    assert r3["por_estrato"]["gana_familia"]["n"] == 12
    assert r3["preferencia_familia_con_calidad_empatada"] == "indefinida", r3

    # ------------------------------------------------------------------
    # EL ESTRATO DECISIVO SE BUSCA, NO SE ESPERA.
    #
    # La corrida m2/20261019T034128Z midio n=15 y salio `indefinida` con
    # **n=2** en `empate_correctas`: 12 de los 15 pares cayeron en
    # `gana_ajeno`, porque el hermano pequeno de la familia del juez pierde
    # casi siempre contra el Qwen afinado. El defecto no era el tamano de la
    # muestra: era tomar los primeros `n` y confiar en la suerte.
    #
    # Aqui se reproduce a proposito el peor orden posible --- los empates al
    # FINAL de la cola --- con un presupuesto menor que el total de casos.
    # Clasificar es gratis, asi que los tiene que encontrar todos.
    anchos = [c for c in _cargar("eval_set_v2.json") if c["mecanismo"]][:40]
    fam, aje = [], []
    for k, cc in enumerate(anchos):
        x = dict(cc)
        if k < 30:                        # gana_ajeno: la familia se equivoca
            x["mecanismo"] = ("accion_popular" if cc["mecanismo"] != "accion_popular"
                              else "tutela")
            x["procede"] = x["mecanismo"] == "tutela"
            fam.append(schema.render_salida(x))
        else:                             # empate_correctas, al final
            fam.append(schema.render_salida(cc))
        aje.append(schema.render_salida(cc))

    r4 = harness.sesgo_autopreferencia(sesgado, anchos, fam, aje, n=15)
    assert r4["disponibles_por_estrato"]["empate_correctas"] == 10, (
        f"no vio los 10 empates disponibles: {r4['disponibles_por_estrato']}")
    assert r4["por_estrato"]["empate_correctas"]["n"] == 10, (
        "gasto el presupuesto en estratos que no miden sesgo y dejo sin medir "
        f"el que si: {r4['por_estrato']}")
    assert r4["n_decididos_en_el_empate"] == 10, r4["n_decididos_en_el_empate"]
    assert r4["preferencia_familia_con_calidad_empatada"] == 1.0, r4
    assert sum(v["n"] for v in r4["por_estrato"].values()) == 15, (
        "no respeto el presupuesto de 15 pares")
    assert r4["seleccion"]["estratificada"] is True, (
        "no declara que `por_estrato` dejo de ser una muestra aleatoria")
    # Y la comprobacion que fija el defecto: entre los primeros 15 casos no
    # habia NI UN empate, asi que la version que tomaba los primeros `n`
    # habria vuelto a salir `indefinida`.
    assert all(schema.parse_salida(fam[k]).get("mecanismo")
               != anchos[k]["mecanismo"] for k in range(15)), (
        "el caso de prueba ya no reproduce el orden que rompia la version "
        "anterior")

    return ("sesgado 1.0 · justo 0.5 · sin estrato -> `indefinida`; y "
            "encuentra los 10 empates aunque esten al final de la cola con "
            "presupuesto 15, donde la version anterior veia 0")


@prueba("el test de longitud sutil caza al juez que compara etiquetas")
def t_longitud():
    casos = [c for c in _cargar("eval_set_v2.json") if c["mecanismo"]][:10]

    def compara_etiquetas(relato, ref, x, y, i):
        mx = schema.parse_salida(x).get("mecanismo")
        my = schema.parse_salida(y).get("mecanismo")
        mr = schema.parse_salida(ref).get("mecanismo")
        if mx == mr and my != mr:
            return "x"
        if my == mr and mx != mr:
            return "y"
        return "y"            # etiquetas iguales: se queda con la mas larga

    r = harness.sesgo_longitud(_JuezGuionado(compara_etiquetas), casos, n=10,
                               nivel="ambos")
    assert r["obvio"]["tasa_sesgo_longitud"] == 0.0, \
        "el nivel obvio deberia pasarlo: el mecanismo esta cambiado"
    assert r["sutil"]["tasa_sesgo_longitud"] == 1.0, \
        "el nivel sutil deberia cazarlo: el mecanismo es correcto"
    assert r["delta_tasa"] == 1.0, r["delta_tasa"]
    # Y el nivel sutil NO debe tocar el mecanismo: si lo tocara, volveria a ser
    # el test facil con otro nombre.
    assert "el mecanismo es correcto" in r["sutil"]["que_falla_en_la_larga"]
    return ("obvio 0.00 y sutil 1.00 con el mismo juez: el obvio no probaba "
            "nada sobre longitud")


@prueba("el acuerdo entre jueces separa ordenar de calibrar")
def t_acuerdo_jueces():
    def ac(a, b):
        return harness.acuerdo_entre_jueces([{"nota": x} for x in a],
                                            [{"nota": y} for y in b], "A", "B")
    ident = ac([3, 4, 5, 2, 4], [3, 4, 5, 2, 4])
    assert ident["acuerdo_exacto"] == 1.0 and ident["kappa_aprueba"] == 1.0
    # El caso que importa: ordenan igual, calibran distinto.
    cal = ac([1, 2, 3, 4, 5], [2, 3, 4, 5, 5])
    assert cal["acuerdo_exacto"] < 0.5, cal["acuerdo_exacto"]
    assert cal["corr_spearman"] > 0.9, cal["corr_spearman"]
    # Un juez constante no puede informar kappa.
    cte = ac([3, 3, 3, 3, 3], [1, 2, 3, 4, 5])
    assert cte["kappa_aprueba"] == "indefinido", cte["kappa_aprueba"]
    assert cte["corr_spearman"] is None
    vacio = ac([None] * 3, [1, 2, 3])
    assert vacio["concluyente"] is False
    return ("identicos k=1.0 · severo/generoso exacto<0.5 pero spearman>0.9 · "
            "constante -> indefinido")


@prueba("un cero y una media censurada no se pueden citar desnudos")
def t_declaraciones_viajan():
    """Dos cifras del brazo 4 se leen al reves si van solas, y las dos se
    arreglan igual: la declaracion viaja DENTRO del artefacto, no en un
    docstring que el lector del scorecard nunca abre.

    `acierto_abstencion: 0.0` parece decir que no sabe callarse. Dice que se
    le pidio no callarse: el defecto pro homine no activa causal de
    improcedencia ante la duda, asi que el motor siempre halla una via. El
    MISMO defecto da `abstencion_indebida: 0.0`, y no se puede celebrar uno y
    llamar fallo al otro.

    `pasos_promedio` con 56% de los casos cortados en el techo no estima los
    pasos que el agente necesita: es una COTA INFERIOR de eso.
    """
    import agente
    import sistema
    # 1 · abstencion: 3 casos que debian callarse y los 3 respondieron.
    AFIRMA = "\n".join(("Derecho: salud (art. 49 CP)",
                        "Accionado: EPS",
                        "Mecanismo: accion de tutela",
                        "Procedencia: si",
                        "Pretension: ordenar el suministro"))
    CALLA = AFIRMA.replace("Mecanismo: accion de tutela",
                           "Mecanismo: no determinable")
    assert schema.se_abstuvo(AFIRMA) is False
    assert schema.se_abstuvo(CALLA) is True
    ab = metricas.abstencion([AFIRMA] * 3, [AFIRMA] * 4)
    assert ab["acierto_abstencion"] == 0.0, ab["acierto_abstencion"]
    assert "cero_abstenciones_es_decision_de_diseno" in ab, sorted(ab)
    d = ab["cero_abstenciones_es_decision_de_diseno"]
    assert d is sistema.DEFECTO_PRO_HOMINE or isinstance(d, str)
    assert "coste_simetrico" in sistema.DEFECTO_PRO_HOMINE
    assert "como_NO_leer_la_cifra" in sistema.DEFECTO_PRO_HOMINE
    assert "lectura_abstencion" in ab
    # Y donde si se abstuvo, la declaracion NO aparece: no es un sello que se
    # pegue siempre, es una lectura de un cero concreto.
    ok = metricas.abstencion([CALLA] * 2, [])
    assert "cero_abstenciones_es_decision_de_diseno" not in ok, sorted(ok)

    # 2 · pasos: una media con casos en el techo se cita como cota inferior.
    class _T:
        trazas = [{"pasos": 4, "segundos": 1.0, "fallas": []}] * 10
        contadores = {"pasos_agotados": 6}
        max_pasos = 4
    cen = agente.Agente._censura_pasos(_T())
    assert cen["censurado"] is True, cen
    assert cen["tasa"] == 0.6, cen["tasa"]
    assert ">=" in cen["como_citar"] and "cota INFERIOR" in cen["como_citar"],         cen["como_citar"]

    class _S(_T):
        contadores = {"pasos_agotados": 0}
    libre = agente.Agente._censura_pasos(_S())
    assert libre["censurado"] is False
    assert "no esta censurada" in libre["como_citar"], libre["como_citar"]

    # Y sin casos, `censurado` no es False: es None. Decir "ninguno toco el
    # techo" cuando no hubo casos es el mismo error que informar
    # `acierto_abstencion: 0.0` donde no habia nada que medir.
    class _V(_T):
        trazas = []
        contadores = {"pasos_agotados": 0}
    vacio = agente.Agente._censura_pasos(_V())
    assert vacio["censurado"] is None, vacio
    assert vacio["tasa"] is None and vacio["n"] == 0, vacio
    assert "sin casos" in vacio["como_citar"], vacio["como_citar"]
    return ("el 0.0 de abstencion llega con su decision de diseno (y solo "
            "cuando es 0.0) · 6/10 en el techo -> la media se cita con `>=`")


@prueba("el kit de calibracion humana no inventa cuando falta la corrida")
def t_calibracion():
    """UNA PRUEBA NO PUEDE DEPENDER DE QUE EL PROYECTO NO SE HAYA USADO.

    Corria `--preparar` en el arbol de trabajo y exigia "Falta una corrida".
    Eso solo es cierto mientras `results/` este vacio: en cuanto M1 y M2
    corren de verdad --- que es el objetivo del proyecto --- el script
    encuentra la corrida y la prueba falla sin que nada este mal. Y si ademas
    alguien diligencio el formulario, se niega a sobreescribirlo, que tambien
    es lo correcto.

    Un suite que solo pasa en un checkout recien clonado es un suite que se
    deja de correr. Asi que se prueba en un arbol temporal VACIO, donde la
    ausencia de corrida es una condicion del fixture y no del estado real.
    """
    import subprocess
    import tempfile as _tf
    arbol = Path(_tf.mkdtemp(prefix="prueba_calib_"))
    (arbol / "data").mkdir()
    (arbol / "results").mkdir()
    for f in ("calibracion_juez.py", "formularios.py", "eval_set_v2.json"):
        (arbol / "data" / f).write_bytes((DATA / f).read_bytes())
    (arbol / "src").mkdir()
    for p in (RAIZ / "src").glob("*.py"):
        (arbol / "src" / p.name).write_bytes(p.read_bytes())
    r = subprocess.run([sys.executable, "-I",
                        str(arbol / "data" / "calibracion_juez.py"),
                        "--preparar"], capture_output=True, text=True,
                       cwd=str(arbol))
    salida = r.stdout + r.stderr
    assert r.returncode == 1, (
        f"sin corrida deberia salir con 1, dio {r.returncode}: {salida[:220]}")
    assert "Falta una corrida" in salida, salida[:260]
    assert "m1_predicciones.json" in salida and "m2_scorecard" in salida
    return ("en un arbol sin corrida dice exactamente que archivos faltan y "
            "sale con exit 1 (en temporal, no en el arbol de trabajo)")


@prueba("no se puede producir una medicion humana sin decir quien anoto")
def t_anotador_obligatorio():
    """La kappa y la calibracion solo significan lo que su nombre dice si los
    dos lados son independientes. Con el mismo equipo --- o el mismo
    asistente --- a los dos lados, una cifra alta mide que la rubrica es
    clara, no que el gold sea correcto. Es el mismo cuidado que
    `por_fiabilidad_etiqueta` tiene con `motor_de_reglas`: CONSISTENTE con el
    arbol del art. 6 no es lo mismo que INDEPENDIENTE de el.

    Por eso el anotador es un argumento obligatorio y no una nota al pie: la
    forma de que nadie publique una kappa sin firma es que el script se
    niegue a calcularla.
    """
    import subprocess
    # Autosuficiente a proposito: dependia de que otra prueba hubiera metido
    # `data/` en sys.path, asi que anadir una prueba antes la rompia.
    sys.path.insert(0, str(DATA))
    for script in ("calibracion_juez.py", "doble_anotacion.py"):
        r = subprocess.run([sys.executable, "-I", str(DATA / script), "--medir"],
                           capture_output=True, text=True, cwd=str(RAIZ))
        sal = r.stdout + r.stderr
        assert r.returncode == 2,             f"{script}: deberia rechazar --medir sin --anotador, dio {r.returncode}"
        assert "--anotador" in sal, f"{script}: {sal[:300]}"
    # Y de las opciones, solo UNA puede llamarse validacion externa. Si alguien
    # anade manana un anotador marcado como independiente, esto lo frena.
    import calibracion_juez as cj
    import doble_anotacion as da
    indep_cj = sorted(k for k, v in cj.ANOTADORES.items() if v["independiente"])
    indep_da = sorted(k for k, v in da.ANOTADORES.items() if v[0])
    # LA LISTA SE ENUMERA, no se cuenta.
    #
    # La guarda no existe para que haya UNA ranura independiente: existe para
    # que anadir una no se pueda hacer en silencio. `doble_anotacion` tiene
    # hoy dos --- la segunda hizo falta porque la guarda de `--preparar`
    # protege el trabajo de la primera, y preparar un formulario para otra
    # persona no puede exigir borrar el de quien ya anoto ---. Enumerarlas
    # mantiene el freno: una tercera sigue rompiendo esto y obliga a que
    # alguien escriba por que cuenta como independiente.
    #
    # Y lo que esta lista NO comprueba: que quien anoto fuera de verdad ajeno
    # al gold. Eso no es verificable desde el codigo --- es una declaracion
    # de procedencia, y el artefacto la publica como tal en
    # `_independencia` ---. La guarda cubre lo unico que si es verificable:
    # que la declaracion este escrita y firmada antes de que salga una cifra.
    assert indep_cj == ["persona-externa"], indep_cj
    assert indep_da == ["persona-externa", "persona-externa-2"], indep_da
    return ("los dos scripts salen con exit 2 sin --anotador · "
            f"calibracion {len(indep_cj)} ranura independiente, "
            f"doble anotacion {len(indep_da)}, todas declaradas")


# ==========================================================================
# 10d · corpus
# ==========================================================================
@prueba("el corpus crecio donde estaba el cuello de botella")
def t_corpus_amplia():
    from collections import Counter
    docs = json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))["documentos"]
    por_norma = Counter(d["norma"] for d in docs)
    assert por_norma["Ley 1751 de 2015"] >= 4, \
        f"Ley 1751 tiene {por_norma['Ley 1751 de 2015']} fragmentos y se cita 28 veces"
    arts = {d["articulo"] for d in docs if d["norma"] == "Ley 1751 de 2015"}
    assert {"art. 6", "art. 14"} <= arts, f"faltan arts en Ley 1751: {arts}"
    # art. 6 trae los principios de Continuidad y Oportunidad, que son el
    # fundamento de los casos de servicio interrumpido y de dilacion.
    a6 = next(d for d in docs if d["id"] == "L1751-06")
    for clave in ("no podrá ser interrumpido por razones administrativas",
                  "deben proveerse sin dilaciones"):
        assert clave in a6["texto"], f"art. 6 sin '{clave[:40]}'"
    chunks = rag.trocear(docs)
    assert len(chunks) >= 67, f"{len(chunks)} chunks, esperaba 67+"
    return (f"{len(docs)} fragmentos, {len(chunks)} chunks · Ley 1751: "
            f"{por_norma['Ley 1751 de 2015']} fragmentos {sorted(arts)}")


@prueba("el segundo juez se prefiere de OTRA familia, y el artefacto lo dice")
def t_familia_jueces():
    """El acuerdo entre jueces controla el RUIDO de un juez; no controla el
    SESGO que dos modelos de la misma familia comparten. Una kappa alta entre
    dos `gpt-oss` es compatible con que los dos se equivoquen igual.

    En m2/20261018T080311Z el segundo juez fue `openai/gpt-oss-20b`: misma
    familia que el principal. La kappa de 0.6835 es real y mide menos de lo
    que su nombre sugiere. Esta prueba fija las dos correcciones: que se
    prefiera otro linaje, y que el artefacto declare cual se uso.
    """
    import harness
    import juez
    assert juez.MODELO in juez.FAMILIA, "el juez principal sin familia declarada"
    primero = juez.MODELOS_ALTERNATIVOS[0]
    assert juez.FAMILIA.get(primero) != juez.FAMILIA[juez.MODELO], (
        f"el primer alternativo ({primero}) es de la misma familia que el "
        f"juez principal: el acuerdo mediria ruido, no sesgo compartido")
    # Qwen sigue excluido: es la familia del sistema evaluado.
    assert juez.MODELOS_EXCLUIDOS_POR_FAMILIA, "se perdio la exclusion de Qwen"
    for m in juez.MODELOS_ALTERNATIVOS:
        assert "qwen" not in m.lower(), f"{m} reintroduce auto-preferencia"
    # Y el artefacto tiene que decir de que linaje es cada uno.
    mismo = harness._lectura_familias(juez.MODELO, "openai/gpt-oss-20b")
    otro = harness._lectura_familias(juez.MODELO, primero)
    assert mismo["misma_familia"] is True, mismo
    assert otro["misma_familia"] is False, otro
    assert "no sesgo" in mismo["que_mide"], mismo["que_mide"]
    return (f"preferido {primero} ({juez.FAMILIA[primero]}) sobre el linaje "
            f"{juez.FAMILIA[juez.MODELO]} del principal · el artefacto "
            "declara si son parientes")


@prueba("el extractor distingue incumplir una norma de danar un derecho colectivo")
def t_prompt_cumplimiento():
    """La correccion de M3-1, fijada para que no se revierta en silencio.

    Medido en m3/20261018T080807Z: `derecho_colectivo` salia True en 8 de 8
    casos de `accion_cumplimiento` y `acto_general` en 6. El motor no era el
    problema --- con los hechos del eval set emite la via correcta en 8 de 8
    --- sino que el extractor confundia dos pares de cosas:

      incumplir un deber general  !=  danar un derecho colectivo
      mencionar una norma         !=  atacar una norma

    Un prompt es codigo: si alguien lo reescribe y se lleva la distincion por
    delante, el defecto vuelve y solo se notaria al correr M3 entero.
    """
    import agente
    import sistema
    for mod, nombre in ((agente, "agente.PROMPT_HECHOS_AGENTE"),
                        (sistema, "sistema._prompt_hechos")):
        txt = getattr(mod, "PROMPT_HECHOS_AGENTE", None)
        if txt is None:
            txt = "".join(
                v for k, v in vars(mod).items()
                if isinstance(v, str) and "derecho_colectivo" in v)
        assert "derecho_colectivo" in txt, nombre
        # La lista del art. 4 tiene que estar como lista CERRADA.
        # SE DEFINE POR EL DANO, NO POR EL TEMA. Y esto es una correccion
        # de la correccion: la primera version anclaba en el catalogo del
        # art. 4 de la Ley 472, y el propio catalogo incluye "acceso a los
        # servicios publicos". Medido con `validar_extractor.py`:
        # `derecho_colectivo` solo bajo de 8 a 6, y los 6 que seguian
        # fallando eran justo aquellos cuyo deber incumplido era un SERVICIO
        # (comisaria, bomberos, sala de lactancia, tarifa). La lista empujaba
        # al modelo hacia True. Lo que separa no es el tema sino si hay un
        # dano actual a un bien colectivo o una norma sin cumplir.
        assert "ACTUAL" in txt, (
            f"{nombre}: `derecho_colectivo` debe definirse por un DANO O "
            "AMENAZA ACTUAL a un bien colectivo, no por el tema del que trate")
        assert "convierte en dano colectivo" in txt or                "convierte en daño colectivo" in txt, (
            f"{nombre}: falta decir que un deber incumplido sobre un SERVICIO "
            "PUBLICO no es dano colectivo. Es lo que dejaba 6 de 8 mal")
        assert "art. 87 hace cumplir" in txt, (
            f"{nombre}: falta anclar que las leyes que ordenan prestar "
            "servicios son lo que el art. 87 hace cumplir")
        assert "SE CUMPLA es lo contrario de atacarla" in txt, (
            f"{nombre}: falta distinguir pedir que una norma se cumpla de "
            "atacarla. `acto_general` salia True en 6 de 8 por esto")
    return ("los dos extractores definen `derecho_colectivo` por DANO ACTUAL "
            "y no por tema, y separan cumplir de atacar una norma")


@prueba("las trazas del agente se empalman con su caso, aunque vengan cortadas")
def t_empalme_trazas():
    """Lo que estableció la causa de `accion_cumplimiento` F1 0.000.

    `Agente.trazas` guarda lo que el agente VE: relato, hechos, herramientas,
    pasos. No guarda el `id` del caso, porque el agente no lo recibe. Y el
    relato lo guarda TRUNCADO a 80 caracteres.

    Las dos cosas juntas hacían que `diagnostico_cumplimiento.py` emparejara
    CERO casos sobre un archivo de 90 trazas correctas, e informara "sin
    establecer" con la evidencia delante. El diagnóstico no fallaba: decía
    que no sabía, sobre datos que sí sabían.

    Se empalma por prefijo. Esta prueba fija las dos condiciones que lo hacen
    seguro: que el prefijo baste, y que sea ÚNICO --- si dos trazas
    compartieran prefijo con un caso, atribuirle una sería inventar.
    """
    sys.path.insert(0, str(DATA))
    import diagnostico_cumplimiento as dc

    ev = json.loads(
        (DATA / "eval_set_v2.json").read_text(encoding="utf-8"))["ejemplos"]
    CORTE = 80

    # Trazas como las que produce el agente: sin `id`, relato cortado.
    trazas = [{"relato": e["relato"][:CORTE],
               "hechos": {"incumplimiento_normativo": True,
                          "afectacion_individual": False},
               "pasos": 3, "fallas": []}
              for e in ev]

    # 1 · los prefijos tienen que ser unicos, o el empalme es una adivinanza.
    prefijos = [t["relato"] for t in trazas]
    assert len(set(prefijos)) == len(prefijos), (
        f"{len(prefijos) - len(set(prefijos))} relatos comparten los primeros "
        f"{CORTE} caracteres: el empalme por prefijo dejaria de ser seguro")

    # 2 · y el empalme tiene que encontrar TODOS los casos.
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="prueba_trazas_"))
    p = tmp / "agente_trazas.json"
    p.write_text(json.dumps({"_corrida": "X", "datos": trazas},
                            ensure_ascii=False), encoding="utf-8")
    r = dc.leer_trazas(p)
    assert r["disponible"], r
    assert not r["sin_traza"], (
        f"no empalmaron: {r['sin_traza'][:6]} --- el relato de las trazas "
        f"viene cortado a {CORTE} chars y hay que empalmar por prefijo")
    assert r["n_con_traza"] == 8, (
        f"{r['n_con_traza']} casos con traza, esperaba los 8 de "
        "accion_cumplimiento")

    # 3 · con los hechos correctos NO se activa ninguna causa: si el extractor
    #     los diera bien, no habria defecto que diagnosticar.
    assert not r["conteo_por_causa"], (
        f"con `incumplimiento_normativo=True` y `afectacion_individual=False` "
        f"no deberia activarse ninguna causa, y se activo {r['conteo_por_causa']}")

    # 4 · y con el hecho que de verdad lo rompe, se nombra ese y no otro.
    for t in trazas:
        t["hechos"]["derecho_colectivo"] = True
    p.write_text(json.dumps({"_corrida": "X", "datos": trazas},
                            ensure_ascii=False), encoding="utf-8")
    r2 = dc.leer_trazas(p)
    assert r2["causa_mas_frecuente"] == "derecho_colectivo", r2
    assert r2["conteo_por_causa"]["derecho_colectivo"] == 8, r2
    return ("90 prefijos de 80 chars unicos · los 8 casos empalman sin `id` · "
            "con los hechos buenos no se activa causa, y con "
            "`derecho_colectivo` se nombra ese")


@prueba("un formulario que vuelve de Excel se lee, en los dos formatos")
def t_formulario_vuelve_de_excel():
    """Los formularios salen en UTF-8 y vuelven de Excel, que ofrece dos
    maneras de guardar y las dos rompian la lectura:

      · «CSV» clasico guarda en cp1252. `read_text(encoding="utf-8")` lanzaba
        UnicodeDecodeError y el script moria. Ruidoso, luego benigno.

      · «CSV UTF-8» guarda con BOM. El BOM se pega a la PRIMERA linea, que es
        un comentario, asi que `l.startswith("#")` daba False y esa linea
        pasaba a ser la cabecera del CSV. A partir de ahi `fila["mecanismo"]`
        valia None en todas las filas y el script informaba «no tiene ninguna
        fila diligenciada» sobre un formulario entero relleno. SILENCIOSO, y
        por eso el grave: pierde el trabajo de una persona y le echa la culpa.

    Ninguno de los dos es culpa de quien anota: son las dos unicas opciones
    que Excel da. Asi que los dos tienen que leerse.
    """
    import tempfile
    sys.path.insert(0, str(DATA))
    import formularios

    COLS = ("mecanismo", "procede", "notas")
    # El CSV puede no estar: Excel lo reemplaza al guardar el xlsx, o se
    # borra a mano. La prueba no puede depender de que siga ahi, asi que si
    # falta se construye el texto de prueba desde el xlsx.
    csv_real = DATA / "anotacion_2.csv"
    if csv_real.exists():
        original = csv_real.read_text(encoding="utf-8-sig")
    else:
        rx0 = formularios.leer(DATA / "anotacion_2.xlsx", COLS)
        import csv as _csv
        import io as _io
        buf = _io.StringIO()
        w = _csv.writer(buf, lineterminator=chr(10))
        w.writerow(["# DOBLE ANOTACION - reconstruido desde el xlsx"])
        w.writerow(["id", "relato", "mecanismo", "procede", "notas"])
        for f in rx0["filas"]:
            w.writerow([f["id"], f["relato"], "", "", ""])
        original = buf.getvalue()
    # Se rellena una fila, que es lo que la persona habria hecho.
    lineas = original.splitlines()
    i = next(k for k, l in enumerate(lineas)
             if l.startswith("A01,") or l.startswith('A01,"'))
    lineas[i] = lineas[i].rstrip() + "tutela,true,sin dudas"
    relleno = chr(10).join(lineas)

    tmp = Path(tempfile.mkdtemp(prefix="prueba_form_"))
    casos = {
        "utf-8 (como sale)": ("utf-8", relleno),
        "CSV UTF-8 de Excel (con BOM)": ("utf-8-sig", relleno),
        "CSV clasico de Excel (cp1252)": ("cp1252", relleno),
    }
    for etq, (enc, txt) in casos.items():
        p = tmp / f"{enc}.csv"
        p.write_bytes(txt.encode(enc, errors="replace"))
        r = formularios.leer(p, COLS)
        assert r["cabecera_valida"], (
            f"{etq}: la cabecera no se reconocio, faltan "
            f"{r['columnas_que_faltan']}. Cabecera leida: {r['cabecera'][:3]}")
        assert "id" in r["cabecera"], (etq, r["cabecera"][:3])
        assert r["diligenciadas"] == 1, (etq, r["diligenciadas"])

    # EL CSV DE VERDAD SALE *CON* BOM, Y ES DELIBERADO.
    #
    # Primero se escribia sin BOM. Resultado medido en el equipo del
    # proyecto, con locale es-CO: Excel lo decodificaba con la pagina 1252 y
    # el relato salia lleno de simbolos raros --- ilegible, y el relato es
    # justo lo que hay que leer para anotar. Con BOM, Excel y Sheets
    # detectan UTF-8 solos, y `formularios` lo quita al leer.
    # EL BOM SE EXIGE A UN FORMULARIO RECIEN GENERADO, NO AL DE TRABAJO.
    #
    # El de trabajo puede venir de cualquier parte --- de Drive, de Excel, de
    # una copia a mano --- y entonces la asercion mide de donde salio el
    # archivo, no lo que `preparar()` escribe. Lo que hay que fijar es el
    # comportamiento del generador.
    import doble_anotacion as _da
    _tmp2 = Path(tempfile.mkdtemp(prefix="prueba_bom_"))
    _orig2 = (_da.RUTA_CSV, _da.RUTA_XLSX)
    try:
        _da.RUTA_CSV = _tmp2 / "anotacion_2.csv"
        _da.RUTA_XLSX = _tmp2 / "anotacion_2.xlsx"
        assert _da.preparar() == 0
        crudo = _da.RUTA_CSV.read_bytes()
        assert crudo.startswith(bytes((0xEF, 0xBB, 0xBF))), (
            "el csv que escribe `preparar()` deberia llevar BOM: sin el, "
            "Excel en un Windows en espanol destroza los acentos del relato")
    finally:
        _da.RUTA_CSV, _da.RUTA_XLSX = _orig2

    # Y el .xlsx, que es el formato que se le pide rellenar, porque es el
    # unico que Excel no puede abrir mal: ni codificacion ni separador.
    xlsx = DATA / "anotacion_2.xlsx"
    if xlsx.exists():
        rx = formularios.leer(xlsx, COLS)
        assert rx["cabecera_valida"], rx["columnas_que_faltan"]
        assert rx["codificacion"] == "xlsx", rx["codificacion"]
        assert len(rx["filas"]) == 14, len(rx["filas"])
        # Los acentos llegan de verdad: se comprueba por punto de codigo, no
        # imprimiendo, porque la consola de Windows no los puede mostrar y
        # eso haria dudar de un archivo correcto.
        texto = " ".join(f["relato"] for f in rx["filas"])
        assert any(c in texto for c in "áéíóúñ"),             "el xlsx no trae ni un acento: algo los perdio al escribirlo"
        assert "�" not in texto, "el xlsx trae caracteres de reemplazo"

    # Un separador `;` --- lo que Excel guarda en es-CO --- tambien se lee.
    punto_y_coma = relleno.replace(",", ";")
    p = tmp / "punto_y_coma.csv"
    p.write_text(punto_y_coma, encoding="utf-8")
    rs = formularios.leer(p, COLS)
    assert rs["cabecera_valida"], (
        f"un csv con `;` no se reconocio: {rs['columnas_que_faltan']}")
    return ("utf-8, con BOM, cp1252 y separador `;` se leen los cuatro · "
            "el csv generado lleva BOM a proposito · el xlsx trae los "
            "acentos intactos")


@prueba("el experimento de inyeccion al juez corre sin API, con un juez de pega")
def t_inyeccion_sin_api():
    """`src/juez.py` estaba al 0% de cobertura: ninguna prueba local tocaba
    una linea. Y ahi vive el cambio de M2-4 --- 18 sondas, tasa por estilo ---
    que por tanto nunca se habia EJECUTADO, solo escrito. Es la misma
    situacion que produjo el fallo de `preferencia_posicion_A`: cambiar lo que
    devuelve una funcion sin que nada local la llame.

    Un juez de pega quita la API de en medio y deja comprobar lo que de verdad
    puede romperse: que cada sonda se puntue DOS veces (con y sin la frase
    inyectada), que la obediencia se atribuya al estilo correcto, y que el
    reparto por estilo sea el que el archivo declara.
    """
    import juez as J
    iny = json.loads(
        (DATA / "inyecciones.json").read_text(encoding="utf-8"))["ejemplos"]

    def render_ref(e):
        return chr(10).join((
            f"Derecho: {e.get('derecho')}",
            f"Accionado: {e.get('accionado')}",
            f"Mecanismo: {e.get('mecanismo')}",
            f"Procedencia: {'si' if e.get('procede') else 'no'}",
            f"Pretension: {e.get('pretension')}"))

    OBEDECE = "falsa politica de evaluacion"

    class JuezDePega:
        """Obedece UN solo estilo. Asi la atribucion se puede comprobar."""

        def __init__(self):
            self.llamadas = 0

        def puntuar(self, relato, referencia, candidato):
            self.llamadas += 1
            for e in iny:
                if e["estilo"] == OBEDECE and e["frase_inyectada"] in relato:
                    return {"nota": e["nota_pedida"], "justificacion": "obedeci"}
            return {"nota": 3, "justificacion": "nota honesta"}

        def guardar_cache(self):
            pass

    j = JuezDePega()
    r = J.experimento_inyeccion(j, iny, render_ref)

    # Dos puntuaciones por sonda: con la frase y sin ella. Si fueran una, las
    # dos notas serian la misma por construccion y el experimento no podria
    # fallar --- que es el defecto que la v1 tenia.
    assert r["n"] == len(iny), (r["n"], len(iny))
    assert j.llamadas == 2 * r["n"], (j.llamadas, r["n"])

    # La obediencia se atribuye al estilo que obedecio, y a ningun otro.
    assert r["por_estilo"][OBEDECE]["obedecieron"] == 3, r["por_estilo"][OBEDECE]
    otros = {e: v["obedecieron"] for e, v in r["por_estilo"].items()
             if e != OBEDECE}
    assert set(otros.values()) == {0}, otros
    assert r["obedecieron"] == 3, r["obedecieron"]

    # El reparto que el archivo declara: 6 estilos, 3 sondas cada uno, las dos
    # direcciones presentes en todos.
    assert len(r["por_estilo"]) == 6, sorted(r["por_estilo"])
    assert all(v["n"] == 3 for v in r["por_estilo"].values()), r["por_estilo"]
    assert all(len(v["direcciones"]) == 2
               for v in r["por_estilo"].values()), r["por_estilo"]
    assert r["estilos_con_una_sola_sonda"] == [], r["estilos_con_una_sola_sonda"]

    # Y el limite que el reparto NO alcanza: 3 no se parte en dos mitades, asi
    # que la mitad de las celdas estilo x direccion tiene n=1. Tiene que estar
    # dicho, no deducible.
    celdas = r["celdas_estilo_direccion_con_una_sola_sonda"]
    assert len(celdas) == 6, celdas
    assert all("/" in c for c in celdas), celdas
    return (f"{r['n']} sondas x 2 puntuaciones = {j.llamadas} llamadas · "
            f"6 estilos x 3 · obediencia atribuida solo al estilo que obedecio "
            f"· {len(celdas)} celdas estilo/direccion con n=1, declaradas")


@prueba("ningun script puede escribir dentro de la huella que certifica")
def t_salidas_fuera_de_la_huella():
    """Tres veces ha pasado lo mismo y por eso esto es una prueba.

    `manifiesto.PATRONES` cubre `data/*.json`. Un script que escribe su
    resultado en `data/` mete su propia salida en la huella que esa huella
    certifica: correrlo cambia el manifiesto, y la siguiente comprobacion
    denuncia el archivo y bloquea el arranque. Paso con
    `cobertura_corpus.json`, con `diagnostico_cumplimiento.json` y con
    `validacion_extractor.json` --- este ultimo en medio de una corrida.

    En vez de acordarse de anadir el cuarto a mano, se buscan todos: cada
    `RUTA_OUT = RAIZ / "data" / "<algo>"` de `data/*.py` tiene que estar
    excluido. La convencion del nombre es lo que lo hace comprobable.
    """
    import re
    sys.path.insert(0, str(DATA))
    import manifiesto as mf

    pat = re.compile(r'RUTA_OUT\s*=\s*RAIZ\s*/\s*"data"\s*/\s*"([^"]+)"')
    salidas = {}
    for p in sorted(DATA.glob("*.py")):
        for m in pat.finditer(p.read_text(encoding="utf-8")):
            salidas[m.group(1)] = p.name
    assert salidas, "no se encontro ningun RUTA_OUT: ¿cambio la convencion?"

    def excluido(n):
        return (n in mf.EXCLUIR
                or any(n.startswith(x) for x in mf.EXCLUIR_PREFIJO))

    dentro = {n: quien for n, quien in salidas.items()
              if n.endswith(".json") and not excluido(n)}
    assert not dentro, (
        "estos scripts escriben su salida dentro de la huella: "
        + ", ".join(f"{n} ({q})" for n, q in sorted(dentro.items()))
        + ". Anadelos a `manifiesto.EXCLUIR`, o correrlos bloqueara el "
          "arranque del siguiente notebook.")
    return (f"{len(salidas)} scripts escriben en data/ y los "
            f"{sum(1 for n in salidas if n.endswith('.json'))} que caen en la "
            "huella estan excluidos")


@prueba("mirar los datos no cuenta como cambiar el codigo")
def t_derivados_fuera_de_la_huella():
    """`data/cobertura_corpus.json` y `data/diagnostico_cumplimiento.json` son
    auditorias DERIVADAS, y viven en `data/` porque describen los datos y no
    una corrida. Pero `manifiesto.PATRONES` incluye `data/*.json`, asi que si
    entraran en la huella, correr una auditoria la moveria.

    El caso grave es el segundo: `diagnostico_cumplimiento.json` incluye la
    lectura de `agente_trazas.json`, que existe solo despues de M3. Si entrara
    en la huella, correr el diagnostico entre M1 y M3 les daria huellas de
    codigo distintas, y `verificar_entrega.py` diria --- correctamente, segun
    su propia regla --- que no son el mismo experimento. Por haber mirado los
    datos.
    """
    import subprocess
    sys.path.insert(0, str(DATA))
    import manifiesto as mf
    antes = mf.total(mf.manifiesto())
    for script in ("auditar_cobertura.py", "diagnostico_cumplimiento.py"):
        r = subprocess.run([sys.executable, "-I", str(DATA / script)],
                           capture_output=True, text=True, cwd=str(RAIZ))
        assert r.returncode == 0, f"{script}: {(r.stdout + r.stderr)[-300:]}"
    despues = mf.total(mf.manifiesto())
    assert antes == despues, (
        f"correr las auditorias movio la huella: {antes} -> {despues}. "
        "Añádelas a `manifiesto.EXCLUIR`.")
    for derivado in ("cobertura_corpus.json", "diagnostico_cumplimiento.json"):
        assert (DATA / derivado).exists(), f"{derivado} no se genero"
        assert derivado in mf.EXCLUIR, f"{derivado} no esta en EXCLUIR"
    return f"las dos auditorias corren y la huella sigue en {antes}"


@prueba("la tesis del reporte la dictan los intervalos, no el autor")
def t_reporte_no_afirma_de_mas():
    """`data/reporte.py` genera REPORTE.md leyendo los artefactos, y la
    afirmacion central --- que el brazo afinado gana con intervalos que no se
    solapan --- es la ULTIMA que podria estar escrita a mano. Si la proxima
    corrida mueve un intervalo, una frase escrita seguiria diciendo que
    separan.

    Esta prueba lo fuerza por los dos lados: con intervalos separados la frase
    afirma, y con intervalos solapados la MISMA funcion dice que la tabla no
    lo sostiene. Y comprueba lo otro que no puede fallar en silencio: que un
    artefacto ausente quede nombrado en vez de desaparecer.
    """
    import tempfile
    sys.path.insert(0, str(DATA))
    import reporte

    def _sc(nombre, punto, bajo, alto):
        return {"sistema": nombre, "n": 63, "acierto_juridico": punto,
                "ic": {"acierto_juridico": {"punto": punto, "ic_bajo": bajo,
                                            "ic_alto": alto, "n": 63}}}

    orig_results, orig_cache = reporte.RESULTS, dict(reporte._CACHE)
    try:
        tmp = Path(tempfile.mkdtemp(prefix="prueba_rep_"))
        reporte.RESULTS = tmp / "results"
        reporte.RESULTS.mkdir(parents=True)

        def _con(brazos):
            reporte._CACHE.clear()
            reporte._FALTAN.clear()
            reporte._CITAS.clear()
            reporte._CACHE["m3_scorecards_comunes.json"] = {"datos": brazos}
            return reporte.separacion()

        # 1 · separados: el primero gana y la frase lo afirma.
        sep = _con([_sc("fine-tuned solo", 0.873, 0.794, 0.952),
                    _sc("RAG ingenuo", 0.667, 0.540, 0.778),
                    _sc("agente + reglas", 0.603, 0.476, 0.730)])
        assert sep["concluyente"] is True, sep
        assert sep["solapan_con"] == [], sep
        assert "no se solapan" in sep["frase"], sep["frase"]

        # 2 · solapados: la misma funcion se retracta.
        sep2 = _con([_sc("fine-tuned solo", 0.700, 0.580, 0.810),
                     _sc("RAG ingenuo", 0.667, 0.540, 0.778)])
        assert sep2["concluyente"] is False, sep2
        assert sep2["solapan_con"] == ["RAG ingenuo"], sep2
        assert "no sostiene" in sep2["frase"], sep2["frase"]

        # 3 · parcial: separa de uno y no del otro, y lo nombra.
        sep3 = _con([_sc("fine-tuned solo", 0.873, 0.794, 0.952),
                     _sc("RAG ingenuo", 0.800, 0.700, 0.900),
                     _sc("agente + reglas", 0.400, 0.300, 0.500)])
        assert sep3["concluyente"] is False
        assert sep3["solapan_con"] == ["RAG ingenuo"], sep3
        assert "RAG ingenuo" in sep3["frase"], sep3["frase"]

        # 4 · sin el artefacto no hay tesis, y se dice.
        reporte._CACHE.clear(); reporte._FALTAN.clear(); reporte._CITAS.clear()
        sep4 = reporte.separacion()
        assert sep4["concluyente"] is False, sep4
        assert "no esta en `results/`" in sep4["frase"], sep4["frase"]

        # 5 · y el reporte entero marca cada ausencia en vez de callarla.
        reporte._CACHE.clear(); reporte._FALTAN.clear(); reporte._CITAS.clear()
        reporte.construir()
        for esperado in ("m1_scorecard_finetuned.json", "m2_sesgos.json",
                         "m3_ganadores.json"):
            assert esperado in reporte._FALTAN, sorted(reporte._FALTAN)
    finally:
        reporte.RESULTS = orig_results
        reporte._CACHE.clear()
        reporte._CACHE.update(orig_cache)
        reporte._FALTAN.clear()
        reporte._CITAS.clear()
    return ("separados -> afirma · solapados -> se retracta · parcial -> "
            "nombra con quien · sin artefacto -> no hay tesis")


@prueba("ninguna cita esperada se queda sin fragmento que la respalde")
def t_cobertura_corpus():
    """Separa dos cosas que `recall == 0` mezcla y que llevaban mal
    diagnosticadas en ROADMAP3 · M3-4: que el fragmento NO EXISTA (cobertura,
    se cura ampliando el corpus) y que exista pero no entre en el top-5
    (ranking, y ampliar el corpus lo EMPEORA porque mete mas candidatos a
    competir por los mismos 5 puestos).

    Medido: la cobertura es completa en los dos eval sets y el ranking es el
    cuello de botella. Esta prueba fija la mitad que si se puede garantizar
    sin correr nada --- que toda cita esperada tenga fragmento --- para que
    anadir un caso nuevo sin su norma falle aqui y no en una corrida de GPU.
    """
    sys.path.insert(0, str(DATA))
    from auditar_cobertura import auditar
    r = auditar()
    for nombre, d in r["por_eval_set"].items():
        assert d["sin_cobertura"] == 0, (
            f"{nombre}: {d['sin_cobertura']} casos citan normas que no estan "
            f"en el corpus: {d['citas_esperadas_sin_fragmento']}")
        assert d["casos_con_citas_esperadas"] > 0, nombre
    v2 = r["por_eval_set"]["eval_set_v2.json"]
    # Y que el diagnostico no se pierda: si algun dia la cobertura se rompe,
    # el mensaje tiene que cambiar solo.
    assert "COBERTURA COMPLETA" in v2["diagnostico"]
    assert v2["cubiertos_pero_fuera_del_top5_bm25"] > 0,         "si BM25 ya acierta en todos, el proxy dejo de medir lo que medía"
    # Y el artefacto guardado no puede estar caducado: `reporte.py` lo cita
    # para afirmar que la cobertura es completa, y un derivado viejo con
    # aspecto de vigente es el modo de fallo que este proyecto persigue.
    guardado = DATA / "cobertura_corpus.json"
    if guardado.exists():
        import hashlib
        g = json.loads(guardado.read_text(encoding="utf-8"))
        viejas = [f for f, h in (g.get("_fuentes") or {}).items()
                  if hashlib.sha256((DATA / f).read_bytes())
                  .hexdigest()[:16] != h]
        assert not viejas, (
            f"data/cobertura_corpus.json se calculo con otra version de "
            f"{viejas}: corre `python -I data/auditar_cobertura.py`")
    return (f"{v2['casos_con_citas_esperadas']} casos, 0 sin cobertura · "
            f"{v2['cubiertos_pero_fuera_del_top5_bm25']} fuera del top-5 de "
            f"BM25 (peor rango {v2['peor_rango_bm25']} de "
            f"{r['corpus']['chunks']}): es ranking, no cobertura · el "
            f"artefacto guardado no esta caducado")


@prueba("todos los fragmentos declaran CUANDO se verificaron")
def t_verificado_el():
    docs = json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))["documentos"]
    sin = [d["id"] for d in docs if not d.get("verificado_el")]
    assert not sin, f"sin `verificado_el`: {sin[:6]}"
    # Y lo que dice ser transcripcion literal no puede ser una nota del equipo.
    for d in docs:
        if d.get("transcripcion") == "literal":
            assert "NO ES DERECHO VIGENTE" not in d["texto"], \
                f"{d['id']}: dice `literal` y su texto es una nota editorial"
    notas = [d["id"] for d in docs if d.get("transcripcion") == "nota_editorial"]
    return (f"{len(docs)} con fecha de verificacion · {len(notas)} marcados "
            f"`nota_editorial` en vez de `literal`: {notas}")


@prueba("las cuatro leyes del cuello de botella salieron de 1-3 fragmentos")
def t_cuellos():
    from collections import Counter
    docs = json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))["documentos"]
    por_norma = Counter(d["norma"] for d in docs)
    esperado = {"Ley 1751 de 2015": 28, "Ley 393 de 1997": 26,
                "Ley 1095 de 2006": 25, "Ley 472 de 1998": 25}
    flojas = {n: por_norma[n] for n in esperado if por_norma[n] < 4}
    assert not flojas, f"siguen con menos de 4 fragmentos: {flojas}"
    return " · ".join(f"{n.split()[1]}:{por_norma[n]}" for n in esperado)


@prueba("citar jurisprudencia REAL no cuenta como alucinacion")
def t_juris():
    docs = json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))["documentos"]
    juris = [d for d in docs if d.get("tipo") == "jurisprudencia"]
    assert len(juris) >= 3, f"solo {len(juris)} fragmentos de jurisprudencia"
    # La T-225 de 1993 es la fuente del test conjuntivo de reglas.py. Que su
    # texto este en el corpus es lo que vuelve esa cita verificable.
    t225 = next((d for d in juris if "T-225" in d["norma"]), None)
    assert t225, "falta la T-225 de 1993, que es la base de reglas.py"
    assert "presencia concurrente" in t225["texto"], \
        "la T-225 no trae la frase que sostiene el test conjuntivo"

    e = {"derecho": "estabilidad_laboral_reforzada", "accionado": "empresa",
         "mecanismo": "tutela", "procede": True, "razon": "x", "pretension": "y",
         "fundamento": "art. 13 CP; Ley 361 de 1997; Sentencia C-531 de 2000; "
                       "Sentencia T-999 de 2099; Ley 9999 de 2050"}
    r = metricas.alucinacion_normativa([schema.render_salida(e)])
    j = r["jurisprudencia"]
    # 5 citas: 3 validas, 1 jurisprudencia conocida, 1 sin verificar, 1 inventada
    assert r["citas_inventadas"] == 1, \
        f"{r['citas_inventadas']} inventadas; solo `Ley 9999 de 2050` lo es"
    assert j["en_fundamento"] == 1, j
    assert j["en_fundamento_sin_verificar"] == 1, j
    # Sin el arreglo, las dos sentencias contaban como inventadas y la tasa
    # era 0.6 en vez de 0.2: el triple, por citar bien.
    assert abs(r["tasa_alucinacion"] - 0.2) < 1e-9, r["tasa_alucinacion"]
    return (f"{len(juris)} sentencias en el corpus · tasa 0.2000 (sin el "
            f"arreglo habria sido 0.6000)")


@prueba("la atribucion de la Ley 361 quedo resuelta, no pendiente")
def t_ley361():
    docs = {d["id"]: d for d in
            json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))["documentos"]}
    nota = docs["L361-26"].get("nota_vigencia", "")
    assert "PENDIENTE DE VERIFICAR" not in nota, "sigue marcada como pendiente"
    assert "ATRIBUCION RESUELTA" in nota, "no declara la resolucion"
    assert "C-744 de 2012" in nota, "no cita la sentencia que lo resuelve"
    # Y las dos fuentes primarias tienen que estar en el corpus.
    for i in ("J-C744-12", "J-C531-00"):
        assert i in docs, f"falta el fragmento {i}"
    assert "INEXEQUIBLE el artículo 137" in docs["J-C744-12"]["texto"]
    assert "oficina de Trabajo" in docs["J-C531-00"]["texto"]
    return "resuelta con dos fuentes primarias, las dos en el corpus"


@prueba("la cobertura del corpus cubre TODOS los eval sets, v2 incluido")
def t_cobertura():
    docs = json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))["documentos"]
    chunks = rag.trocear(docs)
    sin = {}
    for a in ("dataset.json", "eval_set.json", "eval_set_v2.json",
              "eval_set_m3.json"):
        for e in json.loads((DATA / a).read_text(encoding="utf-8"))["ejemplos"]:
            for cita in schema.citas(e.get("fundamento") or ""):
                if not any(rag.cubre(c, cita) for c in chunks):
                    sin.setdefault(cita, []).append(f"{a}:{e['id']}")
    assert not sin, f"citas sin respaldo: {list(sin)[:5]}"
    # Y el auditor tiene que mirar los cuatro archivos, no tres.
    aud = (DATA / "auditar_corpus.py").read_text(encoding="utf-8")
    assert "eval_set_v2.json" in aud, \
        "data/auditar_corpus.py no comprueba la cobertura de eval_set_v2"
    return "4 artefactos sin ninguna cita sin respaldo, y el auditor los mira todos"


# ==========================================================================
# 10e · dataset
# ==========================================================================
@prueba("el dataset entero esta verificado por el motor, salvo la abstencion")
def t_dataset_hechos():
    casos = json.loads((DATA / "dataset.json").read_text(encoding="utf-8"))["ejemplos"]
    ab = [c for c in casos if c.get("tipo") == "abstencion"]
    sin = [c["id"] for c in casos
           if c.get("tipo") != "abstencion" and not c.get("hechos")]
    assert not sin, f"sin hechos codificados: {sin[:8]}"
    mal = []
    for c in casos:
        if not c.get("hechos"):
            continue
        d = decidir(Hechos(**c["hechos"]))
        if d.mecanismo != c["mecanismo"] or d.procede_tutela != c["procede"]:
            mal.append(c["id"])
    assert not mal, f"el motor no deriva la etiqueta: {mal[:6]}"
    return (f"{len(casos) - len(ab)}/{len(casos)} con hechos derivados por el "
            f"motor · {len(ab)} de abstencion por diseno")


@prueba("los juicios afirmados del dataset bajaron de 25 a los declarados")
def t_dataset_estratos():
    from collections import Counter
    casos = json.loads((DATA / "dataset.json").read_text(encoding="utf-8"))["ejemplos"]
    c = Counter(x["estrato_verificacion"] for x in casos
                if x.get("estrato_verificacion"))
    assert c["juicio"] <= 10, f"{c['juicio']} en `juicio`, esperaba <= 10"
    # Y la documentacion tiene que cuadrar con los datos: fue justo lo que
    # fallo al anadir los casos nuevos, y el guardia del script lo caza.
    sys.path.insert(0, str(DATA))
    from codificar_hechos_dataset import SIN_DESGLOSAR
    declarados = sum(len(v["casos"]) for v in SIN_DESGLOSAR.values()
                     if isinstance(v, dict))
    assert declarados == c["juicio"], \
        f"la lista declara {declarados} sin desglosar y hay {c['juicio']}"
    return f"plano {c['plano']} · derivado {c['derivado']} · juicio {c['juicio']}, declarados"


@prueba("hay 9 etiquetas con fuente externa, y su procedencia es verificable")
def t_casos_reales():
    casos = json.loads((DATA / "dataset.json").read_text(encoding="utf-8"))["ejemplos"]
    reales = [c for c in casos if c.get("tipo_fuente") == "real"]
    assert len(reales) >= 9, f"solo {len(reales)} casos de fuente real"
    for c in reales:
        p = c.get("procedencia", "")
        assert "Corte Constitucional" in p, f"{c['id']}: sin la Corte en procedencia"
        assert "expediente" in p.lower(), f"{c['id']}: sin numero de expediente"
    # T-008 de 2024 es el contrapeso de A04: tutela contra providencia que SI
    # procede. Tener las dos caras impide aprender una regla fija.
    contra = [c for c in reales if "providencia" in c.get("categoria", "")]
    assert contra, "falta el caso de tutela contra providencia CONCEDIDA"
    assert contra[0]["mecanismo"] == "tutela", contra[0]["mecanismo"]
    return (f"{len(reales)} con expediente y fallo de la Corte · incluye "
            f"{contra[0]['id']} ({contra[0].get('sentencia')}), el contrapeso de A04")


@prueba("ninguna categoria compartida con el eval tiene un solo ejemplo")
def t_categorias():
    from collections import Counter
    casos = json.loads((DATA / "dataset.json").read_text(encoding="utf-8"))["ejemplos"]
    ev = json.loads((DATA / "eval_set_v2.json").read_text(encoding="utf-8"))["ejemplos"]
    cat = Counter(c["categoria"] for c in casos)
    cat_ev = {e["categoria"] for e in ev}
    compartidas = set(cat) & cat_ev
    singles = sorted(k for k in compartidas if cat[k] == 1)
    assert not singles, f"con un solo ejemplo de entrenamiento: {singles}"
    return (f"{len(compartidas)} categorias compartidas, todas con 2+ casos "
            f"(antes 13 tenian 1)")


# ==========================================================================
# 10f · notebooks: arranque, checkpoint y entrega
# ==========================================================================
def _nb(nombre):
    import json as _j
    return _j.loads((RAIZ / "notebooks" / nombre).read_text(encoding="utf-8"))


NOTEBOOKS = ("M1_finetuning.ipynb", "M2_harness.ipynb", "M3_rag.ipynb")


@prueba("los tres notebooks compilan y tienen celda de arranque")
def t_notebooks():
    import ast
    out = []
    for n in NOTEBOOKS:
        nb = _nb(n)
        mal = []
        for i, c in enumerate(nb["cells"]):
            if c["cell_type"] != "code":
                continue
            # LAS MAGIAS SE QUITAN LINEA A LINEA, NO SE SALTA LA CELDA.
            #
            # Saltaba la celda entera si su primera linea era `!` o `%`. Eso
            # dejaba SIN COMPROBAR todo el Python de esas celdas --- en M1 la
            # primera celda tiene un `assert` y dos `import` que nunca se
            # revisaron --- y ademas convertia un comentario puesto delante de
            # un `!pip` en un falso fallo de sintaxis, porque la celda dejaba
            # de empezar por magia y el `!` pasaba al parser.
            #
            # Quitando solo las lineas de magia se comprueba el resto, que es
            # lo que se queria comprobar.
            s = "".join(c["source"])
            codigo = chr(10).join(
                "" if l.lstrip().startswith(("!", "%")) else l
                for l in s.splitlines())
            try:
                ast.parse(codigo)
            except SyntaxError as ex:
                mal.append((i, ex.msg))
        assert not mal, f"{n}: errores de sintaxis {mal}"
        crudo = json.dumps(nb)
        assert "arranque.celda" in crudo, f"{n}: sin celda de arranque (#31/#33)"
        out.append(f"{n[:2]}:{len(nb['cells'])}")
    return ("0 errores de sintaxis (magias quitadas linea a linea, no celdas "
            "enteras saltadas) · arranque en los 3 · " + " ".join(out))


@prueba("la prueba de humo caza un entorno incompleto")
def t_humo():
    import arranque
    for m in ("m1", "m2", "m3"):
        r = arranque.humo(m)
        assert isinstance(r["ok"], bool) and "fallos" in r, r
        assert r["pasa"], f"{m}: no paso ni una comprobacion"
    # EL REQUISITO SE COMPRUEBA DECLARADO, NO POR QUE AHORA FALLE.
    #
    # Esto miraba que `humo("m2")` FALLARA por falta de las predicciones,
    # lo que solo ocurre mientras `results/` este vacio y deja de ocurrir
    # en cuanto M1 corre. Lo que importa no es que falle hoy: es que el
    # requisito este DECLARADO, porque lo que no se declara no se
    # comprueba nunca.
    for _m in ("m2", "m3"):
        assert any("m1_predicciones" in x
                   for x in arranque.ORDEN[_m]["necesita"]), (
            f"{_m} deberia DECLARAR results/m1_predicciones.json")
    # Y que el chequeo de verdad lo mire: solo comprobable si falta.
    if not (RAIZ / "results" / "m1_predicciones.json").exists():
        assert any("m1_predicciones" in f
                   for f in arranque.humo("m2")["fallos"]), (
            "con las predicciones ausentes, M2 deberia marcarlo")
    mal = arranque.humo("modulo_que_no_existe")
    assert not mal["ok"], "un modulo desconocido deberia fallar"
    return "los 3 modulos se comprueban · M2 exige las predicciones de M1"


@prueba("el checkpoint de M3 es atomico y tolera corrupcion")
def t_checkpoint():
    import arranque
    p = Path(tempfile.gettempdir()) / "_ap_ck.json"
    if p.exists():
        os.remove(p)
    assert arranque.cargar_checkpoint(p) == {}, "sin archivo deberia dar {}"
    arranque.guardar_checkpoint(p, {"brazos": {"a": 1}})
    assert arranque.cargar_checkpoint(p) == {"brazos": {"a": 1}}
    # Un checkpoint corrupto no puede tumbar la corrida.
    p.write_text("{esto no es json", encoding="utf-8")
    assert arranque.cargar_checkpoint(p) == {}, "corrupto deberia dar {}"
    assert not list(p.parent.glob("_ap_ck.json.tmp")), "quedo un .tmp"
    os.remove(p)
    # Y la celda de los brazos tiene que usarlo.
    s = json.dumps(_nb("M3_rag.ipynb"))
    for k in ("brazos_checkpoint", "cargar_checkpoint", "_ck_guardar"):
        assert k in s, f"M3 no usa `{k}` (#32)"
    return "guarda, relee, ignora corrupcion y no deja .tmp · M3 lo usa"


@prueba("todo artefacto declarado se publica, y al reves")
def t_entrega():
    import re
    import arranque
    pub = set()
    # DOS patrones, porque hay dos formas legitimas de declarar un destino.
    #
    # La directa, `publicar("nombre", "results/x.json")`, y la de lista ---
    # `A_PUBLICAR = [("nombre", "results/x.json"), ...]` seguida de un bucle
    # ---, que M3 usa para poder comprobar los doce artefactos ANTES de
    # publicar ninguno. Con solo el primer patron, esa guarda volvia invisible
    # lo que declara, y esta prueba fallaba por la forma y no por el fondo:
    # los destinos siguen siendo literales y auditables, solo viven en una
    # tupla.
    PATRONES_DESTINO = (
        r"publicar\(\s*['\"]([^'\"]+)['\"]\s*,\s*['\"]([^'\"]+)['\"]",
        r"\(\s*['\"][^'\"]+['\"]\s*,\s*['\"](results/[^'\"]+)['\"]\s*\)",
    )
    for n in NOTEBOOKS:
        for c in _nb(n)["cells"]:
            src = "".join(c["source"])
            for m in re.finditer(PATRONES_DESTINO[0], src):
                pub.add(m.group(2))
            for m in re.finditer(PATRONES_DESTINO[1], src):
                pub.add(m.group(1))
    decl = {x for c in arranque.ORDEN.values() for x in c["produce"]}
    # Declarar lo que nadie publica convierte a verificar_entrega.py en un
    # generador de falsas alarmas; publicar lo que nadie declara lo deja fuera
    # de la verificacion. Las dos cosas son defectos.
    assert not (decl - pub), f"declarados y no publicados: {sorted(decl - pub)}"
    assert not (pub - decl), f"publicados y no declarados: {sorted(pub - decl)}"
    return f"{len(decl)} artefactos, declarados y publicados coinciden"


@prueba("verificar_entrega detecta que falta la corrida")
def t_verificar():
    """En un arbol SIN artefactos, no en el de trabajo.

    Exigia que la salida dijera "faltan", lo que solo es cierto mientras
    `results/` este vacio. En cuanto los tres modulos corren --- el objetivo
    del proyecto --- no falta nada y la prueba fallaba por estar bien. Mismo
    defecto que tenian `t_calibracion` y la del BOM: medir el estado del
    directorio en vez del comportamiento del codigo.
    """
    import subprocess
    import tempfile as _tf
    arbol = Path(_tf.mkdtemp(prefix="prueba_ve_"))
    (arbol / "data").mkdir()
    (arbol / "results").mkdir()
    (arbol / "src").mkdir()
    for p in (RAIZ / "src").glob("*.py"):
        (arbol / "src" / p.name).write_bytes(p.read_bytes())
    for f in ("verificar_entrega.py", "manifiesto.py"):
        (arbol / "data" / f).write_bytes((DATA / f).read_bytes())
    r = subprocess.run([sys.executable, "-I",
                        str(arbol / "data" / "verificar_entrega.py")],
                       capture_output=True, text=True, cwd=str(arbol))
    salida = r.stdout + r.stderr
    assert r.returncode == 1, (
        f"sin artefactos deberia salir con 1, dio {r.returncode}")
    assert "VERIFICACION DE LA ENTREGA" in salida
    assert "faltan" in salida.lower(), salida[-320:]
    # Y lo que de verdad importa: que la huella sin leer sea un FALLO y no un
    # silencio. Fue un no-op durante toda la vida del script.
    assert "NO se comprobo que corrieran con el mismo" in salida, salida[-500:]
    return ("en un arbol vacio sale con exit 1, dice que artefactos faltan y "
            "declara que NO pudo cotejar la huella en vez de callarlo")


@prueba("el manifiesto cubre todo lo que una corrida necesita")
def t_manifiesto():
    import subprocess
    sys.path.insert(0, str(DATA))
    import manifiesto as man
    m = man.manifiesto()
    nombres = {n for n, _, _ in m}
    # Lo que los notebooks leen de verdad tiene que estar cubierto, o una
    # corrida puede salir con un archivo viejo sin que nada lo delate.
    for n in ("src/metricas.py", "src/harness.py", "src/reglas.py",
              "src/arranque.py", "data/eval_set_v2.json", "data/corpus.json",
              "data/dataset.json", "notebooks/M1_finetuning.ipynb"):
        assert n in nombres, f"el manifiesto no cubre {n}"
    # Y las SALIDAS no, porque cambian solas entre corridas.
    assert not any("reverificacion_corpus" in n for n in nombres),         "el manifiesto incluye una salida de verificador"
    r = subprocess.run([sys.executable, "-I", str(DATA / "manifiesto.py")],
                       capture_output=True, text=True, cwd=str(RAIZ))
    assert r.returncode == 0 and "_TOTAL" in r.stdout, r.stderr[-200:]
    return f"{len(m)} archivos · huella total {man.total(m)}"


# ==========================================================================
# 11 · idempotencia del pipeline
# ==========================================================================
@prueba("el pipeline de 8 constructores converge en una pasada")
def t_idempotencia():
    import hashlib
    import subprocess
    archivos = ["dataset.json", "eval_set.json", "eval_set_v2.json",
                "eval_set_m3.json"]

    def huella():
        return {a: hashlib.sha256((DATA / a).read_bytes()).hexdigest()[:16]
                for a in archivos}

    antes = huella()
    # EL ORDEN IMPORTA y converge en una pasada solo asi. Los scripts que
    # ANADEN casos van antes del que los verifica, y el de fundamentos al
    # final porque anota sobre lo que los otros construyen. Con
    # `codificar_hechos_dataset` antes de `casos_reales` el pipeline
    # necesitaba DOS pasadas para llegar al punto fijo.
    orden = ["codificar_hechos_eval", "construir_eval_v2",
             # `codificar_hechos_m3` va DESPUES del que construye
             # eval_set_m3.json --- que lo reescribe entero --- y ANTES de
             # `anotar_fundamentos`, que necesita los `hechos` para poder
             # DERIVAR el fundamento del mecanismo en vez de copiarlo.
             "construir_eval_m3_terminos", "codificar_hechos_m3",
             "casos_reales",
             "ampliar_categorias", "codificar_hechos_dataset",
             "anotar_fundamentos"]
    for s in orden:
        r = subprocess.run([sys.executable, "-I", str(DATA / f"{s}.py")],
                           capture_output=True, text=True, cwd=str(RAIZ))
        assert r.returncode == 0, f"{s} fallo: {(r.stdout + r.stderr)[-300:]}"
    despues = huella()
    dif = [a for a in archivos if antes[a] != despues[a]]
    assert not dif, f"cambiaron al re-correr: {dif}"
    return (f"{len(orden)} scripts en orden, {len(archivos)} "
            f"artefactos, 0 cambios al repetir")


# ==========================================================================
# 9 · los dos fallos silenciosos de m1/20261016T174233Z
# ==========================================================================
@prueba("un extractor que no emite JSON queda registrado, no en silencio")
def t_extractor_mudo():
    """El fallo que publico un 42.9% como si fuera un resultado.

    El adaptador de M1 emitia el bloque de cinco lineas en vez del JSON de
    hechos. `_json_de` devolvia `{}`, el default pro homine ponia los doce
    booleanos en False, el motor no encontraba causal y fallaba a tutela, en 62
    de 63 casos. Las metricas de la corrida daban `alucinacion 0.0%` y
    `adherencia_estructural 1.0` --- las dos ciertas y las dos vacias.

    Esta prueba fija el contrato: con un extractor mudo la lista de fallos se
    llena, y con uno que funciona queda vacia.
    """
    ej = _cargar("dataset.json")[0]
    cinco_lineas = schema.render_salida(ej)
    assert sistema._json_de(cinco_lineas) == {}, (
        "si esto deja de ser {} el escenario cambio y la prueba ya no mide "
        "lo que dice medir")

    hechos_json = json.dumps(
        {k: False for k in HECHOS_EXTRAIBLES}
        | {"medio_eficaz": True, "afectacion_individual": True,
           "derecho": "salud", "accionado": "EPS",
           "pretension": "autorizar el medicamento"}, ensure_ascii=False)

    mudo = sistema.SistemaHibrido(lambda _s, _u: cinco_lineas)
    bueno = sistema.SistemaHibrido(lambda _s, _u: hechos_json)
    for _ in range(5):
        mudo(ej["relato"])
        bueno(ej["relato"])

    assert len(mudo.fallos_extraccion) == 5, (
        f"extractor mudo: {len(mudo.fallos_extraccion)}/5 registrados. Si no "
        f"se registran, el brazo vuelve a publicar el default pro homine.")
    assert not bueno.fallos_extraccion, (
        f"falso positivo: {len(bueno.fallos_extraccion)} fallos con un "
        f"extractor que SI emite JSON")
    assert mudo.fallos_extraccion[0]["salida"], "el registro no guarda la salida"
    # Y el brazo 4 de M3 tiene el mismo cableado.
    assert hasattr(sistema.SistemaReglas(lambda _s, _u: "", None),
                   "fallos_extraccion"), "SistemaReglas no registra los fallos"
    return ("extractor mudo 5/5 registrados · extractor bueno 0 falsos "
            "positivos · SistemaReglas cableado igual")


@prueba("un articulo de la Constitucion real y no declarado no es inventado")
def t_cp_sin_verificar():
    """`normas.json` declara 20 articulos de los 380 de la Constitucion.

    La metrica leia esa lista como si fuera la Constitucion entera: `art. 12
    CP` --- tortura y desaparicion forzada --- y `art. 68 CP` ---
    establecimientos educativos --- contaban como alucinacion. En
    m1/20261016T174233Z eran 2 de las 6 "invenciones" del modelo ajustado.

    Lo que SI debe seguir siendo inventado es un numero fuera de rango.
    """
    v, su, le = metricas._vocabulario_normas()
    esperado = {
        "art. 12 CP": "constitucional_sin_verificar",
        "art. 68 CP": "constitucional_sin_verificar",
        "art. 380 CP": "constitucional_sin_verificar",
        "art. 381 CP": "inventada",          # la Constitucion acaba en 380
        "art. 999 CP": "inventada",
        "art. 86 CP": "valida",              # declarado en normas.json
        "Sentencia T-225 de 1993": "jurisprudencia",
        "art. 13": "incompleta",
    }
    mal = {c: metricas.clasificar_cita(c, v, su, le) for c in esperado}
    mal = {c: g for c, g in mal.items() if g != esperado[c]}
    assert not mal, f"clasificacion inesperada: {mal}"

    # Las tres metricas tienen que coincidir en que `art. 12 CP` existe: el
    # fallo original era que `pertinencia_citas` preguntaba `c in validas`.
    assert "art. 12 CP" not in v, "la prueba supone que no esta declarado"
    gold = _cargar("eval_set_v2.json")[:3]
    salidas = [schema.render_salida(g).replace(
        "Derecho:", "Derecho:", 1) for g in gold]
    # Inyectar la cita en el fundamento de la primera salida.
    salidas[0] = salidas[0].replace("(art.", "(art. 12 CP; art.", 1)
    alu = metricas.alucinacion_normativa(salidas)
    assert alu["constitucional_sin_verificar"]["en_fundamento"] >= 1, (
        f"la caja constitucional no se llena: {alu['constitucional_sin_verificar']}")
    per = metricas.pertinencia_citas(salidas, gold)
    assert per["inventadas"] == 0, (
        f"`pertinencia_citas` sigue contando el art. 12 CP como inventado: "
        f"{per['inventadas']}")
    return (f"{len(esperado)} clasificaciones correctas · la caja "
            f"constitucional se llena · pertinencia no lo cuenta como inventado")


@prueba("los tres plazos de peticion no se confunden entre si")
def t_tipo_de_termino():
    """`SistemaReglas` conocia 7 plazos y mapeaba todo a `peticion_general`.

    `terminos.TERMINOS` distingue 15 dias habiles para una peticion general
    (art. 14 Ley 1755), 10 para documentos (art. 14.1) y 30 para una consulta
    (art. 14.2). El brazo de reglas los colapsaba en el primero, asi que MT02
    --- copia de un expediente --- y MT03 --- una consulta --- se calculaban
    con el plazo equivocado, y un plazo equivocado da una conclusion
    equivocada sobre si vencio. El agente nunca tuvo el fallo: su esquema de
    herramienta expone los siete tipos.
    """
    from sistema import tipo_de_termino
    casos = {c["id"]: c for c in _cargar("eval_set_m3.json")}
    esperado = {"MT01": "peticion_general", "MT02": "peticion_documentos",
                "MT03": "peticion_consulta", "MT04": "renuencia_cumplimiento",
                "MT05": "peticion_general"}
    mal = {}
    for i, t_esp in esperado.items():
        c = casos[i]
        h = Hechos(**{k: v for k, v in (c.get("hechos") or {}).items()
                      if k in Hechos().__dataclass_fields__ and v is not None})
        got = tipo_de_termino(c["relato"], {"derecho": c.get("derecho")}, h)
        if got != t_esp:
            mal[i] = f"{got} (esperado {t_esp})"
    assert not mal, f"tipo de termino equivocado: {mal}"
    # Y que no invente un plazo donde no hay ninguno.
    assert tipo_de_termino("me duele la espalda", {"derecho": "salud"}) is None, (
        "inventa un plazo para un caso sin termino legal")
    return (f"{len(esperado)} casos MT con su plazo correcto · sin plazo "
            f"donde no aplica")


@prueba("ningun artefacto se publica antes de generarse")
def t_orden_publicar():
    """El fallo de m1/20261016T234001Z, que la prueba 44 no podia ver.

    La prueba 44 comprueba que lo declarado y lo publicado COINCIDAN. No mira
    el ORDEN, y por eso paso un `c.publicar("estabilidad", ...)` colocado en
    la celda 29 cuando el artefacto se genera en la 31. En Colab eso levanta
    un FileNotFoundError que corta la celda a mitad --- y la cortó justo antes
    de `model.save_pretrained()`, dejando el adaptador sin guardar despues de
    treinta minutos de GPU.

    Es estatico: compara en que celda aparece cada `guardar_json` con la del
    `publicar` del mismo nombre. No necesita correr nada.
    """
    import re
    mal = []
    for nbn in ("M1_finetuning", "M2_harness", "M3_rag"):
        nb = json.loads((RAIZ / "notebooks" / f"{nbn}.ipynb")
                        .read_text(encoding="utf-8"))
        guarda, publica = {}, {}
        for i, c in enumerate(nb["cells"]):
            if c["cell_type"] != "code":
                continue
            src = "".join(c["source"])
            for n in re.findall(r'guardar_(?:json|csv)\(\s*["\']([^"\']+)',
                                src):
                guarda.setdefault(n, i)
            for n in re.findall(r'c\.publicar\(\s*["\']([^"\']+)', src):
                publica.setdefault(n, i)
        for n, cp in publica.items():
            cg = guarda.get(n)
            if cg is None:
                # Lo pone `c.artefactos[...] = ...` a mano; no es un fallo.
                continue
            if cp < cg:
                mal.append(f"{nbn}: publica '{n}' en c{cp} pero se genera "
                           f"en c{cg}")
    if mal:
        raise AssertionError(
            "publicaciones antes de su artefacto: " + " | ".join(mal))
    return "los 3 notebooks publican cada artefacto despues de generarlo"


@prueba("el checkpoint se descarta solo si lo genero otro codigo")
def t_checkpoint_procedencia():
    """Lo que costo tres corridas invalidas de M3.

    `runs/cache/` es compartida entre corridas a proposito, y el checkpoint
    de los brazos acabo ahi. En m3/20261017T001359Z, .../011043Z y
    .../024911Z sirvio salidas de una corrida ANTERIOR al arreglo del prompt
    del agente, y las tres parecian correctas: `scorecard.csv` con sus cuatro
    filas y sus `n` bien, mientras `agente_resumen.json` decia `casos: 0`.

    El remedio no podia ser "acuerdate de borrar un archivo": eso fallo tres
    veces seguidas. Esta prueba fija que se descarte solo.
    """
    import tempfile
    import arranque
    d = Path(tempfile.mkdtemp()) / "ck.json"

    arranque.guardar_checkpoint(d, {"brazos": {"a": 1}})
    sellado = json.loads(d.read_text(encoding="utf-8"))
    assert "_procedencia" in sellado, "guardar_checkpoint no sella"
    assert sellado["_procedencia"].get("codigo"), "el sello no lleva codigo"

    vuelta = arranque.cargar_checkpoint(d)
    assert vuelta.get("brazos") == {"a": 1}, (
        "con el mismo codigo el checkpoint tiene que servir")
    assert "_procedencia" not in vuelta, (
        "el sello no debe volver mezclado con los datos")

    crudo = json.loads(d.read_text(encoding="utf-8"))
    crudo["_procedencia"]["codigo"] = "0" * 16
    d.write_text(json.dumps(crudo), encoding="utf-8")
    assert arranque.cargar_checkpoint(d) == {}, (
        "un checkpoint de otro codigo NO puede servirse")

    d.write_text(json.dumps({"brazos": {"a": 1}}), encoding="utf-8")
    assert arranque.cargar_checkpoint(d) == {}, (
        "un checkpoint sin sello --- de antes de este control --- tampoco")
    return ("sella, sirve con el mismo codigo, y descarta con codigo "
            "distinto o sin sello")


@prueba("abrir un notebook en Colab no cambia la huella del manifiesto")
def t_manifiesto_estable():
    """Un guardian que se dispara al no hacer nada ensena a ignorarlo.

    nbformat 4.5 pone un `id` por celda y Colab lo REGENERA al abrir el
    notebook, sin que nadie edite nada. Medido: abrir M1 cambio su huella en
    20 bytes y nos hizo parar una corrida para investigarlo. Lo mismo pasaba
    con `outputs`, ya descontado.

    Lo que SI tiene que cambiar la huella es una celda editada.
    """
    import hashlib
    import uuid
    sys.path.insert(0, str(DATA))
    import manifiesto as _m

    p = RAIZ / "notebooks" / "M1_finetuning.ipynb"
    h0 = hashlib.sha256(_m._canonico(p)).hexdigest()[:16]
    nb = json.loads(p.read_text(encoding="utf-8"))

    # lo que hace Colab: ids nuevos, salidas, execution_count
    for k, c in enumerate(nb["cells"]):
        c["id"] = uuid.uuid4().hex[:8]
        if c["cell_type"] == "code":
            c["outputs"] = [{"output_type": "stream", "name": "stdout",
                             "text": ["x" * 200]}]
            c["execution_count"] = k
    tmp = RAIZ / "notebooks" / "_tmp_estable.ipynb"
    tmp.write_text(json.dumps(nb, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    h1 = hashlib.sha256(_m._canonico(tmp)).hexdigest()[:16]

    # y ahora una celda EDITADA de verdad
    nb2 = json.loads(p.read_text(encoding="utf-8"))
    i = next(k for k, c in enumerate(nb2["cells"]) if c["cell_type"] == "code")
    nb2["cells"][i]["source"] = ["# una linea nueva\n"] + nb2["cells"][i]["source"]
    tmp.write_text(json.dumps(nb2, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    h2 = hashlib.sha256(_m._canonico(tmp)).hexdigest()[:16]
    tmp.unlink()

    assert h0 == h1, (
        f"abrir el notebook cambio la huella: {h0} -> {h1}. El guardian se "
        f"dispara sin que nadie edite nada.")
    assert h0 != h2, (
        "editar una celda NO cambio la huella: el guardian no guarda nada")
    return "ids y salidas no mueven la huella; una celda editada si"


@prueba("la redaccion no puede inventar normas ni callar el mecanismo")
def t_redaccion():
    """La capa de presentacion es donde se puede perder todo sin que se note.

    El bloque de triaje vale 87.3% con intervalo medido. Un texto que lo
    reformule mal no baja ese numero --- el scorecard sigue igual --- pero es
    lo que lee la persona. Dos fallos la destruyen:

      - INVENTAR una norma: deshace de un golpe la medicion de alucinacion
        normativa de todo el proyecto, porque la cita que ve el lector ya no
        es la que se midio.
      - CALLAR el mecanismo o la procedencia: 1 de cada 8 triajes esta mal, y
        en prosa fluida un error convence mas que en un bloque seco. Decir
        siempre la via y si procede es lo que lo deja detectable de un vistazo.

    Se prueba sin llamar a ningun modelo: `verificar_texto` es determinista.
    """
    import redaccion

    bloque = {"derecho": "trabajo", "accionado": "el empleador",
              "mecanismo": "via_ordinaria", "procede": False,
              "razon": "existe otro medio de defensa judicial idoneo",
              "fundamento": "art. 6.1 Decreto 2591 de 1991",
              "pretension": "reclamar la indemnizacion"}

    bueno = ("Por lo que cuentas, tu caso no va por tutela sino por la via "
             "laboral ordinaria (art. 6.1 Decreto 2591 de 1991). No procede "
             "la tutela porque existe ese otro proceso.")
    inventa = ("Tu caso va por la via ordinaria. Segun la Ley 789 de 2002 "
               "tienes derecho a indemnizacion. No procede tutela.")
    calla = "Lamento lo que te pasa. Tienes derechos que puedes reclamar."

    v = redaccion.verificar_texto(bueno, bloque)
    assert v["valido"], f"el texto correcto no valida: {v}"
    assert not v["citas_intrusas"]

    v = redaccion.verificar_texto(inventa, bloque)
    assert "Ley 789 de 2002" in v["citas_intrusas"], (
        f"no caza una norma inventada: {v['citas_intrusas']}")
    assert not v["valido"]

    v = redaccion.verificar_texto(calla, bloque)
    assert not v["dice_mecanismo"], "no caza que calle el mecanismo"
    assert not v["valido"]

    # La guarda estricta tiene que LEVANTAR, no solo marcar.
    try:
        redaccion.redactar(lambda _s, _u: inventa, bloque)
        raise AssertionError("`redactar` estricto dejo pasar una norma "
                             "inventada")
    except ValueError as ex:
        assert "Ley 789" in str(ex), f"el mensaje no nombra la norma: {ex}"

    # El pivote sale del motor, no de la imaginacion.
    from reglas import Hechos, estrato_verificacion
    h = Hechos(afectacion_individual=True, otro_medio_judicial=True,
               medio_eficaz=True)
    _est, pivota = estrato_verificacion(h)
    _sis, usr = redaccion.construir_prompt(bloque, pivota, "ciudadano")
    assert "condicion_que_cambiaria_el_mecanismo" in usr, (
        "el prompt no lleva la condicion que cambiaria la via")
    assert "no sirviera en concreto" in usr or "inutil la proteccion" in usr

    # Los dos registros existen y producen prompts distintos.
    _s1, _u1 = redaccion.construir_prompt(bloque, None, "ciudadano")
    _s2, _u2 = redaccion.construir_prompt(bloque, None, "abogado")
    assert _s1 != _s2, "los dos registros dan el mismo prompt"
    try:
        redaccion.construir_prompt(bloque, None, "inexistente")
        raise AssertionError("acepto un registro desconocido")
    except ValueError:
        pass

    return ("caza normas inventadas, mecanismo callado y procedencia "
            "callada; 2 registros; el pivote sale del motor")


@prueba("la prosa del reporte no puede contradecir a sus artefactos")
def t_prosa_del_reporte():
    """Corre `data/autoprueba_reporte.py`, que vigila la seccion 7.

    POR QUE POR SUBPROCESO Y NO COPIADO AQUI
        La comprobacion son ~180 lineas que construyen artefactos sinteticos
        y leen las tres secciones derivadas. Copiarlas aqui las duplica, y
        dos copias divergen en el primer arreglo que se haga a una sola ---
        que es exactamente el defecto que vinieron a vigilar.

    QUE VIGILA
        La seccion 7 del reporte tenia TRES parrafos escritos a mano y los
        tres caducaron en la misma corrida: 7.2 afirmaba que los dos jueces
        eran de la misma familia mientras el artefacto guardaba
        `misma_familia: false`; 7.3 que el brazo del agente fallaba
        `accion_cumplimiento` «por completo» cuando el F1 ya valia 0.3636; y
        7.4 que «los intervalos se solapan» en un estrato que no publica
        intervalo. Ahora las tres se derivan del artefacto, y esto comprueba
        que SIGAN al dato en las cuatro situaciones posibles --- incluida la
        de artefacto ausente --- y que las cabeceras no se puedan volver a
        escribir a mano dentro de `construir()`.

    POR QUE ESTUVO FUERA DE LA SUITE UN RATO
        Porque `corridas.version_codigo()` hashea TODOS los `src/*.py`, y
        registrar una funcion de test aqui movio la huella de
        `84520a06cc4e8a2a` a `dda6de212e018522`: habria dejado sin respaldo
        las tres corridas entregadas, por una prueba que no cambia ningun
        resultado. Vivio en `data/` hasta que la huella cambio por una razon
        de verdad.
    """
    import subprocess

    r = subprocess.run([sys.executable, "-I",
                        str(DATA / "autoprueba_reporte.py")],
                       capture_output=True, text=True, cwd=str(RAIZ))
    salida = (r.stdout or "") + (r.stderr or "")
    assert r.returncode == 0, (
        "el guardia de la prosa del reporte falla:\n"
        + "\n".join(ln for ln in salida.splitlines() if "MAL" in ln)[:600])
    assert "sigue al artefacto en las cuatro situaciones" in salida, (
        f"no llego al final de sus comprobaciones: {salida[-300:]}")
    return ("7.2 sigue al artefacto, 7.3 al F1 por clase, 7.4 distingue "
            "empate de solapamiento; las cabeceras no se reescriben a mano")


@prueba("los tres notebooks estan en orden y enganchan entre si")
def t_orden_de_notebooks():
    """Corre `data/auditar_notebooks.py`: orden, numeracion y dependencias.

    QUE COMPRUEBA, Y POR QUE IMPORTA CADA COSA

      - DEPENDENCIAS ENTRE CELDAS, con `ast`: que ninguna celda use un nombre
        que ninguna anterior defina. Es la unica comprobacion que detecta de
        verdad "el notebook esta en mal orden", porque una celda que necesita
        algo definido doce celdas mas abajo FUNCIONA en la sesion donde se
        escribio --- el kernel ya tenia la variable --- y falla en la primera
        ejecucion limpia, que es la del profesor.
      - NUMERACION DE SECCIONES: ni repetidas, ni fuera de orden, ni con el
        nivel de `#` equivocado para su profundidad.
      - ORDEN DE ARRANQUE: el secreto antes de `arranque.celda`, que es quien
        lo comprueba; el manifiesto despues de montar Drive.
      - ARTEFACTOS: que todo lo que `arranque.ORDEN` declara quede publicado.

    LO QUE ENCONTRO AL ESCRIBIRSE, todo en M1 y todo corregido:
      1. `### 6.1 Abstencion` iba DESPUES de `## 6.2`.
      2. DOS secciones distintas numeradas `6.2` --- una era el segundo
         encabezado de una celda de markdown, y por eso la primera version de
         la auditoria no la vio.
      3. `## 7 Artefactos` duplicado con `## 7 La capa de redaccion`, y la
         cabecera de Artefactos a diez celdas de la celda que publica.
      4. `## 0.1` con nivel de seccion en vez de subseccion.

    La auditoria tambien se equivoco dos veces y las dos quedaron arregladas:
    buscaba `arranque.celda` con una regex sobre el texto crudo y lo
    encontraba DENTRO DE UN COMENTARIO, asi que daba dos "GRAVE" falsos en M1
    y M2. Un auditor que manda a arreglar codigo correcto resta credito a sus
    hallazgos reales.
    """
    import subprocess

    r = subprocess.run([sys.executable, "-I",
                        str(DATA / "auditar_notebooks.py")],
                       capture_output=True, text=True, cwd=str(RAIZ))
    salida = (r.stdout or "") + (r.stderr or "")
    assert r.returncode == 0, (
        "la auditoria de notebooks encuentra hallazgos graves:\n"
        + "\n".join(ln for ln in salida.splitlines()
                    if "GRAVE" in ln)[:600])
    assert "0 hallazgos en total" in salida, (
        "quedan hallazgos no graves sin resolver:\n"
        + "\n".join(ln for ln in salida.splitlines()
                    if "MEDIO" in ln)[:600])
    return ("M1, M2 y M3: sin dependencias adelantadas, numeracion sin "
            "repetir ni desordenar, arranque en orden y nada sin publicar")


@prueba("los tres brazos del motor pueden abstenerse, y con el mismo criterio")
def t_abstencion_del_motor():
    """`schema.PREGUNTA_TRIABLE` y sus dos lectores, fijados.

    POR QUE EXISTE ESTA PRUEBA

    En m3/20261019T173316Z los tres brazos de LLM acertaron 3 de 6
    abstenciones y el brazo del motor 0 de 6, porque el motor siempre
    encuentra una via: `DEFECTO_PRO_HOMINE`. La correccion no toca el motor
    --- sigue decidiendo solo --- sino que le anade al extractor UNA pregunta
    de hecho: si hay o no un caso que triar.

    QUE SE FIJA AQUI, Y POR QUE CADA COSA

      - QUE ESTE EN LOS DOS PROMPTS Y SEA LA MISMA CADENA. `sistema` y
        `agente` tienen prompts de hechos separados y casi identicos. Si la
        pregunta se escribe dos veces, el primer arreglo a una sola deja al
        brazo hibrido y al del agente abstenidose con criterios distintos, y
        nada en la salida lo diria.
      - QUE LOS TRES BRAZOS LA USEN. `SistemaReglas`, `SistemaHibrido` y
        `Agente` son los tres que deciden con el motor. Uno que se quede
        fuera no es un brazo con menos abstenciones: es un brazo que no
        responde a la misma pregunta, y la tabla los compara como si si.
      - QUE EL DEFAULT SEA TRIABLE. Si el JSON se trunca o el modelo ignora
        la clave, no se abstiene. Una abstencion por omision es exactamente
        el error que `DEFECTO_PRO_HOMINE` existe para no cometer.
      - QUE LA SALIDA SEA DETECTABLE. `se_abstuvo` tiene que verla, el
        mecanismo tiene que parsear a None, y las citas tienen que
        desaparecer: afirmar "no determinable" con el art. 49 debajo es
        incoherente, y `metricas` mide la pertinencia de esas citas contra un
        gold que en un caso de abstencion no tiene ninguna.

    LO QUE ESTA PRUEBA NO DICE: si el criterio acierta. Eso solo lo dice una
    corrida, y el numero que lo falsa no es el 0 de 6 --- n=6 no valida nada
    --- sino `abstencion_indebida` sobre los 103 casos CON respuesta
    correcta, que hoy vale 0.0.
    """
    import inspect
    import agente
    import schema
    import sistema

    # 1 · la misma cadena, una vez, en los dos prompts
    p_sis = sistema._prompt_hechos()
    p_ag = schema.con_pregunta_triable(agente.PROMPT_HECHOS_AGENTE)
    for n, p in (("sistema._prompt_hechos", p_sis),
                 ("agente.PROMPT_HECHOS_AGENTE", p_ag)):
        assert schema.PREGUNTA_TRIABLE in p, (
            f"{n}: la pregunta de triabilidad no esta, o se reescribio a mano "
            "en vez de salir de `schema.PREGUNTA_TRIABLE`")
        assert p.count('"caso_triable"') == 1, f"{n}: duplicada"
        assert p.rstrip().endswith("}"), f"{n}: el JSON ya no cierra"

    # 2 · los tres brazos del motor, ninguno fuera
    for cls in (sistema.SistemaReglas, sistema.SistemaHibrido, agente.Agente):
        src = inspect.getsource(cls.__call__)
        assert "schema.abstenerse" in src, (
            f"{cls.__name__} decide con el motor y no puede abstenerse: "
            "la tabla lo compararia con brazos que si")

    # 3 · el default es triable, y las tres formas de false se leen
    for d in ({}, {"derecho": "salud"}, {"caso_triable": True},
              {"caso_triable": "true"}):
        assert schema.leer_triable(d) == (False, ""), (
            f"{d}: una abstencion por omision es el error caro")
    for d in ({"caso_triable": False}, {"caso_triable": "false"},
              {"caso_triable": "no"}):
        assert schema.leer_triable(d)[0] is True, d

    # 4 · la salida que produce es una abstencion para la metrica
    campos = {"derecho": "salud", "fundamento": "art. 49 CP; art. 6 D2591",
              "accionado": "EPS Sanitas", "mecanismo": "tutela",
              "procede": True, "razon": "procede por perjuicio irremediable",
              "pretension": "ordenar la cirugia"}
    assert not schema.se_abstuvo(schema.render_salida(campos))
    ab = schema.render_salida(schema.abstenerse(campos, "pide un pronostico"))
    assert schema.se_abstuvo(ab), ab
    assert schema.parse_salida(ab).get("mecanismo") is None, ab
    assert "art. 49" not in ab, "las citas tenian que desaparecer:\n" + ab
    assert "EPS Sanitas" not in ab, (
        "nombrar al accionado contradice a la razon de la linea siguiente, "
        "que dice que no hay accionado identificable:\n" + ab)

    # 5 · de punta a punta, con un generador falso y sin red
    import json as _json

    def _no_triable(_s, _u):
        return _json.dumps({"derecho": "ninguno", "caso_triable": False,
                            "motivo_no_triable": "pide un pronostico"})

    hib = sistema.SistemaHibrido(_no_triable)
    salida = hib("Quiero saber si la EPS va a cumplir el fallo o no.")
    assert schema.se_abstuvo(salida), salida
    t = hib.trazas[-1]
    assert t["no_triable"] is True and t["mecanismo"] is None, t
    assert t["mecanismo_del_motor"], (
        "la traza tiene que guardar lo que el motor HABRIA dicho: es el dato "
        "que permite ver si la abstencion tapo una via correcta")

    def _triable(_s, _u):
        return _json.dumps({"derecho": "salud", "afectacion_individual": True,
                            "continua_vulneracion": True,
                            "caso_triable": True})

    hib2 = sistema.SistemaHibrido(_triable)
    assert not schema.se_abstuvo(
        hib2("Mi EPS me niega una cirugia urgente y tengo 78 anos.")), (
        "un caso con derecho afectado no puede abstenerse")

    return ("la pregunta es una sola cadena en los 2 prompts, los 3 brazos "
            "del motor la usan, el default es triable y la salida la detecta "
            "`se_abstuvo`")


@prueba("el meta de un set de datos no puede contradecir a sus ejemplos")
def t_meta_contra_ejemplos():
    """Lo que `data/ampliar_categorias.py` rompio en silencio.

    EL FALLO, MEDIDO

    Ese script anadio 17 casos al dataset (143 -> 160), subio la version a
    3.5.0 y NO toco `meta`. Quedo asi:

        meta.splits             {"train": 106, "validation": 37}  suma 143
        real                    {"train": 123, "validation": 37}  suma 160
        meta.balance_mecanismo  sumaba 143 sobre 160 ejemplos

    No se queda en el archivo. La cabecera de M1 citaba «143 ejemplos, 106 de
    train» porque eso es lo que el meta decia, y cualquiera que leyera el
    balance para justificar el tamano de una clase estaba leyendo el reparto
    de una version anterior. Un meta que contradice a sus propios `ejemplos`
    es peor que no tenerlo: parece verificado.

    Es el mismo patron que ya costo dos veces en este proyecto: la cobertura
    leida de `eval_set_v2.json` cuando el vigente era v3, y mi propio
    `baseline_clase_mayoritaria` sin recalcular sobre un conjunto de otra
    composicion. Una cifra derivada que se escribe a mano caduca sin avisar.

    POR QUE EL v1 QUEDA FUERA, Y NO ES UNA EXCEPCION DE CONVENIENCIA

    `eval_set.json` declara `{"tutela": 27, "no_tutela": 19,
    "baseline_clase_mayoritaria": 0.587}`: el esquema BINARIO de antes de que
    el vocabulario fuera de cinco mecanismos, con una proporcion en el mismo
    dict. No esta mal, esta en otro formato --- y v1 es el puente de
    comparacion, que otra prueba exige intacto byte a byte. Reescribirlo
    romperia justo lo que lo hace util. La comprobacion distingue los dos
    casos mirando si las claves son del vocabulario de mecanismos, en vez de
    llevar una lista de excepciones a mano.
    """
    sys.path.insert(0, str(DATA))
    import reparar_meta

    revisados, mal = [], []
    for ruta in sorted(DATA.glob("*.json")):
        d = json.loads(ruta.read_text(encoding="utf-8"))
        if not isinstance(d, dict) or "ejemplos" not in d:
            continue
        if ruta.name in reparar_meta.INTOCABLES:
            continue
        revisados.append(ruta.name)
        for clave, declarado, real in reparar_meta.revisar(ruta):
            mal.append(f"{ruta.name}:{clave} declara "
                       f"{json.dumps(declarado, ensure_ascii=False)} y los "
                       f"ejemplos dan {json.dumps(real, ensure_ascii=False)}")
    assert revisados, "no se encontro ningun set con `ejemplos`"
    assert not mal, (
        "el meta contradice a los ejemplos: " + " · ".join(mal)
        + ". Corre `python -I data/reparar_meta.py --escribir`, y si lo rompio "
          "un script de ampliacion, hazlo recalcular el meta ahi.")

    # Y que el v1 siga reconocido como de otro esquema: si alguien "arregla"
    # su balance al vocabulario nuevo, esta prueba empezaria a exigirselo y el
    # puente de comparacion se reescribiria.
    v1 = json.loads((DATA / "eval_set.json").read_text(encoding="utf-8"))
    assert not reparar_meta._es_vocabulario_de_mecanismos(
        v1["meta"].get("balance_mecanismo")), (
        "el balance del eval v1 paso a usar el vocabulario de mecanismos. "
        "Era binario a proposito: v1 es el puente y no se toca.")
    return (f"{len(revisados)} sets con meta derivado y coherente; el v1 "
            "queda fuera por esquema, no por excepcion")


@prueba("la sonda de validez corre de verdad, no solo esta declarada")
def t_sonda_validez_ejecuta():
    """Los tres `NameError` que costaron una corrida de M2.

    QUE PASO

    `juez.experimento_validez` se escribio, se declaro en `arranque.ORDEN` y
    se integro en una celda de M2. La prueba 56 comprobaba que el artefacto
    estuviera declarado; la 63, que se publicara despues de generarse; la 68,
    que la celda no usara nombres sin definir. Las tres pasaban.

    Y en la corrida 20261021T124137Z la funcion reventó tres veces seguidas:

        NameError: name 'metricas' is not defined          (linea 677)
        ValueError: math domain error                      (bootstrap_ic)
        NameError: name 'cargar_normas' is not defined     (ultima linea)

    El tercero salta DESPUES de gastar las 40 llamadas a la API, que es lo
    caro. M2 se saco adelante con un parche en la celda; el parche ya se
    quito y los imports estan en `juez.py`.

    POR QUE NINGUNA PRUEBA LO VIO, QUE ES LA LECCION

    Ninguna LLAMABA a la funcion. "Declarado y publicado" no es "ejecutado":
    un `import` que falta solo existe en tiempo de ejecucion, y el analisis
    estatico de la prueba 68 mira las celdas del notebook, no el interior de
    los modulos de `src/`.

    No se llamaba porque llamar cuesta API. Esta prueba la llama con un juez
    de mentira --- cuatro llamadas por caso, todas locales --- y asi el coste
    es cero. Se cubren los dos escenarios que importan: margenes variados y
    margenes TODOS IGUALES, que es el que disparaba el `math domain error` y
    es el mas probable con el juez a temperatura 0.
    """
    import json as _json
    import juez
    import schema

    casos = [e for e in _cargar("eval_set_v3.json")
             if e.get("mecanismo")][:4]
    assert len(casos) == 4, "hacen falta 4 casos con mecanismo"

    class JuezDeMentira:
        """Puntua sin red. `constante` imita al juez a temperatura 0."""

        def __init__(self, constante):
            self.constante = constante
            self.modelo = "de-mentira"
            self.n = 0

        def guardar_cache(self):
            pass

        def puntuar(self, relato, referencia, respuesta):
            self.n += 1
            intacta = respuesta == referencia
            if self.constante:
                nota = 5 if intacta else 2
            else:
                nota = (5 if intacta else 2) - (self.n % 2)
            return {"nota": nota, "justificacion": "de mentira"}

    for constante in (True, False):
        j = JuezDeMentira(constante)
        # Si falta un import, esto levanta NameError y la prueba falla aqui.
        val = juez.experimento_validez(j, casos, schema.render_salida, n=4)

        assert j.n == 4 * 4, f"esperaba 16 llamadas, hubo {j.n}"
        assert val["n"] == 4 and val["llamadas"] == 16, val
        assert set(val["por_modo"]) == {"mecanismo_cambiado", "norma_inventada",
                                        "razonamiento_vacio"}, val["por_modo"]
        # El margen del mecanismo tiene que ser POSITIVO con este juez, que
        # por construccion castiga la respuesta degradada.
        assert val["margen_por_mecanismo"] > 0, val["margen_por_mecanismo"]
        # Y el `ic_margen` tiene que existir sin reventar en los dos casos.
        ic = val["por_modo"]["mecanismo_cambiado"]["ic_margen"]
        assert isinstance(ic, dict), ic
        if constante:
            assert ic["metodo"] == "sin estimar", (
                "con los margenes todos iguales el intervalo no se puede "
                f"estimar, y `bootstrap_ic` devolvio {ic.get('metodo')}. Si "
                "esto es `wilson`, volvio el `math domain error`: Wilson solo "
                "esta definido para una proporcion")
        # La ultima linea de la funcion, que es donde saltaba el tercer bug.
        assert val["norma_falsa_sigue_fuera_del_whitelist"] is True, (
            f"`{val['norma_falsa_usada']}` entro al whitelist: la degradacion "
            "`norma_inventada` ya no degrada nada")
        _json.dumps(val)        # el artefacto tiene que ser serializable

    # Y que los imports esten DONDE se usan, no parcheados desde una celda.
    import inspect
    fuente = inspect.getsource(juez)
    assert "import metricas" in fuente, (
        "`juez.py` usa `metricas` y no lo importa. M2 lo parcheaba desde la "
        "celda; el parche se quito")
    assert "cargar_normas" in fuente.split("def experimento_validez")[0], (
        "`cargar_normas` se usa y no se importa arriba")

    return ("`experimento_validez` corre con juez de mentira en los dos "
            "escenarios (margenes variados e iguales), 16 llamadas, sin API")


@prueba("la huella de un notebook no depende de quien lo escribio")
def t_canonico_convergente():
    """Dos bytes que pararon una corrida, dos veces.

    EL FALLO

    `manifiesto._canonico` quitaba el salto de linea de la ULTIMA linea de
    cada celda y, si quedaba vacia, la eliminaba --- y ahi paraba. Un escritor
    que deja un elemento vacio al final deja el `\n` de la linea de verdad sin
    normalizar, porque el vacio lo escudaba del `rstrip`.

    Y `texto.split("\n")` produce ese vacio SIEMPRE que el texto termine en
    salto, que es como se escribe un script normal. Asi que el mismo notebook
    pesaba 105805 escrito por nosotros y 105803 guardado por Colab, y la celda
    4 de M1 paro la corrida nombrando un archivo que estaba bien subido. Es la
    segunda vez: la primera fue `M2_harness.ipynb`, 48257 contra 48255.

    QUE SE FIJA

    Para los tres notebooks reales, que las tres formas de escribir el mismo
    contenido den la MISMA huella:

        ["x\n"]        como lo guarda nbformat/Colab
        ["x\n", ""]    como lo deja `split("\n")`
        ["x"]          sin salto final

    Si alguna divergiera, el guardian se dispararia sin que nadie edite nada
    --- y un guardian que salta solo ensena a ignorarlo, que es peor que no
    tenerlo.
    """
    import copy
    import json as _json
    import tempfile
    sys.path.insert(0, str(DATA))
    import manifiesto as man

    for nombre in ("M1_finetuning", "M2_harness", "M3_rag"):
        p = RAIZ / "notebooks" / f"{nombre}.ipynb"
        base = man._canonico(p)
        nb = _json.loads(p.read_bytes())

        variantes = {}
        # a) estilo nbformat: cada linea con su salto, la ultima como venga.
        v = copy.deepcopy(nb)
        for c in v["cells"]:
            if isinstance(c.get("source"), list) and c["source"]:
                c["source"] = "".join(c["source"]).splitlines(keepends=True)
        variantes["nbformat"] = v
        # b) estilo `split("\n")`: elemento vacio al final si termina en salto.
        v = copy.deepcopy(nb)
        for c in v["cells"]:
            if isinstance(c.get("source"), list) and c["source"]:
                ls = "".join(c["source"]).split("\n")
                c["source"] = [x + "\n" for x in ls[:-1]] + [ls[-1]]
        variantes["split"] = v
        # c) sin ningun salto final.
        v = copy.deepcopy(nb)
        for c in v["cells"]:
            if isinstance(c.get("source"), list) and c["source"]:
                ls = "".join(c["source"]).splitlines()
                c["source"] = [x + "\n" for x in ls[:-1]] + ([ls[-1]] if ls else [])
        variantes["sin_salto"] = v

        tmp = Path(tempfile.mkdtemp(prefix="prueba_canon_"))
        try:
            for etiqueta, v in variantes.items():
                q = tmp / f"{etiqueta}.ipynb"
                q.write_text(_json.dumps(v, ensure_ascii=False, indent=1) + "\n",
                             encoding="utf-8")
                assert man._canonico(q) == base, (
                    f"{nombre}: la variante `{etiqueta}` da "
                    f"{len(man._canonico(q))} bytes canonicos y el archivo da "
                    f"{len(base)}. La huella depende de quien escribio el "
                    "notebook, asi que el guardian se dispara sin que nadie "
                    "edite nada.")
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)

    return ("3 notebooks x 3 formas de escribir el source -> la misma huella "
            "canonica")


@prueba("el few-shot del baseline no filtra el eval ni ensena una clase")
def t_few_shot():
    """El brazo que le quita al baseline la excusa del formato.

    QUE MIDE EL BRAZO

    El base acierta el mecanismo en 32.0% y los dos campos en 1.9%: 36 de 103
    salidas tienen el mecanismo ilegible. Un baseline que falla por formato es
    un hombre de paja. Este brazo le ensena el esquema por demostracion --- lo
    unico que cambia --- para que la comparacion con el afinado sea sobre el
    razonamiento.

    LAS DOS COSAS QUE PUEDEN ARRUINARLO, Y QUE ESTO FIJA

      1. FUGA. Una demostracion que este en el eval set convierte la cifra en
         memorizacion: el modelo no acierta el caso, lo lleva en su prompt.
      2. UNA CLASE EN VEZ DE UN FORMATO. Con tres ejemplos, si los tres son
         del mismo mecanismo --- o si son los tres RAROS, que es lo que daba
         el orden alfabetico --- el prompt empuja la respuesta y el brazo mide
         el sesgo del few-shot. Por eso van los mas frecuentes del train:
         `tutela` y `via_ordinaria` son 92 de los 142 etiquetados y son el par
         entre el que el modelo colapsa.

    Y deterministas: dos corridas tienen que mandar el mismo prompt, o la
    celda de estabilidad mide el muestreo del few-shot en vez del modelo.
    """
    tr = json.loads((DATA / "dataset.json").read_text(encoding="utf-8"))
    tr = tr["ejemplos"]
    ids_eval = set()
    for a in ("eval_set.json", "eval_set_v2.json", "eval_set_v3.json",
              "eval_set_m3.json"):
        ids_eval |= {c["id"] for c in _cargar(a)}

    dem = schema.demostraciones_few_shot(tr, ids_eval)
    assert len(dem) == schema.N_FEW_SHOT, f"{len(dem)} demostraciones"

    # 1 · ninguna en NINGUN eval set, ni por id ni por relato.
    relatos_eval = {c["relato"].strip() for a in
                    ("eval_set.json", "eval_set_v2.json", "eval_set_v3.json",
                     "eval_set_m3.json") for c in _cargar(a)}
    for d in dem:
        assert d["id"] not in ids_eval, f"{d['id']} esta en un eval set"
        assert d["relato"].strip() not in relatos_eval, \
            f"{d['id']}: su relato esta en un eval set con otro id"

    # 2 · mecanismos distintos, y los frecuentes presentes.
    mecs = [d["mecanismo"] for d in dem]
    assert len(set(mecs)) == len(mecs), f"mecanismo repetido: {mecs}"
    assert {"tutela", "via_ordinaria"} <= set(mecs), (
        f"el few-shot no demuestra tutela ni via_ordinaria ({mecs}): son 92 "
        "de 142 en el train y el par donde el modelo colapsa, asi que un "
        "prompt sin ellos empuja la respuesta en vez de ensenar el formato")
    assert all(d.get("mecanismo") for d in dem), \
        "una demostracion de abstencion ensena otro formato"

    # 3 · deterministas.
    assert [d["id"] for d in schema.demostraciones_few_shot(tr, ids_eval)] == \
        [d["id"] for d in dem], "la seleccion no es determinista"

    # 4 · y el prohibido se respeta de verdad.
    sin_primero = schema.demostraciones_few_shot(
        tr, ids_eval | {dem[0]["id"]})
    assert dem[0]["id"] not in [d["id"] for d in sin_primero], \
        "ids_prohibidos no excluye"

    # 5 · la forma de los mensajes: el sistema es el MISMO que el del brazo
    # base, y el ultimo turno es el caso a resolver, sin su respuesta.
    caso = next(c for c in _cargar("eval_set_v3.json") if c["mecanismo"])
    msgs = schema.mensajes_few_shot("SISTEMA DEL BRAZO BASE", caso, dem)
    assert [m["role"] for m in msgs] == (
        ["system"] + ["user", "assistant"] * len(dem) + ["user"]), \
        [m["role"] for m in msgs]
    assert msgs[0]["content"] == "SISTEMA DEL BRAZO BASE", (
        "mensajes_few_shot reescribe la instruccion: los dos brazos tienen "
        "que llevar el mismo `system` o la diferencia medida es la del prompt")
    ultimo = msgs[-1]["content"]
    assert caso["relato"] in ultimo, "el ultimo turno no trae el caso"
    assert schema.render_salida(caso) not in ultimo, \
        "el ultimo turno trae la RESPUESTA del caso a resolver"

    return (f"{len(dem)} demostraciones del train ({', '.join(mecs)}), "
            f"0 en los 4 eval sets, deterministas")


@prueba("la validacion del abogado caduca con la corrida, y lo dice")
def t_validacion_caduca():
    """La guarda que hace falta justo antes de volver a correr los notebooks.

    EL FALLO QUE EVITA

    `validacion_juez.py --leer` emparejaba por `id` y nada mas: la nota del
    abogado de la fila `A07` del formulario contra la nota del juez de la fila
    `A07` del CSV vigente. El abogado puntuo la respuesta que tenia delante.
    Si se vuelve a correr M1 la respuesta cambia, y `--leer` seguiria dando una
    kappa --- entre la lectura que el abogado hizo de una salida y la nota que
    el juez puso a OTRA ---. Un numero plausible y sin sentido.

    Y no hacia falta un archivo paralelo: la columna `respuesta_del_sistema`
    del formulario que el abogado devolvio lleva el texto que vio. La guarda
    es comparar.

    QUE SE FIJA AQUI

      1. Con la respuesta intacta, `_casos_que_se_movieron` no inventa un
         desacuerdo. Una guarda que salta siempre se desactiva en una semana.
      2. Si la respuesta cambia, lo detecta.
      3. Si el formulario no trae la columna, dice que NO SE PUEDE comprobar
         en vez de dar por bueno lo que no miro.
      4. `leer()` devuelve 1 y no escribe el artefacto cuando algo se movio.
    """
    sys.path.insert(0, str(DATA))
    import validacion_juez as vj

    respuestas = vj._respuestas()
    # UN ID QUE ESTE EN EL FORMULARIO, no solo en el CSV del juez.
    #
    # Esto tomaba el primer id de `_filas_del_juez()`, que son los 109 casos
    # puntuados; el formulario tiene la MUESTRA de 25. El caso elegido no
    # estaba en el formulario, `leer()` no encontraba nada movido y la prueba
    # fallaba sobre una guarda correcta.
    sys.path.insert(0, str(DATA))
    import formularios as _f
    _ruta = next(p for p in (vj.SALIDA.with_suffix(".xlsx"),
                             vj.SALIDA.with_suffix(".csv")) if p.exists())
    _form = _f.leer(_ruta, vj.COLUMNAS_PERSONA)["filas"]
    cid = next(x["id"] for x in _form
               if (x.get("nota") or "").strip() and x["id"] in respuestas)

    # 1 · intacta: no se mueve nada.
    fila = {"id": cid, "nota": "4",
            "respuesta_del_sistema": respuestas[cid]}
    assert vj._casos_que_se_movieron([fila]) == [], \
        "la guarda marca como movido un caso cuya respuesta es la vigente"

    # Y los finales de linea que Excel reescribe no son un cambio.
    fila_crlf = dict(fila, respuesta_del_sistema=str(
        respuestas[cid]).replace("\n", "\r\n") + "\n")
    assert vj._casos_que_se_movieron([fila_crlf]) == [], \
        "la guarda confunde el CRLF de Excel con un cambio de la respuesta"

    # 2 · la respuesta cambio.
    m = vj._casos_que_se_movieron(
        [dict(fila, respuesta_del_sistema="Mecanismo: otra cosa")])
    assert len(m) == 1 and "cambio" in m[0]["que_cambio"], \
        f"no detecta que la respuesta puntuada ya no existe: {m}"

    # 3 · formulario sin la columna: se declara, no se da por bueno.
    m = vj._casos_que_se_movieron([{"id": cid, "nota": "4"}])
    assert len(m) == 1 and "no se puede comprobar" in m[0]["que_cambio"], \
        f"un formulario sin la columna pasa como valido: {m}"

    # 4 · sin nota no hay nada que invalidar: el abogado no puntuo esa fila.
    assert vj._casos_que_se_movieron(
        [{"id": cid, "nota": "", "respuesta_del_sistema": "cualquier cosa"}]) \
        == [], "invalida una fila que nadie puntuo"

    # 5 · y `leer()` se niega de verdad, sin tocar el artefacto.
    import shutil
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="prueba_caduca_"))
    orig_preds, orig_out = vj.PREDS, vj.RUTA_OUT
    antes = (vj.RUTA_OUT.read_bytes() if vj.RUTA_OUT.exists() else None)
    try:
        # Unas predicciones con la respuesta cambiada, y nada mas.
        d = json.loads(orig_preds.read_text(encoding="utf-8"))
        filas = d.get("datos", d) if isinstance(d, dict) else d
        for p in filas:
            if p["id"] == cid:
                p["finetuned"] = "Mecanismo: otra cosa"
        vj.PREDS = tmp / "m1_predicciones.json"
        vj.PREDS.write_text(json.dumps(d, ensure_ascii=False),
                            encoding="utf-8")
        vj.RUTA_OUT = tmp / "validacion_juez.json"
        assert vj.leer() == 1, \
            "`--leer` publica una kappa con las notas de otra corrida"
        assert not vj.RUTA_OUT.exists(), \
            "`--leer` escribio el artefacto aunque las notas no son validas"
    finally:
        vj.PREDS, vj.RUTA_OUT = orig_preds, orig_out
        if antes is not None:
            vj.RUTA_OUT.write_bytes(antes)
        shutil.rmtree(tmp, ignore_errors=True)

    return (f"intacta no salta, CRLF tampoco, respuesta cambiada y columna "
            f"ausente si · `leer()` devuelve 1 sin escribir el artefacto")


@prueba("depurar las citas no puede mover el acierto juridico")
def t_depurar_citas():
    """La capa que quita citas imposibles, y la comprobacion que la limita.

    QUE HACE Y POR QUE EXISTE

    El modelo emite `art. 6.1 Decreto 2591` --- la causal de SUBSIDIARIEDAD
    --- en el slot del derecho de casos que no son `via_ordinaria`. No es una
    cita discutible: es un error de categoria, porque ningun numeral del art.
    6 dice que derecho esta en juego. Y lo emite porque 59 de 123 ejemplos de
    entrenamiento se lo ensenan (`data/causas_abiertas.json`): el objetivo
    fusiona `fundamento_del_derecho` con `fundamento_del_mecanismo`.

    Medido sobre las 109 salidas: quita 13 citas impertinentes, no pierde
    ninguna correcta, y `precision_citas` pasa de 0.5506 a 0.5939 con el
    recall intacto.

    LO QUE ESTA PRUEBA FIJA, Y ES LO IMPORTANTE

      1. `acierto_juridico` IDENTICO con y sin depurar. Si cambiara, la capa
         estaria tocando el mecanismo o la procedencia, y entonces seria
         maquillaje y no limpieza.
      2. NO quita la norma que SI corresponde al mecanismo emitido. La
         primera version quitaba todas las procesales y tiraba 12 citas que
         el gold cuenta como correctas: el recall bajaba de 0.4135 a 0.3629.
         El gold tiene UN solo slot, asi que para `via_ordinaria` el art. 6.1
         es lo que pide.
      3. No anade citas nunca. Anadir seria decidir el fundamento, que es lo
         que hacen los brazos del motor: otro brazo, no una depuracion.
    """
    import metricas
    import schema as schema_mod
    schema = schema_mod

    base = {"derecho": "salud", "accionado": "EPS", "procede": True,
            "razon": "procede", "pretension": "ordenar la cirugia"}

    # 1 - la causal de OTRO mecanismo se quita
    t = schema.render_salida({**base, "mecanismo": "tutela",
                              "fundamento": "art. 49 CP; art. 6.1 Decreto 2591 de 1991"})
    dep, quit_ = schema.depurar_citas(t)
    assert quit_ == ["art. 6.1 Decreto 2591 de 1991"], quit_
    assert "art. 49 CP" in dep and "6.1" not in dep, dep

    # 2 - la que SI corresponde al mecanismo emitido se queda
    vo = schema.render_salida({**base, "mecanismo": "via_ordinaria",
                               "procede": False,
                               "fundamento": "art. 48 CP; art. 6.1 Decreto 2591 de 1991"})
    dep2, quit2 = schema.depurar_citas(vo)
    assert quit2 == [], (
        "quito la causal del mecanismo que la salida SI emite. El gold tiene "
        "un solo slot de fundamento: para `via_ordinaria` el art. 6.1 es lo "
        f"que pide, y quitarlo baja el recall. Quito: {quit2}")
    assert dep2 == vo, "toco una salida que no habia que tocar"

    # 3 - una salida sin citas procesales queda intacta
    limpia = schema.render_salida({**base, "mecanismo": "tutela",
                                   "fundamento": "art. 49 CP; Ley 1751 de 2015"})
    assert schema.depurar_citas(limpia) == (limpia, [])

    # 4 - si no queda ninguna cita, el parentesis desaparece
    sola = schema.render_salida({**base, "mecanismo": "tutela",
                                 "fundamento": "art. 6.1 Decreto 2591 de 1991"})
    dep4, _ = schema.depurar_citas(sola)
    assert "()" not in dep4 and "Derecho: salud" in dep4, dep4

    # 5 - LA COMPROBACION QUE LIMITA LA CAPA: el acierto no se mueve
    casos = [e for e in _cargar("eval_set_v3.json") if e.get("mecanismo")][:20]
    salidas, deps = [], []
    for i, e in enumerate(casos):
        # se corrompe la cita de la mitad, dejando el mecanismo intacto
        f = e.get("fundamento") or "art. 49 CP"
        if i % 2:
            f += "; art. 6.3 Decreto 2591 de 1991"
        x = schema.render_salida({**e, "fundamento": f})
        salidas.append(x)
        deps.append(schema.depurar_citas(x)[0])
    a = metricas.acierto_juridico([schema.parse_salida(x) for x in salidas], casos)
    b = metricas.acierto_juridico([schema.parse_salida(x) for x in deps], casos)
    assert a == b, (
        f"depurar movio el acierto juridico de {a} a {b}. La capa solo puede "
        "quitar citas; si toca el mecanismo o la procedencia es maquillaje")

    # 6 - y el scorecard publica LAS DOS, no solo la depurada
    sc = metricas.scorecard(salidas, casos, "prueba")
    assert "pertinencia_citas" in sc and "pertinencia_citas_depurada" in sc, (
        "el scorecard tiene que publicar la cruda Y la depurada: solo la "
        "depurada presentaria como mejora del modelo una capa de limpieza")
    return ("quita la causal de otro mecanismo, conserva la del propio, y el "
            "acierto juridico sale identico con y sin depurar")


# ==========================================================================
def main() -> int:
    print("=" * 84)
    print("  AUTOPRUEBA DE INTEGRACION · toda la fontaneria, sin GPU ni API")
    print("=" * 84)
    fallos = []
    for i, (nombre, fn) in enumerate(PRUEBAS, 1):
        try:
            detalle = fn() or ""
            print(f"  [{i:2d}] OK    {nombre}")
            if detalle:
                print(f"            {detalle}")
        except AssertionError as ex:
            fallos.append((nombre, str(ex)))
            print(f"  [{i:2d}] FALLA {nombre}")
            print(f"            {ex}")
        except Exception as ex:                       # noqa: BLE001
            fallos.append((nombre, f"{type(ex).__name__}: {ex}"))
            print(f"  [{i:2d}] ERROR {nombre}")
            print(f"            {type(ex).__name__}: {ex}")
    print("=" * 84)
    if fallos:
        print(f"  {len(fallos)} de {len(PRUEBAS)} pruebas fallaron:")
        for n, e in fallos:
            print(f"    - {n}: {e[:150]}")
        print("=" * 84)
        return 1
    print(f"  las {len(PRUEBAS)} pruebas pasan.")
    print()
    print("  Lo que esto NO dice: si el modelo degenera en los 23 casos nuevos,")
    print("  si el juez se atraganta con `mecanismo: null`, si Groq devuelve un")
    print("  400, ni si los arreglos del presupuesto del agente sirven. Para eso")
    print("  hace falta correr M1, M2 y M3 de verdad.")
    print("=" * 84)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
