"""T3 · Genera los documentos sintéticos del eval set de M4 (m4/eval_set/imagenes/).

Por qué un script y no imágenes sueltas: TODO el texto de los documentos está
aquí, a la vista. Cualquiera puede revisar que no hay nombres, cédulas,
firmas ni sellos reales (ver imagenes/ANONIMIZACION.md).

Los PNG/JPG que están en el repo son la versión CONGELADA del eval set: el
`esperado` de casos_m4.csv se escribió contra ellos. Volver a correr este
script en otra máquina puede cambiar detalles de píxeles (fuentes distintas),
así que no se regeneran después de haber corrido el sistema.

Uso (desde la raíz del repo, sin GPU):
    python m4/eval_set/generar_imagenes.py
"""
from __future__ import annotations

import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SALIDA = Path(__file__).resolve().parent / "imagenes"
W, H = 1100, 1430          # proporción carta; ~2.000 tokens visuales en Qwen2-VL
MARGEN = 90
PAPEL = (252, 251, 247)
TINTA = (25, 25, 30)
ROJO = (190, 20, 30)

ETIQUETA_1 = "DOCUMENTO SINTÉTICO / GENERADO"
ETIQUETA_2 = ("Entidad, personas y datos ficticios · Uso académico (SI4006 · M4 · Amparo) "
              "· Sin validez jurídica")


# --------------------------------------------------------------------------
# Fuentes: DejaVu del sistema o, si no está, la que trae matplotlib
# --------------------------------------------------------------------------
def _ruta_fuente(nombre: str) -> str:
    candidatos = [Path("/usr/share/fonts/truetype/dejavu") / nombre]
    try:
        import matplotlib
        candidatos.append(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / nombre)
    except ImportError:
        pass
    for c in candidatos:
        if c.is_file():
            return str(c)
    raise FileNotFoundError(f"No encuentro la fuente {nombre}. Instala fonts-dejavu o matplotlib.")


def F(estilo: str, tam: int) -> ImageFont.FreeTypeFont:
    nombres = {"serif": "DejaVuSerif.ttf", "serif_b": "DejaVuSerif-Bold.ttf",
               "sans": "DejaVuSans.ttf", "sans_b": "DejaVuSans-Bold.ttf"}
    return ImageFont.truetype(_ruta_fuente(nombres[estilo]), tam)


# --------------------------------------------------------------------------
# Una página con cursor vertical
# --------------------------------------------------------------------------
MANCHA = "[[MANCHA]]"   # marcador: hueco donde va la mancha de tinta (nada debajo)


