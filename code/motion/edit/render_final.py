"""Rendu final : motion designs, bruitages et musique sur montage-cut.mp4.

Les rendus Remotion sont mis en cache avec leur commande. L'assemblage mixe
l'audio une fois. La vidéo est encodée par tronçons HEVC parallèles, concaténée
sans réencodage, puis muxée avec l'audio.

Usage :
  python3 render_final.py [--skip-renders]
  python3 render_final.py --render-only
  python3 render_final.py --skip-renders --test
  python3 render_final.py --skip-renders --duree 60 [--mono]
"""
import argparse
import hashlib
import json
import math
import os
import shlex
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path


E = Path(__file__).resolve().parent
R = E.parent / "remotion"
F = R / "out/final"
SOL = E / "sol"
WORK = SOL / ".assembly"
SRC = Path.home() / "Desktop/montage-2026-09-17/montage-cut.mp4"
OUT = Path.home() / "Desktop/montage-2026-09-17/montage-motion.mp4"
MUS = E / "musique"
FPS = 30
SCALE = "1.3333333333333333"
LAMBDA_SITE = os.environ.get("REMOTION_LAMBDA_SITE", "martell-motion")
LAMBDA_REGION = "eu-north-1"
LAMBDA_DEPLOY_FINGERPRINT = SOL / "lambda-site.sha256"
W, H, FPS_OUT = 2560, 1440, 50
MUSIC_GAIN = 0.07
SFX_GAIN = 0.40
FADE = 1.5
SEGMENT_COUNT = 6
GOP = 250
MUSIQUE = {
    0: "00-intro-Unseen-Elin-Piel.mp3",
    1: "01-amateur-Apparent-Solution-Brendon-Moeller.mp3",
    2: "02-habitue-Steall-Waters-Luba-Hilman.mp3",
    3: "03-integrateur-The-Shape-of-Memory-Luba-Hilman.mp3",
    4: "04-operateur-Shadowed-John-B-Lund.mp3",
    5: "05-batisseur-Fallout-Lennon-Hutton.mp3",
    6: "06-orchestrateur-The-Farmhouse-Silver-Maple.mp3",
}
OUTRO = ("07-outro-Pink-Pulsar-ELFL.mp3", 44.0, 35.0)
BADGE_FADE = 13 / FPS


def run(cmd, cwd=R, essais=1):
    """Exécuter une commande et remonter sa dernière erreur utile."""
    last = None
    for k in range(essais):
        last = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if not last.returncode:
            return last.stdout
        label = cmd[4] if len(cmd) > 4 else cmd[0]
        sys.stderr.write(f"essai {k + 1}/{essais} raté : {label}\n")
    sys.stderr.write(
        f"ÉCHEC : {shlex.join([str(x) for x in cmd])[:600]}\n"
        f"{last.stderr[-4000:]}\n"
    )
    raise SystemExit(1)


def media_duration(path):
    return float(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(path),
            ],
            cwd=E,
        )
    )


def command_signature(cmd):
    clean = [str(x) for x in cmd if not str(x).startswith("--concurrency=")]
    return shlex.join(clean) + "\n"


