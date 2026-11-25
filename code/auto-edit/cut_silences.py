#!/usr/bin/python3
"""
cut_silences.py — Coupe les silences d'une vidéo (VAD Silero + trim énergie).
Pas de transcription, pas de Claude.

Usage :
  /usr/bin/python3 /Users/lucienmallet/cut_silences.py "/chemin/video.mp4"

Options workflow :
  --preview-out JSON   Détecte les coupes, écrit le JSON et sort (pas d'export)
  --from-json JSON     Charge un JSON de segments et lance l'export (skip détection)
  --speed 1.06         Accélère la vidéo finale (voix + image) — 1.0 = désactivé
  --no-notify          Désactive la notification macOS à la fin
"""
import argparse
import array
import json
import os
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from auto_edit import (
    extract_audio, get_duration, export, polish_audio,
    LOUDNESS_TARGET_LUFS,
    get_av_offset,
    snap_segments_to_frames, get_video_fps,
    ensure_cfr_source,
    detect_silences, snap_segments_to_silence,
    apply_tail_bounds, TAIL_MODES, TAIL_RELAX_DEFAULT,
    load_audio_mono,
)

# Mode "relaxed" : le trim énergie doit descendre plus bas avant de déclarer la
# fin de la phrase, sinon la décroissance de la dernière syllabe est rognée.
TAIL_RELAX_DROP_DB = 6


# ─── VAD Silero ───────────────────────────────────────────────────────────────

def get_vad_tight(wav_path, silence_ms=30, threshold=0.55):
    import torch
    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad",
        model="silero_vad",
        force_reload=False,
        trust_repo=True,
    )
    (get_speech_timestamps, *_) = utils
    # ffmpeg plutôt que silero.read_audio : torchaudio ≥ 2.9 exige torchcodec
    # pour l'I/O audio (voir load_audio_mono dans auto_edit.py).
    wav_tensor = load_audio_mono(wav_path, sr=16000)
    timestamps = get_speech_timestamps(
        wav_tensor, model,
        sampling_rate=16000,
        threshold=threshold,
        min_speech_duration_ms=100,
        min_silence_duration_ms=silence_ms,
        return_seconds=True,
    )
    return [(t["start"], t["end"]) for t in timestamps]


# ─── Trim énergie ─────────────────────────────────────────────────────────────

def _rms_windows(samples, sr, win_ms=10):
    win = max(1, int(sr * win_ms / 1000))
    result = []
    for i in range(0, len(samples) - win, win):
        chunk = samples[i:i+win]
        rms   = (sum(x*x for x in chunk) / len(chunk)) ** 0.5
        result.append((i / sr, rms))
    return result


def trim_segment_end(wav_path, seg_end, sr=16000, win_ms=10,
                     drop_db=12, lookback=0.9):
    try:
        with wave.open(wav_path, 'rb') as wf:
            ch   = wf.getnchannels()
            sw   = wf.getsampwidth()
            sr   = wf.getframerate()
            nfr  = wf.getnframes()
            raw  = wf.readframes(nfr)
        fmt = {1:'b', 2:'h', 4:'i'}.get(sw, 'h')
        all_samples = array.array(fmt, raw)
        if ch > 1:
            all_samples = all_samples[::ch]
    except Exception:
        return seg_end

    start_sample = max(0, int((seg_end - lookback) * sr))
    end_sample   = min(len(all_samples), int(seg_end * sr))
    region       = list(all_samples[start_sample:end_sample])
    if not region:
        return seg_end

    windows = _rms_windows(region, sr, win_ms)
    if not windows:
        return seg_end

    peak = max(r for _, r in windows) or 1
    threshold_rms = peak * (10 ** (-drop_db / 20))

    new_end = seg_end
    for t_rel, rms in reversed(windows):
        if rms >= threshold_rms:
            new_end = (seg_end - lookback) + t_rel + win_ms / 1000
            break
    return min(new_end, seg_end)


# ─── Détection complète ───────────────────────────────────────────────────────

