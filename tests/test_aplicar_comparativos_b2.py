"""La escritura de los comparativos v1/v2 como operacion reversible y acotada.

Lo que protege: que registrar el dictamen de un abogado no arrastre nada mas.
El CSV de adjudicacion lleva tres decisiones distintas en la misma fila -- la
pertinencia del contexto, la validez de la etiqueta B2 y la comparacion de los
dos modelos -- aprobadas en momentos distintos y por alcances distintos. Un
script que al escribir una toque otra destruye la trazabilidad sin que se note,
porque el CSV sigue pareciendo valido.

Todo corre contra una copia temporal. Nunca contra docs/m1_b2_adjudicacion.csv.
"""
from __future__ import annotations

import csv
import shutil

import pytest

from tools.adjudicacion_b2 import COLUMNAS, SALIDA, VOCABULARIO
from tools.aplicar_comparativos_b2 import (
    _DICTAMEN_PREVIO,
    AUTORIZADAS,
    CONSULTAS_ABIERTAS,
    DICTAMEN,
    RELLENO,
    aplicar,
    main,
    verificar,
)

# Las ocho etiquetas aprobadas el 2026-10-10. Su validez y su confianza son
# intocables: las aprobo el abogado como dictamen separado.
OCHO = {"3328", "3517", "3822", "3920", "4226", "4321", "4324", "4724"}


def leer(ruta):
    with ruta.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def sin_adjudicar(filas):
    """Las filas como estaban antes de escribir el dictamen comparativo.

    El CSV oficial ya esta adjudicado (se escribio el 2026-10-10), asi que una
    prueba de `aplicar` que lo lea tal cual no veria ningun cambio y no probaria
    nada. Estas pruebas reconstruyen el estado previo en memoria, que es lo que
    las hace independientes de si el oficial se escribio o no.
    """
    previas = []
    for f in filas:
        g = dict(f)
        g["comparacion_v1_v2"] = "pendiente"
        g["revision_juridica"] = "requerida"
        prefijo = _DICTAMEN_PREVIO.sub("", f["justificacion_final"]).strip()
        g["justificacion_final"] = f"{prefijo} {RELLENO}".strip() if prefijo else RELLENO
        # la firma previa es la de la clasificacion, sin la clausula del comparativo
        g["revisor"] = f["revisor"].split("Comparativo v1/v2:")[0].strip()
        previas.append(g)
    return previas


@pytest.fixture
def oficial():
    """El estado previo a la adjudicacion, que es sobre lo que opera el script."""
    return sin_adjudicar(leer(SALIDA))


@pytest.fixture
def escrito():
    """El CSV oficial tal como esta hoy, ya adjudicado."""
    return leer(SALIDA)


@pytest.fixture
def copia(tmp_path, oficial):
    destino = tmp_path / "adjudicacion.csv"
    with destino.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(oficial)
    return destino


# --- cobertura del dictamen ----------------------------------------------------

def test_el_dictamen_cubre_los_35_una_sola_vez(oficial):
    ids = [f["case_id"] for f in oficial]
    assert len(ids) == 35
    assert len(set(ids)) == 35
    assert set(DICTAMEN) | set(CONSULTAS_ABIERTAS) == set(ids)


def test_ningun_caso_esta_adjudicado_y_abierto_a_la_vez():
    assert not set(DICTAMEN) & set(CONSULTAS_ABIERTAS)


def test_los_veredictos_estan_en_el_vocabulario():
    for cid, (veredicto, confianza, _) in DICTAMEN.items():
        assert veredicto in VOCABULARIO["comparacion_v1_v2"] - {"pendiente"}, cid
        assert confianza in VOCABULARIO["confianza"], cid


def test_toda_justificacion_tiene_contenido():
    for cid, (_, _, texto) in DICTAMEN.items():
        assert len(texto.strip()) > 40, cid


# --- conservacion --------------------------------------------------------------

def test_no_se_toca_ninguna_columna_fuera_de_las_autorizadas(oficial):
    despues, _ = aplicar(oficial)
    tocadas = {c for a, b in zip(oficial, despues) for c in COLUMNAS if a[c] != b[c]}
    assert tocadas <= AUTORIZADAS
    # y en particular ninguna de estas, que son otras decisiones
    assert not tocadas & {"pertinencia_contexto", "validez_etiqueta_b2", "confianza",
                          "fragmentos_relevantes", "justificacion_contexto",
                          "commit_matriz", "origen_prompt", "fecha_revision"}


def test_las_ocho_etiquetas_aprobadas_quedan_intactas(oficial):
    despues, _ = aplicar(oficial)
    for a, b in zip(oficial, despues):
        if a["case_id"] in OCHO:
            assert a["validez_etiqueta_b2"] == b["validez_etiqueta_b2"], a["case_id"]
            assert a["confianza"] == b["confianza"], a["case_id"]


