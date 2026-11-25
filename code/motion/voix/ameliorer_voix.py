#!/usr/bin/env python3
"""Amélioration de la voix + Synchronisation des rushs caméra, avec proxy 1080p.

Entrées, dans s3://…/inputs/PROJET/rushs/ ou en arguments :
- l'audio maître : un fichier OBS (MOV ou MKV, micro en PCM) ou un WAV séparé ;
- 1 à 5 rushs caméra 4K 50 i/s avec son témoin.

Sorties, dans s3://…/outputs/PROJET/synchro/ :
- `proxy.mov` : les rushs caméra dans l'ordre chronologique, 1920x1080, 50 i/s,
  H.264 8 Mb/s, GOP de 25 images, timecode 00:00:00:00, image pour image ;
  audio = voix améliorée alignée, PCM 24 bits 48 kHz ;
- `voix.wav` : la même voix, échantillon 0 = image 0 du proxy ;
- `sources.json` : correspondance entre images du proxy et images des rushs 4K ;
- `rapport-rendre.json` : appairage, offsets, dérive, confiance, niveau, contrôles.

Les rushs 4K ne sont jamais écrits sur le disque. ffmpeg les lit par URL présignée.

Sous-commandes :
  analyser  appairage et synchro, sans rendu
  rendre    appairage, chaîne audio, voix alignée, proxy, contrôles, envoi S3

Les helpers S3 reprennent `cloud/transcribe.py` et `cloud/push_output.sh`.
La chaîne audio vient de `voix/chaine_audio.py`, la synchro de `voix/synchro.py`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from urllib.parse import urlparse

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import chaine_audio  # noqa: E402
import synchro  # noqa: E402
from chaine_audio import AUDIO_SR, LOUDNESS_TARGET_LUFS, lancer, log  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
BUCKET = os.environ.get("REMOTION_INPUT_BUCKET", "remotionlambda-eunorth1-08ow3rdhea")
PROJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
PRESIGN_LECTURE_S = 86400     # 24 h pour lire les rushs, le proxy peut durer des heures
PRESIGN_SORTIE_S = 604800     # 7 jours, comme cloud/push_output.sh
VERSION_CHAINE = "auto-edit-2026-09-12"  # clé de cache des masters améliorés

# Proxy
PROXY_FPS = 50
PROXY_LARGEUR = 1920
PROXY_HAUTEUR = 1080
PROXY_DEBIT = "8M"
PROXY_DEBIT_MAX = "10M"
PROXY_TAMPON = "16M"
PROXY_GOP = 25
PROXY_PRESET = os.environ.get("VOIX_PROXY_PRESET", "veryfast")
PROXY_OCTETS_PAR_S = 8.5e6 / 8 + AUDIO_SR * 3  # débit moyen x264 + PCM 24 bits
MARGE_DISQUE = 1.5e9
ECHANTILLONS_PAR_IMAGE = AUDIO_SR // PROXY_FPS  # 960
NOM_PROXY = "proxy.mov"
NOM_VOIX = "voix.wav"
NOM_SOURCES = "sources.json"
PROXY_LAMBDA_SCRIPT = (REPO / ".claude" / "skills" / "recreer-motion-design" /
                       "scripts" / "render_lambda_final.py")
PROXY_LAMBDA_SITE = os.environ.get("REMOTION_LAMBDA_SITE", "martell-motion")

# Contrôles de fin
TOL_NIVEAU_LU = 0.5
PIC_MAX_DBTP = -1.0
TOL_SYNCHRO_FINALE_MS = 10.0
FONDU_RACCORD_S = 0.010       # entre deux maîtres dans un même rush

EXT_VIDEO = {".mp4", ".mov", ".mxf", ".m4v", ".mkv", ".avi", ".mts"}
EXT_AUDIO = {".wav", ".bwf", ".aif", ".aiff", ".flac", ".m4a", ".mp3"}
# Nom par défaut d'un enregistrement OBS : "2026-09-26 10-00-00.mkv"
OBS_NOM_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ _]\d{2}-\d{2}-\d{2}")


class ErreurEntree(RuntimeError):
    """Entrées invalides ou appairage refusé. Code de sortie 2."""


class ErreurControle(RuntimeError):
    """Un contrôle de fin a échoué. Code de sortie 3."""


# ─── AWS (cloud/transcribe.py) ───────────────────────────────────────────────

def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ErreurEntree(f"Variable absente : {name}")
    return value


def aws_env() -> dict[str, str]:
    env = os.environ.copy()
    env["AWS_ACCESS_KEY_ID"] = require_env("REMOTION_AWS_ACCESS_KEY_ID")
    env["AWS_SECRET_ACCESS_KEY"] = require_env("REMOTION_AWS_SECRET_ACCESS_KEY")
    region = require_env("REMOTION_AWS_REGION")
    env["AWS_REGION"] = region
    env["AWS_DEFAULT_REGION"] = region
    env.pop("AWS_PROFILE", None)
    env.pop("AWS_SESSION_TOKEN", None)
    return env


def aws_bin() -> str:
    local = REPO / ".venv" / "bin" / "aws"
    return str(local) if local.exists() else (shutil.which("aws") or "aws")


def run_aws(arguments: list[str]) -> str:
    result = lancer([aws_bin(), *arguments], capture_output=True, text=True,
                            env=aws_env())
    if result.returncode != 0:
        raise ErreurEntree(f"aws {' '.join(arguments[:2])} : {result.stderr.strip()[-400:]}")
    return result.stdout.strip()


def presign(uri: str, expires: int = PRESIGN_LECTURE_S) -> str:
    return run_aws(["s3", "presign", uri, "--expires-in", str(expires)])


def lien_telechargement(uri: str, expires: int = PRESIGN_SORTIE_S) -> str:
    """Lien de téléchargement direct (Content-Disposition: attachment), par boto3."""
    import boto3

    env = aws_env()
    bucket, _, key = uri[5:].partition("/")
    s3 = boto3.client("s3", region_name=env["AWS_REGION"],
                      aws_access_key_id=env["AWS_ACCESS_KEY_ID"],
                      aws_secret_access_key=env["AWS_SECRET_ACCESS_KEY"])
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key,
                "ResponseContentDisposition": f'attachment; filename="{Path(key).name}"'},
        ExpiresIn=expires,
    )


def valider_projet(projet: str) -> str:
    if not PROJECT_RE.fullmatch(projet or ""):
        raise ErreurEntree(f"Nom de projet invalide : {projet}")
    return projet


# ─── Sources ─────────────────────────────────────────────────────────────────

@dataclass
class Source:
    nom: str
    entree: str                 # chemin local ou URL lisible par ffmpeg
    ident: str                  # clé de cache stable
    taille: int | None = None
    s3: str | None = None
    type: str = ""              # "maitre" ou "camera"
    origine: str = ""           # "obs", "audio" ou "camera"
    probe: dict = field(default_factory=dict, repr=False)

    @property
    def distante(self) -> bool:
        return self.entree.startswith(("http://", "https://"))

    @property
    def reference(self) -> str:
        """Adresse durable pour sources.json : URI S3, sinon chemin ou URL."""
        return self.s3 or self.entree


def _ident(*parts) -> str:
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:16]


def sources_projet(projet: str) -> list[Source]:
    prefixe = f"inputs/{projet}/rushs/"
    brut = run_aws(["s3api", "list-objects-v2", "--bucket", BUCKET, "--prefix", prefixe,
                    "--output", "json"])
    objets = json.loads(brut or "{}").get("Contents", [])
    out = []
    for o in objets:
        key = o["Key"]
        nom = key[len(prefixe):]
        if not nom or nom.endswith("/") or "/" in nom or nom.startswith("."):
            continue
        uri = f"s3://{BUCKET}/{key}"
        out.append(Source(nom=nom, entree=presign(uri), ident=_ident(uri, o.get("ETag"), o["Size"]),
                          taille=int(o["Size"]), s3=uri))
    if not out:
        raise ErreurEntree(f"Aucun rush dans s3://{BUCKET}/{prefixe}")
    return out


def source_explicite(arg: str) -> Source:
    if arg.startswith("s3://"):
        bucket, _, key = arg[5:].partition("/")
        head = json.loads(run_aws(["s3api", "head-object", "--bucket", bucket, "--key", key,
                                   "--output", "json"]))
        return Source(nom=Path(key).name, entree=presign(arg),
                      ident=_ident(arg, head.get("ETag"), head.get("ContentLength")),
                      taille=int(head.get("ContentLength", 0)), s3=arg)
    parsed = urlparse(arg)
    if parsed.scheme in {"http", "https"}:
        return Source(nom=Path(parsed.path).name, entree=arg,
                      ident=_ident(parsed.scheme, parsed.netloc, parsed.path))
    path = Path(arg).resolve()
    if not path.is_file():
        raise ErreurEntree(f"Fichier absent : {arg}")
    st = path.stat()
    return Source(nom=path.name, entree=str(path), ident=_ident(path, st.st_size, st.st_mtime_ns),
                  taille=st.st_size)


RECONNEXION = {"reconnect": "1", "reconnect_on_network_error": "1",
               "reconnect_delay_max": "30"}


def _entree_ffmpeg(src: Source) -> list[str]:
    opts = []
    if src.distante:
        for k, v in RECONNEXION.items():
            opts += [f"-{k}", v]
    return opts + ["-i", src.entree]


def _videos(streams: list[dict]) -> list[dict]:
    return [s for s in streams if s.get("codec_type") == "video"
            and not s.get("disposition", {}).get("attached_pic")]


def sonder(src: Source, maitres_forces: set[str]) -> None:
    """Classe la source. Audio seul ou vidéo avec micro PCM : maître. Sinon caméra.

    OBS enregistre le micro en PCM, les caméras DJI en AAC. Un nom OBS par défaut
    (date et heure) classe aussi en maître. `--maitre NOM` force le classement.
    """
    r = lancer(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams",
                        "-show_format", src.entree], capture_output=True, text=True)
    if r.returncode != 0:
        raise ErreurEntree(f"ffprobe refuse {src.nom} : {r.stderr.strip()[-300:]}")
    src.probe = json.loads(r.stdout)
    streams = src.probe.get("streams", [])
    videos = _videos(streams)
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    if not audios:
        raise ErreurEntree(f"{src.nom} : aucune piste audio, appairage impossible.")
    if not videos:
        src.type, src.origine = "maitre", "audio"
    elif (src.nom in maitres_forces
          or (not src.nom.upper().startswith("DJI_")
              and (str(audios[0].get("codec_name", "")).startswith("pcm_")
                   or OBS_NOM_RE.match(src.nom)))):
        src.type, src.origine = "maitre", "obs"
    else:
        src.type, src.origine = "camera", "camera"
    if src.taille is None:
        try:
            src.taille = int(src.probe["format"]["size"])
        except (KeyError, ValueError):
            src.taille = None


def _f(x, defaut=0.0) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return defaut


@dataclass
class InfoCamera:
    codec: str
    profil: str | None
    largeur: int
    hauteur: int
    pix_fmt: str | None
    fps: Fraction
    fps_moyen: Fraction
    frames: int
    av: float                   # début audio - début vidéo, en s
    creation: str | None
    debit: int | None

    @property
    def duree(self) -> float:
        return float(self.frames / self.fps)


def info_camera(src: Source) -> InfoCamera:
    streams = src.probe["streams"]
    v = _videos(streams)[0]
    a = next(s for s in streams if s.get("codec_type") == "audio")
    fps = Fraction(v.get("r_frame_rate") or v.get("avg_frame_rate") or "0/1")
    if fps <= 0:
        raise ErreurEntree(f"{src.nom} : cadence vidéo illisible.")
    moy = v.get("avg_frame_rate") or "0/1"
    fps_moyen = Fraction(moy) if moy != "0/0" else Fraction(0)
    frames = int(v["nb_frames"]) if str(v.get("nb_frames", "")).isdigit() else 0
    if frames <= 0:
        duree = _f(v.get("duration")) or _f(src.probe.get("format", {}).get("duration"))
        frames = int(round(duree * fps))
    tags = {**src.probe.get("format", {}).get("tags", {}), **v.get("tags", {})}
    return InfoCamera(
        codec=v.get("codec_name"), profil=v.get("profile"),
        largeur=int(v.get("width", 0)), hauteur=int(v.get("height", 0)),
        pix_fmt=v.get("pix_fmt"), fps=fps, fps_moyen=fps_moyen, frames=frames,
        av=_f(a.get("start_time")) - _f(v.get("start_time")),
        creation=tags.get("creation_time"),
        debit=int(v["bit_rate"]) if str(v.get("bit_rate", "")).isdigit() else None,
    )


# ─── Son témoin par plages d'octets ──────────────────────────────────────────
#
# ffmpeg lit tout le fichier pour extraire l'audio d'un MP4, même avec -vn :
# 383 Mo lus pour un rush de 381 Mo. Un rush DJI d'une heure pèse 40 Go.
# Ici, on lit la table des échantillons du MP4 (moov), puis on ne télécharge
# que les morceaux audio AAC par requêtes HTTP Range. ffmpeg décode ensuite un
# flux ADTS reconstruit. Un contrôle compare les 20 premières secondes au décodage
# direct par ffmpeg. En cas d'écart ou de format non géré : retour à ffmpeg.

TEMOIN_FILS = 16
TEMOIN_CONTROLE_S = 20.0


class FormatNonGere(RuntimeError):
    """Le MP4 sort du cas géré (AAC simple). On repasse par ffmpeg."""


class LecteurOctets:
    """Lecture par plages d'un fichier local ou d'une URL (HTTP Range)."""

    def __init__(self, entree: str):
        self.entree = entree
        self.distant = entree.startswith(("http://", "https://"))
        self._local = __import__("threading").local()
        self.taille = self._taille()

    def _session(self):
        import requests
        s = getattr(self._local, "session", None)
        if s is None:
            s = self._local.session = requests.Session()
        return s

    def _taille(self) -> int:
        if not self.distant:
            return os.path.getsize(self.entree)
        r = self._session().get(self.entree, headers={"Range": "bytes=0-0"}, timeout=60)
        r.raise_for_status()
        plage = r.headers.get("Content-Range", "")
        if "/" not in plage:
            raise FormatNonGere("le serveur ne gère pas les plages d'octets")
        return int(plage.rsplit("/", 1)[1])

    def lire(self, debut: int, n: int) -> bytes:
        if n <= 0:
            return b""
        if not self.distant:
            with open(self.entree, "rb") as f:
                f.seek(debut)
                return f.read(n)
        for essai in range(5):
            try:
                r = self._session().get(self.entree, timeout=120,
                                        headers={"Range": f"bytes={debut}-{debut + n - 1}"})
                if r.status_code == 206 and len(r.content) == n:
                    return r.content
                raise OSError(f"HTTP {r.status_code}, {len(r.content)} octets sur {n}")
            except Exception as exc:  # noqa: BLE001 - réessai réseau
                if essai == 4:
                    raise OSError(f"lecture {debut}+{n} impossible : {exc}") from exc
                time.sleep(2 ** essai)
        raise AssertionError


def _boites(donnees: bytes, debut: int = 0, fin: int | None = None):
    """Boîtes ISO BMFF contenues dans un tampon : (type, début du contenu, fin)."""
    import struct
    fin = len(donnees) if fin is None else fin
    pos = debut
    while pos + 8 <= fin:
        taille, typ = struct.unpack(">I4s", donnees[pos:pos + 8])
        entete = 8
        if taille == 1:
            taille = struct.unpack(">Q", donnees[pos + 8:pos + 16])[0]
            entete = 16
        elif taille == 0:
            taille = fin - pos
        if taille < entete or pos + taille > fin:
            raise FormatNonGere(f"boîte {typ!r} tronquée")
        yield typ.decode("latin-1"), pos + entete, pos + taille
        pos += taille


def _enfant(donnees: bytes, debut: int, fin: int, chemin: str) -> tuple[int, int] | None:
    for nom in chemin.split("/"):
        for typ, a, b in _boites(donnees, debut, fin):
            if typ == nom:
                debut, fin = a, b
                break
        else:
            return None
    return debut, fin


def _lire_moov(lecteur: LecteurOctets) -> bytes:
    import struct
    pos = 0
    while pos + 8 <= lecteur.taille:
        tete = lecteur.lire(pos, 16)
        taille, typ = struct.unpack(">I4s", tete[:8])
        if taille == 1:
            taille = struct.unpack(">Q", tete[8:16])[0]
        elif taille == 0:
            taille = lecteur.taille - pos
        if taille < 8:
            raise FormatNonGere("boîte de tête invalide")
        if typ == b"moov":
            if taille > 512 * 1024 ** 2:
                raise FormatNonGere("moov démesuré")
            return lecteur.lire(pos, taille)
        pos += taille
    raise FormatNonGere("boîte moov absente")


def _asc_aac(esds: bytes) -> bytes:
    """AudioSpecificConfig trouvé dans l'esds (descripteur de tag 5)."""
    i = 4  # version et drapeaux
    while i < len(esds):
        tag = esds[i]
        i += 1
        n = 0
        for _ in range(4):
            b = esds[i]
            i += 1
            n = (n << 7) | (b & 0x7F)
            if not b & 0x80:
                break
        if tag == 0x03:
            flags = esds[i + 2]
            i += 3 + (2 if flags & 0x80 else 0) + ((1 + esds[i + 3]) if flags & 0x40 else 0) \
                + (2 if flags & 0x20 else 0)
            continue
        if tag == 0x04:
            i += 13
            continue
        if tag == 0x05:
            return esds[i:i + n]
        i += n
    raise FormatNonGere("AudioSpecificConfig absent")


