"""
Los sistemas que M3 pone a competir, todos con la misma firma
`sistema(relato) -> str` para que el harness de M2 los mida sin cambios.

  BRAZO 1  fine-tuned solo            (M1, ya medido)
  BRAZO 2  fine-tuned + RAG ingenuo   punto de partida del delta de retrieval
  BRAZO 3  fine-tuned + RAG avanzado  híbrido + reranking + transformación
  BRAZO 4  gpt-oss + RAG + reglas     el techo: enrutamiento determinista

El brazo 4 reparte el trabajo según lo que cada pieza hace bien:

    relato ──► LLM        extrae HECHOS (cuestiones de hecho, no conclusiones)
           ──► REGLAS     deciden el mecanismo (art. 6 D.2591, art. 9 L.393)
           ──► RAG        recupera el texto del artículo que lo soporta
           ──► HERRAMIENTA calcula el término si hay fecha y plazo en juego
           ──► LLM        redacta las cinco líneas

El LLM nunca elige el mecanismo. Por eso el campo `fundamento` no puede
alucinar: lo pone la regla, no la memoria.
"""
from __future__ import annotations
import json
import re

import schema
import terminos
from reglas import HECHOS_EXTRAIBLES, Hechos, decidir

# --------------------------------------------------------------------------
# Brazos 2 y 3: el modelo ajustado con contexto recuperado
# --------------------------------------------------------------------------
INSTRUCCION_RAG = (
    "Eres un asistente de triaje de acciones constitucionales en Colombia. "
    "Clasificas el caso y respondes SIEMPRE con exactamente cinco líneas, en este orden: "
    "Derecho, Accionado, Mecanismo, Procedencia, Pretensión. Sin texto adicional.\n\n"
    "Apóyate ÚNICAMENTE en los artículos citados abajo. Si ninguno aplica, dilo en la "
    "procedencia en vez de inventar una norma."
)


def cita_completa(f: dict) -> str:
    """La cita de un fragmento en la forma que SE PUEDE VERIFICAR.

    POR QUE EXISTE ESTA FUNCION

    Los brazos 2 y 3 salieron con **7.9%** y **10.1%** de citas `incompleta`
    en m3/20261019T173316Z: «art. 6» sin decir de que norma. El medidor las
    separa de `inventada` a proposito --- no dijo de que ley habla no es se lo
    invento --- pero una cita sin norma no se puede comprobar, que es justo lo
    que el corpus verificado existe para garantizar.

    La causa no estaba en el modelo: estaba en como se le ensenaba el corpus.
    La cabecera era `[{norma}, {articulo} — {titulo}]`, con la norma SEPARADA
    del articulo por una coma, asi que «art. 6» aparecia como una pieza suelta
    y el modelo la copiaba suelta. Medido con el clasificador real sobre los
    69 fragmentos: **12 de 16** formas distintas salian `incompleta` con el
    articulo solo, y **ninguna** con el articulo pegado a su norma.

    No se concatena a ciegas: `articulo` YA trae la norma cuando es
    constitucional (`art. 11 CP`), y pegarle el nombre daria «art. 11 CP
    Constitucion Politica de Colombia». Y un fragmento de jurisprudencia se
    cita por la sentencia, no por un articulo.

    LO QUE NO ES DERECHO VIGENTE NO SE SIRVE LISTO PARA COPIAR.

    `data/normas.json` excluye el art. 11 del Decreto 2591 a proposito, y lo
    dice: esta INEXEQUIBLE por C-543/1992, su texto vive en el corpus
    "para que el sistema pueda recuperarlo y contradecir a quien lo invoque",
    y citarlo como fundamento vigente DEBE contar como alucinacion.

    La primera version de esta funcion le habria servido
    `[art. 11 Decreto 2591 de 1991 — ...]` --- una cita impecable, lista para
    copiar --- justo del unico articulo que el proyecto quiere que NO se cite.
    Habria sido ayudar al modelo a fallar la metrica que mas cuida.

    Asi que para un fragmento no vigente se devuelve la forma SEPARADA, que es
    la que el clasificador deja en `incompleta`, con el aviso delante. Es el
    unico sitio del codigo donde una cita peor es la cita correcta.
    """
    art = (f.get("articulo") or "").strip()
    norma = (f.get("norma") or "").strip()
    vig = (f.get("vigencia") or "").strip()
    if vig and not vig.lower().startswith("vigente"):
        return f"NO ES DERECHO VIGENTE ({vig}) · {norma}, {art}"
    if norma.lower().startswith("sentencia"):
        return norma
    if not art:
        return norma
    if art.upper().endswith(" CP") or "constituci" in art.lower():
        return art
    return f"{art} {norma}" if norma else art


