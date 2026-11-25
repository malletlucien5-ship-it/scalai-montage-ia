#!/usr/bin/python3
"""
multicam.py — Montage automatique multicam : webcam (1..N parties) + capture d'écran.

Pipeline :
  1. Les parties caméra sont lues comme UN flux virtuel (concat demuxer, zéro copie disque).
  2. Synchronisation caméra ↔ écran par cross-corrélation audio (GCC-PHAT, multi-points,
     fit linéaire → dérive d'horloge absorbée par mapping temporel par segment).
  3. Coupes silences (VAD tight) + fillers (euh/hm) sur la piste audio caméra.
     Pas de coupes IA restarts/bafouillages : passage manuel prévu sur la sortie.
  4. Décision de cadrage par segment via transcription + Claude (OpenRouter) :
     "face" (facecam plein cadre) ou "split" (écran croppé à gauche + facecam à droite).
  5. Rendu par segment (clone du moteur export d'auto_edit.py) + polish audio existant.

Usage :
  python3 multicam.py CAM1.MP4 [CAM2.MP4 ...] --screen ECRAN.mp4 [options]

Étapes de validation :
  --sync-only            mesure la sync, imprime, exit
  --sync-check           exporte 10s hstack + audios mixés (écho audible = désync)
  --calibrate [T]        extrait une frame de chaque source pour mesurer les crops
  --layout-only          détection + décision de cadrage, imprime la table, exit
  --preview-out J.json   dump JSON (segments + layouts + sync), pas de rendu
  --from-json J.json     rendu direct depuis un JSON (éditable à la main)
"""
import argparse
import array
import bisect
import json
import os
import subprocess
import sys
import tempfile
import wave
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from auto_edit import (
    AUDIO_SR, EDGE_FADE_S, HAS_VIDEOTOOLBOX, LOUDNESS_TARGET_LUFS,
    FILLERS, CONTEXTUAL_FILLERS, DANGLING_WORDS,
    CONTEXTUAL_MIN_GAP, CUT_PRE_PADDING, CUT_POST_PADDING,
    LEADING_PADDING, TRAILING_PADDING,
    get_duration, get_av_offset, warn_av_sync,
    get_video_fps, get_video_fps_rational, is_source_vfr, ensure_cfr_source,
    detect_silences, snap_segments_to_silence, snap_segments_to_frames,
    get_vad_segments, transcribe_elevenlabs,
    normalize, merge_contractions,
    _plan_segments,
    polish_audio,
)
from cut_silences import get_vad_tight, notify

# ─── Presets ──────────────────────────────────────────────────────────────────

RES_PRESETS = {
    # hauteur → (largeur, hauteur, bitrate cible h264 en b/s, adapté 50 fps)
    1080: (1920, 1080, 20_000_000),
    1440: (2560, 1440, 32_000_000),
    2160: (3840, 2160, 70_000_000),
}
SEEK_PRE = 2.0          # même pré-seek que _encode_one_segment (GOP typique)
XCORR_SR = 16000        # taux d'échantillonnage pour la cross-corrélation
XCORR_WIN_S = 45.0      # durée d'une fenêtre de mesure
XCORR_MIN_CONF = 6.0    # confidence min (peak / median) pour garder un point
SYNC_LINEAR_TOL = 0.015 # résidu max (s) pour accepter le fit linéaire global


def _load_env_fallback():
    """Charge ELEVENLABS_API_KEY / OPENROUTER_API_KEY depuis les stores connus si absents."""
    wanted = [k for k in ("ELEVENLABS_API_KEY", "OPENROUTER_API_KEY")
              if not os.environ.get(k)]
    if not wanted:
        return
    home = Path.home()
    candidates = [
        Path(__file__).resolve().parents[2] / ".env",  # .env du dépôt scalai-montage-ia
        home / ".config/scalai/credentials.env",
        home / "CODE/clipper/.env",
        home / "CODE/.env",
    ]
    for envfile in candidates:
        if not envfile.is_file():
            continue
        try:
            for line in envfile.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip().removeprefix("export ").strip()
                if key in wanted and val.strip():
                    os.environ[key] = val.strip().strip("'\"")
        except OSError:
            pass


# ─── Sources (fichier unique ou parties concaténées à la volée) ───────────────

class SourceInput:
    """
    Un input ffmpeg : fichier unique, ou N parties caméra exposées comme un seul
    flux via le concat demuxer (aucune copie disque — critique quand les rushes
    font 27 Go et qu'il reste moins que ça de libre).
    """

    def __init__(self, paths, workdir, label):
        self.paths = [os.path.abspath(p) for p in paths]
        self.label = label
        self.is_concat = len(self.paths) > 1
        self.part_durations = [get_duration(p) for p in self.paths]
        self.duration = sum(self.part_durations)
        self.list_file = None
        if self.is_concat:
            self._check_parts_match()
            self.list_file = os.path.join(workdir, f"{label}_concat.txt")
            with open(self.list_file, "w") as f:
                for p in self.paths:
                    escaped = p.replace("'", "'\\''")
                    f.write(f"file '{escaped}'\n")

    def _check_parts_match(self):
        keys = ("codec_name", "width", "height", "r_frame_rate", "pix_fmt")
        ref = None
        for p in self.paths:
            r = subprocess.run(
                ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
                 "-print_format", "json", "-show_streams", p],
                capture_output=True, text=True)
            s = json.loads(r.stdout)["streams"][0]
            sig = tuple(s.get(k) for k in keys)
            if ref is None:
                ref = sig
            elif sig != ref:
                sys.exit(f"[ERREUR] Parties caméra incompatibles pour concat :\n"
                         f"  {self.paths[0]} → {ref}\n  {p} → {sig}")

    @property
    def probe_path(self):
        """Chemin pour les probes (fps, bitrate, av_offset) : la 1re partie."""
        return self.paths[0]

    @property
    def part_starts(self):
        starts, acc = [], 0.0
        for d in self.part_durations:
            starts.append(acc)
            acc += d
        return starts

    @property
    def boundaries(self):
        """Timestamps des raccords entre parties (timeline concaténée)."""
        return self.part_starts[1:]

    def locate(self, t):
        """timeline concaténée → (index de partie, temps local dans la partie)."""
        starts = self.part_starts
        idx = bisect.bisect_right(starts, t) - 1
        idx = min(max(idx, 0), len(self.paths) - 1)
        return idx, t - starts[idx]

    def input_args(self, hwaccel=True):
        """
        Input SANS seek (lecture séquentielle : extraction wav). Le concat
        demuxer ne sait PAS seeker (-ss = décodage depuis le début) — pour tout
        accès positionné, utiliser segment_input()/locate() qui ciblent
        directement la bonne partie.
        """
        args = []
        if hwaccel and HAS_VIDEOTOOLBOX:
            args += ["-hwaccel", "videotoolbox"]
        if self.is_concat:
            args += ["-f", "concat", "-safe", "0", "-i", self.list_file]
        else:
            args += ["-i", self.paths[0]]
        return args

    def segment_input(self, start, hwaccel=True):
        """
        Args d'input pré-seekés SEEK_PRE avant `start` dans la bonne partie.
        Retourne (args, position locale de `start` dans le flux ouvert).
        Le segment doit tenir entièrement dans une partie (garanti par
        split_at_boundaries en amont).
        """
        idx, local = self.locate(start)
        seek = max(0.0, local - SEEK_PRE)
        args = []
        if hwaccel and HAS_VIDEOTOOLBOX:
            args += ["-hwaccel", "videotoolbox"]
        if seek > 0:
            args += ["-ss", f"{seek:.6f}"]
        args += ["-i", self.paths[idx]]
        return args, local - seek


def _sources_signature(paths):
    sig = []
    for p in paths:
        st = os.stat(p)
        sig.append([os.path.abspath(p), st.st_size, int(st.st_mtime)])
    return sig


def _cached_artifact(workdir, name, source_paths, builder):
    """
    Artefact persistant dans le workdir, invalidé si les sources changent
    (taille/mtime). builder(dest_path) doit créer le fichier.
    """
    dest = os.path.join(workdir, name)
    manifest = dest + ".manifest.json"
    sig = _sources_signature(source_paths)
    if os.path.exists(dest) and os.path.exists(manifest):
        try:
            if json.load(open(manifest)) == sig:
                return dest, True
        except Exception:
            pass
    builder(dest)
    with open(manifest, "w") as f:
        json.dump(sig, f)
    return dest, False


def extract_wav_48k(src: SourceInput, workdir):
    """WAV 48 kHz mono complet de la source (VAD / Scribe / silencedetect / xcorr)."""
    def build(dest):
        print(f"  Extraction audio {src.label} ({src.duration/60:.1f} min)...")
        r = subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
            + src.input_args(hwaccel=False)
            + ["-vn", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", dest],
            capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"[ERREUR] extraction audio {src.label} :\n{r.stderr[-400:]}")
    dest, cached = _cached_artifact(workdir, f"{src.label}_48k.wav", src.paths, build)
    if cached:
        print(f"  Audio {src.label} : cache workdir")
    return dest


# ─── Synchronisation par cross-corrélation audio (GCC-PHAT) ──────────────────

def _load_pcm_window(wav_path, t0, dur, sr=XCORR_SR):
    import numpy as np
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t0):.3f}", "-t", f"{dur:.3f}",
         "-i", wav_path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "pipe:1"],
        capture_output=True)
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def _xcorr_offset(ref, tgt, sr=XCORR_SR):
    """
    Position de `ref` à l'intérieur de `tgt` par corrélation GCC-PHAT
    (whitening spectral → robuste aux timbres différents des deux micros).
    Retourne (position_s, confidence). confidence = pic / médiane(|cc|).
    """
    import numpy as np
    if len(ref) < sr or len(tgt) <= len(ref):
        return None, 0.0
    ref = ref - ref.mean()
    tgt = tgt - tgt.mean()
    n = 1
    while n < len(ref) + len(tgt):
        n <<= 1
    R = np.fft.rfft(tgt, n) * np.conj(np.fft.rfft(ref, n))
    R /= np.abs(R) + 1e-12
    cc = np.fft.irfft(R, n)
    valid = cc[: len(tgt) - len(ref) + 1]
    p = int(np.argmax(valid))
    conf = float(valid[p] / (np.median(np.abs(valid)) + 1e-12))
    return p / sr, conf


class SyncMap:
    """
    map(t_cam_video) → t_screen_video, par interpolation linéaire entre ancres
    (t_cam, offset). Encapsule aussi les av_offsets des deux sources — aucun
    offset nu ne circule dans le pipeline.
    """

    def __init__(self, anchors, av_cam=0.0, av_screen=0.0):
        self.anchors = sorted(anchors)          # [(t_cam_wav, offset_wav)]
        self.av_cam = av_cam
        self.av_screen = av_screen

    def _offset_wav(self, t):
        a = self.anchors
        if len(a) == 1 or t <= a[0][0]:
            return a[0][1]
        if t >= a[-1][0]:
            return a[-1][1]
        i = bisect.bisect_right([x[0] for x in a], t) - 1
        (t0, o0), (t1, o1) = a[i], a[i + 1]
        if t1 <= t0:
            return o0
        return o0 + (o1 - o0) * (t - t0) / (t1 - t0)

    def map(self, t_cam_video):
        """cam video-time → screen video-time."""
        t_cam_wav = t_cam_video - self.av_cam
        t_scr_wav = t_cam_wav + self._offset_wav(t_cam_wav)
        return t_scr_wav + self.av_screen

    def describe(self):
        offs = [o for _, o in self.anchors]
        if len(offs) >= 2:
            span = self.anchors[-1][0] - self.anchors[0][0]
            drift = (offs[-1] - offs[0]) / span if span else 0.0
            return (f"offset {offs[0]:+.4f}s → {offs[-1]:+.4f}s "
                    f"(dérive {drift*1e6:+.1f} µs/s, {len(offs)} ancres)")
        return f"offset constant {offs[0]:+.4f}s"


