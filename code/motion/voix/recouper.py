#!/usr/bin/env python3
"""Recoupe 4K : reconstruit le montage du monteur depuis les rushs caméra originaux.

Le monteur monte sur le proxy 1080p 50 i/s dans DaVinci Resolve. Il exporte
une EDL CMX 3600 (ou un FCPXML simple), et au besoin le WAV de sa timeline.
Sans WAV, le son est reconstruit depuis voix.wav de l'étape 1 avec les mêmes coupes.
Ce script relit chaque image du montage dans les rushs 4K via
`outputs/PROJET/synchro/sources.json`, encode une seule fois en H.264,
puis pose le son (WAV du monteur ou voix.wav recoupée) en PCM 24 bits dans un .mov.

Les rushs 4K restent dans S3. Ils sont lus par URL présignée, segment par
segment, jamais téléchargés en entier. Chaque segment est encodé en MPEG-TS,
vérifié, versé dans le multiplexeur final puis supprimé. Le disque n'a donc
besoin que de la place de la vidéo finale et d'un segment.

Contrôles bloquants :
- chaque segment contient exactement les images caméra attendues, dans l'ordre ;
- nombre d'images de la sortie = durée de l'EDL ;
- durée audio = durée vidéo à 5 ms près, audio identique au WAV ;
- décodage complet sans erreur ;
- aux raccords, chaque image de sortie ressemble plus à l'image source attendue
  qu'à ses voisines (aucune image en double ni manquante).

Usage :
  .venv/bin/python voix/recouper.py --projet P --edl montage.edl [--wav timeline.wav]
  (EDL et WAV : chemins locaux ou s3://)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import asdict, dataclass, field
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
BUCKET = os.environ.get("REMOTION_INPUT_BUCKET", "remotionlambda-eunorth1-08ow3rdhea")
PROJET_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

FPS_DEFAUT = 50
TAILLE_DEFAUT = (3840, 2160)
X264 = ["-c:v", "libx264", "-preset", "fast", "-crf", "12", "-pix_fmt", "yuv420p", "-g", "100"]
PRESIGN_S = 43200            # 12 h ; une URL neuve est signée pour chaque segment
BASE_TS_S = 10.0             # décalage des segments MPEG-TS : jamais de dts négatif
MARGE_SEEK_S = 0.5           # on se place avant l'image voulue, puis on sélectionne
ESSAIS_SEGMENT = 3
TOL_AUDIO_S = 0.005
TOL_DEPART_S = 0.001
VIGNETTE = (160, 90)         # images de contrôle des raccords, en gris
ECART_MAX = 6.0              # écart moyen max (niveaux de gris) avec l'image attendue
RATIO_VOISINE = 0.8          # une voisine plus proche que 0,8 x l'attendue : raccord faux
ECART_NOIR_MAX = 20.0
DEBIT_ESTIME_MBPS = 250      # pour l'avertissement disque, voir le rapport de mesure


class ErreurEntree(RuntimeError):
    """Entrées invalides ou montage non reconstructible. Code de sortie 2."""


class ErreurControle(RuntimeError):
    """Un contrôle bloquant a échoué. Code de sortie 3."""


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


# ─── Timecodes ───────────────────────────────────────────────────────────────

TC_RE = re.compile(r"^(\d{2}):(\d{2}):(\d{2})([:;.])(\d{2,3})$")


def tc_vers_images(tc: str, fps: int) -> int:
    m = TC_RE.match(tc.strip())
    if not m:
        raise ErreurEntree(f"Timecode illisible : {tc}")
    hh, mm, ss, sep, ff = m.groups()
    if sep != ":":
        raise ErreurEntree(f"Timecode drop frame ou à trames refusé : {tc}. "
                           f"Exporter en non drop frame à {fps} i/s.")
    hh, mm, ss, ff = int(hh), int(mm), int(ss), int(ff)
    if mm > 59 or ss > 59 or ff >= fps:
        raise ErreurEntree(f"Timecode hors plage à {fps} i/s : {tc}")
    return ((hh * 60 + mm) * 60 + ss) * fps + ff


def images_vers_tc(n: int, fps: int) -> str:
    signe = "-" if n < 0 else ""
    n = abs(n)
    ff = n % fps
    s = n // fps
    return f"{signe}{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}:{ff:02d}"


# ─── Montage : EDL CMX 3600 et FCPXML ────────────────────────────────────────

@dataclass
class Evenement:
    numero: str
    bobine: str
    video: bool
    audio: bool
    src_in: int
    src_out: int
    rec_in: int
    rec_out: int
    clip: str = ""
    ligne: int = 0

    @property
    def noir(self) -> bool:
        return self.bobine.upper() in {"BL", "BLK", "BLACK"}


@dataclass
class Montage:
    evenements: list[Evenement]
    format: str
    titre: str = ""
    debut_timeline: int | None = None   # fourni par le FCPXML (tcStart)
    avertissements: list[str] = field(default_factory=list)


def lire_edl(texte: str, fps: int) -> Montage:
    """CMX 3600 tel qu'exporté par Resolve : lignes V et A, coupes « C » seulement."""
    evts: list[Evenement] = []
    avert: list[str] = []
    titre = ""
    dernier: Evenement | None = None
    for num, brut in enumerate(texte.splitlines(), 1):
        ligne = brut.strip().lstrip("\ufeff")
        if not ligne:
            continue
        haut = ligne.upper()
        if haut.startswith("TITLE:"):
            titre = ligne.split(":", 1)[1].strip()
            continue
        if haut.startswith("FCM:"):
            if "NON" not in haut:
                raise ErreurEntree(f"Ligne {num} : {ligne}. Exporter en NON-DROP FRAME.")
            continue
        if ligne.startswith("*"):
            corps = ligne[1:].strip()
            cle, _, valeur = corps.partition(":")
            cle = cle.strip().upper()
            if cle == "FROM CLIP NAME" and dernier is not None:
                dernier.clip = valeur.strip()
            elif cle == "TO CLIP NAME":
                raise ErreurEntree(f"Ligne {num} : transition vers un autre clip. "
                                   "Seules les coupes franches sont reconstruites.")
            elif cle in {"EFFECT NAME", "ASC_SOP", "ASC_SAT"}:
                avert.append(f"ligne {num} : {corps} ignoré (effet ou étalonnage non reporté)")
            continue
        if haut.startswith("M2 ") or haut.startswith("M2\t"):
            raise ErreurEntree(f"Ligne {num} : changement de vitesse (M2) non géré : {ligne}")
        champs = ligne.split()
        if not champs[0].isdigit():
            avert.append(f"ligne {num} ignorée : {ligne}")
            continue
        tcs = [c for c in champs if TC_RE.match(c)]
        if len(tcs) != 4 or len(champs) < 8:
            raise ErreurEntree(f"Ligne {num} : événement illisible : {ligne}")
        numero, bobine, canal, transition = champs[0], champs[1], champs[2].upper(), champs[3].upper()
        if transition != "C":
            raise ErreurEntree(f"Ligne {num} : transition « {champs[3]} » non gérée. "
                               "Remplacer par une coupe franche (C) dans Resolve.")
        if len(champs) != 8:
            raise ErreurEntree(f"Ligne {num} : champ en trop après la transition : {ligne}")
        s_in, s_out, r_in, r_out = (tc_vers_images(t, fps) for t in tcs)
        if s_out - s_in != r_out - r_in:
            raise ErreurEntree(f"Ligne {num} : durées source et enregistrement différentes "
                               "(vitesse modifiée ?).")
        if r_out <= r_in:
            raise ErreurEntree(f"Ligne {num} : événement de durée nulle ou négative.")
        video = "V" in canal or canal == "B"
        audio = canal.startswith("A") or canal == "B" or "/A" in canal
        if canal == "NONE":
            video = audio = False
        dernier = Evenement(numero, bobine, video, audio, s_in, s_out, r_in, r_out, "", num)
        evts.append(dernier)
    if not evts:
        raise ErreurEntree("EDL vide : aucun événement.")
    return Montage(evts, "cmx3600", titre, None, avert)


