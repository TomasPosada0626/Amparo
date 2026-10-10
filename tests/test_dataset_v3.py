"""Dataset v3 (tools/dataset_v3.py) y la regla B2 corregida.

Lo que estas pruebas tienen que impedir, en orden de gravedad:

1. Que el contexto de un B2 traiga el articulo que SI responde. Eso ensena a
   abstenerse con la respuesta delante, y es peor que no tener el ejemplo.
2. Que una pregunta de urgencia reciba un objetivo que solo se abstiene.
3. Que la regla historica deje de reproducirse: si cambia, las corridas
   anteriores dejan de ser comparables.
"""
from __future__ import annotations

from tools import dataset_v2 as d2
from tools import dataset_v3 as d3


class _Frag:
    """Un SearchResult con lo justo para las reglas."""

    def __init__(self, doc_id, articulos, capitulo="", chunk_id="x"):
        self.doc_id = doc_id
        self.articulos_incluidos = list(articulos)
        self.capitulo = capitulo
        self.chunk_id = chunk_id
        self.cita = f"{doc_id}, Articulo {articulos[0] if articulos else ''}"
        self.text = ""


class TestRiesgoDeSuficienciaIndirecta:
    def test_la_fuga_del_articulo_que_responde_es_fallo(self):
        avisos = d2.riesgo_de_suficiencia_indirecta(
            [_Frag("ley820", ["20"])], {"ley820:20"})
        assert any(a.startswith("FUGA_DIRECTA") for a in avisos)

    def test_otro_articulo_del_mismo_capitulo_pide_revision(self):
        """Caso 4006: se retiraron los arts. 139 y 142 del Codigo de la Infancia
        y el contexto trajo el 143 y el 149, del mismo capitulo."""
        avisos = d2.riesgo_de_suficiencia_indirecta(
            [_Frag("infancia", ["143"], capitulo="Responsabilidad penal adolescente")],
            {"infancia:139"},
            {"infancia": {"Responsabilidad penal adolescente"}})
        assert avisos == ["MISMO_CAPITULO infancia :: Responsabilidad penal adolescente"]

    def test_otro_capitulo_de_la_misma_norma_es_el_caso_esperado(self):
        """El Codigo Civil trae arriendo, sucesiones y servidumbres. Que aparezca
        otro articulo suyo es lo que el enrutador real devuelve, no un defecto."""
        avisos = d2.riesgo_de_suficiencia_indirecta(
            [_Frag("codigo_civil", ["2470"], capitulo="Sucesiones")],
            {"codigo_civil:1973"},
            {"codigo_civil": {"Arrendamiento"}})
        assert avisos == ["MISMA_NORMA codigo_civil"]

    def test_un_articulo_contiguo_al_retirado_es_motivo_de_descarte(self):
        """Los dos casos documentados en el dictamen del gold aprobado el
        2026-10-10: el art. 144 de la Ley 769 "viene del 143", y de la Ley 2220
        "los arts. 67, 68, 70 y 71 son los que resuelven el requisito de
        procedibilidad". Un vecino responde lo que responde el retirado."""
        avisos = d2.riesgo_de_suficiencia_indirecta(
            [_Frag("ley769", ["144"], capitulo="Danos materiales")], {"ley769:143"},
            {"ley769": {"Danos materiales"}})
        assert avisos == ["CONTIGUO_AL_ORACULO ley769"]

    def test_la_contiguidad_pesa_mas_que_el_capitulo(self):
        """Un vecino es mas peligroso que un articulo lejano del mismo capitulo,
        asi que se reporta como contiguo y no como MISMO_CAPITULO."""
        avisos = d2.riesgo_de_suficiencia_indirecta(
            [_Frag("ley2220", ["68"], capitulo="Procedibilidad")], {"ley2220:67"},
            {"ley2220": {"Procedibilidad"}})
        assert all(a.startswith("CONTIGUO_AL_ORACULO") for a in avisos)

    def test_un_articulo_lejano_del_mismo_capitulo_no_es_contiguo(self):
        """CONTIGUO_MAX = 2: el 92 de la Ley 2220 esta en el mismo capitulo que
        el 67 pero 25 articulos despues, y eso ya no es una continuacion."""
        avisos = d2.riesgo_de_suficiencia_indirecta(
            [_Frag("ley2220", ["92"], capitulo="Procedibilidad")], {"ley2220:67"},
            {"ley2220": {"Procedibilidad"}})
        assert avisos == ["MISMO_CAPITULO ley2220 :: Procedibilidad"]

    def test_un_articulo_con_sufijo_no_rompe_la_comparacion(self):
        """"572-A" no es un entero. Si el parseo fallara, la regla se caeria o
        dejaria pasar la variante en silencio."""
        avisos = d2.riesgo_de_suficiencia_indirecta(
            [_Frag("cgp", ["572-A"])], {"cgp:548"}, {})
        assert avisos == ["MISMA_NORMA cgp"]

    def test_la_fuga_directa_tiene_prioridad_sobre_el_capitulo(self):
        """Si hay fuga, lo que importa es la fuga: el ejemplo se descarta y no
        tiene sentido informar ademas del capitulo."""
        avisos = d2.riesgo_de_suficiencia_indirecta(
            [_Frag("ley820", ["20"], capitulo="Canon"), _Frag("ley820", ["21"], capitulo="Canon")],
            {"ley820:20"}, {"ley820": {"Canon"}})
        assert all(a.startswith("FUGA_DIRECTA") for a in avisos)


