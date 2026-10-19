"""
Codifica los `hechos` de los 17 casos puntuables de `eval_set_m3.json` y los
verifica contra el motor de reglas.

POR QUE EXISTE, CON EL DATO QUE LO MOTIVA

`eval_set_m3.json` aporta 17 de los 80 casos puntuables sobre los que corren los
brazos 2, 3 y 4 de M3, y era el UNICO artefacto de evaluacion cuyos casos no
tenian `hechos`: 63/63 en `eval_set_v2.json`, 0/17 aqui. `anotar_fundamentos.py`
lo declaraba honestamente --- esos 17 quedaban en `equipo_afirmado`, nivel 4, el
mas debil de la escalera --- pero declarar no es verificar.

Lo que aporta pasarlos por el motor no es subir un nivel en una tabla: es el
CONTROL CRUZADO. En el dataset, ese mismo control encontro que A09 estaba
etiquetado `accion_cumplimiento` cuando el art. 9 de la Ley 393 lo reencauza a
tutela. Una etiqueta que nadie contrasta contra el arbol del art. 6 puede estar
mal y nada lo dice; 17 de 80 es el 21% de la vara con la que se midio M3.

Y hay un segundo efecto, medido: con `hechos` codificados,
`anotar_fundamentos.py` puede DERIVAR `fundamento_del_mecanismo` en vez de
copiarlo del gold, que es lo que hace que `pertinencia_por_plano` distinga
«equivoco la via» de «cito un derecho impertinente».

LOS HECHOS SON CUESTIONES DE HECHO, NUNCA CONCLUSIONES JURIDICAS

La codificacion es esparcida: solo se escriben los campos que se desvian del
default de `Hechos`. `medio_eficaz` tiene default True, asi que negarlo hay que
hacerlo explicito. El comentario de cada caso dice que regla del art. 6 lo
cierra, para que la codificacion sea auditable sin correr nada.

El script es idempotente. Si el motor no deriva la etiqueta de algun caso,
FALLA y no escribe nada: esa discrepancia es un hallazgo sobre la etiqueta, no
un detalle de implementacion.

    python -I data/codificar_hechos_m3.py
"""
from __future__ import annotations
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.reglas import Hechos, decidir, estrato_verificacion  # noqa: E402

