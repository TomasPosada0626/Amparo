"""
Calculadora de términos procesales colombianos.

Es la herramienta externa del sistema (criterio 3 de M3). Existe porque un LLM
no sabe contar días hábiles: tiene que saber que el 20 de julio es festivo, que
el 6 de enero se corre al lunes siguiente por la Ley 51 de 1983, y que el Corpus
Christi depende de la Pascua, que a su vez depende del calendario lunar.

Un plazo mal contado cambia la respuesta jurídica —una petición vencida hace
procedente la tutela y una no vencida no— y el error es invisible: el modelo
diría "ya venció el término" con la misma seguridad en los dos casos.

CUÁNDO SE INVOCA
    El sistema la llama cuando concurren dos condiciones:
      (a) el relato contiene una fecha o una duración ("hace dos meses",
          "radiqué el 3 de marzo"), y
      (b) el mecanismo en juego tiene un término legal asociado: derecho de
          petición, fallo de tutela, impugnación o cumplimiento.
    Si falta cualquiera de las dos, no se invoca: no hay nada que contar.

QUÉ HACE SI FALLA
    Nunca adivina. Si la fecha no se puede interpretar, si queda en el futuro o
    si el tipo de término no existe, devuelve `calculable: False` con el motivo
    escrito, y el sistema debe decir "no fue posible calcular el término" en vez
    de afirmar un vencimiento que no verificó. Un plazo inventado es peor que
    ningún plazo.
"""
from __future__ import annotations
import re
from datetime import date, timedelta

# --------------------------------------------------------------------------
# Términos legales del dominio, con su fundamento
# --------------------------------------------------------------------------
TERMINOS = {
    "peticion_general": {
        "dias": 15, "habiles": True,
        "fundamento": "art. 14 Ley 1755 de 2015",
        "descripcion": "término general para resolver una petición"},
    "peticion_documentos": {
        "dias": 10, "habiles": True,
        "fundamento": "art. 14.1 Ley 1755 de 2015",
        "descripcion": "peticiones de documentos e información"},
    "peticion_consulta": {
        "dias": 30, "habiles": True,
        "fundamento": "art. 14.2 Ley 1755 de 2015",
        "descripcion": "consultas a las autoridades"},
    "fallo_tutela": {
        "dias": 10, "habiles": True,
        "fundamento": "art. 86 CP y art. 29 Decreto 2591 de 1991",
        "descripcion": "plazo máximo para que el juez dicte el fallo"},
    "impugnacion": {
        "dias": 3, "habiles": True,
        "fundamento": "art. 31 Decreto 2591 de 1991",
        "descripcion": "plazo para impugnar el fallo desde su notificación"},
    "cumplimiento": {
        "dias": 2, "habiles": False,
        "fundamento": "art. 27 Decreto 2591 de 1991",
        "descripcion": "48 horas tras las cuales el juez requiere al superior"},
    "renuencia_cumplimiento": {
        "dias": 10, "habiles": True,
        "fundamento": "art. 8 Ley 393 de 1997",
        "descripcion": "plazo para constituir la renuencia antes de la acción de cumplimiento"},
}


