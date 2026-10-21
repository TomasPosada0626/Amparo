"""Lectura de los formularios que rellena una persona. Tolerante a Excel.

POR QUE EXISTE, CON LOS DOS FALLOS QUE LO MOTIVARON

`calibracion_juez.py` y `doble_anotacion.py` escriben un CSV en UTF-8, con las
instrucciones arriba en lineas que empiezan por `#`, y lo volvian a leer con
`read_text(encoding="utf-8")` y un filtro `not l.startswith("#")`. Eso supone
que el archivo vuelve tal como salio. No vuelve: vuelve de Excel.

  1. Excel «CSV» (el de toda la vida) guarda en la pagina de codigos del
     sistema --- cp1252 en Windows. `read_text(encoding="utf-8")` lanza
     UnicodeDecodeError y el script muere. Es ruidoso, asi que es el fallo
     benigno de los dos: se ve y se arregla.

  2. Excel «CSV UTF-8» guarda con BOM. El BOM queda pegado al principio de la
     PRIMERA LINEA, que es un comentario, asi que `l.startswith("#")` da False
     y esa linea NO se filtra: pasa a ser la cabecera del CSV. `DictReader`
     toma el texto del comentario como nombre de columna, y a partir de ahi
     `fila["mecanismo"]` vale None en todas las filas. El script informa
     entonces «no tiene ninguna fila diligenciada» --- sobre un formulario
     entero correctamente rellenado.

El segundo es el grave, y no porque sea mas raro: porque es SILENCIOSO. El
primero pierde un minuto; el segundo pierde el trabajo de una persona y dice
que la persona no lo hizo.

Ninguno de los dos es culpa de quien anota. Las dos son las dos opciones que
Excel ofrece cuando le dices «guardar como CSV».
"""
from __future__ import annotations

import csv
from pathlib import Path

# El orden importa: `utf-8-sig` consume el BOM si esta y se comporta como
# utf-8 si no, asi que va antes de cp1252, que decodifica cualquier byte y por
# tanto nunca falla --- si fuera primero, se "leeria" bien un archivo utf-8
# dejando los acentos destrozados.
CODIFICACIONES = ("utf-8-sig", "utf-8", "cp1252", "latin-1")


def leer_texto(ruta: Path) -> tuple[str, str]:
    """(texto, codificacion que funciono). Nunca lanza por codificacion."""
    crudo = ruta.read_bytes()
    for enc in CODIFICACIONES:
        try:
            t = crudo.decode(enc)
        except UnicodeDecodeError:
            continue
        # El BOM tambien puede venir en medio si alguien concatena archivos.
        return t.replace("﻿", ""), enc
    return crudo.decode("utf-8", errors="replace"), "utf-8 con reemplazos"


def leer(ruta: Path, columnas_de_la_persona: tuple[str, ...]) -> dict:
    """Las filas del formulario, mas lo que hizo falta para poder leerlo.

    `columnas_de_la_persona` son las que rellena quien anota. Se usan para dos
    cosas: decir cuantas filas vienen diligenciadas, y detectar el fallo 2 ---
    si NINGUNA de esas columnas existe en la cabecera, el archivo no se parseo
    como un formulario y hay que decirlo en vez de informar cero respuestas.
    """
    if str(ruta).lower().endswith(".xlsx"):
        filas, enc = _leer_xlsx(ruta), "xlsx"
    else:
        texto, enc = leer_texto(ruta)
        todas = texto.splitlines()

        # SE BUSCA LA CABECERA; NO SE FILTRAN LOS COMENTARIOS.
        #
        # Antes se quitaban las lineas que empiezan por `#`. Eso falla en
        # cuanto algo se cuela delante del primer `#`: un BOM lo hacia, y un
        # BOM reescrito a cp1252 se convierte en `?`, que ningun filtro de
        # comentarios va a reconocer. Buscar la fila que empieza por `id` y
        # tirar todo lo anterior no depende de con que byte empiece el
        # archivo, y es lo unico que de verdad define donde empieza la tabla.
        i = next((k for k, l in enumerate(todas)
                  if l.lstrip("﻿?# ").startswith("id")), None)
        lineas = todas[i:] if i is not None else [
            l for l in todas if not l.lstrip().startswith("#")]

        # El separador tambien se descubre: Excel en un Windows en espanol
        # guarda con `;` porque es el separador de lista del sistema, y un
        # CSV asi leido con comas da UNA columna con todo dentro --- lo que
        # haria que `mecanismo` no exista y pareciera un formulario vacio.
        cab = lineas[0] if lineas else ""
        sep = ";" if cab.count(";") > cab.count(",") else ","
        # La cabecera puede arrastrar basura delante (un `?` de un BOM mal
        # recodificado). Se limpia solo ahi, no en los datos.
        lineas = [lineas[0].lstrip("﻿?# ")] + lineas[1:]
        filas = list(csv.DictReader(lineas, delimiter=sep))
        if sep == ";":
            enc += " con separador ;"
    cabecera = list(filas[0].keys()) if filas else []

    faltan = [c for c in columnas_de_la_persona if c not in cabecera]
    diligenciadas = sum(
        1 for f in filas
        if any((f.get(c) or "").strip() for c in columnas_de_la_persona))

    return {
        "filas": filas,
        "codificacion": enc,
        "cabecera": cabecera,
        "columnas_que_faltan": faltan,
        "diligenciadas": diligenciadas,
        # SI FALTAN LAS COLUMNAS, EL ARCHIVO NO SE LEYO: NO ES QUE ESTE VACIO.
        "cabecera_valida": not faltan,
    }