class Pagina:
    def __init__(self):
        self.img = Image.new("RGB", (W, H), PAPEL)
        self.d = ImageDraw.Draw(self.img)
        self.y = 70
        self.huecos: list[tuple[int, int, int, int]] = []
        self.parrafos: list[tuple[int, int]] = []   # (y0, y1) de cada párrafo del cuerpo

    def texto(self, s: str, fuente, *, alinear="izq", color=TINTA, salto=8):
        ancho = fuente.getlength(s)
        x = {"izq": MARGEN, "der": W - MARGEN - ancho, "centro": (W - ancho) / 2}[alinear]
        self.d.text((x, self.y), s, font=fuente, fill=color)
        self.y += fuente.size + salto

    def lineas(self, bloque: str, fuente, **kw):
        for linea in bloque.split("\n"):
            self.texto(linea, fuente, **kw)

    def regla(self, grosor=2, salto=18):
        self.d.line([(MARGEN, self.y), (W - MARGEN, self.y)], fill=TINTA, width=grosor)
        self.y += salto

    def espacio(self, px: int):
        self.y += px

    def parrafo(self, s: str, fuente, *, interlinea=1.45, sangria=0):
        """Texto justificado a la izquierda con ajuste por píxeles."""
        y0 = self.y
        ancho_max = W - 2 * MARGEN
        esp = fuente.getlength(" ")
        hueco = fuente.getlength("00000")
        palabras = s.split()
        linea: list[str] = []
        ancho = sangria

        def largo(p):
            return hueco if p == MANCHA else fuente.getlength(p)

        def dibujar(ps, x0):
            x = MARGEN + x0
            for p in ps:
                if p == MANCHA:
                    self.huecos.append((int(x), int(self.y), int(x + hueco), int(self.y + fuente.size)))
                else:
                    self.d.text((x, self.y), p, font=fuente, fill=TINTA)
                x += largo(p) + esp
            self.y += int(fuente.size * interlinea)

        x0 = sangria
        for p in palabras:
            extra = largo(p) + (esp if linea else 0)
            if linea and ancho + extra > ancho_max:
                dibujar(linea, x0)
                linea, ancho, x0 = [], 0, 0
                extra = largo(p)
            linea.append(p)
            ancho += extra
        if linea:
            dibujar(linea, x0)
        self.y += 10
        self.parrafos.append((y0, self.y))

    def pie_sintetico(self):
        """La etiqueta visible que exige el curso para lo generado."""
        alto = 92
        y0 = H - alto - 40
        self.d.rectangle([MARGEN - 10, y0, W - MARGEN + 10, y0 + alto], outline=ROJO, width=4)
        f1, f2 = F("sans_b", 26), F("sans", 17)
        self.d.text(((W - f1.getlength(ETIQUETA_1)) / 2, y0 + 14), ETIQUETA_1, font=f1, fill=ROJO)
        self.d.text(((W - f2.getlength(ETIQUETA_2)) / 2, y0 + 56), ETIQUETA_2, font=f2, fill=ROJO)


def encabezado(p: Pagina, entidad: str, dependencia: str, pie_entidad: str):
    tam = 34
    while F("sans_b", tam).getlength(entidad) > W - 2 * MARGEN:   # nombres largos: que quepan
        tam -= 1
    p.texto(entidad, F("sans_b", tam), alinear="centro", salto=10 + 34 - tam)
    p.texto(dependencia, F("sans", 22), alinear="centro", salto=6)
    p.texto(pie_entidad, F("sans", 17), alinear="centro", color=(80, 80, 80), salto=14)
    p.regla(grosor=3, salto=28)


CUERPO = 25        # tamaño del texto del cuerpo
CUERPO_B = 25


# --------------------------------------------------------------------------
# Efectos de "foto": la hoja sobre una mesa, girada, con luz despareja
# --------------------------------------------------------------------------
def foto(pagina: Image.Image, *, angulo: float, desenfoque: float, ruido: float,
         sombra: float, semilla: int) -> Image.Image:
    rng = np.random.default_rng(semilla)
    mesa = Image.new("RGB", (W + 160, H + 160), (92, 72, 55))
    # textura leve de la mesa
    m = np.asarray(mesa).astype(np.float32)
    m += rng.normal(0, 6, m.shape[:2])[..., None]
    mesa = Image.fromarray(np.clip(m, 0, 255).astype(np.uint8))

    hoja = pagina.convert("RGBA").rotate(angulo, resample=Image.BICUBIC, expand=True)
    x = (mesa.width - hoja.width) // 2
    y = (mesa.height - hoja.height) // 2
    mesa.paste(hoja, (x, y), hoja)

    a = np.asarray(mesa).astype(np.float32)
    # luz despareja: más oscuro abajo a la derecha
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    grad = 1.0 - sombra * ((xx / a.shape[1]) * 0.6 + (yy / a.shape[0]) * 0.4)
    a *= grad[..., None]
    a += rng.normal(0, ruido, a.shape)
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    if desenfoque:
        out = out.filter(ImageFilter.GaussianBlur(desenfoque))
    return out.resize((W, int(W * out.height / out.width)), Image.LANCZOS)


