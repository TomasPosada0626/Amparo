"""
Motor de reglas de enrutamiento constitucional.

El artículo 6 del Decreto 2591 no es un criterio difuso: son cinco causales
tasadas que se aplican en orden. El artículo 9 de la Ley 393 es una regla de
prioridad. El artículo 4 de la Ley 472 es una lista cerrada. Todo eso es un
árbol de decisión escrito, y pedirle a un modelo de lenguaje que lo *adivine*
es lo que produce el colapso a "tutela" que mide M2: sin las reglas delante,
lo único que puede hacer es seguir el prior de sus ejemplos.

Aquí el LLM extrae hechos y el motor decide. Tres consecuencias:

  - el enrutamiento es DETERMINISTA: mismo caso, misma salida, siempre;
  - es AUDITABLE: cada decisión sale con el artículo que la soporta y con la
    traza de las reglas que se evaluaron antes;
  - la alucinación normativa en el campo `fundamento` cae a cero por
    construcción, porque el fundamento lo pone la regla y no la memoria.

El orden de las reglas no es decorativo: las causales de improcedencia se
excluyen entre sí y la primera que aplica cierra el caso.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict

MECANISMOS = ("tutela", "accion_popular", "accion_cumplimiento",
              "habeas_corpus", "via_ordinaria")


# --------------------------------------------------------------------------
# Los hechos que el extractor tiene que producir
# --------------------------------------------------------------------------
@dataclass
class Hechos:
    """Lo que el LLM lee del relato. Ninguno es una conclusión jurídica:
    todos son cuestiones de hecho que se pueden leer del texto."""

    privacion_libertad: bool = False
    """¿Hay alguien privado de la libertad sin orden, sin ser llevado ante un
    juez, o recluido después de cumplir su pena?"""

    derecho_colectivo: bool = False
    """¿Lo que se pide protege un interés de una comunidad indeterminada
    (ambiente, espacio público, moralidad administrativa, patrimonio público)?"""

    titular_pide_lo_suyo: bool = False
    """Dentro de una situación colectiva, ¿el solicitante reclama la afectación
    concreta de SU propio derecho? (excepción del art. 6.3)"""

    acto_general: bool = False
    """¿Se impugna una norma o acto de carácter general, impersonal y abstracto,
    sin acto de aplicación concreto?"""

    dano_consumado: bool = False
    """¿El daño ya se produjo del todo (la persona murió, el servicio ya se
    prestó, la situación ya se superó)?"""

    continua_vulneracion: bool = False
    """¿Sigue la acción u omisión que vulnera el derecho? (excepción del 6.4)"""

    incumplimiento_normativo: bool = False
    """¿Lo que se reclama es que una autoridad cumpla una norma o acto
    administrativo que no está ejecutando?"""

    afectacion_individual: bool = False
    """¿Hay una persona identificable cuyo derecho fundamental está afectado
    de forma concreta y actual?"""

    otro_medio_judicial: bool = False
    """¿Existe otro proceso judicial previsto para este asunto (laboral,
    civil, contencioso, familia, consumidor)?"""

    medio_eficaz: bool = True
    """¿Ese otro medio es eficaz EN CONCRETO para esta persona? El art. 6.1
    ordena apreciarlo atendiendo sus circunstancias, no en abstracto."""

    perjuicio_irremediable: bool = False
    """¿Hay urgencia tal que esperar el proceso ordinario haría inútil la
    protección (riesgo vital, edad avanzada sin ingresos, enfermedad terminal)?"""

    sujeto_especial_proteccion: bool = False
    """¿Es menor, adulto mayor, persona con discapacidad, mujer embarazada,
    desplazado o persona en debilidad manifiesta?"""

    # ----------------------------------------------------------------------
    # Desglose OPCIONAL de los dos hechos que no se leen: se ponderan.
    #
    # `perjuicio_irremediable` y `medio_eficaz` eran booleanos que el
    # codificador AFIRMABA. Eso es la debilidad real de la verificación por
    # reglas: quien codifica conoce la etiqueta, así que en esos dos campos la
    # codificación puede elegirse hacia atrás y el motor la confirma igual. El
    # análisis de sensibilidad lo midió: 19 de 63 casos del eval set pivotan
    # ahí.
    #
    # Estos campos descomponen cada juicio en elementos que SÍ se leen del
    # relato. Cuando se dan todos, el motor DERIVA el booleano y EXIGE que
    # coincida con el afirmado; si no coincide, falla. El juicio deja de ser
    # una aserción y pasa a ser una derivación comprobable contra el texto.
    #
    # Son opcionales (`None` = no desglosado) para no romper los 95 casos del
    # dataset que ya están verificados con el booleano solo.
    # ----------------------------------------------------------------------

    pi_inminencia: bool | None = None
    """¿El daño está por ocurrir, de forma concreta y próxima? No basta que
    sea posible o hipotético."""

    pi_gravedad: bool | None = None
    """¿El bien en riesgo es de alta importancia para la persona (vida,
    integridad, salud, subsistencia)?"""

    pi_urgencia: bool | None = None
    """¿Exige medidas inmediatas para conjurarlo?"""

    pi_impostergabilidad: bool | None = None
    """¿La protección perdería su eficacia si esperara al proceso ordinario?"""

    me_idoneo: bool | None = None
    """IDONEIDAD: ¿el otro medio sirve para lo que se pide, en abstracto?
    Un ejecutivo sirve para cobrar una deuda; no sirve para que entreguen un
    medicamento."""

    me_oportuno: bool | None = None
    """EFICACIA TEMPORAL: ¿alcanza en el tiempo del que esta persona dispone?
    Es la pregunta del art. 6.1 leída en concreto: un proceso de tres años no
    es oportuno para quien tiene una expectativa de vida de ocho meses."""

    me_accesible: bool | None = None
    """¿Esta persona puede efectivamente usarlo, atendidas sus condiciones
    (recursos, estado de salud, representación)?"""

    def __post_init__(self):
        campos = asdict(self)
        opcionales = {k for k in campos if k.startswith(("pi_", "me_"))}
        for k, v in campos.items():
            if k in opcionales:
                if v is not None and not isinstance(v, bool):
                    raise TypeError(
                        f"el hecho '{k}' debe ser booleano o None, llegó "
                        f"{type(v).__name__}")
            elif not isinstance(v, bool):
                raise TypeError(
                    f"el hecho '{k}' debe ser booleano, llegó {type(v).__name__}")

        # El test del perjuicio irremediable es CONJUNTIVO: los cuatro
        # elementos tienen que concurrir. Si falta uno, no hay perjuicio
        # irremediable, por grave que sea el resto.
        pi = [self.pi_inminencia, self.pi_gravedad, self.pi_urgencia,
              self.pi_impostergabilidad]
        if all(x is not None for x in pi):
            derivado = all(pi)
            if derivado != self.perjuicio_irremediable:
                falta = [n for n, x in zip(
                    ("inminencia", "gravedad", "urgencia", "impostergabilidad"),
                    pi) if not x]
                raise ValueError(
                    f"`perjuicio_irremediable={self.perjuicio_irremediable}` no "
                    f"se sigue del desglose: el test es conjuntivo y "
                    f"{'falta ' + ', '.join(falta) if falta else 'concurren los cuatro'}. "
                    f"Derivado: {derivado}.")
        elif any(x is not None for x in pi):
            raise ValueError(
                "el desglose del perjuicio irremediable va completo o no va: "
                "faltan elementos de pi_inminencia/pi_gravedad/pi_urgencia/"
                "pi_impostergabilidad")

        # La eficacia también es conjuntiva: un medio idóneo que no alcanza en
        # el tiempo disponible no es eficaz EN CONCRETO, que es lo que el
        # art. 6.1 manda apreciar.
        me = [self.me_idoneo, self.me_oportuno, self.me_accesible]
        if all(x is not None for x in me):
            derivado = all(me)
            if derivado != self.medio_eficaz:
                falta = [n for n, x in zip(
                    ("idoneo", "oportuno", "accesible"), me) if not x]
                raise ValueError(
                    f"`medio_eficaz={self.medio_eficaz}` no se sigue del "
                    f"desglose: {'no es ' + ', '.join(falta) if falta else 'concurren los tres'}. "
                    f"Derivado: {derivado}.")
        elif any(x is not None for x in me):
            raise ValueError(
                "el desglose de la eficacia va completo o no va: faltan "
                "elementos de me_idoneo/me_oportuno/me_accesible")


@dataclass
class Decision:
    mecanismo: str
    procede_tutela: bool
    fundamento: str
    razon: str
    regla: str
    traza: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------
# Las reglas, en el orden en que el ordenamiento las aplica
# --------------------------------------------------------------------------
def decidir(h: Hechos) -> Decision:
    traza: list[str] = []

    def nota(regla: str, aplica: bool, porque: str) -> None:
        traza.append(f"[{'SÍ' if aplica else 'no'}] {regla}: {porque}")

    # --- 1. Habeas corpus (art. 6.2) -------------------------------------
    # Categórica: si el supuesto es de libertad personal, la tutela está
    # excluida sin más análisis.
    if h.privacion_libertad:
        nota("art. 6.2 D.2591", True, "hay privación de la libertad invocable por habeas corpus")
        return Decision(
            "habeas_corpus", False,
            "art. 28 CP; art. 30 CP; Ley 1095 de 2006; art. 6.2 Decreto 2591 de 1991",
            "se alega privación ilegal o prolongación ilícita de la libertad, supuesto "
            "para el cual la Constitución previó el habeas corpus como mecanismo específico",
            "habeas_corpus", traza)
    nota("art. 6.2 D.2591", False, "no hay privación de la libertad")

    # --- 2. Derechos colectivos (art. 6.3) -------------------------------
    # Con su excepción: el titular puede tutelar lo suyo dentro de una
    # situación colectiva si se trata de impedir un perjuicio irremediable.
    if h.derecho_colectivo:
        excepcion = h.titular_pide_lo_suyo and h.perjuicio_irremediable
        if not excepcion:
            nota("art. 6.3 D.2591", True, "se protege un interés colectivo y no opera la excepción")
            return Decision(
                "accion_popular", False,
                "art. 88 CP; Ley 472 de 1998; art. 6.3 Decreto 2591 de 1991",
                "lo que se busca proteger son derechos e intereses colectivos del "
                "artículo 4 de la Ley 472, excluidos del ámbito de la tutela",
                "derechos_colectivos", traza)
        nota("art. 6.3 D.2591", False,
             "hay interés colectivo pero el titular pide lo suyo ante un perjuicio irremediable (excepción)")
    else:
        nota("art. 6.3 D.2591", False, "no se protegen derechos colectivos")

    # --- 3. Actos generales (art. 6.5) -----------------------------------
    if h.acto_general and not h.afectacion_individual:
        nota("art. 6.5 D.2591", True, "se impugna un acto general, impersonal y abstracto")
        return Decision(
            "via_ordinaria", False,
            "art. 6.5 Decreto 2591 de 1991; Ley 1437 de 2011",
            "se impugna un acto de carácter general, impersonal y abstracto, para el "
            "cual existen los medios de control ante la jurisdicción contenciosa",
            "acto_general", traza)
    nota("art. 6.5 D.2591", False, "no se impugna un acto general sin aplicación concreta")

    # --- 4. Daño consumado (art. 6.4) ------------------------------------
    if h.dano_consumado and not h.continua_vulneracion:
        nota("art. 6.4 D.2591", True, "el daño está consumado y la vulneración no continúa")
        return Decision(
            "via_ordinaria", False,
            "art. 6.4 Decreto 2591 de 1991",
            "el daño está consumado y no subsiste la acción u omisión violatoria, de modo "
            "que no hay derecho fundamental actual que amparar; la tutela no es "
            "indemnizatoria ni declarativa de responsabilidad",
            "dano_consumado", traza)
    nota("art. 6.4 D.2591", False,
         "no hay daño consumado, o la vulneración continúa (excepción del 6.4)")

    # --- 5. Cumplimiento frente a tutela (art. 9 Ley 393) ----------------
    # El cumplimiento es SUBSIDIARIO: solo cabe si el derecho NO puede
    # garantizarse por tutela. Por eso se exige que no haya afectación
    # individual concreta.
    if h.incumplimiento_normativo and not h.afectacion_individual:
        nota("art. 9 L.393", True,
             "se reclama el acatamiento general de una norma sin afectación individual concreta")
        return Decision(
            "accion_cumplimiento", False,
            "art. 87 CP; Ley 393 de 1997",
            "lo pretendido es el cumplimiento de una norma o acto administrativo vigente, "
            "sin que se alegue la vulneración concreta de un derecho fundamental individual",
            "incumplimiento_normativo", traza)
    if h.incumplimiento_normativo:
        nota("art. 9 L.393", False,
             "hay incumplimiento normativo PERO afecta a una persona concreta: el art. 9 "
             "hace improcedente el cumplimiento y reencauza a tutela")
    else:
        nota("art. 9 L.393", False, "no se reclama el cumplimiento de una norma")

    # --- 6. Subsidiariedad (art. 6.1) ------------------------------------
    # La eficacia del otro medio se aprecia EN CONCRETO, no en abstracto.
    if h.otro_medio_judicial and h.medio_eficaz and not h.perjuicio_irremediable:
        nota("art. 6.1 D.2591", True,
             "existe otro medio judicial, es eficaz en concreto y no hay perjuicio irremediable")
        return Decision(
            "via_ordinaria", False,
            "art. 6.1 Decreto 2591 de 1991",
            "existe otro medio de defensa judicial idóneo y eficaz en concreto, y no se "
            "acredita un perjuicio irremediable que habilite la tutela",
            "subsidiariedad", traza)
    if h.otro_medio_judicial:
        motivo = ("el otro medio no es eficaz en concreto" if not h.medio_eficaz
                  else "concurre un perjuicio irremediable")
        nota("art. 6.1 D.2591", False, f"existe otro medio PERO {motivo}")
    else:
        nota("art. 6.1 D.2591", False, "no existe otro medio de defensa judicial")

    # --- 7. Procede la tutela --------------------------------------------
    transitorio = h.otro_medio_judicial and h.perjuicio_irremediable
    razon = ("ninguna causal de improcedencia del artículo 6 resulta aplicable")
    if transitorio:
        razon = ("aunque existe otro medio de defensa judicial, el perjuicio irremediable "
                 "habilita la tutela como mecanismo transitorio")
    elif h.sujeto_especial_proteccion:
        razon += ", y se trata de un sujeto de especial protección constitucional"

    nota("procedencia", True, "ninguna causal cierra el paso")
    return Decision(
        "tutela", True,
        "art. 86 CP; art. 8 Decreto 2591 de 1991" if transitorio else "art. 86 CP",
        razon,
        "tutela_transitoria" if transitorio else "tutela", traza)


# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# Que tan solida es una codificacion de hechos
# --------------------------------------------------------------------------
HECHOS_DE_JUICIO = ("medio_eficaz", "perjuicio_irremediable",
                    "titular_pide_lo_suyo", "continua_vulneracion")
"""Los hechos que NO se leen del relato: se ponderan.

