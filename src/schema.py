"""
Esquema del dominio: acción de tutela (Colombia).

Un solo lugar define los campos, los valores válidos y cómo se renderiza la
salida. M1 entrena contra `render_salida`, M2 puntúa campo por campo contra
estos mismos campos, y M3 verifica `fundamento` contra el corpus.
"""
from __future__ import annotations
import json, re, unicodedata
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

# --------------------------------------------------------------------------
# Vocabularios cerrados. Si un valor no está aquí, el validador falla.
# --------------------------------------------------------------------------
DERECHOS = {
    "salud",
    "peticion",
    "seguridad_social",
    "habeas_data",
    "debido_proceso",
    "educacion",
    "estabilidad_laboral_reforzada",
    "trabajo",
    "minimo_vital",
    "libertad_personal",
    "colectivos",
    "ninguno",
    # Valvula de escape del campo `derecho`. El porque esta en el bloque de
    # DERECHO_ESCAPE, mas abajo.
    "no_determinable",
}

MECANISMOS = {
    "tutela": "acción de tutela",
    "accion_popular": "acción popular (Ley 472 de 1998)",
    "accion_cumplimiento": "acción de cumplimiento (Ley 393 de 1997)",
    "habeas_corpus": "habeas corpus (Ley 1095 de 2006)",
    "via_ordinaria": "vía judicial ordinaria",
}

SPLITS = {"train", "validation", "eval", "eval_m3"}

# `abstencion`: casos sin respuesta correcta en el vocabulario cerrado. Llevan
# `mecanismo: null` a propósito y no entran en la accuracy por campo; miden si
# el sistema sabe callarse en vez de forzar una etiqueta.
TIPOS_EVAL = {"gold", "adversarial", "abstencion"}
SPLITS_EVAL = {"eval", "eval_m3"}

CAMPOS_SALIDA = ["derecho", "accionado", "mecanismo", "procede", "pretension"]

# --------------------------------------------------------------------------
# Renderizado: de los campos estructurados al texto que ve el modelo.
# --------------------------------------------------------------------------
# Texto con el que el sistema se abstiene. Tiene que estar en el PROMPT y en
# la métrica a la vez: no se puede medir si el sistema sabe callarse si nunca
# se le dijo que puede, y no se puede detectar la abstención si cada corrida la
# escribe distinto.
MECANISMO_ESCAPE = "no determinable"

# Valvula de escape del campo `derecho`. Existe porque `ninguno` estaba
# SOBRECARGADO: en el dataset v3.1.0 lo usaban tres conclusiones distintas
# --- 20 casos de via_ordinaria ("no hay derecho fundamental que amparar"),
# 16 de accion_cumplimiento ("lo exigible es el cumplimiento de una norma") y
# 18 de abstencion ("no se puede determinar nada") ---, o sea 54 de 143
# ejemplos con UNA etiqueta para TRES razonamientos. No es teoria: de los 16
# errores de `derecho` de la corrida m1/20261015T185732Z, SEIS fueron emitir
# `ninguno` donde si habia un derecho identificable.
#
# Los dos primeros usos si significan lo mismo --- no hay derecho fundamental
# en juego --- y siguen compartiendo `ninguno`. El que se separa es la
# abstencion, que no afirma nada sobre el derecho sino sobre el INSUMO.
#
# Dos detalles deliberados:
#   - la clave va en snake_case y el texto renderizado con espacio, porque
#     `parse_salida` normaliza el valor y cambia espacios por guiones bajos:
#     asi "no determinable" en la salida vuelve a `no_determinable` al
#     parsear, y el viaje de ida y vuelta cierra;
#   - el texto es EL MISMO que el del mecanismo, para que una salida que no se
#     puede determinar lo diga igual en los dos campos, en vez de obligar al
#     lector (y al juez de M2) a aprender dos vocabularios de escape.
DERECHO_ESCAPE = "no_determinable"
DERECHO_ESCAPE_TEXTO = MECANISMO_ESCAPE

FRASES_ESCAPE = (
    "no determinable",
    "no es posible determinar",
    "no se puede determinar",
    "informacion insuficiente",
    "información insuficiente",
    "hechos insuficientes",
    "fuera del alcance",
    "no aplica",
)

