"""
T7 · Pruebas del enchufe real (`m4/pipeline/enchufe_m3.py`).

Sin red ni modelos: el cliente de Groq y el indice son los dobles que ya usa
`src/autoprueba_agente.py`, asi que el agente que se prueba aqui es el MISMO
`agente.Agente` de M3, no una copia.

Lo que fijan, por orden de importancia:

  1. que el sistema multimodal, con el enchufe, responde en el formato de
     Amparo (las cinco lineas que `schema.parse_salida` lee). Con el sustituto
     no lo hacia, y por eso `exacto` y `juez_vlm` no significaban nada;
  2. que el mecanismo lo decide el motor de reglas, no el texto del VLM: la
     traza del agente dice que regla cerro;
  3. que el brazo y el chunking salen de los artefactos publicados de M3, no
     de constantes que puedan discrepar de ellos.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "m4" / "pipeline"))
sys.path.insert(0, str(RAIZ / "m4" / "harness"))

import enchufe_m3                                          # noqa: E402
import schema                                              # noqa: E402
from autoprueba_agente import ClienteGuionado, IndiceFalso  # noqa: E402
from scorecard import armar_relato                         # noqa: E402

pytestmark = pytest.mark.skipif(
    not (RAIZ / "results" / "m3_scorecard.csv").exists(),
    reason="results/ de M3 no esta en esta copia del repo")


class _Transformador:
    """La reescritura de consulta, sin API: devuelve el relato tal cual."""
    def __call__(self, relato):
        return relato


def _responder(tmp_path):
    cliente = ClienteGuionado(
        [[("buscar_normas", '{"consulta": "derecho a la salud cirugia ordenada"}')], None])
    return enchufe_m3.construir_responder_m3(
        cliente, indice=IndiceFalso(), transformador=_Transformador(),
        cache_dir=tmp_path)


def test_el_brazo_enchufado_existe_en_el_scorecard_de_m3():
    fila = enchufe_m3.comprobar_brazo()
    assert fila["sistema"] == enchufe_m3.SISTEMA_M3


def test_un_brazo_mal_escrito_falla_antes_de_la_gpu():
    with pytest.raises(KeyError):
        enchufe_m3.comprobar_brazo("4 - agente + reglas")


def test_el_chunking_es_el_que_eligio_m3():
    elegido = json.loads((RAIZ / "results" / "m3_chunking.json")
                         .read_text(encoding="utf-8"))["elegido"]
    nombre, fn = enchufe_m3.chunking_de_m3()
    assert nombre == elegido and callable(fn)


def test_responde_en_el_formato_de_amparo(tmp_path):
    responder, _ = _responder(tmp_path)
    js = {"tipo_documento": "respuesta_peticion", "entidad": "EPS Salud Serena",
          "fecha": "5 de octubre de 2026", "plazo_dias": None,
          "pretension_visible": "niega la autorizacion del reemplazo de cadera"}
    relato = armar_relato("Me llego esta respuesta de mi EPS. Tengo 68 anos.",
                          js, json.dumps(js))
    salida = responder(relato)
    p = schema.parse_salida(salida)
    assert p.get("mecanismo") in schema.MECANISMOS, salida


def test_el_mecanismo_lo_decide_el_motor(tmp_path):
    responder, ag = _responder(tmp_path)
    responder("Me llego esta respuesta de mi EPS.\n\nDATOS DEL DOCUMENTO ADJUNTO:\n{}")
    t = ag.trazas[-1]
    assert t["regla"], "la traza no dice que regla cerro el caso"
    assert t["mecanismo"] == t["mecanismo_del_motor"]


def test_la_etiqueta_es_la_del_brazo(tmp_path):
    _, ag = _responder(tmp_path)
    assert ag.etiqueta == enchufe_m3.SISTEMA_M3
    assert (ag.estrategia, ag.k) == (enchufe_m3.ESTRATEGIA, enchufe_m3.K)
