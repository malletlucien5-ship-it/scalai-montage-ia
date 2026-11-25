#!/usr/bin/python3
"""
detect_script_ranges.py — Trouve les plages où une page donnée (ex : le script
Google Docs) est visible dans une capture d'écran, à partir d'images extraites
à 1 fps.

Méthode déterministe : chaque image est réduite en gris 48x27, normalisée,
puis comparée (distance L1 moyenne) à une ou plusieurs images de référence.
Une image est "script" si sa distance à la référence la plus proche est sous
le seuil. Les secondes contiguës forment des plages ; les trous < gap_s sont
comblés ; les plages < min_s sont ignorées.

Usage :
  python3 detect_script_ranges.py FRAMES_DIR --ref f00006.jpg [--ref ...]
      [--threshold 0.08] [--gap 2] [--min 1] [--out ranges.json] [--dump]

FRAMES_DIR contient fNNNNN.jpg extraits par `ffmpeg -vf fps=1` :
fNNNNN correspond à la seconde NNNNN-1 (ffmpeg numérote à partir de 1).
"""
import argparse
import json
import os
import re
import sys

import numpy as np
from PIL import Image

SMALL = (48, 27)


def fingerprint(path):
    im = Image.open(path).convert("L").resize(SMALL, Image.BILINEAR)
    a = np.asarray(im, dtype=np.float32) / 255.0
    a = a - a.mean()
    s = a.std()
    return a / s if s > 1e-6 else a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frames_dir")
    ap.add_argument("--ref", action="append", required=True,
                    help="Nom de fichier (dans frames_dir) ou chemin d'une image script")
    ap.add_argument("--threshold", type=float, default=None,
                    help="Distance max pour être 'script' (défaut : auto)")
    ap.add_argument("--gap", type=float, default=2.0)
    ap.add_argument("--min", dest="min_s", type=float, default=1.0)
    ap.add_argument("--pad", type=float, default=0.0,
                    help="Élargit chaque plage de N s de chaque côté")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dump", action="store_true",
                    help="Imprime la distance de chaque seconde")
    args = ap.parse_args()

    files = sorted(f for f in os.listdir(args.frames_dir)
                   if re.fullmatch(r"f\d+\.jpg", f))
    if not files:
        sys.exit("aucune image fNNNNN.jpg dans le dossier")
    refs = []
    for r in args.ref:
        p = r if os.path.isabs(r) or os.path.exists(r) else os.path.join(args.frames_dir, r)
        refs.append(fingerprint(p))

    dists = []
    for f in files:
        fp = fingerprint(os.path.join(args.frames_dir, f))
        d = min(float(np.abs(fp - r).mean()) for r in refs)
        dists.append(d)
    dists = np.array(dists)

    thr = args.threshold
    if thr is None:
        # coupure entre le mode "proche" et le reste : bimodal attendu
        hist, edges = np.histogram(dists, bins=40)
        lo = dists.min()
        # premier creux après le premier pic
        i_peak = int(np.argmax(hist[: max(2, len(hist) // 3)]))
        i_valley = i_peak + int(np.argmin(hist[i_peak: i_peak + 10]))
        thr = float(edges[i_valley + 1])
        print(f"seuil auto = {thr:.3f} (min {lo:.3f}, médiane {np.median(dists):.3f}, "
              f"max {dists.max():.3f})")

    if args.dump:
        for f, d in zip(files, dists):
            sec = int(re.findall(r"\d+", f)[0]) - 1
            print(f"{sec:5d}s  {d:.3f}  {'SCRIPT' if d <= thr else ''}")

    flags = dists <= thr
    ranges = []
    start = None
    for f, on in zip(files, flags):
        sec = int(re.findall(r"\d+", f)[0]) - 1
        if on and start is None:
            start = sec
        elif not on and start is not None:
            ranges.append([start, sec])   # [start, end) en secondes
            start = None
    if start is not None:
        ranges.append([start, int(re.findall(r"\d+", files[-1])[0])])

    # comble les trous courts
    merged = []
    for a, b in ranges:
        if merged and a - merged[-1][1] <= args.gap:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    merged = [[a - args.pad, b + args.pad] for a, b in merged if b - a >= args.min_s]
    merged = [[max(0.0, a), b] for a, b in merged]

    total = sum(b - a for a, b in merged)
    print(f"{len(merged)} plages, {total:.0f}s au total :")
    for a, b in merged:
        print(f"  {a:7.1f} → {b:7.1f}  ({b - a:5.1f}s)")
    if args.out:
        with open(args.out, "w") as f:
            json.dump(merged, f)
        print(f"→ {args.out}")


if __name__ == "__main__":
    main()