# --------------------------------------------------------------------------
# Festivos colombianos
# --------------------------------------------------------------------------
def pascua(anio: int) -> date:
    """Domingo de Resurrección (algoritmo gregoriano anónimo)."""
    a = anio % 19
    b, c = divmod(anio, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = divmod(h + l - 7 * m + 114, 31)
    return date(anio, mes, dia + 1)


def _lunes_siguiente(d: date) -> date:
    """Ley 51 de 1983 ('Emiliani'): el festivo se traslada al lunes siguiente.
    Si ya cae lunes, se queda."""
    return d + timedelta(days=(7 - d.weekday()) % 7)


def festivos(anio: int) -> dict[date, str]:
    """Los 18 festivos colombianos del año, con su nombre."""
    p = pascua(anio)
    fijos = {
        date(anio, 1, 1): "Año Nuevo",
        date(anio, 5, 1): "Día del Trabajo",
        date(anio, 7, 20): "Independencia",
        date(anio, 8, 7): "Batalla de Boyacá",
        date(anio, 12, 8): "Inmaculada Concepción",
        date(anio, 12, 25): "Navidad",
    }
    trasladables = {
        date(anio, 1, 6): "Reyes Magos",
        date(anio, 3, 19): "San José",
        date(anio, 6, 29): "San Pedro y San Pablo",
        date(anio, 8, 15): "Asunción",
        date(anio, 10, 12): "Día de la Raza",
        date(anio, 11, 1): "Todos los Santos",
        date(anio, 11, 11): "Independencia de Cartagena",
    }
    pascuales_fijos = {
        p - timedelta(days=3): "Jueves Santo",
        p - timedelta(days=2): "Viernes Santo",
    }
    pascuales_trasladados = {
        p + timedelta(days=43): "Ascensión del Señor",
        p + timedelta(days=64): "Corpus Christi",
        p + timedelta(days=71): "Sagrado Corazón",
    }

    # Dos festivos pueden caer el mismo día: en 2025 San Pedro (29 de junio,
    # domingo, se corre al 30) coincide con el Sagrado Corazón (Pascua + 71 =
    # 30 de junio). Colombia no desdobla el festivo, así que ese año tiene 17
    # fechas y no 18. Los nombres se acumulan en vez de pisarse: un festivo que
    # desaparece en silencio del calendario desplaza todos los términos.
    out: dict[date, str] = {}

    def poner(d: date, nombre: str) -> None:
        out[d] = f"{out[d]} / {nombre}" if d in out else nombre

    for grupo in (fijos, pascuales_fijos, pascuales_trasladados):
        for d, nombre in grupo.items():
            poner(d, nombre)
    for d, nombre in trasladables.items():
        poner(_lunes_siguiente(d), nombre)
    return out


def es_habil(d: date) -> bool:
    return d.weekday() < 5 and d not in festivos(d.year)


def sumar_habiles(desde: date, n: int) -> date:
    """n días hábiles a partir del día SIGUIENTE a `desde`.

    El día de radicación no cuenta: los términos se cuentan a partir del día
    siguiente, que es la regla general de cómputo.
    """
    d, restantes = desde, n
    while restantes > 0:
        d += timedelta(days=1)
        if es_habil(d):
            restantes -= 1
    return d


def contar_habiles(desde: date, hasta: date) -> int:
    """Días hábiles transcurridos entre dos fechas, sin contar el primero."""
    if hasta < desde:
        return 0
    n, d = 0, desde
    while d < hasta:
        d += timedelta(days=1)
        if es_habil(d):
            n += 1
    return n


# --------------------------------------------------------------------------
# Lectura de fechas en lenguaje natural
# --------------------------------------------------------------------------
MESES = {m: i for i, m in enumerate(
    ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
     "septiembre", "octubre", "noviembre", "diciembre"], 1)}
MESES["setiembre"] = 9


def leer_fecha(texto: str, hoy: date | None = None) -> date | None:
    """Extrae una fecha de un relato. Devuelve None si no hay ninguna legible.

    Reconoce tres formas: '3 de marzo de 2025', '03/03/2025' y expresiones
    relativas como 'hace dos meses'. Deliberadamente NO adivina: si no encaja
    en ninguna, devuelve None y el sistema reporta que no pudo calcular.
    """
    hoy = hoy or date.today()
    t = texto.lower()

    m = re.search(r"(\d{1,2})\s+de\s+([a-záéíóú]+)(?:\s+de\s+(\d{4}))?", t)
    if m and m.group(2) in MESES:
        dia, mes = int(m.group(1)), MESES[m.group(2)]
        anio = int(m.group(3)) if m.group(3) else hoy.year
        try:
            f = date(anio, mes, dia)
            return f if f <= hoy else date(anio - 1, mes, dia)
        except ValueError:
            return None

    m = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", t)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None

    NUM = {"un": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
           "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11,
           "doce": 12, "quince": 15, "veinte": 20, "treinta": 30}
    m = re.search(r"hace\s+(\w+)\s+(d[íi]as?|semanas?|meses?|a[ñn]os?)", t)
    if m:
        bruto = m.group(1)
        n = int(bruto) if bruto.isdigit() else NUM.get(bruto)
        if n is None:
            return None
        u = m.group(2)
        dias = n * (1 if u.startswith("d") else 7 if u.startswith("s")
                    else 30 if u.startswith("mes") else 365)
        return hoy - timedelta(days=dias)

    return None