def detect_segments(video, duration, args):
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "audio.wav")
        print("[1/3] Extraction audio...")
        extract_audio(video, wav)

        print(f"[2/3] Détection des silences...")
        vad = get_vad_tight(wav, silence_ms=args.silence_ms, threshold=args.threshold)
        print(f"  {len(vad)} segments de voix bruts")

        # IMPORTANT : tout le travail wav-bound (trim énergie, silencedetect)
        # se fait en wav-time. L'offset A/V est appliqué EN FIN seulement
        # pour shifter vers la video-time (= grille de la piste vidéo).
        av_offset = get_av_offset(video)

        # Trim énergie (wav-time)
        trimmed = [(s, trim_segment_end(wav, e, drop_db=args.drop_db)) for s, e in vad]

        # Lead / trail (wav-time)
        segments = []
        for s, e in trimmed:
            s2 = max(0.0,     s - args.lead)
            e2 = min(duration, e + args.trail)
            if e2 > s2:
                segments.append((s2, e2))

        # Fusion
        merged = []
        for s, e in segments:
            if merged and s <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            else:
                merged.append((s, e))
        segments = merged

        # Min-seg
        before   = len(segments)
        segments = [(s, e) for s, e in segments if (e - s) >= args.min_seg]
        if (before - len(segments)):
            print(f"  {before - len(segments)} micro-segment(s) ignoré(s)")

        # Snap sur silences RÉELS (amplitude ffmpeg, précision ms) — wav-time.
        silences_fine = detect_silences(wav, noise_db=args.silence_db,
                                        min_dur=args.silence_min_dur)
        segments = snap_segments_to_silence(
            segments, silences_fine,
            max_snap=args.silence_snap,
            edge_pad_lead=args.silence_pad_lead,
            edge_pad_trail=args.silence_pad_trail,
        )

        # Fin "relaxed" : la marge élargie ne doit pas mordre sur le segment suivant
        if getattr(args, "tail", "tight") == "relaxed":
            segments = apply_tail_bounds(segments)

        # FIX SYNC #1 — wav-time → video-time (offset audio_start vs video_start)
        if abs(av_offset) > 1e-4:
            print(f"  [AV sync] offset source détecté : {av_offset*1000:+.1f}ms — recalibrage")
            segments = [(s + av_offset, e + av_offset) for s, e in segments]

        # FIX SYNC #3 — snap sur la grille de frames source (video-time)
        segments = snap_segments_to_frames(segments, get_video_fps(video))

        kept = sum(e - s for s, e in segments)
        cut  = duration - kept
        pct  = 100 * cut / duration if duration else 0
        print(f"  Conservé : {kept:.1f}s / {duration:.1f}s  —  coupé : {cut:.1f}s ({pct:.1f}%)")
        return segments


# ─── Notification ─────────────────────────────────────────────────────────────

def _run_export_and_polish(video, segments, output, args):
    """
    FIX SYNC #11 — export+polish à encodage AAC UNIQUE :
    - --no-polish : export direct AAC.
    - sinon       : export en PCM intermédiaire (MKV), polish encode AAC une seule fois.
    """
    if args.no_polish:
        export(video, segments, output, speed=args.speed, audio_codec="aac")
        return

    suffix = Path(output).suffix
    intermediate = output[:-len(suffix)] + "_pcm.mkv"
    export(video, segments, intermediate, speed=args.speed,
           audio_codec="pcm_s16le")

    print("\n[Polish audio]")
    polish_audio(intermediate, output, lufs=args.lufs,
                 denoise=not args.no_denoise,
                 deesser=not args.no_deesser,
                 hpf=not args.no_hpf,
                 hum=getattr(args, "hum", False))
    try:
        os.remove(intermediate)
    except OSError:
        pass
    print(f"  ✓ Audio polished → {Path(output).name}")


