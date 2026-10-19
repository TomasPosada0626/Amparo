"""
Cuatro casos mas de fuente real, de la Corte Constitucional (ROADMAP #30).

POR QUE IMPORTAN MAS QUE CUALQUIER OTRO CASO

Son las UNICAS etiquetas con fuente externa al equipo. En todo el proyecto ---
143 casos de dataset, 69 de eval v2, 21 de eval m3 --- solo 5 tenian el
mecanismo fijado por un tercero, y ese tercero es el que decide de verdad: la
Corte Constitucional. Los demas los redacto y etiqueto el equipo, y el motor
de reglas comprueba que sean CONSISTENTES con el art. 6, no que sean
CORRECTOS.

Con estos cuatro pasan de 5 a 9. Es el unico nivel 1 de la escalera de
fiabilidad del ROADMAP #8.

COMO SE CONSIGUIERON

La relatoria de la Corte (relatoria.corteconstitucional.gov.co) es alcanzable
con `reverificar_corpus.descargar()`. El primer intento del ROADMAP #30 la dio
por inaccesible usando WebFetch, que limita las citas a 125 caracteres: mismo
error que con el corpus. De cada sentencia se saca el numero de expediente, el
accionante (la Corte los anonimiza), el accionado y la PARTE RESOLUTIVA, que
es la que fija la etiqueta.

El relato se condensa a registro de ciudadano, igual que RE01-RE05: lo que una
persona escribiria al pedir ayuda, no el lenguaje de la sentencia. Lo que NO
se inventa es la etiqueta: es la que decidio la Corte.

LOS CUATRO, Y POR QUE ESTOS

  T-002 de 2024  carencia actual de objeto por hecho superado. Tercer caso de
                 esa familia, que es la mas dificil de acertar: el relato
                 parece tutelable y la respuesta correcta es que ya no hay
                 objeto.
  T-004 de 2024  tutela contra un COLEGIO PRIVADO por una sancion impuesta sin
                 debido proceso. Particular que presta servicio publico.
  T-008 de 2024  **tutela contra PROVIDENCIA JUDICIAL que la Corte SI
                 concedio**, por desconocimiento del precedente. Es el
                 contrapeso de A04 del eval set, que es improcedente por mero
                 desacuerdo con la valoracion de la prueba. Tener las dos
                 caras es lo que impide que el sistema aprenda "tutela contra
                 providencia = improcedente" como regla fija.
  T-011 de 2024  migrante venezolano con VIH, amparado por INTEGRALIDAD y
                 CONTINUIDAD. Es el caso que necesita el art. 6 de la Ley 1751
                 que entro al corpus en el ROADMAP #24, cuyo principio d) dice
                 que un servicio iniciado "no podra ser interrumpido por
                 razones administrativas o economicas".

Cada caso se verifica contra el motor de reglas antes de escribir. Idempotente.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.reglas import Hechos, decidir, estrato_verificacion  # noqa: E402

BASE = "https://www.corteconstitucional.gov.co/relatoria/2024"

CASOS = [
    {
        "id": "RE06",
        "categoria": "real_salud_hecho_superado",
        "relato":
            "Tengo 19 años y me diagnosticaron una enfermedad de los riñones "
            "que es hereditaria: mi abuela necesitó trasplante y mi mamá ya "
            "está en estadio cuatro. El médico me ordenó unos exámenes de "
            "control y la autorización se demoró meses. Puse la tutela y "
            "mientras el proceso iba, la EPS terminó autorizando y me hicieron "
            "todo lo que estaba pendiente.",
        "derecho": "salud",
        "fundamento": "art. 49 CP; Ley 1751 de 2015; art. 6.4 Decreto 2591 de 1991",
        "accionado": "EPS e INVIMA",
        "mecanismo": "via_ordinaria",
        "procede": False,
        "razon":
            "lo pedido se obtuvo durante el trámite, de modo que no subsiste "
            "objeto sobre el cual pronunciarse: la tutela no es declarativa de "
            "una vulneración ya superada",
        "pretension":
            "declarar la carencia actual de objeto por hecho superado",
        "hechos": {"dano_consumado": True, "continua_vulneracion": False,
                   "sujeto_especial_proteccion": True},
        "sentencia": "T-002-24",
        "procedencia":
            "Sentencia T-002 de 2024 de la Corte Constitucional de Colombia, "
            "expediente T-9.493.347, accionante anonimizado por la Corte como "
            "'Ulises', de 19 anos, diagnosticado con poliquistosis renal "
            "autosomica dominante, contra el INVIMA. La Corte REVOCO el fallo "
            "de instancia y DECLARO la carencia actual de objeto por hecho "
            "superado. Hechos condensados a registro de ciudadano por el "
            "equipo; la etiqueta es la que decidio la Corte.",
    },
    {
        "id": "RE07",
        "categoria": "real_educacion_sancion_sin_proceso",
        "relato":
            "A la muchacha que yo represento el colegio la sacó de las clases "
            "presenciales y la mandó a estudiar desde la casa, por un asunto "
            "que le atribuyeron y que nunca se probó. No le hicieron ningún "
            "proceso: no la citaron, no la dejaron explicar, simplemente le "
            "dijeron que no volviera al salón. Es un colegio privado.",
        "derecho": "educacion",
        "fundamento": "art. 29 CP; art. 67 CP; art. 42 Decreto 2591 de 1991",
        "accionado": "Colegio privado",
        "mecanismo": "tutela",
        "procede": True,
        "razon":
            "la sanción se impuso sin formulación de cargos ni oportunidad de "
            "defensa, y la tutela procede contra el particular que presta el "
            "servicio público de educación",
        "pretension":
            "ordenar el reintegro a las clases presenciales y que cualquier "
            "sanción se adopte con el debido proceso",
        "hechos": {"afectacion_individual": True,
                   "sujeto_especial_proteccion": True},
        "sentencia": "T-004-24",
        "procedencia":
            "Sentencia T-004 de 2024 de la Corte Constitucional de Colombia, "
            "expediente T-9.529.760, accion interpuesta por 'Alejandro' como "
            "agente oficioso de la joven 'Camila' (nombres anonimizados por la "
            "Corte) contra el colegio San Blas de Palmira, Valle del Cauca, por "
            "una sancion de educacion extramural. La Corte REVOCO la decision "
            "que habia negado la tutela y AMPARO los derechos a la educacion y "
            "al debido proceso. Hechos condensados a registro de ciudadano por "
            "el equipo; la etiqueta es la que decidio la Corte.",
    },
    {
        "id": "RE08",
        "categoria": "real_contra_providencia_concedida",
        "relato":
            "Soy la hermana y la persona de apoyo de una señora de 56 años con "
            "una discapacidad auditiva que tiene desde niña. Nuestros papás la "
            "cuidaron siempre y los dos murieron; desde entonces la cuido yo. "
            "Pedimos que le pasaran la pensión de nuestro papá y el juzgado nos "
            "la negó diciendo que la invalidez no se estructuró cuando debía. "
            "Apelamos y el tribunal confirmó, pero resolvió apartándose de lo "
            "que la Corte ya tiene decidido sobre cómo se valora esa fecha.",
        "derecho": "debido_proceso",
        "fundamento": "art. 29 CP; art. 48 CP; art. 13 CP",
        "accionado": "Tribunal Superior (Sala Laboral)",
        "mecanismo": "tutela",
        "procede": True,
        "razon":
            "la providencia se apartó del precedente constitucional sobre la "
            "valoración integral de la fecha de estructuración de la invalidez, "
            "que es un defecto específico y no un simple desacuerdo con la "
            "valoración de la prueba; el proceso ordinario se agotó y no "
            "protegió el derecho",
        "pretension":
            "dejar sin efecto la sentencia y ordenar una de reemplazo que "
            "reconozca la sustitución pensional",
        "hechos": {"afectacion_individual": True, "otro_medio_judicial": True,
                   "medio_eficaz": False, "sujeto_especial_proteccion": True,
                   "me_idoneo": True, "me_oportuno": False,
                   "me_accesible": True},
        "sentencia": "T-008-24",
        "limite_del_motor":
            "Tutela contra providencia judicial. Su procedencia se rige por las "
            "causales especificas de la C-590 de 2005 --- aqui el "
            "desconocimiento del precedente --- que el motor de reglas no "
            "implementa. El motor llega a `tutela` por el art. 6.1 leido en "
            "concreto (el medio ordinario se agoto y no fue oportuno), que es "
            "el mecanismo correcto con un fundamento que no es el preciso. "
            "Mismo limite que A04 y A08 del eval set, declarado igual.",
        "procedencia":
            "Sentencia T-008 de 2024 de la Corte Constitucional de Colombia, "
            "expediente T-9.509.042, accion interpuesta por 'Ursula' en calidad "
            "de persona de apoyo de 'Fermina' (nombres anonimizados por la "
            "Corte) contra la Sala de Decision Laboral del Tribunal Superior de "
            "Manizales. La Corte REVOCO la decision que declaraba improcedente "
            "la tutela, CONCEDIO el amparo del derecho al debido proceso y "
            "ORDENO proferir sentencia de reemplazo que reconozca la "
            "sustitucion pensional. Hechos condensados a registro de ciudadano "
            "por el equipo; la etiqueta es la que decidio la Corte.",
    },
    {
        "id": "RE09",
        "categoria": "real_salud_continuidad_migrante",
        "relato":
            "Soy venezolano, tengo 31 años y vivo con VIH. Estoy afiliado al "
            "régimen contributivo y venía con mi tratamiento, pero me lo "
            "empezaron a entregar a pedazos: cada medicamento y cada examen "
            "toca pedirlo otra vez y esperar. Hay meses en que me quedo sin el "
            "antirretroviral.",
        "derecho": "salud",
        "fundamento": "art. 49 CP; art. 13 CP; Ley 1751 de 2015",
        "accionado": "EPS",
        "mecanismo": "tutela",
        "procede": True,
        "razon":
            "un tratamiento iniciado no puede interrumpirse por razones "
            "administrativas y debe prestarse de forma integral, sin que el "
            "estatus migratorio sea oponible al afiliado",
        "pretension":
            "ordenar el suministro integral y continuo del tratamiento "
            "antirretroviral sin autorizaciones sucesivas",
        "hechos": {"afectacion_individual": True,
                   "sujeto_especial_proteccion": True},
        "sentencia": "T-011-24",
        "procedencia":
            "Sentencia T-011 de 2024 de la Corte Constitucional de Colombia, "
            "expediente T-9.375.986, accionante anonimizado por la Corte como "
            "'Genaro', venezolano de 31 anos diagnosticado con VIH, contra la "
            "Nueva EPS, por los principios de integralidad y continuidad. La "
            "Corte REVOCO el fallo de instancia y AMPARO los derechos a la "
            "salud y a la seguridad social. Hechos condensados a registro de "
            "ciudadano por el equipo; la etiqueta es la que decidio la Corte.",
        "respaldo_en_corpus":
            "El principio d) Continuidad del art. 6 de la Ley 1751 de 2015 --- "
            "'Una vez la provision de un servicio ha sido iniciada, este no "
            "podra ser interrumpido por razones administrativas o economicas' "
            "--- es el fundamento exacto, y entro al corpus en el ROADMAP #24. "
            "Este caso es la comprobacion de que ese fragmento hacia falta.",
    },
]
for c in CASOS:
    c.update(tipo_fuente="real", split="train", verificado_con_reglas=True,
             fuente_sentencia=f"{BASE}/{c['sentencia']}.htm")

GENERADO = re.compile(r"RE0[6-9]$")



def subir_version(meta: dict, propia: str) -> None:
    """Sube `meta["version"]` solo si `propia` es mayor.

    Tres scripts escriben el dataset y cada uno fijaba su version a pelo, asi
    que la final dependia del ORDEN en que se corrieran: `casos_reales.py`
    ponia 2.2.0 y despues `codificar_hechos_dataset.py` la bajaba a 2.1.0. Con
    esto la version del artefacto es la misma corra lo que corra primero.
    """
    def t(v):
        return tuple(int(x) for x in str(v or "0").split("."))
    if t(propia) > t(meta.get("version")):
        meta["version"] = propia

def main() -> int:
    ruta = RAIZ / "data" / "dataset.json"
    d = json.loads(ruta.read_text(encoding="utf-8"))
    casos = [c for c in d["ejemplos"] if not GENERADO.fullmatch(c["id"])]

    ids = {c["id"] for c in casos}
    relatos = {c["relato"] for c in casos}
    errores = []
    for c in CASOS:
        if c["id"] in ids:
            errores.append(f"{c['id']}: el id ya existe")
        if c["relato"] in relatos:
            errores.append(f"{c['id']}: relato repetido")
        try:
            dec = decidir(Hechos(**c["hechos"]))
        except (TypeError, ValueError) as ex:
            errores.append(f"{c['id']}: hechos invalidos -> {ex}")
            continue
        if dec.mecanismo != c["mecanismo"]:
            errores.append(f"{c['id']}: etiqueta={c['mecanismo']} pero el motor "
                           f"deriva {dec.mecanismo} (regla: {dec.regla})")
            continue
        if dec.procede_tutela != c["procede"]:
            errores.append(f"{c['id']}: procede no coincide")
            continue
        c["regla_que_cierra"] = dec.regla
        est, campos = estrato_verificacion(Hechos(**c["hechos"]))
        c["estrato_verificacion"] = est
        c["etiqueta_pivota_en"] = campos
        c["hechos"] = {k: c["hechos"][k] for k in sorted(c["hechos"])}

    # Cero solape con los eval sets: estos casos van a ENTRENAMIENTO.
    for a in ("eval_set_v2.json", "eval_set_m3.json"):
        p = RAIZ / "data" / a
        if p.exists():
            ev = {e["relato"] for e in json.loads(p.read_text(encoding="utf-8"))["ejemplos"]}
            for c in CASOS:
                if c["relato"] in ev:
                    errores.append(f"{c['id']}: FUGA, el relato esta en {a}")

    if errores:
        print(f"FALLA en {len(errores)} casos. No se escribio nada.")
        for e in errores:
            print(f"  - {e}")
        return 1

    casos += CASOS
    d["ejemplos"] = casos
    reales = [c for c in casos if c.get("tipo_fuente") == "real"]
    subir_version(d["meta"], "3.4.0")
    d["meta"]["casos_de_fuente_real"] = {
        "n": len(reales),
        "antes": len(reales) - len(CASOS),
        "por_que_importan":
            "Son las UNICAS etiquetas con fuente externa al equipo. El motor de "
            "reglas comprueba que una etiqueta sea CONSISTENTE con el art. 6, "
            "no que sea CORRECTA; aqui la fijo la Corte Constitucional, que es "
            "quien decide de verdad. Es el nivel 1 de la escalera de fiabilidad "
            "del ROADMAP #8, y el unico.",
        "como_se_consiguieron":
            "La relatoria de la Corte es alcanzable con "
            "reverificar_corpus.descargar(). El primer intento la dio por "
            "inaccesible usando WebFetch, que limita las citas a 125 caracteres. "
            "De cada sentencia se saca el expediente, el accionante (la Corte "
            "los anonimiza), el accionado y la parte resolutiva, que es la que "
            "fija la etiqueta. El relato se condensa a registro de ciudadano; "
            "la etiqueta NO se inventa.",
        "anadidos": [{"id": c["id"], "sentencia": c["sentencia"],
                      "mecanismo": c["mecanismo"],
                      "fuente": c["fuente_sentencia"]} for c in CASOS],
        "por_que_estos":
            "T-008 de 2024 es el mas valioso: una tutela contra PROVIDENCIA "
            "JUDICIAL que la Corte SI concedio, por desconocimiento del "
            "precedente. Es el contrapeso de A04 del eval set, que es "
            "improcedente por mero desacuerdo con la prueba. Tener las dos "
            "caras impide que el sistema aprenda 'tutela contra providencia = "
            "improcedente' como regla fija. T-011 de 2024 es la comprobacion de "
            "que el art. 6 de la Ley 1751 hacia falta en el corpus: su "
            "principio de Continuidad es el fundamento exacto.",
    }
    ruta.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                    encoding="utf-8")

    print(f"OK: dataset v3.4.0 con {len(casos)} casos")
    print(f"  fuente real: {len(reales) - len(CASOS)} -> {len(reales)}")
    for c in CASOS:
        print(f"   {c['id']}  {c['sentencia']}  {c['mecanismo']:<14} "
              f"{c['estrato_verificacion']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