def piste_audio_mp4(lecteur: LecteurOctets) -> dict:
    """Première piste son d'un MP4 : config AAC, plages d'octets, amorce à sauter."""
    import struct
    moov = _lire_moov(lecteur)
    for typ, a, b in _boites(moov, 8):
        if typ != "trak":
            continue
        hdlr = _enfant(moov, a, b, "mdia/hdlr")
        if not hdlr or moov[hdlr[0] + 8:hdlr[0] + 12] != b"soun":
            continue
        stbl = _enfant(moov, a, b, "mdia/minf/stbl")
        stsd = _enfant(moov, *stbl, "stsd")
        entree = next(_boites(moov, stsd[0] + 8, stsd[1]))
        if entree[0] != "mp4a":
            raise FormatNonGere(f"codec audio {entree[0]}")
        version_son = struct.unpack(">H", moov[entree[1] + 8:entree[1] + 10])[0]
        saut = 28 + {0: 0, 1: 16, 2: 36}.get(version_son, 0)
        esds = _enfant(moov, entree[1] + saut, entree[2], "esds")
        if not esds:
            raise FormatNonGere("esds absent")
        asc = _asc_aac(moov[esds[0]:esds[1]])
        # stsz
        s0, _ = _enfant(moov, *stbl, "stsz")
        taille_fixe, n_ech = struct.unpack(">II", moov[s0 + 4:s0 + 12])
        tailles = (np.full(n_ech, taille_fixe, dtype=np.int64) if taille_fixe else
                   np.frombuffer(moov, dtype=">u4", count=n_ech, offset=s0 + 12).astype(np.int64))
        # stco ou co64
        co = _enfant(moov, *stbl, "stco")
        if co:
            n = struct.unpack(">I", moov[co[0] + 4:co[0] + 8])[0]
            offsets = np.frombuffer(moov, dtype=">u4", count=n, offset=co[0] + 8).astype(np.int64)
        else:
            co = _enfant(moov, *stbl, "co64")
            n = struct.unpack(">I", moov[co[0] + 4:co[0] + 8])[0]
            offsets = np.frombuffer(moov, dtype=">u8", count=n, offset=co[0] + 8).astype(np.int64)
        # stsc : échantillons par morceau
        sc = _enfant(moov, *stbl, "stsc")
        n_sc = struct.unpack(">I", moov[sc[0] + 4:sc[0] + 8])[0]
        runs = np.frombuffer(moov, dtype=">u4", count=3 * n_sc, offset=sc[0] + 8).reshape(-1, 3)
        par_morceau = np.zeros(len(offsets), dtype=np.int64)
        for k, (premier, nb, _) in enumerate(runs):
            fin_run = runs[k + 1][0] - 1 if k + 1 < len(runs) else len(offsets)
            par_morceau[premier - 1:fin_run] = nb
        if par_morceau.sum() != n_ech:
            raise FormatNonGere("tables stsc et stsz incohérentes")
        # Amorce : media_time de la première entrée non vide de elst
        amorce = 0
        elst = _enfant(moov, a, b, "edts/elst")
        if elst:
            version = moov[elst[0]]
            n_e = struct.unpack(">I", moov[elst[0] + 4:elst[0] + 8])[0]
            pos = elst[0] + 8
            for _ in range(n_e):
                if version == 1:
                    _, media = struct.unpack(">Qq", moov[pos:pos + 16])
                    pos += 20
                else:
                    _, media = struct.unpack(">Ii", moov[pos:pos + 8])
                    pos += 12
                if media >= 0:
                    amorce = int(media)
                    break
        mdhd = _enfant(moov, a, b, "mdia/mdhd")
        v = moov[mdhd[0]]
        echelle = struct.unpack(">I", moov[mdhd[0] + (20 if v == 1 else 12):][:4])[0]
        # Plages : un morceau = échantillons contigus
        fins_morceaux = np.cumsum(par_morceau)
        debuts_morceaux = fins_morceaux - par_morceau
        cumul = np.concatenate([[0], np.cumsum(tailles)])
        plages = [(int(offsets[c]), int(cumul[fins_morceaux[c]] - cumul[debuts_morceaux[c]]))
                  for c in range(len(offsets)) if par_morceau[c]]
        return {"asc": asc, "tailles": tailles, "plages": plages, "amorce": amorce,
                "echelle": echelle, "morceaux": int((par_morceau > 0).sum())}
    raise FormatNonGere("aucune piste son")


