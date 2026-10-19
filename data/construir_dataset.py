"""
Construye data/dataset.json v2.0.0 a partir de los 30 casos originales mas los
90 nuevos de nuevos_a.py y nuevos_b.py.

Tres cosas pasan aqui, en este orden, y si alguna falla el archivo no se
escribe:

  1. VERIFICACION CON EL MOTOR DE REGLAS. Cada caso nuevo trae los `hechos`
     del relato codificados a mano. Se corre `reglas.decidir()` sobre ellos y
     se exige que llegue al mismo mecanismo que dice la etiqueta. Una etiqueta
     que el motor no puede derivar es una etiqueta sospechosa: asi se descubrio
     el error de A09 en el eval set.

  2. VALIDACION DE ESQUEMA. `schema.validar()` revisa vocabulario cerrado,
     coherencia procede <-> mecanismo, ids unicos y que toda cita este en el
     whitelist de normas.json.

  3. SPLIT ESTRATIFICADO POR MECANISMO con semilla 42. El problema del dataset
     v1.0.0 no era el tamano sino el desbalance: 22 de 30 ejemplos eran tutela
     y habia UN solo ejemplo de accion_cumplimiento y UNO de habeas_corpus.
     El modelo no podia aprender esas clases, y M1 lo midio: acc_mecanismo
     58.7% = exactamente la clase mayoritaria.

Uso:  python data/construir_dataset.py
"""
from __future__ import annotations
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "data"))

import schema                                    # noqa: E402
from reglas import Hechos, decidir               # noqa: E402
from nuevos_a import bloque_a                    # noqa: E402
from nuevos_b import bloque_b                    # noqa: E402
from nuevos_c import bloque_c                    # noqa: E402
from nuevos_d import bloque_d                    # noqa: E402

SEMILLA = 42
FRACCION_VALIDATION = 0.25
PREFIJO = {
    "habeas_corpus": "HC",
    "accion_cumplimiento": "AC",
    "accion_popular": "AP",
    "via_ordinaria": "VO",
    "tutela": "TU",
    None: "AB",          # abstencion: no hay mecanismo
}

# Los casos de fuente real llevan prefijo propio para que se puedan contar y
# citar aparte: su procedencia es verificable y la de los demas no.
PREFIJO_REAL = "RE"


def verificar_con_reglas(nuevos: list[dict]) -> list[str]:
    """El motor de reglas tiene que llegar al mismo mecanismo que la etiqueta."""
    errores = []
    for c in nuevos:
        # Los casos de abstencion no pasan por el motor: la abstencion no es
        # una conclusion del arbol del art. 6, es el reconocimiento de que no
        # hay hechos suficientes para entrar al arbol.
        if c.get("tipo") == "abstencion":
            continue
        h = c.get("hechos")
        if not h:
            errores.append(f"{c['categoria']}: sin hechos codificados")
            continue
        try:
            d = decidir(Hechos(**h))
        except TypeError as ex:
            errores.append(f"{c['categoria']}: hechos invalidos -> {ex}")
            continue
        if d.mecanismo != c["mecanismo"]:
            errores.append(
                f"{c['categoria']}: etiqueta={c['mecanismo']} pero el motor "
                f"deriva {d.mecanismo} (regla: {d.regla})"
            )
    return errores


