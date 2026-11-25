"""Assemblage local par GOP, cache indépendant et trois calculs simultanés.

Exemples : --plan-only --no-open ; --benchmark 10 --no-open ; --no-open.
Ce programme ne lance aucun rendu AWS et n'ouvre aucune fenêtre.
"""
import argparse
import bisect
import hashlib
import json
import math
import shlex
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from fractions import Fraction
from pathlib import Path

import render_final as r

ORIGINAL_RUN = r.run
LOCK = threading.Lock()


def limited_run(cmd, cwd=r.R, essais=1):
    """Limiter chaque décodeur, encodeur et graphe FFmpeg."""
    if cmd[0] == "ffmpeg":
        limited = [cmd[0], "-filter_threads", "3", "-filter_complex_threads", "3"]
        for value in cmd[1:]:
            if value == "-i":
                limited += ["-threads", "3"]
            limited.append(str(value))
        limited[-1:-1] = ["-threads", "3"]
        cmd = limited
    return ORIGINAL_RUN(cmd, cwd=cwd, essais=essais)


def probe(path):
    return json.loads(limited_run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=codec_name,profile,level,width,height,pix_fmt,r_frame_rate,time_base,duration,nb_frames,bit_rate,color_range,color_space,color_transfer,color_primaries,sample_aspect_ratio",
        "-of", "json", str(path)], cwd=r.E))["streams"][0]


def load_assets():
    places = json.loads((r.E / "placements.json").read_text())
    caps = json.loads((r.E / "captions_lucien.json").read_text())["occs"]
    badge = json.loads((r.E / "props-05b-badge-chapitres.json").read_text())["chapitres"]
    chapters = json.loads((r.E / "chapitres.json").read_text())
    ranges = {}
    for item in places:
        lo, hi = item["from"], item["from"] + item["dur"] - 1
        current = ranges.setdefault(item["id"], [lo, hi, item["mode"]])
        current[0], current[1] = min(current[0], lo), max(current[1], hi)
    video, audio, missing = r.build_assets(places, caps, badge, ranges)
    if missing:
        raise RuntimeError("Médias manquants : " + ", ".join(sorted(set(missing))))
    return video, audio, badge, chapters


def keyframes(total):
    cache = r.WORK / "fast-keyframes.json"
    state = file_state(r.SRC)
    if cache.exists():
        saved = json.loads(cache.read_text())
        if saved.get("source") == state and saved.get("total") == total:
            return saved["keys"]
    data = json.loads(limited_run([
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-skip_frame", "nokey",
        "-show_frames", "-show_entries", "frame=best_effort_timestamp_time", "-of", "json", str(r.SRC)], cwd=r.E))
    keys = sorted({0.0, total} | {
        round(float(frame["best_effort_timestamp_time"]) * r.FPS_OUT) / r.FPS_OUT
        for frame in data["frames"] if 0 < float(frame["best_effort_timestamp_time"]) < total})
    cache.parent.mkdir(exist_ok=True, parents=True)
    cache.write_text(json.dumps({"source": state, "total": total, "keys": keys}))
    return keys


def plan_segments(assets, keys, max_seconds=10):
    """Élargir chaque plage active aux GOP voisins, puis limiter les tronçons."""
    active = []
    for item in assets:
        start, end = max(0, item["at"]), min(keys[-1], item["at"] + item["dur"])
        if end <= start:
            continue
        active.append((keys[max(0, bisect.bisect_right(keys, start) - 1)],
                       keys[min(len(keys) - 1, bisect.bisect_left(keys, end))]))
    active = r.merge_intervals(active)
    segments = []
    for start, end in zip(keys, keys[1:]):
        render = any(a < end and b > start for a, b in active)
        # Garder les plages copiées longues ; les rendus restent courts.
        if segments and segments[-1]["render"] == render and (
            not render or end - segments[-1]["start"] <= max_seconds):
            segments[-1]["end"] = end
        else:
            segments.append({"start": start, "end": end, "render": render})
    return segments


def file_state(path):
    path = Path(path)
    stat = path.stat()
    return [str(path), stat.st_size, stat.st_mtime_ns]


