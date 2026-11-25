#!/usr/bin/python3
"""
auto_edit.py — Coupe automatiquement les silences, bafouillages et mots de remplissage
Usage : python3 auto_edit.py ta_video.mp4
"""

import argparse
import bisect
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import requests
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path

# ─── Mots de remplissage ──────────────────────────────────────────────────────

# Toujours coupés, peu importe le contexte
FILLERS = {
    "euh", "heu", "euhm", "hum", "hmm", "hm", "mh", "mmh",
    "bah", "beh", "ben", "hein", "eh",
}

# Coupés SEULEMENT si entourés de >150ms de silence (contexte ambigu)
CONTEXTUAL_FILLERS = {"voila", "ok", "bon"}

# ─── Paramètres ───────────────────────────────────────────────────────────────

SILENCE_MIN_MS        = 220    # silence VAD > 220ms → segment séparé
LEADING_PADDING       = 0.14   # garde plus d'attaque avant le 1er mot (moins de débuts mangés)
TRAILING_PADDING      = 0.02   # fin serrée : ne pas garder plus de fin de phrase
CUT_PRE_PADDING       = 0.05   # marge avant une coupe (préserve la fin de phrase)
CUT_POST_PADDING      = 0.01   # marge après une coupe (évite de manger le début suivant)
SEEK_PREROLL          = 5.00   # seek rapide puis trim local précis (sync A/V)
STUTTER_WINDOW        = 1.5    # silence/temps max entre les deux occurrences du mot
STUTTER_MIN_LEN       = 5      # longueur minimale d'un mot stutter (évite "des","qui","mais"…)
STUTTER_MAX_BETWEEN   = 2      # max mots entre les deux occurrences
MIN_SEGMENT_DURATION  = 0.10   # segments < 100ms ignorés
MAX_COUGH_DURATION    = 0.80   # segment VAD court sans mots → toux (0.80s pour capter toux longues)
INTRA_GAP_MIN         = 0.30   # pause entre mots dans un même segment → coupée
CONTEXTUAL_MIN_GAP    = 0.15   # silence min autour d'un filler contextuel
PHRASE_NGRAM          = 3      # taille des séquences pour détecter répétitions
PHRASE_MAX_BETWEEN    = 10     # max mots entre 1ère et 2ème occurrence d'une phrase
                               # (discriminateur clé : 10 mots = restart immédiat,
                               #  80 mots = répétition naturelle de structure)
PHRASE_MAX_DURATION   = 6.0    # durée max du cut de phrase (>6s = discours normal)
LEADING_NOISE_MIN     = 0.45   # bruit/toux en début de segment VAD : gap min avant premier mot
RESTART_TIME_WINDOW   = 5.0    # fenêtre max entre 1ère et 2ème occurrence
RESTART_MIN_CUT       = 0.25   # durée min d'un cut restart
PHRASE_BOUNDARY_GAP   = 0.40   # pause ≥ 0.4s = frontière de phrase (pour coherence check)

# ─── Agressivité de la coupe en FIN de phrase ────────────────────────────────
# Trois réglages agissent en cascade sur la borne de FIN d'un segment gardé
# (le DÉBUT n'est jamais touché par ces profils — lead identique partout) :
#   trailing_padding : marge ajoutée après la fin du segment VAD
#   trim_max_trail   : silence max gardé après le dernier mot (_trim_trailing_silence)
#   snap_pad_trail   : marge gardée après la vraie fin acoustique (snap_segments_to_silence)
#
# "tight" = comportement historique, strictement inchangé (défaut).
# "relaxed" = mêmes valeurs + TAIL_RELAX_DEFAULT secondes : la fin de mot n'est
# plus rognée quand silencedetect déclenche pendant la décroissance de la
# dernière syllabe (fricative, voyelle finale traînante). Les garde-fous de
# `apply_tail_bounds` empêchent la fin relâchée de réintroduire un passage
# coupé (euh, bafouillage) ou de mordre sur le segment suivant.
TAIL_RELAX_DEFAULT = 0.30      # secondes de respiration ajoutées en mode relaxed

TAIL_MODES = ("tight", "relaxed")


def tail_profile(mode="tight", relax=None):
    """
    Retourne le profil de fin de phrase {trailing_padding, trim_max_trail,
    snap_pad_trail, mode, relax}.

    `relax` (secondes) surcharge TAIL_RELAX_DEFAULT en mode "relaxed".
    """
    base = {
        "trailing_padding": TRAILING_PADDING,
        "trim_max_trail":   0.05,
        "snap_pad_trail":   0.02,
        "mode":             "tight",
        "relax":            0.0,
    }
    if mode != "relaxed":
        return base
    pad = TAIL_RELAX_DEFAULT if relax is None else max(0.0, float(relax))
    return {
        "trailing_padding": base["trailing_padding"] + pad,
        "trim_max_trail":   base["trim_max_trail"]   + pad,
        "snap_pad_trail":   base["snap_pad_trail"]   + pad,
        "mode":             "relaxed",
        "relax":            pad,
    }

# Mots "suspens" : ne peuvent pas clore une phrase → un cut juste après = incohérent
DANGLING_WORDS = {
    "de", "du", "d", "a", "au", "aux", "en", "un", "une", "le", "la", "les", "des",
    "et", "ou", "que", "qui", "dont", "car", "si", "ne", "ni", "par", "sur",
    "dans", "avec", "pour", "sans", "sous", "vers", "chez", "entre",
    "mais", "donc", "puis", "comme", "ce", "cet", "cette", "ces",
    "mon", "ton", "son", "ma", "ta", "sa", "notre", "votre", "leur",
    "c", "j", "m", "t", "s", "n", "l",   # contractions séparées
    "en", "y",
}

# Mots trop fréquents pour être détectés comme stutters
STUTTER_STOPWORDS = {
    "les", "des", "une", "sur", "son", "ses", "lui", "que", "qui", "elle",
    "ils", "eux", "par", "pas", "est", "ont", "ete", "mais", "donc",
    "pour", "avec", "dans", "tout", "tres", "bien", "plus", "aussi",
    "comme", "leur", "meme", "cela", "ceux", "nous", "vous", "faut",
    "fait", "peut", "voir", "dire", "etre", "aller", "avoir",
}

# ─── Audio polish (réf Auphonic — Optuna v4, 250 trials + DeepFilterNet3 ML) ──
# Chaîne : DeepFilterNet3 (denoise+dereverb ML) → ffmpeg EQ/compression/loudnorm.
# DeepFilterNet enlève respirations, frottements, queues de réverb (impossible avec ffmpeg seul).
# 7 bandes EQ, loudness verrouillé sur Auphonic. Voir tuning/best_params_v4.json.
LOUDNESS_TARGET_LUFS = -15.76
LOUDNESS_TRUE_PEAK   = -1.19
LOUDNESS_LRA         = 6.3
HPF_FREQ_HZ          = 65
LPF_FREQ_HZ          = 12110
AFFTDN_NR            = 4.2     # bas car DeepFilterNet a déjà denoisé
DEESSER_INTENSITY    = 0.17
COMP_THRESH_DB       = -19.6
COMP_RATIO           = 2.16
COMP_ATTACK_MS       = 14
COMP_RELEASE_MS      = 186
COMP_MAKEUP_DB       = 1.96

# AutoEQ : 7 bandes calées sur réponse Auphonic post-DeepFilterNet
VOICE_EQ_CURVE = [
    (250,   1.0,  +4.13),  # warmth
    (500,   1.4,  -3.04),  # de-mud
    (1500,  1.0,  +2.65),  # basse-presence
    (3000,  1.0,  +8.72),  # presence forte
    (5500,  1.2,  +3.63),  # clarity
    (8500,  1.0,  +1.99),  # air
    (11000, 1.2,  +3.18),  # haut-air
]

BWE_AMOUNT = 0.23
BWE_DRIVE  = 4.1
BWE_FREQ   = 6500
BWE_CEIL   = 14000

# DeepFilterNet3 (ML denoise+dereverb) — pré-traitement avant ffmpeg
USE_DEEPFILTERNET = True       # désactiver pour fallback ffmpeg-only

# Speech gate VAD : silence les pauses non-voix (respirations, frottements)
# Auphonic descend à -180 dB hors voix ; DeepFilterNet seul atteint -72 dB.
USE_SPEECH_GATE   = True
VAD_GATE_ATTEN_DB = 80          # floor des segments non-voix (-80 dB ≈ inaudible)
VAD_GATE_PAD_MS   = 60          # marge avant/après chaque segment voix
VAD_GATE_FADE_MS  = 30          # crossfade pour éviter les pops

# ─── Hardware & Services ─────────────────────────────────────────────────────
def check_videotoolbox():
    """Vérifie si l'encodeur matériel Apple est disponible."""
    try:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"],
                         capture_output=True, text=True)
        return "h264_videotoolbox" in r.stdout
    except:
        return False

HAS_VIDEOTOOLBOX = check_videotoolbox()

# ─── Utilitaires ──────────────────────────────────────────────────────────────

def run(cmd, desc="commande"):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n[ERREUR] {desc}\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result

def get_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True
    )
    return float(json.loads(r.stdout)["format"]["duration"])

def get_stream_duration(path, stream_selector="v:0"):
    r = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-select_streams", stream_selector,
            "-print_format", "json", "-show_streams",
            path,
        ],
        capture_output=True, text=True
    )
    try:
        streams = json.loads(r.stdout).get("streams", [])
        if streams and streams[0].get("duration"):
            return float(streams[0]["duration"])
    except Exception:
        pass
    if stream_selector.startswith("v"):
        try:
            frames = _probe_frame_count(path)
            if frames:
                fps_n, fps_d = get_video_fps_rational(path)
                return frames * fps_d / fps_n
        except Exception:
            pass
    return get_duration(path)

def probe_av(path):
    r = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json", "-show_streams",
            path,
        ],
        capture_output=True, text=True
    )
    info = {"video_duration": None, "audio_duration": None,
            "video_start": None, "audio_start": None,
            "fps": None, "frames": None,
            "r_frame_rate": None, "avg_frame_rate": None}
    try:
        for s in json.loads(r.stdout).get("streams", []):
            if s.get("codec_type") == "video" and info["video_duration"] is None:
                info["video_duration"] = float(s["duration"]) if s.get("duration") else None
                info["video_start"] = float(s.get("start_time", 0) or 0)
                info["frames"] = int(s["nb_frames"]) if str(s.get("nb_frames", "")).isdigit() else None
                fr = s.get("avg_frame_rate") or s.get("r_frame_rate") or "0/0"
                info["avg_frame_rate"] = s.get("avg_frame_rate")
                info["r_frame_rate"]   = s.get("r_frame_rate")
                try:
                    num, den = fr.split("/")
                    info["fps"] = float(num) / float(den) if float(den) else None
                except Exception:
                    pass
            elif s.get("codec_type") == "audio" and info["audio_duration"] is None:
                info["audio_duration"] = float(s["duration"]) if s.get("duration") else None
                info["audio_start"] = float(s.get("start_time", 0) or 0)
    except Exception:
        pass
    return info


def get_av_offset(path):
    """
    Offset à appliquer aux timestamps issus du WAV extrait pour les remettre
    sur la timeline source. Quand audio_start ≠ video_start (fréquent sur
    MOV iPhone, mirrorless avec audio retardé), le WAV 16k extrait part
    de l'instant audio_start de la source — donc tout timestamp t du WAV
    correspond à l'instant (audio_start + t) côté source, qui équivaut à
    (audio_start - video_start + t) sur la timeline vidéo (origin = video_start).

    Retourne la quantité à AJOUTER à chaque t (positif = avance l'audio sur la vidéo).
    """
    info = probe_av(path)
    a = info["audio_start"] or 0.0
    v = info["video_start"] or 0.0
    return a - v


def apply_time_offset(words, vad, offset):
    """Décale tous les timestamps de `offset` secondes (en place sur copies)."""
    if abs(offset) < 1e-4:
        return words, vad
    print(f"  [AV sync] offset source détecté : {offset*1000:+.1f}ms — recalibrage timestamps")
    new_words = [
        {**w, "start": w["start"] + offset, "end": w["end"] + offset}
        for w in words
    ]
    new_vad = [(s + offset, e + offset) for s, e in vad]
    return new_words, new_vad

def warn_av_sync(path, label, tolerance=0.020):
    info = probe_av(path)
    vd, ad = info["video_duration"], info["audio_duration"]
    if vd is None or ad is None:
        print(f"  [AV sync] {label}: mesure ffprobe incomplète")
        return
    delta = abs(vd - ad)
    msg = f"  [AV sync] {label}: vidéo={vd:.3f}s audio={ad:.3f}s Δ={delta*1000:.0f}ms"
    if delta > tolerance:
        print(msg + "  [WARN]")
    else:
        print(msg)

def get_video_fps_rational(path):
    """
    FIX SYNC #13 — FPS comme FRACTION RATIONNELLE EXACTE (num, den) entiers.
    Élimine la perte de précision float (29.97 vs 30000/1001 = ~0.07µs/frame,
    soit ~7.5ms cumulés sur 1h à 29.97 fps). Fallback (30, 1) en dernier recours.
    """
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", path],
        capture_output=True, text=True
    )
    for s in json.loads(r.stdout).get("streams", []):
        if s.get("codec_type") != "video":
            continue
        for key in ("avg_frame_rate", "r_frame_rate"):
            fr = s.get(key, "")
            if not fr or fr == "0/0":
                continue
            try:
                num_s, den_s = fr.split("/")
                num, den = int(num_s), int(den_s)
                if den > 0 and 1 < num / den < 240:
                    return (num, den)
            except Exception:
                pass
    return (30, 1)


def get_video_fps(path):
    """FPS float (legacy / affichage). Source de vérité = get_video_fps_rational()."""
    num, den = get_video_fps_rational(path)
    return num / den


def is_source_vfr(path, tolerance=0.001):
    """
    FIX SYNC #13 — VFR si avg_frame_rate ≠ r_frame_rate au-delà de la tolérance.
    iPhone / GoPro / mirrorless tournent presque tous en VFR.
    """
    info = probe_av(path)
    try:
        afr = info.get("avg_frame_rate", "")
        rfr = info.get("r_frame_rate", "")
        if not afr or not rfr:
            return False
        a_n, a_d = (int(x) for x in afr.split("/"))
        r_n, r_d = (int(x) for x in rfr.split("/"))
        if a_d == 0 or r_d == 0:
            return False
        a = a_n / a_d
        r = r_n / r_d
        if r <= 0 or a <= 0:
            return False
        return abs(a - r) / r > tolerance
    except Exception:
        return False


