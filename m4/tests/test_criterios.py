"""Tests de T5 (m4/harness/criterios.py). Sin GPU, sin VLM, sin imagenes reales.

Las salidas de M3 se generan con schema.render_salida, no se escriben a mano:
si el formato de Amparo cambia, estos tests lo notan.

    python -m pytest m4/tests -v
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
import criterios  # noqa: E402

schema = criterios._schema()

SALIDA_TUTELA = schema.render_salida({
    "derecho": "salud", "accionado": "EPS Sura", "mecanismo": "tutela",
    "procede": True, "razon": "no hay otro medio judicial",
    "pretension": "ordenar el medicamento", "fundamento": "",
})
SALIDA_ABSTENCION = schema.render_salida({
    "derecho": schema.DERECHO_ESCAPE, "accionado": "no aplica", "mecanismo": None,
    "procede": False, "razon": "hechos insuficientes", "pretension": "ninguna",
})


def caso(criterio, esperado="", **extra):
    return {"id": extra.pop("id", "c1"), "criterio": criterio, "esperado": esperado, **extra}


def preguntar_falso(respuesta):
    """preguntar_fn falsa: registra con que la llamaron y devuelve `respuesta`."""
    def fn(imagen, texto):
        fn.llamadas.append((imagen, texto))
        return respuesta
    fn.llamadas = []
    return fn


# --------------------------------------------------------------------------
# Las salidas fabricadas son las que creemos
# --------------------------------------------------------------------------
def test_salidas_fabricadas_parsean_como_se_espera():
    assert schema.parse_salida(SALIDA_TUTELA)["mecanismo"] == "tutela"
    assert not schema.se_abstuvo(SALIDA_TUTELA)
    assert schema.parse_salida(SALIDA_ABSTENCION)["mecanismo"] is None
    assert schema.se_abstuvo(SALIDA_ABSTENCION)


# --------------------------------------------------------------------------
# exacto
# --------------------------------------------------------------------------
def test_exacto_acierto():
    assert criterios.nota_exacto(caso("exacto", "tutela"), {"salida": SALIDA_TUTELA}) == 1.0


def test_exacto_tolera_mayusculas_y_espacios_en_esperado():
    assert criterios.nota_exacto(caso("exacto", " Tutela "), {"salida": SALIDA_TUTELA}) == 1.0


def test_exacto_fallo_de_mecanismo():
    assert criterios.nota_exacto(caso("exacto", "habeas_corpus"), {"salida": SALIDA_TUTELA}) == 0.0


def test_exacto_abstencion_esperada_y_se_abstuvo():
    assert criterios.nota_exacto(caso("exacto", "no_determinable"), {"salida": SALIDA_ABSTENCION}) == 1.0


def test_exacto_abstencion_esperada_pero_forzo_etiqueta():
    assert criterios.nota_exacto(caso("exacto", "no_determinable"), {"salida": SALIDA_TUTELA}) == 0.0


def test_exacto_mecanismo_esperado_pero_se_abstuvo():
    assert criterios.nota_exacto(caso("exacto", "tutela"), {"salida": SALIDA_ABSTENCION}) == 0.0


def test_exacto_salida_vacia_o_sin_formato():
    assert criterios.nota_exacto(caso("exacto", "tutela"), {"salida": ""}) == 0.0
    assert criterios.nota_exacto(caso("exacto", "tutela"), {"salida": "[SUSTITUTO M3] tutela"}) == 0.0


def test_exacto_esperado_mal_formado_es_error_no_nota():
    with pytest.raises(ValueError, match="exacto"):
        criterios.nota_exacto(caso("exacto", "acción de tutela"), {"salida": SALIDA_TUTELA})


# --------------------------------------------------------------------------
# campos
# --------------------------------------------------------------------------
ESPERADO_CAMPOS = '{"tipo_documento": "oficio", "plazo_dias": 15}'


def test_campos_acierto_total_normalizado():
    js = {"tipo_documento": "Oficio", "plazo_dias": "15", "entidad": "Alcaldia"}
    assert criterios.nota_campos(caso("campos", ESPERADO_CAMPOS), {"js": js}) == 1.0


def test_campos_acierto_parcial():
    js = {"tipo_documento": "oficio", "plazo_dias": 10}
    assert criterios.nota_campos(caso("campos", ESPERADO_CAMPOS), {"js": js}) == 0.5


def test_campos_campo_ausente_cuenta_cero():
    js = {"tipo_documento": "oficio"}
    assert criterios.nota_campos(caso("campos", ESPERADO_CAMPOS), {"js": js}) == 0.5


def test_campos_js_none_es_cero():
    assert criterios.nota_campos(caso("campos", ESPERADO_CAMPOS), {"js": None, "crudo": "no es json"}) == 0.0


def test_campos_js_que_no_es_objeto_es_cero():
    # parsear_json del notebook devuelve lo que de json.loads: puede ser una lista.
    assert criterios.nota_campos(caso("campos", ESPERADO_CAMPOS), {"js": ["oficio", 15]}) == 0.0


@pytest.mark.parametrize("leido", [15, "15", 15.0, "15.0", " 15 "])
def test_campos_plazo_dias_compara_como_entero(leido):
    assert criterios.nota_campos(caso("campos", '{"plazo_dias": 15}'), {"js": {"plazo_dias": leido}}) == 1.0


@pytest.mark.parametrize("leido", ["15 dias", 15.5, 16, True, None, "No se aprecia en la imagen."])
def test_campos_plazo_dias_que_no_es_ese_entero_es_cero(leido):
    assert criterios.nota_campos(caso("campos", '{"plazo_dias": 15}'), {"js": {"plazo_dias": leido}}) == 0.0


@pytest.mark.parametrize("campo, esperado, leido", [
    ("entidad", "alcaldia de medellin", "Alcaldía de Medellín - Secretaría de Salud"),
    ("entidad", "Alcaldía de Medellín", "ALCALDIA DE\nMEDELLIN"),  # el VLM partio la linea
    ("fecha", "3 de marzo de 2026", "Medellín, 3 de marzo de 2026"),
    ("pretension_visible", "pagar la multa", "Se le exige pagar la multa en 15 días"),
])
def test_campos_texto_libre_acierta_si_contiene_el_fragmento(campo, esperado, leido):
    c = caso("campos", criterios.json.dumps({campo: esperado}))
    assert criterios.nota_campos(c, {"js": {campo: leido}}) == 1.0


@pytest.mark.parametrize("campo, esperado, leido", [
    ("entidad", "alcaldia de medellin", "Gobernación de Antioquia"),
    ("entidad", "alcaldia de medellin", "Alcaldía"),  # leyo menos de lo exigido
    ("fecha", "3 de marzo de 2026", "2026-03-03"),  # otra forma de la fecha: no se adivina
    ("entidad", "alcaldia", None),
    ("entidad", "alcaldia", "No se aprecia en la imagen."),
])
def test_campos_texto_libre_sin_el_fragmento_es_cero(campo, esperado, leido):
    c = caso("campos", criterios.json.dumps({campo: esperado}))
    assert criterios.nota_campos(c, {"js": {campo: leido}}) == 0.0


def test_campos_tipo_documento_es_igualdad_no_fragmento():
    c = caso("campos", '{"tipo_documento": "oficio"}')
    assert criterios.nota_campos(c, {"js": {"tipo_documento": "OFICIO"}}) == 1.0
    assert criterios.nota_campos(c, {"js": {"tipo_documento": "oficio de cobro"}}) == 0.0


@pytest.mark.parametrize("esperado", [
    "no es json", "[\"tipo_documento\"]", "{}", '{"plazo": 15}',
    '{"fecha": null}',                       # null es de valvula
    '{"tipo_documento": "carta"}',           # fuera del vocabulario del VLM
    '{"tipo_documento": "Oficio"}',          # el vocabulario va en minusculas
    '{"plazo_dias": "quince"}', '{"plazo_dias": 15.5}', '{"plazo_dias": true}', '{"plazo_dias": -1}',
    '{"entidad": ""}', '{"entidad": "   "}', '{"fecha": 2026}',
])
def test_campos_esperado_mal_formado_es_error_no_nota(esperado):
    with pytest.raises(ValueError, match="campos|tipo_documento|plazo_dias|entidad|fecha"):
        criterios.nota_campos(caso("campos", esperado), {"js": {"tipo_documento": "oficio"}})


# --------------------------------------------------------------------------
# valvula
# --------------------------------------------------------------------------
def test_valvula_campo_en_null():
    assert criterios.nota_valvula(caso("valvula", "fecha"), {"js": {"fecha": None}}) == 1.0


def test_valvula_texto_de_valvula_cuenta_como_null():
    js = {"fecha": None, "plazo_dias": "No se aprecia en la imagen."}
    assert criterios.nota_valvula(caso("valvula", "fecha|plazo_dias"), {"js": js}) == 1.0


def test_valvula_valor_inventado_es_cero():
    assert criterios.nota_valvula(caso("valvula", "fecha"), {"js": {"fecha": "2026-01-15"}}) == 0.0


def test_valvula_mitad_inventada():
    js = {"fecha": None, "plazo_dias": 10}
    assert criterios.nota_valvula(caso("valvula", "fecha|plazo_dias"), {"js": js}) == 0.5


def test_valvula_js_none_es_cero():
    assert criterios.nota_valvula(caso("valvula", "fecha"), {"js": None, "crudo": "texto suelto"}) == 0.0


@pytest.mark.parametrize("esperado", ["", " | ", "fecah", "fecha|plazo"])
def test_valvula_esperado_mal_formado_es_error_no_nota(esperado):
    # "fecah" con js sin ese campo daria js.get() -> None y regalaria la nota.
    with pytest.raises(ValueError, match="valvula"):
        criterios.nota_valvula(caso("valvula", esperado), {"js": {"fecha": None}})


# --------------------------------------------------------------------------
# juez_vlm
# --------------------------------------------------------------------------
@pytest.mark.parametrize("respuesta", ["SI", "Sí", "sí.", " SI! ", "¿Sí?"])
def test_juez_vlm_si(respuesta):
    fn = preguntar_falso(respuesta)
    assert criterios.nota_juez_vlm(caso("juez_vlm"), {"salida": SALIDA_TUTELA},
                                   preguntar_fn=fn, imagen="img-falsa") == 1.0


@pytest.mark.parametrize("respuesta", ["No", "NO."])
def test_juez_vlm_no(respuesta):
    fn = preguntar_falso(respuesta)
    assert criterios.nota_juez_vlm(caso("juez_vlm"), {"salida": SALIDA_TUTELA},
                                   preguntar_fn=fn, imagen="img-falsa") == 0.0


@pytest.mark.parametrize("respuesta", ["Probablemente sí", "Sí, se sostiene", "si no", "", None])
def test_juez_vlm_ambiguo_es_cero(respuesta):
    fn = preguntar_falso(respuesta)
    assert criterios.nota_juez_vlm(caso("juez_vlm"), {"salida": SALIDA_TUTELA},
                                   preguntar_fn=fn, imagen="img-falsa") == 0.0


def test_juez_vlm_reenvia_el_mismo_objeto_imagen_y_la_salida():
    imagen = object()  # cualquier objeto: el modulo no lo abre
    fn = preguntar_falso("SI")
    criterios.nota_juez_vlm(caso("juez_vlm"), {"salida": SALIDA_TUTELA}, preguntar_fn=fn, imagen=imagen)
    assert len(fn.llamadas) == 1
    recibida, texto = fn.llamadas[0]
    assert recibida is imagen
    assert SALIDA_TUTELA in texto


@pytest.mark.parametrize("kwargs", [{}, {"imagen": "img-falsa"}, {"preguntar_fn": lambda i, t: "SI"}])
def test_juez_vlm_sin_preguntar_fn_o_imagen_es_error(kwargs):
    with pytest.raises(ValueError, match="juez_vlm"):
        criterios.nota_juez_vlm(caso("juez_vlm"), {"salida": SALIDA_TUTELA}, **kwargs)


# --------------------------------------------------------------------------
# Todas las notas en [0, 1]
# --------------------------------------------------------------------------
@pytest.mark.parametrize("c, traza, kwargs", [
    (caso("exacto", "tutela"), {"salida": SALIDA_TUTELA}, {}),
    (caso("exacto", "via_ordinaria"), {"salida": SALIDA_TUTELA}, {}),
    (caso("exacto", "no_determinable"), {"salida": SALIDA_ABSTENCION}, {}),
    (caso("campos", ESPERADO_CAMPOS), {"js": {"tipo_documento": "oficio"}}, {}),
    (caso("campos", ESPERADO_CAMPOS), {"js": None}, {}),
    (caso("valvula", "fecha|entidad|plazo_dias"), {"js": {"fecha": None, "entidad": "X"}}, {}),
    (caso("valvula", "fecha"), {"js": None}, {}),
    (caso("juez_vlm"), {"salida": SALIDA_TUTELA}, {"preguntar_fn": lambda i, t: "Sí", "imagen": "x"}),
    (caso("juez_vlm"), {"salida": ""}, {"preguntar_fn": lambda i, t: "quizas", "imagen": "x"}),
])
def test_toda_nota_esta_en_rango(c, traza, kwargs):
    nota = criterios.calificar(c, traza, **kwargs)
    assert isinstance(nota, float)
    assert 0.0 <= nota <= 1.0


# --------------------------------------------------------------------------
# calificar
# --------------------------------------------------------------------------
@pytest.mark.parametrize("criterio", criterios.CRITERIOS_VALIDOS)
def test_calificar_enruta_a_la_funcion_del_criterio(criterio, monkeypatch):
    llamadas = []
    for nombre in criterios.CRITERIOS_VALIDOS:
        monkeypatch.setitem(criterios.CRITERIOS, nombre,
                            lambda c, t, _n=nombre, **kw: llamadas.append((_n, kw)) or 0.5)
    nota = criterios.calificar(caso(criterio), {}, preguntar_fn="pf", imagen="img")
    assert nota == 0.5
    assert [n for n, _ in llamadas] == [criterio]
    # Solo juez_vlm recibe preguntar_fn e imagen; los demas criterios no.
    esperados_kw = {"preguntar_fn": "pf", "imagen": "img"} if criterio == "juez_vlm" else {}
    assert llamadas[0][1] == esperados_kw


def test_calificar_da_lo_mismo_que_la_funcion_directa():
    fn = lambda i, t: "SI"
    pares = [
        (caso("exacto", "tutela"), {"salida": SALIDA_TUTELA}, criterios.nota_exacto),
        (caso("campos", ESPERADO_CAMPOS), {"js": {"tipo_documento": "oficio"}}, criterios.nota_campos),
        (caso("valvula", "fecha"), {"js": {"fecha": "ayer"}}, criterios.nota_valvula),
    ]
    for c, t, directa in pares:
        assert criterios.calificar(c, t, preguntar_fn=fn, imagen="x") == directa(c, t)
    c, t = caso("juez_vlm"), {"salida": SALIDA_TUTELA}
    assert criterios.calificar(c, t, preguntar_fn=fn, imagen="x") == \
        criterios.nota_juez_vlm(c, t, preguntar_fn=fn, imagen="x")


@pytest.mark.parametrize("criterio", ["exacta", "Exacto", "", None])
def test_calificar_criterio_desconocido_es_error(criterio):
    with pytest.raises(ValueError, match="no existe"):
        criterios.calificar(caso(criterio, "tutela"), {"salida": SALIDA_TUTELA})


# --------------------------------------------------------------------------
# validar_casos (+ cargar_casos sobre un CSV de verdad)
# --------------------------------------------------------------------------
def filas_validas() -> list[dict]:
    return [
        {"id": "m01", "pregunta": "¿Que hago?", "imagen": "m01.png", "esperado": "tutela",
         "criterio": "exacto", "tipo": "normal"},
        {"id": "m02", "pregunta": "¿Que hago?", "imagen": "m02.png", "esperado": "no_determinable",
         "criterio": "exacto", "tipo": "normal"},
        {"id": "m03", "pregunta": "¿Que dice?", "imagen": "m03.png",
         "esperado": '{"tipo_documento": "oficio", "plazo_dias": 15}', "criterio": "campos", "tipo": "normal"},
        {"id": "m04", "pregunta": "¿Que dice?", "imagen": "m04.png", "esperado": "",
         "criterio": "juez_vlm", "tipo": "normal"},
        {"id": "m05", "pregunta": "¿Que dice?", "imagen": "m05.png", "esperado": "fecha|plazo_dias",
         "criterio": "valvula", "tipo": "adversarial"},
    ]


def escribir_csv(ruta: Path, filas: list[dict], columnas=criterios.COLUMNAS) -> Path:
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(columnas), extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    return ruta


def test_validar_csv_valido(tmp_path):
    casos = criterios.cargar_casos(escribir_csv(tmp_path / "casos_m4.csv", filas_validas()))
    assert len(casos) == 5
    assert criterios.validar_casos(casos) == []


def test_validar_csv_valido_con_imagenes_existentes(tmp_path):
    carpeta = tmp_path / "imagenes"
    carpeta.mkdir()
    for f in filas_validas():
        (carpeta / f["imagen"]).write_bytes(b"")
    casos = criterios.cargar_casos(escribir_csv(tmp_path / "casos_m4.csv", filas_validas()))
    assert criterios.validar_casos(casos, carpeta_imagenes=carpeta) == []


def test_cargar_casos_tolera_bom_de_excel(tmp_path):
    ruta = escribir_csv(tmp_path / "casos_m4.csv", filas_validas())
    ruta.write_bytes(b"\xef\xbb\xbf" + ruta.read_bytes())
    casos = criterios.cargar_casos(ruta)
    assert "id" in casos[0]
    assert criterios.validar_casos(casos) == []


def _sin(filas, i):
    return filas[:i] + filas[i + 1:]


def _con(filas, i, **cambios):
    filas = [dict(f) for f in filas]
    filas[i].update(cambios)
    return filas


# Cada mutacion introduce UN problema; se espera exactamente un mensaje.
MUTACIONES = {
    "menos_de_5_casos": (lambda f: _sin(f, 3), "al menos 5"),
    "sin_adversarial": (lambda f: _con(f, 4, tipo="normal"), "exactamente 1 caso adversarial, hay 0"),
    "dos_adversariales": (lambda f: _con(f, 0, tipo="adversarial"), "exactamente 1 caso adversarial, hay 2"),
    "adversarial_sin_valvula": (lambda f: _con(_con(f, 4, tipo="normal"), 0, tipo="adversarial"),
                                "adversarial debe tener criterio `valvula`"),
    "id_repetido": (lambda f: _con(f, 1, id="m01"), "ids repetidos: ['m01']"),
    "criterio_desconocido": (lambda f: _con(f, 3, criterio="juez"), "m04: criterio 'juez' no existe"),
    "exacto_mal_formado": (lambda f: _con(f, 0, esperado="acción de tutela"), "`exacto` espera"),
    "campos_no_json": (lambda f: _con(f, 2, esperado="tipo_documento=oficio"), "`campos` espera un objeto JSON"),
    "campos_campo_desconocido": (lambda f: _con(f, 2, esperado='{"tipo": "oficio"}'), "el VLM no extrae: ['tipo']"),
    "valvula_vacia": (lambda f: _con(f, 4, esperado=""), "`valvula` lista campos"),
    "valvula_campo_desconocido": (lambda f: _con(f, 4, esperado="fecha|plazo"), "el VLM no extrae: ['plazo']"),
    "juez_vlm_con_esperado": (lambda f: _con(f, 3, esperado="SI"), "`juez_vlm` lleva `esperado` vacio"),
    "campos_con_null": (lambda f: _con(f, 2, esperado='{"fecha": null}'), "no admite null en 'fecha'"),
    "campos_tipo_documento_fuera_de_vocabulario": (lambda f: _con(f, 2, esperado='{"tipo_documento": "carta"}'),
                                                   "`tipo_documento` debe ser una de"),
    "campos_plazo_no_entero": (lambda f: _con(f, 2, esperado='{"plazo_dias": "quince"}'),
                               "`plazo_dias` debe ser un entero"),
    "campos_fragmento_vacio": (lambda f: _con(f, 2, esperado='{"entidad": ""}'), "fragmento de texto no vacio"),
    "tipo_desconocido": (lambda f: _con(f, 0, tipo="facil"), "m01: tipo 'facil' no existe"),
}


@pytest.mark.parametrize("nombre", list(MUTACIONES))
def test_validar_csv_con_un_problema(nombre, tmp_path):
    mutar, fragmento = MUTACIONES[nombre]
    casos = criterios.cargar_casos(escribir_csv(tmp_path / "casos_m4.csv", mutar(filas_validas())))
    problemas = criterios.validar_casos(casos)
    assert len(problemas) == 1, problemas
    assert fragmento in problemas[0]


def test_validar_tipo_adversarial_mal_escrito_no_desaparece_sin_aviso():
    # "Adversarial" no es un tipo valido: se reporta el tipo Y la falta de adversarial.
    problemas = criterios.validar_casos(_con(filas_validas(), 4, tipo="Adversarial"))
    assert any("m05: tipo 'Adversarial' no existe" in p for p in problemas)
    assert any("exactamente 1 caso adversarial, hay 0" in p for p in problemas)
    assert len(problemas) == 2


def test_csv_de_ejemplo_para_lucas_es_valido_y_cubre_los_cuatro_criterios():
    ruta = Path(__file__).resolve().parents[1] / "eval_set" / "casos_m4.ejemplo.csv"
    casos = criterios.cargar_casos(ruta)
    assert criterios.validar_casos(casos) == []
    assert {c["criterio"] for c in casos} == set(criterios.CRITERIOS_VALIDOS)


def test_validar_csv_sin_columna(tmp_path):
    columnas = [c for c in criterios.COLUMNAS if c != "criterio"]
    casos = criterios.cargar_casos(escribir_csv(tmp_path / "casos_m4.csv", filas_validas(), columnas))
    assert criterios.validar_casos(casos) == ["faltan columnas: ['criterio']"]


def test_validar_imagen_inexistente(tmp_path):
    carpeta = tmp_path / "imagenes"
    carpeta.mkdir()
    for f in filas_validas()[1:]:
        (carpeta / f["imagen"]).write_bytes(b"")
    casos = criterios.cargar_casos(escribir_csv(tmp_path / "casos_m4.csv", filas_validas()))
    problemas = criterios.validar_casos(casos, carpeta_imagenes=carpeta)
    assert len(problemas) == 1
    assert "m01: la imagen 'm01.png' no existe" in problemas[0]


def test_validar_tolera_nan_de_pandas_en_esperado_vacio():
    # pandas lee una celda vacia como NaN (float); no debe romper la validacion.
    filas = filas_validas()
    filas[3]["esperado"] = float("nan")
    assert criterios.validar_casos(filas) == []


@pytest.mark.parametrize("js, avisa", [
    ({"plazo_dias": None, "pretension_visible": "un plazo de dos semanas habiles"}, True),
    ({"plazo_dias": None, "pretension_visible": "dentro de 15 dias habiles"}, True),
    ({"plazo_dias": 15, "pretension_visible": "dentro de 15 dias habiles"}, False),
    ({"plazo_dias": None, "pretension_visible": "contratos de 2025 y 2026"}, False),
    (None, False),
])
def test_advertencias_lectura_marca_plazo_sin_respaldo(js, avisa):
    assert bool(criterios.advertencias_lectura(js)) is avisa