def _temps_fcpxml(valeur: str | None) -> Fraction:
    if not valeur:
        return Fraction(0)
    v = valeur.strip()
    if not v.endswith("s"):
        raise ErreurEntree(f"Temps FCPXML illisible : {valeur}")
    v = v[:-1]
    if "/" in v:
        a, b = v.split("/")
        return Fraction(int(a), int(b))
    return Fraction(v)


def _en_images(t: Fraction, fps: int, quoi: str) -> int:
    x = t * fps
    if x.denominator != 1:
        raise ErreurEntree(f"FCPXML : {quoi} = {t} s ne tombe pas sur une image à {fps} i/s.")
    return int(x)


def lire_fcpxml(texte: str, fps: int) -> Montage:
    """FCPXML simple : un seul scénario principal, asset-clip ou clip, gap, pas de transition."""
    racine = ET.fromstring(texte)
    avert: list[str] = []
    assets = {a.get("id"): a for a in racine.iter("asset")}
    sequence = next(racine.iter("sequence"), None)
    if sequence is None:
        raise ErreurEntree("FCPXML sans séquence.")
    spine = sequence.find("spine")
    if spine is None:
        raise ErreurEntree("FCPXML sans spine.")
    tc_debut = _en_images(_temps_fcpxml(sequence.get("tcStart")), fps, "tcStart")
    evts: list[Evenement] = []
    interdits = {"timeMap", "conform-rate", "transition"}

    def verifier(elem: ET.Element, nom: str) -> None:
        for sous in elem.iter():
            if sous.tag in interdits and sous.tag != "conform-rate":
                raise ErreurEntree(f"FCPXML : {sous.tag} dans {nom} non géré.")
            if sous.tag == "conform-rate" and sous.get("scaleEnabled", "1") != "0":
                raise ErreurEntree(f"FCPXML : conform-rate dans {nom} non géré.")
            if sous.tag.startswith("adjust-") or sous.tag == "filter-video":
                avert.append(f"{nom} : {sous.tag} ignoré (effet non reporté)")
            if sous is not elem and sous.get("lane") and int(sous.get("lane")) > 0 \
                    and sous.tag in {"asset-clip", "clip", "video", "title", "ref-clip"}:
                raise ErreurEntree(f"FCPXML : plan connecté vidéo dans {nom} non géré.")

    for i, elem in enumerate(list(spine), 1):
        nom = elem.get("name", elem.tag)
        if elem.tag == "gap":
            verifier(elem, nom)
            continue
        if elem.tag == "transition":
            raise ErreurEntree(f"FCPXML : transition « {nom} » non gérée. Utiliser des coupes franches.")
        if elem.tag == "asset-clip":
            ref = elem.get("ref")
            source = elem
        elif elem.tag == "clip":
            source = elem.find("video")
            if source is None:
                raise ErreurEntree(f"FCPXML : clip « {nom} » sans vidéo.")
            ref = source.get("ref")
        else:
            raise ErreurEntree(f"FCPXML : élément <{elem.tag}> non géré dans le spine.")
        verifier(elem, nom)
        asset = assets.get(ref)
        if asset is None:
            raise ErreurEntree(f"FCPXML : asset {ref} introuvable.")
        offset = _en_images(_temps_fcpxml(elem.get("offset")), fps, f"offset de {nom}")
        duree = _en_images(_temps_fcpxml(elem.get("duration")), fps, f"durée de {nom}")
        # Pour un clip, le temps source est celui de l'élément video intérieur.
        debut_local = _temps_fcpxml(elem.get("start")) if elem.get("start") else Fraction(0)
        if elem.tag == "clip":
            debut_local = debut_local - _temps_fcpxml(source.get("offset")) \
                + _temps_fcpxml(source.get("start"))
        src_in = _en_images(debut_local - _temps_fcpxml(asset.get("start")), fps,
                            f"début source de {nom}")
        if duree <= 0:
            raise ErreurEntree(f"FCPXML : durée nulle pour {nom}.")
        evts.append(Evenement(f"{i:03d}", "AX", True, True, src_in, src_in + duree,
                              offset, offset + duree, asset.get("name") or nom, i))
    if not evts:
        raise ErreurEntree("FCPXML sans plan vidéo.")
    return Montage(evts, "fcpxml", sequence.get("name", ""), tc_debut, avert)


def lire_montage(chemin: Path, fps: int) -> Montage:
    texte = chemin.read_bytes().decode("utf-8", errors="replace")
    if texte.lstrip("\ufeff \r\n\t").startswith("<"):
        return lire_fcpxml(texte, fps)
    return lire_edl(texte, fps)


# ─── sources.json ────────────────────────────────────────────────────────────

@dataclass
class Plage:
    proxy_debut: int
    images: int
    camera: str
    camera_debut: int
    largeur: int
    hauteur: int


@dataclass
class Sources:
    fps: int
    proxy_images: int
    plages: list[Plage]

    def trouver(self, f: int) -> Plage | None:
        for p in self.plages:
            if p.proxy_debut <= f < p.proxy_debut + p.images:
                return p
        return None