def formatear_contexto(frags: list[dict]) -> str:
    # La cabecera lleva la cita COMPLETA y lista para copiar: es lo unico que
    # el modelo tiene delante cuando decide como citar. La excepcion son los
    # fragmentos no vigentes --- ver `cita_completa`.
    return "\n\n".join(
        f"[{cita_completa(f)} — {f['titulo']}]\n{f['texto']}" for f in frags)


class SistemaRAG:
    """Modelo generativo + recuperación. `generar` recibe (sistema, usuario) y
    devuelve texto; así el mismo código sirve para el Qwen local y para Groq."""

    def __init__(self, generar, indice, estrategia: str = "hibrido",
                 k: int = 5, transformador=None, etiqueta: str = "RAG"):
        self.generar = generar
        self.indice = indice
        self.estrategia = estrategia
        self.k = k
        self.transformador = transformador
        self.etiqueta = etiqueta
        self.trazas: list[dict] = []
        from costos import Costos
        self.costos = Costos(etiqueta)

    def __call__(self, relato: str) -> str:
        import time
        self.costos.nuevo_caso()
        consulta = self.transformador(relato) if self.transformador else relato
        frags = self.indice.recuperar(consulta, estrategia=self.estrategia, k=self.k)
        usuario = (f"NORMAS APLICABLES:\n{formatear_contexto(frags)}\n\n"
                   f"{schema.PROMPT.format(relato=relato)}")
        _t = time.perf_counter()
        salida = self.generar(INSTRUCCION_RAG, usuario)
        # Tokens de un modelo LOCAL. `usage` solo existe si la llamada fue
        # a una API; `model.generate()` no devuelve nada parecido, y por eso
        # los brazos 2 y 3 salieron con `llamadas_sin_usage: 90` y
        # `tokens_por_caso: null` en m3/20261019T173316Z. El tokenizador si
        # los cuenta, asi que el generador los publica en `ultimos_tokens` y
        # se leen AQUI, justo despues de la llamada propia: entre una cosa y
        # la otra no corre nada, asi que dos brazos que comparten generador no
        # pueden mezclar su contabilidad.
        _tk = getattr(self.generar, "ultimos_tokens", None)
        self.costos.registrar(time.perf_counter() - _t, tokens=_tk,
                              fuente_tokens="tokenizador" if _tk else None)
        self.trazas.append({"relato": relato[:80], "consulta": consulta[:120],
                            "recuperados": [f["id"] for f in frags],
                            "contexto": [f"{f['articulo']} {f['norma']}" for f in frags]})
        return salida