SISTEMA_TRIAJE = (
    "Eres un asistente de triaje de acciones constitucionales en Colombia. "
    "Clasificas el caso y respondes SIEMPRE con exactamente cinco líneas, en "
    "este orden: Derecho, Accionado, Mecanismo, Procedencia, Pretensión. "
    "Sin texto adicional."
)
"""La instrucción de sistema del triaje, en un solo sitio.

M1 la compone con `GUIA_DERECHOS_VECINOS` para entrenar; M2 la usa tal cual
para generar las respuestas del experimento de auto-preferencia, donde lo que
hace falta es un prompt NEUTRO: si el modelo de la familia del juez recibiera
la guía y el evaluado no, la comparación mediría la guía y no el linaje.
"""


# --------------------------------------------------------------------------
# Desambiguación de derechos vecinos
# --------------------------------------------------------------------------
# Los errores del campo `derecho` del modelo ajustado NO están repartidos: se
# concentran en cuatro pares concretos, y los cuatro son vecinos de contenido,
# no confusiones arbitrarias. Una guía enumerable sirve justo para eso; un
# "clasifica bien el derecho" no.
#
# El criterio de cada par es el MISMO que usa la jurisprudencia para
# separarlos: cuál es el bien que se reclama, no qué palabras usa el relato.
# Por eso la guía dice dónde mirar en vez de dar una regla mecánica.
GUIA_DERECHOS_VECINOS = (
    "Pares que se confunden. El criterio es QUÉ se reclama, no qué palabras "
    "usa el relato:\n"
    "seguridad_social = una prestación del sistema (pensión, licencia) · "
    "minimo_vital = la subsistencia misma\n"
    "trabajo = salarios o prestaciones impagos · minimo_vital = sin ese "
    "dinero no hay con qué vivir\n"
    "salud = un servicio médico · estabilidad_laboral_reforzada = conservar "
    "el empleo por una condición de salud\n"
    "peticion = falta la RESPUESTA · habeas_data = el dato existe y está mal "
    "o se divulgó"
)
"""Los cuatro pares, en la forma mas corta que conserva el criterio.

LA PRIMERA VERSION NO CABIA, Y NO ERA UN PROBLEMA DE `MAX_LEN`.

Ocupaba 1147 caracteres --- unos 350 tokens --- sobre un presupuesto de 640.
Sin ella, el ejemplo de entrenamiento mas largo pedia ~555 tokens y entraba
con margen; con ella, **los 110 ejemplos tocaban el techo** y las respuestas
que el modelo debe aprender quedaban truncadas. El `assert` del notebook lo
cazo, pero el sintoma ("sube MAX_LEN") invitaba al arreglo equivocado: subir
el limite habria duplicado la memoria de activaciones y, peor, habria dejado
350 tokens de texto IDENTICO repetidos en cada uno de los 110 ejemplos de un
LoRA. La guia era mas larga que la mayoria de los casos.

El contenido informativo son cuatro pares y un criterio. Eso cabe en ~400
caracteres, y lo que se pierde es prosa, no senal.
"""

PROMPT = (
    "Clasifica el siguiente caso e indica el mecanismo constitucional idóneo.\n\n"
    "Si el relato no describe la vulneración o amenaza de un derecho, o si los "
    "hechos no alcanzan para determinar el mecanismo, responde "
    f"'Derecho: {DERECHO_ESCAPE_TEXTO}' y 'Mecanismo: {MECANISMO_ESCAPE}', y "
    "explica en la procedencia qué falta. Es preferible decir que no se puede "
    "determinar que afirmar un mecanismo que los hechos no sostienen. "
    "No lo confundas con 'Derecho: ninguno', que afirma algo distinto: que el "
    "caso sí se entiende y que no hay un derecho fundamental en juego, como "
    "en un pleito contractual o en una acción de cumplimiento.\n\n"
    "Caso: {relato}"
)