def hash_paths(roots):
    digest = hashlib.sha256()
    files = []
    for root in roots:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(path for path in root.rglob("*") if path.is_file())
    for path in sorted(set(files)):
        digest.update(str(path.relative_to(R.parent)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


@lru_cache(maxsize=1)
def shared_render_fingerprint():
    """Identifier les entrées communes qui changent le rendu des compositions."""
    return hash_paths(
        [
            R / "src/shared",
            R / "src/index.ts",
            R / "src/Root.tsx",
            R / "public/sfx",
            R / "remotion.config.ts",
        ]
    )


@lru_cache(maxsize=1)
def shared_render_latest_mtime():
    roots = [
        R / "src/shared",
        R / "src/index.ts",
        R / "src/Root.tsx",
        R / "public/sfx",
        R / "remotion.config.ts",
    ]
    mtimes = []
    for root in roots:
        if root.is_file():
            mtimes.append(root.stat().st_mtime)
        elif root.is_dir():
            mtimes.extend(
                path.stat().st_mtime for path in root.rglob("*") if path.is_file()
            )
    return max(mtimes, default=0.0)


def deployed_site_fingerprint():
    """Identifier exactement le bundle et les ressources envoyés sur Lambda."""
    return hash_paths(
        [
            R / "src",
            R / "public",
            R / "remotion.config.ts",
            R / "package.json",
            R / "package-lock.json",
        ]
    )


def record_lambda_deploy():
    SOL.mkdir(parents=True, exist_ok=True)
    LAMBDA_DEPLOY_FINGERPRINT.write_text(deployed_site_fingerprint() + "\n")


def load_lambda_credentials():
    """Utiliser la session temporaire du projet sans exposer de secret."""
    os.environ["REMOTION_AWS_PROFILE"] = "remotion-runtime"
    os.environ["AWS_PROFILE"] = "remotion-runtime"
    os.environ["AWS_SDK_LOAD_CONFIG"] = "1"
    os.environ["REMOTION_AWS_REGION"] = LAMBDA_REGION
    os.environ["AWS_REGION"] = LAMBDA_REGION
    os.environ["AWS_DEFAULT_REGION"] = LAMBDA_REGION
    verified = subprocess.run(
        [
            "aws",
            "sts",
            "get-caller-identity",
            "--profile",
            "remotion-project",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if verified.returncode:
        raise SystemExit(
            "session AWS expirée : lancer aws login --profile remotion-project"
        )


def validate_lambda_deploy():
    if not LAMBDA_DEPLOY_FINGERPRINT.exists():
        raise SystemExit("site Lambda non enregistré : lancer edit/deploy_lambda.sh")
    deployed = LAMBDA_DEPLOY_FINGERPRINT.read_text().strip()
    if deployed != deployed_site_fingerprint():
        raise SystemExit("site Lambda périmé : relancer edit/deploy_lambda.sh")


def composition_fingerprint(job):
    """Identifier le code propre à une composition sans invalider les autres."""
    cid = job[4]
    digest = hashlib.sha256()
    digest.update(shared_render_fingerprint().encode())
    roots = [R / "src/comps" / cid, R / "public" / cid.split("-", 1)[0]]
    for arg in job:
        value = str(arg)
        if value.startswith("--props="):
            props = Path(value.split("=", 1)[1])
            if props.exists():
                roots.append(props)
    files = []
    for root in roots:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(path for path in root.rglob("*") if path.is_file())
    for path in sorted(files):
        digest.update(str(path.relative_to(R.parent)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def composition_latest_mtime(job):
    cid = job[4]
    roots = [R / "src/comps" / cid, R / "public" / cid.split("-", 1)[0]]
    mtimes = []
    for root in roots:
        if root.is_file():
            mtimes.append(root.stat().st_mtime)
        elif root.is_dir():
            mtimes.extend(
                path.stat().st_mtime for path in root.rglob("*") if path.is_file()
            )
    return max([shared_render_latest_mtime(), *mtimes])


def lambda_command(job, output=None):
    """Convertir une ancienne commande locale en commande Remotion Lambda."""
    kind = job[2]
    frames_per_lambda = 250
    command = [
        "npx",
        "--no-install",
        "remotion",
        "lambda",
        kind,
        LAMBDA_SITE,
        job[4],
        str(output if output is not None else job[5]),
    ]
    for arg in job[6:]:
        value = str(arg)
        if value.startswith("--concurrency=") or value == "--enforce-audio-track":
            continue
        if value.startswith("--frames="):
            start, end = value.removeprefix("--frames=").split("-", 1)
            frames_per_lambda = max(5, math.ceil((int(end) - int(start) + 1) / 6))
        command.append(value)
    if kind == "render":
        command.append(f"--frames-per-lambda={frames_per_lambda}")
    return command


def lambda_signature(job):
    stable_command = [
        value
        for value in lambda_command(job)
        if not value.startswith("--frames-per-lambda=")
    ]
    return (
        command_signature(stable_command)
        + f"composition-sha256={composition_fingerprint(job)}\n"
    )


def rendered_output_complete(job, out):
    if not out.exists() or out.stat().st_size <= 0 or Path(str(out) + ".tmp").exists():
        return False
    if job[2] == "still":
        probe = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_name,width,height",
                "-of",
                "csv=p=0",
                str(out),
            ],
            capture_output=True,
            text=True,
        )
        fields = [field for field in probe.stdout.strip().split(",") if field]
        return probe.returncode == 0 and len(fields) == 3 and fields[0] == "png"
    frame_arg = next((value for value in job if str(value).startswith("--frames=")), None)
    if frame_arg is None:
        return False
    lo, hi = (int(value) for value in frame_arg.split("=", 1)[1].split("-", 1))
    expected = (hi - lo + 1) / FPS
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    if probe.returncode:
        return False
    try:
        actual = float(probe.stdout.strip())
    except ValueError:
        return False
    if actual < expected - 0.5 / FPS:
        return False
    video_probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=codec_name,pix_fmt",
            "-of",
            "csv=p=0",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    if video_probe.returncode:
        return False
    codec_fields = [field for field in video_probe.stdout.strip().split(",") if field]
    if "--codec=prores" in job:
        return (
            len(codec_fields) == 2
            and codec_fields[0] == "prores"
            and codec_fields[1].startswith("yuva444p")
        )
    return len(codec_fields) == 2 and codec_fields[0] == "h264"


def render_jobs(places, caps, badge, rng, skip):
    """Construire les médias sur AWS Lambda et valider leur cache."""
    jobs = []
    for cid, (lo, hi, mode) in rng.items():
        if mode == "overlay":
            jobs.append(
                [
                    "npx",
                    "remotion",
                    "render",
                    "build",
                    cid,
                    str(F / f"{cid}.mov"),
                    f"--frames={lo}-{hi}",
                    "--codec=prores",
                    "--prores-profile=4444",
                    "--pixel-format=yuva444p10le",
                    "--image-format=png",
                    '--props={"showPlate":false}',
                ]
            )
        else:
            jobs.append(
                [
                    "npx",
                    "remotion",
                    "render",
                    "build",
                    cid,
                    str(F / f"{cid}.mp4"),
                    f"--frames={lo}-{hi}",
                    "--codec=h264",
                    "--crf=12",
                ]
            )

    cap_props = E / "props-01b-sous-titres-lucien.json"
    for i, occ in enumerate(caps):
        lo, hi = int(occ["start"] * FPS), int(occ["end"] * FPS)
        jobs.append(
            [
                "npx",
                "remotion",
                "render",
                "build",
                "01b-sous-titres-lucien",
                str(F / f"cap{i:02d}.mov"),
                f"--frames={lo}-{hi}",
                "--codec=prores",
                "--prores-profile=4444",
                "--pixel-format=yuva444p10le",
                "--image-format=png",
                f"--props={cap_props}",
            ]
        )

    for level in sorted({item["niveau"] for item in badge}):
        props = E / f"props-badge-{level}.json"
        props_content = json.dumps(
            {
                "durationInFrames": 120,
                "chapitres": [{"niveau": level, "start": 0, "end": 4}],
            }
        )
        if not props.exists() or props.read_text() != props_content:
            props.write_text(props_content)
        jobs.append(
            [
                "npx",
                "remotion",
                "still",
                "build",
                "05b-badge-chapitres",
                str(F / f"badge{level}.png"),
                "--frame=60",
                "--image-format=png",
                f"--props={props}",
            ]
        )

    for job in jobs:
        job += [
            f"--scale={SCALE}",
            "--concurrency=3",
            "--log=error",
            "--timeout=240000",
        ] + ([] if job[2] == "still" else ["--enforce-audio-track"])

    if skip:
        return

    load_lambda_credentials()
    validate_lambda_deploy()

    print("1. musique d'assemblage", flush=True)
    MUS.mkdir(exist_ok=True)
    run(["rsync", "-a", "prod:/root/martell-sound/musique/", str(MUS) + "/"])
    print("2. projet Lambda déjà déployé", flush=True)
    print(f"3. {len(jobs)} rendus Lambda, 1 à la fois", flush=True)
    (SOL / "lambda-renders.log").write_text("")
    done = [0]

    def go(job):
        out = Path(job[5])
        range_file = Path(str(out) + ".range")
        signature = lambda_signature(job)
        complete = rendered_output_complete(job, out)

        # Adopter le nouveau format de cache pour les médias locaux inchangés.
        legacy = (
            complete
            and range_file.exists()
            and "composition-sha256=" not in range_file.read_text()
        )
        if legacy and composition_latest_mtime(job) <= out.stat().st_mtime:
            range_file.write_text(signature)

        cached = (
            complete and range_file.read_text() == signature
            if range_file.exists()
            else False
        )

        if cached:
            done[0] += 1
            print(f"   {done[0]}/{len(jobs)} {job[4]} (déjà rendu)", flush=True)
            return

        download = out.with_name(f".{out.stem}.lambda-download{out.suffix}")
        download.unlink(missing_ok=True)
        command = lambda_command(job, output=download)
        try:
            output = run(command, essais=3)
            if not rendered_output_complete(job, download):
                raise SystemExit(f"téléchargement Lambda invalide : {job[4]}")
            os.replace(download, out)
        finally:
            download.unlink(missing_ok=True)
        with (SOL / "lambda-renders.log").open("a") as log:
            log.write(output)
            if output and not output.endswith("\n"):
                log.write("\n")
        range_file.write_text(signature)
        done[0] += 1
        print(f"   {done[0]}/{len(jobs)} {job[4]}", flush=True)

    def go_safe(job):
        try:
            go(job)
        except SystemExit:
            print(f"   raté définitivement : {job[4]}", flush=True)
            return job[4]
        return None

    with ThreadPoolExecutor(max_workers=1) as pool:
        failures = [item for item in pool.map(go_safe, jobs) if item is not None]
    if failures:
        raise SystemExit("rendus Lambda en échec : " + ", ".join(failures))


def build_assets(places, caps, badge, rng):
    """Décrire les calques vidéo et leurs sons sur la timeline finale."""
    video = []
    audio = []
    missing = []
    readable = {}

    def media_is_readable(path):
        if path not in readable:
            probe = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "stream=index",
                    "-of",
                    "csv=p=0",
                    str(path),
                ],
                capture_output=True,
                text=True,
            )
            readable[path] = probe.returncode == 0 and bool(probe.stdout.strip())
        return readable[path]

    def add_video(
        path, start, dur, at, alpha, image=False, fade=None, blur_band=False
    ):
        path = Path(path)
        if not path.exists() or not media_is_readable(path):
            missing.append(path.name)
            return
        item = {
            "path": path,
            "start": float(start),
            "dur": float(dur),
            "at": float(at),
            "alpha": bool(alpha),
            "image": bool(image),
            "fade": fade,
            "blur_band": bool(blur_band),
        }
        video.append(item)
        if not image:
            audio.append(item.copy())

    for item in places:
        lo = rng[item["id"]][0]
        ext = "mov" if item["mode"] == "overlay" else "mp4"
        add_video(
            F / f"{item['id']}.{ext}",
            (item["from"] - lo) / FPS,
            item["dur"] / FPS,
            item["at"],
            item["mode"] == "overlay",
            blur_band=True,
        )

    for i, occ in enumerate(caps):
        lo = int(occ["start"] * FPS)
        add_video(
            F / f"cap{i:02d}.mov",
            0,
            (int(occ["end"] * FPS) - lo + 1) / FPS,
            lo / FPS,
            True,
            blur_band=True,
        )

    for item in badge:
        dur = item["end"] - item["start"]
        add_video(
            F / f"badge{item['niveau']}.png",
            0,
            dur,
            item["start"],
            True,
            image=True,
            fade=max(0, dur - BADGE_FADE),
        )

    return video, audio, missing


def overlap(item, t0, t1):
    start = max(item["at"], t0)
    end = min(item["at"] + item["dur"], t1)
    if end - start < 0.5 / FPS_OUT:
        return None
    return start, end


def merge_intervals(intervals):
    """Fusionner les plages qui se touchent pour garder un filtre compact."""
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1] + 0.5 / FPS_OUT:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def add_bottom_blur(filters, assets, t0, t1, base="[base0]", mask_input=None):
    """Flouter progressivement le tiers inférieur pendant les motions."""
    intervals = []
    for item in assets:
        if not item.get("blur_band"):
            continue
        intervals.append((item['at'], item['at'] + item['dur']))
    intervals = merge_intervals(intervals)
    intervals = [(a,b) for a,b in intervals if a < t1 and b > t0]
    if not intervals:
        return base

    if mask_input is None:
        raise ValueError('Le masque PNG fixe doit être fourni comme entrée.')
    band_h = H // 3
    band_y = H - band_h
    n = len(intervals)
    filters.append(f'{base}split={n+1}[band_clean]' + ''.join(f'[bs{i}]' for i in range(n)))
    filters.append(f'{mask_input}format=gray,split={n}' + ''.join(f'[bm{i}]' for i in range(n)))
    current = '[band_clean]'
    for i, (absolute_start, absolute_end) in enumerate(intervals):
        start, end = max(absolute_start,t0)-t0, min(absolute_end,t1)-t0
        duration = end-start
        whole = absolute_end-absolute_start
        fade = min(.30, whole/2)
        offset = max(absolute_start,t0)-absolute_start
        filters.append(f'[bs{i}]trim=start={start:.6f}:end={end:.6f},setpts=PTS-STARTPTS,crop={W}:{band_h}:0:{band_y},gblur=sigma=14:steps=3[bb{i}]')
        filters.append(f'[bm{i}]setpts=PTS-STARTPTS+{offset:.6f}/TB,fade=t=in:st=0:d={fade:.6f},fade=t=out:st={whole-fade:.6f}:d={fade:.6f},trim=duration={duration:.6f},setpts=PTS-STARTPTS[mask{i}]')
        filters.append(f'[bb{i}][mask{i}]alphamerge,setpts=PTS-STARTPTS+{start:.6f}/TB[ba{i}]')
        filters.append(f'{current}[ba{i}]overlay=x=0:y={band_y}:eof_action=pass:format=auto[bc{i}]')
        current = f'[bc{i}]'
    return current


def static_blur_mask():
    path = SOL / f'blur-mask-{W}x{H//3}-v1.png'
    if not path.exists():
        run(['ffmpeg','-nostdin','-y','-v','error','-filter_threads','1','-f','lavfi','-i',f'nullsrc=s={W}x{H//3},format=gray,geq=lum=255*(3*pow(Y/H\\,2)-2*pow(Y/H\\,3))','-frames:v','1','-threads','1',str(path)],cwd=E)
    return path


def add_video_inputs(cmd, filters, assets, t0, t1, base="[base0]", first_input=1):
    """Ajouter seulement les calques visibles dans un tronçon."""
    index = first_input
    current = base
    for item in assets:
        visible = overlap(item, t0, t1)
        if not visible:
            continue
        start, end = visible
        local_at = start - t0
        source_offset = item["start"] + start - item["at"]
        visible_dur = end - start
        fmt = "yuva444p" if item["alpha"] else "yuv420p"

        if item["image"]:
            cmd += [
                "-loop",
                "1",
                "-framerate",
                str(FPS_OUT),
                "-t",
                f"{item['dur']:.6f}",
                "-i",
                str(item["path"]),
            ]
            chain = f"[{index}:v]format={fmt}"
            if item["fade"] is not None:
                chain += (
                    f",fade=t=out:st={item['fade']:.6f}:d={BADGE_FADE:.6f}:alpha=1"
                )
            chain += (
                f",trim=start={source_offset:.6f}:duration={visible_dur:.6f},"
                f"setpts=PTS-STARTPTS+{local_at:.6f}/TB[v{index}]"
            )
        else:
            cmd += [
                "-ss",
                f"{source_offset:.6f}",
                "-t",
                f"{visible_dur:.6f}",
                "-i",
                str(item["path"]),
            ]
            chain = (
                f"[{index}:v]fps={FPS_OUT},scale={W}:{H}:flags=lanczos,format={fmt},"
                f"setpts=PTS-STARTPTS+{local_at:.6f}/TB[v{index}]"
            )

        filters.append(chain)
        filters.append(
            f"{current}[v{index}]overlay=eof_action=pass:format=auto[b{index}]"
        )
        current = f"[b{index}]"
        index += 1
    return current, index


def keyframe_boundaries(source, total, count):
    """Placer les frontières près des images clés et sur la grille 50 fps."""
    if count <= 1:
        return [0.0, total]
    packets = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "packet=pts_time,flags",
            "-of",
            "csv=p=0",
            str(source),
        ],
        cwd=E,
    )
    keys = []
    for line in packets.splitlines():
        fields = line.split(",")
        if len(fields) >= 2 and "K" in fields[-1]:
            try:
                keys.append(round(float(fields[0]) * FPS_OUT) / FPS_OUT)
            except ValueError:
                pass

    boundaries = [0.0]
    for i in range(1, count):
        ideal = total * i / count
        candidates = [
            value
            for value in keys
            if boundaries[-1] + 1.0 < value < total - 1.0
            and abs(value - ideal) <= 10.0
        ]
        chosen = (
            min(candidates, key=lambda value: abs(value - ideal))
            if candidates
            else ideal
        )
        chosen = round(chosen * FPS_OUT) / FPS_OUT
        boundaries.append(chosen)
    boundaries.append(round(total * FPS_OUT) / FPS_OUT)
    return boundaries