def test_la_validez_y_la_confianza_quedan_intactas_en_las_35(oficial):
    despues, _ = aplicar(oficial)
    for a, b in zip(oficial, despues):
        assert a["validez_etiqueta_b2"] == b["validez_etiqueta_b2"], a["case_id"]
        assert a["confianza"] == b["confianza"], a["case_id"]


def test_no_cambia_el_numero_ni_el_orden_de_las_filas(oficial):
    despues, _ = aplicar(oficial)
    assert [f["case_id"] for f in despues] == [f["case_id"] for f in oficial]


def test_las_columnas_siguen_siendo_las_mismas(oficial):
    despues, _ = aplicar(oficial)
    for f in despues:
        assert set(f) == set(COLUMNAS)


# --- consultas abiertas --------------------------------------------------------

def test_las_consultas_abiertas_no_se_tocan_en_absoluto(oficial):
    despues, _ = aplicar(oficial)
    for a, b in zip(oficial, despues):
        if a["case_id"] in CONSULTAS_ABIERTAS:
            assert a == b, a["case_id"]


def test_las_consultas_abiertas_siguen_pendientes(oficial):
    """Hoy la lista esta vacia: Leonardo aprobo las cuatro el 2026-10-10."""
    despues, _ = aplicar(oficial)
    abiertas = [f for f in despues if f["case_id"] in CONSULTAS_ABIERTAS]
    assert len(abiertas) == len(CONSULTAS_ABIERTAS)
    for f in abiertas:
        assert f["comparacion_v1_v2"] == "pendiente", f["case_id"]
        assert f["revision_juridica"] == "requerida", f["case_id"]
        assert RELLENO in f["justificacion_final"], f["case_id"]


def test_cada_consulta_abierta_dice_que_falta_responder():
    for cid, pregunta in CONSULTAS_ABIERTAS.items():
        assert "?" in pregunta, cid
        assert len(pregunta) > 50, cid


def test_una_consulta_abierta_deja_su_fila_intacta(oficial, monkeypatch):
    """El mecanismo de retencion, probado aunque la lista este vacia.

    Se vacio al aprobarse las cuatro, y una prueba que solo recorre una lista
    vacia no prueba nada. Si una tanda futura deja una consulta sin responder,
    esto garantiza que su fila no se toca.
    """
    import tools.aplicar_comparativos_b2 as mod

    cid = oficial[0]["case_id"]
    # Retener una consulta es moverla de DICTAMEN a CONSULTAS_ABIERTAS, no
    # dejarla en los dos: verificar() rechaza ese solapamiento, y con razon.
    monkeypatch.setattr(mod, "CONSULTAS_ABIERTAS", {cid: "¿pregunta de prueba sin responder, suficientemente larga?"})
    monkeypatch.setattr(mod, "DICTAMEN", {k: v for k, v in mod.DICTAMEN.items() if k != cid})
    despues, celdas = mod.aplicar(oficial)
    assert despues[0] == oficial[0]
    assert not [c for c in celdas if c[0] == cid]
    assert despues[0]["comparacion_v1_v2"] == "pendiente"
    assert mod.verificar(oficial, despues) == []


# --- coherencia del resultado --------------------------------------------------

def test_los_adjudicados_pierden_la_frase_de_relleno(oficial):
    despues, _ = aplicar(oficial)
    for f in despues:
        if f["comparacion_v1_v2"] != "pendiente":
            assert RELLENO not in f["justificacion_final"], f["case_id"]
            assert f["comparacion_v1_v2"] in f["justificacion_final"], f["case_id"]


def test_ningun_adjudicado_sigue_diciendo_que_falta_el_abogado(oficial):
    despues, _ = aplicar(oficial)
    for f in despues:
        if f["comparacion_v1_v2"] != "pendiente":
            assert f["revision_juridica"] == "cumplida", f["case_id"]


def test_se_conserva_el_texto_propio_que_precede_al_relleno(oficial):
    """20 filas traen texto de la clasificacion delante. No se pierde."""
    despues, _ = aplicar(oficial)
    comprobadas = 0
    for a, b in zip(oficial, despues):
        prefijo = a["justificacion_final"].replace(RELLENO, "").strip()
        if prefijo and a["case_id"] not in CONSULTAS_ABIERTAS:
            assert b["justificacion_final"].startswith(prefijo), a["case_id"]
            comprobadas += 1
    assert comprobadas >= 15


def test_el_reparto_final_es_el_de_los_dictamenes(oficial):
    despues, _ = aplicar(oficial)
    cuenta: dict[str, int] = {}
    for f in despues:
        cuenta[f["comparacion_v1_v2"]] = cuenta.get(f["comparacion_v1_v2"], 0) + 1
    assert cuenta == {"mejora": 12, "empate": 14, "regresion": 9}


def test_verificar_no_encuentra_problemas_en_la_corrida_real(oficial):
    despues, _ = aplicar(oficial)
    assert verificar(oficial, despues) == []


# --- el verificador detecta lo que debe ---------------------------------------