def ensure_cfr_source(video, tmpdir):
    """
    FIX SYNC #13 — force CFR ABSOLU sur la source.

    Si VFR (iPhone, mirrorless, screen capture), re-encode la VIDÉO seule en CFR
    au taux nominal EXACT (rational num/den). L'audio est strictement copié
    (-c:a copy → bit-perfect, 0 perte).

    Effet : tous les seeks/trims subséquents deviennent parfaitement déterministes
    (PTS uniformes), plus de drop/dup asymétrique entre segments.

    Qualité vidéo : libx264 CRF 14 / VT 1.5× bitrate → visuellement transparent
    (au-delà du JND). Le segment encode ultérieur (CRF 17) reste le bottleneck.

    Si source déjà CFR (avg == r), retourne le chemin original (zéro re-encode).
    """
    if not is_source_vfr(video):
        return video

    fps_n, fps_d = get_video_fps_rational(video)
    cfr_path = os.path.join(tmpdir, "source_cfr" + Path(video).suffix)
    src_vbr = get_video_bitrate(video)

    print(f"  [CFR] Source VFR détectée → conversion CFR ABSOLU {fps_n}/{fps_d} fps")
    print(f"  [CFR] Re-encode vidéo visuellement transparent + audio bit-perfect (-c:a copy)")

    if HAS_VIDEOTOOLBOX:
        target_vbr = max(int(src_vbr * 1.5), 20_000_000)
        v_args = [
            "-c:v", "h264_videotoolbox",
            "-b:v", str(target_vbr),
            "-bf", "0",
            "-pix_fmt", "yuv420p",
        ]
    else:
        v_args = [
            "-c:v", "libx264",
            "-crf", "14",
            "-preset", "slow",
            "-pix_fmt", "yuv420p",
            "-bf", "0",
        ]

    r = subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", video,
        # FIX SYNC #13 : fps filter + -fps_mode cfr SUFFISENT (le triple verrouillage
        # avec -r et -vsync corrompait les PTS sur certains containers).
        "-vf", f"fps=fps={fps_n}/{fps_d}:round=near",
        "-fps_mode", "cfr",
        *v_args,
        "-c:a", "copy",
        "-map", "0:v:0", "-map", "0:a:0",
        "-movflags", "+faststart",
        cfr_path,
    ], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  [CFR] échec re-encode :\n{r.stderr[-400:]}")
        print(f"  [CFR] fallback sur source originale (fps filter par segment fera CFR)")
        return video

    if is_source_vfr(cfr_path):
        print(f"  [CFR] avertissement : sortie toujours détectée VFR — fallback")
        return video
    print(f"  [CFR] ✓ source CFR absolue prête : {Path(cfr_path).name}")
    return cfr_path


def get_video_bitrate(path):
    """Retourne le bitrate vidéo de la source en bits/s."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", path],
        capture_output=True, text=True
    )
    for s in json.loads(r.stdout).get("streams", []):
        if s.get("codec_type") == "video" and s.get("bit_rate"):
            return int(s["bit_rate"])
    # Fallback : bitrate total − 320k audio
    r2 = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True
    )
    fmt_br = int(json.loads(r2.stdout).get("format", {}).get("bit_rate", 8_000_000))
    return max(fmt_br - 320_000, 4_000_000)

def extract_audio(video, wav):
    """Extrait l'audio 48 kHz mono — réutilisé par VAD/Scribe (downsamplé en interne) et polish (natif)."""
    run(["ffmpeg", "-y", "-i", video, "-ar", "48000", "-ac", "1", "-vn", wav],
        "extraction audio")

def normalize(word):
    """Retire accents et ponctuation pour comparaison robuste."""
    w = word.lower().strip(".,!?;:«»'\"-")
    return ''.join(c for c in unicodedata.normalize('NFD', w)
                   if unicodedata.category(c) != 'Mn')

# ─── FIX 1 : fusion des contractions ─────────────────────────────────────────

def merge_contractions(words):
    """
    Whisper split "j'ai" → ["j", "'ai"]. Ça casse la détection de répétitions
    car "j" a longueur 1. On fusionne les mots dont le suivant commence par '.

    FIX CRITIQUE : on ne fusionne que si les deux mots sont ADJACENTS (<80ms).
    Sans ce check, la fonction fusionnait "truc" (76s) avec "'on" (103s)
    → mot de 27 secondes → stutter cut catastrophique.
    """
    merged = []
    for w in words:
        adjacent = merged and (w["start"] - merged[-1]["end"]) < 0.08
        if (w["raw"].startswith("'") or w["raw"].startswith("\u2019")) and adjacent:
            prev = merged[-1]
            merged[-1] = {
                "word": normalize(prev["raw"] + w["raw"]),
                "raw":  prev["raw"] + w["raw"],
                "start": prev["start"],
                "end":   w["end"],
            }
        else:
            merged.append(w)
    return merged

# ─── VAD ──────────────────────────────────────────────────────────────────────

def load_audio_mono(path, sr=16000):
    """
    Charge un audio en tensor torch float32 mono à `sr` Hz, décodé par ffmpeg.

    Remplace `silero.read_audio` / `torchaudio.load` : depuis torchaudio 2.9,
    l'I/O audio est déléguée à torchcodec (paquet séparé, qui ne suit pas les
    versions récentes de ffmpeg). Résultat, `read_audio` lève
    "torchaudio version X requires torchcodec for audio I/O" et TOUTE la
    détection VAD tombe. ffmpeg est déjà une dépendance dure du pipeline :
    décodage + downmix mono + resample en une passe, zéro dépendance Python,
    insensible aux versions de torchaudio.
    """
    import torch
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path,
         "-f", "s16le", "-acodec", "pcm_s16le", "-ac", "1", "-ar", str(sr), "-"],
        capture_output=True,
    )
    if proc.returncode != 0 or not proc.stdout:
        raise RuntimeError(
            f"ffmpeg n'a pas pu décoder {path} : "
            f"{proc.stderr.decode(errors='replace')[:200]}"
        )
    pcm = torch.frombuffer(bytearray(proc.stdout), dtype=torch.int16)
    return pcm.float() / 32768.0


def get_vad_segments(wav):
    print("  Détection voix/silence (Silero-VAD)...")
    import torch
    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad",
        model="silero_vad",
        force_reload=False,
        trust_repo=True,
    )
    (get_speech_timestamps, *_) = utils
    # FIX 9 : le wav source est désormais 48 kHz mono (extract_audio unifié),
    # load_audio_mono redescend à 16 kHz via ffmpeg.
    wav_tensor = load_audio_mono(wav, sr=16000)
    timestamps = get_speech_timestamps(
        wav_tensor, model,
        sampling_rate=16000,
        threshold=0.40,              # FIX 7 : relevé de 0.35 → 0.40 (moins de faux positifs)
        min_speech_duration_ms=80,
        min_silence_duration_ms=SILENCE_MIN_MS,
        return_seconds=True,
    )
    return [(t["start"], t["end"]) for t in timestamps]

# ─── Transcription ────────────────────────────────────────────────────────────

def transcribe_elevenlabs(wav):
    """
    Transcription via ElevenLabs Scribe (plus littérale que Whisper).
    ElevenLabs transcrit les mots abandonnés avec '--' (ex: "brand--")
    ce qui permet de détecter les restarts directement sans heuristique.
    Nécessite ELEVENLABS_API_KEY dans l'environnement.
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("  [ERREUR] Variable ELEVENLABS_API_KEY manquante.", file=sys.stderr)
        print("  Lancez : export ELEVENLABS_API_KEY='votre_clé'", file=sys.stderr)
        sys.exit(1)

    # Convertit WAV → MP3 avant envoi : réduit ~16 MB → ~1.5 MB, évite les timeouts
    mp3 = wav.replace(".wav", ".mp3")
    run(["ffmpeg", "-y", "-i", wav, "-b:a", "128k", mp3], "conversion MP3")
    size_mb = os.path.getsize(mp3) / (1024 * 1024)
    print(f"  Envoi à ElevenLabs (Scribe, {size_mb:.1f} MB)...")

    import time
    for attempt in range(1, 4):
        try:
            with open(mp3, "rb") as f:
                resp = requests.post(
                    "https://api.elevenlabs.io/v1/speech-to-text",
                    headers={"xi-api-key": api_key},
                    data={
                        "model_id": "scribe_v1",
                        "language_code": "fr",
                        "timestamps_granularity": "word",
                    },
                    files={"file": ("audio.mp3", f, "audio/mpeg")},
                    timeout=300,
                )
            resp.raise_for_status()
            break
        except Exception as e:
            if attempt == 3:
                print(f"  [ERREUR] ElevenLabs Scribe inaccessible : {e}", file=sys.stderr)
                sys.exit(1)
            wait = 10 * attempt
            print(f"  Timeout, nouvelle tentative dans {wait}s...")
            time.sleep(wait)

    data = resp.json()
    words = []
    for w in data.get("words", []):
        if w.get("type") != "word":
            continue
        start = w.get("start")
        end   = w.get("end")
        if start is None or end is None:
            continue
        words.append({
            "word":  normalize(w["text"]),
            "raw":   w["text"].strip(),
            "start": float(start),
            "end":   float(end),
        })

    print(f"  ElevenLabs Scribe : {len(words)} mots (transcription littérale)")
    return merge_contractions(words)


def transcribe(wav):
    return transcribe_elevenlabs(wav)

# ─── Détection des coupes ─────────────────────────────────────────────────────

def find_coughs(vad_segments, words):
    """Segments VAD courts sans mots transcrits = toux ou bruit."""
    word_starts = [w["start"] for w in words]
    coughs = []
    for seg_s, seg_e in vad_segments:
        if seg_e - seg_s > MAX_COUGH_DURATION:
            continue
        # Premier mot dont start >= seg_s
        idx = bisect.bisect_left(word_starts, seg_s)
        # Y a-t-il un mot qui chevauche [seg_s, seg_e] ?
        has_word = False
        # vérifie mot à idx et mot juste avant (peut chevaucher en queue)
        for k in (idx - 1, idx):
            if 0 <= k < len(words):
                w = words[k]
                if w["start"] < seg_e and w["end"] > seg_s:
                    has_word = True
                    break
        if not has_word:
            coughs.append((seg_s, seg_e, "cough", ""))
    return coughs

def find_intra_segment_gaps(words, vad_segments):
    """
    FIX 2 : détecte les pauses > INTRA_GAP_MIN entre deux mots consécutifs
    qui tombent à l'intérieur d'un même segment VAD (le VAD ne les voit pas).
    """
    gaps = []
    # Pré-indexe : pour chaque mot, dans quel segment VAD ?
    vad_starts = [s for s, _ in vad_segments]
    def seg_of(word):
        idx = bisect.bisect_right(vad_starts, word["start"]) - 1
        if idx < 0:
            return -1
        s, e = vad_segments[idx]
        return idx if s <= word["start"] and word["end"] <= e else -1

    word_seg = [seg_of(w) for w in words]
    for i in range(len(words) - 1):
        gap_s = words[i]["end"]
        gap_e = words[i + 1]["start"]
        if gap_e - gap_s < INTRA_GAP_MIN:
            continue
        if word_seg[i] >= 0 and word_seg[i] == word_seg[i + 1]:
            gaps.append((gap_s + 0.02, gap_e - 0.02, "gap", f"{gap_e - gap_s:.2f}s"))
    return gaps

def find_phrase_repeats(words):
    """
    Détecte les répétitions de séquences de PHRASE_NGRAM mots consécutifs.

    Discriminateur clé : PHRASE_MAX_BETWEEN (max 10 mots entre les 2 occurrences).
    - "j'ai validé le prompt ok j'ai validé" → 2 mots entre → détecté ✓
    - "on va voir le rendu... (50 mots)... on va voir que" → trop loin → ignoré ✓
    - "en train de lire... (12 mots)... en train de réaliser" → trop loin → ignoré ✓

    FIX 4 : le cut part du mot PRÉCÉDENT si celui-ci est court (contraction, "ok"…)
    pour éviter un début tronqué dans la vidéo finale.
    """
    bad = []
    n   = len(words)
    ng  = PHRASE_NGRAM
    if n < 2 * ng:
        return bad

    # Index : pour chaque n-gram (tuple), liste des positions où il apparaît
    seq_positions: dict = {}
    for i in range(n - ng + 1):
        seq = tuple(words[i + k]["word"] for k in range(ng))
        # Au moins 2 mots de longueur ≥ 4 (évite "on va voir")
        if sum(1 for w in seq if len(w) >= 4) < 2:
            continue
        seq_positions.setdefault(seq, []).append(i)

    used = set()
    # Itère sur les n-grams qui apparaissent ≥ 2 fois, dans l'ordre temporel
    candidates = []
    for seq, positions in seq_positions.items():
        if len(positions) < 2:
            continue
        for a, b in zip(positions, positions[1:]):
            if b - a <= PHRASE_MAX_BETWEEN + ng:
                candidates.append((a, b, seq))
    candidates.sort()  # ordre temporel

    for i, j, seq in candidates:
        # déjà consumé ?
        if any(k in used for k in range(i, i + ng)):
            continue
        # FIX 4 : remonte au mot précédent si court
        cut_start = words[i]["start"]
        if i > 0 and len(words[i - 1]["word"]) <= 2:
            cut_start = words[i - 1]["start"]
        cut_end = words[j]["start"]
        cut_dur = cut_end - cut_start
        if cut_dur > PHRASE_MAX_DURATION or cut_dur < 0.05:
            continue
        label = " ".join(seq)
        bad.append((cut_start, cut_end, "repeat", label))
        for k in range(ng):
            used.add(i + k)

    return bad

def build_transcript_with_pauses(words, pause_threshold=0.28, anchor_interval=12.0):
    """
    Génère la transcription brute avec marqueurs de pauses inline.

    Format : [→T.Ts] mot mot mot [Xs→T2s] mot mot [Xs→T3s] mot …
      [→T.Ts]   = ancre de timestamp (mot suivant commence à T.T secondes)
      [Xs→T2s]  = pause de X secondes; le mot suivant commence à T2 secondes

    Avantage : Claude voit exactement où les pauses surviennent et peut identifier
    les restarts même avec une pause courte (<0.6s), ex. :
      "de brand [0.3s→21.8s] et de branding"   → restart évident
      "on va essayer de [0.7s→16.4s] on va essayer de montrer" → restart évident
    """
    parts = []
    last_anchor = -anchor_interval  # force une ancre dès le début

    for i, w in enumerate(words):
        # Ancre de timestamp périodique
        if w["start"] - last_anchor >= anchor_interval:
            parts.append(f"[→{w['start']:.1f}s]")
            last_anchor = w["start"]
        elif i > 0:
            gap = w["start"] - words[i - 1]["end"]
            if gap >= pause_threshold:
                parts.append(f"[{gap:.1f}s→{w['start']:.1f}s]")

        parts.append(w["raw"])

    return " ".join(parts)

# ─── Bloc d'instructions statique pour Claude (identique entre chunks → cache) ──
# Ce bloc est CACHÉ via cache_control sur OpenRouter (Anthropic ephemeral cache).
# Économise ~50% des tokens facturés quand on lance 3 chunks en parallèle.
_CLAUDE_STATIC_INSTRUCTIONS = """Tu es un monteur vidéo expert pour des contenus français (personal branding, éducatif). Vidéo talking-head.