# --------------------------------------------------------------------------
# Los hechos, caso por caso. Leidos del relato, en el orden del art. 6.
# --------------------------------------------------------------------------
HECHOS: dict[str, dict] = {

    # --- M01 · cancer de colon, quimioterapia sin autorizar ---------------
    # No hay otro proceso judicial para el derecho de peticion en salud. El
    # tumor que crece es la inminencia y la gravedad del art. 6.1 leido con la
    # T-225/1993; la enfermedad oncologica es debilidad manifiesta.
    # Cierra por: no hay causal -> tutela.
    "M01": {"afectacion_individual": True, "continua_vulneracion": True,
            "perjuicio_irremediable": True, "sujeto_especial_proteccion": True},

    # --- M02 · reporte en centrales nueve anos despues de la mora ---------
    # El dato existe y es cierto --- lo dice el propio relato --- pero el
    # termino de permanencia ya corrio. No hay proceso judicial para corregir
    # un dato: la via es el art. 15 CP.
    # Cierra por: no hay causal -> tutela.
    "M02": {"afectacion_individual": True, "continua_vulneracion": True},

    # --- M03 · diagnostico psiquiatrico publicado en cartelera -----------
    # El dato sensible YA se divulgo, pero la lista sigue puesta: hay
    # vulneracion que continua, asi que no es dano consumado del art. 6.4.
    # Cierra por: no hay causal -> tutela.
    "M03": {"afectacion_individual": True, "continua_vulneracion": True},

    # --- M04 · resolucion que niega una prima, recursos agotados ---------
    # Acto administrativo particular y concreto: la via es la nulidad y
    # restablecimiento del derecho. Y el relato niega el perjuicio
    # irremediable con sus propias palabras --- "tengo mi sueldo y puedo
    # esperar" ---, que es lo que hace eficaz el otro medio EN CONCRETO.
    # Cierra por: art. 6.1, subsidiariedad -> via ordinaria.
    "M04": {"afectacion_individual": True, "otro_medio_judicial": True},

    # --- M05 · cuota de alimentos sin fijar -------------------------------
    # El proceso de alimentos ante el juez de familia existe y es el idoneo.
    # Los menores son sujetos de especial proteccion, pero eso no desplaza la
    # via: la desplazaria un perjuicio irremediable, y el relato dice que el
    # padre "trabaja y tiene con que".
    # Cierra por: art. 6.1, subsidiariedad -> via ordinaria.
    "M05": {"afectacion_individual": True, "otro_medio_judicial": True,
            "sujeto_especial_proteccion": True},

    # --- M06 · acuerdo que sube el impuesto, sin facturar todavia --------
    # Norma de contenido general y abstracto SIN acto de aplicacion: "todavia
    # no me han facturado nada". Eso es exactamente lo que pone el art. 6.5, y
    # por eso `afectacion_individual` queda en False: no hay afectacion
    # concreta y actual, hay una norma que podria aplicarsele.
    # Cierra por: art. 6.5, acto general -> via ordinaria.
    "M06": {"acto_general": True},

    # --- M07 · agua dos horas al dia, trescientas casas ------------------
    # Interes de una comunidad indeterminada, y lo pedido es que "presten el
    # servicio bien" --- para todos, no la afectacion concreta de uno. Sin la
    # excepcion del art. 6.3 no hay por donde entrar a la tutela.
    # Cierra por: art. 6.3, derecho colectivo -> accion popular.
    "M07": {"derecho_colectivo": True},

    # --- M08 · casa por carcel concedida y no ejecutada, 31 dias ---------
    # Hay una decision judicial que ordena la libertad domiciliaria y la
    # persona sigue en el pabellon: es prolongacion ilicita de la privacion.
    # El art. 6.2 es categorico y no admite ponderacion.
    # Cierra por: art. 6.2, privacion de la libertad -> habeas corpus.
    "M08": {"privacion_libertad": True},

    # --- M09 · resolucion de jornada unica, dos anos sin ejecutar --------
    # Lo que se reclama es el acatamiento de un acto administrativo en firme.
    # `afectacion_individual` es False Y ESO ES LA DECISION DIFICIL DEL CASO:
    # quien escribe es una persona, pero ningun derecho fundamental SUYO esta
    # afectado de forma concreta y actual --- pide que se ejecute una
    # resolucion sobre tres colegios. El art. 9 de la Ley 393 hace el
    # cumplimiento subsidiario frente a la tutela precisamente por esto.
    # Cierra por: incumplimiento normativo -> accion de cumplimiento.
    "M09": {"incumplimiento_normativo": True},

    # --- M10 · ventilador domiciliario, enfermeria suspendida el jueves --
    # Menor de nueve anos con dependencia de ventilador: riesgo vital con
    # fecha. Inminencia, gravedad, urgencia e impostergabilidad concurren.
    # Cierra por: no hay causal -> tutela.
    "M10": {"afectacion_individual": True, "continua_vulneracion": True,
            "perjuicio_irremediable": True, "sujeto_especial_proteccion": True},

    # --- M14 · negacion de medicamento + inyeccion incrustada -----------
    # La inyeccion es ruido dirigido al evaluador, no un hecho del caso. Los
    # hechos son los de una negacion de servicio ordenado por el especialista.
    # Codificarlo asi es lo que permite que el caso MIDA si el sistema se
    # distrae: si el mecanismo sale bien, ignoro la instruccion.
    # Cierra por: no hay causal -> tutela.
    "M14": {"afectacion_individual": True, "continua_vulneracion": True},

    # --- M15 · planta de asfalto y fibrosis pulmonar --------------------
    # EL CASO QUE PRUEBA LA EXCEPCION DEL ART. 6.3. Hay un derecho colectivo
    # --- el ambiente del barrio --- y ademas el titular reclama la afectacion
    # concreta de SU salud, con riesgo vital documentado por el neumologo. Los
    # tres campos juntos son los que abren la excepcion; quitar cualquiera
    # devuelve el caso a accion popular.
    # Cierra por: excepcion del art. 6.3, luego no hay causal -> tutela.
    "M15": {"derecho_colectivo": True, "titular_pide_lo_suyo": True,
            "perjuicio_irremediable": True, "afectacion_individual": True,
            "continua_vulneracion": True, "sujeto_especial_proteccion": True},

    # --- MT01 · peticion del 3 de marzo sin contestar -------------------
    # Falta la respuesta. No hay proceso judicial para obtenerla.
    # Cierra por: no hay causal -> tutela.
    "MT01": {"afectacion_individual": True, "continua_vulneracion": True},

    # --- MT02 · copia del expediente docente ----------------------------
    # Peticion de documentos, con plazo propio mas corto. El hecho es el
    # mismo: no hay respuesta.
    # Cierra por: no hay causal -> tutela.
    "MT02": {"afectacion_individual": True, "continua_vulneracion": True},

    # --- MT03 · consulta a la superintendencia --------------------------
    # Consulta, con plazo propio mas largo, y el relato afirma que ya paso.
    # Cierra por: no hay causal -> tutela.
    "MT03": {"afectacion_individual": True, "continua_vulneracion": True},

    # --- MT04 · acuerdo de inventario de bienes, sin cumplir ------------
    # El relato hace la distincion por si mismo: "no es que a mi me hayan
    # negado algo: es que el acuerdo no se cumple". El escrito del 5 de
    # septiembre es la constitucion de renuencia del art. 8 de la Ley 393, no
    # un derecho de peticion cuya respuesta se reclame --- por eso
    # `afectacion_individual` es False y no hay vulneracion del art. 23 CP que
    # codificar.
    # Cierra por: incumplimiento normativo -> accion de cumplimiento.
    "MT04": {"incumplimiento_normativo": True},

    # --- MT05 · peticion respondida dentro del termino ------------------
    # EL ADVERSARIAL: el derecho de peticion se SATISFIZO --- respuesta
    # escrita, firmada y motivada, dentro del plazo ---, asi que no hay
    # vulneracion que continue. Lo que queda es el desacuerdo con el fondo, y
    # eso tiene su propia via.
    # Cierra por: art. 6.1, subsidiariedad -> via ordinaria.
    "MT05": {"afectacion_individual": True, "otro_medio_judicial": True},
}

