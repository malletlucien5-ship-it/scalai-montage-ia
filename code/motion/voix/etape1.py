#!/usr/bin/env python3
"""Étape 1 de la SOP sans session Claude : son, voix, synchro, puis plan du proxy.

Lancé par `.github/workflows/etape1.yml`. Enchaîne :

1. `--audio maitre` (défaut) : voix et synchro sur l'OBS ou le WAV déposé.
   Le son intégré de chaque rush est aussi extrait et passé en secours : il ne
   couvre que ce que l'OBS ne couvre pas (faux départ hors OBS, fin après l'OBS).
   `--audio camera` : extraction du son intégré de chaque rush caméra
   (`extraire_audio_camera.py`), puis voix et synchro sur ces WAV.
   Refusé si un OBS ou un WAV est dans rushs/, sauf raison dans `--forcer-son-camera`.
2. `ameliorer_voix.py rendre --sans-proxy` : voix.wav et sources.json dans S3.
3. Plan des tranches du proxy (`proxy_parties.py`), écrit dans GITHUB_OUTPUT.

  .venv/bin/python voix/etape1.py --projet PROJET [--audio camera|maitre] [--exclure 0022]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ameliorer_voix as av  # noqa: E402
import extraire_audio_camera as ex  # noqa: E402
from chaine_audio import log  # noqa: E402


def exclu(nom: str, exclure: list[str]) -> bool:
    """Un rush est exclu si son nom contient un des motifs (ex. « 0022 »)."""
    return any(m and m in nom for m in exclure)


def sources_projet(projet: str, exclure: list[str]) -> list[av.Source]:
    sources = [s for s in av.sources_projet(projet) if not exclu(s.nom, exclure)]
    for s in av.sources_projet(projet):
        if exclu(s.nom, exclure):
            log(f"  {s.nom} : exclu.")
    return sources


def sources_camera(projet: str, exclure: list[str], forcer: str = "") -> list[str]:
    """Rushs caméra et WAV extraits, dans l'ordre attendu par ameliorer_voix.py.

    Un OBS ou un WAV présent dans rushs/ porte la voix (règle de Lucien) : le son caméra
    est alors refusé, sauf raison écrite dans --forcer-son-camera.
    """
    sources = sources_projet(projet, exclure)
    for s in sources:
        av.sonder(s, set())
    maitres = [s.nom for s in sources if s.type == "maitre"]
    if maitres and not forcer.strip():
        raise av.ErreurEntree(
            f"Son caméra refusé : {len(maitres)} audio(s) maître(s) dans rushs/ ({', '.join(maitres)}). "
            "Relancer avec --audio maitre, ou donner une raison dans --forcer-son-camera.")
    if maitres:
        log(f"  Son caméra forcé malgré {len(maitres)} OBS ou WAV : {forcer.strip()}")
    prefixe = f"s3://{av.BUCKET}/inputs/{projet}/audio-camera"
    out = []
    for s in sources:
        if s.type == "camera":
            out += [s.s3, f"{prefixe}/{Path(s.nom).stem}.wav"]
    return out


def secours_camera(projet: str, exclure: list[str]) -> list[str]:
    """WAV du son de chaque rush (cache S3 réutilisé), à passer en `--secours`.

    Jamais bloquant : un rush sans secours garde l'ancien comportement (OBS seul).
    """
    log("Son caméra des rushs, en secours de l'OBS...")
    try:
        ignorer = [s.nom for s in av.sources_projet(projet) if exclu(s.nom, exclure)]
        wavs = ex.extraire_projet(projet, ignorer, paralleles=6, tolerant=True)
    except Exception as exc:  # noqa: BLE001 : le secours ne bloque jamais l'étape 1
        log(f"  [AVERTISSEMENT] Aucun secours caméra : {exc}")
        return []
    return [a for w in wavs.values() for a in ("--secours", w)]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--projet", required=True)
    p.add_argument("--audio", choices=["camera", "maitre"], default="maitre")
    p.add_argument("--forcer-son-camera", default="",
                   help="raison écrite pour garder le son caméra malgré un OBS ou un WAV dans rushs/")
    p.add_argument("--minutes-par-tranche", type=float, default=10.0)
    p.add_argument("--exclure", default="",
                   help="rushs à laisser hors du proxy, motifs séparés par des virgules (ex. 0022)")
    args = p.parse_args(argv)
    projet = av.valider_projet(args.projet)
    exclure = [m.strip() for m in args.exclure.split(",") if m.strip()]

    if args.audio == "camera":
        log("Extraction du son caméra...")
        ignorer = [a for s in av.sources_projet(projet) if exclu(s.nom, exclure)
                   for a in ("--ignorer", s.nom)]
        code = ex.main(["--projet", projet, "--paralleles", "6", *ignorer])
        if code:
            return code
        rendre = ["rendre", "--projet", projet, "--sans-proxy", *sources_camera(projet, exclure, args.forcer_son_camera)]
    else:
        # Mêmes rushs et même ordre qu'avant : le secours n'ajoute aucun rush.
        rendre = ["rendre", "--projet", projet, "--sans-proxy"]
        if exclure:
            rendre += [s.s3 for s in sources_projet(projet, exclure)]
        rendre += secours_camera(projet, exclure)
    code = av.main(rendre)
    if code:
        return code

    sortie = av.REPO / "out" / "voix" / projet / "sortie" / av.NOM_SOURCES
    total = json.loads(sortie.read_text())["proxy"]["images"]
    par_tranche = args.minutes_par_tranche * 60 * av.PROXY_FPS
    parties = max(1, math.ceil(total / par_tranche))
    log(f"Proxy : {total} images, {parties} tranche(s) de {args.minutes_par_tranche:g} min.")
    sortie_gh = os.environ.get("GITHUB_OUTPUT")
    if sortie_gh:
        with open(sortie_gh, "a") as f:
            f.write(f"parties={parties}\n")
            f.write(f"indices={json.dumps(list(range(parties)))}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