def exigir(ruta: Path, columnas_de_la_persona: tuple[str, ...]) -> dict:
    """Como `leer`, pero se niega a seguir si la cabecera no es la del
    formulario. Devuelve el mismo dict; si no es valido, imprime por que.

    Se separa de `leer` para que el aviso se imprima UNA vez, desde el CLI, y
    `leer` siga siendo una funcion sin efectos que se pueda probar.
    """
    r = leer(ruta, columnas_de_la_persona)
    if not r["cabecera_valida"]:
        print("=" * 72)
        print(f"  NO SE PUDO LEER {ruta.name} COMO FORMULARIO")
        print("=" * 72)
        print(f"  Faltan las columnas: {', '.join(r['columnas_que_faltan'])}")
        print(f"  La cabecera que se encontro fue:")
        print(f"    {r['cabecera'][:4]}")
        print()
        print("  Casi siempre es esto: el archivo se guardo con BOM y la")
        print("  primera linea de instrucciones paso a ser la cabecera. Las")
        print("  respuestas SI estan en el archivo --- no se han perdido.")
        print()
        print("  Para arreglarlo: abrelo con un editor de texto (Notepad,")
        print("  VS Code), borra las lineas que empiezan por `#` y guarda.")
        print("  O vuelve a guardarlo desde Excel como `CSV UTF-8`.")
        print("=" * 72)
    elif r["codificacion"] not in ("utf-8", "utf-8-sig", "xlsx"):
        print(f"  aviso: {ruta.name} venia en {r['codificacion']}, no en "
              "utf-8. Se leyo bien, pero comprueba que los acentos de la "
              "columna `notas` salgan correctos en el artefacto.")
    return r


# --------------------------------------------------------------------------
# .xlsx · el formato que no se puede abrir mal
# --------------------------------------------------------------------------
# POR QUE SE OFRECE XLSX Y NO SOLO CSV
#
# Un CSV en UTF-8 abierto con doble clic en un Windows en espanol falla DOS
# veces a la vez, y las dos son invisibles para quien anota:
#
#   1. Excel lo decodifica con la pagina de codigos del sistema (1252), asi
#      que todos los acentos salen como simbolos raros. El relato se vuelve
#      ilegible --- y el relato es justo lo que hay que leer para anotar.
#   2. Excel parte las columnas por el SEPARADOR DE LISTA del sistema, que en
#      es-CO es `;`. Con un CSV de comas, las cinco columnas se meten en una.
#
# El BOM arregla (1) pero no (2). El separador `;` arregla (2) pero rompe la
# lectura estandar. Un `.xlsx` no tiene ninguno de los dos problemas porque no
# es texto delimitado: lleva su propia codificacion y sus propias celdas.
#
# Asi que se escriben los dos: el `.xlsx` para rellenar, y el `.csv` --- ahora
# con BOM --- para quien use Google Sheets, un editor de texto o `git diff`.

ANCHOS = {"id": 8, "relato": 90, "mecanismo": 22, "procede": 10, "notas": 34,
          "respuesta_del_sistema": 58, "respuesta_de_referencia": 58,
          "nota_humana": 12, "nota": 10, "comentario": 32, "caso": 62,
          "tipo": 13, "categoria": 26}