def measure_sync(cam_wav, screen_wav, cam_dur, screen_dur, boundaries,
                 forced_offset=None, av_cam=0.0, av_screen=0.0):
    """
    Mesure l'offset caméra→écran en plusieurs points, fit linéaire, fallback
    piecewise si un raccord caméra introduit un saut. Retourne (SyncMap, rapport).
    """
    if forced_offset is not None:
        return SyncMap([(0.0, forced_offset)], av_cam, av_screen), [
            ("forcé", 0.0, forced_offset, float("inf"))]

    win = min(XCORR_WIN_S, cam_dur / 4)

    # Point initial : recherche large
    t0 = min(60.0, max(5.0, cam_dur * 0.1))
    search = 120.0
    ref = _load_pcm_window(cam_wav, t0, win)
    tgt_start = max(0.0, t0 - search)
    tgt = _load_pcm_window(screen_wav, tgt_start, win + 2 * search)
    pos, conf = _xcorr_offset(ref, tgt)
    if pos is None or conf < XCORR_MIN_CONF:
        sys.exit(f"[ERREUR] Sync introuvable au point initial t={t0:.0f}s "
                 f"(confidence {conf:.1f}) — utilisez --offset pour forcer.")
    off0 = (tgt_start + pos) - t0
    points = [(t0, off0, conf)]

    # Points de raffinement : fenêtre étroite autour de off0
    candidates = [cam_dur * 0.25, cam_dur * 0.5, cam_dur * 0.75,
                  cam_dur - win - 30.0]
    for b in boundaries:
        candidates += [max(5.0, b - win - 10.0), b + 10.0]
    tight = 3.0
    for t in sorted(set(round(c, 1) for c in candidates)):
        if t < 5.0 or t + win > cam_dur - 1.0 or abs(t - t0) < win:
            continue
        if t + off0 < 0 or t + off0 + win > screen_dur - 1.0:
            continue
        ref = _load_pcm_window(cam_wav, t, win)
        tgt_start = max(0.0, t + off0 - tight)
        tgt = _load_pcm_window(screen_wav, tgt_start, win + 2 * tight)
        pos, conf = _xcorr_offset(ref, tgt)
        if pos is not None and conf >= XCORR_MIN_CONF:
            points.append((t, (tgt_start + pos) - t, conf))

    points.sort()
    report = [("mesure", t, o, c) for t, o, c in points]

    # Fit linéaire offset(t) = a + b·t
    if len(points) >= 3:
        ts = [p[0] for p in points]
        os_ = [p[1] for p in points]
        n = len(ts)
        mt, mo = sum(ts) / n, sum(os_) / n
        den = sum((t - mt) ** 2 for t in ts)
        b = sum((t - mt) * (o - mo) for t, o in zip(ts, os_)) / den if den else 0.0
        a = mo - b * mt
        resid = max(abs(o - (a + b * t)) for t, o in zip(ts, os_))
        if resid <= SYNC_LINEAR_TOL:
            anchors = [(0.0, a), (cam_dur, a + b * cam_dur)]
            report.append(("fit", resid, a, b))
            return SyncMap(anchors, av_cam, av_screen), report
        report.append(("piecewise", resid, a, b))
    return SyncMap([(t, o) for t, o, _ in points], av_cam, av_screen), report


# ─── Détection des coupes (silences + fillers) ───────────────────────────────

def _read_wav_mono(wav_path):
    with wave.open(wav_path, "rb") as wf:
        ch, sw, sr, nfr = (wf.getnchannels(), wf.getsampwidth(),
                           wf.getframerate(), wf.getnframes())
        raw = wf.readframes(nfr)
    fmt = {1: "b", 2: "h", 4: "i"}.get(sw, "h")
    samples = array.array(fmt, raw)
    if ch > 1:
        samples = samples[::ch]
    return samples, sr


def trim_segment_ends_batch(wav_path, segments, drop_db=14, lookback=0.9,
                            win_ms=10):
    """
    Équivalent de cut_silences.trim_segment_end mais en UNE lecture du WAV
    (l'original relit tout le fichier à chaque segment — inutilisable sur 44 min).
    """
    try:
        samples, sr = _read_wav_mono(wav_path)
    except Exception:
        return segments
    win = max(1, int(sr * win_ms / 1000))
    out = []
    for seg_s, seg_e in segments:
        s0 = max(0, int((seg_e - lookback) * sr))
        s1 = min(len(samples), int(seg_e * sr))
        region = samples[s0:s1]
        new_end = seg_e
        if len(region) > win:
            rms = []
            for i in range(0, len(region) - win, win):
                chunk = region[i:i + win]
                rms.append((i / sr, (sum(x * x for x in chunk) / len(chunk)) ** 0.5))
            if rms:
                peak = max(r for _, r in rms) or 1
                thresh = peak * (10 ** (-drop_db / 20))
                for t_rel, r in reversed(rms):
                    if r >= thresh:
                        new_end = (seg_e - lookback) + t_rel + win_ms / 1000
                        break
        out.append((seg_s, min(new_end, seg_e)))
    return out


def find_filler_intervals(words):
    """
    Intervalles fillers à couper — copie des détecteurs 1 & 2 de build_segments
    (fillers systématiques + contextuels isolés avec back-off sur mots suspens).
    Rien d'autre : pas de stutters, pas de restarts, pas de Claude.
    """
    bad = []
    for w in words:
        if w["word"] in FILLERS:
            bad.append((w["start"], w["end"], w["raw"]))
    for idx, w in enumerate(words):
        if w["word"] not in CONTEXTUAL_FILLERS:
            continue
        prev_end = words[idx - 1]["end"] if idx > 0 else 0.0
        next_start = words[idx + 1]["start"] if idx < len(words) - 1 else float("inf")
        if (w["start"] - prev_end > CONTEXTUAL_MIN_GAP
                and next_start - w["end"] > CONTEXTUAL_MIN_GAP):
            cut_start = w["start"]
            k = idx - 1
            while k >= 0 and words[k]["word"] in DANGLING_WORDS:
                if w["start"] - words[k]["start"] > 1.5:
                    break
                cut_start = words[k]["start"]
                k -= 1
            bad.append((cut_start, w["end"], w["raw"]))
    bad.sort()
    merged = []
    for bs, be, label in bad:
        if merged and bs < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], be), merged[-1][2])
        else:
            merged.append((bs, be, label))
    return merged


def subtract_intervals(segments, bad, min_seg):
    """Soustrait les intervalles `bad` des segments (avec les marges de coupe standard)."""
    out = []
    for s, e in segments:
        cursor = s
        for bs, be, *_ in bad:
            if be <= cursor or bs >= e:
                continue
            cut_s = bs - CUT_PRE_PADDING
            cut_e = be + CUT_POST_PADDING
            if cut_s - cursor >= min_seg:
                out.append((cursor, cut_s))
            cursor = max(cursor, cut_e)
        if e - cursor >= min_seg:
            out.append((cursor, e))
    return out


def detect_segments_multicam(cam_wav, duration, words_wav, args, fps):
    """
    Segments à conserver (video-time caméra) : VAD → trim énergie →
    lead/trail → merge → soustraction fillers → snap silences → av_offset →
    snap grille de frames.

    VAD `auto` (défaut) = get_vad_segments d'auto_edit : les VALEURS de coupe
    de silence du pipeline principal (seuil 0.40, silence min 220 ms) — coupes
    naturelles. VAD `tight` = variante agressive de cut_silences (silence 25 ms).
    """
    if args.vad == "tight":
        print("  Détection voix/silence (Silero-VAD tight)...")
        vad = get_vad_tight(cam_wav, silence_ms=args.silence_ms,
                            threshold=args.threshold)
    else:
        print("  Détection voix/silence (Silero-VAD auto_edit)...")
        vad = get_vad_segments(cam_wav)
    print(f"  {len(vad)} segments de voix bruts")

    trimmed = trim_segment_ends_batch(cam_wav, vad, drop_db=args.drop_db)

    segments = []
    for s, e in trimmed:
        s2 = max(0.0, s - args.lead)
        e2 = min(duration, e + args.trail)
        if e2 > s2:
            segments.append((s2, e2))
    merged = []
    for s, e in segments:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    segments = [(s, e) for s, e in merged if (e - s) >= args.min_seg]

    fillers = find_filler_intervals(words_wav) if words_wav else []
    if fillers:
        before = sum(e - s for s, e in segments)
        segments = subtract_intervals(segments, fillers, args.min_seg)
        print(f"  Fillers coupés : {len(fillers)} "
              f"(−{before - sum(e - s for s, e in segments):.1f}s)")

    # Reprises : on garde la dernière prise, les précédentes sont retirées.
    if getattr(args, "cut_ranges", None):
        with open(args.cut_ranges) as f:
            cuts = [(float(a), float(b)) for a, b in json.load(f)]
        before = sum(e - s for s, e in segments)
        segments = subtract_intervals(segments, cuts, args.min_seg)
        print(f"  Reprises coupées : {len(cuts)} "
              f"(−{before - sum(e - s for s, e in segments):.1f}s)")

    silences_fine = detect_silences(cam_wav, noise_db=args.silence_db,
                                    min_dur=args.silence_min_dur)
    segments = snap_segments_to_silence(
        segments, silences_fine,
        max_snap=args.silence_snap,
        edge_pad_lead=args.silence_pad_lead,
        edge_pad_trail=args.silence_pad_trail,
    )

    av_offset = args._av_cam
    if abs(av_offset) > 1e-4:
        print(f"  [AV sync] offset caméra {av_offset*1000:+.1f}ms — recalibrage")
        segments = [(s + av_offset, e + av_offset) for s, e in segments]

    segments = snap_segments_to_frames(segments, fps)

    # Ne coupe un blanc que s'il dépasse min_gap : les micro-pauses entre mots
    # (respiration, articulation) sont conservées → débit naturel préservé,
    # seuls les vrais silences de réflexion sont retirés. Sans ça, le VAD tight
    # (silence 25ms) hache les phrases sur des coupes de 20-200ms.
    if args.min_gap > 0 and segments:
        merged, dropped = [segments[0]], 0
        for s, e in segments[1:]:
            if s - merged[-1][1] < args.min_gap:
                merged[-1] = (merged[-1][0], e)
                dropped += 1
            else:
                merged.append((s, e))
        segments = merged
        print(f"  Blancs < {args.min_gap*1000:.0f}ms conservés : "
              f"{dropped} coupe(s) fusionnée(s) → {len(segments)} segments")

    # Retirer aussi les creux acoustiques de 130 ms conservés par le VAD.
    # Cette passe suit la fusion des petites pauses pour conserver ses retraits.
    from tools.quiet_cleanup import clean_segments, read_audio
    quiet_audio, quiet_sr = read_audio(cam_wav)
    wav_segments = [(s-av_offset,e-av_offset) for s,e in segments]
    cleaned = clean_segments(wav_segments, quiet_audio, quiet_sr, words_wav, fps)
    segments = [(s+av_offset,e+av_offset) for s,e in cleaned]
    segments = snap_segments_to_frames(segments, fps)

    kept = sum(e - s for s, e in segments)
    print(f"  Conservé : {kept:.1f}s / {duration:.1f}s "
          f"(coupé {100*(duration-kept)/duration:.1f}%)")
    return segments