def encoder_args():
    return [
        "-c:v",
        "hevc_videotoolbox",
        "-b:v",
        "50M",
        "-tag:v",
        "hvc1",
        "-pix_fmt",
        "yuv420p",
        "-g",
        str(GOP),
        "-flags",
        "+cgop",
        "-an",
    ]


def render_segment(index, t0, t1, assets, work):
    """Réencoder un tronçon autonome avec les seuls calques qui le chevauchent."""
    frames = round((t1 - t0) * FPS_OUT)
    out = work / f"segment-{index:02d}.mp4"
    filter_file = work / f"segment-{index:02d}.filter"
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{t0:.6f}",
        "-to",
        f"{t1:.6f}",
        "-i",
        str(SRC),
    ]
    filters = [f"[0:v]trim=end_frame={frames},setpts=PTS-STARTPTS[base0]"]
    backdrop = [item for item in assets if not item["alpha"] and not item["image"]]
    foreground = [item for item in assets if item["alpha"] or item["image"]]
    base, next_input = add_video_inputs(cmd, filters, backdrop, t0, t1)
    if any(a.get('blur_band') and overlap(a,t0,t1) for a in assets):
        cmd += ['-loop','1','-framerate',str(FPS_OUT),'-t',str(t1-t0),'-i',str(static_blur_mask())]
        base = add_bottom_blur(filters, assets, t0, t1, base=base, mask_input=f'[{next_input}:v]')
        next_input += 1
    base, _ = add_video_inputs(
        cmd, filters, foreground, t0, t1, base=base, first_input=next_input
    )
    filter_file.write_text(";\n".join(filters) + "\n")
    cmd += [
        "-/filter_complex",
        str(filter_file),
        "-map",
        base,
        "-frames:v",
        str(frames),
        *encoder_args(),
        str(out),
    ]
    run(cmd, cwd=E)
    return out, cmd