def render_salida(ej: dict) -> str:
    """Convierte los campos gold en el bloque de 5 líneas que el modelo aprende.

    `mecanismo: None` renderiza la abstención: así los casos sin respuesta
    correcta se pueden usar como ejemplo de entrenamiento y como referencia del
    juez, en vez de quedar fuera del formato.
    """
    procede = "sí" if ej["procede"] else "no"
    mec = MECANISMOS[ej["mecanismo"]] if ej["mecanismo"] else MECANISMO_ESCAPE
    fund = ej.get("fundamento") or ""
    # La clave de escape se guarda en snake_case y se escribe con espacio;
    # ver DERECHO_ESCAPE.
    val = DERECHO_ESCAPE_TEXTO if ej["derecho"] == DERECHO_ESCAPE else ej["derecho"]
    derecho = f"{val} ({fund})" if fund else val
    return (
        f"Derecho: {derecho}\n"
        f"Accionado: {ej['accionado']}\n"
        f"Mecanismo: {mec}\n"
        f"Procedencia: {procede} — {ej['razon']}\n"
        f"Pretensión: {ej['pretension']}"
    )


# --------------------------------------------------------------------------
# CUANDO se abstiene el motor. El "como" esta arriba (MECANISMO_ESCAPE); esto
# es el criterio, y hasta ahora no existia.
#
# POR QUE HACIA FALTA, CON EL NUMERO QUE LO MOTIVA
#
# En m3/20261019T173316Z los tres brazos de LLM acertaron 3 de 6 abstenciones
# y el brazo del motor 0 de 6. `sistema.DEFECTO_PRO_HOMINE` explica ese cero y
# lo explica bien para lo que cubre: ante un hecho DUDOSO no se activa causal
# de improcedencia, porque el error caro es cerrarle la puerta a quien si tenia
# un mecanismo. Pero los seis casos de abstencion no son hechos dudosos. Son
# una consulta de inversion, una pregunta de examen, un relato sin fechas, una
# investigacion arancelaria, un relato que se contradice y un pronostico sobre
# lo que hara una EPS. En ninguno hay un dato incierto: no hay caso.
#
# Pro homine responde "ante la duda, que proceda". No responde "ante la
# ausencia de caso, inventa uno". Lo segundo no es generosidad con el
# solicitante: es darle una via que no le sirve.
#
# QUE SE PREGUNTA, Y QUE NO
#
# Se pregunta un HECHO --- hay o no una situacion propia del solicitante, con
# accionado y con una orden que pedir --- y no una cuestion de derecho. El
# extractor sigue sin elegir mecanismo; el motor sigue siendo el unico que
# decide. Las tres razones son generales (no es su caso / no hay a quien
# dirigirla / el relato no se sostiene), no una lista copiada de las familias
# del eval set: una taxonomia ajustada a los seis casos que hay que acertar no
# mediria nada.
#
# HONESTAMENTE: el criterio se escribio SABIENDO que esos seis existen, y n=6
# no valida ningun criterio de abstencion. Lo que si se puede falsar es el otro
# lado, y ahi la muestra es 17 veces mayor: `abstencion_indebida` sobre los 103
# casos CON respuesta correcta vale 0.0 hoy, y si este criterio se abstiene de
# mas, sube. Es el numero que hay que mirar en la proxima corrida, no el 0 de 6.
#
# UNA DE LAS SEIS SE QUEDA FUERA A PROPOSITO. La investigacion arancelaria de
# la DIAN (AB54) tiene accionado identificable y pretension concreta: pasa el
# criterio y el motor le propondra `via_ordinaria`, que no es una respuesta
# absurda. Cazarla exigiria un filtro de "materia no constitucional", que es
# una competencia juridica, no un hecho --- justo el tipo de juicio que este
# proyecto le quita al modelo. Se prefiere fallar ese caso a mover la frontera.
PREGUNTA_TRIABLE = (
    '  "caso_triable": ¿el relato pide el triaje de una situación PROPIA del '
    'solicitante, con una autoridad o un particular identificable y una '
    'pretensión concreta que un juez podría ordenar? Va **false** solo por una '
    'de estas tres razones DE HECHO: (a) no es su caso —una pregunta de '
    'doctrina, una consulta de negocio, o un pronóstico sobre lo que hará un '
    'tercero—; (b) no hay a quién dirigir la acción ni orden que pedir; (c) el '
    'propio relato dice que todavía no tiene los hechos, o afirma dos hechos '
    'esenciales que no pueden ser ciertos a la vez. Ante la duda va **true**: '
    'cerrarle la puerta a quien sí tenía un mecanismo es el error caro,\n'
    '  "motivo_no_triable": si lo anterior es false, en una frase, cuál de las '
    'tres razones y por qué; si es true, cadena vacía'
)
"""Las dos lineas que se anaden al JSON de los prompts de hechos.

Una sola definicion para los dos prompts (`sistema.PROMPT_HECHOS` y
`agente.PROMPT_HECHOS_AGENTE`). Dos copias divergirian en el primer arreglo
que se hiciera a una sola, y entonces el brazo hibrido y el del agente se
abstendrian con criterios distintos sin que nada lo dijera."""


