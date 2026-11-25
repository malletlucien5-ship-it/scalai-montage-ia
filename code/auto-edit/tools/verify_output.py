#!/usr/bin/python3
"""Contrôle final d'un rendu multicam, sans rien ouvrir.

  verify_output.py OUT.mp4 [--expect-frames N] [--sheet-dir DIR]

- frames vidéo vs durée audio (Δ doit être 0 ms ; 1,8 s = clips courts d'une
  frame, voir tpad dans multicam.py)
- si --expect-frames : égalité avec le plan
- images très blanches (page blanche pleine = document ?) listées pour relecture
- planche-contact toutes les 15 s dans --sheet-dir (à regarder avec Read)
"""
import argparse, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,duration,nb_frames,r_frame_rate", "-of", "json", path],
                       capture_output=True, text=True)
    import json
    st = json.loads(r.stdout)["streams"]
    v = next(s for s in st if s["codec_type"] == "video"); a = next(s for s in st if s["codec_type"] == "audio")
    n, d = v["r_frame_rate"].split("/")
    return int(v.get("nb_frames", 0)), float(v["duration"]), float(a["duration"]), int(n) / int(d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--expect-frames", type=int, default=None)
    ap.add_argument("--sheet-dir", default=None)
    a = ap.parse_args()
    nf, vd, ad, fps = probe(a.video)
    ok = True
    print(f"vidéo {nf} frames = {nf/fps:.3f}s | audio {ad:.3f}s | Δ = {(ad - nf/fps)*1000:+.0f} ms")
    if abs(ad - nf / fps) > 0.05:
        print("  ✗ désync audio/vidéo (clips vidéo courts ? tpad manquant ?)"); ok = False
    if a.expect_frames is not None:
        if abs(nf - a.expect_frames) > 1:
            print(f"  ✗ frames {nf} ≠ plan {a.expect_frames}"); ok = False
        else:
            print(f"  ✓ frames = plan ({a.expect_frames})")
    tmp = tempfile.mkdtemp()
    subprocess.run(["ffmpeg", "-v", "error", "-i", a.video, "-vf", "fps=1,scale=320:-1", "-q:v", "5",
                    os.path.join(tmp, "o%05d.jpg")], check=True)
    white = []
    for f in sorted(os.listdir(tmp)):
        g = np.asarray(Image.open(os.path.join(tmp, f)).convert("L"), dtype=float)
        h, w = g.shape; c = g[int(h*.15):int(h*.85), int(w*.2):int(w*.8)]
        if c.mean() > 215 and (c > 240).mean() > 0.6:
            white.append(int(f[1:6]) - 1)
    print(f"images très blanches (à relire, page de doc ?) : {len(white)} → {white[:20]}")
    if a.sheet_dir:
        subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "contact_sheets.py"),
                        "video", a.video, "--every", "15", "--out", a.sheet_dir, "--prefix", "out"], check=True)
    print("RÉSULTAT :", "OK" if ok else "À CORRIGER")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
