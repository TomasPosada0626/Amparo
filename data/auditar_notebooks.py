"""Auditoria estatica de los tres notebooks: orden, enganche y dependencias.

QUE COMPRUEBA, Y POR QUE CADA COSA

1. DEPENDENCIAS ENTRE CELDAS. Para cada celda de codigo, que nombres USA que
   ninguna celda anterior DEFINIO. Es la unica comprobacion que detecta de
   verdad "el notebook esta en mal orden": una celda que necesita algo que se
   define doce celdas mas abajo corre bien en la sesion donde se escribio ---
   porque el kernel ya tenia la variable --- y falla en la primera ejecucion
   limpia, que es justo la del profesor.

2. NUMERACION DE SECCIONES. Encabezados repetidos o fuera de orden. M1 tiene
   DOS secciones "## 7" y un "### 6.1" despues de un "## 6.2".

3. ORDEN DE ARRANQUE. El secreto tiene que cargarse ANTES de `arranque.celda`,
   que es quien lo comprueba; el manifiesto, antes de gastar GPU o API.

4. ARTEFACTOS. Que todo lo que `arranque.ORDEN` declara que el modulo produce
   quede publicado en alguna celda.

Lo que NO comprueba: si las cifras son correctas. Esto mira la fontaneria.
"""
import ast
import builtins
import io
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
import arranque  # noqa: E402

NOTEBOOKS = {"m1": "M1_finetuning.ipynb", "m2": "M2_harness.ipynb",
             "m3": "M3_rag.ipynb"}
BUILTINS = set(dir(builtins)) | {"__name__", "__file__", "get_ipython", "In",
                                 "Out", "exit", "quit", "display"}
HALLAZGOS: list[tuple[str, str, str]] = []   # (notebook, gravedad, texto)


def limpiar(src: str) -> str:
    """Quita magics y shell: `!pip` y `%cd` no son Python y rompen el parser."""
    fuera = []
    for ln in src.splitlines():
        s = ln.lstrip()
        if s.startswith(("!", "%", "?")):
            fuera.append("pass")
        else:
            fuera.append(ln)
    return "\n".join(fuera)


def sin_comentarios(src: str) -> str:
    """El codigo sin comentarios ni docstrings, para buscar marcas de verdad.

    LA PRIMERA VERSION DE ESTA AUDITORIA DIO DOS "GRAVE" FALSOS.
    Buscaba `arranque.celda` con una regex sobre el texto crudo, y la celda
    del manifiesto MENCIONA `arranque.celda()` en su comentario para explicar
    que comprueba otra cosa. Asi que la auditoria concluyo que el secreto se
    cargaba despues de `arranque.celda` en M1 y en M2 --- en los dos el
    `arranque.celda` que encontraba estaba dentro de un comentario.

    Un auditor que manda a arreglar codigo correcto es peor que no tenerlo:
    gasta el tiempo donde no hay nada y resta credito a sus hallazgos reales.

    LOS STRINGS SE CONSERVAN A PROPOSITO. `data/manifiesto.py` solo aparece
    dentro de una lista de argumentos --- `[_sys.executable, "-I",
    "data/manifiesto.py", ...]` --- y las rutas de los artefactos tambien son
    strings. Borrarlos haria fallar justo las comprobaciones que los buscan.
    Las docstrings se van con el resto solo si son el unico contenido, y por
    eso no se tocan: lo que estorba son los COMENTARIOS.
    """
    import tokenize
    fuera, ultimo = [], (1, 0)
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                continue
            if tok.start[0] > ultimo[0]:
                fuera.append("\n" * (tok.start[0] - ultimo[0]))
            fuera.append(tok.string)
            ultimo = tok.end
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # Si no tokeniza, es mejor quedarse con el crudo que no comprobar.
        return src
    return "".join(fuera)