def main() -> int:
    ruta = RAIZ / "data" / "dataset.json"
    viejo = json.loads(ruta.read_text(encoding="utf-8"))

    # El script es IDEMPOTENTE: descarta los casos que el mismo genero en una
    # corrida anterior (ids HC/AC/AP/VO/TU + dos digitos) y reconstruye desde
    # los 30 originales, cuyos ids son T01-T20 y V01-V10. Sin esto, correrlo
    # dos veces duplica los 90 y el validador se llena de ids repetidos.
    generado = re.compile(r"(HC|AC|AP|VO|TU|AB|RE)\d{2}$")
    originales = [c for c in viejo["ejemplos"] if not generado.fullmatch(c["id"])]
    if len(originales) != 30:
        print(f"esperaba 30 casos originales (T01-T20, V01-V10), encontre {len(originales)}")
        return 1

    nuevos = bloque_a() + bloque_b() + bloque_c() + bloque_d()
    print(f"originales: {len(originales)} · nuevos: {len(nuevos)}")

    # --- 1. verificacion con el motor de reglas -------------------------
    errores = verificar_con_reglas(nuevos)
    if errores:
        print(f"\n{len(errores)} casos nuevos NO los deriva el motor de reglas:")
        for e in errores:
            print("  -", e)
        return 1
    n_reglas = sum(1 for c in nuevos if c.get("tipo") != "abstencion")
    n_abs = len(nuevos) - n_reglas
    print(f"motor de reglas: {n_reglas}/{n_reglas} casos derivados correctamente"
          f" ({n_abs} de abstencion quedan fuera del motor, a proposito)")

    # --- ids estables por mecanismo ------------------------------------
    contador: Counter = Counter()
    for c in nuevos:
        p = PREFIJO_REAL if c.get("tipo_fuente") == "real" else PREFIJO[c["mecanismo"]]
        contador[p] += 1
        c["id"] = f"{p}{contador[p]:02d}"
        # Solo los que de verdad paso el motor. Los de abstencion no entran al
        # arbol del art. 6, asi que marcarlos como verificados seria falso.
        c["verificado_con_reglas"] = c.get("tipo") != "abstencion"

    for c in originales:
        c.setdefault("verificado_con_reglas", False)
        c.setdefault("tipo_fuente", "redactado por el equipo")
    for c in nuevos:
        c.setdefault("tipo_fuente", "redactado por el equipo")

    todos = originales + nuevos

    # --- 2. split estratificado por mecanismo --------------------------
    por_mec: dict[str, list[dict]] = defaultdict(list)
    for c in todos:
        por_mec[c["mecanismo"]].append(c)

    rng = random.Random(SEMILLA)
    # `or ""` porque la clave de abstencion es None y no se puede ordenar
    # contra las cadenas de los demas mecanismos.
    for mec, casos in sorted(por_mec.items(), key=lambda kv: kv[0] or ""):
        # La ABSTENCION se sub-estratifica ademas por FAMILIA. Las seis
        # familias son seis comportamientos distintos --- "no entiendo tu
        # caso" no es "tu caso no es de mi competencia" --- y el sorteo plano
        # dejo una familia con UN ejemplo de train y DOS de validation, que es
        # medir el sorteo y no el modelo. Con una familia por caso de
        # validacion la metrica dice ademas CUAL de las seis falla. Para los
        # otros cinco mecanismos no cambia nada.
        grupos = [casos]
        if mec is None:
            por_familia: dict[str, list[dict]] = defaultdict(list)
            for c in casos:
                por_familia[c["categoria"]].append(c)
            grupos = [por_familia[k] for k in sorted(por_familia)]

        for grupo in grupos:
            grupo.sort(key=lambda c: c["id"])      # orden determinista antes de mezclar
            rng.shuffle(grupo)
            n_val = max(1, round(len(grupo) * FRACCION_VALIDATION))
            for i, c in enumerate(grupo):
                c["split"] = "validation" if i < n_val else "train"

    # --- 3. validacion de esquema --------------------------------------
    errs = schema.validar(todos)
    if errs:
        print(f"\n{len(errs)} errores de esquema:")
        for e in errs[:30]:
            print("  -", e)
        return 1
    print(f"schema.validar(): limpio sobre {len(todos)} ejemplos")

    # --- escritura -----------------------------------------------------
    splits = Counter(c["split"] for c in todos)
    mecs = Counter(c["mecanismo"] or "abstencion" for c in todos)
    derechos = Counter(c["derecho"] for c in todos)

    # Cifras calculadas sobre los datos, para que el meta no pueda quedar viejo
    # al re-ejecutar el constructor. La primera version las tenia escritas a
    # mano y se desincronizaron al anadir los bloques C y D.
    ev = json.loads((RAIZ / "data" / "eval_set.json").read_text(encoding="utf-8"))["ejemplos"]
    solape_relatos = len({c["relato"] for c in todos} & {e["relato"] for e in ev})
    cat_eval = {e["categoria"] for e in ev}
    n_cat_eval = len(cat_eval)
    solape_categorias = len({c["categoria"] for c in todos} & cat_eval)
    n_verificados = sum(c.get("verificado_con_reglas", False) for c in todos)
    n_abstencion = sum(c.get("tipo") == "abstencion" for c in todos)
    abs_split = Counter(c["split"] for c in todos
                        if c.get("tipo") == "abstencion")
    abs_train, abs_val = abs_split["train"], abs_split["validation"]
    n_reales = sum(c.get("tipo_fuente") == "real" for c in todos)
    # El campo `fuentes` afirma "tres de los cinco" casos de fuente real, y
    # la entrada 3.0.0 del changelog dice 5. Si entran o salen casos reales
    # esas dos frases quedan falsas sin avisar, asi que se verifica aqui en
    # vez de confiar en que alguien se acuerde de actualizarlas.
    if n_reales != 5:
        print(f"el meta afirma 5 casos de fuente real y hay {n_reales}: "
              "actualiza el campo `fuentes` y el changelog antes de seguir")
        return 1
    n_originales = len(originales)

    salida = {
        "meta": {
            "nombre": "tutela-co-triage",
            "version": "3.2.0",
            "idioma": "es-CO",
            "semilla": SEMILLA,
            "splits": dict(sorted(splits.items())),
            "balance_mecanismo": dict(sorted(mecs.items(), key=lambda kv: -kv[1])),
            "fuentes": {
                "real": "Casos de sentencias de la Corte Constitucional (relatoria oficial), "
                        "con numero de sentencia y de expediente en cada registro. La ETIQUETA "
                        "es la que decidio la Corte; el RELATO son los hechos condensados a "
                        "registro de ciudadano por el equipo, porque los hechos de una "
                        "sentencia estan en registro judicial y el sistema recibe lenguaje de "
                        "ciudadano. Tres de los cinco son carencia actual de objeto, una "
                        "categoria que el dataset escrito por el equipo no tenia: la realidad "
                        "produce supuestos que no se inventan.",
                "redactado por el equipo": "Casos construidos sobre los criterios de "
                        "procedencia del art. 6 del Decreto 2591 de 1991, con los hechos "
                        "codificados y verificados por el motor de reglas.",
            },
            "abstencion": (
                f"{n_abstencion} ejemplos con `mecanismo: null` ensenan la valvula de "
                f"escape del PROMPT ('Mecanismo: no determinable'): {abs_train} en train "
                f"y {abs_val} en validation. Sin ejemplos el prompt no basta, y con "
                "pocos tampoco: con 6 (4 de train) la corrida m1/20261015T182115Z midio "
                "`acierto_abstencion` 0.0 — el modelo forzo una etiqueta en los dos "
                "casos de validacion. El piso se subio al de las clases que si aprendio. "
                "No los verifica el motor de reglas porque la abstencion no es una "
                "conclusion del art. 6. Desde la v3.2.0 llevan ademas "
                f"`derecho: {schema.DERECHO_ESCAPE}` en vez de `ninguno`, que "
                "estaba sobrecargado."),
            "estratificacion": (
                "Split estratificado por mecanismo con semilla 42: el 25% de cada "
                "clase va a validation. Antes de mezclar, los casos se ordenan por id "
                "para que el resultado no dependa del orden del archivo. La abstencion "
                "se sub-estratifica por FAMILIA (seis familias, una razon distinta para "
                "no responder cada una), de modo que validation lleve exactamente una "
                "de cada: el sorteo plano dejaba una familia con un solo ejemplo de "
                "train y dos de validation, y entonces la metrica mide el sorteo."
            ),
            # Calculado, no afirmado. La version anterior de este campo decia
            # que ninguna categoria se repetia entre splits, y al medirlo
            # resulto falso: 15 de las 37 categorias del eval set tambien estan
            # en entrenamiento. Lo que si es cierto es que el solape de RELATOS
            # es cero, y eso es lo que hace valida la evaluacion.
            "disjunto_de": (
                f"data/eval_set.json. Solape de RELATOS: {solape_relatos} (verificado). "
                f"Las CATEGORIAS si reaparecen entre entrenamiento y evaluacion "
                f"({solape_categorias} de {n_cat_eval}) y es deliberado: se mide "
                f"generalizacion dentro de las mismas familias de situaciones "
                f"juridicas, no en familias nuevas. Ningun relato de evaluacion "
                f"participo en el entrenamiento."
            ),
            "verificacion": (
                f"{n_verificados} de los {len(todos)} casos llevan `hechos`: las "
                "cuestiones de hecho del relato codificadas a mano. construir_dataset.py "
                "corre el motor de reglas sobre esos hechos y exige que derive el mismo "
                "mecanismo de la etiqueta; si no coincide, el caso NO entra al dataset. "
                f"Quedan fuera del control {n_abstencion} casos de abstencion (la "
                "abstencion no es una conclusion del art. 6, es el reconocimiento de que "
                f"no hay hechos suficientes para entrar al arbol) y los {n_originales} "
                "casos de la v1.0.0, anteriores a ese control."
            ),
            "cambios": [
                "2.0.0 (2026-10-15): de 30 a 120 ejemplos. El motivo no fue el tamano "
                "sino el DESBALANCE. La v1.0.0 tenia 22 de 30 ejemplos de tutela (73%), "
                "UN solo ejemplo de accion_cumplimiento y UNO de habeas_corpus, y cubria "
                "26 categorias distintas con 30 casos: ~1.15 ejemplos por situacion "
                "juridica. El modelo no podia aprender las clases minoritarias y M1 lo "
                "midio sin ambiguedad: acc_mecanismo 58.7%, identico a la clase "
                "mayoritaria, y 16.7% en adversariales. La v2.0.0 baja tutela al 40% y "
                "lleva las otras cuatro clases a 16-24 ejemplos cada una.",
                "2.0.0: se anaden dos casos de la EXCEPCION del art. 6.3 (situacion "
                "colectiva en la que el titular si puede tutelar su propio derecho ante "
                "un perjuicio irremediable) y tres rutas distintas de improcedencia "
                "(art. 6.1 subsidiariedad, art. 6.4 dano consumado, art. 6.5 acto "
                "general), que la v1.0.0 no distinguia.",
                # Numeros FIJOS: es una entrada historica. La primera version de
                # esta linea los calculaba del estado actual, asi que al construir
                # la v3.1.0 se reescribio y paso a afirmar que la 3.0.0 tenia 143
                # ejemplos y 18 de abstencion. Tenia 131 y 6. Un changelog que se
                # recalcula no es un changelog.
                "3.0.0 (2026-10-15): 131 ejemplos. Entran 6 casos de ABSTENCION, con "
                "`mecanismo: null`, para que el modelo pueda aprender la valvula de "
                "escape del PROMPT en vez de forzar siempre una etiqueta; y 5 casos de "
                "FUENTE REAL, de sentencias de la Corte Constitucional con su numero de "
                "expediente, cuya etiqueta es la que decidio la Corte. Tres de esos "
                "cinco son carencia actual de objeto, una categoria que el dataset "
                "escrito por el equipo no tenia.",
                "3.0.0: el meta pasa a calcularse desde los datos. Las cifras estaban "
                "escritas a mano y se desincronizaron al anadir bloques: el campo "
                "`disjunto_de` llego a afirmar que ninguna categoria se repetia entre "
                "splits, que es falso, y los conteos citaban 120 ejemplos cuando ya "
                "habia mas. Un meta que se escribe a mano caduca sin avisar.",
                f"3.1.0 (2026-10-15): la abstencion pasa de 6 a {n_abstencion} ejemplos, "
                "tres por cada una de las seis familias. No es un ajuste a ojo: la "
                "corrida m1/20261015T182115Z midio `acierto_abstencion` 0.0 con los 6 "
                "anteriores (4 de train contra 94 que si emiten mecanismo) y, en la "
                "direccion contraria, `abstencion_indebida` 0.0 sobre 31 casos. El "
                "modelo no abstenia de mas: no abstenia nunca. En esa misma corrida las "
                "tres clases mas chicas tenian 12 ejemplos de train cada una y SI se "
                "aprendieron (macro F1 de mecanismo 0.844), asi que 12 es el piso "
                f"demostrado en este montaje y la abstencion queda en {abs_train} de "
                f"train. Sube ademas la validacion de 2 casos a {abs_val}: una metrica "
                "medida sobre n=2 no distingue un sistema roto de uno con mala suerte.",
                "3.1.0: la iteracion se hizo contra el SPLIT DE VALIDATION, no contra el "
                "eval set. En esa corrida el acierto en adversariales quedo en 50% (6 de "
                "12 mal) y se decidio NO anadir ejemplos de entrenamiento en las "
                "categorias que fallaron ahi, aunque se sabe cuales son: hacerlo seria "
                "ajustar al conjunto de prueba y el numero resultante ya no mediria "
                "generalizacion. El 50% se reporta como esta.",
                "3.1.0: el split de la abstencion se sub-estratifica por familia. Con "
                "el sorteo plano, `ab_relato_contradictorio` quedo con 1 caso de train "
                "y 2 de validation: la metrica habria medido una familia casi no vista "
                "en vez del comportamiento de abstencion. Ahora validation lleva una de "
                "cada familia, asi que el numero dice ademas cual falla.",
                f"3.2.0 (2026-10-15): la abstencion deja de usar `derecho: ninguno` y "
                f"pasa a `{schema.DERECHO_ESCAPE}`. `ninguno` estaba SOBRECARGADO: lo "
                "usaban tres conclusiones distintas --- 20 casos de via_ordinaria (no "
                "hay derecho fundamental que amparar), 16 de accion_cumplimiento (lo "
                "exigible es el cumplimiento de una norma) y 18 de abstencion (no se "
                "puede determinar nada) ---, o sea 54 de 143 ejemplos con UNA etiqueta "
                "para TRES razonamientos, y encima se median accuracy y macro F1 sobre "
                "ese campo. El efecto estaba medido: de los 16 errores de `derecho` de "
                "la corrida m1/20261015T185732Z, SEIS fueron emitir `ninguno` donde si "
                "habia un derecho identificable. Los otros dos usos si significan lo "
                "mismo y siguen compartiendo `ninguno`; el que se separa es la "
                "abstencion, que no afirma nada sobre el derecho sino sobre el INSUMO.",
                "3.2.0: el defecto se detecta inspeccionando SOLO el dataset --- tres "
                "tipos de caso con la misma etiqueta ---, no mirando cuales casos falla "
                "el modelo en el eval set, asi que corregirlo no es ajustar al conjunto "
                "de prueba. Lo que el eval set aporto fue la MAGNITUD, no el hallazgo.",
                "3.2.0: cambia tambien el PROMPT, que ahora licencia la valvula en los "
                "dos campos y advierte en que se diferencia de `ninguno`. Entrenar un "
                "comportamiento que el prompt no autoriza es exactamente la critica que "
                "le hicimos a la primera version de la valvula del mecanismo. "
                "Consecuencia que hay que declarar: las corridas anteriores a la v3.2.0 "
                "no son estrictamente comparables con las posteriores, porque cambiaron "
                "los datos Y la entrada. Lo comparable es cada corrida contra su propia "
                "clase mayoritaria.",
            ],
        },
        "ejemplos": todos,
    }

    ruta.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")

    print(f"\n{ruta.relative_to(RAIZ)} · {len(todos)} ejemplos")
    print(f"  splits: {dict(sorted(splits.items()))}")
    print("\n  mecanismo              total   train   val")
    for mec, n in mecs.most_common():
        clave = None if mec == "abstencion" else mec
        t = sum(1 for c in todos if c["mecanismo"] == clave and c["split"] == "train")
        v = n - t
        print(f"  {mec:<22}{n:>5}{t:>8}{v:>6}   ({n/len(todos):.0%})")
    print(f"\n  derechos cubiertos: {len(derechos)}/{len(schema.DERECHOS)}")
    print(f"  categorias distintas: {len(set(c['categoria'] for c in todos))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