def _entete_adts(asc: bytes, n: int) -> bytes:
    aot = asc[0] >> 3
    sfi = ((asc[0] & 0x07) << 1) | (asc[1] >> 7)
    canaux = (asc[1] >> 3) & 0x0F
    if aot not in (1, 2, 3, 4) or sfi > 12 or canaux == 0 or canaux > 7:
        raise FormatNonGere(f"AAC hors cas simple (type {aot}, fréquence {sfi}, canaux {canaux})")
    lg = n + 7
    return bytes([0xFF, 0xF1, ((aot - 1) << 6) | (sfi << 2) | (canaux >> 2),
                  ((canaux & 3) << 6) | (lg >> 11), (lg >> 3) & 0xFF,
                  ((lg & 7) << 5) | 0x1F, 0xFC])


FREQUENCES_AAC = [96000, 88200, 64000, 48000, 44100, 32000, 24000, 22050, 16000, 12000,
                  11025, 8000, 7350]


def temoin_par_plages(src: Source, sortie_adts: Path) -> tuple[int, dict]:
    """Écrit le flux ADTS de la piste son.

    Retourne l'amorce à sauter (en échantillons décodés) et des statistiques.
    """
    lecteur = LecteurOctets(src.entree)
    piste = piste_audio_mp4(lecteur)
    asc = piste["asc"]
    _entete_adts(asc, 0)  # refuse tôt les AAC non gérés
    plages = piste["plages"]
    # Par URL : environ 25 ms par requête (16 fils) contre 20 Mo/s en lecture entière.
    # Un MP4 à un morceau audio par trame AAC coûterait plus cher par plages.
    if lecteur.distant and len(plages) * 0.025 > lecteur.taille / 40e6:
        raise FormatNonGere(f"{len(plages)} morceaux audio, lecture entière plus rapide")
    with ThreadPoolExecutor(TEMOIN_FILS) as pool:
        blocs = list(pool.map(lambda p: lecteur.lire(*p), plages))
    tailles = piste["tailles"]
    k = 0
    with open(sortie_adts, "wb") as f:
        for bloc in blocs:
            pos = 0
            while pos < len(bloc):
                n = int(tailles[k])
                f.write(_entete_adts(asc, n))
                f.write(bloc[pos:pos + n])
                pos += n
                k += 1
    if k != len(tailles):
        raise FormatNonGere(f"{k} trames lues sur {len(tailles)}")
    sr = FREQUENCES_AAC[((asc[0] & 0x07) << 1) | (asc[1] >> 7)]
    amorce = int(round(piste["amorce"] * sr / piste["echelle"]))
    stats = {"requetes": len(plages), "octets": int(sum(n for _, n in plages)),
             "taille_fichier": lecteur.taille}
    return amorce, stats


def _decoder_16k(cmd_entree: list[str], filtre: str = "", duree: float | None = None) -> np.ndarray:
    cmd = ["ffmpeg", "-v", "error", *cmd_entree, "-map", "0:a:0", "-vn"]
    if duree:
        cmd += ["-t", f"{duree:.3f}"]
    if filtre:
        cmd += ["-af", filtre]
    cmd += ["-ac", "1", "-ar", str(synchro.XCORR_SR), "-f", "f32le", "-"]
    r = lancer(cmd, capture_output=True)
    if r.returncode != 0 or not r.stdout:
        raise ErreurEntree(f"décodage audio : {r.stderr.decode(errors='replace')[-300:]}")
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


# ─── Extraction audio avec cache ─────────────────────────────────────────────

def _via_plages(src: Source, cache: Path) -> tuple[np.ndarray, dict]:
    adts = cache / f"{src.ident}.adts"
    try:
        amorce, stats = temoin_par_plages(src, adts)
        filtre = f"atrim=start_sample={amorce},asetpts=PTS-STARTPTS" if amorce else ""
        x = _decoder_16k(["-f", "aac", "-i", str(adts)], filtre)
    finally:
        adts.unlink(missing_ok=True)
    # Contrôle : les premières secondes doivent égaler le décodage direct du MP4.
    ref = _decoder_16k(_entree_ffmpeg(src), duree=TEMOIN_CONTROLE_S)
    n = min(len(ref), len(x)) - synchro.XCORR_SR // 2
    if n < synchro.XCORR_SR:
        raise FormatNonGere("contrôle trop court")
    ecart = float(np.max(np.abs(ref[:n] - x[:n])))
    if ecart > 1e-3:
        raise FormatNonGere(f"écart {ecart:.2e} avec le décodage direct")
    stats["ecart_controle"] = ecart
    return x, stats


def extraire_16k_camera(src: Source, cache: Path) -> np.ndarray:
    """Son témoin en 16 kHz mono float32, mis en cache.

    MP4 ou MOV : seuls les morceaux audio sont téléchargés (voir plus haut).
    Autre conteneur ou échec : ffmpeg lit tout le fichier.
    """
    chemin = cache / f"{src.ident}_16k.f32"
    if chemin.is_file():
        return np.fromfile(chemin, dtype=np.float32)
    t = time.time()
    x = None
    methode = "ffmpeg, fichier entier"
    if "mp4" in src.probe.get("format", {}).get("format_name", ""):
        try:
            x, stats = _via_plages(src, cache)
            methode = (f"plages d'octets, {stats['requetes']} requêtes, "
                       f"{stats['octets'] / 1e6:.1f} Mo sur {stats['taille_fichier'] / 1e6:.0f} Mo")
        except (FormatNonGere, OSError, ErreurEntree, ValueError, IndexError, StopIteration,
                TypeError) as exc:
            log(f"  [AVERTISSEMENT] {src.nom} : lecture par plages impossible ({exc}). "
                "ffmpeg lit tout le fichier.")
    if x is None:
        x = _decoder_16k(_entree_ffmpeg(src))
    tmp = chemin.with_suffix(".part")
    x.tofile(tmp)
    tmp.replace(chemin)
    log(f"  Son témoin 16 kHz de {src.nom} : {len(x) / synchro.XCORR_SR / 60:.1f} min "
        f"en {time.time() - t:.1f} s ({methode})")
    return x


