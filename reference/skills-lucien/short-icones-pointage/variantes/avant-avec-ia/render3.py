#!/usr/bin/env python3
"""Montage calé sur la référence : chaque geste de Lucien tombe sur l'image du bip de Dan.

Chaque section de la référence est découpée en 3 morceaux :
- A : du début de section au bip gauche, vitesse normale ;
- B : du bip gauche au bip droit, vitesse ajustée pour que le geste droit tombe pile ;
- C : du bip droit à la fin de section, vitesse normale.
"""
import json
import subprocess
import sys
from pathlib import Path

here = Path(__file__).parent
cfg = json.loads((here / "cuts3.json").read_text())
FPS = 30000 / 1001
out = here.parent / "out3"
out.mkdir(exist_ok=True)
x0, y0, w, h = cfg["crop"]
look = f"crop={w}:{h}:{x0}:{y0},scale=1080:1920:flags=lanczos,{cfg['grade_base']},{cfg['look']},format=yuv420p"

bounds = cfg["sections_frames"]
bips = cfg["bips_ref"]
arr = cfg["arrivees_src"]
pieces = []
for i in range(len(bounds) - 1):
    bL, bR = bips[2 * i], bips[2 * i + 1]
    aL, aR = arr[2 * i], arr[2 * i + 1]
    fL, fR = round(bL * FPS), round(bR * FPS)
    speed = (aR - aL) / (bR - bL)
    pieces.append((bounds[i], fL, aL - (bL - bounds[i] / FPS), 1.0))
    pieces.append((fL, fR, aL + (fL / FPS - bL) * speed, speed))
    pieces.append((fR, bounds[i + 1], aR + (fR / FPS - bR), 1.0))
    print(f"S{i + 1} vitesse entre les gestes {speed:.2f}")

files = []
for k, (o0, o1, s0, speed) in enumerate(pieces):
    p = out / f"p{k:02d}.mp4"
    n = o1 - o0
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-ss", f"{s0:.4f}", "-i", cfg["source"],
        "-vf", f"setpts=(PTS-STARTPTS)/{speed:.5f},fps={cfg['fps']},{look}",
        "-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "15",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(p),
    ], check=True)
    got = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v",
                              "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(p)],
                             capture_output=True, text=True).stdout.split()[0])
    assert got == n, f"morceau {k} : {got} images au lieu de {n}"
    files.append(p)
lst = out / "concat.txt"
lst.write_text("".join(f"file '{p}'\n" for p in files))
name = sys.argv[1] if len(sys.argv) > 1 else "v1"
final = out / f"montage-{name}.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                "-c", "copy", "-movflags", "+faststart", str(final)], check=True)
print(final)
