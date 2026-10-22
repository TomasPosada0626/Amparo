"""
Tool use real: el modelo PROPONE la herramienta, nosotros la ejecutamos.

POR QUE EXISTE ESTE MODULO
    La version anterior tenia la herramienta de terminos (`terminos.py`) con su
    esquema de function calling escrito... y nunca lo usaba. `SistemaReglas`
    invocaba `calcular_termino()` detras de una expresion regular:

        if tipo and PISTA_TEMPORAL.search(relato):   # <- esto decide un regex
            terminos.calcular_termino(...)

    Eso es una llamada a funcion, no tool use. La sesion 10 del curso pide el
    bucle `propone -> ejecutamos -> observa -> responde`, con el JSON de los
    argumentos validado. Aqui esta.

COMO ESTA REPARTIDO EL TRABAJO
    Tres fases, cada una con un solo oficio:

      1. AGENTE        el modelo decide QUE herramientas llamar y con que
                       argumentos. Nosotros las ejecutamos y le devolvemos la
                       observacion. Maximo 5 pasos.
      2. EXTRACCION    con las observaciones en el contexto, el modelo responde
                       las cuestiones DE HECHO en JSON. No decide nada juridico.
      3. DETERMINISTA  el motor de reglas calcula el mecanismo y se renderiza.

    El modelo NUNCA elige el mecanismo. Eso lo hace el art. 6 del Decreto 2591
    aplicado por `reglas.decidir()`, y es la razon de que la alucinacion en el
    campo `fundamento` sea cero por construccion. Es la misma separacion que
    hace falta en cualquier agente que tome decisiones con consecuencias: que
    el modelo elija los medios, no el veredicto.

LAS DOS HERRAMIENTAS
    calcular_termino   la herramienta externa (criterio 3). Cuenta dias habiles
                       con los festivos colombianos. Un LLM no sabe que el 6 de
                       enero se corre al lunes por la Ley 51 de 1983.
    buscar_normas      el retrieval como herramienta. Devuelve articulos reales
                       del corpus, con su norma y su vigencia.

CRITERIO DE INVOCACION
    Va en el prompt del sistema, no solo en esta documentacion, porque si no
    esta en el prompt no es un criterio: es un deseo. Ver INSTRUCCION_AGENTE.

LAS CINCO FALLAS QUE SE MANEJAN
    Cada una devuelve una OBSERVACION al modelo en vez de tumbar la corrida, y
    cada una lleva su contador para que el scorecard pueda mostrar que paso:

      1. argumentos que no son JSON valido
      2. herramienta que no existe
      3. herramienta que lanza una excepcion
      4. la misma herramienta con los mismos argumentos, repetida
      5. pasos agotados sin que el modelo concluya

    La numero 5 es la que obliga al cierre determinista: un agente que se queda
    pidiendo herramientas no puede dejar al usuario sin respuesta.
"""
from __future__ import annotations
import json
import re
import time

import schema
import terminos
from reglas import HECHOS_EXTRAIBLES, Hechos, decidir

MAX_PASOS = 5
"""El techo de pasos PRODUCTIVOS de herramienta. NO SE SUBE, Y ESTA MEDIDO.

Se subio a 8 una vez, para descensurar la media de pasos ---52% de los casos
tocaban el techo, asi que `pasos/caso` solo se podia citar como cota
inferior---. Se revirtio por dos razones, y la segunda es la que manda:

  1. `veredicto_presupuesto()` lleva escrito, con umbral fijado de antemano,
     que «subir max_pasos solo mueve el techo, y el problema puede estar en
     que el agente no sabe cuando ha recuperado suficiente».
  2. Subirlo cambia los resultados del brazo que se reporta. Hacerlo despues
     de ver los numeros es un cambio del experimento, no una mejora del
     sistema, aunque la intencion sea medir mejor.

El techo se ataca por donde el veredicto dice: con un criterio de parada
---ver `CRITERIO_DE_PARADA` en `INSTRUCCION_AGENTE`---. Si la tasa de casos
que lo agotan baja, la media se descensura sola y sin tocar el parametro. Si
no baja, el hallazgo es que el agente no converge, que es un resultado y no
un ajuste pendiente.
"""
MODELO = "openai/gpt-oss-120b"

# --------------------------------------------------------------------------
# Esquemas de las herramientas
# --------------------------------------------------------------------------
ESQUEMA_BUSCAR = {
    "type": "function",
    "function": {
        "name": "buscar_normas",
        "description": (
            "Busca articulos de la ley colombiana en el corpus del sistema "
            "(Constitucion, Decreto 2591 de 1991, Ley 393 de 1997, Ley 472 de 1998, "
            "Ley 1095 de 2006, Ley 1751 de 2015, Ley 1755 de 2015 y otras). "
            "Devuelve el texto del articulo con su norma y su vigencia. Usala cuando "
            "necesites el texto de una norma para decidir si un hecho esta probado, "
            "no para adivinar que mecanismo procede."),
        "parameters": {
            "type": "object",
            "properties": {
                "consulta": {
                    "type": "string",
                    "description": "que se busca, en lenguaje juridico colombiano"},
                "k": {
                    "type": "integer",
                    "description": "cuantos articulos traer (1 a 8); por defecto 4"},
            },
            "required": ["consulta"],
        },
    },
}

HERRAMIENTAS = [terminos.ESQUEMA_TOOL, ESQUEMA_BUSCAR]

