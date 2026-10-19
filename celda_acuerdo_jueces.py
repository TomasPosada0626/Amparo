# ===== CELDA: acuerdo entre jueces =========================================
#
# POR QUE NO HAY "SONDA" Y SE PUNTUAN LOS 25 DE UNA VEZ
#
# Hubo dos versiones antes y las dos fallaron por lo mismo: creer que unas
# pocas llamadas predicen si un modelo aguanta la tarea.
#
#   v1: sondeaba 1 caso. `allam-2-7b` lo acerto y se cayo en el 2.
#   v2: sondeaba 3 casos. `allam-2-7b` acerto los 3 --- y se cayo en el 4.
#       Peor: los 3 aciertos QUEDARON EN CACHE, asi que la corrida completa
#       los daba por buenos y fallaba en todo lo demas.
#
# No hay atajo: la prueba de que un juez sirve es que puntue los 25.
#
# QUE CAMBIO DESPUES DE m2/20261019T034128Z
#
# Esa corrida eligio `allam-2-7b` --- el primer candidato de otra familia que
# aguanto --- y salio **kappa 0.3831 con 2 de 25 casos sin nota**. Un 7B
# juzgando el razonamiento juridico de un 7B afinado. La cifra baja se lee
# como "los jueces discrepan" cuando lo que dice es "el segundo juez no
# sostiene la tarea". Dos arreglos:
#
#   1. EL ORDEN LO DA `juez.orden_de_candidatos()`: otra familia primero y,
#      dentro de cada grupo, el mas grande primero. `allam-2-7b` pasa de la
#      posicion 1 a la 5. Vive en `src/` y lo cubre la autoprueba, en vez de
#      estar escrito aqui donde nada lo mira.
#   2. SE EXIGEN LOS 25 SIN FALLOS. Antes bastaba con no fallar 3 seguidos, y
#      asi entro un juez con 2 huecos. Si ninguno llega a 25 limpios se usa el
#      menos malo Y SE DECLARA, porque perder la cifra entera seria peor.
import os

import groq
import harness
from juez import MODELO, Juez, familia_de, orden_de_candidatos

N_ACUERDO = 25            # lo mismo que en las corridas anteriores: comparable
MAX_FALLOS_SEGUIDOS = 3   # abandona a un modelo roto sin gastar los 25
MAX_CANDIDATOS = 4        # techo de coste: 4 x 25 llamadas en el peor caso

_ej, _sal = eval_set[:N_ACUERDO], sal_ft[:N_ACUERDO]
_cli = groq.Groq(api_key=os.environ["GROQ_API_KEY"])
FAM_JUEZ = familia_de(MODELO)


def _puntua(juez, etiqueta=""):
    """Puntua los N_ACUERDO casos. Devuelve (notas, huecos) o (None, n)."""
    notas, seguidos, huecos = [], 0, 0
    for n, (ej, sal) in enumerate(zip(_ej, _sal), 1):
        try:
            p = juez.puntuar(ej["relato"], schema.render_salida(ej), sal)
        except Exception:
            p = {"nota": None}
        if p.get("nota") is None:
            seguidos += 1
            huecos += 1
            if seguidos >= MAX_FALLOS_SEGUIDOS:
                print(f"    {etiqueta} abandonado en el caso {n} de "
                      f"{N_ACUERDO}: {seguidos} fallos seguidos")
                return None, huecos
        else:
            seguidos = 0
        notas.append(p)
        print(f"    {etiqueta} {n}/{N_ACUERDO}", end="\r")
    print(" " * 44, end="\r")
    return notas, huecos


# --- candidatos: el orden sale de src/, no de aqui ------------------------
try:
    _servidos = [m.id for m in _cli.models.list().data]
except Exception as ex:
    print(f"no pude listar modelos ({str(ex)[:60]}); uso la lista de juez.py")
    from juez import MODELOS_ALTERNATIVOS
    _servidos = list(MODELOS_ALTERNATIVOS)

_orden = orden_de_candidatos(_servidos, MODELO)
print(f"juez principal: {MODELO}  (familia {FAM_JUEZ})")
print(f"de {len(_servidos)} modelos servidos quedan {len(_orden)} candidatos")
print("orden de intento (otra familia primero, el mas grande primero):")
for _i, _m in enumerate(_orden[:MAX_CANDIDATOS], 1):
    print(f"   {_i}. {_m}  (familia {familia_de(_m)})")
print()

# --- el juez A se puntua una vez ------------------------------------------
print(f"juez A · {MODELO}")
_na, _huecos_a = _puntua(j, "A")
if _na is None:
    raise SystemExit("El juez principal no pudo puntuar: sin el no hay nada "
                     "que comparar.")