def split_long_segments(segments, words_vid, max_len=25.0, min_gap=0.25,
                        min_half=4.0, fps=50.0):
    """
    Scinde les segments > max_len à un `word.end` suivi d'une pause ≥ min_gap,
    le plus proche du milieu. Frontières contiguës (start₂ = end₁, snappées frame)
    → aucun contenu perdu, le concat recolle exactement ; seule utilité :
    autoriser un changement de cadrage au milieu d'une longue tirade.
    """
    period = 1.0 / fps
    ends = [w["end"] for w in words_vid]
    out = []
    for seg in segments:
        s, e = seg
        stack = [(s, e)]
        result = []
        while stack:
            s, e = stack.pop(0)
            if e - s <= max_len:
                result.append((s, e))
                continue
            lo, hi = s + min_half, e - min_half
            mid = (s + e) / 2
            best = None
            i0 = bisect.bisect_left(ends, lo)
            for gap_req in (min_gap, 0.15, 0.0):
                for i in range(i0, len(words_vid) - 1):
                    w_end = words_vid[i]["end"]
                    if w_end > hi:
                        break
                    if words_vid[i + 1]["start"] - w_end >= gap_req:
                        if best is None or abs(w_end - mid) < abs(best - mid):
                            best = w_end + min(0.05, gap_req / 2)
                if best is not None:
                    break
            p = best if best is not None else mid
            p = round(p / period) * period
            p = min(max(p, s + period), e - period)
            stack.insert(0, (p, e))
            result.append((s, p))
        out.extend(sorted(result))
    return sorted(out)


def split_at_boundaries(seg_layouts, boundaries, fps):
    """
    Scinde tout segment qui chevauche un raccord entre parties caméra : au rendu,
    chaque segment est lu par seek direct dans UNE partie (le concat demuxer ne
    sait pas seeker). Frontières contiguës → recollées à l'identique au concat.
    """
    if not boundaries:
        return seg_layouts
    period = 1.0 / fps
    out = []
    for s, e, lay in seg_layouts:
        cur = s
        for b in boundaries:
            b = round(b / period) * period
            if cur < b - period / 2 and e > b + period / 2:
                out.append((cur, b, lay))
                cur = b
        out.append((cur, e, lay))
    return out


# ─── Décision de cadrage ─────────────────────────────────────────────────────

_LAYOUT_STATIC_INSTRUCTIONS = """Tu es un monteur vidéo expert en rétention YouTube pour du contenu talking-head français.

La vidéo a deux cadrages possibles :
- "face"  : le créateur en facecam plein écran. Fort impact, connexion directe.
- "split" : document/écran partagé à gauche + facecam à droite. Pour montrer le contenu.

Tu reçois la liste des segments (déjà montés, silences coupés) avec leur texte.
Assigne un cadrage à CHAQUE segment. Règles :
1. Introduction/accroche et conclusion/call-to-action → "face".
2. Punchlines, affirmations fortes, adresses directes au spectateur, transitions
   d'une partie à l'autre → "face".
3. Explication qui s'appuie sur le document affiché, lecture/parcours du contenu,
   démonstration, énumération visible à l'écran → "split".
4. RÉTENTION : varie les cadrages. Évite plus de ~25 secondes consécutives du même
   cadrage quand le contenu le permet ; un passage "face" de 4-10s au milieu d'une
   longue section "split" sert de respiration et relance l'attention.
5. En cas de doute sur un segment central du contenu → "split" (le spectateur est
   venu voir le document), mais garde le rythme de la règle 4.

Réponds en JSON STRICT : {"layouts": [{"seg": 0, "layout": "face"}, {"seg": 1, "layout": "split"}, ...]}
Couvre TOUS les index de segments listés, sans exception. Aucun texte hors JSON."""


def _segment_texts(segments, words_vid):
    texts = []
    starts = [w["start"] for w in words_vid]
    for s, e in segments:
        i = bisect.bisect_left(starts, s - 0.2)
        toks = []
        while i < len(words_vid) and words_vid[i]["start"] < e + 0.2:
            if words_vid[i]["end"] > s:
                toks.append(words_vid[i]["raw"])
            i += 1
        texts.append(" ".join(toks) if toks else "(sans parole)")
    return texts


