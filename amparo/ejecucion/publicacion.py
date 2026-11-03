"""Publicar en `results/`: comprobar TODOS los artefactos antes de publicar
NINGUNO.

`Corrida.publicar()` lanza en el primero que no existe, y lanza A MITAD. Sin
esta guarda, un fallo en el cuarto deja `results/` con tres artefactos de esta
corrida y ocho de la anterior: un estado que no corresponde a ninguna corrida
completa, que es justo lo que `verificar_entrega.py` existe para detectar,
provocado por la propia publicacion. Paso en m3/20261017T024911Z con 6 de 12.

Y el mensaje decia solo "no existe el artefacto X". Aqui se nombra quien lo
genera, para no tener que buscarlo entre decenas de celdas.

LO QUE SE GUARDA EN `runs/` NO ESTA ENTREGADO HASTA QUE SE PUBLICA: la corrida
m2/20261018T203244Z genero cuatro artefactos que se quedaron en su carpeta y
`verificar_entrega.py` los conto como ausentes.
"""
from __future__ import annotations


def faltantes(c, a_publicar) -> list[str]:
    """Los artefactos de `a_publicar` que la corrida todavia no genero."""
    return [n for n, _ in a_publicar
            if not (c.dir / c.artefactos.get(n, f"{n}.json")).exists()]


def publicar_todo(c, a_publicar, quien_lo_genera: dict | None = None) -> None:
    """Publica `[(nombre, destino), ...]` solo si estan todos.

    Si falta alguno no publica nada, imprime quien genera cada faltante y
    lanza RuntimeError. Los destinos se escriben literales en cada pipeline
    (`results/m3_scorecard.csv`) para que la autoprueba los pueda auditar.
    """
    quien_lo_genera = quien_lo_genera or {}
    print(f"  comprobando {len(a_publicar)} artefactos antes de publicar")
    faltan = faltantes(c, a_publicar)
    if faltan:
        print("=" * 70)
        print(f"  NO SE PUBLICA NADA. Faltan {len(faltan)} de {len(a_publicar)}:")
        print("=" * 70)
        for n in faltan:
            print(f"    {n:<22} lo genera -> "
                  f"{quien_lo_genera.get(n, 'revisa `c.artefactos`')}")
        print()
        print("  Genera esos artefactos y vuelve a publicar. No se publica nada a")
        print("  medias: `results/` a medias no corresponde a ninguna corrida.")
        print("=" * 70)
        raise RuntimeError(f"faltan {len(faltan)} artefactos: {', '.join(faltan)}")

    print(f"  los {len(a_publicar)} artefactos estan. Publicando.")
    for nombre, destino in a_publicar:
        c.publicar(nombre, destino)
