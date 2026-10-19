"""
Autoprueba del agente: ejercita las cinco fallas con un cliente guionado.

POR QUE ASI Y NO CON EVIDENCIA DE LAS CORRIDAS
    Documentar "esto nos paso una vez en una corrida" deja la cobertura al azar:
    si el modelo no se equivoca ese dia, la rama de manejo de la falla nunca se
    ejecuta y nadie sabe si funciona. Aqui el cliente esta guionado, asi que las
    cinco fallas se provocan A PROPOSITO, de forma determinista y sin gastar un
    token de la API.

    Se corre con:  python src/autoprueba_agente.py

LAS CINCO FALLAS
    1. argumentos que no son JSON valido
    2. herramienta que no existe
    3. herramienta que lanza una excepcion
    4. la misma herramienta con los mismos argumentos, repetida
    5. pasos agotados sin que el modelo concluya -> cierre determinista

    En los cinco casos el agente tiene que devolver una salida valida (las cinco
    lineas del esquema) y dejar la falla contada en su registro. Un agente que
    se cae ante un JSON mal formado no sirve, y uno que la esconde es peor.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import schema                                  # noqa: E402
from agente import Agente                      # noqa: E402

HECHOS_OK = json.dumps({
    "privacion_libertad": False, "derecho_colectivo": False,
    "titular_pide_lo_suyo": False, "acto_general": False,
    "dano_consumado": False, "continua_vulneracion": False,
    "incumplimiento_normativo": False, "afectacion_individual": True,
    "otro_medio_judicial": False, "medio_eficaz": True,
    "perjuicio_irremediable": False, "sujeto_especial_proteccion": True,
    "derecho": "salud", "accionado": "EPS",
    "pretension": "autorizar y entregar el medicamento ordenado",
}, ensure_ascii=False)


# --------------------------------------------------------------------------
# Dobles de prueba
# --------------------------------------------------------------------------
class _Fn:
    def __init__(self, name, arguments):
        self.name, self.arguments = name, arguments


class _TC:
    def __init__(self, i, name, arguments):
        self.id, self.function = f"call_{i}", _Fn(name, arguments)


class _Msg:
    def __init__(self, content, tool_calls):
        self.content, self.tool_calls = content, tool_calls


class _Resp:
    def __init__(self, msg):
        self.choices = [type("C", (), {"message": msg})()]


class ClienteGuionado:
    """Devuelve los pasos del guion en orden. La llamada de extraccion de
    hechos se reconoce porque trae `response_format`."""

    def __init__(self, guion: list):
        self.guion, self.i, self.llamadas_hechos = guion, 0, 0

    @property
    def chat(self):
        return self

    @property
    def completions(self):
        return self

    def create(self, **kw):
        if kw.get("response_format"):
            self.llamadas_hechos += 1
            return _Resp(_Msg(HECHOS_OK, None))
        paso = self.guion[min(self.i, len(self.guion) - 1)]
        self.i += 1
        if paso is None:
            return _Resp(_Msg("Ya tengo los hechos relevantes.", None))
        return _Resp(_Msg("", [_TC(self.i, n, a) for n, a in paso]))


class IndiceFalso:
    def __init__(self, revienta_con: str | None = None):
        self.revienta_con = revienta_con

    def recuperar(self, consulta, estrategia="reranked", k=5):
        if self.revienta_con and self.revienta_con in consulta:
            raise RuntimeError("el indice denso no esta construido")
        return [{"articulo": "art. 49 CP", "norma": "Constitucion Politica de Colombia",
                 "vigencia": "vigente", "id": "CP-049",
                 "texto": "La atencion de la salud es un servicio publico a cargo del Estado."}]


RELATO = ("A mi mama de 72 anos el medico de la EPS le ordeno un medicamento y en la "
          "farmacia dicen que no esta en el plan. Radicamos la peticion hace dos meses.")


# --------------------------------------------------------------------------
def _correr(nombre: str, guion: list, indice=None, max_pasos: int = 5) -> dict:
    ag = Agente(ClienteGuionado(guion), indice or IndiceFalso(),
                max_pasos=max_pasos, etiqueta=nombre)
    salida = ag(RELATO)
    parseada = schema.parse_salida(salida)
    t = ag.trazas[0]
    return {
        "nombre": nombre,
        "salida_valida": parseada.get("mecanismo") in schema.MECANISMOS,
        "mecanismo": parseada.get("mecanismo"),
        "pasos": t["pasos"],
        "cierre": t["cierre"],
        "fallas": t["fallas"],
        "contadores": {k: v for k, v in ag.contadores.items() if v},
    }


ESCENARIOS = [
    # (nombre, guion, indice, max_pasos, contador que debe activarse)
    ("camino feliz",
     [[("buscar_normas", '{"consulta": "derecho a la salud medicamento no PBS"}')], None],
     None, 5, None),

    ("1 · argumentos no JSON",
     [[("buscar_normas", '{"consulta": "salud"')],
      [("buscar_normas", '{"consulta": "salud"}')], None],
     None, 5, "argumentos_no_json"),

    ("2 · herramienta inexistente",
     [[("consultar_oraculo", '{"pregunta": "procede?"}')],
      [("buscar_normas", '{"consulta": "salud"}')], None],
     None, 5, "herramienta_inexistente"),

    ("3 · herramienta que revienta",
     [[("buscar_normas", '{"consulta": "indice roto a proposito"}')],
      [("buscar_normas", '{"consulta": "salud"}')], None],
     IndiceFalso(revienta_con="roto"), 5, "herramienta_con_error"),

    ("3b · tool externa con tipo invalido",
     [[("calcular_termino", '{"tipo": {"raro": 1}, "relato": "hace dos meses"}')], None],
     None, 5, "herramienta_con_error"),

    ("4 · llamada repetida",
     [[("buscar_normas", '{"consulta": "salud"}')],
      [("buscar_normas", '{"consulta": "salud"}')], None],
     None, 5, "llamada_repetida"),

    ("5 · pasos agotados",
     [[("buscar_normas", '{"consulta": "una cosa"}')],
      [("buscar_normas", '{"consulta": "otra cosa"}')],
      [("buscar_normas", '{"consulta": "tercera cosa"}')]],
     None, 3, "pasos_agotados"),

    ("tool externa bien invocada",
     [[("calcular_termino", '{"tipo": "peticion_general", "relato": "radicamos hace dos meses"}')],
      None],
     None, 5, None),
]


def main() -> int:
    print(f"{'='*96}\n  AUTOPRUEBA DEL AGENTE · las cinco fallas, provocadas a proposito\n{'='*96}")
    print(f"{'escenario':<34}{'salida':>8}{'mec.':>16}{'pasos':>7}  contadores activados")
    print("-" * 96)

    fallos = []
    for nombre, guion, indice, max_pasos, esperado in ESCENARIOS:
        r = _correr(nombre, guion, indice, max_pasos)
        ok = r["salida_valida"]
        if esperado and esperado not in r["contadores"]:
            ok = False
            fallos.append(f"{nombre}: no se activo '{esperado}'")
        if not r["salida_valida"]:
            fallos.append(f"{nombre}: la salida no es valida")
        marca = "ok" if ok else "MAL"
        cont = ", ".join(f"{k}={v}" for k, v in r["contadores"].items()
                         if k not in ("tool_invocada", "tool_buscar", "tool_termino"))
        print(f"{nombre:<34}{marca:>8}{r['mecanismo'] or '-':>16}{r['pasos']:>7}  {cont or '—'}")

    print("=" * 96)
    if fallos:
        print(f"\n{len(fallos)} PROBLEMAS:")
        for f in fallos:
            print("  -", f)
        return 1
    print("\nLas cinco fallas se manejan y en los ocho escenarios el agente devuelve "
          "una salida valida.")
    print("Ninguna falla tumba la corrida y ninguna queda sin contar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
