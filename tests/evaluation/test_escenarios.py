"""Prueba de los cuatro escenarios de contexto (tools/evaluation/escenarios.py).

Se prueba el archivo congelado `data/escenarios_m1.jsonl`, que es lo que reciben
v1 y el candidato. La propiedad central es que el escenario `irrelevante` NO
traiga el articulo que responde -- si lo trajera, se estaria midiendo abstenerse
con la respuesta delante -- y que sea de la misma materia, que es lo que la
validacion no puede probar.
"""
from __future__ import annotations

from collections import Counter

import pytest

from tools.evaluation import escenarios as E

pytestmark = pytest.mark.skipif(not E.ARCHIVO.exists(), reason="sin data/escenarios_m1.jsonl")


@pytest.fixture(scope="module")
def casos():
    return E.leer(E.ARCHIVO)


class TestArchivoCongelado:
    def test_pasa_todas_las_comprobaciones(self, casos):
        assert E.verificar(casos) == []

    def test_trae_los_cuatro_escenarios(self, casos):
        por = Counter(c["escenario"] for c in casos)
        assert set(por) == set(E.ESCENARIOS)
        assert por["suficiente"] == 55 and por["parcial"] == 13 and por["vacio"] == 68

    def test_el_irrelevante_no_trae_el_articulo_que_responde(self, casos):
        """**La prueba central.** Si lo trajera, ensenaria a confundir
        abstenerse con no leer."""
        for c in (x for x in casos if x["escenario"] == "irrelevante"):
            assert not set(c["excluidos"]) & E._pares(c["contexto"]), c["id"]

    def test_el_irrelevante_es_casi_siempre_de_la_misma_materia(self, casos):
        """Es lo que la validacion no puede probar: sus 35 B2 tienen 0 de 35
        fragmentos de su propia categoria. Aqui la mayoria si los trae."""
        r = E.resumen(casos, [])
        hechos, total = map(int, r["irrelevante_con_fragmento_de_su_categoria"].split("/"))
        assert hechos / total >= 0.8

    def test_el_irrelevante_sale_del_buscador_de_produccion(self, casos):
        assert {c["buscador"] for c in casos if c["escenario"] == "irrelevante"} == {"e5+faiss+enrutador"}

    def test_es_pareado_con_las_mismas_preguntas(self, casos):
        """Cada irrelevante tiene su suficiente o su parcial con la MISMA
        pregunta: el modelo tiene que cambiar de conducta solo por el contexto."""
        con = {c["id"]: c["pregunta"] for c in casos if c["escenario"] in ("suficiente", "parcial")}
        for c in (x for x in casos if x["escenario"] == "irrelevante"):
            assert con[c["id"]] == c["pregunta"]

    def test_suficiente_y_parcial_traen_el_articulo_que_responde(self, casos):
        """El otro lado del par: con contexto suficiente el oraculo tiene que
        estar, o 'citar el oraculo' no se podria medir."""
        from tools.dataset_v2_quality import _articulo_normalizado

        for c in (x for x in casos if x["escenario"] in ("suficiente", "parcial")):
            declarados = {_articulo_normalizado(f.rsplit(":", 1)[1]) for f in c["fuentes"]}
            traidos = {_articulo_normalizado(a) for ch in c["contexto"] for a in ch["articulos"]}
            assert declarados & traidos, c["id"]

    def test_todos_los_que_van_al_modelo_llevan_el_prompt_de_contexto(self, casos):
        """El mismo prompt con que se entrena y con que responde el RAG."""
        orden = "Si el CONTEXTO no contiene informacion suficiente"
        for c in (x for x in casos if x["escenario"] != "vacio"):
            assert orden in c["messages"][0]["content"]

    def test_vacio_no_llama_al_modelo(self, casos):
        """El escenario vacio lo resuelve el codigo: con model_bundle=None, si
        intentara generar, fallaria."""
        from tools.rag.pipeline import _generar_verificado
        from tools.rag.prompt_template import RESPUESTA_ESCAPE_POR_CODIGO

        c = next(x for x in casos if x["escenario"] == "vacio")
        respuesta, ver = _generar_verificado(c["pregunta"], [], use_lora=False, model_bundle=None)
        assert respuesta == RESPUESTA_ESCAPE_POR_CODIGO
        assert ver["escape_por_codigo"] == "sin_contexto"


class TestMetricas:
    CASO = {"fuentes": ["LEY-820-2003:20"],
            "contexto": [{"cita": "Ley 820 de 2003 (Regimen de arrendamiento de vivienda urbana), Articulo 20",
                          "doc_id": "ley820", "articulos": ["20"], "chunk_id": "x"}]}

    def test_detecta_la_cita_del_oraculo(self):
        m = E.metricas(self.CASO, "Segun el articulo 20 de la Ley 820 de 2003, el canon solo sube con el IPC.")
        assert m["cita_el_oraculo"] and not m["citas_no_respaldadas"]

    def test_detecta_la_abstencion(self):
        from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO

        m = E.metricas(self.CASO, RESPUESTA_SIN_CONTEXTO + ". Consulta en un consultorio juridico.")
        assert m["abstencion_pura"] and not m["cita_el_oraculo"]

    def test_marca_una_cita_que_el_contexto_no_respalda(self):
        m = E.metricas(self.CASO, "El articulo 99 de la Ley 820 de 2003 lo prohibe.")
        assert m["citas_no_respaldadas"]


def test_congelar_exige_el_buscador_de_produccion():
    """Sin --indice el irrelevante saldria de BM25, que no es lo que ve el
    sistema en servicio: el mismo defecto H4 del dataset."""
    with pytest.raises(SystemExit, match="exige --indice"):
        E.main(["--escribir"])
