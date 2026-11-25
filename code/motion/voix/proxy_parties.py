#!/usr/bin/env python3
"""Proxy 1080p de l'étape 1, fabriqué par tranches ffmpeg indépendantes.

Remplace le proxy Remotion Lambda : un proxy ne demande que décoder, réduire,
encoder. Remotion faisait passer chaque image 4K par Chrome (6,17 $ pour 71 min,
avec des décalages d'images aux raccords, le 27/09/2026).

Chaque tranche lit ses plages de rush par URL présignée avec un saut précis
(`-ss` avant `-i`, vérifié image pour image sur les rushs DJI), puis encode
aux réglages du proxy de `ameliorer_voix.py`. Les tranches tournent en parallèle
(jobs GitHub Actions), puis `assembler` les concatène en copie de flux, ajoute
`voix.wav`, contrôle et envoie `proxy.mov`.

  partie    --projet P --index I --parties N   tranche I sur N, envoyée dans S3
  assembler --projet P --parties N             proxy.mov, contrôles, envoi, lien ;
                                               apercu.mp4 720p lisible en ligne
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ameliorer_voix as av  # noqa: E402
from chaine_audio import log  # noqa: E402

GOP = av.PROXY_GOP
APERCU_LARGEUR, APERCU_HAUTEUR = 1280, 720
NOM_APERCU = "apercu.mp4"


def prefixe_s3(projet: str) -> str:
    return f"s3://{av.BUCKET}/outputs/{projet}/synchro"


def lire_sources(projet: str, travail: Path) -> dict:
    local = travail / av.NOM_SOURCES
    av.run_aws(["s3", "cp", f"{prefixe_s3(projet)}/{av.NOM_SOURCES}", str(local),
                "--only-show-errors"])
    doc = json.loads(local.read_text())
    if doc.get("version") != 1 or doc.get("fps") != av.PROXY_FPS:
        raise av.ErreurEntree(f"sources.json inattendu : version {doc.get('version')}, "
                              f"{doc.get('fps')} i/s")
    return doc


def bornes(total: int, parties: int, index: int) -> tuple[int, int]:
    """Tranche [a, b) du proxy. Les bornes tombent sur un multiple du GOP."""
    par = math.ceil(total / parties / GOP) * GOP
    a = min(total, index * par)
    return a, min(total, a + par)


def morceaux(doc: dict, a: int, b: int) -> list[dict]:
    """Plages de rush couvrant les images [a, b) du proxy, dans l'ordre."""
    out = []
    for p in doc["plages"]:
        d, f = p["proxy_debut"], p["proxy_debut"] + p["images"]
        x, y = max(a, d), min(b, f)
        if x < y:
            out.append({"camera": p["camera"], "debut": p["camera_debut"] + x - d, "images": y - x})
    if sum(m["images"] for m in out) != b - a:
        raise av.ErreurEntree(f"Images {a} à {b} non couvertes par sources.json.")
    return out


def commande_decodeur(url: str, debut: int, images: int) -> list[str]:
    """Saut précis : ffmpeg décode depuis l'image clé précédente et jette tout
    horodatage antérieur. 1 ms avant l'image visée, l'image précédente est à 20 ms."""
    seek = ["-ss", f"{max(0.0, debut / av.PROXY_FPS - 0.001):.6f}"] if debut else []
    vf = (f"scale={av.PROXY_LARGEUR}:{av.PROXY_HAUTEUR}:force_original_aspect_ratio=decrease"
          f":flags=bicubic,pad={av.PROXY_LARGEUR}:{av.PROXY_HAUTEUR}:(ow-iw)/2:(oh-ih)/2,"
          "setsar=1,format=yuv420p")
    reco = [o for k, v in av.RECONNEXION.items() for o in (f"-{k}", v)]
    return ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", *reco, *seek,
            "-i", url, "-map", "0:v:0", "-an", "-sn", "-dn", "-vf", vf,
            "-fps_mode", "passthrough", "-frames:v", str(images),
            "-f", "rawvideo", "-pix_fmt", "yuv420p", "pipe:1"]