# Las columnas que llevan texto largo y necesitan `wrap_text`. Era una lista
# escrita dentro del bucle y se dejaba fuera `caso`, que es la mas larga de
# todas: 62 de ancho sin ajuste deja el relato cortado en una sola linea.
COLUMNAS_LARGAS = ("relato", "caso", "respuesta_del_sistema",
                   "respuesta_de_referencia", "notas")


def escribir_xlsx(ruta, instrucciones: list[str], cabecera: list[str],
                  filas: list[list], columnas_persona: tuple[str, ...],
                  opciones: dict[str, list[str]] | None = None,
                  congelar_columnas: int = 0) -> bool:
    """Escribe el formulario como .xlsx. Devuelve False si falta openpyxl.

    `opciones` pone un desplegable en esa columna. No es adorno: un
    `accion_popular` mal escrito se cuenta como desacuerdo, asi que la
    medicion sale peor por un error de teclado. Con lista cerrada no puede
    pasar.

    `congelar_columnas` deja fijas las N primeras columnas al desplazarse a
    la derecha. Hace falta cuando el formulario tiene columnas de texto largo:
    en `validacion_juez` el caso, la referencia y la respuesta sumaban 160 de
    ancho, asi que la columna donde hay que ESCRIBIR quedaba fuera de la
    pantalla y quien rellenaba tenia que buscarla veinticinco veces. Un
    formulario incomodo no mide peor el criterio de la persona: mide su
    paciencia con Excel.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Alignment, Font, PatternFill
        from openpyxl.utils import get_column_letter
        from openpyxl.worksheet.datavalidation import DataValidation
    except ImportError:
        return False

    wb = Workbook()
    ws = wb.active
    ws.title = "formulario"

    # Las instrucciones van arriba, en una sola columna, para que no se
    # confundan con datos. En el CSV son lineas `#`; aqui son filas de texto.
    for linea in instrucciones:
        t = linea.lstrip("#").strip()
        c = ws.cell(row=ws.max_row if ws.max_row > 1 or ws["A1"].value else 1,
                    column=1)
        if c.value is not None:
            c = ws.cell(row=ws.max_row + 1, column=1)
        c.value = t
        c.font = Font(bold=t.isupper() and len(t) > 3, size=10)
    fila_cab = ws.max_row + 2

    gris = PatternFill("solid", fgColor="EEEEEE")
    amarillo = PatternFill("solid", fgColor="FFF4CC")
    for j, nombre in enumerate(cabecera, start=1):
        c = ws.cell(row=fila_cab, column=j, value=nombre)
        c.font = Font(bold=True)
        c.fill = amarillo if nombre in columnas_persona else gris
        ws.column_dimensions[get_column_letter(j)].width = ANCHOS.get(nombre, 20)

    for i, fila in enumerate(filas, start=fila_cab + 1):
        for j, v in enumerate(fila, start=1):
            c = ws.cell(row=i, column=j, value=v)
            if cabecera[j - 1] in COLUMNAS_LARGAS:
                c.alignment = Alignment(wrap_text=True, vertical="top")
            elif cabecera[j - 1] in columnas_persona:
                c.fill = amarillo
                c.alignment = Alignment(horizontal="center", vertical="top")

    for col, vals in (opciones or {}).items():
        if col not in cabecera:
            continue
        j = get_column_letter(cabecera.index(col) + 1)
        dv = DataValidation(type="list", formula1='"' + ",".join(vals) + '"',
                            allow_blank=True, showDropDown=False)
        dv.error = "Use una de las opciones de la lista."
        dv.errorTitle = "Valor no permitido"
        ws.add_data_validation(dv)
        dv.add(f"{j}{fila_cab + 1}:{j}{fila_cab + len(filas)}")

    ws.freeze_panes = ws.cell(row=fila_cab + 1,
                              column=congelar_columnas + 1)
    wb.save(str(ruta))
    return True


def _leer_xlsx(ruta) -> list[dict]:
    """Las filas de un .xlsx, saltando las instrucciones de arriba.

    La cabecera es la primera fila cuya primera celda vale `id`: las filas de
    instrucciones no la tienen, asi que no hace falta contarlas.
    """
    from openpyxl import load_workbook
    ws = load_workbook(str(ruta), data_only=True).active
    cab, out = None, []
    for fila in ws.iter_rows(values_only=True):
        vals = ["" if v is None else str(v).strip() for v in fila]
        if cab is None:
            if vals and vals[0] == "id":
                cab = vals
            continue
        if not vals or not vals[0]:
            continue
        out.append({k: v for k, v in zip(cab, vals) if k})
    return out
