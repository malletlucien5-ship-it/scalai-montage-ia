#!/usr/bin/env python3
"""Montage prise 2 (vidéo verticale) : coupes + fond prolongé + étalonnage.

La vidéo est réduite puis posée sur un fond prolongé par Bria (plate_raw.png).
Tête au niveau de celle de Dan, plus de place à droite. Aucune fenêtre ne s'ouvre.
"""
import json
import subprocess
import sys
from pathlib import Path

here = Path(__file__).parent
cfg = json.loads((here / "cuts.json").read_text())
out = here.parent / "out2"
out.mkdir(exist_ok=True)
w, h = cfg["video_size"]
ox, oy = cfg["video_pos"]
grade = cfg["grade"]
fc = (
    f"[0:v]fps={cfg['fps']},scale={w}:{h}:flags=lanczos,format=rgba[v];"
    f"[2:v]format=gray,scale={w}:{h}[m];[v][m]alphamerge[va];"
    f"[1:v]format=rgba[bg];[bg][va]overlay={ox}:{oy}:shortest=1,{grade},format=yuv420p[o]"
)
parts = []
for s in cfg["sections"]:
    a, b = s["src"]
    p = out / f"{s['id']}.mp4"
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-ss", str(a), "-t", f"{b - a:.3f}", "-i", cfg["source"],
        "-loop", "1", "-framerate", cfg["fps"], "-i", str(here / "plate_miroir.png"), "-loop", "1", "-framerate", cfg["fps"], "-i", str(here / "mask.png"),
        "-filter_complex", fc, "-map", "[o]", "-an", "-t", f"{b - a:.3f}",
        "-c:v", "libx264", "-preset", "slow", "-crf", "15",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", str(p),
    ], check=True)
    parts.append(p)
lst = out / "concat.txt"
lst.write_text("".join(f"file '{p}'\n" for p in parts))
name = sys.argv[1] if len(sys.argv) > 1 else "v1"
final = out / f"montage-prise2-{name}.mp4"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                "-c", "copy", "-movflags", "+faststart", str(final)], check=True)
print(final)
