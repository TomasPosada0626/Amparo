"""
Casos con FECHA para que `calcular_termino` tenga trabajo (ROADMAP #13).

EL PROBLEMA. El agente del brazo 4 tiene dos herramientas y en la corrida
medida usó una: `buscar_normas` 228 veces y `calcular_termino` **1 vez en 61
casos**. No es que el agente la ignore: es que ningún caso del eval la
necesitaba. Construimos una herramienta y un eval que no la ejercita, y
entonces el 1/61 no mide al agente, mide al eval.

Dos salidas posibles: declarar la herramienta como no ejercitada, o darle
casos. Esto hace lo segundo, que es lo que permite saber si el agente sabe
usarla cuando hace falta.

POR QUÉ VAN EN eval_set_m3.json Y NO EN eval_set_v2.json

`calcular_termino` es una herramienta del brazo 4 de M3. Añadir casos a
`eval_set_v2.json` obligaría a volver a correr M1 y M2, que no tienen ninguna
herramienta que ejercitar. `eval_set_m3.json` existe justo para esto: casos que
solo M3 ve.

LA RESTRICCIÓN QUE HACE REPRODUCIBLE UN CASO CON FECHA

El resultado de `calcular_termino` depende de `date.today()`. Un caso cuyo gold
diga "aún no ha vencido" cambia de respuesta cuando pasa el calendario, y eso
es un caso de evaluación roto: la misma corrida da resultados distintos en
fechas distintas.

Por eso **todas las fechas de aquí están al menos un mes atrás y todos los
términos ya vencieron**. El veredicto "está vencido" es monótono: una vez
cierto, cierto para siempre. El script lo COMPRUEBA antes de escribir, y falla
si algún caso no está vencido todavía.

Idempotente: reconstruye desde los 15 casos originales M01-M15.
"""
from __future__ import annotations
import json
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "src"))

import terminos  # noqa: E402