def con_pregunta_triable(prompt: str) -> str:
    """Anade `PREGUNTA_TRIABLE` al final del objeto JSON de un prompt."""
    i = prompt.rfind("\n}")
    if i < 0:
        raise ValueError("el prompt de hechos no termina en un objeto JSON")
    return prompt[:i] + ",\n" + PREGUNTA_TRIABLE + prompt[i:]


def leer_triable(d: dict) -> tuple[bool, str]:
    """Dijo el extractor que NO hay caso que triar, y por que.

    Devuelve `(no_triable, motivo)`. El default es triable: si la clave falta
    --- porque el JSON se trunco, porque el modelo la ignoro, o porque el
    prompt es de una version anterior --- no se abstiene. Es el mismo criterio
    pro homine que el resto del extractor, aplicado al sitio donde ahora
    importa: una abstencion por omision seria exactamente el error caro.
    """
    v = d.get("caso_triable", True)
    if isinstance(v, str):
        v = v.strip().lower() not in ("false", "no", "0", "")
    if v:
        return False, ""
    return True, str(d.get("motivo_no_triable") or "").strip()[:300]


def abstenerse(campos: dict, motivo: str = "") -> dict:
    """Los campos de una salida, convertidos en la abstencion del formato.

    UNA funcion para los tres brazos que deciden con el motor
    (`SistemaReglas`, `SistemaHibrido` y `Agente`). Tres copias del `if`
    divergen en el primer arreglo que se haga a una sola, y entonces dos
    brazos se abstendrian escribiendo cosas distintas --- que es justo lo que
    `se_abstuvo` no podria detectar igual en los dos.

    Se borran el FUNDAMENTO, el ACCIONADO y la PRETENSION a proposito. El
    fundamento, porque citar articulos mientras se escribe "no determinable"
    es incoherente y `metricas` mide la pertinencia de las citas contra el
    gold, que en un caso de abstencion no tiene ninguna. Los otros dos, porque
    la razon que se escribe justo debajo dice que no hay accionado ni
    pretension identificables: nombrarlos en la linea de arriba contradiria a
    la de abajo en la misma salida de cinco lineas.
    """
    razon = ("el relato no plantea el triaje de una situación propia del "
             "solicitante, con accionado y pretensión identificables, así que "
             "no hay mecanismo que proponer")
    if motivo:
        razon += ". " + motivo[0].upper() + motivo[1:]
    return {**campos, "derecho": DERECHO_ESCAPE, "fundamento": "",
            "accionado": "no aplica", "pretension": "no aplica",
            "mecanismo": None, "procede": False, "razon": razon}


def se_abstuvo(salida: str) -> bool:
    """¿La respuesta se abstuvo en vez de afirmar un mecanismo?

    Dos vías: no emitió ningún mecanismo del vocabulario cerrado, o escribió
    una de las frases de escape. La segunda hace falta porque un modelo puede
    escribir 'Mecanismo: no determinable (posiblemente tutela)' y el parser
    resolvería 'tutela'.
    """
    p = parse_salida(salida)
    if p.get("mecanismo") is None:
        return True
    # El escaneo se limita al MECANISMO y la PROCEDENCIA: ahi se expresa la
    # abstencion. Mirar toda la salida daba falsos positivos, porque un
    # "Accionado: no aplica" perfectamente legitimo contiene una frase de
    # escape y hacia pasar por abstencion a un sistema que si respondio.
    ambito = _norm(" ".join(filter(None, [p.get("mecanismo_crudo"),
                                          p.get("razon")])))
    return any(_norm(f) in ambito for f in FRASES_ESCAPE)


# Caracteres CJK y marcas de turno del chat. Ninguno de los dos puede formar
# parte de una respuesta de triaje juridico colombiano, asi que su aparicion
# marca donde empieza la cola degenerada.
_RE_CJK = re.compile(
    r"[\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff"
    r"\uf900-\ufaff\uff00-\uffef]")