def commande_encodeur(sortie: Path, apercu: Path | None = None) -> list[str]:
    """Mêmes réglages que le proxy de ameliorer_voix.py, sans le son.

    Avec `apercu`, les mêmes images donnent aussi la version de visionnage 720p
    (lisible dans un navigateur), sans second décodage des rushs 4K.
    """
    entree = [
        "ffmpeg", "-nostdin", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        "-video_size", f"{av.PROXY_LARGEUR}x{av.PROXY_HAUTEUR}",
        "-framerate", str(av.PROXY_FPS), "-i", "pipe:0",
    ]
    if apercu is None:
        return entree + ["-map", "0:v:0", *reglages_proxy(sortie)]
    return entree + [
        "-filter_complex", f"[0:v]split=2[p][a];[a]scale={APERCU_LARGEUR}:{APERCU_HAUTEUR}"
        ":flags=bilinear[v]",
        "-map", "[p]", *reglages_proxy(sortie),
        "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
        "-maxrate", "2500k", "-bufsize", "5000k", "-g", str(4 * GOP), "-pix_fmt", "yuv420p",
        "-video_track_timescale", str(av.PROXY_FPS * 100), "-f", "mp4", str(apercu),
    ]


def reglages_proxy(sortie: Path) -> list[str]:
    return [
        "-c:v", "libx264", "-preset", av.PROXY_PRESET, "-profile:v", "high",
        "-b:v", av.PROXY_DEBIT, "-maxrate", av.PROXY_DEBIT_MAX, "-bufsize", av.PROXY_TAMPON,
        "-g", str(GOP), "-keyint_min", str(GOP), "-sc_threshold", "0", "-bf", "0",
        "-pix_fmt", "yuv420p", "-colorspace", "bt709", "-color_primaries", "bt709",
        "-color_trc", "bt709", "-color_range", "tv",
        "-video_track_timescale", str(av.PROXY_FPS * 100), "-f", "mp4", str(sortie),
    ]


def compter_images(chemin: Path) -> int:
    r = av.lancer(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0",
                   "-show_entries", "stream=nb_read_packets", "-of", "csv=p=0", str(chemin)],
                  capture_output=True, text=True, check=True)
    return int(r.stdout.strip())


def partie(args) -> int:
    travail = args.travail / f"partie-{args.index:03d}"
    travail.mkdir(parents=True, exist_ok=True)
    doc = lire_sources(args.projet, travail)
    total = doc["proxy"]["images"]
    a, b = bornes(total, args.parties, args.index)
    if a >= b:
        log(f"Tranche {args.index} vide ({total} images, {args.parties} tranches).")
        return 0
    liste = morceaux(doc, a, b)
    sortie = travail / f"partie-{args.index:03d}.mp4"
    apercu = travail / f"apercu-{args.index:03d}.mp4"
    log(f"Tranche {args.index + 1}/{args.parties} : images {a} à {b - 1} "
        f"({(b - a) / av.PROXY_FPS / 60:.1f} min), {len(liste)} plage(s).")
    t = time.time()
    urls = {}
    enc = subprocess.Popen(commande_encodeur(sortie, apercu), stdin=subprocess.PIPE)
    taille_image = av.PROXY_LARGEUR * av.PROXY_HAUTEUR * 3 // 2
    try:
        for m in liste:
            if m["camera"] not in urls:
                urls[m["camera"]] = (av.presign(m["camera"]) if m["camera"].startswith("s3://")
                                     else m["camera"])
            dec = subprocess.Popen(commande_decodeur(urls[m["camera"]], m["debut"], m["images"]),
                                   stdout=subprocess.PIPE)
            n = 0
            while True:
                bloc = dec.stdout.read(taille_image * 25)
                if not bloc:
                    break
                n += len(bloc) // taille_image
                enc.stdin.write(bloc)
            if dec.wait() != 0 or n != m["images"]:
                raise av.ErreurControle(f"{Path(m['camera']).name} depuis l'image {m['debut']} : "
                                        f"{n} images décodées, {m['images']} attendues.")
        enc.stdin.close()
        if enc.wait() != 0:
            raise av.ErreurControle("encodeur de la tranche en échec")
    finally:
        if enc.poll() is None:
            enc.kill()
    n = compter_images(sortie)
    for fichier in (sortie, apercu):
        if compter_images(fichier) != b - a:
            raise av.ErreurControle(f"Tranche {args.index} : {fichier.name} n'a pas "
                                    f"{b - a} images.")
    duree = time.time() - t
    uri = f"{prefixe_s3(args.projet)}/parties/{args.parties:03d}-{args.index:03d}.mp4"
    av.envoyer(sortie, uri)
    av.envoyer(apercu, uri.replace("/parties/", "/parties/apercu-"))
    sortie.unlink()
    apercu.unlink()
    log(f"  {n} images en {duree:.0f} s ({n / duree:.1f} i/s), envoyée : {uri}")
    return 0