class Recolector(ast.NodeVisitor):
    """Nombres que una celda DEFINE y nombres que USA."""

    def __init__(self):
        self.define, self.usa = set(), set()

    def _objetivo(self, nodo):
        if isinstance(nodo, ast.Name):
            self.define.add(nodo.id)
        elif isinstance(nodo, (ast.Tuple, ast.List)):
            for x in nodo.elts:
                self._objetivo(x)
        elif isinstance(nodo, ast.Starred):
            self._objetivo(nodo.value)
        else:                                  # a.b = ... / a[i] = ...
            self.visit(nodo)

    def visit_Name(self, n):
        if isinstance(n.ctx, ast.Load):
            self.usa.add(n.id)
        else:
            self.define.add(n.id)

    def visit_Assign(self, n):
        for t in n.targets:
            self._objetivo(t)
        self.visit(n.value)

    def visit_AnnAssign(self, n):
        self._objetivo(n.target)
        if n.value:
            self.visit(n.value)

    def visit_AugAssign(self, n):
        self._objetivo(n.target)
        self.visit(n.value)

    def visit_For(self, n):
        self._objetivo(n.target)
        self.visit(n.iter)
        for x in n.body + n.orelse:
            self.visit(x)

    def visit_comprehension(self, n):
        self._objetivo(n.target)
        self.visit(n.iter)
        for x in n.ifs:
            self.visit(x)

    def visit_withitem(self, n):
        self.visit(n.context_expr)
        if n.optional_vars:
            self._objetivo(n.optional_vars)

    def visit_Import(self, n):
        for a in n.names:
            self.define.add((a.asname or a.name).split(".")[0])

    def visit_ImportFrom(self, n):
        for a in n.names:
            self.define.add(a.asname or a.name)

    def _funcion(self, n):
        self.define.add(n.name)
        hijo = Recolector()
        for x in n.body:
            hijo.visit(x)
        args = n.args
        locales = {a.arg for a in
                   args.posonlyargs + args.args + args.kwonlyargs}
        if args.vararg:
            locales.add(args.vararg.arg)
        if args.kwarg:
            locales.add(args.kwarg.arg)
        for d in n.decorator_list:
            self.visit(d)
        for d in args.defaults + [x for x in args.kw_defaults if x]:
            self.visit(d)
        self.usa |= (hijo.usa - hijo.define - locales)

    visit_FunctionDef = _funcion
    visit_AsyncFunctionDef = _funcion

    def visit_ClassDef(self, n):
        self.define.add(n.name)
        hijo = Recolector()
        for x in n.body:
            hijo.visit(x)
        for b in n.bases:
            self.visit(b)
        for d in n.decorator_list:
            self.visit(d)
        self.usa |= (hijo.usa - hijo.define)

    def visit_Lambda(self, n):
        hijo = Recolector()
        hijo.visit(n.body)
        args = n.args
        locales = {a.arg for a in
                   args.posonlyargs + args.args + args.kwonlyargs}
        self.usa |= (hijo.usa - hijo.define - locales)

    def visit_ExceptHandler(self, n):
        if n.name:
            self.define.add(n.name)
        if n.type:
            self.visit(n.type)
        for x in n.body:
            self.visit(x)

    def visit_Global(self, n):
        self.define.update(n.names)


# --------------------------------------------------------------------------
# LAS CIFRAS DEL MARKDOWN CONTRA LOS ARCHIVOS DE DATOS
#
# Tres cifras del texto llevaban dos ampliaciones sin actualizarse:
#
#   M1, cabecera   «dataset v3.1.0: 143 ejemplos, 106 de train»  -> 160 y 123
#   M3, seccion 9  «el corpus tiene 57 fragmentos ... 19 de la CP» -> 69 y 20
#   M3, seccion 9  «el eval compartido tiene 69 casos»            -> 109
#
# Ninguna rompia nada al correr, y eso es justo lo que las hacia durar: un
# notebook que documenta un dataset que ya no existe se lee igual de bien.
#
# EL PROBLEMA DE COMPROBARLO: casi todas las cifras del markdown son
# HISTORICAS y deben quedarse como estan. «`_json_de` devolvia {} en 62 de 63
# casos» describe una corrida concreta; actualizarla la volveria falsa. Asi
# que no se escanea el texto buscando numeros --- eso daria decenas de falsos
# positivos y se acabaria ignorando el auditor, que es peor que no tenerlo.
#
# Se comprueban SOLO las lineas que se declaran como estado actual, con un
# prefijo explicito: `**Datos:**`, `**Corpus:**`, `**Eval:**`. El marcador es
# lo que separa «esto describe el proyecto de hoy» de «esto cuenta lo que
# paso», y lo pone quien escribe.
MARCADORES = ("Datos", "Corpus", "Eval")


def _cifras_reales() -> dict[str, dict[str, int | str]]:
    """Lo que los archivos de datos dicen de verdad, hoy."""
    import collections
    d = json.loads((RAIZ / "data" / "dataset.json").read_text(encoding="utf-8"))
    ej = d["ejemplos"]
    sp = collections.Counter(e["split"] for e in ej)

    co = json.loads((RAIZ / "data" / "corpus.json").read_text(encoding="utf-8"))
    por_norma = collections.Counter(x.get("norma") or "?"
                                    for x in co["documentos"])

    def n_ej(archivo):
        p = RAIZ / "data" / archivo
        return (len(json.loads(p.read_text(encoding="utf-8"))["ejemplos"])
                if p.exists() else None)

    return {
        "Datos": {"version": d["meta"]["version"], "ejemplos": len(ej),
                  "train": sp["train"], "validation": sp["validation"]},
        "Corpus": {"fragmentos": len(co["documentos"]),
                   "constitucion": por_norma["Constitución Política de Colombia"],
                   "decreto": por_norma["Decreto 2591 de 1991"]},
        "Eval": {"compartido": n_ej(arranque.ARCHIVO_EVAL)
                 if hasattr(arranque, "ARCHIVO_EVAL") else n_ej("eval_set_v3.json"),
                 "m3": n_ej("eval_set_m3.json")},
    }