class TestReglaB2:
    def test_la_regla_historica_sigue_siendo_la_predeterminada(self):
        """Si el valor por defecto cambiara, reconstruir el dataset historico
        daria otro resultado y las corridas anteriores dejarian de ser
        comparables."""
        import inspect

        firma = inspect.signature(d2.fragmentos_para)
        assert firma.parameters["regla_b2"].default == d2.REGLA_B2_V2

    def test_una_regla_desconocida_no_pasa_en_silencio(self):
        import pytest

        with pytest.raises(SystemExit):
            d2.fragmentos_para(
                d2.Especificacion(id=1, categoria="Arriendo", modo="B2", respuesta="x"),
                "pregunta", None, None, regla_b2="v9")


class TestObjetivosDeLosContrastivos:
    POOL = {"Arriendo": ["Consulta en la Personeria.", "Acude a un consultorio juridico.",
                         "Pregunta en la inspeccion de policia."]}

    def test_reparte_en_vez_de_repetir(self):
        """El defecto que corrige v3: 418 variantes con 11 objetivos distintos y
        250 identicos. El reparto es round-robin y deterministico."""
        vistos = [d3.objetivo("Arriendo", i, self.POOL)[0] for i in range(3)]
        assert len(set(vistos)) == 3
        assert d3.objetivo("Arriendo", 0, self.POOL) == d3.objetivo("Arriendo", 3, self.POOL)

    def test_el_prefijo_es_la_frase_exacta(self):
        """`es_valvula_de_escape` y el juez buscan esa frase tal cual."""
        from tools.rag.prompt_template import RESPUESTA_SIN_CONTEXTO

        texto, _ = d3.objetivo("Arriendo", 0, self.POOL)
        assert texto.startswith(RESPUESTA_SIN_CONTEXTO)

    def test_una_urgencia_no_recibe_objetivo_mecanico(self):
        """Caso 6077 del historico: a *"estoy en una situacion de violencia
        intrafamiliar y necesito salir del contrato"* le toco *"toma fotos del
        dano, avisa al arrendador"*. Pasaba el regex de ayuda inmediata y era
        ajeno a la situacion. Ahora no se genera."""
        texto, nota = d3.objetivo(
            "Arriendo", 0, self.POOL,
            "Estoy en una situacion de violencia intrafamiliar y necesito salir del contrato")
        assert texto == "" and nota == "URGENCIA_REQUIERE_OBJETIVO_A_MANO"

    def test_una_categoria_sin_punteros_para_en_vez_de_inventar(self):
        import pytest

        with pytest.raises(SystemExit):
            d3.objetivo("Categoria que no existe", 0, self.POOL)


class TestUrgenciaAmplia:
    def test_reconoce_las_cuatro_formas_que_el_patron_estrecho_pierde(self):
        from tools.dataset_quality import URGENCIA
        from tools.evaluation.seguridad_urgencias_reglas import URGENCIA_AMPLIA

        casos = [
            "Mi hijo de 16 anos esta detenido en una estacion de policia desde anoche",
            "En la clinica no dejan salir a mi mama hasta que paguemos la cuenta",
            "Estoy en la audiencia ahora mismo y el juez me pide firmar un acuerdo",
            "El carro que me choco se esta yendo y no alcance a ver la placa",
        ]
        for q in casos:
            assert URGENCIA_AMPLIA.search(q), q
            assert not URGENCIA.search(q), f"el estrecho ya lo veia: {q}"

    def test_no_marca_una_subordinada_temporal_corriente(self):
        """"antes de que" y "en curso" se retiraron del patron por esto: marcaban
        ejemplos B1 correctos cuya respuesta de fondo es la adecuada."""
        from tools.evaluation.seguridad_urgencias_reglas import URGENCIA_AMPLIA

        for q in ("Me embargaron antes de que hubiera sentencia, no entiendo por que.",
                  "Tengo un proceso disciplinario en curso, puedo seguir yendo a clases?",
                  "Tenia un contrato a termino fijo y me lo terminaron antes de que se venciera."):
            assert not URGENCIA_AMPLIA.search(q), q