_RE_TURNO = re.compile(r"<\|im_(?:start|end)\|>|^\s*(?:user|assistant|system)\s*$",
                       re.MULTILINE)


def recortar_al_bloque(salida: str) -> tuple[str, bool]:
    """Corta la cola degenerada. Devuelve (texto, se_recorto).

    POR QUE HACE FALTA
        En la corrida m1/20261015T194000Z, 4 de 46 salidas del modelo ajustado
        siguieron generando despues del cuarto campo: se desviaban al chino y
        abrian un turno falso del chat. No era el limite de tokens --- la
        salida mas larga eran 494 caracteres contra un limite de 200 --- sino
        fuga del modelo base: Qwen2.5 es de origen chino y el adaptador no
        aprendio a emitir EOS de forma fiable.

        Esa cola contamina ROUGE-L, la similitud por embeddings y el conteo de
        citas, y sobre todo contamina a M2, que le pasa estas mismas salidas al
        juez: el juez habria puntuado nuestra basura, no el razonamiento.

    POR QUE DEVUELVE SI RECORTO
        Porque limpiar en silencio haria desaparecer el defecto del informe
        dejandolo intacto en el sistema, que es el patron que este proyecto
        corrige en todas partes. Quien llama tiene que CONTARLO.

        El recorte no inventa el campo que falta: si el modelo nunca escribio
        la linea de Pretension, despues de recortar sigue faltando y
        `adherencia_estructural` lo sigue reflejando. Eso es correcto.
    """
    cortes = [m.start() for m in (_RE_CJK.search(salida), _RE_TURNO.search(salida))
              if m is not None]
    if not cortes:
        return salida, False
    return salida[:min(cortes)].rstrip(), True


def render_entrada(ej: dict) -> str:
    return PROMPT.format(relato=ej["relato"])


def render_ejemplo(ej: dict, eos: str = "") -> str:
    """Texto completo de entrenamiento (formato del notebook de S04)."""
    return f"Pregunta: {render_entrada(ej)}\nRespuesta: {render_salida(ej)}{eos}"