# --------------------------------------------------------------------------
# EL DESGLOSE DE LAS DOS PONDERACIONES
#
# `perjuicio_irremediable` y `medio_eficaz` no se leen del relato: se ponderan.
# Un caso cuya etiqueta pivota en uno de los dos queda en estrato `juicio`, y
# eso es honesto pero poco util --- dice "creeme". Desglosarlos en los
# elementos que SI se leen convierte la afirmacion en una derivacion que
# cualquiera puede auditar contra el relato.
#
# `perjuicio_irremediable` son los cuatro elementos CONCURRENTES de la
# T-225/1993; `medio_eficaz` es la apreciacion en concreto del art. 6.1. El
# `__post_init__` de `Hechos` falla si el booleano afirmado no se sigue del
# desglose, asi que esto no es documentacion: es una comprobacion.
# --------------------------------------------------------------------------
DESGLOSE: dict[str, dict] = {

    # M04 · la resolucion de la prima. El relato niega el perjuicio con sus
    # propias palabras, y la nulidad y restablecimiento sirve para lo que pide.
    "M04": {"me_idoneo": True, "me_oportuno": True, "me_accesible": True,
            "pi_inminencia": False, "pi_gravedad": False,
            "pi_urgencia": False, "pi_impostergabilidad": False},

    # M05 · alimentos. El proceso ante el juez de familia es el idoneo para
    # fijar la cuota, y el relato no alega falta de subsistencia: dice que el
    # padre "trabaja y tiene con que". Sin gravedad no hay perjuicio
    # irremediable, por mas que los titulares sean menores.
    "M05": {"me_idoneo": True, "me_oportuno": True, "me_accesible": True,
            "pi_inminencia": False, "pi_gravedad": False,
            "pi_urgencia": False, "pi_impostergabilidad": False},

    # M15 · los cuatro elementos CONCURREN, y por eso se abre la excepcion del
    # art. 6.3: oxigeno permanente (inminencia), "le puede costar la vida"
    # (gravedad), "en semanas" (urgencia), y esperar la accion popular haria
    # inutil la proteccion (impostergabilidad).
    "M15": {"pi_inminencia": True, "pi_gravedad": True,
            "pi_urgencia": True, "pi_impostergabilidad": True},

    # MT05 · la peticion se respondio en termino, asi que lo que queda es el
    # desacuerdo de fondo y para eso hay via. Nada en el relato alega urgencia.
    "MT05": {"me_idoneo": True, "me_oportuno": True, "me_accesible": True,
             "pi_inminencia": False, "pi_gravedad": False,
             "pi_urgencia": False, "pi_impostergabilidad": False},
}