def lire_sources(obj: dict) -> Sources:
    if obj.get("version") != 1:
        raise ErreurEntree(f"sources.json : version {obj.get('version')} inconnue (attendu 1).")
    try:
        fps = int(obj["fps"])
        n = int(obj["proxy"]["images"])
        plages = [Plage(int(p["proxy_debut"]), int(p["images"]), str(p["camera"]),
                        int(p["camera_debut"]), int(p["camera_largeur"]), int(p["camera_hauteur"]))
                  for p in obj["plages"]]
    except (KeyError, TypeError, ValueError) as exc:
        raise ErreurEntree(f"sources.json : champ manquant ou invalide ({exc}).") from exc
    plages.sort(key=lambda p: p.proxy_debut)
    for a, b in zip(plages, plages[1:]):
        if a.proxy_debut + a.images > b.proxy_debut:
            raise ErreurEntree("sources.json : deux plages se chevauchent dans le proxy.")
    for p in plages:
        if p.images <= 0 or p.camera_debut < 0 or p.proxy_debut < 0:
            raise ErreurEntree(f"sources.json : plage invalide {p}.")
        if p.proxy_debut + p.images > n:
            raise ErreurEntree("sources.json : une plage dépasse la fin du proxy.")
    return Sources(fps, n, plages)


# ─── Plan de reconstruction ──────────────────────────────────────────────────

@dataclass
class Segment:
    sortie_debut: int           # image de la timeline, 0 = début de la sortie
    images: int
    camera: str | None          # None : noir
    camera_debut: int = 0
    largeur: int = 0
    hauteur: int = 0
    evenements: list[str] = field(default_factory=list)


def choisir_proxy(evts: list[Evenement], clip: str | None) -> str:
    noms = Counter(e.clip for e in evts if e.video and not e.noir)
    if clip:
        return clip
    if not noms:
        raise ErreurEntree("Aucun événement vidéo dans le montage.")
    return noms.most_common(1)[0][0]


def planifier(montage: Montage, sources: Sources, fps: int, debut: int, tc_proxy: int,
              clip_proxy: str, inconnus_en_noir: bool) -> tuple[list[Segment], int, list[str]]:
    """Découpe le montage en segments caméra continus. Retourne (segments, images, avertissements)."""
    avert: list[str] = []
    evts = montage.evenements
    fin = max(e.rec_out for e in evts)
    if debut > min(e.rec_in for e in evts):
        raise ErreurEntree(f"Le début de timeline {images_vers_tc(debut, fps)} est après "
                           "le premier événement.")
    total = fin - debut
    videos = sorted((e for e in evts if e.video), key=lambda e: e.rec_in)
    for a, b in zip(videos, videos[1:]):
        if b.rec_in < a.rec_out:
            raise ErreurEntree(f"Événements vidéo {a.numero} et {b.numero} superposés : "
                               "une seule piste vidéo est reconstruite.")
    inconnus = sorted({e.clip for e in videos if not e.noir and e.clip != clip_proxy})
    if inconnus and not inconnus_en_noir:
        raise ErreurEntree(f"Clips autres que le proxy « {clip_proxy} » : {', '.join(inconnus)}. "
                           "Préciser --clip, ou --inconnus-en-noir pour les rendre en noir.")

    brut: list[Segment] = []
    curseur = 0

    def noir(n: int, etiquette: str) -> None:
        if n > 0:
            brut.append(Segment(curseur, n, None, evenements=[etiquette]))

    for e in videos:
        r0 = e.rec_in - debut
        if r0 > curseur:
            avert.append(f"trou de {r0 - curseur} images avant l'événement {e.numero} : noir")
            noir(r0 - curseur, "trou")
            curseur = r0
        n = e.rec_out - e.rec_in
        if e.noir or e.clip != clip_proxy:
            if not e.noir:
                avert.append(f"événement {e.numero} ({e.clip}) rendu en noir")
            noir(n, e.numero)
            curseur += n
            continue
        f = e.src_in - tc_proxy
        reste = n
        while reste > 0:
            p = sources.trouver(f)
            if p is None:
                raise ErreurEntree(f"Événement {e.numero} (ligne {e.ligne}) : l'image {f} du proxy "
                                   f"({images_vers_tc(f + tc_proxy, fps)}) n'a pas de plage caméra "
                                   "dans sources.json.")
            k = min(reste, p.proxy_debut + p.images - f)
            brut.append(Segment(curseur, k, p.camera, p.camera_debut + (f - p.proxy_debut),
                                p.largeur, p.hauteur, [e.numero]))
            curseur += k
            f += k
            reste -= k
    if curseur < total:
        avert.append(f"{total - curseur} images sans vidéo en fin de timeline : noir")
        noir(total - curseur, "fin")
        curseur = total

    # Fusion des segments contigus (même rush, images consécutives, ou noirs voisins).
    segments: list[Segment] = []
    for s in brut:
        d = segments[-1] if segments else None
        if d and d.camera == s.camera and (
                s.camera is None or d.camera_debut + d.images == s.camera_debut):
            d.images += s.images
            d.evenements += [x for x in s.evenements if x not in d.evenements]
        else:
            segments.append(s)
    assert sum(s.images for s in segments) == total
    return segments, total, avert


# ─── AWS ─────────────────────────────────────────────────────────────────────

_S3 = None


def client_s3():
    global _S3
    if _S3 is None:
        import boto3
        manque = [n for n in ("REMOTION_AWS_ACCESS_KEY_ID", "REMOTION_AWS_SECRET_ACCESS_KEY",
                              "REMOTION_AWS_REGION") if not os.environ.get(n)]
        if manque:
            raise ErreurEntree(f"Variables absentes : {', '.join(manque)}")
        _S3 = boto3.client(
            "s3",
            aws_access_key_id=os.environ["REMOTION_AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["REMOTION_AWS_SECRET_ACCESS_KEY"],
            region_name=os.environ["REMOTION_AWS_REGION"])
    return _S3


def decouper_s3(uri: str) -> tuple[str, str]:
    reste = uri[len("s3://"):]
    bucket, _, cle = reste.partition("/")
    if not bucket or not cle:
        raise ErreurEntree(f"URI S3 invalide : {uri}")
    return bucket, cle


def presigner(uri: str) -> str:
    bucket, cle = decouper_s3(uri)
    return client_s3().generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": cle},
                                              ExpiresIn=PRESIGN_S)


def telecharger(uri: str, dest: Path) -> Path:
    bucket, cle = decouper_s3(uri)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        client_s3().download_file(bucket, cle, str(dest))
    except Exception as exc:  # noqa: BLE001
        raise ErreurEntree(f"Téléchargement impossible : {uri} ({exc})") from exc
    return dest