def render_parallel_video(total, assets, work):
    count = 1 if total <= 8.001 else SEGMENT_COUNT
    boundaries = keyframe_boundaries(SRC, total, count)
    jobs = [
        (i, boundaries[i], boundaries[i + 1], assets, work)
        for i in range(len(boundaries) - 1)
    ]
    print(
        "   frontières : " + ", ".join(f"{value:.2f}" for value in boundaries),
        flush=True,
    )
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        rendered = list(pool.map(lambda values: render_segment(*values), jobs))

    concat_file = work / "segments.txt"
    concat_file.write_text(
        "".join(f"file {shlex.quote(str(path))}\n" for path, _ in rendered)
    )
    joined = work / "video-parallel.mp4"
    concat_cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        str(joined),
    ]
    run(concat_cmd, cwd=E)
    elapsed = time.monotonic() - started
    commands = [cmd for _, cmd in rendered] + [concat_cmd]
    return joined, elapsed, commands


def render_mono_video(total, assets, work):
    """Conserver l'ancienne chaîne vidéo dans un seul processus ffmpeg."""
    frames = round(total * FPS_OUT)
    out = work / "video-mono.mp4"
    filter_file = work / "mono.filter"
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-to",
        f"{total:.6f}",
        "-i",
        str(SRC),
    ]
    filters = [f"[0:v]trim=end_frame={frames},setpts=PTS-STARTPTS[base0]"]
    backdrop = [item for item in assets if not item["alpha"] and not item["image"]]
    foreground = [item for item in assets if item["alpha"] or item["image"]]
    base, next_input = add_video_inputs(cmd, filters, backdrop, 0.0, total)
    if any(a.get('blur_band') and overlap(a,0,total) for a in assets):
        cmd += ['-loop','1','-framerate',str(FPS_OUT),'-t',str(total),'-i',str(static_blur_mask())]
        base = add_bottom_blur(filters, assets, 0.0, total, base=base, mask_input=f'[{next_input}:v]')
        next_input += 1
    base, _ = add_video_inputs(
        cmd, filters, foreground, 0.0, total, base=base, first_input=next_input
    )
    filter_file.write_text(";\n".join(filters) + "\n")
    cmd += [
        "-/filter_complex",
        str(filter_file),
        "-map",
        base,
        "-frames:v",
        str(frames),
        *encoder_args(),
        str(out),
    ]
    started = time.monotonic()
    run(cmd, cwd=E)
    return out, time.monotonic() - started, [cmd]