def brut_48k(src: Source, cache: Path) -> Path:
    """Audio maître brut en WAV 48 kHz mono flottant, extrait une seule fois.

    Le fichier OBS peut peser plusieurs Go : on ne le lit qu'une fois.
    La version 16 kHz de l'appairage et la chaîne audio partent de ce WAV.
    """
    chemin = cache / f"{src.ident}_48k.wav"
    if chemin.is_file():
        return chemin
    t = time.time()
    part = chemin.with_suffix(".part.wav")
    r = lancer(["ffmpeg", "-y", "-v", "error", *_entree_ffmpeg(src), "-map", "0:a:0",
                        "-vn", "-ac", "1", "-ar", str(AUDIO_SR), "-c:a", "pcm_f32le", str(part)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise ErreurEntree(f"Extraction audio de {src.nom} : {r.stderr[-300:]}")
    part.replace(chemin)
    log(f"  Audio maître 48 kHz de {src.nom} en {time.time() - t:.1f} s")
    return chemin


def extraire_16k_maitre(src: Source, cache: Path) -> np.ndarray:
    chemin = cache / f"{src.ident}_16k.f32"
    if chemin.is_file():
        return np.fromfile(chemin, dtype=np.float32)
    import soundfile as sf
    import soxr
    x48, _ = sf.read(str(brut_48k(src, cache)), dtype="float32")
    x = soxr.resample(x48, AUDIO_SR, synchro.XCORR_SR, quality="HQ").astype(np.float32)
    tmp = chemin.with_suffix(".part")
    x.tofile(tmp)
    tmp.replace(chemin)
    return x


# ─── Analyse : appairage et synchro ──────────────────────────────────────────

def _cle_naturelle(nom: str):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", nom)]


def _intervalles_moins(a: float, b: float, pris: list[tuple[float, float]]):
    """[a, b) privé des intervalles déjà pris."""
    morceaux = [(a, b)]
    for x, y in pris:
        suite = []
        for s, e in morceaux:
            if y <= s or x >= e:
                suite.append((s, e))
                continue
            if x > s:
                suite.append((s, x))
            if y < e:
                suite.append((y, e))
        morceaux = suite
    return [(s, e) for s, e in morceaux if e - s > 1e-3]


# Écart de durée toléré entre un secours et le son témoin de son rush.
TOL_DUREE_SECOURS_S = 0.5


def paire_secours(camera: str, secours: str) -> dict:
    """Paire d'un rush avec son propre son, extrait par extraire_audio_camera.py.

    Même flux, même horloge : échantillon 0 du WAV = échantillon 0 du son témoin
    (contrôlé à l'extraction sur 20 s). Offset et dérive nuls par construction,
    même pour un faux départ de quelques secondes que GCC-PHAT ne peut pas mesurer.
    Le résidu final de voix.wav contrôle quand même la synchro.
    """
    return {"camera": camera, "maitre": secours, "accepte": True, "secours": True,
            "a": 0.0, "d": 0.0, "confiance": None, "residu_ms": 0.0, "points": [],
            "derive_source": "même horloge (son du rush)"}


def couvrir_rush(duree: float, av: float, acceptees: list[dict],
                 durees_maitres: dict[str, float]) -> tuple[list[dict], list[tuple[float, float]]]:
    """Couverture d'un rush en temps vidéo τ = u + av.

    Les maîtres principaux (OBS, WAV) passent d'abord, par confiance décroissante.
    Les secours (son du rush) passent après, quelle que soit leur confiance :
    ils ne remplissent que ce que les principaux laissent vide.
    Retourne les segments triés et les trous restants.
    """
    pris: list[tuple[float, float]] = []
    segments = []
    for p in sorted(acceptees, key=lambda p: (bool(p.get("secours")), -(p.get("confiance") or 0.0))):
        dur_w = durees_maitres[p["maitre"]]
        a, d = p["a"], p["d"]
        debut = max(0.0, -a / (1 + d) + av)
        fin = min(duree, (dur_w - a) / (1 + d) + av)
        for s, e in _intervalles_moins(debut, fin, pris):
            segments.append({"maitre": p["maitre"], "tau_debut": s, "tau_fin": e,
                             "a": a, "d": d, "confiance": p.get("confiance"),
                             "secours": bool(p.get("secours"))})
            pris.append((s, e))
    segments.sort(key=lambda s: s["tau_debut"])
    trous = _intervalles_moins(0.0, duree, [(s["tau_debut"], s["tau_fin"]) for s in segments])
    return segments, trous


def analyser(sources: list[Source], travail: Path, maitres_forces: set[str],
             secours: list[Source] | None = None) -> dict:
    """Appairage et couverture de chaque rush.

    `secours` : son intégré des rushs (`audio-camera/<rush>.wav`). Chacun ne sert
    qu'à son propre rush, après tous les maîtres principaux (voir `couvrir_rush`).
    """
    t0 = time.time()
    cache = travail / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    secours = list(secours or [])
    with ThreadPoolExecutor(4) as pool:
        list(pool.map(lambda s: sonder(s, maitres_forces), sources + secours))
    maitres = sorted([s for s in sources if s.type == "maitre"],
                     key=lambda s: _cle_naturelle(s.nom))
    cameras = [s for s in sources if s.type == "camera"]
    if not maitres:
        raise ErreurEntree("Aucun audio maître parmi les entrées (fichier OBS ou WAV).")
    if not cameras:
        raise ErreurEntree("Aucun rush caméra parmi les entrées.")
    for s in sources:
        ext = Path(s.nom).suffix.lower()
        attendu = EXT_VIDEO if s.origine in {"camera", "obs"} else EXT_AUDIO
        if ext and ext not in attendu:
            log(f"  [AVERTISSEMENT] {s.nom} classé {s.type} d'après son contenu.")
    infos = {c.nom: info_camera(c) for c in cameras}
    avertissements = []
    # Secours : un WAV par rush, apparié seulement avec le rush du même nom.
    secours_de: dict[str, Source] = {}
    for s in secours:
        if s.type != "maitre":
            raise ErreurEntree(f"Secours {s.nom} : fichier vidéo, un WAV est attendu.")
        rush = [c for c in cameras if Path(c.nom).stem == Path(s.nom).stem]
        if not rush:
            log(f"  Secours {s.nom} : aucun rush de ce nom, ignoré.")
            continue
        secours_de[rush[0].nom] = s
    log(f"Entrées : {len(maitres)} audio(s) maître(s) "
        f"({', '.join(f'{m.nom} [{m.origine}]' for m in maitres)}), "
        f"{len(cameras)} rush(s) caméra, {len(secours_de)} secours (son des rushs).")

    t = time.time()
    with ThreadPoolExecutor(4) as pool:
        f_m = {m.nom: pool.submit(extraire_16k_maitre, m, cache) for m in maitres}
        f_c = {c.nom: pool.submit(extraire_16k_camera, c, cache) for c in cameras}
        f_s = {s.nom: pool.submit(extraire_16k_maitre, s, cache) for s in secours_de.values()}
        p_maitre = {n: synchro.Piste(n, f.result()) for n, f in f_m.items()}
        p_cam = {n: synchro.Piste(n, f.result()) for n, f in f_c.items()}
        p_secours = {n: synchro.Piste(n, f.result()) for n, f in f_s.items()}
    temps_extraction = time.time() - t

    t = time.time()
    # Son caméra extrait (voix/extraire_audio_camera.py) : le WAV porte le nom du rush.
    # Il ne s'apparie qu'avec lui. Un appairage croisé ne peut être qu'un faux positif.
    propre = {c.nom: m.nom for c in cameras for m in maitres
              if m.origine == "audio" and Path(m.nom).stem == Path(c.nom).stem}
    paires = []
    for c in cameras:
        for m in maitres:
            if c.nom in propre and m.nom != propre[c.nom]:
                continue
            r = synchro.mesurer_paire(p_cam[c.nom], p_maitre[m.nom])
            etat = "OK" if r["accepte"] else f"non ({r.get('raison')})"
            log(f"  {c.nom} ↔ {m.nom} : {etat}, "
                f"confiance {r.get('confiance', r['confiance_grossiere'])}")
            paires.append(r)
    # La dérive globale vient des maîtres principaux seulement : un secours partage
    # l'horloge de son rush, il n'a pas de dérive.
    derive_globale = synchro.appliquer_derive_globale(paires)
    for c in cameras:
        s = secours_de.get(c.nom)
        if s is None:
            continue
        ecart = p_secours[s.nom].duree - p_cam[c.nom].duree
        if abs(ecart) > TOL_DUREE_SECOURS_S:
            avertissements.append(f"Secours {s.nom} écarté : {ecart:+.2f} s d'écart de durée "
                                  f"avec le son de {c.nom} (WAV périmé ?).")
            continue
        paires.append(paire_secours(c.nom, s.nom))
    temps_appairage = time.time() - t
    durees = {n: p.duree for n, p in {**p_maitre, **p_secours}.items()}

    refus = []
    cams_out = []
    for c in cameras:
        inf = infos[c.nom]
        acceptees = [p for p in paires if p["camera"] == c.nom and p["accepte"]]
        if not acceptees:
            detail = ", ".join(
                f"{p['maitre']} : confiance {p.get('confiance', p['confiance_grossiere'])}"
                f" ({p.get('raison')})" for p in paires if p["camera"] == c.nom)
            refus.append(f"{c.nom} n'a aucune correspondance fiable. {detail}")
            continue
        segments, trous = couvrir_rush(inf.duree, inf.av, acceptees, durees)
        couvert = sum(s["tau_fin"] - s["tau_debut"] for s in segments)
        plages_secours = [(s["tau_debut"], s["tau_fin"]) for s in segments if s["secours"]]
        couvert_secours = sum(e - s for s, e in plages_secours)
        if plages_secours:
            sans_principal = not any(not p.get("secours") for p in acceptees)
            avertissements.append(
                f"{c.nom} : {couvert_secours:.2f} s couvertes par le son caméra (secours"
                + (", aucun maître principal" if sans_principal else "") + ") "
                + ", ".join(f"[{s:.2f} ; {e:.2f}]" for s, e in plages_secours))
        if trous:
            avertissements.append(
                f"{c.nom} : {sum(e - s for s, e in trous):.2f} s sans aucun audio, "
                "remplies de silence " + ", ".join(f"[{s:.2f} ; {e:.2f}]" for s, e in trous))
        cams_out.append({
            "nom": c.nom, "s3": c.s3, "reference": c.reference,
            "codec": inf.codec, "profil": inf.profil,
            "largeur": inf.largeur, "hauteur": inf.hauteur,
            "resolution": f"{inf.largeur}x{inf.hauteur}", "pix_fmt": inf.pix_fmt,
            "fps": f"{inf.fps.numerator}/{inf.fps.denominator}",
            "fps_moyen": f"{inf.fps_moyen.numerator}/{inf.fps_moyen.denominator}",
            "frames": inf.frames,
            "duree_s": round(inf.duree, 6), "av_ms": round(inf.av * 1000, 3),
            "creation": inf.creation, "debit_video": inf.debit, "taille": c.taille,
            "segments": [{**s, "tau_debut": round(s["tau_debut"], 6),
                          "tau_fin": round(s["tau_fin"], 6), "offset_s": round(s["a"], 6),
                          "derive_us_s": round(s["d"] * 1e6, 3)} for s in segments],
            "couverture_pct": round(100 * couvert / inf.duree, 3) if inf.duree else 0.0,
            "couverture_obs_pct": (round(100 * (couvert - couvert_secours) / inf.duree, 3)
                                   if inf.duree else 0.0),
            "couverture_secours_pct": (round(100 * couvert_secours / inf.duree, 3)
                                       if inf.duree else 0.0),
            "secours": secours_de[c.nom].nom if c.nom in secours_de else None,
            "plages_secours": [[round(s, 3), round(e, 3)] for s, e in plages_secours],
            "trous": [[round(s, 3), round(e, 3)] for s, e in trous],
        })
    if refus:
        raise ErreurEntree("Appairage refusé :\n  " + "\n  ".join(refus))

    # Ordre chronologique : date de création caméra, sinon nom de fichier.
    if (all(c["creation"] for c in cams_out)
            and len({c["creation"] for c in cams_out}) == len(cams_out)):
        cams_out.sort(key=lambda c: (c["creation"], _cle_naturelle(c["nom"])))
        critere = "creation_time des rushs caméra"
    else:
        cams_out.sort(key=lambda c: _cle_naturelle(c["nom"]))
        critere = "nom de fichier (creation_time absent ou identique)"
    # Contrôle : deux rushs sur le même maître doivent suivre sa chronologie.
    for i, c1 in enumerate(cams_out):
        for c2 in cams_out[i + 1:]:
            for s1 in c1["segments"]:
                for s2 in c2["segments"]:
                    t1 = s1["a"] + (1 + s1["d"]) * (s1["tau_debut"] - c1["av_ms"] / 1000)
                    t2 = s2["a"] + (1 + s2["d"]) * (s2["tau_debut"] - c2["av_ms"] / 1000)
                    if s1["maitre"] == s2["maitre"] and t2 < t1:
                        avertissements.append(
                            f"Ordre : {c2['nom']} précède {c1['nom']} dans {s1['maitre']}.")
    for i, c in enumerate(cams_out, 1):
        c["ordre"] = i
    utilises = sorted({s["maitre"] for c in cams_out for s in c["segments"]})
    for m in maitres:
        if m.nom not in utilises:
            avertissements.append(f"{m.nom} ne correspond à aucun rush caméra, ignoré.")
    secours_tous = list(secours_de.values())
    for a in avertissements:
        log(f"  [AVERTISSEMENT] {a}")

    for p in paires:
        if "a" in p:
            p["offset_s"] = round(p["a"], 6)
            p["derive_us_s"] = round(p["d"] * 1e6, 3)
    return {
        "maitres": [{"nom": m.nom, "origine": m.origine, "s3": m.s3,
                     "duree_s": round(p_maitre[m.nom].duree, 3),
                     "taille": m.taille, "utilise": m.nom in utilises, "secours": False}
                    for m in maitres]
                   + [{"nom": m.nom, "origine": "secours", "s3": m.s3,
                       "duree_s": round(p_secours[m.nom].duree, 3),
                       "taille": m.taille, "utilise": m.nom in utilises, "secours": True}
                      for m in secours_tous],
        "cameras": cams_out,
        "ordre_critere": critere,
        "paires": paires,
        "derive_globale_us_s": (round(derive_globale * 1e6, 3)
                                if derive_globale is not None else None),
        "avertissements": avertissements,
        "temps_s": {"extraction_16k": round(temps_extraction, 2),
                    "appairage": round(temps_appairage, 2),
                    "analyse": round(time.time() - t0, 2)},
    }


def afficher_analyse(analyse: dict) -> None:
    log("")
    log(f"Ordre chronologique ({analyse['ordre_critere']}) :")
    for c in analyse["cameras"]:
        log(f"  {c['ordre']}. {c['nom']}  {c['duree_s']:.2f} s  {c['frames']} images  "
            f"{c['codec']} {c['resolution']} {c['fps']}  couverture {c['couverture_pct']:.2f} % "
            f"(maître {c['couverture_obs_pct']:.2f} %, secours {c['couverture_secours_pct']:.2f} %)")
        for s in c["segments"]:
            log(f"       {s['maitre']}  τ {s['tau_debut']:.3f} → {s['tau_fin']:.3f} s  "
                f"offset {s['offset_s']:+.4f} s  dérive {s['derive_us_s']:+.2f} µs/s  "
                + ("secours (son du rush)" if s.get("secours") else f"confiance {s['confiance']}"))
    for p in analyse["paires"]:
        if p["accepte"]:
            log(f"  Paire {p['camera']} ↔ {p['maitre']} : résidu {p['residu_ms']} ms, "
                f"{len(p['points'])} points, dérive {p['derive_source']}")
    if analyse["derive_globale_us_s"] is not None:
        log(f"Dérive globale : {analyse['derive_globale_us_s']:+.2f} µs/s")


# ─── Voix alignée ────────────────────────────────────────────────────────────

def _lire_master(chemin: Path, t_debut: float, d: float, n_out: int) -> np.ndarray:
    """Tranche du master amélioré, recalée par rééchantillonnage de dérive."""
    import soundfile as sf
    info = sf.info(str(chemin))
    marge = 4800
    i_ent = math.floor(t_debut * AUDIO_SR)
    lo = max(0, i_ent - 2 * marge)
    hi = min(info.frames, i_ent + int(math.ceil(n_out * (1 + d))) + 3 * marge)
    if hi <= lo:
        return np.zeros(n_out, dtype=np.float32)
    bloc, _ = sf.read(str(chemin), start=lo, stop=hi, dtype="float32", always_2d=False)
    return synchro.extraire_recale(bloc, t_debut - lo / AUDIO_SR, d, n_out, sr=AUDIO_SR,
                                   marge=marge)


def _fondu(n: int, entree: bool) -> np.ndarray:
    x = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, n, dtype=np.float64))
    return (x if entree else x[::-1]).astype(np.float32)