def main() -> int:
    ruta = RAIZ / "data" / "eval_set_m3.json"
    d = json.loads(ruta.read_text(encoding="utf-8"))
    casos = d["ejemplos"]

    # Los de abstencion no tienen mecanismo que derivar: quedan fuera a
    # proposito, no por olvido.
    puntuables = [c for c in casos if c.get("mecanismo")]
    ids = {c["id"] for c in puntuables}
    faltan = ids - HECHOS.keys()
    sobran = HECHOS.keys() - ids
    if faltan:
        print(f"FALLA: sin hechos codificados: {sorted(faltan)}")
        return 1
    if sobran:
        print(f"FALLA: hechos para ids que no son puntuables: {sorted(sobran)}")
        return 1

    errores: list[str] = []
    ok = 0
    for c in puntuables:
        h = {**HECHOS[c["id"]], **DESGLOSE.get(c["id"], {})}
        try:
            dec = decidir(Hechos(**h))
        except (TypeError, ValueError) as ex:
            errores.append(f"{c['id']}: hechos invalidos -> {ex}")
            continue
        if dec.mecanismo != c["mecanismo"]:
            errores.append(
                f"{c['id']} ({c.get('categoria')}): etiqueta={c['mecanismo']} "
                f"pero el motor deriva {dec.mecanismo} (regla: {dec.regla})")
            continue
        if dec.procede_tutela != c.get("procede"):
            errores.append(
                f"{c['id']}: procede={c.get('procede')} pero el motor deriva "
                f"{dec.procede_tutela}")
            continue
        ok += 1
        c["hechos"] = dict(h)
        c["verificado_con_reglas"] = True
        c["regla_que_cierra"] = dec.regla
        est, campos = estrato_verificacion(Hechos(**h))
        c["estrato_verificacion"] = est
        c["etiqueta_pivota_en"] = campos

    if errores:
        print(f"FALLA: el motor no deriva la etiqueta en {len(errores)} caso(s).")
        print("No se escribio nada. Una discrepancia aqui es un hallazgo sobre")
        print("la ETIQUETA, igual que el caso A09 del dataset.\n")
        for e in errores:
            print(f"  - {e}")
        return 1

    estratos = Counter(c["estrato_verificacion"] for c in puntuables)
    d.setdefault("meta", {})["verificacion"] = {
        "casos_con_hechos": ok,
        "casos_puntuables": len(puntuables),
        "casos_de_abstencion": len(casos) - len(puntuables),
        "estratos": dict(estratos),
        "metodo": "los `hechos` se codificaron leyendo cada relato y se pasaron "
                  "por `reglas.decidir()`; el script falla si el motor no "
                  "reproduce la etiqueta y la procedencia del gold",
        "limite": "`motor_de_reglas` significa CONSISTENTE con el arbol del "
                  "art. 6, no INDEPENDIENTE: los hechos los codifico el mismo "
                  "equipo que puso la etiqueta. Solo una fuente externa da "
                  "independencia.",
    }
    ruta.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")

    print(f"  {ok}/{len(puntuables)} casos puntuables verificados con el motor")
    print(f"  estratos: {dict(estratos)}")
    print(f"  {len(casos) - len(puntuables)} casos de abstencion, sin mecanismo "
          f"que derivar")
    print()
    print("  Ahora `anotar_fundamentos.py` puede DERIVAR "
          "`fundamento_del_mecanismo`")
    print("  en vez de copiarlo del gold. Hay que correrlo despues de esto.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
