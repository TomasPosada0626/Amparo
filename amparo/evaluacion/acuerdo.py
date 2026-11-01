"""Acuerdo entre dos jueces (M2, antes la celda 25 de M2_harness.ipynb).

Una nota de un solo juez no trae medida de su propia fiabilidad. Si dos
modelos distintos coinciden, la nota es una propiedad de LA RESPUESTA; si no,
es una propiedad DEL JUEZ y no se puede reportar sola.

POR QUE NO HAY "SONDA" Y SE PUNTUAN LOS 25 DE UNA VEZ

Hubo dos versiones antes y las dos fallaron por lo mismo: creer que unas pocas
llamadas predicen si un modelo aguanta la tarea.

  v1: sondeaba 1 caso. `allam-2-7b` lo acerto y se cayo en el 2.
  v2: sondeaba 3 casos. `allam-2-7b` acerto los 3 --- y se cayo en el 4.
      Peor: los 3 aciertos QUEDARON EN CACHE, asi que la corrida completa los
      daba por buenos y fallaba en todo lo demas.

No hay atajo: la prueba de que un juez sirve es que puntue los 25.

QUE CAMBIO DESPUES DE m2/20261019T034128Z

Esa corrida eligio `allam-2-7b` --- el primer candidato de otra familia que
aguanto --- y salio kappa 0.3831 con 2 de 25 casos sin nota: un 7B juzgando
el razonamiento juridico de un 7B afinado. La cifra baja se lee como "los
jueces discrepan" cuando lo que dice es "el segundo juez no sostiene la
tarea". Dos arreglos:

  1. EL ORDEN LO DA `juez.orden_de_candidatos()`: otra familia primero y,
     dentro de cada grupo, el mas grande primero.
  2. SE EXIGEN LOS 25 SIN FALLOS. Antes bastaba con no fallar 3 seguidos, y
     asi entro un juez con 2 huecos. Si ninguno llega a 25 limpios se usa el
     menos malo Y SE DECLARA, porque perder la cifra entera seria peor.

Hasta el tag `entrega-m4` habia en la raiz un `celda_acuerdo_jueces.py`, copia
ANTERIOR de esta celda sin la comparacion entre familias. Se retiro en la
migracion: lo vigente es este modulo.
"""
from __future__ import annotations

from amparo.evaluacion import harness
from amparo.evaluacion import juez as _juez
from amparo.nucleo import schema

N_ACUERDO = 25            # lo mismo que en las corridas anteriores: comparable
MAX_FALLOS_SEGUIDOS = 3   # abandona a un modelo roto sin gastar los 25
MAX_CANDIDATOS = 4        # techo de coste: 4 x 25 llamadas en el peor caso


def puntuar_muestra(juez, ejemplos: list[dict], salidas: list[str], etiqueta: str = "",
                    n: int = N_ACUERDO, max_fallos: int = MAX_FALLOS_SEGUIDOS):
    """Puntua los primeros `n` casos. Devuelve `(notas, huecos)` o `(None, huecos)`.

    `None` cuando el juez falla `max_fallos` veces SEGUIDAS: se abandona sin
    gastar el resto. Un fallo aislado deja un hueco (`nota: None`) y se sigue.
    """
    notas, seguidos, huecos = [], 0, 0
    pares = list(zip(ejemplos[:n], salidas[:n]))
    for i, (ej, sal) in enumerate(pares, 1):
        try:
            p = juez.puntuar(ej["relato"], schema.render_salida(ej), sal)
        except Exception:                                  # noqa: BLE001
            p = {"nota": None}
        if p.get("nota") is None:
            seguidos += 1
            huecos += 1
            if seguidos >= max_fallos:
                print(f"    {etiqueta} abandonado en el caso {i} de "
                      f"{len(pares)}: {seguidos} fallos seguidos")
                return None, huecos
        else:
            seguidos = 0
        notas.append(p)
        print(f"    {etiqueta} {i}/{len(pares)}", end="\r")
    print(" " * 44, end="\r")
    return notas, huecos


def candidatos(cliente, modelo_juez: str = _juez.MODELO) -> list[str]:
    """Los modelos servidos en la cuenta, en el orden de `orden_de_candidatos`.

    El orden sale de `juez.py`, no de aqui: alli lo cubre la autoprueba. Si no
    se puede listar, se usa `MODELOS_ALTERNATIVOS`.
    """
    try:
        servidos = [m.id for m in cliente.models.list().data]
    except Exception as ex:                                # noqa: BLE001
        print(f"no pude listar modelos ({str(ex)[:60]}); uso la lista de juez.py")
        servidos = list(_juez.MODELOS_ALTERNATIVOS)
    return _juez.orden_de_candidatos(servidos, modelo_juez)


