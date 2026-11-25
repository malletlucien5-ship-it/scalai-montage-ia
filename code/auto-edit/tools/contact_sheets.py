#!/usr/bin/python3
"""Planches-contact pour relecture visuelle par Claude (jamais d'ouverture d'app).

  contact_sheets.py frames DIR --step 6 --out OUTDIR [--prefix scan]
      DIR contient fNNNNN.jpg extraits à 1 fps (ffmpeg -vf fps=1). Une planche
      de 30 vignettes (6x5) toutes les `step` secondes, horodatée m:ss.
  contact_sheets.py video FILE.mp4 --every 15 --out OUTDIR [--prefix out]
      Extrait une image toutes les `every` s de la vidéo et fait une planche.
"""
import argparse, os, re, subprocess, sys
from PIL import Image, ImageDraw

TW, TH, COLS, ROWS = 320, 180, 6, 5


def sheet(paths_secs, out_path):
    n = len(paths_secs)
    rows = (n + COLS - 1) // COLS
    im = Image.new("RGB", (TW * COLS, TH * max(1, rows)), "black")
    d = ImageDraw.Draw(im)
    for k, (p, s) in enumerate(paths_secs):
        th = Image.open(p).resize((TW, TH))
        x, y = (k % COLS) * TW, (k // COLS) * TH
        im.paste(th, (x, y))
        d.rectangle([x, y, x + 70, y + 16], fill="black")
        d.text((x + 3, y + 3), f"{int(s)//60}:{int(s)%60:02d}", fill="yellow")
    im.save(out_path, quality=78)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("frames"); a.add_argument("dir"); a.add_argument("--step", type=int, default=6)
    a.add_argument("--out", required=True); a.add_argument("--prefix", default="scan")
    b = sub.add_parser("video"); b.add_argument("video"); b.add_argument("--every", type=int, default=15)
    b.add_argument("--out", required=True); b.add_argument("--prefix", default="out")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    if args.cmd == "frames":
        files = sorted(f for f in os.listdir(args.dir) if re.fullmatch(r"f\d+\.jpg", f))
        items = []
        for f in files:
            sec = int(re.findall(r"\d+", f)[0]) - 1
            if sec % args.step == 0:
                items.append((os.path.join(args.dir, f), sec))
        per = COLS * ROWS
        n = 0
        for k in range(0, len(items), per):
            sheet(items[k:k + per], os.path.join(args.out, f"{args.prefix}_{n:02d}.jpg")); n += 1
        print(f"{n} planches ({len(items)} vignettes, pas {args.step}s) → {args.out}")
    else:
        tmp = os.path.join(args.out, f"_{args.prefix}_frames")
        os.makedirs(tmp, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", args.video,
                        "-vf", f"fps=1/{args.every},scale=480:-1", "-q:v", "4",
                        os.path.join(tmp, "o%04d.jpg")], check=True)
        files = sorted(os.listdir(tmp))
        items = [(os.path.join(tmp, f), i * args.every) for i, f in enumerate(files)]
        per = COLS * ROWS
        n = 0
        for k in range(0, len(items), per):
            sheet(items[k:k + per], os.path.join(args.out, f"{args.prefix}_{n:02d}.jpg")); n += 1
        print(f"{n} planches ({len(items)} vignettes, toutes les {args.every}s) → {args.out}")


if __name__ == "__main__":
    main()