# --------------------------------------------------------------------------
# Brazo 5: el ORÁCULO. Mismo generador, contexto perfecto.
# --------------------------------------------------------------------------
class SistemaOraculo:
    """El mismo modelo del brazo 2, pero con el contexto que DEBÍA recuperarse.

    POR QUÉ HACE FALTA UN BRAZO ASÍ

    Los brazos 2, 3 y 4 mezclan dos fallos distintos en un solo número. Si el
    brazo 3 acierta el 60%, no se sabe si el 40% restante es porque el
    retrieval no trajo el artículo o porque el modelo lo tuvo delante y no supo
    usarlo. Son dos arreglos opuestos: mejorar el índice, o mejorar el prompt y
    el modelo. Sin separarlos, elegir cuál atacar es adivinar.

    Este brazo recibe exactamente los fragmentos que el `fundamento` del gold
    señala, así que su `context_recall` es 1.0 por construcción. Lo que mida de
    ahí para abajo es el techo del generador con retrieval perfecto:

        oráculo ≈ brazo 3   el retrieval ya no es el cuello de botella; lo que
                            falta está en el modelo o en el prompt.
        oráculo >> brazo 3  el modelo sí sabe usar el contexto cuando lo tiene;
                            el cuello de botella es el índice.
        oráculo bajo        ni con el contexto perfecto resuelve: el problema no
                            es de RAG en absoluto.

    Es barato: no recupera nada, solo busca en el corpus por cita.

    LO QUE NO ES. No es un sistema desplegable --- necesita la respuesta para
    construir su entrada --- y por eso no compite con los demás: es un techo de
    referencia. Reportarlo como si fuera un brazo más sería hacer trampa, y en
    la tabla va marcado como `oraculo`.
    """

    def __init__(self, generar, chunks: list[dict], casos: list[dict],
                 etiqueta: str = "5 · oráculo (contexto gold)"):
        from rag import cubre
        self._cubre = cubre
        self.generar = generar
        self.chunks = chunks
        self.etiqueta = etiqueta
        self.es_oraculo = True          # para que la tabla no lo lea como brazo
        self.trazas: list[dict] = []
        from costos import Costos
        self.costos = Costos(etiqueta)
        # El relato es la clave porque la firma del harness es
        # `sistema(relato) -> str` y no pasa el caso. Los relatos son únicos:
        # construir_eval_v2.py lo verifica por normalización.
        self._por_relato = {c["relato"]: c for c in casos}
        self.sin_gold = 0

    def contexto_gold(self, caso: dict) -> list[dict]:
        """Los fragmentos del corpus que cubren cada cita del `fundamento`.

        Es la misma definición de "cubre" que usan `context_recall_exacto` y
        `context_precision_exacta`, importada de `rag` para que no haya dos
        nociones distintas de lo mismo en el proyecto.
        """
        esperadas = schema.citas(caso.get("fundamento") or "")
        out, vistos = [], set()
        for cita in esperadas:
            for f in self.chunks:
                if f["id"] not in vistos and self._cubre(f, cita):
                    out.append(f)
                    vistos.add(f["id"])
        return out

    def __call__(self, relato: str) -> str:
        import time
        self.costos.nuevo_caso()
        caso = self._por_relato.get(relato)
        frags = self.contexto_gold(caso) if caso else []
        if not frags:
            # Sin fundamento (los casos de abstención) o sin fragmento que lo
            # cubra. Se cuenta y se deja el contexto vacío en vez de caer al
            # retrieval: si cayera, este brazo dejaría de ser un oráculo y su
            # número no significaría nada.
            self.sin_gold += 1
        usuario = (f"NORMAS APLICABLES:\n{formatear_contexto(frags)}\n\n"
                   f"{schema.PROMPT.format(relato=relato)}")
        _t = time.perf_counter()
        salida = self.generar(INSTRUCCION_RAG, usuario)
        # Tokens de un modelo LOCAL. `usage` solo existe si la llamada fue
        # a una API; `model.generate()` no devuelve nada parecido, y por eso
        # los brazos 2 y 3 salieron con `llamadas_sin_usage: 90` y
        # `tokens_por_caso: null` en m3/20261019T173316Z. El tokenizador si
        # los cuenta, asi que el generador los publica en `ultimos_tokens` y
        # se leen AQUI, justo despues de la llamada propia: entre una cosa y
        # la otra no corre nada, asi que dos brazos que comparten generador no
        # pueden mezclar su contabilidad.
        _tk = getattr(self.generar, "ultimos_tokens", None)
        self.costos.registrar(time.perf_counter() - _t, tokens=_tk,
                              fuente_tokens="tokenizador" if _tk else None)
        self.trazas.append({
            "relato": relato[:80],
            "id": caso["id"] if caso else None,
            "recuperados": [f["id"] for f in frags],
            "contexto": [f"{f['articulo']} {f['norma']}" for f in frags],
            "citas_del_gold": schema.citas(caso.get("fundamento") or "") if caso else [],
            "sin_fragmento_que_cubra": not frags,
        })
        return salida


# --------------------------------------------------------------------------
# Brazo 4: extracción de hechos
# --------------------------------------------------------------------------
PROMPT_HECHOS = """Eres un analista jurídico colombiano. Lee el relato de un ciudadano y responde
ÚNICAMENTE cuestiones DE HECHO. No decidas qué mecanismo procede: eso lo resuelve otro componente.

Devuelve SOLO este JSON, con booleanos:

{
  "privacion_libertad": ¿hay alguien detenido sin orden, no llevado ante un juez, o preso después de cumplir su condena?,
  "derecho_colectivo": ¿hay un DAÑO O AMENAZA ACTUAL a un bien colectivo —contaminación, una obra insegura, desviación de recursos públicos, un servicio que se presta de forma que daña la salubridad—? OJO, aquí está el error que más se comete: si lo que pasa es que una autoridad NO HA HECHO algo que una norma le manda hacer, va **false**, aunque lo mandado sea crear una oficina, una comisaría, un plan, un cuerpo de bomberos, una tarifa o una sala. Que el deber incumplido se refiera a un servicio público NO lo convierte en daño colectivo: las leyes que ordenan a las autoridades prestar servicios son justo lo que el art. 87 hace cumplir. La prueba: si puedes nombrar la norma y el deber concreto que no se cumplió, es INCUMPLIMIENTO, no acción popular,
  "titular_pide_lo_suyo": dentro de esa situación colectiva, ¿el solicitante reclama la afectación concreta de SU propio derecho?,
  "acto_general": ¿el solicitante ATACA una norma o acto general pidiendo que se anule o se inaplique? OJO: pedir que una norma SE CUMPLA es lo contrario de atacarla. Si el relato menciona una ley, ordenanza o acuerdo porque quiere que la autoridad lo obedezca, aquí va false,
  "dano_consumado": ¿el daño ya se produjo del todo (la persona murió, el servicio ya se prestó, la situación ya se superó)?,
  "continua_vulneracion": ¿sigue ocurriendo la acción u omisión que vulnera el derecho?,
  "incumplimiento_normativo": ¿lo que se reclama es que una autoridad cumpla una norma o acto administrativo que no ejecuta?,
  "afectacion_individual": ¿hay un DERECHO FUNDAMENTAL DEL SOLICITANTE afectado de forma concreta y actual? No basta con que exista una persona identificable pidiendo algo: si lo que pide es que una autoridad ejecute una norma o un acto administrativo, y no alega que eso le vulnere un derecho fundamental suyo, responde false,
  "otro_medio_judicial": ¿existe otro proceso judicial previsto para este asunto (laboral, civil, contencioso, familia, consumidor)?,
  "medio_eficaz": ¿ese otro medio sirve EN CONCRETO para esta persona, atendiendo su edad, salud y urgencia?,
  "perjuicio_irremediable": ¿esperar el proceso ordinario haría inútil la protección (riesgo vital, enfermedad terminal, edad avanzada sin ingresos)?,
  "sujeto_especial_proteccion": ¿es menor, adulto mayor, persona con discapacidad, mujer embarazada, desplazado o persona en debilidad manifiesta?,
  "derecho": una de estas etiquetas exactas: VOCABULARIO,
  "accionado": quién vulnera el derecho, en pocas palabras,
  "pretension": qué debería ordenarse, en una frase que empiece por un verbo
}"""