━━━ FORMAT DE LA TRANSCRIPTION ━━━
[→T.Ts] = ancre de timestamp absolu (le mot suivant commence à T.T secondes dans la vidéo entière)
[Xs→Ts] = pause de X secondes ; le mot suivant (restart potentiel) commence à T secondes (absolu)

━━━ MISSION : identifier deux types de coupes ━━━

▶ TYPE "restart" — L'auteur a un tic : il commence une phrase ou un groupe de mots, s'arrête (marqué par une pause [Xs→Ts]), puis REPREND le même groupe, identiquement ou légèrement reformulé.

  IMPORTANT : Tu dois être EXHAUSTIF. Scanne CHAQUE marqueur [Xs→Ts] depuis le DÉBUT de la transcription jusqu'à la FIN, un par un, sans en sauter aucun. Les restarts sont très fréquents (possiblement 10-20 dans une vidéo entière). Mieux vaut signaler un faux positif que rater un vrai restart.

  COMMENT LIRE LA TRANSCRIPTION pour trouver les restarts :
  Pour CHAQUE marqueur [Xs→Ts], compare les 2-6 mots AVANT avec les 2-6 mots APRÈS. Si au moins 1 mot de contenu (≥4 lettres) ou 2 mots courts se retrouvent des deux côtés, c'est un restart.

  EXEMPLES TYPIQUES à chercher (tous issus de ce type de vidéo) :
    • "on va essayer de [0.7s→16.4s] on va essayer de montrer"
      → faux départ : "on va essayer de", restart à 16.4s
      → coupe : start=début de "on va essayer de", end=16.4s

    • "et de brand [0.3s→21.8s] et de branding de zéro"
      → faux départ : "et de brand", restart à 21.8s
      → coupe : start=début de "et de brand", end=21.8s

    • "on va voir ce que [0.5s→49.2s] et on va voir le rendu qu'on a"
      → faux départ : "on va voir ce que", restart à 49.2s
      → coupe : start=début de "on va voir ce que", end=49.2s

    • "un visuel qui est parfaitement [1.3s→323.9s] qui est presque assuré d'être viral"
      → faux départ : phrase incomplète abandonnée, restart à 323.9s

    • "Maintenant si vous êtes une entreprise c'est compliqué [0.8s→462.8s] Maintenant si vous êtes une entreprise vous savez que"
      → même amorce répétée, restart à 462.8s

  RÈGLE RESTART :
  - end = timestamp T de la REPRISE (la valeur T dans [Xs→Ts])
  - start = estime le timestamp du PREMIER mot du faux départ (interpoler depuis l'ancre [→Ts] précédente)
  - Durée minimum : 0.5 seconde
  - PAS de durée maximum
  - IMPORTANT : le cut doit commencer sur un MOT COMPLET, jamais au milieu d'une phrase en cours qui a du sens
  - EN CAS DE DOUTE SUR UN RESTART → SIGNALE-LE QUAND MÊME (mieux vaut un faux positif)

▶ TYPE "content" — Passage à faible valeur, sans information ajoutée :
  • Reformulation de la même idée déjà dite clairement
  • Méta-commentaires vides
  • Répétition textuelle d'une conclusion déjà formulée
  RÈGLE : minimum 3 secondes, maximum 15% du total.
  IMPORTANT : le cut doit commencer et se terminer sur des frontières de phrases complètes (après un . ou une pause longue), jamais en plein milieu d'une phrase.

━━━ NE JAMAIS COUPER ━━━
✗ Exemples concrets, chiffres, démonstrations
✗ Arguments, prises de position
✗ Première et dernière phrase de la vidéo entière
✗ Call-to-action ("likez", "commentez", "abonnez-vous")
✗ Tout passage ambigu — EN CAS DE DOUTE, NE PAS COUPER

━━━ FORMAT DE RÉPONSE ━━━
JSON uniquement, sans texte avant ni après. Les timestamps doivent TOUJOURS être ABSOLUS (relatifs au début de la vidéo entière, jamais relatifs au début du chunk reçu) :
[{"start": X.X, "end": Y.Y, "type": "restart|content", "reason": "raison en <7 mots"}]
Si rien à couper : []"""


def _split_words_into_chunks(words, target_chunks=3, min_pause=0.5):
    """
    Découpe `words` en `target_chunks` chunks sur des frontières de pause >= min_pause.

    Stratégie : on vise des chunks de durée à peu près équilibrée. Pour chaque
    limite cible, on cherche la première pause >= min_pause après la cible —
    on ne coupe JAMAIS au milieu d'une phrase. Chaque chunk conserve les
    timestamps absolus d'origine (pas de re-baselining).

    Retourne une liste de sous-listes de `words`. Si la vidéo est trop courte
    ou les mots trop peu nombreux, retourne `[words]` (pas de chunking).
    """
    n = len(words)
    if target_chunks <= 1 or n < 200:
        return [words]

    total_dur = words[-1]["end"] - words[0]["start"]
    if total_dur <= 0:
        return [words]

    chunk_dur_target = total_dur / target_chunks
    chunks = []
    start_idx = 0
    next_cut_time = words[0]["start"] + chunk_dur_target

    for i in range(1, n - 1):
        if words[i]["end"] < next_cut_time:
            continue
        # Cherche une pause >= min_pause juste après l'index courant
        gap = words[i + 1]["start"] - words[i]["end"]
        if gap >= min_pause:
            chunks.append(words[start_idx:i + 1])
            start_idx = i + 1
            next_cut_time = words[i + 1]["start"] + chunk_dur_target
            if len(chunks) == target_chunks - 1:
                break

    # Dernier chunk : tout ce qui reste
    chunks.append(words[start_idx:])

    # Filtre les chunks trop petits (< 20 mots = pas pertinent)
    filtered = [c for c in chunks if len(c) >= 20]
    return filtered if filtered else [words]


def _call_claude_for_chunk(words_chunk, total_duration, chunk_idx, total_chunks, api_key):
    """
    Un appel Claude pour un chunk de transcription via OpenRouter.

    Retourne une liste de dicts cuts {start, end, type, reason} — pas de tuples,
    pas de filtrage : le caller s'en charge après la déduplication globale.

    Utilise le format de messages structuré avec cache_control sur la partie
    statique (mission + exemples + règles) pour bénéficier du prompt caching
    Anthropic via OpenRouter (≈50% de tokens facturés en moins quand plusieurs
    chunks tournent en parallèle).
    """
    if not words_chunk:
        return []

    chunk_start = words_chunk[0]["start"]
    chunk_end = words_chunk[-1]["end"]
    transcript = build_transcript_with_pauses(words_chunk, pause_threshold=0.20)

    # Partie dynamique : contexte du chunk + transcription
    dynamic_text = (
        f"CONTEXTE DE CETTE REQUÊTE :\n"
        f"Vidéo totale : {total_duration / 60:.1f} minutes ({total_duration:.1f}s).\n"
        f"Ce chunk couvre la portion {chunk_start:.1f}s → {chunk_end:.1f}s "
        f"(chunk {chunk_idx + 1}/{total_chunks}).\n"
        f"Tes timestamps doivent être ABSOLUS (entre 0 et {total_duration:.1f}s), "
        f"jamais relatifs au début du chunk.\n\n"
        f"TRANSCRIPTION (chunk {chunk_idx + 1}/{total_chunks}) :\n"
        f"{transcript}"
    )

    # Format structuré OpenRouter avec cache_control Anthropic.
    # cache_control={"type": "ephemeral"} → bloc caché ~5 min côté Anthropic.
    # Le bloc statique est identique entre chunks → hit cache à partir du 2e appel.
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": _CLAUDE_STATIC_INSTRUCTIONS,
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "text",
                    "text": dynamic_text,
                },
            ],
        }
    ]

    payload = {
        "model": "anthropic/claude-sonnet-4-6",
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=90,
        )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as ex:
        # Fallback : si OpenRouter rejette le format multi-bloc / cache_control,
        # on retombe sur un prompt texte plat (pas de cache, mais ça marche).
        status = getattr(ex.response, "status_code", None) if ex.response is not None else None
        if status in (400, 422):
            flat_prompt = _CLAUDE_STATIC_INSTRUCTIONS + "\n\n" + dynamic_text
            payload_flat = dict(payload)
            payload_flat["messages"] = [{"role": "user", "content": flat_prompt}]
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload_flat,
                timeout=90,
            )
            resp.raise_for_status()
        else:
            raise

    raw = resp.json()["choices"][0]["message"]["content"].strip()

    # Parse JSON — Claude peut retourner soit un tableau direct soit un objet
    # contenant une liste.
    parsed = json.loads(raw)
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for v in parsed.values():
            if isinstance(v, list):
                return v
    return []


def analyze_content(words):
    """
    Envoie la transcription à Claude Sonnet 4.6 via OpenRouter.

    Pour les vidéos longues (≥8 min), découpe la transcription en ~3 chunks
    et lance les appels en PARALLÈLE via ThreadPoolExecutor — gain typique :
    -25% de latence, +15-20% qualité (Claude dérive moins sur des chunks courts).

    Détecte deux types de coupes :
      1. "restart" — faux départs / reformulations de phrases (tic verbal)
      2. "content" — passages à faible valeur (rétention audience)

    La partie statique du prompt (mission + exemples + règles) est cachée
    via cache_control Anthropic — économise ~50% des tokens entre chunks.

    Nécessite OPENROUTER_API_KEY dans l'environnement.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("  [SKIP] OPENROUTER_API_KEY manquante — analyse contenu ignorée.")
        print("  → Obtiens ta clé sur openrouter.ai/keys puis :")
        print("    export OPENROUTER_API_KEY='sk-or-...'")
        return []

    if not words:
        return []

    total_duration = words[-1]["end"]

    # Chunking : 1 chunk si <8 min, sinon 3 chunks équilibrés sur pauses
    target_chunks = 3 if total_duration >= 8 * 60 else 1
    chunks = _split_words_into_chunks(words, target_chunks=target_chunks)
    n_chunks = len(chunks)

    if n_chunks == 1:
        print("  Analyse Claude (contenu + restarts)...")
    else:
        print(f"  Analyse Claude — {n_chunks} chunks en parallèle (cache statique activé)...")

    all_cuts = []
    if n_chunks == 1:
        try:
            all_cuts = _call_claude_for_chunk(chunks[0], total_duration, 0, 1, api_key)
        except Exception as ex:
            print(f"  [AVERTISSEMENT] Analyse contenu échouée : {ex}")
            return []
    else:
        with ThreadPoolExecutor(max_workers=min(3, n_chunks)) as pool:
            futures = {
                pool.submit(_call_claude_for_chunk, c, total_duration, i, n_chunks, api_key): i
                for i, c in enumerate(chunks)
            }
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    chunk_cuts = fut.result()
                    all_cuts.extend(chunk_cuts)
                except Exception as ex:
                    print(f"  [AVERTISSEMENT] Chunk {idx + 1}/{n_chunks} échoué : {ex}")

    # Déduplication conservatrice : trier par start, fusionner les chevauchements
    # de < 50ms (sécurise contre les rares doublons inter-chunks ; jamais perdre
    # un cut distinct).
    def _coerce(c):
        try:
            return {
                "start": float(c.get("start", 0)),
                "end": float(c.get("end", 0)),
                "type": c.get("type", "content"),
                "reason": c.get("reason", "") or "",
            }
        except (TypeError, ValueError):
            return None

    norm = []
    for c in all_cuts:
        if not isinstance(c, dict):
            continue
        coerced = _coerce(c)
        if coerced is not None:
            norm.append(coerced)
    norm.sort(key=lambda c: c["start"])

    deduped = []
    for c in norm:
        if deduped and c["start"] <= deduped[-1]["end"] + 0.05:
            # Chevauchement (ou quasi-) → étend le précédent
            deduped[-1]["end"] = max(deduped[-1]["end"], c["end"])
            # Conserve la raison la plus longue (plus informative)
            if len(c["reason"]) > len(deduped[-1]["reason"]):
                deduped[-1]["reason"] = c["reason"]
        else:
            deduped.append(c)

    if not deduped:
        print("  Aucun passage à couper identifié.")

    # Conversion vers le format tuple attendu + validation durée min
    result = []
    n_restart, n_content = 0, 0
    for c in deduped:
        s, e = c["start"], c["end"]
        kind = c["type"]
        reason = (c["reason"] or "")[:50]
        if kind not in ("restart", "content"):
            kind = "content"
        min_dur = 0.5 if kind == "restart" else 3.0
        if e > s and (e - s) >= min_dur and s < total_duration:
            result.append((s, min(e, total_duration), kind, reason))
            if kind == "restart":
                n_restart += 1
            else:
                n_content += 1

    print(f"  Restarts détectés par Claude  : {n_restart}")
    print(f"  Contenu faible valeur         : {n_content}")
    for s, e, kind, reason in result:
        tag = "↩ restart" if kind == "restart" else "✂ content"
        print(f"    [{s:.1f}s → {e:.1f}s]  {tag}  {reason}")
    return result

def _anchor_claude_cuts(cuts, words):
    """
    Remplace les timestamps estimés par Claude par les timestamps exacts de Whisper.

    Claude identifie QUOI couper (sémantique) mais estime les timestamps par
    interpolation depuis des ancres toutes les ~12s → erreur possible de 1-3s.
    Whisper détient la vérité temporelle mot par mot.

    Pour chaque cut de type "restart" :
    - end   → timestamp du mot Whisper le plus proche (point de reprise, le plus fiable)
    - start → timestamp du mot Whisper le plus proche avant l'end estimé

    Les cuts "content" ne sont pas ancrés : leurs bornes doivent rester sur des
    frontières de phrases, et Claude les place mieux que Whisper ne peut les deviner.
    """
    if not words:
        return cuts

    word_starts = [w["start"] for w in words]
    anchored = []
    for cut_s, cut_e, kind, reason in cuts:
        if kind != "restart":
            anchored.append((cut_s, cut_e, kind, reason))
            continue

        # Mot Whisper le plus proche du END Claude (bisect + comparer voisins)
        idx_e = bisect.bisect_left(word_starts, cut_e)
        candidates_e = [k for k in (idx_e - 1, idx_e) if 0 <= k < len(words)]
        if not candidates_e:
            anchored.append((cut_s, cut_e, kind, reason))
            continue
        best_end_idx = min(candidates_e, key=lambda k: abs(words[k]["start"] - cut_e))
        if abs(words[best_end_idx]["start"] - cut_e) > 2.0:
            anchored.append((cut_s, cut_e, kind, reason))
            continue

        # START : cherche le mot le plus proche dans la fenêtre [best_end_idx - 25, best_end_idx)
        search_start = max(0, best_end_idx - 25)
        idx_s = bisect.bisect_left(word_starts, cut_s, lo=search_start, hi=best_end_idx)
        candidates_s = [k for k in (idx_s - 1, idx_s) if search_start <= k < best_end_idx]
        if not candidates_s:
            best_start_idx = search_start
        else:
            best_start_idx = min(candidates_s, key=lambda k: abs(words[k]["start"] - cut_s))

        new_s = words[best_start_idx]["start"]
        new_e = words[best_end_idx]["start"]
        if new_e - new_s >= RESTART_MIN_CUT:
            anchored.append((new_s, new_e, kind, reason))
        else:
            anchored.append((cut_s, cut_e, kind, reason))

    return anchored


def find_leading_noise(vad_segments, words):
    """
    Coupe le bruit/toux EN DÉBUT de segment VAD quand le premier mot transcrit
    arrive LEADING_NOISE_MIN secondes après le début du segment.

    Cas typique : toux → silence 0.5s → "Ok je vais..."
    Le VAD met tout dans un segment (toux < 220ms de silence avant "Ok"),
    find_coughs() ne coupe pas (le segment a un mot),
    mais la toux reste audible au début de la vidéo.
    """
    bad = []
    for seg_s, seg_e in vad_segments:
        seg_words = [w for w in words if w["start"] >= seg_s and w["start"] < seg_e]
        if not seg_words:
            continue
        first_start = seg_words[0]["start"]
        lead = first_start - seg_s
        if lead >= LEADING_NOISE_MIN:
            # Coupe depuis le début du segment jusqu'à 20ms avant le premier mot
            bad.append((seg_s, first_start - 0.02, "leading_noise", f"{lead:.2f}s avant 1er mot"))
    return bad

def _word_match(a, b):
    """Match exact, ou par préfixe si les deux mots font ≥4 chars (brand↔branding)."""
    if a == b:
        return True
    if len(a) >= 4 and len(b) >= 4:
        return a.startswith(b) or b.startswith(a)
    return False


def find_all_restarts(words):
    """
    Détection agressive de TOUS les restarts par 3 stratégies complémentaires.

    Stratégie 1 — BIGRAMME : 2 mots consécutifs identiques répétés dans ≤5s
      "on va essayer de → on va essayer de montrer"
      "de brand → et de branding"

    Stratégie 2 — MOT FORT + PAUSE : 1 mot ≥5 chars répété autour d'une pause ≥0.15s
      "essayer de → essayer de montrer" (mot "essayer" matche)
      "parfaitement → presque assuré" (mot "parfaitement" non matché → pas de cut)

    Stratégie 3 — ABANDON : mot suspens (article/prép) avant pause ≥0.20s +
      chevauchement de contenu avec la suite → phrase abandonnée
      "on va voir ce que [pause] et on va voir le rendu"
    """
    bad = []
    n = len(words)
    used = set()

    def _extend_back(idx):
        """Remonte tant que le mot précédent est un mot suspens (article, prép…)."""
        while idx > 0 and words[idx - 1]["word"] in DANGLING_WORDS:
            if words[idx]["start"] - words[idx - 1]["start"] > 1.5:
                break
            idx -= 1
        return idx

    def _add_cut(start_idx, end_idx, label_end=None):
        """Ajoute un cut et marque les mots comme utilisés."""
        cs = words[start_idx]["start"]
        ce = words[end_idx]["start"]
        if ce - cs < RESTART_MIN_CUT:
            return False
        le = label_end or min(start_idx + 6, end_idx)
        label = " ".join(words[k]["raw"] for k in range(start_idx, le))
        bad.append((cs, ce, "restart", label[:45]))
        for k in range(start_idx, end_idx):
            used.add(k)
        return True

    # ── Stratégie 1 : Bigrammes ──────────────────────────────────────────────
    for i in range(n - 1):
        if i in used:
            continue
        w1, w2 = words[i]["word"], words[i + 1]["word"]
        # Au moins 1 mot ≥3 chars dans le bigramme
        if max(len(w1), len(w2)) < 3:
            continue

        for j in range(i + 2, min(i + 14, n - 1)):
            if words[j]["start"] - words[i]["start"] > RESTART_TIME_WINDOW:
                break
            if j in used:
                continue
            w3, w4 = words[j]["word"], words[j + 1]["word"]
            if not (_word_match(w1, w3) and _word_match(w2, w4)):
                continue

            # Au moins une micro-pause (≥0.12s) entre les deux occurrences
            has_pause = any(
                words[k + 1]["start"] - words[k]["end"] >= 0.12
                for k in range(i, j)
            )
            if not has_pause:
                continue

            cut_start = _extend_back(i)
            _add_cut(cut_start, j)
            break

    # ── Stratégie 2 : Mot fort unique + pause ────────────────────────────────
    for i in range(n - 1):
        if i in used:
            continue
        w = words[i]["word"]
        if len(w) < 5:
            continue

        # Cherche une pause ≥0.15s dans les mots i-1..i+2
        pause_at = -1
        for k in range(max(0, i - 1), min(i + 3, n - 1)):
            if words[k + 1]["start"] - words[k]["end"] >= 0.15:
                pause_at = k
                break
        if pause_at < 0:
            continue

        # Cherche le même mot après la pause, dans une fenêtre de 4s
        for j in range(pause_at + 1, min(pause_at + 10, n)):
            if words[j]["start"] - words[i]["start"] > 4.0:
                break
            if j in used:
                continue
            if j == i:
                continue
            if not _word_match(words[j]["word"], w):
                continue

            # Le restart part du premier mot après la pause
            restart_idx = pause_at + 1
            cut_start = min(i, pause_at)
            cut_start = _extend_back(cut_start)

            _add_cut(cut_start, restart_idx)
            break

    # ── Stratégie 3 : Phrase abandonnée (mot suspens + pause) ────────────────
    for i in range(2, n - 2):
        if i in used:
            continue
        if words[i]["word"] not in DANGLING_WORDS:
            continue
        gap = words[i + 1]["start"] - words[i]["end"]
        if gap < 0.20 or gap > 3.0:
            continue

        # Mots de contenu (≥4 chars) avant et après la pause
        pre_start = max(0, i - 7)
        pre_content = {words[k]["word"]
                       for k in range(pre_start, i + 1) if len(words[k]["word"]) >= 4}
        if not pre_content:
            continue
        post_end = min(n, i + 9)
        post_content = {words[k]["word"]
                        for k in range(i + 1, post_end) if len(words[k]["word"]) >= 4}

        overlap = any(
            any(_word_match(pw, qw) for qw in post_content)
            for pw in pre_content
        )
        if not overlap:
            continue

        # Remonte au premier mot commun
        cut_start = i
        for k in range(pre_start, i + 1):
            wk = words[k]["word"]
            if len(wk) >= 4 and any(_word_match(wk, pw) for pw in post_content):
                cut_start = k
                break

        cut_start = _extend_back(cut_start)
        _add_cut(cut_start, i + 1)

    return bad

def fix_coherence(bad, words):
    """
    Vérifie que les cuts de type "content" commencent sur une frontière de phrase.

    Si le mot juste avant cut_start est un mot "suspens" (préposition, article,
    conjonction), le cut commence en plein milieu d'une phrase → incohérent.
    On recule cut_start jusqu'à la dernière frontière de phrase (pause ≥ 0.4s)
    pour inclure le fragment orphelin dans le cut.

    Exemple :
      cut content à 47.0s, mot précédent = "en" (dangling)
      → recule à 44.1s (dernière pause ≥ 0.4s avant "en")
      → "en mettant absolument..." est inclus dans le cut, plus de phrase suspendue
    """
    fixed = []
    for cut_s, cut_e, kind, label in bad:
        # On ne touche qu'aux cuts "content" : pour les restarts, le début est
        # intentionnellement le premier mot du faux départ, même mid-phrase.
        if kind != "content":
            fixed.append((cut_s, cut_e, kind, label))
            continue

        # Cherche l'index du dernier mot dont la fin est ≤ cut_start + 50ms
        prev_idx = -1
        for i in range(len(words) - 1, -1, -1):
            if words[i]["end"] <= cut_s + 0.05:
                prev_idx = i
                break

        if prev_idx < 0 or words[prev_idx]["word"] not in DANGLING_WORDS:
            fixed.append((cut_s, cut_e, kind, label))
            continue

        # Remonte jusqu'à la dernière frontière de phrase (pause ≥ PHRASE_BOUNDARY_GAP)
        new_start = cut_s
        for k in range(prev_idx, max(-1, prev_idx - 30), -1):
            if k == 0:
                new_start = words[0]["start"]
                break
            gap_before = words[k]["start"] - words[k - 1]["end"]
            if gap_before >= PHRASE_BOUNDARY_GAP:
                new_start = words[k]["start"]
                break

        if new_start < cut_s - 0.1:
            print(f"  [cohérence] content {cut_s:.1f}s reculé à {new_start:.1f}s "
                  f"(mot suspens avant : '{words[prev_idx]['raw']}')")
        fixed.append((new_start, cut_e, kind, label))

    return fixed


def find_abandoned_words(words):
    """
    Détecte les restarts capturés littéralement par ElevenLabs Scribe.
    ElevenLabs marque les mots abandonnés avec '--' : "brand--", "voir ce que--".

    Pour chaque mot en '--' :
    - Remonte au début du groupe de mots précédant (frontière = pause ≥ 0.25s)
    - Coupe depuis ce début jusqu'au mot suivant (qui est la reprise propre)

    Exemple :
      "et de brand-- [1.5s] et de branding de zéro"
      → coupe [début de "et", début de "et de branding"] = supprime le faux départ
    """
    bad = []
    n = len(words)
    for i, w in enumerate(words):
        if not (w["raw"].endswith("--") or w["raw"].endswith("—")):
            continue

        # Fin du cut = début du mot suivant (le restart propre)
        if i + 1 >= n:
            continue
        cut_end = words[i + 1]["start"]

        # Remonte pour trouver le début du faux départ
        cut_start = w["start"]
        for k in range(i - 1, max(-1, i - 10), -1):
            gap = words[k + 1]["start"] - words[k]["end"]
            if gap >= 0.25:
                cut_start = words[k + 1]["start"]
                break
            cut_start = words[k]["start"]

        if cut_end - cut_start < RESTART_MIN_CUT:
            continue

        label = f"abandon: {' '.join(words[k]['raw'] for k in range(max(0,i-3), i+1))}"
        bad.append((cut_start, cut_end, "abandoned", label[:50]))

    return bad


def _trim_trailing_silence(segments, words, max_trail=0.05, max_lead=0.16):
    """
    Serre les segments gardés autour de la parole réelle.

    - Fin   : si le dernier mot d'un segment se termine > max_trail avant la fin
              du segment, tronque la fin (supprime le silence résiduel).
    - Début : si le premier mot d'un segment commence > max_lead après le début
              du segment, avance le début (évite un bruit de bouche en tête).

    Adresse le cas "me voit me recoiffer" (long silence après la dernière phrase
    gardé tel quel) et les coupes qui tardent à démarrer.
    """
    trimmed = []
    for seg_s, seg_e in segments:
        seg_words = [w for w in words
                     if w["start"] >= seg_s - 0.05 and w["end"] <= seg_e + 0.05]

        if seg_words:
            first_start = seg_words[0]["start"]
            last_end    = seg_words[-1]["end"]

            # Trim début
            if first_start - seg_s > max_lead:
                seg_s = max(seg_s, first_start - max_lead)

            # Trim fin
            if seg_e - last_end > max_trail:
                seg_e = last_end + max_trail

        if seg_e - seg_s >= MIN_SEGMENT_DURATION:
            trimmed.append((seg_s, seg_e))

    return trimmed


def build_segments(vad_segments, words, duration, smart=False, tail=None):
    tail = tail or tail_profile("tight")
    bad = []

    # 1. Fillers systématiques
    for w in words:
        if w["word"] in FILLERS:
            bad.append((w["start"], w["end"], "filler", w["raw"]))

    # 2. Fillers contextuels (isolés)
    for idx, w in enumerate(words):
        if w["word"] not in CONTEXTUAL_FILLERS:
            continue
        prev_end  = words[idx - 1]["end"]  if idx > 0            else 0.0
        next_start= words[idx + 1]["start"] if idx < len(words)-1 else float("inf")
        if w["start"] - prev_end > CONTEXTUAL_MIN_GAP and next_start - w["end"] > CONTEXTUAL_MIN_GAP:
            cut_start = w["start"]
            # FIX #11 : si le mot précédent est suspens (DANGLING_WORDS), recule le cut pour inclure le fragment orphelin
            k = idx - 1
            while k >= 0 and words[k]["word"] in DANGLING_WORDS:
                if w["start"] - words[k]["start"] > 1.5:
                    break
                cut_start = words[k]["start"]
                k -= 1
            bad.append((cut_start, w["end"], "filler_ctx", w["raw"]))

    # 3. Bafouillages mot-à-mot
    # Conditions strictes pour éviter les faux positifs :
    # - mot >= STUTTER_MIN_LEN chars
    # - pas dans STUTTER_STOPWORDS
    # - répétition dans STUTTER_WINDOW secondes
    # - au max STUTTER_MAX_BETWEEN mots entre les deux occurrences
    for i, w in enumerate(words):
        clean = w["word"]
        if len(clean) < STUTTER_MIN_LEN:
            continue
        if clean in STUTTER_STOPWORDS:
            continue
        between = 0
        for j in range(i + 1, len(words)):
            nxt = words[j]
            if nxt["start"] - w["end"] > STUTTER_WINDOW:
                break
            if nxt["word"] == clean:
                bad.append((w["start"], w["end"], "stutter", w["raw"]))
                break
            between += 1
            if between > STUTTER_MAX_BETWEEN:
                break

    # 4. Répétitions de phrases
    bad += find_phrase_repeats(words)

    # 5. Pauses intra-segment (FIX 2)
    bad += find_intra_segment_gaps(words, vad_segments)

    # 6. Toux / bruits (segments VAD sans mots)
    bad += find_coughs(vad_segments, words)

    # 7. Bruit/toux EN DÉBUT de segment VAD (segment avec mots mais bruit avant le 1er)
    bad += find_leading_noise(vad_segments, words)

    # 8. Mots abandonnés ElevenLabs ('--') — restarts capturés littéralement
    bad += find_abandoned_words(words)

    # 9. Restarts (3 stratégies heuristiques) — toujours actif
    # Bigrammes, mot fort+pause, phrase abandonnée. Complémentaire avec Claude.
    bad += find_all_restarts(words)


    # 9. Analyse contenu + restarts par Claude — uniquement si --smart
    if smart:
        claude_cuts = analyze_content(words)
        claude_cuts = _anchor_claude_cuts(claude_cuts, words)  # ancre sur Whisper
        bad += claude_cuts

    # 10. Cohérence sémantique : recule les cuts "content" qui commencent mid-phrase
    bad = fix_coherence(bad, words)

    bad_sorted = sorted(bad, key=lambda x: x[0])

    # Fusion des intervalles qui se chevauchent
    merged_bad = []
    for b in bad_sorted:
        bs, be = b[0], b[1]
        if merged_bad and bs < merged_bad[-1][1]:
            merged_bad[-1] = (merged_bad[-1][0], max(merged_bad[-1][1], be),
                              merged_bad[-1][2], merged_bad[-1][3])
        else:
            merged_bad.append([bs, be, b[2], b[3]])

    # Soustraction des mauvais intervalles des segments VAD
    keep = []
    for seg_start, seg_end in vad_segments:
        s = max(0.0, seg_start - LEADING_PADDING)
        e = min(duration, seg_end + tail["trailing_padding"])
        cursor = s
        for bs, be, *_ in merged_bad:
            if be <= s or bs >= e:
                continue
            cut_start = bs - CUT_PRE_PADDING
            cut_end = be + CUT_POST_PADDING
            if cursor < cut_start and cut_start - cursor > MIN_SEGMENT_DURATION:
                keep.append((cursor, cut_start))
            cursor = max(cursor, cut_end)
        if cursor < e - MIN_SEGMENT_DURATION:
            keep.append((cursor, e))

    # Fusion des segments proches + ajout des gaps intra comme segments séparés
    # (les gaps intra créent des "trous" à l'intérieur de segments VAD —
    #  keep[] les représente déjà correctement comme deux morceaux)
    final = []
    for seg in sorted(keep):
        if seg[1] - seg[0] < MIN_SEGMENT_DURATION:
            continue
        if final and seg[0] <= final[-1][1] + 0.06:
            final[-1] = (final[-1][0], max(final[-1][1], seg[1]))
        else:
            final.append((seg[0], seg[1]))

    final = _trim_trailing_silence(final, words, max_trail=tail["trim_max_trail"])
    return final, merged_bad


def detect_silences(wav, noise_db=-32.0, min_dur=0.04):
    """
    Detection précise des silences via ffmpeg silencedetect (amplitude réelle,
    précision ms — bien plus serré que les timestamps mots ElevenLabs
    ou Silero VAD avec min_silence=220ms).

    Retourne une liste triée de (silence_start, silence_end) en secondes.
    Utilisé pour snapper les bornes de segments sur les vraies transitions
    silence→parole, plutôt que sur les `word.start`/`word.end` lâches.
    """
    print(f"  Détection silences fine (ffmpeg silencedetect, {noise_db}dB / {int(min_dur*1000)}ms)...")
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", wav,
         "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    silences = []
    cur_start = None
    for line in proc.stderr.splitlines():
        if "silence_start:" in line:
            try:
                cur_start = float(line.split("silence_start:")[1].strip().split()[0])
            except Exception:
                cur_start = None
        elif "silence_end:" in line and cur_start is not None:
            try:
                tail = line.split("silence_end:")[1].strip()
                end_val = float(tail.split("|")[0].strip().split()[0])
                silences.append((cur_start, end_val))
            except Exception:
                pass
            cur_start = None
    print(f"    {len(silences)} silences détectés")
    return silences


def snap_segments_to_silence(segments, silences, max_snap=0.30,
                             edge_pad_lead=0.04, edge_pad_trail=0.02):
    """
    Resserre les bornes des segments sur les vraies transitions silence↔parole.

    Pour chaque [s, e] :
      - Recherche un silence se TERMINANT proche de s (fenêtre ±max_snap).
        Si trouvé, avance s à `silence_end - edge_pad_lead` (préserve l'attaque).
      - Recherche un silence DÉMARRANT proche de e (fenêtre ±max_snap).
        Si trouvé, recule e à `silence_start + edge_pad_trail`.

    Ne fait JAMAIS l'inverse (n'étire pas un segment au-delà de ce que VAD/words
    ont choisi) — uniquement resserrement vers la parole réelle.

    Pourquoi : les `word.end` d'ElevenLabs traînent souvent 50–150 ms après
    l'arrêt acoustique réel. silencedetect (amplitude) voit la vraie transition.
    """
    if not silences:
        return segments
    sil_ends   = sorted(silence[1] for silence in silences)
    sil_starts = sorted(silence[0] for silence in silences)
    import bisect

    snapped = []
    for s, e in segments:
        new_s, new_e = s, e

        # START: silence_end le plus proche de s, dans [s - max_snap, s + max_snap]
        idx = bisect.bisect_left(sil_ends, s)
        candidates = []
        if idx < len(sil_ends): candidates.append(sil_ends[idx])
        if idx > 0:             candidates.append(sil_ends[idx-1])
        best = None
        for sil_e_val in candidates:
            if abs(sil_e_val - s) <= max_snap:
                if best is None or abs(sil_e_val - s) < abs(best - s):
                    best = sil_e_val
        if best is not None:
            # Speech commence à best. On garde edge_pad_lead avant.
            new_s = max(0.0, best - edge_pad_lead)

        # END: silence_start le plus proche de e, dans [e - max_snap, e + max_snap]
        idx = bisect.bisect_left(sil_starts, e)
        candidates = []
        if idx < len(sil_starts): candidates.append(sil_starts[idx])
        if idx > 0:               candidates.append(sil_starts[idx-1])
        best = None
        for sil_s_val in candidates:
            if abs(sil_s_val - e) <= max_snap:
                if best is None or abs(sil_s_val - e) < abs(best - e):
                    best = sil_s_val
        if best is not None:
            # Speech s'arrête à best. On garde edge_pad_trail après.
            new_e = best + edge_pad_trail

        if new_e - new_s >= MIN_SEGMENT_DURATION:
            snapped.append((new_s, new_e))

    return snapped


def apply_tail_bounds(segments, bad_intervals=None):
    """
    Garde-fou du mode de fin "relaxed" : une fin de segment relâchée ne doit
    JAMAIS déborder au-delà de ce qui est légitime. Deux bornes :

      (a) le début du prochain intervalle supprimé (filler, bafouillage, restart)
          — sinon la respiration ajoutée réintroduit le "euh" qu'on venait de couper ;
      (b) le début du segment gardé suivant — sinon le même audio est exporté
          deux fois et on entend un bégaiement au montage.

    Ne touche jamais au début des segments. No-op si le mode est "tight"
    (fonction simplement pas appelée) ou si aucune borne ne mord.

    Effet de bord assumé : un éclat de segment qui démarre à moins de
    MIN_SEGMENT_DURATION du début d'une coupe tombe sous le seuil une fois
    borné et disparaît. Par construction il était presque entièrement DANS la
    coupe (typiquement la première syllabe d'une phrase répétée) — le laisser
    passer, c'est le flash de 100 ms que le mode tight garde aujourd'hui.
    """
    if not segments:
        return segments

    bads = sorted((float(b[0]), float(b[1])) for b in (bad_intervals or []))
    bad_starts = [b[0] for b in bads]

    seq = sorted(segments)
    bounded = []
    for i, (s, e) in enumerate(seq):
        limit = e

        # (a) prochain intervalle coupé démarrant après le début du segment
        j = bisect.bisect_right(bad_starts, s)
        if j < len(bads):
            limit = min(limit, bads[j][0] - CUT_PRE_PADDING)

        # (b) segment gardé suivant
        if i + 1 < len(seq):
            limit = min(limit, seq[i + 1][0])

        if limit > s:
            e = min(e, limit)

        if e - s >= MIN_SEGMENT_DURATION:
            bounded.append((s, e))

    return bounded


def snap_segments_to_frames(segments, fps):
    """
    Quantize les bornes (start, end) de chaque segment sur la frontière de frame
    la plus proche à la fréquence `fps` source. Élimine le jitter sub-frame
    aux cuts : sans ce snap, les bornes flottent dans un intervalle de ±1/fps
    seconde, ce qui se traduit en drift accumulé à l'export.

    Garantit :
      - chaque segment dure un nombre ENTIER de frames source
      - les bornes sont des multiples exacts de 1/fps
    """
    if not fps or fps <= 0:
        return segments
    period = 1.0 / fps
    snapped = []
    for s, e in segments:
        sn_s = round(s / period) * period
        sn_e = round(e / period) * period
        # Garantit au moins 1 frame
        if sn_e - sn_s < period * 0.5:
            sn_e = sn_s + period
        snapped.append((sn_s, sn_e))
    return snapped

# ─── Export FFmpeg — libx264 au bitrate source + concat demuxer ──────────────

AUDIO_SR = 48000            # taux audio interne (PCM intermédiaire + AAC final)
EDGE_FADE_S = 0.003         # FIX SYNC #7 : afade 3ms in/out par clip (anti-click, inaudible)


def _round_div(num, den):
    """Division entière arrondie au plus proche, pour nombres positifs."""
    return (num + den // 2) // den


def _time_to_frame(t, fps_n, fps_d):
    """Convertit un timestamp en index de frame sur la grille rationnelle source."""
    return int(round(max(0.0, t) * fps_n / fps_d))


def _samples_for_frames(frame_count, fps_n, fps_d, sr=AUDIO_SR):
    """
    Nombre d'échantillons audio correspondant à `frame_count` frames vidéo.
    Calcul cumulatif arrondi au plus proche pour éviter le biais systématique
    d'un floor à 29.97/59.94 fps.
    """
    return _round_div(frame_count * fps_d * sr, fps_n)


def _probe_frame_count(clip_path):
    """Compte exact des frames vidéo dans un clip. None si indéterminable."""
    r = subprocess.run([
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-count_frames",
        "-show_entries", "stream=nb_read_frames",
        "-of", "default=nokey=1:noprint_wrappers=1",
        clip_path,
    ], capture_output=True, text=True)
    try:
        return int(r.stdout.strip())
    except (ValueError, AttributeError):
        return None


def _build_v_enc(src_vbr):
    """Choisit l'encoder vidéo + paramètres communs à toutes les passes."""
    if HAS_VIDEOTOOLBOX:
        target_vbr = max(int(src_vbr * 1.2), 15_000_000)
        return [
            "-c:v", "h264_videotoolbox",
            "-b:v", str(target_vbr),
            "-bf", "0",
            "-pix_fmt", "yuv420p",
            # FIX SYNC #19 : prio_speed pousse VT au max → ~30-50% plus rapide
            # sans perte qualité significative (bitrate cible préservé)
            "-prio_speed", "1",
        ], "videotoolbox (prio_speed)"
    return [
        "-c:v", "libx264",
        "-crf", "17",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-bf", "0",
    ], "libx264 CRF17"


def _plan_segments(segments, fps_n, fps_d, speed):
    """
    Plan d'export : pour chaque segment, retourne (input_frames, n_frames, n_samples).
    Arithmétique entière exacte, accumulation cumulative pour zéro drift.
    """
    input_frame_plan = []
    frame_plan = []
    samples_plan = []
    cum_in = 0
    cum_out = 0
    cum_samp = 0
    for start, end in segments:
        sf = _time_to_frame(start, fps_n, fps_d)
        ef = _time_to_frame(end, fps_n, fps_d)
        inp = max(1, ef - sf)
        cum_in += inp
        if speed != 1.0:
            nxt = int(round(cum_in / speed))
            nxt = max(cum_out + 1, nxt)
        else:
            nxt = cum_in
        nxt_samp = _samples_for_frames(nxt, fps_n, fps_d)
        if nxt_samp <= cum_samp:
            nxt_samp = cum_samp + 1
        input_frame_plan.append(inp)
        frame_plan.append(nxt - cum_out)
        samples_plan.append(nxt_samp - cum_samp)
        cum_out = nxt
        cum_samp = nxt_samp
    return input_frame_plan, frame_plan, samples_plan, cum_out, cum_samp


def _build_filter_complex(segments, input_frame_plan, frame_plan, samples_plan,
                          total_samples, fps_str, lut, speed):
    """Construit le filter_complex single-pass pour un set de segments."""
    parts = []
    for i, ((start, end), input_frames, n_frames, n_samples) in enumerate(
        zip(segments, input_frame_plan, frame_plan, samples_plan)
    ):
        # FIX SYNC #16 : effective_speed = input_frames / n_frames → audio+vidéo lock
        if speed != 1.0 and n_frames > 0:
            effective_speed = input_frames / n_frames
        else:
            effective_speed = 1.0

        vp = f"[0:v]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS"
        if lut:
            vp += f",lut3d='{lut}':interp=trilinear"
        if effective_speed != 1.0:
            vp += f",setpts=PTS/{effective_speed:.9f}"
        vp += f"[v{i}]"
        parts.append(vp)

        ap = (
            f"[0:a]atrim=start={start:.6f}:end={end:.6f},asetpts=PTS-STARTPTS,"
            f"aresample={AUDIO_SR}:async=1:first_pts=0"
        )
        if effective_speed != 1.0:
            ap += f",atempo={effective_speed:.9f}"
        ap += f",apad=whole_len={n_samples},atrim=end_sample={n_samples}"
        seg_dur_s = n_samples / AUDIO_SR
        fade_out_st = max(0.0, seg_dur_s - EDGE_FADE_S)
        ap += (
            f",afade=t=in:st=0:d={EDGE_FADE_S:.6f}"
            f",afade=t=out:st={fade_out_st:.6f}:d={EDGE_FADE_S:.6f}"
        )
        ap += f"[a{i}]"
        parts.append(ap)

    n = len(segments)
    concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(n))
    parts.append(f"{concat_inputs}concat=n={n}:v=1:a=1[cv][ca]")
    parts.append(f"[cv]fps=fps={fps_str}:round=near[outv]")
    parts.append(
        f"[ca]aresample={AUDIO_SR}:async=1:first_pts=0,"
        f"apad=whole_len={total_samples},"
        f"atrim=end_sample={total_samples}[outa]"
    )
    return ";".join(parts)


def _export_single_pass(video, segments, output, speed, lut, audio_codec,
                        fps_n, fps_d, v_enc, log_prefix=""):
    """
    Single-pass filter_complex pour un set de segments.
    Aucun clip intermédiaire, un seul encode → zéro fragilité de concat.
    """
    fps_str = f"{fps_n}/{fps_d}"
    input_frame_plan, frame_plan, samples_plan, total_frames, total_samples = \
        _plan_segments(segments, fps_n, fps_d, speed)

    filter_complex = _build_filter_complex(
        segments, input_frame_plan, frame_plan, samples_plan,
        total_samples, fps_str, lut, speed,
    )

    with tempfile.TemporaryDirectory() as tmp:
        fc_path = os.path.join(tmp, "filter_complex.txt")
        with open(fc_path, "w") as f:
            f.write(filter_complex)

        if audio_codec == "pcm_s16le":
            a_enc = ["-c:a", "pcm_s16le", "-ar", str(AUDIO_SR)]
        else:
            a_enc = ["-c:a", "aac", "-b:a", "320k", "-ar", str(AUDIO_SR)]

        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats",
            "-i", video,
            "-filter_complex_script", fc_path,
            "-map", "[outv]", "-map", "[outa]",
            *v_enc,
            "-fps_mode", "cfr",
            *a_enc,
            "-movflags", "+faststart",
            "-frames:v", str(total_frames),
            output,
        ]
        result = subprocess.run(cmd, capture_output=False)
        if result.returncode != 0:
            raise RuntimeError(f"{log_prefix}export single-pass échoué (return {result.returncode})")
    return total_frames, total_samples