def entree_ffmpeg(camera: str) -> str:
    if camera.startswith("s3://"):
        return presigner(camera)
    if camera.startswith(("http://", "https://")):
        return camera
    p = Path(camera)
    if not p.is_absolute():
        p = REPO / p
    if not p.exists():
        raise ErreurEntree(f"Rush introuvable : {camera}")
    return str(p)


def options_http(entree: str) -> list[str]:
    if entree.startswith(("http://", "https://")):
        return ["-reconnect", "1", "-reconnect_on_network_error", "1",
                "-reconnect_delay_max", "20", "-rw_timeout", "60000000"]
    return []


# ─── ffmpeg ──────────────────────────────────────────────────────────────────

def ffprobe_json(entree: str, *args: str) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", *args,
                        "-of", "json", entree], capture_output=True, text=True)
    if r.returncode != 0:
        raise ErreurEntree(f"ffprobe impossible : {r.stderr.strip()[-400:]}")
    return json.loads(r.stdout or "{}")


def _fraction(v: str | None) -> Fraction:
    try:
        return Fraction(v or "0")
    except (ValueError, ZeroDivisionError):
        return Fraction(0)


@dataclass
class InfoCamera:
    debut_s: float
    largeur: int
    hauteur: int
    images: int | None
    couleurs: dict


def sonder_camera(camera: str, fps: int) -> InfoCamera:
    entree = entree_ffmpeg(camera)
    j = ffprobe_json(entree, "-select_streams", "v:0", "-show_entries",
                     "stream=start_time,r_frame_rate,avg_frame_rate,width,height,nb_frames,"
                     "color_space,color_primaries,color_transfer,color_range")
    if not j.get("streams"):
        raise ErreurEntree(f"Pas de piste vidéo : {camera}")
    s = j["streams"][0]
    for cle in ("r_frame_rate", "avg_frame_rate"):
        f = _fraction(s.get(cle))
        if f and abs(float(f) - fps) > 0.01 * fps:
            raise ErreurEntree(f"{camera} : {cle} = {s.get(cle)}, attendu {fps} i/s constant.")
    nb = s.get("nb_frames")
    couleurs = {k: s[k] for k in ("color_space", "color_primaries", "color_transfer", "color_range")
                if s.get(k) and s[k] != "unknown"}
    return InfoCamera(float(s.get("start_time") or 0.0), int(s["width"]), int(s["height"]),
                      int(nb) if nb and nb.isdigit() else None, couleurs)