def test_verificar_detecta_una_columna_no_autorizada(oficial):
    despues, _ = aplicar(oficial)
    despues[0]["pertinencia_contexto"] = "suficiente"
    problemas = verificar(oficial, despues)
    assert any("no autorizadas" in p for p in problemas)


def test_verificar_detecta_que_se_toco_una_etiqueta_aprobada(oficial):
    despues, _ = aplicar(oficial)
    i = next(i for i, f in enumerate(despues) if f["case_id"] in OCHO)
    despues[i]["validez_etiqueta_b2"] = "valido" if \
        despues[i]["validez_etiqueta_b2"] != "valido" else "modo_mal_asignado"
    assert verificar(oficial, despues)


def test_verificar_detecta_una_consulta_abierta_cerrada(oficial, monkeypatch):
    import tools.aplicar_comparativos_b2 as mod

    cid = oficial[0]["case_id"]
    monkeypatch.setattr(mod, "CONSULTAS_ABIERTAS", {cid: "¿pregunta de prueba sin responder, suficientemente larga?"})
    despues, _ = mod.aplicar(oficial)
    despues[0]["comparacion_v1_v2"] = "regresion"
    problemas = mod.verificar(oficial, despues)
    assert any("consulta abierta" in p for p in problemas)


def test_verificar_detecta_un_adjudicado_que_sigue_requiriendo_abogado(oficial):
    despues, _ = aplicar(oficial)
    i = next(i for i, f in enumerate(despues) if f["comparacion_v1_v2"] != "pendiente")
    despues[i]["revision_juridica"] = "requerida"
    problemas = verificar(oficial, despues)
    assert any("requerida" in p for p in problemas)


def test_verificar_detecta_un_veredicto_fuera_del_vocabulario(oficial):
    despues, _ = aplicar(oficial)
    despues[0]["comparacion_v1_v2"] = "v2_gana"
    problemas = verificar(oficial, despues)
    assert any("vocabulario" in p for p in problemas)


def test_verificar_detecta_que_se_movio_el_orden(oficial):
    despues, _ = aplicar(oficial)
    despues[0], despues[1] = despues[1], despues[0]
    problemas = verificar(oficial, despues)
    assert any("orden" in p for p in problemas)


def test_verificar_detecta_una_fila_de_menos(oficial):
    recortado = oficial[:-1]
    despues, _ = aplicar(recortado)
    problemas = verificar(recortado, despues)
    assert any("34 filas" in p for p in problemas)


# --- la simulacion no escribe --------------------------------------------------

def test_la_simulacion_deja_el_archivo_igual(copia, capsys):
    antes = copia.read_bytes()
    assert main(["--csv", str(copia)]) == 0
    assert copia.read_bytes() == antes
    assert "no se escribio nada" in capsys.readouterr().out


def test_la_simulacion_muestra_el_diff_celda_por_celda(copia, capsys):
    main(["--csv", str(copia)])
    salida = capsys.readouterr().out
    assert "Celdas que cambiarian" in salida
    assert "'pendiente' -> " in salida
    for col in sorted(AUTORIZADAS):
        assert col in salida


def test_escribir_aplica_y_es_idempotente(copia):
    assert main(["--csv", str(copia), "--escribir"]) == 0
    escrito = leer(copia)
    cuenta: dict[str, int] = {}
    for f in escrito:
        cuenta[f["comparacion_v1_v2"]] = cuenta.get(f["comparacion_v1_v2"], 0) + 1
    assert cuenta == {"mejora": 12, "empate": 14, "regresion": 9}

    # una segunda corrida no vuelve a cambiar nada
    despues, celdas = aplicar(escrito)
    assert celdas == []
    assert verificar(escrito, despues) == []


def test_el_csv_oficial_quedo_adjudicado(escrito):
    """El resultado registrado el 2026-10-10, fijado contra cambios accidentales.

    Sustituye a la guarda anterior, que comprobaba que el oficial siguiera en
    `pendiente`. Esa guarda protegia el procedimiento mientras el dictamen
    estaba en borrador; una vez escrito, lo que hay que proteger es el
    resultado.
    """
    from collections import Counter

    assert len(escrito) == 35
    assert Counter(f["comparacion_v1_v2"] for f in escrito) == {
        "mejora": 12, "empate": 14, "regresion": 9}
    for f in escrito:
        assert f["revision_juridica"] == "cumplida", f["case_id"]
        assert RELLENO not in f["justificacion_final"], f["case_id"]
        assert "Leonardo Galeano" in f["revisor"], f["case_id"]
    # las otras dos decisiones, intactas
    assert Counter(f["validez_etiqueta_b2"] for f in escrito) == {
        "valido": 32, "modo_mal_asignado": 3}
    assert Counter(f["pertinencia_contexto"] for f in escrito) == {
        "insuficiente": 27, "parcial": 8}


def test_reaplicar_sobre_el_oficial_no_cambia_nada(escrito):
    """Idempotencia sobre el archivo real: una corrida extra no lo mueve."""
    despues, celdas = aplicar(escrito)
    assert celdas == []
    assert verificar(escrito, despues) == []