def _encode_one_segment(args):
    """
    Encode UN segment en MOV intermédiaire (H.264 + PCM).
    Filter chain MINIMALE : un seul trim, un seul atrim → graph trivial, encode rapide.

    Workhorse de la stratégie per-segment parallèle (FIX SYNC #20). Contrairement à
    filter_complex single-pass où le graph contient N trim filters qui dégradent
    en O(N) par frame, ici chaque ffmpeg a un graph constant → encode au taux
    max du HW encoder.
    """
    (i, video, start, end, input_frames, n_frames, n_samples,
     speed, lut, fps_n, fps_d, v_enc, out_clip) = args

    fps_str = f"{fps_n}/{fps_d}"
    input_dur = max(0.0, end - start)
    vid_dur = n_frames * fps_d / fps_n
    aud_dur = n_samples / AUDIO_SR

    # FIX SYNC #16 : effective_speed lock audio/vidéo
    if speed != 1.0 and n_frames > 0:
        eff_speed = input_frames / n_frames
    else:
        eff_speed = 1.0

    # FIX SYNC #20 : SEEK_PRE = 2s (GOP typique HEVC iPhone) → suffisant pour
    # tomber sur le keyframe précédent. Réduit le decode wasted de 3s/segment
    # × 200 segments = 10 min de travail en moins.
    SEEK_PRE = 2.0
    seek_start = max(0.0, start - SEEK_PRE)
    local_start = start - seek_start
    local_end = local_start + input_dur

    v_filter = (
        f"trim=start={local_start:.6f}:end={local_end:.6f},"
        f"setpts=PTS-STARTPTS"
    )
    if lut:
        v_filter += f",lut3d='{lut}':interp=trilinear"
    if eff_speed != 1.0:
        v_filter += f",setpts=PTS/{eff_speed:.9f}"
    v_filter += f",fps=fps={fps_str}:round=near"

    a_filter = (
        f"atrim=start={local_start:.6f}:end={local_end:.6f},"
        f"asetpts=PTS-STARTPTS,"
        f"aresample={AUDIO_SR}:async=1:first_pts=0"
    )
    if eff_speed != 1.0:
        a_filter += f",atempo={eff_speed:.9f}"
    a_filter += f",apad=whole_len={n_samples},atrim=end_sample={n_samples}"
    fade_out_st = max(0.0, aud_dur - EDGE_FADE_S)
    a_filter += (
        f",afade=t=in:st=0:d={EDGE_FADE_S:.6f}"
        f",afade=t=out:st={fade_out_st:.6f}:d={EDGE_FADE_S:.6f}"
    )

    # FIX SYNC #20 : -hwaccel videotoolbox sur Apple Silicon → décodage HEVC
    # en HW dédié. Gros gain sur sources HEVC iPhone (gpu decoder + cpu filter
    # peuvent travailler en parallèle au lieu de seriaiser sur le CPU).
    hwaccel = ["-hwaccel", "videotoolbox"] if HAS_VIDEOTOOLBOX else []

    r = subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        *hwaccel,
        "-ss", f"{seek_start:.6f}",
        "-i", video,
        "-vf", v_filter,
        "-af", a_filter,
        "-fps_mode", "cfr",
        *v_enc,
        "-c:a", "pcm_s16le",
        "-frames:v", str(n_frames),
        "-t", f"{max(vid_dur, aud_dur):.9f}",
        out_clip,
    ], capture_output=True, text=True)

    if r.returncode != 0:
        return i, None, input_dur, r.stderr[-400:]
    return i, out_clip, input_dur, None