def filtre_geometrie(larg: int, haut: int, taille: tuple[int, int]) -> str:
    w, h = taille
    if (larg, haut) == (w, h):
        return "null"
    return (f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1")


def options_couleur(couleurs: dict) -> list[str]:
    opts = []
    for cle, opt in (("color_space", "-colorspace"), ("color_primaries", "-color_primaries"),
                     ("color_transfer", "-color_trc"), ("color_range", "-color_range")):
        if couleurs.get(cle):
            opts += [opt, couleurs[cle]]
    return opts


SHOWINFO_RE = re.compile(r"\[showinfo@(enc|chk) @ [^\]]+\] n:\s*\d+ pts:\s*(-?\d+)")
TB_RE = re.compile(r"\[showinfo@(enc|chk) @ [^\]]+\] config in time_base: (\d+)/(\d+)")


def indices_showinfo(stderr: str, debut_s: float, fps: int) -> dict[str, list[int]]:
    tb: dict[str, Fraction] = {}
    for nom, a, b in TB_RE.findall(stderr):
        tb[nom] = Fraction(int(a), int(b))
    res: dict[str, list[int]] = {"enc": [], "chk": []}
    for nom, pts in SHOWINFO_RE.findall(stderr):
        t = Fraction(int(pts)) * tb[nom]
        res[nom].append(round((float(t) - debut_s) * fps))
    return res


@dataclass
class ResultatSegment:
    indices_ok: bool
    controle: dict[int, np.ndarray]        # index caméra -> vignette grise
    secondes: float


def encoder_segment(seg: Segment, info: InfoCamera | None, taille: tuple[int, int], fps: int,
                    sortie: Path, couleurs: list[str]) -> ResultatSegment:
    """Encode un segment en MPEG-TS, horodaté à sa place dans la timeline."""
    t0 = time.time()
    w, h = taille
    decalage = f"{BASE_TS_S + seg.sortie_debut / fps:.6f}"
    fin_enc = ["-map", "[v]", "-frames:v", str(seg.images), *X264, *couleurs,
               "-fps_mode", "passthrough",
               "-output_ts_offset", decalage, "-f", "mpegts", str(sortie)]
    if seg.camera is None:
        cmd = ["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "lavfi",
               "-i", f"color=c=black:s={w}x{h}:r={fps}",
               "-filter_complex", f"[0:v]trim=end_frame={seg.images},format=yuv420p,"
                                  f"settb=1/{fps},setpts=N[v]", *fin_enc]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"noir : {r.stderr.strip()[-600:]}")
        return ResultatSegment(True, {}, time.time() - t0)

    assert info is not None
    k, n = seg.camera_debut, seg.images
    if info.images is not None and k + n > info.images:
        raise ErreurEntree(f"{seg.camera} : images {k} à {k + n - 1} demandées, "
                           f"le rush n'en a que {info.images}.")
    s0 = info.debut_s

    def t(i: float) -> str:
        return f"{s0 + i / fps:.6f}"

    voulus_chk = sorted({i for i in (k - 1, k, k + 1, k + n - 2, k + n - 1, k + n)
                         if i >= 0 and (info.images is None or i < info.images)})
    sel_chk = "+".join(f"lt(abs(t-{t(i)}),{0.5 / fps:.6f})" for i in voulus_chk)
    geo = filtre_geometrie(info.largeur, info.hauteur, taille)
    vw, vh = VIGNETTE
    graphe = (
        f"[0:v]select='gte(t,{t(k - 1.5)})*lt(t,{t(k + n + 0.5)})',split=2[e0][c0];"
        f"[e0]select='gte(t,{t(k - 0.5)})*lt(t,{t(k + n - 0.5)})',showinfo@enc=checksum=0,"
        f"{geo},format=yuv420p,settb=1/{fps},setpts=N[v];"
        f"[c0]select='{sel_chk}',showinfo@chk=checksum=0,{geo},"
        f"scale={vw}:{vh}:flags=area,format=gray[k]"
    )
    seek = max(0.0, (k - 1) / fps - MARGE_SEEK_S)
    entree = entree_ffmpeg(seg.camera)
    vignettes = sortie.with_suffix(".gray")
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-nostdin", "-y",
           *options_http(entree), "-copyts", "-noaccurate_seek", "-ss", f"{seek:.6f}",
           "-i", entree, "-filter_complex", graphe, *fin_enc,
           "-map", "[k]", "-frames:v", str(len(voulus_chk)), "-fps_mode", "passthrough",
           "-f", "rawvideo", str(vignettes)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        erreurs = [l for l in r.stderr.splitlines() if "showinfo" not in l]
        raise RuntimeError("\n".join(erreurs)[-800:])
    idx = indices_showinfo(r.stderr, s0, fps)
    attendu = list(range(k, k + n))
    ok = idx["enc"] == attendu
    if not ok:
        manque = sorted(set(attendu) - set(idx["enc"]))[:5]
        doubles = sorted(i for i, c in Counter(idx["enc"]).items() if c > 1)[:5]
        raise ErreurControle(
            f"Segment {seg.camera} [{k}, {k + n}) : {len(idx['enc'])} images lues au lieu de {n}. "
            f"Manquantes : {manque}. En double : {doubles}. "
            f"Premières lues : {idx['enc'][:3]}, dernières : {idx['enc'][-3:]}.")
    brut = np.fromfile(vignettes, dtype=np.uint8) if vignettes.exists() else np.zeros(0, np.uint8)
    vignettes.unlink(missing_ok=True)
    taille_v = vw * vh
    images = brut[: len(brut) // taille_v * taille_v].reshape(-1, vh, vw)
    if len(images) != len(idx["chk"]):
        raise ErreurControle("Vignettes de contrôle incohérentes avec showinfo.")
    controle = {i: img for i, img in zip(idx["chk"], images)}
    return ResultatSegment(ok, controle, time.time() - t0)


# ─── Contrôles de la sortie ──────────────────────────────────────────────────

def sonder_sortie(chemin: Path) -> dict:
    j = ffprobe_json(str(chemin), "-count_packets", "-show_entries",
                     "stream=index,codec_type,codec_name,width,height,r_frame_rate,pix_fmt,"
                     "sample_rate,channels,start_time,duration,duration_ts,time_base,nb_read_packets")
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    if v is None or a is None:
        raise ErreurControle("La sortie doit avoir une piste vidéo et une piste audio.")
    return {"video": v, "audio": a}


@lru_cache(maxsize=1)
def option_filtre_fichier() -> str:
    """Choisit la syntaxe de filtre fichier prise en charge par ffmpeg.

    FFmpeg 9 a retiré ``-filter_script:v``. La syntaxe générique ``-/filter:v``
    le remplace. Les images cloud actuelles utilisent encore l'ancienne option.
    """
    r = subprocess.run(["ffmpeg", "-hide_banner", "-h", "full"],
                       capture_output=True, text=True)
    return "-filter_script:v" if "-filter_script" in r.stdout else "-/filter:v"


def vignettes_sortie(chemin: Path, indices: list[int], fps: int) -> dict[int, np.ndarray]:
    """Décode toute la vidéo (erreur bloquante) et garde les images demandées en vignettes."""
    vw, vh = VIGNETTE
    uniques = sorted(set(indices))
    # Sélection par numéro d'image décodée, par blocs pour garder une expression courte.
    expr = "+".join(f"eq(n,{i})" for i in uniques) or "0"
    script = chemin.with_suffix(".select.txt")
    script.write_text(f"select='{expr}',scale={vw}:{vh}:flags=area,format=gray")
    cmd = ["ffmpeg", "-v", "error", "-nostdin", "-xerror", "-i", str(chemin), "-map", "0:v:0",
           option_filtre_fichier(), str(script), "-fps_mode", "passthrough",
           "-f", "rawvideo", "pipe:1"]
    r = subprocess.run(cmd, capture_output=True)
    script.unlink(missing_ok=True)
    if r.returncode != 0 or r.stderr.strip():
        raise ErreurControle(f"Décodage de la sortie en erreur : {r.stderr.decode()[-600:]}")
    brut = np.frombuffer(r.stdout, dtype=np.uint8)
    if len(brut) != len(uniques) * vw * vh:
        raise ErreurControle(f"Décodage : {len(brut) // (vw * vh)} vignettes au lieu de "
                             f"{len(uniques)}. Des images manquent dans la sortie.")
    return dict(zip(uniques, brut.reshape(-1, vh, vw)))


def ecart(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean(np.abs(a.astype(np.int16) - b.astype(np.int16))))


def controler_raccords(segments: list[Segment], controles: list[dict[int, np.ndarray]],
                       sortie: dict[int, np.ndarray]) -> list[dict]:
    """Chaque image de bord de segment doit ressembler à son image source attendue plus qu'aux voisines."""
    resultats = []
    for seg, ctl in zip(segments, controles):
        bords = [(seg.sortie_debut, seg.camera_debut)]
        if seg.images > 1:
            bords.append((seg.sortie_debut + seg.images - 1, seg.camera_debut + seg.images - 1))
        for j, k in bords:
            img = sortie[j]
            if seg.camera is None:
                m = float(img.mean())
                ok = m <= ECART_NOIR_MAX     # gris plein écart : noir vidéo = 0
                resultats.append({"sortie": j, "noir": True, "moyenne": round(m, 2), "ok": ok})
                continue
            if k not in ctl:
                resultats.append({"sortie": j, "camera": seg.camera, "image_camera": k,
                                  "ok": False, "raison": "image source de contrôle absente"})
                continue
            d = ecart(img, ctl[k])
            voisines = {i: ecart(img, ctl[i]) for i in (k - 1, k + 1) if i in ctl}
            dmin = min(voisines.values()) if voisines else None
            ok = d <= ECART_MAX and (dmin is None or not (dmin < RATIO_VOISINE * d and d - dmin > 0.3))
            resultats.append({"sortie": j, "camera": seg.camera, "image_camera": k,
                              "ecart": round(d, 3),
                              "voisines": {str(i): round(v, 3) for i, v in voisines.items()},
                              "decidable": dmin is not None and dmin > 1.5 * d + 0.3,
                              "ok": ok})
    return resultats


# ─── Recoupe ─────────────────────────────────────────────────────────────────

def sonder_wav(wav: Path) -> dict:
    j = ffprobe_json(str(wav), "-select_streams", "a:0", "-show_entries",
                     "stream=codec_name,sample_rate,channels,duration_ts,duration,bits_per_sample")
    if not j.get("streams"):
        raise ErreurEntree(f"Pas de piste audio : {wav}")
    s = j["streams"][0]
    if not s["codec_name"].startswith("pcm_"):
        raise ErreurEntree(f"{wav} : {s['codec_name']}, attendu un WAV PCM.")
    sr = int(s["sample_rate"])
    n = int(s.get("duration_ts") or round(float(s["duration"]) * sr))
    return {"codec": s["codec_name"], "sample_rate": sr, "channels": int(s["channels"]),
            "echantillons": n, "duree_s": n / sr}


def md5_audio(entree: Path, reechantillonner: int | None = None) -> str:
    af = ["-af", f"aresample={reechantillonner}"] if reechantillonner else []
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(entree), "-map", "0:a:0",
                        *af, "-c:a", "pcm_s24le", "-f", "md5", "-"], capture_output=True, text=True)
    if r.returncode != 0:
        raise ErreurControle(f"md5 audio : {r.stderr[-300:]}")
    return r.stdout.strip()