El art. 6.1 lo dice expresamente --- la eficacia del otro medio se aprecia
"atendiendo las circunstancias en que se encuentre el solicitante" --- y el
6.4 depende de si la vulneracion continua, que tambien es una valoracion. Los
demas hechos o estan en el texto o no estan: hay o no hay alguien privado de
la libertad, se impugna o no un acto general.
"""


SUBHECHOS = {
    "perjuicio_irremediable": ("pi_inminencia", "pi_gravedad", "pi_urgencia",
                               "pi_impostergabilidad"),
    "medio_eficaz": ("me_idoneo", "me_oportuno", "me_accesible"),
}
"""Que elementos leibles desglosan cada juicio. Ver `Hechos`."""

CAMPOS_DESGLOSE = frozenset(s for subs in SUBHECHOS.values() for s in subs)

HECHOS_EXTRAIBLES = tuple(k for k in Hechos().__dataclass_fields__
                          if k not in CAMPOS_DESGLOSE)
"""Los hechos que un EXTRACTOR puede producir leyendo el relato.

Excluye el desglose de las dos ponderaciones. Esa distincion no es cosmetica:
`agente.py` y `sistema.py` armaban su diccionario con
`set(Hechos().__dataclass_fields__)` y `bool(d.get(k, False))`, asi que al
anadir los campos opcionales del desglose TODOS llegaban en False --- un
desglose completo y contradictorio con `medio_eficaz=True` --- y el
`__post_init__` levantaba ValueError en cada caso. Habria tumbado el brazo 4
entero, los 61 casos, en la primera corrida.

