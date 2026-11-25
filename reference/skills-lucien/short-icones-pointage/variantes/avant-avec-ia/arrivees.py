"""Mesure, à 25 i/s, la hauteur du doigt levé de chaque côté sur la prise DJI verticale.

Arrivée d'un geste = première image où le bout du doigt atteint sa hauteur de maintien (à 6 px près
à l'échelle 540x960). Sortie : arrivees.json et un tableau texte.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

V = sys.argv[1]
approx = json.loads(sys.argv[2])  # [["G", 5.0], ["D", 6.4], ...]
W, H, FPS = 540, 960, 25
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", V, "-vf", f"fps={FPS},scale={W}:{H}", "-f", "rawvideo",
                      "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3).astype(int)


def tip_y(f, side):
    R, G, B = f[..., 0], f[..., 1], f[..., 2]
    skin = (R > 90) & (R - B > 30) & (R > G + 8)
    if side == "G":
        skin[:, 200:] = False
    else:
        skin[:, :340] = False
    skin[:250] = False
    skin[620:] = False
    rows = np.where(skin.sum(1) >= 2)[0]
    return int(rows.min()) if len(rows) else H


out = []
for side, a in approx:
    i0, i1 = int((a - 0.8) * FPS), int((a + 0.8) * FPS)
    ys = np.array([tip_y(fr[i], side) for i in range(i0, i1)])
    hold = int(np.median(ys[int(0.8 * FPS):int(1.2 * FPS)]))
    k = int(np.argmax(ys <= hold + 6))
    t = (i0 + k) / FPS
    out.append({"cote": side, "approx": a, "arrivee": round(t, 3), "y_maintien": hold})
    print(f"{side} approx {a:5.2f}  arrivée {t:6.2f}  y {hold}  profil {' '.join(str(v) for v in ys[::2])}")
Path(sys.argv[3]).write_text(json.dumps(out, indent=1))