def recouper(segments: list[Segment], total: int, wav: Path, sortie: Path, travail: Path,
             fps: int, taille: tuple[int, int]) -> dict:
    t0 = time.time()
    travail.mkdir(parents=True, exist_ok=True)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    info_wav = sonder_wav(wav)
    duree_video = total / fps
    if abs(info_wav["duree_s"] - duree_video) > TOL_AUDIO_S:
        raise ErreurControle(
            f"WAV de {info_wav['duree_s']:.4f} s, montage de {duree_video:.4f} s "
            f"({total} images). Écart {1000 * (info_wav['duree_s'] - duree_video):+.1f} ms "
            f"> {TOL_AUDIO_S * 1000:.0f} ms.")
    sr_sortie = 48000
    reech = None if info_wav["sample_rate"] == sr_sortie else sr_sortie

    libre = shutil.disk_usage(sortie.parent).free
    estime = duree_video * DEBIT_ESTIME_MBPS * 1e6 / 8
    log(f"Disque libre {libre / 1e9:.1f} Go, sortie estimée {estime / 1e9:.1f} Go "
        f"à {DEBIT_ESTIME_MBPS} Mb/s.")
    if estime > libre:
        log("[ATTENTION] La sortie risque de ne pas tenir sur le disque.")

    infos: dict[str, InfoCamera] = {}
    for cam in dict.fromkeys(s.camera for s in segments if s.camera):
        infos[cam] = sonder_camera(cam, fps)
        i = infos[cam]
        log(f"Rush {cam} : {i.largeur}x{i.hauteur}, {i.images or '?'} images, "
            f"début {i.debut_s:.3f} s")
    premiers = [infos[s.camera].couleurs for s in segments if s.camera]
    couleurs = options_couleur(premiers[0] if premiers else {})

    tmp = sortie.with_name(sortie.stem + ".partiel.mov")
    af = ["-af", f"aresample={reech}"] if reech else []
    mux = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "mpegts", "-i", "pipe:0", "-i", str(wav),
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", *af, "-c:a", "pcm_s24le",
         "-ar", str(sr_sortie), "-f", "mov", str(tmp)],
        stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    controles: list[dict[int, np.ndarray]] = []
    journal = []
    try:
        for i, seg in enumerate(segments, 1):
            fichier = travail / f"segment-{i:04d}.ts"
            for essai in range(1, ESSAIS_SEGMENT + 1):
                try:
                    res = encoder_segment(seg, infos.get(seg.camera) if seg.camera else None,
                                          taille, fps, fichier, couleurs)
                    break
                except RuntimeError as exc:
                    fichier.unlink(missing_ok=True)
                    if essai == ESSAIS_SEGMENT or isinstance(exc, (ErreurControle, ErreurEntree)):
                        raise
                    log(f"  segment {i} : essai {essai} en échec, nouvel essai. {str(exc)[-200:]}")
                    time.sleep(3 * essai)
            octets = fichier.stat().st_size
            with fichier.open("rb") as fh:
                shutil.copyfileobj(fh, mux.stdin, 4 << 20)
            fichier.unlink()
            controles.append(res.controle)
            source = (f"{Path(seg.camera).name} [{seg.camera_debut}, "
                      f"{seg.camera_debut + seg.images})") if seg.camera else "noir"
            log(f"  segment {i}/{len(segments)} : {seg.images} images depuis {source}, "
                f"{res.secondes:.1f} s ({seg.images / fps / max(res.secondes, 1e-6):.2f}x), "
                f"{octets / 1e6:.1f} Mo")
            journal.append({"segment": i, "sortie_debut": seg.sortie_debut, "images": seg.images,
                            "camera": seg.camera, "camera_debut": seg.camera_debut,
                            "evenements": seg.evenements, "secondes": round(res.secondes, 2),
                            "octets": octets})
        mux.stdin.close()
        err = mux.stderr.read().decode(errors="replace")
        if mux.wait() != 0:
            raise ErreurControle(f"Multiplexage en erreur : {err[-800:]}")
    except BaseException:
        if mux.poll() is None:
            mux.kill()
        mux.wait()
        tmp.unlink(missing_ok=True)
        for f in travail.glob("segment-*"):
            f.unlink(missing_ok=True)
        raise
    t_encodage = time.time() - t0
    log(f"Encodage et multiplexage : {t_encodage:.1f} s.")

    # Contrôles bloquants sur le fichier final.
    t1 = time.time()
    rapport: dict = {"images_attendues": total, "duree_attendue_s": duree_video, "wav": info_wav}
    p = sonder_sortie(tmp)
    v, a = p["video"], p["audio"]
    erreurs = []
    n_paquets = int(v.get("nb_read_packets", -1))
    if n_paquets != total:
        erreurs.append(f"{n_paquets} images dans la sortie, {total} attendues")
    if (int(v["width"]), int(v["height"])) != taille:
        erreurs.append(f"taille {v['width']}x{v['height']}")
    if _fraction(v["r_frame_rate"]) != fps:
        erreurs.append(f"cadence {v['r_frame_rate']}")
    if v["codec_name"] != "h264" or v.get("pix_fmt") != "yuv420p":
        erreurs.append(f"vidéo {v['codec_name']} {v.get('pix_fmt')}")
    if a["codec_name"] != "pcm_s24le" or int(a["sample_rate"]) != sr_sortie:
        erreurs.append(f"audio {a['codec_name']} {a['sample_rate']} Hz")
    dv = float(v.get("start_time") or 0)
    da = float(a.get("start_time") or 0)
    if abs(dv - da) > TOL_DEPART_S or abs(dv) > TOL_DEPART_S:
        erreurs.append(f"départs vidéo {dv:.4f} s et audio {da:.4f} s différents")
    duree_audio = int(a["duration_ts"]) * float(_fraction(a["time_base"]))
    duree_v = n_paquets / fps
    if abs(duree_audio - duree_v) > TOL_AUDIO_S:
        erreurs.append(f"audio {duree_audio:.4f} s, vidéo {duree_v:.4f} s")
    rapport.update({"images_sortie": n_paquets, "duree_audio_s": duree_audio,
                    "duree_video_s": duree_v, "depart_video_s": dv, "depart_audio_s": da})
    if reech is None:
        identique = md5_audio(tmp) == md5_audio(wav)
        rapport["audio_identique_au_wav"] = identique
        if not identique:
            erreurs.append("audio de la sortie différent du WAV du monteur")
    else:
        rapport["audio_identique_au_wav"] = None
        rapport["audio_reechantillonne_depuis"] = info_wav["sample_rate"]

    indices = []
    for s in segments:
        indices.append(s.sortie_debut)
        indices.append(s.sortie_debut + s.images - 1)
    vign = vignettes_sortie(tmp, indices, fps)
    raccords = controler_raccords(segments, controles, vign)
    faux = [r for r in raccords if not r["ok"]]
    for r in faux[:10]:
        erreurs.append(f"raccord faux à l'image {r['sortie']} : {r}")
    rapport["raccords"] = {"verifies": len(raccords), "faux": len(faux),
                           "decidables": sum(1 for r in raccords if r.get("decidable")),
                           "detail": raccords}
    rapport["temps_controle_s"] = round(time.time() - t1, 2)
    if erreurs:
        rapport["erreurs"] = erreurs
        (travail / "rapport-echec.json").write_text(json.dumps(rapport, ensure_ascii=False,
                                                               indent=2, default=str))
        raise ErreurControle("Contrôles en échec :\n- " + "\n- ".join(erreurs) +
                             f"\nFichier partiel gardé : {tmp}")
    tmp.replace(sortie)
    rapport.update({"segments": journal, "temps_encodage_s": round(t_encodage, 2),
                    "temps_total_s": round(time.time() - t0, 2),
                    "octets_sortie": sortie.stat().st_size,
                    "secondes_par_minute_de_sortie":
                        round((time.time() - t0) / (duree_video / 60), 1)})
    return rapport