INSTRUCCION_AGENTE = """Eres un analista juridico colombiano que prepara el triaje de un caso.
Tu trabajo en esta fase es REUNIR INFORMACION, no decidir. Otro componente decide el
mecanismo aplicando el articulo 6 del Decreto 2591 de 1991; tu no lo elijes.

Tienes dos herramientas. CRITERIO DE INVOCACION:

- `buscar_normas`: usala cuando necesites el texto de un articulo para saber si un hecho
  del relato encaja en un supuesto legal (por ejemplo, si lo que se reclama es un derecho
  colectivo, o si hay privacion de la libertad). Empieza por aqui: es la informacion que
  mas cambia el analisis.
- `calcular_termino`: dos condiciones, y si se cumplen las dos NO ES OPCIONAL llamarla.
  (a) el relato dice CUANDO paso algo, y (b) hay un plazo legal en juego (derecho de
  peticion, fallo de tutela, impugnacion, cumplimiento).

  Sobre (a): «hace cuatro dias», «hace dos meses», «hace seis dias habiles» cuentan
  IGUAL que «el 3 de marzo de 2026». Una duracion relativa es una fecha de inicio y la
  herramienta la resuelve; no hace falta que el relato traiga una fecha de calendario.

  Sobre (b): el plazo sigue en juego AUNQUE LA ENTIDAD YA HAYA RESPONDIDO. Si respondio
  dentro del termino o fuera de el es precisamente lo que la herramienta decide, y es un
  hecho del caso que el relato no afirma.

  Por que no es opcional: «el plazo vencio» o «respondieron a tiempo» es un HECHO que
  ningun relato enuncia y que nadie mas en el sistema puede establecer. Si no la llamas,
  ese hecho se pierde y el componente que decide trabaja sin el.

  Si falta cualquiera de las dos condiciones, no la llames: no hay nada que contar.
- Si el relato no describe un problema juridico, no fuerces ninguna herramienta.

No llames la misma herramienta con los mismos argumentos dos veces: si ya tienes la
observacion, usala.

CUANDO PARAR. Esto no es una cuestion de criterio: el componente que decide necesita
exactamente estos cuatro hechos, y son los unicos para los que hace falta leer una
norma:

  1. hay alguien privado de la libertad?
  2. lo que se reclama es un interes colectivo de una comunidad indeterminada?
  3. se impugna una norma o acto general, sin acto concreto de aplicacion?
  4. hay un incumplimiento de un mandato normativo claro?

Los demas hechos ---si el dano ya se consumo, si sigue la vulneracion, si hay otro
medio judicial, si el sujeto es de especial proteccion, si el perjuicio es
irremediable--- se leen DEL RELATO y ninguna norma los va a contestar. Buscar mas
articulos no los hace aparecer.

Asi que: en cuanto puedas responder esos cuatro con lo que ya tienes, PARA y responde.
Una busqueda mas que no cambie ninguna de las cuatro respuestas no aporta nada ---y
medido, 158 de las busquedas de la ultima corrida fueron exactamente eso---.

Cuando pares, responde en texto breve resumiendo los hechos relevantes que
encontraste. Maximo %d pasos de herramienta.""" % MAX_PASOS


# POR QUE ESTE PROMPT DICE "OJO" DOS VECES
#
# Medido en m3/20261018T080807Z, sobre los 8 casos de `accion_cumplimiento`
# que el brazo del agente fallaba por completo (F1 0.000):
#
#     derecho_colectivo    True en 8 de 8
#     acto_general         True en 6 de 8
#
# El motor no era el problema: con los hechos del eval set emite la via
# correcta en 8 de 8. El extractor confundia dos pares de cosas:
#
#   incumplir un deber general  !=  danar un derecho colectivo
#     El art. 87 CP pide que se CUMPLA una norma; el art. 88 protege un bien
#     juridico colectivo del catalogo del art. 4 de la Ley 472. Que el
#     incumplimiento afecte a todo un municipio no lo convierte en colectivo:
#     la lista del art. 4 es cerrada, no un ejemplo de "cosas que afectan a
#     muchos".
#
#   mencionar una norma  !=  atacar una norma
#     Pedir que una ordenanza se cumpla es lo contrario de pedir que se
#     anule. `acto_general` es para lo segundo.
#
# Las dos confusiones son razonables --- por eso un modelo las comete --- y
# las dos mandaban el caso a `accion_popular` o `via_ordinaria` antes de que
# el motor llegara a mirar el incumplimiento.

PROMPT_HECHOS_AGENTE = """Con base en el relato y en las observaciones de las herramientas, responde
UNICAMENTE cuestiones DE HECHO. No decidas que mecanismo procede.

Devuelve SOLO este JSON, con booleanos:

{
  "privacion_libertad": ¿hay alguien detenido sin orden judicial, no llevado ante un juez en el termino, o recluido despues de cumplir su condena?,
  "derecho_colectivo": ¿hay un DANO O AMENAZA ACTUAL a un bien colectivo --- contaminacion, una obra insegura, desviacion de recursos publicos, un servicio que se presta de forma que dana la salubridad? OJO, aqui esta el error que mas se comete: si lo que pasa es que una autoridad NO HA HECHO algo que una norma le manda hacer, va **false**, aunque lo mandado sea crear una oficina, una comisaria, un plan, un cuerpo de bomberos, una tarifa o una sala. Que el deber incumplido se refiera a un servicio publico NO lo convierte en dano colectivo: las leyes que ordenan a las autoridades prestar servicios son justo lo que el art. 87 hace cumplir. La prueba: si puedes nombrar la norma y el deber concreto que no se cumplio, es INCUMPLIMIENTO, no accion popular,
  "titular_pide_lo_suyo": dentro de esa situacion colectiva, ¿el solicitante reclama la afectacion concreta de SU propio derecho?,
  "acto_general": ¿el solicitante ATACA una norma o acto general pidiendo que se anule o se inaplique? OJO: pedir que una norma SE CUMPLA es lo contrario de atacarla. Si el relato menciona una ley, ordenanza o acuerdo porque quiere que la autoridad lo obedezca, aqui va false,
  "dano_consumado": ¿el dano ya se produjo del todo (la persona murio, el servicio ya se presto, la situacion ya se supero)?,
  "continua_vulneracion": ¿sigue ocurriendo la accion u omision que vulnera el derecho?,
  "incumplimiento_normativo": ¿lo que se reclama es que una autoridad cumpla una norma o acto administrativo que no ejecuta?,
  "afectacion_individual": ¿hay un DERECHO FUNDAMENTAL DEL SOLICITANTE afectado de forma concreta y actual? No basta con que exista una persona identificable pidiendo algo: si lo que pide es que una autoridad ejecute una norma o un acto administrativo, y no alega que eso le vulnere un derecho fundamental suyo, responde false,
  "otro_medio_judicial": ¿existe otro proceso judicial previsto para este asunto (laboral, civil, contencioso, familia, consumidor)?,
  "medio_eficaz": ¿ese otro medio sirve EN CONCRETO para esta persona, atendiendo su edad, salud y urgencia?,
  "perjuicio_irremediable": ¿esperar el proceso ordinario haria inutil la proteccion (riesgo vital, enfermedad terminal, edad avanzada sin ingresos)?,
  "sujeto_especial_proteccion": ¿es menor, adulto mayor, persona con discapacidad, mujer embarazada, desplazado o persona en debilidad manifiesta?,
  "derecho": una de estas etiquetas exactas: VOCABULARIO,
  "accionado": quien vulnera el derecho, en pocas palabras,
  "pretension": que deberia ordenarse, en una frase que empiece por un verbo
}"""

