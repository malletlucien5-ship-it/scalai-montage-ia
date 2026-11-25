#!/usr/bin/env python3
"""Montage sans aucune coupe : une seule prise continue, vitesse ajustée entre les gestes.

La courbe temps référence → temps source passe par les 14 gestes. Entre deux gestes, la vitesse
est constante. Avant le premier et après le dernier, vitesse normale. Chaque arrivée de doigt
tombe sur l'image du bip de la référence. Étalonnage : correction de base + PowerGrade.
"""
import json
import subprocess
import sys
from pathlib import Path

here = Path(__file__).parent
cfg = json.loads((here / "cuts3.json").read_text())
FPS = 30000 / 1001
TOTAL = cfg["sections_frames"][-1]
out = here.parent / "out4"
out.mkdir(exist_ok=True)
x0, y0, w, h = cfg["crop"]
grade = cfg["grade_base"] + "," + cfg.get("look_powergrade", cfg["look"])
chain = f"crop={w}:{h}:{x0}:{y0},scale=1080:1920:flags=lanczos,{grade},format=yuv420p"

frames = [round(b * FPS) for b in cfg["bips_ref"]]
arr = cfg["arrivees_src"]
pieces = [(0, frames[0], arr[0] - frames[0] / FPS, 1.0)]
for k in range(len(frames) - 1):
    dt = (frames[k + 1] - frames[k]) / FPS
    pieces.append((frames[k], frames[k + 1], arr[k], (arr[k + 1] - arr[k]) / dt))
pieces.append((frames[-1], TOTAL, arr[-1], 1.0))
print("vitesses :", " ".join(f"{p[3]:.2f}" for p in pieces))

files = []
for k, (o0, o1, s0, speed) in enumerate(pieces):
    p = out / f"p{k:02d}.mp4"
    n = o1 - o0
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-ss", f"{s0:.4f}", "-i", cfg["source"],
        "-vf", f"setpts=(PTS-STARTPTS)/{speed:.5f},fps={cfg['fps']},{chain}",
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