def franja_etiqueta(img: Image.Image) -> Image.Image:
    """Etiqueta nítida añadida DEBAJO de la foto: sigue visible aunque la
    hoja esté borrosa (doc06)."""
    alto = 70
    out = Image.new("RGB", (img.width, img.height + alto), (255, 255, 255))
    out.paste(img, (0, 0))
    d = ImageDraw.Draw(out)
    d.rectangle([0, img.height, img.width, img.height + alto], fill=ROJO)
    f1 = F("sans_b", 24)
    s = ETIQUETA_1 + " · fotografía simulada · datos ficticios"
    d.text(((img.width - f1.getlength(s)) / 2, img.height + 20), s, font=f1, fill=(255, 255, 255))
    return out


# --------------------------------------------------------------------------
# Los seis documentos
# --------------------------------------------------------------------------
def doc01_respuesta_eps() -> Image.Image:
    p = Pagina()
    encabezado(p, "EPS SALUD SERENA S.A.S.", "Dirección de Autorizaciones · EPS Salud Serena",
               "NIT 000.000.000-0 · Calle 00 # 00-00 · Puerto Almendro")
    p.texto("Puerto Almendro, 5 de octubre de 2026", F("serif", CUERPO), alinear="der", salto=6)
    p.texto("Radicado: SS-AUT-0193", F("serif", 21), alinear="der", salto=30)
    p.texto("RESPUESTA A DERECHO DE PETICIÓN", F("serif_b", 30), alinear="centro", salto=30)
    p.lineas("Señor(a)\nCIUDADANO DE PRUEBA 01\nC.C. 00.000.000\nCalle 00 # 00-00, Puerto Almendro",
             F("serif", CUERPO), salto=6)
    p.espacio(18)
    p.parrafo("Asunto: Respuesta a su petición de autorización de un procedimiento quirúrgico.",
              F("serif_b", CUERPO_B))
    p.parrafo("Respetado(a) afiliado(a):", F("serif", CUERPO))
    p.parrafo("En atención a su petición, en la que solicita la autorización del procedimiento "
              "REEMPLAZO TOTAL DE CADERA DERECHA, ordenado por su médico tratante, especialista "
              "en ortopedia, le informamos lo siguiente:", F("serif", CUERPO))
    p.parrafo("La EPS NIEGA la autorización del procedimiento solicitado, porque no se encuentra "
              "contratado con ningún prestador de la red de servicios de su municipio de residencia.",
              F("serif", CUERPO))
    p.parrafo("Le sugerimos consultar nuevamente cuando la red de prestadores sea actualizada.",
              F("serif", CUERPO))
    p.espacio(10)
    p.lineas("Atentamente,\n\nCoordinación de Autorizaciones\nEPS Salud Serena S.A.S.",
             F("serif", CUERPO), salto=6)
    p.pie_sintetico()
    return p.img


def doc02_oficio_planeacion() -> Image.Image:
    p = Pagina()
    encabezado(p, "ALCALDÍA DE PUERTO ALMENDRO",
               "Secretaría de Planeación Municipal de Puerto Almendro",
               "Centro Administrativo Municipal · Calle 00 # 00-00")
    p.texto("Puerto Almendro, 12 de agosto de 2026", F("serif", CUERPO), alinear="der", salto=30)
    p.texto("OFICIO No. SPM-0412", F("serif_b", 30), alinear="centro", salto=30)
    p.lineas("Señor(a)\nCIUDADANO DE PRUEBA 02\nPropietario(a) del inmueble de la Carrera 00 # 00-00\n"
             "Puerto Almendro", F("serif", CUERPO), salto=6)
    p.espacio(18)
    p.parrafo("Asunto: Requerimiento por obra de construcción sin licencia.", F("serif_b", CUERPO_B))
    p.parrafo("En visita de control urbano, esta Secretaría constató que en el inmueble de su "
              "propiedad se adelanta una obra de ampliación sin que obre en el expediente la "
              "licencia de construcción correspondiente.", F("serif", CUERPO))
    p.parrafo("Por lo anterior, se le REQUIERE para que, dentro de los quince (15) días hábiles "
              "siguientes al recibo del presente oficio, presente ante esta Secretaría la licencia "
              "de construcción de la obra.", F("serif", CUERPO))
    p.parrafo("Si no la presenta dentro de ese plazo, se dará traslado a la Inspección de Policía "
              "para lo de su competencia.", F("serif", CUERPO))
    p.espacio(10)
    p.lineas("Atentamente,\n\nSecretaría de Planeación Municipal\nAlcaldía de Puerto Almendro",
             F("serif", CUERPO), salto=6)
    p.pie_sintetico()
    return p.img


