#!/usr/bin/env python3
"""Extrait le son intégré de chaque rush caméra en WAV PCM 48 kHz 24 bits.

Cas « Le son caméra intégré sert de source audio » de la SOP : aucun WAV ni OBS
ne porte la voix. Chaque WAV extrait devient l'audio maître de son rush pour
`voix/ameliorer_voix.py`.

Le rush n'est jamais téléchargé en entier : seuls les morceaux AAC sont lus par
plages d'octets (voir `temoin_par_plages`). L'amorce AAC est retirée comme le fait
ffmpeg. Les 20 premières secondes sont comparées au décodage direct du MP4.

Sortie : s3://…/inputs/PROJET/audio-camera/NOM_DU_RUSH.wav (canaux d'origine).
La dernière sortie liste les sources à passer à `ameliorer_voix.py rendre`.

  .venv/bin/python voix/extraire_audio_camera.py --projet PROJET
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ameliorer_voix as av  # noqa: E402
from chaine_audio import AUDIO_SR, lancer, log  # noqa: E402

CONTROLE_S = 20.0
META_IDENT = "rush-ident"  # métadonnée S3 : identité du rush source
TOL_CONTROLE = 1e-4


def _decoder(cmd_entree: list[str], filtre: str = "", duree: float | None = None) -> np.ndarray:
    cmd = ["ffmpeg", "-nostdin", "-v", "error", *cmd_entree, "-map", "0:a:0", "-vn"]
    if duree:
        cmd += ["-t", f"{duree:.3f}"]
    if filtre:
        cmd += ["-af", filtre]
    cmd += ["-ar", str(AUDIO_SR), "-f", "f32le", "-"]
    r = lancer(cmd, capture_output=True)
    if r.returncode != 0 or not r.stdout:
        raise av.ErreurEntree(f"décodage audio : {r.stderr.decode(errors='replace')[-300:]}")
    return np.frombuffer(r.stdout, dtype=np.float32)


def extraire(src: av.Source, dossier: Path, cache: Path | None = None) -> tuple[Path, dict]:
    """WAV PCM 24 bits 48 kHz du son caméra, échantillon 0 = premier échantillon du MP4.

    En lecture entière, le même passage écrit aussi le son témoin 16 kHz dans le cache
    de `ameliorer_voix.py` (`cache`) : le rush n'est lu qu'une fois.
    """
    wav = dossier / f"{Path(src.nom).stem}.wav"
    adts = dossier / f"{src.ident}.adts"
    t = time.time()
    try:
        amorce, stats = av.temoin_par_plages(src, adts)
        filtre = f"atrim=start_sample={amorce},asetpts=PTS-STARTPTS" if amorce else ""
        cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "aac", "-i", str(adts),
               "-map", "0:a:0"]
        if filtre:
            cmd += ["-af", filtre]
        cmd += ["-ar", str(AUDIO_SR), "-c:a", "pcm_s24le", str(wav)]
        r = lancer(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise av.ErreurEntree(f"{src.nom} : écriture WAV {r.stderr[-300:]}")
        methode = f"plages d'octets, {stats['octets'] / 1e6:.1f} Mo lus"
    except (av.FormatNonGere, OSError, ValueError, IndexError, StopIteration, TypeError) as exc:
        log(f"  [AVERTISSEMENT] {src.nom} : plages impossibles ({exc}). ffmpeg lit tout.")
        cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error", *av._entree_ffmpeg(src),
               "-map", "0:a:0", "-vn", "-ar", str(AUDIO_SR), "-c:a", "pcm_s24le", str(wav)]
        temoin = cache / f"{src.ident}_16k.f32" if cache else None
        if temoin and not temoin.is_file():
            cache.mkdir(parents=True, exist_ok=True)
            cmd += ["-map", "0:a:0", "-vn", "-ac", "1", "-ar", str(av.synchro.XCORR_SR),
                    "-f", "f32le", str(temoin.with_suffix(".part"))]
        r = lancer(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise av.ErreurEntree(f"{src.nom} : extraction {r.stderr[-300:]}")
        if temoin and temoin.with_suffix(".part").is_file():
            temoin.with_suffix(".part").replace(temoin)
        methode = "ffmpeg, fichier entier" + (", son témoin 16 kHz en cache" if temoin else "")
    finally:
        adts.unlink(missing_ok=True)

    # Contrôle : début identique au décodage direct du MP4 (quantification 24 bits près).
    ref = _decoder(av._entree_ffmpeg(src), duree=CONTROLE_S)
    x = _decoder(["-i", str(wav)], duree=CONTROLE_S)
    n = min(len(ref), len(x))
    ecart = float(np.max(np.abs(ref[:n] - x[:n]))) if n else float("inf")
    if n < AUDIO_SR or ecart > TOL_CONTROLE:
        raise av.ErreurEntree(f"{src.nom} : écart {ecart:.2e} avec le décodage direct")
    sonde = av._sonde_sortie(wav)["streams"][0]
    duree_wav = int(sonde["duration_ts"]) / AUDIO_SR
    duree_rush = av._f(src.probe.get("format", {}).get("duration"))
    info = {"rush": src.nom, "wav": wav.name, "codec": sonde["codec_name"],
            "sample_rate": int(sonde["sample_rate"]), "canaux": int(sonde["channels"]),
            "duree_wav_s": round(duree_wav, 3), "duree_rush_s": round(duree_rush, 3),
            "ecart_controle": ecart, "methode": methode,
            "temps_s": round(time.time() - t, 1)}
    log(f"  {src.nom} → {wav.name} : {duree_wav:.1f} s, {info['canaux']} canaux, "
        f"{info['temps_s']} s ({methode}), écart contrôle {ecart:.1e}")
    return wav, info


def wav_en_cache(src: av.Source, uri: str) -> bool:
    """Le WAV déjà dans S3 vient-il de ce rush, dans sa version actuelle ?

    L'envoi marque le WAV avec l'identité du rush (URI, ETag, taille). Un rush
    remplacé sous le même nom change d'identité : le WAV est alors refait.
    """
    bucket, _, key = uri[5:].partition("/")
    try:
        head = json.loads(av.run_aws(["s3api", "head-object", "--bucket", bucket, "--key", key,
                                      "--output", "json"]))
    except av.ErreurEntree:
        return False
    return head.get("Metadata", {}).get(META_IDENT) == src.ident


def extraire_projet(projet: str, ignorer: list[str] = (), paralleles: int = 3,
                    travail: Path | None = None, reutiliser: bool = True,
                    tolerant: bool = False) -> dict[str, str]:
    """Son de chaque rush caméra du projet dans s3://…/inputs/PROJET/audio-camera/.

    Retourne {URI du rush: URI du WAV}, dans l'ordre des rushs. Un WAV déjà extrait
    du même rush est réutilisé. `tolerant` : un rush en échec est signalé et omis
    au lieu d'arrêter tout (mode secours de l'étape 1).
    """
    sources = [s for s in av.sources_projet(projet) if s.nom not in ignorer]
    for s in sources:
        av.sonder(s, set())
    cameras = [s for s in sources if s.type == "camera"]
    for s in sources:
        if s.type != "camera":
            log(f"  {s.nom} : {s.origine}, pas de son caméra à extraire.")
    if not cameras:
        raise av.ErreurEntree("Aucun rush caméra.")
    prefixe = f"s3://{av.BUCKET}/inputs/{projet}/audio-camera"
    cache = (travail or av.REPO / "out" / "voix" / projet) / "cache"
    (av.REPO / "out").mkdir(exist_ok=True)

    def traiter(src: av.Source) -> dict:
        uri = f"{prefixe}/{Path(src.nom).stem}.wav"
        try:
            if reutiliser and wav_en_cache(src, uri):
                log(f"  {src.nom} → {Path(uri).name} : déjà dans S3, réutilisé.")
                return {"rush": src.nom, "rush_s3": src.s3, "wav": Path(uri).name,
                        "methode": "cache S3", "uri": uri}
            wav, info = extraire(src, dossier, cache)
            av.run_aws(["s3", "cp", str(wav), uri, "--only-show-errors",
                        "--metadata", f"{META_IDENT}={src.ident}"])
            wav.unlink()
            return {**info, "rush_s3": src.s3, "uri": uri}
        except Exception as exc:  # noqa: BLE001 : en mode tolérant, tout échec est un rush sans secours
            if not tolerant:
                raise
            log(f"  [AVERTISSEMENT] {src.nom} : son caméra non extrait ({exc}).")
            return {"rush": src.nom, "erreur": str(exc)}

    t = time.time()
    with tempfile.TemporaryDirectory(dir=av.REPO / "out") as tmp:
        dossier = Path(tmp)
        with ThreadPoolExecutor(max(1, paralleles)) as pool:
            infos = list(pool.map(traiter, cameras))
    log(f"Extraction terminée en {time.time() - t:.0f} s.")
    cache.parent.mkdir(parents=True, exist_ok=True)
    (cache.parent / "audio-camera.json").write_text(
        json.dumps(infos, ensure_ascii=False, indent=2) + "\n")
    return {i["rush_s3"]: i["uri"] for i in infos if "uri" in i}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--projet", required=True)
    p.add_argument("--ignorer", action="append", default=[],
                   help="nom de fichier des rushs/ à ignorer (répétable)")
    p.add_argument("--travail", type=Path,
                   help="dossier de travail de ameliorer_voix.py. Défaut : out/voix/PROJET")
    p.add_argument("--paralleles", type=int, default=3, help="rushs lus en même temps")
    p.add_argument("--reextraire", action="store_true",
                   help="refait les WAV même s'ils sont déjà dans S3 pour ce rush")
    args = p.parse_args(argv)
    try:
        av.valider_projet(args.projet)
        wavs = extraire_projet(args.projet, args.ignorer, args.paralleles, args.travail,
                               reutiliser=not args.reextraire)
        log("Sources pour ameliorer_voix.py :")
        for rush, wav in wavs.items():
            print(rush, flush=True)
            print(wav, flush=True)
        return 0
    except av.ErreurEntree as exc:
        print(f"[ERREUR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
