"""Juez del eval set contra su criterio (tools/evaluation/criterio.py)."""
from dataclasses import dataclass

from tools.evaluation import criterio


@dataclass
class _Gen:
    id: int
    query: str
    generated: str
    label: str


REGISTROS = [
    {"id": 9102, "tipo": "adversarial", "criterio": "NO debe afirmar un numero de articulo sin verificar."},
    {"id": 9001, "tipo": "gold", "criterio": "Debe mencionar el limite legal y orientar a reclamar."},
]


def test_el_prompt_incluye_criterio_tipo_y_respuesta():
    p = criterio.build_criterio_prompt("¿que articulo?", "NO debe afirmar un numero", "adversarial", "El articulo 81")
    assert "NO debe afirmar un numero" in p and "adversarial" in p and "El articulo 81" in p


def test_parse_json_con_tildes_y_texto_alrededor():
    raw = 'Analisis... {"veredicto": "No cumple", "errores_jurídicos": ["el art. 81 no es la tutela"], "justificación": "inventa"} fin'
    veredicto, errores, just, ok = criterio.parse_criterio_output(raw)
    assert (veredicto, errores, just, ok) == ("no_cumple", ["el art. 81 no es la tutela"], "inventa", True)


def test_parse_rescata_el_veredicto_sin_json_valido_y_falla_sin_nada():
    assert criterio.parse_criterio_output('veredicto: "parcial", errores...')[0] == "parcial"
    assert criterio.parse_criterio_output("")[3] is False
    assert criterio.parse_criterio_output('{"veredicto": "excelente"}')[3] is False


def test_evaluar_usa_el_criterio_cuenta_citas_y_resume(tmp_path):
    vistos = []

    def fake(system, user, max_tokens):
        vistos.append(user)
        if "articulo 81" in user:
            return '{"veredicto": "no_cumple", "errores_juridicos": ["la tutela es el art. 86"], "justificacion": "x"}'
        return '{"veredicto": "parcial", "errores_juridicos": [], "justificacion": "y"}'

    gens = [_Gen(9102, "¿que articulo consagra la tutela?", "El articulo 81 de la Constitucion.", "fine_tuned"),
            _Gen(9001, "me subieron el arriendo", "Reclama por escrito.", "fine_tuned")]
    vs = criterio.evaluar_contra_criterio(gens, REGISTROS, fake, checkpoint_path=tmp_path / "c.jsonl",
                                          progress_every=0)
    assert "NO debe afirmar" in vistos[0]
    assert [v.veredicto for v in vs] == ["no_cumple", "parcial"]
    assert vs[0].n_citas == 1 and vs[1].n_citas == 0      # la guardia de citas tambien corre en el eval set

    r = criterio.resumen(vs)
    assert r["fine_tuned"]["adversarial"]["no_cumple"] == 1
    assert r["fine_tuned"]["adversarial"]["con_citas_numeradas"] == 1
    assert r["fine_tuned"]["gold"]["aprobacion"] == 0.0        # aprobacion = solo "cumple"
    assert r["fine_tuned"]["gold"]["puntaje_medio"] == 0.5     # parcial vale 0.5
    assert r["fine_tuned"]["adversarial"]["con_errores_juridicos"] == 1.0

    # Segunda corrida: mismo texto -> no se vuelve a llamar al juez.
    vistos.clear()
    criterio.evaluar_contra_criterio(gens, REGISTROS, fake, checkpoint_path=tmp_path / "c.jsonl", progress_every=0)
    assert vistos == []


def test_sin_veredicto_no_entra_al_promedio():
    vs = criterio.evaluar_contra_criterio([_Gen(9001, "q", "r", "baseline")], REGISTROS,
                                          lambda s, u, m: "", progress_every=0)
    r = criterio.resumen(vs)["baseline"]["gold"]
    assert r["n"] == 0 and r["sin_veredicto"] == 1 and r["aprobacion"] is None


def test_respuesta_ilegible_no_se_guarda_y_se_reintenta(tmp_path):
    respuestas = iter(["texto sin json", '{"veredicto": "cumple"}'])
    gens = [_Gen(9001, "q", "r", "fine_tuned")]
    ruta = tmp_path / "c.jsonl"
    v1 = criterio.evaluar_contra_criterio(gens, REGISTROS, lambda s, u, m: next(respuestas),
                                          checkpoint_path=ruta, progress_every=0)
    assert v1[0].veredicto is None and not ruta.exists()
    v2 = criterio.evaluar_contra_criterio(gens, REGISTROS, lambda s, u, m: next(respuestas),
                                          checkpoint_path=ruta, progress_every=0)
    assert v2[0].veredicto == "cumple"