def doc03_respuesta_cumplimiento() -> Image.Image:
    p = Pagina()
    encabezado(p, "ALCALDÍA DE PUERTO ALMENDRO", "Secretaría General de Puerto Almendro",
               "Centro Administrativo Municipal · Calle 00 # 00-00")
    p.texto("Puerto Almendro, 21 de septiembre de 2026", F("serif", CUERPO), alinear="der", salto=6)
    p.texto("Radicado: SG-0987", F("serif", 21), alinear="der", salto=30)
    p.texto("RESPUESTA A DERECHO DE PETICIÓN", F("serif_b", 30), alinear="centro", salto=30)
    p.lineas("Señor(a)\nCIUDADANO DE PRUEBA 03\nCalle 00 # 00-00, Puerto Almendro",
             F("serif", CUERPO), salto=6)
    p.espacio(18)
    p.parrafo("Asunto: Respuesta a su solicitud de cumplimiento del deber de publicar los contratos "
              "del municipio.", F("serif_b", CUERPO_B))
    p.parrafo("Usted solicitó, en ejercicio del derecho de petición, que la Alcaldía cumpla lo "
              "ordenado en el artículo 10 de la Ley 1712 de 2014 y publique en el Sistema "
              "Electrónico de Contratación Pública (SECOP) los contratos celebrados por el "
              "municipio durante 2025 y 2026, y advirtió que, de no hacerlo, acudiría a la "
              "acción judicial correspondiente.", F("serif", CUERPO))
    p.parrafo("Le informamos que, por ahora, la Administración NO realizará la publicación de los "
              "contratos solicitada, debido a que la entidad se encuentra en un proceso de "
              "actualización tecnológica, sin fecha estimada de terminación.", F("serif", CUERPO))
    p.espacio(10)
    p.lineas("Atentamente,\n\nSecretaría General\nAlcaldía de Puerto Almendro", F("serif", CUERPO), salto=6)
    p.pie_sintetico()
    return p.img


def doc04_respuesta_car() -> Image.Image:
    p = Pagina()
    encabezado(p, "CORPORACIÓN AUTÓNOMA REGIONAL DEL RÍO CLARO",
               "CORPORIOCLARO · Subdirección de Gestión Ambiental",
               "Sede regional · Carrera 00 # 00-00 · Villa Serena")
    p.texto("Villa Serena, 30 de septiembre de 2026", F("serif", CUERPO), alinear="der", salto=6)
    p.texto("Radicado: CRCL-2231", F("serif", 21), alinear="der", salto=30)
    p.texto("RESPUESTA A DERECHO DE PETICIÓN", F("serif_b", 30), alinear="centro", salto=30)
    p.lineas("Señores\nJUNTA DE ACCIÓN COMUNAL DE LA VEREDA LOS NARANJOS\nVilla Serena",
             F("serif", CUERPO), salto=6)
    p.espacio(18)
    p.parrafo("Asunto: Respuesta a la queja por vertimientos en la quebrada La Clara.",
              F("serif_b", CUERPO_B))
    p.parrafo("En atención a la queja presentada por ustedes, en representación de los habitantes "
              "de las veredas Los Naranjos, La Loma, San Pablo y Alto Bonito, sobre los "
              "vertimientos de aguas residuales de una curtiembre a la quebrada La Clara, fuente "
              "que abastece el acueducto veredal, la Corporación realizó una visita técnica al sector.",
              F("serif", CUERPO))
    p.parrafo("Les informamos que la Corporación NO adoptará medidas preventivas en esta oportunidad "
              "y ordena el ARCHIVO de la queja.", F("serif", CUERPO))
    p.espacio(10)
    p.lineas("Atentamente,\n\nSubdirección de Gestión Ambiental\n"
             "Corporación Autónoma Regional del Río Claro", F("serif", CUERPO), salto=6)
    p.pie_sintetico()
    return p.img