def _parse_json_loose(raw):
    """Parse tolérant : fences markdown, préambule texte, suffixe — on extrait l'objet."""
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`").strip()
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        i, j = raw.find("{"), raw.rfind("}")
        if 0 <= i < j:
            return json.loads(raw[i:j + 1])
        raise ValueError(f"réponse non-JSON : {raw[:200]!r}")


def transcribe_whisper(wav, model_size="medium", initial_prompt=None):
    """
    Repli local quand ElevenLabs est indisponible : faster-whisper (CPU int8),
    mots horodatés au même format que transcribe_elevenlabs. Whisper omet une
    partie des "euh" (Scribe est littéral) : les coupes fillers sont donc moins
    complètes. Le prompt initial pousse le modèle à transcrire les hésitations.
    """
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    prompt = initial_prompt or ("Euh, alors, hum, donc euh, je vais vous montrer, "
                                "euh, comment ça marche.")
    segs, info = model.transcribe(
        wav, language="fr", word_timestamps=True, vad_filter=False,
        beam_size=5, condition_on_previous_text=False,
        initial_prompt=prompt)
    words = []
    for seg in segs:
        for w in (seg.words or []):
            txt = w.word.strip()
            if not txt:
                continue
            words.append({"word": normalize(txt), "raw": txt,
                          "start": float(w.start), "end": float(w.end)})
    print(f"  faster-whisper {model_size} : {len(words)} mots")
    return merge_contractions(words)


def decide_layouts_llm(segments, words_vid, api_key,
                       model="anthropic/claude-sonnet-4-6", chunk_size=140):
    """Appel OpenRouter/Claude par chunks de segments. None si échec → fallback heuristique."""
    import requests
    texts = _segment_texts(segments, words_vid)
    total = segments[-1][1] if segments else 0.0
    layouts = [None] * len(segments)

    chunks = [(i, min(i + chunk_size, len(segments)))
              for i in range(0, len(segments), chunk_size)]
    for ci, (lo, hi) in enumerate(chunks):
        lines = []
        for i in range(lo, hi):
            s, e = segments[i]
            lines.append(f"SEG {i} [{s:.1f}s → {e:.1f}s, {e-s:.1f}s] : {texts[i]}")
        dynamic = (
            f"CONTEXTE : vidéo de {total/60:.1f} min, {len(segments)} segments au total. "
            f"Ce lot couvre les segments {lo} à {hi-1} (lot {ci+1}/{len(chunks)}).\n"
            f"Le segment 0 est le début de la vidéo, le segment {len(segments)-1} la fin.\n\n"
            + "\n".join(lines)
        )
        payload = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": _LAYOUT_STATIC_INSTRUCTIONS,
                     "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": dynamic},
                ],
            }],
            "max_tokens": 12000,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        last_err = None
        for attempt in (1, 2):
            try:
                resp = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}",
                             "Content-Type": "application/json"},
                    json=payload, timeout=180)
                if resp.status_code in (400, 422):
                    payload["messages"] = [{
                        "role": "user",
                        "content": _LAYOUT_STATIC_INSTRUCTIONS + "\n\n" + dynamic}]
                    resp = requests.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}",
                                 "Content-Type": "application/json"},
                        json=payload, timeout=180)
                resp.raise_for_status()
                body = resp.json()
                if "error" in body:
                    raise ValueError(f"erreur API : {str(body['error'])[:200]}")
                choice = body["choices"][0]
                raw = (choice["message"].get("content") or "").strip()
                if choice.get("finish_reason") == "length":
                    print(f"  [LLM] lot {ci+1} : réponse tronquée (length)")
                parsed = _parse_json_loose(raw)
                entries = (parsed.get("layouts", parsed)
                           if isinstance(parsed, dict) else parsed)
                for ent in entries or []:
                    try:
                        i = int(ent["seg"])
                        lay = str(ent["layout"]).strip().lower()
                        if lo <= i < hi and lay in ("face", "split"):
                            layouts[i] = lay
                    except (KeyError, ValueError, TypeError):
                        continue
                print(f"  [LLM] lot {ci+1}/{len(chunks)} : "
                      f"{sum(1 for i in range(lo, hi) if layouts[i])} / {hi-lo} "
                      f"segments assignés")
                last_err = None
                break
            except Exception as e:
                last_err = e
        if last_err is not None:
            print(f"  [LLM] lot {ci+1}/{len(chunks)} échoué ({last_err}) — "
                  f"fallback heuristique sur ce lot")

    missing = sum(1 for l in layouts if l is None)
    if missing > len(segments) * 0.5:
        return None
    return ["split" if l is None else l for l in layouts]


def decide_layouts_heuristic(segments, intro_s=25.0, outro_s=25.0,
                             breath_every=20.0):
    """Sans API : face en intro/conclusion, split ailleurs, respiration face ~20s."""
    if not segments:
        return []
    t_start = segments[0][0]
    t_end = segments[-1][1]
    layouts = []
    split_run = 0.0
    for s, e in segments:
        if s - t_start < intro_s or t_end - e < outro_s:
            layouts.append("face")
            split_run = 0.0
        elif split_run >= breath_every and (e - s) <= 12.0:
            layouts.append("face")
            split_run = 0.0
        else:
            layouts.append("split")
            split_run += e - s
    return layouts


def enforce_layout_constraints(layouts, segments, min_shot=4.0, max_split=25.0,
                               edge_face_s=8.0, max_face=None, locked=frozenset()):
    """
    Filet déterministe appliqué MÊME après le LLM (ses index/choix ne sont jamais
    tenus pour fiables) : intro/outro face, fusion des plans trop courts,
    cassure des runs split trop longs.
    """
    n = len(segments)
    if n == 0:
        return layouts
    layouts = list(layouts)

    # 1. Plancher intro/outro en face
    acc = 0.0
    for i in range(n):
        layouts[i] = "face"
        acc += segments[i][1] - segments[i][0]
        if acc >= edge_face_s:
            break
    acc = 0.0
    for i in range(n - 1, -1, -1):
        layouts[i] = "face"
        acc += segments[i][1] - segments[i][0]
        if acc >= edge_face_s:
            break

    def runs():
        out = []
        for i, lay in enumerate(layouts):
            if out and out[-1][0] == lay:
                out[-1][2] = i
            else:
                out.append([lay, i, i])
        return out

    def run_dur(r):
        return sum(segments[i][1] - segments[i][0] for i in range(r[1], r[2] + 1))

    def has_locked(r):
        return any(i in locked for i in range(r[1], r[2] + 1))

    # 2. Fusionne les plans plus courts que min_shot dans le run précédent
    for _ in range(20):
        rs = runs()
        changed = False
        for k, r in enumerate(rs):
            if run_dur(r) < min_shot and len(rs) > 1 and not has_locked(r):
                target = rs[k - 1][0] if k > 0 else rs[k + 1][0]
                for i in range(r[1], r[2] + 1):
                    layouts[i] = target
                changed = True
                break
        if not changed:
            break

    # 3. Casse les runs trop longs : flip du segment médian vers l'autre layout.
    #    split > max_split → face ; face > max_face (si donné) → split.
    #    Les segments du run qui touchent l'intro/outro face restent face.
    limits = [("split", max_split, "face")]
    if max_face:
        limits.append(("face", max_face, "split"))
    for _ in range(200):
        rs = runs()
        changed = False
        for lay, limit, other in limits:
            for r in rs:
                if r[0] != lay or run_dur(r) <= limit:
                    continue
                idxs = list(range(r[1], r[2] + 1))
                if len(idxs) < 3:
                    continue
                mid_t = (segments[r[1]][0] + segments[r[2]][1]) / 2
                free = [i for i in idxs[1:-1] if i not in locked]
                if not free:
                    continue
                good = [i for i in free
                        if 2.0 <= segments[i][1] - segments[i][0] <= 12.0]
                pool = good or free
                best = min(pool, key=lambda i: abs(
                    (segments[i][0] + segments[i][1]) / 2 - mid_t))
                # Le groupe flippé doit durer ≥ min_shot, sinon l'étape 3b le
                # refusionne et le run long revient (segments courts = phrases).
                lo_i, hi_i = best, best
                inner_lo, inner_hi = idxs[1], idxs[-2]
                def grp_dur():
                    return sum(segments[i][1] - segments[i][0]
                               for i in range(lo_i, hi_i + 1))
                side = 0
                can_lo = lambda: lo_i > inner_lo and (lo_i - 1) not in locked
                can_hi = lambda: hi_i < inner_hi and (hi_i + 1) not in locked
                while grp_dur() < min_shot and (can_lo() or can_hi()):
                    if side == 0 and can_hi():
                        hi_i += 1
                    elif can_lo():
                        lo_i -= 1
                    elif can_hi():
                        hi_i += 1
                    side ^= 1
                for i in range(lo_i, hi_i + 1):
                    layouts[i] = other
                changed = True
                break
            if changed:
                break
        if not changed:
            break
    # 3b. Un flip peut créer un run < min_shot : refusionne (une passe)
    for _ in range(20):
        rs = runs()
        changed = False
        for k, r in enumerate(rs):
            if run_dur(r) < min_shot and len(rs) > 1 and not has_locked(r):
                target = rs[k - 1][0] if k > 0 else rs[k + 1][0]
                for i in range(r[1], r[2] + 1):
                    layouts[i] = target
                changed = True
                break
        if not changed:
            break
    return layouts


def solve_layouts_dp(prefs, segments, min_shot=5.0, max_run=14.0,
                     locked=frozenset(), step=0.1, cap=90.0,
                     w_over=40.0, w_under=40.0):
    """
    Cadence par programmation dynamique (remplace la cascade gloutonne
    d'enforce_layout_constraints quand on veut un plafond sur les DEUX layouts).

    Minimise la durée des segments qui contredisent la préférence (LLM ou
    heuristique) sous : chaque run dans [min_shot, max_run]. Les segments
    `locked` sont face et un run face qui en contient échappe au plafond
    (script visible, intro/outro, hors couverture écran). Les bornes sont
    souples (pénalité w_* par seconde de dépassement) : le DP rend toujours
    une solution, jamais d'échec silencieux.
    """
    n = len(segments)
    if n == 0:
        return []
    if not isinstance(locked, dict):
        locked = {i: 0 for i in locked}
    durs = [e - s for s, e in segments]
    LAY = ("face", "split")
    ncap = int(cap / step)
    INF = float("inf")

    def q(d):
        return min(ncap, int(round(d / step)))

    def close_cost(dq, lay, has_lock):
        # dq = durée depuis le dernier segment verrouillé (remise à zéro) :
        # le plafond porte sur la portion libre d'un run, jamais sur le verrou.
        d = dq * step
        c = 0.0
        if d < min_shot and not has_lock:
            c += w_under * (min_shot - d)
        if d > max_run:
            c += w_over * (d - max_run)
        return c

    # state : (lay, dq, has_lock) → (cost, backpointer)
    best = {}
    for lay in (0, 1):
        if 0 in locked and locked[0] != lay:
            continue
        mismatch = durs[0] if LAY[lay] != prefs[0] else 0.0
        lk0 = 0 in locked
        best[(lay, 0 if lk0 else q(durs[0]), lk0)] = (mismatch, None)
    history = [best]
    for i in range(1, n):
        nxt = {}
        for (lay, dq, hl), (cost, _) in best.items():
            for nl in (0, 1):
                if i in locked and locked[i] != nl:
                    continue
                mismatch = durs[i] if LAY[nl] != prefs[i] else 0.0
                lk = i in locked
                if nl == lay:
                    key = (nl, 0 if lk else q(dq * step + durs[i]), hl or lk)
                    c = cost + mismatch
                    if lk:
                        # la portion libre qui précède le verrou est close ici :
                        # son dépassement du plafond doit être payé maintenant
                        c += w_over * max(0.0, dq * step - max_run)
                else:
                    key = (nl, 0 if lk else q(durs[i]), lk)
                    c = cost + mismatch + close_cost(dq, lay, hl)
                if c < nxt.get(key, (INF, None))[0]:
                    nxt[key] = (c, (lay, dq, hl))
        best = nxt
        history.append(best)
    # fin : fermer le dernier run
    end_key, end_cost = None, INF
    for key, (cost, _) in best.items():
        c = cost + close_cost(key[1], key[0], key[2])
        if c < end_cost:
            end_cost, end_key = c, key
    out = [None] * n
    key = end_key
    for i in range(n - 1, -1, -1):
        out[i] = LAY[key[0]]
        key = history[i][key][1]
    return out


def track_face_crops(cam, seg_layouts, side, sw, sh, head_y=0.42, n_samples=3):
    """
    Recadre le carré visage par segment "split" : détection Haar (OpenCV) sur
    n_samples frames réduites du segment, centre moyen, puis moyenne par run de
    segments split consécutifs (pas de saut de cadrage à l'intérieur d'un run).
    Retourne {index: (x, y, side, side)} ; segments sans détection → None (le
    crop global s'applique). head_y = position verticale du visage dans le carré.
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("  [Face track] OpenCV absent → crop fixe")
        return {}
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    scale = 4
    centers = {}
    for i, (s, e, l) in enumerate(seg_layouts):
        if l != "split":
            continue
        pts = []
        for k in range(n_samples):
            t = s + (e - s) * (k + 1) / (n_samples + 1)
            idx, local = cam.locate(t)
            r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{local:.3f}",
                                "-i", cam.paths[idx], "-frames:v", "1",
                                "-vf", f"scale={sw // scale}:{sh // scale}",
                                "-f", "rawvideo", "-pix_fmt", "gray", "pipe:1"],
                               capture_output=True)
            g = np.frombuffer(r.stdout, dtype=np.uint8)
            if g.size != (sw // scale) * (sh // scale):
                continue
            g = g.reshape(sh // scale, sw // scale)
            faces = casc.detectMultiScale(g, 1.1, 4, minSize=(60, 60))
            if len(faces):
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                pts.append(((x + w / 2) * scale, (y + h / 2) * scale))
        if pts:
            centers[i] = (sum(p[0] for p in pts) / len(pts),
                          sum(p[1] for p in pts) / len(pts))
    # moyenne par run de split consécutifs
    crops = {}
    i = 0
    n = len(seg_layouts)
    while i < n:
        if seg_layouts[i][2] != "split":
            i += 1
            continue
        j = i
        while j + 1 < n and seg_layouts[j + 1][2] == "split":
            j += 1
        run = [k for k in range(i, j + 1) if k in centers]
        if run:
            cx = sum(centers[k][0] for k in run) / len(run)
            cy = sum(centers[k][1] for k in run) / len(run)
            x = int(min(max(0, cx - side / 2), sw - side))
            y = int(min(max(0, cy - side * head_y), sh - side))
            for k in range(i, j + 1):
                crops[k] = (x, y, side, side)
        i = j + 1
    print(f"  [Face track] {len(centers)} segments détectés, "
          f"{len(crops)} cadrés (côté {side}px)")
    return crops


def apply_face_ranges(layouts, segments, syncmap, ranges, margin=0.5):
    """
    Force "face" sur tout segment dont la fenêtre ÉCRAN chevauche une plage
    interdite [start, end] (temps écran, ex : script visible), avec `margin` s
    de sécurité de chaque côté. Retourne (layouts, nb forcés).
    """
    if not ranges:
        return layouts, []
    layouts = list(layouts)
    forced = []
    for i, (s, e) in enumerate(segments):
        ss, se = syncmap.map(s), syncmap.map(e)
        for a, b in ranges:
            if ss < b + margin and se > a - margin:
                layouts[i] = "face"
                forced.append(i)
                break
    return layouts, forced


# ─── Polish : DeepFilterNet par blocs (anti-OOM sur vidéos longues) ──────────

def _chunked_deepfilternet_denoise(audio_in_wav, chunk_s=120.0, ctx_s=1.0):
    """
    Remplaçant de auto_edit._deepfilternet_denoise qui traite l'audio d'un seul
    tenseur → pic mémoire de plusieurs Go sur 30+ min → OOM sur un Mac 16 Go.

    Ici : DeepFilterNet3 appliqué par blocs de chunk_s, chacun élargi de ctx_s
    de chaque côté (contexte jeté après) pour des frontières sans couture — le
    champ réceptif du réseau est bien inférieur à 1 s. Pic mémoire borné à ~1 bloc.
    Sortie identique (wav 48 kHz à côté de l'entrée) ; None si indisponible.
    """
    try:
        import sys as _sys, types as _types
        if "torchaudio.backend.common" not in _sys.modules:
            _tb = _types.ModuleType("torchaudio.backend")
            _tbc = _types.ModuleType("torchaudio.backend.common")
            class _Stub:
                pass
            _tbc.AudioMetaData = _Stub
            _sys.modules["torchaudio.backend"] = _tb
            _sys.modules["torchaudio.backend.common"] = _tbc
            import torchaudio as _ta
            _ta.backend = _tb
        from df.enhance import enhance, init_df
        import soundfile as sf
        import torch
        import numpy as np

        df_model, df_state, _ = init_df()
        sr = df_state.sr()
        audio, src_sr = sf.read(audio_in_wav)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        audio = audio.astype(np.float32)
        if src_sr != sr:
            import librosa
            audio = librosa.resample(audio, orig_sr=src_sr, target_sr=sr)
        n = len(audio)
        chunk = int(chunk_s * sr)
        ctx = int(ctx_s * sr)
        n_chunks = (n + chunk - 1) // chunk
        print(f"  DeepFilterNet3 (ML denoise, {n_chunks} blocs de {chunk_s:.0f}s)...")
        out = np.zeros(n, dtype=np.float32)
        pos = 0
        while pos < n:
            a = max(0, pos - ctx)
            b = min(n, pos + chunk + ctx)
            seg = torch.from_numpy(audio[a:b].copy()).unsqueeze(0)
            enh = enhance(df_model, df_state, seg).squeeze().cpu().numpy()[: b - a]
            s = pos - a
            end = min(pos + chunk, n)
            out[pos:end] = enh[s: s + (end - pos)]
            pos += chunk
            del seg, enh
        out_path = audio_in_wav.replace(".wav", "_dfnet.wav")
        sf.write(out_path, out[:n], sr)
        return out_path
    except Exception as e:
        print(f"  [AVERTISSEMENT] DeepFilterNet (chunked) indisponible ({e}) — skip")
        return None


def _install_chunked_denoise():
    """
    Monkey-patch auto_edit avant polish :
    - denoise DeepFilterNet par blocs (borne la mémoire — anti-OOM).
    - get_stream_duration sans -count_frames : le .mkv Matroska intermédiaire
      n'expose pas la durée au niveau flux vidéo → l'original décode les 96k
      frames (>8 min CPU gaspillées). On lit la durée conteneur à la place.
    """
    import auto_edit
    auto_edit._deepfilternet_denoise = _chunked_deepfilternet_denoise

    _orig_probe = auto_edit._probe_frame_count
    auto_edit._probe_frame_count = lambda p: None  # neutralise le count_frames lent
    def _fast_stream_duration(path, stream_selector="v:0"):
        n = _fast_frame_count(path)
        if n is not None:
            fps_n, fps_d = auto_edit.get_video_fps_rational(path)
            if fps_n:
                return n * fps_d / fps_n
        return auto_edit.get_duration(path)
    auto_edit.get_stream_duration = _fast_stream_duration


# ─── Rendu composite ─────────────────────────────────────────────────────────

def _build_v_enc_multicam(target_vbr):
    """Params encodeur communs à TOUS les segments (invariant concat -c:v copy)."""
    if HAS_VIDEOTOOLBOX:
        return ["-c:v", "h264_videotoolbox", "-b:v", str(int(target_vbr)),
                "-bf", "0", "-pix_fmt", "yuv420p", "-prio_speed", "1"], "videotoolbox"
    return ["-c:v", "libx264", "-crf", "17", "-preset", "medium",
            "-pix_fmt", "yuv420p", "-bf", "0"], "libx264 CRF17"


def _fast_frame_count(path):
    """
    Compte de frames via l'entête conteneur (nb_frames) ou durée×fps — instantané.
    Contrairement à _probe_frame_count (-count_frames), ne décode RIEN : sur un
    1440p de 32 min, count_frames décode 96k frames (>10 min CPU) pour un simple
    audit. On lit les métadonnées à la place ; None si indéterminable.
    """
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=nb_frames,duration,avg_frame_rate",
         "-of", "json", path],
        capture_output=True, text=True)
    try:
        s = json.loads(r.stdout)["streams"][0]
        if str(s.get("nb_frames", "")).isdigit():
            return int(s["nb_frames"])
        dur = float(s["duration"])
        num, den = s["avg_frame_rate"].split("/")
        return int(round(dur * float(num) / float(den)))
    except Exception:
        return None


def _even(x):
    return int(round(x / 2)) * 2


def _crop_str(crop):
    x, y, w, h = crop
    return f"crop={_even(w)}:{_even(h)}:{int(x)}:{int(y)}"


def _encode_one_mc_segment(task):
    """
    Encode UN segment composite en MOV intermédiaire (H.264 + PCM).
    Clone de _encode_one_segment (auto_edit.py) étendu à 2 inputs + layouts.
    La chaîne audio sample-locked est copiée à l'identique (invariant sync).
    """
    (i, cam, screen, start, end, layout, scr_start, n_frames, n_samples,
     fps_n, fps_d, v_enc, canvas, w_left, w_right, face_crop, screen_crop,
     screen_fit, pad_color, out_clip, input_frames, layout_mode, pip_geo) = task

    fps_str = f"{fps_n}/{fps_d}"
    input_dur = max(0.0, end - start)
    vid_dur = n_frames * fps_d / fps_n
    aud_dur = n_samples / AUDIO_SR
    W, H = canvas

    # FIX SYNC #16 (clone auto_edit) : vitesse effective = frames in / frames out
    eff = input_frames / n_frames if (input_frames and n_frames) else 1.0
    if abs(eff - 1.0) < 1e-9:
        eff = 1.0
    v_speed = f",setpts=PTS/{eff:.9f}" if eff != 1.0 else ""
    a_speed = f",atempo={eff:.9f}" if eff != 1.0 else ""

    cam_args, ls = cam.segment_input(start)
    le = ls + input_dur

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    cmd += cam_args

    if layout == "split" and layout_mode == "pip":
        # Écran plein cadre (fit sur fond) + visage carré incrusté dans un coin
        scr_args, sls = screen.segment_input(scr_start)
        sle = sls + input_dur
        cmd += scr_args
        ps, margin, corner, radius = pip_geo
        if radius > 0:
            # coins arrondis : alpha = 1 si la distance au rectangle intérieur
            # (rétréci de R) est ≤ R, sinon 0 → rectangle à coins de rayon R
            r_ = int(radius)
            rounded = (
                f",format=yuva444p,geq=lum='lum(X,Y)':cb='cb(X,Y)':cr='cr(X,Y)':"
                f"a='255*lte(hypot(X-clip(X,{r_},W-1-{r_}),Y-clip(Y,{r_},H-1-{r_})),{r_})'"
            )
        else:
            rounded = ""
        if screen_fit == "fit":
            scr_scale = (
                f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,"
                f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color={pad_color}"
            )
        else:
            scr_scale = (
                f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={W}:{H}"
            )
        ox = margin if corner.endswith("left") else W - ps - margin
        oy = margin if corner.startswith("top") else H - ps - margin
        fc = (
            f"[1:v:0]trim=start={sls:.6f}:end={sle:.6f},setpts=PTS-STARTPTS{v_speed},"
            f"fps=fps={fps_str}:round=near,"
            f"{_crop_str(screen_crop)},{scr_scale}[bg];"
            f"[0:v:0]trim=start={ls:.6f}:end={le:.6f},setpts=PTS-STARTPTS{v_speed},"
            f"fps=fps={fps_str}:round=near,"
            f"{_crop_str(face_crop)},scale={ps}:{ps}:flags=lanczos{rounded}[pip];"
            f"[bg][pip]overlay=x={ox}:y={oy}:eof_action=pass,tpad=stop_mode=clone:stop_duration=2,format=yuv420p[v]"
        )
    elif layout == "split":
        scr_args, sls = screen.segment_input(scr_start)
        sle = sls + input_dur
        cmd += scr_args
        if screen_fit == "fit":
            # dézoom : le crop tient entièrement, complété à la couleur de fond
            scr_scale = (
                f"scale={w_left}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,"
                f"pad={w_left}:{H}:(ow-iw)/2:(oh-ih)/2:color={pad_color}"
            )
        else:
            scr_scale = (
                f"scale={w_left}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
                f"crop={w_left}:{H}"
            )
        fc = (
            f"[0:v:0]trim=start={ls:.6f}:end={le:.6f},setpts=PTS-STARTPTS{v_speed},"
            f"fps=fps={fps_str}:round=near,"
            f"{_crop_str(face_crop)},scale={w_right}:{H}:flags=lanczos[right];"
            f"[1:v:0]trim=start={sls:.6f}:end={sle:.6f},setpts=PTS-STARTPTS{v_speed},"
            f"fps=fps={fps_str}:round=near,"
            f"{_crop_str(screen_crop)},{scr_scale}[left];"
            f"[left][right]hstack=inputs=2,tpad=stop_mode=clone:stop_duration=2,format=yuv420p[v]"
        )
    else:
        fc = (
            f"[0:v:0]trim=start={ls:.6f}:end={le:.6f},setpts=PTS-STARTPTS{v_speed},"
            f"fps=fps={fps_str}:round=near,"
            f"scale={W}:{H}:flags=lanczos,tpad=stop_mode=clone:stop_duration=2,format=yuv420p[v]"
        )

    fade_out_st = max(0.0, aud_dur - EDGE_FADE_S)
    fc += (
        f";[0:a:0]atrim=start={ls:.6f}:end={le:.6f},asetpts=PTS-STARTPTS,"
        f"aresample={AUDIO_SR}:async=1:first_pts=0{a_speed},"
        f"apad=whole_len={n_samples},atrim=end_sample={n_samples},"
        f"afade=t=in:st=0:d={EDGE_FADE_S:.6f},"
        f"afade=t=out:st={fade_out_st:.6f}:d={EDGE_FADE_S:.6f}[a]"
    )

    cmd += [
        "-filter_complex", fc,
        "-map", "[v]", "-map", "[a]",
        "-fps_mode", "cfr",
        *v_enc,
        "-c:a", "pcm_s16le",
        "-frames:v", str(n_frames),
        "-t", f"{max(vid_dur, aud_dur):.9f}",
        out_clip,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return i, None, input_dur, r.stderr[-400:]
    return i, out_clip, input_dur, None


def _clip_key(start, end, layout, scr_start, n_frames, n_samples, canvas,
              w_left, w_right, face_crop, screen_crop, screen_fit, pad_color,
              fps_n, fps_d, v_enc, input_frames=None, layout_mode="split",
              pip_geo=None):
    """
    Empreinte déterministe d'un clip segment : tout ce qui influe sur ses pixels
    ou ses samples. Deux rendus avec la même empreinte donnent un clip
    interchangeable → cache réutilisable entre itérations (ex : changer le layout
    d'un segment ne touche PAS l'empreinte des autres → un seul ré-encodage).
    """
    import hashlib
    mat = repr((
        round(start, 4), round(end, 4), layout,
        round(scr_start, 4) if layout == "split" else None,
        n_frames, n_samples, canvas, w_left, w_right,
        face_crop if layout == "split" else None,
        screen_crop if layout == "split" else None,
        screen_fit if layout == "split" else None,
        pad_color if (layout == "split" and screen_fit == "fit") else None,
        fps_n, fps_d, tuple(v_enc),
        input_frames, layout_mode if layout == "split" else None,
        tuple(pip_geo) if (layout == "split" and pip_geo) else None,
        "tpad-v2",
    ))
    return hashlib.md5(mat.encode()).hexdigest()[:16]


def export_multicam(cam, screen, seg_layouts, syncmap, output, canvas,
                    split_ratio, face_crop, screen_crop, target_vbr,
                    workers=3, audio_codec="aac", tmp_root=None,
                    screen_fit="fill", pad_color="0x181818", clip_cache=True,
                    speed=1.0, layout_mode="split", pip_size=0.22,
                    pip_margin=40, pip_corner="bottom-right", pip_radius=0.0,
                    face_crops=None):
    """
    Rendu par segment parallèle + concat demuxer -c:v copy, structure identique
    à export() d'auto_edit.py (mêmes invariants : plans entiers cumulés, params
    encodeur uniques, apad/atrim au sample près, AAC encodé une seule fois).

    clip_cache : conserve les clips MOV dans <tmp_root>/clips, indexés par
    empreinte de rendu. Une itération qui ne change que quelques cadrages ne
    ré-encode que ces segments (les autres sont réutilisés) → re-rendu en ~2 min
    au lieu de ~25. Les clips orphelins sont purgés après le concat.
    """
    n = len(seg_layouts)
    if n == 0:
        sys.exit("[ERREUR] Aucun segment à exporter.")

    fps_n, fps_d = get_video_fps_rational(cam.probe_path)
    segments = [(s, e) for s, e, _ in seg_layouts]
    input_frame_plan, frame_plan, samples_plan, total_frames, total_samples = \
        _plan_segments(segments, fps_n, fps_d, speed)

    W, H = canvas
    w_left = _even(W * split_ratio)
    w_right = W - w_left
    v_enc, enc_name = _build_v_enc_multicam(target_vbr)
    pip_geo = (_even(H * pip_size), int(pip_margin), pip_corner,
               int(round(_even(H * pip_size) * pip_radius)))

    if face_crop is None and layout_mode == "pip":
        # carré centré, pleine hauteur source
        r = subprocess.run(["ffprobe", "-v", "quiet", "-select_streams", "v:0",
                            "-print_format", "json", "-show_streams",
                            cam.probe_path], capture_output=True, text=True)
        s0 = json.loads(r.stdout)["streams"][0]
        sw, sh = int(s0["width"]), int(s0["height"])
        side = _even(min(sw, sh))
        face_crop = ((sw - side) // 2, (sh - side) // 2, side, side)
    if face_crop is None:
        # crop centré au ratio de la demi-droite, pleine hauteur source
        r = subprocess.run(["ffprobe", "-v", "quiet", "-select_streams", "v:0",
                            "-print_format", "json", "-show_streams",
                            cam.probe_path], capture_output=True, text=True)
        s0 = json.loads(r.stdout)["streams"][0]
        sw, sh = int(s0["width"]), int(s0["height"])
        cw = _even(min(sw, sh * w_right / H))
        face_crop = ((sw - cw) // 2, 0, cw, sh)
    if screen_crop is None:
        r = subprocess.run(["ffprobe", "-v", "quiet", "-select_streams", "v:0",
                            "-print_format", "json", "-show_streams",
                            screen.probe_path], capture_output=True, text=True)
        s0 = json.loads(r.stdout)["streams"][0]
        screen_crop = (0, 0, int(s0["width"]), int(s0["height"]))

    clips_dir = os.path.join(tmp_root, "clips") if (clip_cache and tmp_root) else None
    if clips_dir:
        os.makedirs(clips_dir, exist_ok=True)

    # Construit la liste des clips + leur empreinte ; détecte les hits de cache.
    clip_paths, tasks = [], []
    cached = 0
    with tempfile.TemporaryDirectory(dir=tmp_root) as tmp:
        for i, (s, e, layout) in enumerate(seg_layouts):
            scr_start = syncmap.map(s)
            fc_i = tuple((face_crops or {}).get(i, face_crop))
            if clips_dir:
                key = _clip_key(s, e, layout, scr_start, frame_plan[i],
                                samples_plan[i], canvas, w_left, w_right,
                                fc_i, screen_crop, screen_fit, pad_color,
                                fps_n, fps_d, v_enc, input_frame_plan[i],
                                layout_mode, pip_geo)
                clip_path = os.path.join(clips_dir, f"{key}.mov")
                valid = (os.path.exists(clip_path)
                         and _fast_frame_count(clip_path) == frame_plan[i])
            else:
                clip_path = os.path.join(tmp, f"seg{i:04d}.mov")
                valid = False
            clip_paths.append(clip_path)
            if valid:
                cached += 1
            else:
                tasks.append((
                    i, cam, screen, s, e, layout, scr_start,
                    frame_plan[i], samples_plan[i],
                    fps_n, fps_d, v_enc, canvas, w_left, w_right,
                    fc_i, screen_crop, screen_fit, pad_color, clip_path,
                    input_frame_plan[i], layout_mode, pip_geo,
                ))

        n_split = sum(1 for _, _, l in seg_layouts if l == "split")
        print(f"  Export multicam : {n} segments ({n_split} {layout_mode} / {n - n_split} face) "
              f"× {workers} workers ({enc_name}, {W}x{H} @ {fps_n}/{fps_d} CFR"
              + (f", x{speed:.2f}" if speed != 1.0 else "") + ")")
        if cached:
            print(f"  Cache clips : {cached}/{n} réutilisés, {len(tasks)} à ré-encoder")

        total_input = sum(t[4] - t[3] for t in tasks) or 1.0
        encoded = 0.0
        errors = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(_encode_one_mc_segment, t) for t in tasks]
            done = 0
            for fut in as_completed(futures):
                i, clip, seg_dur, err = fut.result()
                done += 1
                encoded += seg_dur
                if err:
                    errors.append((i, err))
                    print(f"  [seg {i+1:04d}] ✗ {err}")
                elif done % 10 == 0 or done == len(tasks):
                    pct = 100.0 * encoded / total_input
                    print(f"  Progress : {done}/{len(tasks)} seg ({pct:.0f}%)", flush=True)

        if errors:
            sys.exit(f"[ERREUR] {len(errors)} segments ont échoué.")

        list_file = os.path.join(tmp, "concat.txt")
        with open(list_file, "w") as f:
            for cp in clip_paths:
                f.write(f"file '{cp}'\n")

        if audio_codec == "pcm_s16le":
            a_enc = ["-c:a", "pcm_s16le", "-ar", str(AUDIO_SR)]
        else:
            a_enc = ["-c:a", "aac", "-b:a", "320k", "-ar", str(AUDIO_SR)]

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
            sys.exit(f"[ERREUR] concat échoué :\n{result.stderr[-400:]}")

    # Purge des clips orphelins (cadrages d'itérations précédentes)
    if clips_dir:
        keep = {os.path.basename(p) for p in clip_paths}
        for fn in os.listdir(clips_dir):
            if fn not in keep:
                try:
                    os.remove(os.path.join(clips_dir, fn))
                except OSError:
                    pass

    actual_frames = _fast_frame_count(output)
    if actual_frames is None:
        try:
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                                "-count_frames", "-show_entries", "stream=nb_read_frames",
                                "-of", "csv=p=0", output], capture_output=True, text=True)
            actual_frames = int(r.stdout.strip() or 0) or None
        except Exception:
            actual_frames = None
    if actual_frames is not None:
        if abs(actual_frames - total_frames) > 2:
            print(f"  [WARN] frames produites {actual_frames} ≠ plan {total_frames}")
        else:
            print(f"  [AV sync] ✓ {actual_frames} frames produites (plan = {total_frames})")
    warn_av_sync(output, "après export")
    return face_crop, screen_crop


# ─── Helpers debug / calibration ─────────────────────────────────────────────

def calibrate(cam, screen, t, out_dir):
    cam_png = os.path.join(out_dir, "cam_frame.png")
    scr_png = os.path.join(out_dir, "screen_frame.png")
    for src, png in ((cam, cam_png), (screen, scr_png)):
        idx, local = src.locate(t)
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-ss", f"{local:.3f}", "-i", src.paths[idx],
                        "-frames:v", "1", "-map", "0:v:0", png], check=False)
    print(f"Frames extraites à t={t:.0f}s :\n  {cam_png}\n  {scr_png}")
    print("Mesure les crops et passe --screen-crop X:Y:W:H / --face-crop X:Y:W:H.")
    return cam_png, scr_png


def sync_check(cam, screen, syncmap, t, out_path, dur=10.0):
    """Extrait hstack + mix des deux audios : un écho audible = désync."""
    scr_t = syncmap.map(t)
    cam_args, c0 = cam.segment_input(t)
    scr_args, s0 = screen.segment_input(scr_t)
    cmd = (["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
           + cam_args + scr_args
           + ["-filter_complex",
              f"[0:v:0]trim=start={c0:.6f}:end={c0+dur:.6f},setpts=PTS-STARTPTS,"
              f"scale=960:540,fps=25[a];"
              f"[1:v:0]trim=start={s0:.6f}:end={s0+dur:.6f},setpts=PTS-STARTPTS,"
              f"scale=960:540,fps=25[b];"
              f"[a][b]hstack=inputs=2[v];"
              f"[0:a:0]atrim=start={c0:.6f}:end={c0+dur:.6f},asetpts=PTS-STARTPTS[a0];"
              f"[1:a:0]atrim=start={s0:.6f}:end={s0+dur:.6f},asetpts=PTS-STARTPTS[a1];"
              f"[a0][a1]amix=inputs=2:normalize=1[aud]",
              "-map", "[v]", "-map", "[aud]",
              "-c:v", "libx264", "-crf", "23", "-preset", "fast",
              "-c:a", "aac", "-b:a", "192k",
              out_path])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[WARN] sync-check échoué :\n{r.stderr[-300:]}")
    else:
        print(f"✓ Clip de vérification sync ({dur:.0f}s à t={t:.0f}s) → {out_path}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def _parse_crop(s):
    try:
        x, y, w, h = (int(v) for v in s.split(":"))
        return (x, y, w, h)
    except Exception:
        raise argparse.ArgumentTypeError("format attendu : X:Y:W:H")


def main():
    ap = argparse.ArgumentParser(
        description="Montage multicam automatique (webcam multi-parties + capture d'écran)")
    ap.add_argument("cam_parts", nargs="+", help="Fichier(s) webcam, dans l'ordre")
    ap.add_argument("--screen", help="Capture d'écran")
    ap.add_argument("--out", default=None, help="Fichier de sortie (.mp4)")
    ap.add_argument("--workdir", default=None,
                    help="Dossier de travail persistant (cache wav/sync/transcription)")
    # Sync
    ap.add_argument("--offset", type=float, default=None,
                    help="Force l'offset cam→écran (s), bypass cross-corrélation")
    ap.add_argument("--sync-only", action="store_true")
    ap.add_argument("--sync-check", action="store_true",
                    help="Exporte des clips hstack+amix de vérification et sort")
    ap.add_argument("--at", type=float, default=None,
                    help="Timestamp (s, timeline cam) pour --sync-check / --calibrate")
    # Calibration cadrage
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--screen-crop", type=_parse_crop, default=None,
                    help="Crop X:Y:W:H de la colonne de contenu sur la capture écran")
    ap.add_argument("--face-crop", type=_parse_crop, default=None,
                    help="Crop X:Y:W:H de la facecam pour la demi-droite (défaut : centré)")
    ap.add_argument("--split-ratio", type=float, default=0.5,
                    help="Part de largeur occupée par l'écran dans le layout split")
    ap.add_argument("--screen-fit", choices=("fill", "fit"), default="fill",
                    help="fill = remplit le panneau (rogne) ; fit = tient entier, "
                         "complété avec --pad-color (dézoom)")
    ap.add_argument("--layout-mode", choices=("split", "pip"), default="split",
                    help="Rendu des plans écran : split (côte à côte) ou pip "
                         "(écran plein cadre + visage carré incrusté)")
    ap.add_argument("--pip-size", type=float, default=0.22,
                    help="Côté du carré visage en fraction de la hauteur (pip)")
    ap.add_argument("--pip-margin", type=int, default=40,
                    help="Marge du carré visage au bord, en px (pip)")
    ap.add_argument("--pip-radius", type=float, default=0.0,
                    help="Rayon des coins du carré visage, fraction du côté (ex 0.08)")
    ap.add_argument("--face-track", action="store_true",
                    help="Recentre le carré visage par segment (OpenCV Haar)")
    ap.add_argument("--pip-corner", default="bottom-right",
                    choices=("bottom-right", "bottom-left", "top-right", "top-left"))
    ap.add_argument("--speed", type=float, default=1.0,
                    help="Accélération globale (ex 1.06), comme auto_edit")
    ap.add_argument("--max-face", type=float, default=None,
                    help="Durée max d'une série face avant flip en écran (défaut : off)")
    ap.add_argument("--split-ranges", default=None,
                    help="JSON [[start,end],...] en temps ÉCRAN où un rendu visuel est "
                         "affiché → segments forcés en écran (les --face-ranges priment)")
    ap.add_argument("--face-ranges", default=None,
                    help="JSON [[start,end],...] en temps ÉCRAN où l'écran est interdit "
                         "(ex : script visible) → segments forcés en face")
    ap.add_argument("--cut-ranges", default=None,
                    help="JSON [[start,end],...] en temps TRANSCRIPTION caméra à retirer "
                         "(reprises : seule la dernière prise reste)")
    ap.add_argument("--pad-color", default="0x181818",
                    help="Couleur de fond du pad en mode fit (défaut : fond Notion sombre)")
    # Coupes — VALEURS du pipeline auto_edit par défaut (coupes naturelles)
    ap.add_argument("--vad", choices=("auto", "tight"), default="auto",
                    help="auto = VAD auto_edit (seuil 0.40, silence 220ms) ; "
                         "tight = variante agressive cut_silences (silence 25ms)")
    ap.add_argument("--lead", type=float, default=LEADING_PADDING)   # 0.14
    ap.add_argument("--trail", type=float, default=TRAILING_PADDING)  # 0.02
    ap.add_argument("--silence-ms", type=int, default=25)   # VAD tight uniquement
    ap.add_argument("--threshold", type=float, default=0.55)  # VAD tight uniquement
    ap.add_argument("--drop-db", type=float, default=14)
    ap.add_argument("--min-seg", type=float, default=0.30)
    ap.add_argument("--min-gap", type=float, default=0.25,
                    help="Ne coupe un blanc que s'il dépasse ce seuil (s). Filet "
                         "anti-hachage léger au-dessus du silence VAD auto_edit "
                         "(220ms). 0 = comportement auto_edit strict.")
    ap.add_argument("--silence-db", type=float, default=-32.0)
    ap.add_argument("--silence-min-dur", type=float, default=0.04)
    ap.add_argument("--silence-snap", type=float, default=0.30)
    ap.add_argument("--silence-pad-lead", type=float, default=0.04)
    ap.add_argument("--silence-pad-trail", type=float, default=0.02)
    ap.add_argument("--no-fillers", action="store_true",
                    help="Ne coupe pas les euh/hm (silences uniquement)")
    ap.add_argument("--transcriber", choices=("elevenlabs", "whisper"),
                    default="elevenlabs",
                    help="whisper = faster-whisper local (repli si ElevenLabs KO)")
    ap.add_argument("--no-cache", action="store_true",
                    help="Ignore les caches (transcription, sync, wav)")
    # Layouts
    ap.add_argument("--no-llm", action="store_true",
                    help="Heuristique déterministe (pas d'appel OpenRouter)")
    ap.add_argument("--layout-only", action="store_true")
    ap.add_argument("--min-shot", type=float, default=4.0)
    ap.add_argument("--max-split", type=float, default=25.0)
    # Rendu
    ap.add_argument("--resolution", type=int, choices=sorted(RES_PRESETS),
                    default=1440)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--no-clip-cache", action="store_true",
                    help="Désactive le cache de clips segments (re-rendu complet)")
    ap.add_argument("--reuse-audio-from", default=None,
                    help="Réutilise la piste audio déjà polie de ce fichier "
                         "(mux lossless, saute le polish). À n'utiliser QUE si les "
                         "coupes sont inchangées — typiquement un ajustement de cadrage.")
    # Preview / reprise
    ap.add_argument("--preview-out", default=None)
    ap.add_argument("--from-json", default=None)
    # Post (hérités d'auto_edit)
    ap.add_argument("--no-polish", action="store_true")
    ap.add_argument("--lufs", type=float, default=LOUDNESS_TARGET_LUFS)
    ap.add_argument("--no-denoise", action="store_true")
    ap.add_argument("--no-deesser", action="store_true")
    ap.add_argument("--no-hpf", action="store_true")
    ap.add_argument("--hum", action="store_true")
    ap.add_argument("--no-notify", action="store_true")
    args = ap.parse_args()

    _load_env_fallback()

    # ── Reprise from-json : les chemins sources sont dans le JSON ──
    payload = None
    if args.from_json:
        with open(args.from_json) as f:
            payload = json.load(f)
        args.cam_parts = payload["cam_parts"]
        args.screen = payload["screen"]

    split_ranges = []
    if args.split_ranges:
        with open(args.split_ranges) as f:
            split_ranges = [[float(a), float(b)] for a, b in json.load(f)]
        print(f"[Split ranges] {len(split_ranges)} plages visuelles chargées "
              f"({sum(b - a for a, b in split_ranges):.0f}s)")
    face_ranges = []
    if args.face_ranges:
        with open(args.face_ranges) as f:
            face_ranges = [[float(a), float(b)] for a, b in json.load(f)]
        print(f"[Face ranges] {len(face_ranges)} plages interdites chargées "
              f"({sum(b - a for a, b in face_ranges):.0f}s)")

    if not args.screen:
        sys.exit("[ERREUR] --screen requis (ou --from-json).")
    for p in list(args.cam_parts) + [args.screen]:
        if not os.path.isfile(p):
            sys.exit(f"[ERREUR] Fichier introuvable : {p}")

    out_default_dir = Path.home() / "Desktop" / "AutoEdit"
    name = Path(args.screen).stem.replace(" ", "_") + "_multicam"
    if args.out:
        output = os.path.abspath(args.out)
        out_dir = Path(output).parent
    else:
        out_dir = out_default_dir
        output = str(out_dir / f"{name}.mp4")
    out_dir.mkdir(parents=True, exist_ok=True)
    workdir = args.workdir or str(out_dir / f"{name}_work")
    os.makedirs(workdir, exist_ok=True)

    cam = SourceInput(args.cam_parts, workdir, "cam")
    screen = SourceInput([args.screen], workdir, "screen")

    # DJI/écran CFR attendus ; si VFR, on refuse plutôt que de désynchroniser.
    # (ensure_cfr_source ne sait pas traiter un input concat multi-parties.)
    for label, src in (("caméra", cam), ("écran", screen)):
        for p in src.paths:
            if is_source_vfr(p):
                if src.is_concat:
                    sys.exit(f"[ERREUR] {p} est VFR : convertis chaque partie en CFR "
                             f"d'abord (ensure_cfr_source) puis relance.")
                print(f"  [CFR] {label} VFR → conversion")
                cfr = ensure_cfr_source(p, workdir)
                src.paths = [cfr]

    av_cam = get_av_offset(cam.probe_path)
    av_screen = get_av_offset(screen.probe_path)
    args._av_cam = av_cam
    fps = get_video_fps(cam.probe_path)
    fps_n, fps_d = get_video_fps_rational(cam.probe_path)

    W, H, target_vbr = RES_PRESETS[args.resolution]
    canvas = (W, H)

    print(f"\n{'─'*60}")
    print(f"  Caméra : {' + '.join(Path(p).name for p in cam.paths)}")
    print(f"           {cam.duration/60:.1f} min @ {fps:.0f} fps"
          + (f" (raccords : {', '.join(f'{b:.1f}s' for b in cam.boundaries)})"
             if cam.boundaries else ""))
    print(f"  Écran  : {Path(screen.paths[0]).name} ({screen.duration/60:.1f} min)")
    print(f"  Sortie : {output} ({W}x{H})")
    print(f"{'─'*60}\n")

    # ── Calibration : frames + exit ──
    if args.calibrate:
        t = args.at if args.at is not None else min(60.0, cam.duration / 2)
        calibrate(cam, screen, t, str(out_dir))
        return

    # ── Sync (cache workdir) ──
    cam_wav = extract_wav_48k(cam, workdir)
    screen_wav = extract_wav_48k(screen, workdir)

    if payload and "sync" in payload:
        sy = payload["sync"]
        syncmap = SyncMap([tuple(a) for a in sy["anchors"]],
                          sy["av_cam"], sy["av_screen"])
        print(f"[Sync] chargée depuis JSON : {syncmap.describe()}")
    else:
        sync_cache = os.path.join(workdir, "sync.json")
        sync_sig = _sources_signature(cam.paths + screen.paths)
        cached = None
        if os.path.exists(sync_cache) and not args.no_cache and args.offset is None:
            try:
                data = json.load(open(sync_cache))
                if data["sig"] == sync_sig:
                    cached = data
            except Exception:
                pass
        if cached:
            syncmap = SyncMap([tuple(a) for a in cached["anchors"]], av_cam, av_screen)
            print(f"[Sync] cache : {syncmap.describe()}")
        else:
            print("[Sync] cross-corrélation audio (GCC-PHAT)...")
            syncmap, report = measure_sync(
                cam_wav, screen_wav, cam.duration, screen.duration,
                cam.boundaries, forced_offset=args.offset,
                av_cam=av_cam, av_screen=av_screen)
            for row in report:
                if row[0] == "mesure":
                    print(f"    t={row[1]:8.1f}s  offset={row[2]:+.4f}s  conf={row[3]:.1f}")
                elif row[0] == "fit":
                    print(f"    fit linéaire OK (résidu max {row[1]*1000:.1f}ms)")
                elif row[0] == "piecewise":
                    print(f"    [WARN] résidu {row[1]*1000:.1f}ms > "
                          f"{SYNC_LINEAR_TOL*1000:.0f}ms → mapping piecewise")
            print(f"  → {syncmap.describe()}")
            if args.offset is None:
                with open(sync_cache, "w") as f:
                    json.dump({"sig": sync_sig, "anchors": syncmap.anchors}, f)

    if args.sync_only:
        return

    if args.sync_check:
        pts = ([args.at] if args.at is not None
               else [cam.duration * 0.1, cam.duration * 0.5, cam.duration * 0.92])
        for t in pts:
            out_clip = str(out_dir / f"{name}_synccheck_{int(t)}s.mp4")
            sync_check(cam, screen, syncmap, t, out_clip)
        return

    # ── Segments + layouts ──
    if payload:
        seg_layouts = [(float(s), float(e), str(l)) for s, e, l in payload["segments"]]
        screen_crop = args.screen_crop or (tuple(payload["crops"]["screen"])
                                           if payload["crops"].get("screen") else None)
        face_crop = args.face_crop or (tuple(payload["crops"]["face"])
                                       if payload["crops"].get("face") else None)
        if "layout_mode" in payload and args.layout_mode == "split":
            args.layout_mode = payload["layout_mode"]
        if payload.get("pip"):
            args.pip_size = payload["pip"].get("size", args.pip_size)
            args.pip_margin = payload["pip"].get("margin", args.pip_margin)
            args.pip_corner = payload["pip"].get("corner", args.pip_corner)
            if args.pip_radius == 0.0:
                args.pip_radius = float(payload["pip"].get("radius", 0.0))
        face_crops = {int(k): tuple(v) for k, v in (payload.get("face_crops") or {}).items()}
        if payload.get("speed") and args.speed == 1.0:
            args.speed = float(payload["speed"])
        # Plages interdites : ré-appliquées même sur un JSON édité à la main
        fr = face_ranges or payload.get("face_ranges") or []
        if fr:
            segs = [(s, e) for s, e, _ in seg_layouts]
            lays, forced = apply_face_ranges([l for _, _, l in seg_layouts],
                                             segs, syncmap, fr)
            seg_layouts = [(s, e, l) for (s, e), l in zip(segs, lays)]
            if forced:
                print(f"  [Face ranges] {len(forced)} segments forcés en face (JSON)")
        # Params de rendu embarqués dans le JSON (le CLI ne prime que s'il diffère du défaut)
        if args.split_ratio == 0.5 and payload.get("split_ratio"):
            args.split_ratio = float(payload["split_ratio"])
        if args.screen_fit == "fill" and payload.get("screen_fit"):
            args.screen_fit = payload["screen_fit"]
        if args.pad_color == "0x181818" and payload.get("pad_color"):
            args.pad_color = payload["pad_color"]
        print(f"[Segments] {len(seg_layouts)} chargés depuis {args.from_json}")
    else:
        # Transcription (cache workdir) + VAD en parallèle
        words = None
        transcache = os.path.join(workdir, "multicam.transcache.json")
        if os.path.exists(transcache) and not args.no_cache:
            try:
                data = json.load(open(transcache))
                if data["sig"] == _sources_signature(cam.paths):
                    words = data["words"]
                    print(f"[Transcription] cache : {len(words)} mots")
            except Exception:
                words = None

        need_words = not args.no_fillers or not args.no_llm
        if words is None and need_words:
            if args.transcriber == "whisper":
                print("[Transcription] faster-whisper local (repli ElevenLabs)...")
                words = transcribe_whisper(cam_wav)
            else:
                print("[Transcription] ElevenLabs Scribe...")
                words = transcribe_elevenlabs(cam_wav)
            with open(transcache, "w") as f:
                json.dump({"sig": _sources_signature(cam.paths), "words": words}, f,
                          ensure_ascii=False)
        words = words or []

        print("[Coupes] silences + fillers sur la piste caméra...")
        segments = detect_segments_multicam(
            cam_wav, cam.duration, [] if args.no_fillers else words, args, fps)

        # mots en video-time pour split + layouts
        words_vid = [{**w, "start": w["start"] + av_cam, "end": w["end"] + av_cam}
                     for w in words]
        segments = split_long_segments(segments, words_vid,
                                       max_len=args.max_split, fps=fps)
        print(f"  {len(segments)} segments après scission des tirades > "
              f"{args.max_split:.0f}s")

        # Layouts
        layouts = None
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not args.no_llm and api_key and words_vid:
            print("[Layouts] décision par Claude (OpenRouter)...")
            layouts = decide_layouts_llm(segments, words_vid, api_key)
        if layouts is None:
            if not args.no_llm:
                print("[Layouts] fallback heuristique")
            layouts = decide_layouts_heuristic(segments)
        layouts = enforce_layout_constraints(layouts, segments,
                                             min_shot=args.min_shot,
                                             max_split=args.max_split,
                                             max_face=args.max_face)
        # Un segment qui sort de la couverture écran ne peut être qu'en face
        for i, (s, e) in enumerate(segments):
            if layouts[i] == "split":
                if syncmap.map(s) < 0 or syncmap.map(e) > screen.duration - 0.5:
                    layouts[i] = "face"
        locked = set()
        for i, (s, e) in enumerate(segments):
            if syncmap.map(s) < 0 or syncmap.map(e) > screen.duration - 0.5:
                locked.add(i)
        layouts, forced = apply_face_ranges(layouts, segments, syncmap, face_ranges)
        if forced:
            print(f"  [Face ranges] {len(forced)} segments forcés en face "
                  f"({len(face_ranges)} plages interdites)")
        locked.update(forced)
        locked_split = set()
        if split_ranges:
            for i, (s, e) in enumerate(segments):
                if i in locked:
                    continue
                ss, se = syncmap.map(s), syncmap.map(e)
                ov = sum(max(0.0, min(se, b) - max(ss, a)) for a, b in split_ranges)
                if ov >= min(1.0, 0.5 * (e - s)):
                    locked_split.add(i)
            print(f"  [Split ranges] {len(locked_split)} segments verrouillés écran "
                  f"({len(split_ranges)} plages visuelles)")
        if args.max_face:
            # Intro/outro face (8 s) verrouillés, puis cadence optimale par DP
            acc = 0.0
            for i in range(len(segments)):
                locked.add(i); acc += segments[i][1] - segments[i][0]
                if acc >= 8.0:
                    break
            acc = 0.0
            for i in range(len(segments) - 1, -1, -1):
                locked.add(i); acc += segments[i][1] - segments[i][0]
                if acc >= 8.0:
                    break
            lock_map = {i: 0 for i in locked}
            lock_map.update({i: 1 for i in locked_split})
            layouts = solve_layouts_dp(layouts, segments, min_shot=args.min_shot,
                                       max_run=max(args.max_split, args.max_face),
                                       locked=lock_map)
            print(f"  [Cadence DP] runs dans [{args.min_shot:.0f}s, "
                  f"{max(args.max_split, args.max_face):.0f}s], "
                  f"{len(locked)} segments verrouillés face")
        for i in locked_split:
            layouts[i] = "split"
        for i in locked:
            layouts[i] = "face"

        seg_layouts = [(s, e, l) for (s, e), l in zip(segments, layouts)]
        screen_crop = args.screen_crop
        face_crop = args.face_crop
        face_crops = {}

    if args.face_track and not face_crops:
        side = face_crop[2] if face_crop else None
        r = subprocess.run(["ffprobe", "-v", "quiet", "-select_streams", "v:0",
                            "-print_format", "json", "-show_streams", cam.probe_path],
                           capture_output=True, text=True)
        s0 = json.loads(r.stdout)["streams"][0]
        sw, sh = int(s0["width"]), int(s0["height"])
        side = side or _even(min(sw, sh))
        sidecar = os.path.join(workdir, "face_crops.json")
        sig = _sources_signature(cam.paths) + f"|{side}|{len(seg_layouts)}"
        cached_fc = None
        if os.path.exists(sidecar) and not args.no_cache:
            try:
                data = json.load(open(sidecar))
                if data.get("sig") == sig:
                    cached_fc = {int(k): tuple(v) for k, v in data["face_crops"].items()}
            except Exception:
                cached_fc = None
        if cached_fc is not None:
            face_crops = cached_fc
            print(f"[Face track] cache workdir : {len(face_crops)} segments cadrés")
        else:
            print("[Face track] détection du visage par segment split...")
            face_crops = track_face_crops(cam, seg_layouts, side, sw, sh)
            with open(sidecar, "w") as f:
                json.dump({"sig": sig,
                           "face_crops": {str(k): list(v) for k, v in face_crops.items()}}, f)

    kept = sum(e - s for s, e, _ in seg_layouts)
    n_split = sum(1 for _, _, l in seg_layouts if l == "split")
    print(f"\n  Durée finale : {kept/60:.1f} min — {len(seg_layouts)} segments "
          f"({n_split} split / {len(seg_layouts)-n_split} face)\n")

    if args.layout_only:
        for i, (s, e, l) in enumerate(seg_layouts):
            print(f"  SEG {i:3d} [{s:8.2f} → {e:8.2f}] {e-s:5.1f}s  {l}")
        return

    if args.preview_out:
        out_payload = {
            "version": 1,
            "mode": "multicam",
            "cam_parts": cam.paths,
            "screen": screen.paths[0],
            "duration": cam.duration,
            "sync": {"anchors": syncmap.anchors, "av_cam": av_cam,
                     "av_screen": av_screen},
            "crops": {"screen": list(screen_crop) if screen_crop else None,
                      "face": list(face_crop) if face_crop else None},
            "canvas": [W, H],
            "split_ratio": args.split_ratio,
            "screen_fit": args.screen_fit,
            "pad_color": args.pad_color,
            "layout_mode": args.layout_mode,
            "pip": {"size": args.pip_size, "margin": args.pip_margin,
                    "corner": args.pip_corner, "radius": args.pip_radius},
            "face_crops": {str(k): list(v) for k, v in (face_crops or {}).items()},
            "speed": args.speed,
            "face_ranges": face_ranges,
            "split_ranges": split_ranges,
            "segments": [[s, e, l] for s, e, l in seg_layouts],
            "kept": kept,
        }
        with open(args.preview_out, "w") as f:
            json.dump(out_payload, f, ensure_ascii=False, indent=1)
        print(f"✓ Aperçu écrit → {args.preview_out}")
        return

    # ── Rendu (FIX SYNC #3 : re-snap frames après tout aller-retour JSON) ──
    seg_layouts = [(s2, e2, l) for ((s2, e2), (_, _, l)) in zip(
        snap_segments_to_frames([(s, e) for s, e, _ in seg_layouts], fps),
        seg_layouts)]
    # Aucun segment ne doit chevaucher un raccord entre parties caméra
    seg_layouts = split_at_boundaries(seg_layouts, cam.boundaries, fps)

    print("[Export]")
    clip_cache = not args.no_clip_cache
    # FIX SYNC #11 : encodage AAC unique — PCM intermédiaire si polish actif
    if args.reuse_audio_from:
        # Ajustement de cadrage : coupes inchangées → l'audio poli existant est
        # réutilisable tel quel (lossless). On rend la vidéo puis on greffe l'audio.
        if not os.path.isfile(args.reuse_audio_from):
            sys.exit(f"[ERREUR] --reuse-audio-from introuvable : {args.reuse_audio_from}")
        vtmp = output[:-len(Path(output).suffix)] + "_vtmp.mp4"
        export_multicam(cam, screen, seg_layouts, syncmap, vtmp, canvas,
                        args.split_ratio, face_crop, screen_crop, target_vbr,
                        workers=args.workers, audio_codec="aac", tmp_root=workdir,
                        screen_fit=args.screen_fit, pad_color=args.pad_color,
                        clip_cache=clip_cache, speed=args.speed,
                        layout_mode=args.layout_mode, pip_size=args.pip_size,
                        pip_margin=args.pip_margin, pip_corner=args.pip_corner,
                        pip_radius=args.pip_radius, face_crops=face_crops)
        print("\n[Audio] réutilisation de la piste polie (mux lossless)...")
        r = subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", vtmp, "-i", args.reuse_audio_from,
            "-map", "0:v:0", "-map", "1:a:0", "-c", "copy",
            "-movflags", "+faststart", output,
        ], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"[ERREUR] mux audio réutilisé échoué :\n{r.stderr[-400:]}")
        try:
            os.remove(vtmp)
        except OSError:
            pass
    elif args.no_polish:
        export_multicam(cam, screen, seg_layouts, syncmap, output, canvas,
                        args.split_ratio, face_crop, screen_crop, target_vbr,
                        workers=args.workers, audio_codec="aac", tmp_root=workdir,
                        screen_fit=args.screen_fit, pad_color=args.pad_color,
                        clip_cache=clip_cache, speed=args.speed,
                        layout_mode=args.layout_mode, pip_size=args.pip_size,
                        pip_margin=args.pip_margin, pip_corner=args.pip_corner,
                        pip_radius=args.pip_radius, face_crops=face_crops)
    else:
        intermediate = output[:-len(Path(output).suffix)] + "_pcm.mkv"
        export_multicam(cam, screen, seg_layouts, syncmap, intermediate, canvas,
                        args.split_ratio, face_crop, screen_crop, target_vbr,
                        workers=args.workers, audio_codec="pcm_s16le",
                        tmp_root=workdir,
                        screen_fit=args.screen_fit, pad_color=args.pad_color,
                        clip_cache=clip_cache, speed=args.speed,
                        layout_mode=args.layout_mode, pip_size=args.pip_size,
                        pip_margin=args.pip_margin, pip_corner=args.pip_corner,
                        pip_radius=args.pip_radius, face_crops=face_crops)
        print("\n[Polish audio]")
        _install_chunked_denoise()   # borne la mémoire (anti-OOM sur vidéos longues)
        polish_audio(intermediate, output, lufs=args.lufs,
                     denoise=not args.no_denoise,
                     deesser=not args.no_deesser,
                     hpf=not args.no_hpf,
                     hum=args.hum)
        try:
            os.remove(intermediate)
        except OSError:
            pass

    print(f"\n✓ Terminé → {output}\n")
    if not args.no_notify:
        notify("AutoEdit multicam", f"Export terminé — {Path(output).name}")


if __name__ == "__main__":
    main()