def assembler(args) -> int:
    t0 = time.time()
    travail = args.travail / "assemblage"
    travail.mkdir(parents=True, exist_ok=True)
    doc = lire_sources(args.projet, travail)
    total = doc["proxy"]["images"]
    prefixe = prefixe_s3(args.projet)
    locaux = []
    for i in range(args.parties):
        a, b = bornes(total, args.parties, i)
        if a >= b:
            continue
        local = travail / f"partie-{i:03d}.mp4"
        av.run_aws(["s3", "cp", f"{prefixe}/parties/{args.parties:03d}-{i:03d}.mp4", str(local),
                    "--only-show-errors"])
        if compter_images(local) != b - a:
            raise av.ErreurControle(f"Tranche {i} : nombre d'images faux.")
        locaux.append(local)
    voix = travail / av.NOM_VOIX
    av.run_aws(["s3", "cp", f"{prefixe}/{av.NOM_VOIX}", str(voix), "--only-show-errors"])
    liste = travail / "tranches.txt"
    liste.write_text("".join(f"file '{p}'\n" for p in locaux))
    proxy = travail / av.NOM_PROXY
    av.lancer(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat", "-safe", "0",
               "-i", str(liste), "-i", str(voix), "-map", "0:v:0", "-map", "1:a:0",
               "-map_metadata", "-1", "-c:v", "copy", "-c:a", "pcm_s24le",
               "-ar", str(av.AUDIO_SR), "-ac", "1", "-timecode", "00:00:00:00",
               "-video_track_timescale", str(av.PROXY_FPS * 100), "-f", "mov", str(proxy)],
              check=True)
    for p in locaux:
        p.unlink()
    cams = [{"nom": Path(p["camera"]).name, "frames": p["images"]} for p in doc["plages"]]
    controles = av.controler_proxy(proxy, cams, av.md5_pcm(voix),
                                   [c["frames"] for c in cams])
    echecs = controles.pop("echecs")
    rapport = {"projet": args.projet, "mode": "ffmpeg-tranches", "parties": args.parties,
               "controles": controles, "echecs": echecs}
    if echecs:
        (travail / "rapport-proxy.json").write_text(json.dumps(rapport, ensure_ascii=False,
                                                               indent=2))
        raise av.ErreurControle("Contrôles du proxy en échec : " + "; ".join(echecs))
    av.envoyer(proxy, f"{prefixe}/{av.NOM_PROXY}")
    lien = av.lien_telechargement(f"{prefixe}/{av.NOM_PROXY}")
    rapport["temps_assemblage_s"] = round(time.time() - t0, 1)
    rapport["lien_proxy"] = lien
    chemin = travail / "rapport-proxy.json"
    chemin.write_text(json.dumps(rapport, ensure_ascii=False, indent=2) + "\n")
    av.envoyer(chemin, f"{prefixe}/rapport-proxy.json")
    lien_txt = travail / "lien-proxy.txt"
    lien_txt.write_text(lien + "\n")
    av.envoyer(lien_txt, f"{prefixe}/lien-proxy.txt")
    proxy.unlink()
    lien_apercu = fabriquer_apercu(args, travail, prefixe, total, voix)
    av.run_aws(["s3", "rm", "--recursive", "--only-show-errors", f"{prefixe}/parties/"])
    log(f"Proxy : {controles['images']} images, timecode {controles['timecode']}, "
        f"audio identique à voix.wav : {controles['audio_proxy_identique_voix']}.")
    # Deux lignes lues par le workflow : téléchargement du proxy, visionnage en ligne.
    print(f"telechargement\t{lien}", flush=True)
    print(f"visionnage\t{lien_apercu}", flush=True)
    return 0