def audio_rush(cam: dict, masters: dict[str, Path]) -> np.ndarray:
    """Audio d'un rush : échantillon 0 = image 0, 960 échantillons par image."""
    n = cam["frames"] * ECHANTILLONS_PAR_IMAGE
    out = np.zeros(n, dtype=np.float32)
    nf = int(FONDU_RACCORD_S * AUDIO_SR)
    for s in cam["segments"]:
        ns = int(round(s["tau_debut"] * AUDIO_SR))
        ne = min(n, int(round(s["tau_fin"] * AUDIO_SR)))
        if ne <= ns:
            continue
        # t_w = a + (1 + d) · u, avec u = τ - av
        t_w = s["a"] + (1 + s["d"]) * (ns / AUDIO_SR - cam["av_ms"] / 1000)
        bloc = _lire_master(masters[s["maitre"]], t_w, s["d"], ne - ns)
        if ns > 0 and ne - ns > 2 * nf:
            bloc[:nf] *= _fondu(nf, True)
        if ne < n and ne - ns > 2 * nf:
            bloc[-nf:] *= _fondu(nf, False)
        out[ns:ne] = bloc
    return out


def ecrire_voix(cams: list[dict], masters: dict[str, Path], pistes_cam: dict[str, synchro.Piste],
                sortie: Path) -> tuple[list[dict], dict]:
    """Écrit voix.wav rush par rush, mesure les résidus de synchro puis le niveau."""
    import soundfile as sf
    import soxr

    residus = []
    with sf.SoundFile(str(sortie), "w", samplerate=AUDIO_SR, channels=1,
                      subtype="PCM_24", format="WAV") as f:
        for c in cams:
            x = audio_rush(c, masters)
            f.write(x)
            final16 = soxr.resample(x, AUDIO_SR, synchro.XCORR_SR, quality="HQ").astype(np.float32)
            for r in synchro.residus_finaux(final16, pistes_cam[c["nom"]], c["av_ms"] / 1000):
                residus.append({"camera": c["nom"], **r})
            del x, final16
    return residus, chaine_audio.mesurer_niveau(str(sortie))


def ameliorer_masters(analyse: dict, sources: dict[str, Source], travail: Path,
                      denoise: bool) -> tuple[dict[str, Path], dict]:
    """Chaîne audio une seule fois par audio maître complet. Masters mis en cache."""
    masters, rapports = {}, {}
    cache = travail / "cache"
    a_faire = []
    for m in analyse["maitres"]:
        if not m["utilise"]:
            continue
        src = sources[m["nom"]]
        cle = _ident(src.ident, denoise, VERSION_CHAINE)
        master = cache / f"{cle}_voix.wav"
        meta = master.with_suffix(".json")
        masters[m["nom"]] = master
        if master.is_file() and meta.is_file():
            log(f"Master amélioré de {m['nom']} : cache.")
            rapports[m["nom"]] = {**json.loads(meta.read_text()), "cache": True}
            continue
        a_faire.append((m, src, master, meta))
    # Plusieurs maîtres : un processus par maître (DeepFilterNet et Silero tournent sur
    # un fil chacun), le plus long d'abord. VOIX_CHAINE_PROCESSUS borne le nombre.
    a_faire.sort(key=lambda x: -x[0]["duree_s"])
    n_proc = max(1, min(len(a_faire), int(os.environ.get("VOIX_CHAINE_PROCESSUS",
                                                         os.cpu_count() or 1))))
    with ThreadPoolExecutor(4) as pool:
        bruts = list(pool.map(lambda x: brut_48k(x[1], cache), a_faire))
    if a_faire:
        log(f"Chaîne audio sur {len(a_faire)} maître(s), {n_proc} processus...")
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    # spawn : torch est déjà chargé dans ce processus. Un fork hérite de ses fils
    # et bloque l'enfant sur un verrou (vu le 27/09/2026).
    with ProcessPoolExecutor(n_proc, mp_context=multiprocessing.get_context("spawn")) as pool:
        futurs = [pool.submit(chaine_audio.ameliorer_wav, str(brut), str(master) + ".part.wav",
                              denoise=denoise)
                  for (_, _, master, _), brut in zip(a_faire, bruts)]
        for (m, _, master, meta), brut, futur in zip(a_faire, bruts, futurs):
            rapport = futur.result()
            Path(str(master) + ".part.wav").replace(master)
            brut.unlink(missing_ok=True)   # le 16 kHz reste en cache pour l'appairage
            meta.write_text(json.dumps(rapport, ensure_ascii=False, indent=2))
            rapports[m["nom"]] = rapport
            log(f"  {m['nom']} ({m['duree_s'] / 60:.1f} min) : {rapport['temps_s']['total']:.1f} s, "
                f"soit {rapport['temps_par_minute_s']:.2f} s par minute d'audio.")
    return masters, rapports