# --------------------------------------------------------------------------
# Los casos. Cada uno lleva `termino_esperado`, que es el tipo que el agente
# debería pedirle a la herramienta, para poder medir no solo SI la usó sino si
# la usó bien.
# --------------------------------------------------------------------------
CASOS = [
    {
        "id": "MT01", "tipo": "gold", "dificultad": "rutinario",
        "categoria": "termino_peticion_general",
        "termino_esperado": "peticion_general",
        "relato": "Radiqué un derecho de petición en la alcaldía el 3 de marzo "
                  "de 2026 para que me certificaran unos pagos y hasta hoy no "
                  "me han contestado nada. Ya fui dos veces a preguntar.",
        "derecho": "peticion",
        "fundamento": "art. 23 CP; Ley 1755 de 2015",
        "accionado": "Alcaldía municipal",
        "mecanismo": "tutela", "procede": True,
        "razon": "el término de quince días hábiles del artículo 14 de la Ley "
                 "1755 de 2015 está ampliamente vencido y la falta de respuesta "
                 "vulnera el derecho de petición",
        "pretension": "ordenar que se resuelva la petición de fondo y se "
                      "notifique al solicitante",
    },
    {
        "id": "MT02", "tipo": "gold", "dificultad": "frontera",
        "categoria": "termino_peticion_documentos",
        "termino_esperado": "peticion_documentos",
        "relato": "El 10 de febrero de 2026 le pedí por escrito a la "
                  "secretaría de educación copia de mi expediente docente. Me "
                  "dijeron que el término para entregar documentos es más corto "
                  "que el de las peticiones normales, pero seguimos sin nada.",
        "derecho": "peticion",
        "fundamento": "art. 23 CP; Ley 1755 de 2015",
        "accionado": "Secretaría de Educación",
        "mecanismo": "tutela", "procede": True,
        "razon": "las peticiones de documentos e información tienen un término "
                 "de diez días hábiles conforme al artículo 14.1 de la Ley 1755 "
                 "de 2015, ampliamente superado",
        "pretension": "ordenar la entrega de la copia del expediente solicitado",
    },
    {
        "id": "MT03", "tipo": "gold", "dificultad": "frontera",
        "categoria": "termino_peticion_consulta",
        "termino_esperado": "peticion_consulta",
        "relato": "El 15 de enero de 2026 elevé una consulta a la "
                  "superintendencia sobre cómo se liquidan unos intereses, "
                  "porque la norma no es clara. Nunca respondieron. Entiendo "
                  "que las consultas tienen un plazo más largo, pero ya pasó.",
        "derecho": "peticion",
        "fundamento": "art. 23 CP; Ley 1755 de 2015",
        "accionado": "Superintendencia",
        "mecanismo": "tutela", "procede": True,
        "razon": "las consultas a las autoridades tienen un término de treinta "
                 "días hábiles conforme al artículo 14.2 de la Ley 1755 de 2015, "
                 "que a la fecha está vencido",
        "pretension": "ordenar que se resuelva la consulta elevada",
    },
    {
        "id": "MT04", "tipo": "gold", "dificultad": "frontera",
        "categoria": "termino_renuencia_cumplimiento",
        "termino_esperado": "renuencia_cumplimiento",
        "relato": "El 5 de septiembre de 2026 le pedí por escrito al municipio "
                  "que cumpliera el acuerdo del concejo que ordena publicar el "
                  "inventario de bienes públicos. No es que a mí me hayan "
                  "negado algo: es que el acuerdo no se cumple. No contestaron.",
        "derecho": "ninguno",
        "fundamento": "art. 87 CP; Ley 393 de 1997",
        "accionado": "Alcaldía municipal",
        "mecanismo": "accion_cumplimiento", "procede": False,
        "razon": "se reclama el acatamiento de un deber impuesto por una norma "
                 "vigente, sin afectación individual concreta, y el término de "
                 "diez días para constituir la renuencia del artículo 8 de la "
                 "Ley 393 de 1997 ya transcurrió",
        "pretension": "interponer la acción de cumplimiento una vez constituida "
                      "la renuencia",
    },
    {
        "id": "MT05", "tipo": "adversarial", "dificultad": "trampa",
        "categoria": "termino_peticion_respondida_a_tiempo",
        "termino_esperado": "peticion_general",
        "trampa": "El relato trae una fecha y un plazo, lo que empuja a "
                  "concluir que el término venció y conceder. Pero la "
                  "autoridad SÍ respondió dentro del término: lo que hay es "
                  "inconformidad con el contenido. La herramienta debe "
                  "calcular el término y el sistema concluir que se cumplió. "
                  "Mide si usa el cálculo para decidir o solo para justificar "
                  "lo que ya decidió.",
        "relato": "Radiqué la petición el 3 de marzo de 2026 y me respondieron "
                  "por escrito el 12 de marzo de 2026, con firma y explicación "
                  "de por qué no procede lo que pedí. No estoy de acuerdo con "
                  "esa respuesta y quiero que la revisen.",
        "derecho": "peticion",
        "fundamento": "art. 23 CP; Ley 1755 de 2015; art. 6.1 Decreto 2591 de 1991",
        "accionado": "Entidad pública",
        "mecanismo": "via_ordinaria", "procede": False,
        "razon": "la respuesta se produjo dentro del término de quince días "
                 "hábiles y fue de fondo y congruente; el derecho de petición "
                 "garantiza una respuesta, no que sea favorable",
        "pretension": "controvertir el contenido por los medios ordinarios, no "
                      "por tutela",
    },
    {
        # `tipo: abstencion`, no `adversarial`, aunque sea una trampa: el
        # scorecard separa los casos sin respuesta por ese campo
        # (`g["tipo"] != "abstencion"`), y marcarlo adversarial lo metía en el
        # grupo de los que SÍ tienen respuesta, de modo que una predicción
        # perfecta contaba una `abstencion_indebida`. La intención de trampa
        # viaja en `trampa` y en `dificultad`, que es la convención que ya usa
        # AB55 del eval v2.
        "id": "MT06", "tipo": "abstencion", "dificultad": "trampa",
        "categoria": "termino_sin_fecha_legible",
        "termino_esperado": None,
        "trampa": "Pide expresamente un cálculo de términos pero NO da una "
                  "fecha legible: dice 'hace rato' y 'el año pasado'. La "
                  "herramienta devuelve `calculable: False` con motivo, y lo "
                  "correcto es reportar eso en vez de inventar un vencimiento. "
                  "Mide si el sistema distingue 'no se puede calcular' de "
                  "'no venció'.",
        "relato": "Puse un derecho de petición hace rato, creo que el año "
                  "pasado o a principios de este, no tengo el radicado a mano. "
                  "Quiero saber si ya se venció el plazo que tienen para "
                  "contestarme.",
        "derecho": "no_determinable",
        "fundamento": "",
        "accionado": "no aplica",
        "mecanismo": None, "procede": False,
        "razon": "no se aporta una fecha de radicación legible ni el radicado, "
                 "de modo que no es posible calcular el término ni determinar si "
                 "hubo mora; falta el hecho del que depende todo lo demás",
        "pretension": "solicitar la fecha de radicación antes de orientar",
    },
]

HOY_DE_REFERENCIA = date(2026, 10, 16)
GENERADO = re.compile(r"MT\d{2}$")