# Solo los hechos que el extractor puede leer del relato: el desglose
# de las ponderaciones NO se le pide (ver reglas.HECHOS_EXTRAIBLES).
CAMPOS_HECHOS = set(HECHOS_EXTRAIBLES)


def _json_de(texto: str) -> dict:
    m = re.search(r"\{.*\}", texto or "", re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


# --------------------------------------------------------------------------
class Agente:
    """Bucle de function calling sobre Groq, con cierre determinista.

    `sistema(relato) -> str` para que el harness de M2 lo mida sin cambios.
    """

    def __init__(self, cliente, indice, modelo: str = MODELO,
                 estrategia: str = "reranked", k: int = 4,
                 transformador=None, max_pasos: int = MAX_PASOS,
                 cache_path: str | None = None, etiqueta: str = "agente + reglas",
                 verbose: bool = False):
        self.cliente = cliente
        self.indice = indice
        self.modelo = modelo
        self.estrategia = estrategia
        self.k = k
        self.transformador = transformador
        self.max_pasos = max_pasos
        self.etiqueta = etiqueta
        self.verbose = verbose

        self.trazas: list[dict] = []
        self.fallos_extraccion: list[dict] = []
        self.contadores = {
            "tool_invocada": 0,
            "tool_buscar": 0,
            "tool_termino": 0,
            "argumentos_no_json": 0,
            "herramienta_inexistente": 0,
            "herramienta_con_error": 0,
            "llamada_repetida": 0,
            "pasos_agotados": 0,
            "casos_sin_ninguna_tool": 0,
            "hechos_no_parseados": 0,
            # Una busqueda cuyos fragmentos ya estaban todos en las
            # observaciones anteriores: informacion cero. Se mide porque es la
            # mitad de la explicacion de por que el 62% de los casos agotaba
            # el presupuesto.
            "busqueda_sin_novedad": 0,
            # Iteraciones que no cobraron paso, por repeticion o por no
            # aportar fragmentos nuevos. `pasos_cobrados` + esto = iteraciones.
            "paso_no_cobrado": 0,
            # El extractor dijo que no hay caso que triar y el brazo se
            # abstuvo en vez de proponer una via. Se cuenta aparte porque es
            # la unica salida del brazo que NO sale del motor, y porque el
            # numero que la puede falsar --- `abstencion_indebida` sobre los
            # 103 casos con respuesta correcta --- se lee contra este.
            "abstencion_por_no_triable": 0,
            # El modelo daba vueltas sin aportar y lo paro el techo de
            # iteraciones, no el presupuesto. Es otra forma de no converger.
            "techo_iteraciones": 0,
        }
        from costos import Costos
        self.costos = Costos(etiqueta)
        self._cache: dict[str, str] = {}
        self._ruta_cache = None
        if cache_path:
            from pathlib import Path
            self._ruta_cache = Path(cache_path)
            self._ruta_cache.parent.mkdir(parents=True, exist_ok=True)
            if self._ruta_cache.exists():
                self._cache = json.loads(self._ruta_cache.read_text(encoding="utf-8"))

    # -- cache ----------------------------------------------------------
    def _clave(self, *partes: str) -> str:
        import hashlib
        crudo = "||".join([self.modelo, *partes])
        return hashlib.sha256(crudo.encode("utf-8")).hexdigest()[:32]

    def guardar_cache(self) -> None:
        if self._ruta_cache is not None:
            self._ruta_cache.write_text(
                json.dumps(self._cache, ensure_ascii=False, indent=1),
                encoding="utf-8", newline="\n")

    # -- ejecucion de herramientas --------------------------------------
    def _buscar_normas(self, consulta: str,
                       k: int | None = None) -> tuple[str, list[str]]:
        """Devuelve (observacion, ids de los fragmentos recuperados).

        Los ids se devuelven y se guardan en la traza. La version anterior solo
        devolvia el texto, asi que para saber QUE habia leido el agente habia
        que rederivar la recuperacion desde los argumentos de la llamada. Dos
        problemas: era fragil --- cualquier cambio de estrategia o de `k` daba
        un contexto distinto del que el agente leyo de verdad --- y el notebook
        de M3 lee `t["recuperados"]` de las trazas, que en el agente no
        existia. Eso es un KeyError en la celda de RAGAS, DESPUES de que los
        cuatro brazos hayan corrido.
        """
        kk = max(1, min(int(k or self.k), 8))
        frags = self.indice.recuperar(consulta, estrategia=self.estrategia, k=kk)
        if not frags:
            return "Sin resultados en el corpus para esa consulta.", []
        obs = "\n\n".join(
            f"[{f['articulo']} · {f['norma']} · vigencia: {f.get('vigencia','?')}]\n{f['texto'][:700]}"
            for f in frags)
        return obs, [f["id"] for f in frags]

    def _ejecutar(self, nombre: str, crudo: str) -> tuple[str, dict]:
        """Ejecuta una herramienta. Devuelve (observacion, registro).

        Nunca lanza: toda falla se convierte en una observacion que el modelo
        puede leer y corregir en el paso siguiente.
        """
        reg = {"herramienta": nombre, "argumentos_crudos": crudo[:300]}

        try:
            args = json.loads(crudo) if crudo else {}
            if not isinstance(args, dict):
                raise ValueError("los argumentos no son un objeto")
        except (json.JSONDecodeError, ValueError) as ex:
            self.contadores["argumentos_no_json"] += 1
            reg["falla"] = f"argumentos_no_json: {ex}"
            return (f"ERROR: los argumentos no son JSON valido ({ex}). "
                    f"Vuelve a llamar la herramienta con un objeto JSON correcto."), reg

        reg["argumentos"] = args

        if nombre not in {"calcular_termino", "buscar_normas"}:
            self.contadores["herramienta_inexistente"] += 1
            reg["falla"] = "herramienta_inexistente"
            return (f"ERROR: la herramienta '{nombre}' no existe. Disponibles: "
                    f"buscar_normas, calcular_termino."), reg

        try:
            if nombre == "buscar_normas":
                obs, ids = self._buscar_normas(args.get("consulta", ""),
                                               args.get("k"))
                reg["recuperados"] = ids
                self.contadores["tool_buscar"] += 1
            else:
                r = terminos.calcular_termino(
                    args.get("tipo", ""), relato=args.get("relato", ""))
                reg["resultado"] = r
                self.contadores["tool_termino"] += 1
                obs = (r["resumen"] if r.get("calculable")
                       else f"No fue posible calcular el termino: {r['motivo']}")
        except Exception as ex:                       # noqa: BLE001
            self.contadores["herramienta_con_error"] += 1
            reg["falla"] = f"herramienta_con_error: {type(ex).__name__}: {ex}"
            return (f"ERROR al ejecutar '{nombre}': {type(ex).__name__}: {ex}. "
                    f"Puedes intentar con otros argumentos o continuar sin esta "
                    f"herramienta."), reg

        self.contadores["tool_invocada"] += 1
        reg["observacion"] = obs[:400]
        return obs, reg

    # -- fase 1: el bucle del agente ------------------------------------
    def _bucle(self, relato: str) -> tuple[list[dict], dict]:
        mensajes = [{"role": "system", "content": INSTRUCCION_AGENTE},
                    {"role": "user", "content": f"RELATO DEL CIUDADANO:\n{relato}"}]
        registros: list[dict] = []
        vistas: set[tuple[str, str]] = set()
        info = {"pasos": 0, "agotado": False, "cierre": "el modelo concluyo"}

        # EL PRESUPUESTO CUENTA PASOS PRODUCTIVOS, NO LLAMADAS AL MODELO.
        #
        # Medido en m3/20261019T173316Z: **81 de 130 casos (62%)** agotaron los
        # 5 pasos, asi que `pasos_promedio` salio censurado por arriba y la
        # cifra de cabecera es una cota inferior. `veredicto_presupuesto()` ya
        # habia dictaminado, con umbral fijado de antemano, que subir
        # `max_pasos` solo mueve el techo.
        #
        # La causa no era el techo: era que se cobraban pasos que no aportaban
        # nada. Dos clases, las dos ya medidas en los contadores:
        #
        #   - `llamada_repetida` (12 casos): la repeticion se detectaba, se le
        #     avisaba al modelo... y el `for paso` avanzaba igual.
        #   - una busqueda cuyos fragmentos YA estaban todos en las
        #     observaciones anteriores. Es informacion cero, y
        #     `reg["recuperados"]` trae los ids para saberlo sin coste.
        #
        # Asi que el paso se cobra solo si la iteracion aporto algo nuevo. El
        # techo de ITERACIONES existe aparte: una llamada al modelo cuesta
        # dinero aunque no aporte, y sin ese tope un modelo que repitiera
        # siempre giraria sin fin.
        TECHO_ITERACIONES = self.max_pasos + 3
        fragmentos_vistos: set = set()
        paso, iteraciones, cerro_solo = 0, 0, False
        while paso < self.max_pasos and iteraciones < TECHO_ITERACIONES:
            iteraciones += 1
            info["pasos"] = paso + 1
            clave = self._clave("agente", json.dumps(mensajes, ensure_ascii=False))
            if clave in self._cache:
                bruto = json.loads(self._cache[clave])
                self.costos.registrar(cacheada=True)
            else:
                _t = time.perf_counter()
                r = self.cliente.chat.completions.create(
                    model=self.modelo, messages=mensajes, tools=HERRAMIENTAS,
                    tool_choice="auto", temperature=0, max_tokens=1024, seed=42)
                self.costos.registrar(time.perf_counter() - _t,
                                      getattr(r, "usage", None))
                m = r.choices[0].message
                bruto = {
                    "content": m.content or "",
                    "tool_calls": [
                        {"id": tc.id, "name": tc.function.name,
                         "arguments": tc.function.arguments or "{}"}
                        for tc in (m.tool_calls or [])],
                }
                self._cache[clave] = json.dumps(bruto, ensure_ascii=False)

            if not bruto["tool_calls"]:
                mensajes.append({"role": "assistant", "content": bruto["content"]})
                cerro_solo = True
                break

            mensajes.append({
                "role": "assistant", "content": bruto["content"] or None,
                "tool_calls": [
                    {"id": tc["id"], "type": "function",
                     "function": {"name": tc["name"], "arguments": tc["arguments"]}}
                    for tc in bruto["tool_calls"]],
            })

            aporto = False
            for tc in bruto["tool_calls"]:
                huella = (tc["name"], tc["arguments"])
                if huella in vistas:
                    self.contadores["llamada_repetida"] += 1
                    obs = ("ERROR: ya llamaste esta herramienta con estos mismos "
                           "argumentos y tienes la observacion arriba. No la repitas: "
                           "usa lo que ya tienes o concluye. Este paso NO se te "
                           "cobra del presupuesto.")
                    registros.append({"herramienta": tc["name"],
                                      "falla": "llamada_repetida"})
                else:
                    vistas.add(huella)
                    obs, reg = self._ejecutar(tc["name"], tc["arguments"])
                    registros.append(reg)
                    recup = reg.get("recuperados")
                    if recup is None:
                        # `calcular_termino` no recupera fragmentos: si no fue
                        # una repeticion, aporto por definicion.
                        aporto = aporto or not reg.get("falla")
                    else:
                        nuevos = [x for x in recup if x not in fragmentos_vistos]
                        reg["fragmentos_nuevos"] = len(nuevos)
                        if nuevos:
                            fragmentos_vistos.update(nuevos)
                            aporto = True
                        else:
                            # Informacion cero: los fragmentos ya estaban todos
                            # en las observaciones de arriba.
                            self.contadores["busqueda_sin_novedad"] += 1
                            reg["falla"] = "busqueda_sin_novedad"
                            obs += ("\n\n[aviso] Todos estos fragmentos ya "
                                    "estaban en tus observaciones anteriores: "
                                    "esta busqueda no aporto nada nuevo y NO se "
                                    "te cobra del presupuesto. Cambia la "
                                    "consulta o concluye.")
                mensajes.append({"role": "tool", "tool_call_id": tc["id"],
                                 "content": obs})

            if aporto:
                paso += 1
            else:
                self.contadores["paso_no_cobrado"] += 1

            # El presupuesto restante viaja con la ultima observacion. El
            # prompt lo anunciaba una vez al principio y el modelo no lleva la
            # cuenta: medido, agotaba los 5 pasos en 39 de 61 casos. Esto es
            # informacion que si usa para decidir entre seguir buscando y
            # concluir, y no cuesta una llamada extra.
            # `paso` ya cuenta los pasos COBRADOS, asi que no se le suma 1: si
            # la iteracion no aporto, el presupuesto no se movio y el aviso
            # tiene que decir lo mismo que la vez anterior.
            restantes = self.max_pasos - paso
            if restantes == 0:
                aviso = ("Era tu ultimo paso de herramienta. Responde AHORA en "
                         "texto breve con los hechos relevantes que encontraste.")
            elif restantes == 1:
                aviso = ("Te queda 1 paso de herramienta. Usalo solo si es "
                         "imprescindible; si ya tienes lo necesario, responde "
                         "en texto breve.")
            else:
                aviso = f"Te quedan {restantes} pasos de herramienta."
            mensajes[-1]["content"] += f"\n\n[presupuesto] {aviso}"

        if not cerro_solo:
            # Pasos agotados: el modelo seguia pidiendo herramientas. Se cuenta
            # --- es informacion real sobre si converge --- pero ya no se cierra
            # a oscuras: se le da UNA llamada mas sin herramientas disponibles,
            # asi que no le queda mas remedio que resumir. Antes, agotar el
            # presupuesto dejaba al extractor de hechos sin el resumen del
            # agente, trabajando solo con las observaciones crudas.
            self.contadores["pasos_agotados"] += 1
            info["agotado"] = True
            # Dos formas distintas de no converger, y conviene distinguirlas:
            # gastar el presupuesto buscando cosas nuevas es trabajo; dar
            # vueltas sin aportar nada es otra cosa, y el techo de iteraciones
            # es lo que la detiene.
            if iteraciones >= TECHO_ITERACIONES and paso < self.max_pasos:
                self.contadores["techo_iteraciones"] += 1
                info["cierre"] = (
                    f"techo de iteraciones ({TECHO_ITERACIONES}) con solo "
                    f"{paso} de {self.max_pasos} pasos cobrados: daba vueltas "
                    "sin aportar fragmentos nuevos")
            else:
                info["cierre"] = "pasos agotados: cierre forzado con resumen"
            try:
                clave_f = self._clave("agente_cierre",
                                      json.dumps(mensajes, ensure_ascii=False))
                if clave_f in self._cache:
                    texto_final = self._cache[clave_f]
                else:
                    rf = self.cliente.chat.completions.create(
                        model=self.modelo,
                        messages=mensajes + [{
                            "role": "user",
                            "content": ("Se agoto el presupuesto de herramientas. "
                                        "Resume en texto breve los hechos "
                                        "relevantes que encontraste. No pidas "
                                        "mas herramientas.")}],
                        tool_choice="none", temperature=0, max_tokens=512, seed=42)
                    texto_final = (rf.choices[0].message.content or "").strip()
                    if texto_final:
                        self._cache[clave_f] = texto_final
                if texto_final:
                    mensajes.append({"role": "assistant", "content": texto_final})
                else:
                    self.contadores["cierre_sin_resumen"] = (
                        self.contadores.get("cierre_sin_resumen", 0) + 1)
            except Exception as ex:                       # noqa: BLE001
                # Que falle el cierre no puede tumbar el caso: se cuenta y se
                # sigue con las observaciones crudas, como antes del arreglo.
                self.contadores["cierre_sin_resumen"] = (
                    self.contadores.get("cierre_sin_resumen", 0) + 1)
                self.fallos_extraccion.append(
                    {"error": type(ex).__name__, "detalle": str(ex)[:200],
                     "donde": "cierre forzado"})

        if not any("observacion" in r for r in registros):
            self.contadores["casos_sin_ninguna_tool"] += 1

        # `pasos_cobrados` es lo que el presupuesto cuenta; `iteraciones` es lo
        # que se le pago a la API. Publicar las dos es lo que permite leer si
        # un caso agoto el presupuesto trabajando o dando vueltas.
        info["iteraciones"] = iteraciones
        info["pasos_cobrados"] = paso
        return mensajes, {**info, "registros": registros}

    # -- fase 2: extraccion de hechos -----------------------------------
    def _hechos(self, mensajes: list[dict], relato: str) -> tuple[Hechos, dict]:
        # La MISMA pregunta de triabilidad que `sistema._prompt_hechos`,
        # desde `schema`. Escribirla dos veces haria que el brazo hibrido y
        # el del agente se abstuvieran con criterios distintos en silencio.
        prompt = schema.con_pregunta_triable(PROMPT_HECHOS_AGENTE).replace(
            "VOCABULARIO", ", ".join(sorted(schema.DERECHOS)))
        observaciones = "\n\n".join(
            f"[{m['role']}] {m['content']}" for m in mensajes[2:]
            if m.get("content"))
        usuario = (f"RELATO:\n{relato}\n\n"
                   f"OBSERVACIONES DE LAS HERRAMIENTAS:\n{observaciones or '(ninguna)'}")

        # LA CLAVE INCLUYE EL PROMPT, Y ESTE ES EL CASO QUE LO EXIGE.
        #
        # Era `self._clave("hechos", usuario)`: solo el relato. Asi que al
        # cambiar este prompt --- la redaccion de `afectacion_individual`, que
        # es lo que mandaba las acciones de cumplimiento a tutela --- el cache
        # seguia devolviendo las respuestas VIEJAS con la misma clave. Medido:
        # en m3/20261017T012001Z el agente resolvio sus 388 llamadas desde
        # cache y `accion_cumplimiento` siguio en F1 0.000, de modo que el
        # arreglo del prompt no se probo y nada lo delataba.
        #
        # Los otros dos caches del proyecto ya lo hacian bien:
        # `generador_groq` indexa por `modelo||sistema||usuario`, y el bucle de
        # arriba por la lista COMPLETA de mensajes. Este era el unico que
        # indexaba por una parte de su entrada, y por eso era el unico que
        # podia servir una respuesta de otro prompt.
        #
        # ---
        #
        # EL COSTE DE ESTAS LLAMADAS NO SE CONTABA, Y ESO HACIA MENTIR LA TABLA.
        #
        # En m3/20261017T143205Z `costos.json` decia `llamadas_reales: 0` para
        # el brazo 4 mientras el agente hacia 90 extracciones contra Groq: solo
        # el bucle pasaba por `costos.registrar`. El 0 no era falso en lo que
        # contaba --- el bucle si salio de cache --- pero si en lo que parecia
        # decir, que es que el brazo no gasto nada.
        _ini = time.perf_counter()
        clave = self._clave("hechos", prompt, usuario)
        if clave in self._cache:
            texto = self._cache[clave]
            self.costos.registrar(cacheada=True)
        else:
            # max_tokens=3072 y no 1024: con JSON forzado, el modelo gasta
            # presupuesto razonando antes de cerrar el documento, y Groq
            # responde 400 ("max completion tokens reached before generating a
            # valid document") en vez de devolver algo parcial. Con 1024 fallaba
            # en casos reales del eval set.
            #
            # Y el try/except, que es lo que de verdad faltaba: esta llamada era
            # la unica del agente sin red. Un 400 en UN caso tumbaba el brazo de
            # 61 entero. El agente cuenta modos de fallo justo para que ninguno
            # pueda hacer eso, asi que este tambien se cuenta y se sigue.
            try:
                r = self.cliente.chat.completions.create(
                    model=self.modelo,
                    messages=[{"role": "system", "content": prompt},
                              {"role": "user", "content": usuario}],
                    temperature=0, max_tokens=3072, seed=42,
                    response_format={"type": "json_object"})
                texto = (r.choices[0].message.content or "").strip()
                self.costos.registrar(time.perf_counter() - _ini,
                                      usage=getattr(r, "usage", None))
                if _json_de(texto):                   # validar ANTES de cachear
                    self._cache[clave] = texto
            except Exception as ex:                   # noqa: BLE001
                # Una llamada que falla igual costo tiempo y cupo: se cuenta,
                # o la latencia media sale optimista por no contar las malas.
                self.costos.registrar(time.perf_counter() - _ini)
                self.contadores["extraccion_api_fallo"] = (
                    self.contadores.get("extraccion_api_fallo", 0) + 1)
                self.fallos_extraccion.append({"error": type(ex).__name__,
                                               "detalle": str(ex)[:200]})
                texto = ""

        d = _json_de(texto)
        if not d:
            self.contadores["hechos_no_parseados"] += 1

        booleanos = {k: bool(d.get(k, False)) for k in CAMPOS_HECHOS}
        if "medio_eficaz" not in d:
            booleanos["medio_eficaz"] = True
        libres = {
            # Si el derecho no resuelve al vocabulario cerrado, el valor
            # es la valvula de escape y NO "ninguno": "ninguno" afirma que no
            # hay derecho fundamental en juego, y aqui lo que pasa es que no
            # se pudo leer. Afirmar lo primero es inventar una conclusion.
            "derecho": (d.get("derecho") if d.get("derecho") in schema.DERECHOS
                        else schema.DERECHO_ESCAPE),
            "accionado": (d.get("accionado") or "autoridad o particular accionado").strip(),
            "pretension": (d.get("pretension") or "amparar el derecho invocado").strip(),
        }
        libres["no_triable"], libres["motivo_no_triable"] = schema.leer_triable(d)
        if libres["no_triable"]:
            self.contadores["abstencion_por_no_triable"] += 1
        return Hechos(**booleanos), libres

    def determinismo_extractor(self, casos: list[dict], n_casos: int = 5,
                               repeticiones: int = 4) -> dict:
        """¿Extrae el modelo los MISMOS hechos de la misma entrada?

        POR QUE HACE FALTA, CON EL NUMERO QUE LO MOTIVA

        `data/validar_extractor.py --via accion_cumplimiento --control 0`
        corrido cinco veces seguidas, sin cache, dio **7, 8, 6, 7, 7** de 8 ---
        y fallando casos distintos cada vez: `E40` en una pasada, `E41` en
        otra, `E30` en la tercera. A `temperature=0` y `seed=42`.

        Eso cambia como se leen varias cifras de M3. El F1 de
        `accion_cumplimiento` del brazo 4 no es una medicion estable: es UNA
        TIRADA de una distribucion cuyo ancho nadie habia medido. Lo mismo que
        ya se midio del juez (`juez.determinismo_lote`), en el otro componente
        que sale a la API.

        QUE SE MIDE, Y POR QUE NO LA VIA

        Se mide la ESTABILIDAD DE LOS HECHOS, no de la via. La via la calcula
        el motor, que es determinista: si los hechos repiten, la via repite
        por construccion. Medir la via confundiria el ruido del extractor con
        la sensibilidad del arbol del art. 6, que son dos cosas y solo una es
        del modelo.

        Se mide SIN bucle de herramientas a proposito. Con bucle habria dos
        fuentes de variacion --- que busque distinto y que extraiga distinto
        --- y el numero no diria cual. El bucle se compara aparte: el dato de
        `validar_extractor` es que `derecho_colectivo` sale True en 0-1 de 8
        sin bucle y en 4 de 8 con bucle.

        Cuesta `n_casos * repeticiones` llamadas reales. Salta el cache, que
        es la unica forma de que la medicion pueda fallar.
        """
        import statistics
        sub = casos[:n_casos]
        por_caso, inestables = [], []
        for e in sub:
            vistos, fallos = [], 0
            for _ in range(repeticiones):
                # Sin bucle: `mensajes` minimo, como en `validar_extractor`.
                msgs = [{"role": "system", "content": "extraccion"},
                        {"role": "user", "content": e["relato"]}]
                clave_antes = dict(self._cache)
                try:
                    hechos, libres = self._hechos(msgs, e["relato"])
                    # La huella de la extraccion: los hechos en True, en
                    # orden. Es lo que el motor consume.
                    vistos.append(tuple(sorted(
                        k for k, v in hechos.__dict__.items() if v is True)))
                except Exception:                              # noqa: BLE001
                    fallos += 1
                # El cache haria que la 2a repeticion devolviera la 1a, y
                # entonces la prueba no podria fallar.
                self._cache = clave_antes
            distintas = len(set(vistos))
            estable = distintas == 1 and not fallos
            if not estable:
                inestables.append(e.get("id"))
            por_caso.append({
                "id": e.get("id"), "extracciones_distintas": distintas,
                "repeticiones": repeticiones, "estable": estable,
                "fallos": fallos,
                # Que hechos bailan, que es lo diagnosticable. Un extractor
                # que varia en `medio_eficaz` --- una ponderacion --- no es lo
                # mismo que uno que varia en `privacion_libertad`, que esta en
                # el texto o no esta.
                "hechos_que_varian": sorted(
                    {h for v in vistos for h in v}
                    - {h for v in vistos for h in v if
                       all(h in w for w in vistos)}),
            })

        est = sum(1 for x in por_caso if x["estable"])
        ds = [x["extracciones_distintas"] for x in por_caso]
        out = {
            "n_casos": len(por_caso), "repeticiones": repeticiones,
            "llamadas_reales": len(por_caso) * repeticiones,
            "casos_estables": est,
            "tasa_estabilidad": (round(est / len(por_caso), 4)
                                 if por_caso else None),
            "extracciones_distintas_media": (round(statistics.mean(ds), 3)
                                             if ds else None),
            "extracciones_distintas_maximo": max(ds) if ds else None,
            "casos_inestables": inestables,
            "por_caso": por_caso,
            "sin_bucle_de_herramientas": True,
            "lectura": (
                "`tasa_estabilidad` dice cada cuanto el extractor devuelve los "
                "MISMOS hechos ante la misma entrada. Si es menor que 1, toda "
                "cifra del brazo 4 que dependa de una sola corrida --- el F1 "
                "por clase, sobre todo en las clases de soporte pequeno --- es "
                "una tirada y no una medicion, y la diferencia entre dos "
                "brazos menor que ese ruido no se puede leer. `hechos_que_"
                "varian` dice CUALES bailan: los de ponderacion (`medio_"
                "eficaz`, `perjuicio_irremediable`) varian con mas motivo que "
                "los que estan en el texto o no estan."),
            "lo_que_no_dice": (
                "por que varia. `temperature=0` y `seed=42` hacen la "
                "reproducibilidad probable, no segura, y desde aqui no se "
                "distingue el lote del servicio, la version del modelo o el "
                "hardware. Tampoco mide el BUCLE: eso se compara aparte con "
                "`data/validar_extractor.py`."),
        }
        return out

    # -- ejecucion completa ---------------------------------------------
    def __call__(self, relato: str) -> str:
        from sistema import ARTICULO_POR_DERECHO

        t0 = time.perf_counter()
        self.costos.nuevo_caso()
        mensajes, info = self._bucle(relato)
        hechos, libres = self._hechos(mensajes, relato)
        dec = decidir(hechos)                          # el mecanismo NO lo elige el modelo

        # El fundamento tambien es determinista: el articulo del derecho sale de
        # un mapa cerrado y el de la decision lo pone la regla.
        citas = []
        art = ARTICULO_POR_DERECHO.get(libres["derecho"])
        if art:
            citas.append(art)
        citas += [c.strip() for c in dec.fundamento.split(";")]

        termino = next((r["resultado"] for r in info["registros"]
                        if r.get("herramienta") == "calcular_termino"
                        and isinstance(r.get("resultado"), dict)), None)
        razon = dec.razon
        if termino and termino.get("calculable"):
            razon += f". {termino['resumen']}"
        elif termino:
            razon += ". No fue posible calcular el termino: " + termino["motivo"]

        campos = {
            "derecho": libres["derecho"],
            "fundamento": "; ".join(dict.fromkeys(citas)),
            "accionado": libres["accionado"],
            "mecanismo": dec.mecanismo,
            "procede": dec.procede_tutela,
            "razon": razon,
            "pretension": libres["pretension"],
        }
        if libres.get("no_triable"):
            campos = schema.abstenerse(campos, libres["motivo_no_triable"])
        salida = schema.render_salida(campos)

        # TODO lo que el agente llego a leer, en el orden en que lo leyo y sin
        # repetidos. Es la union de las busquedas del caso, porque el agente
        # puede llamar `buscar_normas` varias veces y el contexto efectivo que
        # vio su extractor de hechos es la suma, no la ultima.
        recuperados = list(dict.fromkeys(
            i for r in info["registros"] for i in r.get("recuperados", [])))

        self.trazas.append({
            "relato": relato[:80],
            "pasos": info["pasos"],
            "cierre": info["cierre"],
            "recuperados": recuperados,
            "n_busquedas": sum(1 for r in info["registros"]
                               if r.get("herramienta") == "buscar_normas"),
            "herramientas": [r.get("herramienta") for r in info["registros"]],
            "fallas": [r["falla"] for r in info["registros"] if "falla" in r],
            "hechos": {k: v for k, v in hechos.__dict__.items() if v},
            "regla": dec.regla,
            # Lo EMITIDO, no lo que dijo el motor: ver la nota equivalente
            # en `sistema.SistemaReglas`. Las dos cosas se guardan.
            "mecanismo": None if libres.get("no_triable") else dec.mecanismo,
            "mecanismo_del_motor": dec.mecanismo,
            "no_triable": bool(libres.get("no_triable")),
            "motivo_no_triable": libres.get("motivo_no_triable") or "",
            "termino": termino,
            "segundos": round(time.perf_counter() - t0, 2),
            "registros": info["registros"],
        })
        if self.verbose:
            print(f"  {info['pasos']} paso(s) · {info['cierre']} · "
                  f"{[r.get('herramienta') for r in info['registros']]}")
        return salida

    # -- reporte --------------------------------------------------------
    def resumen(self) -> dict:
        n = len(self.trazas) or 1
        lat = sorted(t["segundos"] for t in self.trazas)
        return {
            "etiqueta": self.etiqueta,
            "casos": len(self.trazas),
            "pasos_promedio": round(sum(t["pasos"] for t in self.trazas) / n, 2),
            "latencia_s_media": round(sum(lat) / len(lat), 2) if lat else None,
            "latencia_s_p50": lat[int(0.50 * (len(lat) - 1))] if lat else None,
            "latencia_s_p95": lat[int(0.95 * (len(lat) - 1))] if lat else None,
            "costos": self.costos.resumen(),
            "contadores": dict(self.contadores),
            "casos_con_falla": sum(1 for t in self.trazas if t["fallas"]),
            # EL PROMEDIO ESTA CENSURADO POR ARRIBA, Y ESO NO ES UN DETALLE.
            #
            # En m3/20261017T143205Z 50 de 90 casos (56%) terminaron por
            # agotar `max_pasos`. Un caso que se corta en el techo no aporta
            # los pasos que habria necesitado, aporta el techo: la media no
            # estima "cuantos pasos necesita el agente", estima una cota
            # INFERIOR de eso. Con mas de la mitad de la muestra tocando el
            # limite, la cota es mucho mas baja que la cantidad real.
            #
            # `veredicto_presupuesto()` ya dictamino, con umbral fijado de
            # antemano, que subir `max_pasos` solo mueve el techo. Asi que no
            # se toca el parametro: lo que falta es un criterio de parada. Lo
            # que si se puede hacer hoy es que nadie cite la media sin la
            # censura, y por eso va dentro del mismo dict y no en una nota.
            "pasos_promedio_censura": self._censura_pasos(),
        }

    def _censura_pasos(self) -> dict:
        n = len(self.trazas)
        agot = self.contadores.get("pasos_agotados", 0)
        tasa = agot / n if n else None
        # SIN CASOS NO ES LO MISMO QUE SIN CENSURA.
        #
        # Con `n == 0` la tasa no es 0: no esta definida. Decir "ningun caso
        # toco el techo" cuando no hubo casos es el mismo error que este
        # proyecto corrige en `acierto_abstencion` y en `cohen_kappa`:
        # informar un valor tranquilizador donde no hubo medicion.
        if not n:
            return {"casos_en_el_techo": agot, "n": 0, "tasa": None,
                    "techo": self.max_pasos, "censurado": None,
                    "como_citar": "sin casos: no hay media que citar ni "
                                  "censura que declarar"}
        return {
            "casos_en_el_techo": agot,
            "n": n,
            "tasa": round(tasa, 4),
            "techo": self.max_pasos,
            "censurado": tasa > 0,
            "como_citar": (
                f"pasos/caso >= {round(sum(t['pasos'] for t in self.trazas) / n, 2)} "
                f"(cota INFERIOR: {agot} de {n} casos, {tasa:.0%}, se cortaron "
                f"en el techo de {self.max_pasos} pasos)"
                if tasa else
                f"pasos/caso = {round(sum(t['pasos'] for t in self.trazas) / n, 2)} "
                f"sobre {n} casos (ninguno toco el techo de "
                f"{self.max_pasos}: la media no esta censurada)"),
        }

    # Linea base medida en la corrida m3/20261016T031746Z, ANTES de que el
    # presupuesto viajara con la observacion y de que el cierre fuera forzado
    # con tool_choice="none". Es la cifra contra la que el ROADMAP #9 pide
    # comparar, y la deja comparar el propio resumen en vez de que haya que
    # acordarse de buscarla.
    BASE_PASOS_AGOTADOS = (39, 61)

    def veredicto_presupuesto(self) -> dict:
        """¿Sirvieron los arreglos del presupuesto? (ROADMAP #9)

        El presupuesto visible y el cierre forzado estaban implementados pero
        no probados contra la API real. Esto compara la tasa de esta corrida
        con la de antes de los arreglos y dice si bajo, en vez de dejar el
        numero suelto para que alguien lo interprete.
        """
        n = len(self.trazas)
        if not n:
            return {"concluyente": False, "motivo": "sin trazas"}
        agot = self.contadores["pasos_agotados"]
        tasa = agot / n
        b_a, b_n = self.BASE_PASOS_AGOTADOS
        tasa_base = b_a / b_n
        # Umbral: una caida de menos de un quinto de la tasa base es ruido con
        # estos tamanos de muestra, no una mejora.
        mejoro = tasa <= tasa_base * 0.80
        return {
            "concluyente": True,
            "pasos_agotados": agot, "casos": n, "tasa": round(tasa, 4),
            "tasa_base": round(tasa_base, 4),
            "base": f"{b_a}/{b_n}",
            "mejoro": mejoro,
            "veredicto": (
                "los arreglos del presupuesto FUNCIONAN: la tasa de casos que "
                "agotan los pasos bajo de forma apreciable."
                if mejoro else
                "los arreglos NO bastan. La tasa no bajo lo suficiente, asi que "
                "hay que REPLANTEAR el enfoque en vez de insistir: subir "
                "max_pasos solo mueve el techo, y el problema puede estar en "
                "que el agente no sabe cuando ha recuperado suficiente."),
        }

    def imprimir_resumen(self) -> None:
        r = self.resumen()
        print(f"\n{'='*72}\n  TOOL USE · {r['etiqueta']}\n{'='*72}")
        print(f"  {r['pasos_promedio_censura']['como_citar']}")
        print(f"  casos: {r['casos']} · pasos/caso: {r['pasos_promedio']} · "
              f"latencia {r['latencia_s_media']}s media, {r['latencia_s_p95']}s p95")
        print(f"\n  {'contador':<28}{'veces'}")
        print("  " + "-" * 36)
        for k, v in r["contadores"].items():
            print(f"  {k:<28}{v}")
        print(f"\n  casos con al menos una falla manejada: {r['casos_con_falla']}")
        v = self.veredicto_presupuesto()
        if v["concluyente"]:
            print(f"\n  ROADMAP #9 · presupuesto de pasos")
            print(f"    esta corrida: {v['pasos_agotados']}/{v['casos']} "
                  f"({v['tasa']:.1%})   antes de los arreglos: {v['base']} "
                  f"({v['tasa_base']:.1%})")
            print(f"    {'SIRVIO' if v['mejoro'] else 'NO SIRVIO'}: {v['veredicto']}")
        print("=" * 72)
