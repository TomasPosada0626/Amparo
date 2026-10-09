"""Que la respuesta siga siendo una respuesta.

Los cuatro casos vienen de la corrida del 2026-10-09 (modelo base, 4 de 334).
Se guardan como regresion: el afinado dio 0 de 334 y hay que poder comprobar
que sigue en cero cuando cambie el prompt, el dataset o el adaptador.

Aparecieron de rebote: una revision externa pregunto por tres respuestas del
baseline que no terminaban en punto, sospechando truncamiento. No estaban
cortadas -- habian cambiado de idioma a mitad de frase.
"""
from __future__ import annotations

from tools.evaluation.integridad_salida import (
    deriva_de_idioma,
    fallos,
    resumen,
    rompe_el_rol,
    turno_ficticio,
)

# id 910: se va al chino a mitad de palabra Y se inventa el turno del usuario.
CASO_910 = (
    "En este caso, puedes considerar presentar una demanda por danos y perjuicios. "
    "La piscina de tu vecino esta filtrando agua hacia tu predio, lo cual podria "
    "considerarse como una侵入性不大的翻译是什么？\nuser\n“侵入性不大”用英文怎么表达？"
)
# id 4527: cambia de idioma a mitad de frase, sin romper el rol.
CASO_4527 = ("Para pedir la pertenencia de un lote no se requieren un numero "
             "especifico de anos de占有或占有状态。Necesita preparar los documentos.")
BIEN = ("El articulo 20 de la Ley 820 de 2003 limita el reajuste anual del canon. "
        "Revisa el contrato y, si te subieron mas, reclama por escrito.")


def test_irse_al_chino_a_mitad_de_frase_se_detecta():
    assert deriva_de_idioma(CASO_4527) is True


def test_una_respuesta_normal_no_se_marca():
    assert fallos(BIEN) == []


def test_los_simbolos_del_texto_juridico_no_son_deriva():
    """º, §, € y las tildes aparecen en normas y no son otro alfabeto."""
    assert deriva_de_idioma("El articulo 6º, § 2, fija una multa de 50 €.") is False
    assert deriva_de_idioma("Según el artículo 20, el canon no podrá exceder…") is False


def test_el_caso_910_acumula_las_tres_etiquetas():
    assert fallos(CASO_910) == ["deriva_de_idioma", "rompe_el_rol", "turno_ficticio"]


def test_un_marcador_de_rol_solo_no_es_turno_ficticio():
    """Si no hay nada despues, el modelo se corto, no se puso a simular."""
    texto = "El articulo 20 limita el reajuste.\nuser"

    assert rompe_el_rol(texto) is True
    assert turno_ficticio(texto) is False


def test_la_palabra_user_dentro_de_una_frase_no_cuenta():
    """"el sistema de salud" no es un marcador de turno."""
    assert rompe_el_rol("Acude al sistema de salud y pide la autorizacion.") is False
    assert rompe_el_rol("El usuario debe presentar la queja ante la EPS.") is False


def test_otros_alfabetos_tambien_cuentan():
    assert deriva_de_idioma("El articulo 20 dice что-то совсем другое.") is True


# --- el resumen y su denominador ---------------------------------------------

def test_el_resumen_cuenta_cada_etiqueta_y_el_denominador():
    registros = [{"id": 910, "generated": CASO_910},
                 {"id": 4527, "generated": CASO_4527},
                 {"id": 1, "generated": BIEN}]

    r = resumen(registros)

    assert r["n"] == 3
    assert r["alguno"] == 2
    assert r["deriva_de_idioma"] == 2
    assert r["rompe_el_rol"] == 1
    assert r["turno_ficticio"] == 1
    assert r["ids"] == [910, 4527]


def test_sin_fallos_el_resumen_queda_en_cero_pero_con_su_n():
    """El cero del afinado solo significa algo junto a su denominador."""
    r = resumen([{"id": 1, "generated": BIEN}] * 334)

    assert (r["n"], r["alguno"]) == (334, 0)