def signature(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


def compatible(path, source, expected):
    info = probe(path)
    fields = ("codec_name", "profile", "level", "width", "height", "pix_fmt", "r_frame_rate", "time_base",
              "color_range", "color_space", "color_transfer", "color_primaries", "sample_aspect_ratio")
    differences = {key: (source.get(key), info.get(key)) for key in fields if source.get(key) != info.get(key)}
    if differences:
        raise RuntimeError(f"Concat incompatible {path.name}: {differences}")
    if abs(float(info["duration"]) - expected) > 1 / r.FPS_OUT + 0.001:
        raise RuntimeError(f"Durée incorrecte {path.name}: {info['duration']} / {expected}")
    if "nb_frames" in info and int(info["nb_frames"]) != round(expected * r.FPS_OUT):
        raise RuntimeError(f"Nombre d'images incorrect : {path.name}")


def configure(source):
    if source["codec_name"] != "h264" or source["pix_fmt"] != "yuv420p":
        raise RuntimeError("Cette copie mixte exige une source H.264 yuv420p.")
    r.W, r.H = source["width"], source["height"]
    r.FPS_OUT = float(Fraction(source["r_frame_rate"]))
    timescale = Fraction(source["time_base"]).denominator
    profile = {"High": "high", "Main": "main", "Constrained Baseline": "baseline"}.get(source["profile"])
    if profile is None:
        raise RuntimeError("Profil H.264 non pris en charge")
    r.run = limited_run
    r.encoder_args = lambda: [
        "-c:v", "h264_videotoolbox", "-profile:v", profile,
        "-level:v", str(source["level"] / 10), "-b:v", source.get("bit_rate", "32000000"),
        "-pix_fmt", "yuv420p", "-g", str(round(r.FPS_OUT * 2)),
        "-video_track_timescale", str(timescale),
        *[arg for key, option in (("color_range", "-color_range"), ("color_space", "-colorspace"),
                                  ("color_transfer", "-color_trc"), ("color_primaries", "-color_primaries"))
          if source.get(key) for arg in (option, source[key])], "-an"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=float, metavar="SECONDS")
    parser.add_argument("--start", type=float, help="début de l'extrait de mesure")
    parser.add_argument("--jobs", type=int, default=3, choices=range(1, 4))
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--no-open", action="store_true", help="compatibilité : aucune ouverture dans tous les modes")
    args = parser.parse_args()
    source = probe(r.SRC)
    configure(source)
    video_assets, audio_assets, badge, chapters = load_assets()
    total = math.floor(float(source["duration"]) * r.FPS_OUT + 1e-6) / r.FPS_OUT
    work = r.WORK / "fast-gop"
    work.mkdir(parents=True, exist_ok=True)
    plan = plan_segments(video_assets, keyframes(total))
    summary = {"total_seconds": total, "segments": len(plan),
               "render_seconds": sum(s["end"] - s["start"] for s in plan if s["render"]),
               "copy_seconds": sum(s["end"] - s["start"] for s in plan if not s["render"]), "jobs": args.jobs}
    (work / "plan.json").write_text(json.dumps({"summary": summary, "segments": plan}, indent=2))
    print(json.dumps(summary), flush=True)
    if args.plan_only:
        return
    # Construire le fichier partagé avant de démarrer plusieurs encodeurs.
    r.static_blur_mask()
    if args.benchmark is not None:
        if args.benchmark <= 0:
            parser.error("--benchmark doit être positif")
        # Choisir la fenêtre comptant le plus de secondes-calques, flou inclus.
        starts = [s["start"] for s in plan if s["render"] and s["start"] + args.benchmark <= total]
        start = args.start if args.start is not None else max(starts, key=lambda a: sum(
            max(0, min(a + args.benchmark, v["at"] + v["dur"]) - max(a, v["at"]))
            * (2 if v["blur_band"] else 1) for v in video_assets))
        end = min(total, start + args.benchmark)
        if not 0 <= start < end:
            parser.error("plage de mesure incorrecte")
        bench = work / "benchmark"
        bench.mkdir(exist_ok=True)
        began = time.monotonic()
        path, _ = r.render_segment(0, start, end, video_assets, bench)
        elapsed = time.monotonic() - began
        compatible(path, source, end - start)
        result = {"start": start, "duration": end - start, "wall_seconds": elapsed,
                  "seconds_per_video_second": elapsed / (end - start), "output": str(path),
                  "note": "Mesure isolée. Le débit de trois tâches simultanées reste à mesurer."}
        (work / "benchmark.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result), flush=True)
        return

    code = [file_state(__file__), file_state(r.__file__), file_state(r.SRC), r.encoder_args()]
    progress = {"status": "rendering", "done": 0, "total": len(plan), "segments": {}}
    progress_path = work / "progress.json"

    def save_progress():
        temporary = work / "progress.tmp"
        temporary.write_text(json.dumps(progress, indent=2))
        temporary.replace(progress_path)

    def segment(index, spec):
        start, end = spec["start"], spec["end"]
        relevant = [v for v in video_assets if r.overlap(v, start, end)]
        blur_intervals = [[v["at"], v["dur"]] for v in video_assets if v["blur_band"]]
        key = signature([code, spec, relevant, blur_intervals, [file_state(v["path"]) for v in relevant]])
        folder = work / key[:24]
        folder.mkdir(exist_ok=True)
        path, marker = folder / "segment-00.mp4", folder / "complete.json"
        cached = marker.exists() and path.exists() and json.loads(marker.read_text()).get("signature") == key
        began = time.monotonic()
        if not cached:
            if spec["render"]:
                # Le flou conserve ses fondus sur les intervalles globaux.
                # render_segment filtre lui-même les entrées visibles.
                r.render_segment(0, start, end, video_assets, folder)
            else:
                limited_run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.6f}",
                             "-i", str(r.SRC), "-map", "0:v:0", "-frames:v", str(round((end-start)*r.FPS_OUT)),
                             "-c:v", "copy", "-an", str(path)], cwd=r.E)
            compatible(path, source, end - start)
            marker.write_text(json.dumps({"signature": key, "wall_seconds": time.monotonic() - began}))
        else:
            compatible(path, source, end - start)
        with LOCK:
            progress["done"] += 1
            progress["segments"][str(index)] = {**spec, "cached": cached, "wall_seconds": time.monotonic() - began}
            save_progress()
        return index, path

    save_progress()
    try:
        outputs = {}
        with ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = [pool.submit(segment, i, spec) for i, spec in enumerate(plan)]
            for future in as_completed(futures):
                index, path = future.result()
                outputs[index] = path
        progress["status"] = "audio"
        save_progress()
        audio_key = signature([file_state(r.__file__), file_state(r.SRC), audio_assets, badge, chapters,
                               [file_state(a["path"]) for a in audio_assets],
                               [file_state(p) for p in sorted(r.MUS.glob("*.mp3"))]])
        audio_dir = work / ("audio-" + audio_key[:24])
        audio_dir.mkdir(exist_ok=True)
        audio_marker = audio_dir / "complete.json"
        if audio_marker.exists():
            audio = Path(json.loads(audio_marker.read_text())["path"])
        else:
            audio, _, _ = r.render_audio(total, total, audio_assets, badge, chapters, audio_dir)
            audio_marker.write_text(json.dumps({"path": str(audio)}))
        concat = work / "concat.txt"
        concat.write_text("".join(f"file {shlex.quote(str(outputs[i]))}\nduration {s['end']-s['start']:.6f}\n"
                                  for i, s in enumerate(plan)))
        progress["status"] = "concat"
        save_progress()
        joined = work / "video.mp4"
        limited_run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
                     "-map", "0:v:0", "-c:v", "copy", "-an", str(joined)], cwd=r.E)
        compatible(joined, source, total)
        r.mux(joined, audio, r.OUT, total)
        progress.update(status="complete", output=str(r.OUT))
        save_progress()
        print(str(r.OUT), flush=True)
    except BaseException as error:
        progress.update(status="failed", error=str(error))
        save_progress()
        raise


if __name__ == "__main__":
    main()