El desglose es para datos codificados a mano, donde alguien leyo el relato y
decidio cada elemento. Pedirselo a un extractor seria pedirle justo la
ponderacion que el desglose intenta quitar de en medio.
"""


def pivota_en_juicio(h: Hechos) -> list[str]:
    """Hechos de ponderacion AFIRMADOS de los que depende el mecanismo.

    Un campo cuenta solo si ademas de ser critico esta afirmado a pelo, sin
    desglose. Si lleva desglose, el juicio ya no es discrecional: esta derivado
    de elementos que se leen del relato, y lo reporta `estrato_verificacion`
    como `derivado`.
    """
    est, campos = estrato_verificacion(h)
    return campos if est == "juicio" else []


def estrato_verificacion(h: Hechos) -> tuple[str, list[str]]:
    """Que tan solida es la verificacion por reglas de ESTE caso.

    Que el motor derive la etiqueta prueba que es EXPRESABLE en el arbol del
    art. 6 --- es lo que encontro el error de A09 --- no que sea correcta:
    quien codifica los hechos suele conocer la etiqueta, y donde un hecho
    admite dos valores defendibles la codificacion puede elegirse hacia atras.

    Devuelve uno de tres, y los campos implicados:

      plano     el mecanismo lo fuerzan hechos que se leen del relato. La
                verificacion es solida.
      derivado  el mecanismo depende de una ponderacion, pero esa ponderacion
                esta desglosada en elementos leibles y el motor la DERIVA
                (test conjuntivo). La discrecion se movio del booleano a
                hechos comprobables contra el texto.
      juicio    el mecanismo depende de una ponderacion AFIRMADA sin desglose.
                Aqui la verificacion vale menos y hace falta una lectura
                independiente.
    """
    base = decidir(h).mecanismo
    completo = asdict(h)
    libres: list[str] = []
    derivados: list[str] = []

    for campo in HECHOS_DE_JUICIO:
        subs = SUBHECHOS.get(campo, ())
        desglosado = bool(subs) and all(completo[s] is not None for s in subs)

        if not desglosado:
            # Afirmado a pelo: se voltea y se mira si el mecanismo se mueve.
            alt = dict(completo)
            alt[campo] = not completo[campo]
            if decidir(Hechos(**alt)).mecanismo != base:
                libres.append(campo)
            continue

        # Desglosado: no se puede voltear la conclusion sin contradecir las
        # premisas. Se voltea cada ELEMENTO, se re-deriva el conjuntivo y se
        # mira si el mecanismo se mueve. Si se mueve, el mecanismo depende del
        # desglose, que es justo lo que se queria.
        for s in subs:
            alt = dict(completo)
            alt[s] = not completo[s]
            alt[campo] = all(alt[x] for x in subs)
            if decidir(Hechos(**alt)).mecanismo != base:
                derivados.append(campo)
                break

    if libres:
        return "juicio", libres
    if derivados:
        return "derivado", derivados
    return "plano", []


def explicar(d: Decision) -> str:
    """La traza completa, para poder defender la decisión ante alguien."""
    out = [f"MECANISMO: {d.mecanismo}   (regla: {d.regla})",
           f"FUNDAMENTO: {d.fundamento}", "", "Reglas evaluadas, en orden:"]
    out += [f"  {t}" for t in d.traza]
    return "\n".join(out)