def render_audio(total, source_total, assets, badge, chapters, work):
    """Mixer une seule fois le graphe audio historique vers AAC 320 kbit/s."""
    out = work / "audio.m4a"
    filter_file = work / "audio.filter"
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-t",
        f"{total:.6f}",
        "-i",
        str(SRC),
    ]
    filters = []
    mixed = ["[0:a]"]
    index = 1

    for item in assets:
        visible = overlap(item, 0.0, total)
        if not visible:
            continue
        start, end = visible
        source_offset = item["start"] + start - item["at"]
        cmd += [
            "-ss",
            f"{source_offset:.6f}",
            "-t",
            f"{end - start:.6f}",
            "-i",
            str(item["path"]),
        ]
        delay = int(start * 1000)
        filters.append(
            f"[{index}:a]asetpts=PTS-STARTPTS,aresample=48000,"
            f"volume={SFX_GAIN},adelay={delay}|{delay}[a{index}]"
        )
        mixed.append(f"[a{index}]")
        index += 1

    sfx = R / "public/sfx/grave-apparition.wav"
    seen = set()
    for item in badge:
        level = item["niveau"]
        if level in seen:
            continue
        seen.add(level)
        if item["start"] >= total or not sfx.exists():
            continue
        cmd += ["-i", str(sfx)]
        delay = int(item["start"] * 1000)
        filters.append(
            f"[{index}:a]aresample=48000,volume={0.55 * SFX_GAIN:.6f},"
            f"adelay={delay}|{delay}[a{index}]"
        )
        mixed.append(f"[a{index}]")
        index += 1

    starts = sorted(
        {0: 0.0, **{c["niveau"]: c["start"] for c in chapters}}.items()
    )
    outro_at = source_total - OUTRO[2]
    for pos, (level, t0) in enumerate(starts):
        t1 = starts[pos + 1][1] if pos + 1 < len(starts) else outro_at
        full_duration = t1 - t0
        audible_end = min(t1, total)
        if audible_end <= t0:
            continue
        audible_duration = audible_end - t0
        cmd += [
            "-t",
            f"{audible_duration:.6f}",
            "-i",
            str(MUS / MUSIQUE[level]),
        ]
        delay = int(t0 * 1000)
        filters.append(
            f"[{index}:a]aresample=48000,volume={MUSIC_GAIN},afade=t=in:d=0.3,"
            f"afade=t=out:st={max(0, full_duration - FADE):.6f}:d={FADE},"
            f"adelay={delay}|{delay}[m{index}]"
        )
        mixed.append(f"[m{index}]")
        index += 1

    if outro_at < total:
        offset = max(0.0, -outro_at)
        audible_start = max(0.0, outro_at)
        audible_duration = min(OUTRO[2] - offset, total - audible_start)
        cmd += [
            "-ss",
            f"{OUTRO[1] + offset:.6f}",
            "-t",
            f"{audible_duration:.6f}",
            "-i",
            str(MUS / OUTRO[0]),
        ]
        delay = int(audible_start * 1000)
        filters.append(
            f"[{index}:a]aresample=48000,volume={MUSIC_GAIN},afade=t=in:d=1,"
            f"afade=t=out:st={OUTRO[2] - 3:.6f}:d=3,"
            f"adelay={delay}|{delay}[m{index}]"
        )
        mixed.append(f"[m{index}]")

    filters.append(
        "".join(mixed)
        + f"amix=inputs={len(mixed)}:normalize=0:duration=first,"
        "alimiter=limit=0.95[aout]"
    )
    filter_file.write_text(";\n".join(filters) + "\n")
    cmd += [
        "-/filter_complex",
        str(filter_file),
        "-map",
        "[aout]",
        "-vn",
        "-c:a",
        "aac",
        "-b:a",
        "320k",
        "-movflags",
        "+faststart",
        "-t",
        f"{total:.6f}",
        str(out),
    ]

    signature = command_signature(cmd)
    range_file = Path(str(out) + ".range")
    if out.exists() and range_file.exists() and range_file.read_text() == signature:
        return out, 0.0, []
    started = time.monotonic()
    run(cmd, cwd=E)
    range_file.write_text(signature)
    return out, time.monotonic() - started, [cmd]


