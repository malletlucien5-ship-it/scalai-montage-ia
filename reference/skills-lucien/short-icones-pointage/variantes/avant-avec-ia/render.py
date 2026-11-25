#!/usr/bin/env python3
"""Montage du short « avant l'IA / avec l'IA » : coupes + zoom + étalonnage A.

La prise DJI est verticale (2160x3840 après rotation). On zoome de 1,25 autour de la tête
pour la caler sur Dan (tête centrée à 44 % de la hauteur). Aucune fenêtre ne s'ouvre.
"""
import json
import subprocess
import sys
from pathlib import Path

here = Path(__file__).parent
cfg = json.loads((here / "cuts.json").read_text())
out = here.parent / "out"
out.mkdir(exist_ok=True)
x0, y0, w, h = cfg["crop"]
vf = f"crop={w}:{h}:{x0}:{y0},scale=1080:1920:flags=lanczos,fps={cfg['fps']},{cfg['grade_base']},{cfg['look']},format=yuv420p"
parts = []
for i, (a, b) in enumerate(cfg["ranges"]):
    p = out / f"part{i}.mp4"
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", f"{b - a:.3f}", "-i", cfg["source"],
        "-vf", vf, "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "15",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(p),
    ], check=True)
    parts.append(p)
lst = out / "concat.txt"
lst.write_text("".join(f"file '{p}'\n" for p in parts))
name = sys.argv[1] if len(sys.argv) > 1 else "v1"
final = out / f"montage-{name}.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                "-c", "copy", "-movflags", "+faststart", str(final)], check=True)
print(final)