# ─── CLI ─────────────────────────────────────────────────────────────────────

FONDU_COUPE_S = 0.005        # fondu aux coupes du son reconstruit : évite les clics


def proxy_de_segment(seg: Segment, sources: Sources) -> list[tuple[int, int]]:
    """Plages [image du proxy, nombre d'images] couvertes par un segment caméra."""
    out, cam_debut, reste = [], seg.camera_debut, seg.images
    while reste > 0:
        p = next((p for p in sources.plages if p.camera == seg.camera
                  and p.camera_debut <= cam_debut < p.camera_debut + p.images), None)
        if p is None:
            raise ErreurEntree(f"Image {cam_debut} de {seg.camera} absente de sources.json.")
        n = min(reste, p.camera_debut + p.images - cam_debut)
        out.append((p.proxy_debut + cam_debut - p.camera_debut, n))
        cam_debut += n
        reste -= n
    return out


def wav_depuis_voix(segments: list[Segment], total: int, brut_sources: dict, sources: Sources,
                    fps: int, travail: Path) -> Path:
    """Son du montage reconstruit depuis voix.wav de l'étape 1, sans WAV du monteur.

    voix.wav : échantillon 0 = image 0 du proxy. Chaque segment reprend les échantillons
    de ses images. Fondu de 5 ms aux coupes non contiguës ; silence sur le noir.
    """
    import soundfile as sf

    source = brut_sources.get("audio", {}).get("wav")
    if not source:
        raise ErreurEntree("sources.json n'indique pas voix.wav (audio.wav) : fournir --wav.")
    voix = fichier_local(source, travail)
    info = sf.info(str(voix))
    sr = info.samplerate
    if sr % fps:
        raise ErreurEntree(f"voix.wav à {sr} Hz : non divisible par {fps} i/s.")
    spf = sr // fps
    nf = int(FONDU_COUPE_S * sr)
    rampe = (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, nf))).astype(np.float32)
    sortie = travail / "son-depuis-voix.wav"
    morceaux: list[tuple[int | None, int]] = []      # (échantillon source ou None, longueur)
    for seg in segments:
        if seg.camera is None:
            morceaux.append((None, seg.images * spf))
            continue
        for f, n in proxy_de_segment(seg, sources):
            morceaux.append((f * spf, n * spf))
    ecrits = 0
    with sf.SoundFile(str(voix)) as src, sf.SoundFile(str(sortie), "w", samplerate=sr,
                                                      channels=info.channels,
                                                      subtype="PCM_24", format="WAV") as out:
        for i, (debut, n) in enumerate(morceaux):
            if debut is None:
                bloc = np.zeros((n, info.channels) if info.channels > 1 else n, np.float32)
            else:
                src.seek(debut)
                bloc = src.read(n, dtype="float32")
                if len(bloc) != n:
                    raise ErreurControle(f"voix.wav trop court : {len(bloc)} échantillons lus "
                                         f"sur {n} depuis {debut}.")
                prec = morceaux[i - 1] if i else None
                suiv = morceaux[i + 1] if i + 1 < len(morceaux) else None
                if n > 2 * nf:
                    if prec is None or prec[0] is None or prec[0] + prec[1] != debut:
                        bloc[:nf] *= rampe if bloc.ndim == 1 else rampe[:, None]
                    if suiv is None or suiv[0] is None or debut + n != suiv[0]:
                        bloc[-nf:] *= rampe[::-1] if bloc.ndim == 1 else rampe[::-1, None]
            out.write(bloc)
            ecrits += n
    if ecrits != total * spf:
        raise ErreurControle(f"Son reconstruit : {ecrits} échantillons, {total * spf} attendus.")
    log(f"Son reconstruit depuis {Path(source).name} : {len(morceaux)} morceaux, "
        f"{total / fps:.2f} s, fondus de {FONDU_COUPE_S * 1000:.0f} ms aux coupes.")
    return sortie


def fichier_local(uri: str, travail: Path) -> Path:
    if uri.startswith("s3://"):
        return telecharger(uri, travail / Path(decouper_s3(uri)[1]).name)
    p = Path(uri)
    if not p.exists():
        raise ErreurEntree(f"Fichier introuvable : {uri}")
    return p


