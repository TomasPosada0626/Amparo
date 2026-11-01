"""Tests del pipeline de M2 (amparo/pipelines/m2_harness.py) y de
amparo/evaluacion/acuerdo.py. Sin red: juez, cliente de Groq y corrida son dobles.

LO QUE NO SE EJECUTA AQUI DE VERDAD (necesita Groq y se corre en Colab):
`elegir_juez` con el `Juez` real, las sondas de sesgo (`sesgo_posicion`,
`sesgo_longitud`, `autopreferencia`, `inyeccion`, `validez`) contra el modelo,
`harness_completo` y `reproducibilidad` con notas reales del juez, y
`preparar()` (Drive, sello y secretos de Colab).
"""
from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import pytest

from amparo.evaluacion import acuerdo
from amparo.ejecucion import arranque
from amparo.nucleo import schema
from amparo.pipelines import m2_harness as m2


@pytest.fixture(autouse=True)
def sin_clave(monkeypatch):
    """Ningun test puede depender de GROQ_API_KEY (ni llamar a la API)."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)


# --------------------------------------------------------------------------
# Dobles
# --------------------------------------------------------------------------
class JuezFalso:
    """`puntuar` devuelve la nota de `guion(i)`; None = hueco; 'x' = excepcion."""

    def __init__(self, modelo, guion=lambda i: 4):
        self.modelo, self.guion, self.llamadas = modelo, guion, 0

    def puntuar(self, relato, referencia, salida):
        i = self.llamadas
        self.llamadas += 1
        nota = self.guion(i)
        if nota == "x":
            raise RuntimeError("400 de la API")
        return {"nota": nota}


class ClienteFalso:
    def __init__(self, servidos, respuesta="Derecho: salud"):
        self.servidos, self.respuesta, self.creadas = servidos, respuesta, 0
        cli = self

        class _Models:
            @staticmethod
            def list():
                return type("R", (), {"data": [type("M", (), {"id": m}) for m in cli.servidos]})

        class _Completions:
            @staticmethod
            def create(**kw):
                cli.creadas += 1
                msg = type("Msg", (), {"content": f"{cli.respuesta} ({kw['model']})"})
                return type("Resp", (), {"choices": [type("Ch", (), {"message": msg})]})

        self.models = _Models
        self.chat = type("Chat", (), {"completions": _Completions})


class CorridaFalsa:
    def __init__(self, carpeta: Path, id_="20261101T000000Z"):
        self.dir = carpeta / id_
        self.dir.mkdir(parents=True)
        self.id = id_
        self.artefactos, self.publicados, self.notas = {}, [], []
        self.meta = {"datos": {"eval_set_v3.json": "h1"}, "codigo": {"_conjunto": "c1"},
                     "hardware": {"gpu": None}}
        self.cerrada = None

    def guardar_json(self, nombre, obj):
        (self.dir / f"{nombre}.json").write_text(json.dumps(obj, default=str), encoding="utf-8")
        self.artefactos[nombre] = f"{nombre}.json"

    def guardar_csv(self, nombre, filas):
        (self.dir / f"{nombre}.csv").write_text("x", encoding="utf-8")
        self.artefactos[nombre] = f"{nombre}.csv"

    def ruta_cache(self, nombre):
        return str(self.dir / nombre)

    def nota(self, t):
        self.notas.append(t)

    def publicar(self, nombre, destino):
        self.publicados.append((nombre, destino))

    def cerrar(self, valida, notas=None):
        self.cerrada = (valida, notas)


EJEMPLOS = [{"id": f"E{i:02d}", "relato": f"relato {i}", "derecho": "salud", "accionado": "EPS",
             "mecanismo": "tutela", "procede": True, "razon": "r", "pretension": "p"}
            for i in range(30)]
SALIDAS = [schema.render_salida(e) for e in EJEMPLOS]


# --------------------------------------------------------------------------
# acuerdo.puntuar_muestra
# --------------------------------------------------------------------------
def test_puntuar_muestra_sin_fallos_puntua_los_n():
    j = JuezFalso("a")
    notas, huecos = acuerdo.puntuar_muestra(j, EJEMPLOS, SALIDAS, n=25)
    assert len(notas) == 25 and huecos == 0 and j.llamadas == 25


def test_puntuar_muestra_un_fallo_aislado_deja_un_hueco_y_sigue():
    j = JuezFalso("a", lambda i: None if i == 3 else ("x" if i == 7 else 4))
    notas, huecos = acuerdo.puntuar_muestra(j, EJEMPLOS, SALIDAS, n=25)
    assert len(notas) == 25 and huecos == 2
    assert notas[3]["nota"] is None and notas[7]["nota"] is None


def test_puntuar_muestra_abandona_tras_tres_fallos_seguidos_sin_gastar_el_resto():
    j = JuezFalso("a", lambda i: None if 4 <= i <= 6 else 4)
    notas, huecos = acuerdo.puntuar_muestra(j, EJEMPLOS, SALIDAS, n=25)
    assert notas is None and huecos == 3 and j.llamadas == 7


# --------------------------------------------------------------------------
# acuerdo.medir: la busqueda del segundo juez
# --------------------------------------------------------------------------
SERVIDOS = ["llama-3.3-70b-versatile", "openai/gpt-oss-20b", "allam-2-7b"]


def _fabrica(guiones):
    construidos = []

    def construir(m):
        if guiones.get(m) == "no_construye":
            raise RuntimeError("modelo retirado")
        j = JuezFalso(m, guiones.get(m, lambda i: 4))
        construidos.append(m)
        return j
    return construir, construidos


def test_candidatos_otra_familia_primero_y_sin_modelos_que_no_juzgan():
    orden = acuerdo.candidatos(ClienteFalso(SERVIDOS + ["whisper-large-v3"]), "openai/gpt-oss-120b")
    assert orden == ["llama-3.3-70b-versatile", "allam-2-7b", "openai/gpt-oss-20b"]


def test_candidatos_sin_poder_listar_usa_la_lista_de_juez():
    class Roto:
        class models:
            @staticmethod
            def list():
                raise RuntimeError("sin red")
    assert set(acuerdo.candidatos(Roto, "openai/gpt-oss-120b")) <= set(acuerdo._juez.MODELOS_ALTERNATIVOS)


def test_medir_elige_el_primer_candidato_limpio_de_otra_familia():
    construir, construidos = _fabrica({})
    a = acuerdo.medir(JuezFalso("openai/gpt-oss-120b"), EJEMPLOS, SALIDAS,
                      cliente=ClienteFalso(SERVIDOS), construir_juez=construir)
    assert construidos == ["llama-3.3-70b-versatile"]
    assert a["_familias"]["misma_familia"] is False and a["_familias"]["familia_b"] == "llama"
    assert "acuerdo_entre_familias" not in a          # el cruzado ES el elegido


def test_medir_exige_los_25_sin_huecos_y_conserva_al_de_otra_familia():
    guiones = {"llama-3.3-70b-versatile": lambda i: None if i == 0 else 4,
               "allam-2-7b": lambda i: None if i in (0, 9) else 3}
    construir, construidos = _fabrica(guiones)
    a = acuerdo.medir(JuezFalso("openai/gpt-oss-120b"), EJEMPLOS, SALIDAS,
                      cliente=ClienteFalso(SERVIDOS), construir_juez=construir)
    assert construidos == ["llama-3.3-70b-versatile", "allam-2-7b", "openai/gpt-oss-20b"]
    assert a["_familias"]["misma_familia"] is True          # gpt-oss-20b, pariente
    assert a["_familias"]["por_que_no_otra_familia"]
    cruz = a["acuerdo_entre_familias"]
    assert cruz["modelo_b"] == "llama-3.3-70b-versatile" and cruz["sin_nota"] == 1
    assert "incumple_generoso" in cruz["adherencia_juez_cruzado"]
    motivos = {d["modelo"]: d["motivo"] for d in a["_familias"]["descartados"]}
    assert motivos == {"llama-3.3-70b-versatile": "1 de 25 sin nota", "allam-2-7b": "2 de 25 sin nota"}


def test_medir_sin_ninguno_limpio_usa_el_menos_malo_y_lo_declara():
    guiones = {m: (lambda k: (lambda i: None if i < k else 4))(k)
               for m, k in zip(SERVIDOS, (2, 1, 2))}
    construir, _ = _fabrica(guiones)
    a = acuerdo.medir(JuezFalso("openai/gpt-oss-120b"), EJEMPLOS, SALIDAS,
                      cliente=ClienteFalso(SERVIDOS), construir_juez=construir)
    assert a["sin_nota_en_alguno"] == 1                     # gpt-oss-20b, 1 hueco


def test_medir_sin_segundo_juez_devuelve_none():
    guiones = {"llama-3.3-70b-versatile": "no_construye",
               "allam-2-7b": lambda i: None, "openai/gpt-oss-20b": lambda i: "x"}
    construir, _ = _fabrica(guiones)
    assert acuerdo.medir(JuezFalso("openai/gpt-oss-120b"), EJEMPLOS, SALIDAS,
                         cliente=ClienteFalso(SERVIDOS), construir_juez=construir) is None


def test_medir_para_si_el_juez_principal_no_puntua():
    with pytest.raises(SystemExit, match="juez principal"):
        acuerdo.medir(JuezFalso("openai/gpt-oss-120b", lambda i: None), EJEMPLOS, SALIDAS,
                      cliente=ClienteFalso(SERVIDOS), construir_juez=_fabrica({})[0])


# --------------------------------------------------------------------------
# Etapas que corren sin red
# --------------------------------------------------------------------------
@pytest.fixture
def ctx_con_salidas(tmp_path):
    """Contexto con las predicciones de M1 fabricadas sobre el eval set real:
    ajustado acierta salvo cada quinto caso; base siempre dice via_ordinaria."""
    ev = schema.cargar(archivo="eval_set_v3.json")
    preds = []
    for i, e in enumerate(ev):
        ft = dict(e, mecanismo=("via_ordinaria" if e["mecanismo"] != "via_ordinaria" else "tutela")
                  if i % 5 == 0 else e["mecanismo"])
        preds.append({"id": e["id"], "base": schema.render_salida(dict(e, mecanismo="via_ordinaria")),
                      "finetuned": schema.render_salida(ft)})
    ruta = tmp_path / "m1_predicciones.json"
    ruta.write_text(json.dumps({"_corrida": "20261018T070145Z", "datos": preds}), encoding="utf-8")
    ctx = m2.Contexto(c=CorridaFalsa(tmp_path / "runs" / "m2"))
    m2.cargar_salidas(ctx, ruta)
    return ctx


def test_cargar_salidas_trae_el_eval_set_y_la_corrida_de_m1(ctx_con_salidas):
    ctx = ctx_con_salidas
    assert len(ctx.sal_ft) == len(ctx.eval_set) == len(ctx.sal_base) > 0
    assert ctx.corrida_m1 == "20261018T070145Z"


def test_formato_vocabulario_mide_las_tres_en_los_dos_brazos(ctx_con_salidas):
    out = m2.formato_vocabulario(ctx_con_salidas)
    assert set(out) == {"adherencia estructural", "adherencia vocabulario", "coherencia"}
    for v in out.values():
        for x in v.values():
            assert x is None or 0.0 <= x <= 1.0


def test_rouge_vs_acierto_separa_aciertos_de_fallos_y_lo_guarda(ctx_con_salidas):
    res = m2.rouge_vs_acierto(ctx_con_salidas)
    assert 0 <= res["medio_falla"] <= 1 and 0 <= res["medio_acierta"] <= 1
    assert 0 < len(res["enganosos"]) <= 6
    assert "rouge_vs_acierto" in ctx_con_salidas.c.artefactos


def test_elegir_juez_cae_a_un_alternativo_y_para_si_no_hay_ninguno(ctx_con_salidas):
    ctx = ctx_con_salidas

    def construir(m=None):
        if m is None:
            raise RuntimeError("modelo por defecto retirado")
        return JuezFalso(m)
    m2.elegir_juez(ctx, construir)
    assert ctx.j.modelo == acuerdo._juez.MODELOS_ALTERNATIVOS[0]

    def nunca(m=None):
        raise RuntimeError("sin servicio")
    with pytest.raises(SystemExit, match="Ningun modelo de juez"):
        m2.elegir_juez(ctx, nunca)


def test_respuestas_familia_usa_el_cache_en_la_segunda_pasada(tmp_path):
    cli = ClienteFalso([], respuesta=SALIDAS[0])
    ruta = tmp_path / "autopreferencia.json"
    sal, nuevas = m2.respuestas_familia(cli, "openai/gpt-oss-20b", EJEMPLOS[:4], ruta)
    assert len(sal) == 4 and nuevas == 4 and cli.creadas == 4
    sal2, nuevas2 = m2.respuestas_familia(cli, "openai/gpt-oss-20b", EJEMPLOS[:4], ruta)
    assert sal2 == sal and nuevas2 == 0 and cli.creadas == 4


def test_limpiar_quita_el_entorno_sin_tocar_el_original():
    sc = {"a": 1, "entorno": {"gpu": "x"}}
    assert m2.limpiar(sc) == {"a": 1} and "entorno" in sc


def _corrida_previa(carpeta, nombre, notas, con_csv=True):
    p = carpeta / nombre
    p.mkdir(parents=True)
    (p / "corrida.json").write_text(json.dumps({"notas": notas, "codigo": {"_conjunto": "c0"},
                                                "datos": {"eval_set_v3.json": "h1"}}), encoding="utf-8")
    if con_csv:
        (p / "scorecard_por_caso.csv").write_text("id\nx\n", encoding="utf-8")
    return p


def test_corridas_previas_salta_las_de_control_y_las_sin_scorecard(tmp_path):
    carpeta = tmp_path / "m2"
    _corrida_previa(carpeta, "20261001T000000Z", ["predicciones de la corrida m1: A"])
    _corrida_previa(carpeta, "20261002T000000Z", ["corrida de CONTROL"])
    _corrida_previa(carpeta, "20261003T000000Z", [], con_csv=False)
    _corrida_previa(carpeta, "20261101T000000Z", [])          # la actual
    previas = m2.corridas_previas(carpeta, "20261101T000000Z")
    assert [p.name for p, _ in previas] == ["20261001T000000Z"]


def test_estabilidad_sin_corrida_previa_es_none_y_no_true(tmp_path):
    est = m2.estabilidad(CorridaFalsa(tmp_path), [], "A")
    assert est["identicas"] is None and est["concluyente"] is False


def test_estabilidad_atribuye_codigo_y_predicciones_de_m1(tmp_path, monkeypatch):
    c = CorridaFalsa(tmp_path / "m2")
    prev = _corrida_previa(tmp_path / "m2", "20261001T000000Z", ["predicciones de la corrida m1: A"])
    monkeypatch.setattr(m2.corridas, "comparar", lambda a, b, art: {"identicas": False, "n_filas": 3})
    est = m2.estabilidad(c, m2.corridas_previas(c.dir.parent, c.id), "B")
    assert est["concluyente"] and est["identicas"] is False
    assert est["mismo_codigo"] is False and est["mismos_datos"] is True
    assert (est["m1_previa"], est["m1_actual"]) == ("A", "B")
    assert est["corrida_previa"] == prev.name


# --------------------------------------------------------------------------
# Publicacion
# --------------------------------------------------------------------------
def _ctx_para_publicar(tmp_path, monkeypatch, acuerdo_=None):
    c = CorridaFalsa(tmp_path / "runs" / "m2")
    for n in ("validez_juez", "sesgo_autopreferencia", "determinismo_juez", "estabilidad",
              "rouge_vs_acierto"):
        c.guardar_json(n, {})
    c.guardar_csv("scorecard_por_caso", [])
    monkeypatch.setattr(m2.harness, "a_csv", lambda scs, ruta: Path(ruta).write_text("x"))
    sc = {"sistema": "s"}
    return m2.Contexto(c=c, sc_base=sc, sc_ft=sc, sp={"inconsistentes": 0, "n": 12},
                       sl={"tasa_sesgo_longitud": 0.0}, iny={"obedecieron": 0, "n": 6},
                       est={"identicas": None}, acc=0.8, may=0.4, acuerdo=acuerdo_)


def test_publicar_publica_los_diez_y_el_acuerdo_aparte(tmp_path, monkeypatch):
    ctx = _ctx_para_publicar(tmp_path, monkeypatch, acuerdo_={"n": 25})
    m2.publicar(ctx)
    assert ctx.c.publicados == list(m2.A_PUBLICAR) + [
        ("acuerdo_entre_jueces", "results/m2_acuerdo_entre_jueces.json")]
    assert ctx.c.cerrada[0] is True


def test_publicar_sin_acuerdo_no_lo_publica(tmp_path, monkeypatch):
    ctx = _ctx_para_publicar(tmp_path, monkeypatch, acuerdo_=None)
    m2.publicar(ctx)
    assert ("acuerdo_entre_jueces", "results/m2_acuerdo_entre_jueces.json") not in ctx.c.publicados


def test_publicar_no_publica_nada_si_falta_un_artefacto(tmp_path, monkeypatch):
    ctx = _ctx_para_publicar(tmp_path, monkeypatch)
    (ctx.c.dir / "validez_juez.json").unlink()
    with pytest.raises(RuntimeError, match="validez_juez"):
        m2.publicar(ctx)
    assert ctx.c.publicados == []


def test_lo_publicado_es_lo_que_arranque_declara_para_m2():
    pub = {d for _, d in m2.A_PUBLICAR} | {"results/m2_acuerdo_entre_jueces.json"}
    assert pub == set(arranque.ORDEN["m2"]["produce"])


def test_cada_artefacto_se_guarda_en_el_codigo_antes_de_publicarse():
    """Estatico, como la prueba de los notebooks: en el texto del pipeline,
    cada `guardar_json/csv("x")` aparece antes que la publicacion de "x"."""
    src = inspect.getsource(m2)
    guarda = {m.group(1): m.start()
              for m in re.finditer(r'guardar_(?:json|csv)\(\s*["\']([^"\']+)', src)}
    publica = {m.group(1): m.start()
               for m in re.finditer(r'(?:publicar\(|\()\s*["\']([^"\']+)["\']\s*,\s*["\']results/', src)}
    for n, pos in publica.items():
        if n in guarda:
            assert guarda[n] < pos, f"'{n}' se publica en el texto antes de guardarse"
    assert set(publica) - set(guarda) == {"scorecard"}       # lo pone `c.artefactos[...]`


def test_correr_encadena_las_etapas_en_el_orden_del_notebook():
    assert [e.__name__ for e in m2.ETAPAS] == [
        "cargar_salidas", "formato_vocabulario", "rouge_vs_acierto", "elegir_juez",
        "sesgo_posicion", "sesgo_longitud", "autopreferencia", "inyeccion", "validez",
        "acuerdo_entre_jueces", "harness_completo", "reproducibilidad", "publicar"]


def test_el_notebook_es_un_envoltorio_que_llama_a_cada_etapa():
    nb = json.loads((Path(__file__).resolve().parents[1] / "notebooks" / "M2_harness.ipynb")
                    .read_text(encoding="utf-8"))
    codigo = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
    for e in m2.ETAPAS:
        assert f"m2.{e.__name__}(ctx)" in codigo, f"el notebook no llama a {e.__name__}"
    assert "m2.preparar()" in codigo and "def " not in codigo