def export(video, segments, output, speed=1.0, lut=None, workers=4,
           audio_codec="aac"):
    """
    Export robuste + rapide (FIX SYNC #18 + #19 + #20).

    Stratégie tri-modale, choisie automatiquement :

    - **Per-segment parallèle** (N >= 8 et workers > 1) : un ffmpeg PAR segment,
      avec un graph filter minimal (un seul trim), exécutés en parallèle.
      → Speedup LINÉAIRE avec workers (1.5-4× selon HW encoder), évite l'O(N²)
        du filter_complex single-pass quand N grandit (200 segments + source 47 min
        peuvent prendre 100 min en single-pass vs 10-15 min en per-segment).
      → Concat-demuxer final : tous les clips partagent IDENTIQUEMENT les mêmes
        params encoder (même CLI flags) → SPS/timebase identiques → safe pour
        `-c:v copy` ; audio AAC encodé une seule fois au final.
      → Quality identique au single-pass (un seul encode generation par segment).

    - **Single-pass filter_complex** (N < 8 ou workers <= 1) : un seul ffmpeg
      qui fait tout le boulot dans un graph filter avec concat filter natif.
      → Optimal pour les petits N, élimine les boundaries.

    `audio_codec` : "aac" (final) ou "pcm_s16le" (intermédiaire pour polish).
    """
    n = len(segments)
    if n == 0:
        print("[ERREUR] Aucun segment à exporter.", file=sys.stderr)
        sys.exit(1)

    src_vbr = get_video_bitrate(video)
    fps_n, fps_d = get_video_fps_rational(video)
    fps_str = f"{fps_n}/{fps_d}"
    v_enc, enc_name = _build_v_enc(src_vbr)

    # FIX SYNC #20 : seuil per-segment basé sur N. Sur ANY hardware, le filter_complex
    # single-pass dégrade en O(N) state par frame avec N trim filters → 200 segments
    # × 47 min source = ~100 min wallclock. Per-segment parallèle = O(1) par segment.
    PARALLEL_MIN_SEGS = 8
    n_workers = max(1, int(workers or 1))
    use_per_segment = n_workers > 1 and n >= PARALLEL_MIN_SEGS

    if not use_per_segment:
        print(f"  Export single-pass : {n} segments ({enc_name} @ {fps_str} CFR)")
        try:
            total_frames, total_samples = _export_single_pass(
                video, segments, output, speed, lut, audio_codec,
                fps_n, fps_d, v_enc,
            )
        except RuntimeError as e:
            print(f"[ERREUR] {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # FIX SYNC #20 : PER-SEGMENT PARALLEL — un ffmpeg par segment avec filter
        # chain MINIMAL. Speedup linéaire avec workers. Concat-demuxer safe car
        # tous les segments encodés avec mêmes flags → SPS/timebase identiques.
        input_frame_plan, frame_plan, samples_plan, total_frames, total_samples = \
            _plan_segments(segments, fps_n, fps_d, speed)

        print(f"  Export per-segment parallel : {n} segments × {n_workers} workers "
              f"({enc_name} @ {fps_str} CFR)")

        with tempfile.TemporaryDirectory() as tmp:
            clip_paths = [os.path.join(tmp, f"seg{i:04d}.mov") for i in range(n)]
            tasks = [
                (i, video, segments[i][0], segments[i][1],
                 input_frame_plan[i], frame_plan[i], samples_plan[i],
                 speed, lut, fps_n, fps_d, v_enc, clip_paths[i])
                for i in range(n)
            ]

            total_input = sum(max(0.0, e - s) for s, e in segments)
            encoded = 0.0
            errors = []
            with ThreadPoolExecutor(max_workers=n_workers) as pool:
                futures = [pool.submit(_encode_one_segment, t) for t in tasks]
                done = 0
                for fut in as_completed(futures):
                    i, clip, seg_dur, err = fut.result()
                    done += 1
                    encoded += seg_dur
                    if err:
                        errors.append((i, err))
                        print(f"  [seg {i+1:04d}] ✗ {err}")
                    else:
                        pct = 100.0 * encoded / total_input if total_input else 100.0
                        print(f"  Progress : {done}/{n} seg ({pct:.0f}%)", flush=True)

            if errors:
                print(f"[ERREUR] {len(errors)} segments ont échoué.", file=sys.stderr)
                sys.exit(1)

            # Concat-demuxer : tous les clips ont MÊMES params encoder
            # → SPS/timebase identiques → -c:v copy safe.
            list_file = os.path.join(tmp, "concat.txt")
            with open(list_file, "w") as f:
                for cp in clip_paths:
                    f.write(f"file '{cp}'\n")

            if audio_codec == "pcm_s16le":
                a_enc = ["-c:a", "pcm_s16le", "-ar", str(AUDIO_SR)]
                print(f"  Concat {n} segments → PCM intermédiaire")
            else:
                a_enc = ["-c:a", "aac", "-b:a", "320k", "-ar", str(AUDIO_SR)]
                print(f"  Concat {n} segments → AAC 320k unique")

            # FIX SYNC #9 : aresample=async=1 + apad/atrim sur sample count total
            audio_final_filter = (
                f"aresample={AUDIO_SR}:async=1:first_pts=0,"
                f"apad=whole_len={total_samples},"
                f"atrim=end_sample={total_samples}"
            )
            result = subprocess.run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats",
                "-f", "concat", "-safe", "0", "-i", list_file,
                "-c:v", "copy",
                "-af", audio_final_filter,
                *a_enc,
                "-movflags", "+faststart",
                output,
            ], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[ERREUR] concat échoué :\n{result.stderr[-400:]}", file=sys.stderr)
                sys.exit(1)

    # Audit post-export
    actual_frames = _probe_frame_count(output)
    if actual_frames is not None:
        if abs(actual_frames - total_frames) > 1:
            print(f"  [WARN] frames produites {actual_frames} ≠ plan {total_frames}")
        else:
            print(f"  [AV sync] ✓ {actual_frames} frames produites (plan = {total_frames})")
    warn_av_sync(output, "après export")