def main() -> int:
    ruta = RAIZ / "data" / "eval_set_m3.json"
    d = json.loads(ruta.read_text(encoding="utf-8"))

    # Idempotencia: se descartan los MT## de una corrida anterior.
    originales = [c for c in d["ejemplos"] if not GENERADO.fullmatch(c["id"])]
    if len(originales) != 15:
        print(f"esperaba 15 casos originales M01-M15, encontre {len(originales)}")
        return 1

    errores: list[str] = []
    relatos = {c["relato"] for c in originales}
    ds = json.loads((RAIZ / "data" / "dataset.json").read_text(encoding="utf-8"))
    v2 = json.loads((RAIZ / "data" / "eval_set_v2.json").read_text(encoding="utf-8"))
    relatos |= {c["relato"] for c in ds["ejemplos"]}
    relatos |= {c["relato"] for c in v2["ejemplos"]}

    for c in CASOS:
        if c["relato"] in relatos:
            errores.append(f"{c['id']}: relato repetido")
        relatos.add(c["relato"])

        tipo = c["termino_esperado"]
        if tipo is None:
            # MT06 debe ser NO calculable: es su razon de ser.
            r = terminos.calcular_termino("peticion_general", relato=c["relato"],
                                          hoy=HOY_DE_REFERENCIA)
            if r.get("calculable"):
                errores.append(
                    f"{c['id']}: deberia ser NO calculable y la herramienta "
                    f"leyo una fecha")
            c["termino_calculable_esperado"] = False
            continue

        r = terminos.calcular_termino(tipo, relato=c["relato"],
                                      hoy=HOY_DE_REFERENCIA)
        if not r.get("calculable"):
            errores.append(f"{c['id']}: la herramienta no puede calcular "
                           f"`{tipo}` -> {r.get('motivo')}")
            continue
        # LA RESTRICCION CLAVE: el termino tiene que estar YA VENCIDO, para que
        # el caso no cambie de respuesta con el calendario.
        if not r.get("vencido"):
            errores.append(
                f"{c['id']}: el termino `{tipo}` AUN NO ha vencido "
                f"({r.get('resumen', '')[:90]}). Un caso cuyo veredicto cambia "
                f"con la fecha de la corrida no es reproducible: usa una fecha "
                f"mas antigua.")
            continue
        c["termino_calculable_esperado"] = True
        c["termino_vencido_esperado"] = True

    if errores:
        print(f"FALLA en {len(errores)} casos. No se escribio nada.\n")
        for e in errores:
            print(f"  - {e}")
        return 1

    for c in CASOS:
        c["split"] = "eval_m3"

    d["ejemplos"] = originales + CASOS
    d["meta"]["version"] = "1.1.0"
    d["meta"]["composicion"] = {}
    for c in d["ejemplos"]:
        k = c.get("tipo", "?")
        d["meta"]["composicion"][k] = d["meta"]["composicion"].get(k, 0) + 1
    d["meta"]["casos_con_termino"] = {
        "n": len(CASOS),
        "ids": [c["id"] for c in CASOS],
        "por_que":
            "el agente del brazo 4 tiene dos herramientas y en la corrida "
            "medida uso `buscar_normas` 228 veces y `calcular_termino` 1 vez en "
            "61 casos. No era que el agente la ignorara: ningun caso del eval la "
            "necesitaba, asi que el 1/61 no medía al agente sino al eval.",
        "reproducibilidad":
            "TODAS las fechas estan al menos un mes atras y TODOS los terminos "
            "ya vencieron, verificado por data/construir_eval_m3_terminos.py "
            "antes de escribir. El veredicto 'esta vencido' es monotono: una vez "
            "cierto, cierto siempre. Un caso que dijera 'aun no vence' cambiaria "
            "de respuesta con el calendario y no seria reproducible.",
        "que_mide":
            "`termino_esperado` dice que tipo de termino deberia pedir el "
            "agente, asi que se puede medir no solo SI uso la herramienta sino "
            "si la uso BIEN. MT05 y MT06 son las trampas: en MT05 el termino se "
            "cumplio (la respuesta llego a tiempo) y en MT06 no hay fecha "
            "legible, de modo que la herramienta devuelve `calculable: False` y "
            "lo correcto es reportarlo en vez de inventar un vencimiento.",
    }
    ruta.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"OK: eval_set_m3.json con {len(d['ejemplos'])} casos "
          f"({len(originales)} originales + {len(CASOS)} con termino)")
    print(f"\ncomposicion: {d['meta']['composicion']}")
    print("\ntipos de termino ejercitados:")
    for c in CASOS:
        t = c["termino_esperado"] or "(no calculable, a proposito)"
        print(f"  {c['id']}  {t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