def _prompt_hechos() -> str:
    # La pregunta de triabilidad se anade desde `schema`, no se escribe
    # aqui: el prompt del agente usa LA MISMA, y dos copias divergirian.
    return schema.con_pregunta_triable(PROMPT_HECHOS).replace(
        "VOCABULARIO", ", ".join(sorted(schema.DERECHOS)))


def _json_de(texto: str) -> dict:
    m = re.search(r"\{.*\}", texto or "", re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


# Solo los hechos que el extractor puede leer del relato: el desglose
# de las ponderaciones NO se le pide (ver reglas.HECHOS_EXTRAIBLES).
CAMPOS_HECHOS = set(HECHOS_EXTRAIBLES)


DEFECTO_PRO_HOMINE = {
    "decision": "ante un hecho dudoso, no se activa causal de improcedencia",
    "donde": "sistema.extraer_hechos · todo lo que no llegue como booleano "
             "se asume False",
    "por_que": "en un triaje, el error caro no es sugerir una via de mas: es "
               "cerrarle la puerta a quien si tenia un mecanismo. El motor "
               "solo propone la via y dice que dato la cambiaria; no decide "
               "nada que no se pueda revisar.",
    "coste_simetrico": "el mismo defecto que produce CERO abstenciones "
                       "indebidas produce CERO abstenciones correctas. El "
                       "brazo que usa el motor nunca dice `ninguno`: para el, "
                       "siempre hay una via.",
    "como_NO_leer_la_cifra": "`acierto_abstencion: 0.0` en el brazo del motor "
                             "no mide que no sepa callarse --- mide que se le "
                             "pidio no callarse. Lo que si seria un hallazgo "
                             "es `abstencion_indebida > 0`, y vale 0.",
    "que_lo_cambiaria": "un umbral de confianza en la extraccion, o una "
                        "causal de improcedencia activable por defecto en los "
                        "hechos que el extractor marque como no vistos. "
                        "Ninguna de las dos esta implementada, y ninguna se "
                        "puede evaluar con n=6 abstenciones.",
}
"""Por que el brazo del motor no se abstiene nunca, dicho donde se decide.

ROADMAP3 · M3-2. `ninguno` sale con F1 0.000 y soporte 15, y 0 de 6 en
abstencion, mientras los otros tres brazos aciertan 3 de 6. Eso no es un fallo
del motor: es la consecuencia directa del defecto de arriba, y presentarlo como
fallo seria tan equivocado como presentarlo como virtud sin decir su coste.

Va como constante y no como comentario porque `metricas.abstencion` lo adjunta
al artefacto cuando la cifra sale en cero. Una decision de diseno que solo vive
en un docstring no llega a quien lee el scorecard.
"""


def extraer_hechos(generar, relato: str,
                   registro: list | None = None) -> tuple[Hechos, dict]:
    """Devuelve los hechos para el motor y los campos libres para la redacción.

    Todo lo que no llegue como booleano se asume False: ante la duda, no se
    activa una causal de improcedencia. Es la lectura pro homine del art. 1 de
    la Ley 1095 llevada al código — en la duda, que la tutela proceda.

    `registro` ES OBLIGATORIO EN LA PRÁCTICA, Y ESTE ES EL CASO QUE LO PRUEBA.

    En m1/20261016T174233Z el brazo híbrido dio 42.9% --- exactamente la base
    mayoritaria --- y publicó esa cifra como resultado. `_json_de` devolvía
    `{}`, el default pro homine ponía los doce booleanos en False, el motor no
    encontraba ninguna causal y fallaba a tutela, en 62 de 63 casos.

    POR QUÉ devolvía `{}` quedó sin establecer, y conviene no inventarlo. La
    primera explicación fue "el adaptador emite el bloque de cinco líneas en
    vez del JSON", y la sonda de 20261016T190916Z la DESMINTIÓ: el adaptador
    emite JSON bien formado, con las claves booleanas correctas, y aun así
    `_json_de` falla en 10 de 10. Queda que la salida no llega a parsear ---
    truncada antes de cerrar la llave, o malformada más adelante --- y el
    registro de abajo guarda `cierra` y `chars` precisamente para zanjarlo en
    la próxima corrida en vez de razonarlo.

    Tres capas hicieron algo defendible por separado y la composición produjo
    un número plausible. Nada en la salida lo delataba: `alucinacion_normativa`
    daba 0.0% --- cierto, emitió `art. 86 CP` 63 veces --- y
    `adherencia_estructural` daba 1.0, porque la salida la arma
    `render_salida`, no el modelo. Tres indicadores en verde sobre un brazo
    muerto.

    Pasando una lista, el fallo queda contado y quien llama puede abortar. El
    default `None` mantiene la firma vieja para quien no la use, pero no
    llamarla así en un brazo que se publica es repetir el fallo.
    """
    crudo = generar(_prompt_hechos(), relato)
    d = _json_de(crudo)
    # No basta con `d == {}`: un JSON que trae `derecho` y ningún booleano es
    # igual de inservible para el motor, y se parecia aun mas a un resultado.
    if registro is not None and not (set(d) & CAMPOS_HECHOS):
        # `crudo[:200]` fue un error: corto la salida ANTES del final, que es
        # justo donde estaba la respuesta. El artefacto de la corrida
        # 20261016T190916Z mostraba un JSON impecable en sus primeros 200
        # caracteres y no permitia decir por que no parseaba. `cierra` es el
        # dato decisivo --- si es False, la salida se trunco --- y `chars`
        # dice si choco contra `max_new`.
        texto = crudo or ""
        registro.append({"relato": relato[:70], "salida": texto[:700],
                         "chars": len(texto),
                         "empieza": texto.lstrip()[:1],
                         "cierra": texto.rstrip().endswith("}"),
                         "claves_vistas": sorted(d)})
    booleanos = {k: bool(d.get(k, False)) for k in CAMPOS_HECHOS}
    if "medio_eficaz" not in d:
        booleanos["medio_eficaz"] = True      # el default del dataclass
    libres = {
        # Ver la nota equivalente en agente.py: "ninguno" seria una
        # conclusion inventada; lo que hay es un derecho que no se pudo leer.
        "derecho": (d.get("derecho") if d.get("derecho") in schema.DERECHOS
                    else schema.DERECHO_ESCAPE),
        "accionado": (d.get("accionado") or "autoridad o particular accionado").strip(),
        "pretension": (d.get("pretension") or "amparar el derecho invocado").strip(),
    }
    # Si el extractor dijo que no hay caso que triar, viaja en `libres`: el
    # motor no puede recibirlo --- no es uno de los hechos del art. 6 --- y
    # quien renderiza la salida si tiene que verlo. Ver `schema.leer_triable`.
    libres["no_triable"], libres["motivo_no_triable"] = schema.leer_triable(d)
    return Hechos(**booleanos), libres


# --------------------------------------------------------------------------
# Brazo 4: el sistema completo
# --------------------------------------------------------------------------
# Cuándo se invoca la herramienta de términos: hace falta (a) una pista temporal
# en el relato y (b) que el caso tenga un plazo legal asociado. Fuera de eso no
# hay nada que contar y llamarla solo añadiría ruido.
PISTA_TEMPORAL = re.compile(
    r"\b(hace\s+\w+\s+(d[íi]as?|semanas?|meses?|a[ñn]os?)|\d{1,2}\s+de\s+[a-záéíóú]+|"
    r"\d{1,2}[/-]\d{1,2}[/-]\d{4})\b", re.IGNORECASE)

TERMINO_POR_DERECHO = {"peticion": "peticion_general"}
"""Mapa minimo derecho -> termino. Lo usa `tipo_de_termino` como ultimo
recurso; el tipo fino se decide leyendo el relato."""

# Pistas del relato para elegir ENTRE los plazos de peticion, que son tres y
# NO el mismo. `terminos.TERMINOS` los conoce desde el principio:
#
#     peticion_general       15 dias habiles   art. 14 Ley 1755 de 2015
#     peticion_documentos    10 dias habiles   art. 14.1 Ley 1755 de 2015
#     peticion_consulta      30 dias habiles   art. 14.2 Ley 1755 de 2015
#
# y `SistemaReglas` mapeaba todo a `peticion_general`. Consecuencia concreta:
# MT02 pide copia de un expediente docente --- 10 dias --- y MT03 eleva una
# consulta --- 30 dias ---, y los dos se calculaban con 15. Un plazo
# equivocado da una conclusion equivocada sobre si vencio, que es justo lo que
# la herramienta existe para evitar.
#
# El agente (brazo 4) nunca tuvo este problema: su `ESQUEMA_TOOL` expone los
# siete tipos y el modelo elige. Esto pone al brazo de reglas a la par.
PISTAS_TERMINO = (
    ("peticion_documentos",
     re.compile(r"\b(copia|copias|documento|documentos|expediente|"
                r"certificad\w+|historia (clinica|laboral)|"
                r"informaci[oó]n p[uú]blica)\b", re.IGNORECASE)),
    ("peticion_consulta",
     re.compile(r"\b(consulta|consult[eé]|concepto|interpretaci[oó]n|"
                r"c[oó]mo se (liquida|calcula|interpreta))\b", re.IGNORECASE)),
)


def tipo_de_termino(relato: str, libres: dict, hechos=None) -> str | None:
    """Que plazo legal aplica, leido del relato. None si no aplica ninguno.

    Se decide por PISTAS LEIBLES y en orden de especificidad: documentos y
    consulta antes que el general, porque los dos primeros son casos
    especiales del tercero y el general casaria siempre.
    """
    # Renuencia: antes de la accion de cumplimiento hay que constituirla, y
    # ese plazo tiene su propia norma (art. 8 Ley 393 de 1997). Es el caso
    # MT04, que antes no tenia forma de llegar aqui.
    if hechos is not None and getattr(hechos, "incumplimiento_normativo", False):
        return "renuencia_cumplimiento"
    if libres.get("derecho") == "peticion":
        for tipo, rx in PISTAS_TERMINO:
            if rx.search(relato or ""):
                return tipo
        return "peticion_general"
    return TERMINO_POR_DERECHO.get(libres.get("derecho"))

# Mapa cerrado derecho -> artículo constitucional que lo consagra. Es una
# correspondencia fija del ordenamiento, no una predicción: tomarla de aquí en
# vez de dejar que el modelo o la recuperación la elijan hace que la cita del
# derecho sea correcta por construcción.
ARTICULO_POR_DERECHO = {
    "salud": "art. 49 CP",
    "peticion": "art. 23 CP",
    "seguridad_social": "art. 48 CP",
    "habeas_data": "art. 15 CP",
    "debido_proceso": "art. 29 CP",
    "educacion": "art. 67 CP",
    "estabilidad_laboral_reforzada": "art. 13 CP",
    "trabajo": "art. 25 CP",
    "minimo_vital": "art. 53 CP",
    "libertad_personal": "art. 28 CP",
    "colectivos": "art. 88 CP",
    "ninguno": None,
}


class SistemaReglas:
    """Extracción con LLM, decisión con reglas, fundamento con RAG."""

    def __init__(self, generar, indice, estrategia: str = "reranked", k: int = 4,
                 transformador=None, etiqueta: str = "RAG + reglas"):
        self.generar = generar
        self.indice = indice
        self.estrategia = estrategia
        self.k = k
        self.transformador = transformador
        self.etiqueta = etiqueta
        self.trazas: list[dict] = []
        self.tool_invocada = 0
        self.tool_fallida = 0
        # Ver `extraer_hechos`: sin esto, un extractor que no emite JSON
        # produce un brazo entero de tutelas y ninguna señal.
        self.fallos_extraccion: list[dict] = []

    # -- herramienta ------------------------------------------------------
    def _termino(self, relato: str, libres: dict,
                 hechos=None) -> dict | None:
        tipo = tipo_de_termino(relato, libres, hechos)
        if not tipo or not PISTA_TEMPORAL.search(relato):
            return None
        self.tool_invocada += 1
        r = terminos.calcular_termino(tipo, relato=relato)
        if not r["calculable"]:
            self.tool_fallida += 1
        return r

    # -- fundamento -------------------------------------------------------
    def _fundamento(self, dec, libres: dict, frags: list[dict]) -> str:
        """El fundamento se compone de dos piezas DETERMINISTAS:

          - el artículo que soporta la decisión, que lo pone la regla;
          - el artículo constitucional del derecho invocado, que sale de un
            mapa cerrado.

        La primera versión tomaba el primer artículo constitucional que
        devolviera la recuperación, y en un caso de petición citó el art. 28 CP
        (libertad personal). La cita EXISTÍA —así que la métrica de alucinación
        daba 0%— pero no venía al caso. Una cita real e impertinente engaña
        igual que una inventada, y además esquiva el control.

        La recuperación no elige la cita: aporta el texto para razonar y sirve
        para comprobar que el artículo está en el corpus.
        """
        citas = []
        art_derecho = ARTICULO_POR_DERECHO.get(libres["derecho"])
        if art_derecho:
            citas.append(art_derecho)
        citas += [c.strip() for c in dec.fundamento.split(";")]

        en_corpus = {f["articulo"] for f in frags}
        self._citas_sin_respaldo = [c for c in citas
                                    if c.endswith("CP") and c not in en_corpus]
        return "; ".join(dict.fromkeys(citas))

    # -- ejecución --------------------------------------------------------
    def __call__(self, relato: str) -> str:
        hechos, libres = extraer_hechos(self.generar, relato,
                                        self.fallos_extraccion)
        dec = decidir(hechos)

        consulta = self.transformador(relato) if self.transformador else relato
        frags = self.indice.recuperar(consulta, estrategia=self.estrategia, k=self.k)

        termino = self._termino(relato, libres, hechos)
        razon = dec.razon
        if termino and termino["calculable"]:
            razon += f". {termino['resumen']}"
        elif termino:
            razon += ". No fue posible calcular el término: " + termino["motivo"]

        campos = {
            "derecho": libres["derecho"],
            "fundamento": self._fundamento(dec, libres, frags),
            "accionado": libres["accionado"],
            "mecanismo": dec.mecanismo,
            "procede": dec.procede_tutela,
            "razon": razon,
            "pretension": libres["pretension"],
        }
        if libres.get("no_triable"):
            campos = schema.abstenerse(campos, libres["motivo_no_triable"])
        salida = schema.render_salida(campos)

        self.trazas.append({
            "relato": relato[:80],
            "hechos": {k: v for k, v in hechos.__dict__.items() if v},
            "regla": dec.regla,
            # Lo que el brazo EMITIO, que con abstencion no es lo que el
            # motor dijo. Las dos cosas se guardan: una traza que dijera
            # `tutela` donde la salida dice "no determinable" enganaria a
            # quien la lee para diagnosticar, y perder lo que el motor
            # habria dicho tambien cuesta --- es el dato que permite ver
            # si la abstencion tapo una via correcta.
            "mecanismo": None if libres.get("no_triable") else dec.mecanismo,
            "mecanismo_del_motor": dec.mecanismo,
            "no_triable": bool(libres.get("no_triable")),
            "motivo_no_triable": libres.get("motivo_no_triable") or "",
            "recuperados": [f["id"] for f in frags],
            "termino": termino,
            "traza_reglas": dec.traza,
        })
        return salida


# --------------------------------------------------------------------------
# M1 híbrido: el modelo ajustado extrae HECHOS, las reglas deciden
# --------------------------------------------------------------------------
class SistemaHibrido:
    """Separa quién extrae los hechos de quién decide el mecanismo.

    POR QUÉ, CON EL DATO QUE LO MOTIVA

    Los casos adversariales son trampas de subsidiariedad, de daño consumado,
    de derechos colectivos. Son exactamente las causales tasadas del artículo
    6 del Decreto 2591, o sea un árbol de decisión escrito. Pedirle a un modelo
    que lo adivine es lo que produce el colapso a "tutela" que mide M2, y el
    brazo 4 de M3 --- que reparte el trabajo: el LLM extrae hechos, el motor
    del art. 6 decide --- es el que mejor va en ese estrato.

    QUIÉN EXTRAE NO PUEDE SER EL MODELO AJUSTADO, Y ESO SE MIDIÓ

    La primera versión de este brazo usaba el propio adaptador de M1 como
    extractor, con el argumento de que así solo cambiaba el decisor. No
    funciona, y está medido en dos corridas: en 20261016T174233Z el brazo cayó
    al 42.9% --- la base mayoritaria --- citando `art. 86 CP` una vez por caso,
    y en 20261016T190916Z la sonda dio **10 de 10 salidas que `_json_de` no
    puede parsear**. Con el adaptador apagado, 1 de 69.

    El efecto es sólido; la CAUSA no está establecida. La primera explicación
    fue "colapsa sobre el formato de cinco líneas que se le enseñó", y la
    propia sonda la desmintió: emite JSON, con las claves booleanas correctas.
    Lo que falla es que ese JSON no llega a parsear. Mientras no se mida, se
    dice así y no se adorna.

    Así que la extracción se hace con el adaptador APAGADO
    (`model.disable_adapter()`): mismos pesos base, mismo prompt, y la pregunta
    pasa a ser si el trabajo lo hace el adaptador o el motor de reglas. Ya no
    es "el mismo modelo con otro decisor" --- esa comparación no es
    ejecutable --- y la etiqueta del brazo tiene que decirlo.

    SIN RAG, a propósito. `SistemaReglas` hace lo mismo pero recupera el texto
    del artículo con un índice, y M1 no tiene índice: es el módulo de
    fine-tuning. Aquí el fundamento se construye con la correspondencia fija
    `ARTICULO_POR_DERECHO` más el que emite la regla, así que la alucinación
    normativa es cero por construcción y la comparación con el brazo 4 de M3
    queda limpia: lo que separa a los dos es el RAG, nada más.
    """

    def __init__(self, generar, etiqueta: str = "base extrae + reglas deciden"):
        self.generar = generar
        self.etiqueta = etiqueta
        self.trazas: list[dict] = []
        # Los casos en que no llegó JSON. Si esta lista crece, el brazo está
        # midiendo el default pro homine y no al extractor.
        self.fallos_extraccion: list[dict] = []
        from costos import Costos
        self.costos = Costos(etiqueta)

    def __call__(self, relato: str) -> str:
        import time
        self.costos.nuevo_caso()
        _t = time.perf_counter()
        hechos, libres = extraer_hechos(self.generar, relato,
                                        self.fallos_extraccion)
        # Tokens de un modelo LOCAL. `usage` solo existe si la llamada fue
        # a una API; `model.generate()` no devuelve nada parecido, y por eso
        # los brazos 2 y 3 salieron con `llamadas_sin_usage: 90` y
        # `tokens_por_caso: null` en m3/20261019T173316Z. El tokenizador si
        # los cuenta, asi que el generador los publica en `ultimos_tokens` y
        # se leen AQUI, justo despues de la llamada propia: entre una cosa y
        # la otra no corre nada, asi que dos brazos que comparten generador no
        # pueden mezclar su contabilidad.
        _tk = getattr(self.generar, "ultimos_tokens", None)
        self.costos.registrar(time.perf_counter() - _t, tokens=_tk,
                              fuente_tokens="tokenizador" if _tk else None)
        dec = decidir(hechos)

        # Fundamento determinista: el artículo del derecho sale de un mapa
        # cerrado y el de la decisión lo pone la regla. Ni uno ni otro los
        # elige el modelo, así que no puede inventar una norma.
        citas = []
        art = ARTICULO_POR_DERECHO.get(libres["derecho"])
        if art:
            citas.append(art)
        citas += [c.strip() for c in dec.fundamento.split(";") if c.strip()]

        campos = {
            "derecho": libres["derecho"],
            "fundamento": "; ".join(dict.fromkeys(citas)),
            "accionado": libres["accionado"],
            "mecanismo": dec.mecanismo,
            "procede": dec.procede_tutela,
            "razon": dec.razon,
            "pretension": libres["pretension"],
        }
        if libres.get("no_triable"):
            campos = schema.abstenerse(campos, libres["motivo_no_triable"])
        salida = schema.render_salida(campos)
        self.trazas.append({
            "relato": relato[:80],
            "hechos": {k: v for k, v in hechos.__dict__.items() if v},
            "regla": dec.regla,
            "mecanismo": None if libres.get("no_triable") else dec.mecanismo,
            "mecanismo_del_motor": dec.mecanismo,
            "no_triable": bool(libres.get("no_triable")),
            "motivo_no_triable": libres.get("motivo_no_triable") or "",
            "traza_reglas": dec.traza,
        })
        return salida


# --------------------------------------------------------------------------
def generador_groq(cliente, modelo: str = "openai/gpt-oss-120b", cache_path: str | None = None):
    """Devuelve una función `generar(sistema, usuario) -> str` con caché en disco.

    El caché es lo que hace reproducible el brazo 4, igual que en el juez de M2:
    sin él, dos corridas del harness darían números distintos.
    """
    import hashlib
    from pathlib import Path

    cache, ruta = {}, None
    if cache_path:
        ruta = Path(cache_path)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        if ruta.exists():
            cache = json.loads(ruta.read_text(encoding="utf-8"))

    def generar(sistema: str, usuario: str) -> str:
        k = hashlib.sha256(f"{modelo}||{sistema}||{usuario}".encode()).hexdigest()[:32]
        if k in cache:
            return cache[k]
        kw = dict(model=modelo,
                  messages=[{"role": "system", "content": sistema},
                            {"role": "user", "content": usuario}],
                  temperature=0, max_tokens=1024, seed=42, reasoning_effort="low")
        if "JSON" in sistema:          # solo la extracción de hechos pide JSON
            kw["response_format"] = {"type": "json_object"}
        r = cliente.chat.completions.create(**kw)
        txt = (r.choices[0].message.content or "").strip()
        cache[k] = txt
        if ruta:
            ruta.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
        return txt

    generar.cache = cache
    return generar
