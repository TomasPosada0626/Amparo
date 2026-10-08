"""El manifiesto es lo que permite saber con que se corrio cada cifra de M3.

Ninguna corrida de M3 registraba nada, y el problema dejo de ser teorico el 6 de
octubre: el adaptador de Drive se sobrescribio, asi que ya no se sabe con que
modelo salio ninguna cifra anterior a esa fecha. Lo que estos tests fijan es que
el manifiesto distinga de verdad dos corridas distintas, que es lo unico que lo
hace util.
"""
from __future__ import annotations

import json

from tools.rag import manifiesto


def test_la_huella_cambia_si_el_contenido_cambia(tmp_path):
    """Una fecha no dice si el archivo cambio; una huella si. Es la diferencia
    entre "las dos corridas dicen 2026-10-07" y "las dos midieron sobre lo
    mismo"."""
    a = tmp_path / "indice.faiss"
    a.write_bytes(b"vectores version 1")
    primera = manifiesto.huella_archivo(a)

    a.write_bytes(b"vectores version 2")
    segunda = manifiesto.huella_archivo(a)

    assert primera and segunda and primera != segunda


def test_una_ruta_que_no_existe_da_none_y_no_tumba_la_corrida(tmp_path):
    """El manifiesto se arma tambien fuera de Colab, donde las rutas de Drive no
    existen. Un campo en None dice "no se pudo registrar", que es informacion;
    una excepcion tumbaria la corrida por un dato accesorio."""
    assert manifiesto.huella_archivo(tmp_path / "no_existe.faiss") is None
    assert manifiesto.huella_directorio(tmp_path / "no_existe") is None


def test_la_huella_del_directorio_ve_los_nombres_y_el_contenido(tmp_path):
    d = tmp_path / "corpus"
    d.mkdir()
    (d / "ley_a.md").write_text("texto a", encoding="utf-8")
    (d / "ley_b.md").write_text("texto b", encoding="utf-8")
    base = manifiesto.huella_directorio(d, patron="*.md")

    (d / "ley_b.md").write_text("texto b corregido", encoding="utf-8")
    assert manifiesto.huella_directorio(d, patron="*.md") != base, "no vio el cambio de contenido"

    (d / "ley_b.md").write_text("texto b", encoding="utf-8")
    (d / "ley_c.md").write_text("texto c", encoding="utf-8")
    assert manifiesto.huella_directorio(d, patron="*.md") != base, "no vio la norma nueva"


def test_el_manifiesto_registra_lo_que_hace_falta_para_reproducir():
    m = manifiesto.construir("s10", use_lora=True, n_chunks=3420, n_eval_set=75)

    assert m.modulo == "s10"
    assert m.use_lora is True
    assert m.git_commit and m.git_commit != "unknown"
    assert m.timestamp
    # Las piezas que definen el resultado y que antes no se anotaban.
    assert m.hash_corpus, "sin huella del corpus no se sabe que normas se indexaron"
    assert m.hash_dataset, "sin huella del dataset no se sabe con que se entreno"
    assert m.hash_eval_set, "sin huella del eval set no se sabe sobre que se midio"
    # Config que cambia los resultados sin cambiar el codigo.
    assert m.retrieval["top_k"]
    assert m.retrieval["max_new_tokens_generation"] == 900
    assert "transformers" in m.library_versions


def test_el_manifiesto_se_guarda_como_json_legible(tmp_path):
    m = manifiesto.construir("s08", use_lora=True, n_chunks=3420)
    ruta = m.guardar(tmp_path)

    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos["modulo"] == "s08"
    assert datos["n_chunks"] == 3420
    assert "hash_corpus" in datos