def notify(title, message):
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}" sound name "Glass"'
        ], check=False)
    except Exception:
        pass


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Coupe les silences d'une vidéo")
    ap.add_argument("video",         help="Fichier vidéo source")
    # Lead/trail très serrés : le snap silencedetect (amplitude réelle) prend le relais
    # et tolère un large overshoot des bornes VAD via --silence-snap (300 ms par défaut).
    ap.add_argument("--lead",        type=float, default=0.07)
    ap.add_argument("--trail",       type=float, default=0.05)
    ap.add_argument("--silence-ms",  type=int,   default=25)
    ap.add_argument("--threshold",   type=float, default=0.55)
    ap.add_argument("--drop-db",     type=float, default=14)
    ap.add_argument("--min-seg",     type=float, default=0.30)
    # Snap final sur silences ffmpeg silencedetect (amplitude RMS, précision ~ms).
    ap.add_argument("--silence-db",        type=float, default=-32.0,
                    help="Seuil amplitude pour silencedetect (-32dB par défaut). "
                         "Descendre vers -28 si bruit de fond, vers -36 si studio très propre.")
    ap.add_argument("--silence-min-dur",   type=float, default=0.04,
                    help="Durée min d'un silence détecté (s)")
    ap.add_argument("--silence-snap",      type=float, default=0.30,
                    help="Fenêtre de recherche autour de chaque borne (s). "
                         "Au-delà : borne d'origine conservée.")
    ap.add_argument("--silence-pad-lead",  type=float, default=0.04,
                    help="Marge avant la première frame de parole (s)")
    ap.add_argument("--silence-pad-trail", type=float, default=0.02,
                    help="Marge après la dernière frame de parole (s)")
    ap.add_argument("--speed",       type=float, default=1.0,
                    help="Accélération (1.0 = désactivé, 1.06 = +6%%)")
    ap.add_argument("--preview-out", default=None,
                    help="Détecte + dump JSON + exit (pas d'export)")
    ap.add_argument("--from-json",   default=None,
                    help="Charge segments JSON + export (skip détection)")
    ap.add_argument("--no-notify",   action="store_true")
    ap.add_argument("--no-polish",   action="store_true",
                    help="Désactive le polish audio post-export")
    ap.add_argument("--lufs",        type=float, default=LOUDNESS_TARGET_LUFS)
    ap.add_argument("--no-denoise",  action="store_true")
    ap.add_argument("--no-deesser",  action="store_true")
    ap.add_argument("--no-hpf",      action="store_true")
    ap.add_argument("--hum",         action="store_true",
                    help="Hum reduction (notch 50Hz) — uniquement si buzz secteur audible")
    ap.add_argument("--tail", choices=TAIL_MODES, default="tight",
                    help="Agressivité de la coupe en fin de phrase. tight = réglage "
                         "historique (défaut), relaxed = garde ~%.2fs de plus après le "
                         "dernier mot (évite les fins de mots rognées). Le début de "
                         "phrase est identique dans les deux cas." % TAIL_RELAX_DEFAULT)
    ap.add_argument("--tail-pad", type=float, default=None,
                    help=f"Secondes ajoutées en fin de phrase avec --tail relaxed "
                         f"(défaut: {TAIL_RELAX_DEFAULT})")
    args = ap.parse_args()

    # Mode relaxed : décale les trois réglages de fin (trail VAD, trim énergie,
    # marge post-silence). Une valeur passée explicitement en ligne de commande
    # reste prioritaire — on ne relâche que les défauts.
    if args.tail == "relaxed":
        tail_pad = TAIL_RELAX_DEFAULT if args.tail_pad is None else max(0.0, args.tail_pad)
        if args.trail == ap.get_default("trail"):
            args.trail += tail_pad
        if args.silence_pad_trail == ap.get_default("silence_pad_trail"):
            args.silence_pad_trail += tail_pad
        if args.drop_db == ap.get_default("drop_db"):
            args.drop_db += TAIL_RELAX_DROP_DB
        print(f"Fin de phrase : relaxed (+{tail_pad*1000:.0f}ms, "
              f"trail={args.trail*1000:.0f}ms drop={args.drop_db:.0f}dB)")

    video = os.path.abspath(args.video)
    if not os.path.isfile(video):
        sys.exit(f"Fichier introuvable : {video}")

    stem, suffix = Path(video).stem, Path(video).suffix
    speed_tag = f"_x{args.speed:.2f}".replace(".", "p") if args.speed != 1.0 else ""
    out_dir = Path(video).parent / f"{stem}_nosilence{speed_tag}"
    out_dir.mkdir(exist_ok=True)
    output = str(out_dir / f"{stem}_nosilence{speed_tag}{suffix}")
    duration = get_duration(video)

    # ── Mode 2 : charge JSON et exporte ──
    if args.from_json:
        with open(args.from_json) as f:
            segments = [tuple(s) for s in json.load(f)["segments"]]
        print(f"\nVidéo   : {Path(video).name}")
        print(f"Segments chargés depuis : {args.from_json} ({len(segments)} segments)")
        if args.speed != 1.0:
            print(f"Vitesse : {args.speed}x")
        print(f"Sortie  : {output}\n")

        with tempfile.TemporaryDirectory() as tmp_cfr:
            # FIX SYNC #13 — force CFR ABSOLU (re-encode visuellement transparent si VFR)
            video_cfr = ensure_cfr_source(video, tmp_cfr)

            # FIX SYNC #3 — snap sur la grille de frames de la source CFR
            segments = snap_segments_to_frames(segments, get_video_fps(video_cfr))

            print("[3/3] Export vidéo...")
            # FIX SYNC #11 : export+polish à encodage AAC UNIQUE
            _run_export_and_polish(video_cfr, segments, output, args)

        print(f"\n✓ Terminé → {output}")
        if not args.no_notify:
            notify("AutoEdit", f"Export terminé — {Path(output).name}")
        return

    # ── Mode 1 ou normal : détecte ──
    print(f"\nVidéo    : {Path(video).name}")
    print(f"Durée    : {duration:.1f}s")
    print(f"Réglages : lead={args.lead*1000:.0f}ms trail={args.trail*1000:.0f}ms "
          f"silence={args.silence_ms}ms threshold={args.threshold}")
    if args.speed != 1.0:
        print(f"Vitesse  : {args.speed}x")
    print(f"Sortie   : {output}\n")

    with tempfile.TemporaryDirectory() as tmp_cfr:
        # FIX SYNC #13 — force CFR ABSOLU sur la source pour tout le pipeline
        video_cfr = ensure_cfr_source(video, tmp_cfr)

        segments = detect_segments(video_cfr, duration, args)

        # ── Mode 1 : dump JSON + exit ──
        if args.preview_out:
            payload = {
                "video":    video,
                "duration": duration,
                "segments": [[s, e] for s, e in segments],
                "kept":     sum(e - s for s, e in segments),
            }
            with open(args.preview_out, "w") as f:
                json.dump(payload, f)
            print(f"\n✓ Aperçu écrit → {args.preview_out}")
            return

        # ── Mode normal : export ──
        print("\n[3/3] Export vidéo...")
        # FIX SYNC #11 : export+polish à encodage AAC UNIQUE
        _run_export_and_polish(video_cfr, segments, output, args)

    print(f"\n✓ Terminé → {output}")
    if not args.no_notify:
        notify("AutoEdit", f"Export terminé — {Path(output).name}")


if __name__ == "__main__":
    main()