# --------------------------------------------------------------------------
# Parseo: del texto que genera el modelo de vuelta a campos. Lo usa M2.
# --------------------------------------------------------------------------
_RE_CAMPO = re.compile(
    r"^(derecho|accionado|mecanismo|procedencia|pretensi[óo]n)\s*:\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c))


# El índice inverso se construye normalizado: el modelo puede escribir el
# mecanismo con o sin tildes y debe resolver igual.
_INV_MECANISMOS = {_norm(v.split(" (")[0]): k for k, v in MECANISMOS.items()}
_INV_MECANISMOS.update({_norm(k): k for k in MECANISMOS})
_INV_MECANISMOS["tutela"] = "tutela"


ETIQUETAS = ("derecho", "accionado", "mecanismo", "procedencia", "pretension")


def etiquetas_presentes(texto: str) -> set[str]:
    """Qué etiquetas aparecen, sin mirar si el valor es válido.

    Separa dos cosas que `parse_salida` mezcla: el modelo base de M1 emite las
    cinco líneas pero con valores fuera del vocabulario ("Petición de Amparo"),
    y el parser las devuelve como None. Medir ambas por separado evita atribuir
    al fine-tuning una mejora de formato que en realidad fue de vocabulario.
    """
    out = set()
    for campo, _ in _RE_CAMPO.findall(texto):
        c = _norm(campo)
        out.add("pretension" if c.startswith("pretensi") else c)
    return out & set(ETIQUETAS)


def parse_salida(texto: str) -> dict:
    """Tolerante a ruido: extrae lo que encuentre, deja None lo que falte.

    Un modelo de 1.5B entrenado con 20 ejemplos a veces sigue generando después
    del quinto campo. Parseamos solo la primera aparición de cada uno.
    """
    out = {k: None for k in CAMPOS_SALIDA}
    out["fundamento"] = None
    out["razon"] = None
    out["mecanismo_crudo"] = None

    for campo, valor in _RE_CAMPO.findall(texto):
        campo, valor = _norm(campo), valor.strip()
        if campo == "derecho" and out["derecho"] is None:
            m = re.match(r"([^(]+)(?:\((.+)\))?", valor)
            out["derecho"] = _norm(m.group(1)).replace(" ", "_")
            out["fundamento"] = (m.group(2) or "").strip() or None
        elif campo == "accionado" and out["accionado"] is None:
            out["accionado"] = valor
        elif campo == "mecanismo" and out["mecanismo"] is None:
            out["mecanismo"] = _INV_MECANISMOS.get(_norm(valor.split(" (")[0]))
            # Se conserva el texto tal como lo escribio el modelo: hace falta
            # para detectar la abstencion, que no resuelve a ningun valor del
            # vocabulario cerrado pero si deja rastro en la linea.
            out["mecanismo_crudo"] = valor
        elif campo == "procedencia" and out["procede"] is None:
            cuerpo = valor.split("—")[0] if "—" in valor else valor.split("-")[0]
            out["procede"] = _norm(cuerpo).startswith("si")
            out["razon"] = valor.split("—", 1)[1].strip() if "—" in valor else None
        elif campo.startswith("pretensi") and out["pretension"] is None:
            out["pretension"] = valor

    return out


# --------------------------------------------------------------------------
# Validación del dataset.
# --------------------------------------------------------------------------
def citas(fundamento: str) -> list[str]:
    """Extrae cada cita normativa individual de un campo `fundamento`."""
    return [c.strip() for c in re.split(r"[;,]", fundamento or "") if c.strip()]


def cargar_normas() -> set[str]:
    d = json.loads((DATA / "normas.json").read_text(encoding="utf-8"))
    validas = set(d["constitucion"]) | set(d["leyes"])
    validas |= {
        f"{k} Decreto 2591 de 1991"
        for k in d["decreto_2591_1991"]
        if not k.startswith("_")
    }
    return validas


# --------------------------------------------------------------------------
# Los dos planos de una cita
# --------------------------------------------------------------------------
# Una cita puede sostener dos cosas distintas y el campo `fundamento` las
# mezclaba:
#
#   MECANISMO  por que este asunto va por tutela y no por accion popular.
#              Es el plano procesal: art. 86 CP, el Decreto 2591, la Ley 393.
#   DERECHO    que derecho de fondo esta en juego. art. 49 CP (salud),
#              Ley 1751, art. 23 CP (peticion).
#
# Mezclarlos tenia una consecuencia medida: en el eval set los 8 casos de
# cumplimiento citan art. 87 CP, los 8 de popular citan art. 88 CP, los 8 de
# habeas corpus citan art. 30 CP... y `art. 86 CP` NO aparece en ningun
# fundamento, aunque 27 casos son de tutela. Solo 3 de esos 27 llevan alguna
# cita del plano procesal, contra 8/8 en los demas mecanismos. El campo
# responde "que mecanismo y por que" en los no-tutela y "que derecho se
# protege" en los de tutela: dos preguntas bajo el mismo nombre. Por eso
# `pertinencia_citas` contaba como impertinente el art. 86 CP, que es la norma
# que crea la tutela y lo que emite el motor de reglas.
#
# La particion NO se escribe a mano: se deriva de normas.json. Un norma es del
# plano procesal si CREA o REGULA una accion; del plano de fondo si RECONOCE un
# derecho. La propia Constitucion lo resuelve: su art. 30 se titula "Habeas
# corpus" (procesal) y su art. 28 "Libertad personal" (fondo).
# --------------------------------------------------------------------------
LEYES_PROCESALES = (
    "Ley 393 de 1997",     # regula la accion de cumplimiento
    "Ley 472 de 1998",     # regula las acciones populares y de grupo
    "Ley 1095 de 2006",    # regula el habeas corpus
    "Ley 1437 de 2011",    # CPACA: la via contenciosa ordinaria
)


def planos_normativos() -> tuple[set[str], set[str]]:
    """(plano del mecanismo, plano del derecho de fondo).

    El plano procesal se arma con las normas que los propios `mecanismos` de
    normas.json declaran como su fundamento, mas todo el Decreto 2591 --- que
    es el estatuto procesal de la tutela, incluidas las causales del art. 6 y
    la transitoria del art. 8 --- mas las leyes que regulan los otros
    mecanismos. El resto de la whitelist es plano de fondo.
    """
    d = json.loads((DATA / "normas.json").read_text(encoding="utf-8"))
    mecanismo = set()
    for m in d["mecanismos"].values():
        mecanismo |= set(citas(m["fundamento"]))
    mecanismo |= {f"{k} Decreto 2591 de 1991"
                  for k in d["decreto_2591_1991"] if not k.startswith("_")}
    mecanismo |= {l for l in LEYES_PROCESALES if l in d["leyes"]}
    mecanismo.discard("Decreto 2591 de 1991")   # el decreto entero, sin articulo
    return mecanismo, cargar_normas() - mecanismo


def separar_planos(fundamento: str) -> tuple[list[str], list[str]]:
    """Parte un `fundamento` en (citas de mecanismo, citas de fondo).

    Una cita que no este en la whitelist se cuenta como de fondo: no es tarea
    de esta funcion detectar alucinaciones, eso lo hace
    `metricas.alucinacion_normativa`.
    """
    mec, _ = planos_normativos()
    cs = citas(fundamento)
    return ([c for c in cs if c in mec], [c for c in cs if c not in mec])


def validar(ejemplos: list[dict]) -> list[str]:
    """Devuelve la lista de errores. Vacía = dataset limpio."""
    errores, vistos = [], set()
    normas = cargar_normas()

    for ej in ejemplos:
        eid = ej.get("id", "<sin id>")

        if eid in vistos:
            errores.append(f"{eid}: id duplicado")
        vistos.add(eid)

        for campo in ("id", "split", "relato", "derecho", "fundamento",
                      "accionado", "mecanismo", "procede", "razon", "pretension"):
            if campo not in ej:
                errores.append(f"{eid}: falta el campo '{campo}'")

        if ej.get("derecho") not in DERECHOS:
            errores.append(f"{eid}: derecho inválido '{ej.get('derecho')}'")

        # El mecanismo puede ser null SOLO en los casos de abstención, donde no
        # hay respuesta correcta que exigir. En todo lo demás sigue cerrado.
        es_abstencion = ej.get("tipo") == "abstencion"
        if es_abstencion:
            if ej.get("mecanismo") is not None:
                errores.append(
                    f"{eid}: tipo abstencion exige mecanismo null, llegó "
                    f"'{ej.get('mecanismo')}'")
        elif ej.get("mecanismo") not in MECANISMOS:
            errores.append(f"{eid}: mecanismo inválido '{ej.get('mecanismo')}'")

        # `no_determinable` y la abstención son la misma cosa dicha en dos
        # campos distintos. Si uno aparece sin el otro, la salida se
        # contradice, así que el par se exige en los dos sentidos.
        if es_abstencion and ej.get("derecho") != DERECHO_ESCAPE:
            errores.append(
                f"{eid}: tipo abstencion exige derecho '{DERECHO_ESCAPE}', "
                f"llegó '{ej.get('derecho')}'")
        if not es_abstencion and ej.get("derecho") == DERECHO_ESCAPE:
            errores.append(
                f"{eid}: derecho '{DERECHO_ESCAPE}' solo vale en casos de "
                "abstencion; para 'no hay derecho fundamental en juego' el "
                "valor es 'ninguno'")

        if ej.get("split") not in SPLITS:
            errores.append(f"{eid}: split inválido '{ej.get('split')}'")
        if ej.get("split") in SPLITS_EVAL and ej.get("tipo") not in TIPOS_EVAL:
            errores.append(
                f"{eid}: split de evaluación requiere tipo "
                f"{'|'.join(sorted(TIPOS_EVAL))}")

        # Coherencia: procede=True si y solo si el mecanismo es la tutela.
        if ej.get("procede") is not (ej.get("mecanismo") == "tutela"):
            errores.append(
                f"{eid}: incoherencia procede={ej.get('procede')} "
                f"vs mecanismo={ej.get('mecanismo')}"
            )

        # Toda cita debe existir en el whitelist.
        for c in citas(ej.get("fundamento", "")):
            if c not in normas:
                errores.append(f"{eid}: cita fuera del whitelist -> '{c}'")

        if len(ej.get("relato", "")) < 40:
            errores.append(f"{eid}: relato demasiado corto")

    return errores


def cargar(split: str | None = None, archivo: str = "dataset.json") -> list[dict]:
    datos = json.loads((DATA / archivo).read_text(encoding="utf-8"))
    ejemplos = datos["ejemplos"] if isinstance(datos, dict) else datos
    return [e for e in ejemplos if split is None or e["split"] == split]