def charger_sources(projet: str, chemin: str | None, travail: Path) -> tuple[dict, str]:
    if chemin:
        return json.loads(fichier_local(chemin, travail).read_text()), chemin
    local = REPO / "outputs" / projet / "synchro" / "sources.json"
    if local.exists():
        return json.loads(local.read_text()), str(local)
    uri = f"s3://{BUCKET}/outputs/{projet}/synchro/sources.json"
    return json.loads(telecharger(uri, travail / "sources.json").read_text()), uri


def construire_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--projet", required=True)
    p.add_argument("--edl", required=True, help="EDL CMX 3600 ou FCPXML, chemin local ou s3://")
    p.add_argument("--wav", help="WAV de toute la timeline, chemin local ou s3://. Absent : "
                                 "son reconstruit depuis voix.wav de l'étape 1 avec l'EDL")
    p.add_argument("--sources", help="sources.json (défaut : outputs/P/synchro/, local puis S3)")
    p.add_argument("--sortie", type=Path, help="défaut : outputs/P/cut/<nom de l'EDL>-4k.mov")
    p.add_argument("--travail", type=Path, help="dossier des segments (défaut : out/recoupe/P)")
    p.add_argument("--debut-timeline", help="timecode de début de la timeline "
                                            "(défaut : premier événement, ou tcStart du FCPXML)")
    p.add_argument("--tc-proxy", default="00:00:00:00", help="timecode de la première image du proxy")
    p.add_argument("--clip", help="nom du clip proxy dans l'EDL (défaut : le plus fréquent)")
    p.add_argument("--inconnus-en-noir", action="store_true",
                   help="rend en noir les événements d'un autre clip au lieu d'échouer")
    p.add_argument("--taille", default=f"{TAILLE_DEFAUT[0]}x{TAILLE_DEFAUT[1]}",
                   help="taille de sortie LxH (défaut 3840x2160)")
    p.add_argument("--plan", action="store_true", help="affiche le plan et s'arrête")
    p.add_argument("--sans-envoi", action="store_true", help="n'appelle pas cloud/push_output.sh")
    return p


def main(argv: list[str] | None = None) -> int:
    args = construire_parser().parse_args(argv)
    t0 = time.time()
    try:
        if not PROJET_RE.fullmatch(args.projet):
            raise ErreurEntree(f"Nom de projet invalide : {args.projet}")
        m = re.fullmatch(r"(\d+)x(\d+)", args.taille)
        if not m:
            raise ErreurEntree(f"--taille invalide : {args.taille}")
        taille = (int(m.group(1)), int(m.group(2)))
        travail = args.travail or REPO / "out" / "recoupe" / args.projet
        travail.mkdir(parents=True, exist_ok=True)

        brut, origine = charger_sources(args.projet, args.sources, travail)
        sources = lire_sources(brut)
        fps = sources.fps
        edl = fichier_local(args.edl, travail)
        montage = lire_montage(edl, fps)
        for a in montage.avertissements:
            log(f"[ATTENTION] {a}")
        if args.debut_timeline:
            debut = tc_vers_images(args.debut_timeline, fps)
        elif montage.debut_timeline is not None:
            debut = montage.debut_timeline
        else:
            debut = min(e.rec_in for e in montage.evenements)
        clip = choisir_proxy(montage.evenements, args.clip)
        segments, total, avert = planifier(montage, sources, fps, debut,
                                           tc_vers_images(args.tc_proxy, fps), clip,
                                           args.inconnus_en_noir)
        for a in avert:
            log(f"[ATTENTION] {a}")
        log(f"Montage {montage.format} « {montage.titre} » : "
            f"{sum(1 for e in montage.evenements if e.video)} événements vidéo, clip « {clip} », "
            f"début {images_vers_tc(debut, fps)}, {total} images ({total / fps:.2f} s), "
            f"{len(segments)} segments. Sources : {origine}")
        if args.plan:
            for s in segments:
                print(json.dumps(asdict(s), ensure_ascii=False))
            return 0

        wav = (fichier_local(args.wav, travail) if args.wav else
               wav_depuis_voix(segments, total, brut, sources, fps, travail))
        try:
            info_wav = sonder_wav(wav)
        except ErreurEntree:
            raise
        ecart_s = info_wav["duree_s"] - total / fps
        if abs(ecart_s) > TOL_AUDIO_S:
            conseil = ""
            decal = round(ecart_s * fps)
            if decal > 0 and abs(ecart_s * fps - decal) < 0.25:
                conseil = (f" Si la timeline commence {decal} images avant le premier plan, "
                           f"relancer avec --debut-timeline {images_vers_tc(debut - decal, fps)}.")
            raise ErreurControle(f"WAV de {info_wav['duree_s']:.4f} s pour un montage de "
                                 f"{total / fps:.4f} s ({total} images).{conseil}")

        sortie = args.sortie or REPO / "outputs" / args.projet / "cut" / f"{edl.stem}-4k.mov"
        rapport = recouper(segments, total, wav, sortie, travail, fps, taille)
        rapport.update({
            "projet": args.projet, "edl": args.edl, "wav_entree": args.wav, "sources": origine,
            "sortie": str(sortie), "debut_timeline": images_vers_tc(debut, fps), "clip": clip,
            "date": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "avertissements": montage.avertissements + avert,
        })
        chemin_rapport = sortie.with_name(sortie.stem + ".rapport.json")
        chemin_rapport.write_text(json.dumps(rapport, ensure_ascii=False, indent=2, default=str) + "\n")
        log(f"Sortie : {sortie} ({rapport['octets_sortie'] / 1e9:.2f} Go). Rapport : {chemin_rapport}")
        log(f"Contrôles : {rapport['images_sortie']} images, audio {rapport['duree_audio_s']:.4f} s, "
            f"{rapport['raccords']['verifies']} bords de segment vérifiés. "
            f"Temps {rapport['temps_total_s']:.0f} s, "
            f"{rapport['secondes_par_minute_de_sortie']:.0f} s par minute de sortie.")
        if not args.sans_envoi:
            r = subprocess.run(["bash", str(REPO / "cloud" / "push_output.sh"), str(sortie),
                                args.projet], capture_output=True, text=True)
            if r.returncode != 0:
                raise ErreurEntree(f"Envoi impossible : {r.stderr.strip()[-600:]}")
            for ligne in r.stdout.splitlines():
                print(ligne, flush=True)
        log(f"Durée totale : {time.time() - t0:.1f} s")
        return 0
    except ErreurEntree as exc:
        print(f"[ERREUR] {exc}", file=sys.stderr)
        return 2
    except ErreurControle as exc:
        print(f"[ERREUR] {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