def medir(juez_a, ejemplos: list[dict], salidas: list[str], *, cliente,
          construir_juez=None, n: int = N_ACUERDO,
          max_candidatos: int = MAX_CANDIDATOS) -> dict | None:
    """El acuerdo entre el juez principal y el mejor segundo juez disponible.

    `cliente` es el de Groq (solo para listar modelos) y `construir_juez(modelo)`
    construye un candidato (por defecto `juez.Juez(modelo=...)`): se inyectan
    para poder probarlo sin red. Devuelve el dict de
    `harness.acuerdo_entre_jueces` con `_familias` (y `acuerdo_entre_familias`
    si un candidato de otra familia puntuo aunque no fuera el elegido), o None
    si ningun segundo juez pudo puntuar: un archivo vacio se leeria como una
    medicion que salio mal en vez de una que no se hizo.
    """
    construir_juez = construir_juez or (lambda m: _juez.Juez(modelo=m))
    modelo_a = juez_a.modelo
    fam_juez = _juez.familia_de(modelo_a)
    ej, sal = ejemplos[:n], salidas[:n]

    orden = candidatos(cliente, modelo_a)
    print(f"juez principal: {modelo_a}  (familia {fam_juez})")
    print(f"quedan {len(orden)} candidatos")
    print("orden de intento (otra familia primero, el mas grande primero):")
    for i, m in enumerate(orden[:max_candidatos], 1):
        print(f"   {i}. {m}  (familia {_juez.familia_de(m)})")
    print()

    # --- el juez A se puntua una vez --------------------------------------
    print(f"juez A · {modelo_a}")
    na, huecos_a = puntuar_muestra(juez_a, ej, sal, "A", n=n)
    if na is None:
        raise SystemExit("El juez principal no pudo puntuar: sin el no hay nada "
                         "que comparar.")
    print(f"  juez A listo: {len(na)} notas, {huecos_a} sin nota")
    print()

    # --- se prueba cada candidato PUNTUANDO DE VERDAD ---------------------
    j2 = nb = None
    # `cruzado` guarda el mejor candidato de OTRA familia aunque no sea el
    # elegido: es la unica comparacion que controla sesgo compartido.
    descartados, mejor_parcial, cruzado = [], None, None
    for m in orden[:max_candidatos]:
        fam = _juez.familia_de(m)
        print(f"juez B candidato · {m}  (familia {fam})")
        try:
            cand = construir_juez(m)
        except Exception as ex:                            # noqa: BLE001
            print(f"    no se pudo construir: {str(ex)[:60]}")
            descartados.append({"modelo": m, "familia": fam,
                                "motivo": f"no se pudo construir: {str(ex)[:80]}"})
            continue
        notas, huecos = puntuar_muestra(cand, ej, sal, "B", n=n)
        if notas is None:
            descartados.append({"modelo": m, "familia": fam,
                                "motivo": f"no sostuvo la rubrica en los {n} casos"})
            continue
        if huecos == 0:
            j2, nb = cand, notas
            if fam != fam_juez:
                cruzado = (cand, notas, 0)
            print(f"  juez B elegido: {m}  ({len(nb)} notas, sin huecos)")
            break
        # Puntuo los n pero con huecos: se guarda y se sigue buscando uno limpio.
        print(f"    {m} dejo {huecos} caso(s) sin nota: sigo buscando")
        descartados.append({"modelo": m, "familia": fam,
                            "motivo": f"{huecos} de {n} sin nota"})
        if mejor_parcial is None or huecos < mejor_parcial[2]:
            mejor_parcial = (cand, notas, huecos)
        # UN CANDIDATO DE OTRA FAMILIA NO SE TIRA, AUNQUE NO SEA EL ELEGIDO.
        #
        # Era el agujero: la corrida 20261021T124137Z descarto `allam-2-7b`
        # por «1 de 25 sin nota», eligio `gpt-oss-20b` --- MISMA familia que
        # el juez --- y publico que «ninguno de otra familia sostuvo la
        # rubrica». Las notas de allam YA ESTABAN CALCULADAS y se tiraban.
        # Medido despues a mano: Spearman 0.3206 entre familias contra 0.7853
        # entre parientes, dos lecturas opuestas que la ADHERENCIA separa.
        # Guardarlo no cuesta una llamada mas: ya se pagaron.
        if fam != fam_juez and (cruzado is None or huecos < cruzado[2]):
            cruzado = (cand, notas, huecos)

    if j2 is None and mejor_parcial is not None:
        j2, nb, h = mejor_parcial
        print()
        print(f"NINGUN candidato puntuo los {n} sin huecos. Se usa el "
              f"menos malo: {j2.modelo}, con {h} sin nota.")
        print("Queda declarado en el artefacto: una kappa calculada sobre menos")
        print("casos de los pedidos mide menos, y callarlo seria peor.")

    if j2 is None:
        print()
        print("NINGUN segundo juez pudo puntuar. El acuerdo no se mide en esta")
        print("corrida y el artefacto NO se publica: un archivo vacio se leeria")
        print("como una medicion que salio mal, en vez de una que no se pudo")
        print("hacer.")
        for d in descartados:
            print(f"  {d['modelo']:42s} {d['motivo']}")
        return None

    fam2 = _juez.familia_de(j2.modelo)
    misma_fam = fam_juez == fam2
    acuerdo = harness.acuerdo_entre_jueces(na, nb, modelo_a, j2.modelo)
    acuerdo["_familias"] = {
        "conocido": True, "familia_a": fam_juez, "familia_b": fam2,
        "misma_familia": misma_fam,
        "tamano_declarado_b": _juez.tamano_declarado(j2.modelo),
        "que_mide": (
            "RUIDO del juez, no sesgo compartido: los dos jueces son del "
            "mismo linaje, asi que un acuerdo alto es compatible con que los "
            "dos se equivoquen igual."
            if misma_fam else
            "ruido Y sesgo compartido: al ser de linajes distintos, coincidir "
            "es una senal mas fuerte de que la nota es una propiedad de la "
            "respuesta y no del juez."),
        "descartados": descartados,
        "por_que_no_otra_familia": (
            "" if not misma_fam else
            f"ninguno de los modelos de otra familia servidos en esta cuenta "
            f"puntuo los {n} sin huecos, asi que el juez B elegido es pariente "
            "del principal. La comparacion entre familias NO se pierde: va en "
            "`acuerdo_entre_familias`, con su atribucion"),
    }

    # --- LA COMPARACION ENTRE FAMILIAS, con su atribucion -----------------
    #
    # Un acuerdo bajo entre familias admite dos explicaciones opuestas, y solo
    # la ADHERENCIA A LA RUBRICA las separa: nota >= 3 con el mecanismo
    # equivocado contra el gold es lo que descalifica a un evaluador, y es
    # comprobable sin preguntarle a nadie.
    if cruzado is not None and cruzado[0].modelo != j2.modelo:
        jc, nc, hc = cruzado
        ac = harness.acuerdo_entre_jueces(na, nc, modelo_a, jc.modelo)
        acuerdo["acuerdo_entre_familias"] = {
            "modelo_b": jc.modelo, "familia_b": _juez.familia_de(jc.modelo),
            "sin_nota": hc,
            "n": ac["n"],
            "kappa_aprueba": ac["kappa_aprueba"],
            "corr_spearman": ac["corr_spearman"],
            "acuerdo_exacto": ac["acuerdo_exacto"],
            "acuerdo_a_un_punto": ac["acuerdo_a_un_punto"],
            "adherencia_juez_A": harness.adherencia_a_la_rubrica(na, sal, ej),
            "adherencia_juez_cruzado": harness.adherencia_a_la_rubrica(nc, sal, ej),
            "como_leerlo": (
                "si este acuerdo es MAS BAJO que el de la misma familia, hay "
                "dos explicaciones opuestas: que las notas del juez principal "
                "sean una propiedad del juez y no de la respuesta, o que este "
                "candidato no sostenga la tarea. Compara "
                "`adherencia_juez_cruzado.incumple_generoso` con "
                "`adherencia_juez_A.incumple_generoso`: el que da nota >= 3 a "
                "un mecanismo objetivamente equivocado es el que no sirve "
                "como evaluador, y eso no es opinion --- se comprueba contra "
                "el gold."),
            "lo_que_no_dice": (
                "con un solo candidato de otra familia no se puede concluir "
                "que el sesgo de familia del juez principal sea pequeno. Se "
                "puede concluir si ESTE candidato sirve para medirlo."),
        }
        c_ = acuerdo["acuerdo_entre_familias"]
        print()
        print(f"comparacion ENTRE FAMILIAS - {jc.modelo} (familia {c_['familia_b']})")
        print(f"  {'':<24}{'parientes':>12}{'otra familia':>14}")
        for k in ("n", "kappa_aprueba", "corr_spearman"):
            print(f"  {k:<24}{str(acuerdo[k]):>12}{str(c_[k]):>14}")
        print(f"  {'notas generosas':<24}"
              f"{str(c_['adherencia_juez_A']['incumple_generoso']):>12}"
              f"{str(c_['adherencia_juez_cruzado']['incumple_generoso']):>14}")
        print()
        print("  Una nota >= 3 sobre un mecanismo objetivamente equivocado es")
        print("  lo que descalifica a un evaluador. Mira esa fila antes de")
        print("  leer la kappa.")
    print()
    print(f"juez A: {modelo_a}  (familia {fam_juez})")
    print(f"juez B: {j2.modelo}  (familia {fam2})")
    print(f"{'n comparados':<28}{acuerdo['n']}")
    print(f"{'acuerdo exacto':<28}{acuerdo['acuerdo_exacto']:.1%}")
    print(f"{'acuerdo a 1 punto':<28}{acuerdo['acuerdo_a_un_punto']:.1%}")
    print(f"{'kappa (aprueba >=4)':<28}{acuerdo['kappa_aprueba']}")
    print(f"{'Spearman':<28}{acuerdo['corr_spearman']}")
    print(f"{'sin nota en alguno':<28}{acuerdo['sin_nota_en_alguno']}")
    print()
    print(acuerdo["_familias"]["que_mide"])
    if descartados:
        print()
        print("Descartados por el camino:")
        for d in descartados:
            print(f"  {d['modelo']:42s} {d['motivo']}")
    return acuerdo