def output_path(args, total):
    if args.test:
        return SOL / ("test8-mono.mp4" if args.mono else "test8.mp4")
    if args.duree is not None:
        mode = "mono" if args.mono else "parallel"
        label = f"{total:g}".replace(".", "-")
        return SOL / f"test-{label}s-{mode}.mp4"
    return OUT


def mux(video, audio, out, total):
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video),
        "-i",
        str(audio),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-t",
        f"{total:.6f}",
        "-movflags",
        "+faststart",
        str(out),
    ]
    run(cmd, cwd=E)
    return cmd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-lambda-deploy", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--skip-renders", action="store_true")
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="rendre les médias manquants sur Lambda puis quitter",
    )
    parser.add_argument("--test", action="store_true", help="assembler 8 secondes")
    parser.add_argument("--duree", type=float, help="limiter la timeline à S secondes")
    parser.add_argument(
        "--mono",
        action="store_true",
        help="utiliser l'assemblage vidéo historique",
    )
    args = parser.parse_args()
    if args.record_lambda_deploy:
        record_lambda_deploy()
        return
    if args.duree is not None and args.duree <= 0:
        parser.error("--duree doit être positive")
    if not SRC.exists():
        raise SystemExit(f"source absente : {SRC}")

    F.mkdir(parents=True, exist_ok=True)
    SOL.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    places = json.loads((E / "placements.json").read_text())
    chapters = json.loads((E / "chapitres.json").read_text())
    caps = json.loads((E / "captions_lucien.json").read_text())["occs"]
    badge = json.loads((E / "props-05b-badge-chapitres.json").read_text())[
        "chapitres"
    ]

    rng = {}
    for item in places:
        lo, hi = item["from"], item["from"] + item["dur"] - 1
        current = rng.setdefault(item["id"], [lo, hi, item["mode"]])
        current[0], current[1] = min(current[0], lo), max(current[1], hi)

    render_jobs(places, caps, badge, rng, args.skip_renders)
    if args.render_only:
        print("rendus Lambda terminés", flush=True)
        return
    video_assets, audio_assets, missing = build_assets(places, caps, badge, rng)
    if missing:
        print(
            "rendus manquants, posés sans eux : "
            + ", ".join(sorted(set(missing))),
            flush=True,
        )

    source_total = media_duration(SRC)
    requested = 8.0 if args.test else args.duree
    total = min(source_total, requested) if requested is not None else source_total
    total = math.floor(total * FPS_OUT + 1e-6) / FPS_OUT
    mode = "mono" if args.mono else "parallèle"
    tag = f"{total:.3f}-{mode}"
    work = WORK / tag
    work.mkdir(parents=True, exist_ok=True)

    print(f"4. audio unique, {total:.3f} s", flush=True)
    audio, audio_seconds, audio_commands = render_audio(
        total, source_total, audio_assets, badge, chapters, work
    )
    print(f"   audio : {audio_seconds:.1f} s", flush=True)

    print(f"5. vidéo {mode}", flush=True)
    if args.mono:
        video, video_seconds, video_commands = render_mono_video(
            total, video_assets, work
        )
    else:
        video, video_seconds, video_commands = render_parallel_video(
            total, video_assets, work
        )
    print(f"   vidéo : {video_seconds:.1f} s", flush=True)

    out = output_path(args, total)
    print("6. concaténation et mux", flush=True)
    mux_command = mux(video, audio, out, total)
    all_commands = audio_commands + video_commands + [mux_command]
    (E / "final.sh").write_text(
        "#!/bin/sh\nset -eu\n"
        + "\n".join(shlex.join([str(x) for x in cmd]) for cmd in all_commands)
        + "\n"
    )
    print(f"fini : {out}", flush=True)
    print(
        json.dumps(
            {
                "output": str(out),
                "duration": total,
                "mode": mode,
                "audio_seconds": round(audio_seconds, 3),
                "video_seconds": round(video_seconds, 3),
                "missing": sorted(set(missing)),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