def doc05_notificacion_acueducto() -> Image.Image:
    p = Pagina()
    encabezado(p, "AGUAS DE VILLA SERENA S.A. E.S.P.",
               "Empresa de acueducto y alcantarillado de Villa Serena",
               "Oficina comercial · Calle 00 # 00-00 · Villa Serena")
    p.texto("Villa Serena, 2 de octubre de 2026", F("serif", CUERPO), alinear="der", salto=30)
    p.texto("NOTIFICACIÓN DE SUSPENSIÓN DEL SERVICIO", F("serif_b", 29), alinear="centro", salto=30)
    p.lineas("Suscriptor: CIUDADANO DE PRUEBA 04\nCuenta contrato: 000000\n"
             "Dirección del predio: Carrera 00 # 00-00, Villa Serena", F("serif", CUERPO), salto=6)
    p.espacio(18)
    p.parrafo("Le notificamos que su cuenta presenta saldo vencido por el servicio de acueducto.",
              F("serif", CUERPO))
    p.parrafo("Si dentro de los cinco (5) días hábiles siguientes al recibo de esta notificación "
              "usted no cancela el saldo pendiente o no suscribe un acuerdo de pago, la empresa "
              "procederá a la SUSPENSIÓN del servicio de acueducto en el predio.", F("serif", CUERPO))
    p.parrafo("Para acuerdos de pago, acérquese a la oficina comercial.", F("serif", CUERPO))
    p.espacio(10)
    p.lineas("Atentamente,\n\nGerencia Comercial\nAguas de Villa Serena S.A. E.S.P.",
             F("serif", CUERPO), salto=6)
    p.pie_sintetico()
    # Foto tomada con el celular, pero legible: el caso NO es adversarial.
    return foto(p.img, angulo=1.6, desenfoque=0.6, ruido=4, sombra=0.18, semilla=5)