# --------------------------------------------------------------------------
# La herramienta
# --------------------------------------------------------------------------
def calcular_termino(tipo: str, fecha: str | date | None = None,
                     relato: str | None = None, hoy: date | None = None) -> dict:
    """Calcula si un término legal ya venció.

    `fecha` puede ser una fecha concreta o `None`, en cuyo caso se intenta leer
    del `relato`. Devuelve siempre un dict con `calculable`, y cuando es False
    el campo `motivo` dice por qué, para que el sistema lo reporte en vez de
    inventar un vencimiento.
    """
    hoy = hoy or date.today()

    if tipo not in TERMINOS:
        return {"calculable": False,
                "motivo": f"tipo de término desconocido: '{tipo}'. Disponibles: {sorted(TERMINOS)}"}
    cfg = TERMINOS[tipo]

    if isinstance(fecha, str):
        fecha = leer_fecha(fecha, hoy)
    if fecha is None and relato:
        fecha = leer_fecha(relato, hoy)
    if fecha is None:
        return {"calculable": False, "tipo": tipo, "fundamento": cfg["fundamento"],
                "motivo": "no se encontró una fecha legible en el relato"}
    if fecha > hoy:
        return {"calculable": False, "tipo": tipo, "fundamento": cfg["fundamento"],
                "motivo": f"la fecha leída ({fecha.isoformat()}) está en el futuro"}

    if cfg["habiles"]:
        vence = sumar_habiles(fecha, cfg["dias"])
        transcurridos = contar_habiles(fecha, hoy)
        unidad = "hábiles"
    else:
        vence = fecha + timedelta(days=cfg["dias"])
        transcurridos = (hoy - fecha).days
        unidad = "calendario"

    return {
        "calculable": True,
        "tipo": tipo,
        "descripcion": cfg["descripcion"],
        "fundamento": cfg["fundamento"],
        "fecha_inicio": fecha.isoformat(),
        "dias_termino": cfg["dias"],
        "unidad": unidad,
        "fecha_vencimiento": vence.isoformat(),
        "dias_transcurridos": transcurridos,
        "vencido": hoy > vence,
        "dias_de_exceso": max(0, (hoy - vence).days) if hoy > vence else 0,
        "resumen": (
            f"El término de {cfg['dias']} días {unidad} ({cfg['fundamento']}) "
            f"inició el {fecha.isoformat()} y vencía el {vence.isoformat()}. "
            + (f"Está vencido hace {(hoy - vence).days} días calendario."
               if hoy > vence else "Aún no ha vencido.")),
    }


# --------------------------------------------------------------------------
# Definición para tool calling
# --------------------------------------------------------------------------
ESQUEMA_TOOL = {
    "type": "function",
    "function": {
        "name": "calcular_termino",
        # LA DESCRIPCION SE LEE ANTES DEL PROMPT, asi que tenia que decir lo
        # mismo. Decia «Invocala SOLO si...» y pedia «una fecha o una
        # duracion»: medido, 5 de los 10 casos elegibles no la llamaron y
        # cuatro de los cinco traian la fecha en relativo ---«hace cuatro
        # dias», «hace dos meses»---, que `leer_fecha` resuelve sin problema.
        # El quinto traia dos fechas explicitas y la entidad ya habia
        # respondido, que es el caso en el que mas falta hace.
        "description": (
            "Calcula si un término legal colombiano ya venció, contando días hábiles "
            "con los festivos del país. Invócala cuando el relato diga CUÁNDO pasó "
            "algo y haya un término legal en juego (petición, fallo de tutela, "
            "impugnación, cumplimiento). Una duración relativa sirve igual que una "
            "fecha: «hace cuatro días», «hace dos meses» y «el 3 de marzo de 2026» "
            "se resuelven las tres. Y el término sigue en juego aunque la entidad ya "
            "haya respondido: si respondió dentro del plazo o fuera de él es "
            "precisamente lo que esto decide. No la uses para estimar nada más."),
        "parameters": {
            "type": "object",
            "properties": {
                "tipo": {"type": "string", "enum": sorted(TERMINOS),
                         "description": "qué término se quiere calcular"},
                "relato": {"type": "string",
                           "description": "el texto donde aparece la fecha de inicio"},
            },
            "required": ["tipo", "relato"],
        },
    },
}