# ─── Proxy ───────────────────────────────────────────────────────────────────
#
# Un décodeur ffmpeg par rush, lancés l'un après l'autre, écrit des images brutes
# 1080p dans l'entrée standard d'un seul encodeur. L'encodeur numérote les images
# dans l'ordre d'arrivée : image f du proxy = f-ième image décodée. Aucun horodatage
# de conteneur n'intervient. Le démuxeur concat décalait les rushs d'une image
# quand l'audio AAC démarrait avant la vidéo (amorce de l'encodeur AAC).

def commande_decodeur(src: Source, progression: Path) -> list[str]:
    """Rush lu par URL, toutes les images décodées, mises en 1080p, sans horodatage."""
    vf = (f"scale={PROXY_LARGEUR}:{PROXY_HAUTEUR}:force_original_aspect_ratio=decrease"
          f":flags=bicubic,pad={PROXY_LARGEUR}:{PROXY_HAUTEUR}:(ow-iw)/2:(oh-ih)/2,"
          f"setsar=1,format=yuv420p")
    return ["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-loglevel", "warning",
            "-progress", str(progression), *_entree_ffmpeg(src),
            "-map", "0:v:0", "-an", "-sn", "-dn", "-vf", vf, "-fps_mode", "passthrough",
            "-f", "rawvideo", "-pix_fmt", "yuv420p", "pipe:1"]


def commande_encodeur(voix: str, sortie: Path, progression: Path) -> list[str]:
    """Images brutes à 50 i/s, H.264 8 Mb/s, GOP fixe de 25, sans images B, PCM 24 bits.

    Sans images B, le MOV n'a pas de liste d'édition : l'image 0 est la même partout.
    """
    reconnexion = ([opt for k, v in RECONNEXION.items() for opt in (f"-{k}", v)]
                   if voix.startswith(("http://", "https://")) else [])
    return [
        "ffmpeg", "-nostdin", "-y", "-hide_banner", "-nostats", "-loglevel", "warning",
        "-progress", str(progression),
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        "-video_size", f"{PROXY_LARGEUR}x{PROXY_HAUTEUR}", "-framerate", str(PROXY_FPS),
        "-thread_queue_size", "64", "-i", "pipe:0",
        *reconnexion, "-i", voix,
        "-map", "0:v:0", "-map", "1:a:0", "-map_metadata", "-1",
        "-c:v", "libx264", "-preset", PROXY_PRESET, "-profile:v", "high",
        "-b:v", PROXY_DEBIT, "-maxrate", PROXY_DEBIT_MAX, "-bufsize", PROXY_TAMPON,
        "-g", str(PROXY_GOP), "-keyint_min", str(PROXY_GOP), "-sc_threshold", "0",
        "-bf", "0", "-pix_fmt", "yuv420p",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-color_range", "tv",
        "-c:a", "pcm_s24le", "-ar", str(AUDIO_SR), "-ac", "1",
        "-timecode", "00:00:00:00", "-video_track_timescale", str(PROXY_FPS * 100),
        "-f", "mov", str(sortie),
    ]


def _lire_progression(chemin: Path) -> dict[str, str]:
    etat: dict[str, str] = {}
    try:
        for ligne in chemin.read_text(errors="replace").splitlines():
            k, _, v = ligne.partition("=")
            etat[k.strip()] = v.strip()
    except OSError:
        pass
    return etat


def _arreter(*procs: subprocess.Popen | None) -> None:
    for p in procs:
        if p is not None and p.poll() is None:
            p.kill()
            p.wait()


def fabriquer_proxy(cams: list[dict], sources: dict[str, Source], voix: str, sortie: Path,
                    travail: Path) -> tuple[float, list[int]]:
    """Fabrique le proxy. Retourne la durée et le nombre d'images décodées par rush."""
    images = sum(c["frames"] for c in cams)
    log(f"Proxy {sortie.name} : {images} images ({images / PROXY_FPS / 60:.1f} min), "
        f"x264 {PROXY_PRESET}...")
    prog_enc = travail / "proxy.encodeur.progress"
    prog_dec = travail / "proxy.decodeur.progress"
    journal = travail / "proxy.ffmpeg.log"
    t = time.time()
    decodees: list[int] = []
    enc = dec = None
    with open(journal, "w") as err_f:
        try:
            enc = subprocess.Popen(commande_encodeur(voix, sortie, prog_enc),
                                   stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=err_f)
            assert enc.stdin is not None
            dernier = time.time()
            for c in cams:
                prog_dec.unlink(missing_ok=True)
                err_f.write(f"--- décodeur {c['nom']}\n")
                err_f.flush()
                dec = subprocess.Popen(commande_decodeur(sources[c["nom"]], prog_dec),
                                       stdin=subprocess.DEVNULL, stdout=enc.stdin, stderr=err_f)
                while True:
                    try:
                        dec.wait(timeout=5)
                        break
                    except subprocess.TimeoutExpired:
                        pass
                    if enc.poll() is not None:
                        raise ErreurControle("l'encodeur du proxy s'est arrêté")
                    if time.time() - dernier >= 60:
                        dernier = time.time()
                        fait = int(_lire_progression(prog_enc).get("frame", "0") or 0)
                        vitesse = fait / (dernier - t)
                        reste = (images - fait) / vitesse if vitesse else float("nan")
                        log(f"    {fait}/{images} images, {vitesse:.1f} i/s, "
                            f"reste environ {reste / 60:.0f} min")
                if dec.returncode != 0:
                    raise ErreurControle(f"décodage de {c['nom']} en échec")
                n = int(_lire_progression(prog_dec).get("frame", "-1") or -1)
                decodees.append(n)
                log(f"  {c['nom']} : {n} images décodées sur {c['frames']} annoncées.")
            enc.stdin.close()
            if enc.wait() != 0:
                raise ErreurControle("encodeur du proxy en échec")
        except (ErreurControle, BrokenPipeError, OSError) as exc:
            _arreter(dec, enc)
            err = journal.read_text(errors="replace")
            raise ErreurControle(f"Proxy : {exc}. {err[-800:]}") from exc
    duree = time.time() - t
    log(f"  Proxy fabriqué en {duree:.0f} s, soit "
        f"{duree / max(images / PROXY_FPS / 60, 1e-9):.1f} s par minute de rush.")
    return duree, decodees


def commande_proxy_lambda(projet: str, sources: Path, voix: str, sortie: Path) -> list[str]:
    """Commande du proxy Lambda, sans envoi. Le script voix garde l'envoi et le rapport."""
    return [
        sys.executable, str(PROXY_LAMBDA_SCRIPT), "--proxy", "--projet", projet,
        "--site", PROXY_LAMBDA_SITE, "--sources", str(sources), "--wav", voix,
        "--sortie", str(sortie), "--sans-envoi",
    ]


def fabriquer_proxy_lambda(projet: str, sources: Path, voix: str, sortie: Path,
                            cams: list[dict], travail: Path) -> tuple[float, list[int]]:
    """Fabrique le proxy sur Lambda. Les contrôles détaillés restent exécutés ici ensuite."""
    journal = travail / "proxy.lambda.log"
    t = time.time()
    r = subprocess.run(
        commande_proxy_lambda(projet, sources, voix, sortie),
        cwd=REPO, env=aws_env(), capture_output=True, text=True, check=False,
    )
    journal.write_text(r.stdout + r.stderr, encoding="utf-8")
    if r.returncode or not sortie.exists():
        detail = (r.stderr or r.stdout)[-1200:]
        raise ErreurControle(f"Proxy Lambda en échec. Journal : {journal}. {detail}")
    duree = time.time() - t
    log(f"  Proxy Lambda fabriqué en {duree:.0f} s.")
    return duree, [int(c["frames"]) for c in cams]


def proxy_lambda_possible(args) -> bool:
    """Le mode automatique réserve Lambda aux projets S3 avec les trois variables AWS."""
    return bool(args.projet and PROXY_LAMBDA_SCRIPT.exists() and all(os.environ.get(n) for n in (
        "REMOTION_AWS_ACCESS_KEY_ID", "REMOTION_AWS_SECRET_ACCESS_KEY", "REMOTION_AWS_REGION")))


def plages_sources(cams: list[dict]) -> list[dict]:
    plages, debut = [], 0
    for c in cams:
        plages.append({"proxy_debut": debut, "images": c["frames"], "camera": c["reference"],
                       "camera_debut": 0, "camera_largeur": c["largeur"],
                       "camera_hauteur": c["hauteur"]})
        debut += c["frames"]
    return plages