def doc06_notificacion_borrosa() -> Image.Image:
    """ADVERSARIAL. La fecha y el plazo NO están en la imagen:
      - la fecha nunca se dibuja: la esquina superior derecha, donde iría,
        está arrancada;
      - el número del plazo nunca se dibuja: en su lugar hay una mancha de
        tinta, y el párrafo está mojado y borroso.
    Así el `esperado` (fecha|plazo_dias en null) es verdad por construcción:
    no hay un dato real escondido que un VLM muy bueno pudiera recuperar.
    Tampoco hay otro número ni otra fecha en todo el documento.
    """
    p = Pagina()
    encabezado(p, "INSPECCIÓN MUNICIPAL DE POLICÍA", "Inspección de Policía de Villa Serena",
               "Despacho de convivencia ciudadana · Villa Serena")
    p.texto("Villa Serena,", F("serif", CUERPO), alinear="der", salto=30)   # sin fecha
    p.texto("NOTIFICACIÓN POR AVISO", F("serif_b", 30), alinear="centro", salto=30)
    p.lineas("Señor(a)\nCIUDADANO DE PRUEBA 05\nBarrio Centro, Villa Serena", F("serif", CUERPO), salto=6)
    p.espacio(18)
    p.parrafo("Asunto: Aviso de procedimiento por comportamiento contrario a la convivencia.",
              F("serif_b", CUERPO_B))
    p.parrafo("Por medio del presente aviso se le notifica que en su contra se adelanta un "
              "procedimiento por comportamiento contrario a la convivencia, por ruido en horario "
              "nocturno.", F("serif", CUERPO))
    p.parrafo(f"Usted cuenta con un plazo de {MANCHA} días hábiles, contados a partir del recibo "
              "de este aviso, para presentar sus descargos y las pruebas que pretenda hacer valer "
              "ante este despacho.", F("serif", CUERPO))
    p.parrafo("Vencido ese término sin que se presente, se continuará con el trámite.", F("serif", CUERPO))
    p.espacio(10)
    p.lineas("Atentamente,\n\nInspección Municipal de Policía de Villa Serena", F("serif", CUERPO), salto=6)
    p.pie_sintetico()

    img = p.img
    rng = random.Random(6)
    d = ImageDraw.Draw(img, "RGBA")

    # 1) Mancha de tinta sobre el hueco del plazo (debajo no hay nada escrito).
    for (x0, y0, x1, y1) in p.huecos:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        for _ in range(55):
            r = rng.uniform(12, 26)
            ox, oy = rng.gauss(0, 12), rng.gauss(0, 6)
            d.ellipse([cx + ox - r, cy + oy - r * 0.8, cx + ox + r, cy + oy + r * 0.8],
                      fill=(30, 22, 40, 235))

    # 2) Agua: el cuerpo del texto queda borroso y con un aureola café.
    cuerpo_y0 = p.parrafos[1][0] - 6
    cuerpo_y1 = p.parrafos[-1][1] + 4
    zona = (MARGEN - 20, cuerpo_y0, W - MARGEN + 20, cuerpo_y1)
    img.paste(img.crop(zona).filter(ImageFilter.GaussianBlur(2.6)), zona[:2])
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dc = ImageDraw.Draw(capa)
    for i in range(7):
        r = 330 - i * 30
        dc.ellipse([560 - r, (cuerpo_y0 + cuerpo_y1) / 2 - r * 0.75,
                    560 + r, (cuerpo_y0 + cuerpo_y1) / 2 + r * 0.75],
                   outline=(150, 110, 60, 70), width=10)
    capa = capa.filter(ImageFilter.GaussianBlur(6))
    img = Image.alpha_composite(img.convert("RGBA"), capa).convert("RGB")

    # 3) Esquina superior derecha arrancada (donde iría la fecha).
    mascara = Image.new("L", img.size, 255)
    dm = ImageDraw.Draw(mascara)
    puntos = [(W, 0), (520, 0)]
    x, y = 520, 0
    while x < W:
        x += rng.uniform(25, 55)
        y += rng.uniform(18, 40)
        puntos.append((min(x, W), y + rng.uniform(-10, 10)))
    puntos.append((W, y))
    dm.polygon(puntos, fill=0)
    hoja = img.convert("RGBA")
    hoja.putalpha(mascara)

    # 4) Foto oscura, girada y movida.
    mesa = Image.new("RGBA", hoja.size, (0, 0, 0, 0))
    mesa.alpha_composite(hoja)
    rgba_a_rgb = Image.new("RGB", hoja.size, (92, 72, 55))
    rgba_a_rgb.paste(mesa, (0, 0), mesa)
    out = foto(rgba_a_rgb, angulo=-4.5, desenfoque=1.4, ruido=10, sombra=0.42, semilla=6)
    return franja_etiqueta(out)


DOCUMENTOS = {
    "doc01_respuesta_eps.png": doc01_respuesta_eps,
    "doc02_oficio_planeacion.png": doc02_oficio_planeacion,
    "doc03_respuesta_cumplimiento.png": doc03_respuesta_cumplimiento,
    "doc04_respuesta_car.png": doc04_respuesta_car,
    "doc05_notificacion_acueducto.jpg": doc05_notificacion_acueducto,
    "doc06_notificacion_borrosa.jpg": doc06_notificacion_borrosa,   # adversarial
}


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    for nombre, fn in DOCUMENTOS.items():
        img = fn()
        ruta = SALIDA / nombre
        if nombre.startswith("doc06"):
            img.save(ruta, quality=55)   # foto de celular mala y muy comprimida
        elif ruta.suffix == ".jpg":
            img.save(ruta, quality=88)   # foto de celular legible
        else:
            img.save(ruta, optimize=True)
        print(f"{ruta.name:38s} {img.size[0]}x{img.size[1]}")


if __name__ == "__main__":
    main()