def cifras_del_markdown(mod: str, celdas: list[dict]) -> None:
    """Toda cifra de una linea marcada tiene que estar en los archivos."""
    real = _cifras_reales()
    vistos = 0
    for i, c in enumerate(celdas):
        if c["cell_type"] != "markdown":
            continue
        for linea in "".join(c["source"]).splitlines():
            m = re.match(r"\s*[-*]?\s*\*\*(%s):\*\*(.*)"
                         % "|".join(MARCADORES), linea)
            if not m:
                continue
            etiqueta, resto = m.group(1), m.group(2)
            vistos += 1
            esperadas = real[etiqueta]
            # LAS REFERENCIAS A NORMAS SE QUITAN ANTES DE CONTAR. «Decreto
            # 2591 de 1991» lleva tres numeros y ninguno es un conteo; sin
            # esto, la primera version de esta comprobacion marcaba 2591 como
            # cifra inventada. Un auditor que grita sobre el numero de un
            # decreto ensena a ignorarlo.
            limpio = re.sub(
                r"\b(?:Decreto|Ley|Sentencia)\s+[A-Z]?-?\d+(?:\s+de\s+\d{4})?"
                r"|\bart[íi]?culos?\.?\s*\d+\w*|\bart\.?\s*\d+\w*", "", resto)
            # Cada numero de la linea tiene que ser uno de los reales. Es
            # deliberadamente laxo en QUE numero va donde --- la prosa cambia
            # --- y estricto en que ninguno sea inventado, que es el fallo.
            nums = {int(x.replace(".", "").replace(",", ""))
                    for x in re.findall(r"\b\d[\d.,]*\b", limpio)
                    if x.strip(".,").isdigit()}
            validos = {v for v in esperadas.values() if isinstance(v, int)}
            # Un numero de version (`v3.5.0`) no es un conteo: se comprueba
            # aparte, contra `meta.version`, y no cuenta como cifra.
            vers = re.findall(r"\bv(\d+\.\d+\.\d+)\b", resto)
            for v in vers:
                if v != esperadas.get("version"):
                    HALLAZGOS.append(
                        (mod, "GRAVE",
                         f"c{i}: `**{etiqueta}:**` dice version v{v} y "
                         f"`dataset.json` es v{esperadas.get('version')}"))
            nums -= {int(p) for v in vers for p in v.split(".")}
            inventados = sorted(nums - validos)
            if inventados:
                HALLAZGOS.append(
                    (mod, "GRAVE",
                     f"c{i}: `**{etiqueta}:**` cita {inventados} y los "
                     f"archivos dan {sorted(validos)}. Esa linea se declara "
                     "como estado ACTUAL, asi que no puede llevar una cifra "
                     "de otra version"))
            faltan = sorted(validos - nums)
            if faltan and etiqueta in ("Datos", "Corpus"):
                HALLAZGOS.append(
                    (mod, "AVISO",
                     f"c{i}: `**{etiqueta}:**` no menciona {faltan}"))
    if not vistos and mod in ("m1", "m3"):
        HALLAZGOS.append(
            (mod, "AVISO", "ninguna linea `**Datos:**` / `**Corpus:**` / "
                           "`**Eval:**`: las cifras del estado actual quedan "
                           "sin comprobar contra los archivos"))