def document_sources(cams: list[dict], wav: str) -> dict:
    """Format contractuel partagé avec voix/recouper.py. Ne pas changer sans lui."""
    return {
        "version": 1,
        "fps": PROXY_FPS,
        "proxy": {"largeur": PROXY_LARGEUR, "hauteur": PROXY_HAUTEUR,
                  "images": sum(c["frames"] for c in cams)},
        "plages": plages_sources(cams),
        "audio": {"wav": wav, "sample_rate": AUDIO_SR},
    }


# ─── Contrôles ───────────────────────────────────────────────────────────────

def _sonde_sortie(chemin: Path) -> dict:
    r = lancer(["ffprobe", "-v", "error", "-print_format", "json",
                "-show_streams", "-show_format", str(chemin)],
               capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def md5_pcm(chemin: Path) -> str:
    """Empreinte des échantillons audio, quel que soit le conteneur."""
    r = lancer(["ffmpeg", "-v", "error", "-i", str(chemin), "-map", "0:a:0",
                "-c:a", "pcm_s24le", "-f", "md5", "-"],
               capture_output=True, text=True, check=True)
    return r.stdout.strip()


def controler_voix(voix: Path, cams: list[dict], niveau: dict, residus: list[dict]) -> dict:
    """Contrôles de voix.wav, avant tout envoi et avant le proxy."""
    import soundfile as sf

    attendus = sum(c["frames"] for c in cams) * ECHANTILLONS_PAR_IMAGE
    info = sf.info(str(voix))
    conclusifs = [r for r in residus if r["conclusif"]]
    residu_max = max((abs(r["residu_ms"]) for r in conclusifs), default=None)
    c = {
        "echantillons_voix": int(info.frames), "echantillons_attendus": attendus,
        "voix_format": f"{info.subtype} {info.samplerate} Hz {info.channels} canal",
        "niveau_integre_lufs": niveau["integre_lufs"], "pic_vrai_dbtp": niveau["pic_vrai_dbtp"],
        "lra_lu": niveau["lra_lu"],
        "residu_synchro_max_ms": residu_max, "residu_synchro_points": len(conclusifs),
    }
    echecs = []
    if info.frames != attendus:
        echecs.append(f"voix.wav : {info.frames} échantillons au lieu de {attendus}")
    if (info.subtype, info.samplerate, info.channels) != ("PCM_24", AUDIO_SR, 1):
        echecs.append(f"voix.wav : {c['voix_format']}")
    if abs(niveau["integre_lufs"] - LOUDNESS_TARGET_LUFS) > TOL_NIVEAU_LU:
        echecs.append(f"niveau {niveau['integre_lufs']} LUFS hors ±{TOL_NIVEAU_LU} LU")
    if niveau["pic_vrai_dbtp"] > PIC_MAX_DBTP:
        echecs.append(f"pic vrai {niveau['pic_vrai_dbtp']} dBTP")
    if residu_max is None:
        echecs.append("résidu de synchro non mesurable")
    elif residu_max > TOL_SYNCHRO_FINALE_MS:
        echecs.append(f"résidu de synchro {residu_max} ms")
    c["echecs"] = echecs
    return c


def controler_proxy(proxy: Path, cams: list[dict], md5_voix: str, decodees: list[int]) -> dict:
    p = _sonde_sortie(proxy)
    v = next(s for s in p["streams"] if s["codec_type"] == "video")
    a = next(s for s in p["streams"] if s["codec_type"] == "audio")
    tc = next((s.get("tags", {}).get("timecode") for s in p["streams"]
               if s.get("tags", {}).get("timecode")), None)
    images_attendues = sum(c["frames"] for c in cams)
    images = int(v.get("nb_frames") or 0)
    echantillons = int(a.get("duration_ts") or 0)
    c = {
        "video_codec": v["codec_name"], "largeur": v["width"], "hauteur": v["height"],
        "fps": v.get("r_frame_rate"), "fps_moyen": v.get("avg_frame_rate"),
        "images": images, "images_attendues": images_attendues, "timecode": tc,
        "debit_video": int(v["bit_rate"]) if str(v.get("bit_rate", "")).isdigit() else None,
        "taille_proxy": int(p.get("format", {}).get("size", 0) or 0),
        "audio_codec": a["codec_name"], "audio_sample_rate": int(a["sample_rate"]),
        "audio_canaux": int(a.get("channels", 0)), "echantillons_proxy": echantillons,
        "audio_proxy_identique_voix": md5_pcm(proxy) == md5_voix,
        "images_decodees_par_rush": decodees,
    }
    echecs = []
    for cam, n in zip(cams, decodees):
        if n != cam["frames"]:
            echecs.append(f"{cam['nom']} : {n} images décodées, {cam['frames']} annoncées")
    if v["codec_name"] != "h264":
        echecs.append(f"codec vidéo {v['codec_name']}")
    if (v["width"], v["height"]) != (PROXY_LARGEUR, PROXY_HAUTEUR):
        echecs.append(f"résolution {v['width']}x{v['height']}")
    if (Fraction(v.get("r_frame_rate", "0/1")) != PROXY_FPS
            or Fraction(v.get("avg_frame_rate", "0/1")) != PROXY_FPS):
        echecs.append(f"cadence {v.get('r_frame_rate')} / {v.get('avg_frame_rate')}")
    if images != images_attendues:
        echecs.append(f"{images} images au lieu de {images_attendues}")
    if tc != "00:00:00:00":
        echecs.append(f"timecode {tc}")
    if echantillons != images_attendues * ECHANTILLONS_PAR_IMAGE:
        echecs.append(f"audio du proxy : {echantillons} échantillons au lieu de "
                      f"{images_attendues * ECHANTILLONS_PAR_IMAGE}")
    if a["codec_name"] != "pcm_s24le" or int(a["sample_rate"]) != AUDIO_SR:
        echecs.append(f"audio du proxy {a['codec_name']} {a['sample_rate']} Hz")
    if not c["audio_proxy_identique_voix"]:
        echecs.append("audio du proxy différent de voix.wav")
    c["echecs"] = echecs
    return c


# ─── Rendu ───────────────────────────────────────────────────────────────────

def verifier_cadence(cams: list[dict]) -> None:
    mauvais = [f"{c['nom']} ({c['fps']}, moyenne {c['fps_moyen']})" for c in cams
               if Fraction(c["fps"]) != PROXY_FPS
               or (Fraction(c["fps_moyen"]) and abs(Fraction(c["fps_moyen"]) - PROXY_FPS) > 0.01)]
    if mauvais:
        raise ErreurEntree(f"Le proxy exige des rushs à {PROXY_FPS} i/s constants. "
                           f"Hors norme : {', '.join(mauvais)}")


def envoyer(fichier: Path, uri: str) -> None:
    run_aws(["s3", "cp", str(fichier), uri, "--only-show-errors"])


def _masters_en_cache(travail: Path) -> list[Path]:
    return sorted((travail / "cache").glob("*_voix.wav"))


def assurer_place(dossier: Path, besoin: float, travail: Path, etape: str) -> None:
    """Vérifie la place libre. Sacrifie le cache des masters améliorés s'il le faut."""
    libre = shutil.disk_usage(dossier).free
    if besoin + MARGE_DISQUE <= libre:
        return
    liberable = sum(p.stat().st_size for p in _masters_en_cache(travail))
    if besoin + MARGE_DISQUE > libre + liberable:
        raise ErreurEntree(f"Disque insuffisant pour {etape} : {besoin / 1e9:.1f} Go requis "
                           f"(marge {MARGE_DISQUE / 1e9:.1f} Go), {libre / 1e9:.1f} Go libres.")
    for p in _masters_en_cache(travail):
        log(f"  Place disque : suppression du master en cache {p.name}.")
        p.unlink()
        p.with_suffix(".json").unlink(missing_ok=True)


def rendre(analyse: dict, sources: dict[str, Source], travail: Path, args) -> dict:
    """Chaîne audio, voix.wav, contrôles de voix, proxy, contrôles du proxy, envoi.

    En mode S3, voix.wav part avant le proxy et quitte le disque : ffmpeg la relit
    par URL. Le disque ne porte alors que le proxy pendant l'encodage.
    """
    t0 = time.time()
    cams = analyse["cameras"]
    verifier_cadence(cams)
    images = sum(c["frames"] for c in cams)
    duree = images / PROXY_FPS
    dossier = Path(args.sortie) if args.sortie else travail / "sortie"
    dossier.mkdir(parents=True, exist_ok=True)
    s3 = args.s3_sortie.rstrip("/") if args.s3_sortie else None
    voix_quitte_disque = bool(s3) and not args.garder_local

    # Pic de la chaîne audio : maître brut, copie, DeepFilterNet, filtres, sortie.
    duree_maitres = sum(m["duree_s"] for m in analyse["maitres"] if m["utilise"])
    besoin_chaine = duree_maitres * AUDIO_SR * 4 * 5
    besoin_voix = duree * AUDIO_SR * 3
    besoin_proxy = duree * PROXY_OCTETS_PAR_S + (0 if voix_quitte_disque else besoin_voix)
    assurer_place(dossier, max(besoin_chaine, besoin_proxy), travail, "le rendu")

    chaine_audio.verifier_dependances(denoise=not args.no_denoise)
    t = time.time()
    masters, rapports_chaine = ameliorer_masters(analyse, sources, travail, not args.no_denoise)
    t_chaine = time.time() - t
    cache = travail / "cache"
    pistes_cam = {c["nom"]: synchro.Piste(c["nom"], extraire_16k_camera(sources[c["nom"]], cache))
                  for c in cams}

    proxy = dossier / NOM_PROXY
    voix = dossier / NOM_VOIX
    t = time.time()
    log(f"Voix alignée {voix.name} ({duree / 60:.1f} min)...")
    residus, niveau = ecrire_voix(cams, masters, pistes_cam, voix)
    empreinte_voix = md5_pcm(voix)
    t_voix = time.time() - t
    controles = controler_voix(voix, cams, niveau, residus)
    controles["residus_synchro"] = residus

    wav_ref = f"{s3}/{NOM_VOIX}" if s3 else str(voix.resolve())
    doc = document_sources(cams, wav_ref)
    chemin_sources = dossier / NOM_SOURCES
    chemin_sources.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    res: dict = {
        "chaine": rapports_chaine, "controles": controles, "sources": doc,
        "fichiers": {"proxy": str(proxy), "voix": str(voix), "sources": str(chemin_sources)},
        "temps_s": {"chaine_audio": round(t_chaine, 2), "voix_alignee": round(t_voix, 2)},
    }
    if controles["echecs"]:
        controles["ok"] = False
        log(f"  Contrôles de la voix : ÉCHEC {'; '.join(controles['echecs'])}")
        return res
    log(f"  Voix : {controles['niveau_integre_lufs']} LUFS, {controles['pic_vrai_dbtp']} dBTP, "
        f"résidu synchro max {controles['residu_synchro_max_ms']} ms")

    entree_voix = str(voix)
    voix_lambda = str(voix)
    if s3:
        log(f"Envoi vers {s3}/{NOM_VOIX}...")
        envoyer(voix, f"{s3}/{NOM_VOIX}")
        voix_lambda = f"{s3}/{NOM_VOIX}"
        if voix_quitte_disque:
            entree_voix = presign(f"{s3}/{NOM_VOIX}")
            voix.unlink()
            res["fichiers"]["voix"] = f"{s3}/{NOM_VOIX}"
    if getattr(args, "sans_proxy", False):
        # Le proxy est fabriqué ailleurs (voix/proxy_parties.py, jobs parallèles).
        controles["ok"] = True
        if s3:
            envoyer(chemin_sources, f"{s3}/{NOM_SOURCES}")
            res["s3"] = {"voix": f"{s3}/{NOM_VOIX}", "sources": f"{s3}/{NOM_SOURCES}"}
        res["proxy_mode"] = "aucun"
        res["temps_s"]["rendu"] = round(time.time() - t0, 2)
        return res
    assurer_place(dossier, besoin_proxy, travail, "le proxy")
    mode_proxy = args.proxy_mode
    via_lambda = mode_proxy != "conteneur" and proxy_lambda_possible(args)
    if mode_proxy == "lambda" and not via_lambda:
        log("  Proxy Lambda indisponible. Utilisation du conteneur.")
    if via_lambda:
        try:
            t_proxy, decodees = fabriquer_proxy_lambda(
                args.projet, chemin_sources, voix_lambda, proxy, cams, travail)
            res["proxy_mode"] = "lambda"
        except (ErreurEntree, ErreurControle, OSError) as exc:
            log(f"  {exc}")
            log("  Repli vers le proxy conteneur.")
            t_proxy, decodees = fabriquer_proxy(cams, sources, entree_voix, proxy, travail)
            res["proxy_mode"] = "conteneur-repli"
    else:
        t_proxy, decodees = fabriquer_proxy(cams, sources, entree_voix, proxy, travail)
        res["proxy_mode"] = "conteneur"
    res["temps_s"]["proxy"] = round(t_proxy, 2)
    res["temps_s"]["proxy_par_minute_de_rush"] = round(t_proxy / max(duree / 60, 1e-9), 2)

    ctrl_proxy = controler_proxy(proxy, cams, empreinte_voix, decodees)
    echecs = controles["echecs"] + ctrl_proxy.pop("echecs")
    controles.update(ctrl_proxy)
    controles["echecs"] = echecs
    controles["ok"] = not echecs
    log(f"  Contrôles : {'OK' if controles['ok'] else 'ÉCHEC ' + '; '.join(echecs)}")
    log(f"    images {controles['images']}/{controles['images_attendues']}, "
        f"timecode {controles['timecode']}, audio identique à voix.wav : "
        f"{controles['audio_proxy_identique_voix']}")

    if controles["ok"] and s3:
        t = time.time()
        for f in (chemin_sources, proxy):
            log(f"Envoi vers {s3}/{f.name}...")
            envoyer(f, f"{s3}/{f.name}")
        res["s3"] = {"proxy": f"{s3}/{NOM_PROXY}", "voix": f"{s3}/{NOM_VOIX}",
                     "sources": f"{s3}/{NOM_SOURCES}"}
        res["lien_proxy"] = lien_telechargement(f"{s3}/{NOM_PROXY}")
        res["temps_s"]["envoi"] = round(time.time() - t, 2)
        if not args.garder_local:
            proxy.unlink()
            res["local_supprime"] = True
    res["temps_s"]["rendu"] = round(time.time() - t0, 2)
    return res


# ─── CLI ─────────────────────────────────────────────────────────────────────

def construire_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sous = p.add_subparsers(dest="commande", required=True)
    for nom, aide in (("analyser", "appairage et synchro, sans rendu"),
                      ("rendre", "chaîne audio, voix alignée, proxy, contrôles et envoi")):
        s = sous.add_parser(nom, help=aide)
        s.add_argument("sources", nargs="*",
                       help="audio maître et rushs caméra : chemins, URLs https ou s3://")
        s.add_argument("--projet", help="lit s3://…/inputs/PROJET/rushs/ si aucune source")
        s.add_argument("--maitre", action="append", default=[],
                       help="nom de fichier à traiter comme audio maître (répétable)")
        s.add_argument("--secours", action="append", default=[],
                       help="son intégré d'un rush (WAV nommé comme le rush), utilisé seulement "
                            "là où aucun maître principal ne couvre ce rush (répétable)")
        s.add_argument("--travail", type=Path, help="dossier de travail et de cache")
        s.add_argument("--rapport", type=Path, help="chemin du rapport JSON")
        if nom == "rendre":
            s.add_argument("--no-denoise", action="store_true",
                           help="coupe DeepFilterNet, le gate VAD et afftdn (test)")
            s.add_argument("--sortie", help="dossier local des sorties")
            s.add_argument("--s3-sortie", help="préfixe S3 de sortie. Défaut avec --projet : "
                                               "s3://…/outputs/PROJET/synchro/")
            s.add_argument("--local", action="store_true", help="n'envoie rien dans S3")
            s.add_argument("--garder-local", action="store_true",
                           help="garde proxy.mov et voix.wav après l'envoi S3")
            s.add_argument("--sans-proxy", action="store_true",
                           help="voix.wav et sources.json seulement (proxy par proxy_parties.py)")
            s.add_argument("--proxy-mode", choices=["auto", "lambda", "conteneur"],
                           default=os.environ.get("VOIX_PROXY_MODE", "auto"),
                           help="auto : Lambda pour un projet S3, avec repli conteneur (défaut)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = construire_parser().parse_args(argv)
    t0 = time.time()
    try:
        if args.projet:
            valider_projet(args.projet)
        if args.sources:
            sources = [source_explicite(s) for s in args.sources]
        elif args.projet:
            sources = sources_projet(args.projet)
        else:
            raise ErreurEntree("Donner --projet NOM ou des sources.")
        secours = [source_explicite(s) for s in args.secours]
        noms = [s.nom for s in sources + secours]
        if len(set(noms)) != len(noms):
            raise ErreurEntree("Deux entrées portent le même nom de fichier.")
        inconnus = set(args.maitre) - {s.nom for s in sources}
        if inconnus:
            raise ErreurEntree(f"--maitre inconnu : {', '.join(sorted(inconnus))}")
        travail = args.travail or REPO / "out" / "voix" / (args.projet or "local")
        travail.mkdir(parents=True, exist_ok=True)
        if args.commande == "rendre":
            if args.local:
                args.s3_sortie = None
            elif not args.s3_sortie and args.projet:
                args.s3_sortie = f"s3://{BUCKET}/outputs/{args.projet}/synchro"

        rapport: dict = {
            "commande": args.commande, "projet": args.projet,
            "date": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "argv": sys.argv[1:] if argv is None else argv,
        }
        analyse = analyser(sources, travail, set(args.maitre), secours)
        afficher_analyse(analyse)
        rapport["analyse"] = analyse
        code = 0
        if args.commande == "rendre":
            rapport["no_denoise"] = args.no_denoise
            rapport["rendu"] = rendre(analyse, {s.nom: s for s in sources + secours}, travail, args)
            if not rapport["rendu"]["controles"].get("ok"):
                code = 3
        rapport["temps_total_s"] = round(time.time() - t0, 2)
        dossier = Path(args.sortie) if getattr(args, "sortie", None) else travail
        chemin = args.rapport or dossier / f"rapport-{args.commande}.json"
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(json.dumps(rapport, ensure_ascii=False, indent=2, default=str) + "\n")
        log(f"Rapport : {chemin}")
        rendu = rapport.get("rendu", {})
        if code == 0 and rendu.get("s3"):
            uri = args.s3_sortie.rstrip("/") + "/" + chemin.name
            envoyer(chemin, uri)
            log(f"Rapport envoyé : {uri}")
            for k, v in rendu["s3"].items():
                log(f"  {k} : {v}")
            if rendu.get("lien_proxy"):
                log("Lien de téléchargement du proxy (7 jours) :")
                print(rendu["lien_proxy"], flush=True)
        elif rendu:
            for k, v in rendu["fichiers"].items():
                log(f"  {k} : {v}")
        if code == 3:
            log("[ERREUR] Contrôles de fin en échec. Sorties gardées en local, rien n'est envoyé.")
        log(f"Durée totale : {rapport['temps_total_s']:.1f} s")
        return code
    except (ErreurEntree, synchro.SynchroErreur, chaine_audio.ChaineAudioErreur) as exc:
        print(f"[ERREUR] {exc}", file=sys.stderr)
        return 2
    except ErreurControle as exc:
        print(f"[ERREUR] {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