print(f"  juez A listo: {len(_na)} notas, {_huecos_a} sin nota")
print()

# --- se prueba cada candidato PUNTUANDO DE VERDAD -------------------------
j2 = _nb = None
_descartados, _mejor_parcial = [], None
for _m in _orden[:MAX_CANDIDATOS]:
    _fam = familia_de(_m)
    print(f"juez B candidato · {_m}  (familia {_fam})")
    try:
        _cand = Juez(modelo=_m)
    except Exception as ex:
        print(f"    no se pudo construir: {str(ex)[:60]}")
        _descartados.append({"modelo": _m, "familia": _fam,
                             "motivo": f"no se pudo construir: {str(ex)[:80]}"})
        continue
    _notas, _huecos = _puntua(_cand, "B")
    if _notas is None:
        _descartados.append({"modelo": _m, "familia": _fam,
                             "motivo": "no sostuvo la rubrica en los 25 casos"})
        continue
    if _huecos == 0:
        j2, _nb = _cand, _notas
        print(f"  juez B elegido: {_m}  ({len(_nb)} notas, sin huecos)")
        break
    # Puntuo los 25 pero con huecos: se guarda y se sigue buscando uno limpio.
    print(f"    {_m} dejo {_huecos} caso(s) sin nota: sigo buscando")
    _descartados.append({"modelo": _m, "familia": _fam,
                         "motivo": f"{_huecos} de {N_ACUERDO} sin nota"})
    if _mejor_parcial is None or _huecos < _mejor_parcial[2]:
        _mejor_parcial = (_cand, _notas, _huecos)

if j2 is None and _mejor_parcial is not None:
    j2, _nb, _h = _mejor_parcial
    print()
    print(f"NINGUN candidato puntuo los {N_ACUERDO} sin huecos. Se usa el "
          f"menos malo: {j2.modelo}, con {_h} sin nota.")
    print("Queda declarado en el artefacto: una kappa calculada sobre menos")
    print("casos de los pedidos mide menos, y callarlo seria peor.")

# --- el resultado ---------------------------------------------------------
acuerdo = None
if j2 is None:
    print()
    print("NINGUN segundo juez pudo puntuar. El acuerdo no se mide en esta")
    print("corrida y el artefacto NO se publica: un archivo vacio se leeria")
    print("como una medicion que salio mal, en vez de una que no se pudo")
    print("hacer.")
    for _d in _descartados:
        print(f"  {_d['modelo']:42s} {_d['motivo']}")
else:
    _fam2 = familia_de(j2.modelo)
    _misma_fam = FAM_JUEZ == _fam2
    acuerdo = harness.acuerdo_entre_jueces(_na, _nb, MODELO, j2.modelo)
    acuerdo["_familias"] = {
        "conocido": True, "familia_a": FAM_JUEZ, "familia_b": _fam2,
        "misma_familia": _misma_fam,
        "tamano_declarado_b": __import__("juez").tamano_declarado(j2.modelo),
        "que_mide": (
            "RUIDO del juez, no sesgo compartido: los dos jueces son del "
            "mismo linaje, asi que un acuerdo alto es compatible con que los "
            "dos se equivoquen igual."
            if _misma_fam else
            "ruido Y sesgo compartido: al ser de linajes distintos, coincidir "
            "es una senal mas fuerte de que la nota es una propiedad de la "
            "respuesta y no del juez."),
        "descartados": _descartados,
        "por_que_no_otra_familia": (
            "" if not _misma_fam else
            "ninguno de los modelos de otra familia servidos en esta cuenta "
            "sostuvo la rubrica sobre los 25 casos"),
    }
    print()
    print(f"juez A: {MODELO}  (familia {FAM_JUEZ})")
    print(f"juez B: {j2.modelo}  (familia {_fam2})")
    print(f"{'n comparados':<28}{acuerdo['n']}")
    print(f"{'acuerdo exacto':<28}{acuerdo['acuerdo_exacto']:.1%}")
    print(f"{'acuerdo a 1 punto':<28}{acuerdo['acuerdo_a_un_punto']:.1%}")
    print(f"{'kappa (aprueba >=4)':<28}{acuerdo['kappa_aprueba']}")
    print(f"{'Spearman':<28}{acuerdo['corr_spearman']}")
    print(f"{'sin nota en alguno':<28}{acuerdo['sin_nota_en_alguno']}")
    print()
    print(acuerdo["_familias"]["que_mide"])
    if _descartados:
        print()
        print("Descartados por el camino:")
        for _d in _descartados:
            print(f"  {_d['modelo']:42s} {_d['motivo']}")
    c.guardar_json("acuerdo_entre_jueces", acuerdo)