def lien_visionnage(uri: str, expires: int = av.PRESIGN_SORTIE_S) -> str:
    """Lien lu dans le navigateur, sans téléchargement (Content-Disposition: inline)."""
    import boto3

    env = av.aws_env()
    bucket, _, key = uri[5:].partition("/")
    s3 = boto3.client("s3", region_name=env["AWS_REGION"],
                      aws_access_key_id=env["AWS_ACCESS_KEY_ID"],
                      aws_secret_access_key=env["AWS_SECRET_ACCESS_KEY"])
    return s3.generate_presigned_url(
        "get_object", ExpiresIn=expires,
        Params={"Bucket": bucket, "Key": key, "ResponseContentDisposition": "inline",
                "ResponseContentType": "video/mp4"})


def fabriquer_apercu(args, travail: Path, prefixe: str, total: int, voix: Path) -> str:
    """Aperçu 720p H.264 + AAC, faststart : lisible en ligne sur une connexion lente."""
    locaux = []
    for i in range(args.parties):
        a, b = bornes(total, args.parties, i)
        if a >= b:
            continue
        local = travail / f"apercu-{i:03d}.mp4"
        av.run_aws(["s3", "cp", f"{prefixe}/parties/apercu-{args.parties:03d}-{i:03d}.mp4",
                    str(local), "--only-show-errors"])
        locaux.append(local)
    liste = travail / "apercus.txt"
    liste.write_text("".join(f"file '{p}'\n" for p in locaux))
    apercu = travail / NOM_APERCU
    av.lancer(["ffmpeg", "-nostdin", "-y", "-v", "error", "-f", "concat", "-safe", "0",
               "-i", str(liste), "-i", str(voix), "-map", "0:v:0", "-map", "1:a:0",
               "-map_metadata", "-1", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
               "-ac", "1", "-movflags", "+faststart", str(apercu)], check=True)
    for p in locaux:
        p.unlink()
    n = compter_images(apercu)
    if n != total:
        raise av.ErreurControle(f"Aperçu : {n} images, {total} attendues.")
    uri = f"{prefixe}/{NOM_APERCU}"
    av.run_aws(["s3", "cp", str(apercu), uri, "--only-show-errors",
                "--content-type", "video/mp4"])
    apercu.unlink()
    lien = lien_visionnage(uri)
    lien_txt = travail / "lien-apercu.txt"
    lien_txt.write_text(lien + "\n")
    av.envoyer(lien_txt, f"{prefixe}/lien-apercu.txt")
    return lien


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sous = p.add_subparsers(dest="commande", required=True)
    for nom in ("partie", "assembler"):
        s = sous.add_parser(nom)
        s.add_argument("--projet", required=True)
        s.add_argument("--parties", type=int, required=True)
        s.add_argument("--travail", type=Path, default=av.REPO / "out" / "proxy-parties")
        if nom == "partie":
            s.add_argument("--index", type=int, required=True)
    args = p.parse_args(argv)
    try:
        av.valider_projet(args.projet)
        return partie(args) if args.commande == "partie" else assembler(args)
    except av.ErreurEntree as exc:
        print(f"[ERREUR] {exc}", file=sys.stderr)
        return 2
    except (av.ErreurControle, subprocess.CalledProcessError) as exc:
        print(f"[ERREUR] {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
