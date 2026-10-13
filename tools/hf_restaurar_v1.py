"""Devuelve el repo publico de Hugging Face al adaptador v1, el de produccion.

## Que paso

`Tomas0626/amparo-lora-qwen2.5-7b` es **publico**, y la celda de publicacion de
`colab/m1_finetune.ipynb` subia el adaptador cada vez que alguien corria el
notebook entero. Verificado por huella del `.safetensors`, no por fecha:

    5d37d91af1  2026-10-09  8ce3cc2bc9306974  v1, produccion
    dfffc5b6b1  2026-10-10  82089e4a0d9612a7  v2  (su mensaje dice "2291 ejemplos": mal rotulado)
    a888451f20  2026-10-12  c2d7bb1dfdd8e598  v3  <- main, candidato RECHAZADO

Asi que el `main` publico no era v1 desde el 10 de octubre: primero v2, despues
v3, ninguno adoptado. La celda ya no publica sola (`PUBLICAR_EN_HF = False`).

## Que hace

Descarga los archivos exactos de la revision de v1, **comprueba la huella** del
adaptador antes de subir nada, y los sube a `main` como un commit nuevo. No se
reescribe ni se borra historia: v2 y v3 siguen en el historial del repo, y se
pueden recuperar por su revision.

Por defecto **simula**. Subir exige estar autenticado en Hugging Face, y el
token no pasa por aqui: se hace antes con `hf auth login`.

    python -m tools.hf_restaurar_v1              # descarga, verifica y dice que haria
    hf auth login                                # una vez, con un token de ESCRITURA
    python -m tools.hf_restaurar_v1 --escribir   # sube v1 a main y lo verifica
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

REPO = "Tomas0626/amparo-lora-qwen2.5-7b"
REVISION_V1 = "5d37d91af19ae8e69cd0bd219392b4557fc07e19"
HUELLA_V1 = "8ce3cc2bc9306974"
CONOCIDAS = {
    "8ce3cc2bc9306974": "v1 (produccion)",
    "82089e4a0d9612a7": "v2 (descartado)",
    "c2d7bb1dfdd8e598": "v3 (rechazado el 2026-10-12)",
}


def huella(ruta) -> str | None:
    from tools.rag.manifiesto import huella_archivo

    return huella_archivo(Path(ruta))


def verificar_v1(carpeta) -> str:
    """La huella del adaptador de la carpeta, o se detiene si no es v1.

    Es la comprobacion que impide subir otra cosa creyendo que es v1.
    """
    h = huella(Path(carpeta) / "adapter_model.safetensors")
    if h is None:
        raise SystemExit(f"no hay adapter_model.safetensors en {carpeta}")
    if h != HUELLA_V1:
        raise SystemExit(
            f"lo descargado tiene huella {h} ({CONOCIDAS.get(h, 'desconocido')}) y v1 es "
            f"{HUELLA_V1}. No se sube nada.")
    return h


def huella_de_main() -> str:
    from huggingface_hub import hf_hub_download

    return huella(hf_hub_download(REPO, "adapter_model.safetensors", revision="main",
                                  force_download=True))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--escribir", action="store_true", help="subir de verdad (exige hf auth login)")
    a = ap.parse_args(argv)

    from huggingface_hub import HfApi, get_token, snapshot_download

    antes = huella_de_main()
    print(f"main hoy: {antes} = {CONOCIDAS.get(antes, 'desconocido')}")
    if antes == HUELLA_V1:
        print("main ya es v1: no hay nada que hacer.")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        carpeta = snapshot_download(REPO, revision=REVISION_V1, local_dir=tmp)
        verificar_v1(carpeta)
        archivos = sorted(p.name for p in Path(carpeta).iterdir()
                          if p.is_file() and not p.name.startswith("."))
        print(f"revision de v1 {REVISION_V1[:10]}: huella {HUELLA_V1} verificada")
        print(f"  archivos: {archivos}")

        if not a.escribir:
            print("\nSIMULACION. Subiria esos archivos a main como un commit nuevo, sin borrar "
                  "historia.\nPara hacerlo: `hf auth login` (token de escritura) y despues --escribir.")
            return 0
        if not get_token():
            raise SystemExit("no hay sesion de Hugging Face: corre `hf auth login` primero.")

        HfApi().upload_folder(
            repo_id=REPO, folder_path=carpeta, allow_patterns=archivos,
            commit_message=(f"Restaurar v1 (produccion, huella {HUELLA_V1}) como version "
                            f"principal. v2 y v3 se publicaron por error desde la celda del "
                            f"notebook y no estan adoptados; siguen en el historial."))

    despues = huella_de_main()
    print(f"main ahora: {despues} = {CONOCIDAS.get(despues, 'desconocido')}")
    if despues != HUELLA_V1:
        raise SystemExit("la subida termino pero main no quedo en v1: revisar a mano.")
    print("OK: main vuelve a ser v1.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