# ─── Polish audio (post-concat, inspiré Auphonic) ────────────────────────────

def _vad_speech_gate(audio_in_wav,
                     atten_db=80, pad_ms=60, fade_ms=30,
                     vad_threshold=0.35, min_silence_ms=120):
    """
    Silence les segments non-voix (gap inter-mots, respirations, frottements)
    avec un gate -80dB et crossfade. C'est ce qu'Auphonic fait (noise floor -180dB
    vs -72dB pour DeepFilterNet seul) — la dernière marche pour matcher Auphonic.

    Réutilise Silero VAD déjà chargé dans la pipeline.
    """
    try:
        import soundfile as sf
        import numpy as _np
        import torch as _torch
        try:
            from scipy.ndimage import uniform_filter1d
        except ImportError:
            print("  [AVERTISSEMENT] scipy indispo, skip speech gate")
            return False

        print(f"  Speech gate VAD (floor -{atten_db}dB, pad {pad_ms}ms)...")
        y, sr = sf.read(audio_in_wav)
        if y.ndim > 1:
            y = y.mean(axis=1)
        y = y.astype(_np.float32)

        model, utils = _torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad", force_reload=False, trust_repo=True,
        )
        get_speech_timestamps = utils[0]
        # VAD à 16k
        import librosa as _lr
        y16 = _lr.resample(y, orig_sr=sr, target_sr=16000) if sr != 16000 else y
        ts = get_speech_timestamps(
            _torch.from_numpy(y16), model, sampling_rate=16000,
            threshold=vad_threshold, min_speech_duration_ms=80,
            min_silence_duration_ms=min_silence_ms, return_seconds=True,
        )

        floor = 10 ** (-atten_db / 20.0)  # -80 dB → 0.0001
        fade_samp = int(sr * fade_ms / 1000)
        env = _np.full(len(y), floor, dtype=_np.float32)
        for t in ts:
            s = max(0, int((t["start"] - pad_ms / 1000) * sr))
            e = min(len(y), int((t["end"] + pad_ms / 1000) * sr))
            env[s:e] = 1.0
        env = uniform_filter1d(env, size=max(2, fade_samp * 2))

        sf.write(audio_in_wav, (y * env).astype(_np.float32), sr)
        return True
    except Exception as e:
        print(f"  [AVERTISSEMENT] speech gate échec ({e}) — skip")
        return False