def auditar(mod: str, nombre: str) -> None:
    p = RAIZ / "notebooks" / nombre
    nb = json.load(io.open(p, encoding="utf-8"))
    celdas = nb["cells"]

    cifras_del_markdown(mod, celdas)

    # ---- 1 · dependencias entre celdas ---------------------------------
    disponibles, roto = set(BUILTINS), False
    for i, c in enumerate(celdas):
        if c["cell_type"] != "code":
            continue
        src = limpiar("".join(c["source"]))
        try:
            arbol = ast.parse(src)
        except SyntaxError as ex:
            HALLAZGOS.append((mod, "GRAVE", f"c{i}: no parsea ({ex.msg} "
                                            f"linea {ex.lineno})"))
            roto = True
            continue
        r = Recolector()
        for x in arbol.body:
            r.visit(x)
        faltan = sorted(r.usa - r.define - disponibles)
        if faltan:
            HALLAZGOS.append(
                (mod, "GRAVE", f"c{i}: usa sin definir antes -> "
                               f"{', '.join(faltan[:8])}"))
        disponibles |= r.define
    if not roto:
        pass

    # ---- 2 · numeracion de secciones -----------------------------------
    # TODOS los encabezados de cada celda, no solo el primero.
    #
    # La primera version cortaba con `break` tras el primer encabezado de la
    # celda, y por eso NO vio que M1 tenia DOS secciones 6.2: una era
    # `### 6.2 La sobrecarga de ninguno`, el SEGUNDO encabezado de la celda de
    # 6.1, y la otra `## 6.2 Quien decide el mecanismo`, en su propia celda.
    # Una celda de markdown puede traer varias secciones y las trae.
    vistos, previo = {}, None
    for i, c in enumerate(celdas):
        if c["cell_type"] != "markdown":
            continue
        for ln in "".join(c["source"]).splitlines():
            m = re.match(r"^(#{2,4})\s*([\d]+(?:\.[\d]+)?)\s*[·.\-]", ln.strip())
            if not m:
                continue
            num = m.group(2)
            clave = tuple(int(x) for x in num.split("."))
            # El nivel del encabezado tiene que corresponder a la profundidad
            # del numero: `6.2` es una subseccion y va con `###`, no con `##`.
            nivel, esperado = len(m.group(1)), len(clave) + 1
            if nivel != esperado:
                HALLAZGOS.append(
                    (mod, "MEDIO", f"c{i}: seccion '{num}' lleva "
                                   f"{'#' * nivel} y le corresponde "
                                   f"{'#' * esperado}"))
            if num in vistos:
                HALLAZGOS.append(
                    (mod, "GRAVE", f"c{i}: seccion '{num}' REPETIDA "
                                   f"(ya estaba en c{vistos[num]})"))
            else:
                vistos[num] = i
            if previo and clave < previo[0]:
                HALLAZGOS.append(
                    (mod, "MEDIO", f"c{i}: seccion '{num}' va DESPUES de "
                                   f"'{previo[1]}' (c{previo[2]})"))
            previo = (clave, num, i)

    # ---- 3 · orden de arranque -----------------------------------------
    pos = {}
    for i, c in enumerate(celdas):
        if c["cell_type"] != "code":
            continue
        s = sin_comentarios(limpiar("".join(c["source"])))
        for nombre_marca, pat in (("secreto", r"userdata\.get"),
                                  ("arranque", r"arranque\.celda"),
                                  ("manifiesto", r"manifiesto\.py"),
                                  ("drive", r"drive\.mount")):
            if re.search(pat, s) and nombre_marca not in pos:
                pos[nombre_marca] = i
    for falta in ("manifiesto", "arranque", "drive"):
        if falta not in pos:
            HALLAZGOS.append((mod, "GRAVE", f"no hay celda de '{falta}'"))
    if "secreto" in pos and "arranque" in pos and pos["secreto"] > pos["arranque"]:
        HALLAZGOS.append(
            (mod, "GRAVE", f"el secreto (c{pos['secreto']}) se carga DESPUES "
                           f"de arranque.celda (c{pos['arranque']}), que es "
                           "quien lo comprueba"))
    if "manifiesto" in pos and "drive" in pos and pos["manifiesto"] < pos["drive"]:
        HALLAZGOS.append(
            (mod, "GRAVE", f"el manifiesto (c{pos['manifiesto']}) corre antes "
                           f"de montar Drive (c{pos['drive']})"))

    # ---- 4 · artefactos declarados vs publicados -----------------------
    todo = "".join("".join(c["source"]) for c in celdas
                   if c["cell_type"] == "code")
    declarados = {a.split("/")[-1] for a in arranque.ORDEN[mod]["produce"]}
    sin_publicar = sorted(a for a in declarados if a not in todo)
    if sin_publicar:
        HALLAZGOS.append(
            (mod, "GRAVE", f"declarados en ORDEN y no publicados: "
                           f"{', '.join(sin_publicar)}"))


def main() -> int:
    print("=" * 90)
    print("  AUDITORIA ESTATICA DE LOS TRES NOTEBOOKS")
    print("=" * 90)
    for mod, nombre in NOTEBOOKS.items():
        auditar(mod, nombre)

    for mod in NOTEBOOKS:
        hs = [h for h in HALLAZGOS if h[0] == mod]
        print()
        print(f"  {NOTEBOOKS[mod]}  ·  {len(hs)} hallazgo(s)")
        print("  " + "-" * 86)
        if not hs:
            print("    sin hallazgos")
        for _m, g, t in hs:
            print(f"    {g:6s} {t}")

    print()
    print("=" * 90)
    graves = sum(1 for h in HALLAZGOS if h[1] == "GRAVE")
    print(f"  {len(HALLAZGOS)} hallazgos en total · {graves} graves")
    print("=" * 90)
    return 1 if graves else 0


# La guarda no es cosmetica: sin ella, importar este modulo para reutilizar
# `Recolector` CORRE la auditoria entera y escribe su informe por encima de
# lo que estuviera haciendo quien importa.
if __name__ == "__main__":
    raise SystemExit(main())