def _deepfilternet_denoise(audio_in_wav):
    """
    Pré-traitement ML : DeepFilterNet3 supprime respirations, frottements,
    bruits non-stationnaires et atténue la réverbération de pièce — choses que
    ffmpeg classique (afftdn) ne sait pas faire. Sortie : nouveau wav 48 kHz
    placé à côté de l'entrée. None si DeepFilterNet indisponible (fallback
    silencieux sur la chaîne ffmpeg).
    """
    try:
        # Shim torchaudio.backend.common.AudioMetaData (supprimé en torchaudio 2.11)
        import sys as _sys, types as _types
        if "torchaudio.backend.common" not in _sys.modules:
            _tb  = _types.ModuleType("torchaudio.backend")
            _tbc = _types.ModuleType("torchaudio.backend.common")
            class _Stub: pass
            _tbc.AudioMetaData = _Stub
            _sys.modules["torchaudio.backend"] = _tb
            _sys.modules["torchaudio.backend.common"] = _tbc
            import torchaudio as _ta
            _ta.backend = _tb
        from df.enhance import enhance, init_df
        import soundfile as sf
        import torch
        import numpy as _np

        print("  DeepFilterNet3 (ML denoise + dereverb)...")
        df_model, df_state, _ = init_df()
        sr = df_state.sr()
        audio, src_sr = sf.read(audio_in_wav)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if src_sr != sr:
            import librosa as _lr
            audio = _lr.resample(audio.astype(_np.float32),
                                 orig_sr=src_sr, target_sr=sr)
        n_in = len(audio)
        audio_t = torch.from_numpy(audio.astype(_np.float32)).unsqueeze(0)
        enhanced = enhance(df_model, df_state, audio_t)
        out_arr = enhanced.squeeze().cpu().numpy()
        # DeepFilterNet pad=True peut allonger légèrement — tronquer à la longueur exacte
        out_arr = out_arr[:n_in]
        out_path = audio_in_wav.replace(".wav", "_dfnet.wav")
        sf.write(out_path, out_arr, sr)
        return out_path
    except Exception as e:
        print(f"  [AVERTISSEMENT] DeepFilterNet indisponible ({e}) — skip")
        return None


def _measure_chain_latency(filter_chain_str, sr=AUDIO_SR, duration_s=3.0):
    """
    FIX SYNC #10 — mesure la latence (group delay) d'une chaîne de filtres audio
    par impulse response. Sans compensation, la chaîne polish (afftdn + EQ +
    aexciter + deesser + acompressor) décale l'énergie audio de ~30-60 ms par
    rapport à la vidéo → décalage A/V perceptible après polish.

    Retourne la latence en secondes (0.0 si mesure indisponible / échec).
    """
    try:
        import numpy as _np
        import soundfile as _sf
    except ImportError:
        return 0.0

    with tempfile.TemporaryDirectory() as tmp:
        imp_in  = os.path.join(tmp, "impulse_in.wav")
        imp_out = os.path.join(tmp, "impulse_out.wav")

        n = int(sr * duration_s)
        impulse_pos = sr  # impulse à t=1.0s pour laisser de la place avant
        sig = _np.zeros(n, dtype=_np.float32)
        sig[impulse_pos] = 1.0
        _sf.write(imp_in, sig, sr)

        r = subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", imp_in, "-af", filter_chain_str,
            "-c:a", "pcm_f32le", "-ar", str(sr), imp_out,
        ], capture_output=True, text=True)
        if r.returncode != 0:
            return 0.0

        try:
            out, _ = _sf.read(imp_out)
            if out.ndim > 1:
                out = out.mean(axis=1)
            # Cherche le pic dans une fenêtre [-50ms, +300ms] autour de l'impulse
            search_start = max(0, impulse_pos - int(sr * 0.05))
            search_end   = min(len(out), impulse_pos + int(sr * 0.3))
            region = out[search_start:search_end]
            if len(region) == 0:
                return 0.0
            peak_idx = search_start + int(_np.argmax(_np.abs(region)))
            return max(0.0, (peak_idx - impulse_pos) / sr)
        except Exception:
            return 0.0


def _measure_loudness(audio_path, target_lufs):
    """
    Pass-1 loudnorm : analyse l'audio et renvoie les mesures pour pass-2.
    Returns dict {input_i, input_tp, input_lra, input_thresh, target_offset} ou None.
    """
    result = subprocess.run([
        "ffmpeg", "-hide_banner", "-nostats", "-i", audio_path,
        "-af", f"loudnorm=I={target_lufs}:TP={LOUDNESS_TRUE_PEAK}:"
               f"LRA={LOUDNESS_LRA}:print_format=json",
        "-f", "null", "-",
    ], capture_output=True, text=True)
    stderr = result.stderr or ""
    # Le JSON est imprimé à la fin de stderr ; on prend le dernier bloc { ... }.
    start = stderr.rfind("{")
    end   = stderr.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(stderr[start:end + 1])
    except json.JSONDecodeError:
        return None
    required = ("input_i", "input_tp", "input_lra", "input_thresh", "target_offset")
    if not all(k in data for k in required):
        return None
    # Sécurité : si input_i = -inf (audio quasi muet), on bypass le 2-pass.
    try:
        if float(data["input_i"]) < -70:
            return None
    except (ValueError, TypeError):
        return None
    return data


def polish_audio(video_in, video_out, lufs=LOUDNESS_TARGET_LUFS,
                 denoise=True, deesser=True, hpf=True,
                 autoeq=True, deplosive=False, bwe=True, hum=False):
    """
    Stage 3 : traitement audio post-concat, chaîne mastering voix complète.
    
    BEST PRACTICES (Talking Head) :
    1. Noise Gate/Reduction (afftdn)
    2. Highpass 80Hz (rumble)
    3. EQ (Presence boost 3kHz + Warmth 250Hz)
    4. De-esser (sibilances)
    5. Compression (leveling)
    6. Loudnorm (YouTube -14 LUFS)
    """
    with tempfile.TemporaryDirectory() as tmp:
        audio_in  = os.path.join(tmp, "audio_48k.wav")
        audio_dn  = os.path.join(tmp, "audio_dn.wav")
        audio_eq  = os.path.join(tmp, "audio_eq.wav")

        print("  Extraction audio 48kHz...")
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", video_in, "-vn", "-ar", "48000", "-ac", "1",
            "-c:a", "pcm_s16le", audio_in,
        ], "extraction audio polish")

        # ── Stage 0 : DeepFilterNet3 (ML denoise + dereverb) ──
        if denoise and USE_DEEPFILTERNET:
            denoised = _deepfilternet_denoise(audio_in)
            if denoised is not None:
                audio_in = denoised  # remplace pour la suite de la chaîne

        # ── Stage 0.5 : Speech gate VAD (match Auphonic — silence respirations/frottements) ──
        if denoise and USE_SPEECH_GATE:
            _vad_speech_gate(audio_in,
                             atten_db=VAD_GATE_ATTEN_DB,
                             pad_ms=VAD_GATE_PAD_MS,
                             fade_ms=VAD_GATE_FADE_MS)

        # ── Stage A : denoise → HPF/LPF → EQ → exciter → deesser → compresseur ──
        # Chaîne simplifiée : un seul étage dynamique (acompressor), loudnorm 2-pass
        # fera le leveling final. Évite pumping/musical-noise.
        chain = []

        # Debruitage doux (calé Auphonic, valeur Optuna)
        if denoise:
            chain.append(f"afftdn=nr={AFFTDN_NR}:nf=-25")

        if hum:
            for f in (50, 100, 150, 200):
                chain.append(f"bandreject=f={f}:w=4")

        if hpf:
            chain.append(f"highpass=f={HPF_FREQ_HZ}:p=2")
            if deplosive:
                chain.append(f"highpass=f={HPF_FREQ_HZ}:p=2")

        # Lowpass calé Auphonic (~10.9 kHz — voix chaude, pas brillante)
        chain.append(f"lowpass=f={LPF_FREQ_HZ}")

        if autoeq:
            # UN seul passage EQ (VOICE_EQ_CURVE). L'anequalizer redondant a été retiré.
            for f, q, g in VOICE_EQ_CURVE:
                chain.append(f"equalizer=f={f}:t=q:w={q}:g={g}")

        # Exciter AVANT compresseur (sinon ses harmoniques sont re-comprimées)
        if bwe:
            chain.append(
                f"aexciter=amount={BWE_AMOUNT}:drive={BWE_DRIVE}"
                f":blend=0:freq={BWE_FREQ}:ceil={BWE_CEIL}"
            )

        if deesser:
            chain.append(f"deesser=i={DEESSER_INTENSITY}")

        # Étage dynamique UNIQUE. compand-gate et dynaudnorm retirés (cascade → pumping).
        chain.append(
            f"acompressor=threshold={COMP_THRESH_DB}dB:ratio={COMP_RATIO}"
            f":attack={COMP_ATTACK_MS}:release={COMP_RELEASE_MS}"
            f":makeup={COMP_MAKEUP_DB}"
        )

        af_base = ",".join(chain)
        print(f"  Filter chain : {af_base}")

        # FIX SYNC #10 : mesure la latence (group delay) de la chaîne via impulse.
        # On la compense ensuite par atrim=start={latency},apad au mux final
        # → l'énergie audio reste alignée sur la vidéo après polish.
        chain_latency_s = _measure_chain_latency(af_base, sr=AUDIO_SR)
        if chain_latency_s > 0:
            print(f"  Latence chaîne mesurée : {chain_latency_s*1000:.1f}ms (compensée au mux)")

        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", audio_in, "-af", af_base,
            "-c:a", "pcm_f32le", "-ar", "48000", audio_eq,
        ], "filter chain stage A")

        # ── Stage B : loudnorm 2-pass (EBU R128 vrai) ──
        print("  Loudnorm pass 1 (mesure)...")
        measured = _measure_loudness(audio_eq, lufs)
        if measured:
            print(
                f"    mesuré : I={measured['input_i']} LU  "
                f"TP={measured['input_tp']} dBTP  "
                f"LRA={measured['input_lra']} LU"
            )
            ln_filter = (
                f"loudnorm=I={lufs}:TP={LOUDNESS_TRUE_PEAK}:LRA={LOUDNESS_LRA}"
                f":measured_I={measured['input_i']}"
                f":measured_TP={measured['input_tp']}"
                f":measured_LRA={measured['input_lra']}"
                f":measured_thresh={measured['input_thresh']}"
                f":offset={measured['target_offset']}"
                f":linear=true:print_format=summary"
            )
        else:
            print("    [AVERTISSEMENT] mesure indispo → fallback single-pass")
            ln_filter = (
                f"loudnorm=I={lufs}:TP={LOUDNESS_TRUE_PEAK}"
                f":LRA={LOUDNESS_LRA}:print_format=summary"
            )

        # ── Stage B+C fusionnés : loudnorm pass-2 + comp. latence + apad + mux ──
        # FIX SYNC #10 : compensation de latence chaîne (atrim=start + apad au bout)
        #   → décale l'énergie audio de -chain_latency, repad la fin pour préserver durée
        # FIX SYNC #14 : aresample=async=1 absorbe les sub-samples résiduels du mux
        # -shortest retiré : si loudnorm raccourcit légèrement l'audio, il coupait la vidéo.
        # À la place : apad aligne l'audio sur la durée exacte de la vidéo, -t coupe net.
        print("  Loudnorm pass 2 + comp. latence + mux (fusionnés)...")
        polish_vid_dur = get_stream_duration(video_in, "v:0")

        # Compensation de latence : atrim AVANT loudnorm, apad/whole_dur au bout
        compensation_parts = []
        if chain_latency_s > 0.001:
            compensation_parts.append(
                f"atrim=start={chain_latency_s:.6f},asetpts=PTS-STARTPTS"
            )
        compensation_parts.append(ln_filter)
        compensation_parts.append(f"aresample=async=1:first_pts=0")
        compensation_parts.append(f"apad=whole_dur={polish_vid_dur:.6f}")
        af_final = ",".join(compensation_parts)

        result = subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", video_in, "-i", audio_eq,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy",
            "-af", af_final,
            "-c:a", "aac", "-b:a", "320k",
            "-t", f"{polish_vid_dur:.6f}",
            video_out,
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ERREUR] polish_audio mux échoué :\n{result.stderr}", file=sys.stderr)
            sys.exit(1)
        warn_av_sync(video_out, "après polish")


# ─── Main ─────────────────────────────────────────────────────────────────────

def _notify(title, message):
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}" sound name "Glass"'
        ], check=False)
    except Exception:
        pass


def _run_export_and_post(video, segments, output, args):
    """
    FIX SYNC #11 — chaîne export+polish à encodage AAC UNIQUE.

    - Si --no-polish : export direct en AAC.
    - Sinon : export intermédiaire en PCM (MKV à côté de l'output), puis polish
      qui produit le MP4 final en encodant AAC une seule fois → zéro double-priming,
      zéro génération AAC en cascade.
    """
    if args.no_polish:
        export(video, segments, output, speed=args.speed,
               lut=args.apply_lut, workers=args.workers,
               audio_codec="aac")
        return

    suffix = Path(output).suffix
    intermediate = output[:-len(suffix)] + "_pcm.mkv"

    export(video, segments, intermediate, speed=args.speed,
           lut=args.apply_lut, workers=args.workers,
           audio_codec="pcm_s16le")

    print("\n[Polish audio]")
    polish_audio(intermediate, output, lufs=args.lufs,
                 denoise=not args.no_denoise,
                 deesser=not args.no_deesser,
                 hpf=not args.no_hpf,
                 autoeq=not args.no_autoeq,
                 deplosive=args.deplosive,
                 bwe=not args.no_bwe,
                 hum=args.hum)
    try:
        os.remove(intermediate)
    except OSError:
        pass
    print(f"  ✓ Audio polished → {Path(output).name}")


def _post_process(output, args):
    """Compat shim — polish ré-exécuté sur un MP4 AAC existant (mode --from-json
    legacy ou re-traitement). Le flux normal passe par _run_export_and_post()
    pour l'encodage AAC unique. Ici, on accepte la double-passe AAC pour ne
    pas casser les workflows externes qui appellent encore _post_process().
    """
    suffix = Path(output).suffix
    if not args.no_polish:
        print("\n[Polish audio]")
        polished = output[:-len(suffix)] + "_polish" + suffix
        polish_audio(output, polished, lufs=args.lufs,
                     denoise=not args.no_denoise,
                     deesser=not args.no_deesser,
                     hpf=not args.no_hpf,
                     autoeq=not args.no_autoeq,
                     deplosive=args.deplosive,
                     bwe=not args.no_bwe,
                     hum=args.hum)
        os.replace(polished, output)
        print(f"  ✓ Audio polished → {Path(output).name}")

def main():
    parser = argparse.ArgumentParser(description="Auto-éditeur vidéo français")
    parser.add_argument("video", help="Fichier vidéo source")
    parser.add_argument("--preview", action="store_true",
                        help="Affiche les coupes sans exporter")
    parser.add_argument("--no-cache", action="store_true",
                        help="Force une nouvelle transcription (ignore le cache ElevenLabs)")
    parser.add_argument("--speed", type=float, default=1.0,
                        help="Accélération finale (1.0 = off, 1.06 = +6%%)")
    parser.add_argument("--preview-out", default=None,
                        help="Écrit les segments en JSON et sort (pas d'export)")
    parser.add_argument("--from-json", default=None,
                        help="Charge segments JSON + export (skip tout le pipeline)")
    parser.add_argument("--no-notify", action="store_true")
    parser.add_argument("--no-polish", action="store_true",
                        help="Désactive le polish audio post-export")
    parser.add_argument("--lufs", type=float, default=LOUDNESS_TARGET_LUFS,
                        help=f"Cible LUFS (défaut: {LOUDNESS_TARGET_LUFS})")
    parser.add_argument("--no-denoise", action="store_true",
                        help="Skip DeepFilterNet (debruitage)")
    parser.add_argument("--no-deesser", action="store_true",
                        help="Skip de-esser")
    parser.add_argument("--no-hpf", action="store_true",
                        help="Skip highpass filter")
    parser.add_argument("--no-autoeq", action="store_true",
                        help="Skip AutoEQ (courbe voix : warmth/de-mud/presence/air)")
    parser.add_argument("--deplosive", action="store_true",
                        help="Active de-plosive (cascade HPF 4-pôles) — peut feutrer la voix")
    parser.add_argument("--no-bwe", action="store_true",
                        help="Skip Bandwidth Extension / aexciter")
    parser.add_argument("--hum", action="store_true",
                        help="Hum reduction (notch 50Hz + harmoniques) — uniquement si buzz secteur audible")
    parser.add_argument("--apply-lut", type=str, default=None,
                        help="Applique un fichier LUT (.cube) pour le color grading")
    parser.add_argument("--workers", type=int, default=4,
                        help="Nombre de threads pour l'encodage parallèle (défaut: 4)")
    parser.add_argument("--tail", choices=TAIL_MODES, default="tight",
                        help="Agressivité de la coupe en fin de phrase. "
                             "tight = réglage historique (défaut), "
                             "relaxed = garde ~%.2fs de plus après le dernier mot "
                             "(évite les fins de mots rognées). Le début de phrase "
                             "est identique dans les deux cas." % TAIL_RELAX_DEFAULT)
    parser.add_argument("--tail-pad", type=float, default=None,
                        help=f"Secondes de respiration ajoutées en fin de phrase avec "
                             f"--tail relaxed (défaut: {TAIL_RELAX_DEFAULT})")
    args = parser.parse_args()
    smart = True
    tail = tail_profile(args.tail, args.tail_pad)

    video = os.path.abspath(args.video)
    if not os.path.exists(video):
        print(f"[ERREUR] Fichier introuvable : {video}", file=sys.stderr)
        sys.exit(1)

    # Validation du LUT si présent
    if args.apply_lut and not os.path.exists(args.apply_lut):
        print(f"[ERREUR] LUT introuvable : {args.apply_lut}", file=sys.stderr)
        sys.exit(1)

    speed_tag = f"_x{args.speed:.2f}".replace(".", "p") if args.speed != 1.0 else ""
    out_dir = Path(video).parent / (Path(video).stem + "_edited" + speed_tag)
    out_dir.mkdir(exist_ok=True)
    output = str(out_dir / (Path(video).stem + "_edited" + speed_tag + Path(video).suffix))
    duration = get_duration(video)

    # ── Mode from-json : charge segments et exporte direct ──
    if args.from_json:
        with open(args.from_json) as f:
            segments = [tuple(s) for s in json.load(f)["segments"]]
        print(f"Segments chargés : {len(segments)} depuis {args.from_json}")

        with tempfile.TemporaryDirectory() as tmp:
            # FIX SYNC #13 — force CFR ABSOLU (re-encode visuellement transparent si VFR)
            video_cfr = ensure_cfr_source(video, tmp)

            # FIX SYNC #3 — snap sur la grille de frames de la source CFR
            fps_fromjson = get_video_fps(video_cfr)
            segments = snap_segments_to_frames(segments, fps_fromjson)

            print(f"[Export] → {output}")
            # FIX SYNC #11 : export+polish à encodage AAC UNIQUE
            _run_export_and_post(video_cfr, segments, output, args)

        print(f"\n✓ Terminé → {output}\n")
        if not args.no_notify:
            _notify("AutoEdit", f"Export terminé — {Path(output).name}")
        return

    print(f"\n{'─'*52}")
    print(f"  Fichier  : {Path(video).name}")
    print(f"  Durée    : {duration/60:.1f} min")
    print(f"  Sortie   : {Path(output).name}")
    print(f"{'─'*52}\n")

    with tempfile.TemporaryDirectory() as tmp:
        # FIX SYNC #13 — force CFR ABSOLU sur la source (re-encode visuellement transparent si VFR).
        # Toutes les opérations downstream (extract_audio, probe, export) tournent sur le CFR.
        # On garde `video_src` pour la persistence cache (basé sur le nom de fichier original).
        video_src = video
        print("[0/4] Vérification CFR source...")
        video = ensure_cfr_source(video, tmp)

        wav = os.path.join(tmp, "audio.wav")

        print("[1/4] Extraction audio...")
        extract_audio(video, wav)

        # FIX 4 : cache élargi v2 = {version, words, vad, duration} (legacy v1 = liste de words)
        # Cache adossé au chemin SOURCE (pas au CFR temporaire) → persiste entre runs.
        cache_path = Path(video_src).parent / (Path(video_src).stem + ".transcache.json")
        cache_data = None
        if cache_path.exists() and not args.no_cache:
            try:
                with open(cache_path) as cf:
                    cache_data = json.load(cf)
                # Backward-compat : v1 = liste de words bruts
                if isinstance(cache_data, list):
                    cache_data = {"version": 1, "words": cache_data}
            except Exception:
                cache_data = None

        # FIX 1 : VAD + Scribe en parallèle (indépendants, gain ~30-60s sur vidéo longue)
        print("\n[2-3/4] Détection silences (Silero-VAD) + Transcription (parallèle)...")
        vad = None
        words = None
        cache_v2_complet = (
            cache_data is not None
            and cache_data.get("version", 1) >= 2
            and "vad" in cache_data
            and "words" in cache_data
        )

        if cache_v2_complet:
            print(f"  Cache v2 trouvé → VAD + transcription chargés")
            vad = [tuple(v) for v in cache_data["vad"]]
            words = cache_data["words"]
        else:
            with ThreadPoolExecutor(max_workers=2) as pool:
                vad_future = pool.submit(get_vad_segments, wav)
                if cache_data is not None and "words" in cache_data:
                    print(f"  Cache (mots) trouvé → skip Scribe")
                    words_future = None
                    words = cache_data["words"]
                else:
                    words_future = pool.submit(transcribe, wav)
                vad = vad_future.result()
                if words_future is not None:
                    words = words_future.result()

        speech = sum(e - s for s, e in vad)
        print(f"  Parole détectée : {speech/60:.1f} min sur {duration/60:.1f} min")
        print(f"  Segments VAD    : {len(vad)}")
        contractions = sum(1 for w in words if "'" in w["raw"])
        print(f"  Mots transcrits  : {len(words)}  |  Contractions : {contractions}")

        # Sauvegarde cache élargi v2 si on n'a pas déjà un cache complet
        if not cache_v2_complet:
            try:
                with open(cache_path, "w") as cf:
                    json.dump({
                        "version": 2,
                        "words":   words,
                        "vad":     [[s, e] for s, e in vad],
                        "duration": duration,
                    }, cf, ensure_ascii=False)
                print(f"  Cache mis à jour → {cache_path.name}")
            except Exception as e:
                print(f"  [WARN] cache write failed: {e}")

        # FIX SYNC #1 — recalibre timestamps si audio_start ≠ video_start côté source
        # (iPhone MOV, mirrorless avec audio retardé : décalage constant ~30-80ms)
        av_offset = get_av_offset(video)
        words, vad = apply_time_offset(words, vad, av_offset)

        print("\n[4/4] Construction des coupes...")
        if tail["mode"] == "relaxed":
            print(f"  Fin de phrase : relaxed (+{tail['relax']*1000:.0f}ms après le dernier mot)")
        segments, bad = build_segments(vad, words, duration, smart=smart, tail=tail)

        # Snap sur silences RÉELS (amplitude ffmpeg) — bornes parole→silence
        # précises au ms près, indépendantes du flou des word.start/word.end
        # ElevenLabs (qui traînent souvent 50-150 ms après la fin acoustique).
        # Les silences sont mesurés en wav-time → shift en video-time pour
        # matcher les segments (qui sont déjà en video-time après apply_time_offset).
        silences_fine = detect_silences(wav)
        if abs(av_offset) > 1e-4:
            silences_fine = [(s + av_offset, e + av_offset) for s, e in silences_fine]
        segments = snap_segments_to_silence(segments, silences_fine,
                                            edge_pad_trail=tail["snap_pad_trail"])

        # Mode "relaxed" : la fin élargie ne doit pas réintroduire un passage coupé
        # ni empiéter sur le segment suivant.
        if tail["mode"] == "relaxed":
            segments = apply_tail_bounds(segments, bad)

        # FIX SYNC #3 — snap les bornes sur la grille de frames source pour éliminer
        # le jitter sub-frame aux cuts. Vidéo et audio partagent alors la même grille temporelle.
        src_fps_main = get_video_fps(video)
        segments = snap_segments_to_frames(segments, src_fps_main)

        by_type = {}
        for b in bad:
            by_type[b[2]] = by_type.get(b[2], 0) + 1

        kept    = sum(e - s for s, e in segments)
        removed = duration - kept

        print(f"\n{'─'*52}")
        print(f"  Fillers (euh, hm…)     : {by_type.get('filler', 0)}")
        print(f"  Fillers contextuels     : {by_type.get('filler_ctx', 0)}  (ok, voilà, bon)")
        print(f"  Bafouillages (mots)     : {by_type.get('stutter', 0)}")
        print(f"  Répétitions (phrases)   : {by_type.get('repeat', 0)}")
        print(f"  Mots abandonnés (--)    : {by_type.get('abandoned', 0)}")
        print(f"  Restarts (heuristique)  : {by_type.get('restart', 0)}")
        print(f"  Pauses intra-segment    : {by_type.get('gap', 0)}")
        print(f"  Toux / bruits           : {by_type.get('cough', 0)}")
        print(f"  Bruit début segment     : {by_type.get('leading_noise', 0)}")
        if smart:
            print(f"  Contenu faible valeur   : {by_type.get('content', 0)}")
        print(f"  ───")
        print(f"  Durée originale         : {duration/60:.1f} min")
        print(f"  Durée finale            : {kept/60:.1f} min  ({100*kept/duration:.0f}%)")
        print(f"  Temps supprimé          : {removed/60:.1f} min  ({100*removed/duration:.0f}%)")
        print(f"{'─'*52}\n")

        if args.preview:
            print("Détail des coupes :")
            for bs, be, kind, label in sorted(bad, key=lambda x: x[0])[:40]:
                print(f"  [{bs:7.2f}s → {be:7.2f}s]  {kind:12s}  {label[:45]}")
            if len(bad) > 40:
                print(f"  ... et {len(bad)-40} autres")
            print("\n[Preview] Pas d'export. Relance sans --preview pour générer la vidéo.")
            return

        # Dump JSON des segments pour aperçu UI
        if args.preview_out:
            payload = {
                "video":    video,
                "duration": duration,
                "segments": [[s, e] for s, e in segments],
                "kept":     sum(e - s for s, e in segments),
                "bad":      [[b[0], b[1], b[2], b[3]] for b in bad],
            }
            with open(args.preview_out, "w") as f:
                json.dump(payload, f, ensure_ascii=False)
            print(f"\n✓ Aperçu écrit → {args.preview_out}")
            return

        print("[Export]")
        # FIX SYNC #11 : export+polish à encodage AAC UNIQUE (PCM intermédiaire si polish actif)
        _run_export_and_post(video, segments, output, args)

    print(f"\n✓ Terminé → {output}\n")
    if not args.no_notify:
        _notify("AutoEdit", f"Export terminé — {Path(output).name}")

if __name__ == "__main__":
    main()
